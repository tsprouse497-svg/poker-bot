# MAINT-45 audit packet: phase 18 narrowed, phase 20 left open on purpose

Two rulings from Taylor on 2026-10-05, both recorded before the phases they shape start. It changes
no range, artifact, code path or test.

## What shipped

- **Phase 18, The Yardstick, stays but narrower.** Offered three options (narrower, retire, keep as
  written) he answered "1": the solve is taken as good play, and the phase measures only what the
  bot's departures from it cost, in chips per 100 hands with error bars. The skeleton's opponent pool
  and exploitability figure are dropped. Its contract lists the departures as the coordinator's
  reading: refusals on any street (which void the hand, so how to price them is stage 1's), the
  check-fold postflop fallback, off-menu faced bets refusing, prices the tree does not hold answered
  from the solved price, and the chart's merge of a cold call into the raise. It states the lean that
  the solve is also the opponent, and that lean's three limits.
- Both roadmaps, the loop-policy reason, phase 19's contract (one phrase that named the dropped pool)
  and three phase 18 backlog entries follow.
- **Phase 20, The Home Game, is intentionally left open.** His words: "keep this open ended now and
  not commit to anything", and "make it clear it's intentionally left open". Its contract and the
  loop-policy reason the review queue prints now say so, and that it cannot start before 19 and 22.
- The queue's own count still lists phase 20 as waiting on him, because it ignores dependencies.
  That is code and out of scope; filed as
  THE-REVIEW-QUEUE-LISTS-A-PHASE-WHOSE-DEPENDENCIES-ARE-NOT-MET-AS-WAITING-ON-YOU.

## How to check it without code

Read phase 18's Scope and compare it with the option he picked. Read the first line of phase 20's
reason in `verification/loop_policy.yml`.

## Independent review

Two rounds by read-only reviewers that wrote none of this. Notes in
`reports/phase_audits/reviews/MAINT_45_NARROW_THE_YARDSTICK/`.

- **Round one: one blocker, fixed.** Phase 19's contract gated a rule on "the phase 18 pool".
  Non-blockers fixed: the departure list was wrong in two places (a preflop refusal voids the hand
  rather than check-folding; an off-menu bet refuses rather than snapping) and missed the cold-call
  merge and ruling 8's reach; the lean's limits were unstated. Two more backlog entries got notes.
- **Round two: no blocker.** Three wording fixes folded in; the queue gap filed.
- **Held back by the reviewers:** no count of how many refusals are four-bet against multiway, no
  count of ladder violations on merged spots, the queue board inferred from code rather than run.

## Gate

Green, 50 of 50, `check_gate_bite` included, on the review fixes and this packet. The closeout
edits are covered by the closeout gate.
