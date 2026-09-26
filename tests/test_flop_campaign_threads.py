"""Phase 21, stage 4: part 1, every core - the thread count, the sweep, and the machine record.

Authored from `docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md` before any implementation exists.
Modules stage 6 has not written are reached through fixtures whose import sits in the function
body, so a missing one is a `ModuleNotFoundError` per test rather than a collection error; the
head of `tests/test_postflop_key.py` says why.

**Nothing here starts GTOpen.** The gate has no solver, so what is tested is the function that
builds a server's environment, the arithmetic that picks a thread count, and the reader that turns
a machine's own text into a record. The machine's readers - `sysctl` on Darwin, `/proc/cpuinfo`
and `/proc/meminfo` on Linux - are a hard external boundary and are injected; the Darwin text is
captured from the Apple M4 this phase measured on (`sysctl hw.ncpu hw.physicalcpu hw.memsize
machdep.cpu.brand_string hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu`, 2026-09-26). The
two Linux files are written in `/proc`'s documented format for an Intel Xeon and an AWS Graviton,
not captured, because no rented box existed when this was written; what they pin is the parse.

GTOpen's `init_rayon` (`crates/server/src/main.rs:2546-2563`) takes `SOLVER_THREADS` when it parses
and otherwise `max(1, available_parallelism() / 2)`, which is why the M4 printed five threads.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from poker_training_bot.solver_artifacts import postflop_solve_driver as driver
from poker_training_bot.solver_artifacts import postflop_transport as transport
from scripts.repo_paths import REPO_ROOT

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "flop_campaign"
GIB = 1024**3


@pytest.fixture(scope="module")
def threads():
    """`solver_artifacts.postflop_threads`: the thread count, the sweep and the server env."""
    import poker_training_bot.solver_artifacts.postflop_threads as module

    return module


@pytest.fixture(scope="module")
def machine():
    """`solver_artifacts.postflop_machine`: what a solve record says it ran on."""
    import poker_training_bot.solver_artifacts.postflop_machine as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 21's contract requires it and no"
        " implementation has been written yet"
    )
    return found


def sysctl_reader(name: str):
    """`sysctl -n <key>` answered from a captured `sysctl <keys>` listing."""
    values = {}
    for line in (FIXTURES / name).read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(": ")
        values[key.strip()] = value.strip()

    def read(key: str) -> str:
        if key not in values:
            raise KeyError(f"sysctl: unknown oid '{key}'")
        return values[key]

    return read


def proc_reader(files: dict[str, str]):
    """A `/proc` whose files are fixtures; anything else is absent, as on Darwin."""

    def read(path: str) -> str:
        if path not in files:
            raise FileNotFoundError(path)
        return (FIXTURES / files[path]).read_text(encoding="utf-8")

    return read


def no_sysctl(key: str) -> str:
    raise FileNotFoundError("sysctl is not on this machine")


XEON_PROC = {
    "/proc/cpuinfo": "linux_x86_xeon.cpuinfo.txt",
    "/proc/meminfo": "linux_64gib.meminfo.txt",
}
GRAVITON_PROC = {
    "/proc/cpuinfo": "linux_arm_graviton.cpuinfo.txt",
    "/proc/meminfo": "linux_64gib.meminfo.txt",
}
MEMINFO_BYTES = 65023156 * 1024
"""`MemTotal` in the fixture is in kibibytes, whatever the `kB` label says."""


# --------------------------------------------------------------------------- #
# Which thread counts are timed
# --------------------------------------------------------------------------- #


class TestTheThreadCountsTimedFollowTheMachine:
    """Criterion: the counts timed are GTOpen's default and a quarter, half, three quarters and
    all of the machine's logical processors, rounded, repeats dropped - on the M4 3, 5, 8, 10.

    The M4's 3 and 8 come from 2.5 and 7.5, which banker's rounding would make 2 and 8, so the
    contract's own figures rule the rounding half-up."""

    def test_gtopen_default_is_half_the_logical_processors_rounded_down(self, threads) -> None:
        default = owed(threads, "gtopen_default_threads")

        assert default(10) == 5
        assert default(7) == 3
        assert default(1) == 1, "max(1, n / 2): one processor still gets one thread"

    @pytest.mark.parametrize(
        ("logical", "expected"),
        [
            (10, (3, 5, 8, 10)),
            (64, (16, 32, 48, 64)),
            (48, (12, 24, 36, 48)),
            (16, (4, 8, 12, 16)),
            (7, (2, 3, 4, 5, 7)),
            (6, (2, 3, 5, 6)),
            (2, (1, 2)),
            (1, (1,)),
        ],
    )
    def test_the_counts_timed_on_a_machine(self, threads, logical, expected) -> None:
        """Seven logical processors is the one size here where GTOpen's default (3) is not
        also the half (3.5 rounds to 4), so both are timed and the list has five entries."""
        counts = owed(threads, "thread_counts_to_time")

        assert tuple(counts(logical)) == expected

    def test_the_counts_timed_always_include_gtopen_s_default(self, threads) -> None:
        counts = owed(threads, "thread_counts_to_time")
        default = owed(threads, "gtopen_default_threads")

        for logical in range(1, 97):
            assert default(logical) in counts(logical), logical
            assert logical in counts(logical), logical
            assert min(counts(logical)) >= 1, "a quarter of one processor rounds to zero"


