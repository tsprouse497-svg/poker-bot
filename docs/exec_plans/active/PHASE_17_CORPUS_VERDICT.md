# ExecPlan: Phase 17 - The Corpus Verdict On The Committed Chart

Lane: `phase/17-the-corpus-verdict-on-the-committed-char`
Worktree: `/Users/taylorsprouse/projects/poker-bot-worktrees/phase-17`
Pointer: `verification/loop_runs/17.yml`
Base commit: `9bbdcf44ce5508d19d672812fbc1b3484c32c790` (main, "Merge phase 14: chart cutover")

## Objective

Gate: `pytest_corpus_verdict` and `generate_corpus_verdict_report` pass through
`scripts/run_verify.py`, `reports/active/latest_corpus_verdict_report.txt` is fresh, both commands
carry a mutation canary that `check_gate_bite` proves bites, and
`reports/phase_audits/PHASE_17_CORPUS_VERDICT.md` carries pass/fail evidence a non-coding reviewer
can follow.

What the gate is about: phase 08 measured the retired chart against 499 real hands and found calls
agreeing 59.5 percent for Pluribus and 60.8 for human professionals under a 96.3 percent headline
that folds dominate. It named three explanations for that calling gap - the solve's rake, the
opening price, and a realization model that underprices position - and could separate none of them.
Phase 14 replaced the chart with one whose preflop betting is solved rake-free; the training rake is
still carried at heads-up flop terminals, because the fit ran under `realization: "calibrated"`
(`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json`, and
`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` in `backlog.yml`). So the rake explanation is
partly removed and not eliminated, and no sentence this phase writes may say otherwise. This phase
re-runs the comparison against the committed artifact and reports which explanations survive.

This phase measures. It does not change the chart. A measurement that says the chart is wrong is a
finding for `backlog.yml` and a ruling for Taylor, per the contract's forbidden shortcuts.

## What is already committed, and what the prediction may therefore cover

The contract requires a prediction written before the measurement runs. Part of the measurement is
already on disk at the base commit, because phase 14 regenerated the gate's reports against the
committed chart. Pre-registering a figure that is already published would satisfy the criterion
without doing the work it names, so this plan states the split rather than leaving it to the author
of the decision list.

Already public at `9bbdcf4`, and to be quoted as the starting point rather than predicted:

- `reports/active/latest_spot_vocabulary_report.txt` - the before/after columns for the cutover:
  Pluribus agreement 96.3 to 90.9 percent, human agreement 93.6 to 90.1, human calls agreeing 60.8 to
  36.2 (85 of 235), refusals 290 to 139.
- `reports/active/latest_sample_comparison_report.txt` - those rates with their denominators, the
  price-band split, and the strict sampled-action rate beside the permissive one.
- `docs/BACKLOG.md`, `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART` - the permissive-versus-strict pair
  and the cell-purity statistic, 2.209 nonzero actions per cell at 21.0 percent pure against 1.323 at
  73.0 percent.

Genuinely unpublished, and therefore what the prediction pre-registers:

- Each opener's defence delta recomputed from the committed artifact, and the per-opener band a
  quarter to one times that delta.
- Cell purity over the shared spots specifically, rather than over the whole chart.
- Refusal movement split by cause against the retired-chart baseline, and each of the three coverage
  costs separately.
- The old-versus-new disagreement count and its direction.

The decision list names this section and says which of its own items are pre-registered against an
unpublished number and which are read off a committed file. A stage-8 reviewer can then check the
claim instead of taking it.

## Scope

Approved now (stage 1, `contract-update`):

- `docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md`
- `reports/phase_audits/decisions/PHASE_17_CORPUS_VERDICT_DECISIONS.md`
- `reports/phase_audits/reviews/PHASE_17_CORPUS_VERDICT/**`

Approved later, added by a dated `scope_change_log` entry at the stage that needs them:

- `tests/test_corpus_verdict.py` - stage 4 only. Stage 5 removes it again and `check_scope.py` then
  enforces that the implementer cannot write to `tests/**`.
- `src/poker_training_bot/data_pipeline/corpus_verdict.py` and
  `src/poker_training_bot/data_pipeline/corpus_verdict_report.py` - stage 6. Both named, because
  `check_scope.py` matches paths and an unnamed file is an unapproved one.
- `scripts/generate_corpus_verdict_report.py`, `scripts/run_verify.py` - stage 6.
- `reports/phase_audits/PHASE_17_CORPUS_VERDICT.md` - stage 9.

