# MAINT-37 audit packet: the fleet board trusts main's copy of a lane pointer

After MAINT-36 completed phase 14's pointer on `main`, `scripts/loop_fleet.py` still listed phase 14
as running nine times and `scripts/review_queue.py` printed 246 asks, 54 of them distinct. Every
worktree that branched from or rebased onto `main` after a lane merged carries a stale copy of that
lane's pointer, and `lanes()` counted each copy as a lane. Taylor asked for it fixed on 2026-09-22.

## What shipped

- `lanes()` in `scripts/loop_fleet.py`: for a phase with a pointer on `main`, only two copies are
  read - `main`'s and the one on that phase's own `phase/NN-` branch - and whichever is further
  along (stage, then running, halted, completed) is listed, `main` on a tie. Every other copy is
  ignored. A phase with no pointer on `main` is read from its own worktree as before.
- `phase_status.yml` is deliberately not the test: phase 14 was `completed` there for weeks while its
  stage-11 sign-off was owed, and that rule would have hidden the ask.
- Within one worktree, the newest layout now decides even when it is not live, which matches how
  `loop_stage.state_path_for()` already reads it.
- Eight tests in `tests/test_loop_fleet.py`, additions only; `verification/freeze.lock` re-frozen,
  34 to 42 functions in that file.
- Canary `stale-pointer-copy-outvotes-main` in `verification/mutations.yml`, reddening seven tests.
- `docs/LOOP.md` states the rule and its two limits.

On real data the board goes from 14 lanes to 3 (15, 16, 17) and the queue from 246 asks to 34: the
old distinct set minus the 20 phase-14 items, nothing else lost. Phase 16's sign-off ask shows once.

## Delegation

One implementation worker wrote the code, tests, canary, doc and lock across two rounds. The
coordinator read each diff against the files, re-ran the tests and fast checks, and wrote the
backlog notes, the plan and this packet.

## Independent review

One read-only reviewer that wrote none of it, no gate runs, note at
`reports/phase_audits/reviews/MAINT_37_MAIN_POINTER_WINS/review.md`.

- **Blocker, resolved.** The first cut read a merged phase from `main` only. A lane that merged at
  stage 10 and then halted at 11 in its own tree lost its halt and sign-off asks, and `AGENTS.md`'s
  "a lane's live pointer is in the lane's own tree" became false. Reproduced on a scratch fleet.
  Fixed by also reading the lane's own branch; the reviewer re-checked and marked it resolved.
- **Non-blocker, fixed.** The canary swapped in `if False:`, which drops unmerged lanes instead of
  letting sibling copies count. Now `if True:`, the failure it names.
- **Non-blockers, documented rather than changed.** The rule needs a worktree on `main`, which the
  primary checkout always is; reading `main` through `git show` would remove that, but would need a
  new test seam for every existing lane test. A merged-then-resumed halt shows until the resume
  merges, which errs toward showing an ask. Both are in `docs/LOOP.md`.
- **Noted.** A completed phase reopened later under the same id would be invisible until merged;
  nothing does that today.

## Backlog

- `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` corrected: it said the board was unaffected. The board
  side is fixed; nothing retiring a finished pointer is still open.
- `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION` extended: merge order no longer changes the
  board; which order is intended is still unruled.

## Gate

Green on the first run, 50 of 50, `check_gate_bite` reporting 79 mutations all caught - one more
than before this task, the new canary.
