"""Which solved nodes the chart commits, and the walk that decides it.

`chart_derivation.py` turns a committed node into cells; this module decides which nodes those
are. The two live apart because `src/**/*.py` stops at 500 lines and the walk to the leaves does
not fit beside the conversion, so `chart_derivation` re-exports every name here and no caller has
to know which file a rule sits in.

Three clauses, conjoined, and each one a separate ruling rather than a restatement of the others.
At most two raises are already in the pot hero is being asked about. Under a tenth of the node's
decision mass reaches a flop with three or more players. And hero is not the big blind answering
an open somebody has already cold-called.

**The middle clause is measured, not counted.** "Could three players still be in" is a fact about
the node, and it is what an earlier cut of this rule used; the ruled reading is a fact about the
leaves below the node, which is where the source's pairwise pricing of a multiway pot actually
bites. The two disagree at 186 of the committed nodes: a seat count would have refused every one
of them, because a pot three seats can still enter mostly does not end up three-handed.

**The walk is bottom-up and memoised per tree.** The same subtree hangs under thousands of nodes,
so measuring each node by walking down from it re-walks the deep end of the tree once per
ancestor. Every node's split is instead built once, deepest first, out of the splits of its
children, and the whole tree costs about as much as reading it did.

An action kind no clause has a rule for raises, naming the kind. It is neither an exclusion nor
an inexpressible spot: all three clauses count what a seat did, so none of them can be evaluated
at such a node at all, and filing it under the spot grammar would record a converter that met
something new as a limitation of the chart.
"""

from __future__ import annotations

from dataclasses import dataclass

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts.gtopen_export import SolverAction, SolverNode
from poker_training_bot.solver_artifacts.lookup import (
    DERIVATION_BEYOND_COMMITTED_RAISE_DEPTH,
    DERIVATION_BIG_BLIND_SQUEEZE_SPOT,
    DERIVATION_MULTIWAY_EXPOSURE_ABOVE_THRESHOLD,
)

__all__ = [
    "COMMITTED_RAISE_DEPTH",
    "MULTIWAY_EXPOSURE_THRESHOLD_PCT",
    "SEATS",
    "TABLE_SIZE",
    "below_multiway_exposure_threshold",
    "cold_call_index",
    "exclusion_code",
    "is_big_blind_squeeze_spot",
    "is_committed_node",
    "multiway_exposure_pct",
    "raises_faced",
    "require_known_kind",
    "terminal_split_pct",
    "within_committed_raise_depth",
]

TABLE_SIZE = 6
SEATS = table_positions(TABLE_SIZE)

COMMITTED_RAISE_DEPTH = 2
"""At most two raises already in. Three is the four-bet family, which a later phase takes up.

Counted over the pot hero is being asked about rather than over the seats in front of him, so an
opener who has been three-bet and is now choosing is at two and stays, while the seat answering
his four-bet is at three and goes.
"""

MULTIWAY_EXPOSURE_THRESHOLD_PCT = 10.0
"""A tenth of the decision mass, strictly under, and the margin either side of it is thin: the
widest admitted spot sits at 9.8642 and the narrowest refused at 10.0234, sixteen hundredths of a
point apart. A figure that close to the line is why the measurement is walked rather than
estimated from the seats still live."""

_VOLUNTARY_KINDS = frozenset({"call", "raise", "jam"})
_KNOWN_KINDS = frozenset({"fold"}) | _VOLUNTARY_KINDS

_WALK_CACHE_SIZE = 3


def require_known_kind(node: SolverNode, action: SolverAction) -> str:
    """The kind of one offered action, or a refusal naming what could not be classified."""
    if action.kind not in _KNOWN_KINDS:
        raise ValueError(
            f"node {node.path} offers the action kind {action.kind!r}, which this"
            " derivation has no rule for; all three selection clauses count what each"
            " seat did, so none of them can be evaluated here, and the node is refused"
            " rather than filed under a reason from the closed vocabulary"
        )
    return action.kind


@dataclass(frozen=True)
class SelectionWalk:
    """One pass over one tree, holding everything the three clauses read.

    Four of the five fields are facts about the line into a node - raises in, whether anybody has
    called, who has money in, how many have folded - and the fifth, `below`, is the only one that
    looks downward. Keeping them together is what makes the clauses cheap: each is then a dict
    lookup and a loop over the node's own handful of actions.
    """

    by_path: dict[tuple[int, ...], SolverNode]
    raises_in: dict[tuple[int, ...], int]
    called_in: dict[tuple[int, ...], bool]
    invested: dict[tuple[int, ...], frozenset[str]]
    folded: dict[tuple[int, ...], int]
    frequency: dict[tuple[int, ...], tuple[float, ...]]
    below: dict[tuple[int, ...], tuple[float, float, float]]


