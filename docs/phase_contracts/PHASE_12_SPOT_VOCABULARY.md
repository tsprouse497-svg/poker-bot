---
phase_id: "12"
title: "Spot Vocabulary V2"
depends_on:
  - "11"
required_gate_commands:
  - pytest_spot_vocabulary
  - generate_spot_coverage_report
required_reports:
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_12_SPOT_VOCABULARY.md
---

# Phase 12: Spot Vocabulary V2

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Proposed as phase 12 in `docs/V2_ROADMAP.md`: widen what a spot key can say, so raise size and a second orbit of action stop collapsing into spots that cannot tell them apart.

Phase 12 is limited to the work named by this contract and the active ExecPlan.

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
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_spot_vocabulary`
- `generate_spot_coverage_report`

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
