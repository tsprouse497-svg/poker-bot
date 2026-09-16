"""The one collapse this phase permits: suits, over the board and hero's hand together.

Split out of `postflop_key` rather than written fresh. It is the whole of decision 2's permitted
abstraction and it is the one piece of that module a wrong answer reaches a student by, so it
gets its own file and its own tests. `postflop_key` re-exports every public name here, so a
caller that asks the key producer for `canonical_board` still gets this.

**A representative is a minimum over a group, not a single relabelling.** A board becomes the
smallest member of its suit-isomorphism class under the 24 relabellings of four suits. More than
one relabelling usually reaches that minimum: a flop uses at most three suits, so the suits it
does not use permute freely, and a board whose own suits are interchangeable adds more. The set
of relabellings that reach the representative is the board's **stabiliser**, and it is 1 on a
rainbow flop, 2 on a two-tone or paired-two-tone one and 6 on a monotone one.

**Which is why hero's hand is minimised rather than mapped.** An earlier draft carried hero's two
cards by one published permutation and stopped. That is exact only when the stabiliser is
trivial. On `8c8d3c` the stabiliser swaps the two suits the board never uses, so `Ah7s` and
`As7h` are the same hand played against the same board and were given two different class labels;
910 of that board's 1,176 combos moved with the dressing, and 1,131 of 1,176 on `9c8c7c`. The
consequence was not cosmetic. Decision 6 sizes the committed cell at 1,286,792 hero-combo classes
over all 1,755 flops, which is the count **after** the stabiliser collapses them, so a table
emitting 1,176 labels per flop either asks a cell for labels it does not hold - refusing 38.7% of
hero's combos on `8c8d3c` and 70.7% on `9c8c7c`, on a spot the artifact covers - or costs the
1.6x the byte model already spent. `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`.

So `canonical_hole_cards` takes the smallest image of hero's hand over the whole stabiliser. The
property that makes it a class label, and the one to test it by, is invariance: relabel the board
and the hand by any suit permutation at all and the answer does not move.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import cache
from itertools import permutations

_RANKS = "23456789TJQKA"
_SUITS = "cdhs"
_DECK = frozenset(rank + suit for rank in _RANKS for suit in _SUITS)

FLOP_CARDS = 3
HOLE_CARDS = 2

CANONICAL_FLOP_CLASSES = 1755
"""How many suit-isomorphism classes the 22,100 three-card boards fall into.

