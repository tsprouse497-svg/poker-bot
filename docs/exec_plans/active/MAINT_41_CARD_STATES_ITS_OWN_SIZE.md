# MAINT-41: A Record States Only Its Own Size

- **Task** `MAINT-41`
- **Mode** `maintenance`
- **Branch** `maint/41-card-states-its-own-size`, worktree `~/projects/poker-bot-worktrees/maint-41`
- **Base** `553f6f7931996c3feb4372a710a9845448f4c499`, which is `main`
- **Authorised by** Taylor, 2026-10-04, in session
- **Closes** `SOLVER-EXPORT-CARD-HEADROOM-COUNTS-THE-WHOLE-ARTIFACT-TREE`

## Objective

The preflop export's source card
(`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json`) stores
`size.headroom_bytes`, which is the 20 MiB cap less the bytes of the whole `data/artifacts` tree.
Any file committed anywhere under that tree makes the card stale, and six frozen tests then fail as
if the chart did not reproduce from its export. Phase 16 restamped the card to get past it
(`7d6866f`), and phase 21's lane did the same twice on 2026-10-04.

The fix: a committed record states only figures about itself. A figure about the whole tree is
measured at check time by the check that reads it. The cap stays exactly as strict: the total of
`data/artifacts` must stay under 20 MiB, checked by `scripts/check_file_sizes.py` in the base gate
and by the frozen byte-budget tests.

### Diagnosis, confirmed rather than copied

- `scripts/convert_preflop_export.py` `build_source_card` restamps `size` from the committed card and
  settles `headroom_bytes` to `BYTE_LIMIT - directory_bytes(...)`, where `directory_bytes` walks
  `ARTIFACTS_DIR.rglob("*")`. Its `--check` compares that text with the committed card, so the card
  text depends on every file in the tree.
- `scripts/extract_gtopen_preflop.py` `write_card` does the same at solve time.
- Five of the six tests run `convert_preflop_export.py --check` (or its `outputs()`) and fail on the
  card alone; the sixth, `test_the_committed_export_sits_under_the_limit_with_stated_headroom`,
  asserts `headroom_bytes == limit - total` directly.
- Reproduced in a scratch copy of `553f6f7` (`git archive`, outside every worktree): one
  `{"unrelated": true}` file under `data/artifacts/postflop/` turned exactly those six red, 6 failed.

## Survey: every committed record holding a figure about a directory it does not own

Method: every committed `.json`/`.yml` under `data/` and `verification/` scanned for byte, headroom
and tree figures, every script walking a tree (`rglob`, `tree_bytes`, `directory_bytes`) read, and
every committed report line printing one.

| Record | Figure | Covers | Decision |
| --- | --- | --- | --- |
| preflop source card `size.headroom_bytes` | cap less whole tree | `data/artifacts` | **Goes.** Not the card's. The check measures it. |
| preflop source card `size.limit_bytes` | the cap | policy in `check_file_sizes.py` | **Goes.** A second copy of the cap; the checker owns it. |
| preflop source card `size.bytes`, `bytes_per_node`, `bytes_per_expressible_spot` (+ note) | the export's own size, per node, per chart spot | the export and its derived chart | **Stays.** The card's own facts; none moves when an unrelated file lands. |
| postflop `index.json` `headroom_bytes` | cap less whole tree | `data/artifacts` | **Goes.** Same defect. Scratch probe: a file under `data/artifacts/preflop/` reddens `test_the_headroom_the_index_states_is_the_cap_less_the_whole_tree`. |
| postflop `index.json` `committed_bytes` | bytes of `data/artifacts/postflop/` | the index's own directory | **Stays.** The directory is the postflop artifact the index describes, and every file in it is written by the postflop campaign that rebuilds the index (`solve_postflop_sample.py --index-only`). Phase 16's contract requires the figure and that the generator refuse one that does not reconcile with disk. A file landing elsewhere no longer moves it. |
| postflop `determinism.json` `committed_bytes`, `second_run_bytes` | each cell file's own size | the cell | **Stays.** Owned. |
| `preflop/equity/preflop_eq169.source.json` `bytes` | the table's own size | the table | **Stays.** Owned. |
| `reports/active/latest_postflop_betting_report.txt` "bytes used, whole artifact tree", "headroom left" | live totals | `data/artifacts` | **Stays.** A generated report measured at generation time from `check_file_sizes`' own cap; the gate regenerates it every run. |
| `solve_postflop_sample.py` console lines printing `index['headroom_bytes']` | whole-tree headroom | `data/artifacts` | **Changes** to a live measurement, since the index no longer stores it. |
| `ARTIFACT_BYTE_CAP` / `BYTE_LIMIT` literals in `solve_postflop_sample.py`, `extract_gtopen_preflop.py`, `convert_preflop_export.py` | the cap | policy | **Read from `check_file_sizes.DIRECTORY_BYTE_LIMITS`**, as the betting report already does; the converter loses its copy outright. |

