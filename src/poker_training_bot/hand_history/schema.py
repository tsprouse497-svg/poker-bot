from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from poker_training_bot.poker_core.cards import Card, parse_cards, validate_unique_cards
from poker_training_bot.poker_core.engine import validate_player_count


class StreetName(StrEnum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


STREET_BOARD_CARDS = {
    StreetName.PREFLOP: 0,
    StreetName.FLOP: 3,
    StreetName.TURN: 1,
    StreetName.RIVER: 1,
}


class HistoryActionKind(StrEnum):
    POST_BLIND = "post_blind"
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"


@dataclass(frozen=True)
class HistoryPlayer:
    seat: int
    player_id: str
    starting_stack: int

    def __post_init__(self) -> None:
        if self.seat < 0:
            raise ValueError("player seat must be non-negative")
        if not self.player_id:
            raise ValueError("player_id is required")
        if self.starting_stack <= 0:
            raise ValueError("starting_stack must be positive")


@dataclass(frozen=True)
class BlindStructure:
    small_blind: int
    big_blind: int

    def __post_init__(self) -> None:
        if self.small_blind <= 0:
            raise ValueError("small_blind must be positive")
        if self.big_blind <= 0:
            raise ValueError("big_blind must be positive")
        if self.small_blind > self.big_blind:
            raise ValueError("small_blind cannot exceed big_blind")


@dataclass(frozen=True)
class HistoryAction:
    seat: int
    kind: HistoryActionKind
    amount: int | None = None

    def __post_init__(self) -> None:
        if self.seat < 0:
            raise ValueError("action seat must be non-negative")
        if self.kind in {
            HistoryActionKind.POST_BLIND,
            HistoryActionKind.CALL,
            HistoryActionKind.BET,
            HistoryActionKind.RAISE,
        }:
            if self.amount is None or self.amount <= 0:
                raise ValueError(f"{self.kind.value} requires a positive amount")
        elif self.amount is not None:
            raise ValueError(f"{self.kind.value} must not include an amount")

    @property
    def committed_amount(self) -> int:
        if self.kind in {
            HistoryActionKind.POST_BLIND,
            HistoryActionKind.CALL,
            HistoryActionKind.BET,
            HistoryActionKind.RAISE,
        }:
            if self.amount is None:
                raise ValueError(f"{self.kind.value} requires an amount")
            return self.amount
        return 0


@dataclass(frozen=True)
class HistoryStreet:
    name: StreetName
    board: tuple[Card, ...]
    actions: tuple[HistoryAction, ...]


@dataclass(frozen=True)
class ShowdownEntry:
    seat: int
    hole_cards: tuple[Card, Card]

    def __post_init__(self) -> None:
        if self.seat < 0:
            raise ValueError("showdown seat must be non-negative")
        if len(self.hole_cards) != 2:
            raise ValueError("showdown entries require exactly two hole cards")
        validate_unique_cards(self.hole_cards)


@dataclass(frozen=True)
class ExpectedResult:
    winner_seats: tuple[int, ...]
    pot: int
    payouts: dict[int, int]

    def __post_init__(self) -> None:
        if self.pot < 0:
            raise ValueError("result pot cannot be negative")
        if any(seat < 0 for seat in self.winner_seats):
            raise ValueError("winner seats must be non-negative")
        if len(set(self.winner_seats)) != len(self.winner_seats):
            raise ValueError("duplicate winner seats are not allowed")
        if any(amount < 0 for amount in self.payouts.values()):
            raise ValueError("payout amounts cannot be negative")
        if sum(self.payouts.values()) != self.pot:
            raise ValueError("result payouts must sum to result pot")


@dataclass(frozen=True)
class NormalizedHandHistory:
    schema_version: int
    hand_id: str
    table_id: str
    max_seats: int
    players: tuple[HistoryPlayer, ...]
    button_seat: int
    blinds: BlindStructure
    streets: tuple[HistoryStreet, ...]
    showdown: tuple[ShowdownEntry, ...]
    result: ExpectedResult

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("only hand-history schema_version 1 is supported")
        if not self.hand_id:
            raise ValueError("hand_id is required")
        if not self.table_id:
            raise ValueError("table_id is required")
        if self.max_seats < 2 or self.max_seats > 9:
            raise ValueError("max_seats must be between two and nine")
        validate_player_count(self.players)
        seats = {player.seat for player in self.players}
        if any(seat >= self.max_seats for seat in seats):
            raise ValueError("player seat cannot exceed max_seats")
        if self.button_seat not in seats:
            raise ValueError("button_seat must belong to a player")
        if len({player.player_id for player in self.players}) != len(self.players):
            raise ValueError("duplicate player_id values are not allowed")
        if not self.streets:
            raise ValueError("at least one street is required")
        expected_names = list(StreetName)[: len(self.streets)]
        if [street.name for street in self.streets] != expected_names:
            raise ValueError("streets must run preflop, flop, turn, river without gaps")
        for street in self.streets:
            expected_cards = STREET_BOARD_CARDS[street.name]
            if len(street.board) != expected_cards:
                raise ValueError(
                    f"{street.name.value} street must deal exactly {expected_cards} board cards"
                )
        action_seats = {action.seat for street in self.streets for action in street.actions}
        unknown_action_seats = action_seats - seats
        if unknown_action_seats:
            raise ValueError(f"actions reference unknown seats: {sorted(unknown_action_seats)}")
        showdown_seats = {entry.seat for entry in self.showdown}
        unknown_showdown_seats = showdown_seats - seats
        if unknown_showdown_seats:
            raise ValueError(f"showdown references unknown seats: {sorted(unknown_showdown_seats)}")
        if len(showdown_seats) != len(self.showdown):
            raise ValueError("duplicate showdown seats are not allowed")
        result_seats = set(self.result.winner_seats) | set(self.result.payouts)
        unknown_result_seats = result_seats - seats
        if unknown_result_seats:
            raise ValueError(f"result references unknown seats: {sorted(unknown_result_seats)}")
        showdown_cards = tuple(card for entry in self.showdown for card in entry.hole_cards)
        validate_unique_cards(self.board + showdown_cards)

    @property
    def board(self) -> tuple[Card, ...]:
        return tuple(card for street in self.streets for card in street.board)


def load_hand_history_file(path: Path) -> tuple[NormalizedHandHistory, ...]:
    if path.suffix == ".jsonl":
        return tuple(
            parse_hand_history(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "hands" in payload:
            _require_keys(payload, "hand-history bundle", {"hands"})
            hands = _require_list(payload, "hands")
            return tuple(parse_hand_history(hand) for hand in hands)
        return (parse_hand_history(payload),)
    raise ValueError(f"unsupported hand-history file extension: {path.suffix}")


def parse_hand_history(raw: Any) -> NormalizedHandHistory:
    payload = _require_mapping(raw, "hand")
    _require_keys(
        payload,
        "hand",
        {
            "schema_version",
            "hand_id",
            "table",
            "players",
            "button_seat",
            "blinds",
            "streets",
            "showdown",
            "result",
        },
    )
    table = _require_mapping(payload.get("table"), "table")
    _require_keys(table, "table", {"table_id", "max_seats"})
    return NormalizedHandHistory(
        schema_version=_require_int(payload, "schema_version"),
        hand_id=_require_str(payload, "hand_id"),
        table_id=_require_str(table, "table_id"),
        max_seats=_require_int(table, "max_seats"),
        players=tuple(_parse_player(item) for item in _require_list(payload, "players")),
        button_seat=_require_int(payload, "button_seat"),
        blinds=_parse_blinds(_require_mapping(payload.get("blinds"), "blinds")),
        streets=tuple(_parse_street(item) for item in _require_list(payload, "streets")),
        showdown=tuple(_parse_showdown(item) for item in _require_list(payload, "showdown")),
        result=_parse_result(_require_mapping(payload.get("result"), "result")),
    )


def _parse_player(raw: Any) -> HistoryPlayer:
    payload = _require_mapping(raw, "player")
    _require_keys(payload, "player", {"seat", "player_id", "starting_stack"})
    return HistoryPlayer(
        seat=_require_int(payload, "seat"),
        player_id=_require_str(payload, "player_id"),
        starting_stack=_require_int(payload, "starting_stack"),
    )


def _parse_blinds(payload: dict[str, Any]) -> BlindStructure:
    _require_keys(payload, "blinds", {"small_blind", "big_blind"})
    return BlindStructure(
        small_blind=_require_int(payload, "small_blind"),
        big_blind=_require_int(payload, "big_blind"),
    )


def _parse_street(raw: Any) -> HistoryStreet:
    payload = _require_mapping(raw, "street")
    _require_keys(payload, "street", {"name", "board", "actions"})
    return HistoryStreet(
        name=StreetName(_require_str(payload, "name")),
        board=parse_cards(_require_str_list(payload, "board")),
        actions=tuple(_parse_action(item) for item in _require_list(payload, "actions")),
    )


def _parse_action(raw: Any) -> HistoryAction:
    payload = _require_mapping(raw, "action")
    _require_keys(payload, "action", {"seat", "kind"}, {"amount"})
    return HistoryAction(
        seat=_require_int(payload, "seat"),
        kind=HistoryActionKind(_require_str(payload, "kind")),
        amount=_optional_int(payload, "amount"),
    )


def _parse_showdown(raw: Any) -> ShowdownEntry:
    payload = _require_mapping(raw, "showdown")
    _require_keys(payload, "showdown", {"seat", "hole_cards"})
    cards = parse_cards(_require_str_list(payload, "hole_cards"))
    if len(cards) != 2:
        raise ValueError("showdown entries require exactly two hole cards")
    return ShowdownEntry(seat=_require_int(payload, "seat"), hole_cards=(cards[0], cards[1]))


def _parse_result(payload: dict[str, Any]) -> ExpectedResult:
    _require_keys(payload, "result", {"winner_seats", "pot", "payouts"})
    payout_items = tuple(
        _require_mapping(payout, "payout")
        for payout in _require_list(payload, "payouts")
    )
    for payout in payout_items:
        _require_keys(payout, "payout", {"seat", "amount"})
    payout_seats = [_require_int(payout, "seat") for payout in payout_items]
    if len(set(payout_seats)) != len(payout_seats):
        raise ValueError("duplicate payout seats are not allowed")
    winner_seats = _require_list(payload, "winner_seats")
    return ExpectedResult(
        winner_seats=tuple(_require_int({"seat": seat}, "seat") for seat in winner_seats),
        pot=_require_int(payload, "pot"),
        payouts={
            _require_int(payout, "seat"): _require_int(payout, "amount")
            for payout in payout_items
        },
    )


def _require_mapping(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{name} must be an object")
    return raw


def _require_keys(
    payload: dict[str, Any],
    name: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = set() if optional is None else optional
    keys = set(payload)
    missing = required - keys
    if missing:
        raise ValueError(f"{name} missing required keys: {sorted(missing)}")
    unknown = keys - required - optional
    if unknown:
        raise ValueError(f"{name} contains unknown keys: {sorted(unknown)}")


def _require_list(payload: dict[str, Any], key: str) -> list[Any]:
    raw = payload.get(key)
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a list")
    return raw


def _require_str_list(payload: dict[str, Any], key: str) -> list[str]:
    raw = _require_list(payload, key)
    if not all(isinstance(item, str) for item in raw):
        raise ValueError(f"{key} must be a list of strings")
    return raw


def _require_str(payload: dict[str, Any], key: str) -> str:
    raw = payload.get(key)
    if not isinstance(raw, str):
        raise ValueError(f"{key} must be a string")
    return raw


def _require_int(payload: dict[str, Any], key: str) -> int:
    raw = payload.get(key)
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise ValueError(f"{key} must be an integer")
    return raw


def _optional_int(payload: dict[str, Any], key: str) -> int | None:
    if key not in payload:
        return None
    return _require_int(payload, key)
