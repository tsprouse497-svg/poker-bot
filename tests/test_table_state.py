"""What `StrategyQuery` says about the table, once it says what every seat has put in.

Authored at loop stage 4, before any of it exists. Nothing in this file passes today and
that is the point: these tests are the specification the stage 6 builder is measured
against, and stage 5 freezes them so the builder cannot edit the target it is aiming at.

That creates one mechanical problem, and two rules answer it. The first test in the file
is a shape test driven by `dataclasses.fields`, which fails with a clean `AssertionError`
and gives the stage its red. The per-seat record type is reached through
`_seat_state_class()` at call time rather than imported at the top, so its absence is an
assertion inside a test rather than a collection error across the whole file. Every other
test is written the way it should read once the phase is built.

The names, with the inner fields from Phase 13 decisions 1, 2, 4, 5 and 14 and the container
and class ruled by the coordinator during the build and recorded in the ExecPlan:

* `StrategyQuery.seat_states`, a required tuple sorted by seat, one entry per seated
  seat, with no default - a producer may not omit it.
* `SeatState(seat, street_bet, committed_total, folded=False, all_in=False)`,
  exported from `poker_training_bot.strategy.contract`. The two chip names are the
  engine's own names on `PlayerState` for the same two quantities.
* `StrategyQuery.street_bet` becomes `StrategyQuery.current_bet`, matching
  `BettingRoundState.current_bet`, so the per-seat `street_bet` above is the only
  `street_bet` left and it means what the engine has always meant by it.
* In `to_payload()`, `seat_states` serializes as a mapping keyed by the seat as text,
  mirroring `stacks`, whose seats it is validated against.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest

from poker_training_bot.strategy import contract as contract_module
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy


def _seat_state_class() -> Any:
    """The per-seat record type, resolved at call time rather than imported.

    Before stage 6 this raises `AssertionError` from inside whichever test asked for it,
    where a module-scope import would raise `ImportError` during collection and report as
    an error on every test in the file, telling the loop nothing about what is unmet.
    """
    seat_contribution = getattr(contract_module, "SeatState", None)
    assert seat_contribution is not None, (
        "poker_training_bot.strategy.contract.SeatState does not exist yet;"
        " this file is the specification for it"
    )
    return seat_contribution


def seat_state(
    seat: int,
    street_bet: int,
    committed_total: int | None = None,
    *,
    folded: bool = False,
    all_in: bool = False,
) -> Any:
    """One seat's chips. Preflop the two figures coincide, so the second is optional here,
    in this helper only: on the record itself both are required, because a default is how
    a producer that never learned about the field still constructs.
    """
    if committed_total is None:
        committed_total = street_bet
    return _seat_state_class()(
        seat=seat,
        street_bet=street_bet,
        committed_total=committed_total,
        folded=folded,
        all_in=all_in,
    )


def make_preflop_query(**overrides: Any) -> StrategyQuery:
    """Three-handed 50/100, button opens to 300, small blind folds, hero is the big blind.

    Hero has already put 100 in front of it, which is the situation every arithmetic in
    this phase differs on: a hero who has invested this street is exactly where the bet
    level and hero's own contribution stop being the same number. Contributions
    50 + 100 + 300 make the pot of 450, and every seat started with 10,000.
    """
    fields: dict[str, Any] = {
        "hand_id": "open-into-the-big-blind",
        "street": "preflop",
        "seat": 1,
        "button_seat": 2,
        "hole_cards": ("As", "Kd"),
        "board": (),
        "legal_actions": ("fold", "call", "raise"),
        "to_call": 200,
        "current_bet": 300,
        "min_raise_target": 500,
        "pot": 450,
        "stacks": ((0, 9950), (1, 9900), (2, 9700)),
        "seat_states": (
            seat_state(0, 50, folded=True),
            seat_state(1, 100),
            seat_state(2, 300),
        ),
        "blinds": (50, 100),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def make_flop_query(**overrides: Any) -> StrategyQuery:
    """A flop where 300 each went in preflop and the button has bet 200 into it.

    Postflop is the street the two per-seat figures are carried for: hero's street
    contribution is 0 while its hand contribution is 300, and the pot is made of the second.
    """
    fields: dict[str, Any] = {
        "hand_id": "bet-into-the-turned-caller",
        "street": "flop",
        "seat": 1,
        "button_seat": 0,
        "hole_cards": ("As", "Kd"),
        "board": ("2c", "7h", "Ts"),
        "legal_actions": ("fold", "call", "raise"),
        "to_call": 200,
        "current_bet": 200,
        "min_raise_target": 400,
        "pot": 800,
        "stacks": ((0, 9500), (1, 9700)),
        "seat_states": (seat_state(0, 200, 500), seat_state(1, 0, 300)),
        "blinds": (50, 100),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def make_record(**overrides: Any) -> DecisionAuditRecord:
    fields: dict[str, Any] = {
        "schema_version": DECISION_AUDIT_SCHEMA_VERSION,
        "strategy_id": "table-state-fixture",
        "strategy_version": 1,
        "query": make_preflop_query(),
        "outcome": StrategyDecision("call", None, "x"),
    }
    fields.update(overrides)
    return DecisionAuditRecord(**fields)


class TestTheShapeOfTheQuery:
    """The first test here is the one that goes red cleanly before anything is built."""

    def test_the_query_names_the_bet_level_current_bet_and_carries_contributions(self) -> None:
        names = {field.name for field in dataclasses.fields(StrategyQuery)}

        assert "seat_states" in names, "the query must carry what each seat has put in"
        assert "current_bet" in names, "the street's bet level is now called current_bet"
        assert "street_bet" not in names, (
            "street_bet on the query meant the bet level and on the engine means a seat's"
            " own contribution; the query keeps neither reading of the name"
        )

    def test_the_contributions_field_has_no_default_so_no_producer_can_skip_it(self) -> None:
        """A field a producer may omit is a field the depth derivation guesses behind."""
        field = next(
            candidate
            for candidate in dataclasses.fields(StrategyQuery)
            if candidate.name == "seat_states"
        )

        assert field.default is dataclasses.MISSING
        assert field.default_factory is dataclasses.MISSING

    def test_the_per_seat_record_uses_the_engine_s_own_four_names(self) -> None:
        """One vocabulary across the engine and the query, or a reader translates."""
        names = [field.name for field in dataclasses.fields(_seat_state_class())]

        assert names == ["seat", "street_bet", "committed_total", "folded", "all_in"]

    def test_both_chip_figures_are_required_on_the_record(self) -> None:
        record_fields = {
            field.name: field for field in dataclasses.fields(_seat_state_class())
        }

        for name in ("street_bet", "committed_total"):
            assert record_fields[name].default is dataclasses.MISSING, name

    def test_the_decision_audit_schema_version_moved_because_the_payload_did(self) -> None:
        """Two payload shapes under one version number is the defect this repo already has."""
        assert DECISION_AUDIT_SCHEMA_VERSION == 3


class TestEverySeatIsAccountedFor:
    def test_a_table_where_every_seat_has_an_entry_constructs(self) -> None:
        query = make_preflop_query()

        assert dict(query.stacks).keys() == {entry.seat for entry in query.seat_states}
        assert query.current_bet == 300

    def test_a_seated_player_with_no_contribution_entry_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="seat_state"):
            make_preflop_query(
                seat_states=(seat_state(0, 50, folded=True), seat_state(1, 100))
            )

    def test_a_contribution_entry_for_a_seat_that_is_not_at_the_table_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="seat_state"):
            make_preflop_query(
                seat_states=(
                    seat_state(0, 50, folded=True),
                    seat_state(1, 100),
                    seat_state(2, 300),
                    seat_state(5, 0),
                )
            )

    def test_two_entries_for_one_seat_are_rejected(self) -> None:
        """The seat sets would still match, so a set comparison alone does not catch it."""
        with pytest.raises(ValueError, match="seat_state"):
            make_preflop_query(
                seat_states=(
                    seat_state(0, 50, folded=True),
                    seat_state(1, 100),
                    seat_state(2, 300),
                    seat_state(2, 300),
                )
            )

    def test_contributions_out_of_seat_order_are_rejected(self) -> None:
        """`stacks` is sorted for byte determinism and this is validated against it."""
        with pytest.raises(ValueError, match="seat_state"):
            make_preflop_query(
                seat_states=(
                    seat_state(2, 300),
                    seat_state(1, 100),
                    seat_state(0, 50, folded=True),
                )
            )

    def test_a_folded_seat_keeps_the_chips_it_already_put_in(self) -> None:
        """Its chips are in the pot whatever it does next, so the entry stays."""
        query = make_preflop_query()
        folded = next(entry for entry in query.seat_states if entry.seat == 0)

        assert folded.folded is True
        assert folded.committed_total == 50

    def test_dropping_a_folded_seat_is_how_a_pot_stops_reconciling(self) -> None:
        """Dropped from `stacks` and `seat_states` together the seat sets still agree, so
        the rule that bites is the pot's: 450 chips are stated and 400 are accounted for."""
        with pytest.raises(ValueError):
            make_preflop_query(
                stacks=((1, 9900), (2, 9700)),
                seat_states=(seat_state(1, 100), seat_state(2, 300)),
            )


