"""Phase 14: the report a non-coding reviewer reads, and the closing corpus measurement.

This file owns the published report: every heading the spec names is there, the body under each
makes the claim it promises, and the numbers are the ones the phase measured.
`tests/test_derived_chart_report_validators.py` is the other half, split at the 700-line cap; it
owns the generator's refusals and imports this file's constants and paths rather than copying.

**Re-cut at stage 4 three times on 2026-09-01.** The census is 6 committed against **five**
exclusion codes summing to 33,969: decision 20 added one reason, Taylor's first evening ruling a
second for the jam-facing spots, his second a third for the three-bet-facing spots. Coverage went
to zero - the committed 6 are exactly the 6 retired spots that carry over, so the cutover gains
**nothing** and gives up twenty-nine spots plus the limped pot. The dominance section carries two
families and must say which gates: the per-cell measure over spot partitions does, on **two**
counterfactual arms since the rank ruling, and the group-order ladders do not. Decision 24 makes
the report publish the flat frequency at every committed spot, the withheld jams are published
with aces' weight at each, and decision 9 fixed the prediction's band before it was measured.
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


# The census over the re-sourced export, every figure a tree fact. They are here rather than
# recomputed because this file feeds them to a validator as *inputs*; the walk that derives them
# is `test_chart_derivation.py`'s subject.
EXPORTED_NODES = 33_969
COMMITTED_SPOTS = 6
MULTIWAY_NODES = 29_104
THREE_BET_BRANCH_NODES = 15
FOUR_BET_POT_NODES = 15
JAM_INHERITS_NODES = 15
OUTSIDE_RULE_NODES = 4_814

FOUR_BET_POT_CODE = "derivation:source-misprices-four-bet-pot"
JAM_INHERITS_CODE = "derivation:inherits-a-mispriced-four-bet-node"
THREE_BET_BRANCH_CODE = "derivation:weighs-a-mispriced-four-bet-branch"
"""The three withholding reasons, spelled here because stage 6 has not written them into
`lookup` yet. `tests/test_chart_derivation.py` spells them too and both files assert the module's
own tuple against their spelling. All three families number 15, so a census under one code
balances exactly and says nothing about which fix recovers what."""

# What the cutover did to coverage. The refusal rate rises on the twenty-nine and the limped pot
# and nowhere else; a rise outside them is a defect rather than the cost of the rulings.
WITHHELD_FOUR_BET_SPOTS = 15
"""Decision 20's withholding: hero facing a four-bet, three raises in the sequence. It is the
only family where hero is *offered* a jam, which is what the canary section is about."""
GROUP_LADDERS = 5
"""The five group-order partitions `tests/test_chart_cutover_evidence.py` measures: single pair
ranks, pair bands in four, three and two, and the suited rows. Gating nothing since 2026-09-01."""
RETIRED_CHART_SPOTS = 36
RETIRED_SPOTS_REFUSED = 29
"""Fourteen the predicate never wanted, and fifteen it kept and the second 2026-09-01 ruling
withheld, every one hero facing a three-bet - exactly where GTO Wizard's 36 stop. The limped
pot is counted apart, so 6 + 29 + 1 = 36."""
RETIRED_SPOTS_STILL_COVERED = 6

SPOTS_GAINED = COMMITTED_SPOTS - RETIRED_SPOTS_STILL_COVERED
"""**Zero. The cutover adds no coverage at all.** It replaces raked ranges with rake-free ones at
the same 6 decisions and answers nothing the retired chart did not, while giving up twenty-nine
spots plus the limped pot - legitimate, and not what the contract's framing assumes, so the
report states it plainly. Derived: the committed count less the number carried over."""

LIMPED_SPOT = "t6/d100/BB/SB:call"
# The report's headings, exactly one of each; the body under it is where the claim is made.
HEADINGS = {
    "census": "## The three-way node census",
    "trace": "## One converted cell, traced",
    "dominance": "## The two dominance relations",
    "flats": "## How often the committed spots flat a raise",
    "jams": "## The withheld jams, and what aces do at each",
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

GATED_ROW = (
    r"^\s*(.+?)\s+suit swap\s+solved\s+(\d+)\s+transposed\s+(\d+)"
    r"\s+rank reversal\s+solved\s+(\d+)\s+permuted\s+(\d+)\s*$"
)
"""One gated dominance row: the partition, then both counterfactual arms, each with its own
solved figure - two columns because the arms count different things, the suit swap counting spots
that hold a suited-under-offsuit cell and the rank arm cells that break the row ladder."""

LADDER_ROW = r"^\s*(group .+?)\s+solved\s+(\d+)\s+transposed\s+(\d+)\s*$"
"""A published group-order row: prefixed `group` and carrying no `permuted` column, so a reader
scanning the section cannot mistake one family's row for the other's."""

SIGNED = re.compile(r"[+-]\d+(?:\.\d+)?")
BAND = re.compile(
    r"([+-]?\d+\.\d+)\s+to\s+([+-]?\d+\.\d+)\s+(?:points\s+)?"
    r"against the (lojack|hijack|cutoff|small blind|button)"
)


@pytest.fixture(scope="module")
def generator():
    """Reached through a fixture rather than imported at the top: a top-level import of a module
    stage 6 has not written turns this whole file into one collection error."""
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
    """Decision 9's per-opener band, parsed out of the record that pre-registered it: a band
    restated in the report is the measuring agent setting its own bar."""
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
    """One row per opener: defence delta, both band ends, measured move, verdict, signed."""
    rows: dict[str, PredictionRow] = {}
    for line in body.splitlines():
        match = re.match(r"\s*(LJ|HJ|CO|SB|BTN)\b(.*)$", line)
        if match is None:
            continue
        numbers = [float(value) for value in SIGNED.findall(match.group(2))]
        verdict = re.search(r"\b(inside|above|below)\b", match.group(2))
        assert len(numbers) >= 4 and verdict is not None, (
            f"the row for {match.group(1)} must carry the defence delta, both band ends and the"
            f" measured move, each signed, then inside/above/below: {line!r}"
        )
        rows[match.group(1)] = PredictionRow(
            numbers[0], (min(numbers[1:3]), max(numbers[1:3])), numbers[3], verdict.group(1)
        )
    return rows


def inventory_rows(body: str) -> list[tuple[int, str]]:
    """The republished inventory: decision points and the spot key each reached."""
    found = re.findall(r"^\s*(\d+)\s+(t6/\S+)", body, re.MULTILINE)
    return [(int(points), key) for points, key in found]


def first_action_is_a_call(spot_key: str) -> bool:
    """Decision 12's definition, applied here rather than taken from the report."""
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
    """Every published rate with its population block; a row with no owning population pools two
    different sets of players."""
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


