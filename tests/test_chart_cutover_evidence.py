"""Phase 14: the evidence that replacing the chart was a decision rather than an accident.

The companion to `tests/test_derived_chart.py`, split from it when the pair went past the
700-line cap. That file owns the committed artifact as a thing in its own right - its schema
version, its blind structure, its per-cell arriving reach, its no-limp rule and the predicate
re-derived from its own keys - and it owns the table constants, the predicate walk and the two
cell readers this file imports rather than copies, so the two halves cannot drift apart. This
file owns everything the cutover has to be defended with: that the raked chart it replaces is
gone from the tree and its sizing table with it, exactly which of the retired chart's 36 spots
survive the ruled predicate and which fourteen the bot gives up, that the source card still
posts the ruled game and the one solve phase 10 captured, that the two orderings the export was
gated on survived, and that the group dominance measure prefers the solved hand index to the
transposed one. Both files run under `pytest_derived_chart`.

**The opening frequencies are read off the export, not off the chart.** The ruled predicate
commits one opening range, the small blind's, so "later position opens wider" is a property of
the solve this chart is derived from and can no longer be a property of the chart itself. The
big-blind defence ordering is asserted over the chart, because all twenty of the big blind's
spots survive the predicate. Nothing here is checked against a number this repo remembered: the
realization measurement and the census are recomputed from the export or read off its card.
"""

from __future__ import annotations

import hashlib
import json
import subprocess

import pytest
from test_derived_chart import (
    ARTIFACT_DIR,
    ARTIFACTS,
    OPENING_ORDER,
    SB_OPEN_KEY,
    STACK_DEPTH_BB,
    TABLE_SIZE,
    live_and_invested,
    reach_by_class,
    weights_by_class,
)

