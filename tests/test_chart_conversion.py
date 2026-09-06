"""Phase 14: what a committed spot costs, and where its price came from.

Authored at stage 4, before the converter it specifies. The companion to
`tests/test_derived_chart.py`, split from it at the 700-line cap: that file owns the shape of
the artifact - the keys, the merge, the blind structure, the rows - and this one owns the
**price**.

**What this file owns.** The sizing table rederived in the same run as the chart while the
expectations file is not; the table holding every raise size a spot offers with hero's weight
on each, keyed by what hero faces; the prices being exactly `[2.5, 7.5, 22.5]`; the proof
that the converter reads a size off the export's own action label rather than off a constant,
taken by perturbing a synthetic export; both directions of the sizing invariant, the
no-raise half of which is vacuous here; the two-price schema, also vacuous here and proved
against a synthetic; and the jam-inversion canary, which runs against the export because
hero's own jam lives only at the four-bet-facing spots this phase excludes.

**What siblings own.** `tests/test_chart_derivation.py` owns which nodes are committed and
the census; this file imports its `selected` through `test_derived_chart`, which owns the
keying walk, the family split and the `vacuous` helper - imported here rather than copied so
that one file defines each. `tests/test_derived_chart_report.py` owns what gets printed.

Counts are recomputed here from the export by walks written in this file. Where a walk is
already written in `test_derived_chart.py` it is imported, because two copies of a walk is
two rules that can disagree, and the point of recomputing is to disagree with the *converter*.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

# The sibling that owns the artifact's shape, as a module: it carries this lane's walk, the
# family split, the `vacuous` label and the committed-node keying, and reaching them through
# the module means a rename lands as a per-test `AttributeError` rather than a collection
# error that would stop every assertion in both files from running.
import test_derived_chart as shape

# The derivation as a module for the same reason: the merge and the re-cut sizing table do
# not exist until stage 6.
from poker_training_bot.solver_artifacts import chart_derivation
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
from scripts.repo_paths import REPO_ROOT

PREFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
EXPECTATIONS_PATH = PREFLOP_DIR / "expectations" / "six_max_nl25_100bb.json"
SIZINGS_PATH = PREFLOP_DIR / "sizings" / "six_max_100bb_rakefree.json"
CONVERTER = REPO_ROOT / "scripts" / "convert_preflop_export.py"

SIZING_SCHEMA_VERSION = 2
STACK_BB = 100.0

HERO_PRICES = (2.5, 7.5, 22.5)
"""Exactly the three the contract names. The ladder is the 2.5 open times the 3.0 multiplier
once per raise already in, so it is derived from `RULED_CONFIG` below rather than trusted
here; the fourth rung is 67.5, which `allin_threshold` snaps to the stack, and it lives only
at the four-bet-facing spots this phase excludes."""

PRICE_BY_RAISES_FACED = {0: 2.5, 1: 7.5, 2: 22.5}
"""A spot's price is a function of what hero *faces* and of nothing else - not of his seat,
not of how many cold callers are in. That is what "keyed by what hero faces" means, and it is
the property `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` is stated against."""

SPOTS_OFFERING_A_PRICE = 249
SPOTS_OFFERING_NO_PRICE = 0
"""The two directions of decision 6's invariant over the committed set. The second is one of
the phase's three vacuous criteria: every committed spot offers hero a raise, so the half
that says a spot offering none carries no key has nothing to fire on."""

PRICED_CELLS = 2_562
"""Cells across the 249 whose *published* raise weight is positive, so the strategy has to be
able to ask what the raise is. It counts the merged flats: after decision 45 a class that the
solve only called publishes a raise, and a chart that says raise and cannot say how much is
the defect decision 6 exists to prevent."""

FOUR_BET_RAISES_FACED = 3
JAM_NODES = 4_257
JAM_NODES_BELOW_A_COMMITTED_SPOT = 219
JAM_NODES_WHERE_ACES_ARRIVE = 168
ACES_JAM_THE_WHOLE_RANGE_AT = 57
PAIR_INVERSIONS_ON_THE_JAM = 97
"""The jam canary's own figures, over the export rather than the chart. Every node offering
hero a jam faces three raises, so all 4,257 sit in the family this phase withholds; 219 of
them are one action below a committed spot, which is where a player following this chart
would walk into them. See the canary's own docstring for why the inversions are pinned as a
measurement and not gated."""

PAIRS = ("AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22")


@pytest.fixture(scope="module")
def export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def by_path(export: SolverExport) -> dict[tuple[int, ...], SolverNode]:
    return export.by_path()


@pytest.fixture(scope="module")
def derived(export: SolverExport):
    return chart_derivation.derive_chart(export)


def published_raise_bp(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode, hand_class_text: str
) -> int:
    """What the chart publishes as this cell's raise weight, in basis points.

    Decision 45's merge is part of the price question and not only of the row: at the twenty
    spots where the bot may not cold-call, a class the solve only *called* now publishes a
    raise, so the sizing table owes it a price. Recomputed from the solve rather than read
    off the chart, the chart being what is on trial.
    """
    solved = shape.solve_weights(node, hand_class_text)
    merged = shape.family_of(by_path, node) == shape.MERGED
    return solved["raise"] + (solved["call"] if merged else 0)


def offered_prices(node: SolverNode) -> list[float]:
    """Every price hero may raise to at a node, off the node's own action labels."""
    return sorted({float(a.to) for a in node.actions if a.kind in ("raise", "jam")})


