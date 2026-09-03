"""Phase 14: the report generator's validators, each shown refusing a wrong input.

The companion to `tests/test_derived_chart_report.py`, split from it at the 700-line cap. That
file owns the rendered report and the counts, paths and walk helpers this file reaches rather than
copies, so the two halves cannot drift apart. Both run under `pytest_derived_chart`.

**What is here is the negative half.** A report renders whatever it is handed: a census that does
not cover the export, a spot count that disagrees with the walk that produced it, or an arm whose
counterfactual scores better than the solved index all exit 0 and publish as happily as the right
numbers would. The contract requires the generator to re-derive every figure it names as an
obligation and to **exit non-zero when one does not hold**, and this repo has twice shipped a
validator that could not fail. So each is fed a wrong input and made to refuse, the command is run
against a pin it cannot resolve and against artifacts that load cleanly and are wrong, and one
positive control asserts it still publishes on good input - four refusal tests read
`returncode != 0`, which a script that refuses everything satisfies.

**Re-cut at stage 4 on 2026-09-02, against the 249.** Every earlier cut described a superseded set
- six spots, before that 143 nodes, before that 86 - under a five-code refusal vocabulary of which
not one code survives. Decisions 46, 48, 49, 50 and 53 replace it: three refusal codes, **249** of
**33,969** nodes, **four** per-cell relations, and two arms over **ten** partitions, the rank arm
scoring every spot and skipping the comparisons whose partner cell is absent.

**Neither arm passing is evidence the ranges are sound.** Decision 42 settled that nothing here
gates on whether a range is good poker: both are extraction checks, blind to over-folding, a
mis-assigned actor and a cross-family inversion. The rank arm exists because the suit arm cannot
see a hand index read upside down: a chart with every rank reversed maps pairs to pairs and twins
to twins, so the suit swap scores it as a correct chart.

**The restriction to spots closed under reversal was withdrawn on 2026-09-03**
(`RANK-ARM-RESTRICTION-RESTED-ON-A-SPLICED-FIGURE`), and the one-cell margin this file used to
warn about was an artefact of it. `tests/test_chart_counterfactual_arms.py` carries the account;
what matters here is that the tightest of the ten partitions is `hero=LJ` at 75 against 96, and
that a red is a halt, never a number softened until it admits the artifact it judges.
"""

from __future__ import annotations

import inspect
import json
import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest
import test_chart_derivation as derivation_tests
import test_derived_chart_report as report_tests

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

SCRIPT = REPO_ROOT / "scripts" / f"{report_tests.COMMAND_ID}.py"

RETIRED_CHART = "data/artifacts/preflop/six_max_100bb_rakefree.json"
"""The 86-spot chart this phase retires, read out of git at the pin the ledger names rather than
kept as a second copy, the arrangement that makes a reader ask which chart the bot plays. Its
sizing table is `report_tests.RETIRED_SIZINGS` and shares its basename."""

RANKS = "AKQJT98765432"

RELATION_KEYS = (
    "pair ladder",
    "suited over its offsuit twin",
    "row kicker ladder",
    "pair ladder on the raise weight",
)
"""The four counts the generator publishes, keyed so a printed row reads back to the relation it
came from. Three run on play-not-fold under the names `tests/test_chart_cutover_evidence.py` pins
as data. The fourth is decision 50's and reads the **merged raise weight the bot plays**, the
inversion that halted this phase sitting at cells where both hands are played 100 percent."""


def published(generator, name: str):
    """A function stage 6 owes, fetched by name rather than reached as a bare attribute: a missing
    attribute raises an `AttributeError` that says nothing about what is missing, where a `getattr`
    and an assertion say which function is owed and why
    (`LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`, one level below the import rule)."""
    found = getattr(generator, name, None)
    assert found is not None, (
        f"scripts/{report_tests.COMMAND_ID}.py must publish {name}(), which the 2026-09-02"
        " rulings require and which the generator does not implement yet"
    )
    return found


@pytest.fixture(scope="module")
def generator():
    """Reached through a fixture rather than imported at the top: a top-level import of a module
    stage 6 has not finished turns this file into one collection error, which runs no assertion."""
    import scripts.generate_derived_chart_report as module

    return module


