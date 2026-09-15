"""The postflop spot vocabulary: what a flop spot key says, and the one collapse it makes.

A sibling of `spot_key`, not an extension of it. The preflop key answers "which preflop
spot is this"; this one answers "which flop spot is this", and it carries the preflop key
whole rather than re-deriving or compressing it. Two vocabularies that shared a producer
would be one vocabulary with a branch in it, and a change to either half would move both.

What is borrowed from the preflop side is the *pattern*, which is the part that matters: a
key is **derived here and nowhere else, and compared rather than parsed**. This module
publishes no reader that takes a key apart, and a test in `tests/test_postflop_key.py`
asserts that by name. A parser would be a second answer to "what spot is this", and two
answers drift invisibly.

**The key does not begin with `t`.** `data_pipeline/self_play_reference.py` recovers preflop
keys from a rendered report by taking any whitespace token that starts with `t` and holds at
least three slashes, and a postflop key carries a preflop key verbatim inside it. Beginning
with `f` is what stops that reader claiming a flop spot as a preflop one. Decision 8.

**What the key names, and what it deliberately does not.** It names the canonical board, the
preflop line verbatim with its prices, every flop action so far with its bet size, the pot and
the effective stack. Naming the bet size is decision 9: a caller needs 19.9% equity against a
33% bet and 30.0% against a 75% one, so a key that merged them would overfold to small bets
and overcall large ones, and a later menu change makes the lookup fail closed instead of
silently answering a 50% bet out of a 33% cell. Naming the pot and stack is decision 10: the
geometric three-street size moves 103.9%, 115.8% and 130.9% of pot at 77.5, 97.5 and 127.5bb
effective, so a key that cannot say which depth it was solved at cannot refuse a depth it
holds no cell for.

**The pot and the stack in the key are nominal, not observed.** They are derived from the
*substituted* preflop line - the line the cell was solved for - rather than from the table
being asked about, which is what keeps a cell findable when a hand opened to 2.25bb looks up
an `@2.5` cell. The real table is then compared against the nominal price by
`price_within_band` and refused outside it, never moved onto the nearest one.
`THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` records what that comparison still
does not see: it is a test on price, and the larger channel is that a cheaper open faces a
wider, weaker defender than the cell was solved against.

**The one collapse is over suits, and it is exact only if hero moves with the board.** A board
is replaced by the smallest member of its suit-isomorphism class, and the permutation that
carried it there is published, so hero's two cards can be moved by *that* map and no other. A
hand permuted inconsistently passes every board-level check and still returns a real strategy
for a real hand, which no exploitability figure and no shape check can see;
`AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS` records it. Nothing else is
collapsed: `K72r` and `Q72r` are two boards, not one, because decision 2 defers rank
abstraction rather than taking it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from itertools import permutations

from poker_training_bot.poker_core.positions import POSITION_LABELS
from poker_training_bot.solver_artifacts.spot_key import render_size_bb

_RANKS = "23456789TJQKA"
_SUITS = "cdhs"
_DECK = frozenset(rank + suit for rank in _RANKS for suit in _SUITS)

FLOP_CARDS = 3

CANONICAL_FLOP_CLASSES = 1755
"""How many suit-isomorphism classes the 22,100 three-card boards fall into.

Not a tabulated figure and not a constant this module reads: it is what
`canonical_board` produces over the whole deck, counted. Recomputed from the 52 cards by
`tests/test_postflop_key.py::TestTheOnePermittedCollapse`, which also checks the class sizes
against the three orbit sizes, so a canonicaliser that over-collapsed would show up as a class
of the wrong size long before any strategy was wrong.
"""

# The 24 relabellings of four suits. Suit isomorphism is the whole of the permitted collapse,
# so the group is written out once and minimised over, rather than a texture being classified
# by hand into rainbow, two-tone and monotone - a classification is a second rule that can
# disagree with the first.
_SUIT_PERMUTATIONS: tuple[dict[str, str], ...] = tuple(
    dict(zip(_SUITS, order, strict=True)) for order in permutations(_SUITS)
)

# Decision 11's flop menu as a fraction of pot, which is the unit it was solved in.
FLOP_BET_MENU: tuple[float, ...] = (0.33, 0.75)

MENU_FRACTION_TOLERANCE = 0.05
"""How far, in pot fraction, a faced bet may sit from a menu entry and still be that entry.

