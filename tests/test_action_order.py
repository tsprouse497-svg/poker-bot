from __future__ import annotations

import pytest

from poker_training_bot.poker_core.cards import parse_cards
from poker_training_bot.poker_core.engine import (
    Action,
    ActionKind,
    BettingRoundState,
    PlayerState,
)
from poker_training_bot.poker_core.order import TurnState, blind_seats, next_seat

_HOLE_TEXTS = (
    "As",
    "Ah",
    "Ks",
    "Kh",
    "Qs",
    "Qh",
    "Js",
    "Jh",
    "Ts",
    "Th",
    "9s",
    "9h",
    "8s",
    "8h",
    "7s",
    "7h",
    "6s",
    "6h",
    "5s",
    "5h",
)


def make_player(
    seat: int,
    stack: int = 100,
    bet: int = 0,
    folded: bool = False,
    all_in: bool = False,
) -> PlayerState:
    hole = parse_cards(_HOLE_TEXTS[2 * seat : 2 * seat + 2])
    return PlayerState(
        seat=seat,
        name=f"p{seat}",
        stack=stack,
        hole_cards=(hole[0], hole[1]),
        committed_total=bet,
        street_bet=bet,
        folded=folded,
        all_in=all_in,
    )


def heads_up_preflop_state() -> TurnState:
    round_state = BettingRoundState(
        players=(make_player(0, stack=95, bet=5), make_player(1, stack=90, bet=10)),
        current_bet=10,
        min_raise=10,
    )
    return TurnState.start_preflop(round_state, button_seat=0)


def three_handed_preflop_state() -> TurnState:
    round_state = BettingRoundState(
        players=(
            make_player(0),
            make_player(1, stack=95, bet=5),
            make_player(2, stack=90, bet=10),
        ),
        current_bet=10,
        min_raise=10,
    )
    return TurnState.start_preflop(round_state, button_seat=0)


def heads_up_postflop_state() -> TurnState:
    round_state = BettingRoundState(
        players=(make_player(0), make_player(1)),
        current_bet=0,
        min_raise=10,
    )
    return TurnState.start_postflop(round_state, button_seat=0)


def test_blind_seats_heads_up_button_posts_small_blind() -> None:
    assert blind_seats((2, 5), 2) == (2, 5)
    assert blind_seats((2, 5), 5) == (5, 2)


def test_blind_seats_three_handed_wraps_from_highest_button() -> None:
    assert blind_seats((1, 3, 7), 7) == (1, 3)


def test_blind_seats_rejects_button_not_in_seats() -> None:
    with pytest.raises(ValueError, match="button seat 5 is not an occupied seat"):
        blind_seats((1, 2, 3), 5)


def test_next_seat_wraps_ascending() -> None:
    assert next_seat((1, 3, 7), 1) == 3
    assert next_seat((1, 3, 7), 7) == 1
    with pytest.raises(ValueError, match="seat 4 is not an occupied seat"):
        next_seat((1, 3, 7), 4)


def test_heads_up_preflop_button_acts_first() -> None:
    state = heads_up_preflop_state()
    assert state.to_act == 0
    assert not state.round_complete


def test_heads_up_preflop_big_blind_option_check_completes() -> None:
    state = heads_up_preflop_state()
    state = state.apply(Action(seat=0, kind=ActionKind.CALL))
    assert state.to_act == 1
    state = state.apply(Action(seat=1, kind=ActionKind.CHECK))
    assert state.to_act is None
    assert state.round_complete


def test_heads_up_preflop_big_blind_raise_reopens_action() -> None:
    state = heads_up_preflop_state()
    state = state.apply(Action(seat=0, kind=ActionKind.CALL))
    state = state.apply(Action(seat=1, kind=ActionKind.RAISE, amount=20))
    assert state.to_act == 0
    assert not state.round_complete
    state = state.apply(Action(seat=0, kind=ActionKind.CALL))
    assert state.round_complete


def test_three_handed_preflop_first_to_act_is_after_big_blind() -> None:
    state = three_handed_preflop_state()
    assert state.to_act == 0


def test_three_handed_preflop_skips_folded_seats() -> None:
    state = three_handed_preflop_state()
    state = state.apply(Action(seat=0, kind=ActionKind.FOLD))
    assert state.to_act == 1
    state = state.apply(Action(seat=1, kind=ActionKind.CALL))
    assert state.to_act == 2
    state = state.apply(Action(seat=2, kind=ActionKind.RAISE, amount=20))
    assert state.to_act == 1
    state = state.apply(Action(seat=1, kind=ActionKind.CALL))
    assert state.round_complete


def test_fold_leaving_one_live_player_facing_no_bet_completes_round() -> None:
    state = three_handed_preflop_state()
    state = state.apply(Action(seat=0, kind=ActionKind.FOLD))
    state = state.apply(Action(seat=1, kind=ActionKind.FOLD))
    assert state.to_act is None
    assert state.round_complete


def test_postflop_heads_up_non_button_acts_first() -> None:
    state = heads_up_postflop_state()
    assert state.to_act == 1


def test_postflop_check_check_completes_round() -> None:
    state = heads_up_postflop_state()
    state = state.apply(Action(seat=1, kind=ActionKind.CHECK))
    assert state.to_act == 0
    state = state.apply(Action(seat=0, kind=ActionKind.CHECK))
    assert state.round_complete


def test_bet_resets_acted_so_checker_acts_again() -> None:
    state = heads_up_postflop_state()
    state = state.apply(Action(seat=1, kind=ActionKind.CHECK))
    state = state.apply(Action(seat=0, kind=ActionKind.BET, amount=20))
    assert state.to_act == 1
    state = state.apply(Action(seat=1, kind=ActionKind.CALL))
    assert state.round_complete


