"""The committed export's source card: the numbers a gate can never recompute.

An export's origin is checkable or it is asserted. Nothing in this repo can re-run a solve
- the gate has to pass on a machine with no GTOpen, no Rust toolchain and no network - so
the determinism result, the wall clock and the achieved exploitability arrive as structured
fields on a card rather than as numbers a check derives. What a check can insist on is that
they are present and that they say something, which is what stops them decaying into prose
nobody reads. That is the drift defect Phase 09 exists to have closed.

The card also carries the two claims a reader most needs and would otherwise never see: that
GTOpen ships no LICENSE file upstream, and that its preflop engine resolves flops by scaled
equity share rather than by playing them.
"""

from __future__ import annotations

import json
from pathlib import Path

from poker_training_bot.solver_artifacts.gtopen_config import config_errors


def load_source_card(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


_PLACEHOLDERS = {"", "tbd", "todo", "unknown", "n/a", "none", "-"}
_REQUIRED_BLOCKS: dict[str, tuple[str, ...]] = {
    "solve": (
        "target_gap_bb",
        "achieved_gap_bb",
        "iterations",
        "iteration_cap",
        "wall_clock_seconds",
    ),
    "determinism": ("result", "method", "max_divergence_bp"),
    "walk": ("reresolved_nodes", "mismatches"),
    "node_counts": ("exported", "solver_action_nodes", "reconciliation"),
    "conditioning": ("payload", "discriminator"),
    "size": (
        "bytes",
        "limit_bytes",
        "headroom_bytes",
        "bytes_per_node",
        "bytes_per_expressible_spot",
    ),
    "saved_solve": ("path", "bytes", "sha256"),
}
_REQUIRED_TEXT = ("licence", "model")
_MUST_BE_POSITIVE = {
    ("solve", "wall_clock_seconds"),
    ("solve", "iterations"),
    ("size", "bytes"),
    ("size", "bytes_per_node"),
    ("size", "bytes_per_expressible_spot"),
    ("saved_solve", "bytes"),
}


def _is_placeholder(value) -> bool:
    if value is None:
        return True
    return isinstance(value, str) and value.strip().lower() in _PLACEHOLDERS


def source_card_errors(card: dict) -> list[str]:
    """The numbers the gate can never recompute, checked for being answers at all.

    Determinism and wall clock cannot be recomputed inside a gate that has no solver, so
    the only thing a check can insist on is that the fields are present and say something.
    A field left at a placeholder is the drift defect Phase 09 exists to have closed.
    """
    errors: list[str] = []
    for name in _REQUIRED_TEXT:
        if _is_placeholder(card.get(name)):
            errors.append(f"{name} is missing or left at a placeholder")
    licence = str(card.get("licence") or "")
    if "no license file" not in licence.lower():
        errors.append("licence does not state that GTOpen ships no LICENSE file upstream")
    if "realization" not in str(card.get("model") or ""):
        errors.append("model does not name the realization setting the solve ran under")
    for block, keys in _REQUIRED_BLOCKS.items():
        values = card.get(block)
        if not isinstance(values, dict):
            errors.append(f"{block} block is missing")
            continue
        for key in keys:
            if key not in values:
                errors.append(f"{block}.{key} is missing")
            elif _is_placeholder(values[key]) and (block, key) != ("node_counts", "reconciliation"):
                errors.append(f"{block}.{key} is missing or left at a placeholder")
            elif (block, key) in _MUST_BE_POSITIVE and not values[key] > 0:
                errors.append(f"{block}.{key} is {values[key]}, which is a placeholder")
    if _is_placeholder(card.get("export_sha256")):
        errors.append("export_sha256 is missing or left at a placeholder")
    if isinstance(card.get("config_posted"), dict):
        errors.extend(config_errors(card["config_posted"]))
    else:
        errors.append("config_posted is missing")
    counts = card.get("node_counts")
    if isinstance(counts, dict) and counts.get("exported") != counts.get("solver_action_nodes"):
        if not str(counts.get("reconciliation") or "").strip():
            errors.append("node_counts disagree and carry no reconciliation")
    walk = card.get("walk")
    if isinstance(walk, dict) and walk.get("mismatches"):
        errors.append(f"walk reports {walk['mismatches']} path mismatch(es)")
    return errors
