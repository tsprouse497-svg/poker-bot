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
`src/poker_training_bot/poker_core/positions.py`, the package exports, the
committed artifact under `data/artifacts/**`, `tests/test_preflop_positions.py`,
`tests/test_preflop_artifacts.py`, `tests/test_preflop_lookup.py`,
`tests/test_command_registry.py`, `scripts/build_preflop_chart_artifact.py`,
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
- Ownership: Worker A owns `src/poker_training_bot/poker_core/positions.py`,
  `src/poker_training_bot/solver_artifacts/hand_classes.py`, and
  `tests/test_preflop_positions.py`. Worker B owns
  `src/poker_training_bot/solver_artifacts/schema.py` (including the shared spot
  key), `src/poker_training_bot/solver_artifacts/importer.py`, and
  `tests/test_preflop_artifacts.py`. Worker C owns
  `src/poker_training_bot/solver_artifacts/lookup.py` and
  `tests/test_preflop_lookup.py`. The coordinator owns the committed artifact
  under `data/artifacts/preflop/`, its reviewable range spec and builder in
  `scripts/build_preflop_chart_artifact.py`, the package exports,
  `scripts/generate_preflop_chart_report.py`, command registration in
  `scripts/run_verify.py`, docs, the audit packet, and closeout.
- Expected outputs: each worker returns a changed-file summary, the public API
  it exposes, and passing focused tests for its lane. The coordinator integrates
  the lanes, generates the reports, and runs the full derived gate.
- Status: Stage 1 coordinator-owned, completed. Worker A completed (positions,
  hand classes, 100 tests). Worker B completed (schema, importer, 66 tests).
  Worker C completed (lookup, 30 tests). Coordinator integration completed
  (committed artifact and builder, package exports, chart report generator,
  command registration, docs).
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
- [x] Position vocabulary in the poker core with focused tests.
- [x] Hand-class canonicalization with focused tests.
- [x] Artifact schema, canonical spot key, and fail-closed importer with focused
  tests.
- [x] Fail-closed lookup with focused tests.
- [x] Committed real artifact, chart coverage report, command registration.
- [x] Full derived gate, independent review, audit packet.

## Verification

Stage 1 command IDs: the full derived base gate.
Stage 2 command IDs: `pytest_preflop_artifacts`,
`generate_preflop_chart_report`, `generate_strategy_query_report`, plus the full
derived gate.
Reports: `reports/active/latest_preflop_chart_report.txt`,
`reports/active/latest_strategy_query_report.txt`.

## Outcome

Gate completed 2026-08-11. The three worker lanes delivered as specified and
integrated without conflict: positions and hand classes, schema and importer,
lookup. Two independent read-only reviewers (fail-closed correctness, poker
domain correctness) then raised nine real findings including one blocker, all
fixed before the gate commit and all recorded in the audit packet. The most
important were that `spot_key` accepted keys no real preflop situation can
produce, that no test exercised the committed artifact so it could drift from its
range spec, and that the big blind's defense range folded 76% where reference
defense is 45% or more.

Coordinator implementation exception: the review fixes cut across all three
worker lanes plus the builder, the report generator, and the docs at once, so the
coordinator applied them directly rather than reopening three lanes for a handful
of coupled edits.

The design decision that held: one derived spot key, used by the importer, the
lookup, and the artifact builder, is what let the reviewers find the
canonicalization gap as a single fixable rule rather than three inconsistent
implementations. Deferred: `SECOND-ORBIT-PREFLOP-SPOTS`, `STACK-DEPTH-BUCKETS`,
`ASYMMETRIC-EFFECTIVE-STACKS`, `BLIND-STRUCTURE-VARIANTS`, and
`RAISE-SIZE-IN-SPOT-KEY`.

## Next Agent Bootstrap

Stage 1 landed as commit `5d12eb0`. Stage 2 task `PHASE-04-PREFLOP-ARTIFACTS`
is active (implementation mode, base commit
`5d12eb0baf8e1ae10a602a7e9ee286e1dd45f8e3`) with phase 04 `active` in
`phase_status.yml`. All three worker lanes are integrated and the derived gate is
green; what remains is the independent review record, the audit packet, the gate
commit, and closeout to idle.
Next command: `uv run python scripts/run_verify.py`.
