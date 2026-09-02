---
phase_id: "14"
title: "Chart Cutover"
depends_on:
  - "10"
  - "12"
  - "13"
required_gate_commands:
  - pytest_derived_chart
  - generate_derived_chart_report
required_reports:
  - reports/active/latest_derived_chart_report.txt
required_phase_audit: reports/phase_audits/PHASE_14_CHART_CUTOVER.md
---

# Phase 14: Chart Cutover

## Scope
The bot plays from `data/artifacts/preflop/six_max_nl25_100bb.json`, 36 spots derived from a GTO Wizard export
of a raked game. Phase 10 captured a GTOpen solve of the game this bot is trained for - six-handed, 100bb,
rake-free. This phase derives the artifact from that solve and deletes the old one, committing the ranges
every later phase is measured against; hence `auto_advance: false` in `verification/loop_policy.yml`. The
corpus verdict it used to close with is **phase 17**, split off 2026-08-31.

**Six spots are committed** - `t6/d100/SB/rfi` and the big blind's defence against each of the five openers.
**Decision 14** re-solves with `add_allin: false` at `0.00016`, giving **33,969 action nodes**. **Decision 1,
superseded 2026-08-25**, makes a node eligible when at most one opponent has voluntarily invested beyond the
blinds **and** at most two players are still live - both clauses, the rule having to be stated over
*terminals* (`SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS`); **it selects 51**. **Decision
20**, ruled 2026-08-31 and extended twice on 2026-09-01, solves with `realization: calibrated` and **withholds
45 of those 51** - every spot facing a three-bet, a four-bet or a five-bet jam - the fit behind `calibrated`
having no four-bet-pot cell and no other setting being better.

**What six spots buys and costs, both measured.** The six carry **81.1 percent** of the arrival the phase's
21-spot set carried and **78.9 percent** of everything the predicate selected, small-blind opening and
big-blind defence being the commonest decisions at six-max. Against the retired chart the cutover **gains
nothing**: of its 36 keys, 6 carry over onto exactly the committed six, 15 pass the predicate and are then
withheld, 14 the predicate never selects, and `t6/d100/BB/SB:call` is a limped pot a `limp: false` solve has
no node for. Coverage falls by a factor of six and the refusal rate rises rather than falls; what the phase
buys at the six is that they are rake-free, re-solved and priced inside the fit's support.

## Non-goals
- Do not add PokerNow automation, browser or platform observation, runtime solver calls, LLM-backed poker
  decisions, or training UI surfaces - the standing V1 boundaries. Do not re-solve at a second opening price,
  with limps, at another depth or table size; all are phase-10-shaped work. The one re-solve here changes
  `add_allin` and the target and **nothing else**.
- **Do not fix the multiway pricing here, do not repair a pricing defect by changing `realization`, and do not
  commit a mispriced spot with the defect recorded as a caveat.** The multiway fix changes GTOpen's
  `KIND_POT_SHARE` terminals and is out of scope by Taylor's ruling of 2026-08-31. One field prices the whole
  tree, so fixing one pot type breaks another; a caveat does not reach the human at the table. Do not change
  the spot key grammar (`RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`), and do not rederive
  `data/artifacts/preflop/expectations/six_max_nl25_100bb.json`, the only number here this repo did not
  produce and so the one thing catching a uniformly wrong range.
- Do not widen the predicate, or lift a withholding, to recover the coverage the scope says was lost: a spot
  the source should never have offered is not coverage, nor is one it cannot price. Six is the answer, not a
  shortfall to be topped up. And do not render the corpus verdict; that is phase 17's.

## Acceptance criteria

### What the re-solve owes
- `config_posted` is byte-identical to the previous card **apart from `add_allin`**, the solve block differs
  only in its target, and `model` is derived from `RULED_CONFIG` rather than typed - a card naming one model
  beside a `config_posted` naming another is the one claim about this export no gate command reads. A test
  asserts the config equals `RULED_CONFIG` field for field and then names the forbidden fields individually,
  equality against a constant passing as happily if the constant widens. The two-process determinism proof is
  re-run and written onto the card by the script rather than typed in, per `--determinism-only`: a second full
  solve in a fresh process against a restarted server, diffed node by node, at **0 divergence and 0 shape
  differences**. It is a separate obligation from the re-resolve walk, which re-derives every node from its
  recorded path and must report **0** mismatches over all 33,969. Neither may still read `PENDING`.
