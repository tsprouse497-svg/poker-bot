"""What drives GTOpen's postflop routes, and every refusal it owes before a solve starts.

Nothing in the gate runs this: the gate has no GTOpen, no Rust toolchain and no network, and the
solver is a sibling clone outside this repo. So importing this module touches no socket and no
subprocess - the transport is handed in, and the only thing read at import is this machine's RAM.

**The guards are the point.** A solve costs hours and money on a rented box, and both mistakes
this phase already paid for are silent: a solve that dies on memory after it has run, and a
threshold posted in the wrong unit that builds a different tree and says nothing about it. Both
are refused before `/api/solve`, because afterwards the cost is spent. Three facts about the
record, kept here so nobody infers them from a field name:

- **Three of GTOpen's four postflop routes were driven end to end** on 2026-08-23 and 2026-08-24:
  `/api/spot`, `/api/solve`, `/api/status` and `/api/node`. The batch `/api/reports/*` route was
  read from the README and never executed. `REPORTS_ROUTE_STATUS` says which of the two honest
  states this driver is in; the contract forbids the third, used and unmeasured.
- **GTOpen's own memory guard is not a guard everywhere.** It reads `/proc/meminfo` and falls
  through to a flat 48,000 MB without it, which on Darwin is always, and
  `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` was filed on that. A Linux box has the file and the
  guard goes live, so the entry is restated against the machine rather than closed; this driver
  assumes neither platform and publishes its own ceiling from the box it is running on.
- **Every timing, arena and memory figure this phase quotes was measured on an Apple M4, 10 cores,
  34.4 GB RAM, CPU engine**, and decision 11's machine note rules that none of them transfers to
  the rented box. So nothing here predicts a cost elsewhere: what travels is policy - a fraction
  of RAM, a unit, an ordering - never a number standing in for a measurement nobody took.

`scripts/measure_postflop_solve_cost.py` took the record; this is the campaign driver, and they
share the fraction and the unit guard deliberately. What the wire is - the transport, the routes'
base URL, and the closed readers that refuse a field the server did not send - is in
`postflop_transport`; this module holds what a solve is and how to drive one."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from poker_training_bot.solver_artifacts.postflop_artifact import (
    EXPLOITABILITY_CEILING_PCT_OF_POT,
    EXPLOITABILITY_TARGET_PCT_OF_POT,
    RANGE_WEIGHT_FLOOR,
    SOLVE_ITERATION_CAP,
)
from poker_training_bot.solver_artifacts.postflop_transport import (
    FULL_PRECISION_ARENA,
    SolveDriverError,
    Transport,
    answered,
    arena_bytes,
    numeric,
)

# --- The machine, and the memory ceiling this driver publishes for it

MEASURING_MACHINE = "Apple M4, 10 cores, 34.4 GB RAM, CPU engine"  # what a report must name

MEMORY_CEILING_FRACTION = 0.40
"""A policy rather than a measurement, which is why it is what travels between machines. The arena
is faulted in lazily during the solve, so it is paid as resident memory alongside the tree, the
ranges and whatever else the box runs, and a ceiling near the RAM figure lets a machine swap. The
measuring script keeps the same fraction; it is the only guard that fired in the record.

**It was 0.35 and Taylor moved it to 0.40 on 2026-09-20, `frozen-into-data`, to admit the flop
campaign at full-precision arenas.** Quantized arenas cost about half as much memory, and every
arena figure this phase recorded before that date was taken under them, so asking for full
precision roughly doubles the planned arena on the same tree - `arena_storage` in
`postflop_transport` derives both sizes from one `/api/spot` answer, and they differ by
`entries * 4` less `nodes * 16`. The campaign plans an arena the 0.35 ceiling refused by a
fraction of a percent and this one clears with room to spare. What moved is the policy rather than
the arithmetic: 0.35 was the number meant to travel to the rented box the contract names, so this
loosens the guard there too, which is a cost of the ruling rather than an oversight in it.
Decision 20 carries the measurements and what was rejected."""

FALLBACK_MEMORY_CEILING_BYTES = 4096 * 1024 * 1024
"""Used only when this machine will not say how much memory it has. Deliberately small, and not
GTOpen's own 48,000 MB fallback - about 1.5x the RAM of the box it fell back on, where the same
solver's preflop side uses 2,000 MB, so 48,000 is an outlier rather than a ruling."""


