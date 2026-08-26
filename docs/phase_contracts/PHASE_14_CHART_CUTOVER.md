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
Wizard export of a raked game. Phase 10 captured a GTOpen solve of the game this bot is trained for
- six-handed, 100bb, rake-free - and Taylor read its range grids and judged it sound. That solve has
never been played from. This phase derives the artifact from it and deletes the old one, committing
the ranges every later phase is measured against; hence `auto_advance: false` in
`verification/loop_policy.yml`.

**The phase converts a subset of the export's 38,828 action nodes, and choosing it was the central
decision.** It was first ruled on size - committing the tree is 272 MiB - so decision 1 kept a node
when at least 2 percent of hero's range arrived there, selecting 5,626 spots at 10.3 MiB. That rule
was superseded on 2026-08-24 on the poker rather than the bytes. Stage 4 measured the big blind
closing for 1.5 into 6.5 at 4.3 to 1 against an open and one cold call: it defends **7.44 percent**,
folding KQo, AJo, T9s and K9s while AA jams 100bb. An independent walk reproduced every figure and
found the cause, evidenced in the stage-4 review notes and filed as
`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`: GTOpen prices a multiway pot as the product of hero's
pairwise equities, **understating true three-way equity by 10.5 points** and by 14 on the suited
connectors whose entire value is multiway. Priced correctly the node defends 65.6. It is the core
pricing rather than a parameter, so no re-solve and no size menu touches it.

**First ruled on 2026-08-24 as the 110 heads-up spots, superseded on 2026-08-25: the cutover commits
the 86.** The first ruling kept a node when at most one opponent had voluntarily put money in beyond
the blinds, on the understanding that this selects what the model prices exactly. It does not: the
approximation bites at *terminals* and a node's strategy is backward-induced over every terminal
below it, so a subtree clause is **conjoined** rather than substituted. **Keep a node when at most
one opponent has voluntarily invested beyond the blinds *and* at most two players are still live.**
Neither half alone is the rule - the history half selects 110 and admits 24 nodes that can still go
multiway; the subtree half selects 5,472 and admits 5,386 reached through a cold call, heads-up from
here on but already priced against the degenerate calling ranges the defect produces. **86 satisfy
both**, and `SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS` files the general error.
The 24 dropped are four of the five opens, the RFI defences with seats behind and the decisions
facing a 100bb open-jam, carrying 2,232 real decisions. All 86 clear the retired 2 percent floor, so
decision 1's threshold is retired rather than retuned. Everything else is a lookup miss refused.

**The cost, measured before the ruling rather than after.** The 86 answer **563 of the corpus's 3,048
preflop decision points, 18.5 percent**; only the small blind's opening range survives. **The retired
chart is not a subset: 22 of its 36 spots survive and 14 do not**, four RFI ranges among them, so the
cutover gains 64 spots and gives up 14 the bot answers today. The ruling's second half is that the
source gets fixed: `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` is scheduled and the 24 come back.

Five things arrive ruled and are not reopened. Limps left the solve at phase 10's human gate, on the
measurement that they are 87 percent of the tree and hero never limps, so the export is `limp: false`
and every count here is a no-limp count. The solve is rake-free, which removes one of phase 08's
explanations for the calling gap. Phase 12's ruling 8 stands: opponent prices abstract to the solved
price inside the lookup, and no second opening price is added. The export is not graded against GTO
Wizard, because a threshold over the gap between two programs measures two products. And **no
re-solve is run** - decision 2 ruled ship-as-solved, and a tighter gap does not move a pricing model.
The phase also leaves the spot key grammar, the depth, the table size and `data/samples/**` alone.

## Non-goals
- Do not add PokerNow automation, browser or platform observation, runtime solver calls,
  LLM-backed poker decisions, or training UI surfaces. These are the standing V1 boundaries.
- Do not re-solve at a second opening price, with limps, at another depth, or at another table size.
  All are phase-10-shaped work with their own human verdict.
- Do not fix the multiway pricing here, and do not commit a mispriced spot with the defect recorded
  as a caveat. The fix is a change to GTOpen's `KIND_POT_SHARE` terminals with its own benchmarking:
  no config turns it off, since `realization` picks among `raw`, `static` and `calibrated` and all
  three multiply an equity already computed as a product. A source-card caveat does not reach the
  human at the table, and the rule here is that a spot with no trusted ranges is refused.
- Do not change the spot key grammar. Phase 12 set it, re-keying re-seeds every mixed cell
  (`RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`), and paying that twice buys one result.
