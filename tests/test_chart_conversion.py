"""Phase 14: what one committed export node costs, and where its price came from.

The companion to `tests/test_chart_derivation.py`, split from it at the 700-line cap. That
file owns *which* nodes get committed and what a row says hero does, and the named nodes and
walk helpers this file imports rather than copies. This one owns the price: the sizing
table, the prices hero is offered, the perturbation pair proving prices are read from the
export's own labels, the refusal an excluded node gets, and the external oracle. Both run
under `pytest_derived_chart`, authored at stage 4 before the converter is finished.

**The sizing table holds every raise size a spot offers, with the weight hero gives each,
per hand class.** Decision 6, ruled 2026-08-23 and amended four times as the tree under it
moved; the per-class grain and the seeded draw between two prices were ruled 2026-08-26 and
transcribed 2026-09-01. Over the **36** spots decision 20 commits, hero is offered one price
at 21 and none at all at 15, and **no committed spot offers two**. The schema's headline
case is therefore unexercisable here, so the checks for it are labelled `VACUOUS` rather
than counted as passes - decision 6 says in terms that a check that cannot fail must not be
counted as one that passed. Three things are vacuous here, each labelled where it sits: two
prices at one spot, a jam beside a named raise, and a jam at all. What is not vacuous is
asserted: the price ladder, the 21/15 split, the two-directional invariant, the three menus,
and the per-class membership of every entry.

**Hero can never initiate the last raise, and the chart still answers 15 call-offs for a
full stack.** The spots where hero could shove are the ones decision 20 withholds, so 100.0
is never a price the table quotes; but 15 committed spots face a five-bet jam and at them
the chart puts hero's last 77.5bb in as a *call*.
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

# Counted here as well as in the sibling, because two files reaching 36 independently is the
# check and importing the number would make it one file twice. `spec.selected` is both
# rulings and means committed; `spec.predicate_selects` is decision 1 alone, which keeps 51.
PREDICATE_SPOTS = 51
FOUR_BET_FACED_SPOTS = 15
COMMITTED_SPOTS = 36
FIVE_BET_FACING_SPOTS = 15

# Tree facts. The open is 2.5 and `raise_mults` is 3.0, so hero's price is the open times the
# multiplier once per raise he faces - 2.5, 7.5, 22.5 - until the fourth, where 67.5 crosses
# `allin_threshold` and snaps to the stack. That fourth is the price decision 20 withholds,
# which is why the committed list has three entries and not four.
HERO_PRICES = (2.5, 7.5, 22.5)
SPOTS_OFFERING_PRICE = {2.5: 1, 7.5: 5, 22.5: 15}
STACK_BB = 100.0
COMMITTED_MENUS = {("call", "fold", "raise"): 20, ("call", "fold"): 15, ("fold", "raise"): 1}

# Walked out of the export: 21 priced spots carrying 648 class entries, every one a single
# price, and 15 with nothing to price. A build keeping the withheld 15 lands on 36 keys and
# 812 entries, which is what these catch.
SIZING_SCHEMA_VERSION = 2
PRICED_SPOTS = 21
UNPRICED_SPOTS = 15
ONE_PRICE_CLASS_ENTRIES = 648
TWO_PRICE_CLASS_ENTRIES = 0

# The two named spots: how many arriving classes take the one price each offers.
TRACED_PRICED_CLASSES = 47
SB_OPEN_PRICED_CLASSES = 121
PURE_CLASS = "AA"


def vacuous(what: str) -> None:
    """Stop the test and record it as skipped rather than passed.

    Decision 6, on the schema it keeps over data that cannot exercise it: "a check that
    cannot fail must not be counted as one that passed". The guard this repo usually writes
    - `assert found, "...otherwise vacuous"` - is the wrong tool, because the case is ruled
    absent rather than accidentally absent, so it would be a permanent red against a chart
    the contract describes correctly. A skip is the one outcome that is neither. Every use
    sits *after* an assertion that the premise still holds.
    """
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
    """The 36 the chart holds, keyed. `spec.selected` is decision 1 and decision 20 together."""
    return {spec.key_of(n, state): n for n in export.nodes if spec.selected(n, state)}


def withheld_keys(export: SolverExport, state) -> dict[str, SolverNode]:
    """The 15 decision 20 takes back: hero faces a four-bet and his answer is the stack."""
    kept = (n for n in export.nodes if spec.predicate_selects(n, state))
    return {spec.key_of(n, state): n for n in kept if spec.faces_a_four_bet(n, state)}


def artifact_menu(node: SolverNode) -> tuple[str, ...]:
    """The node's offers in the artifact's vocabulary, where a jam is a raise."""
    return tuple(sorted({"raise" if a.kind == "jam" else a.kind for a in node.actions}))


def raising_classes(row: dict[str, dict[str, float]]) -> set[str]:
    """The hand classes at this spot that put any weight on raising."""
    return {n for n, weights in row.items() if weights.get("raise", 0.0) > 0.0}


def measured_class_sizes(node: SolverNode) -> dict[str, tuple[tuple[float, float], ...]]:
    """Every price hero may raise to here, per hand class, with his weight on each.
    Recomputed from the node, because which class takes which price is solve output and a
    test reading it from the table under test is one copy of a number agreeing with another.
    A class is read off its own row and nothing else - no combo or reach weighting, both of
    which mix classes, which is what the per-class ruling took out. Shares are over that
    class's own volume; reach still decides which classes are here at all.
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
    """One spot's whole entry: every priced class, in the order the table stored them. Read
    positionally, because a reader that sorted could not tell an unordered table from one.
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
    The tolerance is tight because nothing rules this field may be rounded, and rounding
    would drop a price a class takes rarely, turning a class the chart cannot price outright
    into one it can. Every committed weight is 1.0, so it bites on a two-price build only.
    """
    if len(entries) != len(measured):
        return False
    return all(
        price == pytest.approx(other_price)
        and weight == pytest.approx(other_weight, rel=1e-9, abs=1e-12)
        for (price, weight), (other_price, other_weight) in zip(entries, measured, strict=True)
    )


