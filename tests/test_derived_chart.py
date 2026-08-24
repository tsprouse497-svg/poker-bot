"""Phase 14: the committed derived chart, and what its ranges must not have become.

Authored before the converter, the artifact and the report exist, and frozen before any of
them does, so this file is the specification rather than a description of what got built. It
owns the committed data: that the raked chart it replaces is gone, that the library holds one
chart at the new schema version, that every cell carries the arriving reach the selection rule
was ruled on, that no cell limps, that the cells are monotone under the two relations that
hold in every preflop spot, and that the two orderings the export was gated on survived the
conversion. `test_chart_derivation.py` owns the conversion and `test_derived_chart_report.py`
owns the report.

Two habits run through it. Nothing is checked against a number this repo remembered: the
reach, the realization measurement and the blind structure are recomputed from the committed
export or read off the committed source card, because a chart checked against a constant
somebody typed beside it is one number agreeing with itself. And the walk that locates an
export node is written here rather than imported from the conversion module, for the same
reason - it is the conversion that is on trial.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess

import pytest

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts import schema
from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG
from poker_training_bot.solver_artifacts.gtopen_expectations import aggregate_frequencies
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    SolverExport,
    export_checksum,
    gtopen_class_index,
    load_solver_export,
    load_source_card,
    source_card_errors,
)
from poker_training_bot.solver_artifacts.hand_classes import (
    HAND_CLASSES,
    HIGH_TO_LOW_RANKS,
    hand_class_grid_index,
)
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

ARTIFACTS = REPO_ROOT / "data" / "artifacts"
ARTIFACT_DIR = ARTIFACTS / "preflop"
SIZINGS_DIR = ARTIFACT_DIR / "sizings"
EXPECTATIONS_PATH = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"
GTOWIZARD_SOURCE_PATH = ARTIFACT_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"
RETIRED_CHART_NAME = "six_max_nl25_100bb.json"
CONVERTER = REPO_ROOT / "scripts" / "convert_preflop_export.py"

TABLE_SIZE = 6
STACK_DEPTH_BB = 100
OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")
OPENING_ORDER = ("LJ", "HJ", "CO", "BTN")

MONOTONICITY_TOLERANCE_PCT = 1.0
"""Decision 10, ruled 2026-08-24: adjacent ranks, one percentage point, both relations."""

# The external oracle this phase must not rederive: a reference regenerated from what it
# checks cannot fail, so it is pinned by content.
EXPECTATIONS_SHA256 = "39a80b67ae9d47b86656e42092b2ed97bd5829e28b86d56087a1805e3c90e373"

# The 300-iteration solve decision 2 replaces, so a restamp can be shown to be one.
SUPERSEDED_EXPORT_SHA256 = "1c9e383df22e91ee1103e846077371d9b47731c10ab54110bde6d0905271a739"
SUPERSEDED_SAVE_SHA256 = "64d8729a30f758f24e713976ac529bab64c741d22af4b68bdeea424864f27ab5"


def chart_derivation():
    """Imported inside the call rather than at module scope, because stage 6 creates it.

    A module-scope import of a module that does not exist yet hides every assertion here
    behind one collection error, which is `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`. A
    function-body import is also not sorted by isort, so it lints the same either way."""
    import poker_training_bot.solver_artifacts.chart_derivation as module

    return module


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

# Where these tests look the export up: each plan is the actions taken from the root, and the
# node it lands on is the one whose reach the artifact claims to carry. All but the last land
# where hero has not acted, so every class arrives at full weight.
PROBE_PLANS: dict[str, tuple[tuple[str, float | None], ...]] = {
    "LJ open-fold": (),
    "HJ open-fold": (FOLD,),
    "CO open-fold": (FOLD, FOLD),
    "BTN open-fold": (FOLD, FOLD, FOLD),
    "SB open-fold": (FOLD, FOLD, FOLD, FOLD),
    "BB facing a button open": (FOLD, FOLD, FOLD, OPEN, FOLD),
    "BB facing a small-blind open": (FOLD, FOLD, FOLD, FOLD, OPEN),
    "LJ facing a cutoff three-bet": (OPEN, FOLD, THREE_BET, FOLD, FOLD, FOLD),
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


_ADJACENT_PAIRS = tuple(
    (f"{high}{high}", f"{low}{low}")
    for high, low in zip(HIGH_TO_LOW_RANKS, HIGH_TO_LOW_RANKS[1:], strict=False)
)
_SUITED_OVER_OFFSUIT = tuple(
    (f"{high}{low}s", f"{high}{low}o")
    for index, high in enumerate(HIGH_TO_LOW_RANKS)
    for low in HIGH_TO_LOW_RANKS[index + 1 :]
)
RELATIONS = (("ladder", _ADJACENT_PAIRS), ("twins", _SUITED_OVER_OFFSUIT))
"""Decision 10's two relations, nothing wider. Plain card-rank dominance gives 61 to 121
violations per node and its top hits are correct poker - the lojack opens 76s always and T6s
never - because preflop strength is not totally ordered."""


def play_pct(weights) -> float | None:
    """How often a hand is played rather than folded, as a percentage. This is the quantity
    decision 10's relations are monotone in, and the only one that is: a per-action rule is
    false wherever hero can call, since the big blind three-bets aces always and never calls
    with them while calling KJo half the time."""
    if weights is None:
        return None
    return 100.0 * (1.0 - sum(weight for action, weight in weights if action == "fold"))


def monotonicity_violations(spot_id: str, weights_by_class: dict, compared: dict | None = None):
    """Every dominating pair the spot plays the wrong way round, past the tolerance.

    A pair is skipped when either class is uncovered, since a spot behind hero's own raise
    covers only hero's arriving range. `compared` tallies, per relation, what was really
    looked at: without it a class-naming break - a rank string built the wrong way round, a
    suffix convention that stops matching the artifact's keys - compares nothing and passes."""
    violations: list[tuple] = []
    for relation, pairs in RELATIONS:
        for stronger, weaker in pairs:
            played = play_pct(weights_by_class.get(stronger))
            dominated = play_pct(weights_by_class.get(weaker))
            if played is None or dominated is None:
                continue
            if compared is not None:
                compared[relation] = compared.get(relation, 0) + 1
            if played < dominated - MONOTONICITY_TOLERANCE_PCT:
                violations.append((spot_id, stronger, weaker, played, dominated))
    return violations


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
    """A hand-built one-spot artifact: the lojack open-folded to, all 169 classes covered.

    Legitimate in every other respect, so a rejection can only be about the limp.
    """
    key = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "LJ", ())
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
        generated_at="2026-08-24T00:00:00Z",
        table_size=TABLE_SIZE,
        stack_depth_bb=STACK_DEPTH_BB,
        positions=table_positions(TABLE_SIZE),
        spots=(SpotDefinition(spot_id=key, hero_position="LJ", action_sequence=()),),
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


