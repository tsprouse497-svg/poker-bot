# MAINT-37: The Fleet Board Trusts Main's Copy Of A Lane Pointer

- **Task** `MAINT_37_MAIN_POINTER_WINS`
- **Mode** `maintenance`
- **Branch** `maint/37-main-pointer-wins`, worktree `~/projects/poker-bot-worktrees/maint-37`
- **Base** `f6dfe0175ccf7d5019e7706d9ae4cfb94c987d44`, which is `main`
- **Authorised by** Taylor, 2026-09-22, in session

## Objective

After MAINT-36 set `verification/loop_runs/14.yml` to `loop: completed` on `main`,
`scripts/loop_fleet.py` still listed phase 14 as running nine times, and `scripts/review_queue.py`
repeated every phase-14 ask once per copy. Every worktree that branched or rebased after phase 14
merged carries its own copy of that pointer at the older `running`, and `loop_fleet.lanes()` keys
lanes on `(phase_id, worktree)`, so each copy is a lane.

`AGENTS.md` already says only the tree holding `main` describes the repo. The rule this task adds to
`lanes()`: **when the worktree on `main` holds a pointer for a phase, that copy is the only one that
counts for that phase.** A completed pointer there retires the phase from the board everywhere; a
live one there is listed once, from `main`. A phase whose pointer is not on `main` - a lane that has
not merged - is read from its own worktree exactly as today.

Why this rule and not "drop a phase that is `completed` in `phase_status.yml`": phase 14 was
`completed` there for weeks while its stage-11 sign-off was still owed, and that rule would have
hidden the ask, which is the failure the stage-11 review warned about. The pointer on `main` moves
only when the loop really advances.

Not in scope: `loop_stage.run_paths()` counting completed pointers, and what a finished pointer is.
Those are the ruling `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` and `LOOP-LANE-POINTERS-NEVER-RETIRE`
ask for and stay deferred.

## Scope

Approved: `scripts/loop_fleet.py`, `tests/test_loop_fleet.py`, `verification/freeze.lock`,
`verification/mutations.yml`, `docs/LOOP.md`, this task's packet and review directory. Nothing under
`data/`, `src/` or `docs/phase_contracts/`.

## Delegation Plan

- Worker lanes: one implementation worker, `impl`, writes the change to `lanes()`, the tests, the
  mutation canary, the `docs/LOOP.md` sentence and the re-frozen lock.
- Ownership: `impl` owns the five implementation paths. The coordinator owns `CURRENT_TASK.yml`,
  `backlog.yml`, this plan, the packet, integration and the gate.
- Expected outputs: an uncommitted diff in the maint-37 worktree plus the commands it ran and what
  each printed.
- Status: planned.
- Integration order: coordinator reads the diff against the artifact rather than the worker's report,
  runs the fast checks, then hands to review.
- Review handoff: one read-only reviewer that wrote none of it, no gate runs. It must check that the
  rule matches the objective, that an unmerged lane is untouched, that existing tests were not
  weakened, that the canary really reddens the new tests, and that the board from `main` shows no
  phase 14 lane.

## Slices

- [ ] Activate MAINT-37.
- [ ] `impl`: rule, tests, canary, doc, lock.
- [ ] Coordinator integration and fast checks.
- [ ] Independent read-only review.
- [ ] Gate, packet, closeout, gate, merge.

## Verification

`uv run python scripts/run_verify.py`. After merge, `scripts/loop_fleet.py` and
`scripts/review_queue.py` from `main` list no phase 14 lane and no phase 14 ask.

## Outcome

Filled in at closeout.

## Next Agent Bootstrap

Read `CURRENT_TASK.yml` in the maint-37 worktree and the slices above; the first unchecked one is
next. The rule is fixed by the objective; do not widen it into retiring pointers.
