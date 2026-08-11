from __future__ import annotations

from itertools import combinations

import pytest

from poker_training_bot.poker_core.cards import standard_deck
from poker_training_bot.poker_core.order import blind_seats, next_seat
from poker_training_bot.poker_core.positions import (
    POSITION_LABELS,
    position_for_seat,
    preflop_action_order,
    seat_positions,
    table_positions,
)
from poker_training_bot.solver_artifacts.hand_classes import (
    HAND_CLASSES,
    hand_class,
    hand_class_grid_index,
    is_hand_class,
)

EXPECTED_TABLES: dict[int, tuple[str, ...]] = {
    2: ("BTN", "BB"),
    3: ("BTN", "SB", "BB"),
    4: ("CO", "BTN", "SB", "BB"),
    5: ("HJ", "CO", "BTN", "SB", "BB"),
    6: ("LJ", "HJ", "CO", "BTN", "SB", "BB"),
    7: ("UTG", "LJ", "HJ", "CO", "BTN", "SB", "BB"),
    8: ("UTG", "UTG1", "LJ", "HJ", "CO", "BTN", "SB", "BB"),
    9: ("UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB"),
}

# Deliberately non-contiguous physical seat numbers, to keep ring wraparound honest.
SPARSE_SEATS = (2, 5, 7, 11, 12, 20, 21, 30, 41)


def sparse_seats(table_size: int) -> tuple[int, ...]:
    return SPARSE_SEATS[:table_size]


@pytest.mark.parametrize("table_size", sorted(EXPECTED_TABLES))
def test_table_positions_match_expected_vocabulary(table_size: int) -> None:
    assert table_positions(table_size) == EXPECTED_TABLES[table_size]


def test_position_labels_are_the_nine_handed_table() -> None:
    assert POSITION_LABELS == EXPECTED_TABLES[9]
    assert len(set(POSITION_LABELS)) == len(POSITION_LABELS)


@pytest.mark.parametrize("table_size", sorted(EXPECTED_TABLES))
def test_every_table_uses_only_canonical_labels(table_size: int) -> None:
    labels = table_positions(table_size)
    assert len(set(labels)) == len(labels)
    assert set(labels) <= set(POSITION_LABELS)
    assert labels[-1] == "BB"


@pytest.mark.parametrize("table_size", [-1, 0, 1, 10, 11, 100])
def test_table_positions_rejects_out_of_range_table_size(table_size: int) -> None:
    with pytest.raises(ValueError):
        table_positions(table_size)


@pytest.mark.parametrize("table_size", sorted(EXPECTED_TABLES))
def test_preflop_action_order_is_earliest_to_latest(table_size: int) -> None:
    order = preflop_action_order(table_size)
    assert order == EXPECTED_TABLES[table_size]
    assert order[-1] == "BB"
    if table_size > 2:
        assert order[-2:] == ("SB", "BB")
        assert order[-3] == "BTN"


@pytest.mark.parametrize("table_size", [1, 10])
def test_preflop_action_order_rejects_out_of_range_table_size(table_size: int) -> None:
    with pytest.raises(ValueError):
        preflop_action_order(table_size)


def test_seat_positions_with_contiguous_seats() -> None:
    seats = [0, 1, 2, 3, 4, 5]
    assert seat_positions(seats, button_seat=3) == {
        0: "LJ",
        1: "HJ",
        2: "CO",
        3: "BTN",
        4: "SB",
        5: "BB",
    }
    assert seat_positions(seats, button_seat=5) == {
        0: "SB",
        1: "BB",
        2: "LJ",
        3: "HJ",
        4: "CO",
        5: "BTN",
    }


def test_seat_positions_with_non_contiguous_seats() -> None:
    seats = [2, 5, 7, 11]
    assert seat_positions(seats, button_seat=5) == {2: "CO", 5: "BTN", 7: "SB", 11: "BB"}
    # Button on the highest seat forces the blinds to wrap around the ring.
    assert seat_positions(seats, button_seat=11) == {2: "SB", 5: "BB", 7: "CO", 11: "BTN"}


def test_seat_positions_ignores_input_ordering() -> None:
    ordered = seat_positions([2, 5, 7, 11], button_seat=5)
    shuffled = seat_positions([11, 2, 7, 5], button_seat=5)
    assert shuffled == ordered
    assert list(shuffled) == [2, 5, 7, 11]


def test_seat_positions_heads_up_labels_the_button_as_the_small_blind() -> None:
    assert seat_positions([4, 9], button_seat=9) == {4: "BB", 9: "BTN"}
    assert seat_positions([4, 9], button_seat=4) == {4: "BTN", 9: "BB"}
    small_blind, big_blind = blind_seats([4, 9], 9)
    assert small_blind == 9
    assert big_blind == 4


@pytest.mark.parametrize("table_size", sorted(EXPECTED_TABLES))
def test_seat_positions_agrees_with_blind_seats(table_size: int) -> None:
    seats = sparse_seats(table_size)
    for button_seat in seats:
        assignments = seat_positions(seats, button_seat)
        small_blind, big_blind = blind_seats(seats, button_seat)
        assert set(assignments) == set(seats)
        assert sorted(assignments.values()) == sorted(EXPECTED_TABLES[table_size])
        assert assignments[big_blind] == "BB"
        if table_size == 2:
            assert small_blind == button_seat
            assert assignments[button_seat] == "BTN"
        else:
            assert assignments[small_blind] == "SB"
            assert assignments[button_seat] == "BTN"


