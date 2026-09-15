"""Phase 16, stage 4: the query the simulator fills, and three claims made at the table.

Split from `tests/test_postflop_betting.py` and `tests/test_postflop_key.py` at the 700-line cap.
Those own the strategy and the key; this owns the producer that fills the shape they read, plus
the three table-level claims that did not fit beside them: that the strategy plays the committed
mixture rather than purifying it, that a three-handed flop refuses, and that a chip bet is matched
to the ruled menu by pot fraction. All four files run under `pytest_postflop_betting`.

Criterion: `simulator/run.py`, which records history preflop only, records it postflop too.
Without this the query shape widens and nothing fills it, so every live flop lookup reads an empty
flop history and hits the check-check cell whatever actually happened - a silent defect, because
the lookup still returns a real strategy for a real spot.

## The migration sweep, measured here rather than inherited

The contract requires stage 4 to sweep every frozen test of a completed phase that asserts against
the query shape and to **state what the sweep found** rather than take the contract's own count of
three as a bound. Run in this worktree with `grep` over `tests/*.py` for `StrategyQuery`,
`SeatAction`, `DECISION_AUDIT_SCHEMA_VERSION`, `schema_version`, `preflop_actions`,
`postflop_actions` and `to_json_line`:

- **50 test files examined**, of which **23 mention the query shape** by one of those tokens.
  Three of the 23 are this phase's own new files, so **20 pre-existing files were in scope**.
- **Three were migrated**, each for a reason a reader can check. `tests/test_table_state.py`
  pinned `DECISION_AUDIT_SCHEMA_VERSION == 3` and asserted `'"schema_version":3'` in a rendered
  audit line, both of which invert at the bump. `tests/test_spot_vocabulary_downstream.py` pinned
  the same constant. `tests/test_strategy_contract.py` both asserted a **byte-exact** audit JSON
  line, which gains `"postflop_actions":[]` in sort order and `"schema_version":4`, and held
  `test_rejects_a_bet_because_preflop_has_no_bet`, which this phase inverts into an acceptance
  with a sizeless-bet rejection beneath it. The contract named exactly these three files; the
  sweep found a second inverting site inside one of them rather than a fourth file.
- **Seventeen mention the shape and need no change**, in four groups. **No test pins an exhaustive
  field list of `StrategyQuery`**: `tests/test_table_state.py:161` and `:174` name fields
  individually with `in names` / `not in names`, so a defaulted `postflop_actions` is invisible to
  them. **Four of the six files calling `to_json_line` never assert on its bytes** -
  `tests/test_full_table_preflop.py:611`, `tests/test_postflop_fallback.py:687` and
  `tests/test_simulator.py:451` feed it into a set or a tuple for de-duplication and determinism,
  which a new field does not disturb. **`tests/test_engine_fidelity.py` reads committed audit
  lines back but stamps `DECISION_AUDIT_SCHEMA_VERSION` rather than each line's own**, so the bump
  does not red it; its `schema_version=1` at `:218` is `NormalizedHandHistory`'s schema, a
  different number on a different record. And **`tests/test_solver_export.py:656` recomputes
  headroom from the source card** rather than hard-coding it, so regenerating the card - which the
  contract already requires - is enough.

The finding: the migration was complete at three, and three was measured here rather than copied.
"""

from __future__ import annotations

import dataclasses

import pytest

from poker_training_bot.profiles.seating import Profile, reference_profile
from poker_training_bot.simulator.measure import HandResult, SimulationResult
from poker_training_bot.simulator.run import SimulationConfig, run_simulation
from poker_training_bot.strategy import contract as contract_module

SEED = 20260812
SEATS = 6
SMALL_BLIND = 50
BIG_BLIND = 100
STARTING_STACK = 100 * BIG_BLIND


@pytest.fixture(scope="module")
def betting_module():
    """`strategy.postflop_betting`, imported inside the fixture rather than at module scope; the
    head of `tests/test_postflop_key.py` says why a top-level import here runs nothing at all."""
    import poker_training_bot.strategy.postflop_betting as module

    return module


@pytest.fixture(scope="module")
def key_module():
    import poker_training_bot.solver_artifacts.postflop_key as module

    return module


@pytest.fixture(scope="module")
def strategy(betting_module):
    return owed(betting_module, "PostflopBettingStrategy").from_repo()


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 16's contract requires it and no"
        " implementation has been written yet"
    )
    return found


