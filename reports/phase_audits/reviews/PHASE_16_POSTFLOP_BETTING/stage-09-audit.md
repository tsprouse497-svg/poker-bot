# Phase 16, stage 9: independent read-only review of the audit packet

Lane R7. I wrote none of stage 9 and edited nothing but this file. No gate command was run from this
worktree: `verification/.mutation_in_progress` was absent before I started, and the only `run_verify`
and `check_gate_bite` processes on this machine are rooted in `~/projects/poker-bot`, a different
checkout.

Subject: `reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md` (451 lines, cap 500), plus the three
other paths `e336c82` touched in the stage-9 scope: `backlog.yml`,
`docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md` and
`reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md`. Diff read as
`git show e336c82` against `1b5271b`.

## Method, stated once

Every figure below I computed in this worktree and the method is beside it. Nothing is taken from a
review note, the report, the decision list or the packet.

- **Method C, the census.** All 22,100 three-card boards enumerated and canonicalised under the 24
  suit permutations by a scratch script of my own outside the repo, not by the repo's helper.
- **Method F, the committed files.** Plain arithmetic over
  `data/artifacts/postflop/index.json`, the four files in `sample/`, `solve_config.json`,
  `deep_convergence_check.json` and `objects.json`.
- **Method O, the object store.** `sha256` over the five files in
  `~/poker-bot-solve-objects/postflop`, and range arithmetic over the decompressed node objects.
- **Method S, the dealer.** `run_simulation` from `poker_training_bot.simulator.run`, seed 777,
  20,000 hands, six seats. Run twice: once on `seat_profiles(SELF_PLAY, 6)`, which is the composite
  the repo builds, and once on a composite I assembled by hand from `PreflopChartStrategy.from_repo()`
  and `PostflopFallbackStrategy()` to reproduce the comparison row.
- **Method B, the backlog.** `backlog.yml` parsed at `HEAD`, at `main`, and at the merge base
  `1d89158`, and the three compared by id.

### What re-derived exactly

Every one of these came out identical to what the packet prints, to the digit:

| packet claim | my value |
| --- | --- |
| 1,755 flop classes over 22,100 boards; 455 rainbow, 1,014 two-tone, 286 monotone | identical (method C) |
| 8,788 / 12,168 / 1,144 boards per texture | identical (method C) |
| three held boards are 4 + 24 + 12 = 40 of 22,100, 0.1810 percent | identical (method C) |
| pot 5.5 = 0.5 + 2.5 + 2.5 and stack 97.5 = 100 − 2.5 in `monotone-connected-cbet.json` | identical (method F) |
| five index accuracies 0.2774, 0.2830, 0.2830, 0.2837, 0.2717 | identical (method F) |
| four committed spots out of three solved trees | identical: three distinct object digests (method F) |
| all object digests match the files they name | identical, all five (method O) |
| 20,000 hands, 4,543 flops, 2 postflop decisions both check, 0 bets, 0 showdowns, 5,365 voided | identical (method S) |
| the same run on the old fallback: 4,543 flops, 27,261 decisions all checks, 4,543 showdowns, 822 voided | identical (method S) |
| refusal split 3,775 line, 767 board, 822 preflop, 1 multiway | identical (method S) |
| 767 board arrivals is 16.88 percent of 4,543 flops | identical (method S) |
| the refusal inventory carries 113 and 26 rows for the first two codes | identical |
| caller arrives with 294.86 weighted combinations and checks 47.32 percent | identical (method O) |
| the four-row holdings table, all twelve figures, and 7.40 set combinations | identical (method O) |
| pair weights 22 0.9713, 33 0.208, 44 0.9997, 55 1, 66 1, 77 1, 88 0.9993, 99 0.4672 | identical (method F) |
| smallest range weights 0.0147 and 0.7865 | identical (method F) |
| deep solve 280 against 1,200 iterations, 0.2774 against 0.0478 percent | identical (method F) |
| the three-row movement table, and 19 pure at 0.0071 against 101 mixed at 0.1058, worst 0.4670 | identical (method F) |
| 16 classes changed preferred action and none of the 16 involved the check | identical (method F) |
| genuinely mixed on bet-or-check: 0 of 152, 209 of 342, 159 of 230, and 174 of 342 on raise-or-not | identical (method F) |
| the tested cell had at most 0.008 to move on any class | identical: `max p(check)` is exactly 0.008 (method F) |
| eleven successors split nine flop and two turn | identical, walked from the four cells' own action lists |
| bytes 4,938,950, headroom 16,032,570, postflop directory 100,845 | identical, measured off the tree |
| five status changes, all deferred to done | identical (method B) |
| the six named entries are still deferred | identical (method B) |
| 19 review notes, 25 decisions, contract at 299 of 300 | identical |

