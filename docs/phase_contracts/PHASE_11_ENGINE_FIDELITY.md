---
phase_id: "11"
title: "Engine And Query Fidelity"
depends_on:
  - "09"
required_gate_commands:
  - pytest_engine_fidelity
  - generate_engine_fidelity_report
required_reports:
  - reports/active/latest_engine_fidelity_report.txt
required_phase_audit: reports/phase_audits/PHASE_11_ENGINE_FIDELITY.md
---

# Phase 11: Engine And Query Fidelity

## Scope
Phase 11 closes six correctness defects that v1's own reviews found, diagnosed, and
filed, none of which the phase that found them was allowed to fix.
Each of them sits underneath a later measurement, which is why they are closed before
anything derives a chart from the solver export or re-measures agreement against real
hands.
A phase that fixes measurement bugs after the measurements are taken is a phase that
invalidates them.

The six are the `phase: "11"` entries in `backlog.yml`, and this contract is written
against them rather than against a fresh reading of the code:

- `FOLD-WHEN-FREE`: the engine calls a fold illegal whenever checking is free, so a real
  history containing a surrendered river or a timed-out check does not replay at all.
- `UNDER-RAISE-ACCUMULATION`: consecutive short all-ins that together amount to a full
  raise never reopen betting, because each is measured against the bet level immediately
  before it rather than against the last full one.
- `STREET-BET-MEANING-AMBIGUOUS`: `StrategyQuery.street_bet` has two readings, carries no
  docstring saying which is meant, and one producer uses the other one, so replayed hands
  reach the chart with a mis-derived stack depth and refuse for the wrong reason.
- `DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE`: the decision audit's all-in ceiling is too high
  by exactly the price to call, so the legality proof several contracts lean on is weaker
  than those contracts say.
- `FALLBACK-FAIL-CLOSED-CAN-CALL`: the postflop fallback's fail-closed branch can invest,
  and can return a postflop refusal, both of which the Phase 06 contract states never
  happen.
- `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK`: the command registry describes
  `check_solver_export_expectations` as recomputing a directional bound that was withdrawn
  on 2026-08-18.

Four of these change behaviour that an earlier contract states as an acceptance criterion.
Those contracts are amended in `contract-update` mode, before any test is frozen against
them, and never during implementation.
The amendments are part of this phase's work rather than a side effect of it: a fix that
leaves the contract behind it saying the opposite is a fix that the next reader has to
adjudicate.

This phase commits no data.
No chart, artifact, sample, source card, or committed export changes, and no agreement
rate, refusal inventory, or coverage number is recomputed here.
Several existing numbers do move once the engine and the query are corrected; naming the
phase that owns each of them is this phase's job, re-measuring is not.

Phase 11 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not change the spot-key vocabulary. Sizing-aware keys and a position acting twice
  are proposed phase 12, and a fidelity fix that quietly widened the key would take that
  phase's decision away from it.
- Do not change what the query can carry about table state. Per-seat committed chips,
  straddles, antes, and asymmetric effective stacks are proposed phase 13.
- Do not derive, convert, or retire any preflop chart. That is proposed phase 14.
- Do not give the postflop fallback a bet, a raise, or a new calling rule. Its one
  investment path is Phase 06's and stays exactly as wide as Phase 06 left it.

## Acceptance criteria

### A fold is legal whenever a seat may act
- The engine offers `fold` in every state where the seat to act has any legal action at
  all, including states where checking is free.
  Folding for nothing is a bad play and a legal one, and a replayer that rejects it cannot
  ingest anybody's real hands, which is the concrete cost this defect carries.
- Nothing else about a free spot changes: `check` stays legal exactly when the price to
  call is zero, and the bet or raise on offer is the one the engine already offered.
- Folding for free commits no chips, ends the seat's involvement, and leaves the pot,
  the current bet, and the minimum raise untouched.
  A test asserts that against a recorded hand where the fold happens on a street with no
  bet in it, and the hand still settles to its recorded result.
- `StrategyQuery` stops asserting that `check` and `fold` can never both be legal, because
  after this change the engine produces exactly that set and a query that refuses to
  describe an engine-legal state is a query that lies about the game.
  This is the one validation this phase is permitted to remove, named here so that removing
  it is a ruling rather than a convenience: the invariant became false, and the criterion
  below - that no shipped strategy folds for free - is what replaces the protection it gave.
  Every other guard in `StrategyQuery` stays, including the one that `check` is legal
  exactly when the price to call is zero.
- No strategy shipped in this repo ever chooses to fold when checking is free.
  The rule is proved over the postflop enumeration and over the preflop chart's own
  answers rather than asserted, because making an action legal and making a bot take it
  are different things and only the first one is wanted here.
