# Phase 14 stage 4: confirmation review of the post-review fixes

Read-only. This reviewer wrote none of the work, read neither earlier note before starting, and read
`stage-04-recut-review.md` first as instructed. Worktree `~/projects/poker-bot-worktrees/phase-14`,
branch `phase/14-chart-cutover`, HEAD `8006516`. Only this file was written.

**Remit**: the five `[resolved]` blockers, the eleven fixed non-blockers, decisions 54 and 55, and the
contract edits that carry them - not the whole stage.

**What was run.** `pytest_derived_chart`'s eleven files (57 failed / 55 passed / 3 skipped); the whole
`tests` tree (123 failed / 985 passed / 3 skipped); `ruff check --no-cache .` (clean); `check_scope.py`,
`check_file_sizes.py` (both rc 0); `run_full_quality_gate.py`; `loop_stage.py --phase 14` read-only;
`git show`/`log`/`for-each-ref`/`ls-remote` only. `check_gate_bite.py` was **not** run.

**Every figure below was re-derived by a walk written for this pass**, in a scratch directory outside
the repo, importing nothing from `tests/`: my own tree walk, my own exposure and selection clauses, my
own rank reversal, transposition, comparison lists and inversion counter.

---

## Blocker

### `[resolved]` The retired-chart pin is reachable from one unpushed local branch ref, and the lane's own rebase kills it

**Resolved 2026-09-03 by the F1 fix lane, taking the second of the two options offered.** The 86 ids are
now a generated tuple in `tests/test_spot_vocabulary_downstream.py` itself, so they are covered by the
freeze lock, beside `RETIRED_CHART_SHA256`, the sha256 of the source they came from.
`test_the_retired_chart_fixture_agrees_with_its_source` asserts in both directions - ids equal while the
file at `RETIRED_CHART_PATH` hashes to that value, ids different once it does not - so it never skips and
neither branch can go permanently red. Blob addressing was judged and declined: it survives a rebase but a
blob no reachable commit names is a garbage-collection candidate, which trades a certain failure for a
slower one, and it keeps a git dependency that a tarball or a shallow clone still breaks. The reasoning is
recorded in the constant's own docstring, which the freeze then carries.

`tests/test_spot_vocabulary_downstream.py:311` (`RETIRED_CHART_COMMIT`), read at `:325-340` and used at
`:349`, `:501`, `:508` and `:551`.

The B4 fix is right in design and its self-checks are real. I confirmed the pin reads **86** spot ids,
all distinct, with **zero** `:call` keys, reducing to **51** shapes of which **30** carry three or more
raises, and the blob is byte-identical to the file on disk today. Reading history rather than disk is
the correct call: stage 6 replaces that path in place, so a working-tree read would compare the new
chart against itself.

**The pin it chose cannot survive the workflow.** Measured in this tree:

- `git for-each-ref --contains db08304538c26361f3e692230e8cb544a9bf91c0` returns exactly one ref,
  `refs/heads/phase/14-chart-cutover`.
- It is **not** an ancestor of `main`, and `git log main -- data/artifacts/preflop/six_max_100bb_rakefree.json`
  is empty: that file has never existed on `main`.
- `git ls-remote` puts `origin/phase/14-chart-cutover` at `5867621`, which is an ancestor of local HEAD.
  The pin is a local unpushed commit. **A fresh clone of this repository cannot run these tests today.**

`retired_chart_spot_ids()` opens with `assert blob.returncode == 0`, so an unreachable commit is a hard
red that no stage-6 implementation can clear - the same shape as B1 and B2, deferred in time rather than
avoided. `AGENTS.md`'s Parallel Phases section prescribes that a lane **rebases onto the new `main`** when
a sibling merges. A rebase rewrites `db08304` into a new hash, `git show db08304:...` fails from then on,
and `pytest_spot_vocabulary` plus the catch-all `pytest` are red forever. After stage 5 that is not
fixable without unfreezing a frozen test.

**Concrete failure scenario.** `maint/29` or `phase/11` merges to `main` first; this lane rebases as the
fleet rules require; `pytest_spot_vocabulary` goes red on "`data/artifacts/preflop/six_max_100bb_rakefree.json`
is not at the pin"; the retired 86-spot chart exists in no other commit, on no other branch, and on no
remote, so there is nothing to re-pin to.

