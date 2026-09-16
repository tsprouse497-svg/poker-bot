"""One strategy object that plays a whole hand, by routing and nothing else.

Preflop belongs to the committed charts and flop through river belongs to the postflop
component - since phase 16 the betting strategy that answers a committed flop, and
before it the continuity fallback that checked when checking was free. Both halves
already exist; what was missing was a single place that says which one owns a street,
so that Phase 07 hands a hand to one object instead of reassembling the routing at
every call site and getting it subtly different in each.

The design constraint is that this module adds no poker. Its outcome for any query is
the outcome its component would have returned, as the same object, which is why
`decide` returns what it received without touching the amount and without rewriting
the code. That is not tidiness: the code prefix is the whole attribution mechanism, so
an audit line reading `preflop-chart:` or `postflop-betting:` is evidence about which
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
POSTFLOP_COMPONENT = "postflop-betting"

# Two components can own the streets after the flop: the continuity fallback that checks when
# checking is free, and the betting strategy that answers a committed flop out of solved data.
# Which one a composite holds is the caller's choice and is passed in; `from_repo` below builds
# the betting strategy, which is what `POSTFLOP_COMPONENT` above is named after.
#
# `component_for` is a constant per street rather than a read of `self.postflop`, so the constant
# has to follow `from_repo` by hand - and it did not, between the rewiring on 2026-09-15 and
# decision 16a on 2026-09-16. An earlier version of this comment argued the drift was harmless
# because the code prefix on each answer says which component replied. It is not harmless. The
# postflop report generator is a gate command whose summary table headings come from
# `component_for` and carry no code prefix, so the stale label filed three `postflop-betting:`
# refusals under a column headed `postflop-fallback`, directly beneath a sentence saying none of
# them came from the fallback. A reader deciding whether the bot's flop play is worth studying
# reads the heading, not the prefixes further down. The name follows the behaviour.
#
# A composite deliberately built on `PostflopFallbackStrategy` is now mislabelled in the other
# direction by the same mechanism. Nothing in `src` builds one, and reading `self.postflop`
# instead would fix both, but `component_for`'s body is a mutation canary's exact find string,
# so the shape stays as ruled and the alternative is a finding rather than a change.
PostflopComponent = PostflopFallbackStrategy | PostflopBettingStrategy


@dataclass(frozen=True)
class CompositeStrategy:
    """The chart preflop, the postflop component afterwards, and no third opinion.

    Frozen and field-equal like both components, so two composites built from the same
    repo compare equal and answer identically. Nothing is cached here and no state
    crosses calls, which is what lets a decision audit line be replayed.
    """

    preflop: PreflopChartStrategy
    postflop: PostflopComponent
    strategy_id: str = "composite-preflop-chart-postflop-betting"
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
        did, routing it to the postflop component yields an explicit refusal, while a
        listing would fall through to whatever the last branch happened to be.

        The string it returns is the postflop component's own `strategy_id` and code
        prefix, kept in step by hand and by the comment above `PostflopComponent`.
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
