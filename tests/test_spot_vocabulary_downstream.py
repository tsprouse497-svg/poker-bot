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


def solved_line(library, hero: str, *raisers: str) -> tuple:
    """`hero`'s line where each seat raises at the price the chart solved there.

    Phase 14 replaced the chart under this file, and it shares no three-bet price with the
    one these tests were authored against. Each raising point offers the named raise and
    the all-in decision 6 prices at hero's whole stack, so the named raise is the smaller.
    """
    sequence: list = []
    for raiser in raisers:
        prices = library.solved_prices_bb(TABLE, DEPTH, hero, tuple(sequence), raiser)
        assert prices, (hero, raiser, tuple(sequence))
        sequence.append(schema_module.PreflopAction(raiser, "raise", min(prices)))
    return tuple(sequence)


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

    Of the 79 three-bet decisions in the corpus the phase 12 chart held a cell for, 72
    faced a price the tree does not hold and 7 did not. The rake-free solve three-bets to
    a different price and holds far more of these cells, so the count moves and the
    property does not.
    """
    solved = solved_line(library, "LJ", "LJ", "BTN")
    three_bet = solved[1].size_bb
    cheap = round(three_bet * 0.78, 2)

    found = library.lookup(query_facing("LJ", solved[0], raise_to("BTN", cheap)))

    assert isinstance(found, ChartHit)
    assert found.spot_key == schema_module.spot_key(TABLE, DEPTH, "LJ", solved)
    assert found.price_substitutions == ((1, cheap, three_bet),)


def test_both_prices_normalise_independently(library) -> None:
    """A cheap open and a cheap three-bet in the same sequence."""
    solved = solved_line(library, "LJ", "LJ", "BTN")
    open_to, three_bet = solved[0].size_bb, solved[1].size_bb
    cheap_open = round(open_to * 0.9, 2)
    cheap_three_bet = round(three_bet * 0.78, 2)

    found = library.lookup(
        query_facing("LJ", raise_to("LJ", cheap_open), raise_to("BTN", cheap_three_bet))
    )

    assert isinstance(found, ChartHit)
    assert found.spot_key == schema_module.spot_key(TABLE, DEPTH, "LJ", solved)
    assert found.price_substitutions == (
        (0, cheap_open, open_to),
        (1, cheap_three_bet, three_bet),
    )


def test_the_solved_prices_come_from_the_loaded_keys_not_from_a_constant(library) -> None:
    """Authored when the tree carried two opening prices - the small blind opened to 3.5
    and everyone else to 2.5 - so a single constant was already wrong.

    The rake-free solve opens everyone to 2.5, so that instance is gone. The claim is not:
    the candidate set still varies with where in the tree the raise sits, and it varies
    further now, because the same sequence carries an opening price, a three-bet price and
    a four-bet price that no one constant can serve. A normaliser reading a constant
    answers a four-bet at the opening price and hits a cell nobody solved.
    """
    ladder = solved_line(library, "BB", "CO", "BB", "CO")
    prices = [entry.size_bb for entry in ladder]

    assert len(set(prices)) == 3
    assert prices[0] < prices[1] < prices[2]
    for index, entry in enumerate(ladder):
        offered = library.solved_prices_bb(TABLE, DEPTH, "BB", ladder[:index], entry.position)

        assert entry.size_bb in offered, index
        assert prices[0] not in offered or index == 0, index


def test_normalising_a_price_is_not_finding_a_nearest_spot(library) -> None:
    """The line between the ruled abstraction and heuristic guessing.

    Authored on a squeeze, which the phase 12 chart did not hold. The rake-free solve does
    hold squeezes, so the instance moves to the one spot that is structurally uncovered
    rather than merely under the reach floor: nobody limps in a `limp: false` tree, and
    the neighbouring sequence a nearest-spot matcher would reach for - the small blind
    raising instead of calling - is covered at full reach.
    """
    found = library.lookup(query_facing("BB", call_by("SB")))

    assert not isinstance(found, ChartHit)
    assert found.code == lookup_module.MISS_SPOT_NOT_COVERED
    neighbour = library.lookup(query_facing("BB", *solved_line(library, "BB", "SB")))

    assert isinstance(neighbour, ChartHit)


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


def test_the_second_orbit_rows_are_no_longer_all_refused(comparison) -> None:
    """Phase 12 gave these 19 decision points a key and left them uncovered, because it
    added no coverage. That was `CHART-COVERAGE-EXPANSION` at proposed phase 14, and this
    is phase 14: the solved tree holds four-bets and the reach floor keeps the ones real
    players reach, so the count has to fall. Not asserted to reach zero, because a
    four-bet line under the reach floor is still an honest refusal."""
    second_orbit = [
        entry
        for entry in comparison.refusal_inventory
        if any(
            entry.spot_key.count(f"{position}:") > 1
            for position in ("LJ", "HJ", "CO", "BTN", "SB", "BB")
        )
    ]
    assert sum(entry.count for entry in second_orbit) < 19


def test_the_corpus_keeps_its_sample(comparison) -> None:
    """A changed denominator means the replay changed, which this phase does not do."""
    assert comparison.hands_compared == 499
    assert len(comparison.rows) == 3048


def test_every_refusal_names_a_spot_key(comparison) -> None:
    """271 of the 290 refusals carry a key at the branch point. The missing 19 are the
    catch-all, and a refusal with no key names no cell anybody could fill."""
    keyless = [row for row in comparison.rows if row.refusal is not None and not row.spot_key]
    assert keyless == []


def test_the_squeeze_refusals_are_answered_rather_than_normalised_away(comparison) -> None:
    """Phase 12 pinned this at 132 as the falsifiable form of what price normalisation
    does *not* buy: 125 of them were a squeeze or a cold four-bet, expressible and
    uncovered, and normalising a price is not finding a nearest spot, so the count could
    not move.

    Phase 14 moves it by covering the cells rather than by matching a neighbour, which is
    the one way it was allowed to move. Cold calls are in the solved tree - only limps
    left it - so the squeeze family is answered now. The guard against nearest-spot
    matching moves to `test_normalising_a_price_is_not_finding_a_nearest_spot`, where the
    uncovered spot is structural rather than a count.
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
    assert len(two_raise) < 132


