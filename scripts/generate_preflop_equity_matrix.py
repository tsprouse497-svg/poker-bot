"""The all-in preflop equity matrix, and the enumeration that makes it exact.

Owns `data/artifacts/preflop/equity/preflop_eq169.bin` and the source card beside it. The
file holds, for every ordered pair of the 169 starting-hand classes, the share of the pot
the first class takes when all the money goes in before the flop and both hands are shown
down with ties split: 169 rows of 169 little-endian float32, no header, 114,244 bytes, both
axes indexed by `gtopen_class_index`. That is the solver's own ordering rather than the
grid ordering a chart report prints, and confusing the two transposes suited and offsuit.

Exact, not sampled. Every one of the 2,598,960 boards is counted, so the file is a table of
the game's own arithmetic rather than an estimate with a seed attached, and `--check`
recomputes the whole thing and compares rather than trusting the committed bytes.

Card removal is where this computation is usually got wrong, so it is handled by counting
rather than by correction factors. A cell is the average over every *legal ordered pair of
combinations* of the two classes - the pairs that can be dealt at once - and every board
that neither hand blocks. `AA` against `AA` is therefore the average over the 6 ordered
pairs of pocket aces a deck can deal at once - `AcAd` can only ever be facing `AhAs` - and
not the 36 a reading that ignored the deck would take; `AKs` against `AKs` over the 12
ordered pairs of distinct suits, not 16. The pairs a deck cannot deal are never in the
denominator
and never in the numerator, which is why every diagonal entry is exactly 0.5 rather than
merely near it: the set of legal ordered pairs of one class with itself is symmetric, so
the wins and the losses cancel term by term and the ties split. A suited class against
itself is exactly 50 too. It comes out otherwise only when the same combination is allowed
to play itself, or when a class is priced against a fixed representative combination of the
other class instead of against all of them.

Why it finishes in minutes rather than weeks. The naive shape is 14,365 class pairs times
1,712,304 boards times two seven-card evaluations, about 50 billion comparisons, and the
repo's own `poker_core.hand_eval` cannot approach that. Three reductions, none of them
approximations:

- The board is enumerated once for everybody, not once per matchup. On one board every one
  of the 1,081 combinations still live is evaluated a single time, and the 169-by-169 tally
  of who beats whom is read off a histogram of those values, so a board costs about 1,081
  evaluations instead of 28,730.
- Boards are counted up to suit relabelling. Renaming suits maps a board to a board, leaves
  every hand's value alone and leaves every hand's *class* alone, so an orbit of boards
  contributes its representative's tally times its size. 2,598,960 boards collapse to
  134,459 representatives whose orbit sizes sum back to 2,598,960, which the run asserts.
- The histogram counts pairs the deck cannot deal, and those are subtracted exactly by
  inclusion-exclusion over the shared card rather than skipped one pair at a time.

The self-check is not the author marking his own work. The run tallies the category of
every seven-card hand it evaluates and, because each seven-card set is seen once per way of
splitting it into board and hole cards, divides by 21 to recover the exact seven-card
census - which must equal the nine published frequencies, on the nose, with no tolerance.
Those counts are combinatorics that no poker source disputes, and they fail loudly if the
evaluator misreads a straight, a flush or a kicker. On top of that sit the published
matchup equities, which are held to a band rather than to a figure for a reason the
`ORACLE` table states.

numpy is a development dependency and the bot never imports it. The repo's own
`poker_core.hand_eval` was measured at 11,900 seven-card hands a second, so the 145,350,179
evaluations this run makes would be 3.4 hours of pure Python before a single pair is
compared - and the pair tallying, which numpy does as one matrix product per board, is the
larger half. There is no version of this file that produces itself without an array
library, and the alternative to the dependency is not slower code but an uncommitted table.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
import time

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - the message is the whole point
    raise SystemExit(
        "numpy is required to build the preflop equity matrix and is a dev dependency of"
        " this repo. Run this through `uv run`, which installs the dev group."
    ) from None

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.gtopen_export import gtopen_class_index  # noqa: E402
from poker_training_bot.solver_artifacts.hand_classes import (  # noqa: E402
    HAND_CLASSES,
    hand_class,
)

EQUITY_DIR = REPO_ROOT / "data" / "artifacts" / "preflop" / "equity"
MATRIX_PATH = EQUITY_DIR / "preflop_eq169.bin"
CARD_PATH = EQUITY_DIR / "preflop_eq169.source.json"

CLASSES = 169
RANKS = "23456789TJQKA"
SUITS = "cdhs"
BOARDS_PER_MATCHUP = math.comb(48, 5)
ALL_BOARDS = math.comb(52, 5)
CATEGORY_SHIFT = 20

SEVEN_CARD_CENSUS = {
    "high card": 23_294_460,
    "one pair": 58_627_800,
    "two pair": 31_433_400,
    "three of a kind": 6_461_620,
    "straight": 6_180_020,
    "flush": 4_047_644,
    "full house": 3_473_184,
    "four of a kind": 224_848,
    "straight flush": 41_584,
}
"""How many of the 133,784,560 seven-card hands fall in each category. Published
combinatorics, independent of anything anybody believes about equities, and the run
reproduces every one of them exactly or refuses to write."""

ORACLE_BAND = 0.8
"""Points of slack allowed on a published matchup equity, and why any is allowed.

