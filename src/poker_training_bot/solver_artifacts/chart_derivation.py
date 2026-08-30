"""Which solved nodes become committed spots, and what each one becomes.

The export holds 38,828 action nodes and the chart holds 86 of them. Choosing that subset
was the central decision of the cutover, so the rule lives here as a predicate over the
tree rather than as a list of keys somebody wrote down: a list cannot be re-derived, and a
later phase that fixes the source has nothing to re-run.

**Keep a node when at most one opponent has voluntarily invested beyond the blinds and at
most two players are still live.** Both clauses, conjoined. Neither is the rule on its own,
and the counts are what tell them apart: the history clause alone keeps 110 and the subtree
clause alone keeps 5,472. The history clause is about what has happened, and it is not
enough, because GTOpen prices a multiway pot as the product of hero's pairwise equities and
the approximation bites at *terminals* - a node's strategy is backward-induced over every
terminal below it, so heads-up-ness has to be asserted over the reachable subtree too. The
subtree clause is not enough either: 5,386 nodes are heads-up from here on and were reached
through a cold call, so they arrive carrying a range the same defect produced.

Every node the predicate declines is filed under one of two reasons rather than one, and
the precedence is the point. A node with a multiway terminal still reachable takes
`derivation:source-misprices-multiway`, which is the bucket a later phase reads to find the
spots that come back when GTOpen can price multiway; what is left takes
`derivation:outside-selection-rule`. So the 24 nodes that are heads-up by history and still
excluded sit inside the mispricing bucket, because that is *why* they are outside the rule.

An action kind this module has no rule for is neither excluded nor inexpressible: both
clauses count what a seat did, so neither can be evaluated at a node whose kinds cannot be
classified. It raises, naming the kind. Filing it as a property of the spot grammar would
turn a converter bug into a documented limitation.

Blinds are posted rather than chosen and never appear in the tree, so "voluntarily
invested" is exactly "took a call, a raise or a jam". An opener who later folds to a
three-bet still counts, which is the strict reading the predicate-change review settled.
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
from poker_training_bot.solver_artifacts.gtopen_export import (
    QUANTISATION_SCALE,
    SolverAction,
    SolverExport,
    SolverNode,
    gtopen_class_index,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, hand_class_grid_index
from poker_training_bot.solver_artifacts.lookup import (
    DERIVATION_OUTSIDE_SELECTION_RULE,
    DERIVATION_SOURCE_MISPRICES_MULTIWAY,
)
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

__all__ = [
    "ARTIFACT_NOTES",
    "DerivedChart",
    "NodeCensus",
    "census",
    "derive_chart",
    "exclusion_code",
    "invested_opponents",
    "is_committed_node",
    "live_players",
    "node_action_sequence",
    "node_arrival_ppb",
    "node_reach_bp",
    "node_spot_key",
]

TABLE_SIZE = 6
STACK_DEPTH_BB = 100
SEATS = table_positions(TABLE_SIZE)
ORDERED_CLASSES = tuple(sorted(HAND_CLASSES, key=hand_class_grid_index))

PARTS_PER_BILLION = 1_000_000_000
"""Arrival is stored in parts per billion, not basis points. 21 of the 86 spots sit at a
nonzero arrival below one basis point, the smallest at 2.5e-08, so in basis points they
would all round to zero and become indistinguishable from the eight spots the solve never
reaches - which is the one distinction the field exists to carry."""

SIZING_SCHEMA_VERSION = 2

_VOLUNTARY_KINDS = frozenset({"call", "raise", "jam"})
_AGGRESSIVE_KINDS = frozenset({"raise", "jam"})
_KNOWN_KINDS = frozenset({"fold"}) | _VOLUNTARY_KINDS


def _require_known_kind(node: SolverNode, action: SolverAction) -> str:
    """The kind of one offered action, or a refusal naming what could not be classified.

    Not an exclusion and not an inexpressibility. Both halves of the predicate count what
    a seat did, so neither can be evaluated here at all, and filing the node under
    `derivation:no-legal-spot-key` would record a converter that met something new as a
    property of the spot grammar.
    """
    if action.kind not in _KNOWN_KINDS:
        raise ValueError(
            f"node {node.path} offers the action kind {action.kind!r}, which this"
            " derivation has no rule for; the selection predicate counts what each seat"
            " did, so it cannot be evaluated here, and the node is refused rather than"
            " filed under a reason from the closed vocabulary"
        )
    return action.kind


def _validate_action_kinds(node: SolverNode) -> None:
    for action in node.actions:
        _require_known_kind(node, action)


def node_action_sequence(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> tuple[PreflopAction, ...]:
    """What hero faces at a node: the live actions in front of it, in order.

    The actor of a recorded action is whoever was to act at the node the action was taken
    at, which is the *parent* of the node it leads to. Reading it off the child shifts
    every entry one seat down the ring - the lojack's open becomes the hijack's - and the
    result keys a spot that never happened while validating perfectly.

    Folds never enter a sequence. An empty sequence means the pot was folded to hero, so a
    recorded fold would be a second spelling of the same spot and the two would key apart.
    """
    entries: list[PreflopAction] = []
    for depth, index in enumerate(node.path):
        parent = by_path[node.path[:depth]]
        action = parent.actions[index]
        kind = _require_known_kind(parent, action)
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


def invested_opponents(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> int:
    """How many seats other than hero have voluntarily put money in beyond the blinds.

    Counted as distinct seats rather than as actions, because a seat that opened and then
    called a three-bet is one opponent with money in, not two. A seat that opened and later
    folded still counts: the range it opened is what the terminals below were priced
    against, and whether it survived to the showdown does not change that.
    """
    invested: set[str] = set()
    for depth, index in enumerate(node.path):
        parent = by_path[node.path[:depth]]
        if _require_known_kind(parent, parent.actions[index]) in _VOLUNTARY_KINDS:
            invested.add(parent.actor_pos)
    return len(invested - {node.actor_pos})


def live_players(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> int:
    """How many seats can still be in the hand: the table less the ones that have folded.

    This is the clause the history reading was missing. It is a statement about the
    reachable subtree rather than about the action so far, which is what it has to be: with
    three seats live, a pot with three players in it is still reachable below the node, and
    every terminal down there is one the source cannot price.
    """
    folded: set[str] = set()
    for depth, index in enumerate(node.path):
        parent = by_path[node.path[:depth]]
        if _require_known_kind(parent, parent.actions[index]) == "fold":
            folded.add(parent.actor_pos)
    return len(SEATS) - len(folded)


def is_committed_node(by_path: dict[tuple[int, ...], SolverNode], node: SolverNode) -> bool:
    """The ruled predicate, and it needs no threshold constant.

    Decision 1's 2-percent reach floor was retired rather than retuned, and this is why
    there is no floor here to conjoin: all 86 clear it, so adding it back would select
    nothing new and would tell a reader a selection rule that is not the one in force.
    """
    return invested_opponents(by_path, node) <= 1 and live_players(by_path, node) <= 2


def exclusion_code(
    by_path: dict[tuple[int, ...], SolverNode], node: SolverNode
) -> str | None:
    """Why a node is not committed, or None when it is.

    The precedence is load-bearing. A node failing the subtree clause takes the mispricing
    code, so that bucket is exactly the complement of the subtree clause and holds the 24
    the 2026-08-25 supersession dropped - which is how a later phase finds them by name
    when GTOpen can price multiway. One code for both reasons would lose that.
    """
    if live_players(by_path, node) > 2:
        return DERIVATION_SOURCE_MISPRICES_MULTIWAY
    if invested_opponents(by_path, node) > 1:
        return DERIVATION_OUTSIDE_SELECTION_RULE
    return None


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

    Accumulated as a left-to-right float product and rounded once at the end. Three of the
    86 land within a thousandth of a rounding boundary, so accumulating in `Decimal` or in
    integers per node differs by one at those three and is not an improvement.
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

    A reason with no nodes under it carries no entry. The inexpressible bucket publishes
    empty over the committed export, which is a measurement rather than an omission: all
    38,828 nodes derive a valid spot key and no two collide.
    """

    committed: int
    excluded: dict[str, int]
    inexpressible: dict[str, int]

    @property
    def total(self) -> int:
        return self.committed + sum(self.excluded.values()) + sum(self.inexpressible.values())


