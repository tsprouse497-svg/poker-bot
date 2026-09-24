# Phase 16, stage 8: independent domain review, the turn seam and the play that ships

Read-only. The reviewer wrote none of the work under review and holds the domain brief: the poker,
not the code's fidelity to the contract, which is `stage-08-review-mechanical.md`'s and is not
touched here. `stage-06-cells-poker.md` is the previous domain pass over the same cells and nothing
in it is re-filed; where this note disagrees with it, it says so and shows the measurement.

Under review: the committed artifact at `data/artifacts/postflop/`, the strategy that reads it, and
the composite the repo builds, at `679fea1` on `phase/16-postflop-that-can-bet`. Nothing was written
except this file. The gate, the bite check and the solver were not run.

## Method, stated once

Every figure below was computed in this worktree today and each one says how.

**Method S, the repo's own simulator.** `simulator.run.run_simulation` with six copies of
`profiles.seating.composite_profile()`, which is `CompositeStrategy.from_repo()`, at six-handed
100bb and blinds 50/100. Seeds and hand counts are named at each figure. This is the bot the repo
builds, not a fixture.

**Method R, range-weighted over a committed cell.** Expand all 1,326 two-card combinations, drop
the ones the board blocks, weight each by the acting seat's class weight in `solve_config.json`,
map it to the cell's label with `solver_artifacts.postflop_isomorphism.canonical_hole_cards`, and
average the committed row. On the two cells this note uses it reproduces the report's own
range-weighted column to four decimals, so it is the artifact's own convention rather than a second
one.

**Method C, combo-level.** The same expansion, but each combination reported separately rather than
averaged into a category. Where R and C disagree the note prints both, because they answer different
questions and one of this note's findings is that they disagree.

**Method D, recomputed from the committed deep check.** Arithmetic over the parallel arrays in
`data/artifacts/postflop/deep_convergence_check.json`, which the file itself says are there so that
every figure in it can be recomputed without re-running anything.

**Method K, spot keys.** The five keys in `index.json`, and the key of each node that follows a
committed cell's own actions, compared as strings. The key format is
`f/b:<board>/t6/d100/<hero>/<preflop line>/f:<flop line>/p:<pot>/e:<stack>` and hero's position is
its own field, so a successor's key is the same key with the other seat and one more flop action.

Hand categories come from `poker_core.hand_eval.evaluate_best` over the five cards.

## Blocker

- [resolved] **B1. The phase ships a seam it places at the turn. On the repo's own simulator the artifact
  makes no flop bet at all, and every hand that reaches a flop is voided, so the packet obligation
  as the contract words it would state the seam in a place it does not occur.** A paragraph in the
  stage-9 packet closes this. It needs no re-solve, no contract edit and no new data.

Method S, seed 777, 20,000 dealt hands, six copies of the composite the repo builds:

| | hands | flops reached | postflop decisions | of which bets | completed postflop hands | voided |
| --- | --- | --- | --- | --- | --- | --- |
| the composite this phase ships | 20,000 | 4,543 | 2, both `check` | **0** | **0** | 5,365 |
| the same composite on phase 06's fallback | 20,000 | 4,543 | every one | n/a | 4,543 showdowns | 822 |

Same seed, same seats, same deals. The betting strategy produced two checks and not one bet in
twenty thousand hands, and converted 4,543 hands that previously played to showdown into voided
hands. A second run at seed 20260921 over 3,000 hands gives the same shape: 683 flops, 683 voids,
zero postflop decisions, against 683 showdowns on the fallback.

The cause is coverage and it is arithmetic rather than a defect. Brute-forced over all 22,100
three-card boards with `canonical_board`, the three boards this clone holds stand for 40 of them:
`9c8c7c` 4, `Kh7d2c` 24, `8c8d3c` 12. That is 0.1810% of flops, and 0.1629% once `9c8c7c` is set
aside for the reason in B1's second half below. Method S on the same 20,000 hands splits the
refusals 3,775 `no-cell-for-this-preflop-line`, 822 `spot-not-covered` preflop, 767
`no-cell-for-this-board` and 1 multiway, so the covered preflop line reaches a flop 767 times,
16.88% of the 4,543 flops and 3.84% of hands dealt. Multiply that by 40 of 22,100 and the bot meets
a board it holds **about once in fourteen thousand hands**.

