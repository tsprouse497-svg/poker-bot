"""Phase 14: how one selected export node becomes one artifact row and one table entry.

The companion to `tests/test_chart_derivation.py`, split from it at the 700-line cap. That
file owns *which* nodes get committed and what a row says hero does, and the named nodes and
walk helpers this file imports rather than copies. This file owns the price: decision 6's
collapse of a jam and a named raise into one weight, the sizing table, the perturbation pair
proving prices are read from the export's own labels, what an excluded node gets instead of a
row, and the external oracle. Both run under `pytest_derived_chart`, authored at stage 4
before the converter exists.

**The sizing table holds every price a spot offers, per hand class, with hero's weight on
each.** Decision 6, extended 2026-08-24, restated 2026-08-25 when the predicate moved the
measurement under it, and re-cut 2026-08-26 from one weight per price per *spot* to one per
price per *class*. Over the 86, 21 spots offer a named raise and a jam, 15 a jam alone and 50
no raise at all, so a one-price table drops one of two prices at 21 spots and
`CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` cannot close on it. The per-class ruling is
what makes those entries poker: at the big blind against a button open the jam is 7.6 percent
of the *spot's* aggressive volume and runs from nothing on aces to 88.4 percent on 44, so a
spot-level weight jams aces once in thirteen three-bets where the solve never jams. How many
prices a spot offers is tree shape and is pinned; which classes take which is solve output,
recomputed from each class's own row. **How the strategy chooses between two was ruled the
same day: it draws with the seed a mixed action cell already uses.** Not asserted here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from array import array
from collections import Counter

import pytest
from test_chart_derivation import (
    COLD_CALLED_KEY,
    COLD_CALLED_PATH,
    COLD_CALLED_SEQUENCE,
    COMMITTED_NODES,
    DEPTH_BB,
    LOJACK_OPEN_KEY,
    LOJACK_OPEN_PATH,
    SB_OPEN_KEY,
    SB_OPEN_PATH,
    TABLE_SIZE,
    TRACED_KEY,
    TRACED_PATH,
    TRACED_SEQUENCE,
    derivation,
    key_of,
    selected,
    walk_state,
)

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

# The big blind closing against a button open: fold, call, a three-bet to 7.5 and the stack.
# `TRACED_PATH`, `TRACED_KEY` and `TRACED_SEQUENCE` come from the sibling module, which owns
# the same node for its census, its full-reach claim and its traced row.
TRACED_NAMED_RAISE_BB = 7.5

# The same line two actions later: hero three-bet to 7.5, the button four-bet to 22.5, and
# hero's only aggressive option is the whole stack. The case decision 6 exists for, and the
# case the GTO Wizard source never produced.
JAM_ONLY_PATH = (0, 0, 0, 1, 0, 2, 2)
JAM_ONLY_KEY = "t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5"

# Decision 6's table at its own schema version: version 1 held a bare float per spot, version
# 2 a list per hand class. The spot counts are the action menus read as prices - 21 offer a
# named raise and a jam, 15 a jam alone, 50 no raise at all and carry no key. Tree facts, so
# no re-solve at the ruled config moves them.
SIZING_SCHEMA_VERSION = 2
TWO_PRICE_SPOTS = 21
ONE_PRICE_SPOTS = 15
UNPRICED_SPOTS = 50
PRICED_SPOTS = TWO_PRICE_SPOTS + ONE_PRICE_SPOTS

# Solve output, pinned deliberately: decision 2 ships the solve as it stands, so these move
# only if somebody re-solves - the thing the inverted checksum tests make loud. Walked over
# the export: the 36 priced spots carry 2,219 class entries, 531 of them holding two prices.
# A converter writing one entry per class everywhere lands on 2,219 ones and no twos.
ONE_PRICE_CLASS_ENTRIES = 1_688
TWO_PRICE_CLASS_ENTRIES = 531

# The class the per-class ruling was measured on: at `TRACED_KEY` the fours three-bet 203bp
# and shove 1,553bp, so 88.4 percent of their aggression is the shove, against a spot
# aggregate of 7.6 percent and against aces, which never shove here at all. Basis points
# rather than shares, because the payload is integers and a share is the thing under test.
SPLIT_CLASS = "44"
SPLIT_CLASS_RAISE_BP = 203
SPLIT_CLASS_JAM_BP = 1_553
PURE_CLASS = "AA"
TRACED_SPOT_JAM_SHARE = 0.0761
"""What a per-spot weight would have said at `TRACED_KEY`: aces would take it as their jam
weight and the solve gives them none."""


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
def walked(by_path: dict[tuple[int, ...], SolverNode]) -> dict:
    state = walk_state(by_path)
    assert len(state) == len(by_path), "the walk did not reach every node"
    return state


def raising_classes(row: dict[str, dict[str, float]]) -> set[str]:
    """The hand classes at this spot that put any weight on raising."""
    return {n for n, weights in row.items() if weights.get("raise", 0.0) > 0.0}


def measured_class_sizes(node: SolverNode) -> dict[str, tuple[tuple[float, float], ...]]:
    """Every price hero may raise to here, per hand class, with his weight on each.
    Recomputed from the node, because which class shoves and which three-bets is solve output
    and a test reading it from the table under test is one copy of a number agreeing with
    another. A class is read off its own strategy row and nothing else - no combo weighting,
    no reach weighting, both of which mix classes, which is what the ruling took out. Reach
    still decides *which* classes are here: one that never arrives is a cell nobody trained.
    Shares are over that class's own aggressive volume, so folds and calls do not dilute.
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
    """One spot's whole entry: every priced class, in the order the table stored them.
    Read positionally rather than sorted: the ruling puts a class's entries in ascending
    price order, and a reader that sorted them could not tell an unordered table from one.
    """
    return {
        hand_class: tuple((float(e["to_bb"]), float(e["weight"])) for e in entries)
        for hand_class, entries in sizing_payload["raise_to_bb"][key].items()
    }


