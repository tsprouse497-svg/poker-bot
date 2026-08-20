---
phase_id: "12"
title: "Spot Vocabulary V2"
depends_on:
  - "11"
required_gate_commands:
  - pytest_spot_vocabulary
  - generate_spot_vocabulary_report
required_reports:
  - reports/active/latest_spot_vocabulary_report.txt
required_phase_audit: reports/phase_audits/PHASE_12_SPOT_VOCABULARY.md
---

# Phase 12: Spot Vocabulary V2

## Scope
Two changes to what a spot key can say, and one measurement debt that comes due with them.
All three are `phase: "12"` entries in `backlog.yml`, and this contract is written against
them rather than against a fresh reading of the code.

`RAISE-SIZE-IN-SPOT-KEY`: a key records action names without sizes, so a 2.25bb open and a
4bb open are one spot. Every agreement rate in this repo is therefore computed across
prices the chart cannot tell apart, which is why the Phase 08 finding had to be qualified.

`SECOND-ORBIT-PREFLOP-SPOTS`: `solver_artifacts.schema.spot_key` rejects any sequence in
which a position acts twice, in as many words, so a four-bet and everything past it has no
key at all. `CORPUS-INEXPRESSIBLE-SPOTS` is the measurement of what that costs: 19 of
3,048 real decision points, filed as the single largest row of the real-hand refusal
inventory and the one row nobody could act on.

`PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT`: Phase 11 corrected the engine and the
strategy query that every published number in this repo was measured through, and ruled
that a fix phase does not grade its own fixes. This phase is the first to re-run those
measurements, so it owes a restatement of every number they touch, not only the ones the
new vocabulary moves.

Ruling 8 of `docs/V2_ROADMAP.md` is settled and is not reopened here. The solved tree
carries one opening price and every other price is answered from it. What that ruling asks
of this phase is written into the criteria below: the size lives in the key and the
abstraction lives in the lookup, so revisiting the ruling later is a bigger solve rather
than a re-derivation of every spot.

This phase commits no new solve and no new chart. It re-derives the committed artifact from
the export already in the tree, under new keys, carrying the same ranges.

Phase 12 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not change what the query carries about table state. Per-seat committed chips,
  straddles, antes, and asymmetric effective stacks are proposed phase 13.
- Do not derive a chart from the Phase 10 GTOpen export and do not retire the 36-spot
  chart. That is proposed phase 14, and it is the phase this vocabulary exists to serve.
- Do not give the postflop fallback a bet, a raise, or a new calling rule.

## Acceptance criteria

### The key carries the size of every raise in front of hero
- `spot_key` renders a raise entry with the raise-to amount in big blinds and a call or
  limp entry with no size, because a call has no price of its own to record.
- Big blinds rather than chips or multiples of the previous bet. Chips do not survive a
  change of blind level, and a multiple depends on what came before it, so the same spot
  would key two ways.
- Two sequences differing only in a raise size derive different keys, and a test pins both
  strings literally. The key is a string a human reads in a refusal inventory, so its
  rendering is an acceptance criterion and not an implementation detail.
- Sizes render in one fixed decimal form, so `2.5` and `2.50` cannot both exist as keys for
  one spot. A size the renderer cannot represent exactly is rejected rather than rounded
  into a neighbouring cell.
- `PreflopAction` carries the size and `schema.spot_key` stays the only place a key is
  derived. An artifact whose `spot_id` disagrees with its own re-derived key still fails to
  import. No test can prove a second derivation does not exist, so the audit packet records
  the sweep that looked for one, the way Phase 11 recorded its registry sweep.
- A v1 key carrying no sizes is rejected on import rather than accepted as a wildcard. A
  format admitting both is a format where a lookup can silently match the wrong cell.
- `StrategyQuery`'s preflop history carries the raise-to amount of each recorded raise,
  because a size-aware key cannot be derived from a history that does not hold one. Every
  producer of that history supplies it, and the audit packet lists them by file with the
  verdict for each. At this phase's branch point they are the corpus comparison, the
  simulator, and the preflop-strategy and postflop-fallback report generators, and the
  criterion is the sweep rather than that count.
- The committed sizing table keeps holding hero's own raise-to size and is re-keyed with
  the artifact. The key says what hero faces; the sizing table says what hero does. A test
  asserts every sizing key is a key the artifact declares.

### The key carries a position acting more than once
- `spot_key` accepts a sequence in which a position appears more than once, and the order
  rule generalises from a single pass over the preflop action order to repeated passes over
  the positions still live.
- A four-bet spot has a key, pinned by test from both sides. `LJ` opens, `BTN` three-bets,
  `LJ` four-bets and `BTN` is to act: that has a key. A sequence requiring a seat to act
  out of turn across an orbit boundary does not.
- Hero is still required to be the player to act, and the rule generalises from hero's
  first entry to hero's last: after hero's last recorded action there must be a later
  raise, because a call behind hero does not give hero another turn.