def census(export: SolverExport) -> NodeCensus:
    """Walk the whole export and account for every node."""
    by_path = export.by_path()
    committed = 0
    excluded: dict[str, int] = {}
    for node in export.nodes:
        _validate_action_kinds(node)
        if is_committed_node(by_path, node):
            committed += 1
            continue
        code = exclusion_code(by_path, node)
        excluded[code] = excluded.get(code, 0) + 1
    return NodeCensus(committed=committed, excluded=excluded, inexpressible={})


def _cell_weights(node: SolverNode, hand_class_text: str) -> tuple[tuple[str, float], ...]:
    """One cell as the artifact records it: what hero does, not at what price.

    `PREFLOP_ACTIONS` holds one raise, so a named raise and a jam cannot both survive and
    their weights add. Dropping the jam would leave a row that does not sum to one and a
    big blind folding aces to a button open; the prices themselves are not lost, they go
    to the sizing table, which is where the strategy reads them.

    A row carries every action the collapsed menu offers, including the ones this class
    never takes. A zero is a reading rather than a gap - the solve never calls a button
    open with aces here, and dropping the entry would make that indistinguishable from a
    spot where calling was never on offer, which is the distinction a reader of the chart
    needs. The strategy's collapse already treats a zero as an action it does not draw.
    """
    basis_points: dict[str, int] = {}
    for index, action in enumerate(node.actions):
        kind = _require_known_kind(node, action)
        recorded = "raise" if kind in _AGGRESSIVE_KINDS else kind
        basis_points[recorded] = basis_points.get(recorded, 0) + node.weight_bp(
            index, hand_class_text
        )
    return tuple(
        (name, round(basis_points[name] / QUANTISATION_SCALE, 4))
        for name in PREFLOP_ACTIONS
        if name in basis_points
    )


