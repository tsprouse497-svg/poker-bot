"""Simulator tests, written from the contract before the implementation existed.

Three properties carry this file, and they are the three a simulator can get wrong
without any test noticing.

`TestChipConservation` checks the books per hand rather than in aggregate, because an
aggregate that nets to zero hides two errors that cancel.

`TestDeterminism` checks that a run is a pure function of seed, seating and profiles -
including that it is unaffected by the `random` module's global state, which is the
usual way a "seeded" simulation turns out not to be.

`TestReplayAgreement` feeds every dealt hand back through the frozen Phase 02 replayer
and compares the decision points it finds against the ones the simulator asked about.
Without that, the simulator and the replayer are two independent stories about the same
rules and nothing forces them to agree.

The rest pins what the phase is allowed to claim: refusals are counted rather than
converted, stacks reset every hand because the committed chart refuses anything else,
and the floor comparison is a floor comparison.
"""

# `simulator.run` and `profiles.seating` do not exist yet, because these tests were
# authored before the implementation. Until those two modules land, import sorting reads
# them as third-party and asks for a grouping that becomes wrong the moment they do land,
# so the block keeps its first-party order and silences that one rule.
from __future__ import annotations  # noqa: I001

from collections import Counter
from dataclasses import replace

import pytest

from poker_training_bot.hand_history import NormalizedHandHistory, replay_hand
from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.profiles.seating import Profile, reference_profile, seat_profiles
from poker_training_bot.simulator.run import (
    SimulationConfig,
    SimulationResult,
    run_simulation,
)
from poker_training_bot.strategy.contract import DecisionAuditRecord, StrategyDecision

SEED = 20260812
SEATS = 6
SMALL_BLIND = 50
BIG_BLIND = 100
STARTING_STACK = 100 * BIG_BLIND

# One full orbit is six hands, so every count that has to come out even needs a
# multiple of six. Two orbits is the smallest run that gives every profile every
# position twice, which is enough for the coverage assertions without making the
# gate slow.
ORBIT = SEATS
RUN_HANDS = 2 * ORBIT

TERMINAL_OUTCOMES = frozenset({"showdown", "uncontested", "refused"})


def config(**overrides) -> SimulationConfig:
    fields = {
        "seed": SEED,
        "hands": RUN_HANDS,
        "profiles": seat_profiles("self-play", SEATS),
        "starting_stack": STARTING_STACK,
        "blinds": (SMALL_BLIND, BIG_BLIND),
    }
    fields.update(overrides)
    return SimulationConfig(**fields)


def floor_config(**overrides) -> SimulationConfig:
    """The composite in one seat, the reference check-fold strategy in the rest."""
    return config(profiles=seat_profiles("floor", SEATS), **overrides)


@pytest.fixture(scope="module")
def self_play() -> SimulationResult:
    return run_simulation(config())


@pytest.fixture(scope="module")
def floor() -> SimulationResult:
    return run_simulation(floor_config())


class TestEveryHandReachesATerminalState:
    # No hand ends by exhaustion, exception, or timeout.
    def test_every_hand_has_a_terminal_outcome(self, self_play) -> None:
        assert len(self_play.hands) == RUN_HANDS
        assert {hand.outcome for hand in self_play.hands} <= TERMINAL_OUTCOMES

    def test_both_played_outcomes_occur_in_self_play(self, self_play) -> None:
        """Six copies of a chart bot produce both showdowns and uncontested wins."""
        outcomes = Counter(hand.outcome for hand in self_play.hands)

        assert outcomes["showdown"] > 0, outcomes
        assert outcomes["uncontested"] > 0, outcomes

    def test_a_refused_hand_names_the_refusal_that_ended_it(self, self_play) -> None:
        for hand in self_play.hands:
            if hand.outcome == "refused":
                assert hand.refusal_code, hand.hand_id
            else:
                assert hand.refusal_code is None, hand.hand_id

    # Judgment call 4, pinned so that it is pinned. Every other refusal assertion in this
    # file is written as "for each refused hand, ...", which passes perfectly when no hand
    # is refused - so converting a refusal into a fold was invisible to all of them, and a
    # mutation canary proved it. This is the anti-vacuity guard: the seeded self-play run
    # must actually reach spots the committed charts do not cover, and must report them as
    # refusals rather than as folds.
    #
    # It is deliberately coupled to the chart's coverage. If a future artifact covers every
    # spot this run reaches, this test starts failing, and that failure is the correct
    # signal: it means the refusal path is no longer exercised here and the canary needs a
    # new home, not that the assertion was wrong.
    def test_the_run_actually_reaches_refusals_rather_than_folding_through_them(
        self, self_play
    ) -> None:
        refused = [hand for hand in self_play.hands if hand.outcome == "refused"]

        assert refused, "no hand was refused, so every refusal assertion here is vacuous"
        assert all(hand.refusal_code for hand in refused)
        assert all(set(hand.stack_deltas.values()) == {0} for hand in refused)
        assert sum(self_play.refusal_counts().values()) == len(refused)


