"""Phase 14: the committed derived chart itself, and what its cells must not have become.

Authored before the converter, the artifact and the report exist, and frozen before any of
them does, so this file is the specification rather than a description of what got built. It
owns the committed data as a thing in its own right: that the library holds one chart at the
new schema version, that it names the export it came from, that the ruled selection rule can
be re-derived from the artifact's own keys, that it holds one opening range and it is the
small blind's, that it declares the blind structure the solve posted, that every cell carries
the arriving reach decision 5 ruled in, that no cell limps, and that its audit notes confess
the two defects the ranges carry.

`tests/test_chart_cutover_evidence.py` is the other half, split from this one when the pair
went past the 700-line cap. It owns the evidence *about* the cutover rather than the artifact:
the retired chart's overlap with what replaces it, the source card and the solve behind it,
the two orderings the export was gated on, and the dominance measurements. It imports this
file's table constants, its predicate walk and its two cell readers rather than copying them,
so the two halves cannot drift apart. Both files run under `pytest_derived_chart`.

Two habits run through both. Nothing is checked against a number this repo remembered: the
reach and the blind structure are recomputed from the committed export or read off the
committed source card, because a chart checked against a constant somebody typed beside it is
one number agreeing with itself. And the walk that locates an export node is written here
rather than imported from the conversion module, for the same reason - it is the conversion
that is on trial.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter

import pytest
from test_chart_derivation import key_of, selected, walk_state

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts import schema
from poker_training_bot.solver_artifacts.gtopen_expectations import aggregate_frequencies
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    gtopen_class_index,
    load_solver_export,
    load_source_card,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, hand_class_grid_index
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import (
    MISS_HAND_CLASS_NOT_COVERED,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
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

ARTIFACTS = REPO_ROOT / "data" / "artifacts"
ARTIFACT_DIR = ARTIFACTS / "preflop"
CONVERTER = REPO_ROOT / "scripts" / "convert_preflop_export.py"

TABLE_SIZE = 6
STACK_DEPTH_BB = 100
SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")
OPENING_ORDER = ("LJ", "HJ", "CO", "BTN")


COMMITTED_SPOTS = 86
"""The ruled predicate's count over the committed export: at most one opponent voluntarily
invested and at most two players still live. A tree fact, so the re-solve decision 2 permits
and this phase does not run could not move it."""


# The one opening range the cutover commits. The fourteen it gives up are named in
# `tests/test_chart_cutover_evidence.py`, which owns the comparison against the retired
# chart; both halves are the ruled cost rather than an accident.
SB_OPEN_KEY = "t6/d100/SB/rfi"


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR))


@pytest.fixture(scope="module")
def artifact(library: PreflopChartLibrary) -> PreflopArtifact:
    return library.artifacts[0]


@pytest.fixture(scope="module")
def committed_export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def card() -> dict:
    return load_source_card(COMMITTED_SOURCE_CARD_PATH)


FOLD = ("fold", None)


OPEN = ("raise", 2.5)


THREE_BET = ("raise", 7.5)


FOUR_BET = ("raise", 22.5)


# Where these tests look the export up: each plan is the actions taken from the root, and the
# node it lands on is the one whose reach the artifact claims to carry. **Every plan lands on
# a committed spot**, which is what the predicate changed about this list: a plan ending where
# three players are still live is a spot the chart refuses, so probing it would compare the
# artifact against a cell it deliberately does not hold. The last two plans carry the weight,
# because hero has acted there and the arriving range is a real one rather than all 169
# classes at full weight.
PROBE_PLANS: dict[str, tuple[tuple[str, float | None], ...]] = {
    "SB open-folded to": (FOLD, FOLD, FOLD, FOLD),
    "BB facing a button open": (FOLD, FOLD, FOLD, OPEN, FOLD),
    "BB facing a small-blind open": (FOLD, FOLD, FOLD, FOLD, OPEN),
    "BB facing a lojack open": (OPEN, FOLD, FOLD, FOLD, FOLD),
    "SB facing a big-blind three-bet": (FOLD, FOLD, FOLD, FOLD, OPEN, THREE_BET),
    "BB facing a button four-bet": (FOLD, FOLD, FOLD, OPEN, FOLD, THREE_BET, FOUR_BET),
}


def follow(by_path: dict, plan: tuple[tuple[str, float | None], ...]):
    """Walk the export by naming actions, and derive the spot key of where it lands. A recorded
    action's actor is the *parent's* actor, not the node's, and getting that backwards mislabels
    every entry in the key silently, which is why the walk is repeated here."""
    path: tuple[int, ...] = ()
    entries: list[PreflopAction] = []
    for kind, to in plan:
        node = by_path[path]
        chosen = [index for index, act in enumerate(node.actions)
                  if act.kind == kind and (to is None or abs(act.to - to) < 1e-9)]
        assert chosen, f"the export offers no {kind} to {to} at path {path}"
        if kind != "fold":
            entries.append(PreflopAction(node.actor_pos, "raise", node.actions[chosen[0]].to))
        path = (*path, chosen[0])
    landed = by_path[path]
    return landed, spot_key(TABLE_SIZE, STACK_DEPTH_BB, landed.actor_pos, tuple(entries))


def live_and_invested(hero_position: str, entries) -> tuple[int, int]:
    """The ruled predicate's two counts, re-derived from a spot key's own contents.

    This is what makes the selection rule checkable from the artifact rather than only from
    the converter that applied it. The ring walk is the one `spot_key` itself describes: a
    cursor starts at the first seat to act and moves forward, and every seat it passes without
    a recorded action has folded there. Seats the cursor has not reached yet are still live,
    which is the distinction that is easy to get backwards - and getting it backwards is
    exactly the error that made a history predicate look like a subtree one.
    """
    folded: set[str] = set()
    cursor = 0

    def advance_to(target: str) -> None:
        nonlocal cursor
        for _ in range(len(SEATS) + 1):
            standing = SEATS[cursor % len(SEATS)]
            cursor += 1
            if standing == target:
                return
            folded.add(standing)
        raise AssertionError(f"the preflop order never reaches {target}")

    for entry in entries:
        advance_to(entry.position)
    advance_to(hero_position)
    invested = {entry.position for entry in entries} - {hero_position}
    return len(SEATS) - len(folded), len(invested)


def weights_by_class(artifact: PreflopArtifact, spot_id: str) -> dict:
    for keyed, classes in artifact.action_weights:
        if keyed == spot_id:
            return dict(classes)
    raise AssertionError(f"the committed artifact declares no spot {spot_id!r}")


def reach_by_class(artifact: PreflopArtifact, spot_id: str) -> dict:
    for keyed, classes in artifact.arriving_reach_bp:
        if keyed == spot_id:
            return dict(classes)
    raise AssertionError(f"the committed artifact carries no arriving reach for {spot_id!r}")


def rfi_artifact(limping_class: str | None = None) -> PreflopArtifact:
    """A hand-built one-spot artifact: the small blind open-folded to, all 169 classes covered.

    The small blind because that is the one opening range the cutover commits, and because in
    the export it is the single spot offering hero a raise and no call at all. Legitimate in
    every other respect, so a rejection can only be about the limp.
    """
    key = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "SB", ())
    ordered = tuple(sorted(HAND_CLASSES, key=hand_class_grid_index))
    cells = tuple(
        (name, (("call", 1.0),) if name == limping_class else (("raise", 1.0),))
        for name in ordered
    )
    action_weights = ((key, cells),)
    reach = ((key, tuple((name, QUANTISATION_SCALE) for name in ordered)),)
    return PreflopArtifact(
        artifact_schema_version=ARTIFACT_SCHEMA_VERSION,
        source=ArtifactSource("stage four fixture", "hand-authored", "tests/derived-chart"),
        generated_at="2026-08-26T00:00:00Z",
        table_size=TABLE_SIZE,
        stack_depth_bb=STACK_DEPTH_BB,
        positions=table_positions(TABLE_SIZE),
        spots=(SpotDefinition(spot_id=key, hero_position="SB", action_sequence=()),),
        action_weights=action_weights,
        audit_fields=ArtifactAuditFields(
            weights_sha256=weights_checksum(action_weights),
            spot_count=1,
            hand_class_count=len(ordered),
            notes="a fixture, not a chart",
        ),
        blind_structure=schema.BlindStructure(0.5, 1.0, 0.0),
        arriving_reach_bp=reach,
    )


def test_the_library_holds_exactly_one_chart_at_the_new_schema_version(
    library: PreflopChartLibrary,
) -> None:
    """One chart, six-handed, 100bb, at the version decisions 4 and 5 share. The count is the
    point rather than the name: two artifacts is the state where a reader cannot say which
    ranges the bot plays."""
    assert len(library.artifacts) == 1
    artifact = library.artifacts[0]

    assert artifact.artifact_schema_version == ARTIFACT_SCHEMA_VERSION == 2
    assert artifact.table_size == TABLE_SIZE
    assert artifact.stack_depth_bb == STACK_DEPTH_BB
    assert artifact.source.kind == "solver-export"
    assert len(artifact.spots) == len(library.spot_keys()) == COMMITTED_SPOTS


def test_the_chart_names_the_committed_export_it_was_derived_from(
    artifact: PreflopArtifact,
) -> None:
    """Provenance that resolves to the GTOpen export, not to the GTO Wizard source. Both files
    exist in this tree and both are plausible strings, so a reference that merely points at
    something readable proves nothing about which solve produced the ranges."""
    referenced = (REPO_ROOT / artifact.source.reference).resolve()

    assert referenced == COMMITTED_EXPORT_PATH.resolve()
    assert referenced.parent.name == "exports"


def test_every_committed_spot_satisfies_the_ruled_predicate(artifact: PreflopArtifact) -> None:
    """The selection rule, re-derived from the artifact's own keys rather than trusted.

    Both clauses, because either alone is a different chart: the history clause alone selects
    110 nodes of the export and admits 24 whose terminals can still go multiway, and the
    subtree clause alone selects 5,472 and admits 5,386 reached through a cold call. A spot
    with three players still live is the error the 2026-08-25 supersession corrected, and it
    is invisible to every other check here - the cell converts cleanly, imports cleanly and
    is priced by a model that cannot see three-way equity.
    """
    live_counts = Counter()
    for spot in artifact.spots:
        live, invested = live_and_invested(spot.hero_position, spot.action_sequence)
        assert invested <= 1, (spot.spot_id, invested)
        assert live <= 2, (spot.spot_id, live)
        live_counts[live] += 1

    assert len(artifact.spots) == COMMITTED_SPOTS
    assert live_counts == {2: COMMITTED_SPOTS}


def test_the_chart_holds_one_opening_range_and_it_is_the_small_blinds(
    artifact: PreflopArtifact, library: PreflopChartLibrary
) -> None:
    """The ruled cost, stated as what the bot can and cannot do.

    Four of the five opens are among the 24 the predicate drops, so the bot cannot open a pot
    from the lojack, hijack, cutoff or button and refuses those decisions with a code. Taylor
    confirmed that on 2026-08-25 knowing it is a regression against the chart being retired
    rather than only against the 110. A chart carrying a second opening range is a chart built
    on the superseded predicate, which is why the absences are asserted and not just the one
    presence.
    """
    folded_to_hero = {spot.spot_id for spot in artifact.spots if not spot.action_sequence}

    assert folded_to_hero == {SB_OPEN_KEY}
    assert SB_OPEN_KEY in library.spot_keys()
    for position in OPENING_ORDER:
        assert f"t{TABLE_SIZE}/d{STACK_DEPTH_BB}/{position}/rfi" not in library.spot_keys()


def test_the_chart_declares_the_blind_structure_the_solve_posted(
    artifact: PreflopArtifact, card: dict
) -> None:
    """Decision 4, with the blinds read off the posted config rather than spelled here.

    `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` was phase 13's largest finding:
    the chart was solved at 0.5/1 and nothing stopped it being asked about a 1/3 game, where
    the same hand at the same depth is a different decision."""
    posted = card["config_posted"]
    positions, posts = list(posted["positions"]), list(posted["posts"])
    declared = artifact.blind_structure

    assert declared.small_blind_bb == posts[positions.index("SB")]
    assert declared.big_blind_bb == posts[positions.index("BB")]
    assert declared.ante_bb == posted["ante"]
    assert sum(posts) == declared.small_blind_bb + declared.big_blind_bb


# No small blind, a negative one, no big blind, inverted blinds, a negative ante. A zero ante
# is a real table and is deliberately not on the list.
IMPOSSIBLE_BLINDS = [(0.0, 1.0, 0.0), (-0.5, 1.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.5, 0.0),
                     (0.5, 1.0, -0.1)]


@pytest.mark.parametrize(("small", "big", "ante"), IMPOSSIBLE_BLINDS)
def test_a_blind_structure_that_is_not_one_is_rejected(
    small: float, big: float, ante: float
) -> None:
    """Validated on construction rather than merely stored. A field nothing validates is one a
    later artifact can fill with anything, and the lookup refusing a mismatched table would
    then compare against a number that never described a game."""
    with pytest.raises(ValueError):
        schema.BlindStructure(small_blind_bb=small, big_blind_bb=big, ante_bb=ante)


def test_every_committed_cell_carries_an_arriving_reach(artifact: PreflopArtifact) -> None:
    """Decision 5: one reach value per cell, covering exactly the cells the chart answers.

    A per-spot summary is explicitly not on the menu, because a spot-level number cannot tell
    one cell from another. A reach of zero is not committed either: a cell hero cannot arrive
    at is a cell the solver never trained."""
    reach = dict(artifact.arriving_reach_bp)

    assert set(reach) == {spot.spot_id for spot in artifact.spots}
    for spot_id, classes in artifact.action_weights:
        cells = dict(reach[spot_id])
        assert set(cells) == {name for name, _ in classes}, spot_id
        for name, value in cells.items():
            assert isinstance(value, int) and not isinstance(value, bool), (spot_id, name)
            assert 0 < value <= QUANTISATION_SCALE, (spot_id, name, value)


def test_reach_answers_for_a_covered_cell_and_refuses_an_uncovered_one(
    artifact: PreflopArtifact,
) -> None:
    """`reach_bp_for` is the reader's way in, and it fails closed like every other lookup."""
    covered = artifact.reach_bp_for(SB_OPEN_KEY, "AA")

    assert covered == reach_by_class(artifact, SB_OPEN_KEY)["AA"]
    assert covered > 0

    deeper = f"t{TABLE_SIZE}/d500/SB/rfi"
    assert deeper not in {spot.spot_id for spot in artifact.spots}
    assert artifact.reach_bp_for(deeper, "AA") is None