from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG
from poker_training_bot.solver_artifacts.gtopen_expectations import aggregate_frequencies
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    SolverExport,
    class_combos,
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
from poker_training_bot.solver_artifacts.lookup import (
    MISS_SPOT_NOT_COVERED,
    ChartMiss,
    ChartQuery,
    PreflopArtifact,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction
from scripts.repo_paths import REPO_ROOT

SIZINGS_DIR = ARTIFACT_DIR / "sizings"
SIZING_SCHEMA_VERSION = 2
PRICED_SPOTS = 36
"""Decision 6 re-cut per hand class, and how many of the 86 price anything: 21 spots offer a
named raise and a jam, 15 a jam alone, 50 no raise at all."""
EXPECTATIONS_PATH = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"
GTOWIZARD_SOURCE_PATH = ARTIFACT_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"
RETIRED_CHART_NAME = "six_max_nl25_100bb.json"
RETIRED_CHART_PATH = f"data/artifacts/preflop/{RETIRED_CHART_NAME}"

OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")


RETIRED_SPOTS_LOST = (
    "t6/d100/LJ/rfi",
    "t6/d100/HJ/rfi",
    "t6/d100/CO/rfi",
    "t6/d100/BTN/rfi",
    "t6/d100/HJ/LJ:raise@2.5",
    "t6/d100/CO/LJ:raise@2.5",
    "t6/d100/CO/HJ:raise@2.5",
    "t6/d100/BTN/LJ:raise@2.5",
    "t6/d100/BTN/HJ:raise@2.5",
    "t6/d100/BTN/CO:raise@2.5",
    "t6/d100/SB/LJ:raise@2.5",
    "t6/d100/SB/HJ:raise@2.5",
    "t6/d100/SB/CO:raise@2.5",
    "t6/d100/SB/BTN:raise@2.5",
)
RETIRED_SPOT_WITH_NO_NODE = "t6/d100/BB/SB:call"
"""Passes the ruled predicate and still has no node to derive from: the solve is
`limp: false` and the tree holds no limp branch. Counted apart from the fourteen so the two
ledgers agree - 22 of the retired 36 pass the predicate and 21 end up covered."""

PROBE_HAND_CLASS = "AA"
"""A hand class to build a coverage probe with. Which one is immaterial: a query that reaches
a covered spot and a hand class outside hero's arriving range still refuses with
`lookup:hand-class-not-covered`, which names the spot and so still proves it is covered."""


MONOTONICITY_TOLERANCE_PCT = 1.0
"""Decision 10, ruled 2026-08-24: adjacent ranks, one percentage point, both relations."""


# The external oracle this phase must not rederive: a reference regenerated from what it
# checks cannot fail, so it is pinned by content.
EXPECTATIONS_SHA256 = "39a80b67ae9d47b86656e42092b2ed97bd5829e28b86d56087a1805e3c90e373"


# Decision 2 was re-ruled to ship-as-solved on 2026-08-24 and the contract says the phase
# runs no re-solve, so these are the checksums of the solve the chart is derived FROM rather
# than of one it replaces. A restamp here is a re-solve that nobody ruled and that decision 2
# requires five separate proofs for.
COMMITTED_EXPORT_SHA256 = "1c9e383df22e91ee1103e846077371d9b47731c10ab54110bde6d0905271a739"


COMMITTED_SAVE_SHA256 = "64d8729a30f758f24e713976ac529bab64c741d22af4b68bdeea424864f27ab5"


COMMITTED_SOLVE_ITERATIONS = 300


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


_PAIRS_HIGH_TO_LOW = tuple(f"{rank}{rank}" for rank in HIGH_TO_LOW_RANKS)


GROUPS = {
    "pairs, 13 single ranks": tuple((pair,) for pair in _PAIRS_HIGH_TO_LOW),
    "pairs, 4 bands": (
        _PAIRS_HIGH_TO_LOW[:3],
        _PAIRS_HIGH_TO_LOW[3:6],
        _PAIRS_HIGH_TO_LOW[6:9],
        _PAIRS_HIGH_TO_LOW[9:],
    ),
    "pairs, 3 bands": (
        _PAIRS_HIGH_TO_LOW[:4],
        _PAIRS_HIGH_TO_LOW[4:8],
        _PAIRS_HIGH_TO_LOW[8:],
    ),
    "pairs, 2 bands": (_PAIRS_HIGH_TO_LOW[:6], _PAIRS_HIGH_TO_LOW[6:]),
    "suited rows": tuple(
        tuple(f"{high}{low}s" for low in HIGH_TO_LOW_RANKS[index + 1 :])
        for index, high in enumerate(HIGH_TO_LOW_RANKS[:-1])
    ),
}
"""Every partition decision 10's group form could be read as. The item ruled "each pair band
and each suited row" without fixing the bands, so all of them are measured rather than one
chosen - choosing the partition that produces the smallest number is picking a threshold to
go green, which is the move the contract forbids for the selection rule and which is no more
honest here."""


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


def group_play_pct(weights_by_class: dict, reach_by_class: dict, group, transposed: bool):
    """One group's play frequency, combo-weighted over hero's arriving range.

    `transposed` is the counterfactual: the artifact a converter produces when it indexes the
    export payload by the grid ordering rather than by GTOpen's own, which is the
    suited-for-offsuit swap `hand_class_grid_index` and `gtopen_class_index` disagree about.
    Both the weights and the reach come from the swapped class, because a converter reads them
    with the same index and would get both wrong together - taking only the weights would
    compare a full range against a sparse one and measure the sparsity instead of the swap.
    The swap leaves every total intact, so a check that cannot tell the two readings apart
    cannot catch it.
    """
    as_gtopen_stores_them = tuple(sorted(HAND_CLASSES, key=gtopen_class_index))
    total = weighted = 0.0
    for name in group:
        # Row position `grid_index(name)` in GTOpen's own ordering holds a different class,
        # which is exactly what a converter indexing the payload by the grid ordering reads.
        source = as_gtopen_stores_them[hand_class_grid_index(name)] if transposed else name
        played = play_pct(weights_by_class.get(source))
        if played is None or source not in reach_by_class:
            continue
        weight = class_combos(name) * reach_by_class[source]
        if not weight:
            continue
        total += weight
        weighted += weight * played
    return weighted / total if total else None


def group_violating_spots(artifact: PreflopArtifact, groups, transposed: bool) -> int:
    """How many committed spots play some group less often than the group below it."""
    bad = 0
    for spot_id, _ in artifact.action_weights:
        cells = weights_by_class(artifact, spot_id)
        reach = reach_by_class(artifact, spot_id)
        values = [group_play_pct(cells, reach, group, transposed) for group in groups]
        values = [value for value in values if value is not None]
        if any(
            higher < lower - MONOTONICITY_TOLERANCE_PCT
            for higher, lower in zip(values, values[1:], strict=False)
        ):
            bad += 1
    return bad


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


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True)


