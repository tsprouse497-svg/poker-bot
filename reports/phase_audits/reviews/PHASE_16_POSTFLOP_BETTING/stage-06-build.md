# Phase 16 stage 6 review: the build, consolidated

Read-only. I wrote none of the work under review and this file is the only one I changed. No
`git checkout`, no `git stash`, no `run_verify.py` and no mutation tooling. Scratch scripts live
outside the repo. Every figure below was computed in this worktree today and the method is stated
beside it; nothing is copied from `backlog.yml`, a report, or either of the two earlier notes.

**What I read.** `AGENTS.md`; `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md`;
`stage-06-build-mechanical.md` and `stage-06-build-poker.md` in this directory, which between them
raise five blockers; `git diff 01f6ee403de777cd3629702c9c84df939d84630c HEAD` for the whole stage
and `git diff d7712d52d964ede96d98c6d7e2d6f5ed021783eb HEAD` for the half after the merge of main.
The merge brought MAINT-34 and earlier phases' work, reviewed in their own lanes, and I do not
re-review it - except where it moved a figure this phase asserts, which it did once and which is
below. The seven post-merge commits are `52fa2f9`, `7b712c3`, `479aaf2`, `7d6866f`, `de62604`,
`224bfa9`, `399b739`.

**This note consolidates.** Each of the five inherited blockers is re-measured against the tree as
it stands and carries a verdict. Nothing is taken on report.

The driver's question: *does the implementation do the work, or only enough to satisfy the frozen
tests?* The five inherited blockers are genuinely fixed, in code rather than in prose, and I could
break each repair's own claim by measurement if it were false. What is not done is the reporting.
The required report's three sections about the committed solve - determinism, the committed ranges,
and the sentence about convergence - are all describing a different solve from the one in
`data/artifacts/postflop/`, and the two files committed tonight that would have said otherwise are
read by nothing. That is what passes for a reason the contract did not intend, and it is the whole
of my new blocker list.

## Blocker

### The five inherited, re-measured

- **[resolved] `canonical_hole_cards` is not canonical** (mechanical note, blocker 1). Repaired in
  `dbffd03`, which moved the group into
  `src/poker_training_bot/solver_artifacts/postflop_isomorphism.py` and made the hand a minimum
  over the board's whole stabiliser rather than an image under one published map. Measured here by
  applying all 24 suit relabellings to (board, hand) for every one of the 1,176 hero combos on each
  sample board and counting combos that yield more than one answer: **0 of 1,176 on `Kh7d2c`, 0 of
  1,176 on `8c8d3c`, 0 of 1,176 on `9c8c7c`**, against the note's 910 and 1,131. Distinct class
  labels per board are **1,176, 721 and 344**, the true orbit counts for stabilisers of size 1, 2
  and 6. Summed over all 1,755 canonical flops by brute force the collapse gives **1,286,792 classes,
  mean 733.2148 a flop**, reproducing decision 6's byte model exactly. The repair is complete and
  the byte budget was always describing this collapse.

- **[resolved] the report's `servable` column is a copy of the column beside it** (mechanical note,
  blocker 2). Repaired in `abc6603`. `measure_corpus` in
  `scripts/generate_postflop_betting_report.py:653-662` now increments `arrivals` before the
  covered-line and fetched-board gates and `servable` after both. Measured by calling `measure()`
  directly against the committed sample: **225 arrivals, 0 servable, `arrivals == servable` is
  False**; the loss split is 175 to an uncovered line, 50 to an unfetched board, 20 multiway, 14
  outside the price band, over 259 flop-reaching hands. The column is no longer fabricated. It is
  now zero on every row, because only 3 of 1,755 board classes are fetched, and the report says so
  in its own words rather than claiming an order it does not have. See the first non-blocker for
  what the column now means, which is not what the contract's sentence means.

- **[resolved] the solve driver's fail-open defaults** (mechanical note, blocker 3). Repaired in
  `abc6603`, which extracted the wire into
  `src/poker_training_bot/solver_artifacts/postflop_transport.py` and replaced every
  `.get(key, default)` with `answered`/`numeric`, and found a fourth the note had not named. Driven
  here against a stub transport with a valid config: a complete answer solves; **`/api/spot` without
  `arena_mb` refuses; `/api/status` without `state`, without `exploit_pct`, and without `iteration`
  each refuse**, naming the route and the field; a transport answering `{}` refuses. The guards also
  have a production caller now, which they did not when the repair was written -
  `scripts/solve_postflop_sample.py` calls `run_solve` in `solve_one_board` and in `run_deep_check`,
  and the committed cells came through it. Two of the same four defaults survive in a sibling script
  that is out of this task's scope; that is a non-blocker below.