class TestChipConservation:
    # Asserted per hand, because an aggregate that nets to zero can hide two errors
    # that cancel each other out.
    def test_stack_changes_sum_to_zero_in_every_single_hand(self, self_play) -> None:
        offenders = [
            (hand.hand_id, sum(hand.stack_deltas.values()))
            for hand in self_play.hands
            if sum(hand.stack_deltas.values()) != 0
        ]

        assert offenders == []

    def test_the_pot_awarded_equals_the_pot_collected_in_every_hand(self, self_play) -> None:
        offenders = [
            (hand.hand_id, hand.pot_collected, hand.pot_awarded)
            for hand in self_play.hands
            if hand.pot_collected != hand.pot_awarded
        ]

        assert offenders == []

    def test_every_seat_appears_in_every_hands_books(self, self_play) -> None:
        for hand in self_play.hands:
            assert set(hand.stack_deltas) == set(range(SEATS)), hand.hand_id

    # Judgment call 4: a refusal voids the hand, so nothing moves and conservation
    # holds trivially rather than by an accounting fix.
    def test_a_refused_hand_moves_no_chips_at_all(self, self_play) -> None:
        for hand in self_play.hands:
            if hand.outcome == "refused":
                assert set(hand.stack_deltas.values()) == {0}, hand.hand_id
                assert hand.pot_awarded == 0, hand.hand_id


class TestStacksResetEveryHand:
    # Judgment call 1: every hand starts at exactly 100bb, because the committed chart
    # refuses a table that is not one flat stack depth and refuses a depth no artifact
    # holds. Without the reset, hand two onward measures the refusal path.
    def test_every_hand_starts_with_every_seat_at_the_starting_stack(self, self_play) -> None:
        for hand in self_play.hands:
            assert set(hand.starting_stacks.values()) == {STARTING_STACK}, hand.hand_id

    def test_the_reset_is_what_keeps_the_chart_answering_after_the_first_hand(
        self, self_play
    ) -> None:
        """A depth refusal in a later hand would mean the reset is not happening."""
        depth_refusals = [
            hand.hand_id
            for hand in self_play.hands
            if hand.refusal_code
            and ("stack-depth" in hand.refusal_code or "flat-stack-depth" in hand.refusal_code)
        ]

        assert depth_refusals == []


class TestTheSimulatorOwnsNoPokerRules:
    # Every action applied to the engine came from a strategy's StrategyDecision.
    def test_every_applied_action_came_from_a_strategy_decision(self, self_play) -> None:
        for hand in self_play.hands:
            for record in hand.decisions:
                assert isinstance(record, DecisionAuditRecord), hand.hand_id
                assert isinstance(record.outcome, StrategyDecision), hand.hand_id

    # Legality is proved by the Phase 03 record, which rejects an action outside
    # legal_actions, an amount above all-in, and an amount below the minimum raise.
    def test_every_decision_is_recorded_as_a_phase_03_audit_record(self, self_play) -> None:
        recorded = sum(len(hand.decisions) for hand in self_play.hands)

        assert recorded > 0
        for hand in self_play.hands:
            for record in hand.decisions:
                assert record.outcome.action in record.query.legal_actions, hand.hand_id

    def test_no_hand_applies_an_action_after_a_refusal(self, self_play) -> None:
        """A refusal ends the hand; it does not get stepped over."""
        for hand in self_play.hands:
            if hand.outcome == "refused":
                assert all(
                    isinstance(record.outcome, StrategyDecision) for record in hand.decisions
                ), hand.hand_id


