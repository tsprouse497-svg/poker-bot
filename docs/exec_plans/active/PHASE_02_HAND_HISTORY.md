# Phase 02 ExecPlan: Normalized Hand-History Schema And Deterministic Replay

## Objective

Complete the Phase 02 gate by adding a strict normalized hand-history model and
deterministic replay report that uses the existing Phase 01 NLHE core engine.

## Scope

Approved files are controlled by `CURRENT_TASK.yml`. This plan stays inside
`docs/**`, `scripts/**`, `src/**`, `tests/**`, `reports/**`, `data/samples/**`,
and root generated status/task metadata.

Forbidden scope:

- `data/raw/**`
- `data/processed/**`
- Contract edits outside explicit contract-update mode
- PokerNow automation, browser/platform observation, runtime solver calls,
  LLM-backed poker decisions, and training UI surfaces

## Delegation Plan

- No-delegation exception: Phase 02 implementation was completed before the
  mandatory early delegation checkpoint existed; future active ExecPlans must
  document worker lanes or a concrete exception before implementation starts.
- Addendum (2026-08-10): the uncontested-replay addendum below is
  coordinator-implemented because the schema, replay, and settlement changes
  are one tightly coupled slice smaller than the delegation overhead.
  Independent read-only review is delegated to a review subagent and its
  findings are recorded in the Phase 02 audit packet addendum.

## Slices

- [x] Activate Phase 02 task metadata and create this ExecPlan.
- [x] Define normalized hand-history schema objects with fail-closed validation.
- [x] Add deterministic replay from normalized records into Phase 01 settlement.
- [x] Add tiny committed sample fixtures and focused tests.
- [x] Add `pytest_hand_history` and `generate_replay_report` command IDs.
- [x] Generate the Phase 02 replay report and generated status docs.
- [x] Run full verifier/report gate and independent read-only review.
- [x] Write the Phase 02 audit packet and commit the passing gate.

## Addendum Slices (2026-08-10): Uncontested Hands

- [x] Settle uncontested (fold-out) hands through `settle_uncontested`; the
  remaining player wins the whole pot and `showdown` must be empty.
- [x] Validate street contiguity and exact per-street board-card counts.
- [x] Allow short-stack all-in blind posts below the configured blind.
- [x] Give the Phase 01 golden-hand report its own output file so the Phase 02
  report no longer overwrites it; contract path cleanup recorded in
  `backlog.yml` as `CONTRACT-REPORT-PATHS`.
- [x] Add fold-out fixtures, tests, and schema-doc updates.
- [x] Validate blind posting against button-derived blind seats; a short
  all-in blind no longer lowers the call price or minimum raise.
- [x] Run full verifier gate, independent review, and audit packet addendum;
  review found three real bugs, fixed and recorded in the audit packet.

## Verification

Required Phase 02 command IDs:

- `pytest_hand_history`
- `generate_replay_report`

Regression and repo hygiene command IDs:

- `generate_status`
- `generate_phase_ledger`
- `generate_backlog`
- `check_generated_status`
- `check_generated_phase_ledger`
- `check_generated_backlog`
- `check_contracts`
- `check_scope`
- `check_file_sizes`
- `import_smoke`
- `uv_import_smoke`
- `pytest_poker_core`
- `pytest`
- `ruff_check`

Required report:

- `reports/active/latest_replay_report.txt`

## Outcome

Phase 02 implementation is complete. The independent read-only review found
action-legality and closed-schema gaps; both were fixed before closeout, then
the read-only recheck reported no remaining implementation or verifier findings.

## Next Agent Bootstrap

Start from `AGENTS.md`, `CURRENT_TASK.yml`, `phase_status.yml`,
`docs/phase_contracts/PHASE_02_HAND_HISTORY.md`, and this ExecPlan. Run
`uv run python scripts/run_verify.py --commands pytest_hand_history
generate_replay_report` for a focused Phase 02 check, then the full Phase 02
gate after implementation.