The median bullet is right and I want to say so plainly, because the packet struck its own earlier
claim to get here. Sorted, the 152 movements give a 76th value of exactly 0.053 and an interpolating
median of 0.0535. The report's 0.0530 is a real hand group's movement; 0.0535 is nobody's. The
packet's replacement bullet is correct.

## Blocker

- **B1. The packet strikes the sentence and then sends its reader to a document that states it as
  fact.** `reports/active/latest_postflop_betting_report.txt:418` reads "The bot bets a flop and then
  refuses every turn.", and line 517 of the same file says the missing hands "ended at the turn
  refusal". The packet lists that report first under "Reports worth opening" and sources ten of its
  twenty-one checklist rows from it, so the non-coding reviewer the packet is written for will open
  it. The packet's headline says the turn is never reached; the report says the bot refuses every
  turn. Nothing in the packet warns the reader, and nothing in `backlog.yml` owns it: the only entry
  `e336c82` filed is `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`, which is
  a different subject.

  This is not a wording slip and it cannot be fixed by editing the report, which is why it is worth
  stating exactly. Three things hold the sentence in place, and I checked each:

  1. `scripts/generate_postflop_betting_report.py:2347` and `:2592` emit both sentences, so every
     gate run rewrites them.
  2. `tests/test_postflop_betting_report.py:497-499` is a frozen test that **requires** them:
     `assert says(report, "refuses every turn") or says(report, "refuses the turn")`. Deleting the
     sentence from the generator reds the gate. `tests/**` is in neither `approved_scope` nor
     `standing_scope` in `CURRENT_TASK.yml`, so the phase cannot touch it without a freeze re-open.
  3. `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:270` obliges the packet itself to state the
     sentence, and the contract is at 299 of its 300-line cap, so it cannot be amended.

  What resolves this at stage 9, without a re-open and without touching the report: one sentence in
  the packet's "Reports worth opening" list saying that the betting report still carries the struck
  sentence and that the packet's own headline supersedes it, and one `backlog.yml` entry naming the
  generator line, the frozen test and the contract line as the three places that still assert it. The
  measurement is already in this note and in `stage-08-review-poker.md`; nothing needs re-solving.

- **B2. "files 92 new ones" is wrong. It is 93.** Method B, and the count does not depend on the
  baseline: `HEAD` holds 343 entries, `main` holds 261 and the merge base `1d89158` holds 250, and
  the ids present at `HEAD` and absent from either one number 93. All 93 are `deferred`, as the
  packet says, and the five status changes are exactly the five it names. The cause looks mechanical
  and is the shape this phase has been correcting all the way through: `e336c82` itself adds one
  entry, so 92 was true of the tree the packet was drafted against and false of the tree it shipped
  in. The packet's own opening promises every figure was measured again while it was written, and
  this is the one that was not measured again afterwards.