@pytest.mark.parametrize("table_size", sorted(EXPECTED_TABLES))
def test_seat_labels_follow_the_ring_in_preflop_order(table_size: int) -> None:
    seats = sparse_seats(table_size)
    expected = preflop_action_order(table_size)
    for button_seat in seats:
        assignments = seat_positions(seats, button_seat)
        first_to_act = next(seat for seat, label in assignments.items() if label == expected[0])
        seat = first_to_act
        walked: list[str] = []
        for _ in range(table_size):
            walked.append(assignments[seat])
            seat = next_seat(seats, seat)
        assert tuple(walked) == expected
        assert seat == first_to_act


def test_seat_positions_is_deterministic() -> None:
    seats = [2, 5, 7, 11, 12]
    assert seat_positions(seats, 7) == seat_positions(seats, 7)


def test_seat_positions_rejects_duplicate_seats() -> None:
    with pytest.raises(ValueError):
        seat_positions([2, 5, 5], button_seat=2)


@pytest.mark.parametrize("seats", [[], [4], list(range(10))])
def test_seat_positions_rejects_unsupported_seat_counts(seats: list[int]) -> None:
    with pytest.raises(ValueError):
        seat_positions(seats, button_seat=0)


def test_seat_positions_rejects_unoccupied_button() -> None:
    with pytest.raises(ValueError):
        seat_positions([2, 5, 7], button_seat=6)


def test_position_for_seat_matches_seat_positions() -> None:
    seats = [2, 5, 7, 11]
    assignments = seat_positions(seats, button_seat=5)
    for seat, label in assignments.items():
        assert position_for_seat(seats, 5, seat) == label


def test_position_for_seat_rejects_unoccupied_seat() -> None:
    with pytest.raises(ValueError):
        position_for_seat([2, 5, 7], button_seat=5, seat=6)


def test_hand_classes_are_the_canonical_169() -> None:
    assert len(HAND_CLASSES) == 169
    assert len(set(HAND_CLASSES)) == 169
    pairs = [text for text in HAND_CLASSES if len(text) == 2]
    suited = [text for text in HAND_CLASSES if text.endswith("s")]
    offsuit = [text for text in HAND_CLASSES if text.endswith("o")]
    assert len(pairs) == 13
    assert len(suited) == 78
    assert len(offsuit) == 78
    for text in ("AA", "AKs", "AKo", "22", "32s", "32o", "A2o"):
        assert text in HAND_CLASSES


def test_hand_class_grid_order_is_documented_and_stable() -> None:
    assert HAND_CLASSES[0] == "AA"
    assert HAND_CLASSES[1] == "AKs"
    assert HAND_CLASSES[13] == "AKo"
    assert HAND_CLASSES[-1] == "22"
    for index, text in enumerate(HAND_CLASSES):
        assert hand_class_grid_index(text) == index


def test_hand_class_grid_index_rejects_unknown_text() -> None:
    for text in ("AKx", "KAo", "AAs", "", "ak s"):
        with pytest.raises(ValueError):
            hand_class_grid_index(text)


def test_hand_class_examples() -> None:
    assert hand_class(("As", "Kd")) == "AKo"
    assert hand_class(("As", "Ks")) == "AKs"
    assert hand_class(("As", "Ad")) == "AA"
    assert hand_class(("2c", "3c")) == "32s"
    assert hand_class(("as", "kD")) == "AKo"


def test_hand_class_covers_every_two_card_combination() -> None:
    deck = standard_deck()
    counts: dict[str, int] = {}
    for first, second in combinations(deck, 2):
        forward = hand_class((str(first), str(second)))
        assert forward == hand_class((str(second), str(first)))
        assert forward in HAND_CLASSES
        counts[forward] = counts.get(forward, 0) + 1
    assert sum(counts.values()) == 1326
    assert set(counts) == set(HAND_CLASSES)
    for text, count in counts.items():
        if len(text) == 2:
            assert count == 6
        elif text.endswith("s"):
            assert count == 4
        else:
            assert count == 12


def test_hand_class_is_suit_independent_beyond_suitedness() -> None:
    for high, low in (("A", "K"), ("T", "9"), ("7", "2"), ("K", "Q")):
        suited = {hand_class((f"{high}{suit}", f"{low}{suit}")) for suit in "cdhs"}
        assert suited == {f"{high}{low}s"}
        offsuit = {
            hand_class((f"{high}{first}", f"{low}{second}"))
            for first in "cdhs"
            for second in "cdhs"
            if first != second
        }
        assert offsuit == {f"{high}{low}o"}


@pytest.mark.parametrize(
    "hole_cards",
    [
        (),
        ("As",),
        ("As", "Kd", "Qh"),
        ("As", "As"),
        ("Xs", "Kd"),
        ("Ax", "Kd"),
        ("A", "Kd"),
        ("Asx", "Kd"),
    ],
)
def test_hand_class_rejects_bad_input(hole_cards: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        hand_class(hole_cards)


@pytest.mark.parametrize("text", ["AA", "AKs", "AKo", "22", "32s", "32o"])
def test_is_hand_class_accepts_canonical_classes(text: str) -> None:
    assert is_hand_class(text) is True


@pytest.mark.parametrize(
    "text",
    ["AKx", "ka s", "KAo", "AAs", "AAo", "", "aks", "AKS", "AK", "AKoo", "A", "XYs"],
)
def test_is_hand_class_rejects_non_classes(text: str) -> None:
    assert is_hand_class(text) is False


@pytest.mark.parametrize("value", [None, 5, 3.5, ("AA",), ["AA"], {"AA": 1}, object()])
def test_is_hand_class_survives_non_string_input(value: object) -> None:
    assert is_hand_class(value) is False  # type: ignore[arg-type]
