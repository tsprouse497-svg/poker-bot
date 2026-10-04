"""Whether a solve came out the same twice: the box re-run, and the re-solve against git.

Two questions, kept apart because the contract keeps them apart.

**A re-run** is phase 16's four boards solved twice on one machine, in two processes against a
restarted server, and compared the way `data/artifacts/postflop/determinism.json` compares them.
`rerun_verdict` reads every cell rather than the document's own `identical` flag, and refuses a
pair of runs whose wall clocks agree to the microsecond, because that is one run compared with
itself. `matches_committed` is the separate finding - whether that machine also reproduced the
M4's committed digests - and is never a pass condition for the re-run.

**A re-solve** is the same four boards solved again at another thread count, and it must
reproduce the committed cell documents byte for byte, the fifth cell's strategy digest, and every
per-combo strategy exactly. `reproduction_errors` holds the first two against the bytes git holds;
`compare_node_payloads` holds the third against the solver's own answers in the committed run's
objects. No tolerance is set anywhere here: the contract rules that a re-solve that does not
reproduce halts the phase and Taylor is asked.
"""

from __future__ import annotations

import gzip
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from poker_training_bot.solver_artifacts.postflop_artifact import INDEX_PATH, SAMPLE_DIR
from poker_training_bot.solver_artifacts.postflop_harvest import strategy_digest

# --- One node's per-combo strategies, compared exactly


def compare_node_payloads(one: Mapping[str, Any], two: Mapping[str, Any]) -> dict[str, Any]:
    """Two answers for one node compared per combo, under the rounding rather than over it.

    The committed rows are thousandths and the solver answers in floats, so two runs can differ
    by a ten-thousandth and still write the same committed bytes. This looks at what the solver
    produced, which is the only place a difference that small is visible at all.
    """
    if one["actions"] != two["actions"]:
        return {"menu_matched": False, "combos_in_only_one_run": None, "largest_gap": None}
    rows_one = {
        str(hand["combo"]): [float(value) for value in hand["strategy"]]
        for hand in one["players"][int(one["player"])]["hands"]
    }
    rows_two = {
        str(hand["combo"]): [float(value) for value in hand["strategy"]]
        for hand in two["players"][int(two["player"])]["hands"]
    }
    shared = sorted(set(rows_one) & set(rows_two))
    gaps = [
        max(abs(a - b) for a, b in zip(rows_one[combo], rows_two[combo], strict=True))
        for combo in shared
    ]
    return {
        "menu_matched": True,
        "combos": len(rows_one),
        "combos_in_only_one_run": len(set(rows_one) ^ set(rows_two)),
        "largest_gap": max(gaps) if gaps else None,
    }


def per_combo_identical(comparison: Mapping[str, Any]) -> bool:
    return (
        comparison.get("menu_matched") is True
        and comparison.get("combos_in_only_one_run") == 0
        and comparison.get("largest_gap") == 0.0
    )


# --- The re-run on one machine


def _pair(cell: Mapping[str, Any], field: str) -> tuple[Any, Any]:
    value = cell.get(field)
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"cell {cell.get('cell')!r} has no pair of {field}: {value!r}")
    return value[0], value[1]


def rerun_verdict(document: Mapping[str, Any]) -> bool:
    """True when every cell of a two-run record came out identical in both runs.

    Read cell by cell, never from the record's own `identical` flag. A cell whose two wall clocks
    agree to the microsecond is refused with `ValueError`: two runs do not, so the second is a
    copy of the first and comparing it proves nothing."""
    cells = document.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("a re-run record must carry the cells it compared")
    identical = True
    for cell in cells:
        first, second = _pair(cell, "wall_seconds")
        if round(float(first), 6) == round(float(second), 6):
            raise ValueError(
                f"cell {cell.get('cell')!r} reports the same wall clock for both runs to the"
                " microsecond; the second run is a copy of the first, not a second run"
            )
        for field in ("iterations", "achieved_exploitability_pct_of_pot", "strategy_digest"):
            one, two = _pair(cell, field)
            identical = identical and one == two
        identical = identical and cell.get("cell_document_bytes_identical") is True
        identical = identical and per_combo_identical(cell.get("per_combo") or {})
    return identical


def matches_committed(document: Mapping[str, Any], index: Mapping[str, Any]) -> bool:
    """Whether both runs of a re-run record reproduced the committed index's strategy digests. A
    finding beside `rerun_verdict`, never a condition of it."""
    committed = {entry["spot_key"]: entry["strategy_digest"] for entry in index["entries"]}
    for cell in document["cells"]:
        wanted = committed.get(cell["spot_key"])
        if wanted is None or any(digest != wanted for digest in _pair(cell, "strategy_digest")):
            return False
    return True


# --- The re-solve against what git holds


def committed_cells(sample_dir: Path = SAMPLE_DIR) -> dict[str, bytes]:
    return {path.stem: path.read_bytes() for path in sorted(sample_dir.glob("*.json"))}


def committed_digests(index_path: Path = INDEX_PATH) -> dict[str, str]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    return {entry["spot_key"]: entry["strategy_digest"] for entry in index["entries"]}


