# Phase 21 stage 6, decision 17: re-solve review

Read-only review by a subagent that did none of the work, 2026-10-04, of phase 16's four boards
re-solved on the clone at `b058335`: run A in the worktree, run B in a scratch copy, the determinism
record, the restamped export card, the regenerated betting report and the moved cell hashes. Findings
are kept as written; responses follow, and only the reviewer marks a blocker resolved.

## Blocker
1. The regenerated betting report still describes the pin's solve as if it were the committed cell, and now contradicts its own tables. `reports/active/latest_postflop_betting_report.txt` lines 160-163 say a committed cell was re-solved to the cap and diffed against "the strategy the repo holds", line 174 gives the committed run as 280 iterations at 0.2774%, line 181 a 33% bet at 80.86%, lines 197-199 say both solves bet essentially the whole range, and lines 316-326 say the button bets nearly its whole range against a caller who leads half its flops; the repo now holds a 300-iteration cell at 0.2892% where the button checks 46.34%, and the same report prints a 95.19% check and a 4.81% lead. Sources: `scripts/generate_postflop_betting_report.py:2088-2120`, which labels `deep_convergence_check.json`'s `committed_run` "the committed one", and `:2571-2583`, hard-coded prose with no figure behind it. The record stays as the pin's; the generator's framing must name the pin's cell at `479aaf2`, and the paragraph must be derived from data or removed. Breaks "Generated human docs remain current". Response: pending; the generator joins scope and a build lane fixes it.

## Non-blocker
1. ExecPlan lines 133-136 quote 3,704.9 seconds "in `determinism.json`" and assume the old meaning of "committed"; the re-solve slice is not ticked.
2. `determinism.json`'s `the_two_runs_are_distinct` and the report say the second run shared the machine; this time run B was faster on all four boards. The runs are distinct, the stated reason is false; the prose lives in the solve script and the generator.
3. Run A's `Kh7d2c` took 1,804.9 seconds for 340 iterations, about 5.3 a round against the sweep's 3.24; peak resident 12.41 GB against a 13.7 GB ceiling. Probably memory pressure or other load; it does not touch the cells, but no cost figure should be taken from it without `pmset -g log`.
4. `campaign/mac_resolve_at_thread_count.json`'s `what_this_is` and `docs/GTOPEN_SOLVER_NOTES.md:21` speak of "the committed cells"; true of the pin's cells at `479aaf2`, now ambiguous. Name the pin.
5. `backlog.yml` `A-CONTRACT-CLAUSE-ASSERTS-A-GAP-ITS-OWN-PHASE-THEN-CLOSED` says "against the committed 0.2774"; now the pin's cell.
6. The test file changed but the lock was not yet re-frozen. Response: re-frozen in the commit that files this note.

## Alignment
1. `AN-EDIT-THAT-SUPERSEDES-PROSE-OWES-A-RE-READ-AND-NOTHING-ASKS-FOR-ONE` and `A-GENERATED-REPORT-CAN-GO-STALE-WITH-THE-GATE-STILL-GREEN`; proposed: the betting report's continuation-bet narrative is hard-coded prose no figure checks.
2. `THE-PINNED-SOLVER-CARRIES-THE-AGGRESSOR-THROUGH-A-CHECKED-STREET`; proposed: no cell on the clone's tree has a deep-convergence diff, and the new `9c8c7c` cell is far more mixed than the one measured.

## What the reviewer verified, did not look at, and held back
Verified: every object names build `b058335` on the clone's branch, ten threads, CPU, f32; every
recorded arena equals the new-tree planned arena as the driver reads it, which is the proof the
server built the new tree; index and object digests match the files; every export's per-street counts
are 14, 6,419 and 1,549,968; run B equals run A everywhere with distinct wall clocks; the card diff is
`headroom_bytes` only; `solve_config.json` unchanged; the pin's objects preserved. Every cell passes
the commit rule (9c8c7c 300 rounds 0.2892%, Kh7d2c 340 0.2905%, 8c8d3c 340 0.2959%, Ac8c3c 280
0.2846%). The strategy moves fit the tree change and show no harvesting or seat error. Postflop tests
296 passed. Not looked at: the power log, the full export content, the cost report, the
`Ac8c3c` cell content, the spots-asked drop from 39 to 38. Held back: about 24 GB of exports sit only
in `~/poker-bot-solve-objects/postflop` with no second copy; and whether a 36.5% small bet on K72
rainbow is right is a poker judgment it did not make.
