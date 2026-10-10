"""What a flop solve holds, per line and per flop, from GTOpen's tree rule and nothing else.

The tree is counted by `postflop_tree_rule`, a port of the solver's own builder; this module turns
that count into the figures the campaign is planned on. None of it needs a solver or a board solve:
the tree's shape depends on the pot, the stack and the menu, and the board only removes combos. So a
line is one tree, and a flop is two combo counts against it.

- **What closes is what is stored (decision 1, re-ruled 2026-10-04): the flop and the turn.**
  `closure_counts` has no river key. The river the solve still builds is a tree figure, and it is
  split in two: `river_tree_points`, the 48 river cards under each of the 49 turn cards, and
  `unreachable_river_points`, the river GTOpen also builds under the turn card already dealt.
- **The planned arena is `entries * 8` bytes**, GTOpen's `arena_bytes` at full precision: a regret
  and a strategy arena of four-byte floats, where `entries` is each seat's action slots times that
  seat's live combos. The card-memory estimate is `vram_estimate_bytes` in `game.rs`, which adds a
  per-node staging buffer per hand and 512 MiB of slack.
- **The memory bar walks every one of the 22,100 flops**, not the 1,755 classes. The ranges are
  class-level, so the two walks agree, but the walk does not lean on that: it counts each flop.

Every figure carries the rule it was built under (decision 17), `carry_aggressor_through_checks`,
GTOpen's own `TreeConfig` field: false is the clone's tree and the campaign's, true the pin's. A
function that takes figures reads the rule off them rather than taking it again.

The ranges, the pot and the stack of a line come from `postflop_lines.line_ranges`, the same source
the driver's plan is built from, so the tree counted is the tree the plan posts.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType

from poker_training_bot.poker_core.cards import RANKS, SUITS
from poker_training_bot.solver_artifacts.hand_classes import hand_class, is_hand_class
from poker_training_bot.solver_artifacts.postflop_isomorphism import FLOP_CARDS, canonical_board
from poker_training_bot.solver_artifacts.postflop_lines import ADMITTED_LINES, line_ranges
from poker_training_bot.solver_artifacts.postflop_tree_rule import (
    CARDS_PER_CHANCE,
    committed_menu,
    count_tree,
)

TURN_CARDS = CARDS_PER_CHANCE
"""Turn cards a flop solve deals: every card but the three on the flop."""
RIVER_CARDS = CARDS_PER_CHANCE - 1
"""River cards that can follow one turn card. GTOpen builds one more, under the turn card itself."""

CLOSED_STREETS = ("flop", "turn")
"""The streets a solved board closes and the store keeps (decision 1, re-ruled 2026-10-04)."""

ARENAS = 2
"""A regret arena and a strategy arena, one entry each per action slot per live combo."""
F32_BYTES = 4
ARENA_BYTES_PER_ENTRY = ARENAS * F32_BYTES
VRAM_SLACK_BYTES = 512 * 1024 * 1024
"""`game.rs`'s allowance for the river and lock tables, on top of the staging buffers and arenas."""

_DECK = tuple(rank + suit for rank in RANKS for suit in SUITS)
_CARD_INDEX = {card: index for index, card in enumerate(_DECK)}


# --- The tree a line builds


@dataclass(frozen=True)
class TreeFigures:
    """One flop tree, counted: every node, the action nodes per street with out of position first,
    and each seat's action slots, which size the arena. The river is as `tree.rs` builds it, with
    the subtree under the already-dealt turn card still in its slot."""

    starting_pot: float
    effective_stack: float
    carry_aggressor_through_checks: bool
    nodes: int
    action_nodes: Mapping[str, tuple[int, int]]
    slots: tuple[int, int]


@cache
def build_tree_figures(
    starting_pot: float,
    effective_stack: float,
    *,
    carry_aggressor_through_checks: bool = False,
) -> TreeFigures:
    """The tree GTOpen builds for a flop-rooted spot at this pot and stack on the committed menu."""
    nodes, action_nodes, slots = count_tree(
        starting_pot,
        effective_stack,
        committed_menu(),
        carry_aggressor_through_checks=carry_aggressor_through_checks,
    )
    return TreeFigures(
        starting_pot=float(starting_pot),
        effective_stack=float(effective_stack),
        carry_aggressor_through_checks=carry_aggressor_through_checks,
        nodes=nodes,
        action_nodes=MappingProxyType(dict(action_nodes)),
        slots=slots,
    )


