"""What a solve record says it ran on, read off the machine rather than written down.

Phase 16 wrote one hardcoded string, "Apple M4, 10 cores, 34.4 GB RAM, CPU engine", into every
object it solved. A rented box would have recorded the M4 under its own timings, which is the
mislabel the phase 21 contract forbids by name: a timing is only a measurement beside the machine
and the thread count it was taken at. So the machine is measured here, per run, from what the
operating system says about itself - `sysctl` on Darwin, `/proc/cpuinfo` and `/proc/meminfo` on
Linux - and a machine that will not say is refused rather than given a default, because a default
is the constant again under another name.

The readers are handed in. They are a hard external boundary, and handing them in is what lets a
test feed the M4's own captured `sysctl` text, or a Linux box's `/proc` files, without either
machine being present.

The solver build is read the same way: the commit and branch of the clone the server binary was
built in, from git rather than from a note, with a dirty clone refused.

The memory ceiling lives here too, because it is a fraction of the memory this module measures:
the driver publishes `MEMORY_CEILING_BYTES` through `memory_ceiling_bytes`, so the rule that turns
a machine's memory into a ceiling is one function a test can call on any figure.
"""

from __future__ import annotations

import os
import platform as platform_module
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from poker_training_bot.solver_artifacts.postflop_transport import SolveDriverError, answered

# --- The memory ceiling, as a rule over a machine's reported memory

MEMORY_CEILING_FRACTION = 0.40
"""A policy rather than a measurement, which is why it is what travels between machines. The arena
is faulted in lazily during the solve, so it is paid as resident memory alongside the tree, the
ranges and whatever else the box runs, and a ceiling near the RAM figure lets a machine swap.

**It was 0.35 and Taylor moved it to 0.40 on 2026-09-20, `frozen-into-data`, to admit the flop
campaign at full-precision arenas** (phase 16, decision 20). Quantized arenas cost about half as
much memory, and every arena figure recorded before that date was taken under them, so asking for
full precision roughly doubles the planned arena on the same tree. What moved is the policy rather
than the arithmetic: 0.35 was the number meant to travel to the rented box, so this loosens the
guard there too, which is a cost of the ruling rather than an oversight in it. Phase 21's decision
14 keeps it, and keeps the driver's over-reading of `arena_mb`, stating that margin in every
refusal instead."""

FALLBACK_MEMORY_CEILING_BYTES = 4096 * 1024 * 1024
"""Used only when a machine will not say how much memory it has. Deliberately small, and not
GTOpen's own 48,000 MB fallback - about 1.5x the RAM of the box it fell back on, where the same
solver's preflop side uses 2,000 MB, so 48,000 is an outlier rather than a ruling."""


def memory_ceiling_bytes(physical_bytes: int | None) -> int:
    """The largest planned arena a machine reporting `physical_bytes` of memory may solve.

    The ruled fraction of what it reports, or the stated floor when it reports nothing. A
    constant here would be one machine's ceiling wearing another's name."""
    if physical_bytes is None:
        return FALLBACK_MEMORY_CEILING_BYTES
    return int(physical_bytes * MEMORY_CEILING_FRACTION)


# --- The machine record

Sysctl = Callable[[str], str]
ReadText = Callable[[str], str]
RunGit = Callable[[list[str]], str]


@dataclass(frozen=True)
class MachineRecord:
    """One machine as it described itself. `logical_processors` is what the operating system
    counts, which on Linux is not necessarily what GTOpen may use: the server's own printed
    "solver threads" line is the cross-check, compared at every server start."""

    platform: str
    cpu_model: str
    logical_processors: int
    memory_bytes: int
    performance_cores: int | None = None
    efficiency_cores: int | None = None

    def describe(self) -> str:
        cores = f"{self.logical_processors} logical processors"
        if self.performance_cores is not None and self.efficiency_cores is not None:
            cores += f" ({self.performance_cores} performance, {self.efficiency_cores} efficiency)"
        return f"{self.cpu_model}, {cores}, {self.memory_bytes / 1e9:.1f} GB RAM, {self.platform}"

    def to_document(self) -> dict[str, object]:
        document: dict[str, object] = {
            "platform": self.platform,
            "cpu_model": self.cpu_model,
            "logical_processors": self.logical_processors,
            "memory_bytes": self.memory_bytes,
        }
        if self.performance_cores is not None:
            document["performance_cores"] = self.performance_cores
        if self.efficiency_cores is not None:
            document["efficiency_cores"] = self.efficiency_cores
        document["description"] = self.describe()
        return document