def _outcome(
    walk: SelectionWalk, node: SolverNode, index: int
) -> tuple[float, float, float]:
    """Where one branch ends up: hand over preflop, heads-up flop, multiway flop.

    A branch that continues carries its child's own split, already built. A branch that ends is a
    terminal, and what it is a terminal *of* is read off the seats still live after it: one seat
    means everybody folded, two a heads-up flop, three or more the multiway flop the source
    cannot price. The last is a property of the leaf, never of the node it hangs under, which is
    the whole reason this is walked to rather than asked at the top.
    """
    child = (*node.path, index)
    reached = walk.below.get(child)
    if reached is not None:
        return reached
    live = len(SEATS) - walk.folded[node.path]
    if node.actions[index].kind == "fold":
        live -= 1
    return (float(live == 1), float(live == 2), float(live >= 3))


def _build_walk(by_path: dict[tuple[int, ...], SolverNode]) -> SelectionWalk:
    """Read the tree once: the line down to every node, then every node's split, deepest first."""
    raises_in = {(): 0}
    called_in = {(): False}
    invested: dict[tuple[int, ...], frozenset[str]] = {(): frozenset()}
    folded = {(): 0}
    for path in sorted(by_path, key=len):
        node = by_path[path]
        for index, action in enumerate(node.actions):
            kind = require_known_kind(node, action)
            child = (*path, index)
            if child not in by_path:
                continue
            if kind == "fold":
                raises_in[child] = raises_in[path]
                called_in[child] = called_in[path]
                invested[child] = invested[path]
                folded[child] = folded[path] + 1
                continue
            raises_in[child] = raises_in[path] + (0 if kind == "call" else 1)
            called_in[child] = called_in[path] or kind == "call"
            invested[child] = invested[path] | {node.actor_pos}
            folded[child] = folded[path]
    frequency = {
        path: tuple(node.action_frequency(index) for index in range(len(node.actions)))
        for path, node in by_path.items()
    }
    walk = SelectionWalk(by_path, raises_in, called_in, invested, folded, frequency, {})
    for path in sorted(by_path, key=len, reverse=True):
        node = by_path[path]
        totals = [0.0, 0.0, 0.0]
        for index in range(len(node.actions)):
            share = frequency[path][index]
            if not share:
                continue
            outcome = _outcome(walk, node, index)
            for slot in range(3):
                totals[slot] += share * outcome[slot]
        walk.below[path] = (totals[0], totals[1], totals[2])
    return walk


_WALKS: list[tuple[dict[tuple[int, ...], SolverNode], SelectionWalk]] = []


def _walk_of(by_path: dict[tuple[int, ...], SolverNode]) -> SelectionWalk:
    """The walk for one tree, built once per tree the caller hands in.

    Keyed on the mapping's own identity, and the mapping is held beside its walk so that the
    identity cannot be recycled onto a different tree while the answer for the old one is still
    cached. A few trees are kept rather than one, because a conversion asks for a census and a
    chart off the same export and each builds its own mapping, and rather than all of them,
    because a tree is tens of megabytes and a report loops over exports.
    """
    for held, built in _WALKS:
        if held is by_path:
            return built
    built = _build_walk(by_path)
    _WALKS.insert(0, (by_path, built))
    del _WALKS[_WALK_CACHE_SIZE:]
    return built


