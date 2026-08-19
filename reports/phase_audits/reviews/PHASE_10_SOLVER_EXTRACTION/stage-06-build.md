# Stage 06 Review - Build (Phase 10)

Question asked: does the implementation do the work, or only enough to satisfy the frozen
tests? Name anything that passes for a reason the contract did not intend.

Scope: `git diff ce553eeb4aff24713b1633690c541c289c31d451 -- backlog.yml
data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz
data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json
scripts/check_solver_export_expectations.py scripts/extract_gtopen_preflop.py
scripts/generate_solver_export_report.py
src/poker_training_bot/solver_artifacts/gtopen_config.py
src/poker_training_bot/solver_artifacts/gtopen_expectations.py
src/poker_training_bot/solver_artifacts/gtopen_export.py
src/poker_training_bot/solver_artifacts/gtopen_export_report.py
src/poker_training_bot/solver_artifacts/gtopen_source_card.py`

Reviewer: coordinator, read-only pass against the diff and the committed report. Subagent
delegation is switched off in this operator's sessions, so `AGENTS.md` step 6 cannot be
satisfied and step 10's self-review fallback applies. Two passes were kept apart: whether the
code does what it claims, and whether the poker it produced is poker.

## Blocker

- [resolved] **A frozen test asserted a number the fixture it reads does not hold.**
  `test_a_strategy_row_is_uniform_where_the_hand_never_arrives` asserts
  `node["reach"][72o] == 0.0` against `gtopen_node_payloads.captured.json`, where the value is
  `3.6852573e-08`. The test is the conditioning discriminator the contract asks for and its
  finding is right - 72o never arrives and still carries a full uniform strategy row - but
  exact equality against a float a real solver produced is an assertion the captured payload
  was never going to satisfy. Nothing in the implementation can fix it: the test reads the
  fixture, and editing the fixture to fit a test is fitting the evidence to the claim, which
  the contract's forbidden shortcuts name. Stage 4 never caught it because the stage-4 check
  requires the phase's pytest command to be *red*, and it was red on a missing module, so no
  assertion in either file had ever executed. Repaired in its own task, tests re-frozen, and
  the `1e-6` bound is stated in the test rather than left implicit.

## Non-blocker

- **Seven backlog items had a status the gate rejects, filed by this phase's own earlier
  stages.** `ALLOWED_BACKLOG_STATUSES` is `{deferred, done}` and six items filed at stages 2
  through 4 carried `open`, three of them against a phase label `maintenance` that is neither
  a phase nor a declared non-phase label. `check_repo_consistency` does not look at either
  field, so the defect stayed invisible until the quality gate ran here for the first time on
  this branch. Retagged to `deferred` and to `contract-update` where the work is process work.
  The lesson is the same one as the blocker above: this phase reached stage 6 having never run
  the gate its own additions were measured by.

- **The two gated checks cannot catch an extraction that is wrong but ordered, and the
  implementation does not pretend otherwise.** `test_a_solve_nowhere_near_the_reference_still_
  passes_every_check` halves every frequency and passes, by design. So the pipeline assurance
  rests on three things outside the orderings: the converted node reproduces GTOpen's own
  `freq` to within 3.8e-05 on all six captured nodes, the walk re-resolved all 38,828 nodes
  from their own action sequences with zero mismatches, and a human reads grids against the
  saved solve. That is the right division, but the gate's green is worth less than it looks
  and the report says so in its own labels.

- **`bytes_per_expressible_spot` divides the whole export by 36 and needed the note it now
  carries.** The contract asks for bytes per expressible spot so Phase 14 sizes itself from a
  measurement. 4,094,221 over 36 is 113,728 bytes, which is not the size of anything Phase 14
  would build - it is what keeping the entire tree costs per spot currently usable. Left as the
  measurement with a `bytes_per_expressible_spot_note` field saying exactly that, rather than
  inventing a denominator this phase has no vocabulary for. The useful number beside it is
  `bytes_per_node`, 105.45, which is format rather than selection.