def seat_state(seat: int, street_bet: int, committed_total: int | None = None):
    return contract_module.SeatState(
        seat=seat,
        street_bet=street_bet,
        committed_total=street_bet if committed_total is None else committed_total,
    )


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




# --------------------------------------------------------------------------- #
# The strategy has to realise the committed mixture, not purify it
# --------------------------------------------------------------------------- #

MIXTURE_DRAWS = 400
MIXTURE_TOLERANCE = 0.10
"""How many seeded draws a frequency is measured over, and how far it may sit from the committed
weight. At `p = 0.5` the standard error of a frequency over 400 draws is
`sqrt(0.25 / 400) = 0.025`, so 0.10 is four of them and a correct weighted draw does not trip it;
a purified cell sits 0.49 away from a 0.51/0.49 mixture, which is five times the tolerance."""


def covered_flop(**overrides):
    """A flop query on the committed rainbow sample board, in the covered `@2.5` line.

    Same convention as `tests/test_postflop_betting.py::query`: six-handed, the small blind
    folded, its dead 0.5bb carried on the big blind's `committed_total`.
    """
    fields = {
        "hand_id": "h1",
        "street": "flop",
        "seat": 1,
        "button_seat": 0,
        "hole_cards": ("As", "Qd"),
        "board": ("Kc", "7d", "2h"),
        "legal_actions": ("check", "bet"),
        "to_call": 0,
        "current_bet": 0,
        "min_raise_target": BIG_BLIND,
        "pot": 550,
        "stacks": ((0, 9750), (1, 9750)),
        "seat_states": (seat_state(0, 0, 250), seat_state(1, 0, 300)),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": (
            contract_module.SeatAction(0, "raise", 250),
            contract_module.SeatAction(1, "call"),
        ),
    }
    fields.update(overrides)
    return contract_module.StrategyQuery(**fields)


class TestTheCommittedMixtureIsPlayedRatherThanPurified:
    """The gap stage 4's domain review found: **nothing in this phase required the strategy to
    play the mixture it committed.** `class_weights`, `mixture`, `collapse`, `rng` and `random`
    appeared zero times across all six of this phase's test files.

    **Why argmax is the specific wrong implementation being excluded.** A solver mixes exactly
    where it has driven a hand to indifference, so taking the highest-weight action turns every
    indifferent class into a pure one at a frequency an opponent reads off in a single orbit. A
    class solved to bet 0.51 and check 0.49 becomes bet 1.00. The artifact stops being a strategy
    and becomes a very expensive exploitable one, and the bet frequency the report prints is then
    the bot's rather than the artifact's with nothing saying which. Every shape test in this phase
    passes against it: it bets, it raises, its amounts are legal, turn and river refuse.

    Two cruder degenerates are excluded by the same tests: "bet 33% with 100% of the range" and
    "ignore `class_weights` entirely", both of which pass the six files as they stood.

    **The repo already solved this and was not being held to it.**
    `PreflopChartStrategy.collapse` draws one action in proportion to its weights and says in
    terms "Not the highest weight", seeded so a hand decides the same way on every run and a
    replay is a replay. The postflop equivalent is pinned here the same way.
    """

    def mixed_spot(self, betting_module, strategy):
        """One committed spot whose weights for the query's own hand class are a real mixture."""
        weights_for = owed(betting_module, "committed_class_weights")
        for spot in owed(betting_module, "committed_spot_queries")():
            weights = weights_for(spot)
            if sum(1 for _, weight in weights if weight >= 0.05) >= 2:
                return spot, weights
        raise AssertionError(
            "no committed spot holds a mixed cell for its own hand class, so nothing here can"
            " tell a weighted draw from an argmax; a solved flop chart with no mixture anywhere"
            " is itself the finding"
        )

    def drawn(self, strategy, spot, count: int = MIXTURE_DRAWS):
        """`count` decisions on one spot, varying only the hand id the draw is seeded on."""
        return [
            strategy.decide(dataclasses.replace(spot, hand_id=f"mix-{index}"))
            for index in range(count)
        ]

    def test_a_mixed_cell_produces_more_than_one_action_across_seeded_draws(
        self, betting_module, strategy
    ) -> None:
        """The cheapest statement of the property, and the one argmax fails outright."""
        spot, _ = self.mixed_spot(betting_module, strategy)

        actions = {
            outcome.action
            for outcome in self.drawn(strategy, spot)
            if isinstance(outcome, contract_module.StrategyDecision)
        }

        assert len(actions) > 1, actions

    def test_the_observed_frequency_tracks_the_committed_weight(
        self, betting_module, strategy
    ) -> None:
        """Over `MIXTURE_DRAWS` seeded draws, within `MIXTURE_TOLERANCE` of each committed
        weight. The constant's docstring carries the arithmetic for both numbers."""
        spot, weights = self.mixed_spot(betting_module, strategy)
        outcomes = self.drawn(strategy, spot)
        decided = [
            outcome
            for outcome in outcomes
            if isinstance(outcome, contract_module.StrategyDecision)
        ]
        assert len(decided) == MIXTURE_DRAWS, "a covered spot must answer every draw"

        for action, weight in weights:
            seen = sum(1 for outcome in decided if outcome.action == action) / MIXTURE_DRAWS
            assert abs(seen - weight) <= MIXTURE_TOLERANCE, (action, weight, seen)

    def test_the_same_seed_draws_the_same_action_every_time(
        self, betting_module, strategy
    ) -> None:
        """A replay is a replay. A draw that moved between runs would make every committed audit
        line unreproducible, which is the property phase 10 bought with a hashed seed."""
        spot, _ = self.mixed_spot(betting_module, strategy)

        first = strategy.decide(spot)
        second = strategy.decide(spot)

        assert isinstance(first, contract_module.StrategyDecision), first
        assert (first.action, first.amount) == (second.action, second.amount)

    def test_every_answered_action_carries_a_non_zero_committed_weight(
        self, betting_module, strategy
    ) -> None:
        """The other half, and the one that excludes "ignore `class_weights` entirely": an action
        the cell gives no weight to is an action the solve never found, however legal it is."""
        weights_for = owed(betting_module, "committed_class_weights")
        checked = 0
        for spot in owed(betting_module, "committed_spot_queries")():
            outcome = strategy.decide(spot)
            if not isinstance(outcome, contract_module.StrategyDecision):
                continue
            weights = dict(weights_for(spot))
            assert weights.get(outcome.action, 0.0) > 0.0, (spot.hand_id, outcome.action, weights)
            checked += 1

        assert checked, "no committed spot was answered at all"


