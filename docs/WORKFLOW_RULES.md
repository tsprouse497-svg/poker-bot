# Workflow Rules

`CURRENT_TASK.yml` is the active assignment. `phase_status.yml` is the machine
source of truth for phase progress. Generated human docs must stay current.

## Scope

Approved scope is strict by default. Forbidden scope always wins.

## Contract Updates

Do not mix contract changes with implementation unless `task_mode` is an
explicit `contract-update` mode.

## Testing

Prefer real fixtures, golden hands, replay checks, schema validation, CLI
reports, and deterministic simulations. Mocks are allowed only at hard external
boundaries.