- **[resolved] a committed size travels in big blinds and is matched against a pot in chips**
  (poker note, blocker 1, main finding). Repaired in `dbffd03`, which extracted
  `src/poker_training_bot/solver_artifacts/postflop_sizing.py` and made the unit that travels a
  fraction of the cell's own pot, converted at the table through `menu_size_chips`. Measured
  end to end by building a real table at each price in decision 10's band and asking
  `PostflopBettingStrategy` for the button's continuation bet on `9c8c7c`:

  | open | real pot | the bot's bet | as a share of that pot | matched by the other seat |
  | --- | --- | --- | --- | --- |
  | 2.0bb | 450 | 148 | 32.89% | yes, at 0.33 |
  | 2.1bb | 470 | 155 | 32.98% | yes |
  | 2.25bb | 500 | 165 | 33.00% | yes |
  | 2.5bb | 550 | 182 | 33.09% | yes |
  | 2.75bb | 600 | 198 | 33.00% | yes |
  | 3.0bb | 650 | 214 | 32.92% | yes |

  The worst deviation across the band is **0.11 points of pot**, all of it whole-chip rounding,
  against the 7.44 the shipped code carried, and the 3.0bb row no longer survives on a floating
  point accident. The note's second sub-finding, that a cell can commit a bet on no menu entry, is
  also closed: `price_menu` refuses a bet that is not a `FLOP_BET_MENU` entry of the cell's own pot,
  and both committed bet sizes price to exactly 0.33 and 0.75. The third sub-finding is still live
  and is the first non-blocker below.

- **[resolved] the key can name a flop node no dealer can produce** (poker note, blocker 2).
  Repaired in `dbffd03`, which gave `postflop_action_order` its first production caller and put a
  reachability walk in `postflop_key.py:335-410`, run at import and at lookup. I rebuilt the note's
  five impossible cells and every one now refuses, each naming its own cause: hero button with an
  empty flop line ("ends at BB's turn"), the in-position seat betting first ("acts out of turn"),
  hero acting twice, a seat that folded preflop acting, and a line that ends on villain's turn.
  The three legal nodes still build - the big blind first to act, the button facing a check, the
  big blind facing a bet - and those are exactly the three shapes the four committed cells use, so
  the continuation-bet cell is keyed `f:BB:check` rather than `f:none`. `postflop_action_order` is
  no longer dead.

### New

- **The required report's determinism block and its committed-ranges block are both read out of
  the August cost measurement, so both describe a solve that is not the one the repo commits.**

  `determinism_record` (`scripts/generate_postflop_betting_report.py:510`) walks
  `reports/active/latest_postflop_solve_cost.txt` for a row whose group is `determinism`. I read
  that row: board `Kc7c2c`, starting pot **16.0**, effective stack 92.5, **240 iterations**,
  measured 2026-08-24, against ranges `config.range_oop@568ae7b39c57` and
  `config.range_ip@75dddc9d9ce2`. I also classified every one of the 55 tree blocks in that file
  through `arena_storage` and **all 55 are quantized arenas**, so that row predates the
  full-precision ruling as well. The committed campaign is a single-raised pot of **5.5** at stack
  97.5 on four other boards at **280 to 340 iterations** under f32 arenas. The report prints the
  first under the heading "Determinism: solved twice" and the contract asks for determinism "on the
  configuration actually committed". `scripts/solve_postflop_sample.py:884-890` says this in its own
  words - "Neither result stands in for the other, and the contract asks for this one by name".

  `committed_ranges` (`:528`) has the same shape: it reads the cost report's appendix for the
  ranges of its converged rows. The report's section "The committed ranges, as pair weights on both
  sides" therefore prints four ranges, **none of which is either range the committed cells were
  solved against**. The committed ones are in `data/artifacts/postflop/solve_config.json` under
  `oop_bb_call` and `ip_btn_open`; their pocket-pair weights are 22 0.9713, 33 0.208, 44 0.9997, 55
  1.0, 66 1.0, 77 1.0, 88 0.9993, 99 0.4672 out of position, and every pair at 1.0 in position. No
  printed block matches either; the printed ones carry TT through AA in the out-of-position range,
  which the committed one does not hold at all. The printed "dropped by the floor" lists are drops
  that did not happen here: the committed ranges' minimum weights are **0.0147 and 0.7865**, so
  nothing in either sits at or under the 0.01 floor.

  **And nothing anywhere reads `data/artifacts/postflop/determinism.json`.** I grepped `scripts/`,
  `src/`, `tests/` and `docs/`; the only file that names it is the script that wrote it. So the
  phase has a real determinism proof - five cells, both runs, per-combo gaps of 0.0, wall clocks
  375.6s against 606.0s on the monotone board - sitting beside a report that cites somebody else's.

  What closes it: point `determinism_record` at `determinism.json` and `committed_ranges` at
  `solve_config.json`. The second needs `conditional_ranges` to record which classes the floor
  dropped, because `solve_config.json` stores the post-floor range and the dropped list is not
  recoverable from it.