def discrimination_partitions(artifact) -> set[str]:
    """The labels the dominance section owes a gated row for, derived from the committed set: the
    whole set, one per seat hero sits in, one per number of raises faced. Those splits are where
    an aggregate hides a defect - a mis-assigned actor shows in one seat, an index read wrongly
    only deeper shows in one raise bucket. **Over the committed 6 that is five labels over three
    distinct sets**: `hero=SB` and `raises faced 0` are both the small blind's open, `hero=BB`
    and `raises faced 1` both the five defences. The duplication is kept rather than pruned,
    pruning by hand being a choice of which splits to publish after seeing them."""
    labels = {"the committed set"}
    for spot in artifact.spots:
        labels.add(f"hero={spot.hero_position}")
        faced = sum(1 for entry in spot.action_sequence if entry.action == "raise")
        labels.add(f"raises faced {faced}")
    return labels


def spot_menus(artifact) -> dict[str, set[str]]:
    """Which actions each committed spot offers hero, over any class."""
    return {
        spot_id: {action for _, weights in classes for action, _ in weights}
        for spot_id, classes in artifact.action_weights
    }


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True)


def test_the_prediction_matches_the_pre_registered_band_and_names_which_way_it_missed(
    report_text,
) -> None:
    """The band is read off decision 9's record, not restated by the agent that measured it, and
    its rule and verdict are recomputed from the report's own columns. A directional prediction
    was rejected: defence widens against four openers and comes back tighter against the button,
    which generates the most big-blind defending decisions in any six-max sample. The rule is
    checked rather than the five figures, and a miss either way is a result."""
    body = section(report_text, "prediction")
    rows, bands = prediction_rows(body), decision_bands()

    assert set(rows) == set(bands)
    assert "PHASE_14_CHART_CUTOVER_DECISIONS.md" in body
    for position, row in rows.items():
        assert row.band == bands[position], (
            f"{position}: the report predicts {row.band}, the record {bands[position]}"
        )
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
            f"{position} moved {row.measured} against {row.band}, called {row.verdict}"
        )


