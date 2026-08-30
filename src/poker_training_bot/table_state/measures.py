"""Every figure the table-state report publishes, measured.

Measuring only, twice over: the text lives in `scripts/generate_table_state_report.py`, and the
rules that refuse to publish a figure that does not hold live in `table_state.checks`, which
reads this module and is never read by it. A figure that cannot be measured at all raises
`TableStateReportError` from here; a figure that is measured and then fails a rule raises the
same error from there, and either way the command exits non-zero rather than publishing it.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from poker_training_bot.data_pipeline.comparison import _query_for
from poker_training_bot.data_pipeline.sample import load_committed_sample
from poker_training_bot.hand_history.replay import DecisionPoint, replay_hand
from poker_training_bot.solver_artifacts.lookup import ChartHit, ChartMiss
from poker_training_bot.strategy.contract import StrategyQuery, StrategyRefusal
from poker_training_bot.strategy.preflop_chart import (
    REFUSE_ANTE,
    REFUSE_BLIND_STRUCTURE,
    REFUSE_RAGGED_DEPTH,
    REFUSE_SHORT_LIVE_SEAT,
    REFUSE_STRADDLE,
    REFUSE_UNEVEN_TABLE,
    PreflopChartStrategy,
)
from poker_training_bot.table_state.forced_money import predicted_min_raise_target

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_FIXTURE = REPO_ROOT / "data" / "samples" / "normalized_hands.json"
MOVING_FIXTURE_HAND = "phase02-three-way-side-pot"
# What that fixture refused at all three of its preflop decisions before this phase.
BEFORE_MOVING_CODE = "preflop-chart:lookup:no-artifact-for-table-size"

# What the corpus holds. `checks._validate_corpus` demands equality against these, so each is
# a claim about what may and may not move.
#
# The sample and the decision count are the replay, which this report does not touch: a moved
# denominator there is a defect, and holding them at equality is the whole point of the pair.
# The capped count is the population the `to_call` ruling of 2026-08-20 is about, and the one
# the deleted depth derivation was wrong for; it is a property of the recorded hands rather
# than of any chart, so it does not move with one either.
#
# The refusal count does move with the chart, and it moved: 290 until the chart cutover, 2,529
# after it. The cutover replaced the raked chart with a rake-free solve derived under a
# selection rule that keeps a spot only where the source prices every terminal below it, which
# gives up four of the five opening ranges and ten of the eleven spots facing a single open. So
# the decisions that reached those spots are refused now, and the contract for that phase
# requires this number to rise rather than fall. It stays pinned at equality rather than
# becoming a floor: a refusal count that drifts silently is exactly what a coverage change
# looks like from here, and the point of the pin is that changing the chart has to be a
# deliberate edit to this line.
CORPUS_HANDS = 499
CORPUS_DECISIONS = 3048
CORPUS_REFUSALS = 2529
CORPUS_CAPPED_DECISIONS = 10

DEPTH_CODES = (REFUSE_RAGGED_DEPTH, REFUSE_UNEVEN_TABLE, REFUSE_SHORT_LIVE_SEAT)
TABLE_SHAPE_CODES = DEPTH_CODES + (REFUSE_STRADDLE, REFUSE_ANTE, REFUSE_BLIND_STRUCTURE)

STRADDLED = "straddled"
ANTED = "anted"
RESIDUAL = "forced money of no named kind"
CLEAN = "no forced money"
INVISIBLE = "straddled, and invisible to all three signals"


class TableStateReportError(RuntimeError):
    """A measurement that does not hold, raised rather than published."""

# -- hero's depth, from hero's own recorded contribution -------------------- #

@dataclass(frozen=True)
class DepthVerdict:
    """A table's shape, in the vocabulary the refusal codes already use."""

    kind: str
    seat: int | None = None
    depth_bb: str | None = None

    def __str__(self) -> str:
        if self.kind == "flat":
            return f"flat at {self.depth_bb}bb"
        if self.kind == "ragged":
            return "hero's own depth is not a whole big blind"
        which = "deeper than" if self.kind == "deeper" else "shorter than"
        return f"seat {self.seat} is {which} hero, holding {self.depth_bb}bb"


def depth_text(chips: int, big_blind: int) -> str:
    """Chips as big blinds, exactly, with no trailing zeros."""
    return format((Decimal(chips) / Decimal(big_blind)).normalize(), "f")


def seat_start(query: StrategyQuery, seat: int) -> int:
    """What a seat sat down with: what it holds plus what its own record says it put in."""
    state = next(entry for entry in query.seat_states if entry.seat == seat)
    return dict(query.stacks)[seat] + state.committed_total


def hero_start(query: StrategyQuery) -> int:
    """The one derivation this phase exists for, taken from hero's own seat record.

    No contribution anywhere in this module comes out of `to_call`: the price is capped at what
    hero can pay, so the subtraction that used to recover hero's own is now wrong. The price is
    read twice a few lines below, in `priced_at_heros_whole_stack`, to ask whether it takes
    hero's whole stack - a question about the price, not a contribution derived from it.
    """
    hero = next(state for state in query.seat_states if state.seat == query.seat)
    return dict(query.stacks)[query.seat] + hero.street_bet


