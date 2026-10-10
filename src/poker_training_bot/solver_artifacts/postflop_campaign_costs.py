"""What a rented machine costs: the spend ledger, and the ranking of candidate machines.

Nothing here rents, prices or calls anything. Machines, their memory and their hourly prices come
in as data, because decision 5 rules that the machine types and prices go to Taylor before
anything is rented; a price written into this module would be one nobody vouched for.

**The ledger.** Every rented hour is logged with its price, and the running total is printed
beside the cap it counts against. A run the cap cannot pay for is refused by `authorise` before
it starts rather than noted afterwards. `record` always logs what was actually spent, even past
the cap: an overrun is a fact the ledger must hold, and once one is logged nothing more is
authorised. Decision 6 sets the trial cap at `BENCHMARK_CAP_USD`, covering every rented run before
the campaign, the GPU trial included; the campaign cap is asked separately.

**The ranking.** A candidate is ranked on cost per solved flop: its hourly price times the billed
time for one closed flop, every one of `BILLED_PARTS`. A stretch missing a part is refused, since
pricing the solve alone is the cheapest-looking figure available and on a closed flop the harvest
may cost more than the solve. Before any candidate is priced, one that cannot hold the memory bar
at the ruled ceiling is excluded with that reason and never ranked, so the campaign cannot meet a
board its machine refuses. A machine running more than one solve at once (decision 11's default
is one) applies the bar to their sum.

**The bar is the one the driver's guard reads.** The server states an arena in 10^6 bytes and the
solve driver's guard reads that figure as 2^20 bytes on purpose, about five percent high (decision
14). A bar in the server's unit would rank a machine whose memory sits inside that five percent and
then see the driver refuse the line's largest flop on it. So `guard_memory_bar_bytes` turns the
server's figure into the driver's, through the driver's own reading function, and `rank_candidates`
refuses a bar below that reading whenever it is handed the server's figure. The comparison itself
uses the bar exactly as given, and admits a ceiling equal to it, as the driver does.

**A graphics card is checked against its own bar.** A candidate solving on the card names the GPU
engine and carries its card memory; it is excluded with its own reason when GTOpen's own card
budget, free memory less the solver's fixed headroom, cannot hold the card bar (GTOpen's
`vram_estimate_bytes` for the line's largest flop). The host bar still applies to it, because the
driver's guard checks host memory whatever the engine.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from poker_training_bot.solver_artifacts.postflop_machine import CPU_ENGINE, ENGINES, GPU_ENGINE
from poker_training_bot.solver_artifacts.postflop_solve_driver import MEMORY_CEILING_FRACTION
from poker_training_bot.solver_artifacts.postflop_transport import arena_bytes

BENCHMARK_CAP_USD = 100.0
"""Decision 6, confirmed for RunPod on 2026-10-04: the trial cap in dollars."""

BILLED_PARTS = ("server_start", "tree_build", "solve", "harvest", "upload")
"""The billed stretch of one closed flop, in seconds per part: the server started, the tree built,
the flop solved, every flop and turn decision point harvested, and the result uploaded."""

DEFAULT_CONCURRENT_SOLVES = 1
"""Decision 11's default: one solve at a time on one machine."""

SERVER_ARENA_UNIT_BYTES = 1_000_000
"""What the server means by one of `arena_mb`'s megabytes: `spot.arena_bytes_for(storage) as f64 /
1e6` in GTOpen's `/api/spot`. The driver's guard reads the same field through `arena_bytes`."""

GTOPEN_GPU_MARGIN_BYTES = 512 * SERVER_ARENA_UNIT_BYTES
"""GTOpen's `GPU_MARGIN_MB` of 512 (`crates/server/src/main.rs:263`), kept free on the card on top
of its estimate. `gpu_budget` takes the card's free memory in whole 10^6-byte megabytes less this,
and a solve whose estimate is above the budget does not run on the card."""

SECONDS_PER_HOUR = 3600.0
CANDIDATES_RECORD_SCHEMA_VERSION = 1