def _physical_memory_bytes() -> int | None:
    """Total RAM, asking the C library rather than the platform. `SC_PHYS_PAGES` and
    `SC_PAGE_SIZE` are answered by both Linux and Darwin, which keeps this off `/proc/meminfo` on
    one side and `sysctl` on the other; the box is unnamed, so a platform test here would be the
    assumption `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` priced."""
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError):
        return None
    if not isinstance(pages, int) or not isinstance(page_size, int):
        return None
    total = pages * page_size
    return total if total > 0 else None


_PHYSICAL_MEMORY_BYTES = _physical_memory_bytes()
MEMORY_CEILING_IS_MEASURED = _PHYSICAL_MEMORY_BYTES is not None
MEMORY_CEILING_BYTES: int = (
    int(_PHYSICAL_MEMORY_BYTES * MEMORY_CEILING_FRACTION)
    if _PHYSICAL_MEMORY_BYTES is not None
    else FALLBACK_MEMORY_CEILING_BYTES
)
"""What a planned arena may not exceed on **this** machine, read at import. A constant here would
be the M4's ceiling wearing the rented box's name, and the arena verdict for the single-raised tree
- the ordinary way to see a flop - turns on exactly it."""


def describe_memory_ceiling() -> str:
    """One line a report or a refusal can print, saying where the ceiling came from."""
    if not MEMORY_CEILING_IS_MEASURED:
        return (
            f"{MEMORY_CEILING_BYTES / 1e9:.1f} GB, a fallback: this machine did not report its "
            "physical memory, so the ceiling is a stated floor rather than a fraction of anything"
        )
    return (
        f"{MEMORY_CEILING_BYTES / 1e9:.1f} GB, {MEMORY_CEILING_FRACTION:.0%} of the "
        f"{(_PHYSICAL_MEMORY_BYTES or 0) / 1e9:.1f} GB this machine reports"
    )


def gtopen_memory_guard() -> dict[str, object]:
    """Whether the solver's own guard can fire here: a recorded fact, not a refusal. Nothing relies
    on it - this driver's ceiling is required either way and is what refuses - but a box whose
    solver guard is dead runs with one guard rather than two, and the packet must say which."""
    present = os.path.exists("/proc/meminfo")
    return {
        "proc_meminfo_present": present,
        "solver_guard_live": present,
        "solver_fallback_mb": None if present else 48_000,
        "note": (
            "GTOpen reads /proc/meminfo and falls through to a flat 48,000 MB without it; "
            "SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS was filed on that fallback."
        ),
    }


def check_memory_ceiling(planned_bytes: int) -> None:
    """Refuse a planned arena above this machine's ceiling, before anything is solved. A solve
    exceeding RAM fails rather than slows and `/api/spot` has no abort path, so the safe order is
    build, read the arena back, refuse or proceed - measured on the tree, not predicted."""
    if planned_bytes > MEMORY_CEILING_BYTES:
        raise SolveDriverError(
            f"planned arena of {planned_bytes / 1e9:.2f} GB is over this driver's ceiling of "
            f"{describe_memory_ceiling()}, so it is refused before solving. Floor the input ranges "
            f"at {RANGE_WEIGHT_FLOOR} class-level, which leaves the action-node count untouched, "
            "or raise the ceiling as a deliberate decision in the open."
        )


# --- The unit trap on `allin_threshold`

MIN_ALLIN_THRESHOLD_PCT = 1.0
MAX_ALLIN_THRESHOLD_PCT = 100.0


