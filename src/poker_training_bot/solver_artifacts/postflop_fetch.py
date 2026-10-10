"""The fetch a fresh machine runs: one line's index and objects, each checked before it is kept.

Decisions 3 and 4: the full index of a line and every object it lists live in a private bucket,
and git holds the line's manifest - its boards, their counts, and one fingerprint of the index.
The store is injected as anything with `get(key) -> bytes`, because object storage is a hard
external boundary; nothing here opens a socket or reads a credential.

**What the fetch checks, in order, and the code each refusal carries.**

1. The manifest's own counts against its line's tree (`postflop_manifest.decision_point_errors`):
   a manifest and index short by the same turn card agree with each other and not with the tree.
   `DECISION_POINTS_MISMATCH`.
2. The index's bytes against the manifest's fingerprint, size and sha256.
   `INDEX_FINGERPRINT_MISMATCH`.
3. The index's per-board counts against the manifest's, board by board, and that no river is
   listed anywhere. `DECISION_POINTS_MISMATCH`.
4. Each fetched object's bytes against the digest the index lists. `OBJECT_DIGEST_MISMATCH`.
5. Each fetched object's contents against its board's counts: a flop object's cell keys must be
   exactly the line's flop decision points on that board - a count of cells is not enough, since
   fourteen cells can hold one point twice and miss another - and a turn object must hold the
   decision points its counts claim, read from its own bytes by `postflop_street_rows`.
   `DECISION_POINTS_MISMATCH`.

An object is written only once it has passed, atomically, at its object key under the fetched
folder; the index is written last. `require_fetched` is what a player calls before reading: a
board whose object for the street is not on disk refuses with `NOT_FETCHED`, so a machine that
fetched the flop and not the turn never reads as holding the turn.

**The fetch is by street.** A machine that plays only the flop fetches the flop objects and the
index; the turn is fetched by the phase that plays it. **There is no river object** (decision 1,
re-ruled 2026-10-04): a fetch that asks for one is refused.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from poker_training_bot.solver_artifacts import postflop_lines as lines
from poker_training_bot.solver_artifacts.postflop_manifest import (
    CLOSED,
    LINE_INDEX_SCHEMA_VERSION,
    STORED_STREETS,
    decision_point_errors,
    manifest_errors,
    read_strict_json,
)
from poker_training_bot.solver_artifacts.postflop_street_rows import (
    street_object_decision_points,
)

NOT_FETCHED = "postflop:not-fetched"
INDEX_FINGERPRINT_MISMATCH = "postflop:index-fingerprint-mismatch"
OBJECT_DIGEST_MISMATCH = "postflop:object-digest-mismatch"
DECISION_POINTS_MISMATCH = "postflop:decision-points-mismatch"
MALFORMED_INDEX = "postflop:malformed-line-index"
"""An index whose bytes are the fingerprinted ones and whose shape is still not a line index."""

_INDEX_KEYS = frozenset({"line_index_schema_version", "preflop_line", "boards"})
_INDEX_BOARD_KEYS = frozenset({"board", "decision_points", "objects"})
_OBJECT_KEYS = frozenset({"key", "sha256"})


class ObjectStore(Protocol):
    def get(self, key: str) -> bytes: ...


class FetchError(Exception):
    """A refusal to fetch or to read fetched data, carrying one of this module's codes."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _streets(streets: Iterable[str]) -> tuple[str, ...]:
    chosen = tuple(streets)
    if not chosen or any(street not in STORED_STREETS for street in chosen):
        raise ValueError(
            f"a fetch takes streets from {STORED_STREETS}, got {chosen!r}; the river is never"
            " stored, so there is no river object to fetch"
        )
    return tuple(dict.fromkeys(chosen))


def _local_path(root: Path, key: str) -> Path:
    """Where an object key lives under the fetched folder, refusing a key that would leave it."""
    parts = PurePosixPath(key).parts
    if not parts or PurePosixPath(key).is_absolute() or ".." in parts or "\\" in key:
        raise FetchError(MALFORMED_INDEX, f"object key {key!r} is not a relative storage key")
    return Path(root, *parts)


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_bytes(data)
    os.replace(partial, path)


def _check_manifest(manifest: Mapping[str, Any]) -> str:
    """The manifest's counts against its tree first, then everything else it must hold."""
    line = manifest.get("preflop_line")
    boards = manifest.get("boards")
    if isinstance(line, str) and isinstance(boards, list):
        for entry in boards:
            if isinstance(entry, dict):
                errors = decision_point_errors(line, entry)
                if errors:
                    raise FetchError(DECISION_POINTS_MISMATCH, "; ".join(errors))
    errors = manifest_errors(manifest)
    if errors:
        raise ValueError(f"the manifest fails its own checks: {errors}")
    return line