def retired_chart_from_history() -> dict:
    """The retired chart, read out of git history rather than out of the tree.

    Decision 7's arrangement, and the only one available to this file after stage 6: the file
    is deleted, so a test that needs its 36 keys has to go to the history for them. The commit
    is located rather than pinned as a constant, because a hardcoded sha in a frozen test is a
    number that stops resolving the first time somebody rebases the lane.
    """
    revisions = git("rev-list", "HEAD", "--", RETIRED_CHART_PATH).stdout.split()
    assert revisions, f"git history holds no {RETIRED_CHART_PATH}"
    for commit in revisions:
        found = git("cat-file", "-e", f"{commit}:{RETIRED_CHART_PATH}").returncode == 0
        if found:
            return json.loads(git("show", f"{commit}:{RETIRED_CHART_PATH}").stdout)
    raise AssertionError(f"no commit in history carries {RETIRED_CHART_PATH}")


def export_opening_pct(export: SolverExport) -> dict[str, float]:
    """Each seat's opening frequency, read off the solve rather than off the chart.

    The chart holds one opening range, so "later position opens wider" cannot be a property of
    the artifact any more. It remains a property of the export the artifact is derived from,
    which is where the ordering was gated at phase 10 and where it still has to hold: a
    conversion that mis-assigned an actor or transposed a hand index would break the same
    check. `aggregate_frequencies` is the export's own reader, combo-weighted and conditioned
    on the arriving range.
    """
    return dict(aggregate_frequencies(export).opening_pct)


def defence_pct(library: PreflopChartLibrary, opener: str) -> float:
    key = f"t{TABLE_SIZE}/d{STACK_DEPTH_BB}/BB/{opener}:raise@2.5"
    assert key in library.spot_keys(), f"the chart does not cover the big blind versus {opener}"
    return 100.0 - library.action_frequency_pct(key, "fold")


def test_the_raked_chart_is_absent_from_the_artifact_directory() -> None:
    """Deleted, because absence of a duplicate-key collision is not retirement.

    The retired chart three-bets to 8, 11 and 13.5 and opens the small blind to 3.5, while the
    export three-bets uniformly to 7.5 and opens to 2.5. So 17 of its 36 keys - every three-bet
    spot and the whole small-blind-open family - collide with nothing the new artifact declares.
    `PreflopChartLibrary` would build clean with both loaded, no check would say a word, and the
    bot would answer every three-bet spot from raked GTO Wizard ranges while believing it plays
    the rake-free solve. Its sizing table goes too, so one file is left for one chart."""
    assert not (ARTIFACT_DIR / RETIRED_CHART_NAME).exists()
    assert RETIRED_CHART_NAME not in {path.name for path in ARTIFACT_DIR.glob("*.json")}
    assert not (SIZINGS_DIR / RETIRED_CHART_NAME).exists()
    assert len(list(SIZINGS_DIR.glob("*.json"))) == 1


def test_the_committed_sizing_file_is_at_the_per_class_schema() -> None:
    """Decision 6 as re-cut on 2026-08-26: one weight per price per *hand class*.
    Version 1 held a bare float per spot and version 2 a list per class, so the version is what
    a reader checks before it trusts the indexing: a v1 loader on a v2 file reads a mapping
    where it expects a number, a v2 loader on a v1 file reads a float as a mapping of classes.
    The shape is read off the file rather than through `PreflopSizingTable`, whose loader is
    stage 6's and, if it accepted either shape, would make its own version claim vacuous.
    """
    paths = sorted(SIZINGS_DIR.glob("*.json"))
    assert len(paths) == 1, paths
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    sizes = payload["raise_to_bb"]

    assert payload["schema_version"] == SIZING_SCHEMA_VERSION
    assert len(sizes) == PRICED_SPOTS
    for key, spot in sizes.items():
        assert isinstance(spot, dict) and spot, key
        for hand_class, entries in spot.items():
            cell = (key, hand_class)
            assert hand_class in HAND_CLASSES, cell
            assert isinstance(entries, list) and 1 <= len(entries) <= 2, cell
            assert all(set(entry) == {"to_bb", "weight"} for entry in entries), cell
            prices = [entry["to_bb"] for entry in entries]
            assert prices == sorted(prices), cell
            assert all(entry["weight"] > 0.0 for entry in entries), cell
            assert sum(entry["weight"] for entry in entries) == pytest.approx(1.0), cell


