"""The committed GTOpen preflop export: its shape, its reader, and its source card.

An export is one solved tree written in the solver's own vocabulary - action indices,
GTOpen's 169-class ordering, GTOpen's own action labels - rather than in this repo's spot
keys. Nothing here converts it into a chart, and nothing in the runtime reads it.

Two orderings of the 169 hand classes now live in this package and they disagree on all
but a handful of classes. `hand_classes.hand_class_grid_index` walks the rank grid high to
low, which is what a chart report prints. GTOpen numbers ranks low to high and puts suited
above the diagonal. `gtopen_class_index` is the solver's, and it is the only one that may
be used to index a payload.

Frequencies are stored as integers in basis points, renormalised so every class's row sums
to 10,000 exactly (decision 8). One basis point is finer than any decision a chart makes
and coarser than the noise a solve carries, and integers are what makes a checksum over the
data mean something.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import struct
import sys
from array import array
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG, config_errors
from poker_training_bot.solver_artifacts.gtopen_source_card import (
    load_source_card,
    source_card_errors,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES

__all__ = [
    "COMMITTED_EXPORT_PATH",
    "COMMITTED_SOURCE_CARD_PATH",
    "QUANTISATION_SCALE",
    "RULED_CONFIG",
    "SOLVE_ITERATION_CAP",
    "SOLVE_TARGET_GAP_BB",
    "SolverExport",
    "SolverNode",
    "class_combos",
    "export_checksum",
    "gtopen_class_index",
    "load_solver_export",
    # The card is a different subject from the tree and holding both broke the 500-line
    # cap, so it lives in `gtopen_source_card`. It is re-exported because the frozen tests
    # import it from here, which is the name the specification uses.
    "load_source_card",
    "node_from_payload",
    "source_card_errors",
    "write_solver_export",
]

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPORTS_DIR = REPO_ROOT / "data" / "artifacts" / "preflop" / "exports"
COMMITTED_EXPORT_PATH = EXPORTS_DIR / "gtopen_six_max_100bb_rakefree.gtx.gz"
COMMITTED_SOURCE_CARD_PATH = EXPORTS_DIR / "gtopen_six_max_100bb_rakefree.source.json"

QUANTISATION_SCALE = 10_000
"""Decision 8: basis points, 0 to 10,000, each class's row renormalised to the scale."""

SOLVE_TARGET_GAP_BB = 0.01
SOLVE_ITERATION_CAP = 2_000
"""Decision 3: GTOpen's own default target and cap, recorded before the committed run."""

EXPORT_SCHEMA_VERSION = 1
CONTAINER_MAGIC = b"GTOPENEXPORT1\n"

_GTOPEN_RANKS = "23456789TJQKA"


def _build_gtopen_index() -> dict[str, int]:
    index: dict[str, int] = {}
    for name in HAND_CLASSES:
        high, low = _GTOPEN_RANKS.index(name[0]), _GTOPEN_RANKS.index(name[1])
        if len(name) == 2:
            index[name] = high * 13 + high
        elif name.endswith("s"):
            index[name] = high * 13 + low
        else:
            index[name] = low * 13 + high
    return index


_GTOPEN_INDEX = _build_gtopen_index()
_COMBOS_BY_NAME = {n: 6 if len(n) == 2 else 4 if n.endswith("s") else 12 for n in HAND_CLASSES}
_COMBOS_BY_INDEX = [0] * 169
for _name, _index in _GTOPEN_INDEX.items():
    _COMBOS_BY_INDEX[_index] = _COMBOS_BY_NAME[_name]


def gtopen_class_index(hand_class_text: str) -> int:
    """GTOpen's own index for a hand class, read from `preflop/equity.rs`.

    Ranks run 0 to 12 as `2` through `A`; a pair sits at `hi*13+hi`, a suited class at
    `hi*13+lo`, an offsuit class at `lo*13+hi`. Confusing this with the grid ordering
    transposes suited and offsuit, which is the single most likely extraction defect.
    """
    try:
        return _GTOPEN_INDEX[hand_class_text]
    except KeyError:
        raise ValueError(f"unknown hand class: {hand_class_text!r}") from None


def class_combos(hand_class_text: str) -> int:
    """Six for a pair, four suited, twelve offsuit. They sum to 1,326."""
    try:
        return _COMBOS_BY_NAME[hand_class_text]
    except KeyError:
        raise ValueError(f"unknown hand class: {hand_class_text!r}") from None


