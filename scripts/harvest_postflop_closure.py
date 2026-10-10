"""Close solved boards from their own solve: flop and turn objects, the line index, the manifest.

Offline, one-time, never run by the gate. **This script must never be registered in `COMMANDS` in
`scripts/run_verify.py`**: it reads solver exports of about 6 GB a board that no clone holds, and
what the gate reads is the manifest it writes.

**What closing a board means** (phase 21's contract, "A solved board closes"): every flop and turn
decision point of the line, for both seats, kept from the one solve, or all refused together. The
river is not stored (decision 1, re-ruled 2026-10-04): the export still holds it, and this harvest
reads past every river record and writes it nowhere.

**The input is the solve's whole strategy export**, `srp-<board>.strats` in `--export-dir`, written
by `scripts/solve_postflop_sample.py --export-strategies` through the clone's bulk export
(`crates/solver/src/export.rs` in `~/projects/gtopen-poker-bot`, format `GTOSTRATS1`), with its
`.strats.json` sidecar and the solve's object `srp-<board>.nodes.json.gz` beside it. Nothing in
that folder is written, moved or deleted. Per board, in order:

1. The export's sha256 and size against its sidecar, streamed, before a byte is parsed.
2. The object's sha256 against the `object_digest` the committed `index.json` lists, then its
   solve record against the index: the same iterations and exploitability, the same solver build
   as the export, and the export's own iteration count. The machine and thread count the manifest
   records are that object's own machine record, since no committed file holds run A's.
3. One streamed pass over the export: every record's street against the cards on its path, the
   trailer's count against the records read, and the per-street counts against the sidecar.
4. The flop's decision points become cells through `postflop_harvest`, the path every committed
   cell came through: each record is put in the shape `POST /api/node` answers (`node_payload`)
   and handed to `harvest_node` and `cell_document`. The keys must be exactly
   `postflop_lines.flop_spot_keys(line, board)`. The export's per-combo strategy is compared with
   the object's committed node payloads, combo by combo and exactly, so the export is proved to be
   the solve the index digests.
5. The flop object, `{"cells": [...]}` uncompressed, is read back through the strategy's own reader
   (`postflop_committed.fetched_tables`, the importer's re-derivation), and the strategy digest of
   every spot the committed index lists on the board is **re-derived from those cells** and
   compared with the index; each cell the repo holds in `sample/`, or outside it as the listed cell
   document `objects.json` names, is compared whole. Any difference stops the run before anything
   is written: it is a finding for Taylor, never something to work around.
6. The turn object, `postflop_street_rows.encode_street_object`, rounded by decision 15's rule.

Only once every board has passed are the objects and the line index written under `--out`, laid
out by object key, and a fetch is run against them as a fresh machine would (a dict store over that
folder, both streets, into a temporary folder) before the manifest is written into the repo.

**The turn object's order, which the phase that plays the turn reads it by.** The format holds
rows and shapes only (`postflop_street_rows`), so the order is the whole of the naming:

- Decision points are the export's street-1 records in the export's own depth-first order: from
  the flop root, action children in the solver's action index order; where the flop ends, the turn
  cards in GTOpen card-code order, code = rank * 4 + suit with ranks 2 to A as 0 to 12 and suits
  c, d, h, s as 0 to 3, skipping the three flop cards; under one turn card, the turn's action nodes
  depth-first in action index order. The river beneath each is skipped and changes nothing else.
  On the committed line that is 49 turn cards under each of the flop's closing lines, 131 points
  per turn card, 6,419 in all.
- A point's rows are the acting seat's hands in GTOpen's `spot.hands[p]` order, one row per combo:
  ascending `combo_index(hi, lo) = hi * (hi - 1) / 2 + lo` over the two card codes, over the combos
  the posted range holds with positive weight and no flop card. `expected_hand_order` derives it
  from `postflop_lines.line_ranges` and the run refuses an export whose header disagrees. A combo
  holding the turn card keeps its row, the solver's uniform fallback, which no hand reaches.
- A row's entries are the node's actions in action index order, the order GTOpen's tree builder
  emits them and `postflop_tree_rule` ports.

**Rounding.** Every number is first taken the way `/api/node` puts it on the wire, the shortest
decimal that reads back as the same 32-bit float (`wire_value`), because that is what every
committed cell was rounded from; decision 15's rule then rounds turn rows as the flop's.

Usage:

    uv run python scripts/harvest_postflop_closure.py
    uv run python scripts/harvest_postflop_closure.py --measure
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import lzma
import struct
import sys
import tempfile
import time
from array import array
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts import postflop_lines as lines  # noqa: E402
from poker_training_bot.solver_artifacts import postflop_textures as textures  # noqa: E402
from poker_training_bot.solver_artifacts.postflop_artifact import (  # noqa: E402
    INDEX_PATH,
    POSTFLOP_DIR,
    SAMPLE_DIR,
)
from poker_training_bot.solver_artifacts.postflop_fetch import (  # noqa: E402
    fetch_line,
    require_fetched,
)
from poker_training_bot.solver_artifacts.postflop_harvest import (  # noqa: E402
    ACTION_KINDS,
    HarvestError,
    cell_document,
    flop_line,
    harvest_node,
    strategy_digest,
)
from poker_training_bot.solver_artifacts.postflop_key import postflop_spot_key  # noqa: E402
from poker_training_bot.solver_artifacts.postflop_manifest import (  # noqa: E402
    CLOSED,
    LINE_INDEX_SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
    REFUSED,
    STORED_STREETS,
    expected_closure_counts,
    index_object_key,
    manifest_errors,
    manifest_path,
    street_object_key,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (  # noqa: E402
    SolveOutcome,
    classify_outcome,
    commit_verdict,
)
from poker_training_bot.solver_artifacts.postflop_street_rows import (  # noqa: E402
    encode_street_object,
    street_object_decision_points,
)
from poker_training_bot.solver_artifacts.solve_conditions import BlindStructure  # noqa: E402
from poker_training_bot.strategy.postflop_committed import fetched_tables  # noqa: E402

DEFAULT_EXPORT_DIR = Path.home() / "poker-bot-solve-objects" / "postflop-clone-b058335"
DEFAULT_LINE = "BTN:raise@2.5,BB:call"
OBJECT_MANIFEST_PATH = POSTFLOP_DIR / "objects.json"
LISTED_NOT_HELD = "listed_not_held"

STRATS_MAGIC = b"GTOSTRATS1\n"
STRATS_TRAILER = b"END\n"
EXPORT_FORMAT = "GTOSTRATS1"
EXPORT_STREETS = ("flop", "turn", "river")
CARD_STEP = 0x80
"""A path step at or above this is a dealt card, `step - 0x80` its code; below, an action index."""
CARD_RANKS = "23456789TJQKA"
CARD_SUITS = "cdhs"
READ_BUFFER_BYTES = 8 << 20
HASH_CHUNK_BYTES = 16 << 20

_RECORD_HEAD = struct.Struct("<BBH")
_ACTION = struct.Struct("<Bd")
_COUNT = struct.Struct("<Q")
_F32 = struct.Struct("<f")
_ROUNDING_SCALE = 1000
_BOUNDARY_WINDOW = 1e-4
"""How near a half-thousandth a 32-bit value must sit before its wire decimal can round apart from
it. A float32 below one is within 3e-8 of its shortest decimal, so outside this window both round
to the same thousandth and the exact conversion is skipped."""


class ClosureError(RuntimeError):
    """A refusal to close a board. Raised before anything is written."""


# --------------------------------------------------------------------------- #
# Numbers as the wire carries them
# --------------------------------------------------------------------------- #


def wire_value(value: float) -> float:
    """A float32 as `/api/node` serialises it: the shortest decimal that reads back as the same
    float32, then read as a Python float, which is what every committed cell was rounded from."""
    exact = _F32.unpack(_F32.pack(value))[0]
    for digits in range(1, 10):
        text = f"{exact:.{digits}g}"
        if _F32.unpack(_F32.pack(float(text)))[0] == exact:
            return float(text)
    return exact


def wire_row(row: list[float]) -> list[float]:
    """One row as rounding sees it on the wire. Only a row with an entry near a rounding boundary
    pays for the exact conversion; any other row rounds to the same thousandths either way and is
    returned as it is."""
    for value in row:
        if abs((value * _ROUNDING_SCALE) % 1.0 - 0.5) < _BOUNDARY_WINDOW:
            return [wire_value(entry) for entry in row]
    return row


# --------------------------------------------------------------------------- #
# Reading the export
# --------------------------------------------------------------------------- #


@dataclass
class ExportRecord:
    """One action node of the export: who acts, how it was reached, its menu, and its rows."""

    street: int
    player: int
    path: bytes
    actions: tuple[tuple[str, float], ...]
    rows: list[list[float]] = field(default_factory=list)


@dataclass
class ExportContents:
    header: dict[str, Any]
    flop: list[ExportRecord]
    turn: list[list[list[float]]]
    per_street: list[int]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exactly(handle: io.BufferedReader, size: int, what: str) -> bytes:
    data = handle.read(size)
    if len(data) != size:
        raise ClosureError(f"the export ends inside {what}")
    return data


def _rows(data: bytes, hands: int, actions: int) -> list[list[float]]:
    values = array("f")
    values.frombytes(data)
    if sys.byteorder != "little":
        values.byteswap()
    flat = values.tolist()
    return [flat[start : start + actions] for start in range(0, hands * actions, actions)]


def read_export(path: Path) -> ExportContents:
    """One streamed pass: the flop records with their rows, the turn rows, and the river skipped.

    The file is never held whole: a river record's rows are seeked past, so memory is the turn's
    rows and a read buffer."""
    flop: list[ExportRecord] = []
    turn: list[list[list[float]]] = []
    per_street = [0, 0, 0]
    with path.open("rb", buffering=READ_BUFFER_BYTES) as handle:
        if handle.read(len(STRATS_MAGIC)) != STRATS_MAGIC:
            raise ClosureError(f"{path} is not a {EXPORT_FORMAT} export")
        header = json.loads(handle.readline())
        if header.get("format") != EXPORT_FORMAT:
            raise ClosureError(f"{path} declares format {header.get('format')!r}")
        hands = [len(header["hands"][0]), len(header["hands"][1])]
        records = 0
        while True:
            head = _exactly(handle, len(STRATS_TRAILER), "a record or the trailer")
            if head == STRATS_TRAILER:
                break
            street, player, path_len = _RECORD_HEAD.unpack(head)
            route = _exactly(handle, path_len, "a record's path")
            if street >= len(EXPORT_STREETS) or player > 1:
                raise ClosureError(f"record {records} has street {street} and player {player}")
            if sum(step >= CARD_STEP for step in route) != street:
                raise ClosureError(f"record {records} is on street {street}, path {list(route)}")
            (count,) = _exactly(handle, 1, "a record's menu size")
            menu = _exactly(handle, count * _ACTION.size, "a record's menu")
            row_bytes = hands[player] * count * _F32.size
            if street == 2:
                handle.seek(row_bytes, io.SEEK_CUR)
            else:
                rows = _rows(_exactly(handle, row_bytes, "a record's rows"), hands[player], count)
                if street == 0:
                    actions = tuple(
                        (ACTION_KINDS[kind], amount) for kind, amount in _ACTION.iter_unpack(menu)
                    )
                    flop.append(ExportRecord(street, player, route, actions, rows))
                else:
                    turn.append([wire_row(row) for row in rows])
            per_street[street] += 1
            records += 1
        (trailer,) = _COUNT.unpack(_exactly(handle, _COUNT.size, "the trailer's count"))
        if trailer != records or handle.read(1):
            raise ClosureError(f"{path}: the trailer counts {trailer}, the file holds {records}")
    return ExportContents(header, flop, turn, per_street)


def expected_hand_order(weights: Mapping[str, float], board: Sequence[str]) -> list[str]:
    """GTOpen's `spot.hands[p]` for one seat: every combo of a positively weighted class that
    touches no board card, in ascending combo index, each written high card first."""
    codes = {
        f"{rank}{suit}": 4 * r + s
        for r, rank in enumerate(CARD_RANKS)
        for s, suit in enumerate(CARD_SUITS)
    }
    dealt = {codes[card] for card in board}
    held: list[tuple[int, int]] = []
    for hand, weight in weights.items():
        if weight <= 0:
            continue
        high, low = CARD_RANKS.index(hand[0]), CARD_RANKS.index(hand[1])
        for one in range(4):
            for two in range(4):
                if (len(hand) == 2 and one >= two) or (hand.endswith("s") != (one == two)):
                    continue
                pair = sorted((4 * high + one, 4 * low + two), reverse=True)
                if not dealt & set(pair):
                    held.append((pair[0], pair[1]))
    held.sort(key=lambda pair: pair[0] * (pair[0] - 1) // 2 + pair[1])
    names = {code: card for card, code in codes.items()}
    return [names[hi] + names[lo] for hi, lo in held]


# --------------------------------------------------------------------------- #
# The flop, through the harvest every committed cell came through
# --------------------------------------------------------------------------- #


def node_payload(
    record: ExportRecord,
    by_path: Mapping[bytes, ExportRecord],
    hands: Sequence[str],
    starting_pot_bb: float,
) -> dict[str, Any]:
    """One flop record in the shape `POST /api/node` answers, as far as `harvest_node` reads it.

    The history is replayed from the root through each ancestor's own menu: `put` counts the whole
    hand from half the starting pot a seat, a bet or raise moves the actor's street level to its
    amount, a call matches the highest level, and each step carries the pot as it stood before it.
    """
    put = [starting_pot_bb / 2.0, starting_pot_bb / 2.0]
    level = [0.0, 0.0]
    history: list[dict[str, Any]] = []
    for depth, chosen in enumerate(record.path):
        parent = by_path.get(record.path[:depth])
        if parent is None or chosen >= len(parent.actions):
            raise ClosureError(f"flop path {list(record.path)} leaves the exported tree")
        history.append(
            {
                "player": parent.player,
                "pot": sum(put),
                "actions": [{"kind": kind, "amount": amount} for kind, amount in parent.actions],
                "chosen": chosen,
            }
        )
        kind, amount = parent.actions[chosen]
        seat = parent.player
        if kind in ("bet", "raise"):
            put[seat] += amount - level[seat]
            level[seat] = amount
        elif kind == "call":
            put[seat] += max(level) - level[seat]
            level[seat] = max(level)
    menu = [{"kind": kind, "amount": amount} for kind, amount in record.actions]
    history.append({"player": record.player, "pot": sum(put), "actions": menu, "chosen": None})
    players: list[dict[str, Any]] = [{"hands": []}, {"hands": []}]
    players[record.player]["hands"] = [
        {"combo": combo, "strategy": wire_row(row)}
        for combo, row in zip(hands, record.rows, strict=True)
    ]
    return {
        "node_type": "action",
        "player": record.player,
        "actions": menu,
        "players": players,
        "history": history,
        "put": put,
    }


def blinds() -> BlindStructure:
    structure = lines.committed_chart()["blind_structure"]
    return BlindStructure(
        small_blind_bb=float(structure["small_blind_bb"]),
        big_blind_bb=float(structure["big_blind_bb"]),
        ante_bb=float(structure["ante_bb"]),
    )


def flop_cells(
    line: str, board: tuple[str, ...], contents: ExportContents, exploit: float, iterations: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """Every flop decision point as a committed cell, in the export's order, with the node
    payloads they were harvested from, and each point the harvest refuses, by its spot key.

    A refusal is collected rather than raised so that every refused point on a board is named
    at once; a board with any refusal does not close."""
    labels = lines.seat_labels(line)
    by_path = {record.path: record for record in contents.flop}
    cells, payloads, refused, keys = [], [], {}, []
    for record in contents.flop:
        hero = lines.preflop_line_for(line, labels[record.player])
        payload = node_payload(
            record, by_path, contents.header["hands"][record.player], hero.pot_bb
        )
        payloads.append(payload)
        try:
            harvested = harvest_node(payload, board, labels, hero.pot_bb)
        except HarvestError as error:
            history, _ = flop_line(payload, labels, hero.pot_bb)
            spot = postflop_spot_key(hero, board, history, hero.pot_bb, hero.effective_stack_bb)
            refused[spot] = str(error)
            keys.append(spot)
            continue
        cell = cell_document(
            harvested,
            preflop_line=hero,
            board=board,
            blinds=blinds(),
            price_substitutions=lines.price_substitutions(line),
            achieved_exploitability_pct_of_pot=exploit,
            iterations=iterations,
        )
        cells.append(cell)
        keys.append(cell["spot_key"])
    expected = lines.flop_spot_keys(line, board)
    if sorted(keys) != sorted(expected):
        raise ClosureError(
            f"{''.join(board)}: the export's flop keys {keys} are not the line's {expected}"
        )
    return cells, payloads, refused


def compare_with_object(
    board: str, payloads: Sequence[Mapping[str, Any]], nodes: Mapping[str, Any]
) -> int:
    """The export's flop rows against the solve's committed node payloads, exactly, combo by
    combo. Returns how many combos were compared."""
    by_route = {
        tuple(step["chosen"] for step in payload["history"][:-1]): payload for payload in payloads
    }
    compared = 0
    for name, node in nodes.items():
        route = tuple(step["chosen"] for step in node["history"][:-1])
        mine = by_route.get(route)
        if mine is None:
            raise ClosureError(f"{board}: the object's node {name} is not a flop record")
        theirs = [(entry["kind"], entry["amount"]) for entry in node["actions"]]
        if [(entry["kind"], entry["amount"]) for entry in mine["actions"]] != theirs:
            raise ClosureError(f"{board}: node {name}'s menu differs between export and object")
        held = mine["players"][mine["player"]]["hands"]
        committed = node["players"][node["player"]]["hands"]
        for one, two in zip(held, committed, strict=True):
            exact = [wire_value(value) for value in one["strategy"]]
            if one["combo"] != two["combo"] or exact != two["strategy"]:
                raise ClosureError(
                    f"{board}: node {name}, {two['combo']}: the object holds {two['strategy']},"
                    f" the export {one['combo']} {exact}"
                )
            compared += 1
    return compared


# --------------------------------------------------------------------------- #
# One board
# --------------------------------------------------------------------------- #


@dataclass
class ClosedBoard:
    board: tuple[str, ...]
    entry: dict[str, Any]
    objects: dict[str, bytes]
    digests: dict[str, tuple[str, str]]
    whole_cells_matched: int
    combos_compared: int
    seconds: float
    phases: dict[str, float]
    refused: dict[str, str] = field(default_factory=dict)
    """Flop decision points the harvest refuses, by spot key. Any one keeps the board open."""


def _solve_record(object_path: Path, listed: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    digest = sha256_file(object_path)
    wanted = {entry["object_digest"] for entry in listed}
    if wanted != {digest}:
        raise ClosureError(f"{object_path} has sha256 {digest}; the index lists {sorted(wanted)}")
    with gzip.open(object_path, "rb") as stream:
        return json.loads(stream.read())


def _committed_cells(listed: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Each cell document the repo commits or records for the board's listed spots, by key."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(SAMPLE_DIR.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        found[document["spot_key"]] = document
    if OBJECT_MANIFEST_PATH.is_file():
        recorded = json.loads(OBJECT_MANIFEST_PATH.read_text(encoding="utf-8"))
        for spot, figures in recorded.get(LISTED_NOT_HELD, {}).items():
            path = Path(figures.get("cell_document", ""))
            if path.is_file():
                found[spot] = json.loads(path.read_text(encoding="utf-8"))
    keys = {entry["spot_key"] for entry in listed}
    return {spot: document for spot, document in found.items() if spot in keys}


def close_board(
    line: str, board: tuple[str, ...], export_dir: Path, listed: Sequence[Mapping[str, Any]]
) -> ClosedBoard:
    """Every check on one board, ending in its two objects and its manifest entry, or a refusal.
    Nothing is written here."""
    started = time.perf_counter()
    phases: dict[str, float] = {}
    name = "".join(board)
    export = export_dir / f"srp-{name}.strats"
    sidecar = json.loads((export_dir / f"srp-{name}.strats.json").read_text(encoding="utf-8"))
    if sidecar.get("format") != EXPORT_FORMAT or export.stat().st_size != sidecar["bytes"]:
        raise ClosureError(f"{export} is not the {sidecar['bytes']}-byte export its sidecar names")
    if (found := sha256_file(export)) != sidecar["sha256"]:
        raise ClosureError(f"{export} has sha256 {found}; its sidecar says {sidecar['sha256']}")
    phases["export sha256"] = time.perf_counter() - started

    record = _solve_record(export_dir / f"srp-{name}.nodes.json.gz", listed)
    solve = record["solve"]
    exploit, iterations = solve["exploit_pct_of_pot"], solve["iterations"]
    for entry in listed:
        if (entry["achieved_exploitability_pct_of_pot"], entry["iterations"]) != (
            exploit,
            iterations,
        ):
            raise ClosureError(f"{entry['spot_key']}: the index and the solve record disagree")
    if solve["solver_build"] != sidecar["solver_build"]:
        raise ClosureError(f"{name}: the export and the solve name different solver builds")

    mark = time.perf_counter()
    contents = read_export(export)
    phases["export read"] = time.perf_counter() - mark
    header = contents.header
    if tuple(header["board"]) != board or header["iteration"] != iterations:
        raise ClosureError(f"{name}: the export is of {header['board']} at {header['iteration']}")
    if contents.per_street != list(sidecar["export_summary"]["per_street"]):
        raise ClosureError(f"{name}: read {contents.per_street}, the sidecar says otherwise")
    ranges = lines.line_ranges(line)
    for seat, weights in enumerate((ranges.range_oop, ranges.range_ip)):
        if header["hands"][seat] != expected_hand_order(weights, board):
            raise ClosureError(f"{name}: seat {seat}'s hands are not the documented order")
    counts = dict(zip(EXPORT_STREETS[:2], contents.per_street[:2], strict=True))
    if counts != expected_closure_counts(line):
        raise ClosureError(f"{name}: the export holds {counts}, the line's tree closes on more")

    mark = time.perf_counter()
    status = _status(line, name, exploit, iterations)
    entry = {
        "board": list(board),
        "status": status,
        "decision_points": counts if status == CLOSED else dict.fromkeys(STORED_STREETS, 0),
        "achieved_exploitability_pct_of_pot": exploit,
        "iterations": iterations,
        "machine": solve["machine_description"],
        "threads": solve["threads"],
    }
    if status != CLOSED:
        return ClosedBoard(board, entry, {}, {}, 0, 0, time.perf_counter() - started, phases)
    cells, payloads, refused = flop_cells(line, board, contents, exploit, iterations)
    compared = compare_with_object(name, payloads, record["nodes"])
    flop_bytes = json.dumps({"cells": cells}, separators=(",", ":")).encode("utf-8")
    digests, whole = _rederive(flop_bytes, cells, listed)
    entry["strategy_digests"] = {spot: mine for spot, (mine, _) in digests.items()}
    phases["flop harvest"] = time.perf_counter() - mark

    mark = time.perf_counter()
    turn_bytes = encode_street_object(contents.turn)
    if street_object_decision_points(turn_bytes) != counts["turn"]:
        raise ClosureError(f"{name}: the turn object does not hold {counts['turn']} points")
    phases["turn encode"] = time.perf_counter() - mark
    objects = {"turn": turn_bytes} if refused else {"flop": flop_bytes, "turn": turn_bytes}
    seconds = time.perf_counter() - started
    return ClosedBoard(board, entry, objects, digests, whole, compared, seconds, phases, refused)


def _status(line: str, name: str, exploit: float, iterations: int) -> str:
    outcome = SolveOutcome(
        label=name,
        board=name,
        preflop_line=line,
        outcome=classify_outcome(float(exploit), iterations),
        exploit_pct_of_pot=float(exploit),
        iterations=iterations,
        wall_seconds=0.0,
        arena_bytes=0,
    )
    return CLOSED if commit_verdict(outcome)[0] else REFUSED


def _rederive(
    flop_bytes: bytes, cells: Sequence[Mapping[str, Any]], listed: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, tuple[str, str]], int]:
    """Each listed spot's strategy digest, re-derived from the flop object as the strategy reads
    it, against the committed index; and each committed cell document against the harvested one.
    Returns `{spot: (re-derived, committed)}` and how many whole documents matched."""
    with tempfile.TemporaryDirectory() as scratch:
        path = Path(scratch) / "flop.json"
        path.write_bytes(flop_bytes)
        imported = {table.cell.spot_key: table.cell for table in fetched_tables(path)}
    digests: dict[str, tuple[str, str]] = {}
    for entry in listed:
        cell = imported.get(entry["spot_key"])
        if cell is None:
            raise ClosureError(
                f"{entry['spot_key']} is listed in the committed index and the harvest refused it"
            )
        mine = strategy_digest(cell.hand_classes, cell.class_weights)
        digests[entry["spot_key"]] = (mine, entry["strategy_digest"])
    differ = {spot: pair for spot, pair in digests.items() if pair[0] != pair[1]}
    if differ:
        raise ClosureError(f"re-derived strategy digests differ from the index: {differ}")
    by_key = {cell["spot_key"]: cell for cell in cells}
    committed = _committed_cells(listed)
    for spot, document in committed.items():
        if by_key[spot] != document:
            changed = sorted(key for key in document if document[key] != by_key[spot].get(key))
            raise ClosureError(f"{spot}: the harvested cell differs from the committed: {changed}")
    return digests, len(committed)


# --------------------------------------------------------------------------- #
# The line: index, objects, fetch, manifest
# --------------------------------------------------------------------------- #


class FolderStore:
    """An object store answered from the closure folder: the bucket, before any upload."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()