def _parse_index(manifest: Mapping[str, Any], data: bytes) -> dict[str, Any]:
    """The index the manifest fingerprints, or a refusal naming which check failed."""
    reference = manifest["index"]
    if len(data) != reference["bytes"] or _sha256(data) != reference["sha256"]:
        raise FetchError(
            INDEX_FINGERPRINT_MISMATCH,
            f"{reference['object_key']} is {len(data)} bytes with sha256 {_sha256(data)}; the"
            f" manifest fingerprints {reference['bytes']} bytes with sha256 {reference['sha256']}",
        )
    try:
        index = read_strict_json(data, reference["object_key"])
    except ValueError as error:
        raise FetchError(MALFORMED_INDEX, str(error)) from error
    if not isinstance(index, dict) or set(index) != _INDEX_KEYS:
        raise FetchError(MALFORMED_INDEX, f"a line index holds exactly {sorted(_INDEX_KEYS)}")
    if index["line_index_schema_version"] != LINE_INDEX_SCHEMA_VERSION:
        raise FetchError(MALFORMED_INDEX, "unsupported line index schema version")
    if index["preflop_line"] != manifest["preflop_line"]:
        raise FetchError(
            MALFORMED_INDEX,
            f"the index is for {index['preflop_line']!r}, the manifest for"
            f" {manifest['preflop_line']!r}",
        )
    if not isinstance(index["boards"], list):
        raise FetchError(MALFORMED_INDEX, "the index's boards must be a list")
    return index


def _index_boards(index: Mapping[str, Any]) -> dict[tuple[str, ...], dict[str, Any]]:
    listed: dict[tuple[str, ...], dict[str, Any]] = {}
    for entry in index["boards"]:
        if not isinstance(entry, dict) or set(entry) != _INDEX_BOARD_KEYS:
            raise FetchError(
                MALFORMED_INDEX, f"an index board holds exactly {sorted(_INDEX_BOARD_KEYS)}"
            )
        board = entry["board"]
        if not isinstance(board, list) or not all(isinstance(card, str) for card in board):
            raise FetchError(MALFORMED_INDEX, f"{board!r} is not a board")
        if tuple(board) in listed:
            raise FetchError(MALFORMED_INDEX, f"the index lists {''.join(board)} twice")
        listed[tuple(board)] = entry
    return listed


def _check_index_counts(
    manifest: Mapping[str, Any], listed: Mapping[tuple[str, ...], Mapping[str, Any]]
) -> dict[tuple[str, ...], dict[str, dict[str, str]]]:
    """Each board's counts in the index against the manifest's, and the objects each closed board
    lists. Returns the closed boards' objects by street."""
    boards = {tuple(entry["board"]): entry for entry in manifest["boards"]}
    unknown = sorted("".join(board) for board in set(listed) - set(boards))
    if unknown:
        raise FetchError(
            DECISION_POINTS_MISMATCH, f"the index lists boards no manifest holds: {unknown}"
        )
    objects: dict[tuple[str, ...], dict[str, dict[str, str]]] = {}
    for board, entry in boards.items():
        name = "".join(board)
        if entry["status"] != CLOSED:
            if board in listed and (
                listed[board]["decision_points"] != entry["decision_points"]
                or listed[board]["objects"]
            ):
                raise FetchError(DECISION_POINTS_MISMATCH, f"{name} is refused, the index holds it")
            continue
        if board not in listed:
            raise FetchError(DECISION_POINTS_MISMATCH, f"{name} is closed and the index omits it")
        held = listed[board]["decision_points"]
        if isinstance(held, dict) and "river" in held:
            raise FetchError(DECISION_POINTS_MISMATCH, f"the index lists a river count on {name}")
        if held != entry["decision_points"]:
            raise FetchError(
                DECISION_POINTS_MISMATCH,
                f"{name}: the index holds {held}, the manifest {entry['decision_points']}",
            )
        street_objects = listed[board]["objects"]
        if not isinstance(street_objects, dict) or set(street_objects) != set(STORED_STREETS):
            raise FetchError(
                MALFORMED_INDEX, f"{name} must list one object for each of {STORED_STREETS}"
            )
        for street, reference in street_objects.items():
            if not isinstance(reference, dict) or set(reference) != _OBJECT_KEYS:
                raise FetchError(
                    MALFORMED_INDEX, f"{name} {street}: an object is a key and a sha256"
                )
        objects[board] = street_objects
    return objects


def _flop_keys(data: bytes, origin: str) -> list[str]:
    try:
        document = read_strict_json(data, origin)
    except ValueError as error:
        raise FetchError(DECISION_POINTS_MISMATCH, f"{origin} cannot be read: {error}") from error
    cells = document.get("cells") if isinstance(document, dict) else None
    if not isinstance(cells, list) or set(document) != {"cells"}:
        raise FetchError(DECISION_POINTS_MISMATCH, f"{origin} is not a flop object of cells")
    keys = [cell.get("spot_key") if isinstance(cell, dict) else None for cell in cells]
    if not all(isinstance(key, str) for key in keys):
        raise FetchError(DECISION_POINTS_MISMATCH, f"{origin} holds a cell with no spot key")
    return keys


