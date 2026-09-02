"""Phase 14: the evidence that replacing the chart was a decision rather than an accident.

The companion to `tests/test_derived_chart.py`, split from it at the 700-line cap. That file
owns the committed artifact in its own right and the table constants, predicate walk and cell
readers this file imports rather than copies. This file owns what the cutover has to be defended
with: the raked chart gone from the tree with its sizing table, which of its 36 spots survive and
which the bot gives up, the card posting the ruled game and the one re-solve decision 14 ordered,
the two gated orderings, and the dominance measure.

**Re-cut at stage 4 twice on 2026-09-01.** Decision 14 re-solved at `add_allin: false`, so what
is asserted is one re-solve at the ruled target carrying the five obligations one owes. Taylor
then withheld the fifteen jam-facing spots and, the same evening, the fifteen three-bet-facing
ones, cutting the committed set to **6**. Measured against the retired chart that is 6 carried
over of its 36, so **the cutover gains nothing and gives up twenty-nine spots plus the limped
pot**: four opening ranges, the fifteen three-bet spots the retired chart answered, and ten more
the predicate never wanted. And the group dominance ladder stopped gating, its verdict tracking
set composition rather than the hand index. **The only gated range check in the phase is the
per-cell measure over spot partitions**, in `tests/test_derived_chart_report_validators.py`,
which since the second ruling carries two counterfactual arms; the five ladders here are
published for a human.

**The opening frequencies are read off the export, not the chart.** The committed set holds one
opening range, so "later position opens wider" is a property of the solve rather than of the
chart; the defence ordering is asserted over the chart.
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
COMMITTED_SPOTS = 6
PRICED_SPOTS = 6
"""How many of the 6 price anything: all of them. The fifteen that offered call and fold only -
hero facing a five-bet jam, the last raise already in - were withheld on 2026-09-01, so the
unpriced family is gone and the table covers the committed set exactly."""
RULED_PRICES = (2.5, 7.5)
"""Every price the committed set offers. Hero's own 100 is not among them, five-betting being
legal only facing a four-bet and every four-bet-facing spot withheld; nor is 22.5, which only
the withheld three-bet-facing spots ever quoted."""
EXPECTATIONS_PATH = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"
GTOWIZARD_SOURCE_PATH = ARTIFACT_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"
RETIRED_CHART_NAME = "six_max_nl25_100bb.json"
RETIRED_CHART_PATH = f"data/artifacts/preflop/{RETIRED_CHART_NAME}"

OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")


RETIRED_SPOTS_LOST = (
    "t6/d100/LJ/rfi", "t6/d100/HJ/rfi", "t6/d100/CO/rfi", "t6/d100/BTN/rfi",
    "t6/d100/HJ/LJ:raise@2.5", "t6/d100/CO/LJ:raise@2.5", "t6/d100/CO/HJ:raise@2.5",
    "t6/d100/BTN/LJ:raise@2.5", "t6/d100/BTN/HJ:raise@2.5", "t6/d100/BTN/CO:raise@2.5",
    "t6/d100/SB/LJ:raise@2.5", "t6/d100/SB/HJ:raise@2.5", "t6/d100/SB/CO:raise@2.5",
    "t6/d100/SB/BTN:raise@2.5",
)
RETIRED_SPOTS_CARRIED_OVER = 6
RETIRED_SPOTS_WITHHELD = 15
"""Retired spots that pass decision 1's predicate and are then withheld anyway: every one is
hero facing a three-bet, which is what the second 2026-09-01 ruling took. GTO Wizard's 36 stop
there, so no retired spot lands on a four-bet or jam-facing key and those two withholdings cost
this ledger nothing."""
SPOTS_GAINED = COMMITTED_SPOTS - RETIRED_SPOTS_CARRIED_OVER
"""Zero, derived rather than typed. The three withholdings between them cut the committed set to
exactly the 6 spots the retired chart already answered, so the cutover buys no new coverage -
what it buys is that the 6 are rake-free, correctly priced and re-solved, and what it costs is
twenty-nine spots plus the limped pot."""
RAISES_FACED_WHEN_WITHHELD = (2, 3, 4)
"""Two raises is hero facing a three-bet, taken by the second 2026-09-01 ruling; three is a
four-bet, taken by decision 20; four is the jam, taken by the first. No survivor may land on
any of them."""
RETIRED_SPOT_WITH_NO_NODE = "t6/d100/BB/SB:call"
"""Passes the ruled predicate and still has no node to derive from: the solve is `limp: false`
and the tree holds no limp branch. Counted apart from the fourteen so the two ledgers agree."""

PROBE_HAND_CLASS = "AA"
"""Which class is immaterial: a query reaching a covered spot with a class outside hero's
arriving range still refuses with `lookup:hand-class-not-covered`, naming the spot."""

MONOTONICITY_TOLERANCE_PCT = 1.0
"""Decision 10, ruled 2026-08-24: adjacent ranks, one percentage point, both relations."""

# The external oracle this phase must not rederive: a reference regenerated from what it
# checks cannot fail, so it is pinned by content.
EXPECTATIONS_SHA256 = "39a80b67ae9d47b86656e42092b2ed97bd5829e28b86d56087a1805e3c90e373"

# The re-solve decision 14 ruled, pinned by content: the checksums are what make a SECOND one
# loud, any further restamp being a solve nobody ruled with five obligations of its own. The
# superseded `add_allin: true` build checksummed 1c9e383d and its save 64d8729a.
COMMITTED_EXPORT_SHA256 = "f7182f4bbcc080c7715d8195cd0552d4604ec9856c8d7d64cd5a52483e0949e7"
COMMITTED_SAVE_SHA256 = "1777810729942cfda30b10a1189ed5a910a5ce4f6c383f4664fd66a222312027"

COMMITTED_ACTION_NODES = 33_969
"""What the re-sourced tree holds, and what the census has to sum to."""

SOLVE_TARGET_GAP_BB = 0.00016
SOLVE_ITERATION_CAP = 2_000
COMMITTED_SOLVE_ITERATIONS = 1_900
"""The ruled target first met at iteration 1,900 of a 2,000 cap, so the cap **nearly binds** - the
fact worth freezing rather than the achieved gap, a tighter target running out of iterations and
leaving `achieved < target` false."""


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
violations a node and its top hits are correct poker - the lojack opens 76s always, T6s never."""

