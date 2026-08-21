"""Human evidence for the postflop continuity fallback: what it covers, and what it never does.

Written for a reviewer who does not read code, and built around the two claims that
carry this phase. The first is totality: every legal-action set the engine can produce
postflop gets an answer, and the enumeration that proves it reads its shapes out of the
engine's own `legal_actions` rather than from a list written here, so a change to the
engine widens the sweep instead of escaping it. The second is the one place money goes
in postflop, which is shown as named cards with the villain count beside them, because
"exactly one holding out of 990 beats this" is an argument a reviewer can check and
"the code says so" is not. The turn examples carry a second column for the same reason:
a turn fold is a claim about cards that have not come, so the report prints how many of
the possible river cards break the hand, and the pair of rows for the same hand on the
turn and then on the river is the clearest way to show that the two streets are not one
rule with a different board length.

The distinct decision codes are counted from the outcomes actually observed rather than
from the module's list of codes. Two of the codes it defines are unreachable from the
current engine, and printing them as rows of zero would read as coverage of states that
do not exist.

The composite section is the shape of a hand rather than a summary of one. Preflop the
committed charts either answer or refuse, postflop every street checks through, and the
hand is settled at showdown - that is what these tables are for, so nobody has to take
it on trust from a sentence.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from itertools import combinations
from textwrap import fill

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.hand_history import load_hand_history_file
from poker_training_bot.hand_history.replay import DecisionPoint, replay_hand
from poker_training_bot.poker_core.cards import Card, card_texts, parse_cards, standard_deck
from poker_training_bot.poker_core.engine import BettingRoundState, PlayerState
from poker_training_bot.poker_core.hand_eval import evaluate_best
from poker_training_bot.strategy.composite import (
    POSTFLOP_COMPONENT,
    PREFLOP_COMPONENT,
    CompositeStrategy,
)
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    SeatState,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
    records_to_jsonl,
)
from poker_training_bot.strategy.postflop_fallback import (
    DECIDABLE_STREETS,
    POSSIBLE_RIVER_CARDS,
    POSTFLOP_STREETS,
    UNSEEN_HOLDINGS_ON_A_COMPLETE_BOARD,
    PostflopFallbackStrategy,
    hand_cannot_lose,
)

FIXTURE = REPO_ROOT / "data" / "samples" / "normalized_hands.json"
REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_postflop_fallback_report.txt"
AUDIT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_postflop_decision_audit.jsonl"

BOARD_SIZES = {"flop": 3, "turn": 4, "river": 5}

# A two-seat table is the smallest one that produces every postflop legal-action set, so
# the enumeration uses it. Blinds and stacks are round numbers because nothing here
# depends on their size: the fallback reads the street, the action set, and the cards.
SMALL_BLIND = 10
BIG_BLIND = 20
MIN_RAISE = BIG_BLIND
HERO_SEAT = 1
VILLAIN_SEAT = 0
VILLAIN_STACK = 500

# The chips in the enumeration's pot beyond what the two seats have put in on the street
# being played. They are villain's, from the street before: a pot is the sum of what the
# seats put in, so a hundred chips belonging to nobody cannot be described as a query at
# all. Attributing them to villain's earlier street describes a real hand - money went in
# on the flop and the turn is being played - and it is the enumeration's own statement
# about how the hand got here rather than data read off anything.
VILLAIN_EARLIER_STREET = 100

# Forty-five cards hero cannot see on a complete board, taken two at a time, and the
# forty-six cards that can complete a turn board. Both come from the strategy module so
# the report cannot quote a denominator the enumeration does not use.
UNSEEN_HOLDINGS = UNSEEN_HOLDINGS_ON_A_COMPLETE_BOARD
UNSEEN_RIVERS = POSSIBLE_RIVER_CARDS
TURN_PAIRS = UNSEEN_RIVERS * UNSEEN_HOLDINGS

# Prose is wrapped rather than left to the terminal, so the committed file reads the same
# in a diff, in an editor, and in a browser.
WRAP = 88


def wrapped(text: str, indent: str = "") -> list[str]:
    return fill(
        " ".join(text.split()),
        width=WRAP,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    ).splitlines()


@dataclass(frozen=True)
class Shape:
    """One postflop betting shape, together with the legal-action set it produced.

    The action set is not written down: it is whatever `legal_actions` returned for the
    engine state the other three fields describe.
    """

    actions: tuple[str, ...]
    current_bet: int
    hero_street_bet: int
    hero_stack: int

    @property
    def to_call(self) -> int:
        """Capped at hero's stack, so the price is what hero would actually pay."""
        return min(self.current_bet - self.hero_street_bet, self.hero_stack)

    @property
    def hero_is_short(self) -> bool:
        """The price to call takes hero's whole remaining stack.

        Phase 06 wrote this as `0 < stack < to_call`, which the cap makes unsatisfiable:
        a price hero can actually pay never exceeds what hero holds. Same hero, restated.
        """
        return 0 < self.hero_stack == self.to_call

    @property
    def label(self) -> str:
        return "/".join(self.actions)