def test_the_cells_at_full_reach_are_the_ones_hero_reaches_without_acting(
    artifact: PreflopArtifact,
) -> None:
    """Decision 5's field earns its place on the 86 rather than on the 110.

    11 of the 86 sit at full reach against 35 of the 110, so the field distinguishes more
    rather than less - which is what turned the amendment's prospective argument into a
    present one. The eleven are named by a rule rather than listed: hero's whole range
    arrives exactly where hero has not yet acted. Anything else is reach that was written
    instead of read.
    """
    full = set()
    unacted = set()
    for spot in artifact.spots:
        cells = reach_by_class(artifact, spot.spot_id)
        arriving = sum(cells.values()) / len(HAND_CLASSES)
        if arriving >= QUANTISATION_SCALE - 1e-9:
            full.add(spot.spot_id)
        if all(entry.position != spot.hero_position for entry in spot.action_sequence):
            unacted.add(spot.spot_id)

    assert full == unacted
    assert len(full) == 11
    assert SB_OPEN_KEY in full


def test_the_charts_reach_is_the_exports_reach_recomputed(
    artifact: PreflopArtifact, committed_export: SolverExport
) -> None:
    """The reach in the chart is the reach in the solve, class by class.

    Recomputed by walking the export directly and indexing it with GTOpen's own class
    ordering, so this is not two copies of one number agreeing with itself. It also catches the
    transposition defect: `hand_class_grid_index` and `gtopen_class_index` disagree on all but
    a handful of classes, and the wrong one swaps suited for offsuit while leaving every total
    intact. The last two plans carry the weight, since a chart writing 10,000 everywhere passes
    the ones where hero has not acted."""
    by_path = committed_export.by_path()
    graded = 0
    for label, plan in PROBE_PLANS.items():
        node, key = follow(by_path, plan)
        arriving = {name: node.reach_bp[gtopen_class_index(name)] for name in HAND_CLASSES}
        solved = {name: value for name, value in arriving.items() if value > 0}

        assert reach_by_class(artifact, key) == solved, label
        if len(set(solved.values())) > 20:
            graded += 1

    assert graded, "no probed spot had reach varying by class, so nothing was really compared"


