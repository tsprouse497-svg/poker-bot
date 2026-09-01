"""Phase 14: the evidence that replacing the chart was a decision rather than an accident.

The companion to `tests/test_derived_chart.py`, split from it at the 700-line cap. That file
owns the committed artifact in its own right and owns the table constants, the predicate walk
and the two cell readers this file imports rather than copies. This file owns what the cutover
has to be defended with: the raked chart gone from the tree with its sizing table, which of its
36 spots survive and which fourteen the bot gives up, the card posting the ruled game and the
one re-solve decision 14 ordered, the two gated orderings, and the dominance measure.

**Re-cut at stage 4 on 2026-09-01, two premises inverted.** Decision 14 re-solved at
`add_allin: false`, so "no re-solve replaced it" is no longer the claim - what is asserted is
one re-solve, at the ruled target, carrying the five obligations one owes. And the contract's
group-order ladder was amended out the same day: what gates is the **discrimination**, that the
measure flags strictly fewer spots under the solver's own class ordering than under the
transposed one, on every partition, a tie refusing too.

**The opening frequencies are read off the export, not the chart.** The committed set holds one
opening range, the small blind's, so "later position opens wider" is a property of the solve
rather than of the chart; the defence ordering is asserted over the chart.
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
COMMITTED_SPOTS = 36
PRICED_SPOTS = 21
"""How many of the 36 price anything: 21 offer hero a raise and carry an entry, 15 offer call
and fold only - hero facing a five-bet jam, where the last raise is already in."""
RULED_PRICES = (2.5, 7.5, 22.5)
"""Every price the committed set offers, and hero's own 100 is not among them: five-betting
is only legal facing a four-bet and decision 20 withholds every four-bet-facing spot."""
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
RETIRED_SPOTS_CARRIED_OVER = 21
RAISES_FACED_WHEN_WITHHELD = 3
"""Decision 20 withholds the spots where hero faces a four-bet, which is three raises in the
sequence. Four raises is hero facing a five-bet jam and those spots stay committed."""
RETIRED_SPOT_WITH_NO_NODE = "t6/d100/BB/SB:call"
"""Passes the ruled predicate and still has no node to derive from: the solve is `limp: false`
and the tree holds no limp branch. Counted apart from the fourteen so the two ledgers agree."""

PROBE_HAND_CLASS = "AA"
"""Which class is immaterial: a query reaching a covered spot with a class outside hero's
arriving range still refuses with `lookup:hand-class-not-covered`, which names the spot."""

MONOTONICITY_TOLERANCE_PCT = 1.0
"""Decision 10, ruled 2026-08-24: adjacent ranks, one percentage point, both relations."""

# The external oracle this phase must not rederive: a reference regenerated from what it
# checks cannot fail, so it is pinned by content.
EXPECTATIONS_SHA256 = "39a80b67ae9d47b86656e42092b2ed97bd5829e28b86d56087a1805e3c90e373"

# The re-solve decision 14 ruled, pinned by content, because the checksums are what make a
# SECOND one loud: any further restamp is a solve nobody ruled, carrying five obligations of
# its own. The superseded `add_allin: true` build checksummed 1c9e383d and its save 64d8729a.
COMMITTED_EXPORT_SHA256 = "f7182f4bbcc080c7715d8195cd0552d4604ec9856c8d7d64cd5a52483e0949e7"
COMMITTED_SAVE_SHA256 = "1777810729942cfda30b10a1189ed5a910a5ce4f6c383f4664fd66a222312027"

COMMITTED_ACTION_NODES = 33_969
"""What the re-sourced tree holds, and what the census has to sum to."""

SOLVE_TARGET_GAP_BB = 0.00016
SOLVE_ITERATION_CAP = 2_000
COMMITTED_SOLVE_ITERATIONS = 1_900
"""The ruled target first met at iteration 1,900 of a 2,000 cap, so the cap **nearly binds** -
the fact worth freezing rather than the achieved gap, because a tighter target would run out of
iterations and leave `achieved < target` false."""


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
violations a node and its top hits are correct poker, preflop strength not being totally
ordered - the lojack opens 76s always and T6s never."""

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
"""Every partition decision 10's group form could be read as: it ruled "each pair band and
each suited row" without fixing the bands, so all are measured rather than one chosen."""


