"""Phase 14: the report generator's validators, each shown refusing a wrong input.

The companion to `tests/test_derived_chart_report.py`, split from it when the pair went past
the 700-line cap. That file owns the published report - its headings, its sections and the
numbers printed under them - and it owns the census constants, the command id and the paths
this file imports rather than copies, so the two halves cannot drift apart.

Nothing here reads a rendered report, and that is the seam. A report renders whatever it is
handed: a census that does not add up, or a spot count that disagrees with the walk that
produced it, exits 0 and publishes just as happily as the right number would. The contract
requires the generator to validate exactly four figures and to exit non-zero when they do not
hold, and this repo has twice shipped a validator that could not fail. So each is fed a
deliberately wrong input and made to refuse, and the command itself is run against a pin it
cannot resolve and against artifacts that load cleanly and are wrong. Both files run under
`pytest_derived_chart`.

**Re-cut at stage 4 three times on 2026-09-01.** The census validator now takes **five**
exclusion codes: decision 20 added the reason a four-bet pot is refused for, Taylor's first
evening ruling a second for the jam-facing nodes after those, and his second a third for the
three-bet-facing nodes before them. A validator accepting fewer accepts a vocabulary that cannot
say which nodes come back by which route, and because all three new families are 15 nodes, a
census folding any into any other adds up exactly - so the four-code, three-code, two-code and
one-code censuses are all refused here.

**And the per-cell discrimination in this file is the phase's ONLY gated range check**, ruled by
Taylor on 2026-09-01. The group-order ladders in `tests/test_chart_cutover_evidence.py` fail over
the uncut 51, pass over 36, come out mixed over 21 and separate nothing over 6, so their verdict
tracks how many spots are in the set rather than whether the hand index is right; they are
published for a human and gate nothing. This one separates cleanly at every size measured because
it is per cell. It is exercised over the real committed artifact on every partition rather than
only against hand-made inputs: a validator that only ever refuses a fabricated pair has never
been shown reading a chart.

**It carries TWO counterfactual arms since Taylor's second ruling of that day, and they are
different measures with different names.** The suit swap, `transpose_hand_index`, reads each
suited hand off its offsuit twin; it is what catches a hand index built on the grid ordering. The
final stage-4 review found what it cannot catch and measured it: a chart with every hand RANK
reversed maps pairs to pairs and suited twins to suited twins, so the suit swap scores it bit for
bit identically to a correct chart and it passes on every partition. The rank arm,
`reverse_hand_ranks`, reads each cell off its rank-reversed class and is scored on the row
ladder, which is the one relation a rank permutation breaks. Both arms are asserted the same way
- solved strictly under the counterfactual, a tie refusing - and both are proved to distinguish
what they claim to, including the case each cannot see.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest
from test_derived_chart_report import (
    ARTIFACT_DIR,
    COMMAND_ID,
    COMMITTED_SPOTS,
    EXPORTED_NODES,
    FOUR_BET_POT_CODE,
    FOUR_BET_POT_NODES,
    JAM_INHERITS_CODE,
    JAM_INHERITS_NODES,
    MULTIWAY_NODES,
    OUTSIDE_RULE_NODES,
    RETIRED_CHART,
    THREE_BET_BRANCH_CODE,
    THREE_BET_BRANCH_NODES,
    discrimination_partitions,
    git,
)

from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.importer import (
    import_preflop_artifact,
    import_preflop_artifacts,
)
from poker_training_bot.solver_artifacts.schema import weights_checksum
from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_verify import COMMANDS  # noqa: E402

SCRIPT = REPO_ROOT / "scripts" / f"{COMMAND_ID}.py"

# The hand-class rows `a_grid` builds a synthetic spot out of, strongest first.
RANKS = "AKQJT98765432"

ROW_LADDER_COMPARISONS = 132
"""The relation the rank arm is scored on, spelled out so stage 6 builds the one that was
measured. Within each row of the 13x13 grid - a fixed high card, suited and offsuit taken
separately - a hand with a higher kicker must be played at least as often as the hand one rank
below it, at decision 10's one-point tolerance. Adjacent kickers only, for the reason decision 10
gives for the pair ladder: comparing every hand against every weaker one turns one drifting step
into a dozen violations. That is 132 comparisons over a full grid, and it is a **third** relation
beside decision 10's two, needed because neither of those can see a rank permutation - the twins
relation is invariant under one, and every pocket pair is played 100 percent at all six committed
spots so the pair ladder has nothing to read. The contract names two relations and a stage-4
review owes it that correction."""

PARTITIONS_OVER_THE_COMMITTED_SET = 5
"""The whole set, one label per seat hero sits in, one per number of raises faced. Over six spots
that is five labels covering three distinct sets of spots: hero sits at the small blind and the
big blind, and faces nought raises or one, so `hero=SB` and `raises faced 0` name the same spot
and `hero=BB` and `raises faced 1` the same five. Kept rather than pruned - pruning by hand is
choosing which splits to publish after seeing them."""


def published(generator, name: str):
    """A function stage 6 owes, fetched by name rather than reached as an attribute.

    Naming an attribute the module has not grown yet raises an AttributeError inside the test
    body, which is a failure that says nothing; a `getattr` and an assertion says which function
    is missing and what it has to do - `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` again, one
    level down.
    """
    found = getattr(generator, name, None)
    assert found is not None, (
        f"scripts/{COMMAND_ID}.py must publish {name}(); the rank-permutation arm Taylor ruled"
        " on 2026-09-01 has no implementation yet"
    )
    return found


@pytest.fixture(scope="module")
def generator():
    """Reached through a fixture rather than imported at the top, for two reasons that both
    bite at stage 4: neither this module nor `chart_derivation` exists until stage 6, so a
    top-level import turns this whole file into one collection error, and an unresolvable
    module sorts into a different isort block than the same module once written.
    """
    import scripts.generate_derived_chart_report as module

    return module


@pytest.fixture(scope="module")
def derivation():
    """`chart_derivation`, reached the same way and for the same two reasons."""
    import poker_training_bot.solver_artifacts.chart_derivation as module

    return module


def a_census(
    derivation,
    committed: int = COMMITTED_SPOTS,
    excluded: Mapping[str, int] | None = None,
):
    if excluded is None:
        excluded = {
            lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: MULTIWAY_NODES,
            lookup.DERIVATION_OUTSIDE_SELECTION_RULE: OUTSIDE_RULE_NODES,
            THREE_BET_BRANCH_CODE: THREE_BET_BRANCH_NODES,
            FOUR_BET_POT_CODE: FOUR_BET_POT_NODES,
            JAM_INHERITS_CODE: JAM_INHERITS_NODES,
        }
    return derivation.NodeCensus(
        committed=committed, excluded=dict(excluded), inexpressible={}
    )


def test_the_census_is_refused_when_it_does_not_cover_the_export(derivation, generator) -> None:
    """Every node lands in exactly one bucket, or the census is a subset dressed as a census.

    The wrong inputs are the honest ones: counts that sum to one node fewer than the export
    holds, and a reason nobody ruled. Decision 8 closes both vocabularies so a node the converter
    merely failed to handle cannot be filed as a property of the grammar, and the three 2026-09-01
    rulings make that **five** exclusion codes - a census filing all 33,963 excluded nodes under
    one reason cannot say which come back when GTOpen prices multiway, which when the realization
    fit gains a four-bet-pot cell, and which when that fix reaches the jam-facing nodes after
    those and the three-bet-facing nodes before them. So one-code, two-code, three-code and
    four-code censuses are all refused, the last two because the new families are all the same
    size and folding any into any other still adds up.
    """
    # The vocabulary first, because everything below is built out of it: a census fed a reason
    # the module does not carry is refused for the wrong reason, and the refusal would read as
    # this test passing while the ruled three-reason census was the thing being rejected.
    assert set(lookup.DERIVATION_EXCLUSION_CODES) == {
        lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY,
        lookup.DERIVATION_OUTSIDE_SELECTION_RULE,
        THREE_BET_BRANCH_CODE,
        FOUR_BET_POT_CODE,
        JAM_INHERITS_CODE,
    }
    assert lookup.DERIVATION_NO_LEGAL_SPOT_KEY in lookup.DERIVATION_INEXPRESSIBILITY_CODES
    generator.validate_census(a_census(derivation), EXPORTED_NODES)

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_census(a_census(derivation), EXPORTED_NODES + 1)
    with pytest.raises(generator.DerivedChartReportError):
        short = a_census(derivation, committed=COMMITTED_SPOTS - 1)
        generator.validate_census(short, EXPORTED_NODES)
    with pytest.raises(generator.DerivedChartReportError):
        unruled = {"derivation:gave-up": EXPORTED_NODES - COMMITTED_SPOTS}
        wrong = a_census(derivation, excluded=unruled)
        generator.validate_census(wrong, EXPORTED_NODES)
    with pytest.raises(generator.DerivedChartReportError):
        one_code = a_census(
            derivation,
            excluded={
                lookup.DERIVATION_OUTSIDE_SELECTION_RULE: EXPORTED_NODES - COMMITTED_SPOTS
            },
        )
        generator.validate_census(one_code, EXPORTED_NODES)
    with pytest.raises(generator.DerivedChartReportError):
        # The vocabulary as it stood before decision 20: multiway and outside-the-rule, with the
        # thirty withheld nodes folded into one of them rather than named.
        two_codes = a_census(
            derivation,
            excluded={
                lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: MULTIWAY_NODES,
                lookup.DERIVATION_OUTSIDE_SELECTION_RULE: (
                    OUTSIDE_RULE_NODES
                    + THREE_BET_BRANCH_NODES
                    + FOUR_BET_POT_NODES
                    + JAM_INHERITS_NODES
                ),
            },
        )
        generator.validate_census(two_codes, EXPORTED_NODES)
    with pytest.raises(generator.DerivedChartReportError):
        # The vocabulary as it stood between the first and second rulings of 2026-09-01: the
        # jams folded into the four-bet-pot reason and the three-bet spots not yet withheld.
        three_codes = a_census(
            derivation,
            committed=COMMITTED_SPOTS + THREE_BET_BRANCH_NODES,
            excluded={
                lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: MULTIWAY_NODES,
                lookup.DERIVATION_OUTSIDE_SELECTION_RULE: OUTSIDE_RULE_NODES,
                FOUR_BET_POT_CODE: FOUR_BET_POT_NODES + JAM_INHERITS_NODES,
            },
        )
        generator.validate_census(three_codes, EXPORTED_NODES)
    with pytest.raises(generator.DerivedChartReportError):
        # And the vocabulary as it stood after the second ruling but before the third code was
        # written: the three-bet spots withheld and filed under the jam reason. All three
        # families are 15 nodes, so this census balances exactly and is wrong only about which
        # fix brings which nodes back - the one failure a total can never see.
        four_codes = a_census(
            derivation,
            excluded={
                lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: MULTIWAY_NODES,
                lookup.DERIVATION_OUTSIDE_SELECTION_RULE: OUTSIDE_RULE_NODES,
                FOUR_BET_POT_CODE: FOUR_BET_POT_NODES,
                JAM_INHERITS_CODE: JAM_INHERITS_NODES + THREE_BET_BRANCH_NODES,
            },
        )
        generator.validate_census(four_codes, EXPORTED_NODES)
    with pytest.raises(generator.DerivedChartReportError):
        invented = derivation.NodeCensus(
            COMMITTED_SPOTS, {}, {"derivation:not-ruled": EXPORTED_NODES - COMMITTED_SPOTS}
        )
        generator.validate_census(invented, EXPORTED_NODES)


def test_the_artifact_spot_count_is_checked_against_the_walk_key_by_key(generator) -> None:
    """A count that matches while the keys do not is the failure this has to catch: a converter
    that dropped one node and invented one key gives the same count. The last three cases are
    that, and the keys they invent are the lojack's open - one of the 24 the predicate drops -
    the big blind facing a button four-bet, one of the fifteen decision 20 withholds, and the
    button facing a big-blind three-bet, one of the fifteen the second 2026-09-01 ruling
    withholds. A converter built on the superseded rule fails on the first by name and one that
    skipped either withholding on the others."""
    walked = {"t6/d100/SB/rfi", "t6/d100/BB/BTN:raise@2.5", "t6/d100/BB/SB:raise@2.5"}
    four_bet = "t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5"
    three_bet = "t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5"
    generator.validate_spot_count(set(walked), set(walked))

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked - {"t6/d100/SB/rfi"}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked | {"t6/d100/LJ/rfi"}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count((walked - {"t6/d100/SB/rfi"}) | {"t6/d100/LJ/rfi"}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count((walked - {"t6/d100/SB/rfi"}) | {four_bet}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count((walked - {"t6/d100/SB/rfi"}) | {three_bet}, walked)


def a_grid(**overrides: float) -> dict[str, dict[str, float]]:
    """One spot's play frequency per hand class, monotone before anything is overridden."""
    cells = {f"{rank}{rank}": 100.0 - index for index, rank in enumerate(RANKS)}
    for high, low in (("A", "K"), ("K", "Q"), ("7", "6")):
        cells[f"{high}{low}s"] = 80.0
        cells[f"{high}{low}o"] = 60.0
    cells.update(overrides)
    return {"t6/d100/SB/rfi": cells}