- Replay accepts a recorded fold on a street with no bet in it: such a hand replays end to
  end through `replay_hand`, settles to its stated result, and the folding seat is absent
  from the showdown.
  The hand is constructed inside the test rather than added to `data/samples/`, because
  this phase commits no data and a new committed sample would also be a new input that
  every later measurement silently inherits.
  A test asserts that the same hand raises today, which is what makes it a fix.

### Betting reopens when short all-ins accumulate to a full raise
- Raising is reopened for a seat that has already acted when the current bet has advanced,
  since the last full bet or raise, by at least the minimum raise in force at that time.
  It is not reopened by a single short all-in that does not reach that bar, which is the
  rule today and stays the rule.
- The measurement is against the last full bet or raise and not against the immediately
  preceding bet level.
  That is the whole defect: two short all-ins of half a minimum raise each currently leave
  betting closed forever, and in a real room the second one reopens it.
- A worked example is pinned by test and spelled out in the report: a table where seat A
  raises to a full raise, seat B goes all-in short, seat C goes all-in short again, their
  two increments together reach the minimum raise, and seat A may now raise.
  The same example with seat C's all-in one chip smaller leaves seat A unable to raise, so
  the boundary is checked from both sides rather than in one direction.
- The rule composes across more than two short all-ins, and a full raise resets the level
  it is measured from.
  Both are asserted, because an accumulator that never resets is a different bug in the
  same place.
- A seat barred from raising may still call and may still fold, unchanged.
- No previously legal action becomes illegal.
  The change only ever adds `raise` back to a legal-action set, and a test asserts that
  over the enumeration the Phase 06 gate already runs.

### `street_bet` means one thing, and every producer says it
- `StrategyQuery.street_bet` is documented on the field as the street's current bet level,
  which is the reading the Phase 04, 05 and 06 code and tests already use, and hero's own
  contribution to the street is recoverable as `street_bet` minus `to_call`.
  The docstring is an acceptance criterion rather than a nicety: the field had two readings
  because nothing in the repo said which was meant.
- `StrategyQuery` rejects a query whose `street_bet` is less than its `to_call`, because
  the price to call cannot exceed the level being called and no correct producer can
  violate it.
  This is the mechanical guard that makes the wrong reading fail loudly rather than produce
  a plausible wrong answer.
- `scripts/generate_strategy_query_report.py` passes the street's current bet level.
  The report it writes changes as a result, and the phase audit packet states which
  refusals in it changed and why - specifically that the small blind in
  `phase02-heads-up-showdown` stops refusing with a blind-structure code for what is
  really a table-size miss.
- Every other producer of a `StrategyQuery` in the repo is checked against the documented
  meaning, and the audit packet lists them by file with the verdict for each.
  A single corrected caller alongside an unaudited set of others would leave the defect's
  actual claim - that producers disagree - unanswered.
  The prose list is the record and not the proof: each producer named is reached by a gate
  command that builds real queries, so the `street_bet` guard above runs against all of them
  on every gate and a disagreeing producer fails rather than resting on a reviewer's sweep.

### The all-in ceiling is the price hero can actually raise to
- `DecisionAuditRecord` computes the acting seat's all-in maximum as hero's own
  contribution to the street plus hero's remaining stack, that is
  `(street_bet - to_call) + stack`, rather than `street_bet + stack`.
- The old ceiling was too loose by exactly `to_call`, and a test pins the arithmetic with
  numbers a reviewer can check by hand: with a street bet of 20, a price to call of 20 and
  a stack of 100, a raise to 120 is now rejected and a raise to 100 is accepted.
- The tightened ceiling rejects nothing that any shipped strategy produces.
  The preflop chart already caps its raise at `street_bet + stack`, which under the
  corrected reading is its own all-in target, and the phase asserts over the committed
  decision audits that every existing record still validates.
- A raise exactly at the corrected all-in target is accepted, so the fix is a boundary
  correction and not an off-by-one in the other direction.

### The fallback's fail-closed branch never invests, and never refuses postflop
- `PostflopFallbackStrategy`'s fail-closed branch takes `fold` when `fold` is legal and
  refuses otherwise.
  It never returns `call`.
  A branch reached because the rules' chosen action was unavailable must not answer by
  investing in a hand that can lose, which is the one thing the whole module exists not
  to do.
- Both branches get a direct unit test built from a contract-valid `StrategyQuery` rather
  than from an engine state, because neither is reachable from the engine's own
  `legal_actions` and that is exactly why neither was covered.
  A legal-action set of `("call", "raise")` folds or refuses and does not call; a set of
  `("raise",)` refuses.
- Phase 06's claim that the fallback never refuses postflop is restated as what it always
  meant and what its enumeration actually proves: it never refuses from any legal-action
  set the engine can produce.
  The enumeration still finds zero postflop refusals and the gate still asserts that.
- The fallback's investment rule is untouched.
  It still calls exactly when no villain holding can beat hero on the turn or the river,
  and this phase adds no street, no threshold, and no price to that.

