"""Phase 14: which solved nodes become spots, and how one node becomes one row.

Authored at stage 4, before the converter exists, so this file is the specification the
builder has to satisfy rather than a description of what got built. It covers the three
things the contract puts at the centre of the phase: the predicate that decides which of
the export's action nodes become committed chart spots, the three-way census that proves
none of them went missing on the way, and the conversion of one export node into one
artifact row.

Nothing here is checked against a number this repo remembered about a solve, because
decision 2 permits one re-solve and this file is frozen at stage 5. `REACH_FLOOR_BP` is
decision 1's ruling and is pinned as one; every count, weight and reach figure is
recomputed from whatever export is committed. The one exception is the node count, a fact
about the tree the ruled config builds rather than about the solve that ran over it. What
a moved count must never do is send anybody back to re-tighten the floor: the contract
calls a selection that no longer fits the 20 MB cap a halt and a return to the decision
list, because a rule adjusted to make the file fit is a rule the poker did not pick.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from array import array

import pytest

# `lookup` twice on purpose: by name for the codes it already publishes, and as a module
# for the four `DERIVATION_*` codes decision 8 adds at stage 6. Naming those today would
# fail the whole import block and hide every assertion in this file behind one error.
from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    RULED_CONFIG,
    SolverAction,
    SolverExport,
    SolverNode,
    class_combos,
    gtopen_class_index,
    load_solver_export,
    load_source_card,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.importer import import_preflop_artifact
from poker_training_bot.solver_artifacts.lookup import (
    MISS_CODES,
    MISS_SPOT_NOT_COVERED,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key
from scripts.repo_paths import REPO_ROOT

PREFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
EXPECTATIONS_PATH = PREFLOP_DIR / "expectations" / "six_max_nl25_100bb.json"
CONVERTER = REPO_ROOT / "scripts" / "convert_preflop_export.py"

TABLE_SIZE = 6
DEPTH_BB = 100

# The shape `lookup.py` already uses for every refusal it publishes. Decision 8 puts the
# derivation codes in the same one, so a reader meets one vocabulary rather than two.
NAMESPACED_CODE = re.compile(r"\A[a-z]+:[a-z0-9-]+\Z")

# The one figure this file pins, and a fact about the tree rather than about the solve:
# decision 2 permits a re-solve at the ruled config and nothing else, so GTOpen builds the
# identical action tree and only the strategies and the reach move. Every path, key and
# price below is a tree fact for the same reason.
EXPORTED_NODES = 38_828

# LJ opens to 2.5, HJ three-bets to 7.5, the cutoff flats, and the button is to act. Three
# actions by three different players, which is what makes it the trace the contract asks
# for: the actor of an action is the player who was to act *before* it.
TRACED_PATH = (1, 2, 1)
TRACED_KEY = "t6/d100/BTN/LJ:raise@2.5,HJ:raise@7.5,CO:call"
TRACED_SEQUENCE = (
    PreflopAction("LJ", "raise", 2.5),
    PreflopAction("HJ", "raise", 7.5),
    PreflopAction("CO", "call"),
)
TRACED_ACTION_KINDS = ["fold", "call", "raise", "jam"]
TRACED_NAMED_RAISE_BB = 22.5

# The same line one action later, with the cutoff four-betting to 22.5 instead of
# flatting. The button's only aggressive option there is the whole stack, which is the
# case decision 6 exists for and the case the GTO Wizard source never produced.
JAM_ONLY_PATH = (1, 2, 2)
JAM_ONLY_KEY = "t6/d100/BTN/LJ:raise@2.5,HJ:raise@7.5,CO:raise@22.5"

# Folded to the button, which opens; the small blind flats; the big blind three-bets to 7.5
# and the small blind is to act. Four folds and three live actions, which is a shape fact
# and survives the re-solve. Nothing about its reach is asserted.
FOLD_HEAVY_PATH = (0, 0, 0, 1, 1, 2, 0)
FOLD_HEAVY_KEY = "t6/d100/SB/BTN:raise@2.5,SB:call,BB:raise@7.5"
FOLD_HEAVY_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("SB", "call"),
    PreflopAction("BB", "raise", 7.5),
)
FOLD_HEAVY_FOLDS = 4


# --- fixtures, and the definitions this file refuses to import ---


def derivation():
    """The module stage 6 writes, imported inside the call rather than at module scope.

    A module-scope import of a module that does not exist yet stops the whole file
    collecting, hiding every assertion behind one ImportError - the gap
    `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` names. A function-body import is also
    left alone by isort, so this lints identically before and after stage 6.
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