def test_the_per_cell_relations_are_counted_at_the_tolerance_decision_10_ruled(generator) -> None:
    """The measurement, not a gate: decision 10 was re-ruled on 2026-08-24 to measure the two
    relations per cell and gate on aggregates only, so a generator that *refused* a violating
    grid would refuse the committed chart. Taylor read the grids and ruled the splits correct -
    among near-indifferent hands every split has the same EV, so the individual cells carry no
    information and only the aggregate does.

    What still has to be exactly right is the count, because it is published for a human to
    read. The lojack opening 44 at 72.81 percent under 33 at 99.88 is counted. A gap of exactly
    a point is not - 44 at 99.91 under 33 at 99.99 is not a mistake - and a ladder drifting
    nine tenths a step counts nothing though the top pair ends ten points under the bottom one,
    because the ruling compares adjacent ranks only.
    """
    assert generator.MONOTONICITY_TOLERANCE_PCT == 1.0

    def counted(grid) -> int:
        return sum(generator.count_dominance_violations(grid).values())

    assert counted(a_grid()) == 0
    assert counted(a_grid(**{"44": 90.0, "33": 91.0})) == 0
    assert counted(a_grid(**{f"{r}{r}": 88.0 + 0.9 * i for i, r in enumerate(RANKS)})) == 0

    assert counted(a_grid(**{"44": 72.81, "33": 99.88})) == 1
    assert counted(a_grid(**{"44": 90.0, "33": 91.01})) == 1
    assert counted(a_grid(AKs=50.0, AKo=80.0)) == 1
    # Both relations are counted apart, because they move in different directions and by
    # different sizes and one total hides that.
    both = generator.count_dominance_violations(a_grid(**{"44": 72.81, "33": 99.88}, AKs=50.0))
    assert set(both) == {"ladder", "twins"}
    assert both == {"ladder": 1, "twins": 1}


