# Coordinator Workflow

When the user says "start Phase N" or "start package X":

1. Read `AGENTS.md`.
2. Read `CURRENT_TASK.yml`, `phase_status.yml`, and the active phase contract.
3. Enter coordinator mode.
4. Create or update an active ExecPlan.
5. Break the work into internal slices.
6. Delegate to subagents where available.
7. Update the ExecPlan after each meaningful slice.
8. Run verification and required reports.
9. Spawn a read-only independent review subagent before marking the gate
   complete, unless subagents are unavailable.
10. Add the review findings to the audit packet. If review could not run, state
    the concrete reason and add self-review notes.
11. Stop for a true blocker, prohibited scope, or completed gate.

Active ExecPlans are committed living documents and must include a
`Next Agent Bootstrap` section.
