from __future__ import annotations

import pytest

from poker_training_bot.poker_core import (
    Action,
    ActionKind,
    BettingRoundState,
    HandCategory,
    PlayerState,
    evaluate_best,
    parse_cards,
    settle_showdown,
)
from poker_training_bot.poker_core.golden import replay_golden_hands
from scripts.repo_paths import REPO_ROOT


def test_best_hand_evaluator_orders_major_categories() -> None:
    royal = evaluate_best(parse_cards(["As", "Ks", "Qs", "Js", "Ts", "2d", "3c"]))
    full_house = evaluate_best(parse_cards(["Ah", "Ad", "Ac", "Kd", "Kc", "2s", "3h"]))

    assert royal.category == HandCategory.STRAIGHT_FLUSH
    assert full_house.category == HandCategory.FULL_HOUSE
    assert royal.beats(full_house)


def test_best_hand_evaluator_handles_wheel_straight() -> None:
    wheel = evaluate_best(parse_cards(["As", "2d", "3c", "4h", "5s", "Kc", "Qd"]))

    assert wheel.category == HandCategory.STRAIGHT
    assert wheel.kickers == (5,)


def test_betting_round_rejects_illegal_check_and_min_raise() -> None:
    players = (
        PlayerState(0, "Button", 100, parse_cards(["As", "Ad"]), street_bet=0),
        PlayerState(1, "Big Blind", 100, parse_cards(["Ks", "Kd"]), street_bet=10),
    )
    state = BettingRoundState(players=players, current_bet=10, min_raise=10)

    assert state.legal_actions(0) == (ActionKind.FOLD, ActionKind.CALL, ActionKind.RAISE)
    with pytest.raises(ValueError, match="check is not legal"):
        state.apply(Action(0, ActionKind.CHECK))
    with pytest.raises(ValueError, match="minimum raise"):
        state.apply(Action(0, ActionKind.RAISE, amount=15))


def test_betting_round_applies_call_and_all_in_raise() -> None:
    players = (
        PlayerState(0, "Button", 20, parse_cards(["As", "Ad"]), street_bet=0),
        PlayerState(1, "Big Blind", 100, parse_cards(["Ks", "Kd"]), street_bet=10),
    )
    state = BettingRoundState(players=players, current_bet=10, min_raise=10)

    called = state.apply(Action(0, ActionKind.CALL))
    assert called.player(0).stack == 10
    assert called.player(0).street_bet == 10
    raised = state.apply(Action(0, ActionKind.RAISE, amount=20))
    assert raised.player(0).all_in
    assert raised.current_bet == 20


def test_big_blind_option_offers_raise_and_applies_it() -> None:
    players = (
        PlayerState(0, "Small Blind", 90, parse_cards(["As", "Ad"]), street_bet=10),
        PlayerState(1, "Big Blind", 90, parse_cards(["Ks", "Kd"]), street_bet=10),
    )
    state = BettingRoundState(players=players, current_bet=10, min_raise=10)

    # Fold joins the free set in Phase 11 (FOLD-WHEN-FREE): folding for nothing is a bad
    # play and a legal one, and calling it illegal is what stopped real histories replaying.
    assert state.legal_actions(1) == (ActionKind.FOLD, ActionKind.CHECK, ActionKind.RAISE)
    raised = state.apply(Action(1, ActionKind.RAISE, amount=30))
    assert raised.current_bet == 30
    assert raised.player(1).street_bet == 30
    assert raised.player(1).stack == 70
    with pytest.raises(ValueError, match="bet is not legal"):
        state.apply(Action(1, ActionKind.BET, amount=30))


def test_bet_raises_the_minimum_raise_to_the_bet_size() -> None:
    players = (
        PlayerState(0, "Button", 500, parse_cards(["As", "Ad"]), street_bet=0),
        PlayerState(1, "Big Blind", 500, parse_cards(["Ks", "Kd"]), street_bet=0),
    )
    state = BettingRoundState(players=players, current_bet=0, min_raise=10)

    bet = state.apply(Action(1, ActionKind.BET, amount=200))
    assert bet.min_raise == 200
    with pytest.raises(ValueError, match="minimum raise"):
        bet.apply(Action(0, ActionKind.RAISE, amount=210))
    raised = bet.apply(Action(0, ActionKind.RAISE, amount=400))
    assert raised.current_bet == 400


def test_showdown_settlement_splits_side_pots_by_eligibility() -> None:
    board = parse_cards(["2h", "3h", "4h", "8c", "Kd"])
    players = (
        PlayerState(0, "Short", 0, parse_cards(["Ah", "Kh"]), committed_total=50),
        PlayerState(1, "Middle", 0, parse_cards(["8s", "8d"]), committed_total=100),
        PlayerState(2, "Deep", 0, parse_cards(["9s", "9d"]), committed_total=200),
    )

    settlement = settle_showdown(players, board)

    assert [pot.amount for pot in settlement.pots] == [150, 100, 100]
    assert [pot.winner_seats for pot in settlement.pots] == [(0,), (1,), (2,)]
    assert settlement.payouts == {0: 150, 1: 100, 2: 100}


def test_golden_hands_replay_expected_winners_and_totals() -> None:
    results = replay_golden_hands(REPO_ROOT / "data" / "samples" / "golden_hands.json")
    by_id = {hand.hand_id: settlement for hand, settlement in results}

    assert by_id["phase01-heads-up-royal-vs-full-house"].payouts == {0: 200, 1: 0}
    assert by_id["phase01-nine-player-side-pot"].total_pot == 1850
    assert by_id["phase01-nine-player-side-pot"].payouts[0] == 450
    assert by_id["phase01-nine-player-side-pot"].payouts[5] == 1400
    assert by_id["phase01-split-pot-board-straight"].payouts == {0: 75, 1: 75, 2: 75}


def test_engine_rejects_duplicate_cards_and_invalid_player_count() -> None:
    with pytest.raises(ValueError, match="two to nine"):
        BettingRoundState(
            players=(PlayerState(0, "Solo", 100, parse_cards(["As", "Ad"])),),
            current_bet=0,
            min_raise=10,
        )
    with pytest.raises(ValueError, match="duplicate card"):
        evaluate_best(parse_cards(["As", "As", "Qs", "Js", "Ts"]))
