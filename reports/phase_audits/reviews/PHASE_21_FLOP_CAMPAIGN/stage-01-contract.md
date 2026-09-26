# Phase 21 stage 1 review: the contract

Reviewer: independent read-only lane, wrote none of the contract or ExecPlan. Scope:
`git diff b00f9d2a463e43c4713fdf64959390773e3eec2b` over the contract and ExecPlan, plus the whole
contract at `d869636` (234 lines, under the 300 cap). Question: is any criterion unfalsifiable, a
restatement of the title, or satisfiable without the work it names.

**What I recomputed, and what holds.**

Re-derived from committed data, GTOpen source and the scratch scripts (re-run, not quoted):

- 14 flop decision points, 7 per seat: `tree.py` port read against GTOpen `crates/solver/src/tree.rs`
  `legal_actions` (lines 432-523) and found faithful for this menu (raise `2.5x` is `PrevMult`,
  `max_raises` 2 counts raises only, all-in snap at 0.85 of stack behind). The port's planned arenas
  match every object's `solve.arena_bytes` to the byte: 12,041,331,798 (`9c8c7c`), 11,978,042,234
  (`Kh7d2c`), 12,236,838,500 (`8c8d3c`), 11,598,324,830 (`Ac8c3c`). Holds.
- Seconds per iteration from `determinism.json` first runs: 1.341, 1.925, 3.237, 4.934. Holds.
- Ceiling 34,359,738,368 x 0.40 = 13,743,895,347; arenas 11.60-12.24 GB are 84.4-89.0 percent;
  largest / 0.40 = 30.59 GB. Holds for the four committed boards.
- VRAM formula matches `game.rs:365-373`; 30.37-32.00 GB on the committed boards. Holds.
- Index: tracked `data/artifacts` 4,938,950 B, headroom 16,032,570 B; (2,866 - 432) / 5 = 486.8;
  14 x 1,755 x 486.8 = 11.96 MB; 1.34 lines. Holds as arithmetic (see N6 on the entry size).
- Texture: 1,755 = 286 rainbow unpaired + 858 two-tone unpaired + 286 monotone + 312 paired + 13
  trips; two-tone unpaired is 10,296 of 22,100 flops, 46.6 percent. 44 and 40 flops hold.
- Ranking: `rank.py` gives 259 flops, 225 heads-up over 32 lines, rank 4 `SB:call` with 21 arrivals
  and no chart arrival key. Holds. Corpus rank 1 (`BTN:raise@2.5,BB:call`) is not the chart's
  highest arrival among the head, so the rank-1 disagreement claim holds.
- Thread determinism mechanism: `cfr.rs:631-633` collects `par_iter` children into an ordered
  vector and sums in a fixed card loop afterwards. Holds as stated.
- Phase 16 carries: decision 20 f32 and 0.40, decision 22 keeps 0.40, decision 24 rented box and
  machine-local determinism, decision 25 table figures (20,000, seed 777, 2 checks, 0 bets, 5,365
  voided, matching `reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md:44-49`), and the 1 percent
  commit ceiling from decision 4. All agree.

## Blocker

- [resolved] Round 2: fixed at contract line 49-50 and 187-192 at `b1dd5ac` (all of a line's flop decision points for both seats from one solve, or all refused together, with a per-board count test). B1. Closure as written is satisfiable without closing anything that plays. Contract line 166-168
  (and Scope line 49-51) define closure as "every flop decision point reachable from a committed
  one". A board whose committed set is closed downward but omits the root passes: commit only the
  four nodes that face a second raise (fold or call only, nothing after them on the flop) and the
  test at line 167-168 finds zero reachable uncommitted points, yet the bot refuses its first flop
  decision on that board. Phase 16's own `9c8c7c` holds only the button after a check
  (`index.json` entry 1), so under this wording its closure never needs the big blind's first
  decision. The named example reasons also cannot occur inside the tree: an off-menu size is an
  opponent's chip bet, and no one of the 14 on-menu nodes can be refused for it; the exploitability
  ceiling is per solve, so it refuses all 14 or none. Fix: define closure over the line's flop root
  for both seats, so each covered board holds all 14 committed or all 14 refused under the
  whole-board ceiling, and have the test assert that count per board.
- [resolved] Round 2: fixed at contract line 122-126 and 193-196 (the four boards close from the part 1 M4 re-solve, which must reproduce four cell documents and the fifth digest; a mismatch halts, no mixing). B2. Closing phase 16's four boards has no coherent source. The closure test walks "every
  committed board" (line 167), which includes phase 16's four; the tree is never saved (line 169),
  so their 12 or 13 missing nodes need a re-solve; each board is "solved once" and a determinism
  re-solve "never replaces a committed cell" (line 177-178); phase 16's cells stay byte-identical
  (line 234); and the box's result is explicitly allowed not to match the M4 digests (line
  149-150). If the closing solve differs, the board mixes cells from two different solves, which is
  not one strategy, and the contract's own "harvests all of them from one solve" is broken. The
  fifth cell, `Ac8c3c`, has no committed cell document at all (`objects.json` `listed_not_held`),
  so "reproduce their committed cell documents byte for byte" for five cells (line 118-119) is
  false for one. Fix: say where the four boards' closure comes from (for example the part 1 M4
  re-solve, which must reproduce the committed digests), that a board whose closing solve does not
  reproduce its committed cells is not closed by mixing and halts for Taylor, and say "four cell
  documents plus the fifth's strategy digest".
