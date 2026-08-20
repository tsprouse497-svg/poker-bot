"""A postflop continuity device, and deliberately not a postflop strategy.

There is no postflop chart in this repo and there will not be one in v1, so a
simulated hand that reaches a flop has nothing to ask. This module is the smallest
honest thing that lets such a hand finish: it checks whenever checking is free, and
it folds to a bet unless it is holding a fact.

That fact is the whole design. Money goes in on exactly one path - a board on which no
two-card holding drawn from the unseen deck beats hero, whatever cards are still to
come - because it is the only postflop claim this repo can make without a number it
cannot source. A pot-odds rule needs an equity estimate, an equity estimate needs a
range to be against, and a made-hand threshold such as "call top pair or better" is a
number somebody invented that tests would then freeze. None of those appear here.

The bar is "no holding beats hero" and not "no holding beats or ties hero", which is a
correction rather than a preference. A chop is not a loss: the pot that gets chopped
holds the villain's bet and the money already in the middle, so facing a bet of B into
a pot of P that already contains B, a hand nothing can beat returns at least half of
P + B for a payment of B and the call gains at least (P - B) / 2. P always exceeds B,
because a postflop pot holds the preflop money too. Multiway does not change the sign
either - chopping three ways returns P/3 + B for a payment of B. So a hand that can
only be chopped is a hand that cannot lose, and folding it would be the one thing this
module exists not to do.

The claim reaches the turn and the river and stops there. On the river the board is
complete and the question is 990 villain holdings. On the turn a card is still to come,
so it means "no holding beats hero after any river card", and that decomposes exactly:
hero is safe on the turn iff hero is safe on each of the 46 boards a river card
completes. So the turn costs 46 river checks - 45,540 evaluations, a few seconds - and
reuses the river test and its memo rather than needing an enumeration of its own. The
flop is a different animal: 1,081 holdings against 990 runouts, over a million
evaluations for one decision, which no exhaustive sweep can carry. That gap is recorded
in `backlog.yml` rather than approximated, because a sampled version would turn the one
fact this module rests on back into a guess, and until it closes a flop bet always
takes the pot from this bot.

The test is exhaustive by construction. It ranks every villain's seven cards with the
same evaluator that ranks hero's, and consults no hand categories, no table of nut
hands, and no sampled subset of either the holdings or the river cards, each of which
the phase contract forbids by name. It is also not narrowed by how many villains remain
or by which cards folded players took: the full unseen deck is a superset of what any
one villain can hold, so the test can decline to call a hand that was in fact
unbeatable and can never call one that was beatable. Conservative in the only direction
that matters.

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

# The streets on which the unbeatable claim is affordable, and therefore the streets
# on which this module can put money in. The flop is absent by judgment call 3 and
# not by oversight; `POSTFLOP-UNBEATABLE-EARLIER-STREETS` in `backlog.yml` holds it.
DECIDABLE_STREETS: tuple[str, ...] = ("turn", "river")

# Board sizes are validated by `StrategyQuery`, but `hand_cannot_lose` is a public
# function that a report generator or a reviewer can call directly, so it re-checks
# the one precondition its answer depends on.
_TURN_BOARD = 4
_COMPLETE_BOARD = 5
_HOLE_CARDS = 2

REFUSE_NOT_POSTFLOP = f"{CODE_PREFIX}:not-postflop"
CODE_CHECK = f"{CODE_PREFIX}:check-when-free"
CODE_CALL_UNBEATABLE = f"{CODE_PREFIX}:call-hand-cannot-lose"
CODE_FOLD_ON_THE_FLOP = f"{CODE_PREFIX}:fold-facing-bet-on-the-flop"
CODE_FOLD_CAN_LOSE = f"{CODE_PREFIX}:fold-hand-can-lose"

# The two codes below exist so that an impossible legal-action set produces something
# auditable rather than something illegal. Neither is reachable from a state the
# engine's own `legal_actions` can produce, and the phase enumeration asserts that by
# finding zero postflop refusals; they are here because "cannot happen" is a claim
# about today's engine and this module should not depend on it silently.
CODE_PASSIVE_SUBSTITUTE = f"{CODE_PREFIX}:wanted-action-not-legal-here"
REFUSE_NO_PASSIVE_ACTION = f"{CODE_PREFIX}:no-passive-action-is-legal"

# The only action this branch may substitute is a fold. Calling was here once, and it was
# `FALLBACK-FAIL-CLOSED-CAN-CALL`: a branch reached because the chosen action was
# unavailable answered by investing in a hand that can lose, which is the one thing this
# module exists not to do. Where fold is absent too, the answer is a refusal.
_PASSIVE_ORDER: tuple[str, ...] = ("fold",)

# One memo entry per distinct river question. Bounded rather than unbounded because a
# long simulation asks a great many of them and a cache that only grows is a leak. A
# turn question spends 46 of these entries, one per river card, so the ceiling has to
# clear that by a wide margin; a few thousand is far more than any hand or report needs.
_UNBEATABLE_MEMO_SIZE = 4096

# Villain holdings on a complete board, and river cards on the turn. Neither is used to
# drive a loop - both loops run over the actual cards - but the report quotes them and a
# reviewer checking the price of the turn claim should find them named somewhere.
UNSEEN_HOLDINGS_ON_A_COMPLETE_BOARD = 990
POSSIBLE_RIVER_CARDS = 46


def _villain_beats(hero_rank: HandRank, villain_rank: HandRank) -> bool:
    """Whether one villain holding is a reason not to call.

    Only an outright loss counts, by judgment call 2. A tie does not, because a chopped
    pot returns the villain's bet along with a share of the money already in the middle:
    calling a hand nothing can beat gains at least (pot - to_call) / 2 and can never
    lose, whatever the price. An earlier version of this function counted a tie as well
    and called that strict. It was folding hands that cannot lose, which is the one
    thing this module exists not to do.
    """
    return villain_rank.beats(hero_rank)


def _unseen_deck(seen: tuple[Card, ...]) -> tuple[Card, ...]:
    """The full 52 minus everything hero can see: 45 cards on a complete board.

    Not narrowed by seat count or by folded players, per judgment call 7. Those cards
    are genuinely gone from the deck, but the query does not say which they were, and
    guessing would be the one kind of error this test must not make.
    """
    excluded = frozenset(seen)
    return tuple(card for card in standard_deck() if card not in excluded)


@lru_cache(maxsize=_UNBEATABLE_MEMO_SIZE)
def _river_unbeatable(hole_cards: tuple[str, ...], board: tuple[str, ...]) -> bool:
    """The complete-board enumeration, over a canonical key.

    Memoised because it is a pure function of seven cards and nothing else. The memo
    lives on this module function rather than on the strategy so that the strategy
    stays a frozen, field-equal dataclass: two instances compare equal, hold no state
    between calls, and answer identically, which is what makes an audit line
    replayable. A cache is not state in that sense - it changes how long an answer
    takes and never which answer arrives.

    The loop returns on the first holding that beats hero. That is a short-circuit and
    not a shortcut: proving "no holding does" still costs all 990 combinations, and only
    the already-lost cases get cheap.
    """
    hero = parse_cards(hole_cards)
    board_cards = parse_cards(board)
    hero_rank = evaluate_best(hero + board_cards)
    for villain in combinations(_unseen_deck(hero + board_cards), 2):
        if _villain_beats(hero_rank, evaluate_best(villain + board_cards)):
            return False
    return True


def _turn_unbeatable(hole_cards: tuple[str, ...], board: tuple[str, ...]) -> bool:
    """The turn claim, which is the river claim on all 46 boards a river card completes.

    Written as that decomposition rather than as a nested sweep of its own, because the
    two are the same enumeration and this way there is one place where a villain holding
    is ranked. It also means the turn answer and every river answer underneath it land in
    the same memo, so a hand that calls the turn and then faces a river bet pays nothing
    the second time.

    Deliberately not memoised itself. `all` short-circuits on the first river card that
    breaks hero, so a losing turn is cheap, and a winning one is 46 memo hits after the
    first pass. A second cache over the same facts would only add a second thing to
    reason about when the answers disagree.
    """
    hero = parse_cards(hole_cards)
    board_cards = parse_cards(board)
    return all(
        _river_unbeatable(hole_cards, tuple(sorted(board + (str(river),))))
        for river in _unseen_deck(hero + board_cards)
    )


def hand_cannot_lose(hole_cards: tuple[str, str], board: tuple[str, ...]) -> bool:
    """True when no possible villain holding beats hero, whatever card is still to come.

    A tie is not a loss, so a hand every holding chops cannot lose and this returns
    True for it.

    Answerable on the turn and on the river only. A flop board is an error rather than
    an occasion to guess: the honest claim there is over 1,081 holdings against 990
    runouts, a million evaluations for one decision, and the only way to make it cheap
    would be to sample it, which turns the fact back into a guess. The gap is
    `POSTFLOP-UNBEATABLE-EARLIER-STREETS` in `backlog.yml`.

    The key is sorted so that the same cards asked in any order are one memo entry. Hole
    cards and board are sorted separately, because which two cards are hero's is the
    part that matters and the split must survive canonicalization.
    """
    if len(hole_cards) != _HOLE_CARDS:
        raise ValueError(f"exactly two hole cards are required, got {len(hole_cards)}")
    key = tuple(sorted(hole_cards))
    if len(board) == _COMPLETE_BOARD:
        return _river_unbeatable(key, tuple(sorted(board)))
    if len(board) == _TURN_BOARD:
        return _turn_unbeatable(key, tuple(sorted(board)))
    raise ValueError(
        "the unbeatable claim is only decidable against a turn or a complete river"
        f" board, got {len(board)} board cards"
    )


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
        """Fold, unless hero's hand cannot lose on a street where that is decidable."""
        wanted, code = self._wanted_facing_a_bet(query)
        if wanted in query.legal_actions:
            return StrategyDecision(wanted, None, code)
        return self._fail_closed(query)

    def _wanted_facing_a_bet(self, query: StrategyQuery) -> tuple[str, str]:
        """What the rules ask for, before legality is considered.

        Two codes for two folds, because they are different facts about the hand and a
        reviewer counting them should not have to guess which. Folding on the flop says
        nothing about hero's cards - the claim is not decidable there by judgment call 3,
        so the enumeration is never even run. Folding on the turn or the river says the
        enumeration ran and found a holding that beats hero.
        """
        if query.street not in DECIDABLE_STREETS:
            return "fold", CODE_FOLD_ON_THE_FLOP
        if hand_cannot_lose(query.hole_cards, query.board):
            return "call", CODE_CALL_UNBEATABLE
        return "fold", CODE_FOLD_CAN_LOSE

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
