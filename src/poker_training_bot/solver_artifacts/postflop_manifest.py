"""The manifest git holds for each solved preflop line, its checks, and coverage counted from it.

Decision 3, ruled by Taylor on 2026-09-26: the full index of a line lives in object storage beside
its solves, and git holds a manifest per line - the flops held and one fingerprint of that line's
index file - so the repo proves what it points to and the report counts coverage offline. One JSON
file per admitted line under `MANIFEST_DIR`, named by `manifest_path`:

    {"manifest_schema_version": 1,
     "preflop_line": "BTN:raise@2.5,BB:call",
     "index": {"object_key": "...", "sha256": "<64 hex>", "bytes": <int>},
     "flops_held": <flops the closed boards stand for, of 22,100>,
     "refused_boards": <how many boards below are refused>,
     "boards": [{"board": [...], "status": "closed" | "refused",
                 "decision_points": {"flop": ..., "turn": ...},
                 "achieved_exploitability_pct_of_pot": ..., "iterations": ...,
                 "machine": "...", "threads": ...,
                 "strategy_digests": {"<spot key>": "<sha256>"}}]}

`strategy_digests` is optional: a board whose cells the committed `index.json` lists carries the
strategy digest of each of those spots from its closing solve.

**A board closes on its own line's tree, or refuses all of it.** A closed board's per-street
decision points must equal the closure counts of the tree its line builds, the flop and the turn,
counted by `postflop_tree_size` from the line's own pot - never a table pasted here, because the
small blind's 5.0 pot builds another tree than the button's 5.5. A refused board carries zero on
every stored street. **The river is never stored** (decision 1, re-ruled 2026-10-04), so any river
count, zero included, claims a store that does not exist and is refused.

**The commit rule is phase 16's** (decision 8), judged by `postflop_solve_driver.commit_verdict`
itself rather than restated: a closed board is one that rule commits, a refused board one it
refuses, and neither may have run past the iteration cap.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from poker_training_bot.solver_artifacts import postflop_isomorphism as isomorphism
from poker_training_bot.solver_artifacts import postflop_lines as lines
from poker_training_bot.solver_artifacts import postflop_textures as textures
from poker_training_bot.solver_artifacts import postflop_tree_size as tree_size
from poker_training_bot.solver_artifacts.postflop_artifact import (
    POSTFLOP_DIR,
    SAMPLE_DIR,
    SOLVE_ITERATION_CAP,
    import_postflop_sample,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (
    SolveOutcome,
    classify_outcome,
    commit_verdict,
)
from poker_training_bot.solver_artifacts.strict_json import _object_pairs_hook

MANIFEST_DIR = POSTFLOP_DIR / "manifests"
MANIFEST_SCHEMA_VERSION = 1
LINE_INDEX_SCHEMA_VERSION = 1
STORED_STREETS = ("flop", "turn")
"""What a closed board keeps. The river is solved at the table and never stored."""

CLOSED = "closed"
REFUSED = "refused"

_SHA256 = re.compile(r"[0-9a-f]{64}")
_MANIFEST_KEYS = frozenset(
    {"manifest_schema_version", "preflop_line", "index", "flops_held", "refused_boards", "boards"}
)
_INDEX_REF_KEYS = frozenset({"object_key", "sha256", "bytes"})
_BOARD_KEYS = frozenset(
    {
        "board",
        "status",
        "decision_points",
        "achieved_exploitability_pct_of_pot",
        "iterations",
        "machine",
        "threads",
    }
)
_OPTIONAL_BOARD_KEYS = frozenset({"strategy_digests"})


def manifest_path(line: str, directory: Path = MANIFEST_DIR) -> Path:
    """Where a line's manifest lives: `BTN:raise@2.5,BB:call` is `btn-raise-bb-call.json`."""
    words = []
    for step in line.split(","):
        position, _, action = step.partition(":")
        words += [position.lower(), action.split("@")[0]]
    return directory / f"{'-'.join(words)}.json"


def line_object_prefix(line: str) -> str:
    """The object-storage folder of one line's index and objects: `postflop/btn-v-bb`."""
    opener = line.split(":")[0].lower()
    return f"postflop/{opener}-v-bb"


