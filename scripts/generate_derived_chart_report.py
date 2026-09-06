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
from typing import Any

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
from poker_training_bot.solver_artifacts.hand_classes import (  # noqa: E402
    HAND_CLASSES,
    HIGH_TO_LOW_RANKS,
)
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

REFERENCE_SOURCE = ARTIFACT_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"
"""The outside reference the expectations file is distilled from, read here in full.

`expectations/six_max_nl25_100bb.json` carries two families - open frequency and big-blind
defence - and the file it comes from carries per-hand strategies for thirty-six spots: five
first-in, fifteen facing an open, fifteen facing a three-bet and the blind-versus-blind limp.
Until this section was written, the one measurement in this repo able to catch a range that is
uniformly wrong was applied to two of the five committed families, and those were the two that
pass. It is still a raked NL25 solve, so reading wider than it is still a floor and never a pass,
and none of it gates anything.
"""

REFERENCE_SEAT = {"LJ": "UTG", "HJ": "HJ", "CO": "CO", "BTN": "BTN", "SB": "SB", "BB": "BB"}
"""This repo's seat names against the reference's. Only the first seat is named differently."""

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

SPELLED = {
    "ATs": "ace-ten suited",
    "AQo": "ace-queen offsuit",
    "JTs": "jack-ten suited",
    "KQo": "king-queen offsuit",
    "KTs": "king-ten suited",
    "76s": "seven-six suited",
}
"""The few hand classes the prose names in words rather than in grid notation.

A finding a reader has to decode is a finding they skim, and these six carry the merged family's
inversion. The weights beside them are still measured, never spelled: only the name is here."""


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


def _reference_payload() -> dict[str, Any]:
    """The committed reference, parsed once. A halt if it is not there, never a silent skip."""
    if not REFERENCE_SOURCE.exists():
        raise DerivedChartReportError(
            f"{REFERENCE_SOURCE.relative_to(REPO_ROOT)} is not in the tree, so the families the"
            " expectations file drops cannot be measured against anything"
        )
    return json.loads(REFERENCE_SOURCE.read_text(encoding="utf-8"))


def reference_frequencies() -> dict[str, dict[str, float]]:
    """Every reference spot's raise, call and the two together, in points.

    A raise is any of its named raise sizes plus its all-in leg, because the reference offers a
    shove at the vs-three-bet spots and dropping that leg would understate the very family this
    reads it for. `defence` is raise plus call, which is the same quantity this report's own
    `plays` column measures - money in with, either way - so the two columns are comparable.
    """
    found: dict[str, dict[str, float]] = {}
    for spot in _reference_payload()["spots"]:
        actions = {str(entry["label"]): float(entry["pct"]) for entry in spot["actions"]}
        raised = sum(
            weight
            for label, weight in actions.items()
            if label.startswith("Raise") or label.startswith("Allin")
        )
        called = actions.get("Call", 0.0)
        found[str(spot["key"])] = {
            "raise": raised,
            "call": called,
            "defence": raised + called,
        }
    return found


def reference_action_pct(kinds: tuple[str, ...]) -> dict[str, float]:
    """One of the three columns above, per reference spot, so a caller names what it wants."""
    return {
        key: sum(columns[kind] for kind in kinds)
        for key, columns in reference_frequencies().items()
    }


def reference_prices() -> dict[str, dict[str, float]]:
    """Per reference spot, the largest named raise it offers and the raise it is answering.

    A frequency comparison between two solves that price the same decision differently is part
    strategy and part price, and the only way to say which is to publish both prices. The raise
    hero is answering is the last raise in the reference's own `action_path`, so it is read off
    the spot rather than assumed from its name.
    """
    found: dict[str, dict[str, float]] = {}
    for spot in _reference_payload()["spots"]:
        sizes = [
            float(str(entry["label"]).split()[1])
            for entry in spot["actions"]
            if str(entry["label"]).startswith("Raise")
        ]
        answering = [
            float(step[1:]) for step in str(spot["action_path"]).split("-") if step.startswith("R")
        ]
        found[str(spot["key"])] = {
            "raise_to_bb": max(sizes) if sizes else 0.0,
            "answering_bb": answering[-1] if answering else 0.0,
        }
    return found


def chart_raise_to_bb(sizing: Mapping[str, Any], spot_key_text: str) -> float:
    """The largest price the committed sizing table offers hero at one spot, in big blinds."""
    return max(
        (
            float(price["to_bb"])
            for prices in dict(sizing.get(spot_key_text) or {}).values()
            for price in prices
        ),
        default=0.0,
    )


def raise_faced_to_bb(spot_key_text: str) -> float:
    """The size of the last raise already in when hero is asked, read off the key."""
    steps = [step for step in spot_key_text.split("/", 3)[3].split(",") if ":raise@" in step]
    return float(steps[-1].split("@")[1]) if steps else 0.0


def reference_hand_raises() -> dict[str, dict[str, float]]:
    """Per reference spot, how much of each hand class goes into a raise, in points.

    The aggregate frequencies already published can agree to within a point while the ranges
    disagree hand for hand, which is what a range that is the right size with the wrong contents
    looks like. Only a per-hand read sees that, and no relation in this phase can: they all
    compare a grid against its own other cells.
    """
    found: dict[str, dict[str, float]] = {}
    for spot in _reference_payload()["spots"]:
        weights: dict[str, float] = {}
        for label, listing in spot["strategy"].items():
            if not (label.startswith("Raise") or label.startswith("Allin")):
                continue
            for item in str(listing).split(","):
                if not item:
                    continue
                name, _, weight = item.partition(":")
                weights[name] = weights.get(name, 0.0) + 100.0 * float(weight)
        found[str(spot["key"])] = weights
    return found


def reference_hand_plays() -> dict[str, dict[str, float]]:
    """Per reference spot, how much of each hand class puts money in either way, in points.

    The raise-only read above is what a first-in spot has to be read on, hero having no call to
    make there. At a spot where hero faces a bet the question is whether the hand continues at
    all, so raise and call are added exactly as this report's own `plays` column adds them, and
    a hand the reference flats reads as played rather than as a disagreement with a chart that
    raises it.
    """
    found: dict[str, dict[str, float]] = {}
    for spot in _reference_payload()["spots"]:
        weights: dict[str, float] = {}
        for label, listing in spot["strategy"].items():
            if label.startswith("Fold"):
                continue
            for item in str(listing).split(","):
                if not item:
                    continue
                name, _, weight = item.partition(":")
                weights[name] = weights.get(name, 0.0) + 100.0 * float(weight)
        found[str(spot["key"])] = weights
    return found


def holds_an_ace_or_a_king(name: str) -> bool:
    """Whether a hand class holds one of the two cards a three-bet bluff is chosen for.

    Stated once and used on both sides of every count below, because the finding those counts
    carry is that the two directions do not overlap, and a predicate written twice is the way
    two directions come to be measured under two rules.
    """
    return "A" in name[:2] or "K" in name[:2]


