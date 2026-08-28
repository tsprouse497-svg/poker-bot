"""Phase 14: the report a non-coding reviewer reads, and the closing corpus measurement.

This file owns the published report: that every heading the spec names is there, that the body
under each makes the claim the heading promises, and that the numbers printed under them are
the numbers the phase measured. `tests/test_derived_chart_report_validators.py` is the other
half, split from this one when the pair went past the 700-line cap. It owns the generator's
refusals - each validator fed a deliberately wrong input and made to exit non-zero - and it
imports this file's census constants, its command id and its paths rather than copying them,
so the two halves cannot drift apart. The seam is what is on trial: a rendered report here, an
unrendered one there. Both files run under `pytest_derived_chart`.

The split from the derivation tests is the older seam and still holds: the chart being right
and a reviewer being led to the right conclusion about it are separate things. A report renders
whatever it is handed, so the sibling exists at all.

Two things the ruled predicate changed about this file. The census the report publishes is 86
committed against **two** exclusion codes rather than 5,626 against one, so a report naming one
code is naming a vocabulary that cannot say which nodes come back when GTOpen can price
multiway. And the coverage claim reversed sign: the cutover gains 65 spots and gives up 14 plus
the limped pot, so the refusal rate must **rise**, confined to those fifteen spots, where the
criterion previously called any rise a defect.

Decision 9 fixed the closing prediction's band before any of it was measured, so the report is
checked against the decision record rather than allowed to restate its own prediction.

The headings in `HEADINGS` and the row shapes the parsers require are part of the spec.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import NamedTuple

import pytest

from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from scripts.repo_paths import REPO_ROOT

COMMAND_ID = "generate_derived_chart_report"


ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"


EXPECTATIONS = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"


RETIRED_CHART = "data/artifacts/preflop/six_max_nl25_100bb.json"


DECISIONS = (
    REPO_ROOT / "reports" / "phase_audits" / "decisions" / "PHASE_14_CHART_CUTOVER_DECISIONS.md"
)


# The census the ruled predicate produces over the committed export, every figure of it a tree
# fact. They are here rather than recomputed because this file feeds them to a validator as
# *inputs* - the walk that derives them is `test_chart_derivation.py`'s subject.
EXPORTED_NODES = 38_828


COMMITTED_SPOTS = 86


MISPRICED_NODES = 33_356


OUTSIDE_RULE_NODES = 5_386


# What the cutover did to coverage, measured before the ruling rather than after. The refusal
# rate rises on these fifteen and nowhere else; a rise outside them is a defect rather than
# the cost of the ruling.
RETIRED_CHART_SPOTS = 36


RETIRED_SPOTS_REFUSED = 14


RETIRED_SPOTS_STILL_COVERED = 21


SPOTS_GAINED = COMMITTED_SPOTS - RETIRED_SPOTS_STILL_COVERED
"""Derived, never a literal. A spot is gained when the derived chart answers it and the retired
chart did not, so gained is the committed count less the number carried over: 86 - 21 = 65. The
64 this file used to hold was 86 - 22, which counted the limped pot `t6/d100/BB/SB:call` as
carried over although it passes the predicate with no node to derive from and is not among the
86 at all. Stated as the relation so the constants beside it cannot drift apart again, and
because the report's published figure is then checked against the relation rather than against
a number this file remembered."""


LIMPED_SPOT = "t6/d100/BB/SB:call"


# The report's own headings. Exactly one of each, and the body under it is where the claim
# that heading names has to be made.
HEADINGS = {
    "census": "## The three-way node census",
    "trace": "## One converted cell, traced",
    "dominance": "## The two dominance relations",
    "orderings": "## The two orderings",
    "expectations": "## The derived chart against the GTO Wizard expectations",
    "coverage": "## What the cutover gained and gave up",
    "corpus": "## The corpus, before and after",
    "prediction": "## The pre-registered prediction",
    "price": "## The price the corpus was played at",
    "explanations": "## What this measurement can and cannot separate",
    "bounds": "## What this chart does not answer",
    "refusals": "## The refusal inventory, by reason",
    "old_versus_new": "## Where the retired chart and the derived chart disagree",
    "recomputable": "## One number a reader can recompute by hand",
}


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
    than copied here. The record is the pre-registration and this file is frozen after it, so
    a band restated in the report is the agent that ran the measurement setting its own bar.
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


def refusals_before(body: str) -> dict[str, int]:
    return {code: int(before) for code, before, _ in re.findall(REFUSAL_ROW, body, re.MULTILINE)}


def reported_refusals(text: str) -> list[RateRow]:
    rows = rate_rows(section(text, "corpus"))
    return [row for row in rows if row.label == "refused" and row.when == "after"]


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True)


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
    """Decision 9's rule and its verdict, both recomputed from the report's own columns.

    The rule is checked rather than the five figures, because the deltas are a measurement over
    the export and the report is where they are recomputed: the record's numbers are quoted
    from the stage-4 walk and the report owes its own. A miss either way is a result, so the
    side is named rather than the band merely printed.
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
    corpus median of 2.25, and "the price-tracking part will not move" is false for it. It is
    also the only opening price the chart still holds, which is why this family is named.
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


