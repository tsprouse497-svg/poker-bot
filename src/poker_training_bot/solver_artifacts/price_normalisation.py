"""The one abstraction the chart lookup is allowed, and it exists because a human ruled it.

Ruling 8 of `docs/V2_ROADMAP.md` says the solved tree carries one opening price and every
other price is answered from it. Taylor extended it on 2026-08-20 to every raise in the
sequence, because a three-bet also arrives at sizes the tree does not hold, and exact
matching there would refuse 72 of the 79 three-bet decisions the committed chart can
answer at all - collapsing the raised-pot half of every later measurement the same way
the ruling was written to stop the opened-pot half collapsing.

It lives in its own module because the boundary matters more than the code. Normalising
a price is not finding a nearest spot: a nearer position, a nearer depth, a nearer hand
class, or a nearer action sequence is the heuristic guessing this repo's boundaries
forbid permanently. Keeping the ruled abstraction in one named place is what makes the
absence of the others checkable by reading rather than by trust.

Two properties keep it revisitable. The candidate prices come from the keys the loaded
artifacts declare, never from a constant, so committing a chart that opens to a second
size makes that size answerable with no edit here. And there is deliberately no distance
bound: ruling 8 is a single unbounded bucket, so the guard is measurement instead, and
every substitution is reported on the answer and counted in the phase 12 report.
"""

from __future__ import annotations

from collections.abc import Sequence

from poker_training_bot.solver_artifacts.schema import (
    PreflopAction,
    PreflopArtifact,
    SpotDefinition,
    render_entry,
)

# (sequence index, the price the query asked at, the price the chart answered at).
PriceSubstitutions = tuple[tuple[int, float, float], ...]

# Where in the tree a price sits: table, depth, hero, what came before it, who raises.
_PriceLocation = tuple[int, int, str, str, str]


def _price_location(
    table_size: int,
    stack_depth_bb: int,
    hero_position: str,
    prefix: Sequence[PreflopAction],
    position: str,
) -> _PriceLocation:
    """The address a candidate price is offered at.

    The prefix is rendered rather than counted, so a candidate is only offered for the
    exact line that reaches it. That is what keeps a three-bet's candidates from leaking
    across openers, and it is why normalising the open first and then the three-bet
    gives a different answer from normalising them independently.
    """
    return (
        table_size,
        stack_depth_bb,
        hero_position,
        ",".join(render_entry(entry) for entry in prefix),
        position,
    )


class SolvedPriceIndex:
    """Every raise price the loaded artifacts declare, indexed by where it sits.

    Built from the artifacts' own keys as the library loads them. Nothing in here is a
    price somebody typed: this artifact opens the small blind to 3.5 and every other
    position to 2.5, so a single constant would already be wrong today rather than only
    after some future solve.
    """

    def __init__(self) -> None:
        self._prices: dict[_PriceLocation, set[float]] = {}

    def add(self, artifact: PreflopArtifact, spot: SpotDefinition) -> None:
        for index, entry in enumerate(spot.action_sequence):
            if entry.action != "raise" or entry.size_bb is None:
                continue
            location = _price_location(
                artifact.table_size,
                artifact.stack_depth_bb,
                spot.hero_position,
                spot.action_sequence[:index],
                entry.position,
            )
            self._prices.setdefault(location, set()).add(float(entry.size_bb))

    def prices_at(
        self,
        table_size: int,
        stack_depth_bb: int,
        hero_position: str,
        prefix: Sequence[PreflopAction],
        position: str,
    ) -> tuple[float, ...]:
        """Every price declared at one point in the tree, ascending."""
        location = _price_location(
            table_size, stack_depth_bb, hero_position, prefix, position
        )
        return tuple(sorted(self._prices.get(location, ())))

    def normalise(
        self,
        table_size: int,
        stack_depth_bb: int,
        hero_position: str,
        action_sequence: Sequence[PreflopAction],
    ) -> tuple[tuple[PreflopAction, ...], PriceSubstitutions]:
        """Move each raise to the nearest price the chart holds for that exact line.

        A raise at a point in the tree the chart says nothing about is left exactly as
        it was asked. Substituting there would be inventing a price, and the miss that
        follows is the honest answer.
        """
        normalised: list[PreflopAction] = []
        substitutions: list[tuple[int, float, float]] = []
        for index, entry in enumerate(action_sequence):
            if entry.action != "raise" or entry.size_bb is None:
                normalised.append(entry)
                continue
            candidates = self.prices_at(
                table_size, stack_depth_bb, hero_position, normalised, entry.position
            )
            asked = float(entry.size_bb)
            if not candidates or asked in candidates:
                normalised.append(entry)
                continue
            # Ties break to the smaller price, so the choice is a property of the
            # committed keys rather than of set iteration order.
            answered = min(candidates, key=lambda size: (abs(size - asked), size))
            normalised.append(PreflopAction(entry.position, "raise", answered))
            substitutions.append((index, asked, answered))
        return tuple(normalised), tuple(substitutions)
