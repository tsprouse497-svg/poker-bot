"""Simulator tests, written from the contract before the implementation existed.

Three properties carry this file and are the three a simulator can get wrong unnoticed:
`TestChipConservation` checks the books per hand, since an aggregate netting to zero hides two
errors that cancel; `TestDeterminism`, that a run is a pure function of seed, seating and profiles;
`TestReplayAgreement`, that the frozen replayer agrees. **The cutover moves which seating carries
them.** The 86 hold one opening range, the small blind's, so the lojack opens every hand into the
retired `t6/d100/LJ/rfi` and phase 07's judgment call 2 has no table left to run on. The three move
to `contested` - one caller, one raiser, four check-folds - while `self_play` keeps the refusal,
asserted rather than deleted. Over the chart seating the books balance and the replayer agrees, of
nothing, so each moved claim carries its own counter; a counter in a sibling test is no guard.
"""

# `simulator.run` and `profiles.seating` do not exist yet. Until they land, import sorting
# reads them as third-party and asks for a grouping that becomes wrong the moment they do,
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
from poker_training_bot.strategy.contract import (
    DecisionAuditRecord,
    StrategyDecision,
    StrategyQuery,
)

SEED = 20260812
SEATS = 6
SMALL_BLIND = 50
BIG_BLIND = 100
STARTING_STACK = 100 * BIG_BLIND

# One full orbit is six hands, so every count that has to come out even needs a multiple of
# six. No run length is sized to reach a refusal any more: `t6/d100/LJ/rfi` is not one of the
# 86 the ruled predicate keeps, so the chart seating's refusal probability per hand is 1.
ORBIT = SEATS
RUN_HANDS = 6 * ORBIT

TERMINAL_OUTCOMES = frozenset({"showdown", "uncontested", "refused"})

# The opening range every chart-seated hand now dies on, one of the fourteen retired spots,
# named so a chart answering it again fails loudly. Its sibling `t6/d100/SB/rfi` survives.
RETIRED_OPEN_KEY = "t6/d100/LJ/rfi"
CHART_PROFILE = "composite-preflop-chart-postflop-fallback"  # the composite's own strategy_id

# Measured over `contested_config()` at `SEED`: 372 decisions, every hand collecting a pot.
CONTESTED_DECISIONS = 372
SMALLEST_POT = SMALL_BLIND + BIG_BLIND


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


class AlwaysCalls:
    """One seat that limps, so the chart is asked something it structurally cannot answer,
    reached deterministically rather than by a lucky seed: the ruled solve is `limp: false`
    and no re-solve is permitted, so a limped spot has no node. Code: `spot-not-covered`."""

    strategy_id = "test-always-calls"
    strategy_version = 1

    def decide(self, query: StrategyQuery) -> StrategyDecision:
        if query.to_call:
            return StrategyDecision("call", None, "test:limps")
        return StrategyDecision("check", None, "test:checks")


def limped_config(**overrides) -> SimulationConfig:
    """Five composite seats and one limper. Only the seating differs from `config`, so this
    run measures the chart meeting a spot it has no cell for, not a table it refuses."""
    seated = (Profile("limper", AlwaysCalls()), *seat_profiles("self-play", SEATS)[1:])
    return config(profiles=seated, **overrides)


@pytest.fixture(scope="module")
def limped() -> SimulationResult:
    return run_simulation(limped_config())


class RaisesPairsAndAces:
    """One seat that raises, so the books being checked are the books of a raised pot. It
    min-raises preflop and jams the flop, every amount read off the query, which between them
    reach the min-raise path, the all-in path and a settlement layered over more than one
    commitment level. Its hole-card gate keeps both played outcomes reachable here."""

    strategy_id = "test-raises-pairs-and-aces"
    strategy_version = 1

    def decide(self, query: StrategyQuery) -> StrategyDecision:
        first, second = query.hole_cards
        if first[0] == second[0] or "A" in (first[0], second[0]):
            if "raise" in query.legal_actions:
                return StrategyDecision("raise", query.min_raise_target, "test:min-raise")
            if "bet" in query.legal_actions:
                behind = dict(query.stacks)[query.seat]
                held = next(state for state in query.seat_states if state.seat == query.seat)
                return StrategyDecision("bet", held.street_bet + behind, "test:jam")
            if query.to_call:
                return StrategyDecision("call", None, "test:calls")
        if "check" in query.legal_actions:
            return StrategyDecision("check", None, "test:checks")
        return StrategyDecision("fold", None, "test:folds")


