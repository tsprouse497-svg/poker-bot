"""Phase 16, stage 4: what the strategy must do, and where it must refuse.

Authored before any implementation exists. Modules stage 6 has not written are reached through
fixtures whose import sits in the function body; the head of `tests/test_postflop_key.py` says why.

**Nothing here gates on whether the strategy is good poker.** The repo has no postflop oracle and
every shape property below is satisfied by a uniformly wrong strategy. What these tests can prove
is that the bot bets with a legal amount, that it refuses rather than guessing, and that each
refusal names the first thing that was missing. Whether the frequencies are right is the stage-8
domain reviewer's question and no test in this repo answers it.

**The seam this phase accepts, stated because it is the thing a reader will find surprising:** the
bot bets a flop and then refuses every turn. Decision 1 took that deliberately.
"""

from __future__ import annotations

import pytest

from poker_training_bot.strategy import composite as composite_module
from poker_training_bot.strategy import contract as contract_module
from poker_training_bot.strategy import postflop_fallback as fallback_module

SMALL_BLIND = 50
BIG_BLIND = 100
TABLE_SEATS = 6
STARTING_STACK = 100 * BIG_BLIND

BUTTON_SEAT = 0
SB_SEAT = 1
HERO_SEAT = 2
LIVE_HEADS_UP = (BUTTON_SEAT, HERO_SEAT)
"""Six seats with the button at 0, which `poker_core.order.blind_seats` reads as the small blind
at seat 1 and the big blind at seat 2. Hero is the big blind - the seat the covered
`t6/d100/BB/BTN:raise@2.5,BB:call` cell was solved for, that line being the **completed** preflop
street rather than a preflop spot key - and hero and the button are the two still in."""

HERO_CHECKS = contract_module.SeatAction(HERO_SEAT, "check")
"""Postflop the blinds act first, so hero acts before the button on every street after the flop
and a button bet always has hero's check in front of it. A recorded history that opens with the
button's bet describes a street nobody could have played."""

POSTFLOP_CANARIES = (
    "fallback-answers-preflop",
    "fallback-folds-guaranteed-chops",
    "fallback-abandons-the-turn",
    "fallback-turn-needs-only-one-safe-river",
    "composite-routes-preflop-to-the-fallback",
    "fail-closed-can-invest-again",
)
"""The six mutations whose `find` string pins a line in `postflop_fallback.py` or `composite.py`.
Criterion: each is re-pointed with its claim unchanged, never retired. One is witnessed by
`pytest_engine_fidelity` rather than by this phase's command, so each is verified against its own
declared witness rather than against a list."""


@pytest.fixture(scope="module")
def betting_module():
    """`strategy.postflop_betting`: the flop play that can bet and raise."""
    import poker_training_bot.strategy.postflop_betting as module

    return module


@pytest.fixture(scope="module")
def strategy(betting_module):
    """Built from committed data, the way every other strategy in the repo is."""
    built = owed(betting_module, "PostflopBettingStrategy")

    return built.from_repo()


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 16's contract requires it and no"
        " implementation has been written yet"
    )
    return found


def seated(committed: dict[int, int], live: tuple[int, ...], street: dict[int, int] | None = None):
    """`pot`, `stacks` and `seat_states` for one table, derived from what each seat put in.

    **Every seat is listed and the folded ones are marked**, which is what `simulator/table.py`
    does: it walks every seated player and carries `PlayerState`'s own `folded` marker. The
    convention this replaces dropped the folded small blind and lent its dead 0.5bb to the big
    blind: `len(stacks)` was then 2, which `PreflopChartStrategy._chart_query` reads as the table
    size, and `_table_depth_bb` recovers a starting stack as `stack + committed_total`, making
    hero 10,050 against a villain at 10,000 - a `t2` lookup at a ragged 100.5bb.
    """
    on_street = dict(street or {})
    states = tuple(
        contract_module.SeatState(
            seat=seat,
            street_bet=on_street.get(seat, 0),
            committed_total=committed.get(seat, 0),
            folded=seat not in live,
        )
        for seat in range(TABLE_SEATS)
    )
    return {
        "pot": sum(state.committed_total for state in states),
        "stacks": tuple((state.seat, STARTING_STACK - state.committed_total) for state in states),
        "seat_states": states,
    }