def per_hand_disagreement(
    cells: Mapping[str, float], cited: Mapping[str, float]
) -> tuple[list[str], list[str]]:
    """The hand classes two grids disagree about by a wide margin, split by direction.

    One rule for all three families this report reads per hand, so the merged and first-in reads
    cannot be compared under two different thresholds. Wide is `WIDE_KICKER_GAP_PCT`, the same
    gap the kicker relation is stated over.
    """
    names = sorted(set(cells) | set(cited))
    return (
        [n for n in names if cited.get(n, 0.0) - cells.get(n, 0.0) >= WIDE_KICKER_GAP_PCT],
        [n for n in names if cells.get(n, 0.0) - cited.get(n, 0.0) >= WIDE_KICKER_GAP_PCT],
    )


def four_bet_no_blocker_mass(
    raises: Mapping[str, float], weights: Mapping[str, float]
) -> tuple[float, float]:
    """One grid's unpaired four-bet mass, and the part of it holding neither an ace nor a king.

    Pairs are excluded on both sides. The pair ladder is an accepted defect of this chart, so a
    share that counted pairs would be partly measuring a defect already ruled and published, and
    the question here is which unpaired hands were picked to bluff with.

    The caller supplies the weighting, and the two callers below want different ones. A per-spot
    column beside the reference is weighted by combinations alone, the reference publishing no
    reach; the figure over all 219 is weighted by combinations times arriving reach, which is the
    weighting every other frequency in this report uses.
    """
    total = bluffs = 0.0
    for name, weight in raises.items():
        if len(name) == 2:
            continue
        mass = weights.get(name, 0.0) * weight
        total += mass
        if not holds_an_ace_or_a_king(name):
            bluffs += mass
    return total, bluffs


def reference_key_for(spot_key_text: str) -> str | None:
    """The reference spot this committed key asks the same question as, or None.

    Same seat, same history. Hero first in is `RFI_<HERO>`; hero facing one open with nobody
    else in is `<HERO>_vs_<OPENER>_open`; hero having opened and facing one three-bet is
    `<HERO>_vs_<THREE-BETTOR>_3bet`. Everything else - an open plus a cold call, a squeeze, the
    blind-versus-blind limp - has no counterpart in the reference and returns None rather than
    being matched to something nearby, which is the mistake that would make the comparison look
    complete while pricing two different decisions against each other.
    """
    hero = hero_seat(spot_key_text)
    history = spot_key_text.split("/", 3)[3]
    if history == "rfi":
        return f"RFI_{REFERENCE_SEAT[hero]}"
    steps = history.split(",")
    if len(steps) == 1 and ":raise@" in steps[0] and not steps[0].startswith(f"{hero}:"):
        return f"{REFERENCE_SEAT[hero]}_vs_{REFERENCE_SEAT[steps[0].split(':')[0]]}_open"
    if len(steps) == 2 and steps[0].startswith(f"{hero}:raise@") and ":raise@" in steps[1]:
        return f"{REFERENCE_SEAT[hero]}_vs_{REFERENCE_SEAT[steps[1].split(':')[0]]}_3bet"
    return None


def _wrapped(names: Sequence[str], indent: str, per_line: int = 12) -> list[str]:
    """A long list of hand classes as indented rows, so a row stays readable in a text report."""
    return [
        indent + " ".join(names[start : start + per_line])
        for start in range(0, len(names), per_line)
    ]


def spot_menus(artifact: PreflopArtifact, *, positive: bool = False) -> dict[str, frozenset[str]]:
    """Each committed spot's menu, under either of the two readings of "offers".

    By default the menu is every action any of the spot's cells NAMES, whatever weight it carries,
    which is the reading a schema rule about the shape of a spot is stated over. With `positive`
    it is only the actions some class actually takes, which is the reading `tests/**` publishes as
    the menu shape. The two coincided until the arriving classes came apart from the menu and they
    now differ at 81 of the 249, so anything saying "offers hero a raise" has to say which it
    means: a criterion labelled under one reading and measured under the other is how a real
    measurement comes to be reported as empty.
    """
    return {
        spot_id: frozenset(
            action
            for actions in classes.values()
            for action, weight in actions.items()
            if weight > 0.0 or not positive
        )
        for spot_id, classes in cell_weights(artifact).items()
    }


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


