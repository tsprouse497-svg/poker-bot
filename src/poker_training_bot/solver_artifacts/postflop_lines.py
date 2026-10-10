"""The preflop lines the flop campaign solves: which, in what order, and whose range is whose.

Decision 9, ruled by Taylor 2026-09-26: the five single-raised lines the committed chart plays,
the small blind, button, cutoff, hijack and lojack opening to 2.5bb and the big blind calling, in
the order the chart itself reaches them. Decision 10: every one of them is solved on
`solve_config.json`'s sizes and settings, the empty `donk` list included.

**Everything here is read off the committed chart**, `CHART_PATH`: a line's reach from its
`arrival_ppb` and `action_weights`, its two ranges from the same weights, floored class-level at
`RANGE_WEIGHT_FLOOR` the way phase 16 floored the button's line. Nothing is quoted from a report,
so a line ranks and is solved on the chart the bot plays preflop.

**Ranges are assigned by seat position after the flop, never by who raised.** GTOpen has two seats,
out of position and in position, and `scripts/solve_postflop_sample.py` hardcodes the big blind
out of position because every flop phase 16 solved was a button open. Against the small blind that
is backwards: the small blind raises and then acts first on every street after the flop.
`heads_up_seats` is the one place the seats are decided, and `line_ranges`, `seat_labels`,
`plan_for` and `flop_spot_keys` all take them from it.

**A line the chart cannot supply a range for is refused, never given one.** The corpus's fourth
most common flop line, the small blind completing and the big blind checking, is a limp the chart
never makes: its small blind only folds or raises first in. `LineRangeError` names the spot and
the action the chart does not offer.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from poker_training_bot.poker_core.positions import postflop_action_order, preflop_action_order
from poker_training_bot.solver_artifacts.postflop_artifact import floor_range
from poker_training_bot.solver_artifacts.postflop_harvest import (
    IP_PLAYER,
    OOP_PLAYER,
    raise_multiplier,
    size_pct,
)
from poker_training_bot.solver_artifacts.postflop_key import (
    FlopAction,
    PreflopLine,
    canonical_board,
    completed_preflop_line,
    postflop_spot_key,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (
    SolvePlan,
    solve_config_document,
)
from poker_training_bot.solver_artifacts.postflop_tree_rule import (
    ROOT_STREET,
    TreeCounter,
    _State,
    menu_from_config,
)
from poker_training_bot.solver_artifacts.spot_key import PreflopAction, render_entry, spot_key

CHART_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "artifacts"
    / "preflop"
    / "six_max_100bb_rakefree.json"
)

ADMITTED_LINES: tuple[str, ...] = (
    "SB:raise@2.5,BB:call",
    "BTN:raise@2.5,BB:call",
    "CO:raise@2.5,BB:call",
    "HJ:raise@2.5,BB:call",
    "LJ:raise@2.5,BB:call",
)
"""Decision 9's lines in its order. `ranked_lines` re-derives the order from the chart, and a test
holds the two together, so a chart that ranked them differently would be seen rather than obeyed."""

EXCLUDED_LINES: Mapping[str, str] = {
    "SB:call": (
        "a limp: the committed chart's small blind only folds or raises first in, so it has no"
        " range to complete with and the big blind none to check behind with"
    ),
}
"""Lines a reader would expect and the campaign does not solve, each with its reason. `SB:call` is
the corpus's fourth most common flop line; `line_ranges` refuses it, which is the reason proved."""

_PARTS_PER_BILLION = 1_000_000_000
_HEADS_UP = 2
_FLOP_STREET_ENDS = frozenset({"fold", "call"})


class LineRangeError(ValueError):
    """A line the committed chart cannot supply both ranges for, or that is not heads-up."""


@dataclass(frozen=True)
class LineRanges:
    """One heads-up line as GTOpen is asked to solve it: who sits in each seat, with what range,
    in what pot and behind what stack. Ranges are class-level and in the chart's hand order."""

    line: str
    oop_position: str
    ip_position: str
    range_oop: dict[str, float]
    range_ip: dict[str, float]
    starting_pot: float
    effective_stack: float


# --------------------------------------------------------------------------- #
# The chart, and a line in its grammar
# --------------------------------------------------------------------------- #


@cache
def committed_chart() -> Mapping[str, Any]:
    """The committed preflop chart, read once per process."""
    return json.loads(CHART_PATH.read_text(encoding="utf-8"))


