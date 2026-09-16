"""Flop play that can bet and raise, out of committed solved data, refusing everywhere else.

The sibling of `preflop_chart` rather than an extension of `postflop_fallback`. The fallback is a
continuity device that checks when checking is free and folds on the flop without asking; this
answers a flop out of a cell somebody solved, returns `bet` and `raise` with amounts, and refuses
by code wherever the committed data is silent. The fallback stays exactly as it is, because a
completed phase's behaviour is not this phase's to move.

**The seam decision 1 accepted, stated rather than discovered:** the bot bets a flop and then
refuses every turn. Turn and river carry their own codes, and a refusal is not an action - the
composite hands it back untouched and the simulator voids the hand, which is why the bot never
plays out a strategy it did not solve for.

**The committed mixture is played, not purified**, by the seeded weighted draw in `collapse`.

**The walk fails closed, coarsest gap first**, so a refusal names the first thing missing rather
than whichever branch ran last: the street, the number of live players, the depth, the preflop
line, the flop sizes, the board, the spot, then hero's own hand class. Nothing is substituted
onto a nearest value at any step - a preflop price is answered only inside decision 10's band and
a faced bet matched to the menu only inside decision 14's tolerance.

**No refusal detail names a seat or a chip count.** `refusal_inventory` groups on the code plus
the whole detail tuple, so a per-seat figure shatters the work list into one row per hand.
`REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL`.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.solver_artifacts.postflop_artifact import PostflopCell
from poker_training_bot.solver_artifacts.postflop_key import (
    PreflopLine,
    canonical_board,
    canonical_hole_cards,
    completed_preflop_line,
    postflop_spot_key,
    price_within_band,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.strategy.contract import (
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.postflop_committed import (
    SIZED_ACTIONS,
    CoveredLine,
    PostflopLibrary,
    flop_action_line,
    load_library,
)
from poker_training_bot.strategy.postflop_spot_queries import (
    an_indexed_but_unfetched_query,
    committed_spot_queries,
)
from poker_training_bot.strategy.preflop_price import size_bb
from poker_training_bot.strategy.river_pot_odds import (
    holding_counts,
    pot_odds_price,
    river_equity,
)

__all__ = [
    "REFUSAL_CODES",
    "REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED",
    "REFUSE_NO_CELL_FOR_THIS_SPOT",
    "PostflopBettingStrategy",
    "an_indexed_but_unfetched_query",
    "collapse",
    "committed_class_weights",
    "committed_spot_queries",
    "holding_counts",
    "pot_odds_price",
    "river_equity",
]

CODE_PREFIX = "postflop-betting"

REFUSE_NOT_POSTFLOP = f"{CODE_PREFIX}:not-postflop"
REFUSE_NO_TURN_SOLUTION = f"{CODE_PREFIX}:no-committed-turn-solution"
REFUSE_NO_RIVER_SOLUTION = f"{CODE_PREFIX}:no-committed-river-solution"
REFUSE_MORE_THAN_TWO_LIVE_PLAYERS = f"{CODE_PREFIX}:more-than-two-live-players"
REFUSE_RAGGED_DEPTH = f"{CODE_PREFIX}:effective-depth-not-a-whole-big-blind"
REFUSE_UNREPRESENTABLE_PRICE = f"{CODE_PREFIX}:preflop-price-not-a-whole-hundredth"
REFUSE_LINE_NOT_EXPRESSIBLE = f"{CODE_PREFIX}:preflop-line-not-a-completed-street"
REFUSE_NO_CELL_FOR_THIS_LINE = f"{CODE_PREFIX}:no-cell-for-this-preflop-line"
REFUSE_FLOP_SIZE_OFF_THE_MENU = f"{CODE_PREFIX}:flop-size-off-the-committed-menu"
REFUSE_NO_CELL_FOR_THIS_BOARD = f"{CODE_PREFIX}:no-cell-for-this-board"
REFUSE_NO_CELL_FOR_THIS_SPOT = f"{CODE_PREFIX}:no-cell-for-this-spot"
REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED = f"{CODE_PREFIX}:in-the-index-but-not-fetched"
REFUSE_HAND_CLASS_NOT_IN_THE_CELL = f"{CODE_PREFIX}:hand-class-not-in-the-cell"
REFUSE_NO_POSITIVE_WEIGHT = f"{CODE_PREFIX}:no-positive-weight"
REFUSE_ACTION_NOT_LEGAL_HERE = f"{CODE_PREFIX}:committed-action-not-legal-here"
REFUSE_SIZE_BELOW_MINIMUM = f"{CODE_PREFIX}:committed-size-below-minimum-raise"

CODE_POT_ODDS_CALL = f"{CODE_PREFIX}:pot-odds-river-call"

REFUSAL_CODES: tuple[str, ...] = (
    REFUSE_NOT_POSTFLOP,
    REFUSE_NO_TURN_SOLUTION,
    REFUSE_NO_RIVER_SOLUTION,
    REFUSE_MORE_THAN_TWO_LIVE_PLAYERS,
    REFUSE_RAGGED_DEPTH,
    REFUSE_UNREPRESENTABLE_PRICE,
    REFUSE_LINE_NOT_EXPRESSIBLE,
    REFUSE_NO_CELL_FOR_THIS_LINE,
    REFUSE_FLOP_SIZE_OFF_THE_MENU,
    REFUSE_NO_CELL_FOR_THIS_BOARD,
    REFUSE_NO_CELL_FOR_THIS_SPOT,
    REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED,
    REFUSE_HAND_CLASS_NOT_IN_THE_CELL,
    REFUSE_NO_POSITIVE_WEIGHT,
    REFUSE_ACTION_NOT_LEGAL_HERE,
    REFUSE_SIZE_BELOW_MINIMUM,
)
"""Every code this strategy can refuse under, listed once so a report counts a closed set. The
two **table** causes the contract keeps apart are coarser and group it: no cell for this board or
line - never-solved and solved-but-rejected together, because the query meets one absence either
way - and in the index but not fetched on this machine."""

_VOLUNTARY = frozenset({"call", "raise"})
_LIVE_SEATS = 2


# --------------------------------------------------------------------------- #
# The weighted draw
# --------------------------------------------------------------------------- #


def _roll(seed: str) -> float:
    """A uniform draw in [0, 1) that depends only on `seed`, hashed rather than generated so
    the answer is stable across processes and Python versions and an audit line replays."""
    return int.from_bytes(sha256(seed.encode("utf-8")).digest()[:8], "big") / 2**64


def collapse(weights: tuple[tuple[str, float], ...], seed: str = "") -> str | None:
    """Draw one action from a mixed cell, in proportion to its weights.

    **Not the highest weight.** A solver mixes where it has driven a hand to indifference, so an
    argmax makes every indifferent class pure: a class solved to bet 0.51 and check 0.49 bets
    every time, an opponent reads the frequency off in a single orbit, and the bet frequency a
    report then prints is the bot's rather than the artifact's with nothing saying which.

    The same mechanism as `PreflopChartStrategy.collapse`, written again rather than imported off
    a strategy that reads preflop artifacts; two copies of one rule is a finding for the
    coordinator rather than a licence for them to differ. Weights arrive in the cell's own fixed
    action order, so the cumulative walk is stable.
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


