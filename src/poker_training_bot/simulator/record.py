"""The normalized record of a hand, written as the hand is played.

Kept apart from the play so it is plain that the record is a transcript rather than a
reconstruction. A reconstruction would be a second guess at what happened, and the whole
value of handing these hands back to the Phase 02 replayer is that the record was written by
the thing that did it.

The amounts are the fiddly part and they are not a matter of taste: the replayer's own
`_engine_action` expects a call to carry the chips actually put in and a bet or raise to
carry the level it went to. A strategy's `amount` is None for a call, so that number has to
come from the engine rather than from the decision.
"""

from __future__ import annotations

from poker_training_bot.hand_history.schema import (
    BlindStructure,
    ExpectedResult,
    HistoryAction,
    HistoryActionKind,
    HistoryPlayer,
    HistoryStreet,
    NormalizedHandHistory,
    ShowdownEntry,
    StreetName,
)
from poker_training_bot.poker_core.order import blind_seats
from poker_training_bot.simulator.config import SimulationConfig
from poker_training_bot.simulator.table import seat_label
from poker_training_bot.strategy.contract import StrategyDecision

TABLE_ID = "sim"

_HISTORY_KINDS = {
    "fold": HistoryActionKind.FOLD,
    "check": HistoryActionKind.CHECK,
    "call": HistoryActionKind.CALL,
    "bet": HistoryActionKind.BET,
    "raise": HistoryActionKind.RAISE,
}
_LEVEL_KINDS = frozenset({HistoryActionKind.BET, HistoryActionKind.RAISE})


def history_action(decision: StrategyDecision, seat: int, chips_added: int) -> HistoryAction:
    kind = _HISTORY_KINDS[decision.action]
    if kind is HistoryActionKind.CALL:
        return HistoryAction(seat=seat, kind=kind, amount=chips_added)
    if kind in _LEVEL_KINDS:
        return HistoryAction(seat=seat, kind=kind, amount=decision.amount)
    return HistoryAction(seat=seat, kind=kind)


def blinds_only(config: SimulationConfig, button_seat: int) -> tuple[HistoryStreet, ...]:
    """The preflop street of a hand refused before anybody acted voluntarily."""
    small_blind, big_blind = config.blinds
    sb_seat, bb_seat = blind_seats(config.seats, button_seat)
    return (
        HistoryStreet(
            name=StreetName.PREFLOP,
            board=(),
            actions=(
                HistoryAction(sb_seat, HistoryActionKind.POST_BLIND, small_blind),
                HistoryAction(bb_seat, HistoryActionKind.POST_BLIND, big_blind),
            ),
        ),
    )


def normalized_hand(
    config: SimulationConfig,
    hand_id: str,
    button_seat: int,
    stacks: dict[int, int],
    streets: tuple[HistoryStreet, ...],
    showdown: tuple[ShowdownEntry, ...],
    payouts: dict[int, int],
    pot: int,
) -> NormalizedHandHistory:
    return NormalizedHandHistory(
        schema_version=1,
        hand_id=hand_id,
        table_id=TABLE_ID,
        max_seats=len(config.seats),
        players=tuple(
            HistoryPlayer(
                seat=seat,
                player_id=seat_label(seat),
                starting_stack=stacks[seat],
            )
            for seat in config.seats
        ),
        button_seat=button_seat,
        blinds=BlindStructure(*config.blinds),
        streets=streets,
        showdown=showdown,
        result=ExpectedResult(
            winner_seats=tuple(sorted(seat for seat, paid in payouts.items() if paid > 0)),
            pot=pot,
            # Every seat, including the zeros. `HandReplay.passed_expected_result` compares
            # the settlement's payouts against this dict exactly, and the settlement names
            # every seat at the table.
            payouts=dict(payouts),
        ),
    )