- Do not rederive `data/artifacts/preflop/expectations/six_max_nl25_100bb.json` from the export. It
  is "the only numbers in this phase that this repo did not produce", which is what catches a
  uniformly wrong range; a reference regenerated from what it checks cannot fail.

## Acceptance criteria

### Selecting what gets committed
- The committed spots are exactly those the ruled predicate selects - at most one opponent
  voluntarily invested **and** at most two players still live - and the predicate is the ruling
  rather than the 86 it produced. Both clauses live in the converter, never a node list and never one
  clause alone: alone they give 110 and 5,472.
- Every node in the export is accounted for by the walk in exactly one of three buckets: committed,
  excluded, or inexpressible in the spot vocabulary, and the three sum to the node count the source
  card publishes. Both reasons come from a closed vocabulary the tests enumerate, so a node the
  converter merely failed to handle cannot be filed as a property of the grammar.
- The exclusion vocabulary distinguishes **two** reasons: a node outside the selection rule, and a
  node the source misprices. The second is what a later phase finds the mispriced nodes by, and one
  code loses which of them come back when GTOpen can price them.
- A node the selection rule excludes is a lookup miss at runtime, refused with a code and never
  answered from a neighbouring cell. That refusal is the point of the exclusion.
- The committed artifact carries, per cell, enough of the arriving reach for a later reader to tell a
  cell the solver trained from one it barely visited; the schema has no such field today. It earns
  that presently: 11 of the 86 are at full reach where 35 of the 110 were.
- `data/artifacts` stays inside the 20 MiB cap `check_file_sizes.py` enforces, which at 86 spots
  no longer binds. Exceeding it stays a halt and a decision, not a number to raise.

### What a re-solve owes, if one is run
Nothing here is owed unless a re-solve is run, and the phase does not run one. Decision 2 carries
the requirements in full, enumerated from `gtopen_six_max_100bb_rakefree.source.json` rather than
remembered, and all five of the properties it names are owed at their stated thresholds: the
two-process determinism proof, the walk, the node-count reconciliation, the two checksums and the
recomputed `size` block. With them: `config_posted` byte-identical apart from the solve target and
`model` pinned to `realization=calibrated`, both gated orderings re-asserted, and a report of what
moved in which **movement beyond the marginal cells is a human read of the range grids rather than
a number in a report, and the phase says so rather than proceeding.**

### The derived artifact
- The artifact is derived from `data/artifacts/preflop/exports/` by a committed script and is
  reproducible from it: rerunning the conversion reproduces the committed artifact byte for byte,
  and a `--check` mode fails the gate when it does not.
- The retired `six_max_nl25_100bb.json` is **deleted** and a test asserts it absent. Absence of a
  duplicate-key collision is not retirement: it three-bets to 8, 11 and 13.5 and opens the small
  blind to 3.5 where the export three-bets to 7.5 and opens to 2.5, so 17 of its 36 keys collide
  with nothing the new artifact declares. `PreflopChartLibrary` would build clean with both loaded,
  and the bot would answer every three-bet spot and small-blind open from raked ranges while
  believing it plays the rake-free solve.
- A test proves the converter reads its raise sizes from the export's action labels rather than from
  constants: the same converter over a synthetic export with perturbed labels produces keys carrying
  the perturbed sizes. It is otherwise unfalsifiable, because the solved config has one opening size
  and one raise multiplier, so a hardcoded converter produces the same bytes.
- The sizing table is rederived from the export in the same run as the artifact. The expectations
  file is not - see the Non-goal above - and the report prints the chart against it gated by nothing,
  per phase 10's decision 6.
- **The sizing table holds every raise size a spot offers, with the weight hero gives each.** Ruled
  by Taylor on 2026-08-24 extending decision 6, and **restated because the predicate moved the
  measurement under it**: the ruling was made on 313 spots where the shove was 60.6 percent of
  hero's aggressive volume, and over the 86 it is 21 spots, with 15 more offering a jam and no named
  raise at all. The schema stays multi-size on the ground that survives - a spot offering two prices
  is described by two prices, and the multiway family that returns later is where the 60.6 lived. The
  key does not change, because it states what hero faces rather than what hero does. Closes
  `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT`.
- A spot offering no raise carries no size and the strategy refuses rather than invent one: 50 of the
  86 offer hero only fold and call, so "every spot has a size" would price an action the chart never
  offers. A test enumerates the four menus - 50 fold/call, 20 fold/call/raise/jam, 15 fold/call/jam,
  1 fold/raise/jam - because a converter that dropped an action would pass every other check here.

