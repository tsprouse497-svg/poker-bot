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
The bot plays from `data/artifacts/preflop/six_max_nl25_100bb.json`, 36 spots derived from a GTO
Wizard export of a raked game. Phase 10 captured a GTOpen solve of the game this bot is trained for -
six-handed, 100bb, rake-free - and Taylor judged its range grids sound. This phase derives the
artifact from that solve and deletes the old one, committing the ranges every later phase is measured
against; hence `auto_advance: false` in `verification/loop_policy.yml`.

**The phase re-sources the solve twice over, and that is what this rewrite records.** A first cutover
reached a green gate and was rejected on the poker: two stage-6 reviews found the chart jammed 100bb
with a pair of fours and never with aces, at spots arriving in 24.0 percent of hands. The cause was
the config, not the conversion. `add_allin: true` put a full-stack jam on the raise menu at **every**
node where a raise is legal, and the budget does not repair it - at 10,000 iterations the bad cell is
bit-identical. **Taylor ruled on 2026-08-30 to re-source with `add_allin: false`** - decision 14,
`a386c77` the superseded build - and **on 2026-08-31 with `realization: static`**, decision 19, since
`calibrated` prices every flop from 169 per-class numbers fitted with no four-bet-pot cell.
**The re-sourced tree is 33,969 action nodes and 72,798 total** against 38,828; five-bet jams survive
because the 3.0 multiplier puts a five-bet at 67.5bb and `allin_threshold` snaps it to the stack.

**Which nodes are committed was ruled separately and stands.** Keep a node when at most one opponent
has voluntarily invested beyond the blinds **and** at most two players are still live. Neither clause
alone is the rule, because the approximation bites at *terminals* and a node's strategy is
backward-induced over every terminal below it, per
`SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS`. The reason is
`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`: GTOpen prices a multiway pot as the product of hero's
pairwise equities, **understating true three-way equity by 10.5 points** and by 14 on the suited
connectors whose whole value is multiway. Core pricing, not a parameter. **The predicate selects 51.**

**The cost, measured rather than estimated.** The 51 are a **strict subset of the superseded 86** - 51
kept, 35 lost, none gained - and **all 35 lost are all-in-facing**, existing only because opponents
jammed at arbitrary nodes. Only the small blind's opening range survives, a cost of the multiway
ruling and not of either re-source.

Five things arrive ruled and are not reopened: limps left the solve at phase 10's human gate, so the
export is `limp: false` and every count here is a no-limp count; the solve is rake-free, removing one
of phase 08's explanations for the calling gap; phase 12's ruling 8 stands on opponent price
abstraction; the export is not graded against GTO Wizard, since a threshold over the gap between two
programs measures two products; and the key grammar, depth, table size and `data/samples/**` stand.

## Non-goals
- Do not add PokerNow automation, browser or platform observation, runtime solver calls,
  LLM-backed poker decisions, or training UI surfaces. These are the standing V1 boundaries.
- Do not re-solve at a second opening price, with limps, at another depth, or at another table size;
  all are phase-10-shaped work. The one re-solve this phase runs changes `add_allin`, `realization`
  and the solve target and **nothing else**, and the criteria below enforce that.
- Do not fix the multiway pricing here, and do not commit a mispriced spot with the defect recorded
  as a caveat. The fix changes GTOpen's `KIND_POT_SHARE` terminals and has its own benchmarking; no
  config turns it off, since `raw`, `static` and `calibrated` all multiply an equity already computed
  as a product. A caveat does not reach the human at the table; a spot with no trusted ranges is refused.
- Do not change the spot key grammar: re-keying re-seeds every mixed cell
  (`RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`) and paying that twice buys one result.
- Do not rederive `data/artifacts/preflop/expectations/six_max_nl25_100bb.json` from the export. It
  is the only number here this repo did not produce, which is what catches a uniformly wrong range.
