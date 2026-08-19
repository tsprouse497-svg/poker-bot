"""Solve one preflop tree in GTOpen and write it out as committed data. Offline, one-time.

This script is never run by the gate. It needs a GTOpen server, and the gate must pass on a
machine with no GTOpen, no Rust toolchain and no network - which is how the existing chart
artifact already works. What the gate reads is the export and the source card this writes.

Four HTTP calls do the extraction:

    POST /api/preflop/spot    build the tree from the ruled config
    POST /api/preflop/solve   run to a stated target, in the background
    GET  /api/preflop/status  poll until the state leaves "running"
    POST /api/preflop/node    one call per node, the path being action indices

`POST /api/preflop/save` runs between the solve and the walk, and decision 6c makes it
load-bearing rather than a convenience: the save carries the full config in its header,
including `allin_threshold`, which GTOpen's own web form cannot set. Loading that save is
the only way a human can put the exact ruled tree back on screen.

Usage:

    uv run python scripts/extract_gtopen_preflop.py --save-name six-max-100bb-rakefree
    uv run python scripts/extract_gtopen_preflop.py --determinism-only   # second run, diffed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from dataclasses import replace
from pathlib import Path

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.gtopen_export import (  # noqa: E402
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    RULED_CONFIG,
    SOLVE_ITERATION_CAP,
    SOLVE_TARGET_GAP_BB,
    SolverExport,
    export_checksum,
    node_from_payload,
    write_solver_export,
)

BASE_URL = "http://127.0.0.1:3737"
GTOPEN_ROOT = Path.home() / "projects" / "gtopen"
ARTIFACTS_DIR = REPO_ROOT / "data" / "artifacts"
BYTE_LIMIT = 20 * 1024 * 1024


def call(path: str, body: dict | None = None, timeout: float = 900.0) -> dict:
    request = urllib.request.Request(
        BASE_URL + path,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def solve(iterations: int, target_gap: float) -> tuple[dict, float]:
    started = time.time()
    call(
        "/api/preflop/solve",
        {"iterations": iterations, "check_every": 100, "target_gap": target_gap},
    )
    while True:
        status = call("/api/preflop/status")
        if status.get("state") != "running":
            return status, time.time() - started
        time.sleep(2.0)


def walk(action_nodes: int) -> tuple[list, int]:
    """Depth-first over the whole solved tree, then re-resolve every node from its own path.

    Terminality is not in a node view: an action ends the hand exactly when the child it
    leads to is not itself an action node, so the walker asks for each child and records
    what it found. That is also how the traversal closes - a branch that was silently
    dropped is indistinguishable from a tree that never had it.

    `/api/preflop/node` walks from the root on every call, so a misread path encoding does
    not error, it quietly returns a different node. The second pass asks again for every
    node by its own recorded action sequence and counts the disagreements, which is the
    only self-check available for an encoding the gate can never re-derive offline.
    """
    root = call("/api/preflop/node", {"path": []})
    nodes = []
    stack: list[tuple[tuple[int, ...], dict]] = [((), root)]
    while stack:
        path, view = stack.pop()
        terminal = []
        for index in range(len(view["actions"])):
            child = call("/api/preflop/node", {"path": [*path, index]})
            is_action = child.get("kind") == "action"
            terminal.append(not is_action)
            if is_action:
                stack.append(((*path, index), child))
        nodes.append(node_from_payload(view, path, terminal))
        if len(nodes) % 2000 == 0:
            print(f"  walked {len(nodes)} of {action_nodes} action nodes", flush=True)
    mismatches = 0
    for position, node in enumerate(nodes):
        again = call("/api/preflop/node", {"path": list(node.path)})
        labels = [action["label"] for action in again.get("actions", [])]
        if again.get("actor_pos") != node.actor_pos or labels != [a.label for a in node.actions]:
            mismatches += 1
        if position and position % 5000 == 0:
            print(f"  re-resolved {position} of {len(nodes)} nodes", flush=True)
    return nodes, mismatches


def build_export(save: dict | None) -> tuple[SolverExport, dict, dict, float]:
    print("building the ruled tree", flush=True)
    counts = call("/api/preflop/spot", dict(RULED_CONFIG))
    print(f"  {counts}", flush=True)
    status, wall_clock = solve(SOLVE_ITERATION_CAP, SOLVE_TARGET_GAP_BB)
    print(f"  solved in {wall_clock:.1f}s at iteration {status['iteration']}", flush=True)
    if save is not None:
        call("/api/preflop/save", {"name": save["name"]})
        loaded = call("/api/preflop/load", {"name": save["name"]})
        print(f"  saved and reloaded: {loaded.get('ok', loaded)}", flush=True)
    nodes, mismatches = walk(counts["action_nodes"])
    print(f"  walked {len(nodes)} action nodes, {mismatches} mismatch(es)", flush=True)
    export = SolverExport.from_nodes(
        nodes,
        config=dict(RULED_CONFIG),
        positions=list(RULED_CONFIG["positions"]),
        saved_solve=save,
    )
    return export, counts, {"status": status, "mismatches": mismatches}, wall_clock


def saved_solve_facts(name: str) -> dict:
    path = GTOPEN_ROOT / "saves" / "preflop" / f"{name}.gtop"
    if not path.exists():
        matches = sorted((GTOPEN_ROOT / "saves" / "preflop").glob(f"{name}*"))
        if not matches:
            raise SystemExit(f"no saved solve found for {name!r} under {path.parent}")
        path = matches[0]
    data = path.read_bytes()
    return {
        "path": str(path),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def directory_bytes() -> int:
    return sum(path.stat().st_size for path in ARTIFACTS_DIR.rglob("*") if path.is_file())


def record_determinism() -> int:
    """Solve the ruled config a second time, walk it again, and diff it node by node.

    Run in a fresh process against a server that has been restarted, this is the whole of
    what the contract asks for: either the two extractions are byte-identical, or the
    largest per-frequency divergence is what every later comparison has to be written
    against. It writes its own answer onto the source card, because a number a human types
    in afterwards is a number nobody re-derives.
    """
    from poker_training_bot.solver_artifacts.gtopen_export import load_solver_export

    second, _, _, _ = build_export(None)
    committed = load_solver_export(COMMITTED_EXPORT_PATH)
    first_by_path = committed.by_path()
    second_by_path = second.by_path()
    divergence = 0
    missing = sorted(set(first_by_path) ^ set(second_by_path))
    for path, node in first_by_path.items():
        other = second_by_path.get(path)
        if other is None:
            continue
        for row_a, row_b in zip(node.strategy_bp, other.strategy_bp, strict=True):
            for a, b in zip(row_a, row_b, strict=True):
                divergence = max(divergence, abs(a - b))
        for a, b in zip(node.reach_bp, other.reach_bp, strict=True):
            divergence = max(divergence, abs(a - b))
    identical = not missing and export_checksum(second) == export_checksum(committed)
    card = json.loads(COMMITTED_SOURCE_CARD_PATH.read_text(encoding="utf-8"))
    card["determinism"] = {
        "result": (
            "byte-identical"
            if identical
            else f"not byte-identical; divergence up to {divergence} basis points"
        ),
        "method": (
            "the ruled config solved and walked a second time in a fresh process against a"
            " restarted server, and the two exports diffed node by node"
        ),
        "max_divergence_bp": divergence,
        "shape_differences": len(missing),
    }
    write_card(card)
    print(json.dumps(card["determinism"], indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save-name", default="six-max-100bb-rakefree")
    parser.add_argument(
        "--determinism-only",
        action="store_true",
        help="re-solve and re-walk, then diff against the committed export",
    )
    args = parser.parse_args(argv)

    if args.determinism_only:
        return record_determinism()

    call("/api/preflop/spot", dict(RULED_CONFIG))
    export, counts, walked, wall_clock = build_export({"name": args.save_name})
    save = saved_solve_facts(args.save_name)
    export = replace(export, saved_solve=save)
    write_solver_export(COMMITTED_EXPORT_PATH, export)
    size = COMMITTED_EXPORT_PATH.stat().st_size
    total = directory_bytes()
    if total > BYTE_LIMIT:
        raise SystemExit(
            f"data/artifacts totals {total} bytes, over the ruled {BYTE_LIMIT} byte limit."
            " This is a halt and a decision, not a number to raise."
        )
    status = walked["status"]
    card = {
        "config_posted": dict(RULED_CONFIG),
        "solver": {"name": "gtopen", "commit": gtopen_commit(), "engine": "cpu"},
        "solve": {
            "target_gap_bb": SOLVE_TARGET_GAP_BB,
            "achieved_gap_bb": status["gap_total"],
            "iterations": status["iteration"],
            "iteration_cap": SOLVE_ITERATION_CAP,
            "wall_clock_seconds": round(wall_clock, 1),
        },
        "determinism": {
            "result": "PENDING - fill from --determinism-only",
            "method": (
                "the ruled config solved twice in a fresh process and the exports diffed"
            ),
            "max_divergence_bp": None,
        },
        "walk": {"reresolved_nodes": export.node_count, "mismatches": walked["mismatches"]},
        "node_counts": {
            "exported": export.node_count,
            "solver_action_nodes": counts["action_nodes"],
            "reconciliation": (
                "equal"
                if export.node_count == counts["action_nodes"]
                else "see the audit packet"
            ),
        },
        "conditioning": {
            "payload": "unconditional",
            "discriminator": (
                "at the LJ-versus-3bet node the class 72o arrives with a reach of about"
                " 3.7e-08, which quantises to zero basis points, and it still carries a"
                " full uniform strategy row at a quarter per action. The payload is"
                " therefore not conditioned on reaching the node, and reach is the only"
                " thing that conditions it"
            ),
        },
        "licence": (
            "GTOpen ships no LICENSE file upstream, and neither its README.md nor its"
            " Cargo.toml mentions licensing. This is an unresolved limitation rather than"
            " a permission anybody granted."
        ),
        "model": (
            "realization=calibrated. GTOpen's preflop engine resolves flops by scaled"
            " equity share rather than by playing them, so this is a preflop-only model"
            " and not a full solve."
        ),
        "size": {
            "bytes": size,
            "limit_bytes": BYTE_LIMIT,
            "headroom_bytes": BYTE_LIMIT - total,
            "bytes_per_node": round(size / export.node_count, 2),
            "bytes_per_expressible_spot": round(size / 36, 2),
            "bytes_per_expressible_spot_note": (
                "the whole export divided by the 36 spots the committed chart expresses"
                " today, so it is what keeping the entire tree costs per spot currently"
                " usable rather than the size of a derived chart. The roadmap's 7.1 KB per"
                " spot was measured off the GTO Wizard chart format and is not comparable"
            ),
        },
        "saved_solve": save,
        "export_sha256": export_checksum(export),
    }
    write_card(card)
    print(f"wrote {COMMITTED_EXPORT_PATH} ({size} bytes) and its source card")
    return 0


def write_card(card: dict) -> None:
    """Write the source card, with `headroom_bytes` counting the card itself.

    The headroom is what is left in `data/artifacts` after everything committed, and the
    card lives there too, so a figure taken before the card is written is short by the size
    of the file stating it. Its own digits move the total, so this settles to a fixed point
    rather than assuming one pass is enough.
    """
    for _ in range(8):
        COMMITTED_SOURCE_CARD_PATH.write_text(
            json.dumps(card, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        headroom = BYTE_LIMIT - directory_bytes()
        if card["size"]["headroom_bytes"] == headroom:
            return
        card["size"]["headroom_bytes"] = headroom
    raise SystemExit("the source card's headroom figure will not settle")


def gtopen_commit() -> str:
    head = (GTOPEN_ROOT / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        return (GTOPEN_ROOT / ".git" / head[5:]).read_text(encoding="utf-8").strip()
    return head


if __name__ == "__main__":
    raise SystemExit(main())