@pytest.fixture(scope="module")
def derivation():
    """`chart_derivation`, reached the same way and for the same reason."""
    import poker_training_bot.solver_artifacts.chart_derivation as module

    return module


@pytest.fixture(scope="module")
def report_text(generator) -> str:
    output = generator.REPORT_OUTPUT
    assert output.exists(), f"{output} is missing, so `{report_tests.COMMAND_ID}` has not run"
    return output.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def artifact():
    found = import_preflop_artifacts(report_tests.ARTIFACT_DIR)
    assert len(found) == 1, f"the validators would run over {[a.source.name for a in found]}"
    return found[0]


# --- the census, which is where a converter's silence becomes a number ------------------------ #


def a_census(derivation, committed: int | None = None, excluded: Mapping[str, int] | None = None):
    """The census the export produces, with one bucket at a time made wrong."""
    if committed is None:
        committed = derivation_tests.COMMITTED_NODES
    if excluded is None:
        excluded = {
            derivation_tests.EXPOSURE_CODE: derivation_tests.EXPOSURE_REFUSED_NODES,
            derivation_tests.SQUEEZE_CODE: derivation_tests.BB_SQUEEZE_REFUSED_NODES,
            derivation_tests.DEPTH_CODE: derivation_tests.BEYOND_DEPTH_NODES,
        }
    return derivation.NodeCensus(committed=committed, excluded=dict(excluded), inexpressible={})


def test_the_census_is_refused_when_it_does_not_cover_the_export(derivation, generator) -> None:
    """Every one of the 33,969 nodes lands in exactly one bucket, or the census is a subset
    dressed as a census. The vocabulary is checked first, everything below being built out of it:
    a census fed a reason the module does not carry would be refused for the wrong reason, and
    that refusal reads exactly like this test passing. Decision 52 closes it at three codes and
    decision 8 keeps it disjoint from the runtime miss codes, so a node the converter failed to
    handle cannot be filed as a property of the grammar.

    **Three codes rather than one, because each names a different way back.** The 348 refused for
    multiway exposure return when GTOpen can price a multiway pot; the 10 big-blind squeeze spots
    when the flats are repaired; the 33,362 beyond the committed raise depth when a later phase
    takes up the four-bet. A census folding any two together **balances exactly** and is wrong
    only about which fix brings which back, the one failure a total can never see.
    """
    assert set(lookup.DERIVATION_EXCLUSION_CODES) == {
        derivation_tests.EXPOSURE_CODE,
        derivation_tests.SQUEEZE_CODE,
        derivation_tests.DEPTH_CODE,
    }
    assert not set(lookup.DERIVATION_EXCLUSION_CODES) & set(lookup.MISS_CODES), (
        "a derivation reason and a runtime miss code share a name, so an excluded node can be"
        " filed as a lookup failure"
    )
    assert lookup.DERIVATION_NO_LEGAL_SPOT_KEY in lookup.DERIVATION_INEXPRESSIBILITY_CODES

    exported = derivation_tests.EXPORTED_NODES
    committed = derivation_tests.COMMITTED_NODES
    generator.validate_census(a_census(derivation), exported)

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_census(a_census(derivation), exported + 1)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_census(a_census(derivation, committed=committed - 1), exported)
    with pytest.raises(generator.DerivedChartReportError):
        unruled = {"derivation:gave-up": exported - committed}
        generator.validate_census(a_census(derivation, excluded=unruled), exported)
    with pytest.raises(generator.DerivedChartReportError):
        one_code = {derivation_tests.DEPTH_CODE: exported - committed}
        generator.validate_census(a_census(derivation, excluded=one_code), exported)
    with pytest.raises(generator.DerivedChartReportError):
        # The ten squeeze spots filed under exposure. They were refused by the third clause
        # precisely because the exposure clause admitted them, so this is the fold that also
        # tells a plausible story - and it still adds to 33,969.
        squeeze_folded = {
            derivation_tests.EXPOSURE_CODE: (
                derivation_tests.EXPOSURE_REFUSED_NODES
                + derivation_tests.BB_SQUEEZE_REFUSED_NODES
            ),
            derivation_tests.DEPTH_CODE: derivation_tests.BEYOND_DEPTH_NODES,
        }
        generator.validate_census(a_census(derivation, excluded=squeeze_folded), exported)
    with pytest.raises(generator.DerivedChartReportError):
        # And the multiway family filed under the raise-depth reason, which is the fold that
        # would let a build claim the four-bet phase brings everything back.
        depth_folded = {
            derivation_tests.SQUEEZE_CODE: derivation_tests.BB_SQUEEZE_REFUSED_NODES,
            derivation_tests.DEPTH_CODE: (
                derivation_tests.BEYOND_DEPTH_NODES + derivation_tests.EXPOSURE_REFUSED_NODES
            ),
        }
        generator.validate_census(a_census(derivation, excluded=depth_folded), exported)
    with pytest.raises(generator.DerivedChartReportError):
        invented = derivation.NodeCensus(
            committed, {}, {"derivation:not-ruled": exported - committed}
        )
        generator.validate_census(invented, exported)


