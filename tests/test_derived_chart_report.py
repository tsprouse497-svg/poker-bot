"""Phase 14: the report a non-coding reviewer reads, and the closing corpus measurement.

Split from the derivation tests because these check a different kind of claim: the chart
being right and a reviewer being led to the right conclusion about it are separate things.

A report renders whatever it is handed: a census that does not add up, or a spot count that
disagrees with the walk that produced it, exits 0 and publishes just as happily as the right
number would. The contract requires the generator to validate exactly four figures and to
exit non-zero when they do not hold, and this repo has twice shipped a validator that could
not fail. So each is fed a deliberately wrong input and made to refuse.

Decision 9 fixed the closing prediction's band before any of it was measured, so the report
is checked against the decision record rather than allowed to restate its own prediction.

The headings in `HEADINGS` and the row shapes the parsers require are part of the spec.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple

import pytest

from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.importer import (
    import_preflop_artifact,
    import_preflop_artifacts,
)
from poker_training_bot.solver_artifacts.schema import weights_checksum
from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_verify import COMMANDS  # noqa: E402

COMMAND_ID = "generate_derived_chart_report"
SCRIPT = REPO_ROOT / "scripts" / f"{COMMAND_ID}.py"
ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
EXPECTATIONS = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"
RETIRED_CHART = "data/artifacts/preflop/six_max_nl25_100bb.json"
DECISIONS = (
    REPO_ROOT / "reports" / "phase_audits" / "decisions" / "PHASE_14_CHART_CUTOVER_DECISIONS.md"
)

# The report's own headings. Exactly one of each, and the body under it is where the claim
# that heading names has to be made.
HEADINGS = {
    "census": "## The three-way node census",
    "trace": "## One converted cell, traced",
    "dominance": "## The two dominance relations",
    "orderings": "## The two orderings",
    "expectations": "## The derived chart against the GTO Wizard expectations",
    "corpus": "## The corpus, before and after",
    "prediction": "## The pre-registered prediction",
    "price": "## The price the corpus was played at",
    "explanations": "## What this measurement can and cannot separate",
    "bounds": "## What this chart does not answer",
    "refusals": "## The refusal inventory, by reason",
    "old_versus_new": "## Where the retired chart and the derived chart disagree",
    "recomputable": "## One number a reader can recompute by hand",
}

RANKS = "AKQJT98765432"
OPENERS = {"lojack": "LJ", "hijack": "HJ", "cutoff": "CO", "small blind": "SB", "button": "BTN"}
POPULATIONS = ("Pluribus", "humans")
REFUSAL_ROW = r"^\s*(lookup:[a-z-]+)\s+(\d+)\s+(\d+)\s*$"
RATE_ROW = r"\s*([a-z][a-z -]*?),\s*(before|after)\s+(\d+) of (\d+) [a-z ]+\((\d+\.\d)%\)\s*$"
SIGNED = re.compile(r"[+-]\d+(?:\.\d+)?")
BAND = re.compile(
    r"([+-]?\d+\.\d+)\s+to\s+([+-]?\d+\.\d+)\s+(?:points\s+)?"
    r"against the (lojack|hijack|cutoff|small blind|button)"
)


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


@pytest.fixture(scope="module")
def report_text(generator) -> str:
    output = generator.REPORT_OUTPUT
    assert output.exists(), f"{output} is missing, so `{COMMAND_ID}` has not run"
    return output.read_text(encoding="utf-8")


def section(text: str, key: str) -> str:
    """The body under one of the report's headings, so a claim is read where it is made."""
    marker = f"\n{HEADINGS[key]}\n"
    assert text.count(marker) == 1, f"the report needs exactly one {HEADINGS[key]!r} section"
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def decision_bands() -> dict[str, tuple[float, float]]:
    """Decision 9's per-opener band, parsed out of the record that pre-registered it rather
    than copied here: decision 2 re-solves, so the deltas it is a multiple of move with it.
    """
    body = DECISIONS.read_text(encoding="utf-8").split("\n## 9. ", 1)[1].split("\n## ", 1)[0]
    ruling = " ".join(body.split("**Ruled by Taylor", 1)[1].split())
    bands: dict[str, tuple[float, float]] = {}
    read_to = 0
    for match in BAND.finditer(ruling):
        # The button's is a predicted worsening, written as a magnitude under the word "worsen"
        # rather than with a minus sign on each end.
        sign = -1.0 if "worsen" in ruling[read_to : match.start()] else 1.0
        read_to = match.end()
        low, high = sorted(sign * abs(float(match.group(index))) for index in (1, 2))
        bands[OPENERS[match.group(3)]] = (low, high)
    assert len(bands) == 5, "decision 9 no longer bands all five openers, so this checks nothing"
    return bands