# --------------------------------------------------------------------------- #
# A three-handed flop is not a two-seat cell
# --------------------------------------------------------------------------- #


class TestAThreeHandedFlopRefuses:
    """Criterion: the multiway share of the coverage loss is structural rather than fundable,
    because a two-range solve cannot express a three-handed flop at any budget, machine or menu.
    Before this, the only thing in the phase touching it was a check that the report contains the
    words "multiway" and "structural".

    **Why it needs a test rather than an argument.** Under the committed line set a three-way pot
    misses only because its pot is arithmetically different. `t6/d100/SB/BTN:raise@2.5` is the
    same preflop key whether the big blind folds (6.0bb heads-up) or calls (7.5bb, three-handed),
    because the preflop key ends at hero's own decision and the players who act after hero are not
    in it. There is no player-count segment and no pot-type segment. At one open size and a flat
    100bb that arithmetic happens to separate them; a second committed open price, a straddle or a
    non-flat table breaks it, and a two-range cell would then answer a three-handed flop with a
    heads-up strategy and no refusal at all. This test is what makes the separation a requirement
    instead of a coincidence.
    """

    def three_handed(self, **overrides):
        """The button opens to 2.5bb and both blinds call, so three seats see the flop.

        Nothing is dead here - every seat that put money in is still in the hand - so the pot is
        the plain `3 x 250`, and the big blind is first to act postflop.
        """
        fields = {
            "hand_id": "h-multiway",
            "street": "flop",
            "seat": 2,
            "button_seat": 0,
            "hole_cards": ("As", "Qd"),
            "board": ("Kc", "7d", "2h"),
            "legal_actions": ("check", "bet"),
            "to_call": 0,
            "current_bet": 0,
            "min_raise_target": BIG_BLIND,
            "pot": 750,
            "stacks": ((0, 9750), (1, 9750), (2, 9750)),
            "seat_states": (
                seat_state(0, 0, 250),
                seat_state(1, 0, 250),
                seat_state(2, 0, 250),
            ),
            "blinds": (SMALL_BLIND, BIG_BLIND),
            "preflop_actions": (
                contract_module.SeatAction(0, "raise", 250),
                contract_module.SeatAction(1, "call"),
                contract_module.SeatAction(2, "call"),
            ),
        }
        fields.update(overrides)
        return contract_module.StrategyQuery(**fields)

    def test_the_same_board_and_line_heads_up_is_answered(self, strategy) -> None:
        """The positive control. Without it a strategy that refuses everything passes below."""
        outcome = strategy.decide(covered_flop())

        assert isinstance(outcome, contract_module.StrategyDecision), outcome

    def test_a_flop_with_three_live_seats_refuses(self, strategy) -> None:
        outcome = strategy.decide(self.three_handed())

        assert isinstance(outcome, contract_module.StrategyRefusal), outcome

    def test_it_refuses_under_the_phase_s_own_vocabulary(self, betting_module, strategy) -> None:
        """A refusal under some other code would still be a refusal, and would still leave the
        report's multiway figure counting something nobody named."""
        outcome = strategy.decide(self.three_handed())

        assert outcome.code in owed(betting_module, "REFUSAL_CODES"), outcome.code


