# Draft contract for decision 20 - NOT the contract

This is working material for the contract rewrite phase 14 owes. Updated 2026-08-31 after rounds 13 and 14 reviewed it: the multiway-repair prohibition is restored, the false "the bot refuses rather than advising a stack-off" sentence is corrected, the solve-target level is restored, and the mechanical prose defects are fixed. It stands at 305 and still owes the two criteria round 14 asks for.
2026-08-31, preserved here because `docs/phase_contracts/*.md` is capped at 300 lines by
`check_file_sizes.py` and this draft is **323**. It is not a second contract and nothing reads it;
`docs/phase_contracts/PHASE_14_CHART_CUTOVER.md` remains the only one.

**Why it does not fit.** Decision 20 adds criteria the contract did not have - a third exclusion
reason and its census, the disappearance of every jam from the committed set, the training-rake
qualification on the source card, the unfitted-terminal caveat on the three-bet spots, and a pinned
definition for the dominance gate - to a document already at exactly 300 after three amendments. Cut
against it are figures measured on builds the phase discarded, which is the right trade and still
about twenty lines short. AGENTS.md says a contract at the cap is due a rewrite that folds its
amendments into the criteria they amend, that the rewrite is its own `contract-update` task, and that
the cap is never raised; this session attempted it incrementally, which is the thing that section
warns against, and it did not converge.

**What the rewrite has to do**, beyond adopting the draft below: fold the Scope section's history into
the decision record and keep only the three rulings; drop every stated level that was measured on a
build the phase no longer ships, replacing it with the criterion and the stage it is measured at; and

---

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
The bot plays from `data/artifacts/preflop/six_max_nl25_100bb.json`, 36 spots derived from a GTO Wizard
export of a raked game. Phase 10 captured a GTOpen solve of the game this bot is trained for -
six-handed, 100bb, rake-free. This phase derives the artifact from that solve and deletes the old one,
committing the ranges every later phase is measured against; hence `auto_advance: false` in
`verification/loop_policy.yml`.

Three rulings shape what gets committed. The criteria below enforce them and the decision record argues
them; neither the argument nor its measurements are repeated here. **Decision 14** re-solves with
`add_allin: false` at a `0.00016` target, giving a tree of **33,969 action nodes and 72,798 total**
against 38,828 (`a386c77` is the superseded build). **Decision 1, as superseded on 2026-08-25**, makes a
node eligible when at most one opponent has voluntarily invested beyond the blinds **and** at most two
players are still live - both clauses, because the approximation bites at *terminals* and a node's
strategy is backward-induced over every terminal below it
(`SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS`); **it selects 51**. **Decision 20**
solves with `realization: calibrated` and **withholds the 15 four-bet-facing spots, committing 36**,
because the fit behind `calibrated` has no four-bet-pot cell and no other setting is better.

**The cost, measured rather than estimated.** The 51 are a strict subset of the superseded 86 - 35 lost,
none gained, all all-in-facing - and only the small blind's opening range survives. Decision 20 spends
15 more: every spot where hero faces a four-bet, which is every spot where hero could jam.

Five things arrive ruled and are not reopened: limps left the solve at phase 10's human gate, so the
export is `limp: false` and every count here is a no-limp count; the solve is rake-free in its betting,
with the qualification the criteria carry; phase 12's ruling 8 stands on opponent price abstraction; the
export is not graded against GTO Wizard, since a threshold over the gap between two programs measures
two products; and the key grammar, depth, table size and `data/samples/**` stand.

## Non-goals
- Do not add PokerNow automation, browser or platform observation, runtime solver calls, LLM-backed
  poker decisions, or training UI surfaces. These are the standing V1 boundaries.
- Do not re-solve at a second opening price, with limps, at another depth or table size; all are
  phase-10-shaped work. The one re-solve this phase runs changes `add_allin` and the solve target and
  **nothing else**, and the criteria below enforce that.
- **Do not fix the multiway pricing here, do not repair a pricing defect by changing `realization`, and
  do not commit a mispriced spot with the defect recorded as a caveat.** The multiway fix changes
  GTOpen's `KIND_POT_SHARE` terminals, has its own benchmarking and is out of scope by Taylor's ruling
  of 2026-08-31; no config turns it off, all three models multiplying a product. One field prices the
  whole tree, so a setting that fixes one pot type breaks another and decision 20 measures that. A
  caveat does not reach the human at the table; a spot with no trusted ranges is refused.