# The grid the export offers at the committed spots, and what the chart keeps of it. A GTOpen
# payload is unconditional - a hand hero folded four streets of betting ago still carries a full
# strategy row - so every one of the 86 nodes ships all 169 classes and `reach_bp` is the only
# thing that says which of them hero can actually be holding.
GRID_CELLS = 86 * 169
COMMITTED_CELLS = 7_112

# Within one basis point of 1/n, which is the quantisation step, so this is the untouched
# initialisation exactly rather than near it. Every one of the 3,781 is refused, and that is
# checkable without ruling an epsilon: a row the solver never moved has not been rounded off
# something, it is still sitting where the solve put it before the first iteration.
EXACT_INITIALISATION_CELLS = 3_781

# The same rows at the two-point tolerance `UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`
# measured the census at, restricted to the nodes offering three or more actions. There the
# tolerance separates cleanly - all 1,516 sit at zero reach - because 1/3 and 1/4 are not
# frequencies a trained cell lands on. At a two-action node it does not separate at all, since
# 1/n is 50 percent and 50 percent is what an indifferent hand plays; the residue there is
# five cells and is the open question stage 6 needs ruled, recorded in the stage-4 notes.
UNIFORM_CELLS_ON_A_THREE_ACTION_MENU = 1_516
UNIFORM_TOLERANCE_BP = 200