def play_pct(weights) -> float | None:
    """How often a hand is played rather than folded, the only quantity decision 10's relations
    are monotone in: a per-action rule is false wherever hero can call, the big blind
    three-betting aces always and never calling with them."""
    if weights is None:
        return None
    return 100.0 * (1.0 - sum(weight for action, weight in weights if action == "fold"))


def monotonicity_violations(spot_id: str, weights_by_class: dict, compared: dict | None = None):
    """Every dominating pair the spot plays the wrong way round, past the tolerance.

    A pair is skipped when either class is uncovered, since a spot behind hero's own raise
    covers only hero's arriving range. `compared` tallies, per relation, what was really
    looked at: without it a class-naming break - a rank string built the wrong way round, a
    suffix convention that stops matching the artifact's keys - compares nothing and passes.
    """
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

    `transposed` is the counterfactual: the artifact a converter produces indexing the payload
    by the grid ordering rather than GTOpen's own, the suited-for-offsuit swap the two index
    functions disagree about. Both the weights and the reach come from the swapped class,
    because a converter reads them with one index and gets both wrong together - taking only the
    weights compares a full range against a sparse one and measures the sparsity, which is the
    error that read transposed-as-cleaner on the way to the ruling.
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

    Decision 7's arrangement, and the only one left once stage 6 deletes the file. The commit is
    located rather than pinned: a hardcoded sha stops resolving the first time somebody rebases.
    """
    revisions = git("rev-list", "HEAD", "--", RETIRED_CHART_PATH).stdout.split()
    assert revisions, f"git history holds no {RETIRED_CHART_PATH}"
    for commit in revisions:
        found = git("cat-file", "-e", f"{commit}:{RETIRED_CHART_PATH}").returncode == 0
        if found:
            return json.loads(git("show", f"{commit}:{RETIRED_CHART_PATH}").stdout)
    raise AssertionError(f"no commit in history carries {RETIRED_CHART_PATH}")


def retired_split() -> tuple[list[tuple[str, str, tuple]], list[str]]:
    """The retired 36 put through the ruled predicate. One walk for both ledgers below, so
    what passes and what stays covered cannot be taken over two readings of the same file."""
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
    """Each seat's opening frequency, read off the solve rather than off the chart.

    The chart holds one opening range, so "later position opens wider" cannot be a property of
    the artifact any more. It remains one of the export it is derived from, which is where the
    ordering was gated at phase 10 and where a mis-assigned actor or a transposed hand index
    still breaks it. `aggregate_frequencies` is the export's own combo-weighted reader.
    """
    return dict(aggregate_frequencies(export).opening_pct)


def defence_pct(library: PreflopChartLibrary, opener: str) -> float:
    key = f"t{TABLE_SIZE}/d{STACK_DEPTH_BB}/BB/{opener}:raise@2.5"
    assert key in library.spot_keys(), f"the chart does not cover the big blind versus {opener}"
    return 100.0 - library.action_frequency_pct(key, "fold")


def test_the_raked_chart_is_absent_from_the_artifact_directory() -> None:
    """Deleted, because absence of a duplicate-key collision is not retirement.

    The retired chart three-bets to 8, 11 and 13.5 and opens the small blind to 3.5 while the
    export three-bets to 7.5 and opens to 2.5, so 17 of its 36 keys collide with nothing the new
    artifact declares: the library would build clean with both loaded and the bot would answer
    every three-bet spot from raked ranges. The sizing table goes too, one file for one chart."""
    assert not (ARTIFACT_DIR / RETIRED_CHART_NAME).exists()
    assert RETIRED_CHART_NAME not in {path.name for path in ARTIFACT_DIR.glob("*.json")}
    assert not (SIZINGS_DIR / RETIRED_CHART_NAME).exists()
    assert len(list(SIZINGS_DIR.glob("*.json"))) == 1


def test_the_committed_sizing_file_is_at_the_per_class_schema() -> None:
    """Decision 6 as re-cut on 2026-08-26: one weight per price per *hand class*.

    Version 1 held a bare float per spot and version 2 a list per class, so the version is what
    a reader checks before trusting the indexing. The shape is read off the file rather than
    through `PreflopSizingTable`, whose loader would make its own version claim vacuous.

    **The two-price case is unexercised, labelled rather than counted as a check that passed.**
    The schema holds a list because a spot may offer hero two prices, and 0 of the 36 do, so the
    ordering and weights-sum-to-one assertions run over lists of length one where they cannot
    fail. The last assertion makes that a measurement, so a later solve turns it red.
    """
    paths = sorted(SIZINGS_DIR.glob("*.json"))
    assert len(paths) == 1, paths
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    sizes = payload["raise_to_bb"]
    widths = set()

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
    was verified by reading `action_sequence` values, which is a history reading. Under the
    ruled predicate 22 of the 36 pass and 14 do not, and 21 of those 22 end up covered - the
    twenty-second is the limped pot the solve has no branch for. So the cutover gives up 14,
    four opening ranges among them, and gains 36 - 21 = 15. Read out of git history because the
    file is deleted, and asserted spot by spot rather than as a count, because a count of 14
    with the wrong 14 in it is the same arithmetic and a different chart.
    """
    survivors, lost = retired_split()
    passing = [spot_id for spot_id, _, _ in survivors]

    assert len(passing) + len(lost) == 36
    assert sorted(lost) == sorted(RETIRED_SPOTS_LOST)
    assert len(passing) == 22
    assert RETIRED_SPOT_WITH_NO_NODE in passing


