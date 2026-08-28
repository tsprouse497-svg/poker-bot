"""The pieces around the postflop fallback: its codes, its predicate, and its composite.

The companion to `tests/test_postflop_fallback.py`, split from it when the pair went past
the 700-line cap. That file owns the shared harness - the engine-derived betting shapes,
the named card scenarios, and the query builders - along with every test of what
`PostflopFallbackStrategy.decide` returns. The line between the two is that nothing here
calls `decide`, which is also why nothing here needs that file's fixtures.

`TestOutcomeCodes` pins the vocabulary every outcome is labelled with, so an audit line
can be attributed to a component without reading code.

`TestUnbeatableFunction` covers `hand_cannot_lose`, the predicate behind the only place
this bot puts money in postflop, as named cards a reviewer can check by hand. Two bars are
pinned there: a tie is not a loss, so a hand every holding chops calls; and the turn claim
has to survive every river card rather than only the board as it stands.

`TestComposite` pins that the composite this strategy is a component of adds no decision
of its own: for every query in the enumeration its outcome is the outcome its component
returns when asked directly, and a preflop chart refusal comes back as a refusal carrying
its original code.

The harness comes from the sibling module by import rather than by copy, so the two halves
cannot drift apart. Both files run under `pytest_postflop_fallback`.
"""

from __future__ import annotations

import pytest
from test_postflop_fallback import (
    BEATABLE,
    BOARD_NUTS,
    CHOP_ONLY,
    FALLBACK_PREFIX,
    NUTS,
    POSTFLOP_STREETS,
    QUAD_ACES,
    TURN_BREAKS,
    WEAK,
    decision,
    enumeration_queries,
    preflop_query,
    query,
    refusal,
    retired_preflop_query,
    shape_with,
)

from poker_training_bot.strategy.composite import CompositeStrategy
from poker_training_bot.strategy.contract import (
    StrategyDecision,
    StrategyProtocol,
    StrategyQuery,
)
from poker_training_bot.strategy.postflop_fallback import (
    CODE_CALL_UNBEATABLE,
    CODE_CHECK,
    CODE_FOLD_CAN_LOSE,
    CODE_FOLD_ON_THE_FLOP,
    REFUSE_NOT_POSTFLOP,
    hand_cannot_lose,
)

CHART_PREFIX = "preflop-chart:"


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


def uncovered_preflop_query() -> StrategyQuery:
    """A flat 40bb table: no committed chart holds that depth, so the chart refuses.

    Flat matters, because a starting stack is what a seat holds plus what it put in and a
    table that is not one depth refuses on shape before the spot is ever looked up. Its
    refusal is `lookup:no-artifact-for-stack-depth`, which is a different reason from
    `retired_preflop_query`'s and is why both are here.
    """
    return preflop_query(depth_bb=40)


