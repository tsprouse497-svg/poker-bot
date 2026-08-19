"""Phase 11: the six fidelity defects, each pinned from both sides.

Every test here is authored from `docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`
before any implementation exists, so the file is red on assertions rather than on an
import error. Each defect gets a test that fails against the behaviour on `main` at this
phase's branch point, and a test that the correction is not over-applied - because a fix
that goes one step too far is a defect the first kind of test cannot see.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

import scripts.run_verify as run_verify
from poker_training_bot.hand_history.replay import replay_hand
from poker_training_bot.hand_history.schema import (
    BlindStructure,
    ExpectedResult,
    HistoryAction,
    HistoryActionKind,
    HistoryPlayer,
    HistoryStreet,
    NormalizedHandHistory,
    StreetName,
)
from poker_training_bot.poker_core.cards import parse_cards
from poker_training_bot.poker_core.engine import (
    Action,
    ActionKind,
    BettingRoundState,
    PlayerState,
)
from poker_training_bot.poker_core.order import TurnState
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.postflop_fallback import (
    REFUSE_NO_PASSIVE_ACTION,
    PostflopFallbackStrategy,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy
from poker_training_bot.strategy.reference import CheckFoldStrategy
from scripts.repo_paths import REPO_ROOT

_HOLE_TEXTS = ("As", "Ah", "Ks", "Kh", "Qs", "Qh", "Js", "Jh", "Ts", "Th", "9s", "9h")


def make_player(seat: int, stack: int = 100, bet: int = 0) -> PlayerState:
    return PlayerState(
        seat=seat,
        name=f"p{seat}",
        stack=stack,
        hole_cards=parse_cards(_HOLE_TEXTS[2 * seat : 2 * seat + 2]),
        street_bet=bet,
    )


def make_round(stacks: tuple[int, ...], current_bet: int = 0, min_raise: int = 20):
    return BettingRoundState(
        players=tuple(make_player(seat, stack) for seat, stack in enumerate(stacks)),
        current_bet=current_bet,
        min_raise=min_raise,
    )


def make_query(**overrides) -> StrategyQuery:
    fields = {
        "hand_id": "phase11",
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


# --------------------------------------------------------------------------- #
# FOLD-WHEN-FREE
# --------------------------------------------------------------------------- #


class TestFoldIsLegalWhenCheckingIsFree:
    """A fold offered wherever a seat may act at all.

    Folding for nothing is a bad play and a legal one. The cost of calling it illegal is
    that no real history containing a surrendered river or a timed-out check replays at
    all, which is what blocks ingesting anybody's actual hands.
    """

    def test_a_free_spot_offers_fold(self) -> None:
        state = make_round((100, 100))
        assert ActionKind.FOLD in state.legal_actions(0)

    def test_fold_comes_first_in_a_free_legal_action_set(self) -> None:
        """One ordering everywhere, so a caller reading position 0 reads the same thing.

        Facing a bet the engine already returns fold first. A free spot that put it last
        would make the tuple's order carry information, which nothing should have to know.
        """
        state = make_round((100, 100))
        assert state.legal_actions(0) == (ActionKind.FOLD, ActionKind.CHECK, ActionKind.BET)

    def test_a_free_spot_with_a_bet_already_matched_offers_fold_check_and_raise(self) -> None:
        """Hero has matched the level, so checking is free and raising is still on offer."""
        state = BettingRoundState(
            players=(make_player(0, stack=80, bet=20), make_player(1, stack=80, bet=20)),
            current_bet=20,
            min_raise=20,
        )
        assert state.legal_actions(0) == (
            ActionKind.FOLD,
            ActionKind.CHECK,
            ActionKind.RAISE,
        )

    def test_folding_for_free_commits_no_chips(self) -> None:
        state = make_round((100, 100))
        after = state.apply(Action(0, ActionKind.FOLD))
        assert after.player(0).stack == 100
        assert after.player(0).committed_total == 0
        assert after.player(0).street_bet == 0

    def test_folding_for_free_leaves_the_bet_and_the_minimum_raise_alone(self) -> None:
        state = make_round((100, 100))
        after = state.apply(Action(0, ActionKind.FOLD))
        assert after.current_bet == state.current_bet
        assert after.min_raise == state.min_raise

    def test_folding_for_free_ends_the_seats_involvement(self) -> None:
        state = make_round((100, 100))
        after = state.apply(Action(0, ActionKind.FOLD))
        assert after.player(0).folded is True
        assert after.legal_actions(0) == ()

    # -- not over-applied -- #

    def test_check_stays_legal_exactly_when_the_price_to_call_is_zero(self) -> None:
        state = make_round((100, 100)).apply(Action(0, ActionKind.BET, 20))
        assert ActionKind.CHECK not in state.legal_actions(1)

    def test_facing_a_bet_offers_the_same_set_it_always_did(self) -> None:
        state = make_round((100, 100)).apply(Action(0, ActionKind.BET, 20))
        assert state.legal_actions(1) == (
            ActionKind.FOLD,
            ActionKind.CALL,
            ActionKind.RAISE,
        )

    def test_a_seat_that_cannot_act_is_still_offered_nothing(self) -> None:
        state = make_round((100, 100))
        after = state.apply(Action(0, ActionKind.FOLD))
        assert after.legal_actions(0) == ()

    def test_an_all_in_seat_is_still_offered_nothing(self) -> None:
        state = BettingRoundState(
            players=(make_player(0, stack=0, bet=50), make_player(1, stack=100)),
            current_bet=50,
            min_raise=20,
        )
        assert state.legal_actions(0) == ()


class TestTheQueryDescribesAFreeFold:
    def test_check_and_fold_together_is_a_valid_query(self) -> None:
        """The engine now produces this set, and a query that refuses it lies."""
        query = make_query(legal_actions=("fold", "check", "raise"), to_call=0)
        assert query.legal_actions == ("fold", "check", "raise")

    # -- not over-applied -- #

    def test_check_with_a_price_to_call_is_still_rejected(self) -> None:
        with pytest.raises(ValueError, match="to_call"):
            make_query(legal_actions=("fold", "check", "raise"), to_call=20)

    def test_zero_to_call_without_check_is_still_rejected(self) -> None:
        with pytest.raises(ValueError, match="to_call"):
            make_query(legal_actions=("fold", "call"), to_call=0)


def _free_fold_hand() -> NormalizedHandHistory:
    """Heads-up. The button calls, the big blind checks, and folds the flop for free.

    The fold is the whole point: nobody has bet on the flop, so under the behaviour this
    phase replaces, `replay_hand` raises rather than settling.
    """
    return NormalizedHandHistory(
        schema_version=1,
        hand_id="phase11-free-fold",
        table_id="t-phase11",
        max_seats=2,
        players=(
            HistoryPlayer(seat=0, player_id="button", starting_stack=200),
            HistoryPlayer(seat=1, player_id="bigblind", starting_stack=200),
        ),
        button_seat=0,
        blinds=BlindStructure(small_blind=5, big_blind=10),
        streets=(
            HistoryStreet(
                name=StreetName.PREFLOP,
                board=(),
                actions=(
                    HistoryAction(0, HistoryActionKind.POST_BLIND, 5),
                    HistoryAction(1, HistoryActionKind.POST_BLIND, 10),
                    HistoryAction(0, HistoryActionKind.CALL, 5),
                    HistoryAction(1, HistoryActionKind.CHECK),
                ),
            ),
            HistoryStreet(
                name=StreetName.FLOP,
                board=parse_cards(("2c", "7h", "Ts")),
                actions=(
                    HistoryAction(1, HistoryActionKind.FOLD),
                ),
            ),
        ),
        showdown=(),
        result=ExpectedResult(winner_seats=(0,), pot=20, payouts={0: 20, 1: 0}),
    )


class TestReplayAcceptsARecordedFreeFold:
    def test_the_hand_replays_end_to_end(self) -> None:
        replay = replay_hand(_free_fold_hand())
        assert replay.passed_expected_result is True

    def test_the_folding_seat_is_recorded_as_folded(self) -> None:
        replay = replay_hand(_free_fold_hand())
        assert replay.folded_seats == (1,)

    def test_the_free_fold_commits_nothing_beyond_the_blind(self) -> None:
        replay = replay_hand(_free_fold_hand())
        assert replay.committed_by_seat == {0: 10, 1: 10}

    def test_the_pot_goes_to_the_seat_that_did_not_fold(self) -> None:
        replay = replay_hand(_free_fold_hand())
        assert replay.settlement.payouts == {0: 20, 1: 0}


class TestNoShippedStrategyFoldsWhenCheckingIsFree:
    """Legal is not chosen. Making the action available must not make a bot take it."""

    def test_the_postflop_fallback_checks_in_every_free_shape(self) -> None:
        fallback = PostflopFallbackStrategy()
        for street, board in (
            ("flop", ("2c", "7h", "Ts")),
            ("turn", ("2c", "7h", "Ts", "4d")),
            ("river", ("2c", "7h", "Ts", "4d", "9c")),
        ):
            for legal in (("fold", "check", "bet"), ("fold", "check", "raise")):
                outcome = fallback.decide(
                    make_query(street=street, board=board, legal_actions=legal, to_call=0)
                )
                assert isinstance(outcome, StrategyDecision)
                assert outcome.action == "check", (street, legal)

    def test_the_reference_strategy_checks_when_free(self) -> None:
        outcome = CheckFoldStrategy().decide(
            make_query(legal_actions=("fold", "check", "bet"), to_call=0)
        )
        assert isinstance(outcome, StrategyDecision)
        assert outcome.action == "check"

    def test_no_committed_chart_spot_folds_where_checking_is_free(self) -> None:
        """The big blind facing limps is the one committed spot where check is free.

        A spot key's action sequence carries no raise exactly when nobody has raised, so
        the big blind in such a spot may check. If the chart carried fold weight there it
        would be folding a free option, and that would be an artifact finding rather than
        something this phase may silence.
        """
        library = PreflopChartStrategy.from_repo().library
        free_spots = [
            key
            for key in library.spot_keys()
            if key.split("/")[2] == "BB" and "raise" not in key.split("/")[3]
        ]
        assert free_spots, "expected at least one committed big-blind spot with no raise"
        for key in free_spots:
            assert library.action_frequency_pct(key, "fold") == pytest.approx(0.0), key


# --------------------------------------------------------------------------- #
# UNDER-RAISE-ACCUMULATION
# --------------------------------------------------------------------------- #


def _two_short_all_ins(second_stack: int) -> TurnState:
    """Bet 10 with a minimum raise of 10, then two all-ins that are each short.

    Seat 1 is all-in for 15 - five over the bet, half a raise. Seat 2 is all-in for
    `second_stack`. Measured one at a time neither reopens; measured against the last full
    bet, the pair reopens as soon as the level reaches 20.
    """
    state = make_round((100, 15, second_stack, 100), min_raise=2)
    turn = TurnState.start_postflop(state, button_seat=3)
    turn = turn.apply(Action(0, ActionKind.BET, 10))
    turn = turn.apply(Action(1, ActionKind.RAISE, 15))
    return turn.apply(Action(2, ActionKind.RAISE, second_stack))


class TestBettingReopensWhenShortAllInsAccumulate:
    def test_two_short_all_ins_past_the_bar_reopen_betting(self) -> None:
        turn = _two_short_all_ins(21)
        assert 0 not in turn.no_raise
        assert ActionKind.RAISE in turn.legal_actions(0)

    def test_exactly_at_the_bar_reopens(self) -> None:
        """21 clears by a chip; 20 is the boundary itself and must clear too."""
        turn = _two_short_all_ins(20)
        assert ActionKind.RAISE in turn.legal_actions(0)

    def test_one_chip_below_the_bar_does_not_reopen(self) -> None:
        turn = _two_short_all_ins(19)
        assert 0 in turn.no_raise
        assert ActionKind.RAISE not in turn.legal_actions(0)

    def test_three_short_all_ins_accumulate(self) -> None:
        """13, 16 and 21: no increment reaches 10 alone, and the level reaches 21."""
        state = make_round((100, 13, 16, 21, 100), min_raise=2)
        turn = TurnState.start_postflop(state, button_seat=4)
        turn = turn.apply(Action(0, ActionKind.BET, 10))
        for seat, target in ((1, 13), (2, 16), (3, 21)):
            turn = turn.apply(Action(seat, ActionKind.RAISE, target))
        assert ActionKind.RAISE in turn.legal_actions(0)

    def test_three_short_all_ins_short_of_the_bar_do_not_accumulate(self) -> None:
        """The same three, ending at 19. Nine is not ten, however many all-ins made it."""
        state = make_round((100, 13, 16, 19, 100), min_raise=2)
        turn = TurnState.start_postflop(state, button_seat=4)
        turn = turn.apply(Action(0, ActionKind.BET, 10))
        for seat, target in ((1, 13), (2, 16), (3, 19)):
            turn = turn.apply(Action(seat, ActionKind.RAISE, target))
        assert ActionKind.RAISE not in turn.legal_actions(0)

    def test_a_full_raise_resets_the_level_the_accumulation_is_measured_from(self) -> None:
        """After a full raise to 30, a later short all-in is measured against 30.

        Without the reset, the accumulation would still be counted from 10 and a single
        short all-in would reopen - which is the opposite defect.
        """
        state = make_round((100, 100, 35, 100), min_raise=2)
        turn = TurnState.start_postflop(state, button_seat=3)
        turn = turn.apply(Action(0, ActionKind.BET, 10))
        turn = turn.apply(Action(1, ActionKind.RAISE, 30))
        turn = turn.apply(Action(2, ActionKind.RAISE, 35))
        # Seat 1 made the full raise and is the seat that has acted since it, so seat 1 is
        # the one the short all-in must not reopen for. Measured from 30 the advance is 5
        # against a minimum raise of 20; measured from 10 it would be 25 and would reopen,
        # which is the reset this test exists for. Seat 0 keeps its right to raise because
        # seat 1's full raise gave it back, and a short all-in does not take it away again.
        assert 1 in turn.no_raise
        assert ActionKind.RAISE not in turn.legal_actions(1)
        assert 0 not in turn.no_raise

    def test_a_reopened_seat_must_still_meet_the_minimum_raise(self) -> None:
        """Reopening restores the right to raise, not a cheaper price for it."""
        turn = _two_short_all_ins(21)
        # Seat 3 has not acted yet and is next; seat 0 is reopened behind it.
        turn = turn.apply(Action(3, ActionKind.CALL))
        assert turn.to_act == 0
        with pytest.raises(ValueError, match="minimum raise"):
            turn.apply(Action(0, ActionKind.RAISE, 22))
        assert turn.apply(Action(0, ActionKind.RAISE, 31)).round.current_bet == 31

    # -- not over-applied -- #

    def test_a_single_short_all_in_still_does_not_reopen(self) -> None:
        state = make_round((100, 15, 100), min_raise=2)
        turn = TurnState.start_postflop(state, button_seat=2)
        turn = turn.apply(Action(0, ActionKind.BET, 10))
        turn = turn.apply(Action(1, ActionKind.RAISE, 15))
        assert 0 in turn.no_raise
        assert ActionKind.RAISE not in turn.legal_actions(0)

    def test_a_barred_seat_may_still_call_and_fold(self) -> None:
        turn = _two_short_all_ins(19)
        assert ActionKind.CALL in turn.legal_actions(0)
        assert ActionKind.FOLD in turn.legal_actions(0)

    def test_a_seat_that_had_not_acted_was_never_barred(self) -> None:
        turn = _two_short_all_ins(19)
        assert 3 not in turn.no_raise


# --------------------------------------------------------------------------- #
# STREET-BET-MEANING-AMBIGUOUS
# --------------------------------------------------------------------------- #


class TestStreetBetHasOneMeaning:
    def test_the_query_documents_which_reading_it_carries(self) -> None:
        """The field had two readings because nothing in the repo said which was meant."""
        doc = StrategyQuery.__doc__ or ""
        assert "current bet level" in doc
        assert "street_bet" in doc

    def test_a_street_bet_below_the_price_to_call_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="street_bet"):
            make_query(street_bet=10, to_call=20)

    def test_the_query_report_generator_writes_the_street_level(self) -> None:
        """Read out of what the generator actually wrote, not out of its source text.

        The small blind's preflop record is the one that separates the two readings: hero
        has put in 5 and the level is 10. Asserting on the committed audit line means a
        producer that computes the right value on an unreachable path does not pass.
        """
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "generate_strategy_query_report.py")],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stderr
        audit = (REPO_ROOT / "reports" / "active" / "latest_decision_audit.jsonl").read_text()
        preflop = [
            json.loads(line)["query"]
            for line in audit.splitlines()
            if line.strip() and json.loads(line)["query"]["street"] == "preflop"
        ]
        assert preflop, "expected at least one preflop record in the decision audit"
        for query in preflop:
            # Preflop the street's bet level is never below the big blind, because the big
            # blind posted it. Hero's own contribution can be - the small blind's is half
            # of it - so this separates the two readings on the record that matters.
            assert query["street_bet"] >= query["blinds"][1], query["hand_id"]

    # -- not over-applied -- #

    def test_a_street_bet_equal_to_the_price_to_call_is_accepted(self) -> None:
        assert make_query(street_bet=20, to_call=20).street_bet == 20

    def test_a_free_spot_may_carry_a_positive_street_bet(self) -> None:
        """Hero has matched the level, so the price is zero and the level is not."""
        query = make_query(legal_actions=("fold", "check", "raise"), to_call=0, street_bet=20)
        assert query.street_bet == 20


# --------------------------------------------------------------------------- #
# DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE
# --------------------------------------------------------------------------- #


def _record(query: StrategyQuery, outcome: StrategyDecision) -> DecisionAuditRecord:
    return DecisionAuditRecord(
        schema_version=DECISION_AUDIT_SCHEMA_VERSION,
        strategy_id="phase11",
        strategy_version=1,
        query=query,
        outcome=outcome,
    )


class TestTheAllInCeilingIsWhatHeroCanRaiseTo:
    """Street bet 20, price to call 20, stack 100.

    Hero has put in 20 minus 20, which is nothing, so hero's all-in raise target is 100.
    The old ceiling was 20 plus 100 and accepted a raise to 120 - too loose by exactly the
    price to call.
    """

    def test_a_raise_above_the_corrected_ceiling_is_rejected(self) -> None:
        query = make_query(street_bet=20, to_call=20, stacks=((0, 980), (1, 100)))
        with pytest.raises(ValueError, match="all-in maximum"):
            _record(query, StrategyDecision("raise", 120, "phase11:too-big"))

    def test_the_old_ceiling_is_no_longer_the_boundary(self) -> None:
        query = make_query(street_bet=20, to_call=20, stacks=((0, 980), (1, 100)))
        with pytest.raises(ValueError, match="all-in maximum"):
            _record(query, StrategyDecision("raise", 101, "phase11:one-over"))

    def test_hero_who_has_already_invested_keeps_the_higher_ceiling(self) -> None:
        """Street bet 30, price to call 10: hero put in 20, so the target is 20 plus 100."""
        query = make_query(
            street_bet=30, to_call=10, min_raise_target=40, stacks=((0, 980), (1, 100))
        )
        record = _record(query, StrategyDecision("raise", 120, "phase11:all-in"))
        assert record.outcome.amount == 120
        with pytest.raises(ValueError, match="all-in maximum"):
            _record(query, StrategyDecision("raise", 121, "phase11:one-over"))

    # -- not over-applied -- #

    def test_a_raise_exactly_at_the_corrected_target_is_accepted(self) -> None:
        query = make_query(street_bet=20, to_call=20, stacks=((0, 980), (1, 100)))
        record = _record(query, StrategyDecision("raise", 100, "phase11:all-in"))
        assert record.outcome.amount == 100

    def test_a_raise_below_the_minimum_is_still_rejected_unless_all_in(self) -> None:
        query = make_query(street_bet=20, to_call=20, stacks=((0, 980), (1, 500)))
        with pytest.raises(ValueError, match="below the minimum"):
            _record(query, StrategyDecision("raise", 30, "phase11:too-small"))

    def test_every_committed_decision_audit_record_still_validates(self) -> None:
        """Nothing any shipped strategy has written falls outside the tighter ceiling.

        The check runs the real validator rather than recomputing the ceiling here. A test
        that rebuilds the rule it is checking agrees with the code whatever the code says,
        which is the defect MAINT-07 found in the settlement oracle.
        """
        checked = 0
        for name in ("latest_decision_audit.jsonl", "latest_postflop_decision_audit.jsonl"):
            path = REPO_ROOT / "reports" / "active" / name
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                payload = json.loads(line)
                outcome = payload["outcome"]
                if outcome["kind"] != "decision":
                    continue
                query = payload["query"]
                rebuilt = StrategyQuery(
                    hand_id=query["hand_id"],
                    street=query["street"],
                    seat=query["seat"],
                    button_seat=query["button_seat"],
                    hole_cards=tuple(query["hole_cards"]),
                    board=tuple(query["board"]),
                    legal_actions=tuple(query["legal_actions"]),
                    to_call=query["to_call"],
                    street_bet=query["street_bet"],
                    min_raise_target=query["min_raise_target"],
                    pot=query["pot"],
                    stacks=tuple(
                        (int(seat), stack) for seat, stack in sorted(query["stacks"].items())
                    ),
                    blinds=tuple(query["blinds"]),
                )
                _record(
                    rebuilt,
                    StrategyDecision(outcome["action"], outcome["amount"], outcome["code"]),
                )
                checked += 1
        assert checked, "expected committed decision audits to check against"


# --------------------------------------------------------------------------- #
# FALLBACK-FAIL-CLOSED-CAN-CALL
# --------------------------------------------------------------------------- #


class TestTheFallbackFailClosedBranchNeverInvests:
    """Neither branch is reachable from the engine's own legal actions.

    That is exactly why neither was covered, so both are driven from a contract-valid
    query rather than from an engine state.
    """

    def test_a_set_offering_call_but_not_fold_refuses_rather_than_investing(self) -> None:
        """The filed defect exactly: this set used to call, and a call can lose."""
        outcome = PostflopFallbackStrategy().decide(
            make_query(
                street="flop",
                board=("2c", "7h", "Ts"),
                legal_actions=("call", "raise"),
                to_call=20,
            )
        )
        assert isinstance(outcome, StrategyRefusal)
        assert outcome.code == REFUSE_NO_PASSIVE_ACTION

    def test_a_set_offering_only_aggression_refuses(self) -> None:
        outcome = PostflopFallbackStrategy().decide(
            make_query(
                street="flop",
                board=("2c", "7h", "Ts"),
                legal_actions=("raise",),
                to_call=20,
            )
        )
        assert isinstance(outcome, StrategyRefusal)
        assert outcome.code == REFUSE_NO_PASSIVE_ACTION

    def test_a_hand_that_can_lose_still_folds_when_fold_is_legal(self) -> None:
        outcome = PostflopFallbackStrategy().decide(
            make_query(
                street="river",
                board=("2c", "7h", "Ts", "4d", "9c"),
                legal_actions=("fold", "call"),
                to_call=20,
            )
        )
        assert isinstance(outcome, StrategyDecision)
        assert outcome.action == "fold"

    # -- not over-applied -- #

    def test_the_unbeatable_call_is_untouched(self) -> None:
        """Quad aces on a board nothing can beat still calls."""
        outcome = PostflopFallbackStrategy().decide(
            make_query(
                street="river",
                hole_cards=("Ac", "Ad"),
                board=("As", "Ah", "Kd", "Qc", "Jh"),
                legal_actions=("fold", "call"),
                to_call=20,
            )
        )
        assert isinstance(outcome, StrategyDecision)
        assert outcome.action == "call"

    def test_a_preflop_query_still_refuses(self) -> None:
        outcome = PostflopFallbackStrategy().decide(
            make_query(street="preflop", board=(), legal_actions=("fold", "call"), to_call=20)
        )
        assert isinstance(outcome, StrategyRefusal)


# --------------------------------------------------------------------------- #
# GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK
# --------------------------------------------------------------------------- #


class TestTheCommandRegistryDescribesChecksThatExist:
    def test_the_expectations_command_names_no_directional_bound(self) -> None:
        """The bound was withdrawn on 2026-08-18 with the parity solve."""
        description = run_verify.COMMANDS["check_solver_export_expectations"].description
        assert "directional bound" not in description

    def test_the_expectations_command_says_what_it_does_compute(self) -> None:
        description = run_verify.COMMANDS["check_solver_export_expectations"].description
        assert "ordering" in description
        assert "source card" in description

    def test_this_phase_registers_both_of_its_command_ids(self) -> None:
        assert "pytest_engine_fidelity" in run_verify.COMMANDS
        assert "generate_engine_fidelity_report" in run_verify.COMMANDS

    # -- not over-applied -- #

    def test_every_command_still_carries_a_description(self) -> None:
        for command_id, spec in run_verify.COMMANDS.items():
            assert spec.description.strip(), command_id
