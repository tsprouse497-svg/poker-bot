---
phase_id: "21"
title: "The Flop Campaign"
depends_on:
  - "16"
required_gate_commands:
  - pytest_flop_campaign
  - generate_flop_campaign_report
required_reports:
  - reports/active/latest_flop_campaign_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_21_FLOP_CAMPAIGN.md
---

# Phase 21: The Flop Campaign

## Scope
Declared by MAINT-40 on 2026-09-26 from Taylor's ruling of that date: trust the solve and get more
of it, rather than measuring the bot first. Phase 16 built the machinery - the postflop key, the
index, the object storage format, the solve driver - and closed on a sample rather than on coverage,
which its decision 25 states. `data/artifacts/postflop/index.json` holds five flop decision points on
four boards for one preflop line, the button opening and the big blind calling, seen from both
seats; those four board classes are 44 of the 22,100 three-card flops. `data/artifacts/postflop/sample/`
carries four of the five cell documents, on three boards and 40 flops, and the fifth, `Ac8c3c`, is
indexed but its cell document is not in git. On every other flop the bot refuses, and on the flops it
holds it refuses one action later, because no decision point that follows a committed one is
committed. Phase 16's packet names both causes of its null table result: too few boards, and no
closure.

Three parts, in this order, because each one prices the next:

1. **Use every core.** GTOpen's server prints "solver threads: 5" on a ten-core Apple M4. The cause
   is in its source: it takes half of `available_parallelism()` on purpose, to skip hyperthreads on
   what its comment calls a memory-bound workload, unless `SOLVER_THREADS` overrides it. The M4 has
   no hyperthreads, so five is half the machine; whether ten is faster is unmeasured. Measure five
   against ten, set the thread count explicitly on every machine, and record it beside every timing
   from here on. `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`. If the setting is
   not enough, GTOpen is a read-only clone; a patch lives in a local clone and is recorded the way
   earlier phases recorded theirs.
2. **Pick the cloud machine.** Phase 16's decision 24 rules that the campaign runs on a rented box
   whose specification was left open. Solve and time one flop on a few candidates, re-prove
   determinism on the one chosen, since phase 16's proof holds only on the Mac it ran on, and choose
   on cost per solved flop with the memory a solve needs as a hard limit.
3. **Run the campaign.** Solve preflop lines in the order phase 16's decision 3 ruled, by how often a
   line is reached and can be served, into the index and object storage format phase 16 built, as
   many lines as cost and index allow, with the report naming which limit applied. Decision 3 rules a
   method rather than a list, and the order phase 16's report prints comes from the public corpus and
   disagrees with the chart's own arrival order at rank 1, so which order ranks the campaign is a
   stage-2 question. A solved board must also close: every flop decision point reachable from a
   committed one is committed, or refused by name for a reason other than not having been committed,
   such as the exploitability ceiling or an off-menu size. Phase 16's sample already refuses every
   next decision by name, so naming alone closes nothing, and without closure the campaign buys
   boards the bot still cannot play.
   `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`. Nothing is re-solved or
   hand-edited to look better.

Phase 16's rulings carry into this phase: full-precision f32 arenas (decision 20), the 0.40 memory
ceiling (decisions 20 and 22), an index plus object storage with no git LFS, the rented box governing
the campaign (decision 24), and no run on GTOpen's untested CUDA path until one flop is solved and
timed on the box. Stage 2 may reopen one only through a decision of its own; the memory ceiling is
`runtime-reversible` and moves together with the over-read the adopted memory-guard entry names. The
0.3%-of-pot target is already a code constant, `EXPLOITABILITY_TARGET_PCT_OF_POT`, and would become
the campaign's target silently, so stage 2 asks rather than inherits it.

Adopted from `backlog.yml`, each to be closed or carried by this phase, and each entry's adoption
note says what closes it: `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`,
`EVERY-ARENA-FIGURE-IN-THE-COST-RECORD-IS-A-QUANTIZED-ARENA-AND-FULL-PRECISION-ROUGHLY-DOUBLES-IT`,
`THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`,
`THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR`,
`A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`,
`A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`,
`POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`, `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`,
`THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`,
`THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`,
`QUANTIZED-ARENAS-PUT-A-FLOOR-UNDER-EVERY-EXPLOITABILITY-THIS-PHASE-MEASURED` and
`NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`.
`A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE` stays a `contract-update` task
for phase 16's own wording; this contract carries its two terms, that the rented box governs the
campaign and that determinism is re-proved on that box.

