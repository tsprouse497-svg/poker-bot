---
phase_id: "13"
title: "Table-State Fidelity"
depends_on:
  - "11"
required_gate_commands:
  - pytest_table_state
  - generate_table_state_report
required_reports:
  - reports/active/latest_table_state_report.txt
required_phase_audit: reports/phase_audits/PHASE_13_TABLE_STATE.md
---

# Phase 13: Table-State Fidelity

## Scope
Five changes to what `StrategyQuery` carries about the table, and nothing to what a chart
can express. All five are `phase: "13"` entries in `backlog.yml`, and this contract is
written against them.

- `PER-SEAT-CONTRIBUTIONS-IN-QUERY`: the query gives current stacks, one pot total, and the
  price to call, but not what each seat has put in. Nobody's own contribution is recoverable,
  hero's included. That single omission is why the other four exist.
- `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`: Taylor ruled on 2026-08-20 that `to_call` is what
  hero would actually pay, capped at hero's remaining stack. Two producers cap and the rest do
  not, so one table state reaches the chart as two different depths, and the guard that makes
  the all-in ceiling airtight does not exist yet.
- `ASYMMETRIC-EFFECTIVE-STACKS`: a seat holding less than hero is invisible, because a short
  villain and a villain who has already invested look identical from a query with no
  contributions. The chart would answer such a table as if it were flat.
- `BLIND-STRUCTURE-VARIANTS`: the query cannot see a straddle or an ante, so
  `PreflopChartStrategy` detects both by an arithmetic bound on the pot that a straddled pot
  with several callers slips through.
- `STRATEGY-QUERY-STREET-BET-NAME`: `street_bet` on the query means the street's bet level,
  while `street_bet` on the engine's own `PlayerState` means that seat's own contribution to
  it. One name, two meanings, in a phase that puts the second on the query beside the first.

This phase commits no artifact, no chart, and no new sample. It changes the runtime query
and what the strategy can see through it. The chart's vocabulary is untouched: a spot key
still carries one table-wide depth and declares no blind structure, so what this phase buys
is that a table the chart cannot describe is now seen and refused rather than answered as
something else. Making those spots answerable is a chart phase and needs a solve.

Where the evidence comes from, settled before any criterion below is read. All 499 committed
corpus hands are six seats at 10,000 chips, zero antes, and blinds of exactly 50 and 100; the
parser rejects anything else, the engine posts only two blinds, and the simulator gives every
seat one starting stack. The corpus therefore holds no asymmetric, straddled or anted table
and every table-shape count against it is zero before anything is measured, which is filed as
`CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` and is not this phase's to fix. So constructed fixtures
and the strategy-report probes carry the discovery and the corpus carries a zero-delta
regression proof, and a criterion promising a corpus discovery here would be promising a
number that cannot exist.

Phase 13 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not change the spot key, the artifact schema, or any committed artifact. Per-seat depth
  in a key, a declared blind structure, and a call entry that records a short all-in are all
  format changes; they are named in the criteria below, measured, and filed forward.
- Do not derive a chart, widen chart coverage, or retire the 36-spot chart.
- Do not add nearest-depth, nearest-spot, or any other approximate matching.
- Do not give the postflop fallback a bet, a raise, or a new calling rule.

## Acceptance criteria

### The query carries what every seat has put in
- `StrategyQuery` carries, per seat, the chips that seat has put in on the current street and
  the chips it has put in over the hand so far. Both, because the street figure is what a bet
  level is measured against and the hand figure is what the pot is made of, and preflop they
  coincide only until this phase's own postflop callers use them.
- The two names match the engine's own, which already tracks exactly these two quantities on
  `PlayerState`. One vocabulary across the engine and the query, or the next reader repeats
  `STREET-BET-MEANING-AMBIGUOUS` in a new place.
- Every seat in `stacks` has an entry, including a folded seat that has already invested, and
  a query whose contribution seats disagree with its stack seats is rejected. A folded seat's
  chips are in the pot and dropping them is how a pot stops reconciling.
- `pot` is validated against the contributions rather than trusted, and a query whose stated
  pot is not the sum of what the seats put in is rejected. Both live producers already build
  the pot as that sum, so the check is a tautology there and the phase says so rather than
  claiming an oracle it does not have; it bites at the report producers that supply an
  independent pot, one of which attributes 100 chips to no seat, and at every producer written
  after this phase. A pot holding chips no seat contributed is rejected rather than
  mis-derived, which is a hard stop for later ingestion of raked or dead-blind hands.