# The small blind facing a hundred-blind four-bet jam, holding 72o. The class never arrives -
# nobody three-bets it - so the solver never trained the cell, and its row is the initialisation
# exactly: 5,000 and 5,000 across fold and call. That is what makes a uniform row worse than a
# gap rather than merely as bad. Committed, it does not read as missing; it reads as a
# considered coin flip, and the bot calls off a hundred blinds with 72o half the time.
UNTRAINED_SPOT = "t6/d100/SB/CO:raise@2.5,SB:raise@7.5,CO:raise@100"
UNTRAINED_SEQUENCE = (
    PreflopAction("CO", "raise", 2.5),
    PreflopAction("SB", "raise", 7.5),
    PreflopAction("CO", "raise", 100.0),
)
UNTRAINED_CLASS = "72o"


@pytest.fixture(scope="module")
def export_cells(committed_export: SolverExport) -> dict[str, SolverNode]:
    """Every committed spot key mapped to the export node it was derived from.

    The predicate walk is imported from `tests/test_chart_derivation.py`, which owns it, rather
    than from the conversion module - the conversion is what is on trial - and rather than
    copied, so the two halves of the specification cannot drift apart.
    """
    by_path = committed_export.by_path()
    walked = walk_state(by_path)
    return {key_of(node, walked): node for node in committed_export.nodes if selected(node, walked)}


