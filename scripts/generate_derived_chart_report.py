"""The derived preflop chart, written for a reviewer who does not read code.

The chart itself is `solver_artifacts.chart_derivation`'s subject and the artifact is committed;
this script is where a person is led to a conclusion about it. That is a separate job from the
chart being right, which is why it is a separate file: a report renders whatever it is handed, so
a census that does not add up, a spot count that disagrees with the walk that produced it, or an
arm whose counterfactual scores better than the solved index would publish exactly as happily as
the right numbers would.

So every figure the contract names as an obligation is **re-derived here and printed**, and the
command exits non-zero and writes nothing when one does not hold. Nothing below is hand-typed
that the export, the artifact or the report's own columns could tell us instead
(`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`, which this phase has now traced seven
separate defects to).

**The rules are not re-implemented here.** `chart_selection` owns which nodes are committed,
`chart_derivation` owns what each becomes, and `chart_relations` owns the four relations and both
counterfactual arms. Every one of those names is imported rather than copied, because two
definitions of one relation is how seven readings of the same prose produced seven counts.

**What gates and what does not.** The two arms gate, on all ten partitions, both strict with a tie
refusing. The census, the spot set and the old-versus-new disagreement gate. The four relations,
the group-order ladders, the equity relation and the expectations comparison are measured and gate
nothing, and each says so where it is printed - a published count read as a check that passed is
the failure the vacuous labels below exist to stop.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
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
    COMMITTED_RAISE_DEPTH,
    MULTIWAY_EXPOSURE_THRESHOLD_PCT,
    NodeCensus,
    census,
    exclusion_code,
    is_committed_node,
    merged_cells,
    merges_the_cold_call,
    multiway_exposure_pct,
    node_spot_key,
    raises_faced,
    terminal_split_pct,
)
from poker_training_bot.solver_artifacts.chart_relations import (  # noqa: E402
    ADJACENT_PAIRS,
    COMPARISONS,
    RANK_ARM_SPOT_FLOOR,
    RELATIONS,
    ROW_COMPARISONS_PER_FULL_GRID,
    ROW_KICKERS,
    SUITED_OVER_OFFSUIT,
    TOLERANCE_PCT,
    arm_refuses,
    cells_violating_rows,
    count_dominance_violations,
    dominance_inversions,
    inversions,
    is_closed_under_reversal,
    reverse_hand_ranks,
    reverse_rank,
    row_comparisons_skipped,
    spots_violating_twins,
    transpose_hand_index,
)
from poker_training_bot.solver_artifacts.gtopen_export import (  # noqa: E402
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    class_combos,
    gtopen_class_index,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES  # noqa: E402
from poker_training_bot.solver_artifacts.importer import import_preflop_artifact  # noqa: E402
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary  # noqa: E402
from poker_training_bot.solver_artifacts.schema import PreflopArtifact  # noqa: E402
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy  # noqa: E402
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable  # noqa: E402

__all__ = [
    "ADJACENT_PAIRS",
    "COMPARISONS",
    "MONOTONICITY_TOLERANCE_PCT",
    "RANK_ARM_SPOT_FLOOR",
    "RELATIONS",
    "ROW_COMPARISONS_PER_FULL_GRID",
    "ROW_KICKERS",
    "SUITED_OVER_OFFSUIT",
    "DerivedChartReportError",
    "arm_refuses",
    "cells_violating_rows",
    "count_dominance_violations",
    "dominance_inversions",
    "inversions",
    "is_closed_under_reversal",
    "main",
    "play_grid",
    "raise_weight_grid",
    "reverse_hand_ranks",
    "reverse_rank",
    "row_comparisons_skipped",
    "spots_violating_twins",
    "transpose_hand_index",
    "validate_census",
    "validate_disagreement",
    "validate_group_discrimination",
    "validate_rank_discrimination",
    "validate_spot_count",
]
"""The names this module publishes, the relation and arm functions among them.

They are **re-exports and not copies**. The generator used to carry its own one-argument
`count_dominance_violations` and its own `transpose_hand_index`, which is two definitions of one
rule and the way the two come to disagree; the definitions now live once in `chart_relations` and
this module is where a caller reaches them by the names the report is written in.
"""

REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_derived_chart_report.txt"

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"

COMMITTED_ARTIFACT = ARTIFACT_DIR / "six_max_100bb_rakefree.json"

EXPECTATIONS_NAME = "six_max_nl25_100bb"

EXPECTATIONS = ARTIFACT_DIR / "expectations" / f"{EXPECTATIONS_NAME}.json"

SOURCE_CARD_NAME = "data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json"

DECISIONS_DOC = "reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md"

MONOTONICITY_TOLERANCE_PCT = TOLERANCE_PCT
"""Decision 10's tolerance, in points, and an **alias** rather than a second literal.

The value lives in `chart_relations` beside the relations it belongs to. A copy here would be a
second place to change it, and the whole reason that module exists is that this repo has already
published seven counts of one chart from seven readings of one paragraph.
"""

RETIRED_CHART_PATH = "data/artifacts/preflop/six_max_100bb_rakefree.json"

RETIRED_SIZING_PATH = "data/artifacts/preflop/sizings/six_max_100bb_rakefree.json"

RETIRED_CHART_COMMIT = "6f157247cf2217acf358d7cef901a550fc4aae69"
"""The last commit at which the chart this phase retires is in the tree, with its sizing table.

**The retired chart is the 86-spot `six_max_100bb_rakefree.json`**, not the GTO Wizard NL25 chart,
which was deleted before this phase restarted and which no ledger here balances against. Read out
of git history rather than kept as a second copy under `data/artifacts/preflop/`, which is the
arrangement that makes a reader ask which chart the bot plays - the one confusion this phase
exists to end. A pin makes the comparison reproducible: anybody can fetch the same bytes and
recount the 86 spots and the 36 sizing entries, every one of them priced at a jam.
"""

EQUITY_MATRIX_PATH = ARTIFACT_DIR / "equity" / "preflop_eq169.bin"
"""The 169-by-169 preflop all-in equity matrix the contract requires to be committed.

Not a model constant and not a threshold: it is a table of the game's own arithmetic,
deterministic and regenerable, and the equity relation below is the one measurement in this report
that no other committed file can produce. When it is absent the command refuses, rather than
publishing a firing count nobody measured.
"""

OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")

SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")

PURE_PCT = 99.0
"""A cell is pure when one action carries at least this much of it, in points."""

MIXED_PCT = 90.0
"""A cell is mixed when no action carries this much of it, in points."""

WHEEL_ACE_KICKERS = ("A5", "A4", "A3", "A2")
"""A suited wheel ace makes the nut straight and is less dominated than a middling suited ace, so
an ace row playing `A5s` over `A6s` is correct poker rather than an accepted defect. Counting the
kicker family whole overstates what is wrong with the chart by about half."""

WIDE_KICKER_GAP_PCT = 50.0
"""Where the kicker cases with no poker story are split, in points. The two sizes are published
apart because a fifty-point inversion and a two-point one are not the same finding."""


class DerivedChartReportError(RuntimeError):
    """A figure the report would have published that does not hold, or an input it needs.

    Raised rather than printed, and every raise is collected into one list so a reviewer reads
    every broken figure at once instead of fixing them one command at a time.
    """


# -- the validated figures ----------------------------------------------------------------- #


def validate_census(census_counts: NodeCensus, exported_nodes: int) -> None:
    """Every solved node in exactly one bucket, under a reason somebody ruled.

    Three things are checked and each has a way of failing that arithmetic alone misses. The
    buckets have to sum to the export's own node count, or the census is a subset dressed as a
    census - a converter that skipped a subtree balances its own books perfectly. Every reason has
    to be in `lookup.py`'s closed vocabulary, or a node the converter merely failed to handle gets
    filed as a property of the spot grammar. And **all three** exclusion reasons have to appear,
    because each names a different way back: the multiway family returns when GTOpen can price a
    multiway pot, the big blind's squeeze spots when the flats are repaired, and everything beyond
    the committed raise depth when a later phase takes up the four-bet. A census folding two of
    them together **balances exactly** and is wrong only about which fix brings which back, which
    is the one failure a total can never see.
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
            f"the census publishes no excluded nodes under {missing}; a folded code cannot say"
            " which nodes come back when which defect is fixed"
        )
    for code in census_counts.inexpressible:
        if code not in lookup.DERIVATION_INEXPRESSIBILITY_CODES:
            raise DerivedChartReportError(
                f"the census calls nodes inexpressible under {code!r}, which is not one of"
                f" the ruled reasons {list(lookup.DERIVATION_INEXPRESSIBILITY_CODES)}"
            )


def validate_spot_count(artifact_keys: set[str], walked_keys: set[str]) -> None:
    """The committed spot set against the walk's, key by key rather than by count.

    Counting cannot catch this: a converter that dropped one node and invented one key gives the
    same total. So both directions are named, and the invented direction is the one a converter
    built on a superseded predicate fails - it commits a spot the exposure clause refuses, or one
    of the ten big-blind squeeze spots, or one beyond the committed raise depth, and the message
    says which key rather than only that the count moved.
    """
    invented = sorted(artifact_keys - walked_keys)
    dropped = sorted(walked_keys - artifact_keys)
    if invented or dropped:
        raise DerivedChartReportError(
            f"the artifact's {len(artifact_keys)} spots disagree with the walk's"
            f" {len(walked_keys)}: it invents {invented} and drops {dropped}"
        )


def validate_group_discrimination(solved: int, transposed: int) -> None:
    """The suit arm: the solved hand index must flag strictly fewer spots than the transposed one.

    What is asserted is the direction and never the counts, since fixing a count picks the
    partition that reads smallest and calls that the gate. Over an earlier committed set this
    comparison came out backwards - 2,007 spots flagged under the solved mapping against 818 under
    the mapping with suited and offsuit swapped - so the measure scored the defect it exists to
    catch as the better reading. A tie refuses too: a measure that cannot tell the two mappings
    apart cannot catch a transposed index.
    """
    if arm_refuses(solved, transposed):
        raise DerivedChartReportError(
            f"the suit arm flags {solved} spots under the solved hand index and {transposed}"
            " under the index with every suited hand read off its offsuit twin, so it does not"
            " discriminate between them and cannot catch a transposed index"
        )


def validate_rank_discrimination(solved: int, permuted: int) -> None:
    """The rank arm, and it is a second function rather than a second call.

    `validate_group_discrimination` takes `solved` and `transposed`; this one takes `solved` and
    `permuted`. Two names because this repo has already lost a day to two different "transposed"
    counterfactuals being confused, and passing a rank-permutation count into a parameter called
    `transposed` is that confusion written into the call site. The rule is the same and a tie
    refuses on each.
    """
    if arm_refuses(solved, permuted):
        raise DerivedChartReportError(
            f"the rank arm flags {solved} row comparisons under the solved hand index and"
            f" {permuted} under the index with every rank reversed, so it does not discriminate"
            " between them and cannot catch a hand index read upside down"
        )


