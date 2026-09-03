"""Phase 14: which solved nodes become committed spots, and why the others do not.

Authored at stage 4, before the derivation the rulings require exists, so this file is the
specification rather than a description of what got built. It owns the selection rule: the three
clauses each tested alone, no clause co-extensive with another, multiway exposure as a measured
walk to the leaves, and the committed 249 with the coverage it carries. It is also where this
phase's counts, walk and named nodes live, and every other file imports them from here.

`test_chart_census.py` owns the four-bucket census, the closed reason vocabulary and its
disjointness from the runtime miss codes, and what an excluded node does at the table;
`test_chart_conversion.py` and `test_derived_chart.py` what a committed row holds;
`test_chart_arrival_probability.py` the reach and arrival fields; `test_chart_cutover_evidence.py`
the relations and the two counterfactual arms.

**Three clauses select the committed set, and they stay separate because they are separate
rulings.** A node is committed when at most **two raises** are already in, nothing deeper
(decision 35); when the share of its decision mass reaching a **multiway flop terminal** is below
**ten percent**, measured over the branches the bot can take (decision 46); and when it is **not**
a big-blind squeeze spot - hero is the big blind, faces an open, and a cold caller is already in
(decision 48). That selects **249** of 33,969: 5 first-in, 25 facing an open, 219 facing a
three-bet, carrying **98.5949** percent of preflop decisions.

**"The branches the bot can take" names one branch and no other.** Hero's **cold** call is
removed and renormalised away; his call to a three-bet is not, and the big blind's defence never
is (decision 52). The other readings of that phrase commit 257 with nothing removed and 361 with
every hero call removed, so the wording is load-bearing rather than decorative, and this file
measures the ruled one branch by branch instead of asserting the total it happens to produce.

**Why the third clause exists, in poker.** The ten are the only committed shape whose chart still
offers hero a call into a multiway pot; the big blind's call stays in the measurement (decision
52), and it is essentially all of their exposure. The filter misses them because hero's fold -
93.33 percent at `LJ` opening and `HJ` calling - leaves that branch carrying 3.74 to 8.98 points,
under the ten-percent line (`MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`).

Every count is recomputed from the export by a walk written here, because a test that imports the
rule it checks is one copy of a rule agreeing with another, and what is pinned is tree shape
rather than solve output. **`selected` means committed** - sibling files import it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import pytest

from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    SolverExport,
    SolverNode,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key

TABLE_SIZE = 6
DEPTH_BB = 100
SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")

# --- The ruled numbers. Every one is in the contract or in the ExecPlan's ruled-numbers table,
# and every one is re-derived below by this file's own walk of the export.

EXPORTED_NODES = 33_969
COMMITTED_NODES = 249
RAISES_FACED_WHEN_COMMITTED = {0: 5, 1: 25, 2: 219}
EXPOSURE_REFUSED_NODES = 348
BB_SQUEEZE_REFUSED_NODES = 10
BEYOND_DEPTH_NODES = 33_362
EXPOSURE_THRESHOLD_PCT = 10.0
WIDEST_ADMITTED_EXPOSURE_PCT = 9.8642
NARROWEST_REFUSED_EXPOSURE_PCT = 10.0234
COVERAGE_PCT = 98.5949
EXPOSURE_CODE = "derivation:multiway-exposure-above-threshold"
SQUEEZE_CODE = "derivation:big-blind-squeeze-spot"
DEPTH_CODE = "derivation:beyond-committed-raise-depth"

COMMITTED_RAISE_DEPTH = 2
"""At most two raises already in. Three is the four-bet family, which a later phase takes up."""

COVERAGE_BY_RAISES_FACED = {0: 51.9237, 1: 38.5422, 2: 8.1290}
"""The three-way split of the 98.5949, decision 49. A split rather than a total, so that a build
committing the right number of the wrong nodes is caught: the five opens alone are more than half
of every preflop decision the bot ever faces."""

NODES_AT_COMMITTED_DEPTH = 607
"""What the raise-depth clause keeps on its own - 249 + 348 + 10 - and the domain decision 40
measured over. The other two clauses are read here over the whole export, not over this."""

EXPOSURE_REFUSALS_OVER_THE_WHOLE_EXPORT = 15_170
BB_SQUEEZE_NODES_OVER_THE_WHOLE_EXPORT = 26
"""Each clause read as a predicate over all 33,969 nodes rather than behind the others, which is
the only way "no clause is co-extensive with another" is a claim about the clauses. Sixteen of the
26 big-blind squeeze nodes are over the threshold too, so the census bucket holds ten and this
count does not: the precedence is what makes the four buckets a partition."""

COMMITTED_WITH_THREE_OR_MORE_LIVE = 186
COMMITTED_HEADS_UP_ALREADY = 63
"""Exposure is measured, not inferred from live players, and this is the gap between the two
readings: 186 of the 249 still have three or more seats able to reach the flop. A live-player
count would have refused every one of them and shipped 63 spots."""

COMMITTED_WITH_A_CALLER_ALREADY_IN = 10
COMMITTED_WITH_A_CALL_IN_THE_SEQUENCE = 194
COMMITTED_AT_ZERO_EXPOSURE = 76
THREE_BET_SPOTS_WITH_ANY_EXPOSURE = 149

BB_SQUEEZE_FOLD_PCT = 93.33
BB_SQUEEZE_CALL_PCT = 3.58
BB_SQUEEZE_RAISE_PCT = 3.09
"""Decision 48's measurement at `LJ` opens, `HJ` calls. The fold keeps hero's call branch small
enough to slip the ten-percent threshold; it does not name the ten, three committed siblings on
the same sequence folding harder. The test carries the rule that does."""

SPLIT_LEAK_PCT = 0.05
"""A terminal split does not close on exactly 100. Mass reaching a node no hand class arrives at
is dropped rather than redistributed, the solve publishing no strategy to redistribute it by, and
over the committed 249 the largest shortfall measured here is under three hundredths of a point.
Pinned as a tolerance so that a build losing a whole branch cannot hide inside it."""

# --- The nodes this file names, because this file is what names nodes for the phase. ---

# The lojack's own open: the first decision of the hand, and the widest-arriving committed spot.
LOJACK_OPEN_PATH: tuple[int, ...] = ()
LOJACK_OPEN_KEY = "t6/d100/LJ/rfi"

# The small blind opening a folded pot: the one committed spot with nobody left to act behind,
# where `CHART-HERO-MUST-NEVER-LIMP` holds by construction and exposure is exactly zero.
SB_OPEN_PATH = (0, 0, 0, 0)
SB_OPEN_KEY = "t6/d100/SB/rfi"

# The spot the contract asks a non-coding reviewer to follow end to end: the big blind closing
# against a button open, six-max's most-played decision.
TRACED_PATH = (0, 0, 0, 1, 0)
TRACED_KEY = "t6/d100/BB/BTN:raise@2.5"
TRACED_SEQUENCE = (PreflopAction("BTN", "raise", 2.5),)

# Decision 45's worked example: the small blind against a lojack open, defending 9.99 percent,
# whose call weight merges into its raise because the bot may not cold-call.
MERGED_FLAT_PATH = (1, 0, 0, 0)
MERGED_FLAT_KEY = "t6/d100/SB/LJ:raise@2.5"

# A cold call in front of hero, committed anyway: the cutoff answering a lojack open the hijack
# flatted. One of the ten, and the reason the third clause is about a seat and not about a call.
COLD_CALLED_COMMITTED_PATH = (1, 1)
COLD_CALLED_COMMITTED_KEY = "t6/d100/CO/LJ:raise@2.5,HJ:call"
COLD_CALLED_COMMITTED_SEQUENCE = (
    PreflopAction("LJ", "raise", 2.5),
    PreflopAction("HJ", "call"),
)

# The same board with the big blind as hero, and refused: decision 48's named spot.
BB_SQUEEZE_PATH = (1, 1, 0, 0, 0)
BB_SQUEEZE_KEY = "t6/d100/BB/LJ:raise@2.5,HJ:call"
BB_SQUEEZE_SEQUENCE = COLD_CALLED_COMMITTED_SEQUENCE

# The margin, both ends. Sixteen hundredths of a point apart, and the report publishes both.
WIDEST_ADMITTED_PATH = (1, 1, 2, 1, 0)
WIDEST_ADMITTED_KEY = "t6/d100/BB/LJ:raise@2.5,HJ:call,CO:raise@7.5,BTN:call"
WIDEST_ADMITTED_SPLIT = (0.7637, 89.3721, WIDEST_ADMITTED_EXPOSURE_PCT)
NARROWEST_REFUSED_PATH = (0, 1, 1, 1, 1, 2, 0, 0)
NARROWEST_REFUSED_KEY = "t6/d100/BTN/HJ:raise@2.5,CO:call,BTN:call,SB:call,BB:raise@7.5"
NARROWEST_REFUSED_SEQUENCE = (
    PreflopAction("HJ", "raise", 2.5),
    PreflopAction("CO", "call"),
    PreflopAction("BTN", "call"),
    PreflopAction("SB", "call"),
    PreflopAction("BB", "raise", 7.5),
)

# Hero faces a three-bet and is committed: two raises in is the deepest the phase ships.
THREE_BET_FACED_PATH = (0, 0, 0, 1, 0, 2)
THREE_BET_FACED_KEY = "t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5"

# One action later, and refused: the four-bet family a later phase takes up.
FOUR_BET_FACED_PATH = (0, 0, 0, 1, 0, 2, 2)
FOUR_BET_FACED_KEY = "t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5"
FOUR_BET_FACED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("BB", "raise", 7.5),
    PreflopAction("BTN", "raise", 22.5),
)


# --- The walk, and the definitions this file refuses to import ---


def derivation():
    """The module stage 6 finishes, imported inside the call rather than at module scope, so a
    rewrite that renames it fails one test rather than stopping the file collecting."""
    import poker_training_bot.solver_artifacts.chart_derivation as module

    return module


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
    dropping the second commits 361 nodes with 321 three-bet-facing spots instead of 219.
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


def is_committed(walk: Walk, node: SolverNode) -> bool:
    """All three clauses, in the order the census files a refusal under."""
    return (
        within_raise_depth(walk, node)
        and below_exposure_threshold(walk, node)
        and not is_big_blind_squeeze(walk, node)
    )


def selected(export: SolverExport) -> tuple[SolverNode, ...]:
    """The committed 249, walked here rather than asked of the rule under test."""
    walk = walk_of(export)
    return tuple(node for node in export.nodes if is_committed(walk, node))


def key_of(walk: Walk, node: SolverNode) -> str:
    return spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, walk.sequence[node.path])


def coverage_pct(walk: Walk, nodes) -> float:
    """The share of preflop decisions a set of nodes carries: its arrival mass over the tree's."""
    total = sum(walk.arrival.values())
    return 100.0 * sum(walk.arrival[node.path] for node in nodes) / total


