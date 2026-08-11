from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

DECISION_AUDIT_SCHEMA_VERSION = 1

_STREET_BOARD_SIZES = {
    "preflop": 0,
    "flop": 3,
    "turn": 4,
    "river": 5,
}

_ACTION_NAMES = ("fold", "check", "call", "bet", "raise")
_AMOUNT_ACTIONS = frozenset({"bet", "raise"})

_CARD_RANKS = frozenset("23456789TJQKA")
_CARD_SUITS = frozenset("cdhs")


def _validate_card_text(card: str, context: str) -> None:
    if len(card) != 2 or card[0] not in _CARD_RANKS or card[1] not in _CARD_SUITS:
        raise ValueError(f"{context} contains invalid card text: {card!r}")


_PREFLOP_HISTORY_ACTIONS = ("fold", "check", "call", "raise")


@dataclass(frozen=True)
class SeatAction:
    """One completed action by one seat, as game state rather than as a chart key.

    Seat-based on purpose. Positions are derived from the button, so recording a
    position here would bake a derivation into the raw decision context and give
    two places to disagree about what `CO` means.
    """

    seat: int
    action: str

    def __post_init__(self) -> None:
        if not isinstance(self.seat, int) or isinstance(self.seat, bool) or self.seat < 0:
            raise ValueError(f"seat must be a non-negative integer, got {self.seat!r}")
        if self.action not in _PREFLOP_HISTORY_ACTIONS:
            raise ValueError(
                f"unknown history action {self.action!r};"
                f" expected one of {list(_PREFLOP_HISTORY_ACTIONS)}"
            )

    def to_payload(self) -> dict[str, Any]:
        return {"seat": self.seat, "action": self.action}


@dataclass(frozen=True)
class StrategyQuery:
    """Plain-data decision context handed to a strategy.

    Cards are text strings such as "As" so the query serializes cleanly.

    `preflop_actions` is the history the price to call cannot express. A strategy
    reading a committed chart has to know whether it faces an open, a three-bet, or
    a limp, and `to_call` plus `stacks` cannot distinguish those: several different
    histories produce identical numbers. Defaults to empty, which means the action
    folded to hero.
    """

    hand_id: str
    street: str
    seat: int
    button_seat: int
    hole_cards: tuple[str, str]
    board: tuple[str, ...]
    legal_actions: tuple[str, ...]
    to_call: int
    street_bet: int
    min_raise_target: int
    pot: int
    stacks: tuple[tuple[int, int], ...]
    blinds: tuple[int, int]
    preflop_actions: tuple[SeatAction, ...] = ()

    def __post_init__(self) -> None:
        if not self.hand_id:
            raise ValueError("hand_id is required")
        if self.street not in _STREET_BOARD_SIZES:
            raise ValueError(f"unknown street: {self.street!r}")
        if self.seat < 0:
            raise ValueError("seat must be non-negative")
        if self.button_seat < 0:
            raise ValueError("button_seat must be non-negative")
        if len(self.hole_cards) != 2:
            raise ValueError("exactly two hole cards are required")
        for card in self.hole_cards:
            _validate_card_text(card, "hole_cards")
        expected_board = _STREET_BOARD_SIZES[self.street]
        if len(self.board) != expected_board:
            raise ValueError(
                f"{self.street} requires exactly {expected_board} board cards,"
                f" got {len(self.board)}"
            )
        for card in self.board:
            _validate_card_text(card, "board")
        all_cards = self.hole_cards + self.board
        if len(set(all_cards)) != len(all_cards):
            raise ValueError("duplicate cards across hole_cards and board")
        if not self.legal_actions:
            raise ValueError("legal_actions cannot be empty")
        unknown = [action for action in self.legal_actions if action not in _ACTION_NAMES]
        if unknown:
            raise ValueError(f"unknown legal actions: {unknown}")
        if len(set(self.legal_actions)) != len(self.legal_actions):
            raise ValueError("duplicate legal actions are not allowed")
        if "check" in self.legal_actions and "fold" in self.legal_actions:
            raise ValueError("check and fold can never both be legal")
        if self.to_call < 0:
            raise ValueError("to_call cannot be negative")
        if self.street_bet < 0:
            raise ValueError("street_bet cannot be negative")
        if (self.to_call == 0) != ("check" in self.legal_actions):
            raise ValueError("check must be legal exactly when to_call is zero")
        if self.min_raise_target <= 0:
            raise ValueError("min_raise_target must be positive")
        if self.pot <= 0:
            raise ValueError("pot must be positive")
        previous_seat: int | None = None
        for stack_seat, stack in self.stacks:
            if stack_seat < 0:
                raise ValueError("stack seats must be non-negative")
            if stack < 0:
                raise ValueError("stacks cannot be negative")
            if previous_seat is not None and stack_seat <= previous_seat:
                raise ValueError("stacks must be sorted by seat without duplicates")
            previous_seat = stack_seat
        if self.seat not in {stack_seat for stack_seat, _ in self.stacks}:
            raise ValueError("stacks must include the acting seat")
        small_blind, big_blind = self.blinds
        if small_blind <= 0:
            raise ValueError("small blind must be positive")
        if small_blind > big_blind:
            raise ValueError("small blind cannot exceed big blind")
        if not isinstance(self.preflop_actions, tuple):
            raise ValueError(
                "preflop_actions must be a tuple, got"
                f" {type(self.preflop_actions).__name__}"
            )
        seated = {stack_seat for stack_seat, _ in self.stacks}
        for entry in self.preflop_actions:
            if not isinstance(entry, SeatAction):
                raise ValueError(f"preflop_actions entries must be SeatAction, got {entry!r}")
            if entry.seat not in seated:
                raise ValueError(
                    f"preflop_actions names seat {entry.seat}, which is not at the table"
                )

    def to_payload(self) -> dict[str, Any]:
        return {
            "hand_id": self.hand_id,
            "street": self.street,
            "seat": self.seat,
            "button_seat": self.button_seat,
            "hole_cards": list(self.hole_cards),
            "board": list(self.board),
            "legal_actions": list(self.legal_actions),
            "to_call": self.to_call,
            "street_bet": self.street_bet,
            "min_raise_target": self.min_raise_target,
            "pot": self.pot,
            "stacks": {str(seat): stack for seat, stack in self.stacks},
            "blinds": list(self.blinds),
            "preflop_actions": [entry.to_payload() for entry in self.preflop_actions],
        }


