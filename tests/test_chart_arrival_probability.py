"""Phase 14: the spot-level arrival probability, and what a committed cell is not evidence of.

Authored at stage 4 after Taylor's 2026-08-27 ruling on the untrained-cell blocker, so this
file is the specification rather than a description of what got built. It is a seventh file in
the `pytest_derived_chart` family rather than an addition to `tests/test_derived_chart.py`
because that file has 33 lines of headroom and this needs 250; two of its siblings are already
at the 700-line cap exactly, so there was nowhere in the family to put it. The cap forced the
split and the split is the honest response to it.

**The ruling was option one: commit the cells, and record where they came from.** The chart
answers every cell whose class arrives, including the ones the solve never worked out - the
alternative was blanking them, and the reason not to is that a later heuristic layer is
wanted for exactly those spots. That layer is the thing this field exists for. A refused cell
is visibly empty and a heuristic can find it; a committed cell that was never computed looks
exactly like one that was, and the reach field cannot tell them apart at any of the eight spots
the solve never visits. At four of them it points the wrong way outright - the big blind facing
a 100bb open-jam has all 169 classes at 10,000, fully arrived. At the other four it does
something worse than lying, which is looking ordinary: 86 to 95 classes arrive at a mean of
4,753 to 7,654 basis points, which is exactly the shape a well-played spot facing a four-bet
has. So without this field the cells the future heuristic is for are the ones it cannot find.

Arrival probability and arriving reach are orthogonal and the chart needs both. Reach is per
cell and says whether hero can be holding that class here. Arrival is per spot and says
whether the line is one anybody plays. A spot can have every class at full reach and never be
reached at all, which is precisely the case at `BB/BTN:raise@100`.

Stored in parts per billion as an integer, for the reason decision 8 gave for basis points: a
checksum over integers means something. Basis points would not do here, and the reason is the
one thing this field has to get right. 21 of the 86 spots sit at a nonzero arrival below one
basis point, the smallest at 2.5e-08, so in basis points they would all round to zero and
become indistinguishable from the eight the solve genuinely never reaches - which is the single
distinction the field exists to carry. In parts per billion the smallest nonzero value is 25,
so nothing that is not zero rounds to zero.

**What this file does not assert.** No threshold. Nothing here refuses a cell for arriving
rarely, because option one ruled that the chart commits them; the field is recorded so a later
phase can rule on it with the measurement in front of it. Decision 5 covers the reach field
and does not carry this one, so it owes an amendment at the next `contract-update` - until
that lands, `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-untrained-cell-refusal.md`
is where the ruling is written down.
"""

from __future__ import annotations

import pytest
from test_chart_derivation import key_of, selected, walk_state

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts import schema
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    QUANTISATION_SCALE,
    SolverExport,
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

# The eight committed spots the solve never reaches. Four are the big blind facing a 100bb
# open-jam, which nobody does: the jam carries zero weight on all 169 classes at every one of
# the four opening nodes, measured, so the frequency is not small but exactly zero. The other
# four are a 100bb jam over an open. They hold 1,031 committed cells between them, every one of
# which is the solver's placeholder rather than its answer. Not 1,352 - only the four big-blind
# spots carry all 169 classes, and the other four carry 87, 87, 86 and 95, of which 15, 15, 10
# and 10 are at full reach. This is the list a heuristic layer starts from.
NEVER_REACHED_SPOTS = (
    "t6/d100/BB/BTN:raise@100",
    "t6/d100/BB/CO:raise@100",
    "t6/d100/BB/HJ:raise@100",
    "t6/d100/BB/LJ:raise@100",
    "t6/d100/CO/CO:raise@2.5,BTN:raise@100",
    "t6/d100/CO/CO:raise@2.5,SB:raise@100",
    "t6/d100/HJ/HJ:raise@2.5,CO:raise@100",
    "t6/d100/LJ/LJ:raise@2.5,HJ:raise@100",
)
NEVER_REACHED_CELLS = 1_031

# The small blind open-folded to, which is the most-played spot in the chart and the one
# opening range the cutover commits. Solve output rather than tree shape, so decision 2's
# permitted re-solve would move it; the phase runs none.
BUSIEST_SPOT = "t6/d100/SB/rfi"
BUSIEST_PPB = 275_247_995


