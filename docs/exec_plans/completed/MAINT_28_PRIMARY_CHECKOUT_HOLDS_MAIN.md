# MAINT-28: the checkout a session lands in now holds main

Task: `maint-primary-checkout-holds-main`. Mode: `maintenance`. Base: `50d25ee`.

## Objective

Record the workspace change that closes `A-STALE-TREE-CARRIES-ITS-OWN-COPY-OF-THE-RULES`, filed
hours earlier by MAINT-27 as needing an operator ruling.

## The ruling

Taylor chose the first of the three candidates on 2026-08-27: hold `main` in the primary checkout
and retire the separate `main` worktree. Rejected: parking the primary checkout at a detached HEAD
on main's tip, which drifts again on every merge and buys time rather than a fix; and leaving it
with a guard in the operator's own session configuration, which is a rule rather than a fact and
had already failed three times.

## What changed, and where

Nothing tracked. Two git commands, both on this machine:

    git worktree remove ~/projects/poker-bot-worktrees/main
    git -C ~/projects/poker-bot checkout main

`~/projects/poker-bot` now holds `main` at `50d25ee`. Lanes are unchanged and still live in
`~/projects/poker-bot-worktrees/`; `phase/10-solver-extraction` is still a branch, merged, and no
longer checked out anywhere.

## Why no code needed changing

`scripts/loop_fleet.py` was written against the right invariant already. `primary_worktree()`
resolves the repository from `git rev-parse --git-common-dir`, which belongs to the primary
checkout whatever tree the script runs in, and `lane_root()` is its parent plus
`-worktrees`. Neither reads a branch name, so the board is identical before and after. The
integration runbook's `git -C {REPO_ROOT} checkout main` is strictly better off: run from the
primary checkout it now names the tree that holds `main`.

`AGENTS.md` step 1 still says "the tree holding `main`" and not a path, deliberately. Which
worktrees exist is a property of the machine, which is the same reason `docs/LOOP.md` gives for
never committing the board.

## Scope

Approved: nothing beyond standing scope. The fix is a workspace state, and no tracked file
implements it.

Standing: `CURRENT_TASK.yml`, `backlog.yml`, `STATUS.md`, `docs/BACKLOG.md`,
`docs/exec_plans/**`, `reports/active/**`.

## Delegation Plan

- No-delegation exception: subagents are unavailable in this operator's sessions - the standing
  instruction is not to call the Agent tool unless asked - so `AGENTS.md` step 10's self-review
  fallback applies, recorded here and performed below.

## Slices

- [x] Slice 1: the two git commands, with the primary checkout and the retired worktree both
  verified clean first, and no peer poker-bot session live to collide with.
- [x] Slice 2: `A-STALE-TREE-CARRIES-ITS-OWN-COPY-OF-THE-RULES` flipped to `done` carrying the
  ruling, what was run, and why no code moved.
- [x] Slice 3: generated docs regenerated, read-only self-review, full gate.

## Verification

`uv run python scripts/run_verify.py` - the full derived gate, no new command ids. Beyond the
gate's own records and the generated documents, only `backlog.yml` moves.

The change itself was verified where it matters rather than by the gate, which cannot see it:
`git worktree list` shows `~/projects/poker-bot` on `main` at `50d25ee` and no second tree holding
`main`, and `uv run python scripts/loop_fleet.py` run from that directory prints the phase 14 lane,
its stage, its branch, its worktree path and the four items waiting on a human - the answer the
same directory got wrong three times.

## Read-only self-review

Reviewer: coordinator, self-review, per the no-delegation exception above.

Question asked: does the trap actually close, or does it move somewhere new?

- **No blocker.**
- It closes for the case that caused it. The failure was always a session reading state out of the
  directory named after the project, and that directory now holds `main`. There is no longer any
  tree on this machine parked on a merged branch, so the class of tree that carried a stale copy of
  the rules has no members.
- One case survives and is worth naming rather than glossing: a **lane** tree still describes its
  own lane and not the repo. Reading `phase_status.yml` in `phase-14` today reports phase 13 as the
  newest completed phase, which is true of that branch and not of the repo. That is what
  `AGENTS.md` step 1 is for, and it is unchanged by this task - the fix removes the tree that could
  not see step 1, not the need for step 1.
- `loop_fleet.py`'s two path helpers were re-read rather than assumed, because a fleet that placed
  the next lane inside a lane is a failure mode its own docstring names. Both derive from
  `--git-common-dir` and neither reads a branch, so `lane_root()` is `~/projects/poker-bot-worktrees`
  from any tree, before and after.
- Checked for collision before touching anything: `git status` clean in both trees, and no peer
  poker-bot session running that could have been mid-command in the tree being removed.
- The gate rejected this task's own first attempt, which is worth keeping rather than quietly
  fixing: `base_commit` was written as the abbreviated `50d25ee` and `check_scope.py` requires the
  full forty characters while `task_mode` is `maintenance`. The check is right - an abbreviation
  can become ambiguous as the repo grows, and every changed file is measured against that commit.
  A second run was stopped externally partway through; `verification/.mutation_in_progress` was
  absent and the tree held only intended edits, so no canary leaked that time.
- The retired worktree's `.venv` went with it, which is regenerable and cost nothing here, but is
  the kind of thing worth knowing before removing a worktree someone is working in.

## Alignment

- **`docs/LOOP.md` and several completed ExecPlans name `~/projects/poker-bot-worktrees/main` as
  where `main` lives.** In the ExecPlans that is history and correct as written. `docs/LOOP.md`
  does not name the path at all, which is why nothing needed editing. Not filed: no live document
  now points at a tree that does not exist.

## Outcome

The default directory holds `main`. One backlog entry closed, filed and ruled the same day. No
tracked file implements the fix and none needed to. Gate green.

## Next Agent Bootstrap

`main` is in `~/projects/poker-bot`, idle once this task closes. Lanes are in
`~/projects/poker-bot-worktrees/`. Read `AGENTS.md` step 1 before answering any status question;
it is now current in the tree you land in.

Phase 14 is the live lane, in `~/projects/poker-bot-worktrees/phase-14` at stage 4 of 11, and is
not this task's business. Do not run `loop_stage.py --phase 14 --advance` yet: three blockers in
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-predicate-change-review.md` are
marked `[open, for Taylor]`, the advance check cannot see that file
(`STAGE-REVIEW-CHECK-READS-ONE-FILENAME-PER-STAGE`), and a decision packet covering all three was
being prepared when this task closed.