def preflop_actions(line: str) -> tuple[PreflopAction, ...]:
    """A line such as `BTN:raise@2.5,BB:call` as recorded actions, refused unless it renders back
    to exactly itself, so `BTN:raise@2.50` or a stray space is never a second spelling of a line."""
    built: list[PreflopAction] = []
    for part in line.split(","):
        position, _, rest = part.partition(":")
        action, _, size = rest.partition("@")
        try:
            built.append(PreflopAction(position, action, float(size) if size else None))
        except ValueError as error:
            raise LineRangeError(f"{line!r} is not a preflop line: {error}") from error
    if ",".join(render_entry(entry) for entry in built) != line:
        raise LineRangeError(f"{line!r} does not render back to itself, so it is not canonical")
    return tuple(built)


def preflop_line_for(line: str, hero_position: str) -> PreflopLine:
    """The completed preflop street `line` names, from `hero_position`'s seat, at the chart's own
    table size, depth and blinds. Raises `LineRangeError` when no flop follows the line."""
    chart = committed_chart()
    blinds = chart["blind_structure"]
    try:
        return completed_preflop_line(
            int(chart["table_size"]),
            int(chart["stack_depth_bb"]),
            hero_position,
            preflop_actions(line),
            small_blind_bb=float(blinds["small_blind_bb"]),
            big_blind_bb=float(blinds["big_blind_bb"]),
            ante_bb=float(blinds["ante_bb"]),
        )
    except ValueError as error:
        if isinstance(error, LineRangeError):
            raise
        raise LineRangeError(f"{line}: {error}") from error


def _decisions(line: str) -> list[tuple[str, tuple[PreflopAction, ...], str]]:
    """Every decision the line is made of, implicit folds included, in the order they were made:
    who decided, what had happened before, and what they did. The ring is walked the way
    `completed_preflop_line` walks it, which has already refused any line no dealer deals."""
    actions = preflop_actions(line)
    closed = preflop_line_for(line, actions[-1].position)
    order = preflop_action_order(closed.table_size)
    live = set(closed.live_positions)
    made: list[tuple[str, tuple[PreflopAction, ...], str]] = []
    folded: set[str] = set()
    cursor = 0
    for index, entry in enumerate(actions):
        while order[cursor % len(order)] != entry.position:
            standing = order[cursor % len(order)]
            if standing not in folded:
                folded.add(standing)
                made.append((standing, actions[:index], "fold"))
            cursor += 1
        cursor += 1
        made.append((entry.position, actions[:index], entry.action))
    for offset in range(len(order)):
        standing = order[(cursor + offset) % len(order)]
        if standing not in folded and standing not in live:
            folded.add(standing)
            made.append((standing, actions, "fold"))
    return made


def _chart_spot(position: str, before: tuple[PreflopAction, ...]) -> str:
    chart = committed_chart()
    return spot_key(int(chart["table_size"]), int(chart["stack_depth_bb"]), position, before)


def _class_combos(hand: str) -> int:
    return 6 if len(hand) == _HEADS_UP else (4 if hand.endswith("s") else 12)


def _action_rate(spot: str, action: str) -> float:
    """How often the chart takes `action` at `spot`: the combo-weighted mean of its class weights
    over all 1,326 combos, the independence its own `arrival_ppb` is built on, and zero where the
    action is not offered at all."""
    weights = committed_chart()["action_weights"][spot]
    total = sum(_class_combos(hand) for hand in weights)
    return sum(_class_combos(hand) * row.get(action, 0.0) for hand, row in weights.items()) / total


# --------------------------------------------------------------------------- #
# Which lines, and in what order
# --------------------------------------------------------------------------- #


def line_reach(line: str) -> float:
    """How often `line` reaches a flop, as a share of all hands, each action weighted by its chart
    probability.

    The chart's own arrival at the decision that closed the street, times how often that
    decision is the line's action, times each later seat's fold. Every admitted line closes on
    the big blind, so nothing folds after it. A spot the chart never reaches, or an action it
    never offers there, is a line the chart never plays: zero, never an error."""
    decisions = _decisions(line)
    closing = max(index for index, (_, _, action) in enumerate(decisions) if action != "fold")
    position, before, action = decisions[closing]
    spot = _chart_spot(position, before)
    arrival = committed_chart()["arrival_ppb"].get(spot)
    if arrival is None:
        return 0.0
    reach = arrival / _PARTS_PER_BILLION * _action_rate(spot, action)
    for position, before, action in decisions[closing + 1 :]:
        if reach == 0.0:
            break
        later = _chart_spot(position, before)
        if later not in committed_chart()["action_weights"]:
            raise LineRangeError(f"{line}: the chart never decides {later}, so it cannot price it")
        reach *= _action_rate(later, action)
    return reach