def measured_reach_bp(node: SolverNode) -> float:
    """Arriving reach spelled out here rather than imported from the module under test.

    A check comparing two copies of one rule cannot show the rule is right. This is the
    plain mean over the 169 hand classes of the fraction of hero's range that gets to the
    node, in basis points, read straight off the node's own row.
    """
    return sum(node.reach_bp) / 169.0


def combo_weighted_reach_bp(node: SolverNode) -> float:
    """The same figure weighted by combinations - the plausible other definition."""
    pairs = [(node.reach_bp[gtopen_class_index(n)], class_combos(n)) for n in HAND_CLASSES]
    return sum(reach * combos for reach, combos in pairs) / sum(c for _, c in pairs)


def has_raise_weight(row: dict[str, dict[str, float]]) -> bool:
    """True when any hand class at this spot puts weight on raising."""
    return any(weights.get("raise", 0.0) > 0.0 for weights in row.values())


# --- Decision 1: the predicate that decides what gets committed ---


def test_the_floor_is_the_ruled_two_percent_of_heros_range() -> None:
    """Two percent of hero's range, in the basis points the export stores reach in.
    A constant that has drifted to any other number is a different chart.
    """
    assert derivation().REACH_FLOOR_BP == 200
    assert derivation().REACH_FLOOR_BP == round(0.02 * QUANTISATION_SCALE)


def test_arriving_reach_is_the_plain_mean_over_the_169_classes(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode]
) -> None:
    """The definition, checked against the export rather than against itself.

    One named node is recomputed by hand from its own `reach_bp` row, then every node in
    the tree is. Where the two candidate definitions disagree most is found at run time,
    because how far apart they get is a property of the solve; what must hold is that they
    are distinguishable at all, so averaging by combinations cannot pass unnoticed.
    """
    widest = max(
        export.nodes, key=lambda node: abs(measured_reach_bp(node) - combo_weighted_reach_bp(node))
    )
    assert abs(measured_reach_bp(widest) - combo_weighted_reach_bp(widest)) > 1.0

    named = by_path[FOLD_HEAVY_PATH]
    assert derivation().node_reach_bp(named) == pytest.approx(sum(named.reach_bp) / 169.0)
    for node in export.nodes:
        assert abs(derivation().node_reach_bp(node) - measured_reach_bp(node)) < 1e-6, node.path


def test_the_floor_bites_without_selecting_the_whole_tree(export: SolverExport) -> None:
    """The distribution decision 1 was ruled against, re-measured from the export.

    The count the floor produces is NOT the ruling and is not asserted. Decision 1 was
    ruled as a predicate precisely so that four later rulings moving the number is no
    reason to re-tighten the floor, and a count that stops fitting under the 20 MB cap is
    a halt and a return to the decision list rather than a test to repair. What is
    asserted is that the predicate is a threshold at all: it keeps something, it drops
    something, and halving it - one percent, the first floor the contract's table says
    does not fit the budget - keeps strictly more. A floor selecting the whole tree is a
    no-op dressed as a rule, and that is caught without remembering a count.
    """
    assert export.node_count == EXPORTED_NODES

    floor = derivation().REACH_FLOOR_BP
    at_the_floor = sum(1 for node in export.nodes if measured_reach_bp(node) >= floor)
    at_half_the_floor = sum(1 for node in export.nodes if measured_reach_bp(node) >= floor / 2)

    assert 0 < at_the_floor < at_half_the_floor < export.node_count


