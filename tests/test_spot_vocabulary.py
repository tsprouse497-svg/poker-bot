"""Phase 12: what a spot key can say, pinned from both sides.

Authored from `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md` before any
implementation exists. Almost every test here is red on the branch point, because the
size is a new field on `PreflopAction` and constructing one is the first thing most of
these tests do. That kind of red is weaker than an assertion failure - the assertion
never runs, which is `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` - so every expected
key string below was written out by hand against
`data/artifacts/preflop/sizings/six_max_nl25_100bb.json` rather than derived, and the
sections that can assert against today's code do.

The surface this file pins, so stage 6 has no freedom to drift from it:

- `schema.render_size_bb(value) -> str`: hundredths, trailing zeros stripped.
- `schema.PreflopAction(position, action, size_bb=None)`: a raise requires a positive
  size in big blinds, anything else requires None.
- `schema.spot_key(...)`: unchanged signature. Renders `POS:raise@<size>` and
  `POS:call`. Accepts a position acting more than once. Rejects a sequence whose
  raises do not strictly increase, whose sizes cannot be paid at the stated depth, or
  which needs a folded seat to act again.
- `lookup.ChartHit.price_substitutions`: `(sequence index, asked, answered)` per
  substituted raise, empty when every price was exact.
- `contract.SeatAction(seat, action, amount=None)`: a raise carries its raise-to in
  chips, which is the unit the hand history already uses.
- `contract.StrategyDecision(action, amount, code, detail=())`: ordered pairs, the
  same shape `StrategyRefusal.detail` already has.
- `contract.DECISION_AUDIT_SCHEMA_VERSION == 2`.
- `vocabulary_report.render_spot_vocabulary_report() -> str`.
"""

from __future__ import annotations

import subprocess
import sys

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
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

TABLE = 6
DEPTH = 100


def raise_to(position: str, size_bb: float) -> object:
    """A raise entry carrying its raise-to size, in big blinds."""
    return schema_module.PreflopAction(position, "raise", size_bb)


def call_by(position: str) -> object:
    return schema_module.PreflopAction(position, "call")


def key(hero: str, *entries: object) -> str:
    return schema_module.spot_key(TABLE, DEPTH, hero, tuple(entries))


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_directory(ARTIFACT_DIR)


@pytest.fixture(scope="module")
def sizing() -> PreflopSizingTable:
    return PreflopSizingTable.from_repo()


@pytest.fixture(scope="module")
def strategy() -> PreflopChartStrategy:
    return PreflopChartStrategy.from_repo()


@pytest.fixture(scope="module")
def comparison():
    return compare_committed_sample(load_committed_sample())


# --------------------------------------------------------------------------- #
# How a size renders
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("value", "rendered"),
    [
        (2.5, "2.5"),
        (8.0, "8"),
        (11.0, "11"),
        (13.5, "13.5"),
        (2.25, "2.25"),
        (21.5, "21.5"),
        (100.0, "100"),
        (0.5, "0.5"),
    ],
)
def test_a_size_renders_as_hundredths_with_trailing_zeros_stripped(value, rendered) -> None:
    """Taylor ruled this rendering on 2026-08-20 and it goes into committed data.

    Every case is a size the committed sizing table or the corpus actually holds, so
    none of them is a shape nobody will meet.
    """
    assert schema_module.render_size_bb(value) == rendered


def test_a_size_finer_than_a_hundredth_is_rejected_rather_than_rounded() -> None:
    """Rounding would move a size into a neighbouring cell without saying so."""
    with pytest.raises(ValueError):
        schema_module.render_size_bb(2.255)


def test_rendering_is_injective_over_the_committed_sizes(sizing) -> None:
    """Two sizes must never render the same, or two spots collapse into one key."""
    sizes = sorted(set(sizing.raise_to_bb.values()))
    rendered = [schema_module.render_size_bb(size) for size in sizes]
    assert len(set(rendered)) == len(sizes)


# --------------------------------------------------------------------------- #
# What a PreflopAction may carry
# --------------------------------------------------------------------------- #


def test_a_raise_entry_requires_a_size() -> None:
    """A sizeless raise is the v1 shape, and admitting it is admitting a wildcard."""
    with pytest.raises(ValueError):
        schema_module.PreflopAction("CO", "raise")


def test_a_raise_size_must_be_positive() -> None:
    with pytest.raises(ValueError):
        schema_module.PreflopAction("CO", "raise", 0.0)


def test_a_call_entry_must_not_carry_a_size() -> None:
    """A call pays a price the rest of the key already states."""
    with pytest.raises(ValueError):
        schema_module.PreflopAction("SB", "call", 2.5)


