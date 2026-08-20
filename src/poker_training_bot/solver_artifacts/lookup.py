"""Fail-closed preflop chart lookup.

A query is answered with a `ChartHit` carrying the artifact's own weights, or a
`ChartMiss` carrying a reason code. There is no default action, no nearest spot,
no nearest stack depth, no interpolation, and no partial credit: an uncovered
spot stays uncovered and says so.

The lookup never spells a spot key by hand. It rebuilds the key with
`schema.spot_key`, the same function the importer stamps artifacts with, so a
spot that imports is reachable from a query built out of real game state.

There is exactly one abstraction in here, and it exists because a human ruled it.
Ruling 8 of `docs/V2_ROADMAP.md` says the solved tree carries one opening price and
every other price is answered from it; Taylor extended it on 2026-08-20 to every
raise in the sequence, because three-bets arrive at sizes the tree does not hold
either and exact matching there would refuse 72 of the 79 three-bet decisions the
committed chart can answer at all. So an observed price is normalised to the nearest
price the loaded artifacts actually declare for that position after the same
already-normalised prefix, and the answer carries the substitution so nothing
downstream can mistake it for an exact one.

Normalising a price is not finding a nearest spot, and the difference is the whole
boundary. The candidate prices come from the keys the artifacts declare, never from a
constant, so committing a second chart makes a second price answerable with no edit
here. Everything else - a nearer position, a nearer depth, a nearer hand class, a
nearer action sequence - stays forbidden: a squeeze is expressible and uncovered, and
it refuses at every price.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts.hand_classes import (
    hand_class as canonical_hand_class,
)
from poker_training_bot.solver_artifacts.hand_classes import (
    is_hand_class,
)
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.price_normalisation import (
    PriceSubstitutions,
    SolvedPriceIndex,
)
from poker_training_bot.solver_artifacts.schema import (
    ActionWeights,
    PreflopAction,
    PreflopArtifact,
    render_entry,
    render_size_bb,
)
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key

MISS_NO_ARTIFACT_FOR_TABLE = "lookup:no-artifact-for-table-size"
MISS_NO_ARTIFACT_FOR_DEPTH = "lookup:no-artifact-for-stack-depth"
MISS_POSITION_NOT_AT_TABLE = "lookup:position-not-at-table"
MISS_UNREPRESENTABLE_SPOT = "lookup:unrepresentable-spot"
MISS_SPOT_NOT_COVERED = "lookup:spot-not-covered"
MISS_HAND_CLASS_NOT_COVERED = "lookup:hand-class-not-covered"

MISS_CODES: tuple[str, ...] = (
    MISS_NO_ARTIFACT_FOR_TABLE,
    MISS_NO_ARTIFACT_FOR_DEPTH,
    MISS_POSITION_NOT_AT_TABLE,
    MISS_UNREPRESENTABLE_SPOT,
    MISS_SPOT_NOT_COVERED,
    MISS_HAND_CLASS_NOT_COVERED,
)

LIBRARY_DUPLICATE_SPOT = "library:duplicate-spot"
LIBRARY_NO_ARTIFACTS = "library:no-artifacts"

LIBRARY_ERROR_CODES: tuple[str, ...] = (LIBRARY_DUPLICATE_SPOT, LIBRARY_NO_ARTIFACTS)


class ChartLibraryError(ValueError):
    """A chart library that cannot be built without guessing."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _validate_int(value: object, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer, got {value!r}")


