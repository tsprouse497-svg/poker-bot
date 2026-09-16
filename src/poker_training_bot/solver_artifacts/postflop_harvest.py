"""What a solved GTOpen node becomes once hero's suits are collapsed: one committed cell.

The produce side of `postflop_artifact`, which is the consume side. That module says what a
committed cell must survive; this one builds a payload that survives it, out of what
`POST /api/node` answers after a solve. Nothing here opens a socket, starts a server or decides
what to solve: a caller hands it a node payload that has already come back, and
`scripts/solve_postflop_sample.py` is the caller that has one.

**The collapse is the whole of the work, and it is hero's hand rather than the board.** GTOpen
answers per *combo* - 272 of them for a floored big-blind range on `9c8c7c` - and a committed
cell is keyed by *class*, because the board's own stabiliser makes `AhKh` and `AdKd` the same
hand against the same board. `postflop_isomorphism.canonical_hole_cards` is the one producer of
that label here, exactly as it is at the table, so a cell cannot be written under labels the
lookup will never ask for.

**Two combos of one class are checked against each other rather than averaged.** The solver
exploits the same symmetry internally and `/api/node` calls `ensure_symmetric` before it
answers, so the rows of one class are a *prediction* this module can test: they must agree. They
are compared and a disagreement above `CLASS_AGREEMENT_TOLERANCE` refuses the cell, because a
mean over two rows that should have been equal is a number with no solve behind it and nothing
downstream could tell it from one that had. The largest divergence actually seen travels back on
the result so a run reports it rather than assuming it was zero.

**Weights are rounded once, in thousandths, and the residue is paid by the largest entry.**
Decision 6's lean JSON is three-decimal floats; the importer needs every row to sum to one
inside `WEIGHT_SUM_TOLERANCE`, which is 1e-6 and far tighter than a third decimal. Rounding each
entry independently misses that by up to half a thousandth per action, so the rounding is done
in integers and the difference from 1,000 is taken off whichever entry can afford it.

**What this module will not do.** It does not invent a class hero's range does not hold: a cell
carries the classes the solve actually answered for, and a board's full class count - 344 on
`9c8c7c`, 721 on `8c8d3c`, 1,176 on `Kh7d2c` - is what the *deck* collapses to, not what a
floored range reaches. It does not name the preflop line, pick a board, or choose which node is
worth committing; those are the campaign's and they arrive as arguments.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from poker_training_bot.solver_artifacts.postflop_artifact import (
    CELL_SCHEMA_VERSION,
    check_size_is_playable,
)
from poker_training_bot.solver_artifacts.postflop_isomorphism import (
    board_suit_map,
    canonical_board,
    canonical_hole_cards,
)
from poker_training_bot.solver_artifacts.postflop_key import (
    FlopAction,
    PreflopLine,
    postflop_spot_key,
)
from poker_training_bot.solver_artifacts.postflop_sizing import CellAction
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.solve_conditions import BlindStructure

WEIGHT_SCALE = 1000
"""Thousandths. Decision 6's lean JSON is three-decimal floats, and rounding in integers is what
lets the residue be paid once rather than accumulate one half-thousandth per action."""

CLASS_AGREEMENT_TOLERANCE = 5e-4
"""How far two combos of one suit-isomorphism class may disagree before the cell is refused.

Half a thousandth: below the third decimal the cell is written to, so anything this tolerates
cannot change a committed number, and anything it refuses would have. It is not a fudge for a
solver that answers asymmetrically - `ensure_symmetric` runs before every `/api/node` answer, so
a real divergence here says the group the server used is not the group the table will use, and
that is a refusal rather than a rounding."""

OOP_PLAYER = 0
IP_PLAYER = 1
"""GTOpen's two seats. `players[0]` is out of position and `players[1]` in position, which is
fixed by `/api/spot`'s own `range_oop` and `range_ip` fields rather than inferred here."""

SIZED_ACTIONS = frozenset({"bet", "raise"})
ACTION_KINDS = ("fold", "check", "call", "bet", "raise")
"""Every `kind` `ActionView` emits, read off `crates/solver/src/query.rs`. There is no separate
jam kind: an all-in bet comes back as a `bet` whose amount is the stack, which is why the
committed vocabulary needs no sixth name."""