def line_tree_figures(line: str, *, carry_aggressor_through_checks: bool = False) -> TreeFigures:
    """The tree a preflop line builds, at the pot and stack the line itself arrives at."""
    ranges = line_ranges(line)
    return build_tree_figures(
        ranges.starting_pot,
        ranges.effective_stack,
        carry_aggressor_through_checks=carry_aggressor_through_checks,
    )


# --- What one solve closes, and the river it builds anyway


def closure_counts(figures: TreeFigures) -> dict[str, int]:
    """Decision points one flop's solve closes for both seats, per stored street. No river key:
    what is stored is what closes, and a closure with a river is a river someone keeps."""
    return {street: sum(figures.action_nodes[street]) for street in CLOSED_STREETS}


def river_tree_points(figures: TreeFigures) -> int:
    """River decision points a hand can reach: the 48 river cards under each of the 49 turn cards.

    Every turn card builds the same subtree and every river chance in it deals 49 cards, one of
    which is the turn card already on the board; those subtrees are built and never visited."""
    river_built = sum(figures.action_nodes["river"])
    if river_built % (TURN_CARDS * TURN_CARDS):
        raise ValueError(
            f"{river_built} river decision points do not split evenly over {TURN_CARDS} turn and"
            f" {TURN_CARDS} river chance cards; the tree is not a flop-rooted GTOpen tree"
        )
    river_kept = river_built // TURN_CARDS * RIVER_CARDS
    return river_kept


def unreachable_river_points(figures: TreeFigures) -> int:
    """River decision points GTOpen builds under the turn card already dealt, which never occur."""
    return sum(figures.action_nodes["river"]) - river_tree_points(figures)


# --- Live combos and the planned arena


@cache
def _combos_by_class() -> Mapping[str, tuple[tuple[int, int], ...]]:
    """Every two-card combo as deck indices, grouped by the hand class `hand_classes` names."""
    grouped: dict[str, list[tuple[int, int]]] = {}
    for first, second in itertools.combinations(range(len(_DECK)), 2):
        grouped.setdefault(hand_class((_DECK[first], _DECK[second])), []).append((first, second))
    return MappingProxyType({name: tuple(combos) for name, combos in grouped.items()})


def _range_combos(weights: Mapping[str, float]) -> tuple[tuple[int, int], ...]:
    """The combos GTOpen admits from a class-level range: every class with a weight above zero."""
    combos: list[tuple[int, int]] = []
    for hand, weight in weights.items():
        if not is_hand_class(hand):
            raise ValueError(f"range holds {hand!r}, which is not a hand class")
        if float(weight) > 0.0:
            combos.extend(_combos_by_class()[hand])
    return tuple(combos)


def live_combos(weights: Mapping[str, float], board: Sequence[str]) -> int:
    """Combos of the range that share no card with the board, as `game.rs` keeps a seat's hands."""
    blocked = {_CARD_INDEX[card] for card in board}
    if len(blocked) != len(tuple(board)):
        raise ValueError(f"board holds the same card twice: {tuple(board)!r}")
    return sum(1 for first, second in _range_combos(weights) if not {first, second} & blocked)


def planned_arena_bytes(figures: TreeFigures, oop_combos: int, ip_combos: int) -> int:
    """GTOpen's full-precision `arena_bytes`: each seat's slots times its live combos, eight bytes
    an entry."""
    entries = figures.slots[0] * oop_combos + figures.slots[1] * ip_combos
    return entries * ARENA_BYTES_PER_ENTRY


def vram_estimate_bytes(figures: TreeFigures, oop_combos: int, ip_combos: int) -> int:
    """GTOpen's `vram_estimate_bytes`: a per-node staging buffer of both seats' hands and the larger
    seat's again, four bytes each, plus the arenas and 512 MiB of slack."""
    staging = figures.nodes * (oop_combos + ip_combos + max(oop_combos, ip_combos)) * F32_BYTES
    return staging + planned_arena_bytes(figures, oop_combos, ip_combos) + VRAM_SLACK_BYTES


