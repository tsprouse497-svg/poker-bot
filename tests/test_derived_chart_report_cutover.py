"""Phase 14: the cutover the report publishes, and what none of it establishes.

Split off `tests/test_derived_chart_report.py` at the 700-line cap. That file keeps the whole
module-scope interface and this file reaches it as an attribute on it, so no count is owned twice
and no constant is copied.

Owned here: the ledger balancing against the chart this phase retires, whose figures are read back
out of git at the pin the report names; the refusal inventory by reason with the old-versus-new
disagreement and its two directions; the corpus rates republished with their pre-registration,
their price and what the measurement cannot separate; and the one number a reader recomputes by
hand, with the bounds on everything else.
"""

from __future__ import annotations

import json
import re

import pytest
import test_chart_derivation as derivation_tests
import test_derived_chart_report as report

from poker_training_bot.solver_artifacts import lookup


@pytest.fixture(scope="module")
def generator():
    return report.load_generator()


@pytest.fixture(scope="module")
def report_text(generator) -> str:
    return report.load_report_text(generator)


@pytest.fixture(scope="module")
def artifact():
    return report.load_artifact()


def test_the_cutover_ledger_balances_against_the_chart_it_retires(report_text, artifact) -> None:
    """A ledger that does not balance is a coverage claim nobody checked.

    The retired chart is read out of git at a pinned commit rather than kept as a second copy
    under `data/artifacts/preflop/`, which is the arrangement that makes a reader ask which chart
    the bot plays - the confusion this phase exists to end. So the pin is fetched here and the
    retired figures are recomputed from the bytes at it: 86 spots, 36 carrying a sizing entry, and
    every one of those 36 priced at a jam the ruled config cannot produce.

    Both sides have to close. The retired chart's spots are the ones carried over plus the ones
    the new rules refuse; the derived chart's are the ones carried over plus the ones gained.
    """
    body = report.section(report_text, "ledger")
    pin = re.search(r"^\s*retired chart\s+(\S+)\s+at\s+([0-9a-f]{7,40})\s*$", body, re.MULTILINE)
    figures = {
        name: int(value)
        for name, value in re.findall(
            r"^\s*(retired spots|derived spots|carried over|refused|gained|sizing entries|"
            r"priced at a jam)\s+(\d+)\s*$",
            body,
            re.MULTILINE,
        )
    }

    assert pin is not None, "the ledger names no commit the retired chart can be read at"
    reachable = report.git("cat-file", "-e", f"{pin.group(2)}:{pin.group(1)}")
    assert reachable.returncode == 0, pin.groups()
    assert set(figures) >= {
        "retired spots",
        "derived spots",
        "carried over",
        "refused",
        "gained",
        "sizing entries",
        "priced at a jam",
    }, sorted(figures)

    retired = json.loads(report.git("show", f"{pin.group(2)}:{pin.group(1)}").stdout)
    sizings = json.loads(
        report.git("show", f"{pin.group(2)}:{report.RETIRED_SIZINGS}").stdout
    )["raise_to_bb"]
    jammed = sum(
        1
        for cells in sizings.values()
        if any(price["to_bb"] == 100.0 for entries in cells.values() for price in entries)
    )

    assert figures["retired spots"] == len(retired["spots"]) == report.RETIRED_SPOTS
    assert figures["sizing entries"] == len(sizings) == report.RETIRED_SIZING_ENTRIES
    assert figures["priced at a jam"] == jammed == report.RETIRED_SIZING_ENTRIES
    assert figures["derived spots"] == len(artifact.spots) == derivation_tests.COMMITTED_NODES
    assert figures["carried over"] + figures["refused"] == figures["retired spots"], (
        f"the retired side of the ledger does not balance: {figures}"
    )
    assert figures["carried over"] + figures["gained"] == figures["derived spots"], (
        f"the derived side of the ledger does not balance: {figures}"
    )
    carried = {spot["spot_id"] for spot in retired["spots"]} & {s.spot_id for s in artifact.spots}
    assert figures["carried over"] == len(carried), (figures["carried over"], len(carried))


def test_the_refusal_inventory_moves_by_reason_and_the_disagreement_carries_its_directions(
    report_text,
) -> None:
    """One total hides the finding, so every runtime miss code gets a row, a zero included.

    A reason that stopped happening is a result. The rows have to add to the refusals the corpus
    rates publish, and no row may name a code outside the closed vocabulary - the runtime miss
    codes are a different vocabulary from the derivation reasons in the census, and folding the
    two together is how an excluded node gets filed as a lookup failure.

    The disagreement count sits beside it with its direction rows, because a comparison that
    quietly became trivial arrives as a small consistent number rather than as an error.
    """
    body = report.section(report_text, "refusals")
    after = {code: int(now) for code, _, now in report.REFUSAL_ROW.findall(body)}
    before = {code: int(was) for code, was, _ in report.REFUSAL_ROW.findall(body)}
    published = [
        row
        for row in report.rate_rows(report.section(report_text, "corpus"))
        if row[1] == "refused" and row[2] == "after"
    ]

    assert set(after) == set(before) == set(lookup.MISS_CODES), sorted(after)
    assert set(re.findall(r"lookup:[a-z-]+", report_text)) <= set(lookup.MISS_CODES)
    assert not re.findall(r"derivation:[a-z-]+", body), (
        "the runtime refusal inventory names a derivation reason, which is the other vocabulary"
    )
    assert published, "no refusal rate is published per population"
    assert sum(after.values()) == sum(row[3] for row in published)

    disagreement = report.section(report_text, "old_versus_new")
    shared = re.search(r"decisions both charts answer\s+(\d+)", disagreement)
    disagreed = re.search(r"disagreed\s+(\d+)", disagreement)
    directions = re.findall(
        r"^\s*(?:derived|retired) continues[^\n]*?(\d+)\s*$", disagreement, re.MULTILINE
    )

    assert shared is not None and disagreed is not None, disagreement
    assert int(shared.group(1)) > 0, "the two charts share no corpus decision"
    assert int(disagreed.group(1)) > 0, "a zero here is the same chart compared with itself"
    assert len(directions) == 2, "the disagreement is published without which way it went"
    assert sum(int(count) for count in directions) == int(disagreed.group(1))
    assert int(disagreed.group(1)) <= int(shared.group(1))


