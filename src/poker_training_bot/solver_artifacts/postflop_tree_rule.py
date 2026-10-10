"""GTOpen's tree rule, ported to count a flop tree rather than build it.

A line-for-line port of `crates/solver/src/tree.rs` in the solver clone (`legal_actions`,
`apply_action`, `check_behind`, `street_end` and `runout_chance`), with one change: where the Rust
pushes a node, this adds one to a count. The amounts are the same IEEE doubles computed in the same
order, so every snap to all-in and every deduplicated size lands on the side the solver puts it.

**Why counting is enough.** A tree's shape depends on the pot, the stack and the menu and never on
the board. Every card a chance node deals builds the same subtree, so a subtree is counted once per
distinct betting state and multiplied by the cards dealt into it. That collapses a four-million-node
tree to a few thousand states and makes one tree per line a fraction of a second.

**The waste is kept, because the solver keeps it.** `street_end` skips only the three flop cards, so
the river chance under turn card T still builds a subtree in T's own slot. Those river decision
points are counted here as built, and `postflop_tree_size` takes the reachable part apart from them.

**The two rules (decision 17).** `carry_aggressor_through_checks` is GTOpen's own `TreeConfig`
field, added to the clone at `b058335`: true is the pin's rule, where a street both players check
passes the last aggressor on, so out of position meets the empty `donk` list on the next street;
false, the clone's and the campaign's, clears the initiative on a checked-through street.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache

from poker_training_bot.poker_core.cards import RANKS, SUITS
from poker_training_bot.solver_artifacts.postflop_artifact import POSTFLOP_DIR
from poker_training_bot.solver_artifacts.postflop_isomorphism import FLOP_CARDS
from poker_training_bot.solver_artifacts.postflop_solve_driver import (
    STREETS,
    solve_config_errors,
    validate_allin_threshold,
)

SOLVE_CONFIG_PATH = POSTFLOP_DIR / "solve_config.json"

OOP = 0
IP = 1
SEATS = (OOP, IP)
FLOP, TURN, RIVER = range(len(STREETS))
ROOT_STREET = FLOP
"""Every campaign solve is rooted at the flop, so the root street the donk gate compares is this."""

DECK_CARDS = len(RANKS) * len(SUITS)
CARDS_PER_CHANCE = DECK_CARDS - FLOP_CARDS
"""How many children each chance node builds: `street_end` and `runout_chance` skip the static
flop and nothing else, so the turn and the river chance both deal 49."""

_EPSILON = 1e-9
_DEDUPE_TOLERANCE = 1e-6


# --- The menu, as the server hands it to the tree builder


@dataclass(frozen=True)
class SizeRule:
    """One parsed size token: a percent of the pot, a multiple of the bet faced, or all-in."""

    kind: str
    value: float = 0.0


POT_PERCENT = "pot-percent"
PREVIOUS_MULTIPLE = "previous-multiple"
ALL_IN = "all-in"


def parse_sizes(text: str) -> tuple[SizeRule, ...]:
    """GTOpen's `parse_sizes`: `33 75`, `2.5x`, `a`. Refuses what it refuses, so a menu this port
    counts is a menu the server would have accepted."""
    rules: list[SizeRule] = []
    for raw in text.replace(",", " ").replace(";", " ").split(" "):
        token = raw.strip().lower()
        if not token:
            continue
        if token in ("a", "allin", "all-in"):
            rules.append(SizeRule(ALL_IN))
        elif token.endswith("x"):
            multiple = float(token[:-1])
            if multiple != multiple or multiple in (float("inf"), float("-inf")) or multiple <= 1:
                raise ValueError(f"raise multiple must be a finite number > 1: {token!r}")
            rules.append(SizeRule(PREVIOUS_MULTIPLE, multiple))
        else:
            percent = float(token)
            if percent != percent or percent in (float("inf"), float("-inf")) or percent <= 0:
                raise ValueError(f"bet size must be a positive finite number: {token!r}")
            rules.append(SizeRule(POT_PERCENT, percent))
    return tuple(rules)


@dataclass(frozen=True)
class StreetMenu:
    """GTOpen's `StreetSizing`: what one seat may bet, raise and lead into the last aggressor."""

    bet: tuple[SizeRule, ...]
    raise_: tuple[SizeRule, ...]
    donk: tuple[SizeRule, ...]


@dataclass(frozen=True)
class TreeMenu:
    """The parts of GTOpen's `TreeConfig` that are not the pot, the stack or the rule.

    `allin_threshold` is a fraction here, as the tree builder reads it: the server divides the
    posted percent by 100 before building."""

    seats: tuple[tuple[StreetMenu, ...], tuple[StreetMenu, ...]]
    allin_threshold: float
    add_allin: bool
    max_raises: int


def _joined(sizes: object) -> str:
    if isinstance(sizes, str):
        return sizes
    if isinstance(sizes, list | tuple):
        return " ".join(str(size) for size in sizes)
    raise ValueError(f"a size list must be a string or a list, got {sizes!r}")


