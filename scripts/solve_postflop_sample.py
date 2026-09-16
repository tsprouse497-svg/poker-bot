"""Solve the committed flop sample and write it. Offline, one-time, never run by the gate.

**This script must never be registered in `COMMANDS` in `scripts/run_verify.py`.** `AGENTS.md`
forbids runtime solver calls, and phase 10's contract requires the gate to pass on a machine with
no GTOpen, no Rust toolchain and no network. What the gate reads is what this writes; running it
is a deliberate campaign, not a check.

**It restarts the GTOpen server between solves, and that is a measurement rather than hygiene.**
`docs/GTOPEN_SOLVER_NOTES.md` records that the server never returns freed pages to the OS and
that a process carrying a 10.3 GB high-water mark measured about 1.6x slower per iteration than
a freshly restarted one on the identical config. Nothing in `postflop_solve_driver` restarts
anything - it is handed a transport and assumes a server - so the restart lives here, once per
plan, and the wall clock this script reports is therefore a cold-start figure on every row.

**What it will not do.** It will not route around `check_memory_ceiling`: GTOpen's own guard
reads `/proc/meminfo`, which Darwin does not have, and falls through to a flat 48,000 MB it
cannot reach before this machine thrashes, so the driver's ceiling is the only one there is. It
will not use `/api/reports/*`, which `docs/GTOPEN_SOLVER_NOTES.md` records as README-sourced and
never executed, and which would be one long-lived process - the shape the restart above exists to
avoid. It will not invent a range: both sides come out of the committed preflop export, floored
class-level at `RANGE_WEIGHT_FLOOR`.

**The bytes the bot plays do not live in git.** Decision 6 puts the solved object in storage
outside the repo; what is committed is an index plus the sample. This writes the full per-combo
node payload to `--object-dir` outside the repo, digests it, and records that digest in the
index, so the index authenticates something that exists rather than something promised.

Usage:

    uv run python scripts/solve_postflop_sample.py --list
    uv run python scripts/solve_postflop_sample.py --cell monotone-connected-cbet
    uv run python scripts/solve_postflop_sample.py --all
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.gtopen_export import (  # noqa: E402
    COMMITTED_EXPORT_PATH,
    class_combos,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES  # noqa: E402
from poker_training_bot.solver_artifacts.postflop_artifact import (  # noqa: E402
    EXPLOITABILITY_CEILING_PCT_OF_POT,
    INDEX_PATH,
    INDEX_SCHEMA_VERSION,
    POSTFLOP_DIR,
    RANGE_WEIGHT_FLOOR,
    SAMPLE_DIR,
    floor_range,
    import_postflop_cell,
    import_postflop_index,
)
from poker_training_bot.solver_artifacts.postflop_harvest import (  # noqa: E402
    CLASS_AGREEMENT_TOLERANCE,
    cell_document,
    harvest_node,
    strategy_digest,
)
from poker_training_bot.solver_artifacts.postflop_key import (  # noqa: E402
    completed_preflop_line,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (  # noqa: E402
    MEASURING_MACHINE,
    SolvePlan,
    commit_verdict,
    describe_memory_ceiling,
    gtopen_memory_guard,
    run_solve,
    solve_config_document,
)
from poker_training_bot.solver_artifacts.postflop_transport import (  # noqa: E402
    BASE_URL,
    SolveDriverError,
    http_transport,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction  # noqa: E402
from poker_training_bot.solver_artifacts.solve_conditions import BlindStructure  # noqa: E402

ARTIFACT_ROOT = REPO_ROOT / "data" / "artifacts"
ARTIFACT_BYTE_CAP = 20 * 1024 * 1024
SOLVE_CONFIG_PATH = POSTFLOP_DIR / "solve_config.json"
OBJECT_MANIFEST_PATH = POSTFLOP_DIR / "objects.json"

DEFAULT_SERVER = Path.home() / "projects" / "GTOpen" / "target" / "release" / "gto-server"
DEFAULT_OBJECT_DIR = Path.home() / "poker-bot-solve-objects" / "postflop"

TABLE_SIZE = 6
STACK_DEPTH_BB = 100
BLINDS = BlindStructure(small_blind_bb=0.5, big_blind_bb=1.0, ante_bb=0.0)
OPEN_BB = 2.5

OOP_PLAYER = 0
IP_PLAYER = 1

SERVER_START_TIMEOUT_SECONDS = 60.0
SERVER_STOP_TIMEOUT_SECONDS = 30.0

ACTION = "action"


def path_step(index: int) -> dict[str, Any]:
    """One `PathStep` in GTOpen's own tagged shape, from `crates/solver/src/query.rs`."""
    return {"type": ACTION, "index": index}