def opened_to(chips: int, *after):
    """The lojack, hijack and cutoff fold, the button opens, the small blind folds.
    `simulator/run.py` appends every preflop action a seat takes, folds included, so a line
    recorded from the raise onwards is not the line the producer emits."""
    return (
        *(contract_module.SeatAction(seat, "fold") for seat in (3, 4, 5)),
        contract_module.SeatAction(BUTTON_SEAT, "raise", chips),
        contract_module.SeatAction(SB_SEAT, "fold"),
        *after,
    )


def query(**overrides):
    """A contract-valid flop query in the covered single-raised pot, six-handed and flat at 100bb.

    The `@2.5` line the committed chart declares: the button opens to 2.5bb, the small blind folds
    and the big blind calls, so 5.5bb is in the middle - 2.5 + 2.5 + the dead 0.5, which stays on
    the small blind's own seat - and 97.5bb is behind both live seats. Every fixture below takes
    decision 10's arithmetic, `pot = 2 x final_price + 0.5bb`: 4.5bb at a 2.0bb open, 5.5bb at
    2.5bb, 7.5bb at a 3.5bb open, 15.5bb in the 3-bet pot.
    """
    fields = {
        "hand_id": "h1",
        "street": "flop",
        "seat": HERO_SEAT,
        "button_seat": BUTTON_SEAT,
        "hole_cards": ("As", "Qd"),
        "board": ("Kc", "7d", "2h"),
        "legal_actions": ("check", "bet"),
        "to_call": 0,
        "current_bet": 0,
        "min_raise_target": BIG_BLIND,
        **seated({BUTTON_SEAT: 250, SB_SEAT: 50, HERO_SEAT: 250}, LIVE_HEADS_UP),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": opened_to(250, contract_module.SeatAction(HERO_SEAT, "call")),
    }
    fields.update(overrides)
    return contract_module.StrategyQuery(**fields)


def facing_a_bet(**overrides):
    """The same pot after the button bets 33%, so hero has a raise available."""
    fields = {
        "legal_actions": ("fold", "call", "raise"),
        "to_call": 180,
        "current_bet": 180,
        "min_raise_target": 360,
        **seated(
            {BUTTON_SEAT: 430, SB_SEAT: 50, HERO_SEAT: 250}, LIVE_HEADS_UP, {BUTTON_SEAT: 180}
        ),
        "postflop_actions": (HERO_CHECKS, contract_module.SeatAction(BUTTON_SEAT, "bet", 180)),
    }
    fields.update(overrides)
    return query(**fields)


def three_bet_pot(**overrides):
    """The 3-bet the committed chart does not cover: hero makes it 7.5bb and the button calls,
    so 15.5bb is in the middle and 92.5bb is behind."""
    return query(
        preflop_actions=opened_to(
            250,
            contract_module.SeatAction(HERO_SEAT, "raise", 750),
            contract_module.SeatAction(BUTTON_SEAT, "call"),
        ),
        **seated({BUTTON_SEAT: 750, SB_SEAT: 50, HERO_SEAT: 750}, LIVE_HEADS_UP),
        **overrides,
    )


def audit(query_, outcome):
    """Every amount this phase returns has to pass the repo's own legality proof."""
    return contract_module.DecisionAuditRecord(
        schema_version=contract_module.DECISION_AUDIT_SCHEMA_VERSION,
        strategy_id="phase-16-fixture",
        strategy_version=1,
        query=query_,
        outcome=outcome,
    )


# --------------------------------------------------------------------------- #
# It bets, and it raises, and the amounts are legal
# --------------------------------------------------------------------------- #


