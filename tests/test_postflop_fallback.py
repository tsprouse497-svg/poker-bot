"""Postflop fallback tests, written from the contract before the implementation existed.

What this file pins is the one thing a continuity device has to be: total, legal, and
never inventing an investment. Three properties carry most of the weight.

`TestTotalityAndLegality` proves coverage by enumeration rather than by sampling, and the
shapes it enumerates are read out of the engine's own `legal_actions` rather than listed
here, so the sweep follows the engine if the engine changes. Legality is not asserted by
eye: every decision goes through the Phase 03 `DecisionAuditRecord`, which rejects an
action outside `legal_actions`, an amount above all-in, and one below the minimum raise.

`TestUnbeatableFunction` covers the only place this bot puts money in postflop, as named
cards a reviewer can check by hand. Two bars are pinned there: a tie is not a loss, so a
hand every holding chops calls; and the turn claim has to survive every river card rather
than only the board as it stands.

`TestComposite` pins that the composite adds no decision of its own: for every query in
the enumeration its outcome is the outcome its component returns when asked directly, and
a preflop chart refusal comes back as a refusal carrying its original code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from poker_training_bot.poker_core.cards import Card
from poker_training_bot.poker_core.engine import BettingRoundState, PlayerState
from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.strategy.composite import CompositeStrategy
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    StrategyDecision,
    StrategyProtocol,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.postflop_fallback import (
    CODE_CALL_UNBEATABLE,
    CODE_CHECK,
    CODE_FOLD_CAN_LOSE,
    CODE_FOLD_ON_THE_FLOP,
    REFUSE_NOT_POSTFLOP,
    PostflopFallbackStrategy,
    hand_cannot_lose,
)

POSTFLOP_STREETS = ("flop", "turn", "river")
BOARD_SIZES = {"flop": 3, "turn": 4, "river": 5}

SMALL_BLIND = 10
BIG_BLIND = 20
MIN_RAISE = BIG_BLIND
HERO_SEAT = 1
VILLAIN_SEAT = 0
VILLAIN_STACK = 500

FALLBACK_PREFIX = "postflop-fallback:"
CHART_PREFIX = "preflop-chart:"


@dataclass(frozen=True)
class Shape:
    """One postflop betting shape, together with the legal-action set it produced.

    The action set is not written down here: it is whatever `legal_actions` returned
    for the engine state described by the other three fields.
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