Prose that quotes a headroom figure (completed audit packets, review notes, phase 21's contract in
its own lane) is a snapshot of what its phase measured and is left alone; only the two completed
contracts whose criteria assert the stored figure are amended.

## Scope

Approved: the three writer scripts, `gtopen_source_card.py`, `postflop_artifact.py`, the card, the
index, `tests/test_solver_export.py`, `tests/test_postflop_artifact.py`, `verification/freeze.lock`,
`verification/mutations.yml`, the phase 10 and phase 16 contracts, and this task's packet and review
directory. Not the chart, not the sizing table, not any other artifact. No phase 21 work, no solver
run. The scope check's untracked-folder bug, filed only in phase 21's lane backlog, stays there.

## Delegation Plan

- No-delegation exception: the implementation is one data flow - two writers of the card, one writer
  of the index, and the two readers that validate them - and the six failing tests only agree when
  every piece lands together. A lane given any one piece could not run the tests that judge it, so
  splitting it buys a worse check, not parallelism. The coordinator implements it.
- Review is delegated, as it must be: one read-only reviewer that wrote none of it, briefed
  "read-only, no gate runs", asked what it held back.
- Status: implementation complete, review pending.

## Slices

- [x] Activate MAINT-41, reproduce the failure in a scratch copy, survey the class.
- [x] Card: converter and extractor stop writing `headroom_bytes` and `limit_bytes`; the card check
      refuses either on a card. Regenerate with `convert_preflop_export.py`; chart and sizing table
      byte-identical.
- [x] Index: solve driver stops writing `headroom_bytes`; the index importer refuses it; schema
      version 2; console lines measure live.
- [x] Tests: replace the two stored-headroom assertions with refusals of the stored copy, keep every
      cap assertion; add a test that copies the tree, adds an unrelated file, and shows the card
      still reproduces and the cap still fails one byte over. Re-freeze the lock.
- [x] Canaries for the card check, the index importer, the converter and the cap check. Each
      applied by hand in a scratch copy: each reddens exactly the new test meant to catch it.
- [x] Contract amendments, backlog entry closed, generated docs.
- [ ] Independent read-only review; fold in blockers.
- [ ] Gate, packet, closeout, gate, merge.

## Verification

`uv run python scripts/run_verify.py`, read from `reports/active/latest_verify.txt`, not the exit
code. Byte-identity of `data/artifacts/preflop/six_max_100bb_rakefree.json` and
`data/artifacts/preflop/sizings/six_max_100bb_rakefree.json` against `553f6f7` by `git diff --quiet`
and sha256.

## Outcome

Pending.

## Next Agent Bootstrap

Work in `~/projects/poker-bot-worktrees/maint-41` only. Read `CURRENT_TASK.yml`, then this plan's
unchecked slices. The gate plants live mutations for about fifteen minutes: stage named paths, never
`git checkout` a file. Phase 21's lane will need to rebase onto this once it merges.