- Do not widen the predicate to recover the 35 lost spots: a spot the source should never have offered
  is not coverage.

## Acceptance criteria

### What the re-solve owes
The phase runs exactly one re-solve and it is owed in full, enumerated from
`gtopen_six_max_100bb_rakefree.source.json` rather than remembered.
- `config_posted` is byte-identical to the previous card **apart from `add_allin` and `realization`**,
  the solve block differs only in its target, and `model` names the realization the config posts,
  derived from `RULED_CONFIG` rather than typed. A test asserts the export's config equals
  `RULED_CONFIG` field for field; `config_errors` enforces it at import.
- The two-process determinism proof is re-run and its result written onto the source card by the
  script rather than typed in afterwards, per `--determinism-only`.
- The walk re-resolves every node from its recorded path and reports the mismatch count, which must
  be **0**. Its node count equals the `action_nodes` the solver reports; the card publishes both.
- The two checksums and the recomputed `size` block are refreshed on the committed card, and both
  gated orderings are re-asserted on the new solve rather than carried over. Movement beyond the
  marginal cells is a human read of the range grids, not a number in a report.
- **The solve target is `0.00016` at a 2,000-iteration cap**, superseding phase 10's decision 3 for
  this phase only. Decision 14 records why not lower: the trajectory first meets it at iteration 1,900
  of 2,000, so the cap binds and a lower target would make `achieved < target` false. The card records
  the achieved gap and the iteration reached.

### Selecting what gets committed
- The committed spots are exactly those the ruled predicate selects - at most one opponent
  voluntarily invested **and** at most two players still live - and the predicate is the ruling rather
  than the 51 it produced. Both clauses live in the converter, never a node list, never one alone.
- Every node is accounted for in exactly one of three buckets - committed, excluded, or inexpressible
  - summing to the node count the card publishes. Both reasons come from a closed vocabulary the tests
  enumerate, so a node the converter failed to handle cannot be filed as a property of the grammar.
- The exclusion vocabulary distinguishes **two** reasons: outside the selection rule, and mispriced
  by the source. One code loses which nodes come back when GTOpen can price them.
- The census is **51 committed, 29,104 `source-misprices-multiway`, 4,814 `outside-selection-rule`,
  summing to 33,969**; the report publishes it with reasons named. The inexpressible bucket is empty
  over this export, so the three-bucket partition is really two and the report must not imply three.
- A node the rule excludes is a lookup miss at runtime, refused with a code and never answered from a
  neighbouring cell. That refusal is the point of the exclusion.
- The committed artifact carries, per cell, enough arriving reach for a reader to tell a cell the
  solver trained from one it barely visited. At `SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` the
  classes 99, 88 and AQs carry 5, 1 and 1 basis points - noise - while AA carries the full 10,000.
- `data/artifacts` stays inside the 20 MiB cap; exceeding it is a halt and a decision, never a raise.

### The derived artifact
- The artifact is derived from `data/artifacts/preflop/exports/` by a committed script, reproducible
  byte for byte, with a `--check` mode that fails the gate when it is not.
- The retired `six_max_nl25_100bb.json` is **deleted** and a test asserts it absent. No collision is
  not retirement: **31 of its 36 keys collide with nothing the new artifact declares** and only 5
  collide exactly, so both would load clean and the bot would play raked ranges believing it plays
  the rake-free solve.
- A test proves the converter reads raise sizes from the export's action labels, not from constants:
  over a synthetic export with perturbed labels it produces keys carrying the perturbed sizes.
- The sizing table is rederived from the export in the same run as the artifact; the expectations
  file is not, and the report prints the chart against it gated by nothing, per phase 10's decision 6.
- **The sizing table holds every raise size a spot offers, with the weight hero gives each**, and the
  key is unchanged because it states what hero faces, not what hero does. Closes
  `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT`. **The re-source leaves this schema entirely
  unexercised: 0 of the 51 spots offer both a named raise and a jam** - 21 offer a named price only,
  15 a jam only, 15 no raise at all - so any test of the two-price case passes vacuously here and
  must be labelled as doing so. Decision 6 records why the schema is kept anyway; a check that cannot
  fail must not be counted as one that passed.
