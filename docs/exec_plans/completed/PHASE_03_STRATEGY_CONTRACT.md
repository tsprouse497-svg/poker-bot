# Phase 03 ExecPlan: Strategy Contract And Deterministic Decision Audit Shape

## Objective

Complete the Phase 03 gate: turn-order layer in the poker core, fail-closed
turn-order enforcement in replay, the deterministic strategy query/decision
contract with a first-class refusal outcome, JSONL decision audits, the
check-fold reference strategy, and the strategy query report.

## Scope

Approved files are controlled by `CURRENT_TASK.yml` (narrow Phase 03 list:
`poker_core/order.py`, `strategy/**`, replay integration, new tests, report
generator, fixtures, and docs). Forbidden: `data/raw/**`, `data/processed/**`,
contract edits, and all V1 boundaries in `AGENTS.md`.

## Delegation Plan

- Worker lanes: Worker A implements the turn-order layer; Worker B implements
  the strategy contract package. Both are implementation subagents working in
  the shared tree on disjoint new files.
- Ownership: Worker A owns `src/poker_training_bot/poker_core/order.py` and
  `tests/test_action_order.py`. Worker B owns
  `src/poker_training_bot/strategy/contract.py`,
  `src/poker_training_bot/strategy/reference.py`, and
  `tests/test_strategy_contract.py`. The coordinator owns replay integration,
  fixture corrections, `scripts/generate_strategy_query_report.py`, command
  registration, docs, the audit packet, and closeout.
- Expected outputs: each worker returns a changed-file summary plus passing
  focused tests for its lane; the coordinator integrates and runs the full
  derived gate.
- Status: Worker A completed (order.py, 18 tests); Worker B completed
  (contract.py, reference.py, 38 tests); coordinator integration completed
  (replay enforcement, fixtures, report generator, command registration).
- Integration order: Worker A lands first (replay integration depends on the
  turn-order API), Worker B is independent; the coordinator then wires replay
  and the report generator, and updates this plan.
- Review handoff: the independent read-only reviewer inspects the full Phase 03
  diff with emphasis on turn-order rules (big-blind option, under-raise
  reopening, round completion), replay enforcement gaps, and decision-audit
  determinism.

## Slices

- [x] Turn-order layer (`poker_core/order.py`) with focused tests.
- [x] Strategy contract package (`strategy/contract.py`, `strategy/reference.py`)
  with focused tests.
- [x] Replay enforces turn order; fixtures corrected with explicit checks.
- [x] Strategy query report generator and command registration.
- [x] Full derived gate, independent review, audit packet; review found two
  real bugs (under-raise bar overwritten; min-raise not updated after a bet),
  both fixed with regression tests.

## Verification

Command IDs: `pytest_strategy_contract`, `generate_strategy_query_report`,
plus the full derived gate. Reports:
`reports/active/latest_strategy_query_report.txt`,
`reports/active/latest_decision_audit.jsonl`.

## Outcome

Gate completed 2026-08-11. Both worker lanes delivered as specified and
integrated cleanly; the independent review then caught one bug in a worker
lane (under-raise bar overwritten by a second short all-in) and one
pre-existing engine bug (minimum raise not updated after a postflop bet),
both fixed before the gate commit. The turn-order decision from the phase
opening held: the engine owns action order, and replay plus the strategy
query path consume it from one place. Deferred: `UNDER-RAISE-ACCUMULATION`
and `FOLD-WHEN-FREE` in `backlog.yml`.

## Next Agent Bootstrap

Task `PHASE-03-STRATEGY-CONTRACT` is active (implementation mode, base commit
`c15d8453f7736af42be530ef8d41914ea52fb9b3`). Contract:
`docs/phase_contracts/PHASE_03_STRATEGY_CONTRACT.md`. State: worker lanes
delegated per the Delegation Plan. Next command:
`uv run python scripts/run_verify.py` after integration.