def contested_config(**overrides) -> SimulationConfig:
    """One caller, one raiser and four check-folds: a raised pot played to showdown, reading no
    chart. Conservation, the stack reset, replay agreement and determinism are claims about the
    simulator and the chart seating carries none, refusing at the lojack's open so every offender
    list comes out empty. Measured: 36 hands, 11 min-raises, 11 flop jams, 30 layered settlements,
    a 20,150 pot; over a caller and five check-folds, no raise and a 250-chip largest pot."""
    seated = (
        Profile("caller", AlwaysCalls()),
        Profile("raiser", RaisesPairsAndAces()),
        *(reference_profile() for _ in range(SEATS - 2)),
    )
    # Set rather than passed, so an override may replace the seating: the renaming test
    # below hands one in, and `config(profiles=seated, **overrides)` would pass it twice.
    overrides.setdefault("profiles", seated)
    return config(**overrides)


@pytest.fixture(scope="module")
def contested() -> SimulationResult:
    return run_simulation(contested_config())


def actions_taken(result: SimulationResult) -> Counter:
    """The action histogram of a run, so a claim made over it is not a claim about nothing.
    Measured over `contested_config()` at `SEED` by a walk written for this file: 372
    decisions - 149 checks, 149 folds, 52 calls, 11 min-raises, 11 flop jams - over 31
    showdowns and 5 uncontested hands. Over `config()` after the cutover: none of it."""
    return Counter(record.outcome.action for hand in result.hands for record in hand.decisions)


class TestEveryHandReachesATerminalState:
    # No hand ends by exhaustion, exception, or timeout.
    def test_every_hand_has_a_terminal_outcome(self, self_play) -> None:
        assert len(self_play.hands) == RUN_HANDS
        assert {hand.outcome for hand in self_play.hands} <= TERMINAL_OUTCOMES

    def test_six_chart_seats_refuse_the_lojacks_open_before_a_chip_moves(self, self_play) -> None:
        """The ruled cost of the cutover, confirmed 2026-08-25. This read "six copies of a
        chart bot produce both showdowns and uncontested wins"; inverted rather than deleted,
        since a chart on the 110 answers the lojack's open and a run that plays says so."""
        outcomes = Counter(hand.outcome for hand in self_play.hands)

        assert outcomes == Counter({"refused": RUN_HANDS}), outcomes
        for hand in self_play.hands:
            assert hand.refusal_code.endswith("spot-not-covered"), hand.refusal_code
            assert dict(hand.refusal_detail).get("spot_key") == RETIRED_OPEN_KEY, hand.hand_id
            assert not hand.decisions, hand.hand_id

    def test_both_played_outcomes_occur_where_hands_are_played(self, contested) -> None:
        """Both non-refusal outcomes happen, so `TERMINAL_OUTCOMES` is not one value. Same
        claim, moved to a seating that plays, where the raiser's gate keeps both reachable."""
        outcomes = Counter(hand.outcome for hand in contested.hands)

        assert outcomes["showdown"] > 0, outcomes
        assert outcomes["uncontested"] > 0, outcomes
        assert outcomes["refused"] == 0, outcomes

    def test_a_refused_hand_names_the_refusal_that_ended_it(self, limped, contested) -> None:
        """Both halves need a run they can fail in and no single run supplies both: every
        hand in `limped` refuses, so the else branch is unreachable there, and `contested`
        refuses none. Nothing proved either branch was entered, and a pair of empty runs
        satisfies both; the counters pin the split at all 36 of each."""
        named = 0
        silent = 0
        for run in (limped, contested):
            for hand in run.hands:
                if hand.outcome == "refused":
                    named += 1
                    assert hand.refusal_code, hand.hand_id
                else:
                    silent += 1
                    assert hand.refusal_code is None, hand.hand_id

        assert (named, silent) == (RUN_HANDS, RUN_HANDS), (named, silent)

    # Judgment call 4. Every other refusal assertion here reads "for each refused hand, ...",
    # so converting a refusal into a fold was invisible to all of them and a canary proved it.
    def test_the_run_reaches_refusals_rather_than_folding_through_them(self, limped) -> None:
        refused = [hand for hand in limped.hands if hand.outcome == "refused"]

        assert refused, "no hand was refused, so every refusal assertion here is vacuous"
        assert all(hand.refusal_code for hand in refused)
        assert all(set(hand.stack_deltas.values()) == {0} for hand in refused)
        assert sum(limped.refusal_counts().values()) == len(refused)

    def test_the_refusal_is_the_missing_cell_not_a_declined_table(self, limped) -> None:
        """Which code the deterministic driver exercises, stated rather than assumed.
        `spot-not-covered` names a cell somebody could fill; table-shape codes are rejected at
        setup. The lojack's open misses too now, so the limped key is asserted present."""
        refused = [hand for hand in limped.hands if hand.outcome == "refused"]
        first_actions = [
            dict(hand.refusal_detail).get("spot_key", "").split("/")[-1].split(",")[0]
            for hand in refused
        ]
        limps = [action for action in first_actions if action.endswith(":call")]

        assert refused
        assert limps, "the limper produced no limped spot, so the driver is not the limp"
        for hand in refused:
            assert hand.refusal_code.endswith("spot-not-covered"), hand.refusal_code