Decision 14, ruled by Taylor 2026-09-15, and compared **inclusively**: a bet exactly this far
away matches. The menu is a percent of pot and the table is in chips, and the arithmetic does
not come out even - 33% of a 550-chip pot is 181.5, which no dealer can push - so a strict
equality match would refuse every faced bet at a real table and kill the raise branch of the
committed artifact with nothing going red.

The width is bounded on both sides by arithmetic rather than taste. It has to exceed the
rounding a real table imposes, `|180/550 - 0.33| = 0.002727`; it has to stay under half the
distance between two entries, `(0.75 - 0.33)/2 = 0.21`, or one bet lands in two buckets; and
it has to stay under `|0.50 - 0.33| = 0.17`, because the phase separately requires a 50% bet
to refuse. 0.05 is 18.3 times the floor and 3.4 times inside the tighter ceiling. What it
costs is stated rather than hidden: a 28%-of-pot bet and a 38%-of-pot bet both get the
strategy solved for 33%, and those are not the same spot.
"""

PRICE_BAND_FRACTION = 0.20
"""How far a real preflop price may sit from the price a cell was solved at.

Decision 10, ruled by Taylor 2026-09-10, stated as a fraction of the cell's own price and
inclusive at both ends: an open of 2.0bb to 3.0bb against an `@2.5` cell, a 3-bet of 6.0bb to
9.0bb against an `@7.5` one. A fraction rather than a chip width, because a fixed width that
admitted 2.0-3.0 against `@2.5` would admit only 7.0-8.0 against `@7.5` and a 3-bet to 6.5
would fall through the rule entirely - which is what the first draft of this ruling did, and
five of the seven converged rows are 3-bet pots.

This is a coverage rule, not a sensitivity-derived one: 99.0% of the corpus's 409 opens land
inside it, and 47.1% of its 87 3-bets do, because the committed chart's single 3-bet price of
7.5bb sits below the corpus median of 9.25bb.
`THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` owns that gap; it is recorded rather
than tuned away, because no band centred on 7.5 covers that corpus, and widening one until it
did would answer a 12bb 3-bet pot out of a 7.5bb cell.
"""

# Every action a seat can take on a flop. Unlike preflop, a check can precede hero's
# decision and a bet is the commonest entry there is.
_FLOP_ACTIONS = ("fold", "check", "call", "bet", "raise")
_SIZED_FLOP_ACTIONS = frozenset({"bet", "raise"})


_NO_FLOP_ACTION = "none"
"""What the flop segment reads when hero is first to act and nothing has happened yet.