### The command registry describes the checks that exist
- The `check_solver_export_expectations` entry in `scripts/run_verify.py` describes what
  the command computes today and names no withdrawn check.
  The registry is the list a reader scans to learn what the gate covers, so an entry
  naming a check that does not exist is the same drift the Phase 10 contract's Scope
  section carried.
- Every command description in the registry is checked against what its script does, and
  the audit packet records the sweep and any further mismatch it found.
  Fixing one description that a reviewer happened to notice, without looking at the rest,
  would leave the class of defect open.

### Upstream contracts say what the code now does
- The Phase 03 acceptance criterion stating the reopening rule is amended to carry the
  accumulation clause, so no completed contract asserts the behaviour this phase
  deliberately changed.
- Every other completed contract whose acceptance criteria, forbidden shortcuts, or
  regression expectations are contradicted by one of these six fixes is amended in the
  same way and in `contract-update` mode, and the phase audit packet lists each amendment
  with the criterion it replaced.
- A contract that is merely made more true by a fix is left alone, and the audit packet
  says which ones were read and left alone, so "we checked" is a record rather than a
  claim.

### Evidence, reports, and gate
- Every one of the six defects is pinned by at least one test that fails against the
  behaviour in `main` at this phase's branch point, and the audit packet states, per
  defect, which test that is.
  A fix whose test passes before the fix is a fix nothing proved.
- Every one of the six is also pinned by a test in the other direction, asserting the
  corrected behaviour is not over-applied: a free fold that stays a fold, a short all-in
  that still does not reopen, a `street_bet` that is still allowed to equal `to_call`, an
  all-in raise that is still accepted at the target, a fail-closed fold that is not a
  refusal, and a registry description that still names its own script.
- The engine fidelity report shows a non-coding reviewer, for each of the six: what the
  behaviour was, what it is now, and one worked example in chips and cards where the two
  differ.
  The reopening example is spelled out seat by seat with its chip amounts, because it is
  the one fix whose correctness is a poker rule rather than an arithmetic identity.
- At least one number in the report is recomputable by hand from a committed file without
  reading code, and the audit packet says which number and how.
- The report states which existing committed numbers these fixes move without recomputing
  them, and names the phase that owns each re-measurement.
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- The judgment calls recorded in
  `reports/phase_audits/decisions/PHASE_11_ENGINE_FIDELITY_DECISIONS.md` carry a
  reversibility class before implementation begins, and the audit packet records the
  outcome of each one.
- Any deferred work is recorded in `backlog.yml`, and each of the six inherited entries is
  marked resolved with the commit that closed it or restated as what actually remains.

## Required reports
- `reports/active/latest_engine_fidelity_report.txt`

## Required command IDs
- `pytest_engine_fidelity`
- `generate_engine_fidelity_report`

## Human vetting packet requirements
- Plain-language summary of what changed, one paragraph per defect.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- The reopening worked example in chips, so the one change that is a poker rule can be
  checked against how a real room would rule it.
- The list of upstream contract amendments, each with the criterion it replaced.
- The list of committed numbers these fixes move, with the phase that owns each
  re-measurement.
- The recorded judgment calls and what each one changed.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not fix a defect by weakening the check that would have caught it. Loosening
  `StrategyQuery` validation, `DecisionAuditRecord` legality, chart import validation, or
  a chart refusal to make a test pass is the shortcut this phase is most exposed to,
  because five of the six fixes live inside a validator.
  The single exception is the `check`-and-`fold` invariant, which the criteria above
  remove by name and for a stated reason. Any other loosening is the shortcut, whatever
  the justification, and a validator that ends this phase accepting more than it did
  needs the criterion that says so.
- Do not make folding for free reachable by any shipped strategy. Legal is not the same as
  chosen, and a bot that folds a free river is worse than the one that could not.
- Do not implement the reopening rule by widening the minimum raise, by resetting the
  no-raise set on any all-in, or by any other rule that happens to pass the worked example.
  The rule is measured against the last full bet or raise, and a test asserts the case a
  looser rule would get wrong.
- Do not adjust a committed fixture, export, sample, or audit file so that a corrected
  check passes. If a committed file is genuinely wrong, that is a finding for its own
  task, not a repair inside this one.
- Do not re-measure any agreement rate, refusal inventory, or coverage number these fixes
  move. Naming them is this phase's job; recomputing them belongs to the phase that owns
  the measurement.
- Do not change the spot-key vocabulary, the query's table-state fields, or any preflop
  chart.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable, and every committed report that a
  gate command regenerates is regenerated rather than hand-edited.
- The Phase 06 postflop enumeration still finds zero refusals and still proves totality
  over the engine's own legal-action sets, now including the sets that carry a free fold.
- The Phase 03 strategy query report and the Phase 06 fallback report keep their existing
  paths; their contents change only where a corrected producer or a corrected ceiling
  makes them change, and the audit packet says where.
- The committed decision audit files still validate against `DecisionAuditRecord` under
  the tightened ceiling.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