def test_under_raise_all_in_bars_prior_actors_from_raising() -> None:
    round_state = BettingRoundState(
        players=(make_player(0, stack=200), make_player(1, stack=200), make_player(2, stack=35)),
        current_bet=0,
        min_raise=20,
    )
    state = TurnState.start_postflop(round_state, button_seat=2)
    assert state.to_act == 0
    state = state.apply(Action(seat=0, kind=ActionKind.BET, amount=20))
    state = state.apply(Action(seat=1, kind=ActionKind.CALL))
    assert state.to_act == 2
    state = state.apply(Action(seat=2, kind=ActionKind.RAISE, amount=35))
    assert state.to_act == 0
    assert ActionKind.RAISE in state.round.legal_actions(0)
    with pytest.raises(ValueError, match="cannot re-raise after an under-raise all-in"):
        state.apply(Action(seat=0, kind=ActionKind.RAISE, amount=70))
    state = state.apply(Action(seat=0, kind=ActionKind.CALL))
    assert state.to_act == 1
    assert ActionKind.RAISE in state.round.legal_actions(1)
    with pytest.raises(ValueError, match="cannot re-raise after an under-raise all-in"):
        state.apply(Action(seat=1, kind=ActionKind.RAISE, amount=70))
    state = state.apply(Action(seat=1, kind=ActionKind.CALL))
    assert state.round_complete


def test_out_of_turn_action_names_both_seats() -> None:
    state = heads_up_preflop_state()
    with pytest.raises(
        ValueError, match="seat 1 cannot act out of turn; seat 0 is next to act"
    ):
        state.apply(Action(seat=1, kind=ActionKind.CHECK))


def test_acting_on_complete_round_is_rejected() -> None:
    state = heads_up_postflop_state()
    state = state.apply(Action(seat=1, kind=ActionKind.CHECK))
    state = state.apply(Action(seat=0, kind=ActionKind.CHECK))
    with pytest.raises(ValueError, match="betting round is complete"):
        state.apply(Action(seat=1, kind=ActionKind.CHECK))


def test_all_players_all_in_completes_immediately() -> None:
    round_state = BettingRoundState(
        players=(
            make_player(0, stack=0, bet=50, all_in=True),
            make_player(1, stack=0, bet=100, all_in=True),
        ),
        current_bet=100,
        min_raise=10,
    )
    assert TurnState.start_preflop(round_state, button_seat=0).to_act is None
    assert TurnState.start_postflop(round_state, button_seat=0).round_complete


def test_single_live_seat_facing_a_bet_still_acts() -> None:
    round_state = BettingRoundState(
        players=(
            make_player(0, stack=0, bet=25, all_in=True),
            make_player(1, stack=90, bet=10),
        ),
        current_bet=25,
        min_raise=10,
    )
    state = TurnState.start_preflop(round_state, button_seat=0)
    assert state.to_act == 1
    state = state.apply(Action(seat=1, kind=ActionKind.CALL))
    assert state.round_complete


def test_second_under_raise_keeps_earlier_seats_barred() -> None:
    round_state = BettingRoundState(
        players=(
            make_player(0, stack=400, bet=0),
            make_player(1, stack=45, bet=0),
            make_player(2, stack=50, bet=0),
            make_player(3, stack=400, bet=0),
        ),
        current_bet=0,
        min_raise=20,
    )
    state = TurnState.start_postflop(round_state, button_seat=3)
    state = state.apply(Action(seat=0, kind=ActionKind.BET, amount=40))
    state = state.apply(Action(seat=1, kind=ActionKind.RAISE, amount=45))
    state = state.apply(Action(seat=2, kind=ActionKind.RAISE, amount=50))
    state = state.apply(Action(seat=3, kind=ActionKind.CALL))

    assert 0 in state.no_raise
    assert state.legal_actions(0) == (ActionKind.FOLD, ActionKind.CALL)
    with pytest.raises(ValueError, match="cannot re-raise after an under-raise all-in"):
        state.apply(Action(seat=0, kind=ActionKind.RAISE, amount=70))


def test_betting_into_only_all_in_opponents_is_rejected() -> None:
    round_state = BettingRoundState(
        players=(
            make_player(0, stack=0, bet=50, all_in=True),
            make_player(1, stack=500, bet=10),
        ),
        current_bet=50,
        min_raise=10,
    )
    state = TurnState.start_preflop(round_state, button_seat=1)
    assert state.legal_actions(1) == (ActionKind.FOLD, ActionKind.CALL)
    with pytest.raises(ValueError, match="no live opponent"):
        state.apply(Action(seat=1, kind=ActionKind.RAISE, amount=200))


def test_legal_actions_filters_raise_for_barred_seats() -> None:
    round_state = BettingRoundState(
        players=(
            make_player(0, stack=400, bet=0),
            make_player(1, stack=45, bet=0),
            make_player(2, stack=400, bet=0),
        ),
        current_bet=0,
        min_raise=20,
    )
    state = TurnState.start_postflop(round_state, button_seat=2)
    state = state.apply(Action(seat=0, kind=ActionKind.BET, amount=40))
    state = state.apply(Action(seat=1, kind=ActionKind.RAISE, amount=45))
    state = state.apply(Action(seat=2, kind=ActionKind.CALL))

    assert state.to_act == 0
    assert ActionKind.RAISE in state.round.legal_actions(0)
    assert state.legal_actions(0) == (ActionKind.FOLD, ActionKind.CALL)