CARD_RANKS = "23456789TJQKA"
CARD_SUITS = "cdhs"
_CARD_CHARS = 2
_HOLE_CARDS = 2

SIZE_PCT_DECIMALS = 2
FLOAT_NOISE = 1e-9
"""A key renders a size to a hundredth and `render_size_bb` refuses anything finer rather than
rounding it into a neighbouring cell. The solver's own bet is a configured percent of the pot -
33% of 5.5 is 1.8150000000000002 in binary - so the percent read back off it comes to
`33.00000000000001`, which is the hundredth it was configured as wearing a float's tail. It is
recovered rather than rounded: the value is taken to a hundredth and refused unless the
difference is inside `FLOAT_NOISE`, which a genuinely off-menu size is not."""


class HarvestError(ValueError):
    """A refusal to build a cell out of a node. Every one of these fires before anything is
    written, because a cell that disagrees with its own solve is worse than no cell."""


@dataclass(frozen=True)
class HarvestedNode:
    """One solved decision node, in the repo's vocabulary rather than the solver's.

    `class_divergence` is the largest disagreement seen between two combos of one class, kept
    because a run that reports zero and a run that never looked read the same otherwise.
    """

    actions: tuple[CellAction, ...]
    hand_classes: tuple[str, ...]
    class_weights: tuple[tuple[float, ...], ...]
    flop_actions: tuple[FlopAction, ...]
    hero_street_bet_bb: float
    combos: int
    class_divergence: float
    zero_reach_classes: int


# --------------------------------------------------------------------------- #
# Reading one node
# --------------------------------------------------------------------------- #