@pytest.fixture(scope="session")
def export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="session")
def walked(export: SolverExport) -> Walk:
    walk = walk_of(export)
    assert len(walk.sequence) == export.node_count, "the walk did not reach every node"
    return walk


@pytest.fixture(scope="session")
def committed(export: SolverExport) -> tuple[SolverNode, ...]:
    return selected(export)


# --- The three clauses, each alone ---


def test_the_raise_depth_clause_alone_keeps_607_and_names_the_four_bet_family(
    export: SolverExport, walked: Walk
) -> None:
    """Clause one on its own, in the converter and never as a node list.

    Two raises in is the deepest the phase ships. The clause is a statement about the pot hero is
    being asked about rather than about the actions in front of him: a seat that opened, got
    three-bet and is now choosing is at two raises and stays, and the seat answering the four-bet
    after it is at three and goes. It owns the one bucket big enough to hide a whole family in,
    so its two halves are asserted against the export's own node total as well as apart.
    """
    module = derivation()
    kept = [node for node in export.nodes if within_raise_depth(walked, node)]
    beyond = [node for node in export.nodes if not within_raise_depth(walked, node)]

    assert export.node_count == EXPORTED_NODES
    assert len(kept) == NODES_AT_COMMITTED_DEPTH
    assert len(beyond) == BEYOND_DEPTH_NODES
    assert len(kept) + len(beyond) == EXPORTED_NODES
    assert module.COMMITTED_RAISE_DEPTH == COMMITTED_RAISE_DEPTH
    assert max(raises_faced(walked, node) for node in kept) == COMMITTED_RAISE_DEPTH
    assert min(raises_faced(walked, node) for node in beyond) == COMMITTED_RAISE_DEPTH + 1
    # The clause keeps every depth it keeps entirely: no node at two raises is refused here, so
    # what it does and does not carry cannot be confused with what the exposure filter carries.
    assert set(Counter(raises_faced(walked, node) for node in kept)) == {0, 1, 2}

    faced = walked.by_path[FOUR_BET_FACED_PATH]
    kept_here = walked.by_path[THREE_BET_FACED_PATH]
    assert key_of(walked, faced) == FOUR_BET_FACED_KEY
    assert key_of(walked, kept_here) == THREE_BET_FACED_KEY
    assert raises_faced(walked, faced) == 3
    assert raises_faced(walked, kept_here) == COMMITTED_RAISE_DEPTH
    for node in export.nodes:
        assert module.raises_faced(walked.by_path, node) == raises_faced(walked, node), node.path
        assert module.within_committed_raise_depth(
            walked.by_path, node
        ) is within_raise_depth(walked, node), node.path


