"""Phase 13's strategy tests, re-cut at phase 14's stage 4 onto the chart the cutover ships.

Two halves, both of the strategy rather than of the query. Per-seat depth: a seat's starting stack
is what it holds plus what it has put in, and the order the checks fire in is ruled. Then forced
money: three signals, each pinned on a table where it is the only one that can see anything.
`tests/test_table_state.py` covers query validation, the pot reconciliation, the audit schema
version and the all-in ceiling.

**What phase 14 changed, and it is not the phase-13 behaviour.** The chart becomes the 249 spots
the three ruled clauses select: all five first-in seats open, every seat behind an opener is
covered, and the raise-depth clause gives up the four-bet family instead. What the cutover takes
away is narrow - the big blind's ten squeeze spots, the two-or-more-caller pots, the limped pot,
and everything from the four-bet on. A green run can still hide a dead subject: `decide` runs
forced money, then depth, then the chart, so a depth test on a refused spot goes on passing with
its subject unreachable - a claim about a table the bot can never be handed. So every query below
that can be stated on the covered surface is stated there, and the ones deliberately stated on a
refused table say so and read the refusal CODE, so a coverage refusal cannot be mistaken for the
one under test.

Two readings a stage 6 builder needs - what makes forced money an ante, and the vocabulary a
seat-naming refusal uses - are in the stage-04 review note rather than here.
"""

from __future__ import annotations

from functools import cache

import pytest

