"""Committed preflop artifact schema and the canonical spot key.

The spot key is derived here and nowhere else. The importer stamps artifacts with
it and the chart lookup rebuilds it from game state, so a spot that imports is
reachable by a lookup.

Folds never appear in a spot's action sequence. A folded position carries no
information beyond its absence, so an empty sequence means "folded to hero"
(RFI) and every recorded entry is live aggression or a call.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from hashlib import sha256
from typing import Any

from poker_training_bot.poker_core.positions import (
    POSITION_LABELS,
    preflop_action_order,
    table_positions,
)
from poker_training_bot.solver_artifacts.hand_classes import (
    hand_class_grid_index,
    is_hand_class,
)

ARTIFACT_SCHEMA_VERSION = 1
WEIGHT_SUM_TOLERANCE = 1e-6
PREFLOP_ACTIONS = ("fold", "check", "call", "raise")
# A recorded sequence entry can only be a call or a raise. Preflop everyone faces
# the big blind, so the only seat that can check is the big blind, and its check
# ends the betting round. A check can therefore never precede hero's decision.
SEQUENCE_ACTIONS = ("call", "raise")
ARTIFACT_SOURCE_KINDS = ("solver-export", "hand-authored")

MIN_TABLE_SIZE = 2
MAX_TABLE_SIZE = 9

ActionWeights = tuple[tuple[str, float], ...]
HandClassWeights = tuple[tuple[str, ActionWeights], ...]
SpotActionWeights = tuple[tuple[str, HandClassWeights], ...]

_SHA256_HEX = re.compile(r"\A[0-9a-f]{64}\Z")
_SLUG_SEPARATOR = re.compile(r"[^a-z0-9]+")


def _validate_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer, got {value!r}")
    return value


def _validate_table_size(table_size: int) -> tuple[str, ...]:
    _validate_int(table_size, "table_size")
    if table_size < MIN_TABLE_SIZE or table_size > MAX_TABLE_SIZE:
        raise ValueError(
            f"table_size must be between {MIN_TABLE_SIZE} and {MAX_TABLE_SIZE},"
            f" got {table_size}"
        )
    return table_positions(table_size)


def _validate_stack_depth(stack_depth_bb: int) -> int:
    _validate_int(stack_depth_bb, "stack_depth_bb")
    if stack_depth_bb <= 0:
        raise ValueError(f"stack_depth_bb must be positive, got {stack_depth_bb}")
    return stack_depth_bb


def _validate_rfc3339_utc(text: str, field: str) -> datetime:
    if not isinstance(text, str):
        raise ValueError(f"{field} must be a string, got {text!r}")
    if not text.endswith("Z") or text[10:11] != "T":
        raise ValueError(
            f"{field} must be an RFC3339 UTC timestamp such as '2026-08-11T00:00:00Z',"
            f" got {text!r}"
        )
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field} is not a valid RFC3339 timestamp: {text!r}") from error
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be UTC, got {text!r}")
    return parsed


def _validate_subsequence(positions: Sequence[str], order: Sequence[str]) -> None:
    remaining = list(order)
    for position in positions:
        while remaining and remaining[0] != position:
            remaining.pop(0)
        if not remaining:
            raise ValueError(
                "action_sequence positions must follow preflop action order:"
                f" {list(positions)} is not ordered like {list(order)}"
            )
        remaining.pop(0)


def _validate_hero_is_to_act(
    hero_position: str,
    entries: Sequence[PreflopAction],
    order: Sequence[str],
) -> None:
    """Reject sequences that leave hero unable to be the player to act.

    Two shapes are legal. Hero has not acted yet, in which case every recorded
    action must come from a position ahead of hero, and hero cannot be the last
    position with nothing in front (folded to the big blind ends the hand).
    Or hero already acted and faces new aggression, in which case at least one
    later entry must be a raise, since a call behind hero does not give hero
    another turn.
    """
    hero_index = order.index(hero_position)
    own = [index for index, entry in enumerate(entries) if entry.position == hero_position]
    if not own:
        behind = [entry.position for entry in entries if order.index(entry.position) > hero_index]
        if behind:
            raise ValueError(
                f"{hero_position} cannot face action from {behind}, which act later preflop;"
                f" hero would have had to act first"
            )
        if not entries and hero_index == len(order) - 1:
            raise ValueError(
                f"{hero_position} acts last preflop, so a folded-to-hero spot has no decision"
            )
        return
    later = entries[own[0] + 1 :]
    if not later:
        raise ValueError(
            f"{hero_position} acted last in the sequence, so it is not the player to act"
        )
    if not any(entry.action == "raise" for entry in later):
        raise ValueError(
            f"{hero_position} already acted and faces no later raise,"
            " so the betting round is closed"
        )


@dataclass(frozen=True)
class PreflopAction:
    """One recorded preflop action in front of (or by) hero.

    Only calls and raises are recorded, so `action` is restricted to
    `SEQUENCE_ACTIONS`. A fold is implicit in the position's absence, and a check
    cannot precede hero's decision preflop.
    """

    position: str
    action: str

    def __post_init__(self) -> None:
        if self.position not in POSITION_LABELS:
            raise ValueError(f"unknown position: {self.position!r}")
        if self.action not in SEQUENCE_ACTIONS:
            raise ValueError(
                f"action_sequence action must be one of {list(SEQUENCE_ACTIONS)},"
                f" got {self.action!r} (a fold is implicit in the position's absence,"
                " and a preflop check ends the round)"
            )


@dataclass(frozen=True)
class SpotDefinition:
    """A spot hero can face preflop.

    An empty `action_sequence` means the pot is folded to hero (RFI). Table-size
    dependent validation lives on the owning `PreflopArtifact`, because a bare
    spot does not know its table size.
    """

    spot_id: str
    hero_position: str
    action_sequence: tuple[PreflopAction, ...]

    def __post_init__(self) -> None:
        if not self.spot_id:
            raise ValueError("spot_id is required")
        if self.hero_position not in POSITION_LABELS:
            raise ValueError(f"unknown hero_position: {self.hero_position!r}")
        for entry in self.action_sequence:
            if not isinstance(entry, PreflopAction):
                raise ValueError(
                    f"action_sequence entries must be PreflopAction, got {entry!r}"
                )


def spot_key(
    table_size: int,
    stack_depth_bb: int,
    hero_position: str,
    action_sequence: Sequence[PreflopAction],
) -> str:
    """Derive the canonical spot key.

    An empty sequence renders as `rfi` (folded to hero); otherwise the sequence
    renders as comma-separated `POSITION:action` entries in action order. Hero may
    appear in the sequence, which is how an open-raiser facing a 3bet is keyed.

    The sequence must describe a spot where hero is actually the player to act.
    A well-formed string is not enough: `t6/d100/CO/BTN:raise` reads fine but
    cannot happen, because the button acts after the cutoff. Keys that no real
    preflop situation produces are rejected, so the key space stays canonical
    rather than merely parseable.
    """
    positions = _validate_table_size(table_size)
    _validate_stack_depth(stack_depth_bb)
    if hero_position not in positions:
        raise ValueError(
            f"hero_position {hero_position!r} is not a {table_size}-handed position;"
            f" expected one of {list(positions)}"
        )
    entries = tuple(action_sequence)
    for entry in entries:
        if not isinstance(entry, PreflopAction):
            raise ValueError(f"action_sequence entries must be PreflopAction, got {entry!r}")
        if entry.position not in positions:
            raise ValueError(
                f"action_sequence position {entry.position!r} is not a"
                f" {table_size}-handed position"
            )
    acted = [entry.position for entry in entries]
    if len(set(acted)) != len(acted):
        raise ValueError(
            "action_sequence covers a position more than once;"
            f" v1 supports single-orbit spots only: {acted}"
        )
    order = preflop_action_order(table_size)
    _validate_subsequence(acted, order)
    _validate_hero_is_to_act(hero_position, entries, order)
    prefix = f"t{table_size}/d{stack_depth_bb}/{hero_position}/"
    if not entries:
        return f"{prefix}rfi"
    return prefix + ",".join(f"{entry.position}:{entry.action}" for entry in entries)


@dataclass(frozen=True)
class ArtifactSource:
    name: str
    kind: str
    reference: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("source name is required")
        if self.kind not in ARTIFACT_SOURCE_KINDS:
            raise ValueError(
                f"source kind must be one of {list(ARTIFACT_SOURCE_KINDS)}, got {self.kind!r}"
            )
        if not self.reference:
            raise ValueError("source reference is required")


@dataclass(frozen=True)
class ArtifactAuditFields:
    weights_sha256: str
    spot_count: int
    hand_class_count: int
    notes: str

    def __post_init__(self) -> None:
        if not _SHA256_HEX.match(self.weights_sha256):
            raise ValueError(
                f"weights_sha256 must be 64 lowercase hex characters, got {self.weights_sha256!r}"
            )
        for field in ("spot_count", "hand_class_count"):
            value = _validate_int(getattr(self, field), field)
            if value < 0:
                raise ValueError(f"{field} cannot be negative, got {value}")
        if not isinstance(self.notes, str):
            raise ValueError(f"notes must be a string, got {self.notes!r}")


def _weights_mapping(action_weights: SpotActionWeights) -> dict[str, Any]:
    return {
        spot_id: {
            hand_class_text: {action: float(weight) for action, weight in actions}
            for hand_class_text, actions in hand_classes
        }
        for spot_id, hand_classes in action_weights
    }


def weights_checksum(action_weights: SpotActionWeights) -> str:
    """sha256 over the canonical JSON serialization of the weights structure."""
    text = json.dumps(_weights_mapping(action_weights), sort_keys=True, separators=(",", ":"))
    return sha256(text.encode("utf-8")).hexdigest()


def _validate_weights(spot_id: str, hand_class_text: str, actions: ActionWeights) -> None:
    context = f"action_weights[{spot_id!r}][{hand_class_text!r}]"
    if not actions:
        raise ValueError(f"{context} declares no actions")
    names = [action for action, _ in actions]
    unknown = [action for action in names if action not in PREFLOP_ACTIONS]
    if unknown:
        raise ValueError(f"{context} names unknown actions: {unknown}")
    if len(set(names)) != len(names):
        raise ValueError(f"{context} repeats an action: {names}")
    if names != sorted(names, key=PREFLOP_ACTIONS.index):
        raise ValueError(f"{context} actions must follow {list(PREFLOP_ACTIONS)} order: {names}")
    total = 0.0
    positive = False
    for action, weight in actions:
        if isinstance(weight, bool) or not isinstance(weight, int | float):
            raise ValueError(f"{context}[{action!r}] weight must be a number, got {weight!r}")
        if not math.isfinite(weight):
            raise ValueError(f"{context}[{action!r}] weight must be finite, got {weight!r}")
        if weight < 0.0:
            raise ValueError(f"{context}[{action!r}] weight cannot be negative, got {weight!r}")
        if weight > 0.0:
            positive = True
        total += float(weight)
    if not positive:
        raise ValueError(f"{context} has no positive weight")
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValueError(
            f"{context} weights sum to {total!r}, outside {WEIGHT_SUM_TOLERANCE!r} of 1.0"
        )


@dataclass(frozen=True)
class PreflopArtifact:
    """A fully validated committed preflop chart."""

    artifact_schema_version: int
    source: ArtifactSource
    generated_at: str
    table_size: int
    stack_depth_bb: int
    positions: tuple[str, ...]
    spots: tuple[SpotDefinition, ...]
    action_weights: SpotActionWeights
    audit_fields: ArtifactAuditFields

    def __post_init__(self) -> None:
        if self.artifact_schema_version != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"only artifact_schema_version {ARTIFACT_SCHEMA_VERSION} is supported,"
                f" got {self.artifact_schema_version!r}"
            )
        expected_positions = _validate_table_size(self.table_size)
        _validate_stack_depth(self.stack_depth_bb)
        _validate_rfc3339_utc(self.generated_at, "generated_at")
        if self.positions != expected_positions:
            raise ValueError(
                f"positions must equal the derived {self.table_size}-handed vocabulary"
                f" {list(expected_positions)}, got {list(self.positions)}"
            )
        self._validate_spots()
        self._validate_action_weights()
        self._validate_audit_fields()

    def _validate_spots(self) -> None:
        if not self.spots:
            raise ValueError("an artifact must declare at least one spot")
        seen: set[str] = set()
        for spot in self.spots:
            derived = spot_key(
                self.table_size, self.stack_depth_bb, spot.hero_position, spot.action_sequence
            )
            if spot.spot_id != derived:
                raise ValueError(
                    f"spot_id {spot.spot_id!r} does not match its derived key {derived!r}"
                )
            if spot.spot_id in seen:
                raise ValueError(f"duplicate spot_id: {spot.spot_id!r}")
            seen.add(spot.spot_id)

    def _validate_action_weights(self) -> None:
        declared = [spot.spot_id for spot in self.spots]
        keyed = [spot_id for spot_id, _ in self.action_weights]
        if keyed != declared:
            unknown = sorted(set(keyed) - set(declared))
            missing = sorted(set(declared) - set(keyed))
            if unknown:
                raise ValueError(f"action_weights cover undeclared spots: {unknown}")
            if missing:
                raise ValueError(f"spots without action_weights: {missing}")
            raise ValueError("action_weights must be ordered like spots")
        for spot_id, hand_classes in self.action_weights:
            if not hand_classes:
                raise ValueError(f"action_weights[{spot_id!r}] declares no hand classes")
            names = [hand_class_text for hand_class_text, _ in hand_classes]
            unknown = [name for name in names if not is_hand_class(name)]
            if unknown:
                raise ValueError(
                    f"action_weights[{spot_id!r}] names unknown hand classes: {unknown}"
                )
            if len(set(names)) != len(names):
                raise ValueError(f"action_weights[{spot_id!r}] repeats a hand class: {names}")
            if names != sorted(names, key=hand_class_grid_index):
                raise ValueError(
                    f"action_weights[{spot_id!r}] hand classes must be ordered by grid index"
                )
            for hand_class_text, actions in hand_classes:
                _validate_weights(spot_id, hand_class_text, actions)

    def _validate_audit_fields(self) -> None:
        if self.audit_fields.spot_count != len(self.spots):
            raise ValueError(
                f"audit_fields.spot_count {self.audit_fields.spot_count}"
                f" does not match {len(self.spots)} spots"
            )
        distinct = {
            hand_class_text
            for _, hand_classes in self.action_weights
            for hand_class_text, _ in hand_classes
        }
        if self.audit_fields.hand_class_count != len(distinct):
            raise ValueError(
                f"audit_fields.hand_class_count {self.audit_fields.hand_class_count}"
                f" does not match {len(distinct)} distinct hand classes"
            )
        checksum = weights_checksum(self.action_weights)
        if self.audit_fields.weights_sha256 != checksum:
            raise ValueError(
                f"audit_fields.weights_sha256 {self.audit_fields.weights_sha256!r}"
                f" does not match the derived checksum {checksum!r}"
            )

    @cached_property
    def _spot_index(self) -> dict[str, SpotDefinition]:
        return {spot.spot_id: spot for spot in self.spots}

    @cached_property
    def _weight_index(self) -> dict[str, dict[str, ActionWeights]]:
        return {
            spot_id: dict(hand_classes) for spot_id, hand_classes in self.action_weights
        }

    @property
    def artifact_id(self) -> str:
        """`t{table_size}/d{stack_depth_bb}/{slug}`.

        The slug lowercases `source.name` and collapses every run of non
        alphanumeric characters into a single dash, falling back to `unnamed`.
        """
        slug = _SLUG_SEPARATOR.sub("-", self.source.name.lower()).strip("-")
        return f"t{self.table_size}/d{self.stack_depth_bb}/{slug or 'unnamed'}"

    def spot(self, spot_key_text: str) -> SpotDefinition:
        found = self._spot_index.get(spot_key_text)
        if found is None:
            raise ValueError(f"artifact {self.artifact_id} does not declare spot {spot_key_text!r}")
        return found

    def weights_for(self, spot_key_text: str, hand_class_text: str) -> ActionWeights | None:
        """Return the ordered weights, or None when the spot/class is not covered."""
        return self._weight_index.get(spot_key_text, {}).get(hand_class_text)

    def to_payload(self) -> dict[str, Any]:
        return {
            "artifact_schema_version": self.artifact_schema_version,
            "source": {
                "name": self.source.name,
                "kind": self.source.kind,
                "reference": self.source.reference,
            },
            "generated_at": self.generated_at,
            "table_size": self.table_size,
            "stack_depth_bb": self.stack_depth_bb,
            "positions": list(self.positions),
            "spots": [
                {
                    "spot_id": spot.spot_id,
                    "hero_position": spot.hero_position,
                    "action_sequence": [
                        {"position": entry.position, "action": entry.action}
                        for entry in spot.action_sequence
                    ],
                }
                for spot in self.spots
            ],
            "action_weights": _weights_mapping(self.action_weights),
            "audit_fields": {
                "weights_sha256": self.audit_fields.weights_sha256,
                "spot_count": self.audit_fields.spot_count,
                "hand_class_count": self.audit_fields.hand_class_count,
                "notes": self.audit_fields.notes,
            },
        }
