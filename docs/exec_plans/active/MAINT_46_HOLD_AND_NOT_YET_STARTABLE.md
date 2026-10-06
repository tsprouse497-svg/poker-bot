# MAINT-46: A Phase On Hold, And A Phase Not Yet Startable

- **Task** `MAINT-46`
- **Mode** `maintenance`
- **Branch** `maint/46-hold-and-not-yet-startable`, worktree `~/projects/poker-bot-worktrees/maint-46`
- **Base** `e1cdb32`, which is `main` after MAINT-45
- **Authorised by** Taylor, 2026-10-05 in this session

## Objective

Taylor put phase 18 on hold on 2026-10-05, after its lane reached stage 3 with three questions for
him, and asked for the repo to account for it. Its lane is halted with the reason, but `main` does not
know, and the fleet board and review queue still list the three questions as waiting on him. The
same board counts phase 20, which Taylor left open on purpose and which cannot start before 19 and
22, as waiting on him (THE-REVIEW-QUEUE-LISTS-A-PHASE-WHOSE-DEPENDENCIES-ARE-NOT-MET-AS-WAITING-ON-YOU).
This task records the hold on `main` and makes both tools tell a real ask from a phase that owes
nothing yet.

## Taylor's rulings

1. **Phase 18 is on hold.** His words: "can we just put this on hold?", then "please update the repo
   to account for this."

## Design

- `verification/loop_policy.yml` gains an optional `on_hold` field per phase: a non-empty reason
  string. Phase 18 carries it. Absent means not on hold.
- `scripts/review_queue.py`: the heading counts only real asks. A phase with `on_hold` set has none
  of its asks counted (halt, decisions, blockers, pause, gate) and is listed once under an "on hold"
  heading with its reason. A `needs_human_data` phase whose `depends_on` are not all completed on
  `main` is listed under a "not yet startable" heading, using `loop_fleet.py`'s own eligibility rule,
  and is not counted.
- `scripts/loop_fleet.py`: `--plan` never offers an on-hold phase as "may start now" and names the
  hold; `--status` shows a held lane as on hold with its reason, and not its asks as waiting.
- `scripts/loop_stage.py`: `--resume` and `--start` refuse a phase whose policy carries `on_hold`, so
  lifting a hold is an edit to the policy file and is visible in a diff.
- Docs that describe the board (`docs/LOOP.md`, the review-queue line in `AGENTS.md`) and phase 18's
  place in both roadmaps follow. Phase 18's own contract on `main` is unchanged; its lane carries the
  stage 1 contract.

## Delegation Plan

- Worker lanes: lane W, one general-purpose worker, for the three scripts, their tests and the lock.
- Ownership: W owns `scripts/review_queue.py`, `scripts/loop_fleet.py`, `scripts/loop_stage.py`,
  `tests/test_loop_fleet.py` (where the tests went, since `tests/test_loop_machinery.py` sits at 698
  of 700 lines) and `verification/freeze.lock`. The coordinator owns the policy entry, the docs, the
  backlog, the review fixes, integration and the gate.
- Expected outputs: from W, an uncommitted diff, the targeted test and lint commands run with their
  results, and the lock diff; from the coordinator, the docs and the commits.
- Status: W completed and integrated at `69bdc3b`; review fixes by the coordinator at `7a6eef5`.
- Integration order: W's diff first, then the coordinator's docs, committed together; then the review
  fixes; then the gate.
- Review handoff: one read-only reviewer that wrote none of it checks the design against Taylor's
  ruling, that a real ask can never be hidden by the new rules (only `on_hold` and unmet dependencies
  hide anything), that the tests would fail on the old behaviour, and that the lock diff is only the
  test file that changed. Asked also what it held back. No gate runs by the reviewer.

## Slices

- [x] Activate MAINT-46 with a dated scope entry.
- [x] Worker lane W: scripts, tests, lock; 12 tests, each failing on the old code.
- [x] Policy entry, docs, backlog.
- [x] Independent read-only review: no blocker. Fixed after it: an unreadable `main` policy now
  refuses instead of trusting the lane's copy, the branch name lives once, four more tests, an
  unknown-key check on the policy, and the docs name the field and the refusal.
- [ ] Gate, packet, closeout to idle, gate again, merge, push.

## Verification

`uv run python scripts/run_verify.py`, read for its verdict rather than its exit code.

## Outcome

Not yet.

## Next Agent Bootstrap

Worktree `~/projects/poker-bot-worktrees/maint-46`. Next: worker lane W.
