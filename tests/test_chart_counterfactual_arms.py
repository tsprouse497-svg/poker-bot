"""The two counterfactual arms over the committed ranges, and the ten partitions they run on.

Split out of `test_chart_cutover_evidence.py`, which stays the owner of **every number** used
here - the pinned arms, the ten partition rows, the tolerance, the comparison lists - and of the
grid walks and the two permutations. What lives here is the scoring itself: the functions that
turn grids into an arm's figures, and the tests that run them. Nothing in this file defines a
number, so a count still has one home.

**The arms are what this phase gates on.** The suit arm transposes each suited hand with its
offsuit twin and scores spots; the rank arm reverses every rank and scores cells on the row
ladder. Both are strict, a tie refuses on each, and both run on all ten partitions - the whole
set, one per hero seat, one per raises faced - measured from the committed set and never carried
over.

**The rank arm is scored over every spot in its partition**, a comparison whose partner cell is
absent being skipped, and what it skipped is published per partition on both sides.
`reverse_hand_ranks` is total only on a full grid and 83 of the 249 carry one, which is why 19,774
of the solved side's 32,868 possible comparisons and 20,279 of the permuted side's are skipped. A
partition scoring fewer than five spots publishes rather than asserts; none does, the smallest
scoring exactly five.

**The restriction to spots closed under reversal is withdrawn** - Taylor's ruling of 2026-09-03,
`RANK-ARM-RESTRICTION-RESTED-ON-A-SPLICED-FIGURE`. The claim it rested on, that over all 219
three-bet-facing spots the arm reads "149 against 69" and fails, is not a reading of anything: 149
is the solved side of the skip rule and 69 the counterfactual side of a different rule. Both
self-consistent readings pass, and the test below measures both rather than saying so. The
tightest margin over the ten partitions is `hero=LJ` at 75 against 96. If an arm ever does go red
the tolerance and which comparisons count are still frozen: that is a halt and a decision for
Taylor, never a tolerance re-derived until it admits the artifact it judges.

**Neither arm passing is evidence the ranges are sound**, and one test proves that rather than
saying it: both arms score a chart with every spot's grid moved onto the wrong spot identically to
the real one, and both accept a chart that folds twice as much everywhere.
`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR`.

`scripts/generate_derived_chart_report.py` is reached as a module, so a name stage 6 has yet to
add is one `AttributeError` here rather than a collection error in every file.
"""

from __future__ import annotations

import pytest
import test_chart_cutover_evidence as evidence
import test_chart_derivation as derivation

import scripts.generate_derived_chart_report as report
from poker_training_bot.solver_artifacts.gtopen_export import SolverExport, SolverNode
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES

ARMS = evidence.ARMS
PARTITIONS = evidence.PARTITIONS
RANK_ARM_SPOT_FLOOR = evidence.RANK_ARM_SPOT_FLOOR
ROW_COMPARISONS_PER_FULL_GRID = evidence.ROW_COMPARISONS_PER_FULL_GRID
ROW_KICKERS = evidence.ROW_KICKERS
SEATS = evidence.SEATS
SPOTS_FOLDING_EVERY_HAND = evidence.SPOTS_FOLDING_EVERY_HAND
SUITED_OVER_OFFSUIT = evidence.SUITED_OVER_OFFSUIT
inversions = evidence.inversions
is_closed_under_reversal = evidence.is_closed_under_reversal
partitioned = evidence.partitioned
play_not_fold = evidence.play_not_fold
reverse_hand_ranks = evidence.reverse_hand_ranks
reverse_rank = evidence.reverse_rank
transpose_hand_index = evidence.transpose_hand_index
"""Names bound to their owner rather than redefined. `test_chart_cutover_evidence.py` is the one
place any of these is written down, so this file cannot drift from it or hold a stale copy."""


# --- The scoring, which is what an arm is ---------------------------------------------------- #


def spots_violating_twins(grids) -> int:
    """The suit arm's score: spots holding at least one suited-under-offsuit cell."""
    return sum(1 for cells in grids if inversions(cells, SUITED_OVER_OFFSUIT))


def cells_violating_rows(grids) -> int:
    """The rank arm's score: row-ladder comparisons played the wrong way round, over every spot in
    the partition, a comparison whose partner cell is absent being skipped."""
    return sum(len(inversions(cells, ROW_KICKERS)) for cells in grids)