class TestThePotIsMadeOfWhatTheSeatsPutIn:
    def test_a_pot_one_chip_above_the_contributions_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="pot"):
            make_preflop_query(pot=451)

    def test_a_pot_one_chip_below_the_contributions_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="pot"):
            make_preflop_query(pot=449)

    def test_a_pot_holding_chips_no_seat_contributed_is_rejected(self) -> None:
        """The postflop enumeration builds `100 + current_bet + hero_street_bet`, and the
        100 belongs to nobody. Dead money nobody can account for is a defect in the
        producer, not a validation to relax.
        """
        with pytest.raises(ValueError, match="pot"):
            make_flop_query(pot=900)

    def test_the_pot_is_the_sum_of_hand_contributions_and_not_of_street_contributions(
        self,
    ) -> None:
        """On the flop those are 800 and 200, so a producer summing the wrong one is caught."""
        query = make_flop_query()

        assert sum(entry.committed_total for entry in query.seat_states) == 800
        assert sum(entry.street_bet for entry in query.seat_states) == 200
        assert query.pot == 800

    def test_a_seat_holding_more_this_street_than_all_hand_is_rejected(self) -> None:
        """The one direction that is impossible on any street: a seat cannot have put
        more into this street than it has put in over the whole hand."""
        with pytest.raises(ValueError):
            make_preflop_query(
                pot=650,
                seat_states=(
                    seat_state(0, 50, folded=True),
                    seat_state(1, 300, 100),
                    seat_state(2, 300),
                ),
            )

    def test_preflop_a_seat_may_hold_more_over_the_hand_than_on_the_street(self) -> None:
        """An ante is dead money: it goes into the pot and it does not count toward what a
        seat owes, so an anted seat's hand figure is above its street figure preflop even
        though there is no earlier street. The first draft of decision 3 said the two
        coincide preflop, which would have made an anted pot unconstructable, and decision
        10 requires exactly such a pot. The difference between the two figures is that
        seat's dead money, which is also the signal decision 8 reads an ante by.
        """
        query = make_preflop_query(
            pot=480,
            seat_states=(
                seat_state(0, 50, 60, folded=True),
                seat_state(1, 100, 110),
                seat_state(2, 300, 310),
            ),
        )
        dead = {entry.seat: entry.committed_total - entry.street_bet for entry in query.seat_states}

        assert dead == {0: 10, 1: 10, 2: 10}

    def test_an_ante_does_not_reduce_what_hero_owes(self) -> None:
        """The poker statement of the same rule, and the reason the ante cannot live in
        the street figure: hero still owes the full difference to the level."""
        query = make_preflop_query(
            pot=480,
            seat_states=(
                seat_state(0, 50, 60, folded=True),
                seat_state(1, 100, 110),
                seat_state(2, 300, 310),
            ),
        )
        hero = next(entry for entry in query.seat_states if entry.seat == query.seat)

        assert query.to_call == query.current_bet - hero.street_bet == 200

    def test_after_the_flop_the_two_contributions_are_free_to_differ(self) -> None:
        """The preflop rule must not be applied to every street, or no flop query builds."""
        query = make_flop_query()
        hero = next(entry for entry in query.seat_states if entry.seat == 1)

        assert (hero.street_bet, hero.committed_total) == (0, 300)


