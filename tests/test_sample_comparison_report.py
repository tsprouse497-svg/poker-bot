"""Phase 08: what the two committed reports are allowed to put in front of a reader.

Split from the measurement tests because these check a different kind of claim. A
number being right and a reader being led to the right conclusion by it are separate
properties, and this phase has already been wrong about the second while right about
the first more than once.
"""

from __future__ import annotations

import pytest

from poker_training_bot.data_pipeline.comparison import (
    AGREE,
    DISAGREE,
    compare_committed_sample,
)
from poker_training_bot.data_pipeline.comparison_report import (
    render_comparison_report,
    render_refusal_inventory,
)
from poker_training_bot.data_pipeline.sample import load_committed_sample


@pytest.fixture(scope="module")
def sample():
    return load_committed_sample()


@pytest.fixture(scope="module")
def comparison(sample):
    return compare_committed_sample(sample)


def test_the_sample_was_played_at_a_price_the_chart_was_not_solved_for(comparison) -> None:
    """The caveat that turns out to be most of the finding, measured rather than said.

    The committed solve opens to 2.5 big blinds. These players mostly opened smaller,
    and a cheaper price is a correct reason to continue with more hands, so a chart
    answering at 2.5 is answering a more expensive question than the one it was asked.
    """
    solved = dict(comparison.solved_open_bb)["LJ"]
    sizes = comparison.open_sizes_bb()
    below = [size for size in sizes if size < solved]

    assert solved == 2.5
    assert len(below) > len(sizes) / 2

    cheap = comparison.agreement_within("humans", action="call", price_band="at or under 2.25bb")
    dear = comparison.agreement_within("humans", action="call", price_band="over 2.50bb")
    assert cheap.denominator > 50
    assert dear.denominator > 10
    assert cheap.percent < dear.percent - 10.0


def test_the_report_says_the_chart_is_raked_and_the_corpus_is_not(comparison) -> None:
    """The single largest explanation of the blind-defence gap, stated before it.

    A raked solution defends the blinds more tightly than a rake-free one. These hands
    carry no rake, so a chart that folds the big blind more than these players did is
    behaving as designed. A reader who does not know that reads the gap as a defect.
    """
    text = render_comparison_report(comparison)
    preamble = text.split("## Coverage")[0].lower()

    assert "rake" in preamble
    assert "rake" in comparison.chart_source.lower()


def test_the_sampled_action_match_rate_is_reported_as_judgment_call_5_ruled(
    comparison,
) -> None:
    """Ruled to be reported alongside, and it was not, for two maintenance tasks.

    It is the lesser number - on a mixed cell a single draw against a single observed
    action mostly measures the seed - but the ruling said both would be there, and the
    fallback the ruling offered a disagreeing reader was that both are in the report.
    """
    text = render_comparison_report(comparison)
    assert "sampled-action match rate" in text.lower()

    for population in comparison.populations:
        sampled = comparison.sampled_action_match(population)
        nonzero_weight = comparison.agreement(population)
        drawn = sum(
            1
            for row in comparison.rows
            if row.population == population
            and row.verdict in {AGREE, DISAGREE}
            and row.sampled_action is not None
        )

        # Every scored decision in this sample does draw, so the two denominators are
        # equal here. The guard still matters: a spot whose weights are readable but
        # whose raise size is not committed would give no draw, and counting it as a
        # miss would blame the collapse rule for a missing sizing.
        assert sampled.denominator == drawn == nonzero_weight.denominator

        # And it must be the stricter measurement, not a second printing of the looser
        # one. A mixed cell that draws the other way agrees and does not match.
        assert sampled.percent < nonzero_weight.percent - 3.0


def test_the_comparison_is_a_pure_function_of_the_committed_sample(sample) -> None:
    first = compare_committed_sample(sample)
    second = compare_committed_sample(sample)

    assert render_comparison_report(first) == render_comparison_report(second)
    assert render_refusal_inventory(first) == render_refusal_inventory(second)


def test_the_report_states_its_preflop_boundary_before_any_number(comparison) -> None:
    text = render_comparison_report(comparison)
    first_digit = next(
        (index for index, character in enumerate(text) if character.isdigit()), len(text)
    )

    assert "preflop" in text[:first_digit].lower()


def test_the_report_says_a_disagreement_is_not_proof_the_chart_is_wrong(comparison) -> None:
    text = render_comparison_report(comparison).lower()

    assert "disagreement" in text
    assert "does not" in text or "not establish" in text