def candidate_lines() -> tuple[str, ...]:
    """Every single-raised line the chart could play: one open and one call of it, from each spot
    the chart holds that faces exactly one raise. Three-bet pots are decision 9's exclusion."""
    found: list[str] = []
    for spot in committed_chart()["spots"]:
        sequence = spot["action_sequence"]
        if len(sequence) != 1 or sequence[0]["action"] != "raise":
            continue
        opener = PreflopAction(sequence[0]["position"], "raise", sequence[0]["size_bb"])
        found.append(f"{render_entry(opener)},{spot['hero_position']}:call")
    return tuple(found)


def ranked_lines() -> tuple[str, ...]:
    """The single-raised lines the chart plays, most often reached first. A line it never plays
    reaches a flop in no hand at all and ranks nowhere, however often its decision is asked: the
    chart's hijack facing a lojack open is asked often and offers no call to weight."""
    reached = [(line, line_reach(line)) for line in candidate_lines()]
    ordered = sorted((pair for pair in reached if pair[1] > 0.0), key=lambda pair: -pair[1])
    return tuple(line for line, _ in ordered)


# --------------------------------------------------------------------------- #
# Whose range is whose
# --------------------------------------------------------------------------- #


def heads_up_seats(line: str) -> tuple[str, str]:
    """The two seats a heads-up line leaves, out of position first, by who acts first after the
    flop - never by who raised. The opener is whichever live seat put chips in voluntarily first,
    the caller the other; `postflop_action_order` then sorts them, so the small blind's raise is
    out of position and every other opener is in position against the big blind."""
    actions = preflop_actions(line)
    closed = preflop_line_for(line, actions[-1].position)
    live = closed.live_positions
    if len(live) != _HEADS_UP:
        raise LineRangeError(f"{line} leaves {len(live)} seats in; a solve has two")
    opener = next(entry.position for entry in actions if entry.position in live)
    (caller,) = (position for position in live if position != opener)
    action_order = postflop_action_order(closed.table_size)
    oop_position, ip_position = sorted((opener, caller), key=action_order.index)
    return oop_position, ip_position


def _seat_range(line: str, position: str) -> dict[str, float]:
    """One live seat's range: per class, the product of the chart's weight for each action that
    seat took on the line, floored class-level. A single-raised line asks one decision a seat."""
    weights: dict[str, float] | None = None
    for seat, before, action in _decisions(line):
        if seat != position:
            continue
        spot = _chart_spot(seat, before)
        rows = committed_chart()["action_weights"].get(spot)
        if rows is None:
            raise LineRangeError(f"{line}: the committed chart holds no spot {spot}")
        offered = next(iter(rows.values()))
        if action not in offered:
            raise LineRangeError(
                f"{line}: the committed chart's {seat} at {spot} offers only {sorted(offered)},"
                f" so it has no range for a {action}"
            )
        taken = {hand: float(row[action]) for hand, row in rows.items()}
        weights = taken if weights is None else {h: weights[h] * w for h, w in taken.items()}
    if weights is None:
        raise LineRangeError(f"{line}: {position} makes no decision on this line")
    return floor_range(weights)


def line_ranges(line: str) -> LineRanges:
    """Both ranges of a heads-up line from the committed chart, by seat position after the flop,
    with the pot and the stack the completed preflop street leaves."""
    oop_position, ip_position = heads_up_seats(line)
    closed = preflop_line_for(line, oop_position)
    return LineRanges(
        line=line,
        oop_position=oop_position,
        ip_position=ip_position,
        range_oop=_seat_range(line, oop_position),
        range_ip=_seat_range(line, ip_position),
        starting_pot=closed.pot_bb,
        effective_stack=closed.effective_stack_bb,
    )


def seat_labels(line: str) -> dict[int, str]:
    """GTOpen's two players as this repo's positions, the map a harvest reads a node through:
    player 0 is out of position and player 1 in position, as `/api/spot` defines them."""
    oop_position, ip_position = heads_up_seats(line)
    return {OOP_PLAYER: oop_position, IP_PLAYER: ip_position}


# --------------------------------------------------------------------------- #
# What a campaign solve posts, and what it must hold
# --------------------------------------------------------------------------- #


def gtopen_range_text(weights: Mapping[str, float]) -> str:
    """One range in GTOpen's syntax, class-level: `AKs` at full weight, `AKs:0.5` otherwise.

    The rule `scripts/solve_postflop_sample.py`'s `range_text` wrote every committed solve with.
    Never per combo: one suit-specific entry collapses the solver's isomorphism group to the
    identity and forfeits the saving on every non-rainbow board."""
    parts = []
    for hand, weight in weights.items():
        parts.append(hand if weight >= 1.0 else f"{hand}:{weight:.4f}".rstrip("0").rstrip("."))
    return ",".join(parts)


