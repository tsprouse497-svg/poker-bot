# ExecPlan: MAINT-02 Loop Machinery

## Objective

Build the tooling the autonomous phase loop depends on, so a phase can run
unattended without the loop being able to grade its own homework.

This is `maintenance` work: repo tooling and process, outside any phase. No phase
contract semantics change here. Phase 05's own ExecPlan stays active and paused at
its human gate; this task does not touch it.

## Scope

Approved:

- `scripts/check_scope.py`, `scripts/check_contracts.py` (hardening)
- `scripts/freeze_tests.py`, `scripts/check_gate_bite.py`,
  `scripts/check_repo_consistency.py`, `scripts/loop_stage.py` (new)
- `scripts/run_verify.py` (command registration and base gate)
- `verification/**` (freeze lock, mutation table, loop policy and state)
- `tests/test_loop_machinery.py`, `tests/test_check_scope.py`,
  `tests/test_command_registry.py`
- `AGENTS.md`, `docs/LOOP.md`
- Standing scope for task metadata, backlog, and generated docs.

Forbidden: any phase contract's semantics, `data/**`, and any change to Phase 03
decision validation or Phase 04 import validation.

## Delegation Plan

- No-delegation exception: this session is instructed not to spawn subagents
  unless Taylor asks for one, and he has not for this task. The five scripts are
  also tightly coupled through one shared state directory and one command
  registry, so splitting them across lanes would have produced merge conflicts in
  `run_verify.py` and `verification/` rather than parallelism. Coordinator-owned
  end to end, with self-review recorded below in place of an independent reviewer.

## Slices

- [x] `scripts/freeze_tests.py` plus `verification/freeze.lock`: per-file sha256,
  per-file test-function count from the syntax tree, and a suite-wide floor.
- [x] `scripts/check_repo_consistency.py`: declared gate commands are registered,
  every `pytest_*` command names a file that holds tests, phase status agrees with
  ExecPlan location.
- [x] `scripts/check_contracts.py`: an active or completed phase must carry at
  least three acceptance criteria that are not gate boilerplate.
- [x] `scripts/check_scope.py`: scope read from `base_commit`, relaxations need a
  new `scope_change_log` entry, over-broad patterns rejected, real sha required
  while a task is open.
- [x] `scripts/check_gate_bite.py` plus `verification/mutations.yml`: five
  mutations, each required to turn its own gate command red.
- [x] `scripts/loop_stage.py` plus `verification/loop_policy.yml`: eleven stages
  with a deterministic advance check each, and the per-phase auto-advance policy.
- [x] Command registration and base-gate wiring in `scripts/run_verify.py`.
- [x] Tests: `tests/test_loop_machinery.py` (28), plus scope and registry
  coverage for the new rules.
- [x] `docs/LOOP.md` and the `AGENTS.md` loop section.

## Verification

Base gate only; this task adds no contract commands.

New base-gate command IDs: `check_repo_consistency`, `check_test_freeze`,
`check_gate_bite`. `freeze_tests` is registered but deliberately excluded from the
gate, because a gate that rewrites the lock every run is not a freeze.

## Outcome

Two findings came out of building this, both from the new checks firing on the
repo that added them.

1. `check_contracts` found that phases 00, 01, and 02 are marked completed against
   contracts carrying only the four boilerplate acceptance criteria. Those gates
   asserted little more than that the gate passed. Backfilling real criteria is a
   semantic contract change and needs `contract-update` mode, which a maintenance
   task may not do, so they are explicitly exempted in `CRITERIA_BACKFILL_EXEMPT`
   and tracked as `CONTRACT-CRITERIA-BACKFILL`. No new phase can join the
   exemption.

2. `check_gate_bite` poisoned the bytecode cache on its first full gate run. Two
   of the five mutations swap equal-length tokens, so restoring the source changed
   neither mtime nor size and CPython kept executing mutated bytecode from
   `__pycache__`. It surfaced as an unrelated preflop lookup failure on a later
   run. Fixed by purging the target's cached bytecode around each mutation,
   disabling bytecode writing in the mutated subprocess, and re-running each
   command after restore to prove the tree is healthy again. A restore that leaves
   the repo failing is worse than a surviving mutation, because it looks like a
   defect somewhere else entirely.

Self-review notes, in place of an independent reviewer:

- The clean-tree assertion from the loop design deliberately did **not** go into
  the base gate. The gate runs before the commit, so the tree is dirty by
  definition at that moment and the check would have made the gate unpassable. It
  lives in the driver's stage 0 precheck instead.
- Per-phase report freshness was dropped from the plan rather than built. The
  derived gate already regenerates each phase report before its checks run, so a
  stale committed report is refreshed in the same run that would have failed on
  it. The real hole is committing without running the gate, which the driver
  already prevents.
- `check_scope` compares against the base revision but still trusts the working
  tree's `scope_change_log` to justify a relaxation. An agent can therefore widen
  scope and write its own reason. That is intentional: the point is to make the
  widening visible in the diff and to give the driver something to halt on, not to
  make it impossible.

## Next Agent Bootstrap

State: MAINT-02 is committed and the repo is back to `idle`. Phase 05's ExecPlan is
still in `docs/exec_plans/active/`, paused after its contract stage with all eight
judgment calls answered.

The loop has not yet driven a phase. Phase 05's implementation is the first
candidate, and it is a `frozen-into-data` phase, so `loop_policy.yml` marks it
`auto_advance: false`.

Next command: `uv run python scripts/loop_stage.py --start 05`, then follow the
driver. Before that, note that Phase 05 needs the chart export at
`~/Downloads/gtowizard_6max_nl25_100bb_preflop.json` committed under
`data/artifacts/preflop/sources/` by its Lane A.
