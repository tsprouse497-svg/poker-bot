# MAINT-34 independent review: the frozen-test diff and the re-freeze

## Reviewer independence

Read-only lane that wrote none of the work under review. It was given the complete `tests/**` diff
against the lane base `19beb97` - 30 files, roughly 1,816 insertions and 1,133 deletions, plus four
new helper files - and told that the re-freeze gates on its answer. It ran the suite read-only and
no gate command. It was told explicitly that coming back empty with its checks named is a pass.

This round replaces an earlier one that did not survive. The coordinator session was lost on
2026-09-17 with both reviewers in flight and neither's findings written, so both were re-dispatched
from the same briefs and nothing of the first round is recorded here, because nothing of it exists.

## Verdict: no blockers. The diff is a correction, not a weakening.

The single risk this round existed to catch is a test loosened rather than re-derived. It is not
present:

- No test function was deleted anywhere. Per-file `def test_` counts are identical across all 26
  modified modules.
- Assertion counts rise in every file except `test_solver_export.py`, which goes 65 to 64 - exactly
  the two deletions decision 6 authorises, minus one guard added back.
- No tolerance moved. `TOLERANCE_PCT` 1.0, `SPLIT_LEAK_PCT` 0.05, `UNIFORM_TOLERANCE_BP` 200,
  `EXPOSURE_THRESHOLD_PCT` 10.0, `COMMITTED_RAISE_DEPTH` 2, `RANK_ARM_SPOT_FLOOR` 5 and the
  sample-comparison ten-point floor are all unchanged.
- The one bound that moved got **tighter**: `node_count > 33_000` became `> 30_000`, which is 2.0
  percent of headroom below the measurement where 33,000 was 2.85 percent.

## What was recomputed rather than read back

From the chart and sizings: 156 spots; raises-faced 5 / 16 / 135; families 5 first-in, 5 bb-open, 11
merged, 135 three-bet-facing; 14,586 cells at non-zero reach and 11,778 dropped; 3,830 cells with a
published raise weight; prices by depth `{0: {2.5}, 1: {7.5, 13.5}, 2: {22.5, 40.5, 100.0}}`; 148
spots priced and 8 with an empty price list; 33 spots quoting 100.0; 53 spots at `arrival_ppb == 0`;
published purity 91.04 / 5.55; 58 full grids.

From its own walk of the export: 30,609 nodes; the census 156 / 154 / 9 / 160 / 128 / 30,002 summing
exactly; 3,777 jam nodes of which 34 are committed; the widest admitted exposure 9.1945 and the
narrowest refused 10.4362; the widest closure shortfall 0.0106 against an untouched 0.05 tripwire;
the squeeze node at 89.13 / 4.97 / 5.90.

Relations recomputed with the reviewer's own code rather than the repo's: pair inversions 87,
identical rounded and unrounded, so decision 6's six-decimal rounding is provably inert on that
ladder; kicker inversions 197 = 60 wheel-ace + 15 no-story-wide + 122 narrow.

`PARTITIONS` and `ARM_ROWS` - 70 numbers - were not recomputed cell by cell. Every one of their
eight columns balances both by raises-faced and by seat against the committed-set figure, which is
sixteen independent sum constraints, and all sixteen hold.

Uniform cells: 167 exact and 168 tolerant, the one extra being at a different spot and trained -
which is the measurement ruling out a tolerance as the detector, as decision 5 claims.

## Non-blockers, all fixed by the coordinator the same day

1. `test_chart_conversion.py` stated "the 49 blind-versus-blind spots decision 4 accepted" as live.
   49 is decision 4's pre-decision-7 count and the file's own constant three lines up is 34.
2. `test_ask_preflop_chart.py` gave a false reason for a correct choice: it named an `AA` cell at
   0.5002 as nearer the coin flip and skipped for zero arrival. No committed key carries that
   sequence - clause five refused it - and an enumeration of every two-action cell confirms the
   chosen `QQ` cell at 0.5029 is genuinely nearest.
3. The same file's `MISS_UNTRAINED_CELL` comment named `KQs` where the command line asks for `AA`.
   Both carry the uniform initialisation; the comment now names the hand the case uses.
4. `test_derived_chart.py` carried `..._are_two_hundred_and_eighty_four_distinct_keys` in a test's
   own **name**, renamed from "forty_nine" at the intermediate cut and never moved to 156. A pytest
   failure line prints the name, not the docstring.
5. Decision 4's re-measured count is one low and does not say which reading it is: 33 / SB 28 counts
   spots where a class takes the jam, 34 / SB 29 counts menus, and "offer" asks for the menu.
   Corrected in the decision, the ExecPlan and the backlog, with the one spot between the two
   readings named.
6. The census heading reads "four-bucket" over six buckets.
7. `untrained_cells.py` stated a safety argument that is false - "a spot the solve reaches has
   `arrival_ppb > 0`". The field is rounded: 53 committed spots store 0 and only 47 are at exactly
   zero, so 6 are played and indistinguishable here. All 6 publish a three-action menu, so the
   exact-shape half is what keeps the guard sound, not the arrival half. The sentence was corrected
   rather than the code.
8. Decision 6's authorised deletion left its hole empty. After it, nothing in `tests/`, `scripts/`
   or `src/` compared the committed card's `achieved_gap_bb` to its own `target_gap_bb`, though both
   are written side by side and the card is loaded three lines from the deletion. A solve that
   stopped at the iteration cap short of its target would have shipped with the card saying so in a
   field no test read. `test_the_committed_solve_reached_the_target_it_declared` now closes the half
   of `A-SOLVE-THAT-MISSES-ITS-DECLARED-TARGET-SHIPS-WITH-NOTHING-OBJECTING` that concerns the
   committed artifact.
9. Cosmetic: a docstring in `test_chart_derivation.py` still described "the four buckets".

## Alignment items

- **The rounding fix removes a witness.** Making the report's `ARM_ROWS` and the walk's `PARTITIONS`
  equal by construction was the right repair, but "two independent walks agree" was one of this
  phase's few genuinely independent cross-checks. They can no longer disagree about a defect they
  share. Nothing to do; worth knowing it is one witness wearing two names.
- **`NO_ARRIVING_REFUSED_NODES` (160) is the only census bucket whose size is a function of solver
  convergence rather than tree shape.** It read 32 on the unconverged run. A future unconverged
  solve moves a census pin that reads like tree shape.
- **Two tests are one spot from vacuous and both say so.** Recorded honestly, not a defect.

## What the reviewer was asked at the end, and answered

**What it did not look at.** `src/**`, `scripts/**` and `data/**` as code, except where a test pin
pointed at them. Not `docs/**`, `backlog.yml`, `CURRENT_TASK.yml`, `phase_status.yml`, the contract
amendments or `verification/freeze.lock`. It did not re-solve or check determinism; the export is
taken as given and every figure is measured off it. It did not judge whether the ranges are better
poker - that was the other reviewer's brief.

**A finding it was holding back.** `test_chart_cutover_evidence.py`'s fourth relation now asserts an
*absence* - that no inversion is gained by the merge. Pinning absences is the right call and the
file argues for it well, but two of the three witnesses that made the relation concrete are gone and
the surviving grip is `after_pairs <= before_pairs` plus two cases. A consequence of the re-solve
rather than a defect in the repair, so not called a finding.

**A premise in the seven decisions it believes is now false.** One, decision 4's re-measured count,
which is non-blocker 5 above. Everything else holds: decision 7's central claims check out exactly,
decision 5's do, and decision 6's four rulings are all implemented as ruled.