# --- What the committed 36 offer hero, and at what price ---


def test_every_price_the_export_offers_hero_is_in_the_table_with_his_weight_on_it(
    export: SolverExport, walked, derived
) -> None:
    """The ruling over all 36, with the price ladder it produces.

    Hero's price is the 2.5 open times the 3.0 multiplier once per raise in front of him -
    2.5 to open, 7.5 to three-bet, 22.5 to four-bet - so `[2.5, 7.5, 22.5]` is derived rather
    than listed; the fourth rung is 67.5, which `allin_threshold` snaps to the stack, and
    that is the spot decision 20 withholds. Every committed node is then walked and every
    class recomputed, so a table right about one family and wrong about another fails here
    rather than passing on the named spots. Each property hides a defect: prices drawn from
    the node's own offers and never repeated, so nothing was invented; ordered, so a reader
    can tell the small one without sorting; strictly positive, so a price a class never takes
    is not offered as one it might; summing to one, so weights are shares of *that class's*
    volume. 648 catches the build this stage is written against, which keeps the withheld 15
    and lands on 812 entries over 36 keys.
    """
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

        assert prices == ({rung} if prices else set()), key
        for price in prices:
            offered[price] += 1
        if not measured:
            assert key not in sizes, key
            continue
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
    assert set(sizes) <= set(keyed), "the table prices a spot the chart does not commit"
    assert dict(offered) == SPOTS_OFFERING_PRICE
    assert tuple(sorted(offered)) == HERO_PRICES and STACK_BB not in offered
    assert lengths == {1: ONE_PRICE_CLASS_ENTRIES}
    assert spot_lengths == {1: PRICED_SPOTS}
    assert len(sizes) == PRICED_SPOTS == COMMITTED_SPOTS - UNPRICED_SPOTS


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
    arriving classes three-bet a button open and 121 of 169 open the small blind, the rest
    folding or flatting. A per-spot table would either price all 169 - giving an opening
    price to 48 hands the solve never opens, a range two-fifths too wide - or price the spot
    once and lose which hands it was for.
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


