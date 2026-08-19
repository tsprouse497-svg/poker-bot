"""What the committed export is checked against, which is itself.

Nothing here grades this solve's poker against another solver. GTO Wizard is a different
program solving a different game - raked, with limps - so a threshold over the gap between
them measures the difference between two products rather than anything about this
extraction. Ruled by Taylor on 2026-08-18, after running the solver himself.

Two checks remain and both are internal. Later position opens wider is a property of the
game, and big-blind defence tracking the opening order is a relation the export must
satisfy against itself: it holds at any rake basis, for any solver, at any stack depth, and
it still breaks the moment a hand index is transposed, an actor is mis-assigned or a
strategy row goes unnormalised.

`six_max_nl25_100bb.json` is still read. Its eleven numbers are printed beside this solve's
own so a reader can compare them by eye, and nothing gates on them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from poker_training_bot.solver_artifacts.gtopen_export import SolverExport, SolverNode

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTATIONS_PATH = (
    REPO_ROOT / "data" / "artifacts" / "preflop" / "expectations" / "six_max_nl25_100bb.json"
)

OPENING_ORDER: tuple[str, ...] = ("LJ", "HJ", "CO", "BTN")
"""Decision 4: the positions whose opening frequencies must ascend, exactly."""

OPENING_ORDER_EXCLUSIONS: dict[str, str] = {
    "SB": (
        "The small blind acts with only one opponent left, which argues for the widest range"
        " of any position, and it pays the worst postflop position for the rest of the hand,"
        " which argues for the tightest. Which of those wins is decided by rake: raked"
        " references put the button widest, and this rake-free solve puts the small blind"
        " widest, because twelve points of limping became raising. Its place in the opening"
        " order is therefore not structural. Its frequency is reported and gated by nothing."
    )
}

OPENING_KINDS = frozenset({"raise", "jam"})
"""An open is a raise, and a limp is not one. The reference file reports the small blind's
raising and limping separately, so this definition is the one that is comparable to it."""


@dataclass(frozen=True)
class Aggregates:
    """The eleven numbers, computed from the export on every gate run rather than recalled."""

    opening_pct: dict[str, float] = field(default_factory=dict)
    defence_pct: dict[str, float] = field(default_factory=dict)
    limp_pct: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Expectations:
    """The GTO Wizard NL25 reference, read for printing rather than for judging."""

    opening_pct: dict[str, float]
    defence_pct: dict[str, float]
    limp_pct: dict[str, float]


@dataclass(frozen=True)
class ReferenceRow:
    name: str
    measured: float | None
    reference: float | None
    label: str


def load_expectations(path: Path = EXPECTATIONS_PATH) -> Expectations:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Expectations(
        opening_pct=dict(raw["open_frequency_pct"]),
        defence_pct=dict(raw["big_blind_defence_pct"]),
        limp_pct=dict(raw["limp_frequency_pct"]),
    )


def _action_index(node: SolverNode, kind: str, to: float | None = None) -> int | None:
    for index, action in enumerate(node.actions):
        if action.kind == kind and (to is None or abs(action.to - to) < 1e-9):
            return index
    return None


def opening_node(export: SolverExport, position: str) -> SolverNode | None:
    """The node where a position acts first, everyone before it having folded.

    Walked rather than hardcoded as a path, so it survives an action list in a different
    order. The ruled tree offers no limp, so "no prior raise and no prior limp" is just
    "everyone folded".
    """
    by_path = export.by_path()
    path: tuple[int, ...] = ()
    while path in by_path:
        node = by_path[path]
        if node.actor_pos == position:
            return node
        fold = _action_index(node, "fold")
        if fold is None:
            return None
        path = (*path, fold)
    return None


def defence_node(export: SolverExport, opener: str) -> SolverNode | None:
    """The big blind's node after `opener` opens to 2.5 and everyone between folds."""
    by_path = export.by_path()
    start = opening_node(export, opener)
    if start is None:
        return None
    open_index = _action_index(start, "raise", 2.5)
    if open_index is None:
        return None
    path = (*start.path, open_index)
    while path in by_path:
        node = by_path[path]
        if node.actor_pos == "BB":
            return node
        fold = _action_index(node, "fold")
        if fold is None:
            return None
        path = (*path, fold)
    return None