**And the seam is not one street early, it is at hero's first action.** Method K over all five
indexed keys and the eleven nodes that follow the four held cells' own actions: **not one successor
node is committed, and not one is even indexed.** Two of the four cells are also unreachable from
the artifact's own play in the other direction:

| committed cell | the node above it | the nodes below it |
| --- | --- | --- |
| `9c8c7c`, BTN after `BB:check` | the big blind's own first decision on `9c8c7c` is **not committed** | none of the three |
| `Kh7d2c`, BB first to act | hero is first to act | none of the three |
| `Kh7d2c`, BB facing `BTN:bet@33` | the button's continuation bet on `Kh7d2c` is **not committed** | none of the three |
| `8c8d3c`, BB first to act | hero is first to act | none of the three |

So the artifact holds a continuation-bet cell for a node it cannot reach, and a facing-a-bet cell
answering a bet it cannot make. `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`
already corrects the seam's location from the turn to the flop, and it was measured against a
synthetic sample holding the four ruled situations. Against the four cells that actually shipped it
is one step worse than that entry says: there is no two-node chain in the committed set at all, so
even the "check, bet, raise" walk the entry describes cannot be run.

What resolves this: the stage-9 packet states, in its own words and with a number a reader can
recompute, that the artifact holds 40 of 22,100 boards on one preflop line, that no committed cell's
successor is committed, and that the bot therefore refuses at hero's first flop action rather than
at the turn. Writing "the bot bets a flop and then refuses every turn" without that is a statement
about a bot the repo does not build. Closing the phase on it is the false claim the phase is
currently set up to make, and it is the same failure shape the stage-7 note corrected in a smaller
place.

[resolved] 2026-09-24 by MAINT-38: every bullet above that lacked a marker was audited by an independent lane and marked where the fix or ruling is shown, finding by finding, in `reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`.

## Non-blocker

**N1. The deep convergence check moved the one dimension that had mass and reported "settled" about
the one that had none, and the three cells where the money decision is genuinely mixed have no deep
solve.** This is the sharpest thing I found outside B1, and it is an answer to the brief's third
question rather than a complaint about the file, which is careful and honest within its own scope.

Method D over the 152 classes of `monotone-connected-cbet`:

| | committed, 280 iterations | deep, 1,200 iterations |
| --- | --- | --- |
| classes genuinely mixed on bet-versus-check, meaning `p(bet)` strictly inside 0.05 and 0.95 | **0 of 152** | 0 of 152 |
| largest movement in `p(bet)` on any one class | **0.008** | |
| mean movement in `p(bet)` | 0.0011 | |
| largest movement in the size split, the 75% share of the hands that bet | **0.4665** | |
| mean movement in the size split | 0.0809 | |
| classes whose preferred action changed | 16, **all sixteen** from 33% to 75% | |

Not one of the sixteen preference changes involves the check. The file's own reason for choosing
this cell reproduces exactly - 19 of 152 classes put 0.99 or more on a single action and 101 spread
past a tenth onto a second - so it is the most mixed cell on the three-action simplex, and all of
that mixture is in the size. On the dimension the phase drew its conclusion about, this cell had at
most 0.008 available to move on any class.

The mechanism is visible in the same file and it is ordinary solver behaviour, which answers the
brief's question about whether this matches expectation: it matches it precisely. 90 of the 152
classes carried a small non-zero check at 280 iterations, largest 0.008, and at 1,200 iterations
**all 152 read exactly 0.000**. That is a residual on a losing action decaying toward zero, not a
decision settling. The exploitability fell 0.2774% to 0.0478% of pot over a 4.3-fold increase in
iterations, which is faster than the square-root rate a reader would assume and is normal for this
family of solver; the average strategy at an indifference point wandering while exploitability falls
is also normal. Nothing here is a solver misbehaving.