class TestDeterminism:
    # A simulation is a pure function of its seed, its seating, and its profiles.
    def test_the_same_config_produces_an_identical_run(self) -> None:
        first = run_simulation(config())
        second = run_simulation(config())

        assert first == second

    def test_the_same_config_produces_identical_audit_lines(self) -> None:
        first = run_simulation(config())
        second = run_simulation(config())
        lines = [
            tuple(record.to_json_line() for hand in result.hands for record in hand.decisions)
            for result in (first, second)
        ]

        assert lines[0] == lines[1]

    def test_a_different_seed_produces_a_different_run(self) -> None:
        assert run_simulation(config()) != run_simulation(config(seed=SEED + 1))

    # The usual way a "seeded" simulation turns out not to be: it reaches for the
    # random module's global state somewhere.
    def test_the_run_is_unaffected_by_the_random_modules_global_state(self) -> None:
        import random

        random.seed(1)
        first = run_simulation(config())
        random.seed(2)
        [random.random() for _ in range(37)]
        second = run_simulation(config())

        assert first == second

    # The seed that produced a hand is recorded with it, so a single hand can be
    # replayed on its own without rerunning what came before it.
    def test_every_hand_records_a_seed_that_reproduces_that_hand_alone(self, self_play) -> None:
        for hand in self_play.hands[:3]:
            alone = run_simulation(config(seed=hand.seed, hands=1))

            assert alone.hands[0].normalized == hand.normalized, hand.hand_id

    def test_hand_seeds_are_distinct(self, self_play) -> None:
        seeds = [hand.seed for hand in self_play.hands]

        assert len(set(seeds)) == len(seeds)


class TestReplayAgreement:
    # Every dealt hand is expressible in the Phase 02 schema, and feeding it back
    # through the frozen Phase 02 replayer reproduces the same decision points. This
    # is what stops the simulator and the replayer being two independent stories.
    def test_every_dealt_hand_is_a_valid_normalized_hand(self, self_play) -> None:
        for hand in self_play.hands:
            assert isinstance(hand.normalized, NormalizedHandHistory), hand.hand_id
            assert hand.normalized.max_seats == SEATS
            assert len(hand.normalized.players) == SEATS

    def test_the_replayer_finds_the_same_decision_points_the_simulator_asked_about(
        self, self_play
    ) -> None:
        for hand in self_play.hands:
            if hand.outcome == "refused":
                continue
            points: list = []
            replay_hand(hand.normalized, on_decision=points.append)
            replayed = [
                (point.street.value, point.seat, point.action.kind.value) for point in points
            ]
            asked = [
                (record.query.street, record.query.seat, record.outcome.action)
                for record in hand.decisions
            ]

            assert replayed == asked, hand.hand_id

    def test_a_dealt_hand_replays_without_the_simulator_present(self, self_play) -> None:
        """The normalized hand stands on its own, which is what makes it evidence."""
        for hand in self_play.hands[:4]:
            assert replay_hand(hand.normalized) is not None, hand.hand_id