def _field(payload: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in payload or payload[key] is None:
        raise HarvestError(
            f"{where} answered without {key}, so nothing built from it is a measurement"
        )
    return payload[key]


def combo_cards(combo: str) -> tuple[str, str]:
    """GTOpen's `"AhKd"` as this repo's two cards, refusing anything that is not two of them."""
    if not isinstance(combo, str) or len(combo) != _CARD_CHARS * _HOLE_CARDS:
        raise HarvestError(f"a combo is four characters, got {combo!r}")
    cards = (combo[:_CARD_CHARS], combo[_CARD_CHARS:])
    for card in cards:
        if card[0] not in CARD_RANKS or card[1] not in CARD_SUITS:
            raise HarvestError(f"{combo!r} holds {card!r}, which is not a card this repo deals")
    return cards


def node_actions(node: Mapping[str, Any]) -> tuple[CellAction, ...]:
    """The node's action menu, each entry carrying its own raise-to level in big blinds.

    **A record per entry rather than names beside a parallel array of sizes.** Decision 11's flop
    menu puts two entries called `bet` on hero's node, and a list of names cannot say which is
    which; the 2026-09-16 schema repair carries the measurement.

    `amount` on a `Bet` or a `Raise` is the level the acting seat's street contribution goes
    **to**, not what it adds - read off `action_views` in `crates/solver/src/query.rs` and
    confirmed on the wire, where a 33% bet into 5.5 shows `put` moving to 4.565 against a 2.75
    baseline. That is the same unit `check_size_is_playable` compares and the same one a committed
    entry's `size_bb` carries, so nothing is converted between here and the importer.
    """
    built: list[CellAction] = []
    for index, entry in enumerate(_field(node, "actions", "/api/node")):
        kind = str(_field(entry, "kind", f"/api/node actions[{index}]"))
        if kind not in ACTION_KINDS:
            raise HarvestError(f"/api/node offered action kind {kind!r}, which is not playable")
        size = None
        if kind in SIZED_ACTIONS:
            size = float(_field(entry, "amount", f"/api/node actions[{index}]"))
        built.append(CellAction(kind, size))
    if not built:
        raise HarvestError("/api/node answered a node with no actions, so hero decides nothing")
    return tuple(built)


def size_pct(added_bb: float, pot_bb: float) -> float:
    """One flop size as the percent of pot a key can name, or a refusal.

    Taken to a hundredth and checked back against what was read, so a configured 33% arriving as
    `33.00000000000001` is recovered and a size that is genuinely not a hundredth of a percent -
    a jam, say, or a menu nobody committed - is refused here rather than rounded into the cell
    next door. `render_size_bb` makes the same refusal one layer down and this one names the
    solver's own number, which is what a reader needs to see.
    """
    raw = 100.0 * added_bb / pot_bb
    snapped = round(raw, SIZE_PCT_DECIMALS)
    if abs(snapped - raw) > FLOAT_NOISE:
        raise HarvestError(
            f"a size of {added_bb} into a pot of {pot_bb} is {raw}% of it, which is not a"
            " hundredth of a percent and so is not a size this key can name. Refused rather"
            " than rounded onto a neighbouring cell"
        )
    return snapped


def flop_line(
    node: Mapping[str, Any], seat_of_player: Mapping[int, str], starting_pot_bb: float
) -> tuple[tuple[FlopAction, ...], float]:
    """The flop as it stands at this node, and what hero already has out on the street.

    Built from the node's own `history` rather than from the path the caller asked for, so the
    committed line is what the server says happened. A flop size is a percent of the pot **as it
    stood when it went in**, which is the unit `postflop_key` renders and `postflop_sizing` walks
    forward, so each percent is taken against that step's own pot.

    `put` counts the whole hand, blinds included, and the solver splits the starting pot evenly
    between the two seats, so a seat's street contribution is its `put` less half that pot.
    """
    history = list(_field(node, "history", "/api/node"))
    if not history:
        raise HarvestError("/api/node answered with no history, so no flop line can be named")
    baseline = starting_pot_bb / 2.0
    street: dict[int, float] = {}
    built: list[FlopAction] = []
    for step in history[:-1]:
        player = int(_field(step, "player", "/api/node history"))
        if player not in seat_of_player:
            raise HarvestError(f"/api/node history names seat {player}, which the plan omits")
        pot = float(_field(step, "pot", "/api/node history"))
        menu = _field(step, "actions", "/api/node history")
        chosen = int(_field(step, "chosen", "/api/node history"))
        if not 0 <= chosen < len(menu):
            raise HarvestError(f"/api/node history chose action {chosen} of {len(menu)}")
        entry = menu[chosen]
        kind = str(_field(entry, "kind", "/api/node history"))
        standing = street.get(player, 0.0)
        if kind in SIZED_ACTIONS:
            level = float(_field(entry, "amount", "/api/node history"))
            if pot <= 0:
                raise HarvestError("a flop action priced against a pot of zero is no percent")
            built.append(
                FlopAction(seat_of_player[player], kind, size_pct(level - standing, pot))
            )
            street[player] = level
        else:
            if kind == "call":
                street[player] = max(street.values(), default=0.0)
            built.append(FlopAction(seat_of_player[player], kind))
    hero = int(_field(history[-1], "player", "/api/node history"))
    if hero not in seat_of_player:
        raise HarvestError(f"/api/node has seat {hero} deciding, which the plan omits")
    put = list(_field(node, "put", "/api/node"))
    return tuple(built), float(put[hero]) - baseline


# --------------------------------------------------------------------------- #
# The collapse
# --------------------------------------------------------------------------- #


def _rounded(row: Sequence[float]) -> tuple[float, ...]:
    """One strategy row in thousandths, summing to exactly one.

    The residue is taken off the largest entry rather than spread, because spreading it can push
    a second entry across a third decimal it was nowhere near and the largest is the one a half
    thousandth cannot make negative."""
    scaled = [round(float(weight) * WEIGHT_SCALE) for weight in row]
    if any(value < 0 for value in scaled):
        raise HarvestError(f"a solved row holds a negative frequency: {list(row)}")
    drift = WEIGHT_SCALE - sum(scaled)
    largest = max(range(len(scaled)), key=lambda index: (scaled[index], -index))
    scaled[largest] += drift
    if scaled[largest] < 0:
        raise HarvestError(f"a solved row is too far from summing to one to round: {list(row)}")
    return tuple(value / WEIGHT_SCALE for value in scaled)


def collapse_hero_strategy(
    board: Sequence[str],
    hands: Sequence[Mapping[str, Any]],
    action_count: int,
    tolerance: float = CLASS_AGREEMENT_TOLERANCE,
) -> tuple[tuple[str, ...], tuple[tuple[float, ...], ...], float, int]:
    """Hero's per-combo strategy as per-class strategy, or a refusal naming the class.

    Returns the classes in the order they were first met, their rounded rows, the largest
    disagreement seen inside any class, and how many classes hero reaches with no probability at
    all. That last count is reported rather than filtered: a zero-reach class is a hand hero's
    own committed strategy never brings here, so its row is unexercised rather than wrong, and
    dropping it would refuse at a table any seat that arrived off this policy.
    """
    seen: dict[str, list[list[float]]] = {}
    reach: dict[str, float] = {}
    for hand in hands:
        cards = combo_cards(str(_field(hand, "combo", "/api/node hands")))
        raw = _field(hand, "strategy", "/api/node hands")
        row = [float(value) for value in raw]
        if len(row) != action_count:
            raise HarvestError(
                f"{''.join(cards)} carries {len(row)} weights against {action_count} actions"
            )
        label = "".join(canonical_hole_cards(board, cards))
        seen.setdefault(label, []).append(row)
        reach[label] = reach.get(label, 0.0) + float(hand.get("reach") or 0.0)
    if not seen:
        raise HarvestError("/api/node answered no hands for the acting seat, so hero has no range")
    divergence = 0.0
    for label, rows_held in seen.items():
        gap = _widest_gap(rows_held)
        divergence = max(divergence, gap)
        if gap > tolerance:
            raise HarvestError(
                f"the {len(rows_held)} combos of class {label} disagree by {gap:.6f}, over the"
                f" {tolerance} two dresses of one hand may differ by. The solve's suit group is"
                " not the group the table collapses under, so the cell is refused rather than"
                " averaged into a number no solve produced"
            )
    classes = tuple(seen)
    rows = tuple(_rounded(seen[label][0]) for label in classes)
    unreached = sum(1 for label in classes if reach[label] <= 0.0)
    return classes, rows, divergence, unreached


def _widest_gap(rows: Sequence[Sequence[float]]) -> float:
    """The largest disagreement between any two rows of one class, over every pair.

    Every pair rather than every row against the first: a fixed reference under-reports by up to
    half, and the number this returns is the one a run publishes as evidence that the collapse
    held. A class has at most six members - the largest stabiliser a flop has - so the pairs are
    free."""
    widest = 0.0
    for index, one in enumerate(rows):
        for two in rows[index + 1 :]:
            widest = max(widest, max(abs(a - b) for a, b in zip(one, two, strict=True)))
    return widest


def harvest_node(
    node: Mapping[str, Any],
    board: Sequence[str],
    seat_of_player: Mapping[int, str],
    starting_pot_bb: float,
    tolerance: float = CLASS_AGREEMENT_TOLERANCE,
) -> HarvestedNode:
    """One `/api/node` answer as the parts of a committed cell."""
    representative = canonical_board(board)
    if tuple(board) != representative:
        raise HarvestError(
            f"{list(board)} is not the representative of its class, {list(representative)} is."
            " A solve is posted on the representative so hero's combos come back already in the"
            " dressing a committed cell is written in"
        )
    if str(_field(node, "node_type", "/api/node")) != "action":
        raise HarvestError(f"/api/node answered a {node['node_type']!r} node, where nobody acts")
    actor = int(_field(node, "player", "/api/node"))
    actions = node_actions(node)
    players = _field(node, "players", "/api/node")
    hands = _field(players[actor], "hands", "/api/node players")
    classes, rows, divergence, unreached = collapse_hero_strategy(
        representative, hands, len(actions), tolerance
    )
    line, street_bet = flop_line(node, seat_of_player, starting_pot_bb)
    return HarvestedNode(
        actions=actions,
        hand_classes=classes,
        class_weights=rows,
        flop_actions=line,
        hero_street_bet_bb=street_bet,
        combos=len(hands),
        class_divergence=divergence,
        zero_reach_classes=unreached,
    )


# --------------------------------------------------------------------------- #
# The document a cell is committed as
# --------------------------------------------------------------------------- #


def strategy_digest(
    hand_classes: Sequence[str], class_weights: Sequence[Sequence[float]]
) -> str:
    """A sha256 over hero's committed strategy alone, taken on the rounded numbers.

    On the rounded ones deliberately: the digest authenticates the bytes a reader can recompute
    it from, so a digest over the solver's f32 tail would be a claim about something the repo
    does not hold. `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES` owns the fact that
    nothing in the gate re-derives it; this at least makes it re-derivable by hand.
    """
    payload = json.dumps(
        [list(hand_classes), [list(row) for row in class_weights]],
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _action_entries(entries: Sequence[PreflopAction]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    for entry in entries:
        item: dict[str, Any] = {"position": entry.position, "action": entry.action}
        if entry.size_bb is not None:
            item["size_bb"] = float(entry.size_bb)
        built.append(item)
    return built


def _menu_entries(entries: Sequence[CellAction]) -> list[dict[str, Any]]:
    """Hero's own menu as JSON: one object an entry, its size beside its name rather than in a
    parallel array the importer would have to line up by position again."""
    built: list[dict[str, Any]] = []
    for entry in entries:
        item: dict[str, Any] = {"action": entry.name}
        if entry.size_bb is not None:
            item["size_bb"] = float(entry.size_bb)
        built.append(item)
    return built


def _flop_entries(entries: Sequence[FlopAction]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    for entry in entries:
        item: dict[str, Any] = {"position": entry.position, "action": entry.action}
        if entry.size_pct is not None:
            item["size_pct"] = float(entry.size_pct)
        built.append(item)
    return built


def cell_document(
    harvested: HarvestedNode,
    *,
    preflop_line: PreflopLine,
    board: Sequence[str],
    blinds: BlindStructure,
    price_substitutions: Sequence[tuple[str, float, float]],
    achieved_exploitability_pct_of_pot: float,
    iterations: int,
) -> dict[str, Any]:
    """The committed cell as JSON, in the shape `import_postflop_cell` re-derives.

    Every field the importer checks is produced here from the same producer the importer uses -
    `postflop_spot_key` for the key, `canonical_board` and `board_suit_map` for the dressing,
    the line's own pot and stack - so a mismatch at import is a real disagreement rather than
    two spellings of one fact. The sizes are proved playable here as well, because a cell that
    cannot be played is cheaper to refuse before it is written than after.
    """
    representative = canonical_board(board)
    behind = preflop_line.effective_stack_bb - harvested.hero_street_bet_bb
    for action in harvested.actions:
        if action.size_bb is not None:
            check_size_is_playable(
                action.size_bb, harvested.hero_street_bet_bb, behind, cell=preflop_line.rendered
            )
    key = postflop_spot_key(
        preflop_line,
        representative,
        harvested.flop_actions,
        preflop_line.pot_bb,
        preflop_line.effective_stack_bb,
    )
    return {
        "cell_schema_version": CELL_SCHEMA_VERSION,
        "spot_key": key,
        "board": list(representative),
        "suit_map": board_suit_map(representative),
        "preflop_line": preflop_line.rendered,
        "table_size": preflop_line.table_size,
        "stack_depth_bb": preflop_line.stack_depth_bb,
        "hero_position": preflop_line.hero_position,
        "blind_structure": {
            "small_blind_bb": blinds.small_blind_bb,
            "big_blind_bb": blinds.big_blind_bb,
            "ante_bb": blinds.ante_bb,
        },
        "preflop_actions": _action_entries(preflop_line.actions),
        "price_substitutions": [
            {"position": position, "actual_bb": actual, "solved_bb": solved}
            for position, actual, solved in price_substitutions
        ],
        "pot_bb": preflop_line.pot_bb,
        "effective_stack_bb": preflop_line.effective_stack_bb,
        "flop_actions": _flop_entries(harvested.flop_actions),
        "hero_street_bet_bb": harvested.hero_street_bet_bb,
        "actions": _menu_entries(harvested.actions),
        "hand_classes": list(harvested.hand_classes),
        "class_weights": [list(row) for row in harvested.class_weights],
        "achieved_exploitability_pct_of_pot": float(achieved_exploitability_pct_of_pot),
        "iterations": int(iterations),
    }