@pytest.fixture(scope="module")
def export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def artifact() -> PreflopArtifact:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR)).artifacts[0]


def measured_ppb(export: SolverExport, path: tuple[int, ...]) -> int:
    """The chance the line is played at all, recomputed here rather than imported.

    The product of the parent's own frequency for the action taken, down the path from the
    root. `SolverNode.action_frequency` is the solver's own combo-weighted, reach-weighted
    figure, so this multiplies the numbers GTOpen publishes rather than deriving a second
    definition of them - and a test that imports the rule it is checking is one copy of a rule
    agreeing with another.

    **How it accumulates is part of the specification, not an implementation detail.** Float
    multiplication left to right from the root, rounded once at the end. Three of the 86 land
    within a thousandth of a rounding boundary - 1034.5125, 576.5163 and 153589.4885 parts per
    billion exactly - so a stage 6 that accumulated in `Decimal`, or in basis points per node,
    could differ by one and turn this test red for something that is not a defect.
    """
    by_path = export.by_path()
    probability = 1.0
    walked: tuple[int, ...] = ()
    for index in path:
        probability *= by_path[walked].action_frequency(index)
        walked = (*walked, index)
    return round(probability * PARTS_PER_BILLION)


def test_every_committed_spot_records_how_often_its_line_is_played(
    artifact: PreflopArtifact, export: SolverExport
) -> None:
    """The field, checked against the export at every spot rather than at a sample.

    A spot-level number is the right grain here where a cell-level one was right for reach:
    whether a line is played is a property of the line, and the 169 classes at a node all
    share it. Recomputed from the export by this file's own walk, so the chart is compared
    against the solve rather than against itself.
    """
    walked = walk_state(export.by_path())
    recorded = dict(artifact.arrival_ppb)

    assert set(recorded) == {spot.spot_id for spot in artifact.spots}
    graded = 0
    for node in export.nodes:
        if not selected(node, walked):
            continue
        key = key_of(node, walked)
        value = recorded[key]

        assert isinstance(value, int) and not isinstance(value, bool), key
        assert 0 <= value <= PARTS_PER_BILLION, (key, value)
        assert value == measured_ppb(export, node.path), key
        graded += value > 0

    assert graded == len(recorded) - len(NEVER_REACHED_SPOTS)
    assert recorded[BUSIEST_SPOT] == BUSIEST_PPB
    assert recorded[BUSIEST_SPOT] == max(recorded.values())


def test_the_spots_the_solve_never_reaches_are_recorded_as_zero_and_still_answer(
    artifact: PreflopArtifact,
) -> None:
    """Option one, asserted as behaviour: the cells are committed AND they are findable.

    Zero is the value that matters, because it is the only one that says the solve never
    worked the line out at all rather than working it out rarely. These eight spots still
    answer - that is what was ruled - so the assertion is that both halves hold at once: the
    chart has not quietly blanked them, and a later reader can tell them apart from the rest
    without re-walking the export.

    The cell total is asserted because it is what shows arriving reach cannot substitute for this
    field: 1,031 rather than eight times 169, because only the four big-blind spots carry every
    class. At the other four, reach reads like an ordinary range facing a four-bet and a reader
    going by reach alone would see nothing wrong at all.
    """
    recorded = dict(artifact.arrival_ppb)
    weights = dict(artifact.action_weights)
    committed = 0

    for key in NEVER_REACHED_SPOTS:
        assert recorded[key] == 0, key
        cells = dict(weights[key])
        assert cells, f"{key} was ruled committed and holds no cells"
        committed += len(cells)

    assert committed == NEVER_REACHED_CELLS
    assert committed < len(NEVER_REACHED_SPOTS) * len(HAND_CLASSES)
    assert all(value > 0 for key, value in recorded.items() if key not in NEVER_REACHED_SPOTS)