def _engine_shapes() -> tuple[Shape, ...]:
    """Every non-empty legal-action set the engine can produce for a postflop seat.

    A sweep over the engine rather than a hard-coded list, so a change to
    `BettingRoundState.legal_actions` widens this test instead of silently escaping it.
    An empty action set is skipped: a folded or all-in seat is never asked to decide,
    and `StrategyQuery` rejects empty `legal_actions` outright.
    """
    found: dict[tuple[str, ...], Shape] = {}
    for current_bet in (0, MIN_RAISE, 3 * MIN_RAISE):
        for hero_street_bet in (0, MIN_RAISE, 3 * MIN_RAISE):
            if hero_street_bet > current_bet:
                continue
            for hero_stack in (0, MIN_RAISE // 2, MIN_RAISE, 20 * MIN_RAISE):
                hero = PlayerState(
                    seat=HERO_SEAT,
                    name="hero",
                    stack=hero_stack,
                    hole_cards=(Card("A", "s"), Card("K", "d")),
                    committed_total=hero_street_bet,
                    street_bet=hero_street_bet,
                )
                villain = PlayerState(
                    seat=VILLAIN_SEAT,
                    name="villain",
                    stack=VILLAIN_STACK,
                    hole_cards=(),
                    committed_total=current_bet,
                    street_bet=current_bet,
                )
                state = BettingRoundState(
                    players=(villain, hero),
                    current_bet=current_bet,
                    min_raise=MIN_RAISE,
                )
                actions = tuple(kind.value for kind in state.legal_actions(HERO_SEAT))
                if actions and actions not in found:
                    found[actions] = Shape(actions, current_bet, hero_street_bet, hero_stack)
    return tuple(found[key] for key in sorted(found))


SHAPES = _engine_shapes()
FREE_SHAPES = tuple(shape for shape in SHAPES if "check" in shape.actions)
FACING_SHAPES = tuple(shape for shape in SHAPES if "call" in shape.actions)


def shape_with(*actions: str) -> Shape:
    wanted = frozenset(actions)
    for shape in SHAPES:
        if frozenset(shape.actions) == wanted:
            return shape
    raise AssertionError(f"the engine produces no postflop action set {sorted(wanted)}")


@dataclass(frozen=True)
class Scenario:
    """Hero's two cards and a complete five-card board, sliced back per street."""

    name: str
    hole_cards: tuple[str, ...]
    board: tuple[str, ...]

    def board_for(self, street: str) -> tuple[str, ...]:
        return self.board[: BOARD_SIZES[street]]


# Ace high and nothing else: hero is beaten by most of the deck on every street.
WEAK = Scenario("ace-high", ("As", "Kd"), ("2c", "7h", "Ts", "4d", "9s"))

# A royal flush in clubs from the flop onwards. Nothing can beat it and nothing can
# tie it, because a tie needs Ac and Kc and hero holds both. Used to prove that a
# hand which cannot lose still folds to a bet before the river.
NUTS = Scenario("royal-flush-in-hand", ("Ac", "Kc"), ("Qc", "Jc", "Tc", "2d", "3h"))

# Nut flush, beaten by exactly one villain holding: 6d5d makes 2d3d4d5d6d.
BEATABLE = Scenario("nut-flush-one-combo-behind", ("Ad", "Kd"), ("2d", "3d", "4d", "5h", "Kc"))

# Quad nines with the ace kicker already on the board: no holding beats hero and every
# holding ties hero. A chop is not a loss, so this calls.
CHOP_ONLY = Scenario("quads-and-kicker-on-board", ("Kd", "Qh"), ("9c", "9d", "9h", "9s", "Ac"))

# The nuts is the board itself, a royal flush hero cannot possibly hold as two cards,
# and neither can anybody else, so the whole table chops and hero calls.
BOARD_NUTS = Scenario("royal-flush-on-board", ("2d", "7h"), ("Ac", "Kc", "Qc", "Jc", "Tc"))

# Quad aces holding the fourth ace, so no villain can make the same quads.
QUAD_ACES = Scenario("quad-aces-fourth-ace-in-hand", ("Ac", "2c"), ("As", "Ah", "Ad", "Kc", "Kd"))

# The pair that separates the turn from the river. Hero holds the jack-high straight. On
# the turn - 9c 8c 7h 6d - nothing beats it yet, but two clubs are showing, so a club river
# would hand any two clubs a flush, and the turn claim has to survive every river card. The
# river came 2h instead, so the same cards call. Opposite answers, one card apart.
TURN_BREAKS = Scenario(
    "straight-a-club-river-would-break", ("Th", "Jd"), ("9c", "8c", "7h", "6d", "2h")
)

ENUMERATED = (WEAK, NUTS)

SUIT_SWAP = {"c": "d", "d": "c", "h": "s", "s": "h"}


def relabel(cards: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(card[0] + SUIT_SWAP[card[1]] for card in cards)


def relabelled(scenario: Scenario) -> Scenario:
    """The same hand under a consistent suit permutation, so poker value is unchanged."""
    return Scenario(
        f"{scenario.name}-relabelled",
        relabel(scenario.hole_cards),
        relabel(scenario.board),
    )


def query(shape: Shape, street: str, scenario: Scenario, **overrides: Any) -> StrategyQuery:
    """A postflop query whose betting numbers come from an engine-produced shape."""
    fields: dict[str, Any] = {
        "hand_id": f"{scenario.name}|{street}|{'-'.join(shape.actions)}",
        "street": street,
        "seat": HERO_SEAT,
        "button_seat": VILLAIN_SEAT,
        "hole_cards": scenario.hole_cards,
        "board": scenario.board_for(street),
        "legal_actions": shape.actions,
        "to_call": shape.to_call,
        "street_bet": shape.current_bet,
        "min_raise_target": shape.current_bet + MIN_RAISE,
        "pot": 100 + shape.current_bet + shape.hero_street_bet,
        "stacks": ((VILLAIN_SEAT, VILLAIN_STACK), (HERO_SEAT, shape.hero_stack)),
        "blinds": (SMALL_BLIND, BIG_BLIND),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def enumeration_queries() -> tuple[StrategyQuery, ...]:
    return tuple(
        query(shape, street, scenario)
        for shape in SHAPES
        for street in POSTFLOP_STREETS
        for scenario in ENUMERATED
    )


PREFLOP_SEATS = (0, 1, 2, 3, 4, 5)
PREFLOP_BUTTON = 3
PREFLOP_SB = 50
PREFLOP_BB = 100


def preflop_seat_of(position: str) -> int:
    for seat in PREFLOP_SEATS:
        if position_for_seat(PREFLOP_SEATS, PREFLOP_BUTTON, seat) == position:
            return seat
    raise AssertionError(f"no seat holds {position}")


def preflop_query(hole_cards: tuple[str, ...] = ("As", "Ah"), **overrides: Any) -> StrategyQuery:
    """An unopened six-handed 100bb preflop spot the committed charts cover."""
    hero = preflop_seat_of("LJ")
    posted = {preflop_seat_of("SB"): PREFLOP_SB, preflop_seat_of("BB"): PREFLOP_BB}
    full = 100 * PREFLOP_BB
    fields: dict[str, Any] = {
        "hand_id": "preflop-hand",
        "street": "preflop",
        "seat": hero,
        "button_seat": PREFLOP_BUTTON,
        "hole_cards": hole_cards,
        "board": (),
        "legal_actions": ("fold", "call", "raise"),
        "to_call": PREFLOP_BB,
        "street_bet": PREFLOP_BB,
        "min_raise_target": 2 * PREFLOP_BB,
        "pot": PREFLOP_SB + PREFLOP_BB,
        "stacks": tuple((seat, full - posted.get(seat, 0)) for seat in PREFLOP_SEATS),
        "blinds": (PREFLOP_SB, PREFLOP_BB),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def uncovered_preflop_query() -> StrategyQuery:
    """A 40bb table: no committed chart holds that depth, so the chart refuses."""
    return preflop_query(stacks=tuple((seat, 40 * PREFLOP_BB) for seat in PREFLOP_SEATS))


def decision(outcome: Any) -> StrategyDecision:
    assert isinstance(outcome, StrategyDecision), outcome
    return outcome


def refusal(outcome: Any) -> StrategyRefusal:
    assert isinstance(outcome, StrategyRefusal), outcome
    return outcome


def audit(strategy: Any, request: StrategyQuery, outcome: Any) -> DecisionAuditRecord:
    return DecisionAuditRecord(
        schema_version=DECISION_AUDIT_SCHEMA_VERSION,
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.strategy_version,
        query=request,
        outcome=outcome,
    )


@pytest.fixture(scope="module")
def fallback() -> PostflopFallbackStrategy:
    return PostflopFallbackStrategy()


@pytest.fixture(scope="module")
def composite() -> CompositeStrategy:
    return CompositeStrategy.from_repo()


@pytest.fixture(scope="module")
def enumerated(fallback) -> tuple[tuple[StrategyQuery, Any], ...]:
    """Every engine-legal postflop shape, at every street, decided once."""
    return tuple((request, fallback.decide(request)) for request in enumeration_queries())


class TestOutcomeCodes:
    # Every outcome names the component that produced it, so an audit line can be
    # attributed without reading code.
    def test_every_code_names_the_fallback(self) -> None:
        codes = (
            REFUSE_NOT_POSTFLOP,
            CODE_CHECK,
            CODE_CALL_UNBEATABLE,
            CODE_FOLD_ON_THE_FLOP,
            CODE_FOLD_CAN_LOSE,
        )

        assert all(code.startswith(FALLBACK_PREFIX) for code in codes)
        assert len(set(codes)) == len(codes)


class TestStreetRouting:
    # The fallback answers flop, turn and river only. A preflop spot always has
    # either a chart answer or a chart gap, and this phase is neither.
    def test_a_preflop_query_refuses_with_its_own_code(self, fallback) -> None:
        outcome = fallback.decide(preflop_query())

        assert refusal(outcome).code == REFUSE_NOT_POSTFLOP

    def test_a_preflop_query_never_comes_back_as_an_action(self, fallback) -> None:
        """A passive action here would be a second, silent preflop strategy."""
        for hole_cards in (("As", "Ah"), ("7d", "2c")):
            for legal in (("fold", "call", "raise"), ("check", "raise")):
                to_call = 0 if "check" in legal else PREFLOP_BB
                outcome = fallback.decide(
                    preflop_query(hole_cards=hole_cards, legal_actions=legal, to_call=to_call)
                )

                assert not isinstance(outcome, StrategyDecision), outcome

    def test_all_three_postflop_streets_are_answered(self, fallback) -> None:
        for street in POSTFLOP_STREETS:
            outcome = fallback.decide(query(shape_with("check", "bet"), street, WEAK))

            assert isinstance(outcome, StrategyDecision), street


class TestChecksWheneverFree:
    # It checks whenever checking is legal, on every postflop street.
    def test_it_checks_on_every_street_whenever_checking_is_legal(self, fallback) -> None:
        for shape in FREE_SHAPES:
            for street in POSTFLOP_STREETS:
                for scenario in ENUMERATED:
                    outcome = decision(fallback.decide(query(shape, street, scenario)))

                    assert outcome.action == "check", (shape.actions, street, scenario.name)
                    assert outcome.code == CODE_CHECK


class TestNeverAggresses:
    # It never bets and never raises, at any street, in any spot: aggression needs a
    # sizing source and the repo has none postflop.
    def test_it_never_bets_where_betting_is_legal(self, fallback) -> None:
        shape = shape_with("check", "bet")
        for street in POSTFLOP_STREETS:
            outcome = decision(fallback.decide(query(shape, street, NUTS)))

            assert outcome.action == "check", street
            assert outcome.amount is None

    def test_it_never_raises_where_raising_is_legal(self, fallback) -> None:
        for shape in (shape_with("check", "raise"), shape_with("fold", "call", "raise")):
            for street in POSTFLOP_STREETS:
                outcome = decision(fallback.decide(query(shape, street, NUTS)))

                assert outcome.action != "raise", (shape.actions, street)
                assert outcome.amount is None

    def test_no_decision_in_the_enumeration_bets_or_raises(self, enumerated) -> None:
        aggressive = [
            (request.street, request.legal_actions, outcome.action)
            for request, outcome in enumerated
            if isinstance(outcome, StrategyDecision) and outcome.action in {"bet", "raise"}
        ]

        assert aggressive == []


class TestFacingABet:
    # Facing a bet it folds, with exactly one exception on the turn and the river.
    def test_it_folds_facing_a_bet_on_the_flop(self, fallback) -> None:
        for shape in FACING_SHAPES:
            outcome = decision(fallback.decide(query(shape, "flop", WEAK)))

            assert outcome.action == "fold", shape.actions
            assert outcome.code == CODE_FOLD_ON_THE_FLOP

    # Decision item 3: the flop is out of reach, so however strong the hand, the fold
    # there is unconditional rather than the enumeration returning False. The honest
    # claim needs both remaining cards enumerated, over a million evaluations for one
    # decision, and a sampled version would turn the fact back into a guess.
    def test_no_hand_calls_on_the_flop(self, fallback) -> None:
        for scenario in (WEAK, NUTS, BEATABLE, CHOP_ONLY, BOARD_NUTS, QUAD_ACES, TURN_BREAKS):
            for shape in FACING_SHAPES:
                outcome = decision(fallback.decide(query(shape, "flop", scenario)))

                assert outcome.action == "fold", (scenario.name, shape.actions)
                assert outcome.code == CODE_FOLD_ON_THE_FLOP

    # The single exception, proved by example: a royal flush in hand on a complete
    # board beats every holding a villain could have, so it calls.
    def test_it_calls_on_the_river_when_no_holding_can_beat_it(self, fallback) -> None:
        for shape in FACING_SHAPES:
            outcome = decision(fallback.decide(query(shape, "river", NUTS)))

            assert outcome.action == "call", shape.actions
            assert outcome.code == CODE_CALL_UNBEATABLE

    # Proved in the other direction: 6d5d makes 2d3d4d5d6d and beats hero's nut
    # flush, so one combination out of 990 is enough to fold.
    def test_it_folds_on_the_river_when_one_holding_beats_it(self, fallback) -> None:
        for shape in FACING_SHAPES:
            outcome = decision(fallback.decide(query(shape, "river", BEATABLE)))

            assert outcome.action == "fold", shape.actions
            assert outcome.code == CODE_FOLD_CAN_LOSE

    # Decision item 2, re-ruled at stage 8. Quad nines with the ace kicker on the board
    # cannot be beaten and cannot be improved on, and a royal flush on the board is the
    # same situation with the whole table playing it: nothing beats hero and everything
    # chops. A chop is not a loss - the pot returns the villain's bet along with a share
    # of the money already in the middle, so calling gains at least (pot - to_call) / 2
    # whatever the price. Folding these was a certain loss dressed as caution.
    def test_it_calls_on_the_river_when_the_best_villain_hand_is_a_chop(self, fallback) -> None:
        for scenario in (CHOP_ONLY, BOARD_NUTS):
            for shape in FACING_SHAPES:
                outcome = decision(fallback.decide(query(shape, "river", scenario)))

                assert outcome.action == "call", (scenario.name, shape.actions)
                assert outcome.code == CODE_CALL_UNBEATABLE

    # Regression test for the stage 8 blocker itself, stated as the arithmetic rather
    # than as an expected action. Folding a hand no holding can beat gives up half of
    # what is already in the middle, and the enumerated pot makes that a real number.
    def test_folding_a_guaranteed_chop_would_give_up_half_the_dead_money(
        self, fallback
    ) -> None:
        shape = shape_with("fold", "call", "raise")
        request = query(shape, "river", CHOP_ONLY)

        assert hand_cannot_lose(request.hole_cards, request.board) is True
        assert request.pot > request.to_call
        forgone = (request.pot - request.to_call) / 2

        assert forgone == 50
        assert decision(fallback.decide(request)).action == "call"

    # Decision item 3, re-ruled at stage 8: the exception reaches the turn, where the
    # claim is stronger because it has to hold after every river card.
    def test_it_calls_on_the_turn_when_no_river_card_can_break_the_hand(self, fallback) -> None:
        for shape in FACING_SHAPES:
            outcome = decision(fallback.decide(query(shape, "turn", NUTS)))

            assert outcome.action == "call", shape.actions
            assert outcome.code == CODE_CALL_UNBEATABLE

    # The other direction on the turn, and the reason the turn claim is not the river
    # claim: nothing beats hero on the board as it stands, and a club river would.
    def test_it_folds_on_the_turn_when_one_river_card_would_break_the_hand(
        self, fallback
    ) -> None:
        for shape in FACING_SHAPES:
            outcome = decision(fallback.decide(query(shape, "turn", TURN_BREAKS)))

            assert outcome.action == "fold", shape.actions
            assert outcome.code == CODE_FOLD_CAN_LOSE

    # Same cards, opposite answers, one card apart. This is the pair that proves the
    # turn test is not just the river test run early.
    def test_the_same_hand_folds_the_turn_and_calls_the_river(self, fallback) -> None:
        shape = shape_with("fold", "call", "raise")

        assert decision(fallback.decide(query(shape, "turn", TURN_BREAKS))).action == "fold"
        assert decision(fallback.decide(query(shape, "river", TURN_BREAKS))).action == "call"

    # The enumeration must include a hero whose whole remaining stack is less than
    # the price to call, and that hero still gets a legal decision.
    def test_a_hero_all_in_for_less_than_the_price_to_call_still_decides(
        self, fallback
    ) -> None:
        shape = shape_with("fold", "call")

        assert shape.hero_is_short, shape

        for street, scenario, expected in (
            ("flop", WEAK, "fold"),
            ("turn", NUTS, "call"),
            ("river", NUTS, "call"),
        ):
            request = query(shape, street, scenario)
            outcome = decision(fallback.decide(request))

            assert outcome.action == expected, street
            audit(fallback, request, outcome)


# The worked examples, each with the one-line reason for its verdict. Table-driven so the
# reason travels with the cards and is also the assertion message, and so adding a street
# or a hand is a row rather than a copied test. The full argument for each, spelled out at
# length for a non-coding reviewer, is in the committed fallback report.
UNBEATABLE_EXAMPLES = (
    (NUTS, "river", True, "royal flush in clubs; a tie needs Ac Kc and hero holds both"),
    (QUAD_ACES, "river", True, "quad aces holding the fourth ace; the board makes no flush"),
    (CHOP_ONLY, "river", True, "quad nines and the ace kicker all on board: everyone chops"),
    (BOARD_NUTS, "river", True, "the board is a royal flush, so the whole table chops"),
    (BEATABLE, "river", False, "nut flush, and 6d 5d makes 2d 3d 4d 5d 6d: one combo is enough"),
    (NUTS, "turn", True, "royal flush already made, so no river card can beat or tie it"),
    (TURN_BREAKS, "turn", False, "nothing beats the straight yet, but a club river makes a flush"),
    (TURN_BREAKS, "river", True, "the club missed, so nothing beats the straight any more"),
)


class TestUnbeatableFunction:
    """Worked examples, written so a reviewer can check them against the cards."""

    @pytest.mark.parametrize(("scenario", "street", "expected", "why"), UNBEATABLE_EXAMPLES)
    def test_a_worked_example_decides_the_way_its_reason_says(
        self, scenario, street, expected, why
    ) -> None:
        cards = f"{' '.join(scenario.hole_cards)} on {' '.join(scenario.board_for(street))}"

        assert hand_cannot_lose(scenario.hole_cards, scenario.board_for(street)) is expected, (
            f"{street}, {cards}: {why}"
        )

    # The claim is decidable on a turn or a river board and nowhere else, so a flop
    # board or a malformed one is an error rather than a guess.
    def test_a_board_that_is_not_a_turn_or_a_river_raises(self) -> None:
        for board in (
            (),
            ("Qc", "Jc", "Tc"),
            ("Qc", "Jc", "Tc", "2d", "3h", "4h"),
        ):
            with pytest.raises(ValueError):
                hand_cannot_lose(("Ad", "Kd"), board)


class TestTotalityAndLegality:
    """Totality by exhaustive enumeration over engine-legal states, not by sampling."""

    def test_the_engine_shapes_cover_the_free_and_facing_a_bet_forms(self) -> None:
        """Guards the sweep itself: a broken derivation would enumerate nothing."""
        assert {shape.actions for shape in FREE_SHAPES} == {
            ("check", "bet"),
            ("check", "raise"),
        }
        assert {shape.actions for shape in FACING_SHAPES} == {
            ("fold", "call"),
            ("fold", "call", "raise"),
        }
        assert any(shape.hero_is_short for shape in SHAPES)

    def test_every_engine_legal_postflop_state_returns_a_decision(self, enumerated) -> None:
        missing = [
            (request.street, request.legal_actions)
            for request, outcome in enumerated
            if not isinstance(outcome, StrategyDecision)
        ]

        assert missing == []
        assert len(enumerated) == len(SHAPES) * len(POSTFLOP_STREETS) * len(ENUMERATED)

    def test_it_never_refuses_postflop(self, enumerated) -> None:
        refusals = [outcome for _, outcome in enumerated if isinstance(outcome, StrategyRefusal)]

        assert refusals == []

    # Legality is proved by the Phase 03 record, which rejects an action outside
    # legal_actions, an amount above all-in, and an amount below the minimum raise.
    def test_every_decision_passes_the_decision_audit_record(self, fallback, enumerated) -> None:
        for request, outcome in enumerated:
            audit(fallback, request, outcome)

    def test_every_decision_code_names_the_fallback(self, enumerated) -> None:
        for _, outcome in enumerated:
            assert outcome.code.startswith(FALLBACK_PREFIX), outcome


class TestInvarianceAndDeterminism:
    # Two queries that differ only by a consistent suit permutation decide the same.
    # The turn case uses the hand a club river breaks, because relabelling moves which
    # suit that is and the answer still has to come back the same.
    def test_a_consistent_suit_relabelling_does_not_change_the_decision(self, fallback) -> None:
        for shape in (shape_with("fold", "call", "raise"), shape_with("check", "bet")):
            for street, scenario in (("flop", NUTS), ("turn", TURN_BREAKS), ("river", NUTS)):
                original = decision(fallback.decide(query(shape, street, scenario)))
                swapped = decision(fallback.decide(query(shape, street, relabelled(scenario))))

                assert (original.action, original.code) == (swapped.action, swapped.code)

    # Two queries that differ only by the order of the hole cards decide the same.
    def test_hole_card_order_does_not_change_the_decision(self, fallback) -> None:
        shape = shape_with("fold", "call", "raise")
        for street, scenario in (
            ("river", NUTS),
            ("river", BEATABLE),
            ("river", CHOP_ONLY),
            ("turn", TURN_BREAKS),
        ):
            reversed_scenario = Scenario(
                f"{scenario.name}-reversed",
                tuple(reversed(scenario.hole_cards)),
                scenario.board,
            )
            forwards = decision(fallback.decide(query(shape, street, scenario)))
            backwards = decision(fallback.decide(query(shape, street, reversed_scenario)))

            assert (forwards.action, forwards.code) == (backwards.action, backwards.code)

    # Decisions are byte-deterministic: the same query serializes to the same audit
    # line on every run.
    def test_the_same_query_serializes_to_the_same_audit_line(self, fallback) -> None:
        shape = shape_with("fold", "call", "raise")
        request = query(shape, "river", NUTS)
        other = query(shape, "flop", WEAK)
        lines = set()
        for _ in range(3):
            lines.add(audit(fallback, request, fallback.decide(request)).to_json_line())
            fallback.decide(other)

        assert len(lines) == 1

    def test_the_fallback_holds_no_state_between_calls(self, fallback) -> None:
        """A fresh instance answers identically after the shared one has been used."""
        shape = shape_with("fold", "call", "raise")
        request = query(shape, "river", BEATABLE)
        fresh = PostflopFallbackStrategy()

        assert fresh == fallback
        assert fresh.decide(request) == fallback.decide(request)


class TestComposite:
    def test_it_satisfies_the_strategy_protocol(self, composite) -> None:
        assert isinstance(composite, StrategyProtocol)
        assert composite.strategy_id
        assert composite.strategy_version > 0

    # One place decides which component owns a street.
    def test_component_for_routes_preflop_to_the_chart_and_the_rest_to_the_fallback(
        self, composite
    ) -> None:
        assert composite.component_for("preflop") == "preflop-chart"
        for street in POSTFLOP_STREETS:
            assert composite.component_for(street) == "postflop-fallback"

    def test_a_preflop_query_is_answered_by_the_chart(self, composite) -> None:
        outcome = decision(composite.decide(preflop_query()))

        assert outcome.code.startswith(CHART_PREFIX)

    def test_postflop_queries_are_answered_by_the_fallback(self, composite) -> None:
        for street in POSTFLOP_STREETS:
            outcome = decision(composite.decide(query(shape_with("check", "bet"), street, WEAK)))

            assert outcome.code.startswith(FALLBACK_PREFIX), street

    # A preflop chart refusal passes through carrying its original reason code.
    # Substituting a passive action would erase the coverage signal Phases 04 and 05
    # were built to produce.
    def test_a_preflop_chart_refusal_passes_through_unchanged(self, composite) -> None:
        request = uncovered_preflop_query()

        outcome = refusal(composite.decide(request))

        assert outcome.code.startswith(CHART_PREFIX)
        assert outcome == composite.preflop.decide(request)

    def test_a_preflop_chart_refusal_never_becomes_an_action(self, composite) -> None:
        outcome = composite.decide(uncovered_preflop_query())

        assert not isinstance(outcome, StrategyDecision), outcome

    # The composite adds no decision of its own: asserted over the enumeration
    # rather than by inspection.
    def test_its_outcome_is_always_its_components_outcome(self, composite) -> None:
        for request in enumeration_queries():
            assert composite.decide(request) == composite.postflop.decide(request)
        for request in (preflop_query(), preflop_query(hole_cards=("7d", "2c"))):
            assert composite.decide(request) == composite.preflop.decide(request)

    def test_every_outcome_names_the_component_that_produced_it(self, composite) -> None:
        for request in enumeration_queries():
            assert composite.decide(request).code.startswith(FALLBACK_PREFIX)
        for request in (preflop_query(), uncovered_preflop_query()):
            assert composite.decide(request).code.startswith(CHART_PREFIX)