def test_the_refusal_rate_rises_and_the_report_says_it_was_ruled_to(report_text) -> None:
    """The criterion whose sign the predicate reversed, and the reason it is worth a test.

    Until 2026-08-25 this phase expected the refusal rate to fall and called a rise a defect.
    Under the ruled predicate 14 of the retired chart's 36 spots are refused - four opening
    ranges among them - and the limped pot goes with them, so the rate **rises** and that is
    the ruled cost. A report publishing a fall is reporting a chart that is not this one.
    """
    for population in POPULATIONS:
        rows = [
            row
            for row in rate_rows(section(report_text, "corpus"))
            if row.population == population and row.label == "refused"
        ]
        before = next(row for row in rows if row.when == "before")
        after = next(row for row in rows if row.when == "after")
        assert after.percent > before.percent, (population, before, after)


def test_the_report_publishes_what_the_cutover_gained_and_gave_up(report_text) -> None:
    """The coverage claim in the form the measurement left it, spot by spot.

    Every stage-4 document said all 36 retired spots survive, which was a reading of their
    action histories and is false of the predicate that was ruled. 22 pass it, 21 are covered,
    and the twenty-second is the limped pot the solve has no branch for. The fourteen are named
    because a count of fourteen with the wrong fourteen in it is the same arithmetic and a
    different chart, and the opening coverage is stated in seats because that is the loss a
    reader can feel: the bot cannot open a pot from four of six seats.

    The gained figure is read off a labelled row and checked as a **relation**: gained is the
    committed count less the number carried over, and the retired chart's own 36 is those 21
    plus the fourteen refused plus the one limped pot. An earlier draft compared a constant
    against its own definition, which cannot fail, and swept the section for the right integer
    appearing anywhere, which passes on a report that publishes 64 and mentions 65 in prose.
    The phase's own documents did publish 64, which is 86 - 22 and counts the limped pot as
    carried over though it is refused.
    """
    body = section(report_text, "coverage")
    refused = re.findall(r"^\s*refused\s+(t6/\S+)", body, re.MULTILINE)
    gained = re.search(r"^\s*gained\s+(\d+)\s*$", body, re.MULTILINE)
    carried = re.search(r"^\s*carried over\s+(\d+)\s*$", body, re.MULTILINE)

    # The relation is asserted against the figures the report PUBLISHES, not against the
    # constants at the top of this file. Comparing a derived constant to its own definition
    # cannot fail, and a set-membership sweep over every integer in the section passes when
    # the right number appears anywhere in it, including in a sentence about something else.
    assert gained is not None and carried is not None, body
    assert int(carried.group(1)) == RETIRED_SPOTS_STILL_COVERED
    assert int(gained.group(1)) == COMMITTED_SPOTS - int(carried.group(1)) == SPOTS_GAINED
    assert RETIRED_SPOTS_STILL_COVERED + RETIRED_SPOTS_REFUSED + 1 == RETIRED_CHART_SPOTS
    assert len(refused) == RETIRED_SPOTS_REFUSED, refused
    assert len(set(refused)) == len(refused)
    for key in refused:
        assert not key.endswith(":call"), f"{key} is the limped pot, counted apart from the 14"
    assert {f"t6/d100/{seat}/rfi" for seat in ("LJ", "HJ", "CO", "BTN")} <= set(refused)
    assert LIMPED_SPOT in body
    seats = r"five\s+(?:seats|positions)\s+to\s+one|5\s+(?:seats|positions)\s+to\s+1"
    assert re.search(seats, body), (
        "the coverage section does not state that opening coverage falls from five seats to one"
    )