def _finite(value: object, what: str, *, positive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{what} must be a number, got {value!r}")
    number = float(value)
    if not math.isfinite(number) or number < 0 or (positive and number == 0):
        bound = "above zero" if positive else "zero or more"
        raise ValueError(f"{what} must be finite and {bound}, got {value!r}")
    return number


def _named(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty name, got {value!r}")
    return value


def _whole_bytes(value: object, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a whole number of bytes above zero, got {value!r}")
    return value


# --- The bars, as the guards that refuse a solve read them


def guard_memory_bar_bytes(server_arena_bytes: int) -> int:
    """A planned arena in the server's own bytes, as the solve driver's guard reads it: the server
    reports it as `arena_mb` in 10^6 bytes, and the driver reads that through `arena_bytes`, the
    same arithmetic `postflop_solve_driver` runs before it calls `check_memory_ceiling`."""
    server = _whole_bytes(server_arena_bytes, "the server's arena")
    return arena_bytes(server / SERVER_ARENA_UNIT_BYTES)


def gtopen_card_budget_bytes(card_memory_bytes: int) -> int:
    """What GTOpen lets a solve use on a card with `card_memory_bytes` free, ported from
    `gpu_budget`: free memory in whole 10^6-byte megabytes, less the fixed headroom, never below
    zero."""
    card = _whole_bytes(card_memory_bytes, "the card's memory")
    whole_megabytes = card // SERVER_ARENA_UNIT_BYTES * SERVER_ARENA_UNIT_BYTES
    return max(0, whole_megabytes - GTOPEN_GPU_MARGIN_BYTES)


# --- The candidate machines


@dataclass(frozen=True)
class Candidate:
    """One machine offered for the campaign: its memory, its hourly price, the seconds each billed
    part of one closed flop took on it, and the engine it solves on.

    `card_memory_bytes` is the card's free memory as CUDA reports it before a solve, which is what
    GTOpen budgets from; a provider's headline figure overstates it by CUDA's own use. A GPU
    candidate must carry it and a CPU candidate must not, so a card is never left unchecked by
    omission and a figure nothing reads is never recorded as if it were checked."""

    name: str
    memory_bytes: int
    price_per_hour_usd: float
    billed_seconds: Mapping[str, float] = field(default_factory=dict)
    engine: str = CPU_ENGINE
    card_memory_bytes: int | None = None

    def to_document(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "memory_bytes": self.memory_bytes,
            "price_per_hour_usd": self.price_per_hour_usd,
            "billed_seconds": dict(self.billed_seconds),
            "engine": self.engine,
            "card_memory_bytes": self.card_memory_bytes,
        }

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> Candidate:
        """A record written before candidates named their engine reads as a CPU candidate."""
        return cls(
            name=document["name"],
            memory_bytes=document["memory_bytes"],
            price_per_hour_usd=document["price_per_hour_usd"],
            billed_seconds=dict(document["billed_seconds"]),
            engine=document.get("engine", CPU_ENGINE),
            card_memory_bytes=document.get("card_memory_bytes"),
        )


def _check_engine(candidate: Candidate) -> None:
    if candidate.engine not in ENGINES:
        raise ValueError(
            f"{candidate.name}: engine must be one of {ENGINES}, got {candidate.engine!r}"
        )
    if candidate.engine == GPU_ENGINE:
        _whole_bytes(
            candidate.card_memory_bytes, f"{candidate.name}: a GPU candidate's card memory"
        )
    elif candidate.card_memory_bytes is not None:
        raise ValueError(
            f"{candidate.name}: a CPU candidate carries card memory nothing would check; name the"
            f" {GPU_ENGINE} engine or drop the figure"
        )


def billed_seconds_per_flop(candidate: Candidate) -> float:
    """The whole billed stretch of one closed flop, in seconds, refusing a stretch that leaves out
    a billed part or names one the contract does not bill."""
    stretch = candidate.billed_seconds
    missing = [part for part in BILLED_PARTS if part not in stretch]
    if missing:
        raise ValueError(
            f"{candidate.name}: the billed stretch leaves out {missing}; a closed flop is billed"
            f" for all of {list(BILLED_PARTS)}"
        )
    unknown = sorted(set(stretch) - set(BILLED_PARTS))
    if unknown:
        raise ValueError(f"{candidate.name}: the billed stretch names unbilled parts {unknown}")
    return math.fsum(
        _finite(stretch[part], f"{candidate.name}: {part} seconds", positive=False)
        for part in BILLED_PARTS
    )


def cost_per_solved_flop(candidate: Candidate) -> float:
    """Dollars for one closed flop on `candidate`: its hourly price times its billed stretch."""
    price = _finite(candidate.price_per_hour_usd, f"{candidate.name}: price", positive=False)
    return price * billed_seconds_per_flop(candidate) / SECONDS_PER_HOUR


def memory_exclusion(
    candidate: Candidate,
    *,
    memory_bar_bytes: int,
    ceiling_fraction: float = MEMORY_CEILING_FRACTION,
    concurrent_solves: int = DEFAULT_CONCURRENT_SOLVES,
) -> str | None:
    """Why `candidate` cannot hold the memory bar, or None when it can.

    A ceiling equal to the bar holds it; only a ceiling below the bar excludes."""
    _finite(candidate.memory_bytes, f"{candidate.name}: memory bytes", positive=True)
    required_bytes = memory_bar_bytes * concurrent_solves
    if candidate.memory_bytes * ceiling_fraction < required_bytes:
        solves = "one solve" if concurrent_solves == 1 else f"{concurrent_solves} solves at once"
        return (
            f"cannot hold the memory bar at the {ceiling_fraction:.2f} ceiling:"
            f" {candidate.memory_bytes * ceiling_fraction:,.0f} bytes allowed of"
            f" {candidate.memory_bytes:,} bytes of memory, {required_bytes:,} bytes needed for"
            f" {solves}"
        )
    return None


def card_exclusion(
    candidate: Candidate,
    *,
    card_bar_bytes: int,
    concurrent_solves: int = DEFAULT_CONCURRENT_SOLVES,
) -> str | None:
    """Why a GPU candidate's card cannot hold the card bar, or None when it can or the candidate
    solves on the CPU. GTOpen refuses the card only when its estimate is above the budget, so a
    budget equal to the bar holds it."""
    _check_engine(candidate)
    if candidate.engine != GPU_ENGINE or candidate.card_memory_bytes is None:
        return None
    budget = gtopen_card_budget_bytes(candidate.card_memory_bytes)
    required = card_bar_bytes * concurrent_solves
    if budget < required:
        return (
            f"its card cannot hold the card memory bar: GTOpen budgets {budget:,} bytes of the"
            f" {candidate.card_memory_bytes:,} free, {required:,} bytes needed for"
            f" {concurrent_solves} solve{'s' if concurrent_solves > 1 else ''}"
        )
    return None


@dataclass(frozen=True)
class Ranking:
    """Every candidate offered, the ones that hold the bar cheapest per solved flop first, and the
    ones that cannot, by name with the reason."""

    candidates: tuple[Candidate, ...]
    ranked: tuple[Candidate, ...]
    excluded: dict[str, str]
    cost_per_solved_flop_usd: dict[str, float]
    memory_bar_bytes: int
    ceiling_fraction: float
    concurrent_solves: int
    card_bar_bytes: int | None = None

    def to_document(self) -> dict[str, Any]:
        """The committed `campaign/candidates.json` record."""
        return {
            "record_schema_version": CANDIDATES_RECORD_SCHEMA_VERSION,
            "memory_bar_bytes": self.memory_bar_bytes,
            "ceiling_fraction": self.ceiling_fraction,
            "concurrent_solves": self.concurrent_solves,
            "card_memory_bar_bytes": self.card_bar_bytes,
            "candidates": [candidate.to_document() for candidate in self.candidates],
            "ranked": [candidate.name for candidate in self.ranked],
            "excluded": dict(self.excluded),
            "cost_per_solved_flop_usd": dict(self.cost_per_solved_flop_usd),
        }


def rank_candidates(
    candidates: Sequence[Candidate],
    *,
    memory_bar_bytes: int,
    ceiling_fraction: float = MEMORY_CEILING_FRACTION,
    concurrent_solves: int = DEFAULT_CONCURRENT_SOLVES,
    server_arena_bytes: int | None = None,
    card_bar_bytes: int | None = None,
) -> Ranking:
    """Exclude every candidate that cannot hold the bar, then rank the rest on cost per solved
    flop, cheapest first, ties broken by name so the order never depends on the input's.

    `server_arena_bytes`, when given, is the campaign's largest planned arena in the server's
    unit, and a `memory_bar_bytes` below the guard's reading of it is refused: ranked against it,
    a machine could rank and then be refused by the driver. `card_bar_bytes` is required as soon
    as any candidate solves on a card. An excluded candidate is never priced: whether it was timed
    at all does not matter, because it can never be chosen."""
    if isinstance(memory_bar_bytes, bool) or not isinstance(memory_bar_bytes, int):
        raise ValueError(f"the memory bar is a whole number of bytes, got {memory_bar_bytes!r}")
    if memory_bar_bytes <= 0:
        raise ValueError(f"the memory bar must be above zero bytes, got {memory_bar_bytes!r}")
    fraction = _finite(ceiling_fraction, "the ceiling fraction", positive=True)
    if fraction > 1:
        raise ValueError(f"a ceiling is a fraction of memory, at most 1, got {ceiling_fraction!r}")
    if isinstance(concurrent_solves, bool) or not isinstance(concurrent_solves, int):
        raise ValueError(f"concurrent solves is a whole number, got {concurrent_solves!r}")
    if concurrent_solves < 1:
        raise ValueError(f"a machine runs at least one solve, got {concurrent_solves!r}")
    names = [_named(candidate.name, "a candidate's name") for candidate in candidates]
    duplicated = sorted({name for name in names if names.count(name) > 1})
    if duplicated:
        raise ValueError(f"candidate names must be unique; offered twice: {duplicated}")
    if server_arena_bytes is not None:
        guard_bar = guard_memory_bar_bytes(server_arena_bytes)
        if memory_bar_bytes < guard_bar:
            raise ValueError(
                f"a memory bar of {memory_bar_bytes:,} bytes is below {guard_bar:,}, the driver's"
                f" guard's reading of the {server_arena_bytes:,}-byte arena it must hold"
            )
    for candidate in candidates:
        _check_engine(candidate)
    on_cards = [candidate.name for candidate in candidates if candidate.engine == GPU_ENGINE]
    if card_bar_bytes is not None:
        _whole_bytes(card_bar_bytes, "the card memory bar")
    elif on_cards:
        raise ValueError(f"{on_cards} solve on a card, and no card memory bar was given")

    excluded: dict[str, str] = {}
    costs: dict[str, float] = {}
    holding: list[Candidate] = []
    for candidate in candidates:
        reason = memory_exclusion(
            candidate,
            memory_bar_bytes=memory_bar_bytes,
            ceiling_fraction=fraction,
            concurrent_solves=concurrent_solves,
        )
        if reason is None and card_bar_bytes is not None:
            reason = card_exclusion(
                candidate, card_bar_bytes=card_bar_bytes, concurrent_solves=concurrent_solves
            )
        if reason is not None:
            excluded[candidate.name] = reason
            continue
        costs[candidate.name] = cost_per_solved_flop(candidate)
        holding.append(candidate)
    ranked = tuple(sorted(holding, key=lambda found: (costs[found.name], found.name)))
    return Ranking(
        candidates=tuple(candidates),
        ranked=ranked,
        excluded=excluded,
        cost_per_solved_flop_usd={found.name: costs[found.name] for found in ranked},
        memory_bar_bytes=memory_bar_bytes,
        ceiling_fraction=fraction,
        concurrent_solves=concurrent_solves,
        card_bar_bytes=card_bar_bytes,
    )


# --- The spend ledger


class SpendCapError(RuntimeError):
    """A rented run the cap cannot pay for, refused before it starts."""


def _entry(machine: object, hours: object, price_per_hour_usd: object, what: object) -> dict:
    return {
        "machine": _named(machine, "the machine rented"),
        "what": _named(what, "what the rented hours were for"),
        "hours": _finite(hours, "rented hours", positive=True),
        "price_per_hour_usd": _finite(price_per_hour_usd, "the hourly price", positive=False),
    }


class SpendLedger:
    """Every rented hour with its price, and the running total against one cap."""

    def __init__(self, cap_usd: float, entries: Iterable[Mapping[str, Any]] = ()) -> None:
        self.cap_usd = _finite(cap_usd, "the cap", positive=True)
        self.entries: list[dict[str, Any]] = []
        for entry in entries:
            self.record(
                machine=entry["machine"],
                hours=entry["hours"],
                price_per_hour_usd=entry["price_per_hour_usd"],
                what=entry["what"],
            )

    @property
    def total_usd(self) -> float:
        return math.fsum(entry["hours"] * entry["price_per_hour_usd"] for entry in self.entries)

    @property
    def remaining_usd(self) -> float:
        """What the cap can still pay for; below zero once an overrun has been logged."""
        return self.cap_usd - self.total_usd

    @property
    def past_cap(self) -> bool:
        return self.total_usd > self.cap_usd

    def authorise(self, *, hours: float, price_per_hour_usd: float) -> float:
        """Return what a planned run will cost, or raise `SpendCapError` when the total would pass
        the cap. Reaching the cap exactly is allowed: work halts at the cap, not before it."""
        cost = _finite(hours, "planned hours", positive=True) * _finite(
            price_per_hour_usd, "the hourly price", positive=False
        )
        if self.total_usd + cost > self.cap_usd:
            raise SpendCapError(
                f"a run of {hours} hours at ${price_per_hour_usd:,.2f} an hour costs"
                f" ${cost:,.2f}; {self.summary()}, so the cap cannot pay for it"
            )
        return cost

    def record(
        self, *, machine: str, hours: float, price_per_hour_usd: float, what: str
    ) -> dict[str, Any]:
        """Log hours actually rented. Never refused for the cap: spent money is logged as spent,
        and a logged overrun leaves `authorise` refusing everything after it."""
        entry = _entry(machine, hours, price_per_hour_usd, what)
        self.entries.append(entry)
        return entry

    def summary(self) -> str:
        """The running total printed beside the cap it counts against."""
        if self.past_cap:
            return (
                f"${self.total_usd:,.2f} spent, ${-self.remaining_usd:,.2f} past the"
                f" ${self.cap_usd:,.2f} cap; nothing more is authorised"
            )
        return (
            f"${self.total_usd:,.2f} spent of the ${self.cap_usd:,.2f} cap,"
            f" ${self.remaining_usd:,.2f} remaining"
        )

    def to_document(self) -> dict[str, Any]:
        return {
            "cap_usd": self.cap_usd,
            "total_usd": self.total_usd,
            "entries": [dict(entry) for entry in self.entries],
        }

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> SpendLedger:
        """Read a committed ledger back, refusing one whose stated total is not its entries'.

        A ledger past its cap is read as it stands, since it records what was spent; whoever
        publishes it asks `past_cap`."""
        ledger = cls(cap_usd=document["cap_usd"], entries=document["entries"])
        if document["total_usd"] != ledger.total_usd:
            raise ValueError(
                f"the ledger states ${document['total_usd']} spent, but its entries total"
                f" ${ledger.total_usd}"
            )
        return ledger