class TestToCallIsThePriceHeroCanActuallyPay:
    """Taylor's ruling of 2026-08-20, enforced in the one place every producer passes."""

    def test_a_price_above_hero_s_stack_is_rejected_because_hero_cannot_pay_it(self) -> None:
        with pytest.raises(ValueError, match="to_call"):
            make_preflop_query(
                to_call=9901,
                current_bet=10001,
                min_raise_target=20001,
                pot=10251,
                seat_states=(
                    seat_state(0, 50, folded=True),
                    seat_state(1, 100),
                    seat_state(2, 10101),
                ),
                stacks=((0, 9950), (1, 9900), (2, 0)),
            )

    def test_a_hero_all_in_for_the_call_is_still_expressible(self) -> None:
        """Phase 06's short hero restated: `0 < stack < to_call` is now unsatisfiable, and
        the situation survives as `to_call == stack`."""
        query = make_preflop_query(
            to_call=9900,
            current_bet=10000,
            min_raise_target=19900,
            legal_actions=("fold", "call"),
            pot=10150,
            seat_states=(
                seat_state(0, 50, folded=True),
                seat_state(1, 100),
                seat_state(2, 10000),
            ),
            stacks=((0, 9950), (1, 9900), (2, 0)),
        )

        assert query.to_call == dict(query.stacks)[query.seat]

    def test_a_hero_all_in_for_the_call_cannot_be_offered_a_raise(self) -> None:
        """The engine never offers it, and until now the query validated it happily. This
        is the only route by which the all-in ceiling accepts a raise hero cannot make, so
        it is the guard the capped ruling was found to be missing.
        """
        with pytest.raises(ValueError, match="raise"):
            make_preflop_query(
                to_call=9900,
                current_bet=10000,
                min_raise_target=19900,
                legal_actions=("fold", "call", "raise"),
                pot=10150,
                seat_states=(
                    seat_state(0, 50, folded=True),
                    seat_state(1, 100),
                    seat_state(2, 10000),
                ),
                stacks=((0, 9950), (1, 9900), (2, 0)),
            )

    def test_a_seat_with_nothing_behind_cannot_be_offered_a_bet(self) -> None:
        """The same rule at a price of zero: hero owes nothing and has nothing to bet."""
        with pytest.raises(ValueError, match="bet"):
            make_flop_query(
                to_call=0,
                current_bet=0,
                min_raise_target=100,
                legal_actions=("check", "bet"),
                pot=1000,
                seat_states=(seat_state(0, 0, 500), seat_state(1, 0, 500)),
                stacks=((0, 9500), (1, 0)),
            )

    def test_a_seat_with_nothing_behind_may_still_be_offered_a_check(self) -> None:
        """The guard removes an aggressive action, not the seat's ability to be asked."""
        query = make_flop_query(
            to_call=0,
            current_bet=0,
            min_raise_target=100,
            legal_actions=("check",),
            pot=1000,
            seat_states=(seat_state(0, 0, 500), seat_state(1, 0, 500)),
            stacks=((0, 9500), (1, 0)),
        )

        assert query.legal_actions == ("check",)

    def test_a_hero_with_chips_behind_the_call_keeps_its_raise(self) -> None:
        """The control. A guard that refused every raise would pass the two tests above."""
        query = make_preflop_query()

        assert query.to_call < dict(query.stacks)[query.seat]
        assert "raise" in query.legal_actions