@dataclass(frozen=True)
class SolverAction:
    label: str
    kind: str
    to: float
    terminal: bool

    def as_payload(self) -> dict:
        return {"label": self.label, "kind": self.kind, "to": self.to, "terminal": self.terminal}


@dataclass(frozen=True)
class SolverNode:
    """One action node: who is to act, what they may do, and how often they do it."""

    path: tuple[int, ...]
    actor_pos: str
    actions: tuple[SolverAction, ...]
    strategy_bp: tuple[array, ...]
    reach_bp: array

    def weight_bp(self, action_index: int, hand_class_text: str) -> int:
        return self.strategy_bp[action_index][gtopen_class_index(hand_class_text)]

    def action_frequency(self, action_index: int, weight_by_reach: bool = True) -> float:
        """The frequency GTOpen itself reports for an action at this node.

        Combo-weighted, and weighted by the arriving range unless that is switched off.
        The payload is unconditional - a hand the actor folded upstream still carries a
        full strategy row here - so `reach` is the only thing that conditions it, and
        dropping it produces a number that is self-consistent and wrong.
        """
        row = self.strategy_bp[action_index]
        total = 0.0
        weighted = 0.0
        for index in range(169):
            weight = _COMBOS_BY_INDEX[index]
            if weight_by_reach:
                weight *= self.reach_bp[index]
            if weight:
                total += weight
                weighted += weight * row[index]
        return weighted / total / QUANTISATION_SCALE if total else 0.0

    def as_payload(self) -> dict:
        return {
            "path": list(self.path),
            "actor_pos": self.actor_pos,
            "actions": [action.as_payload() for action in self.actions],
            "strategy_bp": [list(row) for row in self.strategy_bp],
            "reach_bp": list(self.reach_bp),
        }


def _quantise_row(raw: Sequence[float]) -> list[int]:
    """One class's action distribution, in basis points summing to the scale.

    Weights below one basis point are dropped rather than rounded up, because that is
    precision the solve does not have. What is left is renormalised by largest remainder,
    since rounding each action independently loses or gains a basis point most of the time.
    """
    kept = [value if value * QUANTISATION_SCALE >= 1.0 else 0.0 for value in raw]
    total = sum(kept)
    if total <= 0.0:
        return [QUANTISATION_SCALE] + [0] * (len(raw) - 1)
    exact = [value / total * QUANTISATION_SCALE for value in kept]
    floors = [int(value) for value in exact]
    short = QUANTISATION_SCALE - sum(floors)
    order = sorted(range(len(exact)), key=lambda i: (exact[i] - floors[i], i), reverse=True)
    for i in order[:short]:
        floors[i] += 1
    return floors


def node_from_payload(
    view: dict, path: Sequence[int], terminal: Sequence[bool] | None = None
) -> SolverNode:
    """Convert one `/api/preflop/node` view into a quantised node.

    A raw view does not say which of its actions end the hand, so the walker that found
    the node's children supplies that; without it every action is recorded as continuing,
    which a traversal check then rejects rather than silently accepts.
    """
    raw_actions = view["actions"]
    count = len(raw_actions)
    flags = list(terminal) if terminal is not None else [False] * count
    strategy = view["strategy"]
    rows = [[0] * 169 for _ in range(count)]
    for index in range(169):
        quantised = _quantise_row([strategy[k * 169 + index] for k in range(count)])
        for k in range(count):
            rows[k][index] = quantised[k]
    reach = [
        min(QUANTISATION_SCALE, max(0, round(value * QUANTISATION_SCALE)))
        for value in view["reach"]
    ]
    actions = tuple(
        SolverAction(action["label"], action["kind"], float(action["to"]), bool(flag))
        for action, flag in zip(raw_actions, flags, strict=True)
    )
    return SolverNode(
        tuple(path),
        view["actor_pos"],
        actions,
        tuple(array("H", row) for row in rows),
        array("H", reach),
    )


def _node_from_export(entry: dict) -> SolverNode:
    actions = tuple(
        SolverAction(a["label"], a["kind"], float(a["to"]), bool(a["terminal"]))
        for a in entry["actions"]
    )
    rows = tuple(_as_weights(row) for row in entry["strategy_bp"])
    return SolverNode(
        tuple(entry["path"]), entry["actor_pos"], actions, rows, _as_weights(entry["reach_bp"])
    )


