"""The synthetic export payloads that exercise `SolverExport.from_payload`'s validator.

Extracted from `tests/test_solver_export.py` on 2026-09-17, the eighth cap-forced extraction
in this repo and the second in MAINT-34. That file reached 716 lines of a 700 cap when the
missing convergence check was added back, and `AGENTS.md` forbids compressing pre-existing
reasoning to make room. The builders and the ten deliberate breakages are the honest seam:
they are fixtures rather than assertions, they name no measurement, and nothing here changes
when a solve does. The assertions that read them stay in the file that owns them.

Real strategies vary by hand class. Everything built here gives every class the same mix,
trading poker realism for a node that fits on one line, because the validator these exist to
exercise reads shape rather than poker.
"""

from __future__ import annotations

from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG
from poker_training_bot.solver_artifacts.gtopen_export import (
    QUANTISATION_SCALE,
    gtopen_class_index,
)

POSITIONS = ["LJ", "HJ", "CO", "BTN", "SB", "BB"]

FOLD = {"label": "Fold", "kind": "fold", "to": 0.0, "terminal": True}
OPEN = {"label": "Raise 2.5", "kind": "raise", "to": 2.5, "terminal": False}
JAM = {"label": "All-in 100", "kind": "jam", "to": 100.0, "terminal": True}
CALL = {"label": "Call 2.5", "kind": "call", "to": 2.5, "terminal": True}
LIMP = {"label": "Limp 1.0", "kind": "limp", "to": 1.0, "terminal": False}


def uniform_node(path: tuple[int, ...], actor: str, actions: list[dict], split: tuple[int, ...]):
    """A node whose every hand class plays the same mix."""
    return {
        "path": list(path),
        "actor_pos": actor,
        "actions": actions,
        "strategy_bp": [[weight] * 169 for weight in split],
        "reach_bp": [QUANTISATION_SCALE] * 169,
    }


def minimal_payload(**overrides) -> dict:
    """The smallest export the validator should accept: a root and one child."""
    payload = {
        "export_schema_version": 1,
        "config": dict(RULED_CONFIG),
        "positions": list(POSITIONS),
        "quantisation_scale": QUANTISATION_SCALE,
        "nodes": [
            uniform_node((), "LJ", [FOLD, OPEN, JAM], (8000, 2000, 0)),
            uniform_node((1,), "HJ", [FOLD, CALL, JAM], (7000, 3000, 0)),
        ],
    }
    payload.update(overrides)
    return payload


def _unbalanced(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"][0][gtopen_class_index("AA")] = 7999


def _missing_row(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"].pop()


def _negative_weight(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"][0][0] = -1


def _oversized_weight(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"][0][0] = QUANTISATION_SCALE + 1


def _no_child(payload: dict) -> None:
    payload["nodes"] = payload["nodes"][:1]


def _child_of_a_terminal(payload: dict) -> None:
    payload["nodes"].append(uniform_node((0,), "HJ", [FOLD, CALL], (5000, 5000)))


def _orphan(payload: dict) -> None:
    payload["nodes"].append(uniform_node((1, 1, 1), "CO", [FOLD, CALL], (5000, 5000)))


def _duplicate_path(payload: dict) -> None:
    payload["nodes"].append(uniform_node((1,), "HJ", [FOLD, CALL, JAM], (1, 9999, 0)))


def _unknown_actor(payload: dict) -> None:
    payload["nodes"][0]["actor_pos"] = "UTG"


def _carries_a_limp(payload: dict) -> None:
    payload["nodes"][0]["actions"] = [FOLD, LIMP, OPEN]
    payload["nodes"][0]["strategy_bp"] = [[8000] * 169, [1000] * 169, [1000] * 169]


BROKEN_EXPORTS = [
    # a class whose action weights no longer form a distribution
    ("unbalanced-class", _unbalanced, "10000"),
    # a strategy with fewer rows than the node has actions
    ("missing-row", _missing_row, "row"),
    ("negative-weight", _negative_weight, "weight"),
    ("oversized-weight", _oversized_weight, "weight"),
    # the traversal must close: a branch silently dropped is the failure that matters
    ("non-terminal-with-no-child", _no_child, "child"),
    ("child-hanging-off-a-terminal", _child_of_a_terminal, "terminal"),
    ("node-whose-parent-is-absent", _orphan, "parent"),
    ("two-nodes-at-one-path", _duplicate_path, "duplicate"),
    ("actor-outside-the-vocabulary", _unknown_actor, "UTG"),
    # ruling 1 read backwards: this is what fails if the wrong config produced the file
    ("limp-in-a-no-limp-tree", _carries_a_limp, "limp"),
]
