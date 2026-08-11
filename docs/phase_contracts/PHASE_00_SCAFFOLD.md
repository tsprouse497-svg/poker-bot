---
phase_id: "00"
title: "Scaffold, Contracts, Tooling, Verifier, Reports, Coordinator Workflow"
depends_on: []
required_gate_commands:
  - check_scope
  - check_contracts
  - check_generated_status
  - check_file_sizes
  - import_smoke
  - pytest
  - ruff_check
required_reports:
  - reports/active/verify_results.json
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_00_SCAFFOLD.md
---

# Phase 00: Scaffold, Contracts, Tooling, Verifier, Reports, Coordinator Workflow

## Scope
Phase 00 is limited to the work named by this contract and the active ExecPlan.

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
- `reports/active/verify_results.json`
- `reports/active/latest_verify.txt`

## Required command IDs
- `check_scope`
- `check_contracts`
- `check_generated_status`
- `check_file_sizes`
- `import_smoke`
- `pytest`
- `ruff_check`

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

