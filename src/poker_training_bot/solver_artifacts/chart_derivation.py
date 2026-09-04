"""What a committed node becomes, and the census that accounts for the ones that are not.

The export holds 33,969 action nodes and the chart holds 249 of them. Which 249 is
`chart_selection.py`'s question, and every name it answers with is re-exported here, so a
caller reads one module and the split between the two stays a line-cap detail. This module
owns the other half: the spot key a node derives, the cells and prices it publishes, the
merge that turns hero's cold call into a raise, the arrival and reach it carries, and the
four-bucket census over the whole export.

Selection lives as a predicate over the tree rather than as a list of keys somebody wrote
down, because a list cannot be re-derived and a later phase that fixes the source would
have nothing to re-run. The census is the same measurement read from the other end: every
node is committed, or filed under the one clause that refused it, or inexpressible in the
spot vocabulary, and the three sum to the node count the source card publishes. That is
what stops a converter which quietly skipped a subtree from balancing its own books.

An action kind this module has no rule for is neither excluded nor inexpressible: every
selection clause counts what a seat did, so none can be evaluated at a node whose kinds
cannot be classified. It raises, naming the kind, because filing it as a property of the
spot grammar would turn a converter bug into a documented limitation of the chart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts.chart_provenance import (
    ARTIFACT_NOTES,
    EXPORT_REFERENCE,
    GENERATED_AT,
    SIZING_NOTES,
    SOURCE_NAME,
)
from poker_training_bot.solver_artifacts.chart_selection import (
    COMMITTED_RAISE_DEPTH,
    MULTIWAY_EXPOSURE_THRESHOLD_PCT,
    TABLE_SIZE,
    below_multiway_exposure_threshold,
    cold_call_index,
    exclusion_code,
    is_big_blind_squeeze_spot,
    is_committed_node,
    multiway_exposure_pct,
    raises_faced,
    require_known_kind,
    terminal_split_pct,
    within_committed_raise_depth,
)
from poker_training_bot.solver_artifacts.gtopen_export import (
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    gtopen_class_index,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, hand_class_grid_index
from poker_training_bot.solver_artifacts.schema import (
    ARTIFACT_SCHEMA_VERSION,
    PREFLOP_ACTIONS,
    ArtifactAuditFields,
    ArtifactSource,
    BlindStructure,
    HandClassWeights,
    PreflopAction,
    PreflopArtifact,
    SpotDefinition,
    spot_key,
    weights_checksum,
)

# The selection names are re-exported rather than re-implemented: `chart_selection.py` is a
# line-cap split, not a second module a caller has to know about, and a name that exists in
# both places is the way the two would come to disagree.
__all__ = [
    "ARTIFACT_NOTES",
    "COMMITTED_RAISE_DEPTH",
    "MULTIWAY_EXPOSURE_THRESHOLD_PCT",
    "DerivedChart",
    "NodeCensus",
    "below_multiway_exposure_threshold",
    "census",
    "cold_call_index",
    "derive_chart",
    "exclusion_code",
    "is_big_blind_squeeze_spot",
    "is_committed_node",
    "merged_cells",
    "merges_the_cold_call",
    "multiway_exposure_pct",
    "node_action_sequence",
    "node_arrival_ppb",
    "node_reach_bp",
    "node_spot_key",
    "raises_faced",
    "terminal_split_pct",
    "within_committed_raise_depth",
]

STACK_DEPTH_BB = 100
ORDERED_CLASSES = tuple(sorted(HAND_CLASSES, key=hand_class_grid_index))

PARTS_PER_BILLION = 1_000_000_000
"""Arrival is stored in parts per billion, not basis points. Over the committed 249 only 2
spots are never reached at all, while 44 round to zero even at this grain and far more sit
below one basis point, so in basis points the played-but-rare lines would be indistinguishable
from the two the solve never reaches - which is the one distinction the field exists to
carry."""

SIZING_SCHEMA_VERSION = 2

_AGGRESSIVE_KINDS = frozenset({"raise", "jam"})


def _validate_action_kinds(node: SolverNode) -> None:
    """Every kind at one node classified, or the first one that cannot be.

    The classifier is the selection's, so a kind no clause can score is the same kind the
    conversion refuses to record, and the two halves cannot disagree about what the source
    is allowed to contain.
    """
    for action in node.actions:
        require_known_kind(node, action)


def node_action_sequence(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> tuple[PreflopAction, ...]:
    """What hero faces at a node: the live actions in front of it, in order.

    The actor of a recorded action is whoever was to act at the node the action was taken
    at, which is the *parent* of the node it leads to. Reading it off the child shifts
    every entry one seat down the ring - the lojack's open becomes the hijack's - and the
    result keys a spot that never happened while validating perfectly. Folds never enter a
    sequence: an empty sequence means the pot was folded to hero, so a recorded fold would
    be a second spelling of the same spot and the two would key apart.
    """
    entries: list[PreflopAction] = []
    for depth, index in enumerate(node.path):
        parent = by_path[node.path[:depth]]
        action = parent.actions[index]
        kind = require_known_kind(parent, action)
        if kind == "fold":
            continue
        if kind == "call":
            entries.append(PreflopAction(parent.actor_pos, "call"))
            continue
        entries.append(PreflopAction(parent.actor_pos, "raise", float(action.to)))
    return tuple(entries)


def node_spot_key(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> str:
    """The spot key a node derives, in the one vocabulary this repo has for naming spots."""
    return spot_key(
        TABLE_SIZE, STACK_DEPTH_BB, node.actor_pos, node_action_sequence(by_path, node)
    )


def merges_the_cold_call(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> bool:
    """Whether this spot publishes hero's call as a raise, which is decision 45.

    The bot never cold-calls: money in behind an opener with nothing already invested buys
    a multiway pot out of position. So where hero faces an open and has posted nothing, the
    solve's call is merged into the raise - merged and not deleted, because at nine of
    these spots a hand's whole weight is on calling and deleting would leave a row of
    zeroes, a hand with no answer at all.

    The big blind is not one of these seats: it has paid a blind, so its call is a defence
    rather than a cold call. Nor is a seat that opened and now faces a three-bet. That is
    why this asks for one raise in front of hero and a seat other than the big blind, and
    never whether a call is on the menu.
    """
    return raises_faced(by_path, node) == 1 and node.actor_pos != "BB"


def _flat_bp(node: SolverNode, column: int) -> int:
    """One class's weight on calling at a node, in basis points."""
    return sum(
        node.strategy_bp[index][column]
        for index, action in enumerate(node.actions)
        if require_known_kind(node, action) == "call"
    )