def test_a_call_entry_still_needs_no_size() -> None:
    assert call_by("SB").size_bb is None


# --------------------------------------------------------------------------- #
# The size in the key
# --------------------------------------------------------------------------- #


def test_facing_an_open_carries_the_openers_price() -> None:
    """The button facing a cutoff open, where the cutoff opened to the solved 2.5."""
    assert key("BTN", raise_to("CO", 2.5)) == "t6/d100/BTN/CO:raise@2.5"


def test_two_prices_are_two_spots() -> None:
    """The defect, in one line: these shared a cell in v1 and must not now."""
    cheap = key("BTN", raise_to("CO", 2.25))
    solved = key("BTN", raise_to("CO", 2.5))
    assert cheap != solved
    assert cheap == "t6/d100/BTN/CO:raise@2.25"


def test_the_opener_facing_a_three_bet_carries_both_prices() -> None:
    """LJ opened to 2.5, the button three-bet to 8, LJ is to act."""
    assert (
        key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 8.0))
        == "t6/d100/LJ/LJ:raise@2.5,BTN:raise@8"
    )


def test_a_small_blind_open_carries_its_own_larger_price() -> None:
    """The tree already has two opening prices: the small blind opens to 3.5."""
    assert key("BB", raise_to("SB", 3.5)) == "t6/d100/BB/SB:raise@3.5"


def test_a_limp_carries_no_price_and_reads_as_it_did() -> None:
    assert key("BB", call_by("SB")) == "t6/d100/BB/SB:call"


def test_a_cold_call_behind_an_open_carries_only_the_raisers_price() -> None:
    assert (
        key("BTN", raise_to("LJ", 2.5), call_by("CO")) == "t6/d100/BTN/LJ:raise@2.5,CO:call"
    )


def test_folded_to_hero_is_still_rfi_with_no_size_anywhere() -> None:
    assert key("BTN") == "t6/d100/BTN/rfi"


# --------------------------------------------------------------------------- #
# A position acting more than once
# --------------------------------------------------------------------------- #


def test_a_four_bet_spot_has_a_key() -> None:
    """The whole of SECOND-ORBIT-PREFLOP-SPOTS, in one assertion.

    LJ opens to 2.5, the button three-bets to 8, LJ four-bets to 21.5, and the button
    has to act. v1 rejects this outright: "v1 supports single-orbit spots only".
    """
    assert (
        key("BTN", raise_to("LJ", 2.5), raise_to("BTN", 8.0), raise_to("LJ", 21.5))
        == "t6/d100/BTN/LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5"
    )


def test_the_deepest_sequence_the_committed_corpus_reached_has_a_key() -> None:
    """Five raises, which is what makes a two-orbit cap a cap set below evidence.

    `HJ:raise,CO:raise,HJ:raise,CO:raise,HJ:raise` occurs in the committed sample and
    is the reason decision 4 chose legality and stack depth over an orbit count.
    """
    assert key(
        "CO",
        raise_to("HJ", 2.5),
        raise_to("CO", 8.0),
        raise_to("HJ", 21.5),
        raise_to("CO", 50.0),
        raise_to("HJ", 100.0),
    ) == "t6/d100/CO/HJ:raise@2.5,CO:raise@8,HJ:raise@21.5,CO:raise@50,HJ:raise@100"


def test_a_limped_pot_that_got_raised_twice_has_a_key() -> None:
    """The one limped second-orbit row in the corpus inventory."""
    assert (
        key("BB", call_by("SB"), raise_to("BB", 3.5), raise_to("SB", 10.0))
        == "t6/d100/BB/SB:call,BB:raise@3.5,SB:raise@10"
    )


def test_a_seat_the_action_already_passed_cannot_act_later() -> None:
    """The small blind folded to the three-bet, so it cannot four-bet afterwards.

    This is the case a test authored from the first draft of the contract would have
    got backwards: absence means folded only once the action has gone by.
    """
    with pytest.raises(ValueError):
        key(
            "BTN",
            raise_to("LJ", 2.5),
            raise_to("BTN", 8.0),
            raise_to("LJ", 21.5),
            raise_to("SB", 50.0),
        )


def test_a_seat_still_to_act_in_the_first_orbit_may_appear() -> None:
    """The over-application guard for the rule above, and it holds on the branch point.

    After LJ opens and the button three-bets, the blinds are absent because their turn
    has not come. v1 accepts this and so must v2.
    """
    assert key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 8.0)).endswith(
        "LJ:raise@2.5,BTN:raise@8"
    )


def test_hero_must_still_be_the_player_to_act_after_its_last_action() -> None:
    """A call behind hero does not give hero another turn, at any orbit depth."""
    with pytest.raises(ValueError):
        key("LJ", raise_to("LJ", 2.5), call_by("BTN"))


