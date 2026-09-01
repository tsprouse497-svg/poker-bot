"""Phase 14: the committed derived chart itself, and what its cells must not have become.

Authored before the converter, the artifact and the report exist, and frozen before any of them
does, so this file is the specification rather than a description of what got built. It owns the
committed data in its own right: that the library holds one chart at the new schema version
naming the export it came from, that all three rulings can be re-derived from the artifact's own
keys, that it holds one opening range and it is the small blind's, that it declares the blind
structure the solve posted, that every cell carries the arriving reach decision 5 ruled in, that
no cell limps, and that its audit notes confess what is absent.

**The chart holds 21 spots.** Decision 1's predicate selects 51; decision 20 withholds the
fifteen where hero faces a four-bet, the `calibrated` fit having no cell for a four-bet pot; and
Taylor's ruling of 2026-09-01 withholds the fifteen where hero answers the five-bet jam that
follows, those cells being priced against a range computed at the very four-bet nodes decision
20 refuses. Together the withholdings are `raises_faced >= 3`. `selected`, imported from
`tests/test_chart_derivation.py`, means committed under all three rulings.

`tests/test_chart_cutover_evidence.py` is the other half, split off at the 700-line cap: it owns
the evidence *about* the cutover - the retired chart's overlap with what replaces it, the source
card, the two orderings, the dominance measurements - and imports this file's table constants,
predicate walk and cell readers rather than copying them.

Two habits run through both. Nothing is checked against a number this repo remembered: reach and
the blind structure are recomputed from the committed export or read off the source card. And
the walk that locates an export node is written here rather than imported from the conversion
module, for the same reason - the conversion is what is on trial.
"""

from __future__ import annotations

import re
import subprocess
import sys
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


COMMITTED_SPOTS = 21
"""What the three rulings leave: the predicate keeps 51 - at most one opponent voluntarily
invested and at most two players still live - decision 20 withholds the 15 four-bet-facing
spots, and the 2026-09-01 ruling the 15 jam-facing ones. All tree facts, so a re-solve at the
ruled config cannot move them."""

RAISES_FACED_AT_A_COMMITTED_SPOT = {0: 1, 1: 5, 2: 15}
"""No entry at 3 and none at 4: the first is decision 20, the second the 2026-09-01 ruling. Both
withheld families number 15, so a build applying one withholding and not the other lands on 36
either way and only the histogram tells them apart."""

FULL_REACH_SPOTS = 6
OPENING_SEATS = ("LJ", "HJ", "CO", "BTN", "SB")
"""The five opens the big blind answers; with the small blind's own open they are the six spots
hero reaches without having acted, which is the whole of the full-reach set."""


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


FOLD, OPEN, THREE_BET = ("fold", None), ("raise", 2.5), ("raise", 7.5)
FOUR_BET, FIVE_BET_JAM = ("raise", 22.5), ("jam", 100.0)


# Where these tests look the export up: each plan is the actions taken from the root, and the
# node it lands on is the one whose reach the artifact claims to carry. **Every plan lands on a
# committed spot.** A plan ending where three players are still live is a spot the chart
# refuses, and so now is one ending where hero faces a four-bet or answers the jam after it, so
# probing any of those would compare the artifact against a cell it deliberately does not hold.
# The last plan carries the weight, because hero has acted there and the arriving range is a
# real one rather than all 169 classes at full weight.
PROBE_PLANS: dict[str, tuple[tuple[str, float | None], ...]] = {
    "SB open-folded to": (FOLD, FOLD, FOLD, FOLD),
    "BB facing a button open": (FOLD, FOLD, FOLD, OPEN, FOLD),
    "BB facing a small-blind open": (FOLD, FOLD, FOLD, FOLD, OPEN),
    "BB facing a lojack open": (OPEN, FOLD, FOLD, FOLD, FOLD),
    "SB facing a big-blind three-bet": (FOLD, FOLD, FOLD, FOLD, OPEN, THREE_BET),
}

# The two plans that land on withheld nodes, kept so the probe set can be shown to stop where
# the rulings stop rather than merely to agree everywhere it looks.
WITHHELD_PLANS: dict[str, tuple[tuple[str, float | None], ...]] = {
    "BB facing a button four-bet": (FOLD, FOLD, FOLD, OPEN, FOLD, THREE_BET, FOUR_BET),
    "BTN facing a big-blind five-bet jam": (
        FOLD, FOLD, FOLD, OPEN, FOLD, THREE_BET, FOUR_BET, FIVE_BET_JAM,
    ),
}