- A folded position stays absent from the sequence, and absence still means folded. The rule
  is about a position the action has already passed: one that a completed orbit went by
  without recording has folded, and a test asserts it cannot reappear in a later orbit,
  because a seat that folded is gone. A position still ahead of the action in the current
  orbit is absent for the ordinary reason that its turn has not come, and it may appear.
- No orbit cap. What bounds the vocabulary is whether the sequence is a legal preflop order,
  not a number of raises this phase happened to imagine.
- A sequence whose raise sizes cannot be paid at the stated stack depth is rejected. This is
  a check the key could not perform at all before it carried sizes, and it is what keeps an
  uncapped orbit count from admitting a five-bet to 300bb in a 100bb game.
- The count of expressible six-handed 100bb spots is recomputed by enumerating `spot_key`
  rather than quoted: the v1 count and the v2 count, each with and without limps. The
  roadmap's 1,691 and 848 are checked against that enumeration and corrected in the report
  if they are wrong, because both are extrapolations nobody has recently run.

### An unsolved price is answered from the solved one, and says so
- The observed price is normalised to the nearest solved price inside the lookup, before
  the key is built, and nowhere else. This is the criterion ruling 8 asks for by name: a key
  that simply stopped carrying size would make the artifact permanently single-price, and
  revisiting the ruling would mean re-deriving every spot rather than solving a bigger tree.
- The set of solved prices is derived from the keys the loaded artifacts declare, not from a
  constant in code. A second solved price must become answerable by committing a chart, with
  no edit to the normaliser.
- Normalisation applies to every raise in the sequence and not only to the open. This is a
  deliberate extension of ruling 8 rather than a reading of it, and Taylor ruled it on
  2026-08-20: three-bets have to be accommodated. Ruling 8 answers the price hero faces from
  an opener; a three-bet and a four-bet also arrive at sizes the tree does not hold, and
  exact matching there would refuse 72 of the 79 three-bet decisions the committed chart
  holds a cell for, collapsing the raised-pot half the same way it would have collapsed the
  opened-pot one.
- No decision in the committed sample refuses for a price the chart does not hold. A
  three-bet at any size reaches the cell the chart holds for that spot, and the phase states
  that count as zero rather than describing the mechanism that should produce it. This is the
  falsifiable form of the ruling above, and it is separate from coverage: a spot the chart
  holds no cell for at any price still refuses, which is `CHART-COVERAGE-EXPANSION` and
  proposed phase 14.
- There is no distance bound, and that is deliberate rather than overlooked. Ruling 8 is a
  single unbounded bucket, so the guard is measurement instead: every answer reports how
  far its price was moved.
- Every answer produced through a substituted price says so on the answer.
  `StrategyDecision` carries the same kind of ordered, structured detail `StrategyRefusal`
  already carries, naming the price asked and the price answered. A decision answered at
  its own price carries no such entry, so a substituted answer and an exact one stay
  distinguishable downstream.
- Normalising a price is not finding a nearest spot. The lookup still refuses when the
  normalised key is uncovered, and a test asserts that a 2.25bb open reaches the 2.5 cell
  while an uncovered table size, depth, or action sequence still refuses.

### The committed artifact re-derives with the same ranges under the new keys
- `scripts/convert_preflop_export.py --check` reproduces the committed artifact and its
  sizing table from `data/artifacts/preflop/sources/` at the new vocabulary. A chart nobody
  can regenerate is a chart nobody can diff against its origin.
- The re-derivation is a re-keying and not a re-solve. A bijection exists between the old
  spot keys and the new ones, and for every pair the per-hand per-action weights are equal.
  A test asserts both, and the report prints the mapping so a reviewer can check a row
  against the source by hand.
- The sizes entering a key come from the source export's own action labels at the upstream
  spot rather than from a constant. Facing an `LJ` open is 2.5 because `RFI_LJ` raises to
  2.5, and facing a three-bet carries the three-bettor's own label, so the report states the
  provenance of every size it put in a key.
- `audit_fields.weights_sha256` changes, because spot ids are inside the checksum. The audit
  packet records the old and the new checksum side by side with the statement that the
  weights themselves did not move, so a changed checksum is evidence rather than an alarm.

### The corpus inventory loses its catch-all row
- The real-hand refusal inventory no longer carries a `(no expressible spot)` row. All 19
  of those decision points name a four-bet-or-beyond spot key that a chart phase could
  fill.
- No corpus decision refuses as `lookup:unrepresentable-spot` any more, and a test asserts
  that count is zero over the committed sample. Those 19 arrive as `lookup:spot-not-covered`
  instead, which is a different miss: the vocabulary can now name the cell.
- The total refusal count is expected not to fall. This phase adds no chart coverage, so a
  drop is a finding to explain rather than a win to report, and the report says which of
  the two it saw.
- The report carries a price-substitution census: how many answered corpus decisions were
  answered at a price they were not asked at, split by the price faced, by how far it was
  moved, and by whether the substituted raise was the open or a later one. This is the
  cheapest available measurement of what ruling 8 costs in play rather than in theory,
  `docs/V2_RULING_MITIGATIONS.md` asks for it by name, and the open-against-later split is
  what tells a reader how much of the cost belongs to the ruling itself and how much to this
  phase's extension of it.

