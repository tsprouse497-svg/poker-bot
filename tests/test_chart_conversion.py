"""Phase 14: what one committed export node costs, and where its price came from.

The companion to `tests/test_chart_derivation.py`, split from it at the 700-line cap. That file
owns *which* nodes get committed, and the named nodes and walk helpers this file imports rather
than copies. This one owns the price: the sizing table, the prices hero is offered, the
perturbation pair proving prices are read from the export's own labels, the refusal a withheld
node gets at the table, and the external oracle.

**The sizing table holds every raise size a spot offers, with the weight hero gives each, per
hand class** - decision 6, ruled 2026-08-23 and amended five times as the tree under it moved.
Over the **6** spots the four rulings commit, hero is offered exactly one price at each and two
at none, so the schema's headline case is unexercisable and its checks are labelled `VACUOUS`
rather than counted as passes: decision 6 says in terms that a check that cannot fail must not
be counted as one that passed. Three things carry that label - two prices at one spot, a jam
beside a named raise, and a committed spot that prices nothing.

**Two prices left the chart with the spots that quoted them.** Until 2026-09-01 fifteen
committed spots were hero facing a five-bet jam on a fold-or-call menu, the whole of decision
6's "a spot the table prices nothing at" half, and fifteen more were hero facing a three-bet,
the only spots quoting 22.5. Taylor withheld both, so hero's menu is 2.5 and 7.5 and nothing
else - the contract's "exactly `[2.5, 7.5, 22.5]`" is stale by one price.
"""

from __future__ import annotations

import json
import subprocess
import sys
from array import array
from collections import Counter

import pytest

# The sibling as a module rather than by name: two dozen node paths, keys, sequences and
# walk helpers, whose import block ran to a twenty-fifth of the line budget. `spec.` also
# says at each use that the fact came from the file where the predicate is on trial.
import test_chart_derivation as spec

from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    QUANTISATION_SCALE,
    RULED_CONFIG,
    SolverAction,
    SolverExport,
    SolverNode,
    gtopen_class_index,
    load_solver_export,
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
from poker_training_bot.solver_artifacts.schema import PreflopAction
from scripts.repo_paths import REPO_ROOT

PREFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
EXPECTATIONS_PATH = PREFLOP_DIR / "expectations" / "six_max_nl25_100bb.json"
CONVERTER = REPO_ROOT / "scripts" / "convert_preflop_export.py"

# Counted here as well as in the sibling, because two files reaching 6 independently is the
# check and importing the number would make it one file twice. `spec.selected` is all four
# rulings and means committed; `spec.predicate_selects` is decision 1 alone, which keeps 51.
PREDICATE_SPOTS = 51
THREE_BET_FACED_SPOTS = 15
FOUR_BET_FACED_SPOTS = 15
FIVE_BET_FACING_SPOTS = 15
COMMITTED_SPOTS = 6

# Tree facts. The open is 2.5 and `raise_mults` is 3.0, so hero's price is the open times the
# multiplier once per raise he faces - 2.5, 7.5, 22.5 - until the fourth, where 67.5 crosses
# `allin_threshold` and snaps to the stack. The chart keeps the first two rungs: 22.5 is only
# ever offered where hero faces a three-bet, and 100 only where he faces a four-bet.
HERO_PRICES = (2.5, 7.5)
SPOTS_OFFERING_PRICE = {2.5: 1, 7.5: 5}
FOUR_BET_PRICE = 22.5
STACK_BB = 100.0
COMMITTED_MENUS = {("call", "fold", "raise"): 5, ("fold", "raise"): 1}

# Walked out of the export: 6 priced spots carrying 320 class entries, every one a single price,
# and none with nothing to price. A build that kept the three-bet spots lands on 21 keys with
# 320 + 428 entries, one that kept the jams too on 36, and one that kept everything on 51.
SIZING_SCHEMA_VERSION = 2
PRICED_SPOTS = 6
UNPRICED_SPOTS = 0
ONE_PRICE_CLASS_ENTRIES = 320

# The two named spots: how many arriving classes take the one price each offers.
TRACED_PRICED_CLASSES = 47
SB_OPEN_PRICED_CLASSES = 121
PURE_CLASS = "AA"


