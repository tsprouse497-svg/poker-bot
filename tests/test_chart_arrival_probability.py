"""Phase 14: how often a committed line is played at all, and how much of hero's range gets there.

**What this file owns**, and it owns nothing else in the phase. Arriving reach as the plain mean
over the 169 hand classes, with no reach floor selecting cells. Arrival probability as one
left-to-right product from the root rounded once at the end, refused at construction when it is
above one or claimed for a spot the chart does not declare. The grain, published with the count of
committed spots whose arrival rounds to zero. And one committed cell traced from the root to its
artifact row with its reach and its arrival, which is the trace the contract asks a non-coding
reviewer to be able to follow.

**What the siblings own.** `tests/test_chart_derivation.py` owns the selection and the census, and
this file imports `selected` and `COMMITTED_NODES` from it rather than restate a rule it does not
own. `tests/test_derived_chart.py` owns the artifact's shape and the dropping of zero-reach
classes; `tests/test_chart_cutover_evidence.py` the relations and both arms;
`tests/test_derived_chart_report.py` what the report prints. A number this file asserts is a number
no other file defines.

**Re-cut at stage 4 on 2026-09-02 against the committed 249**, superseding a cut written against a
six-spot set. That cut recorded two of this field's criteria as unexercised: no committed line
arrived at zero, and the rarest arrived at 1,280 basis points, so parts per billion bought nothing.
**Both statements are now false** - over the 249, **44** spots round to zero in parts per billion
and **2** arrive at exactly zero - which is why the contract says in as many words that the
zero-arrival case is not vacuous. So there is no vacuous criterion here and no `vacuous()` helper:
the one convention this file drops, dropped because the data changed, not the convention.

**Arrival and reach are different questions and the chart needs both.** Reach is per cell and says
whether hero can be holding that class here; arrival is per spot and says whether the line is one
anybody plays. A spot can carry every class at full reach and never be reached at all, which is
what `ARRIVING-REACH-IS-NOT-A-TRAINED-NESS-MEASURE` records and what the two zero spots are.

**What this file does not assert.** No threshold, on either field. Nothing here refuses a cell for
arriving rarely or a spot for being seldom played: the chart commits them and records the number so
that phase 15 can rule on its drill sampling with the distribution in front of it
(`A-SIXTH-OF-THE-COMMITTED-SET-IS-ALMOST-NEVER-DEALT`).
"""

from __future__ import annotations

import pytest

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts import schema
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    class_combos,
    gtopen_class_index,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, hand_class_grid_index
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.solver_artifacts.schema import (
    ARTIFACT_SCHEMA_VERSION,
    ArtifactAuditFields,
    ArtifactSource,
    PreflopAction,
    PreflopArtifact,
    SpotDefinition,
    spot_key,
    weights_checksum,
)
from scripts.repo_paths import REPO_ROOT

TABLE_SIZE = 6
STACK_DEPTH_BB = 100

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"

PARTS_PER_BILLION = 1_000_000_000
HAND_CLASS_COUNT = 169


# --- The spots this file names, and every figure it pins ---

BUSIEST_SPOT = "t6/d100/LJ/rfi"
BUSIEST_PPB = PARTS_PER_BILLION
"""The lojack first-in is the root of the tree, so its line is played in every hand and its arrival
is exactly one. It is a committed spot - one of the five first-in - which makes the boundary a live
case rather than a hypothetical: the refusal has to be *strictly* above one, and a validator
written as "a probability below one" would delete the commonest spot in the chart."""

TRACED_PATH = (1, 2, 0, 0, 0, 0)
TRACED_KEY = "t6/d100/LJ/LJ:raise@2.5,HJ:raise@7.5"
TRACED_SEQUENCE = (
    PreflopAction("LJ", "raise", 2.5),
    PreflopAction("HJ", "raise", 7.5),
)
"""The traced cell's spot: the lojack opens to 2.5, the hijack three-bets to 7.5, everybody folds,
and the lojack is back in facing the three-bet heads-up. It cannot stop being committed - two
raises are in and nothing deeper, only two players are live so no flop below it can be multiway at
all, and hero is not the big blind. It is chosen because one node carries all four of this file's
subjects: hero has acted, so its reach is a real range rather than a full grid; the plain and
combo-weighted readings of that range disagree by 737 basis points; nine of its cells sit below the
retired reach floor; and rounding once and rounding at each step give different answers here."""

