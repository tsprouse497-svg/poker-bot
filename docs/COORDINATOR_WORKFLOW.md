# Coordinator Workflow

When the user says "start Phase N" or "start package X":

1. Read `AGENTS.md`.
2. Read `CURRENT_TASK.yml`, `phase_status.yml`, and the active phase contract.
3. Enter coordinator mode. The main agent is PM/coordinator and owns scope,
   sequencing, delegation, integration, verification, and closeout.
4. Create or update an active ExecPlan.
5. Before implementation, add or refresh the ExecPlan `Delegation Plan` section
   with lanes, ownership, expected outputs, and status.
6. If delegation will not be used, record a concrete no-delegation exception in
   the `Delegation Plan` before implementation begins.
7. Break the work into internal slices.
8. Delegate implementation to worker subagents by default where subagents are
   available. The coordinator implements only when delegation is unavailable or
   unsuitable and the ExecPlan records that exception.
9. Update the ExecPlan after each meaningful slice.
10. Run verification and required reports.
11. Spawn a read-only independent review subagent before marking the gate
   complete, unless subagents are unavailable.
12. Add the review findings to the audit packet. If review could not run, state
    the concrete reason and add self-review notes.
13. Stop for a true blocker, prohibited scope, or completed gate.

Active ExecPlans are committed living documents and must include a
`Delegation Plan` section and a `Next Agent Bootstrap` section.
