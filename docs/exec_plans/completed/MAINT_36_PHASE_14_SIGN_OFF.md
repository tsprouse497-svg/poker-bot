# MAINT-36: Record Taylor's Phase 14 Sign-Off

- **Task** `MAINT_36_PHASE_14_SIGN_OFF`
- **Mode** `maintenance`
- **Branch** `maint/36-phase-14-sign-off`, worktree `~/projects/poker-bot-worktrees/maint-36`
- **Base** `40b53f6898e43ee9a11706ccb7a0b76275724a13`, which is `main`
- **Authorised by** Taylor, 2026-09-22, in session

## Objective

Phase 14 is merged, tagged `phase-14-complete` and `completed` in `phase_status.yml`, but its lane
pointer `verification/loop_runs/14.yml` sits at stage 11 with `loop: running`. It is
`auto_advance: false` in `verification/loop_policy.yml` because it commits the chart the bot plays,
and the stage-11 review (`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-11-advance.md`)
holds the stage on one blocker: the human sign-off is recorded nowhere.

Taylor gave it on 2026-09-22. This task writes it down, releases the blocker and advances the lane
to `loop: completed`.

## The sign-off, as given

Asked what was needed to sign off phase 14, Taylor said the content had already been decided. That
is true of the record: on 2026-09-05 he ruled to publish and ship the chart rather than re-solve or
soften it, and on 2026-09-06 he added the narrow opening ranges as the fifth accepted defect. The
one item the packet itself says is "back with Taylor" is decision 36, the four-bet size, which he
ruled fixed on a coordinator statement that turned out wrong and which ships as accepted defect 4
under `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`. Put to him directly - leave the four-bet as a
known, deferred defect for now - he answered "yea, i'm fine with that."

So the verdict is: **phase 14 signed off as shipped, all five accepted defects standing, decision 36
settled as deferred rather than fixed.** The question named phase 14's own four-bet, 22.5bb, and
nothing else. The two four-bet prices MAINT-34 introduced after phase 14 - 40.5bb, and a blind's
cold four-bet at 5.4x - were not put to him and this sign-off does not rule on them; the review
filed them as their own unruled item.

## Scope

Approved: phase 14's audit packet (one short section), the stage-11 review note (the blocker marked
resolved), this task's packet and review directory. Standing scope covers `CURRENT_TASK.yml`,
`backlog.yml`, `verification/loop_runs/**` and this plan. Nothing under `data/`, `src/`, `tests/`
or `docs/phase_contracts/` changes.

## Delegation Plan

- No-delegation exception: the implementation is transcribing a ruling Taylor gave in this session
  into three files, and the ruling exists only in this conversation. A lane cannot see it, so a lane
  would be writing down what the coordinator told it, which adds a relay and no check. The check
  that is owed is the independent review below.
- Review handoff: one read-only reviewer that wrote none of this, with no gate runs. It must
  inspect that the sign-off states no more than Taylor ruled, that the packet stays under its
  500-line cap, that the stage-11 blocker is the only thing marked resolved, that the backlog note
  on decision 36 matches the packet, and that nothing outside approved and standing scope moved.
- Status: review completed, one blocker found and resolved; see `reports/phase_audits/reviews/MAINT_36_PHASE_14_SIGN_OFF/review.md`.

## Slices

- [x] Activate MAINT-36 in `CURRENT_TASK.yml` with a dated scope entry.
- [x] Add the sign-off to phase 14's packet.
- [x] Mark the stage-11 blocker resolved, citing the packet line.
- [x] Note on `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED` that Taylor accepted it as deferred.
- [x] Independent read-only review.
- [x] `loop_stage.py --phase 14 --advance` to `loop: completed`.
- [x] Gate, packet, closeout to idle, gate again, merge.
- [ ] Remove the merged `phase-14` worktree so its stale pointer leaves the fleet board.

## Verification

`uv run python scripts/run_verify.py` and `uv run python scripts/check_scope.py`. Then
`scripts/loop_fleet.py` and `scripts/review_queue.py` from `main` show no phase 14 lane.

## Outcome

Phase 14's sign-off is recorded in its packet under `## Human sign-off`, the stage-11 blocker is
resolved, and `verification/loop_runs/14.yml` reads `loop: completed`. The independent review found
one blocker - the backlog note stretched the ruling past the 22.5bb four-bet Taylor was asked about -
fixed and marked resolved by the reviewer. The gate was red once on a dangling id in the review note
and green at 50 of 50 after it was repointed. Three items filed; see the audit packet.

## Next Agent Bootstrap

Closed. Nothing is owed here. The next ask this task created is
`BLIND-COLD-FOUR-BET-PRICED-AT-DOUBLE-STANDARD-IS-UNRULED`, which needs a report row and then
Taylor's ruling; do not treat phase 14's sign-off as covering it.