def one_spot_artifact(arrival: tuple | None, extra_spot: str | None = None) -> PreflopArtifact:
    """A hand-built one-spot artifact, legitimate except for what the caller passes in.

    Modelled on `rfi_artifact` in `tests/test_derived_chart.py`, which is the shape this repo
    already uses to prove a schema rule rejects something: build an artifact that is right in
    every other respect, so a rejection can only be about the field under test. Constructed
    through `PreflopArtifact` rather than through a payload reader, because validation on
    construction is what the blind structure's rule does and there is no payload constructor.
    """
    key = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "SB", ())
    ordered = tuple(sorted(HAND_CLASSES, key=hand_class_grid_index))
    cells = tuple((name, (("raise", 1.0),)) for name in ordered)
    spots = (SpotDefinition(spot_id=key, hero_position="SB", action_sequence=()),)
    action_weights = ((key, cells),)
    reach = ((key, tuple((name, QUANTISATION_SCALE) for name in ordered)),)
    if extra_spot is not None:
        # A second, entirely legitimate spot, so an ordering case has something to be out of
        # order with. The big blind facing a small-blind open, which the chart really does hold.
        sequence = (PreflopAction("SB", "raise", 2.5),)
        second = SpotDefinition(
            spot_id=extra_spot, hero_position="BB", action_sequence=sequence
        )
        spots = (*spots, second)
        action_weights = (*action_weights, (extra_spot, cells))
        reach = (*reach, (extra_spot, tuple((name, QUANTISATION_SCALE) for name in ordered)))
    return PreflopArtifact(
        artifact_schema_version=ARTIFACT_SCHEMA_VERSION,
        source=ArtifactSource("stage four fixture", "hand-authored", "tests/chart-arrival"),
        generated_at="2026-08-27T00:00:00Z",
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


# A negative chance, a chance above certainty, a spot the artifact does not declare, and the
# field absent altogether. Zero is deliberately not on the list: it is the whole point of the
# field, and a schema that rejected it would delete the eight spots the ruling exists to mark.
IMPOSSIBLE_ARRIVALS = [
    ("negative", ((BUSIEST_SPOT, -1),)),
    ("above certainty", ((BUSIEST_SPOT, PARTS_PER_BILLION + 1),)),
    ("a spot the chart does not declare", ((BUSIEST_SPOT, 1), ("t6/d100/BTN/rfi", 1))),
    ("no arrival recorded at all", ()),
    # Integrality, because the docstring's whole argument for ppb is that the value is an
    # integer, and `_validate_weights` already rejects both of these for the sibling field. A
    # float here would checksum differently on two machines that formatted it differently.
    ("a fraction", ((BUSIEST_SPOT, 0.5),)),
    ("a boolean, which Python counts as an int", ((BUSIEST_SPOT, True),)),
]


@pytest.mark.parametrize(("label", "arrival"), IMPOSSIBLE_ARRIVALS)
def test_an_arrival_probability_that_is_not_one_is_rejected(label: str, arrival: tuple) -> None:
    """Validated on construction rather than merely stored.

    The blind structure's lesson, in the same phase and the same schema: a field nothing
    validates is one a later artifact can fill with anything, and a heuristic layer keying on
    this field would then read a number that never described a solve. The absent case is on the
    list because absent is not zero - a spot missing from the map is a converter that did not
    compute the field, and reading that as "never reached" would hand the heuristic layer every
    spot the converter failed on.
    """
    with pytest.raises(ValueError, match="(?i)arrival"):
        one_spot_artifact(arrival)


def test_the_arrival_map_must_be_ordered_like_the_spots_it_describes() -> None:
    """The sibling rule, asked of this field too.

    `_validate_action_weights` requires the per-spot weights map to be ordered like `spots`, on
    the ground that two maps over the same keys in different orders serialise differently and
    checksum differently. A second per-spot map with no such rule is the same defect waiting in
    a new field. Two spots are the smallest case that can be out of order.
    """
    key = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "SB", ())
    other = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "BB", (PreflopAction("SB", "raise", 2.5),))

    with pytest.raises(ValueError, match="(?i)arrival"):
        one_spot_artifact(((other, 1), (key, 275_247_995)), extra_spot=other)


def test_the_same_artifact_with_a_real_arrival_is_accepted() -> None:
    """The rejections above are about the field and not about the fixture being malformed."""
    built = one_spot_artifact(((BUSIEST_SPOT, 275_247_995),))

    assert built.audit_fields.spot_count == 1
    assert dict(built.arrival_ppb) == {BUSIEST_SPOT: 275_247_995}
