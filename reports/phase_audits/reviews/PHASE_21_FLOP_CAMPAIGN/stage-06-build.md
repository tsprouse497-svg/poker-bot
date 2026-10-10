# Phase 21 stage 6: build review

Read-only review by a subagent that wrote none of the work, 2026-10-10, of the stage's diff
`49f529c..1c054ce`, centred on the build commit 1c054ce and on d27cf1f and the merge 5e33c8a for
process. Every source file was read through git at 1c054ce, never from the working tree, because a
full gate was planting mutations there. Nothing was run in the worktree: the code ran from a
`git archive 1c054ce` copy in the session scratchpad, against the four kept exports in
`~/poker-bot-solve-objects/postflop-clone-b058335`, read-only. A second read-only subagent checked
the tree port against GTOpen's `tree.rs` at `c48f437`. Findings are kept as written; the
coordinator's response follows each, and only the reviewer marks a blocker resolved.

Round 2, 2026-10-10, same reviewer and rules, of `git diff 1c054ce 999ce2f`, read through git at
999ce2f and run from a fresh archive copy. The blocker is resolved; no new blocker. Round 2 findings
are the bullets marked "Round 2" under each section.

## Blocker
- [resolved] **The halt put to Taylor misdiagnoses the cause, and so misses an option.** The class-agreement
  finding itself is real: an independent reader written from `export.rs`'s format, grouping combos
  by the board's own suit stabiliser rather than through `postflop_harvest`, gives the same ten
  refused points with the same gaps - five on 9c8c7c (0.000541 to 0.001408), one on 8c8d3c
  (0.000734), four on Ac8c3c (0.000622 to 0.001440), Kh7d2c zero everywhere because its stabiliser
  is the identity - and the five committed spots re-derive their index digests and whole cell
  documents from the exports exactly. What is wrong is the backlog entry's reading that this "reads
  as the solve's own unconvergence". The drift is ordered by suit. Over every flop decision point,
  of the classes with three members and a spread above 1e-5, the largest-moving action is monotone
  in GTOpen's hand order (diamonds, hearts, spades) in 497 of 502 classes on 9c8c7c and 317 of 317
  on Ac8c3c; noise would give about one in three. Every refused class shows it, for example Ac8c3c
  after check, bet 33, raise: `Ad6d` calls 0.52283, `Ah6h` 0.52352, `As6s` 0.52419. And phase 16's
  own arena table (its decision list, the f32 rows) has the in-class gap growing with iterations,
  7.15e-05 at 320 to 1.40e-04 at 640, as the quantized one grew 5.03e-04 to 2.48e-03. A gap that is
  systematic by suit and grows with solving is a deterministic asymmetry in the solve, which more
  iterations will not remove, not a run that has not finished converging. Phase 16 said the check
  exists to see exactly this ("what a genuine mismatch between the solver's suit group and this
  repo's would look like"). The entry's three options all change what is stored to accommodate it;
  it should also offer diagnosing the asymmetry in the local clone first, the route decisions 17
  and 18 took, after which a re-solve has the solver as its reason, not the numbers. The poker size
  belongs in the question too: the widest gap is 0.144 percentage points of one action's frequency,
  and the refused points are deep ones (after a raise, or facing the big blind's lead), never a
  first decision. Fix: correct the entry's diagnosis and option list, and the ExecPlan's summary of
  it, before Taylor is asked.

## Non-blocker
- **The two halts are not independent, and the committed harvest cannot reproduce its own
  finding.** Run from the 1c054ce copy with `--out` in scratch, `scripts/harvest_postflop_closure.py`
  stops at the first board with an uncaught `artifact:unknown-field ... cell.flop_actions[2] has
  unknown keys: ['multiplier']` from the importer inside `_rederive`, before it prints a single
  refusal, because lane L's importer patch is not applied. So the ten refusals and the Kh7d2c
  "closes" result were produced on a tree that is not committed, and even a ruling on the class
  agreement closes nothing until the raise patch lands. The ExecPlan should say both. The escape is
  harmless (nothing is written before it), but it is a `PostflopArtifactError`, not the script's own
  `ClosureError` and its "Nothing was written" line.
- **Lane L's unapplied patch is right poker.** GTOpen raises to `street_bet[opp] * m`
  (`tree.rs:467`), so a raise adds its multiplier times the level it faces less the raiser's own
  standing bet, which is what the patch writes in `pot_before_hero_bb` and, rounded to chips, in
  `_flop_street`; the importer change passes `size_pct` or `multiplier` through to `FlopAction`,
  whose own validator refuses a raise with a percent and a bet with a multiplier. Until it lands
  every cell after a raise is refused at import, which fails closed rather than misplaying, and is
  what reddens the two raise tests (`artifact:unknown-field`, confirmed).
- **The bot's own raise is sized as a share of the pot but named as a multiple of the bet.**
  `PostflopBettingStrategy._amount` sizes a raise as the cell's fraction (4.5375 / 7.315 = 0.6203)
  times the pot as it stands; `flop_action_line` then names it by `_menu_multiplier`, within 0.05 of
  the pot of 2.5 times the level faced. The two agree only when the faced bet is near the nominal
  33 percent. Worked: pot 550 chips, a 160-chip bet (29.1 percent, which decision 14's matcher
  accepts as 33), the bot raises to round(0.6203 x 710) = 440, and |440 - 400| / 710 = 0.056 misses,
  so the next decision refuses. The window that misses is a faced bet in [28, 29.55) or (36.63, 38]
  percent of the pot; the 75 percent bet is clear across its whole band. Self-play never reaches it
  (bots bet exact fractions), which is why the frozen test passes; a human opponent at phase 20
  would. Fix: size the bot's raise to the menu multiplier times the faced level, as the solver did.
- **The candidate ranking does not use the bar the driver's guard reads.** `memory_exclusion`
  compares memory x 0.40 with the record's bar, and `candidate_rows` accepts any bar at or above
  the raw arena, 18,710,513,792 bytes. The driver's guard reads that arena 4.86 percent high, 19.62
  GB, so a box with between 46.78 and 49.05 GB of memory ranks and then refuses the small blind
  line's deuce-trips flop, the outcome the contract says ranking prevents. Nor does a candidate
  carry card memory, so a GPU candidate is ranked on host memory against a 51,239,107,576-byte card
  bar. Fix before any candidate record is written: require the bar to include
  `ARENA_READING_MARGIN`, and refuse a GPU candidate without its card memory.
- **The tree port is faithful.** The second reviewer read `postflop_tree_rule` against `tree.rs`
  line by line (facing a bet, minimum raise, all-in snap, dedupe, donk test, the decision 17
  check-through, chance nodes of 49 cards) and found only divergences that no ruled configuration
  reaches, since `menu_from_config` refuses any other. `postflop_tree_size` computes every figure by
  walking the rules, arenas by `game.rs:356-359` at full precision and card memory by
  `game.rs:369-377`; no pinned figure appears as a constant. Two independent rewrites from the Rust
  reproduce every figure: 4,144,704 and 4,339,626 nodes, 14 and 6,419 or 6,566 closure points,
  1,549,968 and 1,620,528 reachable river points, bars 13,042,185,280 and 18,710,513,792 on 2c2d2h.
  The memory estimate, like GTOpen's, leaves out the third arena the PCFR+ variant allocates, so it
  holds only on the default solver.
- **Lines are right.** `heads_up_seats` sorts by action order after the flop, so the small blind
  line posts the small blind's raising range out of position and the big blind's calling range in
  position; `line_reach` gives 5.530, 3.662, 2.752, 2.714 and 2.416 percent from the chart's
  `arrival_ppb` and combo-weighted action rates, the ruled order; `SB:call` is refused with the
  chart's own reason. The harvest goes through `postflop_lines`, not the solve script's
  button-line code.
- **The turn object is lossless apart from decision 15's rounding.** Re-encoding Kh7d2c's 6,419
  turn points and decoding them gives the export back within 0.0009999, the residue the largest
  entry pays on a three-action row; sizes match the ExecPlan (flop object 144,769 bytes, turn
  13,175,620, gzip saves 53.2 percent). Its readability is the alignment item below.
- **Fetch and manifest check what the contract says**: manifest counts against the line's tree,
  index bytes against the fingerprint, per-board counts, no river anywhere, each object against its
  listed digest, flop cell keys exactly the tree's keys (the canary's line is present verbatim), a
  turn object counted from its own bytes. A machine that fetched nothing, or holds a changed
  object, lists every closed board's keys as not held and refuses with
  `in-the-index-but-not-fetched`.
- **The report generator re-derives; it does not print.** Every figure is computed from the chart,
  the tree port, the manifests and the records; `NOT_YET_MEASURED` appears only where no record
  exists. Its two constants are labelled as phase 16's: the ceiling's numerator 194 (its
  denominator 259 and multiway 20 are re-counted and refused on drift), and phase 16's table result
  (20,000 hands, seed 777, 5,365 voided), printed only beside a re-run. Acceptable as labelled. The
  board section's "refused above the 1.0% ceiling" assumes exploitability is the only refusal; if
  Taylor's ruling adds another, that label needs his words. Beyond the committed-tree path nothing
  in it is exercised yet, since every record test stops at the missing manifest folder.
- **Red tests are what the halts explain.** On the 1c054ce copy the flop campaign and postflop test
  files give 732 passed, 20 failed and 18 errors: 35 on the missing manifest folder, 3 on the
  importer refusing `multiplier`. Nothing else. The whole suite on the copy gives 1,841 passed, 26
  failed, 18 errors; the six failures outside these files need a `.git` folder or `python` on the
  path, which an archive copy lacks, so 1,847 passing matches the commit message.
- **Scope is wider than the build.** `src/poker_training_bot/solver_artifacts/**` admits the
  preflop chart's own modules (`importer.py`, `chart_*.py`, `lookup.py`, `spot_key.py`), which the
  ExecPlan forbids. The build touched none of them, but the scope check can no longer say so. Narrow
  it to the postflop modules and `flop_campaign_report_records.py`.
- **The merge and the freeze lock are clean.** The only lock change at 5e33c8a is
  `tests/test_loop_fleet.py` at main's sha256 `f5cfe0bd...` with 58 functions and the floor 1,496 to
  1,512, which is main's 16 new tests; no build commit touches `tests/` or `verification/`.
- **The ExecPlan is stale in three places.** The Delegation Plan status still says lane R is
  assigned, though its generator is in 1c054ce; the rented-box slice compares GTOpen's small blind
  tree with "the port's 4,109,130 nodes", the pin's rule, where the clone's is 4,339,626; and Next
  Agent Bootstrap does not mention either halt.
- Round 2: **the blocker's fix holds, and every figure written into it re-derives.** 1,469 of 1,755
  classes is all but rainbow unpaired's 286, and 22,100 less its 6,864 flops is 15,236, 68.94
  percent. 0.144 percentage points is the widest gap, 0.001440 on Ac8c3c. The raise example: 0.6203
  x 710 = 440.4, so 440 chips against 2.5 x 160 = 400, and 40 / 710 = 0.056; the window 28 to 29.55
  and 36.63 to 38 percent follows from 2.5b / (1 + b) lying within 0.05 of 0.6203. 19,619,395,709
  bytes is 18,710,513,792 x 2^20 / 10^6, truncated. The paragraphs sit on the entries they name
  (raise tolerance, memory guard). `stage-06-raise-arithmetic.diff` is byte-identical to lane L's
  patch.
- Round 2: **two wordings put to Taylor are slightly off, both mine first.** "Never a first
  decision" is wrong for two of the ten: the in-position seat facing the big blind's lead on 9c8c7c
  and Ac8c3c is that seat's first flop decision. Accurate: every refused point follows a raise or
  the big blind's lead, and none is the root or the first decision after a check. And "the harvest
  stops ... before it reaches the class check" is loose: the class check runs (`flop_cells` comes
  before `_rederive`) and the script dies before it reports what it found. The coupling holds either
  way. Fix both phrases in the class-agreement entry and the ExecPlan before Taylor reads them.
