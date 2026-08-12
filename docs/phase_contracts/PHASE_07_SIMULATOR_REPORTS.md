---
phase_id: "07"
title: "Offline Simulator And Bot/Profile Comparison Reports"
depends_on:
  - "06"
required_gate_commands:
  - pytest_simulator
  - generate_profile_comparison_report
required_reports:
  - reports/active/latest_profile_comparison_report.txt
required_phase_audit: reports/phase_audits/PHASE_07_SIMULATOR_REPORTS.md
---

# Phase 07: Offline Simulator And Bot/Profile Comparison Reports

## Scope
Phase 06 gave the repo one strategy object that can play a hand from the first
preflop decision to showdown.
Nothing yet deals that hand.
This phase adds the dealer: a deterministic offline simulator that seats profiles,
runs hands through the Phase 01 engine, asks each seat's strategy for its action,
awards the pot, and reports what happened.

It is limited to the work named by this contract and the active ExecPlan.

The point of the phase is measurement, and the honest boundary of that measurement
is set by Phase 06.
Against another copy of itself the bot checks every postflop street, so a hand it
plays is decided preflop and then shown down.
That makes this a preflop measurement instrument with showdown resolution, and the
contract says so out loud rather than letting a reader infer a full-hand claim from
a report that happens to print river numbers.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not add a postflop strategy, chart, or sizing scheme.
  Phase 06 ruled that out and `V2-POSTFLOP-STRATEGY` holds it.
- Do not add hand-history ingestion or player-tendency comparison.
  Phase 08 consumes what this phase produces.
- Do not add a bankroll model, rake, tournament structure, or antes.
  Cash-game blinds at a single depth are the whole scope.

## Acceptance criteria

### The simulator is a dealer, not a second engine
- The simulator owns dealing, street progression, and pot award, and owns no poker
  rules of its own.
  Legality, turn order, betting arithmetic, and hand ranking come from the Phase 01
  engine and evaluator; the simulator asks and applies rather than deciding.
- Every action it applies to the engine came from a strategy's `StrategyDecision`.
  The simulator never substitutes an action of its own, and a hand in which it would
  have to is an error rather than a hand that quietly continues.
- A `StrategyRefusal` ends the hand as an explicit outcome with the refusal's own
  reason code recorded, rather than being converted into a check, a fold, or a
  skipped seat.
  A refused hand is a coverage measurement, so it is counted and reported and never
  silently dropped from a total.
- Chips are conserved: for every hand, the sum of stack changes across all seats is
  zero, and the pot awarded equals the pot collected.
  This is asserted per hand over the whole simulation rather than in aggregate,
  because an aggregate that nets to zero can hide two errors that cancel.

### Determinism is the property the whole phase rests on
- A simulation is a pure function of its seed, its seating, and its profiles.
  The same inputs produce the same hands, the same decisions, and the same report,
  byte for byte, across runs and across processes.
- Shuffling is seeded and reproducible without the `random` module's global state,
  and the seed that produced a hand is recorded with it, so any single hand can be
  replayed on its own.
- Every hand the simulator deals is expressible in the Phase 02 normalized
  hand-history schema, and a dealt hand fed back through the Phase 02 replayer
  reproduces the same decision points.
  That is the cross-check that the simulator and the replayer agree about what a hand
  is; without it they are two independent stories about the same rules.
- The seed appears in the report, so a number a reader disputes can be regenerated.

### Profiles name what is being compared
- A profile is a named pairing of a strategy with the metadata a report needs to
  label it, and nothing more.
  It carries no poker logic; two profiles differing only in name must play
  identically.
- The composite strategy from Phase 06 is available as a profile, and so is the
  Phase 03 reference check-fold strategy, which gives the comparison a floor that is
  deliberately bad and already trusted.
- A profile that a simulation cannot seat is rejected at setup with a named reason,
  not part way through a hand.

### What the comparison report may and may not claim
- The report states, in plain language and before any number, that every postflop
  street checks through in self-play, so what follows measures preflop decisions with
  equity realized at showdown.
  It makes no postflop claim of any kind.
- It reports per profile: hands played, hands refused with their reason codes, chips
  won and lost, and the same figure normalized per hand at a stated stake, so two
  runs of different lengths can be compared.
- Refusal coverage is a headline number, not a footnote.
  A profile that refuses most hands has not been measured, and the report must make
  that impossible to miss.
- Any result the simulation cannot separate from noise is reported as such.
  A chip difference smaller than the run's own variation is not a finding, and the
  report does not print it as one.
- At least one number in the report is recomputable by hand from a committed file
  without reading code, and the audit packet says which number and how.

### Totality and legality hold by construction
- Every hand runs to a terminal state: a showdown, an uncontested win, or a recorded
  refusal. No hand ends by exhaustion, exception, or timeout.
- Every decision the simulation applies is recorded as a Phase 03
  `DecisionAuditRecord`, which is what proves legality, and the recorded audit for a
  simulation is regenerable from its seed.
- The simulation is exercised over enough hands for every seat to have occupied every
  position and for both terminal outcomes to occur, and the report shows those counts
  rather than asserting the coverage.

### Reports and gate
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- The judgment calls recorded in
  `reports/phase_audits/decisions/PHASE_07_SIMULATOR_REPORTS_DECISIONS.md` carry a
  reversibility class before implementation begins, and the audit packet records the
  outcome of each one.
- The gate stays within a run time a person will actually wait for, and the hand count
  the gate simulates is stated in the report rather than tuned silently.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_profile_comparison_report.txt`

## Required command IDs
- `pytest_simulator`
- `generate_profile_comparison_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- A plain statement of what the comparison measures and what it does not, carried
  forward from Phase 06 rather than restated loosely.
- The chip-conservation and replay cross-check evidence.
- The recorded judgment calls and what each one changed.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not mock the engine, the evaluator, the strategies, or the replayer.
  A simulator tested against a fake dealer has been tested against nothing.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not convert a `StrategyRefusal` into an action, a skipped seat, or a discarded
  hand. That erases the coverage signal Phases 04 through 06 exist to produce.
- Do not seed from the clock, the process, or anything else a rerun cannot reproduce.
- Do not report a chip difference as a finding without showing it exceeds the run's
  own variation.
- Do not describe any output of this phase as measuring postflop play.
- Do not tune the hand count until a comparison comes out a particular way.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- The Phase 02 replayer and the Phase 06 composite are consumed unchanged; neither is
  loosened to make a simulated hand fit.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