- The card carries exactly one solve record; the two checksums and the `size` block are refreshed; and both
  gated orderings are re-asserted on the new solve rather than carried over. `data/artifacts` stays inside the
  20 MiB cap; exceeding it is a halt and a decision, never a raise. **The target is `0.00016` at a
  2,000-iteration cap**, superseding phase 10's decision 3 here only. The ruled build first meets it at
  **iteration 1,900 of 2,000** at an achieved gap of **0.00015590818**, so the cap nearly binds and a lower
  target would make `achieved < target` false.

### Selecting what gets committed
- The predicate selects a node when at most one opponent voluntarily invested **and** at most two players are
  still live; it selects **51**, and the predicate is the ruling rather than the number. Both clauses live in
  the converter, never a node list, and each is tested alone so neither is idle: 65 nodes and 4,865.
  **Decision 20 withholds 45 of the 51 in three families, leaving 6.** The fit behind `calibrated` has cells
  for single-raised and three-bet pots and none for a four-bet pot, so anything priced on a four-bet-pot
  terminal is outside its support and is refused as multiway pots are: never answered from a neighbour.
- **Each family carries its own reason, because one code loses which fix brings a family back.** Hero facing a
  four-bet is the mispriced node itself; hero facing a three-bet **weighs** its four-bet branch on that node,
  inheriting a value; hero facing a five-bet jam **inherits a range** from it. The first two return when the
  fit gains a four-bet-pot cell, the third only once its parent is trusted too. Two families share a shape by
  seat and all three are one size, so only the code separates them, and a census folding any two codes
  together still balances and must be refused. Each family is an exact raise count - two, three, four faced -
  never a node list; the committed six face nought raises or one, the other counts asserted at zero. Every
  node lands in exactly one of committed, excluded or inexpressible, summing to the count the card publishes,
  with reasons drawn from a closed vocabulary the tests enumerate - `namespace:reason`, disjoint from the
  runtime miss codes - so a converter failure cannot be filed as a property of the grammar; an unknown action
  kind raises.
- The census has **six buckets summing to 33,969**: **6** committed, **15**
  `derivation:weighs-a-mispriced-four-bet-branch`, **15** `derivation:source-misprices-four-bet-pot`, **15**
  `derivation:inherits-a-mispriced-four-bet-node`, **29,104** `derivation:source-misprices-multiway`,
  **4,814** `derivation:outside-selection-rule`. The inexpressible bucket is **empty** and the report
  publishes that as a result, not as an omission. A node the rule excludes is a lookup miss at runtime,
  refused with a code naming the spot, with no neighbouring cell and no price substitution consulted.
- The artifact carries per cell the reach arriving at it and **per spot the probability of arriving at the
  spot at all**, reach being unable to separate a committed cell never computed from one that was. Reach is
  the plain mean over the 169 classes, and **no reach floor selects cells** - decision 1's retired two-percent
  floor admits every committed node. Arrival is parts per billion, one left-to-right product from the root
  rounded once at the end, summing to **983,107,279**; one above one, or claimed for an undeclared spot, is
  refused at construction. **No committed row is the solver's untouched initialisation.** A uniform split
  across a three-action menu is what an untrained cell looks like; the count is **0** under both the exact and
  the tolerant reading, and the readings must agree as sets (`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`).

### The derived artifact
- The artifact is derived from `data/artifacts/preflop/exports/` by a committed script, reproducible byte for
  byte, with a `--check` mode that fails the gate when it is not. Reproducible is not the same as right, so
  that test carries the committed spot count with it, and `--check` writes nothing. The retired
  `six_max_nl25_100bb.json` is **deleted** and a test asserts it absent from the artifact directory, its glob,
  and `sizings/`. No collision is not retirement: only **5 of its 36 keys** exist verbatim in the new artifact
  and a sixth matches only once phase 12's ruling 8 normalises the price, so both would load clean and the bot
  would answer 30 keys with raked ranges. The report prints the cutover ledger and it must balance: **6**
  carried over, **29** refused - 15 withheld, 14 outside the predicate - and **1**, the limped
  `t6/d100/BB/SB:call`, with no node. **0 spots are gained**, derived from the two key sets rather than typed.
