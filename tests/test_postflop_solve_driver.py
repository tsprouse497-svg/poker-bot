"""Phase 16, stage 4: the solve driver's own guards.

Split from `tests/test_postflop_artifact.py` at the 700-line cap. That file owns the committed
index, the sample, the byte budget and the input ranges; this one owns the thing that produced
them and the configuration it was pointed at. Both run under `pytest_postflop_betting`.

The driver never runs in the gate - the gate has no solver, no network and no Rust toolchain - so
these are the only tests its guards will ever get. A guard nobody tested is a guard nobody has,
and two of the three below exist because the repo already found the guard missing:
`SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` and `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`.

It also holds decision 14's chip-to-menu matching, moved here from
`tests/test_postflop_query_recording.py` at the same cap on 2026-09-15. The menu it matches
against is the solve configuration's own `33 75`, checked a few classes above, so the two sit
together rather than one of them sitting beside the query shape.

Reached through a fixture whose import sits in the function body; the head of
`tests/test_postflop_key.py` says why.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.repo_paths import REPO_ROOT

SOLVE_CONFIG_PATH = REPO_ROOT / "data" / "artifacts" / "postflop" / "solve_config.json"


def load(path: Path):
    assert path.is_file(), (
        f"{path.relative_to(REPO_ROOT)} is missing, so the committed solve owes everything this"
        " file checks and has delivered none of it"
    )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def driver_module():
    """`solver_artifacts.postflop_solve_driver`: the thing that drives GTOpen and writes the
    artifact."""
    import poker_training_bot.solver_artifacts.postflop_solve_driver as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 16's contract requires it and no"
        " implementation has been written yet"
    )
    return found


@pytest.fixture(scope="module")
def key_module():
    """`solver_artifacts.postflop_key`, which publishes the menu and the matching rule."""
    import poker_training_bot.solver_artifacts.postflop_key as module

    return module


# --------------------------------------------------------------------------- #
# The solve driver's own guards
# --------------------------------------------------------------------------- #


class TestTheSolveDriverRefusesBeforeItSolves:
    """Criterion: the solve driver carries its own memory ceiling and refuses above it before
    solving; it refuses an `allin_threshold` below 1.0 rather than silently asking for 0.67%; and
    a route recorded UNRUN is not assumed to work."""

    def test_the_driver_publishes_a_memory_ceiling(self, driver_module) -> None:
        """`SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` rests on Darwin lacking `/proc/meminfo`. The
        rented Linux box has one, so the entry is restated against that machine - but the
        driver's own ceiling is required either way, which is what this pins."""
        ceiling = owed(driver_module, "MEMORY_CEILING_BYTES")

        assert isinstance(ceiling, int) and ceiling > 0

    def test_a_planned_solve_above_the_ceiling_is_refused_before_solving(
        self, driver_module
    ) -> None:
        check = owed(driver_module, "check_memory_ceiling")
        ceiling = owed(driver_module, "MEMORY_CEILING_BYTES")
        refusal = owed(driver_module, "SolveDriverError")

        with pytest.raises(refusal):
            check(ceiling + 1)

    def test_a_planned_solve_under_the_ceiling_is_allowed(self, driver_module) -> None:
        """The positive control: a guard that refuses everything is not a guard."""
        check = owed(driver_module, "check_memory_ceiling")
        ceiling = owed(driver_module, "MEMORY_CEILING_BYTES")

        assert check(ceiling - 1) is None or check(ceiling - 1) is True

    def test_an_allin_threshold_below_one_is_refused(self, driver_module) -> None:
        validate = owed(driver_module, "validate_allin_threshold")

        with pytest.raises(ValueError):
            validate(0.67)

    def test_an_allin_threshold_that_reads_as_a_percent_is_accepted(self, driver_module) -> None:
        validate = owed(driver_module, "validate_allin_threshold")

        assert validate(67.0) == pytest.approx(67.0)

    def test_the_batch_reports_route_is_recorded_as_exercised_or_unused(
        self, driver_module
    ) -> None:
        """`/api/reports/*` is recorded in `docs/GTOPEN_SOLVER_NOTES.md` as README-sourced and
        never executed. The driver either exercises it and reports what it cost, or does not use
        it and says so. A third state - used and unmeasured - is what this refuses."""
        status = owed(driver_module, "REPORTS_ROUTE_STATUS")

        assert status in {"exercised", "not-used"}, status