- **The source card's headroom counts the card itself, which took a fixed point.** The first
  run recorded 16,397,029 bytes of headroom against a real remaining 16,394,856, because
  `directory_bytes()` ran before the card was written and the card lives in the directory it
  measures. Its own digits move the total, so `write_card` iterates to a stable value. A frozen
  test compares the figure against a live recount, which is what caught it.

- **The saved solve's path on the card is absolute and machine-specific.**
  `/Users/taylorsprouse/projects/gtopen/saves/preflop/six-max-100bb-rakefree.gtop`. That is a
  fact rather than a claim, and a reviewer following decision 6c needs to find the file, so it
  stays. What travels is the sha256 beside it: a reader on another machine can confirm they
  loaded the same save, which is the part that matters.

- **Determinism is a genuine two-run diff, and the runs were made honest.** The server was
  killed and restarted before the second solve, the second extraction ran in a fresh process,
  and the diff is node by node over strategies and reach rather than a checksum comparison
  alone - so a shape difference and a frequency difference are reported separately. Result:
  byte-identical, zero divergence, zero shape differences. The wall clock is 60.2 seconds at
  iteration 300 for a solve, and roughly six minutes for the walk and its re-resolution pass.

- **The export container is a custom format and that is a real cost.** Header JSON plus raw
  little-endian `uint16`, gzipped with `mtime=0` and no member name, which is what makes two
  writes byte-identical. A plain JSON dump of 29.5 million basis points would not have fit
  under the ruled 20 MB; this fits in 4.09 MB with 15.6 MB of headroom. The cost is that the
  committed file is not readable without this repo's reader, which is a step away from the
  "committed data is reviewable" position every other artifact here holds. What buys it back is
  the report: 11 spots rendered as grids, with the omitted count stated.

## Domain pass: is the poker poker

- **The rake-free direction is right nearly everywhere.** Opening frequencies come back wider
  than the raked GTO Wizard reference at LJ (19.08 against 17.49) and big-blind defence comes
  back wider against LJ, HJ, CO and SB. The two that do not follow are known and recorded:
  BB versus BTN comes back tighter (36.76 against 39.43), and SB opens 54.09 against 34.41
  because twelve points of limping became raising in a tree with no limp. Neither is gated, and
  the phase's own ruling is that this comparison measures two products rather than this
  extraction.

- **One cell is not poker, and it is convergence rather than extraction.** The LJ opening
  range raises 44 at 72.81 percent while raising 33 at 99.88 and 22 at 99.92. A pocket pair
  that opens less often than both pairs beneath it is noise, not a strategy, and it is the
  marginal-hand behaviour the contract itself predicts: the solve stopped at iteration 300
  because the summed best-response gap crossed 0.01 bb, which is decision 3's ruled target and
  not this stage's to change. Every other pair in every other opening spot sits above 99.8, so
  it is one cell rather than a pattern. Filed as `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`
  against Phase 14, because a chart derived cell by cell inherits it.

- **The hand-index mapping is right, checked on the grids rather than only on the unit test.**
  In the LJ opening grid the wheel suited aces A5s to A2s open at 100 while A6s opens at 9, and
  the offsuit cells below the diagonal at the same ranks are 0. A transposed index would have
  put that structure below the diagonal, and the eye catches it faster than any assertion.

## Alignment

- `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` - the ruled convergence target leaves one pocket
  pair non-monotone; it belongs to whoever derives a chart from this export, not here.
- `DEFENCE-RELATION-NARROWER-THAN-THE-CONTRACT` - the contract says the defence relation holds
  "for every pair of positions"; the frozen tests require the small blind to be checked only
  as the wider opener, and the implementation follows the tests. The contract sentence should be
  narrowed to match at the next contract-update.
- `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK` - the command registry still describes
  `check_solver_export_expectations` as computing the withdrawn directional bound.
  `scripts/run_verify.py` left `approved_scope` at the freeze, and a description is not worth
  reopening a narrowed scope for.
