# Stage 01 review - Phase 17, contract

Round 1, 2026-09-06. Read-only independent reviewer; wrote none of the work under review.
Diff reviewed: `docs/exec_plans/active/PHASE_17_CORPUS_VERDICT.md` (untracked new file) against
`5f0d502bd32f5e0a59fd3ac16d6f527e0c10edf2`. The contract
`docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md` is unchanged in this diff and was read as the
standard the plan is measured against.

Driver question: "Is any acceptance criterion unfalsifiable, a restatement of the phase title, or
satisfiable without doing the work it names?"

Checked and clean, so it is not repeated below: every backlog id the contract cites exists -
`PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP` (backlog.yml:3925),
`AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART` (:3966),
`A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` (:4293),
`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` (:4316), `CHART-CANNOT-ADVISE-A-FIVE-BET` (:4376),
`CHART-CANNOT-ANSWER-A-LIMPED-POT` (:821), `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` (:629),
`CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` (:720). Every path the plan names exists
(`scripts/freeze_tests.py`, `scripts/check_gate_bite.py`, `scripts/loop_stage.py`,
`src/poker_training_bot/data_pipeline/`, `data/artifacts/preflop/**`,
`src/poker_training_bot/solver_artifacts/lookup.py`). Both commit hashes resolve: base
`9bbdcf4` is "Merge phase 14: chart cutover", and phase 14 decision 7's pin `d046ac9`
(`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md:1204`) is a real ancestor of
`main`. Every phase-08 figure the plan quotes reproduces: 499 hands, 59.5, 60.8, 96.3 and 72 percent
all appear at backlog.yml:636-637. The small blind's 3.5bb to 2.5bb reprice is real - the retired
sizing table at `d046ac9:data/artifacts/preflop/sizings/six_max_nl25_100bb.json` keys
`t6/d100/BB/SB:raise@3.5`, and `reports/active/latest_sample_comparison_report.txt:124` prints the
committed chart opening the small blind at 2.5.

## Blocker

- [resolved] **The plan makes the one rake claim the contract forbids, in its Objective, where the five worker
  lanes read it first.** `docs/exec_plans/active/PHASE_17_CORPUS_VERDICT.md:20` says "Phase 14
  replaced the chart with one solved rake-free" with no qualification. The contract's forbidden
  shortcut is explicit: "Do not claim the solve is rake-free without the heads-up-flop-terminal
  qualification" (`docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md:151`), and its acceptance criterion
  says a claim that rake is eliminated is false (:71-75). This is not hypothetical here: the shipped
  export was solved under `"realization": "calibrated"`
  (`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json:37`), which is exactly the
  condition `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` (backlog.yml:4316) says makes the
  unqualified claim wrong. The plan's own review handoff (:94) requires the qualification on every rake
  claim, so the plan fails the check it writes. Fix: qualify line 20 - rake-free in the preflop
  betting, training rake retained at heads-up flop terminals.

- [resolved] **The prediction cannot be blind, and the plan does not say so, which makes the contract's central
  criterion satisfiable without doing the work it names.** Contract :50 and plan :65 and :102-104
  require the prediction "before the measurement runs". The measurement already exists in the tree at
  the base commit, against the committed chart:
  - [resolved] `reports/active/latest_spot_vocabulary_report.txt:290-294` prints the before/after columns -
    Pluribus agreement 96.3% to 90.9%, human agreement 93.6% to 90.1%, human calls agreeing 60.8% to
    36.2% (85 of 235), refusals 290 to 139 - each row labelled "moved by the chart cutover".
  - [resolved] `reports/active/latest_sample_comparison_report.txt:52-59` prints the same rates with
    denominators, :137-143 prints the price-band split the prediction is supposed to anticipate, and
    :146-155 prints the strict sampled-action rate (Pluribus 423 of 475, humans 2150 of 2432) beside
    it.
  - [resolved] `docs/BACKLOG.md:213` already publishes the permissive-versus-strict pair and the purity statistic
    (2.209 nonzero actions per cell at 21.0 percent pure, versus 1.323 at 73.0 percent).
  So "written before any measurement runs" is trivially true - no *new* measurement has run - while the
  outcome sits on disk in three committed files a lane A author will open in the first ten minutes. The
  review handoff's instruction to verify "the prediction was written before the measurement ran" (:92)
  cannot be discharged by any reader. Fix: the plan must state which committed figures are already
  public, require the decision list to name them as the starting point, and pre-register only what is
  genuinely unpublished - the per-opener defence deltas and bands, cell purity over the shared spots,
  and refusal movement by cause.