def test_a_class_that_never_arrives_is_refused_rather_than_committed(
    artifact: PreflopArtifact, export_cells: dict[str, SolverNode]
) -> None:
    """`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`, asserted over the whole grid.

    `test_every_committed_cell_carries_an_arriving_reach` already requires a committed cell's
    own reach to be positive, but that is the artifact agreeing with itself: it cannot see a
    cell the converter committed while writing a reach it never read. This compares the
    committed cells against the export's own `reach_bp`, class by class, at all 86 spots, so
    the rule is checked where it is applied. 7,422 of the 14,534 never arrive and not one of
    them is an answer.

    The bound is deliberately one-sided, and the reason is a blocker rather than a shortcut.
    Committing a class that never arrives is ruled out; refusing *more* than that is the open
    question - whether an untrained-cell rule fires at a two-action node, and at what reading -
    and no lower bound survives every candidate answer. A one-percent arriving-reach cutoff, the
    form `CHART-MUST-REFUSE-AN-UNTRAINED-CELL` asks for in terms, refuses 1,801 cells that
    arrive; a uniform-row epsilon refuses five. An assertion tight enough to be a real floor
    would pick between them, which is Taylor's to do and not this file's. So what is asserted
    is the direction that is ruled, plus the ceiling: 7,112 is what refusing exactly the cells
    that never arrive commits, and nothing may commit more. The coverage direction is held by
    the tests either side of this one - the chart still has to answer the small blind's open,
    the big blind's defence and the named cell below - so an empty chart does not pass by
    default. Both totals are solve output rather than tree shape; decision 2 ships as solved.
    """
    committed = 0
    for key, node in export_cells.items():
        arriving = {name for name in HAND_CLASSES if node.reach_bp[gtopen_class_index(name)] > 0}
        cells = set(weights_by_class(artifact, key))

        assert cells <= arriving, (key, sorted(cells - arriving))
        committed += len(cells)

    assert len(export_cells) == COMMITTED_SPOTS
    assert 0 < committed <= COMMITTED_CELLS