- Do not change the spot key grammar: re-keying re-seeds every mixed cell
  (`RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`) and paying that twice buys one result. And do not rederive
  `data/artifacts/preflop/expectations/six_max_nl25_100bb.json`: it is the only number here this repo
  did not produce, which is what catches a uniformly wrong range.
- Do not widen the predicate, or lift decision 20's withholding, to recover coverage: a spot the source
  should never have offered is not coverage, and neither is one it cannot price.

## Acceptance criteria

### What the re-solve owes
The phase runs exactly one re-solve, enumerated from `gtopen_six_max_100bb_rakefree.source.json` rather
than remembered.
- `config_posted` is byte-identical to the previous card **apart from `add_allin`**, the solve block
  differs only in its target, and `model` names the realization the config posts, derived from
  `RULED_CONFIG` rather than typed - a card naming one model beside a `config_posted` naming another is
  the one claim about this export no gate command reads. A test asserts the export's config equals
  `RULED_CONFIG` field for field; `config_errors` enforces it at import.
- The two-process determinism proof is re-run and its result written onto the source card by the script
  rather than typed in afterwards, per `--determinism-only`. The walk re-resolves every node from its
  recorded path and reports the mismatch count, which must be **0**; its node count equals the
  `action_nodes` the solver reports and the card publishes both.
- The two checksums and the recomputed `size` block are refreshed on the committed card, and both gated
  orderings are re-asserted on the new solve rather than carried over. Movement beyond the marginal
  cells is a human read of the range grids, not a number in a report.
- **The solve target is `0.00016` at a 2,000-iteration cap**, superseding phase 10's decision 3 here
  only. The ruled build first meets it at **iteration 1,900 of 2,000**, so the cap nearly binds and a
  lower target would make `achieved < target` false; the card records the achieved gap and iteration.

### Selecting what gets committed
- The predicate selects a node when at most one opponent voluntarily invested **and** at most two
  players are still live; it selects **51**, and the predicate is the ruling rather than the number.
  Both clauses live in the converter, never a node list, never one alone.
- **Decision 20 then withholds the 15 four-bet-facing spots of those 51, so 36 are committed.** The fit
  behind `calibrated` has cells for single-raised and three-bet pots and none for a four-bet pot, so
  those spots are priced by a table outside its support and are refused for the same reason multiway
  pots are: a spot the source misprices is declined, never answered from a neighbour.
- Every node is accounted for in exactly one of three buckets - committed, excluded, or inexpressible -
  summing to the node count the card publishes. Every reason comes from a closed vocabulary the tests
  enumerate, so a node the converter failed to handle cannot be filed as a property of the grammar.
- The exclusion vocabulary distinguishes **three** reasons: outside the selection rule, mispriced
  multiway, and mispriced in a four-bet pot. One code loses which nodes come back by which route - a
  solver fix for the multiway kind, a fitted pot-type cell for the four-bet kind.
- The census is **36 committed, 15 `source-misprices-four-bet-pot`, 29,104 `source-misprices-multiway`,
  4,814 `outside-selection-rule`, summing to 33,969**; the report publishes it with reasons named. The
  inexpressible bucket is empty over this export and the report must not imply it is populated.
- A node the rule excludes is a lookup miss at runtime, refused with a code and never answered from a
  neighbouring cell. That refusal is the point of the exclusion.
- The committed artifact carries, per cell, enough arriving reach for a reader to tell a cell the solver
  trained from one it barely visited; the report prints the distribution over the committed set.
- `data/artifacts` stays inside the 20 MiB cap; exceeding it is a halt and a decision, never a raise.

### The derived artifact
- The artifact is derived from `data/artifacts/preflop/exports/` by a committed script, reproducible
  byte for byte, with a `--check` mode that fails the gate when it is not.
- The retired `six_max_nl25_100bb.json` is **deleted** and a test asserts it absent. No collision is not
  retirement: **31 of its 36 keys collide with nothing the new artifact declares** and only 5 collide
  exactly, so both would load clean and the bot would play raked ranges believing it plays the rake-free
  solve.
