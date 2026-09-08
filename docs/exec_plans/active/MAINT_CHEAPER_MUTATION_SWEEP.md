# MAINT: Cheaper Mutation Sweep

## Objective

`check_gate_bite` is 98% of the gate: 11,313 seconds of the 11,525 recorded on 2026-09-07.
Four fifths of that is the whole test suite run 90 times, and those runs prove nothing,
because `tests/test_loop_machinery.py::test_every_mutation_applies_exactly_once_to_its_file`
asserts each mutation's `find` string appears exactly once in its file. Apply any mutation and
that assertion fails, so the suite goes red for all 74 before any behaviour is examined.

Taylor ruled the investigation's recommendation on 2026-09-08: do A, B and C, and delete the
duplicate sweep at loop stage 7. Leave D (parallel mutation workers, measured 2.2x) to the
backlog, and do not do E (nightly or diff-scoped sweeps).

The gate this task closes on is the full derived gate green plus `check_gate_bite` green,
with the sweep costing minutes rather than three hours and requiring strictly more of the
tests than it does today.

## Scope

Approved:

- `scripts/check_gate_bite.py` - restore proved by comparing bytes, health run once per sweep.
- `scripts/run_verify.py` - register `pytest_loop_machinery`, add the worker flag to the two
  slow pytest commands.
- `scripts/check_repo_consistency.py` - new check: every command a mutation names is in the
  derived gate.
- `scripts/quality_checks.py` - exempt the catch-all `pytest` from the rule that every
  `pytest*` command must be named by a mutation, with the measured reason. Added mid-task; the
  scope log carries why.
- `scripts/loop_stage.py` - stage 7 stops running the sweep a second time.
- `verification/mutations.yml` - narrow the 45 `must_fail` lists that name the whole suite.
- `verification/freeze.lock`, `tests/test_loop_machinery.py` - tests for all of the above.
- `pyproject.toml`, `uv.lock` - `pytest-xdist` in the dev group.
- `docs/LOOP.md` - the machinery description that states the old restore behaviour.

Standing scope carries `CURRENT_TASK.yml`, `backlog.yml`, the generated documents, and
`reports/active/**`.

Forbidden: `data/raw/**`, `data/processed/**`. Nothing under `src/` changes: this task does not
touch what the bot does, only what proves it.

## Delegation Plan

Complete before implementation. Lanes run one at a time because all three end in the same test
file, and two of them edit `scripts/run_verify.py`.

- Worker lanes: three sequential worker subagents. Lane 1 sweep-mechanics, lane 2
  witness-narrowing, lane 3 parallel-tests-and-stage-7.
- Ownership: lane 1 owns `scripts/check_gate_bite.py`; lane 2 owns
  `verification/mutations.yml`, `scripts/check_repo_consistency.py` and
  `scripts/quality_checks.py`, and registers the new command in `scripts/run_verify.py`; lane 3 owns `pyproject.toml`, `uv.lock`,
  `scripts/loop_stage.py`, and the command flags in `scripts/run_verify.py`. Each lane appends
  its own tests to `tests/test_loop_machinery.py` while it holds the file. The coordinator owns
  integration, `docs/LOOP.md`, `backlog.yml`, the freeze lock refresh, the gate, and closeout.
- Expected outputs: from each lane, the changed files plus a summary naming what it changed,
  the tests it added, and the command it ran to prove them. No lane runs the full gate.
- Status: lane 1 completed and integrated at `831c020`, lane 2 at `85276f2`, lane 3 at
  `5d3281d`. The independent review is written and its two blockers are fixed and marked
  resolved in the note. Those fixes are coordinator-owned because they are integration: they
  span three lanes' files and arrived after all three closed.
- Integration order: lane 1, then lane 2, then lane 3, coordinator checking the tree is green
  between lanes with the narrow commands rather than the gate. Lane 2 runs after lane 1 because
  narrowing changes what the sweep does, and lane 3 last because its flags change the timings
  the other two are measured by.