from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.lookup import ChartHit, PreflopChartLibrary
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key
from poker_training_bot.strategy import contract as contract_module
from poker_training_bot.strategy import preflop_chart as preflop_chart_module
from poker_training_bot.strategy import preflop_sizing as preflop_sizing_module
from poker_training_bot.strategy.contract import (
    SeatAction,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR, PreflopChartStrategy
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

SMALL_BLIND = 50
BIG_BLIND = 100
FULL_STACK = 100 * BIG_BLIND
SEATS = (0, 1, 2, 3, 4, 5)
BUTTON = 3  # seats 0..5 with the button at 3 puts LJ at seat 0

REFUSE_RAGGED_DEPTH = "preflop-chart:stack-depth-not-a-whole-big-blind"
REFUSE_UNEVEN_TABLE = "preflop-chart:table-is-not-one-flat-stack-depth"
REFUSE_SHORT_LIVE_SEAT = "preflop-chart:a-live-seat-is-shorter-than-hero"
REFUSE_STRADDLE = "preflop-chart:pot-holds-a-straddle"
REFUSE_ANTE = "preflop-chart:pot-holds-an-ante"
REFUSE_BLIND_STRUCTURE = "preflop-chart:blind-structure-not-representable"

# Every refusal the chart layer itself files wears this prefix and nothing in front of it does,
# so "refused for want of a cell" is one string test - which is what tells a spot the cutover
# retired from a table shape phase 13's own checks rejected.
LOOKUP_PREFIX = "preflop-chart:lookup:"
REFUSE_NOT_COVERED = f"{LOOKUP_PREFIX}spot-not-covered"

FORCED_MONEY_CODES = frozenset({REFUSE_STRADDLE, REFUSE_ANTE, REFUSE_BLIND_STRUCTURE})
DEPTH_CODES = frozenset({REFUSE_RAGGED_DEPTH, REFUSE_UNEVEN_TABLE, REFUSE_SHORT_LIVE_SEAT})

# Folded to the small blind, the last of the five committed first-in seats.
FOLDED_TO_SB = ("LJ", "HJ", "CO", "BTN")


@cache
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_directory(ARTIFACT_DIR)


@cache
def solved() -> tuple[int, int, str]:
    """The open in chips, the three-bet in chips, and the three-bet spot key, read out of the
    artifact because this file was authored against a chart that three-bet to 8 and the solve
    three-bets to 7.5. `add_allin: false`, so each raising point offers one named raise and `min`
    picks out of a single price. Behind a call rather than at module scope for the reason
    `seat_state` gives below: mid-cutover a module-scope read fails collection and takes every
    assertion with it. Both prices come off HERO's own keys, which is why they survive the
    cutover: the lojack opens at 2.5 and the cutoff three-bets it to 7.5 either way."""
    open_bb = min(library().solved_prices_bb(6, 100, "LJ", (), "LJ"))
    opened = (PreflopAction("LJ", "raise", open_bb),)
    three_bet_bb = min(library().solved_prices_bb(6, 100, "LJ", opened, "CO"))
    key = spot_key(6, 100, "LJ", (*opened, PreflopAction("CO", "raise", three_bet_bb)))
    return int(open_bb * BIG_BLIND), int(three_bet_bb * BIG_BLIND), key


@cache
def faced_open() -> tuple[int, str]:
    """The cutoff's open in chips and the key it puts the big blind on, off the big blind's own
    arriving prices. The big blind is no longer the only seat left facing an open - the exposure
    clause covers all fifteen pairs - but it is still the one that closes the action."""
    open_bb = min(library().solved_prices_bb(6, 100, "BB", (), "CO"))
    opened = (PreflopAction("CO", "raise", open_bb),)
    return int(open_bb * BIG_BLIND), spot_key(6, 100, "BB", opened)


def seat_of(position: str) -> int:
    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise AssertionError(f"no seat holds {position}")


def seat_state(seat: int, contributed: int, *, folded: bool, dead: int = 0, all_in: bool = False):
    """One `SeatState`, or a TypeError saying which field phase 13 has not added yet. Resolved off
    the module rather than imported at the top so that this file collects and runs today: an
    ImportError at collection reports the whole file as broken, where the point of stage 4 is a
    red that says which behaviour is missing.

    `contributed` is what the seat has put in toward the level, which preflop is both its street
    figure and its hand figure. `dead` is money in the pot buying nothing off the price, which is
    what an ante is, so it lands in `committed_total` alone per the ruling: in the street figure
    it would make an anted seat owe less than an unanted one, and the gap between the two figures
    is the signal the ante detection reads."""
    factory = getattr(contract_module, "SeatState", None)
    if factory is None:
        raise TypeError(
            "StrategyQuery carries no per-seat record yet;"
            " phase 13 adds SeatState(seat, street_bet, committed_total, folded, all_in)"
        )
    return factory(
        seat=seat,
        street_bet=contributed,
        committed_total=contributed + dead,
        folded=folded,
        all_in=all_in,
    )


def table_query(
    hero_position: str,
    *,
    contributed: dict[int, int] | None = None,
    starting: dict[int, int] | None = None,
    ante: int = 0,
    current_bet: int = BIG_BLIND,
    min_raise_target: int | None = None,
    history: tuple[SeatAction, ...] = (),
    folded: tuple[str, ...] = (),
    hole_cards: tuple[str, str] = ("As", "Ks"),
    **overrides,
) -> StrategyQuery:
    """A six-handed preflop query built from what each seat has put in.

    `contributed` is chips into the pot per seat and defaults to the two blinds. `starting` is
    what each seat sat down with and defaults to 100bb everywhere, so a seat's current stack is
    always derived rather than stated: that derivation is the thing under test, and a fixture
    stating both could state them inconsistently. `ante` is posted by every seat and is dead
    money, so it leaves each stack and enters the pot without moving the level or the price.
    `min_raise_target` defaults to one big blind above an unraised level, which is right at a
    50/100 table and wrong at every straddled one, so every straddled fixture states it. That is
    not incidental - it is the third signal."""
    hero = seat_of(hero_position)
    folded_seats = {seat_of(position) for position in folded}
    paid = dict(contributed or {seat_of("SB"): SMALL_BLIND, seat_of("BB"): BIG_BLIND})
    sat_down = dict(starting or {seat: FULL_STACK for seat in SEATS})

    stacks = tuple((seat, sat_down[seat] - paid.get(seat, 0) - ante) for seat in SEATS)
    hero_stack = sat_down[hero] - paid.get(hero, 0) - ante
    to_call = min(max(current_bet - paid.get(hero, 0), 0), hero_stack)
    if to_call == 0:
        legal_actions: tuple[str, ...] = ("check", "raise")
    elif to_call == hero_stack:
        # Hero is all-in for the call, so no raise is on offer.
        legal_actions = ("fold", "call")
    else:
        legal_actions = ("fold", "call", "raise")

    fields = {
        "hand_id": "h1",
        "street": "preflop",
        "seat": hero,
        "button_seat": BUTTON,
        "hole_cards": hole_cards,
        "board": (),
        "legal_actions": legal_actions,
        "to_call": to_call,
        "current_bet": current_bet,
        "min_raise_target": min_raise_target or current_bet + BIG_BLIND,
        "pot": sum(paid.values()) + ante * len(SEATS),
        "stacks": stacks,
        "seat_states": tuple(
            seat_state(seat, paid.get(seat, 0), folded=seat in folded_seats, dead=ante)
            for seat in SEATS
        ),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": history,
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def raised(position: str, amount: int | None = None) -> SeatAction:
    amount = solved()[0] if amount is None else amount
    return SeatAction(seat_of(position), "raise", amount)


def called(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "call")


def dropped(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "fold")


def folds(*positions: str) -> tuple[SeatAction, ...]:
    """The folds in front of or behind hero, in the order the ring produces them. A helper
    because after the cutover almost every covered spot is reached through four or five of them,
    and spelling each one out buried the fixture that mattered."""
    return tuple(dropped(position) for position in positions)


def paid_in(**chips: int) -> dict[int, int]:
    """Chips into the pot, per position, keyed by seat the way `table_query` wants them."""
    return {seat_of(position): amount for position, amount in chips.items()}


def starting_stacks(**chips: int) -> dict[int, int]:
    """100bb at every seat, with the named positions sat down at the chips given."""
    sat_down = {seat: FULL_STACK for seat in SEATS}
    for position, amount in chips.items():
        sat_down[seat_of(position)] = amount
    return sat_down


def refusal(outcome) -> StrategyRefusal:
    assert isinstance(outcome, StrategyRefusal), outcome
    return outcome


def code_of(outcome) -> str:
    """A refusal's code, or the empty string for an answer. Read wherever the claim is "not THIS
    refusal", because `isinstance(outcome, StrategyDecision)` also asserts that the chart covers
    the spot and that the sizing table can price it - two other questions inside this one."""
    return outcome.code if isinstance(outcome, StrategyRefusal) else ""


@pytest.fixture(scope="module")
def strategy() -> PreflopChartStrategy:
    return PreflopChartStrategy.from_repo()


def charted(strategy: PreflopChartStrategy, query: StrategyQuery) -> ChartHit:
    """The cell a query reaches, or an assertion naming what stopped it short. `chart_lookup` runs
    the same forced-money and depth checks `decide` runs and returns None when either answered, so
    a hit proves the shape under test was accepted AND that the spot is one of the 249. Read
    instead of `decide` wherever the claim is about the shape rather than the action, which keeps
    the fixture from also asserting what the sizing table prices."""
    found = strategy.chart_lookup(query)
    assert found is not None, "refused before a chart was consulted at all"
    assert isinstance(found, ChartHit), found
    return found


def one_price_table(spot_key_text: str, to_bb: float) -> PreflopSizingTable:
    """A sizing table offering one price at one spot, in the shape decision 6 ruled: every raise
    size a spot offers with hero's weight on each, so an entry is a list and `amount_bb` answers
    only where that list has one member. The committed table now holds one price everywhere, so
    the fixture's work is the *value* rather than the count - it prices at 150bb, which no stack
    can pay, and the real 22.5 could never exercise the cap below."""
    schema = getattr(preflop_sizing_module, "SCHEMA_VERSION", 1)
    assert schema >= 2, "decision 6 moves the sizing table to schema 2"
    # Per class, not per spot: the 2026-08-26 ruling puts the entry under the hand class, and a
    # fixture at the superseded per-spot shape would make this file specify a payload no
    # `PreflopSizingTable` can satisfy alongside `tests/test_full_table_preflop.py`.
    entries = {name: [{"to_bb": to_bb, "weight": 1.0}] for name in HAND_CLASSES}
    return PreflopSizingTable(
        source_name="stage-4 fixture",
        source_kind="fixture",
        raise_to_bb={spot_key_text: entries},
    )


def sb_open_table(**overrides) -> StrategyQuery:
    """Folded to the small blind. The four folds are the fixture rather than scenery: they are what
    makes the spot `t6/d100/SB/rfi` rather than one of the four opening ranges in front of it, all
    of which the cutover now also commits. Hero owes 50 rather than a full big blind, the one
    arithmetic difference from the lojack tables it replaces."""
    fields = {"history": folds(*FOLDED_TO_SB), "folded": FOLDED_TO_SB}
    fields.update(overrides)
    return table_query("SB", **fields)


def three_bet_table(**overrides) -> StrategyQuery:
    """Hero opened, the cutoff three-bet at the solved price, and hero is deciding. Every seat sat
    down with 100bb, so the table is flat and the chart holds the cell. What it is not is flat in
    *held* chips: hero holds 97.5bb and the cutoff holds less again. Several claims here are this
    fixture read again, so it is written once.

    Everyone but hero and the three-bettor has folded, and that is the street rather than
    tidiness: the action cannot be back on the lojack while the blinds have yet to act. It is
    also the shape the committed node describes, the exposure clause keeping this spot because
    every terminal past it is heads-up."""
    open_to, three_bet_to, _ = solved()
    fields = {
        "contributed": paid_in(SB=SMALL_BLIND, BB=BIG_BLIND, LJ=open_to, CO=three_bet_to),
        "current_bet": three_bet_to,
        "min_raise_target": three_bet_to + (three_bet_to - open_to),
        "history": (
            raised("LJ", open_to),
            dropped("HJ"),
            raised("CO", three_bet_to),
            *folds("BTN", "SB", "BB"),
        ),
        "folded": ("HJ", "BTN", "SB", "BB"),
        "hole_cards": ("As", "Ah"),
    }
    fields.update(overrides)
    return table_query("LJ", **fields)


# 50/100 with a 200 straddle, an open to 600, the straddler and the big blind calling, the small
# blind folding: contributions of 50/600/600/600 and a pot of 1,850 where the deleted
# `small + big + voluntary * level` bound allowed 1,950. The two tests that read it are this pot
# at the two minimum-raise targets that decide whether it is straddled, written once so that
# "identical in every field but one" is a property of the code rather than of a careful reader.
MULTIWAY_CONTRIBUTIONS = paid_in(SB=SMALL_BLIND, BB=600, LJ=600, CO=600)


def multiway_table(min_raise_target: int) -> StrategyQuery:
    return table_query(
        "BTN",
        contributed=MULTIWAY_CONTRIBUTIONS,
        current_bet=600,
        min_raise_target=min_raise_target,
        history=(dropped("HJ"), raised("CO", 600), dropped("SB"), called("BB"), called("LJ")),
        folded=("HJ", "SB"),
    )


class TestRefusalVocabulary:
    def test_the_new_refusal_codes_exist_with_the_strings_the_inventory_reads(self) -> None:
        """The stage's red, and the only test here that can fail cleanly today. These strings are
        stamped into committed refusal inventories, so they are chosen in the decision list rather
        than in code and checked as values rather than by constant name. The three existing codes
        are asserted beside them because decision 16 keeps `blind-structure-not-representable`
        rather than retiring it, and a code that absorbed another would take the distinction it
        drew with it."""
        published = {
            value
            for value in vars(preflop_chart_module).values()
            if isinstance(value, str) and value.startswith("preflop-chart:")
        }

        assert REFUSE_SHORT_LIVE_SEAT in published
        assert REFUSE_STRADDLE in published
        assert REFUSE_ANTE in published
        assert REFUSE_BLIND_STRUCTURE in published
        assert REFUSE_UNEVEN_TABLE in published
        assert REFUSE_RAGGED_DEPTH in published


class TestPerSeatDepth:
    """Decision 6, ruled by Taylor on 2026-08-21: any difference at a live seat refuses."""

    def test_a_live_seat_deeper_than_hero_still_refuses_as_a_table_that_is_not_flat(
        self, strategy
    ) -> None:
        """The check that exists today keeps its code, so no spot changes meaning: a refusal
        inventory that relabelled this case could not tell a genuinely new refusal from a renamed
        old one. On hero's three-bet table rather than a lojack open, because the deep seat must be
        one that can still act, and there the cutoff is the one seat left to act."""
        deep = starting_stacks(CO=200 * BIG_BLIND)

        outcome = refusal(strategy.decide(three_bet_table(starting=deep)))

        assert outcome.code == REFUSE_UNEVEN_TABLE

    def test_a_live_seat_shallower_than_hero_refuses_with_its_own_code(self, strategy) -> None:
        """Invisible before this phase, and answered at hero's depth as if it were flat. A
        separate code rather than the existing one: "somebody is short" and "somebody is deep" are
        different tables, and merging them would leave the inventory unable to say which shape the
        chart is missing. The short seat is the big blind, the seat still to act behind the small
        blind's open."""
        short = starting_stacks(BB=40 * BIG_BLIND)

        outcome = refusal(strategy.decide(sb_open_table(starting=short)))

        assert outcome.code == REFUSE_SHORT_LIVE_SEAT

    def test_each_depth_refusal_names_the_seat_and_the_depth_it_holds(self, strategy) -> None:
        """A count of refusals is not a work list, and neither is a code on its own. Whoever
        re-rules decision 6 once real table state arrives needs which seat was off and by how much,
        which is evidence this phase can leave and cannot backfill. Two spots and so two different
        seats: a layer reporting the first live chair rather than the offending one passes a
        one-seat test."""
        short = starting_stacks(BB=40 * BIG_BLIND)
        deep = starting_stacks(CO=200 * BIG_BLIND)

        shallow_refusal = refusal(strategy.decide(sb_open_table(starting=short)))
        deep_refusal = refusal(strategy.decide(three_bet_table(starting=deep)))

        assert shallow_refusal.named("seat") == str(seat_of("BB"))
        assert shallow_refusal.named("stack_depth_bb") == "40"
        assert deep_refusal.named("seat") == str(seat_of("CO"))
        assert deep_refusal.named("stack_depth_bb") == "200"

    def test_a_seat_that_looks_short_only_because_it_has_invested_does_not_refuse(
        self, strategy
    ) -> None:
        """The whole reason starting stacks are recomputed rather than read. The cutoff holds less
        than hero's 97.5bb and neither sat down with a chip under 100bb; it is not short, it is
        three-betting, and a check reading held chips would refuse the most ordinary raised spot in
        the chart. Read as "no depth code": what the chart then answers with, and at what price, is
        another file's claim - all this one asks is that no depth code fires."""
        assert code_of(strategy.decide(three_bet_table())) not in DEPTH_CODES

    def test_hero_depth_is_measured_from_what_he_started_with_not_what_he_holds(
        self, strategy
    ) -> None:
        """Pinned on the key the lookup asked about rather than on the answer. Hero holds 9,750
        chips, not a whole big blind, and started with 100bb; asserting only that a decision came
        back would pass against a chart covering the held figure too. Through `charted`, so the
        fixture the test above shares with this one reaches a committed cell in exactly one
        place."""
        found = charted(strategy, three_bet_table())

        assert found.spot_key == solved()[2]

    def test_a_folded_seat_shallower_than_hero_does_not_make_the_table_ragged(
        self, strategy
    ) -> None:
        """The case a stricter check gets wrong first, and the one the ruling exempts: effective
        stack is pairwise and against seats that can still act, so a folded 40bb seat cannot change
        a chip of hero's decision. The folded seat is the lojack, one of the four the small blind's
        opening spot needs out of the way in any case."""
        short = starting_stacks(LJ=40 * BIG_BLIND)

        found = charted(strategy, sb_open_table(starting=short))

        assert found.spot_key == spot_key(6, 100, "SB", ())

    def test_a_folded_seat_deeper_than_hero_does_not_make_the_table_ragged(
        self, strategy
    ) -> None:
        """The same exemption in the direction the current check already refuses. Today any seat
        holding more than hero refuses, folded or not, so a rule stated only for the shallower side
        leaves this table refused - and the table is the small blind's opening spot, one of the
        five opening ranges the cutover commits."""
        deep = starting_stacks(LJ=250 * BIG_BLIND)

        found = charted(strategy, sb_open_table(starting=deep))

        assert found.spot_key == spot_key(6, 100, "SB", ())

    def test_a_ragged_hero_is_reported_before_any_villain_shape(self, strategy) -> None:
        """Decision 7's order: hero first, ahead of either villain check, because a hero whose own
        depth is not a whole big blind has no depth to compare against and the other two are then
        not well defined. Each villain shape gets its own table rather than one tripping all three,
        because one seat cannot be deeper and shallower at once. The pair is the claim the single
        table used to make."""
        ragged = 100 * BIG_BLIND + 37
        over = sb_open_table(starting=starting_stacks(SB=ragged, BB=200 * BIG_BLIND))
        under = sb_open_table(starting=starting_stacks(SB=ragged, BB=40 * BIG_BLIND))

        assert refusal(strategy.decide(over)).code == REFUSE_RAGGED_DEPTH
        assert refusal(strategy.decide(under)).code == REFUSE_RAGGED_DEPTH

    def test_a_deeper_live_seat_is_reported_before_a_shallower_one(self, strategy) -> None:
        """The rest of decision 7. Deeper keeps today's precedence, so a spot changes code only
        where this phase genuinely changed the answer for it. Saying it takes three live seats -
        hero, somebody deeper, somebody shallower - which the retired 86 could not state at all,
        every committed spot there leaving at most two players live. The cutover commits the
        lojack's own open, so the table is now one the chart holds and the control gets stronger
        rather than weaker: the same table flat is **answered**, so the refusal above is read off
        the depth check and cannot be the coverage refusal that used to be waiting behind it."""
        both = starting_stacks(BTN=200 * BIG_BLIND, CO=40 * BIG_BLIND)

        outcome = refusal(strategy.decide(table_query("LJ", starting=both)))
        control = strategy.decide(table_query("LJ"))

        assert outcome.code == REFUSE_UNEVEN_TABLE
        assert isinstance(control, StrategyDecision), control

    def test_a_hero_who_bought_in_short_refuses_because_a_live_seat_is_then_deeper(
        self, strategy
    ) -> None:
        """The sentence that reads as the same one as the test two above and is not. Hero short
        *on the street* at a flat-start table is answered; hero short because he sat down short
        is a table with a deeper seat still live, and refuses as that."""
        bought_in_short = starting_stacks(SB=40 * BIG_BLIND)

        outcome = refusal(strategy.decide(sb_open_table(starting=bought_in_short)))

        assert outcome.code == REFUSE_UNEVEN_TABLE


class TestTheChartCapsWhereTheAuditDoes:
    """Decision 11. `PreflopChartStrategy` caps a raise at the bet level plus hero's stack and
    `DecisionAuditRecord` at hero's contribution plus hero's stack, too high by exactly `to_call`
    for a hero who has invested this street. The chart moves."""

    def test_the_chart_caps_a_raise_at_what_hero_started_the_hand_with(self, strategy) -> None:
        """The public path, on the only hero the two ceilings disagree about. Only the sizing is
        replaced, by a price no stack could pay; the library, the spot key and the query are the
        real ones and the cap is what is left doing the work. Hero opened to 250 and holds 9,750,
        so hero started with 10,000 and cannot raise to a chip more, while the deleted formula
        caps at the level plus the stack - more than hero has ever had, and what
        `DecisionAuditRecord` already refuses to record. The one place this file asks for a raise,
        and the fixture is what makes that safe: the real table prices this spot at a four-bet to
        22.5, which any 100bb hero can pay, so only a price no stack covers reaches the cap."""
        capped = PreflopChartStrategy(
            library=strategy.library, sizing=one_price_table(solved()[2], 150.0)
        )

        outcome = capped.decide(three_bet_table())

        assert isinstance(outcome, StrategyDecision), outcome
        assert outcome.amount == 10000


class TestForcedMoney:
    """Decision 8's three signals, each pinned where it is the only one that can see."""

    def test_an_ante_is_found_because_every_seat_holds_more_than_the_blinds_predict(
        self, strategy
    ) -> None:
        """Signal one, reconstruction, on the case it was written for. Nothing voluntary has
        happened, so the declared blinds predict 50 and 100, the four folds predict nothing, and
        every seat has ten chips in beyond that. Uniform unexplained money is an ante, and it
        takes the ante code because an ante does not raise the level a voluntary action is
        measured against. It sits in each seat's hand figure and not its street figure, so hero
        owes what an unanted table would charge and the ten chips show only as the gap between the
        two - 50 here rather than a full big blind, because the opening seat under test is the
        small blind, which has already posted half of it."""
        query = sb_open_table(ante=10)

        assert query.to_call == BIG_BLIND - SMALL_BLIND
        assert refusal(strategy.decide(query)).code == REFUSE_ANTE

    def test_an_unraised_pot_above_the_big_blind_is_a_straddle(self, strategy) -> None:
        """Signal two, which is the whole of the limped case. Nothing has raised, so the level
        can only be the big blind. It is 200. The straddler has folded, which is what leaves the
        table one the chart would otherwise answer: the level alone is carrying the detection."""
        straddle = 2 * BIG_BLIND

        outcome = refusal(
            strategy.decide(
                sb_open_table(
                    contributed=paid_in(SB=SMALL_BLIND, BB=BIG_BLIND, LJ=straddle),
                    current_bet=straddle,
                    min_raise_target=2 * straddle,
                )
            )
        )

        assert outcome.code == REFUSE_STRADDLE

    def test_a_straddler_who_has_called_to_the_level_is_caught_by_the_minimum_raise_target(
        self, strategy
    ) -> None:
        """Signal three, on the worked case the deleted pot bound admits. The contributions above
        are exactly what an unstraddled pot at the same price produces, so reconstruction is blind
        here and so is the unraised-level rule. What is left is the price of a re-raise: the first
        raise was measured from the straddle, so the minimum is 1000 where two declared blinds and
        a recorded raise to 600 predict 1100. The pot shape is `PER-SEAT-CONTRIBUTIONS-IN-QUERY`,
        and hero is the seat still to act, which a straddled order does not literally produce -
        the claim under test is the arithmetic.

        Coverage is the claim this test cannot also make: two opponents have cold-called, and the
        exposure clause refuses the pots with two or more callers already in. Forced money is
        decided before a chart is consulted, so the code read below is this signal's."""
        outcome = refusal(strategy.decide(multiway_table(1000)))

        assert sum(MULTIWAY_CONTRIBUTIONS.values()) == 1850
        assert outcome.code == REFUSE_STRADDLE

    def test_the_same_pot_at_the_same_price_without_a_straddle_is_not_called_one(
        self, strategy
    ) -> None:
        """The false-positive channel decision 15 names, pinned as its own claim. Identical to the
        test above in every field but one: the minimum raise target is 1100, which is what 50/100
        blinds and a recorded raise to 600 predict. Nothing here is forced money, and reporting
        one would make a poker claim out of a producer's arithmetic.

        What the strategy does say is that it has no cell for the pot, and after the cutover that
        is doubly true - two opponents have cold-called, and the exposure clause refuses a pot with
        two or more callers in as well as this action order. That third answer is named rather than
        left as a silence: a signal firing here would give a straddle code and a check that had
        stopped running would give a decision, and only naming the refusal tells those apart."""
        code = code_of(strategy.decide(multiway_table(1100)))

        assert code not in FORCED_MONEY_CODES
        assert code not in DEPTH_CODES
        assert code.startswith(LOOKUP_PREFIX)

    def test_forced_money_on_a_folded_seat_that_is_neither_straddle_nor_ante_keeps_the_old_code(
        self, strategy
    ) -> None:
        """Two claims that are one table: folded seats are reconstructed, and the residual code is
        still reachable. The lojack posted a dead blind on sitting down and folded. Its hundred
        chips are in the pot, no blind and no recorded action predicts them, and no live seat
        carries anything unexplained - so a reconstruction skipping folded seats would see an
        ordinary 50/100 pot and answer it, and the pot it would answer is a committed opening
        spot. It is not a straddle, because the level is still the big blind and
        nothing has raised, and it is not an ante, because an ante is uniform and this sits on one
        seat. That is the residue decision 16 keeps the old code for."""
        contributed = paid_in(SB=SMALL_BLIND, BB=BIG_BLIND, LJ=BIG_BLIND)

        outcome = refusal(strategy.decide(sb_open_table(contributed=contributed)))

        assert outcome.code == REFUSE_BLIND_STRUCTURE
        assert outcome.named("seat") == str(seat_of("LJ"))

    def test_every_pot_the_deleted_arithmetic_bound_refused_still_refuses(
        self, strategy
    ) -> None:
        """A bound deleted before its replacement covers it is a coverage loss. Two pots the old
        `small + big + voluntary * level` bound caught: the anted table at 210 against a bound of
        150, and a 200 button straddle raised to 600 at 950 against a bound of 750. Both are now
        named rather than called too big, and both sit where the chart would otherwise answer, so
        neither refusal can be the cutover's. The anted one is the small blind's opening spot; the
        straddled one is the big blind facing a lojack raise with the straddling button folded out
        of it, one of the fifteen single-open pairs the cutover keeps."""
        anted = sb_open_table(ante=10)
        straddled = paid_in(SB=SMALL_BLIND, BB=BIG_BLIND, BTN=2 * BIG_BLIND, LJ=600)

        anted_outcome = refusal(strategy.decide(anted))
        straddled_outcome = refusal(
            strategy.decide(
                table_query(
                    "BB",
                    contributed=straddled,
                    current_bet=600,
                    min_raise_target=1000,
                    history=(raised("LJ", 600), *folds("HJ", "CO", "BTN", "SB")),
                    folded=("HJ", "CO", "BTN", "SB"),
                )
            )
        )

        assert anted.pot == 210
        assert sum(straddled.values()) == 950
        assert anted_outcome.code == REFUSE_ANTE
        assert straddled_outcome.code == REFUSE_STRADDLE

    def test_a_limper_is_explained_by_its_own_recorded_call_and_is_not_forced_money(
        self, strategy
    ) -> None:
        """Reconstruction is against the blinds *and each seat's own recorded actions*. The small
        blind holds 100 where its blind alone predicts 50, and the extra fifty is a call it is
        recorded as making; comparing against the blinds and nothing else would call the most
        common pot in a home game an anted one. The chart holds no limped spot at all - the solve
        is `limp: false`, so `t6/d100/BB/SB:call` passes all three clauses and has no node to
        derive from - so this refuses, which is why the code is read rather than the
        outcome counted: a limped pot must refuse for want of a cell, never for forced money."""
        outcome = strategy.decide(
            table_query(
                "BB",
                contributed=paid_in(SB=BIG_BLIND, BB=BIG_BLIND),
                history=(*folds(*FOLDED_TO_SB), called("SB")),
                folded=FOLDED_TO_SB,
                hole_cards=("As", "Ah"),
            )
        )

        assert isinstance(outcome, StrategyRefusal), outcome
        assert outcome.code not in FORCED_MONEY_CODES
        assert outcome.code == REFUSE_NOT_COVERED

    def test_an_ordinary_raised_pot_at_a_charted_price_is_answered_rather_than_called_straddled(
        self, strategy
    ) -> None:
        """The negative control the whole detection rests on. A 2.5bb cutoff open at 50/100 with
        the big blind closing the action is the most ordinary spot the chart holds, and after the
        cutover one of the 25 facing an open - five of them the big blind's, where hero keeps fold,
        call and three-bet. A signal firing here replaces a bound that over-refused with a rule
        that over-refuses differently. The button and the small blind fold rather than sitting
        behind hero, which is both the street the big blind actually acts on and the shape the
        committed node describes. Read as a chart hit, since what the chart answers with and at
        what price is another file's claim."""
        open_to, key = faced_open()

        found = charted(
            strategy,
            table_query(
                "BB",
                contributed=paid_in(SB=SMALL_BLIND, BB=BIG_BLIND, CO=open_to),
                current_bet=open_to,
                min_raise_target=open_to + (open_to - BIG_BLIND),
                history=(*folds("LJ", "HJ"), raised("CO", open_to), *folds("BTN", "SB")),
                folded=("LJ", "HJ", "BTN", "SB"),
                hole_cards=("As", "Ah"),
            ),
        )

        assert found.spot_key == key