def test_the_exposure_clause_alone_is_a_walk_to_the_leaves_not_a_live_player_count(
    export: SolverExport, walked: Walk, committed: tuple[SolverNode, ...]
) -> None:
    """Clause two on its own, and the reading of it that is not the ruled one.

    Exposure is the share of a node's decision mass that reaches a flop with three or more
    players, walked from the node to its leaves. It is not "can three players still be in", which
    is where an earlier cut had it: **186 of the 249 committed nodes still have three or more
    seats live**, and a live-player count would have refused every one of them and shipped 63
    spots. The two readings are separated by measurement here rather than argued about.

    The threshold is ten percent and the margin is sixteen hundredths of a point, so both ends
    are named nodes rather than statistics: the widest admitted is the big blind facing a cutoff
    three-bet with two callers in at **9.8642**, and the narrowest refused is the button facing a
    big-blind three-bet into a four-handed pot at **10.0234**.
    """
    module = derivation()
    refused = [node for node in export.nodes if not below_exposure_threshold(walked, node)]
    at_depth = [node for node in export.nodes if within_raise_depth(walked, node)]
    still_multiway = [node for node in committed if len(SEATS) - len(walked.folded[node.path]) > 2]

    assert module.MULTIWAY_EXPOSURE_THRESHOLD_PCT == EXPOSURE_THRESHOLD_PCT
    assert len(refused) == EXPOSURE_REFUSALS_OVER_THE_WHOLE_EXPORT
    assert len(still_multiway) == COMMITTED_WITH_THREE_OR_MORE_LIVE
    assert len(committed) - len(still_multiway) == COMMITTED_HEADS_UP_ALREADY

    widest = walked.by_path[WIDEST_ADMITTED_PATH]
    narrowest = walked.by_path[NARROWEST_REFUSED_PATH]
    assert key_of(walked, widest) == WIDEST_ADMITTED_KEY
    assert key_of(walked, narrowest) == NARROWEST_REFUSED_KEY
    assert round(exposure_pct(walked, widest), 4) == WIDEST_ADMITTED_EXPOSURE_PCT
    assert round(exposure_pct(walked, narrowest), 4) == NARROWEST_REFUSED_EXPOSURE_PCT
    assert widest is max(committed, key=lambda node: exposure_pct(walked, node))
    assert narrowest is min(
        (node for node in at_depth if not below_exposure_threshold(walked, node)),
        key=lambda node: exposure_pct(walked, node),
    )
    assert WIDEST_ADMITTED_EXPOSURE_PCT < EXPOSURE_THRESHOLD_PCT < NARROWEST_REFUSED_EXPOSURE_PCT

    for node in at_depth:
        measured = module.multiway_exposure_pct(walked.by_path, node)
        assert measured == pytest.approx(exposure_pct(walked, node), abs=1e-9), node.path
        assert module.below_multiway_exposure_threshold(
            walked.by_path, node
        ) is below_exposure_threshold(walked, node), node.path


