"""Comparing the bot's preflop decisions against what real players actually did.

Three rules do most of the work here, and all three were ruled on before any code
was written.

Agreement means the observed action carries nonzero weight in the chart's own
distribution. Phase 05 collapses a mixed cell by seeded weighted sampling, so a
single drawn action compared against a single observed action mostly measures the
seed; a chart that folds seven times in ten does not disagree with a fold.

A refusal is never a disagreement. A missing chart cell and a wrong chart cell are
different findings, and folding the first into the second makes absent coverage look
like bad strategy.

The machine and the humans are separate populations. One is a near-equilibrium bot
and the others are people; an average over both describes neither. That rule binds
every rate this module computes, not only the headline one: a split by what the
player did is still a rate, and pooling the populations inside it puts the average
back after the report has just finished explaining why there isn't one.

Every decision also records the position it was taken from. A preflop chart is
indexed by position before anything else, so a disagreement rate that does not carry
one names a symptom and hides the cell.

Rebuilding a replayed decision into a query the strategy can answer lives next door in
`decision_query`, not because it is a small job but because three callers need it and this
file is at the repo's size cap. The rest of the vocabulary is the same: what a chart
answered here is what phase 13's measures and the table-state report ask about too.

And every decision records the price the actor faced. The committed chart was solved
against one opening size; these hands were not played at it. A rate computed across
both is a rate about a table the chart was never solved for, and saying so is not a
caveat on the finding, it is most of the finding.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from poker_training_bot.data_pipeline.decision_query import KIND_TO_ACTION, query_for
from poker_training_bot.data_pipeline.sample import MACHINE_PLAYER, CommittedSample
from poker_training_bot.hand_history.replay import DecisionPoint, replay_hand
from poker_training_bot.poker_core.positions import seat_positions
from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.lookup import ChartMiss
from poker_training_bot.strategy.contract import StrategyRefusal
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

# The query builder moved to its own module when this file reached its size cap. Two files
# outside this phase's scope import it from here by its old private name - phase 13's
# `table_state/measures.py` and `scripts/generate_table_state_report.py` - so the name stays
# reachable rather than editing files this lane does not own to chase a move.
_query_for = query_for

AGREE = "agree"
DISAGREE = "disagree"
REFUSED = "refused"

HUMAN_POPULATION = "humans"
POPULATIONS = (MACHINE_PLAYER, HUMAN_POPULATION)

SELF_PLAY_INVENTORY = (
    Path(__file__).resolve().parents[3] / "reports" / "active" / "latest_refusal_inventory.txt"
)

# Reported in table order rather than sorted, so a reader walks the ring the way the
# chart is indexed: earliest voluntary actor first, blinds last.
REPORTED_POSITIONS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")
REPORTED_ACTIONS = ("fold", "check", "call", "raise")

# The size an open came in at, in big blinds, banded around the size the committed
# solve assumed. Bands are only assigned to decisions facing exactly one raise: past
# that the price is a three-bet's price and comparing it to an opening size measures
# nothing. The boundaries are the solve's own opening size and the modal size these
# players actually used, so a band edge is a real thing rather than a round number.
PRICE_BANDS = (
    ("at or under 2.25bb", 2.25),
    ("2.26 to 2.50bb", 2.50),
    ("over 2.50bb", None),
)
# Every seat the committed chart holds an opening range for. One, since the cutover: the
# small blind is the only seat with a single opponent behind it, so it is the only opening
# spot the ruled predicate keeps. `t6/d100/LJ/rfi` was here and is retired, which is the
# ruled cost paid rather than worked around - a report cannot grade against a seat the chart
# no longer opens from, and reading one out by name is how this section broke.
OPEN_SIZE_SPOTS = ("t6/d100/SB/rfi",)


def named_open_prices_bb(
    sizing: PreflopSizingTable, spots: tuple[str, ...] = OPEN_SIZE_SPOTS
) -> tuple[tuple[str, float], ...]:
    """The price the solved tree assumes an open arrives at, per seat that opens.

    Not the price the bot opens to. Those parted company on 2026-08-26, when decision 6's
    sizing table moved to every price a spot offers a hand class: the small blind's open
    offers 2.5 and a 100bb shove, hero picks between them per hand with a seeded draw, and
    `amount_bb` answers None at any class holding both - so the pair this report is built on
    cannot come from there any more, and built from there it comes back empty and the price
    section formats a None.

    What the report grades against is the price an OPPONENT'S open comes in at, which is the
    number both price-band boundaries are drawn from and the number every committed spot key
    facing a single open is written at. That is the named price: the one strictly below the
    ruled stack. A shove is a stack rather than a solved bet size, and grading a corpus of
    2.25bb opens against 100 would report the sample as universally cheap and say nothing.

    Gathered across all 169 classes because the entry sits under the class. No single class
    can be asked on the spot's behalf: at the small blind's open six classes carry any of the
    shove and aces carry none of it, so aces alone would report a menu the spot does not have.

    A spot whose classes name more than one price below the stack is dropped rather than
    picked between. There is no "the" price to grade against then, and dropping is the
    fail-closed direction: the price section loses its graded row and the frozen test pinning
    this mapping goes red, where a guess here would publish a rate under a price nobody chose.
    """
    priced: list[tuple[str, float]] = []
    for spot in spots:
        named = {
            to_bb
            for hand_class_text in HAND_CLASSES
            for to_bb, _ in sizing.sizes_bb(spot, hand_class_text) or ()
            if to_bb < float(RULED_CONFIG["stack"])
        }
        if len(named) == 1:
            priced.append((spot.rsplit("/", 2)[1], named.pop()))
    return tuple(priced)


@dataclass(frozen=True)
class Rate:
    numerator: int
    denominator: int

    @property
    def percent(self) -> float:
        return 100.0 * self.numerator / self.denominator if self.denominator else 0.0


@dataclass(frozen=True)
class ComparisonRow:
    hand_id: str
    seat: int
    position: str
    player: str
    population: str
    street: str
    spot_key: str | None
    hole_cards: tuple[str, str]
    observed_action: str
    weights: tuple[tuple[str, float], ...]
    verdict: str
    refusal: StrategyRefusal | None
    price_faced_bb: float
    # None where the decision faces no raise or more than one, because a band around
    # an opening size only means something against a single open.
    price_band: str | None
    # What the strategy's own seeded collapse drew, or None where it declined to act
    # on a spot whose weights it could still read. Reported as the lesser measurement
    # it is: judgment call 5 ruled agreement is nonzero weight, not a matching draw.
    sampled_action: str | None
    # Which raises in front of this decision the lookup moved before asking the chart,
    # as (sequence index, asked bb, answered bb). Empty where every price was one the
    # chart holds, and empty where the query never reached a chart at all. This is what
    # ruling 8 costs in play rather than in theory, one decision at a time.
    price_substitutions: tuple[tuple[int, float, float], ...] = ()
    # The key the lookup asked about, carried on every row rather than only on the
    # refusals, because the substitution census has to classify answered decisions by
    # the spot they were answered at. None where no lookup happened.
    asked_spot_key: str | None = None
    # Raises in the recorded history, hero's own included. One is facing an open, two
    # is the opener facing a three-bet or a cold caller facing a squeeze, and the split
    # matters because a price band around an opening size means nothing past the first.
    raises_faced: int = 0
    # The most specific reason the chart gave, or None where it answered. Kept apart
    # from `refusal.code` because a spot the chart declares but has no cell for in
    # hero's range is a covered spot, and the census counts it as one.
    miss_code: str | None = None


@dataclass(frozen=True)
class InventoryEntry:
    spot_key: str
    count: int
    seen_in_self_play: bool


def price_band_for(price_faced_bb: float, raises_faced: int) -> str | None:
    """Which opening-size band a decision belongs to, or None if it belongs to none.

    A decision facing no raise has no price to speak of, and one facing two or more is
    being offered a three-bet's price; banding either against an opening size would
    produce a number whose label is a lie.
    """
    if raises_faced != 1:
        return None
    for label, ceiling in PRICE_BANDS:
        if ceiling is None or price_faced_bb <= ceiling:
            return label
    return None


def _selects(
    row: ComparisonRow,
    population: str,
    action: str | None,
    position: str | None,
    price_band: str | None = None,
) -> bool:
    """The one place a decision is narrowed, so every rate narrows the same way.

    Written once rather than inline at each caller because these three clauses are
    what every figure in the report means. A rate that quietly stops honouring one of
    them is not a smaller mistake than a wrong count; it is a number describing a
    different population than its label claims.
    """
    return (
        row.population == population
        and (action is None or row.observed_action == action)
        and (position is None or row.position == position)
        and (price_band is None or row.price_band == price_band)
    )


@dataclass(frozen=True)
class ComparisonResult:
    rows: tuple[ComparisonRow, ...]
    refusal_inventory: tuple[InventoryEntry, ...]
    hands_compared: int
    hands_excluded: int
    # Carried from the artifacts rather than restated here, so the report cannot claim
    # the chart was solved for something the committed files do not say.
    chart_source: str
    solved_open_bb: tuple[tuple[str, float], ...]

    @property
    def populations(self) -> tuple[str, ...]:
        return POPULATIONS

    def agreement(self, population: str) -> Rate:
        return self.agreement_within(population)

    def refusal_count(self, population: str, *, position: str | None = None) -> int:
        return sum(
            1
            for row in self.rows
            if _selects(row, population, None, position) and row.verdict == REFUSED
        )

    def decision_count(self, population: str, *, position: str | None = None) -> int:
        return sum(1 for row in self.rows if _selects(row, population, None, position))

    def agreement_within(
        self,
        population: str,
        *,
        action: str | None = None,
        position: str | None = None,
        price_band: str | None = None,
    ) -> Rate:
        """Agreement inside one population, optionally narrowed to an action or seat.

        `population` is required and has no pooled value, which is the whole point.
        Every rate this report prints is a rate about one population, because a bot and
        a table of humans averaged together describe neither, and a split by what the
        player did is no more exempt from that than the headline is.

        The two narrowings are what make a rate actionable. Roughly seven in ten preflop
        decisions are folds, and folding a bad hand is the easiest agreement in poker, so
        an unsplit rate mostly measures how often both sides threw away junk. Position
        then says which chart cells the remainder is about: a preflop chart is indexed by
        position first, so a rate without one names a symptom and hides the cause.
        """
        scored = [
            row
            for row in self.rows
            if _selects(row, population, action, position, price_band)
            and row.verdict in {AGREE, DISAGREE}
        ]
        return Rate(sum(1 for row in scored if row.verdict == AGREE), len(scored))

    def sampled_action_match(self, population: str) -> Rate:
        """How often the strategy's single drawn action equalled the player's.

        Judgment call 5 ruled that agreement means nonzero weight and that this rate
        would be reported alongside, labelled as the different and lesser thing it is.
        It is lesser because the chart collapses a mixed cell by a seeded draw, so on a
        spot played as raise three times in ten this number mostly measures the seed.
        It is reported because the ruling said it would be, and because a reader who
        prefers the strict definition should not have to regenerate anything to get it.

        The denominator is the decisions where the strategy actually returned an
        action. A spot whose weights are readable but whose raise size is not committed
        gives no draw, and counting those as misses would blame the collapse for a
        missing sizing.
        """
        drawn = [
            row
            for row in self.rows
            if row.population == population
            and row.verdict in {AGREE, DISAGREE}
            and row.sampled_action is not None
        ]
        return Rate(
            sum(1 for row in drawn if row.sampled_action == row.observed_action), len(drawn)
        )

    def open_sizes_bb(self) -> tuple[float, ...]:
        """Every opening raise size the sample contains, in big blinds.

        Taken from the decisions that faced exactly one raise rather than from the
        hands, because that is the population the price bands are computed over.
        """
        return tuple(
            sorted(row.price_faced_bb for row in self.rows if row.price_band is not None)
        )


def classify_observed_action(
    observed: str, weights: tuple[tuple[str, float], ...]
) -> str:
    """Agreement is nonzero weight, not a matching draw.

    A zero-weight entry that happens to be listed is not agreement: the chart gives
    that action no support at all, and listing it is a formatting detail of the
    artifact rather than a claim about strategy.
    """
    for action, weight in weights:
        if action == observed:
            return AGREE if weight > 0.0 else DISAGREE
    return DISAGREE


def _self_play_spots() -> frozenset[str]:
    """Spot keys the self-play run already reached, read from its committed report.

    Read rather than recomputed. The point of the cross-reference is "did the
    simulator already find this", and only the simulator's own output can answer it.

    It fails loudly when it finds nothing, and that is the important part. This is the
    one input to the comparison that is not the committed sample, and it is recovered
    by pattern from a rendered report rather than from a structured file. An empty
    result is therefore indistinguishable from a real answer: every spot silently
    becomes NEW, and the phase's most actionable claim - that real hands find spots
    self-play never reaches - inverts into a claim that they find all of them, with a
    passing gate underneath it. A missing or unrecognisable inventory is a broken
    cross-reference, not an empty one.
    """
    if not SELF_PLAY_INVENTORY.is_file():
        raise FileNotFoundError(
            f"{SELF_PLAY_INVENTORY} is missing, so no spot can be marked as already found"
            " by self-play. Run generate_profile_comparison_report first"
        )
    spots = set()
    for line in SELF_PLAY_INVENTORY.read_text(encoding="utf-8").splitlines():
        for token in line.split():
            if token.startswith("t") and token.count("/") >= 3:
                spots.add(token)
    if not spots:
        raise ValueError(
            f"{SELF_PLAY_INVENTORY} yielded no spot keys, so the self-play cross-reference"
            " would mark every real-hand spot NEW without that meaning anything."
            " The inventory's format moved and this reader has to move with it"
        )
    return frozenset(spots)


def compare_committed_sample(
    sample: CommittedSample, strategy: PreflopChartStrategy | None = None
) -> ComparisonResult:
    """Score every preflop decision in the committed sample against a chart.

    The chart is a parameter with the committed one as its default, and the default is what
    every gate command and every frozen test uses. What the parameter is for is the cutover's
    own evidence: the same comparison has to run against the RETIRED chart, read out of git
    history rather than out of `data/`, so that "the refusal rate rose" is a measurement over
    one corpus and one comparison rather than two runs of different code a reader has to
    trust agree. Passing a strategy in is the only way to get that without a second copy of
    this function, and a second copy is how the two numbers would drift.

    Pure in its arguments, which the report's byte-equality test relies on: nothing here
    reads a clock, a random source or an environment, and the one file read that is not the
    sample - the self-play inventory - is committed and raises rather than defaults.
    """
    if strategy is None:
        strategy = PreflopChartStrategy.from_repo()
    self_play = _self_play_spots()
    rows: list[ComparisonRow] = []

    for record in sample.records:
        names = record.corpus.players
        cards = record.corpus.hole_cards
        # The repo's own position vocabulary, derived from the button the converter
        # placed, rather than a second seat-to-position rule invented here.
        positions = seat_positions(
            [player.seat for player in record.normalized.players],
            record.normalized.button_seat,
        )

        def collect(point: DecisionPoint, names=names, cards=cards, positions=positions) -> None:
            query = query_for(point, cards[point.seat])
            if query is None:
                return
            observed = KIND_TO_ACTION[point.action.kind]
            outcome = strategy.weights_for(query)
            found = strategy.chart_lookup(query)
            asked_spot_key = None if found is None else found.spot_key
            substitutions = () if found is None else found.price_substitutions
            miss_code = found.code if isinstance(found, ChartMiss) else None
            player = names[point.seat]
            population = MACHINE_PLAYER if player == MACHINE_PLAYER else HUMAN_POPULATION
            big_blind = point.hand.blinds.big_blind
            price_faced_bb = round(query.current_bet / big_blind, 2)
            raises_faced = sum(1 for entry in query.preflop_actions if entry.action == "raise")
            price_band = price_band_for(price_faced_bb, raises_faced)
            if isinstance(outcome, StrategyRefusal):
                rows.append(
                    ComparisonRow(
                        hand_id=point.hand.hand_id,
                        seat=point.seat,
                        position=positions[point.seat],
                        player=player,
                        population=population,
                        street="preflop",
                        spot_key=outcome.named("spot_key"),
                        hole_cards=cards[point.seat],
                        observed_action=observed,
                        weights=(),
                        verdict=REFUSED,
                        refusal=outcome,
                        price_faced_bb=price_faced_bb,
                        price_band=price_band,
                        sampled_action=None,
                        price_substitutions=substitutions,
                        asked_spot_key=asked_spot_key,
                        raises_faced=raises_faced,
                        miss_code=miss_code,
                    )
                )
                return
            drawn = strategy.decide(query)
            rows.append(
                ComparisonRow(
                    hand_id=point.hand.hand_id,
                    seat=point.seat,
                    position=positions[point.seat],
                    player=player,
                    population=population,
                    street="preflop",
                    spot_key=None,
                    hole_cards=cards[point.seat],
                    observed_action=observed,
                    weights=outcome,
                    verdict=classify_observed_action(observed, outcome),
                    refusal=None,
                    price_faced_bb=price_faced_bb,
                    price_band=price_band,
                    sampled_action=None if isinstance(drawn, StrategyRefusal) else drawn.action,
                    price_substitutions=substitutions,
                    asked_spot_key=asked_spot_key,
                    raises_faced=raises_faced,
                    miss_code=miss_code,
                )
            )

        replay_hand(record.normalized, on_decision=collect)

    counts = Counter(
        row.spot_key or "(no expressible spot)" for row in rows if row.verdict == REFUSED
    )
    inventory = tuple(
        InventoryEntry(spot_key, count, spot_key in self_play)
        for spot_key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )
    return ComparisonResult(
        rows=tuple(rows),
        refusal_inventory=inventory,
        hands_compared=len(sample.records),
        hands_excluded=len(sample.exclusions),
        chart_source=strategy.library.artifacts[0].source.name,
        solved_open_bb=named_open_prices_bb(strategy.sizing),
    )