class TestTheBotCanFinallyPutMoneyIn:
    """Criterion: on a covered flop spot the strategy returns `bet` and `raise` with amounts, and
    a test proves at least one committed spot produces each.

    What is true right now, and is the whole reason for the phase: `PostflopFallbackStrategy`
    checks whenever checking is free, calls on turn and river only a hand `hand_cannot_lose`
    proves cannot lose, and folds on the flop without asking. It never returns `bet` or `raise`,
    and no `StrategyDecision` it builds carries an amount.
    """

    def test_the_old_fallback_still_cannot_bet_which_is_what_this_phase_replaces(self) -> None:
        """The before picture, asserted rather than described, so the after means something."""
        outcome = fallback_module.PostflopFallbackStrategy().decide(query())

        assert isinstance(outcome, contract_module.StrategyDecision)
        assert outcome.action == "check"
        assert outcome.amount is None

    def test_at_least_one_committed_spot_produces_a_bet_with_an_amount(
        self, betting_module, strategy
    ) -> None:
        spots = owed(betting_module, "committed_spot_queries")()

        bets = [
            outcome
            for spot in spots
            for outcome in [strategy.decide(spot)]
            if isinstance(outcome, contract_module.StrategyDecision) and outcome.action == "bet"
        ]

        assert bets, "no committed spot produces a bet, so the phase has not done its one job"
        assert all(outcome.amount and outcome.amount > 0 for outcome in bets)

    def test_at_least_one_committed_spot_produces_a_raise_with_an_amount(
        self, betting_module, strategy
    ) -> None:
        spots = owed(betting_module, "committed_spot_queries")()

        raises = [
            outcome
            for spot in spots
            for outcome in [strategy.decide(spot)]
            if isinstance(outcome, contract_module.StrategyDecision) and outcome.action == "raise"
        ]

        assert raises

    def test_every_amount_over_every_committed_spot_passes_the_legality_proof(
        self, betting_module, strategy
    ) -> None:
        """At or above `min_raise_target` unless exactly all-in, never above
        `hero.street_bet + stack`. `DecisionAuditRecord` owns the rule and this runs it rather
        than restating it, because a test that rebuilds the rule agrees with the code whatever the
        code says."""
        checked = 0
        for spot in owed(betting_module, "committed_spot_queries")():
            outcome = strategy.decide(spot)
            if isinstance(outcome, contract_module.StrategyDecision):
                audit(spot, outcome)
                checked += 1

        assert checked, "no committed spot was answered at all"

    def test_an_answered_action_is_always_one_the_query_said_was_legal(
        self, betting_module, strategy
    ) -> None:
        for spot in owed(betting_module, "committed_spot_queries")():
            outcome = strategy.decide(spot)
            if isinstance(outcome, contract_module.StrategyDecision):
                assert outcome.action in spot.legal_actions, spot.hand_id


# --------------------------------------------------------------------------- #
# Where it refuses
# --------------------------------------------------------------------------- #


class TestTurnAndRiverRefuseByTheirOwnCodes:
    """Criterion: turn and river refuse by their own codes rather than folding by default. A
    refusal is not an action: the composite returns it untouched and the simulator voids the hand.

    `CODE_FOLD_ON_THE_FLOP` covers the flop today and is answered after this phase.
    """

    def test_a_turn_refuses_rather_than_folding(self, strategy) -> None:
        outcome = strategy.decide(query(street="turn", board=("Kc", "7d", "2h", "9s")))

        assert isinstance(outcome, contract_module.StrategyRefusal)

    def test_a_river_refuses_rather_than_folding(self, strategy) -> None:
        outcome = strategy.decide(query(street="river", board=("Kc", "7d", "2h", "9s", "4c")))

        assert isinstance(outcome, contract_module.StrategyRefusal)

    def test_the_turn_and_the_river_refuse_under_two_different_codes(self, strategy) -> None:
        """One code for both would pool two different uncovered depths in every count the report
        prints."""
        turn = strategy.decide(query(street="turn", board=("Kc", "7d", "2h", "9s")))
        river = strategy.decide(query(street="river", board=("Kc", "7d", "2h", "9s", "4c")))

        assert turn.code != river.code

    def test_neither_refusal_is_the_old_flop_fold_code(self, strategy) -> None:
        turn = strategy.decide(query(street="turn", board=("Kc", "7d", "2h", "9s")))

        assert turn.code != fallback_module.CODE_FOLD_ON_THE_FLOP

    def test_the_composite_returns_a_postflop_refusal_untouched(self, betting_module) -> None:
        """No branch on the outcome, deliberately: a branch here is where a passive substitute
        would eventually get added."""
        built = owed(betting_module, "PostflopBettingStrategy").from_repo()
        composite = composite_module.CompositeStrategy(
            preflop=composite_module.PreflopChartStrategy.from_repo(),
            postflop=built,
        )
        turn = query(street="turn", board=("Kc", "7d", "2h", "9s"))

        assert composite.decide(turn) == built.decide(turn)