def test_the_report_bounds_what_the_chart_answers_at_all(report_text) -> None:
    """An agreement rate on one table configuration is not a grade on preflop play.

    "Heads-up only" is on the list because it is the ruled predicate stated as a bound: the
    chart answers a decision only where at most one opponent has invested and at most two
    players are live, so a rate read off it says nothing about multiway play.
    """
    body = section(report_text, "bounds").lower()

    for token in (
        "six-handed",
        "100",
        "symmetric",
        "no straddle",
        "no ante",
        "2.5",
        "heads-up",
    ):
        assert token in body, f"the bounds section does not state {token!r}"


def test_the_refusal_movement_is_stated_by_reason_over_the_closed_vocabulary(report_text) -> None:
    """One total hides the finding: the codes move in different directions and by different
    sizes. Every code gets a row, a zero included, because a reason that stopped happening is a
    result; no row may name a code outside the vocabulary; and the rows add up to the refusals
    the per-population rates published. At least one code has to go up, since the predicate
    refuses fourteen spots the retired chart answered.
    """
    body = section(report_text, "refusals")
    after = refusals_after(body)
    before = refusals_before(body)
    reported = reported_refusals(report_text)

    assert set(after) == set(lookup.MISS_CODES)
    assert set(before) == set(lookup.MISS_CODES)
    assert set(re.findall(r"lookup:[a-z-]+", report_text)) <= set(lookup.MISS_CODES)
    assert reported
    assert sum(after.values()) == sum(row.numerator for row in reported)
    assert sum(after.values()) > sum(before.values())


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
    """Three buckets and a total a reader can check against a file this phase did not write.

    Both exclusion reasons get their own row, because the point of having two is that a reader
    can tell the 33,356 nodes the source misprices from the 5,386 that are priced exactly and
    reached through a cold call. A census publishing one excluded row has lost that.
    """
    body = section(report_text, "census")
    committed = re.search(r"^\s*committed\s+(\d+)\s*$", body, re.MULTILINE)
    excluded = re.findall(r"^\s*excluded\s+(derivation:[a-z-]+)\s+(\d+)\s*$", body, re.MULTILINE)
    unwritable = re.findall(r"^\s*inexpressible\s+(derivation:[a-z-]+)\s+(\d+)$", body, re.M)

    assert committed is not None and excluded and unwritable, body
    assert {code for code, _ in excluded} == set(lookup.DERIVATION_EXCLUSION_CODES)
    assert {code for code, _ in unwritable} <= set(lookup.DERIVATION_INEXPRESSIBILITY_CODES)
    assert int(committed.group(1)) == COMMITTED_SPOTS

    cards = sorted((ARTIFACT_DIR / "exports").glob("*.source.json"))
    assert len(cards) == 1, f"expected exactly one export source card, found {cards}"
    counted = list(excluded) + list(unwritable)
    total = int(committed.group(1)) + sum(int(count) for _, count in counted)
    card = json.loads(cards[0].read_text(encoding="utf-8"))
    assert total == card["node_counts"]["exported"] == EXPORTED_NODES


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
    """Per cell, published and gating nothing; per group, published with both mappings.

    Decision 10 was re-ruled to measure per cell and gate on aggregates, and the aggregate's
    own claim to catch a transposed hand index has to be visible rather than asserted: the
    solved column beside the transposed one is what shows the measure discriminating, and over
    the 5,626 that comparison came out backwards. A surviving per-cell violation is decision
    2's ship-as-solved branch and has to be recorded as one.
    """
    body = section(report_text, "dominance")
    counts = [int(value) for value in re.findall(r"violations\s+(\d+)", body)]
    groups = re.findall(r"^\s*(.+?)\s+solved\s+(\d+)\s+transposed\s+(\d+)\s*$", body, re.MULTILINE)

    assert len(counts) == 2, "the report publishes a violation count for each of the two relations"
    assert re.search(rf"{generator.MONOTONICITY_TOLERANCE_PCT}\s*(?:percentage )?point", body)
    assert "adjacent" in body.lower()
    assert groups, "the report publishes no group aggregate against its transposed mapping"
    for label, solved, transposed in groups:
        assert int(solved) < int(transposed), (label, solved, transposed)
    if any(counts):
        assert "ships as solved" in body.lower() or "considered answer" in body.lower()