TRACED_ARRIVAL_PPB = 11_490_264
TRACED_ARRIVAL_ROUNDED_AT_EACH_STEP = 11_490_262
"""The same six frequencies accumulated the two ways the contract distinguishes. Rounding once at
the end gives 11,490,264; carrying parts per billion as an integer and rounding after every factor
gives 11,490,262. Two in eleven million is nothing to a poker decision and everything to a check
claiming to pin how the number is computed."""

TRACED_REACH_SUM_BP = 441_201
TRACED_CLASSES_AT_NON_ZERO_REACH = 55
TRACED_PLAIN_MEAN_REACH_BP = TRACED_REACH_SUM_BP / HAND_CLASS_COUNT
TRACED_COMBO_WEIGHTED_REACH_BP = 1_873.9683257918552
"""2,610.66 against 1,873.97 basis points for the same arriving range. The plain mean is ruled; the
combo-weighted one is what a reader who thinks in combinations computes from the same words, and it
is wrong by 737 basis points here. The disagreement is asserted rather than assumed."""

RETIRED_REACH_FLOOR_BP = 200
TRACED_CELLS_BELOW_THE_RETIRED_FLOOR = 9
TRACED_THINNEST_CELL_BP = 1
"""Decision 1's 2-percent reach floor is retired, and this is what retiring it is worth at one
spot: nine of the traced spot's fifty-five answered cells arrive less than 2 percent of the time,
the thinnest at a single basis point. A floor is therefore not a no-op that could be left in the
code unnoticed - reinstating any floor at all would visibly empty cells the chart answers."""

SPOTS_ROUNDING_TO_ZERO = 44
SPOTS_TRUNCATING_TO_ZERO = 45
SPOTS_BETWEEN_HALF_AND_ONE_PPB = 1
SPOTS_AT_EXACTLY_ZERO = 2
"""The grain, over the committed 249 (decision 53, and
`A-SIXTH-OF-THE-COMMITTED-SET-IS-ALMOST-NEVER-DEALT`). 44 under the repo's own rule,
`round(p * 1e9) == 0`, which is strictly below half a part per billion; 45 if the same field were
truncated instead, because one spot sits between 0.5 and 1.0 parts per billion. Only 2 arrive at
exactly zero. The gap between 44 and 45 is one spot and the rounding rule is the whole of what
decides it, so the rule is pinned here and not only its count."""


# --- The walks, written here rather than imported from the rule they check ---