- A spot offering no raise carries no size and the strategy refuses rather than invent one. The
  invariant is two-directional - a positive raise weight implies a sizing entry and no entry implies
  no raise weight - and over the 51 both sets are non-empty: **36 carry an entry, 15 do not**. A test
  enumerates the three menus - **35 call/fold/raise, 15 call/fold, 1 fold/raise** - since a converter
  that dropped an action would pass every other check. Prices are exactly `[2.5, 7.5, 22.5, 100.0]`.
- **The surviving jams are checked as poker, not merely counted.** Fifteen spots offer a 100bb jam
  and **every one is a five-bet spot**. A test asserts no committed spot where a low pair takes the
  jam and aces do not - the inversion that rejected the first cutover - and the report prints AA's
  jam weight at all fifteen.

### What the ranges must not have become
- No spot with an empty `action_sequence` carries a call weight, enforced by the artifact schema
  rather than measured over one file. That is what `CHART-HERO-MUST-NEVER-LIMP` asks for: the export
  enforces it by construction, "but that is a property of the data rather than a rule", and phase 14
  owns the schema. The retired chart limps 13.73 percent from the small blind across 103 classes.
- The two relations that hold in every preflop spot - a higher pair played at least as often as the
  pair one rank below, and a suited hand at least as often as the offsuit hand of the same ranks -
  are **measured per cell and gated on aggregates only**, because among near-indifferent hands the
  solver's split is its considered answer and a per-cell gate would reject it. Gated instead is the
  same dominance over **groups**, where indifference cancels: the combo-weighted play frequency of
  each pair band and each suited row is at least that of the band or row below, over hero's arriving
  range. No wider order is asserted, because preflop strength is not totally ordered.
- The aggregate gate is **re-measured over the 51 before it is frozen**, and the phase halts rather
  than ship a gate it has not seen pass. Over the retired 5,626 no form passed: suited-versus-offsuit
  scored the wrong index mapping as the better one, 2,007 nodes against 818, and a gate preferring a
  transposed mapping is worse than none. It did not ship in the first cutover
  (`PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP`) and is owed again here.
- The per-cell count, its worst cases and their bands are published for a human, gated by nothing.
  Rank-dominance is **retaken on the re-sourced chart**: the first cutover found 111 inversions across
  42 of 86 spots, where a spot-check of the small blind's grid under the new config found three
  single-cell dips in 169. `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` covers it.
- The orderings the export was gated on hold: later position opens wider among the four non-blind
  positions, and the big blind defends more against whoever opens wider. **The first half is checked
  against the export, not the artifact, which holds zero non-blind opening ranges** - it cannot
  violate that clause, so a test asserting it over the artifact is vacuous like the sizing schema.
  The second half is checkable over the artifact and is where the gate belongs.
