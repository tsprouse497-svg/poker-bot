"""Phase 14: the shape of the committed chart, and what its published cells must be.

Authored at stage 4, before the converter that must satisfy it, so this file is a
specification rather than a description of what got built.

**What this file owns.** That the chart is reproduced byte for byte from
`data/artifacts/preflop/exports/` by a committed script with a `--check` mode that writes
nothing; that the retired chart stays absent from the artifact directory, its glob and
`sizings/`; that the committed 249 are 249 *keys*, checked one at a time; that the artifact
declares the blind structure the solve posted and refuses one that describes no game; that
no spot folded to hero carries a call weight; that no committed row is the solver's
untouched initialisation and that zero-reach classes are dropped; and decision 45's merge -
the menu shape per family and each merged cell's published defence.

**What siblings own.** `tests/test_chart_derivation.py` owns *which* nodes are committed and
why the others are not, and this file imports its `selected`, its committed count and its
raises-faced histogram rather than restating them. `tests/test_chart_conversion.py` owns the
price: the sizing table, the two-directional invariant, the perturbed synthetic export and
the jam canary; it imports this file's walk and its `vacuous` helper.
`tests/test_chart_arrival_probability.py` owns reach as a published field and arrival.

**Two habits run through both of this lane's files.** Every count is recomputed here by a
walk written in this file rather than imported from the derivation under test - a test that
imports the rule it checks is one copy of a rule agreeing with another. And a criterion the
committed 249 cannot exercise is *labelled* vacuous and skipped rather than counted as a
check that passed, after an assertion that the vacuity premise still holds.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

# The sibling that owns the selection, as a module rather than by name: the 249-node
# interface it publishes does not exist until that file is re-cut, and naming its members in
# an import block would turn every miss into a collection error that silences this file too.
import test_chart_derivation as spec

from poker_training_bot.poker_core.positions import table_positions

# The derivation as a module for the same reason: decision 45's merge does not exist until
# stage 6, so `chart_derivation.merged_cells` must fail per test rather than at import.
from poker_training_bot.solver_artifacts import chart_derivation, schema
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

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
SIZINGS_DIR = ARTIFACT_DIR / "sizings"
EXPECTATIONS_DIR = ARTIFACT_DIR / "expectations"
CONVERTER = REPO_ROOT / "scripts" / "convert_preflop_export.py"

TABLE_SIZE = 6
STACK_DEPTH_BB = 100

RETIRED_CHART_NAME = "six_max_nl25_100bb.json"
"""The GTO Wizard chart, deleted on 2026-08-30 and required to stay deleted. The same name
still exists under `expectations/`, which is the external oracle and deliberately not a
chart, so the absence is asserted against three places a chart can hide rather than one."""

LIVE_CHART_NAME = "six_max_100bb_rakefree.json"
"""What stage 6 writes at the same path the stale 86-spot build occupies today. Asserted
present beside the absence above, an empty artifact directory otherwise passing both."""

# --- The families decision 45 rules over, and their published menus ---------------------
#
# Recomputed below by a walk, not read off the artifact: a menu read from the file under
# test is the file agreeing with itself. `first-in` is the pot folded to hero, `bb-open` the
# big blind facing an open, `merged` the twenty other seats facing an open, `three-bet` the
# spots facing a three-bet.
FIRST_IN, BB_OPEN, MERGED, THREE_BET = "first-in", "bb-open", "merged", "three-bet"

FAMILY_SIZES = {FIRST_IN: 5, BB_OPEN: 5, MERGED: 20, THREE_BET: 219}
"""5 + 5 + 20 + 219 = 249. The contract's 25 facing an open split into the 5 big-blind spots
that publish unchanged and the 20 that merge; decisions 45 and 48."""

PUBLISHED_MENUS = {
    FIRST_IN: ("fold", "raise"),
    BB_OPEN: ("call", "fold", "raise"),
    MERGED: ("fold", "raise"),
    THREE_BET: ("call", "fold", "raise"),
}
"""What each family publishes. The first-in spots have no call to publish - the solve offers
none - while the merged twenty *had* one and no longer do, so the two share a menu for
different reasons and only the merged one is evidence about decision 45."""

MERGED_CELLS = 165
MERGED_CELLS_PURE_ENTIRE_WEIGHT = 40
MERGED_CELLS_PURE_AT_99 = 73
"""Decision 45 as corrected by decision 53. The 165 is the number of cells at the twenty
merged spots whose solve puts weight on calling; 40 put a hand's *entire* weight there and 73
put 99 percent or more. Two measures under one name is how the 73 was published as the 40."""

CELLS_AT_NON_ZERO_REACH = 18_431
ZERO_REACH_CELLS_DROPPED = 23_650
"""249 spots times 169 classes is 42,081 grid cells; the chart holds the 18,431 hero can
arrive holding. Decision 49's denominator, and the dropped count is asserted beside it
because a converter that dropped nothing and a converter that dropped everything both agree
with a one-sided bound."""

EXACT_UNIFORM_CELLS = 0
TOLERANT_UNIFORM_CELLS = 0
UNIFORM_TOLERANCE_BP = 200
"""`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`, at both readings the contract names:
within a basis point of 1/n, the quantisation step, and within two points of it. Both read
zero over the committed 249 and the readings are compared as *sets*, which two zeroes agreeing
as counts cannot show."""

CALL_CELLS_AT_A_FIRST_IN_SPOT = 0
"""The vacuity premise for `CHART-HERO-MUST-NEVER-LIMP` over this artifact: the five first-in
nodes offer hero no call action at all, so no committed cell can carry the weight the schema
rule forbids. Asserted before the criterion is labelled vacuous."""


def vacuous(what: str) -> None:
    """Stop the test and record it as skipped rather than as a pass.

    The contract keeps three criteria the committed 249 cannot exercise and requires each
    labelled vacuous wherever it is reported and never counted as a check that passed. A
    skip is the only outcome pytest has that is neither. Every call sits *after* an
    assertion that the premise making it vacuous still holds, so a later solve that
    reactivates the criterion turns the premise red rather than leaving the skip stale.
    """
    pytest.skip(f"VACUOUS over the committed {spec.COMMITTED_NODES}: {what}")


# --- The walk. Written here, not imported from the conversion on trial -----------------


def action_sequence_of(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> tuple[PreflopAction, ...]:
    """What hero faces at a node: the live actions in front of him, in order.

    The actor of a recorded action is whoever was to act at the node the action was taken
    *at*, which is the parent of the node it leads to. Reading it off the child shifts every
    entry one seat round the ring - the lojack's open becomes the hijack's - and the result
    keys a spot that never happened while validating perfectly. Folds never enter: an empty
    sequence means the pot was folded to hero, and a recorded fold would be a second
    spelling of the same spot that keys apart from the first.
    """
    entries: list[PreflopAction] = []
    for depth, index in enumerate(node.path):
        parent = by_path[node.path[:depth]]
        action = parent.actions[index]
        if action.kind == "fold":
            continue
        if action.kind == "call":
            entries.append(PreflopAction(parent.actor_pos, "call"))
        else:
            entries.append(PreflopAction(parent.actor_pos, "raise", float(action.to)))
    return tuple(entries)


def key_of(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> str:
    """The spot key a node derives, in the one vocabulary this repo names spots with."""
    return spot_key(TABLE_SIZE, STACK_DEPTH_BB, node.actor_pos, action_sequence_of(by_path, node))


def raises_faced_of(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> int:
    """How many raises are already in when hero is asked."""
    return sum(1 for entry in action_sequence_of(by_path, node) if entry.action == "raise")


def family_of(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> str:
    """Which of decision 45's four families a committed node belongs to."""
    faced = raises_faced_of(by_path, node)
    if faced == 0:
        return FIRST_IN
    if faced == 1:
        return BB_OPEN if node.actor_pos == "BB" else MERGED
    return THREE_BET