def _sum_frequency(node: SolverNode, kinds) -> float:
    return sum(
        node.action_frequency(index)
        for index, action in enumerate(node.actions)
        if action.kind in kinds
    )


def aggregate_frequencies(export: SolverExport) -> Aggregates:
    """Decision 7's definitions, recomputed from the committed export.

    Opening frequency counts every raise and jam at the first-in node and excludes a limp.
    Big-blind defence is the complement of folding, so calls, raises and jams all count.
    Every one is combo-weighted and weighted by the arriving range, which is what makes
    them the same numbers GTOpen reports for itself.
    """
    opening: dict[str, float] = {}
    defence: dict[str, float] = {}
    limps: dict[str, float] = {}
    for position in (*OPENING_ORDER, *OPENING_ORDER_EXCLUSIONS):
        node = opening_node(export, position)
        if node is not None:
            opening[position] = 100.0 * _sum_frequency(node, OPENING_KINDS)
            limps[position] = 100.0 * _sum_frequency(node, {"limp"})
        against = defence_node(export, position)
        if against is not None:
            defence[position] = 100.0 * (1.0 - _sum_frequency(against, {"fold"}))
    return Aggregates(opening_pct=opening, defence_pct=defence, limp_pct=limps)


def ordering_errors(aggregates: Aggregates) -> list[str]:
    """The two checks that gate, both internal to the export.

    The opening order is a fixed ascent among the four positions whose place in it is
    structural. The defence relation is not a fixed order: against whichever position opens
    wider, the big blind must defend more. The small blind sits outside the opening order by
    name, so nothing is asserted about where it lands - but wherever it lands above the
    others, the consequence still has to hold, which is what keeps the widest-ranged
    position from being covered by nothing at all.
    """
    opening, defence = aggregates.opening_pct, aggregates.defence_pct
    covered = (*OPENING_ORDER, *OPENING_ORDER_EXCLUSIONS)
    missing = [
        f"no opening frequency for {position}"
        for position in covered
        if position not in opening
    ] + [
        f"no big-blind defence frequency for {position}"
        for position in covered
        if position not in defence
    ]
    if missing:
        return missing

    errors: list[str] = []
    for tighter, wider in zip(OPENING_ORDER, OPENING_ORDER[1:], strict=False):
        if not opening[wider] > opening[tighter]:
            errors.append(
                f"{wider} opens {opening[wider]:.2f} percent and {tighter} opens"
                f" {opening[tighter]:.2f}: later position must open wider"
            )
    for wider in covered:
        for tighter in OPENING_ORDER:
            if wider == tighter or not opening[wider] > opening[tighter]:
                continue
            if not defence[wider] > defence[tighter]:
                errors.append(
                    f"{wider} opens wider than {tighter} ({opening[wider]:.2f} against"
                    f" {opening[tighter]:.2f}) but the big blind defends"
                    f" {defence[wider]:.2f} against {wider} and {defence[tighter]:.2f}"
                    f" against {tighter}"
                )
    return errors


def reference_rows(measured: Aggregates, expectations: Expectations) -> list[ReferenceRow]:
    """The eleven aggregates beside the reference's, every one labelled gated by nothing.

    A reader comparing them by eye is the point. A threshold over them would be grading one
    product against another, which is what the 2026-08-18 re-ruling removed.
    """
    rows: list[ReferenceRow] = []
    for position in ("LJ", "HJ", "CO", "BTN", "SB"):
        rows.append(
            ReferenceRow(
                f"RFI {position}",
                measured.opening_pct.get(position),
                expectations.opening_pct.get(position),
                "reported",
            )
        )
    for position in ("LJ", "HJ", "CO", "BTN", "SB"):
        rows.append(
            ReferenceRow(
                f"BB vs {position}",
                measured.defence_pct.get(position),
                expectations.defence_pct.get(position),
                "reported",
            )
        )
    rows.append(
        ReferenceRow(
            "SB limp",
            measured.limp_pct.get("SB", 0.0),
            expectations.limp_pct.get("SB"),
            "reported",
        )
    )
    return rows