**Cheapest fix that keeps the design.** Address the **blob**, not the commit:
`git cat-file blob 9bde32b4631d6c266b521b4b4c90653126a7d587` (verified: that is the blob at the pin). A
rebase preserves the tree for an unchanged path, so the blob id survives a rewrite that the commit id
does not. Stronger still, and it removes the git dependency outright: commit the 86 ids as a fixture
under `tests/`. The reason recorded for rejecting a copy - the importer's glob would find it and a reader
would ask which chart plays - is a reason against a copy in `data/artifacts/preflop/`, not against one in
`tests/`. Whichever is chosen, the branch should be pushed before stage 5 either way.

---

## Non-blocker

### 1. The assertion that replaced B2's wrong one cannot fail

`tests/test_chart_counterfactual_arms.py:345-350`.

```python
assert len(folds_everything) == SPOTS_FOLDING_EVERY_HAND == 13          # line 344 - this one bites
assert sum(1 for before, after in zip(grids, over_folding, strict=True)
           if before != after) == len(grids) - len(folds_everything)     # 345-350 - tautology
```

`over_folding[i] != grids[i]` holds exactly when some cell is non-zero, because `0.0 * 0.5 == 0.0` and
`v * 0.5 != v` for every non-zero finite float; `folds_everything` is defined as the grids where
`not any(cells.values())`. The two sides are therefore the same predicate counted twice, for **any**
input, not only this export. The docstring says "the count is what has to say so", but the count that
says so is `== 13` on the line above, which I confirmed: 13 committed spots fold every arriving hand,
**11 SB, 1 CO, 1 BTN**, exactly as pinned. Nothing is wrong with the fix; the second assertion is
decoration wearing the shape of the check, and a reader will believe it is the check.

### 2. Decision 55's two corrected figures carry the weakest published check in the file

`tests/test_derived_chart_report_ranges.py:234-241`. `numbers = [int(v) for v in re.findall(r"\b(\d+)\b", body)]`
then `assert count in numbers` for `RAISE_ACTION_INVERSIONS = 41` and
`RAISE_ACTION_INVERSIONS_INVISIBLE = 25`. `\b(\d+)\b` splits `93.20` into `93` and `20`, so every share,
band and EV figure in the defects section contributes stray two-digit tokens; `41` and `25` are satisfied
by an appearance in any role. This was already recorded as a non-blocker (N7) and is not new. It is worth
restating because the constants it now guards are the two the phase just spent a decision correcting, and
because the fix that closes it already exists next door: `test_chart_cutover_evidence.py:481-483`
re-derives both off the export. The report-side check should read the same walk rather than a substring.

### 3. Three of the four quality checks are red for reasons no stage-6 chart clears, and the entry that owns them names a stale count

`scripts/run_full_quality_gate.py` reports **33** error lines - 4 fact drift, 29 backlog integrity -
and `tests/test_quality_hardening.py:218,279,403` fail on them. They are backlog statuses of `open`,
`phase:` labels outside the allowed vocabulary, and id-shaped prose read as citations. All but one
pre-date this commit (`TEST-FILES-ARE-WRITTEN-UP-TO-THE-700-LINE-CAP`, filed here against phase
`tooling`, adds one), so this is inherited debt and not a defect of the fixes. Two things make it worth
a line before the freeze. `tests/test_quality_hardening.py` is inside the base gate's catch-all `pytest`,
so the phase cannot close on a red it did not create and nobody has listed. And the backlog entry that
owns the family states the number as **sixteen**, measured 2026-08-31; it is 33 today - the same
hand-typed-count-goes-stale failure the stage's own through-line names, sitting in the file the stage
edited 275 lines of.

### 4. The tree is in `contract-update` mode and the driver will not advance

`scripts/loop_stage.py --phase 14` prints "not done yet: task_mode is 'contract-update', expected
implementation". The switch is properly logged in `CURRENT_TASK.yml`'s `scope_change_log` and the mode
was needed for decisions 54 and 55, so this is a state to return rather than a defect. Recorded because
stage 5 cannot run until it is returned, and because the freeze lock is the other half of that step:
`verification/freeze.lock` is 108 lines and lists **none** of the six new test files.

---

## Alignment

