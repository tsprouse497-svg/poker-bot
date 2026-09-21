"""Phase 14: which solved nodes become committed spots, and why the others do not.

Authored at stage 4, before the derivation the rulings require exists, so this file is the
specification rather than a description of what got built. It owns the selection rule: five
clauses, the first three each tested alone, no clause co-extensive with another, multiway exposure
as a measured walk to the leaves, and the committed 156 with the coverage it carries. It is also
where this phase's counts, walk and named nodes live, and every other file imports them from here.

`test_chart_census.py` owns the six-bucket census, the closed reason vocabulary and its
disjointness from the runtime miss codes, and what an excluded node does at the table;
`test_chart_conversion.py` and `test_derived_chart.py` what a committed row holds;
`test_chart_arrival_probability.py` the reach and arrival fields; `test_chart_cutover_evidence.py`
the relations and the two counterfactual arms.

**Five clauses select the committed set, and they stay separate because they are separate
rulings.** A node is committed when at most **two raises** are already in, nothing deeper
(decision 35); when the share of its decision mass reaching a **multiway flop terminal** is below
**ten percent**, measured over the branches the bot can take (decision 46); when it is **not**
a big-blind squeeze spot - hero is the big blind, faces an open, and a cold caller is already in
(decision 48); when **some hand class arrives at it at all** (MAINT-34's decision 2); and when
its **terminal split closes on a hundred**, so the exposure clause measured something rather than
nothing (MAINT-34's decision 7). That selects **156** of 30,609: 5 first-in, 16 facing an open,
135 facing a three-bet, carrying **98.7380** percent of preflop decisions. The fourth clause was
dead at a 7.5bb blind three-bet: 13.5 drives whole cold-calling lines to zero weight, so the export
carries nodes hero can never be at holding anything and 160 clear the three before it. Both of the
new clauses are placed after the depth clause, so the depth bucket keeps the four-bet family.

**"The branches the bot can take" names one branch and no other.** Hero's **cold** call is
removed and renormalised away; his call to a three-bet is not, and the big blind's defence never
is (decision 52). Removing every hero call instead commits 178, 157 of them facing a three-bet,
so the wording is load-bearing rather than decorative; removing nothing now selects the same 156,
one node only changing which clause refuses it. So this file measures the ruled branch node by
node instead of asserting a total two of the three readings reach together.

**Why the third clause exists, in poker.** The nine are the only committed shape whose chart still
offers hero a call into a multiway pot; the big blind's call stays in the measurement (decision
52), and it is essentially all of their exposure. The filter misses them because hero's fold -
89.13 percent at `LJ` opening and `BTN` calling - leaves that branch carrying 2.90 to 6.13 points,
under the ten-percent line (`MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`).

Every count is recomputed from the export by a walk written here, because a test that imports the
rule it checks is one copy of a rule agreeing with another, and what is pinned is tree shape
rather than solve output. **`selected` means committed** - sibling files import it.
"""

from __future__ import annotations

from collections import Counter

import pytest

from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    SolverExport,
    SolverNode,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction

# `TABLE_SIZE`, `DEPTH_BB` and `SEATS` are the walk module's, imported below with the rest of it
# rather than restated here, so the two cannot drift into describing different tables.

# --- The ruled numbers. Every one is in the contract or in the ExecPlan's ruled-numbers table,
# and every one is re-derived below by this file's own walk of the export.

EXPORTED_NODES = 30_609
COMMITTED_NODES = 156
RAISES_FACED_WHEN_COMMITTED = {0: 5, 1: 16, 2: 135}
EXPOSURE_REFUSED_NODES = 154
BB_SQUEEZE_REFUSED_NODES = 9
NO_ARRIVING_REFUSED_NODES = 160
SPLIT_REFUSED_NODES = 128
BEYOND_DEPTH_NODES = 30_002
WIDEST_ADMITTED_EXPOSURE_PCT = 9.1945
NARROWEST_REFUSED_EXPOSURE_PCT = 10.4362
COVERAGE_PCT = 98.7380
EXPOSURE_CODE = "derivation:multiway-exposure-above-threshold"
SQUEEZE_CODE = "derivation:big-blind-squeeze-spot"
DEPTH_CODE = "derivation:beyond-committed-raise-depth"
NO_ARRIVING_CODE = "derivation:no-arriving-hand-class"
SPLIT_CODE = "derivation:terminal-split-does-not-close"