class PredictionRow(NamedTuple):
    delta: float
    band: tuple[float, float]
    measured: float
    verdict: str


def prediction_rows(body: str) -> dict[str, PredictionRow]:
    """One row per opener: the defence delta, the band's two ends, the measured move, and a
    verdict, signed and in that order. Inside, above and below are on that same signed scale.
    """
    rows: dict[str, PredictionRow] = {}
    for line in body.splitlines():
        match = re.match(r"\s*(LJ|HJ|CO|SB|BTN)\b(.*)$", line)
        if match is None:
            continue
        numbers = [float(value) for value in SIGNED.findall(match.group(2))]
        verdict = re.search(r"\b(inside|above|below)\b", match.group(2))
        assert len(numbers) >= 4 and verdict is not None, (
            f"the prediction row for {match.group(1)} must carry the opener's defence delta, both"
            " ends of its band and the measured move, every one signed, then one of"
            f" inside/above/below: {line!r}"
        )
        rows[match.group(1)] = PredictionRow(
            numbers[0], (min(numbers[1:3]), max(numbers[1:3])), numbers[3], verdict.group(1)
        )
    return rows


def inventory_rows(body: str) -> list[tuple[int, str]]:
    """The republished inventory: decision points, and the spot key they reached."""
    found = re.findall(r"^\s*(\d+)\s+(t6/\S+)", body, re.MULTILINE)
    return [(int(points), key) for points, key in found]


def first_action_is_a_call(spot_key: str) -> bool:
    """Decision 12's definition, applied here rather than trusted from the report."""
    parts = spot_key.split("/")
    return len(parts) > 3 and parts[3].split(",")[0].endswith(":call")


class RateRow(NamedTuple):
    population: str
    label: str
    when: str
    numerator: int
    denominator: int
    percent: float


def rate_rows(body: str) -> list[RateRow]:
    """Every published rate, with the population block it sits in. A row with no owning
    population is a pooled row, and Pluribus and the human professionals are different
    players, so it is an error here rather than something this parser guesses at.
    """
    rows: list[RateRow] = []
    population: str | None = None
    for line in body.splitlines():
        if line.strip() in POPULATIONS:
            population = line.strip()
            continue
        match = re.match(RATE_ROW, line)
        if match is None:
            continue
        assert population is not None, f"a rate published outside any population block: {line!r}"
        label, when, agreed, over, percent = match.groups()
        rows.append(RateRow(population, label, when, int(agreed), int(over), float(percent)))
    return rows


def refusals_after(body: str) -> dict[str, int]:
    return {code: int(after) for code, _, after in re.findall(REFUSAL_ROW, body, re.MULTILINE)}


def reported_refusals(text: str) -> list[RateRow]:
    rows = rate_rows(section(text, "corpus"))
    return [row for row in rows if row.label == "refused" and row.when == "after"]


def a_census(derivation, committed: int = 5626, excluded: Mapping[str, int] | None = None):
    if excluded is None:
        excluded = {lookup.DERIVATION_BELOW_REACH_FLOOR: 33202}
    return derivation.NodeCensus(
        committed=committed, excluded=dict(excluded), inexpressible={}
    )