def wheel_ace_cases(
    play: Mapping[str, Mapping[str, float]],
) -> tuple[tuple[str, str, str, float, float], ...]:
    """Every case the wheel-ace exemption covers, carrying the spot each was found at.

    `kicker_split` returns three counts, which is what the defect row needs and not what a
    reader needs. The exemption is a name match on the more-played hand: it asks whether that
    hand is `A5`, `A4`, `A3` or `A2` and asks nothing about the gap or about the spot. The
    poker story behind it - a suited wheel ace is the canonical three-bet bluff, nut-straight
    potential plus an ace blocker, so picking it over a middling suited ace is bluff selection
    - is a story about a spot where there is bluff selection to do. A first-in raise has none:
    nobody polarises an opening range, the hands that show a profit are opened, and a hand
    that dominates the wheel ace on kicker and on high card gives up only the A2345 straight.
    So the cases are returned rather than only counted, and the section splits them by how
    many raises are already in.
    """
    found: list[tuple[str, str, str, float, float]] = []
    for spot_id, cells in play.items():
        for stronger, weaker, high, low in inversions(cells, ROW_KICKERS):
            if stronger[0] == "A" and weaker[:2] in WHEEL_ACE_KICKERS:
                found.append((spot_id, stronger, weaker, high, low))
    return tuple(sorted(found))


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
    whole_call_cells: dict[str, int]
    squeeze_folds: dict[str, float]
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
    whole_call_cells: dict[str, int] = {}
    squeeze_folds: dict[str, float] = {}
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
            if exclusion_code(by_path, node) == lookup.DERIVATION_BIG_BLIND_SQUEEZE_SPOT:
                squeeze_folds[key] = 100.0 * sum(
                    node.action_frequency(index)
                    for index, action in enumerate(node.actions)
                    if action.kind == "fold"
                )
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
            # Read off the basis points rather than off `_menu_weights`' percent, so "the
            # hand's whole weight" is an exact integer equality and not a float at 100.0.
            whole = sum(
                1
                for name in HAND_CLASSES
                if node.reach_bp[gtopen_class_index(name)] > 0
                and sum(
                    node.strategy_bp[index][gtopen_class_index(name)]
                    for index, action in enumerate(node.actions)
                    if action.kind == "call"
                )
                == QUANTISATION_SCALE
            )
            if whole:
                whole_call_cells[key] = whole
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
        whole_call_cells=whole_call_cells,
        squeeze_folds=squeeze_folds,
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
    raises: dict[str, float]
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
    squeezed = counts.excluded.get(lookup.DERIVATION_BIG_BLIND_SQUEEZE_SPOT, 0)
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
        f"points. The {squeezed} big-blind squeeze spots return when the flats are repaired."
        " Everything",
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
        f"And {counts.committed} nodes are not self-evidently {counts.committed} keys. A converter",
        "that dropped one node while inventing one key publishes the identical count, so the",
        "artifact and the walk are compared key by key and both directions are named:",
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
    squeezed = measured.walk.census.excluded.get(lookup.DERIVATION_BIG_BLIND_SQUEEZE_SPOT, 0)
    folds = measured.walk.squeeze_folds
    # Measured off the printed figures, so the count is the one a reader gets by adding the
    # two columns rather than one taken at a precision the report does not publish.
    short_rows = {
        key: 100.0 - (round(multiway, 4) + round(folded + heads_up, 4))
        for key, (folded, heads_up, multiway) in splits.items()
        if round(multiway, 4) + round(folded + heads_up, 4) != 100.0
    }
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
        "in it. The two are the halves of one mass and a row publishing exposure alone could be",
        "over any denominator at all.",
        "",
        "They do not always close on a hundred, and the shortfall is published rather than",
        "rounded past. Mass that reaches a node no hand class arrives at is dropped rather than",
        "redistributed, so it never reaches a terminal and never lands in either column:",
        "",
        f"  rows adding to a hundred  {len(splits) - len(short_rows)} of {len(splits)}",
        f"  rows falling short  {len(short_rows)}"
        f"  widest shortfall  {max(short_rows.values(), default=0.0):.4f} points",
        "",
        "A row has three columns and only two quantities, and that is said here rather than left",
        "for a reader to notice by adding them up. `exposure` and `multiway` are the SAME number",
        "printed twice - `terminal_split_pct` returns folded, heads-up and multiway, and both",
        "columns read its multiway leg, so they are one quantity by definition rather than two",
        "that happen to agree. The pair a reader should add is `multiway` and `heads-up`, which",
        "make a hundred wherever the walk loses nothing; adding all three columns gives that plus",
        "the multiway figure again.",
        "A frozen test requires the first two columns to be equal, so this stage cannot collapse",
        "them, and a later phase that gives the second column a measurement of its own - the",
        "un-renormalised exposure with hero's cold call left in would be the informative one -",
        "has to change that test with it.",
        "",
        "The filter is blindest exactly where the mispricing has already turned a call into a",
        f"fold. The {squeezed} big-blind squeeze spots passed this clause BECAUSE the big blind",
        "folds most of its range there, so almost nothing of its mass reaches the three-way flop,",
        "and they are refused by a clause of their own instead. That fold rate is a range and not",
        "a figure, so every spot's own is printed below rather than one of them standing for the",
        f"family: it runs from {min(folds.values()):.4f} to {max(folds.values()):.4f} percent, and"
        f" {sum(1 for value in folds.values() if value < 90.0)} of the {len(folds)} are under 90.",
        "Any later build re-measures these rather than carrying them forward",
        "(MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN).",
        "",
    ]
    for key in sorted(folds):
        lines.append(f"  squeeze spot  {key}  big blind folds {folds[key]:.4f}")
    lines.append("")
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
    downstream = tuple(key for key in sorted(arrivals) if f"{hero_seat(key)}:call" in key)
    total_ppb = sum(arrivals.values())
    family_ppb = sum(arrivals[key] for key in downstream)
    ratio = percent(len(downstream), len(arrivals)) / (100.0 * family_ppb / total_ppb)
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
        "",
        "The same grain settles a count this phase can otherwise be read two ways about. The chart",
        "merges hero's cold call away, so a committed spot whose own key records hero calling is a",
        "spot the bot's own play cannot reach. There are a lot of them by count and almost none of",
        "them by weight, and both readings are printed because either one alone misleads:",
        "",
        f"  downstream of hero's own call  {len(downstream)} of {len(arrivals)} spots"
        f"  {percent(len(downstream), len(arrivals)):.1f} percent by count",
        f"  the same family by arrival  {family_ppb:,} of {total_ppb:,} ppb"
        f"  {100.0 * family_ppb / total_ppb:.4f} percent by weight",
        "",
        "Read it as: as the tree the BOT plays, every one of these is dead and no packet may count",
        "them toward what the bot answers - but what they are worth is the weight row and not the",
        f"count row, and the two rows differ by a factor of {ratio:,.0f}.",
        "",
        "As a reference a HUMAN is drilled on they are legitimate, because the range at each is",
        "the solve's own range for a cold-caller and a human student does cold-call: the right",
        "range at the right spot for a student, at a spot this bot's own upstream merge means it",
        "never sees. Those are two claims and this report makes them separately.",
        "",
        "What it may not do, and does not do, is offer `the bot never cold-calls` as the",
        "justification for the merge and then count the spots downstream of a cold call under",
        "that same sentence.",
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
    exempted = wheel_ace_cases(measured.play)
    by_depth: dict[int, list[tuple[str, str, str, float, float]]] = {}
    for case in exempted:
        by_depth.setdefault(raises_faced_in_key(case[0]), []).append(case)
    first_in = tuple(by_depth.get(0, ()))
    wide_gap = sum(1 for case in exempted if case[4] - case[3] >= WIDE_KICKER_GAP_PCT)
    near_pure = sum(1 for case in exempted if case[3] < 5.0 and case[4] > 95.0)
    invisible = raise_inversions_invisible(measured.play, measured.raise_weight)
    solve_cells, solve_pure, solve_mixed = measured.walk.solve_purity
    _, published_pure, published_mixed = purity(cell_weights(measured.artifact))
    defends = [measured.plays[key] for key in measured.family("the big blind facing an open")]
    pair = counted["pair ladder"]
    kicker = counted["row kicker ladder"]
    raise_action = counted["pair ladder on the raise weight"]
    merged_spots = len(measured.walk.merged_spot_keys)
    moved = measured.walk.merged_cell_count
    lines = [
        "Four defects this phase accepts on purpose, each with the measurement it was accepted on.",
        "They are defects and are recorded as defects; none is small print, and the packet",
        "requirements forbid that word for exactly this list.",
        "",
        f"  defect  the big blind over-folds against every opener   it defends {min(defends):.2f}"
        f" to {max(defends):.2f} percent where rake-free solves are roughly 40 through 65, and its"
        " flat barely moves with who opened",
        f"  defect  the pair ladder inverts   {pair} cases on play-not-fold and {raise_action} on"
        f" the raise weight the bot plays, {invisible} of those invisible to play-not-fold",
        f"  defect  the kicker row ladder inverts   {kicker} cases, of which {wheel} are exempted"
        f" as the wheel-ace premium - correct poker at {wheel - len(first_in)} of them and a name"
        f" match with no poker story at the {len(first_in)} first-in spots below - {wide} have no"
        f" poker story at a 50 point gap or wider, and {narrow} below it",
        f"  defect  the merged flats play differently   {moved} cells move at {merged_spots}"
        " spots, and three-betting 66 commits 7.5 big blinds and can face a four-bet where the"
        " solve would have seen a cheap flop",
        "",
        "The wheel-ace cases are separated out because at almost all of them they are correct",
        "poker, and lumping them in overstates what is wrong with the chart by about half: a",
        "suited wheel ace makes the nut straight and is less dominated than a middling suited ace,",
        f"so {wheel - len(first_in)} of the {kicker} are the premium GTOpen's own fit measures",
        f"and not a defect. The other {len(first_in)} the exemption catches are caught by name",
        "alone and the section below says why the argument does not reach them.",
        "The three parts add back to the family, which is the check that the split has the right",
        "members rather than merely the right size.",
        "",
        "What the exemption itself cannot see, published because the sentence above would",
        "otherwise claim more than the measurement supports. `kicker_split` exempts a case",
        "whenever the more-played hand is A5, A4, A3 or A2, and it tests nothing else - not the",
        "size of the gap, and not the spot. The gap it is not testing is usually large:",
        "",
        f"  exempted cases  {wheel}"
        f"  with a gap of {WIDE_KICKER_GAP_PCT:.0f} points or wider  {wide_gap}"
        f"  with the better ace under 5 percent and the wheel ace over 95  {near_pure}",
        "",
        "And the spot it is not testing is the one the poker story turns on. A suited wheel ace is",
        "the canonical three-bet bluff - nut-straight potential plus an ace blocker - so choosing",
        "it over a middling suited ace is bluff selection, and bluff selection is what a strong",
        "player does at a three-bet, a squeeze or a defence. A FIRST-IN raise has no bluff",
        "selection in it at all: nobody polarises an opening range, the hands that show a profit",
        "are opened, and a better ace dominates the wheel ace on kicker and on high card while",
        "giving up only the A2345 straight, worth on the order of a point of equity. So the split",
        "that matters is by how many raises are already in when hero is asked:",
        "",
    ]
    for faced in sorted(by_depth):
        where = {
            0: "first-in, no bluff selection to justify it",
            1: "facing an open - three-bet, squeeze or defence",
            2: "facing a three-bet",
        }.get(faced, "deeper")
        lines.append(f"  exempted at raises faced  {faced}  {len(by_depth[faced])}  {where}")
    lines += [
        "",
        f"The {wheel - len(first_in)} exempted at a raise already in are the ruled case and this",
        "report does not reopen them. The first-in ones are named, because a reader owed the",
        "claim is owed the instances:",
        "",
    ]
    for spot_id, stronger, weaker, high, low in first_in:
        lines.append(
            f"  first-in exempted  {spot_id}  {stronger} played {high:.2f}"
            f"  under {weaker} played {low:.2f}  gap {low - high:.2f}"
        )
    lines += [
        "",
        f"All {len(first_in)} are exempted by name and the exemption's argument reaches none of",
        "them, so the packet may not carry them as correct poker. They are also the smaller half",
        "of what is wrong at those spots, because a ladder compares neighbours and a hole two",
        "cells wide hides in it. The opening range's own composition against the outside",
        "reference is measured further down, under the expectations, where the hole is visible",
        "whole.",
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
        "action` was never available to it. The second pair is the chart this phase writes. The",
        f"merge moved {moved} cells and the pure share moved by"
        f" {published_pure - solve_pure:.2f} points over",
        f"the same {solve_cells}, which is about"
        f" {round((published_pure - solve_pure) * solve_cells / 100)} cells - so most of what the",
        "merge moved was already pure before it, and a sentence saying the merge turned",
        "every moved cell pure would be wrong twice over. A generator computing purity off the",
        "file it just wrote would read only the second pair. Both are printed and each is",
        "labelled, because this phase has already shipped one figure under two meanings.",
    ]
    return lines


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
    cited_flats = {
        position: reference_action_pct(("call",))[f"BB_vs_{REFERENCE_SEAT[position]}_open"]
        for position in OPENERS
    }
    lines += [
        "",
        f"  flat spread  {spread:.2f} points",
        "",
        "That spread is the fingerprint: the flat is nearly invariant to who opened, across",
        "openers whose own ranges span more than thirty-five points",
        "(BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT). It is a separate finding from the level and",
        "it is not what the cost below prices.",
        "",
        "The flat does not merely fail to move, and the direction is published because an",
        "invariant flat could be a tolerance artifact and an inverted one cannot. The reference's",
        "own big-blind calls climb the whole way through the four non-blind openers; this chart's",
        "climb to the cutoff and then fall for the button and the small blind, the two widest",
        "openers of the five, which are the two a correct chart's flat rises fastest against:",
        "",
    ]
    for position in OPENERS:
        lines.append(
            f"  flat vs {position}  chart {flats[position]:.3f}"
            f"  raked reference {cited_flats[position]:.3f}"
        )
    cited_span = max(cited_flats.values()) - min(cited_flats.values())
    lines += [
        "",
        f"  spread  chart {spread:.2f} points  raked reference {cited_span:.2f} points",
        "",
        "The reference column is the SHAPE and not the level. It is a raked solve and its flats",
        "are not a target, but the order it puts them in does not turn on the rake basis, and this",
        "chart does not reproduce it. That belongs under the entry above rather than anywhere new.",
        "",
        "And the over-folding is not confined to this seat. The same realization fit prices every",
        "seat that has to answer an open, and where the outside reference reaches those spots the",
        "chart reads narrower there too - the measurement is under the expectations below, on the",
        "merged family. A reader who takes this section's naming of the big blind as meaning the",
        "merged three-bet ranges are sound is being misled, and the defect list above names the",
        "seat where the cost was priced rather than the only seat where the level is wrong.",
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
        "and the same fold costs 12.5 to 130 times as much, depending on which end of each band",
        "is read against which - the four pairings of the two rows above, none of which this phase",
        "published as a single multiplier until now. The band cannot be narrowed without",
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
        "this phase withholds.",
        "",
        "That argument holds against a four-bet frequency that looks comfortable and does not hold",
        "against one that does not, and the frequency is not comfortable. It is published against",
        "the outside reference under the expectations below, where it is BELOW the reference at",
        "every spot the reference can reach while total defence is wider at every one of them - so",
        "the chart answers a three-bet by calling far more and four-betting far less. None of that",
        "is evidence about the unfitted terminal, for the reason the paragraph above gives; it is",
        "a measurement a reader is owed instead of a sentence saying a measurement would be empty,",
        "and it is where a later phase taking up the four-bet family starts.",
    ]
    return lines