def reproduction_errors(
    cells: Mapping[str, bytes],
    digests: Mapping[str, str],
    *,
    sample_dir: Path = SAMPLE_DIR,
    index_path: Path = INDEX_PATH,
) -> list[str]:
    """Every way a re-solve fails to reproduce the committed sample and index; empty when exact.

    `cells` is each held cell document the re-solve wrote, by name, as bytes; `digests` is the
    strategy digest of every spot it solved, by spot key - which is how the fifth cell, indexed
    but not held in git, is checked at all. Bytes are compared as bytes and digests as strings:
    nothing here parses a number, so nothing here can round one."""
    errors: list[str] = []
    expected_cells = committed_cells(sample_dir)
    for name, committed in sorted(expected_cells.items()):
        if name not in cells:
            errors.append(f"the re-solve produced no {name} cell document")
        elif cells[name] != committed:
            errors.append(f"{name}: the re-solved cell document differs from the committed bytes")
    for name in sorted(set(cells) - set(expected_cells)):
        errors.append(f"{name}: the re-solve produced a cell document git does not hold")
    expected_digests = committed_digests(index_path)
    for spot_key, committed in sorted(expected_digests.items()):
        if spot_key not in digests:
            errors.append(f"{spot_key}: the re-solve produced no strategy digest")
        elif digests[spot_key] != committed:
            errors.append(
                f"{spot_key}: strategy digest {digests[spot_key]} differs from the committed"
                f" {committed}"
            )
    for spot_key in sorted(set(digests) - set(expected_digests)):
        errors.append(f"{spot_key}: the re-solve digested a spot the index does not list")
    return errors


def _load_object(path: Path) -> dict[str, Any]:
    with gzip.open(path) as stream:
        return json.loads(stream.read())


def _cell_digest(document: Mapping[str, Any]) -> str:
    return strategy_digest(
        list(document["hand_classes"]), [list(row) for row in document["class_weights"]]
    )


def resolve_document(
    resolved_tree: Path,
    resolved_objects: Path,
    manifest: Mapping[str, Any],
    *,
    sample_dir: Path = SAMPLE_DIR,
    index_path: Path = INDEX_PATH,
) -> dict[str, Any]:
    """The re-solve, compared every way the contract names, as a record.

    `resolved_tree` is the postflop tree a re-solve wrote (never the committed one) and
    `resolved_objects` its object directory; `manifest` is the committed `objects.json`, which
    says where the committed run's objects are. Wall clocks are kept unrounded, both of them."""
    if resolved_tree.resolve() == sample_dir.parent.resolve():
        raise ValueError(
            "the re-solved tree is the committed one; that compares a file with itself"
        )
    held = {
        name: (resolved_tree / "sample" / f"{name}.json").read_bytes()
        for name in committed_cells(sample_dir)
        if (resolved_tree / "sample" / f"{name}.json").is_file()
    }
    pairs: list[tuple[str, str, bool, Path, Path]] = []
    for name in sorted(committed_cells(sample_dir)):
        spot_key = json.loads((sample_dir / f"{name}.json").read_text(encoding="utf-8"))["spot_key"]
        committed_object = Path(manifest["objects"][spot_key]["object_path"])
        pairs.append(
            (name, spot_key, True, committed_object, resolved_tree / "sample" / f"{name}.json")
        )
    for spot_key, figures in sorted(manifest.get("listed_not_held", {}).items()):
        document_path = Path(figures["cell_document"])
        name = document_path.name.removesuffix(".cell.json")
        committed_object = document_path.parent / f"srp-{''.join(figures['board'])}.nodes.json.gz"
        pairs.append(
            (name, spot_key, False, committed_object, resolved_objects / document_path.name)
        )
    digests: dict[str, str] = {}
    cells: list[dict[str, Any]] = []
    for name, spot_key, in_repo, committed_object, resolved_cell in pairs:
        resolved_document = json.loads(resolved_cell.read_text(encoding="utf-8"))
        digests[resolved_document["spot_key"]] = _cell_digest(resolved_document)
        one = _load_object(committed_object)
        two = _load_object(resolved_objects / committed_object.name)
        cells.append(
            {
                "cell": name,
                "spot_key": spot_key,
                "held_in_the_repo": in_repo,
                "iterations": [one["solve"]["iterations"], two["solve"]["iterations"]],
                "achieved_exploitability_pct_of_pot": [
                    one["solve"]["exploit_pct_of_pot"],
                    two["solve"]["exploit_pct_of_pot"],
                ],
                "wall_seconds": [one["solve"]["wall_seconds"], two["solve"]["wall_seconds"]],
                "threads": [None, two["solve"].get("threads")],
                "peak_resident_bytes": [None, two["solve"].get("peak_resident_bytes")],
                "resolved_strategy_digest": digests[resolved_document["spot_key"]],
                "per_combo": compare_node_payloads(one["nodes"][name], two["nodes"][name]),
            }
        )
    errors = reproduction_errors(held, digests, sample_dir=sample_dir, index_path=index_path)
    for cell in cells:
        if cell["iterations"][0] != cell["iterations"][1]:
            errors.append(f"{cell['cell']}: iterations {cell['iterations']}")
        pct = cell["achieved_exploitability_pct_of_pot"]
        if pct[0] != pct[1]:
            errors.append(f"{cell['cell']}: exploitability {pct}")
        if not per_combo_identical(cell["per_combo"]):
            errors.append(f"{cell['cell']}: per-combo strategies differ {cell['per_combo']}")
        if cell["wall_seconds"][0] == cell["wall_seconds"][1]:
            errors.append(f"{cell['cell']}: identical wall clocks, so this is a copy, not a solve")
    return {"reproduced": not errors, "errors": errors, "cells": cells}