def validate_allin_threshold(value: float) -> float:
    """`SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`. Postflop this field is a percent, and
    the preflop route takes a fraction where this repo's committed preflop config posts `0.67`.
    Posting that here asks for 0.67% and the server converts every configured bet into a jam. Both
    readings parse, both build a tree, and nothing in the response says which you got - measured
    live, 85 built 145,245 nodes with a Check/Bet-75% menu and 0.85 built 31,761 with Check/All-in.
    What it is a percent **of** is the acting player's remaining stack, not the pot: `tree.rs` snaps
    a bet reaching `allin_threshold * max_to`, `max_to` being the stack behind, so
    `docs/GTOPEN_SOLVER_NOTES.md` is wrong about the mechanism and right about the trap.

    The upper bound is this driver's own and the contract does not ask for it, stated rather than
    left implicit: the server divides by 100, so above 100 the comparison is unreachable and every
    jam silently leaves a tree that, per decision 11, gets its jams by this conversion alone."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"allin_threshold must be a number, got {value!r}")
    number = float(value)
    if number != number:  # NaN, which compares false against every bound below
        raise ValueError("allin_threshold is not a number")
    if number < MIN_ALLIN_THRESHOLD_PCT:
        raise ValueError(
            f"allin_threshold={number} is below {MIN_ALLIN_THRESHOLD_PCT} and is refused. This "
            "route takes a PERCENT of the acting player's remaining stack; the preflop engine "
            "takes a fraction and the committed preflop config posts 0.67. A fraction here is "
            "accepted silently and replaces every configured bet size with a jam."
        )
    if number > MAX_ALLIN_THRESHOLD_PCT:
        raise ValueError(
            f"allin_threshold={number} is above {MAX_ALLIN_THRESHOLD_PCT}%, so the snap can never "
            "fire and the tree holds no jam at all. Refused as the mirror of the unit trap."
        )
    return number


# --- The configuration the campaign is pointed at, committed beside the data

RULED_ALLIN_THRESHOLD_PCT = 85.0
"""What every measured row posted. On the flop the snap fires under neither menu in either pot
type, so a committed flop cell's action set is what its menu says. On later streets it does fire,
and the four things deciding which side a node falls on - `max_raises`, the raise multiplier, the
starting pot and the effective stack - are pinned on this config and on every cell."""

RULED_ARENA_STORAGE = FULL_PRECISION_ARENA
"""Full precision, ruled by Taylor 2026-09-20, `frozen-into-data`, and part of the configuration
rather than of the command line because a number solved under quantized arenas and a number solved
under these are not the same measurement. The server picks its arena from its own environment and
reports nothing, so this is the value `check_arena_storage` holds the built tree against, and
`solve_config.json` carries it beside the menu so a reader of a committed cell can tell which of
the two it is reading."""

RULED_MAX_RAISES = 2
FLOP_BET_SIZES = ("33", "75")
LATER_STREET_BET_SIZES = ("66", "125")
RULED_RAISE_SIZE = "2.5x"
STREETS = ("flop", "turn", "river")

_RULED_SEAT: dict[str, dict[str, object]] = {
    "flop": {"bet": list(FLOP_BET_SIZES), "raise": RULED_RAISE_SIZE, "donk": []},
    "turn": {"bet": list(LATER_STREET_BET_SIZES), "raise": RULED_RAISE_SIZE, "donk": []},
    "river": {"bet": list(LATER_STREET_BET_SIZES), "raise": RULED_RAISE_SIZE, "donk": []},
}

RULED_SOLVE_CONFIG: dict[str, object] = {
    "seats": {"ip": _RULED_SEAT, "oop": _RULED_SEAT},
    "arena_storage": RULED_ARENA_STORAGE,
    "allin_threshold": RULED_ALLIN_THRESHOLD_PCT,
    "add_allin": False,
    "max_raises": RULED_MAX_RAISES,
    "rake_pct": 0.0,
    "rake_cap": 0.0,
    "range_weight_floor": RANGE_WEIGHT_FLOOR,
    "target_exploit_pct_of_pot": EXPLOITABILITY_TARGET_PCT_OF_POT,
    "max_iterations": SOLVE_ITERATION_CAP,
}
"""Decision 11, ruled by Taylor 2026-09-10: two bet sizes on every street, `33 75` on the flop and
`66 125` on turn and river, `raise: "2.5x"`, `donk` empty, identically on both seats.