def vacuous(what: str) -> None:
    """Stop the test and record it as skipped rather than passed.

    Decision 6, on the schema it keeps over data that cannot exercise it: "a check that cannot
    fail must not be counted as one that passed". The guard this repo usually writes -
    `assert found, "...otherwise vacuous"` - is the wrong tool, the case being ruled absent
    rather than accidentally absent, so it would be a permanent red against a chart the contract
    describes correctly. A skip is neither; every use sits after an assertion of the premise."""
    pytest.skip(f"VACUOUS over the committed {COMMITTED_SPOTS}: {what}")


@pytest.fixture(scope="module")
def export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def by_path(export: SolverExport) -> dict[tuple[int, ...], SolverNode]:
    return export.by_path()


@pytest.fixture(scope="module")
def derived(export: SolverExport):
    return spec.derivation().derive_chart(export)


@pytest.fixture(scope="module")
def walked(by_path: dict[tuple[int, ...], SolverNode]) -> dict:
    state = spec.walk_state(by_path)
    assert len(state) == len(by_path), "the walk did not reach every node"
    return state


def committed_keys(export: SolverExport, state) -> dict[str, SolverNode]:
    """The 21 the chart holds, keyed. `spec.selected` is all three rulings together."""
    return {spec.key_of(n, state): n for n in export.nodes if spec.selected(n, state)}


def withheld_keys(export: SolverExport, state, family: str) -> dict[str, SolverNode]:
    """One withheld family, keyed. `three-bet` is the 15 where hero's only aggressive answer is
    a four-bet to 22.5, `four-bet` the 15 where it is the stack, and `jam` the 15 where he
    answers that stack. Named rather than flagged, three families needing three names."""
    faces = {
        "three-bet": spec.faces_a_three_bet,
        "four-bet": spec.faces_a_four_bet,
        "jam": spec.faces_a_five_bet_jam,
    }[family]
    kept = (n for n in export.nodes if spec.predicate_selects(n, state))
    return {spec.key_of(n, state): n for n in kept if faces(n, state)}


def artifact_menu(node: SolverNode) -> tuple[str, ...]:
    """The node's offers in the artifact's vocabulary, where a jam is a raise."""
    return tuple(sorted({"raise" if a.kind == "jam" else a.kind for a in node.actions}))


def raising_classes(row: dict[str, dict[str, float]]) -> set[str]:
    """The classes at this spot that put any weight on raising."""
    return {n for n, weights in row.items() if weights.get("raise", 0.0) > 0.0}


def measured_class_sizes(node: SolverNode) -> dict[str, tuple[tuple[float, float], ...]]:
    """Every price hero may raise to here, per hand class, with his weight on each.
    Recomputed from the node, because which class takes which price is solve output and a test
    reading it from the table under test is one copy of a number agreeing with another. A class
    is read off its own row - no combo or reach weighting, both of which mix classes.
    """
    offers = [(i, a) for i, a in enumerate(node.actions) if a.kind in ("raise", "jam")]
    sized: dict[str, tuple[tuple[float, float], ...]] = {}
    for name in HAND_CLASSES:
        column = gtopen_class_index(name)
        if node.reach_bp[column] <= 0:
            continue
        volumes = [(action.to, node.strategy_bp[i][column]) for i, action in offers]
        total = sum(basis_points for _, basis_points in volumes)
        if total <= 0:
            continue
        sized[name] = tuple(sorted((to, bp / total) for to, bp in volumes if bp > 0))
    return sized


def priced_classes(sizing_payload: dict, key: str) -> dict[str, tuple[tuple[float, float], ...]]:
    """One spot's whole entry: every priced class, in the order the table stored them, read
    positionally - a reader that sorted cannot tell an unordered table from an ordered one."""
    return {
        hand_class: tuple((float(e["to_bb"]), float(e["weight"])) for e in entries)
        for hand_class, entries in sizing_payload["raise_to_bb"][key].items()
    }


def priced_entries(sizing_payload: dict, key: str, hand_class: str):
    """One class's prices at one spot: what `sizes_bb` is ruled to return."""
    return priced_classes(sizing_payload, key)[hand_class]


def entries_agree(
    entries: tuple[tuple[float, float], ...], measured: tuple[tuple[float, float], ...]
) -> bool:
    """Whether a class's entry matches a recomputed one, price by price and in order. The
    tolerance is tight because nothing rules this field may be rounded, and rounding would drop
    a price a class takes rarely, turning one the chart cannot price into one it can."""
    if len(entries) != len(measured):
        return False
    return all(
        price == pytest.approx(other_price)
        and weight == pytest.approx(other_weight, rel=1e-9, abs=1e-12)
        for (price, weight), (other_price, other_weight) in zip(entries, measured, strict=True)
    )


