"""A preflop strategy that answers only from committed charts.

The whole design is a refusal machine with a chart bolted on. Every step below can
say "no", and none of them can say "probably": an uncovered spot, a straddle, an ante,
a table that is not one flat depth, a stack depth no artifact holds, a hand class the
chart omits, a weight tie, or a missing raise size each produce an explicit refusal
naming what was absent. A training bot that guesses in the spots it was not given is
worse than one that admits the gap, because the guesses are indistinguishable from
the knowledge.

The one derivation that matters is the spot key, and it is derived rather than spelled:
game state gives table size, stack depth, hero's position from the button and the action
sequence in front of hero, and `schema.spot_key` turns those into the same string the
importer stamped on the artifact. That shared function is what makes a spot that imports
reachable from a real hand.
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
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.strategy.contract import (
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_price import draw_price_bb, size_bb
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable
from poker_training_bot.table_state.forced_money import (
    predicted_min_raise_target,
    unexplained_contributions,
)

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "data" / "artifacts" / "preflop"

CODE_PREFIX = "preflop-chart"
REFUSE_NOT_PREFLOP = f"{CODE_PREFIX}:not-preflop"
# The residual, not a retirement: forced money the three signals cannot classify as a
# straddle or an ante, which is a dead blind and whatever else nobody has named yet.
REFUSE_BLIND_STRUCTURE = f"{CODE_PREFIX}:blind-structure-not-representable"
REFUSE_STRADDLE = f"{CODE_PREFIX}:pot-holds-a-straddle"
REFUSE_ANTE = f"{CODE_PREFIX}:pot-holds-an-ante"
REFUSE_RAGGED_DEPTH = f"{CODE_PREFIX}:stack-depth-not-a-whole-big-blind"
REFUSE_UNEVEN_TABLE = f"{CODE_PREFIX}:table-is-not-one-flat-stack-depth"
REFUSE_SHORT_LIVE_SEAT = f"{CODE_PREFIX}:a-live-seat-is-shorter-than-hero"
REFUSE_ILLEGAL = f"{CODE_PREFIX}:charted-action-not-legal-here"
REFUSE_NO_SIZING = f"{CODE_PREFIX}:no-committed-raise-size"
REFUSE_SIZE_BELOW_MINIMUM = f"{CODE_PREFIX}:committed-size-below-minimum-raise"
REFUSE_UNREPRESENTABLE_PRICE = f"{CODE_PREFIX}:raise-price-not-a-whole-hundredth-of-a-big-blind"

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

        Not the highest weight. Folding is a single bucket while continuing splits across
        calling and raising, so a plurality rule folds hands the chart continues with more
        than half the time, and only ever in that direction. It measured 13 points of extra
        folding against three-bets, past the price at which a pure bluff auto-profits.

        The draw is deterministic in its seed, so a hand decides the same way on every run
        and a replay is a replay. Weights come in the artifact's fixed action order, so the
        cumulative walk below is stable.
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

        The hand is in it, because a seed of spot and hand class alone would freeze every
        mixed cell to one action forever, which is the plurality rule wearing a hash. The raw
        cards are not, because two queries that canonicalize to one hand class must draw alike.
        """
        return f"{query.hand_id}|{query.seat}|{spot_key_text}|{hand_class_text}"

    # -- spot derivation --------------------------------------------------- #

    def _forced_money_refusal(self, query: StrategyQuery) -> StrategyRefusal | None:
        """Name the forced money in the pot, or None if the declared blinds explain it all.

        The format declares two blinds and nothing else, so a straddle or an ante reads as an
        ordinary pot while changing the correct ranges. Three signals, none subsuming another,
        replacing a pot bound that was generous by construction. The two straddle signals fire
        before unexplained money is classified, because a straddler's own chips are unexplained
        too and classifying first would file a straddled pot under the residual code.

        1. An unraised pot whose level is not the big blind is straddled: what moved the level
           is forced money collecting a price, which an ante does not.
        2. After a raise, the minimum the table offers disagrees with the one the declared
           blinds and the recorded raise-to amounts predict, by the straddle less the big
           blind. The only signal that sees a straddler who has already called to the level,
           since that seat holds exactly what an ordinary caller holds.
        3. What is left holding more than reconstruction predicts. Uniform across every seat
           is an ante - dead money buying nothing off the price, so it shows as the gap between
           a seat's hand figure and its street figure - and anything else keeps the residual.

        **The residual is written out in `table_state.forced_money`, and it is larger than a
        big-blind-sized straddle.** Signal 2 can only fire on a pot with one recorded raise, so
        a straddled pot with two of them reaches the chart and is answered with the unstraddled
        range for that spot: `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`.
        """
        _, big_blind = query.blinds
        # None means nothing has raised, so the level itself is the only straddle it can show.
        predicted_min_raise = predicted_min_raise_target(big_blind, query.preflop_actions)
        if predicted_min_raise is None:
            if query.current_bet != big_blind:
                return StrategyRefusal(
                    REFUSE_STRADDLE,
                    (("bet_level", str(query.current_bet)), ("big_blind", str(big_blind))),
                )
        else:
            if query.min_raise_target != predicted_min_raise:
                return StrategyRefusal(
                    REFUSE_STRADDLE,
                    (
                        ("min_raise_target", str(query.min_raise_target)),
                        ("predicted_min_raise", str(predicted_min_raise)),
                    ),
                )
        forced = unexplained_contributions(
            tuple(seat for seat, _ in query.stacks),
            query.button_seat,
            query.blinds,
            query.preflop_actions,
            {state.seat: state.committed_total for state in query.seat_states},
        )
        if not forced:
            return None
        amounts = set(forced.values())
        if len(forced) == len(query.seat_states) and len(amounts) == 1:
            return StrategyRefusal(REFUSE_ANTE, (("ante", str(amounts.pop())),))
        # Most chips, ties to the lowest chair: a figure the seating decides is not evidence.
        seat, chips = max(forced.items(), key=lambda pair: (pair[1], -pair[0]))
        return StrategyRefusal(
            REFUSE_BLIND_STRUCTURE, (("seat", str(seat)), ("forced_chips", str(chips)))
        )

    def _depth_refusal(
        self, code: str, seat: int, starting: int, big_blind: int
    ) -> StrategyRefusal:
        """A depth refusal that says which seat was off and by how much.

        In `_miss_detail`'s vocabulary - `seat` and `stack_depth_bb`, both strings, with
        `starting_chips` beside them in the game's own units. A count of refusals is not a work
        list, and whoever re-rules decision 6 once real table state arrives needs the seat and
        the depth it holds, which cannot be backfilled. All three depth codes carry it, the
        ragged one included: that one fires first and so swallows the majority of live tables,
        and the commonest case is the one a re-ruling can least afford to have no data for.
        There the depth is by definition not a whole number of big blinds - that is the content
        of the refusal - so it is rendered exactly rather than rounded into a whole one.
        """
        depth = format((Decimal(starting) / Decimal(big_blind)).normalize(), "f")
        return StrategyRefusal(
            code,
            (("seat", str(seat)), ("starting_chips", str(starting)), ("stack_depth_bb", depth)),
        )

    def _table_depth_bb(self, query: StrategyQuery) -> tuple[int | None, StrategyRefusal | None]:
        """Hero's starting depth in big blinds, or the refusal naming why there is none.

        Measured from hero, not from the deepest seat: reading the largest stack let a
        twelve-big-blind hero open a hundred-big-blind range whenever one untouched seat sat
        behind - an unbounded tolerance band on a decision ruled exact-only.

        Hero's own contribution is *read* off `seat_states` rather than recovered as
        `current_bet - to_call`. That subtraction was exact until `to_call` was capped at what
        hero can actually pay, and it is now wrong for exactly the capped population: a hero who
        put 100 into a level of 300 out of a 150 stack started with 250, where the subtraction
        says 300. Hero's street figure rather than its hand figure, because the two differ only
        by dead money, which preflop is forced money the check above has already refused.

        Every other seat's starting stack is recomputed the same way, so a short villain and an
        already-invested villain stop being the same picture: the cutoff three-betting to 8bb out
        of 100 holds 92 and is not short. Both directions refuse, each with its own code, because
        "somebody is deep" and "somebody is short" are different tables. Only live seats are
        compared: effective stack is pairwise and against seats that can still act, so a folded
        40bb seat cannot change a chip of hero's decision.

        The order is decision 7 - hero's raggedness, then a deeper live seat, then a shallower one
        - because a hero with no whole depth has nothing for the others to be measured against.
        First match wins, so at a ragged table hero's own raggedness masks every shape behind it
        and the inventory under-counts asymmetric tables in the games where they are commonest.

        Which branch fires is decision 7's; which seat that branch NAMES is poker. The shallower
        branch names the SHORTEST live seat, because that stack caps hero's effective one and is
        why a hundred-big-blind chart is wrong here: against 90bb it is still 100bb poker,
        against 20bb it is a different game. The deeper branch names the deepest, read the other
        way. Ties go to the lowest seat, so the answer stays deterministic. Naming the first
        offender in seat order made the reported depth depend on the seating instead: the same
        two stacks in swapped chairs reported 90bb and 20bb.
        """
        _, big_blind = query.blinds
        stacks = dict(query.stacks)
        hero = next(state for state in query.seat_states if state.seat == query.seat)
        hero_start = stacks[query.seat] + hero.street_bet
        if hero_start <= 0 or hero_start % big_blind:
            return None, self._depth_refusal(REFUSE_RAGGED_DEPTH, query.seat, hero_start, big_blind)
        live: list[tuple[int, int]] = []
        for state in query.seat_states:
            if state.folded:
                continue
            live.append((stacks[state.seat] + state.committed_total, state.seat))
        # Starting stack first in the pair, so the lowest seat breaks a tie in both
        # directions: plain tuple order gives it going down, and a negated seat going up.
        deep = max(live, default=None, key=lambda pair: (pair[0], -pair[1]))
        short = min(live, default=None)
        if deep is not None and deep[0] > hero_start:
            return None, self._depth_refusal(REFUSE_UNEVEN_TABLE, deep[1], deep[0], big_blind)
        if short is not None and short[0] < hero_start:
            return None, self._depth_refusal(REFUSE_SHORT_LIVE_SEAT, short[1], short[0], big_blind)
        return hero_start // big_blind, None

    def _action_sequence(self, query: StrategyQuery) -> tuple[PreflopAction, ...] | None:
        """The sized action sequence in front of hero, or None if a price will not fit.

        A raise-to in chips becomes a raise-to in big blinds, which is the unit the key is
        written in because chips do not survive a change of blind level. The division is
        exact or it is refused: rounding a price into the neighbouring hundredth would put a
        decision in a cell it was not asked about, which is why `render_size_bb` rejects too.
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
            price_bb = size_bb(entry.amount, big_blind)
            if price_bb is None:
                return None
            entries.append(PreflopAction(position, "raise", price_bb))
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
        self, query: StrategyQuery, spot_key_text: str, hand_class_text: str
    ) -> tuple[int | None, str | None]:
        """Chips to raise to, or a refusal code explaining why there are none.

        The price is asked for per hand class, ruled 2026-08-26: a spot offers the class its
        own prices with its own weights, and at `t6/d100/BB/BTN:raise@2.5` that is the whole
        difference between a strategy and a caricature - aces three-bet to 7.5 there and never
        shove, 44 shoves nearly nine times in ten, and one price per spot plays both of them
        the same way. `draw_price_bb` picks among them with this decision's own seed, so the
        price is drawn by the mechanism that drew the action rather than chosen by a rule.
        """
        _, big_blind = query.blinds
        offered = self.sizing.sizes_bb(spot_key_text, hand_class_text)
        seed = self._seed(query, spot_key_text, hand_class_text)
        amount_bb = draw_price_bb(offered, seed, self.collapse)
        if amount_bb is None:
            return None, REFUSE_NO_SIZING
        stacks = dict(query.stacks)
        hero = next(state for state in query.seat_states if state.seat == query.seat)
        all_in_target = hero.street_bet + stacks[query.seat]
        # Capping at all-in is not a guess: you cannot raise to more than you have. Hero's own
        # contribution rather than the street's level - the same number for a hero who has not
        # acted, too high by `to_call` for one who has, which the audit refuses to record.
        amount = min(round(amount_bb * big_blind), all_in_target)
        if amount < query.min_raise_target and amount < all_in_target:
            return None, REFUSE_SIZE_BELOW_MINIMUM
        return amount, None

    @staticmethod
    def _miss_detail(chart_query: ChartQuery, found: ChartMiss) -> tuple[tuple[str, str], ...]:
        """What the chart was asked for, so a refusal names a cell somebody can fill.

        The spot key is the one the lookup itself used, carried out on the miss rather than
        re-derived here. Re-deriving would give the repo two answers to "what spot is this",
        and the drift would be invisible in the worst direction: since phase 12 the lookup
        asks about a normalised price, so a refusal re-deriving the key would send somebody
        to fill a cell the lookup never asked about.

        The key is absent when the position and action sequence do not describe a spot the
        vocabulary can express at all - a different miss from a spot that is expressible and
        uncovered - so it is reported only when it exists, and its absence is the information.
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
        forced_money = self._forced_money_refusal(query)
        if forced_money is not None:
            return forced_money
        depth_bb, depth_refusal = self._table_depth_bb(query)
        if depth_bb is None:
            return depth_refusal or StrategyRefusal(REFUSE_RAGGED_DEPTH)

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

        amount, refusal_code = self._raise_amount(query, found.spot_key, found.hand_class)
        if amount is None:
            return StrategyRefusal(refusal_code or REFUSE_NO_SIZING)
        return StrategyDecision(
            "raise", amount, self._rationale("raise", found.action_weights), detail
        )

    def weights_for(self, query: StrategyQuery) -> tuple[tuple[str, float], ...] | StrategyRefusal:
        """The chart's own action weights for a query, before any collapse.

        Read-only and additive. It exists because "did this player's action agree with the
        chart" is a question about the distribution, not about the single action `decide`
        draws from it: a chart that raises three times in ten does not disagree with a fold,
        and scoring a mixed cell action-for-action makes a correct chart look wrong in
        proportion to how mixed it is.

        The alternative was parsing the weight vector back out of the rationale string
        `decide` returns, or rebuilding the chart query somewhere else. The first couples a
        caller to a private format; the second gives the repo two derivations of "what spot
        is this" that can drift apart invisibly. Sharing `_chart_query` keeps exactly one.
        """
        if query.street != "preflop":
            return StrategyRefusal(REFUSE_NOT_PREFLOP)
        forced_money = self._forced_money_refusal(query)
        if forced_money is not None:
            return forced_money
        depth_bb, depth_refusal = self._table_depth_bb(query)
        if depth_bb is None:
            return depth_refusal or StrategyRefusal(REFUSE_RAGGED_DEPTH)
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

        Read-only and additive, and it exists for the reason `weights_for` sets out against its
        own pair of alternatives, which are not the pair `weights_for` names: parsing the numbers
        back out of a decision's detail strings couples a caller to a private format, and
        rebuilding the chart query here gives the repo two derivations of "what spot is this"
        that can drift apart invisibly. The substitution census asks what the *lookup* did -
        which key it asked about and which prices it moved to get there - which is a different
        question from what `decide` drew out of the answer.

        None means the query was refused before a chart was consulted at all: not preflop, a
        pot the format cannot describe, a depth that is not whole. Those have no key and no
        substitutions because no lookup happened.
        """
        if query.street != "preflop":
            return None
        if self._forced_money_refusal(query) is not None:
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

        Coverage and legality are different questions and mixing them hides both. This answers
        "does the chart resolve here", which is what an enumeration over every committed spot
        asks; `decide` answers "is that action legal in this hand", which needs a real query.
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
        seed = f"spot|{spot_key_text}|{hand_class_text}|{seed_suffix}"
        action = self.collapse(weights, seed)
        if action is None:
            return StrategyRefusal(f"{CODE_PREFIX}:no-positive-weight")
        code = self._rationale(action, weights)
        if action != "raise":
            return StrategyDecision(action, None, code)
        offered = self.sizing.sizes_bb(spot_key_text, hand_class_text)
        amount_bb = draw_price_bb(offered, seed, self.collapse)
        if amount_bb is None:
            return StrategyRefusal(REFUSE_NO_SIZING)
        return StrategyDecision("raise", max(round(amount_bb * 100), 1), code)
