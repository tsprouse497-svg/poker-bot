"""Phase 14: the four relations over the committed ranges, and the machinery both arms run on.

**This file owns the measurement of the ranges** and every number in it, the two arms and the
ten partitions included. `test_chart_counterfactual_arms.py` runs those arms and holds the scoring
functions alone, split out at the 700-line cap and reaching every constant here rather than
restating one; `test_chart_derivation.py` owns which nodes are committed and this file imports its
`selected`.

**None of the four relations is gated as an order.** Decisions 41, 47, 50 and 51 accept the pair,
kicker and raise-action inversions as solved: among hands the solve prices alike the split is the
solver's considered answer, and gating an ordering rejects correct play. Gated is that the
measurement was *taken*, over every cell, with counts and worst cases published, and that its
definition is pinned as data first - `DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`,
seven counts having come out of seven readings of the same prose. The kicker family separates the
wheel-ace cases, which are correct poker, and nothing here calls either half noise.

Every count is recomputed by a walk written here rather than imported from the rule under test.
`scripts/generate_derived_chart_report.py` is reached as a module, so a name stage 6 has yet to
add is one `AttributeError` here rather than a collection error in every file.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import test_chart_derivation as derivation
import test_derived_chart_report as report_tests
import yaml

import scripts.generate_derived_chart_report as report
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    class_combos,
    gtopen_class_index,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, HIGH_TO_LOW_RANKS
from scripts.repo_paths import REPO_ROOT

# --- The four relations, pinned as data before anything is measured ------------------------ #

TOLERANCE_PCT = 1.0
"""Decision 10, ruled 2026-08-24 and never reopened: adjacent ranks, one point, every relation. It
catches the real 44-versus-33 pair at 27 points and ignores two cells a solver plays almost always
sitting 0.08 apart. Re-deriving it from the chart it judges was blocked on 2026-08-31."""

REACH_FLOOR_BP = 0
"""No reach floor selects cells. A cell is present when the class arrives at all, which is the
converter's own rule - it drops zero-reach classes - and reach is otherwise only a weighting."""

FULL_GRID_CELLS = 169
ROW_COMPARISONS_PER_FULL_GRID = 132
"""Adjacent kickers only, suited and offsuit apart: for each high card, one comparison between
each neighbouring pair of lower kickers, twice over. 2 x (11 + 10 + ... + 0) = 132."""

RANK_ARM_SPOT_FLOOR = 5
"""A partition scoring fewer than five spots publishes and does not assert, a strict gate over one
or two grids being a coin flip. Over the committed 249 none falls below it - the smallest, `raises
faced 0`, scores exactly five - so it is a rule kept against a set that moves."""

SPOTS_FOLDING_EVERY_HAND = 13
"""Committed spots whose play-not-fold grid reads zero at every arriving class: eleven small
blind, one cutoff, one button, all deep multiway spots facing a three-bet where one to five
classes arrive and the solve folds all of them. No over-folding can move such a grid, which is why
`test_chart_counterfactual_arms.py` counts the spots its fixture moved rather than all 249."""

SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")
NON_BLIND_OPENERS = ("LJ", "HJ", "CO", "BTN")


@dataclass(frozen=True)
class Relation:
    """One relation's whole definition, as data rather than as prose. The shared fields carry
    defaults so that a relation departing from them has to say so on its own line."""

    name: str
    measure: str
    comparisons_per_full_grid: int
    excluded_families: tuple[str, ...] = ()
    tolerance_pct: float = TOLERANCE_PCT
    reach_floor_bp: int = REACH_FLOOR_BP
    scope: str = "per cell, every committed spot, never pooled across spots"
    gated_as_an_order: bool = False


