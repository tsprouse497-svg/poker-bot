---
phase_id: "05"
title: "Full-Table Preflop Strategy From Committed Artifacts/Charts"
depends_on:
  - "04"
required_gate_commands:
  - pytest_full_table_preflop
  - generate_preflop_strategy_report
  - generate_strategy_query_report
required_reports:
  - reports/active/latest_preflop_strategy_report.txt
  - reports/active/latest_strategy_query_report.txt
required_phase_audit: reports/phase_audits/PHASE_05_FULL_TABLE_PREFLOP.md
---

# Phase 05: Full-Table Preflop Strategy From Committed Artifacts/Charts

## Scope
Phase 05 delivers a preflop playing strategy that answers from committed chart
artifacts alone, and the full-table six-max 100bb artifact it answers from.
Phase 04 proved one artifact could be imported and looked up.
Phase 05 turns that lookup into a strategy that satisfies the Phase 03 contract,
and replaces the hand-authored reference chart with a real solver export whose
frequencies can be checked against their published source.
It is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not add postflop strategy; a postflop query is out of this phase's scope and
  Phase 06 covers the conservative fallback.
- Do not add the simulator or profile comparisons; Phase 07 consumes this
  strategy.
- Do not add table sizes other than six or stack depths other than 100bb.
  Both are artifact coverage questions, and an uncovered table or depth must
  refuse.
- Do not add second-orbit coverage (facing a four-bet or later).
  `SECOND-ORBIT-PREFLOP-SPOTS` records the gap and such a spot must refuse.

## Acceptance criteria

### The committed artifact
- One artifact covering the six-max 100bb first-two-decisions matrix is committed
  under `data/artifacts/preflop/` and imports through the Phase 04 importer with
  no change to the importer's validation.
- Its `source.kind` is `solver-export` and `source` names the solution it came
  from, including the rake structure the solution was solved under, because a
  raked solution's ranges differ materially from a rake-free one.
- Provenance is a human attestation, not a machine fact: the checksum in
  `audit_fields` covers weights only, so the audit packet must record who
  attested the export's origin and how it was obtained.
- The artifact is reproducible from a committed input: the source export is
  committed alongside a converter script, and re-running the converter over that
  input reproduces the committed artifact byte for byte.
- Spot coverage is stated as data, not prose: every opening spot for each
  position that can open, every spot facing a single open, every spot where the
  original raiser faces a three-bet, and the big blind facing a small-blind limp.
- The hand-authored `six_max_100bb_core.json` is retired in the same change, so
  the repo holds one authority for a given table size and stack depth and the
  chart library cannot see two artifacts claiming the same spot.

### Frequencies check against the source
- The artifact carries a committed expectation table of aggregate frequencies
  taken from the published source, and tests assert the imported artifact
  reproduces them within a stated tolerance.
- The expectation table is written in reviewable poker terms, at minimum the
  opening frequency for each position that can open and the total defence
  frequency for the big blind facing each open.
- This is the phase's external oracle: it is the only criterion whose target
  numbers were not produced by this repo, and it must fail if the artifact's
  ranges drift from the source.

### Position and action vocabulary
- Source position names are mapped to `poker_core.positions`, never renamed
  inside it, and the mapping is explicit and tested.
  A six-max table is `LJ`, `HJ`, `CO`, `BTN`, `SB`, `BB`, so a source label for
  the first seat to act maps to `LJ`.
- A spot key carries no raise size, so every raise sizing offered at a spot
  collapses into the single `raise` action by summing its weights, and an
  all-in offer is a raise like any other.
  The collapse is stated in `audit_fields.notes` and reported, so no weight is
  silently discarded.

### The strategy
- A preflop chart strategy satisfies the Phase 03 strategy protocol and returns
  a `StrategyDecision` or a `StrategyRefusal`, never both and never neither.
- It builds its chart query from game state through the same derivation Phase 04
  ships: table size, stack depth, hero position, and the ordered preflop action
  sequence in front of hero.
  It does not spell a spot key by hand.
- Mixed frequencies collapse to one action deterministically: the highest-weight
  legal action wins, and an exact tie refuses rather than picking.
  The rule is named in the decision rationale, and the full weight vector the
  decision came from is recorded in the decision audit.
- Raise amounts come from a committed sizing table sourced from the same solution
  as the ranges, with its own recorded provenance.
  A raise the sizing table does not cover refuses; the strategy never invents a
  size.
- Stack depth must match the artifact exactly.
  There is no rounding, no nearest-depth fallback, and no tolerance band, so an
  87bb or 143bb table refuses with a depth miss code.
- A table carrying a straddle, an ante, or any blind structure the artifact
  cannot express refuses rather than reading the pot as ordinary.
  `BLIND-STRUCTURE-VARIANTS` records the gap.
- Every refusal carries a reason code derived from the underlying chart miss, so
  a refusal can be traced to the coverage that was absent.

### Totality, legality, and determinism
- Totality holds by enumeration, not by sampling: across every committed spot and
  all 169 hand classes the strategy returns a decision, and across an enumeration
  of reachable six-handed preflop states it returns a decision or a refusal.
  It never raises and never returns nothing.
- Every returned decision is legal.
  Legality is proved by routing decisions through the Phase 03 decision audit
  record, which rejects an action outside `legal_actions`, an amount above
  all-in, and an amount below the minimum raise target.
- Decisions are invariant under suit relabelling and hole-card order: any two
  queries that canonicalize to the same hand class return the same decision.
- Decisions are byte-deterministic: the same query serializes to the same
  decision audit line every run.
- "Full table" means every seat at a six-handed 100bb table can be asked and gets
  either a chart-backed decision or an explicit refusal.
  It does not claim every seat is covered by the chart, and the report must show
  which is which.

### Reports and gate
- The preflop strategy report shows, for a non-coding reviewer, the covered
  spots, the decision the strategy takes for a named sample of hands per spot,
  the refusal codes and their counts over the enumeration, and the aggregate
  frequencies next to their expected values from the source.
- At least one number in the report is recomputable by hand from a committed file
  without reading code, and the audit packet says which number and how.
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- The judgment calls recorded in `reports/phase_audits/decisions/PHASE_05_FULL_TABLE_PREFLOP_DECISIONS.md`
  are answered before implementation begins, and the audit packet records the
  outcome of each one.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_preflop_strategy_report.txt`
- `reports/active/latest_strategy_query_report.txt`

## Required command IDs
- `pytest_full_table_preflop`
- `generate_preflop_strategy_report`
- `generate_strategy_query_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- The provenance attestation for the committed export, naming who attested it.
- The answered judgment-call list and what each answer changed.
- Aggregate frequencies next to their expected values from the source.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not fabricate solver output, and do not label a hand-authored range as a
  solver export.
- Do not fill an uncovered spot, hand class, or stack depth with a default
  action, a nearest match, or an interpolation.
- Do not invent a raise size, and do not weaken the sizing table to avoid a
  refusal.
- Do not soften the frequency expectation table to make an artifact pass; a
  disagreement between the artifact and its source is a finding, not a tolerance
  to widen.
- Do not loosen Phase 04 import validation or Phase 03 decision validation to
  admit the new artifact.
- Do not resolve a weight tie by picking an action.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Retiring the hand-authored chart keeps the Phase 04 gate green, including its
  committed-artifact tests and chart coverage report.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
