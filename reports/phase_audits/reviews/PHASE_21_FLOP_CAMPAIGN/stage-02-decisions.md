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
rank.py's corpus order (BTN v BB 50, CO v BB 30, SB v BB 25, the `SB:call` limp 21, seventh place 6).
Two figures do not hold as stated, B4 and N2.

## Blocker

- [resolved] **B1. Decision 1, the most consequential item, is missing its most important fact and one
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

- [resolved] **B2. Decision 8 asks Taylor to freeze the 0.3 percent target without showing him the one
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

- [resolved] **B4. The "about 1.3 lines fit" figure (decisions 2 and 3) leaves out the object manifest, and
  option 3(c) may be less than one line.** 486.8 bytes is `index.json` alone, (2,866 - 432) / 5
  (ExecPlan line 43). Every committed spot also has its own entry in
  `data/artifacts/postflop/objects.json`, which is inside the same 20 MiB cap: (1,582 - 205) / 4 =
  344.25 bytes a spot today. At 831 bytes a spot, 14 on 1,755 flops is 20.4 MB a line and
  16,032,570 bytes holds 0.79 closed lines, and the two-decision figure is 5.5, not 9.4. If the
  campaign will key that manifest per board rather than per spot the figure recovers, but then the
  list must say so. As written, Taylor could pick (c), "stop at about 1.3 closed lines", and get no
  complete line. Fix the two figures (lines 56-57 and 73) or state the assumption.

- **B5 (round 2). The turn's storage figures, which the new recommendation 1(b) rests on, assume a
  format the repo does not use, and are 20 to 30 times too low compressed.** Decisions file at
  `e7948f5` lines 51-53 and 107 give the turn as "about 6.6 MB a flop, about 11.6 GB a line" and
  "about 6.6 MB before compression". That is one byte a strategy weight (`street_counts.py`: 16,709
  turn action slots x 396.5 hands = 6,625,118). Today's saved objects in
  `~/poker-bot-solve-objects/postflop` hold 1 or 2 decision points each and weigh 111,832 to
  126,883 bytes raw and 21,005 to 31,476 bytes compressed per decision point (`srp-Ac8c3c`,
  `srp-9c8c7c`, `srp-8c8d3c`, and `srp-Kh7d2c` at 238,026 raw and 62,951 compressed for two). At
  that format, 6,419 turn points are about 135 to 202 MB a flop compressed (0.72 to 0.81 GB raw),
  and 1,755 flops about 237 to 355 GB a line. The byte count is what Taylor pays to store
  (decision 4) and is the whole cost of 1(b) ("the turn costs storage, not solving", line 66), so
  either state today's figure beside the one-byte one, or make the smaller format part of the
  answer - it is written into every object, so that choice is frozen as well.

## Non-blocker

- **N1. Decision 9's "the committed chart's own reach puts other lines higher" rests on the wrong
  measure.** `rank.py` ranks by the arrival figure of the decision that closes a line
  (`scripts/generate_postflop_betting_report.py:1474-1483`), which is how often a seat is asked,
  not how often the line reaches a flop. On that measure `LJ:raise@2.5,HJ:call` (185.7 million per
  billion) and `BTN:raise@2.5,SB:call` (178.8) outrank the button against the big blind (150.0), but
  the chart never flat-calls an open from any seat but the big blind (call weight 0.0 at
  `t6/d100/HJ/LJ:raise@2.5` and every sibling; `COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY`),
  so those lines never happen in the bot's own play. Arrival times call rate times everyone behind
  folding gives, as a share of hands and ignoring card removal (`review2_linereach.py`): SB v BB 5.53
  percent, BTN v BB 3.66, CO v BB 2.75, HJ v BB 2.71, LJ v BB 2.42. The claim survives at rank 1 for a
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
  `"the flop campaign solves every turn and discards it" (proposed, not filed)`, carrying B1's arithmetic so the follow-on
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

## Round 2

Re-read at `e7948f5` (`git diff 63f9a6a..e7948f5`). Line numbers below are the decisions file at
that commit. Round 1's decision numbers 10 to 13 are now 11 to 14; a new 10 rules bet sizes. The
round 1 text above keeps its own numbering.

