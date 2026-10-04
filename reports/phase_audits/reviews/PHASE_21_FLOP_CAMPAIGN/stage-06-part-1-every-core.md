# Phase 21 stage 6 review: part 1, every core

Reviewer: independent read-only review subagent, which wrote none of the work it reads. Date
2026-10-04. Scope: `git diff 51f407f 055f9c8` - `solver_artifacts/postflop_threads.py`,
`postflop_machine.py`, `postflop_determinism.py`, `postflop_solve_driver.py`;
`scripts/solve_postflop_sample.py`, `scripts/measure_postflop_thread_sweep.py`; the records
`data/artifacts/postflop/campaign/thread_sweep.json` and `mac_resolve_at_thread_count.json`;
`docs/GTOPEN_SOLVER_NOTES.md`; the backlog, scope and ExecPlan edits.

What I ran: `uv run ruff check --no-cache` and `ruff format --check` on the six touched code files;
`uv run python -m pytest tests/test_flop_campaign_threads.py tests/test_postflop_solve_driver.py
tests/test_flop_campaign_costs.py -q` and `tests/test_flop_campaign_report.py`; sha256 of the four
re-solved objects against the committed run's objects, and a full load of each pair; scratch scripts
that ran `resolve_document` on the real re-solve and on nine perturbed scratch copies of it; the
sweep's medians and spreads recomputed from `runs`; `pmset -g log` and `pmset -g custom` for the
sweep's window; a diff of the scratch tree's solve code against `055f9c8`; GTOpen's `init_rayon` at
`~/projects/gtopen`. No gate, `check_gate_bite`, loop driver, server or solve was run. I edited
nothing tracked.

## Blocker

- **[resolved] in `8436788`, verified in round 2 below.** **No solve object records the engine,
  and the one function that requires it is used only by the tests.** The contract: every solve record carries the machine as measured, the thread count, the
  engine read back from the server, and the arena storage, plus peak resident memory per solve.
  `postflop_machine.solve_record` (`postflop_machine.py:270`) enforces all of it, and stage 4's
  tests pin it, but no writer calls it. `write_object` (`scripts/solve_postflop_sample.py:665`)
  builds its own `solve` dict with machine, threads, arena storage and peak, and no engine;
  `check_engine` is called only by the thread sweep. The re-solve's four scratch objects confirm it:
  their `solve` blocks have no `engine` key. The deep-check path (`deep_check_document` at `:1401`,
  `write_deep_object` at `:1540`) records neither engine nor peak memory, and decision 13's
  settling runs to the 1,200-round cap are the kind of solve that path makes. `write_object` also
  accepts `peak_resident_bytes: None`, which `Server.stop` leaves when the process has already
  exited (`:491-493` returns before `wait4`), and `solve_record` would refuse that.
  Failing scenario: the chosen box's determinism solves and six texture solves in part 2 go
  through `solve_postflop_sample.py`, the only solve route, and write records with no engine; on
  the GPU trial a run GTOpen quietly moves to the CPU is written down like any other, which is the
  silent fallback `check_engine` exists to discard. Repair: route every solve-object writer through
  `solve_record`, with the engine from `check_engine` on the final `/api/status` that `run_solve`
  already holds, and the peak from `Server.stop`. This is code only. No committed record needs
  re-solving: `thread_sweep.json` already carries `engine` per run, and the re-solve record is a
  comparison, not a solve record.

## Non-blocker

- **The re-solve is a real re-solve, not a copy.** Every object digest differs from the committed
  one, gzip and decompressed alike (`srp-Kh7d2c` `a43935d5...` against `11be015c...`, and so on for
  all four). Wall clocks differ on every board (1112.1 s against 1677.4 on `Kh7d2c`, 706.2 against
  1035.9 on `8c8d3c`, 300.5 against 375.6, 320.5 against 616.0), and the files' modification times
  (08:39, 08:50, 08:55, 09:01) agree with those solves running back to back from about 08:20.
  Each server log reads `solver threads: 10`. Iterations and exploitability are equal, and the
  whole `nodes` payload of every object is equal to the committed one, not only the acting
  player's rows. The scratch tree's solve code matches `055f9c8` apart from the later move of
  `compare_node_payloads` and the new `resolve_check`. The comparison can fail: on scratch copies
  it rejected one combo moved by 1e-12, the last action of the last combo moved by 1e-15, a
  dropped combo, a changed iteration count, the committed object copied in (caught as identical
  wall clocks), one digit changed in a held cell (bytes and digest), and the fifth cell's weight
  moved by 0.001 (digest). It refuses the committed tree as the re-solved one.