What the phase should not take from it is a general answer, and the report does not: it says the
reader may take the bet-or-check answer *from this cell*. The gap is that the cells a student would
be drilled on have a genuinely mixed money decision and none of them was re-solved:

| cell | the money decision | classes genuinely mixed on it |
| --- | --- | --- |
| `9c8c7c`, BTN after a check | bet or check | **0 of 152 (0.0%)** |
| `Kh7d2c`, BB first to act | bet or check | 209 of 342 (61.1%) |
| `8c8d3c`, BB first to act | bet or check | 159 of 230 (69.1%) |
| `Kh7d2c`, BB facing a bet | raise or not | 174 of 342 (50.9%) |

The phase's own bucket table predicts what would happen to those: pure classes moved 0.0071 on
average and mixed ones 0.1058, worst 0.4670. Apply that rule to a lead frequency of 15.39% and it is
the difference between a strategy that leads and one that does not. One further solve, on either
donk cell, is the measurement that would settle it, and it is the same price as the one already
paid. Recorded rather than asked for, because a re-solve is new committed data and stops for a human.

**N2. What a student is taught that the earlier note did not name: the artifact stops with almost
all of the money still behind, so it teaches the opening move of a plan and deletes the plan.**
Arithmetic from the cells' own sizes against a 5.5bb pot and 97.5bb effective:

| line the artifact can describe | each seat puts in | pot after | stack still behind | share of the stack still behind | stack-to-pot after |
| --- | --- | --- | --- | --- | --- |
| bet 33%, called | 1.815bb | 9.13bb | 95.685bb | **98.14%** | 10.48 |
| bet 75%, called | 4.125bb | 13.75bb | 93.375bb | 95.77% | 6.79 |
| bet 33%, raised to 4.5375, called | 4.5375bb | 14.575bb | 92.963bb | 95.35% | 6.38 |

The pot starts at a stack-to-pot ratio of 17.73. The deepest line in the committed set resolves
4.65% of the stack, and the artifact then refuses. `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE`
states that a flop bet's value here is largely the leverage it creates later; these are the numbers
under that sentence, and they say the leverage is essentially all of it.

The habit a good player would have to unlearn is therefore not a frequency, it is a category error:
that a flop betting frequency is a rule about the flop. It is not. 99.88% on the monotone board and
15.39% on the dry one are the first move of a three-street plan whose second and third moves are the
reason for the first, and the student drilling this artifact would be trained to produce the first
move on cue and never once asked the question that makes it correct. A student who then sits down
and bets the flop at those frequencies against a real opponent, with no barrelling plan, is playing
a strategy that is worse than checking, because the frequencies are sized for a threat that never
arrives. That is a harder habit to unlearn than any of the three the stage-6 note named, because it
is invisible: nothing in the drill would ever look wrong.

**N3. The big blind's lead on the dry board is better poker than its category averages suggest, and
I checked rather than assuming. This is the correction I owe the stage-6 note's shape.** My first cut
was method R over `Kh7d2c`, BB first to act, and it looked strength-blind:

| category | share of range | check | bet 33% | bet 75% |
| --- | --- | --- | --- | --- |
| no pair | 60.40% | 0.8473 | 0.1148 | 0.0379 |
| top pair | 21.85% | 0.8600 | 0.1153 | 0.0247 |
| pocket pair below top | 9.73% | 0.8914 | 0.0970 | 0.0116 |
| middle pair | 2.50% | 0.9240 | 0.0650 | 0.0110 |
| bottom pair | 2.08% | 0.7267 | 0.2088 | 0.0645 |
| three of a kind | 2.05% | 0.5546 | 0.2622 | 0.1832 |
| two pair | 1.39% | 0.7255 | 0.2172 | 0.0572 |
| **whole range** | **100%** | **0.8461** | **0.1183** | **0.0356** |