def validate_disagreement(
    *, shared_decisions: int, disagreements: int, by_direction: Mapping[str, int]
) -> None:
    """The old-versus-new count, checked for having happened at all.

    A comparison that quietly became trivial arrives as a small consistent number rather than as
    an error, which is why the arithmetic is not enough on its own. An empty overlap is refused,
    and so is a zero disagreement count over a non-empty overlap: that is the shape of the
    comparison being handed the same chart twice, and the poker rules it out on its own terms,
    because the retired chart's sizing entries are every one priced at a jam where the derived
    chart offers 2.5, 7.5 and 22.5 and no jam at all.
    """
    if shared_decisions <= 0:
        raise DerivedChartReportError(
            "the two charts share no corpus decision, so there is nothing to disagree about"
            " and the overlap was never measured"
        )
    if disagreements == 0:
        raise DerivedChartReportError(
            f"the two charts agree on all {shared_decisions} shared decisions; the retired chart"
            " prices every one of its sizing entries at a jam the derived chart cannot offer, so"
            " a zero here is a comparison handed the same chart twice rather than a measurement"
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


# -- the grids every measurement is stated over --------------------------------------------- #


def cell_weights(artifact: PreflopArtifact) -> dict[str, dict[str, dict[str, float]]]:
    """The artifact's own rows, as spot to hand class to action to weight."""
    return {
        spot_id: {name: dict(actions) for name, actions in classes}
        for spot_id, classes in artifact.action_weights
    }


def play_grid(artifact: PreflopArtifact) -> dict[str, dict[str, float]]:
    """How often each committed cell puts money in, in points.

    Three of the four relations and both arms are stated over this. One number per cell rather
    than a distribution, because a stronger hand raising where a weaker one calls is not an
    inversion - both continue. What breaks a relation is the stronger hand folding more.
    """
    return {
        spot_id: {
            name: 100.0 * (1.0 - actions.get("fold", 0.0)) for name, actions in classes.items()
        }
        for spot_id, classes in cell_weights(artifact).items()
    }


def raise_weight_grid(artifact: PreflopArtifact) -> dict[str, dict[str, float]]:
    """How often each committed cell raises **in the published chart**, in points.

    The fourth relation's grid, and the reason it exists: at the merged spots this is the solve's
    raise plus its cold call, because that is the action the bot takes there, and the inversion
    that halted this phase sits at cells where both hands are played 100 percent and only this
    split differs.
    """
    return {
        spot_id: {name: 100.0 * actions.get("raise", 0.0) for name, actions in classes.items()}
        for spot_id, classes in cell_weights(artifact).items()
    }


def reach_weights(artifact: PreflopArtifact) -> dict[str, dict[str, float]]:
    """How much of hero's arriving range each cell is: combinations times arriving reach.

    Combinations because there are twelve ways to hold an offsuit hand and four to hold its suited
    twin, and reach because a hand hero folded three actions ago still carries a full strategy row
    in the payload. A frequency weighted by neither is a mean over grid squares rather than over
    hands.
    """
    return {
        spot_id: {name: float(class_combos(name) * reach) for name, reach in dict(cells).items()}
        for spot_id, cells in artifact.arriving_reach_bp
    }


def weighted(values: Mapping[str, float], weights: Mapping[str, float]) -> float:
    """One spot's frequency over hero's arriving range."""
    total = sum(weights.get(name, 0.0) for name in values)
    if not total:
        return 0.0
    return sum(values[name] * weights.get(name, 0.0) for name in values) / total


def spot_frequencies(artifact: PreflopArtifact, action: str) -> dict[str, float]:
    """Each committed spot's combination-weighted frequency for one action, in points.

    `play` is read as the complement of the fold so that "defends" and "opens" are one measurement
    rather than two, and every column in this report saying how wide a range is comes from here.
    """
    weights = reach_weights(artifact)
    found: dict[str, float] = {}
    for spot_id, classes in cell_weights(artifact).items():
        if action == "play":
            values = {name: 100.0 * (1.0 - a.get("fold", 0.0)) for name, a in classes.items()}
        else:
            values = {name: 100.0 * a.get(action, 0.0) for name, a in classes.items()}
        found[spot_id] = weighted(values, weights[spot_id])
    return found


def hero_seat(spot_key_text: str) -> str:
    """The seat hero sits in, read off the key rather than off the declared field, so a spot whose
    key and whose declared seat disagree is visible from the report."""
    return spot_key_text.split("/")[2]


def raises_faced_in_key(spot_key_text: str) -> int:
    """How many raises are already in the pot hero is being asked about, read off the key."""
    history = spot_key_text.split("/", 3)[3]
    return 0 if history == "rfi" else history.count(":raise@")


def partitions(spot_keys: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """The ten partitions both arms run on: the whole set, one per hero seat, one per raises
    faced. Built from the committed keys, so a partition that vanished is a missing row rather
    than a silence, and dropping one is forbidden."""
    found: dict[str, list[str]] = {"the committed set": []}
    for key in spot_keys:
        found["the committed set"].append(key)
        for label in (f"hero={hero_seat(key)}", f"raises faced {raises_faced_in_key(key)}"):
            found.setdefault(label, []).append(key)
    return {label: tuple(keys) for label, keys in found.items()}


@dataclass(frozen=True)
class ArmFigures:
    """What both arms read on one partition, and what the rank arm could not look at."""

    label: str
    spots: int
    suit_solved: int
    suit_transposed: int
    rank_solved: int
    rank_permuted: int
    rank_scored_spots: int
    rank_skipped: int
    rank_skipped_permuted: int

    @property
    def asserted(self) -> bool:
        """Below the floor a strict comparison over one or two grids is a coin flip, so the
        partition publishes rather than asserts and the row says which."""
        return self.rank_scored_spots >= RANK_ARM_SPOT_FLOOR


def arm_figures(label: str, part: Mapping[str, Mapping[str, float]]) -> ArmFigures:
    """Both arms over one partition, scored through the functions that ship.

    The rank arm scores **every spot** and skips the comparisons whose partner cell is absent,
    `reverse_hand_ranks` being total only on a full grid. What it skipped is counted on each side
    because the two sides skip different comparisons - the reversal carries a present cell onto a
    different row - and one number standing for both is exactly how the withdrawn "149 against 69"
    was built, out of the solved side of one rule and the counterfactual side of another.
    """
    swapped = {key: transpose_hand_index(cells) for key, cells in part.items()}
    reversed_part = {key: reverse_hand_ranks(cells) for key, cells in part.items()}
    return ArmFigures(
        label=label,
        spots=len(part),
        suit_solved=spots_violating_twins(part),
        suit_transposed=spots_violating_twins(swapped),
        rank_solved=cells_violating_rows(part),
        rank_permuted=cells_violating_rows(reversed_part),
        rank_scored_spots=sum(
            1
            for cells in part.values()
            if row_comparisons_skipped(cells) < ROW_COMPARISONS_PER_FULL_GRID
        ),
        rank_skipped=sum(row_comparisons_skipped(cells) for cells in part.values()),
        rank_skipped_permuted=sum(
            row_comparisons_skipped(cells) for cells in reversed_part.values()
        ),
    )


def relation_findings(
    play: Mapping[str, Mapping[str, float]], raise_weight: Mapping[str, Mapping[str, float]]
) -> dict[str, list[tuple[str, str, str, float, float]]]:
    """Every case the four relations find, carrying the spot each was found at.

    `chart_relations.dominance_inversions` returns the same rows without the key, which is what a
    count needs and not what a worst case needs - a reader cannot open a grid nobody named. So the
    walk is repeated here over that module's own comparison lists, and the counts are checked
    against its own below, which is what makes this a second reading of one rule rather than a
    second rule.
    """
    found: dict[str, list[tuple[str, str, str, float, float]]] = {}
    for relation in RELATIONS:
        chart = raise_weight if relation.measure == "raise-weight" else play
        rows: list[tuple[str, str, str, float, float]] = []
        for spot_id, cells in chart.items():
            for stronger, weaker, high, low in inversions(cells, COMPARISONS[relation.name]):
                rows.append((spot_id, stronger, weaker, high, low))
        found[relation.name] = rows
    return found


def relation_coverage(
    play: Mapping[str, Mapping[str, float]], raise_weight: Mapping[str, Mapping[str, float]]
) -> dict[str, tuple[int, int]]:
    """Per relation, the comparisons the committed grids actually offered and the ones skipped.

    Published beside every count because a relation measured over a grid that arrived at four hand
    classes has looked at almost nothing, and a reader given only "0 of 2,988" cannot tell that
    from a clean chart.
    """
    coverage: dict[str, tuple[int, int]] = {}
    for relation in RELATIONS:
        chart = raise_weight if relation.measure == "raise-weight" else play
        pairs = COMPARISONS[relation.name]
        compared = sum(
            1 for cells in chart.values() for pair in pairs if all(n in cells for n in pair)
        )
        coverage[relation.name] = (compared, len(pairs) * len(chart) - compared)
    return coverage


def kicker_split(play: Mapping[str, Mapping[str, float]]) -> tuple[int, int, int]:
    """The kicker family in three, because one count overstates the defect by about half.

    A wheel-ace case is an ace row where the hand played more often is `A5`, `A4`, `A3` or `A2`:
    the nut-straight ace is less dominated than a middling suited one, GTOpen's own fit measures
    the premium, and it is correct poker rather than a defect. The rest are split at a fifty-point
    gap, a fifty-point inversion and a two-point one being different findings.
    """
    wheel = wide = narrow = 0
    for cells in play.values():
        for stronger, weaker, high, low in inversions(cells, ROW_KICKERS):
            if stronger[0] == "A" and weaker[:2] in WHEEL_ACE_KICKERS:
                wheel += 1
            elif low - high >= WIDE_KICKER_GAP_PCT:
                wide += 1
            else:
                narrow += 1
    return wheel, wide, narrow


def raise_inversions_invisible(
    play: Mapping[str, Mapping[str, float]], raise_weight: Mapping[str, Mapping[str, float]]
) -> int:
    """Pair inversions on the raise weight that play-not-fold cannot see at all.

    The whole reason the fourth relation was added: at the cells that halted this phase both hands
    are played 100 percent, so every relation stated over play-not-fold reads nothing there.
    """
    invisible = 0
    for spot_id, cells in raise_weight.items():
        for stronger, weaker, _, _ in inversions(cells, ADJACENT_PAIRS):
            if not inversions(play[spot_id], ((stronger, weaker),)):
                invisible += 1
    return invisible


def purity(cells: Mapping[str, Mapping[str, Mapping[str, float]]]) -> tuple[int, float, float]:
    """How much a grid mixes: cells, the share pure at 99 percent, the share mixed below 90.

    It is what makes the merged flats a real cost rather than a relabelling. Had the solve been
    near-indifferent at the cells the merge moved, "the solver did not care, take the other
    action" would have been available to it; it barely mixes, so it was not.
    """
    total = pure = mixed = 0
    for classes in cells.values():
        for actions in classes.values():
            total += 1
            highest = 100.0 * max(actions.values())
            pure += highest >= PURE_PCT
            mixed += highest < MIXED_PCT
    if not total:
        return (0, 0.0, 0.0)
    return (total, 100.0 * pure / total, 100.0 * mixed / total)


def _group_ladders() -> dict[str, tuple[tuple[str, ...], ...]]:
    """The group orderings a human reads, built from the rank order the relations use."""
    ranks = "AKQJT98765432"
    high_to_low = tuple(f"{rank}{rank}" for rank in ranks)
    return {
        "pairs, 13 single ranks": tuple((pair,) for pair in high_to_low),
        "pairs, 4 bands": tuple(high_to_low[start : start + 3] for start in (0, 3, 6, 9)),
        "pairs, 3 bands": tuple(high_to_low[start : start + 4] for start in (0, 4, 8)),
        "pairs, 2 bands": (high_to_low[:6], high_to_low[6:]),
        "suited rows": tuple(
            tuple(f"{high}{low}s" for low in ranks[index + 1 :])
            for index, high in enumerate(ranks[:-1])
        ),
    }


GROUP_LADDERS = _group_ladders()


def ladder_flags(
    chart: Mapping[str, Mapping[str, float]],
    weights: Mapping[str, Mapping[str, float]],
    groups: Sequence[Sequence[str]],
) -> int:
    """Spots whose group frequencies fall out of order by more than the tolerance."""
    flagged = 0
    for spot_id, cells in chart.items():
        values = []
        for group in groups:
            present = {name: cells[name] for name in group if name in cells}
            if present:
                values.append(weighted(present, weights[spot_id]))
        flagged += any(
            high < low - TOLERANCE_PCT for high, low in zip(values, values[1:], strict=False)
        )
    return flagged


# -- the export walk, which is where a converter's silence becomes a number ------------------ #


@dataclass(frozen=True)
class Walk:
    """One walk of the committed export, shared by every section that measures it.

    Re-derived here rather than read back off the artifact. The report's job is to compare the
    two, and a section that read the committed spot set and called it the walk's would agree with
    itself whatever the converter did.
    """

    census: NodeCensus
    spot_keys: frozenset[str]
    exported_nodes: int
    coverage_pct: float
    node_path_by_spot: dict[str, tuple[int, ...]]
    reach_bp_by_cell: dict[tuple[str, str], int]
    splits: dict[str, tuple[float, float, float]]
    widest_admitted: tuple[str, float]
    narrowest_refused: tuple[str, float]
    hero_closes: frozenset[str]
    solve_purity: tuple[int, float, float]
    solve_raise_plus_call: dict[str, float]
    merged_spot_keys: frozenset[str]
    merged_cell_count: int
    arrivals: dict[str, float]
    jam: tuple[str, str, float]


def _menu_weights(node: SolverNode, kinds: tuple[str, ...]) -> dict[str, float]:
    """One node's weight on a family of action kinds, per arriving class, in points."""
    indices = [index for index, action in enumerate(node.actions) if action.kind in kinds]
    return {
        name: 100.0
        * sum(node.strategy_bp[index][gtopen_class_index(name)] for index in indices)
        / QUANTISATION_SCALE
        for name in HAND_CLASSES
        if node.reach_bp[gtopen_class_index(name)] > 0
    }


def _node_weights(node: SolverNode) -> dict[str, float]:
    """Combinations times arriving reach, per class, for one node."""
    return {
        name: float(class_combos(name) * node.reach_bp[gtopen_class_index(name)])
        for name in HAND_CLASSES
        if node.reach_bp[gtopen_class_index(name)] > 0
    }


def _hero_closes(node: SolverNode) -> bool:
    """Whether calling here ends the betting, which is where the equity relation is defined.

    Read off the node's own terminal flags rather than by counting live seats: a call that ends
    the hand is exactly a call with no node below it, and the walker that built the export is what
    knows that.
    """
    return any(action.kind == "call" and action.terminal for action in node.actions)


def walk_export() -> Walk:
    """Account for every solved node, and carry out what the export alone can say.

    Everything the report checks the artifact against comes from here, so the two are separate
    readings of the same solve rather than one reading compared with itself.
    """
    export = load_solver_export(COMMITTED_EXPORT_PATH)
    by_path = export.by_path()
    frequency = {
        node.path: tuple(node.action_frequency(index) for index in range(len(node.actions)))
        for node in export.nodes
    }
    arrival: dict[tuple[int, ...], float] = {(): 1.0}
    for path in sorted(by_path, key=len):
        for index in range(len(by_path[path].actions)):
            child = (*path, index)
            if child in by_path:
                arrival[child] = arrival[path] * frequency[path][index]

    keys: set[str] = set()
    node_path_by_spot: dict[str, tuple[int, ...]] = {}
    reach_bp_by_cell: dict[tuple[str, str], int] = {}
    splits: dict[str, tuple[float, float, float]] = {}
    closes: set[str] = set()
    merged_keys: set[str] = set()
    raise_plus_call: dict[str, float] = {}
    arrivals: dict[str, float] = {}
    committed_arrival = 0.0
    refused_exposure: list[tuple[str, float]] = []
    pure = mixed = cells = 0
    jam: tuple[str, str, float] = ("", "AA", 0.0)
    jam_arrival = -1.0

    for node in export.nodes:
        key = node_spot_key(by_path, node)
        if not is_committed_node(by_path, node):
            # The narrowest refused spot has to come from the clause it is published against.
            # The big blind's squeeze spots are refused by a clause of their own and sit far
            # BELOW the threshold - they passed this one - so folding them in here would name a
            # narrowest refusal of 3.74 against a line drawn at 10.
            if exclusion_code(by_path, node) == lookup.DERIVATION_MULTIWAY_EXPOSURE_ABOVE_THRESHOLD:
                refused_exposure.append((key, multiway_exposure_pct(by_path, node)))
            elif raises_faced(by_path, node) > COMMITTED_RAISE_DEPTH and (
                arrival[node.path] > jam_arrival
            ):
                jammed = _menu_weights(node, ("jam",))
                if "AA" in jammed:
                    jam_arrival = arrival[node.path]
                    jam = (key, "AA", jammed["AA"])
            continue
        keys.add(key)
        node_path_by_spot[key] = node.path
        splits[key] = terminal_split_pct(by_path, node)
        arrivals[key] = arrival[node.path]
        committed_arrival += arrival[node.path]
        if _hero_closes(node):
            closes.add(key)
        if merges_the_cold_call(by_path, node):
            merged_keys.add(key)
            raised = _menu_weights(node, ("raise", "jam"))
            called = _menu_weights(node, ("call",))
            raise_plus_call[key] = weighted(
                {name: raised[name] + called.get(name, 0.0) for name in raised},
                _node_weights(node),
            )
        for name in HAND_CLASSES:
            column = gtopen_class_index(name)
            reach = int(node.reach_bp[column])
            reach_bp_by_cell[(key, name)] = reach
            if reach <= 0:
                continue
            buckets: dict[str, int] = {}
            for index, action in enumerate(node.actions):
                recorded = "raise" if action.kind in ("raise", "jam") else action.kind
                buckets[recorded] = buckets.get(recorded, 0) + node.strategy_bp[index][column]
            cells += 1
            highest = 100.0 * max(buckets.values()) / QUANTISATION_SCALE
            pure += highest >= PURE_PCT
            mixed += highest < MIXED_PCT

    if not refused_exposure:
        raise DerivedChartReportError(
            "the walk refused no node for multiway exposure, so the extremes the filter is"
            " published against cannot be named and the clause was never exercised"
        )
    if not jam[0]:
        raise DerivedChartReportError(
            "no withheld four-bet-facing spot offers hero a jam, so the canary this phase retains"
            " against the export has nothing to read"
        )
    card = json.loads(COMMITTED_SOURCE_CARD_PATH.read_text(encoding="utf-8"))
    widest = max(splits.items(), key=lambda item: item[1][2])
    return Walk(
        census=census(export),
        spot_keys=frozenset(keys),
        exported_nodes=int(card["node_counts"]["exported"]),
        coverage_pct=100.0 * committed_arrival / sum(arrival.values()),
        node_path_by_spot=node_path_by_spot,
        reach_bp_by_cell=reach_bp_by_cell,
        splits=splits,
        widest_admitted=(widest[0], widest[1][2]),
        narrowest_refused=min(refused_exposure, key=lambda item: item[1]),
        hero_closes=frozenset(closes),
        solve_purity=(cells, 100.0 * pure / cells, 100.0 * mixed / cells),
        solve_raise_plus_call=raise_plus_call,
        merged_spot_keys=frozenset(merged_keys),
        merged_cell_count=len(merged_cells(export)),
        arrivals=arrivals,
        jam=jam,
    )


# -- the equity relation, which needs a table the export does not carry ---------------------- #


def load_equity_matrix(path: Path) -> tuple[tuple[float, ...], ...]:
    """The 169-by-169 preflop all-in equity matrix, indexed by GTOpen's own class index.

    Refused rather than approximated when it is absent. The relation below is the only figure in
    this report that no committed file can produce, and publishing a firing count off a table
    nobody committed would be the hand-typed count this phase has been burned by repeatedly.

    The layout read here is 169 rows of 169 32-bit floats, little-endian, in GTOpen's own class
    order, with an optional four-byte header skipped. Only the ORDER of the values matters to the
    relation, never their scale, so a table written as shares rather than as percentages reads the
    same firing count.
    """
    if not path.exists():
        raise DerivedChartReportError(
            f"the preflop all-in equity matrix is not committed at {path}, so the equity relation"
            " cannot be measured. The contract requires the 169-by-169 matrix in the tree,"
            " deterministic and regenerable; no other committed file carries the equity of one"
            " hand class against another, and the solver that built the solve disk-caches one at"
            " `cache/preflop_eq169.bin`"
        )
    raw = path.read_bytes()
    expected = 169 * 169 * 4
    if len(raw) not in (expected, expected + 4):
        raise DerivedChartReportError(
            f"{path} holds {len(raw)} bytes where a 169-by-169 matrix of 32-bit floats is"
            f" {expected}, so the equity relation would be read off a table of the wrong shape"
        )
    flat = struct.unpack(f"<{169 * 169}f", raw[len(raw) - expected :])
    return tuple(tuple(flat[row * 169 : (row + 1) * 169]) for row in range(169))


def opponent_ranges(export: SolverExport) -> dict[str, dict[str, float]]:
    """The range the last raiser holds when hero is asked to close the action.

    Not hero's range, and not the raiser's whole range either: it is the raiser's arriving range
    at the node they raised from, weighted by how often each class took that raise, which is what
    hero is actually up against. Reading the raiser's unconditional range instead would price
    hero's call against hands that folded.
    """
    by_path = export.by_path()
    found: dict[str, dict[str, float]] = {}
    for node in export.nodes:
        if not is_committed_node(by_path, node) or not _hero_closes(node):
            continue
        raiser: dict[str, float] | None = None
        for depth, index in enumerate(node.path):
            parent = by_path[node.path[:depth]]
            if parent.actions[index].kind not in ("raise", "jam"):
                continue
            raiser = {
                name: float(class_combos(name))
                * parent.reach_bp[gtopen_class_index(name)]
                * parent.strategy_bp[index][gtopen_class_index(name)]
                for name in HAND_CLASSES
            }
        if raiser is not None and sum(raiser.values()) > 0:
            found[node_spot_key(by_path, node)] = raiser
    return found


def equity_relation(
    play: Mapping[str, Mapping[str, float]],
    ranges: Mapping[str, Mapping[str, float]],
    matrix: Sequence[Sequence[float]],
) -> tuple[int, int]:
    """The equity relation, measured and gating nothing.

    At a spot where hero closes the action, no class folded above 99 percent may hold more equity
    against the opponent's arriving range than a class played above 99 percent. It fires on `A9s`
    folded while `87s` and `76s` are played, which is correct poker in a three-bet pot, so a
    correct chart fails it and a firing is not by itself a defect.
    """
    fires = 0
    for spot_id, villain in ranges.items():
        cells = play.get(spot_id)
        if cells is None:
            continue
        total = sum(villain.values())
        against = {
            name: sum(
                villain[other] * matrix[gtopen_class_index(name)][gtopen_class_index(other)]
                for other in villain
            )
            / total
            for name in cells
        }
        folded = [against[name] for name, value in cells.items() if value < 100.0 - PURE_PCT]
        played = [against[name] for name, value in cells.items() if value > PURE_PCT]
        fires += bool(folded and played and max(folded) > min(played))
    return fires, len(ranges)


# -- the retired chart, read out of git history ---------------------------------------------- #


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
            f"{path} cannot be read at commit {commit!r}, so the retired chart the cutover ledger"
            f" balances against is not there: {result.stderr.strip()}"
        )
    return result.stdout


@dataclass(frozen=True)
class RetiredChart:
    """The chart this phase retires, its prices, and the strategy that plays them."""

    artifact: PreflopArtifact
    sizing: PreflopSizingTable
    strategy: PreflopChartStrategy
    jam_priced_spots: int


def load_retired_chart_from_git(commit: str) -> RetiredChart:
    """The retired chart and its own sizing table, played from git history.

    Both files from the same commit: the sizing table went with the chart, and pricing the retired
    ranges off the derived table would report a chart nobody ever shipped. They are read through
    the repo's own importer and loader rather than parsed here, so the bytes at the pin have to be
    a chart this build would accept - a retired chart only a private parser can read is a chart
    nobody can check the ledger against.
    """
    payload = _read_at_commit(commit, RETIRED_CHART_PATH)
    prices = _read_at_commit(commit, RETIRED_SIZING_PATH)
    with tempfile.TemporaryDirectory() as directory:
        chart_path = Path(directory) / "retired.json"
        sizing_path = Path(directory) / "retired_sizings.json"
        chart_path.write_text(payload, encoding="utf-8")
        sizing_path.write_text(prices, encoding="utf-8")
        try:
            artifact = import_preflop_artifact(chart_path)
            sizing = PreflopSizingTable.from_json(sizing_path)
        except Exception as error:  # noqa: BLE001 - the message names the pin either way
            raise DerivedChartReportError(
                f"the chart at commit {commit!r} is not one this build can read: {error}"
            ) from error
    jammed = sum(
        1
        for classes in sizing.raise_to_bb.values()
        if any(entry["to_bb"] == 100.0 for entries in classes.values() for entry in entries)
    )
    return RetiredChart(
        artifact=artifact,
        sizing=sizing,
        strategy=PreflopChartStrategy(
            library=PreflopChartLibrary.from_artifacts([artifact]), sizing=sizing
        ),
        jam_priced_spots=jammed,
    )


# -- the corpus comparison -------------------------------------------------------------------- #


OPENER_KEY = re.compile(r"^t6/d\d+/BB/(LJ|HJ|CO|BTN|SB):raise@")
"""The big blind facing exactly one open, and which seat opened.

Read off the key the lookup asked about rather than off either chart's coverage, so the before and
after columns are over the same decisions.
"""

SCORED = frozenset({AGREE, DISAGREE})

RATE_LABELS = ("agreement", "refused", "sampled-action match")

RATE_SAMPLE_NOUN = {
    "agreement": "scored decisions",
    "refused": "decisions",
    "sampled-action match": "drawn decisions",
}


def scored_rows(result: ComparisonResult, population: str) -> list[ComparisonRow]:
    return [row for row in result.rows if row.population == population and row.verdict in SCORED]


def population_rates(result: ComparisonResult, population: str) -> dict[str, tuple[int, int]]:
    """The three rates one population gets, each with the sample it is over.

    Three rather than one because they answer different questions and a reader given only the
    first will read it as the other two. Agreement is over the decisions the chart answered, so it
    is silent about how many it declined; the refusal rate is that silence, published; and the
    sampled-action match is the stricter reading, beside it because a chart that got more mixed
    scores higher on the looser one while playing no better.
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

    Narrowed to calls because a fold is the easiest agreement in poker and roughly seven in ten
    preflop decisions are folds, so an unsplit rate mostly measures how often both sides threw
    away junk.
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

    Pooled here and nowhere else, and the difference is what is being counted. A rate is a claim
    about how well a chart matched a player, and Pluribus and the human professionals are
    different players; a reason code is a property of the chart's own coverage, which does not
    know who was sitting there.
    """
    counted = dict.fromkeys(lookup.MISS_CODES, 0)
    for row in result.rows:
        if row.verdict == REFUSED and row.miss_code is not None:
            counted[row.miss_code] += 1
    return counted


def first_action_is_a_call(spot_key_text: str) -> bool:
    """The definition of a limped pot, stated so a reader can apply it."""
    parts = spot_key_text.split("/")
    return len(parts) > 3 and parts[3].split(",")[0].endswith(":call")


def old_versus_new(
    before: ComparisonResult, after: ComparisonResult
) -> tuple[int, dict[str, int]]:
    """Where the two charts part company on a decision they both answer.

    Stated as continue-or-fold rather than as the exact action, for two reasons. It is the
    difference a reader can price - money in or money not in - and it partitions cleanly into the
    two directions, where a raise-against-call disagreement belongs to neither and would leave the
    published split not adding up to its own total.
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
                f"the two comparisons disagree about decision {new.hand_id}/{new.seat}, so they"
                " are not over the same corpus and nothing can be paired"
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


def percent(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


# -- what the report prints ------------------------------------------------------------------- #


@dataclass(frozen=True)
class Measured:
    """Everything the sections print, taken once so no two of them can disagree."""

    walk: Walk
    artifact: PreflopArtifact
    play: dict[str, dict[str, float]]
    raise_weight: dict[str, dict[str, float]]
    weights: dict[str, dict[str, float]]
    partitions: dict[str, tuple[str, ...]]
    arms: dict[str, ArmFigures]
    relations: dict[str, list[tuple[str, str, str, float, float]]]
    coverage: dict[str, tuple[int, int]]
    plays: dict[str, float]
    calls: dict[str, float]
    retired: RetiredChart
    before: ComparisonResult
    after: ComparisonResult
    shared: int
    directions: dict[str, int]
    equity_fires: int
    equity_over: int

    def family(self, name: str) -> tuple[str, ...]:
        """One of the families a band or a menu is published over, derived from the keys.

        Named rather than sliced at the call site, because a band over a subset of the family it
        names is the failure this report exists partly to stop, and a family with one definition
        cannot quietly become two.
        """
        if name == "the committed set":
            return tuple(sorted(self.play))
        if name == "the first-in spots":
            return self.partitions["raises faced 0"]
        if name == "the big blind facing an open":
            return tuple(
                key
                for key in sorted(self.play)
                if hero_seat(key) == "BB" and raises_faced_in_key(key) == 1
            )
        if name == "the merged spots":
            return tuple(sorted(self.walk.merged_spot_keys))
        if name == "the three-bet-facing spots":
            return self.partitions["raises faced 2"]
        raise DerivedChartReportError(f"no family is named {name!r}")


def census_section(measured: Measured) -> list[str]:
    """Four buckets, a total checkable against a file this phase did not write, and the walk's own
    keys against the artifact's."""
    counts = measured.walk.census
    artifact_keys = {spot.spot_id for spot in measured.artifact.spots}
    histogram: dict[int, int] = {}
    for key in artifact_keys:
        faced = raises_faced_in_key(key)
        histogram[faced] = histogram.get(faced, 0) + 1
    lines = [
        "Every action node in the committed export is in exactly one of four buckets, and the",
        "four add up to the node count the export's own source card publishes. That total is the",
        "check worth making: a converter that quietly skipped a subtree balances its own books",
        "perfectly, and only a figure from outside catches it.",
        "",
        f"  committed  {counts.committed}",
    ]
    for code in lookup.DERIVATION_EXCLUSION_CODES:
        lines.append(f"  excluded  {code}  {counts.excluded.get(code, 0)}")
    for code in lookup.DERIVATION_INEXPRESSIBILITY_CODES:
        lines.append(f"  inexpressible  {code}  {counts.inexpressible.get(code, 0)}")
    lines += [
        f"  total  {counts.total}",
        f"  coverage  {measured.walk.coverage_pct:.4f} percent",
        "",
        "Three exclusion reasons rather than one, and a reader should not read past that. Each",
        "names a different way back. The multiway family returns when GTOpen can price a pot with",
        "three or more players in it - it values one as the product of hero's equity against each",
        "opponent separately, which understates true three-way equity by about ten and a half",
        "points. The ten big-blind squeeze spots return when the flats are repaired. Everything",
        "beyond the committed raise depth returns when a later phase takes up the four-bet. A",
        "census folding any two of them together adds to the same total and is wrong only about",
        "which fix brings which back, which is the one failure a total can never see.",
        "",
        "The inexpressible bucket is empty, which is a measurement rather than an omission: all",
        f"{counts.total} nodes derive a spot key the vocabulary can write and no two collide.",
        "",
        "Coverage is the share of the preflop decisions the bot ever faces that the committed set",
        "answers, weighted by how often each node is actually reached rather than by counting",
        "nodes. The four-bet family is the great majority of the nodes and a little over one",
        "percent of the play, which is why the two readings are so far apart.",
        "",
        "And 249 nodes are not self-evidently 249 keys. A converter that dropped one node while",
        "inventing one key publishes the identical count, so the artifact and the walk are",
        "compared key by key and both directions are named:",
        "",
        f"  artifact keys  {len(artifact_keys)}  walked keys  {len(measured.walk.spot_keys)}"
        f"  invented  {len(artifact_keys - measured.walk.spot_keys)}"
        f"  dropped  {len(measured.walk.spot_keys - artifact_keys)}",
        "",
        "What the committed set is made of, by how many raises are already in when hero is asked.",
        "Three-bet-facing is the deepest the filters admit, so a fourth row here would be a",
        "converter that committed something above the ruled depth:",
        "",
    ]
    for faced in sorted(histogram):
        lines.append(f"  raises faced  {faced}  {histogram[faced]}")
    lines += [
        "",
        "Every price on a committed key is one of the three the solve offers - 2.5 to open, 7.5",
        "to three-bet, 22.5 to four-bet - and a shove is not among them. Hero's own jam lives only",
        "at the four-bet-facing spots this phase withholds, which is why the canary further down",
        "runs against the export rather than against the chart.",
    ]
    return lines


def exposure_section(measured: Measured) -> list[str]:
    """The filter's margin is sixteen hundredths of a point, so it is published, not described."""
    splits = measured.walk.splits
    lines = [
        "A node ships only where under a tenth of its decision mass reaches a flop with three or",
        "more players in it, measured by walking to the leaves rather than by counting who is",
        "still live, and over the branches the bot can take - hero's cold call is removed, since",
        "the chart never offers it to him.",
        "",
        f"  threshold  {MULTIWAY_EXPOSURE_THRESHOLD_PCT:.1f}",
        f"  widest admitted  {measured.walk.widest_admitted[0]}"
        f"  {measured.walk.widest_admitted[1]:.4f}",
        f"  narrowest refused  {measured.walk.narrowest_refused[0]}"
        f"  {measured.walk.narrowest_refused[1]:.4f}",
        "",
        "Sixteen hundredths of a point separate the two, which is why every committed spot's own",
        "figure is printed rather than summarised. The split is what makes a row readable:",
        "exposure is the share of a spot's decision mass reaching a multiway flop terminal, and",
        "`heads-up` is all the rest - the pot folded out before a flop, or a flop with two players",
        "in it. The two are the halves of one mass and add to a hundred, so a row publishing",
        "exposure alone could be over any denominator at all.",
        "",
        "The filter is blindest exactly where the mispricing has already turned a call into a",
        "fold. The ten big-blind squeeze spots passed this clause BECAUSE the big blind folds 93",
        "percent of its range there, so almost nothing of its mass reaches the three-way flop, and",
        "they are refused by a clause of their own instead. Any later build re-measures these",
        "rather than carrying them forward",
        "(MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN).",
        "",
    ]
    for key in sorted(splits):
        folded, heads_up, multiway = splits[key]
        lines.append(
            f"  {key}  exposure {multiway:.4f}  multiway {multiway:.4f}"
            f"  heads-up {folded + heads_up:.4f}"
        )
    return lines


def traced_cell(measured: Measured) -> tuple[str, str]:
    """Which cell the trace follows, chosen by a rule rather than named.

    A rule so it moves with the chart instead of pinning a row a later solve may not hold, and
    this rule because a near-pure cell would trace just as truthfully and show a reviewer nothing.
    What the conversion has to get right is a split, so the cell is a mixed one; and the per-cell
    reach is only legible where the whole range did not arrive, so a partially-arrived cell is
    preferred over a fully-arrived one.
    """
    mixed = [
        (spot_id, name)
        for spot_id, classes in measured.artifact.action_weights
        for name, weights in classes
        if spot_id in measured.walk.node_path_by_spot
        and max((weight for _, weight in weights), default=1.0) <= 0.9
    ]
    partial = [
        cell
        for cell in mixed
        if (measured.artifact.reach_bp_for(*cell) or QUANTISATION_SCALE) < QUANTISATION_SCALE
    ]
    for candidates in (partial, mixed):
        if candidates:
            return candidates[0]
    raise DerivedChartReportError(
        "no committed cell mixes two actions, so the chart is a pure strategy everywhere and"
        " there is nothing for a trace to show"
    )


def trace_section(measured: Measured) -> list[str]:
    """One solved node followed to the row it became, with nothing invented on the way."""
    spot_key_text, hand_class_text = traced_cell(measured)
    artifact = measured.artifact
    weights = dict(artifact.weights_for(spot_key_text, hand_class_text) or ())
    printed = "  ".join(f"{action}={weight:.4f}" for action, weight in weights.items())
    path = measured.walk.node_path_by_spot[spot_key_text]
    reach = artifact.reach_bp_for(spot_key_text, hand_class_text)
    export_reach = measured.walk.reach_bp_by_cell[(spot_key_text, hand_class_text)]
    arrival = dict(artifact.arrival_ppb)[spot_key_text]
    return [
        "One cell, from the solved node it came from to the row it is committed as. Every figure",
        "below is in the committed files, so a reviewer can open both and follow it without",
        "reading any code.",
        "",
        f"  export node  {'/'.join(str(step) for step in path) or 'root'}",
        f"  export reach for the class  {export_reach} bp",
        f"  artifact row  {spot_key_text}  {hand_class_text}  {printed}"
        f"  reach {reach} bp  arrival {arrival} ppb",
        "",
        "The weights are the solver's own, renormalised over the actions the chart vocabulary",
        "holds and nothing else: a named raise and an all-in both read as `raise` here, and what",
        "each costs is in the sizing table beside the chart rather than lost.",
        "",
        "Reach and arrival are both on the row because neither says what the other does. Reach is",
        "whether hero can be holding this hand here - a plain mean over the 169 classes, with no",
        "floor selecting cells. Arrival is whether the line is played at all - one left-to-right",
        "product from the root, in parts per billion. A spot can carry every class at full reach",
        "and never be reached at all, which is the next section's subject.",
    ]


def arrival_section(measured: Measured) -> list[str]:
    """Arrival is a probability at a scale where a sixth of the committed set rounds away."""
    arrivals = dict(measured.artifact.arrival_ppb)
    rounding = sum(1 for value in arrivals.values() if value == 0)
    exactly = sum(1 for key in arrivals if measured.walk.arrivals.get(key, 1.0) == 0.0)
    return [
        "Arrival is how often a spot's line is played at all, and over the committed set it spans",
        "many orders of magnitude. So the grain it is published at is stated, with the count of",
        "spots that round away at that grain - a reader who saw the zeroes without the grain would",
        "read every one of them as a spot the solve never reaches, where almost all of them are",
        "lines that are played and are rare.",
        "",
        "  grain  parts per billion",
        f"  rounding to zero  {rounding} of {len(arrivals)}",
        f"  exactly zero  {exactly}",
        "",
        "The two figures are different measurements and the gap between them is the point. The",
        "first counts spots whose arrival falls below half a part per billion once rounded; the",
        "second counts the spots the solve genuinely never reaches, read off the unrounded product",
        "rather than off the field. Only the second is a spot nobody plays.",
    ]


def relations_section(measured: Measured) -> list[str]:
    """Four relations, measured per cell, gating nothing, each with its worst case."""
    counted = {name: len(rows) for name, rows in measured.relations.items()}
    spots = len(measured.play)
    lines = [
        "Four things a solved preflop range should almost always do, measured on every committed",
        "cell at a tolerance of one percentage point. A gap of exactly a point is not a violation;",
        "the count is of gaps strictly wider. Three of the four read how often a hand puts money",
        "in at all, raise or call together. The fourth reads how often it RAISES in the published",
        "chart, and it is the one that matters: the inversion that halted this phase sits at cells",
        "where both hands are played 100 percent, so anything stated over play-not-fold reads",
        "nothing there at all.",
        "",
    ]
    for relation in RELATIONS:
        rows = measured.relations[relation.name]
        if rows:
            worst = max(rows, key=lambda row: row[4] - row[3])
            case = (
                f"{worst[1]} at {worst[3]:.2f} under {worst[2]} at {worst[4]:.2f},"
                f" a {worst[4] - worst[3]:.2f} point gap, at {worst[0]}"
            )
        else:
            case = "none, 0 comparisons played the wrong way round"
        lines.append(
            f"  relation  {relation.name}  violations  {counted[relation.name]}"
            f"  of {relation.comparisons_per_full_grid * spots} comparisons  worst  {case}"
        )
    lines += [
        "",
        "The denominator is the comparisons the committed spots would offer if every one carried a",
        "full grid. Most do not - a deep line hero reaches holding four hand classes offers almost",
        "nothing to compare - so what was actually looked at is published beside it, a comparison",
        "whose other half never arrived being skipped rather than scored against a stand-in zero:",
        "",
    ]
    for relation in RELATIONS:
        compared, skipped = measured.coverage[relation.name]
        lines.append(f"  compared  {relation.name}  {compared} compared  {skipped} skipped")
    lines += [
        "",
        "None of the four is gated as an order, and this is a ruling rather than an omission. The",
        "committed chart holds surviving cases that were read grid by grid and ruled correct play:",
        "a nut-straight suited ace is less dominated than a middling one, and a pick among hands",
        "the solve prices alike is bluff selection. A generator that refused a violating grid",
        "would refuse the chart the bot ships. What is gated is that the measurement was taken",
        "over every cell and published with its worst case, so these counts gate nothing and are",
        "measured rather than checked - a reader must not read one as a check that passed.",
        "",
        "And a split among hands the solve prices alike is not noise. It is bluff selection, which",
        "is further from arbitrary rather than nearer to it, and no packet may claim otherwise.",
    ]
    return lines


def ladders_section(measured: Measured) -> list[str]:
    """The family that returned a different verdict on every committed set it has been run on."""
    swapped = {key: transpose_hand_index(cells) for key, cells in measured.play.items()}
    lines = [
        "Group orderings: whether the aces-through-deuces ladder, taken in bands as well as one",
        "rank at a time, and each high card's row of suited hands, come out in order. The solved",
        "column is the committed chart; the transposed column is the same measure over a chart",
        "with every suited hand reading its offsuit twin's row.",
        "",
    ]
    for label, groups in GROUP_LADDERS.items():
        solved = ladder_flags(measured.play, measured.weights, groups)
        other = ladder_flags(swapped, measured.weights, groups)
        lines.append(f"  group  {label}  solved  {solved}  transposed  {other}")
    lines += [
        "",
        "This family gates nothing and is published only for a human to read. It returned a",
        "different verdict on every committed set it has ever been run over - it failed on one,",
        "passed on the next, came out mixed on a third and blind on a fourth - so what it measures",
        "is set composition rather than whether the hand index is right. It is kept because a",
        "reader finds it informative, and it is labelled so that a published tie cannot be",
        "mistaken for a gate that passed.",
    ]
    return lines


def arms_section(measured: Measured) -> list[str]:
    """Ten partitions, two arms, and the rank arm's coverage published rather than assumed."""
    lines = [
        "The range gate, and the only measurement in this report that refuses anything. Two arms,",
        "both strict, a tie refusing on each. The suit arm transposes every suited hand with its",
        "offsuit twin and scores SPOTS; the rank arm reverses every rank - a chart that opens 32o",
        "and folds aces - and scores CELLS on the row ladder. Two rather than one, because a",
        "rank-reversed chart maps pairs onto pairs and suited twins onto suited twins, so the suit",
        "arm scores it bit for bit as it scores the real chart and cannot see it at all.",
        "",
        "Both run on all ten partitions - the whole set, one per hero seat, one per raises faced -",
        "and dropping one is forbidden. What is asserted is the direction and never the counts:",
        "fixing a count picks the partition that reads smallest and calls that the gate.",
        "",
        "`reverse_hand_ranks` is total only on a full grid and most committed spots do not carry",
        "one, so the rank arm scores every spot and skips the comparisons whose partner cell is",
        "absent. What it skipped is published on EACH side, because the two sides skip different",
        "comparisons - the reversal carries a present cell onto a different row - and one number",
        "standing for both is how the withdrawn `149 against 69` was built, out of the solved side",
        "of one rule and the counterfactual side of another.",
        "",
    ]
    for label in sorted(measured.arms):
        figures = measured.arms[label]
        lines.append(
            f"  {figures.label}  spots {figures.spots}"
            f"  suit swap solved {figures.suit_solved} transposed {figures.suit_transposed}"
            f"  rank reversal solved {figures.rank_solved} permuted {figures.rank_permuted}"
            f"  over {figures.rank_scored_spots} scored"
            f"  skipped {figures.rank_skipped}"
            f"  permuted-skipped {figures.rank_skipped_permuted}"
            f"  {'asserted' if figures.asserted else 'published'}"
        )
    lines += [
        "",
        f"A partition scoring fewer than {RANK_ARM_SPOT_FLOOR} spots publishes rather than",
        "asserts, a strict comparison over one or two grids being a coin flip, and each row says",
        "which it did. Over the committed set none falls below the floor.",
        "",
        "Neither arm passing is evidence the ranges are sound. Both are extraction checks: they",
        "ask whether the hand grid came out of the solver the right way up, and every comparison",
        "either of them makes is against another cell of the same grid rather than against any",
        "outside standard. Neither can see a chart that folds too much everywhere, one whose grids",
        "sit on the wrong seats, or an inversion across two families",
        "(THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR). A green gate",
        "here means the hand index survived extraction, and nothing more.",
    ]
    return lines


def equity_section(measured: Measured) -> list[str]:
    """A correct chart fails this one, so it publishes and gates nothing."""
    return [
        "The one relation in this phase that asks whether a range is good poker rather than",
        "whether it was extracted right, and it is published and gates nothing. At a spot where",
        "hero closes the action, no hand folded above 99 percent of the time should hold more",
        "equity against the opponent's arriving range than a hand played above 99 percent. It is",
        "internal consistency: no realization model can excuse violating it.",
        "",
        f"  fires at  {measured.equity_fires} of {measured.equity_over} spots where hero closes",
        "",
        "A correct chart would fail it, which is why it gates nothing and is a measurement rather",
        "than a check. The firings are not near-ties a tolerance would remove. They are `A9s`",
        "folded while `87s` and `76s` are played, at six-point gaps, at the spots where an opener",
        "faces a three-bet - and that is good poker: in a three-bet pot a weak suited ace is",
        "dominated by the three-bettor's broadway aces while a suited connector keeps its",
        "playability. All-in equity is not the property that orders preflop hands, so a reader",
        "must not read a firing here as a defect by itself.",
        "",
        "What that leaves open is stated rather than closed.",
        "GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE stays deferred and this phase does not",
        "close it. Nothing in this repo measures whether a published range is good poker, and a",
        "measurement toward that gap is not the gap filled.",
    ]


def defects_section(measured: Measured) -> list[str]:
    """Accepted defects, never caveats, each with the number the phase accepted it on."""
    counted = {name: len(rows) for name, rows in measured.relations.items()}
    wheel, wide, narrow = kicker_split(measured.play)
    invisible = raise_inversions_invisible(measured.play, measured.raise_weight)
    solve_cells, solve_pure, solve_mixed = measured.walk.solve_purity
    _, published_pure, published_mixed = purity(cell_weights(measured.artifact))
    defends = [measured.plays[key] for key in measured.family("the big blind facing an open")]
    pair = counted["pair ladder"]
    kicker = counted["row kicker ladder"]
    raise_action = counted["pair ladder on the raise weight"]
    merged_spots = len(measured.walk.merged_spot_keys)
    moved = measured.walk.merged_cell_count
    return [
        "Four defects this phase accepts on purpose, each with the measurement it was accepted on.",
        "They are defects and are recorded as defects; none is small print, and the packet",
        "requirements forbid that word for exactly this list.",
        "",
        f"  defect  the big blind over-folds against every opener   it defends {min(defends):.2f}"
        f" to {max(defends):.2f} percent where rake-free solves are roughly 40 through 65, and its"
        " flat barely moves with who opened",
        f"  defect  the pair ladder inverts   {pair} cases on play-not-fold and {raise_action} on"
        f" the raise weight the bot plays, {invisible} of those invisible to play-not-fold",
        f"  defect  the kicker row ladder inverts   {kicker} cases, of which {wheel} are the"
        f" wheel-ace premium and correct poker, {wide} have no poker story at a 50 point gap or"
        f" wider, and {narrow} below it",
        f"  defect  the merged flats play differently   {moved} cells move at {merged_spots}"
        " spots, and three-betting 66 commits 7.5 big blinds and can face a four-bet where the"
        " solve would have seen a cheap flop",
        "",
        "The wheel-ace cases are separated out because they are correct poker, and lumping them in",
        "overstates what is wrong with the chart by about half: a suited wheel ace makes the nut",
        f"straight and is less dominated than a middling suited ace, so {wheel} of the"
        f" {kicker} are",
        "the premium GTOpen's own fit measures rather than a defect. The three parts add back to",
        "the family, which is the check that the split has the right members rather than merely",
        "the right size.",
        "",
        "The mixed-cell share sits here because it is what makes the merged flats a real cost",
        "rather than a relabelling, and each reading says which grid it is measured over, both",
        f"being taken over the same {solve_cells} cells at non-zero reach:",
        "",
        f"  in the solve, before the merge  pure at 99 percent {solve_pure:.2f}"
        f"  mixed below 90 percent {solve_mixed:.2f}",
        f"  in the published chart, after the merge  pure at 99 percent {published_pure:.2f}"
        f"  mixed below 90 percent {published_mixed:.2f}",
        "",
        "Read the first pair as the argument: the solve barely mixes, so the hole the merge had to",
        "fill was large rather than marginal - `the solver was near-indifferent, take the other",
        "action` was never available to it. The second pair is the chart this phase writes, where",
        f"the merge itself has turned {moved} mixed cells pure, and a generator computing purity",
        "off the file it just wrote would read only that one. Both are printed and each is",
        "labelled, because this phase has already shipped one figure under two meanings.",
    ]


def orderings_section(measured: Measured) -> list[str]:
    """Two orderings that survive any rake basis and any solver, so they transfer."""
    lines = [
        "Later position opens wider, and the big blind defends more against a wider opener.",
        "Neither depends on the rake basis or on which solver produced the ranges, which is why",
        "they are worth checking on a chart nobody has played from: a solve that got these",
        "backwards would be wrong in a way no agreement rate could excuse. Both columns are the",
        "committed chart's own, combination-weighted over the range that arrives.",
        "",
    ]
    for position in OPENERS:
        opens = measured.plays[f"t6/d100/{position}/rfi"]
        defends = measured.plays[f"t6/d100/BB/{position}:raise@2.5"]
        lines.append(f"  {position}  opens  {opens:.3f}  big blind defends  {defends:.3f}")
    lines += [
        "",
        "The small blind opens widest of the five and the big blind defends most against it, which",
        "is the ordering holding at its extreme rather than an exception to it: the small blind is",
        "opening into one seat that will have position on it for the rest of the hand.",
        "",
        "An ordering is not a level, though, and only the level catches a broken realization",
        "model. That is why the comparison against an outside reference sits below it, and why the",
        "big blind's own section prints what its tightness costs.",
    ]
    return lines


def big_blind_section(measured: Measured) -> list[str]:
    """The defect this phase accepts on purpose, published where it is signed off."""
    reference = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["big_blind_defence_pct"]
    flats = {position: measured.calls[f"t6/d100/BB/{position}:raise@2.5"] for position in OPENERS}
    lines = [
        "The big blind defends too tight against every opener, and this phase accepts that",
        "deliberately rather than as a residual. The cause is not the cold-call branch - at all",
        "five of these nodes hero closes the action - but the fit's own realization number for",
        "facing a bet in a single-raised pot, taken from raked games where flatting genuinely is",
        "worse. The fingerprint is the flat: it should widen sharply against a late seat and it",
        "barely moves.",
        "",
        "Two things are printed here and each names its own reference, because they read opposite",
        f"ways. The cited column is expectations/{EXPECTATIONS_NAME}.json, which is GTO Wizard",
        "6-max 100bb NL25 WITH RAKE. Against it this chart reads wider at four of the five openers",
        "and narrower only against the button, and that direction is expected rather than",
        "contradictory: rake is a toll on every contested pot, so a rake-free solve should defend",
        "wider than a raked reference. It is therefore the floor a rake-free solve has to clear",
        "and never evidence that the level is sound. This repo commits no rake-free reference to",
        "read the level against at all",
        "(NOTHING-READS-THE-DEFENCE-LEVEL-AGAINST-A-RAKE-FREE-REFERENCE, with",
        "REFERENCE-RANGES-HAVE-NO-CITED-SOURCE for the cited file's own provenance).",
        "",
    ]
    for position in OPENERS:
        defends = measured.plays[f"t6/d100/BB/{position}:raise@2.5"]
        cited = float(reference[position])
        verdict = "wider" if defends > cited else "narrower"
        lines.append(
            f"  vs {position}  defends {defends:.3f}  flats {flats[position]:.3f}"
            f"  raked reference {cited:.3f}  {verdict}"
        )
    spread = max(flats.values()) - min(flats.values())
    lines += [
        "",
        f"  flat spread  {spread:.2f} points",
        "",
        "That spread is the fingerprint: the flat is nearly invariant to who opened, across",
        "openers whose own ranges span more than thirty-five points",
        "(BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT). It is a separate finding from the level and",
        "it is not what the cost below prices.",
        "",
        "What the cost prices is the over-folding, and the over-folding is the accepted defect,",
        "which COMMITTED-SPOTS-NEVER-FLAT-A-RAISE now carries under that name. A reader given only",
        "the flat entry never reaches the level, so both are cited here. The cost turns on a",
        "realization number nothing in this repo measures, so it is published at both ends of the",
        "range it turns on and never as one figure somewhere between them - a single number would",
        "be a measurement this phase did not take. Both ends are over all five spots of the",
        "family, its true minimum and maximum:",
        "",
        "  R = 0.65  0.10 to 0.70 bb per 100",
        "  R = 0.85  8.76 to 13.04 bb per 100",
        "",
        "Read it as: at the low end of the realization range the equity folded away could not have",
        "been realized anyway and the mistake is nearly free; at the high end it could have been,",
        "and the same fold costs about 125 times as much. The band cannot be narrowed without",
        "measuring realization in this game, which no work in this repo does. These two rows are",
        f"quoted from {DECISIONS_DOC}, item 34, which is where the cost was ruled; every other",
        "figure in this report is re-derived by the command that prints it.",
        "",
        "This is accepted rather than corrected because the bot has no postflop strategy. A chart",
        "teaching wide big-blind defence would be teaching a student to take marginal hands out of",
        "position to flops this bot cannot help them play, so the tightness and the missing",
        "postflop half point the same way.",
    ]
    return lines


def bands_section(measured: Measured) -> list[str]:
    """A band over a subset of the family it names is the failure this section exists to stop."""
    lines = [
        "Every band below is over ALL of the family it names, and the size it is over is printed",
        "beside it so a reader can check that. A band measured over part of a family and published",
        "as the family's is a failure this phase has already caught once, and it is invisible in a",
        "row carrying only two numbers.",
        "",
        "One quantity, five families: how much of hero's arriving range the chart puts money in",
        "with, combination-weighted, in points. The ends are the family's true minimum and maximum",
        "rather than a summary of them.",
        "",
    ]
    for name in (
        "the committed set",
        "the first-in spots",
        "the big blind facing an open",
        "the merged spots",
        "the three-bet-facing spots",
    ):
        keys = measured.family(name)
        values = [measured.plays[key] for key in keys]
        lines.append(
            f"  band  {name}  over {len(keys)} spots  min {min(values):.4f} max {max(values):.4f}"
        )
    lines += [
        "",
        "No four-bet frequency appears in any band here, and none may be offered as evidence that",
        "the unfitted terminal fails to reach the output. A committed three-bet-facing spot has to",
        "price hero's own four-bet, and that routes through a flop terminal the realization fit",
        "has no observation for (THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL). The family",
        "that would show the damage is the four-bet-facing one, and that is exactly the family",
        "this phase withholds, so a comfortable four-bet frequency here would show nothing at all.",
    ]
    return lines


def menus_section(measured: Measured) -> list[str]:
    """Three families, three menus, and the merge shown preserving the range exactly."""
    merged = measured.family("the merged spots")
    big_blind = measured.family("the big blind facing an open")
    three_bet = measured.family("the three-bet-facing spots")
    lines = [
        "The bot never cold-calls. Money in behind an opener with nothing already posted buys a",
        "multiway pot out of position, so where hero faces an open and has posted nothing the",
        "solve's call is merged into his raise. The big blind is not one of those seats - it has",
        "paid a blind, so its call is a defence rather than a cold call - and neither is a seat",
        "that opened and now faces a three-bet. Three families, three menus:",
        "",
        f"  family  the big blind facing an open  spots {len(big_blind)}  menu fold/call/raise",
        f"  family  the merged spots  spots {len(merged)}  menu fold/raise",
        f"  family  the three-bet-facing spots  spots {len(three_bet)}  menu fold/call/raise",
        "",
        f"  cells moved  {measured.walk.merged_cell_count}",
        "",
        "Merged and not deleted, and the difference is a hand with an answer against a hand with",
        "none: at nine of these spots a hand's whole weight sits on calling, so deleting would",
        "leave a row of zeroes, and printing fold would publish `fold pocket nines to an open`.",
        "Adding rather than renormalising is the point too - hero folds exactly as often as the",
        "solve folds, and the hands it wanted to see a flop with are the hands he now raises with.",
        "",
        "So the published defence at every merged spot equals the solve's raise plus its call, to",
        "the basis point, and both columns are printed rather than the claim:",
        "",
    ]
    for key in merged:
        lines.append(
            f"  {key}  defence {measured.plays[key]:.4f}"
            f"  solve raise+call {measured.walk.solve_raise_plus_call[key]:.4f}"
        )
    lines += [
        "",
        "The cost is real and is stated rather than waved through. A hand that flatted now",
        "three-bets: 66 commits 7.5 big blinds and can face a four-bet, where the solve would have",
        "seen a cheap flop with it. The range is preserved and the way it plays is not",
        "(MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED).",
    ]
    return lines


def expectations_section(measured: Measured) -> list[str]:
    """The one column this repo did not produce, printed and graded against nothing."""
    reference = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    quoted = {
        "opens": reference["open_frequency_pct"],
        "big blind defends": reference["big_blind_defence_pct"],
    }
    lines = [
        "GTO Wizard's own published frequencies for a raked NL25 six-max game, beside what this",
        "phase measured. They are the only numbers here this repo did not produce, which is what",
        "makes them worth printing: a range that is uniformly wrong is self-consistent everywhere",
        "inside the repo and only shows against something outside it.",
        "",
    ]
    for measure_name, values in quoted.items():
        for position in OPENERS:
            key = (
                f"t6/d100/{position}/rfi"
                if measure_name == "opens"
                else f"t6/d100/BB/{position}:raise@2.5"
            )
            lines.append(
                f"  {position}  {measure_name}  derived  {measured.plays[key]:.3f}"
                f"  GTO Wizard  {float(values[position]):.3f}"
            )
    lines += [
        "",
        "This comparison is gated by nothing and no threshold is drawn on it, because the two",
        "columns are not measuring the same game. GTO Wizard's solve is raked and this one is not,",
        "and rake is a toll on every pot that is contested, so a rake-free solve opens more and",
        "defends more. Reading wider than this file is therefore a floor rather than a pass.",
        "",
        "The small blind's gap is the largest and has a second cause on top of that: the reference",
        "solve limps 13.73 percent of the time from the small blind, where this one has no limp",
        "branch at all, so the hands that limped there open here.",
    ]
    return lines


def ledger_section(measured: Measured, commit: str) -> list[str]:
    """A ledger that does not balance is a coverage claim nobody checked."""
    retired_keys = {spot.spot_id for spot in measured.retired.artifact.spots}
    derived_keys = {spot.spot_id for spot in measured.artifact.spots}
    carried = retired_keys & derived_keys
    return [
        "What the cutover retired and what it committed, as a ledger that has to balance on both",
        "sides. The retired chart is deleted from the tree and is read out of git history at the",
        "pin below rather than kept as a second copy under `data/artifacts/preflop/` - a second",
        "copy works and makes a reader ask which chart the bot plays, which is the confusion this",
        "phase exists to end. Anybody can fetch the same bytes and recount every figure here.",
        "",
        f"  retired chart  {RETIRED_CHART_PATH}  at  {commit}",
        f"  retired spots  {len(retired_keys)}",
        f"  sizing entries  {len(measured.retired.sizing.raise_to_bb)}",
        f"  priced at a jam  {measured.retired.jam_priced_spots}",
        f"  derived spots  {len(derived_keys)}",
        f"  carried over  {len(carried)}",
        f"  refused  {len(retired_keys - derived_keys)}",
        f"  gained  {len(derived_keys - retired_keys)}",
        "",
        "Both sides close. The retired chart's spots are the ones carried over plus the ones the",
        "new rules refuse; the derived chart's are the ones carried over plus the ones gained.",
        "",
        "Every one of the retired chart's sizing entries is priced at a shove - hero's whole stack",
        "- which the ruled config cannot produce, the solve being `add_allin: false`. That is the",
        "measured reason the two charts cannot agree on every shared decision, and it is why a",
        "zero disagreement count further down would be a comparison handed the same chart twice",
        "rather than a result.",
    ]


def vacuous_section() -> list[str]:
    """Three criteria with no instance over the committed set, labelled wherever reported."""
    return [
        "Three criteria this phase keeps have no instance over the committed set. A criterion that",
        "cannot fire did not pass, and none of these three is counted anywhere as a check that",
        "passed. Each is kept because a later solve reactivates it:",
        "",
        "  vacuous  the two-price sizing schema: every committed spot offers hero exactly one",
        "  raise, so the per-class price list never carries two entries. It is kept because the",
        "  multiway family returns with two-price menus, and it is proved against a synthetic",
        "  export instead of against the committed one.",
        "  vacuous  the no-raise half of the sizing invariant: no committed spot offers hero zero",
        "  raises, so the half of the rule saying such a spot carries no key and makes the",
        "  strategy refuse has nothing to refuse here.",
        "  vacuous  the jam-and-named-raise collapse rule: under `add_allin: false` no committed",
        "  spot offers hero both a named raise and a shove, so the rule that adds their weights",
        "  never fires at all.",
        "",
        "Wherever one of these is reported it carries this label, because a vacuous criterion is",
        "not a check that passed. It is never counted as one, and a packet counting one would be",
        "claiming coverage the phase does not have.",
    ]


def jams_section(measured: Measured) -> list[str]:
    """Hero's own jam, at the spots this phase withholds."""
    key, hand_class_text, weight = measured.walk.jam
    return [
        "Hero's own shove is not in this chart at all, and that is a property of what the phase",
        "withheld rather than of the conversion. The solve is `add_allin: false`, so the only",
        "place hero is offered his whole stack is at the four-bet-facing spots, and those are",
        "exactly the family a later phase takes up.",
        "",
        "So the jam-inversion canary that rejected the first cutover is retained against the",
        "EXPORT rather than against the chart, and the weight it reads is printed here. The spot",
        "named is one the chart does not answer:",
        "",
        f"  {key}  {hand_class_text} jams  {weight:.2f}",
        "",
        "Read it as the check working: aces take the whole stack at the most-played spot of the",
        "withheld family, which is what a solve that read its hand index the right way up must",
        "say. A chart offering hero a jam at a committed spot would be a chart contradicting the",
        "config it was solved under.",
    ]


def limitations_section() -> list[str]:
    """What the source cannot price, in poker terms."""
    return [
        "What the source cannot price, stated in poker terms with the entry that carries each. A",
        "reader should take these as the shape of what the chart is, not as small print.",
        "",
        "  The solve is rake-free at the table and is NOT rake-free at its heads-up flop",
        "  terminals. `realization: calibrated` settles a flop by scaling each hand's equity share",
        "  using numbers fitted on raked games, so the rake it was trained on comes back in at",
        "  every flop it does not play out (CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE).",
        "",
        "  The four-bet is solved a quarter oversized, at 22.5 big blinds where a standard sizing",
        "  is nearer 18. Every committed three-bet-facing spot prices hero's own four-bet through",
        "  it (PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED).",
        "",
        "  The published ranges answer a field that under-cold-calls. The export branches on every",
        "  cold call and prices it against a continuation structure that punishes it, so villains",
        "  flat far less often here than in a real game, and opening and three-betting therefore",
        "  look slightly better than they are",
        "  (PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS).",
        "",
        "  The merged flats play differently, not just differently labelled. The range is",
        "  preserved to the basis point and the money is not: a hand that flatted for 2.5 now",
        "  three-bets for 7.5 and can be four-bet off it",
        "  (MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED).",
        "",
        "  And the multiway pricing underneath all of it: GTOpen values a pot with three or more",
        "  players as the product of hero's pairwise equities, which understates real three-way",
        "  equity by about ten and a half points and by fourteen on the suited connectors whose",
        "  whole value is playing a multiway pot. That is what the exposure filter is for, and it",
        "  is why the withheld multiway family is a decision rather than a gap.",
    ]


def corpus_section(measured: Measured) -> list[str]:
    """Three rates, two populations, before and after, and never one figure over both."""
    lines = [
        "The same public corpus, scored twice: once against the chart being retired and once",
        "against the chart being committed. One comparison, one corpus, one piece of code - the",
        "chart is a parameter to it - so the before and after columns cannot have drifted apart by",
        "being measured differently.",
        "",
        "Two definitions make these rates readable. Agreement means the chart gives the action the",
        "player actually took nonzero weight, not that a draw matched. And these are real players,",
        "not an oracle - agreeing with them is not the same as playing well, and Pluribus and the",
        "human professionals are different players, so nothing here is pooled.",
        "",
    ]
    for population in POPULATIONS:
        lines.append(f"  {population}")
        rates = {
            "before": population_rates(measured.before, population),
            "after": population_rates(measured.after, population),
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
        "None of this is a verdict and none of it gates. The corpus verdict is PHASE 17's, and",
        "what this report does is republish the measurement so a reader can see what moved. A",
        "rendered agreement rate with no label is read as a grade, so this one carries the label.",
        "",
        "The refusal rate rises, on both populations, and that is the ruled cost rather than a",
        "regression: the committed predicate refuses everything from the four-bet on, every pot",
        "multiway more than one time in ten, and the big blind's squeeze spots. What is left after",
        "the refusals is the harder subset, which is why an agreement rate over a smaller sample",
        "is the shape to expect rather than evidence of a worse chart.",
    ]
    return lines


def prediction_section(measured: Measured) -> list[str]:
    """The pre-registered band, republished as a form rather than as numbers that moved."""
    lines = [
        "A band was pre-registered on 2026-08-24, before any of this was measured: per opener,",
        "big-blind call agreement was to move in the same direction as that opener's defence",
        "delta, by between a quarter to one times the delta in points. The record is",
        f"{DECISIONS_DOC}, item 9.",
        "",
        "Its NUMBERS are void and are not reprinted here. They were computed on an export this",
        "phase no longer ships, and a pre-registration whose figures were fixed against data that",
        "has since moved is not a pre-registration. What travels is the FORM - a quarter to one",
        "times that opener's own delta, written down before the numbers are seen - and PHASE 17",
        "re-registers the arithmetic and reads it. Nothing here concludes anything and this",
        "section gates nothing.",
        "",
        "What is printed instead is the delta itself, recomputed from the two committed charts, so",
        "that the later phase has the measurement its band will be drawn on rather than a claim",
        "about it:",
        "",
    ]
    for position in OPENERS:
        key = f"t6/d100/BB/{position}:raise@2.5"
        new = measured.plays[key]
        old = 100.0 - measured.retired.strategy.library.action_frequency_pct(key, "fold")
        lines.append(
            f"  vs {position}  retired {old:.3f}  derived {new:.3f}  delta {new - old:+.3f}"
        )
    lines += [
        "",
        "And the move each rate actually made, unpooled, with the sample under it, because a rate",
        "over three or five decisions cannot resolve a band a point wide and a pooled figure would",
        "hide which population it came from:",
        "",
    ]
    for population in POPULATIONS:
        before = big_blind_call_agreement(measured.before, population)
        after = big_blind_call_agreement(measured.after, population)
        for position in OPENERS:
            was, now = before.get(position), after.get(position)
            if not was or not now or not was[1] or not now[1]:
                lines.append(f"  {population}, vs {position}: no calls faced that opener")
                continue
            lines.append(
                f"  {population}, vs {position}: {now[1]} calls,"
                f" {percent(*was):.1f} to {percent(*now):.1f} percent"
            )
    return lines


def price_section(measured: Measured) -> list[str]:
    """What the corpus actually paid to see a flop, against what the solve assumes."""
    prices = measured.after.open_sizes_bb()
    total = len(prices)
    counted: dict[float, int] = {}
    for price in prices:
        counted[price] = counted.get(price, 0) + 1
    ordered = sorted(prices)
    median = (
        (ordered[total // 2 - 1] + ordered[total // 2]) / 2.0
        if total % 2 == 0
        else ordered[total // 2]
    )
    lines = [
        "The committed solve assumes an open arrives at one price. These hands were not played at",
        "it, and the lookup abstracts an opponent's price to the solved one before asking the",
        "chart, so every rate above is partly a rate about a table the chart was never solved for.",
        "The qualification on its own cannot be weighed; a distribution can.",
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
        "A cheaper open is a better price to defend against, so where the corpus opened below the",
        "solved 2.5 the chart is systematically a little tighter than the spot in front of it",
        "deserves. That is a bias with a known direction rather than noise, and it is one of the",
        "two explanations the next section cannot separate.",
    ]
    return lines


def explanations_section() -> list[str]:
    """Which candidate explanation this measurement separates, and which two it cannot."""
    return [
        "Any residual gap between this chart and what the players did has three candidate causes,",
        "and this measurement separates one of them. Naming which is not small print on the",
        "finding; it is most of the finding.",
        "",
        "  rake  separated: the committed solve is rake-free at the table, so a raked-solve",
        "        explanation for a residual gap no longer applies to this chart",
        "  price  uncontrolled: the lookup abstracts an opponent's open to the solved size, and",
        "        the distribution above shows how far that reaches",
        "  realization  uncontrolled: the equity-realization model underprices position, and this",
        "        phase accepts that rather than fixing it",
        "",
        "Two of the three therefore survive the cutover untouched. A reader who sees a residual",
        "disagreement here cannot read it as a defect in the ranges, because two explanations for",
        "it are still standing and neither has been measured away.",
    ]


def bounds_section(measured: Measured) -> list[str]:
    """What an agreement rate off this chart is not a statement about."""
    return [
        "Every figure above is about one table configuration and one branch of the tree. The chart",
        "answers a decision only when all of the following hold, and refuses otherwise:",
        "",
        "  six-handed, and no other table size",
        "  100 big blinds effective, and no other depth",
        "  symmetric stacks: every live seat started the hand at hero's depth",
        "  no straddle in the pot",
        "  no ante posted",
        "  one solved opening price, 2.5 big blinds",
        "  at most two raises already in: everything from the four-bet on is refused",
        "  under a tenth of the spot's decision mass reaching a multiway flop",
        "  not the big blind answering an open somebody has already called",
        "",
        "The last three are the ruled predicate stated as bounds rather than as rules, and they",
        "are what costs most: a rate read off this chart says nothing whatever about multiway",
        "play, which is most of the hands a six-handed game actually deals, and nothing at all",
        "about a four-bet pot.",
        "",
        "What a trainee gets is the other side of the same sentence:",
        f"{measured.walk.coverage_pct:.4f} percent of the preflop decisions the bot ever faces,",
        "answered from a solve of the game this bot is trained for rather than converted from a",
        "raked one.",
    ]


def refusals_section(measured: Measured) -> list[str]:
    """Movement by reason over the closed vocabulary, and the inventory republished."""
    old_codes = refusals_by_code(measured.before)
    new_codes = refusals_by_code(measured.after)
    inventory = measured.after.refusal_inventory
    limped = [entry for entry in inventory if first_action_is_a_call(entry.spot_key)]
    lines = [
        "One total would hide the finding: the reasons move in different directions and by very",
        "different sizes. Every runtime miss code gets a row, a zero included, because a reason",
        "that stopped happening is a result too. The columns are the retired chart and the derived",
        "one, over both populations together - a reason code is a property of the chart's coverage",
        "rather than of who was sitting in the seat.",
        "",
        "These are the runtime miss codes and they are a different vocabulary from the reasons in",
        "the census above. Folding the two together is how an excluded node gets filed as a lookup",
        "failure, so no reason from that other vocabulary appears in this section at all.",
        "",
    ]
    for code in lookup.MISS_CODES:
        lines.append(f"  {code}  {old_codes[code]}  {new_codes[code]}")
    lines += [
        "",
        "The count of decision points facing a limp is published with the rule it was counted by,",
        "because the figure quoted elsewhere carries none and does not reproduce",
        "(LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION). The rule is this:",
        "the first recorded action in the spot key is a call.",
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


def old_versus_new_section(measured: Measured) -> list[str]:
    """Where the two charts part company, with the directions the disagreement went."""
    lines = [
        "Where the two charts would actually have played differently, over the decisions BOTH of",
        "them answer. That is a different question from the coverage rows above, which are about",
        "what each chart declines; here both returned an action and the actions differ.",
        "",
        f"  decisions both charts answer  {measured.shared}",
        f"  disagreed  {sum(measured.directions.values())}",
    ]
    for label in ("derived continues, retired folds", "retired continues, derived folds"):
        lines.append(f"  {label}  {measured.directions[label]}")
    lines += [
        "",
        "The difference counted is whether hero puts money in: a raise where the other chart calls",
        "is the same decision priced differently, and it belongs in the sizing table rather than",
        "here. Both directions are published because a comparison that quietly became trivial",
        "arrives as a small consistent number rather than as an error, and a split that does not",
        "add to its own total is the shape of a comparison that was never taken.",
    ]
    return lines


def recomputable_section(measured: Measured) -> list[str]:
    """One number a reviewer can check with a pencil and one committed file."""
    counts = measured.walk.census
    terms = (
        [counts.committed]
        + [counts.excluded.get(code, 0) for code in lookup.DERIVATION_EXCLUSION_CODES]
        + [counts.inexpressible.get(code, 0) for code in lookup.DERIVATION_INEXPRESSIBILITY_CODES]
    )
    arithmetic = " + ".join(str(term) for term in terms) + f" = {counts.total}"
    return [
        "The packet owes a reader one figure they can verify without running anything, so here it",
        "is with the file it comes out of and the arithmetic that produces it.",
        "",
        f"  the number  {counts.total} action nodes in the committed export",
        f"  the file  {SOURCE_CARD_NAME}",
        f"  the arithmetic  {arithmetic}",
        "",
        "The terms are the census rows above, in the same order, and the total is the",
        "`node_counts.exported` figure on that card. If they do not add to it then a solved node",
        "has gone missing between the export and this report, and no other check in this phase",
        "would notice.",
    ]


HEADINGS: tuple[str, ...] = (
    "## The four-bucket node census",
    "## Multiway exposure, per committed spot",
    "## One converted cell, traced",
    "## The arrival grain, and the spots that round to zero",
    "## The four relations, measured and gating nothing",
    "## The group-order ladders, published for a human",
    "## The two counterfactual arms, on every partition",
    "## The equity relation, published and gating nothing",
    "## The four accepted defects, and what each costs",
    "## The two orderings",
    "## The big blind's defence and flat, per opener",
    "## Every published band, against its family's extremes",
    "## The menu each family publishes, and the merged flats",
    "## The derived chart against the GTO Wizard expectations",
    "## The cutover ledger",
    "## The three criteria with no instance in the committed set",
    "## Hero's own jam, at the spots this phase withholds",
    "## What the source cannot price, in poker terms",
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
bounds: what was converted, what one cell became, whether the ranges behave like poker, what the
cutover cost, what the corpus says, and only then what none of it establishes.
"""

PREAMBLE = """The derived preflop chart, and what the cutover changed

This is the phase's evidence for a reader who does not read code. The bot's preflop ranges have
been replaced. It used to play from 86 spots taken out of a superseded reading of the solve, every
one of its priced spots costed at a shove the config cannot produce; it now plays from 249 derived
under a stated rule from a GTOpen solve of the game it is actually trained for - six-handed, 100
big blinds, rake-free. The old chart is deleted from the tree and is read out of git history here.

Nothing below is a grade on the new chart. Two of the three things that could explain a gap
between it and how people played are still uncontrolled, real players are not an oracle, and the
corpus verdict belongs to a later phase. What this report can do is show that the conversion was
faithful, that the hand index survived it, what coverage was bought and sold, and what the four
accepted defects cost - and say plainly which of its figures gate and which are published."""


def render(sections: Sequence[list[str]]) -> str:
    """One heading per section, exactly once, with the claim made under its own heading."""
    parts = [PREAMBLE]
    for heading, body in zip(HEADINGS, sections, strict=True):
        parts.append(f"{heading}\n\n" + "\n".join(body).rstrip())
    return "\n\n".join(parts) + "\n"


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """The four inputs a caller can move, three of which the frozen tests feed a wrong one.

    The artifact, the pin and the equity matrix are inputs rather than constants because they are
    things the report VALIDATES: a generator that could only ever be handed the right chart and
    the right commit could not be shown refusing the wrong ones.
    """
    parser = argparse.ArgumentParser(description="Generate the derived preflop chart report")
    parser.add_argument("--output", type=Path, default=REPORT_OUTPUT)
    parser.add_argument("--retired-commit", default=RETIRED_CHART_COMMIT)
    parser.add_argument("--artifact", type=Path, default=COMMITTED_ARTIFACT)
    parser.add_argument("--equity-matrix", type=Path, default=EQUITY_MATRIX_PATH)
    return parser.parse_args(argv)


def measure(arguments: argparse.Namespace) -> tuple[Measured, list[str]]:
    """Take every figure the report prints, and collect the ones that do not hold.

    Measuring and validating are one pass because the validators are stated over the measurements:
    a validator handed a number the report did not take is a validator checking something else.
    """
    walk = walk_export()
    artifact = import_preflop_artifact(arguments.artifact)
    retired = load_retired_chart_from_git(arguments.retired_commit)
    derived = PreflopChartStrategy(
        library=PreflopChartLibrary.from_artifacts([artifact]),
        sizing=PreflopSizingTable.from_repo(),
    )
    sample = load_committed_sample()
    after = compare_committed_sample(sample, strategy=derived)
    before = compare_committed_sample(sample, strategy=retired.strategy)
    shared, directions = old_versus_new(before, after)

    play = play_grid(artifact)
    raise_weight = raise_weight_grid(artifact)
    walked = partitions(sorted(play))
    arms = {
        label: arm_figures(label, {key: play[key] for key in keys})
        for label, keys in walked.items()
    }
    findings = relation_findings(play, raise_weight)
    counted = count_dominance_violations(play=play, raise_weight=raise_weight)
    errors: list[str] = []
    if {name: len(rows) for name, rows in findings.items()} != counted:
        errors.append(
            "the report's own relation walk and `chart_relations` disagree about the counts, so"
            " one of the two is not the relation this phase pinned as data"
        )
    rows_by_relation = dominance_inversions(play=play, raise_weight=raise_weight)
    if {name: len(rows) for name, rows in rows_by_relation.items()} != counted:
        errors.append("the relation rows and the relation counts are not of the same walk")

    equity_fires = equity_over = 0
    try:
        matrix = load_equity_matrix(arguments.equity_matrix)
        equity_fires, equity_over = equity_relation(
            play, opponent_ranges(load_solver_export(COMMITTED_EXPORT_PATH)), matrix
        )
    except DerivedChartReportError as error:
        errors.append(str(error))

    measured = Measured(
        walk=walk,
        artifact=artifact,
        play=play,
        raise_weight=raise_weight,
        weights=reach_weights(artifact),
        partitions=walked,
        arms=arms,
        relations=findings,
        coverage=relation_coverage(play, raise_weight),
        plays=spot_frequencies(artifact, "play"),
        calls=spot_frequencies(artifact, "call"),
        retired=retired,
        before=before,
        after=after,
        shared=shared,
        directions=directions,
        equity_fires=equity_fires,
        equity_over=equity_over,
    )

    checks = [
        lambda: validate_census(walk.census, walk.exported_nodes),
        lambda: validate_spot_count(
            {spot.spot_id for spot in artifact.spots}, set(walk.spot_keys)
        ),
        lambda: validate_disagreement(
            shared_decisions=shared,
            disagreements=sum(directions.values()),
            by_direction=directions,
        ),
    ]
    for figures in arms.values():
        checks.append(
            lambda figures=figures: validate_group_discrimination(
                solved=figures.suit_solved, transposed=figures.suit_transposed
            )
        )
        if figures.asserted:
            checks.append(
                lambda figures=figures: validate_rank_discrimination(
                    solved=figures.rank_solved, permuted=figures.rank_permuted
                )
            )
    for check in checks:
        try:
            check()
        except DerivedChartReportError as error:
            errors.append(str(error))
    return measured, errors


def main(argv: list[str] | None = None) -> int:
    """Measure first, validate second, publish last.

    The order is the point. A refused figure must not also be published: a report on disk is what
    a reviewer reads, and a wrong one beside a non-zero exit code is worse than no report at all.
    So every validator runs and every failure is collected before anything is written, and one
    gate decides whether the file appears.
    """
    arguments = parse_arguments(argv)
    try:
        measured, errors = measure(arguments)
    except DerivedChartReportError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 1
    if errors:
        for message in errors:
            print(f"refused: {message}", file=sys.stderr)
        return 1

    text = render(
        [
            census_section(measured),
            exposure_section(measured),
            trace_section(measured),
            arrival_section(measured),
            relations_section(measured),
            ladders_section(measured),
            arms_section(measured),
            equity_section(measured),
            defects_section(measured),
            orderings_section(measured),
            big_blind_section(measured),
            bands_section(measured),
            menus_section(measured),
            expectations_section(measured),
            ledger_section(measured, arguments.retired_commit),
            vacuous_section(),
            jams_section(measured),
            limitations_section(),
            corpus_section(measured),
            prediction_section(measured),
            price_section(measured),
            explanations_section(),
            bounds_section(measured),
            refusals_section(measured),
            old_versus_new_section(measured),
            recomputable_section(measured),
        ]
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(text, encoding="utf-8")
    print(f"wrote {arguments.output} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
