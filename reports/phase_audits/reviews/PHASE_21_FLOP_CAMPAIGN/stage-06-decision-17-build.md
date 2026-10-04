# Phase 21 stage 6, decision 17: tests and build review

Read-only review by a subagent that wrote none of the work, 2026-10-04, of commit 7ff2a4b: the frozen
tests re-opened for decision 17's tree and the solve path pointed at the patched clone. Round 2 confirmed both blockers fixed, found no new one, and named the cost script's rebuild-while-running gap as still open, since fixed. Findings are
kept as written; the coordinator's response follows each, and only the reviewer marks a blocker
resolved.

## Blocker
- [resolved] **A stale binary is accepted after a branch switch, and the record then names the wrong build.** `check_binary_is_current` refused only a binary older than HEAD's commit time, so checking the clone out to an older commit left a newer binary that passed, and the record named the older commit while the binary built the new tree. Also: the build was read once per run though each board starts a fresh server, the cost script read a rebuilt file for a server started before the rebuild (round 2: not fixed by the first response; the cost script now refuses a binary modified after the running process started), and no test or mutation covered any of it. Response: the check also refuses when any file git tracks under `crates/`, `Cargo.lock` or `Cargo.toml` is newer than the binary, which is what a checkout leaves; its docstring states what it does not catch (it compares times, not compiled bytes); every server start re-reads the build and refuses a change mid-run; the cost script refuses a server that is not on this machine. `tests/test_flop_campaign_solver_build.py`, 16 tests on a real git repository in a temporary folder, covers the review's case and each refusal, and is in `pytest_flop_campaign`. Six canaries were added, and the coordinator applied each by hand and saw it fail its tests, every file restored byte for byte. The tree comparison that would catch a wrong binary whatever git says is filed as `THE-SOLVE-DRIVER-NEVER-CHECKS-THAT-THE-SERVER-BUILT-THE-TREE-THE-PORT-PLANS`.
- [resolved] **`tests/test_flop_campaign_report.py:242` still pins the pin's figure**, `river=1_477_055` in the test of a board one river decision point short, which on the new tree is 72,913 short. Response: now `1_549_967`; a wider grep for neighbours of every old figure found no other.

## Non-blocker
- Test hunks gone through one by one: no test dropped, no tolerance widened, every old pin moved or kept under the pin's rule, two tests stronger. Every new figure re-derived from a fresh build of the counter.
- `test_each_river_card_gains_the_same_thirty_one_decision_points` was misnamed (the small blind line gains 32). Response: renamed, assertions unchanged.
- Phase 16's gate holds today: `tests/test_postflop_*.py` 288 passed.
- The re-solve will break `TestPhase16StaysByteIdentical::test_each_committed_cell_document_is_unchanged`, which pins the old cells' sha256. Response: it cannot be restated before the re-solve exists; a further re-open, for that pin alone, follows the re-solve, with the sample and `determinism.json` paths joining scope then.
- The export path matches the clone's route and format; each export is about 6 GB a board, about 24 GB for phase 16's four, with no free-disk check. Response: recorded in the ExecPlan's re-solve slice; this Mac has about 700 GB free.
- The bulk export calls `ensure_symmetric`, so "reads the arenas" was loose. Response: the solver notes now say it does what `/api/node` does before reading, and changes no solved value.
- The cost script labelled a remote server with the local build. Response: a non-local `--url` is refused.
- Decision 17's answer bracket held coordinator text. Response: moved outside the bracket as a coordinator's note.
- The ExecPlan quoted 48.50 GB and 18.53 GB. Response: now 51.24 GB and 19.62 GB on the new tree, the pin's figure named.
- `--untracked-files=no` ignores a new uncommitted source file. Response: carried; the tree comparison filed above covers it.

## Alignment
- `PHASE-21-CONTRACT-CARRIES-THREE-MEMORY-FIGURES-ITS-OWN-TREE-RULES-CONTRADICT`: closed, the rewrite carries all three corrections.
- `THE-SOLVE-DRIVER-NEVER-CHECKS-THAT-THE-SERVER-BUILT-THE-TREE-THE-PORT-PLANS`: filed from the reviewer's proposal.
- `DECISION-17-SOLVE-PATH-REFUSALS-NEED-MUTATION-CANARIES`: filed from the reviewer's proposal; six canaries added in this re-open, closing at the stage 7 sweep.

## What the reviewer did not look at, when asked
The contract rewrite beyond the lines cited, phase 16's amendment, decision 18's patch, whether the
GTOpen tests pass (not run), and whether `lsof`'s first text entry is always the executable. Held
back: the bot plays the flop from old-tree cells until the re-solve, a known consequence of the
ruling; no code today mishandles an out of position river bet after a checked-through turn, because
turn and river refuse wholesale, and a future harvest must read the legal actions from the export
rather than assume who holds the initiative.