def arriving_classes(node: SolverNode) -> list[str]:
    """The classes hero can be holding here, in the grid order the artifact writes."""
    return [
        name
        for name in sorted(HAND_CLASSES, key=hand_class_grid_index)
        if node.reach_bp[gtopen_class_index(name)] > 0
    ]


def solve_weights(node: SolverNode, hand_class_text: str) -> dict[str, int]:
    """One cell as the solve holds it, in basis points, keyed by the artifact's action names
    with a jam counted as a raise. Read off the node so the merge below compares the
    published number against the source rather than against another published number."""
    column = gtopen_class_index(hand_class_text)
    totals = {"fold": 0, "call": 0, "raise": 0}
    for index, action in enumerate(node.actions):
        recorded = "raise" if action.kind in ("raise", "jam") else action.kind
        totals[recorded] = totals.get(recorded, 0) + node.strategy_bp[index][column]
    return totals


def weights_by_class(artifact: PreflopArtifact, spot_id: str) -> dict[str, dict[str, float]]:
    for keyed, classes in artifact.action_weights:
        if keyed == spot_id:
            return {name: dict(weights) for name, weights in classes}
    raise AssertionError(f"the committed artifact declares no spot {spot_id!r}")


def reach_by_class(artifact: PreflopArtifact, spot_id: str) -> dict[str, int]:
    for keyed, classes in artifact.arriving_reach_bp:
        if keyed == spot_id:
            return dict(classes)
    raise AssertionError(f"the committed artifact carries no arriving reach for {spot_id!r}")