def priced_at_heros_whole_stack(query: StrategyQuery) -> bool:
    """Whether the price to call takes everything hero holds."""
    return query.to_call > 0 and query.to_call == dict(query.stacks)[query.seat]


def level_as_depth(query: StrategyQuery) -> str:
    """The bet level as a depth: what the pre-phase code returned for a capped hero, and
    printed beside the truth rather than derived from for anything."""
    _, big_blind = query.blinds
    return depth_text(query.current_bet, big_blind)


def independent_depth_verdict(query: StrategyQuery) -> DepthVerdict:
    """The table shape `seat_states` alone says this query has.

    A second copy of the strategy's rule, not an oracle: contributions rather than the price, the
    ruled order, folded seats skipped, and the extreme seat in the offending direction with ties to
    the lowest seat are all exactly what `_table_depth_bb` does. Two copies cannot show the rule is
    right. What they do show is a change that landed on only one of them - a refactor or a mutation
    touching the strategy alone stops agreeing here and the report exits non-zero - which is a real
    if narrower guarantee. That the seat named is the extreme one is the part two agreeing copies
    cannot establish, so `_validate_depth_probes` asserts it separately.
    """
    _, big_blind = query.blinds
    started = hero_start(query)
    if started <= 0 or started % big_blind:
        return DepthVerdict("ragged")
    live = [(seat_start(query, s.seat), s.seat) for s in query.seat_states if not s.folded]
    deep = max(live, default=None, key=lambda pair: (pair[0], -pair[1]))
    short = min(live, default=None)
    if deep is not None and deep[0] > started:
        return DepthVerdict("deeper", deep[1], depth_text(deep[0], big_blind))
    if short is not None and short[0] < started:
        return DepthVerdict("shorter", short[1], depth_text(short[0], big_blind))
    return DepthVerdict("flat", None, depth_text(started, big_blind))


def _depth_from_key(text: str) -> str:
    for part in text.split("/"):
        if part.startswith("d") and part[1:].isdigit():
            return part[1:]
    raise TableStateReportError(f"the spot key {text!r} carries no stack depth")


def observed_depth_verdict(strategy: PreflopChartStrategy, query: StrategyQuery) -> DepthVerdict:
    """The table shape the strategy acted on: named in a depth refusal's detail, and
    otherwise the depth the lookup asked at, from the spot key or the miss detail."""
    outcome = strategy.decide(query)
    if isinstance(outcome, StrategyRefusal) and outcome.code in DEPTH_CODES:
        if outcome.code == REFUSE_RAGGED_DEPTH:
            return DepthVerdict("ragged")
        kind = "deeper" if outcome.code == REFUSE_UNEVEN_TABLE else "shorter"
        named = outcome.named("seat")
        seat = None if named is None else int(named)
        return DepthVerdict(kind, seat, outcome.named("stack_depth_bb"))
    found = strategy.chart_lookup(query)
    if isinstance(found, ChartHit | ChartMiss) and found.spot_key:
        return DepthVerdict("flat", None, _depth_from_key(found.spot_key))
    if isinstance(outcome, StrategyRefusal) and outcome.named("stack_depth_bb"):
        return DepthVerdict("flat", None, outcome.named("stack_depth_bb"))
    raise TableStateReportError(
        f"the strategy answered {outcome} without saying which depth it derived, so this"
        " report cannot check the figure it is about to print"
    )


@dataclass(frozen=True)
class DepthProbe:
    """One table where hero's depth is worth printing, and what it refused before."""

    label: str
    query: StrategyQuery
    before_code: str = ""

    @property
    def diverges(self) -> bool:
        """A capped hero whose true depth is not the street's bet level. A probe where the
        pre-phase collapse lands on the right answer anyway checks nothing."""
        _, big_blind = self.query.blinds
        truth = depth_text(hero_start(self.query), big_blind)
        return priced_at_heros_whole_stack(self.query) and level_as_depth(self.query) != truth


# -- the straddle census ---------------------------------------------------- #

# Which refusal codes are a statement about forced money, and what the census calls each. The
# other side of it - every code that is deliberately NOT such a statement - is listed by hand
# in `table_state.checks`, which fails on a code appearing in neither.
VERDICT_BY_CODE = {
    REFUSE_STRADDLE: STRADDLED,
    REFUSE_ANTE: ANTED,
    REFUSE_BLIND_STRUCTURE: RESIDUAL,
}


@dataclass(frozen=True)
class StraddleProbe:
    """One pot and what it truly holds, for the census to classify."""

    label: str
    truth: str
    query: StrategyQuery
    absorbed: bool = False

    @property
    def min_raise_pair(self) -> tuple[int, int | None]:
        """What the table offers as a minimum raise, and what the blinds predict."""
        _, big_blind = self.query.blinds
        predicted = predicted_min_raise_target(big_blind, self.query.preflop_actions)
        return self.query.min_raise_target, predicted

    @property
    def disagrees(self) -> bool:
        offered, predicted = self.min_raise_pair
        return predicted is not None and predicted != offered