def test_the_artifact_spot_count_is_checked_against_the_walk_key_by_key(generator) -> None:
    """249 nodes are not self-evidently 249 keys, and a total cannot tell the difference.

    A converter that dropped one node while inventing one key publishes the identical count, so
    the comparison runs key by key. The three count-preserving swaps below invent one key from
    each refusal family in turn - refused for multiway exposure, one of the ten big-blind squeeze
    spots, and one beyond the committed raise depth - so a converter missing any one clause fails
    here by the name of the clause it lost."""
    walked = {
        derivation_tests.SB_OPEN_KEY,
        derivation_tests.TRACED_KEY,
        derivation_tests.THREE_BET_FACED_KEY,
    }
    refused = (
        derivation_tests.NARROWEST_REFUSED_KEY,
        derivation_tests.BB_SQUEEZE_KEY,
        derivation_tests.FOUR_BET_FACED_KEY,
    )
    assert not walked & set(refused), "a key is being used as both committed and refused"
    generator.validate_spot_count(set(walked), set(walked))

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked - {derivation_tests.SB_OPEN_KEY}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked | {derivation_tests.LOJACK_OPEN_KEY}, walked)
    for invented in refused:
        swapped = (walked - {derivation_tests.SB_OPEN_KEY}) | {invented}
        assert len(swapped) == len(walked), invented
        with pytest.raises(generator.DerivedChartReportError):
            generator.validate_spot_count(swapped, walked)


# --- the four relations, counted rather than gated -------------------------------------------- #


def a_full_grid(value) -> dict[str, float]:
    """All 169 classes with `value(name)` in each. A partial grid silently drops the comparisons
    whose other half is missing and reports a clean measurement."""
    return {name: value(name) for name in HAND_CLASSES}


def monotone(name: str) -> float:
    """A frequency falling with the high card and with the kicker, a tenth of a point higher
    suited than offsuit - so all three play-not-fold relations hold with room to spare and any
    violation counted below is the one the case put there."""
    high, low = RANKS.index(name[0]), RANKS.index(name[1])
    return 100.0 - 3.0 * high - 0.2 * low + (0.1 if name.endswith("s") else 0.0)


def a_grid(**overrides: float) -> dict[str, dict[str, float]]:
    """One spot's grid, monotone before anything is overridden."""
    return {derivation_tests.SB_OPEN_KEY: a_full_grid(monotone) | overrides}