- Hero's own contribution is read from the new field and never re-derived by subtraction. The
  subtraction identity `street_bet` minus `to_call` was wrong under the capped ruling and the
  repo has now written it down twice; a field nobody has to reconstruct is what stops a third.
- Every producer supplies the contributions from what the engine or the replayed hand actually
  recorded, never from a reconstruction. The audit packet lists every producer by file with a
  verdict for each, the way Phase 11 recorded its registry sweep.

### `to_call` is the price hero can actually pay, at every producer
- `to_call` is capped at hero's remaining stack at every producer, which is Taylor's ruling of
  2026-08-20 applied rather than restated. The criterion is the sweep, not a count: the backlog
  entry says three producers are uncapped, and stage 1 measured nine construction sites across
  six files of which two cap. Two the entry does not name are load-bearing and are named here
  rather than discovered at stage 6. The preflop strategy report builds its straddle probe by
  overriding the bet level alone and its ante probe by overriding the pot alone, so under this
  phase's rules the first stops refusing and the second cannot be built at all; both are
  rebuilt to carry per-seat forced chips so that report keeps the two refusals it exists to
  show. The postflop fallback enumeration attributes 100 chips to no seat, so the phase decides
  where that dead money sits rather than relaxing the reconciliation around it.
- `StrategyQuery` rejects a query that offers `raise` or `bet` while `to_call` equals hero's
  stack. A hero who is all-in for the call cannot raise, the engine already never offers it,
  and today such a query validates fine. This is the only route by which the all-in ceiling
  accepts a raise hero cannot make, and it is the guard the ruling was found to be missing.
- The two all-in ceilings become one. `PreflopChartStrategy` caps its raise at the street's bet
  level plus hero's stack while `DecisionAuditRecord` caps at hero's contribution plus hero's
  stack, differing by exactly `to_call`. Both are now expressed from hero's recorded
  contribution, and a test pins that they agree on a hero who has already invested this street.
- Phase 06's short hero is restated. `0 < stack < to_call` is unsatisfiable once `to_call` is
  capped, and the situation survives as `to_call == stack`. The enumeration keeps covering
  that hero and its contract says so.

### An asymmetric table is seen, and refused for what it is
- Each seat's starting stack is recomputed exactly as what it holds plus what it has put in,
  so a short villain and an invested villain stop being the same picture.
- The flat-table test runs in both directions and over the seats still live in the hand only.
  Today only a seat deeper than hero refuses; a seat shallower than hero is invisible and the
  chart answers at hero's depth. Both now refuse, and a shallower seat gets a refusal code of
  its own, because "somebody is short" and "somebody is deep" are different tables and a
  single code would merge them in the inventory.
- A seat that has already folded does not make the table ragged, and a test pins that. Its chips
  stay in the pot and in the reconciliation, but effective stack is pairwise and against seats
  that can still act, so a folded 40bb seat cannot change a chip of hero's decision. Refusing on
  it is a regression this phase would have introduced.
- The refusal names the seat and the depth it holds in its detail, so the refusal inventory can
  say which table shape the chart is missing rather than only that one is.
- The order the depth checks fire in is ruled and pinned by test, since a ragged hero is
  tested before any villain today. Without an order the codes are unpredictable in exactly the
  low-stakes games where no stack is a whole number of big blinds, and the inventory stops
  being able to say which table shape is missing.
- A hero short on the street at a flat-start table still reaches a decision wherever the chart
  holds a cell. A hero who bought in short is a different thing: a live seat is then deeper
  than hero by construction, so the table is not flat and it refuses. The two are stated apart
  because they read as one sentence and are not.
- On the committed corpus every count above is expected to be zero, and the phase reports those
  zeros as a checked regression proof rather than omitting them: a corpus number that moves is
  a defect, not a discovery. The discovery evidence is constructed fixtures, and the report
  states for each what the chart derived before and derives now. One committed fixture is
  expected to move and is the phase's only live evidence: the three-handed side-pot hand at 50,
  100 and 200 chips changes refusal code in the postflop fallback report.