COVERAGE_BY_RAISES_FACED = {0: 52.7327, 1: 38.0261, 2: 7.9792}
"""The three-way split of the 98.7380, decision 49. A split rather than a total, so that a build
committing the right number of the wrong nodes is caught: the five opens alone are more than half
of every preflop decision the bot ever faces."""

NODES_AT_COMMITTED_DEPTH = 607
"""What the raise-depth clause keeps on its own - 156 + 154 + 9 + 160 + 128 - and the domain
decision 40 measured over. The other four are read over the whole export. The total is still 607
while every part of it moved, a coincidence of the two trees."""

EXPOSURE_REFUSALS_OVER_THE_WHOLE_EXPORT = 12_416
BB_SQUEEZE_NODES_OVER_THE_WHOLE_EXPORT = 26
NO_ARRIVING_NODES_OVER_THE_WHOLE_EXPORT = 9_079
NON_CLOSING_NODES_AT_COMMITTED_DEPTH = 375
"""Each clause read as a predicate over all 30,609 nodes rather than behind the others, which is
the only way "no clause is co-extensive with another" is a claim about the clauses. Seventeen of
the 26 big-blind squeeze nodes are over the threshold too, so the census bucket holds nine and
this count does not: the precedence is what makes the six buckets a partition."""

COMMITTED_WITH_THREE_OR_MORE_LIVE = 109
COMMITTED_HEADS_UP_ALREADY = 47
"""Exposure is measured, not inferred from live players, and this is the gap between the two
readings: 109 of the 156 still have three or more seats able to reach the flop. A live-player
count would have refused every one of them and shipped 47 spots."""

COMMITTED_WITH_A_CALLER_ALREADY_IN = 1
COMMITTED_WITH_A_CALL_IN_THE_SEQUENCE = 101
COMMITTED_AT_ZERO_EXPOSURE = 51
THREE_BET_SPOTS_WITH_ANY_EXPOSURE = 90

BB_SQUEEZE_FOLD_PCT = 89.13
BB_SQUEEZE_CALL_PCT = 4.97
BB_SQUEEZE_RAISE_PCT = 5.90
"""Decision 48's measurement at `LJ` opens, `BTN` calls. The fold keeps hero's call branch small
enough to slip the ten-percent threshold; it does not name the nine, three committed siblings on
the same sequence folding harder. The test carries the rule that does."""

SPLIT_LEAK_PCT = 0.05
"""A terminal split does not close on exactly 100. Mass reaching a node no hand class arrives at
is dropped rather than redistributed, the solve publishing no strategy to redistribute it by, and
over the committed 249 of the 7.5bb solve the largest shortfall measured here was under three
hundredths of a point. Pinned as a tolerance so that a build losing a whole branch cannot hide
inside it.

**Not moved for MAINT-34, and it is the reason clause five exists.** The re-solve tripped it: at
the intermediate 284-spot cut 128 committed spots no longer closed and 109 of those lost their
split entirely, reading an exposure of exactly 0.0 because every branch evaporated rather than
because hero is heads-up. Widening this is what it was written to prevent, so decision 7 made it a
clause instead: those 128 are refused, every one of the committed 156 closes inside it with the
widest shortfall left at 0.0106 of a point, and the assertion reading it in
`test_chart_census.py` holds."""

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

# A cold call in front of hero, committed anyway: the small blind answering a lojack open the
# button flatted. The **only** one left after MAINT-34's clause five - the cutoff's version of
# this spot, named here until decision 7, is now refused for a split that does not close - and
# still the reason the third clause is about a seat and not about a call.
COLD_CALLED_COMMITTED_PATH = (1, 0, 0, 1)
COLD_CALLED_COMMITTED_KEY = "t6/d100/SB/LJ:raise@2.5,BTN:call"
COLD_CALLED_COMMITTED_SEQUENCE = (
    PreflopAction("LJ", "raise", 2.5),
    PreflopAction("BTN", "call"),
)