def follow(by_path: dict, plan: tuple[tuple[str, float | None], ...]):
    """Walk the export by naming actions and derive the spot key of where it lands. A recorded
    action's actor is the *parent's*, and getting that backwards silently mislabels every entry
    in the key, which is why the walk is repeated here."""
    path: tuple[int, ...] = ()
    entries: list[PreflopAction] = []
    for kind, to in plan:
        node = by_path[path]
        chosen = [index for index, act in enumerate(node.actions)
                  if act.kind == kind and (to is None or abs(act.to - to) < 1e-9)]
        assert chosen, f"the export offers no {kind} to {to} at path {path}"
        if kind == "call":
            entries.append(PreflopAction(node.actor_pos, "call"))
        elif kind != "fold":
            entries.append(PreflopAction(node.actor_pos, "raise", node.actions[chosen[0]].to))
        path = (*path, chosen[0])
    landed = by_path[path]
    return landed, spot_key(TABLE_SIZE, STACK_DEPTH_BB, landed.actor_pos, tuple(entries))


def live_and_invested(hero_position: str, entries) -> tuple[int, int]:
    """The ruled predicate's two counts, re-derived from a spot key's own contents.

    This is what makes the selection rule checkable from the artifact rather than only from the
    converter that applied it. The ring walk is the one `spot_key` describes: a cursor starts at
    the first seat to act and moves forward, and every seat it passes without a recorded action
    has folded there. Seats the cursor has not reached are still live, the distinction easy to
    get backwards - and getting it backwards made a history predicate look like a subtree one.
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
    The small blind because it is the one opening range the cutover commits and the single spot
    offering hero a raise and no call; legitimate otherwise, so a rejection is about the limp."""
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


def test_the_library_holds_one_chart_that_names_the_export_it_came_from(
    library: PreflopChartLibrary,
) -> None:
    """One chart, six-handed, 100bb, at the version decisions 4 and 5 share, pointing at the
    solve it was derived from.

    The count is the point rather than the name: two artifacts is the state where a reader
    cannot say which ranges the bot plays. And the provenance has to resolve to the GTOpen
    export rather than the GTO Wizard source - both exist in this tree and both are plausible
    strings, so a reference that merely points at something readable proves nothing.
    """
    assert len(library.artifacts) == 1
    artifact = library.artifacts[0]
    referenced = (REPO_ROOT / artifact.source.reference).resolve()

    assert artifact.artifact_schema_version == ARTIFACT_SCHEMA_VERSION == 2
    assert artifact.table_size == TABLE_SIZE
    assert artifact.stack_depth_bb == STACK_DEPTH_BB
    assert artifact.source.kind == "solver-export"
    assert len(artifact.spots) == len(library.spot_keys()) == COMMITTED_SPOTS
    assert referenced == COMMITTED_EXPORT_PATH.resolve()
    assert referenced.parent.name == "exports"


def test_every_committed_spot_satisfies_the_ruled_predicate(artifact: PreflopArtifact) -> None:
    """Both rulings, re-derived from the artifact's own keys rather than trusted.

    The predicate needs both clauses, either alone being a different chart: the history clause
    alone selects 65 nodes and admits 14 whose terminals can still go multiway, the subtree
    clause alone 4,865 and admits 4,814 reached through a cold call. A spot with three players
    still live is the error the 2026-08-25 supersession corrected and is invisible to every
    other check here - the cell converts, imports, and is priced by a model that cannot see
    three-way equity.

    The withholdings are the second half, asserted by the raise counts rather than the total,
    because 36 and 21 are both totals a wrong filter produces and both withheld families number
    15. No committed spot faces three raises, which is decision 20, and none faces four, which
    is the 2026-09-01 ruling. No committed sequence quotes 100 at all, the same claim read off
    the keys rather than the counts.
    """
    live_counts = Counter()
    raise_counts = Counter()
    for spot in artifact.spots:
        live, invested = live_and_invested(spot.hero_position, spot.action_sequence)
        assert invested <= 1, (spot.spot_id, invested)
        assert live <= 2, (spot.spot_id, live)
        live_counts[live] += 1
        raise_counts[sum(1 for e in spot.action_sequence if e.action == "raise")] += 1

    assert len(artifact.spots) == COMMITTED_SPOTS
    assert live_counts == {2: COMMITTED_SPOTS}
    assert dict(raise_counts) == RAISES_FACED_AT_A_COMMITTED_SPOT
    assert raise_counts[3] == 0, "decision 20 withholds every four-bet-facing spot"
    assert raise_counts[4] == 0, "the 2026-09-01 ruling withholds every jam-facing spot"
    for spot in artifact.spots:
        for entry in spot.action_sequence:
            assert entry.size_bb != 100.0, spot.spot_id


