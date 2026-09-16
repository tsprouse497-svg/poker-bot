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