- Review handoff: a read-only reviewer that wrote none of it inspects the whole diff against
  `b5eb610`, and answers one question: does the sweep still refuse a bug that no test catches?
  It must check every narrowed `must_fail` entry against what the green gate proves, the new
  restore path for a case where a file is left changed, and whether removing the second stage-7
  call removed any check that `run_verify.py` does not already make.

## Slices

- [x] Lane 1: restore proved by byte comparison, one health run at the end of the sweep over
      the union of commands the sweep ran. Evidence: a test that a corrupted restore is caught,
      and a test that the health run covers every command named.
- [x] Lane 2: `pytest_loop_machinery` registered and in the base gate; the 41 mutations that
      already name a narrower command drop `pytest`; the four that name only the suite name the
      new command; the four that name only a report generator drop `pytest` and get a backlog
      entry saying no test covers them. New consistency check that every named command is in
      the derived gate. The catch-all `pytest` becomes the first entry in
      `EXEMPT_FROM_MUTATION_COVERAGE`, because the bookkeeping test makes it red for every
      mutation and a witness that cannot fail to fire is not a witness. Evidence: the check
      fails on a mutation naming an unreachable command.
- [x] Lane 3: `pytest-xdist` in the dev group, `-n 4` on `pytest` and `pytest_derived_chart`,
      stage 7 stops calling `check_gate_bite` a second time and instead refuses if the derived
      gate does not contain it. Evidence: the suite green under workers, and a test that stage
      7 still requires the sweep.
- [x] Coordinator: `docs/LOOP.md`, backlog entries for D and for the four uncovered
      behaviours, freeze lock, full gate, independent review, audit note, closeout.

## Verification

Full derived gate via `scripts/run_verify.py`, which includes `check_gate_bite`,
`check_repo_consistency`, `check_test_freeze`, `check_scope`, and `ruff_check`. The sweep's
own cost is recorded before and after in this plan's Outcome from
`reports/active/verify_results.json`.

## Outcome

Filled after the gate; the numbers below are from `reports/active/verify_results.json` on the
run that certified this lane.

- Before, on `main` at `b5eb610`: the gate took 11,525 seconds, of which `check_gate_bite` was
  11,313. 45 of the 74 mutations named the whole suite, so the sweep ran it 90 times.
- After: see the committed verify report. No mutation names the whole suite. The sweep runs 85
  command runs plus one health pass over the 19 distinct witnesses, against 148 runs before.
- What the sweep asks for went up, not down. Every mutation is now witnessed by a command that
  exercises the behaviour it breaks, rather than by a suite that a bookkeeping test reddens for
  any mutation at all. `check_repo_consistency` refuses a witness the derived gate does not run,
  and that check has a canary of its own.
- Two findings this work could not close are filed rather than fixed:
  `SEAT-ORDER-REFUSALS-HAVE-NO-TEST` and `MUTATION-SWEEP-RUNS-ONE-MUTATION-AT-A-TIME`. Two more
  came from the review: `MERGE-INTEGRATION-STILL-RUNS-THE-SWEEP-TWICE` and
  `A-NARROW-COMMAND-CAN-HOLD-A-TEST-THAT-REDDENS-FOR-EVERY-MUTATION`.
- One deferred item closed: `MUTATION-DRILL-CHECKOUT-DESTROYS-UNCOMMITTED-WORK`, whose named fix
  was the rule `docs/LOOP.md` now carries.

## Next Agent Bootstrap

Lane worktree `/Users/taylorsprouse/projects/poker-bot-worktrees/maint-33` on branch
`maint/33-cheaper-mutation-sweep`, seeded from `b5eb610` on `main`.

State: all three lanes integrated, the independent review written with both blockers fixed and
marked resolved, and the freeze lock rebuilt. What remains is the full gate, the closeout, and a
ruling on whether this merges to `main` now, since a merge makes four live lanes rebase.

Next command: `uv run python scripts/run_verify.py`, once no sibling lane is running one. Only one
full gate fits on this machine at a time.

Open, and not to be invented: whether the four refusal mutations
(`the-depth-refusal-names-the-first-offender-in-seat-order` and its three siblings) should keep
a witness at all is settled for now: they keep `generate_table_state_report`, and the backlog
records that no test covers those behaviours. Writing those tests is a separate task and is not
in this scope.