RELATIONS = (
    Relation("pair ladder", "play-not-fold", 12),
    Relation("suited over its offsuit twin", "play-not-fold", 78),
    Relation(
        "row kicker ladder",
        "play-not-fold",
        ROW_COMPARISONS_PER_FULL_GRID,
        ("suited and offsuit are never compared to each other here",),
    ),
    Relation(
        "pair ladder on the raise weight",
        "raise-weight",
        12,
        ("hero's jam, which lives only at the excluded four-bet spots",),
        scope="per cell, every committed spot, the merged raise weight the bot plays",
    ),
)
"""Decision 50 added the fourth, and it is the reason this phase halted: the pair inversion
decision 31 named is invisible to play-not-fold, both hands being played 100 percent and only the
raise-versus-call split differing.

**The fourth is read on the raise weight the bot actually plays** - at the 20 merged spots the
solve's raise plus its cold call, everywhere else the solve's raise unchanged. Taylor ruled that
on 2026-09-03, superseding the pre-merge reading this file first pinned, because a relation
defined on an *action* has to be stated over the action the bot takes. Over those 20 spots the
pre-merge reading finds 11 inversions and the merged one 9: three of the eleven do not exist in
play, the merge filling each flat into the raise, and one the bot really commits was invisible
before it - `t6/d100/CO/HJ:raise@2.5` three-bets `66` at 66.23 against `77` at 49.21. Decision 55
carries the working, and decision 50's three named cases survive either reading."""

_RANKS = HIGH_TO_LOW_RANKS

ADJACENT_PAIRS = tuple(
    (f"{high}{high}", f"{low}{low}") for high, low in zip(_RANKS, _RANKS[1:], strict=False)
)
SUITED_OVER_OFFSUIT = tuple(
    (f"{high}{low}s", f"{high}{low}o")
    for index, high in enumerate(_RANKS)
    for low in _RANKS[index + 1 :]
)
ROW_KICKERS = tuple(
    (f"{high}{better}{suit}", f"{high}{worse}{suit}")
    for index, high in enumerate(_RANKS)
    for better, worse in zip(_RANKS[index + 1 :], _RANKS[index + 2 :], strict=False)
    for suit in ("s", "o")
)

COMPARISONS = {
    "pair ladder": ADJACENT_PAIRS,
    "suited over its offsuit twin": SUITED_OVER_OFFSUIT,
    "row kicker ladder": ROW_KICKERS,
    "pair ladder on the raise weight": ADJACENT_PAIRS,
}

WHEEL_ACE_KICKERS = ("A5", "A4", "A3", "A2")
"""Decision 47: a suited wheel ace makes the nut straight and is less dominated than a middling
suited ace, so the lojack opening `A5s` while folding `A6s` is correct poker. GTOpen's fit leaves
them unchained on purpose, and they are never recorded among the accepted defects."""

KICKER_LABELS = ("wheel-ace premium, correct poker", "no poker story, accepted as solved")
FORBIDDEN_LABELS = ("noise", "mixing noise", "coin flip", "arbitrary")
"""Decision 51: a pick among hands the solve prices alike is bluff selection, which is further
from noise rather than closer to it, and it ships unmeasured with nothing waiting on a value
gap. No label this file publishes may call the family noise."""

# --- The two arms, pinned as data ---------------------------------------------------------- #


@dataclass(frozen=True)
class Arm:
    """One counterfactual arm. Both are strict and a tie refuses on each."""

    name: str
    permutation: str
    parameter: str
    unit: str
    scored_over: str
    spot_floor: int | None


ARMS = (
    Arm("suit", "transpose_hand_index", "spots_violating_twins", "spots",
        "every committed spot", None),
    Arm("rank", "reverse_hand_ranks", "cells_violating_rows", "cells",
        "every committed spot, absent-partner comparisons skipped", RANK_ARM_SPOT_FLOOR),
)
"""Two arms rather than one, because the suit arm alone scores a chart with every rank reversed
exactly as it scores a correct one - `test_chart_counterfactual_arms.py` runs that. Each keeps its
own permutation, scoring unit and parameter name, so one arm's number can never be read through
the other's validator. `transpose_hand_index` and `spots_violating_twins` are already committed in
the report generator; `reverse_hand_ranks` and `cells_violating_rows` are stage 6's to add."""

RANK_REVERSAL = dict(zip(_RANKS, reversed(_RANKS), strict=True))
"""A<->2, K<->3, Q<->4, J<->5, T<->6, 9<->7, 8<->8. Its own inverse, and it preserves pair,
suited and offsuit, so it maps the 169 classes onto themselves."""


