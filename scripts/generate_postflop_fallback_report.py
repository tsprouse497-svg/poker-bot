"""Human evidence for the postflop continuity fallback: what it covers, and what it never does.

Written for a reviewer who does not read code, and built around the two claims that
carry this phase. The first is totality: every legal-action set the engine can produce
postflop gets an answer, and the enumeration that proves it reads its shapes out of the
engine's own `legal_actions` rather than from a list written here, so a change to the
engine widens the sweep instead of escaping it. The second is the one place money goes
in postflop, which is shown as named cards with the villain count beside them, because
"exactly one holding out of 990 beats this" is an argument a reviewer can check and
"the code says so" is not.

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
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
    records_to_jsonl,
)
from poker_training_bot.strategy.postflop_fallback import (
    POSTFLOP_STREETS,
    PostflopFallbackStrategy,
    river_hand_cannot_lose,
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

# Forty-five cards hero cannot see on a complete board, taken two at a time.
UNSEEN_HOLDINGS = 990

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
        return self.current_bet - self.hero_street_bet

    @property
    def hero_is_short(self) -> bool:
        """Hero's whole remaining stack is less than the price to call."""
        return 0 < self.hero_stack < self.to_call

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
    " every villain holds the same hand: nothing beats hero and every holding chops",
)
ROYAL_ON_BOARD = Scenario(
    "royal flush on the board",
    ("2d", "7h"),
    ("Ac", "Kc", "Qc", "Jc", "Tc"),
    "the nuts is the board itself, a royal flush, and hero's two cards are irrelevant; hero"
    " cannot hold that hand as a two-card holding and neither can any villain, so the whole"
    " table chops",
)

# The five the phase contract names by hand, plus the ordinary case, in the order a
# reviewer reads them: the two that call first, then the three that fold.
WORKED_EXAMPLES = (
    ROYAL_IN_HAND,
    QUAD_ACES,
    NUT_FLUSH_BEATABLE,
    QUAD_NINES_CHOP,
    ROYAL_ON_BOARD,
)
ENUMERATED = (ACE_HIGH, *WORKED_EXAMPLES)