class TestChipConservation:
    # Per hand, since an aggregate netting to zero hides two errors that cancel.
    def test_the_books_are_checked_over_a_raised_all_in_pot(self, contested) -> None:
        """Both directions a run can go vacuous, excluded here: a table where nothing was
        collected keeps perfect books, which is what six chart seats produce, and so does one
        never putting in a chip beyond the price it was asked."""
        moved = [
            hand.hand_id
            for hand in contested.hands
            if any(delta != 0 for delta in hand.stack_deltas.values())
        ]
        taken = Counter(
            record.outcome.action for hand in contested.hands for record in hand.decisions
        )

        assert len(moved) == len(contested.hands), moved
        assert taken["raise"] and taken["bet"], taken
        assert max(hand.pot_collected for hand in contested.hands) >= 2 * STARTING_STACK

    def test_stack_changes_sum_to_zero_in_every_single_hand(self, contested) -> None:
        """An empty offender list is what a simulator that settles nothing also reports, and
        the guard for that lived one test up rather than here. `moved` is this one's own."""
        moved = 0
        offenders: list[tuple[str, int]] = []
        for hand in contested.hands:
            moved += any(delta != 0 for delta in hand.stack_deltas.values())
            if sum(hand.stack_deltas.values()) != 0:
                offenders.append((hand.hand_id, sum(hand.stack_deltas.values())))

        assert moved == RUN_HANDS, moved
        assert offenders == []

    def test_the_pot_awarded_equals_the_pot_collected_in_every_hand(self, contested) -> None:
        """Same shape and the same repair: `0 == 0` holds in every hand of a run that
        collected no pot, so the pots are counted before they are compared."""
        collected = [hand.pot_collected for hand in contested.hands]
        offenders = [
            (hand.hand_id, hand.pot_collected, hand.pot_awarded)
            for hand in contested.hands
            if hand.pot_collected != hand.pot_awarded
        ]

        assert len(collected) == RUN_HANDS, len(collected)
        assert min(collected) == SMALLEST_POT, sorted(collected)[:3]
        assert offenders == []

    def test_every_seat_appears_in_every_hands_books(self, self_play, contested) -> None:
        """Both runs, because a voided hand still owes a complete set of books: it reports a
        zero for every seat rather than nothing. `booked` counts the hands walked, an
        unqualified for-each over two empty runs making the same claim about nothing."""
        booked = 0
        for run in (self_play, contested):
            for hand in run.hands:
                booked += 1
                assert set(hand.stack_deltas) == set(range(SEATS)), hand.hand_id

        assert booked == 2 * RUN_HANDS, booked

    # Judgment call 4: a refusal voids the hand, so conservation holds trivially.
    def test_a_refused_hand_moves_no_chips_at_all(self, limped) -> None:
        for hand in limped.hands:
            if hand.outcome == "refused":
                assert set(hand.stack_deltas.values()) == {0}, hand.hand_id
                assert hand.pot_awarded == 0, hand.hand_id

    def test_the_settlement_layers_over_an_all_in_and_shuts_nobody_out(self, contested) -> None:
        """A seat's commitment is its payout less its stack delta, so the levels
        `settle_showdown` splits on are readable off the record. Judgment call 1 resets every seat
        to one depth, so none commits past `STARTING_STACK` and every contender is eligible for
        every layer. It read `<= 1`, then `== 1` over a non-empty set, and neither could fail:
        both hold of the one-element set a single-contender showdown produces, which `judged`
        counted. Two or more is the gate, so `judged == 31` claims all 31."""
        layered = 0
        jammed = 0
        judged = 0
        for hand in contested.settled_hands():
            paid = hand.normalized.result.payouts
            put_in = {seat: paid[seat] - delta for seat, delta in hand.stack_deltas.items()}
            contenders = {entry.seat for entry in hand.normalized.showdown}
            levels = {amount for amount in put_in.values() if amount > 0}

            assert max(levels) <= STARTING_STACK, hand.hand_id
            if len(contenders) > 1:
                judged += 1
                assert len({put_in[seat] for seat in contenders}) == 1, (hand.hand_id, put_in)
            layered += len(levels) > 1
            jammed += STARTING_STACK in levels

        assert judged == sum(1 for hand in contested.hands if hand.outcome == "showdown") == 31
        assert layered, "no settlement split into more than one pot"
        assert jammed, "no seat ever got all in, so the all-in path is untested"


