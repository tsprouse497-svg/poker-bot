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
    postflop_spot_key,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (  # noqa: E402
    MEASURING_MACHINE,
    RULED_ARENA_STORAGE,
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