- A test proves the converter reads raise sizes from the export's action labels, not from constants:
  over a synthetic export with perturbed labels it produces keys carrying the perturbed sizes.
- The sizing table is rederived from the export in the same run as the artifact; the expectations file
  is not, and the report prints the chart against it gated by nothing, per phase 10's decision 6.
- **The sizing table holds every raise size a spot offers, with the weight hero gives each**, and the
  key is unchanged because it states what hero faces, not what hero does. Closes
  `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT`. **The schema is entirely unexercised over the
  committed set: 0 of the 36 offer two prices**, 21 offer one and 15 no raise at all, so any test of the
  two-price case passes vacuously and must be labelled so. Decision 6 records why the schema is kept; a
  check that cannot fail must not be counted as one that passed.
- A spot offering no raise carries no size and the strategy refuses rather than invent one. The
  invariant is two-directional - a positive raise weight implies a sizing entry and no entry implies no
  raise weight - and over the 36 both sets are non-empty: **21 carry an entry, 15 do not**. A test
  enumerates the three menus - **20 call/fold/raise, 15 call/fold, 1 fold/raise** - since a converter
  that dropped an action would pass every other check. Prices are exactly `[2.5, 7.5, 22.5]`.
- **Hero can never initiate the last raise, and the chart still answers 15 call-offs for a full stack.**
  Five-betting is only legal facing a four-bet and those 15 spots are withheld, so `100.0` leaves hero's
  price menu; but 15 committed spots face a five-bet jam, and at them the chart puts the last 77.5bb in.
  Those cells are hero's response to a villain jam range computed at the very nodes this ruling refuses,
  so they are a **second inheritance** beside the three-bet spots and the packet names both. The
  jam-inversion canary that rejected the first cutover is **vacuous over the committed set** and is
  retained against the *export* instead; the report prints AA's jam weight at those 15 as excluded
  evidence. `CHART-CANNOT-ADVISE-A-FIVE-BET` records the capability not added, not coverage spent: the
  retired chart has no four-bet-facing key either, so **the refusal rate must not rise there at all**.

### What the ranges must not have become
- No spot with an empty `action_sequence` carries a call weight, enforced by the artifact schema rather
  than measured over one file. That is what `CHART-HERO-MUST-NEVER-LIMP` asks for: the export enforces
  it by construction, "but that is a property of the data rather than a rule", and phase 14 owns the
  schema. The retired chart limps 13.73 percent from the small blind across 103 classes.
- The two relations that hold in every preflop spot - a higher pair played at least as often as the pair
  one rank below, and a suited hand at least as often as the offsuit hand of the same ranks - are
  **measured per cell and gated on aggregates only**, because among near-indifferent hands the solver's
  split is its considered answer and a per-cell gate would reject it. Gated instead is the same
  dominance over **groups**, where indifference cancels: the combo-weighted play frequency of each pair
  band and each suited row is at least that of the band or row below, over hero's arriving range. No
  wider order is asserted, because preflop strength is not totally ordered.
- The aggregate gate is **re-measured over the committed 36 before it is frozen**, and the phase halts
  rather than ship a gate it has not seen pass. Over the retired 5,626 no form passed: the
  suited-against-offsuit aggregate scored the wrong index mapping as better, 2,007 nodes against 818, so
  it rewards a transposed index rather than catching one
  (`PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP`). Its definition is pinned as data before
  freezing - weighting, reach floor, tolerance, family exclusions, per spot or per chart - the prose
  having produced seven counts (`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`).
- The per-cell count, its worst cases and their bands are published for a human, gated by nothing, and
  retaken on the committed set. `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` covers why the aggregate
  alone is not enough.
- The orderings the export was gated on hold: later position opens wider among the four non-blind
  positions, and the big blind defends more against whoever opens wider. **The first half is checked
  against the export, not the artifact, which holds zero non-blind opening ranges** - it cannot violate
  that clause, so a test asserting it over the artifact is vacuous like the sizing schema. The second
  half is checkable over the artifact and is where the gate belongs.
