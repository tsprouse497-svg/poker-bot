"""The table: cards, engine state, and the question put to a strategy.

Split out of `run` so the hand loop reads as a hand loop rather than as one wrapped around
a pile of state plumbing. Nothing here decides anything about poker. It deals from a seeded
deck, hands the engine the state it needs, and turns live engine state into the Phase 03
query a strategy answers.

`street_state` is deliberately the same shape as the Phase 02 replayer's own - street bets
cleared, committed totals carried, current bet at zero, minimum raise back at one big blind
- because the two have to agree about what a street boundary is. Every dealt hand goes back
through that replayer as a cross-check, so a disagreement here would surface there as a
hand that cannot be re-derived.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from random import Random

from poker_training_bot.hand_history.schema import StreetName
from poker_training_bot.poker_core.cards import Card, card_texts, standard_deck
from poker_training_bot.poker_core.engine import BettingRoundState, PlayerState
from poker_training_bot.poker_core.order import TurnState
from poker_training_bot.simulator.config import SimulationConfig
from poker_training_bot.strategy.contract import SeatAction, SeatState, StrategyQuery

_STREET_SLICES = {
    StreetName.PREFLOP: slice(0, 0),
    StreetName.FLOP: slice(0, 3),
    StreetName.TURN: slice(3, 4),
    StreetName.RIVER: slice(4, 5),
}


def seat_label(seat: int) -> str:
    """How a seat is named inside a dealt hand.

    Deliberately not the profile's name. A dealt hand is a record of cards and actions, and
    which profile occupied a seat is a fact about the run - `SimulationResult.seat_names`
    carries that, and every decision audit line carries its own `strategy_id`. Keeping the
    two apart means renaming a profile cannot change a single byte of a dealt hand, which is
    what makes "two profiles differing only in name play identically" checkable rather than
    merely intended.
    """
    return f"seat-{seat}"


@dataclass(frozen=True)
class Dealt:
    """The cards a hand was dealt, kept apart from the betting so neither can drift."""

    hole_cards: dict[int, tuple[Card, Card]]
    board: tuple[Card, ...]

    def board_for(self, street: StreetName) -> tuple[Card, ...]:
        return self.board[_STREET_SLICES[street]]


def deal(config: SimulationConfig, rng: Random) -> Dealt:
    deck = list(standard_deck())
    rng.shuffle(deck)
    hole_cards = {
        seat: (deck[2 * index], deck[2 * index + 1]) for index, seat in enumerate(config.seats)
    }
    offset = 2 * len(config.seats)
    return Dealt(hole_cards=hole_cards, board=tuple(deck[offset : offset + 5]))


def post_blind(state: BettingRoundState, seat: int, owed: int) -> BettingRoundState:
    """Post a blind without going through `apply`, which only knows chosen actions.

    A forced post is not a decision and the engine's `legal_actions` never offers one, so the
    money moves directly here and the round's bet level rises to match. Everything after this
    point goes through the engine.
    """
    player = state.player(seat)
    posted = min(player.stack, owed)
    updated = replace(
        player,
        stack=player.stack - posted,
        committed_total=player.committed_total + posted,
        street_bet=player.street_bet + posted,
        all_in=player.stack - posted == 0,
    )
    players = tuple(updated if other.seat == seat else other for other in state.players)
    return BettingRoundState(
        players=players,
        current_bet=max(state.current_bet, owed),
        min_raise=state.min_raise,
    )


def street_state(
    config: SimulationConfig,
    stacks: dict[int, int],
    committed: dict[int, int],
    folded: set[int],
    all_in: set[int],
) -> BettingRoundState:
    """A fresh betting round with the street bets cleared, exactly as the replayer does."""
    _, big_blind = config.blinds
    return BettingRoundState(
        players=tuple(
            PlayerState(
                seat=seat,
                name=seat_label(seat),
                stack=stacks[seat] - committed[seat],
                hole_cards=(),
                committed_total=committed[seat],
                street_bet=0,
                folded=seat in folded,
                all_in=seat in all_in,
            )
            for seat in config.seats
        ),
        current_bet=0,
        min_raise=big_blind,
    )


def snapshot(state: BettingRoundState) -> tuple[dict[int, int], set[int], set[int]]:
    return (
        {player.seat: player.committed_total for player in state.players},
        {player.seat for player in state.players if player.folded},
        {player.seat for player in state.players if player.all_in},
    )


def build_query(
    config: SimulationConfig,
    dealt: Dealt,
    hand_id: str,
    button_seat: int,
    street: StreetName,
    turn: TurnState,
    seat: int,
    board: tuple[Card, ...],
    history: tuple[SeatAction, ...],
) -> StrategyQuery:
    """The Phase 03 decision context for one seat, built from live engine state.

    `current_bet` is the street's current bet level. What hero itself has put in is carried
    on hero's own `seat_states` entry and read from there rather than worked back out of the
    level and the price: `to_call` is capped at what hero holds, so nothing computed from
    those two is hero's contribution.

    Every per-seat figure is `PlayerState`'s own - `street_bet`, `committed_total`, `folded`
    and `all_in`, under the same four names - so nothing here is a reconstruction of what the
    engine already recorded. `pot` is the sum of those hand totals by construction.

    `min_raise_target` is the level plus `min_raise`, which the engine holds at the size of
    the last full bet or raise and at one big blind until something raises.
    """
    state = turn.round
    player = state.player(seat)
    hero = dealt.hole_cards[seat]
    seated = sorted(state.players, key=lambda other: other.seat)
    return StrategyQuery(
        hand_id=hand_id,
        street=street.value,
        seat=seat,
        button_seat=button_seat,
        hole_cards=(str(hero[0]), str(hero[1])),
        board=tuple(card_texts(board)),
        legal_actions=tuple(kind.value for kind in turn.legal_actions(seat)),
        to_call=min(max(0, state.current_bet - player.street_bet), player.stack),
        current_bet=state.current_bet,
        min_raise_target=state.current_bet + state.min_raise,
        pot=sum(other.committed_total for other in seated),
        stacks=tuple((other.seat, other.stack) for other in seated),
        seat_states=tuple(
            SeatState(
                seat=other.seat,
                street_bet=other.street_bet,
                committed_total=other.committed_total,
                folded=other.folded,
                all_in=other.all_in,
            )
            for other in seated
        ),
        blinds=config.blinds,
        preflop_actions=history,
    )