def test_the_retired_chart_is_not_a_subset_of_what_replaces_it() -> None:
    """The claim every stage-4 document made and the terminal-clean predicate falsified.

    "All 36 spots of the retired chart are heads-up, so nothing the bot answers today is
    lost" was verified by reading `action_sequence` values, which is a history reading. Under
    the ruled predicate 22 of the 36 pass and 14 do not, and 21 of those 22 end up covered -
    the twenty-second is the limped pot the solve has no branch for. So the cutover gains 65
    spots and gives up 14, four opening ranges among them. Gained is the committed count less
    the number carried over, 86 - 21, and not 86 - 22: the limped pot is refused and is in
    neither set. Read out of git history because the file is deleted, and asserted spot by spot
    rather than as a count, because a count of 14 with the wrong 14 in it is the same
    arithmetic and a different chart.
    """
    retired = retired_chart_from_history()
    spots = retired["spots"]
    lost = []
    passing = []
    for spot in spots:
        entries = tuple(
            PreflopAction(entry["position"], entry["action"], entry.get("size_bb"))
            for entry in spot["action_sequence"]
        )
        live, invested = live_and_invested(spot["hero_position"], entries)
        (passing if invested <= 1 and live <= 2 else lost).append(spot["spot_id"])

    assert len(spots) == 36
    assert sorted(lost) == sorted(RETIRED_SPOTS_LOST)
    assert len(passing) == 22
    assert RETIRED_SPOT_WITH_NO_NODE in passing


def test_the_retired_spots_that_survive_the_predicate_are_covered_bar_the_limp(
    library: PreflopChartLibrary,
) -> None:
    """21 of the retired 36 stay covered, and the twenty-second is the limped pot.

    **Asked the way the bot asks it, and that is the whole of why 21 is the number.** The
    retired chart's keys carry GTO Wizard's prices - it opens the small blind to 3.5 and
    three-bets to 8, 11 and 13.5 - while the derived chart holds only 2.5, 7.5, 22.5 and 100.
    Measured, exactly five of the retired chart's 36 keys exist verbatim among the 86, so raw
    membership in `spot_keys()` answers 5 and answers a different question. What makes 21 true
    is phase 12's ruling 8: the lookup normalises an observed price to the nearest one the
    loaded artifacts declare for that exact line, so each survivor is put to `library.lookup`
    as a `ChartQuery` built from its own `hero_position` and `action_sequence`, and the 21
    land on 21 distinct committed keys. Both counts are asserted here so that nobody "fixes"
    this back to set membership and gets a green 5 that reads like coverage.

    Coverage is read off the refusal code rather than off one hand class, because a spot
    behind hero's own raise covers only hero's arriving range: anything but
    `lookup:spot-not-covered` means the chart holds that cell. `BB/SB:call` passes the
    predicate and has no node to derive from, because the solve is `limp: false` and the tree
    holds no limp branch. That is `CHART-CANNOT-ANSWER-A-LIMPED-POT` and it is counted here
    so the two ledgers agree, and it is the baseline the contract's refusal-rate criterion is
    stated against: the rate rises on the fourteen the predicate drops plus this one, and a
    rise anywhere else is a defect rather than the cost of the ruling.
    """
    retired = retired_chart_from_history()
    covered = set(library.spot_keys())
    survivors = []
    for spot in retired["spots"]:
        entries = tuple(
            PreflopAction(entry["position"], entry["action"], entry.get("size_bb"))
            for entry in spot["action_sequence"]
        )
        live, invested = live_and_invested(spot["hero_position"], entries)
        if invested <= 1 and live <= 2:
            survivors.append((spot["spot_id"], spot["hero_position"], entries))

    answered: dict[str, str] = {}
    refused = []
    for spot_id, hero, entries in survivors:
        result = library.lookup(
            ChartQuery(TABLE_SIZE, STACK_DEPTH_BB, hero, entries, PROBE_HAND_CLASS)
        )
        if isinstance(result, ChartMiss) and result.code == MISS_SPOT_NOT_COVERED:
            refused.append(spot_id)
            continue
        assert result.spot_key is not None, spot_id
        answered[spot_id] = result.spot_key

    assert len(answered) == 21
    assert len(set(answered.values())) == 21, answered
    assert refused == [RETIRED_SPOT_WITH_NO_NODE]
    assert len([spot_id for spot_id, _, _ in survivors if spot_id in covered]) == 5
    for key in RETIRED_SPOTS_LOST:
        assert key not in covered, key


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


