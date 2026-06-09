---
phase_id: "02"
title: "Normalized Hand-History Schema And Deterministic Replay"
status: future
depends_on:
  - "01"
required_gate_commands:
  - pytest_hand_history
  - generate_replay_report
required_reports:
  - reports/active/latest_replay_report.txt
required_phase_audit: reports/phase_audits/PHASE_02_HAND_HISTORY.md
---

# Phase 02: Normalized Hand-History Schema And Deterministic Replay

## Scope
Phase 02 is limited to the work named by this contract and the active ExecPlan.

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
- `reports/active/latest_replay_report.txt`

## Required command IDs
- `pytest_hand_history`
- `generate_replay_report`

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