No pair and top pair are 82.25% of the range and they lead at 0.1148 and 0.1153, a gap of five
ten-thousandths, and the lead range's composition is a near-copy of the checking range's: 58.60%
against 60.49% no pair, 21.29% against 22.21% top pair. On those figures the lead separates nothing
and would be a residual rather than a strategy.

Method C says that reading is wrong, and the category average is the wrong lens. Combo by combo:

| | combinations | mean `p(bet)` | standard deviation | share under 0.02 | share over 0.50 | largest |
| --- | --- | --- | --- | --- | --- | --- |
| no pair | 212 | 0.1921 | 0.2756 | **48.6%** | **19.3%** | 0.996 |
| top pair | 63 | 0.1400 | 0.0819 | 0.0% | 0.0% | 0.401 |

The no-pair block is not uniform at all, it is two blocks: nearly half of it never leads and a fifth
of it leads more often than not, one combination at 0.996. That is a bluffing selection, and the
range-weighted average hid it completely. Top pair is ordered by kicker in the right direction, mean
`p(bet)` by kicker: KQ 0.2789, KJ 0.1502, KT 0.1140, K9 0.0882, K8 0.0827, K6 0.0753, K5 0.0957,
K4 0.0873, K3 0.0740. A spread of 0.2789 down to 0.0740 across nine kickers, monotone over the four
with twelve combinations each, is real structure and not noise. Filed as a positive finding, and as
a caution that a category table over these cells can invert the conclusion.

**N4. The one thing in the committed play I would question with a number, stated as an intuition
because the repo holds nothing to check it against.** Method R: the big blind leads 15.39% of its
range into the preflop raiser on `Kh7d2c` and 29.84% on `8c8d3c`, and within the first of those,
top pair leads 11.53% and king-queen specifically 27.89% by method C. Leading a third of the pot
with top pair and a good kicker, out of position, into the range that raised preflop, is the line I
would least expect to survive a second opinion: it is the hand with the most to gain from keeping
the raiser's whole bluffing range in the pot, and the artifact bets it more than any other top pair.
I cannot produce a reference number, the repo holds no external postflop solution to compare
against, and `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` is exactly why. So this is
an intuition with a measured subject, not a measured objection, and it is not a reason to hold
anything. It is, though, the single number I would spend one deep solve on if N1's solve had to
answer two questions at once, because the same solve would answer both.

**N5. One preflop line is the right one, it is useful rather than a curiosity, and the second line
should be the small blind's open rather than the cutoff's.** Counted by me from the 499 committed
public-corpus hands, parsing each hand's actions to the first dealt board and applying decision 10's
own 20% price band, so a 2.25bb open reads as `@2.5`:

| rank | substituted preflop line | heads-up flops | share of the 259 flop-reaching hands |
| --- | --- | --- | --- |
| 1 | `BTN:raise@2.5,BB:call` | 50 | **19.31%** |
| 2 | `CO:raise@2.5,BB:call` | 30 | 11.58% |
| 3 | `SB:raise@2.5,BB:call` | 25 | 9.65% |
| 4 | `SB:call,BB:call` | 21 | 8.11% |
| 5 | `LJ:raise@2.5,BB:call` | 20 | 7.72% |
| 6 | `HJ:raise@2.5,BB:call` | 19 | 7.34% |

The whole "one seat opens, the big blind calls" family is 144 of 259, 55.60% of flops, and the
button is 34.7% of that family. So the chosen line is the single most frequent postflop
configuration in the corpus by a wide margin, and it is also the one where both ranges are at their
widest, which is where a student's errors are largest and most costly. That is the right first line
and I would not move it.

It is a curiosity only in the sense B1 measures: one line with every board solved would answer
19.31% of corpus flops, against the 74.9% ceiling
`THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS` computes for the phase's full ruled
coverage. One line is a fifth of the flops and a real fifth.