def menu_from_config(config: Mapping[str, object]) -> TreeMenu:
    """The tree builder's menu from a committed config, refusing one that is not the ruled config:
    the tree counted must be the tree the driver posts, and `plan_refusals` holds the driver to
    exactly that configuration."""
    errors = solve_config_errors(config)
    if errors:
        raise ValueError("solve config is not the ruled one: " + "; ".join(errors))
    seats = config["seats"]
    assert isinstance(seats, Mapping)
    built: list[tuple[StreetMenu, ...]] = []
    for name in ("oop", "ip"):
        streets = seats[name]
        assert isinstance(streets, Mapping)
        built.append(
            tuple(
                StreetMenu(
                    bet=parse_sizes(_joined(streets[street].get("bet", []))),
                    raise_=parse_sizes(_joined(streets[street].get("raise", ""))),
                    donk=parse_sizes(_joined(streets[street].get("donk", []))),
                )
                for street in STREETS
            )
        )
    threshold = config["allin_threshold"]
    max_raises = config["max_raises"]
    assert isinstance(threshold, int | float) and isinstance(max_raises, int)
    return TreeMenu(
        seats=(built[OOP], built[IP]),
        allin_threshold=validate_allin_threshold(threshold) / 100.0,
        add_allin=bool(config.get("add_allin", False)),
        max_raises=max_raises,
    )


@cache
def committed_menu() -> TreeMenu:
    """The menu in `data/artifacts/postflop/solve_config.json`, read once."""
    return menu_from_config(json.loads(SOLVE_CONFIG_PATH.read_text(encoding="utf-8")))


# --- The count

COUNT_WIDTH = 1 + len(STREETS) * len(SEATS) + len(SEATS)
"""A count is a flat tuple: the node total, then action nodes for each street and seat (flop out of
position, flop in position, turn, river), then the action slots of each seat."""
_NODE = 0
_SLOTS = 1 + len(STREETS) * len(SEATS)

Count = tuple[int, ...]
_ONE_NODE: Count = (1,) + (0,) * (COUNT_WIDTH - 1)


def _add(left: Count, right: Count) -> Count:
    return tuple(a + b for a, b in zip(left, right, strict=True))


def _scale(count: Count, times: int) -> Count:
    return tuple(value * times for value in count)


def _action_index(street: int, seat: int) -> int:
    return 1 + street * len(SEATS) + seat


@dataclass(frozen=True)
class _State:
    """GTOpen's `BuildState`, hashable so a subtree is counted once per state."""

    street: int
    to_act: int
    put: tuple[float, float]
    street_bet: tuple[float, float]
    last_increment: float
    num_raises: int
    last_aggressor: int | None
    checked: bool


def _dedupe(amounts: list[float]) -> list[float]:
    """`dedupe_amounts`: sort, then drop an amount within 1e-6 of the last one kept."""
    kept: list[float] = []
    for amount in sorted(amounts):
        if not kept or abs(amount - kept[-1]) >= _DEDUPE_TOLERANCE:
            kept.append(amount)
    return kept


