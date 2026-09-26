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
which its decision 25 states. `data/artifacts/postflop/index.json` holds five flop decision points
on four boards for one preflop line, the button opening and the big blind calling, seen from both
seats; those four board classes are 44 of the 22,100 three-card flops.
`data/artifacts/postflop/sample/` carries four of the five cell documents, on three boards and 40
flops, and the fifth, `Ac8c3c`, is indexed but its cell document is not in git. On every other flop
the bot refuses, and on the flops it holds it refuses one action later, because no decision point
that follows a committed one is committed. Phase 16's packet names both causes of its null table
result: too few boards, and no closure.

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
3. **Run the campaign.** Solve preflop lines in the order phase 16's decision 3 ruled, by how often
   a line is reached and can be served, into the index and object storage format phase 16 built, as
   many lines as cost and index allow, with the report naming which limit applied. Decision 3 rules
   a method rather than a list, and the order phase 16's report prints comes from the public corpus
   and disagrees with the chart's own arrival order at rank 1, so which order ranks the campaign is
   a stage-2 question. A solved board must also close: every flop decision point in its line, for
   both seats, committed from the one solve, or all of them refused together. Phase 16's sample
   already refuses every next decision by name, so naming alone closes nothing, and without closure
   the campaign buys boards the bot still cannot play.
   `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`. Nothing is re-solved or
   hand-edited to look better.

Phase 16's rulings carry into this phase: full-precision f32 arenas (decision 20), the 0.40 memory
ceiling (decisions 20 and 22), an index plus object storage with no git LFS, the rented box
governing the campaign (decision 24), and no run on GTOpen's untested CUDA path until one flop is
solved and timed on the box. Phase 16's contract calls the rented box NVIDIA; whether the campaign
needs a GPU at all is reopened at stage 2 rather than assumed either way. Stage 2 may reopen one
only through a decision of its own; the memory ceiling is `runtime-reversible` and moves together
with the over-read the adopted memory-guard entry names. The 0.3%-of-pot target, the 1,200-iteration
cap and the 1% refusal ceiling are already code constants in `postflop_artifact.py` and would become
the campaign's silently, so stage 2 asks rather than inherits them.

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
  provider, the machine candidates and the benchmark cap below.

## Acceptance criteria

Every figure below was measured on 2026-09-26 against the tree at this phase's base commit; the
commands and scratch scripts are recorded in the ExecPlan. None is a target a later stage may tune.

### Part 1: every core

- **Every server the driver starts is given an explicit thread count through `SOLVER_THREADS`, and
  the driver refuses to start one without it.** Nothing in `scripts/` or `src/` sets it today, so
  every solve on record ran at GTOpen's default of half `available_parallelism()`: five threads on
  this Apple M4, whose ten cores are four performance and six efficiency cores
  (`hw.perflevel0.physicalcpu` 4, `hw.perflevel1.physicalcpu` 6), so ten will not be twice five.
- **The count used is the fastest measured, and it is measured on every machine the phase solves
  on**, never carried from another. The counts timed are GTOpen's default and a quarter, half, three
  quarters and all of the machine's reported cores, rounded, with repeats dropped - on this Mac 3,
  5, 8 and 10 - each three times interleaved, as a fixed stretch of 100 iterations of one committed
  cell's configuration, unchanged, on a machine doing nothing else. The median of the three decides.
  The report prints each run's seconds per iteration and the spread. One run per count is not
  enough: the committed runs of `9c8c7c` read 1.34 and 2.16 seconds per iteration on the same
  configuration, because the second shared the machine. The committed first-run record is 1.34,
  1.93, 3.24 and 4.93 seconds per iteration on `9c8c7c`, `Ac8c3c`, `8c8d3c` and `Kh7d2c`, from
  `determinism.json`.
- **A changed thread count does not change the answer.** GTOpen's CPU recursion collects its
  parallel children into an ordered vector and sums in a fixed loop, so phase 16's four boards
  re-solved on the M4 at ten threads, whatever count is fastest, since five would prove nothing,
  reproduce the four committed cell documents byte for byte,
  the fifth cell's strategy digest, and every per-combo strategy exactly. If they do not, the phase
  halts and Taylor is asked; no tolerance is set here.