def test_the_price_section_says_which_way_the_repricing_went_and_publishes_the_spread(
    report_text,
) -> None:
    """The cutover reprices hero's small-blind open from 3.5bb to 2.5bb, so the big blind facing
    it moves from a 3.5-solved answer to a 2.5-solved one against a corpus median of 2.25; it is
    also the only opening price the chart holds. How much of the sample sits at each price
    quantifies phase 12's ruling 8, so it is published as counts adding to the decisions it is
    over. Two of the three candidate explanations survive uncontrolled and the report says so:
    the rake-free solve removes rake, price and realization are untouched."""
    body = section(report_text, "price")
    repriced = [x for x in body.splitlines()
                if "small blind" in x.lower() and "3.5" in x and "2.5" in x]
    median = r"median[^\n]*\b2\.25\b|\b2\.25\b[^\n]*median"
    rows = re.findall(r"^\s*(\d+(?:\.\d+)?)bb\s+(\d+)\s+\((\d+(?:\.\d+)?)%\)\s*$", body, re.M)
    total = re.search(r"decisions facing exactly one raise\s+(\d+)", body, re.IGNORECASE)

    assert repriced, "the report does not say hero's small-blind open moved from 3.5bb to 2.5bb"
    assert re.search(r"t6/d\d+/BB/SB:raise@2\.5", body), "no spot family named for the repricing"
    assert re.search(median, body, re.IGNORECASE), "no corpus median price beside the word median"
    assert len(rows) >= 4, f"an opening-price distribution over {len(rows)} prices is a summary"
    assert total is not None, "the distribution is published without the total it is over"
    assert sum(int(count) for _, count, _ in rows) == int(total.group(1))
    for price, count, percent in rows:
        share = 100.0 * int(count) / int(total.group(1))
        assert float(percent) == pytest.approx(share, abs=0.05), price

    named = r"^\s*(?:the\s+)?(rake|price|realization)\b[^\n]*\b(separated|uncontrolled)\b"
    verdicts = dict(re.findall(named, section(report_text, "explanations"), re.MULTILINE))
    assert verdicts == {"rake": "separated", "price": "uncontrolled", "realization": "uncontrolled"}


def test_every_rate_carries_its_sample_per_population_and_the_refusal_rate_rises(
    report_text,
) -> None:
    """Three rates, two populations, before and after, never one figure over both. The refusal
    rate sits beside the agreement rate because a rate over the subset the chart could answer is
    a narrower claim, and the sampled-action match beside those because a chart that got more
    mixed scores higher while playing no better. The refusal rate is also the criterion whose
    sign the predicate reversed: this phase expected it to fall, but 29 of the retired 36 are
    refused and the limped pot with them, so it **rises** and that is ruled."""
    rows = rate_rows(section(report_text, "corpus"))
    wanted = {"agreement", "refused", "sampled-action match"}

    for population in POPULATIONS:
        for when in ("before", "after"):
            here = [row for row in rows if row.population == population and row.when == when]
            assert wanted <= {row.label for row in here}, f"{population} {when}: {here}"
        refusals = [r for r in rows if r.population == population and r.label == "refused"]
        before = next(row for row in refusals if row.when == "before")
        after = next(row for row in refusals if row.when == "after")
        assert after.percent > before.percent, (population, before, after)
    for row in rows:
        assert row.denominator > 0
        assert row.percent == pytest.approx(100.0 * row.numerator / row.denominator, abs=0.05), row
        if row.label != "sampled-action match":
            continue
        key = (row.population, row.when, "agreement")
        looser = next(o for o in rows if (o.population, o.when, o.label) == key)
        assert row.percent <= looser.percent, f"the stricter rate cannot beat the looser: {row}"

    assert "nonzero weight" in report_text.lower() and "not an oracle" in report_text.lower()