class TreeCounter:
    """Counts the tree `TreeBuilder::build` would build for one pot, stack, menu and rule."""

    def __init__(
        self,
        starting_pot: float,
        effective_stack: float,
        menu: TreeMenu,
        *,
        carry_aggressor_through_checks: bool,
    ) -> None:
        if not (starting_pot > 0 and effective_stack > 0):
            raise ValueError("pot and stacks must be positive finite numbers")
        self.starting_pot = float(starting_pot)
        self.effective_stack = float(effective_stack)
        self.menu = menu
        self.carry = carry_aggressor_through_checks
        self._memo: dict[_State, Count] = {}

    def count(self) -> Count:
        half = self.starting_pot / 2.0
        root = _State(ROOT_STREET, OOP, (half, half), (0.0, 0.0), 0.0, 0, None, False)
        return self._action_node(root)

    def _stack_behind(self, put_me: float) -> float:
        return self.effective_stack - (put_me - self.starting_pot / 2.0)

    def legal_actions(self, st: _State) -> list[tuple[str, float]]:
        """`legal_actions`: fold, call and the raises when facing a bet; else check and the bets."""
        me, opp = st.to_act, 1 - st.to_act
        stack_me = self._stack_behind(st.put[me])
        sizing = self.menu.seats[st.to_act][st.street]
        facing = st.street_bet[opp] - st.street_bet[me]
        if facing > _EPSILON:
            actions: list[tuple[str, float]] = [("fold", 0.0), ("call", st.street_bet[opp])]
            if stack_me > facing + _EPSILON and st.num_raises < self.menu.max_raises:
                pot_after_call = st.put[0] + st.put[1] + facing
                max_to = st.street_bet[me] + stack_me
                candidates: list[float] = []
                for size in sizing.raise_:
                    if size.kind == POT_PERCENT:
                        candidates.append(st.street_bet[opp] + size.value / 100.0 * pot_after_call)
                    elif size.kind == PREVIOUS_MULTIPLE:
                        candidates.append(st.street_bet[opp] * size.value)
                    else:
                        candidates.append(max_to)
                if self.menu.add_allin:
                    candidates.append(max_to)
                min_to = st.street_bet[opp] + max(st.last_increment, _EPSILON)
                tos: list[float] = []
                for to in candidates:
                    if to < min_to:
                        to = min_to
                    if (
                        to >= max_to - _EPSILON
                        or to >= self.menu.allin_threshold * max_to - _EPSILON
                    ):
                        to = max_to
                    if to > st.street_bet[opp] + _EPSILON:
                        tos.append(to)
                actions.extend(("raise", to) for to in _dedupe(tos))
            return actions
        actions = [("check", 0.0)]
        if stack_me > _EPSILON:
            donking = st.to_act == OOP and st.street > ROOT_STREET and st.last_aggressor == IP
            size_list = sizing.donk if donking else sizing.bet
            pot = st.put[0] + st.put[1]
            max_to = stack_me
            candidates = []
            for size in size_list:
                if size.kind == POT_PERCENT:
                    candidates.append(size.value / 100.0 * pot)
                elif size.kind == ALL_IN:
                    candidates.append(max_to)
                # A raise multiple in a bet list is dropped, as the lenient load drops it.
            if self.menu.add_allin and (size_list or not donking):
                candidates.append(max_to)
            tos = []
            for to in candidates:
                if to <= _EPSILON:
                    continue
                if to >= max_to - _EPSILON or to >= self.menu.allin_threshold * max_to - _EPSILON:
                    to = max_to
                tos.append(to)
            actions.extend(("bet", to) for to in _dedupe(tos))
        return actions

    def _action_node(self, st: _State) -> Count:
        found = self._memo.get(st)
        if found is not None:
            return found
        actions = self.legal_actions(st)
        if not actions or len(actions) > 250:
            raise ValueError(f"invalid action count {len(actions)} during tree build")
        here = list(_ONE_NODE)
        here[_action_index(st.street, st.to_act)] += 1
        here[_SLOTS + st.to_act] += len(actions)
        total: Count = tuple(here)
        for action in actions:
            total = _add(total, self._apply(st, action))
        self._memo[st] = total
        return total

    def _apply(self, st: _State, action: tuple[str, float]) -> Count:
        """`apply_action`."""
        kind, to = action
        me, opp = st.to_act, 1 - st.to_act
        if kind == "fold":
            return _ONE_NODE
        if kind == "check":
            if st.checked:
                aggressor = st.last_aggressor if self.carry else None
                return self._street_end(st.street, st.put, aggressor, allin=False)
            return self._action_node(
                _State(
                    st.street,
                    st.to_act ^ 1,
                    st.put,
                    st.street_bet,
                    st.last_increment,
                    st.num_raises,
                    st.last_aggressor,
                    True,
                )
            )
        put = list(st.put)
        if kind == "call":
            put[me] += to - st.street_bet[me]
            allin = (
                self._stack_behind(put[me]) <= _EPSILON or self._stack_behind(put[opp]) <= _EPSILON
            )
            return self._street_end(st.street, (put[0], put[1]), st.to_act ^ 1, allin=allin)
        put[me] += to - st.street_bet[me]
        street_bet = list(st.street_bet)
        street_bet[me] = to
        increment = to - max(st.street_bet[opp], st.street_bet[me])
        return self._action_node(
            _State(
                st.street,
                st.to_act ^ 1,
                (put[0], put[1]),
                (street_bet[0], street_bet[1]),
                max(increment, st.last_increment),
                st.num_raises + (1 if kind == "raise" else 0),
                st.last_aggressor,
                st.checked,
            )
        )

    def _street_end(
        self, street: int, put: tuple[float, float], aggressor: int | None, *, allin: bool
    ) -> Count:
        """`street_end`: a showdown after the river, a runout after an all-in, else a chance node
        dealing every card but the flop into a fresh action round."""
        if street == RIVER:
            return _ONE_NODE
        if allin:
            return self._runout(street)
        child = _State(street + 1, OOP, put, (0.0, 0.0), 0.0, 0, aggressor, False)
        return _add(_ONE_NODE, _scale(self._action_node(child), CARDS_PER_CHANCE))

    def _runout(self, street: int) -> Count:
        """`runout_chance`: chance nodes down to the river showdowns, with no decision on them."""
        below = _ONE_NODE if street + 1 == RIVER else self._runout(street + 1)
        return _add(_ONE_NODE, _scale(below, CARDS_PER_CHANCE))


def count_tree(
    starting_pot: float,
    effective_stack: float,
    menu: TreeMenu,
    *,
    carry_aggressor_through_checks: bool,
) -> tuple[int, dict[str, tuple[int, int]], tuple[int, int]]:
    """The node total, action nodes per street and seat, and action slots per seat."""
    counted = TreeCounter(
        starting_pot,
        effective_stack,
        menu,
        carry_aggressor_through_checks=carry_aggressor_through_checks,
    ).count()
    action_nodes = {
        name: (counted[_action_index(index, OOP)], counted[_action_index(index, IP)])
        for index, name in enumerate(STREETS)
    }
    return counted[_NODE], action_nodes, (counted[_SLOTS + OOP], counted[_SLOTS + IP])
