"""Postflop fallback tests, written from the contract before the implementation existed.

What this file pins is the one thing a continuity device has to be: total, legal, and
never inventing an investment. It owns the harness the pair shares - the engine-derived
betting shapes, the named card scenarios, and the query builders - and every test of what
`PostflopFallbackStrategy.decide` returns.

`TestTotalityAndLegality` proves coverage by enumeration rather than by sampling, and the
shapes it enumerates are read out of the engine's own `legal_actions` rather than listed
here, so the sweep follows the engine if the engine changes. Legality is not asserted by
eye: every decision goes through the Phase 03 `DecisionAuditRecord`, which rejects an
action outside `legal_actions`, an amount above all-in, and one below the minimum raise.

Everything in the pair that never calls `decide` lives in the companion,
`tests/test_postflop_fallback_components.py`, which imports this harness rather than
copying it: the outcome-code vocabulary, the `hand_cannot_lose` predicate the single
postflop call rests on, and the `CompositeStrategy` this strategy is a component of. That
line is what lets the companion need none of the fixtures defined here. Both files run
under `pytest_postflop_fallback`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from poker_training_bot.poker_core.cards import Card
from poker_training_bot.poker_core.engine import BettingRoundState, PlayerState
from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    SeatState,
    StrategyDecision,
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
        """Capped at hero's stack, so the price is what hero would actually pay."""
        return min(self.current_bet - self.hero_street_bet, self.hero_stack)

    @property
    def hero_is_short(self) -> bool:
        """The price to call takes hero's whole remaining stack. Phase 06 wrote this as
        `0 < stack < to_call`, which the cap makes unsatisfiable: a price hero can
        actually pay never exceeds the stack. Same hero, restated."""
        return 0 < self.hero_stack == self.to_call


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
        "current_bet": shape.current_bet,
        "min_raise_target": shape.current_bet + MIN_RAISE,
        "pot": 100 + shape.current_bet + shape.hero_street_bet,
        # The 100 belonged to nobody and a pot is now the sum of what the seats put in,
        # so it is villain's money from an earlier street: a real hand, not a constant.
        "seat_states": (
            SeatState(VILLAIN_SEAT, shape.current_bet, 100 + shape.current_bet, False, False),
            SeatState(HERO_SEAT, shape.hero_street_bet, shape.hero_street_bet, False, False),
        ),
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