def test_the_report_publishes_what_the_cutover_gained_and_gave_up(report_text) -> None:
    """The coverage claim in the form the measurement left it, spot by spot.

    Every stage-4 document said all 36 retired spots survive, a reading of their action histories
    the ruled predicate falsifies: 22 pass it, and of those 6 are covered, 15 are withheld as
    three-bet-facing and the twenty-second is the limped pot. **The gained figure is zero: the
    cutover adds no coverage at all.** It was 15 until Taylor withheld the jam-facing spots on
    2026-09-01 and stayed 0 when he withheld the three-bet spots that evening, leaving the
    committed set at exactly the 6 decisions the retired chart already answered. What it buys is
    that those 6 are rake-free, correctly priced and re-solved. A zero has to be published as a
    figure rather than omitted, and the refused rows carry both reasons, because a count of
    twenty-nine with the wrong twenty-nine is the same arithmetic and a different chart."""
    body = section(report_text, "coverage")
    refused = re.findall(r"^\s*refused\s+(t6/\S+)", body, re.MULTILINE)
    gained = re.search(r"^\s*gained\s+(\d+)\s*$", body, re.MULTILINE)
    carried = re.search(r"^\s*carried over\s+(\d+)\s*$", body, re.MULTILINE)

    # Asserted against the figures the report PUBLISHES, not the constants above: comparing a
    # derived constant to its own definition cannot fail, and sweeping the section for an
    # integer passes when the right number appears in a sentence about something else.
    assert gained is not None and carried is not None, body
    assert int(carried.group(1)) == RETIRED_SPOTS_STILL_COVERED
    assert int(gained.group(1)) == COMMITTED_SPOTS - int(carried.group(1)) == SPOTS_GAINED == 0
    assert RETIRED_SPOTS_STILL_COVERED + RETIRED_SPOTS_REFUSED + 1 == RETIRED_CHART_SPOTS
    assert len(refused) == RETIRED_SPOTS_REFUSED, refused
    assert len(set(refused)) == len(refused)
    for key in refused:
        assert not key.endswith(":call"), f"{key} is the limped pot, counted apart from the 29"
    assert {f"t6/d100/{seat}/rfi" for seat in ("LJ", "HJ", "CO", "BTN")} <= set(refused)
    withheld = [key for key in refused if key.split("/")[3].count(":raise@") == 2]
    assert len(withheld) == JAM_INHERITS_NODES, withheld
    assert LIMPED_SPOT in body
    seats = r"five\s+(?:seats|positions)\s+to\s+one|5\s+(?:seats|positions)\s+to\s+1"
    assert re.search(seats, body), "opening coverage is not stated as falling five seats to one"


def test_the_refusal_section_moves_by_reason_and_counts_its_own_limped_decision_points(
    report_text,
) -> None:
    """One total hides the finding: the codes move in different directions and sizes. Every code
    gets a row, a zero included, because a reason that stopped happening is a result; no row may
    name a code outside the vocabulary; and the rows add up to the refusals the per-population
    rates published. At least one code has to go up, the cutover refusing twenty-nine spots the
    retired chart answered. Decision 12 sits in the same section: the limped-decision-point count
    by a stated definition, recounted from the inventory, since `CHART-CANNOT-ANSWER-A-LIMPED-POT`
    carries no figure - the rule being that the spot key's first recorded action is a call."""
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

    limp = r"^\s*decision points facing a limp\s+(\d+) inventory rows\s+(\d+) decision points$"
    stated = re.search(limp, body, re.MULTILINE)
    rows = inventory_rows(body)
    limped = [(points, key) for points, key in rows if first_action_is_a_call(key)]

    assert stated is not None, "the limped-decision-point count is not published"
    assert "first recorded action in the spot key is a call" in body
    assert int(stated.group(1)) == len(limped)
    assert int(stated.group(2)) == sum(points for points, _ in limped)
    assert sum(points for points, _ in rows) == sum(row.numerator for row in reported)