# The same board with the big blind as hero, and refused: decision 48's named spot. Moved with
# `COLD_CALLED_COMMITTED` under MAINT-34's clause five, so the pair still shares one sequence and
# differs only in who hero is - which is the whole of what the third clause turns on.
BB_SQUEEZE_PATH = (1, 0, 0, 1, 0)
BB_SQUEEZE_KEY = "t6/d100/BB/LJ:raise@2.5,BTN:call"
BB_SQUEEZE_SEQUENCE = COLD_CALLED_COMMITTED_SEQUENCE

# The margin, both ends. A point and a quarter apart, and the report publishes both. The widest
# admitted moved under clause five: the spot that held it reads 9.6609 off a split that closes on
# 76.67, so it is refused now rather than being the margin.
WIDEST_ADMITTED_PATH = (1, 0, 1, 1, 2, 0, 1, 0)
WIDEST_ADMITTED_KEY = "t6/d100/BTN/LJ:raise@2.5,CO:call,BTN:call,SB:raise@13.5,LJ:call"
WIDEST_ADMITTED_SPLIT = (0.0017, 90.8038, WIDEST_ADMITTED_EXPOSURE_PCT)
NARROWEST_REFUSED_PATH = (0, 0, 1, 1, 0)
NARROWEST_REFUSED_KEY = "t6/d100/BB/CO:raise@2.5,BTN:call"
NARROWEST_REFUSED_SEQUENCE = (
    PreflopAction("CO", "raise", 2.5),
    PreflopAction("BTN", "call"),
)

# Hero faces a three-bet and is committed: two raises in is the deepest the phase ships. The blind
# three-bet is 13.5 and the button's four-bet over it 40.5, the button still on the global 3.0.
THREE_BET_FACED_PATH = (0, 0, 0, 1, 0, 2)
THREE_BET_FACED_KEY = "t6/d100/BTN/BTN:raise@2.5,BB:raise@13.5"

# One action later, and refused: the four-bet family a later phase takes up.
FOUR_BET_FACED_PATH = (0, 0, 0, 1, 0, 2, 2)
FOUR_BET_FACED_KEY = "t6/d100/BB/BTN:raise@2.5,BB:raise@13.5,BTN:raise@40.5"
FOUR_BET_FACED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("BB", "raise", 13.5),
    PreflopAction("BTN", "raise", 40.5),
)


# --- The walk, and the definitions this file refuses to import ---


def derivation():
    """The module stage 6 finishes, imported inside the call rather than at module scope, so a
    rewrite that renames it fails one test rather than stopping the file collecting."""
    import poker_training_bot.solver_artifacts.chart_derivation as module

    return module


# The walk itself lives in `chart_selection_walk.py`, a support module this file owns: MAINT-34's
# fourth clause did not fit under the 700-line cap and the ruling was to split rather than to
# compress the reasoning here. The names are re-exported rather than re-reached, so the four
# sibling files that read them through `test_chart_derivation` need no edit and there is still
# exactly one place each of them is defined.
from chart_selection_walk import (  # noqa: E402
    COMMITTED_RAISE_DEPTH,
    DEPTH_BB,  # noqa: F401  - re-exported for the sibling files
    EXPOSURE_THRESHOLD_PCT,
    SEATS,
    TABLE_SIZE,  # noqa: F401  - re-exported for the sibling files
    Walk,
    _outcome,
    below_exposure_threshold,
    cold_call_index,
    coverage_pct,
    exposure_pct,
    has_an_arriving_hand_class,  # noqa: F401  - re-exported for the sibling files
    is_big_blind_squeeze,
    is_committed,
    key_of,
    raises_faced,
    selected,
    terminal_split_closes,  # noqa: F401  - re-exported for the sibling files
    terminal_split_pct,  # noqa: F401  - re-exported for the sibling files
    walk_of,
    within_raise_depth,
)


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