Not tabulated and not read: it is what `canonical_board` produces over the whole deck, counted.
Recomputed from the 52 cards by `tests/test_postflop_key.py::TestTheOnePermittedCollapse`,
which also checks the class sizes against the three orbit sizes, so a canonicaliser that
over-collapsed would show up as a class of the wrong size long before any strategy was wrong."""

# The 24 relabellings of four suits. Suit isomorphism is the whole of the permitted collapse,
# so the group is written out once and minimised over, rather than a texture being classified
# by hand into rainbow, two-tone and monotone - a classification is a second rule that can
# disagree with the first.
SUIT_PERMUTATIONS: tuple[dict[str, str], ...] = tuple(
    dict(zip(_SUITS, order, strict=True)) for order in permutations(_SUITS)
)


def _validated_board(board: Sequence[str]) -> tuple[str, ...]:
    cards = tuple(board)
    if len(cards) != FLOP_CARDS:
        raise ValueError(f"a flop is exactly {FLOP_CARDS} cards, got {len(cards)}: {cards!r}")
    for card in cards:
        if card not in _DECK:
            raise ValueError(f"board holds a card that is not in the deck: {card!r}")
    if len(set(cards)) != FLOP_CARDS:
        raise ValueError(f"board holds the same card twice: {cards!r}")
    return cards


_Image = tuple[tuple[str, ...], tuple[tuple[tuple[str, str], ...], ...]]


@cache
def _smallest_image(board: tuple[str, ...]) -> _Image:
    """The smallest relabelling of `board`, and **every** permutation that produces it.

    All of it comes out of one minimisation on purpose: computed separately the representative
    and the maps could disagree, leaving no permutation for hero's cards to move under at all.
    The maps are returned as a tuple rather than the first of them because the stabiliser is
    what hero's hand is minimised over, and a caller wanting one map takes the first - ties
    break on `SUIT_PERMUTATIONS` order, so one class always publishes the same one."""
    best: tuple[str, ...] | None = None
    achieving: list[dict[str, str]] = []
    for mapping in SUIT_PERMUTATIONS:
        moved = tuple(sorted(card[0] + mapping[card[1]] for card in board))
        if best is None or moved < best:
            best, achieving = moved, [mapping]
        elif moved == best:
            achieving.append(mapping)
    assert best is not None
    return (
        tuple(sorted(best, key=_board_order)),
        tuple(tuple(mapping.items()) for mapping in achieving),
    )


def _board_order(card: str) -> tuple[int, int]:
    """Highest rank first, then by suit - the order a flop is written and read in. The
    minimisation above compares card text, which puts `2c7dKh` ahead of `Kh7d2c`; which of the
    two is stored is free, because a key is compared and never taken apart, but which one a
    person reads off a refusal inventory is not."""
    return -_RANKS.index(card[0]), _SUITS.index(card[1])


def canonical_board(board: Sequence[str]) -> tuple[str, ...]:
    """The representative of `board`'s suit-isomorphism class, highest rank first. A member of
    the class rather than a label for it, so canonicalising the representative returns it and
    two dresses of one board - `Kc7d2h` and `Kh7s2c` - are one key. Two-tone `Kc7c2h` is not
    collapsed onto rainbow `Kc7d2h`: one holds a flush draw and the other does not, and no
    relabelling of four suits turns one into the other."""
    return _smallest_image(tuple(sorted(_validated_board(board))))[0]


def board_suit_maps(board: Sequence[str]) -> tuple[dict[str, str], ...]:
    """Every permutation of the four suits that carries `board` to its representative.

    The board's stabiliser composed with any one of them, which is the group hero's hand is
    minimised over. Published because a caller that moves a hand by one member of this set and
    stops has the bug this module exists to fix, and fresh dictionaries each call so a caller
    cannot reach into the cached answer."""
    return tuple(
        dict(mapping) for mapping in _smallest_image(tuple(sorted(_validated_board(board))))[1]
    )


def board_suit_map(board: Sequence[str]) -> dict[str, str]:
    """One permutation of the four suits that carries `board` to its representative.

    Kept for the board-level check the importer makes - a committed cell records the dressing it
    was written in, and one map settles whether that dressing reaches the representative. It is
    **not** enough to canonicalise a hand: see `canonical_hole_cards`, which minimises over all
    of `board_suit_maps` instead."""
    return board_suit_maps(board)[0]


def canonical_hole_cards(board: Sequence[str], hole_cards: Sequence[str]) -> tuple[str, ...]:
    """Hero's two cards as the smallest image of themselves over the board's whole stabiliser.

    The half a board-level isomorphism test cannot see, and the half one published permutation
    does not finish. On a two-tone board `AhQh` holds the flush draw and `AsQd` does not, so a
    map applied to the board but not to the hand serves one the other's strategy while every
    board-level check passes; and a map applied to the hand without minimising over the suits
    the board leaves free gives one hand two labels, which is the same failure wearing the
    opposite sign. The answer here is invariant under relabelling board and hand together, which
    is what makes it a class rather than a rendering.
    `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`."""
    cards = tuple(hole_cards)
    if len(cards) != HOLE_CARDS:
        raise ValueError(f"hero holds exactly two cards, got {len(cards)}: {cards!r}")
    table = _validated_board(board)
    for card in cards:
        if card not in _DECK:
            raise ValueError(f"hole_cards holds a card that is not in the deck: {card!r}")
        if card in table:
            raise ValueError(f"{card!r} is on the board and cannot also be in hero's hand")
    if cards[0] == cards[1]:
        raise ValueError(f"hero cannot hold the same card twice: {cards!r}")
    return min(
        tuple(sorted(card[0] + mapping[card[1]] for card in cards))
        for mapping in board_suit_maps(table)
    )
