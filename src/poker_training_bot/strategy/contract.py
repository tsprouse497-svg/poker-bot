from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

# Version 3 carries each seat's own contributions and its folded and all-in markers, and
# renames the bet-level key from `street_bet` to `current_bet`. Version 2 bytes and version 3
# bytes would otherwise be indistinguishable at an unchanged version number, which is the
# defect `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS` already records once.
DECISION_AUDIT_SCHEMA_VERSION = 3

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

    A raise carries the amount it raised *to*, in chips, which is the unit the hand
    history and the engine already use; converting to big blinds is the chart layer's
    job and it needs the blinds to do it. Without this a size-aware spot key cannot be
    derived at all, because the history is where the price in front of hero lives.
    Every other action carries nothing: a call pays the level the preceding raise
    states, and a fold and a check pay nothing.
    """

    seat: int
    action: str
    amount: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.seat, int) or isinstance(self.seat, bool) or self.seat < 0:
            raise ValueError(f"seat must be a non-negative integer, got {self.seat!r}")
        if self.action not in _PREFLOP_HISTORY_ACTIONS:
            raise ValueError(
                f"unknown history action {self.action!r};"
                f" expected one of {list(_PREFLOP_HISTORY_ACTIONS)}"
            )
        if self.action == "raise":
            if (
                self.amount is None
                or isinstance(self.amount, bool)
                or not isinstance(self.amount, int)
                or self.amount <= 0
            ):
                raise ValueError(
                    "a recorded raise requires the positive raise-to amount in chips,"
                    f" got {self.amount!r}"
                )
        elif self.amount is not None:
            raise ValueError(f"a recorded {self.action} must not carry an amount")

    def to_payload(self) -> dict[str, Any]:
        return {"seat": self.seat, "action": self.action, "amount": self.amount}


@dataclass(frozen=True)
class SeatState:
    """One seated player's chips and status, under the engine's own four names.

    `PlayerState` already tracks exactly these quantities under exactly these names, so the
    repo holds one vocabulary instead of a translation at the boundary. `street_bet` is this
    seat's own share of the street's `current_bet`; `committed_total` is what it has put in
    over the whole hand, which is what the pot is made of. Neither takes a default, because
    a default is how a producer that never learned about the field still constructs.

    `folded` and `all_in` are carried rather than derived: a folded seat's chips stay in the
    pot, so no arithmetic tells it from a live one, and a zero stack means all-in, all-in on
    an earlier street, or a seat that sat down with nothing.
    """

    seat: int
    street_bet: int
    committed_total: int
    folded: bool = False
    all_in: bool = False

    def __post_init__(self) -> None:
        for name in ("seat", "street_bet", "committed_total"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
        if self.committed_total < self.street_bet:
            # The one direction no street allows. The other is that seat's dead money, which
            # is what an ante is, so equality is not required even preflop. It belongs here
            # rather than on the query: a record that cannot exist should not construct.
            raise ValueError(
                f"seat_state for seat {self.seat} holds {self.street_bet} on this street"
                f" and {self.committed_total} over the hand, which cannot happen"
            )


@dataclass(frozen=True)
class StrategyQuery:
    """Plain-data decision context handed to a strategy.

    Cards are text strings such as "As" so the query serializes cleanly.

    `current_bet` is the street's **current bet level** - the amount a seat must have in
    front of it to be square with the action. The per-seat `street_bet` on `seat_states` is
    one seat's own share of that level, under the engine's own name for it. Until this field
    was renamed one name carried both readings, which is how `STREET-BET-MEANING-AMBIGUOUS`
    happened: two consumers read it two ways and hands reached the chart mis-derived.

    `seat_states` says what every seated player has put in, on this street and over the hand,
    and whether it has folded or is all-in. Required with no default: a field a producer may
    omit is one the depth derivation guesses behind. `pot` is validated against it rather
    than trusted, and hero's own contribution is read out of it rather than reconstructed,
    because the capped-`to_call` ruling of 2026-08-20 made every reconstruction wrong.

    `preflop_actions` is the history the price to call cannot express: a strategy reading a
    committed chart has to know whether it faces an open, a three-bet or a limp, and `to_call`
    plus `stacks` cannot distinguish those. Defaults to empty, meaning the action folded to
    hero. Each recorded raise carries the amount it raised to, because a spot key telling a
    2.25bb open from a 2.5bb one cannot come from a history without the price in it.
    """

    hand_id: str
    street: str
    seat: int
    button_seat: int
    hole_cards: tuple[str, str]
    board: tuple[str, ...]
    legal_actions: tuple[str, ...]
    to_call: int
    current_bet: int
    min_raise_target: int
    pot: int
    stacks: tuple[tuple[int, int], ...]
    seat_states: tuple[SeatState, ...]
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
        # There is deliberately no rule that `check` and `fold` cannot both be legal. The
        # engine offers a fold wherever a seat may act, including where checking is free,
        # so a query refusing to describe that set would be a query that lies about the
        # game. Phase 11's contract names this as the single validation it may remove.
        if self.to_call < 0:
            raise ValueError("to_call cannot be negative")
        if self.current_bet < 0:
            raise ValueError("current_bet cannot be negative")
        if self.current_bet < self.to_call:
            # The price to call cannot exceed the level being called, so a producer passing
            # one seat's own share as the level trips this whenever that share is the smaller.
            raise ValueError(
                f"current_bet {self.current_bet} is below to_call {self.to_call};"
                " current_bet is the street's bet level, not one seat's share of it"
            )
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
        seated = {stack_seat for stack_seat, _ in self.stacks}
        if self.seat not in seated:
            raise ValueError("stacks must include the acting seat")
        hero_stack = dict(self.stacks)[self.seat]
        if self.to_call > hero_stack:
            raise ValueError(
                f"to_call {self.to_call} exceeds hero's stack of {hero_stack};"
                " to_call is the price hero can actually pay, capped at what hero holds"
            )
        aggressive = tuple(name for name in self.legal_actions if name in _AMOUNT_ACTIONS)
        if self.to_call == hero_stack and aggressive:
            # Hero is all-in for the call and has nothing left to put in behind it. At a
            # price of zero this is the seat with an empty stack, which cannot bet either.
            raise ValueError(
                f"hero holds {hero_stack} and owes {self.to_call}, so it is all-in for the"
                f" call; {' and '.join(aggressive)} cannot be offered"
            )
        if not isinstance(self.seat_states, tuple):
            raise ValueError(f"seat_states must be a tuple, got {type(self.seat_states).__name__}")
        contributed_total = 0
        previous_state_seat: int | None = None
        for state in self.seat_states:
            if not isinstance(state, SeatState):
                raise ValueError(f"seat_states entries must be SeatState, got {state!r}")
            if previous_state_seat is not None and state.seat <= previous_state_seat:
                raise ValueError("seat_states must be sorted by seat without duplicates")
            previous_state_seat = state.seat
            contributed_total += state.committed_total
        if {state.seat for state in self.seat_states} != seated:
            raise ValueError(
                "seat_states needs exactly one entry per seat in stacks, got"
                f" {sorted(state.seat for state in self.seat_states)} against {sorted(seated)}"
            )
        if self.pot != contributed_total:
            raise ValueError(
                f"pot {self.pot} is not the {contributed_total} the seats put in;"
                " chips in must equal chips out, and dropping a folded seat is how that stops"
            )
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
            "current_bet": self.current_bet,
            "min_raise_target": self.min_raise_target,
            "pot": self.pot,
            "stacks": {str(seat): stack for seat, stack in self.stacks},
            # Keyed by seat exactly as `stacks` is, the field it is validated against seat
            # for seat. The inner object does not repeat the seat: that is where drift starts.
            "seat_states": {
                str(state.seat): {
                    "street_bet": state.street_bet,
                    "committed_total": state.committed_total,
                    "folded": state.folded,
                    "all_in": state.all_in,
                }
                for state in self.seat_states
            },
            "blinds": list(self.blinds),
            "preflop_actions": [entry.to_payload() for entry in self.preflop_actions],
        }


def _validate_detail(detail: tuple[tuple[str, str], ...], noun: str) -> None:
    """The shape both outcomes use for structured detail.

    Ordered pairs rather than a mapping, because the record has to serialize to
    identical bytes on every run and an ordering that is explicit cannot drift.
    """
    if not isinstance(detail, tuple):
        raise ValueError(f"{noun} detail must be a tuple, got {type(detail).__name__}")
    for entry in detail:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise ValueError(f"{noun} detail entries must be name/value pairs, got {entry!r}")
        name, value = entry
        if not isinstance(name, str) or not name:
            raise ValueError(f"{noun} detail names must be non-empty strings, got {name!r}")
        if not isinstance(value, str):
            raise ValueError(f"{noun} detail values must be strings, got {value!r}")
    names = [name for name, _ in detail]
    if len(set(names)) != len(names):
        raise ValueError(f"{noun} detail names must be unique, got {names}")


@dataclass(frozen=True)
class StrategyDecision:
    """An action a strategy is willing to take, and anything qualifying it.

    `detail` is the same ordered, structured shape `StrategyRefusal` already carries,
    on the branch that answers rather than the branch that declines. It exists because
    an answer can be exact or substituted - the chart holds the spot but not at the
    price that was asked - and a report that cannot tell those apart silently mixes
    them into every rate it computes. An exact answer carries no detail at all, so the
    absence is as informative as the presence.

    The alternative was a flag inside the rationale string, which makes every consumer
    parse a private format to find out whether a number is exact; the Phase 03 contract
    already had to fix that once.
    """

    action: str
    amount: int | None
    code: str
    detail: tuple[tuple[str, str], ...] = ()

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
        _validate_detail(self.detail, "decision")

    def named(self, name: str) -> str | None:
        """One detail value by name, or None."""
        for entry_name, value in self.detail:
            if entry_name == name:
                return value
        return None


@dataclass(frozen=True)
class StrategyRefusal:
    """Fail-closed outcome: a strategy refuses rather than guesses.

    Two fields, doing two different jobs. `code` is a stable vocabulary naming the *kind*
    of miss, so refusals group and count. `detail` names the specific thing that could not
    be found, so they can be acted on.

    The split exists because a count of refusals is not a work list. A phase that measures
    coverage can report that a chart was silent forty times; closing the gap needs to know
    which forty spots. Before this field the only trace of that was the action sequence
    that led to the refusal, which put the burden on every caller to preserve it - and the
    Phase 07 simulator did not, which is how 565 actions across 128 hands went missing.

    Ordered pairs rather than a mapping, because the record has to serialize to identical
    bytes on every run and an ordering that is explicit cannot drift. Empty by default, so
    a refusal with nothing useful to add stays exactly as simple as it was.
    """

    code: str
    detail: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("refusal code is required")
        _validate_detail(self.detail, "refusal")

    def named(self, name: str) -> str | None:
        """One detail value by name, or None.

        A reader wanting the spot key should not have to know where in the sequence it
        sits, and a producer should be free to add a field without moving another one.
        """
        for entry_name, value in self.detail:
            if entry_name == name:
                return value
        return None


@runtime_checkable
class StrategyProtocol(Protocol):
    strategy_id: str
    strategy_version: int

    def decide(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal: ...


def _outcome_payload(outcome: StrategyDecision | StrategyRefusal) -> dict[str, Any]:
    if isinstance(outcome, StrategyDecision):
        decision: dict[str, Any] = {
            "kind": "decision",
            "action": outcome.action,
            "amount": outcome.amount,
            "code": outcome.code,
        }
        if outcome.detail:
            # Only when there is something to say, so an exact answer and a substituted
            # one differ in the bytes rather than in a field that is always present and
            # usually empty.
            decision["detail"] = [list(entry) for entry in outcome.detail]
        return decision
    if isinstance(outcome, StrategyRefusal):
        payload: dict[str, Any] = {"kind": "refusal", "code": outcome.code}
        if outcome.detail:
            # Only when there is something to say, so every audit line written before this
            # field existed still serializes to the bytes it did before.
            payload["detail"] = [list(entry) for entry in outcome.detail]
        return payload
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
                # Hero's own recorded contribution to the street plus what is left behind
                # it, read off hero's seat record. The chart's old ceiling used the street's
                # whole level and accepted raises hero could not make.
                hero = next(s for s in self.query.seat_states if s.seat == self.query.seat)
                max_target = hero.street_bet + stacks[self.query.seat]
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