def solve_records(card: dict) -> list[dict]:
    """Every solve the card records, wherever on the card it chose to put them."""
    found: list[dict] = []

    def visit(value) -> None:
        if isinstance(value, dict):
            if "iterations" in value and "achieved_gap_bb" in value:
                found.append(value)
                return
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(card)
    return found


def test_the_raked_chart_is_absent_from_the_artifact_directory() -> None:
    """Deleted, because absence of a duplicate-key collision is not retirement.

    The retired chart three-bets to 8, 11 and 13.5 and opens the small blind to 3.5, while the
    export three-bets uniformly to 7.5 and opens to 2.5. So 17 of its 36 keys - every three-bet
    spot and the whole small-blind-open family - collide with nothing the new artifact
    declares. `PreflopChartLibrary` would build clean with both loaded, no check here would say
    a word, and the bot would answer every three-bet spot from raked GTO Wizard ranges while
    believing it plays the rake-free solve. Its sizing table goes too, and decision 13 keeps
    that one file, so one file is left for one chart."""
    assert not (ARTIFACT_DIR / RETIRED_CHART_NAME).exists()
    assert RETIRED_CHART_NAME not in {path.name for path in ARTIFACT_DIR.glob("*.json")}
    assert not (SIZINGS_DIR / RETIRED_CHART_NAME).exists()
    assert len(list(SIZINGS_DIR.glob("*.json"))) == 1


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
    assert len(artifact.spots) == len(library.spot_keys())


