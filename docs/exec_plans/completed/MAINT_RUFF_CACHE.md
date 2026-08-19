# ExecPlan: MAINT - The gate's ruff command can pass on a stale cache

Contract: none. Maintenance work outside any phase.
Loop state: not driven by `scripts/loop_stage.py`; phase 10 is closed and tagged.

## Objective

`ruff_check` passed on the phase 10 branch and fails the moment the cache is dropped:
`uv run ruff check --no-cache .` reports two unsorted import blocks in
`tests/test_solver_expectations.py`, a file frozen since stage 4. The same two errors
appear on `main`, which is how the merge surfaced them.

A gate command whose answer depends on what a previous run happened to leave in
`.ruff_cache` is not a check. Fix the two import blocks, and make the command run
without the cache so the result is a property of the tree rather than of the machine.

## Scope

Approved, `task_mode: maintenance`:

- `tests/test_solver_expectations.py` - two import blocks, no assertion changes
- `verification/freeze.lock` - the file changed, so the lock is rewritten
- `scripts/run_verify.py` - `ruff check --no-cache .`

Forbidden: any change to the committed export, the source card, the reader, the
expectations module, the report, or the audit packet. This task fixes a lint result and
a gate command, and touches no poker and no evidence.

## Delegation Plan

- No-delegation exception: subagent delegation is switched off in this operator's
  sessions (the standing instruction is not to call the Agent tool unless it is
  requested), so `AGENTS.md` step 6 cannot be satisfied and step 10's self-review
  fallback applies. Self-review, recorded here.

## Slices

- [x] **S1.** Reorder the two import blocks, re-freeze, run `ruff check --no-cache`.
- [x] **S2.** `ruff_command` gains `--no-cache`; full gate; move `phase-10-complete` onto
      the resulting commit so the tag marks a commit that passes without a warm cache.

## Verification

`uv run python scripts/run_verify.py`, and `uv run ruff check --no-cache .` directly.

## Outcome

Two import blocks reordered, no assertion changed, tests re-frozen. `ruff_command` now
runs `--no-cache`, so the gate's answer is a property of the tree. Full gate green across
38 commands, and `phase-10-complete` moves onto this commit so the tag marks a state that
passes without a warm cache.

Self-review, read-only over the diff: the two changes are a whitespace reorder inside an
import block and one flag. Nothing in the export, the reader, the expectations module, the
report or the audit packet moved, and `check_test_freeze` proves the test file's only
change is the one recorded in the lock. The one judgement in the task - whether the gate
should pay the cost of an uncached lint run - was taken on the grounds that a cached one
already let two errors through a tagged phase. It costs a few seconds per gate run.

## Next Agent Bootstrap

If this is unfinished: the two errors are in `tests/test_solver_expectations.py` and
`ruff check --fix` writes the whole fix. The only judgement in the task is whether the
gate should run ruff without its cache, and the answer is yes - the alternative is a
command that can report clean because it reported clean before.
