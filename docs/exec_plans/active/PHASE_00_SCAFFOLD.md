# Phase 00 Scaffold ExecPlan

## Objective

Create the fresh repository scaffold, contracts, tooling, reports, coordinator
workflow, and Phase 00 audit packet without implementing poker logic.

## Scope

Approved scope is defined in `CURRENT_TASK.yml`. Forbidden scope is
`data/raw/**` and `data/processed/**`.

## Slices

- [x] Create package and documentation scaffold.
- [x] Create phase contracts for all v1 phases.
- [x] Create verifier and report generators.
- [x] Generate active verification reports.
- [x] Write Phase 00 audit packet.

## Verification

Run `scripts/verify.ps1` and `scripts/verify.sh`.

## Outcome

Phase 00 scaffold is complete when verification reports are committed and the
initial local git commit exists.

## Next Agent Bootstrap

Read `AGENTS.md`, `CURRENT_TASK.yml`, `phase_status.yml`, and
`docs/phase_contracts/PHASE_01_CORE_ENGINE.md`. Start Phase 01 by updating the
active ExecPlan and keeping work limited to synthetic core-engine evidence.