@dataclass(frozen=True)
class StrategyDecision:
    action: str
    amount: int | None
    code: str

    def __post_init__(self) -> None:
        if self.action not in _ACTION_NAMES:
            raise ValueError(f"unknown action: {self.action!r}")
        if not self.code:
            raise ValueError("decision code is required")
        if self.action in _AMOUNT_ACTIONS:
            if self.amount is None or self.amount <= 0:
                raise ValueError(f"{self.action} requires a positive amount")
        elif self.amount is not None:
            raise ValueError(f"{self.action} must not include an amount")


@dataclass(frozen=True)
class StrategyRefusal:
    """Fail-closed outcome: a strategy refuses rather than guesses."""

    code: str

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("refusal code is required")


@runtime_checkable
class StrategyProtocol(Protocol):
    strategy_id: str
    strategy_version: int

    def decide(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal: ...


def _outcome_payload(outcome: StrategyDecision | StrategyRefusal) -> dict[str, Any]:
    if isinstance(outcome, StrategyDecision):
        return {
            "kind": "decision",
            "action": outcome.action,
            "amount": outcome.amount,
            "code": outcome.code,
        }
    if isinstance(outcome, StrategyRefusal):
        return {"kind": "refusal", "code": outcome.code}
    raise ValueError(f"unsupported outcome type: {type(outcome).__name__}")


@dataclass(frozen=True)
class DecisionAuditRecord:
    schema_version: int
    strategy_id: str
    strategy_version: int
    query: StrategyQuery
    outcome: StrategyDecision | StrategyRefusal

    def __post_init__(self) -> None:
        if self.schema_version != DECISION_AUDIT_SCHEMA_VERSION:
            raise ValueError(
                f"only decision-audit schema_version {DECISION_AUDIT_SCHEMA_VERSION} is supported"
            )
        if not self.strategy_id:
            raise ValueError("strategy_id is required")
        if self.strategy_version <= 0:
            raise ValueError("strategy_version must be positive")
        if not isinstance(self.outcome, StrategyDecision | StrategyRefusal):
            raise ValueError(f"unsupported outcome type: {type(self.outcome).__name__}")
        if isinstance(self.outcome, StrategyDecision):
            if self.outcome.action not in self.query.legal_actions:
                raise ValueError(
                    f"decision action {self.outcome.action!r} is not in legal_actions"
                )
            if self.outcome.action in _AMOUNT_ACTIONS:
                stacks = dict(self.query.stacks)
                max_target = self.query.street_bet + stacks[self.query.seat]
                amount = self.outcome.amount
                if amount is None:
                    raise ValueError(f"{self.outcome.action} requires an amount")
                if amount > max_target:
                    raise ValueError(
                        "decision amount exceeds the acting seat's all-in maximum"
                    )
                if amount < self.query.min_raise_target and amount != max_target:
                    raise ValueError(
                        "decision amount is below the minimum unless all-in"
                    )

    def to_json_line(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "query": self.query.to_payload(),
            "outcome": _outcome_payload(self.outcome),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def records_to_jsonl(records: Sequence[DecisionAuditRecord]) -> str:
    if not records:
        return ""
    return "\n".join(record.to_json_line() for record in records) + "\n"