### What the ranges must not have become
- No spot with an empty `action_sequence` carries a call weight, enforced by the artifact schema
  rather than measured over one file. That is what `CHART-HERO-MUST-NEVER-LIMP` asks for: the export
  enforces it by construction, "but that is a property of the data rather than a rule", and phase 14
  owns the schema. The retired chart limps 13.73 percent from the small blind across 103 classes.
- The two relations that hold in every preflop spot - a higher pair played at least as often as the
  pair one rank below, and a suited hand at least as often as the offsuit hand of the same ranks -
  are **measured per cell and gated on aggregates only**. Ruled by Taylor on 2026-08-24 against the
  small blind facing a button open, which plays 22 at 99.94 percent and 44 at 0.07: among
  near-indifferent hands the solver's split is its considered answer, and a per-cell gate would
  reject it.
- Gated instead is the same dominance over **groups**, where indifference cancels: the
  combo-weighted play frequency of each pair band and each suited row is at least that of the band
  or row below, over hero's arriving range. No wider order is asserted, because preflop strength is
  not totally ordered - card-rank dominance gives 61 to 121 violations per node and its top hits
  are correct poker, the lojack opening 76s always and T6s never.
- The aggregate gate is **re-measured over the 86 before it is frozen**, and the phase halts rather
  than ship a gate it has not seen pass. Over the retired 5,626 no form passed: suited-versus-offsuit
  flagged 2,007 nodes as solved against 818 transposed, scoring the wrong index mapping as the
  better one. A gate that prefers a transposed mapping is worse than none.
- The per-cell count, its worst cases and their bands are published for a human, gated by nothing,
  per phase 10's decision 6. That closes `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` as ship-as-solved,
  with the lojack's 44 at 72.81 percent recorded rather than re-solved away.
- The orderings the export was gated on hold in the derived artifact: later position opens wider
  among the four non-blind positions, and the big blind defends more against whoever opens wider.
  These survive any rake basis and any solver, which is why they transfer.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` is accepted and stated on the artifact's source card per
  decision 3, in poker terms with its measurement: the big blind folds 50.98 percent facing a 2.5bb
  small-blind open from a 54 percent range, closing with 1.5 to win 3.5 and needing 30 percent in
  position. Unnamed it would make the closing measurement unfalsifiable, since the big blind holds
  58 of the 89 human call disagreements. The multiway defect is stated there too, with the excluded
  node count, so a reader can tell the absence is a decision.

### The closing measurement
- The prediction is written into the decision list before the measurement runs, **per opener and
  with a magnitude band** - a quarter to one times that opener's defence delta - with the deltas
  recomputed from the export rather than carried over. A directional prediction cannot answer this
  phase's question: defence widens against four openers and comes back 2.67 points *tighter*
  against the button, which generates the most defending decisions in any six-max sample. And five
  points of defence is about 60 combos of 1,326 against a 39-point call-agreement gap, so any
  nonzero movement confirms a sign-only prediction while leaving the gap intact.
- The prediction covers price and says which way. The cutover reprices hero's small-blind open from
  3.5bb to 2.5bb against a corpus median of 2.25, so "the price-tracking part will not move" is
  false for that family.
- The report names all three candidate explanations for any residual gap - rake, price, and the
  realization model's underpricing of position - and says which this measurement separates and which
  it cannot; two of the three survive uncontrolled. It publishes the corpus opening-price
  distribution, which quantifies the cost of phase 12's ruling 8.
- The retained sample and the refusal rate are reported beside every agreement rate, with the two
  definitions that make a rate readable: agreement means the chart gives the observed action nonzero
  weight rather than that a draw matched, and real players are not an oracle. The stricter
  sampled-action match rate is reported beside it for both populations.
- **The refusal rate is reported against a named baseline and split by cause**, so a multiway refusal
  is reported apart from a limp or an unmatched key. The baseline is the retired chart, of whose 36
  spots **21 stay covered**, so the rate must **rise** on the 14 the predicate drops plus the limped
  pot and nowhere else; a rise outside those 15 is a defect, not the cost of this ruling. The report bounds what
  the chart answers at all - six-handed, 100bb, symmetric stacks, no straddle, no ante, one solved
  opening price, heads-up only - so no agreement rate reads as a grade on preflop play when it
  grades one table configuration and one branch of the tree.
- The refusal inventory is republished and its movement stated by reason rather than as one total,
  over the closed vocabulary `lookup.py` defines. The phase publishes its own count of decision
  points facing a limp with the definition it counted by, because the figure in
  `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry one.