@pytest.fixture(scope="module")
def composite() -> CompositeStrategy:
    return CompositeStrategy.from_repo()


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
        """The subject is the routing, and the spot is chosen so the routing is all it tests.

        It used to ask at the lojack's opening range, which the cutover retires. The open
        hero faces here is for the whole stack, and `t6/d100/BB/BTN:raise@100` is one of the
        50 committed spots offering hero fold and call and nothing else - so the chart's
        answer needs no raise size, and this stays a test about which component answered
        rather than about the sizing table. A spot offering two prices was ruled on
        2026-08-26 - having decided to raise, the strategy draws the price with the seed
        it already collapses a mixed cell with - and the sized case is the test below,
        kept apart so that a routing failure and a re-sizing failure never arrive as the
        same red.

        What is asserted is no longer that the action is fold or call. `preflop_query` leaves
        hero exactly those two legal actions here, and `preflop_chart.py` refuses any drawn
        action outside the legal set, so that held for every possible implementation and for
        the fallback's own answers too. What is asserted instead is that the composite hands
        back the chart's own answer untouched, at a spot whose menu really is the two: a router
        that rebuilt the query on the way through, and a converter that put a raise branch under
        an all-in, both fail here and neither failed before.
        """
        request = preflop_query(open_to_bb=100)

        outcome = decision(composite.decide(request))
        weights = dict(composite.preflop.weights_for(request))

        assert outcome.code.startswith(CHART_PREFIX)
        assert outcome == composite.preflop.decide(request)
        assert weights.get("raise", 0.0) == 0.0
        assert weights.get("call", 0.0) > 0.9

    def test_a_charted_raise_travels_out_at_the_size_the_chart_set(self, composite) -> None:
        """The composite must not re-price a charted decision, and nothing here said so.

        `composite.py` claims it in terms - `decide` returns what it received "without
        touching the amount" - and every preflop outcome this file asserts over comes back
        fold, call or refusal, so the amount compared on both sides is `None` in all of
        them. A router that capped a raise to the query's `min_raise_target`, rounded it to
        whole big blinds, or clamped it to hero's stack would pass every one. A fallback
        layer silently re-sizing a decision the chart already priced is exactly the defect
        this file exists to catch, and it needs a query that actually carries a size.

        Both subjects sit in the big blind against a button open to 2.5, which keys to
        `t6/d100/BB/BTN:raise@2.5` - committed, and one of the 21 spots offering hero a
        named raise and the jam both: the 20 whose menu is fold, call, raise and jam, plus
        `t6/d100/SB/rfi`, which offers the raise and the jam with no call at all. Both put
        all their weight on the raise branch and none on fold or call, read off export node
        `(0,0,0,1,0)`, so the collapse returns an aggressive action on every seed and
        neither can flap. The blinds are 50 and 100, so a price in big blinds is a hundred
        chips each and the spot's menu is 750 or 10,000.

        Aces are the single-price half and are pinned exactly. The 2026-08-26 ruling put
        the weights under the hand class, and measured at that node aces raise to 7.5 with
        weight 1.0 and jam with weight 0 - so aces have one price, the draw has nothing to
        draw between, and 750 is the only amount a correct build can produce. `> 0` passed
        for 400 (the query's `min_raise_target`), for 800 (rounded to whole big blinds) and
        for 9,900 (clamped to hero's remaining stack rather than to the all-in target);
        every one of those now fails.

        Jacks are the two-price half, which is what the ruling is actually about and what
        nothing in this file asserted. JJ splits its aggression 0.3687 against 0.6313 over
        the same two prices, so which one arrives is the seed's business and is deliberately
        not pinned - but it must be one of the two the chart holds, and a table that priced
        the spot rather than the class would have to answer aces and jacks alike. Note that
        `t6/d100/SB/rfi` is not the same shape and must never be pinned at two prices: of its
        169 classes 118 carry the 2.5 alone, aces among them, 45 fold pure and carry no price
        at all, and six carry both. 163 counts those 45 as priced.

        The small blind's open would be the sharper subject, being the one spot the bot
        opens from at all. No query builder reaches it, and the harness is the sibling
        module's to grow rather than this file's to copy, so the claim is frozen at the
        seat the existing fixture reaches; the routing it exercises is the same one.
        """
        one_price = preflop_query()
        two_prices = preflop_query(hole_cards=("Jd", "Jc"))

        aces = decision(composite.decide(one_price))
        jacks = decision(composite.decide(two_prices))

        assert aces.code.startswith(CHART_PREFIX)
        assert aces.action == "raise"
        assert aces.amount == 750
        assert aces == composite.preflop.decide(one_price)

        assert jacks.action == "raise"
        assert jacks.amount in {750, 10_000}, jacks
        assert jacks == composite.preflop.decide(two_prices)

    def test_a_retired_preflop_spot_comes_back_as_the_charts_own_refusal(
        self, composite
    ) -> None:
        """Routing a refusal is the common case after the cutover, so it is pinned.

        The chart answers 86 spots and refuses everything else, and the lojack's open is
        one of the fourteen it gives up. A composite that let a refused preflop query fall
        through to the postflop component would answer it with a check or a fold and look
        entirely normal, which is why the code is asserted rather than the outcome kind.
        """
        request = retired_preflop_query()

        outcome = refusal(composite.decide(request))

        assert outcome.code.startswith(CHART_PREFIX)
        assert not outcome.code.startswith(FALLBACK_PREFIX)
        assert outcome == composite.preflop.decide(request)

    def test_postflop_queries_are_answered_by_the_fallback(self, composite) -> None:
        for street in POSTFLOP_STREETS:
            free = query(shape_with("fold", "check", "bet"), street, WEAK)
            assert decision(composite.decide(free)).code.startswith(FALLBACK_PREFIX), street

    # A preflop chart refusal passes through carrying its original reason code; a passive
    # action would erase the coverage signal Phases 04 and 05 were built to produce.
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
        for request in (
            preflop_query(open_to_bb=100),
            preflop_query(hole_cards=("7d", "2c")),
            retired_preflop_query(),
        ):
            assert composite.decide(request) == composite.preflop.decide(request)

    def test_every_outcome_names_the_component_that_produced_it(self, composite) -> None:
        for request in enumeration_queries():
            assert composite.decide(request).code.startswith(FALLBACK_PREFIX)
        for request in (
            preflop_query(open_to_bb=100),
            uncovered_preflop_query(),
            retired_preflop_query(),
        ):
            assert composite.decide(request).code.startswith(CHART_PREFIX)