def menus_section(measured: Measured) -> list[str]:
    """Three families, three menus, and the merge shown preserving the range exactly."""
    merged = measured.family("the merged spots")
    big_blind = measured.family("the big blind facing an open")
    three_bet = measured.family("the three-bet-facing spots")
    small_blind_merges = sum(1 for key in merged if hero_seat(key) == "SB")
    lines = [
        "The bot never cold-calls. Money in behind an opener with nothing of hero's own already",
        "in buys a multiway pot out of position, so where hero faces an open and has nothing in",
        "BEYOND THE BLINDS the solve's call is merged into his raise. That wording is the whole",
        f"rule, because {small_blind_merges} of these {len(merged)} spots ARE the small blind,",
        "which has posted 0.5: a blind is posted rather than chosen, so calling from there is",
        "still money going in behind an opener and it merges like the rest. The big blind is the",
        "one seat exempted, and not because it has posted more - because it closes the action.",
        "Its call ends the betting into a heads-up pot at a price it is already half paying,",
        "which is a defence rather than a cold call. The small blind's does neither: the big",
        "blind is still behind it and can raise. Nor is a seat that opened and now faces a",
        "three-bet cold, its own raise being already in. Three families, three menus:",
        "",
        f"  family  the big blind facing an open  spots {len(big_blind)}  menu fold/call/raise",
        f"  family  the merged spots  spots {len(merged)}  menu fold/raise",
        f"  family  the three-bet-facing spots  spots {len(three_bet)}  menu fold/call/raise",
        "",
        f"  cells moved  {measured.walk.merged_cell_count}",
        "",
        "Merged and not deleted, and the difference is a hand with an answer against a hand with",
        f"none: at {len(measured.walk.whole_call_cells)} of these {len(merged)} spots, across"
        f" {sum(measured.walk.whole_call_cells.values())} of the"
        f" {measured.walk.merged_cell_count} moved cells, a hand's",
        "whole weight sits on calling, so deleting would leave a row of zeroes, and printing fold",
        "would publish `fold pocket nines to an open`. Both counts are over the merging spots and",
        "nothing wider - the same walk over every committed spot is a different measurement.",
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
        "",
        "The merge preserving the range is not the same claim as the range being right, and the",
        "level at these spots is measured against the outside reference under the expectations",
        "below. It reads narrower there at almost every spot the reference can reach, in the one",
        "direction a rake-free solve is not supposed to go - the same over-folding the defect list",
        "names in the big blind, from the same realization fit, at a family the defect list does",
        "not name. A reader may not take the merged three-bet ranges as sound on the strength of",
        "the two columns above.",
    ]
    return lines


