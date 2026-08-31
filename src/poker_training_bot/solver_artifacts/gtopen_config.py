"""The one solve config this repo commits an export from, and the check that it was used.

Phase 10's decision 2 fixed it verbatim: six-handed, 100bb, 2.5bb opens, no limp,
rake-free, `realization: "calibrated"`, `allin_threshold: 0.67`. Phase 14 supersedes two
fields of that ruling. Decision 14: `add_allin` is `False`, because `True` put a
full-stack jam on the raise menu at every node where a raise was legal, with no reference
to the pot, and genuine five-bet jams survive through `allin_threshold` instead. Decision 19,
ruled by Taylor on 2026-08-31: `realization` is `"static"`, because `calibrated` prices every
flop terminal from 169 per-class numbers fitted only on single-raised and three-bet pots -
GTOpen's own fitter has no four-bet cell - and applied unchanged at SPR 1.67 it folds JJ at
40.8 percent equity into a 32.3 percent price while calling 76s at 29.6. It lives in its own
module because both the export reader and the source card have to hold an export to it, and
neither of them owns the ruling.

`allin_threshold` is the one field GTOpen's own web form cannot set, which is why a human
verifies the committed export by loading the saved solve rather than by rebuilding from the
form.

**What decision 19 owes a measurement, stated here because this is the field that carries
it.** `realization` is absent from the config body in `docs/GTOPEN_SOLVER_NOTES.md`, so every
run before phase 10's probe took its default - and the default is `static`. Phase 10 measured
that default, same tree and same target with only this field changed, and found a big blind
defending **99.71** percent against a small-blind open, 97.44 against a button open and 72.94
against the lojack, against 49.03, 36.88 and 27.19 under `calibrated`. Its decision 2 ruled in
those words that nothing may be committed under the default. Decision 19 was ruled on the
four-bet pots, where `static` has no per-class term to get backwards; it does not address the
single-raised pots, where phase 10 found that term load-bearing. One field decides both, so
the big-blind defence figures are re-measured on this build and read by a human before
anything derived from it is committed.
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
    "realization": "static",
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
