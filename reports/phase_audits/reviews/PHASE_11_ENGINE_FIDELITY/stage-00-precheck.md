# Phase 11 stage 0 (precheck) review

Read-only pass over `git diff 1b8314c -- docs/exec_plans/active/PHASE_11_ENGINE_FIDELITY.md`.
Context read: `AGENTS.md`, `docs/LOOP.md`, `docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`,
`verification/loop_policy.yml`, the six `phase: "11"` entries in `backlog.yml`. No gate run.

Reviewer: coordinator, self-review. Subagents are unavailable in this session (the
operator said so in the message that opened the phase, and the standing account
instruction is not to call the Agent tool unless asked), so `AGENTS.md` step 10's
self-review fallback applies. Recorded here rather than left implicit.

## What arrived in the diff, and why

One new file: the active ExecPlan. `AGENTS.md` start-of-work step 5 and the coordinator
workflow both require it before implementation, and stage 1's advance check requires an
active plan, so it could not wait for a later stage. It is the only reviewed path the
stage touched; `CURRENT_TASK.yml`, `phase_status.yml`, the lane pointer and the three
generated documents are all on the driver's unreviewed list, which is right - each is
bookkeeping that `check_scope`, `check_contracts` and the generator checks already
enforce exactly.

Three claims in it were checked against their sources rather than accepted:

- `auto_advance: true` and `needs_human_data: false` match `verification/loop_policy.yml`
  lines 67-73.
- The six defects, their IDs and their diagnoses match the six `phase: "11"` entries in
  `backlog.yml` and the phase 11 section of `docs/V2_ROADMAP.md`. The roadmap names five;
  the sixth, `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK`, was filed by Phase 10
  after the roadmap was written, and the plan says so instead of quietly counting six.
- Every code location the plan names was opened and holds the defect claimed:
  `engine.py:76` offers `("fold", "call")` only when `to_call > 0`, `order.py:146`
  measures a raise against `previous_bet` rather than against the last full level,
  `contract.py:298` computes `street_bet + stack`, `postflop_fallback.py:276` iterates
  `("fold", "call")`, `generate_strategy_query_report.py:38` passes `player.street_bet`
  where every other producer passes `state.current_bet`, and `run_verify.py:233` still
  says "directional bound".

## Blocker

None.

## Non-blocker

- The plan's S4 (amending the Phase 01, 02, 03 and 06 contracts) has no stage of its own.
  The loop's stage 1 is the contract stage and stage 4 is tests, so an upstream amendment
  discovered at stage 2 has to land as an extra `contract-update` task with the pointer
  rewound, which is exactly what Phase 10 did at its S4b. The plan should not pretend the
  loop has a slot for it, and it does not: S4 is listed as its own slice with its own
  evidence. Carried rather than fixed, because inventing a stage is a change to the driver
  and this is a phase.
- `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK` is a one-line edit to
  `scripts/run_verify.py`, and that is the same file where this phase registers
  `pytest_engine_fidelity`. Phase 10's stage 5 removed `run_verify.py` from
  `approved_scope` at the freeze, on the ground that a builder editing the command
  registry would be editing its own specification. If phase 11 follows that precedent the
  description fix has to land at or before stage 4, not during the build. Named now so it
  is not discovered at stage 6.
- The plan's Verification section leaves the command IDs to stage 1 rather than repeating
  the skeleton's `pytest_engine_fidelity` as though it were settled. That is correct - the
  contract's own Scope section says the frontmatter is a placeholder from the proposal -
  but it does mean the plan's Verification section is provisional until S1 closes.

## Alignment

None. No long-term drift surfaced by a diff that is one planning document.