# --------------------------------------------------------------------------- #
# What the driver does with a field the server did not send
# --------------------------------------------------------------------------- #


class ScriptedServer:
    """A GTOpen that answers from a script rather than from a socket.

    One list of answers per route, the last entry repeating, so a poll loop needs no padded
    script. No server, no network and no real clock: `run_solve` takes its transport, its
    `now` and its `sleep` as arguments precisely so a guard can be exercised in milliseconds.
    """

    def __init__(self, **routes: list[dict]) -> None:
        self.script = {f"/api/{name}": list(answers) for name, answers in routes.items()}
        self.calls: list[str] = []

    def __call__(self, path: str, body: dict | None = None) -> dict:
        self.calls.append(path)
        answers = self.script.get(path, [{}])
        return answers.pop(0) if len(answers) > 1 else answers[0]


HEALTHY_STATUS = {"state": "complete", "exploit_pct": 0.24, "iteration": 240}
"""What a server that finished answers: not running, under the 0.3%-of-pot target, inside the
1,200-iteration cap. Every case below removes or spoils exactly one field of this, so the case
is that one change and nothing else."""


def a_plan(driver_module):
    """One flop `plan_refusals` passes, so a case reaches the transport rather than the
    pre-flight. The board and the line are the committed sample's own."""
    return owed(driver_module, "SolvePlan")(
        label="Kh7d2c single-raised",
        board="Kh7d2c",
        preflop_line="t6/d100/BB/BTN:raise@2.5,BB:call",
        range_oop="AA:1",
        range_ip="AA:1",
        starting_pot=5.5,
        effective_stack=97.5,
    )


def run_against(driver_module, server):
    """`run_solve` against a scripted server, with the clock and the sleep stubbed out."""
    return owed(driver_module, "run_solve")(
        a_plan(driver_module), server, sleep=lambda _: None, now=lambda: 0.0
    )