def test_the_group_measure_is_refused_when_it_prefers_the_transposed_hand_index(
    generator,
) -> None:
    """What decision 10's aggregate is for, and the only form of it that measured true.

    Over the 5,626 the suited-versus-offsuit aggregate flagged 2,007 nodes as solved against
    818 transposed, so it scored the *wrong* index mapping as the better one - a check that
    rewards the defect it exists to catch. The claim was withdrawn rather than restated, and
    what the generator gates is the discrimination itself: the solved mapping must violate
    strictly fewer spots than the mapping with suited and offsuit swapped. A tie is a refusal
    too, because a measure that cannot tell them apart cannot catch a transposition.
    """
    generator.validate_group_discrimination(solved=1, transposed=62)

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_group_discrimination(solved=2_007, transposed=818)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_group_discrimination(solved=6, transposed=6)


def test_the_rank_permutation_is_refused_when_it_does_not_beat_the_solved_hand_index(
    generator,
) -> None:
    """The second arm's validator, and it is a second function rather than a second call.

    `validate_group_discrimination` takes `solved` and `transposed`; this one takes `solved` and
    `permuted`. Two names because this repo has already lost a day to two different "transposed"
    counterfactuals being confused for one another, and passing a rank-permutation count into a
    parameter called `transposed` is that confusion written into the call site. The rule is the
    same and is asserted the same way: the solved hand index must break the row ladder in
    strictly fewer cells than the rank-reversed one, and a tie refuses, because a measure that
    cannot tell the two apart cannot catch a permuted index.
    """
    validate = published(generator, "validate_rank_discrimination")

    validate(solved=14, permuted=70)

    with pytest.raises(generator.DerivedChartReportError):
        validate(solved=70, permuted=14)
    with pytest.raises(generator.DerivedChartReportError):
        validate(solved=14, permuted=14)


