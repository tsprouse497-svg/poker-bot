"""Committed preflop artifact schema: the container the ranges are shipped in.

The vocabulary a spot is named in lives in `solver_artifacts.spot_key`, and is
re-exported here because every caller in this repo has always reached for it through
`schema` and there is still exactly one derivation behind the name. What is left in this
file is the artifact itself: where it came from, what it covers, what it declares, and
the validation that makes an artifact either fully trustworthy or refused.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from hashlib import sha256
from typing import Any

from poker_training_bot.poker_core.positions import POSITION_LABELS
from poker_training_bot.solver_artifacts.hand_classes import (
    hand_class_grid_index,
    is_hand_class,
)
from poker_training_bot.solver_artifacts.solve_conditions import (
    ArrivalProbabilities,
    ArrivingReach,
    BlindStructure,
    arrival_payload,
    reach_payload,
    validate_arrival_probabilities,
    validate_arriving_reach,
)
from poker_training_bot.solver_artifacts.spot_key import (
    MAX_TABLE_SIZE,
    MIN_TABLE_SIZE,
    SEQUENCE_ACTIONS,
    SIZE_QUANTUM,
    PreflopAction,
    _validate_int,
    _validate_stack_depth,
    _validate_table_size,
    action_entry_payload,
    render_entry,
    render_size_bb,
    spot_key,
)

__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "ARTIFACT_SOURCE_KINDS",
    "MAX_TABLE_SIZE",
    "MIN_TABLE_SIZE",
    "PREFLOP_ACTIONS",
    "SEQUENCE_ACTIONS",
    "SIZE_QUANTUM",
    "WEIGHT_SUM_TOLERANCE",
    "ActionWeights",
    # The conditions of the solve are a different subject from the ranges and holding both
    # broke the 500-line cap, so they live in `solve_conditions`. They are re-exported
    # because an artifact carries them and the frozen tests read them off this module.
    "ArrivalProbabilities",
    "ArrivingReach",
    "ArtifactAuditFields",
    "ArtifactSource",
    "BlindStructure",
    "HandClassWeights",
    "PreflopAction",
    "PreflopArtifact",
    "SpotActionWeights",
    "SpotDefinition",
    "action_entry_payload",
    "render_entry",
    "render_size_bb",
    "spot_key",
    "weights_checksum",
]

ARTIFACT_SCHEMA_VERSION = 2
WEIGHT_SUM_TOLERANCE = 1e-6
PREFLOP_ACTIONS = ("fold", "check", "call", "raise")
ARTIFACT_SOURCE_KINDS = ("solver-export", "hand-authored")

ActionWeights = tuple[tuple[str, float], ...]
HandClassWeights = tuple[tuple[str, ActionWeights], ...]
SpotActionWeights = tuple[tuple[str, HandClassWeights], ...]

_SHA256_HEX = re.compile(r"\A[0-9a-f]{64}\Z")
_SLUG_SEPARATOR = re.compile(r"[^a-z0-9]+")

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
    blind_structure: BlindStructure
    spots: tuple[SpotDefinition, ...]
    action_weights: SpotActionWeights
    arriving_reach_bp: ArrivingReach
    audit_fields: ArtifactAuditFields
    # Optional because a chart may be committed before its arrival probabilities are
    # measured, and absent has to stay distinguishable from a spot that is never reached.
    # Present, it is validated; None is the only thing that means "not recorded here".
    arrival_ppb: ArrivalProbabilities | None = None

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
        self._validate_no_limp()
        validate_arriving_reach(self.arriving_reach_bp, self._declared_cells())
        if self.arrival_ppb is not None:
            validate_arrival_probabilities(
                self.arrival_ppb, tuple(spot.spot_id for spot in self.spots)
            )
        self._validate_audit_fields()

    def _declared_cells(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """The cells the chart answers: every spot with the hand classes it declares."""
        return tuple(
            (spot_id, tuple(hand_class_text for hand_class_text, _ in hand_classes))
            for spot_id, hand_classes in self.action_weights
        )

    def _validate_no_limp(self) -> None:
        """`CHART-HERO-MUST-NEVER-LIMP`, as a rule rather than a property of one file.

        The pot folded to hero is an empty `action_sequence`, so a call there is a limp: hero
        pays the big blind to give every seat behind a free look at a flop in position, and
        the solve the cutover derives from offers him no call at that spot at all. The chart
        being retired limped 13.73 percent from the small blind across 103 hand classes, so
        this is the state the repo shipped in rather than a hypothetical. A rule refuses the
        next artifact too; a measurement over this one refuses nothing.
        """
        for spot, (spot_id, hand_classes) in zip(self.spots, self.action_weights, strict=True):
            for hand_class_text, actions in hand_classes:
                call_weight = dict(actions).get("call", 0.0)
                if not spot.action_sequence and call_weight > 0.0:
                    raise ValueError(
                        f"action_weights[{spot_id!r}][{hand_class_text!r}] limps: the pot is"
                        f" folded to hero and call carries weight {call_weight!r}"
                    )

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

    @cached_property
    def _reach_index(self) -> dict[str, dict[str, int]]:
        return {spot_id: dict(cells) for spot_id, cells in self.arriving_reach_bp}

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

    def reach_bp_for(self, spot_key_text: str, hand_class_text: str) -> int | None:
        """The cell's arriving reach in basis points, or None when it is not covered.

        Fails closed like `weights_for`, and for the same reason: a caller that gets a number
        for an uncovered cell cannot tell it from a cell the chart answers.
        """
        return self._reach_index.get(spot_key_text, {}).get(hand_class_text)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
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
            "blind_structure": {
                "small_blind_bb": self.blind_structure.small_blind_bb,
                "big_blind_bb": self.blind_structure.big_blind_bb,
                "ante_bb": self.blind_structure.ante_bb,
            },
            "spots": [
                {
                    "spot_id": spot.spot_id,
                    "hero_position": spot.hero_position,
                    "action_sequence": [
                        action_entry_payload(entry) for entry in spot.action_sequence
                    ],
                }
                for spot in self.spots
            ],
            "action_weights": _weights_mapping(self.action_weights),
            "arriving_reach_bp": reach_payload(self.arriving_reach_bp),
            "audit_fields": {
                "weights_sha256": self.audit_fields.weights_sha256,
                "spot_count": self.audit_fields.spot_count,
                "hand_class_count": self.audit_fields.hand_class_count,
                "notes": self.audit_fields.notes,
            },
        }
        if self.arrival_ppb is not None:
            payload["arrival_ppb"] = arrival_payload(self.arrival_ppb)
        return payload