class TestTheTwoTableCausesAndTheCodesThatNameThem:
    """Criterion: an uncovered preflop line refuses with a code that names the line, and an
    uncovered board refuses with its own. At the table a miss carries exactly two causes and the
    report never pools them.

    The two are: no cell for this board or line - which is never-solved and solved-but-rejected
    together, because neither is in the artifact and the query meets one absence; and in the index
    but not fetched on this machine. How many cells the campaign rejected above 1% of pot is a
    report figure, not a third cause here.
    """

    def test_an_uncovered_preflop_line_refuses_and_its_detail_names_the_line(
        self, strategy
    ) -> None:
        outcome = strategy.decide(three_bet_pot())

        assert isinstance(outcome, contract_module.StrategyRefusal)
        assert outcome.named("preflop_line"), outcome.detail

    def test_an_uncovered_board_refuses_under_its_own_code(self, strategy, betting_module) -> None:
        """The board-miss code is live rather than vacuous: all 1,755 classes are in scope, but a
        cell over 1% of pot refuses and rainbow has never been solved to target."""
        line_code = strategy.decide(three_bet_pot()).code
        board_miss = strategy.decide(query(board=("Jd", "6s", "3c")))

        assert isinstance(board_miss, contract_module.StrategyRefusal)
        assert board_miss.code != line_code
        assert board_miss.named("board"), board_miss.detail

    def test_the_two_table_causes_have_two_codes_and_neither_is_the_other(
        self, betting_module
    ) -> None:
        absent = owed(betting_module, "REFUSE_NO_CELL_FOR_THIS_SPOT")
        unfetched = owed(betting_module, "REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED")

        assert absent != unfetched

    def test_a_spot_the_index_holds_but_this_machine_has_not_fetched_says_so(
        self, betting_module, strategy
    ) -> None:
        """On a fresh clone this is the common case - 1,752 of 1,755 classes - and pooling it with
        never-solved would understate coverage by the whole artifact."""
        listed = owed(betting_module, "an_indexed_but_unfetched_query")()

        outcome = strategy.decide(listed)

        assert isinstance(outcome, contract_module.StrategyRefusal)
        assert outcome.code == owed(betting_module, "REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED")

    def test_the_refusal_vocabulary_is_a_closed_list(self, betting_module) -> None:
        codes = owed(betting_module, "REFUSAL_CODES")

        assert len(set(codes)) == len(codes)
        assert owed(betting_module, "REFUSE_NO_CELL_FOR_THIS_SPOT") in codes
        assert owed(betting_module, "REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED") in codes


class TestTheLookupFailsClosedCoarsestGapFirst:
    """Criterion: the lookup fails closed on the preflop library's own walk - coarsest gap first,
    so the code names the first thing missing. No nearest-neighbour substitution of board, line,
    flop action, pot or stack."""

    def test_a_query_missing_both_line_and_board_names_the_line_first(self, strategy) -> None:
        """Both gaps at once. The walk has one order and the code says which it found, rather
        than whichever branch happened to run last."""
        missing_line_only = three_bet_pot()
        both = three_bet_pot(board=("Jd", "6s", "3c"))

        assert strategy.decide(both).code == strategy.decide(missing_line_only).code

    def test_a_price_outside_the_band_refuses_rather_than_answering_from_the_nearest_cell(
        self, strategy
    ) -> None:
        """A 3.5bb open is outside 20% of the `@2.5` cell. The preflop chart would substitute; this
        one refuses, and the sensitivity is why."""
        wide_open = query(
            preflop_actions=opened_to(350, contract_module.SeatAction(HERO_SEAT, "call")),
            **seated({BUTTON_SEAT: 350, SB_SEAT: 50, HERO_SEAT: 350}, LIVE_HEADS_UP),
        )

        assert isinstance(strategy.decide(wide_open), contract_module.StrategyRefusal)

    def test_a_price_at_the_band_endpoint_is_answered_rather_than_refused(
        self, strategy
    ) -> None:
        """The endpoints are inclusive and real hands land exactly on them: 2.0bb is a min-open
        and 3.0bb a standard 3x. Inclusivity is what makes that safe."""
        min_open = query(
            preflop_actions=opened_to(200, contract_module.SeatAction(HERO_SEAT, "call")),
            **seated({BUTTON_SEAT: 200, SB_SEAT: 50, HERO_SEAT: 200}, LIVE_HEADS_UP),
        )

        outcome = strategy.decide(min_open)

        assert isinstance(outcome, contract_module.StrategyDecision)

    def test_a_flop_action_the_menu_does_not_offer_refuses(self, strategy) -> None:
        """Naming the size in the key is what makes a later menu change fail closed. A 50% bet is
        not on the ruled `33 75` menu and has no cell."""
        off_menu = facing_a_bet(
            to_call=275,
            current_bet=275,
            min_raise_target=550,
            **seated(
                {BUTTON_SEAT: 525, SB_SEAT: 50, HERO_SEAT: 250},
                LIVE_HEADS_UP,
                {BUTTON_SEAT: 275},
            ),
            postflop_actions=(HERO_CHECKS, contract_module.SeatAction(BUTTON_SEAT, "bet", 275)),
        )

        assert isinstance(strategy.decide(off_menu), contract_module.StrategyRefusal)

    def test_a_real_table_s_rounding_of_a_menu_size_is_still_answered(self, strategy) -> None:
        """Decision 14. The menu is in pot fractions and the table in chips: 33% of the 550-chip
        `@2.5` pot is 181.5, so no real table produces the menu size exactly. The fixture bets 180,
        which is 32.73%, inside the tolerance, and has to be answered. The positive control on the
        refusal below: a strict equality match would refuse every faced bet at a real table and
        kill the artifact's whole raise branch with nothing going red."""
        outcome = strategy.decide(facing_a_bet())

        assert isinstance(outcome, contract_module.StrategyDecision), outcome

    def test_a_bet_halfway_between_two_menu_sizes_refuses_rather_than_snapping(
        self, strategy
    ) -> None:
        """Decision 14's other half, and the half a tolerance without a ceiling loses. 297 chips
        is 54.0% of the 550-chip pot, exactly halfway between the menu's 33% and 75%. A rule
        snapping a faced bet to the nearest menu entry answers it from whichever cell rounding
        picked, which is the nearest-neighbour substitution the contract forbids by name."""
        between = facing_a_bet(
            to_call=297,
            current_bet=297,
            min_raise_target=594,
            **seated(
                {BUTTON_SEAT: 547, SB_SEAT: 50, HERO_SEAT: 250},
                LIVE_HEADS_UP,
                {BUTTON_SEAT: 297},
            ),
            postflop_actions=(HERO_CHECKS, contract_module.SeatAction(BUTTON_SEAT, "bet", 297)),
        )

        assert isinstance(strategy.decide(between), contract_module.StrategyRefusal)