def _as_weights(values) -> array:
    """Basis points as `uint16`. A node holds 760 of them and a tree holds 29 million, so
    a list of boxed Python ints is a gigabyte of pointers for data that fits in 59 MB."""
    if isinstance(values, array) and values.typecode == "H":
        return values
    if any(not isinstance(value, int) or not 0 <= value <= 65535 for value in values):
        raise ValueError(f"weight outside 0 to {QUANTISATION_SCALE} in a strategy or reach row")
    return array("H", values)


def _node_errors(node: SolverNode) -> list[str]:
    errors = []
    if node.actor_pos not in RULED_CONFIG["positions"]:
        errors.append(f"node {node.path} has actor {node.actor_pos}, outside the position list")
    if len(node.strategy_bp) != len(node.actions):
        errors.append(
            f"node {node.path} carries {len(node.strategy_bp)} strategy row(s)"
            f" for {len(node.actions)} action(s)"
        )
        return errors
    if len(node.reach_bp) != 169:
        errors.append(f"node {node.path} carries {len(node.reach_bp)} reach values, not 169")
    for row in node.strategy_bp:
        if len(row) != 169:
            errors.append(f"node {node.path} has a strategy row of {len(row)} classes, not 169")
            return errors
        if any(not 0 <= value <= QUANTISATION_SCALE for value in row):
            errors.append(f"node {node.path} carries a weight outside 0 to {QUANTISATION_SCALE}")
            return errors
    for index in range(169):
        total = sum(row[index] for row in node.strategy_bp)
        if total != QUANTISATION_SCALE:
            errors.append(
                f"node {node.path} class {index} sums to {total}, not {QUANTISATION_SCALE}"
            )
            return errors
    return errors


def _traversal_errors(by_path: dict[tuple[int, ...], SolverNode]) -> list[str]:
    """The walk closes: every node has a parent, and every continuing action has a child.

    A misread path encoding does not error, it silently returns a different node, and a
    dropped branch looks exactly like a tree that was always that shape.
    """
    errors = []
    for path, node in sorted(by_path.items()):
        if path and path[:-1] not in by_path:
            errors.append(f"node {path} has no parent node at {path[:-1]}")
            continue
        if path:
            parent = by_path[path[:-1]]
            if path[-1] >= len(parent.actions):
                errors.append(f"node {path} hangs off action {path[-1]}, which its parent lacks")
            elif parent.actions[path[-1]].terminal:
                errors.append(
                    f"node {path} hangs off {parent.actions[path[-1]].label!r},"
                    " a terminal action"
                )
        for index, action in enumerate(node.actions):
            if not action.terminal and (*path, index) not in by_path:
                errors.append(
                    f"node {path} action {action.label!r} continues but has no child node"
                )
    return errors


@dataclass(frozen=True)
class SolverExport:
    config: dict
    positions: tuple[str, ...]
    quantisation_scale: int
    nodes: tuple[SolverNode, ...]
    saved_solve: dict | None = None

    @classmethod
    def from_payload(cls, payload: dict) -> SolverExport:
        return cls.from_nodes(
            [_node_from_export(entry) for entry in payload["nodes"]],
            config=payload.get("config") or {},
            positions=payload.get("positions") or [],
            quantisation_scale=payload.get("quantisation_scale"),
            saved_solve=payload.get("saved_solve"),
        )

    @classmethod
    def from_nodes(
        cls,
        nodes: Sequence[SolverNode],
        config: dict,
        positions: Sequence[str],
        quantisation_scale: int | None = QUANTISATION_SCALE,
        saved_solve: dict | None = None,
    ) -> SolverExport:
        """Validate a tree and hold it, or say every way it is broken at once.

        The extractor builds nodes directly rather than through a payload dict, because a
        38,828-node tree round-tripped through lists of boxed integers is a gigabyte of
        pointers for data that fits in 59 MB.
        """
        errors = config_errors(config)
        if quantisation_scale != QUANTISATION_SCALE:
            errors.append(f"quantisation_scale is not {QUANTISATION_SCALE}")
        by_path: dict[tuple[int, ...], SolverNode] = {}
        for node in nodes:
            if node.path in by_path:
                errors.append(f"duplicate node at path {node.path}")
            by_path[node.path] = node
        for node in nodes:
            errors.extend(_node_errors(node))
        if not config.get("limp", True):
            for node in nodes:
                if any(action.kind == "limp" for action in node.actions):
                    errors.append(f"node {node.path} offers a limp in a no-limp tree")
        errors.extend(_traversal_errors(by_path))
        if errors:
            raise ValueError("; ".join(errors))
        return cls(
            config=dict(config),
            positions=tuple(positions),
            quantisation_scale=QUANTISATION_SCALE,
            nodes=tuple(nodes),
            saved_solve=saved_solve,
        )

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    def node(self, path: Iterable[int]) -> SolverNode:
        key = tuple(path)
        for node in self.nodes:
            if node.path == key:
                return node
        raise KeyError(f"no node at path {key}")

    def by_path(self) -> dict[tuple[int, ...], SolverNode]:
        return {node.path: node for node in self.nodes}

    def as_payload(self) -> dict:
        payload = {
            "export_schema_version": EXPORT_SCHEMA_VERSION,
            "config": dict(self.config),
            "positions": list(self.positions),
            "quantisation_scale": self.quantisation_scale,
            "nodes": [node.as_payload() for node in self.nodes],
        }
        if self.saved_solve is not None:
            payload["saved_solve"] = dict(self.saved_solve)
        return payload


