"""Six texture groups over the 1,755 canonical flop classes, and a line's cost projected on them.

A texture group is a property of a class, not of a dressing: it reads only how many distinct ranks
and how many distinct suits the board holds, and no relabelling of suits changes either. So the
group is read off the class representative `postflop_isomorphism.canonical_board` gives, and the
classes and flops each group holds are counted by walking all 22,100 flops through that one
canonicaliser rather than by a second definition of what a class is.

The projection is how the report prices one closed line from six timed solves: each group's cost is
the cost of one class, and the line costs that times the classes in the group, summed. Five groups
priced is not a line priced, so a projection missing a group is refused rather than summed short.
"""

from __future__ import annotations

import itertools
from collections import Counter
from collections.abc import Mapping, Sequence
from functools import cache
from types import MappingProxyType

from poker_training_bot.poker_core.cards import RANKS, SUITS
from poker_training_bot.solver_artifacts.postflop_isomorphism import (
    CANONICAL_FLOP_CLASSES,
    FLOP_CARDS,
    canonical_board,
)

RAINBOW_UNPAIRED = "rainbow unpaired"
TWO_TONE_UNPAIRED = "two-tone unpaired"
RAINBOW_PAIRED = "rainbow paired"
TWO_TONE_PAIRED = "two-tone paired"
MONOTONE = "monotone"
TRIPS = "trips"

TEXTURE_GROUPS = (
    RAINBOW_UNPAIRED,
    TWO_TONE_UNPAIRED,
    RAINBOW_PAIRED,
    TWO_TONE_PAIRED,
    MONOTONE,
    TRIPS,
)
"""In the contract's order."""

_GROUP_BY_SHAPE = {
    (3, 3): RAINBOW_UNPAIRED,
    (3, 2): TWO_TONE_UNPAIRED,
    (3, 1): MONOTONE,
    (2, 3): RAINBOW_PAIRED,
    (2, 2): TWO_TONE_PAIRED,
    (1, 3): TRIPS,
}
"""Distinct ranks and distinct suits to group. A paired board cannot be one suit and trips must be
three suits, so these six are every shape a flop can have."""


def texture_group(board: Sequence[str]) -> str:
    """The texture group of a flop's class."""
    representative = canonical_board(board)
    shape = (len({card[0] for card in representative}), len({card[1] for card in representative}))
    return _GROUP_BY_SHAPE[shape]


@cache
def _flops_per_class() -> Mapping[tuple[str, ...], int]:
    """Every three-card flop counted under the class representative it canonicalises to."""
    deck = tuple(rank + suit for rank in RANKS for suit in SUITS)
    counted = Counter(canonical_board(flop) for flop in itertools.combinations(deck, FLOP_CARDS))
    if len(counted) != CANONICAL_FLOP_CLASSES:
        raise AssertionError(
            f"the deck canonicalised to {len(counted)} classes, not {CANONICAL_FLOP_CLASSES}"
        )
    return MappingProxyType(dict(counted))


def flops_in_class(board: Sequence[str]) -> int:
    """How many of the 22,100 flops the board's class stands for."""
    return _flops_per_class()[canonical_board(board)]


def group_class_counts() -> dict[str, int]:
    """Canonical classes per texture group, in the contract's order."""
    counts = Counter(texture_group(board) for board in _flops_per_class())
    return {group: counts[group] for group in TEXTURE_GROUPS}


def group_flop_counts() -> dict[str, int]:
    """Flops per texture group, in the contract's order."""
    counts: Counter[str] = Counter()
    for board, flops in _flops_per_class().items():
        counts[texture_group(board)] += flops
    return {group: counts[group] for group in TEXTURE_GROUPS}


def project_line_cost(costs_per_class: Mapping[str, float]) -> float:
    """One line's cost from one cost per texture group, each weighted by the classes the group
    holds. Every group must be priced and no other key may appear: a missing group would project
    a line without its share of the flops, and an unknown one is a misspelt group."""
    unknown = sorted(set(costs_per_class) - set(TEXTURE_GROUPS))
    if unknown:
        raise ValueError(f"no such texture group: {unknown}")
    missing = [group for group in TEXTURE_GROUPS if group not in costs_per_class]
    if missing:
        raise ValueError(f"a line's cost needs every texture group priced; missing {missing}")
    classes = group_class_counts()
    return sum(classes[group] * float(costs_per_class[group]) for group in TEXTURE_GROUPS)