def _real_sysctl(key: str) -> str:
    completed = subprocess.run(  # noqa: S603 - a fixed system binary with one fixed oid
        ["/usr/sbin/sysctl", "-n", key], capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def _real_read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _optional_int(sysctl: Sysctl, key: str) -> int | None:
    """A perf-level count, present on Apple silicon and absent on an Intel Mac."""
    try:
        return int(sysctl(key))
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError):
        return None


def _darwin(sysctl: Sysctl) -> MachineRecord:
    return MachineRecord(
        platform="Darwin",
        cpu_model=sysctl("machdep.cpu.brand_string").strip(),
        logical_processors=int(sysctl("hw.ncpu")),
        memory_bytes=int(sysctl("hw.memsize")),
        performance_cores=_optional_int(sysctl, "hw.perflevel0.physicalcpu"),
        efficiency_cores=_optional_int(sysctl, "hw.perflevel1.physicalcpu"),
    )


ARM_PARTS: Mapping[tuple[str, str], str] = {
    ("0x41", "0xd0c"): "Arm Neoverse N1",
    ("0x41", "0xd40"): "Arm Neoverse V1",
    ("0x41", "0xd49"): "Arm Neoverse N2",
    ("0x41", "0xd4f"): "Arm Neoverse V2",
    ("0x41", "0xd84"): "Arm Neoverse V3",
}
"""ARM `/proc/cpuinfo` names no model: it gives an implementer and a part number. These are Arm's
own part numbers for the Neoverse cores AWS's Graviton generations use. A part not listed here is
still named, by its numbers, rather than given a guessed name."""


def _cpuinfo_fields(text: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            if current:
                blocks.append(current)
                current = {}
            continue
        key, separator, value = line.partition(":")
        if separator:
            current[key.strip()] = value.strip()
    if current:
        blocks.append(current)
    return blocks


def _linux_cpu_model(processors: list[dict[str, str]]) -> str:
    first = processors[0]
    if first.get("model name"):
        return first["model name"]
    implementer, part = first.get("CPU implementer"), first.get("CPU part")
    if implementer and part:
        known = ARM_PARTS.get((implementer.lower(), part.lower()))
        numbers = f"implementer {implementer}, part {part}"
        return f"{known} ({numbers})" if known else f"ARM CPU, {numbers}"
    raise ValueError("/proc/cpuinfo names no model name and no CPU implementer and part")


def _linux_memory_bytes(meminfo: str) -> int:
    for line in meminfo.splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "MemTotal":
            number, _, unit = value.strip().partition(" ")
            if unit.strip() != "kB":
                raise ValueError(f"/proc/meminfo MemTotal has unit {unit!r}, expected kB")
            return int(number) * 1024  # the kernel's "kB" is kibibytes
    raise ValueError("/proc/meminfo has no MemTotal line")


def _linux(read_text: ReadText) -> MachineRecord:
    processors = [
        block for block in _cpuinfo_fields(read_text("/proc/cpuinfo")) if "processor" in block
    ]
    if not processors:
        raise ValueError("/proc/cpuinfo lists no processor")
    return MachineRecord(
        platform="Linux",
        cpu_model=_linux_cpu_model(processors),
        logical_processors=len(processors),
        memory_bytes=_linux_memory_bytes(read_text("/proc/meminfo")),
    )


def measure_machine(
    *,
    platform: str | None = None,
    sysctl: Sysctl = _real_sysctl,
    read_text: ReadText = _real_read_text,
) -> MachineRecord:
    """This machine as its operating system describes it, or a refusal. Nothing is defaulted."""
    system = platform or platform_module.system()
    if system == "Darwin":
        record = _darwin(sysctl)
    elif system == "Linux":
        record = _linux(read_text)
    else:
        raise ValueError(f"no reader for platform {system!r}; refused rather than defaulted")
    if not record.cpu_model or record.logical_processors < 1 or record.memory_bytes < 1:
        raise ValueError(f"the machine described itself incompletely: {record!r}")
    return record


def physical_memory_bytes() -> int | None:
    """Total RAM through the C library, which Linux and Darwin both answer, so the driver's ceiling
    is read on whichever box imports it without a platform test."""
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError):
        return None
    if not isinstance(pages, int) or not isinstance(page_size, int):
        return None
    total = pages * page_size
    return total if total > 0 else None


