"""The four dominance relations and the two counterfactual arms, as pure functions over grids.

This module owns the *rules* the chart's range gate is made of, and owns nothing else. It opens no
file, renders no report, and knows nothing about a spot beyond its grid, so every caller measures
the same relation instead of its own reading of the same prose - seven counts came out of seven
readings before this was written down once
(`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`).

A **grid** is one spot's cells: a hand class mapped to how often it takes some action, in
percentage points out of a hundred. A **chart** is one grid per spot, keyed by spot id. A class
missing from a grid never arrived at that spot, and every comparison it would have entered is
skipped rather than scored against a stand-in zero - a stand-in measures how sparse the grid is,
not how the hands are played.

Three relations read how often a hand puts money in at all. The fourth reads how often it raises,
because the inversion that stopped this phase sits at cells where both hands play every time and
only the raise-versus-call split differs. None of the four refuses a chart: strong hands really do
get played less than weak ones among holdings the solve prices alike, and a gate on the ordering
would throw out correct play. What is asked is that the measurement was taken over every cell.

What does refuse is the pair of arms below, and neither arm passing says the ranges are good
poker. Both ask one question: did the hand grid survive coming out of the solver right way up.
Nothing here can see a chart that folds too much everywhere or one whose grids are on the wrong
seats, because every comparison is against another cell of the same grid rather than against any
outside standard.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, HIGH_TO_LOW_RANKS

Grid = Mapping[str, float]
Chart = Mapping[str, Grid]

RANKS = HIGH_TO_LOW_RANKS
"""Strongest rank first, so neighbours in this sequence are neighbouring ranks."""

TOLERANCE_PCT = 1.0
"""How far the weaker hand may be played ahead of the stronger one before it counts, in points.

Ruled on 2026-08-24 for every relation here and never reopened. It catches the real case - a pair
played 27 points less often than the pair below it - and ignores two hands a solve plays almost
always sitting eight hundredths apart, where the split carries no meaning. A gap of exactly a
point is not a violation; the count is of gaps strictly wider. Re-deriving it from the chart it
judges was refused, that being the move that ends with a tolerance wide enough to admit anything.
"""

REACH_FLOOR_BP = 0
"""No hand is dropped for arriving rarely. A cell counts when its class arrives at all, which is
the converter's own rule, and how often it arrives is a weighting elsewhere rather than a filter
here. A floor would quietly shrink what the gate looks at as the chart moved."""

FULL_GRID_CELLS = 169
"""Every hand class. A grid holding all of them is one where the rank reversal below loses
nothing."""

ROW_COMPARISONS_PER_FULL_GRID = 132
"""Kicker comparisons a full grid offers: for each high card, each neighbouring pair of lower
kickers, suited hands and offsuit hands counted apart. 2 x (11 + 10 + ... + 0) = 132."""

RANK_ARM_SPOT_FLOOR = 5
"""Below five scoring spots a partition is published and not asserted. A strict comparison over
one or two grids is a coin flip, and a gate that turns on a coin flip fails for the wrong
reasons."""

ADJACENT_PAIRS: tuple[tuple[str, str], ...] = tuple(
    (f"{high}{high}", f"{low}{low}") for high, low in zip(RANKS, RANKS[1:], strict=False)
)
"""Each pair against the pair one rank below it, twelve comparisons. Neighbours only: comparing
every pair against every weaker one reports one drifting step a dozen times over, in a dozen
places it did not happen."""

SUITED_OVER_OFFSUIT: tuple[tuple[str, str], ...] = tuple(
    (f"{high}{low}s", f"{high}{low}o")
    for index, high in enumerate(RANKS)
    for low in RANKS[index + 1 :]
)
"""Each suited hand against the offsuit hand of the same two ranks, 78 comparisons. Same cards,
one of them a flush draw more often, so the suited hand is never the worse holding."""

ROW_KICKERS: tuple[tuple[str, str], ...] = tuple(
    (f"{high}{better}{suit}", f"{high}{worse}{suit}")
    for index, high in enumerate(RANKS)
    for better, worse in zip(RANKS[index + 1 :], RANKS[index + 2 :], strict=False)
    for suit in ("s", "o")
)
"""Within one high card's row, each kicker against the kicker one rank below it, suited and
offsuit kept apart. Suited and offsuit are never compared to each other here - that is the twins
relation's job, and folding the two together turns one defect into two counts of it."""

RANK_REVERSAL: dict[str, str] = dict(zip(RANKS, reversed(RANKS), strict=True))
"""Ace swaps with the deuce, king with the trey, and the eight maps to itself. It is its own
inverse and it never carries a hand out of its family, so pairs stay pairs and suited stays
suited."""