class TestTheDriverRefusesAFieldTheServerDidNotSend:
    """Decision 16b, ruled by Taylor 2026-09-16, as an addition rather than a correction.

    Nothing in this repo calls `run_solve`, so none of the four fail-closed reads committed at
    `abc6603` is covered by anything. Measured before the ruling: restore all four
    `.get(key, default)` defaults and this file still reports what it reports now.

    Each of those defaults passed the guard it fed. An absent `arena_mb` planned a zero-byte
    tree, so the memory ceiling - the whole reason the tree is built before it is solved -
    cleared trivially. An absent `exploit_pct` read as 0.0% of pot, better than the target, so a
    cell that was never solved classified as converged and committed, and the bot would play it
    as studied strategy. An absent `iteration` read as zero, under the cap. An absent `state`
    ended the poll on its first look, which makes a mid-solve reading the final one.

    A mutation canary cannot stand in for these, because a canary is only as good as the test it
    points at and there was no test to point at. Each case asserts that the refusal names **both**
    the route and the field: one saying only that something was missing sends nobody anywhere.
    """

    def test_a_healthy_server_solves_rather_than_refusing(self, driver_module) -> None:
        """The positive control, and it is load-bearing: all four cases below would also pass
        against a driver that refused every answer it was ever handed."""
        server = ScriptedServer(status=[HEALTHY_STATUS], spot=[{"arena_mb": 1.0}], solve=[{}])

        outcome = run_against(driver_module, server)

        assert outcome.exploit_pct_of_pot == pytest.approx(0.24)
        assert outcome.iterations == 240
        assert server.calls[:3] == ["/api/status", "/api/spot", "/api/solve"]

    def test_a_spot_answered_without_arena_mb_is_refused(self, driver_module) -> None:
        """The arena is the only number the memory ceiling ever sees. Defaulted to 0.0 it
        planned a zero-byte tree, which clears any ceiling."""
        server = ScriptedServer(status=[HEALTHY_STATUS], spot=[{}], solve=[{}])

        with pytest.raises(owed(driver_module, "SolveDriverError")) as raised:
            run_against(driver_module, server)

        assert "/api/spot" in str(raised.value) and "arena_mb" in str(raised.value)

    def test_a_status_answered_without_state_is_refused(self, driver_module) -> None:
        """Read twice: once before `/api/spot` to refuse a server already mid-solve, and once a
        poll to decide whether the solve is still running. Absent, both readings invert."""
        server = ScriptedServer(
            status=[{"exploit_pct": 0.24, "iteration": 240}], spot=[{"arena_mb": 1.0}], solve=[{}]
        )

        with pytest.raises(owed(driver_module, "SolveDriverError")) as raised:
            run_against(driver_module, server)

        assert "/api/status" in str(raised.value) and "state" in str(raised.value)

    def test_a_status_answered_without_exploit_pct_is_refused(self, driver_module) -> None:
        """The one that reaches committed data. 0.0% of pot is better than the 0.3% target, so
        the cell classifies as converged and is committed as solved poker."""
        server = ScriptedServer(
            status=[{"state": "complete", "iteration": 240}], spot=[{"arena_mb": 1.0}], solve=[{}]
        )

        with pytest.raises(owed(driver_module, "SolveDriverError")) as raised:
            run_against(driver_module, server)

        assert "/api/status" in str(raised.value) and "exploit_pct" in str(raised.value)

    def test_a_status_answered_without_iteration_is_refused(self, driver_module) -> None:
        """Defaulted to zero it sits under the 1,200 cap, so a capped solve reports as one that
        converged early and the index's iteration count becomes fiction."""
        server = ScriptedServer(
            status=[{"state": "complete", "exploit_pct": 0.24}], spot=[{"arena_mb": 1.0}],
            solve=[{}],
        )

        with pytest.raises(owed(driver_module, "SolveDriverError")) as raised:
            run_against(driver_module, server)

        assert "/api/status" in str(raised.value) and "iteration" in str(raised.value)

    def test_an_exploit_pct_that_is_not_a_number_is_refused_rather_than_parsed(
        self, driver_module
    ) -> None:
        """The fifth case, and it is a different guard from the four: presence is not enough.
        A string that would parse is refused too, because the comparison against the target -
        not the parse - is what this field feeds."""
        server = ScriptedServer(
            status=[{**HEALTHY_STATUS, "exploit_pct": "0.24"}], spot=[{"arena_mb": 1.0}],
            solve=[{}],
        )

        with pytest.raises(owed(driver_module, "SolveDriverError")) as raised:
            run_against(driver_module, server)

        assert "/api/status" in str(raised.value) and "exploit_pct" in str(raised.value)
        assert "not a number" in str(raised.value)


# --------------------------------------------------------------------------- #
# The configuration the driver was pointed at, committed beside the data
# --------------------------------------------------------------------------- #


class TestTheSolveConfigurationIsCommittedBesideTheData:
    """Criterion: two bet sizes on every street - flop `33 75`, turn and river `66 125`,
    `raise: "2.5x"`, `donk` empty - identically on both seats."""

    @pytest.fixture(scope="class")
    def config(self):
        return load(SOLVE_CONFIG_PATH)

    def test_both_seats_carry_the_same_menu(self, config) -> None:
        seats = config.get("seats")

        assert seats and len(seats) == 2, "a two-range solve, configured identically on both sides"
        first, second = (seats[name] for name in sorted(seats))
        assert first == second

    def test_the_flop_menu_is_thirty_three_and_seventy_five(self, config) -> None:
        for seat in config["seats"].values():
            assert seat["flop"]["bet"] == ["33", "75"], seat

    def test_the_turn_and_river_menu_is_sixty_six_and_one_twenty_five(self, config) -> None:
        for seat in config["seats"].values():
            assert seat["turn"]["bet"] == ["66", "125"], seat
            assert seat["river"]["bet"] == ["66", "125"], seat

    def test_the_raise_is_two_and_a_half_x_on_every_street(self, config) -> None:
        for seat in config["seats"].values():
            for street in ("flop", "turn", "river"):
                assert seat[street]["raise"] == "2.5x", (street, seat)

    def test_no_street_offers_a_donk(self, config) -> None:
        for seat in config["seats"].values():
            for street in ("flop", "turn", "river"):
                assert seat[street].get("donk", []) == [], (street, seat)

    def test_the_allin_threshold_is_a_percent_of_the_remaining_stack(self, config) -> None:
        """`SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`. `tree.rs` snaps any bet reaching
        `allin_threshold * max_to` to a stack-off outside the `add_allin` guard, so `add_allin:
        false` still holds jams by conversion. Posted as a percent postflop where preflop takes a
        fraction, and a value below 1.0 is asking for 0.67% rather than 67%."""
        threshold = config.get("allin_threshold")

        assert isinstance(threshold, int | float) and not isinstance(threshold, bool)
        assert threshold >= 1.0, (
            f"{threshold} postflop reads as {threshold}% of the remaining stack, which snaps"
            " every bet to a stack-off"
        )


