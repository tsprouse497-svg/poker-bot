---
phase_id: "08"
title: "Tiny Normalized Sample Ingestion And Player Tendency Comparison"
depends_on:
  - "07"
required_gate_commands:
  - pytest_sample_comparison
  - generate_sample_comparison_report
required_reports:
  - reports/active/latest_sample_comparison_report.txt
required_phase_audit: reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md
---

# Phase 08: Tiny Normalized Sample Ingestion And Player Tendency Comparison

## Scope
Phase 08 is limited to the work named by this contract and the active ExecPlan.

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
- `reports/active/latest_sample_comparison_report.txt`

## Required command IDs
- `pytest_sample_comparison`
- `generate_sample_comparison_report`

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