def test_the_chart_names_the_committed_export_it_was_derived_from(
    artifact: PreflopArtifact,
) -> None:
    """Provenance that resolves to the GTOpen export, not to the GTO Wizard source. Both files
    exist in this tree and both are plausible strings, so a reference that merely points at
    something readable proves nothing about which solve produced the ranges."""
    referenced = (REPO_ROOT / artifact.source.reference).resolve()

    assert referenced == COMMITTED_EXPORT_PATH.resolve()
    assert referenced.parent.name == "exports"


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
    opening = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "LJ", ())
    covered = artifact.reach_bp_for(opening, "AA")

    assert covered == reach_by_class(artifact, opening)["AA"]
    assert covered > 0

    deeper = f"t{TABLE_SIZE}/d500/LJ/rfi"
    assert deeper not in {spot.spot_id for spot in artifact.spots}
    assert artifact.reach_bp_for(deeper, "AA") is None


def test_every_committed_spot_clears_the_ruled_reach_floor(artifact: PreflopArtifact) -> None:
    """Decision 1's rule, living in the artifact instead of applied once and forgotten.

    A spot's arriving reach is the plain mean over the 169 classes, and an uncovered class
    contributes nothing. Reading it off the committed cells is what makes the selection rule
    checkable by a later reader."""
    floor = chart_derivation().REACH_FLOOR_BP

    assert floor == 200
    for spot_id, classes in artifact.arriving_reach_bp:
        arriving = sum(value for _, value in classes) / len(HAND_CLASSES)
        assert arriving >= floor, (spot_id, arriving)


def test_the_charts_reach_is_the_exports_reach_recomputed(
    artifact: PreflopArtifact, committed_export: SolverExport
) -> None:
    """The reach in the chart is the reach in the solve, class by class.

    Recomputed by walking the export directly and indexing it with GTOpen's own class
    ordering, so this is not two copies of one number agreeing with itself. It also catches the
    transposition defect: `hand_class_grid_index` and `gtopen_class_index` disagree on all but
    a handful of classes, and the wrong one swaps suited for offsuit while leaving every total
    intact. The last plan carries the weight, since a chart writing 10,000 everywhere passes
    the shallow ones."""
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
    opening = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "LJ", ())

    assert built.audit_fields.spot_count == 1
    assert built.weights_for(opening, "A5s") == (("raise", 1.0),)


def test_no_committed_spot_limps(artifact: PreflopArtifact) -> None:
    """And the committed chart satisfies the rule, which the rule alone does not prove: a
    schema rule no committed file exercises is a rule nobody has run."""
    folded_to_hero = {spot.spot_id for spot in artifact.spots if not spot.action_sequence}

    assert folded_to_hero, "the chart declares no open-folded-to spot at all"
    for spot_id in folded_to_hero:
        for name, weights in weights_by_class(artifact, spot_id).items():
            called = sum(weight for action, weight in weights if action == "call")
            assert called == 0.0, (spot_id, name, called)


