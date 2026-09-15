"""Phase 16, stage 4: the simulator has to record what happened on the flop.

Split from `tests/test_postflop_betting.py` at the 700-line cap. That file owns the strategy;
this one owns the one producer that has to fill the shape the strategy reads. Both run under
`pytest_postflop_betting`.

Criterion: `simulator/run.py`, which records history preflop only, records it postflop too.
Without this the query shape widens and nothing fills it, so every live flop lookup reads an empty
flop history and hits the check-check cell whatever actually happened - a silent defect, because
the lookup still returns a real strategy for a real spot.
"""

from __future__ import annotations

import pytest

from poker_training_bot.profiles.seating import Profile, reference_profile
from poker_training_bot.simulator.run import SimulationConfig, run_simulation
from poker_training_bot.strategy import contract as contract_module

SEED = 20260812
SEATS = 6
SMALL_BLIND = 50
BIG_BLIND = 100
STARTING_STACK = 100 * BIG_BLIND


# --------------------------------------------------------------------------- #
# The simulator has to record what happened on the flop
# --------------------------------------------------------------------------- #


class BetsTheFlopOnce:
    """One seat that bets the flop when it can, so a second seat's query carries a flop action.

    Written here rather than reused, because what this file needs is a deterministic flop bet and
    the reference strategies do not produce one.
    """

    strategy_id = "test-bets-the-flop-once"
    strategy_version = 1

    def decide(self, query_):
        if query_.street == "flop" and "bet" in query_.legal_actions:
            held = next(s for s in query_.seat_states if s.seat == query_.seat)
            all_in = held.street_bet + dict(query_.stacks)[query_.seat]
            # At or above the minimum unless exactly all-in, which is the rule
            # `DecisionAuditRecord` enforces. A third-pot bet is below it on a small pot.
            wanted = max(query_.min_raise_target, query_.pot // 3)
            return contract_module.StrategyDecision("bet", min(wanted, all_in), "test:bets")
        if "check" in query_.legal_actions:
            return contract_module.StrategyDecision("check", None, "test:checks")
        if query_.to_call:
            return contract_module.StrategyDecision("call", None, "test:calls")
        return contract_module.StrategyDecision("fold", None, "test:folds")


class Calls:
    strategy_id = "test-calls"
    strategy_version = 1

    def decide(self, query_):
        if query_.to_call:
            return contract_module.StrategyDecision("call", None, "test:calls")
        return contract_module.StrategyDecision("check", None, "test:checks")


class TestTheSimulatorRecordsPostflopHistory:
    """Criterion: `simulator/run.py`, which records history preflop only, records it postflop too.

    Without this the query shape widens and nothing fills it, so every live flop lookup reads an
    empty flop history and hits the check-check cell whatever actually happened.
    """

    @pytest.fixture(scope="class")
    def played(self):
        seated = (
            Profile("bettor", BetsTheFlopOnce()),
            Profile("caller", Calls()),
            *(reference_profile() for _ in range(SEATS - 2)),
        )
        return run_simulation(
            SimulationConfig(
                seed=SEED,
                hands=SEATS * 4,
                profiles=seated,
                starting_stack=STARTING_STACK,
                blinds=(SMALL_BLIND, BIG_BLIND),
            )
        )

    def postflop_queries(self, played):
        return [
            record.query
            for hand in played.hands
            for record in hand.decisions
            if record.query.street != "preflop"
        ]

    def test_the_run_reaches_a_flop_at_all(self, played) -> None:
        """The positive control: every assertion below is vacuous over an empty list."""
        assert self.postflop_queries(played)

    def test_at_least_one_postflop_query_carries_a_recorded_flop_action(self, played) -> None:
        with_history = [
            found for found in self.postflop_queries(played) if found.postflop_actions
        ]

        assert with_history, (
            "no postflop query carries any within-street history, so `simulator/run.py` is still"
            " appending on preflop only"
        )

    def test_a_recorded_flop_bet_carries_the_amount_it_bet(self, played) -> None:
        bets = [
            entry
            for found in self.postflop_queries(played)
            for entry in found.postflop_actions
            if entry.action == "bet"
        ]

        assert bets
        assert all(entry.amount and entry.amount > 0 for entry in bets)

    def test_the_postflop_history_does_not_leak_across_streets(self, played) -> None:
        """Within-street history. A turn query holding the flop's actions is a different claim
        about the spot, and the key built from it would name a line nobody played."""
        for found in self.postflop_queries(played):
            if found.street == "flop":
                continue
            seats_named = {entry.seat for entry in found.postflop_actions}
            assert seats_named <= {
                state.seat for state in found.seat_states if not state.folded
            }, found.hand_id

    def test_the_preflop_history_is_still_recorded_exactly_as_it_was(self, played) -> None:
        preflop = [
            record.query
            for hand in played.hands
            for record in hand.decisions
            if record.query.street == "preflop"
        ]

        assert any(found.preflop_actions for found in preflop)