- **B3. The one recomputable-number section quotes a `spot_key` that is not the file it names.** The
  section names `data/artifacts/postflop/sample/monotone-connected-cbet.json` and then prints
  "the `spot_key` line at the top of the same file: `.../BTN:raise@2.5,BB:call/f:none/p:5.5/e:97.5`".
  That file's actual spot key is
  `f/b:9c8c7c/t6/d100/BTN/BTN:raise@2.5,BB:call/f:BB:check/p:5.5/e:97.5`. The string `f:none` occurs
  zero times in it; it belongs to the three big-blind-first cells. A reader doing exactly what the
  packet says, in a text editor, finds `f:BB:check` where the packet promised `f:none` and has no way
  to tell whether the packet or the file is wrong. This is the one section the contract requires to
  be checkable by hand, so an unverifiable line in it costs more than its size.

  The sentence above it is loose in the same place: "the same five numbers appear inside the
  situation's name". Three of them do. The blind structure's 0.5 and 1 are not in the key, and the
  key carries `t6` and `d100`, which the four things the reader was told to find do not.

## Non-blocker

- **N1. Two of the twenty-one rows cannot be worked by the reader the table is for, and one of the
  six spot-check steps sets a trap.** I walked all twenty-one rows and all six steps as a reader with
  no source files and no Python, and this is the answer to the question the packet exists to answer.

  - **Row 10**, "the five stored solve files are the ones the index claims", cites "five checksums
    recomputed here". Those five files are not in the repo. They are in
    `~/poker-bot-solve-objects/postflop`, four of them gzipped, and checking them needs a `sha256`
    tool and a shell. There is no way for the intended reader to do this row, and the row does not
    say so. It also sits oddly against the packet's own opening claim that every figure comes from a
    committed file or the repo's dealer; this one comes from neither.
  - **Row 4** and **spot-check step 2** tell the reader to count four files in `sample/` and five
    entries in `index.json` and conclude the fifth is "listed but not fetched". That works. But the
    same fifth situation, `Ac8c3c`, is the worked example in the small-pairs section, where the reader
    is told it is "such a board". The reader cannot open it, and the packet does not repeat there
    that it is the one file that is not here.
  - **Spot-check step 5** says the headroom figure is "the same number `index.json` carries as
    `headroom_bytes`". It is: I measured 16,032,570 off the tree, and both documents agree. But the
    line directly above it in `index.json` reads `committed_bytes: 100845`, and 20,971,520 minus
    100,845 is not 16,032,570. The report explains why these are three different questions; the
    packet does not, and the reader is standing in `index.json` when the contradiction appears.
  - **Spot-check step 6** says "add the five rows" over a block that prints six. The sum is right
    because the omitted row is zero, but a reader counting rows to check they have the right block
    counts six and stops.
  - **Row 13** says "the committed ranges have no weight under the 0.01 floor". True of the input
    ranges, which is where the report checks it. A reader who has just been sent into a sample file
    for the pot arithmetic and looks at `class_weights` there finds 108 values below 0.01 in
    `monotone-connected-cbet.json` alone. Those are action frequencies, not range weights. Two
    different things are called weights and the packet never separates them.

  Everything else works. Rows 1, 2, 3, 12 and 16 are arithmetic the reader does unaided; rows 5 to 9,
  11, 14, 15 and 19 are a named heading in a named report with the figure printed there, and I
  confirmed each heading exists and carries the figure. Rows 17 to 21 are verdicts rather than
  lookups and say so.

- **N2. "1,751 board classes with no committed cell" and "three boards is 40 of 22,100" count
  different sets, and the packet does not say which is which.** Both are right. The index lists four
  distinct classes, so 1,755 − 4 = 1,751; the repo holds three of them, so 4 + 24 + 12 = 40. The
  fourth class, `Ac8c3c`, is itself 4 boards (method C), so a reader reconciling the two figures is
  out by one class and four boards with nothing to tell them why.