def table_entries(payload: dict, key: str) -> dict[str, list[tuple[float, float]]]:
    """One spot's whole entry, read positionally - a reader that sorted the entries first
    could not tell an unordered table from an ordered one, and the order is what lets a
    reader pick the small price out without knowing the ladder."""
    return {
        name: [(float(e["to_bb"]), float(e["weight"])) for e in entries]
        for name, entries in payload["raise_to_bb"][key].items()
    }


def entries_agree(
    entries: list[tuple[float, float]], expected: list[tuple[float, float]]
) -> bool:
    """Whether a class's entry matches a recomputed one, price by price and in order. The
    tolerance is tight because nothing rules this field may be rounded, and rounding would
    drop a price a class takes rarely - turning one the chart cannot price into one it can."""
    if len(entries) != len(expected):
        return False
    return all(
        price == pytest.approx(other_price)
        and weight == pytest.approx(other_weight, rel=1e-9, abs=1e-12)
        for (price, weight), (other_price, other_weight) in zip(entries, expected, strict=True)
    )


# --- The prices the committed 249 offer hero -------------------------------------------


def test_the_price_ladder_is_the_one_the_solved_config_produces(
    export: SolverExport, by_path, derived
) -> None:
    """Prices exactly `[2.5, 7.5, 22.5]`, derived rather than listed, and keyed by what hero
    faces.

    The ladder is the config's own opening size times its own multiplier once per raise
    already in front of hero, so a re-solve at the ruled config cannot move it and a test
    that spelled the three numbers would be pinning a coincidence. The fourth rung, 67.5
    snapped to the stack by `allin_threshold`, is quoted only where hero faces a four-bet,
    and that family is withheld - so `100.0` is in no committed key and in no committed
    entry.

    **One price per spot is asserted, not assumed.** It is what makes the price a function of
    the spot key; a spot offering two would be the case decision 6's schema exists for, and
    over this artifact there is none.
    """
    open_to = float(RULED_CONFIG["open_raises"][0])
    multiplier = float(RULED_CONFIG["raise_mults"][0])
    keyed = shape.committed_nodes(export, by_path)
    by_faced: dict[int, set[float]] = {}
    for node in keyed.values():
        prices = offered_prices(node)
        faced = shape.raises_faced_of(by_path, node)

        assert len(prices) == 1, (faced, prices)
        assert prices[0] == pytest.approx(open_to * multiplier**faced)
        by_faced.setdefault(faced, set()).add(prices[0])

    quoted = {price for prices in by_faced.values() for price in prices}

    assert {faced: sorted(p)[0] for faced, p in by_faced.items()} == PRICE_BY_RAISES_FACED
    assert tuple(sorted(quoted)) == HERO_PRICES
    assert STACK_BB not in quoted
    assert all("@100" not in key for key in derived.artifact_payload["action_weights"])