def forced_money_verdict(strategy: PreflopChartStrategy, query: StrategyQuery) -> str:
    """What the three signals made of a pot, as the census counts it."""
    outcome = strategy.decide(query)
    code = outcome.code if isinstance(outcome, StrategyRefusal) else ""
    return VERDICT_BY_CODE.get(code, CLEAN)


def census_counts(strategy: PreflopChartStrategy, probes: Sequence[StraddleProbe]) -> Counter[str]:
    """How many pots the detector put in each class."""
    return Counter(forced_money_verdict(strategy, probe.query) for probe in probes)


# -- the committed corpus, as a checked regression proof -------------------- #

@dataclass(frozen=True)
class CorpusCounts:
    """Every corpus figure this report prints, measured in one walk of the sample."""

    hands: int
    decisions: int
    refusals: int
    by_code: tuple[tuple[str, int], ...]
    capped: int
    capped_diverging: int
    facing_a_raise: int
    with_a_recorded_call: int
    under_raises: int
    short_all_in_calls: int

    def count(self, code: str) -> int:
        return dict(self.by_code).get(code, 0)


def corpus_queries() -> Iterator[StrategyQuery]:
    """Every preflop decision the corpus produces, through the comparison's own builder."""
    for record in load_committed_sample().records:
        replayed: list[DecisionPoint] = []
        replay_hand(record.normalized, on_decision=replayed.append)
        for point in replayed:
            query = _query_for(point, record.corpus.hole_cards[point.seat])
            if query is not None:
                yield query


def has_an_under_raise(query: StrategyQuery) -> bool:
    """Whether any recorded raise is below the full raise a legal action produces: the
    standing level plus the larger of the previous increment and one big blind."""
    _, big_blind = query.blinds
    level = increment = big_blind
    for entry in query.preflop_actions:
        if entry.action != "raise" or entry.amount is None:
            continue
        if entry.amount < level + max(increment, big_blind):
            return True
        increment = entry.amount - level
        level = entry.amount
    return False


def has_a_short_all_in_call(query: StrategyQuery) -> bool:
    """Whether any recorded call came from a seat all-in for less than the level."""
    states = {state.seat: state for state in query.seat_states}
    return any(
        entry.action == "call" and states[entry.seat].all_in
        and states[entry.seat].street_bet < query.current_bet
        for entry in query.preflop_actions
    )


def measure_corpus(strategy: PreflopChartStrategy) -> CorpusCounts:
    """Walk every committed corpus decision once and count everything the report needs."""
    codes: Counter[str] = Counter()
    decisions = capped = diverging = raises = calls = under = short = 0
    for query in corpus_queries():
        decisions += 1
        outcome = strategy.weights_for(query)
        if isinstance(outcome, StrategyRefusal):
            codes[outcome.code] += 1
        if priced_at_heros_whole_stack(query):
            capped += 1
            # Measured rather than assumed: every corpus seat starts with exactly 100bb, so the
            # level a capped hero faces is at most what hero itself started with, and the two
            # readings of hero's depth cannot come apart anywhere in the corpus.
            if query.current_bet != hero_start(query):
                diverging += 1
        raises += any(entry.action == "raise" for entry in query.preflop_actions)
        calls += any(entry.action == "call" for entry in query.preflop_actions)
        under += has_an_under_raise(query)
        short += has_a_short_all_in_call(query)
    return CorpusCounts(
        hands=len(load_committed_sample().records), decisions=decisions,
        refusals=sum(codes.values()), by_code=tuple(sorted(codes.items())),
        capped=capped, capped_diverging=diverging, facing_a_raise=raises,
        with_a_recorded_call=calls, under_raises=under, short_all_in_calls=short,
    )


# -- the recomputable number the report prints the recipe for --------------- #

def recomputed_pot(query: StrategyQuery) -> tuple[int, ...]:
    """The recorded amounts a reader adds up to get this decision's pot, checked.

    The recipe the report prints is executed rather than described: the amounts in the
    committed JSON have to sum to the pot the replayed query carried.
    """
    hands = json.loads(SAMPLE_FIXTURE.read_text(encoding="utf-8"))["hands"]
    hand = next(entry for entry in hands if entry["hand_id"] == MOVING_FIXTURE_HAND)
    actions = hand["streets"][0]["actions"]
    hero_call = next(
        i for i, act in enumerate(actions) if act["seat"] == query.seat and act["kind"] == "call"
    )
    addends = tuple(int(action["amount"]) for action in actions[:hero_call])
    if sum(addends) != query.pot:
        raise TableStateReportError(
            f"the preflop amounts recorded in {SAMPLE_FIXTURE.name} for {MOVING_FIXTURE_HAND} add"
            f" up to {sum(addends)}, and the query built by replaying that hand carries a pot of"
            f" {query.pot}"
        )
    return addends
