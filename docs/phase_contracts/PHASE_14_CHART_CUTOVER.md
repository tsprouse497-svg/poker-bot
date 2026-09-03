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
**What is on disk right now, stated first because three rewrites of this contract described a state that
had already changed.** The GTO Wizard chart is **already deleted**, and what is committed is
`six_max_100bb_rakefree.json`, **86 spots from the superseded export**, **36** carrying a sizing entry and
every one of the 36 priced at a jam the ruled config cannot produce. Stage 6 replaces it, and a test asserts the artifact's source checksum equals
the export's - the check that would have caught it. Phase 10 captured a GTOpen solve of the game this bot
trains for: six-handed, 100bb, rake-free. This phase derives the artifact from it and commits the ranges
every later phase is measured against; hence `auto_advance: false` in `verification/loop_policy.yml`. The
corpus verdict is **phase 17**.

The committed export stands as solved and is **not re-solved**: `add_allin: false`,
`realization: calibrated`, **33,969 action nodes**, solve record on the source card.

**249 nodes are committed** - 5 first-in, 25 facing an open, 219 facing a three-bet - carrying **98.5949
percent** of preflop decisions. Decision 49 carries the corrected counts and supersedes every figure
taken over an earlier set.

**Decision 44 states the rules the bot plays by and governs this contract**, as amended by 45 to 51. **The
phase ships GTOpen's preflop output as solved**, withholding only the four-bet family, which a later phase
takes up, and the multiway spots the filter refuses. The bot never cold-calls, though opponents do. Four
defects are accepted on purpose with published costs: the tight big blind, the pair and kicker ladder
inversions, and merged flats playing differently. Nothing gates on whether a range is good poker.

## Non-goals
- The standing V1 boundaries: no PokerNow automation, browser or platform observation, runtime solver
  calls, LLM-backed poker decisions, or training UI surfaces. No re-solve at a second opening price, with
  limps, at another depth or table size. **No re-solve at all.**
- **Do not fix the multiway pricing, repair a pricing defect by changing `realization`, or commit a
  mispriced spot with the defect recorded as a caveat** (Taylor, 2026-08-31). Do not change the spot key
  grammar (`RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`). Do not rederive
  `data/artifacts/preflop/expectations/six_max_nl25_100bb.json`, the only figure here this repo did not
  produce.
- **Do not patch the GTOpen clone.** Decision 33 declined the `call_only_seats` mirror; decision 36
  declined a depth-aware re-raise multiplier. Neither is reopened by an implementer.
- **Do not adjust any published frequency by hand**, widen the big blind's flat, or smooth a ladder.
  Decisions 34, 41 and 47 accept those as solved; a smoothing rule is a later `contract-update`.
- **Do not reinstate decision 1's opponent-investment clause as a third filter**, which decision 40
  dropped as strictly stronger than exposure. Do not render the corpus verdict; that is phase 17's.

## Acceptance criteria

### What the committed export owes
- `config_posted` equals `RULED_CONFIG` field for field, and the test then names the forbidden fields
  individually. `model` is derived from `RULED_CONFIG` rather than typed.
- The determinism proof and the re-resolve walk are separate obligations, both written by the script and
  neither reading `PENDING`: a second full solve in a fresh process against a restarted server, diffed node
  by node, at **0 divergence and 0 shape differences**; and every node re-derived from its recorded path at
  **0** mismatches over all 33,969.
- **The target is `0.00016` at a 2,000-iteration cap**, first met at iteration 1,900, so the cap nearly
  binds; the achieved `0.00015591` clears the target by 2.6 percent. The card carries one solve record,
  refreshed checksums and a refreshed `size` block, its `bytes_per_expressible_spot` note being stale at 51
  spots. `data/artifacts` stays inside the 20 MiB cap; exceeding it is a halt, never a raise.
- **The card must describe the export it ships beside**: node count, checksum and size are asserted
  against the export file, not only against `RULED_CONFIG`, which cannot catch a card that drifted from its
  own export.

