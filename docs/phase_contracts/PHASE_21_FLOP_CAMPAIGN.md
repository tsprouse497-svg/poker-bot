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
Declared by MAINT-40 on 2026-09-26 from Taylor's ruling: trust the solve and get more of it. Phase
16 built the machinery - the postflop key, the index, object storage, the solve driver - and closed
on a sample (its decision 25): five flop decision points on four boards, 44 of the 22,100 flops, for
the button opening and the big blind calling. Elsewhere the bot refuses, and on those flops it
refuses one action later, because nothing after a committed decision point is committed: too few
boards, and no closure.

Three parts, in this order, because each one prices the next:

1. **Use every core.** GTOpen takes half of `available_parallelism()` unless `SOLVER_THREADS`
   overrides it, to skip hyperthreads the M4 does not have. Measure the counts, set one explicitly
   on every machine, and record it beside every timing from here on.
   `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`.
2. **Pick the cloud machine.** Solve and time one flop on a few candidates, re-prove determinism on
   the one chosen, and choose on cost per solved flop with the memory a solve needs as a hard limit.
3. **Run the campaign.** Solve the five single-raised lines the chart plays into object storage, as
   many as the campaign budget allows, each solved board closed: every flop and turn decision point
   of its line, for both seats, kept from the one solve, or all refused together; the river is not
   stored but solved at the table by a later phase. Nothing is re-solved or hand-edited to look
   better. `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`.

Phase 16's rulings carry over: f32 arenas (decision 20), the 0.40 memory ceiling (20 and 22,
`runtime-reversible`, moving with the over-read the adopted guard entry names), object storage with
no git LFS, and the rented box governing the campaign (24). Taylor's phase 21 rulings are in
`reports/phase_audits/decisions/PHASE_21_FLOP_CAMPAIGN_DECISIONS.md`, each cited at the criterion it
carries: the turn is stored and played by a later phase, the river solved at the table, never stored
(1, re-ruled 2026-10-04), and the trial runs on RunPod, from a GPU large enough for the small blind
line (5, re-ruled 2026-10-04).

**The solver is a local clone.** Every solve runs GTOpen's `4aee435` plus three changes and no other
upstream change: a read-only bulk strategy export; upstream `85b0a692`'s tree fix, so a street both
players check clears the initiative and out of position may lead the next street with its normal
sizes (decision 17); and upstream `8ff89f42`'s fixed-order GPU fold sum (decision 18), which changes
GPU code only and is required before the first GPU solve. A lead straight after calling a bet stays
out by design, as the empty `donk` setting rules.
`THE-PINNED-SOLVER-CARRIES-THE-AGGRESSOR-THROUGH-A-CHECKED-STREET`.

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
`QUANTIZED-ARENAS-PUT-A-FLOOR-UNDER-EVERY-EXPLOITABILITY-THIS-PHASE-MEASURED`,
`NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED` and
`THE-PINNED-SOLVER-CARRIES-THE-AGGRESSOR-THROUGH-A-CHECKED-STREET`.
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
- Do not make the bot play the turn or the river, and do not store the river. Both still refuse at
  the table when this phase ends.
- Do not solve three-bet pots. Decision 9 admits only the five single-raised lines.
- Do not group similar flops so that one solve answers several. `POSTFLOP-BOARD-ABSTRACTION` stays
  deferred in `docs/ROADMAP.md`, and suit isomorphism remains the only collapse permitted.
- Do not re-solve, hand-edit or drop a cell because its numbers look wrong. A solved cell is
  committed as solved or refused by the rule phase 16 ruled, and a finding about it is a finding.
- Do not add runtime solver calls, LLM-backed poker decisions, PokerNow automation, browser or
  platform observation, UI surfaces or large hand-history ingestion. `AGENTS.md` Boundaries.
- Do not spend on a cloud account, or provision anything outward-facing, before Taylor has seen the
  exact machine and its hourly price.

## Acceptance criteria