def test_the_exposure_measurement_removes_heros_cold_call_and_nothing_else(
    export: SolverExport, walked: Walk
) -> None:
    """Decision 52's wording, which selects a different set under each of its readings.

    Removing nothing commits 257; removing hero's call wherever it is cold, the big blind exempt,
    commits 259 before the third clause takes ten of them; removing hero's call at every node he
    acts at commits 361. This asserts which branch the ruled measurement drops, node by node,
    rather than asserting the total it happens to produce - a total three rules can reach.
    """
    module = derivation()
    at_depth = [node for node in export.nodes if within_raise_depth(walked, node)]
    cold = [node for node in at_depth if cold_call_index(walked, node) is not None]
    big_blind_calls = [
        node
        for node in at_depth
        if node.actor_pos == "BB" and any(a.kind == "call" for a in node.actions)
    ]

    assert cold, "no node offers hero a cold call, so the clause is untested"
    assert big_blind_calls, "no big blind is offered a call, so the exemption is untested"
    for node in big_blind_calls:
        assert cold_call_index(walked, node) is None, node.path
    for node in at_depth:
        index = cold_call_index(walked, node)
        if index is None:
            continue
        assert node.actions[index].kind == "call", node.path
        assert node.actor_pos != "BB", node.path
        assert node.actor_pos not in walked.invested[node.path], node.path
        # Nobody is offered a cold call before there is a raise to call.
        assert raises_faced(walked, node) >= 1, node.path

    opener_facing_a_three_bet = walked.by_path[THREE_BET_FACED_PATH]
    assert opener_facing_a_three_bet.actor_pos in walked.invested[THREE_BET_FACED_PATH]
    assert cold_call_index(walked, opener_facing_a_three_bet) is None
    for node in (
        walked.by_path[COLD_CALLED_COMMITTED_PATH],
        walked.by_path[BB_SQUEEZE_PATH],
        opener_facing_a_three_bet,
    ):
        assert module.cold_call_index(walked.by_path, node) == cold_call_index(
            walked, node
        ), node.path