def test_the_census_is_refused_when_it_does_not_cover_the_export(derivation, generator) -> None:
    """Every node lands in exactly one bucket, or the census is a subset dressed as a census.

    The wrong inputs are the honest ones: counts that sum to one node fewer than the export
    holds, and a reason nobody ruled. Decision 8 closes both vocabularies so a node the
    converter merely failed to handle cannot be filed as a property of the grammar.
    """
    generator.validate_census(a_census(derivation), 38828)

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_census(a_census(derivation), 38829)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_census(a_census(derivation, committed=5625), 38828)
    with pytest.raises(generator.DerivedChartReportError):
        wrong = a_census(derivation, excluded={"derivation:gave-up": 33202})
        generator.validate_census(wrong, 38828)
    with pytest.raises(generator.DerivedChartReportError):
        invented = derivation.NodeCensus(5626, {}, {"derivation:not-ruled": 33202})
        generator.validate_census(invented, 38828)

    assert lookup.DERIVATION_BELOW_REACH_FLOOR in lookup.DERIVATION_EXCLUSION_CODES
    assert lookup.DERIVATION_NO_LEGAL_SPOT_KEY in lookup.DERIVATION_INEXPRESSIBILITY_CODES


def test_the_artifact_spot_count_is_checked_against_the_walk_key_by_key(generator) -> None:
    """A count that matches while the keys do not is the failure this has to catch: a converter
    that dropped one node and invented one key gives the same count. The last case is that.
    """
    walked = {"t6/d100/LJ/rfi", "t6/d100/BTN/rfi", "t6/d100/BB/BTN:raise@2.5"}
    generator.validate_spot_count(set(walked), set(walked))

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked - {"t6/d100/LJ/rfi"}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count(walked | {"t6/d100/SB/rfi"}, walked)
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_spot_count((walked - {"t6/d100/LJ/rfi"}) | {"t6/d100/SB/rfi"}, walked)


def a_grid(**overrides: float) -> dict[str, dict[str, float]]:
    """One spot's play frequency per hand class, monotone before anything is overridden."""
    cells = {f"{rank}{rank}": 100.0 - index for index, rank in enumerate(RANKS)}
    for high, low in (("A", "K"), ("K", "Q"), ("7", "6")):
        cells[f"{high}{low}s"] = 80.0
        cells[f"{high}{low}o"] = 60.0
    cells.update(overrides)
    return {"t6/d100/LJ/rfi": cells}


def test_the_dominance_relations_are_refused_at_the_tolerance_decision_10_ruled(generator) -> None:
    """The measured violation put back in as a wrong input, and the ruling that scopes it.

    The lojack opening 44 at 72.81 percent under 33 at 99.88 is a cell the solver had not
    finished. But a gap of exactly a point is not a violation - 44 at 99.91 under 33 at 99.99
    is not a mistake - and a ladder drifting nine tenths a step passes though the top pair
    ends ten points under the bottom one, because the ruling compares adjacent ranks only.
    """
    assert generator.MONOTONICITY_TOLERANCE_PCT == 1.0
    generator.validate_dominance(a_grid())
    generator.validate_dominance(a_grid(**{"44": 90.0, "33": 91.0}))
    generator.validate_dominance(a_grid(**{f"{r}{r}": 88.0 + 0.9 * i for i, r in enumerate(RANKS)}))

    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_dominance(a_grid(**{"44": 72.81, "33": 99.88}))
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_dominance(a_grid(**{"44": 90.0, "33": 91.01}))
    with pytest.raises(generator.DerivedChartReportError):
        generator.validate_dominance(a_grid(AKs=50.0, AKo=80.0))