Tree figures were measured on 2026-10-04 by building each spot, unsolved, through the clone's solver
crate under both tree rules; the pin's rule reproduces every figure the frozen tests pinned to the
byte. Other figures were measured on 2026-09-26 against the base commit. Commands and scratch
scripts are in the ExecPlan. None is a target a later stage may tune.

### Part 1: every core

- **Every server the driver starts is given an explicit thread count through `SOLVER_THREADS`, and
  the driver refuses to start one without it.** Every solve before this phase ran at five threads.
- **The count used is the fastest measured, and it is measured on every machine the phase solves
  on**, never carried from another. The counts timed are GTOpen's default and a quarter, half, three
  quarters and all of the machine's logical processors, rounded, with repeats dropped - on this Mac
  3, 5, 8 and 10 - each three times interleaved, as a fixed stretch of 100 iterations of one
  committed cell's configuration, unchanged, on a machine doing nothing else. The median of the
  three decides, because one run is not enough: phase 16's two `9c8c7c` runs read 1.34 and 2.16
  seconds per iteration on one configuration. The report prints every run and the spread.
- **A changed thread count does not change the answer.** GTOpen's CPU recursion collects its
  parallel children into an ordered vector and sums in a fixed loop. Phase 16's four boards, solved
  again on the M4 at ten threads on the pin's tree, reproduced its committed cell documents byte for
  byte, the fifth cell's strategy digest and every per-combo strategy, which
  `campaign/mac_resolve_at_thread_count.json` records. Decision 17's commit changes the tree
  builder, the save loader and the server's request, never that summation, so it is not repeated. A
  difference halts the phase for Taylor; no tolerance is set here.
- **Every solve record carries the machine it ran on as measured, the thread count, the engine (CPU
  or GPU, read back from the server), the arena storage and the solver build**, the clone's commit,
  so a cell solved on the pin's tree can never pass for one solved on the new tree. A hardcoded
  machine name fails a test. Peak resident memory is recorded per solve.
- **The clone is recorded by branch, commit and diff hash in `docs/GTOPEN_SOLVER_NOTES.md`**, with
  its release build and the GTOpen tests it passed, and the repo's solve path selects that build by
  default and says how another is chosen. `~/projects/gtopen` stays the untouched reference.
- **The driver's memory guard is tested as behaviour**: a test proves the ceiling follows the
  machine's reported memory, and one ties the committed configuration to the body the driver posts.
  The arena over-read is repaired by one of the three routes its entry names, in the same decision
  as any move of the ceiling. `THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR`,
  `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`.

### Part 2: the machine

- **Two caps, each ruled by Taylor before the money it covers is spent.** The $100 trial cap
  (decision 6, confirmed for RunPod) covers every rented solve before the campaign: per candidate
  the thread sweep of at most 15 stretches of 100 iterations and one `Kh7d2c` solve; on the chosen
  box eight determinism solves, phase 16's four boards twice, the six texture solves and the six
  settling runs below, stated beside the cap; and the GPU trial, one CPU flop first, then two GPU
  solves of it. A campaign cap is asked only once the six-texture projection exists. Every rented
  hour is logged with its price, the running total is printed beside the cap it counts against, and
  work halts at a cap rather than past it.
- **The memory bar is the largest planned arena over every flop of every admitted line, computed
  before any candidate is ranked, and the report prints it.** Walking the new tree over all 22,100
  flops, every line's largest flop is the deuce-trips class. The small blind line's arena is
  18,710,513,792 bytes, 19.62 GB as the driver reads it, about 49.0 GB of RAM at
  `MEMORY_CEILING_FRACTION` 0.40 and 51,239,107,576 bytes of card memory by GTOpen's own estimate,
  within 0.3 GB of a 48 GiB card before CUDA's own use, too thin to rent on. The committed line's is
  13,042,185,280 bytes, 13.68 GB as the driver reads it and 34.2 GB of RAM, and 35,645,460,288 bytes
  of card memory. 3,484 of the 22,100 flops plan at or above the largest committed board, 3,444
  strictly above. A candidate that cannot hold the bar is excluded with that reason and never
  ranked, so the campaign cannot meet a board its box refuses.
