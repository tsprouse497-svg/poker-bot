"""Simulator tests, written from the contract before the implementation existed.

Three properties carry this file and are the three a simulator can get wrong unnoticed:
`TestChipConservation` checks the books per hand, since an aggregate netting to zero hides two
errors that cancel; `TestDeterminism`, that a run is a pure function of seed, seating and profiles;
`TestReplayAgreement`, that the frozen replayer agrees. All three sit on `contested` - one caller,
one raiser, four check-folds - which reads no chart at all, so no cutover can empty them out. That
placement was made when the retired 86 held one opening range and six chart seats produced 36
refusals and nothing else; the cutover commits a first-in spot for every seat that can be first in,
so `self_play` plays hands again, but a claim about the simulator's own books belongs on a seating
whose behaviour no artifact decides. Each moved claim carries its own counter: a counter in a
sibling test is no guard.

Every chart-driven figure here is measured by the run rather than pinned. The contract expects the
simulator's figures and every refusal count to move a long way in both directions, and the ruled
list of counts for this cutover holds none of them.

What a run is allowed to *claim* - chips per hand, its standard error, and which profile a refusal
is booked against - is the companion's, `tests/test_simulator_reports.py`, which imports this
harness rather than copying it. The refusal work list stays here, because two of this
command's mutation canaries aim at it. Both files run under `pytest_simulator`, which names
them both.
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
# six. No run length is sized to reach a refusal: the chart seating refuses on its own tree
# depth rather than at a rate any run length here could be set against.
ORBIT = SEATS
RUN_HANDS = 6 * ORBIT

TERMINAL_OUTCOMES = frozenset({"showdown", "uncontested", "refused"})

# A first-in key ends `/rfi`, and the cutover commits one for each of the five seats that can
# be first in. That suffix is how this file says "a spot the chart is ruled to hold" without
# naming a facing-an-open key, which the ruled census counts at 25 without listing them.
FIRST_IN_SUFFIX = "/rfi"
FIRST_IN_POSITIONS = frozenset({"LJ", "HJ", "CO", "BTN", "SB"})
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
    simulator, and a seating whose behaviour an artifact decides is the wrong place to make one.
    Measured: 36 hands, 11 min-raises, 11 flop jams, 30 layered settlements, a 20,150 pot; over a
    caller and five check-folds, no raise and a 250-chip largest pot."""
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
    showdowns and 5 uncontested hands. That seating reads no chart, so the cutover does not
    move it. Over `config()` the histogram is the chart's, and nothing here pins it."""
    return Counter(record.outcome.action for hand in result.hands for record in hand.decisions)