**1. The contract says "the skipped count", singular, where decision 54 and the frozen tests require two.**
`docs/phase_contracts/PHASE_14_CHART_CUTOVER.md`, rank-arm criterion: "a comparison whose partner cell is
absent being skipped and the skipped count published per partition". Decision 54's whole diagnosis is that
one number standing for both sides is the splice that produced "149 against 69", and the tests enforce two
(`PartitionFigures.rank_skipped` and `.rank_skipped_permuted`, `ARM_ROW`'s ninth capture group). Nothing
contradicts today - two counts satisfy a criterion asking for a count - but a later phase re-reading only
the contract can collapse them back and stay inside it. The contract is at 300 of 300 lines, so this is a
note for the rewrite rather than an edit now. `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` already exists.

**2. `TRACED_KEY`, `TRACED_PATH` and `TRACED_SEQUENCE` name two different spots in two files in one gate
command.** `tests/test_chart_arrival_probability.py:85-86` is `t6/d100/LJ/LJ:raise@2.5,HJ:raise@7.5` at
path `(1,2,0,0,0,0)`; `tests/test_chart_derivation.py:132-133` is `t6/d100/BB/BTN:raise@2.5` at
`(0,0,0,1,0)`, which `tests/test_spot_vocabulary.py` also uses. No live collision - the arrival file
imports only `selected` and `COMMITTED_NODES` from the derivation file - but four files in
`pytest_derived_chart` import each other by module, and this is the `A5`/`N12` shape one level down.

**3. Three names for 18,431, one spelled so a grep misses it.** `CELLS_AT_NON_ZERO_REACH = 18_431` in
`tests/test_derived_chart.py:117` and `tests/test_preflop_committed_charts.py:77`, and
`DECLARED_CELLS = 18431` in `tests/test_full_table_preflop.py:52`. Belongs with `A4`, which already
records eleven copied counts; the underscore-free spelling is what makes this one worse than the rest.

---

## What I re-derived, independently, and found sound

Recorded so a later reader knows these were measured rather than accepted.

- **No test in the tree is permanently red.** I pulled the failing source line for every one of the 123
  failures across the whole `tests` tree and read each expression. Every one resolves through the
  artifact, the sizing table, `chart_derivation`, `lookup`, `PreflopChartLibrary`,
  `generate_derived_chart_report` or a subprocess run of a stage-6 script. None compares two quantities
  both built from `tests/` and the frozen export. B1 and B2 are genuinely gone: four of the five tests in
  `test_chart_counterfactual_arms.py` are green today and the fifth fails only on
  `report.reverse_hand_ranks`, which stage 6 adds.
- **All ten re-measured partition rows reproduce, exactly, on all eight columns.** My own walk gives
  `the committed set (249, 7, 167, 208, 181, 433, 19774, 20279)`, `raises faced 0 (5,0,5,5,11,61,0,0)`,
  `raises faced 1 (25,0,25,25,21,112,0,0)`, `raises faced 2 (219,7,137,178,149,260,19774,20279)`,
  `hero=LJ (32,7,32,32,75,96,3224,3410)`, `hero=HJ (36,0,15,36,23,59,3972,4102)`,
  `hero=CO (44,0,18,32,22,72,4777,4876)`, `hero=BTN (47,0,28,33,14,66,4351,4416)`,
  `hero=SB (52,0,36,37,17,65,3450,3475)`, `hero=BB (38,0,38,38,30,75,0,0)`. Zero rows disagree with
  `PARTITIONS`, and `ARM_ROWS` carries the same forty figures in its own column order.
- **The two skipped counts are genuinely two, end to end.** They are separate dataclass fields, separately
  asserted at `test_chart_counterfactual_arms.py:263-267` and `:271-275`, separately pinned in `ARM_ROWS`,
  and separately captured by `ARM_ROW`'s eighth and ninth groups, so a report printing one number twice
  fails. They differ on every partition that skips anything (19,774 against 20,279 over the whole set) and
  both columns sum correctly by seat and by raises faced.
- **`RAISE_ACTION_INVERSIONS = 41` and `_INVISIBLE = 25` reproduce** under the merged reading, from my own
  walk: 41 and 25 post-merge against 43 and 28 pre-merge, and 11 against 9 over the 20 merged spots.
- **Decision 54's four-rule table reproduces**: restricted-to-closed 32 against 33 (over 53 full grids),
  skip rule 149 against 260, common-cell rule 42 against 69.
- **Every named case in decision 55 reproduces to the digit.** `t6/d100/BB/HJ:raise@2.5` raises `33` at
  1.80 against `22` at 70.15, with the unnamed `44`-over-`33` at 0.00 against 1.80;
  `t6/d100/CO/CO:raise@2.5,BB:raise@7.5` at 0.00 against 81.45; `t6/d100/BB/CO:raise@2.5` carries `33`
  over `22` at 0.00 against 8.13 with `99` and `88` both at 100.00; and the node the record mislabelled,
  `t6/d100/BB/CO:raise@2.5,SB:call`, does read `99` 0.00 against `88` 71.82, is at 8.98 percent exposure,
  and is refused by the squeeze clause alone. The three merge-resolved inversions and the one the merge
  reveals (`66` 66.23 over `77` 49.21 at `t6/d100/CO/HJ:raise@2.5`, raw raise 0.00 against 1.70) are all
  as written.
- **`ROWS_THE_RAKE_DID_NOT_MOVE = {("open","HJ")}` is correct and bites.** Measured against
  `gtopen_expectations`: the hijack's open sits 0.0851 from the raked reference and the next-nearest row
  is the cutoff's open at 0.7167, so the set equality at
  `tests/test_preflop_committed_charts.py:521` fails the moment a second row lands inside half a point.
  The mechanical note's proposed `min(gaps) > 0.5` would indeed have been permanently red; the per-row
  rewrite is the right fix. (`:522-524` is implied by `:521` and is harmless.)
- **The `_SOLVED`/`_PUBLISHED` purity split is correctly labelled and each half is the number claimed.**
  Over the same 18,431 cells at non-zero reach my walk gives 93.20 pure at 99 percent or more and 3.85
  mixed below 90 on the solve's own grid, and 93.48 and 3.66 after the merge.
- **The positive control exists and bites.** `tests/test_derived_chart_report_validators.py:601-609`
  asserts `run_report(tmp_path)` exits 0 and writes the file; it is red today because the generator
  refuses, which is exactly what N1 asked for.
- **The other tightenings bite.** `test_covered_spots_do_not_all_declare_the_same_hand_classes`
  (`test_full_table_preflop.py:693-700`) now asserts more than one distinct ordering over all 249 keys;
  `test_sample_comparison.py:690-700` now asserts the flags are non-empty, are real `bool`s, and carry
  both values; the three `CHART_PREFIX` sites in `test_postflop_fallback_components.py` each sit beside
  an assertion that separates a decision from a refusal; and N2's missing size guard is closed by
  `assert len(keyed) == SPOTS_OFFERING_A_PRICE` at `test_chart_conversion.py:300`.
- **The records match the rulings on the point that matters most.** `loop_stage.decision_items` parses
  all 55 items; decisions **50 and 53 each still carry exactly one `Answer:` line, their own**, so the
  supersession notices did not overwrite either recorded ruling. `unanswered_frozen` is empty, and every
  item declares a reversibility class. Decision 24 carries two identical `Answer:` lines, which pre-dates
  this commit. The contract's rewritten fourth-relation and rank-arm criteria say what the tests assert,
  and the renamed big-blind defect is measurable: the chart reads wider than the raked reference at LJ,
  HJ, CO and SB and narrower only at BTN, so "over-folds" was the wrong name and the flat's invariance is
  the right one.
- **Registration is clean.** All 42 test files are reached by a gate command; the six new files are named
  in `pytest_derived_chart` and the five that no specific command names run under the base gate's
  catch-all `pytest`. No registered path is missing or misspelled.
- Also reproduced from the export, since the freeze pins them: 249 committed on the 5 / 25 / 219 split,
  seats 32/36/44/47/52/38, coverage 98.5949 with the 51.9237 / 38.5422 / 8.1290 breakdown, 44 spots
  rounding to zero and 2 exactly zero, exposure extremes 9.8642 admitted and 10.0234 refused, 165 merged
  cells with 40 whole-weight flats and 73 at 99 percent or more, and the four relation counts 114 / 7 /
  181 / (87 wheel-ace + 94 no-story). The traced arrival spot's 55 classes at non-zero reach, thinnest
  cell at 1 basis point and 9 below the retired 200 floor all reproduce.