# --------------------------------------------------------------------------- #
# A chip bet is matched to the ruled menu by pot fraction
# --------------------------------------------------------------------------- #

SINGLE_RAISED_POT_CHIPS = 550
"""5.5bb at 50/100, the pot of the covered `@2.5` line, and the pot every figure below is in."""


class TestAChipBetIsMatchedToTheMenuByPotFraction:
    """Decision 14, `frozen-into-data`, ruled by Taylor 2026-09-15.

    The ruled flop menu is `33 75` as a percent of pot and the table is in chips, and the
    arithmetic does not come out even: 33% of the 550-chip pot is 181.5, which no dealer can
    push. A strict equality match at stage 6 would refuse every faced bet at a real table and
    kill the whole raise branch of the committed artifact with nothing going red; a loose one with
    no stated ceiling could as easily swallow a 40% bet as a 32.7% one.

    The rule: **match by pot fraction inside a named tolerance, refuse anything that matches no
    entry rather than snapping it to the nearer one, and convert a committed artifact size to
    chips by rounding to the nearest chip.** The tolerance is a module constant the test imports,
    so a later re-ruling moves one number. The class was filed `runtime-reversible` and corrected:
    a default a frozen test pins is a fixture, which halts for a human, and it did. Decision 14
    carries the ruling, the options as put, and what the chosen width costs; the tests below
    re-derive every bound rather than quoting it.
    """

    def test_the_tolerance_is_published_as_a_named_constant(self, key_module) -> None:
        assert owed(key_module, "MENU_FRACTION_TOLERANCE") == pytest.approx(0.05)

    def test_the_tolerance_sits_between_the_two_bounds_the_arithmetic_forces(
        self, key_module
    ) -> None:
        """Both bounds recomputed here rather than quoted.

        The floor is what a real table's rounding costs: the committed fixtures bet 180 into 550,
        which is 32.7273%, so the tolerance must exceed `|0.327273 - 0.33| = 0.002727`. The
        ceiling is half the distance to the next menu entry, `(0.75 - 0.33) / 2 = 0.21`, past
        which one bet lands in two buckets. The binding ceiling in practice is the 50% bet the
        phase already requires to be refused, `|0.50 - 0.33| = 0.17`.

        The ruled 0.05 is 18.3 times the floor and 3.4 times inside the tighter ceiling. At 0.05
        the two buckets reach 38% and 70% and still do not touch; 0.17 is what a later re-ruling
        has left before a 50% bet starts matching 33%.
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

    def test_the_round_numbers_a_real_table_bets_match_rather_than_refuse(
        self, key_module
    ) -> None:
        """What the ruled width was chosen for. 200 chips is 36.36% of this pot and 175 is
        31.82%; both are numbers people actually bet and neither is a rounding of 33%. At the 0.01
        first proposed, both refused and the raise frequency would have read near zero."""
        match = owed(key_module, "match_menu_fraction")

        assert match(200, SINGLE_RAISED_POT_CHIPS) == pytest.approx(0.33)
        assert match(175, SINGLE_RAISED_POT_CHIPS) == pytest.approx(0.33)

    def test_the_bucket_ends_where_the_tolerance_says_and_not_a_chip_later(
        self, key_module
    ) -> None:
        """The sharpest whole-chip pair this pot allows. 154 chips is 28.000% of 550, the last
        chip inside; 153 is 27.82% and the first outside. A stage 6 that widened the bucket by
        rounding, or narrowed it, fails on one of the two."""
        match = owed(key_module, "match_menu_fraction")

        assert match(154, SINGLE_RAISED_POT_CHIPS) == pytest.approx(0.33)
        assert match(153, SINGLE_RAISED_POT_CHIPS) is None

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