def priced_entries(sizing_payload: dict, key: str, hand_class: str):
    """One class's prices at one spot, which is what `sizes_bb` is ruled to return."""
    return priced_classes(sizing_payload, key)[hand_class]


def entries_agree(
    entries: tuple[tuple[float, float], ...], measured: tuple[tuple[float, float], ...]
) -> bool:
    """Whether a class's entry matches a recomputed one, price by price and in order.
    The tolerance is tight on purpose: nothing rules that this field may be rounded, and the
    smallest weight in the committed table is one basis point, held by eight cells - three of
    the six that open-shove at the small blind's open among them - so a table rounding further
    would drop those entries, turning a class the table cannot price into one it can.
    """
    if len(entries) != len(measured):
        return False
    return all(
        price == pytest.approx(other_price)
        and weight == pytest.approx(other_weight, rel=1e-9, abs=1e-12)
        for (price, weight), (other_price, other_weight) in zip(entries, measured, strict=True)
    )


# --- Decision 6: every price a spot offers, per class, with hero's weight on each ---


def test_a_class_that_plays_two_prices_carries_both_and_one_that_plays_one_carries_one(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """Decision 6 at the per-class shape, at the spot the whole phase is defended on.
    The big blind closing against a button open may fold, call, three-bet to 7.5 or shove.
    `PREFLOP_ACTIONS` holds one raise, so the artifact collapses both aggressive offers into
    one weight and the table is the only place the split survives; 21 of the 86 are this
    shape. What the per-class ruling adds is that the split is not one number: the fours shove
    88.4 percent of the aggression they show and aces none of theirs, the two ends of the
    range a 7.6 percent spot aggregate averages away. A converter writing that aggregate
    against every class passes every ordering, positivity and sum check here and hands aces a
    jam branch the solve never plays, which the two `PURE_CLASS` assertions alone catch.
    """
    node = by_path[TRACED_PATH]
    offers = {action.kind: index for index, action in enumerate(node.actions)}
    stack = RULED_CONFIG["stack"]
    column = gtopen_class_index(SPLIT_CLASS)
    raise_bp = node.strategy_bp[offers["raise"]][column]
    jam_bp = node.strategy_bp[offers["jam"]][column]
    entries = priced_entries(derived.sizing_payload, TRACED_KEY, SPLIT_CLASS)

    assert {"raise", "jam"} <= set(offers)
    assert node.actions[offers["raise"]].to == pytest.approx(TRACED_NAMED_RAISE_BB)
    assert node.actions[offers["jam"]].to == pytest.approx(stack)
    assert (raise_bp, jam_bp) == (SPLIT_CLASS_RAISE_BP, SPLIT_CLASS_JAM_BP)

    measured = measured_class_sizes(node)
    assert entries_agree(entries, measured[SPLIT_CLASS]), (entries, measured[SPLIT_CLASS])
    assert [price for price, _ in entries] == pytest.approx([TRACED_NAMED_RAISE_BB, stack])
    assert [weight for _, weight in entries] == pytest.approx(
        [raise_bp / (raise_bp + jam_bp), jam_bp / (raise_bp + jam_bp)]
    )
    assert sum(weight for _, weight in entries) == pytest.approx(1.0, abs=1e-9)

    # The spot aggregate the ruling rejected, recomputed rather than remembered, and the two
    # facts that tell a per-class table from a per-spot one: the fours shove an order of
    # magnitude more often than it says, and aces do not shove at all.
    aggregate = node.action_frequency(offers["jam"]) / (
        node.action_frequency(offers["raise"]) + node.action_frequency(offers["jam"])
    )
    assert aggregate == pytest.approx(TRACED_SPOT_JAM_SHARE, abs=5e-5)
    assert entries[1][1] > 10 * aggregate
    pure = priced_entries(derived.sizing_payload, TRACED_KEY, PURE_CLASS)
    assert node.strategy_bp[offers["jam"]][gtopen_class_index(PURE_CLASS)] == 0
    assert entries_agree(pure, ((TRACED_NAMED_RAISE_BB, 1.0),))


def test_a_jam_only_spot_is_priced_at_heros_whole_stack(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """Decision 6, and the case the GTO Wizard source this repo converted never had.
    Facing the button's four-bet to 22.5, hero may fold, call, or shove; there is no named
    raise to take a price from, so the old rule says raise and cannot say how much. The ruling
    prices it at the stack and 15 of the 86 are this shape. Every class that raises here
    raises to the same price, so every entry is a one-element list of the shape the split
    classes use, and each weight is 1.0 because it is that class's only price.
    """
    node = by_path[JAM_ONLY_PATH]
    kinds = {action.kind for action in node.actions}
    classes = priced_classes(derived.sizing_payload, JAM_ONLY_KEY)
    measured = measured_class_sizes(node)
    assert "jam" in kinds and "raise" not in kinds
    assert JAM_ONLY_KEY in derived.artifact_payload["action_weights"]
    assert set(classes) == set(measured)
    assert classes, "a jam-only spot with no priced class would pass every check below"
    for hand_class, entries in classes.items():
        assert entries_agree(entries, measured[hand_class]), (hand_class, entries)
        assert len(entries) == 1, hand_class
        assert entries[0] == pytest.approx((float(DEPTH_BB), 1.0)), hand_class
        assert entries[0][0] == pytest.approx(RULED_CONFIG["stack"]), hand_class

    # And the ruling reaches no further than it was ruled: where a named raise exists the
    # stack is one entry of two rather than the class's price.
    named = priced_entries(derived.sizing_payload, TRACED_KEY, SPLIT_CLASS)
    assert [p for p, _ in named] == pytest.approx([TRACED_NAMED_RAISE_BB, RULED_CONFIG["stack"]])


SB_OPEN_JAMMING = ("99", "AKo", "AKs", "AQs", "JJ", "TT")
"""The only classes carrying two prices at the small blind's open, walked out of the export.
The spot's *menu* offers two, which is what made "the small blind's open is a two-price spot"
read true and is why the six are written out: under the per-class ruling only they put any
weight on the shove, one to three basis points each, so 118 classes carry exactly one price
and 45 carry none. Pinning two prices at this spot is false for a correct build.
"""
SB_OPEN_PRICED_CLASSES = 124
SB_OPEN_FOLDING_CLASSES = 45


def test_the_small_blinds_open_offers_two_prices_and_six_classes_take_the_second(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """The one opening range the cutover commits, and the only fold/raise/jam spot in the 86.
    Folded to the small blind with one seat behind, hero may fold, open to 2.5, or shove;
    there is no call, which is `CHART-HERO-MUST-NEVER-LIMP` holding by construction. This is
    the spot that punishes reading the shape off the menu: the open-shove is one part in a
    hundred thousand of the *spot's* aggressive volume, and per class one to three basis
    points on six classes and nothing elsewhere, so the lengths here are 118 ones and six
    twos. A table giving every class both prices would open-shove 45 percent of the range at
    some frequency; one that rounded its weights would drop the six and turn a spot the
    strategy must draw at into one it can price outright.
    """
    node = by_path[SB_OPEN_PATH]
    classes = priced_classes(derived.sizing_payload, SB_OPEN_KEY)
    measured = measured_class_sizes(node)
    open_to, stack = RULED_CONFIG["open_raises"][0], RULED_CONFIG["stack"]

    assert [action.kind for action in node.actions] == ["fold", "raise", "jam"]
    assert set(classes) == set(measured)
    assert len(classes) == SB_OPEN_PRICED_CLASSES
    assert len(HAND_CLASSES) - len(classes) == SB_OPEN_FOLDING_CLASSES
    assert all(entries_agree(e, measured[n]) for n, e in classes.items()), classes
    assert sorted(n for n, e in classes.items() if len(e) == 2) == sorted(SB_OPEN_JAMMING)
    assert Counter(len(e) for e in classes.values()) == {
        1: SB_OPEN_PRICED_CLASSES - len(SB_OPEN_JAMMING),
        2: len(SB_OPEN_JAMMING),
    }
    assert entries_agree(classes[PURE_CLASS], ((open_to, 1.0),))
    for hand_class in SB_OPEN_JAMMING:
        (open_price, open_weight), (jam_price, jam_weight) = classes[hand_class]

        assert (open_price, jam_price) == pytest.approx((open_to, stack)), hand_class
        assert 0.0 < jam_weight < open_weight, hand_class
        assert open_weight + jam_weight == pytest.approx(1.0, abs=1e-9), hand_class


def test_every_price_the_export_offers_hero_is_in_the_table_with_his_weight_on_it(
    export: SolverExport, walked, derived
) -> None:
    """The ruling over all 86 rather than at three named spots.
    Every committed node is walked and every one of its classes recomputed, so a table that
    got one family right and collapsed another fails here rather than passing on the spots
    this file names. Each property hides a different defect: ordered by price, so a reader can
    say which of two is the small one without sorting; drawn from the offers the node holds
    and never repeated, so nothing was invented; strictly positive, so a price that class
    never takes is not offered as one it might; summing to one, so they are shares of *that
    class's* volume, not the spot's. No epsilon - the smallest weight is one basis point.
    """
    sizes = derived.sizing_payload["raise_to_bb"]
    lengths: Counter = Counter()
    spot_lengths: Counter = Counter()
    for node in export.nodes:
        if not selected(node, walked):
            continue
        key = key_of(node, walked)
        measured = measured_class_sizes(node)
        if not measured:
            assert key not in sizes, key
            continue
        table = priced_classes(derived.sizing_payload, key)
        offered = {action.to for action in node.actions if action.kind in ("raise", "jam")}
        assert set(table) == set(measured), key
        for hand_class, entries in table.items():
            prices = [price for price, _ in entries]
            weights = [weight for _, weight in entries]

            assert entries_agree(entries, measured[hand_class]), (key, hand_class, entries)
            assert set(prices) <= offered and len(set(prices)) == len(prices), (key, hand_class)
            assert prices == sorted(prices), (key, hand_class)
            assert all(weight > 0.0 for weight in weights), (key, hand_class)
            assert sum(weights) == pytest.approx(1.0, abs=1e-9), (key, hand_class)
            lengths[len(entries)] += 1
        spot_lengths[max(len(entries) for entries in table.values())] += 1

    assert derived.sizing_payload["schema_version"] == SIZING_SCHEMA_VERSION
    assert lengths == {1: ONE_PRICE_CLASS_ENTRIES, 2: TWO_PRICE_CLASS_ENTRIES}
    assert spot_lengths == {2: TWO_PRICE_SPOTS, 1: ONE_PRICE_SPOTS}
    assert sum(spot_lengths.values()) == PRICED_SPOTS == COMMITTED_NODES - UNPRICED_SPOTS


def test_a_one_price_class_and_a_two_price_class_are_told_apart_in_the_table(derived) -> None:
    """A table that wrapped every class in a one-element list has changed shape and gained
    nothing.

    The point of the schema is that a class playing two prices is described by two, so both
    lengths must occur and in the proportion the export's own weights give. A converter
    emitting one entry per class - the majority price, or the stack - passes every ordering,
    positivity and sum assertion and fails this one. It is the distinction the runtime rule
    rests on: one price can be priced from the table alone and two cannot. The three named
    spots are the three menus that price anything.
    """
    sizes = derived.sizing_payload["raise_to_bb"]
    lengths = Counter(len(entries) for spot in sizes.values() for entries in spot.values())
    shapes = {key: {len(e) for e in spot.values()} for key, spot in sizes.items()}

    assert lengths == {1: ONE_PRICE_CLASS_ENTRIES, 2: TWO_PRICE_CLASS_ENTRIES}
    assert (shapes[JAM_ONLY_KEY], shapes[TRACED_KEY], shapes[SB_OPEN_KEY]) == ({1}, {1, 2}, {1, 2})
    assert len(sizes) == PRICED_SPOTS

    # The entry vocabulary is closed, so a third field carrying a chosen price or a rounded
    # one cannot appear beside the two the ruling names.
    for key, spot in sizes.items():
        for hand_class, entries in spot.items():
            assert hand_class in HAND_CLASSES, (key, hand_class)
            assert all(set(entry) == {"to_bb", "weight"} for entry in entries), (key, hand_class)


def test_a_spot_and_a_class_absent_from_the_table_have_no_size_to_hold(derived) -> None:
    """The note decision 6 promised, at both levels the per-class shape has.
    A spot absent from the table is one where hero's only options are fold and call - facing
    a shove, or after the raise cap - so there is nothing to price, and 50 of the 86 are that
    shape. A *class* absent from a priced spot's entry is the same one level down: a hand hero
    only folds or flats here, which is most of the range at most spots. The invariant runs
    both ways at both levels - a priced class the row never raises prices an action the chart
    does not offer, an unpriced class it does raise is a raise the strategy cannot make.
    Absent means no key, not an empty list, which is the second wearing the first's shape.
    """
    sizes = derived.sizing_payload["raise_to_bb"]
    rows = derived.artifact_payload["action_weights"]
    priced = {key for key, row in rows.items() if raising_classes(row)}
    unpriced = set(rows) - priced

    assert priced == set(sizes)
    assert unpriced.isdisjoint(sizes)
    assert len(unpriced) == UNPRICED_SPOTS
    assert len(priced) == PRICED_SPOTS == COMMITTED_NODES - UNPRICED_SPOTS

    silent = 0
    for key, spot in sizes.items():
        assert set(spot) == raising_classes(rows[key]), key
        assert all(entries for entries in spot.values()), key
        silent += len(rows[key]) - len(spot)
    assert silent, "no committed row holds a class that never raises, so nothing was tested"


def test_a_jam_and_a_named_raise_collapse_into_one_raise_whose_parts_add(
    by_path: dict[tuple[int, ...], SolverNode], derived
) -> None:
    """`PREFLOP_ACTIONS` holds one raise, so the two offers cannot both survive.
    Their weights add because the artifact holds what hero does rather than at what price.
    Dropping the shove would leave a row that does not sum to one and a big blind folding aces
    to a button open. 20 of the 86 are this shape; the small blind's open is the twenty-first.
    """
    node = by_path[TRACED_PATH]
    named = [i for i, action in enumerate(node.actions) if action.kind == "raise"]
    jams = [i for i, action in enumerate(node.actions) if action.kind == "jam"]
    row = derived.artifact_payload["action_weights"][TRACED_KEY]
    assert len(named) == 1 and len(jams) == 1
    graded = 0
    for hand_class in ("AA", "KK", "AKs"):
        named_bp = node.weight_bp(named[0], hand_class)
        jam_bp = node.weight_bp(jams[0], hand_class)
        assert row[hand_class]["raise"] == pytest.approx(
            (named_bp + jam_bp) / QUANTISATION_SCALE, abs=1e-6
        ), hand_class
        if jam_bp > 0:
            graded += 1
            assert row[hand_class]["raise"] > named_bp / QUANTISATION_SCALE, hand_class
    assert graded, "no probed class shoved, so nothing here distinguishes a dropped jam"


# --- The sizes come from the export's own labels, proved by perturbing them ---

FOLD_CONTINUES = SolverAction("Fold", "fold", 0.0, False)
FOLD_ENDS_IT = SolverAction("Fold", "fold", 0.0, True)


def uniform_node(
    path: tuple[int, ...], actor: str, actions: list[SolverAction], split: tuple[int, ...]
) -> SolverNode:
    """A node whose every hand class plays the same mix and arrives in full.
    The trade `tests/test_solver_export.py` makes for its own fixtures: real strategies vary
    by class, and these exist to exercise a converter rather than to be poker.
    """
    return SolverNode(
        path,
        actor,
        tuple(actions),
        tuple(array("H", [weight] * 169) for weight in split),
        array("H", [QUANTISATION_SCALE] * 169),
    )


def synthetic_export(open_to: float) -> SolverExport:
    """The smallest tree that carries an opening price *and* satisfies the ruled predicate.
    Four seats fold, the small blind opens, the big blind answers. The folds are what the
    predicate needs: a node with six players live fails the subtree clause however heads-up
    its history is. The early seats get a fold and nothing else, so the opening price appears
    exactly once. `config` stays the ruled one while the labels move: a converter reading
    `config["open_raises"][0]` is as hardcoded as one with 2.5 in it.
    """
    opening = SolverAction(f"Raise {open_to}", "raise", open_to, False)
    call = SolverAction(f"Call {open_to}", "call", open_to, True)
    folded_to_sb = (0, 0, 0, 0)
    return SolverExport.from_nodes(
        [
            uniform_node((), "LJ", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node((0,), "HJ", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node((0, 0), "CO", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node((0, 0, 0), "BTN", [FOLD_CONTINUES], (QUANTISATION_SCALE,)),
            uniform_node(folded_to_sb, "SB", [FOLD_ENDS_IT, opening], (3_000, 7_000)),
            uniform_node((*folded_to_sb, 1), "BB", [FOLD_ENDS_IT, call], (6_000, 4_000)),
        ],
        config=dict(RULED_CONFIG),
        positions=list(RULED_CONFIG["positions"]),
    )


def test_the_synthetic_export_is_a_tree_the_reader_accepts() -> None:
    """The fixture below is evidence only if it is a real export: were it rejected, the
    perturbation test would be red for a reason with nothing to do with the converter.
    """
    export = synthetic_export(2.5)
    opener = export.node((0, 0, 0, 0))

    assert export.node_count == 6
    assert export.node(()).actor_pos == "LJ"
    assert opener.actor_pos == "SB"
    assert [action.label for action in opener.actions] == ["Fold", "Raise 2.5"]
    assert "call" not in {action.kind for action in opener.actions}


@pytest.mark.parametrize("open_to", [2.5, 3.75, 4.0])
def test_the_converter_reads_its_sizes_from_the_export_s_own_labels(open_to: float) -> None:
    """The contract's unfalsifiability criterion, and the hardest thing in this file.
    The solved config has one opening size and one raise multiplier, so a converter with the
    prices written into it produces a byte-identical artifact and passes every other test
    here; perturbing the label is the only thing that tells the two apart. 2.5 is the control
    - if the perturbed cases pass and it fails, prices are transformed, not read. The price is
    read out of a class's entry rather than a bare float, holding the converter to the ruled
    shape at a one-price class too: every class here opens and none shoves, so all 169 carry
    one entry, and the big blind's fold-or-call spot carries none.
    """
    chart = derivation().derive_chart(synthetic_export(open_to))
    rfi_key = f"t{TABLE_SIZE}/d{DEPTH_BB}/SB/rfi"
    facing_key = f"t{TABLE_SIZE}/d{DEPTH_BB}/BB/SB:raise@{open_to:g}"
    opened = priced_classes(chart.sizing_payload, rfi_key)

    assert set(chart.artifact_payload["action_weights"]) == {rfi_key, facing_key}
    assert set(chart.sizing_payload["raise_to_bb"]) == {rfi_key}
    assert set(opened) == set(HAND_CLASSES)
    assert all(entries_agree(e, ((open_to, 1.0),)) for e in opened.values()), opened
    assert chart.census.committed == 2
    # The four folded seats are excluded by the subtree clause, which is the mispricing code:
    # with more than two players live, every terminal below them is one GTOpen cannot price.
    assert chart.census.excluded == {lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: 4}
    assert sum(chart.census.inexpressible.values()) == 0


def test_two_prices_produce_two_different_charts() -> None:
    """Stated as a difference, because "the key holds 3.75" could still be a constant.
    The same converter over the same tree at two prices must disagree in exactly one place,
    and the sizing table has to move with the key - the price *inside* the class's entry,
    since a table that moved the key and left the entry alone is the same defect one level
    down. A converter keying off the label but pricing off a constant passes the test above.
    """
    solved = derivation().derive_chart(synthetic_export(2.5))
    perturbed = derivation().derive_chart(synthetic_export(3.75))
    solved_keys = set(solved.artifact_payload["action_weights"])
    perturbed_keys = set(perturbed.artifact_payload["action_weights"])
    rfi_key = f"t{TABLE_SIZE}/d{DEPTH_BB}/SB/rfi"
    # Read at a named class, because a per-spot reader is what this round replaced.
    solved_entries = priced_entries(solved.sizing_payload, rfi_key, PURE_CLASS)
    perturbed_entries = priced_entries(perturbed.sizing_payload, rfi_key, PURE_CLASS)

    assert solved_keys - perturbed_keys == {f"t{TABLE_SIZE}/d{DEPTH_BB}/BB/SB:raise@2.5"}
    assert perturbed_keys - solved_keys == {f"t{TABLE_SIZE}/d{DEPTH_BB}/BB/SB:raise@3.75"}
    assert entries_agree(solved_entries, ((2.5, 1.0),))
    assert entries_agree(perturbed_entries, ((3.75, 1.0),))
    assert solved_entries != perturbed_entries


def test_a_node_the_converter_cannot_handle_raises_rather_than_being_filed() -> None:
    """The closure is load-bearing or it is decoration.
    An action kind nothing in this repo has a rule for is not "inexpressible in the spot
    vocabulary" - it is a converter meeting something it does not understand, and filing it as
    a property of the grammar turns a bug into a documented limitation. Nor may it be filed as
    excluded: neither clause of the predicate can be evaluated at a node whose action kinds the
    walk cannot classify, because both count what a seat did. The export reader validates shape
    rather than the poker vocabulary of its labels and accepts the tree, so the converter must
    refuse and the error must name the kind: a blanket `except ValueError` filing everything
    under `derivation:no-legal-spot-key` is the defect guarded against.
    """
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
        derivation().census(export)
    with pytest.raises(ValueError, match="straddle"):
        derivation().derive_chart(export)


# --- An excluded node is a refusal at the table, never a neighbouring cell ---


@pytest.fixture(scope="module")
def committed_library(derived, tmp_path_factory) -> PreflopChartLibrary:
    """The derived artifact, written out and imported the way the runtime imports it.
    Going through the importer rather than the payload dict is the point: a library built from
    what the converter emitted is what the bot answers from.
    """
    directory = tmp_path_factory.mktemp("derived-chart")
    path = directory / "six_max_100bb_rakefree.json"
    text = json.dumps(derived.artifact_payload, indent=2, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return PreflopChartLibrary.from_artifacts([import_preflop_artifact(path)])


@pytest.mark.parametrize(
    ("label", "path", "key", "sequence"),
    [
        ("the lojack's own open, one of the 24", LOJACK_OPEN_PATH, LOJACK_OPEN_KEY, ()),
        ("a cold-called line, one of the 5,386", COLD_CALLED_PATH, COLD_CALLED_KEY,
         COLD_CALLED_SEQUENCE),
    ],
)
def test_an_excluded_node_is_refused_rather_than_answered_from_a_neighbour(
    committed_library: PreflopChartLibrary,
    by_path: dict[tuple[int, ...], SolverNode],
    walked,
    label: str,
    path: tuple[int, ...],
    key: str,
    sequence: tuple[PreflopAction, ...],
) -> None:
    """The whole point of the exclusion, asked as a query rather than asserted as prose.
    One node from each exclusion bucket, so a chart that refused only the obvious half fails.
    Both are legal spots with legal keys whose ranges were never committed: answering the
    lojack's open from the small blind's range, or the cold-called three-bet from the same
    three-bet without the flat, would be a range hero never had and nothing downstream could
    tell. The lojack's open is the sharp one - a range the bot answers today.
    """
    node = by_path[path]
    query = ChartQuery(TABLE_SIZE, DEPTH_BB, node.actor_pos, sequence, "AA")
    refused = committed_library.lookup(query)

    assert not selected(node, walked), label
    assert key_of(node, walked) == key
    assert query.spot_key == key
    assert key not in committed_library.spot_keys()
    assert isinstance(refused, ChartMiss), label
    assert refused.code == MISS_SPOT_NOT_COVERED
    assert refused.code in MISS_CODES
    assert refused.spot_key == key
    assert key in refused.detail


def test_a_committed_spot_is_still_answered(committed_library: PreflopChartLibrary) -> None:
    """A chart that refused everything would satisfy the test above.
    The two asked are the ones the cutover is defended on: the big blind closing against a
    button open, and the one opening range that survives. Only that they answer is checked.
    """
    for position, sequence, key in (
        ("BB", TRACED_SEQUENCE, TRACED_KEY),
        ("SB", (), SB_OPEN_KEY),
    ):
        answered = committed_library.lookup(
            ChartQuery(TABLE_SIZE, DEPTH_BB, position, sequence, "AA")
        )
        assert not isinstance(answered, ChartMiss), getattr(answered, "detail", "")
        assert answered.spot_key == key
        assert answered.price_substitutions == ()
        assert dict(answered.action_weights)["raise"] > 0.0


# --- The external oracle is not regenerated by the thing it checks ---


def test_the_converter_does_not_write_the_expectations_file() -> None:
    """The contract's non-goal, asserted as behaviour rather than as intent.
    The expectations file holds "the only numbers in this phase that this repo did not
    produce", which catches a range uniformly wrong rather than merely self-consistent, and a
    reference regenerated from what it checks cannot fail. The mtime is checked as well as the
    bytes: a file rewritten with identical content has still been rewritten, and on the day
    the numbers behind it move nobody would notice.
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