### A straddle and an ante are detected exactly, not bounded
- Forced money is found by reconstructing what each seat should hold from the two declared
  blinds and its own recorded actions, and comparing that to what it does hold. A seat holding
  more than the reconstruction predicts is carrying chips it never chose to put in. That is
  exact where the pot bound it replaces is generous by construction, and it catches an ante
  always, including on a seat that has since folded.
- Reconstruction alone is not enough, and the contract says so because a stage 4 author who
  believes it is will freeze a fixture that proves nothing. A straddler who has already called
  to the level holds exactly what an ordinary caller holds, so the straddle is absorbed and no
  comparison of contributions can see it. Two further signals are therefore required. An
  unraised pot whose bet level is not the big blind is straddled, which is the whole of the
  limped case. And after a raise, the minimum raise target the query carries disagrees with the
  one the declared blinds and the recorded raise-to amounts predict, by exactly the straddle:
  over a 200 straddle a raise to 600 leaves a minimum of 1000 where the same price in an
  unstraddled 50/100 game leaves 1100. The phase pins that arithmetic and states the residual,
  if any, that all three signals together still miss.
- The two are told apart rather than merged. A straddle raises the bet level a voluntary action
  is measured against; an ante does not, and they change the correct ranges differently, so
  each gets its own refusal code and detail instead of one "unrepresentable pot".
- The generous pot bound is deleted, but only after a test shows the replacement refuses every
  pot the bound refuses. A bound and an exact test that disagree is a repo with two answers;
  a bound deleted before its replacement covers it is a coverage loss dressed as a cleanup.
- The case the bound admits today is pinned by test as detected: 50/100 with a 200 straddle,
  a raise to 600, the straddler and the big blind calling, the small blind folding. Its pot of
  1,850 sits under the bound's 1,950 and slips through, its contributions are indistinguishable
  from an unstraddled pot at the same price, and the minimum raise target is what gives it
  away. It is the case named in `PER-SEAT-CONTRIBUTIONS-IN-QUERY` and it is common in the home
  games this bot is pointed at.
- What the chart can express is unchanged, so both still refuse. The artifact declares no
  blind structure and this phase adds no field to it; the deliverable is that a straddled pot
  is now refused because it was recognised, rather than answered because it was not. The
  format half of `BLIND-STRUCTURE-VARIANTS` is restated as what remains and filed forward.

### One name for the street's bet level
- `StrategyQuery.street_bet` is renamed to the name the engine already uses for the same
  quantity, so the repo holds one vocabulary rather than two readings of one word. Phase 11
  documented the meaning and left the name; this phase is the one that puts the other reading
  on the query beside it, which is what makes the collision unaffordable.
- The serialized decision-audit key changes with the field, so
  `DECISION_AUDIT_SCHEMA_VERSION` moves and the audit packet says why. Two payload shapes
  under one version number is `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS`, which
  this repo has already recorded once.
- No completed contract is left naming a field that no longer exists. Phase 03 is amended at
  stage 1 in the two-line form `AGENTS.md` requires. Phase 11 names the field in three criteria
  and separately asserts that the preflop chart's raise cap is its own all-in target, which the
  ceiling criterion above makes false, and it cannot take an amendment at all because it sits
  at exactly the 300-line cap. `AGENTS.md` rules that case a rewrite as its own
  `contract-update` task and forbids raising the cap, so that task is
  `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP`, the ExecPlan names it, and this phase does not
  tag until it has run.
- No producer, consumer, report, or committed audit is left on the old name, and no alias is
  kept. An alias is how a rename leaves two vocabularies instead of ending one.

### The tests earlier phases already froze are migrated with it
- The frozen tests of completed phases are migrated in the same task that changes the shape
  they assert against, authored at stage 4 with this phase's own tests. Phase 11 and Phase 12
  both shipped a stage 6 that went red on dozens of frozen tests for this reason and each paid
  a separate repair task; a third is a process failure rather than bad luck.
- No frozen assertion is weakened to fit. A test that asserted the old field name asserts the
  new one; one that asserted behaviour now wrong is rewritten to the claim it was making, and
  the audit packet says which and why. That includes the frozen test asserting phrases from
  `StrategyQuery`'s class docstring, which is rewritten to the fields the query now has rather
  than contorted to satisfy its test.

