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
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from poker_training_bot.data_pipeline.sample import MACHINE_PLAYER, CommittedSample
from poker_training_bot.hand_history.replay import DecisionPoint, replay_hand
from poker_training_bot.hand_history.schema import HistoryActionKind, StreetName
from poker_training_bot.poker_core.positions import seat_positions
from poker_training_bot.strategy.contract import SeatAction, StrategyQuery, StrategyRefusal
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy

AGREE = "agree"
DISAGREE = "disagree"
REFUSED = "refused"

HUMAN_POPULATION = "humans"
POPULATIONS = (MACHINE_PLAYER, HUMAN_POPULATION)

SELF_PLAY_INVENTORY = (
    Path(__file__).resolve().parents[3] / "reports" / "active" / "latest_refusal_inventory.txt"
)

_KIND_TO_ACTION = {
    HistoryActionKind.FOLD: "fold",
    HistoryActionKind.CHECK: "check",
    HistoryActionKind.CALL: "call",
    HistoryActionKind.BET: "bet",
    HistoryActionKind.RAISE: "raise",
}

# Reported in table order rather than sorted, so a reader walks the ring the way the
# chart is indexed: earliest voluntary actor first, blinds last.
REPORTED_POSITIONS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")
REPORTED_ACTIONS = ("fold", "check", "call", "raise")


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


@dataclass(frozen=True)
class InventoryEntry:
    spot_key: str
    count: int
    seen_in_self_play: bool


def _selects(
    row: ComparisonRow,
    population: str,
    action: str | None,
    position: str | None,
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
    )


@dataclass(frozen=True)
class ComparisonResult:
    rows: tuple[ComparisonRow, ...]
    refusal_inventory: tuple[InventoryEntry, ...]
    hands_compared: int
    hands_excluded: int

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
            if _selects(row, population, action, position) and row.verdict in {AGREE, DISAGREE}
        ]
        return Rate(sum(1 for row in scored if row.verdict == AGREE), len(scored))


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


def _query_for(point: DecisionPoint, hole_cards: tuple[str, str]) -> StrategyQuery | None:
    """Rebuild the decision context the acting seat faced, or None if it is not one.

    Everything but the hole cards comes from the replayer's own turn state, so the
    query describes the hand as the frozen Phase 02 replayer understands it rather
    than as this module re-derives it.
    """
    if point.street is not StreetName.PREFLOP:
        return None
    if point.action.kind is HistoryActionKind.POST_BLIND:
        return None
    state = point.turn.round
    hero = state.player(point.seat)
    stacks = tuple(
        (player.seat, player.stack) for player in sorted(state.players, key=lambda p: p.seat)
    )
    legal = tuple(kind.value for kind in point.legal_actions)
    seen: list[SeatAction] = []
    for action in point.hand.streets[0].actions:
        if action.kind is HistoryActionKind.POST_BLIND:
            continue
        if action is point.action:
            break
        seen.append(SeatAction(action.seat, _KIND_TO_ACTION[action.kind]))
    return StrategyQuery(
        hand_id=point.hand.hand_id,
        street="preflop",
        seat=point.seat,
        button_seat=point.hand.button_seat,
        hole_cards=hole_cards,
        board=(),
        legal_actions=legal,
        to_call=max(0, state.current_bet - hero.street_bet),
        # The street's bet level rather than hero's own contribution to it, which is
        # the reading `_table_depth_bb` needs to recover hero's starting depth.
        street_bet=state.current_bet,
        min_raise_target=state.current_bet + state.min_raise,
        pot=sum(player.committed_total for player in state.players),
        stacks=stacks,
        blinds=(point.hand.blinds.small_blind, point.hand.blinds.big_blind),
        preflop_actions=tuple(seen),
    )


def compare_committed_sample(sample: CommittedSample) -> ComparisonResult:
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
            query = _query_for(point, cards[point.seat])
            if query is None:
                return
            observed = _KIND_TO_ACTION[point.action.kind]
            outcome = strategy.weights_for(query)
            player = names[point.seat]
            population = MACHINE_PLAYER if player == MACHINE_PLAYER else HUMAN_POPULATION
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
                    )
                )
                return
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
    )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

_PREAMBLE = """\
Real-Hand Comparison Report
===========================

Read this before any number below.

This compares the bot's preflop decisions against what real players did in the same
spots, using a committed slice of a public hand corpus that nobody in this repo wrote.
It is a preflop comparison and nothing else. The postflop half of this bot is a
continuity fallback that never bets and never raises, so comparing it against real
postflop play would measure the fallback's known shape rather than these hands.

A disagreement means this chart and this player did different things in this spot. It
does not establish that either is wrong. Real players are not an oracle for strategy
quality, and one of the seats here is a near-equilibrium machine while the others are
people, which is why they are never averaged together.

Agreement means the action the player took carries nonzero weight in the chart's own
distribution, not that it matched the single action the chart happens to draw. A chart
that folds a hand seven times in ten does not disagree with a fold.

A spot the chart could not answer is a refusal. Refusals are reported on their own and
are never counted as disagreements, because a missing chart cell and a wrong chart cell
need different fixes.
"""


def _cell(rate: Rate) -> str:
    """One cell of the position table: agreed over scored, or a dash for no decisions."""
    return f"{rate.numerator}/{rate.denominator}" if rate.denominator else "-"


