---
phase_id: "06"
title: "Conservative Postflop Fallback For Simulation Continuity"
depends_on:
  - "05"
required_gate_commands:
  - pytest_postflop_fallback
  - generate_postflop_fallback_report
required_reports:
  - reports/active/latest_postflop_fallback_report.txt
  - reports/active/latest_postflop_decision_audit.jsonl
required_phase_audit: reports/phase_audits/PHASE_06_POSTFLOP_FALLBACK.md
---

# Phase 06: Conservative Postflop Fallback For Simulation Continuity

## Scope
Phase 06 delivers the postflop half of a bot that can play a hand to its end.
Phase 05 gave the repo a preflop strategy that answers from committed charts and
refuses everywhere they are silent.
There is no postflop chart, there will not be one in v1, and a simulated hand
that reaches a flop with nothing to ask has nowhere to go.

This phase closes that gap with the smallest thing that is honest: a fallback
that never invests unless the investment cannot lose, and a composite strategy
that routes preflop to the chart and postflop to the fallback so Phase 07 has one
object to hand a hand to.
It is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not add a postflop chart, artifact, or range model.
  Postflop coverage is not a v1 goal, and this phase is what stands in for it.
- Do not add the simulator or profile comparisons.
  Phase 07 consumes the composite strategy this phase ships.
- Do not let the fallback answer a preflop query, and do not let it stand in for
  a preflop chart refusal.
  That is the heuristic guessing for a missing chart spot that v1 forbids.

## Acceptance criteria

### What the fallback is, and what it is not
- The fallback is a continuity device, not a playing strategy, and it is named and
  documented as one in code, in reports, and in the audit packet.
  Nothing in the repo may describe it as postflop strategy.
- It answers flop, turn, and river only.
  A preflop query returns an explicit refusal with its own code rather than a
  passive action, because a preflop spot always has a chart answer or a chart gap
  and this phase is neither.
- What it means downstream is stated rather than left to be discovered: against
  another copy of itself every postflop street checks through, so a hand played by
  this bot is decided preflop and then shown down.
  Phase 07 may measure preflop decisions against that backdrop and may not claim
  postflop quality of any kind.

### Conservative means it never invests unless the investment cannot lose
- It never bets and never raises, at any street, in any spot.
  Aggression needs a sizing source, the repo has none postflop, and a fallback
  that invented one would be a strategy nobody solved.
- It checks whenever checking is legal.
- Facing a bet it folds, with exactly one exception: on the river, when hero's
  hand beats every holding a villain could possibly have, it calls.
  That is a fact rather than a read.
  The board is complete, so the claim is decidable by enumerating the unseen deck.
- The exception is strict.
  A hand that some possible holding ties folds, because a guaranteed chop pays a
  full call to win half a pot and this phase has no oracle for the price at which
  that is correct.
- The exception is river-only, and deliberately so.
  On the flop and the turn the same claim needs every runout enumerated as well,
  and a hand that cannot lose now can be beaten by a card that has not come.
  The gap is recorded in `backlog.yml`, and until it is closed a flop or turn bet
  always takes the pot from this bot.
- There is no pot-odds rule, no hand-strength threshold, and no equity estimate
  against an assumed range.
  Each of those needs a number this repo cannot source, and a fallback carrying
  one would be indistinguishable from a strategy while resting on an invention.

### Totality and legality hold by enumeration
- Totality holds by exhaustive enumeration over engine-legal postflop states
  rather than by sampling: for every legal-action set the engine can produce
  postflop, at every street, the fallback returns a `StrategyDecision`.
  It never refuses postflop, never raises an exception, and never returns nothing.
- The enumeration covers every postflop legal-action set the engine's own
  `legal_actions` can produce, in both the free and the facing-a-bet shapes, and
  includes a hero whose whole remaining stack is less than the price to call.
- Every returned decision is legal, and legality is proved by routing each
  decision through the Phase 03 `DecisionAuditRecord`, which rejects an action
  outside `legal_actions`, an amount above all-in, and an amount below the
  minimum raise target.
- The river call rule is proved in both directions and by example, not only in
  aggregate: a named board and holding that cannot lose calls, a named board and
  holding that a single villain combination beats folds, and a named board and
  holding that can only be tied folds.
  Each example is written so a reviewer can check it against the cards by hand.
- Decisions are invariant under suit relabelling and hole-card order: two queries
  that differ only by a consistent suit permutation or by the order of the hole
  cards return the same decision.
- Decisions are byte-deterministic.
  The same query serializes to the same decision audit line on every run, and the
  fallback holds no state between calls.

### The composite strategy
- One strategy object plays a whole hand: preflop from the Phase 05 chart
  strategy, flop through river from the fallback.
  Phase 07 consumes this rather than assembling the routing itself, so there is
  one place that decides which component owns a street.
- It satisfies the Phase 03 strategy protocol and returns a `StrategyDecision` or
  a `StrategyRefusal`, never both and never neither.
- Every outcome names which component produced it, so a decision audit line can
  be attributed to the chart or to the fallback without reading code.
- The composite adds no decision of its own.
  For any query its outcome is the outcome its component would have returned, and
  a test asserts that over the enumeration rather than by inspection.
- A preflop chart refusal passes through as a refusal, carrying its original
  reason code.
  Substituting a passive action there would erase exactly the coverage signal
  Phases 04 and 05 were built to produce.

### Reports and gate
- The postflop fallback report shows, for a non-coding reviewer: how many states
  the enumeration covered, how many chose each action, every distinct decision
  code with its count, the count of postflop refusals which must be zero, and the
  worked river examples with their cards spelled out.
- The report also shows what the composite does over the committed sample hands,
  broken out by which component answered, so the preflop-and-then-showdown shape
  of a hand is visible rather than asserted.
- The postflop decision audit is committed as JSONL in the Phase 03 record shape,
  so the reader that already checks preflop decisions checks these unchanged.
- At least one number in the report is recomputable by hand from a committed file
  without reading code, and the audit packet says which number and how.
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- The judgment calls recorded in
  `reports/phase_audits/decisions/PHASE_06_POSTFLOP_FALLBACK_DECISIONS.md` carry a
  reversibility class before implementation begins, and the audit packet records
  the outcome of each one.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_postflop_fallback_report.txt`
- `reports/active/latest_postflop_decision_audit.jsonl`

## Required command IDs
- `pytest_postflop_fallback`
- `generate_postflop_fallback_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- The worked river examples, with cards, so the one place this bot puts money in
  postflop can be checked by hand.
- A plain statement of what a hand played by this bot looks like, and therefore
  what Phase 07 may and may not claim from it.
- The recorded judgment calls and what each one changed.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not give the fallback a bet or a raise, and do not add a sizing table to
  make one possible.
- Do not let the fallback answer a preflop query, and do not let the composite
  convert a preflop chart refusal into an action.
- Do not approximate the river unbeatable test.
  A hand-category shortcut, a nut-hand lookup table, or a sampled subset of the
  unseen deck all turn a fact back into a guess.
- Do not relax the strictness of that test to include hands that can be tied in
  order to make the bot call more often.
- Do not weaken Phase 03 decision validation, Phase 04 import validation, or
  Phase 05 chart refusals to admit a fallback decision.
- Do not describe the fallback as a postflop strategy in code, documentation, or
  reports.
- Do not replace or retire the Phase 03 reference check-fold strategy, which is a
  contract reference and not this phase's concern.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- The Phase 03 strategy query report and its decision audit keep their existing
  paths and content, so this phase's audit is a new file rather than a rewrite of
  an existing one.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
