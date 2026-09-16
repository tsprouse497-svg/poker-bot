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
from poker_training_bot.strategy.postflop_betting import PostflopBettingStrategy
from poker_training_bot.strategy.postflop_fallback import PostflopFallbackStrategy
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy

# These names match each component's own `strategy_id` and code prefix, so a component
# label in a report and a code prefix in an audit line refer to the same thing rather
# than to two vocabularies a reader has to reconcile.
PREFLOP_COMPONENT = "preflop-chart"
POSTFLOP_COMPONENT = "postflop-fallback"

# Two components can own the streets after the flop now: the continuity fallback that checks
# when checking is free, and the betting strategy that answers a committed flop. Which one a
# composite holds is the caller's choice and is passed in, because `from_repo` below builds the
# default the repo has always built and phase 16 does not move it.
#
# What that costs is worth stating rather than leaving to be discovered. `component_for` answers
# which *street* a component owns and is asked without a query, so it cannot read the object; a
# composite built on `PostflopBettingStrategy` therefore still reports its postflop component as
# `postflop-fallback`. The code prefix on each answer is what actually says which one replied,
# which is the attribution mechanism this module's docstring already rests on.
PostflopComponent = PostflopFallbackStrategy | PostflopBettingStrategy


@dataclass(frozen=True)
class CompositeStrategy:
    """The chart preflop, the fallback afterwards, and no third opinion.

    Frozen and field-equal like both components, so two composites built from the same
    repo compare equal and answer identically. Nothing is cached here and no state
    crosses calls, which is what lets a decision audit line be replayed.
    """

    preflop: PreflopChartStrategy
    postflop: PostflopComponent
    strategy_id: str = "composite-preflop-chart-postflop-fallback"
    strategy_version: int = 1

    @classmethod
    def from_repo(cls) -> CompositeStrategy:
        """Build from committed data, which is each library's job and not this one.

        **Postflop is the betting strategy, and wiring it here is the whole point of phase 16.**
        Until 2026-09-15 this line returned `PostflopFallbackStrategy()` while
        `PostflopBettingStrategy` was imported for a type annotation and constructed nowhere in
        `src` at all, so the bot this repo builds folded every flop - the exact behaviour the
        phase exists to replace - and the phase's frozen tests passed over it, because every one
        of them builds the betting strategy directly and none asked what `from_repo` returns.

        On a clone holding no committed flop artifact the betting strategy's library is empty and
        it refuses by code, where the fallback folded the flop without asking. That is the trade
        taken deliberately: a refusal is not an action, the composite hands it back untouched and
        the simulator voids the hand, which is the seam decision 1 accepted arriving one street
        earlier than the turn. A refusal names the gap; a fold hides it behind a decision nobody
        solved.

        The I/O belongs to both libraries. `PostflopBettingStrategy.from_repo` reads the
        committed sample and index when they are on this machine and returns an empty library
        when they are not, because a clone that has fetched nothing genuinely holds nothing.
        """
        return cls(
            preflop=PreflopChartStrategy.from_repo(),
            postflop=PostflopBettingStrategy.from_repo(),
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

    def _component_owning(self, street: str) -> PreflopChartStrategy | PostflopComponent:
        """The component object `component_for` named.

        Routed through `component_for` rather than repeating the street test, so the
        label a report prints and the object that actually answers cannot disagree.
        """
        if self.component_for(street) == PREFLOP_COMPONENT:
            return self.preflop
        return self.postflop