def test_the_committed_spots_are_exactly_what_the_predicate_selects(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """The artifact holds the predicate's answer, not a subset chosen somewhere else.

    Computed from the export by hand here, then compared against what the converter
    emitted, so a converter that dropped an awkward spot fails even though its own census
    still adds up. The five folded-to-hero spots are named because losing an open to an
    arithmetic accident is the chart refusing the commonest decision made.
    """
    expected = {
        spot_key(
            TABLE_SIZE, DEPTH_BB, node.actor_pos, derivation().node_action_sequence(by_path, node)
        )
        for node in export.nodes
        if measured_reach_bp(node) >= derivation().REACH_FLOOR_BP
    }
    committed = set(derived.artifact_payload["action_weights"])

    assert committed == expected
    for position in ("LJ", "HJ", "CO", "BTN", "SB"):
        assert f"t{TABLE_SIZE}/d{DEPTH_BB}/{position}/rfi" in committed


# --- The three-way census, over two closed vocabularies ---


def test_the_three_buckets_account_for_every_node_the_source_card_publishes(
    export: SolverExport, counted, derived
) -> None:
    """Committed, excluded, inexpressible - and nothing falls between them.

    The total is checked against the source card rather than the export object, because
    the card is what a reader of the report has: a converter that quietly skipped a
    subtree would balance its own books and still not match the card. Every other
    denominator is recomputed from the export here, so a re-solve moves both sides.
    """
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)
    floor = derivation().REACH_FLOOR_BP
    selected = sum(1 for node in export.nodes if measured_reach_bp(node) >= floor)
    excluded = sum(counted.excluded.values())
    inexpressible = sum(counted.inexpressible.values())

    assert counted.total == card["node_counts"]["exported"]
    assert counted.total == EXPORTED_NODES
    assert counted.committed + excluded + inexpressible == counted.total
    assert counted.committed == selected
    assert excluded + inexpressible == counted.total - selected
    assert set(counted.excluded) == {lookup.DERIVATION_BELOW_REACH_FLOOR}
    assert set(counted.inexpressible).issubset(lookup.DERIVATION_INEXPRESSIBILITY_CODES)
    assert derived.census.committed == counted.committed
    assert dict(derived.census.excluded) == dict(counted.excluded)


def test_both_reason_vocabularies_are_closed_and_enumerated_here() -> None:
    """The contract asks for "a closed vocabulary the phase's tests enumerate".

    Enumerated literally, so a code added without a ruling fails this file rather than
    passing quietly. The closure is what stops a node the converter merely failed to
    handle being filed as a property of the grammar. No census fixture on purpose: this is
    the vocabulary, and it runs whether or not the converter does.
    """
    below = lookup.DERIVATION_BELOW_REACH_FLOOR
    no_key = lookup.DERIVATION_NO_LEGAL_SPOT_KEY
    everything = lookup.DERIVATION_EXCLUSION_CODES + lookup.DERIVATION_INEXPRESSIBILITY_CODES

    assert below == "derivation:below-reach-floor"
    assert no_key == "derivation:no-legal-spot-key"
    assert lookup.DERIVATION_EXCLUSION_CODES == (below,)
    assert lookup.DERIVATION_INEXPRESSIBILITY_CODES == (no_key,)
    for code in everything:
        assert NAMESPACED_CODE.fullmatch(code), code
        assert code.split(":")[0] == "derivation"
    # They live beside the refusal codes and must not shadow one: a reader meeting
    # `lookup:` knows a query was refused, and `derivation:` that a node never shipped.
    assert set(everything).isdisjoint(MISS_CODES)
    for code in MISS_CODES:
        assert NAMESPACED_CODE.fullmatch(code), code