@dataclass(frozen=True)
class PartitionFigures:
    """What the arms read on one partition. Decision 53 as re-measured under decision 54's
    withdrawal of the closed-spot restriction, by two walks written independently of each other."""

    name: str
    spots: int
    suit_solved: int
    suit_counterfactual: int
    rank_scored_spots: int
    rank_solved: int
    rank_counterfactual: int
    rank_skipped: int
    rank_skipped_permuted: int


PARTITIONS = (
    PartitionFigures("the committed set", 249, 7, 167, 208, 181, 433, 19774, 20279),
    PartitionFigures("raises faced 0", 5, 0, 5, 5, 11, 61, 0, 0),
    PartitionFigures("raises faced 1", 25, 0, 25, 25, 21, 112, 0, 0),
    PartitionFigures("raises faced 2", 219, 7, 137, 178, 149, 260, 19774, 20279),
    PartitionFigures("hero=LJ", 32, 7, 32, 32, 75, 96, 3224, 3410),
    PartitionFigures("hero=HJ", 36, 0, 15, 36, 23, 59, 3972, 4102),
    PartitionFigures("hero=CO", 44, 0, 18, 32, 22, 72, 4777, 4876),
    PartitionFigures("hero=BTN", 47, 0, 28, 33, 14, 66, 4351, 4416),
    PartitionFigures("hero=SB", 52, 0, 36, 37, 17, 65, 3450, 3475),
    PartitionFigures("hero=BB", 38, 0, 38, 38, 30, 75, 0, 0),
)
"""All ten, and dropping one is forbidden - the whole set, one per raises faced, one per hero
seat. Every column sums by seat and by raises faced to the whole set's own figure, which is what
stops a partition being quietly re-cut.

**The rank arm now scores every spot in its partition**, skipping a comparison whose partner cell
is absent, so the two skipped columns say how much of a partition it could look at: `hero=LJ`
skips 3,224 of its 4,224 possible comparisons on the solved side and 3,410 on the permuted one.
The sides skip different comparisons, the reversal carrying a present cell onto a different row,
so one number for both would be the splice that produced the withdrawn "149 against 69". The
tightest margin is `hero=LJ`, 75 against 96, and no partition is near refusing."""

EQUITY_BACKLOG_ID = "GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE"
"""Decision 42: a correct chart fails the equity relation, so it is published, it gates nothing,
and this entry stays deferred. No test or packet here may claim it closed."""


# --- The walk, written here rather than imported, so this file is not one copy of a rule -- #


def load_committed_export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


def select_committed(export: SolverExport) -> tuple[SolverNode, ...]:
    """The committed set, from the lane that owns the selection rule rather than re-derived."""
    nodes = tuple(derivation.selected(export))
    assert len(nodes) == derivation.COMMITTED_NODES
    return nodes


def build_tree(export: SolverExport) -> tuple[dict, dict]:
    """Two facts only the path to the root carries: how many raises are in when hero acts, and
    which seat put the last one in. A plain function with a fixture over it, because a fixture
    does not cross a module import and `test_chart_counterfactual_arms.py` needs the same one."""
    by_path = {node.path: node for node in export.nodes}
    faced = {(): 0}
    raiser: dict[tuple[int, ...], str | None] = {(): None}
    for path in sorted(by_path, key=len):
        node = by_path[path]
        for index, action in enumerate(node.actions):
            if action.terminal:
                continue
            raised = action.kind in ("raise", "jam")
            faced[path + (index,)] = faced[path] + (1 if raised else 0)
            raiser[path + (index,)] = node.actor_pos if raised else raiser[path]
    return faced, raiser


@pytest.fixture(scope="module")
def export() -> SolverExport:
    return load_committed_export()


@pytest.fixture(scope="module")
def committed(export: SolverExport) -> tuple[SolverNode, ...]:
    return select_committed(export)


@pytest.fixture(scope="module")
def tree(export: SolverExport) -> tuple[dict, dict]:
    return build_tree(export)