- Round 2: **the candidate ranking fix is correct.** `guard_memory_bar_bytes` goes through the
  driver's own `arena_bytes`, so the two cannot drift; `rank_candidates` refuses a bar below it
  whenever it is given the server's arena, and `candidate_rows` always gives it, so a record ranked
  on the raw bar is refused (seen: 18,710,513,792 refused against 19,619,395,709). The card check
  ports GTOpen exactly: `gpu_budget` is free memory in whole 10^6-byte megabytes less 512, and the
  solve refuses the card when `estimate_vram`, which is `vram_estimate_bytes`, the figure
  `postflop_tree_size` mirrors, is above it (`main.rs:269-278`, `656-658`, `gpu/mod.rs:965-977`).
  Exercised on a synthetic record: a 48 GB box excluded, 49.049 GB ranked, an 80 GB card ranked, a
  51.7 GB card excluded at a 51,188,000,000-byte budget, and the record re-derives through
  `candidate_rows`. The flop campaign tests are unchanged at 732 passed, 20 failed and 18 errors, the
  same two halts.
- Round 2: **`candidate_rows` uses two bars inconsistently.** It re-ranks against the record's own
  host bar, which may sit above the campaign's, but always against the campaign's card bar, though
  the record may carry a higher `card_memory_bar_bytes`. A record ranked at a higher card bar, with a
  card whose budget falls between the two, would be refused for an excluded set that differs, under
  a message that does not say why. Re-rank with the record's card bar when it is present, as for the
  host bar.