def node_action_sequence(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> tuple[PreflopAction, ...]:
    """The live actions in front of hero, recomputed rather than imported.

    The actor of an action is whoever was to act at the node it was taken at - the *parent* of the
    node it leads to. Reading it off the child shifts every entry one seat down the ring and keys a
    spot that never happened while validating perfectly. Folds never enter: an empty sequence means
    the pot was folded to hero, and a recorded fold would be a second spelling of the same spot.
    """
    entries: list[PreflopAction] = []
    for depth, index in enumerate(node.path):
        parent = by_path[node.path[:depth]]
        action = parent.actions[index]
        if action.kind == "fold":
            continue
        if action.kind == "call":
            entries.append(PreflopAction(parent.actor_pos, "call"))
            continue
        entries.append(PreflopAction(parent.actor_pos, "raise", float(action.to)))
    return tuple(entries)


def key_of(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> str:
    return spot_key(
        TABLE_SIZE, STACK_DEPTH_BB, node.actor_pos, node_action_sequence(by_path, node)
    )


def step_frequencies(
    by_path: dict[tuple[int, ...], SolverNode], path: tuple[int, ...]
) -> list[float]:
    """Each parent's own frequency for the action taken, from the root down to the node.

    `SolverNode.action_frequency` is the solver's own combo-weighted, reach-weighted figure, so
    this multiplies the numbers GTOpen publishes rather than deriving a second definition of them.
    """
    frequencies: list[float] = []
    walked: tuple[int, ...] = ()
    for index in path:
        frequencies.append(by_path[walked].action_frequency(index))
        walked = (*walked, index)
    return frequencies


def arrival_probability(
    by_path: dict[tuple[int, ...], SolverNode], path: tuple[int, ...]
) -> float:
    """The unrounded left-to-right product, which is the only place the grain is still visible."""
    probability = 1.0
    for frequency in step_frequencies(by_path, path):
        probability *= frequency
    return probability


def arrival_ppb_rounded_once(
    by_path: dict[tuple[int, ...], SolverNode], path: tuple[int, ...]
) -> int:
    """The ruled accumulation: a left-to-right float product, rounded once at the end."""
    return round(arrival_probability(by_path, path) * PARTS_PER_BILLION)


def arrival_ppb_rounded_at_each_step(
    by_path: dict[tuple[int, ...], SolverNode], path: tuple[int, ...]
) -> int:
    """The accumulation the contract rules out: parts per billion carried as an integer.

    The natural implementation for anyone who reads "parts per billion" as the unit the quantity is
    held in rather than the unit it is reported in. It disagrees with the ruled one at 56 nodes of
    the tree this phase selects from, which is what lets the check on the ruled reading
    discriminate rather than merely agree with itself.
    """
    probability = PARTS_PER_BILLION
    for frequency in step_frequencies(by_path, path):
        probability = round(probability * frequency)
    return probability


def plain_mean_reach_bp(node: SolverNode) -> float:
    """The ruled reading: the plain mean of the arriving reach over the 169 classes."""
    return sum(node.reach_bp) / HAND_CLASS_COUNT


def combo_weighted_reach_bp(node: SolverNode) -> float:
    """The other reading of the same words, weighting each class by its combinations."""
    weighted = sum(
        node.reach_bp[gtopen_class_index(name)] * class_combos(name) for name in HAND_CLASSES
    )
    return weighted / sum(class_combos(name) for name in HAND_CLASSES)


def arriving_classes(node: SolverNode) -> set[str]:
    """The classes hero can be holding at a node: the only rule that selects a cell."""
    return {name for name in HAND_CLASSES if node.reach_bp[gtopen_class_index(name)] > 0}


# --- Fixtures ---


@pytest.fixture(scope="module")
def export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def by_path(export: SolverExport) -> dict[tuple[int, ...], SolverNode]:
    return export.by_path()


@pytest.fixture(scope="module")
def selection():
    """`tests/test_chart_derivation.py`, reached through a fixture rather than imported at the top.

    That file owns the selection rule and is rewritten alongside this one. A module-level import of
    a sibling mid-rewrite stops this file collecting, and a file that does not collect runs none of
    its assertions - which is how a previous cut froze a completed phase's tests having never
    executed one (`LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`).
    """
    import test_chart_derivation as module

    return module


@pytest.fixture(scope="module")
def committed(selection, export: SolverExport) -> tuple[SolverNode, ...]:
    """The 249 nodes the phase commits, taken from the file that owns the rule that picks them."""
    nodes = tuple(selection.selected(export))
    assert len(nodes) == selection.COMMITTED_NODES
    return nodes


@pytest.fixture(scope="module")
def derivation():
    """The module stage 6 finishes, imported in the function body for the same reason."""
    import poker_training_bot.solver_artifacts.chart_derivation as module

    return module


@pytest.fixture(scope="module")
def derived(export: SolverExport, derivation):
    return derivation.derive_chart(export)


@pytest.fixture(scope="module")
def artifact() -> PreflopArtifact:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR)).artifacts[0]


@pytest.fixture(scope="module")
def recorded_arrival(artifact: PreflopArtifact) -> dict[str, int]:
    assert artifact.arrival_ppb is not None, "the artifact records no arrival probabilities at all"
    return dict(artifact.arrival_ppb)


# --- Arrival: the field, its accumulation, and its grain ---