@dataclass(frozen=True)
class ChartQuery:
    """A preflop chart question: table, depth, hero position, action, hand class.

    Validation here is deliberately light. A caller builds a query out of live
    game state, so an unknown table size or a position that does not exist at
    that table is a lookup miss it can log, not an exception it has to catch.
    Only genuine programming errors raise: a hand class outside the canonical
    169, or an action sequence holding something that is not a `PreflopAction`.
    """

    table_size: int
    stack_depth_bb: int
    hero_position: str
    action_sequence: tuple[PreflopAction, ...]
    hand_class: str

    def __post_init__(self) -> None:
        _validate_int(self.table_size, "table_size")
        _validate_int(self.stack_depth_bb, "stack_depth_bb")
        if not isinstance(self.hero_position, str) or not self.hero_position:
            raise ValueError(
                f"hero_position must be a non-empty string, got {self.hero_position!r}"
            )
        if not isinstance(self.action_sequence, tuple):
            raise ValueError(
                f"action_sequence must be a tuple, got {type(self.action_sequence).__name__}"
            )
        for entry in self.action_sequence:
            if not isinstance(entry, PreflopAction):
                raise ValueError(f"action_sequence entries must be PreflopAction, got {entry!r}")
        if not is_hand_class(self.hand_class):
            raise ValueError(f"unknown hand class: {self.hand_class!r}")

    @classmethod
    def from_hole_cards(
        cls,
        table_size: int,
        stack_depth_bb: int,
        hero_position: str,
        action_sequence: tuple[PreflopAction, ...],
        hole_cards: Sequence[str],
    ) -> ChartQuery:
        """Build a query from two hole cards such as `("As", "kd")`.

        Canonicalization is `hand_classes.hand_class`, so card order and suits
        beyond suitedness cannot change which spot is asked about.
        """
        return cls(
            table_size=table_size,
            stack_depth_bb=stack_depth_bb,
            hero_position=hero_position,
            action_sequence=action_sequence,
            hand_class=canonical_hand_class(hole_cards),
        )

    @property
    def spot_key(self) -> str | None:
        """The derived spot key at the query's own prices, or None if there is none.

        None is not an error. It means no legal preflop situation produces this
        sequence at all - a seat acting out of turn, a re-raise that is not an
        increase, a raise nobody at the stated depth can pay - and the lookup misses
        rather than guesses. A position acting more than once is no longer one of
        those cases, which is what closed `SECOND-ORBIT-PREFLOP-SPOTS`.
        """
        try:
            return derive_spot_key(
                self.table_size, self.stack_depth_bb, self.hero_position, self.action_sequence
            )
        except ValueError:
            return None


@dataclass(frozen=True)
class ChartHit:
    """A covered spot and hand class, carrying the artifact's own weights.

    `action_weights` is the artifact's tuple, unchanged and in the artifact's
    action order.
    """

    artifact_id: str
    spot_key: str
    hand_class: str
    action_weights: ActionWeights
    # Empty when every price in the query was one the chart holds. Non-empty is the
    # only thing that keeps a substituted answer and an exact one distinguishable
    # downstream, and it is what the phase 12 substitution census is computed from.
    price_substitutions: PriceSubstitutions = ()

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id is required")
        if not self.spot_key:
            raise ValueError("spot_key is required")
        if not self.hand_class:
            raise ValueError("hand_class is required")
        if not self.action_weights:
            raise ValueError("a hit must carry at least one action weight")

    def substitution_detail(self) -> tuple[tuple[str, str], ...]:
        """The substitutions as ordered name/value pairs, for a decision's detail.

        `price_substitution_2 = 6.25->8` reads as "the raise at sequence index 2 was
        asked at 6.25 big blinds and answered from the 8 cell".
        """
        return tuple(
            (
                f"price_substitution_{index}",
                f"{render_size_bb(asked)}->{render_size_bb(answered)}",
            )
            for index, asked, answered in self.price_substitutions
        )

    @property
    def best_action(self) -> str | None:
        """The action when exactly one carries positive weight, else None.

        A mixed hand class has no single action, and inventing one would be
        strategy this layer is not allowed to have. Ties are never broken.
        """
        positive = [action for action, weight in self.action_weights if weight > 0.0]
        if len(positive) == 1:
            return positive[0]
        return None


@dataclass(frozen=True)
class ChartMiss:
    """An uncovered query, carrying the most specific reason code that applies."""

    code: str
    detail: str
    # The key the lookup actually asked about, once it had one. A refusal that names a
    # key names a cell somebody can fill; a refusal that names the key the lookup did
    # *not* use would send them to fill the wrong one, which is why this is carried out
    # of the lookup rather than re-derived by the caller.
    spot_key: str | None = None
    price_substitutions: PriceSubstitutions = ()

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("miss code is required")
        if not self.detail:
            raise ValueError("miss detail is required")


def _combinations(hand_class_text: str) -> int:
    """How many of the 1326 starting hands a 169-class name stands for."""
    if len(hand_class_text) == 2:
        return 6
    return 4 if hand_class_text.endswith("s") else 12


def _artifact_sort_key(artifact: PreflopArtifact) -> tuple[str, str, str]:
    """Content-derived order, so library order never depends on input order.

    `artifact_id` alone is not enough: two charts can share a table size, stack
    depth, and source name while covering different spots, so the timestamp and
    the weights checksum break the tie by content rather than by arrival.
    """
    return (artifact.artifact_id, artifact.generated_at, artifact.audit_fields.weights_sha256)