def line_index(line: str, closed: Sequence[ClosedBoard]) -> bytes:
    boards = []
    for board in closed:
        if board.entry["status"] != CLOSED:
            continue
        boards.append(
            {
                "board": list(board.board),
                "decision_points": board.entry["decision_points"],
                "objects": {
                    street: {
                        "key": street_object_key(line, board.board, street),
                        "sha256": hashlib.sha256(board.objects[street]).hexdigest(),
                    }
                    for street in STORED_STREETS
                },
            }
        )
    document = {
        "line_index_schema_version": LINE_INDEX_SCHEMA_VERSION,
        "preflop_line": line,
        "boards": boards,
    }
    return (json.dumps(document, indent=1) + "\n").encode("utf-8")


def manifest_document(line: str, index_bytes: bytes, closed: Sequence[ClosedBoard]) -> dict:
    entries = [board.entry for board in closed]
    return {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "preflop_line": line,
        "index": {
            "object_key": index_object_key(line),
            "sha256": hashlib.sha256(index_bytes).hexdigest(),
            "bytes": len(index_bytes),
        },
        "flops_held": sum(
            textures.flops_in_class(tuple(entry["board"]))
            for entry in entries
            if entry["status"] == CLOSED
        ),
        "refused_boards": sum(entry["status"] == REFUSED for entry in entries),
        "boards": entries,
    }


