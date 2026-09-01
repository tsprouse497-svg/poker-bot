"""The one solve config this repo commits an export from, and the check that it was used.

Phase 10's decision 2 fixed it verbatim: six-handed, 100bb, 2.5bb opens, no limp,
rake-free, `realization: "calibrated"`, `allin_threshold: 0.67`. Phase 14 supersedes one
field of that ruling. Decision 14: `add_allin` is `False`, because `True` put a full-stack
jam on the raise menu at every node where a raise was legal, with no reference to the pot,
and genuine five-bet jams survive through `allin_threshold` instead. It lives in its own
module because both the export reader and the source card have to hold an export to it, and
neither of them owns the ruling.

`allin_threshold` is the one field GTOpen's own web form cannot set, which is why a human
verifies the committed export by loading the saved solve rather than by rebuilding from the
form.

**`realization` was moved to `"static"` on 2026-08-31 and moved back the same day. Read this
before proposing it again.** Decision 19 ruled `static` because `calibrated` prices every flop
terminal from 169 per-class numbers with no four-bet-pot cell, and applied at SPR 1.67 it folds
JJ at 40.8 percent equity into a 32.3 percent price while calling 76s at 29.6. That diagnosis
stands. The build it produced does not: measured on this tree, the big blind defends 76.31,
84.51, 91.46, 98.19 and **100.00** percent against the lojack, hijack, cutoff, button and small
blind, folding zero combos to a small-blind open. Phase 10 measured the same model at 72.94,
97.44 and 99.71 and its decision 2 ruled that nothing may be committed under it; GTOpen's own
author records the same comparison as "BB defends 50% vs 2.5x with textbook composition vs
static's junk-loving 94%" and ships `static` as a sensitivity-check dropdown rather than a
model. `raw` is `static` with the positional term removed as well.

**Decision 20, ruled by Taylor on 2026-08-31, is what settles it:** solve with `calibrated`,
which is right in the pot types its fit covers, and **refuse the four-bet-facing spots** rather
than commit cells the fit has no cell for. So the misprice is answered by what the chart
declines to answer, not by the realization field. Do not change this field to route around a
pricing defect - one field prices the whole tree, and the pot type it is wrong in is the one to
exclude. `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` carries the residual that ruling
accepts, and `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` the limitation it inherits.
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