def play_not_fold(node: SolverNode) -> dict[str, float]:
    """How often each arriving class puts money in, which is what three of the four relations are
    stated over. One number per cell rather than a distribution: a stronger hand raising where a
    weaker one calls is not an inversion, both continuing. Invariant to decision 45's merge."""
    return {name: 100.0 - folded for name, folded in _weight(node, ("fold",)).items()}


def _weight(node: SolverNode, kinds: tuple[str, ...]) -> dict[str, float]:
    indices = [i for i, action in enumerate(node.actions) if action.kind in kinds]
    return {
        name: 100.0
        * sum(node.strategy_bp[i][gtopen_class_index(name)] for i in indices)
        / QUANTISATION_SCALE
        for name in HAND_CLASSES
        if node.reach_bp[gtopen_class_index(name)] > REACH_FLOOR_BP
    }


def is_merged_spot(node: SolverNode, faced: dict) -> bool:
    """One of decision 45's twenty: hero faces an open and is not the big blind, so his cold call
    is folded into his raise and the published menu is raise or fold."""
    return faced[node.path] == 1 and node.actor_pos != "BB"


def raise_weight(node: SolverNode, faced: dict) -> dict[str, float]:
    """How often each arriving class **raises in the published chart**, which is where decision
    50's inversions live and where play-not-fold reads nothing, both hands being played 100
    percent. At the twenty merged spots that is the solve's raise plus its cold call, because that
    is the action the bot takes there; everywhere else the solve's raise is already what it plays.
    Taylor ruled the merged reading on 2026-09-03: the raw raise row reports three inversions the
    bot never commits and hides one it does."""
    raised = _weight(node, ("raise", "jam"))
    if not is_merged_spot(node, faced):
        return raised
    called = _weight(node, ("call",))
    return {name: value + called.get(name, 0.0) for name, value in raised.items()}


def inversions(cells: dict[str, float], pairs, tally: dict | None = None) -> list[tuple]:
    """Every comparison the grid plays the wrong way round, past the tolerance. A comparison is
    skipped when either class is absent, and `tally` counts what was looked at - without which a
    class-naming break compares nothing and reports a clean grid."""
    found = []
    for stronger, weaker in pairs:
        high, low = cells.get(stronger), cells.get(weaker)
        if high is None or low is None:
            continue
        if tally is not None:
            tally["compared"] = tally.get("compared", 0) + 1
        if low - high > TOLERANCE_PCT:
            found.append((stronger, weaker, high, low))
    return found


def transpose_hand_index(cells: dict[str, float]) -> dict[str, float]:
    """The suit arm's counterfactual: every suited hand reads its offsuit twin's row. Both the
    value and the cell's presence come from the swapped class - taking one without the other
    measures sparsity rather than the mapping, which decision 10 records as the classic error."""
    swapped = dict(cells)
    for suited, offsuit in SUITED_OVER_OFFSUIT:
        if suited in cells and offsuit in cells:
            swapped[suited], swapped[offsuit] = cells[offsuit], cells[suited]
    return swapped


def reverse_rank(name: str) -> str:
    """A class with both ranks reversed, re-ordered high card first. Its own inverse, and it
    preserves pair, suited and offsuit."""
    high, low = RANK_REVERSAL[name[0]], RANK_REVERSAL[name[1]]
    if _RANKS.index(low) < _RANKS.index(high):
        high, low = low, high
    return f"{high}{low}{name[2:]}"


def reverse_hand_ranks(cells: dict[str, float]) -> dict[str, float]:
    """The rank arm's counterfactual: every cell reads the class with its ranks reversed. Total
    only on a full grid, so on a sparse one it returns the image of the present classes under the
    map, and a comparison whose partner did not survive is skipped rather than scored on what did.
    It is its own inverse on a sparse grid too."""
    return {
        name: cells[reverse_rank(name)] for name in HAND_CLASSES if reverse_rank(name) in cells
    }


def is_closed_under_reversal(cells: dict[str, float]) -> bool:
    """A full grid, on which the reversal is total and nothing is skipped. It no longer selects
    what the rank arm scores - that restriction was withdrawn on 2026-09-03 - and what it names
    here is the coverage floor the four relations are held to."""
    return len(cells) == FULL_GRID_CELLS