### Every number Phase 11 moved is restated, separately from the ones this phase moves
- Every number the Phase 07 and Phase 08 audit packets quote is restated, and each one is
  reported as unchanged, moved by Phase 11's engine and query fixes, or moved by this
  phase's vocabulary.
- The two causes are separated rather than merged into one re-run. A number that moved for
  both reasons and is reported once teaches nothing, and the whole point of Phase 11's
  decision 9 was to keep a moved number and a mistaken one out of the same commit.
- The separation is measured rather than asserted, and it is cheap: the committed reports at
  this phase's branch point already carry the corrected engine, so Phase 11's effect is the
  difference between those and the figures the older audit packets quote, and this phase's
  effect is the difference between those and the branch.
- A number that did not move is reported as not moved, and says which of the two changes it
  was checked against, so "we checked" is a record rather than a claim.
- No committed audit packet is edited. Phase 07's and Phase 08's packets are the record of
  what those phases found and believed, and rewriting them would destroy the only evidence
  that a number ever changed. The restatement lives in this phase's report and audit
  packet, which name the stale figures and where they sit.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code: what a spot key looked like
  before and after, for one raised spot and one four-bet spot; the old-to-new key mapping;
  the expressible-spot counts; the inventory row that disappeared; the substitution census;
  and the restated numbers with their cause.
- At least one number in the report is recomputable by hand from a committed file without
  reading code, and the audit packet says which number and how.
- Both new command IDs are declared here, registered in `COMMANDS` in
  `scripts/run_verify.py`, and pass through `scripts/run_verify.py`.
- Both new command IDs carry a mutation canary in `verification/mutations.yml`, authored
  before the implementation exists. Phases 08, 09 and 10 each wrote canaries for every
  command except the one the phase was adding, and each was caught by a gate that would
  otherwise have been decorative for exactly the behaviour the phase existed to add.
- The judgment calls in
  `reports/phase_audits/decisions/PHASE_12_SPOT_VOCABULARY_DECISIONS.md` carry a
  reversibility class before implementation begins, and the audit packet records the outcome
  of each. The key's rendering is `frozen-into-data`: it goes into the committed artifact
  that proposed phase 14 is then measured against.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`, and each of the four inherited entries is
  marked resolved with the commit that closed it or restated as what actually remains.

## Required reports
- `reports/active/latest_spot_vocabulary_report.txt`

## Required command IDs
- `pytest_spot_vocabulary`
- `generate_spot_vocabulary_report`

## Human vetting packet requirements
- Plain-language summary of what changed, one paragraph per backlog entry closed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- One spot key before and after, and one four-bet key that could not be written at all
  before, so the change is legible without reading the schema.
- The old-to-new key mapping and both checksums, with the statement that the ranges did not
  move.
- The price-substitution census, stated as what ruling 8 costs in this sample.
- The restated Phase 07 and Phase 08 numbers, each labelled with its cause.
- The recorded judgment calls and what each one changed.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not reopen ruling 8 and do not add a second solved opening price. One price is a
  ruled and priced cost, not a defect to route around.
- Do not implement the price abstraction by dropping the size from the key. This is the
  shortcut this phase is most exposed to, because it passes every test about a lookup
  hitting the right cell while making the artifact permanently single-price, which is the
  one outcome the ruling asked this phase to avoid.
- Do not add nearest-spot, nearest-depth, nearest-position, or nearest-hand-class matching.
  The price normaliser is the single named abstraction in this phase and it exists because a
  human ruled it; anything else is the heuristic guessing the boundary forbids permanently.
- Do not weaken import validation, lookup refusal, `StrategyQuery` validation, or decision
  audit legality to admit a re-keyed file. If a committed file is genuinely wrong, that is a
  finding for its own task.
- Do not adjust a committed fixture, export, sample, or audit file so that a re-keyed lookup
  hits.
- Do not edit the Phase 07 or Phase 08 audit packets, or any other committed audit packet,
  to correct a number this phase re-measures.
- Do not widen the query's table-state fields, derive a chart from the Phase 10 export, or
  retire the 36-spot chart.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable, and every committed report a gate
  command regenerates is regenerated rather than hand-edited.
- The corpus comparison keeps its 499 compared hands and its 3,048 preflop decision points.
  A changed denominator means the replay changed, which this phase does not touch, so it is
  a defect rather than a result.
- The committed decision audits still validate against `DecisionAuditRecord`. If the query
  payload gains a field, the decision-audit schema version moves with it and the audit
  packet says why, because a payload that changed shape under an unchanged version number is
  the defect `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS` already records.
- Every existing refusal code keeps its meaning. `lookup:unrepresentable-spot` stays in the
  vocabulary and stays reachable by a genuinely illegal sequence, because a code that
  disappears takes the distinction it drew with it.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
</content>
</invoke>