It cannot collide with a rendered line: every `FlopAction` renders as `POSITION:action`, so
every non-empty flop segment holds a colon and this one does not.
"""


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


_Image = tuple[tuple[str, ...], tuple[tuple[str, str], ...]]


@cache
def _smallest_image(board: tuple[str, ...]) -> _Image:
    """The smallest relabelling of `board`, and the permutation that produced it.

    Both halves come out of one minimisation on purpose. If the representative and the map
    were computed separately they could disagree, and then there is no single permutation for
    hero's cards to move under at all. Ties - a board whose stabiliser is larger than the
    identity, which every board that does not use all four suits has - are broken by taking
    the first permutation in `_SUIT_PERMUTATIONS` order, so one class always publishes one map.
    """
    best: tuple[str, ...] | None = None
    chosen: dict[str, str] = _SUIT_PERMUTATIONS[0]
    for mapping in _SUIT_PERMUTATIONS:
        moved = tuple(sorted(card[0] + mapping[card[1]] for card in board))
        if best is None or moved < best:
            best, chosen = moved, mapping
    assert best is not None
    return tuple(sorted(best, key=_board_order)), tuple(chosen.items())


def _board_order(card: str) -> tuple[int, int]:
    """Highest rank first, then by suit - the order a flop is written and read in.

    The minimisation above compares card text, which puts `2c7dKh` ahead of `Kh7d2c`. Which
    of the two is stored is free, because a key is compared and never taken apart; which one
    a person reads off a refusal inventory is not.
    """
    return -_RANKS.index(card[0]), _SUITS.index(card[1])


def canonical_board(board: Sequence[str]) -> tuple[str, ...]:
    """The representative of `board`'s suit-isomorphism class, highest rank first.

    A member of the class rather than a label for it, so canonicalising the representative
    returns the representative, and two dresses of one board - `Kc7d2h` and `Kh7s2c` - are one
    key. Two-tone `Kc7c2h` is not collapsed onto rainbow `Kc7d2h`: one holds a flush draw and
    the other does not, and no relabelling of four suits turns one into the other.
    """
    return _smallest_image(tuple(sorted(_validated_board(board))))[0]


def board_suit_map(board: Sequence[str]) -> dict[str, str]:
    """The permutation of the four suits that carries `board` to its representative.

    Published rather than kept private because hero's cards have to move under this map and no
    other. A fresh dictionary each call, so a caller cannot reach into the cached answer.
    """
    return dict(_smallest_image(tuple(sorted(_validated_board(board))))[1])


def canonical_hole_cards(board: Sequence[str], hole_cards: Sequence[str]) -> tuple[str, ...]:
    """Hero's two cards moved by `board`'s own map, sorted.

    This is the half a board-level isomorphism test cannot see. On a two-tone board `AhQh`
    holds the flush draw and `AsQd` does not, and a map applied to the board but not to the
    hand - or applied to the hand inconsistently - serves one of them the other's strategy
    while every board-level check still passes.
    """
    cards = tuple(hole_cards)
    if len(cards) != 2:
        raise ValueError(f"hero holds exactly two cards, got {len(cards)}: {cards!r}")
    table = _validated_board(board)
    for card in cards:
        if card not in _DECK:
            raise ValueError(f"hole_cards holds a card that is not in the deck: {card!r}")
        if card in table:
            raise ValueError(f"{card!r} is on the board and cannot also be in hero's hand")
    if cards[0] == cards[1]:
        raise ValueError(f"hero cannot hold the same card twice: {cards!r}")
    mapping = board_suit_map(table)
    return tuple(sorted(card[0] + mapping[card[1]] for card in cards))


@dataclass(frozen=True)
class FlopAction:
    """One completed flop action, in the unit the solve was configured in.

    `size_pct` is a percent of the pot, which is what decision 11's menu is written in and
    what the committed cells are indexed by; chips belong to the table and are matched onto
    this menu by `match_menu_fraction`. A bet or a raise must carry one, because a sizeless
    aggressive action is the defect decision 9 names: two cells facing different prices merge
    into one and the lookup answers a 75% bet out of a 33% cell.
    """

    position: str
    action: str
    size_pct: float | None = None

    def __post_init__(self) -> None:
        if self.position not in POSITION_LABELS:
            raise ValueError(f"unknown position: {self.position!r}")
        if self.action not in _FLOP_ACTIONS:
            raise ValueError(
                f"flop action must be one of {list(_FLOP_ACTIONS)}, got {self.action!r}"
            )
        if self.action in _SIZED_FLOP_ACTIONS:
            if self.size_pct is None:
                raise ValueError(
                    f"a {self.action} by {self.position} must carry its size as a percent of"
                    " pot; a sizeless one reads as matching any price"
                )
            if isinstance(self.size_pct, bool) or not isinstance(self.size_pct, int | float):
                raise ValueError(f"size_pct must be a number, got {self.size_pct!r}")
            if not self.size_pct > 0:
                raise ValueError(f"size_pct must be positive, got {self.size_pct!r}")
            render_size_bb(self.size_pct)
        elif self.size_pct is not None:
            raise ValueError(
                f"a {self.action} carries no size of its own, got size_pct={self.size_pct!r}"
            )


def render_flop_action(entry: FlopAction) -> str:
    """One flop action as it appears inside a key, on the preflop key's own `@size` shape."""
    if entry.size_pct is None:
        return f"{entry.position}:{entry.action}"
    return f"{entry.position}:{entry.action}@{render_size_bb(entry.size_pct)}"