class TestStacksResetEveryHand:
    # Judgment call 1: every hand starts at exactly 100bb, because the committed chart refuses
    # any other flat depth. Without the reset, hand two onward measures the refusal path; a
    # reset is only load-bearing where chips move, which is why it hangs on `contested`.
    def test_every_hand_starts_with_every_seat_at_the_starting_stack(self, contested) -> None:
        for hand in contested.hands:
            assert set(hand.starting_stacks.values()) == {STARTING_STACK}, hand.hand_id

    def test_no_hand_refuses_for_a_depth_no_artifact_holds(self, self_play, contested) -> None:
        """A depth refusal in a later hand would mean the reset is not happening. Over both
        runs, since a depth refusal hiding behind the chart seating's coverage one matters."""
        depth_refusals = [
            hand.hand_id
            for run in (self_play, contested)
            for hand in run.hands
            if hand.refusal_code
            and ("stack-depth" in hand.refusal_code or "flat-stack-depth" in hand.refusal_code)
        ]

        assert depth_refusals == []
        assert sum(contested.refusal_counts().values()) == 0


class TestTheSimulatorOwnsNoPokerRules:
    # Every action applied to the engine came from a strategy's StrategyDecision. The guard
    # was `recorded > 0` in the next test down, which guards that test and not this one: this
    # one is an unqualified for-each and a run applying no action satisfies it. It counts now.
    def test_every_applied_action_came_from_a_strategy_decision(self, contested) -> None:
        applied = 0
        for hand in contested.hands:
            for record in hand.decisions:
                applied += 1
                assert isinstance(record, DecisionAuditRecord), hand.hand_id
                assert isinstance(record.outcome, StrategyDecision), hand.hand_id

        assert applied == CONTESTED_DECISIONS, applied

    # Legality is proved by the Phase 03 record, which rejects an action outside
    # legal_actions, an amount above all-in, or one below the minimum raise.
    def test_every_decision_is_recorded_as_a_phase_03_audit_record(self, contested) -> None:
        recorded = sum(len(hand.decisions) for hand in contested.hands)

        assert recorded > 0
        for hand in contested.hands:
            for record in hand.decisions:
                assert record.outcome.action in record.query.legal_actions, hand.hand_id

    def test_no_hand_applies_an_action_after_a_refusal(self, limped) -> None:
        """A refusal ends the hand rather than being stepped over, hence `limped`: a refused
        chart-seated hand carries no decision at all, dying on its first."""
        refused = [hand for hand in limped.hands if hand.outcome == "refused"]

        assert any(hand.decisions for hand in refused), "no refusal followed a real action"
        for hand in refused:
            assert all(
                isinstance(record.outcome, StrategyDecision) for record in hand.decisions
            ), hand.hand_id