def test_the_chart_holds_one_opening_range_and_it_is_the_small_blinds(
    artifact: PreflopArtifact, library: PreflopChartLibrary
) -> None:
    """The ruled cost, stated as what the bot can and cannot do.

    Four of the five opens are among the 24 the predicate drops, so the bot cannot open a pot
    from the lojack, hijack, cutoff or button and refuses those decisions with a code. Taylor
    confirmed that on 2026-08-25 knowing it is a regression against the retired chart. A chart
    with a second opening range is one built on the superseded predicate, which is why the
    absences are asserted and not just the presence.
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

    `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` was phase 13's largest finding: the
    chart was solved at 0.5/1 and nothing stopped it being asked about a 1/3 game."""
    posted = card["config_posted"]
    positions, posts = list(posted["positions"]), list(posted["posts"])
    declared = artifact.blind_structure

    assert declared.small_blind_bb == posts[positions.index("SB")]
    assert declared.big_blind_bb == posts[positions.index("BB")]
    assert declared.ante_bb == posted["ante"]
    assert sum(posts) == declared.small_blind_bb + declared.big_blind_bb


# No small blind, a negative one, no big blind, inverted blinds, a negative ante. A zero ante is
# a real table and is deliberately not on the list.
IMPOSSIBLE_BLINDS = [(0.0, 1.0, 0.0), (-0.5, 1.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.5, 0.0),
                     (0.5, 1.0, -0.1)]


@pytest.mark.parametrize(("small", "big", "ante"), IMPOSSIBLE_BLINDS)
def test_a_blind_structure_that_is_not_one_is_rejected(
    small: float, big: float, ante: float
) -> None:
    """Validated on construction rather than merely stored: a field nothing validates is one a
    later artifact can fill with anything."""
    with pytest.raises(ValueError):
        schema.BlindStructure(small_blind_bb=small, big_blind_bb=big, ante_bb=ante)


def test_every_committed_cell_carries_an_arriving_reach(artifact: PreflopArtifact) -> None:
    """Decision 5: one reach value per cell, covering exactly the cells the chart answers, and
    `reach_bp_for` failing closed like every other lookup.

    A per-spot summary is not on the menu, a spot-level number being unable to tell one cell
    from another; a reach of zero is not committed either."""
    reach = dict(artifact.arriving_reach_bp)

    assert set(reach) == {spot.spot_id for spot in artifact.spots}
    for spot_id, classes in artifact.action_weights:
        cells = dict(reach[spot_id])
        assert set(cells) == {name for name, _ in classes}, spot_id
        for name, value in cells.items():
            assert isinstance(value, int) and not isinstance(value, bool), (spot_id, name)
            assert 0 < value <= QUANTISATION_SCALE, (spot_id, name, value)

    covered = artifact.reach_bp_for(SB_OPEN_KEY, "AA")
    deeper = f"t{TABLE_SIZE}/d500/SB/rfi"

    assert covered == reach_by_class(artifact, SB_OPEN_KEY)["AA"] > 0
    assert deeper not in {spot.spot_id for spot in artifact.spots}
    assert artifact.reach_bp_for(deeper, "AA") is None