- **The required report says "nothing here has diffed a deep solve against a shallow one" in the
  commit that committed that diff, and the diff contradicts the sentence it is reassuring the
  reader with.**

  `reports/active/latest_postflop_betting_report.txt:132` still carries that clause.
  `399b739` committed `data/artifacts/postflop/deep_convergence_check.json` and regenerated the
  report in the same commit; the only lines that moved were the byte figures. I read the deep check:
  the monotone continuation-bet cell re-solved to the 1,200-iteration cap reaches 0.0478% of pot
  against the committed 0.2774%, and of its 152 hand classes **none is unmoved**, the median moves
  0.053, the worst 0.467, **79 move past 0.05**, and **16 change which action they prefer**. The
  bet-or-check decision is settled - check goes 0.0012 to 0.0000 - and the split between the two
  bet sizes is not: 0.8086 to 0.7584 small and 0.1903 to 0.2416 large. That is the strongest single
  piece of evidence this phase produced about its own data, it is exactly what the contract's
  qualification "convergence at the committed iteration count is unproven" is about, and the report
  denies it exists. Like `determinism.json`, `deep_convergence_check.json` is read by nothing.

  What closes it: delete the clause, and print the movement summary the file already holds. The
  contract's ban is on reporting an accuracy for the solve as a whole, not on reporting how far the
  frequencies moved.

## Non-blocker

- **A raise the matcher cannot name, still live, and the fix is one field.** The poker note's
  sub-finding under its first blocker was not repaired. `load_library`
  (`src/poker_training_bot/strategy/postflop_committed.py:174-180`) derives `raise_fractions` from
  raise entries in each cell's **`flop_actions`** - the line leading *to* the cell - rather than
  from the cell's own `actions`. No committed cell has a raise in its flop line, so
  `raise_fractions` is `()`, measured. Meanwhile the facing-a-bet cell on `Kh7d2c` **does** hold a
  raise, priced at fraction 0.6203. Driven end to end: hero big blind facing a 182-chip bet raises
  to **454**, and from the other chair the same library refuses that raise under
  `postflop-betting:flop-size-off-the-committed-menu` with detail `pct_of_pot 62`. The refusal
  blames the other seat for a size the bot itself chose. Reading the raise fractions off `actions`
  instead of `flop_actions` would close it, since the number the matcher needs is already on the
  cell. `THE-FLOP-RAISE-TOLERANCE-IS-BORROWED-FROM-THE-BET-MENU-RULING` is the neighbouring entry
  and owns the tolerance rather than the source.

- **The contract's own servable figure was falsified by the merge and nothing records it.**
  `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:140` states "a 3-bet line serves 47.1% of its
  arrivals against a single-raised line's 99.0%". Measured off the corpus today against the chart
  prices the tree now holds - `(2.5, 7.5, 13.5)`, the 13.5 added by MAINT-34 - the split is **62 of
  87 three-bets in a declared band, 71.3%**, made up of 41 at the 7.5 price and 21 at the new 13.5
  one. The 41 is the contract's old figure exactly. Opens are unmoved at 405 of 409, 99.0%. The
  criterion the sentence justifies still stands; the measurement in it is now wrong by 24 points,
  and correcting it is a `contract-update` task rather than something this stage can do.
  `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` needs re-reading for the same reason: the
  corpus median three-bet of 9.25bb now sits *between* two chart prices rather than above the only
  one.