def test_the_monotonicity_rule_catches_what_it_was_ruled_to_catch() -> None:
    """The helper above, shown failing and shown not over-firing. A rule driven only over a
    clean chart proves nothing about the rule, and the cases are decision 10's own: the real
    44-versus-33 pair at 27 points is caught, the noise pair at 0.08 points is not, and an
    offsuit hand played more often than its suited twin is caught."""
    real = {"44": (("fold", 0.2719), ("raise", 0.7281)), "33": (("raise", 1.0),)}
    noise = {"44": (("fold", 0.0009), ("raise", 0.9991)),
             "33": (("fold", 0.0001), ("raise", 0.9999))}
    inverted = {"T9s": (("fold", 0.9), ("raise", 0.1)), "T9o": (("fold", 0.6), ("raise", 0.4))}

    assert [entry[1:3] for entry in monotonicity_violations("spot", real)] == [("44", "33")]
    assert monotonicity_violations("spot", noise) == []
    assert [entry[1:3] for entry in monotonicity_violations("spot", inverted)] == [("T9s", "T9o")]


def test_the_committed_cells_are_monotone(artifact: PreflopArtifact) -> None:
    """Every committed spot, both relations, at decision 10's tolerance.

    Decision 2 leaves exactly one way for a violation to survive: the lojack opening 44 less
    than 33 is settled by the permitted re-solve, and if it holds after the tighter gap it is
    the solver's considered answer and ships as solved *with that recorded*. So a violation is
    admissible only at the lojack's opening spot, only on the pair ladder, and only if the
    notes say so. Nobody hand-edits a cell either way. The counter stops a clean result meaning
    nothing: an open-folded-to spot covers all 169 classes, so both relations must have got to
    compare every one of their pairs there."""
    compared: dict[str, int] = {}
    violations = [
        entry
        for spot_id, _ in artifact.action_weights
        for entry in monotonicity_violations(spot_id, weights_by_class(artifact, spot_id), compared)
    ]
    full = sum(1 for spot in artifact.spots if not spot.action_sequence)

    assert compared.get("ladder", 0) >= len(_ADJACENT_PAIRS) * full, compared
    assert compared.get("twins", 0) >= len(_SUITED_OVER_OFFSUIT) * full, compared
    if violations:
        assert len(violations) == 1, violations
        spot_id, stronger, weaker, _, _ = violations[0]
        assert spot_id == spot_key(TABLE_SIZE, STACK_DEPTH_BB, "LJ", ()), violations
        assert (stronger, weaker) in _ADJACENT_PAIRS, violations
        assert "monoton" in artifact.audit_fields.notes.lower(), (
            "a surviving violation ships as solved only when the artifact records it"
        )


def opening_pct(library: PreflopChartLibrary, position: str) -> float:
    key = f"t{TABLE_SIZE}/d{STACK_DEPTH_BB}/{position}/rfi"
    assert key in library.spot_keys(), f"the chart does not cover {position} open-folded to"
    return library.action_frequency_pct(key, "raise")


def defence_pct(library: PreflopChartLibrary, opener: str) -> float:
    key = f"t{TABLE_SIZE}/d{STACK_DEPTH_BB}/BB/{opener}:raise@2.5"
    assert key in library.spot_keys(), f"the chart does not cover the big blind versus {opener}"
    return 100.0 - library.action_frequency_pct(key, "fold")


def test_later_position_opens_wider_in_the_derived_chart(library: PreflopChartLibrary) -> None:
    """A property of the game, so it survives the conversion or the conversion broke it.

    Read through `action_frequency_pct`, which is combo-weighted, because counting hand classes
    overweights suited hands three to one and puts every published frequency out by several
    points. Decision 6 folds the jam into the raise, so an open is a raise here even where the
    solver's only aggressive offer was a shove. The small blind sits outside the order because
    whether it or the button opens widest is decided by rake rather than by structure.
    """
    opens = {position: opening_pct(library, position) for position in OPENING_ORDER}

    for tighter, wider in zip(OPENING_ORDER, OPENING_ORDER[1:], strict=False):
        assert opens[wider] > opens[tighter], opens