def test_the_big_blind_squeeze_clause_alone_names_the_ten_the_other_two_admit(
    export: SolverExport, walked: Walk
) -> None:
    """Clause three on its own, and the poker that forced it.

    Hero is the big blind, faces an open, and a cold caller is already in. Twenty-six nodes in the
    export are that shape; sixteen fail the exposure clause too, so the census bucket holds the
    ten that would otherwise have shipped.

    **What names the ten is hero's own published call, not the size of his fold.** The fold does
    not separate them: on the identical sequence `LJ:raise@2.5,HJ:call` the big blind folds 93.33
    percent and is refused at 3.7368 exposure, while the small blind folds 95.50 and ships at
    3.7873, the button 95.44 at 5.1382 and the cutoff 95.68 at 6.1947 - the refused spot has the
    smallest fold and the lowest exposure of the four. What differs is whose branch the exposure
    is. `cold_call_index` exempts the big blind, which posted and whose defence decision 52 keeps
    inside the measurement, so at these ten the figure is hero's own call landing him in a
    three-way pot the calibrated fit has no cell for: take that branch out and all ten fall under
    a point. At the 20 merged spots decision 46 removes hero's cold call from the measurement and
    decision 45 removes it from the chart, so their 3.8-to-6.2 is flops hero is not in; at the
    five big-blind spots with no caller in, hero's call is heads-up and the figure is exactly 0.

    So the clause is not a second exposure rule: it refuses the only committed shape whose chart
    offers a call that puts hero in a multiway pot, which the exposure clause cannot reach because
    the fold leaves that branch at 3.74 to 8.98 points, the widest a point under the threshold."""
    module = derivation()
    squeezes = [node for node in export.nodes if is_big_blind_squeeze(walked, node)]
    slipping_through = [node for node in squeezes if below_exposure_threshold(walked, node)]

    assert len(squeezes) == BB_SQUEEZE_NODES_OVER_THE_WHOLE_EXPORT
    assert len(slipping_through) == BB_SQUEEZE_REFUSED_NODES
    for node in squeezes:
        assert node.actor_pos == "BB", node.path
        assert raises_faced(walked, node) == 1, node.path
        assert within_raise_depth(walked, node), "every squeeze node is inside the depth clause"
        assert module.is_big_blind_squeeze_spot(walked.by_path, node) is True, node.path

    named = walked.by_path[BB_SQUEEZE_PATH]
    assert key_of(walked, named) == BB_SQUEEZE_KEY
    assert named in slipping_through
    kinds = [action.kind for action in named.actions]
    assert kinds == ["fold", "call", "raise"]
    assert {
        kind: round(named.action_frequency(index) * 100.0, 2) for index, kind in enumerate(kinds)
    } == {
        "fold": BB_SQUEEZE_FOLD_PCT,
        "call": BB_SQUEEZE_CALL_PCT,
        "raise": BB_SQUEEZE_RAISE_PCT,
    }

    # The argument, asserted rather than described: at every one of the ten the exposure is hero's
    # own call, so removing that branch and renormalising leaves under a point everywhere.
    for node in slipping_through:
        kinds = [action.kind for action in node.actions]
        assert "call" in kinds, key_of(walked, node)
        multiway = mass = 0.0
        for index in range(len(node.actions)):
            if index == kinds.index("call"):
                continue
            share = walked.frequency[node.path][index]
            mass += share
            out = _outcome(walked.by_path, walked.folded, walked.below, node, index)
            multiway += share * out[2]
        assert 100.0 * multiway / mass < 1.0, (key_of(walked, node), multiway, mass)
        assert exposure_pct(walked, node) < EXPOSURE_THRESHOLD_PCT

    # The five big-blind spots with no caller in stay, so the clause is about the squeeze and not
    # about the seat: its 48 committed nodes carry 14.09 percent of preflop decisions and the
    # five no-caller spots alone carry 11.39, so a blanket exclusion is a fourteen-point hole in
    # the seat a beginner plays worst.
    kept_bb = [
        node
        for node in export.nodes
        if node.actor_pos == "BB" and raises_faced(walked, node) == 1 and is_committed(walked, node)
    ]
    assert len(kept_bb) == 5
    for node in kept_bb:
        assert not any(entry.action == "call" for entry in walked.sequence[node.path])
    assert module.is_big_blind_squeeze_spot(walked.by_path, walked.by_path[TRACED_PATH]) is False


