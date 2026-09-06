"""What a simulation run is allowed to claim: chips per hand, its noise, and its coverage.

Split from `tests/test_simulator.py` when the pair went past the 700-line cap. That file
owns the harness - the seatings, the test strategies and the run fixtures - along with
every claim about what the simulator does to a hand, and it keeps the refusal work list
because that is where `verification/mutations.yml` aims two of its simulator canaries. The
line between the two is that nothing here is about a hand: these are claims about
`measure.py`, the layer that turns a finished run into a figure a report may print.

The harness comes from the sibling module by import rather than by copy. The fixtures do
not travel with it - a module-scoped fixture belongs to the module that defines it - so the
runs are rebuilt here from the sibling's own config builders, which is what keeps the two
files describing the same three seatings.

Both files run under `pytest_simulator`, which names this one beside the sibling.
"""

from __future__ import annotations

from collections import Counter

import pytest
from test_simulator import (
    CHART_PROFILE,
    FIRST_IN_POSITIONS,
    RUN_HANDS,
    SEATS,
    SEED,
    config,
    contested_config,
    floor_config,
)

from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.simulator.run import SimulationResult, run_simulation


@pytest.fixture(scope="module")
def self_play() -> SimulationResult:
    return run_simulation(config())


@pytest.fixture(scope="module")
def floor() -> SimulationResult:
    return run_simulation(floor_config())


@pytest.fixture(scope="module")
def contested() -> SimulationResult:
    return run_simulation(contested_config())


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
        """The one place this file can tell the ruled chart from an empty one.

        Five reference check-folds never raise and never call, so the only spots the
        composite is ever asked about are first-in ones: it opens from each of the five
        seats that can be first in, and in the big blind everyone has folded and it is not
        asked at all. The cutover commits all five, so the run refuses nothing and counts
        every hand - derived from the ruled census rather than measured, since a seating
        that can only reach five named spots needs no run to say which they are.

        The figures moved and are stated as moved. Masking the library and rerunning under
        the 86, which held one of the five: 24 refusals and 12 counted, one refusal per hand
        opened from the lojack, hijack, cutoff or button. Under a chart holding nothing at
        all: 30 and 6. So the pair still separates the ruled chart from an empty one, in the
        opposite direction, and the third assertion is what stops it passing for a chart
        that answers five other things - the positions the composite actually decided at
        have to be the five that can be first in.

        `chips_per_hand` is not pinned beside them: it read 50.0 under all three of those
        charts, counting the button rotation rather than any decision."""
        seats = tuple(range(SEATS))
        hero = floor.seats_for(CHART_PROFILE)[0]
        decided_at = {
            position_for_seat(seats, hand.button_seat, hero)
            for hand in floor.hands
            for record in hand.decisions
            if record.query.seat == hero and record.query.street == "preflop"
        }

        assert floor.refusal_counts() == {CHART_PROFILE: 0, "reference-check-fold": 0}
        assert floor.hands_counted() == RUN_HANDS
        assert decided_at == FIRST_IN_POSITIONS, decided_at

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

    # Refusal coverage is a headline number, and the key set cannot fail - `refusal_counts`
    # seeds a zero per name and only increments those keys - so the figures carry it. The
    # self-play figure moved off `RUN_HANDS` with its premise and no ruled count replaces it,
    # so it is checked against a walk written here: `refusal_counts` reads `refusing_seat` and
    # this reads the outcome, so the two fields have to agree about which hands died.
    def test_refusal_coverage_is_reported_per_profile(self, self_play, contested) -> None:
        refused = sum(1 for hand in self_play.hands if hand.outcome == "refused")

        assert self_play.refusal_counts() == {CHART_PROFILE: refused}
        assert contested.refusal_counts() == {"caller": 0, "raiser": 0, "reference": 0}

    def test_refused_hands_leave_the_chips_per_hand_denominator(self, self_play, contested) -> None:
        """Pinned at both ends, because `0 == 0` is what a run that plays nothing reports.

        That is the figure the cutover moved: the chart seating counted no hand at all while
        the lojack's open was refused, so the identity held of an empty denominator. It plays
        now, and how many of the 36 survive is the run's to say rather than this file's."""
        for run in (self_play, contested):
            played = sum(1 for hand in run.hands if hand.outcome != "refused")

            assert run.hands_counted() == played

        assert self_play.hands_counted() > 0
        assert contested.hands_counted() == RUN_HANDS

    def test_the_seed_and_the_hand_count_are_carried_on_the_result(self, self_play) -> None:
        assert self_play.seed == SEED
        assert self_play.hands_dealt() == RUN_HANDS