class TestHeroSOwnContributionIsReadRatherThanSubtracted:
    def _capped_hero_query(self) -> StrategyQuery:
        """The case the decision list works out, at a big blind of 10. Hero holds 150 and
        has put 100 into a level of 300, so hero started with 250, which is 25bb. The price
        is 200 uncapped and 150 once capped at what hero holds.
        """
        return StrategyQuery(
            hand_id="capped-short-hero",
            street="preflop",
            seat=1,
            button_seat=0,
            hole_cards=("As", "Kd"),
            board=(),
            legal_actions=("fold", "call"),
            to_call=150,
            current_bet=300,
            min_raise_target=600,
            pot=400,
            stacks=((0, 700), (1, 150)),
            seat_states=(seat_state(0, 300), seat_state(1, 100)),
            blinds=(5, 10),
        )

    def test_hero_s_contribution_is_carried_rather_than_recovered_from_the_price(self) -> None:
        query = self._capped_hero_query()
        hero = next(entry for entry in query.seat_states if entry.seat == 1)

        assert hero.street_bet == 100
        assert query.current_bet - query.to_call == 150, (
            "the subtraction identity gives 150 here, which is not what hero put in;"
            " it was right until to_call was capped and is wrong for exactly the"
            " capped population"
        )

    def test_the_depth_the_contribution_gives_is_25bb_and_the_subtraction_gives_30bb(
        self,
    ) -> None:
        query = self._capped_hero_query()
        _, big_blind = query.blinds
        hero_stack = dict(query.stacks)[query.seat]
        hero = next(entry for entry in query.seat_states if entry.seat == 1)

        assert (hero_stack + hero.street_bet) / big_blind == 25
        assert (hero_stack + (query.current_bet - query.to_call)) / big_blind == 30

    def test_a_seat_s_starting_stack_is_what_it_holds_plus_what_it_put_in(self) -> None:
        """A short villain and an invested villain stop being the same picture."""
        query = self._capped_hero_query()
        stacks = dict(query.stacks)
        starting = {
            entry.seat: stacks[entry.seat] + entry.committed_total
            for entry in query.seat_states
        }

        assert starting == {0: 1000, 1: 250}

    def _ragged_only_when_read_correctly(self) -> StrategyQuery:
        """The same capped hero at the 50/100 blinds, sized so the two readings part.

        The button opened to 300, hero three-bet to 1,000 out of a 2,450 stack, the button
        re-raised all-in to 3,000, and hero holds 1,450 against a price capped at exactly
        that. Read from hero's own contribution hero started with 1,450 + 1,000 = 2,450,
        which is 24.5 big blinds; recovered by subtraction it is 3,000, a clean 30bb.
        """
        return make_preflop_query(
            legal_actions=("fold", "call"),
            to_call=1450,
            current_bet=3000,
            min_raise_target=5000,
            pot=4050,
            stacks=((0, 9950), (1, 1450), (2, 0)),
            seat_states=(
                seat_state(0, 50, folded=True),
                seat_state(1, 1000),
                seat_state(2, 3000),
            ),
            preflop_actions=(
                SeatAction(2, "raise", 300),
                SeatAction(0, "fold"),
                SeatAction(1, "raise", 1000),
                SeatAction(2, "raise", 3000),
            ),
        )

    def test_the_chart_refuses_the_depth_hero_actually_has_rather_than_the_subtracted_one(
        self,
    ) -> None:
        """The derivation measured rather than restated, which the two tests above cannot do.

        A capped hero cannot exist at a flat table - the level would have to exceed hero's
        whole starting stack - so what separates the two derivations is hero's own
        raggedness, checked before any villain is looked at. The true depth is 24.5bb and
        refuses; the subtracted one is a whole 30bb and gets past this check entirely.
        """
        outcome = PreflopChartStrategy.from_repo().decide(
            self._ragged_only_when_read_correctly()
        )

        assert isinstance(outcome, StrategyRefusal), outcome
        assert outcome.code == "preflop-chart:stack-depth-not-a-whole-big-blind"