def test_no_clause_is_co_extensive_with_another(export: SolverExport, walked: Walk) -> None:
    """Each clause refuses something the other two admit, so none is idle behind another.

    Decision 40 dropped a clause for failing exactly this: no node failed exposure while passing
    the opponent-investment test, so investment was strictly the stronger rule and exposure was
    inert behind it, and a criterion asserting that all three bit was written anyway. The check
    is taken over all 33,969 nodes rather than over the 607 the depth clause leaves, because a
    clause evaluated only where another has already passed cannot be shown to do work of its own.
    """
    deep = {node.path for node in export.nodes if not within_raise_depth(walked, node)}
    exposed = {node.path for node in export.nodes if not below_exposure_threshold(walked, node)}
    squeezed = {node.path for node in export.nodes if is_big_blind_squeeze(walked, node)}
    refusals = {"raise depth": deep, "exposure": exposed, "big-blind squeeze": squeezed}

    assert len(deep) == BEYOND_DEPTH_NODES
    assert len(exposed) == EXPOSURE_REFUSALS_OVER_THE_WHOLE_EXPORT
    assert len(squeezed) == BB_SQUEEZE_NODES_OVER_THE_WHOLE_EXPORT
    for name, refused in refusals.items():
        for other_name, other in refusals.items():
            if name == other_name:
                continue
            assert refused - other, (
                f"the {name} clause refuses nothing the {other_name} clause admits, so it is"
                " idle behind it and one of the two is not doing any selecting"
            )
    # The stronger form of the same claim: each clause is the sole reason for refusing somebody.
    assert len(exposed - deep) == EXPOSURE_REFUSED_NODES
    assert len(squeezed - exposed - deep) == BB_SQUEEZE_REFUSED_NODES
    assert deep - exposed - squeezed