# --- What the committed 6 offer hero, and at what price ---


def test_every_price_the_export_offers_hero_is_in_the_table_with_his_weight_on_it(
    export: SolverExport, walked, derived
) -> None:
    """The ruling over all 6, with the price ladder it produces.

    Hero's price is the 2.5 open times the 3.0 multiplier once per raise in front of him, so the
    ladder is derived rather than listed. The chart keeps the first two rungs: the third, 22.5,
    is quoted only where hero faces a three-bet, and the fourth is 67.5 snapped to the stack by
    `allin_threshold` and quoted only where he faces a four-bet, both families being withheld.
    Every committed node is walked and every class recomputed. Each property hides a defect:
    prices drawn from the node's own offers and never repeated; ordered, so a reader can tell
    the small one without sorting; strictly positive; summing to one, so weights are shares of
    *that class's* volume."""
    open_to = float(RULED_CONFIG["open_raises"][0])
    multiplier = float(RULED_CONFIG["raise_mults"][0])
    sizes = derived.sizing_payload["raise_to_bb"]
    keyed = committed_keys(export, walked)
    lengths: Counter = Counter()
    spot_lengths: Counter = Counter()
    offered: Counter = Counter()

    for key, node in keyed.items():
        prices = {float(a.to) for a in node.actions if a.kind in ("raise", "jam")}
        measured = measured_class_sizes(node)
        rung = open_to * multiplier ** spec.raises_faced(node, walked)

        assert prices == {rung}, key
        assert measured, f"{key} offers a price and prices no class"
        for price in prices:
            offered[price] += 1
        table = priced_classes(derived.sizing_payload, key)
        assert set(table) == set(measured), key
        for hand_class, entries in table.items():
            quoted = [price for price, _ in entries]
            weights = [weight for _, weight in entries]

            assert entries_agree(entries, measured[hand_class]), (key, hand_class, entries)
            assert set(quoted) <= prices and len(set(quoted)) == len(quoted), (key, hand_class)
            assert quoted == sorted(quoted), (key, hand_class)
            assert all(weight > 0.0 for weight in weights), (key, hand_class)
            assert sum(weights) == pytest.approx(1.0, abs=1e-9), (key, hand_class)
            lengths[len(entries)] += 1
        spot_lengths[max(len(entries) for entries in table.values())] += 1

    assert derived.sizing_payload["schema_version"] == SIZING_SCHEMA_VERSION
    assert set(sizes) == set(keyed), "the table and the committed set differ"
    assert dict(offered) == SPOTS_OFFERING_PRICE
    assert tuple(sorted(offered)) == HERO_PRICES
    assert STACK_BB not in offered and FOUR_BET_PRICE not in offered
    assert lengths == {1: ONE_PRICE_CLASS_ENTRIES}
    assert spot_lengths == {1: PRICED_SPOTS}
    assert len(sizes) == PRICED_SPOTS == COMMITTED_SPOTS


@pytest.mark.parametrize(
    ("label", "path", "key", "kinds", "price", "priced"),
    [
        # The most-played decision in six-max: fold, flat, or three-bet to 7.5. With
        # `add_allin: false` there is no fourth offer, which is what emptied decision 6 out.
        ("the big blind closing against a button open", spec.TRACED_PATH, spec.TRACED_KEY,
         ["fold", "call", "raise"], 7.5, TRACED_PRICED_CLASSES),
        # The only opening range committed. The retired `add_allin: true` build offered an
        # open-shove here that six classes took at one to three basis points, which made "the
        # small blind's open is a two-price spot" this file's headline case; the re-sourced
        # solve has no shove here, so that claim is false of what ships.
        ("the small blind's open, the only spot with no call on the menu", spec.SB_OPEN_PATH,
         spec.SB_OPEN_KEY, ["fold", "raise"], 2.5, SB_OPEN_PRICED_CLASSES),
    ],
)
def test_a_named_committed_spot_prices_every_class_that_raises_and_no_other(
    by_path, derived, label: str, path: tuple[int, ...], key: str, kinds: list[str],
    price: float, priced: int,
) -> None:
    """What is on trial at a one-price spot is the *grain*, not the split.

    Both spots offer hero one price, so every weight is 1.0 and the per-class weight the
    2026-08-26 ruling fixed is unexercised. The per-class *membership* is not: 47 of the 169
    arriving classes three-bet a button open and 121 of 169 open the small blind. A per-spot
    table would price all 169 - an opening price for 48 hands the solve never opens - or price
    the spot once and lose which hands it was for.
    """
    node = by_path[path]
    classes = priced_classes(derived.sizing_payload, key)
    measured = measured_class_sizes(node)
    row = derived.artifact_payload["action_weights"][key]

    assert [action.kind for action in node.actions] == kinds, label
    assert "jam" not in kinds, "add_allin is false, so the two-price case cannot arise"
    assert len(row) == len(HAND_CLASSES), "every class arrives here, folding ones included"
    assert set(classes) == set(measured) == raising_classes(row), label
    assert len(classes) == priced, label
    assert len(classes) < len(row), "every arriving class raises, so membership is untested"
    for hand_class, entries in classes.items():
        assert entries_agree(entries, measured[hand_class]), (hand_class, entries)
        assert entries_agree(entries, ((price, 1.0),)), (hand_class, entries)
    for hand_class in set(row) - set(classes):
        assert row[hand_class]["raise"] == 0.0, hand_class
    assert entries_agree(priced_entries(derived.sizing_payload, key, PURE_CLASS), ((price, 1.0),))


