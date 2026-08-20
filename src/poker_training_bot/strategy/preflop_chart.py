"""A preflop strategy that answers only from committed charts.

The whole design is a refusal machine with a chart bolted on. Every step below can
say "no", and none of them can say "probably": an uncovered spot, an unfamiliar
blind structure, a stack depth no artifact holds, a hand class the chart omits, a
weight tie, or a missing raise size each produce an explicit refusal carrying the
code of whatever was actually absent. That is the point. A training bot that
guesses in the spots it was not given is worse than one that admits the gap,
because the guesses are indistinguishable from the knowledge.

The one derivation that matters is the spot key, and it is derived rather than
spelled: game state gives table size, stack depth, hero's position from the button,
and the action sequence in front of hero, and `schema.spot_key` turns those into the
same string the importer stamped on the artifact. That shared function is what makes
a spot that imports reachable from a real hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.solver_artifacts.hand_classes import hand_class
from poker_training_bot.solver_artifacts.lookup import (
    ChartHit,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import SIZE_QUANTUM, PreflopAction
from poker_training_bot.strategy.contract import (
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

ARTIFACT_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "artifacts" / "preflop"
)

CODE_PREFIX = "preflop-chart"
REFUSE_NOT_PREFLOP = f"{CODE_PREFIX}:not-preflop"
REFUSE_BLIND_STRUCTURE = f"{CODE_PREFIX}:blind-structure-not-representable"
REFUSE_RAGGED_DEPTH = f"{CODE_PREFIX}:stack-depth-not-a-whole-big-blind"
REFUSE_UNEVEN_TABLE = f"{CODE_PREFIX}:table-is-not-one-flat-stack-depth"
REFUSE_ILLEGAL = f"{CODE_PREFIX}:charted-action-not-legal-here"
REFUSE_NO_SIZING = f"{CODE_PREFIX}:no-committed-raise-size"
REFUSE_SIZE_BELOW_MINIMUM = f"{CODE_PREFIX}:committed-size-below-minimum-raise"
REFUSE_UNREPRESENTABLE_PRICE = f"{CODE_PREFIX}:raise-price-not-a-whole-hundredth-of-a-big-blind"

# Only voluntary actions describe a spot. A fold adds no information beyond the
# folder's absence, and preflop the big blind's check ends the round rather than
# posing a spot, so both drop out on the way to a chart key.
_SPOT_ACTIONS = frozenset({"call", "raise"})


def _size_bb(amount: int | None, big_blind: int) -> float | None:
    """A raise-to in chips as a raise-to in big blinds, or None if it is not exact.

    Exact arithmetic rather than float division, so the answer depends on the numbers
    and not on how a binary fraction happened to land. At the 50/100 blinds of every
    committed sample and every simulator profile this is always exact; a game whose
    blind level makes it inexact refuses, which is the fail-closed direction.
    """
    if amount is None or big_blind <= 0:
        return None
    value = Decimal(amount) / Decimal(big_blind)
    quantized = value.quantize(SIZE_QUANTUM)
    if quantized != value:
        return None
    return float(quantized)


def _roll(seed: str) -> float:
    """A uniform draw in [0, 1) that depends only on `seed`.

    Hashing rather than a random module keeps the draw stable across processes and
    Python versions, which is what makes a decision audit replayable.
    """
    digest = sha256(seed.encode("utf-8")).digest()[:8]
    return int.from_bytes(digest, "big") / 2**64


@dataclass(frozen=True)
class PreflopChartStrategy:
    """Chart-backed preflop play, fail-closed everywhere the chart is silent."""

    library: PreflopChartLibrary
    sizing: PreflopSizingTable
    strategy_id: str = "preflop-chart"
    strategy_version: int = 1

    @classmethod
    def from_repo(cls) -> PreflopChartStrategy:
        return cls(
            library=PreflopChartLibrary.from_directory(ARTIFACT_DIR),
            sizing=PreflopSizingTable.from_repo(),
        )

    # -- collapse ---------------------------------------------------------- #

    def collapse(self, weights: tuple[tuple[str, float], ...], seed: str = "") -> str | None:
        """Draw one action from a mixed strategy, in proportion to its weights.

        Not the highest weight. Folding is a single bucket while continuing splits
        across calling and raising, so a plurality rule folds hands the chart
        continues with more than half the time, and only ever in that direction. It
        measured 13 points of extra folding against three-bets, which is past the
        price at which a pure bluff auto-profits.

        The draw is deterministic in its seed, so a hand decides the same way on
        every run and a replay is a replay. Weights come in the artifact's fixed
        action order, so the cumulative walk below is stable.
        """
        positive = [(action, weight) for action, weight in weights if weight > 0.0]
        if not positive:
            return None
        if len(positive) == 1:
            return positive[0][0]
        roll = _roll(seed) * sum(weight for _, weight in positive)
        cumulative = 0.0
        for action, weight in positive:
            cumulative += weight
            if roll < cumulative:
                return action
        return positive[-1][0]

    def _rationale(self, action: str, weights: tuple[tuple[str, float], ...]) -> str:
        vector = ",".join(f"{name}={weight:g}" for name, weight in weights)
        return f"{CODE_PREFIX}:weighted-draw:{action}[{vector}]"

    def _seed(self, query: StrategyQuery, spot_key_text: str, hand_class_text: str) -> str:
        """What the draw is a function of.

        The hand is in it, because a seed of spot and hand class alone would freeze
        every mixed cell to one action forever, which is the plurality rule wearing
        a hash. The raw cards are not, because two queries that canonicalize to the
        same hand class have to draw the same action.
        """
        return f"{query.hand_id}|{query.seat}|{spot_key_text}|{hand_class_text}"

    # -- spot derivation --------------------------------------------------- #

    def _blind_structure_is_representable(self, query: StrategyQuery) -> bool:
        """Reject a pot the artifact format cannot describe.

        The format declares two blinds and nothing else, so a straddle or an ante
        reads as an ordinary pot while changing the correct ranges. The test is
        arithmetic rather than positional: work out the largest pot the blinds and
        the recorded voluntary actions could possibly have built, and refuse
        anything bigger, because the excess is money the format cannot name.

        Nobody can have put in more than the current bet, so the bound is the two
        blinds plus one full bet for each voluntary action. It is deliberately
        generous, which makes a false refusal unlikely and leaves the check working
        at every seat rather than only at the first one to act. An earlier version
        only looked at hero's first decision and so accepted a straddled pot from
        the moment anyone raised, which in a straddled game is always.
        """
        small_blind, big_blind = query.blinds
        raised = any(entry.action == "raise" for entry in query.preflop_actions)
        if not raised and query.street_bet != big_blind:
            return False
        voluntary = sum(
            1 for entry in query.preflop_actions if entry.action in _SPOT_ACTIONS
        )
        largest_explainable = small_blind + big_blind + voluntary * query.street_bet
        return query.pot <= largest_explainable

    def _table_depth_bb(self, query: StrategyQuery) -> tuple[int | None, str | None]:
        """Hero's starting depth in big blinds, or None when it is not usable.

        Measured from hero, not from the deepest seat. Hero's own contribution is
        exact - what hero owes plus what hero has left is what hero started with -
        so this is the one depth in the query that can be derived rather than
        guessed. An earlier version took the largest stack at the table, which meant
        a twelve-big-blind hero opened a hundred-big-blind range as long as one
        untouched seat sat behind, an unbounded tolerance band on a decision ruled
        exact-only.

        A seat holding more than hero started with cannot happen if everyone bought
        in the same, so it means the table is not the flat structure the artifact
        describes and the answer is a refusal with its own code, because "your table
        is not flat" and "your depth is ragged" are different problems.

        A seat holding *less* than hero is invisible here: a short villain and a
        villain who has already put money in look identical from a query that
        carries no per-seat contributions. That gap is `ASYMMETRIC-EFFECTIVE-STACKS`.
        """
        _, big_blind = query.blinds
        stacks = dict(query.stacks)
        hero_start = stacks[query.seat] + (query.street_bet - query.to_call)
        if hero_start <= 0 or hero_start % big_blind:
            return None, REFUSE_RAGGED_DEPTH
        if any(stack > hero_start for stack in stacks.values()):
            return None, REFUSE_UNEVEN_TABLE
        return hero_start // big_blind, None

    def _action_sequence(self, query: StrategyQuery) -> tuple[PreflopAction, ...] | None:
        """The sized action sequence in front of hero, or None if a price will not fit.

        A raise-to in chips becomes a raise-to in big blinds, which is the unit the key
        is written in because chips do not survive a change of blind level. The
        division is exact or it is refused: rounding a price into the neighbouring
        hundredth would put a decision in a cell it was not asked about, and it is the
        same reason `render_size_bb` rejects rather than rounds.
        """
        seats = tuple(seat for seat, _ in query.stacks)
        _, big_blind = query.blinds
        entries: list[PreflopAction] = []
        for entry in query.preflop_actions:
            if entry.action not in _SPOT_ACTIONS:
                continue
            position = position_for_seat(seats, query.button_seat, entry.seat)
            if entry.action != "raise":
                entries.append(PreflopAction(position, entry.action))
                continue
            size_bb = _size_bb(entry.amount, big_blind)
            if size_bb is None:
                return None
            entries.append(PreflopAction(position, "raise", size_bb))
        return tuple(entries)

    def _chart_query(self, query: StrategyQuery, depth_bb: int) -> ChartQuery | None:
        sequence = self._action_sequence(query)
        if sequence is None:
            return None
        seats = tuple(seat for seat, _ in query.stacks)
        return ChartQuery(
            table_size=len(query.stacks),
            stack_depth_bb=depth_bb,
            hero_position=position_for_seat(seats, query.button_seat, query.seat),
            action_sequence=sequence,
            hand_class=hand_class(query.hole_cards),
        )

    # -- amounts ----------------------------------------------------------- #

    def _raise_amount(
        self, query: StrategyQuery, spot_key_text: str
    ) -> tuple[int | None, str | None]:
        """Chips to raise to, or a refusal code explaining why there are none."""
        _, big_blind = query.blinds
        amount_bb = self.sizing.amount_bb(spot_key_text)
        if amount_bb is None:
            return None, REFUSE_NO_SIZING
        stacks = dict(query.stacks)
        all_in_target = query.street_bet + stacks[query.seat]
        # Capping at all-in is not a guess: you cannot raise to more than you have,
        # and the decision audit rejects an amount above it.
        amount = min(round(amount_bb * big_blind), all_in_target)
        if amount < query.min_raise_target and amount < all_in_target:
            return None, REFUSE_SIZE_BELOW_MINIMUM
        return amount, None

    @staticmethod
    def _miss_detail(chart_query: ChartQuery, found: ChartMiss) -> tuple[tuple[str, str], ...]:
        """What the chart was asked for, so a refusal names a cell somebody can fill.

        The spot key is the one the lookup itself used, carried out on the miss rather
        than re-derived here. Re-deriving would give the repo two answers to "what spot
        is this" that could drift, and the drift would be invisible in the worst
        direction: since phase 12 the lookup asks about a normalised price, so a refusal
        re-deriving the key would send somebody to fill a cell the lookup never asked
        about.

        The key is absent when the position and action sequence do not describe a spot
        the vocabulary can express at all - a different miss from a spot that is
        expressible and uncovered - so it is reported only when it exists, and its
        absence is itself the information.
        """
        detail: list[tuple[str, str]] = [
            ("table_size", str(chart_query.table_size)),
            ("stack_depth_bb", str(chart_query.stack_depth_bb)),
            ("hand_class", chart_query.hand_class),
        ]
        if found.spot_key is not None:
            detail.insert(0, ("spot_key", found.spot_key))
        return tuple(detail)

    # -- entry points ------------------------------------------------------ #

    def decide(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        if query.street != "preflop":
            return StrategyRefusal(REFUSE_NOT_PREFLOP)
        if not self._blind_structure_is_representable(query):
            return StrategyRefusal(REFUSE_BLIND_STRUCTURE)
        depth_bb, depth_refusal = self._table_depth_bb(query)
        if depth_bb is None:
            return StrategyRefusal(depth_refusal or REFUSE_RAGGED_DEPTH)

        chart_query = self._chart_query(query, depth_bb)
        if chart_query is None:
            return StrategyRefusal(REFUSE_UNREPRESENTABLE_PRICE)
        found = self.library.lookup(chart_query)
        if not isinstance(found, ChartHit):
            return StrategyRefusal(
                f"{CODE_PREFIX}:{found.code}", self._miss_detail(chart_query, found)
            )

        seed = self._seed(query, found.spot_key, found.hand_class)
        action = self.collapse(found.action_weights, seed)
        if action is None:
            return StrategyRefusal(f"{CODE_PREFIX}:no-positive-weight")
        if action not in query.legal_actions:
            return StrategyRefusal(REFUSE_ILLEGAL)
        # Every answer produced through a substituted price says so on the answer, so a
        # substituted decision and an exact one stay distinguishable downstream. An
        # exact answer carries nothing, which is what makes the field's absence a fact
        # rather than a default.
        detail = found.substitution_detail()
        if action != "raise":
            return StrategyDecision(
                action, None, self._rationale(action, found.action_weights), detail
            )

        amount, refusal_code = self._raise_amount(query, found.spot_key)
        if amount is None:
            return StrategyRefusal(refusal_code or REFUSE_NO_SIZING)
        return StrategyDecision(
            "raise", amount, self._rationale("raise", found.action_weights), detail
        )

    def weights_for(
        self, query: StrategyQuery
    ) -> tuple[tuple[str, float], ...] | StrategyRefusal:
        """The chart's own action weights for a query, before any collapse.

        Read-only and additive. It exists because "did this player's action agree
        with the chart" is a question about the distribution, not about the single
        action `decide` draws from it: a chart that raises three times in ten does
        not disagree with a fold, and scoring a mixed cell action-for-action makes a
        correct chart look wrong in proportion to how mixed it is.

        The alternative was parsing the weight vector back out of the rationale
        string `decide` returns, or rebuilding the chart query somewhere else. The
        first couples a caller to a private format; the second gives the repo two
        derivations of "what spot is this" that can drift apart invisibly. Sharing
        `_chart_query` keeps exactly one.
        """
        if query.street != "preflop":
            return StrategyRefusal(REFUSE_NOT_PREFLOP)
        if not self._blind_structure_is_representable(query):
            return StrategyRefusal(REFUSE_BLIND_STRUCTURE)
        depth_bb, depth_refusal = self._table_depth_bb(query)
        if depth_bb is None:
            return StrategyRefusal(depth_refusal or REFUSE_RAGGED_DEPTH)
        chart_query = self._chart_query(query, depth_bb)
        if chart_query is None:
            return StrategyRefusal(REFUSE_UNREPRESENTABLE_PRICE)
        found = self.library.lookup(chart_query)
        if not isinstance(found, ChartHit):
            return StrategyRefusal(
                f"{CODE_PREFIX}:{found.code}", self._miss_detail(chart_query, found)
            )
        return found.action_weights

    def chart_lookup(self, query: StrategyQuery) -> ChartHit | ChartMiss | None:
        """The raw lookup outcome for a query, or None if it never reached the chart.

        Read-only and additive, and it exists for the same reason `weights_for` does.
        The substitution census asks what the *lookup* did - which key it asked about
        and which prices it moved to get there - and that is a different question from
        what `decide` drew out of the answer. The alternative is parsing the numbers
        back out of a decision's detail strings, which couples a caller to a format,
        or rebuilding the chart query somewhere else, which gives the repo two
        derivations of "what spot is this" that can drift apart invisibly.

        None means the query was refused before a chart was consulted at all: not
        preflop, a pot the format cannot describe, a depth that is not whole. Those
        have no key and no substitutions because no lookup happened.
        """
        if query.street != "preflop":
            return None
        if not self._blind_structure_is_representable(query):
            return None
        depth_bb, _ = self._table_depth_bb(query)
        if depth_bb is None:
            return None
        chart_query = self._chart_query(query, depth_bb)
        if chart_query is None:
            return None
        return self.library.lookup(chart_query)

    def decide_spot(
        self, spot_key_text: str, hand_class_text: str, seed_suffix: str = ""
    ) -> StrategyDecision | StrategyRefusal:
        """Decide from a chart key directly, with no chips and no legality.

        Coverage and legality are different questions, and mixing them hides both.
        This answers "does the chart resolve here", which is what an enumeration over
        every committed spot is actually asking; `decide` answers "is that action
        legal in this hand", which needs a real query.
        """
        artifact = None
        for candidate in self.library.artifacts:
            if spot_key_text in {spot.spot_id for spot in candidate.spots}:
                artifact = candidate
                break
        if artifact is None:
            return StrategyRefusal(f"{CODE_PREFIX}:spot-not-covered")
        weights = artifact.weights_for(spot_key_text, hand_class_text)
        if weights is None:
            return StrategyRefusal(f"{CODE_PREFIX}:hand-class-not-covered")
        action = self.collapse(weights, f"spot|{spot_key_text}|{hand_class_text}|{seed_suffix}")
        if action is None:
            return StrategyRefusal(f"{CODE_PREFIX}:no-positive-weight")
        code = self._rationale(action, weights)
        if action != "raise":
            return StrategyDecision(action, None, code)
        amount_bb = self.sizing.amount_bb(spot_key_text)
        if amount_bb is None:
            return StrategyRefusal(REFUSE_NO_SIZING)
        return StrategyDecision("raise", max(round(amount_bb * 100), 1), code)
