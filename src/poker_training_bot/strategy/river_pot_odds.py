"""Decision 5: call a river bet when equity against the unseen deck beats the price.

Split out of `postflop_betting` rather than written inside it, and the split is the whole of
decision 5's subject. This rule reads no committed artifact, needs no solve and answers a street
the phase deliberately did not solve; the strategy beside it does the opposite on all three
counts. Keeping them in one file would also have put the module past the repo's 500-line cap,
and compressing the reasoning in either place to make room deletes the part that is hard.

**A uniform unseen deck flatters hero**, which is the accepted cost rather than a defect to be
tuned away. A villain betting the river does not hold a uniform slice of the deck, so counting
against every holding still in it over-states what hero beats - and the rule built on it
over-calls, as the exact mirror of the fallback's over-folding. Decision 5 ships it behind an
explicit flag and asks the report to print the frequency it fires rather than to claim it is
right.

**The orientation of `holding_counts` is this module's one real hazard.** A function of that name
already lives in `scripts/generate_postflop_fallback_report.py` and returns `(beats, ties, label)`
with `beats` counting the holdings that beat *hero*. Lifting it into `src` unchanged inverts
every equity here, and a check that the three numbers add to 990 passes either way. They are the
other way round below, and the frozen test pins the numbers rather than the name.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from poker_training_bot.poker_core.cards import parse_cards, standard_deck
from poker_training_bot.poker_core.hand_eval import evaluate_best
from poker_training_bot.strategy.contract import StrategyQuery

UNSEEN_HOLDINGS_ON_A_COMPLETE_BOARD = 990
"""Two-card holdings the 45 unseen cards make on a complete board. Named rather than inlined,
because it is the denominator of every figure below and a reader checking the price of the claim
should find it written down."""

_HOLE_CARDS = 2
_COMPLETE_BOARD = 5
_EQUITY_MEMO = 4096
"""One memo entry per distinct river question. Bounded rather than unbounded, on the fallback's
own reasoning: a long simulation asks a great many of them and a cache that only grows is a leak.
A cache is not state in the sense that matters here - it changes how long an answer takes and
never which answer arrives - so the strategy holding it stays field-equal and replayable."""


@lru_cache(maxsize=_EQUITY_MEMO)
def holding_counts(hole_cards: tuple[str, ...], board: tuple[str, ...]) -> tuple[int, int, int]:
    """Holdings hero **beats**, holdings that tie hero, and holdings that beat hero.

    In that order, and the order is the point: `AhAd` on `Kc7d2h9s4c` is `(884, 1, 105)`, not
    `(105, 1, 884)`. Inverted, the same three numbers read as 10.66% equity rather than 89.34%,
    which is the wrong side of a 25% price, and nothing about their sum says which way round
    they are.

    Counted rather than short-circuited. `hand_cannot_lose` returns on the first holding that
    beats hero, because it only ever answers "does one exist"; a price needs the total, so this
    walks all 990 every time and pays for it once per distinct question.

    River only. On an incomplete board the honest claim is over runouts as well as holdings, and
    approximating it turns a count back into a guess - the same line `hand_cannot_lose` holds,
    for the same reason, in `POSTFLOP-UNBEATABLE-EARLIER-STREETS`.
    """
    if len(hole_cards) != _HOLE_CARDS:
        raise ValueError(f"exactly two hole cards are required, got {len(hole_cards)}")
    if len(board) != _COMPLETE_BOARD:
        raise ValueError(
            f"equity against the unseen deck is counted on a complete board, got {len(board)}"
        )
    hero = parse_cards(tuple(hole_cards))
    table = parse_cards(tuple(board))
    hero_rank = evaluate_best(hero + table)
    seen = frozenset(hero + table)
    deck = tuple(card for card in standard_deck() if card not in seen)
    wins = ties = losses = 0
    for villain in combinations(deck, 2):
        rank = evaluate_best(villain + table)
        if rank.beats(hero_rank):
            losses += 1
        elif rank.ties(hero_rank):
            ties += 1
        else:
            wins += 1
    return wins, ties, losses


def river_equity(hole_cards: tuple[str, ...], board: tuple[str, ...]) -> float:
    """Hero's share against a uniform unseen deck: `(wins + ties/2) / 990`.

    A tie is worth half a pot rather than nothing, which is the same correction the fallback's
    unbeatable test already carries: a chopped pot returns the villain's bet along with a share
    of the middle, so counting a chop as a loss folds hands that cannot lose.
    """
    wins, ties, _ = holding_counts(tuple(hole_cards), tuple(board))
    return (wins + ties / 2) / UNSEEN_HOLDINGS_ON_A_COMPLETE_BOARD


def pot_odds_price(query: StrategyQuery) -> float:
    """The price of the call as a share of the pot it wins: `to_call / (pot + to_call)`.

    Both numbers off the query, so the price is what the table says rather than what a line
    reconstruction believes. `query.pot` already holds the bet hero is facing, because every
    seat's contribution is in it, which is why the denominator adds only hero's own call.
    """
    return query.to_call / (query.pot + query.to_call)
