"""Fail-closed importer for committed preflop chart artifacts.

Every rejection carries a namespaced reason code and names the offending path.
Nothing partially loaded is ever returned: an artifact is either fully validated
or the import raises.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts.hand_classes import (
    hand_class_grid_index,
    is_hand_class,
)
from poker_training_bot.solver_artifacts.schema import (
    ARTIFACT_SCHEMA_VERSION,
    ARTIFACT_SOURCE_KINDS,
    MAX_TABLE_SIZE,
    MIN_TABLE_SIZE,
    PREFLOP_ACTIONS,
    SEQUENCE_ACTIONS,
    WEIGHT_SUM_TOLERANCE,
    ArtifactAuditFields,
    ArtifactSource,
    PreflopAction,
    PreflopArtifact,
    SpotActionWeights,
    SpotDefinition,
    spot_key,
    weights_checksum,
)
from poker_training_bot.solver_artifacts.strict_json import (
    INVALID_VALUE,
    MISSING_FIELD,
    NOT_AN_OBJECT,
    UNKNOWN_FIELD,
    ArtifactImportError,
    _fail,
    _object_pairs_hook,
    _require_int,
    _require_keys,
    _require_list,
    _require_object,
    _require_str,
    _require_unique_keys,
)

UNREADABLE_FILE = "artifact:unreadable-file"
INVALID_JSON = "artifact:invalid-json"
UNSUPPORTED_SCHEMA_VERSION = "artifact:unsupported-schema-version"
INVALID_POSITION_VOCABULARY = "artifact:invalid-position-vocabulary"
SPOT_KEY_MISMATCH = "artifact:spot-key-mismatch"
DUPLICATE_SPOT = "artifact:duplicate-spot"
UNKNOWN_SPOT_WEIGHTS = "artifact:unknown-spot-weights"
MISSING_SPOT_WEIGHTS = "artifact:missing-spot-weights"
UNKNOWN_HAND_CLASS = "artifact:unknown-hand-class"
DUPLICATE_HAND_CLASS = "artifact:duplicate-hand-class"
UNKNOWN_ACTION = "artifact:unknown-action"
INVALID_WEIGHT = "artifact:invalid-weight"
WEIGHT_SUM = "artifact:weight-sum"
CHECKSUM_MISMATCH = "artifact:checksum-mismatch"
AUDIT_COUNT_MISMATCH = "artifact:audit-count-mismatch"

REASON_CODES = (
    UNREADABLE_FILE,
    INVALID_JSON,
    NOT_AN_OBJECT,
    MISSING_FIELD,
    UNKNOWN_FIELD,
    UNSUPPORTED_SCHEMA_VERSION,
    INVALID_VALUE,
    INVALID_POSITION_VOCABULARY,
    SPOT_KEY_MISMATCH,
    DUPLICATE_SPOT,
    UNKNOWN_SPOT_WEIGHTS,
    MISSING_SPOT_WEIGHTS,
    UNKNOWN_HAND_CLASS,
    DUPLICATE_HAND_CLASS,
    UNKNOWN_ACTION,
    INVALID_WEIGHT,
    WEIGHT_SUM,
    CHECKSUM_MISMATCH,
    AUDIT_COUNT_MISMATCH,
)

_ARTIFACT_KEYS = {
    "artifact_schema_version",
    "source",
    "generated_at",
    "table_size",
    "stack_depth_bb",
    "positions",
    "spots",
    "action_weights",
    "audit_fields",
}
_SOURCE_KEYS = {"name", "kind", "reference"}
_SPOT_KEYS = {"spot_id", "hero_position", "action_sequence"}
_ACTION_KEYS = {"position", "action"}
# `size_bb` is present exactly where the entry is a raise, so it is optional at the
# key-set level and required by `PreflopAction` itself. A raise entry without one is a
# v1 record, and it is rejected rather than read as matching any price: a format that
# admits both is a format where a lookup can silently hit the wrong cell.
_ACTION_OPTIONAL_KEYS = {"size_bb"}
_AUDIT_KEYS = {"weights_sha256", "spot_count", "hand_class_count", "notes"}


def _parse_source(payload: dict[str, Any], origin: str) -> ArtifactSource:
    path = "artifact.source"
    raw = _require_object(payload.get("source"), origin, path)
    _require_unique_keys(raw, origin, path, INVALID_VALUE)
    _require_keys(raw, origin, path, _SOURCE_KEYS)
    name = _require_str(raw, origin, path, "name")
    kind = _require_str(raw, origin, path, "kind")
    reference = _require_str(raw, origin, path, "reference")
    if kind not in ARTIFACT_SOURCE_KINDS:
        raise _fail(
            INVALID_VALUE,
            origin,
            f"{path}.kind must be one of {list(ARTIFACT_SOURCE_KINDS)}, got {kind!r}",
        )
    if not name:
        raise _fail(INVALID_VALUE, origin, f"{path}.name cannot be empty")
    if not reference:
        raise _fail(INVALID_VALUE, origin, f"{path}.reference cannot be empty")
    return ArtifactSource(name=name, kind=kind, reference=reference)


def _parse_positions(payload: dict[str, Any], origin: str, table_size: int) -> tuple[str, ...]:
    raw = _require_list(payload, origin, "artifact", "positions")
    if not all(isinstance(item, str) for item in raw):
        raise _fail(INVALID_VALUE, origin, "artifact.positions must be a list of strings")
    expected = table_positions(table_size)
    if tuple(raw) != expected:
        raise _fail(
            INVALID_POSITION_VOCABULARY,
            origin,
            f"artifact.positions must equal the derived {table_size}-handed vocabulary"
            f" {list(expected)}, got {raw}",
        )
    return expected


def _parse_action_entry(
    raw: Any, origin: str, path: str, vocabulary: tuple[str, ...]
) -> PreflopAction:
    entry = _require_object(raw, origin, path)
    _require_unique_keys(entry, origin, path, INVALID_VALUE)
    _require_keys(entry, origin, path, _ACTION_KEYS, _ACTION_OPTIONAL_KEYS)
    position = _require_str(entry, origin, path, "position")
    action = _require_str(entry, origin, path, "action")
    if position not in vocabulary:
        raise _fail(
            INVALID_POSITION_VOCABULARY,
            origin,
            f"{path}.position {position!r} is not in the derived vocabulary {list(vocabulary)}",
        )
    if action not in SEQUENCE_ACTIONS:
        detail = " (folds are implicit, so they are never recorded)" if action == "fold" else ""
        raise _fail(
            UNKNOWN_ACTION,
            origin,
            f"{path}.action must be one of {list(SEQUENCE_ACTIONS)}, got {action!r}{detail}",
        )
    size_bb = entry.get("size_bb")
    if size_bb is not None and (
        isinstance(size_bb, bool) or not isinstance(size_bb, int | float)
    ):
        raise _fail(
            INVALID_VALUE, origin, f"{path}.size_bb must be a number, got {size_bb!r}"
        )
    try:
        return PreflopAction(position=position, action=action, size_bb=size_bb)
    except ValueError as error:
        raise _fail(INVALID_VALUE, origin, f"{path}: {error}") from error


def _parse_spots(
    payload: dict[str, Any],
    origin: str,
    table_size: int,
    stack_depth_bb: int,
    vocabulary: tuple[str, ...],
) -> tuple[SpotDefinition, ...]:
    spots: list[SpotDefinition] = []
    seen: set[str] = set()
    for index, item in enumerate(_require_list(payload, origin, "artifact", "spots")):
        path = f"artifact.spots[{index}]"
        entry = _require_object(item, origin, path)
        _require_unique_keys(entry, origin, path, INVALID_VALUE)
        _require_keys(entry, origin, path, _SPOT_KEYS)
        spot_id = _require_str(entry, origin, path, "spot_id")
        hero_position = _require_str(entry, origin, path, "hero_position")
        if hero_position not in vocabulary:
            raise _fail(
                INVALID_POSITION_VOCABULARY,
                origin,
                f"{path}.hero_position {hero_position!r} is not in the derived vocabulary"
                f" {list(vocabulary)}",
            )
        sequence = tuple(
            _parse_action_entry(
                action_raw, origin, f"{path}.action_sequence[{action_index}]", vocabulary
            )
            for action_index, action_raw in enumerate(
                _require_list(entry, origin, path, "action_sequence")
            )
        )
        try:
            derived = spot_key(table_size, stack_depth_bb, hero_position, sequence)
        except ValueError as error:
            raise _fail(INVALID_VALUE, origin, f"{path}: {error}") from error
        if spot_id != derived:
            raise _fail(
                SPOT_KEY_MISMATCH,
                origin,
                f"{path}.spot_id {spot_id!r} does not match its derived key {derived!r}",
            )
        if spot_id in seen:
            raise _fail(DUPLICATE_SPOT, origin, f"{path}.spot_id {spot_id!r} is declared twice")
        seen.add(spot_id)
        spots.append(
            SpotDefinition(spot_id=spot_id, hero_position=hero_position, action_sequence=sequence)
        )
    if not spots:
        raise _fail(
            INVALID_VALUE,
            origin,
            "artifact.spots declares no spots; an artifact with nothing in it would still"
            " claim its table size and stack depth are covered",
        )
    return tuple(spots)


def _parse_weights(raw: Any, origin: str, path: str) -> tuple[tuple[str, float], ...]:
    actions = _require_object(raw, origin, path)
    _require_unique_keys(actions, origin, path, INVALID_VALUE)
    if not actions:
        raise _fail(INVALID_VALUE, origin, f"{path} declares no actions")
    for name in actions:
        if name not in PREFLOP_ACTIONS:
            raise _fail(
                UNKNOWN_ACTION,
                origin,
                f"{path} names unknown action {name!r}; expected one of {list(PREFLOP_ACTIONS)}",
            )
    weights: list[tuple[str, float]] = []
    total = 0.0
    for name in sorted(actions, key=PREFLOP_ACTIONS.index):
        weight = actions[name]
        if isinstance(weight, bool) or not isinstance(weight, int | float):
            raise _fail(
                INVALID_WEIGHT, origin, f"{path}.{name} must be a number, got {weight!r}"
            )
        if not math.isfinite(weight):
            raise _fail(INVALID_WEIGHT, origin, f"{path}.{name} must be finite, got {weight!r}")
        if weight < 0:
            raise _fail(
                INVALID_WEIGHT, origin, f"{path}.{name} cannot be negative, got {weight!r}"
            )
        weights.append((name, float(weight)))
        total += float(weight)
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise _fail(
            WEIGHT_SUM,
            origin,
            f"{path} weights sum to {total!r}, outside {WEIGHT_SUM_TOLERANCE!r} of 1.0",
        )
    return tuple(weights)


def _parse_action_weights(
    payload: dict[str, Any], origin: str, spot_ids: tuple[str, ...]
) -> SpotActionWeights:
    path = "artifact.action_weights"
    mapping = _require_object(payload.get("action_weights"), origin, path)
    _require_unique_keys(mapping, origin, path, DUPLICATE_SPOT)
    declared = set(spot_ids)
    for key in mapping:
        if key not in declared:
            raise _fail(
                UNKNOWN_SPOT_WEIGHTS,
                origin,
                f"{path}[{key!r}] has no matching entry in artifact.spots",
            )
    for spot_id in spot_ids:
        if spot_id not in mapping:
            raise _fail(
                MISSING_SPOT_WEIGHTS, origin, f"{path} is missing weights for spot {spot_id!r}"
            )
    entries: list[tuple[str, tuple[tuple[str, tuple[tuple[str, float], ...]], ...]]] = []
    for spot_id in spot_ids:
        spot_path = f"{path}[{spot_id!r}]"
        classes = _require_object(mapping[spot_id], origin, spot_path)
        _require_unique_keys(classes, origin, spot_path, DUPLICATE_HAND_CLASS)
        if not classes:
            raise _fail(INVALID_VALUE, origin, f"{spot_path} declares no hand classes")
        for name in classes:
            if not is_hand_class(name):
                raise _fail(
                    UNKNOWN_HAND_CLASS,
                    origin,
                    f"{spot_path}[{name!r}] is not a canonical 169-class hand notation",
                )
        entries.append(
            (
                spot_id,
                tuple(
                    (name, _parse_weights(classes[name], origin, f"{spot_path}[{name!r}]"))
                    for name in sorted(classes, key=hand_class_grid_index)
                ),
            )
        )
    return tuple(entries)


def _parse_audit_fields(
    payload: dict[str, Any],
    origin: str,
    spots: tuple[SpotDefinition, ...],
    action_weights: SpotActionWeights,
) -> ArtifactAuditFields:
    path = "artifact.audit_fields"
    raw = _require_object(payload.get("audit_fields"), origin, path)
    _require_unique_keys(raw, origin, path, INVALID_VALUE)
    _require_keys(raw, origin, path, _AUDIT_KEYS)
    checksum = _require_str(raw, origin, path, "weights_sha256")
    spot_count = _require_int(raw, origin, path, "spot_count")
    hand_class_count = _require_int(raw, origin, path, "hand_class_count")
    notes = _require_str(raw, origin, path, "notes")
    try:
        audit_fields = ArtifactAuditFields(
            weights_sha256=checksum,
            spot_count=spot_count,
            hand_class_count=hand_class_count,
            notes=notes,
        )
    except ValueError as error:
        raise _fail(INVALID_VALUE, origin, f"{path}: {error}") from error
    expected_classes = len(
        {name for _, classes in action_weights for name, _ in classes}
    )
    if spot_count != len(spots):
        raise _fail(
            AUDIT_COUNT_MISMATCH,
            origin,
            f"{path}.spot_count {spot_count} does not match {len(spots)} declared spots",
        )
    if hand_class_count != expected_classes:
        raise _fail(
            AUDIT_COUNT_MISMATCH,
            origin,
            f"{path}.hand_class_count {hand_class_count} does not match"
            f" {expected_classes} distinct hand classes",
        )
    derived_checksum = weights_checksum(action_weights)
    if checksum != derived_checksum:
        raise _fail(
            CHECKSUM_MISMATCH,
            origin,
            f"{path}.weights_sha256 {checksum!r} does not match the derived checksum"
            f" {derived_checksum!r}",
        )
    return audit_fields


def _build_artifact(raw: Any, origin: str) -> PreflopArtifact:
    payload = _require_object(raw, origin, "artifact")
    _require_unique_keys(payload, origin, "artifact", INVALID_VALUE)
    _require_keys(payload, origin, "artifact", _ARTIFACT_KEYS)
    version = _require_int(payload, origin, "artifact", "artifact_schema_version")
    if version != ARTIFACT_SCHEMA_VERSION:
        raise _fail(
            UNSUPPORTED_SCHEMA_VERSION,
            origin,
            f"artifact_schema_version {version} is not supported;"
            f" this build reads version {ARTIFACT_SCHEMA_VERSION}",
        )
    table_size = _require_int(payload, origin, "artifact", "table_size")
    if table_size < MIN_TABLE_SIZE or table_size > MAX_TABLE_SIZE:
        raise _fail(
            INVALID_VALUE,
            origin,
            f"artifact.table_size must be between {MIN_TABLE_SIZE} and {MAX_TABLE_SIZE},"
            f" got {table_size}",
        )
    stack_depth_bb = _require_int(payload, origin, "artifact", "stack_depth_bb")
    if stack_depth_bb <= 0:
        raise _fail(
            INVALID_VALUE, origin, f"artifact.stack_depth_bb must be positive, got {stack_depth_bb}"
        )
    generated_at = _require_str(payload, origin, "artifact", "generated_at")
    source = _parse_source(payload, origin)
    positions = _parse_positions(payload, origin, table_size)
    spots = _parse_spots(payload, origin, table_size, stack_depth_bb, positions)
    action_weights = _parse_action_weights(payload, origin, tuple(spot.spot_id for spot in spots))
    audit_fields = _parse_audit_fields(payload, origin, spots, action_weights)
    try:
        return PreflopArtifact(
            artifact_schema_version=version,
            source=source,
            generated_at=generated_at,
            table_size=table_size,
            stack_depth_bb=stack_depth_bb,
            positions=positions,
            spots=spots,
            action_weights=action_weights,
            audit_fields=audit_fields,
        )
    except ValueError as error:
        raise _fail(INVALID_VALUE, origin, str(error)) from error


def import_preflop_artifact(path: Path | str) -> PreflopArtifact:
    """Import one committed artifact file, or raise `ArtifactImportError`."""
    file_path = Path(path)
    origin = str(file_path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ArtifactImportError(UNREADABLE_FILE, f"{origin}: cannot be read: {error}") from error
    try:
        raw = json.loads(text, object_pairs_hook=_object_pairs_hook)
    except json.JSONDecodeError as error:
        raise _fail(INVALID_JSON, origin, f"is not valid JSON: {error}") from error
    return _build_artifact(raw, origin)


def import_preflop_artifacts(directory: Path | str) -> tuple[PreflopArtifact, ...]:
    """Import every `*.json` file directly under `directory`, sorted by filename.

    A single unimportable file fails the whole call.
    """
    root = Path(directory)
    origin = str(root)
    if not root.is_dir():
        raise ArtifactImportError(UNREADABLE_FILE, f"{origin}: is not a directory")
    files = sorted((item for item in root.glob("*.json") if item.is_file()), key=lambda p: p.name)
    if not files:
        raise ArtifactImportError(UNREADABLE_FILE, f"{origin}: contains no *.json artifacts")
    return tuple(import_preflop_artifact(item) for item in files)
