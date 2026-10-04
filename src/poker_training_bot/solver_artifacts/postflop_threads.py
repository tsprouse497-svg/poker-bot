"""How many threads GTOpen solves with: the counts timed, the sweep's verdict, and the server env.

GTOpen's `init_rayon` (`crates/server/src/main.rs:2546-2563`) takes `SOLVER_THREADS` when it
parses as a whole number and otherwise `max(1, available_parallelism() / 2)`, on the comment that
hyperthreads hurt a memory-bound workload. The Apple M4 has no hyperthreads, so every solve phase
16 committed ran on five of its ten cores, and no record said so
(`GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`).

So every server is started through `server_environment`, which refuses to build an environment
without an explicit count, and the count is chosen per machine by a sweep: GTOpen's default and a
quarter, half, three quarters and all of the logical processors, rounded half up with repeats
dropped, each timed three times interleaved over a fixed 100 iterations, the median deciding. The
median rather than the mean, because one run that shared the machine is enough to move a mean -
the committed `9c8c7c` runs read 1.34 and 2.16 seconds per iteration on one configuration for
exactly that reason.
"""

from __future__ import annotations

import os
import re
import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from poker_training_bot.solver_artifacts.postflop_machine import MachineRecord
from poker_training_bot.solver_artifacts.postflop_transport import SolveDriverError

SOLVER_THREADS_VARIABLE = "SOLVER_THREADS"
SOLVER_COMPRESS_VARIABLE = "SOLVER_COMPRESS"
SOLVER_COMPRESS_FULL_PRECISION = "0"
"""GTOpen matches `SOLVER_COMPRESS` against the exact string `"0"` for full-precision arenas and
reads anything else, absence included, as the quantized arena. Decision 20 rules full precision,
so it rides the same environment the thread count does."""

ITERATIONS_PER_STRETCH = 100
REPEATS_PER_COUNT = 3
SWEEP_RECORD_SCHEMA_VERSION = 1


# --- Which counts are timed