def test_the_report_names_a_commit_the_retired_chart_can_be_read_at(report_text) -> None:
    """Decision 7's pin, checked as a pin rather than a string that looks like one, and the
    disagreement published with its direction; a pin nobody can fetch is a citation."""
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
    """Three buckets and a total a reader checks against a file this phase did not write.

    **Five exclusion reasons rather than two, each with its own row**, so a reader can tell which
    nodes come back by which route: 29,104 when GTOpen prices a multiway pot properly, 15 when
    the realization fit gains a four-bet-pot cell, 15 more when that fix reaches the jam-facing
    nodes after those, 15 more again at the three-bet-facing nodes before them, and 4,814 outside
    the rule for good. The three fifteens are the same size, so a report filing them under one
    code adds up and cannot say which nodes a later fix recovered."""
    body = section(report_text, "census")
    committed = re.search(r"^\s*committed\s+(\d+)\s*$", body, re.MULTILINE)
    excluded = re.findall(r"^\s*excluded\s+(derivation:[a-z-]+)\s+(\d+)\s*$", body, re.MULTILINE)
    unwritable = re.findall(r"^\s*inexpressible\s+(derivation:[a-z-]+)\s+(\d+)$", body, re.M)
    counts = {code: int(count) for code, count in excluded}

    assert committed is not None and excluded and unwritable, body
    assert set(counts) == set(lookup.DERIVATION_EXCLUSION_CODES)
    assert FOUR_BET_POT_CODE in counts, "the four-bet-pot reason has no row of its own"
    assert JAM_INHERITS_CODE in counts, "the inherited-node reason has no row of its own"
    assert THREE_BET_BRANCH_CODE in counts, "the three-bet-branch reason has no row of its own"
    assert counts[FOUR_BET_POT_CODE] == FOUR_BET_POT_NODES
    assert counts[JAM_INHERITS_CODE] == JAM_INHERITS_NODES
    assert counts[THREE_BET_BRANCH_CODE] == THREE_BET_BRANCH_NODES
    assert counts[lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY] == MULTIWAY_NODES
    assert counts[lookup.DERIVATION_OUTSIDE_SELECTION_RULE] == OUTSIDE_RULE_NODES
    assert len(counts) == 5, "a census with fewer rows cannot say which fix recovers what"
    assert {code for code, _ in unwritable} <= set(lookup.DERIVATION_INEXPRESSIBILITY_CODES)
    assert all(int(count) == 0 for _, count in unwritable), unwritable
    assert "four-bet" in body.lower(), "the census names no reason a reader could act on"
    assert "jam" in body.lower(), "the census does not say what became of the jam answers"
    assert "three-bet" in body.lower(), "the census does not name the three-bet withholding"
    assert int(committed.group(1)) == COMMITTED_SPOTS

    cards = sorted((ARTIFACT_DIR / "exports").glob("*.source.json"))
    assert len(cards) == 1, f"expected exactly one export source card, found {cards}"
    counted = list(excluded) + list(unwritable)
    total = int(committed.group(1)) + sum(int(count) for _, count in counted)
    card = json.loads(cards[0].read_text(encoding="utf-8"))
    assert total == card["node_counts"]["exported"] == EXPORTED_NODES