### Selecting what gets committed
- **Two filters, each tested alone, both in the converter and never a node list.** A node is committed when
  at most **two raises** are already in, nothing deeper, and when the share of its decision mass reaching a
  **multiway flop terminal is below ten percent, measured over the branches the bot can take** (decision
  46): hero's **cold** call is removed, not his call to a three-bet.
- **A third clause excludes the big blind's squeeze spots** (decision 48): hero is the big blind, faces an
  open, and a cold caller is already in. They passed the exposure filter **because** the big blind folds
  there, so little mass reaches the three-way flop - **the filter is blindest where the mispricing has
  already turned a call into a fold**, which the report states. The three clauses **select 249**, and a
  test proves no clause is co-extensive with another.
- **Exposure is measured, not inferred from live players**, by a walk from the node to its leaves, and is
  published per committed spot with the terminal split and the admitted and refused extremes. Any future
  build re-measures rather than carrying these figures forward
  (`MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`).
- **The census has four buckets summing to 33,969**: **249** committed, **348**
  `derivation:multiway-exposure-above-threshold`, **10** `derivation:big-blind-squeeze-spot`, **33,362**
  `derivation:beyond-committed-raise-depth`. The inexpressible bucket is empty and publishes as a result.
  Reasons come from a closed `namespace:reason` vocabulary the tests enumerate, disjoint from the runtime
  miss codes; an unknown action kind raises; a census folding two codes together balances and is refused
  anyway.
- **An excluded node is a lookup miss at runtime**, refused with a code naming the spot, no neighbouring
  cell and no price substitution consulted. A cold call in front of hero refuses nothing on its own.
- **The bot's own cold call is merged into its raise, not deleted** (decision 45). Of the 25 facing-an-open
  spots, the **5** big-blind spots publish fold, call and three-bet unchanged; the **20** others publish
  **raise or fold**, each cell's published raise weight being the solve's raise plus its call. The **219**
  three-bet-facing spots publish fold, call and four-bet. Tests assert the menu shape per family and that
  each merged spot's published defence equals the solve's raise-plus-call to the basis point; a converter
  that publishes a cold-call weight, or drops one instead of merging it, fails. The report prints the cells
  moved and each merged spot's defence against its reference band.
- The artifact carries **per cell the arriving reach** and **per spot the probability of arriving at all**.
  Reach is the plain mean over the 169 classes and **no reach floor selects cells**. Arrival is parts per
  billion, one left-to-right product from the root rounded once at the end; one above one, or claimed for
  an undeclared spot, is refused at construction. Arrival spans many orders of magnitude here, so the grain
  is printed with the count of spots rounding to zero, and the zero-arrival case is not vacuous.
- **No committed row the solver trained is its untouched initialisation**: uniform splits number **0 among
  cells with non-zero reach**, under both the exact and tolerant reading, the readings agreeing as sets
  (`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`). The reach precondition is part of the criterion, so a
  test asserts the converter drops zero-reach classes.

### The derived artifact
- Derived from `data/artifacts/preflop/exports/` by a committed script, reproducible byte for byte, with a
  `--check` mode that writes nothing and fails the gate when it is not. That test carries the committed
  spot count with it.
- The retired chart stays **absent**, asserted so against the artifact directory, its glob and `sizings/`,
  and the report prints the cutover ledger, which must balance.
- **249 nodes are not self-evidently 249 keys**: the spot-count test runs **key by key**, and a grammar
  collision is a halt and a decision, never a silently merged cell.
- The sizing table is rederived in the same run; the expectations file is not, and the report prints the
  chart against it gated by nothing (decision 6). **The table holds every raise size a spot offers with
  hero's weight on each**, keyed by what hero faces (`CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT`). A
  test proves the converter reads sizes from action labels rather than constants, via a perturbed synthetic
  export. Prices are exactly `[2.5, 7.5, 22.5]`.
- **The sizing invariant is two-directional**: a spot offering a raise carries a key for every size it
  offers, and one offering none carries no key, **the strategy refusing rather than inventing a size**.
