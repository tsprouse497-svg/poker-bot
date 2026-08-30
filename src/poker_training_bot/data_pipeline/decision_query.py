"""Turning a replayed decision point into a query the strategy can answer.

Two vocabularies meet here and neither belongs to the other. The frozen Phase 02 replayer
speaks in `HistoryActionKind` and `PlayerState`; the strategy contract speaks in action
names, seat states and a bet level. This module is the one translation between them, and it
lives on its own because three callers need it - the real-hand comparison, phase 13's
table-state measures, and the table-state report - and none of them owns it.

Its rule is that nothing is re-derived. Every per-seat figure is the engine's own, under the
engine's own names, so a decision the comparison scores is the decision the replayer saw and
not a reconstruction that agrees with it most of the time. The one number that is computed
rather than copied is `to_call`, and it is capped at what hero actually holds, per Taylor's
ruling of 2026-08-20.
"""

from __future__ import annotations

from poker_training_bot.hand_history.replay import DecisionPoint
from poker_training_bot.hand_history.schema import HistoryActionKind, StreetName
from poker_training_bot.strategy.contract import SeatAction, SeatState, StrategyQuery

KIND_TO_ACTION = {
    HistoryActionKind.FOLD: "fold",
    HistoryActionKind.CHECK: "check",
    HistoryActionKind.CALL: "call",
    HistoryActionKind.BET: "bet",
    HistoryActionKind.RAISE: "raise",
}


def query_for(point: DecisionPoint, hole_cards: tuple[str, str]) -> StrategyQuery | None:
    """Rebuild the decision context the acting seat faced, or None if it is not one.

    Everything but the hole cards comes from the replayer's own turn state, so the
    query describes the hand as the frozen Phase 02 replayer understands it rather
    than as this module re-derives it.
    """
    if point.street is not StreetName.PREFLOP:
        return None
    if point.action.kind is HistoryActionKind.POST_BLIND:
        return None
    state = point.turn.round
    hero = state.player(point.seat)
    seated = sorted(state.players, key=lambda player: player.seat)
    stacks = tuple((player.seat, player.stack) for player in seated)
    legal = tuple(kind.value for kind in point.legal_actions)
    seen: list[SeatAction] = []
    for action in point.hand.streets[0].actions:
        if action.kind is HistoryActionKind.POST_BLIND:
            continue
        if action is point.action:
            break
        # A raise carries its raise-to target, which is what `HistoryAction.amount`
        # already holds for a raise; every other kind carries nothing. Without it the
        # chart cannot tell a 2.25bb open from the 2.5bb one it was solved against,
        # which is the whole of `RAISE-SIZE-IN-SPOT-KEY`.
        raised = action.kind is HistoryActionKind.RAISE
        seen.append(
            SeatAction(
                action.seat,
                KIND_TO_ACTION[action.kind],
                action.amount if raised else None,
            )
        )
    return StrategyQuery(
        hand_id=point.hand.hand_id,
        street="preflop",
        seat=point.seat,
        button_seat=point.hand.button_seat,
        hole_cards=hole_cards,
        board=(),
        legal_actions=legal,
        # The price hero can actually pay, capped at what hero holds.
        to_call=min(max(0, state.current_bet - hero.street_bet), hero.stack),
        # The street's bet level. What hero itself put in is carried on hero's own seat
        # record below and read from there, never worked back out of the level and the
        # capped price. Every per-seat figure is `PlayerState`'s own, under the engine's
        # own four names, so the replayed hand is reported rather than reconstructed.
        current_bet=state.current_bet,
        min_raise_target=state.current_bet + state.min_raise,
        pot=sum(player.committed_total for player in seated),
        stacks=stacks,
        seat_states=tuple(
            SeatState(
                seat=player.seat,
                street_bet=player.street_bet,
                committed_total=player.committed_total,
                folded=player.folded,
                all_in=player.all_in,
            )
            for player in seated
        ),
        blinds=(point.hand.blinds.small_blind, point.hand.blinds.big_blind),
        preflop_actions=tuple(seen),
    )
