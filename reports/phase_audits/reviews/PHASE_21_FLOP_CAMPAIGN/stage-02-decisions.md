# Phase 21 stage 2 review: the decision list

Independent read-only review of `reports/phase_audits/decisions/PHASE_21_FLOP_CAMPAIGN_DECISIONS.md`
as added in `63f9a6a` (diff from `023322b5d6554d5baac5f667b09f57b40bd4425f`). The reviewer wrote
none of it. Read against `AGENTS.md`, `docs/LOOP.md:133-149`, the contract
`docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md`, phase 16's decision list, packet and committed
data. Scratch scripts re-run: `tree.py`, `tree2.py`, `nodes.py`, `vram.py`, `rank.py`,
`review_maxarena.py`; two new ones written by this review in the same scratchpad,
`review2_linereach.py` and `review2_sbbb_arena.py`.

The loop's question - is every class right - has a short answer: yes. All nine frozen items are
frozen, and the four runtime-reversible ones change how fast or how the campaign runs rather than
what it commits, with one caveat on 13 (N4). The blockers are about what the frozen questions leave
out, because each is a question Taylor answers once and the answer is written into every cell.

Mechanics verified with the loop's own parser (`scripts/loop_stage.py:283-309`, run through
`uv run`): 13 items, every `Reversibility:` line holds exactly `frozen-into-data` or
`runtime-reversible` and nothing else (decisions file lines 32, 51, 67, 81, 96, 113, 134, 149, 162,
178, 187, 196, 205), every `Answer:` bracket is `[ ]`, which the parser treats as empty
(`loop_stage.py:307`), and `unanswered_frozen` returns 9.

Figures verified true: 1,755 x 375.6 = 659,178 s = 183.1 h and 1,755 x 1,677.4 = 2,943,837 s =
817.7 h (`data/artifacts/postflop/determinism.json`); 486.8 x 14 x 1,755 = 11,960,892 bytes and
16,032,570 / that = 1.34; the two-decision figure 9.38; headroom 20 x 2^20 - 4,938,950 tracked
bytes = 16,032,570; 14 flop decision points, 7 a seat (`tree2.py` and `tree.py` listing); memory bar
12.87 GB on `2d2h2s`, 32.18 GB at 0.40, 33.69 GB of card memory, 15.8 percent above 12.24 GB
(`review_maxarena.py`); objects 21,005 to 62,951 bytes on disk; over-read 1.048576, 4.86 percent;
`atomicAdd` at `~/projects/gtopen/crates/solver/src/gpu/kernels.cu:143-148`; the benchmark
arithmetic 1,500 rounds x 1.34 to 4.93 s = 0.56 to 2.05 h, plus 1,677.4 s = 0.47 h, three times,
plus 14 x 6.3 to 28.0 min = 1.5 to 6.5 h, totals 4.8 to 14.3 h, so "about 5 to 14 hours" holds;
rank.py's corpus order (BTN-BB 50, CO-BB 30, SB-BB 25, the `SB:call` limp 21, seventh place 6).
Two figures do not hold as stated, B4 and N2.

## Blocker

- **B1. Decision 1, the most consequential item, is missing its most important fact and one
  option.** A flop solve already solves the turn and the river: "a flop-rooted tree already contains
  and iterates its own turn and river subgames - it is 99.5% river nodes"
  (`reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:187-190`), and the
  campaign's tree is never saved (contract line 204-205: "the solved tree itself is never saved").
  So every hour the campaign buys also computes a turn strategy that is then thrown away, and the
  follow-on phase that option (a) recommends has to solve for it again. Rough size of that, from
  MAINT-26's turn-root cost of about 1/212 of a flop solve (same file line 187) and the 13 non-fold
  ways a flop can end on the committed tree (`tree.py` output): 13 x 49 turn cards = 637 turn solves
  a flop, about 3.0 flop solves' worth, so the follow-on's turn work is of the order of three flop
  campaigns unless it is kept now (an over-estimate by the all-in endings, which have no turn
  decisions; unmeasured storage). Taylor is asked to set a spending cap without being told this.
  The missing option is (d): save the turn decision points from the same solve into the bucket now,
  served by nobody until the follow-on phase - which, like (b), needs a `contract-update` because
  contract line 92 forbids committing turn spots. Two framing fixes in the same item: "moves every
  voided hand from the flop to the turn" (line 35-36) is true only on the lines and boards solved -
  in phase 16's own 20,000 hands the covered line was 16.88 percent of flops dealt
  (`reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md:57-58`), so even a complete first line leaves
  about five flops in six voiding on the flop; and option (b) should carry its measured upside (the
  old fallback reached 4,543 showdowns in the same 20,000 hands, packet line 50) and its poker cost
  (`A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE`: the flop bets assume a turn
  barrel, so checking the turn plays a strategy nobody solved, and any win rate over it is wrong).
  The recommendation (a) may well survive; it has to survive with (d) beside it.