# --- The engine, read back from the server

CPU_ENGINE = "CPU"
GPU_ENGINE = "GPU"
ENGINES = (CPU_ENGINE, GPU_ENGINE)


def engine_from_status(status: Mapping[str, object]) -> str:
    """Which engine the server says ran the solve. `/api/status` answers `gpu`, true while the
    solve ran on the card; an answer without it is refused rather than read as the CPU."""
    gpu = answered(status, "/api/status", "gpu")
    if not isinstance(gpu, bool):
        raise SolveDriverError(f"/api/status answered gpu={gpu!r}, which is not true or false")
    return GPU_ENGINE if gpu else CPU_ENGINE


def check_engine(status: Mapping[str, object], wanted: str) -> str:
    """`engine_from_status`, refusing a run on any engine but the one asked for. A GPU run the
    server reports as off the card is a silent CPU fallback, and its timing is discarded."""
    found = engine_from_status(status)
    if found != wanted:
        note = status.get("gpu_note") or "the server gave no reason"
        raise SolveDriverError(
            f"the solve was asked to run on the {wanted} and /api/status reports the {found}"
            f" ({note}). Its timing describes another engine and is discarded."
        )
    return found


# --- The solver build, read off the clone the binary was built in

COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
"""A full commit as `git rev-parse HEAD` prints it. An abbreviation is refused rather than
expanded, because a short hash is a guess about which commit it means."""


def real_run_git(repository: Path) -> RunGit:
    """`git -C <repository>`, returning its standard output. A hard external boundary, handed in
    to `read_solver_build` so a test can feed a clone's answers without the clone."""

    def run(args: list[str]) -> str:
        completed = subprocess.run(  # noqa: S603 - git, in a repository named on the command line
            ["git", "-C", str(repository), *args], capture_output=True, text=True, check=False
        )
        if completed.returncode != 0:
            raise ValueError(
                f"git {' '.join(args)} in {repository} failed: {completed.stderr.strip()}"
            )
        return completed.stdout

    return run


def solver_repository(binary: Path) -> Path:
    """The clone a server binary was built in: `<clone>/target/release/gto-server`. It is also the
    server's working directory, which is where GTOpen reads its files and writes its saves."""
    return binary.resolve().parents[2]


def recorded_repository(repository: Path, home: Path | None = None) -> str:
    """The clone as a record names it: home-relative when it sits under the home directory, so a
    committed record carries no username and reads the same on a rented box."""
    home = Path.home() if home is None else home
    for base in dict.fromkeys((home, home.resolve())):  # the resolved form, for a symlinked home
        if repository.is_absolute() and repository.is_relative_to(base):
            return "~/" + repository.relative_to(base).as_posix()
    return str(repository)


BUILD_INPUTS = ("crates", "Cargo.lock", "Cargo.toml")
"""What GTOpen compiles from, as git tracks it: the two crates, the lock and the workspace manifest
that carries the release profile. Nothing else in the clone is compiled in."""


def check_binary_is_current(binary: Path, run_git: RunGit | None = None) -> None:
    """Refuse a server binary that file times say was not built from the clone's checked-out tree.

    Three refusals: (a) no binary; (b) a binary older than HEAD's commit time, built before the
    commit existed; (c) a tracked build input newer than the binary, which is what a checkout of
    another commit leaves, since git rewrites every file it changes and a clean tree alone cannot
    see it. It compares times and never the compiled bytes, so it does not catch a binary copied in
    from elsewhere or given a fresh time, inputs whose times were set back, or a build with other
    flags, features or toolchain. The clean-tree check is `read_solver_build`'s."""
    if not binary.is_file():
        raise ValueError(f"{binary} is not a file; run `cargo build --release` in its clone")
    repository = solver_repository(binary)
    run_git = run_git or real_run_git(repository)
    rebuild = (
        f" Run `cargo build --release` in {repository}; if cargo finds nothing to do, force a"
        " relink with `cargo clean --release -p server` first."
    )
    built_at = binary.resolve().stat().st_mtime
    committed_at = int(run_git(["log", "-1", "--format=%ct"]).strip())
    if built_at < committed_at:
        raise ValueError(f"{binary} was built before {repository}'s HEAD commit." + rebuild)
    tracked = run_git(["ls-files", "-z", *BUILD_INPUTS]).split("\0")
    newer = [name for name in tracked if name and _mtime(repository / name) > built_at]
    if newer:
        raise ValueError(
            f"{len(newer)} tracked build input(s) in {repository} changed after {binary} was"
            f" built, as a checkout of another commit leaves them, e.g. {newer[0]}." + rebuild
        )