def raises_faced(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> int:
    """How many raises are already in the pot hero is being asked about.

    A statement about the pot and not about the seats: hero's own earlier raise is one of them,
    so an opener facing a three-bet faces two, the same as the seat that opened behind him would.
    Reading it as "raises by other people" would ship the four-bet family under the opener's name.
    """
    return _walk_of(by_path).raises_in[node.path]


def within_committed_raise_depth(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> bool:
    """Clause one: at most two raises in, nothing deeper."""
    return raises_faced(by_path, node) <= COMMITTED_RAISE_DEPTH


def cold_call_index(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> int | None:
    """Hero's cold call, which is the one branch the exposure measurement drops.

    Cold means hero has nothing in beyond the blinds. The small blind IS cold, its 0.5 being
    posted rather than chosen, and it is half the merging spots. The big blind is never cold, and
    not because it posted more: it closes the action, so its call is a defence of a price it is
    already half paying rather than money in behind an opener, and it stays inside the
    measurement. A seat that opened and now faces a three-bet is not cold either, its own raise
    being already in, so its call stays too. The second exemption carries weight rather than
    decorating the sentence: dropping it removes a branch the chart still offers, and commits 346
    spots - 5 first-in, 25 facing an open, 316 facing a three-bet - instead of 249 with 219
    facing a three-bet. Recount it against the export rather than from here. The 361 this line
    used to carry was a different counterfactual, taken before the third clause removes ten.
    """
    walk = _walk_of(by_path)
    if node.actor_pos == "BB" or node.actor_pos in walk.invested[node.path]:
        return None
    for index, action in enumerate(node.actions):
        if require_known_kind(node, action) == "call":
            return index
    return None


def terminal_split_pct(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> tuple[float, float, float]:
    """Where a node's decision mass ends up, over the branches the bot can take.

    Three shares: the hand over before a flop, a heads-up flop, a multiway flop. "The branches
    the bot can take" names hero's cold call and nothing else - it is removed and the rest
    renormalised - because that is the one branch the chart refuses to offer him, so leaving it
    in measures a pot he is never in. Removing every call of hero's instead would drop the big
    blind's defence, which he does play.

    The three do not close on exactly 100. Mass that reaches a node no hand class arrives at is
    dropped rather than redistributed, the solve publishing no strategy to redistribute it by.
    """
    walk = _walk_of(by_path)
    cold = cold_call_index(by_path, node)
    totals = [0.0, 0.0, 0.0]
    mass = 1.0
    for index in range(len(node.actions)):
        share = walk.frequency[node.path][index]
        if index == cold:
            mass -= share
            continue
        outcome = _outcome(walk, node, index)
        for slot in range(3):
            totals[slot] += share * outcome[slot]
    if mass <= 0.0:
        return (0.0, 0.0, 0.0)
    return (100.0 * totals[0] / mass, 100.0 * totals[1] / mass, 100.0 * totals[2] / mass)


def multiway_exposure_pct(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> float:
    """Clause two's measurement: the multiway-flop share of the split, and the same number the
    report prints per spot rather than a second derivation of it."""
    return terminal_split_pct(by_path, node)[2]


def below_multiway_exposure_threshold(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> bool:
    """Clause two: under a tenth of the decision mass reaches a multiway flop."""
    return multiway_exposure_pct(by_path, node) < MULTIWAY_EXPOSURE_THRESHOLD_PCT


def is_big_blind_squeeze_spot(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> bool:
    """Clause three: hero is the big blind, faces one raise, and a caller is already in.

    Not a second exposure rule. These are the only committed shape whose chart still offers hero
    a call that puts him in a three-way pot: everywhere else the call the bot may take is either
    removed from the measurement as cold or heads-up by then. The exposure clause cannot reach
    them because the big blind folds better than nine times in ten here, which leaves that branch
    carrying under nine points, and a clause about a seat is what refuses them.

    It is about the seat rather than about the call in front of it, and that is the correction it
    encodes: the cutoff answering the same open and the same flat is committed. The five
    big-blind spots with nobody flatting stay too, and they are worth eleven points of coverage
    on their own, so a blanket exclusion of the big blind would be a hole in the seat a beginner
    plays worst.
    """
    walk = _walk_of(by_path)
    return (
        node.actor_pos == "BB"
        and walk.raises_in[node.path] == 1
        and walk.called_in[node.path]
    )


def exclusion_code(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> str | None:
    """Why a node is not committed, or None when it is.

    The precedence is load-bearing rather than a coding order. Twenty-six nodes are big-blind
    squeeze spots and sixteen of them are over the exposure threshold as well; filed here they
    take the exposure code, so the squeeze bucket holds exactly the ten that would otherwise have
    shipped and a later phase reading either bucket by name gets the set the name claims. The
    reverse order balances at the same total with a bucket of 26 and a bucket of 332.
    """
    if not within_committed_raise_depth(by_path, node):
        return DERIVATION_BEYOND_COMMITTED_RAISE_DEPTH
    if not below_multiway_exposure_threshold(by_path, node):
        return DERIVATION_MULTIWAY_EXPOSURE_ABOVE_THRESHOLD
    if is_big_blind_squeeze_spot(by_path, node):
        return DERIVATION_BIG_BLIND_SQUEEZE_SPOT
    return None


def is_committed_node(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> bool:
    """All three clauses together, read off the reason the node would be refused for.

    Written as the absence of a code rather than as the conjunction again, so that the chart and
    the census cannot drift apart: a spot that ships without a bucket accounting for its absence,
    or a bucket counting a spot that shipped, is not expressible from here.
    """
    return exclusion_code(by_path, node) is None