def a_full_grid(value) -> dict[str, float]:
    """All 169 classes with `value(name)` in each. The rank map reads a cell off another class,
    so a partial grid would silently drop the cells whose partner is missing."""
    return {name: value(name) for name in HAND_CLASSES}


def kind_of(hand_class_text: str) -> int:
    """0 for a pair, 1 for suited, 2 for offsuit - the three families a rank map cannot mix."""
    return 0 if len(hand_class_text) == 2 else (1 if hand_class_text.endswith("s") else 2)


def test_the_two_counterfactuals_are_different_functions_and_neither_is_the_other(
    generator,
) -> None:
    """The trap this repo has already fallen into, closed by assertion rather than by comment.

    `transpose_hand_index` swaps each suited hand with its offsuit twin. `reverse_hand_ranks`
    reads each cell off the class with every rank reversed - ace becomes deuce, king becomes
    trey, and eight maps to itself. They are different mappings and they keep different names: a
    stage-4 reimplementation that substituted one for the other reproduced neither family's
    counts, and `group_play_pct` in `tests/test_chart_cutover_evidence.py` is a third reading
    again.

    Four properties pin the rank map. It covers the whole grid, so no cell is quietly dropped.
    It is its own inverse, so applying it twice is the identity and the counterfactual is well
    defined. It maps pairs to pairs, suited to suited and offsuit to offsuit - **which is
    precisely why the suit swap cannot see it**, the twins relation comparing a suited hand with
    its offsuit twin and a rank map permuting those comparisons among themselves. And it is not
    the identity, which a mapping that failed to find its classes would be.
    """
    reverse = published(generator, "reverse_hand_ranks")
    ranked = a_full_grid(lambda name: float(HAND_CLASSES.index(name)))
    kinds = a_full_grid(lambda name: float(kind_of(name)))
    permuted = reverse(ranked)

    assert set(permuted) == set(ranked) == set(HAND_CLASSES)
    assert reverse(permuted) == ranked, "the rank map is not its own inverse"
    assert permuted != ranked, "the rank map left the grid alone"
    assert permuted["AA"] == ranked["22"] and permuted["22"] == ranked["AA"]
    assert permuted["88"] == ranked["88"], "the middle rank maps to itself under a reversal"
    assert permuted["AKs"] == ranked["32s"] and permuted["AKo"] == ranked["32o"]
    assert reverse(kinds) == kinds, "the rank map moved a cell between pairs, suited and offsuit"

    # And it is not the suit swap, which moves cells the other way: across the twins relation
    # and never across ranks.
    swapped = generator.transpose_hand_index(ranked)
    assert swapped != permuted
    assert swapped["AKs"] == ranked["AKo"] and swapped["AKo"] == ranked["AKs"]
    assert swapped["AA"] == ranked["AA"], "the suit swap moved a pair"