def _mtime(path: Path) -> float:
    """A tracked file's time; one missing from the tree is a dirty tree, refused elsewhere."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return float("-inf")


def solver_build_for(binary: Path, run_git: RunGit | None = None) -> dict[str, str]:
    """The build a run on `binary` records, after `check_binary_is_current` accepts the binary."""
    repository = solver_repository(binary)
    run_git = run_git or real_run_git(repository)
    check_binary_is_current(binary, run_git)
    return read_solver_build(repository, run_git)


def read_solver_build(repository: Path, run_git: RunGit | None = None) -> dict[str, str]:
    """Which GTOpen a solve ran: the clone's repository, branch and commit, as git says.

    Two trees exist since decision 17 - the patched clone every solve runs and the untouched
    reference beside it - so a record that does not name its build cannot say which tree it
    solved. A dirty tree is refused: a binary built from uncommitted changes is not the commit it
    would name. A detached head is refused too, because "HEAD" is not a branch anyone can find."""
    run_git = run_git or real_run_git(repository)
    status = run_git(["status", "--porcelain", "--untracked-files=no"])
    if status.strip():
        raise ValueError(
            f"the solver clone {repository} has uncommitted changes, so a binary built there is"
            f" not the commit it would name:\n{status.rstrip()}"
        )
    commit = run_git(["rev-parse", "HEAD"]).strip()
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    if branch == "HEAD":
        raise ValueError(f"the solver clone {repository} is on a detached head, not a branch")
    return check_solver_build(
        {"repository": recorded_repository(repository), "branch": branch, "commit": commit}
    )


def check_solver_build(build: object) -> dict[str, str]:
    """The build a solve record carries, refused when any part of it is missing."""
    if not isinstance(build, Mapping):
        raise ValueError(f"a solve record needs the solver build it ran on, got {build!r}")
    for name in ("repository", "branch"):
        value = build.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"a solve record needs the solver build's {name}, got {value!r}")
    commit = build.get("commit")
    if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
        raise ValueError(
            f"a solve record needs the solver build's commit as 40 lowercase hex, got {commit!r}"
        )
    return {"repository": build["repository"], "branch": build["branch"], "commit": commit}


# --- What every solve record carries


def _positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"a solve record needs {name} as a positive whole number, got {value!r}")
    return value


def solve_record(
    outcome,
    *,
    machine: MachineRecord,
    threads: int,
    engine: str,
    arena_storage: str,
    peak_resident_bytes: int,
    solver_build: Mapping[str, str],
) -> dict[str, object]:
    """One solve as measured, with where, how and on which solver build it ran. Every field is
    required and none has a default: a timing whose thread count or build nobody wrote down is the
    record this exists to stop."""
    if not isinstance(machine, MachineRecord):
        raise ValueError(f"a solve record needs a measured machine, got {machine!r}")
    if engine not in ENGINES:
        raise ValueError(f"engine must be one of {ENGINES} as read back, got {engine!r}")
    if not isinstance(arena_storage, str) or not arena_storage:
        raise ValueError(f"a solve record needs the arena storage read back, got {arena_storage!r}")
    build = check_solver_build(solver_build)
    return {
        "label": outcome.label,
        "board": outcome.board,
        "preflop_line": outcome.preflop_line,
        "outcome": outcome.outcome,
        "exploit_pct_of_pot": outcome.exploit_pct_of_pot,
        "iterations": outcome.iterations,
        "wall_seconds": outcome.wall_seconds,
        "arena_bytes": outcome.arena_bytes,
        "machine": machine.to_document(),
        "threads": _positive_int("threads", threads),
        "engine": engine,
        "arena_storage": arena_storage,
        "peak_resident_bytes": _positive_int("peak_resident_bytes", peak_resident_bytes),
        "solver_build": build,
    }
