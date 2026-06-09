---
phase_id: "06"
title: "Conservative Postflop Fallback For Simulation Continuity"
status: future
depends_on:
  - "05"
required_gate_commands:
  - pytest_postflop_fallback
  - generate_decision_audit
required_reports:
  - reports/active/latest_decision_audit.jsonl
required_phase_audit: reports/phase_audits/PHASE_06_POSTFLOP_FALLBACK.md
---

# Phase 06: Conservative Postflop Fallback For Simulation Continuity

## Scope
Phase 06 is limited to the work named by this contract and the active ExecPlan.

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
- `reports/active/latest_decision_audit.jsonl`

## Required command IDs
- `pytest_postflop_fallback`
- `generate_decision_audit`

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