def merged_cells(export: SolverExport) -> tuple[tuple[str, str], ...]:
    """Every cell decision 45 moves, as (spot key, hand class).

    A cell moves when hero can hold the class at a merging spot and the solve puts weight
    on calling there. The cells rather than a count, so a report can print which hands
    changed answer and the count is that walk's own rather than a second tally beside it.
    """
    by_path = export.by_path()
    moved: list[tuple[str, str]] = []
    for node in export.nodes:
        if not is_committed_node(by_path, node) or not merges_the_cold_call(by_path, node):
            continue
        key = node_spot_key(by_path, node)
        for hand_class_text in ORDERED_CLASSES:
            column = gtopen_class_index(hand_class_text)
            if node.reach_bp[column] > 0 and _flat_bp(node, column) > 0:
                moved.append((key, hand_class_text))
    return tuple(moved)


def node_reach_bp(node: SolverNode) -> float:
    """The share of hero's range that arrives at a node, in basis points.

    The plain mean over the 169 hand classes, not the combination-weighted one. They are
    different numbers for the same words, and this is the one decision 5 publishes per
    cell; a reader comparing the two readings would find them disagreeing by more than a
    basis point somewhere in the tree.
    """
    return sum(node.reach_bp) / 169.0


def node_arrival_ppb(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> int:
    """The chance a node's line is played at all, in parts per billion.

    The product of each parent's own frequency for the action taken, down the path from the
    root, so this multiplies figures GTOpen publishes rather than deriving a second
    definition of them. Orthogonal to reach: reach says whether hero can hold a class here,
    arrival says whether anybody plays the line, and a spot can have every class at full
    reach and never be reached at all.

    Accumulated as a left-to-right float product and rounded once at the end. Carrying
    parts per billion as an integer and rounding after every factor instead disagrees at
    31 of the committed 249, so it is a different answer rather than a better one, and the
    ruled reading is the one written here.
    """
    probability = 1.0
    walked: tuple[int, ...] = ()
    for index in node.path:
        probability *= by_path[walked].action_frequency(index)
        walked = (*walked, index)
    return round(probability * PARTS_PER_BILLION)


@dataclass(frozen=True)
class NodeCensus:
    """Every node in the export, in exactly one of three buckets.

    Committed, excluded with a reason, or inexpressible in the spot vocabulary. The three
    sum to the node count the source card publishes, which is what stops a converter that
    skipped a subtree balancing its own books. Both reason vocabularies are closed and
    `lookup.py` owns them, so a node the converter merely failed to handle cannot be filed
    as a property of the grammar - it raises instead.

    One reason per node and never two, so the excluded buckets are a partition rather than
    overlapping descriptions: a node beyond the raise depth that is also over the exposure
    threshold is counted once, under the depth, that being the first thing that would have
    to change for it to ship. A reason with no nodes under it carries no entry, and the
    inexpressible bucket publishes empty over the committed export - a measurement rather
    than an omission, all 33,969 nodes deriving a valid spot key and no two colliding.
    """

    committed: int
    excluded: dict[str, int]
    inexpressible: dict[str, int]

    @property
    def total(self) -> int:
        return self.committed + sum(self.excluded.values()) + sum(self.inexpressible.values())


def census(export: SolverExport) -> NodeCensus:
    """Walk the whole export and account for every node.

    Committed is read as "no code applies" rather than as a second call to the predicate, so
    the count of what shipped and the counts of what did not are the same reading of the
    same node and cannot balance while disagreeing.
    """
    by_path = export.by_path()
    committed = 0
    excluded: dict[str, int] = {}
    for node in export.nodes:
        _validate_action_kinds(node)
        code = exclusion_code(by_path, node)
        if code is None:
            committed += 1
            continue
        excluded[code] = excluded.get(code, 0) + 1
    return NodeCensus(committed=committed, excluded=excluded, inexpressible={})


def _cell_weights(
    node: SolverNode, hand_class_text: str, merged: bool
) -> tuple[tuple[str, float], ...]:
    """One cell as the artifact records it: what hero does, not at what price.

    `PREFLOP_ACTIONS` holds one raise, so a named raise and a jam cannot both survive and
    their weights add. Dropping the jam would leave a row that does not sum to one and a
    big blind folding aces to a button open; the prices themselves are not lost, they go
    to the sizing table, which is where the strategy reads them.

    At a merging spot the call joins them. Adding rather than renormalising is the point:
    hero folds exactly as often as the solve folds, and the hands it wanted to see a flop
    with are the hands he now raises with.

    A row carries every action the collapsed menu offers, including the ones this class
    never takes. A zero is a reading rather than a gap - the solve never calls a button
    open with aces here, and dropping the entry would make that indistinguishable from a
    spot where calling was never on offer, which is the distinction a reader of the chart
    needs. The strategy's collapse already treats a zero as an action it does not draw.
    """
    basis_points: dict[str, int] = {}
    for index, action in enumerate(node.actions):
        kind = require_known_kind(node, action)
        aggressive = kind in _AGGRESSIVE_KINDS or (merged and kind == "call")
        recorded = "raise" if aggressive else kind
        basis_points[recorded] = basis_points.get(recorded, 0) + node.weight_bp(
            index, hand_class_text
        )
    return tuple(
        (name, round(basis_points[name] / QUANTISATION_SCALE, 4))
        for name in PREFLOP_ACTIONS
        if name in basis_points
    )


def _committed_cells(node: SolverNode, merged: bool) -> tuple[HandClassWeights, dict[str, int]]:
    """The cells one committed spot answers, with the reach that put them there.

    A cell is committed when its class arrives. That is the whole refusal rule: Taylor
    ruled on 2026-08-27 that the chart commits the cells the solve never worked out, a
    later heuristic layer being wanted for exactly those, and refuses only classes that
    never arrive. So there is no reach threshold here, no uniform-row epsilon and no
    arrival cutoff - a class hero cannot be holding is refused, and nothing else is.

    A GTOpen payload is unconditional: a hand hero folded three actions ago still carries a
    full strategy row, and many such rows are the solver's untouched initialisation, an
    even split across the menu rather than a played frequency. `reach_bp` is the only thing
    that says which classes hero can hold, which is why the same index expression is read
    twice rather than once into a local - the guard and the recorded value have to be the
    same reading of the same row.
    """
    cells: list[tuple[str, tuple[tuple[str, float], ...]]] = []
    reach_by_class: dict[str, int] = {}
    for hand_class_text in ORDERED_CLASSES:
        if node.reach_bp[gtopen_class_index(hand_class_text)] <= 0:
            continue
        reach_by_class[hand_class_text] = node.reach_bp[gtopen_class_index(hand_class_text)]
        cells.append((hand_class_text, _cell_weights(node, hand_class_text, merged)))
    return tuple(cells), reach_by_class


def _spot_prices(node: SolverNode, merged: bool) -> dict[str, list[dict[str, float]]] | None:
    """Every price a spot offers hero, per hand class, with his weight on each.

    Decision 6 at the per-class shape ruled on 2026-08-26. A weight is a share of that
    class's own aggressive volume, so folds and calls do not dilute it and the entries sum
    to one; the per-spot aggregate the ruling rejected averages away the two ends of the
    range, and the ends are the poker - the solve three-bets small with the hands that want
    action and shoves the ones that do not want to play a three-bet pot out of position.
    Prices come off the node's own offers, so a jam is hero's whole stack because that is
    the price the solve wrote and not because a constant here says so, and weights are left
    unrounded, rounding turning a price a class takes rarely into one it never takes.

    At a merging spot the flat is priced too, or the chart says raise where it cannot say
    how much. It goes on the cheapest raise offered, the smallest raise being the nearest
    thing to the flat it replaces and never the shove, which is the opposite bet. Every
    committed spot offers one price, so here the choice is between that price and itself;
    it is written down because the multiway family returns with two-price menus.

    None means the spot offers hero no raise at all, which is not the same as offering one
    no class takes: the first carries no key here, so the strategy refuses when asked for a
    size rather than reading an empty map as a price it failed to find.
    """
    offers: list[tuple[int, float]] = []
    for index, action in enumerate(node.actions):
        if require_known_kind(node, action) in _AGGRESSIVE_KINDS:
            offers.append((index, float(action.to)))
    if not offers:
        return None
    priced: dict[str, list[dict[str, float]]] = {}
    for hand_class_text in ORDERED_CLASSES:
        column = gtopen_class_index(hand_class_text)
        if node.reach_bp[column] <= 0:
            continue
        volumes = sorted((to, node.strategy_bp[index][column]) for index, to in offers)
        if merged:
            cheapest, held = volumes[0]
            volumes[0] = (cheapest, held + _flat_bp(node, column))
        aggressive = sum(basis_points for _, basis_points in volumes)
        if aggressive <= 0:
            continue
        priced[hand_class_text] = [
            {"to_bb": to, "weight": basis_points / aggressive}
            for to, basis_points in volumes
            if basis_points > 0
        ]
    return priced


def _blind_structure(config: dict) -> BlindStructure:
    """The blinds the solve posted, read out of the export's own config.

    Read rather than declared, because a declared-but-wrong structure is worse than an
    absent one: the same hand at the same stack depth is a different decision at 1/3, and
    a field nothing checks against the posted config closes
    `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` in name only.
    """
    positions = list(config["positions"])
    posted = list(config["posts"])
    posts = [float(posted[positions.index(seat)]) for seat in ("SB", "BB")]
    return BlindStructure(
        small_blind_bb=float(posts[0]),
        big_blind_bb=float(posts[-1]),
        ante_bb=float(config["ante"]),
    )


@dataclass(frozen=True)
class DerivedChart:
    """One conversion of one export: the artifact, its sizing table, and the census."""

    artifact_payload: dict[str, Any]
    sizing_payload: dict[str, Any]
    census: NodeCensus


def derive_chart(export: SolverExport) -> DerivedChart:
    """Convert an export into the committed chart, its prices, and the walk that proves it.

    The artifact is built through `PreflopArtifact` rather than assembled as a dict, so
    every rule the schema enforces on an imported chart is enforced on this one before it
    reaches a file. A payload that would be refused on import is a payload nobody should
    be able to write.
    """
    by_path = export.by_path()
    counted = census(export)
    keyed = sorted(
        (
            (node_spot_key(by_path, node), node)
            for node in export.nodes
            if is_committed_node(by_path, node)
        ),
        key=lambda pair: pair[0],
    )

    spots: list[SpotDefinition] = []
    action_weights: list[tuple[str, HandClassWeights]] = []
    arriving_reach: list[tuple[str, tuple[tuple[str, int], ...]]] = []
    arrival_ppb: dict[str, int] = {}
    prices: dict[str, dict[str, list[dict[str, float]]]] = {}
    for key, node in keyed:
        merged = merges_the_cold_call(by_path, node)
        cells, reach_by_class = _committed_cells(node, merged)
        spots.append(
            SpotDefinition(
                spot_id=key,
                hero_position=node.actor_pos,
                action_sequence=node_action_sequence(by_path, node),
            )
        )
        action_weights.append((key, cells))
        arriving_reach.append((key, tuple(reach_by_class.items())))
        arrival_ppb[key] = node_arrival_ppb(by_path, node)
        spot_prices = _spot_prices(node, merged)
        if spot_prices is not None:
            prices[key] = spot_prices

    weights = tuple(action_weights)
    artifact = PreflopArtifact(
        artifact_schema_version=ARTIFACT_SCHEMA_VERSION,
        source=ArtifactSource(
            name=SOURCE_NAME, kind="solver-export", reference=EXPORT_REFERENCE
        ),
        generated_at=GENERATED_AT,
        table_size=TABLE_SIZE,
        stack_depth_bb=STACK_DEPTH_BB,
        positions=table_positions(TABLE_SIZE),
        blind_structure=_blind_structure(export.config),
        spots=tuple(spots),
        action_weights=weights,
        arriving_reach_bp=tuple(arriving_reach),
        audit_fields=ArtifactAuditFields(
            weights_sha256=weights_checksum(weights),
            spot_count=len(spots),
            hand_class_count=len({name for _, cells in weights for name, _ in cells}),
            notes=ARTIFACT_NOTES,
        ),
        arrival_ppb=tuple(arrival_ppb.items()),
    )
    sizing_payload = {
        "schema_version": SIZING_SCHEMA_VERSION,
        "source": {
            "name": SOURCE_NAME,
            "kind": "solver-export",
            "reference": EXPORT_REFERENCE,
        },
        "notes": SIZING_NOTES,
        "raise_to_bb": prices,
    }
    return DerivedChart(
        artifact_payload=artifact.to_payload(),
        sizing_payload=sizing_payload,
        census=counted,
    )