- **B2. Decision 8 asks Taylor to freeze the 0.3 percent target without showing him the one
  measurement that bears on it.** `data/artifacts/postflop/deep_convergence_check.json` solved
  `9c8c7c` on from 280 to 1,200 rounds: per hand group the largest action change was mean 0.082,
  median 0.053, worst 0.467; 79 of 152 groups moved more than 0.05; 16 changed their preferred
  action, all sixteen between the two bet sizes; the small bet went 80.86 to 75.84 percent
  (`reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md:287-310`, "Whether to put money in had
  settled. Which size to bet had not."). The deep run took 1,812.6 s against 375.6 s, 4.8 times.
  That is the trade Taylor is actually ruling - bet-or-check is solid at 0.3 percent, bet size is
  not, and tightening costs several times the campaign - and item 8 (lines 149-158) says none of it.
  Its stated reason, keeping campaign flops and phase 16's flops the same kind of answer, is real
  (part 1's re-solve must reproduce phase 16's cells at their own target, contract line 206-209) but
  it is four boards against 1,755. Decision 12's settling sample also runs only after 8 is frozen,
  so the list should say that 12 cannot change 8's answer. The recommendation may stay "keep all
  three"; the question must show the numbers.

- **B3. A frozen call the contract leaves to stage 2 is missing: the solve configuration for any
  line other than the committed one, and which lines are admitted at all.** Contract line 170-171
  has the six texture flops solved "on the first admitted line under the configuration stage 2 rules
  for it", line 154 has the memory bar taken "over every flop of every line stage 2 admits, computed
  before any candidate is ranked", and line 231-232 stops the campaign at "the last line stage 2
  admits". Decision 9 gives an order and no admitted set, and no item rules the bet menu, raise size
  or donk rule for a new line (today `solve_config.json`, ruled for the button against the big
  blind). This bites at once: ranked by the chart's true reach (N1), the first line is the small
  blind raising and the big blind calling - pot 5.0 not 5.5, the raiser out of position, and wider
  ranges (742 and 494 combos against the committed 498 and 380). Rough largest arena on that line,
  assuming the committed tree's slot counts: 18.0 GB as the driver reads it on `2c2d2h`, needing
  about 45 GB of RAM at 0.40 (`review2_sbbb_arena.py`), against decision 5's 12.87 GB and 32.2 GB.
  Decision 5's "64 GB or more" still holds one such solve; decision 10's "two at once" would not.
  The menu choice is written into every cell of that line, so it is `frozen-into-data`. Either add
  the item, or have 9 name the admitted lines and state that each carries the committed menu
  unchanged, and have 5 say its memory figure is for the committed line only.

- **B4. The "about 1.3 lines fit" figure (decisions 2 and 3) leaves out the object manifest, and
  option 3(c) may be less than one line.** 486.8 bytes is `index.json` alone, (2,866 - 432) / 5
  (ExecPlan line 43). Every committed spot also has its own entry in
  `data/artifacts/postflop/objects.json`, which is inside the same 20 MiB cap: (1,582 - 205) / 4 =
  344.25 bytes a spot today. At 831 bytes a spot, 14 on 1,755 flops is 20.4 MB a line and
  16,032,570 bytes holds 0.79 closed lines, and the two-decision figure is 5.5, not 9.4. If the
  campaign will key that manifest per board rather than per spot the figure recovers, but then the
  list must say so. As written, Taylor could pick (c), "stop at about 1.3 closed lines", and get no
  complete line. Fix the two figures (lines 56-57 and 73) or state the assumption.

## Non-blocker

- **N1. Decision 9's "the committed chart's own reach puts other lines higher" rests on the wrong
  measure.** `rank.py` ranks by the arrival figure of the decision that closes a line
  (`scripts/generate_postflop_betting_report.py:1474-1483`), which is how often a seat is asked,
  not how often the line reaches a flop. On that measure `LJ:raise@2.5,HJ:call` (185.7 million per
  billion) and `BTN:raise@2.5,SB:call` (178.8) outrank the button against the big blind (150.0), but
  the chart never flat-calls an open from any seat but the big blind (call weight 0.0 at
  `t6/d100/HJ/LJ:raise@2.5` and every sibling; `COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY`),
  so those lines never happen in the bot's own play. Arrival times call rate times everyone behind
  folding gives, as a share of hands and ignoring card removal (`review2_linereach.py`): SB-BB 5.53
  percent, BTN-BB 3.66, CO-BB 2.75, HJ-BB 2.71, LJ-BB 2.42. The claim survives at rank 1 for a
  different reason than the one shown. The recommendation should define reach that way, and tell
  Taylor in plain words that his answer makes the small blind against the big blind the first line.
- **N2. Decision 6's machine-hour estimate leaves out decision 12's settling runs and sits below a
  known figure.** Six flops taken on to 1,200 rounds is about 900 more rounds each if continued, 6 x
  900 x 1.34 to 4.93 s = 2.0 to 7.4 hours, or 2.7 to 9.9 hours if solved fresh - as large as the
  whole benchmark - and no item says which cap pays for them. The 14 chosen-box solves' lower bound,
  1.5 hours, is below the eight determinism solves' own known total, 2 x 3,704.9 s = 2.06 hours. The
  GPU trial is to be "counted and capped in the same ruling" (contract line 150-151); decision 7's
  "try it later" should say that a yes makes it part of 6's answer. Stating the cap in machine hours
  as well as money would let Taylor multiply by a price he sees at sign-up.
- **N3. Decision 10's default has side effects it does not state.** Two solves at once share the
  memory speed GTOpen calls the bottleneck (`crates/server/src/main.rs:2551`), so the thread count
  decision 11 measures alone does not carry to two at once, and every wall clock written into a
  committed solve record becomes a shared-machine figure - the exact case the contract warns about
  (lines 119-121, 1.34 against 2.16 s a round). The default should say how threads are split and
  that such timings are marked. Class is still right: the answers do not change.
- **N4. Decision 13 is runtime-reversible because the contract says so (line 61-62), and stays so
  only if stage 4's frozen guard tests (contract line 137-141) do not pin the reading or the margin
  text.** Phase 16's list records that a default a frozen test pins is a fixture and so
  `frozen-into-data` (`PHASE_16_POSTFLOP_BETTING_DECISIONS.md:24-27`). Say so in 13 so the test
  author knows.
- **N5. Decision 3(a)'s manifest is too thin for the gate.** The report must re-derive coverage by
  board type, share of the 22,100 flops and fresh-clone coverage from committed files with no network
  (contract lines 242-250). "Counts and one digest" cannot. A per-line list of covered and refused
  boards is a few tens of KB a line and keeps that promise.
- **N6. Decision 4's reason overstates the lock-in.** The location sits once in the `index.json`
  header and once per spot in `objects.json`; the digests do not depend on it. Moving is a scripted
  rewrite, not a re-solve. The class is fine, since spending needs Taylor anyway (contract line
  99-100), but "which is why it is asked now" should not rest on a rewrite cost.
- **N7. The 183 to 818 hours scale figure (lines 24-28) is not a ceiling and should say so.** 15.8
  percent of flops plan a bigger arena than any board timed, two-tone unpaired (46.6 percent of
  flops) was never solved, a board may run to 1,200 rounds (1,200 x 4.93 s = 1.6 hours), and B3's
  first line is larger.
- **N8. Plain language.** Undefined for a non-engineer: "index", "object storage", "manifest",
  "digest" (3), "x86 and ARM", "determinism proof" (5), "single-raised" and "three-bet pots" (9),
  "binary megabytes where the server means decimal" (13). Each needs a six-word definition in the
  same sentence. Decisions 5 and 6 have honest no-price recommendations; 6 can still recommend a
  number of machine hours.
- **N9. Decision 11: on the rented box, that the thread count cannot change the answer is inferred
  from GTOpen's source, not measured there**; the box's determinism re-proof runs at one count. Say
  so, or re-prove one board at a second count.

## Alignment

- `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` and
  `A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED`: the campaign multiplies both by the number of
  lines it solves, and decision 1 cites neither. Whatever 1 rules should be written into both
  entries.
- `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`: its reason still says
  "nothing in the repo has solved a cell deep and diffed the frequencies" (`backlog.yml:8940-8941`),
  and `deep_convergence_check.json` has done exactly that since 2026-09-21. The entry should record
  the result before phase 21 closes it.
- Proposed new id for the coordinator, if Taylor rules 1(a) or 1(c) without (d):
  `THE-FLOP-CAMPAIGN-SOLVES-EVERY-TURN-AND-DISCARDS-IT`, carrying B1's arithmetic so the follow-on
  turn phase is priced knowing the work was once done.
- Proposed new id: `LINE-RANKING-BY-CLOSING-DECISION-ARRIVAL-COUNTS-LINES-THE-CHART-NEVER-PLAYS`,
  for `arrival_key_for` in `scripts/generate_postflop_betting_report.py:1474` and any ranking built
  on it (N1).

## What I held back

- I did not check whether GTOpen can hand back turn decision points from a flop solve through its
  server routes, or what saving them would cost in storage; B1's option (d) assumes the tree holds
  them (it does, per the node counts) and that the harvest can reach them. That is the first thing
  to measure if Taylor leans toward (d).
- B3's 18.0 GB is rough: it reuses the committed tree's per-seat slot counts, while a 5.0 pot
  changes bet sizes and all-in snapping, and it takes every combo with any call weight rather than
  the floor phase 16 applied to the committed ranges (committed 380 against the chart's 412). The
  true figure needs `nodes.py` re-walked for that line.
- N1's reach figures ignore card removal and assume the chart's weights are the bot's play.
- I did not judge whether 0.3 percent is the right target, only that item 8 hides the evidence;
  nor whether the 66/125 turn and river menu suits a small-blind line.
- Decision 10 is borderline between classes: "runtime-reversible" is defined as query-time, and
  concurrency is neither query-time nor written into what later phases are measured against. I left
  it where it is.