An empty `donk` list does **not** mean the out-of-position player never bets the flop: GTOpen gates
the donk list on `street > root_street`, false on a flop-rooted solve, so out of position uses the
`bet` list exactly as in position. What it removes is the probe - leading turn or river into the
previous street's aggressor - which biases hero's flop betting upward through continuation values.

Nothing measured uses 66% or 125%; every row is `33 75` or `75`, so the menu is unmeasured on both
cost and strategy and the phase's first solve runs on it."""

CHECK_EVERY_ITERATIONS = 20
"""Exploitability is checked only this often, so no count is finer than a 20-iteration bracket."""


def solve_config_document() -> dict[str, object]:
    """The configuration as committed beside the data. A deep copy, because a caller mutating what
    it was handed would re-rule decision 11 by accident and the two seats are one object here."""
    return json.loads(json.dumps(RULED_SOLVE_CONFIG))


def solve_config_errors(config: Mapping[str, object]) -> list[str]:
    """Every way a config differs from the ruled one, on `gtopen_config`'s pattern and re-derived
    against `RULED_SOLVE_CONFIG`. One that does not match is rejected rather than read: the menu
    decides what a committed cell's action set even contains."""
    errors: list[str] = []
    seats = config.get("seats")
    if not isinstance(seats, Mapping) or set(seats) != set(RULED_SOLVE_CONFIG["seats"]):
        errors.append(f"seats is {seats!r}, ruled {sorted(RULED_SOLVE_CONFIG['seats'])}")
    else:
        for name, seat in sorted(seats.items()):
            if seat != _RULED_SEAT:
                errors.append(f"seat {name} is {seat!r}, ruled {_RULED_SEAT!r}")
    for key, ruled in RULED_SOLVE_CONFIG.items():
        if key != "seats" and config.get(key) != ruled:
            errors.append(f"config field {key} is {config.get(key)!r}, ruled {ruled!r}")
    return errors


def _wire_streets(seat: Mapping[str, object]) -> list[dict[str, str]]:
    """The committed shape turned into GTOpen's: three positional streets of space-separated
    strings rather than a mapping of lists."""
    wire: list[dict[str, str]] = []
    for street in STREETS:
        sizes = seat.get(street)
        if not isinstance(sizes, Mapping):
            raise SolveDriverError(f"the {street} menu must be an object, got {sizes!r}")
        wire.append(
            {
                "bet": " ".join(str(size) for size in sizes.get("bet", [])),
                "raise": str(sizes.get("raise", "")),
                "donk": " ".join(str(size) for size in sizes.get("donk", [])),
            }
        )
    return wire


@dataclass(frozen=True)
class SolvePlan:
    """One flop, one preflop line: everything `POST /api/spot` needs, plus what names the cell.
    `starting_pot` and `effective_stack` follow from the substituted preflop line rather than any
    table, which is what ties a committed cell to the key it is stored under."""

    label: str
    board: str
    preflop_line: str
    range_oop: str
    range_ip: str
    starting_pot: float
    effective_stack: float
    config: Mapping[str, object] = field(default_factory=solve_config_document)