_PAIRS_HIGH_TO_LOW = tuple(f"{rank}{rank}" for rank in HIGH_TO_LOW_RANKS)

GROUPS = {
    "pairs, 13 single ranks": tuple((pair,) for pair in _PAIRS_HIGH_TO_LOW),
    "pairs, 4 bands": tuple(_PAIRS_HIGH_TO_LOW[start : start + 3] for start in (0, 3, 6, 9)),
    "pairs, 3 bands": tuple(_PAIRS_HIGH_TO_LOW[start : start + 4] for start in (0, 4, 8)),
    "pairs, 2 bands": (_PAIRS_HIGH_TO_LOW[:6], _PAIRS_HIGH_TO_LOW[6:]),
    "suited rows": tuple(
        tuple(f"{high}{low}s" for low in HIGH_TO_LOW_RANKS[index + 1 :])
        for index, high in enumerate(HIGH_TO_LOW_RANKS[:-1])
    ),
}
"""Every partition decision 10's group form could be read as: it ruled "each pair band and each
suited row" without fixing the bands, so all are measured rather than one chosen."""


def play_pct(weights) -> float | None:
    """How often a hand is played rather than folded, the only quantity decision 10's relations
    are monotone in: a per-action rule is false wherever hero can call."""
    if weights is None:
        return None
    return 100.0 * (1.0 - sum(weight for action, weight in weights if action == "fold"))


