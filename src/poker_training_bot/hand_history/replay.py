from __future__ import annotations

from dataclasses import dataclass, replace

from poker_training_bot.hand_history.schema import (
    HistoryAction,
    HistoryActionKind,
    NormalizedHandHistory,
    StreetName,
)
from poker_training_bot.poker_core.cards import Card
from poker_training_bot.poker_core.engine import (
    Action,
    ActionKind,
    BettingRoundState,
    PlayerState,
    Settlement,
    settle_showdown,
    settle_uncontested,
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
    sb_seat, bb_seat = _blind_seats(hand)
    if not hand.streets or len(hand.streets[0].actions) < 2:
        raise ValueError("preflop must open with small and big blind posts")
    for street in hand.streets:
        if len(set(committed) - folded) <= 1:
            raise ValueError(f"{street.name.value} street follows an uncontested hand")
        state = _street_state(hand, committed, folded, all_in)
        for position, action in enumerate(street.actions):
            if len(set(committed) - folded) <= 1:
                raise ValueError(f"seat {action.seat} acts after the hand is decided")
            is_blind_slot = street.name == StreetName.PREFLOP and position < 2
            if is_blind_slot:
                expected_seat, owed = (
                    (sb_seat, hand.blinds.small_blind)
                    if position == 0
                    else (bb_seat, hand.blinds.big_blind)
                )
                if action.kind != HistoryActionKind.POST_BLIND:
                    raise ValueError("preflop must open with small and big blind posts")
                if action.seat != expected_seat:
                    raise ValueError(
                        f"seat {action.seat} posted a blind owed by seat {expected_seat}"
                    )
                state = _apply_post_blind(state, action.seat, action.committed_amount, owed)
            elif action.kind == HistoryActionKind.POST_BLIND:
                raise ValueError("post_blind is only allowed as the first two preflop actions")
            else:
                state = _apply_betting_action(state, action)
            committed = {player.seat: player.committed_total for player in state.players}
            folded = {player.seat for player in state.players if player.folded}
            all_in = {player.seat for player in state.players if player.all_in}

    if sum(committed.values()) != hand.result.pot:
        raise ValueError("committed chips do not match result pot")

    active_seats = set(committed) - folded
    if not active_seats:
        raise ValueError("at least one non-folded seat is required")
    if len(active_seats) == 1:
        if hand.showdown:
            raise ValueError("uncontested hands must not include showdown entries")
        settlement = settle_uncontested(_final_players(hand, committed, folded, {}))
    else:
        if len(hand.board) != 5:
            raise ValueError("deterministic showdown replay requires a five-card board")
        hole_cards = {entry.seat: entry.hole_cards for entry in hand.showdown}
        missing_hole_cards = active_seats - set(hole_cards)
        if missing_hole_cards:
            raise ValueError(
                f"active seats missing showdown hole cards: {sorted(missing_hole_cards)}"
            )
        settlement = settle_showdown(
            _final_players(hand, committed, folded, hole_cards),
            hand.board,
        )
    replay = HandReplay(
        hand=hand,
        settlement=settlement,
        committed_by_seat=committed,
        folded_seats=tuple(sorted(folded)),
    )
    if not replay.passed_expected_result:
        raise ValueError(f"replay result does not match expected result for {hand.hand_id}")
    return replay


def _final_players(
    hand: NormalizedHandHistory,
    committed: dict[int, int],
    folded: set[int],
    hole_cards: dict[int, tuple[Card, Card]],
) -> tuple[PlayerState, ...]:
    return tuple(
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


def _blind_seats(hand: NormalizedHandHistory) -> tuple[int, int]:
    seats = sorted(player.seat for player in hand.players)
    sb_seat = hand.button_seat if len(seats) == 2 else _next_seat(seats, hand.button_seat)
    return sb_seat, _next_seat(seats, sb_seat)


def _next_seat(seats: list[int], seat: int) -> int:
    for candidate in seats:
        if candidate > seat:
            return candidate
    return seats[0]


def _apply_post_blind(
    state: BettingRoundState,
    seat: int,
    amount: int,
    owed: int,
) -> BettingRoundState:
    player = state.player(seat)
    short_all_in = amount == player.stack and amount < owed
    if amount != owed and not short_all_in:
        raise ValueError("post_blind amount must match a configured blind unless all-in for less")
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
        current_bet=max(state.current_bet, owed),
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