# --------------------------------------------------------------------------- #
# The sample: which flops, which lines, and which node of each solved tree
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SampleCell:
    """One committed cell: a board, a completed preflop line, and one node of its solved tree.

    `board` is the canonical representative of its class, because a solve posted on the
    representative comes back with hero's combos already in the dressing a committed cell is
    written in and nothing has to be re-dressed afterwards.
    """

    name: str
    board: tuple[str, ...]
    hero_position: str
    node_path: tuple[int, ...]
    why: str

    @property
    def board_text(self) -> str:
        return "".join(self.board)


BTN_OPEN_BB_CALL = (PreflopAction("BTN", "raise", OPEN_BB), PreflopAction("BB", "call"))
"""The single-raised pot decision 3 ranks first: 99.0% of the corpus's opens fall inside
decision 10's band around it, against 47.1% of its 3-bets."""

PRICE_SUBSTITUTIONS: tuple[tuple[str, float, float], ...] = (("BTN", OPEN_BB, OPEN_BB),)
"""What each cell records as the price it was solved at, against the price actually played.

They are the same figure here and that is the honest reading rather than a placeholder: this
campaign solves the chart's own `@2.5` open, so no substitution has happened yet. The field
exists because decision 10 admits a real open 20% either side of it, and the substitution is a
fact settled when the cell is committed rather than recomputed at a table - which is why a cell
records the pair even when the pair is equal."""

SAMPLE_CELLS: tuple[SampleCell, ...] = (
    SampleCell(
        name="rainbow-dry-high-donk",
        board=("Kh", "7d", "2c"),
        hero_position="BB",
        node_path=(),
        why="the caller first to act, which is the cell a bet has to come out of",
    ),
    SampleCell(
        name="rainbow-dry-high-facing-a-bet",
        board=("Kh", "7d", "2c"),
        hero_position="BB",
        node_path=(0, 1),
        why="the caller facing a 33% continuation bet, which is the cell a raise comes out of",
    ),
    SampleCell(
        name="two-tone-paired-donk",
        board=("8c", "8d", "3c"),
        hero_position="BB",
        node_path=(),
        why="a two-tone board, where a flush draw must not be served the no-draw strategy",
    ),
    SampleCell(
        name="monotone-connected-cbet",
        board=("9c", "8c", "7c"),
        hero_position="BTN",
        node_path=(0,),
        why="the preflop raiser continuation-betting, about half of all flops",
    ),
)
"""Four cells on the three ruled flops. Decision 6 item 4 freezes the texture and rank splits -
rainbow and dry-high, two-tone and paired, monotone and connected - and Taylor's 2026-09-15
amendment allows a fourth file on a board already present, which is what puts two cells on the
rainbow board.

**Three of the four come off three solves rather than four**, and that is a property of the tree
rather than a saving anybody arranged: one flop solve holds every node of that flop, so the
caller's first decision, the raiser's answer to a check, and the caller's decision facing that
bet are three nodes of one solved tree, reached by `path` `[]`, `[Check]` and `[Check, Bet 33%]`.
Only the board changes the solve."""


def cells_for_board(
    board: tuple[str, ...], wanted: tuple[SampleCell, ...]
) -> tuple[SampleCell, ...]:
    return tuple(cell for cell in wanted if cell.board == board)


# --------------------------------------------------------------------------- #
# The input ranges, out of the committed export
# --------------------------------------------------------------------------- #

BTN_RFI_PATH = (0, 0, 0)
"""LJ, HJ and CO fold, so the button is first in. Action index 0 is Fold at each of them."""

BB_VS_BTN_PATH = (0, 0, 0, 1, 0)
"""...the button raises and the small blind folds, which leaves the big blind facing the open."""

RAISE_INDEX = 1
CALL_INDEX = 1
"""The button's node offers Fold, Raise; the big blind's offers Fold, Call, 3-bet. Both are read
off the export's own action labels below rather than assumed."""