# --------------------------------------------------------------------------- #
# The flush draw, at the table rather than in the map
# --------------------------------------------------------------------------- #


class TestAFlushDrawIsNotServedTheNoDrawStrategy:
    """The contract's second named gate test on the canonical-board criterion, asked of the
    strategy rather than of the canonicaliser.

    `tests/test_postflop_key.py` proves the map is joint over all 22,100 boards, which is the
    general property. This proves the consequence at the table on the committed two-tone sample
    board, which is where a reader can see it.
    `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`.
    """

    TWO_TONE_SAMPLE = ("8h", "8d", "3h")

    def answered(self, strategy, hole):
        outcome = strategy.decide(query(board=self.TWO_TONE_SAMPLE, hole_cards=hole))
        assert isinstance(outcome, contract_module.StrategyDecision), (hole, outcome)
        return outcome

    def test_the_two_tone_sample_board_is_answered_at_all(self, strategy) -> None:
        """The positive control. Two refusals compare equal and would pass the test below."""
        assert self.answered(strategy, ("Ah", "Qh"))

    def test_a_flush_draw_and_the_same_ranks_without_one_are_played_differently(
        self, strategy
    ) -> None:
        with_draw = self.answered(strategy, ("Ah", "Qh"))
        without_draw = self.answered(strategy, ("As", "Qd"))

        moved = (with_draw.action, with_draw.amount) != (without_draw.action, without_draw.amount)
        assert moved or with_draw.detail != without_draw.detail


# --------------------------------------------------------------------------- #
# The pot-odds river call
# --------------------------------------------------------------------------- #