def monotonicity_violations(spot_id: str, weights_by_class: dict, compared: dict | None = None):
    """Every dominating pair the spot plays the wrong way round, past the tolerance. A pair is
    skipped when either class is uncovered; `compared` tallies per relation what was looked at,
    without which a class-naming break compares nothing and passes."""
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

    `transposed` is the counterfactual: the artifact a converter produces indexing the payload by
    the grid ordering rather than GTOpen's own - **not** either counterfactual the gate in
    `tests/test_derived_chart_report_validators.py` uses. Both the weights and the reach come
    from the swapped class, a converter reading them with one index getting both wrong."""
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
    """How many committed spots play a group less often than the group below it."""
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
    """Every solve the card records, wherever it put them."""
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
    """The retired chart, read out of git history rather than the tree - decision 7's
    arrangement, and the only one left once stage 6 deletes the file. The commit is located
    rather than pinned: a hardcoded sha stops resolving the first time somebody rebases."""
    revisions = git("rev-list", "HEAD", "--", RETIRED_CHART_PATH).stdout.split()
    assert revisions, f"git history holds no {RETIRED_CHART_PATH}"
    for commit in revisions:
        found = git("cat-file", "-e", f"{commit}:{RETIRED_CHART_PATH}").returncode == 0
        if found:
            return json.loads(git("show", f"{commit}:{RETIRED_CHART_PATH}").stdout)
    raise AssertionError(f"no commit in history carries {RETIRED_CHART_PATH}")


def retired_split() -> tuple[list[tuple[str, str, tuple]], list[str]]:
    """The retired 36 put through the ruled predicate - one walk for both ledgers below, so
    what passes and what stays covered cannot be two readings of the same file."""
    survivors: list[tuple[str, str, tuple]] = []
    lost: list[str] = []
    for spot in retired_chart_from_history()["spots"]:
        entries = tuple(
            PreflopAction(entry["position"], entry["action"], entry.get("size_bb"))
            for entry in spot["action_sequence"]
        )
        live, invested = live_and_invested(spot["hero_position"], entries)
        if invested <= 1 and live <= 2:
            survivors.append((spot["spot_id"], spot["hero_position"], entries))
        else:
            lost.append(spot["spot_id"])
    return survivors, lost


def export_opening_pct(export: SolverExport) -> dict[str, float]:
    """Each seat's opening frequency, read off the solve rather than the chart. The chart holds
    one opening range, so "later position opens wider" is no longer a property of the artifact.
    It remains one of the export, where the ordering was gated at phase 10 and where a
    mis-assigned actor or a transposed hand index still breaks it."""
    return dict(aggregate_frequencies(export).opening_pct)


def defence_pct(library: PreflopChartLibrary, opener: str) -> float:
    key = f"t{TABLE_SIZE}/d{STACK_DEPTH_BB}/BB/{opener}:raise@2.5"
    assert key in library.spot_keys(), f"the chart does not cover the big blind versus {opener}"
    return 100.0 - library.action_frequency_pct(key, "fold")


def test_the_raked_chart_is_gone_and_the_sizing_file_left_is_at_the_per_class_schema() -> None:
    """Deleted, because absence of a duplicate-key collision is not retirement; and decision 6's
    2026-08-26 re-cut, one weight per price per *hand class*, on the one sizing file left.
    The retired chart three-bets to 8, 11 and 13.5 and opens the small blind to 3.5 while the
    export three-bets to 7.5 and opens to 2.5, so 31 of its 36 keys collide with nothing the new
    artifact declares and only five exist verbatim: the library would build clean with both
    loaded and the bot would answer every three-bet spot from raked ranges.

    Version 1 held a bare float per spot and version 2 a list per class, so the version is what a
    reader checks before trusting the indexing; the shape is read off the file rather than
    through `PreflopSizingTable`, whose loader would make its version claim vacuous. **The
    two-price case is unexercised and labelled rather than counted as a pass** - the schema holds
    a list because a spot may offer two prices and 0 of the 6 do. The last assertion makes that
    a measurement, so a later solve turns it red.
    """
    assert not (ARTIFACT_DIR / RETIRED_CHART_NAME).exists()
    assert RETIRED_CHART_NAME not in {path.name for path in ARTIFACT_DIR.glob("*.json")}
    assert not (SIZINGS_DIR / RETIRED_CHART_NAME).exists()

    paths = sorted(SIZINGS_DIR.glob("*.json"))
    assert len(paths) == 1, paths
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    sizes = payload["raise_to_bb"]
    widths = set()

    assert payload["schema_version"] == SIZING_SCHEMA_VERSION
    assert len(sizes) == PRICED_SPOTS == COMMITTED_SPOTS
    for key, spot in sizes.items():
        assert isinstance(spot, dict) and spot, key
        for hand_class, entries in spot.items():
            cell = (key, hand_class)
            assert hand_class in HAND_CLASSES, cell
            assert isinstance(entries, list) and 1 <= len(entries) <= 2, cell
            assert all(set(entry) == {"to_bb", "weight"} for entry in entries), cell
            prices = [entry["to_bb"] for entry in entries]
            assert prices == sorted(prices), cell
            assert set(prices) <= set(RULED_PRICES), cell
            assert all(entry["weight"] > 0.0 for entry in entries), cell
            assert sum(entry["weight"] for entry in entries) == pytest.approx(1.0), cell
            widths.add(len(entries))

    assert widths == {1}, (
        "a committed spot now offers hero two prices at one hand class, so decision 6's"
        f" two-price branch is no longer vacuous and the label above is out of date: {widths}"
    )


def test_the_retired_chart_is_not_a_subset_of_what_replaces_it() -> None:
    """The claim every stage-4 document made and the terminal-clean predicate falsified.
    "All 36 spots of the retired chart are heads-up, so nothing the bot answers today is lost"
    was verified by reading `action_sequence` values, which is a history reading. Under the ruled
    predicate 22 of the 36 pass and 14 do not; of the 22, six end up covered, fifteen are
    withheld as three-bet-facing and the twenty-second is the limped pot the solve has no branch
    for. So the cutover gives up 29 spots and the limp, four opening ranges among them, and gains
    6 - 6 = **nothing**. Read out of git history because the file is deleted, and asserted spot
    by spot rather than as a count, because a count of 14 with the wrong 14 in it is the same
    arithmetic and a different chart."""
    survivors, lost = retired_split()
    passing = [spot_id for spot_id, _, _ in survivors]

    assert len(passing) + len(lost) == 36
    assert sorted(lost) == sorted(RETIRED_SPOTS_LOST)
    assert len(passing) == 22
    assert RETIRED_SPOT_WITH_NO_NODE in passing


def test_the_retired_spots_that_survive_are_covered_or_withheld_bar_the_limp(
    library: PreflopChartLibrary,
) -> None:
    """6 of the retired 36 stay covered; 15 more pass the predicate and are withheld, and the
    twenty-second survivor is the limped pot.

    **Asked the way the bot asks it, which is the whole of why 6 is the number.** The retired
    chart opens the small blind to 3.5 and three-bets to 8, 11 and 13.5 while the derived chart
    holds 2.5 and 7.5, so exactly five keys exist verbatim and raw membership in `spot_keys()`
    answers a different question. Phase 12's ruling 8 makes 6 true: the lookup normalises an
    observed price to the nearest one declared for that line, so each survivor goes to
    `library.lookup` as a `ChartQuery` and the 6 land on 6 distinct keys.

    Coverage is read off the refusal code rather than one hand class, a spot behind hero's own
    raise covering only hero's arriving range. `BB/SB:call` passes the predicate with no node to
    derive from, the solve being `limp: false`; that is `CHART-CANNOT-ANSWER-A-LIMPED-POT`.

    **The three withholdings cost this ledger fifteen spots, and which fifteen is measured
    rather than assumed.** GTO Wizard's 36 stop at hero facing a three-bet, so the retired chart
    has no four-bet-facing key and no jam-facing one and those two withholdings cost nothing
    here; the third takes every three-bet-facing spot, and the retired chart has fifteen of them.
    They are asserted as a set beside the carried-over set, fifteen matching fifteen by size
    while differing by membership being the shape a wrong withholding takes. The gain side is
    still empty: the 6 answered keys are the whole committed set.
    """
    covered = set(library.spot_keys())
    survivors, _ = retired_split()
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

    withheld = [key for key in refused if key != RETIRED_SPOT_WITH_NO_NODE]

    assert len(answered) == RETIRED_SPOTS_CARRIED_OVER
    assert len(set(answered.values())) == RETIRED_SPOTS_CARRIED_OVER, answered
    assert RETIRED_SPOT_WITH_NO_NODE in refused
    assert len(withheld) == RETIRED_SPOTS_WITHHELD, withheld
    assert all(key.count(":raise@") == 2 for key in withheld), withheld
    assert set(withheld).isdisjoint(answered)
    assert len([spot_id for spot_id, _, _ in survivors if spot_id in covered]) == 5
    for key in RETIRED_SPOTS_LOST:
        assert key not in covered, key
    for spot_id, landed in answered.items():
        faced = landed.split("/")[3]
        raises = 0 if faced == "rfi" else sum(1 for e in faced.split(",") if ":raise@" in e)
        assert raises not in RAISES_FACED_WHEN_WITHHELD, (spot_id, landed)
    assert set(answered.values()) == covered, "the carried-over keys are not the committed set"
    assert len(covered) == COMMITTED_SPOTS
    assert COMMITTED_SPOTS - RETIRED_SPOTS_CARRIED_OVER == SPOTS_GAINED == 0


def test_the_per_cell_relations_are_measured_and_the_rule_catches_what_it_was_ruled_to(
    artifact: PreflopArtifact,
) -> None:
    """Decision 10 re-ruled: the two relations are measured per cell and gate nothing.

    Taylor read the grids and ruled the splits correct - among near-indifferent hands every split
    has the same EV, so a per-cell gate rejects correct play. What survives as a gate is that the
    measurement was taken: every committed spot covers all 169 classes now, so both relations
    compared every pair or a run that compared nothing goes green.

    The helper is shown failing and not over-firing first, on decision 10's own cases: the real
    44-versus-33 pair at 27 points is caught, the noise pair at 0.08 points is not, and an
    offsuit hand beating its suited twin is caught. Without that a helper that never fires would
    satisfy the coverage half below.
    """
    real = {"44": (("fold", 0.2719), ("raise", 0.7281)), "33": (("raise", 1.0),)}
    noise = {"44": (("fold", 0.0009), ("raise", 0.9991)),
             "33": (("fold", 0.0001), ("raise", 0.9999))}
    inverted = {"T9s": (("fold", 0.9), ("raise", 0.1)), "T9o": (("fold", 0.6), ("raise", 0.4))}

    assert [entry[1:3] for entry in monotonicity_violations("spot", real)] == [("44", "33")]
    assert monotonicity_violations("spot", noise) == []
    assert [entry[1:3] for entry in monotonicity_violations("spot", inverted)] == [("T9s", "T9o")]

    compared: dict[str, int] = {}
    for spot_id, _ in artifact.action_weights:
        monotonicity_violations(spot_id, weights_by_class(artifact, spot_id), compared)
    full = sum(1 for spot in artifact.spots if not spot.action_sequence)

    assert len(artifact.spots) == COMMITTED_SPOTS
    assert full == 1
    assert compared.get("ladder", 0) >= len(_ADJACENT_PAIRS) * full, compared
    assert compared.get("twins", 0) >= len(_SUITED_OVER_OFFSUIT) * full, compared


def test_the_group_dominance_figures_are_computed_and_published_for_every_partition(
    artifact: PreflopArtifact,
) -> None:
    """Published for a human, gating nothing. **Ruled by Taylor on 2026-09-01.**

    **This measure has returned four verdicts on four committed sets.** Over the uncut 51 it
    FAILS - 36 spots flagged as solved against 33 transposed, found by lane R3, so it scored the
    wrong index mapping as the better one. Over the 36 it PASSES on all five partitions: 14/27
    on single pair ranks, 1/26 on four bands, 1/26 on three, 1/24 on two, 21/24 on the suited
    rows. Over the 21 it is mixed - the three pair-band partitions still separate perfectly at
    0/12 each, single pair ranks TIE at 12/12, and the suited rows SATURATE at 21/21. Over the
    committed 6 it separates nothing anywhere: the four pair partitions read 0 against 0, which
    flags nothing under either mapping, and the suited rows read 6 against 6, which flags every
    spot under both.

    A measure whose verdict tracks how many spots are in the set is measuring set composition
    rather than whether the hand index is right. So it does not gate, which also restores
    Taylor's 2026-08-26 ruling that no group ORDER is gated: this is a group-order measure and
    gating it was drift. **What gates instead is the per-cell measure over spot partitions**, in
    `tests/test_derived_chart_report_validators.py`, which separates cleanly at every size
    measured - 0 against 26 over the 36, 0 against 21 over the 21, 0 against 6 over the 6 -
    because a per-cell swap is what it tests and that does not need the tree to have a deep part.

    What survives is that the figures are *taken*: a published measurement nobody computes is a
    blank column, so both arms must be present and bounded by the spot count on every partition.

    **A trap named on 2026-09-01: `transposed` here is NOT the counterfactual that gates.**
    `group_play_pct` reads row position `grid_index(name)` out of GTOpen's own ordering, which is
    what a converter indexing the payload by the grid ordering reads; the gate's
    `transpose_hand_index` swaps each suited hand with its offsuit twin outright, and its rank
    arm permutes ranks instead. None of the three is equivalent to another and they give
    materially different numbers - a stage-4 reimplementation that substituted one for another
    reproduced neither family's counts - so none predicts the others."""
    ordered = {
        label: (
            group_violating_spots(artifact, groups, transposed=False),
            group_violating_spots(artifact, groups, transposed=True),
        )
        for label, groups in GROUPS.items()
    }

    assert len(ordered) == len(GROUPS)
    assert len(artifact.spots) == COMMITTED_SPOTS
    for label, arms in ordered.items():
        # Computed and publishable, not compared: a `None` or a figure outside the set is a
        # column the report cannot print, which is the only failure left here.
        assert all(isinstance(a, int) and 0 <= a <= COMMITTED_SPOTS for a in arms), (label, arms)
    assert any(sum(arms) for arms in ordered.values()), "the measure computed nothing anywhere"
    # And the saturation is recorded rather than left as a surprising zero elsewhere: over six
    # spots the suited rows flag every spot under both mappings, which is what a measure that
    # has stopped separating looks like from the inside.
    assert ordered["suited rows"] == (COMMITTED_SPOTS, COMMITTED_SPOTS)


