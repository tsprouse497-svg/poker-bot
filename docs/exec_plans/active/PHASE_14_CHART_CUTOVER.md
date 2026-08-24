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
- Review handoff: an independent read-only reviewer reads the stage diff against the question
  the driver prints, writes to
  `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-NN-name.md` with the three required
  headings, and never edits what it reviews. Stage 6 gets two, one mechanical and one on the
  poker, and the poker reviewer is briefed to judge the ranges rather than the code's fidelity
  to the contract - a chart that converts cleanly and plays badly passes every mechanical check
  in this repo.

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
- Paused: two stage-4 blockers move `frozen-into-data` rulings and are with Taylor. First, whether
      the permitted re-solve moves ahead of the test freeze, since decision 10's two relations give
      1,938 violating nodes and 8,962 violations over the 5,626 committed nodes - 36 nodes and 541
      violations even where hero's whole range arrives - against a contract that expects one.
      Second, whether decision 6 is reopened to price hero's raise by where his aggressive weight
      actually sits, since at the 313 spots offering both a named raise and a jam the shove is 60.6
      percent of that weight, the majority at 177 of them and all of it at 35. Full evidence in
      `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-tests.md`.
- [ ] S5 Freeze.
- [ ] S6 Build. The walk and its census, the converter, the artifact, the retirement of the old
      chart, the sizings, the comparison rerun. The expectations file is external and is not
      rebuilt.
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

**Current state: stages 1 to 3 are done and committed. The loop sits at stage 4, the tests.**
`task_mode: implementation`, `base_commit` `b834bdc` (the stage-3 close), phase 14 `active` in
`phase_status.yml`. The contract carries real criteria, all thirteen judgment calls are ruled, and
the stage-1, stage-2 and stage-3 review notes are under
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/`.

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
2. The export cannot be committed whole and should not be, for two independent reasons - the byte
   cap and the fact that its deep nodes are unconverged. The selection rule is the phase.
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
   and `build_sizings` gains an entry for every one of the 4,257 jam-only spots the filter keeps.
   Committing them sizeless was the option that was rejected, and the note that a spot absent from
   the sizing table has no size stays true only because none of these will be absent.
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

**New module `solver_artifacts/chart_derivation.py`.** `REACH_FLOOR_BP = 200` is decision 1's
ruled 2 percent in basis points. `node_reach_bp` is the plain mean over the 169 hand classes of a
node's `reach_bp`; that definition is what reproduces the table decision 1 was ruled against, and
it was verified on this branch to give 891 / 1,424 / 3,296 / 5,626 / 9,407 / 13,575 nodes at the
20, 10, 5, 2, 1 and 0.5 percent floors. `node_action_sequence` walks a node's path into a
`PreflopAction` sequence, taking each action's actor from the **parent** node's `actor_pos` and
dropping folds. `census(export)` returns a `NodeCensus` of committed, excluded and inexpressible
counts summing to the source card's own node count. Verified on the committed export: all 38,828
nodes derive a valid key, 38,828 distinct, zero collisions, and the 2 percent floor keeps 5,626
of them with all five opening spots surviving.

**Reason codes in `lookup.py`**, which is decision 8's ruling that a reader meets one vocabulary
rather than two: `DERIVATION_BELOW_REACH_FLOOR`, `DERIVATION_NO_LEGAL_SPOT_KEY`, and the two
closed tuples over them. The inexpressible bucket publishes at zero, which is a result rather
than an omission.

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
survives, which is the 17-of-36 non-collision the contract cites. Gained: the big blind facing a
four-bet (14.5 percent reach) and the squeeze after an open and a cold call (full reach), both of
which the committed tests currently assert are uncovered. Lost: the limped pot, which is absent
from the tree at any floor because the solve is `limp: false`, so `t6/d100/BB/SB:call` moves from
covered to refused. That is the accepted cost of phase 10's human gate, filed as
`CHART-CANNOT-ANSWER-A-LIMPED-POT`, and stage 4 migrated the tests to assert the refusal rather
than deleting the claim.

## What stage 6 will have to face that stage 4 could not settle

Two things are known to be waiting and neither is a reason to stop now.

**The byte budget is not proven.** Decision 1's 10.3 MiB was measured without a reach field,
without a blind structure, without the jam sizings and against the 300-iteration export. The
decision record is explicit that 10.3 MiB is a floor rather than an estimate and that stage 6
measures the real figure before committing anything. If the 2 percent floor no longer fits under
15.9 MiB, the contract's own rule applies: exceeding the cap is a halt and a decision for Taylor,
not a quiet re-tightening of the floor to whatever fits. Decision 1 was ruled as a predicate
precisely so that arithmetic cannot move it.

**The registered facts will drift.** `scripts/repo_facts.py` computes ten facts from the
committed chart and pins them into live documents, and the cutover moves several of them. That is
`quality_checks`'s fact-drift check doing its job rather than a failure, but it is check-script
territory a phase task may not reach, so it is likely to need its own maintenance task between
stage 6 commits, on the MAINT-24 and MAINT-25 precedent.