- **An ordering is not a level.** Both orderings hold under the `static` default phase 10 rejected at
  a 99.71 percent big-blind defence, so the defence level per opener is re-measured, printed against
  the expectations file, and read by a human: `STATIC-REALIZATION-UNMEASURED-IN-SINGLE-RAISED-POTS`.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` is accepted and stated on the source card per decision 3,
  in poker terms with its measurement, **retaken on the re-sourced solve**; unnamed it would make the
  closing measurement unfalsifiable. The multiway defect is stated there too, with the excluded node
  count, so a reader can tell the absence is a decision.
- **`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT` is re-measured rather than assumed to have moved,
  and it did not.** The flat band is 19.63 to 22.44 percent against openers 6.07 to 28.09 percent
  wide. Removing the jam did not push value into the three-bet: call moves -0.91 to -2.29 points and
  the three-bet -0.20 to +1.66. The entry stays open and the report prints the band.

### The closing measurement
- The prediction is written into the decision list before the measurement runs, **per opener and with
  a magnitude band** - a quarter to one times that opener's defence delta - with the deltas
  **recomputed from the re-sourced export**, since decision 9's ruled bands were fixed on the
  superseded one. A sign-only prediction cannot answer this phase's question: five points of defence
  is about 60 combos of 1,326, so any nonzero movement confirms it while leaving the gap intact. It
  covers price and says which way - the small-blind open reprices from 3.5bb to 2.5bb.
- **The permissive agreement rate is never reported alone, because on this corpus it rewards an
  unconverged chart.** Agreement means nonzero weight on the observed action, so a cell with every
  action nonzero cannot disagree with anything. Over the 51 shared spots the superseded chart holds
  2.209 nonzero actions per cell and is 21.0 percent pure, 1,669 of 3,985 cells offering all three;
  the re-sourced chart holds 1.323 and is 73.0 percent pure. So the permissive rate **falls** -
  Pluribus 94.4 to 70.4, humans 89.3 to 73.1 - while the strict sampled-action rate barely moves,
  70.8 to 66.2 and 69.8 to 68.5. The report publishes the strict rate and the purity statistic
  **beside** the permissive one and states that the fall is what a converged chart looks like, not a
  regression; printing the fall alone states the reverse of the truth.
  `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`.
- The report names all three candidate explanations for a residual gap - rake, price, and realization
  underpricing position - saying which it separates and which it cannot; two survive uncontrolled.
- The retained sample and refusal rate are reported beside every agreement rate, with the definitions
  that make one readable: agreement means nonzero weight, and real players are not an oracle.
- **The refusal rate is reported against a named baseline and split by cause**, so a multiway refusal
  reads apart from a limp or an unmatched key. The baseline is the retired chart, of whose 36 spots
  **21 stay covered** - re-measured on the re-sourced artifact, unchanged from the 86 - so the rate
  must **rise** on the 15 it does not cover, being the 14 the predicate drops plus the limped pot, and
  nowhere else. **A rise outside those 15 is a defect, not the cost of this ruling.** The report also
  bounds what the chart answers at all - six-handed, 100bb, symmetric stacks, no straddle, no ante,
  one opening price, heads-up only - so no rate reads as a grade on preflop play.
- **The re-source's own coverage cost is reported separately from the cutover's.** Against the
  superseded 86 the re-sourced chart refuses 1 more Pluribus decision of 502 and 9 more human
  decisions of 2,546; the remaining refusals are the multiway ruling's and predate this re-solve.
  Conflating the two would charge the re-source for a cost it did not incur.
- The refusal inventory is republished and its movement stated by reason rather than as one total,
  over the closed vocabulary `lookup.py` defines. The phase publishes its own count of decision
  points facing a limp with the definition it counted by, because the figure in
  `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry one.
- Where the derived and retired charts both answer the same corpus decision, the report says how
  often they disagree and in which direction, reading the retired chart from git history.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code: the node census with reasons, one
  cell traced from export node to artifact row, the two dominance relations, the two orderings, the
  chart against the GTO Wizard expectations, the surviving jams with AA's weight at each, and the
  corpus figures before and after. At least one number is recomputable by hand from a committed file,
  and the audit packet says which and how.
- The report generator validates its own figures and exits non-zero when they do not hold: the node
  census, the artifact's spot count against the walk's, the dominance relations, and the
  old-versus-new disagreement count. The rest is prose and the audit packet says so.