def index_object_key(line: str) -> str:
    return f"{line_object_prefix(line)}/index.json"


def street_object_key(line: str, board: tuple[str, ...] | list[str], street: str) -> str:
    """A board's object for one stored street: the flop as JSON cells, the turn as rows."""
    if street not in STORED_STREETS:
        raise ValueError(f"only {STORED_STREETS} are stored; {street!r} has no object")
    suffix = "flop.json" if street == "flop" else f"{street}.bin"
    return f"{line_object_prefix(line)}/{''.join(board)}.{suffix}"


@cache
def _closure(line: str) -> tuple[tuple[str, int], ...]:
    figures = tree_size.line_tree_figures(line)
    return tuple(sorted(dict(tree_size.closure_counts(figures)).items()))


def expected_closure_counts(line: str) -> dict[str, int]:
    """The flop and turn decision points one solve of `line` holds on any board, from its tree."""
    if line not in lines.ADMITTED_LINES:
        raise ValueError(f"{line!r} is not an admitted line, so it has no tree to close on")
    return dict(_closure(line))


def decision_point_errors(line: str, entry: Mapping[str, Any]) -> list[str]:
    """What is wrong with one board's per-street counts, against its own line's tree.

    Shared by `manifest_errors` and the fetch, so the manifest and an index are held to one
    closure rule."""
    where = f"board {entry.get('board')!r}"
    points = entry.get("decision_points")
    if not isinstance(points, dict):
        return [f"{where}: decision_points must be an object, got {points!r}"]
    errors = []
    if "river" in points:
        errors.append(
            f"{where}: carries a river count ({points['river']!r}); the river is never stored"
        )
    if any(not isinstance(value, int) or isinstance(value, bool) for value in points.values()):
        errors.append(f"{where}: every decision point count must be an integer: {points!r}")
    if entry.get("status") == REFUSED:
        if points != dict.fromkeys(STORED_STREETS, 0):
            errors.append(f"{where}: a refused board carries zero on every stored street: {points}")
    elif entry.get("status") == CLOSED:
        try:
            expected_points = expected_closure_counts(line)
        except ValueError as error:
            return [*errors, f"{where}: {error}"]
        if entry["decision_points"] != expected_points:
            errors.append(
                f"{where}: closed on {points}, but one solve of {line} holds {expected_points}"
            )
    return errors


def _is_count(value: Any, minimum: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _canonical(board: Any) -> tuple[str, ...] | None:
    if not isinstance(board, list) or not all(isinstance(card, str) for card in board):
        return None
    try:
        return isomorphism.canonical_board(board)
    except ValueError:
        return None


def _verdict_errors(where: str, line: str, entry: Mapping[str, Any]) -> list[str]:
    """The commit rule, applied by the solve driver's own verdict."""
    exploit, iterations = entry["achieved_exploitability_pct_of_pot"], entry["iterations"]
    if not _is_number(exploit) or exploit < 0:
        return [f"{where}: exploitability must be a non-negative number, got {exploit!r}"]
    if not _is_count(iterations, 1):
        return [f"{where}: iterations must be a positive integer, got {iterations!r}"]
    if iterations > SOLVE_ITERATION_CAP:
        return [f"{where}: {iterations} iterations is past the {SOLVE_ITERATION_CAP} cap"]
    outcome = SolveOutcome(
        label="manifest board",
        board="".join(entry["board"]),
        preflop_line=line,
        outcome=classify_outcome(float(exploit), iterations),
        exploit_pct_of_pot=float(exploit),
        iterations=iterations,
        wall_seconds=0.0,
        arena_bytes=0,
    )
    commits, reason = commit_verdict(outcome)
    if entry["status"] == CLOSED and not commits:
        return [f"{where}: closed, but the commit rule refuses it: {reason}"]
    if entry["status"] == REFUSED and commits:
        return [f"{where}: refused, but the commit rule commits it: {reason}"]
    return []


def _digest_errors(where: str, line: str, entry: Mapping[str, Any]) -> list[str]:
    digests = entry["strategy_digests"]
    if not isinstance(digests, dict):
        return [f"{where}: strategy_digests must be an object"]
    if entry["status"] != CLOSED:
        return [f"{where}: only a closed board carries strategy digests"]
    errors = [
        f"{where}: strategy digest of {spot} is not one sha256"
        for spot, digest in digests.items()
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest)
    ]
    keys = set(lines.flop_spot_keys(line, tuple(entry["board"])))
    errors += [
        f"{where}: {spot} is not a flop decision point of {line} on this board"
        for spot in sorted(set(digests) - keys)
    ]
    return errors