- [resolved] **Lane D's brief drops one of the three coverage costs the contract requires reported separately.**
  Contract :88-89: "Each exclusion's coverage cost is reported separately: the multiway ruling's, the
  re-source's, and the four-bet withholding's." Plan :73-75 gives lane D "phase 14's two exclusions
  costed separately from the limp" - the multiway ruling and the four-bet withholding - and never names
  the re-source. The re-source is a distinct event with its own coverage effect: phase 14 decision 14
  re-solved with `add_allin: false` over a smaller export
  (`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md:499`, `docs/BACKLOG.md:213`).
  With no lane owning it, lane B will not author a test for it at stage 4, and the tests freeze at
  stage 5.

## Non-blocker

- Three contract criteria have no owner in the Delegation Plan and no evidence in any slice. Lane E is
  scoped to "the generator, its self-validation, and the `COMMANDS` registration" (:75), which is
  plumbing, and nothing else covers the prose the contract is actually about:
  - contract :70-75, the report naming all three explanations and saying which it separates and which
    it cannot. This is the phase's stated purpose and no lane owns it.
  - contract :90-92, the bounds paragraph - six-handed, 100bb, symmetric stacks, no straddle, no ante,
    one opening price, heads-up only, no spot facing a four-bet.
  - contract :105-106, "at least one number is recomputable by hand from a committed file, and the
    audit packet says which and how". Slice S7 (:112-113) names only "the packet's pass/fail
    checklist". Stage 9's own driver check asks for this number (`scripts/loop_stage.py:582`).
- The review handoff (:90-96) plans one reviewer and gives it only document-hygiene checks: ordering,
  qualification present, no file changed, permissive never alone. Stage 8 is two reviewers, one
  mechanical and one poker-domain, and the domain pass exists to ask "whether the work is right, which
  is the only question a green gate cannot answer" (`scripts/loop_stage.py:571-577`). For a phase whose
  entire output is a poker verdict, the plan asks nobody whether the verdict is right.
- No reconciliation with the corpus machinery that already exists.
  `src/poker_training_bot/data_pipeline/comparison.py` already computes agreement and refusals
  (`compare_committed_sample`, :361), the strict rate (`sampled_action_match`, :302) and the price
  bands (`price_band_for`, :208), and `generate_sample_comparison_report` is already a registered gate
  command (`scripts/run_verify.py:230-233`). The plan invents
  `src/poker_training_bot/data_pipeline/corpus_verdict.py` (:38, :78) without a word about reuse or
  about the two having to agree. The result is two gate-registered generators publishing agreement
  rates over the same corpus against the same chart, with nothing checking one against the other.
- S1's evidence is circular (:100-101): "contract confirmed real rather than skeleton. Evidence:
  `loop_stage.py --phase 17 --advance` moves off stage 1." `check_contract`
  (`scripts/loop_stage.py:264-275`) counts non-boilerplate acceptance-criteria bullets and checks the
  plan file exists; the advance is unblocked by the very artifacts this slice produces, and tests no
  claim the slice makes.
- S7 (:112) files "backlog restatements" at "stage 9-10". Stage 10 is bookkeeping only - "A content
  change here belongs to an earlier stage" (`scripts/loop_stage.py:592`). Backlog restatement is
  content; put it at stage 9.
- Scope line :38 approves "`src/poker_training_bot/data_pipeline/corpus_verdict.py` and its report
  module". The second file is never named, here or in Ownership (:76-81). `check_scope.py` matches
  paths, so an unnamed file is an unapproved one and stage 6 will trip on it.
- Scope line :46-49 lists `data/artifacts/preflop/**` under "Forbidden, and not merely unapproved".
  AGENTS.md defines `forbidden_scope` as an existence rule - matching paths must not exist anywhere in
  the tracked tree - and that directory must exist, since it holds the chart this phase reads. Adding
  it to `forbidden_scope` in `CURRENT_TASK.yml` would red the gate. The intent is unapproved and
  read-only; say that instead.
- Scope line :42-44 restates standing scope and drops `verification/loop_state.yml`, which
  `CURRENT_TASK.yml:11` carries.
- Lane C (:73) is to produce "the old-versus-new disagreement count". Contract :97-99 requires the
  count *and* the direction.
- Lane B (:68) is to author "the two mutation canaries" without saying what each proves. Contract
  :110-112 is specific: one proves a wrong rate fails the gate rather than merely printing, one proves
  a refusal filed under the wrong cause is caught. An unspecified canary is the kind
  `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL` (backlog.yml:2117) describes.

