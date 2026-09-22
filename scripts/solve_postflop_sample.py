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

**It starts the server with full-precision arenas and then proves it got them.** GTOpen defaults
to quantized ones and no route it serves says which it allocated, so asking is not enough: the
server is started with `SOLVER_COMPRESS=0` in its own environment, and every tree it builds is
checked against the arena the configuration rules before anything is solved. What the index
records is that reading rather than the value the run asked for.

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

**The index is larger than the sample, and one cell here is what makes it so.** A cell whose
`in_the_sample` is false is solved and stored like any other and then not written into `sample/`:
its four measured figures go into the object manifest and from there into the index, and its
document goes to `--object-dir` with its object. That is the ordinary state of a fresh clone -
listed here, fetched nowhere - and until decision 18b it was the one state this sample could not
reach, because every cell it solved it also kept.

**`--deep-check` asks a different question and is the only thing here that changes the stopping
rule.** Every figure the campaign rests on is an exploitability figure, which says what a perfect
opponent wins against a strategy and not that the strategy has stopped moving; hands the solver
has driven to indifference keep trading frequency long after exploitability has flattened,
because moving them costs nothing by the measure being minimised. Decision 15 rules that one
committed cell is re-solved with the iteration cap as the only stopping condition and its action
frequencies diffed against the committed strategy, and that the diff is committed beside the
sample. The tree, the menu, the ranges, the arena and every guard are the committed campaign's;
one field of the `/api/solve` body moves, because a run that keeps the ruled target stops where
the committed run stopped and measures nothing.