def test_the_three_menus_decide_which_spots_carry_a_size_and_which_carry_none(
    export: SolverExport, walked, derived
) -> None:
    """The three menus enumerated, and the two-directional invariant they produce.

    Twenty spots offer fold, call and a raise - the big blind closing against an open, and
    hero holding the three-bet. Fifteen offer fold and call only, because hero has been
    jammed on for the last 77.5bb and the raise cap is reached, so there is nothing to price
    and the strategy refuses rather than invent a size. One offers fold and a raise and no
    call, the small blind's open, where `CHART-HERO-MUST-NEVER-LIMP` holds by construction.
    So 21 spots carry an entry and 15 do not, both non-empty, and the invariant runs both
    ways at both levels: a *class* absent from a priced spot is a hand hero only folds or
    flats. Absent means no key, never an empty list, which is the second wearing the first's
    shape. Menus are read off the rows rather than the export's kinds, which is the sibling's
    reading - a converter that read a node right and dropped an action passes there and fails
    here, because a row missing an action still sums to one over the actions it kept.
    """
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
    assert len(priced) == PRICED_SPOTS
    assert len(unpriced) == UNPRICED_SPOTS
    assert priced and unpriced, "one direction of the invariant has nothing to bite on"

    silent = 0
    for key in priced:
        assert set(sizes[key]) == raising_classes(rows[key]), key
        assert all(entries for entries in sizes[key].values()), key
        silent += len(rows[key]) - len(sizes[key])
    assert silent, "no committed row holds a class that never raises, so nothing was tested"
    for key in unpriced:
        assert artifact_menu(keyed[key]) == ("call", "fold"), key
        assert all("raise" not in weights for weights in rows[key].values()), key


def test_the_whole_stack_left_heros_price_menu_and_the_chart_still_calls_off_for_it(
    export: SolverExport, walked, derived
) -> None:
    """Two nodes one action apart, read as prices rather than as a selection.

    Hero four-bets the button to 22.5; the button jams 100. At the node *before* that - hero
    holding the four-bet, his only aggressive answer the stack - the fit behind `calibrated`
    has no four-bet-pot cell, so decision 20 withholds the spot and 100.0 never becomes a
    price the table quotes. At the node *after* it hero is on a fold-or-call menu and the
    chart answers, by putting his last 77.5bb in. The sibling owns whether either is
    committed; the consequence for the table is here, both ways. Dropping the call-offs would
    leave 15 committed spots unanswered with every price count here still adding up, and
    quoting the stack would advise a five-bet the phase does not ship.
    """
    sizes = derived.sizing_payload["raise_to_bb"]
    rows = derived.artifact_payload["action_weights"]
    keyed = committed_keys(export, walked)
    held_back = withheld_keys(export, walked)
    call_offs = {k: n for k, n in keyed.items() if spec.raises_faced(n, walked) == 4}

    assert len(held_back) == FOUR_BET_FACED_SPOTS
    assert len(keyed) + len(held_back) == PREDICATE_SPOTS
    assert spec.FOUR_BET_FACED_KEY in held_back and spec.FIVE_BET_JAM_KEY in call_offs
    for key, node in held_back.items():
        assert {a.to for a in node.actions if a.kind == "jam"} == {STACK_BB}, key
        assert key not in rows and key not in sizes, key

    # And the call-offs: 15 committed spots, no raise to price, hero's last 77.5bb going in
    # as a call. Aces call every combo of it, which is the floor any inversion check needs.
    assert len(call_offs) == FIVE_BET_FACING_SPOTS
    for key, node in call_offs.items():
        called = [action.to for action in node.actions if action.kind == "call"]
        four_bet = max(e.size_bb for e in walked[node.path][2] if e.size_bb and e.size_bb < 100)

        assert artifact_menu(node) == ("call", "fold"), key
        assert called == [STACK_BB], key
        assert STACK_BB - four_bet == pytest.approx(spec.FIVE_BET_CALL_OFF_BB), key
        assert key not in sizes, key
        assert rows[key][PURE_CLASS]["call"] == pytest.approx(1.0), key


# --- What the committed 36 cannot exercise, labelled rather than counted ---


def test_a_spot_offering_two_prices_is_described_by_both_of_them(derived) -> None:
    """Decision 6's headline case, and `VACUOUS` over what this phase commits.

    The schema holds a list per hand class so that a spot offering two raise sizes is
    described by two, which is how `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` closes.
    Over the committed 36 the case does not arise - 21 spots offer one price and 15 none - so
    every entry is a one-element list and an assertion about the two-price shape holds for
    want of anything to hold of. The schema is kept anyway: it costs nothing and the multiway
    family that returns once GTOpen can price it is where the case lived.
    """
    sizes = derived.sizing_payload["raise_to_bb"]
    lengths = Counter(len(entries) for spot in sizes.values() for entries in spot.values())

    assert lengths.get(2, 0) == TWO_PRICE_CLASS_ENTRIES
    assert set(lengths) == {1}
    vacuous("no spot offers two prices, so the multi-size schema is unexercisable here")