- Where the derived and retired charts both answer the same corpus decision, the report says how
  often they disagree and in which direction, reading the retired chart from git history.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code: the node census with reasons, one
  converted cell traced from an export node to its artifact row, the two dominance relations, the
  two orderings, the chart against the GTO Wizard expectations, and the corpus figures before and
  after with their refusal rates. At least one number is recomputable by hand from a committed file,
  and the audit packet says which and how.
- The report generator validates its own figures and exits non-zero when they do not hold: the node
  census, the artifact's spot count against the walk's, the dominance relations, and the
  old-versus-new disagreement count. The rest is prose and the audit packet says so, so stage 4
  knows what a canary can reach and what it cannot.
- Both new command IDs are declared here, registered in `COMMANDS` in `scripts/run_verify.py`, and
  carry a mutation canary in `verification/mutations.yml` authored before the implementation, with
  `check_gate_bite` proving each bites. One must prove a wrong artifact, not merely a wrong report,
  fails the gate; one must widen the predicate to admit a multiway node, which nothing else notices.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.
- Required command IDs pass through `scripts/run_verify.py`.

### The backlog entries this phase settles
- `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` closes or is restated with what the rake-free chart
  measured. Its 59.5 percent for Pluribus on 37 call decisions and 60.8 percent for humans on 227
  are pre-cutover full-sample figures, and the restatement recomputes both on whatever sample the
  new chart retains rather than comparing a new rate against them.
- `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` is restated with the excluded node count and the
  scope of the fix; it is why the phase commits 86, and the 2026-08-25 ruling makes it the route by
  which the other 24 return. The roadmap owes it a phase slot, which this phase does not assign.
  `CHART-HERO-MUST-NEVER-LIMP` closes on the schema rule above, not on a measurement, and
  `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` closes on ship-as-solved per the 2026-08-24 ruling.
- `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` closes on the multi-size sizing table above,
  with the restated measurement rather than the one the ruling was made on.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` closes on one of its three named dispositions, and
  `CHART-CANNOT-ANSWER-A-LIMPED-POT` is restated with the measured cost and its definition.
- `CHART-COVERAGE-EXPANSION` and `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` are restated rather than
  closed against what the cutover covered, because the work list they name is now mostly blocked on
  GTOpen. `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` is restated too: the cap stopped binding when
  the predicate changed, and the entry must not keep a headroom argument nothing now rests on.
- `BLIND-STRUCTURE-VARIANTS` and `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` both ask
  for a declared blind structure on the artifact, and this is the one phase that rewrites it. It
  either does so or records why the schema change waits, by id.
- Every other entry reading `phase: "14"` is closed, restated with a measurement, or moved forward
  with a reason - and so is every entry this phase's own stages filed under a subject area rather
  than under `phase: "14"`, which a sweep scoped by phase cannot see.

## Required reports
- `reports/active/latest_derived_chart_report.txt`

## Required command IDs
- `pytest_derived_chart`
- `generate_derived_chart_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- The closing measurement stated with what it does not establish, in the same paragraph as what it
  does.
- The selection rule, in poker terms, with what the bot now refuses that it used to answer and what
  it answers that it used to refuse - including why the multiway half is not committed, checkably:
  the price offered, the equity the model assigns, the equity the hand has, and the fold produced.
- Which committed spots inherit the pricing defect anyway, named individually with the flat-call
  frequencies as evidence. No packet may claim the committed set is priced exactly.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not change this contract during implementation mode.
- Do not hand-edit the committed artifact, the sizing table, or the expectations file. Every one
  of them is derived or external, and a hand edit is a number with no origin.
- Do not fill a cell the selection rule excluded, by interpolation, by a neighbouring cell, or by a
  heuristic. An excluded spot is a lookup miss, which is honest.
- Do not choose the selection rule to fit the byte limit and then justify it in poker terms, and do
  not widen the predicate to recover coverage or raise an agreement rate. The multiway spots are
  excluded because the source misprices them, and a rate is not a reason to commit them.
- Do not narrow the corpus sample to improve an agreement rate, and do not pool the two populations.
  Pluribus and the human professionals are different players.
- Do not read a residual disagreement as a defect in the chart while price and the realization
  model are both uncontrolled.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- Every frozen test of a completed phase that asserts against the chart's contents is migrated in
  the same task that changes those contents, at stage 4 and before the freeze. Phases 11 and 12
  each deferred this and each paid a separate repair task.
- The self-play simulator's figures are expected to move, because the ranges moved and because the
  bot now refuses the multiway spots it used to answer. A moved number is not a regression, and the
  report says which moved and why rather than pinning the old value.
