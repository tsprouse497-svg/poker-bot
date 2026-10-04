# MAINT-41 independent review

I am a read-only review subagent and wrote none of this task. I read `git diff 553f6f7 HEAD` in the
`maint-41` worktree (19 files, commits `5d69cf4` and `f935e15`), the ExecPlan, the top
`scope_change_log` entry, `AGENTS.md`, the old and new `gtopen_source_card.py`, the index importer,
`scripts/check_file_sizes.py`, every `rglob` tree walk in `scripts/`, `src/` and `tests/`, every
committed `.json`/`.yml` under `data/` and `verification/`, and phase 21's lane diff
(`git diff main...HEAD` in `phase-21`, read-only).

I ran, in the worktree: `pytest tests/test_solver_export.py tests/test_postflop_artifact.py`
(98 passed), `ruff check --no-cache .` (clean), `check_scope.py` (exit 0), `freeze_tests.py --check`
("test freeze intact: 56 files"), `convert_preflop_export.py --check` (reproduces), and
`check_file_sizes.py` (exit 0). Every experiment that edits files ran in `git archive` copies in my
scratch directory. I did not run `run_verify.py`, `check_gate_bite.py` or `loop_stage.py`. The only
file I created in the worktree is this note.

## Blocker

- [resolved] Fixed by the coordinator: `THE-CHARTS-REPRODUCE-CHECK-IS-COUPLED-TO-EVERY-OTHER-ARTIFACT` is marked done and points at the item that carries what changed. Original finding: A second backlog item for the same defect is left deferred.
  `THE-CHARTS-REPRODUCE-CHECK-IS-COUPLED-TO-EVERY-OTHER-ARTIFACT` (`backlog.yml:7124`, status
  `deferred`, phase 14, which is completed) describes exactly this coupling: the converter restamps
  the card's `headroom_bytes` from `ARTIFACTS_DIR.rglob("*")`, so an unrelated artifact turns the
  chart's reproduce check red. It even names this task's fix ("the headroom figure moves off the
  card the chart's `--check` compares"). This task closes it in fact and leaves it open on paper.
  The gate cannot see a deferred item against a completed phase, so nothing else will catch it.
  Fix: mark it `done` with a one-line pointer to MAINT-41 and the closing commit, and regenerate
  `docs/BACKLOG.md`. `backlog.yml` is already touched by this task.

- [resolved] Resolved by precedent and a filing: the only text replaced is the false sentence the amendment corrects, which is how MAINT-39 amended phase 14 at its cap (phase 14's pointer to phase 17 was replaced in place, `git log -S` on that contract shows it). Nothing else was cut. The rewrite the cap now owes is filed as `POSTFLOP-BETTING-CONTRACT-IS-AT-ITS-LINE-CAP`, and the ExecPlan records the choice. Original finding: The phase 16 amendment deletes the original criterion text to fit the line cap.
  `PHASE_16_POSTFLOP_BETTING.md` was 299 lines at `553f6f7` and is 298 now. The diff removes the
  original sentence ("The solver export's source card is regenerated in the same task, since its
  `headroom_bytes` counts the whole artifact tree and ...") and writes the amendment in its place.
  Keeping the original and adding a two-line amendment would make it 301, over the 300 cap. `AGENTS.md`
  (Contract Amendments) says a contract that reaches the cap is due for a rewrite that "is its own
  `contract-update` task and is not done to make room mid-amendment". This is that, done
  mid-amendment, in `maintenance` mode. The phase 10 amendment, by contrast, keeps its original text
  and adds two lines (297 lines, fine). Neither the ExecPlan nor the scope log says the phase 16 text
  was removed or why. This needs a ruling rather than a quiet fix, since the two rules collide here:
  either restore the original sentence and file the phase 16 rewrite as its own `contract-update`
  item (the contract then keeps one stale present-tense clause until that task), or get Taylor's
  explicit ruling that this in-place edit is acceptable and record it in the ExecPlan and packet.

## Non-blocker

- Q1, cap strictness. Every cap assertion that existed at `553f6f7` is still there, unchanged:
  `check_file_sizes.py:52-54` (`total > limit` fails), `tests/test_solver_export.py:618`
  (`total < limit`), `tests/test_postflop_artifact.py:580` (`measured() <= ARTIFACT_BYTE_CAP`),
  `tests/test_solver_expectations.py:328` (the cap's value), and the extractor's halt at
  `scripts/extract_gtopen_preflop.py:240`, which now reads its limit from `check_file_sizes` instead of
  a literal. The only assertions removed are the two stored-copy equalities
  (`card["size"]["headroom_bytes"] == limit - total`, and the index's
  `declared == ARTIFACT_BYTE_CAP - measured()`). Neither added strictness beyond the `<`/`<=`
  assertions that remain: the old card check never required headroom to be positive (it was not in
  `_MUST_BE_POSITIVE`), and the old converter never halted on it. Net strictness is unchanged, and
  the new copy test adds a direct check that the gate's size check fails at limit + 1.
- Q2, byte identity. Blob hashes at `553f6f7` and `HEAD` are equal for the chart (`952f07f`) and the
  sizing table (`872553b`). `git diff --stat 553f6f7 HEAD -- data/` lists only the card and the
  index, so the export (`.gtx.gz`) is untouched. The card, loaded as JSON, equals the old card with
  `headroom_bytes` and `limit_bytes` dropped from `size`, and nothing else differs. The index differs
  in exactly three fields. `committed_bytes` falls 100,845 to 100,816, which is the 29 bytes of the
  removed ` "headroom_bytes": 16032570,` line, so it reconciles. The report's whole-tree delta of 86
  bytes is that 29 plus the card's 57 (two lines and one comma).
- Q3, bite. With the new test files dropped onto a `553f6f7` copy, 7 fail, including both
  `test_a_card_stating_a_whole_tree_figure_is_refused` cases and
  `test_an_unrelated_artifact_leaves_the_card_reproducible_and_the_cap_still_binds` (it fails on "does
  not reproduce from the committed export"), and `test_an_index_stating_headroom_is_refused`. The
  original defect reproduces on `553f6f7` too: one `unrelated.json` under `data/artifacts/preflop/equity/`
  reddens exactly the six preflop tests plus the index headroom test across the nine affected files
  (7 failed, 320 passed). The same probe on a `HEAD` copy gives 330 passed. Each of the four canaries
  has a `find` that occurs exactly once (I checked all 83 mutations, none off by count). Applied by
  hand in a copy, each reddens its named command: the card-check canary reddens both refusal cases,
  the importer canary reddens `test_an_index_stating_headroom_is_refused`, and the converter and
  cap canaries each redden only the copy test.
- The cap canary's description overclaims. `the-artifact-cap-stops-binding` says the size check "is
  the only thing that holds the cap". It is not: `tests/test_solver_export.py:618` and
  `tests/test_postflop_artifact.py:580` still assert the committed tree is under the cap. The canary
  bites; only the sentence is wrong. Suggest "is the only thing that holds the cap for a tree that is
  not the committed one" or just drop the clause.
- The converter canary bites for a broader reason than it names.
  `the-card-depends-on-the-artifact-tree-again` adds a `tree_files` key, and on an unchanged tree
  `convert_preflop_export.py --check` already exits 1 under it (I ran it in a copy). So it proves
  "the card text changed", not "the card moves when the tree grows". It still reddens the right test
  and the description is not false. Noting it because a canary that only shows when an unrelated
  file lands would be the exact proof, and this one is not that.
- Q4, survey, and `committed_bytes`. I found no other committed record storing a figure about a
  directory it does not own: `determinism.json` sizes are per cell, `preflop_eq169.source.json` sizes
  itself, `arena_bytes` is solver memory, and `saved_solve.bytes` is the saved solve. No other code reads
  `headroom_bytes` or `limit_bytes`, including scripts outside the gate
  (`generate_derived_chart_report.py:1192` reads only `node_counts`). No other copy of the 20 MiB
  number remains outside `check_file_sizes.py` except the deliberate restatement at
  `tests/test_postflop_artifact.py:46`. I agree `committed_bytes` should stay, because phase 16's
  contract requires it and removing it is a semantic change. But the ExecPlan's reason (line 49,
  "every file in it is written by the postflop campaign that rebuilds the index") is contradicted by
  phase 21's lane: `scripts/measure_postflop_thread_sweep.py:98` writes
  `postflop/campaign/thread_sweep.json` and never rebuilds the index, and phase 21's commit `8436788`
  says "three budget tests had gone red when they landed". On a `HEAD` copy, one unrelated file under
  `data/artifacts/postflop/` still reddens
  `test_the_index_declares_the_bytes_it_believes_it_costs_and_they_reconcile` and
  `test_the_command_publishes_on_good_input` (2 failed). So the narrower form of this defect remains
  for the postflop directory. Fix the ExecPlan's reasoning so it states that, and see the alignment
  item below.
- Q5, the phase 10 amendment. It is two lines, names the backlog id, says what is no longer true and
  what replaced it, and the claims hold: the gate's size check measures the total and the betting
  report prints the headroom (`reports/active/latest_postflop_betting_report.txt:451`). But it is
  inserted in the middle of its bullet, so the old next sentence, "That directory is covered by no
  size check at all today", now follows a sentence about the postflop betting report. Move it to the
  end of the bullet. No other completed contract asserts that the card or the index stores the
  headroom: phase 16's lines 156 and 213 are about the report, which still prints it.
- Q6, index schema version 2. Justified. The key set is exact (`_require_keys` with only
  `digest_authenticates` optional), so a version 1 index with `headroom_bytes` is already refused by
  key, and the bump makes the refusal name the version instead. Nothing pins version 1: no test,
  fixture or script in this tree or in phase 21's lane writes `index_schema_version` other than
  through `INDEX_SCHEMA_VERSION` (phase 21's `line_index_schema_version: 1` is a different record).
- Q7, frozen test edits. Each is needed by this fix alone. `complete_card()` drops the two keys
  because the card check now refuses them (otherwise `test_a_complete_card_reports_nothing` reds,
  which I saw on the old copy). The renamed test keeps the export-size and `total < limit` assertions
  and swaps only the stored-headroom equality. The postflop test replaces the stored-headroom equality
  with the importer refusal. Two new functions in `test_solver_export.py` (34 to 36, one is
  parametrized), postflop unchanged at 38, floor 1210 to 1212. The lock diff is exactly those two
  hashes, that count and that floor, and `freeze_tests.py --check` passes.
- Q8, phase 21's rebase. In a scratch clone, `git merge-tree` of this branch and
  `phase/21-the-flop-campaign` conflicts in `CURRENT_TASK.yml` and `STATUS.md` (these go once
  MAINT-41 closes to idle), the card, `index.json`, the betting report, `freeze.lock` and
  `mutations.yml`. `scripts/solve_postflop_sample.py` auto-merges, and the merged tree has no reader of
  `index['headroom_bytes']` or the card's removed keys. For the lane: take this task's card (its
  `2af8273` restamp is moot), rebuild the index with `solve_postflop_sample.py --index-only` (expect
  `committed_bytes` around 127,164, which is the lane's 127,193 less the 29-byte line), regenerate the
  betting report, union the two `mutations.yml` tails and re-freeze. Worth telling the lane that its
  campaign records will still move `committed_bytes` (see above), so it should keep rebuilding the
  index when it writes them.
- The scope log says canaries were added "for the two readers and the cap check". There are four; the
  converter canary is not mentioned. Trivial.

## Alignment

- File a backlog item: the postflop index's `committed_bytes` counts every file under
  `data/artifacts/postflop/`, and writers other than the index rebuild (phase 21's thread sweep and
  re-solve records under `postflop/campaign/`) put files there. So the index goes stale and two tests
  plus the report generator go red whenever they land. This is the same shape as the defect this task
  fixed, in a smaller directory. Options are for `committed_bytes` to cover only what the index
  describes (index and sample, which the report already separates as "the committed index and sample:
  56,762"), or for campaign records to live outside the directory the index sizes, or for every writer
  there to rebuild the index. Each changes phase 16's criterion, so it is `contract-update` work.

## What was not checked

- The full gate and `check_gate_bite`, by instruction. I judged the canaries with pytest on copies,
  not with the real mutation runner.
- Whether `solve_postflop_sample.py --index-only` actually produced this index, as opposed to a hand
  edit. The result reconciles with disk, which is what the tests check.
- A full resolved rebase of phase 21 with its tests run. I only computed the conflict list and grepped
  the merged tree.
- The audit packet, which does not exist yet.
- `extract_gtopen_preflop.py` end to end. It needs a running GTOpen server; I read it only.

## Held back, not defects of this task

- A one-byte disagreement about the cap that predates this task: `tests/test_solver_export.py:618`
  asserts `total < limit`, while `check_file_sizes.py` and `tests/test_postflop_artifact.py:580` accept
  `total == limit`. The new copy test asserts that a tree at exactly the limit passes the gate's check,
  so the repo now states both. Harmless until a tree lands exactly on 20,971,520 bytes.
- `tests/test_postflop_query_recording.py:45` is a frozen docstring that says
  `tests/test_solver_export.py:656` "recomputes headroom from the source card". That is now false, but
  it is a snapshot in a completed phase's frozen test, the line number had already drifted, and nothing
  reads it.
- `reports/active/latest_postflop_betting_report.txt` still prints whole-tree bytes and headroom, so it
  goes stale on any unrelated commit. Nothing reds on that; the gate regenerates it. I agree with the
  ExecPlan's "stays".