def render_comparison_report(result: ComparisonResult) -> str:
    lines = [_PREAMBLE, ""]
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"  hands compared                    {result.hands_compared:6d}")
    lines.append(f"  hands excluded, named below       {result.hands_excluded:6d}")
    lines.append(f"  preflop decision points           {len(result.rows):6d}")
    lines.append("")
    lines.append("## Agreement, by population")
    lines.append("")
    lines.append("  Every rate carries the count it was computed over. Refusals are not in")
    lines.append("  the denominator; they are reported beside it.")
    lines.append("")
    for population in result.populations:
        rate = result.agreement(population)
        refused = result.refusal_count(population)
        total = sum(1 for row in result.rows if row.population == population)
        lines.append(f"  {population}")
        lines.append(
            f"    agreed {rate.numerator} of {rate.denominator} scored decisions"
            f"  ({rate.percent:.1f}%)"
        )
        lines.append(f"    refused {refused} of {total} decision points")
        lines.append("")
    lines.append("## The number that matters more than the one above")
    lines.append("")
    lines.append("  Read this before quoting any figure from the previous section.")
    lines.append("")
    lines.append("  Roughly seven in ten preflop decisions in any six-handed sample are folds,")
    lines.append("  and folding a bad hand is the easiest agreement in poker. An unsplit")
    lines.append("  agreement rate is therefore mostly a measurement of how often both sides")
    lines.append("  threw away junk, and it will look high no matter what the chart does with")
    lines.append("  the hands people actually play. Split by what the player did:")
    lines.append("")
    for population in result.populations:
        lines.append(f"  {population}")
        for action in REPORTED_ACTIONS:
            rate = result.agreement_within(population, action=action)
            if not rate.denominator:
                continue
            lines.append(
                f"    player {action:6s} agreed {rate.numerator:5d} of {rate.denominator:5d}"
                f"  ({rate.percent:.1f}%)"
            )
        lines.append("")
    lines.append("  Where those diverge, the low one is the finding. A chart that matches on")
    lines.append("  folds and misses on calls is not 'mostly right'; it is right about the")
    lines.append("  decisions that cost nothing and unproven about the ones that cost chips.")
    lines.append("")
    lines.append("## Which seat the disagreement is in")
    lines.append("")
    lines.append("  A preflop chart is indexed by position before anything else, so a rate")
    lines.append("  without one names a symptom rather than a cell. Each entry below is")
    lines.append("  agreed/scored for that seat, and the last column is how many of that")
    lines.append("  seat's decision points the chart could not answer at all.")
    lines.append("")
    lines.append("  Refusals are outside every rate here, as they are everywhere in this")
    lines.append("  report. They are printed alongside because they are not spread evenly: a")
    lines.append("  seat that both refuses often and agrees poorly is being graded on the")
    lines.append("  questions it chose to answer, and its rate reads better than it deserves.")
    lines.append("")
    for population in result.populations:
        lines.append(f"  {population}")
        header = "    seat" + "".join(f"{action:>12s}" for action in REPORTED_ACTIONS)
        lines.append(header + f"{'refused':>14s}")
        for position in REPORTED_POSITIONS:
            cells = [
                _cell(result.agreement_within(population, action=action, position=position))
                for action in REPORTED_ACTIONS
            ]
            refused = result.refusal_count(population, position=position)
            points = result.decision_count(population, position=position)
            lines.append(
                f"    {position:<4s}"
                + "".join(f"{cell:>12s}" for cell in cells)
                + f"{f'{refused}/{points}':>14s}"
            )
        lines.append("")
    lines.append("## What a disagreement looked like")
    lines.append("")
    disagreements = [row for row in result.rows if row.verdict == DISAGREE]
    for row in disagreements[:20]:
        vector = ",".join(f"{name}={weight:g}" for name, weight in row.weights)
        lines.append(
            f"  {row.hand_id}  {row.position:<4s} {row.player}"
            f"  {row.hole_cards[0]}{row.hole_cards[1]}"
            f"  played {row.observed_action}  chart [{vector}]"
        )
    if len(disagreements) > 20:
        lines.append(f"  ... and {len(disagreements) - 20} more")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_refusal_inventory(result: ComparisonResult) -> str:
    lines = [
        "Real-Hand Refusal Inventory",
        "===========================",
        "",
        "Every spot below is one the committed charts could not answer while replaying",
        "real hands. Each row names a spot key taken from the refusal's own detail, the",
        "number of decision points that reached it, and whether the self-play run had",
        "already found it. Most-reached first.",
        "",
        "A spot marked new is one only real hands reached, which is a different priority",
        "from one the simulator already surfaces on every run.",
        "",
        "This is a lower bound on the gap, not a census of the charts: it reports only the",
        "spots this committed sample actually reached.",
        "",
        f"  distinct spots  {len(result.refusal_inventory)}",
        "",
        "   points  spot key                                      also in self-play",
    ]
    for entry in result.refusal_inventory:
        marker = "yes" if entry.seen_in_self_play else "NEW"
        lines.append(f"  {entry.count:6d}  {entry.spot_key:<44s}  {marker}")
    return "\n".join(lines) + "\n"