# --------------------------------------------------------------------------- #
# The sweep: three interleaved runs per count, the median decides
# --------------------------------------------------------------------------- #

M4_COUNTS = (3, 5, 8, 10)

SWEEP_SECONDS = {3: (4.0, 4.1, 3.9), 5: (2.6, 2.5, 2.7), 8: (1.9, 2.0, 1.8), 10: (1.7, 1.6, 9.0)}
"""Invented seconds per iteration, shaped so the median and the mean disagree. Ten threads has
one run that shared the machine - the committed `9c8c7c` pair read 1.34 and 2.16 on one
configuration for exactly that reason - so its mean, 4.1, loses to eight threads' 1.9 while its
median, 1.7, wins. A sweep deciding by mean picks eight."""


def interleaved_runs(seconds: dict[int, tuple[float, ...]]) -> list[tuple[int, float]]:
    return [(count, seconds[count][round_]) for round_ in range(3) for count in sorted(seconds)]


class TestTheSweepVerdict:
    """Criterion: each count is timed three times interleaved, the median of the three decides,
    the fastest median is chosen, and the spread is reported. One run per count is not enough."""

    def test_the_schedule_interleaves_the_counts_three_times(self, threads) -> None:
        schedule = owed(threads, "interleaved_schedule")

        assert tuple(schedule(M4_COUNTS)) == M4_COUNTS * 3

    def test_the_stretch_is_one_hundred_iterations_three_times_per_count(self, threads) -> None:
        assert owed(threads, "ITERATIONS_PER_STRETCH") == 100
        assert owed(threads, "REPEATS_PER_COUNT") == 3

    def test_the_median_decides_and_not_the_mean(self, threads) -> None:
        verdict = owed(threads, "sweep_verdict")(interleaved_runs(SWEEP_SECONDS))

        assert verdict.chosen_threads == 10
        assert verdict.medians == {3: 4.0, 5: 2.6, 8: 1.9, 10: 1.7}

    def test_the_spread_of_each_count_is_its_slowest_run_less_its_fastest(self, threads) -> None:
        verdict = owed(threads, "sweep_verdict")(interleaved_runs(SWEEP_SECONDS))

        assert verdict.spreads[10] == pytest.approx(7.4)
        assert verdict.spreads[8] == pytest.approx(0.2)

    def test_the_fastest_median_wins_whichever_count_it_is(self, threads) -> None:
        """The positive control against a verdict that always picks the most threads."""
        seconds = {3: (4.0, 4.0, 4.0), 5: (1.5, 1.5, 1.6), 8: (1.9, 1.9, 1.9), 10: (2.2, 2.1, 2.3)}

        verdict = owed(threads, "sweep_verdict")(interleaved_runs(seconds))

        assert verdict.chosen_threads == 5

    def test_one_run_per_count_is_refused(self, threads) -> None:
        with pytest.raises(ValueError):
            owed(threads, "sweep_verdict")([(3, 4.0), (5, 2.6), (8, 1.9), (10, 1.7)])

    def test_runs_taken_one_count_at_a_time_are_refused_as_not_interleaved(self, threads) -> None:
        """Three runs of three threads back to back, then three of five, and so on: every run of
        one count shares whatever else the machine was doing in that stretch, which is the
        failure interleaving exists to spread across counts."""
        blocked = [(count, SWEEP_SECONDS[count][i]) for count in M4_COUNTS for i in range(3)]

        with pytest.raises(ValueError):
            owed(threads, "sweep_verdict")(blocked)

    def test_the_sweep_record_names_the_machine_its_runs_and_its_verdict(
        self, threads, machine
    ) -> None:
        """One record per machine, never carried to another: the report re-derives the counts
        from the machine's own processor count and the choice from the runs."""
        m4 = owed(machine, "measure_machine")(
            platform="Darwin",
            sysctl=sysctl_reader("darwin_apple_m4.sysctl.txt"),
            read_text=proc_reader({}),
        )

        record = owed(threads, "sweep_record")(m4, interleaved_runs(SWEEP_SECONDS))

        assert record["machine"]["cpu_model"] == "Apple M4"
        assert record["machine"]["logical_processors"] == 10
        assert tuple(record["counts"]) == M4_COUNTS
        assert record["gtopen_default_threads"] == 5
        assert record["chosen_threads"] == 10
        assert [run["threads"] for run in record["runs"]] == list(M4_COUNTS * 3)
        assert record["runs"][11]["seconds_per_iteration"] == 9.0

    def test_a_sweep_record_whose_counts_are_not_this_machine_s_is_refused(
        self, threads, machine
    ) -> None:
        """Runs at 16, 32, 48 and 64 threads handed in with the M4's record are another
        machine's sweep carried over, which the contract forbids by name."""
        m4 = owed(machine, "measure_machine")(
            platform="Darwin",
            sysctl=sysctl_reader("darwin_apple_m4.sysctl.txt"),
            read_text=proc_reader({}),
        )
        on_a_64_way_box = {3: 16, 5: 32, 8: 48, 10: 64}
        carried = [
            (on_a_64_way_box[count], seconds) for count, seconds in interleaved_runs(SWEEP_SECONDS)
        ]

        with pytest.raises(ValueError):
            owed(threads, "sweep_record")(m4, carried)


