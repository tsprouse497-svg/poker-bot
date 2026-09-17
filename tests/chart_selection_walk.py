"""The walk of a solver export that `test_chart_derivation.py` states the selection rule over.

**A support module, not a test module, and the split is a line cap and nothing more.** The four
clauses, the counts they select and every assertion about them stay in `test_chart_derivation.py`,
which owns them; this file is the machinery those assertions are written on. MAINT-34 forced the
split: decision 2 adds a fourth clause to a file that was already at the 700-line cap with no
headroom, and the ruling was to split rather than to compress a phase's reasoning to make room.

**It is still not an import of the rule under test.** Every definition here is written out rather
than taken from `poker_training_bot.solver_artifacts.chart_selection`, because a test that imports
the rule it checks is one copy of a rule agreeing with another. `test_chart_derivation.py` asserts
node by node that the shipped rule and this walk pick the same set, and that assertion is the
whole point of keeping two.

Siblings reach these through `test_chart_derivation` rather than from here, because that module
re-exports them and owns which of them are part of the phase's vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass

from poker_training_bot.solver_artifacts.gtopen_export import SolverExport, SolverNode
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key

TABLE_SIZE = 6
DEPTH_BB = 100
SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")

COMMITTED_RAISE_DEPTH = 2
"""At most two raises already in. Three is the four-bet family, which a later phase takes up."""

EXPOSURE_THRESHOLD_PCT = 10.0
"""Decision 46's line, in points of a node's decision mass reaching a multiway flop."""

SPLIT_CLOSURE_TOLERANCE_PCT = 0.05
"""How far a terminal split may miss 100 before clause two has not measured anything.

The same tolerance `SPLIT_LEAK_PCT` in `test_chart_derivation.py` has carried since phase 14,
which is the point: it was frozen as the line a build losing a whole branch could not hide
inside, it caught exactly that, and MAINT-34's decision 7 turned it from a tripwire into the
clause. One number for one question."""


@dataclass(frozen=True)
class Walk:
    """Everything this file measures, taken once over the export."""

    by_path: dict[tuple[int, ...], SolverNode]
    folded: dict[tuple[int, ...], frozenset[str]]
    invested: dict[tuple[int, ...], frozenset[str]]
    sequence: dict[tuple[int, ...], tuple[PreflopAction, ...]]
    frequency: dict[tuple[int, ...], tuple[float, ...]]
    below: dict[tuple[int, ...], tuple[float, float, float]]
    arrival: dict[tuple[int, ...], float]


_WALKS: dict[int, tuple[SolverExport, Walk]] = {}


def _outcome(by_path, folded, below, node: SolverNode, index: int) -> tuple[float, float, float]:
    """Where one branch ends up: hand over preflop, heads-up flop, multiway flop.

    A branch with a child carries the child's own split. A branch without one is a terminal, and
    what it is a terminal *of* is read off the seats still live after it: one seat means
    everybody folded, two a heads-up flop, three or more a multiway flop. That last is the
    quantity the calibrated fit has no cell for, and it is a property of the leaf rather than of
    the node, which is why it is walked to instead of inferred at the top.
    """
    child = (*node.path, index)
    if child in by_path:
        return below[child]
    live = len(SEATS) - len(folded[node.path])
    if node.actions[index].kind == "fold":
        live -= 1
    return (float(live == 1), float(live == 2), float(live >= 3))


def _build_walk(export: SolverExport) -> Walk:
    by_path = export.by_path()
    folded = {(): frozenset()}
    invested = {(): frozenset()}
    sequence: dict[tuple[int, ...], tuple[PreflopAction, ...]] = {(): ()}
    for path in sorted(by_path, key=len):
        node = by_path[path]
        for index, action in enumerate(node.actions):
            child = (*path, index)
            if child not in by_path:
                continue
            if action.kind == "fold":
                folded[child] = folded[path] | {node.actor_pos}
                invested[child] = invested[path]
                sequence[child] = sequence[path]
            elif action.kind in ("call", "raise", "jam"):
                entry = (
                    PreflopAction(node.actor_pos, "call")
                    if action.kind == "call"
                    else PreflopAction(node.actor_pos, "raise", float(action.to))
                )
                folded[child] = folded[path]
                invested[child] = invested[path] | {node.actor_pos}
                sequence[child] = (*sequence[path], entry)
            else:
                raise AssertionError(f"node {path} offers an unhandled kind {action.kind!r}")
    frequency = {
        node.path: tuple(node.action_frequency(index) for index in range(len(node.actions)))
        for node in export.nodes
    }
    below: dict[tuple[int, ...], tuple[float, float, float]] = {}
    for path in sorted(by_path, key=len, reverse=True):
        node = by_path[path]
        totals = [0.0, 0.0, 0.0]
        for index in range(len(node.actions)):
            share = frequency[path][index]
            if not share:
                continue
            outcome = _outcome(by_path, folded, below, node, index)
            for slot in range(3):
                totals[slot] += share * outcome[slot]
        below[path] = (totals[0], totals[1], totals[2])
    arrival = {(): 1.0}
    for path in sorted(by_path, key=len):
        for index in range(len(by_path[path].actions)):
            child = (*path, index)
            if child in by_path:
                arrival[child] = arrival[path] * frequency[path][index]
    return Walk(by_path, folded, invested, sequence, frequency, below, arrival)


def walk_of(export: SolverExport) -> Walk:
    """The walk for one export, built once. The export is held beside its walk so the identity
    the cache is keyed on cannot be recycled onto a different object."""
    cached = _WALKS.get(id(export))
    if cached is not None and cached[0] is export:
        return cached[1]
    built = _build_walk(export)
    _WALKS[id(export)] = (export, built)
    return built


def raises_faced(walk: Walk, node: SolverNode) -> int:
    """How many raises are already in the pot hero is being asked about."""
    return sum(1 for entry in walk.sequence[node.path] if entry.action == "raise")


def within_raise_depth(walk: Walk, node: SolverNode) -> bool:
    """Clause one: at most two raises in, nothing deeper."""
    return raises_faced(walk, node) <= COMMITTED_RAISE_DEPTH


def cold_call_index(walk: Walk, node: SolverNode) -> int | None:
    """Hero's cold call, which is the one branch decision 46 removes.

    Cold means hero has put nothing in beyond the blinds. The big blind is never cold - it has
    posted, and decision 52 keeps its defence inside the measurement - and a seat that opened and
    now faces a three-bet is not cold either, so its call stays. Both exemptions are load-bearing:
    dropping the second commits 314 nodes with 284 three-bet-facing spots instead of 254.
    """
    if node.actor_pos == "BB" or node.actor_pos in walk.invested[node.path]:
        return None
    for index, action in enumerate(node.actions):
        if action.kind == "call":
            return index
    return None


def terminal_split_pct(walk: Walk, node: SolverNode) -> tuple[float, float, float]:
    """Where a node's decision mass ends up, over the branches the bot can take.

    Three percentages: the hand over before a flop, a heads-up flop, a multiway flop. Hero's cold
    call is removed and the rest renormalised, which is what "over the branches the bot can take"
    means and all it means.
    """
    cold = cold_call_index(walk, node)
    totals = [0.0, 0.0, 0.0]
    mass = 1.0
    for index in range(len(node.actions)):
        share = walk.frequency[node.path][index]
        if index == cold:
            mass -= share
            continue
        outcome = _outcome(walk.by_path, walk.folded, walk.below, node, index)
        for slot in range(3):
            totals[slot] += share * outcome[slot]
    if mass <= 0.0:
        return (0.0, 0.0, 0.0)
    return (100.0 * totals[0] / mass, 100.0 * totals[1] / mass, 100.0 * totals[2] / mass)


def exposure_pct(walk: Walk, node: SolverNode) -> float:
    """Clause two's measurement: the multiway-flop share of the split."""
    return terminal_split_pct(walk, node)[2]


