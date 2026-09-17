# MAINT-34 independent review: the poker

## Reviewer independence

Read-only lane that wrote none of the work under review, and not the lane that reviewed
`tests/**`. Briefed on the poker rather than on the diff: whether the new ranges are better poker
measured against the artifacts, and whether anything in the repo still states the old ladder as a
live fact. Told that coming back empty with its checks named is a pass, and that a solved range is
not to be called a defect without a number attached.

Like the lock-diff round, this replaces a round lost with the coordinator session on 2026-09-17.

## Are the new ranges better poker? Yes, and every headline figure re-derives exactly.

Re-derived from the committed chart, the committed reference, and the pre-task chart pulled with
`git show 19beb97:...`. At `t6/d100/BB/BTN:raise@2.5` against `BB_vs_BTN_open`:

| | claimed old | measured | claimed new | measured | claimed ref | measured |
| --- | --- | --- | --- | --- | --- | --- |
| fold / call / 3-bet | 63.35/21.09/15.57 | 63.3474/21.0853/15.5673 | 62.67/24.41/12.91 | 62.6738/24.4135/12.9127 | 60.57/26.54/12.89 | 60.5672/26.5434/12.8895 |
| mixed classes | 3/169 | 3 | 9/169 | 9 | 40/169 | 40 |
| pairs in call branch | 12.0/78 | 12.00 | 39.9/78 | 39.87 | 43.4/78 | 43.39 |
| sets on `9c8c7c` | 0.00 | 0.0000 | 7.40 | 7.3995 | 8.34 | 8.34 |
| 3-bet bias on pairs | +0.4025 | +0.4025 | +0.0451 | +0.0451 | 0 | 0 |

No claim in the ExecPlan table failed to reproduce. The reference's own big-blind three-bet is
**13.5**, so the size this task chose is not a guess - it is the size the one outside standard in
this repo uses.

**One suspicion exonerated rather than filed.** The call branch still holds zero `TT+` at every
spot. So does the reference: `BB_vs_BTN_open` call weights read `AA` through `TT` at 0.00, `99` at
0.85, `88` at 1.00, `77` at 0.94. A capped top-of-flat is correct poker against a 13.5 three-bet and
is not a defect.

## BLOCKER, on the record rather than on the data

**The central claim is a one-spot measurement and is false at the heaviest of the five spots.**

Sets on `9c8c7c` in the big blind's call branch, of a possible 9, before and after, with each spot's
share of the 6,054,005,282 ppb of committed arrival:

| opener | before | after | pairs in call, of 78 | arrival share |
| --- | --- | --- | --- | --- |
| LJ | 6.56 | 9.00 | 43.12 -> 49.74 | 2.230% |
| HJ | 1.59 | 9.00 | 28.87 -> 53.18 | 2.126% |
| CO | 0.00 | 8.99 | 26.03 -> 47.98 | 2.083% |
| BTN | 0.00 | **7.40** | 12.00 -> 39.87 | 2.477% |
| **SB** | 0.00 | **0.00** | 11.52 -> 30.00 | **2.665%** |

At `t6/d100/BB/SB:raise@2.5` the chart raises every pair sevens and up at 1.00 and flats sixes and
below at 1.00, so no set reaches that call branch before the re-solve or after. The shape is
strictly better - the old chart raised `22` at 1.00 while flatting `44` and `33`, and that inversion
is gone - but the spot went *purer*, 7 mixed classes to 2, where the headline spot went 3 to 9.

This matters because phase 16 is halted on this task specifically so it can solve flops against this
branch, and the 99.94%-of-range continuation bet it is un-halting from was produced by exactly this
input. **The artifact ships; no route re-solves it. The record was what needed fixing**, and every
statement of the fix - the ExecPlan, `backlog.yml`, `docs/BACKLOG.md` - was taken at the button spot
alone and none of them said so. All now carry this table, and phase 16 is told to pick its flop
cells from it.

Also measured, and going the wrong way at one opener: against LJ the flat went 19.63 to 17.90
(reference 17.52) while the three-bet went 6.07 to 7.05 (reference 5.12). The three-bet got 80
percent more expensive and is used *more* often.

## BLOCKER, on the gate

**A mutation canary went vacuous and `check_gate_bite` fails until it is re-pinned.**
`a-spot-above-the-exposure-threshold-is-committed` moves the exposure threshold from 10.0 to 10.05
and rests entirely on one node sitting in that gap. It names
`t6/d100/BTN/HJ:raise@2.5,CO:call,BTN:call,SB:call,BB:raise@7.5` at 10.0234 - a key spelling a 7.5bb
blind three-bet, which this solve cannot emit. Measured on the shipped artifact the widest admitted
is 9.1945 and the narrowest refused 10.4362, so nothing at all sits in the gap: the mutation moves no
spot and `generate_derived_chart_report`, which the canary's own text calls its load-bearing entry,
exits 0 under it. Repaired under a dated scope widening; see the canary lane's own findings, which
include the fact that no pin can admit the 10.4362 node at all, because it is *also* a big-blind
squeeze spot and the exposure clause runs first.