def test_every_price_a_spot_offers_is_in_the_table_with_heros_weight_on_it(
    export: SolverExport, by_path, derived
) -> None:
    """The table against the export, spot by spot and class by class.

    Each property here hides a different defect. The table's keys are the committed spots
    exactly, so a table carrying a spot the chart does not hold prices a range nobody has.
    Its classes at a spot are the classes whose *published* raise weight is positive - which
    after decision 45's merge includes the flats - so a chart that says raise and cannot say
    how much fails here rather than at runtime. Weights are shares of that class's own
    published aggressive volume, so they sum to one and a fold does not dilute them; entries
    are ordered by price and never repeat a price; and every weight is strictly positive,
    a zero-weight entry being a price the solve never takes recorded as one it does.
    """
    keyed = shape.committed_nodes(export, by_path)
    sizes = derived.sizing_payload["raise_to_bb"]
    priced_cells = 0

    for key, node in keyed.items():
        prices = offered_prices(node)
        expected = {
            name: [(prices[0], 1.0)]
            for name in shape.arriving_classes(node)
            if published_raise_bp(by_path, node, name) > 0
        }
        table = table_entries(derived.sizing_payload, key)

        assert set(table) == set(expected), key
        for name, entries in table.items():
            quoted = [price for price, _ in entries]
            weights = [weight for _, weight in entries]

            assert entries_agree(entries, expected[name]), (key, name, entries)
            assert set(quoted) <= set(prices), (key, name)
            assert len(set(quoted)) == len(quoted), (key, name)
            assert quoted == sorted(quoted), (key, name)
            assert all(weight > 0.0 for weight in weights), (key, name)
            assert sum(weights) == pytest.approx(1.0, abs=1e-9), (key, name)
        priced_cells += len(table)

    assert derived.sizing_payload["schema_version"] == SIZING_SCHEMA_VERSION
    assert set(sizes) == set(keyed), "the table and the committed set differ"
    assert priced_cells == PRICED_CELLS


def test_a_spot_that_offers_a_raise_carries_a_key_and_a_class_that_never_raises_does_not(
    export: SolverExport, by_path, derived
) -> None:
    """The direction of the invariant that bites over the committed set.

    Every spot offering hero a raise carries a key for every size it offers - all 249 do -
    and within a spot, a class absent from the table is a hand hero only folds or flats. The
    second half is what stops the table being a per-spot number wearing a per-class shape:
    at the small blind's open 121 of the 169 classes raise and 48 do not, and a table that
    priced all 169 would be quoting an opening price for hands the solve never opens.
    """
    keyed = shape.committed_nodes(export, by_path)
    sizes = derived.sizing_payload["raise_to_bb"]
    priced = {key for key, node in keyed.items() if offered_prices(node)}
    silent = 0

    assert len(priced) == SPOTS_OFFERING_A_PRICE == len(keyed)
    assert set(sizes) == priced
    for key, node in keyed.items():
        raising = {
            name
            for name in shape.arriving_classes(node)
            if published_raise_bp(by_path, node, name) > 0
        }

        assert set(sizes[key]) == raising, key
        assert all(entries for entries in sizes[key].values()), key
        silent += len(shape.arriving_classes(node)) - len(raising)

    assert silent, "no committed row holds a class that never raises, so nothing was tested"


