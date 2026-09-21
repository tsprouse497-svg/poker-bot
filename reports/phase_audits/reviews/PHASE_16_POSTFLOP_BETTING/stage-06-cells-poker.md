# Phase 16, stage 6: independent domain review of the committed flop cells

Read-only. The reviewer wrote none of the work under review, holds the domain brief, and judges the
poker rather than the code's fidelity to the contract. `stage-06-build-mechanical.md` is the
mechanical pass and the open blockers there are not re-checked here.
`stage-06-build-poker.md` is the previous domain review, written when `data/artifacts/postflop/`
did not yet exist and the strategy had to be exercised against a synthetic sample; nothing in it is
re-filed here. What is new tonight is the real solved data, and this note is about that.

Under review: `data/artifacts/postflop/sample/` (four cells on three boards),
`data/artifacts/postflop/index.json`, `solve_config.json`, `deep_convergence_check.json`, and the
solved node objects under `/Users/taylorsprouse/poker-bot-solve-objects/postflop/`, at
`399b739` on `phase/16-postflop-that-can-bet`. Nothing was written except this file.

## Method, stated once

Every figure below was computed in this worktree tonight. Three methods are used and each figure
says which.

**Method A, range-weighted.** Expand all 1,326 two-card combinations, drop the ones the board
blocks, weight each by its class weight in `solve_config.json` for the seat that acts, map it to
the cell's class label with `solver_artifacts.postflop_isomorphism.canonical_hole_cards`, and
average the committed row. On the monotone cell this reproduces the artifact's own
`aggregate_frequencies` to four decimals - check 0.0012, bet 33% 0.8086, bet 75% 0.1903 - so the
weighting is on the artifact's own footing and not a second convention.

**Method B, reach-weighted.** The same, but weighted by the acting seat's `reach` in the solved
node object. At a node with no prior hero decision, A and B agree. At the facing-a-bet node they do
not, and B is the correct one, so the facing-a-bet figures are all B.

**Method C, derived opponent frequency.** At any harvested node the *opponent's* `reach` divided by
its preflop class weight is the probability the opponent took the action that leads to this node.
This is how the big blind's flop lead frequency on `9c8c7c` and the button's continuation-bet
frequency on `Kh7d2c` are recovered, since neither of those nodes is itself committed.

Hand categories come from `poker_core.hand_eval.evaluate_best` on the five cards, not from a
hand-typed list.

## Blocker

- **B1. The continuation-bet artefact this phase halted on four days ago is still in the committed
  artifact at very close to its old size, the cause is no longer the preflop chart, and nothing in
  the phase records either fact.** A human ruling is what closes this, not a re-solve.

The record says the phase stopped because a flop cell solved against a broken caller's range came
out at a 99.94% continuation bet. The chart was re-solved and the lane resumed. The committed cell
now says:

| `monotone-connected-cbet`, board `9c8c7c`, button acting after the big blind checks | check | bet 33% | bet 75% |
| --- | --- | --- | --- |
| committed, 280 iterations, 0.2774% of pot (method A) | 0.0012 | 0.8086 | 0.1903 |
| deep, 1,200 iterations, 0.0478% of pot (the artifact's own `deep_convergence_check.json`) | 0.0000 | 0.7584 | 0.2416 |

The button bets 99.88% of its range, and betting harder is what convergence buys: at the deeper
solve the check disappears entirely. Across the 152 committed classes **not one checks as often as
1% of the time**, and the largest check frequency in the file is 0.008, on `JcTd` (method A over
the committed rows). The earlier record's phrasing was "no combo checking more than 20 percent";
the equivalent figure here is 0.8 percent. On this measure the cell is further from a real strategy
than the one that stopped the phase, not closer.

**The preflop fix did land, and it is not the cause.** The backlog entry
`RE-SOLVE-THE-PREFLOP-CHART-WITH-A-REALISTIC-BLIND-THREE-BET` predicts that after the fix the big
blind's call branch holds 7.40 set combinations on this board against a possible 9. Recomputed from
`solve_config.json`: 99 at 0.4672, 88 at 0.9993 and 77 at 1.0, three combinations each with no
board blockers, is 7.399. The entry is right and the caller has its sets back.

**The caller is not even weak here.** Composition of each seat's range on `9c8c7c`, as a share of
its own weighted combinations (method A plus the evaluator):

| | flush | set | straight | straight flush |
| --- | --- | --- | --- | --- |
| button, in position | 6.29% | 2.02% | 4.04% | 0.45% |
| big blind, out of position | 8.67% | 2.51% | 1.02% | 0.34% |

The caller holds *more* flushes and *more* sets by share than the raiser. A range-wide bet into
that is not something the preflop input explains.

**What does explain it: the caller has already bet half of its range, and three quarters of its
best hands, before this node is reached.** Method C on the opponent's reach at this very node:

| big blind's holding on `9c8c7c` | weighted combos | share that leads out |
| --- | --- | --- |
| straight flush | 1.00 | 0.904 |
| set | 7.40 | 0.740 |
| flush | 25.57 | 0.739 |
| no pair | 168.58 | 0.524 |
| one pair | 89.27 | 0.454 |
| straight | 3.00 | 0.398 |
| **whole range** | **294.86** | **0.5268** |

The big blind leads 52.68% of its range on this flop. What reaches the button's decision is a range
in which flushes have fallen from 8.67% to 4.79% and sets from 2.51% to 1.38%. Against *that* the
button's 99.88% is close to coherent. The committed cell is the right answer to a question nobody
should be asking.

This is not the solver misbehaving and it is not a tree bug: the repo already knows the empty
`donk` list does not stop the out-of-position seat betting a flop, and says so in
`postflop_solve_driver.py` and in `A-SOLVER-CONFIG-FIELD-IS-READ-FROM-ITS-NAME-AND-NOT-FROM-THE-BUILDER`.
It is a modelling choice with a large consequence that nobody has measured, and it sits
underneath the one number the phase was halted on. What this blocker asks for is the ruling and the
record, not a re-solve: that the phase state its continuation-bet frequency with the measurement
beside it, that it state the 52.68% lead the frequency is conditioned on, and that a human decide
whether a flop-leading caller is the opponent this training artifact wants. Closing the phase with
the record implying the re-solve fixed the c-bet would be the false statement, and it is the one
the phase is currently set up to make.

## Non-blocker

**N1. The rainbow board's continuation bet is real poker, and this is the strongest positive
finding in the note.** There is no committed cell for the button's decision on `Kh7d2c`, so the
frequency has to be recovered by method C from the opponent's reach at `rainbow-dry-high-facing-a-bet`:

| button's holding on `Kh7d2c`, big blind having checked | reach before | reach after | bets 33% |
| --- | --- | --- | --- |
| bottom pair (a 2) | 6.00 | 5.72 | 0.954 |
| top pair (a king) | 75.00 | 69.44 | 0.926 |
| small pocket pair | 24.00 | 22.22 | 0.926 |
| middle pair (a 7) | 31.08 | 28.43 | 0.915 |
| pocket pair between 8 and Q | 30.00 | 27.32 | 0.911 |
| no pair | 260.00 | 229.94 | 0.884 |
| set | 9.00 | 7.79 | 0.865 |
| two pair | 4.00 | 3.42 | 0.854 |
| overpair | 6.00 | 5.01 | 0.834 |
| **whole range** | **445.08** | **399.29** | **0.8971** |

89.71% at the small size, so the check-back range is at most 10.29% and is smaller than that,
because some of the residual is the 75% bet this method cannot see. A range bet at a third of pot
on a dry king-high flop, with the overpairs and the sets betting least and going into the
check-back, is what a real six-max solution looks like. The answer to "does it bet a king" is yes,
92.6% of the time; the answer to "does it bet anything that is not a king" is also yes, 88.4% of
its no-pair hands. The complaint that could be made - that a deuce bets more often than a king and
a king more often than a set - spans 12 points across the whole range and is the ordinary
protect-the-checking-range shape, not a defect.

**N2. Flush draws are genuinely served a different strategy from no-draw hands, which is the thing
the isomorphism work existed to buy.** On `8c8d3c` (method B, reach-weighted): a hand holding only
the board's pair checks 0.791, and the same hand carrying a flush draw checks 0.383. A 40.8-point
gap is a real distinction, not a rounding artefact. On `9c8c7c` the gap is much smaller - no-pair
hands take the big size 0.207 and no-pair-with-a-club 0.247, four points - but a monotone board is
where that distinction is weakest anyway.

**N3. Facing a third-pot continuation bet on the driest board in the sample, the caller both
over-folds and check-raises far more than any reference play I know.** Method B, reach-weighted, at
`rainbow-dry-high-facing-a-bet`:

| big blind facing 1.815bb into 5.5bb | share of range | fold | call | raise to 4.54 |
| --- | --- | --- | --- | --- |
| ace high | 36.77% | 0.334 | 0.540 | 0.126 |
| no pair, no ace | 23.71% | 0.757 | 0.017 | 0.226 |
| top pair (a king) | 22.21% | 0.000 | 0.407 | **0.593** |
| pocket pair below a 7 | 7.32% | 0.000 | 1.000 | 0.000 |
| pocket pair below a king | 2.92% | 0.000 | 0.885 | 0.115 |
| middle pair (a 7) | 2.73% | 0.000 | 0.381 | 0.619 |
| bottom pair (a 2) | 1.79% | 0.000 | 0.860 | 0.140 |
| set | 1.34% | 0.000 | 0.072 | 0.928 |
| two pair | 1.19% | 0.000 | 0.027 | 0.973 |
| **whole range** | **100%** | **0.3022** | **0.4193** | **0.2784** |

Two figures. It defends 69.78% where the minimum defence against a third-pot bet is 75.19%
(`1 - 1.815/(5.5+1.815)`, and the same figure the phase's own decision 9 uses) - it over-folds by
5.4 points. And it raises 27.84% of its range, of which the largest single block is top pair
raising 59.3%. Minimum defence is a reference point rather than a law, since the bettor's range is
not all bluffs, so the over-fold is the softer of the two claims. The raise is the hard one: 27.84%
is roughly double the check-raise frequency I would expect on a dry king-high flop against a small
bet, and check-raising the majority of one's top pair on a board with no draw to protect against is
the part I would want a second opinion on. This is an intuition with a measured subject, not a
measured objection - the repo holds no external postflop reference to check it against, which is
what `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` is about.

**N4. On the paired board the caller leads its single unbeatable hand 94.7% of the time.** Method B
at `two-tone-paired-donk`, board `8c8d3c`, big blind first to act:

| holding | share of range | check | bet 33% | bet 75% |
| --- | --- | --- | --- | --- |
| quads (pocket eights) | 0.33% | 0.053 | 0.942 | 0.005 |
| full house (pocket threes) | 0.21% | 0.238 | 0.732 | 0.030 |
| trips (an eight) | 5.36% | 0.512 | 0.481 | 0.006 |
| one pair plus a flush draw | 10.19% | 0.383 | 0.610 | 0.008 |
| two pair | 14.52% | 0.590 | 0.406 | 0.004 |
| the board's pair only | 69.39% | 0.791 | 0.207 | 0.002 |
| **whole range** | **100%** | **0.7016** | **0.2951** | **0.0033** |

The caller leads 29.84% of its range, and the lead frequency rises with hand strength all the way
to the top. Quads is the one hand in poker that cannot be outdrawn and has no reason to narrow the
opponent's range; betting it 94.7% into the preflop raiser is the single line in this artifact I
would most confidently call wrong, and I cannot produce a reference number for it, so it is an
intuition with a measurement attached rather than a measured defect.

**N5. The 75% size is very nearly dead on both out-of-position cells, so the two-size menu is one
size there.** Method A: 0.0356 of range on `Kh7d2c` and 0.0033 on `8c8d3c`. On the second board
the big size is taken by 0.33% of the range, which is less than one weighted combination in three
hundred. Whatever the sizing question is answered by, it is not answered by these two cells.

**N6. "No donk bet" is not what the artifact does, and the repo already knows.** The empty `donk`
list in `solve_config.json` removes the out-of-position probe on a later street, not the flop lead;
`postflop_solve_driver.py` says so in its own docstring and
`A-SOLVER-CONFIG-FIELD-IS-READ-FROM-ITS-NAME-AND-NOT-FROM-THE-BUILDER` records the earlier misreading.
Recorded here only because a reader coming to these cells from the config will get the opposite
impression, and three of the four committed cells are lead nodes.

## Alignment

- **The gate cannot fail on any of the above.** Every figure in this note is computable from
  committed files and none of them is compared to anything. A cell that bets 100% of range, leads
  its quads and check-raises its top pair passes every check the gate runs. Owned jointly by
  `NO-GATE-MEASURE-CAN-FAIL-ON-A-BAD-RANGE`, which is the general statement, and
  `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL`, which is why there is nothing to
  compare against. This note is the concrete postflop instance of both.

- **The only continuation-bet cell the phase commits is on the texture that generalises worst.**
  Of the four cells, three are the caller's and one is the raiser's, and that one is the monotone
  board. The board the brief expected a continuation bet on, `Kh7d2c`, has no such cell, and its
  frequency had to be recovered from an opponent's reach field. Owned by
  `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` and
  `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`.

- **The size mix carries no hand-strength information and should not be read as sizing advice.**
  Over the monotone cell's 152 classes the Spearman rank correlation between hand strength, ranked
  by `evaluate_best`, and the 75% frequency is **0.0022**. Restricted to the 30 made flushes it is
  0.4162, but inside that the ace-king flush takes the big size 1.4% of the time and the ace-queen
  flush, one rank weaker, takes it 31.6%. Set against the artifact's own deep check - aggregate
  33% falling 0.8086 to 0.7584 while the check moves 0.0012 to 0.0000, and individual mixed classes
  moving up to 0.467 - the "bet or check" decision is settled at the committed accuracy and the
  size split is not. Owned by `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`
  for the settling, and by `ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE` and
  `ONE-FLOP-RAISE-SIZE-AND-NO-SIZE-BETWEEN-33-AND-75` for the menu that produces it.

- **Nothing splits any of these frequencies into value and bluff, which is the split that would
  have made the monotone cell's 99.88% legible at a glance.** Owned by
  `NO-FIGURE-SPLITS-THE-FLOP-BET-FREQUENCY-INTO-VALUE-AND-BLUFF`.

- **The frequencies assume a turn the bot will not play, and that is sharper on the board where the
  caller leads half its range.** Owned by
  `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE`.

- **The caller's preflop range is still tighter than a real one and that is a standing, known
  limit.** The call branch is 380 of 1,326 combinations, 28.66%, against the roughly 40 to 65
  percent rake-free defence band the backlog names; the entry
  `RE-SOLVE-THE-PREFLOP-CHART-WITH-A-REALISTIC-BLIND-THREE-BET` already records that total defence
  moved only 36.65 to 37.33 percent and calls the remaining over-fold out by name. Recorded here
  because it is the obvious first suspect for B1 and it is **not** the cause: the caller's range on
  `9c8c7c` holds more flushes and more sets by share than the raiser's.

## What a student would be taught wrong

Asked directly by the brief, and answered from the numbers above rather than separately measured.

Drilling these three flops against this artifact, a person would come away with three habits.
First, that the preflop raiser bets every flop - on the one continuation-bet cell the artifact
holds, checking back is an action that effectively does not exist, and the student would never once
be shown a check-back. Second, that leading into the preflop raiser is normal and that the stronger
the hand the more it leads, since on `8c8d3c` they would lead quads nine times in ten. Third, that
top pair on a dry board is a check-raising hand, at 59.3%.

All three are unlearnable-at-a-cost habits against real opponents, and the first is the one the
phase is closest to shipping as its headline. The rainbow continuation bet, by contrast, would
teach them something true.