def row_comparisons_skipped(cells: dict[str, float]) -> int:
    """Row-ladder comparisons this grid cannot score, one cell of the pair being absent."""
    return sum(1 for pair in ROW_KICKERS if not all(name in cells for name in pair))


def scores_any_row_comparison(cells: dict[str, float]) -> bool:
    """Whether the rank arm can look at this grid at all. A spot arriving at one class scores
    nothing, and the five-spot floor is counted over the spots that score something."""
    return row_comparisons_skipped(cells) < ROW_COMPARISONS_PER_FULL_GRID


def arm_refuses(solved: int, counterfactual: int) -> bool:
    """Both arms are strict and a tie refuses on each: a measure that cannot tell the solved index
    from the permuted one cannot catch the permutation."""
    return solved >= counterfactual


def arm_scores(chart) -> tuple[int, int, int, int]:
    """Both arms' four numbers over one chart, given as one grid per spot: suit solved, suit
    counterfactual, rank solved, rank counterfactual. Both arms read every spot."""
    return (
        spots_violating_twins(chart),
        spots_violating_twins([transpose_hand_index(cells) for cells in chart]),
        cells_violating_rows(chart),
        cells_violating_rows([reverse_hand_ranks(cells) for cells in chart]),
    )


def rank_arm_coverage(chart) -> tuple[int, int, int]:
    """What the rank arm could and could not look at: the spots scoring at least one comparison,
    then the comparisons skipped on the solved side and on the permuted one. The two differ
    because the reversal carries a present cell onto a different row, and they are published apart
    for that reason - one number standing for both is how "149 against 69" was built."""
    permuted = [reverse_hand_ranks(cells) for cells in chart]
    return (
        sum(1 for cells in chart if scores_any_row_comparison(cells)),
        sum(row_comparisons_skipped(cells) for cells in chart),
        sum(row_comparisons_skipped(cells) for cells in permuted),
    )


def arm_verdicts(chart) -> tuple[bool, bool]:
    """Whether each arm refuses a chart. A tie refuses on both."""
    suit_solved, suit_other, rank_solved, rank_other = arm_scores(chart)
    return arm_refuses(suit_solved, suit_other), arm_refuses(rank_solved, rank_other)


@pytest.fixture(scope="module")
def export() -> SolverExport:
    return evidence.load_committed_export()


@pytest.fixture(scope="module")
def committed(export: SolverExport) -> tuple[SolverNode, ...]:
    """The committed set, from the lane that owns the selection rule rather than re-derived."""
    return evidence.select_committed(export)


@pytest.fixture(scope="module")
def tree(export: SolverExport) -> tuple[dict, dict]:
    """How many raises are already in when hero acts, and which seat put the last one in."""
    return evidence.build_tree(export)


def test_the_two_arms_are_pinned_as_data_and_share_nothing(
    committed: tuple[SolverNode, ...],
) -> None:
    """Two arms, both strict, a tie refusing on each, each keeping its own validator and
    parameter name. Sharing a parameter is how one arm's number gets read as the other's, so the
    permutations, the parameters and the scoring units are asserted pairwise distinct.

    The permutations are the report generator's own, reached as attributes so that
    `reverse_hand_ranks`, which stage 6 adds, is one `AttributeError` here rather than a
    collection error in every file of the family. Each is checked against this file's own walk on
    a real committed grid, so the two are the same map rather than two names for a guess. Applying
    either twice must be a no-op, which is what makes the counterfactual well defined.

    The rank arm's declared scope is asserted too, the restriction Taylor withdrew being the kind
    of thing that comes back as a one-word edit to a data row."""
    assert len(ARMS) == 2
    for field in ("name", "permutation", "parameter", "unit"):
        values = [getattr(arm, field) for arm in ARMS]
        assert len(set(values)) == 2, (field, values)
    assert {arm.unit for arm in ARMS} == {"spots", "cells"}
    assert ARMS[0].spot_floor is None
    assert ARMS[1].spot_floor == RANK_ARM_SPOT_FLOOR == 5
    assert ARMS[1].scored_over == "every committed spot, absent-partner comparisons skipped"
    assert arm_refuses(3, 3) and arm_refuses(4, 3) and not arm_refuses(2, 3)
    assert all(reverse_rank(reverse_rank(name)) == name for name in HAND_CLASSES)
    assert {reverse_rank(name) for name in HAND_CLASSES} == set(HAND_CLASSES)

    cells = play_not_fold(committed[0])
    assert report.transpose_hand_index(cells) == transpose_hand_index(cells)
    assert report.reverse_hand_ranks(cells) == reverse_hand_ranks(cells)
    assert transpose_hand_index(transpose_hand_index(cells)) == cells
    assert reverse_hand_ranks(reverse_hand_ranks(cells)) == cells


