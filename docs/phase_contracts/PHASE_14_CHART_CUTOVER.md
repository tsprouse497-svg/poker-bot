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
Wizard export of a raked game. Phase 10 captured a GTOpen solve of the game this bot is being
trained for - six-handed, 100bb, rake-free - and Taylor read its range grids and judged it sound.
That solve has never been played from. This phase derives the artifact from it and deletes the
old one.

The phase commits the ranges. Every phase after it is measured against what is committed here,
which is why `verification/loop_policy.yml` gives it `auto_advance: false` and why more of its
decision list is `frozen-into-data` than any phase since 10.

**The phase converts a subset of the export, and choosing the subset was its central decision.**
Two independent reasons, both measured. The export holds 38,828 action nodes, and committing them
as chart spots is 272 MiB at the retired chart's own 7,346 bytes per spot or 131 MiB compacted,
against a 20 MiB cap on `data/artifacts` that phase 10 set as a halt rather than a number to
raise - about 2,267 spots of headroom, or 8,650 once each spot is filtered to hero's arriving
range. And the deep nodes should not be committed even if they fit: the solve target is a gap
summed over the whole tree, so it constrains nothing where mass is negligible. The one deep node
the export publishes shows it - the hijack facing a lojack four-bet to 22.5 folds JJ 97 percent
and TT, 99 and KJs outright while calling 76s outright, at 64 to 100 percent arriving reach - and
the two dominance relations separate the shallow tree from that one node sharply under every
tolerance tried. The export is clean where a human read it and unconverged where he did not, and
phase 10 committed the whole tree so that this phase could choose.

**Ruled by Taylor on 2026-08-23: keep a node when at least 2 percent of hero's range arrives
there.** 5,626 spots and 10.3 MiB against a 15.9 MiB budget as measured on the current export;
decision 1 records that the threshold is the ruling and the count is not, since four other
rulings move it.

Four things arrive ruled and are not reopened. Limps left the solve at phase 10's human gate, on
the measurement that limps are 87 percent of the tree and that hero never limps, so the committed
export is `limp: false` and every count here is a no-limp count - the roadmap's 1,691 spots and 12
MB were the limps-included estimate and are superseded. The solve is rake-free, which matches the
rake-free corpus and removes one of the explanations phase 08 offered for the calling gap. Phase
12's ruling 8 stands: opponent prices abstract to the solved price inside the lookup, and no
second solved opening price is added. And the export is not graded against GTO Wizard, because a
threshold over the gap between two programs measures two products.

What this phase does not do: it does not change the spot key grammar, it adds no depth or table
size, and it does not touch `data/samples/**`. The corpus is evidence and a phase does not get to
edit the thing it is measured by.

**One re-solve is permitted, at the ruled config and nothing else.** Taylor ruled decision 2 on
2026-08-24 by re-solving rather than by hand-editing or accepting the one non-monotone cell the
shallow tree carries: the committed solve stopped at 300 iterations against a 2,000 cap because
its target is a gap summed over the whole tree, and marginal hands converge last. So the phase may
re-run the same six-handed, 100bb, 2.5bb-open, no-limp, rake-free config at a tighter gap. It may
not add an opening price, add limps, add a depth or change a table size; those remain
phase-10-shaped work. What the re-solve owes is in the criteria below, because a new export does
not inherit the old one's proofs.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not re-solve at a second opening price, with limps, at another depth, or at another table
  size. All are phase-10-shaped work with their own human verdict. The one permitted re-solve is
  the ruled config at a tighter gap, and its purpose is to settle decision 2 rather than to widen
  coverage.
- Do not change the spot key grammar. Phase 12 set it, re-keying re-seeds every mixed cell
  (`RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`), and paying that twice buys one result.
- Do not rederive `data/artifacts/preflop/expectations/six_max_nl25_100bb.json` from the export. Its
  own notes call it "the only numbers in this phase that this repo did not produce", which is what
  catches a uniformly wrong range; a reference regenerated from what it checks cannot fail.

## Acceptance criteria