- Round 2: **the narrowed scope covers every source file changed since `base_commit`**, and no
  preflop module.

## Alignment
- `THE-CLASS-AGREEMENT-RULE-REFUSES-TEN-OF-THE-FOUR-BOARDS-FIFTY-SIX-FLOP-DECISION-POINTS`: carry
  the corrected diagnosis from the blocker. Proposed new id for the cause, which outlives this
  ruling: `THE-SOLVE-DRIFTS-BY-SUIT-INSIDE-A-CLASS-AND-THE-DRIFT-GROWS-WITH-ITERATIONS`, closing when
  the asymmetry is located in the clone or shown to be inherent. The turn rows are stored per combo
  with no agreement check at all, so they carry the same drift unmeasured; that belongs in the same
  entry. `THE-COMMITTED-ROW-IS-ONE-COMBO-RATHER-THAN-AN-AGREED-ANSWER` is the existing entry any
  collapse ruling would close or amend.
- Proposed new id: `THE-TURN-OBJECT-NAMES-NOTHING-AND-ITS-ORDER-LIVES-IN-A-DOCSTRING`. The turn
  format holds shapes and counts only. A reader must rebuild each point's path and turn card, its
  menu and its hand list from the tree port, `solve_config.json` and `postflop_lines.line_ranges`
  over the committed chart and floor, following prose in the harvest's docstring. A later chart or
  floor change that keeps a point's row count would relabel rows silently. Closes when the line
  index or manifest records what fixes the order (the hand lists or their digest, the configuration
  digest, the solver build) and the phase that plays the turn checks them.