def write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_bytes(data)
    partial.replace(path)


def listed_boards(line: str) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    """The committed index's entries on `line`, by board, in the index's order."""
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    by_board: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for entry in index["entries"]:
        if entry["preflop_line"].endswith(f"/{line}"):
            by_board.setdefault(tuple(entry["board"]), []).append(entry)
    return by_board


def measure(closed: Sequence[ClosedBoard]) -> None:
    """Stored size of a closed flop and what standard compression saves on each turn object.
    Printed only: these are figures for the campaign budget ask, never committed."""
    for board in closed:
        name = "".join(board.board)
        turn = board.objects.get("turn")
        if turn is None:
            continue
        flop = board.objects.get("flop")
        stored = f"closed flop {len(flop) + len(turn):,} B" if flop else "board not closed"
        flop_size = f"{len(flop):,} B" if flop else "none"
        print(f"  {name}: flop object {flop_size}, turn object {len(turn):,} B, {stored}")
        for label, packed in (
            ("gzip -9", gzip.compress(turn, compresslevel=9, mtime=0)),
            ("lzma -9e", lzma.compress(turn, preset=9 | lzma.PRESET_EXTREME)),
        ):
            saved = 100 * (1 - len(packed) / len(turn))
            print(f"    turn {label}: {len(packed):,} B, {saved:.1f}% saved")