Standing scope carries `CURRENT_TASK.yml`, `verification/loop_state.yml`, `verification/loop_runs/**`,
`backlog.yml`, `phase_status.yml`, `STATUS.md`, `docs/PHASE_LEDGER.md`, `docs/BACKLOG.md`,
`docs/exec_plans/**` and `reports/active/**`.

Read-only and never approved, which is not the same as `forbidden_scope` - that is an existence rule
and these paths must exist:

- `data/artifacts/preflop/**` - the committed chart, its sizing table and its expectations file. This
  phase reads them. Changing one to move a rate is the defect the contract exists to prevent.
- `tests/**` frozen by phase 14 - read, never edited.

Genuinely forbidden, the standing `forbidden_scope` existence rule: `data/raw/**`,
`data/processed/**`.

## Delegation Plan

Complete before implementation. Lanes are worker subagents, not worktrees; this phase runs in one
worktree and the coordinator owns every commit.

- Worker lanes: A prediction (stage 3), B tests (stage 4), C measurement (stage 6), D refusals
  (stage 6), E report and gate (stage 6-7), F verdict and packet (stage 7-9). Each is one bounded
  worker subagent.
  - **A - prediction.** Recomputes each opener's defence delta from the committed artifact and writes
    the per-opener prediction with its magnitude band, a quarter to one times that opener's delta,
    plus the direction the small blind's reprice from 3.5bb to 2.5bb implies. Pre-registers only the
    unpublished figures listed above, and quotes the published ones as the starting point.
  - **B - tests.** Authors the phase's tests against the contract before any implementation exists,
    expected to fail: strict and permissive rates never reported apart, denominators present, the
    artifact checksum on every figure, refusal counts reconciling against the inventory, the four-bet
    exclusion producing no rise against the retired baseline, all three coverage costs reported
    separately, and the generator exiting non-zero on a figure that does not hold. Also the two
    canaries the contract names: one proving a wrong rate fails the gate rather than merely printing,
    one proving a refusal filed under the wrong cause is caught. A canary whose failure mode is not
    stated is the shape `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL` describes.
  - **C - measurement.** Strict sampled-action rate, permissive rate, cell purity over the shared
    spots, retained sample, and the old-versus-new disagreement count **and its direction**, read from
    the retired chart at the git pin phase 14's decision 7 names (`d046ac9`). Builds on
    `data_pipeline/comparison.py` rather than reimplementing it - see the reuse note below. Reads
    `tests/**`, never writes it.
  - **D - refusals.** The refusal split by cause against the retired-chart baseline, and the three
    coverage costs the contract requires separately: the multiway ruling's, the re-source's, and the
    four-bet withholding's. Plus this phase's own count of decision points facing a limp with the
    definition it counted by, since `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry one. The
    four-bet withholding must show no rise at all against the baseline; a rise there is a measurement
    error, not a cost.
  - **E - report and gate.** The generator, its self-validation, and the `COMMANDS` registration.
  - **F - verdict and packet.** The prose the phase exists for: the three explanations with which
    survive and which cannot be separated, the bounds paragraph (six-handed, 100bb, symmetric stacks,
    no straddle, no ante, one opening price, heads-up only, no spot facing a four-bet), and the one
    number a reader can recompute by hand from a committed file with the audit packet saying which and
    how.
- Ownership: A owns `reports/phase_audits/decisions/PHASE_17_CORPUS_VERDICT_DECISIONS.md`; B owns
  `tests/test_corpus_verdict.py` and the canaries; C and D share
  `src/poker_training_bot/data_pipeline/corpus_verdict.py` and are ordered C then D so neither writes
  behind the other; E owns `scripts/generate_corpus_verdict_report.py` and the `COMMANDS` block in
  `scripts/run_verify.py`; F owns `corpus_verdict_report.py`'s prose and
  `reports/phase_audits/PHASE_17_CORPUS_VERDICT.md`. The coordinator owns sequencing, the loop pointer,
  `backlog.yml`, and every commit. No two lanes write the same file at the same time.
- Expected outputs: A the decision list with every item marked `frozen-into-data` or
  `runtime-reversible`, the commands its numbers came from, and which items are pre-registered against
  an unpublished number; B the failing test module plus two canaries with their stated failure modes;
  C and D a module and a changed-file summary each, with their numbers; E the generator, the committed
  report at `reports/active/latest_corpus_verdict_report.txt`, and a green gate; F the verdict
  paragraphs, the bounds paragraph, and the audit packet.
- Status: A planned, B planned, C planned, D planned, E planned, F planned.
- Integration order: A, then B frozen by `scripts/freeze_tests.py`, then C, then D, then E, then F.
  The coordinator reads each lane's diff before the next starts, and a lane that lands red goes back to
  its own author rather than being patched by the next lane.
- Review handoff: two independent read-only reviewers at stage 8, neither of whom wrote the work, plus
  the per-stage reviews the driver calls for. The mechanical pass checks that the prediction's
  pre-registered items were genuinely unpublished at `9bbdcf4` and were not edited after the
  measurement ran, that no figure is quoted from another build, that the permissive rate never appears
  without the strict rate beside it, that no file under `data/artifacts/preflop/**` changed, and that
  every claim about rake carries the heads-up-flop-terminal qualification. The poker-domain pass asks
  whether the verdict is right - whether the three explanations are honestly separated, and whether a
  residual disagreement is being read as a chart defect while price and realization stay uncontrolled -
  because that is the question a green gate cannot answer. Findings are filed as blocker, non-blocker,
  or alignment item; an alignment item goes to `backlog.yml` rather than staying in the note.

Reuse note, carried into lane C's brief: `data_pipeline/comparison.py` already computes agreement and
refusals (`compare_committed_sample`), the strict rate (`sampled_action_match`) and the price bands
(`price_band_for`), and `generate_sample_comparison_report` is already a registered gate command. Two
gate-registered generators publishing agreement rates over the same corpus against the same chart from
separate code is drift with a gate around it. Lane C builds on `comparison.py`, or the phase adds a
check that the two agree; either way the choice is recorded in the decision list, not made silently.

## Slices

- [ ] S1 (stage 1). This plan committed; contract confirmed real rather than skeleton. Evidence: the
      stage-01 review note answers the driver's question with its blockers resolved, and
      `check_execplan_delegation.py` passes.
- [ ] S2 (stage 2-3). Decision list written, the prediction among it, with its pre-registered items
      separated from the figures already published at `9bbdcf4`. Evidence: the decision list committed,
      the frozen items answered by Taylor, the reversible ones proceeding on a recorded default.
- [ ] S3 (stage 4-5). Tests authored and frozen. Evidence: `freeze_tests.py` lock, and `tests/**` out
      of `approved_scope`.
- [ ] S4 (stage 6). Measurement and refusal split implemented against the frozen tests. Evidence:
      `pytest_corpus_verdict` green.
- [ ] S5 (stage 6-7). Generator, self-validation, `COMMANDS` registration, report committed. Evidence:
      `generate_corpus_verdict_report` green and the report fresh.
- [ ] S6 (stage 7-8). Full gate and `check_gate_bite`. Evidence: both canaries make the gate fail, each
      against the failure mode it was written for.
- [ ] S7 (stage 9). Verdict prose, the hand-recomputable number, backlog restatements, audit packet.
      Evidence: the four backlog entries the contract names restated or closed, and the packet's
      pass/fail checklist. Stage 10 is bookkeeping only, so no content lands there.

## Verification

- `uv run python scripts/run_verify.py` - the full derived gate.
- `pytest_corpus_verdict`, `generate_corpus_verdict_report` - this phase's command IDs, declared in
  the contract frontmatter and registered in `COMMANDS` in `scripts/run_verify.py`.
- `uv run python scripts/check_gate_bite.py` - proves each canary bites.
- `reports/active/latest_corpus_verdict_report.txt` - the required report.

## Outcome

Not filled in. This plan is at stage 1.

## Next Agent Bootstrap

State: the lane is open at stage 1 with the seed committed at `5f0d502`. Phase 17 is `active` in
`phase_status.yml` in this worktree only; `main` still reads `future` until integration.
`CURRENT_TASK.yml` is `PHASE_17_CORPUS_VERDICT`, `contract-update`, base `9bbdcf4`.

The contract at `docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md` is already real - it was written
when Taylor split phase 14 on 2026-08-31 - so stage 1 owes this plan and nothing else.

Open, and not to be invented:

- The per-opener defence deltas and the prediction bands. Phase 14's decision 9 bands are void, not
  inherited. Recompute them from the committed artifact.
- The limp count. `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry one, so this phase counts it and
  publishes the definition it counted by.
- Whether lane C extends `data_pipeline/comparison.py` or the phase asserts the two generators agree.

Settled, and not to be re-derived: the retired chart's git pin is `d046ac9`, named in phase 14's
decision 7 and verified as an ancestor of `main` by the stage-01 review.

Next command:

    cd /Users/taylorsprouse/projects/poker-bot-worktrees/phase-17
    uv run python scripts/loop_stage.py --phase 17
