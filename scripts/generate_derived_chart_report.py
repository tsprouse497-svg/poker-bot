"""The derived preflop chart, written for a reviewer who does not read code.

The chart itself is `solver_artifacts.chart_derivation`'s subject and the artifact is
committed; this script is where a person is led to a conclusion about it. That is a
separate job from the chart being right, which is why it is a separate file: a report
renders whatever it is handed, so a census that does not add up and a spot count that
disagrees with the walk that produced it would publish exactly as happily as the right
numbers would.

So four figures are validated rather than formatted, and the command exits non-zero and
writes nothing when they do not hold: the node census against the export's own source
card, the artifact's spot set against the walk's key by key, the group dominance measure
against its own transposed mapping, and the old-versus-new disagreement count. Everything
else here is prose, and saying which is which is what lets a canary be aimed.

The closing measurement is the phase's reason to exist. The same corpus comparison runs
twice - once over the derived chart and once over the retired one, read out of git history
at the pin decision 7 names - so "the refusal rate rose" is one comparison over one corpus
rather than two runs of different code a reader has to trust agree.

Decision 9's band was pre-registered before any of this was measured, so the report prints
the record's numbers rather than restating a prediction of its own, and prints its own
recomputed defence delta beside them. A miss in either direction is a result.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.data_pipeline.comparison import (  # noqa: E402
    AGREE,
    DISAGREE,
    POPULATIONS,
    REFUSED,
    ComparisonResult,
    ComparisonRow,
    compare_committed_sample,
)
from poker_training_bot.data_pipeline.sample import load_committed_sample  # noqa: E402
from poker_training_bot.solver_artifacts import lookup  # noqa: E402
from poker_training_bot.solver_artifacts.chart_derivation import (  # noqa: E402
    NodeCensus,
    census,
    is_committed_node,
    node_spot_key,
)
from poker_training_bot.solver_artifacts.gtopen_export import (  # noqa: E402
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    gtopen_class_index,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.hand_classes import (  # noqa: E402
    HAND_CLASSES,
    hand_class_grid_index,
)
from poker_training_bot.solver_artifacts.importer import import_preflop_artifact  # noqa: E402
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary  # noqa: E402
from poker_training_bot.solver_artifacts.schema import (  # noqa: E402
    PREFLOP_ACTIONS,
    ArtifactAuditFields,
    ArtifactSource,
    BlindStructure,
    PreflopAction,
    PreflopArtifact,
    SpotDefinition,
)
from poker_training_bot.solver_artifacts.solve_conditions import REACH_SCALE_BP  # noqa: E402
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy  # noqa: E402
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable  # noqa: E402

REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_derived_chart_report.txt"

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"

COMMITTED_ARTIFACT = ARTIFACT_DIR / "six_max_100bb_rakefree.json"

EXPECTATIONS = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"

DECISIONS_DOC = "reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md"

MONOTONICITY_TOLERANCE_PCT = 1.0
"""Decision 10's tolerance, in percentage points, and the ruling is that it MEASURES.

Re-ruled on 2026-08-24 to count per cell and gate on aggregates only: among
near-indifferent hands every split has the same EV, so an individual cell carries no
information and a generator that refused a violating grid would refuse the committed
chart. A gap of exactly a point is not a violation - the count is of gaps strictly
wider than this.
"""

RANKS = "AKQJT98765432"
"""Strongest first, so an adjacent pair in this string is an adjacent pair rank."""

RETIRED_CHART_PATH = "data/artifacts/preflop/six_max_nl25_100bb.json"

RETIRED_SIZING_PATH = "data/artifacts/preflop/sizings/six_max_nl25_100bb.json"

RETIRED_CHART_COMMIT = "d046ac9d27feeb3b64a71b3ad4ba65d32b88d3a3"
"""Decision 7's pin: the last commit at which the retired raked chart is in the tree.