def test_the_per_cell_relations_are_measured_over_every_committed_spot(
    artifact: PreflopArtifact,
) -> None:
    """Decision 10 re-ruled: the two relations are measured per cell and gate nothing.

    Taylor read the grids and ruled the splits correct - among near-indifferent hands every
    split has the same EV, so a per-cell dominance gate rejects correct play, and the small
    blind facing a button open playing 22 at 99.94 percent and 44 at 0.07 is the case it was
    ruled against. What survives as a gate is that the measurement was really taken: the one
    folded-to-hero spot covers all 169 classes, so both relations must have compared every one
    of their pairs there. A run that compared nothing would otherwise publish a clean sheet.
    """
    compared: dict[str, int] = {}
    for spot_id, _ in artifact.action_weights:
        monotonicity_violations(spot_id, weights_by_class(artifact, spot_id), compared)
    full = sum(1 for spot in artifact.spots if not spot.action_sequence)

    assert full == 1
    assert compared.get("ladder", 0) >= len(_ADJACENT_PAIRS) * full, compared
    assert compared.get("twins", 0) >= len(_SUITED_OVER_OFFSUIT) * full, compared


def test_the_group_dominance_measure_prefers_the_solved_hand_index_to_the_transposed_one(
    artifact: PreflopArtifact,
) -> None:
    """What decision 10's group form is actually for, and the half of it that measured true.

    The item ruled the aggregate in to keep a real check on a transposed hand index or a
    mis-assigned actor without asserting a per-cell order the solve does not owe. Over the
    5,626 it failed at exactly that: the suited-versus-offsuit aggregate flagged 2,007 nodes
    as solved against 818 transposed, scoring the *wrong* index mapping as the better one,
    which is worse than having no check. Over the 86 the discrimination runs the right way for
    every partition the ruling could be read as, and that is what is asserted here - the
    ordering between the two mappings rather than a violation count, because a count fixes a
    partition and choosing the partition that reads smallest is picking a number to go green.

    Decision 10's literal group form does **not** hold over the 86 on any partition, so this
    file does not gate on it and the phase halts on it rather than freezing a gate it has not
    seen pass. Measured over the committed set at the ruled one-point tolerance, the number of
    spots violating the group order is 51 on single pair ranks, 17 on four bands, 10 on three,
    1 on two, and 41 on the suited rows. Full measurement in the stage-4 review note.
    """
    ordered = {}
    for label, groups in GROUPS.items():
        solved = group_violating_spots(artifact, groups, transposed=False)
        transposed = group_violating_spots(artifact, groups, transposed=True)
        ordered[label] = (solved, transposed)

    assert len(ordered) == len(GROUPS)
    for label, (solved, transposed) in ordered.items():
        assert solved < transposed, (
            f"{label}: the measure flags {solved} spots as solved and {transposed} with suited"
            " and offsuit transposed, so it does not prefer the solved index mapping"
        )
    assert any(transposed > 0 for _, transposed in ordered.values())


def test_later_position_opens_wider_in_the_solve_the_chart_came_from(
    committed_export: SolverExport,
) -> None:
    """A property of the game, so it survives the conversion or the conversion broke it -
    except that after the cutover the chart no longer holds four of the five opening ranges,
    so the claim is asserted where it still lives. That is a narrowing and it is stated as one:
    the ordering is evidence about the solve, and what the chart inherits from it is the
    defence ordering below, which is measured over the artifact."""
    opens = export_opening_pct(committed_export)

    assert set(opens) >= set(OPENERS)
    for tighter, wider in zip(OPENING_ORDER, OPENING_ORDER[1:], strict=False):
        assert opens[wider] > opens[tighter], opens


