from __future__ import annotations

from dataclasses import dataclass, replace

from poker_training_bot.hand_history.schema import (
    HistoryAction,
    HistoryActionKind,
    HistoryStreet,
    NormalizedHandHistory,
    StreetName,
)
from poker_training_bot.poker_core.engine import (
    Action,
    ActionKind,
    BettingRoundState,
    PlayerState,
    Settlement,
    settle_showdown,
)


@dataclass(frozen=True)
class HandReplay:
    hand: NormalizedHandHistory
    settlement: Settlement
    committed_by_seat: dict[int, int]
    folded_seats: tuple[int, ...]

    @property
    def passed_expected_result(self) -> bool:
        actual_winner_seats = tuple(
            sorted(seat for seat, amount in self.settlement.payouts.items() if amount > 0)
        )
        return (
            self.settlement.total_pot == self.hand.result.pot
            and self.settlement.payouts == self.hand.result.payouts
            and actual_winner_seats == tuple(sorted(self.hand.result.winner_seats))
        )


def replay_hand(hand: NormalizedHandHistory) -> HandReplay:
    committed = {player.seat: 0 for player in hand.players}
    folded: set[int] = set()
    all_in: set[int] = set()
    for street in hand.streets:
        state = _street_state(hand, committed, folded, all_in)
        for action in street.actions:
            if action.kind == HistoryActionKind.POST_BLIND:
                state = _apply_post_blind(hand, street, state, action.seat, action.committed_amount)
            else:
                state = _apply_betting_action(state, action)
            committed = {player.seat: player.committed_total for player in state.players}
            folded = {player.seat for player in state.players if player.folded}
            all_in = {player.seat for player in state.players if player.all_in}

    if sum(committed.values()) != hand.result.pot:
        raise ValueError("committed chips do not match result pot")
    if len(hand.board) != 5:
        raise ValueError("deterministic showdown replay requires a five-card board")

    hole_cards = {entry.seat: entry.hole_cards for entry in hand.showdown}
    active_seats = set(committed) - folded
    missing_hole_cards = active_seats - set(hole_cards)
    if missing_hole_cards:
        raise ValueError(f"active seats missing showdown hole cards: {sorted(missing_hole_cards)}")

    players = tuple(
        PlayerState(
            seat=player.seat,
            name=player.player_id,
            stack=player.starting_stack - committed[player.seat],
            hole_cards=hole_cards.get(player.seat, ()),
            committed_total=committed[player.seat],
            folded=player.seat in folded,
            all_in=player.starting_stack - committed[player.seat] == 0,
        )
        for player in hand.players
    )
    settlement = settle_showdown(players, hand.board)
    replay = HandReplay(
        hand=hand,
        settlement=settlement,
        committed_by_seat=committed,
        folded_seats=tuple(sorted(folded)),
    )
    if not replay.passed_expected_result:
        raise ValueError(f"replay result does not match expected result for {hand.hand_id}")
    return replay


def replay_hands(hands: tuple[NormalizedHandHistory, ...]) -> tuple[HandReplay, ...]:
    return tuple(replay_hand(hand) for hand in hands)


def _street_state(
    hand: NormalizedHandHistory,
    committed: dict[int, int],
    folded: set[int],
    all_in: set[int],
) -> BettingRoundState:
    return BettingRoundState(
        players=tuple(
            PlayerState(
                seat=player.seat,
                name=player.player_id,
                stack=player.starting_stack - committed[player.seat],
                hole_cards=(),
                committed_total=committed[player.seat],
                street_bet=0,
                folded=player.seat in folded,
                all_in=player.seat in all_in,
            )
            for player in hand.players
        ),
        current_bet=0,
        min_raise=hand.blinds.big_blind,
    )


def _apply_post_blind(
    hand: NormalizedHandHistory,
    street: HistoryStreet,
    state: BettingRoundState,
    seat: int,
    amount: int,
) -> BettingRoundState:
    if street.name != StreetName.PREFLOP:
        raise ValueError("post_blind is only allowed preflop")
    if amount not in {hand.blinds.small_blind, hand.blinds.big_blind}:
        raise ValueError("post_blind amount must match a configured blind")
    player = state.player(seat)
    if player.folded or player.all_in or player.stack == 0:
        raise ValueError(f"seat {seat} cannot post a blind after leaving action")
    if player.street_bet != 0:
        raise ValueError(f"seat {seat} cannot post more than one blind")
    if amount > player.stack:
        raise ValueError(f"seat {seat} committed more than its starting stack")
    updated = replace(
        player,
        stack=player.stack - amount,
        committed_total=player.committed_total + amount,
        street_bet=player.street_bet + amount,
        all_in=player.stack - amount == 0,
    )
    players = tuple(
        updated if existing.seat == updated.seat else existing
        for existing in state.players
    )
    return BettingRoundState(
        players=players,
        current_bet=max(state.current_bet, updated.street_bet),
        min_raise=state.min_raise,
    )


def _apply_betting_action(state: BettingRoundState, action: HistoryAction) -> BettingRoundState:
    player = state.player(action.seat)
    if action.kind == HistoryActionKind.CALL:
        expected = min(player.stack, state.current_bet - player.street_bet)
        if action.committed_amount != expected:
            raise ValueError(f"call amount does not match legal call for seat {action.seat}")
        return state.apply(Action(action.seat, ActionKind.CALL))
    if action.kind == HistoryActionKind.BET:
        return state.apply(Action(action.seat, ActionKind.BET, action.committed_amount))
    if action.kind == HistoryActionKind.RAISE:
        return state.apply(Action(action.seat, ActionKind.RAISE, action.committed_amount))
    if action.kind == HistoryActionKind.CHECK:
        return state.apply(Action(action.seat, ActionKind.CHECK))
    if action.kind == HistoryActionKind.FOLD:
        return state.apply(Action(action.seat, ActionKind.FOLD))
    raise ValueError(f"unsupported betting action: {action.kind.value}")
