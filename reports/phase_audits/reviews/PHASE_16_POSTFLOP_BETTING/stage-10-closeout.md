# Phase 16, stage 10: independent read-only review of the closeout

Lane R8. I wrote none of the closeout and edited nothing but this file. No gate command was run from
this worktree: `verification/.mutation_in_progress` was absent before I started, and no python
process on this machine is rooted in `~/projects/poker-bot-worktrees/phase-16`. I never ran
`scripts/run_verify.py` or `scripts/check_gate_bite.py`, and never used `git checkout`, `git stash`
or `git tag`.

Subject: `6be678c`, `080202d`, and the annotated tag `phase-16-complete`. Specification: the
**Task Closeout** section of `AGENTS.md` at this branch.

## Method, stated once

Every figure below I computed in this worktree. The method is beside it.

- **Method S, the scope diff.** `CURRENT_TASK.yml` extracted at `6be678c^`, `6be678c` and `080202d`
  with `git show`, then the region from the `standing_scope:` key to end of file compared with
  `diff`. Not a comparison of the file as it stands now against itself.
- **Method G, the gate record.** `reports/active/verify_results.json` parsed at `080202d` and at
  `6be678c`, plus `git cat-file -p phase-16-complete` for the tagger epoch and `git log --format=%ci`
  for commit times. All arithmetic on raw epochs, all local times at the recorded offset of -0400.
- **Method M, the mutation catalogue.** All 78 entries of `verification/mutations.yml` loaded, and
  for each one the *`find`* string counted in its own file in the working tree. See the note on
  method below: this is the check that does not produce false positives.
- **Method T, the source trees.** `git diff --stat` over `src` and `scripts` between `ce714ff`,
  `6be678c` and `080202d`, plus `git status --porcelain`.
- **Method B, the backlog.** `backlog.yml` parsed at `HEAD` and grouped by `phase` and `status`.

## Blocker

None.

## Non-blocker

- **1. Order and content of the closeout: correct, with one deviation.** `AGENTS.md` steps 3, 4 and 5
  are all present. The plan move is a pure rename detected at 100% similarity,
  `docs/exec_plans/{active => completed}/PHASE_16_POSTFLOP_BETTING.md`, with zero content change.
  `phase_status.yml` moves phase 16 from `active` to `completed` and nothing else; the file holds 16
  completed and 2 future phases, and `STATUS.md` line 7 reads a count of 16, which agrees.
  `CURRENT_TASK.yml` resets all five required fields: `task_id`, `active_phase` and `base_commit` to
  `null`, `task_mode` to `idle`, `approved_scope` to `[]`. The deviation is step 2: `6be678c` commits
  a *failing* gate record, 46 of 50 with `all_passed: false`. It is transient and superseded 22
  minutes later, but see item 3, because it is the commit the tag names.
- **2. Standing and forbidden scope are byte-identical across the closeout (Method S).** The whole
  region from `standing_scope:` to end of file is unchanged from `6be678c^` to `080202d`: the same 10
  standing paths, the same 2 forbidden paths, and the same 397 `scope_change_log` entries. The
  closeout's single hunk touches only the first 8 lines of the file. This is the item I checked
  against the before state rather than the after state, and it passes cleanly.
- **3. The gate record is true and internally consistent (Method G).** At `080202d`:
  `schema_version: 1`, `all_passed: true`, 50 result entries, 50 with `passed: true`, 50 with
  `returncode: 0`, and 50 distinct `command_id` values, so nothing is double counted.
  `check_gate_bite` is among them, green, with stdout `gate bites: 78 mutations all caught`, which
  matches the 78 entries I counted in the catalogue. Its own duration is 1,154.55 s of the run's
  1,316.05 s total, that is 21.93 minutes for the run and 19.24 for the bite check alone.