def test_the_two_menus_decide_which_spots_carry_a_size_and_none_carry_none(
    export: SolverExport, walked, derived
) -> None:
    """The two menus enumerated, and the one direction of the invariant that still bites.

    Five spots offer fold, call and a raise: the big blind closing against each open. One offers
    fold and a raise and no call, the small blind's own, where `CHART-HERO-MUST-NEVER-LIMP`
    holds by construction. **All 6 carry a sizing entry**, which is what the first 2026-09-01
    withholding did to decision 6's two-directional invariant: the fold-and-call menu it was
    stated over went with the jams. What survives is the per-class direction - a *class* absent
    from a priced spot is a hand hero only folds or flats. Menus are read off the rows rather
    than the export's kinds: a converter that read a node right and dropped an action passes the
    sibling's reading and fails here."""
    sizes = derived.sizing_payload["raise_to_bb"]
    rows = derived.artifact_payload["action_weights"]
    keyed = committed_keys(export, walked)
    priced = {key for key in keyed if raising_classes(rows[key])}
    unpriced = set(keyed) - priced

    assert len(keyed) == COMMITTED_SPOTS
    assert Counter(artifact_menu(node) for node in keyed.values()) == COMMITTED_MENUS
    for key, node in keyed.items():
        declared = {action for weights in rows[key].values() for action in weights}
        assert tuple(sorted(declared)) == artifact_menu(node), key

    assert priced == set(sizes), "the table's keys are the committed spots that raise, exactly"
    assert priced == set(keyed)
    assert len(priced) == PRICED_SPOTS
    assert len(unpriced) == UNPRICED_SPOTS == 0

    silent = 0
    for key in priced:
        assert set(sizes[key]) == raising_classes(rows[key]), key
        assert all(entries for entries in sizes[key].values()), key
        silent += len(rows[key]) - len(sizes[key])
    assert silent, "no committed row holds a class that never raises, so nothing was tested"


def test_a_committed_spot_that_prices_nothing_is_absent_from_the_table(
    export: SolverExport, walked, derived
) -> None:
    """The other direction of decision 6's invariant, `VACUOUS` since 2026-09-01.
    A committed spot whose menu offers no raise must have no key in the sizing table at all,
    rather than a key holding an empty map - the second wears the first's shape and a reader
    cannot tell "nothing to price" from "priced nothing". The fifteen spots that exercised the
    rule were hero answering a five-bet jam and Taylor withheld them; the multiway family that
    returns once GTOpen can price it brings fold-or-call menus back."""
    rows = derived.artifact_payload["action_weights"]

    assert {k for k in committed_keys(export, walked) if not raising_classes(rows[k])} == set()
    vacuous("every committed spot offers hero a raise, so no spot prices nothing")


# --- What the committed 6 cannot exercise, labelled rather than counted ---


def test_a_spot_offering_two_prices_is_described_by_both_of_them(derived) -> None:
    """Decision 6's headline case, and `VACUOUS` over what this phase commits.

    The schema holds a list per hand class so that a spot offering two raise sizes is described
    by two, which is how `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` closes. Over the
    committed 6 the case does not arise - every spot offers hero exactly one price - so every
    entry is a one-element list and the two-price assertion holds for want of anything to hold
    of. The schema costs nothing, and the multiway family that returns once GTOpen can price it
    is where the case lived."""
    sizes = derived.sizing_payload["raise_to_bb"]
    lengths = Counter(len(entries) for spot in sizes.values() for entries in spot.values())

    assert set(lengths) == {1}, "a committed spot now offers two prices at one hand class"
    vacuous("no spot offers two prices, so the multi-size schema is unexercisable here")