class TestThePotOddsRiverCall:
    """Decision 5's default, behind an explicit flag, reporting the frequency it fires rather than
    claiming it is correct.

    A uniform unseen deck flatters hero, so this makes the bot over-call as the mirror of its
    current over-folding. That is the accepted cost, not a defect this file is trying to catch.
    """

    RIVER_BOARD = ("Kc", "7d", "2h", "9s", "4c")

    RIVER_POT = 1365
    RIVER_TO_CALL = 455
    RIVER_PRICE = RIVER_TO_CALL / (RIVER_POT + RIVER_TO_CALL)
    """Exactly 0.25: 455 over 1,820. The price is `to_call / (pot + to_call)` off the query, and
    the fixture is built to land on a round number rather than asserted at a tolerance."""

    def river(self, **overrides):
        """A real river in a real line, the pot equal to what the seats actually put in.

        Button opens to 2.5bb, big blind calls (550 with the dead small blind, as `seated`
        explains); button bets the 33% menu size of 180 and the big blind calls (910); both check
        the turn; button bets 455 on the river. The button has committed `250 + 180 + 455 = 885`,
        hero `250 + 180 = 430`, the folded small blind still holds its own dead 50, and that is
        the 1,365.
        """
        fields = {
            "street": "river",
            "board": self.RIVER_BOARD,
            "legal_actions": ("fold", "call"),
            "to_call": self.RIVER_TO_CALL,
            "current_bet": self.RIVER_TO_CALL,
            "min_raise_target": 2 * self.RIVER_TO_CALL,
            **seated(
                {BUTTON_SEAT: 885, SB_SEAT: 50, HERO_SEAT: 430},
                LIVE_HEADS_UP,
                {BUTTON_SEAT: 455},
            ),
            "postflop_actions": (HERO_CHECKS, contract_module.SeatAction(BUTTON_SEAT, "bet", 455)),
        }
        fields.update(overrides)
        return query(**fields)

    def test_the_counting_equity_helper_lives_in_src_now(self, betting_module) -> None:
        """It lived in `scripts/generate_postflop_fallback_report.py`, which is not somewhere a
        strategy can reach. `hand_cannot_lose` is the short-circuiting bool and stays one.

        **The orientation is asserted on the numbers, because the name collides.** Today's
        `scripts/generate_postflop_fallback_report.py::holding_counts` returns
        `(beats, ties, hero_label)`, `beats` being holdings that **beat** hero; this one returns
        `(wins, ties, losses)`, `wins` being holdings hero beats. A stage 6 lifting that function
        into `src` unchanged inverts every equity, and a check that the three add to 990 passes.

        Counted over the full unseen deck with `poker_core.evaluate_best`: `AhAd` on
        `Kc7d2h9s4c` beats 884 of 990, ties 1, loses to 105, so `(884 + 0.5) / 990 = 89.34%`.
        Inverted those same numbers read 10.66%, the wrong side of this class's 25.0% price.
        """
        counts = owed(betting_module, "holding_counts")

        wins, ties, losses = counts(("Ah", "Ad"), self.RIVER_BOARD)

        assert wins + ties + losses == 990
        assert (wins, ties, losses) == (884, 1, 105), (
            "either the evaluator moved or `holding_counts` returns the count of holdings that"
            " BEAT hero first, which is what the report script's function of the same name does"
        )

    def test_the_equity_formula_is_wins_plus_half_the_ties_over_nine_hundred_and_ninety(
        self, betting_module
    ) -> None:
        counts = owed(betting_module, "holding_counts")
        equity = owed(betting_module, "river_equity")
        wins, ties, _ = counts(("Ah", "Ad"), self.RIVER_BOARD)

        assert equity(("Ah", "Ad"), self.RIVER_BOARD) == pytest.approx((wins + ties / 2) / 990)

    def test_the_price_is_to_call_over_the_pot_after_the_call(self, betting_module) -> None:
        price = owed(betting_module, "pot_odds_price")

        assert price(self.river()) == pytest.approx(self.RIVER_PRICE)
        assert self.RIVER_PRICE == 0.25

    def test_the_flag_is_explicit_and_off_the_bot_does_not_pot_odds_call(
        self, betting_module
    ) -> None:
        built = owed(betting_module, "PostflopBettingStrategy")
        off = built.from_repo(pot_odds_river_call=False)

        outcome = off.decide(self.river(hole_cards=("Ah", "Ad")))

        assert not (
            isinstance(outcome, contract_module.StrategyDecision) and outcome.action == "call"
        )

    def test_with_the_flag_on_a_hand_whose_equity_beats_the_price_calls(
        self, betting_module
    ) -> None:
        built = owed(betting_module, "PostflopBettingStrategy")
        equity = owed(betting_module, "river_equity")
        on = built.from_repo(pot_odds_river_call=True)
        spot = self.river(hole_cards=("Ah", "Ad"))
        assert equity(("Ah", "Ad"), self.RIVER_BOARD) > self.RIVER_PRICE

        outcome = on.decide(spot)

        assert isinstance(outcome, contract_module.StrategyDecision)
        assert outcome.action == "call"

    def test_with_the_flag_on_a_hand_whose_equity_does_not_beat_the_price_does_not_call(
        self, betting_module
    ) -> None:
        """The negative control. A rule that called every river would pass the test above.

        **The hand was picked on a count, not on how it looks.** An earlier draft used `3c2d`,
        the sort of hand a reader waves through as trash - and on `Kc7d2h9s4c` it pairs the
        board's deuce. Counted over all 990 villain holdings with `poker_core.evaluate_best`:
        villain beats it 548, ties 22, hero wins 420, so `(420 + 11) / 990 = 43.54%` against a
        price of 25.0%. The precondition was false by 18.5 points and the test was red against a
        correct implementation.

        `Jd8d` is jack-high, no pair, nothing to come: 180 wins, 9 ties, 801 losses, so
        `(180 + 4.5) / 990 = 18.64%` - below the price with 6.4 points to spare, and near enough
        that a rule folding only the very bottom of the deck does not pass by accident.

        The over-calling the contract concedes, measured here: 272 of the 1,081 hero holdings are
        under 25.0% and the median has 48.38%, so decision 5's rule calls with about three quarters
        of the deck. The precondition assert stays; it is what keeps the control honest."""
        built = owed(betting_module, "PostflopBettingStrategy")
        equity = owed(betting_module, "river_equity")
        counts = owed(betting_module, "holding_counts")
        on = built.from_repo(pot_odds_river_call=True)
        hole = ("Jd", "8d")
        assert counts(hole, self.RIVER_BOARD) == (180, 9, 801)
        assert equity(hole, self.RIVER_BOARD) == pytest.approx((180 + 9 / 2) / 990)
        assert equity(hole, self.RIVER_BOARD) < self.RIVER_PRICE

        outcome = on.decide(self.river(hole_cards=hole))

        assert not (
            isinstance(outcome, contract_module.StrategyDecision) and outcome.action == "call"
        )

    def test_hand_cannot_lose_still_refuses_a_flop_board(self) -> None:
        """Unchanged by this phase, and pinned because the equity work moves next to it. The
        honest claim on a flop is 1,081 holdings against 990 runouts, and sampling it turns a fact
        back into a guess. `POSTFLOP-UNBEATABLE-EARLIER-STREETS`."""
        with pytest.raises(ValueError):
            fallback_module.hand_cannot_lose(("Ah", "Ad"), ("Kc", "7d", "2h"))


