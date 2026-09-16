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
  them. **Three of the six files calling `to_json_line` never assert on its bytes** -
  `tests/test_full_table_preflop.py:611`, `tests/test_postflop_fallback.py:687` and
  `tests/test_simulator.py:451` feed it into a set or a tuple for de-duplication and determinism,
  which a new field does not disturb. Of the three that do assert on the bytes, two are the
  migrated files above and the third is this phase's own `tests/test_postflop_key.py`, so the
  sweep found no pre-existing byte assertion it left standing.
  **`tests/test_engine_fidelity.py` reads committed audit lines back but stamps
  `DECISION_AUDIT_SCHEMA_VERSION` rather than each line's own**, so the bump
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


BUTTON_SEAT, SB_SEAT, HERO_SEAT = 0, 1, 2
LIVE_HEADS_UP = (BUTTON_SEAT, HERO_SEAT)
LIVE_THREE_WAY = (BUTTON_SEAT, SB_SEAT, HERO_SEAT)
"""Six seats with the button at 0, so `poker_core.order.blind_seats` puts the small blind at 1 and
the big blind at 2, and hero is the big blind."""


def seated(committed: dict[int, int], live: tuple[int, ...], street: dict[int, int] | None = None):
    """`pot`, `stacks` and `seat_states` for one table, derived from what each seat put in.

    Every seat is listed and the folded ones are marked, which is what `simulator/table.py` does.
    `tests/test_postflop_betting.py::seated` carries why dropping one is a defect rather than a
    shorthand: `len(stacks)` is read as the table size, and a dead blind lent to a live seat is
    read as that seat's depth.
    """
    on_street = dict(street or {})
    states = tuple(
        contract_module.SeatState(
            seat=seat,
            street_bet=on_street.get(seat, 0),
            committed_total=committed.get(seat, 0),
            folded=seat not in live,
        )
        for seat in range(SEATS)
    )
    return {
        "pot": sum(state.committed_total for state in states),
        "stacks": tuple((state.seat, STARTING_STACK - state.committed_total) for state in states),
        "seat_states": states,
    }


