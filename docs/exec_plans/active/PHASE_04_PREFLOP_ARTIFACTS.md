# Phase 04 ExecPlan: Preflop Artifact/Chart Contract, Importer, And Fail-Closed Lookup

## Objective

Complete the Phase 04 gate: a versioned preflop artifact schema, a canonical
position vocabulary and spot key, a fail-closed importer, a fail-closed chart
lookup, at least one committed real artifact, and a human-readable chart
coverage report.

Stage 1 of this plan is the contract-update task `PHASE-04-CONTRACT-UPDATE`,
which replaces the placeholder Phase 04 acceptance criteria with concrete,
testable ones.
Stage 2 is the implementation task `PHASE-04-PREFLOP-ARTIFACTS`.

## Scope

Approved files are controlled by `CURRENT_TASK.yml`.
Stage 1 approves only `docs/phase_contracts/PHASE_04_PREFLOP_ARTIFACTS.md`.
Stage 2 approves `src/poker_training_bot/solver_artifacts/**`,
`src/poker_training_bot/poker_core/positions.py`, the committed artifact under
`data/artifacts/**`, `tests/test_preflop_artifacts.py`,
`scripts/generate_preflop_chart_report.py`, `scripts/run_verify.py`, the
supporting docs, and the phase audit packet.

Forbidden: `data/raw/**`, `data/processed/**`, phase contract edits during
implementation mode, and every V1 boundary in `AGENTS.md`.
Phase 04 does not wire charts into a playing strategy; that is Phase 05.

## Delegation Plan

Complete before implementation begins.

- Worker lanes: Stage 1 (contract authoring) is coordinator-owned because a
  contract-update task must not mix with implementation and the phase contract
  is a single small file. Stage 2 splits into Worker A (position vocabulary and
  canonical spot key in the poker core plus hand-class canonicalization) and
  Worker B (artifact schema, checksum validation, and fail-closed importer),
  followed by Worker C (fail-closed lookup over imported artifacts, built on the
  Worker A and Worker B APIs).
- Ownership: Worker A owns `src/poker_training_bot/poker_core/positions.py` and
  `src/poker_training_bot/solver_artifacts/hand_classes.py`. Worker B owns
  `src/poker_training_bot/solver_artifacts/schema.py` and
  `src/poker_training_bot/solver_artifacts/importer.py`. Worker C owns
  `src/poker_training_bot/solver_artifacts/lookup.py`. The coordinator owns the
  committed artifact fixture, `tests/test_preflop_artifacts.py` integration,
  `scripts/generate_preflop_chart_report.py`, command registration in
  `scripts/run_verify.py`, docs, the audit packet, and closeout.
- Expected outputs: each worker returns a changed-file summary, the public API
  it exposes, and passing focused tests for its lane. The coordinator integrates
  the lanes, generates the reports, and runs the full derived gate.
- Status: Stage 1 coordinator-owned, completed. Worker A planned. Worker B
  planned. Worker C planned. Coordinator integration planned.
- Integration order: Worker A and Worker B run in parallel on disjoint files,
  then Worker C consumes both APIs, then the coordinator wires the report
  generator, registers command IDs, and runs the gate.
- Review handoff: the independent read-only reviewer inspects the full Phase 04
  diff with emphasis on fail-closed behavior (no default action, no nearest
  spot, no partial load on rejection), spot-key canonicalization agreeing
  between importer and lookup, hand-class canonicalization across card order and
  suits, weight validation and checksum verification, and lookup determinism.

## Slices

- [x] Stage 1: Phase 04 contract fleshed out with concrete acceptance criteria.
- [ ] Position vocabulary and canonical spot key with focused tests.
- [ ] Hand-class canonicalization with focused tests.
- [ ] Artifact schema and fail-closed importer with focused tests.
- [ ] Fail-closed lookup with focused tests.
- [ ] Committed real artifact, chart coverage report, command registration.
- [ ] Full derived gate, independent review, audit packet.

## Verification

Stage 1 command IDs: the full derived base gate.
Stage 2 command IDs: `pytest_preflop_artifacts`,
`generate_preflop_chart_report`, `generate_strategy_query_report`, plus the full
derived gate.
Reports: `reports/active/latest_preflop_chart_report.txt`,
`reports/active/latest_strategy_query_report.txt`.

## Outcome

Fill this in before completing the gate.

## Next Agent Bootstrap

Stage 1 task `PHASE-04-CONTRACT-UPDATE` is active (contract-update mode, base
commit `a53ba35fff8a09d80b9cbbad9522bca1c0e3b2ba`), approving only
`docs/phase_contracts/PHASE_04_PREFLOP_ARTIFACTS.md`.
After the Stage 1 gate commit, activate `PHASE-04-PREFLOP-ARTIFACTS` in
implementation mode with the Stage 2 scope above, set phase 04 to `active` in
`phase_status.yml`, and set `base_commit` to the Stage 1 commit.
Next command: `uv run python scripts/run_verify.py`.