def test_a_committed_spot_that_prices_nothing_carries_no_key_at_all(
    export: SolverExport, by_path, derived
) -> None:
    """The other direction, and the second of the phase's three vacuous criteria.

    A committed spot whose menu offers hero no raise must be absent from the table entirely
    rather than carry a key holding an empty map: the second wears the first's shape and a
    reader cannot tell "nothing to price" from "priced nothing". The strategy then refuses
    when asked for a size rather than inventing one.

    Over the committed 249 no spot offers zero raises, so the rule has nothing to fire on.
    The premise is asserted before the label, and the rule is retained because the multiway
    family that returns once GTOpen can price it brings fold-or-call menus back with it.
    """
    keyed = shape.committed_nodes(export, by_path)
    unpriced = {key for key, node in keyed.items() if not offered_prices(node)}

    # The premise before the label. "No committed spot lacks a price" is equally true of no
    # committed spots at all, and the intersection below is then empty against anything, so
    # an empty walk would skip as VACUOUS having measured nothing.
    assert len(keyed) == SPOTS_OFFERING_A_PRICE
    assert len(unpriced) == SPOTS_OFFERING_NO_PRICE
    assert not (unpriced & set(derived.sizing_payload["raise_to_bb"]))
    shape.vacuous("every committed spot offers hero a raise, so none prices nothing")


def test_a_spot_offering_two_prices_is_described_by_both_of_them(derived) -> None:
    """Decision 6's headline case, and the first of the three vacuous criteria.

    The schema holds a *list* per hand class so a spot offering two raise sizes is described
    by two, which is how `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` closes. Over the
    committed 249 the case does not arise - `add_allin: false` removed the jam from every
    node that also offers a named raise, and the four-bet family that still jams is withheld
    - so every entry is a one-element list and the two-price assertion holds for want of
    anything to hold of. Decision 6 keeps the schema anyway, and requires this said plainly:
    a check that cannot fail must not be counted as one that passed. The case is proved
    against a synthetic export in the test below instead.
    """
    table = derived.sizing_payload["raise_to_bb"]
    lengths = {len(entries) for spot in table.values() for entries in spot.values()}

    # The premise before the label, for the same reason as the sibling above: `{1}` is what a
    # table holding a single one-element entry reads too, so the span is asserted first.
    assert len(table) == SPOTS_OFFERING_A_PRICE
    assert lengths == {1}, "a committed spot now offers two prices at one hand class"
    shape.vacuous("no committed spot offers two prices, so the multi-size schema is idle")


# --- The synthetic exports, where the vacuous cases are actually proved ------------------

FOLD_CONTINUES = SolverAction("Fold", "fold", 0.0, False)
FOLD_ENDS_IT = SolverAction("Fold", "fold", 0.0, True)
SYNTHETIC_RAISE_BP = 7_000
SYNTHETIC_JAM_BP = 2_000
SYNTHETIC_SPOTS = 6
"""Every node of the synthetic tree is committed: four seats fold with nothing multiway
below them, the small blind opens and the big blind answers heads-up, so no node's exposure
is above zero and none faces a third raise. The four folding seats offer no raise at all,
which is what makes this tree - and not the committed 249 - the place the no-raise half of
the invariant is actually exercised."""


def uniform_node(
    path: tuple[int, ...], actor: str, actions: list[SolverAction], split: tuple[int, ...]
) -> SolverNode:
    """A node whose every class plays the same mix and arrives in full. These exercise a
    converter rather than poker, so a flat range is the honest fixture."""
    from array import array

    return SolverNode(
        path,
        actor,
        tuple(actions),
        tuple(array("H", [weight] * 169) for weight in split),
        array("H", [QUANTISATION_SCALE] * 169),
    )


