"""Phase 14: the spot-level arrival probability, and what a committed cell is not evidence of.

Authored at stage 4 after Taylor's 2026-08-27 ruling on the untrained-cell blocker, and re-cut
at stage 4 again on 2026-09-01 after decision 14 re-sourced the solve at `add_allin: false` and
decision 20 cut the committed set from 51 spots to 36. So this file is the specification rather
than a description of what got built. It is a separate file in the `pytest_derived_chart` family
because two of its siblings sit at the 700-line cap exactly and there was nowhere in the family
to put it.

**The ruling was option one: commit the cells, and record where they came from.** The chart
answers every cell whose class arrives, including the ones the solve never worked out - the
alternative was blanking them, and the reason not to is that a later heuristic layer is wanted
for exactly those spots. That layer is the thing this field exists for. A refused cell is
visibly empty and a heuristic can find it; a committed cell that was never computed looks
exactly like one that was, and the reach field cannot tell them apart. On the 86-spot build the
ruling was taken against, reach pointed the wrong way outright at four of the eight spots the
solve never visited: the big blind facing a 100bb open-jam carried all 169 classes at 10,000
basis points, fully arrived and never played.

Arrival probability and arriving reach are orthogonal and the chart needs both. Reach is per
cell and says whether hero can be holding that class here. Arrival is per spot and says whether
the line is one anybody plays. A spot can have every class at full reach and never be reached
at all.

**Two things this field was ruled for are unexercised over the committed 36, and this file says
so rather than counting them as checks that passed.** The re-source removed the open-jam
branches, so no committed spot is one the solve never reaches - the zero case is measured empty
and only a hand-built fixture exercises it. And the smallest committed arrival is 1.03 basis
points, so nothing here would have rounded to zero in basis points either; the parts-per-billion
grain decision 5 ruled buys nothing on this set. Both are kept for the reason decision 5 gives,
which is prospective: the multiway family that returns once GTOpen can price it is deep and
rare, adding the field later is a second `ARTIFACT_SCHEMA_VERSION` bump, and a check that cannot
fail today must not be recorded as one that did.

**What this file does not assert.** No threshold. Nothing here refuses a cell for arriving
rarely, because option one ruled that the chart commits them; the field is recorded so a later
phase can rule on it with the measurement in front of it.
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

ONE_BASIS_POINT_IN_PPB = 100_000


COMMITTED_SPOTS = 36
"""Decision 1's predicate keeps 51 of the re-sourced tree's nodes and decision 20 withholds
the fifteen where hero faces a four-bet, so 36 are committed. `selected` in
`tests/test_chart_derivation.py` is both rulings together, which is what "a spot the chart
holds" means; that file owns the split and this one only counts what came out of it."""


# The most-played committed line: the small blind opened to, everybody folded. Solve output
# rather than tree shape, so decision 14's re-source moved it - the 275,247,995 this file
# carried was measured on the superseded `add_allin: true` build.
BUSIEST_SPOT = "t6/d100/SB/rfi"
BUSIEST_PPB = 281_908_314


