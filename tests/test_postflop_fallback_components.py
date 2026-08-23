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
    """A flat 40bb table: no committed chart holds that depth, so the chart refuses. Flat
    matters now that a starting stack is what a seat holds plus what it put in - the old
    fixture left 4,000 in front of a blind that had posted 50, which refuses on shape."""
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
        outcome = decision(composite.decide(preflop_query()))

        assert outcome.code.startswith(CHART_PREFIX)

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
        for request in (preflop_query(), preflop_query(hole_cards=("7d", "2c"))):
            assert composite.decide(request) == composite.preflop.decide(request)

    def test_every_outcome_names_the_component_that_produced_it(self, composite) -> None:
        for request in enumeration_queries():
            assert composite.decide(request).code.startswith(FALLBACK_PREFIX)
        for request in (preflop_query(), uncovered_preflop_query()):
            assert composite.decide(request).code.startswith(CHART_PREFIX)