def spot_body(plan: SolvePlan) -> dict[str, object]:
    """The `/api/spot` body for a plan, in the solver's own field names and units."""
    seats = plan.config.get("seats")
    if not isinstance(seats, Mapping) or {"ip", "oop"} - set(seats):
        raise SolveDriverError(f"the config must carry an ip and an oop seat, got {seats!r}")
    return {
        "board": plan.board,
        "range_oop": plan.range_oop,
        "range_ip": plan.range_ip,
        "starting_pot": plan.starting_pot,
        "effective_stack": plan.effective_stack,
        "rake_pct": plan.config.get("rake_pct", 0.0),
        "rake_cap": plan.config.get("rake_cap", 0.0),
        "allin_threshold": validate_allin_threshold(plan.config["allin_threshold"]),
        "add_allin": plan.config.get("add_allin", False),
        "max_raises": plan.config.get("max_raises", RULED_MAX_RAISES),
        "oop": _wire_streets(seats["oop"]),
        "ip": _wire_streets(seats["ip"]),
    }


def plan_refusals(plan: SolvePlan) -> list[str]:
    """Everything wrong with a plan that is visible without a server; empty means proceed. The
    memory ceiling is not here and cannot be - the arena is known only once `/api/spot` has built
    the tree - so `run_solve` checks it between the build and the solve."""
    refusals = [f"config: {error}" for error in solve_config_errors(plan.config)]
    try:
        validate_allin_threshold(plan.config["allin_threshold"])
    except (KeyError, ValueError) as error:
        refusals.append(f"allin_threshold: {error}")
    if len(plan.board.replace(" ", "")) != 6:
        refusals.append(f"board {plan.board!r} is not three cards; only flop roots were ever run")
    if plan.starting_pot <= 0 or plan.effective_stack <= 0:
        refusals.append(f"pot {plan.starting_pot} and stack {plan.effective_stack} must be > 0")
    return refusals


# --- The routes, and which of them this driver uses

EXERCISED_ROUTES = ("/api/spot", "/api/solve", "/api/status", "/api/node")
"""Driven end to end on 2026-08-23 and 2026-08-24, and the only routes this driver calls."""

REPORTS_ROUTE_STATUS = "not-used"
"""`/api/reports/*` is recorded in `docs/GTOPEN_SOLVER_NOTES.md` as README-sourced and never
executed, so this driver does not use it and says so rather than assuming it works.

It would have batched one spot over a weighted canonical subset of 47, 95, 184 or all 1,755 flops
in one call. Two reasons not to reach for it unmeasured: nothing in the record says what the batch
costs beyond one solve times a count, and a batch is one long-lived process, the shape the cost
notes single out as worst - the server never returns freed pages, and a session carrying a 10.3 GB
high-water mark measured about 1.6x slower per iteration than a freshly restarted one on the same
config. One flop per invocation is what makes a restart between solves possible, and moving this
to `exercised` is a measurement rather than a switch: a run that records what the batch cost, on
the machine that ran it."""


# --- Driving one solve, and judging what came back

CONVERGED = "converged-to-target"
HIT_CAP = "hit-iteration-cap"
STOPPED_OTHERWISE = "stopped-without-either-condition"


@dataclass(frozen=True)
class SolveOutcome:
    """One solve as measured rather than as hoped. `exploit_pct_of_pot` and `iterations` are what
    every committed cell carries; `wall_seconds` is a cost only when `outcome` is
    `converged-to-target`, a floor otherwise, and the contract forbids reporting a capped solve's
    wall clock as a cost."""

    label: str
    board: str
    preflop_line: str
    outcome: str
    exploit_pct_of_pot: float
    iterations: int
    wall_seconds: float
    arena_bytes: int
    iteration_bracket: int = CHECK_EVERY_ITERATIONS
    machine: str = ""


def classify_outcome(exploit_pct: float, iterations: int) -> str:
    """Which of the server's two stopping conditions fired, since `done` alone does not say. The
    target is checked first: a run reaching it at exactly the cap has converged, and reading that
    as capped would throw away a usable cost."""
    if exploit_pct <= EXPLOITABILITY_TARGET_PCT_OF_POT:
        return CONVERGED
    if iterations >= SOLVE_ITERATION_CAP:
        return HIT_CAP
    return STOPPED_OTHERWISE