Mechanics: the loop's parser (`scripts/loop_stage.py:283-309`, run through `uv run`) reads 14
items, every `Reversibility:` line exactly one class, every bracket `[ ]`, 10 unanswered frozen.
Cross-references after renumbering all land: "if 1 is (b)" (82), "Decision 3" (82, 90), "decision
5" (111), "decision 9" (124), "decision 13" settling (142, 185), "if 7 is yes" (146), "decision 6"
(243), and "Ten questions ... Four more" (30). The ExecPlan and `verification/loop_runs/21.yml` cite
no phase 21 decision number. Nothing stale found.

Figures recomputed:

- 14 / 6,419 / 1,507,828 decision points, sum 1,514,261: true, by re-running `street_counts.py`,
  and the sum matches `nodes.py`'s action count, which was checked against GTOpen's own node count.
- Turn 6.6 MB a flop and 11.6 GB a line, river 1.4 GB a flop and 2.5 TB a line: the arithmetic is
  true at one byte a weight (6,625,118 x 1,755 = 11.6 GB; 1,435,610,722 x 1,755 = 2.52 TB), but not
  for the format the repo saves today - B5.
- 830.8 bytes, 0.79 and 5.5 lines: true (486.8 + 344 = 830.8; 16,032,570 / (14 x 1,755 x 830.8) =
  0.785; / (2 x 1,755 x 830.8) = 5.50).
- 8 to 22 hours: true. Timing and benchmark 3 x (1,500 x 1.34 + 1,677.4) = 11,062 s = 3.07 h to 3 x
  (1,500 x 4.93 + 1,677.4) = 27,217 s = 7.56 h; repeats 2 x 3,704.9 s = 2.06 h; six flops 6 x 375.6
  to 6 x 1,677.4 s = 0.63 to 2.80 h; settling 6 x 1,200 x 1.34 to 4.93 s = 2.68 to 9.86 h; total 8.44
  to 22.28 h. It leaves out the turn harvest if 1 is (b) - N11.
- `node_view` at `~/projects/gtopen/crates/solver/src/query.rs:490`: true. It walks the path through
  `walk_path`, which accepts `PathStep::Card` at chance nodes (`query.rs:14-19`, `325-331`) and
  adds each dealt card to the board it returns (`query.rs:495-497`); the server exposes it as
  `/api/node` (`crates/server/src/main.rs:2587`). What it costs is unmeasured: for the player to act
  it averages the strategy over the whole subtree below the node for every action (`query.rs:549-565`)
  and computes equity, so 6,419 calls a flop are not free - N11.

Status of every round 1 item:

- B1: fixed. The fact is stated (line 44), the option to keep the turn is (b) (58-59), 16.88
  percent (47-48) and 4,543 showdowns (60-61) are in, and the recommendation is now (b) (66-67). Its
  cost figure is wrong - raised as B5, not held against B1.
- B2: fixed. Lines 175-185 show the deep run, 4.8 times the time, 79 of 152 groups past 0.05 and the
  0.467 worst, and give Taylor a tighter-target option. One wording slip, N12.
- B3: partly fixed, still open. New decision 10 (205-214) rules the same sizes for every
  single-raised line, and decision 5 now gives the small blind line's memory (123-124). Still open:
  decision 9 says three-bet pots "follow them" (201) without saying whether phase 21 admits them,
  while contract line 231-232 stops the campaign at "the last line stage 2 admits" and line 154
  takes the memory bar over every admitted line before any machine is ranked; and 10 covers
  single-raised lines only, so an admitted three-bet line would reach stage 6 with its sizes
  unruled. One sentence in 9 ("phase 21 admits the five single-raised lines only", or the three-bet
  lines by name with 10 extended to them) closes it. Decision 10 should also say the other two
  pieces of the ruled configuration carry over, the raise of two and a half times (it does, 210)
  and no leading bet into the last aggressor (`"donk": []` in `solve_config.json`), since that one
  plays differently when the raiser is out of position.