# --------------------------------------------------------------------------- #
# Every server gets an explicit SOLVER_THREADS, or does not start
# --------------------------------------------------------------------------- #


class TestEveryServerIsGivenAnExplicitThreadCount:
    """Criterion: every server the driver starts is given an explicit thread count through
    `SOLVER_THREADS`, and the driver refuses to start one without it."""

    def test_the_variable_is_the_one_gtopen_reads(self, threads) -> None:
        assert owed(threads, "SOLVER_THREADS_VARIABLE") == "SOLVER_THREADS"

    def test_the_count_given_is_the_count_in_the_server_environment(self, threads) -> None:
        environment = owed(threads, "server_environment")(10, base={"PATH": "/usr/bin"})

        assert environment["SOLVER_THREADS"] == "10"
        assert environment["PATH"] == "/usr/bin", "the rest of the environment is passed through"

    def test_the_server_is_still_started_with_full_precision_arenas(self, threads) -> None:
        """Decision 20's arena rides the same environment, and GTOpen matches the exact string
        `"0"` - anything else is the quantized arena, silently."""
        environment = owed(threads, "server_environment")(10, base={})

        assert environment["SOLVER_COMPRESS"] == "0"

    def test_no_thread_count_is_refused_before_a_server_starts(self, threads) -> None:
        with pytest.raises(transport.SolveDriverError):
            owed(threads, "server_environment")(None, base={})

    @pytest.mark.parametrize("bad", [0, -4, True])
    def test_a_count_that_is_not_a_positive_whole_number_is_refused(self, threads, bad) -> None:
        with pytest.raises(transport.SolveDriverError):
            owed(threads, "server_environment")(bad, base={})

    def test_a_count_inherited_from_the_shell_is_not_an_explicit_count(self, threads) -> None:
        """A login shell exporting `SOLVER_THREADS=5` would otherwise make every solve look
        configured while running at whatever that shell said."""
        with pytest.raises(transport.SolveDriverError):
            owed(threads, "server_environment")(None, base={"SOLVER_THREADS": "5"})

    def test_the_explicit_count_overrides_one_inherited_from_the_shell(self, threads) -> None:
        environment = owed(threads, "server_environment")(10, base={"SOLVER_THREADS": "5"})

        assert environment["SOLVER_THREADS"] == "10"

    def test_every_script_that_starts_gto_server_builds_its_environment_through_the_guard(
        self,
    ) -> None:
        """Static, and the lowest rung that holds it: a file that launches `gto-server` and does
        not call `server_environment` builds the environment itself and can skip the count."""
        offenders = []
        for path in [*REPO_ROOT.glob("scripts/*.py"), *REPO_ROOT.glob("src/**/*.py")]:
            text = path.read_text(encoding="utf-8")
            if "Popen(" in text and "gto-server" in text and "server_environment(" not in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))

        assert offenders == []