def test_the_old_versus_new_disagreement_count_is_refused_when_it_cannot_be_read(generator) -> None:
    """A comparison that did not happen arrives as a small consistent number, not as an error.

    Every case below is one shape: a validator that only checks a count's arithmetic cannot
    tell a real zero from an input that quietly became trivial - an empty overlap, a pin that
    no longer resolves, a retired chart read as zero spots, or a comparison handed the derived
    chart twice. The poker rules the last one out on its own, because the two charts share no
    three-bet price and no small-blind opening price: the retired one prices them at 8, 11,
    13.5 and 3.5 against the derived chart's 7.5 and 2.5, and the derived chart holds only
    four prices in all, so they cannot agree on a thousand shared corpus decisions.
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


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True)


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
        del payload["action_weights"][dropped]
        payload["audit_fields"]["spot_count"] = len(payload["spots"])
    else:
        spot = "t6/d100/LJ/rfi"
        assert spot in payload["action_weights"], f"{spot} is not in the committed artifact"
        payload["action_weights"][spot]["44"] = {"fold": 0.9, "raise": 0.1}
        payload["action_weights"][spot]["33"] = {"raise": 1.0}
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


@pytest.mark.parametrize("how", ["drop-a-spot", "invert-the-pair-ladder"])
def test_a_wrong_artifact_fails_the_command_rather_than_being_rendered(tmp_path, how) -> None:
    """Both artifacts below load cleanly and are wrong, which is the case that matters. One
    holds a spot fewer than the walk selected and says so in its own audit fields, so only a
    comparison against the export sees it. The other opens 44 a tenth of the time under 33.
    """
    result = run_report(tmp_path, "--artifact", str(corrupted_artifact(tmp_path, how)))

    assert result.returncode != 0, result.stdout + result.stderr
    assert not (tmp_path / "report.txt").exists()


def test_the_report_states_the_band_the_decision_record_pre_registered(report_text) -> None:
    """The band is read off decision 9's record, not restated by the agent that measured it.

    A directional prediction was rejected: defence widens against four openers and comes back
    2.67 points tighter against the button, which generates the most big-blind defending
    decisions in any six-max sample, so an aggregate "defence widens" is falsified in advance
    on its largest component. And five points of extra defence is 60 combos of 1,326 against a
    39-point call-agreement gap, so any nonzero movement confirms a sign-only prediction.
    """
    body = section(report_text, "prediction")
    rows = prediction_rows(body)
    bands = decision_bands()

    assert set(rows) == set(bands)
    for position, row in rows.items():
        assert row.band == bands[position], (
            f"the report predicts {row.band} against the {position} where the decision record"
            f" pre-registered {bands[position]}"
        )
    assert "PHASE_14_CHART_CUTOVER_DECISIONS.md" in body


def test_the_band_is_a_quarter_to_one_of_the_delta_and_the_miss_is_named(report_text) -> None:
    """Decision 9's rule and its verdict, both recomputed from the report's own columns. The
    record's numbers came off the 300-iteration export and the re-solve moves them, so the
    rule is checked rather than the figures. A miss either way is a result, so the side is
    named rather than the band merely printed.
    """
    rows = prediction_rows(section(report_text, "prediction"))

    assert rows
    for position, row in rows.items():
        low, high = sorted((row.delta * 0.25, row.delta))
        assert row.band[0] == pytest.approx(low, abs=0.011), position
        assert row.band[1] == pytest.approx(high, abs=0.011), position
        if row.measured < row.band[0] - 0.005:
            expected = "below"
        elif row.measured > row.band[1] + 0.005:
            expected = "above"
        else:
            expected = "inside"
        assert row.verdict == expected, (
            f"{position} moved {row.measured} against a band of {row.band} and the report calls"
            f" that {row.verdict}"
        )


def test_the_prediction_covers_price_and_says_which_way(report_text) -> None:
    """The cutover reprices hero's own small-blind open from 3.5bb to 2.5bb, so the big blind
    facing a small-blind open moves from a 3.5-solved answer to a 2.5-solved one against a
    corpus median of 2.25, and "the price-tracking part will not move" is false for it.
    """
    body = section(report_text, "price")
    lines = body.splitlines()
    repriced = [x for x in lines if "small blind" in x.lower() and "3.5" in x and "2.5" in x]

    assert repriced, "the report does not say hero's small-blind open moved from 3.5bb to 2.5bb"
    assert re.search(r"t6/d\d+/BB/SB:raise@2\.5", body), (
        "the report does not name the spot family the repricing lands on"
    )
    median = r"median[^\n]*\b2\.25\b|\b2\.25\b[^\n]*median"
    assert re.search(median, body, re.IGNORECASE), (
        "the corpus median opening price is not published beside the word median"
    )


def test_all_three_candidate_explanations_are_named_with_what_this_controls(report_text) -> None:
    """Two of the three survive the cutover uncontrolled, and the report has to say so.

    The rake-free solve removes rake. Price does not go away: phase 12 abstracts an opponent's
    price to the solved one and the corpus was played cheaper. Nor does the realization model,
    which underprices position and is accepted rather than fixed under decision 3.
    """
    body = section(report_text, "explanations")
    named = r"^\s*(?:the\s+)?(rake|price|realization)\b[^\n]*\b(separated|uncontrolled)\b"
    verdicts = dict(re.findall(named, body, re.MULTILINE))

    assert verdicts == {"rake": "separated", "price": "uncontrolled", "realization": "uncontrolled"}


def test_the_corpus_opening_price_distribution_is_published(report_text) -> None:
    """How much of the sample sits at each price is what quantifies phase 12's ruling 8. The
    qualification alone cannot be weighed; a distribution can, so it is published as counts
    that add up to the decisions it is over, with the percentages recomputed here.
    """
    body = section(report_text, "price")
    rows = re.findall(r"^\s*(\d+(?:\.\d+)?)bb\s+(\d+)\s+\((\d+(?:\.\d+)?)%\)\s*$", body, re.M)
    total = re.search(r"decisions facing exactly one raise\s+(\d+)", body, re.IGNORECASE)

    assert len(rows) >= 4, f"an opening-price distribution over {len(rows)} prices is a summary"
    assert total is not None, "the distribution is published without the total it is over"
    assert sum(int(count) for _, count, _ in rows) == int(total.group(1))
    for price, count, percent in rows:
        share = 100.0 * int(count) / int(total.group(1))
        assert float(percent) == pytest.approx(share, abs=0.05), price


def test_every_rate_carries_its_sample_and_is_published_per_population(report_text) -> None:
    """Three rates, two populations, before and after, and never one figure over both.

    The refusal rate is beside the agreement rate because a rate over the subset the chart
    could answer is a narrower claim, and the stricter sampled-action match is beside it
    because a chart that got more mixed scores higher while playing no better.
    """
    rows = rate_rows(section(report_text, "corpus"))
    wanted = {"agreement", "refused", "sampled-action match"}

    for population in POPULATIONS:
        for when in ("before", "after"):
            here = [row for row in rows if row.population == population and row.when == when]
            assert wanted <= {row.label for row in here}, f"{population} {when}: {here}"
    for row in rows:
        assert row.denominator > 0
        assert row.percent == pytest.approx(100.0 * row.numerator / row.denominator, abs=0.05), row
        if row.label != "sampled-action match":
            continue
        key = (row.population, row.when, "agreement")
        looser = next(o for o in rows if (o.population, o.when, o.label) == key)
        assert row.percent <= looser.percent, f"the stricter rate cannot beat the looser: {row}"

    assert "nonzero weight" in report_text.lower()
    assert "not an oracle" in report_text.lower()


def test_the_report_bounds_what_the_chart_answers_at_all(report_text) -> None:
    """An agreement rate on one table configuration is not a grade on preflop play."""
    body = section(report_text, "bounds").lower()

    for token in ("six-handed", "100", "symmetric", "no straddle", "no ante", "2.5"):
        assert token in body, f"the bounds section does not state {token!r}"


def test_the_refusal_movement_is_stated_by_reason_over_the_closed_vocabulary(report_text) -> None:
    """One total hides the finding: the codes move in different directions and by different
    sizes. Every code gets a row, a zero included, because a reason that stopped happening is a
    result; no row may name a code outside the vocabulary; and the rows add up to the refusals
    the per-population rates published.
    """
    after = refusals_after(section(report_text, "refusals"))
    reported = reported_refusals(report_text)

    assert set(after) == set(lookup.MISS_CODES)
    assert set(re.findall(r"lookup:[a-z-]+", report_text)) <= set(lookup.MISS_CODES)
    assert reported
    assert sum(after.values()) == sum(row.numerator for row in reported)


def test_the_phase_publishes_its_own_limped_decision_point_count(report_text) -> None:
    """Decision 12: counted by a stated definition, and recounted here from the inventory.

    The figure quoted in `CHART-CANNOT-ANSWER-A-LIMPED-POT` carries no definition and is not
    reproduced. What the phase owes instead is a count whose rule a reader can apply - the
    first recorded action in the spot key is a call - applied here to the report's own
    inventory, which has to be the whole of it for that to mean anything.
    """
    body = section(report_text, "refusals")
    limp = r"^\s*decision points facing a limp\s+(\d+) inventory rows\s+(\d+) decision points$"
    stated = re.search(limp, body, re.MULTILINE)
    rows = inventory_rows(body)
    limped = [(points, key) for points, key in rows if first_action_is_a_call(key)]

    assert stated is not None, "the limped-decision-point count is not published"
    assert "first recorded action in the spot key is a call" in body
    assert int(stated.group(1)) == len(limped)
    assert int(stated.group(2)) == sum(points for points, _ in limped)
    assert sum(points for points, _ in rows) == sum(
        row.numerator for row in reported_refusals(report_text)
    )


def test_the_report_names_a_commit_the_retired_chart_can_be_read_at(report_text) -> None:
    """Decision 7's pin, checked as a pin rather than as a string that looks like one, and the
    disagreement it produced published with its direction. A pin nobody can fetch the same
    bytes from is a citation rather than a comparison.
    """
    body = section(report_text, "old_versus_new")
    found = re.finditer(r"commit\s+([0-9a-f]{7,40})", body)
    pins = [
        match.group(1)
        for match in found
        if "retired" in body[max(0, match.start() - 200) : match.end() + 200].lower()
    ]
    shared = re.search(r"decisions both charts answer\s+(\d+)", body)
    disagreed = re.search(r"disagreed\s+(\d+)", body)
    directions = re.findall(r"^\s*(?:derived|retired) continues[^\n]*?(\d+)\s*$", body, re.M)

    assert pins, "the old-versus-new section names no commit the retired chart was read at"
    for pin in pins:
        assert git("cat-file", "-e", f"{pin}:{RETIRED_CHART}").returncode == 0, pin
    assert shared is not None and disagreed is not None, body
    assert int(shared.group(1)) > 0
    assert len(directions) == 2, "the disagreement is published without which way it went"
    assert sum(int(count) for count in directions) == int(disagreed.group(1))
    assert int(disagreed.group(1)) <= int(shared.group(1))


def test_the_census_in_the_report_adds_up_to_the_export_source_card(report_text) -> None:
    """Three buckets and a total a reader can check against a file this phase did not write."""
    body = section(report_text, "census")
    committed = re.search(r"^\s*committed\s+(\d+)\s*$", body, re.MULTILINE)
    excluded = re.findall(r"^\s*excluded\s+(derivation:[a-z-]+)\s+(\d+)\s*$", body, re.MULTILINE)
    unwritable = re.findall(r"^\s*inexpressible\s+(derivation:[a-z-]+)\s+(\d+)$", body, re.M)

    assert committed is not None and excluded and unwritable, body
    assert {code for code, _ in excluded} <= set(lookup.DERIVATION_EXCLUSION_CODES)
    assert {code for code, _ in unwritable} <= set(lookup.DERIVATION_INEXPRESSIBILITY_CODES)

    cards = sorted((ARTIFACT_DIR / "exports").glob("*.source.json"))
    assert len(cards) == 1, f"expected exactly one export source card, found {cards}"
    counted = list(excluded) + list(unwritable)
    total = int(committed.group(1)) + sum(int(count) for _, count in counted)
    card = json.loads(cards[0].read_text(encoding="utf-8"))
    assert total == card["node_counts"]["exported"]


def test_one_cell_is_traced_from_an_export_node_to_the_row_it_became(report_text) -> None:
    """The trace is checked against the artifact, because a printed trace proves nothing.

    A reviewer who cannot read code follows this row to see a solved node become a chart cell
    with nothing invented on the way, so the weights and the arriving reach are read back out
    of the committed artifact here, decision 5's per-cell reach included.
    """
    body = section(report_text, "trace")
    traced = r"^\s*artifact row\s+(t6/\S+)\s+([2-9TJQKA]{2}[so]?)\s+(.+?)\s+reach\s+(\d+) bp$"
    row = re.search(traced, body, re.MULTILINE)

    assert re.search(r"^\s*export node\s+\S+", body, re.MULTILINE), (
        "the trace does not name the export node the row came from"
    )
    assert row is not None, "the trace does not print the artifact row in the pinned form"

    artifacts = import_preflop_artifacts(ARTIFACT_DIR)
    named = [art.source.name for art in artifacts]
    assert len(artifacts) == 1, f"the report's figures are about a mixture of charts: {named}"
    artifact = artifacts[0]
    spot_key, hand_class, printed, reach = row.groups()
    weights = [classes for spot, classes in artifact.action_weights if spot == spot_key]
    cells = {text: dict(actions) for classes in weights for text, actions in classes}
    assert hand_class in cells, f"{spot_key} carries no {hand_class} in the committed artifact"
    for action, weight in re.findall(r"([a-z]+)=([0-9.]+)", printed):
        assert cells[hand_class].get(action) == pytest.approx(float(weight), abs=0.0001), action
    assert artifact.reach_bp_for(spot_key, hand_class) == int(reach)


def test_the_relations_are_published_at_the_ruled_tolerance(generator, report_text) -> None:
    """A surviving violation is decision 2's second branch and has to be recorded as one."""
    body = section(report_text, "dominance")
    counts = [int(value) for value in re.findall(r"violations\s+(\d+)", body)]

    assert len(counts) == 2, "the report publishes a violation count for each of the two relations"
    assert re.search(rf"{generator.MONOTONICITY_TOLERANCE_PCT}\s*(?:percentage )?point", body)
    assert "adjacent" in body.lower()
    if any(counts):
        assert "ships as solved" in body.lower() or "considered answer" in body.lower()