def synthetic_export(open_to: float, jam: bool = False) -> SolverExport:
    """The smallest tree carrying an opening price that every ruled clause admits.

    Four seats fold, the small blind opens, the big blind answers. `config` stays the ruled
    one while the *labels* move, because a converter reading `config["open_raises"][0]` is as
    hardcoded as one with 2.5 written into it - and it is the label the artifact has to
    follow, the config describing the solve rather than any one node.
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


def test_two_prices_at_one_spot_are_both_priced_and_their_weights_add() -> None:
    """Where the two vacuous rules above are actually proved.

    A node offering hero fold, an open to 2.5 and the stack is the shape the multiway family
    will bring back and the shape decision 6's 2026-08-24 extension was ruled on. Converting
    it does both halves at once: the table holds both prices in ascending order with hero's
    weight on each, and the artifact row holds one `raise` weight equal to their sum, so the
    row still says what hero *does* and still sums to one. A converter that dropped the jam
    fails only here.

    The four folding seats are the second proof: they offer no raise, so they must be absent
    from the table entirely rather than carry an empty entry.
    """
    chart = chart_derivation.derive_chart(synthetic_export(2.5, jam=True))
    rfi_key = f"t{shape.TABLE_SIZE}/d{shape.STACK_DEPTH_BB}/SB/rfi"
    entries = table_entries(chart.sizing_payload, rfi_key)["AA"]
    row = chart.artifact_payload["action_weights"][rfi_key]["AA"]
    named, shoved = SYNTHETIC_RAISE_BP, SYNTHETIC_JAM_BP

    assert [price for price, _ in entries] == pytest.approx([2.5, STACK_BB])
    assert [weight for _, weight in entries] == pytest.approx(
        [named / (named + shoved), shoved / (named + shoved)]
    )
    assert sum(weight for _, weight in entries) == pytest.approx(1.0, abs=1e-9)
    assert set(row) == {"fold", "raise"}
    assert row["raise"] == pytest.approx((named + shoved) / QUANTISATION_SCALE)
    assert row["raise"] > named / QUANTISATION_SCALE, "the jam's weight was dropped"

    assert chart.census.committed == SYNTHETIC_SPOTS
    assert set(chart.sizing_payload["raise_to_bb"]) == {rfi_key}
    for seat in ("LJ", "HJ", "CO", "BTN"):
        folding = f"t{shape.TABLE_SIZE}/d{shape.STACK_DEPTH_BB}/{seat}/rfi"
        assert folding in chart.artifact_payload["action_weights"]
        assert folding not in chart.sizing_payload["raise_to_bb"], seat


@pytest.mark.parametrize("open_to", [2.5, 3.75, 4.0])
def test_the_converter_reads_its_sizes_from_the_exports_own_labels(open_to: float) -> None:
    """The contract's unfalsifiability criterion, and the hardest thing in this file.

    The solved config has one opening size and one multiplier, so a converter with the three
    prices written into it produces a byte-identical artifact and passes every other test
    here. Perturbing the label is the only thing that tells the two apart: the fixture keeps
    the ruled config and moves only the action's own `to`, so a converter reading the config,
    a constant, or a ladder derived from either lands on 2.5 and fails at 3.75 and 4.0.

    2.5 is the control. If the perturbed cases pass and the control fails, prices are being
    transformed rather than read, which is a different defect with the same symptom.
    """
    built = synthetic_export(open_to)
    chart = chart_derivation.derive_chart(built)
    rfi_key = f"t{shape.TABLE_SIZE}/d{shape.STACK_DEPTH_BB}/SB/rfi"
    facing_key = f"t{shape.TABLE_SIZE}/d{shape.STACK_DEPTH_BB}/BB/SB:raise@{open_to:g}"
    opened = table_entries(chart.sizing_payload, rfi_key)

    # The fixture is evidence only if the reader accepts it as a real export; were it
    # rejected, everything below would be red for a reason with nothing to do with prices.
    assert built.node_count == SYNTHETIC_SPOTS and built.node(()).actor_pos == "LJ"
    assert built.node((0, 0, 0, 0)).actor_pos == "SB"
    assert [a.label for a in built.node((0, 0, 0, 0)).actions] == ["Fold", f"Raise {open_to}"]

    assert facing_key in chart.artifact_payload["action_weights"]
    assert set(chart.sizing_payload["raise_to_bb"]) == {rfi_key}
    assert set(opened) == set(HAND_CLASSES)
    assert all(entries_agree(e, [(open_to, 1.0)]) for e in opened.values()), opened


def test_a_node_the_converter_cannot_classify_raises_rather_than_being_filed() -> None:
    """The closed reason vocabulary is load-bearing or it is decoration.

    An action kind nothing in this repo has a rule for is not "inexpressible in the spot
    grammar" - it is a converter meeting something it does not understand, and filing that as
    a property of the grammar turns a bug into a documented limitation. Nor is it excluded:
    no clause of the selection rule can be evaluated at a node whose kinds the walk cannot
    classify. The reader accepts the tree, so the converter must refuse by name.
    """
    straddle = SolverAction("Straddle 2", "straddle", 0.0, False)
    call = SolverAction("Call 2", "call", 2.0, True)
    built = SolverExport.from_nodes(
        [
            uniform_node((), "LJ", [FOLD_ENDS_IT, straddle], (3_000, 7_000)),
            uniform_node((1,), "HJ", [FOLD_ENDS_IT, call], (6_000, 4_000)),
        ],
        config=dict(RULED_CONFIG),
        positions=list(RULED_CONFIG["positions"]),
    )

    with pytest.raises(ValueError, match="straddle"):
        chart_derivation.census(built)
    with pytest.raises(ValueError, match="straddle"):
        chart_derivation.derive_chart(built)


# --- The table is rederived; the external oracle is not ---------------------------------


def test_the_sizing_table_is_rederived_in_the_same_run_and_the_oracle_is_not() -> None:
    """Two files, two opposite obligations, asserted against the converter's own outputs.

    The sizing table is derived from the export and must be rewritten whenever the chart is,
    or the bot reads new ranges at old prices. The expectations file holds the only figures
    in this phase this repo did not produce - which is what catches a chart uniformly wrong
    rather than merely self-consistent - so the thing being checked must not be able to
    regenerate its own oracle.

    `outputs()` is the converter's own list of what it writes, so this is asserted against
    the converter rather than against a run that happened to touch nothing. The mtime is
    checked beside the bytes because rewriting a file with identical content is still a
    write, and `--check` is then run for real rather than after a write that guaranteed its
    answer.
    """
    import scripts.convert_preflop_export as converter

    assert EXPECTATIONS_PATH.exists(), f"the external oracle is missing at {EXPECTATIONS_PATH}"
    before = EXPECTATIONS_PATH.read_bytes()
    before_mtime = EXPECTATIONS_PATH.stat().st_mtime_ns
    writes = {path.resolve() for path, _ in converter.outputs()}

    assert writes, "the converter declares no outputs, so this proves nothing about either"
    assert SIZINGS_PATH.resolve() in writes, sorted(str(path) for path in writes)
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


# --- The jam canary, which runs against the export because the chart cannot jam ---------


def test_heros_own_jam_lives_only_at_the_four_bet_facing_spots_the_phase_excludes(
    export: SolverExport, by_path, derived
) -> None:
    """The containment half of the canary, and the half that is strict.

    The canary that rejected the first cutover caught a chart telling hero to put a hundred
    blinds in where the solve raises to seven and a half. This export cannot produce that at
    a committed spot: every one of the 4,257 nodes offering hero a jam faces three raises
    already, and `raises_faced <= 2` withholds all of them. So the claim is asserted where it
    can fail - the jam family is exactly the four-bet-facing family, none of it is committed,
    and neither `100.0` nor a `@100` key reaches the chart or its table.
    """
    jam_nodes = [n for n in export.nodes if any(a.kind == "jam" for a in n.actions)]
    keyed = shape.committed_nodes(export, by_path)
    quoted = {
        entry["to_bb"]
        for spot in derived.sizing_payload["raise_to_bb"].values()
        for entries in spot.values()
        for entry in entries
    }

    assert len(jam_nodes) == JAM_NODES
    assert {shape.raises_faced_of(by_path, n) for n in jam_nodes} == {FOUR_BET_RAISES_FACED}
    assert not ({n.path for n in jam_nodes} & {n.path for n in keyed.values()})
    assert STACK_BB not in quoted
    assert all("@100" not in key for key in derived.sizing_payload["raise_to_bb"])


def test_no_committed_node_offers_a_jam_beside_a_named_raise(export, by_path) -> None:
    """The third of the contract's three vacuous criteria, with its premise asserted.

    `_cell_weights` records a jam and a named raise as one `raise` and adds their weights,
    because `PREFLOP_ACTIONS` holds one raise and dropping either would leave a row that does
    not sum to one. Under `add_allin: false` no committed node offers both, so over the 249
    the collapse never fires and the artifact's raise weight is always a single action's.

    The rule is retained because `add_allin: true`, or a solve whose `allin_threshold` snaps a
    named raise to the stack inside the committed depth, reactivates it; it is proved on a
    synthetic above. The premise is asserted first so that solve turns this red rather than
    leaving a stale skip, and it is asserted over the whole menu rather than over the jam
    alone: a node offering only a jam would not collapse either, and would not be this rule.
    """
    keyed = shape.committed_nodes(export, by_path)
    jamming = {key for key, node in keyed.items() if any(a.kind == "jam" for a in node.actions)}
    both = {
        key
        for key, node in keyed.items()
        if any(a.kind == "jam" for a in node.actions)
        and any(a.kind == "raise" for a in node.actions)
    }

    assert len(keyed) == SPOTS_OFFERING_A_PRICE
    assert jamming == set()
    assert both == set()
    shape.vacuous("no committed node offers a jam, so the collapse to one raise never fires")


def test_the_jam_inversion_canary_is_measured_against_the_export(export, by_path) -> None:
    """The canary retained against the export, and what it finds there, pinned.

    Decision 6 keeps this check on the ground that the defect it exists to catch - a weaker
    class committing a hundred blinds where aces do not - has to stay measured even after
    the family that can express it leaves the chart. Over this export the family is the 4,257
    four-bet-facing nodes; the 219 that sit one action below a committed spot are the ones a
    player following this chart walks into, so they are where the canary is taken.

    **What it finds is not clean, and the number is recorded rather than softened.** Aces
    arrive at 168 of the 219 and jam their whole range at 57. At the rest, 97 comparisons
    have a lower pocket pair jamming more often than aces do, both classes arriving - kings
    jamming 100 percent where aces jam 12 is the worst of them. That is decision 50's
    raise-action inversion in the family this phase withholds, and decisions 41, 47, 50 and
    51 accept inversions of that kind as solved, so it is **not** gated here: gating it would
    be this lane overturning four rulings. It is pinned as a measurement instead, so a later
    solve that repairs the family turns this red and whoever sees it re-reads the exclusion
    rather than inheriting it. The report prints aces' jam weight at these spots.
    """
    committed_paths = {node.path for node in shape.committed_nodes(export, by_path).values()}
    below = [
        node
        for node in export.nodes
        if node.path[:-1] in committed_paths and any(a.kind == "jam" for a in node.actions)
    ]

    def jam_bp(node: SolverNode, name: str) -> int:
        column = gtopen_class_index(name)
        return sum(
            node.strategy_bp[index][column]
            for index, action in enumerate(node.actions)
            if action.kind == "jam"
        )

    with_aces = [n for n in below if n.reach_bp[gtopen_class_index("AA")] > 0]
    pure = [n for n in with_aces if jam_bp(n, "AA") == QUANTISATION_SCALE]
    inversions = [
        (node.path, name)
        for node in with_aces
        for name in PAIRS[1:]
        if node.reach_bp[gtopen_class_index(name)] > 0
        and jam_bp(node, name) > jam_bp(node, "AA")
    ]

    assert len(below) == JAM_NODES_BELOW_A_COMMITTED_SPOT
    assert len(with_aces) == JAM_NODES_WHERE_ACES_ARRIVE
    assert len(pure) == ACES_JAM_THE_WHOLE_RANGE_AT
    assert len(inversions) == PAIR_INVERSIONS_ON_THE_JAM
    assert set(PAIRS) <= set(HAND_CLASSES)