# --------------------------------------------------------------------------- #
# The machine record is measured, not a constant
# --------------------------------------------------------------------------- #


class TestTheMachineRecordIsMeasured:
    """Criterion: every solve record carries the machine it ran on as measured. Today
    `MEASURING_MACHINE` is a hardcoded "Apple M4" string written into every object, so a rented
    box would record the wrong machine; a test fails on a constant in its place."""

    def test_the_m4_reads_as_itself_from_its_own_sysctl(self, machine) -> None:
        record = owed(machine, "measure_machine")(
            platform="Darwin",
            sysctl=sysctl_reader("darwin_apple_m4.sysctl.txt"),
            read_text=proc_reader({}),
        )

        assert record.cpu_model == "Apple M4"
        assert record.logical_processors == 10
        assert record.memory_bytes == 34359738368

    def test_a_linux_xeon_reads_as_a_xeon_from_its_proc_files(self, machine) -> None:
        record = owed(machine, "measure_machine")(
            platform="Linux", sysctl=no_sysctl, read_text=proc_reader(XEON_PROC)
        )

        assert record.cpu_model == "Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz"
        assert record.logical_processors == 4
        assert record.memory_bytes == MEMINFO_BYTES

    def test_a_graviton_with_no_model_name_line_is_still_counted_and_not_named_apple(
        self, machine
    ) -> None:
        """ARM `/proc/cpuinfo` has no `model name` line at all. A reader keyed on that line alone
        would blank the model or fall back to a default, and a default is the constant again."""
        record = owed(machine, "measure_machine")(
            platform="Linux", sysctl=no_sysctl, read_text=proc_reader(GRAVITON_PROC)
        )

        assert record.logical_processors == 4
        assert record.memory_bytes == MEMINFO_BYTES
        assert "Apple" not in record.cpu_model
        assert "0xd40" in record.cpu_model or "Neoverse" in record.cpu_model, (
            "the fixture's CPU part is 0xd40, Arm Neoverse V1; name it from what the file says"
            f" rather than a default, got {record.cpu_model!r}"
        )

    def test_a_machine_that_will_not_say_what_it_is_is_refused_rather_than_defaulted(
        self, machine
    ) -> None:
        with pytest.raises((ValueError, OSError, KeyError)):
            owed(machine, "measure_machine")(
                platform="Linux", sysctl=no_sysctl, read_text=proc_reader({})
            )

    def test_the_description_names_the_model_and_the_processor_count(self, machine) -> None:
        record = owed(machine, "measure_machine")(
            platform="Linux", sysctl=no_sysctl, read_text=proc_reader(XEON_PROC)
        )

        described = record.describe()
        assert record.cpu_model in described and "4" in described

    def test_the_hardcoded_machine_string_is_gone_from_every_writer(self) -> None:
        """`MEASURING_MACHINE` is the constant the contract names. Static on purpose: it is a
        name, and the only thing that proves a name unused is that nothing says it."""
        users = [
            str(path.relative_to(REPO_ROOT))
            for path in [*REPO_ROOT.glob("scripts/*.py"), *REPO_ROOT.glob("src/**/*.py")]
            if "MEASURING_MACHINE" in path.read_text(encoding="utf-8")
        ]

        assert users == []
        assert not hasattr(driver, "MEASURING_MACHINE")