def test_a_jam_and_a_named_raise_collapse_into_one_raise_whose_parts_add(export) -> None:
    """`PREFLOP_ACTIONS` holds one raise, so two aggressive offers cannot both survive as
    actions - and `VACUOUS`, over the whole re-sourced export rather than only the 36.

    The rule is real and the artifact needs it: hero's weight on raising is the named raise
    plus the jam, because a row says what hero does rather than at what price, and dropping
    the jam leaves a row that does not sum to one. Decision 14 re-sourced with
    `add_allin: false`, and the consequence is stronger than decision 6 recorded: **not one
    node in the export offers both**, so nothing anywhere is left for the addition to add.
    """
    both = [n for n in export.nodes if {"raise", "jam"} <= {a.kind for a in n.actions}]
    assert both == []
    vacuous("no node in the export offers a named raise and a jam, so nothing collapses")


def test_two_prices_at_one_spot_are_both_priced_and_their_weights_add(derived) -> None:
    """Where the two vacuous rules above are actually proved: a synthetic export.

    A node offering hero fold, an open to 2.5, and the stack is the shape the multiway family
    will bring back and the shape the 2026-08-24 extension was ruled on. Converting it does
    the two halves of decision 6 at once: the table holds both prices in ascending order with
    hero's weight on each, so the split survives somewhere, and the row holds one `raise`
    weight equal to their sum, so it still says what hero does and sums to one. A converter
    taking the named raise and dropping the jam passes both vacuous tests above and fails
    here. The fixture keeps the ruled config because `config_errors` refuses an unruled one.
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
    `tests/test_solver_export.py` makes too, since these exercise a converter, not poker.
    """
    return SolverNode(
        path,
        actor,
        tuple(actions),
        tuple(array("H", [weight] * 169) for weight in split),
        array("H", [QUANTISATION_SCALE] * 169),
    )


def synthetic_export(open_to: float, jam: bool = False) -> SolverExport:
    """The smallest tree that carries an opening price *and* satisfies the ruled predicate.
    Four seats fold, the small blind opens, the big blind answers. The folds are what the
    predicate needs: six players live fails the subtree clause however heads-up the history
    is. Early seats get a fold and nothing else, so the opening price appears exactly once.
    `config` stays the ruled one while the labels move, since a converter reading
    `config["open_raises"][0]` is as hardcoded as one with 2.5 in it. With `jam` the opener
    also gets a shove, terminal so the tree needs no node below it.
    """
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


def test_the_synthetic_export_is_a_tree_the_reader_accepts() -> None:
    """The fixture is evidence only if it is a real export: were it rejected, the tests
    below would be red for a reason with nothing to do with the converter."""
    export = synthetic_export(2.5)
    opener = export.node((0, 0, 0, 0))
    shoving = synthetic_export(2.5, jam=True).node((0, 0, 0, 0))

    assert export.node_count == 6
    assert export.node(()).actor_pos == "LJ"
    assert opener.actor_pos == "SB"
    assert [action.label for action in opener.actions] == ["Fold", "Raise 2.5"]
    assert "call" not in {action.kind for action in opener.actions}
    assert [action.kind for action in shoving.actions] == ["fold", "raise", "jam"]


@pytest.mark.parametrize("open_to", [2.5, 3.75, 4.0])
def test_the_converter_reads_its_sizes_from_the_export_s_own_labels(open_to: float) -> None:
    """The contract's unfalsifiability criterion, and the hardest thing in this file.
    The solved config has one opening size and one multiplier, so a converter with the prices
    written into it produces a byte-identical artifact and passes every other test here;
    perturbing the label is the only thing that tells the two apart. 2.5 is the control - if
    the perturbed cases pass and it fails, prices are transformed rather than read. The key
    set and the class's entry are both pinned at each price, so the three cases together are
    the pair comparison an earlier round stated separately: two prices, two different charts.
    """
    chart = spec.derivation().derive_chart(synthetic_export(open_to))
    rfi_key = f"t{spec.TABLE_SIZE}/d{spec.DEPTH_BB}/SB/rfi"
    facing_key = f"t{spec.TABLE_SIZE}/d{spec.DEPTH_BB}/BB/SB:raise@{open_to:g}"
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