def conditional_ranges() -> tuple[dict[str, float], dict[str, float]]:
    """The two flop ranges, derived from the committed preflop export rather than quoted.

    In position is the button's opening frequency by class; out of position is the big blind's
    calling frequency facing that open. Both are read off the export the repo commits, so the
    solve's inputs are re-derivable from bytes in this repo rather than from a string in a report
    appendix.

    Neither is conditioned on anything else: the export's own source card records the payload as
    unconditional, and reaching these nodes does not depend on either seat's cards.
    """
    export = load_solver_export(COMMITTED_EXPORT_PATH)
    button = export.node(BTN_RFI_PATH)
    big_blind = export.node(BB_VS_BTN_PATH)
    _expect_action(button, RAISE_INDEX, "raise")
    _expect_action(big_blind, CALL_INDEX, "call")
    in_position = {
        hand: button.weight_bp(RAISE_INDEX, hand) / 10_000 for hand in HAND_CLASSES
    }
    out_of_position = {
        hand: big_blind.weight_bp(CALL_INDEX, hand) / 10_000 for hand in HAND_CLASSES
    }
    return floor_range(out_of_position), floor_range(in_position)


def _expect_action(node: Any, index: int, kind: str) -> None:
    action = node.actions[index]
    if action.kind != kind:
        raise SystemExit(
            f"the committed export's node {node.path} offers {action.kind!r} at index {index},"
            f" not {kind!r}; the range derivation is reading the wrong branch"
        )


def range_text(weights: dict[str, float]) -> str:
    """One range in GTOpen's own syntax, class-level and never per combo.

    A single suit-specific entry anywhere in either range collapses the solver's isomorphism
    group to the identity and forfeits the whole saving on every non-rainbow board, so this
    writes `AKs` and `AKs:0.5` and never `AhKh`.
    """
    parts: list[str] = []
    for hand, weight in weights.items():
        if weight >= 1.0:
            parts.append(hand)
        else:
            parts.append(f"{hand}:{weight:.4f}".rstrip("0").rstrip("."))
    return ",".join(parts)


# --------------------------------------------------------------------------- #
# The server, restarted between solves
# --------------------------------------------------------------------------- #