### Selecting what gets committed
- The committed spots are exactly those the ruled predicate selects, and the predicate is the
  ruling rather than the spot count it produced: if the count no longer fits under the cap once the
  schema fields and the re-solve land, that is a halt and a return to the decision list, not a
  quietly tightened floor. A rule adjusted to make the file fit is a rule the poker did not pick.
- Every node in the export is accounted for by the walk in exactly one of three buckets:
  committed, excluded by the selection rule, or inexpressible in the spot vocabulary. The three
  counts sum to the node count published in the export's source card. The exclusion reason and the
  inexpressibility reason each come from a closed vocabulary the phase's tests enumerate, so a
  node the converter merely failed to handle cannot be filed as a property of the grammar.
- A node the selection rule excludes is a lookup miss at runtime, refused with a code, and never
  answered from a neighbouring cell. The bot refusing a spot it has no trained ranges for is the
  whole point of the exclusion.
- The committed artifact carries, per cell, enough of the arriving reach for a later reader to
  tell a cell the solver trained from one it barely visited, or the phase states why the schema
  cannot and files it. Today the schema has no such field, and a refusal and an untrained cell are
  the same information the chart cannot express.

### What the permitted re-solve owes
- The re-solved export replaces the committed one and re-establishes **every** property its source
  card claims, because none is inherited. Enumerated from
  `gtopen_six_max_100bb_rakefree.source.json` rather than remembered: the two-process determinism
  proof at zero divergence and zero shape differences; the walk, meaning every action node asked a
  second time by its own recorded action sequence and returning the same node with zero
  mismatches; the node-count reconciliation between the export and the solver's own count; a
  restamped `export_sha256` and saved-solve checksum; and the recomputed `size` block.
- The `config_posted` block is byte-identical to the current one apart from the solve target, and
  the criterion asserts that rather than trusting it. That is what makes this a re-solve of the
  ruled game rather than a new one, and it is the only thing standing between decision 2's ruling
  and a second opening price arriving by accident.
- `model` stays `realization=calibrated`. Decision 3's ruling records a measured realization bias
  onto the artifact's source card, and that statement is about this model; a different one makes
  the recorded bias false rather than fixed.
- The two gated orderings are re-asserted against the new export: later position opens wider among
  the four non-blind positions, and the big blind defends more against whoever opens wider.
- The report publishes what moved between the two solves - the cells whose frequency changed by
  more than the monotonicity tolerance, and the eleven aggregate frequencies before and after. If
  anything beyond the marginal cells moved, that is a human read of the range grids rather than a
  number in a report, and the phase says so rather than proceeding.
- The one violation the monotonicity rule names in the shallow tree is expected to disappear. If
  it survives the tighter gap, decision 2's ruling says it is the solver's considered answer and
  ships as solved, with that outcome recorded rather than reopened.
- The source card records both solves: the iteration count, the target and achieved gap, and the
  wall clock for each. A reader must be able to see that the committed ranges came from the second.

### The derived artifact
- The artifact is derived from `data/artifacts/preflop/exports/` by a committed script and is
  reproducible from it: rerunning the conversion over the committed export reproduces the
  committed artifact byte for byte, and a `--check` mode fails the gate when it does not.
- The retired `six_max_nl25_100bb.json` is **deleted**, and a test asserts it is absent from
  `data/artifacts/preflop/`. Absence of a duplicate-key collision is not retirement and must not
  be treated as it: the retired chart three-bets to 8, 11 and 13.5 and opens the small blind to
  3.5 while the export three-bets uniformly to 7.5 and opens to 2.5, so 17 of its 36 keys do not
  collide with anything the new artifact declares. `PreflopChartLibrary` would build clean with
  both loaded and the bot would answer every three-bet spot and every small-blind open from raked
  GTO Wizard ranges while believing it plays the rake-free solve.
- A test proves the converter reads its raise sizes from the export's own action labels rather
  than from constants: the same converter run over a synthetic export whose labels are perturbed
  produces keys carrying the perturbed sizes. The property is otherwise unfalsifiable, because the
  solved config has exactly one opening size and one raise multiplier and a hardcoded converter
  produces a byte-identical artifact.