def test_an_untrained_cell_is_refused_at_the_table_rather_than_answered(
    library: PreflopChartLibrary, export_cells: dict[str, SolverNode]
) -> None:
    """The refusal asked as a query, because absence from a payload is not yet a refusal.

    A cell missing from the weights is only a refusal if the lookup turns it into one with a
    code the caller can log, which is the same standard the excluded nodes are held to. The
    spot itself is committed and answers a hand that does arrive, so this is one cell being
    declined rather than the chart being empty - a chart holding nothing passes the refusal
    half on its own.
    """
    node = export_cells[UNTRAINED_SPOT]
    index = gtopen_class_index(UNTRAINED_CLASS)
    menu = len(node.actions)
    query = ChartQuery(TABLE_SIZE, STACK_DEPTH_BB, "SB", UNTRAINED_SEQUENCE, UNTRAINED_CLASS)

    assert node.reach_bp[index] == 0
    assert [node.strategy_bp[act][index] for act in range(menu)] == [
        QUANTISATION_SCALE // menu
    ] * menu

    refused = library.lookup(query)
    answered = library.lookup(
        ChartQuery(TABLE_SIZE, STACK_DEPTH_BB, "SB", UNTRAINED_SEQUENCE, "AA")
    )

    assert query.spot_key == UNTRAINED_SPOT
    assert isinstance(refused, ChartMiss)
    assert refused.code == MISS_HAND_CLASS_NOT_COVERED
    assert refused.spot_key == UNTRAINED_SPOT
    assert UNTRAINED_CLASS in refused.detail
    assert not isinstance(answered, ChartMiss), getattr(answered, "detail", "")
    assert answered.spot_key == UNTRAINED_SPOT


def test_no_committed_cell_sits_at_the_solvers_untouched_initialisation(
    artifact: PreflopArtifact, export_cells: dict[str, SolverNode]
) -> None:
    """The same rule read off the strategy row rather than off the reach, at no ruled epsilon.

    Reach says a cell was never visited; the row says the solver never touched it. They are
    different readings and neither implies the other - 3,502 cells at zero reach carry a
    perfectly ordinary row, and the row is what a reader of the chart would see. Asserted at
    the two tolerances that need nobody's ruling: within a basis point of 1/n, which is the
    quantisation step and cannot be anything but initialisation, and the census tolerance
    restricted to menus of three or more actions, where 1/n is not a frequency trained play
    lands on. Every cell either reading catches is refused already, which is what makes the
    rule assertable before the epsilon question is answered.
    """
    exact = 0
    on_a_wide_menu = 0
    for key, node in export_cells.items():
        committed = set(weights_by_class(artifact, key))
        menu = len(node.actions)
        share = QUANTISATION_SCALE / menu
        for name in HAND_CLASSES:
            index = gtopen_class_index(name)
            row = [node.strategy_bp[act][index] for act in range(menu)]
            deviation = max(abs(weight - share) for weight in row)
            if deviation < 1.0:
                exact += 1
                assert name not in committed, (key, name)
            if menu >= 3 and deviation < UNIFORM_TOLERANCE_BP:
                on_a_wide_menu += 1
                assert name not in committed, (key, name)

    assert exact == EXACT_INITIALISATION_CELLS
    assert on_a_wide_menu == UNIFORM_CELLS_ON_A_THREE_ACTION_MENU