def test_one_cell_is_traced_from_an_export_node_to_the_row_it_became(report_text) -> None:
    """The trace is checked against the artifact, because a printed trace proves nothing. A
    reviewer who cannot read code follows this row to see a solved node become a chart cell, so
    weights, reach and arrival are read back out of the artifact. **Arrival is there because of
    what reach cannot say**: reach is "can hero hold this hand", arrival "is this line played",
    and over the committed 6 reach is a flat 10,000 while arrival still varies."""
    body = section(report_text, "trace")
    traced = (
        r"^\s*artifact row\s+(t6/\S+)\s+([2-9TJQKA]{2}[so]?)\s+(.+?)\s+reach\s+(\d+) bp"
        r"\s+arrival\s+(\d+) ppb$"
    )
    row = re.search(traced, body, re.MULTILINE)

    assert re.search(r"^\s*export node\s+\S+", body, re.M), "no export node named on the trace"
    assert row is not None, "the trace does not print the artifact row in the pinned form"

    artifacts = import_preflop_artifacts(ARTIFACT_DIR)
    named = [art.source.name for art in artifacts]
    assert len(artifacts) == 1, f"the report's figures are about a mixture of charts: {named}"
    artifact = artifacts[0]
    spot_key, hand_class, printed, reach, arrival = row.groups()
    weights = [classes for spot, classes in artifact.action_weights if spot == spot_key]
    cells = {text: dict(actions) for classes in weights for text, actions in classes}
    assert hand_class in cells, f"{spot_key} carries no {hand_class} in the committed artifact"
    for action, weight in re.findall(r"([a-z]+)=([0-9.]+)", printed):
        assert cells[hand_class].get(action) == pytest.approx(float(weight), abs=0.0001), action
    assert artifact.reach_bp_for(spot_key, hand_class) == int(reach)
    assert dict(artifact.arrival_ppb)[spot_key] == int(arrival)


def test_the_dominance_section_separates_what_gates_from_what_only_informs(
    generator, report_text
) -> None:
    """Two families of figures under one heading, and the report has to say which is which.

    **Ruled by Taylor on 2026-09-01, twice.** The per-cell measure over spot partitions gates;
    the group-order ladders are published for a human and gate nothing, having returned a
    different verdict on every committed set - fail over 51, pass over 36, mixed over 21, blind
    over 6 - so their verdict tracks set composition rather than the hand index. That restores
    Taylor's 2026-08-26 ruling that no group ORDER is gated. Both are still printed.

    **The gate has two counterfactual arms and each owes a column.** The suit swap reads each
    suited hand off its offsuit twin and catches a transposed hand index; it cannot catch a rank
    permutation, a chart with every rank reversed mapping pairs to pairs and twins to twins and
    scoring identically to a correct one. The rank arm reads each cell off its rank-reversed
    class, counted over cells rather than spots because every rank-sensitive relation flags all
    six spots under both mappings. So five gated rows must discriminate strictly on both arms,
    ladder rows prefixed `group` are required present and bounded but never compared, and a
    sentence says which family gates. **Each counterfactual names itself in its own column**,
    this repo having three "transposed" readings and a stage-4 reimplementation that swapped two
    of them reproducing neither family's counts."""
    body = section(report_text, "dominance")
    counts = [int(value) for value in re.findall(r"violations\s+(\d+)", body)]
    gated = re.findall(GATED_ROW, body, re.M)
    ladders = re.findall(LADDER_ROW, body, re.M)
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert len(counts) == 2, "the report publishes a violation count for each of the two relations"
    assert re.search(rf"{generator.MONOTONICITY_TOLERANCE_PCT}\s*(?:percentage )?point", body)
    assert "adjacent" in body.lower()

    assert gated, "the report publishes no per-cell discrimination against either counterfactual"
    assert {label.strip() for label, *_ in gated} == discrimination_partitions(artifact)
    for label, swap_solved, transposed, rank_solved, permuted in gated:
        assert int(swap_solved) < int(transposed), ("suit swap", label, swap_solved, transposed)
        assert int(rank_solved) < int(permuted), ("rank reversal", label, rank_solved, permuted)

    assert len(ladders) == GROUP_LADDERS, ladders
    assert len({label.strip() for label, _, _ in ladders}) == GROUP_LADDERS
    for label, solved, transposed in ladders:
        # Present and printable, never compared: a tie here is the ruled outcome over 6.
        assert 0 <= int(solved) <= COMMITTED_SPOTS, (label, solved)
        assert 0 <= int(transposed) <= COMMITTED_SPOTS, (label, transposed)

    assert re.search(r"gates|gated", body, re.IGNORECASE), "the section says which family gates"
    assert re.search(r"group[^\n]*(?:gates? nothing|not gated|published only)", body, re.I), (
        "the section does not say the group ladders gate nothing, so a reader cannot tell a"
        " published tie from a failure"
    )
    if any(counts):
        assert "ships as solved" in body.lower() or "considered answer" in body.lower()