def test_the_retired_spots_that_survive_the_predicate_are_covered_bar_the_limp(
    library: PreflopChartLibrary,
) -> None:
    """21 of the retired 36 stay covered, and the twenty-second is the limped pot.

    **Asked the way the bot asks it, which is the whole of why 21 is the number.** The retired
    chart opens the small blind to 3.5 and three-bets to 8, 11 and 13.5 while the derived chart
    holds 2.5, 7.5 and 22.5, so exactly five keys exist verbatim and raw membership in
    `spot_keys()` answers a different question. Phase 12's ruling 8 is what makes 21 true: the
    lookup normalises an observed price to the nearest one declared for that line, so each
    survivor goes to `library.lookup` as a `ChartQuery` and the 21 land on 21 distinct keys.

    Coverage is read off the refusal code rather than one hand class, because a spot behind
    hero's own raise covers only hero's arriving range. `BB/SB:call` passes the predicate with
    no node to derive from, the solve being `limp: false`; that is
    `CHART-CANNOT-ANSWER-A-LIMPED-POT` and the baseline the refusal-rate criterion is stated
    against - the rate rises on those fourteen plus this one and nowhere else.

    **Decision 20 costs this ledger nothing, measured rather than assumed.** It refuses the
    fifteen four-bet-facing spots and the retired chart has no four-bet-facing key at all, GTO
    Wizard's 36 stopping at hero facing a three-bet, so no survivor lands on a withheld key and
    "must not rise there at all" holds. A converter that withheld the wrong fifteen breaks it.
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

    assert len(answered) == RETIRED_SPOTS_CARRIED_OVER
    assert len(set(answered.values())) == RETIRED_SPOTS_CARRIED_OVER, answered
    assert refused == [RETIRED_SPOT_WITH_NO_NODE]
    assert len([spot_id for spot_id, _, _ in survivors if spot_id in covered]) == 5
    for key in RETIRED_SPOTS_LOST:
        assert key not in covered, key
    for spot_id, landed in answered.items():
        faced = landed.split("/")[3]
        raises = 0 if faced == "rfi" else sum(1 for e in faced.split(",") if ":raise@" in e)
        assert raises != RAISES_FACED_WHEN_WITHHELD, (spot_id, landed)


def test_the_monotonicity_rule_catches_what_it_was_ruled_to_catch() -> None:
    """The helper above, shown failing and shown not over-firing, on decision 10's own cases: the
    real 44-versus-33 pair at 27 points is caught, the noise pair at 0.08 points is not, and an
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
    split has the same EV, so a per-cell gate rejects correct play. What survives as a gate is
    that the measurement was taken at all: the one folded-to-hero spot covers all 169 classes,
    so both relations compared every pair there or a run that compared nothing goes green.
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
    """The gate the contract was amended onto on 2026-09-01, and the only dominance gate there is.

    **No group order is gated.** Taylor ruled that out on 2026-08-26 and the contract asserted
    it anyway until the amendment. What gates is the discrimination: the measure must flag
    strictly fewer spots under GTOpen's own class ordering than under the grid ordering, on
    every partition, a tie refusing too. A transposition leaves every total intact, so this is
    the only thing in the phase that would notice one.

    **The direction is asserted and the counts are not, deliberately.** A count fixes a
    partition, and choosing the partition that reads smallest is picking a number to go green -
    the move the contract forbids for the selection rule and no more honest here. The counts go
    in the report, where a human reads them; measured over the real 36 on 2026-09-01 these five
    read 14 solved against 27 transposed on single pair ranks, 1 against 26 on four bands, 1
    against 26 on three, 1 against 24 on two, and 21 against 24 on the suited rows.

    These five partition the **hand classes**, which is decision 10's sense of the word. The
    stage-3 retake's eleven partition the **spots** and read them with the twins measure the
    generator ships; both measured green, and the second family is asserted in
    `tests/test_derived_chart_report_validators.py` against the shipped functions themselves.
    """
    ordered = {}
    for label, groups in GROUPS.items():
        ordered[label] = (
            group_violating_spots(artifact, groups, transposed=False),
            group_violating_spots(artifact, groups, transposed=True),
        )

    assert len(ordered) == len(GROUPS)
    assert len(artifact.spots) == COMMITTED_SPOTS
    for label, (solved, transposed) in ordered.items():
        assert solved < transposed, (
            f"{label}: the measure flags {solved} spots as solved and {transposed} with suited"
            " and offsuit transposed, so it does not prefer the solved index mapping"
        )


