"""Time GTOpen at every thread count this machine owes, and pick the fastest. Offline, never gated.

**This script must never be registered in `COMMANDS` in `scripts/run_verify.py`.** It starts the
solver, and the gate passes with no GTOpen, no network and no Rust toolchain.

Phase 21's first criterion: GTOpen takes half the logical processors unless `SOLVER_THREADS` says
otherwise, so every solve phase 16 committed ran on five of the M4's ten cores and no record said
so. This times the counts `postflop_threads.thread_counts_to_time` names for the machine it runs
on - GTOpen's default and a quarter, half, three quarters and all of the logical processors - three
times each, interleaved round by round, as a fixed stretch of 100 iterations of one committed
cell's configuration unchanged. The median decides; every run's seconds per iteration and the
spread are written down.

**One stretch is one fresh server.** The server never returns freed pages and a process carrying a
large high-water mark measured about 1.6x slower per iteration on the identical config, so each run
starts its own server, builds the tree, solves 100 iterations and is stopped. Seconds per iteration
is the server's own `elapsed_secs` over the 100 iterations, which times the solve loop alone and
not this script's polling; the client's wall clock and the tree build are recorded beside it.

**The machine must be doing nothing else, and the record says whether it was.** Before every run
the one-minute load average and the busiest processes are recorded as read. Nothing here hides a
busy run or repeats it: the interleaving and the median are what absorb one.

**The configuration is the committed one.** The board defaults to `Kh7d2c`, the flop every rented
candidate is timed on, on the committed button-open line with `solve_config.json`'s menu, and the
ranges posted are re-derived from the committed export and checked against the ranges
`solve_config.json` records before any server starts. The stopping target is posted at zero so the
100-iteration cap alone ends the stretch; nothing else of the solve body moves.

Usage:

    uv run python scripts/measure_postflop_thread_sweep.py
    uv run python scripts/measure_postflop_thread_sweep.py --smoke   # one short run, writes nothing
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from solve_postflop_sample import (  # noqa: E402
    DEFAULT_SERVER,
    SERVER_HELP,
    SOLVE_CONFIG_PATH,
    ArenaVerifiedTransport,
    Server,
    conditional_ranges,
    describe_build,
    preflop_line_for,
    range_text,
    refuse_a_foreign_server,
    run_solver_build,
)

from poker_training_bot.solver_artifacts.postflop_artifact import POSTFLOP_DIR  # noqa: E402
from poker_training_bot.solver_artifacts.postflop_machine import (  # noqa: E402
    CPU_ENGINE,
    MachineRecord,
    check_engine,
    measure_machine,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (  # noqa: E402
    CHECK_EVERY_ITERATIONS,
    RULED_ARENA_STORAGE,
    SolvePlan,
    check_memory_ceiling,
    describe_memory_ceiling,
    plan_refusals,
    solve_config_document,
    spot_body,
)
from poker_training_bot.solver_artifacts.postflop_threads import (  # noqa: E402
    ITERATIONS_PER_STRETCH,
    SWEEP_RECORD_SCHEMA_VERSION,
    interleaved_schedule,
    sweep_record,
    thread_counts_to_time,
)
from poker_training_bot.solver_artifacts.postflop_transport import (  # noqa: E402
    SolveDriverError,
    answered,
    arena_bytes,
    http_transport,
    numeric,
)

DEFAULT_OUTPUT = POSTFLOP_DIR / "campaign" / "thread_sweep.json"
DEFAULT_BOARD = "Kh7d2c"
POLL_SECONDS = 0.5
MAX_ATTEMPTS_PER_SLOT = 2
SMOKE_ITERATIONS = 20


def load_average() -> float:
    """The one-minute load average as the operating system reports it."""
    if sys.platform == "darwin":
        text = subprocess.run(  # noqa: S603 - fixed system binary
            ["/usr/sbin/sysctl", "-n", "vm.loadavg"], capture_output=True, text=True, check=True
        ).stdout
        return float(text.strip().strip("{}").split()[0])
    return float(Path("/proc/loadavg").read_text(encoding="utf-8").split()[0])


def busiest_processes(count: int = 3) -> list[dict[str, Any]]:
    """The processes using the most CPU right now, as `ps` reports them, leaving out this script
    and the `uv` that launched it, whose start-up work would otherwise head every list."""
    lines = subprocess.run(  # noqa: S603 - fixed system binary
        ["/bin/ps", "-Aceo", "pcpu=,pid=,comm="], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    own = {os.getpid(), os.getppid()}
    rows = []
    for line in lines:
        parts = line.split(None, 2)
        if len(parts) == 3 and int(parts[1]) not in own:
            rows.append({"cpu_pct": float(parts[0]), "pid": int(parts[1]), "command": parts[2]})
    rows.sort(key=lambda row: row["cpu_pct"], reverse=True)
    return rows[:count]


POWER_EVENT_TYPES = ("Sleep", "Wake", "DarkWake", "ThermalEvent")
"""`pmset -g log` event types that mean a stretch did not run on an awake, unthrottled machine.
A run that overlaps one is discarded and its slot run again, never kept."""


def power_events(since: str, until: str) -> list[str]:
    """Sleep, wake and thermal lines `pmset -g log` recorded between two local timestamps
    (`YYYY-MM-DD HH:MM:SS`), and every line mentioning thermal, whatever its type. Darwin only;
    elsewhere there is no such log and the list is empty."""
    if sys.platform != "darwin":
        return []
    text = subprocess.run(  # noqa: S603 - fixed system binary
        ["/usr/bin/pmset", "-g", "log"], capture_output=True, text=True, check=True
    ).stdout
    events = []
    for line in text.splitlines():
        stamp = line[:19]
        if not (since <= stamp <= until):
            continue
        kind = line[26:].split(None, 1)[0] if len(line) > 26 else ""
        if kind in POWER_EVENT_TYPES or "thermal" in line.lower():
            events.append(" ".join(line.split())[:300])
    return events


def thermal_state() -> str:
    """`pmset -g therm` as printed: the CPU speed limit, if macOS has set one."""
    if sys.platform != "darwin":
        return ""
    return subprocess.run(  # noqa: S603 - fixed system binary
        ["/usr/bin/pmset", "-g", "therm"], capture_output=True, text=True, check=True
    ).stdout.strip()


def committed_plan(board: str) -> SolvePlan:
    """The committed button-open line on `board`, its ranges re-derived and held against the
    ranges `solve_config.json` records, so the stretch is the committed configuration unchanged."""
    oop, ip = conditional_ranges()
    committed = json.loads(SOLVE_CONFIG_PATH.read_text(encoding="utf-8"))
    if committed["ranges"] != {"oop_bb_call": oop, "ip_btn_open": ip}:
        raise SystemExit(
            "the ranges re-derived from the committed export are not the ranges solve_config.json"
            " records, so a stretch on them would not be the committed configuration"
        )
    line = preflop_line_for("BB")
    plan = SolvePlan(
        label=f"thread-sweep-{board}",
        board=board,
        preflop_line=line.rendered,
        range_oop=range_text(oop),
        range_ip=range_text(ip),
        starting_pot=line.pot_bb,
        effective_stack=line.effective_stack_bb,
        config=solve_config_document(),
    )
    refusals = plan_refusals(plan)
    if refusals:
        raise SystemExit("; ".join(refusals))
    return plan


def one_stretch(
    plan: SolvePlan,
    threads: int,
    iterations: int,
    binary: Path,
    log_dir: Path,
    position: int,
    solver_build: dict[str, str],
) -> dict[str, Any]:
    """One fresh server at `threads`, one tree, `iterations` iterations, stopped."""
    before = {
        "load_average_1m_before": load_average(),
        "busiest_processes_before": busiest_processes(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "thermal_state_before": thermal_state(),
    }
    since = time.strftime("%Y-%m-%d %H:%M:%S")
    server = Server(binary, log_dir, threads, solver_build)
    server.start(f"sweep-{position:02d}-{threads}t")
    try:
        transport = ArenaVerifiedTransport(http_transport(), RULED_ARENA_STORAGE)
        status = transport("/api/status", None)
        if str(answered(status, "/api/status", "state")) == "running":
            raise SolveDriverError("a fresh server reported a running solve")
        build_started = time.monotonic()
        built = transport("/api/spot", spot_body(plan))
        build_seconds = time.monotonic() - build_started
        planned = arena_bytes(numeric(built, "/api/spot", "arena_mb"))
        check_memory_ceiling(planned)
        solve_started = time.monotonic()
        transport(
            "/api/solve",
            {
                "max_iterations": iterations,
                "target_exploit_pct": 0.0,
                "check_every": CHECK_EVERY_ITERATIONS,
            },
        )
        while True:
            time.sleep(POLL_SECONDS)
            status = transport("/api/status", None)
            if str(answered(status, "/api/status", "state")) != "running":
                break
        client_seconds = time.monotonic() - solve_started
        state = str(answered(status, "/api/status", "state"))
        done = int(numeric(status, "/api/status", "iteration"))
        if state != "done" or done != iterations:
            raise SolveDriverError(
                f"the stretch ended in state {state!r} at iteration {done}, not done at"
                f" {iterations}; its timing is not a stretch of {iterations}"
            )
        engine = check_engine(status, CPU_ENGINE)
        elapsed = numeric(status, "/api/status", "elapsed_secs")
    finally:
        server.stop()
    events = power_events(since, time.strftime("%Y-%m-%d %H:%M:%S"))
    return {
        **before,
        "thermal_state_after": thermal_state(),
        "power_events_during": events,
        "valid": not events,
        "server_elapsed_seconds": elapsed,
        "client_wall_seconds": client_seconds,
        "tree_build_seconds": build_seconds,
        "iterations": done,
        "exploit_pct_of_pot_at_end": numeric(status, "/api/status", "exploit_pct"),
        "engine": engine,
        "arena_storage": transport.arena(),
        "planned_arena_bytes": planned,
        "peak_resident_bytes": server.peak_resident_bytes,
        "server_log": str(server.log_path),
    }


MACHINE_IDENTITY = ("platform", "cpu_model", "logical_processors", "memory_bytes")
"""What makes two sweep records the same machine. Two rented boxes of one instance type read
alike and are one machine here, which is what a sweep per machine type means."""


def merged_sweep_document(output: Path, record: dict[str, Any]) -> dict[str, Any]:
    """The sweep file with this machine's record put in, replacing only an earlier record of the
    same machine, so a rented box's sweep keeps the Mac's and every other machine's."""
    machines: list[dict[str, Any]] = []
    if output.is_file():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing.get("record_schema_version") != SWEEP_RECORD_SCHEMA_VERSION:
            raise SystemExit(
                f"{output} is schema {existing.get('record_schema_version')!r}, not"
                f" {SWEEP_RECORD_SCHEMA_VERSION}; refused rather than merged"
            )
        machines = list(existing.get("machines", []))
    identity = tuple(record["machine"][key] for key in MACHINE_IDENTITY)
    kept = [
        entry
        for entry in machines
        if tuple(entry["machine"].get(key) for key in MACHINE_IDENTITY) != identity
    ]
    if len(kept) != len(machines):
        print(
            f"replacing          the earlier sweep of {record['machine']['cpu_model']}"
            f" ({record['machine']['logical_processors']} logical processors) in {output};"
            f" {len(kept)} other machine(s) kept"
        )
    return {"record_schema_version": SWEEP_RECORD_SCHEMA_VERSION, "machines": [*kept, record]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", default=DEFAULT_BOARD)
    parser.add_argument("--server", default=str(DEFAULT_SERVER), help=SERVER_HELP)
    parser.add_argument("--log-dir", default=str(Path.home() / ".cache" / "poker-bot-solves"))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--progress",
        default=None,
        metavar="FILE",
        help="append each finished run here as one JSON line",
    )
    parser.add_argument(
        "--note", default=None, help="what the record should say about the sweep's conditions"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help=f"one {SMOKE_ITERATIONS}-iteration run, most threads; writes nothing",
    )
    args = parser.parse_args(argv)

    machine: MachineRecord = measure_machine()
    solver_build = run_solver_build(Path(args.server))
    counts = thread_counts_to_time(machine.logical_processors)
    plan = committed_plan(args.board)
    schedule = (max(counts),) if args.smoke else interleaved_schedule(counts)
    iterations = SMOKE_ITERATIONS if args.smoke else ITERATIONS_PER_STRETCH
    print(f"machine            {machine.describe()}")
    print(f"solver build       {describe_build(solver_build)}")
    print(f"memory ceiling     {describe_memory_ceiling()}")
    print(f"board              {plan.board} on {plan.preflop_line}, solve_config.json unchanged")
    print(f"counts             {list(counts)}, schedule {list(schedule)}")
    print(
        f"stretch            {iterations} iterations, exploitability checked every"
        f" {CHECK_EVERY_ITERATIONS}"
    )
    refuse_a_foreign_server()

    runs: list[tuple[int, float]] = []
    details: list[dict[str, Any]] = []
    discarded: list[dict[str, Any]] = []
    for position, threads in enumerate(schedule):
        for attempt in range(1, MAX_ATTEMPTS_PER_SLOT + 1):
            detail = one_stretch(
                plan,
                threads,
                iterations,
                Path(args.server),
                Path(args.log_dir),
                position,
                solver_build,
            )
            detail["attempt"] = attempt
            if detail["valid"]:
                break
            discarded.append({"position": position, "threads": threads, **detail})
            print(
                f"run {position + 1:2d} attempt {attempt} DISCARDED: a sleep, wake or thermal"
                f" event during it: {detail['power_events_during']}",
                flush=True,
            )
        else:
            raise SystemExit(
                f"slot {position + 1} hit a power event on {MAX_ATTEMPTS_PER_SLOT} attempts; the"
                " machine is not awake and quiet enough for a sweep, and nothing is written"
            )
        seconds = detail["server_elapsed_seconds"] / iterations
        runs.append((threads, seconds))
        details.append(detail)
        print(
            f"run {position + 1:2d}/{len(schedule)}  {threads:3d} threads  {seconds:.4f} s/it"
            f"  load {detail['load_average_1m_before']:.2f}"
            f"  busiest {detail['busiest_processes_before'][0]['command']}"
            f" {detail['busiest_processes_before'][0]['cpu_pct']:.0f}%"
            f"  peak {detail['peak_resident_bytes'] / 1e9:.2f} GB",
            flush=True,
        )
        if args.progress:
            with Path(args.progress).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"threads": threads, "seconds": seconds, **detail}) + "\n")

    if args.smoke:
        print("smoke run: nothing written")
        return 0
    record = sweep_record(machine, runs, details)
    record["solver_build"] = solver_build
    record["board"] = plan.board
    record["preflop_line"] = plan.preflop_line
    record["configuration"] = str(SOLVE_CONFIG_PATH.relative_to(REPO_ROOT))
    record["seconds_per_iteration_is"] = (
        "the server's own elapsed_secs at the end of the stretch divided by its iterations: the"
        " solve loop alone, exploitability checks included, tree build and polling excluded"
    )
    record["discarded_runs"] = discarded
    if args.note:
        record["conditions_note"] = args.note
    record["load_average_note"] = (
        "load_average_1m_before is the one-minute load average as read just before each run. It"
        " decays over minutes, so after the first run it still carries the previous stretch's own"
        " server; busiest_processes_before is the reading of what else was running"
    )
    output = Path(args.output)
    document = merged_sweep_document(output, record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    for row in record["per_count"]:
        print(
            f"{row['threads']:3d} threads  median {row['median_seconds_per_iteration']:.4f}"
            f"  spread {row['spread_seconds_per_iteration']:.4f} s/it"
        )
    print(f"chosen             {record['chosen_threads']} threads")
    print(f"wrote              {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