def test_a_seat_cannot_act_twice_in_a_row() -> None:
    """LJ opens, the button three-bets, and the button four-bets its own three-bet.

    The live set is LJ and the button, so the order alternates. Nothing about a second
    orbit lets one seat take two turns running.
    """
    with pytest.raises(ValueError):
        key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 8.0), raise_to("BTN", 21.5))


# --------------------------------------------------------------------------- #
# What the sizes in the key let the key check
# --------------------------------------------------------------------------- #


def test_a_raise_beyond_the_stated_depth_is_rejected() -> None:
    """A check the key could not perform before it carried sizes.

    It is also what stops an uncapped orbit count admitting a five-bet to 300bb in a
    100bb game.
    """
    with pytest.raises(ValueError):
        key("BTN", raise_to("CO", 100.5))


def test_a_raise_exactly_at_the_stated_depth_is_accepted() -> None:
    """All-in is a legal raise, so the bound is inclusive."""
    assert key("BTN", raise_to("CO", 100.0)) == "t6/d100/BTN/CO:raise@100"


def test_raises_must_strictly_increase_along_the_sequence() -> None:
    """A three-bet to less than the open it faces is not a three-bet."""
    with pytest.raises(ValueError):
        key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 2.5))


def test_a_short_all_in_re_raise_is_still_an_increase() -> None:
    """The guard for the rule above: a raise can be small without being flat."""
    assert key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 3.0)).endswith("BTN:raise@3")


# --------------------------------------------------------------------------- #
# The committed artifact, re-keyed
# --------------------------------------------------------------------------- #


def test_every_committed_raise_entry_carries_a_size(library) -> None:
    """Asserts against today's artifact, so this red is a real assertion failure."""
    sizeless = [
        spot_key_text
        for spot_key_text in library.spot_keys()
        if ":raise" in spot_key_text and ":raise@" not in spot_key_text
    ]
    assert sizeless == []


def test_the_committed_artifact_still_holds_thirty_six_spots(library) -> None:
    """Re-keying is not re-solving. Each prefix admits one solved size, so the count
    does not move, which is what makes the size free in cells."""
    assert len(library.spot_keys()) == 36


def test_the_committed_keys_are_the_measured_ones(library) -> None:
    """Five hand-checked keys, each traceable to a sizing entry by a reader.

    `t6/d100/CO/rfi` is 2.5 and `t6/d100/BTN/LJ:raise` is 8.0, which is where the two
    prices in the three-bet key below come from.
    """
    keys = set(library.spot_keys())
    assert "t6/d100/BTN/CO:raise@2.5" in keys
    assert "t6/d100/BB/SB:raise@3.5" in keys
    assert "t6/d100/BB/SB:call" in keys
    assert "t6/d100/LJ/LJ:raise@2.5,BTN:raise@8" in keys
    assert "t6/d100/SB/SB:raise@3.5,BB:raise@10.5" in keys


def test_every_sizing_key_is_a_key_the_artifact_declares(library, sizing) -> None:
    """The key says what hero faces; the sizing table says what hero does. They are
    indexed the same way, so a re-keying that moved one and not the other would leave
    every raise refusing for no committed size."""
    assert set(sizing.raise_to_bb) == set(library.spot_keys())


def test_the_artifact_re_derives_from_its_source() -> None:
    """`convert_preflop_export.py --check` is what makes the re-keying auditable.

    Green at the branch point, so this is an over-application guard: a chart nobody can
    regenerate is a chart nobody can diff against its origin, and re-keying must not
    cost that property.
    """
    completed = subprocess.run(
        [sys.executable, "scripts/convert_preflop_export.py", "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


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
    """The payload gained a field, so version 1 bytes and version 2 bytes would
    otherwise be indistinguishable, which is
    DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS repeated knowingly."""
    assert contract_module.DECISION_AUDIT_SCHEMA_VERSION == 2


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
    purpose. As authored, the filter also caught
    `t6/d100/BB/SB:call,BB:raise@3,SB:raise@12` - the one limped second-orbit decision in
    the sample, which had no key at the branch point and so was invisible to a filter
    requiring one. Counting it here would have made a guard against nearest-spot matching
    fail for the second orbit finally having a key, which is the opposite of what it is
    guarding.
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
    query = contract_module.StrategyQuery(
        hand_id="h1",
        street="preflop",
        seat=3,
        button_seat=3,
        hole_cards=("As", "Kd"),
        board=(),
        legal_actions=("fold", "call", "raise"),
        to_call=225,
        street_bet=225,
        min_raise_target=350,
        pot=375,
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