def test_the_cells_at_full_reach_are_the_ones_hero_reaches_without_acting(
    artifact: PreflopArtifact,
) -> None:
    """Decision 5's field earns its place on the committed 21.

    Six sit at full reach and fifteen do not, so the per-cell field has something to distinguish
    at five spots out of seven. The six are named by a rule *and* listed, a count of six being
    what a chart holding the wrong six also reports: hero's whole range arrives exactly where
    hero has not yet acted, which is the small blind open-folded to and the big blind against
    each of the five opens. The spot count is asserted here too - on the stale 86-spot chart
    this file was authored against, the rule and the list both held over a set nobody committed.
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

    assert len(artifact.spots) == COMMITTED_SPOTS
    assert full == unacted
    assert len(full) == FULL_REACH_SPOTS
    assert full == {SB_OPEN_KEY} | {
        f"t{TABLE_SIZE}/d{STACK_DEPTH_BB}/BB/{seat}:raise@2.5" for seat in OPENING_SEATS
    }


def test_the_charts_reach_is_the_exports_reach_recomputed(
    artifact: PreflopArtifact, committed_export: SolverExport
) -> None:
    """The reach in the chart is the reach in the solve, class by class.

    Recomputed by walking the export directly and indexing it with GTOpen's own class
    ordering, so this is not two copies of one number agreeing with itself. It also catches the
    transposition defect: `hand_class_grid_index` and `gtopen_class_index` disagree on all but a
    handful of classes, and the wrong one swaps suited for offsuit while leaving every total
    intact. The last plan carries the weight, a chart writing 10,000 everywhere passing the ones
    where hero has not acted. **The withheld plans are followed too and must land nowhere**:
    agreeing on five probed spots is a property the stale 86-spot chart also had, and what tells
    this chart from that one is where it stops."""
    by_path = committed_export.by_path()
    declared = {spot.spot_id for spot in artifact.spots}
    graded = 0
    for label, plan in PROBE_PLANS.items():
        node, key = follow(by_path, plan)
        arriving = {name: node.reach_bp[gtopen_class_index(name)] for name in HAND_CLASSES}
        solved = {name: value for name, value in arriving.items() if value > 0}

        assert key in declared, label
        assert reach_by_class(artifact, key) == solved, label
        if len(set(solved.values())) > 20:
            graded += 1

    assert graded, "no probed spot had reach varying by class, so nothing was really compared"
    assert len(declared) == COMMITTED_SPOTS
    for label, plan in WITHHELD_PLANS.items():
        _, key = follow(by_path, plan)
        assert key not in declared, (label, key)


# The grid the export offers at the committed spots, and what the chart keeps of it. A GTOpen
# payload is unconditional - a hand hero folded three actions ago still carries a full strategy
# row - so all 21 nodes ship 169 classes and `reach_bp` alone says which hero can hold. 1,517
# of the 3,549 never arrive.
GRID_CELLS = 21 * 169
COMMITTED_CELLS = 2_032

# Within one basis point of 1/n, the quantisation step, so this is the untouched initialisation
# exactly rather than near it. Every one of the 592 is refused, and that is checkable without
# ruling an epsilon: a row the solver never moved is still where the solve put it.
EXACT_INITIALISATION_CELLS = 592

# The same rows at the two-point tolerance `UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY` used,
# restricted to menus of three or more actions, where 1/3 is not a frequency trained play lands
# on. **Over the committed 21 the two readings coincide exactly** - the same 592 cells, not
# merely the same count - where over the 36 the exact reading caught 1,593 and this one 592. The
# extra 1,001 were the jam spots' two-action rows at 5,000 and 5,000, all withheld now; the only
# two-action node left is the small blind's open, which has no uniform row at all.
UNIFORM_CELLS_ON_A_THREE_ACTION_MENU = 592
UNIFORM_TOLERANCE_BP = 200

# The lojack facing the hijack's three-bet, holding 72o. The class never arrives - nobody opens
# it from the lojack - so the solver never trained the cell and its row is the initialisation:
# 3,333, 3,333 and 3,334 across fold, call and raise. Committed, that reads as a considered
# three-way mix rather than as missing, which is what makes a uniform row worse than a gap.
# Until 2026-09-01 the named spot was the lojack answering the hijack's five-bet jam at 5,000
# and 5,000; that spot is withheld now, so the example moved one street shallower. The row is
# checked by deviation, `QUANTISATION_SCALE` not dividing by three.
UNTRAINED_SPOT = "t6/d100/LJ/LJ:raise@2.5,HJ:raise@7.5"
UNTRAINED_SEQUENCE = (
    PreflopAction("LJ", "raise", 2.5),
    PreflopAction("HJ", "raise", 7.5),
)
UNTRAINED_CLASS = "72o"
UNTRAINED_HERO = "LJ"


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
    committed cells against the export's own `reach_bp`, class by class, at all 21 spots, so the
    rule is checked where it is applied. 1,517 of the 3,549 never arrive and none is an answer.

    The bound is deliberately one-sided, and the reason is a blocker rather than a shortcut.
    Committing a class that never arrives is ruled out; refusing *more* than that is the open
    question - whether an untrained-cell rule fires at a two-action node, and at what reading -
    and no lower bound survives every candidate answer. So what is asserted is the ruled
    direction plus the ceiling: 2,032 is what refusing exactly the cells that never arrive
    commits, and nothing may commit more. Coverage is held by the tests either side, so an empty
    chart does not pass by default. Both totals are solve output; decision 2 ships as solved.

    **`export_cells` is the walk, so the spot count is compared against the artifact and not
    against itself.** Until 2026-09-01 this read `len(export_cells) == COMMITTED_SPOTS`, the
    walk agreeing with a constant: the fixture is built from `selected` and cannot see a wrong
    chart at all. What it has to be compared with is the artifact's own declared spots.
    """
    declared = {spot.spot_id for spot in artifact.spots}
    committed = 0
    for key, node in export_cells.items():
        arriving = {name for name in HAND_CLASSES if node.reach_bp[gtopen_class_index(name)] > 0}
        cells = set(weights_by_class(artifact, key))

        assert cells <= arriving, (key, sorted(cells - arriving))
        committed += len(cells)

    assert set(export_cells) == declared
    assert len(declared) == COMMITTED_SPOTS
    assert len(export_cells) * len(HAND_CLASSES) == GRID_CELLS
    assert 0 < committed <= COMMITTED_CELLS