def export_checksum(export: SolverExport) -> str:
    """A checksum over the data rather than over the container.

    Two files holding the same tree agree here whatever their framing, and one basis point
    moved between two actions does not.
    """
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "config": export.config,
                "positions": list(export.positions),
                "quantisation_scale": export.quantisation_scale,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    for node in export.nodes:
        digest.update(json.dumps(list(node.path), separators=(",", ":")).encode("utf-8"))
        digest.update(node.actor_pos.encode("utf-8"))
        for action in node.actions:
            digest.update(f"{action.label}|{action.kind}|{action.to}|{action.terminal}".encode())
        digest.update(_pack(node.reach_bp))
        for row in node.strategy_bp:
            digest.update(_pack(row))
    return digest.hexdigest()


def _pack(values: Sequence[int]) -> bytes:
    packed = values if isinstance(values, array) and values.typecode == "H" else array("H", values)
    if sys.byteorder != "little":
        packed = array("H", packed)
        packed.byteswap()
    return packed.tobytes()


def _unpack(raw: bytes) -> array:
    values = array("H")
    values.frombytes(raw)
    if sys.byteorder != "little":
        values.byteswap()
    return values


def write_solver_export(path: Path, export: SolverExport) -> None:
    """Write the export as a deterministic gzip container.

    Header JSON carries the config and one descriptor per node; the weights follow as raw
    little-endian `uint16`, which is what keeps a 38,828-node tree inside a byte limit a
    reviewer can defend. `mtime=0` is what makes two writes of the same tree byte-identical,
    and a container that stamps the clock makes every checksum a moving target.
    """
    header = {
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "config": export.config,
        "positions": list(export.positions),
        "quantisation_scale": export.quantisation_scale,
        "nodes": [
            {
                "path": list(node.path),
                "actor_pos": node.actor_pos,
                "actions": [action.as_payload() for action in node.actions],
            }
            for node in export.nodes
        ],
    }
    if export.saved_solve is not None:
        header["saved_solve"] = dict(export.saved_solve)
    body = bytearray()
    for node in export.nodes:
        body += _pack(node.reach_bp)
        for row in node.strategy_bp:
            body += _pack(row)
    blob = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        # filename="" keeps the member name out of the gzip header, which otherwise
        # records the file it was first written to and makes two identical trees differ.
        with gzip.GzipFile(filename="", fileobj=handle, mode="wb", mtime=0) as stream:
            stream.write(CONTAINER_MAGIC)
            stream.write(struct.pack("<Q", len(blob)))
            stream.write(blob)
            stream.write(bytes(body))


def load_solver_export(path: Path) -> SolverExport:
    raw = gzip.decompress(Path(path).read_bytes())
    if not raw.startswith(CONTAINER_MAGIC):
        raise ValueError(f"{path} is not a solver export container")
    offset = len(CONTAINER_MAGIC)
    (length,) = struct.unpack_from("<Q", raw, offset)
    offset += 8
    header = json.loads(raw[offset : offset + length].decode("utf-8"))
    offset += length
    for entry in header["nodes"]:
        count = len(entry["actions"])
        entry["reach_bp"] = _unpack(raw[offset : offset + 338])
        offset += 338
        rows = []
        for _ in range(count):
            rows.append(_unpack(raw[offset : offset + 338]))
            offset += 338
        entry["strategy_bp"] = rows
    return SolverExport.from_payload(header)