def test_both_arms_prefer_the_solved_hand_index_on_every_partition(
    committed: tuple[SolverNode, ...], tree: tuple[dict, dict]
) -> None:
    """The gate. Ten partitions, both arms, measured from the committed set and never carried over
    from an earlier one.

    What is asserted is the direction - the solved index flags strictly fewer than the
    counterfactual - and not the counts, because a count fixes a partition and choosing the
    partition that reads smallest is picking a number to go green. The counts are checked anyway,
    as the figures two independent walks re-derived on 2026-09-03, so a walk that silently stops
    comparing goes red on the numbers rather than passing on a vacuous direction.

    **If this goes red, nothing here is adjusted.** Not the tolerance and not which comparisons
    count. The contract calls a failure a halt and a decision for Taylor. Every partition is
    asserted, none scoring below the five-spot floor, and the closest of the ten is `hero=LJ` at
    75 against 96."""
    faced, _ = tree
    groups = partitioned(committed, faced)
    expected = {figures.name: figures for figures in PARTITIONS}

    assert set(groups) == set(expected), "a partition was dropped or renamed"
    assert sum(len(groups[f"hero={seat}"]) for seat in SEATS) == derivation.COMMITTED_NODES
    assert sum(len(groups[f"raises faced {r}"]) for r in (0, 1, 2)) == derivation.COMMITTED_NODES

    for name, nodes in groups.items():
        figures = expected[name]
        grids = [play_not_fold(node) for node in nodes]
        suit_solved, suit_other, rank_solved, rank_other = arm_scores(grids)
        scored, skipped, skipped_permuted = rank_arm_coverage(grids)
        measured = {
            "spots": len(nodes),
            "suit_solved": suit_solved,
            "suit_counterfactual": suit_other,
            "rank_scored_spots": scored,
            "rank_solved": rank_solved,
            "rank_counterfactual": rank_other,
            "rank_skipped": skipped,
            "rank_skipped_permuted": skipped_permuted,
        }
        for field, value in measured.items():
            assert value == getattr(figures, field), (name, field, value, figures)

        assert not arm_refuses(suit_solved, suit_other), (
            f"the suit arm does not prefer the solved index at {name}: that is a halt and a"
            " decision for Taylor, not a tolerance to re-derive"
        )
        assert scored >= RANK_ARM_SPOT_FLOOR, (name, scored)
        assert not arm_refuses(rank_solved, rank_other), (
            f"the rank arm does not prefer the solved index at {name}: that is a halt and a"
            " decision for Taylor, not a tolerance to re-derive"
        )


def test_the_rank_arm_is_scored_on_every_spot_and_says_what_it_skipped(
    committed: tuple[SolverNode, ...], tree: tuple[dict, dict]
) -> None:
    """`reverse_hand_ranks` is total only on a full grid, so the arm scores every spot and skips
    the comparisons whose partner cell is absent, publishing what it skipped per partition on each
    side. Both sides are published because they differ: the reversal carries a present cell onto a
    different row, so the two skip different comparisons.

    **The withdrawn restriction is measured here rather than argued about.** The claim that the
    unrestricted arm fails - "149 against 69" over the 219 three-bet-facing spots - is not a
    reading of anything. Under the skip rule that partition reads 149 against 260 and passes;
    restricted to the spots closed under reversal it reads 32 against 33 and also passes. The
    failing figure took the solved side of the first and the counterfactual side of the second.
    Both readings are computed below and both must pass, so a later hand that wants the
    restriction back has to make one of them fail first.

    The five-spot floor is kept and has no instance here: every partition scores at least five
    spots and the smallest scores exactly five."""
    faced, _ = tree
    groups = partitioned(committed, faced)
    expected = {figures.name: figures for figures in PARTITIONS}
    skipped: dict[str, tuple[int, int]] = {}

    for name, nodes in groups.items():
        grids = [play_not_fold(node) for node in nodes]
        scored_spots, solved_side, permuted_side = rank_arm_coverage(grids)
        possible = ROW_COMPARISONS_PER_FULL_GRID * len(nodes)
        skipped[name] = (solved_side, permuted_side)

        assert (scored_spots, solved_side, permuted_side) == (
            expected[name].rank_scored_spots,
            expected[name].rank_skipped,
            expected[name].rank_skipped_permuted,
        ), name
        assert 0 <= solved_side < possible and 0 <= permuted_side < possible, name
        assert scored_spots >= RANK_ARM_SPOT_FLOOR, (name, scored_spots)

    whole = skipped["the committed set"]
    assert len(skipped) == 10, "the skipped count is published per partition, all ten of them"
    for side in (0, 1):
        assert sum(skipped[f"hero={seat}"][side] for seat in SEATS) == whole[side]
        assert sum(skipped[f"raises faced {r}"][side] for r in (0, 1, 2)) == whole[side]

    three_bet = [play_not_fold(node) for node in groups["raises faced 2"]]
    closed = [cells for cells in three_bet if is_closed_under_reversal(cells)]
    for label, grids in (("every spot, partners skipped", three_bet), ("closed spots", closed)):
        solved = cells_violating_rows(grids)
        permuted = cells_violating_rows([reverse_hand_ranks(cells) for cells in grids])
        assert not arm_refuses(solved, permuted), (label, solved, permuted)