- `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`: the
  ranking gap above is this entry's over-read meeting a second consumer; note it there if it is not
  fixed in this stage.
- `THE-FLOP-RAISE-TOLERANCE-IS-BORROWED-FROM-THE-BET-MENU-RULING`: the bot's own raise sizing above
  is the same seam from the other side; note it there if it is not fixed in this stage.
- Round 2, proposed new id: `THE-MEMORY-GUARD-READS-HOST-MEMORY-NOT-A-CONTAINER-LIMIT`. The fixed
  ranking and the driver's guard both trust a machine's memory figure, and the machine record reads
  it from `/proc/meminfo` `MemTotal` or `SC_PHYS_PAGES` (`postflop_machine.py:182`, `227`). Inside
  a container, which is what a RunPod pod is (decision 5), both usually report the host's memory and
  not the pod's limit, so the 0.40 ceiling can sit above what the solve may use, and a candidate's
  `memory_bytes` copied from the host figure would rank a pod that cannot hold the bar. It is the
  memory twin of `THE-MACHINE-RECORD-COUNTS-PROCESSORS-GTOPEN-MAY-NOT-BE-ALLOWED-TO-USE`. Closes when
  the record also reads the cgroup memory limit, the guard and the ranking use the smaller figure,
  and a test proves it. Not verified on a pod: no rented machine has run.

## Coordinator response, 2026-10-10
- Blocker: the class-agreement entry now carries the suit-ordered cause, the iteration growth, the
  poker size (0.144 percentage points at most, deep points only), diagnosing the asymmetry in the
  clone as the first option, and the coupling with the raise patch; the ExecPlan's summary says the
  same. Filed `THE-SOLVE-DRIFTS-BY-SUIT-INSIDE-A-CLASS-AND-THE-DRIFT-GROWS-WITH-ITERATIONS` for the
  cause, including the unmeasured drift in per-combo turn rows. For the reviewer to mark resolved
  or not.
- Coupled halts: recorded in the backlog entry and the ExecPlan. The harvest's escape on the
  importer's refusal is left as is: it writes nothing first, and it disappears with the patch.
- Raise patch: kept for Taylor, now committed at `stage-06-raise-arithmetic.diff` beside this note
  so it outlives the session; still not applied, since the permission check refused it.
- The bot's own raise sizing: noted on `THE-FLOP-RAISE-TOLERANCE-IS-BORROWED-FROM-THE-BET-MENU-RULING`
  with the worked example, held with the raise patch because it is the same arithmetic.
- Candidate ranking: fixed by lane C (bar through the driver's own reading via
  `guard_memory_bar_bytes`, card memory and a card exclusion from GTOpen's `gpu_budget`) and lane R
  (`candidate_rows` passes both bars and refuses a record ranked on the raw bar). Noted on the
  memory guard entry.
- Scope: narrowed to the fourteen postflop modules, with a scope log entry.
- ExecPlan: lane R's status, the clone's 4,339,626 small blind nodes, and both halts in Next Agent
  Bootstrap, corrected.
- Alignment: both proposed ids filed; notes added to the memory guard and raise tolerance entries.


## Coordinator response, round 2, 2026-10-10
- Both phrases corrected in the class-agreement entry and the ExecPlan: every refused point follows
  a raise or the big blind's lead, none the root or the first decision after a check; and the
  harvest dies before it reports what the class check found.
- Card bar: lane R's `candidate_rows` now ranks against the record's own card bar when it states
  one, falling back to the campaign's, and still refuses one below the campaign's.
- Filed `THE-MEMORY-GUARD-READS-HOST-MEMORY-NOT-A-CONTAINER-LIMIT`.