def test_the_per_cell_relations_are_counted_at_the_tolerance_decision_10_pinned(
    generator,
) -> None:
    """Four relations, measured per cell at a one-point tolerance, and none of them a gate.

    Decision 10 measures and gates nothing, because a generator that *refused* a violating grid
    would refuse the committed chart: the pair and kicker ladders both invert and decisions 41, 47
    and 51 accept all of it as solved. What has to be exactly right is the count, it being
    published for a human, and `DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS` says
    why the definition is pinned as data first. **The fourth relation is the point of the four**
    and the last case below is it: at a spot where every pair is played 100 percent there is
    nothing for play-not-fold to read, so the three relations stated over it count zero while the
    raise weight inverts by 60 points. It reads the merged weight, which is the action the bot
    takes (Taylor, 2026-09-03).

    The boundary cases are the tolerance itself: a gap of exactly a point is not a violation, a
    hundredth past it is, and a ladder drifting nine tenths a step counts nothing though the top
    pair ends ten points under the bottom one, only adjacent ranks being compared."""
    assert generator.MONOTONICITY_TOLERANCE_PCT == 1.0
    parameters = set(inspect.signature(generator.count_dominance_violations).parameters)
    assert parameters == {"play", "raise_weight"}, (
        "count_dominance_violations must take both grids the four relations are stated over -"
        f" play-not-fold and the merged raise weight - and takes {sorted(parameters)}"
    )
    flat = a_grid()

    def counted(play, raise_weight=None) -> dict[str, int]:
        found = generator.count_dominance_violations(
            play=play, raise_weight=flat if raise_weight is None else raise_weight
        )
        assert set(found) == set(RELATION_KEYS), sorted(found)
        return found

    assert set(counted(flat).values()) == {0}, "the monotone grid violates something"
    assert set(counted(a_grid(**{"44": 90.0, "33": 91.0})).values()) == {0}
    drift = a_grid(**{f"{rank}{rank}": 88.0 + 0.9 * index for index, rank in enumerate(RANKS)})
    assert set(counted(drift).values()) == {0}, "the ladder was compared past adjacent ranks"

    assert counted(a_grid(**{"44": 72.81, "33": 99.88}))["pair ladder"] == 1
    assert counted(a_grid(**{"44": 90.0, "33": 91.01}))["pair ladder"] == 1
    # `32s` and `32o` are the one twin pair in no row comparison at all - the deuce row has no
    # second kicker to compare against - so this counts the twins relation and nothing else.
    assert counted(a_grid(**{"32o": 70.0}))["suited over its offsuit twin"] == 1
    # One step of one row, both suit families, and the twins relation left holding.
    row = counted(a_grid(**{"42s": 70.0, "42o": 69.9}))
    assert row["row kicker ladder"] == 2 and row["suited over its offsuit twin"] == 0

    # Decision 50, as the two grids the generator is handed: every hand played, and the
    # raise-versus-call split inverted underneath.
    always_played = {derivation_tests.SB_OPEN_KEY: a_full_grid(lambda name: 100.0)}
    blind = counted(always_played, always_played)
    assert set(blind.values()) == {0}, "play-not-fold saw a spot where every hand is played"
    seen = counted(always_played, a_grid(**{"44": 20.0, "33": 80.0}))
    assert seen["pair ladder on the raise weight"] == 1, seen
    assert seen["pair ladder"] == 0, "the raise-weight inversion was counted on play-not-fold too"


# --- the two arms, which are the only thing here that gates ----------------------------------- #


def test_the_group_measure_is_refused_when_it_prefers_the_transposed_hand_index(
    generator,
) -> None:
    """The suit arm's validator, shown refusing before it is trusted to accept. What the arm
    asserts is the direction and never the counts: the solved hand index must flag strictly fewer
    spots than the index with every suited hand read off its offsuit twin. The
    second case retired the aggregate this replaced - over an earlier set it scored 2,007 solved
    against 818 transposed, preferring the *wrong* mapping, which rewards the defect it exists to
    catch. A tie refuses too, a measure that cannot tell the mappings apart catching nothing."""
    solved, transposed, *_ = report_tests.ARM_ROWS["the committed set"]
    generator.validate_group_discrimination(solved=solved, transposed=transposed)

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_group_discrimination(solved=2_007, transposed=818)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_group_discrimination(solved=transposed, transposed=solved)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_group_discrimination(solved=solved, transposed=solved)


def test_the_rank_permutation_is_refused_when_it_does_not_beat_the_solved_hand_index(
    generator,
) -> None:
    """The second arm's validator, and it is a second function rather than a second call.
    `validate_group_discrimination` takes `solved` and `transposed`; this one takes `solved` and
    `permuted`. Two names because this repo has already lost a day to two different "transposed"
    counterfactuals being confused, and passing a rank-permutation count into a parameter called
    `transposed` is that confusion written into the call site. The rule is asserted the same way,
    a tie refusing on each."""
    validate = published(generator, "validate_rank_discrimination")
    _, _, solved, permuted, *_ = report_tests.ARM_ROWS["the committed set"]

    validate(solved=solved, permuted=permuted)

    with pytest.raises(generator.DerivedChartReportError):
        validate(solved=permuted, permuted=solved)
    with pytest.raises(generator.DerivedChartReportError):
        validate(solved=solved, permuted=solved)


