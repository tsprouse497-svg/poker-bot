# Phase 16, stage 4: independent domain review of the tests

Read-only. Reviewer wrote none of the work under review, and is the domain reviewer: this note
judges the poker the tests describe, not their fidelity to the contract.
`stage-04-tests-mechanical.md` is the mechanical pass and is not duplicated here. Where it already
found something I also saw (the orbit-size docstring at its N9, the flush-draw escape hatch at its
N7), I say so and do not re-file it.

Diff under review: `git diff 58ed4636ed6f744c4938319614d207b2334dd988 HEAD` in
`poker-bot-worktrees/phase-16`, branch `phase/16-postflop-that-can-bet`.

Every number below is recomputed in this worktree. The scripts are throwaway and the method is
stated beside each figure so it can be re-run.

## Blocker

**B1. The pot-odds negative control asserts a false thing about poker, and cannot pass.**
`tests/test_postflop_betting.py:537-553` picks `3c2d` as the hand whose equity does not beat the
price, and asserts `equity(("3c","2d"), ("Kc","7d","2h","9s","4c")) < 550/(1650+550)` as its own
precondition. `3c2d` pairs the board's deuce. Counted over all 990 villain holdings with the repo's
own evaluator (`scripts/generate_postflop_fallback_report.py::holding_counts`, which is the function
decision 5 moves into `src`): villain beats hero 548, ties 22, hero wins 420, so hero equity is
`(420 + 11) / 990 = 43.54%` against a price of 25.0%. The precondition is false by 18.5 points, so
the test is red against a correct implementation and the poker claim it freezes is wrong.

This is not a one-hand slip, and the repair has to be picked on a number rather than on intuition.
Over the same board and price, 272 of the 1,081 hero holdings fall below 25.0% and the median
holding has 48.38% equity, so at quarter-pot odds decision 5's rule calls with about three quarters
of the deck. That is the over-calling the contract already concedes, now with a figure. A hand that
really fails here is `3c5c` at 0.45%, the minimum over the board.

**B2. Two frozen fixtures build a `StrategyQuery` the repo's own validator rejects, so the tests
that use them can never run against any implementation.** `StrategyQuery.__post_init__`
(`src/poker_training_bot/strategy/contract.py:246`) requires `pot` to equal the sum of every seat's
`committed_total`. Constructed directly, outside pytest:

- [resolved] `tests/test_postflop_betting.py:371-382`, the 3.5bb open that is meant to prove the 20% band
  refuses on the high side: `pot=750` against `350 + 350 = 700`. Raises
  `ValueError: pot 750 is not the 700 the seats put in`. This is the phase's only test that an
  out-of-band price refuses rather than being answered from the nearest cell.
- [resolved] `tests/test_postflop_betting.py:471-484`, the river fixture behind every test in
  `TestThePotOddsRiverCall`: `pot=1650` against `800 + 300 = 1100`. Same refusal. The whole
  pot-odds river rule is untested as a result.

Both are masked today because the module fixtures error first on modules stage 6 has not written.
They surface the moment the implementation lands, and after stage 5 nobody may repair them.

**B3. Nothing requires the strategy to play the committed mixture, and the repo already has the
precedent it is not being held to.** `PreflopChartStrategy.collapse`
(`src/poker_training_bot/strategy/preflop_chart.py:97-121`) draws one action in proportion to its
weights and says in terms "Not the highest weight." No test in this diff, and no sentence in the
contract or the decision list, requires `PostflopBettingStrategy` to do the same. An implementation
that takes the highest-weight action passes every test in the six files: it bets, it raises, its
amounts are legal, its actions are legal, the turn and river refuse.

What that implementation is, in poker: a solver mixes exactly where it has driven a hand to
indifference, so purifying the mixture turns every indifferent class into a pure action at the
frequency an opponent can read off in one orbit. A class solved to bet 0.51 and check 0.49 becomes
bet 1.00. The artifact stops being a strategy and becomes a very expensive exploitable one, and the
bet frequency the report prints is then the bot's, not the artifact's, with nothing saying which.

The same gap admits the cruder degenerates. A strategy that bets 33% with 100% of its range on
every covered flop and raises 2.5x with 100% of its range facing a menu bet passes all six files.
So does its mirror, checking everything except one spot that bets and one that raises, because the
two tests at `tests/test_postflop_betting.py:158-180` only require at least one committed spot to
produce each. So does a strategy that ignores `class_weights` entirely, because nothing ties a
returned action back to a non-zero weight in the cell it came from.

Three cheap frozen tests close all of it, none of them needing an oracle:
1. Over one committed cell and N hand ids, the realised frequency of each action for one hand class
   is within a stated tolerance of that class's committed weight.
2. The action returned for a hand carries non-zero weight in the committed cell for that hand's
   class, checked over every class in one cell.
3. On one committed spot, at least two distinct actions appear across the range, and the bet
   frequency is strictly between 0 and 1.