def test_the_two_orderings_hold_where_each_of_them_still_lives(
    library: PreflopChartLibrary, committed_export: SolverExport
) -> None:
    """Later position opens wider, and the big blind defends more against whoever opens wider.

    Both are properties of the game, so they survive the conversion or the conversion broke them
    - except that the chart no longer holds four of the five opening ranges, so the opening half
    is asserted over the export and the defence half over the chart, which inherits it. The
    defence relation follows the opening frequencies wherever they land rather than a fixed seat
    order, so the widest-opening seat is never covered by nothing."""
    opens = export_opening_pct(committed_export)
    defends = {position: defence_pct(library, position) for position in OPENERS}
    compared = 0

    assert set(opens) >= set(OPENERS)
    for tighter, wider in zip(OPENING_ORDER, OPENING_ORDER[1:], strict=False):
        assert opens[wider] > opens[tighter], opens
    for wider in OPENERS:
        for tighter in OPENERS:
            if wider == tighter or not opens[wider] > opens[tighter]:
                continue
            compared += 1
            assert defends[wider] > defends[tighter], (wider, tighter, opens, defends)

    assert compared >= len(OPENERS), (opens, defends)


def test_the_external_expectations_file_is_untouched_and_is_not_what_shipped(
    library: PreflopChartLibrary, artifact: PreflopArtifact
) -> None:
    """Pinned by content, because a reference regenerated from what it checks cannot fail. It is
    a raked GTO Wizard reference and this is a rake-free GTOpen solve, so the report prints one
    against the other and gates on nothing. All that is asserted is that the phase did not
    rewrite it - and that the derived chart is not it. The reference records the small blind
    limping 13.73 percent and this solve ran `limp: false`, so a chart agreeing with it came from
    the wrong file."""
    raw = EXPECTATIONS_PATH.read_bytes()
    reference = json.loads(raw)

    assert hashlib.sha256(raw).hexdigest() == EXPECTATIONS_SHA256
    assert set(reference["open_frequency_pct"]) == set(OPENERS)
    assert set(reference["big_blind_defence_pct"]) == set(OPENERS)
    assert GTOWIZARD_SOURCE_PATH.exists()

    assert reference["limp_frequency_pct"]["SB"] > 0.0
    assert library.action_frequency_pct(SB_OPEN_KEY, "call") == 0.0
    assert weights_by_class(artifact, SB_OPEN_KEY)