def _canonical(board: Sequence[str]) -> tuple[str, ...]:
    cards = tuple(board)
    if canonical_board(cards) != cards:
        raise LineRangeError(
            f"{list(cards)} is not its class's representative, {list(canonical_board(cards))} is;"
            " a solve is posted on the representative so its cells need no relabelling"
        )
    return cards


def plan_for(line: str, board: Sequence[str]) -> SolvePlan:
    """The solve plan for one admitted line on one flop: its two ranges in their seats, its pot
    and stack, and decision 10's configuration unchanged."""
    if line not in ADMITTED_LINES:
        raise LineRangeError(f"{line} is not one of decision 9's admitted lines {ADMITTED_LINES}")
    cards = _canonical(board)
    ranges = line_ranges(line)
    named = "".join(cards)
    return SolvePlan(
        label=f"srp-{ranges.oop_position.lower()}-v-{ranges.ip_position.lower()}-{named}",
        board=named,
        preflop_line=preflop_line_for(line, ranges.oop_position).rendered,
        range_oop=gtopen_range_text(ranges.range_oop),
        range_ip=gtopen_range_text(ranges.range_ip),
        starting_pot=ranges.starting_pot,
        effective_stack=ranges.effective_stack,
        config=solve_config_document(),
    )


def price_substitutions(line: str) -> tuple[tuple[str, float, float], ...]:
    """Each raise on the line as a cell records it, `(position, actual_bb, solved_bb)`: a campaign
    solve is posted at the line's own prices, so actual and solved agree for every opener - the
    small blind's line records the small blind's raise, never the button's."""
    return tuple(
        (entry.position, float(entry.size_bb or 0.0), float(entry.size_bb or 0.0))
        for entry in preflop_actions(line)
        if entry.action == "raise"
    )


def flop_spot_keys(line: str, board: Sequence[str]) -> list[str]:
    """The spot key of every flop decision point one solve of `line` holds on `board`, both seats,
    in the tree's own depth-first order. The board changes only the key's board segment, so the
    tree is walked once per line, by `flop_decision_points`, and each key is derived here."""
    cards = _canonical(board)
    return [
        postflop_spot_key(hero, cards, history, hero.pot_bb, hero.effective_stack_bb)
        for hero, history in flop_decision_points(line)
    ]


@cache
def flop_decision_points(line: str) -> tuple[tuple[PreflopLine, tuple[FlopAction, ...]], ...]:
    """Every flop decision point one solve of `line` builds: the seat deciding, as its completed
    preflop line, and the flop actions before it.

    Walked rather than listed: GTOpen's tree rule, `postflop_tree_rule.TreeCounter.legal_actions`,
    over decision 10's configuration at the line's own pot and stack, down every flop action that
    leaves a flop decision to make. Each step is named the way the harvest names it - a bet by
    `size_pct` against the pot as it stood, a raise by `raise_multiplier` against the level it
    faced - so a raise the menu does not hold, a clamp to all-in say, refuses here as it would
    there."""
    labels = seat_labels(line)
    heroes = {player: preflop_line_for(line, label) for player, label in labels.items()}
    closed = heroes[OOP_PLAYER]
    menu = menu_from_config(solve_config_document())
    counter = TreeCounter(
        closed.pot_bb, closed.effective_stack_bb, menu, carry_aggressor_through_checks=False
    )
    half = closed.pot_bb / 2.0
    root = _State(ROOT_STREET, OOP_PLAYER, (half, half), (0.0, 0.0), 0.0, 0, None, False)
    points: list[tuple[PreflopLine, tuple[FlopAction, ...]]] = []

    def visit(state: _State, history: tuple[FlopAction, ...]) -> None:
        points.append((heroes[state.to_act], history))
        me, opp = state.to_act, 1 - state.to_act
        for kind, to in counter.legal_actions(state):
            if kind in _FLOP_STREET_ENDS or (kind == "check" and state.checked):
                continue
            put, street_bet = list(state.put), list(state.street_bet)
            raises = state.num_raises
            if kind == "check":
                step = FlopAction(labels[me], "check")
            elif kind == "bet":
                step = FlopAction(labels[me], "bet", size_pct(to - street_bet[me], sum(put)))
            else:
                step = FlopAction(
                    labels[me], "raise", multiplier=raise_multiplier(to, street_bet[opp])
                )
                raises += 1
            increment = 0.0 if kind == "check" else to - max(street_bet[opp], street_bet[me])
            if kind != "check":
                put[me] += to - street_bet[me]
                street_bet[me] = to
            child = _State(
                state.street,
                opp,
                (put[0], put[1]),
                (street_bet[0], street_bet[1]),
                max(increment, state.last_increment),
                raises,
                state.last_aggressor,
                state.checked or kind == "check",
            )
            visit(child, (*history, step))

    visit(root, ())
    return tuple(points)
