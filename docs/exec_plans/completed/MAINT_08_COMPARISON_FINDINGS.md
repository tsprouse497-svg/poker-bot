# MAINT-08: Close The Five Findings The Phase 08 Gate Could Not See

## Objective

The same post-hoc review that produced MAINT-07 left five findings.
None of them is a failing test, because none of them is the kind of thing a test was ever asked about.

1. The comparison never recorded the position a decision was taken from, so the phase's headline calling gap named a symptom and hid the cell.
2. `agreement_by_observed_action` filtered on the action and nothing else, pooling Pluribus with the humans.
   That is the one operation judgment call 7 forbids, reintroduced by the stage 8 fix for a different problem.
3. `_self_play_spots` recovers spot keys by pattern from another phase's rendered report and returned an empty set when it found nothing, so a format move would mark every real-hand spot NEW and read as the strongest possible version of the phase's most actionable claim.
4. `corpus_sidecar.json` is the largest file in the committed sample, is read by nothing at run time, and had only its key set checked.
5. Three committed documents state that 7 of the sample's hands contain an all-in.
   That count scans for a preflop shove of a full stack; the sample holds 24.

## Scope

Approved:

- `src/poker_training_bot/data_pipeline/comparison.py`
- `tests/test_sample_comparison.py`
- `verification/mutations.yml`, `verification/freeze.lock`
- `docs/SAMPLE_CORPUS_SOURCE.md`
- `reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md`, its decision record, and its review notes

Forbidden here:

- The Phase 08 contract.
  Nothing below needs it: the contract already requires the populations to be reported separately and every rate to carry its denominator, and findings 1 and 2 are the report failing to do what it already promised.
- The committed sample, the selection rule, and the charts.
  A phase may not edit the thing it measures, and that does not expire when the phase closes.

## Delegation Plan

- No-delegation exception: subagent delegation is disabled in this operator's sessions, the same constraint recorded in the Phase 08 audit packet and in MAINT-07, so implementation and review are coordinator-owned.

## Slices

- [x] Slice 1: every `ComparisonRow` carries the position it was taken from, derived from `seat_positions` against the button the converter placed rather than from a second seat-to-position rule.
      Evidence: a test comparing every row's position against `seat_positions` for its own hand.
- [x] Slice 2: `agreement_by_observed_action` is replaced by `agreement_within(population, *, action, position)`, where the population is a required positional argument and has no pooled value.
      Evidence: a test that asks for a rate without naming a population and requires a `TypeError`.
- [x] Slice 3: the report prints the action split per population and a per-seat table per population, with each seat's refusal count beside its rates.
      Evidence: the committed report, and tests that the position split partitions its population exactly and that it localises the calling gap to the big blind.
- [x] Slice 4: `_self_play_spots` raises on a missing file and on a file it cannot recognise.
      Evidence: a test that redirects the path at both failure modes.
- [x] Slice 5: the sidecar's every field is checked against the corpus text it describes.
- [x] Slice 6: the all-in count is corrected in all three documents and pinned by a test, with what the old number actually counted written down rather than quietly replaced.
- [x] Slice 7: three canaries - a pooled rate, a vacuous position filter, and a silently empty cross-reference - and the tests re-frozen.

## Verification

- `uv run python scripts/run_verify.py` (full derived gate)
- `check_gate_bite` at 25 mutations

## Outcome

Full gate green.
25 mutations applied and all 25 caught, up from 22.
49 tests in `pytest_sample_comparison`, up from 41.

The finding underneath finding 1 turned out to be the useful one: the calling gap is a blind-defence gap.
Human calls agree 53.2% in the big blind against 62-77% in every other seat, and the big blind holds 58 of the 89 human call disagreements.
The same seat is refused most often, on 26.6% of its decision points against 1.3% in the hijack, and refusals sit outside every agreement rate, so the big blind's rate is computed over the subset of its decisions the chart could answer.

Corrected in MAINT-09: this paragraph originally read 70 of 104, which pools Pluribus with the humans while carrying a humans label - the exact violation this task removed from the code, reinstated in the sentence describing the removal.
It also read "the seat the chart plays worst", which presents a disagreement with a human player as evidence the chart is wrong and is a forbidden shortcut in the Phase 08 contract.
MAINT-09 also found that most of this gap is predicted by the artifact: the chart is a raked solve read against a rake-free corpus, at an opening size the sample mostly did not use.
Both halves are now printed side by side and pinned by tests, and `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` is rewritten around them.

## Next Agent Bootstrap

The repo is at `task_mode: idle` with Phase 08 completed and Phase 09 still `future`.
Two findings from the same review are deliberately not done here and are not filed either:
the report still lists only the first 20 of 164 disagreements with no committed file holding the rest,
and `convert.py` still builds `showdown_seats` from the corpus's own show records and then discards it, so a normalized hand's `showdown` means "did not fold" rather than "showed".
Both are small. The second touches Phase 02's schema meaning, so it wants a contract read before it is moved.