class TestTheTwoAllInCeilingsBecomeOne:
    """`DecisionAuditRecord` capped at hero's contribution plus hero's stack and
    `PreflopChartStrategy` capped at the bet level plus hero's stack, differing by exactly
    `to_call`. The chart half is pinned in `tests/test_table_state_strategy.py`, on a hero
    who has already invested this street, which is the only hero the two disagree about."""

    def test_the_ceiling_is_hero_s_contribution_plus_what_hero_holds(self) -> None:
        record = make_record(outcome=StrategyDecision("raise", 100 + 9900, "x"))

        assert '"amount":10000' in record.to_json_line()

    def test_the_ceiling_is_exactly_what_hero_started_the_hand_with(self) -> None:
        """The poker statement of the same number: hero cannot put in more than it had."""
        query = make_preflop_query()
        hero = next(entry for entry in query.seat_states if entry.seat == query.seat)

        assert hero.committed_total + dict(query.stacks)[query.seat] == 10000

    def test_a_raise_to_the_bet_level_plus_hero_s_stack_is_more_than_hero_has(self) -> None:
        """The chart's old ceiling, which the audit must reject rather than agree with."""
        with pytest.raises(ValueError, match="all-in maximum"):
            make_record(outcome=StrategyDecision("raise", 300 + 9900, "x"))

    def test_the_two_ceilings_differ_by_exactly_the_price_to_call(self) -> None:
        query = make_preflop_query()
        hero_stack = dict(query.stacks)[query.seat]
        hero = next(entry for entry in query.seat_states if entry.seat == query.seat)
        chart_ceiling = query.current_bet + hero_stack
        audit_ceiling = hero.street_bet + hero_stack

        assert chart_ceiling - audit_ceiling == query.to_call == 200

    def test_a_raise_one_chip_over_the_ceiling_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="all-in maximum"):
            make_record(outcome=StrategyDecision("raise", 10001, "x"))

    def test_a_raise_at_the_minimum_is_still_accepted(self) -> None:
        """The control: a ceiling low enough to reject legal raises would be no better."""
        record = make_record(outcome=StrategyDecision("raise", 500, "x"))

        assert '"amount":500' in record.to_json_line()