def test_the_two_orderings_hold_in_the_numbers_the_report_publishes(report_text) -> None:
    """Later position opens wider, and the big blind defends more against a wider opener,
    recomputed from the published column rather than read off a sentence saying they hold.
    These survive any rake basis and any solver, which is why they transfer.
    """
    body = section(report_text, "orderings")
    pattern = r"^\s*(LJ|HJ|CO|BTN|SB)\s+opens\s+(\d+\.\d+)\s+big blind defends\s+(\d+\.\d+)$"
    found = re.findall(pattern, body, re.MULTILINE)
    rows = {position: (float(opens), float(defends)) for position, opens, defends in found}

    assert set(rows) == {"LJ", "HJ", "CO", "BTN", "SB"}
    opens = [rows[position][0] for position in ("LJ", "HJ", "CO", "BTN")]
    defence = [rows[position][1] for position in ("LJ", "HJ", "CO", "BTN")]
    assert opens == sorted(opens), f"later position does not open wider: {opens}"
    # The small blind sits out of the defence ordering rather than failing it: the big blind
    # closes heads-up against it, in position and at a price, so it defends 42.88 against a
    # 34.41 opener, which is correct poker rather than a broken ordering.
    assert defence == sorted(defence), f"the big blind does not defend more against wider: {rows}"