@pytest.fixture(scope="module")
def committed_export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def by_path(committed_export: SolverExport) -> dict[tuple[int, ...], SolverNode]:
    """The export indexed by path, loaded once: a node's key is read off its ancestors."""
    return committed_export.by_path()


_COMMITTED: dict[int, dict[str, SolverNode]] = {}


def committed_nodes(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode]
) -> dict[str, SolverNode]:
    """Every committed node, keyed by the walk above.

    `spec.selected` is the three ruled clauses and is the sibling's to own; the keying is
    this file's, because "249 nodes" and "249 keys" are different claims and the second is
    what the chart has to satisfy. A function rather than a fixture on purpose: while the
    sibling is mid-re-cut this call is the thing that fails, and a fixture would report that
    as a setup error against every test at once instead of as a failure inside each.
    """
    if id(export) not in _COMMITTED:
        _COMMITTED[id(export)] = {
            key_of(by_path, node): node for node in spec.selected(export)
        }
    return _COMMITTED[id(export)]


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR))


@pytest.fixture(scope="module")
def artifact(library: PreflopChartLibrary) -> PreflopArtifact:
    assert len(library.artifacts) == 1, "two charts is the state nobody can read"
    return library.artifacts[0]


@pytest.fixture(scope="module")
def card() -> dict:
    return load_source_card(COMMITTED_SOURCE_CARD_PATH)


def rfi_artifact(limping_class: str | None = None) -> PreflopArtifact:
    """A hand-built one-spot artifact: the small blind, pot folded to hero, every class
    covered and every class raising. Legitimate in every other respect, so a rejection is
    known to be about the limp rather than about the fixture."""
    key = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "SB", ())
    ordered = tuple(sorted(HAND_CLASSES, key=hand_class_grid_index))
    cells = tuple(
        (name, (("call", 1.0),) if name == limping_class else (("raise", 1.0),))
        for name in ordered
    )
    action_weights = ((key, cells),)
    return PreflopArtifact(
        artifact_schema_version=ARTIFACT_SCHEMA_VERSION,
        source=ArtifactSource("stage four fixture", "hand-authored", "tests/derived-chart"),
        generated_at="2026-09-02T00:00:00Z",
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
        arriving_reach_bp=((key, tuple((name, QUANTISATION_SCALE) for name in ordered)),),
    )


# --- Derived from the export, reproducibly, and the retired chart stays gone ------------