- **An ordering is not a level, and only the level catches a broken realization model.** Both orderings
  hold under `static`, which defends the big blind 100.00 percent, so the defence level per opener is
  measured, printed against the expectations file, and read by a human before the artifact is committed
  (`STATIC-REALIZATION-UNMEASURED-IN-SINGLE-RAISED-POTS`).
- The source card states three limitations of what is committed, in poker terms with their measurements,
  so a reader can tell each absence and caveat is a decision: `REALIZATION-MODEL-UNDERPRICES-POSITION`
  per decision 3, retaken on the committed set; that under `calibrated` a rake-free solve is **not
  rake-free at its heads-up flop terminals**, the fit being measured net-of-rake over the gross pot
  (`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`); and that the committed three-bet spots weigh
  hero's four-bet on terminals the fit has no cell for
  (`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`). The multiway and four-bet defects are stated
  with their excluded node counts.
- **`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT` is re-measured on the committed set rather than assumed
  to have moved**, with the flat band and the opener widths printed beside each other. Whether it
  survives is a result either way; the numbers earlier drafts quoted were taken on discarded builds.

### The closing measurement
- The prediction is written into the decision list before the measurement runs, **per opener and with a
  magnitude band** - a quarter to one times that opener's defence delta - with the deltas **recomputed
  from the committed 36**, since decision 9's bands were fixed on a build this phase no longer ships. A
  sign-only prediction cannot answer this phase's question: five points of defence is about 60 combos of
  1,326, so any nonzero movement confirms it while leaving the gap intact. It covers price and its
  direction - the small-blind open reprices from 3.5bb to 2.5bb.
- **The permissive agreement rate is never reported alone, because on this corpus it rewards an
  unconverged chart.** Agreement means nonzero weight on the observed action, so a cell with every
  action nonzero cannot disagree with anything, so a chart converging to purer cells scores worse while
  playing better. The report publishes the **strict sampled-action rate and the cell-purity statistic
  beside** it, over the shared spots, and states that a fall is what a converged chart looks like rather
  than a regression; printing the fall alone states the reverse of the truth
  (`AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`). **Every rate is measured at stage 6 against the
  committed 36 and none carried forward** - earlier drafts quoted discarded builds
  (`A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT`).
- The report names all three candidate explanations for a residual gap - rake, price, and realization
  underpricing position - saying which it separates and which it cannot; two survive uncontrolled, and
  the rake one is qualified by the source-card criterion above rather than claimed.
- The retained sample and refusal rate are reported beside every agreement rate, with the definitions
  that make one readable: agreement means nonzero weight, and real players are not an oracle.
- **The refusal rate is reported against a named baseline and split by cause**, so a multiway refusal
  reads apart from a four-bet-pot refusal, a limp or an unmatched key. The baseline is the retired
  chart, and the rate must **rise only on the spots this phase's two exclusions and the limp account
  for, and nowhere else**. A rise outside them is a defect, not the cost of a ruling. The report bounds
  what the chart answers at all - six-handed, 100bb, symmetric stacks, no straddle, no ante, one opening
  price, heads-up only, **no spot facing a four-bet** - so no rate reads as a grade on preflop play.
- **Each exclusion's coverage cost is reported separately**: the multiway ruling's, the re-source's, and
  decision 20's four-bet withholding. Conflating them charges one ruling for another's cost.
- The refusal inventory is republished and its movement stated by reason rather than as one total, over
  the closed vocabulary `lookup.py` defines. The phase publishes its own count of decision points facing
  a limp with the definition it counted by, because `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry
  one.
- Where the derived and retired charts both answer the same corpus decision, the report says how often
  they disagree and in which direction, reading the retired chart from git history.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code: the node census with reasons, one cell
  traced from export node to artifact row, the two dominance relations, the two orderings, the chart
  against the GTO Wizard expectations, the withheld jams with AA's weight at each, and the corpus
  figures before and after. At least one number is recomputable by hand from a committed file, and the
  audit packet says which and how.
- The report generator validates its own figures and exits non-zero when they do not hold: the node
  census, the artifact's spot count against the walk's, the dominance relations, and the old-versus-new
  disagreement count. The rest is prose and the audit packet says so.
- Both new command IDs are declared here, registered in `COMMANDS` in `scripts/run_verify.py`, and carry
  a mutation canary authored before the implementation, with `check_gate_bite` proving each bites. One
  proves a wrong artifact fails the gate, not merely a wrong report; one widens the predicate to admit a
  multiway node, which nothing else notices.
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`, the
  audit packet carries plain-language pass/fail evidence, and deferred work is in `backlog.yml`.