def test_both_arms_discriminate_on_every_partition_of_the_committed_set(generator) -> None:
    """The phase's only gated range check, run over the real chart on each partition, through
    the validators that ship.

    **Ruled by Taylor on 2026-09-01, twice.** The group-order ladders in
    `tests/test_chart_cutover_evidence.py` returned a different verdict on every committed set -
    fail over the uncut 51, pass over 36, mixed over 21, blind over 6 - so they measure set
    composition rather than the hand index, and they now publish rather than gate. Nothing else
    in the phase would notice a wrong hand index, so a red here is a halt and not a number to
    soften.

    The refusal tests above prove each validator says no to a bad pair of numbers. They cannot
    show the numbers it will actually be handed are good ones, and the contract's amendment
    states the gate **on every partition** rather than over the committed set as a whole. So the
    shipped measures are run here against the committed artifact and every partition is put
    through its validator - the same functions the report calls, not second copies of the rules.

    **What the partitions are for.** A measure can separate over the whole chart and still be
    blind on the part that matters: a converter reading the payload by the grid ordering only
    where hero faces a raise breaks the deep spots and leaves the shallow ones right, and an
    aggregate absorbs that. Splitting by hero's seat catches a mis-assigned actor the same way.

    **Re-measured over the committed 6 on 2026-09-01, with the shipped functions.** The suit
    swap reads 0 flagged under the solver's own class ordering against 6 under the swapped one
    over the whole set, 0 against 5 at the big blind and at `raises faced 1`, and 0 against 1 at
    the small blind and at `raises faced 0`. The rank arm reads 14 cells against 70 over the set,
    11 against 55 at the big blind and at `raises faced 1`, and 3 against 15 at the small blind
    and at `raises faced 0`. None ties. There are five partitions rather than ten because the
    three withholdings took four of hero's six seats and three of the five raise counts out.

    **The rank arm counts cells where the suit arm counts spots, and that is measured rather
    than stylistic.** Over six spots every rank-sensitive relation flags at least one cell at
    every spot under both mappings, so a spot count reads 6 against 6 and saturates exactly the
    way the group ladders do - the failure that retired them. Counting cells keeps the two
    mappings apart at every partition. The counts here are recorded rather than asserted, the
    ruling being the direction: fixing a count fixes a partition, and picking the partition that
    reads smallest is picking a number to go green.
    """
    reverse = published(generator, "reverse_hand_ranks")
    row_ladder = published(generator, "cells_violating_the_row_ladder")
    validate_rank = published(generator, "validate_rank_discrimination")
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]
    grid = generator.play_grid(artifact)
    descending = a_full_grid(lambda name: 100.0 - 5.0 * RANKS.index(name[1]))
    ascending = a_full_grid(lambda name: 5.0 * RANKS.index(name[1]))
    by_label: dict[str, tuple[str, ...]] = {"the committed set": tuple(grid)}
    for spot in artifact.spots:
        faced = sum(1 for entry in spot.action_sequence if entry.action == "raise")
        for label in (f"hero={spot.hero_position}", f"raises faced {faced}"):
            by_label[label] = (*by_label.get(label, ()), spot.spot_id)

    # The row ladder is shown counting before it is trusted to count zero anywhere. A grid whose
    # value falls with the kicker violates nothing; the same grid with aces-king folded outright
    # violates once, at that one step and nowhere else; a grid whose value rises with the kicker
    # violates every comparison there is, which pins the comparison count at the ruled 132
    # rather than at every pair in a row; and a flat grid violates nothing, so the count is of
    # gaps strictly past the tolerance rather than of differences.
    assert row_ladder({"probe": descending}) == 0
    assert row_ladder({"probe": descending | {"AKs": 0.0}}) == 1
    assert row_ladder({"probe": ascending}) == ROW_LADDER_COMPARISONS
    assert row_ladder({"probe": a_full_grid(lambda name: 0.0)}) == 0

    assert len(artifact.spots) == COMMITTED_SPOTS
    assert set(by_label) == discrimination_partitions(artifact)
    assert len(by_label) == PARTITIONS_OVER_THE_COMMITTED_SET, (
        "the committed set no longer splits into the five measured parts"
    )
    for label, keys in by_label.items():
        part = {key: grid[key] for key in keys}
        solved = generator.spots_violating_twins(part)
        transposed = generator.spots_violating_twins(
            {key: generator.transpose_hand_index(cells) for key, cells in part.items()}
        )
        rank_solved = row_ladder(part)
        permuted = row_ladder({key: reverse(cells) for key, cells in part.items()})

        assert solved < transposed, ("suit swap", label, solved, transposed)
        assert rank_solved < permuted, ("rank reversal", label, rank_solved, permuted)
        # Through the validators as well as beside them: a partition this test calls good and
        # the gate calls bad is a gate nobody is testing. Asserted first so a partition that
        # fails fails as an assertion rather than as the validator's own exception.
        generator.validate_group_discrimination(solved=solved, transposed=transposed)
        validate_rank(solved=rank_solved, permuted=permuted)