def test_the_two_orderings_hold_in_the_numbers_the_report_publishes(report_text) -> None:
    """Later position opens wider, and the big blind defends more against a wider opener,
    recomputed from the published column rather than read off a sentence saying they hold.
    These survive any rake basis and any solver, which is why they transfer.

    The opening column is the **export's**, and the report has to say so: the ruled predicate
    commits one opening range, so four of the five opening frequencies are no longer properties
    of the chart at all. Printing them as the chart's would be the report claiming coverage the
    cutover gave up. The defence column is the chart's, because every one of the big blind's
    twenty spots survives the predicate.
    """
    body = section(report_text, "orderings")
    pattern = (
        r"^\s*(LJ|HJ|CO|BTN|SB)\s+opens\s+\(export\)\s+(\d+\.\d+)"
        r"\s+big blind defends\s+\(chart\)\s+(\d+\.\d+)$"
    )
    found = re.findall(pattern, body, re.MULTILINE)
    rows = {position: (float(opens), float(defends)) for position, opens, defends in found}

    assert set(rows) == {"LJ", "HJ", "CO", "BTN", "SB"}
    opens = [rows[position][0] for position in ("LJ", "HJ", "CO", "BTN")]
    assert opens == sorted(opens), f"later position does not open wider: {opens}"
    # The defence ordering follows the opening frequencies wherever they land rather than a
    # fixed seat order, which is what keeps the widest-opening seat inside the check.
    ordered = sorted(rows, key=lambda position: rows[position][0])
    defence = [rows[position][1] for position in ordered]
    assert defence == sorted(defence), f"the big blind does not defend more against wider: {rows}"


def test_the_derived_chart_is_printed_against_the_external_expectations(report_text) -> None:
    """The one column the repo did not produce, so it must match the file: a reference
    regenerated from what it checks cannot fail, which is why it is not rederived here.

    Each row says where its own left-hand figure came from, and only one can say `derived`:
    the small blind's is the one opening range the cutover commits. The other four come from
    the export, and a row claiming `derived` for the lojack is a chart built on the superseded
    predicate saying so in its own report.
    """
    body = section(report_text, "expectations")
    pattern = r"^\s*(LJ|HJ|CO|BTN|SB)\s+(derived|export)\s+(\d+\.\d+)\s+GTO Wizard\s+(\d+\.\d+)$"
    rows = re.findall(pattern, body, re.MULTILINE)
    expected = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["open_frequency_pct"]

    assert {position for position, _, _, _ in rows} == set(expected)
    assert [position for position, source, _, _ in rows if source == "derived"] == ["SB"]
    for position, _, _, printed in rows:
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
