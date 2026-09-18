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

**MAINT-34, 2026-09-16, adds `raise_mults_by_seat` and it is not a simplification of
`raise_mults`.** `raise_mults` is the re-raise TO-amount as a multiple of the current bet and
it applies at *every* re-raise level, so a global `[5.4]` would put the four-bet at
13.5 x 5.4 = 72.9, and `mults_of` at `crates/solver/src/preflop/mod.rs:97-102` feeds a clamp at
`:2219` that turns any raise at or above `allin_threshold * stack` - 67bb here - into a jam. The
sized four-bet would cease to exist and every three-bet-facing committed spot would become
fold/call/shove. The per-seat form gives the two blind seats 5.4 and leaves the other four on the
global 3.0, so the ladder is 2.5 / 13.5 / 40.5 / jam: a realistic blind three-bet with the
four-bet still a sized raise. An empty inner list means "use the global menu", which is the
solver's own convention. Seat order is the `positions` order, so index 4 is the small blind and
index 5 the big blind. `RE-SOLVE-THE-PREFLOP-CHART-WITH-A-REALISTIC-BLIND-THREE-BET`.

It is a `RULED_CONFIG` key rather than a field the extractor posts on the side, and that is
load-bearing: `config_errors` iterates `RULED_CONFIG.items()`, so a posted field this dict does
not name is invisible to the card check, the frozen config guards and the gate, and the export's
own origin would stop being checkable at exactly the field this task changed.

Copy this dict deeply if you intend to change a copy. `dict(RULED_CONFIG)` is shallow, so the
lists inside it - `positions`, `posts`, `open_raises`, `raise_mults` and now the per-seat menus -
are shared with every copy, and a caller that edits one in place silently rewrites the ruling for
the whole process. Nothing does that today; the hazard predates this field and is recorded here
because a per-seat menu is a nested list and the obvious way to build a variant is to reach in.

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
    "raise_mults_by_seat": [[], [], [], [], [5.4], [5.4]],
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