**B4. Nothing pins that a three-handed flop refuses.** The multiway limit is the one coverage gap
this phase calls structural rather than fundable, and the only thing in the diff that touches it is
`tests/test_postflop_betting_report.py:158-162`, which requires the report to contain the words
"multiway" and "structural". No test asks the strategy what it does when three seats reach the
flop.

The reason that matters here rather than in general: under the committed line set a three-way pot
misses only because its pot is arithmetically different. `t6/d100/SB/BTN:raise@2.5` is the same
preflop key whether the big blind folds (pot 6.0bb heads-up) or calls (pot 7.5bb, three-handed),
and the key separates them through the `pot` segment alone, because the preflop key ends at hero's
own decision and the players who act after hero are not in it. There is no player-count segment and
no pot-type segment. At one open size and flat 100bb that arithmetic happens to hold; a second
committed open price, a straddle or a non-flat table breaks it, and a two-range cell would then
answer a three-handed flop with a heads-up strategy and no refusal. A test that a three-handed flop
refuses is the thing that makes the separation a requirement instead of a coincidence.

[resolved] 2026-09-24 by MAINT-38: every bullet above that lacked a marker was audited by an independent lane and marked where the fix or ruling is shown, finding by finding, in `reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`.

## Non-blocker

**N1. No test pins how a chip bet becomes a menu size, and the arithmetic does not come out even.**
The ruled flop menu is `33 75` as a percent of pot. At 50/100 blinds the `@2.5` single-raised pot is
550 chips, and 33% of 550 is 181.5, which is not an integer number of chips, so no real table can
produce the menu size exactly. The fixtures use two different readings without saying so:
`facing_a_bet` (`tests/test_postflop_betting.py:105-117`) bets 180, which is 32.73%, and the
off-menu test (`:405-415`) bets 275, which is 50.0%, and requires a refusal. Nothing between them is
pinned. If stage 6 requires an exact match, every facing-a-bet node refuses at a real table and the
whole raise branch of the artifact is dead; if it rounds, the tolerance is unstated and could as
easily swallow a 40% bet as a 32.7% one. `NOTHING-MEASURES-POSTFLOP-ACTION-COVERAGE-AGAINST-REAL-BET-SIZES`
owns the coverage half of this and not the rounding rule.

**N2. The three single-raised fixtures use three different conventions for the folded small
blind, and one of them pays the big blind the wrong price.** In
`tests/test_postflop_betting.py::query` the pot is 550 and seat 1 carries `committed_total=300`
against a stack of 9750, which says it put in 250. So the fixture's big blind is recorded as having
paid 3.0bb against a 2.5bb open, and it passes the pot check only because the 50 chips of dead small
blind were parked on it. The 3.5bb fixture instead puts the dead blind in the pot alone (750 against
700, which is B2), and the 2.0bb min-open fixture (`:388-397`) has no dead blind at all: pot 400 for
`200 + 200`, where a six-max hand with a 2.0bb open and one caller makes 4.5bb by decision 10's own
`pot = 2 x open + 0.5`. Three spots labelled as the same line are three different pots.

**N3. The default of `pot_odds_river_call` is not pinned, and the rule cannot fire in play
anyway.** `strategy` is built with a bare `from_repo()`; the flag is exercised only through explicit
`True` and `False`. Decision 5 says the default ships and the contract says the river refuses, and
nothing here says which `from_repo()` takes. Separately, the turn always refuses and a refusal voids
the hand, so no hand in this repo reaches a river where the rule could fire. The report must print a
"pot-odds fired" figure that is therefore 0 by construction, and unlike the refusal codes there is
no requirement that a vacuous one be labelled.

**N4. The at-the-table flush-draw test can be satisfied without playing the two hands
differently** (`tests/test_postflop_betting.py:444-455`): the assertion is that the action and
amount differ *or* the detail string differs, and a detail carrying the hand class differs for free.
The map-level test in `tests/test_postflop_key.py` is the real one. Already filed by the mechanical
pass as its N7; recorded here because the poker statement the test claims to make is not made.

**N5. Every positive answer except the flush-draw pair is checked against spots the implementation
chose for itself.** `committed_spot_queries()` is published by the module under test, so "it bets",
"it raises", "the amounts are legal" and "the actions are legal" are all evaluated on a list stage 6
writes. A strategy that answers only its own three spots and refuses every independently built query
passes.

**N6. The range floor was checked and is small.** If stage 6 puts all 169 classes in each range,
flooring lifts every trash class to 0.01. Against an opening range of about 45%, which is 597 of the
1,326 combos, the floored mass is `13.26 - 5.97 = 7.29` combos, 1.22% of the range. Not a defect.
Recorded so the question shows as asked rather than skipped.

