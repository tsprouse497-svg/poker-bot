# MAINT-27: an agent is told to read state out of whichever tree it woke up in

Task: `maint-locate-the-live-lane`. Mode: `maintenance`. Base: `ada5205`.

## Objective

Fix the Start Of Work step that has handed four sessions a wrong answer about where the repo
stands, and file the half of the defect no committed change can reach.

## How it was found

A session was asked which stage the repo was on. It followed `AGENTS.md` step 1, read
`CURRENT_TASK.yml` in its own working directory, read `phase_status.yml` beside it, and reported
the repo idle with phase 10 the newest completed phase and phase 11 unstarted. Main holds phases
11, 12 and 13 completed and phase 14 live at stage 4 in its own tree.

That directory was `~/projects/poker-bot`, the primary checkout, parked on the merged
`phase/10-solver-extraction` branch. The same wrong answer was given on 2026-08-20 and again on
2026-08-24, each time from the same tree and each time corrected by the operator.

## What is actually broken

Three things, and only one of them can be fixed in the repo.

`AGENTS.md` step 1 was written when the repo was one shared tree, and it still says "Read
`CURRENT_TASK.yml`" with no way to tell whose state that is. Under parallel lanes the answer to
"where are we" lives in three places at once, and the two files that read most like the answer
are the two that mislead hardest: `CURRENT_TASK.yml` reads `idle` in every tree whose own task
closed, and `verification/loop_state.yml` - whose name says it holds the loop's state - has said
phase 10, stage 11, `completed` in every tree since August. `docs/LOOP.md` documents
`scripts/loop_fleet.py` correctly and has the whole time; nothing in the file an agent is
*required* to read pointed at it.

`scripts/loop_fleet.py` run from the `main` tree names phase 14, its stage, its branch, its
worktree and what it is waiting on, in one command. The tooling was never the gap.

The third was found while checking the first, and it is live rather than historical. Asked what
comes next, `loop_stage.py --phase 14` prints `this stage's checks pass; run --advance to move on`
while `review_queue.py --list` prints `4 item(s) waiting on you`. `check_stage_review` builds one
path, `stage-NN-<stage name>.md`, and validates that file alone; phase 14's stage 4 has four notes
and the other three are never opened. Three blockers marked `[open, for Taylor]` therefore cannot
hold the stage, and an agent that trusts `--advance` freezes the tests with open questions still
on the board. Filed as `STAGE-REVIEW-CHECK-READS-ONE-FILENAME-PER-STAGE`; the fix is a ruling
about whether the check globs or the loop forbids a second note, and both change a driver phase 14
is mid-loop against.

The second half is not fixable from here. A tree parked on an old commit carries its own
`AGENTS.md`, `CLAUDE.md`, `phase_status.yml` and check scripts at that commit, so this task's fix
is invisible in the tree that most needs it - `loop_fleet.py` does not exist there at all, and the
phase-10 `loop_stage.py` there answers `loop is 'completed'; start it with --start PHASE_ID`,
which is a confident wrong answer rather than a refusal. Every candidate fix changes where the
operator lands when he opens the project, so it is his ruling and it is filed, not taken.

## Scope

Approved: `AGENTS.md`. It is the single source for behavior rules and the only place a Start Of
Work step exists to be fixed.

Standing: `CURRENT_TASK.yml`, `backlog.yml`, `STATUS.md`, `docs/BACKLOG.md`,
`docs/exec_plans/**`, `reports/active/**`.

Deliberately untouched: `scripts/loop_stage.py`, `scripts/loop_fleet.py`,
`verification/loop_state.yml` and `verification/loop_runs/**`. Retiring a completed lane's
pointer is already filed twice over as `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` and
`LOOP-LANE-POINTERS-NEVER-RETIRE`, both waiting on one ruling from the drivers' owner, and
phase 14 is mid-loop against those drivers in its own tree. `docs/LOOP.md` is already correct.

## Delegation Plan

- No-delegation exception: subagents are unavailable in this operator's sessions - the standing
  instruction is not to call the Agent tool unless asked - so `AGENTS.md` step 10's self-review
  fallback applies, recorded here and performed below.

## Slices

- [x] Slice 1: Start Of Work gains two steps ahead of every read - `git worktree list`, then
  `scripts/loop_fleet.py` from the `main` tree - and names `main` as the only tree that describes
  the repo, a merged branch as a finished phase, and `loop_state.yml` as history.
- [x] Slice 2: `START-OF-WORK-READS-THE-CURRENT-DIRECTORY` filed `done` with the four sessions it
  cost, and `A-STALE-TREE-CARRIES-ITS-OWN-COPY-OF-THE-RULES` filed `deferred` with its three
  candidate fixes.