def partitioned(nodes, faced: dict) -> dict[str, tuple[SolverNode, ...]]:
    """The ten partitions, built here so a dropped one is a missing key rather than a silence."""
    groups = {"the committed set": tuple(nodes)}
    for count in (0, 1, 2):
        groups[f"raises faced {count}"] = tuple(n for n in nodes if faced[n.path] == count)
    for seat in SEATS:
        groups[f"hero={seat}"] = tuple(n for n in nodes if n.actor_pos == seat)
    return groups


def combo_weighted_play(node: SolverNode) -> float:
    """One spot's play-not-fold frequency over hero's arriving range, combo-weighted."""
    cells, total, weighted = play_not_fold(node), 0.0, 0.0
    for name, value in cells.items():
        weight = class_combos(name) * node.reach_bp[gtopen_class_index(name)]
        total += weight
        weighted += weight * value
    return weighted / total if total else 0.0


# --- The four relations -------------------------------------------------------------------- #


def test_the_four_relations_are_pinned_as_data_before_they_are_measured() -> None:
    """`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`. The prose form of this rule
    produced seven counts over the same export, so what is frozen is the record above: weighting,
    reach floor, tolerance, family exclusions, scope, and the comparison list each relation runs.
    Three measure play-not-fold and the fourth the raise weight, which is the only reason decision
    50's inversions are visible. None is gated as an order, and that is a property of the data, so
    a later hand that flips one has to flip it here."""
    assert len(RELATIONS) == 4
    assert {relation.measure for relation in RELATIONS} == {"play-not-fold", "raise-weight"}
    assert sum(1 for r in RELATIONS if r.measure == "raise-weight") == 1
    assert {relation.name for relation in RELATIONS} == set(COMPARISONS)

    for relation in RELATIONS:
        assert relation.tolerance_pct == TOLERANCE_PCT == 1.0, relation
        assert relation.reach_floor_bp == REACH_FLOOR_BP == 0, relation
        assert relation.gated_as_an_order is False, relation
        assert relation.scope.startswith("per cell, every committed spot"), relation
        pairs = COMPARISONS[relation.name]
        assert len(pairs) == relation.comparisons_per_full_grid, relation
        assert len(set(pairs)) == len(pairs), relation

    assert len(ROW_KICKERS) == ROW_COMPARISONS_PER_FULL_GRID == 132
    assert all(stronger[2:] == weaker[2:] for stronger, weaker in ROW_KICKERS)
    assert all(stronger[0] == weaker[0] for stronger, weaker in ROW_KICKERS)
    assert all(
        _RANKS.index(weaker[1]) - _RANKS.index(stronger[1]) == 1 for stronger, weaker in ROW_KICKERS
    )


def test_the_relation_walk_fires_where_it_was_ruled_to_and_nowhere_else() -> None:
    """The helper shown working before any count is read off it, one that never fires satisfying
    the coverage assertion below and reporting a clean chart. Decision 10's own cases: the real
    44-versus-33 pair at 27 points is caught, the noise pair at 0.08 is not, an offsuit hand
    beating its suited twin is caught. Then decision 50's: two hands played 100 percent with their
    raise weights inverted reads clean on play-not-fold and fires on the raise weight."""
    real = {"44": 72.81, "33": 99.88}
    noise = {"44": 99.91, "33": 99.99}
    twin = {"T9s": 10.0, "T9o": 40.0}
    both_played = {"33": 100.0, "22": 100.0}
    raises = {"33": 1.8, "22": 70.2}
    tally: dict[str, int] = {}

    assert [row[:2] for row in inversions(real, ADJACENT_PAIRS)] == [("44", "33")]
    assert inversions(noise, ADJACENT_PAIRS) == []
    assert [row[:2] for row in inversions(twin, SUITED_OVER_OFFSUIT)] == [("T9s", "T9o")]
    assert inversions(both_played, ADJACENT_PAIRS) == []
    assert [row[:2] for row in inversions(raises, ADJACENT_PAIRS)] == [("33", "22")]

    inversions({}, ADJACENT_PAIRS, tally)
    assert tally == {}, "an empty grid must compare nothing rather than pass quietly"


