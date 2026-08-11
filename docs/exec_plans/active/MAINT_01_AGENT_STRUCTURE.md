# Maintenance 01 ExecPlan: Structure The Repo For Agent-Only Development

## Objective

Apply the high and medium findings from the 2026-08-08 structure review: single-source verify gates, function-based naming, consolidated agent rules, guaranteed rule loading, an explicit idle state, and diff-based narrow scope checks.

## Scope

Approved and forbidden scope are controlled by `CURRENT_TASK.yml` for task `MAINT-01-AGENT-STRUCTURE`.
This task must not change poker behavior in `src/**` beyond what the concurrent uncontested-settlement feature commit already contains.

## Delegation Plan

- No-delegation exception: every slice rewires the same shared metadata (contract frontmatter, `CURRENT_TASK.yml`, `run_verify.py`, `AGENTS.md`), so parallel worker lanes would conflict on nearly every file; the coordinator implements serially and uses an independent read-only review subagent before closeout.

## Slices

- [x] Coordinated with the concurrent session, which committed its uncontested-settlement feature as `3396d40` before this task started.
- [x] Derive verify gates from contract frontmatter plus `phase_status.yml`; delete per-phase gate lists and `required_task_commands`.
- [x] Rename phase-numbered scripts, fixtures, reports, and command IDs by function; separate the two replay reports that collided on one output file.
- [x] Add `CLAUDE.md` importing `AGENTS.md`.
- [x] Consolidate behavior rules into `AGENTS.md`; delete duplicate workflow docs.
- [x] Add idle task mode, task activation/closeout rituals, and drop `completed_local_commit`.
- [x] Rework `check_scope.py` to check changed files against narrow approved scope plus standing scope, measured from `base_commit`.
- [x] Update contracts (remove duplicate `status`, fix stale report references), tests, CI checkout depth, and generated docs.
- [x] Run the full derived gate, independent read-only review, and close out to idle.

## Verification

Full derived gate via `uv run python scripts/run_verify.py`, which must include `pytest_poker_core`, `pytest_hand_history`, `generate_golden_hand_report`, and `generate_hand_history_replay_report` from the phase 01/02 contracts.

## Outcome

All high and medium findings from the structure review are applied and the full derived gate passes (18 commands).
An independent read-only review subagent examined the uncommitted tree and reported 19 findings: 2 blockers and 17 minor/nit.
Both blockers were latent traps for the next agent and are fixed: the phase-status vocabulary (`future`/`active`/`completed`) is now documented in `AGENTS.md` and validated by `check_contracts.py`, and the closeout ritual now says to preserve `standing_scope`/`forbidden_scope` so the closeout gate cannot deadlock.
All minors were also fixed in this task: `--no-renames` scope diffs, task-mode validation in both checkers, failing verify reports on gate-setup errors, completed-phase report/audit existence checks, `docs/exec_plans/**` size limits, template placeholder warning, orphan example fixtures deleted, `git cat-file` base-commit validation (a YAML integer-coercion bug found by the new `tests/test_check_scope.py`), and quotepath-safe git output.
One review suggestion was adopted as a rule change instead of a rename: the naming rule now targets file/script/command-ID names, so historical fixture hand IDs keep their committed values.

## Next Agent Bootstrap

Read `AGENTS.md` (canonical rules), then `CURRENT_TASK.yml` and `phase_status.yml`.
The repo rests in `task_mode: idle`; activate Phase 03 per the Task Activation ritual in `AGENTS.md`, fleshing out the Phase 03 contract in `contract-update` mode first.
Run `uv run python scripts/run_verify.py` for the full derived gate.