- **Each candidate solves the same flop: `Kh7d2c` on the committed line and `solve_config.json`,
  unchanged.** It is the slowest board phase 16 solved. The report prints, per candidate: machine,
  thread count, engine, wall clock, iterations, achieved exploitability, peak memory, hourly price,
  and **cost per solved flop**: the price times the billed time for one closed flop - server start,
  tree build, solve, harvest of every flop and turn decision point, and upload - which is what the
  choice is made on. A box runs one solve at a time unless decision 11's default is changed, and a
  box running more than one applies the memory bar to their sum.
- **Before the campaign cap is asked, and after the determinism re-proof below has passed on it, the
  chosen box has solved one flop from each of the six texture groups**, on the first admitted line
  under phase 16's configuration and closed, so they are the campaign's first six boards and are
  never solved again - rainbow unpaired, two-tone unpaired, rainbow paired, two-tone paired,
  monotone, trips - and the report projects one closed line's cost from them, weighted by each
  group's share of the 1,755 classes. Two-tone unpaired, 858 classes and 46.6 percent of all flops,
  has never been solved under phase 16's configuration. `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`,
  `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`.
- **Determinism is re-proved on the chosen box, not inherited.** Phase 16's four boards are solved
  twice there, in two processes against a restarted server, and compared as `determinism.json`
  compares them. If the two runs on the box differ, the phase halts and Taylor is asked. Whether the
  box's result also matches the M4's new-tree digests, committed first, is printed as a separate
  finding and is not a pass condition.
- **One GPU machine is tried, as Taylor ruled (decision 7)**, with a card that holds the memory bar,
  and only after one flop is solved and timed on a CPU of the same provider. Repeatability comes
  first: one flop solved twice and compared exactly, the first proof of decision 18's fixed-order
  fold. A GPU that does not repeat itself is a finding, not a campaign machine, without another
  ruling; a run the server reports as not using the GPU is a silent CPU fallback and its timing is
  discarded.

### Part 3: the campaign

- **The lines are small blind, button, cutoff, hijack and lojack opening against the big blind, in
  that order (decision 9), each on `solve_config.json`'s bet sizes (decision 10), and the covered
  set is committed explicitly.** The order is the chart's own: those lines reach a flop in 5.53,
  3.66, 2.75, 2.71 and 2.42 percent of hands, weighting each action by its chart probability; the
  real-hand order is printed beside it.
  `LINE-RANKING-BY-CLOSING-DECISION-ARRIVAL-COUNTS-LINES-THE-CHART-NEVER-PLAYS`. A line the
  committed chart cannot supply ranges for is excluded by name with that reason: the corpus's fourth
  most common flop line, `SB:call`, is a limp and the chart has no range for it. The ranges for any
  heads-up line are derived from the committed chart by one tested function that assigns them by
  seat position after the flop, not by who raised: in `SB:raise@2.5,BB:call` the raiser is out of
  position.
- **Every per-line figure is re-derived for each admitted line** - its flop tree, its decision point
  count, its pot, its largest arena and its index cost - because a line with another pot builds
  another tree. The report prints them per line. The button, cutoff, hijack and lojack lines share
  the 5.5 pot and one tree of 4,144,704 nodes; the small blind's 5.0 pot builds 4,339,626.