def test_every_committed_cell_is_measured_by_all_four_relations(
    committed: tuple[SolverNode, ...], tree: tuple[dict, dict]
) -> None:
    """What is gated is that the measurement was taken over every cell, not its verdict. Every
    committed spot is walked by all four relations and a full grid contributes at least the
    comparison count its relation declares. Nothing asserts a count is zero - decisions 41, 47, 50
    and 51 accept these inversions as solved, and the chart the solve produced fails an order gate.

    **The fourth relation's two counts are asserted at decision 55's figures**, because the 27
    they replace was carried through four documents without ever being re-derived and reproduces
    under no reading anyone could construct. They come off the export by the walk in this file: 41
    pair inversions on the merged raise weight, 25 of them invisible to play-not-fold. A zero
    there means the relation stopped measuring or the defect left the set, and either is a halt."""
    faced, _ = tree
    counts = {relation.name: 0 for relation in RELATIONS}
    tallies: dict[str, dict] = {relation.name: {} for relation in RELATIONS}
    full_grids = invisible_to_play_not_fold = 0

    for node in committed:
        played, raised = play_not_fold(node), raise_weight(node, faced)
        full_grids += is_closed_under_reversal(played)
        for relation in RELATIONS:
            cells = raised if relation.measure == "raise-weight" else played
            found = inversions(cells, COMPARISONS[relation.name], tallies[relation.name])
            counts[relation.name] += len(found)
        for stronger, weaker, _, _ in inversions(raised, ADJACENT_PAIRS):
            if not inversions(played, ((stronger, weaker),)):
                invisible_to_play_not_fold += 1

    assert len(committed) == derivation.COMMITTED_NODES
    assert full_grids > 0, "no committed spot carries a full grid, so nothing was measured whole"
    for relation in RELATIONS:
        floor = full_grids * relation.comparisons_per_full_grid
        assert tallies[relation.name].get("compared", 0) >= floor, (relation.name, tallies)
        assert isinstance(counts[relation.name], int)
    assert counts["pair ladder on the raise weight"] == report_tests.RAISE_ACTION_INVERSIONS
    assert invisible_to_play_not_fold == report_tests.RAISE_ACTION_INVERSIONS_INVISIBLE > 0, (
        "the fourth relation no longer finds the inversions play-not-fold misses, which is the"
        " one thing decision 50 added it for"
    )


def test_the_fourth_relation_reads_the_raise_weight_the_bot_plays(
    export: SolverExport, committed: tuple[SolverNode, ...], tree: tuple[dict, dict]
) -> None:
    """Taylor's ruling of 2026-09-03, measured rather than described. At each of the twenty merged
    spots the relation reads the solve's raise plus its cold call, which is what the bot commits
    there: the pre-merge reading finds 11 pair inversions over those spots and the merged one 9,
    three of the eleven being resolved by the merge and one the bot really does commit - `66`
    three-bet more often than `77` at `t6/d100/CO/HJ:raise@2.5` - appearing only after it.

    Decision 50's three named cases survive the change and all three stay invisible to
    play-not-fold, which is the whole reason the relation exists. None of the three merges, so
    they were never what the reading turned on; the twenty that do merge were."""
    faced, _ = tree
    keyed = {derivation.key_of(derivation.walk_of(export), node): node for node in committed}
    merged = [node for node in committed if is_merged_spot(node, faced)]
    raw = {node.path: _weight(node, ("raise", "jam")) for node in merged}
    before = sum(len(inversions(cells, ADJACENT_PAIRS)) for cells in raw.values())
    after = sum(len(inversions(raise_weight(node, faced), ADJACENT_PAIRS)) for node in merged)

    assert len(merged) == report_tests.MERGED_SPOTS == 20
    for node in merged:
        called = _weight(node, ("call",))
        assert raise_weight(node, faced) == {n: v + called[n] for n, v in raw[node.path].items()}
    assert (before, after) == (11, 9), (before, after)

    gained = keyed["t6/d100/CO/HJ:raise@2.5"]
    assert inversions(raise_weight(gained, faced), (("77", "66"),))
    assert not inversions(raw[gained.path], (("77", "66"),))
    for key in ("t6/d100/BB/HJ:raise@2.5", "t6/d100/BB/CO:raise@2.5",
                "t6/d100/CO/CO:raise@2.5,BTN:raise@7.5"):
        played = play_not_fold(keyed[key])
        found = inversions(raise_weight(keyed[key], faced), ADJACENT_PAIRS)
        assert not is_merged_spot(keyed[key], faced), key
        assert found and all(not inversions(played, (row[:2],)) for row in found), key