- The sizing table is rederived from the export in the same run as the artifact. The expectations
  file is not - see the Non-goal above - and the report prints the derived chart against it for a
  reader, gated by nothing, which is what phase 10's decision 6 already ruled for the export.

### What the ranges must not have become
- No spot with an empty `action_sequence` carries a call weight, enforced by the artifact schema
  rather than measured over one committed file. `CHART-HERO-MUST-NEVER-LIMP` asks for exactly
  this and says why: the export enforces it by construction, "but that is a property of the data
  rather than a rule", and phase 14 owns the schema. The retired chart limps 13.73 percent from
  the small blind, combo-weighted over 1,326 combos, across 103 hand classes carrying a nonzero
  call weight.
- The committed cells are monotone under the two relations that hold in every preflop spot, at the
  tolerance decision 10 rules: a higher pair played at least as often as the pair one rank below,
  and a suited hand at least as often as the offsuit hand of the same two ranks, with a gap over one
  percentage point counting. No wider order is asserted, because preflop strength is not totally
  ordered - plain card-rank dominance gives 61 to 121 violations per node over the published grids
  and its top hits are correct poker, the lojack opening 76s always and T6s never.
- The one violation that rule finds in the shallow tree today is settled by the permitted re-solve
  rather than declared: the lojack opens 44 at 72.81 percent while opening 33 at 99.88 and 22 at
  99.92 (`SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`). If it survives a tighter gap, decision 2 rules
  that it is the solver's considered answer and ships as solved with that recorded; nobody
  hand-edits the cell in either branch.
- The orderings the export was gated on hold in the derived artifact: later position opens wider
  among the four non-blind positions, and the big blind defends more against whoever opens wider.
  These survive any rake basis and any solver, which is why they transfer.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` is accepted and stated on the committed artifact's
  source card, which is decision 3's ruling, in poker terms with its measurement: the big blind
  folds 50.98 percent facing a 2.5bb small-blind open from a 54 percent range, closing with 1.5 to
  win 3.5 and needing 30 percent in position. Leaving it unnamed would make the closing measurement
  unfalsifiable, since the big blind holds 58 of the 89 human call disagreements.

### The closing measurement
- The prediction is written into the decision list before the measurement runs, **per opener and
  with a magnitude band** - ruled at a quarter to one times that opener's defence delta - and the
  deltas are recomputed from the re-solved export rather than carried over. A directional
  prediction cannot answer the question this phase is asked: defence widens against four openers
  and comes back 2.67 points *tighter* against the button, which generates the most big-blind
  defending decisions in any six-max sample, so an aggregate "defence widens" is falsified in
  advance on its largest component. And five points of extra defence is about 60 combos of 1,326
  against a 39-point call-agreement gap, so any nonzero movement confirms a sign-only prediction
  while leaving the gap intact.
- The prediction covers price too, and says which way. The cutover reprices hero's own small-blind
  open from 3.5bb to 2.5bb, so the big-blind-facing-small-blind family moves from a 3.5-solved
  answer to a 2.5-solved one against a corpus median open of 2.25, and "the price-tracking part
  will not move" is false by construction for that family.
- The report names all three candidate explanations for any residual gap - rake, price, and the
  realization model's underpricing of position - and says which this measurement can separate and
  which it cannot. Two of the three survive the cutover uncontrolled. It states that price is
  uncontrolled and publishes the corpus opening-price distribution rather than only the
  qualification, since how much of the sample sits at each price is what quantifies the cost of
  phase 12's ruling 8.
- The retained sample and the refusal rate are reported beside every agreement rate, and the two
  definitions that make a rate readable are carried into the new report rather than dropped: that
  agreement means the chart gives the observed action nonzero weight rather than that a draw
  matched, and that real players are not an oracle. The stricter sampled-action match rate is
  reported beside the agreement rate for both populations.
- The report bounds what the chart answers at all: six-handed, 100bb, symmetric stacks, no
  straddle, no ante, one solved opening price. A reader must not be able to take an agreement rate
  as a grade on preflop play when it is a grade on one table configuration.
- The refusal inventory is republished and its movement stated by reason rather than as one
  total, over the closed vocabulary `lookup.py` already defines. The phase publishes its own count
  of decision points facing a limp, with the definition it counted by, because the figure quoted
  in `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry one.