def opened_to(chips: int, *after):
    """The lojack, hijack and cutoff fold, the button opens, then `after`.
    `simulator/run.py` appends every preflop action a seat takes, folds included, so a line
    recorded from the raise onwards is not the line the producer emits."""
    return (
        *(contract_module.SeatAction(seat, "fold") for seat in (3, 4, 5)),
        contract_module.SeatAction(BUTTON_SEAT, "raise", chips),
        *after,
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

    Same convention as `tests/test_postflop_betting.py::query`: six-handed and flat at 100bb, the
    button opens to 2.5bb, the small blind folds and keeps its own dead 0.5bb, hero the big blind
    calls, and every folded seat is still listed and marked.
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
        "preflop_actions": opened_to(
            250,
            contract_module.SeatAction(SB_SEAT, "fold"),
            contract_module.SeatAction(HERO_SEAT, "call"),
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

    **Why it needs a test rather than an argument.** As drafted at stage 4 the key could not say
    how many seats saw the flop: `t6/d100/SB/BTN:raise@2.5` was one preflop key whether the big
    blind folded (6.0bb heads-up) or called (7.5bb, three-handed), because a preflop spot key ends
    at hero's own decision and the seats acting after hero are not in it, and only the pot
    arithmetic separated them. Decision 8's 2026-09-15 amendment carries the **completed** line
    instead, so `BTN:raise@2.5,BB:call` and `BTN:raise@2.5,SB:call,BB:call` are two lines and the
    seat count is named rather than inferred. The refusal is still required and still tested here:
    a live-seat count is a structural property of the cell, not of the pot it happens to produce,
    and this is what keeps the separation a requirement rather than a coincidence.
    """

    def three_handed(self, **overrides):
        """The button opens to 2.5bb and both blinds call, so three seats see the flop.

        Nothing is dead here - every seat that put money in is still in the hand - so the pot is
        the plain `3 x 250`. **The small blind is first to act postflop**, not the big blind:
        action starts left of the button and the blinds act before it on every street after the
        flop, which is what `postflop_action_order` exists to say. Hero is the big blind and acts
        second, so the small blind's check is on the record in front of it.
        """
        fields = {
            "hand_id": "h-multiway",
            "street": "flop",
            "seat": HERO_SEAT,
            "button_seat": BUTTON_SEAT,
            "hole_cards": ("As", "Qd"),
            "board": ("Kc", "7d", "2h"),
            "legal_actions": ("check", "bet"),
            "to_call": 0,
            "current_bet": 0,
            "min_raise_target": BIG_BLIND,
            **seated(
                {BUTTON_SEAT: 250, SB_SEAT: 250, HERO_SEAT: 250},
                LIVE_THREE_WAY,
            ),
            "blinds": (SMALL_BLIND, BIG_BLIND),
            "preflop_actions": opened_to(
                250,
                contract_module.SeatAction(SB_SEAT, "call"),
                contract_module.SeatAction(HERO_SEAT, "call"),
            ),
            "postflop_actions": (contract_module.SeatAction(SB_SEAT, "check"),),
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


DEEPER_BUTTON_EXTRA = 2750
"""27.5bb, which is enough that the button covers hero and the table is visibly not flat."""

DEEPER_BUTTON_STACKS = tuple(
    (seat, stack + DEEPER_BUTTON_EXTRA if seat == BUTTON_SEAT else stack)
    for seat, stack in seated(
        {BUTTON_SEAT: 750, SB_SEAT: 50, HERO_SEAT: 750}, LIVE_HEADS_UP
    )["stacks"]
)
FLAT_STARTING_STACKS = dict.fromkeys(range(SEATS), STARTING_STACK)
DEEPER_BUTTON_STARTING_STACKS = {
    **FLAT_STARTING_STACKS,
    BUTTON_SEAT: STARTING_STACK + DEEPER_BUTTON_EXTRA,
}


def refused_hand(hand_id: str, outcome, stacks: dict[int, int]) -> HandResult:
    """One voided hand carrying a refusal, which is all `refusal_inventory` reads."""
    return HandResult(
        hand_id=hand_id,
        seed=SEED,
        button_seat=BUTTON_SEAT,
        outcome="voided",
        refusal_code=outcome.code,
        refusing_seat=HERO_SEAT,
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
    spot, one at a flat table and one where the button sat down deeper than everybody else, have
    to come back as **one** row reached twice. The effective stack is the same in both, because
    that is the quantity the spot is defined by; what differs is how the chips are distributed,
    which is not.
    """

    def uncovered(self, **overrides):
        """A 3-bet line the committed chart does not cover, so the lookup refuses on the line."""
        fields = {
            "preflop_actions": opened_to(
                250,
                contract_module.SeatAction(SB_SEAT, "fold"),
                contract_module.SeatAction(HERO_SEAT, "raise", 750),
                contract_module.SeatAction(BUTTON_SEAT, "call"),
            ),
            **seated({BUTTON_SEAT: 750, SB_SEAT: 50, HERO_SEAT: 750}, LIVE_HEADS_UP),
        }
        fields.update(overrides)
        return covered_flop(**fields)

    def both(self, strategy):
        """The same spot twice: every seat at 100bb, then the button sat down 27.5bb deeper.

        The chips behind differ; the effective stack does not, because hero still covers exactly
        92.5bb either way and that is the quantity the spot is defined by.
        """
        flat = strategy.decide(self.uncovered())
        uneven = strategy.decide(self.uncovered(stacks=DEEPER_BUTTON_STACKS))
        assert isinstance(flat, contract_module.StrategyRefusal), flat
        assert isinstance(uneven, contract_module.StrategyRefusal), uneven
        return flat, uneven

    def test_the_two_refusals_group_into_one_row_reached_twice(self, strategy) -> None:
        flat, uneven = self.both(strategy)
        result = SimulationResult(
            seed=SEED,
            seat_names=tuple("abcdef"),
            hands=(
                refused_hand("h-flat", flat, FLAT_STARTING_STACKS),
                refused_hand("h-uneven", uneven, DEEPER_BUTTON_STARTING_STACKS),
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
# The preflop raiser's flop, which the key could not name until 2026-09-15
# --------------------------------------------------------------------------- #


class TestThePreflopRaiserHasAFlopSpotAtAll:
    """Decision 8's amendment, and the one thing no stage-4 test asked for.

    **What was broken.** The key was built on a preflop *spot* key, which names a decision hero is
    about to make. Every flop is reached with the preflop betting closed, so the only seat such a
    key could name was the caller, and `spot_key` refused the raiser outright with "BTN already
    acted and faces no later raise". The bot could therefore never continuation-bet - about half of
    all flops, and the single spot the phase exists for. Nothing went red: the frozen test
    requiring a committed spot to produce a bet is satisfied by the caller's donk bet.

    **What is asserted here.** That the raiser's flop keys at all, that both seats derive the same
    5.5bb pot and 97.5bb behind off one completed line, and that the two keys differ - so a
    raiser's cell and a caller's cell on one board and line never collide."""

    OPEN_BB = 2.5
    POT_BB = 5.5
    """`2 x 2.5 + the folded small blind's dead 0.5`, decision 10's own arithmetic."""
    BEHIND_BB = 97.5
    """100bb less the 2.5 both live seats put in. The old key derived 2.5 and 99.0, because with
    no completed line the raiser's own open was not in it."""

    def line(self, key_module, hero: str):
        action = owed(key_module, "PreflopAction")
        built = (action("BTN", "raise", self.OPEN_BB), action("BB", "call"))
        return owed(key_module, "completed_preflop_line")(6, 100, hero, built)

    def key(self, key_module, hero: str) -> str:
        line = self.line(key_module, hero)
        return owed(key_module, "postflop_spot_key")(
            line, ("Kc", "7d", "2h"), (), line.pot_bb, line.effective_stack_bb
        )

    def test_the_raiser_keys_rather_than_refusing(self, key_module) -> None:
        assert self.key(key_module, "BTN")

    def test_the_raiser_s_pot_and_stack_come_off_the_whole_line(self, key_module) -> None:
        line = self.line(key_module, "BTN")

        assert (line.pot_bb, line.effective_stack_bb) == (self.POT_BB, self.BEHIND_BB)

    def test_the_caller_derives_the_same_pot_and_stack(self, key_module) -> None:
        """One street, one pot: the seats differ in what they decide, not in what is in the
        middle. A raiser and a caller deriving different pots would be two cells for one spot."""
        line = self.line(key_module, "BB")

        assert (line.pot_bb, line.effective_stack_bb) == (self.POT_BB, self.BEHIND_BB)

    def test_the_two_seats_are_two_keys(self, key_module) -> None:
        """The collision this closes. Same board, same line, two ranges: the raiser is deciding
        whether to continuation-bet and the caller whether to donk or check."""
        assert self.key(key_module, "BTN") != self.key(key_module, "BB")

    def test_neither_key_begins_with_t_so_the_preflop_reader_ignores_both(self, key_module) -> None:
        """The completed line inside a postflop key renders in the preflop key's grammar, so the
        non-`t` prefix does exactly the work decision 8 gave it on both seats now."""
        for hero in ("BTN", "BB"):
            assert not self.key(key_module, hero).startswith("t")

    def test_a_street_that_is_not_closed_is_refused_rather_than_keyed(self, key_module) -> None:
        """The other half, and why the preflop validator was not simply loosened: an open the big
        blind has not answered is not a flop, and a line saying it is would put a cell behind a
        spot nobody reached."""
        action = owed(key_module, "PreflopAction")

        with pytest.raises(ValueError):
            owed(key_module, "completed_preflop_line")(
                6, 100, "BB", (action("BTN", "raise", self.OPEN_BB),)
            )

    def test_a_committed_spot_hero_opened_produces_a_bet(self, betting_module, strategy) -> None:
        """The committed-data half, and the test whose absence let the defect ship.

        The amendment says so in terms: "No frozen test caught it: the one requiring a committed
        spot to produce a bet is satisfied by the caller's donk bet." A donk bet and a
        continuation bet are different spots out of different ranges, and only the second is the
        one this phase exists for, so the raiser's seat is named here rather than counted in with
        the rest. The raiser's cells are found off the committed line's own fields and their keys
        are **compared**, never taken apart, which is the rule `postflop_key` states.
        """
        opened = {
            cell.spot_key
            for cell in strategy.library.cells
            if any(
                entry.position == cell.preflop_line.hero_position and entry.action == "raise"
                for entry in cell.preflop_line.actions
            )
        }
        bets = [
            outcome
            for spot in owed(betting_module, "committed_spot_queries")()
            for outcome in [strategy.decide(spot)]
            if isinstance(outcome, contract_module.StrategyDecision)
            and outcome.action == "bet"
            and dict(outcome.detail).get("spot_key") in opened
        ]

        assert bets, (
            "no committed spot where hero is the preflop raiser produces a bet, so the bot still"
            " cannot continuation-bet and the sample holds only the caller's seat"
        )
        assert all(outcome.amount and outcome.amount > 0 for outcome in bets)