def test_the_source_card_posts_the_ruled_game_and_names_its_own_model(card: dict) -> None:
    """The re-solve changes `add_allin` and the solve target and nothing else.

    Field for field against `RULED_CONFIG`, which is what `config_errors` refuses an unruled
    export by, then the forbidden fields by name - equality against an imported constant passes
    just as happily if somebody widens the constant. `add_allin` is named because the re-solve
    moved it: with it true GTOpen inserts a jam beside every named raise, and the first cutover's
    chart jammed 44 at 1.0 where aces never jammed. The model line is derived from the config
    rather than matched against a remembered word, a card naming one model beside a
    `config_posted` naming another being the one claim about this export no gate command reads."""
    posted = card["config_posted"]

    assert posted == RULED_CONFIG
    assert posted["add_allin"] is False
    assert posted["open_raises"] == [2.5]
    assert posted["limp"] is False
    assert posted["stack"] == 100.0
    assert posted["ante"] == 0.0
    assert len(posted["positions"]) == TABLE_SIZE
    assert (posted["rake_pct"], posted["rake_cap"]) == (0.0, 0.0)
    assert f"realization={posted['realization']}" in card["model"]
    assert posted["realization"] == RULED_CONFIG["realization"]


def test_the_one_re_solve_decision_fourteen_ruled_is_the_only_solve_on_the_card(
    card: dict, committed_export: SolverExport
) -> None:
    """The inverted premise. A re-solve **did** replace the solve phase 10 captured.

    Until 2026-08-30 this asserted the opposite - one solve at phase 10's 300 iterations,
    checksums unmoved - because decision 2 had been re-ruled to ship as solved. Decision 14 then
    re-sourced at `add_allin: false`, on the finding that the shipped chart stacked off 100 blinds
    with a range inverted against hand strength. So what has to be loud now is a *second*
    re-solve: one solve record, two restamped checksums, the ruled target, pinned with its
    iteration count because the pair is the claim - 0.00016 met first at 1,900 of a 2,000 cap
    means the cap nearly binds. The achieved gap is asserted only against the target."""
    records = solve_records(card)
    committed = card["solve"]

    assert len(records) == 1, records
    assert committed["target_gap_bb"] == SOLVE_TARGET_GAP_BB
    assert committed["iteration_cap"] == SOLVE_ITERATION_CAP
    assert committed["iterations"] == COMMITTED_SOLVE_ITERATIONS
    assert committed["iterations"] < committed["iteration_cap"]
    assert committed["achieved_gap_bb"] < committed["target_gap_bb"]
    assert card["export_sha256"] == export_checksum(committed_export)
    assert card["export_sha256"] == COMMITTED_EXPORT_SHA256
    assert card["saved_solve"]["sha256"] == COMMITTED_SAVE_SHA256