def test_a_node_the_converter_cannot_handle_raises_rather_than_being_filed() -> None:
    """The closure is load-bearing or it is decoration.
    An action kind nothing in this repo has a rule for is not "inexpressible in the spot
    vocabulary" - it is a converter meeting something it does not understand, and filing that
    as a property of the grammar turns a bug into a documented limitation. Nor is it
    excluded: neither clause of the predicate can be evaluated at a node whose kinds the walk
    cannot classify, because both count what a seat did. The reader validates shape rather
    than poker vocabulary and accepts the tree, so the converter must refuse by name.
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
        spec.derivation().census(export)
    with pytest.raises(ValueError, match="straddle"):
        spec.derivation().derive_chart(export)


# --- An excluded node is a refusal at the table, never a neighbouring cell ---


@pytest.fixture(scope="module")
def committed_library(derived, tmp_path_factory) -> PreflopChartLibrary:
    """The derived artifact, written out and imported the way the runtime imports it: a
    library built from what the converter emitted is what the bot answers from.
    """
    directory = tmp_path_factory.mktemp("derived-chart")
    path = directory / "six_max_100bb_rakefree.json"
    text = json.dumps(derived.artifact_payload, indent=2, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return PreflopChartLibrary.from_artifacts([import_preflop_artifact(path)])


@pytest.mark.parametrize(
    ("label", "path", "key", "sequence"),
    [
        # Re-derived on the 33,969-node export: the history clause alone selects 65 and the
        # subtree clause alone 4,865, so the two ways a node can miss the conjunction are 14
        # and 4,814. The retired build's 24 and 5,386 were counts over 38,828 nodes.
        ("the lojack's own open, one of the 14", spec.LOJACK_OPEN_PATH, spec.LOJACK_OPEN_KEY, ()),
        ("a cold-called line, one of the 4,814", spec.COLD_CALLED_PATH, spec.COLD_CALLED_KEY,
         spec.COLD_CALLED_SEQUENCE),
    ],
)
def test_an_excluded_node_is_refused_rather_than_answered_from_a_neighbour(
    committed_library: PreflopChartLibrary, by_path, walked, label: str,
    path: tuple[int, ...], key: str, sequence: tuple[PreflopAction, ...],
) -> None:
    """The point of the exclusion, asked as a query rather than asserted as prose.
    One node from each exclusion bucket, so a chart refusing only the obvious half fails.
    Both are legal spots with legal keys whose ranges were never committed: answering the
    lojack's open from the small blind's range, or the cold-called three-bet from the same
    three-bet without the flat, is a range hero never had and nothing downstream could tell.
    """
    node = by_path[path]
    query = ChartQuery(spec.TABLE_SIZE, spec.DEPTH_BB, node.actor_pos, sequence, "AA")
    refused = committed_library.lookup(query)

    assert not spec.predicate_selects(node, walked), label
    assert not spec.selected(node, walked), label
    assert spec.key_of(node, walked) == key
    assert query.spot_key == key
    assert key not in committed_library.spot_keys()
    assert isinstance(refused, ChartMiss), label
    assert refused.code == MISS_SPOT_NOT_COVERED
    assert refused.code in MISS_CODES
    assert refused.spot_key == key
    assert key in refused.detail


def test_a_committed_spot_is_still_answered(committed_library, walked) -> None:
    """A chart that refused everything would satisfy the test above.
    Two of the three are what the cutover is defended on - the big blind closing against a
    button open, and the one opening range that survives. The third is a five-bet call-off,
    which the withholding is easiest to over-apply to: filtering on "three or more raises"
    rather than "exactly three" drops all fifteen, lands on 21 committed spots, and leaves a
    chart that folds a hundred blinds holding aces.
    """
    for position, sequence, key, action in (
        ("BB", spec.TRACED_SEQUENCE, spec.TRACED_KEY, "raise"),
        ("SB", (), spec.SB_OPEN_KEY, "raise"),
        ("BTN", walked[spec.FIVE_BET_JAM_PATH][2], spec.FIVE_BET_JAM_KEY, "call"),
    ):
        answered = committed_library.lookup(
            ChartQuery(spec.TABLE_SIZE, spec.DEPTH_BB, position, sequence, PURE_CLASS)
        )
        assert not isinstance(answered, ChartMiss), getattr(answered, "detail", "")
        assert answered.spot_key == key
        assert answered.price_substitutions == ()
        assert dict(answered.action_weights)[action] > 0.0, key


# --- The external oracle is not regenerated by the thing it checks ---


def test_the_converter_does_not_write_the_expectations_file() -> None:
    """The contract's non-goal, asserted as behaviour rather than as intent.
    The expectations file holds the only numbers in this phase this repo did not produce,
    which is what catches a range uniformly wrong rather than merely self-consistent, and a
    reference regenerated from what it checks cannot fail. The mtime is checked as well as
    the bytes: rewriting with identical content is still a rewrite, and on the day the
    numbers behind it move nobody would notice.
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