- **Every solve record carries the machine it ran on as measured, the thread count, the engine
  (CPU or GPU, read back from the server) and the arena storage.** `MEASURING_MACHINE` in
  `postflop_solve_driver.py` is a hardcoded "Apple M4" string written into every object today, so a
  rented box would record the wrong machine; a test fails on a constant in its place. Peak resident
  memory is recorded per solve: no f32 solve on record has one, only its planned arena.
- If `SOLVER_THREADS` is not enough to use the machine, any GTOpen patch lives in a local clone and
  is recorded by commit and diff the way `docs/GTOPEN_SOLVER_NOTES.md` records the clone today.
- **The driver's memory guard is tested as behaviour**: a test proves the ceiling follows the
  machine's reported memory, and one ties the committed configuration to the body the driver posts.
  The arena over-read is repaired by one of the three routes its entry names, in the same decision
  as any move of the ceiling. `THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR`,
  `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`.

### Part 2: the machine

- **Two caps, each ruled by Taylor before the money it covers is spent.** A benchmark cap, ruled
  with the provider and candidates, covers every rented solve before the campaign: per candidate the
  thread sweep of at most 15 stretches of 100 iterations and one `Kh7d2c` solve; on the chosen box
  eight determinism solves, phase 16's four boards twice, and the six texture solves below. That is
  at most 15 stretches and one solve per candidate and 14 solves on the chosen box, and the contract
  states the count beside the cap. A campaign cap is asked only once the six-texture projection
  exists. Every rented hour is logged with its price, the running total is printed beside the cap it
  counts against, and work halts at a cap rather than past it.
- **The memory bar is the largest planned arena over every flop of every line stage 2 admits,
  computed before any candidate is ranked, and the report prints it.** For the committed line and
  menu, walking GTOpen's `tree.rs` rules over all 22,100 flops, it is 12.87 GB as the driver reads
  it, on `2d2h2s`, which needs 32.2 GB of RAM at `MEMORY_CEILING_FRACTION` 0.40, or about 33.7 GB
  of VRAM by GTOpen's own estimate; 15.8 percent of flops plan above the largest committed board's
  12.24 GB. A candidate that cannot hold the bar is excluded with that reason and never ranked, so
  the campaign cannot meet a board its box refuses.
- **Each candidate solves the same flop: `Kh7d2c` on the committed line and `solve_config.json`,
  unchanged.** It is the slowest board on record, 340 iterations in 1,677.4 seconds at five threads
  on the M4. The report prints, per candidate: machine, thread count, engine, wall clock,
  iterations, achieved exploitability, peak memory, hourly price, and **cost per solved flop**: the
  price times the billed time for one closed flop - server start, tree build, solve, harvest of
  every flop decision point and upload - which is what the choice is made on. How many solves one
  box may run at once is a stage-2 ruling, and a box running more than one applies the memory bar to
  their sum.
- **Before the campaign cap is asked, the chosen box has solved one flop from each of the six
  texture groups**, on the first admitted line under the committed configuration and closed, so they
  are the campaign's first six boards and are never solved again - rainbow unpaired, two-tone
  unpaired, rainbow paired, two-tone paired, monotone, trips - and the report projects the cost of
  one closed line from those six, weighted by how many of the 1,755 classes each group holds.
  Two-tone unpaired is 858 classes and 46.6 percent of all flops and has never been solved under the
  committed configuration. `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`,
  `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`.
- **Determinism is re-proved on the chosen box, not inherited.** Phase 16's four boards are solved
  twice there, in two processes against a restarted server, and compared as `determinism.json`
  compares them. If the two runs on the box differ, the phase halts and Taylor is asked. Whether the
  box's result also matches the M4's committed digests is printed as a separate finding and is not a
  pass condition.
- **A GPU run happens only if Taylor rules to try one**, and only after one flop is solved and timed
  on a CPU of the same provider. A GPU run the server reports as not using the GPU is a silent CPU
  fallback and its timing is discarded. The report states that GTOpen's kernels sum with
  `atomicAdd`, whose order is not fixed, so the GPU determinism re-proof is expected to be at risk.

### Part 3: the campaign