def test_arrival_is_recorded_for_every_committed_spot_and_for_no_other(
    recorded_arrival: dict[str, int],
    artifact: PreflopArtifact,
    committed: tuple[SolverNode, ...],
    by_path: dict[tuple[int, ...], SolverNode],
) -> None:
    """The field, checked against the export at every committed spot rather than at a sample.

    A spot-level number is the right grain where a cell-level one was right for reach: whether a
    line gets played is a property of the line, and the 169 classes at a node all share it. The map
    may hold nothing else - a declared spot with no arrival is a converter that did not compute the
    field, and an arrival for an undeclared spot is a figure about a line nobody asks about.
    """
    measured = {
        key_of(by_path, node): arrival_ppb_rounded_once(by_path, node.path) for node in committed
    }

    assert len(measured) == len(committed), "two committed nodes derived one key"
    assert set(recorded_arrival) == {spot.spot_id for spot in artifact.spots}
    assert set(recorded_arrival) == set(measured)

    for key, value in recorded_arrival.items():
        assert isinstance(value, int) and not isinstance(value, bool), key
        assert 0 <= value <= PARTS_PER_BILLION, (key, value)
        assert value == measured[key], key


def test_the_commonest_committed_line_arrives_at_exactly_one_and_is_kept(
    recorded_arrival: dict[str, int],
) -> None:
    """One is a value the chart really holds, so the refusal above it has to be strict.

    The lojack's first-in spot is the root of the solved tree: every hand passes through it, its
    arrival is one, and it is committed. A validator written as "a probability is below one" would
    reject the artifact at the commonest spot in it. Asserting the value here is what makes the
    refusal test below a boundary test rather than a test of an arbitrary large number.
    """
    assert BUSIEST_SPOT in recorded_arrival, "the chart does not answer the lojack's open"
    assert recorded_arrival[BUSIEST_SPOT] == BUSIEST_PPB
    assert recorded_arrival[BUSIEST_SPOT] == max(recorded_arrival.values())


def test_arrival_is_one_product_rounded_once_and_not_rounded_at_each_step(
    recorded_arrival: dict[str, int],
    committed: tuple[SolverNode, ...],
    by_path: dict[tuple[int, ...], SolverNode],
) -> None:
    """The accumulation, tested where the two readings actually disagree.

    A test that only recomputed the field the way the converter does would pass against either
    implementation, so this one names the alternative and shows it giving a different answer. At
    the traced spot the ruled reading gives 11,490,264 and rounding at each step gives 11,490,262.
    Both readings are then run across the whole committed set: every recorded value is the
    round-once one, and at least one committed spot is a spot where saying so is a claim rather
    than a coincidence.

    The *direction* of the product is not pinned here and this file says so rather than pretending
    otherwise. Multiplying the same factors right to left changes the float in its last bits and
    changes no committed spot's parts-per-billion value, so "left to right" has no failing case on
    this export and no test written here could have one.
    """
    once = arrival_ppb_rounded_once(by_path, TRACED_PATH)
    each_step = arrival_ppb_rounded_at_each_step(by_path, TRACED_PATH)

    assert TRACED_KEY in recorded_arrival, "the chart does not answer the traced spot"
    assert once == TRACED_ARRIVAL_PPB
    assert each_step == TRACED_ARRIVAL_ROUNDED_AT_EACH_STEP
    assert once != each_step, "the traced spot no longer separates the two accumulations"
    assert recorded_arrival[TRACED_KEY] == once

    disagreeing = []
    for node in committed:
        key = key_of(by_path, node)
        ruled = arrival_ppb_rounded_once(by_path, node.path)
        assert recorded_arrival[key] == ruled, key
        if ruled != arrival_ppb_rounded_at_each_step(by_path, node.path):
            disagreeing.append(key)

    assert disagreeing, "no committed spot separates the two accumulations, so nothing pins one"
    assert TRACED_KEY in disagreeing


