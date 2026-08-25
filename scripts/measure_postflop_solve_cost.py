"""Measure what one postflop solve costs in GTOpen: wall clock, and peak resident memory.

Never run by the gate, for the same reason `scripts/extract_gtopen_preflop.py` is not: it needs
a running GTOpen server, and the gate must pass on a machine with no GTOpen, no Rust toolchain
and no network. It writes a report a human reads, commits no data, registers no command ID.

Five calls do the measurement:

    GET  /api/status   refuse to start if another client is mid-solve
    POST /api/spot     build the tree; returns node counts and the arena estimate
    POST /api/solve    start the solve in the background; returns immediately
    GET  /api/status   poll until the state leaves "running", under our own watchdog
    POST /api/node     the root action menu, so a row proves which betting tree was solved

The Mac this runs on is not the machine that will do the real solve, so a wall-clock total
answers nothing alone. Every row carries per-unit costs beside the hardware they were taken on,
because those are what rescale. Peak resident memory is a separate axis rather than a footnote:
a solve that exceeds a box's RAM fails, it does not slow.

Four hazards shape the code.

`allin_threshold` is a PERCENT here and a FRACTION in (0,1] in the preflop engine, whose
committed config uses 0.67. A fraction posted here is accepted silently, means 0.85%, and
replaces every configured bet size with a jam: measured live, 85 builds 145,245 nodes with a
Check/Bet-75% menu and 0.85 builds 31,761 with Check/All-in. Nothing in the response says which
you got, so `guard_allin_threshold` refuses anything below 1.0.

The server's own "tree too large" guard cannot be relied on here, and the ceiling this script
keeps is not a nice-to-have but the only guard that exists. `mem_cap_mb()` reads `/proc/meminfo`,
gets an error on Darwin, and falls through to a flat 48,000 MB constant - about 1.5x this
machine's physical RAM - with no `SOLVER_MEM_MB` set in the running server's environment. The
gate it feeds compares only `arena_bytes_for(storage)` and counts no tree nodes, children or
actions at all, and the mid-build `node_budget` derived from that cap works out near 3.6e8 nodes,
over 21 GB of tree structure before a single arena byte. There is also no abort path for a build:
`/api/stop` reaches a running solve only. So the only safe order is build, read `arena_mb`,
refuse or proceed, stepping sizes up rather than launching an arbitrary config. `--build-only` is
that step, and its rows are a first-class group in the report.

`/api/spot` unconditionally drops whatever solve was there. This assumes it is the server's only
client and refuses to start against a running one.

`done` does not mean converged; it fires on either stopping condition. Every row reads
`exploit_pct` back and classifies itself, and only a row that reached its target is marked usable
for a mean - a cap-bound or watchdog-stopped row's wall clock is a floor, not a cost.

The transport lives in `SolverClient` alone; nothing else here speaks HTTP.

Usage:

    uv run python scripts/measure_postflop_solve_cost.py --preset smoke
    uv run python scripts/measure_postflop_solve_cost.py --preset smoke --build-only
    uv run python scripts/measure_postflop_solve_cost.py --spot-json spots/srp.json \\
        --label flop-srp-two-tone --target 0.3 --deadline 3600
    uv run python scripts/measure_postflop_solve_cost.py --preset smoke --determinism
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

BASE_URL = "http://127.0.0.1:3737"
GTOPEN_ROOT = Path.home() / "projects" / "gtopen"
REPORT_PATH = REPO_ROOT / "reports" / "active" / "latest_postflop_solve_cost.txt"
SERVER_PROCESS = "gto-server"

# Every row is rendered for a human and read back by machine from this one line, so the report
# is its own database. Regenerating from parsed rows is what lets a later run recompute the
# group aggregate rather than append one that was true when written and false afterwards.
ROW_MARKER = "Row data: "
APPENDIX_MARKER = "Appendix data: "
REF_PREFIX = "ref:"
# A run holds two preflop lines and two bet menus but dozens of rows, so a range string written
# into every row is the same 1.8 KB copied dozens of times, and that duplication alone was 44%
# of a report that then failed the 300 KB size gate. These fields are emitted once in an
# appendix and referenced by a hash OF THEMSELVES, so nothing is lost: the reference still
# proves which range and which menu a row was measured on, which is what the copy was for.
INTERN_PATHS = (
    ("config", "range_oop"),
    ("config", "range_ip"),
    ("config", "oop"),
    ("config", "ip"),
    ("menu",),
    ("solver",),
    ("machine",),
)
GROUPS = ("build", "solve", "determinism")
GROUP_TITLES = {
    "build": "Builds (tree geometry and arena, no solve)",
    "solve": "Solves (measured cost)",
    "determinism": "Determinism (one config solved twice and diffed)",
}

MIN_ALLIN_THRESHOLD_PCT = 1.0
# A third of physical RAM, deliberately low. The arena is faulted in lazily during the solve, so
# it is paid as resident memory alongside the tree, the ranges, and whatever else the box is
# running, and a ceiling near the RAM figure is a ceiling that lets the machine swap. Raising it
# is a decision somebody takes with --arena-ceiling-mb, in the open. For scale: the postflop
# server's own fallback for the same missing /proc/meminfo is 48,000 MB, while the preflop side's
# fallback for the identical situation is 2,000 MB - so 48,000 is the outlier, not a ruling.
ARENA_CEILING_FRACTION = 0.35
FALLBACK_ARENA_CEILING_MB = 4096.0
MAX_CURVE_POINTS = 200
REFERENCE_SOLVE = {"max_iterations": 2000, "target_exploit_pct": 0.3, "check_every": 20}

OUTCOME_CONVERGED = "converged-to-target"
NOT_USABLE = {
    "hit-iteration-cap": "the cap stopped it short of the target, so its wall clock is a floor",
    "stopped-by-watchdog": "the watchdog stopped it, so its wall clock is just the deadline",
    "solver-panic": "the solver died, so nothing in the row is a cost",
    "stopped-without-either-condition": "it ended on neither condition, so something else moved "
    "the session",
}


# ---------------------------------------------------------------------------
# Spot configuration
# ---------------------------------------------------------------------------


def guard_allin_threshold(value: float) -> None:
    """Refuse a preflop-style fraction where the postflop route wants a percent.

    This is the one input error the server cannot report, because both readings parse and both
    build a tree. Only the node count and the action menu differ, and by the time anybody looks
    at those, the timing has already been written down as if it were the answer.
    """
    if value < MIN_ALLIN_THRESHOLD_PCT:
        raise SystemExit(
            f"allin_threshold={value} is below {MIN_ALLIN_THRESHOLD_PCT} and is refused.\n"
            "  The postflop route takes a PERCENT (85 means 85% of pot; the server divides by\n"
            "  100). The preflop engine takes a FRACTION in (0,1] and this repo's committed\n"
            "  preflop config uses 0.67, which is where the mistake comes from. A fraction here\n"
            "  is accepted silently, means 0.85%, and replaces every bet size with a jam: 85\n"
            "  builds 145,245 nodes with a Check/Bet-75% menu, 0.85 builds 31,761 with\n"
            "  Check/All-in, about 4.5x smaller. Pass a percent."
        )


@dataclass(frozen=True)
class StreetSizes:
    """One player's sizing menu on one street. `raise_size` is `raise` on the wire.

    A bare number is a percent of pot ("75"), "Nx" a raise-to multiple, "a" all-in, "" none.
    Several sizes on one street are separated by a comma, a space or a semicolon, which is why
    the CLI separates STREETS with "/" instead.
    """

    bet: str = ""
    raise_size: str = ""
    donk: str = ""

    def to_body(self) -> dict[str, str]:
        return {"bet": self.bet, "raise": self.raise_size, "donk": self.donk}


@dataclass(frozen=True)
class SpotSpec:
    """Everything `POST /api/spot` needs, plus the label its rows are filed under."""

    label: str
    board: str
    range_oop: str
    range_ip: str
    starting_pot: float
    effective_stack: float
    oop: tuple[StreetSizes, ...]
    ip: tuple[StreetSizes, ...]
    allin_threshold: float = 85.0
    max_raises: int = 10
    add_allin: bool = False
    rake_pct: float = 0.0
    rake_cap: float = 0.0

    def __post_init__(self) -> None:
        guard_allin_threshold(self.allin_threshold)
        for role, streets in (("oop", self.oop), ("ip", self.ip)):
            if len(streets) != 3:
                raise SystemExit(f"{role} needs 3 streets [flop, turn, river], got {len(streets)}")

    def to_body(self) -> dict:
        return {
            "board": self.board,
            "range_oop": self.range_oop,
            "range_ip": self.range_ip,
            "starting_pot": self.starting_pot,
            "effective_stack": self.effective_stack,
            "rake_pct": self.rake_pct,
            "rake_cap": self.rake_cap,
            "allin_threshold": self.allin_threshold,
            "add_allin": self.add_allin,
            "max_raises": self.max_raises,
            "oop": [street.to_body() for street in self.oop],
            "ip": [street.to_body() for street in self.ip],
        }

    @classmethod
    def from_payload(cls, payload: dict, label: str | None) -> SpotSpec:
        def streets(key: str) -> tuple[StreetSizes, ...]:
            return tuple(
                StreetSizes(
                    str(entry.get("bet", "")),
                    str(entry.get("raise", entry.get("raise_size", ""))),
                    str(entry.get("donk", "")),
                )
                for entry in payload[key]
            )

        numbers = {
            key: float(payload.get(key, default))
            for key, default in (
                ("starting_pot", 0.0),
                ("effective_stack", 0.0),
                ("allin_threshold", 85.0),
                ("rake_pct", 0.0),
                ("rake_cap", 0.0),
            )
        }
        return cls(
            label=label or payload.get("label") or payload["board"],
            board=payload["board"],
            range_oop=payload["range_oop"],
            range_ip=payload["range_ip"],
            oop=streets("oop"),
            ip=streets("ip"),
            max_raises=int(payload.get("max_raises", 10)),
            add_allin=bool(payload.get("add_allin", False)),
            **numbers,
        )


# The validation tree, and the thermal reference. Small enough to solve in about half a second,
# which is what makes it usable as a before/after probe on every row.
SMOKE_SPOT = SpotSpec(
    label="smoke-AhKs2d-toy-ranges",
    board="AhKs2d",
    range_oop="QQ+,AKs,AQs",
    range_ip="TT+,AKs,KQs",
    starting_pot=20.0,
    effective_stack=100.0,
    oop=(StreetSizes(bet="75"),) * 3,
    ip=(StreetSizes(bet="75"),) * 3,
    max_raises=2,
)


class SolverClient:
    """The only thing here that speaks to the solver.

    Kept as a seam rather than free functions, so a different instrument could be dropped in
    behind the same six methods. `target/release/solve-cli` is NOT that drop-in, and was checked:
    its config is a different schema from the server's and flips units again - `rake_pct` and
    `allin_threshold` are fractions there and percents on this route - and its own
    `peak_rss_mb()` reads `/proc/self/status` and prints NaN on macOS. Swapping to it would be a
    new adapter and a new unit guard, not a change of base URL.
    """

    def __init__(self, base_url: str = BASE_URL, timeout: float = 900.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def _call(self, path: str, body: dict | None = None) -> dict:
        request = urllib.request.Request(
            self.base_url + path,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace").strip()
            raise SystemExit(f"{path} refused with HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise SystemExit(
                f"{path} could not reach {self.base_url}: {error.reason}. Start the GTOpen "
                "server first; this script never starts or restarts it."
            ) from error

    def status(self) -> dict:
        return self._call("/api/status")

    def build(self, spec: SpotSpec) -> dict:
        return self._call("/api/spot", spec.to_body())

    def start_solve(self, request: dict) -> dict:
        return self._call("/api/solve", request)

    def stop(self) -> dict:
        # The handler takes no body, but the route is a POST, so send an empty object.
        return self._call("/api/stop", {})

    def node(self) -> dict:
        return self._call("/api/node", {"path": []})


# ---------------------------------------------------------------------------
# The machine, and the solver process
# ---------------------------------------------------------------------------


def run_text(command: list[str]) -> str:
    try:
        done = subprocess.run(command, capture_output=True, text=True, check=False)
    except (OSError, ValueError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def darwin_free_gb() -> float | None:
    """Free plus inactive pages, which is what a new arena can actually be faulted into."""
    output = run_text(["vm_stat"])
    page = re.search(r"page size of (\d+) bytes", output)
    if not page:
        return None
    pages = dict(re.findall(r"^(.*?):\s+(\d+)\.?$", output, flags=re.MULTILINE))
    keys = ("Pages free", "Pages inactive", "Pages speculative")
    return sum(int(pages.get(key, 0)) for key in keys) * int(page.group(1)) / 1e9


def linux_meminfo(key: str) -> float | None:
    try:
        text = Path("/proc/meminfo").read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(rf"^{key}:\s+(\d+) kB$", text, flags=re.MULTILINE)
    return int(match.group(1)) * 1024 / 1e9 if match else None


@dataclass(frozen=True)
class Machine:
    """The hardware a row was taken on. A timing without it does not transfer anywhere."""

    cpu: str
    physical_cores: int
    logical_cores: int
    ram_gb: float
    os_name: str
    free_ram_gb: float | None
    power: str

    def one_line(self) -> str:
        return (
            f"{self.cpu}, {self.physical_cores} physical / {self.logical_cores} logical cores, "
            f"{self.ram_gb:.1f} GB RAM, {self.os_name}"
        )

    def to_dict(self) -> dict:
        free = None if self.free_ram_gb is None else round(self.free_ram_gb, 2)
        return {
            "cpu": self.cpu,
            "physical_cores": self.physical_cores,
            "logical_cores": self.logical_cores,
            "ram_gb": round(self.ram_gb, 2),
            "os": self.os_name,
            "free_ram_gb": free,
            "power": self.power,
        }


def read_machine() -> Machine:
    """Read the machine facts once per run.

    Free RAM and AC state are here because both change the answer. A solve that fits when the
    box is quiet swaps when it is not, and a Mac on battery throttles, so a row taken on battery
    is a row about a slower machine than the one named on the first line.
    """
    system = platform.system()
    cpu = platform.processor() or platform.machine()
    physical = logical = 0
    ram_gb = 0.0
    free_gb: float | None = None
    power = "unknown"
    if system == "Darwin":
        keys = ("machdep.cpu.brand_string", "hw.physicalcpu", "hw.logicalcpu", "hw.memsize")
        brand, cores, threads, memory = (run_text(["sysctl", "-n", key]) for key in keys)
        cpu = brand or cpu
        physical, logical = int(cores or 0), int(threads or 0)
        ram_gb = float(memory or 0.0) / 1e9
        free_gb = darwin_free_gb()
        source = run_text(["pmset", "-g", "ps"])
        if "AC Power" in source:
            power = "AC"
        elif "Battery Power" in source:
            power = "battery (the CPU throttles; treat this row as a slower machine)"
    elif system == "Linux":
        cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
        model = re.search(r"^model name\s*:\s*(.+)$", cpuinfo, flags=re.MULTILINE)
        cpu = model.group(1).strip() if model else cpu
        logical = physical = int(run_text(["nproc"]) or 0)
        ram_gb = linux_meminfo("MemTotal") or 0.0
        free_gb = linux_meminfo("MemAvailable")
    return Machine(cpu, physical, logical, ram_gb, platform.platform(), free_gb, power)


def find_server_pid() -> int | None:
    """The pid whose resident memory is the measurement. Ambiguity is refused, not guessed."""
    pids = [int(line) for line in run_text(["pgrep", "-x", SERVER_PROCESS]).split() if line]
    if len(pids) > 1:
        raise SystemExit(
            f"{len(pids)} {SERVER_PROCESS} processes are running ({pids}). This script assumes "
            "it is the only client of one server; leave exactly one running."
        )
    return pids[0] if pids else None


def read_rss_mb(pid: int) -> float | None:
    """Resident set in decimal MB, to match the server's own `arena_mb` (bytes / 1e6)."""
    text = run_text(["ps", "-o", "rss=", "-p", str(pid)])
    return int(text) * 1024 / 1e6 if text.isdigit() else None