class TestDeterminism:
    # A simulation is a pure function of its seed, its seating and its profiles - and not on
    # the chart seating after the cutover, where every hand refuses before an action is
    # applied, so every claim below would pass for a simulator that decides nothing.
    def test_the_same_config_produces_an_identical_run(self) -> None:
        first = run_simulation(contested_config())
        second = run_simulation(contested_config())
        taken = actions_taken(first)

        assert taken["raise"] and taken["bet"] and taken["call"], taken
        assert max(hand.pot_collected for hand in first.hands) > STARTING_STACK
        assert first == second

    def test_the_same_config_produces_identical_audit_lines(self) -> None:
        """The chart seating records no decision, so both sides of this comparison flattened
        to an empty tuple and it held for any simulator. Non-emptiness is asserted first."""
        first = run_simulation(contested_config())
        second = run_simulation(contested_config())
        lines = [
            tuple(record.to_json_line() for hand in result.hands for record in hand.decisions)
            for result in (first, second)
        ]

        assert lines[0], "no audit line was produced, so the comparison is vacuous"
        assert lines[0] == lines[1]

    def test_a_different_seed_produces_a_different_run(self) -> None:
        """The cards dealt have to differ, not just the integer each hand records: over the
        chart seating the runs differed in their seed fields alone, as one fixed deck would."""
        first = run_simulation(contested_config())
        other = run_simulation(contested_config(seed=SEED + 1))
        dealt = [tuple(hand.normalized for hand in run.hands) for run in (first, other)]

        assert all(entry is not None for side in dealt for entry in side)
        assert dealt[0] != dealt[1]
        assert first != other

    # The usual way a "seeded" simulation turns out not to be: it reaches for the random
    # module's global state somewhere. Over the chart seating the only card reaching the
    # record is a refusal's `hand_class`; here it is 36 dealt hands, boards and actions.
    def test_the_run_is_unaffected_by_the_random_modules_global_state(self) -> None:
        import random

        random.seed(1)
        first = run_simulation(contested_config())
        random.seed(2)
        [random.random() for _ in range(37)]
        second = run_simulation(contested_config())

        assert sum(actions_taken(first).values()) == CONTESTED_DECISIONS, actions_taken(first)
        assert first == second

    # The seed that produced a hand is recorded with it, so a single hand replays alone. A
    # refused hand's `normalized` is None, so the first assertion is that there is one.
    def test_every_hand_records_a_seed_that_reproduces_that_hand_alone(self, contested) -> None:
        for hand in contested.hands[:3]:
            alone = run_simulation(contested_config(seed=hand.seed, hands=1))

            assert hand.normalized is not None, hand.hand_id
            assert alone.hands[0].normalized == hand.normalized, hand.hand_id

    def test_hand_seeds_are_distinct(self, self_play) -> None:
        seeds = [hand.seed for hand in self_play.hands]

        assert len(seeds) == RUN_HANDS, len(seeds)
        assert len(set(seeds)) == len(seeds)


class TestReplayAgreement:
    # Every settled hand is expressible in the Phase 02 schema, and feeding it back through
    # the frozen replayer reproduces the same decision points. Each test below has a guard.
    def test_every_settled_hand_is_a_valid_normalized_hand(self, contested) -> None:
        settled = contested.settled_hands()

        assert settled, "no hand settled, so this whole class is vacuous"
        for hand in settled:
            assert isinstance(hand.normalized, NormalizedHandHistory), hand.hand_id
            assert hand.normalized.max_seats == SEATS
            assert len(hand.normalized.players) == SEATS

    # A refused hand stops mid-round, so it is not a completed history and the replayer rejects
    # it. Stays on the chart seating, where all 36 refuse after the cutover.
    def test_a_refused_hand_carries_no_completed_hand_history(self, self_play) -> None:
        refused = [hand for hand in self_play.hands if hand.outcome == "refused"]

        assert refused, "no hand was refused, so this assertion is vacuous"
        assert all(hand.normalized is None for hand in refused)
        settled_ids = {hand.hand_id for hand in self_play.settled_hands()}
        assert settled_ids.isdisjoint({hand.hand_id for hand in refused})

    def test_the_replayer_finds_the_same_points_the_simulator_asked_about(self, contested) -> None:
        """The guard counts what kind of decision point was compared rather than how many:
        the disagreement worth catching is over a raised round, not an unreopened one."""
        compared: Counter = Counter()
        for hand in contested.settled_hands():
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
            compared.update(action for _, _, action in asked)

        assert compared["raise"] and compared["bet"] and compared["call"], compared

    # The normalized hand stands on its own, which is what makes it evidence.
    def test_a_settled_hand_replays_without_the_simulator_present(self, contested) -> None:
        replayed = [replay_hand(hand.normalized) for hand in contested.settled_hands()[:4]]

        assert len(replayed) == 4
        assert all(result is not None for result in replayed)


