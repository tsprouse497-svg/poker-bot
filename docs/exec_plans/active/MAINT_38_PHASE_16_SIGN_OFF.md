# MAINT-38: Record Taylor's Phase 16 Sign-Off

- **Task** `MAINT_38_PHASE_16_SIGN_OFF`
- **Mode** `maintenance`
- **Branch** `maint/38-phase-16-sign-off`, worktree `~/projects/poker-bot-worktrees/maint-38`
- **Base** `2d90379296f36f3e04d719a2b43cb802d0bb3584`, which is `main`
- **Authorised by** Taylor, 2026-09-24, in session

## Objective

Phase 16 is merged, tagged `phase-16-complete` and `completed` in `phase_status.yml`, but its lane
pointer `verification/loop_runs/16.yml` sits at stage 11 with `loop: running`. It is
`auto_advance: false` in `verification/loop_policy.yml` because it commits the solution the bot plays
postflop, and `scripts/review_queue.py` prints "sign off before the fleet moves past phase 16".

Taylor gave the sign-off on 2026-09-24. This task writes it down and advances the lane to
`loop: completed`. The same queue also lists eighteen open-looking bullets under `## Blocker` across
phase 16's earlier review notes, which the stage-11 note did not see; advancing would drop them off
the board unexamined, so each is audited first.

## The sign-off, as given

Asked what he had to decide, Taylor was told the one ask was the sign-off, and that signing accepts a
flop chart that in the 20,000-hand self-play run makes no flop bet and voids 4,543 hands the old
fallback played to showdown. He asked which boards it does not bet on, and was told it is coverage
rather than a choice: 3 boards, 40 of 22,100 flops, one preflop line, and a refusal voids the hand
rather than checking. He then pointed out that as the button against a human big blind the bot does
not need the big blind's cell; that is right, and it means the self-play figure overstates the harm
at a real table, though at this coverage the bot would still bet about one flop in 550. He asked
whether renting compute to solve more makes this fine, and was told three things more solving does
not fix: flop only, a three-quarter ceiling on multiway flops, and a gate that cannot tell good poker
from bad. He answered "yea, i think it's fine then. we can say mission accomplished for this phase
since we've extracted and stored output", and then "ok, yes you can record signoff on phase."

So the verdict is: **phase 16 signed off as shipped, on decision 25.** It rules on nothing the
packet leaves open and on none of the eighteen blocker bullets below.

## Scope

Approved: phase 16's audit packet (one short section), phase 16's review notes (blocker bullets
marked resolved only where the audit shows the fix), this task's packet and review directory.
Standing scope covers `CURRENT_TASK.yml`, `backlog.yml`, `verification/loop_runs/**` and this plan.
Nothing under `data/`, `src/`, `tests/`, `scripts/` or `docs/phase_contracts/` changes.

## Delegation Plan

- No-delegation exception for the sign-off: it transcribes a ruling that exists only in this
  conversation, so a lane would be writing down what the coordinator told it.
- Lane A, blocker audit: one read-only subagent that wrote none of phase 16 classifies each of the
  eighteen bullets as not-a-finding, fixed-but-unmarked (with evidence), or still open, and writes
  `reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`. Status: completed.
  Of the eighteen, twelve were evidence inside other findings, five fixed but unmarked, one closed
  by Taylor's decision 21; none open. It also found twelve paragraph blockers the parser never
  sees, all fixed with evidence in their notes.
- Review handoff: one read-only reviewer that wrote none of this checks that the sign-off states no
  more than Taylor ruled, that every `[resolved]` mark matches the audit's evidence, that the packet
  stays under its 500-line cap, and that nothing outside scope moved. Status: not started.

## Slices

- [x] Activate MAINT-38 in `CURRENT_TASK.yml` with a dated scope entry.
- [x] Add the sign-off to phase 16's packet.
- [x] Blocker audit (lane A).
- [x] Mark the eighteen resolved with a pointer to the audit; none went back to Taylor.
- [x] Extend `REVIEW-QUEUE-COUNTS-EVIDENCE-BULLETS-AS-BLOCKERS` and
  `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN` with what this task found.
- [ ] Independent read-only review.
- [ ] `loop_stage.py --phase 16 --advance` to `loop: completed`.
- [ ] Gate, packet, closeout to idle, gate again, merge.

## Verification

`uv run python scripts/run_verify.py` and `uv run python scripts/check_scope.py`. Then
`scripts/loop_fleet.py` and `scripts/review_queue.py` from `main` show no phase 16 lane.

## Next Agent Bootstrap

Read this plan, then `blocker-audit.md` in the review directory. If lane A found any blocker still
open, the lane does not advance until Taylor rules on it.