It depends on 16 alone, because 16 is the machinery it runs. Phase 19 depends on it, ruled by Taylor
on 2026-09-26, so that any rule of thumb 19 writes for a flop covers only what this campaign could
not solve, and 19 measures its merge against the bot this campaign leaves.

Phase 21 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not solve preflop spots the chart is missing - four-bets, limped pots, other stack depths. They
  need a re-solve of the preflop chart and are a separate phase. The committed preflop chart, its
  key and its artifact do not change here.
- Do not commit turn or river spots. Phase 16's decision 1 rules flop only.
- Do not group similar flops so that one solve answers several. `POSTFLOP-BOARD-ABSTRACTION` stays
  deferred in `docs/ROADMAP.md`, and suit isomorphism remains the only collapse permitted.
- Do not re-solve, hand-edit or drop a cell because its numbers look wrong. A solved cell is
  committed as solved or refused by the rule phase 16 ruled, and a finding about it is a finding.
- Do not add runtime solver calls, LLM-backed poker decisions, PokerNow automation, browser or
  platform observation, UI surfaces or large hand-history ingestion. `AGENTS.md` Boundaries.
- Do not spend on a cloud account, or provision anything outward-facing, before Taylor has ruled the
  provider, the machine candidates and a spending cap.

## Acceptance criteria

Every figure below was measured on 2026-09-26 against the tree at this phase's base commit; the
commands and scratch scripts are recorded in the ExecPlan. None is a target a later stage may tune.

### Part 1: every core

- **Every server the driver starts is given an explicit thread count through `SOLVER_THREADS`, and
  the driver refuses to start one without it.** Today nothing in `scripts/` or `src/` sets it, so
  every solve on record ran at GTOpen's default of half `available_parallelism()`: five threads on
  this Apple M4, whose ten cores are four performance and six efficiency cores
  (`hw.perflevel0.physicalcpu` 4, `hw.perflevel1.physicalcpu` 6), so ten will not be twice five.
- **Five threads against ten is measured, not assumed**, on one committed cell's configuration,
  unchanged, on a machine doing nothing else, and the report prints seconds per iteration at each.
  The committed record is 1.34, 1.93, 3.24 and 4.93 seconds per iteration on `9c8c7c`, `Ac8c3c`,
  `8c8d3c` and `Kh7d2c` at five threads, from `determinism.json` and each object's `solve` block.
- **A changed thread count does not change the answer.** GTOpen's CPU recursion collects its
  parallel children in order and sums in a fixed loop, so the five committed cells re-solved at the
  new count must reproduce their committed cell documents byte for byte and their per-combo
  strategies exactly. If they do not, the phase halts and Taylor is asked; no tolerance is set here.
- **Every solve record carries the machine it ran on as measured, the thread count, the engine (CPU
  or GPU, read back from `/api/status`) and the arena storage.** `MEASURING_MACHINE` in
  `postflop_solve_driver.py` is a hardcoded "Apple M4" string written into every object today, so a
  rented box would record the wrong machine; a test fails on a constant in its place. Peak resident
  memory is recorded per solve: no f32 solve on record has one, only its planned arena.
- If `SOLVER_THREADS` is not enough to use the machine, any GTOpen patch lives in a local clone and
  is recorded by commit and diff the way `docs/GTOPEN_SOLVER_NOTES.md` records the clone today.

### Part 2: the machine

- **No money is spent and no account is opened before Taylor rules the provider, the candidates and
  a spending cap.** Every rented hour is logged with its price, the running total is printed in the
  report beside the cap, and the campaign halts at the cap rather than past it.
- **Each candidate solves the same flop: `Kh7d2c` on the committed line and `solve_config.json`,
  unchanged.** It is the slowest board on record, 340 iterations in 1,677.4 seconds at five threads
  on the M4, and it is rainbow, which the cost model has never measured to target
  (`POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`). The report prints, per candidate: machine, thread
  count, engine, wall clock, iterations, achieved exploitability, peak memory, hourly price, and
  **cost per solved flop, the price times the wall clock**, which is what the choice is made on.
- **Memory is a hard limit, not a cost.** The four committed boards planned f32 arenas of 11.60 to
  12.24 GB as the driver reads them, which is 84 to 89 percent of the 13.74 GB ceiling this 34.4 GB
  machine gives at `MEMORY_CEILING_FRACTION` 0.40; the largest needs about 30.6 GB of RAM to pass
  the guard. A candidate whose ceiling cannot hold the arena is excluded with that reason and never
  ranked. On a GPU the bar is GTOpen's own VRAM estimate, 30.4 to 32.0 GB for the committed tree,
  so a 24 GB card is excluded.