def test_a_jam_and_a_named_raise_collapse_into_one_raise_whose_parts_add(export) -> None:
    """`PREFLOP_ACTIONS` holds one raise, so two aggressive offers cannot both survive as
    actions - and `VACUOUS`, over the whole re-sourced export rather than only the 6.

    The rule is real and the artifact needs it: hero's weight on raising is the named raise plus
    the jam, a row saying what hero does rather than at what price, so dropping the jam leaves a
    row that does not sum to one. Decision 14 re-sourced with `add_allin: false` and the
    consequence is stronger than decision 6 recorded: **not one node in the export offers both**,
    so nothing anywhere is left for the addition to add.
    """
    both = [n for n in export.nodes if {"raise", "jam"} <= {a.kind for a in n.actions}]
    assert both == []
    vacuous("no node in the export offers a named raise and a jam, so nothing collapses")


def test_two_prices_at_one_spot_are_both_priced_and_their_weights_add(derived) -> None:
    """Where the two vacuous rules above are actually proved: a synthetic export.

    A node offering hero fold, an open to 2.5, and the stack is the shape the multiway family
    will bring back and the shape the 2026-08-24 extension was ruled on. Converting it does both
    halves of decision 6 at once: the table holds both prices in ascending order with hero's
    weight on each, and the row holds one `raise` weight equal to their sum, so it still says
    what hero does and sums to one. A converter dropping the jam fails only here.
    """
    chart = spec.derivation().derive_chart(synthetic_export(2.5, jam=True))
    rfi_key = f"t{spec.TABLE_SIZE}/d{spec.DEPTH_BB}/SB/rfi"
    entries = priced_entries(chart.sizing_payload, rfi_key, PURE_CLASS)
    row = chart.artifact_payload["action_weights"][rfi_key][PURE_CLASS]
    named, shoved = SYNTHETIC_RAISE_BP, SYNTHETIC_JAM_BP

    assert [price for price, _ in entries] == pytest.approx([2.5, STACK_BB])
    assert [weight for _, weight in entries] == pytest.approx(
        [named / (named + shoved), shoved / (named + shoved)]
    )
    assert sum(weight for _, weight in entries) == pytest.approx(1.0, abs=1e-9)
    assert set(row) == {"fold", "raise"}
    assert row["raise"] == pytest.approx((named + shoved) / QUANTISATION_SCALE)
    assert row["raise"] > named / QUANTISATION_SCALE, "the jam's weight was dropped"

    # And the committed chart has neither shape, which is why this had to be synthetic.
    assert all(
        len(entries) == 1
        for spot in derived.sizing_payload["raise_to_bb"].values()
        for entries in spot.values()
    )


# --- The sizes come from the export's own labels, proved by perturbing them ---

FOLD_CONTINUES = SolverAction("Fold", "fold", 0.0, False)
FOLD_ENDS_IT = SolverAction("Fold", "fold", 0.0, True)
SYNTHETIC_RAISE_BP = 7_000
SYNTHETIC_JAM_BP = 2_000


def uniform_node(
    path: tuple[int, ...], actor: str, actions: list[SolverAction], split: tuple[int, ...]
) -> SolverNode:
    """A node whose every hand class plays the same mix and arrives in full - the trade
    `tests/test_solver_export.py` makes too, these exercising a converter and not poker."""
    return SolverNode(
        path,
        actor,
        tuple(actions),
        tuple(array("H", [weight] * 169) for weight in split),
        array("H", [QUANTISATION_SCALE] * 169),
    )