class ResidentSampler:
    """Poll the solver process's RSS while a solve runs and keep the high-water mark.

    Sampling is the honest method available, not a good one. The solver is a separate process,
    nothing in its API reports memory, and macOS exposes no high-water-mark counter for a
    process that is not our own child - `getrusage` covers children only - so there is nothing
    to read but the current value, repeatedly. Three limits, none of them hidden: a peak living
    entirely between two samples is invisible, so every figure is a LOWER bound; RSS counts
    shared pages; and a process that frees does not necessarily hand pages back to the OS, so a
    baseline taken after a larger solve is inflated and `peak above baseline` can read low or
    negative. The absolute peak is the figure to carry into a decision about which box can run
    a spot at all.
    """

    def __init__(self, pid: int | None, interval: float) -> None:
        self.pid = pid
        self.interval = interval
        self.samples: list[float] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            value = read_rss_mb(self.pid) if self.pid is not None else None
            if value is not None:
                self.samples.append(value)
            self._stop.wait(self.interval)

    def start(self) -> None:
        if self.pid is not None:
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)

    @property
    def peak_mb(self) -> float | None:
        return max(self.samples) if self.samples else None


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


def canonical(value: object) -> object:
    """Numbers as floats, so a posted int and an echoed float compare equal. Bools stay bools."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    return value


def digest(value: object) -> str:
    blob = json.dumps(canonical(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def gtopen_commit() -> str:
    """Which solver build produced the timing. Two builds are not one measurement."""
    try:
        head = (GTOPEN_ROOT / ".git" / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            return (GTOPEN_ROOT / ".git" / head[5:]).read_text(encoding="utf-8").strip()
        return head
    except OSError:
        return "unknown"


def arena_ceiling_mb(machine: Machine, override: float | None) -> float:
    if override is not None:
        return override
    if machine.ram_gb > 0:
        return machine.ram_gb * 1000.0 * ARENA_CEILING_FRACTION
    return FALLBACK_ARENA_CEILING_MB


def fit_iteration_cost(trace: list[tuple[float, int, int]]) -> dict | None:
    """Split the wall clock into per-iteration work and per-best-response-pass work.

    The gross figure folds in the exploitability passes, and those are a polling knob
    (`check_every`) rather than a property of the tree, so a box sized from it is sized for one
    particular polling rate. `/api/status` reports the solve's own elapsed seconds and its
    iteration on every poll, so the run leaves a trace of (elapsed, iterations, checks) for free
    and `elapsed = a*iterations + b*checks` fits both at once by least squares, with no extra
    solve paid for it. Suppressed when the trace never spans two different check counts: a fit
    through one boundary can attribute all the time to either term.
    """
    rows = [point for point in trace if point[1] > 0]
    if len(rows) < 4 or len({point[2] for point in rows}) < 2:
        return None
    s11 = sum(float(it) ** 2 for _, it, _ in rows)
    s12 = sum(float(it) * ck for _, it, ck in rows)
    s22 = sum(float(ck) ** 2 for _, _, ck in rows)
    t1 = sum(elapsed * it for elapsed, it, _ in rows)
    t2 = sum(elapsed * ck for elapsed, _, ck in rows)
    determinant = s11 * s22 - s12 * s12
    if abs(determinant) < 1e-12:
        return None
    per_iteration = (t1 * s22 - t2 * s12) / determinant
    per_check = (s11 * t2 - s12 * t1) / determinant
    residuals = [elapsed - per_iteration * it - per_check * ck for elapsed, it, ck in rows]
    return {
        "net_seconds_per_iteration": per_iteration,
        "seconds_per_best_response_pass": per_check,
        "samples": len(rows),
        "residual_rms_seconds": (sum(r * r for r in residuals) / len(residuals)) ** 0.5,
    }


def classify(status: dict, target: float, iterations: int, cap: int, fired: bool) -> str:
    if status.get("error"):
        return "solver-panic"
    if fired:
        return "stopped-by-watchdog"
    if float(status.get("exploit_pct", 0.0)) <= target:
        return OUTCOME_CONVERGED
    if iterations >= cap:
        return "hit-iteration-cap"
    return "stopped-without-either-condition"


def target_bracket(curve: list[list], target: float, check_every: int) -> dict:
    """When the target was reached, at the resolution the solver actually has.

    Exploitability is computed only on a best-response pass, so the crossing is known to within
    `check_every` iterations and never more finely. A single number would report the polling
    rate as if it were a measurement, so this reports the bracket and its width. It reads the
    full curve, before downsampling, or the crossing could be a sample that was thrown away.
    """
    reached = next((point for point in curve if point[1] <= target), None)
    if reached is None:
        return {"reached_at_iteration": None, "quantisation_iterations": check_every}
    at = int(reached[0])
    return {
        "reached_at_iteration": at,
        "bracket_low_exclusive": max(at - check_every, 0),
        "bracket_high_inclusive": at,
        "quantisation_iterations": check_every,
    }


def downsample(points: list[list], limit: int = MAX_CURVE_POINTS) -> list[list]:
    """Keep the curve readable and the report under its size limit; both ends always kept."""
    if len(points) <= limit:
        return points
    step = len(points) / (limit - 1)
    return [points[int(index * step)] for index in range(limit - 1)] + [points[-1]]


def root_strategy(node: dict) -> dict[str, list[float]]:
    actor = node.get("player")
    if actor is None:
        return {}
    hands = node["players"][actor]["hands"]
    return {hand["combo"]: list(hand.get("strategy") or []) for hand in hands}


def require_idle(client: SolverClient) -> dict:
    status = client.status()
    if status.get("state") == "running":
        raise SystemExit(
            "the server is mid-solve. There is one global session and /api/spot drops it "
            "unconditionally, so this refuses to start rather than destroy someone else's work. "
            "Wait for it, or POST /api/stop deliberately."
        )
    return status


def build_row(client: SolverClient, spec: SpotSpec, machine: Machine, ceiling: float) -> dict:
    """Build the tree and record its geometry. The cheap half, and never skipped.

    The build is also the only place the arena can be refused: `/api/stop` reaches a running
    solve and nothing reaches a running build, so the sizing decision has to be taken here, off
    the figure the build itself returns.
    """
    require_idle(client)
    body = spec.to_body()
    started = time.monotonic()
    tree = client.build(spec)
    build_seconds = time.monotonic() - started
    status = client.status()
    node = client.node()
    menu = {
        "node_type": node.get("node_type"),
        "street": node.get("street"),
        "pot": node.get("pot"),
        "actor": node.get("player"),
        "actions": node.get("actions", []),
    }
    geometry = {key: tree.get(key) for key in ("nodes", "action_nodes", "hands_oop", "hands_ip")}
    return {
        "group": "build",
        "label": spec.label,
        "measured_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "machine": machine.one_line(),
        "machine_detail": machine.to_dict(),
        "solver": {
            "url": client.base_url,
            "commit": gtopen_commit(),
            "engine": "gpu" if status.get("gpu") else "cpu",
            "gpu_available": bool(tree.get("gpu_available")),
        },
        "config": body,
        "config_sha256": digest(body),
        "echo_matched": canonical(status.get("spot_request")) == canonical(body),
        "tree": tree,
        "tree_sha256": digest(geometry),
        "build_seconds": build_seconds,
        "arena_mb": float(tree.get("arena_mb", 0.0)),
        "arena_ceiling_mb": ceiling,
        "menu": menu,
        "menu_sha256": digest(menu["actions"]),
        "spr": spec.effective_stack / spec.starting_pot if spec.starting_pot else None,
    }


def refuse_oversized(row: dict) -> None:
    if row["arena_mb"] > row["arena_ceiling_mb"]:
        raise SystemExit(
            f"{row['label']}: the arena is {row['arena_mb']:.0f} MB, over this script's "
            f"{row['arena_ceiling_mb']:.0f} MB ceiling, so the solve is refused. The server's "
            "own guard cannot save you here - mem_cap_mb() reads /proc/meminfo, absent on macOS, "
            "and falls back to a flat 48,000 MB cap. The tree is already built and there is no "
            "abort path for a build, so step the bet sizes, max_raises or ranges down and "
            "rebuild, or raise --arena-ceiling-mb deliberately."
        )


def watch_solve(
    client: SolverClient, request: dict, args: argparse.Namespace
) -> tuple[dict, float, bool, list[tuple[float, int, int]]]:
    """Poll until the state leaves "running", stopping it ourselves if the deadline passes.

    The server has exactly two stopping conditions, the exploitability target and the iteration
    cap, and neither is a clock: a tree that converges slowly runs to the cap however long that
    takes, so this is the only wall-clock bound in existence. The trace collected on the way is
    what `fit_iteration_cost` reads.
    """
    trace: list[tuple[float, int, int]] = []
    base = int(client.status().get("iteration", 0))
    started = time.monotonic()
    client.start_solve(request)
    fired = False
    try:
        while True:
            status = client.status()
            elapsed = float(status.get("elapsed_secs", 0.0))
            run_it = int(status.get("iteration", base)) - base
            if elapsed > 0 and run_it > 0:
                trace.append((elapsed, run_it, run_it // max(args.check_every, 1)))
            if status.get("state") != "running":
                return status, time.monotonic() - started, fired, trace
            if not fired and time.monotonic() - started > args.deadline:
                fired = True
                print(f"  deadline of {args.deadline:g}s passed; stopping", flush=True)
                client.stop()
            time.sleep(args.poll_interval)
    except BaseException:
        # Never leave a solve running behind a crash or a Ctrl-C: the next client to build a
        # spot would silently inherit and destroy it.
        try:
            client.stop()
        except SystemExit:
            pass
        raise


def solve_row(client: SolverClient, row: dict, args: argparse.Namespace, pid: int | None) -> dict:
    """Start the solve, watch it against our own clock, and turn it into a measured row."""
    request = {
        "max_iterations": args.max_iterations,
        "target_exploit_pct": args.target,
        "check_every": args.check_every,
    }
    if args.algorithm:
        request["algorithm"] = args.algorithm
    base = int(client.status().get("iteration", 0))
    sampler = ResidentSampler(pid, args.sample_interval)
    baseline = read_rss_mb(pid) if pid else None
    sampler.start()
    try:
        status, wall, fired, trace = watch_solve(client, request, args)
    finally:
        sampler.stop()

    final = int(status.get("iteration", base))
    iterations = max(final - base, 0)
    # The server's history counts in the cumulative iteration counter; a curve is comparable
    # across rows only in iterations of its own run, so it is rebased here.
    curve = [
        [int(point["iteration"]) - base, float(point["exploit_pct"])]
        for point in status.get("history", [])
    ]
    outcome = classify(status, args.target, iterations, args.max_iterations, fired)
    peak = sampler.peak_mb
    hands = int(row["tree"].get("hands_oop", 0)) + int(row["tree"].get("hands_ip", 0))
    strategy = root_strategy(client.node())
    # A history point carries `exploit_pct` and nothing else, so per-check chips can only be
    # derived, never read. The final check is the one point where the server reports both, so
    # the derivation is asserted against it: agreement is a cheap end-to-end check that the pot
    # this row thinks it solved is the pot the server scaled its exploitability by.
    pot = float(row["config"]["starting_pot"])
    reported_chips = float(status.get("exploit_chips", 0.0))
    derived_chips = float(status.get("exploit_pct", 0.0)) * pot / 100.0
    row = dict(row)
    row.update(
        {
            "group": "solve",
            "solve": {
                "target_exploit_pct": args.target,
                "target_chips": args.target / 100.0 * float(row["config"]["starting_pot"]),
                "max_iterations": args.max_iterations,
                "check_every": args.check_every,
                "algorithm": args.algorithm or "dcfr (server default)",
                "deadline_seconds": args.deadline,
                "wall_seconds": wall,
                "server_elapsed_seconds": float(status.get("elapsed_secs", 0.0)),
                "iteration_base": base,
                "iteration_final": final,
                "run_iterations": iterations,
                "best_response_passes": len(status.get("history", [])),
                "exploit_pct": float(status.get("exploit_pct", 0.0)),
                "exploit_chips_reported": reported_chips,
                "exploit_chips_derived": derived_chips,
                "exploit_chips_agree": abs(derived_chips - reported_chips)
                <= max(1e-9, abs(reported_chips) * 1e-6),
                "state": status.get("state"),
                "error": status.get("error", ""),
            },
            "outcome": outcome,
            "usable_for_mean": outcome == OUTCOME_CONVERGED,
            "not_usable_because": NOT_USABLE.get(outcome, ""),
            "curve": downsample(curve),
            "iterations_to_target": target_bracket(curve, args.target, args.check_every),
            "fit": fit_iteration_cost(trace),
            "memory": {
                "pid": pid,
                "baseline_mb": baseline,
                "peak_mb": peak,
                "above_baseline_mb": None if peak is None or baseline is None else peak - baseline,
                "samples": len(sampler.samples),
                "sample_interval_seconds": args.sample_interval,
            },
            "per_unit": per_unit(wall, iterations, hands, peak, baseline, row),
            "root_strategy_sha256": digest(strategy),
            # Underscored keys stay out of the serialised row. The solved strategy is what the
            # determinism diff compares, and it has to be read here rather than later, because a
            # thermal recheck rebuilds the spot and replaces the session.
            "_root_strategy": strategy,
        }
    )
    return row


def per_unit(
    wall: float, iterations: int, hands: int, peak: float | None, baseline: float | None, row: dict
) -> dict:
    """The quantities that survive being carried to another machine."""

    def over(numerator: float, denominator: float) -> float | None:
        return numerator / denominator if denominator else None

    nodes = int(row["tree"].get("action_nodes", 0))
    above = None if peak is None or baseline is None else max(peak - baseline, 0.0)
    return {
        "seconds_per_iteration": over(wall, iterations),
        "seconds_per_1000_action_nodes": over(wall * 1000.0, nodes),
        "microseconds_per_action_node_iteration": over(wall * 1e6, iterations * nodes),
        "nanoseconds_per_action_node_iteration_per_hand": over(
            wall * 1e9, iterations * nodes * hands
        ),
        "hands_counted": hands,
        "arena_bytes_per_action_node": over(row["arena_mb"] * 1e6, nodes),
        "peak_above_baseline_bytes_per_action_node": (
            None if above is None else over(above * 1e6, nodes)
        ),
        "peak_over_arena_ratio": (
            None if above is None or not row["arena_mb"] else above / row["arena_mb"]
        ),
    }


def measure_reference(client: SolverClient, args: argparse.Namespace) -> float | None:
    """Solve the smoke tree and return its wall clock, as a thermal and load probe.

    A matrix takes long enough for the machine to heat up and throttle, and a row measured on a
    hot box is not comparable with one measured on a cold box. The same tiny tree solved before
    and after a row gives the drift directly, rather than leaving every later row quietly slower
    with nothing recording it. It costs about a second, and it rebuilds the spot, which is why
    the recheck after a row discards that row's solved tree.
    """
    probe = argparse.Namespace(deadline=min(args.deadline, 120.0), poll_interval=0.05,
                               check_every=20)
    client.build(SMOKE_SPOT)
    status, wall, fired, _ = watch_solve(client, dict(REFERENCE_SOLVE), probe)
    return None if fired or status.get("error") else wall


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

SOLVE_FIELDS = (
    ("target, percent of starting pot", "solve.target_exploit_pct", ".3g"),
    ("target, chips", "solve.target_chips", ".4f"),
    ("iteration cap, per run", "solve.max_iterations", ""),
    ("iterations between best-response passes", "solve.check_every", ""),
    ("algorithm", "solve.algorithm", ""),
    ("watchdog deadline, seconds", "solve.deadline_seconds", ".1f"),
    ("wall clock, seconds", "solve.wall_seconds", ".3f"),
    ("server-reported elapsed, seconds", "solve.server_elapsed_seconds", ".3f"),
    ("iterations this run", "solve.run_iterations", ""),
    ("cumulative counter, before and after", "solve.iteration_span", ""),
    ("best-response passes", "solve.best_response_passes", ""),
    ("reached exploitability, percent of pot", "solve.exploit_pct", ".4f"),
    ("reached exploitability, chips as reported by the server", "solve.exploit_chips_reported",
     ".4f"),
    ("reached exploitability, chips derived from the percent", "solve.exploit_chips_derived",
     ".4f"),
    ("reported and derived chips agree", "solve.exploit_chips_agree", ""),
    ("final state", "solve.state", ""),
    ("outcome", "outcome", ""),
    ("usable for a mean", "usable_for_mean", ""),
    ("excluded because", "not_usable_because", ""),
    ("iterations to target", "iterations_to_target.reached_at_iteration", ""),
    ("iterations to target, bracket", "iterations_to_target.bracket", ""),
    ("bracket width, iterations", "iterations_to_target.quantisation_iterations", ""),
)
MEMORY_FIELDS = (
    ("solver pid", "memory.pid", ""),
    ("baseline resident, MB", "memory.baseline_mb", ".1f"),
    ("peak resident, MB", "memory.peak_mb", ".1f"),
    ("peak above baseline, MB", "memory.above_baseline_mb", ".1f"),
    ("server arena estimate, MB", "arena_mb", ".1f"),
    ("samples", "memory.samples", ""),
    ("sample interval, seconds", "memory.sample_interval_seconds", ".2f"),
)
UNIT_FIELDS = (
    ("seconds per iteration, gross", "per_unit.seconds_per_iteration", ".5f"),
    ("seconds per iteration, net of checks", "fit.net_seconds_per_iteration", ".5f"),
    ("seconds per best-response pass", "fit.seconds_per_best_response_pass", ".5f"),
    ("fit samples, and residual RMS seconds", "fit.quality", ""),
    ("seconds per 1000 action nodes", "per_unit.seconds_per_1000_action_nodes", ".5f"),
    ("microseconds per action-node iteration", "per_unit.microseconds_per_action_node_iteration",
     ".4f"),
    ("nanoseconds per action-node iteration per hand",
     "per_unit.nanoseconds_per_action_node_iteration_per_hand", ".4f"),
    ("hands counted in that figure", "per_unit.hands_counted", ""),
    ("arena bytes per action node", "per_unit.arena_bytes_per_action_node", ".1f"),
    ("measured peak above baseline, bytes per action node",
     "per_unit.peak_above_baseline_bytes_per_action_node", ".1f"),
    ("measured peak above baseline over arena estimate", "per_unit.peak_over_arena_ratio", ".2f"),
    ("root strategy sha256", "root_strategy_sha256", ""),
)
THERMAL_FIELDS = (
    ("smoke reference before this row, seconds", "thermal.before_seconds", ".3f"),
    ("smoke reference after this row, seconds", "thermal.after_seconds", ".3f"),
    ("drift, percent", "thermal.drift_pct", "+.1f"),
)
DETERMINISM_FIELDS = (
    ("identical solved strategy", "determinism.identical", ""),
    ("root strategy sha256, run 1 and run 2", "determinism.shas", ""),
    ("largest per-action frequency divergence", "determinism.max_divergence", ".6g"),
    ("combos present in one run only", "determinism.shape_differences", ""),
    ("exploitability percent, run 1 and run 2", "determinism.exploit_pcts", ""),
    ("exploitability chips, run 1 and run 2", "determinism.exploit_chips", ""),
    ("iterations, run 1 and run 2", "determinism.iterations", ""),
    ("wall clock seconds, run 1 and run 2", "determinism.walls", ""),
)

NOTE_QUANTISATION = (
    "- the crossing is known only to the bracket width, because exploitability is measured only"
    " on a best-response pass and never between two"
)
NOTE_SAMPLING = (
    "- sampled with ps, so the peak is a lower bound: a peak between two samples is invisible,"
    " RSS counts shared pages, and freed pages are not always returned to the OS, which inflates"
    " a baseline taken after a larger solve"
)
# Two measured limitations of the block above, recorded so the columns are not misread. Both
# were observed against a live server: the arena turned out to be resident before the sampler
# ever started, and a process holding only a 145,245-node smoke tree still reported 9,912 MB
# resident because it had held a 6,220,932-node tree earlier in the same session.
NOTE_BASELINE_IS_POST_BUILD = (
    "- the baseline is read AFTER the tree is built and the arena is already resident by then,"
    " so `peak above baseline` measures almost nothing and must not be read as the solve's"
    " memory cost; the absolute peak is the only figure in this block that carries meaning"
)
NOTE_FRESH_SERVER_ONLY = (
    "- the server does not return freed pages to the OS, so `peak resident` is a high-water mark"
    " over everything that process has ever held rather than over this row; it is trustworthy"
    " only on a freshly started server, and otherwise is an upper bound carrying earlier spots"
)
NOTE_UNITS = (
    "- the net figures come from a least-squares fit of elapsed = a*iterations + b*checks over"
    " the run's own status samples; n/a means the trace never spanned two check boundaries, so"
    " the split could not be seen"
)
NOTE_THERMAL = (
    "- a positive drift means the machine slowed while this row ran, so the row's own cost"
    " over-states the same work on a cold box"
)
NOTE_DETERMINISM = (
    "- wall clock is expected to vary and is no part of the determinism claim; the strategy"
    " digest and the iteration count are"
)

LIMITATIONS = "\n".join(
    [
        "Limitations of the columns below",
        "--------------------------------",
        "",
        "These held for every row, so they are stated once here rather than repeated under each.",
        "",
        "Exploitability and the curve",
        NOTE_QUANTISATION,
        "- the chips figure on each curve point is DERIVED as percent x starting pot / 100; the"
        " API's history carries the percent only, and the server reports chips just for the"
        " final check, which is the figure each Solve block cross-checks the derivation against",
        "",
        "Memory",
        NOTE_SAMPLING,
        NOTE_BASELINE_IS_POST_BUILD,
        NOTE_FRESH_SERVER_ONLY,
        "",
        "Per-unit costs and thermal drift",
        NOTE_UNITS,
        NOTE_THERMAL,
        NOTE_DETERMINISM,
    ]
)

HOW_TO_READ = """How to read this
----------------