def test_the_grain_is_published_as_the_count_of_spots_that_round_to_zero(
    recorded_arrival: dict[str, int],
) -> None:
    """The published grain, read off the artifact: 44 of the 249 record an arrival of zero.

    The contract asks for the count because arrival here runs from one down to about 1e-26, and a
    reader given only the values cannot see how much of the chart is effectively never dealt. What
    the artifact can show is the count and that nothing in the map is negative; which rounding rule
    produced 44 rather than 45 is only visible before the field is written, and the sibling test
    below measures it there.
    """
    values = list(recorded_arrival.values())

    assert values
    assert sum(1 for value in values if value == 0) == SPOTS_ROUNDING_TO_ZERO
    assert min(values) == 0, "no committed spot rounds to zero, which would move the grain line"
    assert SPOTS_TRUNCATING_TO_ZERO - SPOTS_ROUNDING_TO_ZERO == SPOTS_BETWEEN_HALF_AND_ONE_PPB


def test_the_grain_counts_are_measured_from_the_export_under_both_rounding_rules(
    committed: tuple[SolverNode, ...], by_path: dict[tuple[int, ...], SolverNode]
) -> None:
    """The rule that decides 44 from 45, measured where the distinction still exists.

    The artifact only ever stores the rounded value, so once the field is written the difference
    between rounding and truncating is gone. Measured on the unrounded product: 44 committed spots
    are strictly below half a part per billion, 45 are below one, and the single spot between them
    is the whole of the difference. A test that pinned only the count would go green against a
    converter that had quietly changed how it rounds.

    Only 2 of the 249 arrive at exactly zero, which is the other half of why the grain is worth
    printing: 42 spots that the field cannot tell from never-played are in fact played, just not in
    any hand a student will ever be dealt.
    """
    products = [arrival_probability(by_path, node.path) for node in committed]

    assert len(products) == len(committed)
    assert sum(1 for p in products if round(p * PARTS_PER_BILLION) == 0) == SPOTS_ROUNDING_TO_ZERO
    assert sum(1 for p in products if int(p * PARTS_PER_BILLION) == 0) == SPOTS_TRUNCATING_TO_ZERO
    assert (
        sum(1 for p in products if 0.5 <= p * PARTS_PER_BILLION < 1.0)
        == SPOTS_BETWEEN_HALF_AND_ONE_PPB
    )
    assert sum(1 for p in products if p == 0.0) == SPOTS_AT_EXACTLY_ZERO


def test_the_spots_the_solve_never_reaches_are_recorded_at_zero_and_still_answer(
    recorded_arrival: dict[str, int],
    artifact: PreflopArtifact,
    committed: tuple[SolverNode, ...],
    by_path: dict[tuple[int, ...], SolverNode],
) -> None:
    """The zero case, which over this committed set is real and is not labelled vacuous.

    Two of the 249 are lines the solve gives no weight to at all, and 44 are lines it gives so
    little weight to that the field cannot tell them from zero. The contract states in as many
    words that this case is not vacuous, and this is where that claim is measured rather than
    asserted in prose: a cut of this file that skipped here would be describing the retired
    six-spot set, where the case really was empty.

    Both halves matter. A spot at zero arrival is still a spot the chart answers - blanking an
    untrained cell is what the 2026-08-27 ruling refused, because a refused cell is visibly empty
    and a heuristic layer can find it while a committed one that was never computed looks exactly
    like one that was. So every zero-arrival spot must still carry cells.
    """
    weights = dict(artifact.action_weights)
    never_reached = sorted(key for key, value in recorded_arrival.items() if value == 0)
    measured_zero = sorted(
        key_of(by_path, node)
        for node in committed
        if arrival_ppb_rounded_once(by_path, node.path) == 0
    )

    assert never_reached, "the zero-arrival case is not vacuous over the committed set"
    assert never_reached == measured_zero
    assert len(never_reached) == SPOTS_ROUNDING_TO_ZERO
    for key in never_reached:
        assert weights[key], f"{key} arrives at zero and answers nothing, so it is not committed"


# --- Reach: the plain mean, and the absence of a floor ---