- **The artifact declares the blind structure it was solved at**, read off the posted config, refusing an
  impossible one at construction: a blind at or below zero, a small blind at or above the big blind, or a
  negative ante. A zero ante stays valid.

### What the ranges must not have become
- No spot with an empty `action_sequence` carries a call weight, enforced by the artifact schema
  (`CHART-HERO-MUST-NEVER-LIMP`).
- **Four relations are measured per cell** at decision 10's one-point tolerance. Three run on
  play-not-fold: a higher pair played at least as often as the pair below; a suited hand at least as often
  as its offsuit twin; and within a grid row a higher kicker at least as often as the kicker below, suited
  and offsuit apart, adjacent kickers only, **132 comparisons** over a full grid. **The fourth runs on
  the published raise weight** (decisions 50, 55), merged as the bot plays it, because the inversion that
  halted this phase sits on the raise action with both hands played 100 percent, where play-not-fold is
  blind. **None is gated as an order**; gated is that the measurement was taken over every cell, with
  counts and worst cases published. Their definition - weighting, reach floor, tolerance, family
  exclusions, per spot or per chart - is pinned as data before it is measured
  (`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`).
- **The pair and kicker ladders both invert; decisions 41, 47 and 51 accept all of it as solved.** The report
  prints them as accepted defects, separates the wheel-ace cases that are correct poker from the ones with
  no poker story, and publishes the mixed-cell share. **A pick among hands the solve prices alike is bluff
  selection**: it ships unmeasured, nothing waits on a value gap, and no packet may call it noise.
- **The group-order ladders gate nothing and are published for a human.** The measurement is taken on every
  partition and printed, never asserted: the family returned a different verdict on every committed set it
  has been run over, so it measures set composition rather than the hand index.
- **The range gate is two counterfactual arms, both strict, a tie refusing on each, each keeping its own
  validator and parameter name.** The suit arm transposes each suited hand with its offsuit twin
  (`transpose_hand_index`) scoring **spots** (`spots_violating_twins`); the rank arm reverses every rank
  (`reverse_hand_ranks`, its own inverse) scoring **cells** on the row ladder. The solved index must flag
  strictly fewer than the counterfactual; what is asserted is the direction. Both gate on all **ten**
  partitions - the whole set, one per hero seat, one per raises faced - measured from the committed set and
  never carried over, and dropping one is forbidden. The rank arm carries a test proving it discriminates
  where the others cannot: a rank-reversed chart scores identically on the suit arm, and the test shows
  that arm accepting it while the rank arm refuses it.
- **The rank arm is scored over every spot in its partition**, a comparison whose partner cell is absent
  being skipped and the skipped count published per partition: `reverse_hand_ranks` is total only on a full
  grid. The restriction to spots closed under reversal is withdrawn, its stated justification having failed
  to reproduce (`RANK-ARM-RESTRICTION-RESTED-ON-A-SPLICED-FIGURE`). **A partition scoring fewer than five
  spots is published and not asserted**, a strict gate over one or two grids being a coin flip. Pinning that
  set is part of pinning the relations above.
- **Neither arm passing is evidence the ranges are sound.** Both are extraction checks and cannot see
  over-folding, a mis-assigned actor, or a cross-family inversion
  (`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR`, named in the packet).
  **Both are re-measured over the committed 249 before they are frozen and the phase halts rather than ship
  a gate it has not seen pass.** A failure is a halt and a decision for Taylor, never a tolerance re-derived
  until it admits the artifact it judges.
- **The equity relation is published and gates nothing** (decision 42). The 169-by-169 all-in equity matrix
  is committed and deterministic; the relation is that at a spot where hero closes the action, no class
  folded above 99 percent holds more equity against the opponent's arriving range than a class played above
  99 percent. **A correct chart fails it**, so `GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE` stays
  **deferred** and no packet may claim it closed.