# --- The first three clauses, each alone ---


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
    is where an earlier cut had it: **109 of the 156 committed nodes still have three or more
    seats live**, and a live-player count would have refused every one of them and shipped 47
    spots. The two readings are separated by measurement here rather than argued about.

    The threshold is ten percent and the margin is a point and a quarter, so both ends are named
    nodes rather than statistics: the widest admitted is the button answering a small-blind
    three-bet the lojack has already called, at **9.1945**, and the narrowest refused is the big
    blind facing a cutoff open the button flatted, at **10.4362**.
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

    Removing nothing commits the same 156, one node only moving between the exposure and the
    split buckets; the ruled reading commits 161 without the third clause, which refuses the five
    of its nine the other four would have kept; removing hero's call at every node he acts at
    commits 178. This asserts which branch the ruled measurement drops, node by node, rather than
    asserting the total it happens to produce - a total two different rules now reach.
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


def test_the_big_blind_squeeze_clause_alone_names_the_nine_the_others_admit(
    export: SolverExport, walked: Walk
) -> None:
    """Clause three on its own, and the poker that forced it.

    Hero is the big blind, faces an open, and a cold caller is already in. Twenty-six nodes in the
    export are that shape; seventeen fail the exposure clause too, so the census bucket holds the
    nine that would otherwise have shipped.

    **What names the nine is hero's own published call, not the size of his fold.** The fold does
    not separate them: on the sequence `LJ:raise@2.5,BTN:call` the big blind folds 89.13 percent
    and is refused at 4.9716 exposure, while the small blind on the same board folds harder at
    92.28 and ships at 4.6476 - the refused spot has the smaller fold and the wider exposure, so
    neither reading picks it out. What differs is whose branch it is. `cold_call_index` exempts
    the big blind, which posted and whose defence decision 52 keeps inside the measurement, so at
    these nine the figure is hero's own call landing him in a three-way pot the calibrated fit has
    no cell for: take that branch out and all nine fall under two tenths of a point. At the 11
    merged spots decision 46 removes hero's cold call from the measurement and decision 45 removes
    it from the chart, so their 0.0005-to-4.6476 is flops hero is not in; at the five big-blind
    spots with no caller in, hero's call is heads-up and the figure is exactly 0.

    So the clause is not a second exposure rule: it refuses the only committed shape whose chart
    offers a call that puts hero in a multiway pot, which the exposure clause cannot reach because
    the fold leaves that branch at 2.90 to 6.13 points, the widest near four points under the
    threshold."""
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

    # The argument, asserted rather than described: at every one of the nine the exposure is hero's
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
    # about the seat: its 26 committed nodes carry 13.67 percent of preflop decisions and the
    # five no-caller spots alone carry 11.44, so a blanket exclusion is a near-fourteen-point hole
    # in the seat a beginner plays worst.
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
    is taken over all 30,609 nodes rather than over the 607 the depth clause leaves, because a
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


def test_the_five_clauses_select_the_committed_156(
    export: SolverExport, walked: Walk, committed: tuple[SolverNode, ...]
) -> None:
    """The set every later measurement in this phase is taken over.

    **156 of 30,609** - 5 first-in, 16 facing an open, 135 facing a three-bet - carrying
    **98.7380 percent** of preflop decisions, split 52.7327 across the five opens, 38.0261 across
    the answers to an open and 7.9792 across the answers to a three-bet. The split is asserted
    and not only the total, because a build committing 156 of the wrong nodes reaches the same
    total from a different shape.

    **The coverage did not move when clause five removed 128 spots**, and that is the check on
    decision 7 rather than a coincidence: every one of the 128 carries zero arrival, so the chart
    lost 0 of 6,054,005,282 parts per billion. A build that refused the wrong 128 would move it.

    Compared as keys as well as counts: 156 nodes are not self-evidently 156 spots, and a grammar
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