def test_arriving_reach_is_the_plain_mean_over_the_169_classes(
    committed: tuple[SolverNode, ...], by_path: dict[tuple[int, ...], SolverNode], derivation
) -> None:
    """The reading, tested at a spot where the two readings give different numbers.

    "The mean over the 169 classes" has a plain reading and a combination-weighted one, and they
    are different numbers for the same words: at the traced spot 2,610.66 against 1,873.97 basis
    points. The plain one is ruled. Asserting it at every committed spot alone would pass against
    either implementation at the thirty spots where hero has not yet acted and every class arrives
    at 10,000 basis points, so the traced spot - where hero opened and his arriving range is a real
    one - is what makes this test discriminate.
    """
    node = by_path[TRACED_PATH]

    assert sum(node.reach_bp) == TRACED_REACH_SUM_BP
    assert plain_mean_reach_bp(node) == TRACED_PLAIN_MEAN_REACH_BP
    assert combo_weighted_reach_bp(node) == pytest.approx(TRACED_COMBO_WEIGHTED_REACH_BP)
    assert plain_mean_reach_bp(node) != pytest.approx(combo_weighted_reach_bp(node)), (
        "the traced spot's two readings of reach now agree, so this test discriminates nothing"
    )
    assert derivation.node_reach_bp(node) == plain_mean_reach_bp(node)

    for committed_node in committed:
        assert derivation.node_reach_bp(committed_node) == plain_mean_reach_bp(committed_node)


def test_no_reach_floor_selects_the_cells_a_committed_spot_answers(
    artifact: PreflopArtifact,
    committed: tuple[SolverNode, ...],
    by_path: dict[tuple[int, ...], SolverNode],
) -> None:
    """The published cells are the classes that arrive, and nothing thinner than that is dropped.

    Decision 1's 2-percent reach floor is retired rather than retuned, and "retired" is a claim
    about the data, not only about whether a constant survives in a module. What makes it checkable
    is that a floor would not be a no-op: nine of the traced spot's fifty-five answered cells
    arrive less than 2 percent of the time, the thinnest at one basis point in ten thousand, and
    every one is a cell the chart answers. Reinstating any floor at all - 200, 100, or 10 - would
    empty cells that are answered today. The only rule that selects a cell is that hero can be
    holding the class at all, so at every committed spot the reach map and the weights cover
    exactly the classes at non-zero reach.
    """
    reach_index = {spot_id: dict(cells) for spot_id, cells in artifact.arriving_reach_bp}
    weights = dict(artifact.action_weights)

    assert TRACED_KEY in reach_index, "the chart records no arriving reach at the traced spot"
    traced = reach_index[TRACED_KEY]
    assert len(traced) == TRACED_CLASSES_AT_NON_ZERO_REACH
    assert min(traced.values()) == TRACED_THINNEST_CELL_BP
    assert sum(1 for bp in traced.values() if bp < RETIRED_REACH_FLOOR_BP) == (
        TRACED_CELLS_BELOW_THE_RETIRED_FLOOR
    )
    for floor in (10, 100, RETIRED_REACH_FLOOR_BP):
        assert any(bp < floor for bp in traced.values()), (
            f"a floor at {floor} basis points would select nothing, so nothing here proves"
            " that reinstating one would change the chart"
        )

    for node in committed:
        key = key_of(by_path, node)
        arriving = arriving_classes(node)
        assert set(reach_index[key]) == arriving, key
        assert {name for name, _ in weights[key]} == arriving, key


# --- The trace the contract asks a non-coding reviewer to follow ---