def vacuous(what: str) -> None:
    """Stop the test and record it as skipped rather than passed.

    R2's convention from `tests/test_chart_conversion.py`, restated here rather than imported
    so two files that share nothing else do not become coupled by a three-line helper. The rule
    it carries is decision 6's and it applies to any check the committed data cannot exercise:
    "a check that cannot fail must not be counted as one that passed". A skip is the one outcome
    that is neither a green nor a permanent red against a chart the contract describes
    correctly, and every use sits *after* an assertion that the premise still holds.
    """
    pytest.skip(f"VACUOUS over the committed {COMMITTED_SPOTS}: {what}")


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
    multiplication left to right from the root, rounded once at the end. A stage 6 that
    accumulated in `Decimal`, or in basis points per node, could differ by one on a spot that
    lands near a rounding boundary and turn this test red for something that is not a defect.
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

    Every committed line is covered rather than a sample of them, and the map may hold nothing
    else: a spot the chart declares with no arrival recorded is a converter that did not compute
    the field, and one recorded for a spot the chart does not declare is a figure about a line
    the bot never asks about.
    """
    walked = walk_state(export.by_path())
    measured = {
        key_of(node, walked): measured_ppb(export, node.path)
        for node in export.nodes
        if selected(node, walked)
    }
    recorded = dict(artifact.arrival_ppb)

    assert len(measured) == COMMITTED_SPOTS
    assert set(recorded) == {spot.spot_id for spot in artifact.spots}
    assert set(recorded) == set(measured)

    for key, value in recorded.items():
        assert isinstance(value, int) and not isinstance(value, bool), key
        assert 0 <= value <= PARTS_PER_BILLION, (key, value)
        assert value == measured[key], key

    assert recorded[BUSIEST_SPOT] == BUSIEST_PPB
    assert recorded[BUSIEST_SPOT] == max(recorded.values())


def test_the_spots_the_solve_never_reaches_are_recorded_as_zero_and_still_answer(
    artifact: PreflopArtifact,
) -> None:
    """The zero case, measured empty over the committed 36 and labelled as unexercised.

    On the build this ruling was taken against, eight committed spots were lines nobody plays:
    four were the big blind facing a 100bb open-jam and four were a 100bb jam over an open.
    `add_allin: false` removed both families from the tree, so every one of the 36 spots the
    chart now commits is a line the solve reaches. **That makes the distinguishing job this
    field was ruled for unexercised here**, and it is recorded as a measurement rather than
    quietly dropped: a later solve that puts an unplayed line back must record it as zero and
    must still answer there.

    The half that is real on this build is asserted first: every committed spot holds cells at
    all, blanking an untrained cell being what option one refused. Then the premise is asserted
    and the test skips itself as vacuous, which is R2's convention for a check the committed
    data cannot exercise - a green here would say the zero case was tested when nothing was.
    """
    recorded = dict(artifact.arrival_ppb)
    weights = dict(artifact.action_weights)
    never_reached = sorted(key for key, value in recorded.items() if value == 0)

    assert all(weights[key] for key in recorded), "a committed spot with no cells is not committed"
    assert never_reached == [], never_reached
    vacuous("no committed spot is a line the solve never reaches, so zero is never recorded")


def test_the_parts_per_billion_grain_is_unexercised_over_the_committed_set(
    artifact: PreflopArtifact,
) -> None:
    """Decision 5's reason for parts per billion, measured on the set that shipped.

    The grain was ruled because 21 of the 86 spots then committed sat at a nonzero arrival
    below one basis point, the smallest at 2.5e-08, so in basis points all 21 would have
    rounded to zero and become indistinguishable from the spots the solve genuinely never
    reaches. Over the committed 36 the rarest line is played about one time in ten thousand,
    which is 1.03 basis points, so **basis points would have lost nothing here**. The field
    keeps the finer grain for the prospective reason decision 5 gives, and this test records
    that the reason is prospective rather than present, because a check that cannot fail must
    not be counted as one that passed.
    """
    values = [value for _, value in artifact.arrival_ppb]

    assert values
    assert min(values) >= ONE_BASIS_POINT_IN_PPB, (
        "a committed spot now arrives below one basis point, so the parts-per-billion grain"
        " has started doing the job decision 5 ruled it in for and this label is out of date"
    )
    vacuous("the rarest committed line is 1.03 basis points, so basis points would have done")


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
# field, and a schema that rejected it would delete the spots the ruling exists to mark.
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


def test_a_spot_the_solve_never_reaches_is_accepted_at_zero() -> None:
    """The other side of the rejection list, and the only place the zero case is exercised.

    No committed spot arrives at zero after the re-source, so this fixture is the whole of what
    stands between the schema and a later artifact that cannot express an unplayed line at all.
    A validator tightened to "a real probability is positive" would look like a fix and would
    delete exactly the distinction Taylor ruled the field in to carry.
    """
    built = one_spot_artifact(((BUSIEST_SPOT, 0),))

    assert dict(built.arrival_ppb) == {BUSIEST_SPOT: 0}


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
        one_spot_artifact(((other, 1), (key, BUSIEST_PPB)), extra_spot=other)


def test_the_same_artifact_with_a_real_arrival_is_accepted() -> None:
    """The rejections above are about the field and not about the fixture being malformed."""
    built = one_spot_artifact(((BUSIEST_SPOT, BUSIEST_PPB),))

    assert built.audit_fields.spot_count == 1
    assert dict(built.arrival_ppb) == {BUSIEST_SPOT: BUSIEST_PPB}