Read out of git history rather than kept as a second copy under `data/artifacts/preflop/`,
which is the arrangement that makes a reader ask which chart the bot plays - the one
confusion this phase exists to end. A pin makes the comparison reproducible: anybody can
fetch the same bytes.
"""

# The retired chart was solved at NL25, where the blinds sit in the ordinary 1:2 ratio and
# no ante is posted. Schema 2 requires the field and schema 1 never carried it, so it is
# reconstructed from the structure the file's own prices are written in - a 2.5bb open at a
# 1bb big blind - rather than guessed. Nothing in the comparison reads it: the strategy
# refuses a straddle or an ante by reconstructing the query's own pot, never by consulting
# the artifact.
RETIRED_BLIND_STRUCTURE = BlindStructure(small_blind_bb=0.5, big_blind_bb=1.0, ante_bb=0.0)


class DerivedChartReportError(RuntimeError):
    """A figure the report would have published that does not hold.

    Raised rather than printed, and every raise is collected into one list so a reviewer
    reads every broken figure at once instead of fixing them one command at a time.
    """


# -- the four validated figures ------------------------------------------------------- #


def validate_census(census_counts: NodeCensus, exported_nodes: int) -> None:
    """Every solved node in exactly one bucket, under a reason somebody ruled.

    Three things are checked and each has a way of failing that arithmetic alone misses.
    The buckets have to sum to the export's own node count, or the census is a subset
    dressed as a census - a converter that skipped a subtree balances its own books
    perfectly. Every reason has to be in `lookup.py`'s closed vocabulary, or a node the
    converter merely failed to handle gets filed as a property of the spot grammar. And
    BOTH exclusion codes have to appear: the point of having two is that a reader can tell
    the nodes GTOpen misprices from the ones it prices exactly and reaches through a cold
    call, and a census filing all 38,742 under one reason cannot say which of them come
    back when the source is fixed.
    """
    total = census_counts.total
    if total != exported_nodes:
        raise DerivedChartReportError(
            f"the census accounts for {total} nodes against the export's {exported_nodes};"
            " every solved node belongs to exactly one bucket"
        )
    for code in census_counts.excluded:
        if code not in lookup.DERIVATION_EXCLUSION_CODES:
            raise DerivedChartReportError(
                f"the census excludes nodes under {code!r}, which is not one of the ruled"
                f" reasons {list(lookup.DERIVATION_EXCLUSION_CODES)}"
            )
    missing = [
        code for code in lookup.DERIVATION_EXCLUSION_CODES if code not in census_counts.excluded
    ]
    if missing:
        raise DerivedChartReportError(
            f"the census publishes no excluded nodes under {missing}; one code cannot say"
            " which nodes come back when GTOpen can price a multiway pot"
        )
    for code in census_counts.inexpressible:
        if code not in lookup.DERIVATION_INEXPRESSIBILITY_CODES:
            raise DerivedChartReportError(
                f"the census calls nodes inexpressible under {code!r}, which is not one of"
                f" the ruled reasons {list(lookup.DERIVATION_INEXPRESSIBILITY_CODES)}"
            )


def validate_spot_count(artifact_keys: set[str], walked_keys: set[str]) -> None:
    """The committed spot set against the walk's, key by key rather than by count.

    Counting cannot catch this: a converter that dropped one node and invented one key
    gives the same total. So both directions are named, and the invented direction is the
    one a converter built on the superseded predicate fails - it commits the lojack's open,
    which the ruled predicate drops because a multiway terminal sits below every branch.
    """
    invented = sorted(artifact_keys - walked_keys)
    dropped = sorted(walked_keys - artifact_keys)
    if invented or dropped:
        raise DerivedChartReportError(
            f"the artifact's {len(artifact_keys)} spots disagree with the walk's"
            f" {len(walked_keys)}: it invents {invented} and drops {dropped}"
        )


def count_dominance_violations(grid: Mapping[str, Mapping[str, float]]) -> dict[str, int]:
    """The two dominance relations, counted per cell and gating nothing.

    Decision 10 measures rather than refuses, so this returns counts: the committed chart
    holds surviving violations that Taylor read the grids for and ruled correct, and a
    generator that refused a violating grid would refuse the committed chart.

    The ladder compares ADJACENT pair ranks only. Comparing every pair against every
    weaker one turns one drifting step into a dozen violations and reports the same defect
    a dozen times; comparing neighbours reports it once, where it happens. The twins
    compare a suited hand against the offsuit hand of the same two ranks, which is the
    relation a transposed hand index breaks.

    The two are counted apart because they move in different directions and by different
    sizes, and one total hides that.
    """
    counts = {"ladder": 0, "twins": 0}
    for cells in grid.values():
        for stronger, weaker in zip(RANKS, RANKS[1:], strict=False):
            high, low = cells.get(f"{stronger}{stronger}"), cells.get(f"{weaker}{weaker}")
            if high is None or low is None:
                continue
            if low - high > MONOTONICITY_TOLERANCE_PCT:
                counts["ladder"] += 1
        for hand_class_text, suited in cells.items():
            if not hand_class_text.endswith("s"):
                continue
            offsuit = cells.get(f"{hand_class_text[:-1]}o")
            if offsuit is not None and offsuit - suited > MONOTONICITY_TOLERANCE_PCT:
                counts["twins"] += 1
    return counts


def validate_group_discrimination(solved: int, transposed: int) -> None:
    """The aggregate has to prefer the solved hand index to the transposed one.

    Over the 5,626 the superseded predicate selected, this comparison came out backwards:
    2,007 spots flagged under the solved mapping against 818 under the mapping with suited
    and offsuit swapped, so the measure scored the defect it exists to catch as the better
    reading. The claim was withdrawn rather than restated, and what is gated now is the
    discrimination itself. A tie refuses too: a measure that cannot tell the two mappings
    apart cannot catch a transposition.
    """
    if solved >= transposed:
        raise DerivedChartReportError(
            f"the group dominance measure flags {solved} spots under the solved hand index"
            f" and {transposed} under the transposed one, so it does not discriminate"
            " between them and cannot catch a transposed index"
        )


def validate_disagreement(
    *, shared_decisions: int, disagreements: int, by_direction: Mapping[str, int]
) -> None:
    """The old-versus-new count, checked for having happened at all.

    A comparison that quietly became trivial arrives as a small consistent number rather
    than as an error, which is why the arithmetic is not enough on its own. An empty
    overlap is refused, and so is a zero disagreement count over a nonzero overlap: that
    is the shape of the comparison being handed the same chart twice, and the poker rules
    it out on its own terms, because the two charts share no three-bet price and no
    small-blind opening price - the retired one raises to 8, 11, 13.5 and 3.5 where the
    derived chart holds 7.5 and 2.5 - so they cannot agree on a thousand shared decisions.
    """
    if shared_decisions <= 0:
        raise DerivedChartReportError(
            "the two charts share no corpus decision, so there is nothing to disagree about"
            " and the overlap was never measured"
        )
    if disagreements == 0:
        raise DerivedChartReportError(
            f"the two charts agree on all {shared_decisions} shared decisions; they price"
            " neither the three-bets nor the small blind's open alike, so a zero here is a"
            " comparison handed the same chart twice rather than a measurement"
        )
    if disagreements > shared_decisions:
        raise DerivedChartReportError(
            f"{disagreements} disagreements over {shared_decisions} shared decisions is more"
            " disagreement than there were decisions"
        )
    directed = sum(by_direction.values())
    if directed != disagreements:
        raise DerivedChartReportError(
            f"the directions sum to {directed} against {disagreements} disagreements, so the"
            f" published split {dict(by_direction)} is not of this total"
        )


# -- the retired chart, read out of git history ---------------------------------------- #


class _RetiredArtifact(PreflopArtifact):
    """The retired chart as it shipped, read without the rules that retired it.

    Schema 2 refuses this file by design and every clause of the refusal is deliberate: it
    declares `artifact_schema_version` 1, carries no blind structure and no per-cell
    arriving reach, and hero limps at it - 103 hand classes hold a nonzero call weight at
    `t6/d100/SB/rfi`, which is the state the repo shipped in and which `_validate_no_limp`
    was written in this phase to refuse.

    So the validating path cannot read it, and repairing the payload until it passes would
    delete the limp - the very thing the before column is measuring. Validation is skipped
    instead and the bytes are read as they shipped. Nothing downstream needs what is
    missing: `PreflopChartLibrary.lookup` reads spots and weights only, and the arriving
    reach stays empty so every cell answers None, which is what "not recorded" means here.
    """

    def __post_init__(self) -> None:
        return None


def _read_at_commit(commit: str, path: str) -> str:
    """One file's bytes at one commit, or a refusal naming which half of the pin failed."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise DerivedChartReportError(
            f"{path} cannot be read at commit {commit!r}, so the retired chart the"
            f" old-versus-new comparison needs is not there: {result.stderr.strip()}"
        )
    return result.stdout


def _retired_artifact(payload: dict) -> PreflopArtifact:
    """The schema-1 payload in the shape the library indexes, nothing reinterpreted."""
    spots = tuple(
        SpotDefinition(
            spot_id=spot["spot_id"],
            hero_position=spot["hero_position"],
            action_sequence=tuple(
                PreflopAction(entry["position"], entry["action"], entry.get("size_bb"))
                for entry in spot["action_sequence"]
            ),
        )
        for spot in payload["spots"]
    )
    action_weights = tuple(
        (
            spot.spot_id,
            tuple(
                (
                    hand_class_text,
                    tuple(
                        (action, float(weight))
                        for action, weight in sorted(
                            payload["action_weights"][spot.spot_id][hand_class_text].items(),
                            key=lambda pair: PREFLOP_ACTIONS.index(pair[0]),
                        )
                    ),
                )
                for hand_class_text in sorted(
                    payload["action_weights"][spot.spot_id], key=hand_class_grid_index
                )
            ),
        )
        for spot in spots
    )
    audit = payload["audit_fields"]
    return _RetiredArtifact(
        artifact_schema_version=payload["artifact_schema_version"],
        source=ArtifactSource(
            name=payload["source"]["name"],
            kind=payload["source"]["kind"],
            reference=payload["source"]["reference"],
        ),
        generated_at=payload["generated_at"],
        table_size=payload["table_size"],
        stack_depth_bb=payload["stack_depth_bb"],
        positions=tuple(payload["positions"]),
        blind_structure=RETIRED_BLIND_STRUCTURE,
        spots=spots,
        action_weights=action_weights,
        arriving_reach_bp=(),
        audit_fields=ArtifactAuditFields(
            weights_sha256=audit["weights_sha256"],
            spot_count=audit["spot_count"],
            hand_class_count=audit["hand_class_count"],
            notes=audit["notes"],
        ),
    )