A published figure is quoted for one suit configuration; a cell here is the average over
every legal combination pair. Measured, that convention is worth up to 1.55 points on a
single matchup - `AA` against `72o` runs 87.42 when the two hands share no suit and 88.98
when they share both - so half that spread is the widest an anchor can be off for the
convention alone, and a real defect in the enumeration moves a cell far further than this.
The census above is the check with no tolerance at all.
"""

ORACLE = (
    ("AA", "KK", 82.4),
    ("AA", "72o", 87.7),
    ("AKs", "QQ", 46.0),
    ("AKo", "QQ", 43.0),
    ("22", "AKo", 52.0),
)
"""Published all-in equities for the first class, in points.

`22` against `AKo` is the classic pair-versus-two-overcards coinflip and it is the *low*
pair's number. A middle pair is a bigger favourite than that and this table would be wrong
to say otherwise: `88` against `AKo` measures 55.16 here, and 54.75 to 55.57 across the suit
configurations, so no reading of it is a 52. Reported in the card as a measurement.
"""


def _rank_tables() -> tuple[np.ndarray, ...]:
    """Everything a hand's value needs from a 13-bit set of ranks, precomputed.

    Indexed by the mask, not by a card list: `POP` counts the ranks present, `HIGH1` names
    the highest, `TOP2`/`TOP3`/`TOP5` pack the highest few into four-bit fields from bit 16
    down, and `STRAIGHT` names the top rank of the best straight or -1. The wheel is a
    straight whose top rank is the five, which is the case a hand-rolled loop forgets.
    """
    size = 1 << 13
    pop = np.zeros(size, dtype=np.int8)
    high1 = np.full(size, -1, dtype=np.int8)
    top2 = np.zeros(size, dtype=np.int32)
    top3 = np.zeros(size, dtype=np.int32)
    top5 = np.zeros(size, dtype=np.int32)
    straight = np.full(size, -1, dtype=np.int8)
    for mask in range(size):
        bits = [rank for rank in range(12, -1, -1) if mask >> rank & 1]
        pop[mask] = len(bits)
        if bits:
            high1[mask] = bits[0]
        packed = 0
        for position, rank in enumerate(bits[:5]):
            packed |= rank << (16 - 4 * position)
        top5[mask] = packed
        top3[mask] = packed >> 8 << 8
        top2[mask] = packed >> 12 << 12
        top = -1
        for high in range(12, 3, -1):
            if all(mask >> (high - step) & 1 for step in range(5)):
                top = high
                break
        if top < 0 and mask >> 12 & 1 and all(mask >> step & 1 for step in range(4)):
            top = 3
        straight[mask] = top
    return pop, high1, top2, top3, top5, straight


POP, HIGH1, TOP2, TOP3, TOP5, STRAIGHT = _rank_tables()
POWERS = (1 << np.arange(13)).astype(np.int32)


def evaluate(counts: np.ndarray, suit_masks: np.ndarray) -> np.ndarray:
    """The value of many seven-card hands at once, higher being better.

    A hand arrives as how many cards it holds of each rank and which ranks it holds in each
    suit, because both are cheap to build by adding two hole cards to a fixed board. The
    value is the category in the top bits and the five cards that play packed beneath it,
    so a plain integer comparison is the poker comparison and equality is a genuine chop.

    Every category is scored and the best is taken, rather than testing them in order. That
    is what gets seven-card hands right: a hand can be a flush and a full house at once, and
    it plays the full house, so the ordering has to decide rather than the first test that
    fires. Only the five cards that play are packed - three of a kind carries two kickers,
    never three - because a sixth card that cannot be shown must not break a tie.
    """
    rank_mask = (counts > 0).astype(np.int32) @ POWERS
    quads_mask = (counts == 4).astype(np.int32) @ POWERS
    trips_mask = (counts == 3).astype(np.int32) @ POWERS
    pairs_mask = (counts == 2).astype(np.int32) @ POWERS

    suit_counts = POP[suit_masks]
    flush_suit = suit_counts.argmax(axis=1)
    has_flush = suit_counts.max(axis=1) >= 5
    flush_ranks = np.take_along_axis(suit_masks, flush_suit[:, None], axis=1)[:, 0]
    flush_ranks = np.where(has_flush, flush_ranks, 0)
    straight_flush = STRAIGHT[flush_ranks]
    flush_value = np.where(
        straight_flush >= 0,
        (8 << CATEGORY_SHIFT) | (straight_flush.astype(np.int64) << 16),
        (5 << CATEGORY_SHIFT) | TOP5[flush_ranks].astype(np.int64),
    )
    flush_value = np.where(has_flush, flush_value, -1)

    quad = HIGH1[quads_mask].astype(np.int64)
    quad_kicker = HIGH1[
        np.where(quads_mask != 0, rank_mask & ~(1 << np.maximum(quad, 0)), 0)
    ].astype(np.int64)
    quads_value = np.where(
        quads_mask != 0,
        (7 << CATEGORY_SHIFT) | (quad << 16) | (quad_kicker << 12),
        -1,
    )

    trip = HIGH1[trips_mask].astype(np.int64)
    spare_trips = np.where(trips_mask != 0, trips_mask & ~(1 << np.maximum(trip, 0)), 0)
    pair_pool = np.where(trips_mask != 0, pairs_mask | spare_trips, 0)
    boat_pair = HIGH1[pair_pool].astype(np.int64)
    boat_value = np.where(
        (trips_mask != 0) & (pair_pool != 0),
        (6 << CATEGORY_SHIFT) | (trip << 16) | (boat_pair << 12),
        -1,
    )

    straight_top = STRAIGHT[rank_mask].astype(np.int64)
    straight_value = np.where(
        straight_top >= 0, (4 << CATEGORY_SHIFT) | (straight_top << 16), -1
    )

    trip_kickers = np.where(trips_mask != 0, rank_mask & ~(1 << np.maximum(trip, 0)), 0)
    trips_value = np.where(
        trips_mask != 0,
        (3 << CATEGORY_SHIFT) | (trip << 16) | (TOP2[trip_kickers].astype(np.int64) >> 4),
        -1,
    )

    both_pairs = TOP2[pairs_mask].astype(np.int64)
    high_pair = both_pairs >> 16
    low_pair = (both_pairs >> 12) & 0xF
    two_pair_kicker = np.where(
        POP[pairs_mask] >= 2, rank_mask & ~(1 << high_pair) & ~(1 << low_pair), 0
    )
    two_pair_value = np.where(
        POP[pairs_mask] >= 2,
        (2 << CATEGORY_SHIFT)
        | (high_pair << 16)
        | (low_pair << 12)
        | (HIGH1[two_pair_kicker].astype(np.int64) << 8),
        -1,
    )

    pair = HIGH1[pairs_mask].astype(np.int64)
    pair_kickers = np.where(pairs_mask != 0, rank_mask & ~(1 << np.maximum(pair, 0)), 0)
    pair_value = np.where(
        pairs_mask != 0,
        (1 << CATEGORY_SHIFT) | (pair << 16) | (TOP3[pair_kickers].astype(np.int64) >> 4),
        -1,
    )

    best = np.maximum(flush_value, quads_value)
    best = np.maximum(best, boat_value)
    best = np.maximum(best, straight_value)
    best = np.maximum(best, trips_value)
    best = np.maximum(best, two_pair_value)
    best = np.maximum(best, pair_value)
    return np.maximum(best, TOP5[rank_mask].astype(np.int64))


class Combinations:
    """The 1,326 two-card holdings, and what each one contributes to a hand.

    Held as arrays rather than objects because they are added to a board 1,081 at a time.
    `class_index` is `gtopen_class_index`, so a tally over these is already a tally over the
    matrix's own axes.
    """

    def __init__(self) -> None:
        pairs = list(itertools.combinations(range(52), 2))
        self.count = len(pairs)
        self.mask = np.zeros(self.count, dtype=np.uint64)
        self.counts = np.zeros((self.count, 13), dtype=np.int16)
        self.suits = np.zeros((self.count, 4), dtype=np.int32)
        self.class_index = np.zeros(self.count, dtype=np.int64)
        for index, (first, second) in enumerate(pairs):
            for card in (first, second):
                self.mask[index] |= np.uint64(1) << np.uint64(card)
                self.counts[index, card // 4] += 1
                self.suits[index, card % 4] |= 1 << (card // 4)
            self.class_index[index] = gtopen_class_index(
                hand_class((card_text(first), card_text(second)))
            )
        self.by_card = np.array(
            [[i for i, (a, b) in enumerate(pairs) if c in (a, b)] for c in range(52)],
            dtype=np.int64,
        )

    def legal_pairs_by_class(self) -> np.ndarray:
        """How many ordered pairs of combinations each class pair can be dealt.

        The denominator, and the only place card removal enters the count of matchups
        rather than the count of boards: `AA` against `AA` has 6 such pairs and `AKs`
        against `AKs` has 12, where a reading that ignored the deck would say 36 and 16.
        Every legal pair sees the same C(48,5) boards, so the board count is a factor here
        rather than a per-pair sum, and the whole table sums to the 1,624,350 ordered pairs
        a deck can deal - 1,326 holdings against the 1,225 that do not block them.
        """
        disjoint = (self.mask[:, None] & self.mask[None, :]) == 0
        flat = (self.class_index[:, None] * CLASSES + self.class_index[None, :]).ravel()
        totals = np.bincount(
            flat, weights=disjoint.ravel().astype(np.float64), minlength=CLASSES**2
        )
        return totals.reshape(CLASSES, CLASSES)


def card_text(card: int) -> str:
    """`0` is the deuce of clubs and `51` the ace of spades, in this repo's card text."""
    return RANKS[card // 4] + SUITS[card % 4]


def canonical_boards() -> tuple[np.ndarray, np.ndarray]:
    """One representative of every board up to suit relabelling, with its orbit size.

    Renaming suits is a symmetry of the whole computation: it maps a board to a board, does
    not change any hand's value, and does not change any hand's class, because pairs stay
    pairs and suited stays suited. So a board's tally is its orbit's tally divided by the
    orbit size, and counting the representative that many times is the same total. It is a
    24-fold saving and not an approximation; the caller asserts the orbit sizes sum to
    C(52,5), which is the statement that no board was counted twice or dropped.
    """
    boards = np.array(list(itertools.combinations(range(52), 5)), dtype=np.int8)
    smallest: np.ndarray | None = None
    for permutation in itertools.permutations(range(4)):
        relabel = np.array(
            [(card // 4) * 4 + permutation[card % 4] for card in range(52)], dtype=np.int64
        )
        moved = relabel[boards]
        mask = np.zeros(len(boards), dtype=np.uint64)
        for column in range(5):
            mask |= np.uint64(1) << moved[:, column].astype(np.uint64)
        smallest = mask if smallest is None else np.minimum(smallest, mask)
    _, first_seen, orbit_sizes = np.unique(
        smallest, return_index=True, return_counts=True
    )
    return boards[first_seen].astype(np.int64), orbit_sizes


def accumulate(
    combos: Combinations, boards: np.ndarray, orbits: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Walk every board and tally, for each ordered class pair, twice equity in showdowns.

    The unit is doubled so the tally is a whole number: a win scores 2, a chop scores 1, and
    a loss scores 0, which keeps every addition exact in float64 and makes the total
    independent of the order the boards are walked.

    Three steps per board. First the value of all 1,081 live combinations. Then the tally
    over *all* ordered pairs of those, read off a histogram of values per class: for a
    holding of value v the class-j holdings it beats are those below v and the ones it chops
    with are those at v, so one matrix product does 28,561 cells at once. That step counts
    pairs the deck cannot deal - two holdings sharing a card - so the third step subtracts
    them, once per shared card and then correcting the holding paired with itself, which the
    two shared cards would otherwise remove twice.

    The category of every hand evaluated is tallied on the way past. Each seven-card set is
    met once per way of splitting it into five board cards and two hole cards, so that
    census divided by 21 is the exact seven-card census, and it is the check that fails if
    the evaluator is wrong about anything.
    """
    doubled = np.zeros((CLASSES, CLASSES), dtype=np.float64)
    census = np.zeros(9, dtype=np.int64)
    position = np.full(combos.count, -1, dtype=np.int64)
    all_cards = np.arange(52)
    for board, orbit in zip(boards, orbits, strict=True):
        board_mask = np.uint64(0)
        board_counts = np.zeros(13, dtype=np.int16)
        board_suits = np.zeros(4, dtype=np.int32)
        for card in board:
            board_mask |= np.uint64(1) << np.uint64(int(card))
            board_counts[card // 4] += 1
            board_suits[card % 4] |= 1 << (card // 4)

        live = np.flatnonzero((combos.mask & board_mask) == 0)
        values = evaluate(combos.counts[live] + board_counts, combos.suits[live] | board_suits)
        classes = combos.class_index[live]
        census += orbit * np.bincount(values >> CATEGORY_SHIFT, minlength=9)

        _, ordinal = np.unique(values, return_inverse=True)
        width = int(ordinal.max()) + 1
        histogram = (
            np.bincount(classes * width + ordinal, minlength=CLASSES * width)
            .reshape(CLASSES, width)
            .astype(np.float64)
        )
        below = np.cumsum(histogram, axis=1) - histogram
        board_tally = histogram @ (2.0 * below + histogram).T

        position[live] = np.arange(len(live))
        live_cards = np.setdiff1d(all_cards, board)
        sharing = position[combos.by_card[live_cards]]
        sharing = sharing[sharing >= 0].reshape(len(live_cards), -1)
        shared_values = values[sharing]
        shared_classes = classes[sharing]
        score = 2 * (shared_values[:, :, None] > shared_values[:, None, :]) + (
            shared_values[:, :, None] == shared_values[:, None, :]
        )
        cells = (shared_classes[:, :, None] * CLASSES + shared_classes[:, None, :]).ravel()
        illegal = np.bincount(
            cells, weights=score.ravel().astype(np.float64), minlength=CLASSES**2
        ).reshape(CLASSES, CLASSES)
        position[live] = -1

        held = np.bincount(classes, minlength=CLASSES).astype(np.float64)
        doubled += orbit * (board_tally - illegal + np.diag(held))
    return doubled, census


def build(verbose: bool = False) -> tuple[np.ndarray, int]:
    """The 169-by-169 matrix of equity shares, checked as it is built.

    Every assertion here is a statement the arithmetic must satisfy on its own, not a
    comparison against a stored answer: the orbits cover the deck, the census reproduces the
    published seven-card frequencies exactly, and each pair of opposite cells accounts for
    every showdown between those two classes and nothing else - which is what proves the
    illegal pairs came out and that none of the legal ones went with them.
    """
    started = time.time()
    combos = Combinations()
    legal = combos.legal_pairs_by_class()
    dealable = combos.count * math.comb(50, 2)
    if int(legal.sum()) != dealable:
        raise SystemExit(
            f"the class pairs account for {int(legal.sum()):,} ordered pairs of holdings"
            f" where a deck can deal {dealable:,}, so card removal was counted wrong"
        )
    boards, orbits = canonical_boards()
    if int(orbits.sum()) != ALL_BOARDS:
        raise SystemExit(
            f"the suit-relabelling orbits cover {int(orbits.sum())} boards where the deck"
            f" has {ALL_BOARDS}, so the board enumeration is not a partition"
        )
    if verbose:
        print(
            f"{len(boards):,} boards up to suit relabelling covering {ALL_BOARDS:,},"
            f" setup {time.time() - started:.0f}s",
            flush=True,
        )

    doubled, census = accumulate(combos, boards, orbits)

    if int(census.sum()) % 21:
        raise SystemExit("the seven-card census is not a whole number of hands")
    census = census // 21
    for index, (name, published) in enumerate(SEVEN_CARD_CENSUS.items()):
        if int(census[index]) != published:
            raise SystemExit(
                f"the evaluator produced {int(census[index]):,} seven-card hands of"
                f" {name} where there are {published:,}, so it misreads the game"
            )

    showdowns = 2.0 * legal * BOARDS_PER_MATCHUP
    if not np.array_equal(doubled + doubled.T, showdowns):
        raise SystemExit(
            "a class pair's two cells do not account for exactly its legal showdowns, so"
            " the pairs the deck cannot deal were not removed cleanly"
        )
    if verbose:
        print(f"accumulated in {(time.time() - started) / 60:.1f} min", flush=True)
    return (doubled / showdowns).astype("<f4"), len(boards)


def self_check(matrix: np.ndarray) -> dict[str, str]:
    """Hold the built matrix to what is known about preflop poker from outside this repo.

    Returns what it measured so the card can carry it. A failure here is a halt: the numbers
    below are the most published in the game, and a table that disagrees with them is wrong
    in a way no amount of internal consistency redeems.
    """
    measured: dict[str, str] = {}
    diagonal = np.array([matrix[i][i] for i in range(CLASSES)])
    if not np.all(diagonal == np.float32(0.5)):
        raise SystemExit(
            "a class is not exactly even money against itself, which means the illegal"
            " pairings of a combination with itself survived"
        )
    measured["diagonal"] = "every class against itself is exactly 0.500000"

    opposites = matrix.astype(np.float64) + matrix.astype(np.float64).T
    drift = float(np.max(np.abs(opposites - 1.0)))
    if drift > 1e-6:
        raise SystemExit(f"opposite cells sum to 1 only within {drift}, which is not rounding")
    measured["symmetry"] = (
        f"equity[i][j] + equity[j][i] differs from 1 by at most {drift:.3e}, which is"
        " float32 rounding of an identity the counting makes exact"
    )

    for first, second, published in ORACLE:
        value = 100.0 * float(matrix[gtopen_class_index(first)][gtopen_class_index(second)])
        if abs(value - published) > ORACLE_BAND:
            raise SystemExit(
                f"{first} against {second} measures {value:.2f} where the published figure"
                f" is about {published}, a gap wider than the {ORACLE_BAND}-point band the"
                " suit-configuration convention explains"
            )
        measured[f"{first} vs {second}"] = f"{value:.2f} against a published {published}"
    middle = 100.0 * float(matrix[gtopen_class_index("88")][gtopen_class_index("AKo")])
    measured["88 vs AKo"] = (
        f"{middle:.2f}, measured and reported rather than anchored: the 52 that is quoted"
        " for a pair against two overcards is the low pair's figure, not a middle pair's"
    )
    return measured


def class_by_row() -> dict[int, str]:
    """The matrix's own row ordering, inverted from the index the matrix is built with.

    The card names rows so a reader can open the headerless bytes and check them, which
    only works if the name comes from the ordering the bytes are in. `HAND_CLASSES` is a
    different ordering - it runs `AA` first and `22` last, the reverse of this one at both
    ends - so a row named out of it names the wrong hand, which is how the card came to
    publish `row_0: AA` for a row that holds `22`. Derived here from
    `gtopen_class_index` itself, the same call the matrix and its self-check are indexed
    by, and refused if that index does not cover every row exactly once.
    """
    rows = {gtopen_class_index(name): name for name in HAND_CLASSES}
    if sorted(rows) != list(range(CLASSES)):
        raise SystemExit(
            "gtopen_class_index does not land the 169 classes on rows 0 to 168 exactly"
            " once, so the matrix has no row ordering to name"
        )
    return rows


def render_card(matrix_bytes: bytes, measured: dict[str, str], representatives: int) -> str:
    """The card that says where the bytes came from, in the export card's own house style."""
    rows = class_by_row()
    card = {
        "checks": measured,
        "class_order": {
            "index": "gtopen_class_index, from src/poker_training_bot/solver_artifacts",
            "note": (
                "ranks 0 to 12 as 2 through A; a pair at hi*13+hi, a suited class at"
                " hi*13+lo, an offsuit class at lo*13+hi. Not the 13x13 grid ordering a"
                " chart report prints, which transposes suited and offsuit"
            ),
            "row_0": rows[0],
            f"row_{CLASSES - 1}": rows[CLASSES - 1],
        },
        "layout": {
            "bytes": len(matrix_bytes),
            "dtype": "float32",
            "endianness": "little",
            "header": "none",
            "order": "row-major, 169 rows of 169",
            "reading": (
                "value[i][j] is the share of the pot class i takes all-in preflop against"
                " class j, ties split. A share in 0 to 1, not a percentage"
            ),
        },
        "method": {
            "boards": (
                f"every one of the {ALL_BOARDS:,} boards, counted as {representatives:,}"
                " representatives up to suit relabelling weighted by orbit size"
            ),
            "card_removal": (
                "a cell averages over the ordered pairs of combinations the deck can deal"
                " at once and no others, so AA against AA is 6 ordered pairs and AKs"
                " against AKs is 12, where ignoring the deck would say 36 and 16"
            ),
            "sampling": "none; the enumeration is exhaustive and the result is exact",
            "ties": "split, counted as half a pot each",
        },
        "regenerate": "uv run python scripts/generate_preflop_equity_matrix.py",
        "sha256": hashlib.sha256(matrix_bytes).hexdigest(),
        "verify": "uv run python scripts/generate_preflop_equity_matrix.py --check",
    }
    return json.dumps(card, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="recompute the matrix and compare it with the committed files, writing nothing",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="do not report progress while computing"
    )
    arguments = parser.parse_args(argv)

    matrix, representatives = build(verbose=not arguments.quiet)
    measured = self_check(matrix)
    matrix_bytes = matrix.tobytes()
    card_text = render_card(matrix_bytes, measured, representatives)

    if not arguments.check:
        EQUITY_DIR.mkdir(parents=True, exist_ok=True)
        MATRIX_PATH.write_bytes(matrix_bytes)
        CARD_PATH.write_text(card_text, encoding="utf-8")
        print(f"wrote {MATRIX_PATH.name} ({len(matrix_bytes):,} bytes) and {CARD_PATH.name}")
        for name, value in measured.items():
            print(f"  {name}: {value}")
        return 0

    stale = []
    if not MATRIX_PATH.exists() or MATRIX_PATH.read_bytes() != matrix_bytes:
        stale.append(MATRIX_PATH)
    if not CARD_PATH.exists() or CARD_PATH.read_text(encoding="utf-8") != card_text:
        stale.append(CARD_PATH)
    if stale:
        for path in stale:
            name = path.relative_to(REPO_ROOT)
            print(f"{name} is not what this script produces", file=sys.stderr)
        return 1
    print("the committed preflop equity matrix and its card reproduce from this enumeration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
