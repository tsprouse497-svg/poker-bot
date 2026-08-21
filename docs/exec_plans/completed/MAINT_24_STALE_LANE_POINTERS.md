# MAINT-24: a finished lane keeps its pointer, and a reader is told a dead phase

Task: `maint-stale-lane-pointers`. Mode: `maintenance`. Base: `beec7d6`.

## Objective

File the defect, do not fix it.

Nothing retires a lane pointer when its phase completes.
`verification/loop_state.yml` still reads phase 10, stage 11, `loop: completed` in all four
worktrees, and `verification/loop_runs/11.yml` says the same for phase 11.

## How it was found

A session was asked where phase 11 stood.
It read `verification/loop_state.yml`, the tracked file whose name says it holds the loop's
state, and reported the repo idle with phase 11 unstarted.
Phase 11 was in fact merged, tagged `phase-11-complete`, and closed a day earlier, and phase 12
was live at stage 7 in its own worktree at the moment of the reply.

The file is not lying about what it is - it is the pre-fleet single-lane pointer, and the lane
it points at really did finish at stage 11.
It is stale rather than wrong, and nothing in it says so.

## What is actually broken

`loop_stage.py` and `loop_fleet.py` both read the old and new layouts deliberately, so the
drivers are not confused and this is not the fleet seam already filed as
`FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION`.

Two consequences follow from pointers outliving their phase.

`loop_stage.run_paths()` counts every pointer on disk without looking at `loop`, so with no
`--phase` it refuses to guess: the phase-11 worktree answers `2 lanes in this worktree (11,
loop_state)` and the phase-12 worktree holds three.
Every phase that finishes makes the bare invocation worse.

`loop_fleet.lanes()` filters to `running` and `halted`, so the board is unaffected.
That is most of why this went unnoticed - the tool built to show the whole fleet is the one
tool that hides the problem.

## Why it is filed rather than fixed

Refusing to migrate a live lane mid-phase is deliberate and documented in `loop_stage.py`'s
module docstring, but retiring a pointer whose loop is completed is not migration.

The fix is a choice between at least three: the closeout stage deletes its own pointer,
`run_paths` ignores completed ones, or finished pointers move somewhere that does not read as
current state.
That is a ruling about what a finished lane's pointer *is* - history or garbage - and the
answer decides which of the three is right.
It belongs to whoever owns the two drivers, which is the same owner as the seam item, and it is
filed as `contract-update` for the same reason that one is.

Fixing it inside this task would also mean a maintenance task editing `scripts/loop_stage.py`
while a live lane in another worktree is mid-loop against that exact file.

## Scope

Approved: nothing beyond standing scope. Every file this task touches is already standing.

Standing: `backlog.yml`, `docs/BACKLOG.md`, `CURRENT_TASK.yml`, `STATUS.md`,
`docs/exec_plans/**`, `reports/active/**`.

Deliberately untouched: `scripts/loop_stage.py`, `scripts/loop_fleet.py`,
`verification/loop_state.yml`, `verification/loop_runs/**`, and the phase-11 and phase-12
worktrees.
Deleting the stale pointers is the fix, not the filing, and one of those worktrees is running.

## Delegation Plan

- No-delegation exception: subagents are unavailable in this operator's sessions - the standing
  instruction is not to call the Agent tool unless asked - so `AGENTS.md` step 10's self-review
  fallback applies, recorded here and performed below.

## Slices

- [x] Slice 1: `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` filed as `contract-update`, naming
  both consequences, the three candidate fixes, and the session it already cost.
- [x] Slice 2: `docs/BACKLOG.md` regenerated, read-only self-review, full gate.

## Verification

`uv run python scripts/run_verify.py` - the full derived gate, no new command ids.
Filing only, so no report a gate command regenerates may move apart from the gate's own records
and `docs/BACKLOG.md`.

## Read-only self-review

Reviewer: coordinator, self-review, per the no-delegation exception above.

Question asked: is the filed entry true, and is it the same item as the seam already filed?

- **No blocker.**
- Both claims in the entry were re-derived from the source rather than from the symptom.
  `run_paths()` appends `LEGACY_STATE_PATH` whenever the file exists and never reads `loop`;
  `lanes()` filters on `LIVE_LOOPS = {"running", "halted"}`.
  The `2 lanes` refusal was reproduced by running the bare driver in the phase-11 worktree,
  which is read-only and writes no pointer.
- It is not the seam item. `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION` is about the two
  drivers disagreeing over who owns integration once a lane finishes; this is about the artifact
  the finished lane leaves behind. They share an owner and the entry says so, which is the
  honest relationship between them.
- The entry names the session it cost, including that the session was this one. A filing that
  described the defect abstractly would lose the only evidence that it misleads a reader in
  practice rather than in theory.
- Worth stating rather than leaving implicit: this task changes no behaviour, and the defect it
  files is still on disk in four worktrees when the task closes.

## Alignment

- A maintenance task that only files a backlog entry still has to invent an ExecPlan, because
  `check_execplan_delegation` requires an active plan for every non-`idle` mode.
  MAINT-23 passed the same gate without one only because a paused phase plan happened to be
  sitting in `active/` at the time.
  Not filed: it is process shape rather than a defect, and it belongs in the same ruling as the
  two driver items rather than in a third entry.

## Outcome

One item filed. `docs/BACKLOG.md` regenerated. Gate green with no source, test, fixture,
pointer, or committed report changed apart from the gate's own records.

## Next Agent Bootstrap

Repo is on `main` in `~/projects/poker-bot-worktrees/main`, idle after this task closes.
Phase 12 is live in `~/projects/poker-bot-worktrees/phase-12` at stage 8 and is not this task's
business.
`COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` and `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION`
both need the same ruling from whoever owns `scripts/loop_stage.py` and `scripts/loop_fleet.py`
before anything implements either.
Until then, read lane state from `verification/loop_runs/<phase>.yml` and treat
`verification/loop_state.yml` as history.