Each row is one build or one solve, measured end to end on the machine named in its own Machine
line. Totals are not the point, because the box that will run the real solve is not this one, so
every solve row carries per-unit costs and those are what rescale. Peak resident memory is a
separate axis from time: a solve that exceeds a box's RAM fails rather than slows, so the memory
block decides which boxes can run a spot at all and the timing block decides how long it takes on
the ones that can. A row that stopped on the iteration cap or on the watchdog reports a floor
rather than a cost and is excluded from every aggregate here. Nothing below is extrapolated: a
figure for 1,755 flops, or for any count of preflop lines, is a multiplication somebody else does
and is not a measurement."""


def fmt(value: object, spec: str = "") -> str:
    if value is None:
        return "n/a"
    return format(value, spec) if spec and isinstance(value, float) else str(value)


def dig(row: dict, path: str) -> object:
    value: object = row
    for key in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def render_fields(row: dict, fields: tuple[tuple[str, str, str], ...]) -> list[str]:
    lines = []
    for caption, path, spec in fields:
        value = dig(row, path)
        if value != "":
            lines.append(f"- {caption}: {fmt(value, spec)}")
    return lines


def sizes_line(streets: list[dict]) -> str:
    return " | ".join(
        f"{name} bet={sizes['bet'] or '-'} raise={sizes['raise'] or '-'} "
        f"donk={sizes['donk'] or '-'}"
        for name, sizes in zip(("flop", "turn", "river"), streets, strict=True)
    )


def derived(row: dict) -> dict:
    """Composite strings the field tables read, kept out of the stored row.

    They are presentation, not measurement: every part of them is already a field of its own in
    the serialised row, and a stored copy would be a second place for the same number to live.
    """
    view = json.loads(json.dumps({key: value for key, value in row.items() if key != "_"}))
    solve, fit, bracket = view.get("solve"), view.get("fit"), view.get("iterations_to_target")
    if solve:
        solve["iteration_span"] = f"{solve['iteration_base']} -> {solve['iteration_final']}"
    if fit:
        fit["quality"] = f"{fit['samples']} samples, residual RMS {fit['residual_rms_seconds']:.4f}"
    if bracket and bracket.get("reached_at_iteration") is not None:
        bracket["bracket"] = (
            f"({bracket['bracket_low_exclusive']}, {bracket['bracket_high_inclusive']}]"
        )
    diff = view.get("determinism")
    if diff:
        for name, keys, spec in (
            ("shas", ("sha_a", "sha_b"), ""),
            ("exploit_pcts", ("exploit_pct_a", "exploit_pct_b"), ".4f"),
            ("exploit_chips", ("exploit_chips_a", "exploit_chips_b"), ".4f"),
            ("iterations", ("iterations_a", "iterations_b"), ""),
            ("walls", ("wall_a", "wall_b"), ".3f"),
        ):
            diff[name] = " vs ".join(fmt(diff[key], spec) for key in keys)
    return view


def render_row(row: dict, stored: dict | None = None) -> list[str]:
    """`row` carries real values and renders the text; `stored` carries references and is what
    the machine-readable line holds. They are the same row, written twice at different cost."""
    stored = row if stored is None else stored
    view = derived(row)
    cfg, tree, menu = view["config"], view["tree"], view["menu"]
    actions = " | ".join(f"{i} {action['label']}" for i, action in enumerate(menu["actions"]))
    lines = [
        f"### {view['label']}",
        "",
        f"Measured at: {view['measured_at']}",
        f"Machine: {view['machine']}",
        f"Solver: GTOpen {view['solver']['commit'][:12]} on {view['solver']['engine']}"
        f" at {view['solver']['url']}",
        "",
        "Spot",
        f"- {cfg['board']}, pot {cfg['starting_pot']:g}, stack {cfg['effective_stack']:g},"
        f" SPR {fmt(view['spr'], '.2f')}, allin_threshold {cfg['allin_threshold']:g} percent,"
        f" max_raises {cfg['max_raises']}, add_allin {cfg['add_allin']},"
        f" rake {cfg['rake_pct']:g}% cap {cfg['rake_cap']:g}",
        f"- ranges, resolved in the appendix: oop {reference(stored, ('config', 'range_oop'))},"
        f" ip {reference(stored, ('config', 'range_ip'))}",
        f"- oop sizes: {sizes_line(cfg['oop'])}",
        f"- ip sizes: {sizes_line(cfg['ip'])}",
        f"- config sha256 {view['config_sha256'][:16]}, and the server echoed the posted config"
        f" back unchanged: {view['echo_matched']}",
        "",
        "Tree",
        f"- {tree['nodes']} nodes, {tree['action_nodes']} action nodes,"
        f" {tree['hands_oop']}v{tree['hands_ip']} hands, arena {view['arena_mb']:.1f} MB of a"
        f" {view['arena_ceiling_mb']:.0f} MB ceiling, built in {view['build_seconds']:.3f} s",
        f"- geometry sha256 {view['tree_sha256'][:16]}, root menu sha256"
        f" {view['menu_sha256'][:16]}",
        f"- root {menu['node_type']} node, street {menu['street']}, pot {menu['pot']:g},"
        f" actor {menu['actor']}: {actions}",
    ]
    if view["group"] == "solve":
        lines += render_solve_block(view)
    if view["group"] == "determinism":
        lines += ["", "Determinism", *render_fields(view, DETERMINISM_FIELDS)]
    # `per_unit` is dropped rather than stored: every field in it is a ratio of numbers already
    # on this row, so storing it is the same figures written twice. `restore_per_unit` puts it
    # back on load, which keeps the row identical without paying 400 bytes a row for it.
    payload = {
        key: value
        for key, value in stored.items()
        if not key.startswith("_") and key != "per_unit"
    }
    return lines + ["", ROW_MARKER + json.dumps(payload, sort_keys=True, separators=(",", ":")), ""]


def render_solve_block(view: dict) -> list[str]:
    # The chips column is derived, not read: a history point carries `exploit_pct` alone.
    pot = float(view["config"]["starting_pot"])
    curve = "  ".join(
        f"{int(it)}:{pct:.3f}%/{pct * pot / 100.0:.3f}c" for it, pct in view["curve"]
    )
    lines = [
        "",
        "Solve",
        *render_fields(view, SOLVE_FIELDS),
        "",
        "Convergence curve (iteration of this run : exploitability percent of pot / chips)",
        f"- {curve or 'none'}",
        "",
        f"Memory (peak resident set of the {SERVER_PROCESS} process)",
        *render_fields(view, MEMORY_FIELDS),
        "",
        "Per unit (what transfers to other hardware)",
        *render_fields(view, UNIT_FIELDS),
    ]
    if view.get("thermal"):
        lines += ["", "Thermal reference", *render_fields(view, THERMAL_FIELDS)]
    return lines


FLOP_TEXTURES = ("rainbow", "two-tone", "monotone")


def board_texture(board: str) -> str:
    """Suit texture of a board, read off the cards rather than trusted from the row's label.

    Rainbow, two-tone and monotone are a three-card vocabulary and do not survive being
    stretched: a two-flush turn has three distinct suits and is not rainbow in any sense a
    reader would accept. So a 4 or 5 card board reports its suit multiset instead of
    borrowing a name that would misdescribe it, and the flop names stay exact.
    """
    suits = [board[i + 1] for i in range(0, len(board) - 1, 2)]
    if len(suits) == 3:
        return {1: "monotone", 2: "two-tone"}.get(len(set(suits)), "rainbow")
    counts = sorted(Counter(suits).values(), reverse=True)
    return "suits " + "-".join(str(count) for count in counts)


def render_aggregate(rows: list[dict]) -> list[str]:
    usable = [row for row in rows if row.get("usable_for_mean")]
    excluded = [row for row in rows if not row.get("usable_for_mean")]
    lines = [
        f"Aggregate over the {len(usable)} of {len(rows)} rows that reached their target;"
        f" {len(excluded)} excluded as cap-bound or failed.",
    ]
    lines += [f"- excluded: {row['label']} - {row['outcome']}" for row in excluded]
    for key, spec in (
        ("microseconds_per_action_node_iteration", ".4f"),
        ("nanoseconds_per_action_node_iteration_per_hand", ".4f"),
        ("seconds_per_iteration", ".5f"),
    ):
        values = [row["per_unit"][key] for row in usable if row["per_unit"].get(key) is not None]
        if values:
            lines.append(
                f"- {key}: min {min(values):{spec}}, median {statistics.median(values):{spec}},"
                f" max {max(values):{spec}}"
            )
    peaks = [row["memory"]["peak_mb"] for row in usable if row["memory"].get("peak_mb")]
    if peaks:
        lines.append(f"- peak resident MB: min {min(peaks):.1f}, max {max(peaks):.1f}")
    lines.append(
        "- these are per-unit costs pooled across different spots, which is the only thing that"
        " can be pooled; pooling wall clocks across spots would mean nothing"
    )
    targets = sorted(
        {row["solve"]["target_exploit_pct"] for row in usable if row.get("solve")}
    )
    if len(targets) > 1:
        lines.append(
            "- WARNING: these rows do not share one target, they span"
            f" {', '.join(f'{t:g}%' for t in targets)} of pot. Iterations to target and every"
            " figure derived from them are not comparable across different targets, so this"
            " block should be read per target and not as one pool"
        )
    elif targets:
        lines.append(f"- every pooled row targets {targets[0]:g}% of the starting pot")
    lines += render_texture_coverage(usable, rows)
    return lines


def texture_ratios(rows: list[dict]) -> dict[tuple[str, str], list[float]]:
    """Per-iteration cost ratios between textures, measured only where nothing else varies.

    A ratio is worth quoting only from rows that share a tree size, a bet menu and an
    iteration count, because then texture is the one thing left that differs. Rows are
    grouped on exactly that and every cross-texture pair inside a group is emitted, so the
    caller sees the spread between groups rather than one number with no error bar.
    Cap-bound rows are wanted here: a fixed-iteration probe is the cleanest comparison there
    is, and excluding it would leave the ratio resting on whichever spots happened to converge.
    """
    groups: dict[tuple, dict[str, float]] = {}
    for row in rows:
        solve, tree, unit = row.get("solve"), row.get("tree"), row.get("per_unit") or {}
        cost = unit.get("seconds_per_iteration")
        if not solve or not tree or cost is None:
            continue
        key = (tree["action_nodes"], row.get("menu_sha256"), solve["run_iterations"])
        groups.setdefault(key, {})[board_texture(tree["board"])] = cost
    ratios: dict[tuple[str, str], list[float]] = {}
    for costs in groups.values():
        for dearer in costs:
            for cheaper in costs:
                if dearer != cheaper and costs[cheaper] > 0:
                    ratios.setdefault((dearer, cheaper), []).append(
                        costs[dearer] / costs[cheaper]
                    )
    return ratios


def render_texture_coverage(usable: list[dict], rows: list[dict]) -> list[str]:
    """Name the textures the pooled figures rest on, because texture is the largest cost driver.

    An aggregate that happens to exclude a texture is not a mean over flops, and the ratios
    below say how far off it is. Everything here is derived from the rows, including the
    ratios, so it stays true as cells are added rather than freezing today's numbers into a
    sentence that quietly goes stale.
    """
    textures = [board_texture(row["tree"]["board"]) for row in usable if row.get("tree")]
    if not textures:
        return []
    counted = Counter(textures)
    missing = [name for name in FLOP_TEXTURES if name not in counted]
    counts = ", ".join(f"{name} {counted.get(name, 0)}" for name in FLOP_TEXTURES)
    extra = sorted(name for name in counted if name not in FLOP_TEXTURES)
    if extra:
        counts += ", " + ", ".join(f"{name} {counted[name]}" for name in extra)
    lines = [f"- texture coverage of the pooled rows: {counts}"]
    if not missing:
        return lines
    lines.append(
        f"- NOT MEASURED at this target: {', '.join(missing)}. A figure for those textures taken"
        " from this block is scaled rather than measured"
    )
    for (dearer, cheaper), seen in sorted(texture_ratios(rows).items()):
        if dearer in missing and cheaper in counted:
            spread = (
                f"{min(seen):.2f}x"
                if len(seen) == 1
                else f"{min(seen):.2f}x to {max(seen):.2f}x"
            )
            lines.append(
                f"- measured scaling for that: one {dearer} iteration costs {spread} a"
                f" {cheaper} one, from {len(seen)} group(s) of rows sharing a tree size, a menu"
                " and an iteration count, so texture is the only thing left differing"
            )
    return lines


def render_report(rows: list[dict], machine: Machine, url: str) -> str:
    lines = [
        "Postflop Solve Cost Report",
        "==========================",
        "",
        f"Generated at: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"Solver: GTOpen at {url}, commit {gtopen_commit()[:12]}",
        f"Machine: {machine.one_line()}",
        f"Free RAM at generation: {fmt(machine.free_ram_gb, '.1f')} GB; power: {machine.power}",
        "",
        HOW_TO_READ,
        "",
        LIMITATIONS,
        "",
    ]
    stored_rows, table = intern_rows(rows)
    for group in GROUPS:
        members = [
            (row, stored)
            for row, stored in zip(rows, stored_rows, strict=True)
            if row.get("group") == group
        ]
        lines += [f"## {GROUP_TITLES[group]}", ""]
        if not members:
            lines += ["(none recorded)", ""]
            continue
        if group == "solve":
            lines += render_aggregate([row for row, _ in members]) + [""]
        for row, stored in members:
            lines += render_row(row, stored)
    lines += render_appendix(table)
    return "\n".join(lines).rstrip() + "\n"



def _intern_holder(row: dict, path: tuple[str, ...]) -> tuple[dict | None, str]:
    holder: object = row
    for key in path[:-1]:
        if not isinstance(holder, dict):
            return None, path[-1]
        holder = holder.get(key)
    return (holder if isinstance(holder, dict) else None), path[-1]


def intern_rows(rows: list[dict]) -> tuple[list[dict], dict[str, object]]:
    """Swap the repeated bulk fields for references, and return the table they point into."""
    table: dict[str, object] = {}
    out: list[dict] = []
    for row in rows:
        copy = json.loads(json.dumps(row))
        for path in INTERN_PATHS:
            holder, leaf = _intern_holder(copy, path)
            if holder is None or leaf not in holder:
                continue
            value = holder[leaf]
            if isinstance(value, str) and value.startswith(REF_PREFIX):
                continue
            key = f"{'.'.join(path)}@{digest(value)[:12]}"
            table[key] = value
            holder[leaf] = REF_PREFIX + key
        out.append(copy)
    return out, table


def expand_rows(rows: list[dict], table: dict[str, object]) -> list[dict]:
    """Put the referenced values back, so a loaded row is indistinguishable from a fresh one."""
    for row in rows:
        for path in INTERN_PATHS:
            holder, leaf = _intern_holder(row, path)
            if holder is None:
                continue
            value = holder.get(leaf)
            if isinstance(value, str) and value.startswith(REF_PREFIX):
                stored = table.get(value[len(REF_PREFIX) :])
                if stored is not None:
                    holder[leaf] = json.loads(json.dumps(stored))
    return rows


def reference(stored: dict, path: tuple[str, ...]) -> str:
    holder, leaf = _intern_holder(stored, path)
    value = holder.get(leaf) if holder else None
    if isinstance(value, str) and value.startswith(REF_PREFIX):
        return value[len(REF_PREFIX) :]
    return "inline"


def render_appendix(table: dict[str, object]) -> list[str]:
    lines = [
        "## Appendix: the values the rows reference",
        "",
        "Each entry is written once here and named by every row that used it. The key is a hash"
        " of the value, so a row naming a key is still proof of which range, which sizing and"
        " which menu it was measured on - the same proof a per-row copy gave, without paying"
        " for the copy on every row.",
        "",
    ]
    for key in sorted(table):
        lines += [
            f"### {key}",
            APPENDIX_MARKER
            + json.dumps({"key": key, "value": table[key]}, separators=(",", ":"), sort_keys=True),
            "",
        ]
    return lines


def load_rows(path: Path) -> list[dict]:
    """Rows with their referenced values put back, so a reload round-trips to the same report."""
    if not path.exists():
        return []
    rows: list[dict] = []
    table: dict[str, object] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = ROW_MARKER if line.startswith(ROW_MARKER) else None
        marker = APPENDIX_MARKER if line.startswith(APPENDIX_MARKER) else marker
        if marker is None:
            continue
        try:
            payload = json.loads(line[len(marker) :])
        except json.JSONDecodeError:
            continue
        if marker == APPENDIX_MARKER:
            table[payload["key"]] = payload["value"]
        else:
            rows.append(payload)
    return [restore_per_unit(row) for row in expand_rows(rows, table)]


def restore_per_unit(row: dict) -> dict:
    """Recompute the derived per-unit block a loaded row does not carry."""
    if row.get("group") not in {"solve", "determinism"} or "per_unit" in row:
        return row
    solve, memory, tree = row.get("solve"), row.get("memory") or {}, row.get("tree") or {}
    if not solve:
        return row
    hands = int(tree.get("hands_oop", 0)) + int(tree.get("hands_ip", 0))
    row["per_unit"] = per_unit(
        float(solve.get("wall_seconds", 0.0)),
        int(solve.get("run_iterations", 0)),
        hands,
        memory.get("peak_mb"),
        memory.get("baseline_mb"),
        row,
    )
    return row


def write_report(new_rows: list[dict], machine: Machine, url: str, fresh: bool) -> Path:
    """Upsert rows by (group, label) and regenerate the file from every row it then holds."""
    existing = [] if fresh else load_rows(REPORT_PATH)
    keys = {(row["group"], row["label"]) for row in new_rows}
    kept = [row for row in existing if (row.get("group"), row.get("label")) not in keys]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(kept + new_rows, machine, url), encoding="utf-8")
    return REPORT_PATH


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def per_street(value: str) -> tuple[str, str, str]:
    """Split a sizing argument into three streets on "/".

    Not on a comma: a comma already separates several sizes within one street, which is exactly
    the mistake that would silently build a different tree.
    """
    parts = [part.strip() for part in value.split("/")] if value else [""]
    if len(parts) == 1:
        parts = parts * 3
    if len(parts) != 3:
        raise SystemExit(f"sizing {value!r} needs one value or three separated by '/'")
    return parts[0], parts[1], parts[2]


# Flags that describe the tree. A preset or a spot file already describes it, so one of these
# arriving beside them is a request the script cannot honour, and honouring it silently is how a
# row ends up labelled as one tree and measured on another.
SPOT_FLAGS = (
    "board",
    "range_oop",
    "range_ip",
    "pot",
    "stack",
    "bet",
    "raise_size",
    "donk",
    "allin_threshold",
    "max_raises",
    "add_allin",
    "rake_pct",
    "rake_cap",
)


def refuse_ignored_flags(args: argparse.Namespace, source: str) -> None:
    defaults = parse_args([])
    given = [flag for flag in SPOT_FLAGS if getattr(args, flag) != getattr(defaults, flag)]
    if given:
        raise SystemExit(
            f"{source} already describes the whole spot, so {', '.join(sorted(given))} would be "
            "ignored rather than applied. Drop the flag, or describe the spot with --board "
            "instead of a preset."
        )


def spec_from_args(args: argparse.Namespace) -> SpotSpec:
    if args.preset == "smoke":
        refuse_ignored_flags(args, "--preset")
        return replace(SMOKE_SPOT, label=args.label) if args.label else SMOKE_SPOT
    if args.spot_json:
        refuse_ignored_flags(args, "--spot-json")
        payload = json.loads(Path(args.spot_json).read_text(encoding="utf-8"))
        return SpotSpec.from_payload(payload, args.label)
    if not args.board:
        raise SystemExit(
            "describe a spot one of three ways: --preset smoke, --spot-json PATH, or --board"
            " with --range-oop, --range-ip, --pot, --stack and --bet."
        )
    bets, raises, donks = (per_street(value) for value in (args.bet, args.raise_size, args.donk))
    return SpotSpec(
        label=args.label or f"{args.board}-pot{args.pot:g}-stack{args.stack:g}",
        board=args.board,
        range_oop=args.range_oop,
        range_ip=args.range_ip,
        starting_pot=args.pot,
        effective_stack=args.stack,
        oop=tuple(StreetSizes(bets[i], raises[i], donks[i]) for i in range(3)),
        # donk sizes are an OOP concept in the engine, so the IP menu never carries one.
        ip=tuple(StreetSizes(bets[i], raises[i]) for i in range(3)),
        allin_threshold=args.allin_threshold,
        max_raises=args.max_raises,
        add_allin=args.add_allin,
        rake_pct=args.rake_pct,
        rake_cap=args.rake_cap,
    )


ARGUMENTS = (
    ("--preset", {"choices": ["smoke"], "help": "the tiny validation tree"}),
    ("--spot-json", {"help": "a JSON file holding the full spot config"}),
    ("--label", {"help": "the name this row is filed under in the report"}),
    ("--board", {"help": "3 to 5 cards, e.g. AhKs2d"}),
    ("--range-oop", {"default": "", "help": 'range text, e.g. "QQ+,AKs:0.5,A5s-A2s"'}),
    ("--range-ip", {"default": ""}),
    ("--pot", {"type": float, "default": 0.0}),
    ("--stack", {"type": float, "default": 0.0}),
    ("--bet", {"default": "", "help": "one size set, or three streets split on '/'"}),
    ("--raise", {"dest": "raise_size", "default": ""}),
    ("--donk", {"default": "", "help": "OOP only, as in the engine"}),
    ("--allin-threshold", {"type": float, "default": 85.0,
                           "help": "PERCENT of pot, not the preflop fraction; under 1.0 refused"}),
    ("--max-raises", {"type": int, "default": 10}),
    ("--add-allin", {"action": "store_true"}),
    ("--rake-pct", {"type": float, "default": 0.0}),
    ("--rake-cap", {"type": float, "default": 0.0}),
    ("--target", {"type": float, "default": 0.3, "help": "percent of the starting pot"}),
    ("--max-iterations", {"type": int, "default": 2000}),
    ("--check-every", {"type": int, "default": 20}),
    ("--algorithm", {"choices": ["dcfr", "cfr+", "pcfr+"]}),
    ("--deadline", {"type": float, "default": 900.0,
                    "help": "wall-clock seconds; the server has no time cap of its own"}),
    ("--build-only", {"action": "store_true", "help": "build and size the tree, do not solve"}),
    ("--determinism", {"action": "store_true", "help": "solve the same config twice and diff"}),
    ("--arena-ceiling-mb", {"type": float, "help": "refuse to solve above this arena size"}),
    ("--no-thermal-recheck", {"dest": "thermal", "action": "store_false",
                              "help": "skip the drift probe; it rebuilds and discards the solve"}),
    ("--poll-interval", {"type": float, "default": 0.25}),
    ("--sample-interval", {"type": float, "default": 0.25}),
    ("--url", {"default": BASE_URL}),
    ("--no-report", {"dest": "report", "action": "store_false"}),
    ("--fresh", {"action": "store_true", "help": "discard rows already in the report"}),
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for flag, options in ARGUMENTS:
        parser.add_argument(flag, **options)
    return parser.parse_args(argv)


def run_one(
    client: SolverClient,
    spec: SpotSpec,
    machine: Machine,
    ceiling: float,
    pid: int | None,
    args: argparse.Namespace,
    label: str,
) -> dict:
    before = measure_reference(client, args) if args.thermal else None
    row = build_row(client, replace(spec, label=label), machine, ceiling)
    refuse_oversized(row)
    row = solve_row(client, row, args, pid)
    if args.thermal:
        after = measure_reference(client, args)
        drift = (after / before - 1.0) * 100.0 if before and after else None
        row["thermal"] = {"before_seconds": before, "after_seconds": after, "drift_pct": drift}
    return row


def run_determinism(
    client: SolverClient,
    spec: SpotSpec,
    machine: Machine,
    ceiling: float,
    pid: int | None,
    args: argparse.Namespace,
) -> list[dict]:
    """Build and solve the same config twice, and diff what came out.

    The rebuild between the two runs is deliberate: the iteration counter is cumulative and
    survives a stop, so re-solving without rebuilding would resume rather than repeat, and the
    second run would be a different experiment.
    """
    first = run_one(client, spec, machine, ceiling, pid, args, f"{spec.label} (run 1)")
    second = run_one(client, spec, machine, ceiling, pid, args, f"{spec.label} (run 2)")
    strategy_a, strategy_b = first["_root_strategy"], second["_root_strategy"]
    divergence = 0.0
    for combo, row_a in strategy_a.items():
        row_b = strategy_b.get(combo)
        if row_b is None or len(row_a) != len(row_b):
            continue
        pairs = zip(row_a, row_b, strict=True)
        divergence = max(divergence, max((abs(a - b) for a, b in pairs), default=0.0))
    shape = len(set(strategy_a) ^ set(strategy_b))
    diff = {
        "identical": digest(strategy_a) == digest(strategy_b) and not shape,
        "sha_a": digest(strategy_a)[:16],
        "sha_b": digest(strategy_b)[:16],
        "max_divergence": divergence,
        "shape_differences": shape,
    }
    for name, key in (
        ("exploit_pct", "exploit_pct"),
        ("exploit_chips", "exploit_chips_reported"),
        ("iterations", "run_iterations"),
        ("wall", "wall_seconds"),
    ):
        diff[f"{name}_a"] = first["solve"][key]
        diff[f"{name}_b"] = second["solve"][key]
    summary = dict(second)
    summary.update({"group": "determinism", "label": spec.label, "determinism": diff})
    print(
        f"determinism: identical={diff['identical']}, max divergence"
        f" {diff['max_divergence']:.6g}, shape differences {shape}",
        flush=True,
    )
    return [first, second, summary]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    client = SolverClient(args.url)
    machine = read_machine()
    spec = spec_from_args(args)
    ceiling = arena_ceiling_mb(machine, args.arena_ceiling_mb)
    pid = find_server_pid()
    print(f"machine: {machine.one_line()}", flush=True)
    if pid is None:
        print(
            f"  no {SERVER_PROCESS} process found by name, so memory cannot be measured;"
            " timings still can",
            flush=True,
        )

    if args.build_only:
        row = build_row(client, spec, machine, ceiling)
        tree = row["tree"]
        over = " - OVER the ceiling, a solve would be refused" if row["arena_mb"] > ceiling else ""
        print(
            f"build-only {spec.label}: {tree['nodes']} nodes, {tree['action_nodes']} action"
            f" nodes, {tree['hands_oop']}v{tree['hands_ip']} hands, arena"
            f" {row['arena_mb']:.1f} MB of a {ceiling:.0f} MB ceiling, built in"
            f" {row['build_seconds']:.3f} s{over}",
            flush=True,
        )
        rows = [row]
    elif args.determinism:
        rows = run_determinism(client, spec, machine, ceiling, pid, args)
    else:
        rows = [run_one(client, spec, machine, ceiling, pid, args, spec.label)]

    for row in rows:
        if row["group"] == "solve":
            solve = row["solve"]
            print(
                f"{row['label']}: {row['outcome']} in {solve['wall_seconds']:.3f} s over"
                f" {solve['run_iterations']} iterations at {solve['exploit_pct']:.4f}%,"
                f" peak {fmt(row['memory']['peak_mb'], '.1f')} MB",
                flush=True,
            )
    if args.report:
        print(f"wrote {write_report(rows, machine, args.url, args.fresh)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
