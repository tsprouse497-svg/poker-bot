# MAINT-46 independent review

Read-only pass over `git diff e1cdb32..69bdc3b` by a reviewer that wrote none of it. It ran the
fleet tests (54 passed) and no gate. Resolution marks added by the coordinator after fixing.

## Blocker
None.

## Non-blocker
- [resolved] `hold_refusal` fell back to the worktree's own policy when `git show main:` failed, which
  is exactly the copy that may predate the hold, so the held lane could resume. It now refuses, with
  a test.
- [resolved] `"main"` was written a second time in `loop_stage.py`; `INTEGRATION_REF` now lives there
  once and `loop_fleet.py` reuses it.
- [resolved] The policy file's header and the policy paragraph of `docs/LOOP.md` now describe
  `on_hold`.
- [resolved] `AGENTS.md` now states the refusal, not only the display.
- [resolved] A misspelt `on_hold` held nothing silently; a test now rejects unknown policy keys.
- [resolved] Untested paths covered: a blank hold, `--resume` refused by `main`'s copy alone, the
  unreadable-policy path. A held phase that is completed with no lane is left off the board by design
  and stays untested.
- [resolved] The ExecPlan named a test file that did not change; corrected.
- The roadmap's dated "lane halted at stage 3" note will go stale on resume; acceptable as dated.

## Alignment
- The proposed id for unvalidated policy keys is not filed: the key check landed here instead.
- THE-FLEET-BOARD-SHOWS-A-LANE-WHOSE-PHASE-WAS-RETIRED stays deferred, correctly.

## Checks with no finding
- Faithful to the ruling; the not-yet-startable change is the existing backlog item, not a widening.
- Only `on_hold` and unmet dependencies hide anything, and an unmet dependency never hides a live
  lane's asks. Holds come from `main`'s policy only.
- Each new test fails on the old behaviour; control tests exist.
- The lock changed only for `tests/test_loop_fleet.py` and the floor.
- THE-REVIEW-QUEUE-LISTS-A-PHASE-WHOSE-DEPENDENCIES-ARE-NOT-MET-AS-WAITING-ON-YOU is done: phase 20
  now shows as not yet startable and is not counted.
- No em dashes; every cited id exists.

## Held back
- No gate, no `check_gate_bite`; `tests/test_loop_machinery.py` unchanged and not reviewed.
- The live board shows phase 18's asks until this merges, so merge promptly.
- `loop_fleet.policy()` crashes rather than degrading when `show` returns nothing; predates this task.

## Verdict
Pass with non-blockers, all but one fixed.