def _committed_cells(node: SolverNode) -> tuple[HandClassWeights, dict[str, int]]:
    """The cells one committed spot answers, with the reach that put them there.

    A cell is committed when its class arrives. That is the whole refusal rule: Taylor
    ruled on 2026-08-27 that the chart commits the cells the solve never worked out, on
    the ground that a later heuristic layer is wanted for exactly those spots, and refuses
    only classes that never arrive. So there is no reach threshold here, no uniform-row
    epsilon and no arrival cutoff - a class hero cannot be holding is refused, and nothing
    else is.

    A GTOpen payload is unconditional: a hand hero folded three actions ago still carries
    a full strategy row, and 3,781 of those rows are the solver's untouched initialisation.
    `reach_bp` is the only thing that says which classes hero can actually hold, which is
    why the same index expression is read twice here rather than once into a local - the
    guard and the recorded value have to be the same reading of the same row.
    """
    cells: list[tuple[str, tuple[tuple[str, float], ...]]] = []
    reach_by_class: dict[str, int] = {}
    for hand_class_text in ORDERED_CLASSES:
        if node.reach_bp[gtopen_class_index(hand_class_text)] <= 0:
            continue
        reach_by_class[hand_class_text] = node.reach_bp[gtopen_class_index(hand_class_text)]
        cells.append((hand_class_text, _cell_weights(node, hand_class_text)))
    return tuple(cells), reach_by_class


def _spot_prices(node: SolverNode) -> dict[str, list[dict[str, float]]]:
    """Every price a spot offers hero, per hand class, with his weight on each.

    Decision 6 at the per-class shape ruled on 2026-08-26. A weight is a share of that
    class's own aggressive volume, so folds and calls do not dilute it and the entries sum
    to one; the per-spot aggregate the ruling rejected averages away the two ends of the
    range, and the ends are the poker - the solve three-bets small with the hands that want
    action and shoves the ones that do not want to play a three-bet pot out of position.

    Prices come off the node's own offers, so a jam is hero's whole stack because that is
    the price the solve wrote and not because a constant here says so. Weights are left
    unrounded: the smallest in the committed table is one basis point, held by cells that
    open-shove at the small blind's open, and rounding further would turn a class the
    strategy has to draw at into one it can price outright.
    """
    offers: list[tuple[int, float]] = []
    for index, action in enumerate(node.actions):
        if action.kind in ("raise", "jam"):
            offers.append((index, float(action.to)))
    if not offers:
        return {}
    priced: dict[str, list[dict[str, float]]] = {}
    for hand_class_text in ORDERED_CLASSES:
        column = gtopen_class_index(hand_class_text)
        if node.reach_bp[column] <= 0:
            continue
        volumes = sorted((to, node.strategy_bp[index][column]) for index, to in offers)
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
        cells, reach_by_class = _committed_cells(node)
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
        spot_prices = _spot_prices(node)
        if spot_prices:
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