def test_the_three_clauses_select_the_committed_249(
    export: SolverExport, walked: Walk, committed: tuple[SolverNode, ...]
) -> None:
    """The set every later measurement in this phase is taken over.

    **249 of 33,969** - 5 first-in, 25 facing an open, 219 facing a three-bet - carrying
    **98.5949 percent** of preflop decisions, split 51.9237 across the five opens, 38.5422 across
    the answers to an open and 8.1290 across the answers to a three-bet. The split is asserted
    and not only the total, because a build committing 249 of the wrong nodes reaches the same
    total from a different shape.

    Compared as keys as well as counts: 249 nodes are not self-evidently 249 spots, and a grammar
    collision shows up here as a set that is short rather than as a merge nobody noticed.
    """
    module = derivation()
    keys = {key_of(walked, node) for node in committed}

    assert len(committed) == COMMITTED_NODES
    assert len(keys) == COMMITTED_NODES, "two committed nodes collide in the key grammar"
    assert dict(Counter(raises_faced(walked, node) for node in committed)) == (
        RAISES_FACED_WHEN_COMMITTED
    )
    assert sum(RAISES_FACED_WHEN_COMMITTED.values()) == COMMITTED_NODES
    assert round(coverage_pct(walked, committed), 4) == COVERAGE_PCT
    for depth, share in COVERAGE_BY_RAISES_FACED.items():
        family = [node for node in committed if raises_faced(walked, node) == depth]
        assert len(family) == RAISES_FACED_WHEN_COMMITTED[depth]
        assert round(coverage_pct(walked, family), 4) == share, depth
    assert round(sum(COVERAGE_BY_RAISES_FACED.values()), 4) == COVERAGE_PCT

    for path, key in (
        (LOJACK_OPEN_PATH, LOJACK_OPEN_KEY),
        (SB_OPEN_PATH, SB_OPEN_KEY),
        (TRACED_PATH, TRACED_KEY),
        (MERGED_FLAT_PATH, MERGED_FLAT_KEY),
        (COLD_CALLED_COMMITTED_PATH, COLD_CALLED_COMMITTED_KEY),
        (THREE_BET_FACED_PATH, THREE_BET_FACED_KEY),
        (WIDEST_ADMITTED_PATH, WIDEST_ADMITTED_KEY),
    ):
        node = walked.by_path[path]
        assert key_of(walked, node) == key
        assert is_committed(walked, node), key
    for path, key in (
        (BB_SQUEEZE_PATH, BB_SQUEEZE_KEY),
        (NARROWEST_REFUSED_PATH, NARROWEST_REFUSED_KEY),
        (FOUR_BET_FACED_PATH, FOUR_BET_FACED_KEY),
    ):
        node = walked.by_path[path]
        assert key_of(walked, node) == key
        assert not is_committed(walked, node), key

    for node in export.nodes:
        assert module.is_committed_node(walked.by_path, node) is is_committed(
            walked, node
        ), node.path