def synthetic_export(open_to: float, jam: bool = False) -> SolverExport:
    """The smallest tree that carries an opening price *and* satisfies the ruled predicate.
    Four seats fold, the small blind opens, the big blind answers - the folds being what the
    predicate needs, six players live failing the subtree clause however heads-up the history
    is. `config` stays the ruled one while the labels move, a converter reading
    `config["open_raises"][0]` being as hardcoded as one with 2.5 in it. Both nodes are
    committed under every ruling: the open faces no raise and the answer faces one."""
    opening = SolverAction(f"Raise {open_to}", "raise", open_to, False)
    call = SolverAction(f"Call {open_to}", "call", open_to, True)
    shove = SolverAction("All-in 100", "jam", STACK_BB, True)
    opens = [FOLD_ENDS_IT, opening, shove] if jam else [FOLD_ENDS_IT, opening]
    split = (1_000, SYNTHETIC_RAISE_BP, SYNTHETIC_JAM_BP) if jam else (3_000, 7_000)
    folded_to_sb = (0, 0, 0, 0)
    return SolverExport.from_nodes(
        [
            uniform_node((), "LJ", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node((0,), "HJ", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node((0, 0), "CO", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node((0, 0, 0), "BTN", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node(folded_to_sb, "SB", opens, split),
            uniform_node((*folded_to_sb, 1), "BB", [FOLD_ENDS_IT, call], (6_000, 4_000)),
        ],
        config=dict(RULED_CONFIG),
        positions=list(RULED_CONFIG["positions"]),
    )


@pytest.mark.parametrize("open_to", [2.5, 3.75, 4.0])
def test_the_converter_reads_its_sizes_from_the_export_s_own_labels(open_to: float) -> None:
    """The contract's unfalsifiability criterion, and the hardest thing in this file.
    The solved config has one opening size and one multiplier, so a converter with the prices
    written into it produces a byte-identical artifact and passes every other test here;
    perturbing the label is the only thing that tells the two apart. 2.5 is the control - if the
    perturbed cases pass and it fails, prices are transformed rather than read.
    """
    built = synthetic_export(open_to)
    chart = spec.derivation().derive_chart(built)
    rfi_key = f"t{spec.TABLE_SIZE}/d{spec.DEPTH_BB}/SB/rfi"
    facing_key = f"t{spec.TABLE_SIZE}/d{spec.DEPTH_BB}/BB/SB:raise@{open_to:g}"
    opened = priced_classes(chart.sizing_payload, rfi_key)

    # The fixture is evidence only if it is a real export the reader accepts; were it rejected,
    # everything below would be red for a reason with nothing to do with the converter.
    assert built.node_count == 6 and built.node(()).actor_pos == "LJ"
    assert built.node((0, 0, 0, 0)).actor_pos == "SB"
    assert [a.label for a in built.node((0, 0, 0, 0)).actions] == ["Fold", f"Raise {open_to}"]

    assert set(chart.artifact_payload["action_weights"]) == {rfi_key, facing_key}
    assert set(chart.sizing_payload["raise_to_bb"]) == {rfi_key}
    assert set(opened) == set(HAND_CLASSES)
    assert all(entries_agree(e, ((open_to, 1.0),)) for e in opened.values()), opened
    assert chart.census.committed == 2
    # The four folded seats are excluded by the subtree clause, which is the mispricing code:
    # with more than two players live, every terminal below them is one GTOpen cannot price.
    assert chart.census.excluded == {lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: 4}
    assert sum(chart.census.inexpressible.values()) == 0


def test_a_node_the_converter_cannot_handle_raises_rather_than_being_filed() -> None:
    """The closure is load-bearing or it is decoration.
    An action kind nothing in this repo has a rule for is not "inexpressible in the spot
    vocabulary" - it is a converter meeting something it does not understand, and filing that as
    a property of the grammar turns a bug into a documented limitation. Nor is it excluded:
    neither clause of the predicate can be evaluated at a node whose kinds the walk cannot
    classify. The reader accepts the tree, so the converter must refuse by name."""
    straddle = SolverAction("Straddle 2", "straddle", 0.0, False)
    call = SolverAction("Call 2", "call", 2.0, True)
    export = SolverExport.from_nodes(
        [
            uniform_node((), "LJ", [FOLD_ENDS_IT, straddle], (3_000, 7_000)),
            uniform_node((1,), "HJ", [FOLD_ENDS_IT, call], (6_000, 4_000)),
        ],
        config=dict(RULED_CONFIG),
        positions=list(RULED_CONFIG["positions"]),
    )

    with pytest.raises(ValueError, match="straddle"):
        spec.derivation().census(export)
    with pytest.raises(ValueError, match="straddle"):
        spec.derivation().derive_chart(export)


# --- An excluded node is a refusal at the table, never a neighbouring cell ---


@pytest.fixture(scope="module")
def committed_library(derived, tmp_path_factory) -> PreflopChartLibrary:
    """The derived artifact, written out and imported the way the runtime imports it."""
    directory = tmp_path_factory.mktemp("derived-chart")
    path = directory / "six_max_100bb_rakefree.json"
    text = json.dumps(derived.artifact_payload, indent=2, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return PreflopChartLibrary.from_artifacts([import_preflop_artifact(path)])


@pytest.mark.parametrize(
    ("label", "path", "key", "sequence", "kept"),
    [
        # The two the predicate never wanted. Re-derived on the 33,969-node export: the history
        # clause alone selects 65 and the subtree clause alone 4,865, so the two ways a node can
        # miss the conjunction are 14 and 4,814.
        ("the lojack's own open, one of the 14", spec.LOJACK_OPEN_PATH,
         spec.LOJACK_OPEN_KEY, (), False),
        ("a cold-called line, one of the 4,814", spec.COLD_CALLED_PATH,
         spec.COLD_CALLED_KEY, spec.COLD_CALLED_SEQUENCE, False),
        # The three the predicate keeps and a later ruling withholds.
        ("the button facing a big-blind three-bet", spec.THREE_BET_FACED_PATH,
         spec.THREE_BET_FACED_KEY, spec.THREE_BET_FACED_SEQUENCE, True),
        ("the big blind facing a button four-bet", spec.FOUR_BET_FACED_PATH,
         spec.FOUR_BET_FACED_KEY, spec.FOUR_BET_FACED_SEQUENCE, True),
        ("the button answering the jam it drew", spec.FIVE_BET_JAM_PATH,
         spec.FIVE_BET_JAM_KEY, spec.FIVE_BET_JAM_SEQUENCE, True),
    ],
)
def test_a_node_the_chart_does_not_hold_is_refused_rather_than_answered_from_a_neighbour(
    committed_library: PreflopChartLibrary, by_path, walked, label: str,
    path: tuple[int, ...], key: str, sequence: tuple[PreflopAction, ...], kept: bool,
) -> None:
    """The point of every exclusion, asked as a query rather than asserted as prose.
    One node from each of the five reasons, so a chart refusing only the obvious ones fails. All
    five are legal spots with legal keys whose ranges were never committed: answering the
    lojack's open from the small blind's range is a range hero never had, and nothing downstream
    could tell.

    **The withheld ones were checked only as missing keys until 2026-09-01, and that gap is
    dangerous here specifically.** Phase 12's ruling 8 normalises an observed price to the
    nearest one the chart declares for that line, so a withheld spot is where a neighbouring
    answer could arrive: a 22.5 four-bet quietly reading as the 7.5 three-bet the chart does
    hold, handing hero a three-bet-pot range in a four-bet pot, the query resolving and the
    weights looking ordinary. The three-bet-facing spot is the sharpest, being one action from a
    spot the chart *does* answer. `price_substitutions` is deliberately not consulted - a
    substitution that produced an answer is the defect, not the evidence. `kept` is the one way
    the five differ: the first two fail decision 1's predicate, the last three pass it."""
    node = by_path[path]
    query = ChartQuery(spec.TABLE_SIZE, spec.DEPTH_BB, node.actor_pos, sequence, PURE_CLASS)
    refused = committed_library.lookup(query)

    assert spec.predicate_selects(node, walked) is kept, label
    assert not spec.selected(node, walked), label
    assert spec.key_of(node, walked) == key
    assert query.spot_key == key
    assert key not in committed_library.spot_keys()
    assert isinstance(refused, ChartMiss), (label, getattr(refused, "spot_key", None))
    assert refused.code == MISS_SPOT_NOT_COVERED
    assert refused.code in MISS_CODES
    assert refused.spot_key == key and key in refused.detail


def test_a_committed_spot_is_still_answered(committed_library) -> None:
    """A chart that refused everything would satisfy the test above.
    Both are what the cutover is defended on: the big blind closing against a button open, the
    most-played decision in six-max, and the one opening range that survives. They are also all
    the shapes there are - since the third withholding the chart holds one open and five
    defences and nothing else. A five-bet call-off was a third example until 2026-09-01."""
    for position, sequence, key, action in (
        ("BB", spec.TRACED_SEQUENCE, spec.TRACED_KEY, "raise"),
        ("SB", (), spec.SB_OPEN_KEY, "raise"),
    ):
        answered = committed_library.lookup(
            ChartQuery(spec.TABLE_SIZE, spec.DEPTH_BB, position, sequence, PURE_CLASS)
        )
        assert not isinstance(answered, ChartMiss), getattr(answered, "detail", "")
        assert answered.spot_key == key
        assert answered.price_substitutions == ()
        assert dict(answered.action_weights)[action] > 0.0, key


def test_no_withheld_family_is_priced_or_answered_anywhere(
    export: SolverExport, walked, derived
) -> None:
    """All three withholdings read as prices, over whole families rather than named nodes.

    The button opens, the big blind three-bets, the button four-bets to 22.5 and the big blind
    jams 100; all three of those decisions leave the chart. At the four-bet node the `calibrated`
    fit has no four-bet-pot cell, so decision 20 withholds it and 100.0 is never quoted. At the
    node *after* it, where the chart put hero's last 77.5bb in as a call, the price is set by a
    range computed at that refused parent. At the node *before* it, hero's only aggressive answer
    is the 22.5 four-bet that walks into it, so 22.5 leaves the menu too. The 77.5 arithmetic is
    kept as the measurement of what is no longer advised."""
    sizes = derived.sizing_payload["raise_to_bb"]
    rows = derived.artifact_payload["action_weights"]
    names = ("three-bet", "four-bet", "jam")
    families = {name: withheld_keys(export, walked, name) for name in names}
    every = set().union(*(set(keys) for keys in families.values()))

    for name, keys in families.items():
        assert len(keys) == 15, name
    assert len(every) == THREE_BET_FACED_SPOTS + FOUR_BET_FACED_SPOTS + FIVE_BET_FACING_SPOTS
    assert len(committed_keys(export, walked)) + len(every) == PREDICATE_SPOTS
    assert not every & (set(rows) | set(sizes))

    for key, node in families["three-bet"].items():
        assert artifact_menu(node) == ("call", "fold", "raise"), key
        assert {a.to for a in node.actions if a.kind == "raise"} == {FOUR_BET_PRICE}, key
    for key, node in families["four-bet"].items():
        assert {a.to for a in node.actions if a.kind == "jam"} == {STACK_BB}, key
    for key, node in families["jam"].items():
        called = [action.to for action in node.actions if action.kind == "call"]
        four_bet = max(e.size_bb for e in walked[node.path][2] if e.size_bb and e.size_bb < 100)

        assert artifact_menu(node) == ("call", "fold"), key
        assert called == [STACK_BB], key
        assert STACK_BB - four_bet == pytest.approx(spec.FIVE_BET_CALL_OFF_BB), key

    # And nothing committed quotes or answers either price, the claim in three lines.
    quoted = {float(e["to_bb"]) for spot in sizes.values() for c in spot.values() for e in c}
    assert STACK_BB not in quoted and FOUR_BET_PRICE not in quoted
    assert all("100" not in key.split("/")[3] for key in rows)
    assert all("22.5" not in key.split("/")[3] for key in rows)


# --- The external oracle is not regenerated by the thing it checks ---


def test_the_converter_does_not_write_the_expectations_file() -> None:
    """The contract's non-goal, asserted as behaviour rather than as intent.

    The expectations file holds the only numbers in this phase this repo did not produce, which
    is what catches a range uniformly wrong rather than merely self-consistent. The mtime is
    checked as well as the bytes: rewriting with identical content is still a rewrite.

    **This test used to run the converter's writing mode, and that was a defect in the suite
    rather than an untidiness.** The write landed in `data/artifacts/preflop/`, repairing a stale
    chart mid-run, and under the gate's plain `pytest` this file sorts before every file that
    checks reproduction. What replaces it touches nothing: the converter's own `outputs()` is the
    list of files it writes and the oracle must not be in it, and `--check` then runs for real
    rather than after a write that guaranteed its answer."""
    import scripts.convert_preflop_export as converter

    assert EXPECTATIONS_PATH.exists(), f"the external oracle is missing at {EXPECTATIONS_PATH}"
    before = EXPECTATIONS_PATH.read_bytes()
    before_mtime = EXPECTATIONS_PATH.stat().st_mtime_ns
    writes = {path.resolve() for path, _ in converter.outputs()}

    assert writes, "the converter declares no outputs, so this proves nothing about the oracle"
    assert EXPECTATIONS_PATH.resolve() not in writes, sorted(str(path) for path in writes)

    checked = subprocess.run(
        [sys.executable, str(CONVERTER), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert EXPECTATIONS_PATH.read_bytes() == before
    assert EXPECTATIONS_PATH.stat().st_mtime_ns == before_mtime
    assert checked.returncode == 0, checked.stdout + checked.stderr