def _check_contents(
    line: str, board: tuple[str, ...], street: str, counts: Mapping[str, int], data: bytes, key: str
) -> None:
    """An object whose digest is right still holds what its board's counts say, or is refused."""
    if street == "flop":
        held_keys = _flop_keys(data, key)
        expected_keys = list(lines.flop_spot_keys(line, board))
        if len(expected_keys) != counts["flop"]:
            raise FetchError(
                DECISION_POINTS_MISMATCH,
                f"{line} names {len(expected_keys)} flop decision points and its tree closes on"
                f" {counts['flop']}",
            )
        if sorted(held_keys) != sorted(expected_keys):
            missing = sorted(set(expected_keys) - set(held_keys))
            extra = sorted(set(held_keys) - set(expected_keys))
            repeated = sorted({spot for spot in held_keys if held_keys.count(spot) > 1})
            raise FetchError(
                DECISION_POINTS_MISMATCH,
                f"{key} is not the {len(expected_keys)} flop decision points of {line} on"
                f" {''.join(board)}: missing {missing}, not in the tree {extra}, twice {repeated}",
            )
        return
    try:
        held = street_object_decision_points(data)
    except ValueError as error:
        raise FetchError(DECISION_POINTS_MISMATCH, f"{key} cannot be counted: {error}") from error
    if held != counts[street]:
        raise FetchError(
            DECISION_POINTS_MISMATCH,
            f"{key} holds {held} {street} decision points; its board's counts claim"
            f" {counts[street]}",
        )


def _object_bytes(store: ObjectStore, path: Path, key: str, digest: str) -> bytes:
    """An object already on disk with the listed digest is kept rather than pulled again."""
    if path.is_file():
        held = path.read_bytes()
        if _sha256(held) == digest:
            return held
    return store.get(key)


def fetch_line(
    manifest: Mapping[str, Any],
    store: ObjectStore,
    root: Path,
    *,
    streets: Iterable[str] = ("flop",),
) -> dict[tuple[str, ...], dict[str, Path]]:
    """Fetch one line's index and every closed board's objects for `streets`, checking each.

    Returns where each object now lives, by board and street. Nothing that fails a check is
    written; an object that passed is kept even if a later one fails, since its own checks hold."""
    chosen = _streets(streets)
    line = _check_manifest(manifest)
    reference = manifest["index"]
    index_bytes = store.get(reference["object_key"])
    index = _parse_index(manifest, index_bytes)
    objects = _check_index_counts(manifest, _index_boards(index))
    counts = {tuple(entry["board"]): entry["decision_points"] for entry in manifest["boards"]}
    fetched: dict[tuple[str, ...], dict[str, Path]] = {}
    for board, street_objects in objects.items():
        for street in chosen:
            key, digest = street_objects[street]["key"], street_objects[street]["sha256"]
            path = _local_path(root, key)
            data = _object_bytes(store, path, key, digest)
            if (found := _sha256(data)) != digest:
                raise FetchError(
                    OBJECT_DIGEST_MISMATCH, f"{key} has sha256 {found}; the index lists {digest}"
                )
            _check_contents(line, board, street, counts[board], data, key)
            _write(path, data)
            fetched.setdefault(board, {})[street] = path
    _write(_local_path(root, reference["object_key"]), index_bytes)
    return fetched


def read_fetched_index(manifest: Mapping[str, Any], root: Path) -> dict[str, Any]:
    """The line index on disk, checked against the manifest's fingerprint, or a refusal."""
    index_key = manifest["index"]["object_key"]
    path = _local_path(root, index_key)
    if not path.is_file():
        raise FetchError(NOT_FETCHED, f"line index not fetched: {index_key}")
    return _parse_index(manifest, path.read_bytes())


def require_fetched(
    manifest: Mapping[str, Any], root: Path, *, street: str = "flop"
) -> dict[tuple[str, ...], Path]:
    """Every closed board's object for `street` on disk, with its listed digest, or a refusal.

    Returns where each board's object lives. A board whose object is not on disk refuses as
    `NOT_FETCHED`; one whose bytes changed since the fetch refuses as `OBJECT_DIGEST_MISMATCH`,
    because what the player would read is no longer what the index lists."""
    (street,) = _streets((street,))
    _check_manifest(manifest)
    objects = _check_index_counts(manifest, _index_boards(read_fetched_index(manifest, root)))
    held: dict[tuple[str, ...], Path] = {}
    for board, street_objects in objects.items():
        key, digest = street_objects[street]["key"], street_objects[street]["sha256"]
        path = _local_path(root, key)
        if not path.is_file():
            raise FetchError(NOT_FETCHED, f"{street} object not fetched: {key}")
        if _sha256(path.read_bytes()) != digest:
            raise FetchError(OBJECT_DIGEST_MISMATCH, f"{key} changed on disk since it was fetched")
        held[board] = path
    return held
