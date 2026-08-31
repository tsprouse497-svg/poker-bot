"""The one solve config this repo commits an export from, and the check that it was used.

Phase 10's decision 2 fixed it verbatim: six-handed, 100bb, 2.5bb opens, no limp,
rake-free, `realization: "calibrated"`, `allin_threshold: 0.67`. Phase 14's decision 14
supersedes one field of that ruling: `add_allin` is `False`, because `True` put a
full-stack jam on the raise menu at every node where a raise was legal, with no reference
to the pot. Genuine five-bet jams survive through `allin_threshold` instead. It lives in its own module because both
the export reader and the source card have to hold an export to it, and neither of them owns
the ruling.

Two fields carry most of the weight and neither is obvious. `realization` is absent from the
config body in `docs/GTOPEN_SOLVER_NOTES.md`, so every run before this phase's probe took its
default of `static`, under which the big blind defends 99.71 percent against a small-blind
open - self-consistent, checksummable, and not poker. `allin_threshold` is the one field
GTOpen's own web form cannot set, which is why a human verifies the committed export by
loading the saved solve rather than by rebuilding from the form.
"""

from __future__ import annotations

RULED_CONFIG: dict = {
    "positions": ["LJ", "HJ", "CO", "BTN", "SB", "BB"],
    "stack": 100.0,
    "posts": [0, 0, 0, 0, 0.5, 1.0],
    "ante": 0.0,
    "limp": False,
    "open_raises": [2.5],
    "raise_mults": [3.0],
    "max_raises": 4,
    "add_allin": False,
    "allin_threshold": 0.67,
    "rake_pct": 0.0,
    "rake_cap": 0.0,
    "no_flop_no_drop": True,
    "realization": "calibrated",
}


def config_errors(config: dict) -> list[str]:
    """Every field of a posted config that is not the ruled one.

    An export produced by another config is rejected rather than read: the source card's
    claims about rake, limps and realization are the only thing standing between a reader
    and a range that is thoroughly reported and wrong.
    """
    return [
        f"config field {field} is {config.get(field)!r}, ruled {expected!r}"
        for field, expected in RULED_CONFIG.items()
        if config.get(field) != expected
    ]