## Non-blockers, fixed

- Three deferred backlog entries stated superseded figures as the current measurement, and the
  report cites one of them. `OPENING-RANGES-READ-NARROWER-THAN-A-RAKED-REFERENCE` carried the 7.5bb
  opening frequencies; re-measured, every seat tightened and the three negative gaps roughly
  tripled - HJ -0.085 to -0.348, CO -0.721 to -2.554, BTN -1.298 to -3.201 - so its own honesty
  calling HJ a tie no longer holds. `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED` rests on the
  global `[3.0]` this task replaced. `FOUR-BET-BLUFFS-ARE-CHOSEN-WITHOUT-BLOCKERS` cites 219
  three-bet-facing spots, now 135, and builds on a key the solve cannot emit.
- Two `src/**` docstrings stated the old ladder as a live structural fact, in
  `data_pipeline/self_play_reference.py` and `data_pipeline/comparison.py`. The second claimed both
  sample instances refuse with `committed-size-below-minimum-raise` at "the ruled four-bet at 22.5";
  re-measured, that code now fires **zero** times - the committed sample's refusals are exactly
  `lookup:spot-not-covered` 184 and `lookup:hand-class-not-covered` 10 - because decision 7 stopped
  committing the spots that produced both.
- The jam count is published twice with two values and no label, 33 against 34. Both are true of
  different things; decision 4's word is "offer", so 34 is the one its sentence wants.

## The finding that is nobody's defect and is filed rather than fixed

**Nobody has asked whether 40.5 is a good four-bet, and one of its two families is measured
nowhere.** The 66 committed spots priced at 40.5 split two ways: 40 where a non-blind answers a
blind's 13.5, which is 3.00x against the reference's 28.5 over the same 13.5, or 2.11x - so 40.5 is
42 percent over a standard price, not a quarter; and **26 where a blind cold-four-bets an
in-position 7.5**, hero BB at 16 and SB at 10, carrying 2.720 percent of committed arrival, priced
at 5.4x where the reference answering an 8bb three-bet raises to 21.5, or 2.69x. That second family
is priced at roughly double a standard four-bet and appears in no column of any committed report.
Route C was ruled on a sized four-bet **surviving** the clamp, never on it being priced like poker.
Filed into `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED` beside the geometry entry rather than
fixed, because it is structural for a per-seat multiplier and repairing it is another re-solve.

## Alignment items

- `gtopen_export_report.py` hardcodes "the bot still plays the committed 36-spot chart", two chart
  generations stale and predating this task. Regenerating does not fix it; the sentence is in the
  generator. Same class as the finding this whole task opened on, one level out.
- The chart over-defends badly against the **in-position** 7.5 three-bet, which this task did not
  touch: the opener calls 36 to 43 percent where the reference calls 11.5, and defends 49 to 57
  against roughly 32. The report names the shape but attaches a number only to the four-bet column.
  Same cause as the accepted over-folding - a realization model that cannot tell a 7.5 three-bet pot
  from a 13.5 one - so it belongs under
  `THE-PREFLOP-CHART-CANNOT-PRICE-A-FLAT-AGAINST-A-THREE-BET-AND-ITS-CALL-BRANCH-IS-NOISE`.

## What the reviewer was asked at the end, and answered

**What it did not look at.** `tests/**` and the freeze lock, which the other lane owned - except
`verification/mutations.yml`, read because a canary is a claim about the poker, and the gate blocker
above came out of it. It never unpacked the export, so the node census, the 160 zero-reach nodes and
the 128 unmeasurable spots are taken on the report's and the source card's word. Not the convergence
or determinism record, which needs the solver. Not phase 16's 99.94% c-bet, which is a postflop
solve in another worktree.

**Premises in the seven decisions it believes are now false.** Decision 1 materially: its success
test for route C is "the button's four-bet survives sized at 40.5", which is true, but it treats
*sized* as the property that matters and 40.5 is 3.00x where the reference is 2.11x. Decision 4 in
one word, the jam count reading. And a caveat rather than a falsification on decisions 2 and 7:
their verification clauses - "zero of the 160 would have been exposure-refused had the clause run
first", "every one of the 128 carries zero arrival" - are **unfalsifiable from the shipped
artifact**, because the spots they are about were removed from it. No reviewer working from the
committed chart can check them, and the only witness is the lane that made the claim. Decisions 3, 5
and 6 it found nothing against.
