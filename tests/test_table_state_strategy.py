"""Phase 13 strategy tests, authored at stage 4 before any implementation exists.

Everything below is a specification rather than a regression net. `StrategyQuery` does
not yet carry `seat_states` or `current_bet`, `PreflopChartStrategy` does not yet know
that a folded seat cannot make a table ragged, and the three straddle signals are not
written. So this file is red on purpose and the shape test at the top of it is the one
that reports the red as an assertion rather than as a broken import.

Two halves, both of the strategy rather than of the query. The first is per-seat depth:
a seat's starting stack is what it holds plus what it has put in, the flat-table test
runs in both directions over the seats still live in the hand, and the order the checks
fire in is ruled. The second is forced money: three signals, each pinned on a table
where it is the only one that can see anything.

What this file does not cover, because `tests/test_table_state.py` was authored beside
it and covers them: `StrategyQuery` validation, the pot reconciliation, the
decision-audit schema version, and the all-in ceiling.

Two readings this file fixes, because a stage 6 builder needs them fixed and neither the
contract nor the decision list writes them down:

- Forced money classifies as an ante when every seat carries the same unexplained
  amount. Unexplained money that is not uniform, and that neither straddle signal
  claims, is the residual `preflop-chart:blind-structure-not-representable` keeps.
  A seat's unexplained money is measured against `committed_total`, so preflop an ante
  shows up as a uniform gap between that and `street_bet`: it is in the pot and it buys
  nothing off the price, which is the coordinator's ruling and what the fixtures build.
- A refusal that names a seat does it in the vocabulary `_miss_detail` already uses:
  `seat` for the seat number and `stack_depth_bb` for the depth it holds.
"""

from __future__ import annotations

import pytest