def kind_of(hand_class_text: str) -> int:
    """0 for a pair, 1 for suited, 2 for offsuit - the three families a rank map cannot mix."""
    return 0 if len(hand_class_text) == 2 else (1 if hand_class_text.endswith("s") else 2)


def test_the_two_counterfactuals_are_different_functions_and_neither_is_the_other(
    generator,
) -> None:
    """The trap this repo has already fallen into, closed by assertion rather than by comment.
    `transpose_hand_index` swaps each suited hand with its offsuit twin. `reverse_hand_ranks`
    reads each cell off the class with both ranks reversed - ace becomes deuce, eight maps to
    itself. They are different mappings and keep different names: a stage-4 reimplementation that
    substituted one for the other reproduced neither family's counts.

    Four properties pin the rank map. It covers the whole grid, so no cell is quietly dropped; it
    is its own inverse, so the counterfactual is well defined; it maps pairs to pairs, suited to
    suited and offsuit to offsuit - **which is exactly why the suit swap cannot see it** - and it
    is not the identity, which a mapping that failed to find its classes would be.
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

    swapped = generator.transpose_hand_index(ranked)
    assert swapped != permuted
    assert swapped["AKs"] == ranked["AKo"] and swapped["AKo"] == ranked["AKs"]
    assert swapped["AA"] == ranked["AA"], "the suit swap moved a pair"

    # And what the arm does where the reversal is not total. A sparse grid maps onto the image of
    # the classes it holds, never onto whatever survived: the cell whose partner is gone is absent
    # rather than carrying a neighbour's value, and the comparisons it would have entered are
    # skipped. `72o` reverses to `A9o`, so dropping it drops `A9o` from the permuted grid - the
    # two sides lose different classes, which is why each publishes its own skipped count.
    skipped = published(generator, "row_comparisons_skipped")
    sparse = {name: ranked[name] for name in HAND_CLASSES if name != "72o"}
    assert set(reverse(sparse)) == set(HAND_CLASSES) - {"A9o"}
    assert reverse(sparse) == {n: v for n, v in permuted.items() if n != "A9o"}
    assert skipped(ranked) == 0 and skipped(sparse) > 0
    assert skipped(reverse(sparse)) == skipped({n: 0.0 for n in HAND_CLASSES if n != "A9o"})


def test_both_arms_discriminate_on_every_partition_of_the_committed_set(
    generator, artifact
) -> None:
    """The gate, run over the real chart on all ten partitions, through the validators that ship.

    The refusal tests above prove each validator says no to a bad pair of numbers, not that the
    numbers it will be handed are good ones, and the contract states the gate **on every
    partition**. A measure can separate over the whole chart and still be blind where it matters:
    a converter reading the payload by the grid ordering only where hero faces a raise breaks the
    deep spots, leaves the shallow ones right, and an aggregate absorbs it.

    **The rank arm scores every spot and publishes what it had to skip**, on each side, the two
    sides skipping different comparisons. No partition falls below the five-spot floor. The counts
    are re-derived through the shipped functions rather than carried over, so a measure that
    quietly stops comparing goes red on a number instead of passing on a vacuous direction."""
    reverse = published(generator, "reverse_hand_ranks")
    skipped = published(generator, "row_comparisons_skipped")
    rows = published(generator, "cells_violating_rows")
    validate_rank = published(generator, "validate_rank_discrimination")
    grid = generator.play_grid(artifact)
    walked = report_tests.partitions(artifact)
    expected = report_tests.ARM_ROWS

    assert len(artifact.spots) == derivation_tests.COMMITTED_NODES
    assert set(walked) == set(expected), sorted(set(walked) ^ set(expected))
    assert len(walked) == 10, f"the committed set no longer splits into ten: {sorted(walked)}"
    assert set(grid) == {spot.spot_id for spot in artifact.spots}

    for label, keys in walked.items():
        part = {key: grid[key] for key in keys}
        solved = generator.spots_violating_twins(part)
        transposed = generator.spots_violating_twins(
            {key: generator.transpose_hand_index(cells) for key, cells in part.items()}
        )
        reversed_part = {key: reverse(cells) for key, cells in part.items()}
        rank_solved = rows(part)
        permuted = rows(reversed_part)
        ladder = report_tests.ROW_LADDER_COMPARISONS
        scored = sum(1 for cells in part.values() if skipped(cells) < ladder)

        measured = (
            solved,
            transposed,
            rank_solved,
            permuted,
            scored,
            sum(skipped(cells) for cells in part.values()),
            sum(skipped(cells) for cells in reversed_part.values()),
        )
        assert measured == expected[label], (label, measured, expected[label])
        assert solved < transposed, ("suit swap", label, solved, transposed)
        generator.validate_group_discrimination(solved=solved, transposed=transposed)
        if scored < report_tests.RANK_ARM_SPOT_FLOOR:
            continue
        assert rank_solved < permuted, ("rank reversal", label, rank_solved, permuted)
        validate_rank(solved=rank_solved, permuted=permuted)


def test_the_rank_arm_catches_the_reversed_chart_the_suit_swap_cannot_tell_apart(
    generator, artifact
) -> None:
    """The hole a stage-4 review found, and the proof that the second arm closes it.

    A chart with every hand rank reversed is a chart that opens 32o and folds aces. It is the
    shape a converter produces if it reads GTOpen's rank axis the wrong way up, and the suit arm
    cannot see it: pairs map to pairs and suited twins to suited twins, so the twins relation is
    permuted among its own comparisons and scores the reversed chart **bit for bit** as the real
    one. That is asserted here over the whole committed chart, and the suit arm's validator is
    then shown accepting the reversed chart. The rank arm's reading swaps instead, and it swaps
    exactly: the reversal is its own inverse on a sparse grid as well as a full one, so the solved
    and permuted counts trade places. Both directions matter - an arm that refused everything
    would also refuse the reversed chart, so the real chart goes through first and must pass.
    """
    reverse = published(generator, "reverse_hand_ranks")
    rows = published(generator, "cells_violating_rows")
    validate_rank = published(generator, "validate_rank_discrimination")
    grid = generator.play_grid(artifact)
    reversed_chart = {key: reverse(cells) for key, cells in grid.items()}

    def suit_arm(chart) -> tuple[int, int]:
        swapped = {key: generator.transpose_hand_index(cells) for key, cells in chart.items()}
        return generator.spots_violating_twins(chart), generator.spots_violating_twins(swapped)

    assert len(grid) == derivation_tests.COMMITTED_NODES
    assert reversed_chart != grid, "the reversed chart is the same chart, so nothing is proved"

    blind = suit_arm(reversed_chart)
    assert blind == suit_arm(grid), (
        "the suit arm now reads the rank-reversed chart differently from the real one, so the"
        " measurement the second arm was added for no longer holds and the pair needs re-deriving"
    )
    # It reads them identically, so its verdict on the reversed chart is its verdict on the real
    # one: it accepts a chart that opens 32o and folds aces.
    generator.validate_group_discrimination(solved=blind[0], transposed=blind[1])

    solved, permuted = rows(grid), rows(reversed_chart)
    assert solved < permuted, (solved, permuted)
    validate_rank(solved=solved, permuted=permuted)
    assert rows({key: reverse(cells) for key, cells in reversed_chart.items()}) == solved, (
        "the reversal is not its own inverse over the committed chart"
    )
    with pytest.raises(generator.DerivedChartReportError):
        validate_rank(solved=permuted, permuted=solved)


# --- the cutover comparison, the vacuous labels, and the command itself ------------------------ #


def test_the_old_versus_new_disagreement_count_is_refused_when_it_cannot_be_read(
    generator,
) -> None:
    """A comparison that did not happen arrives as a small consistent number, not as an error.
    Every case below is one shape: a validator that checks only a count's arithmetic cannot tell a
    real zero from an input that quietly became trivial - an empty overlap, a pin that no longer
    resolves, a retired chart read as zero spots, or a comparison handed the derived chart twice
    (`corpus-self-play-crossref-empties-silently` is the same failure elsewhere). A zero
    disagreement over a non-empty overlap is refused rather than argued about, and the measured
    reason it cannot be true is on the ledger: the retired chart's 36 sizing entries are every one
    priced at a jam, where the derived chart offers 2.5, 7.5 and 22.5 and no jam at all."""
    ways = {"derived continues, retired folds": 140, "retired continues, derived folds": 40}
    generator.validate_disagreement(shared_decisions=1200, disagreements=180, by_direction=ways)

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(shared_decisions=0, disagreements=0, by_direction={})
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(shared_decisions=1200, disagreements=0, by_direction={})
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(
            shared_decisions=1200, disagreements=181, by_direction=ways
        )
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_disagreement(shared_decisions=100, disagreements=180, by_direction=ways)


def test_the_three_vacuous_criteria_are_labelled_and_heros_jam_is_shown_where_it_lives(
    report_text, artifact
) -> None:
    """Three criteria have no instance over the 249, and a criterion that cannot fail did not
    pass. Each is kept because a later solve reactivates it: the two-price sizing schema, proved
    against a synthetic export under decision 6; the no-raise half of the sizing invariant, no
    committed spot offering zero raises; and the jam-and-named-raise collapse rule, which under
    `add_allin: false` never fires. Wherever one is reported it carries the label, a packet
    counting one as a check that passed claiming coverage the phase does not have.

    Hero's own jam is the same argument from the other side. It lives only at the four-bet-facing
    spots this phase withholds, so the jam-inversion canary that rejected the first cutover is
    retained against the **export**, the report prints AA's jam weight there, and the spot it
    names has to be one the chart does not answer."""
    vacuous = report_tests.section(report_text, "vacuous")
    rows = re.findall(r"^\s*vacuous\s+(\S.*?)\s*$", vacuous, re.MULTILINE)
    assert len(rows) == 3, f"the report labels {len(rows)} vacuous criteria rather than three"
    for token in ("two-price", "no-raise", "jam-and-named-raise"):
        assert sum(1 for row in rows if token in row) == 1, (token, rows)
    assert re.search(r"not a check that passed|never counted|does not pass", vacuous), (
        "the three are labelled without the report saying a vacuous criterion is not a pass"
    )

    jams = report_tests.section(report_text, "jams")
    row = re.search(r"^\s*(t6/\S+)\s+AA jams\s+(\d+\.\d+)\s*$", jams, re.MULTILINE)
    assert row is not None, f"no AA jam weight is printed at a withheld spot: {jams!r}"
    key, weight = row.group(1), float(row.group(2))
    assert report_tests.raises_faced(key) > derivation_tests.COMMITTED_RAISE_DEPTH, (
        f"{key} is within the committed raise depth, so it is not one of the withheld spots"
    )
    assert key not in {spot.spot_id for spot in artifact.spots}, f"{key} is committed"
    assert 0.0 <= weight <= 100.0, weight

    limitations = report_tests.section(report_text, "limitations")
    for entry in (
        "CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE",
        "PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED",
        "PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS",
        "MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED",
    ):
        assert entry in limitations, f"the source card's limitations do not state {entry}"


def run_report(tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    # Asserted, or a missing script would make every refusal below pass with no validator run.
    assert SCRIPT.exists(), f"{SCRIPT} does not exist, so nothing here runs a validator"
    command = [sys.executable, str(SCRIPT), "--output", str(tmp_path / "report.txt"), *arguments]
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)


def test_the_command_publishes_a_report_when_every_validator_holds(tmp_path) -> None:
    """The positive control, without which every refusal in this file is satisfied by a script
    that refuses everything. Four assertions below read `returncode != 0`, and argparse exits 2 on
    an unknown flag, so a generator shipped without `--retired-commit` or `--artifact` would pass
    all four while refusing good input too, and the packet would record that the command rejects a
    bad pin when in fact it rejects every pin. This is the one assertion that says it works."""
    result = run_report(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "report.txt").exists(), "the command exited 0 and published nothing"


def test_the_gate_command_runs_this_script() -> None:
    """A validator the gate does not run is a validator nothing runs."""
    assert report_tests.COMMAND_ID in COMMANDS
    registered = COMMANDS[report_tests.COMMAND_ID].command
    assert any(str(SCRIPT.relative_to(REPO_ROOT)) in part for part in registered)


@pytest.mark.parametrize("pin", ["nonexistent", "root"])
def test_a_pin_the_retired_chart_cannot_be_read_at_fails_the_command(tmp_path, pin) -> None:
    """The retired chart is read out of git history, so the pin is an input like any other, and
    the two bad pins fail differently: one is not a commit at all, the other a real commit at
    which the retired chart does not exist, which a resolvable-looking sha sails past. Keeping a
    copy in a subdirectory the importer's glob misses was rejected for this: it works, and it
    makes a reader ask which chart plays."""
    assert Path(RETIRED_CHART).name == Path(report_tests.RETIRED_SIZINGS).name, (
        "the retired chart and its sizing table are pinned at two different files"
    )
    commit = "0" * 40
    if pin == "root":
        commit = report_tests.git("rev-list", "--max-parents=0", "HEAD").stdout.split()[-1]
        assert report_tests.git("cat-file", "-e", f"{commit}:{RETIRED_CHART}").returncode != 0

    result = run_report(tmp_path, "--retired-commit", commit)

    assert result.returncode != 0, result.stdout + result.stderr
    assert not (tmp_path / "report.txt").exists(), "a refused report must not also be published"


def corrupted_artifact(tmp_path: Path, how: str) -> Path:
    """A committed artifact that loads cleanly and is wrong, which is the case that matters."""
    paths = sorted(report_tests.ARTIFACT_DIR.glob("*.json"))
    assert len(paths) == 1, f"expected exactly one committed preflop artifact, found {paths}"
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    source = payload["spots"][0]["spot_id"]
    if how == "drop-a-spot":
        payload["spots"] = [spot for spot in payload["spots"] if spot["spot_id"] != source]
        # Every per-spot map loses the spot too, or the importer refuses the file for its own
        # reason and no validator here is reached. The forms differ because the density rules do:
        # the first two owe an entry per declared spot, `arrival_ppb` only a subset in spot order.
        del payload["action_weights"][source]
        del payload["arriving_reach_bp"][source]
        payload["arrival_ppb"].pop(source, None)
    else:
        # The narrowest spot the exposure filter refuses, at 10.0234 percent against the ruled
        # ten. Its cells are copied off a committed spot, so the file stays internally consistent
        # and only a comparison against the walk can see it.
        invented = derivation_tests.NARROWEST_REFUSED_KEY
        assert invented not in payload["action_weights"], f"{invented} is already committed"
        payload["spots"].append(
            {
                "spot_id": invented,
                "hero_position": invented.split("/")[2],
                "action_sequence": [
                    {"position": entry.position, "action": entry.action}
                    | ({} if entry.size_bb is None else {"size_bb": entry.size_bb})
                    for entry in derivation_tests.NARROWEST_REFUSED_SEQUENCE
                ],
            }
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
    # If the schema rejected it the command would exit non-zero for the loader's reason.
    import_preflop_artifact(path)
    return path


@pytest.mark.parametrize("how", ["drop-a-spot", "commit-a-spot-above-the-exposure-threshold"])
def test_a_wrong_artifact_fails_the_command_rather_than_being_rendered(tmp_path, how) -> None:
    """Both artifacts below load cleanly and are wrong, and neither may be rendered. One holds a
    spot fewer than the walk selected and says so in its own audit fields, so only a comparison
    against the export sees it. The other holds one more: the narrowest spot the exposure filter
    refuses, which is what a converter produces with the ruled ten nudged into the gap between
    that spot at 10.0234 and the next refused one at 10.1189 - five hundredths, the canary's own
    figure, where the two hundredths this once said would admit nothing. Nothing but the walk
    notices: the cell converts, imports and answers, and it is the second of the phase's two
    canaries, authored before what it aims at."""
    result = run_report(tmp_path, "--artifact", str(corrupted_artifact(tmp_path, how)))

    assert result.returncode != 0, result.stdout + result.stderr
    assert not (tmp_path / "report.txt").exists()