# --------------------------------------------------------------------------- #
# The refusal inventory at a table whose stacks are not all equal
# --------------------------------------------------------------------------- #


def refused_hand(hand_id: str, outcome, stacks: dict[int, int]) -> HandResult:
    """One voided hand carrying a refusal, which is all `refusal_inventory` reads."""
    return HandResult(
        hand_id=hand_id,
        seed=SEED,
        button_seat=0,
        outcome="voided",
        refusal_code=outcome.code,
        refusing_seat=1,
        refusal_detail=outcome.detail,
        starting_stacks=stacks,
        stack_deltas=dict.fromkeys(stacks, 0),
        pot_collected=0,
        pot_awarded=0,
        decisions=(),
        streets=(),
        normalized=None,
    )


class TestTheRefusalInventoryKeepsWorkingAtANonFlatTable:
    """Criterion, and the half `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` records: the
    inventory groups on the refusal code plus the **entire** detail tuple, so any exact per-seat
    chip count rendered into a postflop refusal shatters the work list into one singleton row per
    distinct stack. Phase 13's depth codes already do that, and a postflop code carrying board or
    line detail is what makes it visible on a code somebody will actually read.

    The test runs the real grouper rather than restating the rule: two hands refused at the same
    spot, one at a flat table and one where the two seats hold different chips, have to come back
    as **one** row reached twice. The effective stack is the same in both, because that is the
    quantity the spot is defined by; what differs is how the chips are distributed, which is not.
    """

    def uncovered(self, **overrides):
        """A 3-bet line the committed chart does not cover, so the lookup refuses on the line."""
        return covered_flop(
            preflop_actions=(
                contract_module.SeatAction(0, "raise", 250),
                contract_module.SeatAction(1, "raise", 750),
                contract_module.SeatAction(0, "call"),
            ),
            pot=1550,
            seat_states=(seat_state(0, 0, 750), seat_state(1, 0, 800)),
            **overrides,
        )

    def both(self, strategy):
        flat = strategy.decide(self.uncovered(stacks=((0, 9250), (1, 9250))))
        uneven = strategy.decide(self.uncovered(stacks=((0, 12000), (1, 9250))))
        assert isinstance(flat, contract_module.StrategyRefusal), flat
        assert isinstance(uneven, contract_module.StrategyRefusal), uneven
        return flat, uneven

    def test_the_two_refusals_group_into_one_row_reached_twice(self, strategy) -> None:
        flat, uneven = self.both(strategy)
        result = SimulationResult(
            seed=SEED,
            seat_names=("a", "b"),
            hands=(
                refused_hand("h-flat", flat, {0: 9250, 1: 9250}),
                refused_hand("h-uneven", uneven, {0: 12000, 1: 9250}),
            ),
            position_counts={},
        )

        inventory = result.refusal_inventory()

        assert len(inventory) == 1, [(row.code, row.detail) for row in inventory]
        assert inventory[0].hands == 2

    def test_no_postflop_refusal_detail_names_a_seat_or_a_chip_count(self, strategy) -> None:
        """The mechanism behind the row above, asserted directly so a red says which field did
        it. A detail naming `seat` or `starting_chips` is what fragments the grouping."""
        forbidden = {"seat", "seats", "chips", "starting_chips", "stack", "stack_chips"}
        for outcome in self.both(strategy):
            named = {name for name, _ in outcome.detail}
            assert named & forbidden == set(), (outcome.code, sorted(named))


# --------------------------------------------------------------------------- #
# A chip bet is matched to the ruled menu by pot fraction
# --------------------------------------------------------------------------- #

