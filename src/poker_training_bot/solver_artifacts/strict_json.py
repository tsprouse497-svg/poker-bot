"""Strict JSON reading, with a namespaced rejection for every way a file can be wrong.

Separated from the artifact importer because it is a different job: this layer knows
nothing about poker and only about what a trustworthy file looks like. Duplicate keys
are the reason it exists at all - `json.loads` silently keeps the last one, so a file
declaring a field twice would import as though it had declared it once, and the reader
would never know which value it got.
"""

from __future__ import annotations

from typing import Any

# The four rejections this layer can make on its own, before anything poker-specific is
# read. They live here rather than in the importer so the layer is self-contained; the
# importer re-exports them, because a caller matching on a reason code should not have to
# know which file the constant sits in.
NOT_AN_OBJECT = "artifact:not-an-object"
MISSING_FIELD = "artifact:missing-field"
UNKNOWN_FIELD = "artifact:unknown-field"
INVALID_VALUE = "artifact:invalid-value"


class ArtifactImportError(ValueError):
    """A fail-closed artifact rejection carrying a namespaced reason code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class _JsonObject(dict):
    """JSON object that remembers duplicate keys the parser collapsed."""

    duplicate_keys: tuple[str, ...] = ()


def _object_pairs_hook(pairs: list[tuple[str, Any]]) -> _JsonObject:
    obj = _JsonObject(pairs)
    if len(obj) != len(pairs):
        names = [name for name, _ in pairs]
        obj.duplicate_keys = tuple(sorted({name for name in names if names.count(name) > 1}))
    return obj


def _fail(code: str, origin: str, message: str) -> ArtifactImportError:
    return ArtifactImportError(code, f"{origin}: {message}")


def _require_object(raw: Any, origin: str, path: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise _fail(
            NOT_AN_OBJECT, origin, f"{path} must be a JSON object, got {type(raw).__name__}"
        )
    return raw


def _require_unique_keys(payload: dict[str, Any], origin: str, path: str, code: str) -> None:
    duplicates = getattr(payload, "duplicate_keys", ())
    if duplicates:
        raise _fail(code, origin, f"{path} repeats keys: {list(duplicates)}")


def _require_keys(
    payload: dict[str, Any],
    origin: str,
    path: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    missing = sorted(required - set(payload))
    if missing:
        raise _fail(MISSING_FIELD, origin, f"{path} is missing required keys: {missing}")
    unknown = sorted(set(payload) - required - (optional or set()))
    if unknown:
        raise _fail(UNKNOWN_FIELD, origin, f"{path} has unknown keys: {unknown}")


def _require_str(payload: dict[str, Any], origin: str, path: str, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise _fail(INVALID_VALUE, origin, f"{path}.{key} must be a string, got {value!r}")
    return value


def _require_int(payload: dict[str, Any], origin: str, path: str, key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise _fail(INVALID_VALUE, origin, f"{path}.{key} must be an integer, got {value!r}")
    return value


def _require_list(payload: dict[str, Any], origin: str, path: str, key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise _fail(INVALID_VALUE, origin, f"{path}.{key} must be a list, got {value!r}")
    return value


