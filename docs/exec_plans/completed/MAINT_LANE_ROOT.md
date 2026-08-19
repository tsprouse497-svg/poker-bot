# MAINT-22 - Lanes Are Siblings Of The Repository

## Objective

Put a new lane's worktree beside the repository rather than beside whichever worktree ran the driver.

The fleet's first real `--start-lane 11` printed
`.../poker-bot-worktrees/maint-loop-fleet-worktrees/phase-11`,
one directory too deep, because `LANE_ROOT` was derived from `REPO_ROOT`.
That is correct exactly once, from the primary checkout.
Run from a lane it puts the next lane inside that lane, and the tree nests a level deeper on every phase.

Found by running the command rather than by reading it, which is the only way this one shows up: the constant is right in the worktree the driver was written in.

## Scope

Approved: `scripts/loop_fleet.py`, `tests/test_loop_fleet.py`, `verification/mutations.yml`, `verification/freeze.lock`.
Forbidden: everything else. No contract, no phase, no other driver.

## Delegation Plan

- No-delegation exception: this session is instructed not to spawn subagents, and the change is one function plus its tests. Self-review is in the Outcome.

## Slices

- [x] `primary_worktree()` reads the shared git directory, which belongs to the primary checkout whatever worktree the driver runs in, and `lane_root()` returns its sibling.
- [x] Two tests: the invariant against the live repo, and the derivation against a fixed path.
- [x] A canary that makes lanes nest inside the repository and requires `pytest_loop_fleet` to notice.

## Verification

- `pytest_loop_fleet`, `check_test_freeze`, `check_scope`, `check_gate_bite`
- `scripts/run_verify.py` full gate
- `loop_fleet.py --start-lane 11` prints `~/projects/poker-bot-worktrees/phase-11`

## Outcome

The runbook now names `/Users/taylorsprouse/projects/poker-bot-worktrees/phase-11`, a sibling of the repository, run from a linked worktree.

### Self-review

No independent subagent review; this session cannot spawn one.

The test that matters is the invariant one rather than the fixed-path one.
Asserting `lane_root()` equals a literal would have passed against the old code too when run from the primary checkout, which is exactly how the defect survived being written.
Asserting that the root is a sibling of the repository and not inside it fails against the old code from any linked worktree and is silent about the exact string, which is the property the code is actually for.

Sibling rather than inside is load-bearing beyond tidiness: an untracked `worktrees/` directory in the primary checkout makes `tree_is_clean()` false, and stage 0's precheck would then fail for every lane at once. That reason is in the docstring, because a later reader would otherwise be entitled to think it cosmetic and move it.

## Next Agent Bootstrap

Branch `maint/lane-root` off `main` at `a8a96d6`, worked in `~/projects/poker-bot-worktrees/maint-loop-fleet`.
Phase 10 runs untouched in the primary worktree at loop stage 5, and phase 11 is startable.
Next command: `uv run python scripts/loop_fleet.py --plan`.
