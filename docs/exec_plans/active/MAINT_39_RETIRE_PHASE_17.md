# MAINT-39: Retire Phase 17

- **Task** `MAINT_39_RETIRE_PHASE_17`
- **Mode** `contract-update`
- **Branch** `maint/39-retire-phase-17`, worktree `~/projects/poker-bot-worktrees/maint-39`
- **Base** `65e87d28aaec6a7a19643e0864c8adbc717f7f50`, which is `main`
- **Authorised by** Taylor, 2026-09-25, in session

## Objective

Phase 17, The Corpus Verdict On The Committed Chart, was to re-run the real-hand comparison against
the committed chart and say whether the calling gap is rake, price, or a defect in the ranges. Taylor
was told what it measures and that phase 18 measures how well the bot plays, and ruled: "idc what real
people do. you can remove it." He also approved keeping the lane's branch under a tag and removing its
worktree.

Deleting a contract and a phase is a semantic contract change, so this runs in `contract-update`, the
same shape MAINT-35 used to retire phase 15.

## Scope

Approved: the phase 17 contract (deleted), phase 14's contract (one in-place amendment, since it sits
at its 300-line cap), both roadmaps, `verification/loop_policy.yml`, the derived-chart report
generator's prose, and this task's packet and review directory. Standing scope covers
`phase_status.yml`, `backlog.yml`, the generated documents and `reports/active/**`. Nothing under
`data/`, `src/` or `tests/` changes.

## Delegation Plan

- Worker lanes: none for the edits. They are coordinator-owned because each one transcribes a ruling
  that exists only in this conversation, or re-homes a backlog entry on a reading of that ruling, and
  the whole set is under a hundred lines of prose across files that must agree with each other; a lane
  would be writing down what the coordinator told it.
- Ownership: the coordinator owns every changed path; the reviewer owns
  `reports/phase_audits/reviews/MAINT_39_RETIRE_PHASE_17/independent-review.md`.
- Expected outputs: phase 17 absent from `phase_status.yml`, loop policy and the contracts; no backlog
  entry filed against it; no live document saying a phase renders the corpus verdict; the lane's
  findings that do not depend on it carried to `main`.
- Status: edits done. Seven entries re-homed, four of the lane's own findings carried, one
  retirement entry and one alignment item filed.
- Integration order: edits, then review, then fixes, then the gate, then closeout.
- Review handoff: one read-only reviewer that wrote none of this, briefed with no gate runs, checks
  that nothing still points at phase 17 as live, that each re-homed entry's new label fits what it
  asks for, that every figure and claim in the retirement entry is true of the tree, and that the
  phase 14 amendment keeps the contract inside its cap. Status: pending.

## Slices

- [x] Activate MAINT-39 in `CURRENT_TASK.yml` with a dated scope entry.
- [x] Delete the contract; remove the phase from `phase_status.yml` and loop policy.
- [x] Amend phase 14's contract in place; fix both roadmaps; fix the derived-chart report's prose.
- [x] Re-home the seven entries; carry four lane findings; file the retirement entry.
- [x] Tag the lane tip `7e0dd71` as `retired/phase-17`.
- [ ] Independent read-only review.
- [ ] Gate, packet, closeout to idle, gate again, merge, push.
- [ ] Remove the phase 17 worktree and its local branch; the tag keeps the commits.

## Verification

`uv run python scripts/run_verify.py` and `uv run python scripts/check_scope.py`. Then
`scripts/loop_fleet.py` from `main` shows no phase 17 lane.

## Next Agent Bootstrap

Read `THE-CORPUS-VERDICT-PHASE-IS-RETIRED` in `backlog.yml` for what moved and where the lane's work
is kept. Open slices are listed above; nothing here needs Taylor.