def test_an_untrained_cell_is_refused_at_the_table_and_none_sits_at_the_initialisation(
    library: PreflopChartLibrary, artifact: PreflopArtifact, export_cells: dict[str, SolverNode]
) -> None:
    """The refusal asked as a query, and the same rule read off every strategy row.

    A cell missing from the weights is only a refusal if the lookup turns it into one with a
    code the caller can log, the same standard the excluded nodes are held to. The named spot is
    committed and answers a hand that does arrive, so one cell is being declined rather than the
    chart being empty - a chart holding nothing passes the refusal half on its own.

    Then the whole grid, off the row rather than the reach. Reach says a cell was never visited;
    the row says the solver never touched it, and neither implies the other - 925 cells at zero
    reach carry an ordinary row, and the row is what a reader sees. Asserted at the two
    tolerances needing nobody's ruling: within a basis point of 1/n, and the census tolerance on
    menus of three or more actions. Every cell either catches is refused already; over the
    committed 21 the readings catch the identical 592, so the looser one only detects drift.
    """
    assert UNTRAINED_SPOT in export_cells, "the named untrained spot is not committed"
    node = export_cells[UNTRAINED_SPOT]
    index = gtopen_class_index(UNTRAINED_CLASS)
    menu = len(node.actions)
    share = QUANTISATION_SCALE / menu
    row = [node.strategy_bp[act][index] for act in range(menu)]
    query = ChartQuery(
        TABLE_SIZE, STACK_DEPTH_BB, UNTRAINED_HERO, UNTRAINED_SEQUENCE, UNTRAINED_CLASS
    )

    assert node.reach_bp[index] == 0
    assert menu == 3, "the named untrained cell is no longer on a fold, call and raise menu"
    assert max(abs(weight - share) for weight in row) < 1.0, row

    refused = library.lookup(query)
    answered = library.lookup(
        ChartQuery(TABLE_SIZE, STACK_DEPTH_BB, UNTRAINED_HERO, UNTRAINED_SEQUENCE, "AA")
    )

    assert query.spot_key == UNTRAINED_SPOT
    assert isinstance(refused, ChartMiss)
    assert refused.code == MISS_HAND_CLASS_NOT_COVERED
    assert refused.spot_key == UNTRAINED_SPOT
    assert UNTRAINED_CLASS in refused.detail
    assert not isinstance(answered, ChartMiss), getattr(answered, "detail", "")
    assert answered.spot_key == UNTRAINED_SPOT

    exact = 0
    on_a_wide_menu = 0
    for key, cell_node in export_cells.items():
        committed = set(weights_by_class(artifact, key))
        width = len(cell_node.actions)
        uniform = QUANTISATION_SCALE / width
        for name in HAND_CLASSES:
            column = gtopen_class_index(name)
            weights = [cell_node.strategy_bp[act][column] for act in range(width)]
            deviation = max(abs(weight - uniform) for weight in weights)
            if deviation < 1.0:
                exact += 1
                assert name not in committed, (key, name)
            if width >= 3 and deviation < UNIFORM_TOLERANCE_BP:
                on_a_wide_menu += 1
                assert name not in committed, (key, name)

    assert exact == EXACT_INITIALISATION_CELLS
    assert on_a_wide_menu == UNIFORM_CELLS_ON_A_THREE_ACTION_MENU
    assert exact == on_a_wide_menu, "the two readings have stopped coinciding"