def test_the_big_blind_defends_more_against_whoever_opens_wider(
    library: PreflopChartLibrary,
) -> None:
    """Not a fixed order: the relation follows the opening frequencies wherever they land, so
    the widest-opening position is never covered by nothing at all. It is also the check a
    transposed hand index or a mis-assigned actor breaks first."""
    opens = {position: opening_pct(library, position) for position in OPENERS}
    defends = {position: defence_pct(library, position) for position in OPENERS}
    compared = 0

    for wider in OPENERS:
        for tighter in OPENERS:
            if wider == tighter or not opens[wider] > opens[tighter]:
                continue
            compared += 1
            assert defends[wider] > defends[tighter], (wider, tighter, opens, defends)

    assert compared >= len(OPENERS), (opens, defends)


def test_the_committed_chart_reproduces_from_the_committed_export() -> None:
    """The export is the source of truth; the chart and its sizings are its output. A hand
    edit to a derived file is a number with no origin, and `--check` is what tells one from a
    conversion nobody re-ran."""
    result = subprocess.run(
        ["python", str(CONVERTER), "--check"], cwd=REPO_ROOT, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_the_external_expectations_file_is_untouched() -> None:
    """Pinned by content, because a reference regenerated from what it checks cannot fail.

    It is a raked GTO Wizard reference and this chart is a rake-free GTOpen solve, so the
    report prints one against the other for a reader and gates on nothing. Nothing here
    asserts they agree; what is asserted is that the phase did not rewrite the one file in
    the comparison that this repo did not produce."""
    raw = EXPECTATIONS_PATH.read_bytes()
    reference = json.loads(raw)

    assert hashlib.sha256(raw).hexdigest() == EXPECTATIONS_SHA256
    assert set(reference["open_frequency_pct"]) == set(OPENERS)
    assert set(reference["big_blind_defence_pct"]) == set(OPENERS)
    assert GTOWIZARD_SOURCE_PATH.exists()


def test_the_derived_chart_is_not_the_raked_reference(
    library: PreflopChartLibrary, artifact: PreflopArtifact
) -> None:
    """The one difference between the two that is ruled rather than measured: the reference
    records the small blind limping 13.73 percent of the time, and this solve was run
    `limp: false`, so a chart agreeing with the reference here came from the wrong file."""
    reference = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))
    small_blind_open = spot_key(TABLE_SIZE, STACK_DEPTH_BB, "SB", ())

    assert reference["limp_frequency_pct"]["SB"] > 0.0
    assert library.action_frequency_pct(small_blind_open, "call") == 0.0
    assert weights_by_class(artifact, small_blind_open)


def test_the_chart_states_the_realization_bias_in_poker_terms(
    artifact: PreflopArtifact, committed_export: SolverExport
) -> None:
    """`REALIZATION-MODEL-UNDERPRICES-POSITION`, accepted and recorded rather than corrected.

    GTOpen prices postflop with a scalar realization weight rather than a solve, and the effect
    is measured: the big blind folds far more than a real postflop solve gives facing a 2.5bb
    small-blind open, closing the action in position. The closing measurement names it as a
    third explanation it cannot separate, and the big blind holds 58 of the 89 human call
    disagreements, so leaving it unnamed makes that measurement unfalsifiable. The quoted fold
    frequency is recomputed from the export rather than compared against 50.98, which came off
    the 300-iteration solve decision 2 replaces."""
    notes = artifact.audit_fields.notes
    lowered = notes.lower()
    folds = 100.0 - aggregate_frequencies(committed_export).defence_pct["SB"]
    quoted = [float(text) for text in re.findall(r"\d+\.\d+", notes)]

    assert "realization" in lowered
    assert "position" in lowered
    assert "fold" in lowered
    assert "2.5" in notes
    assert any(abs(value - folds) <= 0.05 for value in quoted), (folds, quoted)