- The sizing table is rederived from the export in the same run as the artifact; the expectations file is not,
  and the report prints the chart against it gated by nothing, per decision 6. **The table holds every raise
  size a spot offers with the weight hero gives each**, the key stating what hero faces rather than what hero
  does (`CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT`). A test proves the converter reads raise sizes
  from the export's action labels rather than constants: over a synthetic export with perturbed labels it
  produces keys carrying the perturbed sizes. **All 6 committed spots price something and the table's keys are
  the committed six exactly.** A test enumerates the menus - **5 fold/call/raise and 1 fold/raise** - a
  converter that dropped an action passing every other check. The prices offered are exactly **`[2.5, 7.5]`**:
  `22.5` was only ever quoted by the withheld three-bet-facing spots, and `100.0` is not a price hero can
  name. A spot offering no raise must carry no key at all and the strategy must refuse rather than invent a
  size; that invariant is two-directional and its second half is **vacuous** here (see below).
- **The artifact declares the blind structure it was solved at**, read off the posted config, and refuses an
  impossible one at construction - a blind at or below zero, a small blind at or above the big blind, a
  negative ante - a zero ante staying valid.

### What the ranges must not have become
- No spot with an empty `action_sequence` carries a call weight, enforced by the artifact schema rather than
  measured over one file. That is what `CHART-HERO-MUST-NEVER-LIMP` asks for: the export enforces it by
  construction, which is data rather than a rule, and phase 14 owns the schema. The retired chart limps 13.73
  percent from the small blind across 103 classes. **Three relations are measured, not two.** A higher pair
  played at least as often as the pair one rank below; a suited hand at least as often as its offsuit twin;
  and, within a row of the 13x13 grid, a higher kicker at least as often as the kicker one rank below, suited
  and offsuit apart and adjacent kickers only - **132 comparisons** over a full grid. All three are measured
  **per cell** on play-not-fold at decision 10's **one-point tolerance**, and none is gated as an order, the
  solver's split among near-indifferent hands being its considered answer. Gated is that it was taken over
  every cell; counts and worst cases publish (`UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE`).
- **The range gate is two counterfactual arms, both strict, a tie refusing on each.** The suit arm transposes
  each suited hand with its offsuit twin (`transpose_hand_index`) and scores **spots**
  (`spots_violating_twins`); the rank arm reverses every rank (`reverse_hand_ranks` - total, its own inverse,
  pairs to pairs and suited to suited) and scores **cells** on the row ladder. On each, the solved hand index
  must flag strictly fewer than the counterfactual one. Each arm keeps its own validator and parameter name,
  this repo having lost a day to two "transposed" counterfactuals taken for one another.
- **The rank arm exists because the other relations are provably blind to a rank permutation**, measured
  rather than argued: the twins relation is invariant under one, and every pocket pair is played 100 percent
  at all six spots, so the pair ladder reads nothing. A rank-reversed chart scores identically to the right
  one on the suit arm; a test shows the suit arm accepting it and the rank arm refusing it. The arms score
  different units for a measured reason: over six spots a spot count on the rank arm would read 6 against 6
  and saturate the way the group ladders did.
- **Both arms gate on every partition, and there are five**: the whole set, one per seat hero sits in, one per
  number of raises faced. Over six spots those five labels cover three distinct sets, and the duplicates are
  kept, pruning by hand being a choice of splits made after seeing them. Fixing a count fixes a partition, so
  what is asserted is the direction. **The gate is re-measured over the committed 6 before it is frozen** and
  the phase halts rather than ship a gate it has not seen pass. Its definition - weighting, reach floor,
  tolerance, family exclusions, per spot or per chart - is pinned as data first
  (`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`).
- **The group-order ladders gate nothing and are published for a human**, ruled 2026-08-26 and re-affirmed
  2026-09-01. The measurement is still taken on all five partitions and printed, but not asserted: the family
  returned a different verdict on every committed set - failing over the uncut 51, passing over 36, tying over
  21, separating nothing over 6 - so it measures set composition rather than the hand index. Its saturation
  over six spots is stated, and the report says in words that it gates nothing. **Neither arm passing is
  evidence the ranges are sound.** The gate is an extraction check: it catches a transposed or a permuted hand
  index and cannot see uniform over-folding, a mis-assigned actor, or a cross-family inversion
  (`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR`, named in the packet). A failure
  is a halt and a decision for Taylor, never a tolerance re-derived until it admits the artifact it judges.