# --------------------------------------------------------------------------- #
# The strategy
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PostflopBettingStrategy:
    """A flop answered out of committed solved data, and a refusal everywhere else."""

    library: PostflopLibrary
    pot_odds_river_call: bool = False
    strategy_id: str = "postflop-betting"
    strategy_version: int = 1

    @classmethod
    def from_repo(cls, pot_odds_river_call: bool = False) -> PostflopBettingStrategy:
        """Build from committed data. The flag is explicit and off, decision 5: the pot-odds
        river call is a rule this repo evaluates rather than a solution it committed."""
        return cls(library=load_library(), pot_odds_river_call=pot_odds_river_call)

    # -- entry point ------------------------------------------------------- #

    def decide(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        """The street guard first, on the fallback's own reasoning: a preflop spot has either a
        chart answer or a chart gap, and letting this module answer one would give the repo a
        second preflop strategy reachable by mistake. Turn and river then carry their own codes.
        """
        if query.street == "preflop":
            return StrategyRefusal(REFUSE_NOT_POSTFLOP)
        if query.street == "turn":
            return StrategyRefusal(REFUSE_NO_TURN_SOLUTION)
        if query.street == "river":
            return self._river(query)
        return self._flop(query)

    def _river(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        if (
            self.pot_odds_river_call
            and query.to_call > 0
            and "call" in query.legal_actions
            and river_equity(query.hole_cards, query.board) > pot_odds_price(query)
        ):
            return StrategyDecision("call", None, CODE_POT_ODDS_CALL)
        return StrategyRefusal(REFUSE_NO_RIVER_SOLUTION)

    def _flop(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        live = [state for state in query.seat_states if not state.folded]
        if len(live) != _LIVE_SEATS:
            # Structural rather than fundable: a two-range solve cannot express a three-handed
            # flop at any budget, machine or menu, so this is not a gap a later campaign closes.
            return StrategyRefusal(
                REFUSE_MORE_THAN_TWO_LIVE_PLAYERS, (("live_players", str(len(live))),)
            )
        found = self._resolve(query)
        if isinstance(found, StrategyRefusal):
            return found
        return self._answer(query, found)

    # -- the walk ---------------------------------------------------------- #

    def _resolve(self, query: StrategyQuery) -> PostflopCell | StrategyRefusal:
        """Walk from the table down to one committed cell, refusing at the first gap."""
        board = "".join(canonical_board(query.board))
        depth_bb = self._effective_depth_bb(query)
        if depth_bb is None:
            return StrategyRefusal(REFUSE_RAGGED_DEPTH)
        actual = self._preflop_line(query)
        if actual is None:
            return StrategyRefusal(REFUSE_UNREPRESENTABLE_PRICE)
        seats = tuple(seat for seat, _ in query.stacks)
        hero_position = position_for_seat(seats, query.button_seat, query.seat)
        table_size = len(seats)
        try:
            asked = self._completed_line(query, table_size, depth_bb, hero_position, actual)
        except ValueError:
            return StrategyRefusal(REFUSE_LINE_NOT_EXPRESSIBLE)
        named = (("preflop_line", asked.rendered), ("board", board))
        line = self._covered_line(query, table_size, depth_bb, hero_position, actual)
        if line is None:
            return StrategyRefusal(REFUSE_NO_CELL_FOR_THIS_LINE, named)
        flop_line, miss = flop_action_line(query, self.library.raise_fractions)
        if flop_line is None:
            return StrategyRefusal(REFUSE_FLOP_SIZE_OFF_THE_MENU, miss)
        spot = postflop_spot_key(
            line.preflop_line, query.board, flop_line, line.pot_bb, line.effective_stack_bb
        )
        cell = self.library.cell_for(spot)
        if cell is not None:
            return cell
        detail = (("board", board), ("spot_key", spot))
        if spot in self.library.listed:
            return StrategyRefusal(REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED, detail)
        if canonical_board(query.board) not in line.boards:
            return StrategyRefusal(REFUSE_NO_CELL_FOR_THIS_BOARD, detail)
        return StrategyRefusal(REFUSE_NO_CELL_FOR_THIS_SPOT, detail)

    @staticmethod
    def _effective_depth_bb(query: StrategyQuery) -> int | None:
        """The effective starting depth in big blinds, or None when it is not a whole one.

        The **minimum** over live seats, because effective stack is pairwise and the shorter one
        caps the hand; a table where one seat sat down deeper is the same spot, which is why two
        such refusals group into one inventory row. Each seat's starting stack is its chips
        behind plus what it put in over the hand, read off `seat_states` - never
        `current_bet - to_call`, which has been wrong for exactly the capped population since
        `to_call` was capped at what hero can actually pay.
        """
        _, big_blind = query.blinds
        stacks = dict(query.stacks)
        starting = [
            stacks[state.seat] + state.committed_total
            for state in query.seat_states
            if not state.folded
        ]
        if not starting:
            return None
        depth = min(starting)
        if depth <= 0 or depth % big_blind:
            return None
        return depth // big_blind

    @staticmethod
    def _preflop_line(query: StrategyQuery) -> tuple[PreflopAction, ...] | None:
        """The **completed** preflop street as committed actions, or None on a price the key
        cannot say.

        Folds and the big blind's check drop out, which is `spot_key`'s own vocabulary, and a
        raise-to in chips becomes a raise-to in big blinds exactly or the line refuses.

        Nothing is dropped from the end. An earlier draft dropped whichever seat closed the
        betting, on the reading that a cell keys the line at the decision that ended it - and
        that reading is what left the preflop raiser with no expressible cell and the bot unable
        to continuation-bet at all. Decision 8's 2026-09-15 amendment: the key carries the
        completed line, hero's own closing call included, and hero's position in it is what
        makes the raiser's flop and the caller's flop two spots rather than one.
        """
        seats = tuple(seat for seat, _ in query.stacks)
        _, big_blind = query.blinds
        built: list[PreflopAction] = []
        for entry in query.preflop_actions:
            if entry.action not in _VOLUNTARY:
                continue
            position = position_for_seat(seats, query.button_seat, entry.seat)
            if entry.action != "raise":
                built.append(PreflopAction(position, entry.action))
                continue
            price = size_bb(entry.amount, big_blind)
            if price is None:
                return None
            built.append(PreflopAction(position, "raise", price))
        return tuple(built)

    @staticmethod
    def _completed_line(
        query: StrategyQuery,
        table_size: int,
        depth_bb: int,
        hero_position: str,
        actions: tuple[PreflopAction, ...],
    ) -> PreflopLine:
        """The table's own line as a closed preflop street, raising when it is not one.

        The blinds come off the query rather than being assumed, because what a seat posted is
        what decides whether the street closed: a small blind that never matched the level folded
        there, and its dead chips stay in the middle.
        """
        small, big = query.blinds
        return completed_preflop_line(
            table_size, depth_bb, hero_position, actions,
            small_blind_bb=small / big, big_blind_bb=1.0,
        )

    def _covered_line(
        self,
        query: StrategyQuery,
        table_size: int,
        depth_bb: int,
        hero_position: str,
        actual: tuple[PreflopAction, ...],
    ) -> CoveredLine | None:
        """The committed line this table's line substitutes onto, or None.

        Substitution is by **price only**, inside decision 10's band, and the match is confirmed
        by re-deriving the completed line from this table's own seats, depth and position against
        the covered cell's prices: if the rendering is the cell's own then table size, depth,
        hero's seat and every action agreed, and nothing was parsed out of a string to see it. A
        price outside the band falls through and the walk refuses rather than moving onto the
        nearest cell - deliberately the opposite of the preflop chart, because 0.25bb barely moves
        a preflop range and moves the pot, the SPR and both postflop ranges at once.
        """
        for line in self.library.lines:
            if len(line.preflop_actions) != len(actual):
                continue
            if any(
                got.position != want.position
                or got.action != want.action
                or (
                    want.action == "raise"
                    and not price_within_band(float(want.size_bb or 0.0), float(got.size_bb or 0.0))
                )
                for got, want in zip(actual, line.preflop_actions, strict=True)
            ):
                continue
            try:
                derived = self._completed_line(
                    query, table_size, depth_bb, hero_position, line.preflop_actions
                )
            except ValueError:
                continue
            if derived.rendered == line.preflop_line.rendered:
                return line
        return None

    # -- the answer -------------------------------------------------------- #

    def class_weights(self, query: StrategyQuery) -> tuple[tuple[str, float], ...]:
        """The cell's own strategy for this query's hand class, before any collapse.

        Read-only and additive, on `PreflopChartStrategy.weights_for`'s reasoning: "did this agree
        with the solve" asks about the distribution, not about the one action a draw produced.
        """
        found = self._resolve(query) if query.street == "flop" else None
        if not isinstance(found, PostflopCell):
            return ()
        row = found.weights_for("".join(canonical_hole_cards(query.board, query.hole_cards)))
        if row is None:
            return ()
        return tuple(zip(found.actions, row, strict=True))

    def _answer(
        self, query: StrategyQuery, cell: PostflopCell
    ) -> StrategyDecision | StrategyRefusal:
        """Draw hero's action out of the cell and price it, or refuse and say which.

        Hero's two cards are moved by the **board's own** suit map, the half a board-level
        isomorphism test cannot see: on a two-tone board `AhQh` holds the flush draw and `AsQd`
        does not, and a hand permuted inconsistently is served the other's strategy while every
        board-level check still passes.
        """
        hand = "".join(canonical_hole_cards(query.board, query.hole_cards))
        row = cell.weights_for(hand)
        if row is None:
            return StrategyRefusal(
                REFUSE_HAND_CLASS_NOT_IN_THE_CELL,
                (("spot_key", cell.spot_key), ("hand_class", hand)),
            )
        weights = tuple(zip(cell.actions, row, strict=True))
        seed = f"{query.hand_id}|{query.seat}|{cell.spot_key}|{hand}"
        action = collapse(weights, seed)
        if action is None:
            return StrategyRefusal(REFUSE_NO_POSITIVE_WEIGHT, (("spot_key", cell.spot_key),))
        if action not in query.legal_actions:
            return StrategyRefusal(REFUSE_ACTION_NOT_LEGAL_HERE, (("action", action),))
        # The vector travels on the answer, so a reader can see that two hands were played out
        # of two different strategies rather than out of one that happened to draw differently:
        # a pure cell and a mixed cell that drew alike are one action and two pieces of evidence.
        detail = (
            ("spot_key", cell.spot_key),
            ("class_weights", ",".join(f"{name}={weight:g}" for name, weight in weights)),
        )
        code = f"{CODE_PREFIX}:weighted-draw:{action}"
        if action not in SIZED_ACTIONS:
            return StrategyDecision(action, None, code, detail)
        amount, refusal = self._amount(query, cell, action)
        if amount is None:
            return StrategyRefusal(refusal or REFUSE_SIZE_BELOW_MINIMUM, detail[:1])
        return StrategyDecision(action, amount, code, detail)

    @staticmethod
    def _amount(
        query: StrategyQuery, cell: PostflopCell, action: str
    ) -> tuple[int | None, str | None]:
        """Chips to put the level at, or the code saying why there are none.

        The cell prices its sized actions in big blinds, one per sized action in its own order, so
        the size is the solve's own number rather than one recomputed from the pot here. Capping at
        all-in is not a guess - you cannot bet more than you hold - and hero's ceiling is hero's
        **own** street contribution plus the stack behind it, read off `seat_states`, the same
        ceiling `DecisionAuditRecord` proves the answer against.
        """
        _, big_blind = query.blinds
        sized = [name for name in cell.actions if name in SIZED_ACTIONS]
        size = cell.bet_sizes_bb[sized.index(action)]
        hero = next(state for state in query.seat_states if state.seat == query.seat)
        all_in = hero.street_bet + dict(query.stacks)[query.seat]
        amount = min(round(size * big_blind), all_in)
        if amount < query.min_raise_target and amount != all_in:
            return None, REFUSE_SIZE_BELOW_MINIMUM
        return amount, None


def committed_class_weights(query: StrategyQuery) -> tuple[tuple[str, float], ...]:
    """The committed strategy for one query's hand class, without building a strategy first."""
    return PostflopBettingStrategy.from_repo().class_weights(query)
