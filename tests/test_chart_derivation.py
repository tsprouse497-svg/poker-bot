"""Phase 14: which solved nodes become committed spots, and why the others do not.

Authored at stage 4, before the converter exists, so this file is the specification the
builder has to satisfy rather than a description of what got built. It owns which nodes get
committed and what each one becomes: the predicate that selects them, the three-way census
that proves none went missing, the two exclusion codes that partition the rest, the walk that
says whose action is whose, and one export node traced to the artifact row it became.
`tests/test_chart_conversion.py` is the other half, split from this one when the pair went
past the 700-line cap: it owns what that row costs and where its numbers came from - decision
6's sizing table, the perturbation proof that prices are read rather than written, the
refusal an excluded node gets at the table, and the external oracle. It imports this file's
named nodes and walk helpers rather than copying them, so the two halves cannot drift apart.
Both files run under `pytest_derived_chart`.

**The predicate is two clauses conjoined and it needs no threshold constant.** Keep a node
when at most one opponent has voluntarily invested beyond the blinds *and* at most two
players are still live. Decision 1 was superseded twice - a reach floor on 2026-08-23, the
history clause alone on 2026-08-24 - and the counts are what tell the three rules apart:
5,626 at the retired floor, 110 on the history clause, 5,472 on the subtree clause, **86 on
the conjunction**. Every count here is recomputed from the committed export by a walk
written in this file, because a test that imports the rule it is checking is one copy of a
rule agreeing with another.

What is pinned is tree shape rather than solve output: the node count, the four selection
counts, the census buckets, the seat and depth distributions and the four action menus all
depend on the action tree the ruled config builds, not on the strategies solved over it, so
they move only if the config moves - which decision 2 forbids. Reach is the exception and is
asserted as a property, the spots at full reach being exactly the spots where hero has not
yet acted, rather than as a number somebody remembered.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

# `lookup` twice on purpose: by name for the codes it already publishes, and as a module
# for the `DERIVATION_*` codes decision 8 adds at stage 6. Naming those today would
# fail the whole import block and hide every assertion in this file behind one error.
from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    class_combos,
    gtopen_class_index,
    load_solver_export,
    load_source_card,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.lookup import MISS_CODES
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key

TABLE_SIZE = 6
DEPTH_BB = 100
SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")

# The shape `lookup.py` already uses for every refusal it publishes. Decision 8 puts the
# derivation codes in the same one, so a reader meets one vocabulary rather than two.
NAMESPACED_CODE = re.compile(r"\A[a-z]+:[a-z0-9-]+\Z")

# Tree facts, every one. Decision 2 permits a re-solve at the ruled config and nothing else,
# so GTOpen builds the identical action tree and only the strategies and the reach move.
EXPORTED_NODES = 38_828
COMMITTED_NODES = 86
HISTORY_CLAUSE_NODES = 110
SUBTREE_CLAUSE_NODES = 5_472
HISTORY_BUT_NOT_CLEAN = 24
RETIRED_FLOOR_BP = 200
"""Decision 1's retired 2-percent reach floor. Kept only to assert it now selects nothing
the ruled predicate does not: all 86 clear it, so conjoining it changes nothing, which is
what made it a retirement rather than a retune."""

# The two exclusion buckets, and they partition the 38,742 excluded nodes. A node with a
# multiway terminal still reachable is filed under the mispricing, because that is the fact
# a later phase reads to find the spots that come back when GTOpen can price multiway.
MISPRICED_NODES = 33_356
OUTSIDE_RULE_NODES = 5_386

# The committed spot the contract asks a non-coding reviewer to follow end to end: the big
# blind closing the action against a button open, at full reach, offering fold, call, a
# three-bet to 7.5 and the stack. The most-played decision in six-max, and one of the 21
# spots that offer hero both a named raise and a jam - the case decision 6 exists for.
TRACED_PATH = (0, 0, 0, 1, 0)
TRACED_KEY = "t6/d100/BB/BTN:raise@2.5"
TRACED_SEQUENCE = (PreflopAction("BTN", "raise", 2.5),)
TRACED_ACTION_KINDS = ["fold", "call", "raise", "jam"]

# The one opening range the cutover commits. Four folds, then the small blind is to act
# with only the big blind behind, so it is the single spot in the 86 offering hero a raise
# and no call - which is `CHART-HERO-MUST-NEVER-LIMP` holding by construction.
SB_OPEN_PATH = (0, 0, 0, 0)
SB_OPEN_KEY = "t6/d100/SB/rfi"

# LJ opens to 2.5, HJ three-bets to 7.5, the cutoff flats, and the button is to act. Three
# actions by three different players, which is what makes it the walk's test rather than the
# artifact's: the actor of an action is the player who was to act *before* it. Two opponents
# have invested, so it is not a committed spot and never was under any of the three rules.
THREE_ACTOR_PATH = (1, 2, 1)
THREE_ACTOR_KEY = "t6/d100/BTN/LJ:raise@2.5,HJ:raise@7.5,CO:call"
THREE_ACTOR_SEQUENCE = (
    PreflopAction("LJ", "raise", 2.5),
    PreflopAction("HJ", "raise", 7.5),
    PreflopAction("CO", "call"),
)

# Folded to the button, which opens; the small blind flats; the big blind three-bets to 7.5
# and the small blind is to act. Four folds and three live actions, which is a shape fact and
# survives the re-solve. It is also one of the 5,386: heads-up from here on, so every terminal
# below it is priced exactly, and reached through a cold call, so the range it prices is one
# the same defect produced. That is the whole reason the subtree clause alone is not the rule.
COLD_CALLED_PATH = (0, 0, 0, 1, 1, 2, 0)
COLD_CALLED_KEY = "t6/d100/SB/BTN:raise@2.5,SB:call,BB:raise@7.5"
COLD_CALLED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("SB", "call"),
    PreflopAction("BB", "raise", 7.5),
)
COLD_CALLED_FOLDS = 4

# One of the 24 the 2026-08-25 supersession drops, and the sharpest of them: the lojack's
# own open. Every terminal below it can go multiway, so the model that prices it cannot see
# three-way equity, and the bot refuses a decision it answers today. The ruled cost, in one
# key.
LOJACK_OPEN_PATH: tuple[int, ...] = ()
LOJACK_OPEN_KEY = "t6/d100/LJ/rfi"


# --- fixtures, and the definitions this file refuses to import ---


def derivation():
    """The module stage 6 writes, imported inside the call rather than at module scope.

    A module-scope import of a module that does not exist yet stops the whole file
    collecting, hiding every assertion behind one ImportError - the gap
    `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` names. isort also leaves a function-body
    import alone, so this lints identically before and after stage 6.
    """
    import poker_training_bot.solver_artifacts.chart_derivation as module
    return module


@pytest.fixture(scope="module")
def export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def by_path(export: SolverExport) -> dict[tuple[int, ...], SolverNode]:
    return export.by_path()


@pytest.fixture(scope="module")
def derived(export: SolverExport):
    return derivation().derive_chart(export)


@pytest.fixture(scope="module")
def counted(export: SolverExport):
    return derivation().census(export)


def walk_state(
    by_path: dict[tuple[int, ...], SolverNode],
) -> dict[tuple[int, ...], tuple[frozenset[str], frozenset[str], tuple[PreflopAction, ...]]]:
    """Who has folded, who has voluntarily invested, and what hero faces, at every node.

    Written here rather than imported, because the predicate is on trial. Blinds are posted
    rather than chosen and never appear in the tree, so "voluntarily invested" is exactly
    "took a call, a raise or a jam"; an opener who later folds to a three-bet still counts,
    the strict reading the predicate-change review settled.
    """
    state = {(): (frozenset(), frozenset(), ())}
    for path in sorted(by_path, key=len):
        node = by_path[path]
        folded, invested, entries = state[path]
        for index, action in enumerate(node.actions):
            child = (*path, index)
            if child not in by_path:
                continue
            if action.kind == "fold":
                state[child] = (folded | {node.actor_pos}, invested, entries)
            elif action.kind in ("call", "raise", "jam"):
                entry = PreflopAction(
                    node.actor_pos,
                    "call" if action.kind == "call" else "raise",
                    None if action.kind == "call" else action.to,
                )
                state[child] = (folded, invested | {node.actor_pos}, (*entries, entry))
            else:
                raise AssertionError(f"node {path} offers an unhandled kind {action.kind!r}")
    return state


@pytest.fixture(scope="module")
def walked(by_path: dict[tuple[int, ...], SolverNode]) -> dict:
    state = walk_state(by_path)
    assert len(state) == len(by_path), "the walk did not reach every node"
    return state


def history_clause(node: SolverNode, state) -> bool:
    """At most one opponent has voluntarily put money in beyond the blinds."""
    _, invested, _ = state[node.path]
    return len(invested - {node.actor_pos}) <= 1


def subtree_clause(node: SolverNode, state) -> bool:
    """At most two players are still live, so every terminal below is heads-up.

    The clause the 110 was missing. The product approximation bites at *terminals* and a
    node's strategy is backward-induced over every terminal below it, so heads-up-ness has
    to be stated over the reachable subtree rather than over the action history.
    """
    folded, _, _ = state[node.path]
    return len(SEATS) - len(folded) <= 2


def selected(node: SolverNode, state) -> bool:
    return history_clause(node, state) and subtree_clause(node, state)


def key_of(node: SolverNode, state) -> str:
    return spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, state[node.path][2])


def measured_reach_bp(node: SolverNode) -> float:
    """Arriving reach spelled out here rather than imported from the module under test.

    A check comparing two copies of one rule cannot show the rule is right. The plain mean
    over the 169 hand classes of the fraction of hero's range that reaches the node, in
    basis points, read straight off the node's own row.
    """
    return sum(node.reach_bp) / 169.0


def combo_weighted_reach_bp(node: SolverNode) -> float:
    """The same figure weighted by combinations - the plausible other definition."""
    pairs = [(node.reach_bp[gtopen_class_index(n)], class_combos(n)) for n in HAND_CLASSES]
    return sum(reach * combos for reach, combos in pairs) / sum(c for _, c in pairs)


# --- Decision 1: the predicate that decides what gets committed ---


def test_the_predicate_is_the_conjunction_and_neither_clause_alone(
    export: SolverExport, walked
) -> None:
    """The ruling, and the two counts that prove it is not either clause on its own.

    Each supersession left a number behind that reads like the answer. The history clause
    alone commits 110 and admits the 24 nodes whose terminals can still go multiway - four
    of the five opens among them. The subtree clause alone commits 5,472 and admits 5,386
    that are heads-up from here on but arrive carrying a range the same defect produced.
    Only the conjunction is the ruling, so all four counts are asserted.
    """
    counts = Counter()
    for node in export.nodes:
        counts["history"] += history_clause(node, walked)
        counts["subtree"] += subtree_clause(node, walked)
        counts["both"] += selected(node, walked)
        counts["history not subtree"] += history_clause(node, walked) and not subtree_clause(
            node, walked
        )

    assert export.node_count == EXPORTED_NODES
    assert counts["history"] == HISTORY_CLAUSE_NODES
    assert counts["subtree"] == SUBTREE_CLAUSE_NODES
    assert counts["both"] == COMMITTED_NODES
    assert counts["history not subtree"] == HISTORY_BUT_NOT_CLEAN

    # And the module's own predicate is that conjunction at every node, not merely at the
    # count. Two rules can agree on a total and disagree on which nodes they picked.
    for node in export.nodes:
        assert derivation().is_committed_node(export.by_path(), node) is selected(
            node, walked
        ), node.path


def test_neither_clause_is_a_no_op_and_dropping_either_keeps_strictly_more(
    export: SolverExport, walked
) -> None:
    """A conjunction whose second half never fires is the first half with extra words.

    Both clauses have to bite: each alone keeps strictly more than the pair, and the pair
    keeps strictly less than the tree and more than nothing. That is the shape a count-free
    reader can check, and it tells a real conjunction from one spelled as one.
    """
    history = {n.path for n in export.nodes if history_clause(n, walked)}
    subtree = {n.path for n in export.nodes if subtree_clause(n, walked)}
    both = history & subtree

    assert 0 < len(both) < len(history) < export.node_count
    assert len(both) < len(subtree) < export.node_count
    assert both == {n.path for n in export.nodes if selected(n, walked)}


def test_the_retired_reach_floor_now_selects_nothing_the_predicate_does_not(
    export: SolverExport, walked
) -> None:
    """Decision 1's 2-percent floor is retired rather than retuned, and this is why.

    Every one of the 86 clears it, so conjoining it changes nothing. The floor is asserted
    as redundant rather than deleted, because "the predicate needs no threshold" can only be
    checked against the threshold it replaced. What must never happen is the reverse: a
    phase re-tightening a floor to make the bytes work, which the contract calls a halt.
    """
    committed = [node for node in export.nodes if selected(node, walked)]
    conjoined = [node for node in committed if measured_reach_bp(node) >= RETIRED_FLOOR_BP]

    assert len(committed) == COMMITTED_NODES
    assert conjoined == committed
    assert not hasattr(derivation(), "REACH_FLOOR_BP"), (
        "the ruled predicate needs no threshold constant; a floor left in the module is a"
        " second selection rule nobody ruled"
    )


def test_arriving_reach_is_the_plain_mean_over_the_169_classes(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode]
) -> None:
    """The definition, checked against the export rather than against itself.

    Reach stopped being the selection rule and stayed a published measurement - decision 5
    carries it per cell - so its definition still has to be pinned, because the
    combo-weighted reading is a different number for the same words. One named node is
    recomputed by hand from its own `reach_bp` row, then every node is, and where the two
    definitions disagree most is found at run time because that is a property of the solve.
    """
    widest = max(
        export.nodes, key=lambda node: abs(measured_reach_bp(node) - combo_weighted_reach_bp(node))
    )
    assert abs(measured_reach_bp(widest) - combo_weighted_reach_bp(widest)) > 1.0

    named = by_path[COLD_CALLED_PATH]
    assert derivation().node_reach_bp(named) == pytest.approx(sum(named.reach_bp) / 169.0)
    for node in export.nodes:
        assert abs(derivation().node_reach_bp(node) - measured_reach_bp(node)) < 1e-6, node.path


def test_the_committed_spots_are_exactly_what_the_predicate_selects(
    export: SolverExport, walked, derived
) -> None:
    """The artifact holds the predicate's answer, not a subset chosen somewhere else.

    Computed from the export by hand here, then compared against what the converter emitted,
    so a converter that dropped an awkward spot fails even though its census adds up. The
    opening ranges are named in both directions because they are the ruled cost: the small
    blind's is the one the bot keeps and the other four are ranges it answers today and
    refuses after the cutover. A chart carrying `LJ/rfi` is one built on the 110.
    """
    expected = {key_of(node, walked) for node in export.nodes if selected(node, walked)}
    committed = set(derived.artifact_payload["action_weights"])

    assert len(expected) == COMMITTED_NODES, "the predicate's spots collide in the key grammar"
    assert committed == expected
    assert SB_OPEN_KEY in committed
    for position in ("LJ", "HJ", "CO", "BTN"):
        assert f"t{TABLE_SIZE}/d{DEPTH_BB}/{position}/rfi" not in committed


def test_the_committed_set_has_the_measured_seat_and_depth_shape(
    export: SolverExport, walked
) -> None:
    """The distributions the rulings that rest on the 86 were re-taken against.

    Decisions 5, 6 and 10 were each first ruled on a count over a set this phase no longer
    commits, and each was restated against these. They are tree facts, so a re-solve at the
    ruled config cannot move them. The big blind's 20 is the mechanism in one number - it
    closes the action, so every one of its spots is terminal-clean.
    """
    committed = [node for node in export.nodes if selected(node, walked)]
    by_seat = Counter(node.actor_pos for node in committed)
    by_depth = Counter(len(node.path) for node in committed)
    by_aggression = Counter(
        sum(1 for entry in walked[node.path][2] if entry.action == "raise") for node in committed
    )
    dropped_by_seat = Counter(
        node.actor_pos
        for node in export.nodes
        if history_clause(node, walked) and not subtree_clause(node, walked)
    )

    assert by_seat == {"LJ": 15, "HJ": 14, "CO": 13, "BTN": 12, "SB": 12, "BB": 20}
    assert sorted(by_depth.items()) == [(4, 1), (5, 10), (6, 30), (7, 30), (8, 15)]
    assert sorted(by_aggression.items()) == [(0, 1), (1, 10), (2, 30), (3, 30), (4, 15)]
    assert dropped_by_seat == {"LJ": 1, "HJ": 3, "CO": 5, "BTN": 7, "SB": 8}
    assert "BB" not in dropped_by_seat


def test_the_spots_at_full_reach_are_the_spots_where_hero_has_not_acted(
    export: SolverExport, walked
) -> None:
    """Decision 5's premise, asserted as the property rather than as the count.

    11 of the 86 are at full reach against 35 of the 110, which gave the per-cell reach field
    a present reason rather than a prospective one. The eleven are named by a rule instead of
    listed: hero's whole range arrives exactly where hero has not yet acted, so any other
    full-reach set has mis-assigned an actor or written reach it did not read.
    """
    committed = [node for node in export.nodes if selected(node, walked)]
    full = {
        key_of(node, walked)
        for node in committed
        if measured_reach_bp(node) >= QUANTISATION_SCALE - 1e-9
    }
    unacted = {
        key_of(node, walked)
        for node in committed
        if all(entry.position != node.actor_pos for entry in walked[node.path][2])
    }

    assert full == unacted
    assert len(full) == 11
    assert SB_OPEN_KEY in full and TRACED_KEY in full


def test_the_four_action_menus_are_the_ruled_counts(export: SolverExport, walked) -> None:
    """A converter that dropped an action passes every other check in this file.

    The menus are what decision 6 was restated against and the sharpest cheap check on the
    conversion: 50 of the 86 offer hero only fold and call, so "every spot has a size" would
    price an action the chart never offers, and the 21 offering both a named raise and a jam
    are what the multi-size table rests on - against the 313 and the 60.6 percent of
    aggressive volume the ruling was originally made on.
    """
    committed = [node for node in export.nodes if selected(node, walked)]
    menus = Counter(tuple(action.kind for action in node.actions) for node in committed)
    kinds = [{action.kind for action in node.actions} for node in committed]

    assert menus == {
        ("fold", "call"): 50,
        ("fold", "call", "raise", "jam"): 20,
        ("fold", "call", "jam"): 15,
        ("fold", "raise", "jam"): 1,
    }
    assert sum(menus.values()) == COMMITTED_NODES
    assert sum(1 for menu in kinds if "raise" in menu and "jam" in menu) == 21
    assert sum(1 for menu in kinds if "jam" in menu and "raise" not in menu) == 15
    assert sum(1 for menu in kinds if menu == {"fold", "call"}) == 50
    # Every menu offers a fold, which is what makes "played rather than folded" a quantity
    # the dominance measurements can be taken in at all.
    for menu in kinds:
        assert "fold" in menu


# --- The three-way census, over two closed vocabularies ---


def test_the_three_buckets_account_for_every_node_the_source_card_publishes(
    export: SolverExport, walked, counted, derived
) -> None:
    """Committed, excluded, inexpressible - and nothing falls between them.

    The total is checked against the source card rather than the export object, because the
    card is what a reader of the report has: a converter that skipped a subtree would balance
    its own books and still not match the card. Every other denominator is recomputed here.
    """
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)
    selection = sum(1 for node in export.nodes if selected(node, walked))
    excluded = sum(counted.excluded.values())
    inexpressible = sum(counted.inexpressible.values())

    assert counted.total == card["node_counts"]["exported"]
    assert counted.total == EXPORTED_NODES
    assert counted.committed + excluded + inexpressible == counted.total
    assert counted.committed == selection == COMMITTED_NODES
    assert excluded + inexpressible == counted.total - selection
    assert set(counted.excluded) == set(lookup.DERIVATION_EXCLUSION_CODES)
    assert set(counted.inexpressible).issubset(lookup.DERIVATION_INEXPRESSIBILITY_CODES)
    assert derived.census.committed == counted.committed
    assert dict(derived.census.excluded) == dict(counted.excluded)


def test_the_two_exclusion_reasons_partition_the_excluded_nodes(
    export: SolverExport, walked, counted
) -> None:
    """Decision 8's amendment: two codes, and which node lands under which.

    One code cannot say which of the 38,742 come back when GTOpen can price multiway, which
    is why there are two. They do not overlap: a node with a multiway terminal still
    reachable is filed under the mispricing, and what is left is the 5,386 that are heads-up
    from here on and were reached through a cold call. So the mispricing bucket is exactly
    the complement of the subtree clause - including the 24 the 2026-08-25 ruling dropped,
    which is how a later phase finds them by name - and the other bucket is exactly the nodes
    that pass the subtree clause and fail the history one.
    """
    mispriced = {node.path for node in export.nodes if not subtree_clause(node, walked)}
    outside = {
        node.path
        for node in export.nodes
        if subtree_clause(node, walked) and not history_clause(node, walked)
    }
    committed = {node.path for node in export.nodes if selected(node, walked)}

    assert len(mispriced) == MISPRICED_NODES
    assert len(outside) == OUTSIDE_RULE_NODES
    assert mispriced.isdisjoint(outside)
    assert len(mispriced | outside | committed) == EXPORTED_NODES

    assert counted.excluded == {
        lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: MISPRICED_NODES,
        lookup.DERIVATION_OUTSIDE_SELECTION_RULE: OUTSIDE_RULE_NODES,
    }
    # The 24 are inside the mispricing bucket rather than beside it, which is the point of
    # the precedence: they are outside the rule *because* the source misprices them.
    dropped = {
        node.path
        for node in export.nodes
        if history_clause(node, walked) and not subtree_clause(node, walked)
    }
    assert len(dropped) == HISTORY_BUT_NOT_CLEAN
    assert dropped <= mispriced


def test_each_node_is_given_the_reason_that_names_what_is_wrong_with_it(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode], walked
) -> None:
    """The code per node, not merely the totals, because two wrong buckets can sum right.

    Three named nodes carry the distinction. The lojack's own open is heads-up by history and
    misprices, so it takes the mispricing code - the ruled cost in one key, a range the bot
    answers today and refuses after the cutover. The cold-called node is priced exactly from
    here on and takes the other code. The big blind against a button open takes neither.
    """
    code_for = derivation().exclusion_code
    misprices = lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY
    outside = lookup.DERIVATION_OUTSIDE_SELECTION_RULE

    assert code_for(by_path, by_path[LOJACK_OPEN_PATH]) == misprices
    assert code_for(by_path, by_path[COLD_CALLED_PATH]) == outside
    assert code_for(by_path, by_path[TRACED_PATH]) is None

    for node in export.nodes:
        code = code_for(by_path, node)
        if selected(node, walked):
            assert code is None, node.path
        elif not subtree_clause(node, walked):
            assert code == misprices, node.path
        else:
            assert code == outside, node.path


def test_both_reason_vocabularies_are_closed_and_enumerated_here() -> None:
    """The contract asks for "a closed vocabulary the phase's tests enumerate".

    Enumerated literally, so a code added without a ruling fails this file rather than
    passing quietly. The closure stops a node the converter merely failed to handle being
    filed as a property of the grammar. No census fixture on purpose: this is the vocabulary,
    and it runs whether or not the converter does. `DERIVATION_BELOW_REACH_FLOOR` is asserted
    gone, because decision 1's floor is retired and a code nothing files tells a reader a
    selection rule that is not the one in force.
    """
    misprices = lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY
    outside = lookup.DERIVATION_OUTSIDE_SELECTION_RULE
    no_key = lookup.DERIVATION_NO_LEGAL_SPOT_KEY
    everything = lookup.DERIVATION_EXCLUSION_CODES + lookup.DERIVATION_INEXPRESSIBILITY_CODES

    assert misprices == "derivation:source-misprices-multiway"
    assert outside == "derivation:outside-selection-rule"
    assert no_key == "derivation:no-legal-spot-key"
    assert set(lookup.DERIVATION_EXCLUSION_CODES) == {misprices, outside}
    assert lookup.DERIVATION_INEXPRESSIBILITY_CODES == (no_key,)
    assert not hasattr(lookup, "DERIVATION_BELOW_REACH_FLOOR")
    for code in everything:
        assert NAMESPACED_CODE.fullmatch(code), code
        assert code.split(":")[0] == "derivation"
    # They live beside the refusal codes and must not shadow one: a reader meeting
    # `lookup:` knows a query was refused, and `derivation:` that a node never shipped.
    assert set(everything).isdisjoint(MISS_CODES)
    for code in MISS_CODES:
        assert NAMESPACED_CODE.fullmatch(code), code


def test_nothing_in_the_committed_export_is_inexpressible(
    export: SolverExport, walked, counted
) -> None:
    """Zero is a result here, not an omission.

    Measured: all 38,828 nodes derive a valid v2 spot key, zero collisions - a clean
    bijection. Expressibility was never the constraint here; the selection rule does all the
    selecting. The bucket exists anyway, for a later export that may not be so clean.
    """
    keys = {key_of(node, walked) for node in export.nodes}

    assert sum(counted.inexpressible.values()) == 0
    assert len(keys) == export.node_count


# --- The walk: whose action is it, and what does it become ---


def test_the_actor_of_an_action_is_the_parent_node_s(
    by_path: dict[tuple[int, ...], SolverNode],
) -> None:
    """The single most likely conversion defect, and it is silent.

    An action recorded at a node was taken by whoever was to act *at that node*, the parent
    of the node it leads to. Read the actor off the child instead and every action shifts one
    seat down the ring - the lojack's open becomes the hijack's - keying a spot that never
    happened while validating perfectly. The subject is a three-actor node on purpose, and it
    is not a committed spot: the walk runs over the whole tree because the census does, and a
    node with two opponents invested is the only place three distinct actors can be found.
    """
    node = by_path[THREE_ACTOR_PATH]
    assert node.actor_pos == "BTN"

    walked = derivation().node_action_sequence(by_path, node)

    assert walked == THREE_ACTOR_SEQUENCE
    assert [entry.position for entry in walked] == ["LJ", "HJ", "CO"]
    assert spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, walked) == THREE_ACTOR_KEY

    # The confusion spelled out, so this test is known to discriminate: taking each actor
    # from the node the action leads to shifts the sequence one seat down the ring and
    # leaves the button calling before anybody has asked it to act.
    shifted = tuple(
        PreflopAction(by_path[THREE_ACTOR_PATH[: index + 1]].actor_pos, entry.action, entry.size_bb)
        for index, entry in enumerate(walked)
    )
    assert shifted != walked
    with pytest.raises(ValueError):
        spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, shifted)


def test_folds_never_enter_the_sequence(by_path: dict[tuple[int, ...], SolverNode]) -> None:
    """An empty sequence means folded to hero, so a recorded fold would be a second
    spelling of the same spot and the two would key differently.

    This node is reached through four folds and three live actions; only the three live
    ones survive the walk. Which node that is depends on the tree's shape rather than on
    the solve, so the permitted re-solve cannot take the test's subject away.
    """
    node = by_path[COLD_CALLED_PATH]
    folds = sum(
        1
        for index in range(len(COLD_CALLED_PATH))
        if by_path[COLD_CALLED_PATH[:index]].actions[COLD_CALLED_PATH[index]].kind == "fold"
    )
    assert folds == COLD_CALLED_FOLDS

    walked = derivation().node_action_sequence(by_path, node)

    assert walked == COLD_CALLED_SEQUENCE
    assert all(entry.action in ("call", "raise") for entry in walked)
    assert spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, walked) == COLD_CALLED_KEY


def test_one_export_node_traced_to_its_artifact_row(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """The end-to-end conversion the contract asks a non-coding reviewer to follow.

    Node (0, 0, 0, 1, 0). Three folds, the button opens to 2.5, the small blind folds, and
    the big blind closes the action holding aces. Its four offers are fold, call, a
    three-bet to 7.5 and the stack; the artifact holds what hero does rather than at what
    price, so the aggressive offers add into one raise weight and the call passes through.
    The numbers are read off the node, because what the solver plays with aces there is a
    solve measurement rather than something this file remembers.
    """
    node = by_path[TRACED_PATH]
    weights = {
        action.kind: node.weight_bp(index, "AA") for index, action in enumerate(node.actions)
    }

    assert node.actor_pos == "BB"
    assert [action.kind for action in node.actions] == TRACED_ACTION_KINDS
    assert derivation().node_action_sequence(by_path, node) == TRACED_SEQUENCE
    assert spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, TRACED_SEQUENCE) == TRACED_KEY

    row = derived.artifact_payload["action_weights"][TRACED_KEY]["AA"]

    assert row["call"] == pytest.approx(weights["call"] / QUANTISATION_SCALE, abs=1e-6)
    assert row["raise"] == pytest.approx(
        (weights["raise"] + weights["jam"]) / QUANTISATION_SCALE, abs=1e-6
    )
    assert row.get("fold", 0.0) == pytest.approx(weights["fold"] / QUANTISATION_SCALE, abs=1e-6)
    assert sum(row.values()) == pytest.approx(1.0, abs=1e-6)
