---
phase_id: "04"
title: "Preflop Artifact/Chart Contract, Importer, And Fail-Closed Lookup"
depends_on:
  - "03"
required_gate_commands:
  - pytest_preflop_artifacts
  - generate_preflop_chart_report
  - generate_strategy_query_report
required_reports:
  - reports/active/latest_preflop_chart_report.txt
  - reports/active/latest_strategy_query_report.txt
required_phase_audit: reports/phase_audits/PHASE_04_PREFLOP_ARTIFACTS.md
---

# Phase 04: Preflop Artifact/Chart Contract, Importer, And Fail-Closed Lookup

## Scope
Phase 04 delivers the committed preflop artifact format, the canonical position
and spot vocabulary charts are keyed by, a fail-closed importer, and a
fail-closed chart lookup.
It is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not wire charts into a playing strategy or into the simulator; Phase 05
  consumes this lookup and Phase 06 covers postflop.
- Do not ship full-table chart coverage. One real committed artifact is enough
  to prove import and lookup; broad coverage belongs to Phase 05.

## Acceptance criteria
- The poker core gains a canonical position vocabulary: `poker_core.positions`
  derives position labels from occupied seats, the button seat, and table size
  for two through nine seats, and it is the only source of position names.
  Heads-up derives button/small-blind and big-blind; larger tables derive small
  blind, big blind, the under-the-gun run, and the late positions through
  cutoff and button.
- A canonical spot key is derived, never hand-written: one function maps table
  size, stack depth in big blinds, hero position, and the ordered preflop
  action sequence in front of hero to a stable spot key string. The importer and
  the lookup both use that same function, so a spot that imports is reachable by
  a lookup built from game state.
- Hand classes use canonical 169-class notation (`AA`, `AKs`, `AKo`).
  Canonicalization is order-independent and suit-independent: any two hole cards
  map to exactly one class, and the class round-trips through the importer and
  the lookup unchanged.
- The `solver_artifacts` package defines the versioned artifact schema with the
  required fields named in `docs/PREFLOP_ARTIFACT_CONTRACT.md`:
  `artifact_schema_version`, `source`, `generated_at`, `table_size`,
  `stack_depth_bb`, `positions`, `spots`, `action_weights`, and `audit_fields`.
  `spots` declares spot metadata, `action_weights` maps spot key to hand class to
  action weights, and `audit_fields` carries verifiable import evidence
  including a content checksum over the weights.
- Artifact import is fail-closed and total: a missing field, an unknown field, an
  unsupported `artifact_schema_version`, a position outside the derived
  vocabulary for the declared table size, a spot key that does not match its
  derived value, a duplicate spot, an unknown or duplicate hand class, an
  unknown action name, a negative weight, weights that do not sum to one within
  the declared tolerance, `action_weights` for an undeclared spot, a spot with no
  weights, or a checksum mismatch each raises with a specific reason code and
  yields no partially loaded chart.
- Chart lookup is fail-closed: a query whose table size, stack depth, position,
  spot key, or hand class is not covered returns an explicit miss carrying a
  reason code. No default action, no nearest spot, no nearest stack depth, no
  interpolation, and no heuristic fill.
- Chart lookup is deterministic: identical inputs return identical results, and
  returned action weights carry a stable ordering.
- At least one real preflop chart artifact is committed under `data/artifacts/`,
  imports cleanly, and is exercised by tests. Uncovered spots stay uncovered and
  are reported rather than filled.
- The chart coverage report lists each imported artifact, its source and
  checksum verdict, its spot count, its covered positions, and its covered hand
  class count, so a non-coding reviewer can judge coverage without reading code.
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_preflop_chart_report.txt`
- `reports/active/latest_strategy_query_report.txt`

## Required command IDs
- `pytest_preflop_artifacts`
- `generate_preflop_chart_report`
- `generate_strategy_query_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not fabricate solver output. A committed artifact must declare in `source`
  what produced it, and a hand-authored chart must say so.
- Do not soften import validation to make a committed artifact pass.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