def postflop_spot_key(
    preflop_spot_key: str,
    board: Sequence[str],
    flop_actions: Sequence[FlopAction],
    pot_bb: float,
    effective_stack_bb: float,
) -> str:
    """Derive the canonical postflop spot key.

    `f/b:<board>/<preflop key>/f:<flop line>/p:<pot>/e:<stack>`, where the board is the
    canonical representative of its class, the preflop key is carried verbatim with its
    prices, and the flop line is comma-separated in action order or `none` when hero is first
    to act. Pot and effective stack are the nominal ones the cell was solved for, in big
    blinds, so a 100bb cell can never quietly answer a spot at another depth.

    The whole key is one whitespace-free token beginning with `f`, which is what keeps the
    preflop key inside it invisible to `self_play_reference.py`.
    """
    if not isinstance(preflop_spot_key, str) or not preflop_spot_key.startswith("t"):
        raise ValueError(
            "preflop_spot_key must be a preflop spot key, which begins with `t`,"
            f" got {preflop_spot_key!r}"
        )
    entries = tuple(flop_actions)
    for entry in entries:
        if not isinstance(entry, FlopAction):
            raise ValueError(f"flop_actions entries must be FlopAction, got {entry!r}")
    line = ",".join(render_flop_action(entry) for entry in entries) or _NO_FLOP_ACTION
    cards = "".join(canonical_board(board))
    pot = render_size_bb(pot_bb)
    stack = render_size_bb(effective_stack_bb)
    return f"f/b:{cards}/{preflop_spot_key}/f:{line}/p:{pot}/e:{stack}"


def price_within_band(solved_bb: float, actual_bb: float) -> bool:
    """Whether a real preflop price is close enough to the one a cell was solved at.

    Inclusive at both ends, because the endpoints are prices real hands actually land on - 2.0
    is a min-open and 3.0 a standard 3x - and because the previous draft of this rule failed
    at a boundary nobody had written down. A price outside the band refuses; it is never moved
    onto the nearest one, which is deliberately the opposite of the preflop chart's behaviour.
    Preflop 0.25bb barely moves a range; postflop the same 0.25bb moves the pot, the SPR and
    both ranges at once.
    """
    for value, field in ((solved_bb, "solved_bb"), (actual_bb, "actual_bb")):
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"{field} must be a number, got {value!r}")
    if not solved_bb > 0:
        raise ValueError(f"solved_bb must be positive, got {solved_bb!r}")
    return abs(actual_bb - solved_bb) <= solved_bb * PRICE_BAND_FRACTION


def _validated_pot(pot_chips: int) -> int:
    if isinstance(pot_chips, bool) or not isinstance(pot_chips, int | float):
        raise ValueError(f"pot_chips must be a number, got {pot_chips!r}")
    if not pot_chips > 0:
        raise ValueError(f"pot_chips must be positive, got {pot_chips!r}")
    return pot_chips


def match_menu_fraction(bet_chips: int, pot_chips: int) -> float | None:
    """Which menu entry a chip bet is, or None when it is none of them.

    Decision 14. The comparison is by pot fraction rather than by chips, so it holds at any
    blind level, and `None` is the answer for anything outside every bucket rather than the
    nearer entry - snapping is the nearest-neighbour substitution the contract forbids by
    name, and at a bet exactly halfway between two entries there is no nearer entry anyway.

    The first matching entry wins, and no bet can match two: at the ruled tolerance the
    buckets reach 38% and 70% of pot and do not touch.
    """
    if isinstance(bet_chips, bool) or not isinstance(bet_chips, int | float):
        raise ValueError(f"bet_chips must be a number, got {bet_chips!r}")
    fraction = bet_chips / _validated_pot(pot_chips)
    for entry in FLOP_BET_MENU:
        if abs(fraction - entry) <= MENU_FRACTION_TOLERANCE:
            return entry
    return None


def menu_size_chips(fraction: float, pot_chips: int) -> int:
    """A committed artifact size as chips, rounded to the nearest chip.

    The other direction of decision 14's rule, and the reason it needs stating: 33% of a
    550-chip pot is 181.5 and the table can only push whole chips.
    """
    if isinstance(fraction, bool) or not isinstance(fraction, int | float):
        raise ValueError(f"fraction must be a number, got {fraction!r}")
    if not fraction > 0:
        raise ValueError(f"fraction must be positive, got {fraction!r}")
    return round(fraction * _validated_pot(pot_chips))