def commit_verdict(outcome: SolveOutcome) -> tuple[bool, str]:
    """Decision 4, as ruled: commit a cap-bound cell under 1% of pot, refuse it above. 1% is not
    a target - 0.3% is what the campaign aims at, and 1% is the worst a played cell may carry,
    twice the upper edge of the 0.1% to 0.5% band study work uses. So a committed set is not
    uniform in accuracy, which is why the report prints the spread and why no report or packet may
    state one accuracy for the solve as a whole."""
    if outcome.outcome == STOPPED_OTHERWISE:
        return False, "the solve ended on neither stopping condition, so nothing in it is a result"
    if outcome.exploit_pct_of_pot > EXPLOITABILITY_CEILING_PCT_OF_POT:
        return False, (
            f"{outcome.exploit_pct_of_pot:.4f}% of pot is over the "
            f"{EXPLOITABILITY_CEILING_PCT_OF_POT}% ceiling, so the cell is refused rather than "
            "committed as a floor"
        )
    return True, (
        f"{outcome.exploit_pct_of_pot:.4f}% of pot at {outcome.iterations} iterations "
        f"(+/-{CHECK_EVERY_ITERATIONS}), {outcome.outcome}"
    )


def run_solve(
    plan: SolvePlan,
    transport: Transport,
    *,
    deadline_seconds: float = 6 * 60 * 60,
    poll_seconds: float = 5.0,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> SolveOutcome:
    """Build, refuse or proceed, solve, poll, and report what it actually cost.

    The order is the guard: the tree is built first, its arena read back, and the ceiling applied
    to a measured number before `/api/solve` is called. The watchdog is here because a solve that
    will not converge otherwise runs until somebody notices, and on a rented box that is money; a
    run it stops is a floor and it raises rather than returning a cost. `/api/stop` is **not** one
    of the four routes the record drove end to end, so nothing here reads its response.
    """
    refusals = plan_refusals(plan)
    if refusals:
        raise SolveDriverError(f"{plan.label} refused before solving: " + "; ".join(refusals))

    status = transport("/api/status", None)
    if str(answered(status, "/api/status", "state")) == "running":
        raise SolveDriverError(
            "the server is mid-solve and /api/spot would drop that session. There is one global "
            "session; wait for it or stop it deliberately."
        )

    built = transport("/api/spot", spot_body(plan))
    planned = arena_bytes(numeric(built, "/api/spot", "arena_mb"))
    check_memory_ceiling(planned)

    started = now()
    transport(
        "/api/solve",
        {
            "max_iterations": plan.config.get("max_iterations", SOLVE_ITERATION_CAP),
            "target_exploit_pct": plan.config.get(
                "target_exploit_pct_of_pot", EXPLOITABILITY_TARGET_PCT_OF_POT
            ),
            "check_every": CHECK_EVERY_ITERATIONS,
        },
    )
    while True:
        status = transport("/api/status", None)
        if str(answered(status, "/api/status", "state")) != "running":
            break
        if now() - started > deadline_seconds:
            transport("/api/stop", {})
            raise SolveDriverError(
                f"{plan.label} passed its {deadline_seconds:.0f}s watchdog and was stopped. Its "
                "wall clock is the deadline rather than a cost, and nothing from it is committed."
            )
        sleep(poll_seconds)

    exploit = numeric(status, "/api/status", "exploit_pct")
    iterations = int(numeric(status, "/api/status", "iteration"))
    return SolveOutcome(
        label=plan.label,
        board=plan.board,
        preflop_line=plan.preflop_line,
        outcome=classify_outcome(exploit, iterations),
        exploit_pct_of_pot=exploit,
        iterations=iterations,
        wall_seconds=now() - started,
        arena_bytes=planned,
        machine=describe_memory_ceiling(),
    )
