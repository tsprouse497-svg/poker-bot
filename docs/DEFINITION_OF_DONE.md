# Definition Of Done

Behavior rules live in `AGENTS.md`; this file is only the closeout checklist.

Every completed phase or package must satisfy:

- Phase contract acceptance criteria met.
- Full derived gate passed via `scripts/run_verify.py`.
- Required active reports fresh.
- Phase audit packet committed.
- Gate logs committed where required.
- `phase_status.yml` updated.
- Generated `STATUS.md`, `docs/PHASE_LEDGER.md`, and `docs/BACKLOG.md` current.
- Active ExecPlan includes a pre-implementation `Delegation Plan` with lanes,
  owners, expected outputs, and status, or a concrete no-delegation exception.
- Worker subagents handled implementation by default where available, with any
  coordinator implementation exception recorded in the ExecPlan.
- Active ExecPlan outcome or retrospective filled in.
- No forbidden scope changes.
- Backlog updated for deferred work.
- Independent read-only subagent review completed where available.
- Phase audit packet records review findings, or the concrete reason a subagent
  review could not run plus self-review notes.
- If Taylor performs human review, the phase audit packet records the human
  sign-off verdict and keeps a source-code-free spot-check path where practical.
- ExecPlan moved from `docs/exec_plans/active/` to `docs/exec_plans/completed/`.
- `CURRENT_TASK.yml` reset to `task_mode: idle` and the closeout committed.
- The gate commit tagged `phase-NN-complete` for phase gates.
