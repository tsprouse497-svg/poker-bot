"""A postflop continuity device, and deliberately not a postflop strategy.

There is no postflop chart in this repo and there will not be one in v1, so a
simulated hand that reaches a flop has nothing to ask. This module is the smallest
honest thing that lets such a hand finish: it checks whenever checking is free, and
it folds to a bet unless it is holding a fact.

That fact is the whole design. Money goes in on exactly one path - a complete board
on which no two-card holding drawn from the unseen deck beats or ties hero - because
it is the only postflop claim this repo can make without a number it cannot source.
A pot-odds rule needs an equity estimate, an equity estimate needs a range to be
against, and a made-hand threshold such as "call top pair or better" is a number
somebody invented that tests would then freeze. None of those appear here, and the
visible cost is that any flop or turn bet takes the pot from this bot: on those
streets "nothing beats me" would have to mean "nothing beats me after any runout",
which is 903 runouts against 990 holdings for a single decision. That gap is
recorded in `backlog.yml` rather than approximated, because an approximation would
turn the one fact this module rests on back into a guess.

The unbeatable test is exhaustive by construction. It enumerates all 990
combinations of the 45 cards hero cannot see and ranks each villain's seven cards
with the same evaluator that ranks hero's. It consults no hand categories, no table
of nut hands, and no sampled subset, each of which the phase contract forbids by
name. It is also not narrowed by how many villains remain or by which cards folded
players took: the full unseen deck is a superset of what any one villain can hold, so
the test can decline to call a hand that was in fact unbeatable and can never call
one that was beatable. Conservative in the only direction that matters.

Aggression is absent rather than restrained. Nothing here returns a bet or a raise
on any path at any street, because a bet needs a size and the repo's only sizing
source is the preflop solver export; a postflop sizing scheme invented to fill the
hole would produce a bot whose postflop play looks deliberate and is not. Against
another copy of itself every postflop street therefore checks through, so a hand this
bot plays is decided preflop and then shown down, and no report may read postflop
quality into it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations

from poker_training_bot.poker_core.cards import Card, parse_cards, standard_deck
from poker_training_bot.poker_core.hand_eval import HandRank, evaluate_best
from poker_training_bot.strategy.contract import (
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)

CODE_PREFIX = "postflop-fallback"

POSTFLOP_STREETS: tuple[str, ...] = ("flop", "turn", "river")

_RIVER = "river"

# Board sizes are validated by `StrategyQuery`, but `river_hand_cannot_lose` is a
# public function that a report generator or a reviewer can call directly, so it
# re-checks the one precondition its answer depends on.
_COMPLETE_BOARD = 5
_HOLE_CARDS = 2

REFUSE_NOT_POSTFLOP = f"{CODE_PREFIX}:not-postflop"
CODE_CHECK = f"{CODE_PREFIX}:check-when-free"
CODE_CALL_UNBEATABLE = f"{CODE_PREFIX}:call-river-hand-cannot-lose"
CODE_FOLD_BEFORE_RIVER = f"{CODE_PREFIX}:fold-facing-bet-before-river"
CODE_FOLD_RIVER_CAN_LOSE = f"{CODE_PREFIX}:fold-river-hand-can-lose"

# The two codes below exist so that an impossible legal-action set produces something
# auditable rather than something illegal. Neither is reachable from a state the
# engine's own `legal_actions` can produce, and the phase enumeration asserts that by
# finding zero postflop refusals; they are here because "cannot happen" is a claim
# about today's engine and this module should not depend on it silently.
CODE_PASSIVE_SUBSTITUTE = f"{CODE_PREFIX}:wanted-action-not-legal-here"
REFUSE_NO_PASSIVE_ACTION = f"{CODE_PREFIX}:no-passive-action-is-legal"

# Facing a bet, checking is by definition not on offer, so the only passive actions
# left are folding and calling. Folding comes first because it invests nothing.
_PASSIVE_ORDER: tuple[str, ...] = ("fold", "call")

# One memo entry per distinct river question. Bounded rather than unbounded because a
# long simulation asks a great many of them and a cache that only grows is a leak; a
# few thousand entries is far more than any single hand or report needs.
_UNBEATABLE_MEMO_SIZE = 4096


def _villain_at_least_ties(hero_rank: HandRank, villain_rank: HandRank) -> bool:
    """Whether one villain holding is a reason not to call.

    Strict, by judgment call 2. A guaranteed chop pays a full call to win half a pot,
    so whether calling is right there depends on the price, and the price is exactly
    the number this phase has no oracle for. A tie therefore counts against calling
    alongside an outright loss, which is why the two clauses are joined here rather
    than the second one being dropped as a nicety.
    """
    return villain_rank.beats(hero_rank) or villain_rank.ties(hero_rank)


def _unseen_deck(seen: tuple[Card, ...]) -> tuple[Card, ...]:
    """The full 52 minus everything hero can see: 45 cards on a complete board.

    Not narrowed by seat count or by folded players, per judgment call 7. Those cards
    are genuinely gone from the deck, but the query does not say which they were, and
    guessing would be the one kind of error this test must not make.
    """
    excluded = frozenset(seen)
    return tuple(card for card in standard_deck() if card not in excluded)


@lru_cache(maxsize=_UNBEATABLE_MEMO_SIZE)
def _unbeatable(hole_cards: tuple[str, ...], board: tuple[str, ...]) -> bool:
    """The enumeration itself, over a canonical key.

    Memoised because it is a pure function of seven cards and nothing else. The memo
    lives on this module function rather than on the strategy so that the strategy
    stays a frozen, field-equal dataclass: two instances compare equal, hold no state
    between calls, and answer identically, which is what makes an audit line
    replayable. A cache is not state in that sense - it changes how long an answer
    takes and never which answer arrives.

    The loop returns on the first holding that beats or ties hero. That is a
    short-circuit and not a shortcut: proving "no holding does" still costs all 990
    combinations, and only the already-lost cases get cheap.
    """
    hero = parse_cards(hole_cards)
    board_cards = parse_cards(board)
    hero_rank = evaluate_best(hero + board_cards)
    for villain in combinations(_unseen_deck(hero + board_cards), 2):
        if _villain_at_least_ties(hero_rank, evaluate_best(villain + board_cards)):
            return False
    return True


def river_hand_cannot_lose(hole_cards: tuple[str, str], board: tuple[str, ...]) -> bool:
    """True when no possible villain holding beats or ties hero on this board.

    The claim is only decidable against a complete board, so an incomplete or
    over-long one is an error rather than an occasion to guess: on the flop or the
    turn a hand that cannot lose now can be beaten by a card that has not come, which
    is a different and much larger enumeration.

    The key is sorted so that the same seven cards asked in any order are one memo
    entry. Hole cards and board are sorted separately, because which two cards are
    hero's is the part that matters and the split must survive canonicalization.
    """
    if len(board) != _COMPLETE_BOARD:
        raise ValueError(
            "the unbeatable claim is only decidable against a complete five-card"
            f" board, got {len(board)} board cards"
        )
    if len(hole_cards) != _HOLE_CARDS:
        raise ValueError(f"exactly two hole cards are required, got {len(hole_cards)}")
    return _unbeatable(tuple(sorted(hole_cards)), tuple(sorted(board)))


@dataclass(frozen=True)
class PostflopFallbackStrategy:
    """Check when it is free, fold when it is not, call the one hand that cannot lose.

    Field-free and frozen on purpose. The fallback has nothing to configure, so two
    instances are equal and interchangeable, and there is no per-instance state a
    replay could disagree about.
    """

    strategy_id: str = "postflop-fallback"
    strategy_version: int = 1

    def decide(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        """Answer a postflop query, or refuse a query that is not postflop at all.

        The street guard comes first and returns a refusal rather than a passive
        action, by judgment call 6. A preflop spot always has either a chart answer or
        a chart gap, and this module is neither; letting it answer would give the repo
        a second, silent preflop strategy reachable by mistake.

        `StrategyQuery` guarantees that checking is legal exactly when there is
        nothing to call, so the second branch is the whole "free" case and everything
        after it is facing a bet.
        """
        if query.street not in POSTFLOP_STREETS:
            return StrategyRefusal(REFUSE_NOT_POSTFLOP)
        if "check" in query.legal_actions:
            return StrategyDecision("check", None, CODE_CHECK)
        return self._facing_a_bet(query)

    def _facing_a_bet(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        """Fold, unless this is the river and hero's hand cannot lose."""
        wanted, code = self._wanted_facing_a_bet(query)
        if wanted in query.legal_actions:
            return StrategyDecision(wanted, None, code)
        return self._fail_closed(query)

    def _wanted_facing_a_bet(self, query: StrategyQuery) -> tuple[str, str]:
        """What the rules ask for, before legality is considered.

        Two codes for two folds, because they are different facts about the hand and a
        reviewer counting them should not have to guess which. Folding on the flop or
        the turn says nothing about hero's cards - the exception is river-only by
        judgment call 3, so the enumeration there is never even run. Folding on the
        river says the enumeration ran and found a holding that beats or ties hero.
        """
        if query.street != _RIVER:
            return "fold", CODE_FOLD_BEFORE_RIVER
        if river_hand_cannot_lose(query.hole_cards, query.board):
            return "call", CODE_CALL_UNBEATABLE
        return "fold", CODE_FOLD_RIVER_CAN_LOSE

    def _fail_closed(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        """Handle a legal-action set the engine cannot currently produce.

        Reached only if the action the rules chose is not on offer. Rather than return
        something illegal, take the most passive action that is legal, and refuse
        outright if none of them is - a set offering only aggression leaves nothing
        this module is allowed to do, and returning a bet or a raise to escape that is
        the one thing the contract forbids everywhere.
        """
        for candidate in _PASSIVE_ORDER:
            if candidate in query.legal_actions:
                return StrategyDecision(candidate, None, CODE_PASSIVE_SUBSTITUTE)
        return StrategyRefusal(REFUSE_NO_PASSIVE_ACTION)
