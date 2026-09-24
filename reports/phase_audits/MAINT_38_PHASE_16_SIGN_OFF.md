# MAINT-38 audit packet: Taylor's phase 16 sign-off, written down

Phase 16 was merged, tagged `phase-16-complete` and `completed` in `phase_status.yml`, but its lane
pointer stayed at stage 11 with `loop: running`. It is `auto_advance: false` because it commits the
solution the bot plays postflop, and the review queue printed "sign off before the fleet moves past
phase 16". Taylor gave it on 2026-09-24. This task records it and closes the lane. It changes no
range, artifact, code or test.

## The sign-off

Taylor was shown that the shipped flop chart makes no flop bet in 20,000 self-play hands, because it
covers 3 boards on one preflop line and a refusal voids the hand; that more solving does not fix
flop-only scope, a ceiling of about three quarters of flops, or a gate that cannot judge poker. He
signed off: "we can say mission accomplished for this phase since we've extracted and stored
output." The review then found a figure he had been given was wrong (below); given the corrected
one, he answered "yes, i still sign off."

**Verdict: phase 16 signed off as shipped, on decision 25.** It rules on nothing the packet leaves
open.

## What shipped

- `reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md` gains `## Human sign-off`, 497 of 500 lines.
- Eighteen bullets the queue read as open blockers across eight phase 16 review notes are marked
  `[resolved]`, each note carrying one line that points at the audit.
- `verification/loop_runs/16.yml` reads `loop: completed`.
- Two backlog entries extended, one filed.

## The blocker audit

One read-only lane that wrote none of phase 16, note at
`reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`. Of the eighteen: twelve
were evidence bullets inside other findings, five were real blockers fixed but never marked, and one,
the c-bet cell, was closed by Taylor's decision 21 rather than a fix. None was open work. It also
found twelve blockers written as bold paragraphs that the parser never sees, all fixed with evidence
in their notes.

## Independent review

One read-only reviewer that wrote none of this, no gate runs, note at
`reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/review.md`.

- **Blocker, resolved.** Taylor was told the button would bet about one flop in 550 against a human
  big blind. The lookup keys on hero's seat and only one committed cell is hero on the button, so it
  is 4 of 22,100 flops, about 1 in 5,525, on the one covered line after a check. He was given the
  corrected figure and reaffirmed the sign-off.
- **Non-blockers, fixed.** The resolution line now covers paragraph blockers and the one ruling; the
  self-play backlog note says the node after the c-bet still refuses; the ExecPlan's voided-hand
  count matches decision 25 (5,365, against 822 on the fallback).
- **Alignment, filed.** `A-REFUSAL-AT-A-LIVE-TABLE-HAS-NO-DEFINED-ACTION`, owned by phase 20.

## Filed rather than fixed

- `REVIEW-QUEUE-COUNTS-EVIDENCE-BULLETS-AS-BLOCKERS`, extended: its second instance, and two shapes
  the known indent fix does not cover - a marker on a continuation line, and paragraph blockers.
- `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`, extended: part of the gap is
  self-play, and the button's coverage is 4 flops, not 40.
- `A-REFUSAL-AT-A-LIVE-TABLE-HAS-NO-DEFINED-ACTION`, new.

## Gate

First run red, 49 of 50: the ExecPlan's Delegation Plan lacked the fields `check_execplan_delegation`
requires once a lane is used. They were added. Second run green, 50 of 50, `check_gate_bite` reporting
79 mutations all caught.
