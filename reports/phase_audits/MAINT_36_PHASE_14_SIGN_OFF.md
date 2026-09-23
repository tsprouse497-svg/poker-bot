# MAINT-36 audit packet: Taylor's phase 14 sign-off, written down

Phase 14 was merged, tagged `phase-14-complete` and `completed` in `phase_status.yml`, but its lane
pointer stayed at stage 11 with `loop: running`. It is `auto_advance: false` because it commits the
chart the bot plays, and the stage-11 review held it on one blocker: no human sign-off was recorded.

Taylor gave it on 2026-09-22. This task records it and closes the lane. It changes no range, price,
artifact, code or test.

## The sign-off

Asked what was needed, Taylor said the content had already been decided, and the record agrees: on
2026-09-05 he ruled to publish and ship the chart rather than re-solve it, and on 2026-09-06 he made
the narrow opening ranges the fifth accepted defect. The one open item was decision 36, the four-bet
size, ruled fixed on a wrong claim and shipped as defect 4. Asked whether it could stay a known,
deferred defect for now, he said "yea, i'm fine with that."

**Verdict: phase 14 signed off as shipped, all five accepted defects standing, decision 36 settled
as deferred.** The question named phase 14's own 22.5bb four-bet and nothing else.

## What shipped

- `reports/phase_audits/PHASE_14_CHART_CUTOVER.md` gains `## Human sign-off` at its foot, where
  `docs/DEFINITION_OF_DONE.md` puts a human verdict. Four lines, 499 of 500.
- The stage-11 note's one blocker is marked `[resolved]` and points at that section.
- `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED` records the ruling, scoped to the 22.5bb four-bet.
- `verification/loop_runs/14.yml` reads `loop: completed`.
- The merged `phase-14` worktree is removed so its own stale pointer, still `running`, leaves the
  fleet board. The branch stays.

## Independent review

One read-only reviewer that wrote none of this, no gate runs, note at
`reports/phase_audits/reviews/MAINT_36_PHASE_14_SIGN_OFF/review.md`.

- **Blocker, resolved.** The first backlog note said Taylor accepted "the four-bet size". Since
  MAINT-34 the shipped chart prices four-bets three ways, and the question named only phase 14's
  22.5bb one. The 40.5bb four-bet and a blind's cold four-bet at 5.4x, about double standard, were
  never put to him. The note and the ExecPlan now say so, and the reviewer marked it resolved.
- **Non-blockers.** `docs/BACKLOG.md` needed regenerating, done. The stage-11 resolution named a
  review before one existed; it exists now. Four lines elsewhere still say decision 36 is "back with
  Taylor" or "pending Taylor"; they are snapshots and stay as written, and the packet's own foot
  corrects the one in it.
- **Held back, then asked.** Decision 36 sat unasked for three weeks because a pre-filled default
  with "(pending Taylor)" beside it read as answered.

## Filed rather than fixed

- `BLIND-COLD-FOUR-BET-PRICED-AT-DOUBLE-STANDARD-IS-UNRULED`, new: the 5.4x price is unruled, in
  no report, and owed to Taylor as its own question.
- `PHASE-AUDIT-PACKET-AT-ITS-LINE-CAP`: phase 14's packet is the second one at 499 of 500.
- `PRE-FILLED-ANSWER-HIDES-AN-ITEM-FROM-THE-PAUSE-BOARD`: decision 36 is its second instance.

## Gate

First run red, 46 of 50: the review note cited the id it proposed for the pre-filled-answer finding,
which had been folded into an existing entry rather than created, so `backlog integrity` failed and
three commands failed with it. The citation now names the entry it was folded into. Second run green,
50 of 50, `check_gate_bite` reporting 78 mutations all caught.

## What was not checked

No poker was re-judged. The chart, its five defects and every frequency are phase 14's and were
not re-derived here.