- **4. The run placed after the tag, proved by content rather than by arithmetic.** The tagger epoch
  is 11:23:04 local and the record's `generated_at_epoch` is 11:45:05, a gap of 1,321 s against
  1,316.05 s of summed command time, so 4.95 s of slack. That margin is consistent with a start after
  the tag but does not by itself prove one, because summed durations are a lower bound on elapsed
  time and therefore put only an *upper* bound on the start. The proof is in the content: the
  immediately preceding run failed on exactly `phase 16 is completed but tag 'phase-16-complete' does
  not exist`, and this run passes that check, so the tag existed while `run_full_quality_gate` ran.
  Commit `080202d` follows at 11:45:25, 20 s after the record was written.
- **5. The tag sits one commit short of the green record, and that is bookkeeping, not a defect.**
  `AGENTS.md` says to tag the gate commit; `phase-16-complete` is on `6be678c`, whose own committed
  record is the 46 of 50 red run, while the 50 of 50 record lives on the untagged `080202d`. The
  ordering is circular and no ordering escapes it: the tag has to exist before the gate can be green,
  and the commit recording that green gate cannot exist before the run that produced it. Nothing in
  the gate notices, because `quality_checks.py:273` tests `expected not in tags`, that is existence
  only, never placement. **Where it should sit:** on the merge result on `main` after the integration
  re-gate, which is both what the parallel-phases section of `AGENTS.md` prescribes and what phase 10
  actually did, per `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION`. Until then I would leave it
  alone rather than move it to `080202d`; it is superseded either way, and the entry's point is that
  nobody recorded the intended resolution.
- **6. The "tree did not come back healthy" diagnosis is correct, and I verified it independently
  (Methods M and T).** Three separate lines of evidence, none of them the coordinator's:
  - *The catalogue check.* All 78 `find` strings occur exactly once in their own file in the working
    tree. A file left mutated would have its `find` count at 0 and its `replace` present, and none
    does. 29 distinct files are covered.
  - *The trees.* `git diff --stat` over `src` and `scripts` between `ce714ff` and `080202d` is empty,
    and `git status --porcelain` is empty, so the source is byte-identical to what stage 9 reviewed
    and nothing uncommitted is sitting on top of it.
  - *The mechanism, reproduced from the record.* `check_gate_bite.py:267-278` runs a health pass over
    every `must_fail` command after the last restore and emits that warning whenever any of them
    fails, for any reason. The 46 of 50 run is the proof: it emitted the identical warning naming
    `pytest_quality_hardening`, and its cause was demonstrably the missing tag, not a mutation. The
    message therefore does not imply a live mutation. The stated first cause is also real in code:
    `check_execplan_delegation.py` lines 124 and 125 error with `no active ExecPlan markdown files found` whenever
    `task_mode` is not `idle` and `docs/exec_plans/active/` holds no plan, which is exactly the state
    the first run was in, and `check_repo_consistency.check_plan_location` adds a second error on the
    same condition if the phase still read `active`.
  - *On method.* I used the `find` count, not a scan for `replace`. A scan for `replace` gives 4
    false positives on a perfectly clean tree, which is the trap: for
    `engine-min-raise-not-updated-after-bet` and
    `under-sized-all-in-bet-becomes-the-reference-level` the `replace` string is a literal substring
    of the `find` string, so it can never be absent; for `loop-review-trigger-never-fires` the
    replacement is `return []`, which occurs on 6 unrelated lines of `scripts/loop_stage.py`; and for
    `spot-key-drops-the-raise-size` the replacement matches line 268 of `spot_key.py`, the branch
    directly below the `find` at line 267.
  - *One limit, stated.* The first failing run's own record is not preserved anywhere.
    `reports/active/verify_results.json` is a single live slot and the 46 of 50 run overwrote it, so
    the count of five reds rests on the commit message. The evidence above covers the claim that
    matters, which is that nothing was left mutated; the count of five is merely consistent.
