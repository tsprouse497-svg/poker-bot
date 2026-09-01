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

**Re-cut at stage 4 on 2026-09-01.** The census validator now takes **three** exclusion codes,
because decision 20 added the reason a four-bet pot is refused for, and a validator accepting
fewer accepts a vocabulary that cannot say which nodes come back by which route. And the
discrimination gate is exercised over the real committed artifact on every partition, not only
against hand-made inputs: the contract's amendment of that day states the gate per partition,
and a validator that only ever refuses a fabricated pair has never been shown reading a chart.
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
    MULTIWAY_NODES,
    OUTSIDE_RULE_NODES,
    RETIRED_CHART,
    discrimination_partitions,
    git,
)

from poker_training_bot.solver_artifacts import lookup
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
            FOUR_BET_POT_CODE: FOUR_BET_POT_NODES,
        }
    return derivation.NodeCensus(
        committed=committed, excluded=dict(excluded), inexpressible={}
    )


def test_the_census_is_refused_when_it_does_not_cover_the_export(derivation, generator) -> None:
    """Every node lands in exactly one bucket, or the census is a subset dressed as a census.

    The wrong inputs are the honest ones: counts that sum to one node fewer than the export
    holds, and a reason nobody ruled. Decision 8 closes both vocabularies so a node the converter
    merely failed to handle cannot be filed as a property of the grammar, and decision 20 makes
    that **three** exclusion codes - a census filing all 33,933 excluded nodes under one reason
    cannot say which come back when GTOpen prices multiway and which when the realization fit
    gains a four-bet-pot cell, so a two-code census is refused here as well as a one-code one.
    """
    # The vocabulary first, because everything below is built out of it: a census fed a reason
    # the module does not carry is refused for the wrong reason, and the refusal would read as
    # this test passing while the ruled three-reason census was the thing being rejected.
    assert set(lookup.DERIVATION_EXCLUSION_CODES) == {
        lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY,
        lookup.DERIVATION_OUTSIDE_SELECTION_RULE,
        FOUR_BET_POT_CODE,
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
        # fifteen four-bet-pot nodes folded into one of them rather than named.
        two_codes = a_census(
            derivation,
            excluded={
                lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: MULTIWAY_NODES,
                lookup.DERIVATION_OUTSIDE_SELECTION_RULE: (
                    OUTSIDE_RULE_NODES + FOUR_BET_POT_NODES
                ),
            },
        )
        generator.validate_census(two_codes, EXPORTED_NODES)
    with pytest.raises(generator.DerivedChartReportError):
        invented = derivation.NodeCensus(
            COMMITTED_SPOTS, {}, {"derivation:not-ruled": EXPORTED_NODES - COMMITTED_SPOTS}
        )
        generator.validate_census(invented, EXPORTED_NODES)


def test_the_artifact_spot_count_is_checked_against_the_walk_key_by_key(generator) -> None:
    """A count that matches while the keys do not is the failure this has to catch: a converter
    that dropped one node and invented one key gives the same count. The last case is that, and
    the key it invents is the lojack's open - one of the 24 the predicate drops, so a converter
    built on the superseded rule fails here by name.
    """
    walked = {"t6/d100/SB/rfi", "t6/d100/BB/BTN:raise@2.5", "t6/d100/BB/SB:raise@2.5"}
    generator.validate_spot_count(set(walked), set(walked))

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked - {"t6/d100/SB/rfi"}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked | {"t6/d100/LJ/rfi"}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count((walked - {"t6/d100/SB/rfi"}) | {"t6/d100/LJ/rfi"}, walked)


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


def test_the_group_measure_discriminates_on_every_partition_of_the_committed_set(
    generator,
) -> None:
    """The gate run over the real chart, on each partition, through the validator that ships.

    The refusal test above proves the validator says no to a bad pair of numbers. It cannot show
    the numbers it will actually be handed are good ones, and the contract's 2026-09-01
    amendment states the gate **on every partition** rather than over the committed set as a
    whole. So the shipped measure is run here against the committed artifact and every partition
    is put through `validate_group_discrimination` - the same function the report calls, not a
    second copy of the rule, because two copies of a rule agreeing tells you nothing.

    **What the partitions are for.** A measure can discriminate over the whole chart and still
    be blind on the part of it that matters: a converter reading the payload by the grid
    ordering only where hero faces a raise breaks the deep spots and leaves the shallow ones
    right, and an aggregate over 36 spots absorbs that. Splitting by hero's seat catches a
    mis-assigned actor the same way.

    Measured over the real committed 36 on 2026-09-01: 0 flagged under the solver's own class
    ordering against 26 under the transposed one over the whole set, and 0 against between 1 and
    15 on every seat and raise-count split. Every partition passed and none tied. The counts are
    recorded here rather than asserted, because the ruling is the direction: fixing a count
    fixes a partition, and picking the partition that reads smallest is picking a number to go
    green. A solved arm of 0 is the measure passing rather than the measure being blind - the
    transposed arm flags 26, so it tells the two mappings apart.
    """
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]
    grid = generator.play_grid(artifact)
    by_label: dict[str, tuple[str, ...]] = {"the committed set": tuple(grid)}
    for spot in artifact.spots:
        faced = sum(1 for entry in spot.action_sequence if entry.action == "raise")
        for label in (f"hero={spot.hero_position}", f"raises faced {faced}"):
            by_label[label] = (*by_label.get(label, ()), spot.spot_id)

    assert len(artifact.spots) == COMMITTED_SPOTS
    assert set(by_label) == discrimination_partitions(artifact)
    for label, keys in by_label.items():
        solved = generator.spots_violating_twins({key: grid[key] for key in keys})
        transposed = generator.spots_violating_twins(
            {key: generator.transpose_hand_index(grid[key]) for key in keys}
        )
        assert solved < transposed, (label, solved, transposed)
        # Through the validator as well as beside it: a partition this test calls good and the
        # gate calls bad is a gate nobody is testing. Asserted first so a partition that fails
        # fails as an assertion rather than as the validator's own exception.
        generator.validate_group_discrimination(solved=solved, transposed=transposed)


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