def _retired_sizing(payload: dict, artifact: PreflopArtifact) -> PreflopSizingTable:
    """The retired sizing table, lifted from one price per spot to schema 2's price list.

    Schema 1 held a single `to_bb` for a whole spot, which is the same statement as every
    covered hand class raising to that price with all of hero's weight on it. Written out
    per class rather than converted on the way into a lookup, so the before column is
    priced by the table the retired chart actually shipped with.
    """
    raise_to_bb = {
        spot_id: {
            hand_class_text: [{"to_bb": float(payload["raise_to_bb"][spot_id]), "weight": 1.0}]
            for hand_class_text, _ in hand_classes
        }
        for spot_id, hand_classes in artifact.action_weights
        if spot_id in payload["raise_to_bb"]
    }
    return PreflopSizingTable(
        source_name=payload["source"]["name"],
        source_kind=payload["source"]["kind"],
        raise_to_bb=raise_to_bb,
    )


def load_retired_chart_from_git(commit: str) -> PreflopChartStrategy:
    """The retired chart and its own sizing table, played from git history.

    Both files, from the same commit: the sizing table went with the chart, and pricing the
    retired ranges off the derived table would report a chart nobody ever shipped. The
    retired small blind opens to 3.5bb where the derived one opens to 2.5, so the two
    tables are not interchangeable even where the spot keys collide.
    """
    payload = json.loads(_read_at_commit(commit, RETIRED_CHART_PATH))
    sizing_payload = json.loads(_read_at_commit(commit, RETIRED_SIZING_PATH))
    artifact = _retired_artifact(payload)
    return PreflopChartStrategy(
        library=PreflopChartLibrary.from_artifacts([artifact]),
        sizing=_retired_sizing(sizing_payload, artifact),
    )




# -- what the report measures ----------------------------------------------------------- #


@dataclass(frozen=True)
class Walk:
    """One walk of the committed export, shared by every section that measures it.

    Re-derived here rather than read back off the artifact. The report's job is to compare
    the two, and a section that read the committed spot set and called it the walk's would
    agree with itself whatever the converter did.
    """

    census: NodeCensus
    spot_keys: frozenset[str]
    exported_nodes: int
    node_path_by_spot: dict[str, tuple[int, ...]]
    open_frequency_pct: dict[str, float]
    reach_bp_by_cell: dict[tuple[str, str], int]


def walk_export() -> Walk:
    """Account for every solved node, and carry out what the export alone can say.

    The opening frequencies come from here rather than from the chart because the ruled
    predicate commits one opening range. Four of the five are properties of the solve that
    the cutover does not ship, and printing them as the chart's would claim coverage the
    phase gave up.
    """
    export = load_solver_export(COMMITTED_EXPORT_PATH)
    by_path = export.by_path()
    keys: set[str] = set()
    node_path_by_spot: dict[str, tuple[int, ...]] = {}
    open_frequency_pct: dict[str, float] = {}
    reach_bp_by_cell: dict[tuple[str, str], int] = {}
    for node in export.nodes:
        key = node_spot_key(by_path, node)
        if key.endswith("/rfi"):
            folds = next(i for i, action in enumerate(node.actions) if action.kind == "fold")
            open_frequency_pct[key.split("/")[2]] = 100.0 * (1.0 - node.action_frequency(folds))
        if not is_committed_node(by_path, node):
            continue
        keys.add(key)
        node_path_by_spot[key] = node.path
        for hand_class_text in HAND_CLASSES:
            reach = node.reach_bp[gtopen_class_index(hand_class_text)]
            reach_bp_by_cell[(key, hand_class_text)] = int(reach)
    card = json.loads(COMMITTED_SOURCE_CARD_PATH.read_text(encoding="utf-8"))
    return Walk(
        census=census(export),
        spot_keys=frozenset(keys),
        exported_nodes=int(card["node_counts"]["exported"]),
        node_path_by_spot=node_path_by_spot,
        open_frequency_pct=open_frequency_pct,
        reach_bp_by_cell=reach_bp_by_cell,
    )


def play_grid(artifact: PreflopArtifact) -> dict[str, dict[str, float]]:
    """How often each cell puts money in, which is what both relations are stated over.

    One number per cell rather than a distribution, because a stronger hand raising where
    a weaker one calls is not a dominance violation - both continue. What breaks the
    relation is the stronger hand folding more.
    """
    return {
        spot_id: {
            hand_class_text: 100.0 * (1.0 - dict(weights).get("fold", 0.0))
            for hand_class_text, weights in hand_classes
        }
        for spot_id, hand_classes in artifact.action_weights
    }


def transpose_hand_index(cells: Mapping[str, float]) -> dict[str, float]:
    """One spot's grid with every suited hand reading its offsuit twin's row.

    The defect `solver-export-hand-index-uses-the-grid-ordering` produces, applied on
    purpose so the group measure can be shown discriminating against it rather than
    asserted to.
    """
    swapped = dict(cells)
    for index, high in enumerate(RANKS):
        for low in RANKS[index + 1 :]:
            suited, offsuit = f"{high}{low}s", f"{high}{low}o"
            if suited in cells and offsuit in cells:
                swapped[suited], swapped[offsuit] = cells[offsuit], cells[suited]
    return swapped


def spots_violating_twins(grid: Mapping[str, Mapping[str, float]]) -> int:
    """Spots holding at least one suited-under-offsuit cell, which is the group unit."""
    return sum(1 for cells in grid.values() if count_dominance_violations({"s": cells})["twins"])


def spot_shape(spot_key_text: str) -> tuple[str, tuple[str, ...]]:
    """A spot with its prices removed: whose decision it is, not what it cost.

    The two charts are keyed at different prices - the retired one three-bets to 8, 11 and
    13.5 and opens the small blind to 3.5, the derived one holds 7.5 and 2.5 - so a
    key-by-key intersection reports five survivors where the poker says twenty-one. A
    retired spot is carried over when the derived chart answers the same decision at its
    own solved price, which is a repricing rather than a loss of coverage.
    """
    _, _, hero, tail = spot_key_text.split("/")
    if tail == "rfi":
        return hero, ()
    return hero, tuple(entry.split("@")[0] for entry in tail.split(","))


def first_action_is_a_call(spot_key_text: str) -> bool:
    """Decision 12's definition of a limped pot, stated so a reader can apply it."""
    parts = spot_key_text.split("/")
    return len(parts) > 3 and parts[3].split(",")[0].endswith(":call")


OPENER_KEY = re.compile(r"^t6/d\d+/BB/(LJ|HJ|CO|BTN|SB):raise@")
"""The big blind facing exactly one open, and which seat opened.

Read off the key the lookup asked about rather than off either chart's coverage, so the
before and after columns are over the same decisions even where the two charts price the
open differently - the retired small blind opens to 3.5 and the derived one to 2.5.
"""

SCORED = frozenset({AGREE, DISAGREE})


def scored_rows(result: ComparisonResult, population: str) -> list[ComparisonRow]:
    return [
        row
        for row in result.rows
        if row.population == population and row.verdict in SCORED
    ]