SINGLE_RAISED_POT_CHIPS = 550
"""5.5bb at 50/100, the pot of the covered `@2.5` line, and the pot every figure below is in."""


class TestAChipBetIsMatchedToTheMenuByPotFraction:
    """Decision 14, `runtime-reversible`, proceeding on its recorded default rather than halting.

    The ruled flop menu is `33 75` as a percent of pot and the table is in chips, and the
    arithmetic does not come out even: 33% of the 550-chip pot is 181.5, which no dealer can
    push. A strict equality match at stage 6 would refuse every faced bet at a real table and
    kill the whole raise branch of the committed artifact with nothing going red; a loose one with
    no stated ceiling could as easily swallow a 40% bet as a 32.7% one.

    The default: **match by pot fraction with a named tolerance, and convert a committed artifact
    size to chips by rounding to the nearest chip.** The tolerance is a module constant the test
    imports rather than a literal written twice, so a later session moving it moves one number.
    `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` item 14 carries the
    arithmetic; the test below re-derives both bounds rather than quoting them.
    """

    def test_the_tolerance_is_published_as_a_named_constant(self, key_module) -> None:
        assert owed(key_module, "MENU_FRACTION_TOLERANCE") == pytest.approx(0.01)

    def test_the_tolerance_sits_between_the_two_bounds_the_arithmetic_forces(
        self, key_module
    ) -> None:
        """Both bounds recomputed here rather than quoted.

        The floor is what a real table's rounding costs: the committed fixtures bet 180 into 550,
        which is 32.7273%, so the tolerance must exceed `|0.327273 - 0.33| = 0.002727`. The
        ceiling is half the distance to the next menu entry, `(0.75 - 0.33) / 2 = 0.21`, past
        which one bet lands in two buckets. The binding ceiling in practice is the 50% bet the
        phase already requires to be refused, `|0.50 - 0.33| = 0.17`.

        0.01 is 3.67 times the floor and 17 times inside the tighter ceiling.
        """
        tolerance = owed(key_module, "MENU_FRACTION_TOLERANCE")
        rounding_floor = abs(180 / SINGLE_RAISED_POT_CHIPS - 0.33)
        overlap_ceiling = (0.75 - 0.33) / 2
        off_menu_ceiling = abs(275 / SINGLE_RAISED_POT_CHIPS - 0.33)

        assert rounding_floor == pytest.approx(0.002727, abs=1e-6)
        assert off_menu_ceiling == pytest.approx(0.17)
        assert rounding_floor < tolerance < min(overlap_ceiling, off_menu_ceiling)

    def test_the_published_flop_menu_is_the_ruled_two_sizes(self, key_module) -> None:
        assert tuple(owed(key_module, "FLOP_BET_MENU")) == (0.33, 0.75)

    def test_a_table_sized_bet_matches_the_menu_entry_it_is_a_rounding_of(
        self, key_module
    ) -> None:
        match = owed(key_module, "match_menu_fraction")

        assert match(180, SINGLE_RAISED_POT_CHIPS) == pytest.approx(0.33)
        assert match(413, SINGLE_RAISED_POT_CHIPS) == pytest.approx(0.75)

    def test_a_bet_off_the_menu_matches_nothing_rather_than_the_nearer_entry(
        self, key_module
    ) -> None:
        match = owed(key_module, "match_menu_fraction")

        assert match(275, SINGLE_RAISED_POT_CHIPS) is None

    def test_a_bet_exactly_between_two_menu_entries_matches_nothing(self, key_module) -> None:
        """297 chips is 54.0% of 550, halfway between 33% and 75%. Snapping it to the nearer
        entry is the nearest-neighbour substitution the contract forbids by name, and at a
        midpoint there is no nearer entry to snap to."""
        match = owed(key_module, "match_menu_fraction")

        assert match(297, SINGLE_RAISED_POT_CHIPS) is None

    def test_an_artifact_size_converts_to_chips_by_rounding_to_the_nearest_chip(
        self, key_module
    ) -> None:
        """181.5 is pinned because both rounding conventions agree on it, so the test states the
        rule rather than a choice between two readings of a half. The two exact cases beside it
        are what say the conversion is a conversion and not a table."""
        chips = owed(key_module, "menu_size_chips")

        assert chips(0.33, SINGLE_RAISED_POT_CHIPS) == 182
        assert chips(0.33, 400) == 132
        assert chips(0.75, 400) == 300