class TestTheSerializedQuery:
    def test_the_payload_names_the_bet_level_current_bet_and_no_longer_street_bet(self) -> None:
        payload = make_preflop_query().to_payload()

        assert payload["current_bet"] == 300
        assert "street_bet" not in payload

    def test_the_payload_carries_every_seat_s_chips_and_markers(self) -> None:
        payload = make_preflop_query().to_payload()

        assert payload["seat_states"] == {
            "0": {
                "street_bet": 50,
                "committed_total": 50,
                "folded": True,
                "all_in": False,
            },
            "1": {
                "street_bet": 100,
                "committed_total": 100,
                "folded": False,
                "all_in": False,
            },
            "2": {
                "street_bet": 300,
                "committed_total": 300,
                "folded": False,
                "all_in": False,
            },
        }

    def test_the_payload_keys_the_contributions_the_same_way_it_keys_the_stacks(self) -> None:
        """They are validated seat for seat against each other, so they read the same."""
        payload = make_preflop_query().to_payload()

        assert payload["seat_states"].keys() == payload["stacks"].keys()

    def test_the_audit_line_carries_the_moved_schema_version(self) -> None:
        assert '"schema_version":3' in make_record().to_json_line()

    def test_a_record_at_the_old_schema_version_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="schema_version"):
            make_record(schema_version=2)

    def test_the_audit_line_stays_byte_deterministic(self) -> None:
        assert make_record().to_json_line() == make_record().to_json_line()

    def test_the_audit_line_is_still_json(self) -> None:
        payload = json.loads(make_record().to_json_line())

        assert payload["query"]["seat_states"]["1"]["committed_total"] == 100


class TestTheMarkersMakeTwoTablesTellApart:
    def test_a_folded_seat_and_a_live_seat_do_not_serialize_alike(self) -> None:
        """Decision 5. Nothing else in the query distinguishes them: a folded seat's chips
        are in the pot either way, so the reconciliation is identical."""
        folded = make_preflop_query()
        live = make_preflop_query(
            seat_states=(seat_state(0, 50), seat_state(1, 100), seat_state(2, 300))
        )

        assert folded.pot == live.pot
        assert folded.to_payload() != live.to_payload()

    def test_a_short_all_in_caller_and_a_full_caller_do_not_serialize_alike(self) -> None:
        """Phase 12 handed this on by name: `SeatAction` forbids an amount on a call, so
        the button's call is one identical record in both tables below. It called the full
        300 in the first and was all-in for 250 in the second, and after the action record
        has been read the only thing left saying which is the marker. Four seats with the
        button at 3, so there is a caller sitting behind the raiser for it to happen to.
        """
        history = (
            SeatAction(2, "raise", 300),
            SeatAction(3, "call"),
            SeatAction(0, "fold"),
        )
        rest = (seat_state(0, 50, folded=True), seat_state(1, 100), seat_state(2, 300))
        full_caller = make_preflop_query(
            button_seat=3,
            preflop_actions=history,
            pot=750,
            stacks=((0, 9950), (1, 9900), (2, 9700), (3, 9700)),
            seat_states=(*rest, seat_state(3, 300)),
        )
        short_all_in = make_preflop_query(
            button_seat=3,
            preflop_actions=history,
            pot=700,
            stacks=((0, 9950), (1, 9900), (2, 9700), (3, 0)),
            seat_states=(*rest, seat_state(3, 250, all_in=True)),
        )
        full_payload = full_caller.to_payload()
        short_payload = short_all_in.to_payload()

        assert full_caller.preflop_actions == short_all_in.preflop_actions
        assert full_payload["seat_states"]["3"]["all_in"] is False
        assert short_payload["seat_states"]["3"]["all_in"] is True
        assert full_payload != short_payload

    def test_the_all_in_marker_is_not_derived_from_an_empty_stack(self) -> None:
        """Decision 14. A seat all-in on an earlier street holds zero with no all-in this
        street, and a seat that sat down with nothing holds zero having never acted."""
        query = make_flop_query(
            to_call=0,
            current_bet=0,
            min_raise_target=100,
            legal_actions=("check",),
            pot=1000,
            seat_states=(seat_state(0, 0, 500), seat_state(1, 0, 500)),
            stacks=((0, 9500), (1, 0)),
        )
        broke = next(entry for entry in query.seat_states if entry.seat == 1)

        assert dict(query.stacks)[1] == 0
        assert broke.all_in is False