def test_the_schema_rejects_an_artifact_whose_hero_limps_and_accepts_one_that_does_not(
) -> None:
    """A spot with an empty action sequence may not carry a positive call weight.

    The pot is folded to hero, so a call is a limp, and `CHART-HERO-MUST-NEVER-LIMP` asks for
    this as a rule rather than a measurement over one file: the export enforces it by
    construction, "but that is a property of the data rather than a rule", and phase 14 owns the
    schema. The retired chart limps 13.73 percent from the small blind across 103 classes with a
    nonzero call weight, so this is not hypothetical. The same fixture without the limp is built
    afterwards, so the rejection is known to be about the limp.
    """
    with pytest.raises(ValueError, match="(?i)limp"):
        rfi_artifact(limping_class="A5s")

    built = rfi_artifact()

    assert built.audit_fields.spot_count == 1
    assert built.weights_for(SB_OPEN_KEY, "A5s") == (("raise", 1.0),)


def test_no_committed_spot_limps(artifact: PreflopArtifact) -> None:
    """And the committed chart satisfies the rule, which the rule alone does not prove: a schema
    rule no committed file exercises is a rule nobody has run. One folded-to-hero spot is left to
    exercise it, and the export does not even offer a call there, so the rule holds by
    construction and is asserted anyway."""
    folded_to_hero = {spot.spot_id for spot in artifact.spots if not spot.action_sequence}

    assert folded_to_hero == {SB_OPEN_KEY}
    for spot_id in folded_to_hero:
        for name, weights in weights_by_class(artifact, spot_id).items():
            called = sum(weight for action, weight in weights if action == "call")
            assert called == 0.0, (spot_id, name, called)


def test_the_committed_chart_reproduces_from_the_committed_export(
    artifact: PreflopArtifact,
) -> None:
    """The export is the source of truth; the chart and its sizings are its output. A hand edit
    to a derived file is a number with no origin, and `--check` is what tells one from a
    conversion nobody re-ran.

    **Reproducible is not the same as right, so the spot count goes with it.** A chart the
    converter regenerates byte for byte is still the wrong chart if the converter applies the
    wrong rulings, and until 2026-09-01 the only thing between this test and a green was whether
    somebody had run the converter - a sibling in this family used to do exactly that, mid-run.
    The interpreter is `sys.executable`, so a second one cannot answer for this.
    """
    result = subprocess.run(
        [sys.executable, str(CONVERTER), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert len(artifact.spots) == COMMITTED_SPOTS


def test_the_chart_confesses_the_realization_bias_and_what_it_left_out(
    artifact: PreflopArtifact, committed_export: SolverExport
) -> None:
    """Both halves of the audit note the contract requires, off the one field carrying them.

    `REALIZATION-MODEL-UNDERPRICES-POSITION` is accepted and recorded rather than corrected.
    GTOpen prices postflop with a scalar realization weight rather than a solve, and the big
    blind folds far more than a real solve gives facing a 2.5bb small-blind open, closing the
    action in position. The closing measurement names it as a third explanation it cannot
    separate and the big blind holds 58 of the 89 human call disagreements, so leaving it
    unnamed makes that measurement unfalsifiable. The fold frequency is recomputed from the
    export rather than compared against a remembered 50.98.

    The other half is what is absent: `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` and
    `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` are why the chart holds 21 rather than
    the tree, and the counts tell a reader each absence is a decision rather than an oversight.
    **Three absences now, and the notes must distinguish the last two.** Both withheld families
    number 15, so one "15" describes either and neither; the notes must name the four-bet pot
    and the jam after it, so a reader can tell a node refused for its own mispricing from one
    refused for its parent's.
    """
    notes = artifact.audit_fields.notes
    lowered = notes.lower()
    folds = 100.0 - aggregate_frequencies(committed_export).defence_pct["SB"]
    quoted = [float(text) for text in re.findall(r"\d+\.\d+", notes)]

    assert "realization" in lowered
    assert "position" in lowered
    assert "fold" in lowered
    assert "2.5" in notes
    assert any(abs(value - folds) <= 0.05 for value in quoted), (folds, quoted)

    assert "multiway" in lowered
    assert "four-bet" in lowered
    assert "jam" in lowered, "the notes do not say what happened to the answers to a five-bet"
    assert "29,104" in notes or "29104" in notes
    assert "21" in notes
    assert lowered.count("15") >= 2, "one 15 cannot describe both withheld families"