- **N3. The packet claims one unmarked poker judgement and carries two.** Its closing paragraph says
  "The one place in this packet where a poker judgement is offered rather than measured is marked as
  such: the continuation bet on the three-club board". But the headline section ends
  "**That trade is deliberate and it is the right one.**", followed by an argument that a refusal is
  better than a fold. Decision 25 rules that the phase closes on machinery and that the packet says
  so plainly; it does not rule that refusing beats folding at a table, and nothing in this repo
  measures that. It is the one sentence in the packet that argues rather than reports, and it lands
  immediately after the sentence admitting the bot got worse, which is where an advocating document
  would put it.

  Two smaller instances, both milder: "the split is the useful part", and the recurring
  "X rather than Y" construction in which the packet narrates its own virtue ("states it rather than
  leaving a reader to find it", "carries it rather than the conclusion alone", "said out loud"). The
  substance underneath every one of them is honest, which is why this is a non-blocker and not a
  finding about the record. But a reader deciding whether to trust the phase is being told by the
  document that the document can be trusted.

- **N4. Decision 21's pairing holds where it is enforced by prose and lapses where it is not.** The
  continuation-bet section pairs 99.88 percent with the caller's 47.32 percent check correctly, and
  the bootstrap repeats the pairing. But the deep-solve section reprints the same cell's
  frequencies as 80.86 percent and 19.03 percent with no lead frequency in that section at all, 70
  lines further down. A reader reading front to back has seen the conditioning; a reader landing on
  the deep-solve table, or quoting it, has not. The packet already says nothing in the gate enforces
  the pairing, so this is the same exposure it names, showing up inside the packet itself.

- **N5. The rewritten bootstrap is true where it was rewritten and stale in the part that was
  carried over.** Answering the brief's sixth question directly: the new "Stage 9 of 11, running"
  block, the "what this phase shipped" block, the five rulings and the four pick-up items are all
  correct today. I checked: `verification/loop_runs/16.yml` says stage 9, `loop: running`;
  `reports/active/verify_results.json` holds 50 commands with `all_passed: true` and `check_gate_bite`
  among them, generated 2026-09-21; the five backlog ids cited in items 3 and 4 all exist; the 99.88
  against 52.68 pairing in decision 21's bullet reproduces; and the twenty-thousand-deal figures
  reproduce. Three things in it are not true today:

  - "**Four files** sit at exactly their cap" then names **five**, and all five are at their cap:
    `postflop_artifact.py` and `postflop_betting.py` at 500, `test_postflop_artifact.py`,
    `test_simulator.py` and `test_postflop_query_recording.py` at 700.
  - "`ruff format` is not in the gate and 39 of 50 test files fail it". Measured now: 56 files in
    `tests/`, of which 40 would be reformatted. Both halves of the figure have moved.
  - "every blocker across the five review notes in
    `reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/` is marked resolved". That directory
    holds 19 notes. The stage-8 resolutions were consolidated into `stage-08-review.md`, which is
    defensible, but `stage-08-review-poker.md`'s own B1 carries no `[resolved]` marker in its own
    file, and neither do the blockers in `stage-06-build-mechanical.md`, `stage-06-cells-poker.md`
    or `stage-04-repair-verification.md`. A next agent told "every blocker is marked resolved" who
    opens the directory finds otherwise.

  The section's header says it was rewritten at stage 9 "to what is true". The three items above are
  all in "Things that will bite you", which `e336c82` did not touch. That is the honest reading and
  it is worth writing down, because the same header now vouches for lines nobody re-measured.

## Alignment

- `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`. The packet makes this entry's cost
  visible in a new way and should be read as evidence for it: checklist row 10 asks a non-coding
  reviewer to confirm five checksums that the gate never re-derives and that the reader cannot reach.
  I re-derived all five by hand for this note, which is now the third hand re-derivation this phase
  has recorded. Already open, phase `contract-update`.

- `A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED`. The packet's one unmarked judgement (N3
  above) argues that voiding the hand is the right trade because the bot never plays a line nobody
  solved. This open entry, filed by this phase's own stage-6 domain review, argues that voiding
  biases the surviving record of the bot's flop betting toward the bets that worked. Both can be
  true, but the packet asserts the benefit and does not mention the cost, and the entry is not in the
  packet's limitations list. The drift is long-term and belongs here rather than in a stage-9 edit.
  Already open, phase 16.

- `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`. This entry and B1 above are
  the same fact seen from two sides: the entry corrects where the seam is, and B1 is the three places
  in the repo that still assert the old location. The entry does not name the generator line, the
  frozen test or the contract line, so closing it as written would leave all three standing. Already
  open, phase 16.