class Server:
    """One GTOpen process, started and stopped by this script.

    Restarted per plan on purpose: the server never returns freed pages, and a session carrying
    a large high-water mark measured about 1.6x slower per iteration on the identical config.
    """

    def __init__(self, binary: Path, log_dir: Path) -> None:
        self.binary = binary
        self.log_dir = log_dir
        self.process: subprocess.Popen | None = None

    def start(self, label: str) -> None:
        if not self.binary.is_file():
            raise SystemExit(
                f"{self.binary} is not a file. Build GTOpen first (`cargo build --release` in the"
                " clone) or point --server at the binary; this script never installs one."
            )
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log = (self.log_dir / f"gto-server-{label}.log").open("wb")
        self.process = subprocess.Popen(  # noqa: S603 - a local binary named on the command line
            [str(self.binary)],
            cwd=str(self.binary.resolve().parents[2]),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"{BASE_URL}/api/status", timeout=2) as answer:
                    json.loads(answer.read())
                    return
            except (urllib.error.URLError, OSError, ValueError):
                time.sleep(0.25)
        self.stop()
        raise SystemExit(f"the server did not answer /api/status within "
                         f"{SERVER_START_TIMEOUT_SECONDS:.0f}s; see {log.name}")

    def stop(self) -> None:
        process = self.process
        self.process = None
        if process is None or process.poll() is not None:
            return
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        try:
            process.wait(timeout=SERVER_STOP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait(timeout=SERVER_STOP_TIMEOUT_SECONDS)


def refuse_a_foreign_server() -> None:
    """A server this script did not start is somebody's session, and `/api/spot` drops it."""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/status", timeout=2) as answer:
            json.loads(answer.read())
    except (urllib.error.URLError, OSError, ValueError):
        return
    raise SystemExit(
        f"something is already serving {BASE_URL}. `/api/spot` drops whatever session is there"
        " unconditionally, so this refuses to start rather than destroy it. Stop that server"
        " first; this script restarts its own between solves and needs the port."
    )


# --------------------------------------------------------------------------- #
# One board: solve it, read every wanted node back, build the cells
# --------------------------------------------------------------------------- #


@dataclass
class BoardResult:
    """What one solved flop produced, measured rather than hoped."""

    board: tuple[str, ...]
    outcome: Any
    cells: list[dict[str, Any]] = field(default_factory=list)
    node_payloads: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    committed: bool = True
    verdict: str = ""


def preflop_line_for(hero_position: str):
    return completed_preflop_line(
        TABLE_SIZE,
        STACK_DEPTH_BB,
        hero_position,
        BTN_OPEN_BB_CALL,
        small_blind_bb=BLINDS.small_blind_bb,
        big_blind_bb=BLINDS.big_blind_bb,
        ante_bb=BLINDS.ante_bb,
    )


def seat_of_player(hero_position: str) -> dict[int, str]:
    """GTOpen's two seats as this repo's labels. The big blind is out of position on every flop
    after a button open, which is `postflop_action_order`'s own ordering and not a convention
    invented here."""
    del hero_position
    return {OOP_PLAYER: "BB", IP_PLAYER: "BTN"}


def solve_one_board(
    board: tuple[str, ...],
    wanted: tuple[SampleCell, ...],
    transport,
    oop_text: str,
    ip_text: str,
    tolerance: float,
) -> BoardResult:
    line = preflop_line_for("BB")
    plan = SolvePlan(
        label=f"srp-{''.join(board)}",
        board="".join(board),
        preflop_line=line.rendered,
        range_oop=oop_text,
        range_ip=ip_text,
        starting_pot=line.pot_bb,
        effective_stack=line.effective_stack_bb,
        config=solve_config_document(),
    )
    outcome = run_solve(plan, transport)
    result = BoardResult(board=board, outcome=outcome)
    commit, verdict = commit_verdict(outcome)
    result.committed, result.verdict = commit, verdict
    if not commit:
        result.notes.append(f"{plan.label} refused: {verdict}")
        return result
    for cell in wanted:
        node = transport(
            "/api/node", {"path": [path_step(index) for index in cell.node_path]}
        )
        hero_line = preflop_line_for(cell.hero_position)
        harvested = harvest_node(
            node, board, seat_of_player(cell.hero_position), hero_line.pot_bb, tolerance
        )
        document = cell_document(
            harvested,
            preflop_line=hero_line,
            board=board,
            blinds=BLINDS,
            price_substitutions=PRICE_SUBSTITUTIONS,
            achieved_exploitability_pct_of_pot=outcome.exploit_pct_of_pot,
            iterations=outcome.iterations,
        )
        result.cells.append({"sample": cell, "document": document, "harvested": harvested})
        result.node_payloads[cell.name] = node
        result.notes.append(
            f"{cell.name}: {len(harvested.hand_classes)} classes from {harvested.combos} combos,"
            f" largest in-class divergence {harvested.class_divergence:.2e},"
            f" {harvested.zero_reach_classes} classes at zero reach"
        )
    return result


# --------------------------------------------------------------------------- #
# Writing: the sample, the object, the config, the index
# --------------------------------------------------------------------------- #


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def write_object(object_dir: Path, board: tuple[str, ...], result: BoardResult) -> tuple[Path, str]:
    """The solved object: every combo of every harvested node, outside git, digested.

    The index authenticates this rather than the sample, which is decision 6's whole shape - the
    bytes the bot plays live in object storage and the repo holds an index plus a sample. Written
    gzipped because it is the large half by construction and nothing in the gate reads it.
    """
    object_dir.mkdir(parents=True, exist_ok=True)
    path = object_dir / f"srp-{''.join(board)}.nodes.json.gz"
    payload = {
        "board": list(board),
        "preflop_line": preflop_line_for("BB").rendered,
        "solve": {
            "outcome": result.outcome.outcome,
            "exploit_pct_of_pot": result.outcome.exploit_pct_of_pot,
            "iterations": result.outcome.iterations,
            "wall_seconds": result.outcome.wall_seconds,
            "arena_bytes": result.outcome.arena_bytes,
            "machine": MEASURING_MACHINE,
            "memory_ceiling": describe_memory_ceiling(),
        },
        "config": solve_config_document(),
        "nodes": result.node_payloads,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    with path.open("wb") as handle, gzip.GzipFile(
        filename="", mode="wb", fileobj=handle, mtime=0
    ) as stream:
        stream.write(raw)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def write_solve_config(oop: dict[str, float], ip: dict[str, float]) -> None:
    """Decision 11's menu and decision 12's floored ranges, committed beside the data.

    The ranges are keyed by class and never by combo, which is a constraint rather than a
    preference: one suit-specific weight collapses the solver's isomorphism group to the identity
    and forfeits the saving on every non-rainbow board.
    """
    document = solve_config_document()
    document["range_weight_floor"] = RANGE_WEIGHT_FLOOR
    document["ranges"] = {"oop_bb_call": oop, "ip_btn_open": ip}
    document["range_source"] = {
        "export": str(COMMITTED_EXPORT_PATH.relative_to(REPO_ROOT)),
        "oop": "the big blind's call frequency facing a 2.5bb button open",
        "ip": "the button's opening frequency with the three earlier seats folded",
        "note": (
            "derived from the committed export by scripts/solve_postflop_sample.py, floored"
            f" class-level at {RANGE_WEIGHT_FLOOR}; combos after the floor are"
            f" {sum(class_combos(hand) for hand in oop)} out of position and"
            f" {sum(class_combos(hand) for hand in ip)} in position"
        ),
    }
    write_json(SOLVE_CONFIG_PATH, document)


def tree_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def rebuild_index(manifest: dict[str, Any]) -> dict[str, Any]:
    """The committed index, rebuilt from the sample on disk and the object manifest beside it.

    `committed_bytes` and `headroom_bytes` are self-referential - writing them changes the file
    they are written into - so the write is iterated to a fixed point rather than computed once
    and left one digit wrong.
    """
    entries: list[dict[str, Any]] = []
    lines: list[str] = []
    for path in sorted(SAMPLE_DIR.glob("*.json")):
        cell = import_postflop_cell(path)
        recorded = manifest["objects"].get(cell.spot_key)
        if recorded is None:
            raise SystemExit(
                f"{path.name} has no object recorded in {OBJECT_MANIFEST_PATH.name}, so its index"
                " entry would carry a digest of nothing. Re-solve that board or remove the file."
            )
        entries.append(
            {
                "spot_key": cell.spot_key,
                "preflop_line": cell.preflop_line.rendered,
                "board": list(cell.board),
                "achieved_exploitability_pct_of_pot": cell.achieved_exploitability_pct_of_pot,
                "iterations": cell.iterations,
                "strategy_digest": strategy_digest(cell.hand_classes, cell.class_weights),
                "object_digest": recorded["object_digest"],
            }
        )
        if cell.preflop_line.rendered not in lines:
            lines.append(cell.preflop_line.rendered)
    index = {
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "object_storage": manifest["object_storage"],
        "covered_preflop_lines": lines,
        "line_count_bound_by": "campaign-cost",
        "cells_solved_and_rejected_above_one_percent": int(manifest["rejected_above_one_percent"]),
        "committed_bytes": 0,
        "headroom_bytes": 0,
        "entries": entries,
    }
    for _ in range(8):
        write_json(INDEX_PATH, index)
        committed = tree_bytes(POSTFLOP_DIR)
        headroom = ARTIFACT_BYTE_CAP - tree_bytes(ARTIFACT_ROOT)
        if (index["committed_bytes"], index["headroom_bytes"]) == (committed, headroom):
            return index
        index["committed_bytes"], index["headroom_bytes"] = committed, headroom
    raise SystemExit("the index's own byte figures did not settle, which they must in one step")


def load_manifest(object_storage: str) -> dict[str, Any]:
    if OBJECT_MANIFEST_PATH.is_file():
        return json.loads(OBJECT_MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        "object_storage": object_storage,
        "rejected_above_one_percent": 0,
        "objects": {},
    }


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def report(result: BoardResult) -> None:
    outcome = result.outcome
    print(f"  outcome            {outcome.outcome}")
    print(f"  exploitability     {outcome.exploit_pct_of_pot:.4f}% of pot"
          f" (ceiling {EXPLOITABILITY_CEILING_PCT_OF_POT}%)")
    print(f"  iterations         {outcome.iterations} (+/-{outcome.iteration_bracket})")
    print(f"  wall clock         {outcome.wall_seconds:.1f}s"
          f" = {outcome.wall_seconds / 60:.1f} min")
    print(f"  planned arena      {outcome.arena_bytes / 1e9:.2f} GB")
    for note in result.notes:
        print(f"  {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", action="append", default=[], help="a cell name; repeatable")
    parser.add_argument("--all", action="store_true", help="every cell in the sample")
    parser.add_argument("--list", action="store_true", help="name the cells and stop")
    parser.add_argument("--server", default=str(DEFAULT_SERVER), help="the gto-server binary")
    parser.add_argument("--object-dir", default=str(DEFAULT_OBJECT_DIR))
    parser.add_argument("--log-dir", default=str(Path.home() / ".cache" / "poker-bot-solves"))
    parser.add_argument("--tolerance", type=float, default=None,
                        help="in-class agreement tolerance; the harvest's own default otherwise")
    parser.add_argument("--index-only", action="store_true",
                        help="rebuild the index from what is already committed, solving nothing")
    args = parser.parse_args(argv)

    if args.list:
        for cell in SAMPLE_CELLS:
            path = "root" if not cell.node_path else " -> ".join(str(i) for i in cell.node_path)
            print(f"{cell.name:34s} {cell.board_text:8s} hero={cell.hero_position:3s}"
                  f" node=[{path}]  {cell.why}")
        return 0

    object_storage = f"local directory {args.object_dir} (no remote store is provisioned yet)"
    if args.index_only:
        index = rebuild_index(load_manifest(object_storage))
        print(f"index rebuilt: {len(index['entries'])} entries,"
              f" {index['committed_bytes']} bytes committed,"
              f" {index['headroom_bytes']} bytes of headroom")
        return 0

    wanted = SAMPLE_CELLS if args.all else tuple(
        cell for cell in SAMPLE_CELLS if cell.name in set(args.cell)
    )
    if not wanted:
        parser.error("name at least one --cell, or pass --all or --list")
    unknown = set(args.cell) - {cell.name for cell in SAMPLE_CELLS}
    if unknown:
        parser.error(f"no such cell: {sorted(unknown)}")

    oop, ip = conditional_ranges()
    oop_text, ip_text = range_text(oop), range_text(ip)
    print(f"machine            {MEASURING_MACHINE}")
    print(f"memory ceiling     {describe_memory_ceiling()}")
    print(f"solver own guard   {gtopen_memory_guard()['solver_guard_live']}")
    print(f"floor              {RANGE_WEIGHT_FLOOR} class-level, from the committed export")
    print(f"range oop          {len(oop)} classes, {sum(class_combos(h) for h in oop)} combos")
    print(f"range ip           {len(ip)} classes, {sum(class_combos(h) for h in ip)} combos")

    write_solve_config(oop, ip)
    manifest = load_manifest(object_storage)
    refuse_a_foreign_server()
    server = Server(Path(args.server), Path(args.log_dir))
    tolerance = CLASS_AGREEMENT_TOLERANCE if args.tolerance is None else float(args.tolerance)

    boards = []
    for cell in wanted:
        if cell.board not in boards:
            boards.append(cell.board)
    failures = 0
    for board in boards:
        label = "".join(board)
        print(f"\n=== {label} ===")
        server.start(label)
        try:
            result = solve_one_board(
                board, cells_for_board(board, wanted), http_transport(),
                oop_text, ip_text, tolerance,
            )
        except SolveDriverError as error:
            print(f"  refused: {error}")
            failures += 1
            continue
        finally:
            server.stop()
        report(result)
        if not result.committed:
            manifest["rejected_above_one_percent"] += 1
            failures += 1
            continue
        path, digest = write_object(Path(args.object_dir), board, result)
        print(f"  object             {path} sha256 {digest[:16]}...")
        for built in result.cells:
            sample, document = built["sample"], built["document"]
            target = SAMPLE_DIR / f"{sample.name}.json"
            write_json(target, document)
            import_postflop_cell(target)
            manifest["objects"][document["spot_key"]] = {
                "object_path": str(path),
                "object_digest": digest,
                "board": list(board),
            }
            print(f"  wrote              {target.relative_to(REPO_ROOT)}"
                  f" ({target.stat().st_size} bytes, re-imported clean)")

    manifest["object_storage"] = object_storage
    write_json(OBJECT_MANIFEST_PATH, manifest)
    index = rebuild_index(manifest)
    import_postflop_index(INDEX_PATH)
    print(f"\nindex              {len(index['entries'])} entries")
    print(f"committed bytes    {index['committed_bytes']} in data/artifacts/postflop")
    print(f"artifact headroom  {index['headroom_bytes']} of {ARTIFACT_BYTE_CAP}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