### The two findings Phase 12 handed to this phase are answered, not inherited
- The spot key admits a re-raise no legal preflop action produces, because nothing checks the
  minimum raise and the key cannot tell an under-raise from a short all-in. This phase says
  whether the query's new fields close it and, where they do not, what a key would have to
  carry, with the count of corpus decisions affected. A finding handed on with a number is a
  work list; handed on without one it is the same sentence a third time.
- A call entry carries no record of being all-in for less, so a short all-in call and a full
  call are one spot. Same treatment: measured, then closed here or restated as a key change
  with what it costs to leave open.
- `spot_key`'s claim to validate a "legal preflop order" is corrected to what the check behind
  it does. A docstring stronger than its check is how the next reader stops looking. The same
  overclaim sits in a Phase 12 acceptance criterion; correcting only the docstring leaves the
  contract asserting it, so the phase either amends Phase 12 or files the mismatch by id.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code: one table state before and
  after with the pot reconciled seat by seat, the depth the chart derived against the depth
  that is true, the straddled pot that used to slip through the bound, and the corpus counts
  for every claim above. At least one number in it is recomputable by hand from a committed
  file, and the audit packet says which and how.
- Both new command IDs are declared here, registered in `COMMANDS` in
  `scripts/run_verify.py`, and pass through `scripts/run_verify.py`.
- Both new command IDs carry a mutation canary in `verification/mutations.yml`, authored
  before the implementation exists. At least one canary must prove the pot reconciliation
  bites, because a validator nobody can break is a validator nobody has tested.
- The judgment calls in `reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`
  carry a reversibility class before implementation begins and the packet records each
  outcome. `frozen-into-data` reaches a fixture as well as an artifact, so a behaviour default
  this contract requires a frozen test to pin carries the class even though the phase commits
  no artifact.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`, and each of the five entries this contract
  is written against is marked `done` with the evidence that closed it, or restated as what
  actually remains. Two consecutive phases have tagged and merged with their own items still
  `deferred`, which is `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE`.

## Required reports
- `reports/active/latest_table_state_report.txt`

## Required command IDs
- `pytest_table_state`
- `generate_table_state_report`

## Human vetting packet requirements
- Plain-language summary of what changed, one paragraph per backlog entry closed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- One table state written out seat by seat, before and after, so the pot reconciliation is
  legible without reading the validator.
- The corpus counts, expected to be zero and reported as a checked regression proof, beside
  the constructed fixtures that carry the discovery, each with the depth or blind structure
  the chart derived before and after.
- The producer sweep, by file, with the verdict for each.
- The recorded judgment calls and what each one changed.
- Known limitations and deferred items, including what a spot key would have to carry for the
  two findings Phase 12 handed on.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not make the contributions optional, defaulted, or reconstructable. A field a producer may
  omit is a field the depth derivation has to guess behind, relocating this phase's defect.
- Do not keep the pot as an independently supplied number that the contributions merely agree
  with when convenient. If a producer cannot make its pot reconcile, that is a defect in the
  producer and a finding, not a validation to relax.
- Do not reintroduce the subtraction identity anywhere, including in a comment, a docstring, or
  a report. It is wrong under the capped ruling and it has already been copied once.
- Do not answer an asymmetric, straddled, or anted spot by choosing a depth, rounding a stack,
  ignoring the forced money, or reaching for a neighbouring cell. Each is the heuristic
  guessing the V1 boundary forbids permanently, and refusing exactly is the deliverable.
- Do not adjust a committed fixture, sample, artifact, or audit file so that a stricter query
  validates, and do not weaken `StrategyQuery` validation, chart refusal, or decision-audit
  legality to admit a producer this phase did not finish updating.
- Do not change the spot key, the artifact schema, or any committed artifact.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable, and every committed report a gate
  command regenerates is regenerated rather than hand-edited.
- The corpus comparison keeps its 499 compared hands and its 3,048 preflop decision points. A
  changed denominator means the replay changed, which this phase does not touch, so it is a
  defect rather than a result.
- Agreement rates are expected not to move, because the corpus is one flat structure and no
  decision in it stops being answered. Any that does move is reported with its cause, and no
  committed audit packet is edited to match.
- The committed decision audits still validate, at the moved schema version, and the report
  regenerates them rather than the phase hand-editing a payload.
- Every existing refusal code stays reachable and the new ones are additions, because a code
  that absorbs another takes the distinction it drew with it. Generated docs stay current.
- File-size and scope checks continue to pass.
