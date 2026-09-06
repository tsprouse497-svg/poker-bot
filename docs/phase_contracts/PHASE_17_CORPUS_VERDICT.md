---
phase_id: "17"
title: "The Corpus Verdict On The Committed Chart"
depends_on:
  - "14"
required_gate_commands:
  - pytest_corpus_verdict
  - generate_corpus_verdict_report
required_reports:
  - reports/active/latest_corpus_verdict_report.txt
required_phase_audit: reports/phase_audits/PHASE_17_CORPUS_VERDICT.md
---

# Phase 17: The Corpus Verdict On The Committed Chart

## Scope
Phase 14 commits a preflop chart derived from a GTOpen solve. This phase measures that chart against
the public hand corpus and says what the result does and does not establish about v1's calling gap.
The two were one phase until 2026-08-31, when Taylor split them: committing an artifact and rendering
a verdict on it are different jobs with different failure modes, and phase 14's contract could not hold
both inside the 300-line cap `check_file_sizes.py` sets
(`PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP`).

**The question this phase exists to answer.** Phase 08 measured the committed chart against 499 real
hands and found calls agreeing 59.5 percent for Pluribus and 60.8 for human professionals, against a
96.3 percent headline dominated by the 72 percent of decisions that are folds. It offered three
explanations for the gap and could separate none of them: the chart was solved with NL25 rake against a
rake-free corpus, it was solved against a 2.5bb open where the players opened to a median 2.25, and its
realization model underprices position. Phase 14 removes the first of those and keeps the third. This
phase re-runs the comparison and reports which explanations survive.

**What it inherits and does not re-litigate.** The committed artifact, its selection rule, its two
exclusions and their node counts, and the source card's stated limitations are phase 14's and arrive
ruled. This phase may not change the chart to improve a rate. If the measurement suggests the chart is
wrong, that is a finding and a backlog entry, not an edit.

## Non-goals
- Do not add PokerNow automation, browser or platform observation, runtime solver calls, LLM-backed
  poker decisions, or training UI surfaces. These are the standing V1 boundaries.
- Do not re-solve, re-derive or hand-edit the committed chart, its sizing table or the expectations
  file. This phase reads committed data and writes a report.
- Do not narrow the corpus sample to improve an agreement rate, do not pool the two populations, and do
  not read a residual disagreement as a chart defect while price and realization stay uncontrolled.
- Do not widen the chart's coverage to raise a rate. A refusal is phase 14's ruling and this phase
  measures its cost rather than reversing it.

## Acceptance criteria

### The prediction, before the measurement
- The prediction is written into this phase's decision list **before the measurement runs, per opener
  and with a magnitude band** - a quarter to one times that opener's defence delta - with the deltas
  recomputed from the committed chart. Phase 14's decision 9 bands were fixed against builds that phase
  discarded and are void rather than inherited.
- A sign-only prediction cannot answer the question: five points of defence is **66.3 combos of 1,326**,
  so any nonzero movement confirms a sign while leaving the gap intact. The prediction covers price and
  its direction - the small-blind open reprices from 3.5bb to 2.5bb.

### What the rates must say
- **The permissive agreement rate is never reported alone, because on this corpus it rewards an
  unconverged chart.** Agreement means nonzero weight on the observed action, so a cell with every
  action nonzero cannot disagree with anything, and a chart converging to purer cells scores worse while
  playing better. The report publishes the **strict sampled-action rate and the cell-purity statistic
  beside** it, over the shared spots, and states that a fall is what a converged chart looks like rather
  than a regression; printing the fall alone states the reverse of the truth
  (`AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`).
- **Every rate is measured against the committed chart in this phase and none is carried forward.**
  Phase 14's contract quoted rates taken on three different builds it discarded; a level with no named
  artifact is what `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` is about, and this
  phase states the artifact checksum every figure was taken on.
- The report names all three candidate explanations for a residual gap - rake, price, and realization
  underpricing position - and says which it separates and which it cannot. **The rake explanation is
  only partly removed**: the solve is rake-free in its betting, but under `calibrated` the fit was
  measured net-of-rake over the gross pot and the engine skips the rake deduction at heads-up flop
  terminals, so those leaves carry the fit's training rake
  (`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`). A claim that rake is eliminated is false.
- The retained sample and refusal rate are reported beside every agreement rate, with the definitions
  that make one readable: agreement means nonzero weight, and real players are not an oracle.