def _board_errors(line: str, position: int, entry: Any) -> list[str]:
    where = f"boards[{position}]"
    if not isinstance(entry, dict):
        return [f"{where} must be an object"]
    missing = sorted(_BOARD_KEYS - set(entry))
    unknown = sorted(set(entry) - _BOARD_KEYS - _OPTIONAL_BOARD_KEYS)
    if missing or unknown:
        return [f"{where}: missing keys {missing}, unknown keys {unknown}"]
    canonical = _canonical(entry["board"])
    if canonical is None:
        return [f"{where}: {entry['board']!r} is not a flop"]
    if tuple(entry["board"]) != canonical:
        return [f"{where}: {entry['board']} is not its class's canonical dressing {canonical}"]
    where = f"board {''.join(canonical)}"
    if entry["status"] not in (CLOSED, REFUSED):
        return [f"{where}: unknown status {entry['status']!r}"]
    errors = []
    if not isinstance(entry["machine"], str) or not entry["machine"]:
        errors.append(f"{where}: names no machine it was solved on")
    if not _is_count(entry["threads"], 1):
        errors.append(f"{where}: names no thread count it was solved at: {entry['threads']!r}")
    errors += _verdict_errors(where, line, entry)
    errors += decision_point_errors(line, entry)
    if "strategy_digests" in entry:
        errors += _digest_errors(where, line, entry)
    return errors


def _index_reference_errors(reference: Any) -> list[str]:
    if not isinstance(reference, dict) or set(reference) != _INDEX_REF_KEYS:
        return [f"index must hold exactly {sorted(_INDEX_REF_KEYS)}, got {reference!r}"]
    errors = []
    if not isinstance(reference["object_key"], str) or not reference["object_key"]:
        errors.append("index.object_key must name the line index's object")
    if not isinstance(reference["sha256"], str) or not _SHA256.fullmatch(reference["sha256"]):
        errors.append("index.sha256 must be one sha256 in lowercase hex")
    if not _is_count(reference["bytes"], 1):
        errors.append(f"index.bytes must be a positive integer, got {reference['bytes']!r}")
    return errors


def manifest_errors(manifest: Any) -> list[str]:
    """Every inconsistency in one line's manifest, empty when it holds together."""
    if not isinstance(manifest, dict) or set(manifest) != _MANIFEST_KEYS:
        keys = sorted(manifest) if isinstance(manifest, dict) else type(manifest).__name__
        return [f"a manifest holds exactly {sorted(_MANIFEST_KEYS)}, got {keys}"]
    errors = []
    if manifest["manifest_schema_version"] != MANIFEST_SCHEMA_VERSION:
        errors.append(f"manifest schema {manifest['manifest_schema_version']!r} is unsupported")
    line = manifest["preflop_line"]
    if line not in lines.ADMITTED_LINES:
        return [*errors, f"{line!r} is not an admitted line"]
    errors += _index_reference_errors(manifest["index"])
    boards = manifest["boards"]
    if not isinstance(boards, list):
        return [*errors, "boards must be a list"]
    seen: set[tuple[str, ...]] = set()
    for position, entry in enumerate(boards):
        board_errors = _board_errors(line, position, entry)
        errors += board_errors
        if isinstance(entry, dict) and (canonical := _canonical(entry.get("board"))):
            if canonical in seen:
                errors.append(f"board {''.join(canonical)} is listed twice")
            seen.add(canonical)
    if errors:
        return errors
    refused = sum(entry["status"] == REFUSED for entry in boards)
    if not _is_count(manifest["refused_boards"], 0) or manifest["refused_boards"] != refused:
        errors.append(f"refused_boards says {manifest['refused_boards']!r}, the boards {refused}")
    held = sum(
        textures.flops_in_class(tuple(entry["board"]))
        for entry in boards
        if entry["status"] == CLOSED
    )
    if not _is_count(manifest["flops_held"], 0) or manifest["flops_held"] != held:
        errors.append(
            f"flops_held says {manifest['flops_held']!r}, the closed boards stand for {held}"
        )
    return errors


