"""Turning a corpus hand into the Phase 02 normalized schema.

Two things in here are worth more attention than their line count suggests.

The first is the amount conversion. The corpus writes an aggressive action as the
total its actor's street bet reaches; the Phase 02 schema wants a target total for a
`raise` but *added chips* for a `bet` and a `call`. Those are different numbers, and
a converter that copies the corpus figure across produces hands that replay cleanly
and settle to the wrong stacks - the exact failure an outside oracle exists to catch.

The second is `result`. It is built from the corpus's published finishing stacks and
never from our own replay, because `replay_hand` checks the settlement it computes
against `result` and raises when they differ. That check is the oracle. Deriving
`result` from the replay would turn it into a mirror that always agrees.
"""

from __future__ import annotations

from poker_training_bot.data_pipeline.corpus import (
    DEAL_BOARD,
    DEAL_HOLE,
    SHOWDOWN,
    CorpusHand,
)
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
from poker_training_bot.poker_core.cards import Card, parse_cards
from poker_training_bot.poker_core.order import next_seat

SUPPORTED_VARIANT = "NT"
STREET_ORDER = (StreetName.PREFLOP, StreetName.FLOP, StreetName.TURN, StreetName.RIVER)
TABLE_ID = "public-corpus"


class ConversionError(ValueError):
    """A corpus hand this repo cannot express, named rather than skipped."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _button_seat(seat_count: int) -> int:
    """The seat the corpus's blind placement implies.

    The corpus posts the small blind in the first seat and the big blind in the
    second, so the button is the seat immediately before the small blind on the ring.
    Heads-up is different - the button posts the small blind - but that case cannot
    arise here and is refused rather than guessed at.
    """
    if seat_count < 3:
        raise ConversionError(
            f"a {seat_count}-handed corpus hand posts its blinds differently;"
            " this converter only handles three or more seats"
        )
    seats = list(range(seat_count))
    return next_seat(seats, seats[-2])


def _split_board(text: str) -> tuple[Card, ...]:
    return parse_cards(tuple(text[index : index + 2] for index in range(0, len(text), 2)))


def convert_hand(hand: CorpusHand) -> NormalizedHandHistory:
    if hand.variant != SUPPORTED_VARIANT:
        raise ConversionError(
            f"{hand.hand_id}: corpus variant {hand.variant!r} is not no-limit hold'em"
        )

    seat_count = hand.seat_count
    button_seat = _button_seat(seat_count)
    small_blind, big_blind = hand.blinds
    seat_of_player = {f"p{index + 1}": index for index in range(seat_count)}

    streets: list[HistoryStreet] = []
    actions: list[HistoryAction] = [
        HistoryAction(0, HistoryActionKind.POST_BLIND, small_blind),
        HistoryAction(1, HistoryActionKind.POST_BLIND, big_blind),
    ]
    board: tuple[Card, ...] = ()
    street_index = 0
    street_committed = {0: small_blind, 1: big_blind}
    street_bet = big_blind
    total_committed = dict(street_committed)
    folded: set[int] = set()
    showdown_seats: list[int] = []

    def close_street() -> None:
        streets.append(HistoryStreet(STREET_ORDER[street_index], board, tuple(actions)))

    for raw in hand.actions:
        if raw.startswith(DEAL_HOLE):
            continue
        if raw.startswith(DEAL_BOARD):
            close_street()
            street_index += 1
            if street_index >= len(STREET_ORDER):
                raise ConversionError(f"{hand.hand_id}: corpus deals more streets than hold'em has")
            board = _split_board(raw.split()[2])
            actions = []
            street_committed = {}
            street_bet = 0
            continue

        parts = raw.split()
        actor, verb = parts[0], parts[1]
        if verb == SHOWDOWN:
            if seat_of_player[actor] not in showdown_seats:
                showdown_seats.append(seat_of_player[actor])
            continue

        seat = seat_of_player[actor]
        already = street_committed.get(seat, 0)
        if verb == "f":
            folded.add(seat)
            actions.append(HistoryAction(seat, HistoryActionKind.FOLD))
        elif verb == "cc":
            owed = street_bet - already
            if owed == 0:
                actions.append(HistoryAction(seat, HistoryActionKind.CHECK))
            else:
                actions.append(HistoryAction(seat, HistoryActionKind.CALL, owed))
                street_committed[seat] = street_bet
                total_committed[seat] = total_committed.get(seat, 0) + owed
        elif verb == "cbr":
            target = int(parts[2])
            if street_bet > 0:
                actions.append(HistoryAction(seat, HistoryActionKind.RAISE, target))
            else:
                actions.append(HistoryAction(seat, HistoryActionKind.BET, target - already))
            total_committed[seat] = total_committed.get(seat, 0) + (target - already)
            street_committed[seat] = target
            street_bet = target
        else:
            raise ConversionError(f"{hand.hand_id}: unknown corpus action verb {verb!r}")

    close_street()

    live = [seat for seat in range(seat_count) if seat not in folded]
    showdown: tuple[ShowdownEntry, ...] = ()
    if len(live) > 1:
        showdown = tuple(
            ShowdownEntry(seat, parse_cards(hand.hole_cards[seat])) for seat in sorted(live)
        )

    pot = sum(total_committed.values())
    payouts = {
        seat: (
            hand.finishing_stacks[seat]
            - hand.starting_stacks[seat]
            + total_committed.get(seat, 0)
        )
        for seat in range(seat_count)
    }
    if any(amount < 0 for amount in payouts.values()):
        raise ConversionError(
            f"{hand.hand_id}: the published finishing stacks imply a seat paid out less"
            " than nothing, so the action list and the settlement disagree"
        )

    return NormalizedHandHistory(
        schema_version=1,
        hand_id=hand.hand_id,
        table_id=TABLE_ID,
        max_seats=seat_count,
        players=tuple(
            HistoryPlayer(seat, hand.players[seat], hand.starting_stacks[seat])
            for seat in range(seat_count)
        ),
        button_seat=button_seat,
        blinds=BlindStructure(small_blind, big_blind),
        streets=tuple(streets),
        showdown=showdown,
        result=ExpectedResult(
            winner_seats=tuple(seat for seat in sorted(payouts) if payouts[seat] > 0),
            pot=pot,
            payouts=payouts,
        ),
    )
