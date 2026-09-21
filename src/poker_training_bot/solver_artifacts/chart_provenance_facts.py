"""What the committed chart's note measures, separated from how the note reads.

Split out of `chart_provenance` when decision 7's fifth census bucket took that module past the
500-line cap. The seam is the module's own argument: `chart_provenance` exists so the artifact's
prose is derived from the run that writes it, and this half is what makes that true while the
other half is what a human opens the chart to read. Nothing here formats anything.

Everything takes the path mapping rather than the export, because `SolverExport.by_path()` builds
a fresh dict per call and `chart_selection` caches its tree walk on that dict's identity, so a
mapping per sentence re-walks the whole tree per sentence.
"""

from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING

from poker_training_bot.solver_artifacts.chart_selection import (
    SEATS,
    cold_call_index,
    is_committed_node,
    require_known_kind,
)
from poker_training_bot.solver_artifacts.gtopen_export import class_combos, gtopen_class_index
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES

if TYPE_CHECKING:
    from poker_training_bot.solver_artifacts.gtopen_export import SolverNode

    _ByPath = dict[tuple[int, ...], SolverNode]

_PERCENT = 100.0
_AGGRESSIVE_KINDS = ("raise", "jam")


def _derivation() -> ModuleType:
    """`chart_derivation`, fetched at call time rather than imported at the top.

    That module imports this one, so a module-level import here would be a cycle; by the time
    anything asks for a note it is fully loaded. Fetched rather than restated: the readings the
    note shares with the chart are ruled, and a second copy is how the two come to disagree.
    """
    from poker_training_bot.solver_artifacts import chart_derivation

    return chart_derivation


def _committed(by_path: _ByPath) -> tuple[SolverNode, ...]:
    """Every node the chart commits, in export order.

    Takes the mapping rather than the export, and so does everything above and below it that
    can, up to the two public entry points. `SolverExport.by_path()` builds a FRESH dict on every
    call and `chart_selection` caches its tree walk on that dict's identity, so a mapping per
    sentence re-walks the whole tree per sentence. Threading `derive_chart`'s own mapping through
    leaves exactly one rebuild, inside `merged_cells`, which takes the export, and took the
    notes' share of `--check` from about 9 seconds to about 3.3 here. The seconds are
    machine-dependent; the one-rebuild count is not.
    """
    return tuple(node for node in by_path.values() if is_committed_node(by_path, node))


def _kind_at(by_path: _ByPath, path: tuple[int, ...], index: int) -> str:
    """What the seat to act at `path` did when it took its action `index`."""
    return require_known_kind(by_path[path], by_path[path].actions[index])


def _seats_live(by_path: _ByPath, node: SolverNode) -> int:
    """How many seats have not folded on the line into a node - the reading the multiway clause
    was deliberately written *not* to use. A seat count asks who could still enter the pot, the
    clause asks where the decision mass ends up, and the note states the gap between them.
    """
    folds = [d for d, i in enumerate(node.path) if _kind_at(by_path, node.path[:d], i) == "fold"]
    return len(SEATS) - len(folds)


def _faced_price(by_path: _ByPath, node: SolverNode) -> float:
    """The largest amount anybody has raised to on the line into a node."""
    raised = [
        float(by_path[node.path[:depth]].actions[index].to)
        for depth, index in enumerate(node.path)
        if _kind_at(by_path, node.path[:depth], index) in _AGGRESSIVE_KINDS
    ]
    return max(raised, default=0.0)


def _combo_weighted_fold_pct(node: SolverNode) -> float:
    """How much of hero's range folds at a node, weighted by combinations rather than by the
    plain mean over the 169 classes: the two disagree by four to five points at the spots this
    note quotes, and the one a reader checks against a published range is the weighted one.
    """
    folded = 0.0
    combos = 0.0
    for hand_class_text in HAND_CLASSES:
        column = gtopen_class_index(hand_class_text)
        weight = class_combos(hand_class_text)
        folded += weight * sum(
            node.strategy_bp[index][column]
            for index, action in enumerate(node.actions)
            if require_known_kind(node, action) == "fold"
        )
        combos += weight
    return folded / combos / 100.0


def _closes_into_a_multiway_flop(by_path: _ByPath, node: SolverNode) -> bool:
    """Whether a call the chart publishes here ends the betting into a three-or-more-way pot.

    Hero's cold call is skipped, the chart republishing it as a raise. "Closes" is the whole
    claim - a terminal, not a subtree that mostly ends multiway - so the child must be absent
    from the tree and three or more seats live when the call is made.
    """
    cold = cold_call_index(by_path, node)
    return _seats_live(by_path, node) >= 3 and any(
        require_known_kind(node, action) == "call"
        and index != cold
        and (*node.path, index) not in by_path
        for index, action in enumerate(node.actions)
    )


def _aggressive_prices(node: SolverNode) -> tuple[tuple[str, float], ...]:
    """Every price hero may put in at a node, as (kind, to), deduplicated and sorted."""
    offered = {
        (require_known_kind(node, action), float(action.to))
        for action in node.actions
        if require_known_kind(node, action) in _AGGRESSIVE_KINDS
    }
    return tuple(sorted(offered))


def _decision_shares(by_path: _ByPath) -> tuple[float, float]:
    """What share of the bot's preflop decisions the committed set carries, and what the rest
    do. Weighted by arrival - the chance the line gets played at all - not by node count, which
    is the other figure in the same sentence and a different reading of the same split.
    """
    node_arrival_ppb = _derivation().node_arrival_ppb
    total = 0.0
    committed = 0.0
    for node in by_path.values():
        arrival = node_arrival_ppb(by_path, node)
        total += arrival
        if is_committed_node(by_path, node):
            committed += arrival
    if total <= 0.0:
        return (0.0, 0.0)
    return (_PERCENT * committed / total, _PERCENT * (total - committed) / total)


