"""What a GTOpen answer is, and how to read one without inventing the part it did not send.

Split out of `postflop_solve_driver` at the 500-line cap, on the seam that module's own name
draws: the driver holds what a solve is and how to drive one, and this holds what the wire is.
`postflop_isomorphism` and `postflop_sizing` came out of the same cap earlier in this phase.

Nothing here opens a socket at import. `http_transport` is built by a caller that has a server,
and every reader below is handed a mapping that has already come back.

**Read closed.** Each reader below was once a `.get(key, default)` inside the driver, and every
one of those defaults passed the guard it fed. An absent `arena_mb` planned a zero-byte tree, so
the memory ceiling - the whole reason the tree is built before it is solved - cleared trivially.
An absent `exploit_pct` read as 0.0% of pot, better than the target, so the solve classified as
converged and the cell committed. An absent `iteration` read as zero, under the cap. An absent
`state` ended the poll on its first look, which makes a mid-solve reading the final one. A server
that answered nothing produced a cell that looked perfect, and that is the one way a guard must
not fail: absence is a refusal here, never a number."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping


class SolveDriverError(RuntimeError):
    """A refusal. Every one of these fires before the solve, or stops it part-way."""


# --- The wire itself

BASE_URL = "http://127.0.0.1:3737"

Transport = Callable[[str, dict | None], dict]
"""Method-free by design: a body means POST and no body means GET, which is the whole of GTOpen's
convention. Handed in so nothing here opens a socket at import or in a test."""


def http_transport(base_url: str = BASE_URL, timeout: float = 900.0) -> Transport:
    """The real transport. Constructed by a caller that has a server, never at import."""

    def call(path: str, body: dict | None = None) -> dict:
        request = urllib.request.Request(
            base_url + path,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace").strip()
            raise SolveDriverError(f"{path} refused with HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise SolveDriverError(
                f"{path} could not reach {base_url}: {error.reason}. Start the GTOpen server "
                "first; this driver never starts, restarts or installs one."
            ) from error

    return call


# --- Reading one answer, closed rather than open


def answered(response: Mapping[str, object], route: str, key: str) -> object:
    """One field the server actually answered, or a refusal naming the route and the field. The
    module docstring lists what each of these used to default to and what the default passed."""
    value = response.get(key)
    if value is None:
        raise SolveDriverError(
            f"{route} answered without {key}, so nothing downstream of it is a measurement. "
            "Refused rather than defaulted: no default here reads as worse than the run it "
            "stands in for."
        )
    return value


def numeric(response: Mapping[str, object], route: str, key: str) -> float:
    """`answered`, narrowed to the fields a guard compares against a threshold. A string that
    would parse is refused too: the comparison, not the parse, is what this feeds."""
    value = answered(response, route, key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SolveDriverError(f"{route} answered {key}={value!r}, which is not a number")
    return float(value)


def arena_bytes(arena_mb: float) -> int:
    """`/api/spot`'s `arena_mb` in bytes, taking the larger reading of the unit: nothing in
    GTOpen's routes says whether that field is 10^6 or 2^20 bytes, and 2^20 makes a planned solve
    look bigger, so the ambiguity errs toward refusing rather than starting a run that dies."""
    return int(arena_mb * 1024 * 1024)


# --- Which arena the server actually allocated, decided rather than assumed

FULL_PRECISION_ARENA = "f32"
QUANTIZED_ARENA = "compressed"
"""GTOpen's two storage modes, named as `crates/solver/src/store.rs` names them: four bytes an
entry, or two bytes an entry plus one f32 scale per tree node for each of four arrays."""

_MB = 1_000_000
"""The server's own conversion, `spot.arena_bytes_for(storage) as f64 / 1e6`. `arena_bytes` above
reads the same field as 2^20 on purpose, because a guard that over-reads refuses early; this
reader is reproducing the server's arithmetic rather than sizing a guard, so it must use the
server's unit or it compares two different numbers."""

_GPU_SLACK_BYTES = 512 * 1024 * 1024
"""The flat term `Spot::vram_estimate_bytes` adds after the staging buffers and the arenas."""


def arena_storage(built: Mapping[str, object]) -> str:
    """Which arena a built tree got, read off `/api/spot`'s own answer, or a refusal.

    **No route reports the storage mode.** The server picks it from its own environment and says
    nothing about it, so a run asking for full precision and silently getting quantized arenas
    looks identical on the wire - which is the one failure that makes every number a campaign
    produces the wrong measurement under a right-looking label.

    It is nevertheless decidable, because two fields of one `TreeInfo` are computed from the same
    entry count under different rules. `vram_mb` is
    `nodes * (hands_oop + hands_ip + max of the two) * 4 + entries * 8 + 512 MiB`, and its arena
    term is full precision whatever the storage is; `arena_mb` is `entries * 8` under full
    precision and `entries * 4 + nodes * 16` under quantization. So the entry count comes out of
    `vram_mb` and the two candidate arenas are then arithmetic, and they differ by roughly a
    factor of two - far too wide for the answer to be in doubt.

    Every reading is refused rather than guessed: an entry count that is not a whole number, an
    arena matching neither candidate, and the degenerate tree where both candidates coincide.
    """
    nodes = int(numeric(built, "/api/spot", "nodes"))
    oop = int(numeric(built, "/api/spot", "hands_oop"))
    ip = int(numeric(built, "/api/spot", "hands_ip"))
    arena = round(numeric(built, "/api/spot", "arena_mb") * _MB)
    vram = round(numeric(built, "/api/spot", "vram_mb") * _MB)
    staging = nodes * (oop + ip + max(oop, ip)) * 4
    entries_bytes = vram - staging - _GPU_SLACK_BYTES
    if entries_bytes <= 0 or entries_bytes % 8:
        raise SolveDriverError(
            f"/api/spot answered arena_mb and vram_mb that do not reconcile: {vram} bytes of VRAM "
            f"less {staging} of staging and {_GPU_SLACK_BYTES} of slack leaves {entries_bytes}, "
            "which is not a whole number of solver entries. The storage mode cannot be told from "
            "this answer, so the run is refused rather than assumed."
        )
    candidates = {
        FULL_PRECISION_ARENA: entries_bytes,
        QUANTIZED_ARENA: entries_bytes // 2 + nodes * 16,
    }
    matched = sorted(name for name, size in candidates.items() if size == arena)
    if len(matched) != 1:
        raise SolveDriverError(
            f"/api/spot planned an arena of {arena} bytes, and this tree's two storage modes come "
            f"to {candidates}. {'Both' if matched else 'Neither'} answers to that, so which arena "
            "the server allocated cannot be told and the run is refused."
        )
    return matched[0]


def check_arena_storage(built: Mapping[str, object], wanted: str) -> str:
    """`arena_storage`, refusing anything but the arena the campaign was configured for.

    The server chooses from its environment and reports nothing, so the only honest order is ask,
    read back, refuse - the same order the memory ceiling uses, and for the same reason: a run
    that has already started is a cost that has already been paid.
    """
    found = arena_storage(built)
    if found != wanted:
        raise SolveDriverError(
            f"the solve was configured for {wanted} arenas and the server built {found} ones. "
            "GTOpen selects storage from SOLVER_COMPRESS in its own environment and answers "
            "nothing about it, so a server started without that variable, or with any value but "
            "the one it tests for, quantizes silently. Refused before solving: numbers from the "
            "two arenas are not the same measurement."
        )
    return found