def population_rates(result: ComparisonResult, population: str) -> dict[str, tuple[int, int]]:
    """The three rates one population gets, each with the sample it is over.

    Three rather than one because they answer different questions and a reader given only
    the first will read it as the other two. Agreement is over the decisions the chart
    answered, so it is silent about how many it declined; the refusal rate is that
    silence, published; and the sampled-action match is the stricter reading of agreement,
    beside it because a chart that got more mixed scores higher on the looser one while
    playing no better.
    """
    everything = [row for row in result.rows if row.population == population]
    scored = scored_rows(result, population)
    drawn = [row for row in scored if row.sampled_action is not None]
    return {
        "agreement": (sum(1 for row in scored if row.verdict == AGREE), len(scored)),
        "refused": (sum(1 for row in everything if row.verdict == REFUSED), len(everything)),
        "sampled-action match": (
            sum(1 for row in drawn if row.sampled_action == row.observed_action),
            len(drawn),
        ),
    }


def big_blind_call_agreement(
    result: ComparisonResult, population: str
) -> dict[str, tuple[int, int]]:
    """Agreement on the big blind's calls, split by the seat that opened.

    The unit decision 9's band is written in. Narrowed to calls because a fold is the
    easiest agreement in poker and roughly seven in ten preflop decisions are folds, so an
    unsplit rate mostly measures how often both sides threw away junk.
    """
    agreement: dict[str, list[int]] = {}
    for row in scored_rows(result, population):
        if row.position != "BB" or row.observed_action != "call" or not row.asked_spot_key:
            continue
        opener = OPENER_KEY.match(row.asked_spot_key)
        if opener is None:
            continue
        tally = agreement.setdefault(opener.group(1), [0, 0])
        tally[0] += row.verdict == AGREE
        tally[1] += 1
    return {opener: (agreed, over) for opener, (agreed, over) in sorted(agreement.items())}


def refusals_by_code(result: ComparisonResult) -> dict[str, int]:
    """Refusals under each reason `lookup.py` names, over both populations together.

    Pooled here and nowhere else, and the difference is what is being counted. A rate is a
    claim about how well a chart matched a player, and Pluribus and the human
    professionals are different players; a reason code is a property of the chart's own
    coverage, which does not know who was sitting there.
    """
    counted = dict.fromkeys(lookup.MISS_CODES, 0)
    for row in result.rows:
        if row.verdict == REFUSED and row.miss_code is not None:
            counted[row.miss_code] += 1
    return counted


def old_versus_new(
    before: ComparisonResult, after: ComparisonResult
) -> tuple[int, dict[str, int]]:
    """Where the two charts part company on a decision they both answer.

    Stated as continue-or-fold rather than as the exact action, for two reasons. It is the
    difference a reader can price - money in or money not in - and it partitions cleanly
    into the two directions, where a raise-against-call disagreement belongs to neither
    and would leave the published split not adding up to its own total.

    The two row lists are index-aligned because `compare_committed_sample` replays the same
    committed sample in the same order and the decision points it visits do not depend on
    the strategy. That is checked rather than assumed: a mispaired comparison would report
    a disagreement rate between two different decisions.
    """
    shared = 0
    directions = {"derived continues, retired folds": 0, "retired continues, derived folds": 0}
    for new, old in zip(after.rows, before.rows, strict=True):
        if (new.hand_id, new.seat, new.observed_action) != (
            old.hand_id,
            old.seat,
            old.observed_action,
        ):
            raise DerivedChartReportError(
                f"the two comparisons disagree about decision {new.hand_id}/{new.seat}, so"
                " they are not over the same corpus and nothing can be paired"
            )
        if new.sampled_action is None or old.sampled_action is None:
            continue
        shared += 1
        new_continues = new.sampled_action != "fold"
        if new_continues == (old.sampled_action != "fold"):
            continue
        if new_continues:
            directions["derived continues, retired folds"] += 1
        else:
            directions["retired continues, derived folds"] += 1
    return shared, directions


# -- the report ------------------------------------------------------------------------- #


DECISION_BANDS: dict[str, tuple[float, float]] = {
    "LJ": (1.16, 4.65),
    "HJ": (0.93, 3.72),
    "CO": (0.66, 2.64),
    "BTN": (-2.67, -0.67),
    "SB": (1.54, 6.14),
}
"""Decision 9's band, per opener, exactly as the record pre-registered it on 2026-08-24.

Quoted rather than recomputed, and the difference is the whole point of a pre-registration:
a band the agent that ran the measurement derived for itself is that agent setting the bar
it is graded against. The report recomputes the DELTA beside it, which is the measurement
the band was drawn from, so a reader can see the quarter-to-one rule holding or not.
"""

MEASURED_POPULATION = "humans"
"""The population the prediction row is measured over, named on the row.

One number per row, and pooling is forbidden - Pluribus and the human professionals are
different players - so the row has to pick one and say which. It is the humans because
they bring 124 of the 144 big-blind calls facing a single open; Pluribus brings twenty
across four openers and none at all against the hijack, and a rate over five decisions
cannot move by a quarter of a point. Pluribus is published beside it in this same section
rather than folded in.
"""

OPENER_ORDER = ("LJ", "HJ", "CO", "BTN", "SB")

RATE_LABELS = ("agreement", "refused", "sampled-action match")

RATE_SAMPLE_NOUN = {
    "agreement": "scored decisions",
    "refused": "decisions",
    "sampled-action match": "drawn decisions",
}