- [x] Slice 3: `STAGE-REVIEW-CHECK-READS-ONE-FILENAME-PER-STAGE` filed `deferred`, with the two
  drivers' opposite answers reproduced in the phase-14 lane and the four notes counted.
- [x] Slice 4: generated docs regenerated, read-only self-review, full gate.

## Verification

`uv run python scripts/run_verify.py` - the full derived gate, no new command ids. No source,
test, fixture, artifact or committed report moves apart from the gate's own records and the
generated documents.

## Read-only self-review

Reviewer: coordinator, self-review, per the no-delegation exception above.

Question asked: does the new step 1 actually stop the wrong answer, or does it only describe it?

- **No blocker.**
- The failure was reproduced rather than recalled. In `~/projects/poker-bot`,
  `cat CURRENT_TASK.yml` reads `task_mode: idle`, `phase_status.yml` lists phase 10 as the last
  `completed` and 11 through 16 as `future`, and `verification/loop_state.yml` reads phase 10,
  stage 11. Nothing in that tree contradicts any of it.
- The fix was checked the same way, from the `main` tree: `git worktree list` names every tree on the machine,
  `scripts/loop_fleet.py` prints one lane - phase 14, stage 4/11, running, with its branch and
  worktree path - and `verification/loop_runs/14.yml` in that lane's own tree confirms the stage.
  Both new steps are read-only and neither writes a pointer.
- Worth stating plainly rather than leaving implied: this fix is a document, and the defect it
  fixes is a document being wrong. It closes the case where the agent is in a current tree and
  had no instruction to look outward, which is every lane and the `main` tree. It does not close
  the case where the agent is in a stale tree, because that tree cannot see it. Claiming
  otherwise would be the more comfortable filing and the false one, which is why the second
  entry exists and says the fix must live outside the repo.
- A canary leaked into this tree during the task and is recorded rather than left out of the
  record. The first gate run was stopped mid-flight to take the third filing, and
  `check_gate_bite` had `price-substitution-not-recorded` applied to
  `src/poker_training_bot/solver_artifacts/lookup.py` at the moment it died.
  `verification/.mutation_in_progress` named the file and the canary, the working tree showed the
  one-line diff, and both were restored before the gate was re-run. The rule the phase-14 lane
  wrote after two leaks of its own holds here too: run `check_scope.py` after anything that may
  mutate, and do not stop a gate mid-run for an edit that could have waited.
- `AGENTS.md` lands at 148 lines against its 150-line cap, which is two lines of headroom and
  worth knowing before the next edit. Not filed: `check_file_sizes.py` already fails the gate on
  it, so nothing here is invisible, and the sibling cap items are all about files with no
  headroom left.

## Alignment

- **The two files most likely to be read as the answer are still on disk saying phase 10.**
  `verification/loop_state.yml` is tracked in every tree and its name promises exactly the thing
  it no longer holds. Step 2 now says so in words, which is strictly worse than deleting the
  file. Not filed again: `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` and
  `LOOP-LANE-POINTERS-NEVER-RETIRE` are the same defect already filed from two lanes, and both
  wait on the one ruling that decides whether a finished pointer is history or garbage.

## Outcome

`AGENTS.md` Start Of Work now locates the lane before reading anything. Three entries filed, one
closed and two open on operator rulings. Generated docs regenerated. Gate green.

## Next Agent Bootstrap

Read this from the tree holding `main`, at `~/projects/poker-bot-worktrees/main`, which is idle
once this task closes. `~/projects/poker-bot` is parked on merged `phase/10-solver-extraction`,
118 commits behind, and is not the repo.

Phase 14 is the live lane, in `~/projects/poker-bot-worktrees/phase-14` at stage 4 of 11, in
`implementation` mode, and is not this task's business. Its stage-4 test re-cut is finished across
five rounds and sitting uncommitted in that tree, with all three blockers ruled by the operator on
2026-08-26; the note is
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-test-recut.md`. The next moves there
are to commit the re-cut and run `loop_stage.py --phase 14 --advance` into the stage-5 freeze -
but read `review_queue.py --list` first and settle the three blockers still marked
`[open, for Taylor]` in `stage-04-predicate-change-review.md`, because `--advance` cannot see them
(`STAGE-REVIEW-CHECK-READS-ONE-FILENAME-PER-STAGE`).
Decisions 6 and 10 of that phase owe amendments at the next `contract-update`, transcribing three
rulings the note is currently the only record of.