- The orderings the export was gated on hold: later position opens wider among the four non-blind
  positions, and the big blind defends more against whoever opens wider. Both are checkable against the
  artifact. **An ordering is not a level, and only the level catches a broken realization model**, so the
  defence level per opener is measured, printed against the expectations file, and read by a human before
  the artifact is committed (`STATIC-REALIZATION-UNMEASURED-IN-SINGLE-RAISED-POTS`).
- **The big blind's flat barely moves with who opened, and this phase accepts that** (decision 34). It
  reads wider than the raked reference against four openers and narrower only against the button, so the
  defect is that invariance, not an over-fold. The report prints defence and flat per opener against the
  reference and the EV forgone **at both ends of the realization range, never a midpoint**.
- **Every published band is its family's true min and max, and a test asserts it.** No four-bet frequency
  may be offered as evidence that the unfitted terminal fails to reach the output
  (`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`).
- The source card states each limitation in poker terms with its measurement: that under `calibrated` a
  rake-free solve is **not rake-free at its heads-up flop terminals**
  (`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`); that the four-bet is solved a quarter oversized
  (`PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`); that the ranges answer a field that under-cold-calls
  (`PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS`); and that merged flats play differently
  (`MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED`). The excluded four-bet family is stated
  with the continue range that took it, against its reference.
- **Three criteria have no instance over the committed 249 and are each labelled vacuous wherever
  reported**, never counted as a check that passed, being retained because a later solve reactivates them:
  the two-price sizing schema, kept per decision 6 and proved against a synthetic export; the **no-raise**
  half of the sizing invariant, no committed spot offering zero raises; and the jam-and-named-raise
  collapse rule, which under `add_allin: false` never fires at all. **Hero's own jam** lives only at the
  excluded four-bet-facing spots, so the jam-inversion canary that rejected the first cutover is retained
  against the **export**, the report printing AA's jam weight there.