def test_the_determinism_proof_and_the_walk_were_retaken_on_the_re_solve(
    card: dict, committed_export: SolverExport
) -> None:
    """Two of the five obligations a re-solve carries, retaken rather than carried over.
    Neither could be inherited: both are claims about a particular export and decision 14
    replaced it. The determinism result arrives as a structured field because nothing in the gate
    can re-run a solve, and the contract makes the script write it per `--determinism-only` - so
    the extractor's placeholder is refused by name, PENDING being a proof nobody took that still
    reads as an answer.
    """
    determinism, walk = card["determinism"], card["walk"]

    assert "PENDING" not in str(determinism["result"]), determinism
    assert determinism["max_divergence_bp"] == 0
    assert determinism.get("shape_differences") == 0
    assert walk["mismatches"] == 0
    assert walk["reresolved_nodes"] == committed_export.node_count
    assert walk["reresolved_nodes"] == COMMITTED_ACTION_NODES


def test_the_node_counts_and_size_block_are_recomputed(
    card: dict, committed_export: SolverExport
) -> None:
    """The reconciliation and the byte budget, both against the file that is actually there. The
    cap stopped binding when the predicate changed but the rule did not: exceeding the
    `data/artifacts` limit is a halt and a decision, not a number to raise. Deleting the retired
    chart, re-solving and writing a smaller chart all move the directory total, so the block is
    restamped or this fails. **The reconciliation is asserted against the committed chart as
    well**: a card whose counts match the export still describes the wrong build if the chart
    beside it holds a different number of spots."""
    counts, size = card["node_counts"], card["size"]
    total = sum(item.stat().st_size for item in ARTIFACTS.rglob("*") if item.is_file())
    per_node = size["bytes"] / committed_export.node_count

    assert committed_export.node_count == COMMITTED_ACTION_NODES
    assert counts["exported"] == committed_export.node_count
    assert counts["solver_action_nodes"] == committed_export.node_count
    assert size["limit_bytes"] == 20 * 1024 * 1024
    assert size["bytes"] == COMMITTED_EXPORT_PATH.stat().st_size
    assert size["bytes_per_node"] == pytest.approx(per_node, abs=0.01)
    assert total < size["limit_bytes"]
    assert size["headroom_bytes"] == size["limit_bytes"] - total
    assert len(import_preflop_artifacts(ARTIFACT_DIR)[0].spots) == COMMITTED_SPOTS


def test_the_committed_card_answers_every_field_it_owes(card: dict) -> None:
    """A field left at a placeholder is the drift defect phase 09 exists to have closed. The
    re-solve restamped the whole card, so every field is owed again; today this catches the
    determinism block, which the extractor leaves null until `--determinism-only` runs."""
    assert source_card_errors(card) == []
