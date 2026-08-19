"""The human review surface for the committed solver export.

This phase's closing act is a judgement no check performs: a person loads the saved solve
in GTOpen's own interface and reads range grids against this report. Both sides come from
the same solved arena, so a disagreement is this repo's tree walk, hand-class mapping,
reach handling, quantisation, storage or rendering - which is exactly where a defect would
live and where nothing automated in this phase can reach.

The report is capped like every other report, so it cannot hold 38,828 nodes. Decision 11
fixes the selection: the five opening spots and the five big-blind-versus-open spots the
reference file names, plus one four-bet line, which is the part of the tree no reference
covers and no v1 spot key reaches. What is omitted is counted rather than left implicit.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from poker_training_bot.solver_artifacts.gtopen_expectations import (
    OPENING_ORDER_EXCLUSIONS,
    Aggregates,
    Expectations,
    defence_node,
    opening_node,
    reference_rows,
)
from poker_training_bot.solver_artifacts.gtopen_export import (
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    export_checksum,
    gtopen_class_index,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = REPO_ROOT / "reports" / "active" / "latest_solver_export_report.txt"

COMPARISON_LABELS: tuple[str, ...] = ("gated", "reported")
"""Every number printed here says which of these it is.

`gated` means a named check in `check_solver_export_expectations` fails if it moves out of
relation. `reported` means no threshold covers it at all. A reader must be able to tell
them apart, or a green gate reads as though it vouched for the whole table.
"""

POSITIONS = ("LJ", "HJ", "CO", "BTN", "SB")
GRID_RANKS = "AKQJT98765432"


def four_bet_node(export: SolverExport) -> tuple[str, SolverNode | None]:
    """LJ opens, HJ three-bets, LJ four-bets, HJ to act.

    Chosen by label rather than by counting raises: GTOpen names its own raise levels, and
    the contract's "fourth raise counting the open as the first" and the solver's "4-bet"
    are the same node under two readings.
    """
    node = opening_node(export, "LJ")
    for needle in ("Raise 2.5", "3-bet", "4-bet"):
        if node is None:
            return "HJ vs LJ 4-bet", None
        index = next(
            (i for i, action in enumerate(node.actions) if needle in action.label), None
        )
        if index is None:
            return "HJ vs LJ 4-bet", None
        child = export.by_path().get((*node.path, index))
        node = child
    return "HJ vs LJ 4-bet", node


def selected_spots(export: SolverExport) -> list[tuple[str, SolverNode | None]]:
    spots: list[tuple[str, SolverNode | None]] = [
        (f"RFI {position}", opening_node(export, position)) for position in POSITIONS
    ]
    spots += [(f"BB vs {position}", defence_node(export, position)) for position in POSITIONS]
    spots.append(four_bet_node(export))
    return spots


def _grid(values_by_class: dict[str, int]) -> list[str]:
    """A 13x13 rank grid, pairs on the diagonal, suited above it, offsuit below."""
    lines = ["     " + "".join(f"{rank:>4}" for rank in GRID_RANKS)]
    for row, high in enumerate(GRID_RANKS):
        cells = []
        for column, low in enumerate(GRID_RANKS):
            if row == column:
                name = f"{high}{high}"
            elif row < column:
                name = f"{high}{low}s"
            else:
                name = f"{low}{high}o"
            cells.append(f"{values_by_class[name]:>4}")
        lines.append(f"{high:>4} " + "".join(cells))
    return lines


def _percent_grid(node: SolverNode, action_index: int) -> list[str]:
    values = {
        name: round(
            100 * node.strategy_bp[action_index][gtopen_class_index(name)] / QUANTISATION_SCALE
        )
        for name in HAND_CLASSES
    }
    return _grid(values)


def _reach_grid(node: SolverNode) -> list[str]:
    values = {
        name: round(100 * node.reach_bp[gtopen_class_index(name)] / QUANTISATION_SCALE)
        for name in HAND_CLASSES
    }
    return _grid(values)


def _spot_section(label: str, node: SolverNode | None) -> list[str]:
    lines = ["", f"--- {label} ---"]
    if node is None:
        lines.append("  not present in this export")
        return lines
    lines.append(f"  path {list(node.path)}  ·  {node.actor_pos} to act")
    lines.append(
        "  frequencies: " + ", ".join(
            f"{action.label} {100 * node.action_frequency(index):.2f}%"
            for index, action in enumerate(node.actions)
        )
    )
    lines.append("")
    lines.append("  arriving range, percent of each class that reaches this node")
    lines += ["  " + line for line in _reach_grid(node)]
    for index, action in enumerate(node.actions):
        if action.kind == "fold":
            continue
        lines.append("")
        lines.append(f"  {action.label}, percent of each class taking it")
        lines += ["  " + line for line in _percent_grid(node, index)]
    return lines


def _own_numbers(measured: Aggregates) -> list[str]:
    """This solve's aggregates, each said to be gated or not gated."""
    lines = [
        "",
        "This solve's aggregates, and what checks them",
        "-" * 46,
        "  gated    a named check in check_solver_export_expectations fails if this",
        "           moves out of relation with the others",
        "  reported no threshold covers this number at all",
        "",
        f"  {'number':<14}{'this solve':>12}   label",
    ]
    for position in POSITIONS:
        label = "reported" if position in OPENING_ORDER_EXCLUSIONS else "gated"
        value = measured.opening_pct.get(position)
        shown = "-" if value is None else f"{value:.2f}"
        lines.append(f"  {'RFI ' + position:<14}{shown:>12}   {label}")
    for position in POSITIONS:
        value = measured.defence_pct.get(position)
        shown = "-" if value is None else f"{value:.2f}"
        lines.append(f"  {'BB vs ' + position:<14}{shown:>12}   gated")
    limp = measured.limp_pct.get("SB")
    lines.append(f"  {'SB limp':<14}{'-' if limp is None else f'{limp:.2f}':>12}   reported")
    lines.append("")
    lines.append("  The opening order is gated among LJ, HJ, CO and BTN only, and the small")
    lines.append("  blind is out of it by name:")
    lines += textwrap.wrap(
        OPENING_ORDER_EXCLUSIONS["SB"], width=76, initial_indent="    ", subsequent_indent="    "
    )
    lines.append("  Big-blind defence is gated as a relation rather than a fixed order, so it")
    lines.append("  covers the small blind wherever this solve puts it.")
    return lines