def test_the_derived_chart_is_printed_against_the_external_expectations(report_text) -> None:
    """The one column the repo did not produce, so it must match the file: a reference
    regenerated from what it checks cannot fail, which is why it is not rederived here."""
    body = section(report_text, "expectations")
    pattern = r"^\s*(LJ|HJ|CO|BTN|SB)\s+derived\s+(\d+\.\d+)\s+GTO Wizard\s+(\d+\.\d+)$"
    rows = re.findall(pattern, body, re.MULTILINE)
    expected = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["open_frequency_pct"]

    assert {position for position, _, _ in rows} == set(expected)
    for position, _, printed in rows:
        assert float(printed) == pytest.approx(expected[position], abs=0.005), position
    assert re.search(r"gated by nothing|does not gate|not a threshold", body), (
        "the comparison against another program's product must say it grades nothing"
    )


def test_the_report_names_the_number_a_reader_can_recompute_by_hand(report_text) -> None:
    """The audit packet has to say which number and how, so the report has to name one."""
    body = section(report_text, "recomputable")
    number = re.search(r"^\s*the number\s+(\S.*?)\s*$", body, re.MULTILINE)
    origin = re.search(r"^\s*the file\s+(\S+)\s*$", body, re.MULTILINE)
    arithmetic = re.search(r"^\s*the arithmetic\s+(\S.*?)\s*$", body, re.MULTILINE)

    assert number is not None and origin is not None and arithmetic is not None, body
    assert re.search(r"\d", number.group(1)), "the named number is not a number"
    assert (REPO_ROOT / origin.group(1)).exists(), origin.group(1)


def test_the_report_fits_the_size_the_file_check_allows(report_text, generator) -> None:
    """`reports/active/*.txt` is capped at 300 KB, and the inventory above is most of it."""
    assert generator.REPORT_OUTPUT.stat().st_size <= 300 * 1024
    assert report_text.endswith("\n")