- **The whole refusal block of the report is structurally unable to count a refusal, and the phase
  built the thing that would have made one fire.** `measure_behaviour` (`:716`) iterates
  `committed_spot_queries()`, which rebuilds each table from a cell the machine holds, so the
  strategy is only ever asked about spots it can answer. The report prints "refusals counted: 0"
  and labels all 16 codes `vacuous`. Two of them are trivially reachable and I fired both in about
  twenty lines: `postflop-betting:in-the-index-but-not-fetched` on the `Ac8c3c` cell that `52fa2f9`
  added to the index expressly so that code would be live, and
  `postflop-betting:flop-size-off-the-committed-menu` as above. `an_indexed_but_unfetched_query`
  already exists in `postflop_spot_queries.py:297` and is called by one frozen test and by nothing
  in the report. Adding it to the behaviour loop would turn one label from `vacuous` to a count.
  `THE-BEHAVIOUR-SECTION-ASKS-THE-STRATEGY-ONLY-ABOUT-SPOTS-IT-CHOSE` owns the general shape; this
  is the specific instance the stage created and then did not use.

- **`check_servable_never_exceeds_arrivals` cannot fail on the input the generator hands it.** Both
  its clauses are true by construction of the loop it checks. `servable[line] += 1` at
  `:661` is only reachable after `arrivals[line] += 1` at `:653`, so a line can never be servable
  more often than it arrived; and `answerable += 1` at `:662` is the very next statement, so the
  column always sums to `answerable`. It is a genuine regression guard on those three increment
  sites - fed the shipped defect's shape it does raise, and I do not dispute the commit message on
  that - but it is not a re-derivation of anything about this run, and the report does not
  distinguish the two. This is the fifth instance of the shape the stage has now found four times.
  `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL`.

- **The four fail-open defaults closed in the driver survive verbatim in the script that produced
  the whole cost record.** `scripts/measure_postflop_solve_cost.py` still carries
  `float(tree.get("arena_mb", 0.0))` at `:648`, whose zero passes `refuse_oversized` at `:657`;
  `float(status.get("exploit_pct", 0.0)) <= target` at `:554`, whose zero reads as converged;
  `int(status.get("iteration", 0))` at `:679` and `:716`; and `status.get("state") != "running"` at
  `:690`, whose absence ends the poll. That file is out of this task's `approved_scope`, so this is
  a finding rather than an omission by the lane. Proposed
  `the-measuring-script-kept-every-fail-open-default-the-driver-closed`, to be filed in upper case
  by whoever files it.

- **Two guards over one quantity now disagree by 9%, and the driver's docstring asserts they do
  not.** `postflop_solve_driver.py:65-73` says "The measuring script keeps the same fraction".
  It does not: `MEMORY_CEILING_FRACTION` is 0.40 and `measure_postflop_solve_cost.ARENA_CEILING_FRACTION`
  is 0.35. They also read the server's `arena_mb` in different units - the driver at 2^20 through
  `arena_bytes`, the measuring script at the server's own 10^6. On this 34,359,738,368-byte machine
  the driver refuses above an effective **13,107,200,000** true bytes and the measuring script above
  **12,026,000,000**, so the driver is **9.0%** looser than the script whose figure the docstring
  claims it matches. That is the answer to "does anything else compare figures across that unit":
  the second place is `deep_convergence_check.json`, which commits `arena_bytes: 12041331798` - the
  2^20 reading - into git with no unit named beside it, where every arena figure in
  `latest_postflop_solve_cost.txt` is in the other unit.

- **The rejected-cell counter counts boards and mislabels its causes.**
  `scripts/solve_postflop_sample.py:1736` increments `rejected_above_one_percent` once per refused
  **board**, where the index field it feeds is named
  `cells_solved_and_rejected_above_one_percent` and a board yields one or two cells; and
  `commit_verdict` returns False for two reasons, the 1%-of-pot ceiling and "ended on neither
  stopping condition", both of which land in a counter that names only the first. The figure is 0
  today, so it is unexercised rather than wrong, but it is a contract-named report figure that would
  be wrong the first time it was not zero.