def below_exposure_threshold(walk: Walk, node: SolverNode) -> bool:
    return exposure_pct(walk, node) < EXPOSURE_THRESHOLD_PCT


def is_big_blind_squeeze(walk: Walk, node: SolverNode) -> bool:
    """Clause three: hero is the big blind, faces an open, and a cold caller is already in."""
    return (
        node.actor_pos == "BB"
        and raises_faced(walk, node) == 1
        and any(entry.action == "call" for entry in walk.sequence[node.path])
    )


def has_an_arriving_hand_class(walk: Walk, node: SolverNode) -> bool:
    """Clause four: hero can be at this node holding something. Not a reach floor - a spot hero
    reaches rarely still ships. This asks whether he can be dealt anything here at all."""
    del walk  # A property of the node alone; the signature matches the other three clauses.
    return any(node.reach_bp)


def terminal_split_closes(walk: Walk, node: SolverNode) -> bool:
    """Clause five: the exposure measurement measured something.

    The three shares close on 100 when every branch is accounted for, and do not when mass
    reaches a node no hand class arrives at - `action_frequency` reads 0.0 there, so the mass
    leaves the walk rather than being redistributed and clause two divides by a denominator
    missing the branches it was meant to weigh. MAINT-34's decision 7: a guard that cannot see
    its own input fails closed.
    """
    return abs(100.0 - sum(terminal_split_pct(walk, node))) <= SPLIT_CLOSURE_TOLERANCE_PCT


def is_committed(walk: Walk, node: SolverNode) -> bool:
    """All five clauses, in the order the census files a refusal under."""
    return (
        within_raise_depth(walk, node)
        and below_exposure_threshold(walk, node)
        and not is_big_blind_squeeze(walk, node)
        and has_an_arriving_hand_class(walk, node)
        and terminal_split_closes(walk, node)
    )


def selected(export: SolverExport) -> tuple[SolverNode, ...]:
    """The committed 156, walked here rather than asked of the rule under test."""
    walk = walk_of(export)
    return tuple(node for node in export.nodes if is_committed(walk, node))


def key_of(walk: Walk, node: SolverNode) -> str:
    return spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, walk.sequence[node.path])


def coverage_pct(walk: Walk, nodes) -> float:
    """The share of preflop decisions a set of nodes carries: its arrival mass over the tree's."""
    total = sum(walk.arrival.values())
    return 100.0 * sum(walk.arrival[node.path] for node in nodes) / total