- **A solved board closes, for both seats, on the flop and the turn.** On the committed line and
  menu one flop's solve holds 14 flop and 6,419 turn decision points, 131 for each of 49 turn cards,
  and the small blind line's 14 and 6,566. A covered board keeps all of them from its one solve, or
  refuses all of them because that solve missed the exploitability ceiling (decision 2). The river
  is not stored (decision 1, re-ruled 2026-10-04): the solve still holds it, 1,549,968 reachable
  river decision points on the committed line and 1,620,528 on the small blind's, and the counts are
  printed as tree figures, but nothing keeps them. Every decision point after a raise has a key, a
  raise being named by its multiplier (decision 16). The manifest carries each board's flop and turn
  counts and a test asserts them offline. The fetch command checks every fetched flop object against
  its board's counts and its digest. Turn rows are two bytes a number, each frequency rounded to a
  tenth of a percent with the residue on the largest entry so a decision sums to one, and standard
  compression is measured before any custom format (decision 15). How the driver gets them out is
  chosen at stage 6 on a measurement, and **the time it takes and the stored size of one closed flop
  are measured on the six trial flops and reported before the campaign budget is asked**.
- **Phase 16's four boards are re-solved on the new tree, and close from that solve.** Their
  committed cells, index entries, objects and `determinism.json` were solved on the pin's tree,
  which the campaign does not use, so they are replaced by a solve on the clone, proved
  deterministic by a second solve in a fresh process, and their turn decision points are harvested
  from the first. A re-solve that does not repeat itself is not closed by mixing two solves, and the
  phase halts for Taylor. Its reason is the tree, never the numbers, and no other solve replaces a
  committed cell. `deep_convergence_check.json` stays as the pin's record of its own solve.
- **The full index lives in object storage, and git holds a manifest per line** (decision 3): the
  flops held and one fingerprint of that line's index file, which the fetch command checks and the
  gate checks offline against the committed sample, and from which the report counts coverage. Git
  cannot hold the full index: 14 decision points on each of 1,755 flops at 830.8 bytes each,
  object-list entry included, is 20.4 MB against about 16 MB of headroom under the 20 MiB
  `data/artifacts` cap. The manifest's size is printed per line. The cap is not raised and no git
  LFS is used.
- **The commit rule is phase 16's, as Taylor kept it** (decision 8): a target of 0.3 percent of the
  pot, a 1,200-iteration cap and refusal above 1 percent, the constants in `postflop_artifact.py`.
  The refused count is in the index header. Each board is solved once in the campaign; a determinism
  re-solve never replaces a committed cell.
- **Every object is stored in a private AWS bucket on Taylor's account (decision 4), with its digest
  in the index and a fetch command a fresh machine can run**; a machine that has not fetched refuses
  with the not-fetched code. Every object is in the standard class (decision 4, re-ruled 2026-10-04
  once the river was dropped). The fetch covers the flop objects and the index; turn objects are
  written from the solve machine, each checked against its board's counts and its digest there
  before upload, and fetched by the phase that plays the turn. The report prints how many flop
  classes a fresh clone can answer beside how many a fetched machine can.
  `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`.
- **A board refusal says which line and seat it was scoped to, and every coverage figure counts
  lines and seats under different words.**
  `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`.
- **Settling is measured on a sample of campaign cells**, the way phase 16's deep convergence check
  measured one: one flop of each texture group solved on to the cap, printed as a finding.
  `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`.
- **The campaign budget is asked with the measured turn size for the five lines and its monthly
  storage bill at AWS's price on the day.**
- **The campaign stops at the first of two limits, the campaign budget or the fifth admitted line,
  and the report names which one.**
- **The table result is re-run on a machine that has fetched every flop object, on phase 16's own
  terms**: 20,000 hands, seed 777, six seats of the composite strategy, printing postflop decisions,
  bets, showdowns and voided hands **split by the street the hand voided on**, beside phase 16's two
  decisions, both checks, no bets and 5,365 voided hands. The bot does not play the turn or river in
  this phase, so a hand that reaches a turn still voids; the report says so beside the figures, and
  it is a measurement of flop coverage and closure, never a win rate.

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
- Do not solve on the pin's tree, or on any build the solver notes do not record.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- Every cell phase 16 committed stays byte-identical except the re-solve on the new tree that
  decision 17 requires, and phase 16's contract is amended to say so.