def test_nothing_in_the_committed_export_is_inexpressible(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode], counted
) -> None:
    """Zero is a result here, not an omission.

    Measured: all 38,828 nodes derive a valid v2 spot key, zero collisions - a clean
    bijection. Expressibility was never the constraint on this phase and the reach floor
    does all of the selecting. The bucket exists anyway, because a later export at another
    depth or table size may not be so clean.
    """
    keys = {
        spot_key(
            TABLE_SIZE, DEPTH_BB, node.actor_pos, derivation().node_action_sequence(by_path, node)
        )
        for node in export.nodes
    }

    assert sum(counted.inexpressible.values()) == 0
    assert len(keys) == export.node_count


# --- The walk: whose action is it, and what does it become ---


def test_the_actor_of_an_action_is_the_parent_node_s(
    by_path: dict[tuple[int, ...], SolverNode],
) -> None:
    """The single most likely conversion defect, and it is silent.

    An action recorded at a node was taken by whoever was to act *at that node*, which is
    the parent of the node it leads to. Read the actor off the child instead and every
    action shifts one seat down the ring - the lojack's open becomes the hijack's - keying
    a spot that never happened while validating perfectly.
    """
    node = by_path[TRACED_PATH]
    assert node.actor_pos == "BTN"

    walked = derivation().node_action_sequence(by_path, node)

    assert walked == TRACED_SEQUENCE
    assert [entry.position for entry in walked] == ["LJ", "HJ", "CO"]

    # The confusion spelled out, so this test is known to discriminate: taking each actor
    # from the node the action leads to shifts the sequence one seat down the ring and
    # leaves the button calling before anybody has asked it to act.
    shifted = tuple(
        PreflopAction(by_path[TRACED_PATH[: index + 1]].actor_pos, entry.action, entry.size_bb)
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
    node = by_path[FOLD_HEAVY_PATH]
    folds = sum(
        1
        for index in range(len(FOLD_HEAVY_PATH))
        if by_path[FOLD_HEAVY_PATH[:index]].actions[FOLD_HEAVY_PATH[index]].kind == "fold"
    )
    assert folds == FOLD_HEAVY_FOLDS

    walked = derivation().node_action_sequence(by_path, node)

    assert walked == FOLD_HEAVY_SEQUENCE
    assert all(entry.action in ("call", "raise") for entry in walked)
    assert spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, walked) == FOLD_HEAVY_KEY


