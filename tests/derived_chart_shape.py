"""Reading a solved node as the committed chart will key it: its line, its family, its cells.

**A support module, not a test module, and the split is a line cap and nothing more.**
`test_derived_chart.py` owns every assertion about the derived chart and `test_chart_conversion.py`
was already reaching seven of these names through it. MAINT-34 forced the split: decision 5's
untrained-cell refusal had to be asserted somewhere, and the owner was at the 700-line cap with no
headroom. The ruling was to split rather than compress a phase's reasoning to make room.

**It is still not an import of the conversion on trial.** Every definition here is written out
rather than taken from `chart_derivation`, because a walk that imports the converter it checks is
the converter agreeing with itself. Both files reach these through `test_derived_chart`, which
re-exports them and owns which are part of the phase's vocabulary.
"""

from __future__ import annotations

from poker_training_bot.solver_artifacts.gtopen_export import (
    SolverNode,
    gtopen_class_index,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, hand_class_grid_index
from poker_training_bot.solver_artifacts.schema import PreflopAction, PreflopArtifact, spot_key

TABLE_SIZE = 6
STACK_DEPTH_BB = 100

# `first-in` is the pot folded to hero, `bb-open` the big blind facing an open, `merged` the
# eleven other seats facing an open, `three-bet` the spots facing a three-bet. Recomputed by the
# walk below rather than read off the artifact: a family read from the file under test is the
# file agreeing with itself.
FIRST_IN, BB_OPEN, MERGED, THREE_BET = "first-in", "bb-open", "merged", "three-bet"


def action_sequence_of(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> tuple[PreflopAction, ...]:
    """What hero faces at a node: the live actions in front of him, in order.

    The actor of a recorded action is whoever was to act at the node the action was taken
    *at*, which is the parent of the node it leads to. Reading it off the child shifts every
    entry one seat round the ring - the lojack's open becomes the hijack's - and the result
    keys a spot that never happened while validating perfectly. Folds never enter: an empty
    sequence means the pot was folded to hero, and a recorded fold would be a second
    spelling of the same spot that keys apart from the first.
    """
    entries: list[PreflopAction] = []
    for depth, index in enumerate(node.path):
        parent = by_path[node.path[:depth]]
        action = parent.actions[index]
        if action.kind == "fold":
            continue
        if action.kind == "call":
            entries.append(PreflopAction(parent.actor_pos, "call"))
        else:
            entries.append(PreflopAction(parent.actor_pos, "raise", float(action.to)))
    return tuple(entries)


def key_of(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> str:
    """The spot key a node derives, in the one vocabulary this repo names spots with."""
    return spot_key(TABLE_SIZE, STACK_DEPTH_BB, node.actor_pos, action_sequence_of(by_path, node))


def raises_faced_of(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> int:
    """How many raises are already in when hero is asked."""
    return sum(1 for entry in action_sequence_of(by_path, node) if entry.action == "raise")


def family_of(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> str:
    """Which of decision 45's four families a committed node belongs to."""
    faced = raises_faced_of(by_path, node)
    if faced == 0:
        return FIRST_IN
    if faced == 1:
        return BB_OPEN if node.actor_pos == "BB" else MERGED
    return THREE_BET


def arriving_classes(node: SolverNode) -> list[str]:
    """The classes hero can be holding here, in the grid order the artifact writes."""
    return [
        name
        for name in sorted(HAND_CLASSES, key=hand_class_grid_index)
        if node.reach_bp[gtopen_class_index(name)] > 0
    ]


def solve_weights(node: SolverNode, hand_class_text: str) -> dict[str, int]:
    """One cell as the solve holds it, in basis points, keyed by the artifact's action names
    with a jam counted as a raise. Read off the node so the merge below compares the
    published number against the source rather than against another published number."""
    column = gtopen_class_index(hand_class_text)
    totals = {"fold": 0, "call": 0, "raise": 0}
    for index, action in enumerate(node.actions):
        recorded = "raise" if action.kind in ("raise", "jam") else action.kind
        totals[recorded] = totals.get(recorded, 0) + node.strategy_bp[index][column]
    return totals


def weights_by_class(artifact: PreflopArtifact, spot_id: str) -> dict[str, dict[str, float]]:
    for keyed, classes in artifact.action_weights:
        if keyed == spot_id:
            return {name: dict(weights) for name, weights in classes}
    raise AssertionError(f"the committed artifact declares no spot {spot_id!r}")


def reach_by_class(artifact: PreflopArtifact, spot_id: str) -> dict[str, int]:
    for keyed, classes in artifact.arriving_reach_bp:
        if keyed == spot_id:
            return dict(classes)
    raise AssertionError(f"the committed artifact carries no arriving reach for {spot_id!r}")


RANKS = "AKQJT98765432"
"""High card first, so an index into it falls as the card gets weaker."""


def a_full_grid(value) -> dict[str, float]:
    """All 169 classes with `value(name)` in each. A partial grid silently drops the comparisons
    whose other half is missing and reports a clean measurement.

    Here rather than beside its callers because MAINT-34's decision 7 took the validators file
    past its 700-line cap. The assertions stay with their owner; only the grid builders moved.
    """
    return {name: value(name) for name in HAND_CLASSES}


def monotone(name: str) -> float:
    """A frequency falling with the high card and with the kicker, a tenth of a point higher
    suited than offsuit - so all three play-not-fold relations hold with room to spare and any
    violation a case counts is the one that case put there."""
    high, low = RANKS.index(name[0]), RANKS.index(name[1])
    return 100.0 - 3.0 * high - 0.2 * low + (0.1 if name.endswith("s") else 0.0)