- **`solve_config.json` publishes a range size that ignores the weights it just preserved.** Its
  `range_source.note` says "combos after the floor are 380 out of position and 498 in position". I
  re-derived both: 380 and 498 are the combos of the classes that survive, counted at full weight.
  Weighted by the weights the floor kept, the same ranges are **323.7** and **495.4** combos. The
  out-of-position figure overstates the range it describes by **17.4%**.
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` is the neighbouring entry.

- **The self-comparison guard on the determinism check is real and bites, and is absent on one of
  the two loops.** I drove `determinism_document` twice. Pointed at the committed tree it refuses
  ("this would compare a file with itself"); pointed at a copy of the committed tree with the first
  run's own object directory it refuses on the wall clock ("report the same wall clock to the
  microsecond, which two runs do not"). So the answer to whether `identical: true` can be produced
  by comparing a run with itself is no, for the four sample cells. The fifth cell - the one the
  index lists and the sample does not hold - goes through the second loop at
  `solve_postflop_sample.py:986-1030`, which has **no wall-clock check at all**. It shares the same
  `--second-objects` argument as the first loop, which is why the hole is not reachable today, but
  the guard is written once for two loops that both need it.

- **The committed determinism proof cannot be re-derived, even on this machine.**
  `/Users/taylorsprouse/poker-bot-solve-objects/postflop/` holds the first run's five objects only;
  the second run's tree and objects are gone. All five object digests in `objects.json` re-derive
  by sha256 against the files on disk, and all four index entries' `strategy_digest`,
  `achieved_exploitability_pct_of_pot` and `iterations` re-derive from the committed cells - I
  checked every one. `determinism.json` is the only figure in the tree with nothing behind it any
  more. `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`.

- **A figure inside the deep check compares two different populations.**
  `DEEP_CHECK_CELL_REASON` says "rainbow collapses to 1,176 classes against this board's 152". The
  152 is the committed monotone cell's class count and the 1,176 is rainbow's whole-deck class
  count. The like-for-like comparisons are 1,176 against **344** at deck level, or **342** against
  152 between the two committed cells. The three figures the sentence rests on - 152 classes, 19 at
  or above 0.99 on one action, 101 below 0.90 - I recomputed off the committed file and all three
  hold exactly.

### Checked and clean

- `arena_storage` in `postflop_transport.py` is right in both branches, verified against GTOpen's
  own source rather than against its docstring. `crates/solver/src/game.rs:352` gives
  `arena_bytes_for(F32) = entries * 2 * 4` and `Compressed = entries * 2 * 2 + nodes * 16`, and
  `:365` gives `vram_estimate_bytes = nodes * (hands_oop + hands_ip + max) * 4 + entries * 2 * 4 +
  512 MiB`, so the entry count does come out of `vram_mb` and both candidates are exact. Run over
  every tree block in `latest_postflop_solve_cost.txt`: **55 rows, 32 distinct trees, all classified
  compressed, and the compressed formula reproduces `arena_mb` with a maximum error of 0 bytes**.
  The f32 branch matches 0 of those rows, which is expected - the record predates the ruling - and
  it is nevertheless the correct formula, because it is `arena_bytes_for(F32)` term for term. The
  field names are confirmed at `crates/server/src/main.rs:285-298`.
- The two sentences rewritten in `postflop_harvest.py` are now true and were false before.
  `ensure_symmetric` (`crates/solver/src/cfr.rs:749`) calls `symmetrize_node`, whose `KIND_ACTION`
  arm (`:762-767`) only recurses into children and writes nothing into the node's own per-hand
  arrays, so the flop node this module harvests is untouched by it. The old docstring's claim that
  the solver guarantees the agreement the check tests was the opposite of the source.
- The memory-guard over-read is filed accurately. The entry
  `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT` states
  4.86% and "about 95.5 percent of that ceiling"; I re-derived both off the deep run's own recorded
  arena. The over-read factor is exactly 1.048576, the deep run's planned arena reads 12,041,331,798
  bytes and is **11,483,508,871** in the server's unit, which is **95.49%** of the 0.35 ceiling of
  12,025,908,428 and **4.51% under it**. So the 0.13% overage that prompted decision 20's move to
  0.40 is entirely the unit. Taylor has not ruled again and the entry does not pre-empt him.
- `pytest_postflop_betting`'s six files pass: **238 passed** in 5.9s. `check_scope.py` exits 0.
- Byte figures reconcile. The postflop tree is **100,845** bytes on disk against the index's
  declared 100,845; the whole artifact tree is **4,938,950** and 20 MiB less that is **16,032,570**,
  matching the index's headroom and the report. Weights are 3,198, which is
  `(152 + 342 + 342 + 230) * 3` exactly.
- The committed solve configuration matches the contract line for line: flop `33 75`, turn and river
  `66 125`, `raise: "2.5x"`, `donk` empty, identical on both seats, `add_allin: false`,
  `max_raises: 2`, `allin_threshold: 85.0` as a percent, floor 0.01, target 0.3, cap 1,200.
- The three sample boards are the ruled three in their canonical dressings, and the fifth index
  entry sits in the index rather than in `sample/`, which is what decision 18b asks for.

### The poker of what was committed, which no report prints

The contract says plainly that nothing here gates on whether the strategy is good poker, so none of
this is a blocker. It is the thing a reader of the packet will ask first and cannot currently find,
because the report's only behaviour figures are taken over hands the artifact chose. Each row is the
mean over the cell's own classes, and beside it the same mean weighted by how many dealt combos each
class stands for; the two agree closely, so the choice of weighting is not what produces them.

| cell | action | class mean | combo weighted |
| --- | --- | --- | --- |
| `9c8c7c`, button continuation bet | check | 0.0011 | 0.0012 |
| | bet 33% | 0.7955 | 0.8089 |
| | bet 75% | 0.2034 | 0.1899 |
| `Kh7d2c`, big blind first to act | check | 0.8251 | 0.8251 |
| | bet 33% | 0.1340 | 0.1340 |
| `8c8d3c`, big blind first to act | check | 0.6319 | 0.6679 |
| | bet 33% | 0.3632 | 0.3275 |
| `Kh7d2c`, big blind facing a 33% bet | fold | 0.2878 | 0.2878 |
| | call | 0.4386 | 0.4386 |
| | raise | 0.2736 | 0.2736 |

The first row is the one to look at. **The button bets 99.88% of its range on a monotone connected
flop** - the texture where the in-position raiser's check-back frequency is normally at its highest,
because the caller's range holds the straights and the made flushes. The deep run drives it to
100.00%. Two more rows sit well outside what published solver output looks like: a big blind leading
17.5% of the time on a dry king-high rainbow board, and check-raising 27.4% of the time facing a
third-pot bet.

I did not find a defect in the harvest, the key or the menu that would produce those, and I am not
calling a solved range wrong without one. What I can measure is the input. Off the committed export,
the big blind facing a 2.5bb button open **folds 62.67%, calls 24.41% and three-bets 12.91%**, so it
defends **37.33%** of 1,326 combos. The button risks 1.5bb to win the 1.5bb in the middle, which
makes the defence frequency that prices the open at zero **50%**. The big blind is 12.7 points under
it, and the 24.41% calling slice is the whole of the out-of-position range every committed cell was
solved against. A flop solve run against a caller who has already folded too much will c-bet too
much, and that is the first thing to rule out before these cells teach anybody.
`EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` is the contract's own entry for this and it says
the phase must repair it or refuse it explicitly; neither has happened, and the report's range
section - which is the place a reader would see it - is printing somebody else's ranges.

## Alignment

- `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`. The code is fixed and the entry's
  long-term point is not: the frozen tests at `tests/test_postflop_key.py` still reach this through
  the implementation's own formula. The property that makes the fix provable is invariance under
  relabelling board and hand together, which is what I measured above and what no test asserts.
- `THE-BEHAVIOUR-SECTION-ASKS-THE-STRATEGY-ONLY-ABOUT-SPOTS-IT-CHOSE`. Now the sole source of
  every published behaviour figure, including a bet frequency of 22 of 39 that a reader will take
  for a bet frequency and that says only that the cells round-trip.
- `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`. Accurate
  as filed, re-derived above, and it now has a second half: a sibling guard at a different fraction
  in a different unit, and a committed data file carrying the over-read number.
- `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`. Made materially worse by this stage.
  Five object digests and one determinism verdict now rest on one laptop's home directory, and half
  the evidence behind the determinism verdict no longer exists.
- `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`. The contract makes this phase's to repair or
  refuse explicitly. It is neither, and it is now the input to every committed cell.
- `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN`. The merge moved the ground under it: the
  chart now holds a 13.5bb price and the corpus median of 9.25bb falls between two prices rather
  than above the only one.
- `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL`. Five instances in one stage is a pattern,
  not a run of bad luck, and the common cause is that a validator is written next to the code it
  validates and is fed that code's own intermediate value.
- `THE-COMMITTED-ROW-IS-ONE-COMBO-RATHER-THAN-AN-AGREED-ANSWER`. Correctly filed by the harvest
  repair and worth keeping in view, because the deep run's largest in-class divergence is
  1.27e-4 - inside the tolerance, and above the thousandth boundary a committed row rounds at.
- `NOTHING-TESTS-THE-MODULE-THAT-DECIDES-WHAT-EVERY-COMMITTED-CELL-CONTAINS`. `postflop_harvest.py`
  had two false sentences in its docstring for the whole stage and they were caught by reading the
  solver's source, not by a test, because it has none.
- `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`. Confirmed live by the
  raise measurement above: the bot check-raises and the hand dies on the flop, from its own other
  chair.