# --------------------------------------------------------------------------- #
# The memory ceiling follows the machine
# --------------------------------------------------------------------------- #


class TestTheMemoryCeilingFollowsTheMachine:
    """Criterion: a test proves the ceiling follows the machine's reported memory.
    `THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR`: the frozen phase 16 test
    passed with any positive integer, so 12,026 MB hardcoded into the rented box's driver
    satisfied it."""

    @pytest.mark.parametrize("gib", [32, 64, 128, 192])
    def test_the_ceiling_is_the_ruled_fraction_of_the_memory_reported(self, machine, gib) -> None:
        ceiling = owed(machine, "memory_ceiling_bytes")

        assert ceiling(gib * GIB) == int(gib * GIB * driver.MEMORY_CEILING_FRACTION)

    def test_twice_the_memory_is_twice_the_ceiling(self, machine) -> None:
        ceiling = owed(machine, "memory_ceiling_bytes")

        assert ceiling(128 * GIB) == 2 * ceiling(64 * GIB)

    def test_a_machine_that_reports_no_memory_gets_the_stated_floor(self, machine) -> None:
        ceiling = owed(machine, "memory_ceiling_bytes")

        assert ceiling(None) == driver.FALLBACK_MEMORY_CEILING_BYTES

    def test_the_driver_s_ceiling_is_this_machine_s_memory_through_the_same_rule(
        self, machine
    ) -> None:
        """Read here through the C library the way the driver says it reads it, so the test
        measures this machine rather than repeating a number measured on another."""
        physical = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")

        assert driver.MEMORY_CEILING_BYTES == owed(machine, "memory_ceiling_bytes")(physical)


# --------------------------------------------------------------------------- #
# The engine is read back from the server, and a silent CPU fallback is discarded
# --------------------------------------------------------------------------- #


class TestTheEngineIsReadBackFromTheServer:
    """Criteria: every solve record carries the engine, read back from the server; a GPU run the
    server reports as not using the GPU is a silent CPU fallback and its timing is discarded.
    GTOpen's `/api/status` answers `gpu` (true while the solve ran on the card) and `gpu_note`
    (why not, on a fallback) - `crates/server/src/main.rs:142-163` and `:540-547`."""

    def test_a_status_on_the_card_reads_as_gpu(self, machine) -> None:
        assert owed(machine, "engine_from_status")({"state": "done", "gpu": True}) == "GPU"

    def test_a_status_off_the_card_reads_as_cpu(self, machine) -> None:
        assert owed(machine, "engine_from_status")({"state": "done", "gpu": False}) == "CPU"

    def test_a_status_without_the_field_is_refused_rather_than_read_as_cpu(self, machine) -> None:
        with pytest.raises(transport.SolveDriverError) as raised:
            owed(machine, "engine_from_status")({"state": "done"})

        assert "/api/status" in str(raised.value) and "gpu" in str(raised.value)

    def test_a_gpu_run_that_fell_back_to_the_cpu_is_refused(self, machine) -> None:
        status = {"state": "done", "gpu": False, "gpu_note": "GPU unavailable: out of memory"}

        with pytest.raises(transport.SolveDriverError) as raised:
            owed(machine, "check_engine")(status, "GPU")

        assert "GPU unavailable: out of memory" in str(raised.value)

    def test_a_gpu_run_on_the_card_is_accepted(self, machine) -> None:
        assert owed(machine, "check_engine")({"state": "done", "gpu": True}, "GPU") == "GPU"

    def test_a_cpu_run_on_the_cpu_is_accepted(self, machine) -> None:
        assert owed(machine, "check_engine")({"state": "done", "gpu": False}, "CPU") == "CPU"