def test_one_export_node_traced_to_its_artifact_row(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """The end-to-end conversion the contract asks a non-coding reviewer to follow.

    Node (1, 2, 1). LJ opened to 2.5, the hijack three-bet to 7.5, the cutoff called, and
    the button holds aces. Its four offers are fold, call, a four-bet to 22.5 and the
    stack; the artifact holds what hero does rather than at what price, so the aggressive
    offers add into one raise weight and the call passes through. The numbers are read off
    the node, because what the solver plays with aces there is a solve measurement.
    """
    node = by_path[TRACED_PATH]
    weights = {
        action.kind: node.weight_bp(index, "AA") for index, action in enumerate(node.actions)
    }

    assert node.actor_pos == "BTN"
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


# --- Decision 6: a shove is a raise priced at hero's whole stack ---


def test_a_jam_only_spot_is_priced_at_heros_whole_stack(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """Decision 6, and the case the GTO Wizard source this repo converted never had.

    Facing the cutoff's four-bet to 22.5, the button may fold, call, or shove; there is no
    named raise to take a price from. Import the old rule unchanged and the chart says
    raise and cannot say how much. The ruling prices it at the stack.
    """
    node = by_path[JAM_ONLY_PATH]
    sizes = derived.sizing_payload["raise_to_bb"]
    kinds = {action.kind for action in node.actions}

    assert "jam" in kinds and "raise" not in kinds
    assert JAM_ONLY_KEY in derived.artifact_payload["action_weights"]
    assert sizes[JAM_ONLY_KEY] == pytest.approx(float(DEPTH_BB))
    assert sizes[JAM_ONLY_KEY] == pytest.approx(RULED_CONFIG["stack"])

    # And the ruling reaches no further than it was ruled: where a named raise exists the
    # size is still the solved price, not the stack.
    assert sizes[TRACED_KEY] == pytest.approx(TRACED_NAMED_RAISE_BB)


def test_a_spot_absent_from_the_sizing_table_has_no_size_to_hold(derived) -> None:
    """The note decision 6 promised, in the form this export makes it true in.

    Every committed spot where hero can put chips in carries a price. The spots absent
    from the table are those where hero's only options are fold and call - facing a shove,
    or after the raise cap - so there is nothing to price and nothing to invent.
    """
    sizes = derived.sizing_payload["raise_to_bb"]
    rows = derived.artifact_payload["action_weights"]
    priced = {key for key, row in rows.items() if has_raise_weight(row)}
    unpriced = {key for key, row in rows.items() if not has_raise_weight(row)}

    assert priced <= set(sizes)
    assert set(sizes) <= set(rows)
    assert unpriced.isdisjoint(sizes)
    assert priced and unpriced


def test_a_jam_and_a_named_raise_collapse_into_one_raise_whose_parts_add(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """`PREFLOP_ACTIONS` holds one raise, so the two offers cannot both survive.

    Their weights add because the artifact holds what hero does rather than at what price.
    Dropping the shove would leave a row that does not sum to one and a button folding
    aces to a four-bet.
    """
    node = by_path[TRACED_PATH]
    named = [index for index, action in enumerate(node.actions) if action.kind == "raise"]
    jams = [index for index, action in enumerate(node.actions) if action.kind == "jam"]

    assert len(named) == 1 and len(jams) == 1

    row = derived.artifact_payload["action_weights"][TRACED_KEY]
    for hand_class in ("AA", "KK", "AKs"):
        named_bp = node.weight_bp(named[0], hand_class)
        jam_bp = node.weight_bp(jams[0], hand_class)
        assert jam_bp > 0, hand_class
        assert row[hand_class]["raise"] == pytest.approx(
            (named_bp + jam_bp) / QUANTISATION_SCALE, abs=1e-6
        ), hand_class
        assert row[hand_class]["raise"] > named_bp / QUANTISATION_SCALE, hand_class


# --- The sizes come from the export's own labels, proved by perturbing them ---

FOLD = SolverAction("Fold", "fold", 0.0, True)


def uniform_node(
    path: tuple[int, ...], actor: str, actions: list[SolverAction], split: tuple[int, ...]
) -> SolverNode:
    """A node whose every hand class plays the same mix and arrives in full.

    The same trade `tests/test_solver_export.py` makes for its own fixtures: real
    strategies vary by class, and these exist to exercise a converter rather than to be
    poker. Full reach keeps every node above the floor, so the tests see the conversion.
    """
    return SolverNode(
        path,
        actor,
        tuple(actions),
        tuple(array("H", [weight] * 169) for weight in split),
        array("H", [QUANTISATION_SCALE] * 169),
    )


def synthetic_export(open_to: float) -> SolverExport:
    """The smallest tree that carries an opening price: LJ opens, HJ answers.

    The lojack may fold or open, so the folded-to-hero spot carries no call weight and the
    no-limp rule holds by construction rather than by luck. `config` stays the ruled one
    while the labels move, which is deliberate: a converter reading
    `config["open_raises"][0]` is as hardcoded as one with 2.5 written into it.
    """
    opening = SolverAction(f"Raise {open_to}", "raise", open_to, False)
    call = SolverAction(f"Call {open_to}", "call", open_to, True)
    return SolverExport.from_nodes(
        [
            uniform_node((), "LJ", [FOLD, opening], (3_000, 7_000)),
            uniform_node((1,), "HJ", [FOLD, call], (6_000, 4_000)),
        ],
        config=dict(RULED_CONFIG),
        positions=list(RULED_CONFIG["positions"]),
    )


def test_the_synthetic_export_is_a_tree_the_reader_accepts() -> None:
    """The fixture below is evidence only if it is a real export.

    If `from_nodes` rejected it, the perturbation test would be red for a reason with
    nothing to do with the converter, and would go green the day somebody loosened the
    reader.
    """
    export = synthetic_export(2.5)

    assert export.node_count == 2
    assert export.node(()).actor_pos == "LJ"
    assert [action.label for action in export.node(()).actions] == ["Fold", "Raise 2.5"]


@pytest.mark.parametrize("open_to", [2.5, 3.75, 4.0])
def test_the_converter_reads_its_sizes_from_the_export_s_own_labels(open_to: float) -> None:
    """The contract's unfalsifiability criterion, and the hardest thing in this file.

    The solved config has one opening size and one raise multiplier, so a converter with
    the prices written into it produces a byte-identical artifact and passes every other
    test here. Perturbing the label is the only thing that tells the two apart. 2.5 is the
    control - if the perturbed cases pass and it fails, prices are transformed, not read.
    """
    chart = derivation().derive_chart(synthetic_export(open_to))
    rfi_key = f"t{TABLE_SIZE}/d{DEPTH_BB}/LJ/rfi"
    facing_key = f"t{TABLE_SIZE}/d{DEPTH_BB}/HJ/LJ:raise@{open_to:g}"

    assert set(chart.artifact_payload["action_weights"]) == {rfi_key, facing_key}
    assert chart.sizing_payload["raise_to_bb"][rfi_key] == pytest.approx(open_to)
    assert chart.census.committed == 2
    assert sum(chart.census.excluded.values()) == 0
    assert sum(chart.census.inexpressible.values()) == 0


def test_two_prices_produce_two_different_charts() -> None:
    """Stated as a difference, because "the key holds 3.75" could still be a constant.

    The same converter over the same tree at two prices must disagree in exactly one
    place, and the sizing table has to move with the key. A converter that keyed off the
    label but priced off a constant passes the test above and fails this one.
    """
    solved = derivation().derive_chart(synthetic_export(2.5))
    perturbed = derivation().derive_chart(synthetic_export(3.75))
    solved_keys = set(solved.artifact_payload["action_weights"])
    perturbed_keys = set(perturbed.artifact_payload["action_weights"])
    rfi_key = f"t{TABLE_SIZE}/d{DEPTH_BB}/LJ/rfi"

    assert solved_keys - perturbed_keys == {f"t{TABLE_SIZE}/d{DEPTH_BB}/HJ/LJ:raise@2.5"}
    assert perturbed_keys - solved_keys == {f"t{TABLE_SIZE}/d{DEPTH_BB}/HJ/LJ:raise@3.75"}
    assert solved.sizing_payload["raise_to_bb"][rfi_key] == pytest.approx(2.5)
    assert perturbed.sizing_payload["raise_to_bb"][rfi_key] == pytest.approx(3.75)


def test_a_node_the_converter_cannot_handle_raises_rather_than_being_filed() -> None:
    """The closure is load-bearing or it is decoration.

    An action kind nothing in this repo has a rule for is not "inexpressible in the spot
    vocabulary" - it is a converter meeting something it does not understand, and filing it
    as a property of the grammar would turn a bug into a documented limitation. The export
    reader accepts the tree, since it validates a tree's shape rather than the poker
    vocabulary of its labels, so the converter must refuse. The error must name the kind: a
    blanket `except ValueError` filing everything under `derivation:no-legal-spot-key` is
    exactly the defect guarded against.
    """
    straddle = SolverAction("Straddle 2", "straddle", 0.0, False)
    call = SolverAction("Call 2", "call", 2.0, True)
    export = SolverExport.from_nodes(
        [
            uniform_node((), "LJ", [FOLD, straddle], (3_000, 7_000)),
            uniform_node((1,), "HJ", [FOLD, call], (6_000, 4_000)),
        ],
        config=dict(RULED_CONFIG),
        positions=list(RULED_CONFIG["positions"]),
    )

    with pytest.raises(ValueError, match="straddle"):
        derivation().census(export)
    with pytest.raises(ValueError, match="straddle"):
        derivation().derive_chart(export)


# --- An excluded node is a refusal at the table, never a neighbouring cell ---


@pytest.fixture(scope="module")
def committed_library(derived, tmp_path_factory) -> PreflopChartLibrary:
    """The derived artifact, written out and imported the way the runtime imports it.

    Going through the importer rather than the payload dict is the point: a library built
    from what the converter emitted is what the bot answers from, and anything the
    importer would reject never reaches a query.
    """
    directory = tmp_path_factory.mktemp("derived-chart")
    path = directory / "six_max_100bb_rakefree.json"
    text = json.dumps(derived.artifact_payload, indent=2, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return PreflopChartLibrary.from_artifacts([import_preflop_artifact(path)])


@pytest.fixture(scope="module")
def excluded_probe(export: SolverExport, by_path: dict[tuple[int, ...], SolverNode]):
    """The node the floor drops hardest, found rather than named.

    Naming a path would pin its reach, and a tighter gap could lift it over the floor, at
    which point the refusal test still passes while its subject has quietly become a
    committed spot. The lowest-reach node cannot go stale, and the test asserts the margin
    it relies on rather than assuming it.
    """
    node = min(export.nodes, key=lambda item: (measured_reach_bp(item), item.path))
    sequence = derivation().node_action_sequence(by_path, node)
    return node, spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, sequence), sequence


def test_an_excluded_node_is_refused_and_a_committed_one_is_answered(
    committed_library: PreflopChartLibrary, excluded_probe
) -> None:
    """The whole point of the exclusion, asked as a query rather than asserted as prose.

    A line hero's range essentially never reaches. It is a legal spot with a legal key and
    the solver's ranges for it were never committed, so the bot must say so: answering
    from a neighbouring cell - the same three-bet without the flat - would be a range hero
    never had and nothing downstream could tell. The traced spot is asked in the same
    breath, because a chart that refused everything would satisfy the first half; its
    exact weights are the previous test's subject, so only presence is checked here.
    """
    node, key, sequence = excluded_probe
    query = ChartQuery(TABLE_SIZE, DEPTH_BB, node.actor_pos, sequence, "AA")
    refused = committed_library.lookup(query)
    answered = committed_library.lookup(
        ChartQuery(TABLE_SIZE, DEPTH_BB, "BTN", TRACED_SEQUENCE, "AA")
    )

    assert derivation().node_reach_bp(node) < derivation().REACH_FLOOR_BP
    assert query.spot_key == key
    assert key not in committed_library.spot_keys()
    assert isinstance(refused, ChartMiss)
    assert refused.code == MISS_SPOT_NOT_COVERED
    assert refused.code in MISS_CODES
    assert refused.spot_key == key
    assert key in refused.detail

    assert not isinstance(answered, ChartMiss), getattr(answered, "detail", "")
    assert answered.spot_key == TRACED_KEY
    assert answered.price_substitutions == ()
    assert dict(answered.action_weights)["raise"] > 0.0


# --- The external oracle is not regenerated by the thing it checks ---


def test_the_converter_does_not_write_the_expectations_file() -> None:
    """The contract's non-goal, asserted as behaviour rather than as intent.

    The expectations file holds "the only numbers in this phase that this repo did not
    produce", which is what catches a range that is uniformly wrong rather than merely
    self-consistent. A reference regenerated from what it checks cannot fail. The
    modification time is checked as well as the bytes, because a file rewritten with
    identical content has still been rewritten - and on the day the numbers behind it move
    it would be rewritten with different content and nobody would notice.
    """
    assert EXPECTATIONS_PATH.exists(), f"the external oracle is missing at {EXPECTATIONS_PATH}"
    before = EXPECTATIONS_PATH.read_bytes()
    before_mtime = EXPECTATIONS_PATH.stat().st_mtime_ns

    written = subprocess.run(
        [sys.executable, str(CONVERTER)], cwd=REPO_ROOT, capture_output=True, text=True
    )
    checked = subprocess.run(
        [sys.executable, str(CONVERTER), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert written.returncode == 0, written.stderr
    assert EXPECTATIONS_PATH.read_bytes() == before
    assert EXPECTATIONS_PATH.stat().st_mtime_ns == before_mtime
    assert checked.returncode == 0, checked.stdout + checked.stderr
