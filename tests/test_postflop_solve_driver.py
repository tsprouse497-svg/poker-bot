"""Phase 16, stage 4: the solve driver's own guards.

Split from `tests/test_postflop_artifact.py` at the 700-line cap. That file owns the committed
index, the sample, the byte budget and the input ranges; this one owns the thing that produced
them and the configuration it was pointed at. Both run under `pytest_postflop_betting`.

The driver never runs in the gate - the gate has no solver, no network and no Rust toolchain - so
these are the only tests its guards will ever get. A guard nobody tested is a guard nobody has,
and two of the three below exist because the repo already found the guard missing:
`SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` and `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`.

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