- Where the derived chart and the retired chart both answer the same corpus decision, the report
  says how often they disagree and in which direction. The retired chart is read from git history
  for this comparison, since the criterion above deletes it from the tree.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code: the three-way node census with
  reasons, one converted cell traced from an export node to its artifact row, the two dominance
  relations, the two orderings, the derived chart against the GTO Wizard expectations, and the
  corpus figures before and after with their refusal rates. At least one number in it is
  recomputable by hand from a committed file, and the audit packet says which and how.
- The report generator validates its own figures and exits non-zero when they do not hold. The
  contract requires this of the node census, the artifact's own spot count against the walk's, the
  dominance relations, and the old-versus-new disagreement count. The remaining report
  requirements are prose and the audit packet says so, so that stage 4 knows what a canary can
  reach and what it cannot.
- Both new command IDs are declared here, registered in `COMMANDS` in `scripts/run_verify.py`,
  and pass through `scripts/run_verify.py`.
- Both new command IDs carry a mutation canary in `verification/mutations.yml`, authored before
  the implementation, and `check_gate_bite` proves each bites. At least one canary must prove that
  a wrong artifact, not merely a wrong report, fails the gate.
- `data/artifacts` stays inside its 20 MB limit in `scripts/check_file_sizes.py`. The tree holds
  4.4 MB today, of which 4.0 MB is the gzipped export itself, and deleting the retired chart frees
  0.25 MB. Exceeding the limit is a halt and a decision, not a number to raise.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.
- Required command IDs pass through `scripts/run_verify.py`.

### The backlog entries this phase settles
- `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` closes or is restated with what the rake-free chart
  measured. Calls agree 59.5 percent for Pluribus on 37 decisions and 60.8 percent for humans on
  227, against 96.3 and 93.6 percent headlines dominated by the 72 percent of decisions that are
  folds.
- `CHART-HERO-MUST-NEVER-LIMP` closes on the schema rule above, not on a measurement.
- `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` closes on one of its two named remedies.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` closes on one of its three named dispositions.
- `CHART-CANNOT-ANSWER-A-LIMPED-POT` is restated, not closed, with the measured cost and the
  definition behind it.
- `CHART-COVERAGE-EXPANSION` and `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` are settled against
  what the cutover covered, by id.
- `BLIND-STRUCTURE-VARIANTS` and `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` both ask
  for a declared blind structure on the artifact, and this is the one phase that rewrites the
  artifact. The phase either does it or records why the schema change waits, by id.
- Every other entry reading `phase: "14"` is closed, restated with a measurement, or moved forward
  with a reason. Most need `src/poker_training_bot/**`, which this phase opens only at stage 6 and
  only for the conversion, so "moved forward" is expected for them and expected is not silent.

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
- The closing measurement stated with what it does not establish, in the same paragraph as what
  it does.
- The selection rule, in poker terms, with what the bot now refuses that it used to answer and
  what it answers that it used to refuse.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not change this contract during implementation mode.
- Do not hand-edit the committed artifact, the sizing table, or the expectations file. Every one
  of them is derived or external, and a hand edit is a number with no origin.
- Do not fill a cell the selection rule excluded, by interpolation, by a neighbouring cell, or by
  a heuristic. An excluded spot is a lookup miss, which is honest.
- Do not choose the selection rule to fit the byte limit and then justify it in poker terms.
- Do not narrow the corpus sample to improve an agreement rate, and do not pool the two
  populations. Pluribus and the human professionals are different players.
- Do not read a residual disagreement as a defect in the chart while price and the realization
  model are both uncontrolled.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- Every frozen test of a completed phase that asserts against the chart's contents is migrated in
  the same task that changes those contents, at stage 4 and before the freeze, rather than
  repaired afterwards. Phases 11 and 12 each deferred this and each paid a separate repair task.
- The self-play simulator's figures are expected to move, because the ranges moved. A moved number
  here is not a regression, and the report says which moved and why rather than pinning the old
  value.