def test_later_position_opens_wider_in_the_solve_the_chart_came_from(
    committed_export: SolverExport,
) -> None:
    """A property of the game, so it survives the conversion or the conversion broke it -
    except that the chart no longer holds four of the five opening ranges, so the claim is
    asserted where it still lives. What the chart inherits is the defence ordering below."""
    opens = export_opening_pct(committed_export)

    assert set(opens) >= set(OPENERS)
    for tighter, wider in zip(OPENING_ORDER, OPENING_ORDER[1:], strict=False):
        assert opens[wider] > opens[tighter], opens


def test_the_big_blind_defends_more_against_whoever_opens_wider(
    library: PreflopChartLibrary, committed_export: SolverExport
) -> None:
    """Not a fixed order: the relation follows the opening frequencies wherever they
    land, so the widest-opening seat is never covered by nothing at all. It is also the check a
    transposed hand index or a mis-assigned actor breaks first, and the big blind closes the
    action, so every one of its spots is terminal-clean and survives both rulings."""
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

    It is a raked GTO Wizard reference and this is a rake-free GTOpen solve, so the report
    prints one against the other and gates on nothing. All that is asserted is that the phase
    did not rewrite the one file in the comparison this repo did not produce."""
    raw = EXPECTATIONS_PATH.read_bytes()
    reference = json.loads(raw)

    assert hashlib.sha256(raw).hexdigest() == EXPECTATIONS_SHA256
    assert set(reference["open_frequency_pct"]) == set(OPENERS)
    assert set(reference["big_blind_defence_pct"]) == set(OPENERS)
    assert GTOWIZARD_SOURCE_PATH.exists()


def test_the_derived_chart_is_not_the_raked_reference(
    library: PreflopChartLibrary, artifact: PreflopArtifact
) -> None:
    """The one difference that is ruled rather than measured: the reference records the
    small blind limping 13.73 percent and this solve ran `limp: false`, so a chart agreeing with
    it came from the wrong file. It is also the one opening range both files hold."""
    reference = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    assert reference["limp_frequency_pct"]["SB"] > 0.0
    assert library.action_frequency_pct(SB_OPEN_KEY, "call") == 0.0
    assert weights_by_class(artifact, SB_OPEN_KEY)


def test_the_source_card_posts_the_ruled_game_unchanged(card: dict) -> None:
    """The re-solve changes `add_allin` and the solve target and nothing else.

    Field for field against `RULED_CONFIG`, which is what `config_errors` refuses an unruled
    export by, then the forbidden fields by name - equality against an imported constant passes
    just as happily if somebody widens the constant. `add_allin` is named because it is the one
    field the re-solve moved: with it true GTOpen inserts a jam beside every named raise, and
    the first cutover's chart jammed 44 at 1.0 where aces never jammed at all.
    """
    posted = card["config_posted"]

    assert posted == RULED_CONFIG
    assert posted["add_allin"] is False
    assert posted["open_raises"] == [2.5]
    assert posted["limp"] is False
    assert posted["stack"] == 100.0
    assert posted["ante"] == 0.0
    assert len(posted["positions"]) == TABLE_SIZE
    assert (posted["rake_pct"], posted["rake_cap"]) == (0.0, 0.0)


def test_the_card_names_the_realization_model_its_own_config_posted(card: dict) -> None:
    """A card naming one model beside a `config_posted` naming another is the one claim about
    this export no gate command reads, so the model line is derived from the config rather than
    matched against a remembered word. Decision 3's recorded bias is about `calibrated`: under
    the default `static` the big blind defends 99.71 percent against a small-blind open, which
    is not poker, so a changed model makes the recorded bias false rather than fixed."""
    posted = card["config_posted"]

    assert f"realization={posted['realization']}" in card["model"]
    assert posted["realization"] == RULED_CONFIG["realization"]


def test_the_one_re_solve_decision_fourteen_ruled_is_the_only_solve_on_the_card(
    card: dict, committed_export: SolverExport
) -> None:
    """The inverted premise. A re-solve **did** replace the solve phase 10 captured.

    Until 2026-08-30 this asserted the opposite - one solve at phase 10's 300 iterations,
    checksums unmoved - because decision 2 had been re-ruled to ship as solved. Decision 14 then
    re-sourced at `add_allin: false`, on the finding that the shipped chart stacked off 100 big
    blinds with a range inverted against hand strength. So what has to be loud now is a *second*
    re-solve, not a first: one solve record, two restamped checksums, the ruled target.

    The target is pinned with its iteration count because the pair is the claim: 0.00016 met
    first at 1,900 of a 2,000 cap means the cap nearly binds, so a reader can tell a solve that
    converged from one that ran out of iterations. The achieved gap is asserted only against the
    target, being solver output to seventeen digits that an honest re-derivation may round.
    """
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
    replaced it. The determinism result arrives as a structured field because nothing in the
    gate can re-run a solve, and the contract makes the script write it per `--determinism-only`
    rather than a human type it - so the extractor's placeholder is refused by name, PENDING
    being a proof nobody took that still reads as an answer.
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
    """The reconciliation and the byte budget, both against the file that is actually there.

    The cap stopped binding when the predicate changed but the rule did not: exceeding the
    `data/artifacts` limit is a halt and a decision, not a number to raise. Deleting the retired
    chart, re-solving and writing a smaller chart all move the directory total, so the block is
    restamped or this fails. The node count is the third of the re-solve's five obligations."""
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


def test_the_committed_card_answers_every_field_it_owes(card: dict) -> None:
    """A field left at a placeholder is the drift defect phase 09 exists to have closed.

    The re-solve restamped the whole card, so every field is owed again; today this catches the
    determinism block, which the extractor leaves null until `--determinism-only` runs.
    """
    assert source_card_errors(card) == []