## Alignment

- `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` (backlog.yml:4316). The entry's own trigger
  condition is met and unrecorded: it says that if `calibrated` ships, the rake-free claim needs
  qualifying wherever it appears, and the export shipped `"realization": "calibrated"`
  (`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json:37`). The committed,
  gate-generated `reports/active/latest_sample_comparison_report.txt:28-35` makes the unqualified
  claim and goes further than the contract permits: "nothing below is explained by it", "that
  explanation is gone", "has nothing to excuse it". That is phase 14's report and not phase 17's to
  edit, but phase 17 is the phase that measures the rake explanation, so the instance belongs on this
  entry rather than in this note.

- Proposed `PREDICTION-CANNOT-BE-BLIND-TO-A-COMMITTED-MEASUREMENT`. The loop asks a phase to
  pre-register a prediction about a measurement its predecessor already regenerated into
  `reports/active/`. Nothing in `scripts/loop_stage.py` or `scripts/check_contracts.py` detects that a
  pre-registration's answer is already committed in the same tree; the honesty of every such criterion
  rests on the author not opening a file. General form, larger than phase 17, and phase 17 cannot fix
  it - it can only disclose its own instance, which is the second blocker above.

- Proposed `CORPUS-AGREEMENT-HAS-NO-SINGLE-SOURCE`. On the plan as written the repo ends with two
  registered gate commands - `generate_sample_comparison_report` and
  `generate_corpus_verdict_report` - each computing agreement, refusals and a strict rate over the
  same corpus against the same chart from separate modules, with no check that they produce the same
  numbers. That is the drift shape
  `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` (backlog.yml:4293) already
  describes for figures, applied to generators. Either the new module builds on
  `data_pipeline/comparison.py` or something asserts the two agree.


## Coordinator resolution, 2026-09-06

The three blockers were fixed in `docs/exec_plans/active/PHASE_17_CORPUS_VERDICT.md` by the
coordinator, who wrote the plan under review. The reviewer's text above is unedited apart from the
`[resolved]` markers, which the driver requires on every bullet inside `## Blocker`, including the
three evidence sub-bullets under blocker 2.

- Blocker 1, the rake claim. The Objective now says the preflop betting is solved rake-free and the
  training rake is still carried at heads-up flop terminals under `realization: "calibrated"`, names
  the source card and `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`, and states that no sentence
  this phase writes may say otherwise.
- Blocker 2, the prediction that cannot be blind. The plan gains a section, "What is already
  committed, and what the prediction may therefore cover", listing the three files that already
  publish the outcome at `9bbdcf4` and the four figures that are genuinely unpublished. Lane A
  pre-registers only the second set and quotes the first as its starting point, and the decision list
  must mark which of its items is which so a stage-8 reviewer can check the claim rather than take it.
  The general defect is larger than this phase and is filed as
  `PREDICTION-CANNOT-BE-BLIND-TO-A-COMMITTED-MEASUREMENT`; the plan's disclosure is not a fix for it.
- Blocker 3, the missing third coverage cost. Lane D's brief now names all three - the multiway
  ruling's, the re-source's, and the four-bet withholding's - and lane B's test brief names them too,
  so the freeze at stage 5 covers the re-source.

Non-blockers taken in the same edit: lane F added for the verdict prose, the bounds paragraph and the
hand-recomputable number; two reviewers at stage 8, one mechanical and one poker-domain; the reuse
note pointing lane C at `data_pipeline/comparison.py`; S1's evidence de-circularised; backlog
restatement moved from stage 9-10 to stage 9; `corpus_verdict_report.py` named in scope;
`data/artifacts/preflop/**` restated as read-only-and-unapproved rather than `forbidden_scope`;
`verification/loop_state.yml` restored to the standing-scope list; lane C given the disagreement
direction as well as its count; lane B's two canaries given the failure mode each must prove.

Alignment items filed: `PREDICTION-CANNOT-BE-BLIND-TO-A-COMMITTED-MEASUREMENT` and
`CORPUS-AGREEMENT-HAS-NO-SINGLE-SOURCE` are now in `backlog.yml`. The
`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` instance the reviewer found in phase 14's committed
`latest_sample_comparison_report.txt` is real and is not phase 17's to edit at stage 1; it is carried
into this phase's stage-3 decision list as an open question for Taylor, since correcting another
phase's committed report is a ruling rather than a fix.