def test_the_schema_rejects_an_artifact_whose_hero_limps() -> None:
    """A spot with an empty action sequence may not carry a positive call weight.

    The pot is folded to hero, so a call is a limp, and `CHART-HERO-MUST-NEVER-LIMP` asks for
    this as a rule rather than as a measurement over one file: the export enforces it by
    construction, "but that is a property of the data rather than a rule", and phase 14 owns
    the schema. The chart being retired limps 13.73 percent from the small blind,
    combo-weighted over 1,326 combos, across 103 hand classes with a nonzero call weight, so
    this is not a hypothetical shape."""
    with pytest.raises(ValueError, match="(?i)limp"):
        rfi_artifact(limping_class="A5s")


def test_the_same_artifact_without_the_limp_is_accepted() -> None:
    """The rejection above is about the limp and not about the fixture being malformed."""
    built = rfi_artifact()

    assert built.audit_fields.spot_count == 1
    assert built.weights_for(SB_OPEN_KEY, "A5s") == (("raise", 1.0),)


def test_no_committed_spot_limps(artifact: PreflopArtifact) -> None:
    """And the committed chart satisfies the rule, which the rule alone does not prove: a
    schema rule no committed file exercises is a rule nobody has run. There is exactly one
    folded-to-hero spot left to exercise it, and in the export it is not even offered a call -
    the small blind's menu there is fold, raise and jam - so the rule holds by construction
    and is asserted anyway."""
    folded_to_hero = {spot.spot_id for spot in artifact.spots if not spot.action_sequence}

    assert folded_to_hero == {SB_OPEN_KEY}
    for spot_id in folded_to_hero:
        for name, weights in weights_by_class(artifact, spot_id).items():
            called = sum(weight for action, weight in weights if action == "call")
            assert called == 0.0, (spot_id, name, called)


def test_the_committed_chart_reproduces_from_the_committed_export() -> None:
    """The export is the source of truth; the chart and its sizings are its output. A hand
    edit to a derived file is a number with no origin, and `--check` is what tells one from a
    conversion nobody re-ran."""
    result = subprocess.run(
        ["python", str(CONVERTER), "--check"], cwd=REPO_ROOT, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_the_chart_states_the_realization_bias_in_poker_terms(
    artifact: PreflopArtifact, committed_export: SolverExport
) -> None:
    """`REALIZATION-MODEL-UNDERPRICES-POSITION`, accepted and recorded rather than corrected.

    GTOpen prices postflop with a scalar realization weight rather than a solve, and the effect
    is measured: the big blind folds far more than a real postflop solve gives facing a 2.5bb
    small-blind open, closing the action in position. The closing measurement names it as a
    third explanation it cannot separate, and the big blind holds 58 of the 89 human call
    disagreements, so leaving it unnamed makes that measurement unfalsifiable. The quoted fold
    frequency is recomputed from the export rather than compared against a remembered 50.98."""
    notes = artifact.audit_fields.notes
    lowered = notes.lower()
    folds = 100.0 - aggregate_frequencies(committed_export).defence_pct["SB"]
    quoted = [float(text) for text in re.findall(r"\d+\.\d+", notes)]

    assert "realization" in lowered
    assert "position" in lowered
    assert "fold" in lowered
    assert "2.5" in notes
    assert any(abs(value - folds) <= 0.05 for value in quoted), (folds, quoted)


def test_the_chart_states_the_multiway_defect_and_the_nodes_it_excluded(
    artifact: PreflopArtifact,
) -> None:
    """The other half of the source card's confession, and the contract requires it by count.

    `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` is why the chart holds 86 spots rather than
    the tree, and the excluded node count is what tells a reader the absence is a decision
    rather than an oversight. Without it the missing four opening ranges read as a gap in the
    conversion. No packet and no card may claim the committed set is priced exactly, so the
    24 that were dropped *because* the model misprices them are named as such.
    """
    notes = artifact.audit_fields.notes
    lowered = notes.lower()

    assert "multiway" in lowered
    assert "38,742" in notes or "38742" in notes
    assert "86" in notes
    assert "24" in notes