- [resolved] Round 2: fixed at contract line 145-151 and 184-186 (the bar is the largest arena over every flop of every admitted line, computed before ranking, with this line's 12.87 GB, 32.2 GB and 33.7 GB stated). B3. The memory bar is measured on the wrong set. Line 140-145 excludes candidates against the
  four committed boards' arenas (30.6 GB RAM, 30.4-32.0 GB VRAM). Over all 22,100 flops on this
  same line the largest planned arena is 12.87 GB as the guard reads it (`2d2h2s`, 365 and 483
  hands), needing 32.18 GB of RAM at 0.40 and about 33.7 GB of VRAM, and 15.8 percent of flops plan
  above the paired board's 12.24 GB (my script `review_maxarena.py` in the session scratchpad,
  reusing `vram.py`'s node and slot counts). Other lines stage 2 may admit have other ranges and
  pots, so other arenas. A box chosen on the stated bar can pass and then refuse boards mid-campaign;
  the driver fails closed, so coverage narrows silently rather than breaking. Fix: the hard limit is
  the largest planned arena over every flop of every line stage 2 admits, computed before a
  candidate is ranked, and the report prints it.

- [resolved] Round 3: fixed at contract line 99-100 and 145-152 at `62dce5d` (a benchmark cap ruled with the provider and candidates covers every rented solve before the campaign, counted as at most 15 stretches and one solve per candidate and 14 on the chosen box; a campaign cap is asked only after the projection) and line 168-170 (the six texture flops are the campaign's first six boards, never solved again). B4. Round 2, new. The pre-cap solves contradict the spending rule and are neither costed nor
  bounded. Contract line 99-100 and 142-144 forbid any spend before Taylor rules a spending cap, but
  line 160-165 requires the chosen box to have solved six texture flops "before the spending cap is
  asked", which needs an account, candidates solved (line 152-159) and a box chosen, all of it
  money. Every rented solve before the campaign is also unpriced: per candidate a thread sweep
  (line 114-117: at least two counts, up to every count between, three runs each) plus `Kh7d2c`; on
  the chosen box, eight determinism solves (line 166-170) and the six texture solves. At M4 rates
  that is roughly an hour of solving per candidate and about four more on the chosen box, which is
  probably small in money but is not stated anywhere Taylor would see it before ruling. Fix: split
  the cap into a benchmark cap ruled with the candidates and a campaign cap asked after the
  projection, or one cap that names both, and state the expected count of benchmark solves beside
  it. Also say whether the six texture flops are committed as campaign boards (line 206 "each board
  is solved once") or are throwaway.

## Non-blocker

- N1. Part 1 can pass without using every core. Line 108-116 requires an explicit
  `SOLVER_THREADS` and a five-against-ten measurement, but not that the chosen count be the fastest
  measured, and part 2 never re-measures the thread curve on the box (x86 with SMT may make half the
  right answer there). Setting it to 5 explicitly satisfies part 1. Also a single timing at each count
  is weak: the same config on the M4 read 1.34 and 2.16 seconds per iteration across the two
  determinism runs (`determinism.json`), a 60 percent spread; ask for repeated, interleaved runs.
- N2. Cost per solved flop (line 139) is price x solve wall clock, one solve per box. It omits
  billed time outside the solve (server start, tree build, 14-node harvest, upload) and ignores that
  a large box can run two or more solves at once; the 0.40 ceiling is per solve, so a two-solve box
  needs its own guard rule. It prices big boxes wrongly either way. Stage 2 should put concurrency
  to Taylor with the formula.
- N3. `Kh7d2c` is a fair time benchmark (slowest per iteration, rainbow, and closes
  `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`) and a poor memory benchmark (see B3). For ranking CPU
  boxes one board is probably enough; for CPU against GPU the ratio depends on nodes x hands and may
  not travel across textures. Taylor's spending cap needs a projected per-line cost weighted by the
  texture mix (two-tone unpaired, never measured, is 46.6 percent), which nothing requires before
  the cap is asked.
- N4. Closure is not a Taylor ruling. MAINT-40's recorded rulings
  (`docs/exec_plans/completed/MAINT_40_DECLARE_THE_FLOP_CAMPAIGN.md:17-25`) are direction,
  numbering and the 19 edge; closure came in through the backlog adoption note and the roadmap. It
  sets the git budget sevenfold: at 14 entries a line fits 1.3 lines, at 2 (one root per seat)
  about 9.4. The poker strongly favours closure (decision 25: unclosed boards void one action
  later), but stage 2 should present it to Taylor coupled with where the index lives, since an index
  outside git removes the trade.
- N5. Phase 16's contract says "rented NVIDIA cloud box"
  (`docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:30`); this contract carries decision 24 but
  lets candidates be CPU-only (line 151). That is a reopening; stage 2 should name it. Relatedly, the
  0.3 percent target is re-asked (line 62-63) but the 1 percent ceiling and the 1,200 cap
  (`postflop_artifact.py:75,79`) come from the same decision 4; ask or inherit all three the same way.
- N6. The 487 bytes per entry is measured on flop-root and one-deep keys of one single-raised line;
  deeper keys (four actions) and 3-bet line strings are longer, so 1.3 is an upper figure. The
  budget also assumes campaign cell documents go to object storage, not git (phase 16's sample cells
  are 8-17 KB each); say so.
- N7. The table re-run (line 185-188) is useful only if it splits voided hands by street. With one
  line closed on the flop and no turn cells, hands move from voiding on the flop to voiding on the
  turn and showdowns stay near zero, so the printed columns cannot show closure worked. Also state
  whether it runs on a fetched machine; on a fresh clone every campaign board refuses as not
  fetched.
- N8. Four adopted entries have no criterion that closes them, although line 65 says each is
  "closed or carried": `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`
  (refusal wording, line and seat vocabulary),
  `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED` (settling on a sample),
  `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS` (the report prints a share of 22,100
  flops, not the corpus share beside 74.9 percent with multiway named structural),
  `THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR` (ceiling pinned to reported
  memory, config tied to posted body). `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`
  also needs "who pays" and "how a machine fetches", which line 179-182 omits, and
  `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT` closes only
  on a repair, which no criterion requires.
- N9. Wording. Line 197-199 reads as if rainbow unpaired has never been solved at f32; `Kh7d2c` is
  rainbow unpaired and was. Line 136-137 "never measured to target" is true of the MAINT-26 cost
  report, not of the repo. Line 165 "checked against all four committed planned arenas": the arenas
  are in objects outside git. The ExecPlan line 44 cites `tree2.py` where line 28 lists `tree.py`
  and `nodes.py`; `tree2.py` is the per-seat count and should be listed.
- N10. Line 162 derives other lines' ranges "by one function" but OOP and IP must follow seat, not
  raiser: in `SB:raise@2.5,BB:call` the raiser is out of position. And the 14-point count, the pot
  (5.5) and the arena are per line; lines with other pots (a button call of a cutoff open is 6.5)
  or 3-bet depths have different trees. Say the count and budget are re-derived per admitted line.

- N11. Round 2, new. The thread sweep's bounds are the M4's. Line 115 "at least five and ten"
  applies "on every machine" (line 114), so on a 32 or 64 core box it can pick 10 as "fastest
  measured" while never timing 16 or 32. State the ends per machine as half and all of its reported
  parallelism, and say whether a timing is a full solve or a fixed iteration window (the latter
  keeps the sweep cheap).
- N12. Round 2, new. If the fastest M4 count is five, the part 1 re-solve (line 122-126) runs at the
  same count as phase 16 and proves nothing about a changed count. Require the determinism re-solve
  at a count other than five whatever the sweep picks, or say the check is skipped and why.
- N13. Round 2, new. "Fastest" over three runs with a printed spread (line 116-118) has no rule
  for which statistic decides (median, best). Name it.
- N14. Round 2, new, cosmetic. Line 60 and line 213 run well past the file's wrap width.

- N15. Round 3, new. The six texture boards (line 168-170) are committed campaign boards, but the
  contract does not order them after the chosen box's own determinism re-proof (line 176-180). If
  that re-proof fails and the phase halts, six committed boards came from a box shown not to
  reproduce itself. Solve the determinism pairs first. The same bullet says "under the committed
  configuration", while line 215-218 has stage 2 rule the target, iteration cap and ceiling, and the
  first admitted line may not be the button against the big blind whose ranges are committed. Say
  "under the configuration stage 2 rules for that line", so the first six boards follow the same
  commit rule as the rest.
- N16. Round 3, new. "All of the machine's reported cores" (line 115-116) is ambiguous on a box with
  hyperthreads: GTOpen's default is half the logical count, so if "cores" means physical cores the
  sweep never times the logical count. Say logical processors, as `available_parallelism()` reports.
- N17. Round 3, new. The benchmark count (line 149) leaves out any GPU trial (line 181-184), which
  the benchmark cap also has to cover if Taylor rules to try one. Add it to the count or say it is
  priced separately.
- N18. Round 3, new, cosmetic. Line 126-128 was reflowed so line 127 is a short fragment
  ("reproduce the four committed cell documents byte for byte,").

## Alignment

- The four entries in N8 are existing ids and stay with this phase; the coordinator records how
  each closes before stage 4, or files a carry note in each entry.
- B3 and N10 generalise to every later line: the coordinator must file one, proposed id
  `THE-MEMORY-BAR-IS-THE-LARGEST-ARENA-OVER-EVERY-ADMITTED-LINE-NOT-THE-SAMPLE`, unless B3's fix
  lands in this contract.

- Round 2: the proposed id above is no longer needed. B3's fix landed in the contract at line
  145-151 and the per-line rule at line 184-186 carries it to later lines, so nothing to file.

## What I held back

- I did not check the claim that `/api/status` reports `"gpu"`; I only confirmed the `gpu` feature
  in `crates/solver/Cargo.toml:22-23`. `atomicAdd` in `kernels.cu` was not re-grepped (my glob missed
  the file); treat line 154 as unverified by me.
- I did not compute the largest arena for any line other than button against big blind.
- The lower sizes in N6 are reasoned, not measured; I did not build a deep key.
- Boundaries: nothing here anticipates a lift. No browser, no runtime solver call, no ingestion;
  the non-goals at line 96-99 hold, and the spending gate at line 131-133 is the right shape.
- My view as a player: closure plus one fully covered line is worth more than many unclosed lines,
  but the bot will still void every hand that reaches a turn, so the table result after this phase
  will look almost as empty as phase 16's in showdowns. Say that to Taylor before he sets a cap.

## Round 2

Scope: `git diff d869636..b1dd5ac` over the contract and ExecPlan. Line numbers below are the
contract at `b1dd5ac` (270 lines, under the 300 cap).

- B1: fixed. Line 49-50 and 187-192: every flop decision point in the line, both seats, from one
  solve, or all refused together on the shared solve's ceiling miss; a test asserts the count per
  board. The vacuous off-menu example is gone.
- B2: fixed. Line 122-126 re-solves the four boards on the M4 and requires four cell documents byte
  for byte plus the fifth's digest; line 193-196 closes them from that same solve and halts rather
  than mixing.
- B3: fixed. Line 145-151 sets the bar over every flop of every admitted line before ranking, with
  the figures I measured; line 184-186 re-derives per line. The claim "the campaign cannot meet a
  board its box refuses" (line 150-151) holds for the planned-arena guard only, which is the guard
  that exists.
- B4: new blocker, see the Blocker section. Asked directly whether the six-texture projection and
  the thread sweep are costed and bounded: no. Neither is priced, the sweep has no upper count on a
  large box (N11) and no statement of full solve against an iteration window, and the projection is
  sequenced before the cap in a contract that forbids spending before the cap.
- N1: partly fixed. Line 114-121: fastest count, measured on every machine, three interleaved runs,
  spread printed. New flaws in N11, N12, N13.
- N2: fixed. Line 155-159: billed time from server start to upload; concurrency is a stage-2 ruling
  and the bar applies to the sum.
- N3: fixed in substance by the six-texture projection, line 160-165; weighting by class count is
  right for a line's cost because each class is solved once. The six groups sum to 1,755 (286, 858,
  156, 156, 286, 13). Its sequencing is B4.
- N4: not fixed. Closure is still stated as a requirement (line 49-52, 187) with no Taylor ruling
  cited and no stage-2 question; nothing in the ExecPlan names it for stage 2. It stays a
  non-blocker: stage 2 should put closure against breadth to Taylor coupled with where the index
  lives.
- N5: fixed. Line 59-60 reopens NVIDIA at stage 2; line 62-64 and 204-206 ask the target, the cap
  and the 1 percent ceiling together.
- N6: fixed. Line 198-199 calls the lines an upper bound; line 201-202 sends cell documents to object
  storage.
- N7: fixed. Line 219-224: fetched machine, voids split by street, turn voiding stated.
- N8: fixed. Guard tests and over-read repair line 134-138; payment and fetch line 208-211; refusal
  scope line 212-213; settling line 214-216; corpus share beside 74.9 percent with multiway named
  structural line 233-235.
- N9: fixed. The rainbow sentence and "never measured to target" are gone; ExecPlan line 28 lists
  `tree2.py`. Line 188-189 still says the walk reproduces "every committed object's" arena, and the
  objects sit outside git, which is accurate as worded.
- N10: fixed. Line 181-183 assigns ranges by seat position; line 184-186 re-derives tree, count,
  pot, arena and index cost per line.
- Alignment 1: fixed. Every entry named in N8 now has a criterion that closes it.
- Alignment 2: no longer needed; the fix landed in the contract.

New errors checked: the six texture group counts, the 12.87, 32.2 and 33.7 GB figures and the
ExecPlan's memory-bar bullet (ExecPlan line 45-47) all match my measurement. No new unfalsifiable
criterion, apart from line 214-216 ("unless stage 2 rules it out"), which matches the backlog
entry's own closing condition and is acceptable.

### What I held back in round 2

- I did not re-run `review_maxarena.py`; the numbers copied into the contract match what I wrote in
  round 1.
- The hour figures in B4 are M4 rates scaled by solve count, not measured on any box.
- I did not re-check the GPU status field or `atomicAdd`, as in round 1.
- I did not check whether a line longer than the wrap width fails any repo check.

## Round 3

Scope: `git diff b1dd5ac..62dce5d` over the contract (282 lines, under the 300 cap). Line numbers
are the contract at `62dce5d`.

- Reflow check: `git diff --word-diff` shows wording changes only in the places listed below. Every
  other hunk is whitespace. No line is longer than 100 columns.
- B4: fixed and marked [resolved]. The benchmark and campaign caps (line 145-152) remove the
  contradiction, and line 99-100 now agrees with them. The count adds up: at most five thread counts
  (default, quarter, half, three quarters, all, repeats dropped) times three runs is 15 stretches.
  On this Mac that is 3, 5, 8 and 10, so 12. Eight determinism solves plus six texture solves is 14.
  The sweep is now bounded in iterations (100 a stretch). At the slowest committed per-iteration
  rate, 4.93 seconds, 15 stretches is about 2.1 hours of solving at M4 speed. That is bounded but
  not trivial per candidate. The contract states counts rather than hours, which is what Taylor
  needs to price a cap against a quoted hourly rate.
- N4: fixed as a deferral. Line 197 closes boards "unless stage 2's decision 2 rules otherwise".
  I could not check the decision itself because it is not in the tree.
- N11: fixed at line 115-117, with the counts scaled to each machine. The logical-against-physical
  ambiguity is N16.
- N12: fixed at line 126. The re-solve runs at ten threads whatever count wins.
- N13: fixed at line 118. The median of three decides.
- N14: fixed. Nothing is over 100 columns, and N18 is the one leftover wrapping fragment.
- Other items keep their round 2 status. N1 is now fixed through N11 to N13.
- New: N15 (order the determinism re-proof before the six committed boards, and name the
  configuration they use), N16, N17, N18. None is a blocker.

The Blocker section now holds only [resolved] bullets.

### What I held back in round 3

- Stage 2's decision 2 is drafted outside the tree, so I have not read what it asks Taylor about
  closure.
- The 2.1-hour figure scales M4 rates. No rented box was measured, and I did not check which
  committed cell the sweep will use.
- The GPU status field and `atomicAdd` are still unchecked, as in earlier rounds.
