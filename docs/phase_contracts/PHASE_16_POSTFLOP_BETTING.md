---
phase_id: "16"
title: "Postflop That Can Bet"
depends_on:
  - "15"
required_gate_commands:
  - pytest_postflop_betting
required_reports:
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md
---

# Phase 16: Postflop That Can Bet

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Proposed as phase 16 in `docs/V2_ROADMAP.md`: replace the conservative fallback with postflop play that can invest.
It opens the way Phase 08 did, blocked on a source the repo does not have, and its contract stage is where that source gets chosen rather than assumed.

Phase 16 is limited to the work named by this contract and the active ExecPlan.

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
- `pytest_postflop_betting`

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