def gtopen_default_threads(logical_processors: int) -> int:
    """What GTOpen picks with no `SOLVER_THREADS`: half the logical processors, rounded down,
    never below one."""
    return max(1, logical_processors // 2)


def _quarters_rounded_half_up(logical_processors: int, quarters: int) -> int:
    """`logical * quarters / 4` rounded half up, in integers: the contract's own M4 figures (3 from
    2.5, 8 from 7.5) rule out banker's rounding."""
    return (2 * logical_processors * quarters + 4) // 8


def thread_counts_to_time(logical_processors: int) -> tuple[int, ...]:
    """GTOpen's default and a quarter, half, three quarters and all of the machine, ascending."""
    if isinstance(logical_processors, bool) or logical_processors < 1:
        raise ValueError(f"a machine has at least one processor, got {logical_processors!r}")
    counts = {gtopen_default_threads(logical_processors)}
    for quarters in (1, 2, 3, 4):
        counts.add(max(1, _quarters_rounded_half_up(logical_processors, quarters)))
    return tuple(sorted(counts))


def interleaved_schedule(counts: Iterable[int]) -> tuple[int, ...]:
    """Every count once per round, three rounds: whatever else the machine does in one stretch
    lands on every count rather than on all three runs of one."""
    return tuple(counts) * REPEATS_PER_COUNT


# --- The verdict


@dataclass(frozen=True)
class SweepVerdict:
    chosen_threads: int
    medians: dict[int, float]
    spreads: dict[int, float]


def _check_interleaved(order: Sequence[int]) -> tuple[int, ...]:
    """The counts of one round, refusing runs that were not taken as `interleaved_schedule`
    lays them out: one run per count, or each count's runs back to back."""
    counts = tuple(dict.fromkeys(order))
    if len(order) != len(counts) * REPEATS_PER_COUNT:
        raise ValueError(
            f"{len(order)} runs over {len(counts)} thread counts; the sweep needs"
            f" {REPEATS_PER_COUNT} runs of every count, and one run per count is not enough"
        )
    if tuple(order) != interleaved_schedule(counts):
        raise ValueError(
            f"the runs were taken in the order {list(order)}, not interleaved round by round as"
            f" {list(interleaved_schedule(counts))}; runs of one count taken back to back share"
            " whatever else the machine was doing in that stretch"
        )
    return counts


def sweep_verdict(runs: Sequence[tuple[int, float]]) -> SweepVerdict:
    """The fastest median seconds per iteration wins; ties go to fewer threads."""
    _check_interleaved([count for count, _ in runs])
    by_count: dict[int, list[float]] = {}
    for count, seconds in runs:
        if isinstance(seconds, bool) or not isinstance(seconds, int | float) or seconds <= 0:
            raise ValueError(f"a run at {count} threads took {seconds!r} seconds per iteration")
        by_count.setdefault(count, []).append(float(seconds))
    medians = {count: statistics.median(times) for count, times in by_count.items()}
    spreads = {count: max(times) - min(times) for count, times in by_count.items()}
    chosen = min(medians, key=lambda count: (medians[count], count))
    return SweepVerdict(chosen_threads=chosen, medians=medians, spreads=spreads)


def sweep_record(
    machine: MachineRecord,
    runs: Sequence[tuple[int, float]],
    details: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """One machine's sweep, refusing runs whose counts are not the ones this machine times.

    `details` carries whatever each run measured beside its seconds per iteration - the load
    average and busiest process before it, its peak memory - one mapping per run, in run order."""
    counts = thread_counts_to_time(machine.logical_processors)
    timed = sorted({count for count, _ in runs})
    if tuple(timed) != counts:
        raise ValueError(
            f"the runs time {timed} threads and {machine.cpu_model} with"
            f" {machine.logical_processors} logical processors times {list(counts)}; a sweep is"
            " measured on the machine it describes and never carried from another"
        )
    if details is not None and len(details) != len(runs):
        raise ValueError(f"{len(details)} run details for {len(runs)} runs")
    verdict = sweep_verdict(runs)
    return {
        "machine": machine.to_document(),
        "counts": list(counts),
        "gtopen_default_threads": gtopen_default_threads(machine.logical_processors),
        "iterations_per_stretch": ITERATIONS_PER_STRETCH,
        "repeats_per_count": REPEATS_PER_COUNT,
        "chosen_threads": verdict.chosen_threads,
        "per_count": [
            {
                "threads": count,
                "median_seconds_per_iteration": verdict.medians[count],
                "spread_seconds_per_iteration": verdict.spreads[count],
            }
            for count in counts
        ],
        "runs": [
            {
                **(dict(details[position]) if details is not None else {}),
                "threads": count,
                "seconds_per_iteration": seconds,
            }
            for position, (count, seconds) in enumerate(runs)
        ],
    }


# --- The server's environment


def server_environment(
    threads: int | None, *, base: Mapping[str, str] | None = None
) -> dict[str, str]:
    """The environment a GTOpen server is started with: `base` (this process's own by default),
    with the thread count and the full-precision arena set explicitly.

    A missing count is refused even when `base` already carries one: a login shell exporting
    `SOLVER_THREADS` would otherwise make every solve look configured while running at whatever
    that shell said. An explicit count always replaces an inherited one."""
    if threads is not None and not isinstance(threads, int):
        raise SolveDriverError(f"the thread count must be a whole number, got {threads!r}")
    if threads is None or isinstance(threads, bool) or threads < 1:
        raise SolveDriverError(
            f"no explicit thread count ({threads!r}) for the GTOpen server. Without one it runs"
            " at half the machine's processors and nothing records it; pass the count this"
            " machine's sweep chose."
        )
    environment = dict(os.environ if base is None else base)
    environment[SOLVER_THREADS_VARIABLE] = str(threads)
    environment[SOLVER_COMPRESS_VARIABLE] = SOLVER_COMPRESS_FULL_PRECISION
    return environment


_PRINTED_THREADS = re.compile(r"^solver threads: (\d+)$", re.MULTILINE)


def check_printed_threads(server_output: str, threads: int) -> int:
    """The count the server printed at start, which must be the count it was given. GTOpen
    silently falls back to its default on a value it cannot parse, and only this line says so."""
    printed = _PRINTED_THREADS.findall(server_output)
    if printed != [str(threads)]:
        raise SolveDriverError(
            f"the server was given {threads} threads and printed {printed or 'no'} 'solver"
            " threads' line; refused rather than recorded at a count it may not be running"
        )
    return threads