def test_the_source_card_posts_the_ruled_game_unchanged(card: dict) -> None:
    """The re-solve is the ruled config at a tighter gap, and this is what says so.

    `config_posted` carries no target field, so "byte-identical apart from the solve target"
    excepts nothing here and equality is the whole claim. The fields spelled out are the ones
    decision 2 forbids moving, named because equality against an imported constant would pass
    just as happily if somebody widened the constant."""
    posted = card["config_posted"]

    assert posted == RULED_CONFIG
    assert posted["open_raises"] == [2.5]
    assert posted["limp"] is False
    assert posted["stack"] == 100.0
    assert posted["ante"] == 0.0
    assert len(posted["positions"]) == TABLE_SIZE
    assert (posted["rake_pct"], posted["rake_cap"]) == (0.0, 0.0)


def test_the_source_card_still_names_the_calibrated_realization_model(card: dict) -> None:
    """Decision 3's recorded bias is a statement about this model. Under the default `static`
    realization the big blind defends 99.71 percent against a small-blind open, which is not
    poker, so a re-solve that changed it would make the recorded bias false rather than
    fixed."""
    assert "realization=calibrated" in card["model"]


def test_the_source_card_records_both_solves(card: dict) -> None:
    """A reader must be able to see that the committed ranges came from the second one. The
    card's `solve` block is the committed solve and it is the deeper of the two, since
    decision 2 permits one re-solve at a tighter gap. Recording only the survivor would leave
    nothing saying a re-solve happened at all."""
    records = solve_records(card)
    committed = card["solve"]

    assert len(records) >= 2, records
    for record in records:
        for field in ("target_gap_bb", "achieved_gap_bb", "iterations", "wall_clock_seconds"):
            assert record.get(field, 0) > 0, (field, record)
    superseded = min(records, key=lambda record: record["iterations"])

    assert committed["iterations"] == max(record["iterations"] for record in records)
    assert committed["iterations"] > superseded["iterations"]
    assert committed["achieved_gap_bb"] < superseded["achieved_gap_bb"]


def test_the_re_solved_export_restamps_its_checksums(
    card: dict, committed_export: SolverExport
) -> None:
    """None of the old export's proofs is inherited, starting with its identity."""
    assert card["export_sha256"] == export_checksum(committed_export)
    assert card["export_sha256"] != SUPERSEDED_EXPORT_SHA256
    assert re.fullmatch(r"[0-9a-f]{64}", card["saved_solve"]["sha256"])
    assert card["saved_solve"]["sha256"] != SUPERSEDED_SAVE_SHA256


def test_the_determinism_proof_and_the_walk_are_re_established(
    card: dict, committed_export: SolverExport
) -> None:
    """Two claims a gate can never recompute, and one it can. The determinism result arrives
    as a structured field because nothing here can re-run a solve; the walk is different,
    since its claim covers a node count checkable against the export on disk."""
    determinism, walk = card["determinism"], card["walk"]

    assert determinism["max_divergence_bp"] == 0
    assert determinism.get("shape_differences") == 0
    assert walk["mismatches"] == 0
    assert walk["reresolved_nodes"] == committed_export.node_count


def test_the_node_counts_and_size_block_are_recomputed(
    card: dict, committed_export: SolverExport
) -> None:
    """The reconciliation and the byte budget, both against the file that is actually there.
    Exceeding the `data/artifacts` limit is a halt and a decision rather than a number to
    raise, and the card's headroom is what a later phase reads before it solves."""
    counts, size = card["node_counts"], card["size"]
    total = sum(item.stat().st_size for item in ARTIFACTS.rglob("*") if item.is_file())
    per_node = size["bytes"] / committed_export.node_count

    assert counts["exported"] == committed_export.node_count
    assert counts["solver_action_nodes"] == committed_export.node_count
    assert size["limit_bytes"] == 20 * 1024 * 1024
    assert size["bytes"] == COMMITTED_EXPORT_PATH.stat().st_size
    assert size["bytes_per_node"] == pytest.approx(per_node, abs=0.01)
    assert total < size["limit_bytes"]
    assert size["headroom_bytes"] == size["limit_bytes"] - total


def test_the_committed_card_answers_every_field_it_owes(card: dict) -> None:
    """A field left at a placeholder is the drift defect phase 09 exists to have closed."""
    assert source_card_errors(card) == []