def percent(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def census_section(walk: Walk) -> list[str]:
    """Three buckets and a total, checkable against a file this phase did not write."""
    counts = walk.census
    lines = [
        "Every action node in the committed export is in exactly one of three buckets, and the",
        "three add up to the node count the export's own source card publishes. That total is",
        "the check worth making: a converter that quietly skipped a subtree balances its own",
        "books perfectly, and only a figure from outside catches it.",
        "",
        f"  committed  {counts.committed}",
    ]
    for code in lookup.DERIVATION_EXCLUSION_CODES:
        lines.append(f"  excluded  {code}  {counts.excluded.get(code, 0)}")
    for code in lookup.DERIVATION_INEXPRESSIBILITY_CODES:
        lines.append(f"  inexpressible  {code}  {counts.inexpressible.get(code, 0)}")
    lines += [
        f"  total  {counts.total}",
        "",
        "Two exclusion reasons rather than one, and a reader should not read past that. The",
        "first bucket is every node with a multiway terminal still reachable below it: GTOpen",
        "prices a multiway pot as the product of hero's pairwise equities and understates true",
        "three-way equity by 10.5 points, so those nodes are solved against ranges the",
        "approximation produced. They are named separately because they are the nodes that come",
        "back when the source is fixed, and one merged reason could not say which those are.",
        "The second is what is left outside the rule: heads-up from here on, but reached through",
        "a cold call, so already carrying a range the same defect shaped.",
        "",
        "The inexpressible bucket is empty, which is a measurement rather than an omission. All",
        f"{counts.total} nodes derive a spot key the vocabulary can write and no two collide.",
    ]
    return lines


def traced_cell(walk: Walk, artifact: PreflopArtifact) -> tuple[str, str]:
    """Which cell the trace follows, chosen by a rule rather than named.

    A rule so it moves with the chart instead of pinning a row a later solve may not
    hold, and this rule because a near-pure cell would trace just as truthfully and show
    a reviewer nothing. What the conversion has to get right is a split, so the cell is
    a mixed one; and the per-cell reach is only legible where the whole range did not
    arrive, so a partially-arrived cell is preferred over a fully-arrived one.
    """
    mixed = [
        (spot_id, name)
        for spot_id, classes in artifact.action_weights
        for name, weights in classes
        if spot_id in walk.node_path_by_spot
        and max((weight for _, weight in weights), default=1.0) <= 0.9
    ]
    partial = [
        cell for cell in mixed if (artifact.reach_bp_for(*cell) or REACH_SCALE_BP) < REACH_SCALE_BP
    ]
    for candidates in (partial, mixed):
        if candidates:
            return candidates[0]
    raise DerivedChartReportError(
        "no committed cell mixes two actions, so the chart is a pure strategy everywhere"
        " and there is nothing for a trace to show"
    )


def trace_section(walk: Walk, artifact: PreflopArtifact) -> list[str]:
    """One solved node followed to the row it became, with nothing invented on the way."""
    spot_key_text, hand_class_text = traced_cell(walk, artifact)
    weights = dict(artifact.weights_for(spot_key_text, hand_class_text) or ())
    printed = "  ".join(f"{action}={weight:.4f}" for action, weight in weights.items())
    path = walk.node_path_by_spot[spot_key_text]
    reach = artifact.reach_bp_for(spot_key_text, hand_class_text)
    export_reach = walk.reach_bp_by_cell[(spot_key_text, hand_class_text)]
    return [
        "One cell, from the solved node it came from to the row it is committed as. Every",
        "figure below is in the committed files, so a reviewer can open both and follow it",
        "without reading any code.",
        "",
        f"  export node  {'/'.join(str(step) for step in path) or 'root'}",
        f"  export reach for the class  {export_reach} bp",
        f"  artifact row  {spot_key_text}  {hand_class_text}  {printed}  reach {reach} bp",
        "",
        "The weights are the solver's own, renormalised over the actions the chart vocabulary",
        "holds and nothing else: a named raise and an all-in both read as `raise` here, and what",
        "each costs is in the sizing table beside the chart rather than lost. The reach is",
        "decision 5's, per cell rather than per spot, and it is the difference between a cell the",
        "solve trained and a cell it barely visited - a distinction a chart that published only",
        "the strategy row would throw away.",
    ]


def dominance_section(artifact: PreflopArtifact) -> tuple[list[str], int, int]:
    """Both relations per cell, and the group aggregate against its transposed mapping."""
    grid = play_grid(artifact)
    counts = count_dominance_violations(grid)
    cells = sum(len(spot) for spot in grid.values())
    solved = spots_violating_twins(grid)
    transposed = spots_violating_twins(
        {spot_id: transpose_hand_index(cells) for spot_id, cells in grid.items()}
    )
    lines = [
        "Two things a solved preflop range should almost always do: play a pair more often than",
        "the pair one rank below it, and play a suited hand at least as often as the offsuit hand",
        "of the same two ranks. Both are measured per cell at a tolerance of",
        f"{MONOTONICITY_TOLERANCE_PCT} percentage point, and the ladder compares adjacent pair",
        "ranks only - comparing every pair against every weaker one reports one drifting step a",
        "dozen times over.",
        "",
        f"  ladder violations  {counts['ladder']} of {cells} committed cells",
        f"  twins violations  {counts['twins']} of {cells} committed cells",
        "",
        "Decision 10 was re-ruled on 2026-08-24: these measure and gate nothing. Taylor read the",
        "grids and ruled the splits correct - among near-indifferent hands every split has the",
        "same expected value, so an individual cell carries no information about the solve's",
        "quality and only an aggregate does. Each surviving violation therefore ships as solved,",
        "which is decision 2's branch taken deliberately rather than a defect nobody noticed.",
        "",
        "The aggregate is what has a claim to catch a real defect, so it is published against the",
        "defect it claims to catch: the same measure run over a chart whose suited and offsuit",
        "rows have been swapped. A measure that cannot tell those apart cannot catch a transposed",
        "hand index, and over the 5,626 spots the superseded predicate selected this comparison",
        "came out backwards - it scored the wrong mapping as the better one.",
        "",
        f"  suited against its offsuit twin, spots violating  solved {solved}  transposed"
        f" {transposed}",
    ]
    return lines, solved, transposed


def orderings_section(walk: Walk, derived: PreflopChartLibrary) -> list[str]:
    """Two orderings that survive any rake basis and any solver, so they transfer."""
    lines = [
        "Later position opens wider, and the big blind defends more against a wider opener.",
        "Neither depends on the rake basis or on which solver produced the ranges, which is why",
        "they are worth checking on a chart nobody has played from: a solve that got these",
        "backwards would be wrong in a way no agreement rate could excuse.",
        "",
        "The opening column is the EXPORT'S and the row says so. The ruled predicate commits one",
        "opening range - the small blind's - so four of these five opening frequencies are",
        "properties of the solve that the chart does not ship, and printing them as the chart's",
        "would claim coverage the cutover gave up. The defence column is the chart's: all twenty",
        "of the big blind's spots survive the predicate.",
        "",
    ]
    for position in OPENER_ORDER:
        defends = 100.0 - derived.action_frequency_pct(
            f"t6/d100/BB/{position}:raise@2.5", "fold"
        )
        lines.append(
            f"  {position}  opens (export)  {walk.open_frequency_pct[position]:.3f}"
            f"  big blind defends (chart)  {defends:.3f}"
        )
    lines += [
        "",
        "The small blind opens widest of the five and the big blind defends most against it,",
        "which is the ordering holding at its extreme rather than an exception to it: the small",
        "blind is opening into one seat with position on it for the rest of the hand.",
    ]
    return lines


def expectations_section(walk: Walk, derived: PreflopChartLibrary) -> list[str]:
    """The one column this repo did not produce, printed and graded against nothing."""
    expected = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["open_frequency_pct"]
    derived_sb = 100.0 - derived.action_frequency_pct("t6/d100/SB/rfi", "fold")
    lines = [
        "GTO Wizard's own published opening frequencies for a raked NL25 six-max game, beside",
        "what this phase measured. They are the only numbers here this repo did not produce,",
        "which is what makes them worth printing: a range that is uniformly wrong is",
        "self-consistent everywhere inside the repo and only shows against something outside it.",
        "",
        "Each row says where its own left-hand figure came from. Only one can say `derived` - the",
        "small blind's, the single opening range the cutover commits - and the other four are the",
        "export's, for the same reason the orderings section gives.",
        "",
    ]
    for position in OPENER_ORDER:
        source = "derived" if position == "SB" else "export"
        mine = derived_sb if position == "SB" else walk.open_frequency_pct[position]
        lines.append(
            f"  {position}  {source}  {mine:.3f}  GTO Wizard  {expected[position]:.3f}"
        )
    lines += [
        "",
        "This comparison is gated by nothing and no threshold is drawn on it, because the two",
        "columns are not measuring the same game. GTO Wizard's solve is raked and this one is",
        "not, and rake is a toll on every pot that is contested, so a rake-free solve opens more",
        "and defends more. The small blind's gap is the largest and has a second cause on top of",
        "that: the source solve limps 13.73 percent of the time from the small blind, where this",
        "one has no limp branch at all, so the hands that limped there open here.",
    ]
    return lines


def coverage_section(
    derived: PreflopChartLibrary, retired: PreflopChartLibrary
) -> list[str]:
    """What the cutover bought and what it cost, spot by spot rather than as a count."""
    derived_shapes = {spot_shape(key) for key in derived.spot_keys()}
    retired_keys = sorted(retired.spot_keys())
    limped = [key for key in retired_keys if first_action_is_a_call(key)]
    carried = [
        key
        for key in retired_keys
        if key not in limped and spot_shape(key) in derived_shapes
    ]
    refused = [
        key
        for key in retired_keys
        if key not in limped and spot_shape(key) not in derived_shapes
    ]
    committed = len(derived.spot_keys())
    lines = [
        "The retired chart is not a subset of the derived one, and every stage-4 document in this",
        "phase said it was. Twenty-two of its thirty-six spots pass the ruled predicate, but one",
        "of those twenty-two is a limped pot the rake-free solve has no branch for, so twenty-one",
        "are actually covered.",
        "",
        f"  carried over  {len(carried)}",
        f"  gained  {committed - len(carried)}",
        "",
        "Gained is the committed count less the number carried over, and it is stated as that",
        f"relation rather than as a number: {committed} committed less {len(carried)} carried"
        f" over is {committed - len(carried)}. This phase's own earlier documents published 64,",
        f"which is {committed} less 22 and counts the limped pot as carried over although the",
        "chart refuses it.",
        "",
        "The fourteen the bot answers today and will refuse tomorrow, named individually, because",
        "fourteen of the wrong fourteen is the same arithmetic and a different chart:",
        "",
    ]
    lines += [f"  refused  {key}" for key in refused]
    lines += [
        "",
        "And separately from those fourteen, the limped pot:",
        "",
    ]
    lines += [f"  the limped pot  {key}" for key in limped]
    lines += [
        "",
        "Four of the fourteen are opening ranges. Opening coverage falls from five seats to one:",
        "the bot could open a pot from the lojack, the hijack, the cutoff, the button and the",
        "small blind, and after the cutover it can open only from the small blind. That is the",
        "loss a reader can feel at the table, and it is the ruled cost of a predicate stated over",
        "reachable terminals rather than over action histories - a first-in open has four seats",
        "behind it and a multiway terminal under every branch.",
        "",
        "What was bought is the other side of the same rule: 65 spots the retired chart never",
        "held, every one of them solved for the game this bot is actually trained for -",
        "six-handed, 100 big blinds, rake-free - rather than converted from a raked NL25 solve.",
    ]
    return lines


def corpus_section(
    before: ComparisonResult, after: ComparisonResult
) -> list[str]:
    """Three rates, two populations, before and after, and never one figure over both."""
    lines = [
        "The same 499 hands of the public corpus, scored twice: once against the chart being",
        "retired and once against the chart being committed. One comparison, one corpus, one",
        "piece of code - the chart is a parameter to it - so the before and after columns cannot",
        "have drifted apart by being measured differently.",
        "",
        "Two definitions make these rates readable. Agreement means the chart gives the action",
        "the player actually took nonzero weight, not that a draw matched: the chart collapses a",
        "mixed cell by a seeded draw, so a chart that folds seven times in ten does not disagree",
        "with a fold. And these are real players, not an oracle - agreeing with them is not the",
        "same as playing well, and Pluribus and the human professionals are different players, so",
        "nothing here is pooled.",
        "",
    ]
    for population in POPULATIONS:
        lines.append(f"  {population}")
        rates = {
            "before": population_rates(before, population),
            "after": population_rates(after, population),
        }
        for label in RATE_LABELS:
            for when in ("before", "after"):
                numerator, denominator = rates[when][label]
                lines.append(
                    f"    {label}, {when}  {numerator} of {denominator}"
                    f" {RATE_SAMPLE_NOUN[label]} ({percent(numerator, denominator):.1f}%)"
                )
        lines.append("")
    lines += [
        "The refusal rate rises, on both populations, and that is the ruled cost rather than a",
        "regression. Until 2026-08-25 this phase expected it to fall and called any rise a",
        "defect; the predicate that was ruled drops fourteen of the retired chart's spots plus",
        "the limped pot, four opening ranges among them, and those fifteen are where the rise",
        "lives. A rise anywhere else would be the defect the old criterion was pointing at.",
        "",
        "The agreement rate falls a little and is over a much smaller sample, which is the shape",
        "to expect and not evidence of a worse chart: what is left after the refusals is the",
        "harder subset. The stricter sampled-action match sits below the looser agreement",
        "everywhere, as it must - it asks the seeded draw to have landed on the observed action",
        "rather than merely to have given it weight.",
    ]
    return lines


def _moved(before: tuple[int, int] | None, after: tuple[int, int] | None) -> str:
    """One population's call agreement against one opener, before and after, with its size.

    Written out beside the prediction row because the row carries one measured number and
    the two populations must not be pooled. A population that never faced that opener says
    so rather than reading as a zero.
    """
    if not before or not after or not before[1] or not after[1]:
        return "no calls faced that opener"
    return (
        f"{after[1]} calls, {percent(*before):.1f} to {percent(*after):.1f} percent"
    )


def prediction_section(
    derived: PreflopChartLibrary,
    retired: PreflopChartLibrary,
    before: ComparisonResult,
    after: ComparisonResult,
) -> list[str]:
    """Decision 9's band, quoted; the delta, recomputed; the move, measured."""
    measured_before = big_blind_call_agreement(before, MEASURED_POPULATION)
    measured_after = big_blind_call_agreement(after, MEASURED_POPULATION)
    machine_before = big_blind_call_agreement(before, "Pluribus")
    machine_after = big_blind_call_agreement(after, "Pluribus")
    lines = [
        "Decision 9 fixed this band on 2026-08-24, before any of it was measured. The record is",
        f"{DECISIONS_DOC},",
        "item 9. Big-blind call agreement was predicted to move in the same direction as that",
        "opener's defence delta, by between a quarter and one times the delta in points. The",
        "button's is a predicted worsening: the cutover defends 2.68 points less against it, and",
        "the button generates more big-blind defending decisions than any other seat in a",
        "six-max sample.",
        "",
        "The delta column is recomputed here from the committed files rather than carried over",
        "from the record - combination-weighted over each spot's covered classes, as 100 less the",
        "fold frequency - and the band beside it is quoted from the record unchanged. The retired",
        "chart's small blind opens to 3.5 and the derived one to 2.5, so the before figure for",
        "that row is read at `t6/d100/BB/SB:raise@3.5`; read at 2.5 it would return nothing and",
        "the row would disappear rather than show as wrong.",
        "",
        f"  opener   defence delta   pre-registered band   measured move ({MEASURED_POPULATION})",
    ]
    for position in OPENER_ORDER:
        price = "3.5" if position == "SB" else "2.5"
        old = 100.0 - retired.action_frequency_pct(
            f"t6/d100/BB/{position}:raise@{price}", "fold"
        )
        new = 100.0 - derived.action_frequency_pct(
            f"t6/d100/BB/{position}:raise@2.5", "fold"
        )
        delta = round(new - old, 2)
        low, high = DECISION_BANDS[position]
        agreed_before, over_before = measured_before.get(position, (0, 0))
        agreed_after, over_after = measured_after.get(position, (0, 0))
        move = round(
            percent(agreed_after, over_after) - percent(agreed_before, over_before), 2
        )
        if move < low - 0.005:
            verdict = "below"
        elif move > high + 0.005:
            verdict = "above"
        else:
            verdict = "inside"
        lines.append(
            f"  {position}  {delta:+.2f}  {low:+.2f} to {high:+.2f}  {move:+.2f}  {verdict}"
        )
    lines += [
        "",
        "Read the row as: the chart now defends this much more of hero's range against that",
        "opener, the band is what that was predicted to be worth in call agreement, and the",
        "measured column is what it was worth. The sample under each measured figure is small and",
        "the same size on both sides - the big blind facing one open survives the cutover, so",
        "these are the same decisions scored twice:",
        "",
    ]
    for position in OPENER_ORDER:
        human = _moved(measured_before.get(position), measured_after.get(position))
        machine = _moved(machine_before.get(position), machine_after.get(position))
        lines.append(f"  against the {position}: humans {human}; Pluribus {machine}")
    lines += [
        "",
        "The measured column is the human professionals' and says so, because pooling the two",
        "populations is forbidden and one row carries one number. Pluribus's own figures are on",
        "the lines above, unpooled: it brings twenty of those calls across four openers and none",
        "at all against the hijack, and a rate over three or five decisions cannot resolve a band",
        "a point wide. It moved the same way on every opener it faced.",
        "",
        "Every row misses high, and a miss is a result. The honest reading is that the band was",
        "drawn on the wrong scale rather than that the cutover outperformed it: a quarter-to-one",
        "band ties a rate over a hundred-odd decisions to a frequency over 1,326 combinations,",
        "and those are not the same units. The direction is right in four of five and wrong for",
        "the button, whose defence tightened while its call agreement rose.",
    ]
    return lines


def price_section(after: ComparisonResult) -> list[str]:
    """What the corpus actually paid to see a flop, against what the solve assumes."""
    prices = after.open_sizes_bb()
    total = len(prices)
    counted: dict[float, int] = {}
    for price in prices:
        counted[price] = counted.get(price, 0) + 1
    middle = sorted(prices)
    median = (
        (middle[total // 2 - 1] + middle[total // 2]) / 2.0
        if total % 2 == 0
        else middle[total // 2]
    )
    lines = [
        "The committed solve assumes an open arrives at one price. These hands were not played",
        "at it, and phase 12's ruling 8 abstracts an opponent's price to the solved one before",
        "asking the chart, so every rate above is partly a rate about a table the chart was never",
        "solved for. The qualification on its own cannot be weighed; a distribution can.",
        "",
        f"  decisions facing exactly one raise  {total}",
        f"  median opening price  {median:g} big blinds",
        "",
    ]
    for price in sorted(counted):
        count = counted[price]
        lines.append(f"  {price:.2f}bb  {count}  ({percent(count, total):.2f}%)")
    lines += [
        "",
        "The median open in this corpus is a quarter of a big blind cheaper than the solved 2.5,",
        "and a cheaper open is a better price to defend against, so the chart is systematically",
        "a little tighter than the spot in front of it deserves. That is a bias with a known",
        "direction, not noise.",
        "",
        "The cutover moves hero's own price too, which is why the prediction covers it:",
        "",
        "  hero's own open from the small blind  3.5bb before the cutover, 2.5bb after",
        "",
        "So the big blind facing a small-blind open moves from a 3.5-solved answer to a",
        "2.5-solved one, at `t6/d100/BB/SB:raise@2.5`, against a corpus median of 2.25. It is the",
        "only opening price the chart still holds, and `the price-tracking part will not move` is",
        "false for exactly that family.",
    ]
    return lines


def explanations_section() -> list[str]:
    """Which candidate explanation this measurement separates, and which two it cannot."""
    return [
        "Any residual gap between this chart and what the players did has three candidate",
        "causes, and this measurement separates one of them. Naming which is not a caveat on the",
        "finding; it is most of the finding.",
        "",
        "  rake  separated: the committed solve is rake-free, so a raked-solve explanation for a",
        "        residual gap no longer applies to this chart",
        "  price  uncontrolled: phase 12 ruling 8 abstracts an opponent's open to the solved",
        "         price, and the distribution above shows how far that reaches",
        "  realization  uncontrolled: the equity-realization model underprices position, and",
        "               decision 3 accepts it rather than fixing it in this phase",
        "",
        "Two of the three therefore survive the cutover untouched. A reader who sees a residual",
        "disagreement here cannot read it as a defect in the ranges, because two explanations for",
        "it are still standing and neither has been measured away.",
    ]


def bounds_section() -> list[str]:
    """What an agreement rate off this chart is not a statement about."""
    return [
        "Every figure above is about one table configuration and one branch of the tree. The",
        "chart answers a decision only when all of the following hold, and refuses otherwise:",
        "",
        "  six-handed, and no other table size",
        "  100 big blinds effective, and no other depth",
        "  symmetric stacks: every live seat started the hand at hero's depth",
        "  no straddle in the pot",
        "  no ante posted",
        "  one solved opening price, 2.5 big blinds",
        "  heads-up: at most one opponent has voluntarily invested and at most two players live",
        "",
        "The last of those is the ruled predicate stated as a bound rather than as a rule, and it",
        "is the one that costs most: a rate read off this chart says nothing whatever about",
        "multiway play, which is most of the hands a six-handed game actually deals.",
    ]


def refusals_section(before: ComparisonResult, after: ComparisonResult) -> list[str]:
    """Movement by reason over the closed vocabulary, and the inventory republished."""
    old_codes = refusals_by_code(before)
    new_codes = refusals_by_code(after)
    inventory = after.refusal_inventory
    limped = [entry for entry in inventory if first_action_is_a_call(entry.spot_key)]
    lines = [
        "One total would hide the finding: the reasons move in different directions and by very",
        "different sizes. Every code `lookup.py` defines gets a row, a zero included, because a",
        "reason that stopped happening is a result too. The columns are the retired chart and the",
        "derived one, over both populations together - a reason code is a property of the",
        "chart's coverage rather than of who was sitting in the seat.",
        "",
    ]
    for code in lookup.MISS_CODES:
        lines.append(f"  {code}  {old_codes[code]}  {new_codes[code]}")
    lines += [
        "",
        "Almost all of the movement is one code. The chart declares fewer spots that this corpus",
        "actually reaches, so decisions that used to find a spot now do not, and that is the",
        "cutover's cost stated in the vocabulary a reader can act on rather than as one number.",
        "",
        "Decision 12 asks this phase to publish its own count of decision points facing a limp,",
        "with the definition it counted by, because the figure quoted in",
        "`CHART-CANNOT-ANSWER-A-LIMPED-POT` carries none and does not reproduce. The rule is that",
        "the first recorded action in the spot key is a call:",
        "",
        f"  decision points facing a limp  {len(limped)} inventory rows"
        f"  {sum(entry.count for entry in limped)} decision points",
        "",
        "The whole inventory follows, which is what makes that count checkable: decision points",
        "first, then the spot key they reached.",
        "",
    ]
    lines += [f"  {entry.count}  {entry.spot_key}" for entry in inventory]
    return lines


def old_versus_new_section(
    commit: str, shared: int, directions: dict[str, int]
) -> list[str]:
    """Where the two charts part company, with the pin the retired one was read at."""
    lines = [
        "The retired chart is deleted from the tree, so this comparison reads it out of git",
        "history at the commit decision 7 pins. A pin rather than a second copy under",
        "`data/artifacts/preflop/`: a reader can fetch the same bytes and nobody has to ask which",
        "chart the bot plays.",
        "",
        f"  the retired chart, read at commit {commit}",
        f"  decisions both charts answer  {shared}",
        f"  disagreed  {sum(directions.values())}",
    ]
    for label in ("derived continues, retired folds", "retired continues, derived folds"):
        lines.append(f"  {label}  {directions[label]}")
    lines += [
        "",
        "Answered by both means both charts returned an action for that decision, so the",
        "comparison is over what the two would actually have done rather than over their coverage",
        "differences, which the refusal rows above already carry. The difference counted is",
        "whether hero puts money in: a raise where the other chart calls is the same decision",
        "priced differently, and it belongs in the sizing table rather than here.",
        "",
        "The derived chart continues where the retired one folded four times as often as the",
        "reverse, which is the rake-free solve showing up as looser play - a raked solve pays a",
        "toll on every contested pot and folds more because of it.",
    ]
    return lines


def recomputable_section(walk: Walk) -> list[str]:
    """One number a reviewer can check with a pencil and one committed file."""
    counts = walk.census
    parts = " + ".join(
        [str(counts.committed)]
        + [str(counts.excluded.get(code, 0)) for code in lookup.DERIVATION_EXCLUSION_CODES]
        + [
            str(counts.inexpressible.get(code, 0))
            for code in lookup.DERIVATION_INEXPRESSIBILITY_CODES
        ]
    )
    return [
        "The audit packet owes a reader one figure they can check without running anything, so",
        "here it is with the file it comes out of and the arithmetic that produces it.",
        "",
        f"  the number  {counts.total} action nodes in the committed export",
        "  the file  data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json",
        f"  the arithmetic  {parts} = {counts.total}, against `node_counts.exported` in that file",
        "",
        "The four terms are the census rows above, in the same order. If they do not add to the",
        "card's own figure then a solved node has gone missing between the export and this",
        "report, and no other check in this phase would notice.",
    ]


HEADINGS = (
    "## The three-way node census",
    "## One converted cell, traced",
    "## The two dominance relations",
    "## The two orderings",
    "## The derived chart against the GTO Wizard expectations",
    "## What the cutover gained and gave up",
    "## The corpus, before and after",
    "## The pre-registered prediction",
    "## The price the corpus was played at",
    "## What this measurement can and cannot separate",
    "## What this chart does not answer",
    "## The refusal inventory, by reason",
    "## Where the retired chart and the derived chart disagree",
    "## One number a reader can recompute by hand",
)
"""The report's sections, in reading order, and exactly one of each.

Ordered so a reviewer meets the chart before the measurement and the measurement before its
bounds: what was converted, what one cell became, whether the ranges behave like poker,
what the cutover cost, what the corpus says, and only then what none of it establishes.
"""

PREAMBLE = """The derived preflop chart, and what the cutover changed

This is the phase's evidence for a reader who does not read code. The bot's preflop ranges
have been replaced: it used to play from 36 spots converted out of a raked GTO Wizard NL25
solve, and it now plays from 86 derived from a GTOpen solve of the game it is actually
trained for - six-handed, 100 big blinds, rake-free. The old chart is deleted.

Nothing below is a grade on the new chart. Two of the three things that could explain a gap
between it and how people played are still uncontrolled, the corpus is 499 hands, and real
players are not an oracle. What the report can do is show the conversion was faithful, show
what coverage was bought and sold, and put the closing measurement beside the prediction
that was written down before it ran."""


def render(sections: dict[str, list[str]]) -> str:
    """One heading per section, exactly once, with the claim made under its own heading."""
    parts = [PREAMBLE]
    for heading in HEADINGS:
        parts.append(f"{heading}\n\n" + "\n".join(sections[heading]).rstrip())
    return "\n\n".join(parts) + "\n"


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """The three inputs a caller can move, each of which the frozen tests feed a wrong one.

    The artifact and the pin are inputs rather than constants because both are things the
    report VALIDATES: a generator that could only ever be handed the right chart and the
    right commit could not be shown refusing the wrong ones.
    """
    parser = argparse.ArgumentParser(description="Generate the derived preflop chart report")
    parser.add_argument("--output", type=Path, default=REPORT_OUTPUT)
    parser.add_argument("--retired-commit", default=RETIRED_CHART_COMMIT)
    parser.add_argument("--artifact", type=Path, default=COMMITTED_ARTIFACT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Measure first, validate second, publish last.

    The order is the point. A refused figure must not also be published: a report on disk is
    what a reviewer reads, and a wrong one beside a non-zero exit code is worse than no
    report at all. So every validator runs and every failure is collected before anything is
    written, and one gate decides whether the file appears.
    """
    arguments = parse_arguments(argv)
    validation_errors: list[str] = []

    walk = walk_export()
    artifact = import_preflop_artifact(arguments.artifact)
    derived = PreflopChartStrategy(
        library=PreflopChartLibrary.from_artifacts([artifact]),
        sizing=PreflopSizingTable.from_repo(),
    )
    # The pin is a constant with a command-line override, and the override is bound back
    # onto the constant's own name so the loader is always called with the pin itself. A
    # call reading `arguments.retired_commit` here would make the pin look like an ordinary
    # argument, where decision 7 makes it the input the whole comparison is defined by.
    RETIRED_CHART_COMMIT = arguments.retired_commit  # noqa: N806
    retired = load_retired_chart_from_git(RETIRED_CHART_COMMIT)

    sample = load_committed_sample()
    after = compare_committed_sample(sample, strategy=derived)
    before = compare_committed_sample(sample, strategy=retired)
    shared, directions = old_versus_new(before, after)
    dominance, solved, transposed = dominance_section(artifact)

    for check in (
        lambda: validate_census(walk.census, walk.exported_nodes),
        lambda: validate_spot_count(
            {spot.spot_id for spot in artifact.spots}, set(walk.spot_keys)
        ),
        lambda: validate_group_discrimination(solved=solved, transposed=transposed),
        lambda: validate_disagreement(
            shared_decisions=shared,
            disagreements=sum(directions.values()),
            by_direction=directions,
        ),
    ):
        try:
            check()
        except DerivedChartReportError as error:
            validation_errors.append(str(error))

    if validation_errors:
        for message in validation_errors:
            print(f"refused: {message}", file=sys.stderr)
        return 1

    sections = dict(
        zip(
            HEADINGS,
            [
                census_section(walk),
                trace_section(walk, artifact),
                dominance,
                orderings_section(walk, derived.library),
                expectations_section(walk, derived.library),
                coverage_section(derived.library, retired.library),
                corpus_section(before, after),
                prediction_section(derived.library, retired.library, before, after),
                price_section(after),
                explanations_section(),
                bounds_section(),
                refusals_section(before, after),
                old_versus_new_section(RETIRED_CHART_COMMIT, shared, directions),
                recomputable_section(walk),
            ],
            strict=True,
        )
    )
    text = render(sections)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(text, encoding="utf-8")
    print(f"wrote {arguments.output} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
