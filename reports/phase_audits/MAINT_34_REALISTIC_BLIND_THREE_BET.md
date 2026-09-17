# MAINT-34 audit packet: a realistic blind three-bet

- **Task** `MAINT_34_REALISTIC_BLIND_THREE_BET`, mode `contract-update`
- **Branch** `maint/34-realistic-blind-three-bet`, base `19beb97` on `main`
- **Authorised by** Taylor, 2026-09-16, as phase 16's decision 19, filed as
  `RE-SOLVE-THE-PREFLOP-CHART-WITH-A-REALISTIC-BLIND-THREE-BET`

## What shipped

The committed preflop chart is re-solved with `raise_mults_by_seat`, giving the two blind seats a
5.4 multiplier and everyone else the global 3.0. The blinds' three-bet against a 2.5bb open goes
from 7.5bb to 13.5bb, which is the size the repo's one outside reference uses at the same spot.

The reason this is not a preflop cosmetic: the big blind's **call** branch is the whole
out-of-position input to every postflop solve, and at 7.5bb it held no set and no overpair. Phase 16
solved a real flop against it and hero's continuation bet came out at 99.94% of range.

## The measurement, and the spot it is taken at

At `t6/d100/BB/BTN:raise@2.5`, committed 7.5bb then re-solved 13.5bb then the committed reference:
fold/call/3-bet 63.35/21.09/15.57 → 62.67/24.41/12.91 against 60.57/26.54/12.89; genuinely mixed
classes 3 → 9 of 169 against 40; pocket pairs in the call branch 12.0 → 39.9 of 78 against 43.4;
sets on `9c8c7c` 0.00 → 7.40 combos against 8.34; three-bet bias on pairs +0.4025 → +0.0451
against 0. The independent poker review re-derived every one of these from the artifacts and all
reproduced to the digit.

**It is one spot of five, and the fix is not uniform.** Sets on `9c8c7c` in the big blind's call
branch, of a possible 9, before and after, with each spot's share of the 6,054,005,282 ppb of
committed arrival: LJ 6.56 → 9.00 (2.230%); HJ 1.59 → 9.00 (2.126%); CO 0.00 → 8.99 (2.083%);
BTN 0.00 → **7.40** (2.477%); **SB 0.00 → 0.00 (2.665%)**. The spot the fix does not reach is the
heaviest of the five: at `BB/SB:raise@2.5` the chart raises every pair sevens and up and flats sixes
and below, so no set reaches that call branch either side of the re-solve. The shape is still
strictly better - the old chart raised `22` while flatting `44` and `33` - but that spot went purer,
7 mixed classes to 2, where the headline spot went 3 to 9.

**Phase 16 picks its flop cells from that table, not from the headline**, and a c-bet frequency
measured at BB-versus-SB is not evidence about this fix in either direction.

## What the chart now costs, stated rather than buried

- Committed spots go 284 to **156** under decision 7, which refuses every spot where the multiway
  exposure guard could not measure its own input. All 128 refused carry zero arrival, so the
  coverage cost is 0 ppb.
- The four-bet is three prices, not one: 22.5 at 28 committed spots, 40.5 at 73 and hero's whole
  stack at 34, counting menus. Counting only spots where an arriving class takes the price, 40.5 is
  66 and the shove 33, the difference being 8 spots whose menu names a raise nobody takes.
- 34 spots offer hero nothing but a jam, SB 29 and BB 5, all answering the other blind's 13.5:
  13.5 × 5.4 = 72.9, above the solve's own 67 all-in threshold, clamped to the stack. Accepted by
  Taylor as decision 4.
- The big blind still over-folds, 36.65% to 37.33% against a rake-free band of roughly 40 to 65, and
  the realization model is still blind to stack-to-pot ratio.
- **Every opening range tightened and the three that read narrower than a raked reference got
  worse**: HJ -0.085 → -0.348, CO -0.721 → -2.554, BTN -1.298 → -3.201. Correct solver behaviour - a
  bigger blind three-bet makes opening less profitable - but it moves further in the one direction
  the rake argument cannot explain. The accepted-defect ruling is unchanged.

## Independent review

Two read-only lanes, neither of which wrote any of the work, and neither of which was the other.
Full notes in `reports/phase_audits/reviews/MAINT_34_REALISTIC_BLIND_THREE_BET/`.

**Both rounds were run twice.** The coordinator session was lost on 2026-09-17 with both reviewers
in flight and their findings unwritten. Nothing of the first round survives and nothing of it is
claimed here; both were re-dispatched from the same briefs.

**`tests/**` and the re-freeze - no blockers.** Roughly 60 pinned values recomputed from the
artifacts rather than read back. No test function deleted, no tolerance moved, and the one bound
that changed got tighter. Nine non-blockers, all fixed, the two worth naming being a test whose own
*name* still said 284 spots, and decision 6's authorised deletion leaving nothing anywhere that
compared the committed card's `achieved_gap_bb` to its own `target_gap_bb` - a solve that stopped
short of its declared accuracy would have shipped with the card saying so in a field no test read.

**The poker - two blockers, both fixed, neither on the data.**

1. The central claim was a one-spot measurement published as though it were general. Fixed in the
   record: the per-spot table above now sits in the ExecPlan, `backlog.yml` and this packet. No
   route re-solves it and the artifact ships as measured.