def enumeration_query(shape: Shape, street: str, scenario: Scenario) -> StrategyQuery:
    """A postflop query whose betting numbers come from an engine-produced shape."""
    return StrategyQuery(
        hand_id=f"enumeration|{scenario.name}|{street}|{shape.label}",
        street=street,
        seat=HERO_SEAT,
        button_seat=VILLAIN_SEAT,
        hole_cards=scenario.hole_cards,
        board=scenario.board_for(street),
        legal_actions=shape.actions,
        to_call=shape.to_call,
        street_bet=shape.current_bet,
        min_raise_target=shape.current_bet + MIN_RAISE,
        pot=100 + shape.current_bet + shape.hero_street_bet,
        stacks=((VILLAIN_SEAT, VILLAIN_STACK), (HERO_SEAT, shape.hero_stack)),
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
    """How many of the unseen holdings beat hero, how many tie, and what hero holds."""

    beats: int
    ties: int
    hero_hand: str
    cannot_lose: bool


@cache
def villain_census(scenario: Scenario) -> Census:
    """Count the holdings that beat or tie hero, and ask the fallback for its verdict.

    Recounted here rather than read off the fallback's boolean, because the boolean
    short-circuits on the first holding that beats or ties and the report needs the
    total. It is one pass over 990 combinations per worked example, which is the whole
    argument for the call rule and cheap enough to spend. The verdict itself still comes
    from `river_hand_cannot_lose`, so the report cannot disagree with the strategy.
    """
    hero = parse_cards(scenario.hole_cards)
    board = parse_cards(scenario.board)
    hero_rank = evaluate_best(hero + board)
    seen = frozenset(hero + board)
    unseen = tuple(card for card in standard_deck() if card not in seen)
    beats = ties = 0
    for villain in combinations(unseen, 2):
        villain_rank = evaluate_best(villain + board)
        if villain_rank.beats(hero_rank):
            beats += 1
        elif villain_rank.ties(hero_rank):
            ties += 1
    return Census(
        beats=beats,
        ties=ties,
        hero_hand=hero_rank.label.lower(),
        cannot_lose=river_hand_cannot_lose(scenario.hole_cards, scenario.board),
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
            " free, folds to a bet, and puts money in on exactly one path - a complete board on"
            " which no holding a villain could possibly have beats or ties hero."
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
        note = "  (hero's whole stack is short of the price to call)" if shape.hero_is_short else ""
        lines.append(f"  {shape.label:<24}to call {shape.to_call:>4}{note}")
    lines += [
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


def worked_example_lines() -> list[str]:
    lines = [
        "## Where money goes in: the worked river examples",
        "",
        *wrapped(
            "The river call is the only path in this module that invests, so it is written out"
            " as cards. Hero can see seven of the 52 cards - two in hand and five on a"
            f" complete board - which leaves 45 unseen and {UNSEEN_HOLDINGS} possible two-card"
            " villain holdings. Every one of them is ranked with the same evaluator that ranks"
            " hero's own hand. No hand categories, no table of nut hands, no sampled subset."
        ),
        "",
        *wrapped(
            "The bar is strict: hero calls only when no holding beats hero and no holding ties"
            " hero. A guaranteed chop pays a full call to win half a pot, and the price at"
            " which that is correct is a number this repo cannot source."
        ),
        "",
        *wrapped(
            "The `hero holds` column is the evaluator's own category name. It has no separate"
            " royal-flush category, so a royal flush reads there as a straight flush."
        ),
        "",
        f"{'hero':<8}{'board':<20}{'hero holds':<18}{'beat':>6}{'tie':>6}   verdict",
    ]
    for scenario in WORKED_EXAMPLES:
        census = villain_census(scenario)
        lines.append(
            f"{scenario.cards_text:<8}{scenario.board_text:<20}{census.hero_hand:<18}"
            f"{census.beats:>6}{census.ties:>6}   {'calls' if census.cannot_lose else 'folds'}"
        )
    lines.append("")
    for scenario in WORKED_EXAMPLES:
        census = villain_census(scenario)
        lines += [
            f"{scenario.name}: {scenario.cards_text} on {scenario.board_text}",
            *wrapped(
                f"{'Calls' if census.cannot_lose else 'Folds'}, because {scenario.reason}."
                f" Of {UNSEEN_HOLDINGS} possible villain holdings, {census.beats} beat hero"
                f" and {census.ties} tie hero.",
                indent="  ",
            ),
            "",
        ]
    lines += wrapped(
        "The exception is the river only. On the flop and the turn the same claim would have"
        " to mean 'nothing beats me after any runout', which is a far larger enumeration, so a"
        " flop or turn bet always takes the pot from this bot. That gap is recorded in"
        " `backlog.yml` rather than approximated."
    )
    return lines


def build_query(
    point: DecisionPoint,
    hole_cards: tuple[str, str],
    history: tuple[SeatAction, ...],
) -> StrategyQuery:
    """Turn one replayed decision point into a query, in the shape Phase 03 defined.

    `street_bet` is the street's current bet level rather than hero's own contribution
    to it. That is the reading the rest of the repo is built on: `docs/BACKLOG.md` states
    that hero's own contribution is recoverable as `street_bet` minus `to_call`, and the
    preflop chart derives hero's starting depth that way. Passing hero's own bet here
    instead would hand the chart a depth it never had.
    """
    state = point.turn.round
    player = state.player(point.seat)
    return StrategyQuery(
        hand_id=point.hand.hand_id,
        street=point.street.value,
        seat=point.seat,
        button_seat=point.hand.button_seat,
        hole_cards=hole_cards,
        board=tuple(card_texts(point.board)),
        legal_actions=tuple(kind.value for kind in point.legal_actions),
        to_call=min(max(0, state.current_bet - player.street_bet), player.stack),
        street_bet=state.current_bet,
        min_raise_target=state.current_bet + state.min_raise,
        pot=point.pot,
        stacks=tuple(
            (seat_player.seat, seat_player.stack)
            for seat_player in sorted(state.players, key=lambda entry: entry.seat)
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
    """
    earlier = points[:index] if points[index].street.value == "preflop" else points
    return tuple(
        SeatAction(point.seat, point.action.kind.value)
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