def test_the_rank_arm_discriminates_where_the_suit_arm_cannot(
    committed: tuple[SolverNode, ...],
) -> None:
    """Why there are two arms rather than one.

    A chart with every hand rank reversed - aces where the deuces were - is a broken extraction
    of exactly the kind the gate exists to catch. It scores identically on the suit arm, because
    reversing ranks carries a suited hand and its offsuit twin together, so that arm accepts it
    with the same two numbers it gives the real chart. The rank arm refuses it.

    Asserted both ways round: the suit arm's pair of figures on the reversed chart equals its
    pair on the solved one to the unit, and the rank arm's verdict flips."""
    grids = [play_not_fold(node) for node in committed]
    reversed_chart = [reverse_hand_ranks(cells) for cells in grids]

    solved_suit = arm_scores(grids)[:2]
    reversed_suit = arm_scores(reversed_chart)[:2]

    assert reversed_suit == solved_suit, (reversed_suit, solved_suit)
    assert arm_verdicts(grids) == (False, False), "the committed chart must pass both arms"
    assert arm_verdicts(reversed_chart) == (False, True), (
        "the suit arm was expected to accept a rank-reversed chart and the rank arm to refuse"
        " it; if the rank arm accepts it the second arm buys nothing"
    )


def test_neither_arm_passing_is_evidence_the_ranges_are_sound(
    committed: tuple[SolverNode, ...],
) -> None:
    """`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR`, demonstrated
    rather than asserted in prose, because a limitation nobody can reproduce gets forgotten.

    Two broken charts, both of which this gate would ship. **A mis-assigned actor**: every spot's
    grid moved onto the next spot, so the bot answers the button with the small blind's range.
    Both arms score it to the unit exactly as they score the real chart, because both are
    per-spot measures and the multiset of grids has not changed. **Over-folding**: every cell
    plays half as often, which is the defect decision 34 accepts in the big blind and which
    nothing here can see, both arms comparing cells against each other rather than against any
    external level.

    The over-folded chart differs from the committed one at 236 of the 249 spots and at none of
    the other 13, because those 13 fold every hand that reaches them and half of zero is zero. No
    over-folding of a chart can move a grid that already folds everything, so the fixture is right
    and the count is what has to say so.

    A green gate here means the hand index survived extraction. It does not mean the ranges are
    good poker, and nothing in this repo measures whether they are."""
    grids = [play_not_fold(node) for node in committed]
    mis_assigned = grids[1:] + grids[:1]
    over_folding = [{name: value * 0.5 for name, value in cells.items()} for cells in grids]
    folds_everything = [cells for cells in grids if not any(cells.values())]

    assert arm_verdicts(grids) == (False, False), "the committed chart must pass both arms"
    assert arm_scores(mis_assigned) == arm_scores(grids), (
        "the arms told the mis-assigned chart apart, which would be better than the contract"
        " claims and would mean this demonstration is stale"
    )
    assert arm_verdicts(mis_assigned) == (False, False)
    assert arm_verdicts(over_folding) == (False, False)
    assert len(folds_everything) == SPOTS_FOLDING_EVERY_HAND == 13
    assert sum(
        1 for before, after in zip(grids, over_folding, strict=True) if before != after
    ) == len(grids) - len(folds_everything), (
        "the over-folded chart differs from the committed one at a spot that plays something, or"
        " matches it at one that does, so this fixture is not the over-folding it claims to be"
    )
