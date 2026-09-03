"""Phase 12: the spot vocabulary report a person reads.

The third file of the set, split from `tests/test_spot_vocabulary_downstream.py` at the
700-line cap the way that file was split from `tests/test_spot_vocabulary.py`. The first pins
what a key can say, the second what the repo does once it can say it, and this one pins what
the report states as a claim: the worked example, the measured spot counts, the price
substitution census, and the phase 11 restatement. All three run under
`pytest_spot_vocabulary`, so this path has to join that command's file list.

Read through `report_row` rather than by substring: every figure and key the report states as
a claim sits on an indented row, and `key in report` is satisfied by the key-mapping table.
"""

from __future__ import annotations

import pytest

from poker_training_bot.data_pipeline.comparison import compare_committed_sample
from poker_training_bot.data_pipeline.sample import load_committed_sample
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_directory(ARTIFACT_DIR)


@pytest.fixture(scope="module")
def comparison():
    return compare_committed_sample(load_committed_sample())


@pytest.fixture(scope="module")
def report() -> str:
    from poker_training_bot.solver_artifacts import vocabulary_report

    return vocabulary_report.render_spot_vocabulary_report()


REPORT_EXAMPLE_KEY = "t6/d100/BB/BTN:raise@2.5"
"""The spot `vocabulary_report._key_examples` works through, and the one thing a chart cutover
breaks outright: the module raises `VocabularyReportError` when the library stops declaring
it, which exits `generate_spot_vocabulary_report` non-zero - a completed phase's gate command.
The big blind facing a button open survives the cutover as one of the 249, and as one of the
five where hero still has fold, call and three-bet in front of him."""


def report_row(report: str, label: str, value_prefix: str = "") -> str:
    """What the report prints after `label`, on the one indented row beginning with it.

    Every figure and key the report states as a claim sits on an indented row, and the prose
    around them is flush left. Read from anywhere else a claim proves nothing: `key in report`
    is satisfied by the key-mapping table, a bare figure by any number of the same digits.
    `value_prefix` narrows the match where the label is an ordinary English word - "before"
    and "after" head the worked example's two rows, and stage 6 rewrites that section, so any
    indented prose row it adds beginning with either word would be a false red."""
    indented = [row.strip() for row in report.splitlines() if row.startswith(" ")]
    rows = [
        row
        for row in indented
        if row.startswith(label) and row[len(label) :].strip().startswith(value_prefix)
    ]

    assert len(rows) == 1, f"{label!r} begins {len(rows)} rows of the report, not one"
    return rows[0][len(label) :].strip()


def report_figure(report: str, label: str) -> int:
    """The single number the report prints on that row."""
    figures = report_row(report, label).split()

    assert len(figures) == 1, f"{label!r} carries {len(figures)} figures, not one"
    return int(figures[0].replace(",", ""))


def test_the_report_shows_a_key_before_and_after(report) -> None:
    """Read off the worked example's own two rows. As `REPORT_EXAMPLE_KEY in report` it passed
    while `_key_examples` still worked through the retired `t6/d100/BTN/CO:raise@2.5`, matching
    a key-mapping row instead. The two rows differ only by the `@2.5`, so both are asserted."""
    assert report_row(report, "after", "t6/d100/") == REPORT_EXAMPLE_KEY
    assert report_row(report, "before", "t6/d100/") == REPORT_EXAMPLE_KEY.split("@")[0]


def test_the_worked_example_is_a_spot_the_committed_chart_declares(library) -> None:
    """Deliberately without the `report` fixture: it is module-scoped, so a retired example
    raises at setup rather than failing here."""
    assert REPORT_EXAMPLE_KEY in set(library.spot_keys())


def test_the_report_shows_a_four_bet_key_that_could_not_be_written_before(
    report, library
) -> None:
    # The 8 and 21.5 are prices no committed spot holds, which is not a defect:
    # `_key_examples` builds this key and never checks it, so it demonstrates the grammar
    # rather than claiming coverage. The chart's own use of that grammar is what inverted:
    # nothing past two raises in is committed, so no committed key repeats a seat. Stated as
    # `all`, because the `any` it replaces would have kept passing off a single stray key.
    example = report_row(report, "could not be written before")

    assert example == "t6/d100/BTN/LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5"

    entries = [key.split("/")[-1].split(",") for key in library.spot_keys()]

    assert all(len({entry.split(":")[0] for entry in row}) == len(row) for row in entries)


def test_the_report_publishes_the_measured_spot_counts(report) -> None:
    """The roadmap's 1,691 and 848 do not reproduce; enumerating spot_key gives these, checked
    against `vocabulary_measures.expressible_spots` before they were pinned.
    ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE owns correcting the documents."""
    assert report_row(report, "v1, one orbit only").split() == ["1,949", "977"]


def test_the_report_carries_the_price_substitution_census(report, comparison) -> None:
    """Split by whether the substituted raise was the open or a later one, so the cost of
    ruling 8 stays separable from the cost of extending it past the open. Phase 12 pinned 72
    here, the three-bet decisions the extension buys, and the cutover moves that count.

    Recomputed from the rows rather than loosened to a keyword: a substring test on
    "substitution" and "open" cannot fail while the section heading exists.
    `ComparisonRow.price_substitutions` carries the raise index, and index 0 is the open."""
    answered = [row for row in comparison.rows if row.refusal is None]
    moved = [row.price_substitutions for row in answered if row.price_substitutions]
    opener = sum(1 for subs in moved if any(index == 0 for index, _, _ in subs))
    later = sum(1 for subs in moved if any(index > 0 for index, _, _ in subs))
    both = sum(
        1 for subs in moved if any(i == 0 for i, _, _ in subs) and any(i > 0 for i, _, _ in subs)
    )

    assert opener and later, "one side of the split is empty, so it separates nothing"
    assert report_figure(report, "the opener's price was moved") == opener
    assert report_figure(report, "a later raise's price was moved") == later
    assert report_figure(report, "both, counted once in each line above") == both


def test_the_report_states_the_refusal_total_it_measured(report, comparison) -> None:
    """Phase 12 asserted 290 at its branch point. The cutover moves the total in both directions
    - 249 answered nodes against 86 declared keys, and the four-bet family given up - and no
    ruling fixes where it lands, so the direction is not asserted here and the report is what says
    which way it moved. What is asserted is that the report states the number it measured:
    `str(refused) in report` passed off the restatement table's carried-over `refusals` row, so
    the figure is read off the claim's own row instead."""
    refused = sum(1 for row in comparison.rows if row.refusal is not None)

    assert report_figure(report, "total refusals over the committed sample") == refused


def test_the_report_restates_the_phase_eleven_numbers_with_a_cause(report, comparison) -> None:
    """Every number the Phase 07 and Phase 08 packets quote, labelled with a cause. Read off
    the restatement's own row, whose columns are the packet's figure, the branch point's and
    this run's. `"3048" in report` was satisfied by the header, which gives no cause."""
    row = report_row(report, "preflop decision points").split()

    assert "phase 11" in report.lower()
    assert row[:3] == [str(len(comparison.rows))] * 3
    assert "unchanged" in row
