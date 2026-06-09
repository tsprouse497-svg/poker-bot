# Agent Instructions

This repo is an offline-first deterministic NLHE training bot. Git is the source
of truth. Runtime poker decisions must not rely on LLM reasoning.

## Start Of Work

1. Read `CURRENT_TASK.yml`.
2. Read `phase_status.yml`.
3. Read the active phase contract in `docs/phase_contracts/`.
4. Read or create the active ExecPlan under `docs/exec_plans/active/`.
5. Stay inside approved scope and away from forbidden scope.

## Current Task Rules

- One official active task is allowed at a time.
- `CURRENT_TASK.yml` controls task mode and approved scope.
- `forbidden_scope` always wins over `approved_scope`.
- Contract changes require explicit `contract-update` task mode.
- Internal slices belong in the active ExecPlan, not `CURRENT_TASK.yml`.

## Coordinator Workflow

When asked to start a phase or package, enter coordinator mode:

1. Load the current task, phase status, and active contract.
2. Create or update an ExecPlan.
3. Break the phase into small internal slices.
4. Delegate to subagents where available.
5. Update the ExecPlan after meaningful slices.
6. Run verification and required reports.
7. Before completing the gate, spawn a read-only independent review subagent
   when subagents are available.
8. Record the independent review findings in the audit packet. If no subagent
   can be spawned, record the concrete reason and perform self-review.
9. Stop only for a blocker, prohibited scope, or completed gate.

## Testing Ladder

- Prefer real fixtures, golden hands, replay checks, schema validation, CLI
  reports, and deterministic simulations.
- Mocks are allowed only at hard external boundaries.
- Do not mock core poker state, strategy legality, replay, or report generation
  just to pass tests.

## V1 Boundaries

- No PokerNow automation.
- No browser/platform observation.
- No UI package.
- No runtime solver calls.
- No heuristic guessing for missing preflop chart spots.
- No large hand-history ingestion.
