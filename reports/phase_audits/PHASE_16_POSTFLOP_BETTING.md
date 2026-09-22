# Phase 16 audit packet: Postflop That Can Bet

Contract `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` · Decisions
`reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` (25 items) · Reviews
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/` (19 notes, stages 1 to 8) · Report
`reports/active/latest_postflop_betting_report.txt`, rewritten by the gate on every run · Lane:
worktree `~/projects/poker-bot-worktrees/phase-16`, branch `phase/16-postflop-that-can-bet`.

Written for a reviewer who does not read code. **Every figure here was measured again while this
packet was written**, in this worktree, from a committed file or from the repo's own dealer, and
none was copied out of a review note, the report or a decision. Where a figure differs from an
earlier document the difference is printed and said out loud. A hyphenated capitalised name is the
id of a `backlog.yml` entry that carries the diagnosis; `report -> Section` names a heading in the
report above, which is greppable.

Phase 16 has more findings than this packet has lines. The findings are not restated here. They
live in the review notes named above, and the sections below point at the note that holds each one.

## What the phase set out to do, and what it built

Before this phase the bot could not put a chip in after the flop. Its postflop component checked
when checking was free, called on the turn and river only with a hand that provably cannot lose,
and folded the flop without asking. It never bet and never raised.

The phase built the machinery for flop play out of solved data: a spot key that names a flop
situation, a file format and a strict reader for solved cells, a driver that runs the solver, the
strategy that reads a cell and answers, and the report that publishes what all of it did. It then
solved four flop situations on three boards, committed them, proved the solve reproduces when it is
run again, and measured how far the answers move when one of them is solved four times deeper.

All of that works. The four situations import, the strategy returns a bet and a raise with real
chip amounts on them, and every figure in the report re-derives from a committed file when the
report is generated. **What the phase does not have is coverage**, and that is the next section,
because it is the thing a reader is most likely to miss and the thing that decides what this
artifact is good for.

## The headline: what the bot actually does at a table

Taylor ruled on 2026-09-21 (decision 25) that the phase closes on machinery rather than on
coverage, and that this packet says plainly what that buys and what it costs.

**Measured here, not quoted.** Twenty thousand hands dealt by the repo's own dealer, seed 777, six
seats each holding the composite strategy this repo actually builds:

| | hands | reached a flop | postflop decisions | of which bets | hands reaching showdown | hands voided |
| --- | --- | --- | --- | --- | --- | --- |
| the bot this phase ships | 20,000 | 4,543 | 2, both a check | **0** | **0** | 5,365 |
| the same bot on the old fallback | 20,000 | 4,543 | 27,261, all checks | 0 | 4,543 | 822 |

Same seed, same seats, same deals. The new component bet nothing in twenty thousand hands and
turned 4,543 hands that used to reach a showdown into hands the dealer voids.

Two causes, both arithmetic rather than defects.

**Coverage.** Three boards is 40 of the 22,100 three-card flops, 0.1810 percent, counted by
canonicalising every one of the 22,100 and adding the three classes' sizes: 4 plus 24 plus 12. One
preflop line is covered. In the 20,000 hands that line reached a flop 767 times, 16.88 percent of
the flops dealt, so the bot meets a held board about once in fourteen thousand hands.

**Closure.** The four committed situations offer twelve actions between them. One is a fold, which
ends the hand. **The other eleven each lead somewhere, and not one of those eleven is committed or
indexed.** The eleven split two ways, and the split is the useful part. **Nine are still on the
flop, and those nine are the gap this phase could have closed and did not.** The remaining two end
the flop and lead to a turn, which decision 1 put out of scope, so they are not a shortfall against
what this phase promised. Two of the four committed situations also cannot be reached from above,
because the situation leading into them is not committed either. There is no two-move sequence
anywhere in this artifact.

**The two postflop decisions in twenty thousand hands are the proof of that, and they are worth
reading.** Both are the big blind checking on a board of the `Kh7d2c` class, straight out of a
committed cell, and both hands then die immediately, because the next situation - the button facing
that check on that board - is exactly one of the **nine uncommitted flop situations**. The refusal
even names the key it could not find.

**So the sentence this packet was going to carry is struck.** "The bot bets a flop and then refuses
every turn" describes a bot this repo does not build. The turn is never reached, because the bot
refuses at hero's first flop action. What ships is a **flop chart** of four situations on three
boards and one preflop line. As a chart it is sound on what it holds. As a bot at a table it is
worse than the one it replaces, by the measured amount in the table above.

**That trade is deliberate and it is the right one.** A refusal voids the hand instead of playing
on, so the bot never plays out a line nobody solved, and a refusal that names the gap is better
than a fold that hides one. It is stated here rather than discovered by whoever runs it next.

## The one number a reader can recompute by hand

**The number is 5.5, the pot each committed situation was solved at, in big blinds.**

**The file**: `data/artifacts/postflop/sample/monotone-connected-cbet.json`. Any of the four files
in that directory works; this one is the smallest.

**The method**, with a calculator and no code. Open the file in a text editor and find four things,
each on its own line near the top:

- `blind_structure` says the small blind is 0.5 big blinds and the big blind is 1, with no ante.
- `preflop_actions` says the button raised to 2.5 big blinds and the big blind called.
- `pot_bb` says 5.5.
- `effective_stack_bb` says 97.5.

Now add up what is in the middle. Everyone else folded. The small blind folded and left its 0.5
behind. The button put in 2.5. The big blind called, so it put in 2.5 as well. **0.5 + 2.5 + 2.5 =
5.5**, which is what `pot_bb` says. The same arithmetic gives the second figure: each player started
with 100 big blinds and put in 2.5, so 100 − 2.5 = 97.5, which is what `effective_stack_bb` says.

**Why this is the number worth checking.** The contract requires that the pot and the stack a
situation is solved at come from the preflop betting that was substituted in, never from whatever
table happens to be asking. If those two numbers matched a table instead of the line, a hand played
at a different pot size would silently get an answer solved for a different pot. The arithmetic
above is the whole of that rule, and it is checkable in about a minute without opening any code.

The same five numbers appear inside the situation's name, which is the `spot_key` line at the top
of the same file: `.../BTN:raise@2.5,BB:call/f:none/p:5.5/e:97.5`.

## Pass and fail checklist for a reviewer who does not read code

Every row is something a reader can check by opening the named file and finding the named row. The
verdict column is what this packet measured, not what an earlier document reported.

| # | claim | where to look | verdict |
| --- | --- | --- | --- |
| 1 | The pot and stack come from the preflop line, not the table | the section above; 0.5 + 2.5 + 2.5 = 5.5 | PASS |
| 2 | There are 1,755 distinct flop classes over 22,100 flops | report -> The cost model; 455 + 1,014 + 286 = 1,755 | PASS |
| 3 | The three held boards cover 40 of 22,100 flops | 4 + 24 + 12 = 40, re-derived here | PASS |
| 4 | Four situations are committed and a fifth is listed but not on this machine | `data/artifacts/postflop/index.json` has 5 entries; `sample/` holds 4 files | PASS |
| 5 | Every committed entry records its accuracy, its iteration count and two digests | `index.json`, five entries, none blank | PASS |
| 6 | Every committed situation beat the 0.3 percent accuracy target | `index.json`: 0.2774, 0.2830, 0.2830, 0.2837, 0.2717 | PASS |
| 7 | Nothing was committed between 0.3 and 1.0 percent, and nothing was rejected above 1 percent | report -> Per-spot accuracy, last two rows; both 0 | PASS |
| 8 | Four committed situations rest on three solved runs, not four | report -> Per-spot accuracy; two rows name the run they share | PASS |
| 9 | The solve was run twice and the two answers are identical byte for byte | report -> Determinism, "strategies compared: byte-identical" | PASS |
| 10 | The five stored solve files are the ones the index claims | five checksums recomputed here; all five match | PASS |
| 11 | The strategy returns a bet and a raise with a real chip amount on them | report -> What the strategy does: 22 bets and 3 raises of 39 spots asked | PASS |
| 12 | Those counts add up | 22 + 3 + 4 calls + 7 checks + 3 folds = 39 | PASS |
| 13 | The committed ranges have no weight under the 0.01 floor | report -> The committed ranges; smallest are 0.0147 and 0.7865 | PASS |
| 14 | The bet menu is two sizes a street, the same for both seats | report -> The bet menu; flop 33 and 75 | PASS |
| 15 | Turn and river refuse by their own reason rather than folding | report -> Refusals by code; two turn and river codes exist | PASS |
| 16 | The committed data fits the 20 MiB budget with room left | 20,971,520 − 4,938,950 = 16,032,570 | PASS |
| 17 | The bot bets a flop at a table | measured here: 0 bets in 20,000 hands | **FAIL, by coverage, ruled and shipped** |
| 18 | Any committed situation leads to another committed one | 0 of 11 next situations committed, and 0 of the 9 still on the flop | **FAIL, ruled and shipped** |
| 19 | The artifact can answer a flop from the reference hand corpus | report -> The share of corpus flops; 0 of 259 | **FAIL, ruled and shipped** |
| 20 | The frequencies have stopped moving at the committed accuracy | one situation was checked, and it was the one with nothing to move | **NOT MEASURED for the other three** |
| 21 | Any of the above says the strategy is good poker | nothing here does | **NOT MEASURED, and no oracle exists** |

Rows 17 to 19 are failures that ship on purpose, each with a ruling behind it. Rows 20 and 21 are
the honest answers to the two questions a reader most wants answered.

**Sixteen refusal reasons are listed in the report with a count of zero beside them and the word
vacuous.** That is not the same as never firing. The report asks the strategy only about situations
it holds a cell for, so no refusal can arise there. At a simulated table they fire constantly: in
the 20,000 hands above the reasons were 3,775 "no cell for this preflop line", 767 "no cell for
this board", 822 preflop misses and 1 multiway, and `reports/active/latest_refusal_inventory.txt`
carries 113 and 26 rows for the first two. No document joins the two views, so a reader of the
betting report alone would conclude the codes have never fired anywhere.

### A spot check with no code at all

Fifteen minutes, a text editor and a calculator.

1. Open `data/artifacts/postflop/index.json`. Count the entries: five. Each names a board, an
   accuracy, an iteration count and two long hexadecimal strings. Check that no accuracy is above
   0.3 and that no field is blank or says something like "TODO".
2. Open `data/artifacts/postflop/sample/` and count the files: four. So one of the five entries has
   no file here. That is the fifth, `Ac8c3c`, and it is the "listed but not fetched" case the
   report has a row for.
3. Do the pot arithmetic from the section above on any one sample file.
4. Open `reports/active/latest_postflop_betting_report.txt` and find "What the strategy does". Add
   the five action counts: they must come to the number of spots asked. They do: 39.
5. In the same report find "Bytes". Subtract: 20,971,520 − 4,938,950 = 16,032,570, which is the
   headroom the report prints and the same number `index.json` carries as `headroom_bytes`.
6. In the same report find "The share of corpus flops". Add the five rows: 0 + 20 + 14 + 175 + 50 =
   259, which is the flop count above them. No hand is counted twice and none is dropped.

## The four qualifications, as qualifications and not as small print

These are conditions on what the committed data means. They are not caveats softening a claim; they
are the claim.

**One. Convergence at the committed iteration count is unproven.** What was measured is
exploitability, which is how much a perfect opponent wins against the strategy. That is not the same
as the strategy having stopped moving. Hands the solver has driven to a tie between two actions keep
trading frequency back and forth long after exploitability has flattened, because moving them costs
nothing by the measure being minimised. No packet, report or later phase may describe this data as
accurate to 0.3 percent.

**Two. The published accuracy binds only against an opponent confined to the same bet menu.** The
solve offers two bet sizes a street and one raise size. A number saying a perfect opponent wins
0.28 percent of the pot means a perfect opponent *restricted to those sizes*. An opponent with other
sizes is not measured anywhere.

**Three. Rainbow boards, and three rank patterns with them, were never solved to the target.**
Rainbow is 455 of the 1,755 classes and 39.76 percent of flops, and every rainbow cost figure in the
report is scaled from a converged run on a different texture rather than measured. The report's cost
table labels each row measured or scaled; nothing may quote a scaled figure as a measurement.

**Four. The repo holds an index and a three-board sample, not the artifact the bot plays.** The
solved files live in a directory outside git. A later phase measuring "the committed chart" has to
say which of the two it means. `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT` owns this.

## The continuation bet, and the number that must never travel without it

Ruled on 2026-09-21 as decision 21. The solve lets the out-of-position player bet the flop first,
which is legal poker, and the committed cells are a correct solution to the game as configured. They
ship. What must never travel without them is the second block below.

On the three-club board `9c8c7c`, hero on the button, after the big blind checks:

    hero checks 0.12% of the time and bets 99.88% of the time

Read alone, that is the sentence "the preflop raiser bets every flop", and a student drilled on it
would learn to bet every flop in position. It is not that sentence, because of what happened one
move earlier. Recomputed here from the stored solve file, whose checksum matches the one the index
commits:

    the big blind arrives with 294.86 weighted hand combinations
    it checks 47.32% of the time, so 52.68% of its range has already bet
    and hero is never asked in those hands

    holding            share before   share after   how often it bets instead
    high card              57.17%        57.53%          52.39%
    a pair                 30.27%        34.93%          45.40%
    a flush                 8.67%         4.79%          73.89%
    three of a kind         2.51%         1.38%          73.95%

The caller takes three quarters of its flushes and three quarters of its sets out of the pot before
hero acts. What is left in front of hero is a range with its best hands thinned out of it, and
betting almost everything into that is close to coherent. The true sentence is narrower: against a
caller who leads half its flops, what is left to bet into is weak.

Whether a caller who leads half its flops is the opponent worth drilling against is a ruling, not a
measurement, and the alternative was rejected on its merits: forbidding the out-of-position seat to
bet needs a patch to our own copy of the solver and buys a number comparable to a published chart by
modelling a game in which nobody may ever bet a flop out of position. That is a different wrong
answer, not a right one.

The preflop re-solve that preceded this campaign is not the cause and must not be recorded as having
fixed it. On this line the caller now holds 7.40 set combinations of a possible 9, which is what
that re-solve was predicted to deliver.

Nothing in the gate enforces this pairing. The block is in the report generator and no frozen test
asserts it, so a future regeneration could drop it and the gate would stay green.

## What refusing to smooth the caller's small pairs costs

The contract made this phase either repair or explicitly refuse
`EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`. Half of it was repaired: the 0.01 floor on input
ranges was ruled and the committed solves ran under it. The other half was **refused in writing** by
Taylor on 2026-09-21 as decision 23, in his words: "idk if we need to solve for this. if it's what
the solver says we should stick with it." That is this repo's standing position - we ship the
solver's output as solved, and the burden is on the objection.

This is what the refusal costs, and the packet states it rather than leaving a reader to find it.
Read off the committed ranges every cell was solved against:

    the caller's pocket pairs:  22 at 0.9713   33 at 0.208   44 at 0.9997   55 at 1
                                66 at 1        77 at 1       88 at 0.9993   99 at 0.4672

Threes call about a fifth as often as fours and deuces, for no strategic reason. It is an arbitrary
pick among options the preflop solve judged equally good, and it has a cost that depends on the
board rather than a cosmetic one. **On any flop holding a three, the caller arrives with about four
fifths of its sets of threes missing**: 0.208 of them present, 79.2 percent absent. `Ac8c3c`, the
fifth situation the index lists, is such a board.

So: the committed cells are solved against a caller whose small pairs are an arbitrary pick among
options the preflop solve judged equal, and on a flop holding a three that caller arrives missing
about four fifths of its sets of threes. The backlog entry stays open and unowned by this phase.

## What the deep solve settled, and what it did not

Decision 15 required one committed situation to be solved again with the iteration cap as its only
stopping rule, and its answers compared with the committed ones. That was done on `9c8c7c`: 280
iterations against 1,200, accuracy 0.2774 percent of pot against 0.0478 percent.

    action           committed     deep      moved
    check               0.12%     0.00%    -0.0012
    bet 33% of pot     80.86%    75.84%    -0.0502
    bet 75% of pot     19.03%    24.16%    +0.0513

**Whether to put money in had settled. Which size to bet had not.** The two bet sizes trade range
between them, and the hands that moved are the ones the committed strategy already had mixing: of
152 hand groups, the 19 playing a single action moved 0.0071 on average and the 101 genuinely mixed
ones moved 0.1058, worst 0.4670. Sixteen groups changed which action they prefer, and **all sixteen
switched between the two bet sizes**. None of them involved the check.

**The independent domain review at stage 8 found the limit of that conclusion, and this packet
carries it rather than the conclusion alone.** The deep check landed on the one situation of the
four where the bet-or-check decision was not genuinely mixed to begin with, so it could not have
falsified itself. Recomputed here, counting hand groups whose chance of betting sits strictly
between 5 and 95 percent:

    9c8c7c, button after a check      bet or check      0 of 152    (0.0%)
    Kh7d2c, big blind first to act    bet or check    209 of 342   (61.1%)
    8c8d3c, big blind first to act    bet or check    159 of 230   (69.1%)
    Kh7d2c, big blind facing a bet    raise or not    174 of 342   (50.9%)

On the dimension the phase drew its conclusion about, the tested situation had at most 0.008
available to move on any hand group. The three situations where the money decision is genuinely
mixed were not re-solved. So a reader may take the bet-or-check answer **from this one situation**
and may not generalise it, and qualification one above stands unchanged for the other three.
`NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED` stays open: its letter is
satisfied and its question is not.

## Every timing here is a laptop figure, and the determinism proof is machine-local

Ruled on 2026-09-21 as decision 24. The contract's scope says solving moves to a rented cloud
machine with every timing re-derived there. **That binds the campaign, not this sample.** The
three-board sample was a test of the machinery and it was solved here: an Apple M4, 10 cores,
34.4 GB, using the processor rather than a graphics card, four boards in about 62 minutes.

Two things follow.

**Every timing and memory figure this phase publishes is a laptop figure** and is re-derived on the
rented machine before a campaign is planned. The cost table's 759.7, 853.0 and 248.2 seconds a class
are this machine's.

**The proof that the solve reproduces is machine-local.** It is two runs in two processes on this
one Mac, so it constrains this machine and nothing else. The campaign re-proves it on the machine it
runs on rather than inheriting this. The rented machine differs by more than an addition order: it
is a different instruction set, where a compiler may fuse a multiply and an add where another does
not, and it exists to use a graphics-card solver that this contract's own scope calls untested. A
run on a graphics card is not this computation with its sums reordered.

The gap between the contract's wording and this ruling is filed as
`A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE` rather than amended, because
the contract sits at 299 of its 300-line cap.

## The backlog: five entries closed, two refused on the evidence

Measured against `main` while writing this: this lane changes the status of exactly five entries,
all from deferred to done, and files 92 new ones, all deferred.

**Closed.** `V2-POSTFLOP-STRATEGY`, on capability rather than coverage, and honest only while the
three coverage entries below stay open. `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`, which ships exactly
the rule the entry specified, behind a flag that is off by default, untested against an opponent that
bets because nothing bets at the bot. `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`.
`ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS`. `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`, which closed
because its stated condition was met rather than waived: one line in `docs/V2_ROADMAP.md` still
offered the falsified ratio as a basis for reasoning, it was fixed, and the sweep was re-run.

**Refused on the evidence, and a reader of the contract alone would not learn this.**

`POSTFLOP-UNBEATABLE-EARLIER-STREETS` is on the contract's Closed list and **did not close, because
the work it names was not done**. It asks for the unbeatable call to be extended from the turn back
to the flop. Nothing about that moved. What moved is its surroundings: the composite now routes
every postflop street to the new component, so the flop fold the entry was filed against no longer
happens, and the bot refuses instead. The entry's subject survives that, because on the 1,751 board
classes with no committed cell the bot now refuses where a hand that cannot lose could still call.
Closing it would record as done a piece of work nobody did.

`SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` was expected by the contract to leave the Closed list
because the rented Linux machine has the memory file that Darwin lacks. Decision 24 then ruled that
the sample was solved on the Mac, so the premise did not dissolve: it holds, for the machine
actually used. The restatement is the opposite of the one the contract drafted. Half the entry is
discharged - this phase's solve driver carries its own memory ceiling - and half is untouched.

That shape, a contract asserting a closure its own phase then refused, is filed as
`A-CONTRACT-CLOSED-LIST-ASSERTS-A-CLOSURE-ITS-PHASE-REFUSED-ON-EVIDENCE`.

**Explicitly not closed, as the contract requires**: `POSTFLOP-BOARD-ABSTRACTION`,
`POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`, `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`,
`THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`,
`THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` and
`THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP`. All six verified still deferred.

## Command summary, and the reports a reader can open

The phase adds two commands to the verification gate, both run by
`uv run python scripts/run_verify.py`:

- `pytest_postflop_betting` - the key, the committed-solve reader, the strategy and the report tests.
- `generate_postflop_betting_report` - writes
  `reports/active/latest_postflop_betting_report.txt`, re-deriving every figure it prints and
  exiting non-zero rather than writing a report when one does not reconcile.

Three mutation canaries guard them, in `verification/mutations.yml`: one breaks the weight-bounds
check, one breaks the rejection of a committed size that cannot legally be played, and one drifts
the report's own spot count, which is the canary aimed at this phase's new report command. All six
canaries that pin the old fallback and the composite were re-pointed with their claims unchanged and
none was retired, verified against `main`.

Reports worth opening: `reports/active/latest_postflop_betting_report.txt` (this phase),
`reports/active/latest_refusal_inventory.txt` (what the bot refuses at a simulated table),
`reports/active/latest_postflop_fallback_report.txt` (the component this replaces),
`reports/active/latest_verify.txt` and `reports/active/verify_results.json` (the gate).

**The recorded gate run is the stage-7 one**: 50 commands, all passed, including `check_gate_bite`,
which proves the committed canaries make the gate fail. The report generator changed after that
record while stage-8 findings were repaired, so the committed record predates the current generator.
The closeout re-runs the full gate before this phase is tagged, and that run is the one that counts.

## Known limitations and deferred items

Coverage and closure, which are the phase's own headline: `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`
for which boards are in, and `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`
for the fact that nothing leads anywhere. Even at the phase's full ruled coverage the ceiling is
about three quarters of corpus flops, because a two-range solve cannot express a three-handed pot at
any budget: `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`.

What a student would be taught, from the stage-8 domain review, which is the note to read before
anyone funds a campaign: the artifact resolves 4.65 percent of the stack at its deepest line and
then refuses, so it teaches the opening move of a three-street plan and deletes the plan
(`A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE`); a table of averages over
these cells can invert the conclusion a hand-by-hand table gives, which that note demonstrates on a
real cell (`NO-FIGURE-SPLITS-THE-FLOP-BET-FREQUENCY-INTO-VALUE-AND-BLUFF`); and the second preflop
line should be the small blind's open rather than the cutoff's, which buys a contrast rather than a
repeat.

Nothing in the gate can go red on any of that. Every figure in this packet comes from a committed
file or the repo's own dealer, and none is compared against anything that could fail. A bot that
bets zero times in twenty thousand hands passes every command the gate runs
(`NO-GATE-MEASURE-CAN-FAIL-ON-A-BAD-RANGE`, and `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL`
for why there is nothing to compare a frequency against).

Three smaller things a careful reader will meet, all measured here:

- **"Covered preflop lines committed: 2" counts chairs, not lines, and the two units are not
  comparable.** The index's two entries are `t6/d100/BTN/BTN:raise@2.5,BB:call` and
  `t6/d100/BB/BTN:raise@2.5,BB:call`: **the same betting sequence seen from two seats**. So the
  phase covers **one** distinct preflop line, not two. This matters beyond the wording, because the
  ranking that chose the line is a ranking over lines: the same report counts this same thing as
  one line with 50 arrivals, and the corpus reaches twelve. A reader who puts the 2 against the 12
  is comparing seats against lines and will read the coverage as twice what it is.
- **The report's "median: 0.0530" is deliberate and a reader recomputing it will get 0.0535.** The
  figure is a nearest-rank median, so it is one hand group's own movement: sorted, the 76th of the
  152 movements is exactly 0.053. A standard median function interpolates between the two middle
  values and returns 0.0535, which **is not any hand group's movement at all**. The file's own
  helper takes nearest rank for exactly that reason, and the report used to print the interpolated
  figure until a stage-6 reviewer filed it and it was fixed. The report is right; recomputing it
  the obvious way is what misleads.
- **"No cell for this board" is scoped to the preflop line being asked about.** A board committed
  for one chair reads as a board miss from the other. Both of the two postflop decisions in the
  20,000-hand run refused that way on `Kh7d2c`, a board the artifact does hold, because it holds it
  only for the other seat. The walk is behaving as specified; the wording invites a wrong reading.

Also open and named by the contract: `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`, which
this phase makes worse rather than closes - all ten checksums were re-derived by hand across the
stage-8 review and this packet, and the gate re-derives none of them.

## What this packet does not claim

No figure of chips won and no expected-value figure is published over this artifact. The hands such
a figure would come from are the ones that ended at a refusal, so the number does not exist rather
than being expensive to get.

No single accuracy figure is published for the artifact as a whole. The per-situation figures are
the evidence; one number over the set would be a claim nothing measured.

**A green gate says the committed data is internally consistent and that the walk refuses where it
says it refuses. It says nothing about whether this is good poker.** The repo has no postflop
reference to check a frequency against, and every shape property the gate checks is satisfied by a
uniformly wrong strategy. The one place in this packet where a poker judgement is offered rather
than measured is marked as such: the continuation bet on the three-club board is coherent given what
the caller has already taken out of the pot. Everything else here is arithmetic.