def test_the_rank_arm_catches_the_reversed_chart_the_suit_swap_cannot_tell_apart(
    generator,
) -> None:
    """The hole the final stage-4 review found, and the proof that the second arm closes it.

    A chart with every hand rank reversed is a chart that opens 32o and folds aces. It is the
    shape a converter produces if it reads GTOpen's rank axis the wrong way up, and nothing in
    this phase noticed it: the suit swap moves weights and reach together, pairs map to pairs and
    suited twins to suited twins, so the cell-subset relation holds and the aggregate defence
    percentages are unchanged. The review measured it scoring **bit for bit identically to a
    correct chart** and passing the only gated range check on every partition.

    So the reversed chart is built here and put through both arms. The suit swap is asserted to
    be *unable* to tell it from the real one - the same solved figure, the same transposed
    figure, and `validate_group_discrimination` passing it - which is the hole stated as a
    measurement rather than as a worry. The rank arm is then asserted to refuse it, on the same
    validator that accepted the real chart a few lines above.

    Both directions matter. An arm that refused everything would also refuse the reversed chart,
    so the real chart is put through first and must pass; an arm that accepted everything would
    pass the reversed chart, so the reversed chart must be refused.
    """
    reverse = published(generator, "reverse_hand_ranks")
    row_ladder = published(generator, "cells_violating_the_row_ladder")
    validate_rank = published(generator, "validate_rank_discrimination")
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]
    grid = generator.play_grid(artifact)
    reversed_chart = {key: reverse(cells) for key, cells in grid.items()}

    def suit_arm(chart) -> tuple[int, int]:
        swapped = {key: generator.transpose_hand_index(cells) for key, cells in chart.items()}
        return generator.spots_violating_twins(chart), generator.spots_violating_twins(swapped)

    def rank_arm(chart) -> tuple[int, int]:
        permuted = {key: reverse(cells) for key, cells in chart.items()}
        return row_ladder(chart), row_ladder(permuted)

    assert len(artifact.spots) == COMMITTED_SPOTS
    assert reversed_chart != grid, "the reversed chart is the same chart, so nothing is proved"

    # The hole: the suit swap reads the reversed chart exactly as it reads the real one, and
    # its validator accepts it. This is asserted rather than described.
    assert suit_arm(reversed_chart) == suit_arm(grid)
    blind_solved, blind_transposed = suit_arm(reversed_chart)
    generator.validate_group_discrimination(solved=blind_solved, transposed=blind_transposed)

    # The close: the rank arm accepts the real chart and refuses the reversed one.
    solved, permuted = rank_arm(grid)
    assert solved < permuted, (solved, permuted)
    validate_rank(solved=solved, permuted=permuted)

    reversed_solved, reversed_permuted = rank_arm(reversed_chart)
    assert reversed_solved > reversed_permuted, (reversed_solved, reversed_permuted)
    with pytest.raises(generator.DerivedChartReportError):
        validate_rank(solved=reversed_solved, permuted=reversed_permuted)