def test_the_report_publishes_the_flat_frequency_at_every_committed_spot(report_text) -> None:
    """Decision 24, and the reason it is a report requirement rather than a backlog line.

    **The three spots this finding was first stated on are ones the chart REFUSES, and that
    correction is Taylor's of 2026-09-01.** The cutoff facing a lojack open continues 7.35
    percent and flats 0.69, the button facing a cutoff open 8.63 and 1.65, the small blind 10.04
    and 4.54 - but at all three five players are still live once the folds in front are counted,
    so decision 1's second clause refuses them. What is true of the committed set now covers all
    of it: five of the six spots are the big blind facing an open, and the big blind over-folds -
    25.70 percent continuing with a 19.63 flat against a lojack open, rising to 48.39 and 20.30
    against the small blind, where six-max at 100bb rake-free wants nearer 40. Phase 16 is the
    exit. **The acceptance has to be visible where it is signed off**, so every spot gets a row;
    only the small blind's open has no call, so exactly one row may read a flat of zero."""
    body = section(report_text, "flats")
    rows = re.findall(
        r"^\s*(t6/\S+)\s+continues\s+(\d+\.\d+)\s+flats\s+(\d+\.\d+)\s*$", body, re.M
    )
    menus = spot_menus(import_preflop_artifacts(ARTIFACT_DIR)[0])
    published = {key: (float(cont), float(flat)) for key, cont, flat in rows}

    assert published, "the report publishes no flat frequency at all"
    assert set(published) == set(menus), sorted(set(published) ^ set(menus))
    for key, (continues, flats) in published.items():
        assert 0.0 <= flats <= continues <= 100.0, (key, continues, flats)
        assert (flats > 0.0) == ("call" in menus[key]), (key, flats, sorted(menus[key]))
    assert sum(1 for _, flats in published.values() if flats == 0.0) == 1
    assert "COMMITTED-SPOTS-NEVER-FLAT-A-RAISE" in body
    assert re.search(r"phase\s*16", body, re.IGNORECASE), "no exit named for the acceptance"


def test_the_withheld_jams_are_published_with_what_aces_do_at_each(report_text) -> None:
    """The canary that rejected the first cutover, published as excluded evidence.

    A range that jams 44 always and aces never is the defect decision 14 re-solved out, and the
    canary that caught it cannot run over what this phase commits: hero is offered a jam at none
    of the 6. So it is retained against the **export** and the report prints aces' jam weight at
    each of the fifteen withheld spots. The vacuity is asserted rather than assumed, R2's rule;
    the test does not skip, publishing the fifteen not being itself vacuous. The rows are that
    family and nothing else, which is why every key must carry exactly three raises - the
    three-bet-facing fifteen carry two, the jam-facing fifteen four."""
    body = section(report_text, "jams")
    rows = re.findall(r"^\s*(t6/\S+)\s+AA jams\s+(\d+\.\d+)\s*$", body, re.M)
    committed = spot_menus(import_preflop_artifacts(ARTIFACT_DIR)[0])
    faced = {key: key.split("/")[3].count(":raise@") for key, _ in rows}

    assert len(rows) == WITHHELD_FOUR_BET_SPOTS, rows
    assert len(set(faced)) == len(rows), "the same withheld spot is published twice"
    assert all(count == 3 for count in faced.values()), faced
    assert not set(faced) & set(committed), "a withheld spot is also in the committed chart"
    assert all(0.0 <= float(weight) <= 1.0 for _, weight in rows), rows
    assert re.search(r"vacuous", body, re.IGNORECASE), (
        "the section prints the jams without saying the canary cannot run over the committed set"
    )
    assert "export" in body.lower(), "the section does not say what the canary is retained on"