- **The lines are taken in the order stage 2 rules, and the covered set is committed explicitly.**
  A line the committed chart cannot supply ranges for is excluded by name with that reason: the
  corpus's fourth most common flop line, `SB:call`, is a limp and the chart has no range for it. The
  driver hardcodes button against big blind today, so the ranges for any other heads-up line are
  derived from the committed chart by one tested function that assigns them by seat position after
  the flop, not by who raised: in `SB:raise@2.5,BB:call` the raiser is out of position.
- **Every per-line figure is re-derived for each admitted line** - its flop tree, its decision point
  count, its pot, its largest arena and its index cost - because a line with another pot or a 3-bet
  depth builds another tree. The report prints them per line.
- **A solved board closes, for both seats**, unless stage 2's decision 2 rules otherwise. On the
  committed line and menu a flop has 14 decision points, seven for each seat, counted by walking
  GTOpen's `tree.rs` rules; the same walk reproduces every committed object's planned arena to the
  byte. A covered board holds all of its line's flop decision points committed, or all of them
  refused because the one solve they share missed the exploitability ceiling, and a test asserts
  that count per board. The driver harvests all of them from one solve before the server stops,
  because the solved tree itself is never saved.
- **Phase 16's four boards close from the part 1 re-solve**, which must reproduce their committed
  cells; their other decision points are harvested from that same solve. A board whose re-solve does
  not reproduce its committed cells is not closed by mixing two solves, and the phase halts for
  Taylor. `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`.
- **The index budget is stated before the campaign starts, and the index does not silently outgrow
  git.** A committed index entry on this line costs 486.8 bytes, measured on root and one-deep keys,
  so deeper keys and longer 3-bet lines cost more and every figure here is an upper bound on lines.
  The whole 20 MiB `data/artifacts` cap has 16,032,570 bytes of headroom, so 14 entries on each of
  1,755 flops, about 12.0 MB a line, fits about 1.3 closed lines. Campaign cell documents go to
  object storage, not git. Where the index lives beyond that is a stage-2 ruling. The cap is not
  raised and no git LFS is used.
- **The commit rule is phase 16's, with every number in it ruled at stage 2**: the target, the
  iteration cap and the ceiling above which a solve is refused, today 0.3 percent, 1,200 and 1
  percent in `postflop_artifact.py`. The refused count is in the index header. Each board is solved
  once in the campaign; a determinism re-solve never replaces a committed cell.
- **Every object is stored where stage 2 rules, paid for as it rules, with its digest in the index
  and a fetch command a fresh machine can run**; a machine that has not fetched refuses with the
  not-fetched code. The report prints how many flop classes a fresh clone can answer beside how
  many a fetched machine can. `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`.
- **A board refusal says which line and seat it was scoped to, and every coverage figure counts
  lines and seats under different words.**
  `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`.
- **Settling is measured on a sample of campaign cells**, the way phase 16's deep convergence check
  measured one, unless stage 2 rules it out, and the report says which.
  `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`.
- **The campaign stops at the first of three limits - the campaign cap, the index budget, or the
  last line stage 2 admits - and the report names which one.**
- **The table result is re-run on a machine that has fetched every object, on phase 16's own
  terms**: 20,000 hands, seed 777, six seats of the composite strategy, printing postflop decisions,
  bets, showdowns and voided hands **split by the street the hand voided on**, beside phase 16's two
  decisions, both checks, no bets and 5,365 voided hands. Turn and river are out of scope, so a hand
  that reaches a turn still voids; the report says so beside the figures, and it is a measurement of
  flop coverage and closure, never a win rate.

### Evidence, reports, and gate

- **The report prints every figure this contract names and its generator re-derives each one from
  committed files, exiting non-zero on one that does not reconcile**: lines covered and excluded
  with reasons, the per-line tree figures, boards and closed decision points per line, cells refused
  above the ceiling, bytes used and headroom left, the memory bar, per-candidate costs, money spent
  against the cap, the thread comparison, both determinism results, the fresh-clone and fetched
  coverage, coverage by texture group, the share of the 22,100 flops the bot can answer, the share
  of corpus flops it can answer beside phase 16's 74.9 percent ceiling with the multiway share named
  structural (`THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`), and the table result.
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