class TestEveryHandReachesATerminalState:
    # No hand ends by exhaustion, exception, or timeout.
    def test_every_hand_has_a_terminal_outcome(self, self_play) -> None:
        assert len(self_play.hands) == RUN_HANDS
        assert {hand.outcome for hand in self_play.hands} <= TERMINAL_OUTCOMES

    def test_six_chart_seats_play_the_hand_out_rather_than_dying_on_the_open(
        self, self_play
    ) -> None:
        """Phase 07's own claim, restored with its premise.

        It read "six copies of a chart bot produce both showdowns and uncontested wins"
        until the 2026-08-25 pass inverted it: the 86 held one opening range, so the lojack
        opened every hand into a spot the chart did not hold and all 36 died before a chip
        moved. The cutover commits a first-in spot for each of the five seats that can be
        first in, so nothing dies there and the run plays.

        Two claims, and the second is the one that fails loudly if the five opening ranges
        did not arrive: no refused hand names a first-in key. Refusals themselves are not
        asserted away - a four-bet is past the committed raise depth and six chart seats
        reach one - so their count is left to the run rather than pinned here.
        """
        outcomes = Counter(hand.outcome for hand in self_play.hands)
        died_first_in = [
            hand.hand_id
            for hand in self_play.hands
            if dict(hand.refusal_detail).get("spot_key", "").endswith(FIRST_IN_SUFFIX)
        ]

        assert died_first_in == [], died_first_in
        assert sum(outcomes.values()) == RUN_HANDS, outcomes
        assert outcomes["showdown"] > 0, outcomes
        assert outcomes["uncontested"] > 0, outcomes

    def test_both_played_outcomes_occur_where_hands_are_played(self, contested) -> None:
        """Both non-refusal outcomes happen, so `TERMINAL_OUTCOMES` is not one value, on a
        seating no artifact can empty: the raiser's gate keeps both reachable."""
        outcomes = Counter(hand.outcome for hand in contested.hands)

        assert outcomes["showdown"] > 0, outcomes
        assert outcomes["uncontested"] > 0, outcomes
        assert outcomes["refused"] == 0, outcomes

    def test_a_refused_hand_names_the_refusal_that_ended_it(self, limped, contested) -> None:
        """Both halves need a run they can fail in and no single run supplies both, and a
        pair of empty runs satisfies an unqualified for-each either way, so the counters are
        what stop this claiming nothing.

        The split was 36 and 36 while every hand in `limped` refused at the lojack's open.
        It moves: the limper only creates a limped pot in the seats where it acts first, and
        closing the action from the big blind it puts the table into a hand the chart plays
        out. So both counters are asserted non-zero and their total is pinned, which no
        empty run can satisfy, rather than a share being invented for either side."""
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

        assert named > 0, "no hand refused, so the named branch never ran"
        assert silent > 0, "no hand settled, so the silent branch never ran"
        assert named + silent == 2 * RUN_HANDS, (named, silent)

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
        setup. The limped key is asserted present, because the limp is meant to be the driver
        and the cutover leaves other families - a four-bet, a multiway spot - refused too."""
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
        collected keeps perfect books, and so does one never putting in a chip beyond the
        price it was asked."""
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
        zero for every seat rather than nothing. `booked` counts the hands walked, since an
        unqualified for-each over two empty runs makes the same claim about nothing."""
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
    # A simulation is a pure function of its seed, its seating and its profiles. Asserted on
    # `contested`, whose behaviour no artifact decides, so no cutover can turn these into
    # claims about a run that took no decision at all.
    def test_the_same_config_produces_an_identical_run(self) -> None:
        first = run_simulation(contested_config())
        second = run_simulation(contested_config())
        taken = actions_taken(first)

        assert taken["raise"] and taken["bet"] and taken["call"], taken
        assert max(hand.pot_collected for hand in first.hands) > STARTING_STACK
        assert first == second

    def test_the_same_config_produces_identical_audit_lines(self) -> None:
        """Two empty tuples compare equal, so this held for any simulator whatever until
        non-emptiness was asserted first. It still is."""
        first = run_simulation(contested_config())
        second = run_simulation(contested_config())
        lines = [
            tuple(record.to_json_line() for hand in result.hands for record in hand.decisions)
            for result in (first, second)
        ]

        assert lines[0], "no audit line was produced, so the comparison is vacuous"
        assert lines[0] == lines[1]

    def test_a_different_seed_produces_a_different_run(self) -> None:
        """The cards dealt have to differ, not just the integer each hand records: a run
        that refuses everything differs in its seed fields alone, as one fixed deck would."""
        first = run_simulation(contested_config())
        other = run_simulation(contested_config(seed=SEED + 1))
        dealt = [tuple(hand.normalized for hand in run.hands) for run in (first, other)]

        assert all(entry is not None for side in dealt for entry in side)
        assert dealt[0] != dealt[1]
        assert first != other

    # The usual way a "seeded" simulation turns out not to be: it reaches for the random
    # module's global state somewhere. Over a run that refuses everything the only card
    # reaching the record is a refusal's `hand_class`; here it is 36 hands, boards, actions.
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
    # it. It moved off the chart seating with the cutover: `self_play` refused all 36 hands
    # while the lojack's open was uncovered and refuses an unpinned number now, so the run
    # that is built to refuse - `limped`, whose limper asks for a cell `limp: false` forbids -
    # is the one that can carry the claim without a count nobody has measured.
    def test_a_refused_hand_carries_no_completed_hand_history(self, limped) -> None:
        refused = [hand for hand in limped.hands if hand.outcome == "refused"]

        assert refused, "no hand was refused, so this assertion is vacuous"
        assert all(hand.normalized is None for hand in refused)
        settled_ids = {hand.hand_id for hand in limped.settled_hands()}
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


class TestRefusalsAreActionable:
    """The half of this phase that turns a coverage count into a work list. The first
    simulator reported the charts silent 128 times and could not say where, its record being
    built from whole streets where a refusal never completes one. Every assertion here guards
    against vacuity first. On `limped` the refusals are the limped cell the ruled `limp: false`
    solve can hold no node for, together with whatever the limper's flatting drives the table
    into past the committed raise depth, and the inventory accounts for all of them."""

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