### The backlog entries this phase settles
Each is closed, restated with a measurement, or moved forward with a reason; the reasoning lives in
`backlog.yml` rather than here.
- `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`: recomputed on the sample the committed chart retains, and
  restated against the strict rate too, since `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART` shows the
  permissive rate cannot carry it alone.
- `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` and `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`:
  each restated with its excluded node count and the route by which those nodes come back - a solver fix
  for the first, a fitted pot-type cell for the second. They are why the phase commits 36; the roadmap
  owes them a slot this phase does not assign.
- `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` is **reopened**, having closed on ship-as-solved against a
  config that has since changed. `CHART-HERO-MUST-NEVER-LIMP` closes on the schema rule above, and
  `CHART-CANNOT-ADVISE-A-FIVE-BET` opens on the jam this ruling withholds.
- `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`: restated with what `add_allin: false`
  did and did not fix. The model still prices the all-in terminal exactly and every named raise through
  a model; only the misplaced jam is gone.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` closes on one of its three dispositions;
  `CHART-CANNOT-ANSWER-A-LIMPED-POT` is restated with the measured cost and its definition; and
  `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` is stated on the source card rather than closed.
- `CHART-COVERAGE-EXPANSION`, `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` and
  `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` are restated rather than closed: the first two are now
  mostly blocked on GTOpen, and the third must not keep a headroom argument nothing rests on.
- `BLIND-STRUCTURE-VARIANTS` and `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` both want a
  declared blind structure on the artifact. This phase either writes it or records why it waits, by id.
- Every other entry reading `phase: "14"`, and every entry this phase's stages filed under a subject
  area instead - which a sweep scoped by phase cannot see. The eleven the first cutover's reviews filed
  are included, and the three about the export are re-measured rather than assumed to have moved.

## Required reports
- `reports/active/latest_derived_chart_report.txt`

## Required command IDs
- `pytest_derived_chart`
- `generate_derived_chart_report`

## Human vetting packet requirements
- Plain-language summary of what changed, including why the phase was re-sourced and re-scoped, and a
  pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports; known limitations and deferred items.
- The closing measurement with what it does not establish in the same paragraph as what it does, and the
  permissive agreement rate never stated without the strict rate beside it.
- The selection rule and the four-bet withholding in poker terms, with what the bot now refuses that it
  used to answer and what it answers that it used to refuse - including why the multiway half is not
  committed, checkably: price offered, equity the model assigns, equity the hand has, fold produced.
- Which committed spots inherit a pricing defect anyway, named individually with the frequencies as
  evidence. No packet may claim the committed set is priced exactly.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success, infer missing strategy, chart or hand-history
  behavior, or change this contract during implementation mode.
- Do not hand-edit the committed artifact, the sizing table, or the expectations file: each is derived
  or external, and a hand edit is a number with no origin.
- Do not fill a cell the selection rule or decision 20 excluded, by interpolation, neighbouring cell or
  heuristic.
- Do not choose the selection rule to fit the byte limit and then justify it in poker terms, and do not
  widen the predicate or narrow the corpus sample to raise an agreement rate. Do not pool the two
  populations, and do not read a residual disagreement as a chart defect while price and realization are
  uncontrolled. A spot is excluded because the source misprices it; a rate is not a reason to commit
  one.
- Do not patch `RULED_CONFIG` at runtime for anything that writes to the repo. `config_errors` refusing
  an export built from an unruled config is the check working, not an obstacle.

## Regression expectations
- Previously completed phase gates remain verifiable, generated human docs remain current, and file-size
  and scope checks continue to pass. Every frozen test of a completed phase that asserts against the
  chart's contents is migrated in the same task that changes those contents, at stage 4 and before the
  freeze; phases 11 and 12 each deferred this and each paid a separate repair task.
- The self-play simulator's figures are expected to move, because the ranges moved and because the bot
  now refuses the multiway and four-bet spots it used to answer. A moved number is not a regression; the
  report says which moved and why rather than pinning the old value.