- **One perturbation it missed.** `compare_node_payloads` (`postflop_determinism.py:34`) reads only
  the acting player's `strategy` rows, so a change to the other player's `reach`, `ev` or `eq` at
  the same node passed as reproduced. It does not touch the verdict here, because I found the
  whole node payloads equal, but `one["nodes"] == two["nodes"]` is a stronger and simpler check
  and would have caught it.
- **Nothing refuses a re-solve at the wrong count.** `resolve_document` records `threads` per cell
  but never checks that every re-solved object ran at one count, or at a count other than GTOpen's
  default, which the contract says would prove nothing. `resolve_check` takes the record's
  headline `threads` from the first object alone. Here all four objects read 10, so the record is
  true.
- **Held cell bytes start as copies.** The re-solve ran in a copy of the repo, so before it ran,
  `sample/*.json` already held the committed bytes, and comparing bytes cannot tell a rewritten
  cell from one the re-solve never wrote. Here the modification times show all four rewritten, and
  the per-combo check reads the fresh objects, so the verdict holds. Emptying `sample/` before a
  re-solve would close the gap.
- **The sweep is sound and 10 threads is the right choice for this Mac.** Recomputed from `runs`:
  medians 6.088, 4.867, 3.750, 3.245 seconds per iteration at 3, 5, 8 and 10 threads, and spreads
  1.450, 1.362, 0.636, 0.150, matching the record. The run order is 3, 5, 8, 10 three times
  over. The counts follow the contract's rounding, and the fastest median picks 10. Ten wins every
  round on its own (3.38, 3.23, 3.24 against eight's 4.23, 3.75, 3.59). Two independent figures
  agree with it: the AC-powered 10-thread `Kh7d2c` re-solve ran at 1112.1 / 340 = 3.27 s/it,
  against the battery sweep's 3.24, and the committed five-thread run's 4.93 sits against the
  sweep's 4.87. So running on battery did not move the measurement. `pmset -g custom` shows
  low-power mode off on both battery and AC. The battery correction in the conditions note is true
  (`pmset` reads `Using BATT` from 09:06:42 to 10:42), and no sleep, wake or thermal event falls
  inside a run.
- **What the conditions note leaves out.** (a) The first round ran slow at every count (7.44, 6.05,
  4.23, 3.38) against rounds two and three, so the 3- and 5-thread spreads are almost entirely
  round one rather than noise. The note says the machine "started warm" but not that this is what
  it cost. (b) `thermal_state_before` and `thermal_state_after` read "No CPU power status has been
  recorded" on every run, because `pmset -g therm` reports nothing on Apple silicon. So the note's
  promise to discard a run that overlaps a thermal event covers emergency events only. Throttling
  is invisible to the script on this machine. The record should say both.
- **Ten threads on this Air may be what tripped the emergency sleep.** The Thermal Emergency Sleep
  came at 09:01:31, 15 seconds after 41 minutes of 10-thread solving ended (`EXIT 0` at 09:01:16).
  Part 2 solves on the rented box, so this does not change the choice. But the
  `docs/GTOPEN_SOLVER_NOTES.md` threads row should warn that long all-core runs on this machine
  have ended in a thermal emergency, before anyone runs another Mac solve at 10.
- **The sweep record keeps only one machine.** `measure_postflop_thread_sweep.py:353-356` writes
  `{"machines": [record]}` over the file. Run with the default `--output` on a rented candidate, it
  replaces the Mac's record. The contract asks for a sweep on every machine the phase solves on, and
  the report must print each, so part 2 needs to merge by machine or write one file per machine.
- **A field name that no longer means what it says.** `SolveOutcome.machine`
  (`postflop_solve_driver.py:474`) still holds the memory-ceiling text. This predates the phase,
  and nothing reads it, but in a phase that now measures the machine, a field called `machine` that
  holds a ceiling will mislead someone.
- **Behaviour checks that passed.** `server_environment` refuses `None`, a bool or a count below
  one, and overrides an inherited `SOLVER_THREADS`. Both solve entry points call `begin_run`, which
  refuses a missing `--threads`. `check_printed_threads` matches GTOpen's own line,
  `println!("solver threads: {threads}")` in `init_rayon`. That check matters: GTOpen falls back to
  its default without a word on a value it cannot parse, and `SOLVER_THREADS=0` would hand rayon
  its all-cores default while printing 0. The refusal below one blocks that. The driver's
  ceiling is `memory_ceiling_bytes` of `sysconf`'s reported RAM. `check_memory_ceiling` is the only
  refusal on planned arena, and it prints the margin as 4.86% (2^20 / 10^6 - 1). `ru_maxrss` is
  scaled correctly for each platform, in bytes on Darwin and kibibytes on Linux.
- **Lint and tests.** `ruff check` passes on all six files. `ruff format --check` would reformat
  `postflop_solve_driver.py` at `:442-447`, but `51f407f` was already off by the same lines, so the
  drift predates this work. The formatter is not gated. The three named test files: 101 passed and
  14 errors. All 14 are `ModuleNotFoundError: postflop_campaign_costs`, part 2's module, which is not
  built yet. `test_flop_campaign_report.py`: 3 passed and 23 errors, on the report generator, which
  is part 3's. Neither is a regression; both are frozen reds waiting for later slices.

## Alignment

- `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT` now has its Mac answer: five
  threads to ten takes `Kh7d2c` from 4.87 to 3.24 s/it, 1.5 times as fast, and the answer does not
  change. When the entry closes, its note should carry those figures and say that the entry's
  1.11 against 1.79 ns per node-hand puzzle is still unexplained by thread count. Every committed
  phase 16 run used the same five threads, so that gap came from something else.
- `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`: decision
  14's default is implemented as written, with the margin in the one refusal. Nothing more is owed
  in part 1.
- `THE-REPO-S-FORMATTER-IS-NOT-IN-THE-GATE-AND-THIRTY-NINE-TEST-FILES-DIVERGE` covers the format
  drift in `postflop_solve_driver.py`.

## Round 2, 2026-10-04: the repair in `8436788`

Scope: `git diff 256c5c3 8436788`, and `7da38c6`, which only regenerates
`reports/active/latest_postflop_betting_report.txt`. Same reviewer, same rules: no gate, server or
solve run, nothing tracked edited. I ran one scratch script against HEAD `7da38c6`, which sent each
fix through the failing scenario round 1 named. I also ran `ruff check` on the touched code, and
pytest on the threads, driver, artifact, betting report and costs test files.

### Blocker

None. Round 1's blocker is resolved:

- `write_object` and the deep check now build their `solve` block through
  `RunConditions.solve_block`, which calls `solve_record`. The engine is read back with
  `check_engine` from `SolveOutcome.final_status`, the last `/api/status` that `run_solve` now
  keeps. My scratch script used scratch outcomes, no server:
  - Asked for the GPU while the server reported `gpu: false`: refused (`SolveDriverError`).
  - A status with no `gpu` field: refused.
  - A peak of `None`: refused (`SystemExit`). A peak of 0: refused (`ValueError` from
    `solve_record`).
  - A CPU run with a real peak: accepted, with `engine`, `machine`, `threads` and
    `peak_resident_bytes` present.
- `Server.stop` now reaps with `wait4` even when the process has already exited. On a child that
  had already exited it returned a peak (1,654,784 bytes) rather than `None`. Nothing else in the
  script calls `poll` or `wait`, so nothing reaps the child first.
- The deep check writes its object in `finish_deep_check`, after the server stops, with engine and
  peak from the same `solve_block`.

### Round 1 non-blockers, checked

- **Whole-node comparison.** `compare_node_payloads` now returns `whole_node_identical`, and
  `per_combo_identical` requires it. A 1e-9 change to the non-acting player's `reach` now fails,
  where round 1 saw it pass.
- **Mixed or default thread counts.** `check_resolve_threads` refuses objects that disagree (one
  set to 8 among 10s) and objects all at 5, GTOpen's default on this machine. On the real re-solve
  objects it returns 10.
- **A tree that was never emptied.** `resolve_document` refuses the round 1 scratch tree, which has
  no `resolve_run.json`. With the marker present and one held cell deleted, as `--resolve` would
  leave a board it skipped, the cell is reported missing and `reproduced` is false. With the marker
  and all cells present, `reproduced` is true and `threads` is 10. `prepare_resolve_tree` refuses a
  git checkout (a worktree's `.git` file counts) and an object directory that is not empty.
- **The sweep file keeps every machine.** `merged_sweep_document` replaces only a record with the
  same platform, CPU model, logical processor count and memory.
- **The field name.** `SolveOutcome.machine` is now `memory_ceiling`.
- **Lint and tests.** `ruff check` passes. The artifact and betting report budget tests pass on
  the rebuilt index: 205 passed. The 14 errors are still part 2's unbuilt
  `postflop_campaign_costs` module.

### Are the new record texts true, and do they add no measurement?

- **The sweep note.** Every figure re-derives from `runs`:
  - round one: 7.440, 6.052, 4.228 and 3.377 s/it
  - rounds two and three: 5.990 to 6.088, 4.690 to 4.867, 3.592 to 3.750 and 3.227 to 3.245 s/it
  - spreads without round one: 0.098 and 0.177

  The `pmset -g therm` sentence is true. No new measurement.
- **`checks_added_after_this_record`.** Checks (1) and (2) hold as stated: I reran both on copies
  of the scratch objects. All five nodes are whole-identical, and all four objects ran at 10
  threads.
  - **One figure is misattributed.** The record says the four held cells' modification times are
    08:39, 08:50, 08:55 and 09:01. The four held cells are at 08:39:03 (both `Kh7d2c` cells),
    08:50:52 and 08:55:54. 09:01 is the fifth cell, which sits in object storage and is not held.
    My round 1 note gave those four times for the objects, which is where they belong.
  - The fix is one line: "the four held cells' modification times (08:39 for both `Kh7d2c`
    cells, 08:50, 08:55)". It is a non-blocker, but it is a wrong figure in a committed record and
    should be corrected before `--advance`.
- **The heat row in `docs/GTOPEN_SOLVER_NOTES.md`.** Both dates are real Thermal Emergency Sleeps
  in `pmset -g log` (2026-10-03 21:57:43 and 2026-10-04 09:01:31), and "the cause is not proven"
  is honest. But the first did not follow "a long all-core solve". It followed the first, abandoned
  sweep, which ran 3, 5 and 8 threads from 21:18, and then 10 threads from 21:44:14 for about six
  minutes. A `Clamshell Sleep` (lid closed) was logged at 21:43:29 just before that run.
  Non-blocker: reword to "a long solve" and mention the lid.

### The lane's held-back points

- **(a) An engine or peak refusal stops the whole `--all` run with a traceback.** Confirmed.
  `write_object` runs after `server.stop()`, outside the per-board `try`. `SolveDriverError` from
  `check_engine` and `SystemExit` from a missing peak both propagate out of `main`. The cost of
  that is larger than a traceback: boards finished earlier have written their objects, and their
  held cells through `record_cell`, but `objects.json` and `index.json` are written only after the
  loop. So the tree is left with new cells and a stale manifest and index.
  - It fails closed: nothing wrong is recorded as right. `--resolve` would report the missing
    cells, and the gate's budget tests would catch the stale index.
  - Its realistic trigger is the GPU trial, which solves one board. So this is a non-blocker.
  - Recommended before part 2's multi-board runs on the box: call `check_engine` inside the
    per-board `try`, where `final_status` already exists, so a fallback counts as one refused
    board and the loop goes on. Keep the peak check after `stop`, inside its own `try`.
- **(b) Two rented boxes of one instance type are one sweep entry.** Acceptable. The contract asks
  for a sweep per machine, and an instance type is a fixed hardware specification. Part 2's budget
  pays for one sweep per candidate, not per box.
  - Two caveats. A second sweep of the same type silently replaces the first, so the script should
    print that it replaced a record. And `MemTotal` can differ by a few kilobytes between kernels,
    so the same type can also end up as two entries, which is harmless.
  - What makes it safe is that every solve object records its own measured machine.
- **(c) The old re-solve record cannot pass the new marker check.** Acceptable without a re-solve.
  The marker guards only the held cell bytes. In this run those cells were provably rewritten:
  their modification times match their objects. Every strategy check reads the fresh objects, and
  those now pass the whole-node and thread-count checks.
  - A second 41-minute all-core run on this Air, with its thermal record, would buy nothing
    stronger.
  - The record should name the code that wrote it (`055f9c8`), since the current
    `--resolve-tree` refuses that scratch tree and cannot regenerate the record.