The second line should be `SB:raise@2.5,BB:call`, third by arrival at 9.65% and five hands behind
the cutoff, and the poker reason beats the five hands. Every line above it puts the preflop raiser
**in position**, so a student drilling button-versus-big-blind and then cutoff-versus-big-blind
learns the same positional lesson twice with slightly different range widths, and has no way to tell
which of their new habits is about position and which is about range. The small blind's open is the
most frequent single-raised pot in which the raiser is out of position, it is the one configuration
the current artifact cannot teach at any board count, and it is the spot where a player who has only
ever studied in position goes most wrong. Adding it buys a contrast; adding the cutoff buys a
replicate.

## Alignment

- **The shipped bot's postflop behaviour is zero bets in twenty thousand hands, and the coverage
  arithmetic that produces it is a board-count question rather than a strategy one.** Owned jointly
  by `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY` for which boards are in and
  `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN` for the closure half. B1 is
  the measured instance of both against the cells that actually shipped rather than against a
  synthetic sample.

- **The selection bias an earlier review found in the voided-hand record is currently vacuous, and
  will stop being vacuous the moment a second board is committed.**
  `A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED` reasons that a continuation bet folded to
  is recorded while one that is called is erased, so the surviving record is a record of the bets
  that worked. Method S says there is nothing to select from yet: no bet is made, so no hand is
  recorded with one. The entry is right about the mechanism and its subject does not exist at this
  coverage, which is worth knowing before someone treats an empty record as a clean one.

- **Whether the committed frequencies have settled is still unmeasured for every cell whose money
  decision is genuinely mixed.** Owned by
  `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`, whose text asks for
  one deep solve and treats that as the measurement. One was taken, and N1 measures that it landed
  on the only cell of the four with 0 of its classes mixed on bet-versus-check. The entry's
  condition is satisfied in letter and its question is open in substance for the other three cells.

- **A category table over these cells can invert the conclusion a combination-level table gives.**
  N3 is the concrete instance: range-weighted, no pair and top pair lead within 0.0005 of each
  other and the lead looks like noise; combination by combination, 48.6% of no-pair hands never lead
  and 19.3% lead more than half the time. Owned by
  `NO-FIGURE-SPLITS-THE-FLOP-BET-FREQUENCY-INTO-VALUE-AND-BLUFF`, which asks for exactly the split
  that resolves it, and this is the measurement showing the split is not cosmetic.

- **Nothing in the gate can go red on any finding in this note.** Every figure here is computed from
  committed files or from the repo's own simulator, and none of them is compared against anything
  that could fail. A composite that bets zero times in twenty thousand hands passes every command
  the gate runs. Owned by `NO-GATE-MEASURE-CAN-FAIL-ON-A-BAD-RANGE` for the general statement and
  `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` for why there is nothing to compare
  a frequency against. The stage-6 note records the same alignment over the cells; this is the same
  hole over the behaviour.

## The question the exec plan reserved, answered in plain words

Asked: is a bot that bets a flop and then refuses every turn better or worse at the table than one
that never bets?

As a training chart, the refusal is safe and is the right choice. The committed frequencies are
correct for an agent that can barrel, and a refusal voids the hand rather than playing on, so the
student is never shown a continuation the solver did not endorse. A bot that bet the flop and then
checked the turn down would teach a line no solution contains, which is worse.

As a bot at a table, it is worse than one that never bets, and by a measured amount rather than an
argued one: the same 20,000 deals give 4,543 showdowns on the old fallback and 4,543 voided hands
with zero bets on this one. That trade is deliberate and a refusal that names a gap is better than a
fold that hides one, so it is the right trade; it is just not the trade the phase describes.

And the question as posed does not reach the thing that is actually true, which is that the seam is
not at the turn. The turn is never reached. The bot refuses at hero's first flop action, because no
committed cell's successor is committed and because the artifact holds 40 of 22,100 boards. What
ships is a flop chart of four cells, one preflop line and three boards, and it should ship: the
cells are a correct solution to the game as configured, the dry board's play is real poker, and a
chart is a useful thing. What should not ship is the sentence calling it a bot that bets a flop and
then refuses every turn.