**N7. The orbit-size docstring misattributes sizes to textures** (`tests/test_postflop_key.py:46`,
"Rainbow boards have a 24-element orbit, two-tone 12, monotone 4"). Already filed by the mechanical
pass as its N9. The poker cost is worth adding, because the contract tells stage 6 to scale every
rainbow cost figure "from an exact orbit factor": brute-forced over all 22,100 boards under all 24
suit permutations, rainbow splits into 286 classes at orbit 24, 156 paired at orbit 12 and 13 trips
at orbit 4, so 455 rainbow classes cover 8,788 boards and average 19.314 boards per class. Scaling
455 classes at 24 gives 10,920 boards and overstates rainbow by 24.3%. The `ORBIT_HISTOGRAM`
constant itself is correct.

## Alignment

**A1. The committed sample misses the modal flop family and every ace-high board.**
`THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY` (**proposed**). Counted over all 22,100
three-card boards with the tests' own `texture` and `rank_structure` functions: the three cells the
sample occupies hold 34.28% of flops (rainbow unpaired-spread 24.76%, two-tone paired 8.47%,
monotone connected 1.05%). The largest cell in the deck, two-tone unpaired-spread at 37.14% of all
flops, has no representative at all, and the rarest non-trips cell gets a third of the sample. No
board in the sample contains an ace, and 21.74% of flops do, which is the family where the preflop
raiser's range advantage and c-bet frequency are largest and therefore where a wrong committed
strategy is most visible.

The sample is not a random draw and the tests say so: a frequency-weighted three would be two
two-tones, and the spread is deliberate. The drift is that the 3x3 diagonal is what forces the
two-tone slot to be paired, and the diagonal is the contract's (decision 6 item 4 names two boards
and freezes the splits), so stage 4 had one cell to choose in and chose inside it correctly. Any
test that reads as a claim about flop play reads it off 40 of 22,100 boards.

**A2. The seam is worse than never betting, and no figure in the phase will show by how much.**
`A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` (existing) owns the general
statement. Asked plainly, my answer is worse, and here is the arithmetic. A 33% c-bet in the `@2.5`
single-raised pot risks 1.815bb to win 5.5bb, so as a pure bluff it needs
`1.815 / (5.5 + 1.815) = 24.81%` immediate folds to break even. The minimum defence frequency
against a 33% bet is 75.2% (decision 9's own figure, and `1 - 0.2481 = 0.7519` recomputes it), so
against an opponent defending correctly the bluffing half of the c-bet is break-even before the
barrel and strictly losing against anyone who defends more. Everything above break-even is the turn
bet that never comes. The value half is worse off still: 33% is the first leg of a three-street
plan, and taken alone it collects 1.815bb where the plan collects up to 97.5bb. Never betting loses
the same pots and does not pay 1.8bb a time for the privilege.

Two things soften it and neither rescues it. The simulator voids the hand at a refusal, so the bot
never plays out the abandoned turn, and the contract already bars the winrate that would expose it.

What is not owned by an existing entry, and is my finding:
`NO-FIGURE-SPLITS-THE-FLOP-BET-FREQUENCY-INTO-VALUE-AND-BLUFF` (**proposed**). The report prints a
bet frequency and a raise frequency and nothing splits either into the value hands, whose loss is
foregone streets, and the bluffs, whose loss is chips. Those are the two halves of the seam and they
have opposite signs. As specified, the one number that would tell a reader the size of the donation
is not computed.

**A3. The flop menu has one raise size and nothing between 33% and 75%.**
`ONE-FLOP-RAISE-SIZE-AND-NO-SIZE-BETWEEN-33-AND-75` (**proposed**);
`NO-MENU-IN-THE-RECORD-OFFERS-AN-OVERBET` (existing) owns the overbet half.

What the committed artifact can express on a flop: check, bet 33% of pot, bet 75% of pot, raise to
2.5x the facing bet, and a stack-off reached by the `allin_threshold` snap, which decision 11
measured as never firing on the flop under either menu. What it cannot express, in ordinary poker
terms: any stab below 33%, half pot, two thirds, pot, and every flop overbet. Facing a 33% bet the
only raise available is to 0.825 of the original pot, which is a 62% pot-sized raise; facing 75% it
is a 107% pot-sized raise. There is no small check-raise, no large one, no jam, and at
`max_raises: 2` no second raise.

The size of the gap at the top, recomputed rather than quoted: to get 97.5bb in over three streets
from a 5.5bb pot the final pot is `5.5 + 2 x 97.5 = 200.5`, the per-street multiplier is
`(200.5 / 5.5) ^ (1/3) = 3.316`, so the geometric size is `(3.316 - 1) / 2 = 115.8%` of pot. The
largest flop bet the menu offers is 75%, which is 64.8% of that. A value hand in the ordinary pot
cannot start the line it wants to start. Taylor ruled that acceptable for its own reason and this is
not a re-ruling; it is the statement of what a later phase buys by adding a size.
