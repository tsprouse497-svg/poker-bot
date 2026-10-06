# MAINT-46 audit packet: phase 18 on hold, and two kinds of phase that owe nothing yet

Taylor put phase 18 on hold on 2026-10-05 ("can we just put this on hold?") and asked for the repo to
account for it. It changes no range, artifact or strategy code.

## What shipped

- `verification/loop_policy.yml` gains an optional `on_hold` reason per phase. Phase 18 carries it.
- `scripts/loop_stage.py`: `--start` and `--resume` refuse a phase held on `main`, and refuse when
  `main`'s policy cannot be read, since the lane's own copy may predate the hold.
- `scripts/review_queue.py`: the "waiting on you" count covers only real asks. A held phase is listed
  once with its reason; a `needs_human_data` phase whose dependencies are not complete on `main` is
  listed as not yet startable. Phase 20 is the second kind.
- `scripts/loop_fleet.py`: `--plan` never offers a held phase; `--status` shows a held lane as on hold.
- `AGENTS.md`, `docs/LOOP.md`, both roadmaps and the policy header describe the hold.
- THE-REVIEW-QUEUE-LISTS-A-PHASE-WHOSE-DEPENDENCIES-ARE-NOT-MET-AS-WAITING-ON-YOU closed as done.
- 16 new tests in `tests/test_loop_fleet.py`, re-frozen; the lock diff is that file and the floor.

## How to check it without code

After the merge, run `uv run python scripts/review_queue.py --list` from `main`: it should say nothing
is waiting on you, then list phase 18 on hold and phase 20 not yet startable.

## Independent review

A read-only reviewer that wrote none of it. Note at
`reports/phase_audits/reviews/MAINT_46_HOLD_AND_NOT_YET_STARTABLE/independent-review.md`. No blocker.
The one finding that mattered: an unreadable `main` policy fell back to the lane's copy, which would
let the held lane resume; it now refuses. The rest were tests, docs and one duplicated branch name.
Held back: no gate run, and a pre-existing crash in `loop_fleet.policy()` when `main` cannot be read.

## Gate

Recorded in the ExecPlan.