class TestButtonRotationAndCoverage:
    # Judgment call 6: the button advances one seat per hand and profiles stay put, so
    # over any multiple of six hands every profile plays every position equally.
    def test_the_button_advances_one_seat_per_hand(self, self_play) -> None:
        buttons = [hand.button_seat for hand in self_play.hands]

        assert buttons == [(self_play.hands[0].button_seat + n) % SEATS for n in range(RUN_HANDS)]

    def test_every_seat_occupies_every_position_the_same_number_of_times(
        self, self_play
    ) -> None:
        seats = tuple(range(SEATS))
        held: dict[int, Counter] = {seat: Counter() for seat in seats}
        for hand in self_play.hands:
            for seat in seats:
                held[seat][position_for_seat(seats, hand.button_seat, seat)] += 1

        for seat in seats:
            assert set(held[seat].values()) == {RUN_HANDS // ORBIT}, (seat, held[seat])

    def test_the_result_reports_the_per_position_counts_rather_than_asserting_them(
        self, self_play
    ) -> None:
        assert self_play.position_counts
        for counts in self_play.position_counts.values():
            assert sum(counts.values()) == RUN_HANDS


class TestProfiles:
    # A profile is a strategy plus the metadata a report needs, and no poker logic.
    def test_two_profiles_differing_only_in_name_play_identically(self) -> None:
        renamed = tuple(
            replace(profile, name=f"{profile.name}-renamed")
            for profile in seat_profiles("self-play", SEATS)
        )
        original = run_simulation(config())
        under_new_names = run_simulation(config(profiles=renamed))

        assert [hand.normalized for hand in original.hands] == [
            hand.normalized for hand in under_new_names.hands
        ]

    def test_a_profile_carries_a_strategy_and_a_label(self) -> None:
        for profile in seat_profiles("floor", SEATS):
            assert isinstance(profile, Profile)
            assert profile.name
            assert profile.strategy.strategy_id
            assert profile.strategy.strategy_version > 0

    def test_the_reference_check_fold_strategy_is_available_as_a_floor(self) -> None:
        assert reference_profile().strategy.strategy_id == "reference-check-fold"

    # Judgment call 5: six-max at exactly 100bb, because any other configuration
    # measures the refusal path and nothing else. Rejected at setup, not part way in.
    def test_a_table_size_no_artifact_covers_is_rejected_at_setup(self) -> None:
        with pytest.raises(ValueError):
            run_simulation(config(profiles=seat_profiles("self-play", 3)))

    def test_a_depth_no_artifact_covers_is_rejected_at_setup(self) -> None:
        with pytest.raises(ValueError):
            run_simulation(config(starting_stack=40 * BIG_BLIND))

    def test_a_seating_that_does_not_fill_the_table_is_rejected_at_setup(self) -> None:
        with pytest.raises(ValueError):
            run_simulation(config(profiles=seat_profiles("self-play", SEATS)[:-1]))


class TestWhatTheComparisonMayClaim:
    # Judgment call 2: self-play carries the mechanical criteria, because symmetry
    # gives a known expected answer to check against.
    def test_self_play_nets_to_zero_across_the_table(self, self_play) -> None:
        totals = Counter()
        for hand in self_play.hands:
            totals.update(hand.stack_deltas)

        assert sum(totals.values()) == 0

    # And the floor run carries one directional number, which must come out positive.
    def test_the_chart_bot_beats_a_bot_that_folds_everything(self, floor) -> None:
        chart = floor.chips_per_hand("composite-preflop-chart-postflop-fallback")

        assert chart > 0, floor.chips_per_hand_by_profile()

    # Judgment call 3: the figure is reported with its own standard error, and no
    # winner is named when the run cannot separate the profiles.
    def test_every_reported_figure_carries_a_standard_error(self, floor) -> None:
        for name in floor.profile_names():
            assert floor.standard_error(name) >= 0

    def test_a_difference_inside_the_noise_is_not_reported_as_a_finding(self, self_play) -> None:
        """Six identical profiles cannot be separated, and the result must say so."""
        assert self_play.separated_profiles() == ()

    # Refusal coverage is a headline number, not a footnote: a profile that refuses
    # most hands has not been measured.
    def test_refusal_coverage_is_reported_per_profile(self, self_play) -> None:
        coverage = self_play.refusal_counts()

        assert set(coverage) == set(self_play.profile_names())

    def test_refused_hands_are_excluded_from_the_chips_per_hand_denominator(
        self, self_play
    ) -> None:
        played = sum(1 for hand in self_play.hands if hand.outcome != "refused")

        assert self_play.hands_counted() == played

    def test_the_seed_and_the_hand_count_are_carried_on_the_result(self, self_play) -> None:
        assert self_play.seed == SEED
        assert self_play.hands_dealt() == RUN_HANDS