Usage:

    uv run python scripts/solve_postflop_sample.py --list
    uv run python scripts/solve_postflop_sample.py --cell monotone-connected-cbet
    uv run python scripts/solve_postflop_sample.py --all
    uv run python scripts/solve_postflop_sample.py --deep-check
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
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
    EXPLOITABILITY_TARGET_PCT_OF_POT,
    INDEX_PATH,
    INDEX_SCHEMA_VERSION,
    POSTFLOP_DIR,
    RANGE_WEIGHT_FLOOR,
    SAMPLE_DIR,
    SOLVE_ITERATION_CAP,
    floor_range,
    import_postflop_cell,
    import_postflop_index,
)
from poker_training_bot.solver_artifacts.postflop_harvest import (  # noqa: E402
    CLASS_AGREEMENT_TOLERANCE,
    cell_document,
    combo_cards,
    harvest_node,
    strategy_digest,
)
from poker_training_bot.solver_artifacts.postflop_isomorphism import (  # noqa: E402
    canonical_hole_cards,
)
from poker_training_bot.solver_artifacts.postflop_key import (  # noqa: E402
    completed_preflop_line,
    postflop_spot_key,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (  # noqa: E402
    CHECK_EVERY_ITERATIONS,
    MEASURING_MACHINE,
    RULED_ARENA_STORAGE,
    RUN_TO_THE_CAP_TARGET_PCT,
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
    check_arena_storage,
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

    `in_the_sample` is how a cell says whether the repo keeps its bytes. A cell with it set is
    solved, written into `sample/` and listed in the index, which is every cell decision 6 item 4
    ruled. A cell without it is solved, listed in the index with the same four measured figures,
    and its document and its object stay in object storage - so the index names a spot this clone
    can see and cannot play, which on a real clone is the ordinary case and in a sample where the
    two sets coincide is a case the refusal vocabulary can never reach.
    """

    name: str
    board: tuple[str, ...]
    hero_position: str
    node_path: tuple[int, ...]
    why: str
    in_the_sample: bool = True

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
    SampleCell(
        name="monotone-disconnected-listed-not-held",
        board=("Ac", "8c", "3c"),
        hero_position="BB",
        node_path=(),
        in_the_sample=False,
        why="a spot the index lists and this clone cannot play, which nothing else here is",
    ),
)
"""Five cells on four flops: four the repo keeps, and one it lists and does not keep.

Decision 6 item 4 freezes the texture and rank splits - rainbow and dry-high, two-tone and
paired, monotone and connected - and Taylor's 2026-09-15 amendment allows a fourth file on a
board already present, which is what puts two cells on the rainbow board. Those four are the
sample and the splits govern them.

**Three of those four come off three solves rather than four**, and that is a property of the
tree rather than a saving anybody arranged: one flop solve holds every node of that flop, so the
caller's first decision, the raiser's answer to a check, and the caller's decision facing that
bet are three nodes of one solved tree, reached by `path` `[]`, `[Check]` and `[Check, Bet 33%]`.
Only the board changes the solve.

**The fifth is outside the splits on purpose, and it is chosen for cost rather than for poker.**
Decision 18b rules it. It exists because the index is meant to be larger than the sample and in a
four-cell sample it was not, so the refusal a fresh clone meets on almost every spot - listed
here, fetched nowhere - had nothing to name and could not be exercised at all. `Ac8c3c` is
monotone because monotone is the cheapest flop this machine solves: all three cards share a suit,
the solver's isomorphism group collapses hardest, and the one monotone solve this phase measured
took 7.7 minutes and 320 iterations to 0.2954% of pot. Its ranks are as far from `9c8c7c` as the
deck allows - ace-high rather than nine-high, and no two of A, 8, 3 within four ranks of each
other - so it cannot be mistaken for a second reading of the ruled monotone-connected split. The
7.7 minutes is the figure measured on the connected board and is quoted as the nearest
measurement there is, not as a prediction for this one.

**Its hero and its node are fixed by the strategy side rather than chosen.** The big blind first
to act - `BB` at `path` `[]` - is what `an_indexed_but_unfetched_query` looks for, because that
helper builds its key from the committed table whose spot key sorts first and walks boards with
no flop action in front of hero. `check_the_listed_cell_is_reachable` holds the two ends
together and fails the rebuild rather than letting them drift."""


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


SOLVER_COMPRESS_VARIABLE = "SOLVER_COMPRESS"
SOLVER_COMPRESS_FULL_PRECISION = "0"
"""How GTOpen picks its arena, read off `crates/server/src/main.rs` rather than off the name.

    fn storage_from_env() -> Storage {
        match std::env::var("SOLVER_COMPRESS").as_deref() {
            Ok("0") => Storage::F32,
            _ => Storage::Compressed,
        }
    }

The match is on the exact string `"0"` and everything else is the quantized arena: the variable
absent, `"false"`, `"no"`, `"0.0"`, `" 0"`, an unset value inherited from a login shell. There is
no error and no log line, so a name typed slightly wrong produces a solve that looks entirely
normal and measures something else. The value is read per request rather than at boot, but from
the server process's own environment, so it is fixed when the process starts and this is the only
place it can be set. `check_arena_storage` is what proves it took, because nothing the server
answers says so.
"""


class Server:
    """One GTOpen process, started and stopped by this script.

    Restarted per plan on purpose: the server never returns freed pages, and a session carrying
    a large high-water mark measured about 1.6x slower per iteration on the identical config.

    Started with the arena the campaign is configured for, so full precision is a property of the
    committed run rather than of whoever typed the command.
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
            env={**os.environ, SOLVER_COMPRESS_VARIABLE: SOLVER_COMPRESS_FULL_PRECISION},
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


class ArenaVerifiedTransport:
    """The real transport with one thing added: every built tree is checked for its arena.

    The check sits here rather than in `postflop_solve_driver.run_solve` because it has to hold
    for the committed campaign and cannot hold for a caller handing the driver a two-field stub.
    Wrapping the transport puts it on the only path a real solve takes - `/api/spot` answers, the
    arena is decided from that answer, and a quantized tree raises before `/api/solve` is called -
    with no flag to forget and no way to run the campaign around it.

    `verified` is what the run actually got, kept so the provenance records a reading rather than
    the constant the run asked for.
    """

    def __init__(self, inner, wanted: str) -> None:
        self.inner = inner
        self.wanted = wanted
        self.verified: str | None = None

    def __call__(self, path: str, body: dict | None = None) -> dict:
        answer = self.inner(path, body)
        if path == "/api/spot":
            self.verified = check_arena_storage(answer, self.wanted)
        return answer

    def arena(self) -> str:
        """The verified arena, or a refusal: a board that never built a tree has nothing to say
        about which arena it was solved in, and a blank string in the provenance is exactly the
        placeholder the index forbids."""
        if self.verified is None:
            raise SystemExit(
                "no tree was built on this transport, so nothing verified which arena the solve"
                " used. Refused rather than recorded as the value it was asked for."
            )
        return self.verified


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
    arena_storage: str = ""
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
    result = BoardResult(board=board, outcome=outcome, arena_storage=transport.arena())
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
            "arena_storage": result.arena_storage,
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


LISTED_NOT_HELD = "listed_not_held"
"""The manifest key under which a solved cell the repo does not keep records its figures.

It lives in `objects.json` beside the object digests rather than in `sample/`, which is decision
18b's whole point: the bytes of that cell are in object storage and what the repo commits is the
evidence that they exist and what they came out to. `sample/` stays exactly the four files
decision 6 item 4 rules, so nothing that walks the sample picks this cell up by accident."""

INDEX_ENTRY_FIELDS = (
    "spot_key",
    "preflop_line",
    "board",
    "achieved_exploitability_pct_of_pot",
    "iterations",
    "arena_storage",
    "strategy_digest",
    "object_digest",
)
"""What an index entry carries: its key, where it sits, the four measured figures, and the arena
its solve ran in.

Named once and filled through `index_entry`, because the sample cells and the listed-not-held
cell reach the index by different routes and an entry that is thinner on one route is exactly
the placeholder the index forbids.

**The arena is per entry rather than in the header**, even though one campaign rules one arena
for every cell it solves. A cell is solved one board at a time, a run can be resumed days later
against a server somebody else started, and the manifest carries entries across runs - so the
storage mode is a property of the solve that produced a cell, in the same way its iteration count
is, and a header field would assert it for cells it never saw. A quantized number and a
full-precision one are not the same measurement, so a reader reconstructing one cell has to be
able to tell which it is holding without trusting that the file beside it describes that run."""


def index_entry(figures: dict[str, Any], origin: str) -> dict[str, Any]:
    """One index entry, refused rather than written thin.

    A present-but-empty field passes a presence check and authenticates nothing, so absence and
    `None` are the same failure here and both name the cell they came from.
    """
    missing = [name for name in INDEX_ENTRY_FIELDS if figures.get(name) is None]
    if missing:
        raise SystemExit(f"{origin} would enter the index missing {missing}")
    return {name: figures[name] for name in INDEX_ENTRY_FIELDS}


def check_the_listed_cell_is_reachable(
    held: list[Any], listed: list[dict[str, Any]]
) -> None:
    """A listed-but-unheld entry the strategy cannot reach proves nothing, so this derives the
    key the strategy will look for and refuses anything else.

    `an_indexed_but_unfetched_query` builds its key from the committed table whose spot key sorts
    first, on boards with no flop action in front of hero, and walks the index for it. That ties
    the listed cell's hero, node, pot and stack to a sort order over four other files - which is
    a coupling nothing else in the repo would notice parting, so it is checked here on every
    rebuild rather than left to the gate to discover.
    """
    if not held or not listed:
        return
    first = min(held, key=lambda cell: cell.spot_key)
    for entry in listed:
        try:
            wanted = postflop_spot_key(
                first.preflop_line, entry["board"], (), first.pot_bb, first.effective_stack_bb
            )
        except ValueError as error:
            raise SystemExit(
                f"the sample's first spot key is {first.spot_key}, and the strategy cannot build"
                f" a hero-first key from its line at all: {error}. The helper takes that cell's"
                " line verbatim, so the first-sorting sample cell has to be one hero acts first"
                " in, and adding a board that sorts ahead of it is what breaks this."
            ) from error
        if entry["spot_key"] != wanted:
            raise SystemExit(
                f"the index lists {entry['spot_key']} as solved and unheld, but the strategy will"
                f" look for {wanted} - the same board on the sample's own line, hero first to act."
                " Re-solve that cell at hero BB on the root node, or it is listed unreachably."
            )


def rebuild_index(manifest: dict[str, Any]) -> dict[str, Any]:
    """The committed index, rebuilt from the sample on disk and the object manifest beside it.

    The index is deliberately larger than the sample - decision 6 puts the bytes in object
    storage and commits an index plus three flops - so it is built from two sources: the sample
    files, and the manifest's record of cells solved and stored without being kept.

    `committed_bytes` and `headroom_bytes` are self-referential - writing them changes the file
    they are written into - so the write is iterated to a fixed point rather than computed once
    and left one digit wrong.
    """
    entries: list[dict[str, Any]] = []
    lines: list[str] = []
    held: list[Any] = []
    for path in sorted(SAMPLE_DIR.glob("*.json")):
        cell = import_postflop_cell(path)
        recorded = manifest["objects"].get(cell.spot_key)
        if recorded is None:
            raise SystemExit(
                f"{path.name} has no object recorded in {OBJECT_MANIFEST_PATH.name}, so its index"
                " entry would carry a digest of nothing. Re-solve that board or remove the file."
            )
        held.append(cell)
        entries.append(
            index_entry(
                {
                    "spot_key": cell.spot_key,
                    "preflop_line": cell.preflop_line.rendered,
                    "board": list(cell.board),
                    "achieved_exploitability_pct_of_pot": (
                        cell.achieved_exploitability_pct_of_pot
                    ),
                    "iterations": cell.iterations,
                    "arena_storage": recorded.get("arena_storage"),
                    "strategy_digest": strategy_digest(cell.hand_classes, cell.class_weights),
                    "object_digest": recorded["object_digest"],
                },
                path.name,
            )
        )
        if cell.preflop_line.rendered not in lines:
            lines.append(cell.preflop_line.rendered)
    listed: list[dict[str, Any]] = []
    for spot_key, figures in sorted(manifest.get(LISTED_NOT_HELD, {}).items()):
        if spot_key in {entry["spot_key"] for entry in entries}:
            raise SystemExit(
                f"{spot_key} is recorded as listed and not held, and {SAMPLE_DIR.name}/ holds it."
                " Delete one of the two; a spot cannot be both."
            )
        listed.append(index_entry({**figures, "spot_key": spot_key}, spot_key))
        if figures["preflop_line"] not in lines:
            lines.append(figures["preflop_line"])
    check_the_listed_cell_is_reachable(held, listed)
    entries.extend(listed)
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
    manifest = {
        "object_storage": object_storage,
        "rejected_above_one_percent": 0,
        "objects": {},
        LISTED_NOT_HELD: {},
    }
    if OBJECT_MANIFEST_PATH.is_file():
        manifest.update(json.loads(OBJECT_MANIFEST_PATH.read_text(encoding="utf-8")))
    manifest.setdefault(LISTED_NOT_HELD, {})
    return manifest


def record_cell(
    built: dict[str, Any],
    manifest: dict[str, Any],
    object_dir: Path,
    object_path: Path,
    digest: str,
    arena_storage: str,
) -> str:
    """Write one solved cell where its own `in_the_sample` sends it, and record it.

    Both routes write the document, re-import it and record what the *importer* returned rather
    than what the harvest handed over, so a cell that a fresh clone would refuse is refused here
    instead of being listed on figures nothing ever read back.

    The difference is only where the bytes land. A sample cell goes into the repo and the
    manifest keeps its object's digest beside it. A listed-not-held cell goes to object storage,
    document and all, and the manifest keeps the four figures its index entry owes - which is the
    only copy of them the repo gets, and the reason they are read off a re-import.
    """
    sample, document = built["sample"], built["document"]
    spot_key = document["spot_key"]
    if sample.in_the_sample:
        target = SAMPLE_DIR / f"{sample.name}.json"
        write_json(target, document)
        cell = import_postflop_cell(target)
        manifest["objects"][spot_key] = {
            "object_path": str(object_path),
            "object_digest": digest,
            "arena_storage": arena_storage,
            "board": list(cell.board),
        }
        return (f"wrote              {target.relative_to(REPO_ROOT)}"
                f" ({target.stat().st_size} bytes, re-imported clean)")
    target = object_dir / f"{sample.name}.cell.json"
    write_json(target, document)
    cell = import_postflop_cell(target)
    manifest[LISTED_NOT_HELD][spot_key] = {
        "preflop_line": cell.preflop_line.rendered,
        "board": list(cell.board),
        "achieved_exploitability_pct_of_pot": cell.achieved_exploitability_pct_of_pot,
        "iterations": cell.iterations,
        "arena_storage": arena_storage,
        "strategy_digest": strategy_digest(cell.hand_classes, cell.class_weights),
        "object_digest": digest,
        "cell_document": str(target),
    }
    return f"listed, not held  {target} (outside the repo, re-imported clean)"


# --------------------------------------------------------------------------- #
# The determinism proof the contract asks for
# --------------------------------------------------------------------------- #


DETERMINISM_PATH = POSTFLOP_DIR / "determinism.json"
DETERMINISM_SCHEMA_VERSION = 1

DETERMINISM_NOTE = (
    "Determinism proved by re-solving and diffing rather than by checksumming one run, on the"
    " configuration actually committed, in two processes against a restarted server. No"
    " tolerance is set anywhere here: the contract rules that if the two runs are not"
    " byte-identical the phase halts and a human is asked, so this records identical or not and"
    " never how close."
)
"""What this check is, in the contract's own terms rather than in a summary of them.

It is worth saying which configuration, because the only determinism figure this repo held before
was taken on a different one: `reports/active/latest_postflop_solve_cost.txt` carries a
determinism row on `Kc7c2c` in a three-bet pot of 16.0 with a 92.5 stack at 240 iterations under
quantized arenas, and the committed campaign is a single-raised pot of 5.5 with a 97.5 stack on
four other boards at 280 to 340 iterations under full-precision ones. Neither result stands in
for the other, and the contract asks for this one by name."""


def second_run_objects(second_objects: Path, name: str) -> Path:
    path = second_objects / name
    if not path.is_file():
        raise SystemExit(
            f"{path} does not exist, so the second run did not solve that board and there is"
            " nothing to compare. Re-solve it before asking whether the two runs agree."
        )
    return path


def compare_node_payloads(one: dict[str, Any], two: dict[str, Any]) -> dict[str, Any]:
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


def determinism_document(second_tree: Path, second_objects: Path) -> dict[str, Any]:
    """Both runs of the committed configuration, compared, with nothing averaged or tolerated."""
    if second_tree.resolve() == POSTFLOP_DIR.resolve():
        raise SystemExit(
            "the second run's tree is the committed one, so this would compare a file with"
            " itself and pass whatever the solver did. Point it at a tree a second run wrote."
        )
    manifest = json.loads(OBJECT_MANIFEST_PATH.read_text(encoding="utf-8"))
    committed_objects = {
        key: Path(value["object_path"]) for key, value in manifest["objects"].items()
    }
    cells: list[dict[str, Any]] = []
    for path in sorted(SAMPLE_DIR.glob("*.json")):
        committed = import_postflop_cell(path)
        other_path = second_tree / "sample" / path.name
        if not other_path.is_file():
            raise SystemExit(f"{other_path} does not exist, so the second run skipped {path.name}")
        object_path = committed_objects[committed.spot_key]
        one = json.loads(gzip.open(object_path).read())
        two = json.loads(gzip.open(second_run_objects(second_objects, object_path.name)).read())
        if one["solve"]["wall_seconds"] == two["solve"]["wall_seconds"]:
            raise SystemExit(
                f"{object_path.name} and the second run's copy report the same wall clock to the"
                " microsecond, which two runs do not. The second tree is a copy of the first"
                " rather than a second run, and comparing it would prove nothing."
            )
        name = path.stem
        cells.append(
            {
                "cell": name,
                "spot_key": committed.spot_key,
                "board": list(committed.board),
                "cell_document_bytes_identical": (
                    path.read_bytes() == other_path.read_bytes()
                ),
                "committed_bytes": path.stat().st_size,
                "second_run_bytes": other_path.stat().st_size,
                "iterations": [one["solve"]["iterations"], two["solve"]["iterations"]],
                "achieved_exploitability_pct_of_pot": [
                    one["solve"]["exploit_pct_of_pot"],
                    two["solve"]["exploit_pct_of_pot"],
                ],
                "wall_seconds": [
                    round(one["solve"]["wall_seconds"], 1),
                    round(two["solve"]["wall_seconds"], 1),
                ],
                "arena_storage": [one["solve"]["arena_storage"], two["solve"]["arena_storage"]],
                "strategy_digest": [
                    strategy_digest(committed.hand_classes, committed.class_weights),
                    strategy_digest(
                        *_cell_strategy(json.loads(other_path.read_text(encoding="utf-8")))
                    ),
                ],
                "per_combo": compare_node_payloads(one["nodes"][name], two["nodes"][name]),
            }
        )
    for spot_key, figures in sorted(manifest.get(LISTED_NOT_HELD, {}).items()):
        document_path = Path(figures["cell_document"])
        other_path = second_objects / document_path.name
        if not other_path.is_file():
            raise SystemExit(
                f"{other_path} does not exist, so the second run did not produce the cell the"
                " index lists and the repo does not hold. It is part of the committed"
                " configuration and is compared like any other."
            )
        name = document_path.name.removesuffix(".cell.json")
        object_path = Path(
            str(document_path.parent / f"srp-{''.join(figures['board'])}.nodes.json.gz")
        )
        one = json.loads(gzip.open(object_path).read())
        two = json.loads(gzip.open(second_run_objects(second_objects, object_path.name)).read())
        cells.append(
            {
                "cell": name,
                "spot_key": spot_key,
                "board": list(figures["board"]),
                "held_in_the_repo": False,
                "cell_document_bytes_identical": (
                    document_path.read_bytes() == other_path.read_bytes()
                ),
                "committed_bytes": document_path.stat().st_size,
                "second_run_bytes": other_path.stat().st_size,
                "iterations": [one["solve"]["iterations"], two["solve"]["iterations"]],
                "achieved_exploitability_pct_of_pot": [
                    one["solve"]["exploit_pct_of_pot"],
                    two["solve"]["exploit_pct_of_pot"],
                ],
                "wall_seconds": [
                    round(one["solve"]["wall_seconds"], 1),
                    round(two["solve"]["wall_seconds"], 1),
                ],
                "arena_storage": [one["solve"]["arena_storage"], two["solve"]["arena_storage"]],
                "strategy_digest": [
                    strategy_digest(
                        *_cell_strategy(json.loads(document_path.read_text(encoding="utf-8")))
                    ),
                    strategy_digest(
                        *_cell_strategy(json.loads(other_path.read_text(encoding="utf-8")))
                    ),
                ],
                "per_combo": compare_node_payloads(one["nodes"][name], two["nodes"][name]),
            }
        )
    identical = all(
        cell["cell_document_bytes_identical"]
        and cell["per_combo"]["menu_matched"]
        and cell["per_combo"]["combos_in_only_one_run"] == 0
        and cell["per_combo"]["largest_gap"] == 0.0
        for cell in cells
    )
    return {
        "check_schema_version": DETERMINISM_SCHEMA_VERSION,
        "what_this_is": DETERMINISM_NOTE,
        "configuration": "data/artifacts/postflop/solve_config.json, unchanged between the runs",
        "the_two_runs_are_distinct": (
            "Each cell carries both wall clocks, and they differ: the second run shared the"
            " machine with other work. A second tree whose wall clock matched the first to the"
            " microsecond is refused rather than compared, because that is a copy of the first"
            " run and would pass whatever the solver did."
        ),
        "identical": identical,
        "cells_compared": len(cells),
        "how": (
            "Two comparisons per cell. The committed cell document byte for byte, which is what"
            " the repo holds; and the solver's own per-combo strategies inside the two runs'"
            " objects, which is the stronger of the two because a committed row is rounded to a"
            " thousandth and two runs could differ under that and still write the same bytes."
        ),
        "cells": cells,
    }


def _cell_strategy(document: dict[str, Any]) -> tuple[list[str], list[list[float]]]:
    return list(document["hand_classes"]), [list(row) for row in document["class_weights"]]


def report_determinism(document: dict[str, Any]) -> None:
    print(f"  identical          {document['identical']}")
    for cell in document["cells"]:
        combo = cell["per_combo"]
        print(f"  {cell['cell']:40s} document"
              f" {'identical' if cell['cell_document_bytes_identical'] else 'DIFFERENT'},"
              f" {combo['combos']} combos, largest per-combo gap {combo['largest_gap']},"
              f" combos in only one run {combo['combos_in_only_one_run']}")


# --------------------------------------------------------------------------- #
# Decision 15's deep convergence check
# --------------------------------------------------------------------------- #


DEEP_CHECK_PATH = POSTFLOP_DIR / "deep_convergence_check.json"
DEEP_CHECK_SCHEMA_VERSION = 1

DEEP_CHECK_CELL = "monotone-connected-cbet"
"""Which cell is re-solved deep, and why it is this one rather than the cheapest one.

Decision 15 already names the monotone cell, so this is not a choice being made here; what
follows is the poker reason it is also the right cell rather than only the affordable one.

**The question is about hands the solver has driven to indifference**, because those are the ones
that keep trading frequency after exploitability has flattened - moving them costs nothing by the
measure being minimised. So the cell that tests the settling claim hardest is the one holding the
most indifference, and on the committed sample that is this one by a distance: of its 152 classes
only 19 put 99% or more on a single action and 101 spread past a tenth, measured off the
committed file rather than asserted. `9c8c7c` is monotone and connected, every hand in the
button's range has some share of the flush and straight structure, and equities run close
together - which is exactly the texture that produces mixing. A dry, disconnected, ace- or
king-high rainbow board is the opposite: much of the range plays one action at a frequency near
one, so a settling check run there would flatter the answer by asking it of hands that were never
going to move.

**It is also the node a reader consults most.** Hero is the preflop raiser deciding a continuation
bet after the caller checks, which is about half of all flops, against a caller's donk node that
is reached only when hero's own line puts them there.

**What it cannot settle.** One board is one board. The classes here are 152 because a monotone
flop collapses hardest, against 1,176 on the rainbow board the sample also holds, and rainbow was
never solved to target anywhere in this phase. A settled answer here is evidence about this cell
and is not a campaign-wide result - which is the same limit the cost model already states about
rainbow, in the other direction."""

PURE_ENOUGH = 0.99
"""At or above this on one action, a class is playing that action and nothing else: the residue
is under the third decimal a committed row is even written in."""

LIGHTLY_MIXED = 0.90
"""Between this and `PURE_ENOUGH` a class has a clear action and a small alternative; below it,
two actions are genuinely in contention and the class is where indifference lives."""

NOTABLE_MOVEMENT = 0.05
"""Past this, a frequency written on a chart would be written differently: a hand bet 60% of the
time rather than 65%. Under it, the difference is inside what a reader rounds away anyway. It is
the threshold the shape split counts against, so the sentence a reader wants - how many of the
hands that actually moved were the indifferent ones - comes off the file rather than off prose."""

MOVEMENT_BUCKET_EDGES = (0.0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25)
"""How far a class moved, in bands a reader can act on rather than in a single mean.

The first is exact equality, which is a real outcome and not a rounding artefact: both rows are
thousandths. `0.005` is half of the third decimal a row carries, `0.05` is the point at which a
mixed frequency written on a chart would be written differently, and `0.25` is a different
strategy for that hand rather than a different frequency."""


def committed_cell_path(name: str) -> Path:
    path = SAMPLE_DIR / f"{name}.json"
    if not path.is_file():
        raise SystemExit(
            f"{path} does not exist, so there is no committed strategy to diff a deep run"
            " against. Solve the sample first; the deep check measures movement away from what"
            " the repo holds and cannot invent the end it is measuring from."
        )
    return path


def class_reach_shares(
    node: dict[str, Any], board: tuple[str, ...]
) -> dict[str, float]:
    """How often hero's own committed line actually brings each class to this node, normalised.

    Read off the solved node rather than off the committed cell, because a cell carries hero's
    strategy and not hero's reach - and a movement figure that ignores reach counts a class hero
    arrives here with once as loudly as one they arrive with a hundred times. The board's own suit
    map collapses combos into classes here exactly as the harvest does, so the labels line up with
    the committed rows without any re-dressing.
    """
    actor = int(node["player"])
    totals: dict[str, float] = {}
    for hand in node["players"][actor]["hands"]:
        cards = combo_cards(str(hand["combo"]))
        label = "".join(canonical_hole_cards(board, cards))
        totals[label] = totals.get(label, 0.0) + float(hand.get("reach") or 0.0)
    live = sum(totals.values())
    if live <= 0:
        raise SystemExit(
            "the deep node answers a zero reach for every class, so nothing here is weighted by"
            " how often hero arrives and the check would be reporting an unweighted figure under"
            " a weighted name"
        )
    return {label: value / live for label, value in totals.items()}


def quantile(values: list[float], fraction: float) -> float:
    """The nearest-rank quantile of an already-sorted-able list, taken without numpy.

    Nearest rank rather than interpolated: every value here is a multiple of a thousandth and an
    interpolated quantile would publish a movement figure no class actually exhibits.
    """
    if not values:
        raise SystemExit("no classes to summarise, so every distribution figure would be empty")
    ordered = sorted(values)
    rank = max(1, min(len(ordered), math.ceil(fraction * len(ordered))))
    return ordered[rank - 1]


def row_shape(row: list[float]) -> str:
    """What kind of decision a committed row describes, which is what the movement is sorted by."""
    top = max(row)
    if top >= PURE_ENOUGH:
        return "pure"
    if top >= LIGHTLY_MIXED:
        return "lightly-mixed"
    return "mixed"


def movement_buckets(movements: list[float]) -> dict[str, int]:
    counts = {"exactly 0": sum(1 for value in movements if value == 0.0)}
    previous = 0.0
    for edge in MOVEMENT_BUCKET_EDGES[1:]:
        counts[f"> {previous:g} and <= {edge:g}"] = sum(
            1 for value in movements if previous < value <= edge
        )
        previous = edge
    counts[f"> {previous:g}"] = sum(1 for value in movements if value > previous)
    return counts


def summarise_movement(
    movements: list[float], shapes: list[str], reach: list[float]
) -> dict[str, Any]:
    """The distribution of per-class movement, and the same thing split by how mixed the class is.

    The split is the poker question rather than a presentation choice: a strategy that has settled
    where a reader would act and still trades frequency between two actions worth the same thing
    is a different finding from one that has moved a hand off a decision, and a single mean over
    all classes cannot tell them apart.
    """
    by_shape: dict[str, Any] = {}
    for shape in ("pure", "lightly-mixed", "mixed"):
        picked = [value for value, kind in zip(movements, shapes, strict=True) if kind == shape]
        by_shape[shape] = {
            "classes": len(picked),
            "max": round(max(picked), 4) if picked else None,
            "mean": round(sum(picked) / len(picked), 5) if picked else None,
            f"classes_moving_past_{NOTABLE_MOVEMENT:g}": sum(
                1 for value in picked if value > NOTABLE_MOVEMENT
            ),
        }
    weighted = sum(value * share for value, share in zip(movements, reach, strict=True))
    return {
        "metric": (
            "per class, the largest absolute change in any one action's frequency between the"
            " committed strategy and the deep one"
        ),
        "classes": len(movements),
        "max": round(max(movements), 4),
        "mean": round(sum(movements) / len(movements), 5),
        "median": round(quantile(movements, 0.50), 4),
        "p75": round(quantile(movements, 0.75), 4),
        "p90": round(quantile(movements, 0.90), 4),
        "p95": round(quantile(movements, 0.95), 4),
        "p99": round(quantile(movements, 0.99), 4),
        "reach_weighted_mean": round(weighted, 5),
        "buckets": movement_buckets(movements),
        "by_committed_shape": by_shape,
    }


def aggregate_frequencies(
    actions: list[dict[str, Any]],
    shallow: list[list[float]],
    deep: list[list[float]],
    reach: list[float],
) -> list[dict[str, Any]]:
    """What the whole range does with each action, which is the figure a reader takes off a chart.

    Weighted by the deep run's reach on both sides, so the two numbers differ only by the strategy
    and never by the weights. A range betting the same share of the time out of hands that have
    swapped places is the specific outcome decision 15 predicts for indifferent hands, and it is
    invisible in a per-class figure.
    """
    built: list[dict[str, Any]] = []
    for index, action in enumerate(actions):
        before = sum(row[index] * share for row, share in zip(shallow, reach, strict=True))
        after = sum(row[index] * share for row, share in zip(deep, reach, strict=True))
        built.append(
            {
                **action,
                "committed_frequency": round(before, 4),
                "deep_frequency": round(after, 4),
                "moved": round(after - before, 4),
            }
        )
    return built


def action_flips(
    classes: list[str],
    shallow: list[list[float]],
    deep: list[list[float]],
    reach: list[float],
) -> list[dict[str, Any]]:
    """Every class whose most-played action is a different action after the deep run.

    `committed_margin` is what separated the top two actions in the committed row, and it is the
    whole reading: a flip out of a row whose top two were a thousandth apart is two actions the
    solver holds equal swapping places, and a flip out of a row that was not close is the deep run
    contradicting something a reader would have acted on.
    """
    flips: list[dict[str, Any]] = []
    for index, label in enumerate(classes):
        before, after = shallow[index], deep[index]
        if before.index(max(before)) == after.index(max(after)):
            continue
        ordered = sorted(before, reverse=True)
        flips.append(
            {
                "hand_class": label,
                "committed": before,
                "deep": after,
                "committed_margin": round(ordered[0] - ordered[1], 4),
                "reach_share": round(reach[index], 5),
            }
        )
    return flips


def deep_check_document(
    cell: SampleCell,
    committed: dict[str, Any],
    deep: dict[str, Any],
    outcome: Any,
    arena_storage: str,
    node: dict[str, Any],
    divergence: float,
) -> dict[str, Any]:
    """The committed diff: both strategies, what moved, and enough of each to recompute it."""
    if deep["spot_key"] != committed["spot_key"]:
        raise SystemExit(
            f"the deep run landed on {deep['spot_key']} and the committed cell is"
            f" {committed['spot_key']}. Two different spots cannot be diffed as one."
        )
    if deep["actions"] != committed["actions"]:
        raise SystemExit(
            f"the deep run's menu is {deep['actions']} against the committed"
            f" {committed['actions']}. A frequency is a frequency of an action, so a moved menu"
            " makes every difference below meaningless."
        )
    order = list(committed["hand_classes"])
    deep_rows = dict(zip(deep["hand_classes"], deep["class_weights"], strict=True))
    missing = [label for label in order if label not in deep_rows]
    extra = [label for label in deep["hand_classes"] if label not in set(order)]
    if missing or extra:
        raise SystemExit(
            f"the deep run answers for a different set of hand classes: {len(missing)} the"
            f" committed cell holds are absent and {len(extra)} are new. Refused rather than"
            " diffed over the intersection, which would publish a movement figure for a range"
            " that is not the committed one."
        )
    shares = class_reach_shares(node, tuple(committed["board"]))
    shallow_rows = [list(row) for row in committed["class_weights"]]
    aligned = [list(deep_rows[label]) for label in order]
    reach = [shares.get(label, 0.0) for label in order]
    movements = [
        round(max(abs(a - b) for a, b in zip(before, after, strict=True)), 4)
        for before, after in zip(shallow_rows, aligned, strict=True)
    ]
    shapes = [row_shape(row) for row in shallow_rows]
    ranked = sorted(range(len(order)), key=lambda i: (-movements[i], order[i]))
    return {
        "check_schema_version": DEEP_CHECK_SCHEMA_VERSION,
        "what_this_is": (
            "Decision 15's deep convergence check. One committed cell re-solved on the same tree"
            " with the iteration cap as the only stopping condition, and its action frequencies"
            " diffed against the strategy this repo committed. Exploitability says what a perfect"
            " opponent wins; it does not say the strategy has stopped moving, and this is the"
            " measurement that does."
        ),
        "the_arithmetic_decision_15_states": (
            "The ruling says four cells at a 240-iteration working point and one of them"
            " re-solved to the cap and diffed against 'its own 240-iteration strategy'. No run"
            " ever produced a 240-iteration strategy: 240 was the working point assumed before"
            " the arena was ruled to full precision, and the cells the repo committed converged"
            " to the 0.3%-of-pot target at 280 to 340 iterations at full precision. So the"
            " comparison is against this cell's own committed strategy, at the iteration count it"
            " actually converged at, which is what the ruling's 'its own' names."
        ),
        "cell": cell.name,
        "why_this_cell": DEEP_CHECK_CELL_REASON,
        "spot_key": committed["spot_key"],
        "board": list(committed["board"]),
        "hero_position": committed["hero_position"],
        "preflop_line": committed["preflop_line"],
        "node_path": list(cell.node_path),
        "actions": committed["actions"],
        "committed_run": {
            "iterations": committed["iterations"],
            "achieved_exploitability_pct_of_pot": committed[
                "achieved_exploitability_pct_of_pot"
            ],
            "strategy_digest": strategy_digest(
                committed["hand_classes"], committed["class_weights"]
            ),
            "source": str(committed_cell_path(cell.name).relative_to(REPO_ROOT)),
            "stopping_rule": (
                f"the ruled target of {EXPLOITABILITY_TARGET_PCT_OF_POT}% of pot, checked every"
                f" {CHECK_EVERY_ITERATIONS} iterations"
            ),
        },
        "deep_run": {
            "iterations": outcome.iterations,
            "achieved_exploitability_pct_of_pot": outcome.exploit_pct_of_pot,
            "wall_seconds": round(outcome.wall_seconds, 1),
            "arena_storage": arena_storage,
            "arena_bytes": outcome.arena_bytes,
            "machine": MEASURING_MACHINE,
            "largest_in_class_divergence": divergence,
            "strategy_digest": strategy_digest(deep["hand_classes"], deep["class_weights"]),
            "stopping_rule": (
                f"the {SOLVE_ITERATION_CAP}-iteration cap alone, with the target posted at"
                f" {RUN_TO_THE_CAP_TARGET_PCT} so nothing else could stop it. The tree, the menu,"
                " the ranges and the arena are the committed configuration unchanged."
            ),
        },
        "movement": summarise_movement(movements, shapes, reach),
        "aggregate_frequencies": aggregate_frequencies(
            committed["actions"], shallow_rows, aligned, reach
        ),
        "classes_whose_top_action_changed": action_flips(order, shallow_rows, aligned, reach),
        "largest_movers": [
            {
                "hand_class": order[index],
                "committed": shallow_rows[index],
                "deep": aligned[index],
                "moved": movements[index],
                "committed_shape": shapes[index],
                "reach_share": round(reach[index], 5),
            }
            for index in ranked[:25]
        ],
        "per_class": {
            "note": (
                "Parallel arrays in the committed cell's own class order, so every figure above"
                " can be recomputed from this file without re-running anything. `reach_share` is"
                " the deep run's, and is how often hero's own line brings that class here."
            ),
            "hand_classes": order,
            "committed_weights": shallow_rows,
            "deep_weights": aligned,
            "moved": movements,
            "committed_shape": shapes,
            "reach_share": [round(value, 5) for value in reach],
        },
    }


DEEP_CHECK_CELL_REASON = (
    "9c8c7c is where indifference lives on the committed sample: of its 152 classes only 19 put"
    " 99% or more on one action and 101 spread past a tenth, so it is the hardest cell to claim"
    " settling on rather than the easiest. It is also hero's continuation-bet decision, which is"
    " the node a flop chart is read at most. Decision 15 names the monotone cell, and it is also"
    " the cheapest board this machine solves. One board is one board: rainbow collapses to 1,176"
    " classes against this board's 152 and was never solved to target anywhere in this phase."
)


def write_deep_object(
    object_dir: Path, cell: SampleCell, outcome: Any, arena_storage: str, node: dict[str, Any]
) -> tuple[Path, str]:
    """The deep run's whole node payload, outside git and digested, on the campaign's own shape.

    The committed diff is a reading of this, and a reading whose source nobody kept is a figure
    with nothing behind it. It is written beside the sample's objects for the same reason they
    are: the bytes are large, nothing in the gate reads them, and the repo holds the evidence
    that they exist rather than the bytes.
    """
    object_dir.mkdir(parents=True, exist_ok=True)
    path = object_dir / f"deep-srp-{cell.board_text}.node.json.gz"
    payload = {
        "board": list(cell.board),
        "cell": cell.name,
        "preflop_line": preflop_line_for("BB").rendered,
        "solve": {
            "outcome": outcome.outcome,
            "exploit_pct_of_pot": outcome.exploit_pct_of_pot,
            "iterations": outcome.iterations,
            "wall_seconds": outcome.wall_seconds,
            "arena_bytes": outcome.arena_bytes,
            "arena_storage": arena_storage,
            "machine": MEASURING_MACHINE,
            "stopping_rule": f"the {SOLVE_ITERATION_CAP}-iteration cap alone",
        },
        "config": solve_config_document(),
        "nodes": {cell.name: node},
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    with path.open("wb") as handle, gzip.GzipFile(
        filename="", mode="wb", fileobj=handle, mtime=0
    ) as stream:
        stream.write(raw)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def run_deep_check(
    cell: SampleCell,
    transport,
    oop_text: str,
    ip_text: str,
    tolerance: float,
    object_dir: Path,
) -> dict[str, Any]:
    """Re-solve one committed cell to the iteration cap and diff its frequencies."""
    committed = json.loads(committed_cell_path(cell.name).read_text(encoding="utf-8"))
    line = preflop_line_for("BB")
    plan = SolvePlan(
        label=f"deep-srp-{cell.board_text}",
        board=cell.board_text,
        preflop_line=line.rendered,
        range_oop=oop_text,
        range_ip=ip_text,
        starting_pot=line.pot_bb,
        effective_stack=line.effective_stack_bb,
        config=solve_config_document(),
    )
    outcome = run_solve(plan, transport, stop_only_at_the_iteration_cap=True)
    if outcome.iterations != SOLVE_ITERATION_CAP:
        raise SystemExit(
            f"the deep run stopped at {outcome.iterations} of {SOLVE_ITERATION_CAP} iterations,"
            " so it is not the deep run decision 15 asks for and nothing from it is written."
        )
    node = transport("/api/node", {"path": [path_step(i) for i in cell.node_path]})
    hero_line = preflop_line_for(cell.hero_position)
    harvested = harvest_node(
        node, cell.board, seat_of_player(cell.hero_position), hero_line.pot_bb, tolerance
    )
    deep = cell_document(
        harvested,
        preflop_line=hero_line,
        board=cell.board,
        blinds=BLINDS,
        price_substitutions=PRICE_SUBSTITUTIONS,
        achieved_exploitability_pct_of_pot=outcome.exploit_pct_of_pot,
        iterations=outcome.iterations,
    )
    arena_storage = transport.arena()
    document = deep_check_document(
        cell, committed, deep, outcome, arena_storage, node, harvested.class_divergence
    )
    path, digest = write_deep_object(object_dir, cell, outcome, arena_storage, node)
    document["deep_run"]["object_path"] = str(path)
    document["deep_run"]["object_digest"] = digest
    return document


def report_deep_check(document: dict[str, Any]) -> None:
    movement = document["movement"]
    deep = document["deep_run"]
    print(f"  deep run           {deep['iterations']} iterations,"
          f" {deep['achieved_exploitability_pct_of_pot']:.4f}% of pot,"
          f" {deep['wall_seconds'] / 60:.1f} min")
    print(f"  committed run      {document['committed_run']['iterations']} iterations,"
          f" {document['committed_run']['achieved_exploitability_pct_of_pot']:.4f}% of pot")
    print(f"  movement           max {movement['max']}, median {movement['median']},"
          f" p90 {movement['p90']}, mean {movement['mean']},"
          f" reach-weighted mean {movement['reach_weighted_mean']}")
    for shape, figures in movement["by_committed_shape"].items():
        print(f"  {shape:17s} {figures['classes']} classes,"
              f" max {figures['max']}, mean {figures['mean']}")
    for action in document["aggregate_frequencies"]:
        size = "" if action.get("size_bb") is None else f" {action['size_bb']:.4g}bb"
        print(f"  {action['action'] + size:17s} {action['committed_frequency']:.4f}"
              f" -> {action['deep_frequency']:.4f} ({action['moved']:+.4f})")
    print(f"  top action changed {len(document['classes_whose_top_action_changed'])} classes")


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
    print(f"  planned arena      {outcome.arena_bytes / 1e9:.2f} GB, {result.arena_storage}"
          " (read back off the built tree, not assumed from the environment)")
    for note in result.notes:
        print(f"  {note}")


def deep_check_run(args: argparse.Namespace, object_storage: str) -> int:
    """Decision 15's deep run end to end: one cell, one restarted server, one committed diff.

    It writes the deep node's whole payload to object storage the way a solve does, so the diff
    in the repo is a reading of bytes that exist rather than the only copy of them, and then
    rebuilds the index because the diff lands inside `data/artifacts` and moves its byte figures.
    """
    named = [cell for cell in SAMPLE_CELLS if cell.name == args.deep_check]
    if not named:
        raise SystemExit(f"no such cell: {args.deep_check!r}")
    cell = named[0]
    if not cell.in_the_sample:
        raise SystemExit(
            f"{cell.name} is listed and not held, so the repo holds no committed strategy to"
            " diff a deep run against."
        )
    oop, ip = conditional_ranges()
    oop_text, ip_text = range_text(oop), range_text(ip)
    print(f"machine            {MEASURING_MACHINE}")
    print(f"memory ceiling     {describe_memory_ceiling()}")
    print(f"arena              {RULED_ARENA_STORAGE}, asked for by"
          f" {SOLVER_COMPRESS_VARIABLE}={SOLVER_COMPRESS_FULL_PRECISION!r}")
    print(f"deep check         {cell.name} on {cell.board_text}, to the"
          f" {SOLVE_ITERATION_CAP}-iteration cap")
    refuse_a_foreign_server()
    server = Server(Path(args.server), Path(args.log_dir))
    tolerance = CLASS_AGREEMENT_TOLERANCE if args.tolerance is None else float(args.tolerance)
    transport = ArenaVerifiedTransport(http_transport(), RULED_ARENA_STORAGE)
    server.start(f"deep-{cell.board_text}")
    try:
        document = run_deep_check(
            cell, transport, oop_text, ip_text, tolerance, Path(args.object_dir)
        )
    except SolveDriverError as error:
        print(f"  refused: {error}")
        return 1
    finally:
        server.stop()
    write_json(DEEP_CHECK_PATH, document)
    report_deep_check(document)
    print(f"  wrote              {DEEP_CHECK_PATH.relative_to(REPO_ROOT)}"
          f" ({DEEP_CHECK_PATH.stat().st_size} bytes)")
    index = rebuild_index(load_manifest(object_storage))
    import_postflop_index(INDEX_PATH)
    print(f"  index             {index['committed_bytes']} bytes committed,"
          f" {index['headroom_bytes']} of headroom")
    return 0


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
    parser.add_argument("--determinism-tree", default=None, metavar="DIR",
                        help="a second run's data/artifacts/postflop tree; with"
                             " --determinism-objects, diffs it against the committed one and"
                             " writes data/artifacts/postflop/determinism.json")
    parser.add_argument("--determinism-objects", default=None, metavar="DIR",
                        help="that second run's object directory")
    parser.add_argument("--deep-check", nargs="?", const=DEEP_CHECK_CELL, default=None,
                        metavar="CELL",
                        help="decision 15's deep run: re-solve one committed cell to the"
                             f" {SOLVE_ITERATION_CAP}-iteration cap and diff its action"
                             " frequencies against the strategy the repo committed"
                             f" (default {DEEP_CHECK_CELL})")
    args = parser.parse_args(argv)

    if args.list:
        for cell in SAMPLE_CELLS:
            path = "root" if not cell.node_path else " -> ".join(str(i) for i in cell.node_path)
            kept = "sample+index" if cell.in_the_sample else "index only "
            print(f"{cell.name:38s} {cell.board_text:8s} hero={cell.hero_position:3s}"
                  f" node=[{path}]  {kept}  {cell.why}")
        return 0

    object_storage = f"local directory {args.object_dir} (no remote store is provisioned yet)"
    if args.index_only:
        index = rebuild_index(load_manifest(object_storage))
        print(f"index rebuilt: {len(index['entries'])} entries,"
              f" {index['committed_bytes']} bytes committed,"
              f" {index['headroom_bytes']} bytes of headroom")
        return 0

    if args.determinism_tree or args.determinism_objects:
        if not (args.determinism_tree and args.determinism_objects):
            parser.error("--determinism-tree and --determinism-objects are used together")
        document = determinism_document(
            Path(args.determinism_tree), Path(args.determinism_objects)
        )
        write_json(DETERMINISM_PATH, document)
        report_determinism(document)
        print(f"  wrote              {DETERMINISM_PATH.relative_to(REPO_ROOT)}"
              f" ({DETERMINISM_PATH.stat().st_size} bytes)")
        index = rebuild_index(load_manifest(object_storage))
        import_postflop_index(INDEX_PATH)
        print(f"  index              {index['committed_bytes']} bytes committed,"
              f" {index['headroom_bytes']} of headroom")
        return 0 if document["identical"] else 1

    if args.deep_check is not None:
        return deep_check_run(args, object_storage)

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
    print(f"arena              {RULED_ARENA_STORAGE}, asked for by"
          f" {SOLVER_COMPRESS_VARIABLE}={SOLVER_COMPRESS_FULL_PRECISION!r} and verified on"
          " every built tree")
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
                board, cells_for_board(board, wanted),
                ArenaVerifiedTransport(http_transport(), RULED_ARENA_STORAGE),
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
        object_dir = Path(args.object_dir)
        path, digest = write_object(object_dir, board, result)
        print(f"  object             {path} sha256 {digest[:16]}...")
        for built in result.cells:
            recorded = record_cell(
                built, manifest, object_dir, path, digest, result.arena_storage
            )
            print(f"  {recorded}")

    manifest["object_storage"] = object_storage
    write_json(OBJECT_MANIFEST_PATH, manifest)
    index = rebuild_index(manifest)
    import_postflop_index(INDEX_PATH)
    print(f"\nindex              {len(index['entries'])} entries,"
          f" {len(manifest[LISTED_NOT_HELD])} listed and not held")
    print(f"committed bytes    {index['committed_bytes']} in data/artifacts/postflop")
    print(f"artifact headroom  {index['headroom_bytes']} of {ARTIFACT_BYTE_CAP}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
