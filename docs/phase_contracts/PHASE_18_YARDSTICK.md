---
phase_id: "18"
title: "The Yardstick"
depends_on:
  - "14"
required_gate_commands:
  - pytest_playing_strength
  - generate_playing_strength_report
required_reports:
  - reports/active/latest_playing_strength_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_18_YARDSTICK.md
---

# Phase 18: The Yardstick

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Declared by MAINT-35 on 2026-09-21, when Taylor ruled that the goal of this repo is a bot that plays
strong poker. Nothing here measures how well it plays, and the repo says so itself: the committed
`reports/active/latest_profile_comparison_report.txt` reports its one directional figure against five
copies of a check-fold strategy and then states, in its own words, "Producing the other kind of number
needs an opponent with a strategy, and this repo does not have one yet." Every other strength-shaped
figure in the repo is agreement with a chart or distance from a reference range, which is fidelity to a
source rather than money won.

Three things this phase delivers, and they are one instrument rather than three: an opponent pool whose
members have actual strategies, a head-to-head result in chips per 100 hands with error bars wide enough
to say whether a difference is a difference, and a best-response exploitability figure measured against
this repo's own committed strategy rather than against a solver's idea of one.

It depends on 14 because 14 commits the strategy there is anything to measure. It does not depend on 16:
a yardstick that can only read a bot with postflop play could not be built before the postflop play it
is meant to judge, and the number it gives today - what a preflop chart plus a check-fold postflop is
worth - is the baseline every later phase is read against.

Phase 18 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not change the committed chart, its sizing table or its expectations file to improve a number.
  This phase measures what is committed; a measurement that says the chart is wrong is a finding.
- Do not add PokerNow automation or browser observation. Those are phase 20's and stay out here.
- Do not add runtime solver calls or LLM-backed poker decisions.
- Do not add UI surfaces.
- Do not fill a refusal with a heuristic to keep a match running. A refused spot is a measurement of
  coverage and it is phase 19 that answers it.
- Do not report a chips-per-100 figure without its error bar, and do not call a pool member a
  strategy when it is a stub.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_playing_strength_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_playing_strength`
- `generate_playing_strength_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- What each opponent in the pool actually does, in plain words, so a reader can judge whether beating
  it means anything.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not change this contract during implementation mode.
- Do not publish a strength number taken over too few hands to clear its own noise, and do not quote a
  result from one pool as though it held against another.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