def expectations_section(measured: Measured) -> list[str]:
    """The one column this repo did not produce, printed and graded against nothing."""
    reference = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    quoted = {
        "opens": reference["open_frequency_pct"],
        "big blind defends": reference["big_blind_defence_pct"],
    }
    defence = reference_action_pct(("defence",))
    faced = sorted(
        (key, str(reference_key_for(key)))
        for key in measured.family("the merged spots")
        if (reference_key_for(key) or "").endswith("_open")
    )
    three_bet_family = measured.family("the three-bet-facing spots")
    three_bet = sorted(
        (key, str(reference_key_for(key)))
        for key in three_bet_family
        if (reference_key_for(key) or "").endswith("_3bet")
    )
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
        "",
        "Those two families are two of the five this chart ships, and until this block was written",
        "they were the only two anything outside the repo was read against - and they are the two",
        "that pass. The file the expectations are distilled from carries full per-hand strategies",
        f"for {len(defence)} spots ({REFERENCE_SOURCE.relative_to(REPO_ROOT)}), so the rest of",
        "what it can reach is read below. The same caveat holds throughout and it is the whole",
        "caveat: the reference is RAKED, so this chart reading WIDER than it is a floor cleared",
        "and never a level confirmed, and this chart reading NARROWER than it is a direction a",
        "rake-free solve is not supposed to go. Nothing below gates anything.",
        "",
        f"First, defence against a single open at the merged family - the {len(faced)} spots where",
        "hero has nothing in beyond the blinds, faces one open and nobody else is in."
        f" {sum(1 for key, _ in faced if hero_seat(key) == 'SB')} of them are the small blind,",
        "whose posted 0.5 is not something it chose to put in; the big blind, which closes the",
        "action, is a family of its own and is read separately below. These are the same spots",
        "whose raise-plus-call the menu section prints; here they are beside a figure from",
        "outside:",
        "",
    ]
    deltas: list[float] = []
    for key, reference_key in faced:
        cited = defence[reference_key]
        derived = measured.plays[key]
        deltas.append(derived - cited)
        lines.append(
            f"  vs one open  {key}  defends {derived:.4f}  raked reference {cited:.3f}"
            f"  {'wider' if derived > cited else 'narrower'}  {derived - cited:+.4f}"
        )
    tighter = [-delta for delta in deltas if delta < 0.0]
    lines += [
        "",
        f"  narrower at  {len(tighter)} of {len(deltas)} spots"
        f"  mean shortfall over all  {-sum(deltas) / len(deltas):.4f} points"
        f"  over the narrower  {sum(tighter) / len(tighter):.4f} points",
        f"  widest shortfall  {max(tighter):.4f} points"
        f"  narrowest  {min(tighter):.4f} points",
        "",
        "Read that as the finding it is. The accepted defect above says the BIG BLIND over-folds",
        "and names the cause as the fit's own realization number for facing a bet in a",
        f"single-raised pot. That same fit prices these {len(deltas)} spots, and at"
        f" {len(tighter)} of the {len(deltas)} this chart is narrower than a solve that is",
        "paying rake and that, from the small blind, is three-betting at a worse price than this",
        "one does.",
        "So the over-folding is a property of every seat that has to answer an open rather than of",
        "the big blind, and a reader may not take the defect list's naming of one seat as clearing",
        "the merged three-bet ranges. What this measurement does not do is re-price anything or",
        "move a weight: the four accepted defects are the four that were ruled, and whether the",
        "list is extended to name this family is a ruling and not a measurement.",
        "",
        f"Second, hero's own four-bet at the {len(three_bet)} spots where he opened and then faced",
        "a three-bet - the family the bands section declines to publish a band over. Both columns",
        "are printed because they go opposite ways:",
        "",
    ]
    raised = reference_action_pct(("raise",))
    prices = reference_prices()
    sizing = PreflopSizingTable.from_repo().raise_to_bb
    shortfalls: list[float] = []
    below = wider = dearer = 0
    for key, reference_key in three_bet:
        cited_raise = raised[reference_key]
        cited_defence = defence[reference_key]
        own = measured.raises[key]
        shortfalls.append(100.0 * (cited_raise - own) / cited_raise)
        below += own < cited_raise
        wider += measured.plays[key] > cited_defence
        multiple = chart_raise_to_bb(sizing, key) / raise_faced_to_bb(key)
        cited = prices[reference_key]
        cited_multiple = cited["raise_to_bb"] / cited["answering_bb"]
        dearer += multiple > cited_multiple
        lines.append(
            f"  vs one three-bet  {key}  four-bets {own:.2f}"
            f"  raked reference {cited_raise:.2f}"
            f"  defends {measured.plays[key]:.2f}  raked reference {cited_defence:.2f}"
            f"  price {multiple:.2f}x  raked reference {cited_multiple:.2f}x"
        )
    lines += [
        "",
        f"  four-bet below the reference at  {below} of {len(three_bet)} spots"
        f"  by {min(shortfalls):.1f} to {max(shortfalls):.1f} percent relatively",
        f"  total defence wider at  {wider} of {len(three_bet)} spots",
        f"  four-bet priced dearer than the reference's at  {dearer} of {len(three_bet)} spots",
        "",
        "So this chart answers a three-bet by calling far more and four-betting far less. The",
        "defence column clears the floor at every spot and the four-bet column is below at every",
        "spot, which is a shape rather than a scatter.",
        "",
        "The price column is why it is published and not accepted as a fifth defect. It is the",
        "four-bet as a multiple of the three-bet being answered, and this chart's four-bet is the",
        "dearer of the two at every one of these spots - the reference answers a bigger three-bet",
        "with a raise that is proportionally smaller. A dearer four-bet is four-bet less often by",
        "construction, so part of this gap is a price difference rather than a strategy",
        "difference, which is PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED showing up in the",
        "output rather than a new finding. Separating the two halves needs a rake-free reference",
        "at this solve's own prices, which this repo does not commit",
        "(NOTHING-READS-THE-DEFENCE-LEVEL-AGAINST-A-RAKE-FREE-REFERENCE). It is also not evidence",
        "about the unfitted terminal, for the reason the bands section gives. What it is: the",
        "measurement a reader is owed in place of a sentence saying a measurement would be empty,",
        "and the number a later phase taking up the four-bet family starts from.",
        "",
        "Third, the first-in family, per HAND rather than per aggregate. The aggregate figures at",
        "the top of this section agree with the reference to about a point, and a range can be",
        "the right size with the wrong contents. So every hand class whose weight differs by"
        f" {WIDE_KICKER_GAP_PCT:.0f} points or more is counted and named, and the direction is",
        "counted on each side:",
        "",
    ]
    hand_raises = reference_hand_raises()
    for position in OPENERS:
        key = f"t6/d100/{position}/rfi"
        reference_key = str(reference_key_for(key))
        cited_cells = hand_raises[reference_key]
        cells = measured.play[key]
        folded, opened = per_hand_disagreement(cells, cited_cells)
        lines += [
            f"  first-in  {position}  opens {measured.plays[key]:.3f}"
            f"  raked reference {raised[reference_key]:.2f}"
            f"  hands differing by {WIDE_KICKER_GAP_PCT:.0f} points or more"
            f"  {len(folded) + len(opened)}",
            f"    folded here, opened there  {len(folded)}",
            *_wrapped(folded, "      "),
            f"    opened here, folded there  {len(opened)}",
            *_wrapped(opened, "      "),
        ]
    lines += [
        "",
        "The small blind row is not a comparison and is printed only so the family is complete:",
        "the reference limps from that seat and this solve has no limp branch, so its opening",
        "range absorbs the limps and every hand that differs is on that one side.",
        "",
        "The other four rows are the finding. The aggregates agree to about a point while the",
        "contents disagree in dozens of places, and the disagreement has a direction rather than",
        "being scatter: offsuit broadways and high-card suited hands out, small pairs and suited",
        "connectors and gappers in. The concrete case is the ace row at the lightest-opening seat,",
        "where the exempted first-in kicker inversion in the defects section sits - the two suited",
        "aces beside the wheel aces are folded pure while all four wheel aces open pure, and the",
        "reference opens all twelve suited aces from that seat. A ladder relation compares",
        "neighbours, so a hole two cells wide shows up as one case, and the wheel-ace exemption",
        "then reports that one case as correct poker. This row is where the hole is visible whole.",
        "",
        f"Fourth, the SAME per-hand read over the merged family - the {len(faced)} spots whose",
        "aggregate is the first block above. The aggregate there is short of the reference by",
        "about a point and reads as tightness. Per hand it is not tightness, it is an inversion,",
        "and the two directions do not overlap at a single hand class. Each row carries how many",
        "of its disagreeing classes hold an ace or a king, which is the whole finding:",
        "",
    ]
    hand_plays = reference_hand_plays()
    merged_folded = merged_played = merged_folded_blockers = merged_played_blockers = 0
    for key, reference_key in faced:
        folded, played = per_hand_disagreement(measured.play[key], hand_plays[reference_key])
        blocking = sum(1 for name in folded if holds_an_ace_or_a_king(name))
        bluffing = sum(1 for name in played if holds_an_ace_or_a_king(name))
        merged_folded += len(folded)
        merged_played += len(played)
        merged_folded_blockers += blocking
        merged_played_blockers += bluffing
        lines += [
            f"  merged per hand  {key}  folded here, played there  {len(folded)}"
            f"  of which hold an ace or a king  {blocking}"
            f"  played here, folded there  {len(played)}"
            f"  of which hold an ace or a king  {bluffing}",
            *_wrapped(folded, "      folded here, played there   "),
            *_wrapped(played, "      played here, folded there   "),
        ]
    king_queen_folded = sum(
        1 for key, _ in faced if measured.play[key].get("KQo", 0.0) <= 100.0 - PURE_PCT
    )
    cutoff = "t6/d100/CO/LJ:raise@2.5"
    cutoff_bluffs = [
        SPELLED[name]
        for name in ("JTs", "76s")
        if measured.play[cutoff].get(name, 0.0) >= PURE_PCT
    ]
    cutoff_folds = [
        SPELLED[name]
        for name in ("AQo", "KQo")
        if measured.play[cutoff].get(name, 0.0) <= 100.0 - PURE_PCT
    ]
    cutoff_marginals = [(name, measured.play[cutoff].get(name, 0.0)) for name in ("ATs", "KTs")]
    control_folded = control_played = control_folded_blockers = control_played_blockers = 0
    for key in measured.family("the big blind facing an open"):
        folded, played = per_hand_disagreement(
            measured.play[key], hand_plays[str(reference_key_for(key))]
        )
        control_folded += len(folded)
        control_played += len(played)
        control_folded_blockers += sum(1 for name in folded if holds_an_ace_or_a_king(name))
        control_played_blockers += sum(1 for name in played if holds_an_ace_or_a_king(name))
    lines += [
        "",
        f"  merged family  folded here, played there  {merged_folded}"
        f"  holding an ace or a king  {merged_folded_blockers}"
        f"  played here, folded there  {merged_played}"
        f"  holding an ace or a king  {merged_played_blockers}",
        f"  big blind control  folded here, played there  {control_folded}"
        f"  holding an ace or a king  {control_folded_blockers}"
        f"  played here, folded there  {control_played}"
        f"  holding an ace or a king  {control_played_blockers}",
        "",
        "Say what that is in poker. Standard theory three-bets the hands that BLOCK the opener's",
        "continuing range - the aces and the kings - and folds or flats the connectors that block",
        f"nothing. This chart does the reverse: all {merged_folded} classes it folds where the",
        f"reference plays hold an ace or a king, and {merged_played_blockers} of the"
        f" {merged_played} it plays where the",
        f"reference folds do. King-queen offsuit is folded pure at {king_queen_folded} of the"
        f" {len(faced)} spots, and it",
        "shows in nine of the per-spot lists above rather than ten because at the tenth the",
        "reference plays it under this section's fifty-point bar, so the case does not qualify.",
        "At the cutoff",
        f"facing a lojack open it three-bets {' and '.join(cutoff_bluffs)} pure while folding",
        f"{' and '.join(cutoff_folds)} pure, with"
        f" {', '.join(f'{SPELLED[n]} at {v:.3f} percent' for n, v in cutoff_marginals)}.",
        "Nothing in bluff selection reaches that ordering: the hands it folds block better AND",
        "hold more equity than the ones it three-bets, so the polarization argument this report",
        "makes for the wheel aces in the defects section points the other way here.",
        "",
        "Three things this is NOT, each measured rather than assumed. It is not the merge: the",
        "fold weight at these spots is the solve's OWN fold with the call branch still on the",
        "menu, and the merge only ever moves call into raise, so the solve folds ace-ten suited",
        "at the cutoff against an under-the-gun open with a cold call available. It is not the",
        "rake: rake makes a cold call worse, so the RAKED column is the one that should be",
        "dropping the marginal aces and kings, and the direction here is the one this section's",
        "own floor rule says a rake-free solve is not supposed to go. And it is not the big",
        "blind's accepted over-folding: the control row above runs the identical read over the",
        "five big-blind spots, where hero keeps a call branch, and the one-direction signature is",
        "absent - which is what makes it a property of these ten spots and not of the chart.",
        "",
        "What that costs the packet: the accepted defect naming the big blind does not cover this",
        "family, the merged family's shape is not sound whatever its size is, and a student",
        f"drilled on these {len(faced)} grids is being taught to fold king-queen offsuit to an"
        " open at every one of them.",
        "It is published here rather than repaired because repairing it is a re-solve, which this",
        "phase does not do, and because the conversion itself is exact against the export at all",
        f"{measured.walk.solve_purity[0]} cells at non-zero reach"
        " (PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS,",
        "whose word for the size of this was `slightly`).",
        "",
        f"Fifth, WHICH hands do the four-betting at the {len(three_bet)} spots the reference"
        f" reaches out of the",
        f"{len(three_bet_family)} in the family -"
        f" {100.0 * len(three_bet_family) / len(measured.play):.0f} percent of this chart -",
        "because the second block published how OFTEN and nobody had asked what with. A",
        "four-bet bluff is chosen for its blockers: it wants the ace and the king that the hands",
        "continuing against it are made of. Two columns per spot - how much king-ten or king-jack",
        "suited four-bets, which is the reference's own bluff, and the share of UNPAIRED four-bet",
        "mass held by hands with neither an ace nor a king, which is the opposite of a blocker:",
        "",
    ]
    king_here = king_there = no_blocker_higher = 0
    shares: list[float] = []
    priced_alike: list[tuple[str, float, float]] = []
    combinations = {name: float(class_combos(name)) for name in HAND_CLASSES}
    for key, reference_key in three_bet:
        cited_cells = hand_raises[reference_key]
        cells = measured.raise_weight[key]
        blocker_here = max(cells.get("KTs", 0.0), cells.get("KJs", 0.0))
        blocker_there = max(cited_cells.get("KTs", 0.0), cited_cells.get("KJs", 0.0))
        total, bluffs = four_bet_no_blocker_mass(cells, combinations)
        cited_total, cited_bluffs = four_bet_no_blocker_mass(cited_cells, combinations)
        share = 100.0 * bluffs / total if total else 0.0
        cited_share = 100.0 * cited_bluffs / cited_total if cited_total else 0.0
        shares.append(share)
        king_here += blocker_here > 50.0
        king_there += blocker_there > 50.0
        no_blocker_higher += share > cited_share
        if abs(prices[reference_key]["answering_bb"] - raise_faced_to_bb(key)) <= 0.5:
            priced_alike.append((key, share, cited_share))
        lines.append(
            f"  four-bet mix  {key}  KTs/KJs {blocker_here:.3f}"
            f"  raked reference {blocker_there:.3f}"
            f"  unpaired four-bet mass with no ace and no king {share:.1f}"
            f"  raked reference {cited_share:.1f}"
        )
    weighted_total = weighted_bluffs = 0.0
    carrying = 0
    # Arrival is a property of the walk, so the heaviest spot is picked over what the walk
    # carries rather than by indexing it with a chart key. On a committed artifact the two key
    # sets are identical and this reads the same; on an artifact that disagrees with the walk,
    # `main` has already refused it before this renders, and indexing the walk here turned that
    # refusal into a `KeyError` instead - which is how the canary that proves the refusal matters
    # came to read a crash as a kill. Regression introduced 2026-09-05 at 25f0d76 and caught by
    # `check_gate_bite` at the closeout, three commits later.
    heaviest = max(three_bet_family, key=lambda key: measured.walk.arrivals.get(key, 0.0))
    for key in three_bet_family:
        total, bluffs = four_bet_no_blocker_mass(measured.raise_weight[key], measured.weights[key])
        weighted_total += total
        weighted_bluffs += bluffs
        carrying += total > 0.0
    pure_bluffs = sorted(
        name
        for name, weight in measured.raise_weight[heaviest].items()
        if weight >= PURE_PCT and not holds_an_ace_or_a_king(name) and len(name) > 2
    )
    blockers_held = [
        name
        for name in measured.raise_weight[heaviest]
        if name.endswith("s") and holds_an_ace_or_a_king(name)
    ]
    flatted = sorted(
        name
        for name in blockers_held
        if measured.play[heaviest].get(name, 0.0) >= PURE_PCT
        and measured.raise_weight[heaviest].get(name, 0.0) <= 100.0 - PURE_PCT
    )
    valued = sorted(
        name
        for name in blockers_held
        if measured.raise_weight[heaviest].get(name, 0.0) >= PURE_PCT
    )
    # Suited connectors only, because that is the comparison the four-bet list invites: the
    # grid raises 86s and 96s, which are the same shape one and two gaps wider than what it
    # folds, so naming every folded hand would bury the one pair of rows a reader can weigh.
    folded_connectors = sorted(
        name
        for name in measured.raise_weight[heaviest]
        if name.endswith("s")
        and not holds_an_ace_or_a_king(name)
        and abs(HIGH_TO_LOW_RANKS.index(name[0]) - HIGH_TO_LOW_RANKS.index(name[1])) == 1
        and measured.play[heaviest].get(name, 0.0) <= 100.0 - PURE_PCT
    )
    lines += [
        "",
        f"  KTs or KJs four-betting above 50 percent at  {king_here} of {len(three_bet)} spots"
        f"  raked reference  {king_there} of {len(three_bet)}",
        f"  no-blocker share higher here at  {no_blocker_higher} of {len(three_bet)} spots"
        f"  here {min(shares):.1f} to {max(shares):.1f} percent",
        f"  over all {len(three_bet_family)} three-bet-facing spots  arrival-weighted"
        f"  {100.0 * weighted_bluffs / weighted_total:.2f} percent"
        f"  carrying four-bet mass  {carrying}",
        f"  at the {len(priced_alike)} spots priced within half a big blind of each other"
        f"  here {min(share for _, share, _ in priced_alike):.1f}"
        f" to {max(share for _, share, _ in priced_alike):.1f} percent"
        f"  raked reference {min(cited for _, _, cited in priced_alike):.1f}"
        f" to {max(cited for _, _, cited in priced_alike):.1f}",
        "",
        "The reference four-bets a king-blocker hand and this chart never does. Where its four-bet",
        "mass goes instead is hands that block nothing, at every spot the reference can be read",
        f"against, and the last row is why that is not the price: at the {len(priced_alike)}",
        "spots where the two solves are answering three-bets within half a big blind of each",
        "other the gap is as wide as anywhere. The family's most-arrived-at grid shows the whole",
        f"shape at once. At {heaviest}",
        f"the chart four-bets to {chart_raise_to_bb(sizing, heaviest):.1f} big blinds with these,"
        f" none of which holds an ace or a king:",
        *_wrapped(pure_bluffs, "    "),
        "while flat-calling these, every one of which does:",
        *_wrapped(flatted, "    "),
        "That is every suited ace and every suited king in hero's range bar"
        f" {' and '.join(valued)}, which",
        f"four-bet for value. It also folds the suited connectors {' '.join(folded_connectors)}"
        " outright, so",
        "even among the hands that block nothing the four-bet is taking the higher ones and",
        "folding the lower - a cut by height rather than by anything a bluff is chosen for. The",
        "bluffs come out of what blocks nothing the big blind continues with, and what does block",
        f"it goes in the calling range. All weights at {PURE_PCT:.0f} percent or better.",
        "",
        "The tension a reader is owed rather than left to find: the defects section defends the",
        "wheel-ace exemption on blocker logic - `nut-straight potential plus an ace blocker, and",
        "picking A5s over A6s for that job is what a strong player does at a three-bet` - and the",
        "four-bet family, which is most of this chart, selects its bluffs by the opposite rule.",
        "Both statements are in this packet and only one of them can be how the chart picks a",
        "bluff. What follows for a later phase: the four-bet frequency the second block hands",
        "forward is not on its own the number to start from, because a frequency says nothing",
        "about a range whose composition points this way.",
        "",
        "None of this is a re-solve and none of it moves a weight. It is the measurement the four",
        "internal relations cannot make - every one of them compares a grid against its own other",
        "cells, so a chart that is uniformly wrong reads clean on all four - and it is taken",
        "against a raked file, per hand, gating nothing",
        "(THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR).",
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


def vacuous_section(measured: Measured) -> list[str]:
    """Three criteria with no instance over the committed set, labelled wherever reported.

    The second of the three has two readings and only one of them is vacuous, so the split that
    tells them apart is printed here. Nothing in the label was wrong; what was missing is the
    two denominators, and a reader given the word without them reads a real 81-instance
    measurement as an empty one.
    """
    menus = spot_menus(measured.artifact)
    taken = spot_menus(measured.artifact, positive=True)
    named_a_raise = sum(1 for actions in menus.values() if actions & {"raise", "jam"})
    took_a_raise = sum(1 for actions in taken.values() if actions & {"raise", "jam"})
    priced = PreflopSizingTable.from_repo().raise_to_bb
    entries = {key: classes for key, classes in priced.items() if key in menus}
    with_a_price = sum(1 for classes in entries.values() if classes)
    raising = sum(1 for weight in measured.raises.values() if weight > 0.0)
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
        "",
        "The middle one of the three is labelled under one reading of `offers hero a raise` and is",
        "measured under another, and the word alone does not say which, so all three readings are",
        "printed. `Offers` can mean the spot carries a sizing KEY at all, or that its cells NAME a",
        "raise, or that some arriving class actually TAKES one - and the three came apart when the",
        "arriving classes came apart from the menu:",
        "",
        f"  spots carrying a sizing key  {len(entries)} of {len(measured.raises)}"
        f"  carrying none  {len(measured.raises) - len(entries)}",
        f"  menus naming a raise for hero  {named_a_raise} of {len(menus)}"
        f"  naming none  {len(menus) - named_a_raise}",
        f"  spots where some arriving class takes a raise  {took_a_raise} of {len(taken)}",
        f"  sizing keys with at least one class priced  {with_a_price}"
        f"  with an empty price list  {len(entries) - with_a_price}",
        f"  spots whose arriving range raises at all  {raising} of {len(measured.raises)}",
        "",
        "The label belongs to the first two rows and to those only. The criterion is about a spot",
        "that carries NO KEY and therefore makes the strategy refuse, and no committed spot",
        "carries no key, so there is nothing here for that half of the rule to refuse. Under the",
        f"third reading it is not empty at all: {len(measured.raises) - took_a_raise} committed"
        " spots name a raise no arriving class ever takes, and they ship a key with an empty",
        "price list under it. A packet may print the word for this criterion only with those rows",
        "it, because the error a bare label makes here runs the opposite way round to the one the",
        "paragraph above warns about - it tells a reader that a real measurement is empty rather",
        "than that an empty one passed.",
        "",
        "The same rows say that a SPOT-level reading of `exactly the spots that raise carry a",
        f"sizing entry` is now FALSE rather than vacant: every spot carries an entry and only"
        f" {with_a_price} raise, so the rule holds class by class and not spot by spot. That is a",
        "gap in what is asserted rather than a figure in dispute",
        "(COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY).",
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
        "The denominators of the two are not the same number and are not meant to be, which is",
        "said here because two figures a couple of decisions apart printed four lines from each",
        "other read as one of them being wrong. Every decision that yields a draw was scored, and",
        "not every decision that was scored yields a draw: where the chart's committed four-bet",
        "price sits below the table's own minimum raise at the price the hand was really played,",
        "the strategy refuses to render it rather than inventing a size, so the decision is scored",
        "for agreement and produces nothing to draw. Counting those as misses would blame the",
        "seeded draw for a chart fidelity problem.",
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
        "The refusal rate FALLS on both populations and the scored sample grows, which is the",
        "cutover buying coverage: the retired chart answered 36 priced spots and this one answers",
        "249. That is what the rows above read, and it is stated here rather than inferred from",
        "the ruling. The committed predicate still refuses everything from the four-bet on, every",
        "pot multiway more than one time in ten and the big blind's squeeze spots, and those",
        "refusals are the ruled cost - they are simply a smaller cost than the coverage hole they",
        "replaced. Corrected 2026-09-05: this passage read `the refusal rate rises ... an",
        "agreement rate over a smaller sample is the shape to expect`, which was written when the",
        "committed set was 36 spots and is false of the set this phase ships, on both counts and",
        "on both populations.",
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
        raises=spot_frequencies(artifact, "raise"),
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
            vacuous_section(measured),
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