- The orderings the export was gated on hold: later position opens wider among the four non-blind positions,
  and the big blind defends more against whoever opens wider. The first is checked against the **export**, the
  artifact holding no non-blind opening range; the second over the artifact, following the measured opening
  frequencies rather than a fixed seat order. **An ordering is not a level, and only the level catches a
  broken realization model**: both orderings hold under `static`, which defends the big blind 100.00 percent,
  so the defence level per opener is measured, printed against the expectations file, and read by a human
  before the artifact is committed (`STATIC-REALIZATION-UNMEASURED-IN-SINGLE-RAISED-POTS`).
- **The big blind over-folds and this phase records it rather than hides it** - decision 24, restated on
  2026-09-01 once its three example spots were found to be spots the chart refuses. Five of the six committed
  spots are big-blind defence, so the continue and flat frequency at each is printed beside the opening range
  it answers, and exactly one committed spot flats nothing, the small blind's open having no call.
  `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT` is re-measured here rather than assumed to have moved. The exit
  is phase 16.
- The source card states the limitations of what is committed, in poker terms with their measurements:
  `REALIZATION-MODEL-UNDERPRICES-POSITION` per decision 3, retaken on the committed set, and that under
  `calibrated` a rake-free solve is **not rake-free at its heads-up flop terminals**, the fit being measured
  net-of-rake over the gross pot (`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`). The multiway and the
  three four-bet defects are stated with their node counts and their fixes.

### Criteria this committed set leaves vacuous
A criterion here has **no instance** over the committed six. It is retained because a later solve, or a lifted
withholding, reactivates it, and each must be **labelled vacuous** wherever it is reported and never counted
as a check that passed: a phase that quietly drops a criterion whose subject vanished has lowered its own bar
with nobody ruling that it may.
- **The two-price sizing schema** - 0 of the 6 offer two prices; decision 6 records why it is kept, and the
  two-price case is proved against a synthetic export. **The second half of the sizing invariant** - all 6
  price something, the fifteen call-and-fold jam spots that exercised it having been withheld. **The
  jam-and-named-raise collapse rule** - with `add_allin: false` no node offers both. **Per-cell reach as a
  discriminator between a trained cell and a barely-visited one.** All six are spots hero reaches without
  having acted, so all 1,014 cells sit at full reach, 10,000 basis points, and the field separates nothing -
  including a transposed hand index, which the gate above now catches alone. It is still printed; arrival
  separates.
- **The parts-per-billion grain and the zero-arrival case** - the rarest committed spot arrives at 1,280 basis
  points, and none arrives at zero. **"Later position opens wider" over the artifact**, which holds no
  non-blind opening range. **The pair ladder as a signal** - every pocket pair is played 100 percent at all
  six spots, and the rank arm replaces the discrimination it can no longer provide. **The jam-inversion canary
  that rejected the first cutover** - no committed spot faces a five-bet jam, so it is retained against the
  **export**, and since hero's own jam lives at the withheld four-bet-facing spots the report prints AA's jam
  weight at each of those fifteen, which is not itself vacuous.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code, every figure the criteria above name: the
  census, a traced cell with its reach and arrival, the three relations, both arms on every partition, the
  group ladders, the orderings, the chart against the expectations, the cutover ledger, the refusal inventory,
  and the flat frequency per spot. One number is recomputable by hand from a committed file and the packet
  says which and how. The corpus comparison, the pre-registered prediction against its band, the price the
  corpus was played at and what the measurement cannot separate are republished as evidence gating nothing,
  and the limped-decision-point count is printed with its definition.
