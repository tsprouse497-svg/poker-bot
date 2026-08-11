# ExecPlan Template

Replace every placeholder below with concrete content before committing.
`scripts/check_execplan_delegation.py` rejects plans whose Delegation Plan still contains this template's placeholder text.

## Objective

State the phase or package gate.

## Scope

List approved files and forbidden files.

## Delegation Plan

Complete this before implementation begins.

- Worker lanes: list worker subagents and their bounded implementation lanes.
- Ownership: list file/module ownership for each worker and coordinator-owned
  integration responsibilities.
- Expected outputs: list patches, reports, review notes, or changed-file
  summaries expected from each lane.
- Status: planned, assigned, integrated, blocked, or completed for each lane.
- Integration order: state how the coordinator will review and merge lanes.
- Review handoff: state what the independent read-only reviewer must inspect.

If no implementation work is delegated, replace these fields with:

- No-delegation exception: concrete reason implementation is coordinator-owned.

## Slices

- [ ] Slice name and expected evidence.

## Verification

List command IDs and reports.

## Outcome

Fill this in before completing the gate.

## Next Agent Bootstrap

Provide exact context, current state, and next command.
