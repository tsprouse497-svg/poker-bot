"""Every check the table-state report has to pass before a line of it is written to disk.

Separate from `table_state.measures` because measuring a figure and refusing to publish a
figure that does not hold are two jobs with different readers. `measures` answers questions -
what hero's depth is, what the census counted, what the corpus holds - and each answer is
short enough to read on its own. The rules below are the argument for trusting those answers,
and each one carries several paragraphs saying which canary it kills and why a weaker version
of it could not fail. Keeping them here means the reasoning can grow without crowding out the
arithmetic it is about, and it makes the dependency one-directional: this module reads
`measures`, and `measures` never reads this one.

`validate` is the single entry point. Anything that does not hold raises
`TableStateReportError`, so `scripts/generate_table_state_report.py` exits non-zero rather
than publishing it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from poker_training_bot.strategy import preflop_chart
from poker_training_bot.strategy.contract import SeatAction
from poker_training_bot.strategy.preflop_chart import (
    REFUSE_ILLEGAL,
    REFUSE_NO_SIZING,
    REFUSE_NOT_PREFLOP,
    REFUSE_RAGGED_DEPTH,
    REFUSE_SHORT_LIVE_SEAT,
    REFUSE_SIZE_BELOW_MINIMUM,
    REFUSE_UNEVEN_TABLE,
    REFUSE_UNREPRESENTABLE_PRICE,
    PreflopChartStrategy,
)
from poker_training_bot.table_state.measures import (
    ANTED,
    CLEAN,
    CORPUS_CAPPED_DECISIONS,
    CORPUS_DECISIONS,
    CORPUS_HANDS,
    CORPUS_REFUSALS,
    INVISIBLE,
    RESIDUAL,
    STRADDLED,
    TABLE_SHAPE_CODES,
    VERDICT_BY_CODE,
    CorpusCounts,
    DepthProbe,
    StraddleProbe,
    TableStateReportError,
    census_counts,
    forced_money_verdict,
    hero_start,
    independent_depth_verdict,
    observed_depth_verdict,
    seat_start,
)

# -- hero's depth, against hero's own recorded contribution ----------------- #

def _validate_depth_probes(strategy: PreflopChartStrategy, probes: Sequence[DepthProbe]) -> None:
    """Hero's depth, checked against hero's own recorded contribution.

    The canary `hero-depth-is-derived-by-subtraction-again` takes hero's depth back to the price
    it is being offered, which for a capped hero collapses to the bet level and gives 30bb where
    the truth is 25bb. Three rules catch it: the verdict the contributions imply is the verdict
    the strategy acted on; no refusal names hero as deeper or shorter than hero, which is what a
    mis-derived hero depth looks like from outside; and at least one probe is a capped hero whose
    depth and bet level differ, or none of it could have failed.

    A fourth rule pins WHICH seat a refusal names, which the first three cannot: they only ask the
    two copies of the rule to agree, and reverting both to the first offender in seat order agrees
    just as well. So the seat named has to hold the extreme stack among the live seats offending in
    that direction - recomputed below from the seat states, not from either copy - and a row in each
    direction has to exist where the extreme seat is not the first one, or the canary
    `the-depth-refusal-names-the-first-offender-in-seat-order` survives.
    """
    pinned: set[str] = set()
    for probe in probes:
        expected = independent_depth_verdict(probe.query)
        observed = observed_depth_verdict(strategy, probe.query)
        if observed != expected:
            raise TableStateReportError(
                f"{probe.label}: hero started with {hero_start(probe.query)} chips by its own seat"
                f" record, so this table is {expected} and the strategy acted on {observed}"
            )
        if observed.seat == probe.query.seat:
            raise TableStateReportError(
                f"{probe.label}: the refusal names seat {probe.query.seat} as deeper or shorter"
                " than hero, and that seat is hero"
            )
        if observed.seat is None or observed.kind not in ("deeper", "shorter"):
            continue
        deeper = observed.kind == "deeper"
        started = hero_start(probe.query)
        live = [seat_start(probe.query, s.seat) for s in probe.query.seat_states if not s.folded]
        starts = [c for c in live if (c > started if deeper else c < started)]
        extreme = max(starts) if deeper else min(starts)
        if seat_start(probe.query, observed.seat) != extreme:
            raise TableStateReportError(
                f"{probe.label}: the live seats {observed.kind} than hero sat down with {starts} in"
                f" seat order, and the refusal names seat {observed.seat}, which sat down with"
                f" {seat_start(probe.query, observed.seat)} rather than the extreme {extreme}"
            )
        if starts[0] != extreme:
            pinned.add(observed.kind)
    if not any(probe.diverges for probe in probes):
        raise TableStateReportError(
            "no probe has a capped hero whose true depth differs from the street's bet level, so"
            " nothing here would notice hero's depth taken from the price"
        )
    if pinned != {"deeper", "shorter"}:
        raise TableStateReportError(
            "the seat a depth refusal names is only pinned on a table where a nearer seat offends"
            f" in the same direction, and that holds for {sorted(pinned)} rather than both"
        )

# -- the straddle census ---------------------------------------------------- #

# The other side of `measures.VERDICT_BY_CODE`, listed by hand rather than defaulted: every
# refusal the strategy declares that is deliberately not a statement about forced money. A
# code in neither table is what `_validate_verdict_coverage` fails on, and the listing is the
# whole point - `forced_money_verdict` falls back to CLEAN, so a refusal code added to the
# strategy without a decision here would silently be counted as a pot holding nothing
# forced. Lookup misses (`preflop-chart:lookup:*`) are not listed and not checked: they are
# coverage misses raised by the artifact layer, they carry no claim about the money, and
# their vocabulary belongs to `solver_artifacts.lookup` rather than to the strategy.
_NOT_FORCED_MONEY = frozenset(
    {
        REFUSE_NOT_PREFLOP,
        REFUSE_RAGGED_DEPTH,
        REFUSE_UNEVEN_TABLE,
        REFUSE_SHORT_LIVE_SEAT,
        REFUSE_ILLEGAL,
        REFUSE_NO_SIZING,
        REFUSE_SIZE_BELOW_MINIMUM,
        REFUSE_UNREPRESENTABLE_PRICE,
    }
)


def _validate_verdict_coverage() -> None:
    """Every refusal the strategy declares is classified, one way or the other.

    This replaces a check that counted the four census classes and compared the total against
    the number of probes. That one could not fail for any input or any implementation:
    `forced_money_verdict` is `VERDICT_BY_CODE.get(code, CLEAN)`, which returns one of those
    four names and nothing else, so the total was `len(probes)` by construction. What is
    genuinely at risk is the `.get` default rather than the arithmetic - a new forced-money
    refusal code lands in the strategy, no line here mentions it, and every pot refused under
    it is counted as holding no forced money at all. That fails here, at the next run, which is
    what the vacuous count only looked like it was doing.
    """
    declared = {
        value
        for name, value in vars(preflop_chart).items()
        if name.startswith("REFUSE_") and isinstance(value, str)
    }
    unclassified = sorted(declared - set(VERDICT_BY_CODE) - _NOT_FORCED_MONEY)
    if unclassified:
        raise TableStateReportError(
            f"the strategy can refuse with {unclassified}, and this census says nothing about"
            " whether that is forced money, so every pot refused that way would be counted as"
            " holding none"
        )


def _validate_straddle_census(
    strategy: PreflopChartStrategy, probes: Sequence[StraddleProbe]) -> None:
    """The census, reconciled against the minimum raise the detector predicted.

    The canary `an-absorbed-straddle-goes-unseen` drops the minimum-raise signal, the only one that
    can see a straddler who has already called to the level: that seat holds exactly what an
    ordinary caller holds. One implication catches it - a pot whose offered minimum raise disagrees
    with the prediction is straddled and must be counted as straddled - checked in both directions,
    because a detector calling every pot straddled would satisfy half of it alone.

    The residual row is measured here too rather than stated: the pots that truly hold a
    straddle no signal can see have to be counted as holding no forced money at all, which is
    what makes the census's own `no forced money` count exceed the number of clean pots.
    """
    for probe in probes:
        verdict = forced_money_verdict(strategy, probe.query)
        offered, predicted = probe.min_raise_pair
        if probe.disagrees and verdict != STRADDLED:
            raise TableStateReportError(
                f"{probe.label}: the table offers a minimum raise of {offered} where the blinds and"
                f" the recorded raises predict {predicted}, a straddle counted as {verdict!r}"
            )
        if probe.truth == CLEAN and verdict != CLEAN:
            raise TableStateReportError(
                f"{probe.label}: no forced money here, and the census counted it as {verdict!r}"
            )
        if probe.truth in (STRADDLED, ANTED, RESIDUAL) and verdict != probe.truth:
            raise TableStateReportError(
                f"{probe.label}: this pot is {probe.truth}, counted as {verdict!r}"
            )
    absorbed = [probe for probe in probes if probe.absorbed]
    if len(absorbed) != 1:
        raise TableStateReportError(
            "the census needs exactly one absorbed straddle, the pot the deleted bound admitted,"
            f" and holds {len(absorbed)}"
        )
    counts = census_counts(strategy, probes)
    if not absorbed[0].disagrees or forced_money_verdict(strategy, absorbed[0].query) != STRADDLED:
        raise TableStateReportError(
            "the absorbed straddle is not counted as a straddle through a minimum raise that"
            " disagrees with the prediction, so the pot the deleted bound let through goes"
            " unseen here too"
        )
    truly = sum(1 for probe in probes if probe.truth == STRADDLED)
    if counts[STRADDLED] != truly:
        raise TableStateReportError(
            f"the census counted {counts[STRADDLED]} pots as straddled where {truly} hold one"
        )
    _validate_verdict_coverage()
    unseen = [probe for probe in probes if probe.truth == INVISIBLE]
    if not unseen or any(forced_money_verdict(strategy, p.query) != CLEAN for p in unseen):
        raise TableStateReportError(
            "the residual needs at least one pot that truly holds a straddle, and every such"
            " pot has to be counted as holding no forced money at all"
        )

# -- the committed corpus, as a checked regression proof -------------------- #

def _validate_corpus(counts: CorpusCounts) -> None:
    """A regression proof: every table-shape count is zero because all 499 corpus hands are one
    flat structure, so a zero that moves is a defect, and so is a moved denominator."""
    for label, measured, expected in (
        ("hands compared", counts.hands, CORPUS_HANDS),
        ("preflop decision points", counts.decisions, CORPUS_DECISIONS),
        ("refusals", counts.refusals, CORPUS_REFUSALS),
        ("decisions priced at hero's whole stack", counts.capped, CORPUS_CAPPED_DECISIONS),
    ):
        if measured != expected:
            raise TableStateReportError(
                f"{label} measured {measured} against the {expected} this phase started from,"
                " so the replay changed, which this phase does not touch"
            )
    for code in TABLE_SHAPE_CODES:
        if counts.count(code):
            raise TableStateReportError(
                f"{counts.count(code)} corpus decisions refused with {code}, and the corpus holds"
                " no asymmetric, straddled or anted table, so that is a defect not a discovery"
            )
    # These two were `under_raises > facing_a_raise` and `short_all_in_calls >
    # with_a_recorded_call`, neither of which could fail for any input or any implementation:
    # a query is counted in the denominator whenever it holds the entry the numerator
    # iterates, so each numerator is a subset of its own denominator pointwise. The claim the
    # report actually makes about these numbers is that they are zero - "every raise in the
    # corpus is a full legal raise", and no corpus call is tagged all-in at all - and that is
    # a claim a changed replay, converter or corpus can falsify, exactly like the table-shape
    # zeros above.
    #
    # The second zero is the weaker of the two, and the report now says so rather than reading
    # it as "every corpus all-in is for the exact level", which it is not evidence for.
    # `has_a_short_all_in_call` asks two things of a recorded call - that the seat is marked
    # all-in, and that its street figure is below the level - and measured over the corpus only
    # the flag is load-bearing: none of the 183 recorded call entries comes from an all-in seat,
    # the corpus holds 10 all-in seat-states across 18,288, and loosening `street_bet <
    # current_bet` to `<=` leaves the count at zero. A check insensitive to its own comparison
    # pins only what the other half of it asks, which here is that the converter never tags a
    # call all-in.
    if counts.under_raises:
        raise TableStateReportError(
            f"{counts.under_raises} of the {counts.facing_a_raise} corpus decisions facing a"
            " raise carry a recorded raise below the legal minimum, and the report states that"
            " every raise in the corpus is a full legal raise"
        )
    if counts.short_all_in_calls:
        raise TableStateReportError(
            f"{counts.short_all_in_calls} of the {counts.with_a_recorded_call} corpus decisions"
            " whose history holds a call carry one from a seat all-in for less than the level,"
            " so the corpus now records a call from an all-in seat where the report states that"
            " it records none"
        )

# -- the record a report producer computes by hand -------------------------- #

def _validate_impossible_history_is_refused(probes: Sequence[StraddleProbe]) -> None:
    """The one betting sequence no street produces is refused where the record is built.

    `StrategyQuery` refuses a preflop raise-to at or below the standing level. Both walks in
    `table_state.forced_money` take their level from that same sequence, so without the rule a
    sub-level entry drops the level and every increment after it is measured from the wrong
    number. Measured, at 50/100 six-handed with the button at seat 3 and the history `LJ fold,
    HJ raise 250, CO raise 200, BTN call, SB fold, BB call` against an offered minimum raise of
    400: the min-raise walk predicts 350 and the pot is announced as holding a straddle, and the
    contributions walk predicts {1: 250, 2: 200, 3: 200, 5: 200} where the seats that paid the
    real level hold 250 each, so with the straddle signal quieted the same pot is announced as a
    blind structure this repo cannot represent, naming a seat for 50 chips of forced money. Both
    are poker claims about a pot with nothing forced in it.

    Checked here because nothing else in the gate can check it. The rule is not reachable from a
    frozen test that was written before the defect was found, and all 66 of them pass with it
    present or absent; `BettingRoundState.apply` rejects a sub-level raise, so no live producer
    emits one and only a hand-computed report query can. `dataclasses.replace` re-runs
    `__post_init__` on the frozen dataclass, so corrupting a probe this report already builds is
    a direct test of the constructor the report's own queries go through.

    The canary `an-impossible-raise-sequence-still-constructs` names this validator and the module
    it lives in, so moving or renaming it means editing `verification/mutations.yml` in the same
    change. Both were written in the same round and the registry entry already says
    `table_state/checks.py`; keep them in step.
    """
    if not probes:
        raise TableStateReportError(
            "the boundary rule on preflop_actions is checked by corrupting a probe, and there"
            " is no probe to corrupt"
        )
    query = probes[0].query
    _, big_blind = query.blinds
    standing, below = 5 * big_blind, 4 * big_blind
    impossible = (
        SeatAction(query.seat, "raise", standing),
        SeatAction(query.seat, "raise", below),
    )
    try:
        replace(query, preflop_actions=impossible)
    except ValueError:
        return
    raise TableStateReportError(
        f"a query accepted a preflop history where seat {query.seat} raises to {below} over a"
        f" standing level of {standing}, which no betting round produces; the forced-money walks"
        " take the level from that sequence, so such a pot is reported as straddled or as an"
        " unrepresentable blind structure while holding nothing forced at all"
    )


def validate(
    strategy: PreflopChartStrategy, depth_probes: Sequence[DepthProbe],
    straddle_probes: Sequence[StraddleProbe], corpus: CorpusCounts,
) -> None:
    """Every check this report has to pass before any of it is written to disk."""
    _validate_depth_probes(strategy, depth_probes)
    _validate_straddle_census(strategy, straddle_probes)
    _validate_impossible_history_is_refused(straddle_probes)
    _validate_corpus(corpus)