def test_the_kicker_family_separates_the_wheel_aces_from_the_ones_with_no_poker_story(
    committed: tuple[SolverNode, ...],
) -> None:
    """Decision 47. A count of the whole family overstates the defect by nearly four and a count
    of the rest understates the family's size, so the two are measured apart and both published.
    A wheel-ace case is an ace row where the hand played more often is `A5`, `A4`, `A3` or `A2`:
    correct poker, the nut-straight ace being less dominated than a middling suited one, and not
    an accepted defect. The split is asserted disjoint and exhaustive rather than at a count, a
    split of the right size with the wrong members being the same arithmetic and a different
    chart, and both labels are checked against the forbidden ones - decision 51 ruled this bluff
    selection, so no label here may call it noise."""
    published: dict[str, list[tuple]] = {label: [] for label in KICKER_LABELS}

    for node in committed:
        for stronger, weaker, high, low in inversions(play_not_fold(node), ROW_KICKERS):
            row = (node.path, stronger, weaker, high, low)
            wheel = stronger[0] == "A" and weaker[:2] in WHEEL_ACE_KICKERS
            published[KICKER_LABELS[0 if wheel else 1]].append(row)

    wheel_ace, no_story = published[KICKER_LABELS[0]], published[KICKER_LABELS[1]]

    assert wheel_ace, "no wheel-ace case found, and that family is the one decision 47 exempts"
    assert no_story, "every case read as correct poker, which decision 47 measured false"
    assert len(wheel_ace) + len(no_story) == sum(
        len(inversions(play_not_fold(node), ROW_KICKERS)) for node in committed
    )
    assert all(row[1][0] == "A" and row[2][:2] in WHEEL_ACE_KICKERS for row in wheel_ace)
    assert not any(row[1][0] == "A" and row[2][:2] in WHEEL_ACE_KICKERS for row in no_story)
    assert not [label for label in KICKER_LABELS if label in FORBIDDEN_LABELS]
    assert not [word for word in FORBIDDEN_LABELS if any(word in t for t in KICKER_LABELS)]


def test_the_group_order_ladders_are_measured_on_every_partition_and_asserted_on_none(
    committed: tuple[SolverNode, ...], tree: tuple[dict, dict]
) -> None:
    """Published for a human, gating nothing, and that is a ruling rather than an omission. The
    family returned a different verdict on every committed set it has been run over - failed on
    the 5,626, passed on the 86, tied on the 21, saturated on the 6 - so it measures set
    composition rather than whether the hand index is right. Taylor ruled on 2026-08-26 that no
    group ORDER is gated, and it has crept back twice since. What survives is that the figures are
    taken, a published measurement nobody computes being a blank column, so every partition is
    measured and no comparison between the numbers appears below."""
    faced, _ = tree
    high_to_low = tuple(f"{rank}{rank}" for rank in _RANKS)
    ladders = {
        "pairs, 13 single ranks": tuple((pair,) for pair in high_to_low),
        "pairs, 4 bands": tuple(high_to_low[s : s + 3] for s in (0, 3, 6, 9)),
        "pairs, 3 bands": tuple(high_to_low[s : s + 4] for s in (0, 4, 8)),
        "pairs, 2 bands": (high_to_low[:6], high_to_low[6:]),
        "suited rows": tuple(
            tuple(f"{high}{low}s" for low in _RANKS[index + 1 :])
            for index, high in enumerate(_RANKS[:-1])
        ),
    }

    def band_pct(cells, node, group):
        total = weighted = 0.0
        for name in group:
            if name not in cells:
                continue
            weight = class_combos(name) * node.reach_bp[gtopen_class_index(name)]
            total += weight
            weighted += weight * cells[name]
        return weighted / total if total else None

    def flagged(nodes, groups) -> int:
        bad = 0
        for node in nodes:
            cells = play_not_fold(node)
            values = [band_pct(cells, node, group) for group in groups]
            values = [value for value in values if value is not None]
            bad += any(
                high < low - TOLERANCE_PCT
                for high, low in zip(values, values[1:], strict=False)
            )
        return bad

    groups = partitioned(committed, faced)
    published = {
        (name, label): flagged(nodes, ladders[label])
        for name, nodes in groups.items()
        for label in ladders
    }

    assert len(groups) == len(PARTITIONS) == 10
    assert len(published) == 10 * len(ladders)
    for (name, label), value in published.items():
        assert isinstance(value, int) and 0 <= value <= len(groups[name]), (name, label, value)
    assert any(published.values()), "every group ladder computed nothing anywhere"