def engine_shapes() -> tuple[Shape, ...]:
    """Every non-empty legal-action set the engine can produce for a postflop seat.

    A sweep over the engine rather than a hard-coded list. An empty action set is
    skipped, because a folded or all-in seat is never asked to decide and
    `StrategyQuery` rejects empty `legal_actions` outright.
    """
    found: dict[tuple[str, ...], Shape] = {}
    for current_bet in (0, MIN_RAISE, 3 * MIN_RAISE):
        for hero_street_bet in (0, MIN_RAISE, 3 * MIN_RAISE):
            if hero_street_bet > current_bet:
                continue
            for hero_stack in (0, MIN_RAISE // 2, MIN_RAISE, 20 * MIN_RAISE):
                state = BettingRoundState(
                    players=(
                        PlayerState(
                            seat=VILLAIN_SEAT,
                            name="villain",
                            stack=VILLAIN_STACK,
                            hole_cards=(),
                            committed_total=current_bet,
                            street_bet=current_bet,
                        ),
                        PlayerState(
                            seat=HERO_SEAT,
                            name="hero",
                            stack=hero_stack,
                            hole_cards=(Card("A", "s"), Card("K", "d")),
                            committed_total=hero_street_bet,
                            street_bet=hero_street_bet,
                        ),
                    ),
                    current_bet=current_bet,
                    min_raise=MIN_RAISE,
                )
                actions = tuple(kind.value for kind in state.legal_actions(HERO_SEAT))
                if actions and actions not in found:
                    found[actions] = Shape(actions, current_bet, hero_street_bet, hero_stack)
    return tuple(found[key] for key in sorted(found))


@dataclass(frozen=True)
class Scenario:
    """Hero's two cards and a complete five-card board, sliced back per street.

    These are the scenarios `tests/test_postflop_fallback.py` names, with the same cards
    and the same reasoning, so the report and the tests cannot drift into telling
    different stories about the one spot where this bot invests.
    """

    name: str
    hole_cards: tuple[str, ...]
    board: tuple[str, ...]
    reason: str

    def board_for(self, street: str) -> tuple[str, ...]:
        return self.board[: BOARD_SIZES[street]]

    @property
    def cards_text(self) -> str:
        return " ".join(self.hole_cards)

    @property
    def board_text(self) -> str:
        return " ".join(self.board)


ACE_HIGH = Scenario(
    "ace high, nothing else",
    ("As", "Kd"),
    ("2c", "7h", "Ts", "4d", "9s"),
    "an ordinary hand: most of the deck beats it, so it is the enumeration's normal case",
)
ROYAL_IN_HAND = Scenario(
    "royal flush in hand",
    ("Ac", "Kc"),
    ("Qc", "Jc", "Tc", "2d", "3h"),
    "hero holds a royal flush in clubs; nothing beats a royal flush, and the only hand that"
    " ties it needs Ac and Kc, both of which hero holds",
)
QUAD_ACES = Scenario(
    "quad aces holding the fourth ace",
    ("Ac", "2c"),
    ("As", "Ah", "Ad", "Kc", "Kd"),
    "hero holds four aces with a king; only a straight flush beats quad aces and no three"
    " board cards share a suit, so no flush exists, and a tie needs the fourth ace, which"
    " hero holds",
)
NUT_FLUSH_BEATABLE = Scenario(
    "nut flush that one straight flush beats",
    ("Ad", "Kd"),
    ("2d", "3d", "4d", "5h", "Kc"),
    "hero holds the ace-high flush and no villain flush can match it, but 6d 5d makes"
    " 2d 3d 4d 5d 6d, a six-high straight flush; one holding out of 990 is enough to fold",
)
QUAD_NINES_CHOP = Scenario(
    "quad nines with the kicker on the board",
    ("Kd", "Qh"),
    ("9c", "9d", "9h", "9s", "Ac"),
    "hero's best five cards are the four nines and the ace, all of them on the board, so"
    " every villain holds the same hand: nothing beats hero and every holding chops, and a"
    " chop is not a loss - the pot hands back the villain's bet along with a share of the"
    " money already in the middle",
)
ROYAL_ON_BOARD = Scenario(
    "royal flush on the board",
    ("2d", "7h"),
    ("Ac", "Kc", "Qc", "Jc", "Tc"),
    "the nuts is the board itself, a royal flush, and hero's two cards are irrelevant; hero"
    " cannot hold that hand as a two-card holding and neither can any villain, so the whole"
    " table chops and hero's share of the pot is guaranteed",
)
STRAIGHT_A_CLUB_BREAKS = Scenario(
    "straight a club river would break",
    ("Th", "Jd"),
    ("9c", "8c", "7h", "6d", "2h"),
    "hero holds the jack-high straight and nothing beats it on the board as it stands, but"
    " two clubs are showing, so a club river would give any two clubs a flush; the turn"
    " claim has to survive every river card and this one does not",
)


@dataclass(frozen=True)
class WorkedExample:
    """One named hand, on one street, with the sentence that argues its verdict.

    Street-bearing because the same cards decide differently on the turn and the river,
    and that pair is the clearest thing this report can show a reviewer about why the two
    streets are not one rule.
    """

    scenario: Scenario
    street: str
    reason: str

    @property
    def board(self) -> tuple[str, ...]:
        return self.scenario.board_for(self.street)

    @property
    def board_text(self) -> str:
        return " ".join(self.board)


# The river examples the phase contract names by hand, in the order a reviewer reads
# them: the ones that call first, then the one that folds.
RIVER_EXAMPLES = tuple(
    WorkedExample(scenario, "river", scenario.reason)
    for scenario in (
        ROYAL_IN_HAND,
        QUAD_ACES,
        QUAD_NINES_CHOP,
        ROYAL_ON_BOARD,
        NUT_FLUSH_BEATABLE,
    )
)

# The turn examples, and the pair that makes the difference between the streets visible.
TURN_EXAMPLES = (
    WorkedExample(
        ROYAL_IN_HAND,
        "turn",
        "hero already holds a royal flush in clubs, so no river card can beat it and none"
        " can tie it, because a tie needs Ac and Kc and hero holds both",
    ),
    WorkedExample(STRAIGHT_A_CLUB_BREAKS, "turn", STRAIGHT_A_CLUB_BREAKS.reason),
    WorkedExample(
        STRAIGHT_A_CLUB_BREAKS,
        "river",
        "the river came 2h rather than a club, so no flush is ever possible now, nothing"
        " beats the jack-high straight, and the hand that folded a turn bet calls a river"
        " one - the same cards, one card later, and the card that would have broken it"
        " missed",
    ),
)

ENUMERATED = (
    ACE_HIGH,
    ROYAL_IN_HAND,
    QUAD_ACES,
    NUT_FLUSH_BEATABLE,
    QUAD_NINES_CHOP,
    ROYAL_ON_BOARD,
)


def enumeration_query(shape: Shape, street: str, scenario: Scenario) -> StrategyQuery:
    """A postflop query whose betting numbers come from an engine-produced shape.

    The pot is a construction rather than a replayed hand: villain's earlier street plus
    what the two seats have put in on this one. Nothing in the enumeration reads the pot -
    the fallback reads the street, the action set and the cards - so the attribution buys
    a shape that describes a real hand instead of one holding money nobody paid.

    Neither seat has folded, because a folded seat is never asked to decide, and neither is
    all-in: villain has its whole stack behind and every hero the engine offers an action to
    has chips left. Both markers are stated rather than read off a zero stack.
    """
    villain_total = VILLAIN_EARLIER_STREET + shape.current_bet
    return StrategyQuery(
        hand_id=f"enumeration|{scenario.name}|{street}|{shape.label}",
        street=street,
        seat=HERO_SEAT,
        button_seat=VILLAIN_SEAT,
        hole_cards=scenario.hole_cards,
        board=scenario.board_for(street),
        legal_actions=shape.actions,
        to_call=shape.to_call,
        current_bet=shape.current_bet,
        # The level plus the size of the last full bet or raise, which on this street is
        # `MIN_RAISE`. It is the engine's own derivation rather than a number chosen here.
        min_raise_target=shape.current_bet + MIN_RAISE,
        pot=villain_total + shape.hero_street_bet,
        stacks=((VILLAIN_SEAT, VILLAIN_STACK), (HERO_SEAT, shape.hero_stack)),
        seat_states=(
            SeatState(
                seat=VILLAIN_SEAT,
                street_bet=shape.current_bet,
                committed_total=villain_total,
                folded=False,
                all_in=False,
            ),
            SeatState(
                seat=HERO_SEAT,
                street_bet=shape.hero_street_bet,
                committed_total=shape.hero_street_bet,
                folded=False,
                all_in=False,
            ),
        ),
        blinds=(SMALL_BLIND, BIG_BLIND),
    )


def enumeration_queries(shapes: tuple[Shape, ...]) -> tuple[StrategyQuery, ...]:
    return tuple(
        enumeration_query(shape, street, scenario)
        for shape in shapes
        for street in POSTFLOP_STREETS
        for scenario in ENUMERATED
    )


@dataclass(frozen=True)
class Census:
    """What a reviewer needs beside a worked example in order to check its verdict.

    `beats` and `ties` are counted on the board the fallback is actually looking at, so on
    a turn example they show that nothing beats hero yet. `unsafe_rivers` is the column
    that explains a turn fold: how many of the river cards leave some holding beating
    hero. It is None on a river example, where there is no card left to come.
    """

    beats: int
    ties: int
    hero_hand: str
    cannot_lose: bool
    unsafe_rivers: int | None = None


def unseen_cards(hole_cards: tuple[str, ...], board: tuple[str, ...]) -> tuple[Card, ...]:
    seen = frozenset(parse_cards(hole_cards) + parse_cards(board))
    return tuple(card for card in standard_deck() if card not in seen)


def holding_counts(
    hole_cards: tuple[str, ...], board: tuple[str, ...]
) -> tuple[int, int, str]:
    """Holdings that beat hero, holdings that tie hero, and hero's own category.

    Counted rather than read off the fallback's boolean, because the boolean
    short-circuits on the first holding that beats hero and the report needs the total.
    One pass over the unseen deck per example, which is the whole argument for the call
    rule and cheap enough to spend.
    """
    hero = parse_cards(hole_cards)
    board_cards = parse_cards(board)
    hero_rank = evaluate_best(hero + board_cards)
    beats = ties = 0
    for villain in combinations(unseen_cards(hole_cards, board), 2):
        villain_rank = evaluate_best(villain + board_cards)
        if villain_rank.beats(hero_rank):
            beats += 1
        elif villain_rank.ties(hero_rank):
            ties += 1
    return beats, ties, hero_rank.label.lower()


@cache
def villain_census(example: WorkedExample) -> Census:
    """Count what a reviewer would count, and take the verdict from the strategy itself.

    The verdict comes from `hand_cannot_lose` rather than from the counts, so the report
    cannot disagree with the module it reports on. The unsafe-river count is built out of
    the same river test the strategy calls on each completed board, so it reuses that
    memo rather than paying for a second sweep of its own.
    """
    hole_cards = example.scenario.hole_cards
    board = example.board
    beats, ties, hero_hand = holding_counts(hole_cards, board)
    unsafe_rivers = None
    if example.street == "turn":
        unsafe_rivers = sum(
            0 if hand_cannot_lose(hole_cards, board + (str(river),)) else 1
            for river in unseen_cards(hole_cards, board)
        )
    return Census(
        beats=beats,
        ties=ties,
        hero_hand=hero_hand,
        cannot_lose=hand_cannot_lose(hole_cards, board),
        unsafe_rivers=unsafe_rivers,
    )


def audit_record(
    strategy: PostflopFallbackStrategy | CompositeStrategy,
    query: StrategyQuery,
    outcome: StrategyDecision | StrategyRefusal,
) -> DecisionAuditRecord:
    return DecisionAuditRecord(
        schema_version=DECISION_AUDIT_SCHEMA_VERSION,
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.strategy_version,
        query=query,
        outcome=outcome,
    )


def header_lines(fallback: PostflopFallbackStrategy, composite: CompositeStrategy) -> list[str]:
    return [
        "Postflop Fallback Report",
        "========================",
        "",
        f"Fallback: {fallback.strategy_id} v{fallback.strategy_version}",
        f"Composite: {composite.strategy_id} v{composite.strategy_version}",
        "",
        "## What this is, and what it is not",
        "",
        *wrapped(
            "This is a continuity device, not a postflop strategy. There is no postflop chart in"
            " this repo and there will not be one in v1, so a simulated hand that reaches a flop"
            " would otherwise have nothing to ask; this fallback checks whenever checking is"
            " free, folds to a bet, and puts money in on exactly one path - a board on which no"
            " holding a villain could possibly have beats hero, whatever card is still to come."
        ),
        "",
        *wrapped(
            "That path is open on the"
            f" {' and the '.join(DECIDABLE_STREETS)} and closed on the flop, where the honest"
            " enumeration costs over a million hand evaluations for one decision. So a flop bet"
            " always takes the pot from this bot."
        ),
        "",
        *wrapped(
            "What that makes a hand: against another copy of itself every postflop street checks"
            " through, so a hand is decided preflop by the committed charts and then settled at"
            " showdown. Nothing downstream may read postflop quality into it, because there is"
            " no postflop play here to have quality."
        ),
    ]


def enumeration_lines(
    shapes: tuple[Shape, ...],
    decided: tuple[tuple[StrategyQuery, object], ...],
) -> list[str]:
    actions: Counter[str] = Counter()
    codes: Counter[str] = Counter()
    refusals = 0
    for _, outcome in decided:
        if isinstance(outcome, StrategyDecision):
            actions[outcome.action] += 1
            codes[outcome.code] += 1
        else:
            refusals += 1
    lines = [
        "## The enumeration over engine-legal postflop states",
        "",
        *wrapped(
            "Coverage is proved by enumeration, not by sampling. The legal-action sets below were"
            " not written down: each one is what the engine's own `legal_actions` returned for a"
            " postflop seat, swept over every combination of current bet, hero's street bet, and"
            " hero's remaining stack that the engine can be put in. If the engine ever produces"
            " a new action set, this sweep widens on its own rather than missing it."
        ),
        "",
        f"Legal-action sets the engine produced: {len(shapes)}",
    ]
    for shape in shapes:
        note = "  (the price to call takes hero's whole stack)" if shape.hero_is_short else ""
        lines.append(f"  {shape.label:<24}to call {shape.to_call:>4}{note}")
    lines += [
        "",
        *wrapped(
            "The price to call is capped at what hero holds, so it is the price hero can"
            " actually pay. A hero whose whole stack is the price is Phase 06's short hero"
            " restated: the old form, a stack below the price, cannot happen once the price is"
            " capped, and the situation survives as a price equal to the stack."
        ),
        "",
        *wrapped(
            f"The pot in each enumerated state is a construction, not data: it is the"
            f" {VILLAIN_EARLIER_STREET} chips villain put in on the street before, plus what the"
            " two seats have put in on the street being played. A pot is the sum of what the"
            " seats put in, so those chips had to belong to somebody, and villain's earlier"
            " street is the attribution that describes a real hand. Nothing in the enumeration"
            " reads the pot, so no verdict below depends on it - read it as a claim about how"
            " the hand got here rather than as a measurement."
        ),
        "",
        f"Streets: {len(POSTFLOP_STREETS)} ({', '.join(POSTFLOP_STREETS)})",
        f"Hands enumerated at each: {len(ENUMERATED)}",
        f"States covered: {len(decided)}"
        f" = {len(shapes)} x {len(POSTFLOP_STREETS)} x {len(ENUMERATED)}",
        "",
        *wrapped(
            "Every state returned a decision. Not one of them was a bet or a raise, at any"
            " street, because aggression needs a size and this repo has no postflop sizing."
        ),
        "",
        "Action chosen:",
    ]
    for action, count in sorted(actions.items()):
        lines.append(f"  {action:<24}{count:>6}")
    lines += [
        "",
        *wrapped(
            "Decision codes seen. These are counted from the outcomes actually observed, so a"
            " code the current engine cannot reach does not appear here as a row of zero and"
            " read as coverage of a state that does not exist."
        ),
        "",
    ]
    for code, count in sorted(codes.items()):
        lines.append(f"  {code:<52}{count:>6}")
    lines += [
        "",
        f"Postflop refusals: {refusals}",
        "",
        *wrapped(
            "That number must be zero. A refusal postflop would be a hand the simulator cannot"
            " finish, which is the whole gap this phase exists to close."
        ),
    ]
    return lines


def example_table_lines(examples: tuple[WorkedExample, ...]) -> list[str]:
    lines = [
        f"{'hero':<8}{'board':<20}{'hero holds':<18}{'beat':>6}{'tie':>6}"
        f"{'bad rivers':>12}   verdict"
    ]
    for example in examples:
        census = villain_census(example)
        rivers = "-" if census.unsafe_rivers is None else str(census.unsafe_rivers)
        lines.append(
            f"{example.scenario.cards_text:<8}{example.board_text:<20}{census.hero_hand:<18}"
            f"{census.beats:>6}{census.ties:>6}{rivers:>12}"
            f"   {'calls' if census.cannot_lose else 'folds'}"
        )
    return lines


def example_prose_lines(examples: tuple[WorkedExample, ...]) -> list[str]:
    lines: list[str] = []
    for example in examples:
        census = villain_census(example)
        counted = (
            f" Of {UNSEEN_HOLDINGS} possible villain holdings on that board,"
            f" {census.beats} beat hero and {census.ties} tie hero."
        )
        if census.unsafe_rivers is not None:
            counted += (
                f" Of the {UNSEEN_RIVERS} cards that can complete the board,"
                f" {census.unsafe_rivers} leave some holding beating hero."
            )
        lines += [
            f"{example.street}, {example.scenario.name}:"
            f" {example.scenario.cards_text} on {example.board_text}",
            *wrapped(
                f"{'Calls' if census.cannot_lose else 'Folds'}, because {example.reason}."
                f"{counted}",
                indent="  ",
            ),
            "",
        ]
    return lines


def worked_example_lines() -> list[str]:
    lines = [
        "## Where money goes in: the worked call examples",
        "",
        *wrapped(
            "The unbeatable call is the only path in this module that invests, so it is written"
            " out as cards. On a complete board hero can see seven of the 52 - two in hand and"
            f" five on the board - which leaves 45 unseen and {UNSEEN_HOLDINGS} possible"
            " two-card villain holdings. Every one of them is ranked with the same evaluator"
            " that ranks hero's own hand. No hand categories, no table of nut hands, no sampled"
            " subset."
        ),
        "",
        *wrapped(
            "The bar is that no holding beats hero. A tie does not count against calling,"
            " because a chop is not a loss: the pot that gets chopped holds the villain's bet"
            " and the money already in the middle, so facing a bet of B into a pot of P that"
            " already contains B, a hand nothing can beat returns at least half of P + B for a"
            " payment of B and the call gains at least (P - B) / 2. P always exceeds B, because"
            " a postflop pot holds the preflop money too. There is no price in that and no"
            " equity estimate, which is the whole reason this one path is allowed to invest."
        ),
        "",
        *wrapped(
            "The `hero holds` column is the evaluator's own category name. It has no separate"
            " royal-flush category, so a royal flush reads there as a straight flush. The `bad"
            " rivers` column applies to turn rows only, and is the number of river cards after"
            " which some holding beats hero; one is enough to fold."
        ),
        "",
        "### On the river, where the board is complete",
        "",
        *example_table_lines(RIVER_EXAMPLES),
        "",
        *example_prose_lines(RIVER_EXAMPLES),
        "### On the turn, where a card is still to come",
        "",
        *wrapped(
            "The turn claim is the stronger one: not 'no holding beats me now' but 'no holding"
            f" beats me after any river card'. It decomposes into {UNSEEN_RIVERS} river checks,"
            " one per card that can complete the board, so hero calls the turn only when every"
            f" one of them comes back safe. That is {UNSEEN_RIVERS} x {UNSEEN_HOLDINGS} ="
            f" {TURN_PAIRS:,} (river, holding) pairs for a single decision."
        ),
        "",
        *example_table_lines(TURN_EXAMPLES),
        "",
        *example_prose_lines(TURN_EXAMPLES),
        "### Why the flop is not on this list",
        "",
        *wrapped(
            "On the flop two cards are still to come, so the same claim runs over C(47,2) ="
            " 1,081 villain holdings against C(45,2) = 990 runouts: 1,070,190 evaluations for a"
            f" single decision, against {TURN_PAIRS:,} on the turn and {UNSEEN_HOLDINGS} on the"
            " river. That is roughly a thousand river checks where the turn is roughly"
            " forty-six, which is the whole difference between the two, and it is why the turn"
            " is here and the flop is not."
        ),
        "",
        *wrapped(
            "So a flop bet always takes the pot from this bot. That gap is recorded in"
            " `backlog.yml` as POSTFLOP-UNBEATABLE-EARLIER-STREETS rather than approximated,"
            " because a sampled version would turn the one fact this module rests on back into"
            " a guess."
        ),
    ]
    return lines


def build_query(
    point: DecisionPoint,
    hole_cards: tuple[str, str],
    history: tuple[SeatAction, ...],
) -> StrategyQuery:
    """Turn one replayed decision point into a query, in the shape Phase 03 defined.

    `current_bet` is the street's current bet level rather than hero's own contribution to
    it. Hero's own contribution is carried on hero's seat record and read from there, which
    is what the rest of the repo now does: the price to call is capped at what hero holds,
    so nothing computed from the level and the price is a contribution.

    Every per-seat figure is the replayer's own `PlayerState`, under the engine's four
    names, and the pot is the sum of those hand totals rather than a second number stated
    beside them.
    """
    state = point.turn.round
    player = state.player(point.seat)
    seated = sorted(state.players, key=lambda entry: entry.seat)
    return StrategyQuery(
        hand_id=point.hand.hand_id,
        street=point.street.value,
        seat=point.seat,
        button_seat=point.hand.button_seat,
        hole_cards=hole_cards,
        board=tuple(card_texts(point.board)),
        legal_actions=tuple(kind.value for kind in point.legal_actions),
        to_call=min(max(0, state.current_bet - player.street_bet), player.stack),
        current_bet=state.current_bet,
        min_raise_target=state.current_bet + state.min_raise,
        pot=sum(entry.committed_total for entry in seated),
        stacks=tuple((entry.seat, entry.stack) for entry in seated),
        seat_states=tuple(
            SeatState(
                seat=entry.seat,
                street_bet=entry.street_bet,
                committed_total=entry.committed_total,
                folded=entry.folded,
                all_in=entry.all_in,
            )
            for entry in seated
        ),
        blinds=(point.hand.blinds.small_blind, point.hand.blinds.big_blind),
        preflop_actions=history,
    )


@dataclass(frozen=True)
class SamplePoint:
    """One replayed decision point, with what the composite said about it."""

    hand_id: str
    street: str
    seat: int
    component: str
    verdict: str
    record: DecisionAuditRecord | None
    queried: bool


def preflop_history(points: list[DecisionPoint], index: int) -> tuple[SeatAction, ...]:
    """The preflop actions in front of this decision point.

    A preflop point sees only what came before it. A postflop point sees the whole
    preflop orbit, which is the real context even though the fallback never reads it: the
    chart needs the history to derive a spot key, and a query that carried a truncated
    one postflop would be a different query than the hand actually produced.

    The two blind posts are forced rather than chosen, so the replayer never offers them
    as decision points and they are absent here by construction, which is also what
    `SeatAction` requires - it knows nothing called `post_blind`.

    A raise carries the amount it raised to, which is what `HistoryAction.amount`
    already holds for a raise. Without it the chart cannot tell which price the spot
    was played at, which is the whole of `RAISE-SIZE-IN-SPOT-KEY`.
    """
    earlier = points[:index] if points[index].street.value == "preflop" else points
    return tuple(
        SeatAction(
            point.seat,
            point.action.kind.value,
            point.action.amount if point.action.kind.value == "raise" else None,
        )
        for point in earlier
        if point.street.value == "preflop"
    )


def sample_hand_points(composite: CompositeStrategy) -> list[SamplePoint]:
    """Drive every committed sample hand through the replayer and ask the composite."""
    collected: list[SamplePoint] = []
    for hand in load_hand_history_file(FIXTURE):
        points: list[DecisionPoint] = []
        replay_hand(hand, on_decision=points.append)
        hole_cards = {
            entry.seat: tuple(card_texts(entry.hole_cards)) for entry in hand.showdown
        }
        for index, point in enumerate(points):
            street = point.street.value
            component = composite.component_for(street)
            if point.seat not in hole_cards:
                collected.append(
                    SamplePoint(
                        hand.hand_id,
                        street,
                        point.seat,
                        component,
                        "not asked (this seat's hole cards are not recorded)",
                        None,
                        False,
                    )
                )
                continue
            query = build_query(point, hole_cards[point.seat], preflop_history(points, index))
            outcome = composite.decide(query)
            if isinstance(outcome, StrategyDecision):
                amount = f" {outcome.amount}" if outcome.amount is not None else ""
                verdict = f"{outcome.action}{amount}  ({outcome.code})"
            else:
                verdict = f"refused  ({outcome.code})"
            collected.append(
                SamplePoint(
                    hand.hand_id,
                    street,
                    point.seat,
                    component,
                    verdict,
                    audit_record(composite, query, outcome),
                    True,
                )
            )
    return collected


def composite_lines(points: list[SamplePoint]) -> list[str]:
    lines = [
        "## What the composite does over the committed sample hands",
        "",
        f"Fixture: `{FIXTURE.relative_to(REPO_ROOT)}`",
        "",
        *wrapped(
            "One strategy object plays the whole hand: preflop from the committed charts, flop"
            " through river from the fallback. Every recorded action in a hand is a decision"
            " point. A point can only be asked when the hand history records that seat's hole"
            " cards, which it does only for seats that reached showdown, so points belonging to"
            " a seat that folded earlier are skipped rather than guessed at."
        ),
        "",
        *wrapped(
            "These four hands were recorded to exercise the replayer, not to be preflop spots the"
            " six-handed 100bb charts cover, so the chart refuses every one of them. That is the"
            " behavior to want: a refusal carries its own reason code out to the caller instead"
            " of being quietly converted into a check."
        ),
        "",
    ]
    for hand_id in dict.fromkeys(point.hand_id for point in points):
        lines.append(f"  {hand_id}")
        for point in points:
            if point.hand_id != hand_id:
                continue
            lines.append(f"    {point.street:<8}seat {point.seat}   {point.verdict}")
        lines.append("")
    columns = (PREFLOP_COMPONENT, POSTFLOP_COMPONENT)
    rows: tuple[tuple[str, Callable[[SamplePoint], bool]], ...] = (
        ("decision points", lambda point: True),
        ("asked (hole cards recorded)", lambda point: point.queried),
        ("decisions", _is_decision),
        ("refusals", lambda point: point.queried and not _is_decision(point)),
        ("skipped (hole cards unknown)", lambda point: not point.queried),
    )
    lines += [
        *wrapped(
            "Broken out by which component answered. Preflop is the chart, flop through river is"
            " the fallback, and no query reaches both."
        ),
        "",
        f"{'':<32}{'preflop':>22}{'postflop':>22}",
        f"{'':<32}{PREFLOP_COMPONENT:>22}{POSTFLOP_COMPONENT:>22}",
        "",
    ]
    for label, predicate in rows:
        counts = [
            sum(1 for point in points if point.component == column and predicate(point))
            for column in columns
        ]
        lines.append(f"{label:<32}{counts[0]:>22}{counts[1]:>22}")
    codes: Counter[str] = Counter()
    for point in points:
        if point.record is not None and not isinstance(point.record.outcome, StrategyDecision):
            codes[point.record.outcome.code] += 1
    lines += ["", "Refusal codes, all of them from the chart and none from the fallback:", ""]
    for code, count in sorted(codes.items()):
        lines.append(f"  {code:<52}{count:>6}")
    lines += [
        "",
        *wrapped(
            "Read the per-hand listing above as the shape of a hand played by this bot: the chart"
            " speaks preflop or declines to, every postflop street checks through, and the hand"
            " is settled at showdown. Nothing bets and nothing raises after the flop."
        ),
    ]
    return lines


def _is_decision(point: SamplePoint) -> bool:
    return point.record is not None and isinstance(point.record.outcome, StrategyDecision)


def hand_check_lines(points: list[SamplePoint]) -> list[str]:
    """The one number a reviewer can recompute from a committed file without code."""
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    per_hand: list[tuple[str, list[tuple[str, int]]]] = []
    for hand in raw["hands"]:
        per_hand.append(
            (
                hand["hand_id"],
                [
                    (street["name"], len(street["actions"]))
                    for street in hand["streets"]
                    if street["name"] != "preflop"
                ],
            )
        )
    counted = sum(count for _, streets in per_hand for _, count in streets)
    replayed = sum(1 for point in points if point.street != "preflop")
    lines = [
        "## Check one number by hand",
        "",
        f"Postflop decision points across the committed sample hands: {counted}.",
        "",
        *wrapped(
            f"Open `{FIXTURE.relative_to(REPO_ROOT)}`. For each hand, go to `streets` and find the"
            " entries named `flop`, `turn` and `river`, ignoring `preflop`. Count the entries in"
            " each one's `actions` list and add them up. The replayer visits exactly one decision"
            " point per recorded action, so that tally is the number above."
        ),
        "",
    ]
    for hand_id, streets in per_hand:
        detail = ", ".join(f"{name} {count}" for name, count in streets) or "no postflop streets"
        lines.append(f"  {hand_id:<32}{detail:<40}{sum(count for _, count in streets):>4}")
    lines += [
        f"  {'total':<32}{'':<40}{counted:>4}",
        "",
        *wrapped(
            f"Counting the file by hand gives {counted}. Driving the same file through the replayer"
            f" and the composite reached {replayed} postflop decision points. The two agree, and"
            " the first of them needed no code at all."
        ),
        "",
        *wrapped(
            "The two `post_blind` entries that open every preflop street are deliberately not in"
            " this count. They are forced posts rather than decisions, and the replayer never"
            " offers them to a strategy."
        ),
    ]
    return lines


def audit_lines(records: list[DecisionAuditRecord], enumeration_count: int) -> list[str]:
    from_hands = len(records) - enumeration_count
    return [
        "## The committed decision audit",
        "",
        *wrapped(
            f"`{AUDIT_OUTPUT.relative_to(REPO_ROOT)}` holds one line per decision in the Phase 03"
            " record shape, written with the same serializer as the preflop audit, so the reader"
            " that already checks preflop decisions checks these unchanged."
        ),
        "",
        f"  from the enumeration                              {enumeration_count:>6}",
        f"  from the sample hands (postflop only)             {from_hands:>6}",
        f"  total lines                                       {len(records):>6}",
        "",
        *wrapped(
            "Refusals are counted in this report and are deliberately not written to that file."
            " The record shape does accept a refusal, but a decision audit whose lines are not all"
            " decisions is a file every future reader has to filter before trusting a count, and"
            " the preflop refusals worth auditing are already Phase 05's own evidence."
        ),
        "",
        *wrapped(
            "Every line was constructed through `DecisionAuditRecord`, which is what proves"
            " legality: it rejects an action outside `legal_actions`, an amount above all-in, and"
            " an amount below the minimum raise target. A decision that was not legal could not"
            " have been written to the file."
        ),
    ]


def render() -> tuple[str, str]:
    fallback = PostflopFallbackStrategy()
    composite = CompositeStrategy.from_repo()
    shapes = engine_shapes()
    decided = tuple(
        (query, fallback.decide(query)) for query in enumeration_queries(shapes)
    )
    records = [
        audit_record(fallback, query, outcome)
        for query, outcome in decided
        if isinstance(outcome, StrategyDecision)
    ]
    enumeration_count = len(records)
    points = sample_hand_points(composite)
    records += [
        point.record
        for point in points
        if point.street != "preflop" and _is_decision(point) and point.record is not None
    ]
    sections = [
        header_lines(fallback, composite),
        enumeration_lines(shapes, decided),
        worked_example_lines(),
        composite_lines(points),
        hand_check_lines(points),
        audit_lines(records, enumeration_count),
    ]
    body: list[str] = []
    for section in sections:
        body.extend(section)
        body.append("")
    body.append("Generated by `scripts/generate_postflop_fallback_report.py`.")
    return "\n".join(body) + "\n", records_to_jsonl(records)


def main() -> int:
    report_text, audit_jsonl = render()
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(report_text, encoding="utf-8")
    AUDIT_OUTPUT.write_text(audit_jsonl, encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT.relative_to(REPO_ROOT)}")
    print(f"wrote {AUDIT_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
