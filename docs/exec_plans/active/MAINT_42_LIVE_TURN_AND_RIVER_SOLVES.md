# MAINT-42: Solve The Turn And River At The Table

- **Task** `MAINT-42`
- **Mode** `contract-update`
- **Branch** `maint/42-live-turn-and-river-solves`, worktree `~/projects/poker-bot-worktrees/maint-42`
- **Base** `553f6f7931996c3feb4372a710a9845448f4c499`, which is `main`
- **Authorised by** Taylor, 2026-10-04, in session

## Objective

Taylor asked whether rivers must be solved and stored, since storing them multiplies the data. The
session measured single turn and river solves on GTOpen and showed him the numbers. He ruled to lift
the runtime-solver boundary for the turn and river: preflop and the flop stay committed offline
artifacts, the turn and river are solved at the table, and the river must answer within one second.
Moving a boundary is a semantic change, so this runs in `contract-update`. It changes the rule and
the documents that state it, and builds nothing.

## Taylor's rulings, 2026-10-04

1. **Lift the runtime-solver boundary for the turn and river.** Not for preflop or the flop.
2. **Do not store the turn or river.** No river rule of thumb is needed as the plan.
3. **Latency.** The turn at the 1.7 to 2.4 seconds measured is acceptable; the river under one
   second.

## Scope

Approved: `AGENTS.md`, both roadmaps, `docs/GTOPEN_SOLVER_NOTES.md`, and this task's packet and
review directory. Standing scope covers `CURRENT_TASK.yml`, `backlog.yml`, the generated documents
and this plan. Nothing under `data/`, `src/`, `tests/` or `scripts/` changes, and no phase contract
changes: the non-goals of phases 18, 19 and 20 that forbid adding runtime solver calls are scope
limits on those phases, and moving them belongs to whichever task declares the owning phase.

## Delegation Plan

- No-delegation exception: the edits transcribe a ruling made in this conversation, and figures the
  coordinator measured in it, into four documents and one backlog entry that must agree with each
  other. A lane would be writing down what the coordinator told it.
- Review handoff: one read-only reviewer that wrote none of this checks that the new boundary says
  exactly what Taylor ruled and no more; that every figure in it is true of the measurement rows in
  the packet; that no live document still calls the boundary permanent without the exception; that
  the backlog entry's six questions are real and complete, and in particular that phases 18 to 20
  really do forbid the work; and that nothing anticipates building it. Asked also what it held back.

## Slices

- [x] Activate MAINT-42 with a dated scope entry.
- [x] Amend the boundary in `AGENTS.md`.
- [x] Record the turn and river timings in `docs/GTOPEN_SOLVER_NOTES.md`, and correct its two
  statements that turn and river roots were never run.
- [x] Correct both roadmaps.
- [x] File `LIVE-TURN-AND-RIVER-SOLVING`.
- [x] Independent read-only review: one blocker (an unruled network condition, removed and filed as
  a question for Taylor), ten non-blockers of which four were confirmations, one alignment item
  already filed; round 2 clear.
- [ ] Gate, packet, closeout to idle, gate again, merge, push.

## Verification

`uv run python scripts/run_verify.py`, read for its verdict rather than its exit code, and
`uv run python scripts/check_scope.py`.

## Outcome

Pending review and gate.

## Next Agent Bootstrap

Work in `~/projects/poker-bot-worktrees/maint-42`. The edits are done; the open slices are the
review and the gate. Run the review, fix what it finds, write the packet at
`reports/phase_audits/MAINT_42_LIVE_TURN_AND_RIVER_SOLVES.md`, then the gate.