def test_the_chart_is_reproduced_from_the_export_and_check_writes_nothing(
    artifact: PreflopArtifact,
) -> None:
    """The export is the source of truth and the chart is its output.

    A hand edit to a derived file is a number with no origin, and `--check` is what tells one
    from a conversion nobody re-ran. Three things are asserted and they fail apart. The
    converter's declared outputs must all sit under `data/artifacts/preflop/`, so a
    reproduction check that quietly writes somewhere else is caught. `--check` must leave
    every one of them byte-identical *and* untouched - rewriting a file with identical
    content is still a write, and a `--check` that repairs the tree before comparing it
    always agrees with itself. And the run must exit zero.

    **Reproducible is not the same as right, so the spot count travels with it**: a chart the
    converter regenerates byte for byte is still the wrong chart if the converter applies the
    wrong rulings, and the count is what tells the committed 249 from the 86 in the tree now.
    """
    import scripts.convert_preflop_export as converter

    declared = [path for path, _ in converter.outputs()]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in declared}
    result = subprocess.run(
        [sys.executable, str(CONVERTER), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert declared, "the converter declares no outputs, so --check proves nothing"
    for path in declared:
        assert ARTIFACT_DIR in path.parents, f"the converter writes outside the chart tree: {path}"
    for path in declared:
        assert path.read_bytes() == before[path][0], f"--check rewrote {path}"
        assert path.stat().st_mtime_ns == before[path][1], f"--check touched {path}"
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(artifact.spots) == spec.COMMITTED_NODES


def test_the_retired_chart_stays_absent_from_the_directory_the_glob_and_the_sizings() -> None:
    """The GTO Wizard chart was deleted on 2026-08-30 and does not come back.

    Three places, because a chart hides in three ways: the path itself, the glob the importer
    reads (a second chart in the directory is a library nobody can read), and `sizings/`,
    where a price table outliving its chart would price the new one from the old one's
    ladder. The retired chart three-bet to 8, 11 and 13.5 and opened the small blind to 3.5,
    none of which is a price this solve offers.

    Two assertions beside the absences, because an empty directory satisfies all three: the
    chart stage 6 writes must be present, and the file that shares the retired chart's *name*
    under `expectations/` must still be there. That file is the external oracle - the only
    figures in this phase this repo did not produce - and it is deliberately not a chart.
    """
    charts = {path.name for path in ARTIFACT_DIR.glob("*.json")}

    assert not (ARTIFACT_DIR / RETIRED_CHART_NAME).exists()
    assert RETIRED_CHART_NAME not in charts
    assert not (SIZINGS_DIR / RETIRED_CHART_NAME).exists()

    assert charts == {LIVE_CHART_NAME}, sorted(charts)
    assert (SIZINGS_DIR / LIVE_CHART_NAME).exists()
    assert (EXPECTATIONS_DIR / RETIRED_CHART_NAME).exists(), "the external oracle is gone"


def test_the_committed_nodes_are_two_hundred_and_forty_nine_distinct_keys(
    artifact: PreflopArtifact, committed_export: SolverExport
) -> None:
    """249 nodes are not self-evidently 249 keys, so the count is taken key by key.

    Two nodes reaching the same key is a grammar collision. The spot key states what hero
    *faces*, and two different lines can face the same thing - so a collision would silently
    merge two solved cells into one committed cell, and neither a node count nor a key count
    on its own can see it. The contract's disposition is that a collision is a halt and a
    decision, never a merge, so the walk collects every node under its key and asserts each
    bucket holds one.

    The artifact is then compared against the walk as *sets* rather than as counts, a chart
    holding 249 of the wrong keys reporting the right total, and the raises-faced histogram
    goes with it: 5 first-in, 25 facing an open, 219 facing a three-bet is what tells this
    selection from one that admitted the four-bet family and refused something else.
    """
    by_path = committed_export.by_path()
    buckets: dict[str, list[tuple[int, ...]]] = {}
    faced: dict[int, int] = {}
    for node in spec.selected(committed_export):
        buckets.setdefault(key_of(by_path, node), []).append(node.path)
        depth = raises_faced_of(by_path, node)
        faced[depth] = faced.get(depth, 0) + 1

    collisions = {key: paths for key, paths in buckets.items() if len(paths) > 1}

    assert collisions == {}, "a spot key is claimed by two solved nodes; halt, do not merge"
    assert len(buckets) == spec.COMMITTED_NODES
    assert faced == spec.RAISES_FACED_WHEN_COMMITTED
    assert {spot.spot_id for spot in artifact.spots} == set(buckets)
    assert len(artifact.spots) == len(buckets)
    assert artifact.audit_fields.spot_count == len(buckets)


# --- The blind structure the solve was played at ---------------------------------------


def test_the_chart_declares_the_blind_structure_the_solve_posted(
    artifact: PreflopArtifact, card: dict
) -> None:
    """Decision 4, with the blinds read off the posted config rather than spelled here.

    `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` was phase 13's largest finding:
    the chart was solved at 0.5/1 and nothing stopped it being asked about a 1/3 game, where
    the same hand at the same stack depth is a different decision.
    """
    posted = card["config_posted"]
    positions, posts = list(posted["positions"]), list(posted["posts"])
    declared = artifact.blind_structure

    assert declared.small_blind_bb == posts[positions.index("SB")]
    assert declared.big_blind_bb == posts[positions.index("BB")]
    assert declared.ante_bb == posted["ante"]
    assert sum(posts) == declared.small_blind_bb + declared.big_blind_bb


# No small blind, a negative one, no big blind, blinds the wrong way round, a negative ante.
IMPOSSIBLE_BLINDS = [
    (0.0, 1.0, 0.0),
    (-0.5, 1.0, 0.0),
    (0.5, 0.0, 0.0),
    (1.0, 0.5, 0.0),
    (1.0, 1.0, 0.0),
    (0.5, 1.0, -0.1),
]


@pytest.mark.parametrize(("small", "big", "ante"), IMPOSSIBLE_BLINDS)
def test_a_blind_structure_that_describes_no_game_is_refused_at_construction(
    small: float, big: float, ante: float
) -> None:
    """Refused where it is built, not where it is read. A field nothing validates is one a
    later artifact fills with anything, and the lookup that refuses a mismatched table would
    then be comparing against a number that never described a game. A small blind *equal* to
    the big blind is on the list beside one above it: the contract says at or above."""
    with pytest.raises(ValueError):
        schema.BlindStructure(small_blind_bb=small, big_blind_bb=big, ante_bb=ante)


def test_a_zero_ante_is_a_real_table_and_is_accepted() -> None:
    """The one case the refusals must not sweep up, and the one this solve posted. Asserted
    on its own because a construction guard that refused everything passes the six above."""
    built = schema.BlindStructure(small_blind_bb=0.5, big_blind_bb=1.0, ante_bb=0.0)

    assert (built.small_blind_bb, built.big_blind_bb, built.ante_bb) == (0.5, 1.0, 0.0)


# --- What the ranges must not have become ----------------------------------------------


def test_the_schema_refuses_an_artifact_whose_hero_limps(artifact: PreflopArtifact) -> None:
    """`CHART-HERO-MUST-NEVER-LIMP` as a rule rather than as a measurement over one file.

    The pot folded to hero is an empty `action_sequence`, so a call there is a limp: hero
    pays the big blind to give every seat behind a free look in position. The export enforces
    it by construction, but that is a property of the data rather than a rule, and a rule is
    what refuses the *next* artifact. The retired chart limped 13.73 percent from the small
    blind across 103 classes, so this is the state the repo shipped in.

    The same fixture without the limp is built afterwards, a schema that refused everything
    passing the first half on its own, and the committed chart is checked against the rule
    beside it - a schema rule no committed file exercises is a rule nobody has run.
    """
    with pytest.raises(ValueError, match="(?i)limp"):
        rfi_artifact(limping_class="A5s")

    built = rfi_artifact()

    assert built.audit_fields.spot_count == 1
    assert built.weights_for(spot_key(TABLE_SIZE, STACK_DEPTH_BB, "SB", ()), "A5s") == (
        ("raise", 1.0),
    )
    for spot in artifact.spots:
        if spot.action_sequence:
            continue
        for name, weights in weights_by_class(artifact, spot.spot_id).items():
            assert weights.get("call", 0.0) == 0.0, (spot.spot_id, name)


def test_no_first_in_spot_could_carry_a_call_weight_here(
    committed_export: SolverExport, by_path
) -> None:
    """The no-limp schema rule, vacuous here, with its premise asserted before the label.

    Not one of the contract's three vacuous criteria - those are the two-price sizing schema,
    the no-raise half of the sizing invariant and the jam-and-named-raise collapse, all three
    labelled in `test_chart_conversion.py` and counted as exactly three by the report. This is
    a fourth vacuity the phase carries, reported as a schema rule rather than as one of them.

    The rule above forbids a call at a spot folded to hero. Over the committed 249 nothing
    can violate it: the five first-in nodes offer hero fold and a raise and no call at all,
    so there is no weight for the converter to write. The rule is retained because a solve
    with `limp: true` reactivates it, and the premise is asserted so that solve turns this
    red rather than leaving a stale skip.
    """
    keyed = committed_nodes(committed_export, by_path)
    first_in = [n for n in keyed.values() if family_of(by_path, n) == FIRST_IN]
    offered = sum(1 for node in first_in for action in node.actions if action.kind == "call")

    assert len(first_in) == FAMILY_SIZES[FIRST_IN]
    assert offered == CALL_CELLS_AT_A_FIRST_IN_SPOT
    vacuous("no first-in node offers hero a call, so no committed cell can limp")


def test_no_committed_row_is_the_solvers_untouched_initialisation(
    artifact: PreflopArtifact, committed_export: SolverExport, by_path
) -> None:
    """`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`, with its reach precondition.

    A GTOpen payload is unconditional: a hand hero folded three actions ago still carries a
    full strategy row, and an untouched row is the solver's initialisation - an even split
    across the menu - rather than a played frequency. The criterion is stated over cells with
    **non-zero reach**, so the precondition is half the check and is asserted first: the
    converter must drop the classes hero cannot be holding. 18,431 of the 42,081 grid cells
    survive that and 23,650 do not, and both are asserted, a one-sided bound being satisfied
    by a converter that dropped everything.

    Then the rows, at both readings the contract names - within a basis point of 1/n, the
    quantisation step, so this is the initialisation exactly rather than near it; and within
    two points of it, which is where a trained frequency does not land on a menu of three.
    Both read zero, and they are compared as **sets**, which two zeroes agreeing as counts
    cannot show.
    """
    keyed = committed_nodes(committed_export, by_path)
    kept = 0
    dropped = 0
    exact: set[tuple[str, str]] = set()
    tolerant: set[tuple[str, str]] = set()

    for key, node in keyed.items():
        arriving = arriving_classes(node)
        dropped += len(HAND_CLASSES) - len(arriving)
        kept += len(arriving)
        assert list(weights_by_class(artifact, key)) == arriving, key
        assert list(reach_by_class(artifact, key)) == arriving, key

        width = len(node.actions)
        even = QUANTISATION_SCALE / width
        for name in arriving:
            column = gtopen_class_index(name)
            row = [node.strategy_bp[index][column] for index in range(width)]
            deviation = max(abs(weight - even) for weight in row)
            if deviation < 1.0:
                exact.add((key, name))
            if deviation < UNIFORM_TOLERANCE_BP:
                tolerant.add((key, name))

    assert kept == CELLS_AT_NON_ZERO_REACH
    assert dropped == ZERO_REACH_CELLS_DROPPED
    assert len(exact) == EXACT_UNIFORM_CELLS
    assert len(tolerant) == TOLERANT_UNIFORM_CELLS
    assert exact == tolerant, "the exact and tolerant readings have stopped agreeing"


# --- Decision 45: the bot's cold call is merged into its raise, not deleted -------------


def test_the_menu_shape_is_the_one_decision_45_rules_for_each_family(
    artifact: PreflopArtifact, committed_export: SolverExport, by_path
) -> None:
    """The four families and what each publishes, asserted apart rather than in total.

    The five first-in spots publish fold and a raise, having no call on offer. The five big
    blind spots facing an open publish fold, call and three-bet unchanged - the big blind is
    already in for one blind, so its call is a defence rather than a cold call. The twenty
    other seats facing an open publish **raise or fold**: their call is a cold call the bot
    may not make, and decision 45 merges it rather than deleting it. The 219 spots facing a
    three-bet publish fold, call and four-bet, hero's call there being a call to a raise he
    made himself.

    The family sizes are asserted with the menus because 5 + 5 + 20 + 219 and 5 + 20 + 5 +
    219 are the same 249, and a converter that took the big blind for one of the merged seats
    would publish the right number of the wrong menus.
    """
    keyed = committed_nodes(committed_export, by_path)
    sizes: dict[str, int] = {}
    for key, node in keyed.items():
        family = family_of(by_path, node)
        sizes[family] = sizes.get(family, 0) + 1
        published = {
            action
            for weights in weights_by_class(artifact, key).values()
            for action in weights
        }
        assert tuple(sorted(published)) == PUBLISHED_MENUS[family], (key, family)

    assert sizes == FAMILY_SIZES
    assert sum(sizes.values()) == spec.COMMITTED_NODES


def test_each_merged_cell_publishes_the_solves_raise_plus_its_call(
    artifact: PreflopArtifact, committed_export: SolverExport, by_path
) -> None:
    """The merge itself, cell by cell against the solve.

    At each of the twenty merged spots the published raise weight is the solve's raise plus
    its call, to the basis point, and no cold-call weight is published anywhere. The two
    failures this separates are the ones decision 45 was ruled between: a converter that
    *publishes* the call has not merged, and one that drops it has thrown range away - at 9
    of these spots the solve puts a hand's entire weight on calling, so dropping would leave
    an all-zero row, which is the untouched initialisation the criterion above forbids.

    **165 cells move**, 40 of them a hand's entire weight and 73 at 99 percent or more, and
    all three are asserted because they are three measures the record has published under one
    name. The fold weight is asserted unchanged beside the raise: a converter that renormalised
    the row rather than adding into the raise would satisfy the sum and change every fold.
    """
    keyed = committed_nodes(committed_export, by_path)
    moved = 0
    entire = 0
    at_99 = 0
    for key, node in keyed.items():
        if family_of(by_path, node) != MERGED:
            continue
        published = weights_by_class(artifact, key)
        for name in arriving_classes(node):
            solved = solve_weights(node, name)
            cell = published[name]

            assert "call" not in cell, (key, name, "a cold-call weight was published")
            assert cell["raise"] == pytest.approx(
                (solved["raise"] + solved["call"]) / QUANTISATION_SCALE, abs=1e-4
            ), (key, name)
            assert cell["fold"] == pytest.approx(
                solved["fold"] / QUANTISATION_SCALE, abs=1e-4
            ), (key, name)
            if solved["call"] > 0:
                moved += 1
            if solved["call"] == QUANTISATION_SCALE:
                entire += 1
            if solved["call"] >= 0.99 * QUANTISATION_SCALE:
                at_99 += 1

    assert moved == MERGED_CELLS
    assert entire == MERGED_CELLS_PURE_ENTIRE_WEIGHT
    assert at_99 == MERGED_CELLS_PURE_AT_99


def test_the_unmerged_families_publish_the_solves_call_untouched(
    artifact: PreflopArtifact, committed_export: SolverExport, by_path
) -> None:
    """The other side of the merge, without which it is a rule with no boundary.

    A converter that merged *everywhere* passes the test above and destroys the big blind's
    defending range and every call to a three-bet. So the five big-blind spots facing an open
    and the 219 facing a three-bet are checked to publish the solve's call and raise apart,
    to the basis point, with `chart_derivation.merged_cells` asked which cells it moved so
    the derivation's own answer is compared against the walk rather than assumed.
    """
    keyed = committed_nodes(committed_export, by_path)
    checked = 0
    for key, node in keyed.items():
        if family_of(by_path, node) not in (BB_OPEN, THREE_BET):
            continue
        published = weights_by_class(artifact, key)
        for name in arriving_classes(node):
            solved = solve_weights(node, name)
            cell = published[name]

            assert cell["call"] == pytest.approx(
                solved["call"] / QUANTISATION_SCALE, abs=1e-4
            ), (key, name)
            assert cell["raise"] == pytest.approx(
                solved["raise"] / QUANTISATION_SCALE, abs=1e-4
            ), (key, name)
            checked += 1

    assert checked == CELLS_AT_NON_ZERO_REACH - (
        FAMILY_SIZES[FIRST_IN] * len(HAND_CLASSES) + FAMILY_SIZES[MERGED] * len(HAND_CLASSES)
    )
    assert len(chart_derivation.merged_cells(committed_export)) == MERGED_CELLS
