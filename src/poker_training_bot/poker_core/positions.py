"""Canonical position vocabulary.

This module is the only source of position names in the repo. Every chart,
artifact, report, and strategy layer spells positions the way `POSITION_LABELS`
spells them.
"""

from __future__ import annotations

from collections.abc import Sequence

from poker_training_bot.poker_core.order import blind_seats, next_seat

MIN_TABLE_SIZE = 2
MAX_TABLE_SIZE = 9

POSITION_LABELS: tuple[str, ...] = (
    "UTG",
    "UTG1",
    "UTG2",
    "LJ",
    "HJ",
    "CO",
    "BTN",
    "SB",
    "BB",
)

_HEADS_UP_LABELS: tuple[str, ...] = ("BTN", "BB")
_BLIND_LABELS: tuple[str, ...] = ("SB", "BB")
_LATE_LABELS_BUTTON_FIRST: tuple[str, ...] = ("BTN", "CO", "HJ", "LJ")
_EARLY_LABELS: tuple[str, ...] = ("UTG", "UTG1", "UTG2")


def _validated_table_size(table_size: int) -> int:
    if table_size < MIN_TABLE_SIZE or table_size > MAX_TABLE_SIZE:
        raise ValueError(f"table size must be between two and nine seats: {table_size}")
    return table_size


def table_positions(table_size: int) -> tuple[str, ...]:
    """Positions present at a table of `table_size` seats, in preflop action order.

    Non-blind positions are filled from the button backwards (`BTN`, `CO`, `HJ`,
    `LJ`) and the under-the-gun run (`UTG`, `UTG1`, `UTG2`) is added ahead of
    them as the table grows. The blinds are appended last, because they act last
    on the first preflop orbit. Heads-up is special: the button posts the small
    blind, so the table is `("BTN", "BB")`.
    """
    size = _validated_table_size(table_size)
    if size == MIN_TABLE_SIZE:
        return _HEADS_UP_LABELS
    non_blind = size - len(_BLIND_LABELS)
    late = tuple(reversed(_LATE_LABELS_BUTTON_FIRST[:non_blind]))
    early_count = max(non_blind - len(_LATE_LABELS_BUTTON_FIRST), 0)
    return _EARLY_LABELS[:early_count] + late + _BLIND_LABELS


def preflop_action_order(table_size: int) -> tuple[str, ...]:
    """Order the positions act in on the first preflop orbit.

    This currently equals `table_positions`, which is ordered earliest-to-latest
    preflop on purpose. It stays a separate function because postflop order is
    different (the blinds act first once the flop is out), so later phases need
    to ask for the preflop order by name rather than assume the seating order.
    """
    return table_positions(table_size)


def seat_positions(seats: Sequence[int], button_seat: int) -> dict[int, str]:
    """Map each occupied seat to its position label.

    Seats are physical seat numbers, not indices. They form a ring in ascending
    numeric order with wraparound, exactly like `poker_core.order.next_seat`.
    Blind seats come from `poker_core.order.blind_seats` so the blind rules are
    never restated here. Labels are assigned by walking the ring forward from
    the seat after the big blind, which is the same thing as walking backwards
    from the button through `table_positions`.

    The returned mapping is keyed in ascending seat order regardless of the
    order the seats were passed in.
    """
    _, big_blind = blind_seats(seats, button_seat)
    ordered = tuple(sorted(seats))
    labels = table_positions(len(ordered))
    assignments: dict[int, str] = {}
    seat = next_seat(ordered, big_blind)
    for label in labels:
        assignments[seat] = label
        seat = next_seat(ordered, seat)
    return {occupied: assignments[occupied] for occupied in ordered}


def position_for_seat(seats: Sequence[int], button_seat: int, seat: int) -> str:
    """Position label for one occupied seat."""
    assignments = seat_positions(seats, button_seat)
    if seat not in assignments:
        raise ValueError(f"seat {seat} is not an occupied seat")
    return assignments[seat]