class TestButtonRotationAndCoverage:
    # Judgment call 6: the button advances one seat per hand and profiles stay put, so over
    # any multiple of six hands every profile plays every position equally.
    def test_the_button_advances_one_seat_per_hand(self, self_play) -> None:
        buttons = [hand.button_seat for hand in self_play.hands]

        assert buttons == [(self_play.hands[0].button_seat + n) % SEATS for n in range(RUN_HANDS)]

    def test_every_seat_occupies_every_position_the_same_number_of_times(self, self_play) -> None:
        seats = tuple(range(SEATS))
        held: dict[int, Counter] = {seat: Counter() for seat in seats}
        for hand in self_play.hands:
            for seat in seats:
                held[seat][position_for_seat(seats, hand.button_seat, seat)] += 1

        for seat in seats:
            assert set(held[seat].values()) == {RUN_HANDS // ORBIT}, (seat, held[seat])

    def test_the_per_position_counts_are_reported_rather_than_asserted(self, self_play) -> None:
        assert self_play.position_counts
        for counts in self_play.position_counts.values():
            assert sum(counts.values()) == RUN_HANDS


class TestProfiles:
    # A profile is a strategy plus the metadata a report needs, and no poker logic.
    def test_two_profiles_differing_only_in_name_play_identically(self) -> None:
        """Two runs of thirty-six Nones are equal, so this compared nothing until it moved."""
        renamed = tuple(
            replace(profile, name=f"{profile.name}-renamed")
            for profile in contested_config().profiles
        )
        original = run_simulation(contested_config())
        under_new_names = run_simulation(contested_config(profiles=renamed))

        assert all(hand.normalized is not None for hand in original.hands)
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

    # Judgment call 5: six-max at exactly 100bb, because any other configuration measures
    # the refusal path and nothing else. Rejected at setup, not part way in.
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
    # Judgment call 2 gave self-play the symmetry criteria; the chart seating now meets them only
    # because it never plays, so the assertion moves to where chips move.
    def test_the_table_nets_to_zero_across_every_seat(self, contested) -> None:
        totals = Counter()
        for hand in contested.hands:
            totals.update(hand.stack_deltas)

        assert sum(totals.values()) == 0
        assert any(total != 0 for total in totals.values()), totals

    # And the floor run carries one directional number, which must come out positive.
    def test_the_chart_bot_beats_a_bot_that_folds_everything(self, floor) -> None:
        chart = floor.chips_per_hand(CHART_PROFILE)

        assert chart > 0, floor.chips_per_hand_by_profile()

    def test_the_floor_run_counts_the_hands_the_committed_chart_can_actually_play(
        self, floor
    ) -> None:
        """The one place this file can tell the ruled chart from an empty one. Every other
        played-poker claim runs on a seating that never consults the chart, and the two that do
        assert only that it refuses, which an empty chart does too. Masking the library and
        rerunning: under the 86 the composite refuses 24 and counts 12; without the small blind's
        open, and under a chart holding nothing, 30 and 6. So the pair asserts the one surviving
        opening range survived. `chips_per_hand` is not pinned beside them - it reads 50.0 under
        all three, counting the button rotation rather than any decision."""
        assert floor.refusal_counts() == {CHART_PROFILE: 24, "reference-check-fold": 0}
        assert floor.hands_counted() == 12

    # Judgment call 3: the figure is reported with its own standard error, and no winner is
    # named when the run cannot separate the profiles.
    def test_every_reported_figure_carries_a_standard_error(self, contested) -> None:
        """`>= 0` was not a claim: a standard error cannot be negative, and the zero a
        profile with no counted hand returns satisfies it, so it held for a constant."""
        errors = {name: contested.standard_error(name) for name in contested.profile_names()}

        assert len(errors) == 3, errors
        assert all(error > 0 for error in errors.values()), errors

    def test_a_difference_inside_the_noise_is_not_reported_as_a_finding(self, contested) -> None:
        """Six identical profiles are one profile, so the old form asserted `() == ()` for
        any simulator whatever. Over `contested` the rule bites both ways: the raiser holds
        the largest figure at +1,402.78 chips a hand and is not named, its variation being
        898.09, while the four check-folds lose 37.50 and are named, theirs being 16.83.
        Ranking by chips names the raiser, the finding judgment call 3 exists to refuse."""
        figures = contested.chips_per_hand_by_profile()
        errors = {name: contested.standard_error(name) for name in contested.profile_names()}
        biggest = max(figures, key=lambda name: abs(figures[name]))
        reported = contested.separated_profiles()

        assert all(figure != 0 for figure in figures.values()), figures
        assert biggest not in reported, (biggest, figures, errors)
        assert abs(figures[biggest]) < 2 * errors[biggest], (figures, errors)
        assert reported == ("reference",), (reported, figures, errors)

    # Refusal coverage is a headline number. The key set cannot fail - `refusal_counts` seeds a
    # zero per name and only increments those keys - so the counts are pinned instead, both ends.
    def test_refusal_coverage_is_reported_per_profile(self, self_play, contested) -> None:
        assert self_play.refusal_counts() == {CHART_PROFILE: RUN_HANDS}
        assert contested.refusal_counts() == {"caller": 0, "raiser": 0, "reference": 0}

    def test_refused_hands_leave_the_chips_per_hand_denominator(self, self_play, contested) -> None:
        """Pinned at both ends: over the chart seating alone the identity is 0 == 0."""
        for run in (self_play, contested):
            played = sum(1 for hand in run.hands if hand.outcome != "refused")

            assert run.hands_counted() == played

        assert self_play.hands_counted() == 0
        assert contested.hands_counted() == RUN_HANDS

    def test_the_seed_and_the_hand_count_are_carried_on_the_result(self, self_play) -> None:
        assert self_play.seed == SEED
        assert self_play.hands_dealt() == RUN_HANDS


class TestRefusalsAreActionable:
    """The half of this phase that turns a coverage count into a work list. The first
    simulator reported the charts silent 128 times and could not say where, its record being
    built from whole streets where a refusal never completes one. Every
    assertion here guards against vacuity first. On `limped` the refusals are two families,
    the limped cell and the lojack's retired open, and the inventory accounts for both."""

    def test_a_refused_hand_keeps_every_action_taken_before_the_refusal(self, limped) -> None:
        refused = [hand for hand in limped.hands if hand.outcome == "refused"]

        assert refused, "no hand was refused, so this assertion is vacuous"
        assert any(hand.decisions for hand in refused), "no refusal followed a real action"
        for hand in refused:
            recorded = sum(len(street.actions) for street in hand.streets)

            # Two blind posts, which are forced rather than chosen, plus one recorded action
            # per decision the simulator actually applied before the refusal.
            assert recorded == len(hand.decisions) + 2, hand.hand_id

    def test_a_refusal_names_the_spot_the_chart_could_not_answer(self, limped) -> None:
        refused = [hand for hand in limped.hands if hand.outcome == "refused"]

        assert refused, "no hand was refused, so this assertion is vacuous"
        for hand in refused:
            assert hand.refusal_detail, hand.hand_id
            named = dict(hand.refusal_detail)
            assert named.get("hand_class"), hand.hand_id
            assert named.get("table_size") == str(SEATS), hand.hand_id

    def test_the_inventory_accounts_for_every_refused_hand(self, limped) -> None:
        inventory = limped.refusal_inventory()
        refused = sum(1 for hand in limped.hands if hand.outcome == "refused")

        assert refused > 0
        assert sum(spot.hands for spot in inventory) == refused

    def test_the_inventory_is_ordered_by_how_many_hands_reached_each_spot(self, limped) -> None:
        counts = [spot.hands for spot in limped.refusal_inventory()]

        assert counts == sorted(counts, reverse=True)

    def test_the_inventory_is_stable_across_runs(self) -> None:
        """Byte-stability is what makes its diff a record of coverage improving."""
        first = run_simulation(limped_config()).refusal_inventory()
        second = run_simulation(limped_config()).refusal_inventory()

        assert first == second
