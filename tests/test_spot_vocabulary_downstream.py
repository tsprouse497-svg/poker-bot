"""Phase 12: what the widened spot key changes downstream of the key itself.

The companion to `tests/test_spot_vocabulary.py`, split from it when the pair went past
the 700-line cap. That file pins what a key can say; this one pins what the repo does
once it can say it: the price normaliser that answers an unsolved price from a solved
one, the query and the answer that have to carry a size and a substitution, the corpus
measurements the vocabulary moves, and the report a person reads. Both run under
`pytest_spot_vocabulary`.

The surface this file pins:

- `lookup.ChartHit.price_substitutions`: `(sequence index, asked, answered)` per
  substituted raise, empty when every price was exact.
- `contract.SeatAction(seat, action, amount=None)`: a raise carries its raise-to in
  chips, which is the unit the hand history already uses.
- `contract.StrategyDecision(action, amount, code, detail=())`: ordered pairs, the
  same shape `StrategyRefusal.detail` already has.
- `contract.DECISION_AUDIT_SCHEMA_VERSION == 3` (Phase 13 moved it again).
- `vocabulary_report.render_spot_vocabulary_report() -> str`.
"""

from __future__ import annotations

import pytest

from poker_training_bot.data_pipeline.comparison import compare_committed_sample
from poker_training_bot.data_pipeline.sample import load_committed_sample
from poker_training_bot.solver_artifacts import lookup as lookup_module
from poker_training_bot.solver_artifacts import schema as schema_module
from poker_training_bot.solver_artifacts.lookup import (
    MISS_UNREPRESENTABLE_SPOT,
    ChartHit,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.strategy import contract as contract_module
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR, PreflopChartStrategy

TABLE = 6
DEPTH = 100


def raise_to(position: str, size_bb: float) -> object:
    """A raise entry carrying its raise-to size, in big blinds."""
    return schema_module.PreflopAction(position, "raise", size_bb)


def call_by(position: str) -> object:
    return schema_module.PreflopAction(position, "call")


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_directory(ARTIFACT_DIR)


@pytest.fixture(scope="module")
def strategy() -> PreflopChartStrategy:
    return PreflopChartStrategy.from_repo()


@pytest.fixture(scope="module")
def comparison():
    return compare_committed_sample(load_committed_sample())


# --------------------------------------------------------------------------- #
# Normalising a price the tree does not hold
# --------------------------------------------------------------------------- #


def query_facing(hero: str, *entries: object, hand: str = "AKs") -> ChartQuery:
    return ChartQuery(
        table_size=TABLE,
        stack_depth_bb=DEPTH,
        hero_position=hero,
        action_sequence=tuple(entries),
        hand_class=hand,
    )


def test_a_cheap_open_is_answered_from_the_solved_cell(library) -> None:
    """Ruling 8, measured: 80.8 percent of the corpus faced 2.25 or less."""
    found = library.lookup(query_facing("BTN", raise_to("CO", 2.25)))
    assert isinstance(found, ChartHit)
    assert found.spot_key == "t6/d100/BTN/CO:raise@2.5"


def test_the_answer_says_which_price_it_was_asked_at(library) -> None:
    """Without this, an exact answer and a substituted one are indistinguishable and
    every later measurement silently mixes them."""
    found = library.lookup(query_facing("BTN", raise_to("CO", 2.25)))
    assert isinstance(found, ChartHit)
    assert found.price_substitutions == ((0, 2.25, 2.5),)


def test_an_exact_price_records_no_substitution(library) -> None:
    found = library.lookup(query_facing("BTN", raise_to("CO", 2.5)))
    assert isinstance(found, ChartHit)
    assert found.price_substitutions == ()


def test_a_three_bet_at_an_unsolved_price_is_answered_too(library) -> None:
    """Taylor ruled on 2026-08-20 that three-bets have to be accommodated.

    Of the 79 three-bet decisions in the corpus the chart holds a cell for, 72 faced a
    price the tree does not hold and 7 did not.
    """
    found = library.lookup(
        query_facing("LJ", raise_to("LJ", 2.5), raise_to("BTN", 6.25))
    )
    assert isinstance(found, ChartHit)
    assert found.spot_key == "t6/d100/LJ/LJ:raise@2.5,BTN:raise@8"
    assert found.price_substitutions == ((1, 6.25, 8.0),)


def test_both_prices_normalise_independently(library) -> None:
    """A cheap open and a cheap three-bet in the same sequence."""
    found = library.lookup(
        query_facing("LJ", raise_to("LJ", 2.25), raise_to("BTN", 6.25))
    )
    assert isinstance(found, ChartHit)
    assert found.spot_key == "t6/d100/LJ/LJ:raise@2.5,BTN:raise@8"
    assert found.price_substitutions == ((0, 2.25, 2.5), (1, 6.25, 8.0))


def test_the_solved_prices_come_from_the_loaded_keys_not_from_a_constant(library) -> None:
    """The small blind opens to 3.5 and everyone else to 2.5, so one constant is
    already wrong today rather than only after some future solve."""
    from_sb = library.lookup(query_facing("BB", raise_to("SB", 2.25)))
    from_lj = library.lookup(query_facing("BB", raise_to("LJ", 2.25)))
    assert isinstance(from_sb, ChartHit) and isinstance(from_lj, ChartHit)
    assert from_sb.spot_key == "t6/d100/BB/SB:raise@3.5"
    assert from_lj.spot_key == "t6/d100/BB/LJ:raise@2.5"


def test_normalising_a_price_is_not_finding_a_nearest_spot(library) -> None:
    """A squeeze is expressible and uncovered, and it still refuses at any price.
    This is the line between the ruled abstraction and heuristic guessing."""
    found = library.lookup(
        query_facing("BTN", raise_to("HJ", 2.5), raise_to("CO", 8.0))
    )
    assert not isinstance(found, ChartHit)
    assert found.code == lookup_module.MISS_SPOT_NOT_COVERED


def test_an_uncovered_table_size_still_refuses(library) -> None:
    found = library.lookup(
        ChartQuery(
            table_size=2,
            stack_depth_bb=DEPTH,
            hero_position="BTN",
            action_sequence=(),
            hand_class="AKs",
        )
    )
    assert not isinstance(found, ChartHit)
    assert found.code == lookup_module.MISS_NO_ARTIFACT_FOR_TABLE


def test_the_unrepresentable_code_survives_for_a_genuinely_illegal_sequence(library) -> None:
    """A code that disappears takes the distinction it drew with it. Second-orbit
    sequences are representable now; an out-of-turn one never will be."""
    found = library.lookup(
        query_facing("CO", raise_to("BTN", 2.5), raise_to("HJ", 8.0))
    )
    assert not isinstance(found, ChartHit)
    assert found.code == MISS_UNREPRESENTABLE_SPOT


# --------------------------------------------------------------------------- #
# What the query and the answer carry
# --------------------------------------------------------------------------- #


def test_a_recorded_raise_carries_its_raise_to_amount() -> None:
    """A size-aware key cannot be derived from a history that does not hold a size."""
    entry = contract_module.SeatAction(3, "raise", 225)
    assert entry.amount == 225


def test_a_recorded_raise_without_an_amount_is_rejected() -> None:
    with pytest.raises(ValueError):
        contract_module.SeatAction(3, "raise")


def test_a_recorded_fold_carries_no_amount() -> None:
    with pytest.raises(ValueError):
        contract_module.SeatAction(3, "fold", 225)


def test_a_decision_can_carry_structured_detail() -> None:
    """The same shape `StrategyRefusal.detail` already has, on the branch that answers
    rather than the branch that declines."""
    decision = contract_module.StrategyDecision(
        "call", None, "test", (("price_substitution_0", "2.25->2.5"),)
    )
    assert decision.detail == (("price_substitution_0", "2.25->2.5"),)


def test_a_decision_detail_name_cannot_repeat() -> None:
    with pytest.raises(ValueError):
        contract_module.StrategyDecision(
            "call", None, "test", (("price_substitution_0", "a"), ("price_substitution_0", "b"))
        )


def test_a_decision_with_nothing_to_add_carries_no_detail() -> None:
    assert contract_module.StrategyDecision("fold", None, "test").detail == ()


def test_the_decision_audit_schema_version_moved() -> None:
    """The payload keeps changing shape, and the version has to keep up or two shapes
    share one number, which is DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS.
    Phase 12 moved it to 2 for the raise-to amount; Phase 13 moves it to 3, because the
    payload gained per-seat states and renamed the bet-level key to `current_bet`."""
    assert contract_module.DECISION_AUDIT_SCHEMA_VERSION == 3


# --------------------------------------------------------------------------- #
# The committed corpus
# --------------------------------------------------------------------------- #


def test_no_corpus_decision_refuses_as_unrepresentable(comparison) -> None:
    """CORPUS-INEXPRESSIBLE-SPOTS closed. All 19 were a position acting twice."""
    unrepresentable = [
        row
        for row in comparison.rows
        if row.refusal is not None and row.refusal.code.endswith(MISS_UNREPRESENTABLE_SPOT)
    ]
    assert unrepresentable == []


def test_the_inventory_has_no_catch_all_row(comparison) -> None:
    """19 points, the largest single row of the real-hand inventory and the one nobody
    could act on, because a refusal with no spot key names no cell to fill."""
    catch_all = [
        entry
        for entry in comparison.refusal_inventory
        if entry.spot_key == "(no expressible spot)"
    ]
    assert catch_all == []


def test_every_inventory_row_names_a_spot_a_chart_phase_could_fill(comparison) -> None:
    for entry in comparison.refusal_inventory:
        assert entry.spot_key.startswith("t6/d100/")


def test_the_second_orbit_rows_arrive_as_uncovered_rather_than_inexpressible(
    comparison,
) -> None:
    """The same 19 decision points, now naming four-bet-or-beyond keys. They are not
    answered: this phase adds no coverage, and that is CHART-COVERAGE-EXPANSION at
    proposed phase 14."""
    second_orbit = [
        entry
        for entry in comparison.refusal_inventory
        if any(
            entry.spot_key.count(f"{position}:") > 1
            for position in ("LJ", "HJ", "CO", "BTN", "SB", "BB")
        )
    ]
    assert sum(entry.count for entry in second_orbit) == 19


def test_the_corpus_keeps_its_sample(comparison) -> None:
    """A changed denominator means the replay changed, which this phase does not do."""
    assert comparison.hands_compared == 499
    assert len(comparison.rows) == 3048


def test_every_refusal_names_a_spot_key(comparison) -> None:
    """271 of the 290 refusals carry a key at the branch point. The missing 19 are the
    catch-all, and a refusal with no key names no cell anybody could fill."""
    keyless = [row for row in comparison.rows if row.refusal is not None and not row.spot_key]
    assert keyless == []


def test_the_squeeze_refusals_are_untouched(comparison) -> None:
    """The falsifiable form of what the three-bet ruling does *not* buy.

    132 refusals face a two-raise sequence in which every position acts once, and 125 of
    those are a squeeze or a cold four-bet: expressible today, uncovered today, and
    uncovered after this phase. Normalising a price is not finding a nearest spot, so
    this count must not move.

    Repeated-position sequences are excluded because this phase grows that population on
    purpose: as authored, the filter also caught the one limped second-orbit decision in
    the sample, which had no key at the branch point and so was invisible to a filter
    requiring one. Counting it would make a guard against nearest-spot matching fail for
    the second orbit finally having a key, which is the opposite of what it guards.
    """
    positions = ("LJ", "HJ", "CO", "BTN", "SB", "BB")
    two_raise = [
        row
        for row in comparison.rows
        if row.refusal is not None
        and row.spot_key
        and row.spot_key.split("/")[-1].count(":raise") == 2
        and not any(row.spot_key.count(f"{position}:") > 1 for position in positions)
    ]
    assert len(two_raise) == 132


def test_the_refusal_total_did_not_fall(comparison) -> None:
    """This phase adds no chart coverage, so a drop is a finding to explain rather
    than a win to report. 290 is the count at the branch point."""
    refused = [row for row in comparison.rows if row.refusal is not None]
    assert len(refused) == 290


# --------------------------------------------------------------------------- #
# What the strategy puts on its answer
# --------------------------------------------------------------------------- #


def test_the_strategy_reports_a_substituted_price_on_its_decision(strategy) -> None:
    """The cheapest possible measurement of what ruling 8 costs in play, and it has to
    be on the answer or no report can split on it."""
    # Seats 0 and 1 folded, CO raised to 225, hero is the button. The three contributions
    # sum to the stated pot exactly, and every seat started on 10,000, so the table is
    # flat at 100bb and the spot reaches the chart rather than refusing on its shape.
    contributed = {2: 225, 4: 50, 5: 100}
    query = contract_module.StrategyQuery(
        hand_id="h1",
        street="preflop",
        seat=3,
        button_seat=3,
        hole_cards=("As", "Kd"),
        board=(),
        legal_actions=("fold", "call", "raise"),
        to_call=225,
        current_bet=225,
        min_raise_target=350,
        pot=375,
        seat_states=tuple(
            contract_module.SeatState(
                seat=seat,
                street_bet=contributed.get(seat, 0),
                committed_total=contributed.get(seat, 0),
                folded=seat in (0, 1),
                all_in=False,
            )
            for seat in range(6)
        ),
        stacks=((0, 10000), (1, 10000), (2, 9775), (3, 10000), (4, 9950), (5, 9900)),
        blinds=(50, 100),
        preflop_actions=(contract_module.SeatAction(2, "raise", 225),),
    )
    outcome = strategy.decide(query)
    assert isinstance(outcome, contract_module.StrategyDecision)
    assert outcome.detail == (("price_substitution_0", "2.25->2.5"),)


# --------------------------------------------------------------------------- #
# The report a person reads
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def report() -> str:
    from poker_training_bot.solver_artifacts import vocabulary_report

    return vocabulary_report.render_spot_vocabulary_report()


def test_the_report_shows_a_key_before_and_after(report) -> None:
    assert "t6/d100/BTN/CO:raise" in report
    assert "t6/d100/BTN/CO:raise@2.5" in report


def test_the_report_shows_a_four_bet_key_that_could_not_be_written_before(report) -> None:
    assert "LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5" in report


def test_the_report_publishes_the_measured_spot_counts(report) -> None:
    """The roadmap's 1,691 and 848 do not reproduce; enumerating spot_key gives these.
    ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE owns correcting the documents."""
    assert "1,949" in report
    assert "977" in report


def test_the_report_carries_the_price_substitution_census(report) -> None:
    """Split by whether the substituted raise was the open or a later one, so the cost
    of ruling 8 stays separable from the cost of extending it past the open.

    72 is the number the extension buys: three-bet decisions the chart can answer that
    faced a price the tree does not hold.
    """
    lowered = report.lower()
    assert "substitution" in lowered
    assert "open" in lowered
    assert "72" in report


def test_the_report_states_that_the_refusal_total_did_not_fall(report) -> None:
    assert "290" in report


def test_the_report_restates_the_phase_eleven_numbers_with_a_cause(report) -> None:
    """Every number the Phase 07 and Phase 08 packets quote, labelled as unchanged,
    moved by Phase 11, or moved by this phase's vocabulary."""
    lowered = report.lower()
    assert "phase 11" in lowered
    assert "unchanged" in lowered
    assert "3,048" in report or "3048" in report