from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.strategy import contract as contract_module
from poker_training_bot.strategy import preflop_chart as preflop_chart_module
from poker_training_bot.strategy.contract import (
    SeatAction,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy
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

FORCED_MONEY_CODES = frozenset({REFUSE_STRADDLE, REFUSE_ANTE, REFUSE_BLIND_STRUCTURE})
DEPTH_CODES = frozenset({REFUSE_RAGGED_DEPTH, REFUSE_UNEVEN_TABLE, REFUSE_SHORT_LIVE_SEAT})

# The prices the committed six-max 100bb solve actually plays at, in chips.
OPEN_TO = int(2.5 * BIG_BLIND)
THREE_BET_TO = int(8.0 * BIG_BLIND)
THREE_BET_SPOT = "t6/d100/LJ/LJ:raise@2.5,CO:raise@8"


def seat_of(position: str) -> int:
    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise AssertionError(f"no seat holds {position}")


def seat_state(
    seat: int, contributed: int, *, folded: bool, dead: int = 0, all_in: bool = False
):
    """One `SeatState`, or a TypeError saying which field phase 13 has not added yet.

    Resolved off the module rather than imported at the top so that this file collects
    and runs today: an ImportError at collection would report the whole file as broken,
    where the point of stage 4 is a red that says which behaviour is missing.

    `contributed` is what the seat has put in toward the level, which preflop is both its
    street figure and its hand figure. `dead` is money that is in the pot and buys nothing
    off the price, which is what an ante is, so it lands in `committed_total` alone. The
    coordinator ruled that; putting it in the street figure would make an anted seat owe
    less to call than an unanted one at the same level, and the gap between the two
    figures is exactly the signal the ante detection reads.
    """
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

    `contributed` is chips into the pot per seat and defaults to the two blinds.
    `starting` is what each seat sat down with and defaults to 100bb everywhere, so a
    seat's current stack is always derived rather than stated: that derivation is the
    thing under test and a fixture that stated both could state them inconsistently.

    `ante` is posted by every seat and is dead money, so it leaves each stack and enters
    the pot without moving the level or the price. Hero owes the same at an anted table
    as at an unanted one, which is the whole poker content of the coordinator's ruling.

    `min_raise_target` defaults to one big blind above an unraised level, which is the
    right number at a 50/100 table and wrong at every straddled one, so every straddled
    fixture states it. That is not incidental - it is the third signal.
    """
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


def raised(position: str, amount: int = OPEN_TO) -> SeatAction:
    return SeatAction(seat_of(position), "raise", amount)


def called(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "call")


def dropped(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "fold")


def refusal(outcome) -> StrategyRefusal:
    assert isinstance(outcome, StrategyRefusal), outcome
    return outcome


@pytest.fixture(scope="module")
def strategy() -> PreflopChartStrategy:
    return PreflopChartStrategy.from_repo()


def three_bet_table() -> StrategyQuery:
    """Hero opened to 2.5bb, the cutoff three-bet to 8bb, and hero is deciding.

    Every seat sat down with 100bb, so the table is flat and the committed chart holds
    the cell. What it is not is flat in *held* chips: hero put in 250 and holds 9,750,
    which is 97.5bb, the cutoff put in 800 and holds 9,200, which is 92bb, and the blinds
    hold 99.5bb and 99bb. Two of this phase's claims are the same fixture read twice,
    which is why it is written once.
    """
    return table_query(
        "LJ",
        contributed={
            seat_of("SB"): SMALL_BLIND,
            seat_of("BB"): BIG_BLIND,
            seat_of("LJ"): OPEN_TO,
            seat_of("CO"): THREE_BET_TO,
        },
        current_bet=THREE_BET_TO,
        min_raise_target=THREE_BET_TO + (THREE_BET_TO - OPEN_TO),
        history=(raised("LJ", OPEN_TO), raised("CO", THREE_BET_TO)),
        folded=("HJ", "BTN"),
        hole_cards=("As", "Ah"),
    )


class TestRefusalVocabulary:
    def test_the_new_refusal_codes_exist_with_the_strings_the_inventory_reads(self) -> None:
        """The stage's red, and the only test here that can fail cleanly today.

        These strings are stamped into committed refusal inventories, so they are chosen
        in the decision list rather than in code and checked as values rather than by
        constant name. The three existing codes are asserted beside them because
        decision 16 keeps `blind-structure-not-representable` rather than retiring it,
        and a code that absorbed another would take the distinction it drew with it.
        """
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
        """The check that exists today keeps its code, so no spot changes meaning.

        A refusal inventory that relabelled this case could not tell a genuinely new
        refusal from a renamed old one.
        """
        deep = {seat: FULL_STACK for seat in SEATS}
        deep[seat_of("BTN")] = 200 * BIG_BLIND

        outcome = refusal(strategy.decide(table_query("LJ", starting=deep)))

        assert outcome.code == REFUSE_UNEVEN_TABLE

    def test_a_live_seat_shallower_than_hero_refuses_with_its_own_code(self, strategy) -> None:
        """Invisible before this phase, and answered at hero's depth as if it were flat.

        A separate code rather than the existing one: "somebody is short" and "somebody
        is deep" are different tables, and merging them would leave the inventory unable
        to say which shape the chart is missing.
        """
        short = {seat: FULL_STACK for seat in SEATS}
        short[seat_of("CO")] = 40 * BIG_BLIND

        outcome = refusal(strategy.decide(table_query("LJ", starting=short)))

        assert outcome.code == REFUSE_SHORT_LIVE_SEAT

    def test_each_depth_refusal_names_the_seat_and_the_depth_it_holds(self, strategy) -> None:
        """A count of refusals is not a work list, and neither is a code on its own.

        Whoever re-rules decision 6 once real table state arrives needs which seat was
        off and by how much, which is evidence this phase can leave and cannot backfill.
        """
        short = {seat: FULL_STACK for seat in SEATS}
        short[seat_of("CO")] = 40 * BIG_BLIND
        deep = {seat: FULL_STACK for seat in SEATS}
        deep[seat_of("BTN")] = 200 * BIG_BLIND

        shallow_refusal = refusal(strategy.decide(table_query("LJ", starting=short)))
        deep_refusal = refusal(strategy.decide(table_query("LJ", starting=deep)))

        assert shallow_refusal.named("seat") == str(seat_of("CO"))
        assert shallow_refusal.named("stack_depth_bb") == "40"
        assert deep_refusal.named("seat") == str(seat_of("BTN"))
        assert deep_refusal.named("stack_depth_bb") == "200"

    def test_a_seat_that_looks_short_only_because_it_has_invested_does_not_refuse(
        self, strategy
    ) -> None:
        """The whole reason starting stacks are recomputed rather than read.

        The cutoff holds 92bb against hero's 97.5bb, and neither of them sat down with a
        chip less than 100bb. The cutoff is not short, it is three-betting, and a check
        reading held chips would refuse the most ordinary spot in the chart.
        """
        outcome = strategy.decide(three_bet_table())

        assert isinstance(outcome, StrategyDecision), outcome

    def test_hero_depth_is_measured_from_what_he_started_with_not_what_he_holds(
        self, strategy
    ) -> None:
        """Pinned on the key the lookup asked about rather than on the answer.

        Hero holds 9,750 chips, which is not a whole big blind at all, and started with
        100bb. Asserting only that a decision came back would pass against a chart that
        happened to cover the held figure too.
        """
        found = strategy.chart_lookup(three_bet_table())

        assert found is not None
        assert found.spot_key == THREE_BET_SPOT

    def test_a_folded_seat_shallower_than_hero_does_not_make_the_table_ragged(
        self, strategy
    ) -> None:
        """The case a stricter check gets wrong first, and the one the ruling exempts.

        Effective stack is pairwise and against seats that can still act, so a folded
        40bb seat cannot change a chip of hero's decision.
        """
        short = {seat: FULL_STACK for seat in SEATS}
        short[seat_of("LJ")] = 40 * BIG_BLIND

        outcome = strategy.decide(
            table_query("HJ", starting=short, history=(dropped("LJ"),), folded=("LJ",))
        )

        assert isinstance(outcome, StrategyDecision), outcome

    def test_a_folded_seat_deeper_than_hero_does_not_make_the_table_ragged(
        self, strategy
    ) -> None:
        """The same exemption in the direction the current check already refuses.

        Today any seat holding more than hero refuses, folded or not, so a rule stated
        only for the shallower side leaves this table refused.
        """
        deep = {seat: FULL_STACK for seat in SEATS}
        deep[seat_of("LJ")] = 250 * BIG_BLIND

        outcome = strategy.decide(
            table_query("HJ", starting=deep, history=(dropped("LJ"),), folded=("LJ",))
        )

        assert isinstance(outcome, StrategyDecision), outcome

    def test_a_ragged_hero_is_reported_before_any_villain_shape(self, strategy) -> None:
        """Decision 7's order, on a table that trips all three checks at once.

        Hero first because a hero whose own depth is not a whole big blind has no depth
        to compare against, so the other two are not well defined.
        """
        ragged = {seat: FULL_STACK for seat in SEATS}
        ragged[seat_of("LJ")] = 100 * BIG_BLIND + 37
        ragged[seat_of("BTN")] = 200 * BIG_BLIND
        ragged[seat_of("CO")] = 40 * BIG_BLIND

        outcome = refusal(strategy.decide(table_query("LJ", starting=ragged)))

        assert outcome.code == REFUSE_RAGGED_DEPTH

    def test_a_deeper_live_seat_is_reported_before_a_shallower_one(self, strategy) -> None:
        """The rest of decision 7, on a table that trips both villain checks.

        Deeper keeps today's precedence, so a spot changes code only where this phase
        genuinely changed the answer for it.
        """
        both = {seat: FULL_STACK for seat in SEATS}
        both[seat_of("BTN")] = 200 * BIG_BLIND
        both[seat_of("CO")] = 40 * BIG_BLIND

        outcome = refusal(strategy.decide(table_query("LJ", starting=both)))

        assert outcome.code == REFUSE_UNEVEN_TABLE

    def test_a_hero_who_bought_in_short_refuses_because_a_live_seat_is_then_deeper(
        self, strategy
    ) -> None:
        """The sentence that reads as the same one as the test two above and is not.

        Hero short *on the street* at a flat-start table is answered. Hero short because
        he sat down short is a table with five seats deeper, and refuses as that.
        """
        bought_in_short = {seat: FULL_STACK for seat in SEATS}
        bought_in_short[seat_of("LJ")] = 40 * BIG_BLIND

        outcome = refusal(strategy.decide(table_query("LJ", starting=bought_in_short)))

        assert outcome.code == REFUSE_UNEVEN_TABLE


class TestTheChartCapsWhereTheAuditDoes:
    """Decision 11. `PreflopChartStrategy` caps a raise at the bet level plus hero's stack
    and `DecisionAuditRecord` at hero's own contribution plus hero's stack, too high by
    exactly `to_call` for a hero who has already invested this street. The chart moves."""

    def test_the_chart_caps_a_raise_at_what_hero_started_the_hand_with(
        self, strategy
    ) -> None:
        """The public path, on the only hero the two ceilings disagree about.

        The committed sizing table tops out at 28.5bb against a 100bb hero, so no spot in
        it can reach either ceiling and no fixture built from it can tell the two apart.
        Only the sizing is replaced, by a price no stack could pay; the library, the spot
        key and the query are the real ones, and the cap is what is left doing the work.

        Hero opened to 250 and holds 9,750, so hero started with 10,000 and cannot raise
        to a chip more. The formula this phase deletes caps at the bet level plus the
        stack, 800 + 9,750 = 10,550, which is 550 more than hero has ever had and is the
        amount `DecisionAuditRecord` already refuses to record.
        """
        unpayable = PreflopSizingTable(
            source_name="stage-4 fixture",
            source_kind="fixture",
            raise_to_bb={THREE_BET_SPOT: 150.0},
        )
        capped = PreflopChartStrategy(library=strategy.library, sizing=unpayable)

        outcome = capped.decide(three_bet_table())

        assert isinstance(outcome, StrategyDecision), outcome
        assert outcome.amount == 10000


class TestForcedMoney:
    """Decision 8's three signals, each pinned where it is the only one that can see."""

    def test_an_ante_is_found_because_every_seat_holds_more_than_the_blinds_predict(
        self, strategy
    ) -> None:
        """Signal one, reconstruction, on the case it was written for.

        Nobody has acted, so the declared blinds predict 50 and 100 and nothing else.
        Every seat has ten chips in the pot beyond that. Uniform unexplained money is an
        ante, and it takes the ante code because an ante does not raise the level a
        voluntary action is measured against, and the two change the ranges differently.

        The ante is in each seat's hand figure and not in its street figure, so hero owes
        the full big blind and the ten chips are visible only as the gap between the two.
        A fixture that discounted the price would pin an ante buying ten chips off it.
        """
        query = table_query("LJ", ante=10)

        assert query.to_call == BIG_BLIND
        assert refusal(strategy.decide(query)).code == REFUSE_ANTE

    def test_an_unraised_pot_above_the_big_blind_is_a_straddle(self, strategy) -> None:
        """Signal two, which is the whole of the limped case.

        Nothing has raised, so the level can only be the big blind. It is 200.
        """
        straddle = 2 * BIG_BLIND
        contributed = {
            seat_of("SB"): SMALL_BLIND,
            seat_of("BB"): BIG_BLIND,
            seat_of("LJ"): straddle,
        }

        outcome = refusal(
            strategy.decide(
                table_query(
                    "HJ",
                    contributed=contributed,
                    current_bet=straddle,
                    min_raise_target=2 * straddle,
                )
            )
        )

        assert outcome.code == REFUSE_STRADDLE

    def test_a_straddler_who_has_called_to_the_level_is_caught_by_the_minimum_raise_target(
        self, strategy
    ) -> None:
        """Signal three, on the worked case the deleted pot bound admits.

        50/100 with a 200 straddle, an open to 600, the straddler and the big blind
        calling, the small blind folding. The pot is 1,850 where the old bound allowed
        1,950, so it slipped through. The contributions are 50/600/600/600, which is
        exactly what an unstraddled pot at the same price produces, so reconstruction is
        blind here and so is the unraised-level rule. What is left is the price of a
        re-raise: the first raise was measured from the straddle rather than from the
        big blind, so the minimum is 1000 where two declared blinds and a recorded raise
        to 600 predict 1100.

        The pot shape is the one named in `PER-SEAT-CONTRIBUTIONS-IN-QUERY`. Hero is the
        seat still to act, which a straddled betting order does not literally produce -
        the claim under test is the arithmetic, and the query is expressible either way.
        """
        contributed = {
            seat_of("SB"): SMALL_BLIND,
            seat_of("BB"): 600,
            seat_of("LJ"): 600,
            seat_of("CO"): 600,
        }
        outcome = refusal(
            strategy.decide(
                table_query(
                    "BTN",
                    contributed=contributed,
                    current_bet=600,
                    min_raise_target=1000,
                    history=(
                        dropped("HJ"),
                        raised("CO", 600),
                        dropped("SB"),
                        called("BB"),
                        called("LJ"),
                    ),
                    folded=("HJ", "SB"),
                )
            )
        )

        assert sum(contributed.values()) == 1850
        assert outcome.code == REFUSE_STRADDLE

    def test_the_same_pot_at_the_same_price_without_a_straddle_is_not_called_one(
        self, strategy
    ) -> None:
        """The false-positive channel decision 15 names, pinned as its own claim.

        Identical to the test above in every field but one: the minimum raise target is
        1100, which is what 50/100 blinds and a recorded raise to 600 predict. Nothing
        here is forced money, and reporting one would make a poker claim out of a
        producer's arithmetic.
        """
        contributed = {
            seat_of("SB"): SMALL_BLIND,
            seat_of("BB"): 600,
            seat_of("LJ"): 600,
            seat_of("CO"): 600,
        }
        outcome = strategy.decide(
            table_query(
                "BTN",
                contributed=contributed,
                current_bet=600,
                min_raise_target=1100,
                history=(
                    dropped("HJ"),
                    raised("CO", 600),
                    dropped("SB"),
                    called("BB"),
                    called("LJ"),
                ),
                folded=("HJ", "SB"),
            )
        )

        code = outcome.code if isinstance(outcome, StrategyRefusal) else ""

        assert code not in FORCED_MONEY_CODES
        assert code not in DEPTH_CODES

    def test_forced_money_on_a_folded_seat_that_is_neither_straddle_nor_ante_keeps_the_old_code(
        self, strategy
    ) -> None:
        """Two claims that are one table: folded seats are reconstructed, and the
        residual code is still reachable.

        The lojack posted a dead blind on sitting down and folded. Its hundred chips are
        in the pot, no blind and no recorded action predicts them, and no live seat
        carries anything unexplained - so a reconstruction that skipped folded seats
        would see an ordinary 50/100 pot and answer it. It is not a straddle, because
        the level is still the big blind and nothing has raised, and it is not an ante,
        because an ante is uniform and this sits on one seat. That is precisely the
        residue decision 16 keeps `blind-structure-not-representable` for.
        """
        contributed = {
            seat_of("SB"): SMALL_BLIND,
            seat_of("BB"): BIG_BLIND,
            seat_of("LJ"): BIG_BLIND,
        }

        outcome = refusal(
            strategy.decide(
                table_query(
                    "HJ",
                    contributed=contributed,
                    history=(dropped("LJ"),),
                    folded=("LJ",),
                )
            )
        )

        assert outcome.code == REFUSE_BLIND_STRUCTURE

    def test_every_pot_the_deleted_arithmetic_bound_refused_still_refuses(
        self, strategy
    ) -> None:
        """A bound deleted before its replacement covers it is a coverage loss.

        Two pots the old `small + big + voluntary * level` bound caught: the anted
        table at 210 against a bound of 150, and a 200 button straddle raised to 600 at
        950 against a bound of 750. Both are now named rather than called too big.
        """
        anted = table_query("LJ", ante=10)

        straddled = {
            seat_of("SB"): SMALL_BLIND,
            seat_of("BB"): BIG_BLIND,
            seat_of("BTN"): 2 * BIG_BLIND,
            seat_of("LJ"): 600,
        }

        anted_outcome = refusal(strategy.decide(anted))
        straddled_outcome = refusal(
            strategy.decide(
                table_query(
                    "HJ",
                    contributed=straddled,
                    current_bet=600,
                    min_raise_target=1000,
                    history=(raised("LJ", 600),),
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
        """Reconstruction is against the blinds *and each seat's own recorded actions*.

        The small blind holds 100 where its blind alone predicts 50, and the extra fifty
        is a call it is recorded as making. Comparing against the blinds and nothing
        else would call the most common pot in a home game an anted one.
        """
        contributed = {seat_of("SB"): BIG_BLIND, seat_of("BB"): BIG_BLIND}

        outcome = strategy.decide(
            table_query(
                "BB",
                contributed=contributed,
                history=(
                    dropped("LJ"),
                    dropped("HJ"),
                    dropped("CO"),
                    dropped("BTN"),
                    called("SB"),
                ),
                folded=("LJ", "HJ", "CO", "BTN"),
                hole_cards=("As", "Ah"),
            )
        )

        assert isinstance(outcome, StrategyDecision), outcome

    def test_an_ordinary_raised_pot_at_a_charted_price_is_answered_rather_than_called_straddled(
        self, strategy
    ) -> None:
        """The negative control the whole detection rests on.

        A 2.5bb cutoff open at 50/100 with the big blind to act is the most ordinary
        spot the chart holds. A signal firing here replaces a bound that over-refused
        with a rule that over-refuses differently.
        """
        contributed = {
            seat_of("SB"): SMALL_BLIND,
            seat_of("BB"): BIG_BLIND,
            seat_of("CO"): OPEN_TO,
        }

        outcome = strategy.decide(
            table_query(
                "BB",
                contributed=contributed,
                current_bet=OPEN_TO,
                min_raise_target=OPEN_TO + (OPEN_TO - BIG_BLIND),
                history=(dropped("LJ"), dropped("HJ"), raised("CO", OPEN_TO)),
                folded=("LJ", "HJ"),
                hole_cards=("As", "Ah"),
            )
        )

        assert isinstance(outcome, StrategyDecision), outcome
