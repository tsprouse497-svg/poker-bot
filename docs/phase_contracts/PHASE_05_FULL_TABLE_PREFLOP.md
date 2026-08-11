---
phase_id: "05"
title: "Full-Table Preflop Strategy From Committed Artifacts/Charts"
depends_on:
  - "04"
required_gate_commands:
  - pytest_full_table_preflop
  - generate_strategy_query_report
required_reports:
  - reports/active/latest_strategy_query_report.txt
required_phase_audit: reports/phase_audits/PHASE_05_FULL_TABLE_PREFLOP.md
---

# Phase 05: Full-Table Preflop Strategy From Committed Artifacts/Charts

## Scope
Phase 05 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_strategy_query_report.txt`

## Required command IDs
- `pytest_full_table_preflop`
- `generate_strategy_query_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
