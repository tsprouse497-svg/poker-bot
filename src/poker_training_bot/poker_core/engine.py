from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from poker_training_bot.poker_core.cards import Card, validate_unique_cards
from poker_training_bot.poker_core.hand_eval import HandRank, evaluate_best


class ActionKind(StrEnum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"


@dataclass(frozen=True)
class Action:
    seat: int
    kind: ActionKind
    amount: int | None = None


@dataclass(frozen=True)
class PlayerState:
    seat: int
    name: str
    stack: int
    hole_cards: tuple[Card, Card] | tuple[()]
    committed_total: int = 0
    street_bet: int = 0
    folded: bool = False
    all_in: bool = False

    def __post_init__(self) -> None:
        if self.seat < 0:
            raise ValueError("seat must be non-negative")
        if self.stack < 0:
            raise ValueError("stack cannot be negative")
        if len(self.hole_cards) not in {0, 2}:
            raise ValueError("players must have either zero or two hole cards")
        validate_unique_cards(tuple(self.hole_cards))


@dataclass(frozen=True)
class BettingRoundState:
    players: tuple[PlayerState, ...]
    current_bet: int
    min_raise: int

    def __post_init__(self) -> None:
        validate_player_count(self.players)
        if self.current_bet < 0:
            raise ValueError("current bet cannot be negative")
        if self.min_raise <= 0:
            raise ValueError("minimum raise must be positive")
        validate_unique_cards(tuple(card for player in self.players for card in player.hole_cards))

    def player(self, seat: int) -> PlayerState:
        for player in self.players:
            if player.seat == seat:
                return player
        raise ValueError(f"unknown seat: {seat}")

    def legal_actions(self, seat: int) -> tuple[ActionKind, ...]:
        player = self.player(seat)
        if player.folded or player.all_in or player.stack == 0:
            return ()
        to_call = self.current_bet - player.street_bet
        if to_call <= 0:
            actions = [ActionKind.CHECK]
            if player.stack > 0:
                actions.append(ActionKind.BET)
            return tuple(actions)
        actions = [ActionKind.FOLD, ActionKind.CALL]
        if player.stack > to_call:
            actions.append(ActionKind.RAISE)
        return tuple(actions)

    def apply(self, action: Action) -> BettingRoundState:
        player = self.player(action.seat)
        if action.kind not in self.legal_actions(action.seat):
            raise ValueError(f"{action.kind.value} is not legal for seat {action.seat}")

        if action.kind == ActionKind.FOLD:
            return self._replace_player(replace(player, folded=True))
        if action.kind == ActionKind.CHECK:
            return self
        if action.kind == ActionKind.CALL:
            to_call = self.current_bet - player.street_bet
            return self._commit(
                player,
                min(player.stack, to_call),
                self.current_bet,
                self.min_raise,
            )
        if action.kind == ActionKind.BET:
            amount = _required_amount(action)
            if self.current_bet != 0:
                raise ValueError("bet is only legal before a bet exists")
            if amount < self.min_raise and amount < player.stack:
                raise ValueError("bet must meet the minimum bet unless all-in")
            return self._commit(player, amount, amount, self.min_raise)
        if action.kind == ActionKind.RAISE:
            target = _required_amount(action)
            to_call = self.current_bet - player.street_bet
            added = target - player.street_bet
            raise_size = target - self.current_bet
            if target <= self.current_bet:
                raise ValueError("raise target must exceed the current bet")
            if added > player.stack:
                raise ValueError("raise target exceeds player stack")
            if raise_size < self.min_raise and added < player.stack:
                raise ValueError("raise must meet the minimum raise unless all-in")
            if to_call < 0:
                raise ValueError("player street bet cannot exceed current bet")
            new_min_raise = self.min_raise if raise_size < self.min_raise else raise_size
            return self._commit(player, added, target, new_min_raise)
        raise ValueError(f"unsupported action: {action.kind}")

    def _commit(
        self,
        player: PlayerState,
        added: int,
        current_bet: int,
        min_raise: int,
    ) -> BettingRoundState:
        if added < 0:
            raise ValueError("cannot commit negative chips")
        if added > player.stack:
            raise ValueError("cannot commit more than player stack")
        updated = replace(
            player,
            stack=player.stack - added,
            committed_total=player.committed_total + added,
            street_bet=player.street_bet + added,
            all_in=player.stack - added == 0,
        )
        return self._replace_player(updated, current_bet=current_bet, min_raise=min_raise)

    def _replace_player(
        self,
        player: PlayerState,
        current_bet: int | None = None,
        min_raise: int | None = None,
    ) -> BettingRoundState:
        players = tuple(
            player if existing.seat == player.seat else existing for existing in self.players
        )
        return BettingRoundState(
            players=players,
            current_bet=self.current_bet if current_bet is None else current_bet,
            min_raise=self.min_raise if min_raise is None else min_raise,
        )


@dataclass(frozen=True)
class PotResult:
    amount: int
    eligible_seats: tuple[int, ...]
    winner_seats: tuple[int, ...]
    hand_rank: HandRank


@dataclass(frozen=True)
class Settlement:
    pots: tuple[PotResult, ...]
    payouts: dict[int, int]
    showdown_ranks: dict[int, HandRank]

    @property
    def total_pot(self) -> int:
        return sum(pot.amount for pot in self.pots)


def validate_player_count(players: tuple[PlayerState, ...] | list[PlayerState]) -> None:
    if len(players) < 2 or len(players) > 9:
        raise ValueError("NLHE core engine supports two to nine players")
    seats = [player.seat for player in players]
    if len(seats) != len(set(seats)):
        raise ValueError("duplicate player seats are not allowed")


def settle_showdown(players: tuple[PlayerState, ...], board: tuple[Card, ...]) -> Settlement:
    validate_player_count(players)
    if len(board) != 5:
        raise ValueError("showdown settlement requires a five-card board")
    validate_unique_cards(tuple(card for player in players for card in player.hole_cards) + board)
    contenders = [player for player in players if not player.folded and len(player.hole_cards) == 2]
    if not contenders:
        raise ValueError("at least one non-folded contender is required")

    ranks = {
        player.seat: evaluate_best(tuple(player.hole_cards) + board)
        for player in contenders
    }
    positive_levels = sorted(
        {player.committed_total for player in players if player.committed_total > 0}
    )
    if not positive_levels:
        raise ValueError("cannot settle a hand with no committed chips")

    payouts = {player.seat: 0 for player in players}
    pots: list[PotResult] = []
    previous = 0
    for level in positive_levels:
        amount = sum(max(0, min(player.committed_total, level) - previous) for player in players)
        if amount == 0:
            previous = level
            continue
        eligible = tuple(
            player for player in contenders if player.committed_total >= level
        )
        if not eligible:
            previous = level
            continue
        best = max((ranks[player.seat] for player in eligible), key=lambda rank: rank.sort_key)
        winners = tuple(player for player in eligible if ranks[player.seat].ties(best))
        share, remainder = divmod(amount, len(winners))
        for index, winner in enumerate(winners):
            payouts[winner.seat] += share + (1 if index < remainder else 0)
        pots.append(
            PotResult(
                amount=amount,
                eligible_seats=tuple(player.seat for player in eligible),
                winner_seats=tuple(player.seat for player in winners),
                hand_rank=best,
            )
        )
        previous = level
    return Settlement(pots=tuple(pots), payouts=payouts, showdown_ranks=ranks)


def _required_amount(action: Action) -> int:
    if action.amount is None:
        raise ValueError(f"{action.kind.value} requires an amount")
    if action.amount <= 0:
        raise ValueError("amount must be positive")
    return action.amount