def _print_board(result: ClosedBoard) -> None:
    for spot, (mine, committed) in result.digests.items():
        verdict = "matches" if mine == committed else "DIFFERS"
        print(f"  digest re-derived  {spot}: {mine} (index {committed}, {verdict})")
    print(
        f"  {result.whole_cells_matched} committed cell documents equal whole,"
        f" {result.combos_compared} combos equal the solve's object exactly"
    )
    for spot, reason in result.refused.items():
        print(f"  harvest refused    {spot}: {reason}")
    timing = ", ".join(f"{label} {seconds:.1f}s" for label, seconds in result.phases.items())
    state = "not closed" if result.refused else result.entry["status"]
    print(f"  {state} in {result.seconds:.1f}s ({timing})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--line", default=DEFAULT_LINE)
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR), metavar="DIR")
    parser.add_argument(
        "--out",
        default=None,
        metavar="DIR",
        help="where the objects and line index are written, by object key;"
        " default <export-dir>/closure, outside git",
    )
    parser.add_argument(
        "--measure",
        action="store_true",
        help="print each closed flop's stored size and what compression saves on its turn",
    )
    args = parser.parse_args(argv)
    export_dir = Path(args.export_dir).expanduser()
    out = Path(args.out).expanduser() if args.out else export_dir / "closure"
    line = args.line

    closed: list[ClosedBoard] = []
    try:
        for board, listed in listed_boards(line).items():
            print("".join(board))
            closed.append(close_board(line, board, export_dir, listed))
            _print_board(closed[-1])
    except ClosureError as error:
        print(f"REFUSED: {error}. Nothing was written.", file=sys.stderr)
        return 1
    if args.measure:
        measure(closed)
    open_boards = ["".join(board.board) for board in closed if board.refused]
    if open_boards:
        print(
            f"REFUSED: the harvest refuses flop decision points on {open_boards}, so those boards"
            " cannot close and no manifest is written. Nothing was written.",
            file=sys.stderr,
        )
        return 1

    index_bytes = line_index(line, closed)
    manifest = manifest_document(line, index_bytes, closed)
    if errors := manifest_errors(manifest):
        print(f"REFUSED: the manifest fails its own checks: {errors}", file=sys.stderr)
        return 1
    for board in closed:
        for street, data in board.objects.items():
            write_file(out / street_object_key(line, board.board, street), data)
    write_file(out / index_object_key(line), index_bytes)
    with tempfile.TemporaryDirectory() as scratch:
        fetched = fetch_line(manifest, FolderStore(out), Path(scratch), streets=STORED_STREETS)
        for street in STORED_STREETS:
            require_fetched(manifest, Path(scratch), street=street)
    print(f"fetched from {out}: {len(fetched)} boards, both streets, every check passed")
    target = manifest_path(line)
    write_file(target, (json.dumps(manifest, indent=1) + "\n").encode("utf-8"))
    print(f"wrote {target.relative_to(REPO_ROOT)}; run solve_postflop_sample.py --index-only next")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