@dataclass(frozen=True)
class Relation:
    """One relation's whole definition as data, so it is fixed before anything is measured.

    Prose describing a relation is what produced seven different counts of the same chart. The
    shared fields carry defaults, which means a relation departing from one has to say so on its
    own line rather than in a paragraph somebody has to notice.
    """

    name: str
    measure: str
    comparisons_per_full_grid: int
    excluded_families: tuple[str, ...] = ()
    tolerance_pct: float = TOLERANCE_PCT
    reach_floor_bp: int = REACH_FLOOR_BP
    scope: str = "per cell, every committed spot, never pooled across spots"
    gated_as_an_order: bool = False


PLAY_NOT_FOLD = "play-not-fold"
"""How often a hand puts money in at all, raise or call taken together. A stronger hand raising
where a weaker one calls is not an inversion - both continue - so the split is deliberately
invisible to the three relations stated over this."""

RAISE_WEIGHT = "raise-weight"
"""How often a hand raises in the published chart. Where the chart offers no cold call, that is
the solve's raise plus its call, because that is the action the bot actually takes there."""

RELATIONS: tuple[Relation, ...] = (
    Relation("pair ladder", PLAY_NOT_FOLD, len(ADJACENT_PAIRS)),
    Relation("suited over its offsuit twin", PLAY_NOT_FOLD, len(SUITED_OVER_OFFSUIT)),
    Relation(
        "row kicker ladder",
        PLAY_NOT_FOLD,
        ROW_COMPARISONS_PER_FULL_GRID,
        ("suited and offsuit are never compared to each other here",),
    ),
    Relation(
        "pair ladder on the raise weight",
        RAISE_WEIGHT,
        len(ADJACENT_PAIRS),
        ("hero's jam, which lives only at the four-bet spots this chart withholds",),
        scope="per cell, every committed spot, the merged raise weight the bot plays",
    ),
)
"""Four rather than three, and the fourth is why the phase stopped: a pair played less often than
the pair below it, at cells where both are played every single time. Nothing that reads
play-not-fold can see it, both hands reading 100 there, so the relation is stated over the raise
instead."""

COMPARISONS: dict[str, tuple[tuple[str, str], ...]] = {
    "pair ladder": ADJACENT_PAIRS,
    "suited over its offsuit twin": SUITED_OVER_OFFSUIT,
    "row kicker ladder": ROW_KICKERS,
    "pair ladder on the raise weight": ADJACENT_PAIRS,
}
"""Which comparisons each relation runs. The fourth reuses the pair ladder's list and is a
different relation for reading it off a different action, which is the only thing separating
them."""


def inversions(
    cells: Grid, pairs: Sequence[tuple[str, str]]
) -> list[tuple[str, str, float, float]]:
    """Every comparison this grid plays the wrong way round by more than the tolerance.

    Each row names the stronger hand, the weaker one, and how often each is taken, so a caller can
    publish the worst case rather than only a total - a bare count cannot tell one grid drifting a
    point from one folding aces.

    A comparison is skipped when either hand is missing from the grid. Reading an absent class as
    zero would score a hand that never arrived as folded, which turns sparsity into inversions and
    is the classic way one of these measures starts reporting a chart it has not looked at.
    """
    found = []
    for stronger, weaker in pairs:
        high, low = cells.get(stronger), cells.get(weaker)
        if high is None or low is None:
            continue
        if low - high > TOLERANCE_PCT:
            found.append((stronger, weaker, high, low))
    return found


def dominance_inversions(
    *, play: Chart, raise_weight: Chart
) -> dict[str, list[tuple[str, str, float, float]]]:
    """Every case the four relations find, kept apart by relation and carrying its two figures.

    Both charts are required rather than one, because three relations are stated over how often a
    hand is played and the fourth over how often it raises, and handing the same grid to all four
    silently answers the fourth question with the third's data. The four are never summed: they
    move in different directions and by different sizes, and one total hides which relation moved.
    """
    return {
        relation.name: [
            row
            for cells in (raise_weight if relation.measure == RAISE_WEIGHT else play).values()
            for row in inversions(cells, COMPARISONS[relation.name])
        ]
        for relation in RELATIONS
    }


def count_dominance_violations(*, play: Chart, raise_weight: Chart) -> dict[str, int]:
    """How many cases each of the four relations finds, counted per cell and refusing nothing.

    A count and not a verdict. The committed chart holds surviving cases that were read hand by
    hand and ruled correct play - a nut-straight suited ace is less dominated than a middling one,
    and a split among hands the solve prices alike is bluff selection rather than a mistake - so a
    caller that refused a chart on any of these would refuse the chart the bot ships.
    """
    found = dominance_inversions(play=play, raise_weight=raise_weight)
    return {name: len(rows) for name, rows in found.items()}


