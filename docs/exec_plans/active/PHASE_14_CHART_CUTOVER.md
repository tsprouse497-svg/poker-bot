# ExecPlan: Phase 14, Chart Cutover

Contract: `docs/phase_contracts/PHASE_14_CHART_CUTOVER.md`
Lane: worktree `~/projects/poker-bot-worktrees/phase-14`, branch `phase/14-chart-cutover`,
opened from `main` at `28e302d`.
Loop pointer: `verification/loop_runs/14.yml`. Driver: `uv run python scripts/loop_stage.py --phase 14`.

## Objective

Replace the committed 36-spot chart, which was derived from a GTO Wizard export of a raked
game, with one derived from the GTOpen solve phase 10 captured and a human verified. Then rerun
the public-corpus comparison against it and say what the result does and does not establish
about v1's calling gap.

The phase commits data the bot plays from. That is what makes it different from the three
before it: phases 11, 12 and 13 changed what the bot is told and left the ranges alone, and a
wrong range here becomes the reference every later phase is measured against.
`verification/loop_policy.yml` has it `auto_advance: false` for that reason.

## The restart, 2026-08-30

The phase reached stage 6 and was sent back to stage 1. What follows is why, so a fresh reader does
not mistake the earlier sections for the current specification.

Two independent stage-6 reviewers, one mechanical and one on the poker, found that the chart the
build committed stacks off 100 big blinds preflop with a range inverted against hand strength.
At `t6/d100/BTN/BTN:raise@2.5,SB:raise@7.5` aces never jam and 44 jams at 1.0; at
`t6/d100/BB/BTN:raise@2.5`, the second-busiest spot in the chart, aces three-bet to 7.5 and never
jam while AKo jams 0.66 and 44 jams 0.88. Across the 36 spots where any hand can jam, aces jam
0.000 at five spots where 44 jams up to 0.979, and those five arrive in 24.0 percent of hands.
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-06-build.md` carries the full
measurement and is the record of what the reviews found.

The cause is the solve config rather than anything the phase wrote. `add_allin: true` pushes a
full-stack jam onto the raise menu at every node where a raise is legal, with no reference to the
pot, so the big blind can shove 100 to win 4. Running the full 2,000-iteration budget with the flag
still on does not repair it: at 10,000 iterations the bad cell is bit-identical, so it is structural
and not noise. With the flag off the defect is gone and the solve converges roughly forty times
better.

**Taylor ruled on 2026-08-30 to re-source with `add_allin: false` and restart the phase.** The two
constants that carry it, `RULED_CONFIG["add_allin"]` and `SOLVE_TARGET_GAP_BB`, are both
frozen-into-data, so this is a `contract-update` task rather than implementation work.

The superseded stage-6 build is committed rather than discarded, at `a386c77`, on Taylor's ruling.
It is real work and the only record of the two reviews that caught the defect. Its commit message
says it is evidence rather than a base to build on.

**The contract is rewritten rather than amended.** It sits at exactly 300 of the 300 lines
`check_file_sizes.py` allows a contract, so no amendment of any length fits, and about 27 of its
lines carry figures the new source falsifies. Its dormant "What a re-solve owes, if one is run"
section becomes binding, because "no re-solve is run" stops being true. AGENTS.md's remedy for a
contract at the cap is a rewrite that folds its amendments into the criteria they amend; Taylor
ruled on 2026-08-30 that this task perform it. The cap is not raised.

The loop pointer was hand-edited from stage 6 back to stage 1 in `verification/loop_runs/14.yml`,
because the driver has no reverse gear. `stage_base` moves to `a386c77` so the stage-1 review sees
exactly the contract-update diff and nothing of the build behind it.

Two things the restart does not change. The multiway pricing defect stands: only spots with at most
two live players are committed, because the source misprices multiway pots, and that is why the
chart holds so few opening ranges. And `B3`, the rank-dominance inversions, is carried forward as a
measurement to retake rather than as a defect the ruling repairs.

## Halted, 2026-08-30

- Paused: phase 14 is halted at stage 1 by Taylor's ruling of 2026-08-30, pending a fix to GTOpen's
  calibrated realization table. The re-source with `add_allin: false` did what it was ruled to do -
  the jam inversion is gone and convergence improved roughly fortyfold - but two independent stage-1
  reviews found the chart still folds JJ, TT, 99 and 88 outright while calling 76s and 87s at
  four-bet nodes, shows no improvement in rank dominance (54 inversions against 52), and five-bet
  jams 87s where AK never does. The cause is `class_base` in `cache/realization_fit.json`, which
  rates 76s above KK, QQ, JJ, TT and 99 and 22 above every pair through JJ; the chart is a correct
  solve of a wrong payoff function. `REALIZATION-FIT-TABLE-IS-NON-MONOTONE-IN-HAND-STRENGTH` carries
  the diagnosis, decision 16 the ruling, and the stage-1 review note the measurements.
- The artifact is withheld, not the machinery. The derivation pipeline is proven end-to-end on real
  solver output and re-runs in about four minutes against a corrected source: census, schema,
  provenance, sizing table, refusal path and determinism all hold. What resumes this lane is a
  source, not a rebuild.
- Updated 2026-08-31. A controlled experiment now backs the halt's causal claim and corrects its
  diagnosis: changing only `realization` from calibrated to static, same 38,828-node tree with
  `add_allin: true` and `allin_threshold: 0.67` held and comparable convergence, moves JJ at the
  four-bet node from a pure fold at 97 percent to a 37 percent continue and 76s from a pure call to
  53, and drops 87s and 76s - 21 percent - out of LJ's four-betting range in favour of A5s. So the
  class term is causal, but the fault is that a pot-type marginal with no four-bet-pot cell is
  applied undiminished at SPR 1.67, not that the 169 numbers are unordered. Round 3 of the stage-01
  review note carries the run; decision 17 asks Taylor at which stack depths the exit
  condition must hold and how tightly, after two independent review passes withdrew two earlier
  framings of that question. Ruled by Taylor on 2026-08-31: measure it - GTOpen's realization loop
  is re-run on four-bet pots and refitted, rather than its output corrected. So this lane now waits on
  a v6 source, and separately on a cause for round 2's jam-composition blocker, which the experiment
  leaves unmoved and which no option in decision 17 accounts for.
- The gate is red while halted and stays that way. `add_allin` is `False` in `RULED_CONFIG` while
  the committed export was built with `True`, so `config_errors` refuses it. Reverting the constant
  to green the gate would erase the correction this restart established. A halted lane owes no green
  gate and `main` is untouched.

## What is already settled, and must not be reopened here

Four things arrive ruled. A phase that relitigates them spends its budget on decisions that
already have answers.

- **Limps leave the solve.** Taylor narrowed roadmap ruling 3 at phase 10's human gate on a
  measurement: limps are 87 percent of the tree, and hero never limps. The committed export is
  `"limp": false`, confirmed in `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json`.
  So the roadmap's 1,691-spot and 12 MB figures are superseded - they were the limps-included
  estimate - and every count in this contract is a no-limp count. The accepted cost is 21 of
  3,048 corpus decision points staying refused, filed as `CHART-CANNOT-ANSWER-A-LIMPED-POT`.
- **Rake-free.** The solve carries `rake_pct: 0.0`, `rake_cap: 0.0`. This is what removes one of
  the two explanations phase 08 offered for the calling gap.
- **Opponent prices abstract to the solved price.** Phase 12's ruling 8, not reopened: the size
  lives in the spot key and the abstraction lives in the lookup, so no corpus decision is lost to
  a price the chart was not solved at. `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md` says in
  as many words not to reopen it and not to add a second solved opening price.
- **The export is not graded against GTO Wizard.** Phase 10 re-ruled that after Taylor ran the
  solver himself: a threshold over the gap between two programs measures two products. The
  closing verdict on the solve was a human reading range grids, and it has already happened.

## What this phase must decide, and what it must not

The judgment calls go in `reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md`
at stage 2, each declaring `frozen-into-data` or `runtime-reversible`. Stage 1's two independent
reviewers found six between them that the first draft of the contract had left implicit:

- **The selection rule, and it is the phase.** The export cannot be committed whole and should
  not be. It holds 38,828 action nodes against roughly 2,100 spots of headroom under the 20 MB
  cap, and its deep nodes are unconverged: GTOpen's target is a summed best-response gap over the
  whole tree, so a 0.01bb target constrains nothing where mass is negligible. The published
  four-bet node folds JJ 97 percent, TT and 99 and KJs outright, and calls 76s outright, at 64 to
  100 percent arriving reach. One dominance violation across the ten shallow reference nodes;
  42 at that one node. `frozen-into-data`, and it rests on reach rather than on bytes.
- **The non-monotone pair**, `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`: the lojack opens 44 at
  72.81 percent while opening 33 and 22 outright. The contract now permits only that entry's own
  two remedies, so this decision is which one.
- **The realization bias**, `REALIZATION-MODEL-UNDERPRICES-POSITION`: the big blind folds 50.98
  percent facing a 2.5bb small-blind open from a 54 percent range, needing 30 percent in
  position. Accept and record on the source card, correct with a stated adjustment, or solve
  elsewhere. It is the third candidate explanation for the calling gap and the measurement cannot
  separate it.
- **The prediction, per opener and with a magnitude band.** The aggregate version is falsified in
  advance: defence widens against four openers and comes back 2.67 points tighter against the
  button, which generates the most defending decisions in the sample.
- **Whether the artifact declares a blind structure**, which `BLIND-STRUCTURE-VARIANTS` and
  `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` both want and which is cheapest in the
  one phase that rewrites the artifact.
- **Whether cells carry arriving reach.** The schema has no field distinguishing a cell the
  solver trained from one it barely visited, which is the same information a refusal carries.

Settled by the contract rather than left to this list: the retired chart is deleted rather than
left to a duplicate-key collision, because 17 of its 36 keys do not collide - it three-bets to 8,
11 and 13.5 and opens the small blind to 3.5 where the export uses 7.5 and 2.5 - so the library
would build clean with both loaded and the bot would answer every three-bet spot from raked GTO
Wizard ranges while believing it plays the rake-free solve.

## Scope

Approved at stage 1 (`contract-update`), which is where this plan is written:

- `docs/phase_contracts/PHASE_14_CHART_CUTOVER.md`
- `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/**`
- standing scope only for `CURRENT_TASK.yml`, `phase_status.yml`, `backlog.yml`,
  `verification/loop_runs/**`, the generated docs, `docs/exec_plans/**`, `reports/active/**`

Expected at later stages, each needing its own `scope_change_log` entry when it is opened:

- stage 2: `reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md`
- stage 4: `tests/**`, `verification/mutations.yml`, `verification/freeze.lock`, and
  `scripts/run_verify.py` (command registration only). `tests/**` as a whole rather than this
  phase's own three files, because the contract's regression expectation requires every frozen
  test of a completed phase that asserts against the chart's contents to be migrated here, before
  the freeze, rather than repaired afterwards - which phases 11 and 12 each deferred and each paid
  a separate repair task for.
- stage 6: `scripts/convert_preflop_export.py` and whatever module the conversion grows into,
  the report generator this phase declares, and `data/artifacts/preflop/**` - the one stage in
  this phase's life where the committed artifact is writable
- stage 9: `reports/phase_audits/PHASE_14_CHART_CUTOVER.md`

Forbidden throughout: `AGENTS.md`, the check scripts, `data/samples/**`, and `tests/**` from
stage 5 onwards. The corpus is evidence and this phase does not get to edit it.

## Delegation Plan

- Worker lanes: L1 the GTOpen tree walk, the three-way node census, and the reach statistics the
  selection rule is ruled against; L2 the converter, from node payloads to artifact rows at the
  v2 vocabulary, plus the retirement of the old chart; L3 the sizing table rederived from the new
  source - the expectations file is external and stays put; L4 the corpus comparison rerun and
  its report; L5 the phase's own tests and canaries, authored at stage 4 before any
  implementation.
- Ownership: L1 owns the walk and the census it publishes; L2 owns
  `scripts/convert_preflop_export.py`, the artifact it writes, and the deletion of
  `six_max_nl25_100bb.json`; L3 owns the sizings file under `data/artifacts/preflop/`; L4 owns the
  closing measurement and the report generator; L5 owns `tests/**` at stage 4 only. The
  coordinator owns `CURRENT_TASK.yml`, the contract, this plan, `backlog.yml`,
  `verification/mutations.yml`, command registration in `scripts/run_verify.py`, every merge, the
  gate, and the audit packet.
- Expected outputs: each lane returns a patch confined to the files it owns, the commands it ran
  with their output, a changed-file summary, and the frozen tests it made pass or found failing.
  L1 also returns the enumeration as data rather than as prose, because every later lane's
  denominators come from it. L4 returns the measurement with its prediction stated before the
  numbers.
- Status: stages 1 to 3 were coordinator work by construction - a contract, a decision list and a
  human gate are each a single document, and splitting their authorship produces a document with
  two voices and no owner - and two independent read-only reviewers read the contract before
  stage 2 opened. Stage 4 is the first delegated stage. Four lanes ran concurrently on disjoint
  files: three authoring one new test file each, and a fourth migrating the frozen tests of
  completed phases that the cutover makes false. The coordinator kept `CURRENT_TASK.yml`, the
  command registration, `verification/mutations.yml`, this plan and the review.
- Integration order: L1 first and alone, because the census and the reach distribution are what
  the selection rule is ruled against at stage 3 and what every other lane counts against. Then
  L2, then L3 in parallel with L2 once the artifact's shape is fixed, then L4 last, because the
  closing measurement is not real until the artifact it measures is committed. The coordinator
  runs the phase's own commands after each merge and the full gate only after L4.
- Status, second contract-update (2026-08-24): coordinator work by the same argument as stages 1
  to 3 - the contract, the decision record and this plan are single documents. Two independent
  read-only reviewers ran concurrently on the finished diff before it was committed, one
  mechanical (re-measuring every count in the new text against the committed export, and checking
  the rewrite dropped no criterion the previous contract carried) and one on the poker (whether
  "at most one opponent voluntarily invested" is the right line, whether the unconverged four-bet
  continuations should ship, and whether decision 6 still makes sense on the new set).
- Status, stage 6 (2026-08-27): five lanes, run in three waves because the dependencies are
  real rather than stylistic. Wave 1 is one lane on the container - `lookup.py`'s two exclusion
  codes, `schema.py` at version 2 with `BlindStructure`, `arriving_reach_bp`, `arrival_ppb` and
  the no-limp rule, the importer that reads them, and `preflop_sizing.py` at the per-class
  shape - because every other lane imports those names and two lanes inventing them
  concurrently produces two shapes. Wave 2 is one lane on `chart_derivation.py`, the converter,
  the committed artifact, the sizing table, the deletion of the retired chart and the source
  card's restamped size block; it is one lane rather than three because the artifact, its
  sizings and its census come out of one `derive_chart` call the frozen tests read as a unit.
  Wave 3 is three lanes on disjoint files over the artifact wave 2 committed: L3C the report
  generator and its four validators, L3D the runtime price draw in `preflop_chart.py` plus
  phase 08's `comparison.py`, L3E the three other completed-phase gate commands
  (`generate_preflop_strategy_report.py`, `repo_facts.py`, `vocabulary_report.py`) and the
  re-measured `CORPUS_REFUSALS` in `table_state/measures.py`.
- Ownership at stage 6: L1 owns `solver_artifacts/{schema,lookup,importer}.py` and
  `strategy/preflop_sizing.py`; L2 owns `solver_artifacts/chart_derivation.py`,
  `scripts/convert_preflop_export.py`, `data/artifacts/preflop/**`; L3C owns
  `scripts/generate_derived_chart_report.py`; L3D owns `strategy/preflop_chart.py` and
  `data_pipeline/{comparison,comparison_report}.py`; L3E owns
  `scripts/generate_preflop_strategy_report.py`, `scripts/repo_facts.py`,
  `solver_artifacts/{vocabulary_report,vocabulary_measures}.py` and `table_state/measures.py`.
  The coordinator owns the waves, the integration, the gate, `CURRENT_TASK.yml`, this plan and
  the review notes, and writes no implementation itself.
- Operational rules given to every lane: `tests/**`, `verification/mutations.yml` and
  `verification/freeze.lock` are read-only and outside `approved_scope`; the canary `find`
  strings in `verification/mutations.yml` are a specification and are written verbatim,
  indentation included; no lane runs a bare `pytest` or two mutating invocations at once, and
  `check_scope.py` runs after anything that may apply a mutation.
- Review handoff: an independent read-only reviewer reads the stage diff against the question
  the driver prints, writes to
  `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-NN-name.md` with the three required
  headings, and never edits what it reviews. Stage 6 gets two, one mechanical and one on the
  poker, and the poker reviewer is briefed to judge the ranges rather than the code's fidelity
  to the contract - a chart that converts cleanly and plays badly passes every mechanical check
  in this repo.

- Status, restart (2026-08-30): the contract rewrite, the two constants and the decision-record
  amendments are coordinator work on the same argument stages 1 to 3 used - a contract and a
  decision record are single documents, and splitting their authorship produces a document with
  two voices and no owner. What is delegated from this stage is the measurement the rewrite is
  written against: a lane solves the re-sourced tree against the live GTOpen at `4aee435`, walks
  it, and returns the census, the chart, the action menus, the relationship to the superseded 86,
  the blind-defence comparison and the jam retest, writing nothing into the repo because
  `approved_scope` holds five paths and none of them is `data/artifacts/**`. The coordinator
  re-derives the headline figures from the lane's serialised export rather than taking them on
  report, on the stage-6 precedent that a reviewer's report is not evidence either. Independent
  read-only review of the finished contract-update diff before it is committed, as at stage 1 and
  at the 2026-08-24 contract-update.

## Slices

- [x] S1 Contract. Skeleton replaced with criteria written against the backlog entries this phase
      is assigned. Two independent reviewers, one mechanical and one on the poker, found eleven
      blockers between them and neither had seen the other's work; all are resolved in the
      contract and the two that could not be are filed. The phase's centre moved as a result,
      from converting the export to selecting from it.
- [x] S2 Decisions. Thirteen judgment calls recorded with a reversibility class before any code,
      eight of them `frozen-into-data` against phase 13's one, because this phase commits the
      ranges every later phase is measured against. The stage-2 reviewer overturned one item that
      had answered itself: the export offers a jam and no named raise at 4,257 nodes where the
      GTO Wizard source had zero, so the inherited collapse rule had been ruled against a source
      where the case never arose.
- [x] S3 Human gate. Cleared 23 to 24 August. All eight `frozen-into-data` items ruled, five
      `runtime-reversible` items proceeding on their recorded defaults. Decision 1 stands as plain
      reach-at-2-percent with no depth floor. Decision 2 went round twice, because Taylor first
      put back the hypothesis that 72.81 percent is the solver's real answer rather than an
      unfinished cell, and the ruling rests on the argument that it is not. None of the thirteen
      is reopened by any later stage.
- [ ] S4 Tests. Authored before implementation, and **held short of the freeze on two blockers**.
      Four lanes wrote three new test files and migrated thirteen frozen files of completed phases.
      Two independent reviewers, mechanical and poker, found five blockers between them and neither
      had seen the other's work; three are resolved in the tests and the canaries, and two need a
      human because they move `frozen-into-data` rulings. The poker reviewer's finding is the
      phase's centre: decision 10's monotonicity criterion cannot be satisfied at the ruled reach
      floor, and the "one violation in the shallow tree" it rests on is a measurement of the eleven
      grids the export publishes rather than of the shallow tree.
- Not paused. All three stage-4 blockers in
      `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-predicate-change-review.md` are
      resolved as of 2026-08-27. Blocker 1 was answered by `da05adf` a day after it was written;
      blocker 2 is withdrawn as a defect, with the four-bet realisation question filed against
      phase 16; blocker 3 is ruled to commit the cell as solved, and the band ruling taken earlier
      the same day was withdrawn before any implementation once the solver output was investigated.
      Stage 4's last pass is written and **halted on one blocker for Taylor**, 2026-08-27. Three
      tests in `tests/test_derived_chart.py` assert that a class the solver never trained is
      refused rather than committed - at the artifact over all 86 spots, at the table as a coded
      lookup miss, and off the strategy row at two tolerances that need nobody's ruling - plus the
      canary `a-class-that-never-arrives-is-committed-anyway`. Two independent reviewers, mechanical
      and poker, neither having seen the other's work, both reproduced the census exactly and found
      five blockers between them. Three mechanical ones are fixed: a two-sided cell bound that
      foreclosed every reach-threshold answer, a tautology, and a `mutations.yml` comment that was
      false twice over. The poker one is the halt and it refutes this pass's own first argument:
      the five near-uniform cells it called threshold hands are undertrained rows, the 100bb
      open-jam carries zero weight at every opening node so one of them is a strategy against a
      range that does not exist, and eight committed spots holding 1,031 cells have arrival
      probability exactly zero while reach flags none of them - four carry every class at full
      reach and four look like an ordinary range facing a four-bet. Arriving reach is hero's
      own range filter, not a measure of whether the solver trained the node. The open question -
      does the rule refuse on arriving reach alone, or also where the solve never trained the
      node - was put to Taylor and ruled the same day: **option one, the chart commits the
      untrained cells and refuses only the classes that never arrive**, because heuristics for
      spots with no solver output are wanted later and a spot with no output is where such a layer
      belongs. One addition was put back to him and taken, since option one as stated defeats its
      own purpose: a committed cell that was never computed is indistinguishable from one that
      was, so **the converter records each spot's arrival probability on the artifact** in parts
      per billion, beside the per-cell reach. The eight never-reached spots read zero; nothing the
      bot answers today changes. Frozen in `tests/test_chart_arrival_probability.py`, a seventh
      file in the family because two of the six are at the 700-line cap and the rest have no room,
      with the canary `every-spot-claims-its-line-is-always-played`. A third independent review of
      that file found three blockers, all fixed: a false "every one of their 169 classes reads full
      reach" in six places, which holds at four of the eight spots and which the file's own cell
      count contradicted; a canary description naming a detector that cannot see the defect; and a
      band that included one of the eight zeros. Decision 5 and the contract's artifact
      criterion both owe an amendment at the next `contract-update`.
- [ ] S5 Freeze.
- [ ] S6 Build. The walk and its census, the converter, the artifact, the retirement of the old
      chart, the sizings, the comparison rerun. The expectations file is external and is not
      rebuilt. Two things arrive owed rather than discovered: the known list in
      `stage-04-test-recut.md` under "What stage 6 owes in `src/` and `scripts/`" - four gate
      commands of completed phases crash once the artifact is rebuilt, and `table_state/measures.py`
      pins `CORPUS_REFUSALS = 290` which must be re-measured - and the arrival-probability field
      ruled on 2026-08-27, which `schema.py` and `chart_derivation.py` both have to carry.
- [ ] S7 Gate. Full `scripts/run_verify.py` plus `check_gate_bite`.
- [ ] S8 Review. Two independent reviewers, mechanical and poker.
- [ ] S9 Audit. Packet with the closing measurement and what it does not establish.
- [ ] S10 Closeout.
- [ ] S11 Advance. Policy says `auto_advance: false`, so this lane stops for Taylor here.

## Measurements this plan is written against

Taken from the committed files rather than from the roadmap, because the roadmap's own
mitigations document says its estimates do not reproduce.

- The export: `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz`, 4,094,221
  bytes, 38,828 action nodes, 105.45 bytes per node. Solved in 54.2 seconds over 300 iterations
  to an achieved gap of 0.0062bb against a 0.01bb target, and byte-identical across two runs in
  separate processes against a restarted server.
- The config solved: six-handed, 100bb, `open_raises: [2.5]`, `raise_mults: [3.0]`,
  `max_raises: 4`, `add_allin: true` at a 0.67 threshold, `ante: 0.0`, `limp: false`,
  rake-free, calibrated realization.
- The chart it replaces: `data/artifacts/preflop/six_max_nl25_100bb.json`, 264,462 bytes, 36
  spots, so 7,346 bytes per spot in the artifact format - which is what the roadmap's "7.1 KB"
  is, and it is measured off a GTO Wizard-shaped source rather than a GTOpen one.
- The directory cap: `data/artifacts` is limited to 20 MB in `scripts/check_file_sizes.py`, and
  the tree holds 4.4 MB of which 4.0 MB is the gzipped export itself. Deleting the retired chart
  frees 0.25 MB, so the budget is about 15.9 MB - roughly 2,100 spots at the retired chart's own
  rate, against 38,828 nodes.
- What committing the whole export would cost, measured three ways rather than extrapolated:
  272 MiB at the retired chart's 7,346 bytes per spot, 131 MiB at its compact-JSON rate, and 407
  MiB if every node keeps all 169 hand classes the way a GTOpen node carries them. Filtering each
  spot to hero's own arriving range, which is what the retired chart does, brings the whole export
  to 71 MiB. All four are over the cap by between 4.5x and 26x. There is no version of "commit
  the tree" that fits.
- Convergence is not uniform over that tree. The solve target is a summed best-response gap in
  big blinds, so it says nothing about a node carrying negligible mass. Over the eleven grids the
  export publishes, the two airtight dominance relations give one violation across the ten
  shallow reference nodes and 42 at the single deep four-bet node.
- The corpus today: 499 hands, 3,048 preflop decision points, 290 refusals across 159 distinct
  spots, 206 of the 290 in the two blinds. Calls agree 59.5 percent for Pluribus on 37 decisions
  and 60.8 percent for humans on 227, against a 96.3 and 93.6 percent headline dominated by the
  72 percent of decisions that are folds. The stricter sampled-action match is 89.0 and 85.3.
- The deltas the closing measurement's prediction must be built from: big-blind defence widens
  4.65 points against the lojack, 3.72 against the hijack, 2.64 against the cutoff and 6.14
  against the small blind, and comes back 2.67 points tighter against the button.

## Next Agent Bootstrap

Work only in `~/projects/poker-bot-worktrees/phase-14` on `phase/14-chart-cutover`.
Never work in `~/projects/poker-bot` or the main worktree.

Ask the driver and do only what it names, then `--advance`:

    uv run python scripts/loop_stage.py --phase 14 [--advance]

**Current state: the loop sits at stage 4 and the phase is on its second contract-update.**
Stages 1 to 3 are done and committed. Phase 14 is `active` in `phase_status.yml`. The stage-1 to
stage-4 review notes are under `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/` and the
stage-4 ones must be read before anything else, because they moved the phase's central ruling.

**The selection predicate changed twice and the tests know neither change.** Taylor superseded
decision 1 on 2026-08-24 onto the 110 heads-up spots, then superseded that on 2026-08-25 onto the
**86 spots**: keep a node when at most one opponent has voluntarily invested beyond the blinds
**and** at most two players are still live. Both clauses, conjoined - the first alone gives 110 and
the second alone gives 5,472. The first
supersession is in `stage-04-cold-call-verification.md` and in
`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` - GTOpen prices a multiway pot as the product of hero's
pairwise equities, understating true three-way equity by 10.5 points, so the big blind folds 92.6
percent closing at 4.3 to 1 three-handed. The second is in `stage-04-predicate-change-review.md`:
the approximation bites at *terminals*, so a history predicate does not select what the model prices
exactly and 24 of the 110 carry the defect. The coverage measurement the ruling was made on is in
`stage-04-eighty-six-coverage.md` and the ruling itself is at the foot of
`stage-04-disposition-options.md`.

Main was merged into this lane at `9be45bf`, bringing MAINT-26; phase 13 was already here.

**What the next implementation task owes**, once this contract-update is committed and the mode
flips back:
- Re-cut every stage-4 test that asserts 5,626, 110, the reach floor, or a multiway spot. The
  predicate, the node census counts, the exclusion vocabulary (now two reasons, not one) and the
  sizing-table numbers all moved, twice.
- State the predicate over live seats, not over the action history. The two disagree on 24 nodes and
  a test that asserts 110 is asserting the superseded rule.
- Re-measure the aggregate dominance gate over the 86 before freezing it. Over the 5,626 no
  aggregate form passed and the suited-versus-offsuit form scored the transposed mapping as better;
  the contract now requires the phase to halt rather than freeze a gate it has not seen pass.
- Add the canary the contract now requires: one that widens the predicate to admit a multiway node.
  A canary that admits a *history*-heads-up node with a multiway terminal is the sharper one, since
  that is the error the 2026-08-25 supersession corrects.
- Carry the four action menus into a test - 50 fold/call, 20 fold/call/raise/jam, 15 fold/call/jam,
  1 fold/raise/jam - because a converter that dropped an action passes every other check.

The contract and the decision record left `approved_scope` at stage 4, which is the point:
`check_scope.py` is what mechanically enforces the rule that implementation mode may not edit the
contract it is measured against. Do not reopen any of the thirteen rulings.

`check_repo_consistency` was red from stage 1 until stage 4, saying phase 14 declares
`pytest_derived_chart` and `generate_derived_chart_report` and neither is registered in
`scripts/run_verify.py`. Stage 4 registered both, which is where registration belongs: the same
check demands a registered `pytest_*` command name a real test file holding at least one test, so
it cannot land before the tests do.

**Everything below is red on purpose until stage 6.** The phase's own three test files are red
because the modules they import do not exist; the migrated tests of completed phases are red
because the artifact has not been rebuilt; eight canaries in `verification/mutations.yml` name
`find` strings the builder has not written yet, so `test_every_mutation_applies_exactly_once_to_its_file`
is red too. None of that is a defect to repair. What would be a defect is a red from a broken test
file - a syntax error, a typo, a fixture that raises - and stage 4's own check cannot see one,
because it accepts a `ModuleNotFoundError` as a legitimate red. `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`
is that gap, and phase 10 paid two separate repair tasks to it, which is why every lane at this
stage ran `ruff --no-cache` and read its own pytest output rather than trusting the driver.

Read before doing anything: this plan, then `docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md`
and `reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md`, where the config
this phase converts was ruled; then `docs/V2_RULING_MITIGATIONS.md` sections 2 and 3, which name
what this phase owes; then `scripts/convert_preflop_export.py`, which already does this
conversion from a different source and whose docstring states the three transformations that
lose information on purpose.

Six things that will bite if they are not carried forward.

1. The committed export has no limps. Any plan quoting 1,691 spots or 12 MB is quoting the
   superseded limps-included estimate.
2. The export cannot be committed whole and should not be - and as of 2026-08-24 the reason is
   neither the byte cap nor convergence but the multiway pricing. The selection rule is the phase,
   and as of 2026-08-25 it is the history clause **conjoined with** "at most two players are still
   live" - the subtree statement the 110 was missing, not a replacement for the history one. Either
   clause alone is wrong: 110 and 5,472. The byte cap no longer binds at 86 spots and any plan that
   reasons from it is reasoning from a retired premise.
3. The retired chart is deleted rather than left to a duplicate-key collision. 17 of its 36 keys
   do not collide, and every one of those is a three-bet spot or a small-blind open.
4. The closing measurement must state that price is uncontrolled, and now the realization model
   too - two of the three candidate explanations survive the cutover. It must also report the
   retained sample and the refusal rate beside the agreement rate, because an agreement rate means
   different things on 40 percent of a sample and on 95.
5. `PREFLOP_ACTIONS` in the artifact schema is `fold, check, call, raise` and the export's action
   kinds are `fold, call, raise, jam`. The jam has no home, so hero's raise offers collapse the
   way the existing converter already collapses them, and the sizes go to the sizing table.
   Decision 6 settled where the price comes from: a shove is a raise **to hero's whole stack**,
   and `build_sizings` gains an entry for every jam-only spot the filter keeps. Its 4,257 and 313
   counts are pre-supersession; over the 86 it is 15 jam-only spots and 21 offering both, against
   313 and 60.6 percent when the ruling was made. The multi-size table survives on that narrower
   ground, restated in decision 6, and 50 of the 86 offer hero no raise at all.
6. `docs/CORPUS_COMPARISON_LIMITS.md` carries a sentence saying spot keys hold no size, which
   phase 12 made false. It is out of this stage's scope and is filed as
   `CORPUS-LIMITS-DOC-STILL-SAYS-KEYS-CARRY-NO-SIZE`.

## What stage 4 froze as a specification for stage 6

Tests authored before an implementation are a specification, and so are the canaries. Both were
written against names the builder has to produce, on the phase 11, 12 and 13 precedent: a canary
written after the code can only describe what was already written, which is how phases 08, 09 and
10 each ended up with no canary for the one behaviour their phase existed to add. A `find` string
that does not occur at stage 6 is the builder having drifted, not the canary being wrong.

Five of the eight canaries target `chart_derivation.py`, one `schema.py`, and two the report
generator. Two were re-aimed at stage 4 after an independent mechanical review, and both would
otherwise have failed silently rather than loudly, which is worth recording because it is the
failure mode a canary is least able to report about itself. The jam-pricing canary named
`scripts/convert_preflop_export.py` while the frozen tests put the collapse rule in the `src/`
module, and `check_gate_bite` requires the find string to occur exactly once in the file it names,
so stage 7 would have halted on zero occurrences. The blind-structure canary replaced a line in
`PreflopArtifact.to_payload()` and would have bitten only if the derived payload happened to be
assembled through it; the one committed test that exercises `to_payload` round-trips it, so both
dumps would have carried the same wrong structure and agreed with each other.

**New module `solver_artifacts/chart_derivation.py`.** *Superseded in part on 2026-08-24: the
selection predicate is no longer a reach floor, so `REACH_FLOOR_BP = 200` and everything that reads
it are stage-4 work to be re-cut, not a design to build to.* What survives unchanged:
`node_action_sequence` walks a node's path into a `PreflopAction` sequence, taking each action's
actor from the **parent** node's `actor_pos` and dropping folds; `census(export)` returns a
`NodeCensus` whose buckets sum to the source card's own node count; and it is verified on the
committed export that all 38,828 nodes derive a valid key, 38,828 distinct, with zero collisions.
What replaces the floor is a two-clause predicate needing no threshold constant at all: at most one
non-actor seat has taken a call, raise or jam, **and** at most two seats are not yet folded. Together
they select 86. *Do not build either clause on its own: the history clause was ruled on 2026-08-24,
selects 110, and was superseded on 2026-08-25 because 24 of those 110 still reach a multiway
terminal; the subtree clause alone selects 5,472, admitting nodes reached through a cold call whose
arriving ranges the same defect already distorted.* The
reach mean stays as a *published measurement* rather than a filter, and note its definition: the
plain unweighted mean over the 169 classes, which is what reproduced 891 / 1,424 / 3,296 / 5,626 /
9,407 / 13,575 at the 20, 10, 5, 2, 1 and 0.5 percent floors. A combo-weighted reading gives 4,856
at 2 percent and is a different number for the same words.

**Reason codes in `lookup.py`**, which is decision 8's ruling that a reader meets one vocabulary
rather than two. `DERIVATION_NO_LEGAL_SPOT_KEY` stands and its bucket publishes at zero, which is a
result rather than an omission. `DERIVATION_BELOW_REACH_FLOOR` is superseded: decision 8's amendment
requires **two** exclusion codes rather than one - a node outside the selection rule, and a node the
source misprices - because one code cannot say which of the 38,742 excluded nodes come back when
GTOpen can price multiway. The two codes now genuinely differ: the 24 that the 2026-08-25 ruling
drops are outside the rule *because* the source misprices them, and 5,386 terminal-clean nodes are
outside the rule for the separate reason that they are reached through a cold call.

**Schema at version 2**, carrying `BlindStructure` (decision 4) and `arriving_reach_bp` per cell
(decision 5), plus the rule that a spot with an empty `action_sequence` may not carry a positive
`call` weight. That last one is `CHART-HERO-MUST-NEVER-LIMP`, and it closes on the schema rather
than on a measurement: the export enforces it by construction, but that is a property of the data
and this phase owns the schema.

**Paths.** The artifact becomes `data/artifacts/preflop/six_max_100bb_rakefree.json` with its
sizings alongside; `six_max_nl25_100bb.json` and its sizing table are deleted; the expectations
file and the GTO Wizard source it came from stay untouched, because a reference regenerated from
what it checks cannot fail.

**What the cutover does to coverage, measured rather than assumed.** The kept chart holds exactly
four raise prices - 2.5, 7.5, 22.5 and 100 - so none of the retired chart's 3.5, 8, 11 or 13.5
survives, which is the 17-of-36 non-collision the contract cites. *Revised 2026-08-24:* the squeeze
after an open and a cold call is no longer gained - it is the family the ruling excludes. Gained is
the big blind facing a four-bet and the rest of the heads-up three-bet and four-bet skeleton, 86
spots against the retired chart's 36 - *revised again 2026-08-25, and four of the five opening
ranges are now excluded with it, leaving only the small blind's.* The retired 36 are all heads-up by
the superseded history predicate but **only 22 of them are terminal-clean**, so 14 spots the bot
answers today are refused after the cutover and the "nothing currently answered is lost" claim dies
with the 110. Beyond those 14 the limped pot is lost too, absent from the tree because the solve is
`limp: false`, so
`t6/d100/BB/SB:call` moves from covered to refused. That is the accepted cost of phase 10's human
gate, filed as `CHART-CANNOT-ANSWER-A-LIMPED-POT`, and stage 4 migrated the tests to assert the
refusal rather than deleting the claim. So of the retired 36, **22 pass the ruled predicate but only
21 are actually covered** - `BB/SB:call` passes it and still has no node, because the tree has no limp
branch to hold one. **Spot count rises 36 to 86 and the refusal rate rises with it**, on those 15 and
on nothing else; a rise outside the 15 named spots is a defect rather than the cost of this ruling.
The 2026-08-25 note reversing the direction of this criterion is in
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-eighty-six-coverage.md`.

## What stage 6 will have to face that stage 4 could not settle

Two things are known to be waiting and neither is a reason to stop now.

**~~The byte budget is not proven.~~ Retired 2026-08-24.** This was a live risk while the phase
committed 5,626 spots. At 86 it is not: the artifact is two orders of magnitude under the 20 MiB
cap and no field the schema gains can close that gap. The contract's rule still stands - exceeding
the cap is a halt and a decision for Taylor, not a number to raise - it simply has nothing to bite
on here. Any plan that reasons from the byte budget is reasoning from a retired premise.

**The registered facts will drift.** `scripts/repo_facts.py` computes ten facts from the
committed chart and pins them into live documents, and the cutover moves several of them. That is
`quality_checks`'s fact-drift check doing its job rather than a failure, but it is check-script
territory a phase task may not reach, so it is likely to need its own maintenance task between
stage 6 commits, on the MAINT-24 and MAINT-25 precedent.

## Verification brief for the next agent: the cold-call finding

**Discharged 2026-08-24.** This brief was executed; the result is
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-cold-call-verification.md`, which
reproduced all seven claims and found the mechanism. It is kept as the record of what was asked,
and it is history rather than instruction - in particular its item 4, that both cold-call nodes
clear the 2 percent floor and are therefore committed spots, is no longer true of what this phase
commits.

Written at the stage-4 halt, 2026-08-24. Everything below is a claim to be **falsified**, not a
result to be confirmed. It was measured by the agent that also wrote the tests, which is exactly
the arrangement this repo distrusts, so recompute rather than quote.

    Work only in ~/projects/poker-bot-worktrees/phase-14 on phase/14-chart-cutover. The loop is
    halted at stage 4; do not advance it. Read reports/phase_audits/reviews/
    PHASE_14_CHART_CUTOVER/stage-04-tests.md and verification/loop_runs/14.yml first.

    Verify or refute, independently, from
    data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz. Write your own walk;
    do not import chart_derivation, which does not exist yet, and do not reuse the scratch
    scripts.

    1. At node path [1,0,0,0,0] the big blind faces a 2.5bb lojack open and defends 27.28% of
       its range, combo-weighted, with KQo calling 99.9% and AA raising to 7.5 at 99.7%.
    2. At node path [1,1,0,0,0], the same spot plus one hijack cold-call, it defends 7.44%,
       KQo folds 99.9%, AJo 99.5%, T9s 99.9%, K9s 99.2%, and AA jams 100bb at 94.3%.
    3. The price improves from needing 27.3% equity to needing 18.8%.
    4. Both nodes clear the ruled 2% reach floor, so both are committed spots.
    5. Across the 26 committed spots where the big blind faces one 2.5bb open plus one to four
       cold calls, defence never rises above 40.57% and falls as low as 4.01%, and is not
       monotone in the number of callers.

    Then answer the question the numbers cannot: is this a defect, or is it correct for a
    100bb six-max game with no rake? State which hands you would defend at node 2 and why, in
    poker terms, before you look at what the solver did.

    Two claims to check separately, because they change what the phase does rather than what it
    believes. First: `reach_bp` in the export is the ACTOR's own range survival, not the
    probability the line occurs, so decision 1's floor keeps every node where hero has not yet
    acted however rare the line. Second: no aggregate form of decision 10's two relations passes
    over all 5,626 committed nodes, and over the 351 full-reach nodes the suited-versus-offsuit
    aggregate gives 6 violations as solved against 97 with suited and offsuit transposed.

    Report findings only. Change no test, contract or artifact.