- The generator validates its own figures and exits non-zero when they do not hold: the census against the
  export's node count and the five-code vocabulary, the artifact's spot count against the walk's key by key,
  each arm on every partition, and the old-versus-new disagreement count against its direction rows. Both
  command IDs are declared here, registered in `COMMANDS` in `scripts/run_verify.py`, and carry a mutation
  canary authored before the implementation, with `check_gate_bite` proving each bites. One proves a wrong
  artifact fails the command rather than being rendered; one commits a multiway spot the predicate excludes,
  which nothing else notices.
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`, the audit
  packet carries plain-language pass/fail evidence, and deferred work is in `backlog.yml`.

### The backlog entries this phase settles
Each is closed, restated with a measurement, or moved forward with a reason recorded in `backlog.yml`. The
sweep covers every entry reading `phase: "14"` and every entry this phase's stages filed under a subject area
instead, which a phase-scoped sweep cannot see.
- Moved to phase 17: `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`, `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`,
  `CHART-CANNOT-ANSWER-A-LIMPED-POT`, `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK`. Closed:
  `CHART-HERO-MUST-NEVER-LIMP`, `REALIZATION-MODEL-UNDERPRICES-POSITION`,
  `PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP`, the artifact half of `BLIND-STRUCTURE-VARIANTS` and
  `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE`, and - on this rewrite -
  `PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP`. Reopened:
  `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`, closed on ship-as-solved against a config since changed.
- Restated with their excluded node counts and the route back - a solver fix for the first, a fitted pot-type
  cell for the second: `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` and
  `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`, the second no longer describing a committed spot but
  the reason `derivation:weighs-a-mispriced-four-bet-branch` exists. `COMMITTED-SPOTS-NEVER-FLAT-A-RAISE` is a
  misnomer whose three example spots are not committed, and is **renamed** onto what was measured: the big
  blind over-folds, decision 24's accept-and-record unchanged. Also restated:
  `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`, `CHART-COVERAGE-EXPANSION` and
  `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`. Left open with a reason: `CHART-CANNOT-ADVISE-A-FIVE-BET` and
  `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`.

## Required reports
- `reports/active/latest_derived_chart_report.txt`

## Required command IDs
- `pytest_derived_chart`
- `generate_derived_chart_report`

## Human vetting packet requirements
- Plain-language summary of what changed and why the phase was re-sourced and re-scoped, a pass/fail checklist
  for a non-coding reviewer, a command summary linking the reports, and known limitations. **What six spots
  means for the trainee, stated first and not left to be inferred**: which decisions the bot now answers, that
  it refuses every other preflop spot, that it gains nothing the retired chart answered and refuses 29 keys it
  did answer, and that the six still carry 81.1 percent of the traffic.
- The three withholdings in poker terms, each with the evidence that took it and the fix that returns it,
  including the four-bet range and AA's jam weight at the withheld four-bet-facing spots and the jam call-offs
  at the withheld jam spots, since those ranges are why those families are refused.
- The defence level and the flat frequency per opener, and the four-bet-pot contamination of what is
  committed, as the reads a human owes before the artifact is frozen. Why the multiway half is not committed,
  checkably: price offered, equity the model assigns, equity the hand has, fold produced. Which criteria are
  vacuous over this committed set and why, listed rather than silently passing - no packet may claim the
  committed set is priced exactly, that a vacuous check passed, or that either arm passing means the ranges
  are good poker.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success, infer missing strategy, chart or hand-history
  behavior, or change this contract during implementation mode.
- Do not hand-edit the committed artifact, the sizing table, or the expectations file - each is derived or
  external, and a hand edit is a number with no origin - and do not fill a cell the selection rule or a
  withholding excluded, by interpolation, neighbouring cell or heuristic.
- Do not choose the selection rule to fit the byte limit and then justify it in poker terms, and do not widen
  the predicate or narrow the corpus sample to raise an agreement rate. A spot is excluded because the source
  misprices it; a rate is not a reason to commit one. Do not soften either arm, drop a partition, fold two
  exclusion codes together, or count a vacuous criterion as a pass.
- Do not patch `RULED_CONFIG` at runtime for anything that writes to the repo. `config_errors` refusing an
  export built from an unruled config is the check working, not an obstacle.

## Regression expectations
- Previously completed phase gates remain verifiable, generated human docs remain current, and file-size and
  scope checks continue to pass. Every frozen test of a completed phase that asserts against the chart's
  contents is migrated in the same task that changes those contents, at stage 4 and before the freeze, as
  phases 11 and 12 each learned. The self-play simulator's figures and every committed refusal count are
  expected to move a long way, because the chart answers six spots where it answered 36 and the refusal rate
  rises rather than falls. A moved number is not a regression; the report says which moved and why.