def read_strict_json(data: bytes | str, origin: str) -> Any:
    """JSON that refuses a key given twice, which `json.loads` would silently keep the last of."""
    try:
        payload = json.loads(data, object_pairs_hook=_object_pairs_hook)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"{origin} is not valid JSON: {error}") from error
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if getattr(item, "duplicate_keys", ()):
                raise ValueError(f"{origin} repeats keys {list(item.duplicate_keys)}")
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return payload


def load_manifests(directory: Path = MANIFEST_DIR) -> dict[str, dict[str, Any]]:
    """Every manifest in `directory`, keyed by its preflop line.

    Reading is not checking: `manifest_errors` judges each one. A missing folder is refused rather
    than read as no line held, because the folder is committed and its absence is a broken
    checkout or a wrong path, not a fresh clone."""
    folder = Path(directory)
    if not folder.is_dir():
        raise FileNotFoundError(f"no manifest folder at {folder}")
    manifests: dict[str, dict[str, Any]] = {}
    for path in sorted(folder.glob("*.json")):
        manifest = read_strict_json(path.read_bytes(), str(path))
        line = manifest.get("preflop_line") if isinstance(manifest, dict) else None
        if not isinstance(line, str):
            raise ValueError(f"{path} names no preflop line")
        if line in manifests:
            raise ValueError(f"{path} is a second manifest for {line}")
        if path.name != manifest_path(line, folder).name:
            raise ValueError(f"{path} holds {line}, whose manifest is {manifest_path(line).name}")
        manifests[line] = manifest
    return manifests


@dataclass(frozen=True)
class Coverage:
    """What a fresh clone and a fetched machine can answer, counted from the manifests.

    A fresh clone answers the boards whose cells are committed in `sample/`; a fetched machine
    answers every closed board. Lines and seats are counted under different words: a closed board
    is closed for both seats of its line, so each line holding one is two seats."""

    fresh_clone_classes: int
    fresh_clone_flops: int
    classes_held: dict[str, int]
    flops_held: dict[str, int]
    by_texture: dict[str, dict[str, int]]
    lines: int
    seats: int


def coverage(manifests: Mapping[str, Mapping[str, Any]], sample_dir: Path = SAMPLE_DIR) -> Coverage:
    """Coverage by line and by texture group, refusing a manifest that fails its own checks."""
    for line, manifest in manifests.items():
        errors = manifest_errors(manifest)
        if errors:
            raise ValueError(f"the manifest for {line} fails its checks: {errors}")
        if manifest["preflop_line"] != line:
            raise ValueError(f"the manifest filed under {line} is for {manifest['preflop_line']}")
    fresh = {isomorphism.canonical_board(cell.board) for cell in import_postflop_sample(sample_dir)}
    classes_held, flops_held, by_texture = {}, {}, {}
    for line, manifest in manifests.items():
        closed = [
            tuple(entry["board"]) for entry in manifest["boards"] if entry["status"] == CLOSED
        ]
        classes_held[line] = len(closed)
        flops_held[line] = sum(textures.flops_in_class(board) for board in closed)
        groups = dict.fromkeys(textures.TEXTURE_GROUPS, 0)
        for board in closed:
            groups[textures.texture_group(board)] += 1
        by_texture[line] = groups
    held_lines = sum(1 for count in classes_held.values() if count)
    return Coverage(
        fresh_clone_classes=len(fresh),
        fresh_clone_flops=sum(textures.flops_in_class(board) for board in fresh),
        classes_held=classes_held,
        flops_held=flops_held,
        by_texture=by_texture,
        lines=held_lines,
        seats=2 * held_lines,
    )