def test_the_refusal_total_fell_and_the_limped_points_are_what_is_left(comparison) -> None:
    """Phase 12 pinned 290 because it added no coverage and a drop would have been a
    finding. Phase 14 adds thousands of spots, so the number has to fall, and the
    direction is the assertion rather than the value, which the report publishes by
    reason code.

    What must not fall to zero is the limped population. Every decision whose first
    recorded action is a call arrives at a spot the solved tree does not hold at any reach
    floor, and `CHART-CANNOT-ANSWER-A-LIMPED-POT` is restated on that count rather than
    closed. Both halves are asserted, because the drop alone would also be satisfied by a
    chart that quietly answered a limp from a neighbouring cell.
    """
    refused = [row for row in comparison.rows if row.refusal is not None]
    limped = [
        row
        for row in refused
        if row.spot_key and row.spot_key.split("/")[-1].split(",")[0].endswith(":call")
    ]

    assert len(refused) < 290
    assert limped


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


def report_figure(report: str, label: str) -> int:
    """The number the report prints on the line beginning `label`."""
    line = next(row for row in report.splitlines() if row.strip().startswith(label))
    return int(line.split()[-1])


def test_the_report_carries_the_price_substitution_census(report, comparison) -> None:
    """Split by whether the substituted raise was the open or a later one, so the cost
    of ruling 8 stays separable from the cost of extending it past the open.

    Phase 12 pinned 72 here, the three-bet decisions the extension buys, and the cutover
    moves that count. Recomputed from the rows rather than loosened to a keyword: a
    substring test on "substitution" and "open" cannot fail while the section heading
    exists, so it would have read as coverage of a split nothing checked. The split is
    recomputable because `ComparisonRow.price_substitutions` carries the raise index on
    every row, and index 0 is the open by construction.
    """
    answered = [row for row in comparison.rows if row.refusal is None]
    moved = [row.price_substitutions for row in answered if row.price_substitutions]
    opener = sum(1 for subs in moved if any(index == 0 for index, _, _ in subs))
    later = sum(1 for subs in moved if any(index > 0 for index, _, _ in subs))
    both = sum(
        1
        for subs in moved
        if any(i == 0 for i, _, _ in subs) and any(i > 0 for i, _, _ in subs)
    )

    assert opener and later, "one side of the split is empty, so it separates nothing"
    assert report_figure(report, "the opener's price was moved") == opener
    assert report_figure(report, "a later raise's price was moved") == later
    assert report_figure(report, "both, counted once in each line above") == both


def test_the_report_states_the_refusal_total_it_measured(report, comparison) -> None:
    """Phase 12 asserted 290, the count at its branch point. The cutover moves it, so
    what is pinned is that the report prints the total this run measured rather than one
    carried over from the phase before it."""
    refused = sum(1 for row in comparison.rows if row.refusal is not None)

    assert f"{refused:,}" in report or str(refused) in report


def test_the_report_restates_the_phase_eleven_numbers_with_a_cause(report) -> None:
    """Every number the Phase 07 and Phase 08 packets quote, labelled as unchanged,
    moved by Phase 11, or moved by this phase's vocabulary."""
    lowered = report.lower()
    assert "phase 11" in lowered
    assert "unchanged" in lowered
    assert "3,048" in report or "3048" in report