- B4: fixed. Lines 77-79, 91 and 94-95.
- N1: fixed (196-201, and 124 names the small blind line). Wording slip, N13.
- N2: fixed. Settling runs counted (142, 145), the repeat solves use their recorded 2.1 hours (144),
  and a card trial comes out of the same budget (146-147). The budget is still asked only as money
  (149-150); fine.
- N3: fixed. Default is now one at a time (222-223).
- N4: fixed (253-255).
- N5: fixed (92-93).
- N6: fixed (108-109).
- N7: fixed in substance (37-38), with a wrong count, N14.
- N8: partly fixed. A word list (18-26), "Intel or AMD" (127), "fingerprint" (92), repeat-proof
  wording (120-121). Still undefined: "single-raised" and "three-bet pots" (196, 201, 214),
  "binary megabytes where the server means decimal" (251, a default rather than a question), and
  "manifest" (92).
- N9: fixed (232-233).

New in round 2:

- B5 (blocker, in `## Blocker` above): the turn storage figures.
- N10. Option (a) says a later phase "would have to solve every flop again" (57-58). GTOpen can also
  save a whole solve to disk (`/api/save`, `crates/server/src/main.rs:2259-2291`), so the honest
  wording is "solve again, or keep every full solve", and a full solve is about the size of its
  working memory, around 11 to 12 GB a flop on this line and so around 20 TB a line (unmeasured;
  the save format is not read here). It does not change the recommendation.
- N11. Decision 6's 8 to 22 hours has no time for reading the turn back out of the six closed flops,
  6,419 node queries each if 1 is (b), and each query does real work (above). The six flops are
  rented time, so the trial should time the harvest and the budget should say it is counted.
- N12. "Hands that always bet or always check did not move" (177) is slightly strong: the 19 groups
  playing one action moved 0.0071 on average and at most 0.042 (`PHASE_16_POSTFLOP_BETTING.md:306-309`,
  `deep_convergence_check.json` `movement.by_committed_shape.pure`). "Barely moved" is true.
- N13. "small blind opens 5.53 percent of hands" (197-198) reads as how often the small blind opens.
  The figure is how often the whole line - small blind opens, big blind calls, heads-up flop -
  happens. Reword as "the small blind opening and the big blind calling happens in 5.53 percent of
  hands".
- N14. "two of the six board types have never been timed" (37): three have. Timed: monotone
  (`9c8c7c`, `Ac8c3c`), rainbow unpaired (`Kh7d2c`), two-tone paired (`8c8d3c`). Never timed:
  two-tone unpaired, rainbow paired, trips.

Alignment items after the fixes:

- `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` and
  `A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED`: still needed. If 1 is (b), both seams move
  from the turn to the river rather than closing, and the entries should say that once Taylor rules.
- `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`: still needed. Its
  reason still says nothing has been solved deep (`backlog.yml:8940-8941`); decision 8 now quotes the
  deep run that says otherwise.
- `"the flop campaign solves every turn and discards it" (proposed, not filed)`: no longer needed as a standing entry, since
  decision 1 now puts the fact and the option in front of Taylor. File it only if he rules (a) or (d).
  The river is discarded under every option, but a river-rooted solve costs about 1/38,000 of a flop
  (`PHASE_16_POSTFLOP_BETTING_DECISIONS.md:187-188`), so re-solving it later is cheap and needs no
  entry.
- `LINE-RANKING-BY-CLOSING-DECISION-ARRIVAL-COUNTS-LINES-THE-CHART-NEVER-PLAYS`: still needed. The
  decision list is right now, but `arrival_key_for` (`scripts/generate_postflop_betting_report.py:1474-1483`)
  is unchanged and is the only ranking code in the repo, so the campaign report would reproduce the
  wrong order unless the entry marks it.

What I held back in round 2:

- I did not time a `node_view` call or read GTOpen's save format, so N10's 20 TB and N11's harvest
  cost are orders of size only.
- B5's per-point sizes come from four objects on one line; a turn point has the same hand lists, but
  its per-hand data may be smaller once blocked hands drop out, which would pull the figure down a
  little, not by twenty times.
- I did not re-check the 18.0 GB small blind figure beyond round 1's rough script; decision 5 now
  quotes it as "roughly", which is right.
- I did not judge whether (b) is the better poker call than (c), only that each is fairly stated.