def preflop_query(
    hole_cards: tuple[str, ...] = ("As", "Ah"),
    depth_bb: int = 100,
    open_to_bb: float = 2.5,
    **overrides: Any,
) -> StrategyQuery:
    """Hero in the big blind closing the action against a single button open.

    It used to seat hero at the lojack with the pot unopened. The cutover retires
    `t6/d100/LJ/rfi` - four opponents are still live behind an under-the-gun open, so it
    fails the ruled predicate - and the bot now opens from the small blind and faces an
    open from the big blind and nowhere else. A fixture that still means what it meant has
    to sit at one of those two, and this is the second: everyone folds to the button, which
    comes in at `open_to_bb`, the small blind folds, and hero closes the action.

    At the default price that is `t6/d100/BB/BTN:raise@2.5`, the spot the phase traces end
    to end. Setting `open_to_bb` to `depth_bb` makes it an open-shove, a committed spot too,
    which offers hero fold and call and nothing else.
    """
    hero = preflop_seat_of("BB")
    opener = preflop_seat_of("BTN")
    full = depth_bb * PREFLOP_BB
    open_to = round(open_to_bb * PREFLOP_BB)
    street = {preflop_seat_of("SB"): PREFLOP_SB, hero: PREFLOP_BB, opener: open_to}
    acted = tuple(preflop_seat_of(position) for position in ("LJ", "HJ", "CO", "BTN", "SB"))
    folders = tuple(seat for seat in acted if seat != opener)
    fields: dict[str, Any] = {
        "hand_id": "preflop-hand",
        "street": "preflop",
        "seat": hero,
        "button_seat": PREFLOP_BUTTON,
        "hole_cards": hole_cards,
        "board": (),
        # An open for the whole stack leaves hero nothing to raise with, and the contract
        # refuses a query that offers one.
        "legal_actions": ("fold", "call") if open_to >= full else ("fold", "call", "raise"),
        # The price hero can actually pay, capped at what hero holds.
        "to_call": min(open_to - PREFLOP_BB, full - PREFLOP_BB),
        "current_bet": open_to,
        "min_raise_target": open_to + (open_to - PREFLOP_BB),
        "pot": sum(street.values()),
        "seat_states": tuple(
            SeatState(
                seat,
                street.get(seat, 0),
                street.get(seat, 0),
                seat in folders,
                street.get(seat, 0) >= full,
            )
            for seat in PREFLOP_SEATS
        ),
        "stacks": tuple((seat, full - street.get(seat, 0)) for seat in PREFLOP_SEATS),
        "blinds": (PREFLOP_SB, PREFLOP_BB),
        # The folds travel with the raise. A spot key drops them, but the history and the
        # seat states are read by different code and a reader should see one hand.
        "preflop_actions": tuple(
            SeatAction(seat, "raise", open_to)
            if seat == opener
            else SeatAction(seat, "fold")
            for seat in acted
        ),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def retired_preflop_query(**overrides: Any) -> StrategyQuery:
    """The lojack opening an unopened 100bb pot: what `preflop_query` used to build.

    Kept rather than deleted, because the cutover turns it from a covered spot into a
    refused one. `t6/d100/LJ/rfi` leaves four opponents live behind an under-the-gun open,
    so it fails the predicate's subtree clause and the chart declines a decision the bot
    answers today. That is the ruled cost, and refusal being the common preflop answer is
    exactly why a component that routed one wrongly would be invisible.
    """
    hero = preflop_seat_of("LJ")
    posted = {preflop_seat_of("SB"): PREFLOP_SB, preflop_seat_of("BB"): PREFLOP_BB}
    full = 100 * PREFLOP_BB
    fields: dict[str, Any] = {
        "hand_id": "retired-preflop-hand",
        "street": "preflop",
        "seat": hero,
        "button_seat": PREFLOP_BUTTON,
        "hole_cards": ("As", "Ah"),
        "board": (),
        "legal_actions": ("fold", "call", "raise"),
        "to_call": PREFLOP_BB,
        "current_bet": PREFLOP_BB,
        "min_raise_target": 2 * PREFLOP_BB,
        "pot": PREFLOP_SB + PREFLOP_BB,
        "seat_states": tuple(
            SeatState(seat, posted.get(seat, 0), posted.get(seat, 0), False, False)
            for seat in PREFLOP_SEATS
        ),
        "stacks": tuple((seat, full - posted.get(seat, 0)) for seat in PREFLOP_SEATS),
        "blinds": (PREFLOP_SB, PREFLOP_BB),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


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
def enumerated(fallback) -> tuple[tuple[StrategyQuery, Any], ...]:
    """Every engine-legal postflop shape, at every street, decided once."""
    return tuple((request, fallback.decide(request)) for request in enumeration_queries())


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
                # Facing the open hero owes the fixture's own price; the check shape is a
                # hero who owes nothing, which is the other way a preflop seat can be asked.
                priced = {} if "check" not in legal else {"to_call": 0}
                outcome = fallback.decide(
                    preflop_query(hole_cards=hole_cards, legal_actions=legal, **priced)
                )

                assert not isinstance(outcome, StrategyDecision), outcome

    def test_all_three_postflop_streets_are_answered(self, fallback) -> None:
        for street in POSTFLOP_STREETS:
            outcome = fallback.decide(query(shape_with("fold", "check", "bet"), street, WEAK))

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
        shape = shape_with("fold", "check", "bet")
        for street in POSTFLOP_STREETS:
            outcome = decision(fallback.decide(query(shape, street, NUTS)))

            assert outcome.action == "check", street
            assert outcome.amount is None

    def test_it_never_raises_where_raising_is_legal(self, fallback) -> None:
        for shape in (shape_with("fold", "check", "raise"), shape_with("fold", "call", "raise")):
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

    # The enumeration must include a hero whose whole remaining stack is the price to
    # call - Phase 06's stack-below-the-price, restated - and that hero still decides.
    def test_a_hero_all_in_for_the_whole_price_to_call_still_decides(
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


class TestTotalityAndLegality:
    """Totality by exhaustive enumeration over engine-legal states, not by sampling."""

    def test_the_engine_shapes_cover_the_free_and_facing_a_bet_forms(self) -> None:
        """Guards the sweep itself: a broken derivation would enumerate nothing."""
        # Fold joins both free shapes in Phase 11 (FOLD-WHEN-FREE); the set is still the
        # engine's own, so widening it here follows the engine rather than describing it.
        assert {shape.actions for shape in FREE_SHAPES} == {
            ("fold", "check", "bet"),
            ("fold", "check", "raise"),
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
        for shape in (shape_with("fold", "call", "raise"), shape_with("fold", "check", "bet")):
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
