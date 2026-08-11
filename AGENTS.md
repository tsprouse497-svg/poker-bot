# Agent Instructions

This repo is an offline-first deterministic NLHE training bot.
Git is the source of truth.
Runtime poker decisions must not rely on LLM reasoning.
This file is the single source for behavior rules.
If another document contradicts it, this file wins and the other document must be fixed.

## Start Of Work

1. Read `CURRENT_TASK.yml`.
2. Read `phase_status.yml`.
3. If `task_mode` is `idle`, no task is active. Do not change the repo until a task is activated by an explicit request.
4. Read the active phase contract in `docs/phase_contracts/`.
5. Read or create the active ExecPlan under `docs/exec_plans/active/`, starting from `docs/exec_plans/TEMPLATE.md`.
6. Stay inside approved scope and away from forbidden scope.
7. Before closing any phase or package, satisfy every item in `docs/DEFINITION_OF_DONE.md`.

## Task Modes

- `idle`: no active task. Between phases the repo must rest in this mode.
- `implementation`: normal phase or package work. Contract edits are forbidden.
- `contract-update`: contract edits are allowed and must not mix with unrelated implementation.
- `maintenance`: repo tooling, structure, or process work outside any phase, including the mechanical contract edits that work requires. Semantic contract changes still require `contract-update`.

## Scope Model

`CURRENT_TASK.yml` controls scope. `scripts/check_scope.py` enforces it.

- `approved_scope`: paths this task may change. Keep it narrow; approve only what the task genuinely touches.
- `standing_scope`: task metadata and generated outputs that any task may change. Do not grow it casually.
- `forbidden_scope`: always wins over everything. It is an existence rule, not a change rule: matching paths must not exist anywhere in the tracked tree.
- `base_commit`: the commit the task started from. Changed files are measured against it; `null` means HEAD.
- Widening `approved_scope` mid-task requires a dated entry in `scope_change_log`.

## Task Activation

1. Confirm `task_mode` is `idle` and the previous task is committed.
2. Set `task_id`, `active_phase`, `task_mode`, a narrow `approved_scope`, and `base_commit` to the current HEAD hash.
3. For a phase: flesh out the phase contract first in `contract-update` mode if it still has placeholder criteria, then activate implementation.
4. For a phase: set the phase's `status` to `active` in `phase_status.yml`. The only valid statuses are `future`, `active`, and `completed`; the verify gate includes a contract's commands only while its phase is `active` or `completed`, so a phase left at `future` skips its own gate.
5. Create the ExecPlan under `docs/exec_plans/active/`.

## Task Closeout

1. Run the full gate: `uv run python scripts/run_verify.py`.
2. Commit the passing gate with audit packet and regenerated docs.
3. Move the ExecPlan from `docs/exec_plans/active/` to `docs/exec_plans/completed/`.
4. For a phase: set the phase's `status` to `completed` in `phase_status.yml` and tag the gate commit `phase-NN-complete`.
5. Reset `CURRENT_TASK.yml` to `idle` (`task_id: null`, `active_phase: null`, `task_mode: idle`, `approved_scope: []`, `base_commit: null`). Keep `standing_scope` and `forbidden_scope` unchanged; the closeout edits themselves pass scope only through `standing_scope`.
6. Run the gate again and commit the closeout.

## Coordinator Workflow

When asked to start a phase or package, enter coordinator mode:

1. Load the current task, phase status, and active contract.
2. Create or update an ExecPlan. Active ExecPlans are committed living documents and must include a `Delegation Plan` section and a `Next Agent Bootstrap` section.
3. Act as PM/coordinator: own scope, sequencing, delegation, integration, verification, and closeout.
4. Before implementation, add a `Delegation Plan` section to the active ExecPlan with lanes, owners, expected outputs, and status. If no work is delegated, record a concrete no-delegation exception before implementation.
5. Break the phase into small internal slices.
6. Delegate implementation to worker subagents by default where subagents are available. The coordinator implements only when the ExecPlan records why delegation is unavailable or unsuitable.
7. Update the ExecPlan after meaningful slices.
8. Run verification and required reports.
9. Before completing the gate, spawn a read-only independent review subagent when subagents are available.
10. Record the independent review findings in the audit packet. If no subagent can be spawned, record the concrete reason and perform self-review.
11. Stop only for a blocker, prohibited scope, or completed gate.

## Verification Gate

`scripts/run_verify.py` derives the full gate: a fixed base gate plus `required_gate_commands` from every contract whose phase is active or completed in `phase_status.yml`.
Do not add per-phase gate lists anywhere else.
A phase's new command IDs are declared in its contract frontmatter and registered in `COMMANDS` in `scripts/run_verify.py`.
`phase_status.yml` is the machine source of truth for phase progress; generated docs (`STATUS.md`, `docs/PHASE_LEDGER.md`, `docs/BACKLOG.md`) must stay current via their generators.

## Naming Rules

Script, fixture, test, report, and command-ID names describe what the thing does, never which phase produced it.
Phase numbers belong only in contracts, exec plans, and audit packets.
Example: `generate_golden_hand_report.py`, not `generate_phase_01_replay_report.py`.

## Testing Ladder

Prefer the lowest test that proves real behavior without hiding defects:

1. Static contract and schema checks.
2. Import smoke tests.
3. Unit tests with real fixtures.
4. Golden hand and replay checks.
5. CLI report generation.
6. Deterministic simulation comparisons.

Mocks are allowed only at hard external boundaries.
Do not mock core poker state, strategy legality, replay, or report generation just to pass tests.

## V1 Boundaries

- No PokerNow automation.
- No browser/platform observation.
- No UI package.
- No runtime solver calls.
- No heuristic guessing for missing preflop chart spots.
- No large hand-history ingestion.