def test_one_committed_cell_traced_from_the_root_to_its_artifact_row(
    by_path: dict[tuple[int, ...], SolverNode],
    recorded_arrival: dict[str, int],
    artifact: PreflopArtifact,
    derived,
) -> None:
    """The end-to-end trace: a named spot, its line, its six frequencies, and their product.

    The lojack opens to 2.5, the hijack three-bets to 7.5, the cutoff, button, small blind and big
    blind all fold, and the lojack is in for the second time facing 7.5 heads-up. Every step is
    read off the export rather than remembered. Whose action each one is comes from the parent
    node, which is the single most likely conversion defect and a silent one: read the actor off
    the child instead and the lojack's open becomes the hijack's, keying a spot that never happened
    while validating perfectly. Hero's own raise stays in the sequence, which is how the key says
    it is the lojack who is back in. The arrival is those six numbers multiplied together, checked
    as a product so a reviewer can follow the arithmetic. The cell is `AA`: it arrives at full
    reach - the lojack opens it every time - and four-bets to 22.5 every time.
    """
    node = by_path[TRACED_PATH]
    frequencies = step_frequencies(by_path, TRACED_PATH)

    assert node.actor_pos == "LJ"
    assert node_action_sequence(by_path, node) == TRACED_SEQUENCE
    assert [entry.position for entry in TRACED_SEQUENCE] == ["LJ", "HJ"]
    assert key_of(by_path, node) == TRACED_KEY
    assert [action.kind for action in node.actions] == ["fold", "call", "raise"]

    assert len(frequencies) == len(TRACED_PATH)
    product = 1.0
    for frequency in frequencies:
        assert 0.0 < frequency <= 1.0
        product *= frequency
    assert round(product * PARTS_PER_BILLION) == TRACED_ARRIVAL_PPB
    assert recorded_arrival[TRACED_KEY] == TRACED_ARRIVAL_PPB

    reach_index = {spot_id: dict(cells) for spot_id, cells in artifact.arriving_reach_bp}
    assert reach_index[TRACED_KEY]["AA"] == QUANTISATION_SCALE

    weights = {
        action.kind: node.weight_bp(index, "AA") for index, action in enumerate(node.actions)
    }
    row = derived.artifact_payload["action_weights"][TRACED_KEY]["AA"]
    assert row["raise"] == pytest.approx(weights["raise"] / QUANTISATION_SCALE, abs=1e-6)
    assert row.get("call", 0.0) == pytest.approx(weights["call"] / QUANTISATION_SCALE, abs=1e-6)
    assert row.get("fold", 0.0) == pytest.approx(weights["fold"] / QUANTISATION_SCALE, abs=1e-6)
    assert sum(row.values()) == pytest.approx(1.0, abs=1e-6)


# --- What the schema refuses at construction ---


FIXTURE_KEY = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "SB", ())
SECOND_FIXTURE_KEY = spot_key(
    TABLE_SIZE, STACK_DEPTH_BB, "BB", (PreflopAction("SB", "raise", 2.5),)
)


def one_spot_artifact(arrival: tuple | None, extra_spot: str | None = None) -> PreflopArtifact:
    """A hand-built artifact, legitimate in every respect except what the caller passes in.

    Modelled on `rfi_artifact` in `tests/test_derived_chart.py`, the shape this repo already uses to
    prove a schema rule rejects something: a rejection can then only be about the field under test.
    Built through `PreflopArtifact` rather than a payload reader, because validating on
    construction is what the criterion asks for.
    """
    ordered = tuple(sorted(HAND_CLASSES, key=hand_class_grid_index))
    cells = tuple((name, (("raise", 1.0),)) for name in ordered)
    spots = (SpotDefinition(spot_id=FIXTURE_KEY, hero_position="SB", action_sequence=()),)
    action_weights = ((FIXTURE_KEY, cells),)
    reach = ((FIXTURE_KEY, tuple((name, QUANTISATION_SCALE) for name in ordered)),)
    if extra_spot is not None:
        # A second, entirely legitimate spot, so that an ordering case has something to be out of
        # order with. The big blind facing a small-blind open, which the chart really does hold.
        second = SpotDefinition(
            spot_id=extra_spot,
            hero_position="BB",
            action_sequence=(PreflopAction("SB", "raise", 2.5),),
        )
        spots = (*spots, second)
        action_weights = (*action_weights, (extra_spot, cells))
        reach = (*reach, (extra_spot, tuple((name, QUANTISATION_SCALE) for name in ordered)))
    return PreflopArtifact(
        artifact_schema_version=ARTIFACT_SCHEMA_VERSION,
        source=ArtifactSource("stage four fixture", "hand-authored", "tests/chart-arrival"),
        generated_at="2026-09-02T00:00:00Z",
        table_size=TABLE_SIZE,
        stack_depth_bb=STACK_DEPTH_BB,
        positions=table_positions(TABLE_SIZE),
        spots=spots,
        action_weights=action_weights,
        audit_fields=ArtifactAuditFields(
            weights_sha256=weights_checksum(action_weights),
            spot_count=len(spots),
            hand_class_count=len(ordered),
            notes="a fixture, not a chart",
        ),
        blind_structure=schema.BlindStructure(0.5, 1.0, 0.0),
        arriving_reach_bp=reach,
        arrival_ppb=arrival,
    )