def test_the_corpus_measurement_is_republished_gating_nothing(report_text) -> None:
    """The closing measurement, its pre-registration, its price and its bounds - none of it gates.

    Decision 21 moved the corpus verdict to phase 17 and decision 9 voided its bands with it: they
    were a quarter to one times defence deltas computed on an export this phase no longer ships,
    and a pre-registration whose numbers were fixed against data that moved is not one. What
    travels is the **form** - per opener, a quarter to one times that opener's delta, written down
    before the numbers are seen - and phase 17 re-registers the arithmetic.

    So this report republishes rather than concludes, and it has to say so, because a rendered
    agreement rate with no label is read as a grade. The limped-decision-point count comes with
    its own definition for the same reason: the older figure appears in three committed documents
    under no stated rule at all.
    """
    corpus = report.section(report_text, "corpus")
    rows = report.rate_rows(corpus)
    wanted = {"agreement", "refused", "sampled-action match"}

    for population in report.POPULATIONS:
        for when in ("before", "after"):
            here = [row for row in rows if row[0] == population and row[2] == when]
            assert wanted <= {row[1] for row in here}, f"{population} {when}: {here}"
    for _, label, _, numerator, denominator, percent in rows:
        assert denominator > 0
        assert percent == pytest.approx(100.0 * numerator / denominator, abs=0.05), label
    assert re.search(r"gates? nothing|no verdict|phase\s*17", corpus, re.IGNORECASE), (
        "the corpus rates are published without saying the verdict is phase 17's"
    )

    prediction = report.section(report_text, "prediction")
    assert "PHASE_14_CHART_CUTOVER_DECISIONS.md" in prediction
    assert re.search(r"phase\s*17", prediction, re.IGNORECASE), (
        "the prediction is republished without saying which phase re-registers and reads it"
    )
    assert re.search(r"void|re-registered", prediction, re.IGNORECASE)
    assert re.search(r"quarter to one", prediction), "the band's ruled form is not republished"
    assert re.search(r"gates? nothing|no verdict|does not conclude", prediction, re.IGNORECASE)

    price = report.section(report_text, "price")
    assert re.findall(r"^\s*(\d+(?:\.\d+)?)bb\s+(\d+)\s+\((\d+(?:\.\d+)?)%\)\s*$", price, re.M), (
        "the price the corpus was played at is published without a distribution"
    )
    named = r"^\s*(?:the\s+)?(rake|price|realization)\b[^\n]*\b(separated|uncontrolled)\b"
    verdicts = dict(re.findall(named, report.section(report_text, "explanations"), re.MULTILINE))
    assert verdicts == {"rake": "separated", "price": "uncontrolled", "realization": "uncontrolled"}

    limped = re.search(
        r"^\s*decision points facing a limp\s+(\d+) inventory rows\s+(\d+) decision points\s*$",
        report.section(report_text, "refusals"),
        re.MULTILINE,
    )
    assert limped is not None, "the limped-decision-point count is not published"
    assert "first recorded action in the spot key is a call" in report_text
    assert "LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION" in report_text


def test_the_report_names_a_recomputable_number_and_states_what_the_chart_cannot_answer(
    report_text, generator
) -> None:
    """One figure a reviewer checks with a pencil, and the bounds on everything else.

    The packet owes a reader one number they can verify without running anything, so the report
    names it with the file it comes out of and the arithmetic that produces it - and the
    arithmetic is added up here, because a published sum nobody adds is the hand-typed count this
    phase has now been burned by four times.

    The bounds are beside it because an agreement rate on one table configuration is not a grade
    on preflop play, and because what this chart refuses is as much a property of it as what it
    answers: everything from the four-bet on, every pot multiway more than one time in ten, and
    the big blind's squeeze spots.
    """
    body = report.section(report_text, "recomputable")
    number = re.search(r"^\s*the number\s+(\S.*?)\s*$", body, re.MULTILINE)
    origin = re.search(r"^\s*the file\s+(\S+)\s*$", body, re.MULTILINE)
    arithmetic = re.search(r"^\s*the arithmetic\s+(\S.*?)\s*$", body, re.MULTILINE)

    assert number is not None and origin is not None and arithmetic is not None, body
    assert re.search(r"\d", number.group(1)), "the named number is not a number"
    assert (report.REPO_ROOT / origin.group(1)).exists(), origin.group(1)
    terms = [int(value) for value in re.findall(r"\d+", arithmetic.group(1).replace(",", ""))]
    assert len(terms) >= 5, f"the arithmetic has too few terms to check: {arithmetic.group(1)!r}"
    assert sum(terms[:-1]) == terms[-1], f"the published arithmetic does not add up: {terms}"

    bounded = report.section(report_text, "bounds").lower()
    for token in ("six-handed", "100", "no straddle", "no ante", "2.5", "four-bet", "multiway"):
        assert token in bounded, f"the bounds section does not state {token!r}"
    assert "98.59" in report_text, "the report never states the coverage a trainee gets"

    assert generator.REPORT_OUTPUT.stat().st_size <= 300 * 1024
    assert report_text.endswith("\n")
    for key in report.HEADINGS:
        assert report.section(report_text, key).strip(), f"the {key!r} section is empty"
