# Preflop Artifact Contract

Preflop strategy is artifact-backed and imported offline. Runtime consumption is
deterministic.

Required artifact fields:

- `artifact_schema_version`
- `source`
- `generated_at`
- `table_size`
- `stack_depth_bb`
- `positions`
- `spots`
- `action_weights`
- `audit_fields`

Missing chart spots must abstain or fail closed in v1. Heuristic guessing for
missing coverage is forbidden.