def test_the_old_versus_new_disagreement_count_is_refused_when_it_cannot_be_read(generator) -> None:
    """A comparison that did not happen arrives as a small consistent number, not as an error.

    Every case below is one shape: a validator that only checks a count's arithmetic cannot
    tell a real zero from an input that quietly became trivial - an empty overlap, a pin that
    no longer resolves, a retired chart read as zero spots, or a comparison handed the derived
    chart twice. The poker rules the last one out on its own, because the two charts share no
    three-bet price and no small-blind opening price: the retired one prices them at 8, 11,
    13.5 and 3.5 against the derived chart's 7.5 and 2.5, and the derived chart holds only
    four prices in all, so they cannot agree on every shared corpus decision.
    `corpus-self-play-crossref-empties-silently` is the same failure in another subsystem.
    """
    ways = {"derived continues, retired folds": 140, "retired continues, derived folds": 40}
    generator.validate_disagreement(shared_decisions=1200, disagreements=180, by_direction=ways)

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(shared_decisions=0, disagreements=0, by_direction={})
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(shared_decisions=1200, disagreements=0, by_direction={})
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(shared_decisions=1200, disagreements=181, by_direction=ways)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(shared_decisions=100, disagreements=180, by_direction=ways)


def run_report(tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    # Or a missing script would make every refusal below pass without a validator existing.
    assert SCRIPT.exists(), f"{SCRIPT} does not exist, so nothing here runs a validator"
    command = [sys.executable, str(SCRIPT), "--output", str(tmp_path / "report.txt"), *arguments]
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)


def test_the_gate_command_runs_this_script() -> None:
    """A validator the gate does not run is a validator nothing runs."""
    assert COMMAND_ID in COMMANDS
    assert any(str(SCRIPT.relative_to(REPO_ROOT)) in part for part in COMMANDS[COMMAND_ID].command)