def planned_arena_for(
    line: str, board: Sequence[str], *, carry_aggressor_through_checks: bool = False
) -> int:
    """The arena one flop of one line plans, in the server's own unit."""
    ranges = line_ranges(line)
    figures = line_tree_figures(line, carry_aggressor_through_checks=carry_aggressor_through_checks)
    return planned_arena_bytes(
        figures, live_combos(ranges.range_oop, board), live_combos(ranges.range_ip, board)
    )


# --- The walk over every flop


@cache
def _all_flops() -> tuple[tuple[int, int, int], ...]:
    return tuple(itertools.combinations(range(len(_DECK)), FLOP_CARDS))


def _live_per_flop(weights: Mapping[str, float]) -> tuple[int, ...]:
    """Live combos on every flop, by inclusion and exclusion: the combos a flop blocks are those
    holding any of its three cards, less the combos counted twice for holding two of them."""
    combos = _range_combos(weights)
    per_card = [0] * len(_DECK)
    both: set[tuple[int, int]] = set()
    for first, second in combos:
        per_card[first] += 1
        per_card[second] += 1
        both.add((first, second))
    total = len(combos)
    return tuple(
        total
        - per_card[a]
        - per_card[b]
        - per_card[c]
        + ((a, b) in both)
        + ((a, c) in both)
        + ((b, c) in both)
        for a, b, c in _all_flops()
    )


@cache
def _line_live_combos(line: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Each seat's live combos on every flop, in `_all_flops` order. The rule does not enter."""
    ranges = line_ranges(line)
    return _live_per_flop(ranges.range_oop), _live_per_flop(ranges.range_ip)


@cache
def _line_arenas(line: str, carry_aggressor_through_checks: bool) -> tuple[int, ...]:
    figures = line_tree_figures(line, carry_aggressor_through_checks=carry_aggressor_through_checks)
    oop, ip = _line_live_combos(line)
    return tuple(planned_arena_bytes(figures, o, i) for o, i in zip(oop, ip, strict=True))


@dataclass(frozen=True)
class MemoryBar:
    """The largest planned arena over every flop of a line, the flop it falls on as its class
    representative, how many flops plan exactly that much, and that flop's card memory."""

    line: str
    board: tuple[str, ...]
    arena_bytes: int
    vram_bytes: int
    oop_combos: int
    ip_combos: int
    flops_at_bar: int
    carry_aggressor_through_checks: bool


def line_memory_bar(line: str, *, carry_aggressor_through_checks: bool = False) -> MemoryBar:
    """The largest planned arena over all 22,100 flops of one line. Ties are broken by deck order,
    and the board is reported as its class representative; `flops_at_bar` says how many tied."""
    arenas = _line_arenas(line, carry_aggressor_through_checks)
    largest = max(arenas)
    at = arenas.index(largest)
    oop, ip = _line_live_combos(line)
    figures = line_tree_figures(line, carry_aggressor_through_checks=carry_aggressor_through_checks)
    return MemoryBar(
        line=line,
        board=canonical_board(tuple(_DECK[card] for card in _all_flops()[at])),
        arena_bytes=largest,
        vram_bytes=vram_estimate_bytes(figures, oop[at], ip[at]),
        oop_combos=oop[at],
        ip_combos=ip[at],
        flops_at_bar=arenas.count(largest),
        carry_aggressor_through_checks=carry_aggressor_through_checks,
    )


def campaign_memory_bar(*, carry_aggressor_through_checks: bool = False) -> MemoryBar:
    """The largest line bar over every admitted line; ties go to the earlier line in the ruled
    order. Computed before any candidate is ranked, because it decides which machines can run."""
    bars = [
        line_memory_bar(line, carry_aggressor_through_checks=carry_aggressor_through_checks)
        for line in ADMITTED_LINES
    ]
    return max(bars, key=lambda bar: bar.arena_bytes)


def flops_planned_above(
    line: str, threshold_bytes: int, *, carry_aggressor_through_checks: bool = False
) -> int:
    """How many of the 22,100 flops plan an arena strictly above `threshold_bytes` on this line."""
    return sum(
        1 for arena in _line_arenas(line, carry_aggressor_through_checks) if arena > threshold_bytes
    )