# --------------------------------------------------------------------------- #
# What a solve record carries
# --------------------------------------------------------------------------- #


def an_outcome():
    return driver.SolveOutcome(
        label="srp-Kh7d2c",
        board="Kh7d2c",
        preflop_line="t6/d100/BB/BTN:raise@2.5,BB:call",
        outcome=driver.CONVERGED,
        exploit_pct_of_pot=0.283013340119407,
        iterations=340,
        wall_seconds=1677.4,
        arena_bytes=11978042234,
    )


class TestEverySolveRecordNamesWhereAndHowItRan:
    """Criterion: every solve record carries the machine as measured, the thread count, the
    engine and the arena storage, and peak resident memory per solve - no f32 solve on record
    has one."""

    def xeon(self, machine):
        return owed(machine, "measure_machine")(
            platform="Linux", sysctl=no_sysctl, read_text=proc_reader(XEON_PROC)
        )

    def test_the_record_carries_the_machine_it_was_handed_and_not_the_m4(self, machine) -> None:
        record = owed(machine, "solve_record")(
            an_outcome(),
            machine=self.xeon(machine),
            threads=4,
            engine="CPU",
            arena_storage="f32",
            peak_resident_bytes=30_000_000_000,
        )

        assert record["machine"]["cpu_model"] == "Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz"
        assert record["machine"]["logical_processors"] == 4
        assert "Apple" not in str(record)

    def test_the_record_carries_threads_engine_arena_and_peak_memory(self, machine) -> None:
        record = owed(machine, "solve_record")(
            an_outcome(),
            machine=self.xeon(machine),
            threads=4,
            engine="CPU",
            arena_storage="f32",
            peak_resident_bytes=30_000_000_000,
        )

        assert record["threads"] == 4
        assert record["engine"] == "CPU"
        assert record["arena_storage"] == "f32"
        assert record["peak_resident_bytes"] == 30_000_000_000
        assert record["iterations"] == 340
        assert record["wall_seconds"] == pytest.approx(1677.4)

    @pytest.mark.parametrize(
        "missing",
        [
            {"threads": None},
            {"threads": 0},
            {"engine": "cpu"},
            {"engine": ""},
            {"peak_resident_bytes": None},
            {"peak_resident_bytes": 0},
            {"arena_storage": ""},
        ],
    )
    def test_a_record_missing_a_measurement_is_refused(self, machine, missing) -> None:
        """A blank or a default in any of these is the constant problem again under another
        name: a timing whose thread count nobody wrote down is the record this phase exists to
        stop producing."""
        fields = {
            "machine": self.xeon(machine),
            "threads": 4,
            "engine": "CPU",
            "arena_storage": "f32",
            "peak_resident_bytes": 30_000_000_000,
            **missing,
        }

        with pytest.raises((ValueError, transport.SolveDriverError)):
            owed(machine, "solve_record")(an_outcome(), **fields)


# --------------------------------------------------------------------------- #
# The fixtures are what they say they are
# --------------------------------------------------------------------------- #


def test_the_captured_m4_listing_is_the_machine_the_contract_describes() -> None:
    """The contract's own figures: ten cores, four performance and six efficiency. If this file
    is ever re-captured on another machine the M4 tests above stop meaning what they say."""
    text = Path(FIXTURES / "darwin_apple_m4.sysctl.txt").read_text(encoding="utf-8")

    assert re.search(r"^hw\.perflevel0\.physicalcpu: 4$", text, re.MULTILINE)
    assert re.search(r"^hw\.perflevel1\.physicalcpu: 6$", text, re.MULTILINE)
    assert re.search(r"^hw\.ncpu: 10$", text, re.MULTILINE)
