from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    StrategyDecision,
    StrategyProtocol,
    StrategyQuery,
    StrategyRefusal,
    records_to_jsonl,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy
from poker_training_bot.strategy.reference import CheckFoldStrategy


def make_query(**overrides: Any) -> StrategyQuery:
    fields: dict[str, Any] = {
        "hand_id": "h1",
        "street": "flop",
        "seat": 1,
        "button_seat": 0,
        "hole_cards": ("As", "Kd"),
        "board": ("2c", "7h", "Ts"),
        "legal_actions": ("fold", "call", "raise"),
        "to_call": 20,
        "street_bet": 20,
        "min_raise_target": 40,
        "pot": 60,
        "stacks": ((0, 980), (1, 940)),
        "blinds": (5, 10),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def _audit_line_for(outcome: StrategyDecision | StrategyRefusal) -> str:
    return DecisionAuditRecord(
        schema_version=DECISION_AUDIT_SCHEMA_VERSION,
        strategy_id="test",
        strategy_version=1,
        query=make_query(),
        outcome=outcome,
    ).to_json_line()


def _uncovered_spot_query() -> StrategyQuery:
    """A six-handed 100bb four-bet spot, which the committed charts do not hold.

    Phase 05 committed opens, responses to a single open, an opener facing a three-bet, and
    the big blind against a small-blind limp. A third raise is past all of those, so the
    lookup misses and the refusal has a spot key to name.
    """
    seats = (0, 1, 2, 3, 4, 5)
    big_blind = 100
    full = 100 * big_blind
    return StrategyQuery(
        hand_id="four-bet",
        street="preflop",
        seat=1,
        button_seat=3,
        hole_cards=("As", "Ah"),
        board=(),
        legal_actions=("fold", "call", "raise"),
        to_call=2200,
        street_bet=2200,
        min_raise_target=4400,
        pot=3000,
        stacks=tuple((seat, full - (2200 if seat == 2 else 0)) for seat in seats),
        blinds=(50, big_blind),
        preflop_actions=(
            SeatAction(1, "raise"),
            SeatAction(2, "raise"),
            SeatAction(1, "raise"),
            SeatAction(2, "raise"),
        ),
    )


def make_free_query(**overrides: Any) -> StrategyQuery:
    fields: dict[str, Any] = {
        "legal_actions": ("check", "bet"),
        "to_call": 0,
    }
    fields.update(overrides)
    return make_query(**fields)


def make_record(**overrides: Any) -> DecisionAuditRecord:
    fields: dict[str, Any] = {
        "schema_version": DECISION_AUDIT_SCHEMA_VERSION,
        "strategy_id": "reference-check-fold",
        "strategy_version": 1,
        "query": make_query(),
        "outcome": StrategyDecision("call", None, "x"),
    }
    fields.update(overrides)
    return DecisionAuditRecord(**fields)


class TestStrategyQueryValidation:
    def test_valid_query_constructs(self) -> None:
        assert make_query().street == "flop"
        assert make_free_query().to_call == 0

    def test_rejects_empty_hand_id(self) -> None:
        with pytest.raises(ValueError, match="hand_id"):
            make_query(hand_id="")

    def test_rejects_bad_street(self) -> None:
        with pytest.raises(ValueError, match="street"):
            make_query(street="showdown")

    def test_rejects_negative_seats(self) -> None:
        with pytest.raises(ValueError, match="seat"):
            make_query(seat=-1)
        with pytest.raises(ValueError, match="button_seat"):
            make_query(button_seat=-1)

    def test_rejects_bad_card_text(self) -> None:
        with pytest.raises(ValueError, match="invalid card"):
            make_query(hole_cards=("As", "Xx"))
        with pytest.raises(ValueError, match="invalid card"):
            make_query(board=("2c", "7h", "ace of spades"))

    def test_rejects_duplicate_cards(self) -> None:
        with pytest.raises(ValueError, match="duplicate cards"):
            make_query(board=("As", "7h", "Ts"))

    def test_rejects_board_cards_preflop(self) -> None:
        with pytest.raises(ValueError, match="preflop"):
            make_query(street="preflop", board=("2c", "7h", "Ts"))

    def test_rejects_wrong_board_size_for_street(self) -> None:
        with pytest.raises(ValueError, match="turn"):
            make_query(street="turn")

    def test_rejects_empty_legal_actions(self) -> None:
        with pytest.raises(ValueError, match="legal_actions"):
            make_query(legal_actions=())

    def test_rejects_unknown_legal_action(self) -> None:
        with pytest.raises(ValueError, match="unknown legal actions"):
            make_query(legal_actions=("fold", "limp"))

    def test_rejects_duplicate_legal_actions(self) -> None:
        with pytest.raises(ValueError, match="duplicate legal actions"):
            make_query(legal_actions=("fold", "call", "call"))

    def test_accepts_check_and_fold_together(self) -> None:
        """Phase 11 (FOLD-WHEN-FREE) removed this invariant, because it became false.

        The engine now offers a fold wherever a seat may act, so a query refusing to
        describe that set would be a query that lies about the game. It is the one
        validation Phase 11's contract permits removing, and it is named there.
        """
        query = make_query(legal_actions=("check", "fold"), to_call=0)
        assert set(query.legal_actions) == {"check", "fold"}

    def test_rejects_check_with_positive_to_call(self) -> None:
        with pytest.raises(ValueError, match="to_call"):
            make_query(legal_actions=("check", "bet"), to_call=20)

    def test_rejects_zero_to_call_without_check(self) -> None:
        with pytest.raises(ValueError, match="to_call"):
            make_query(legal_actions=("fold", "call"), to_call=0)

    def test_rejects_negative_to_call(self) -> None:
        with pytest.raises(ValueError, match="to_call"):
            make_query(to_call=-1)

    def test_rejects_non_positive_min_raise_target_and_pot(self) -> None:
        with pytest.raises(ValueError, match="min_raise_target"):
            make_query(min_raise_target=0)
        with pytest.raises(ValueError, match="pot"):
            make_query(pot=0)

    def test_rejects_unsorted_stacks(self) -> None:
        with pytest.raises(ValueError, match="sorted by seat"):
            make_query(stacks=((1, 940), (0, 980)))

    def test_rejects_duplicate_stack_seats(self) -> None:
        with pytest.raises(ValueError, match="sorted by seat"):
            make_query(stacks=((0, 980), (0, 940)))

    def test_rejects_negative_stack(self) -> None:
        with pytest.raises(ValueError, match="stacks cannot be negative"):
            make_query(stacks=((0, 980), (1, -1)))

    def test_rejects_bad_blinds(self) -> None:
        with pytest.raises(ValueError, match="small blind"):
            make_query(blinds=(0, 10))
        with pytest.raises(ValueError, match="small blind"):
            make_query(blinds=(20, 10))

    def test_to_payload_is_json_primitives(self) -> None:
        payload = make_query().to_payload()
        assert payload["hole_cards"] == ["As", "Kd"]
        assert payload["board"] == ["2c", "7h", "Ts"]
        assert payload["legal_actions"] == ["fold", "call", "raise"]
        assert payload["stacks"] == {"0": 980, "1": 940}
        assert payload["blinds"] == [5, 10]


class TestStrategyDecisionValidation:
    def test_bet_and_raise_require_positive_amount(self) -> None:
        with pytest.raises(ValueError, match="bet requires a positive amount"):
            StrategyDecision("bet", None, "x")
        with pytest.raises(ValueError, match="raise requires a positive amount"):
            StrategyDecision("raise", 0, "x")
        assert StrategyDecision("raise", 40, "x").amount == 40

    def test_amount_forbidden_for_other_actions(self) -> None:
        for action in ("fold", "check", "call"):
            with pytest.raises(ValueError, match="must not include an amount"):
                StrategyDecision(action, 10, "x")

    def test_rejects_unknown_action(self) -> None:
        with pytest.raises(ValueError, match="unknown action"):
            StrategyDecision("limp", None, "x")

    def test_rejects_empty_codes(self) -> None:
        with pytest.raises(ValueError, match="decision code"):
            StrategyDecision("fold", None, "")
        with pytest.raises(ValueError, match="refusal code"):
            StrategyRefusal("")


class TestDecisionAuditRecord:
    def test_rejects_decision_outside_legal_actions(self) -> None:
        with pytest.raises(ValueError, match="not in legal_actions"):
            make_record(outcome=StrategyDecision("check", None, "x"))

    def test_rejects_wrong_schema_version(self) -> None:
        with pytest.raises(ValueError, match="schema_version"):
            make_record(schema_version=2)

    def test_rejects_bad_strategy_identity(self) -> None:
        with pytest.raises(ValueError, match="strategy_id"):
            make_record(strategy_id="")
        with pytest.raises(ValueError, match="strategy_version"):
            make_record(strategy_version=0)

    def test_accepts_refusal_outcome(self) -> None:
        record = make_record(outcome=StrategyRefusal("reference:no-passive-action"))
        assert '"kind":"refusal"' in record.to_json_line()

    def test_to_json_line_is_byte_deterministic(self) -> None:
        assert make_record().to_json_line() == make_record().to_json_line()

    def test_to_json_line_pins_key_ordering(self) -> None:
        expected = (
            '{"outcome":{"action":"call","amount":null,"code":"x","kind":"decision"},'
            '"query":{"blinds":[5,10],"board":["2c","7h","Ts"],"button_seat":0,'
            '"hand_id":"h1","hole_cards":["As","Kd"],'
            '"legal_actions":["fold","call","raise"],"min_raise_target":40,"pot":60,'
            '"preflop_actions":[],'
            '"seat":1,"stacks":{"0":980,"1":940},"street":"flop","street_bet":20,'
            '"to_call":20},'
            '"schema_version":1,"strategy_id":"reference-check-fold",'
            '"strategy_version":1}'
        )
        assert make_record().to_json_line() == expected

    def test_rejects_raise_amount_below_minimum_unless_all_in(self) -> None:
        with pytest.raises(ValueError, match="below the minimum unless all-in"):
            make_record(outcome=StrategyDecision("raise", 25, "x"))
        # Hero's own contribution to the street plus hero's stack, per Phase 11
        # (DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE). The query carries street_bet 20 and
        # to_call 20, so hero has put in nothing and the target is the stack itself. The
        # old form added the whole level and was too high by exactly the price to call.
        all_in_target = (20 - 20) + 940
        record = make_record(outcome=StrategyDecision("raise", all_in_target, "x"))
        assert '"amount":940' in record.to_json_line()

    def test_rejects_raise_amount_above_all_in_maximum(self) -> None:
        with pytest.raises(ValueError, match="exceeds the acting seat's all-in maximum"):
            make_record(outcome=StrategyDecision("raise", (20 - 20) + 940 + 1, "x"))

    def test_records_to_jsonl_has_trailing_newline(self) -> None:
        record = make_record()
        jsonl = records_to_jsonl([record, record])
        assert jsonl == record.to_json_line() + "\n" + record.to_json_line() + "\n"

    def test_records_to_jsonl_empty_sequence(self) -> None:
        assert records_to_jsonl([]) == ""


class TestCheckFoldStrategy:
    def test_checks_when_free(self) -> None:
        decision = CheckFoldStrategy().decide(make_free_query())
        assert decision == StrategyDecision("check", None, "reference:check-when-free")

    def test_folds_facing_a_bet(self) -> None:
        decision = CheckFoldStrategy().decide(make_query())
        assert decision == StrategyDecision("fold", None, "reference:fold-facing-bet")

    def test_refuses_when_neither_is_legal(self) -> None:
        query = make_query(legal_actions=("call", "raise"))
        assert CheckFoldStrategy().decide(query) == StrategyRefusal("reference:no-passive-action")

    def test_decisions_are_recordable_as_audit_records(self) -> None:
        strategy = CheckFoldStrategy()
        query = make_query()
        outcome = strategy.decide(query)
        record = DecisionAuditRecord(
            schema_version=DECISION_AUDIT_SCHEMA_VERSION,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.strategy_version,
            query=query,
            outcome=outcome,
        )
        assert replace(record).to_json_line() == record.to_json_line()

    def test_conforms_to_strategy_protocol(self) -> None:
        strategy = CheckFoldStrategy()
        assert isinstance(strategy, StrategyProtocol)
        assert strategy.strategy_id == "reference-check-fold"
        assert strategy.strategy_version == 1


class TestPreflopActionHistory:
    """The history `to_call` and `stacks` cannot express.

    Several different sequences produce identical prices, so without this a
    chart-backed strategy cannot tell an open from a three-bet from a limp.
    """

    def test_defaults_to_empty_so_existing_callers_are_unaffected(self) -> None:
        assert make_query().preflop_actions == ()

    def test_accepts_an_ordered_history_of_seat_actions(self) -> None:
        history = (SeatAction(0, "raise"), SeatAction(1, "call"))

        query = make_query(preflop_actions=history)

        assert query.preflop_actions == history

    def test_records_folds_as_well_as_voluntary_actions(self) -> None:
        """This is game state, not an already-canonicalized chart key."""
        query = make_query(preflop_actions=(SeatAction(0, "fold"), SeatAction(1, "raise")))

        assert [entry.action for entry in query.preflop_actions] == ["fold", "raise"]

    def test_hero_may_appear_in_its_own_history(self) -> None:
        """The original raiser facing a three-bet is a real spot."""
        query = make_query(preflop_actions=(SeatAction(1, "raise"), SeatAction(0, "raise")))

        assert query.preflop_actions[0].seat == 1

    def test_rejects_a_seat_that_is_not_at_the_table(self) -> None:
        with pytest.raises(ValueError, match="not at the table"):
            make_query(preflop_actions=(SeatAction(7, "raise"),))

    def test_rejects_an_unknown_action(self) -> None:
        with pytest.raises(ValueError, match="unknown history action"):
            SeatAction(0, "shove")

    def test_rejects_a_bet_because_preflop_has_no_bet(self) -> None:
        with pytest.raises(ValueError, match="unknown history action"):
            SeatAction(0, "bet")

    def test_rejects_a_negative_seat(self) -> None:
        with pytest.raises(ValueError, match="non-negative integer"):
            SeatAction(-1, "raise")

    def test_rejects_entries_that_are_not_seat_actions(self) -> None:
        with pytest.raises(ValueError, match="must be SeatAction"):
            make_query(preflop_actions=((0, "raise"),))

    def test_history_reaches_the_decision_audit(self) -> None:
        query = make_query(preflop_actions=(SeatAction(0, "raise"),))

        payload = query.to_payload()

        assert payload["preflop_actions"] == [{"seat": 0, "action": "raise"}]

    def test_audit_line_stays_byte_deterministic_with_history(self) -> None:
        history = (SeatAction(0, "raise"), SeatAction(1, "call"))
        first = make_record(query=make_query(preflop_actions=history))
        second = make_record(query=make_query(preflop_actions=history))

        assert first.to_json_line() == second.to_json_line()

    def test_different_histories_serialize_differently(self) -> None:
        """Two spots that share a price must not share an audit line."""
        opened = make_record(query=make_query(preflop_actions=(SeatAction(0, "raise"),)))
        limped = make_record(query=make_query(preflop_actions=(SeatAction(0, "call"),)))

        assert opened.to_json_line() != limped.to_json_line()


class TestRefusalDetail:
    """A refusal names what was missing, not only that something was.

    The code is a groupable vocabulary and the detail is what makes a refusal actionable.
    The split exists because a count of refusals is not a work list: a phase measuring
    coverage can say a chart was silent 128 times, and closing the gap needs the 128 spots.
    """

    def test_a_refusal_needs_no_detail(self) -> None:
        """Empty by default, so a refusal with nothing to add stays as simple as it was."""
        refusal = StrategyRefusal("some:code")

        assert refusal.detail == ()
        assert refusal.named("spot_key") is None

    def test_detail_is_readable_by_name_rather_than_by_position(self) -> None:
        refusal = StrategyRefusal(
            "some:code", (("spot_key", "t6/d100/BTN/rfi"), ("hand_class", "A2o"))
        )

        assert refusal.named("spot_key") == "t6/d100/BTN/rfi"
        assert refusal.named("hand_class") == "A2o"
        assert refusal.named("absent") is None

    def test_detail_reaches_the_audit_line(self) -> None:
        refusal = StrategyRefusal("some:code", (("spot_key", "t6/d100/BTN/rfi"),))
        payload = json.loads(_audit_line_for(refusal))

        assert payload["outcome"]["code"] == "some:code"
        assert payload["outcome"]["detail"] == [["spot_key", "t6/d100/BTN/rfi"]]

    def test_a_refusal_without_detail_serializes_as_it_always_did(self) -> None:
        """No key at all, so audit lines written before this field existed are unchanged."""
        payload = json.loads(_audit_line_for(StrategyRefusal("some:code")))

        assert "detail" not in payload["outcome"]

    def test_the_same_refusal_serializes_to_the_same_bytes(self) -> None:
        detail = (("spot_key", "t6/d100/BTN/rfi"), ("hand_class", "A2o"))
        lines = {_audit_line_for(StrategyRefusal("some:code", detail)) for _ in range(3)}

        assert len(lines) == 1

    def test_malformed_detail_is_rejected(self) -> None:
        for bad in (
            [("spot_key", "x")],
            (("spot_key",),),
            (("", "x"),),
            (("spot_key", 3),),
            (("spot_key", "x"), ("spot_key", "y")),
        ):
            with pytest.raises(ValueError):
                StrategyRefusal("some:code", bad)


class TestChartRefusalsNameTheirSpot:
    # The spot key comes from the lookup's own derivation, so a refusal names a cell the
    # lookup actually asked about rather than one this layer guessed at.
    def test_an_uncovered_spot_reports_the_key_it_looked_for(self) -> None:
        strategy = PreflopChartStrategy.from_repo()
        outcome = strategy.decide(_uncovered_spot_query())

        assert isinstance(outcome, StrategyRefusal), outcome
        assert outcome.named("hand_class")
        assert outcome.named("table_size") == "6"
        assert outcome.named("stack_depth_bb") == "100"