### Evidence, reports, and gate
- **Every figure this contract names as an obligation is printed by the report and re-derived by the
  generator, which exits non-zero when one does not hold.** That covers: the census against the export's
  node count and the code vocabulary; exposure per spot with the admitted and refused extremes; the
  artifact's spot count against the walk, key by key; a traced cell with its reach and arrival; the arrival
  grain with its zero count; the four relations; the group ladders; both arms on every partition with the
  rank arm's unscored count; the equity relation labelled as gating nothing; the four accepted defects with
  their measurements; the orderings; the defence level and flat per opener with the EV band at both ends;
  every band against its family's true extremes; the menu shape per family; each merged spot's defence
  against the solve's raise-plus-call; the chart against the expectations; the cutover ledger; the refusal
  inventory; and the old-versus-new disagreement count against its direction rows. **No count in this
  contract or in a packet may be hand-typed rather than re-derived**
  (`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`). One number is recomputable by hand and the
  packet says which and how. The corpus comparison, its pre-registered prediction and band, the price the
  corpus was played at, what the measurement cannot separate, and the limped-decision-point count with its
  definition are republished gating nothing (`LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION`).
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`, the audit
  packet carries plain-language pass/fail evidence, and deferred work is in `backlog.yml`. Both command IDs
  are declared here, registered in `COMMANDS` in `scripts/run_verify.py`, and carry a mutation canary
  authored before the implementation, with `check_gate_bite` proving each bites: one proves a wrong artifact
  fails the command rather than being rendered, one commits a spot above the exposure threshold.

### The backlog entries this phase settles
Each is closed, restated with a measurement, or moved forward with a reason in `backlog.yml`. The sweep
covers every entry reading `phase: "14"`, every entry filed under a subject area instead, and every entry
this contract names.
- Moved to phase 17: `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`, `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`,
  `CHART-CANNOT-ANSWER-A-LIMPED-POT`, `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK`.
- Closed: `CHART-HERO-MUST-NEVER-LIMP`, `PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP`, the artifact half
  of `BLIND-STRUCTURE-VARIANTS` and
  `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE`, and
  `PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP`.
- **Explicitly not closed**: `GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE` (decision 42) and
  `REALIZATION-MODEL-UNDERPRICES-POSITION`, accepted rather than fixed. Both restated, neither marked done.
- Filed here: `PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS`,
  `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`, `PAIR-LADDER-INVERSIONS-ARE-PUBLISHED-AS-SOLVED`,
  `MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`,
  `KICKER-LADDER-INVERSIONS-ARE-PUBLISHED-AS-SOLVED`,
  `MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED`,
  `NOTHING-MEASURES-HOW-MUCH-THE-SOLVE-MIXES`, `REFERENCE-RANGES-HAVE-NO-CITED-SOURCE`,
  `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`,
  `RAISE-ACTION-INVERSIONS-WERE-INVISIBLE-TO-EVERY-RELATION`.
- Restated with their node counts and the route back: `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`,
  `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`, `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`,
  `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`, `CHART-COVERAGE-EXPANSION`,
  `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`, `SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS`,
  `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE`.
  `COMMITTED-SPOTS-NEVER-FLAT-A-RAISE` is **renamed** onto what was measured: the big blind over-folds.
  Left open with a reason: `CHART-CANNOT-ADVISE-A-FIVE-BET`,
  `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`, `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`.

## Required reports
- `reports/active/latest_derived_chart_report.txt`

## Required command IDs
- `pytest_derived_chart`
- `generate_derived_chart_report`

## Human vetting packet requirements
- Plain-language summary of what changed and why, a pass/fail checklist for a non-coding reviewer, a
  command summary linking the reports, and known limitations. **What the committed set means for the
  trainee, stated first**: which decisions the bot answers, that it never cold-calls outside the big blind,
  that it refuses everything from the four-bet on, every pot multiway more than one time in ten, and the
  big blind's squeeze spots, and that it answers 98.59 percent of preflop decisions.
- The exclusions in poker terms, each with the evidence that took it and the fix that returns it, including
  AA's jam weight at the excluded four-bet-facing spots and why the multiway family is refused, checkably:
  price offered, equity the model assigns, equity the hand has, fold produced.
- **The four accepted defects as accepted defects, never as caveats**, each with the measurement the report
  prints: the tight big blind, **with a statement that the expectations file is a raked game so the chart
  reading wider than it is expected rather than contradictory**; the pair, kicker and raise-action
  inversions, with the wheel-ace cases separated out as correct poker; the merged flats playing
  differently; and the oversized four-bet. No packet may claim the committed set is priced exactly, that a
  vacuous check passed, that either arm passing means the ranges are good poker, or that anything here
  measures whether a range is good poker.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success, infer missing strategy or chart behavior, or
  change this contract during implementation mode.
- Do not hand-edit the committed artifact, the sizing table, or the expectations file, and do not fill a
  cell the selection rule excluded by any means.
- Do not choose the selection rule to fit the byte limit and then justify it in poker terms, and do not
  widen a filter or narrow the corpus sample to raise an agreement rate. Do not soften either arm, drop a
  partition, fold two exclusion codes together, or count a vacuous criterion as a pass.
- **Do not raise the multiway exposure threshold again.** It is ten percent by decision 46, the admitted
  and refused extremes are published, and a spot that misses it is one the source cannot price.
- **Do not publish a band measured over a subset of the family it names.**
- Do not patch `RULED_CONFIG` at runtime for anything that writes to the repo. `config_errors` refusing an
  export built from an unruled config is the check working, not an obstacle.

## Regression expectations
- Previously completed phase gates remain verifiable, generated human docs remain current, and file-size
  and scope checks continue to pass. Every frozen test of a completed phase that asserts against the
  chart's contents is migrated in the same task that changes those contents, at stage 4 and before the
  freeze, as phases 11 and 12 each learned. The simulator's figures and every committed refusal count are
  expected to move a long way in both directions: the chart answers 249 nodes where it answered 36 keys,
  and it never cold-calls. A moved number is not a regression; the report says which moved and why.