### What the refusals must say
- **The refusal rate is reported against a named baseline and split by cause**, so a multiway refusal
  reads apart from a four-bet-pot refusal, a limp or an unmatched key. The baseline is the retired
  chart, and the rate must **rise only where phase 14's two exclusions and the limp account for it, and
  nowhere else**. A rise outside them is a defect, not the cost of a ruling.
- **The four-bet exclusion must produce no rise at all against that baseline**, because the retired
  chart holds 36 keys and not one of them faces a four-bet. What phase 14 forwent is a capability it
  could have added, not one the bot had (`CHART-CANNOT-ADVISE-A-FIVE-BET`). A rise attributed to the
  four-bet withholding is a measurement error.
- **Each exclusion's coverage cost is reported separately**: the multiway ruling's, the re-source's, and
  the four-bet withholding's. Conflating them charges one ruling for another's cost.
- The report bounds what the chart answers at all - six-handed, 100bb, symmetric stacks, no straddle, no
  ante, one opening price, heads-up only, and no spot facing a four-bet - so no rate reads as a grade on
  preflop play.
- The refusal inventory is republished and its movement stated by reason rather than as one total, over
  the closed vocabulary `lookup.py` defines. The phase publishes its own count of decision points facing
  a limp with the definition it counted by, because `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry
  one.
- Where the committed and retired charts both answer the same corpus decision, the report says how often
  they disagree and in which direction, reading the retired chart from git history at the pin phase 14's
  decision 7 names.

### Evidence, reports, and gate
- The report shows a non-coding reviewer, without reading code, what the comparison found: the
  prediction beside the outcome, the rates with their denominators, the refusal movement by cause, and
  the three explanations with which survive. At least one number is recomputable by hand from a
  committed file, and the audit packet says which and how.
- The report generator validates its own figures and exits non-zero when they do not hold: the retained
  sample against the corpus size, the refusal counts against the inventory, and the old-versus-new
  disagreement count. The rest is prose and the audit packet says so.
- Both command IDs are declared here, registered in `COMMANDS` in `scripts/run_verify.py`, and carry a
  mutation canary authored before the implementation, with `check_gate_bite` proving each bites. One
  proves a wrong rate fails the gate rather than merely printing; one proves a refusal filed under the
  wrong cause is caught.
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`, the
  audit packet carries pass/fail evidence, and deferred work is in `backlog.yml`.

### The backlog entries this phase settles
- `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`: recomputed on the sample the committed chart retains, and
  restated against the strict rate too. Its stated 89 and 58 human call disagreements are stale against
  a repo that computes 42 and 14, and this phase is where they are restated rather than left drifting.
- `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART` closes on the reporting rule above, or is restated with
  what it would take to close.
- `CHART-CANNOT-ANSWER-A-LIMPED-POT` is restated with the measured cost and the definition it was
  counted by; `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` is restated with the inventory this phase
  republishes.
- `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` is not closed here. It bounds what this phase may
  claim about rake, and it closes when the source changes.

## Required reports
- `reports/active/latest_corpus_verdict_report.txt`

## Required command IDs
- `pytest_corpus_verdict`
- `generate_corpus_verdict_report`

## Human vetting packet requirements
- Plain-language summary of what the comparison found and what it does not establish, in the same
  paragraph as what it does, with a pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports; known limitations and deferred items.
- The permissive agreement rate never stated without the strict rate beside it.
- The prediction as it was written before the measurement, beside the outcome, with a miss in either
  direction reported as a result rather than explained away.
- The artifact checksum every figure was taken on, so a later reader can tell which build was measured.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success, infer missing corpus behavior, or change
  this contract during implementation mode.
- Do not change the committed chart, its sizing table or the expectations file to move a rate. If the
  measurement says the chart is wrong, that is a finding for `backlog.yml` and a ruling for Taylor.
- Do not report a rate without its denominator and the definition it was computed under, and do not
  compare a rate to one taken on a different build without saying so.
- Do not claim the solve is rake-free without the heads-up-flop-terminal qualification.

## Regression expectations
- Previously completed phase gates remain verifiable, generated human docs remain current, and
  file-size and scope checks continue to pass.
- Phase 14's frozen tests are not edited by this phase. It reads the artifact they guard.
- The refusal inventory and the sample comparison reports are expected to move, because the chart
  moved. A moved number is not a regression; the report says which moved and why.