@pytest.mark.parametrize("pin", ["nonexistent", "root"])
def test_a_pin_the_retired_chart_cannot_be_read_at_fails_the_command(tmp_path, pin) -> None:
    """Decision 7 reads the retired chart out of git history, so the pin is an input.

    Both bad pins fail differently. One is not a commit at all; the other is a real commit at
    which the retired chart does not exist, which a resolvable-looking sha sails past. A copy
    kept under `data/artifacts/preflop/` in a subdirectory the importer's non-recursive glob
    misses was rejected for this: it works, and it makes a reader ask which chart plays.
    """
    commit = "0" * 40
    if pin == "root":
        commit = git("rev-list", "--max-parents=0", "HEAD").stdout.split()[-1]
        assert git("cat-file", "-e", f"{commit}:{RETIRED_CHART}").returncode != 0

    result = run_report(tmp_path, "--retired-commit", commit)

    assert result.returncode != 0, result.stdout + result.stderr
    assert not (tmp_path / "report.txt").exists(), "a refused report must not also be published"


def corrupted_artifact(tmp_path: Path, how: str) -> Path:
    paths = sorted(ARTIFACT_DIR.glob("*.json"))
    assert len(paths) == 1, f"expected exactly one committed preflop artifact, found {paths}"
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    if how == "drop-a-spot":
        dropped = payload["spots"][0]["spot_id"]
        payload["spots"] = [spot for spot in payload["spots"] if spot["spot_id"] != dropped]
        # Every per-spot map has to lose the spot as well, or the importer refuses the file
        # for its own reason and no validator here is ever reached. The forms differ because
        # the density rules do: `action_weights` and `arriving_reach_bp` owe an entry for
        # every declared spot, so a missing key is a broken assumption worth raising, while
        # `arrival_ppb` need only be a subset of `spots` in `spots` order and a spot may
        # legitimately have no entry at all.
        del payload["action_weights"][dropped]
        del payload["arriving_reach_bp"][dropped]
        payload["arrival_ppb"].pop(dropped, None)
        payload["audit_fields"]["spot_count"] = len(payload["spots"])
    else:
        # A spot the predicate excludes, made to look committed: the lojack's own open, one of
        # the 24 whose terminals GTOpen cannot price. Its cells are copied off a spot that is
        # committed, so the artifact stays internally consistent and only a comparison against
        # the walk can see it.
        source = "t6/d100/SB/rfi"
        assert source in payload["action_weights"], f"{source} is not in the committed artifact"
        invented = "t6/d100/LJ/rfi"
        payload["spots"].append(
            {"spot_id": invented, "hero_position": "LJ", "action_sequence": []}
        )
        payload["action_weights"][invented] = dict(payload["action_weights"][source])
        payload["arriving_reach_bp"][invented] = dict(payload["arriving_reach_bp"][source])
        payload["audit_fields"]["spot_count"] = len(payload["spots"])
    # Restamped through the repo's own checksum, so the corruption stays a valid artifact.
    weights = tuple(
        (spot, tuple((text, tuple(acts.items())) for text, acts in sorted(cells.items())))
        for spot, cells in sorted(payload["action_weights"].items())
    )
    payload["audit_fields"]["weights_sha256"] = weights_checksum(weights)
    path = tmp_path / "corrupted.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    # It has to stay a valid artifact. If the schema rejected it the command would exit
    # non-zero for the loader's reason and this test would prove nothing about the report.
    import_preflop_artifact(path)
    return path


@pytest.mark.parametrize("how", ["drop-a-spot", "commit-a-multiway-spot"])
def test_a_wrong_artifact_fails_the_command_rather_than_being_rendered(tmp_path, how) -> None:
    """Both artifacts below load cleanly and are wrong, which is the case that matters.

    One holds a spot fewer than the walk selected and says so in its own audit fields, so only
    a comparison against the export sees it. The other holds one more: the lojack's opening
    range, which is heads-up by action history and has a multiway terminal below every branch.
    That is the artifact a converter built on the superseded predicate produces, and nothing
    but the walk notices - the cell converts, imports, and answers.
    """
    result = run_report(tmp_path, "--artifact", str(corrupted_artifact(tmp_path, how)))

    assert result.returncode != 0, result.stdout + result.stderr
    assert not (tmp_path / "report.txt").exists()