2. `a-spot-above-the-exposure-threshold-is-committed` had gone vacuous. It moves the exposure
   threshold 10.0 → 10.05 and named a node at 10.0234 whose key spells a 7.5bb blind three-bet this
   solve cannot emit; measured today the widest admitted is 9.1945 and the narrowest refused
   10.4362, so nothing sat in the gap and `generate_derived_chart_report`, which the canary calls
   its load-bearing entry, exited 0 under it. Re-pinned at **11.4**, admitting exactly
   `t6/d100/SB/HJ:raise@2.5,SB:call,BB:raise@13.5,HJ:call` at 11.3681, verified by re-running the
   selection: 157 committed, one spot added, none removed. Under a dated scope widening for
   `verification/mutations.yml`.

   **The obvious pin would have been vacuous too, and the lane said so rather than shipping it.**
   The coordinator's brief asked for a value just above the narrowest refused. That node is *also* a
   big-blind squeeze spot and `exclusion_code` runs exposure before squeeze, so any threshold that
   stops refusing it there simply hands it to clause three and the committed set does not move. No
   pin can ever admit it. Four further mutations were found carrying 7.5bb or 249-spot figures and
   re-measured - one claimed 2,207 spots move where the real number is 599.

## The recurring defect this task hit again, twice

`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`. Phase 14's contract requires the report
generator to re-derive every figure it names and forbids a hand-typed count, and the generator still
carried nine of them. The price ladder, the exposure margin ("sixteen hundredths of a point" where
the measured margin is 1.2417), the ledger's sized-raise split, the corpus section's spot count and
the jam section's figures are all derived now, and the ladder prints **both** readings side by side
so the 8 empty-price spots are visible rather than absorbed.

A coordinator misdiagnosis is recorded here because it is the same disease: the ladder was called a
mix of two readings on the strength of a reconstruction from spot-key text, which defaults a
first-in spot to a faced price of 2.5 and is simply wrong. The lane measured hero's menu from the
export's own action labels and the printed table matched it on every row. What was actually wrong
was that the figures were literals and the 8 spots were invisible.

## One dead check, made live

The jam-inversion canary printed `AA jams 0.00` under a sentence reading "the check working". The
node it walked to has a menu of `(fold, call)` - the small blind has already shoved and hero has no
jam to take - and `_menu_weights` answers 0.0 for a class with reach at a node carrying no jam
action, so nothing noticed. The walk now requires the node to offer hero a jam and reads
`t6/d100/SB/BTN:raise@2.5,SB:raise@13.5,BTN:raise@40.5  AA jams  100.00`. The frozen test passed
either way, asserting only `0.0 <= weight <= 100.0`; it now asserts strictly above zero, because a
zero there is the failure rather than a value in range. Pre-existing at `main`, report-only,
runtime-reversible.

## A second dead canary, found by the gate itself

The first full gate run came back `all_passed: False` behind a zero exit code, and one of the two
failures was `check_gate_bite` reporting that
`the-derived-chart-report-renders-whatever-it-is-handed` survived `pytest_derived_chart`. That
mutation replaces the one branch deciding whether a refused figure is published anyway with
`if False:`, and it is killed by
`test_a_wrong_artifact_fails_the_command_rather_than_being_rendered`, which feeds the command two
artifacts that load cleanly and are wrong.

**The test could not tell a refusal from a crash.** It asserted only a non-zero exit and no report
on disk. Under the mutation the command no longer refuses - it runs on and dies in a traceback
further down, which exits non-zero and writes no report, so both assertions passed and the mutation
lived. Verified by applying the mutation in place, running the two cases, and restoring the file
byte for byte against a copy taken first.

The test now asserts the **reason**: `refused:` in stderr and no `Traceback`. Re-verified under the
mutation, both cases go red. The file was at the 700-line cap with no headroom, so the
corrupted-artifact builder was extracted to `tests/corrupted_artifacts.py` rather than compressing
anything already there - the ninth cap-forced extraction in this repo.

This is the same shape as the jam canary above and as the exposure canary: a check that reports a
pass while measuring nothing. Three of them in one task.

## Filed rather than fixed

**Nobody has asked whether 40.5 is a good four-bet, and one of its two families is measured
nowhere.** The 66 spots priced at 40.5 in the sizing table split 40 where a non-blind answers a
blind's 13.5 - 3.00x against the reference's 2.11x, so 42 percent over a standard price rather than
a quarter - and **26 where a blind cold-four-bets an in-position 7.5**, hero BB at 16 and SB at 10,
carrying 2.720% of committed arrival, priced at **5.4x** where the reference answering an 8bb
three-bet raises 2.69x. That family appears in no column of any committed report. Route C was ruled
on a sized four-bet **surviving** the clamp, never on it being priced like poker. Filed into
`PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`, which is retitled, since its own diagnosis - the
global `raise_mults: [3.0]` - is what this task replaced.

## What no reviewer could check

Decisions 2 and 7 rest on claims about nodes the artifact no longer contains - "zero of the 160
would have been exposure-refused had the clause run first", "every one of the 128 carries zero
arrival". Those are unfalsifiable from the shipped chart, because the spots they are about were
removed from it. The only witness is the lane that made the claim. Recorded rather than resolved.