# --------------------------------------------------------------------------- #
# The canaries that already pin these two files
# --------------------------------------------------------------------------- #


class TestTheSixExistingCanariesAreRePointedNotRetired:
    """Criterion: every mutation whose `find` string pins a line in `postflop_fallback.py` or
    `composite.py` is re-pointed with its claim unchanged, never retired.

    Phase 13's L2 did this and it is the pattern. A canary quietly dropped during a rewrite takes
    the behaviour it was guarding with it, and nothing in the gate notices a mutation that is no
    longer there.
    """

    @pytest.fixture(scope="class")
    def mutations(self):
        import sys

        from scripts.repo_paths import REPO_ROOT

        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import check_gate_bite

        return {entry["id"]: entry for entry in check_gate_bite.load_mutations()}

    def test_all_six_are_still_declared(self, mutations) -> None:
        missing = [name for name in POSTFLOP_CANARIES if name not in mutations]

        assert missing == []

    def test_each_still_points_at_a_postflop_or_composite_file(self, mutations) -> None:
        for name in POSTFLOP_CANARIES:
            target = mutations[name]["file"]
            assert target.endswith(
                ("postflop_fallback.py", "composite.py", "postflop_betting.py")
            ), (name, target)

    def test_the_one_witnessed_by_engine_fidelity_keeps_its_own_witness(self, mutations) -> None:
        """Each canary is verified against its own declared witness rather than against a list.
        `fail-closed-can-invest-again` is not this phase's command's to prove."""
        assert mutations["fail-closed-can-invest-again"]["must_fail"] == [
            "pytest_engine_fidelity"
        ]

    def test_no_canary_names_the_whole_suite_as_its_witness(self, mutations) -> None:
        """A `must_fail` of bare `pytest` is not evidence that anything bites:
        `test_every_mutation_applies_exactly_once_to_its_file` reds the whole suite for any
        mutation, on one bookkeeping test, before any behaviour is examined."""
        for name in POSTFLOP_CANARIES:
            assert "pytest" not in mutations[name]["must_fail"], name
