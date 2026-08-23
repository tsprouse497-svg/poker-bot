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
- stage 4: the phase's own test file, `verification/mutations.yml`, `scripts/run_verify.py`
  (command registration only)
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
- Status: none dispatched. Stage 1 is coordinator work by construction - a contract is a single
  document and splitting its authorship produces a document with two voices and no owner - and
  two independent read-only reviewers read it before stage 2 opens.
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
- [ ] S2 Decisions. Every judgment call recorded with a reversibility class before any code.
- [ ] S3 Human gate. The `frozen-into-data` calls go to Taylor. This phase commits the ranges,
      so more of its list is frozen than any phase since 10.
- [ ] S4 Tests. Authored before implementation and frozen at stage 5.
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

**Current state: stage 1 is done and committed. The loop sits at stage 2, the decision list.**
`task_mode: contract-update`, `base_commit` `28e302d`, phase 14 `active` in `phase_status.yml`.
The contract carries real criteria and the stage-1 review note is under
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/`. Stage 2 adds the decision list to
`approved_scope` under its own `scope_change_log` entry and writes it before any code.

`check_repo_consistency` is red from here until stage 4, saying phase 14 declares
`pytest_derived_chart` and `generate_derived_chart_report` and neither is registered in
`scripts/run_verify.py`. That is the expected state of a phase between declaring its commands and
registering them, not a failure to repair: registration lands at stage 4 alongside the tests those
commands run, because `check_repo_consistency` also demands a registered `pytest_*` command name a
real test file holding at least one test.

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
6. `docs/CORPUS_COMPARISON_LIMITS.md` carries a sentence saying spot keys hold no size, which
   phase 12 made false. It is out of this stage's scope and is filed as
   `CORPUS-LIMITS-DOC-STILL-SAYS-KEYS-CARRY-NO-SIZE`.