def _reference_table(measured: Aggregates, expectations: Expectations) -> list[str]:
    lines = [
        "",
        "The GTO Wizard NL25 reference, for a reader to compare by eye",
        "-" * 60,
        "  Nothing below is checked. That file is a raked six-max NL25 solution with limps",
        "  in the tree, and this solve is rake-free without them, so a threshold over the",
        "  gap would be grading one product against another rather than measuring this",
        "  extraction. It is still the only set of numbers in this repo that this repo did",
        "  not produce, which is why it is printed rather than deleted.",
        "",
        f"  {'number':<14}{'this solve':>12}{'reference':>12}{'difference':>12}   label",
    ]
    for row in reference_rows(measured, expectations):
        if row.measured is None or row.reference is None:
            lines.append(f"  {row.name:<14}{'-':>12}{'-':>12}{'-':>12}   {row.label}")
            continue
        lines.append(
            f"  {row.name:<14}{row.measured:>12.2f}{row.reference:>12.2f}"
            f"{row.measured - row.reference:>+12.2f}   {row.label}"
        )
    return lines


def render_solver_export_report(
    export: SolverExport, measured: Aggregates, expectations: Expectations
) -> str:
    """The whole report, as text a person reads beside GTOpen's own interface."""
    spots = selected_spots(export)
    shown = sum(1 for _, node in spots if node is not None)
    saved = export.saved_solve or {}
    lines = [
        "Solver export report",
        "=" * 60,
        "",
        "One solved six-handed 100bb preflop tree, captured from GTOpen and committed as",
        "data. Nothing downstream reads it yet: the bot still plays the committed 36-spot",
        "chart. This report exists so a person can say whether the extraction is faithful.",
        "",
        "How to check it: load the saved solve named below in GTOpen's own interface and",
        "read its range grids against the grids here. Do not press BUILD or RE-SOLVE after",
        "loading - the web form has no control for allin_threshold and re-posting it",
        "silently reverts the tree from the ruled 0.67 to the server default of 0.85.",
        "",
        f"  saved solve      {saved.get('path', 'not recorded in this export')}",
        f"  saved solve sha  {saved.get('sha256', '-')}",
        f"  export sha256    {export_checksum(export)}",
        f"  action nodes     {export.node_count}",
        "",
        "  config posted to the solver:",
    ]
    for key in sorted(export.config):
        lines.append(f"    {key}: {export.config[key]}")
    lines += _own_numbers(measured)
    lines += _reference_table(measured, expectations)
    lines += [
        "",
        "Range grids",
        "-" * 60,
        "  Rows and columns run A down to 2. Pairs sit on the diagonal, suited classes",
        "  above it, offsuit classes below it. Every cell is a whole percent.",
        f"  spots shown: {shown} of {export.node_count} action nodes,"
        f" omitted: {export.node_count - shown} spots",
        "  The selection is decision 11 and is fixed rather than emergent: the five opening",
        "  spots and the five big-blind-versus-open spots the reference file names, plus one",
        "  four-bet line, which no reference covers and no v1 spot key reaches.",
    ]
    for label, node in spots:
        lines += _spot_section(label, node)
    lines.append("")
    return "\n".join(lines) + "\n"