- **7. The filed ExecPlan is not true as filed.** Its `Next Agent Bootstrap` was rewritten at stage 9
  to be accurate at stage 9, then filed at stage 10 without being brought forward, so a permanent
  record now asserts four things the same commit falsified: "**Stage 9 of 11, running**" against a
  pointer at stage 10; "`task_mode: implementation`" against `idle`; stage 10's closeout listed as
  work still to do, item by item, all of which `6be678c` did; and "the gate recorded in
  `reports/active/verify_results.json` is the stage-7 run", which was true at `ce714ff` and is now the
  closeout run. The `## Outcome` section is worse: in a plan filed as completed it reads "Not yet.
  Stage 4 closed 2026-09-14; stage 5, the freeze, next." Nothing in the gate can see this, because
  `check_execplan_delegation` validates plans in `active/` and stops looking once a plan is filed. I
  am not making this a blocker: the letter of `AGENTS.md` step 3 is "move the ExecPlan", which was
  done, and no code or gate claim depends on the prose. But it is a one-file edit now and an
  amendment to `main` later, so the cheap moment is before the merge, and the plan's own rewrite note
  says the previous bootstrap died the same way one session earlier.
- **8. The pre-closeout green was real but stale, which the phase knew.** `ce714ff` carries a 50 of 50
  record with `all_passed: true` generated 2026-09-21 at 22:52:24, satisfying steps 1 and 2. The
  bootstrap flags it as the stage-7 run with source changed after it, and
  `scripts/generate_postflop_betting_report.py` did last change at `de7d1b9`, after the commit that
  recorded it. So the first green measured on the final tree is the post-tag run, which is what step 6
  exists for. Working as intended, recorded honestly.
- **9. `CURRENT_TASK.yml` is 4,336 lines and 377,011 bytes at idle**, of which the 397
  `scope_change_log` entries dated from 2026-06-08 onward are nearly all of it. `AGENTS.md` does not
  ask the closeout to trim them and no size cap binds the file, so this is compliant, not a defect.
  Recording it because the file grows monotonically, every task reads it, and nothing bounds it.

## Alignment

- `LOOP-STAGE-10-DEMANDS-A-REVIEW-IT-FORBIDS-WRITING` - this note is the entry's own prediction
  arriving again. Stage 10 owes a review note under `reports/phase_audits/reviews/<stem>/`, the task
  is idle with `approved_scope: []`, and that directory is not in `standing_scope`, so the file I
  just wrote is out of scope by construction, and I measured both halves of it. Before I wrote the
  file, `check_scope.py` exited 0. With the file present and untracked it exits 1 with
  `outside approved scope: reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-10-closeout.md`.
  Because `base_commit` is `null` the check measures against `HEAD`, so committing the note makes it
  invisible and the gate goes green again. **Practical consequence for whoever drives stage 11: this
  note must be committed before the gate is run, or `check_scope` reds on it.** Passing on a loophole
  is still not passing, and phase 16 is now the second lane to use it.
- `AN-EDIT-THAT-SUPERSEDES-PROSE-OWES-A-RE-READ-AND-NOTHING-ASKS-FOR-ONE` - non-blocker 7 is a fresh
  instance of the defect class this entry was filed for, and the entry already names "the ExecPlan
  Bootstrap" among its seven. The remedy it proposes, a stage obligation to re-read the containing
  section after an edit supersedes it, would have caught this one too, since filing a plan supersedes
  every present-tense sentence in it.
- `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION` - non-blocker 5. The entry already records that
  stage 10 and the integration runbook disagree about when the tag is written, and that phase 10
  resolved it by tagging the closeout commit and then moving the tag onto the merge commit with
  nothing recording that as the intended resolution. Phase 16 has reproduced the first half exactly.
- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` - phase 16 closes with 52 of its 57 backlog items at
  `deferred` and 5 at `done` (Method B). I am not calling that a closeout defect: the allowed
  vocabulary in `quality_checks.py:37` is `{deferred, done}` only, so genuinely open work has nowhere
  else to sit, and this phase closed on machinery rather than coverage by an explicit ruling. That is
  precisely why the entry matters: with a two-value vocabulary, an item that was silently finished and
  an item deliberately left open are indistinguishable, and 52 is a large surface to leave in that
  state on merge.
