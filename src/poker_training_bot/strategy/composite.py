"""One strategy object that plays a whole hand, by routing and nothing else.

Preflop belongs to the committed charts and flop through river belongs to the
continuity fallback. Both halves already exist; what was missing was a single place
that says which one owns a street, so that Phase 07 hands a hand to one object
instead of reassembling the routing at every call site and getting it subtly
different in each.

The design constraint is that this module adds no poker. Its outcome for any query is
the outcome its component would have returned, as the same object, which is why
`decide` returns what it received without touching the amount and without rewriting
the code. That is not tidiness: the code prefix is the whole attribution mechanism, so
an audit line reading `preflop-chart:` or `postflop-fallback:` is evidence about which
component answered, and a composite that restamped codes would destroy exactly the
evidence the audit exists to carry.

The consequence worth stating out loud is what happens to a preflop refusal. The chart
refuses whenever it is silent - an uncovered spot, a depth no artifact holds, a
straddled pot - and those refusals travel out through here unchanged. Handing them to
the fallback instead would produce a check, the simulation would never stop, and the
coverage gap Phases 04 and 05 were built to measure would vanish without a trace. That
is the heuristic guessing for a missing chart spot that `AGENTS.md` forbids by name: a
refusal that becomes a check is a guess with the evidence deleted. Phase 07 therefore
has to handle an outcome that is not a decision, which is more work there and the
correct place for it.
"""

from __future__ import annotations

from dataclasses import dataclass

from poker_training_bot.strategy.contract import (
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.postflop_fallback import PostflopFallbackStrategy
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy

# These names match each component's own `strategy_id` and code prefix, so a component
# label in a report and a code prefix in an audit line refer to the same thing rather
# than to two vocabularies a reader has to reconcile.
PREFLOP_COMPONENT = "preflop-chart"
POSTFLOP_COMPONENT = "postflop-fallback"


@dataclass(frozen=True)
class CompositeStrategy:
    """The chart preflop, the fallback afterwards, and no third opinion.

    Frozen and field-equal like both components, so two composites built from the same
    repo compare equal and answer identically. Nothing is cached here and no state
    crosses calls, which is what lets a decision audit line be replayed.
    """

    preflop: PreflopChartStrategy
    postflop: PostflopFallbackStrategy
    strategy_id: str = "composite-preflop-chart-postflop-fallback"
    strategy_version: int = 1

    @classmethod
    def from_repo(cls) -> CompositeStrategy:
        """Build from committed data, which is the chart library's job and not this one.

        The only I/O in the whole module happens inside `PreflopChartStrategy.from_repo`.
        The fallback reads nothing at all, because a deck enumeration needs no artifact.
        """
        return cls(
            preflop=PreflopChartStrategy.from_repo(),
            postflop=PostflopFallbackStrategy(),
        )

    def component_for(self, street: str) -> str:
        """Which component owns a street.

        Public and answerable without a query, because a report that breaks results out
        by component should ask this rather than re-derive the split from a street name
        and drift from it later.

        Everything that is not preflop is postflop, rather than a membership test
        against the three postflop street names. `StrategyQuery` already rejects a
        street it does not know, so an unknown value cannot arrive here; if one somehow
        did, routing it to the fallback yields an explicit refusal, while a listing
        would fall through to whatever the last branch happened to be.
        """
        return PREFLOP_COMPONENT if street == "preflop" else POSTFLOP_COMPONENT

    def decide(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        """Ask the street's owner, and return its answer untouched.

        No inspection of the outcome, deliberately. A branch here on whether a refusal
        came back is where a passive substitute would eventually get added, so there is
        nowhere for one to go.
        """
        return self._component_owning(query.street).decide(query)

    def _component_owning(
        self, street: str
    ) -> PreflopChartStrategy | PostflopFallbackStrategy:
        """The component object `component_for` named.

        Routed through `component_for` rather than repeating the street test, so the
        label a report prints and the object that actually answers cannot disagree.
        """
        if self.component_for(street) == PREFLOP_COMPONENT:
            return self.preflop
        return self.postflop