IMPOSSIBLE_ARRIVALS = [
    ("negative", ((FIXTURE_KEY, -1),)),
    ("above one", ((FIXTURE_KEY, PARTS_PER_BILLION + 1),)),
    ("a spot the chart does not declare", ((FIXTURE_KEY, 1), ("t6/d100/BTN/rfi", 1))),
    ("no arrival recorded at all", ()),
    # Integrality, because the whole argument for parts per billion is that the value is a whole
    # number; a float would checksum differently on two machines that formatted it differently.
    ("a fraction", ((FIXTURE_KEY, 0.5),)),
    ("a boolean, which Python counts as an int", ((FIXTURE_KEY, True),)),
]


@pytest.mark.parametrize(("label", "arrival"), IMPOSSIBLE_ARRIVALS)
def test_an_arrival_probability_that_is_not_one_is_refused_at_construction(
    label: str, arrival: tuple
) -> None:
    """Validated when the artifact is built, not merely stored and hoped about.

    The contract names two of these six explicitly - above one, and claimed for a spot the chart
    does not declare - and both are refusals rather than silent clamps, because a clamp writes a
    number that describes no solve and nothing downstream can tell it from one that does. The
    absent case is on the list because absent is not zero: a spot missing from the map is a
    converter that did not compute the field, and reading that as "never reached" would hand a
    later heuristic layer every spot the converter failed on. Zero is deliberately not on the list
    - it is the case the field exists to carry, and 44 committed spots are at it.
    """
    with pytest.raises(ValueError, match="(?i)arrival"):
        one_spot_artifact(arrival)


def test_a_spot_the_solve_never_reaches_is_accepted_at_zero() -> None:
    """The other side of the refusal list.

    A validator tightened to "a real probability is positive" would look like a fix and would
    delete exactly the distinction the field was ruled in to carry, at the 44 committed spots that
    round to zero and the 2 that are exactly it.
    """
    built = one_spot_artifact(((FIXTURE_KEY, 0),))

    assert dict(built.arrival_ppb) == {FIXTURE_KEY: 0}


def test_an_arrival_of_exactly_one_is_accepted() -> None:
    """The boundary the lojack's first-in spot sits on. One is not above one."""
    built = one_spot_artifact(((FIXTURE_KEY, PARTS_PER_BILLION),))

    assert dict(built.arrival_ppb) == {FIXTURE_KEY: PARTS_PER_BILLION}


def test_the_arrival_map_must_be_ordered_like_the_spots_it_describes() -> None:
    """The sibling field's rule, asked of this one too.

    `_validate_action_weights` requires the per-spot weights map to be ordered like `spots`, on the
    ground that two maps over the same keys in different orders serialise differently and checksum
    differently. A second per-spot map with no such rule is the same defect waiting in a new field.
    Two spots are the smallest case that can be out of order.
    """
    with pytest.raises(ValueError, match="(?i)arrival"):
        one_spot_artifact(
            ((SECOND_FIXTURE_KEY, 1), (FIXTURE_KEY, BUSIEST_PPB)), extra_spot=SECOND_FIXTURE_KEY
        )


def test_the_same_fixture_with_a_real_arrival_is_accepted() -> None:
    """The refusals above are about the field and not about the fixture being malformed."""
    built = one_spot_artifact(((FIXTURE_KEY, TRACED_ARRIVAL_PPB),))

    assert built.audit_fields.spot_count == 1
    assert dict(built.arrival_ppb) == {FIXTURE_KEY: TRACED_ARRIVAL_PPB}