# --- What is published and gates nothing --------------------------------------------------- #


def test_the_equity_relation_gates_nothing_and_its_backlog_entry_stays_open() -> None:
    """Decision 42. A correct chart fails the equity relation at any tolerance - `A9s` folded
    while `87s` and `76s` are played is a real solver pattern and good poker, a weak suited ace
    being dominated by the three-bettor's broadway aces where a suited connector keeps its
    playability. So it prints for a human on every committed spot and refuses nothing, and this is
    the check that it never quietly became a gate: the generator exposes no equity validator at
    all. `test_derived_chart_report.py` owns the printing; here is the negative half and the
    backlog status, nothing in this repo measuring whether a published range is good poker."""
    entries = yaml.safe_load((REPO_ROOT / "backlog.yml").read_text(encoding="utf-8"))
    rows = entries["items"] if isinstance(entries, dict) else entries
    matching = [row for row in rows if row.get("id") == EQUITY_BACKLOG_ID]
    validators = [name for name in dir(report) if name.startswith("validate_")]

    assert len(matching) == 1, EQUITY_BACKLOG_ID
    assert matching[0]["status"] == "deferred", matching[0]
    assert not [name for name in validators if "equity" in name], validators


def test_the_two_orderings_the_export_was_gated_on_survive_into_the_committed_set(
    committed: tuple[SolverNode, ...], tree: tuple[dict, dict]
) -> None:
    """Later position opens wider among the four non-blind seats, and the big blind defends more
    against whoever opens wider. Both are properties of the game, so they survive the selection or
    the selection broke them, and both are readable off the committed set now that it holds all
    five first-in spots and the big blind's answer to each. The defence half follows the opening
    frequencies wherever they land rather than a fixed seat order, so the widest-opening seat is
    never the one nothing covers. **An ordering is not a level**, and only the level catches a
    broken realization model: that is printed for a human and gated on nothing
    (`STATIC-REALIZATION-UNMEASURED-IN-SINGLE-RAISED-POTS`), the big blind's over-folding being
    decision 34's accepted defect rather than a failure of either ordering."""
    faced, raiser = tree
    opens = {n.actor_pos: combo_weighted_play(n) for n in committed if faced[n.path] == 0}
    defends = {
        raiser[n.path]: combo_weighted_play(n)
        for n in committed
        if n.actor_pos == "BB" and faced[n.path] == 1
    }
    compared = 0

    assert set(opens) == {"LJ", "HJ", "CO", "BTN", "SB"}, opens
    assert set(defends) == set(opens), defends
    for tighter, wider in zip(NON_BLIND_OPENERS, NON_BLIND_OPENERS[1:], strict=False):
        assert opens[wider] > opens[tighter], opens
    for wider in opens:
        for tighter in opens:
            if opens[wider] <= opens[tighter]:
                continue
            compared += 1
            assert defends[wider] > defends[tighter], (wider, tighter, opens, defends)
    assert compared >= len(opens), (opens, defends)