def test_the_big_blind_defends_more_against_whoever_opens_wider(
    library: PreflopChartLibrary, committed_export: SolverExport
) -> None:
    """Not a fixed order: the relation follows the opening frequencies wherever they land, so
    the widest-opening position is never covered by nothing at all. It is also the check a
    transposed hand index or a mis-assigned actor breaks first, and it survives the predicate
    change intact - no big-blind spot is among the 24, because the big blind closes the action
    and every one of its spots is therefore terminal-clean."""
    opens = export_opening_pct(committed_export)
    defends = {position: defence_pct(library, position) for position in OPENERS}
    compared = 0

    for wider in OPENERS:
        for tighter in OPENERS:
            if wider == tighter or not opens[wider] > opens[tighter]:
                continue
            compared += 1
            assert defends[wider] > defends[tighter], (wider, tighter, opens, defends)

    assert compared >= len(OPENERS), (opens, defends)


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
    `limp: false`, so a chart agreeing with the reference here came from the wrong file. It is
    also the one opening range both files hold, which is what makes the comparison possible at
    all after the predicate dropped the other four."""
    reference = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    assert reference["limp_frequency_pct"]["SB"] > 0.0
    assert library.action_frequency_pct(SB_OPEN_KEY, "call") == 0.0
    assert weights_by_class(artifact, SB_OPEN_KEY)


def test_the_source_card_posts_the_ruled_game_unchanged(card: dict) -> None:
    """Decision 2 ships as solved and no re-solve is run, so this is the config that produced
    the committed ranges rather than one a re-solve had to match.

    The fields spelled out are the ones decision 2 forbids moving, named because equality
    against an imported constant would pass just as happily if somebody widened the constant.
    """
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
    poker, so a card that changed it would make the recorded bias false rather than fixed."""
    assert "realization=calibrated" in card["model"]


def test_the_committed_solve_is_the_one_phase_ten_captured_and_no_re_solve_replaced_it(
    card: dict, committed_export: SolverExport
) -> None:
    """Decision 2 was re-ruled to ship-as-solved, so the absence of a re-solve is the claim.

    The first ruling was re-solve-to-a-tighter-gap, on the argument that the lojack opening 44
    at 72.81 percent was an unfinished cell. Taylor read the grids and re-ruled: dominance
    constrains EV rather than frequency, and a solver at indifference may put the frequency
    anywhere, so the split is its considered answer. A re-solve remains permitted and produces
    a new export, which would carry five separate obligations of its own - a determinism proof,
    a walk, a node reconciliation, two restamped checksums and a recomputed size block. This
    test is what makes a silent re-solve loud: one solve on the card, at the iteration count
    phase 10 captured, and the export and save checksums unmoved.
    """
    records = solve_records(card)
    committed = card["solve"]

    assert len(records) == 1, records
    assert committed["iterations"] == COMMITTED_SOLVE_ITERATIONS
    assert committed["achieved_gap_bb"] < committed["target_gap_bb"]
    assert card["export_sha256"] == export_checksum(committed_export)
    assert card["export_sha256"] == COMMITTED_EXPORT_SHA256
    assert card["saved_solve"]["sha256"] == COMMITTED_SAVE_SHA256


def test_the_determinism_proof_and_the_walk_still_hold(
    card: dict, committed_export: SolverExport
) -> None:
    """Phase 10's two proofs, which the cutover inherits because the export is unchanged.

    The determinism result arrives as a structured field because nothing here can re-run a
    solve; the walk is different, since its claim covers a node count checkable against the
    export on disk. Either one restated against a different node count is a re-solve nobody
    declared."""
    determinism, walk = card["determinism"], card["walk"]

    assert determinism["max_divergence_bp"] == 0
    assert determinism.get("shape_differences") == 0
    assert walk["mismatches"] == 0
    assert walk["reresolved_nodes"] == committed_export.node_count


def test_the_node_counts_and_size_block_are_recomputed(
    card: dict, committed_export: SolverExport
) -> None:
    """The reconciliation and the byte budget, both against the file that is actually there.

    The cap stopped binding when the predicate changed - 86 spots are two orders of magnitude
    under it - but the rule did not change with it: exceeding the `data/artifacts` limit is a
    halt and a decision rather than a number to raise, and the card's headroom is what a later
    phase reads before it solves. Deleting the retired chart and writing a smaller one both
    move the directory total, so the block is restamped or this fails."""
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