class PreflopChartLibrary:
    """Every imported chart, indexed by derived spot key.

    Two artifacts declaring the same spot key is a genuine ambiguity, so the
    library refuses to build rather than pick one. Lookups are pure: nothing in
    an artifact is copied, mutated, or reordered on the way out.
    """

    def __init__(self, artifacts: Sequence[PreflopArtifact]) -> None:
        ordered = tuple(sorted(artifacts, key=_artifact_sort_key))
        if not ordered:
            raise ChartLibraryError(
                LIBRARY_NO_ARTIFACTS, "a chart library needs at least one imported artifact"
            )
        owner_by_spot: dict[str, PreflopArtifact] = {}
        depths_by_table: dict[int, set[int]] = {}
        solved_prices = SolvedPriceIndex()
        for artifact in ordered:
            depths_by_table.setdefault(artifact.table_size, set()).add(artifact.stack_depth_bb)
            for spot in artifact.spots:
                existing = owner_by_spot.get(spot.spot_id)
                if existing is not None:
                    raise ChartLibraryError(
                        LIBRARY_DUPLICATE_SPOT,
                        f"artifacts {existing.artifact_id!r} and {artifact.artifact_id!r}"
                        f" both declare spot {spot.spot_id!r}",
                    )
                owner_by_spot[spot.spot_id] = artifact
                solved_prices.add(artifact, spot)
        self._artifacts = ordered
        self._owner_by_spot = owner_by_spot
        self._depths_by_table = {
            table_size: frozenset(depths) for table_size, depths in depths_by_table.items()
        }
        self._solved_prices = solved_prices

    @classmethod
    def from_artifacts(cls, artifacts: Sequence[PreflopArtifact]) -> PreflopChartLibrary:
        """Build from already-imported artifacts."""
        return cls(artifacts)

    @classmethod
    def from_directory(cls, directory: Path | str) -> PreflopChartLibrary:
        """Import every `*.json` artifact under `directory` and build from them.

        Import failures surface as `ArtifactImportError`, so nothing partially
        loaded ever reaches the library.
        """
        return cls(import_preflop_artifacts(directory))

    @property
    def artifacts(self) -> tuple[PreflopArtifact, ...]:
        """Artifacts ordered by `artifact_id`, so reports are byte-comparable."""
        return self._artifacts

    def spot_keys(self) -> tuple[str, ...]:
        """Every covered spot key, sorted, independent of artifact input order."""
        return tuple(sorted(self._owner_by_spot))

    def hand_classes_for(self, spot_key_text: str) -> tuple[str, ...]:
        """Hand classes a spot covers, in the artifact's own fixed order.

        Empty for an uncovered spot rather than an error: callers here are
        enumerating coverage, and absence is the answer they are asking about.
        """
        artifact = self._owner_by_spot.get(spot_key_text)
        if artifact is None:
            return ()
        for spot_id, hand_classes in artifact.action_weights:
            if spot_id == spot_key_text:
                return tuple(hand_class_text for hand_class_text, _ in hand_classes)
        return ()

    def action_frequency_pct(self, spot_key_text: str, action: str) -> float:
        """Combo-weighted percentage of hero's range taking `action` at a spot.

        Weighted by combinations, not by hand classes, because 169 classes are not
        equally likely: a pair is six combinations, a suited hand four, an offsuit
        hand twelve. Counting classes would overweight suited hands by three to one
        and put every published frequency out by several points.

        The percentage is of the spot's covered classes. For a spot where hero has
        already acted, the artifact covers only hero's own range, so this is a
        frequency within that range rather than within all 1326 combinations.
        """
        artifact = self._owner_by_spot.get(spot_key_text)
        if artifact is None:
            return 0.0
        total = 0.0
        chosen = 0.0
        for spot_id, hand_classes in artifact.action_weights:
            if spot_id != spot_key_text:
                continue
            for hand_class_text, weights in hand_classes:
                combos = _combinations(hand_class_text)
                total += combos
                for name, weight in weights:
                    if name == action:
                        chosen += weight * combos
        return 0.0 if total == 0.0 else 100.0 * chosen / total

    def solved_prices_bb(
        self,
        table_size: int,
        stack_depth_bb: int,
        hero_position: str,
        prefix: Sequence[PreflopAction],
        position: str,
    ) -> tuple[float, ...]:
        """Every raise price the loaded artifacts declare at one point in the tree.

        Read-only, and it is the whole of "where the set of solved prices comes from".
        Committing a chart that opens to a second size makes that size answerable with
        no edit to the normaliser.
        """
        return self._solved_prices.prices_at(
            table_size, stack_depth_bb, hero_position, prefix, position
        )

    def _substituted_key(
        self, query: ChartQuery, asked_key: str
    ) -> tuple[str, PriceSubstitutions]:
        """The key the lookup asks the artifacts about, and what moving cost.

        A normalised sequence can fail to be a legal spot even though the sequence as
        asked was one - move an open down to the solved price and a small three-bet
        behind it may stop being an increase. That is not a spot to guess at, so the
        query is answered at its own prices instead and misses honestly.
        """
        sequence, substitutions = self._solved_prices.normalise(
            query.table_size,
            query.stack_depth_bb,
            query.hero_position,
            query.action_sequence,
        )
        if not substitutions:
            return asked_key, ()
        try:
            return (
                derive_spot_key(
                    query.table_size,
                    query.stack_depth_bb,
                    query.hero_position,
                    sequence,
                ),
                substitutions,
            )
        except ValueError:
            return asked_key, ()

    def lookup(self, query: ChartQuery) -> ChartHit | ChartMiss:
        """Answer `query` with the artifact's weights or an explicit miss.

        Resolution walks from the coarsest gap to the finest, so the returned
        code names the first thing that is actually missing.
        """
        depths = self._depths_by_table.get(query.table_size)
        if depths is None:
            return ChartMiss(
                MISS_NO_ARTIFACT_FOR_TABLE,
                f"no artifact covers a {query.table_size}-handed table;"
                f" covered table sizes: {sorted(self._depths_by_table)}",
            )
        if query.stack_depth_bb not in depths:
            return ChartMiss(
                MISS_NO_ARTIFACT_FOR_DEPTH,
                f"no {query.table_size}-handed artifact covers {query.stack_depth_bb}bb;"
                f" covered depths: {sorted(depths)}",
            )
        positions = table_positions(query.table_size)
        if query.hero_position not in positions:
            return ChartMiss(
                MISS_POSITION_NOT_AT_TABLE,
                f"{query.hero_position!r} is not a {query.table_size}-handed position;"
                f" the table is {list(positions)}",
            )
        absent = [
            entry.position
            for entry in query.action_sequence
            if entry.position not in positions
        ]
        if absent:
            return ChartMiss(
                MISS_POSITION_NOT_AT_TABLE,
                f"the action sequence names {absent}, which are not"
                f" {query.table_size}-handed positions; the table is {list(positions)}",
            )
        asked_key = query.spot_key
        if asked_key is None:
            rendered = [render_entry(entry) for entry in query.action_sequence]
            return ChartMiss(
                MISS_UNREPRESENTABLE_SPOT,
                f"{query.hero_position} facing {rendered} has no spot key;"
                " no legal preflop order produces it",
            )
        spot_key_text, substitutions = self._substituted_key(query, asked_key)
        artifact = self._owner_by_spot.get(spot_key_text)
        if artifact is None:
            return ChartMiss(
                MISS_SPOT_NOT_COVERED,
                f"no artifact declares spot {spot_key_text!r}",
                spot_key=spot_key_text,
                price_substitutions=substitutions,
            )
        weights = artifact.weights_for(spot_key_text, query.hand_class)
        if weights is None:
            return ChartMiss(
                MISS_HAND_CLASS_NOT_COVERED,
                f"spot {spot_key_text!r} in artifact {artifact.artifact_id!r} declares no"
                f" weights for {query.hand_class}",
                spot_key=spot_key_text,
                price_substitutions=substitutions,
            )
        return ChartHit(
            artifact_id=artifact.artifact_id,
            spot_key=spot_key_text,
            hand_class=query.hand_class,
            action_weights=weights,
            price_substitutions=tuple(substitutions),
        )

    def lookup_hole_cards(
        self,
        table_size: int,
        stack_depth_bb: int,
        hero_position: str,
        action_sequence: tuple[PreflopAction, ...],
        hole_cards: Sequence[str],
    ) -> ChartHit | ChartMiss:
        """Canonicalize `hole_cards` into a hand class, then look the spot up."""
        return self.lookup(
            ChartQuery.from_hole_cards(
                table_size=table_size,
                stack_depth_bb=stack_depth_bb,
                hero_position=hero_position,
                action_sequence=action_sequence,
                hole_cards=hole_cards,
            )
        )
