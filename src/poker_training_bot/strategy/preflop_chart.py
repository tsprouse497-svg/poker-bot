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
from hashlib import sha256
from pathlib import Path

from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.solver_artifacts.hand_classes import hand_class
from poker_training_bot.solver_artifacts.lookup import (
    ChartHit,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction
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

# Only voluntary actions describe a spot. A fold adds no information beyond the
# folder's absence, and preflop the big blind's check ends the round rather than
# posing a spot, so both drop out on the way to a chart key.
_SPOT_ACTIONS = frozenset({"call", "raise"})


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

    def _action_sequence(self, query: StrategyQuery) -> tuple[PreflopAction, ...]:
        seats = tuple(seat for seat, _ in query.stacks)
        return tuple(
            PreflopAction(position_for_seat(seats, query.button_seat, entry.seat), entry.action)
            for entry in query.preflop_actions
            if entry.action in _SPOT_ACTIONS
        )

    def _chart_query(self, query: StrategyQuery, depth_bb: int) -> ChartQuery:
        seats = tuple(seat for seat, _ in query.stacks)
        return ChartQuery(
            table_size=len(query.stacks),
            stack_depth_bb=depth_bb,
            hero_position=position_for_seat(seats, query.button_seat, query.seat),
            action_sequence=self._action_sequence(query),
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
    def _miss_detail(chart_query: ChartQuery) -> tuple[tuple[str, str], ...]:
        """What the chart was asked for, so a refusal names a cell somebody can fill.

        The spot key comes from `ChartQuery.spot_key`, which is the derivation Phase 04
        already shares between the importer and the lookup. Deriving it a second time here
        would give the repo two answers to "what spot is this" that could drift, and the
        drift would be invisible: the refusal would name a spot the lookup never asked
        about.

        `spot_key` is None when the position and action sequence do not describe a spot the
        vocabulary can express at all - a different miss from a spot that is expressible
        and uncovered - so it is reported only when it exists, and its absence is itself the
        information.
        """
        detail: list[tuple[str, str]] = [
            ("table_size", str(chart_query.table_size)),
            ("stack_depth_bb", str(chart_query.stack_depth_bb)),
            ("hand_class", chart_query.hand_class),
        ]
        spot_key = chart_query.spot_key
        if spot_key is not None:
            detail.insert(0, ("spot_key", spot_key))
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
        found = self.library.lookup(chart_query)
        if not isinstance(found, ChartHit):
            return StrategyRefusal(f"{CODE_PREFIX}:{found.code}", self._miss_detail(chart_query))

        seed = self._seed(query, found.spot_key, found.hand_class)
        action = self.collapse(found.action_weights, seed)
        if action is None:
            return StrategyRefusal(f"{CODE_PREFIX}:no-positive-weight")
        if action not in query.legal_actions:
            return StrategyRefusal(REFUSE_ILLEGAL)
        if action != "raise":
            return StrategyDecision(action, None, self._rationale(action, found.action_weights))

        amount, refusal_code = self._raise_amount(query, found.spot_key)
        if amount is None:
            return StrategyRefusal(refusal_code or REFUSE_NO_SIZING)
        return StrategyDecision("raise", amount, self._rationale("raise", found.action_weights))

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