- Both new command IDs are declared here, registered in `COMMANDS` in `scripts/run_verify.py`, and
  carry a mutation canary authored before the implementation, with `check_gate_bite` proving each
  bites. One proves a wrong artifact fails the gate, not merely a wrong report; one widens the
  predicate to admit a multiway node, which nothing else notices.
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`,
  the audit packet carries plain-language pass/fail evidence, and deferred work is in `backlog.yml`.

### The backlog entries this phase settles
Each is closed, restated with a measurement, or moved forward with a reason; the reasoning lives in
`backlog.yml` rather than here.
- `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`: recompute its 59.5 and 60.8 percent on the sample the new
  chart retains, and restate against the strict rate too, since
  `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART` shows the permissive rate cannot carry it alone.
- `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`: restated with the excluded node count and the scope
  of the fix. It is why the phase commits 51 and the route by which the rest return; the roadmap owes
  it a slot this phase does not assign.
- `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` is **reopened**, having closed on ship-as-solved against a
  config that has since changed. `CHART-HERO-MUST-NEVER-LIMP` closes on the schema rule above.
- `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`: restated with what
  `add_allin: false` did and did not fix. The model still prices the all-in terminal exactly and every
  named raise through a model; only the misplaced jam is gone.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` closes on one of its three dispositions;
  `CHART-CANNOT-ANSWER-A-LIMPED-POT` is restated with the measured cost and its definition.
- `CHART-COVERAGE-EXPANSION`, `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` and
  `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` are restated rather than closed: the first two are now
  mostly blocked on GTOpen, and the third must not keep a headroom argument nothing rests on.
- `BLIND-STRUCTURE-VARIANTS` and `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` both want a
  declared blind structure on the artifact. This phase either writes it or records why it waits, by id.
- Every other entry reading `phase: "14"`, and every entry this phase's stages filed under a subject
  area instead - which a sweep scoped by phase cannot see. The eleven the first cutover's reviews
  filed are included, and the three about the export are re-measured rather than assumed to have moved.

## Required reports
- `reports/active/latest_derived_chart_report.txt`

## Required command IDs
- `pytest_derived_chart`
- `generate_derived_chart_report`

## Human vetting packet requirements
- Plain-language summary of what changed, including why the phase was re-sourced and restarted, and
  a pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports; known limitations and deferred items.
- The closing measurement with what it does not establish in the same paragraph as what it does, and
  the permissive agreement rate never stated without the strict rate beside it.
- The selection rule in poker terms, with what the bot now refuses that it used to answer and what it
  answers that it used to refuse - including why the multiway half is not committed, checkably: price
  offered, equity the model assigns, equity the hand has, fold produced.
- Which committed spots inherit the pricing defect anyway, named individually with the flat-call
  frequencies as evidence. No packet may claim the committed set is priced exactly.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success, infer missing strategy, chart or
  hand-history behavior, or change this contract during implementation mode.
- Do not hand-edit the committed artifact, the sizing table, or the expectations file: each is
  derived or external, and a hand edit is a number with no origin.
- Do not fill a cell the selection rule excluded, by interpolation, neighbouring cell or heuristic.
- Do not choose the selection rule to fit the byte limit and then justify it in poker terms, and do
  not widen the predicate to recover coverage or raise an agreement rate. The multiway spots are
  excluded because the source misprices them, and a rate is not a reason to commit them.
- Do not narrow the corpus sample to improve an agreement rate, do not pool the two populations, and
  do not read a residual disagreement as a chart defect while price and realization are uncontrolled.
- Do not patch `RULED_CONFIG` at runtime for anything that writes to the repo. `config_errors`
  refusing an export built from an unruled config is the check working, not an obstacle.

## Regression expectations
- Previously completed phase gates remain verifiable, generated human docs remain current, and
  file-size and scope checks continue to pass.
- Every frozen test of a completed phase that asserts against the chart's contents is migrated in
  the same task that changes those contents, at stage 4 and before the freeze. Phases 11 and 12
  each deferred this and each paid a separate repair task.
- The self-play simulator's figures are expected to move, because the ranges moved and because the
  bot now refuses the multiway spots it used to answer. A moved number is not a regression, and the
  report says which moved and why rather than pinning the old value.