def transpose_hand_index(cells: Grid) -> dict[str, float]:
    """The suit arm's counterfactual: every suited hand reads its offsuit twin's row, and back.

    This is what a converter produces when it reads the hand grid across where it should read it
    down, applied on purpose so the arm can be shown telling it apart from the real chart rather
    than assumed to.

    A hand is swapped only when both twins are in the grid, and the swap carries the value and the
    cell's presence together. Moving the value without the presence would measure how sparse the
    grid is instead of the mapping, which is the mistake this arm exists to catch.
    """
    swapped = dict(cells)
    for suited, offsuit in SUITED_OVER_OFFSUIT:
        if suited in cells and offsuit in cells:
            swapped[suited], swapped[offsuit] = cells[offsuit], cells[suited]
    return swapped


def reverse_rank(hand_class_text: str) -> str:
    """The hand with both its ranks turned upside down, written high card first.

    Aces become deuces, kings become treys, eights stay eights. It is its own inverse and it keeps
    a hand in its family, so it is invisible to the suit arm and needs an arm of its own.
    """
    high, low = RANK_REVERSAL[hand_class_text[0]], RANK_REVERSAL[hand_class_text[1]]
    if RANKS.index(low) < RANKS.index(high):
        high, low = low, high
    return f"{high}{low}{hand_class_text[2:]}"


def reverse_hand_ranks(cells: Grid) -> dict[str, float]:
    """The rank arm's counterfactual: a chart that opens 32o and folds aces.

    It is the shape a converter produces reading the solver's rank axis the wrong way up, and the
    suit arm cannot see it at all - pairs land on pairs and suited twins on suited twins, so that
    arm scores it exactly as it scores the real chart.

    On a grid missing some classes the result is the image of the classes that are there, never
    whatever happened to survive: a cell whose source is absent is absent too, rather than keeping
    a neighbour's value. That is why the two sides of this arm skip different comparisons, and why
    each publishes its own skipped count - one number standing for both is a figure spliced from
    two readings.
    """
    return {name: cells[reverse_rank(name)] for name in HAND_CLASSES if reverse_rank(name) in cells}


def row_comparisons_skipped(cells: Grid) -> int:
    """Kicker comparisons this grid cannot make, one hand of the pair never having arrived.

    Published rather than kept, because it says how much of a partition the rank arm was able to
    look at. A partition where nearly everything is skipped can pass on a handful of comparisons,
    and a reader who cannot see that reads the pass as wider than it is.
    """
    return sum(1 for pair in ROW_KICKERS if not all(name in cells for name in pair))


def scores_any_row_comparison(cells: Grid) -> bool:
    """Whether the rank arm can look at this grid at all.

    A spot where only one or two hands arrive offers no kicker comparison, so it contributes
    nothing and must not be counted toward the five-spot floor - a floor met by spots that scored
    nothing is a floor that is not there.
    """
    return row_comparisons_skipped(cells) < ROW_COMPARISONS_PER_FULL_GRID


def is_closed_under_reversal(cells: Grid) -> bool:
    """Whether every hand class arrived here, so the rank reversal loses nothing.

    It no longer chooses which spots the rank arm scores - that restriction was withdrawn, the
    figure said to justify it having been spliced from two different readings. What it names now
    is the coverage a grid has to have for a relation's full comparison count to be available.
    """
    return len(cells) == FULL_GRID_CELLS


def spots_violating_twins(chart: Chart) -> int:
    """The suit arm's score: spots holding at least one suited hand played under its offsuit twin.

    Spots and not cells, and the two arms never share a unit or a validator. This repo has already
    lost a day to one counterfactual's number being read through the other's rule, and the counts
    are close enough in size that the swap does not look wrong.
    """
    return sum(1 for cells in chart.values() if inversions(cells, SUITED_OVER_OFFSUIT))


def cells_violating_rows(chart: Chart) -> int:
    """The rank arm's score: kicker comparisons played the wrong way round, over every spot.

    Cells and not spots, because a rank map read upside down breaks a row in many places at once
    and counting the spot once throws that away. Every spot in the partition is scored, a
    comparison whose partner hand is absent being skipped rather than the spot being dropped.
    """
    return sum(len(inversions(cells, ROW_KICKERS)) for cells in chart.values())


def arm_refuses(solved: int, counterfactual: int) -> bool:
    """Whether an arm rejects a chart: the real hand grid did not flag strictly fewer than the
    scrambled one.

    A tie refuses. A measure that scores the real chart and the broken one alike cannot tell them
    apart, and one that cannot tell them apart catches nothing, so reading a tie as a pass would
    ship the arm with no power at all. Each arm keeps its own caller and its own words for the two
    numbers; only the direction is ever asserted, never the counts, since fixing a count picks the
    partition that reads smallest and calls that the gate.
    """
    return solved >= counterfactual
