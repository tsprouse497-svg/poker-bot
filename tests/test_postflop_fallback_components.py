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
its original code. Its chart claims are made at the lojack's first-in open, which the
cutover commits, and its refusal claim at a four-bet, which the cutover excludes.

The harness comes from the sibling module by import rather than by copy, so the two halves
cannot drift apart. Both files run under `pytest_postflop_fallback`.
"""

from __future__ import annotations

import pytest
from test_postflop_fallback import (
    BEATABLE,
    BEYOND_RAISE_DEPTH_KEY,
    BOARD_NUTS,
    CHOP_ONLY,
    FALLBACK_PREFIX,
    FIRST_IN_KEY,
    NUTS,
    POSTFLOP_STREETS,
    QUAD_ACES,
    TURN_BREAKS,
    WEAK,
    beyond_raise_depth_query,
    decision,
    enumeration_queries,
    first_in_preflop_query,
    preflop_query,
    query,
    refusal,
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
    `beyond_raise_depth_query`'s and is why both are here.
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

        It used to ask in the big blind against an all-in open, on the reading that the
        cutover retired every opening range but the small blind's. That premise inverted:
        the committed set holds a first-in spot for each of the five seats that can be
        first in, so the lojack's open is answered. Which facing-an-open keys survive the
        exposure clause is not something the ruled census says - it gives 25 without naming
        them - so a claim made there would be a guess, and the first-in family is the one
        this file can stand on.

        Seven-deuce offsuit folds pure at an under-the-gun open, so the chart's answer
        needs no raise size and this stays a test about which component answered rather
        than about the sizing table; the sized case is the test below, kept apart so that
        a routing failure and a re-sizing failure never arrive as the same red.

        The menu is asserted beside the routing. `limp: false` is ruled, so no committed
        spot gives a call any weight at a first-in spot, and a call carrying weight here
        would mean the conversion invented a limp. The equality is what catches a router
        that rebuilt the query on the way through.
        """
        request = first_in_preflop_query(hole_cards=("7d", "2c"))

        outcome = decision(composite.decide(request))
        weights = dict(composite.preflop.weights_for(request))

        assert composite.preflop.chart_lookup(request).spot_key == FIRST_IN_KEY
        assert outcome.code.startswith(CHART_PREFIX)
        assert outcome == composite.preflop.decide(request)
        assert weights.get("call", 0.0) == 0.0
        assert weights.get("fold", 0.0) > 0.9

    def test_a_charted_raise_travels_out_at_the_size_the_chart_set(self, composite) -> None:
        """The composite must not re-price a charted decision, and nothing here said so.

        `composite.py` claims it in terms - `decide` returns what it received "without
        touching the amount" - and a preflop outcome that comes back fold, call or refusal
        compares `None` against `None` on both sides. A router that capped a raise to the
        query's `min_raise_target`, rounded it to whole big blinds, or clamped it to hero's
        stack would pass every one of those. It needs a query that carries a size.

        The subject is the lojack's open with aces, the sharpest one available: it is a
        spot the bot opens from rather than one it defends, it is committed by the
        first-in family, and aces raise it pure, so the collapse returns an aggressive
        action on every seed and the test cannot flap. The blinds are 50 and 100, so a
        price in big blinds is a hundred chips, and a first-in open is priced at 2.5 - the
        committed set names exactly 2.5, 7.5 and 22.5, one price per spot, with hero's own
        jam living only at the four-bet-facing spots the selection rule excludes. So 250 is
        the only amount a correct build can produce, and `> 0` would have passed for 200
        (the query's `min_raise_target`), for 300 (rounded to whole big blinds) and for
        10,000 (clamped to hero's stack rather than to the charted target).

        The two-price half of this test is gone with its premise. It paired aces against
        jacks to pin that the price sits under the hand class rather than under the spot,
        which mattered while 21 of the 86 committed spots offered a named raise and the
        jam both. One price per spot leaves the draw nothing to draw between.
        """
        request = first_in_preflop_query()

        aces = decision(composite.decide(request))
        weights = dict(composite.preflop.weights_for(request))

        assert composite.preflop.chart_lookup(request).spot_key == FIRST_IN_KEY
        assert weights.get("raise", 0.0) > 0.99
        assert aces.code.startswith(CHART_PREFIX)
        assert aces.action == "raise"
        assert aces.amount == 250
        assert aces == composite.preflop.decide(request)

    def test_a_four_bet_comes_back_as_the_charts_own_refusal(self, composite) -> None:
        """Routing a refusal is still a real case after the cutover, so it is pinned.

        This asked at the lojack's open while that spot was read as retired. The chart
        answers it now, so the refusal had to move to a spot the cutover genuinely gives
        up: hero in the big blind facing a four-bet. Three raises are already in and the
        selection rule keeps at most two, so the key is outside the committed set by a
        count of the sequence rather than by a measurement nobody here can redo - and the
        ruled census, 5 first-in plus 25 facing an open plus 219 facing a three-bet, holds
        no facing-a-four-bet family at all.

        A composite that let a refused preflop query fall through to the postflop
        component would answer it with a check or a fold and look entirely normal, which
        is why the code is asserted rather than the outcome kind. The key is asserted with
        it, so a refusal arriving for some other reason - a depth, a blind structure - does
        not read as this one.
        """
        request = beyond_raise_depth_query()

        outcome = refusal(composite.decide(request))

        assert outcome.code.startswith(CHART_PREFIX)
        assert not outcome.code.startswith(FALLBACK_PREFIX)
        assert dict(outcome.detail).get("spot_key") == BEYOND_RAISE_DEPTH_KEY
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
            first_in_preflop_query(),
            first_in_preflop_query(hole_cards=("7d", "2c")),
            beyond_raise_depth_query(),
        ):
            assert composite.decide(request) == composite.preflop.decide(request)

    def test_every_outcome_names_the_component_that_produced_it(self, composite) -> None:
        """The prefix names the component, and the kind is asserted beside it.

        Both kinds carry `preflop-chart:` - a `StrategyDecision` coded
        `preflop-chart:weighted-draw:raise[...]` and a `StrategyRefusal` coded
        `preflop-chart:lookup:spot-not-covered` are indistinguishable to `startswith`. The
        lojack's first-in spot is the one the cutover turns on: under the retired 86 it was a
        refusal and under the 249 it is an answer, so a chart shipped with every key misspelled
        would still name the right component here. The expected kind is what tells them apart.
        """
        for request in enumeration_queries():
            assert composite.decide(request).code.startswith(FALLBACK_PREFIX)

        answered = decision(composite.decide(first_in_preflop_query()))
        assert answered.code.startswith(CHART_PREFIX)
        for request in (uncovered_preflop_query(), beyond_raise_depth_query()):
            assert refusal(composite.decide(request)).code.startswith(CHART_PREFIX)