- **Determinism is re-proved on the chosen box, not inherited.** The five committed cells are solved
  twice there, in two processes against a restarted server, and compared as `determinism.json`
  compares them: cell document byte for byte and per-combo strategies exactly. If the two runs on
  the box differ, the phase halts and Taylor is asked. Whether the box's result also matches the
  M4's committed digests is printed as a separate finding and is not a pass condition.
- **A GPU run happens only if Taylor rules to try one**, and only after one flop is solved and timed
  on the CPU of the same box. A GPU run that `/api/status` reports as `"gpu": false` is a silent CPU
  fallback and its timing is discarded. The report states that GTOpen's kernels sum with
  `atomicAdd`, whose order is not fixed, so the GPU determinism re-proof is expected to be at risk.

### Part 3: the campaign

- **The lines are taken in the order stage 2 rules, and the covered set is committed explicitly.**
  A line the committed chart cannot supply ranges for is excluded by name with that reason: the
  corpus's fourth most common flop line, `SB:call`, is a limp and the chart has no range for it.
  The driver today hardcodes button against big blind, so the ranges for any other heads-up line
  are derived from the committed chart by one function with a test, never typed.
- **A solved board closes.** On the committed menu a flop in this line has 14 decision points, seven
  for each seat, counted by walking GTOpen's `tree.rs` rules and checked against all four committed
  planned arenas to the byte; the index holds one or two of the 14 on each committed board. Every
  flop decision point reachable from a committed one is committed, or refused by name for a reason
  other than not having been committed, and a test walks every committed board's flop tree and
  fails on any reachable decision point that is neither. The driver harvests all of them from one
  solve before the server stops, because the solved tree itself is never saved.
- **The index budget is stated before the campaign starts, and the index does not silently
  outgrow git.** An index entry costs about 487 bytes and the whole 20 MiB `data/artifacts` cap has
  16,032,570 bytes of headroom, so 14 entries on each of 1,755 flops, about 12.0 MB a line, fits
  about 1.3 fully closed lines. Where the index lives beyond that is a stage-2 ruling. The cap is not
  raised and no git LFS is used.
- **The commit rule is phase 16's**: solved to the target stage 2 rules, capped at the iteration
  count it rules, committed at or under 1% of pot and refused above it, with the refused count in
  the index header. Each board is solved once in the campaign; a determinism re-solve never
  replaces a committed cell.
- **Every object is stored where stage 2 rules, with its digest in the index, and a machine that
  has not fetched it refuses with the not-fetched code.** The report prints how many flop classes
  a fresh clone can answer beside how many a machine that has fetched can.
  `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`.
- **The campaign stops at the first of three limits - the spending cap, the index budget, or the
  last line stage 2 admits - and the report names which one.**
- **The table result is re-run on the result, on phase 16's own terms**: 20,000 hands, seed 777,
  six seats of the composite strategy, printing postflop decisions, bets, showdowns and voided
  hands beside phase 16's two decisions, both checks, no bets and 5,365 voided hands. It is a
  measurement of coverage and closure, and no packet may call it a win rate.

### Evidence, reports, and gate

- **The report prints every figure this contract names and its generator re-derives each one from
  committed files, exiting non-zero on one that does not reconcile**: lines covered and excluded
  with reasons, boards and closed decision points per line, cells refused above 1% of pot, bytes
  used and headroom left, per-candidate costs, money spent against the cap, the thread comparison,
  both determinism results, the fresh-clone and fetched coverage, the share of the 22,100 flops the
  bot can answer, and the table result. Rainbow unpaired is 286 of the 1,755 classes and two-tone
  unpaired, 858 classes and 46.6 percent of all flops, has never been solved at f32 on this config;
  the report prints its coverage by texture so neither can hide.
- The gate passes with no GTOpen, no network and no fetched object, against the committed sample.
- Both new command IDs carry a mutation canary authored at stage 4, one targeting this phase's own
  new command, and `check_gate_bite` proves each bites.
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`,
  the audit packet carries plain-language pass/fail evidence, and deferred work is in `backlog.yml`.

## Required reports
- `reports/active/latest_flop_campaign_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_flop_campaign`
- `generate_flop_campaign_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- What was spent, on which machine, against the cap Taylor ruled, and what each solved flop cost.
- How many preflop lines and flops the bot can now play, beside how many it could before, and which
  limit stopped the campaign where it stopped.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not change this contract during implementation mode.
- Do not carry a laptop timing or a laptop determinism proof to the rented box as though it had been
  measured there.
- Do not report a campaign figure without the machine and thread count it was measured at.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- Every cell phase 16 committed stays byte-identical unless this contract names why it moves.
