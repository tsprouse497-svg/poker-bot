from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from poker_training_bot.poker_core.engine import (
    Action,
    ActionKind,
    BettingRoundState,
    PlayerState,
)


def _validated_seats(seats: Sequence[int]) -> tuple[int, ...]:
    ordered = tuple(sorted(seats))
    if len(ordered) != len(set(ordered)):
        raise ValueError("duplicate seats are not allowed")
    if len(ordered) < 2 or len(ordered) > 9:
        raise ValueError("turn order requires two to nine occupied seats")
    return ordered


def next_seat(seats: Sequence[int], seat: int) -> int:
    ordered = _validated_seats(seats)
    if seat not in ordered:
        raise ValueError(f"seat {seat} is not an occupied seat")
    index = ordered.index(seat)
    return ordered[(index + 1) % len(ordered)]


def blind_seats(seats: Sequence[int], button_seat: int) -> tuple[int, int]:
    ordered = _validated_seats(seats)
    if button_seat not in ordered:
        raise ValueError(f"button seat {button_seat} is not an occupied seat")
    small_blind = button_seat if len(ordered) == 2 else next_seat(ordered, button_seat)
    big_blind = next_seat(ordered, small_blind)
    return small_blind, big_blind


def _is_live(player: PlayerState) -> bool:
    return not player.folded and not player.all_in and player.stack > 0


def _occupied_seats(round: BettingRoundState) -> tuple[int, ...]:
    return tuple(sorted(player.seat for player in round.players))


def _next_to_act(round: BettingRoundState, start_seat: int, acted: frozenset[int]) -> int | None:
    seats = _occupied_seats(round)
    live = [seat for seat in seats if _is_live(round.player(seat))]
    if not live:
        return None
    candidate: int | None = None
    seat = start_seat
    for _ in range(len(seats)):
        seat = next_seat(seats, seat)
        if seat in acted:
            continue
        if _is_live(round.player(seat)):
            candidate = seat
            break
    if candidate is None:
        return None
    if len(live) == 1 and round.player(candidate).street_bet == round.current_bet:
        return None
    return candidate


@dataclass(frozen=True)
class TurnState:
    """Whose turn it is, who has acted, and who may no longer raise.

    `reopen_level` is the bet level the last full bet or raise landed on, and it is what
    the reopening rule measures against. Measuring against the immediately preceding bet
    level instead is `UNDER-RAISE-ACCUMULATION`: two short all-ins that each fall short on
    their own but together advance the bet by a full raise leave betting closed forever,
    where a real room reopens it for the seats that already acted.
    """

    round: BettingRoundState
    to_act: int | None
    acted: frozenset[int]
    no_raise: frozenset[int]
    reopen_level: int = 0

    def __post_init__(self) -> None:
        seats = set(_occupied_seats(self.round))
        if self.to_act is not None and self.to_act not in seats:
            raise ValueError(f"seat to act is not an occupied seat: {self.to_act}")
        for seat in self.acted | self.no_raise:
            if seat not in seats:
                raise ValueError(f"tracked seat is not an occupied seat: {seat}")

    @staticmethod
    def start_preflop(round: BettingRoundState, button_seat: int) -> TurnState:
        _, big_blind = blind_seats(_occupied_seats(round), button_seat)
        return TurnState(
            round=round,
            to_act=_next_to_act(round, big_blind, frozenset()),
            acted=frozenset(),
            no_raise=frozenset(),
            reopen_level=round.current_bet,
        )

    @staticmethod
    def start_postflop(round: BettingRoundState, button_seat: int) -> TurnState:
        if button_seat not in _occupied_seats(round):
            raise ValueError(f"button seat {button_seat} is not an occupied seat")
        return TurnState(
            round=round,
            to_act=_next_to_act(round, button_seat, frozenset()),
            acted=frozenset(),
            no_raise=frozenset(),
            reopen_level=round.current_bet,
        )

    @property
    def round_complete(self) -> bool:
        return self.to_act is None

    def has_live_opponent(self, seat: int) -> bool:
        return any(
            player.seat != seat and _is_live(player) for player in self.round.players
        )

    def legal_actions(self, seat: int) -> tuple[ActionKind, ...]:
        actions = self.round.legal_actions(seat)
        if seat in self.no_raise:
            actions = tuple(kind for kind in actions if kind is not ActionKind.RAISE)
        if not self.has_live_opponent(seat):
            aggressive = {ActionKind.BET, ActionKind.RAISE}
            actions = tuple(kind for kind in actions if kind not in aggressive)
        return actions

    def apply(self, action: Action) -> TurnState:
        if self.to_act is None:
            raise ValueError("betting round is complete")
        if action.seat != self.to_act:
            raise ValueError(
                f"seat {action.seat} cannot act out of turn; seat {self.to_act} is next to act"
            )
        if action.kind is ActionKind.RAISE and action.seat in self.no_raise:
            raise ValueError(f"seat {action.seat} cannot re-raise after an under-raise all-in")
        if action.kind in {ActionKind.BET, ActionKind.RAISE} and not self.has_live_opponent(
            action.seat
        ):
            raise ValueError(
                f"seat {action.seat} cannot bet or raise with no live opponent to respond"
            )
        previous_min_raise = self.round.min_raise
        new_round = self.round.apply(action)
        if action.kind is ActionKind.BET:
            acted = frozenset({action.seat})
            no_raise: frozenset[int] = frozenset()
            reopen_level = new_round.current_bet
        elif action.kind is ActionKind.RAISE:
            acted = frozenset({action.seat})
            # Against the last full bet or raise, not against the bet level immediately
            # before this action. Short all-ins accumulate: each may fall short alone while
            # the pair advances the bet by a full raise, and that reopens betting for the
            # seats that already acted. A full raise resets the level it is measured from,
            # so an accumulator that never resets - which would reopen on any later
            # all-in - is a different bug in the same place.
            full_raise = new_round.current_bet - self.reopen_level >= previous_min_raise
            no_raise = frozenset() if full_raise else (self.no_raise | self.acted)
            reopen_level = new_round.current_bet if full_raise else self.reopen_level
        else:
            acted = self.acted | {action.seat}
            no_raise = self.no_raise
            reopen_level = self.reopen_level
        return TurnState(
            round=new_round,
            to_act=_next_to_act(new_round, action.seat, acted),
            acted=acted,
            no_raise=no_raise,
            reopen_level=reopen_level,
        )