def test_the_two_orderings_hold_and_the_chart_is_printed_against_the_expectations(
    report_text,
) -> None:
    """Later position opens wider and the big blind defends more against a wider opener,
    recomputed from the published column rather than read off a sentence saying they hold; both
    survive any rake basis and any solver, and the opening column is the **export's**, the
    committed set holding one opening range. Each row says where its left-hand figure came from
    and only the small blind's can say `derived`, so a row claiming `derived` for the lojack is a
    chart built on the superseded predicate saying so in its own report."""
    body = section(report_text, "orderings")
    pattern = (
        r"^\s*(LJ|HJ|CO|BTN|SB)\s+opens\s+\(export\)\s+(\d+\.\d+)"
        r"\s+big blind defends\s+\(chart\)\s+(\d+\.\d+)$"
    )
    rows = {p: (float(o), float(d)) for p, o, d in re.findall(pattern, body, re.MULTILINE)}

    assert set(rows) == {"LJ", "HJ", "CO", "BTN", "SB"}
    opens = [rows[position][0] for position in ("LJ", "HJ", "CO", "BTN")]
    assert opens == sorted(opens), f"later position does not open wider: {opens}"
    # The defence ordering follows the opening frequencies wherever they land rather than a
    # fixed seat order, which is what keeps the widest-opening seat inside the check.
    ordered = sorted(rows, key=lambda position: rows[position][0])
    defence = [rows[position][1] for position in ordered]
    assert defence == sorted(defence), f"the big blind does not defend more against wider: {rows}"

    against = section(report_text, "expectations")
    shape = r"^\s*(LJ|HJ|CO|BTN|SB)\s+(derived|export)\s+(\d+\.\d+)\s+GTO Wizard\s+(\d+\.\d+)$"
    printed = re.findall(shape, against, re.MULTILINE)
    expected = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["open_frequency_pct"]

    assert {position for position, _, _, _ in printed} == set(expected)
    assert [position for position, source, _, _ in printed if source == "derived"] == ["SB"]
    for position, _, _, quoted in printed:
        assert float(quoted) == pytest.approx(expected[position], abs=0.005), position
    grades = r"gated by nothing|does not gate|not a threshold"
    assert re.search(grades, against), "the comparison must say it grades nothing"


def test_the_report_names_a_recomputable_number_and_fits_the_size_the_file_check_allows(
    report_text, generator
) -> None:
    """The packet says which number and how, so the report names one; the report bounds what the
    chart answers at all; and `reports/active/*.txt` is capped at 300 KB. An agreement rate on
    one table configuration is not a grade on preflop play, so the bounds are stated, and
    "heads-up only" is on that list because it is the ruled predicate as a bound."""
    body = section(report_text, "recomputable")
    number = re.search(r"^\s*the number\s+(\S.*?)\s*$", body, re.MULTILINE)
    origin = re.search(r"^\s*the file\s+(\S+)\s*$", body, re.MULTILINE)
    arithmetic = re.search(r"^\s*the arithmetic\s+(\S.*?)\s*$", body, re.MULTILINE)

    assert number is not None and origin is not None and arithmetic is not None, body
    assert re.search(r"\d", number.group(1)), "the named number is not a number"
    assert (REPO_ROOT / origin.group(1)).exists(), origin.group(1)

    bounded = section(report_text, "bounds").lower()
    for token in ("six-handed", "100", "symmetric", "no straddle", "no ante", "2.5", "heads-up"):
        assert token in bounded, f"the bounds section does not state {token!r}"

    assert generator.REPORT_OUTPUT.stat().st_size <= 300 * 1024
    assert report_text.endswith("\n")
