# Phase 05 independent review

Loop stage 8. Read-only reviewers, no write access to the tree.

- Poker domain review: complete. One blocker, four non-blockers.
- Mechanical review: complete. Three blockers, all fixed and pinned with tests.

## BLOCKER: the collapse rule over-folds, and by a measurable amount

`src/poker_training_bot/strategy/preflop_chart.py` takes the highest-weight action.
`fold` is one bucket while continuing is split across `call` and `raise`, so a
solver split of fold 0.42 / call 0.30 / raise 0.28 collapses to a pure fold even
though the equilibrium continues 58% of the time.

Enumerated over every spot and hand class in the committed artifact: **16 pairs, 76
combinations, where the chart's fold weight is below 0.50 and the bot folds anyway.
Zero in the reverse direction.** The bias is strictly one-way.

| spot | hand | chart | bot |
|---|---|---|---|
| `t6/d100/BTN/HJ:raise` | 77 | fold .417 / call .301 / raise .281 | fold |
| `t6/d100/LJ/LJ:raise,BB:raise` | JJ | fold .4946 / call .493 / raise .0124 | fold |
| `t6/d100/BTN/CO:raise` | JTs | fold .497 / call .302 / raise .201 | fold |
| `t6/d100/SB/CO:raise` | 77 | fold .407 / call .396 / raise .198 | fold |

The aggregate is worse than those 76 combinations, because the same bias operates
wherever fold is already the plurality. Measured over the range the bot actually
opens:

- LJ opens and faces a CO three-bet to 8bb: bot folds **72.8%**, chart folds 59.8%.
- LJ opens and faces a BTN three-bet: bot folds **73.7%**, chart folds 58.6%.

An 8bb three-bet over a 2.5x open risks 8 to win 4, so it auto-profits as a pure
bluff above 66.7% folds. The solver holds LJ at 59.8%, deliberately below that line.
The bot sits at 72.8%, which hands any three-bettor a free profitable bluff with any
two cards. That is a first-order exploit, not a rounding artifact.

Same cause, same direction, elsewhere: HJ's cold-call versus an LJ open goes from
1.41% to **0.00%**, so that spot becomes pure three-bet-or-fold; BB's three-bet
frequency versus CO drops 8.86% to 6.64%, stripping out the bluffs and leaving a
linear value range; SB's opening frequency rises 34.41% to 38.31% while its limp
falls 13.73% to 10.11%.

**This is not a code defect.** Judgment call 3 was ruled `highest`, and the accepted
cost was written as "the bot is unbalanced and exploitable, but never illegal". The
finding is that the cost was described qualitatively and is quantitatively much
larger than that phrasing suggests: it folds 77 on the button to a 21.7% open, and
it over-folds to three-bets by 13 to 15 points across the board. Nobody measured it
before ruling on it, including me when I wrote the decision list.

The remedy is a ruling, not a patch. Options are the ones already on the decision
list: keep `highest` with the cost now measured and recorded, or switch to
`random-per-hand-by-weight`, which reproduces the chart's frequencies exactly and
removes the bias. Changing it later invalidates every Phase 07 baseline, so it is
cheapest to settle now.

Also required either way: `reports/active/latest_preflop_strategy_report.txt` shows
only chart frequencies, with no column for what the bot actually does. A reviewer
reading that report cannot see any of the above.

## NON-BLOCKER findings

1. **The all-in branch is a real strategy, and collapsing it hides its size.**
   Contract-sanctioned, but worth recording per spot. In `UTG_vs_BB_3bet`, 25% of
   what the bot four-bets to 28.5bb should have been a 100bb shove (`AKo` 0.53,
   `KK` 0.36, `AKs` 0.06). In `SB_vs_BB_3bet` the shove range includes `KJs` at
   0.78; the bot instead four-bets it to 22bb, a 2.1x raise it must fold to a
   five-bet, and there is no facing-a-five-bet spot in v1, so it refuses there.

2. **Four zero cells in the opening grids look like holes.** `87s` at exactly 0% in
   a 27.9% CO opening range that contains `K2s` at 44% and `Q6s` at 35%, with `98s`
   at 75% and `76s` at 12% on either side. Same shape for CO `Q7s`, LJ `98s`, HJ
   `98s`. Countervailing evidence: they are explicit zeros in the source, combo
   totals reconcile to the site everywhere, and there are zero monotonicity
   violations across all 169 hands from LJ to BTN. Exposure is 16 combinations.
   Cheapest resolution is to open the CO grid on GTO Wizard and read four cells.

3. **The external oracle is not external.** The expectations file, the contract, and
   the report all call it the only column this repo did not produce. It is computed
   by `build_expectations()` from the same committed source in the same converter
   run as the ranges. It has real power, because it reads the source's aggregate
   combo counts while the ranges read the strategy grid, and substituting a wrong
   range breaks it by 8 to 15 combos. But it cannot catch a wrong source, and it
   covers only 10 of 36 spots. The prose overclaims in three places.

4. **Committed sizes assume the tree's exact bet sizes.** A spot key carries no
   size, so the 8bb three-bet fires against a 4bb open as a 2x raise using a range
   solved for 3.2x. Worse in the four-bet spots. `RAISE-SIZE-IN-SPOT-KEY` names the
   range consequence but not the sizing one.

## Checks that passed, with evidence

- **Three-bet attribution is correct.** For all 15 spots, weight times the opener's
  own RFI raise weight times combinations reproduces the source's displayed combo
  counts to 0.00 for every action. Substituting the three-bettor's range instead
  breaks it, so the check has power.
- **The out-of-range drop discards nothing.** No hand appears in a vs-three-bet
  strategy while absent from hero's opening range, and none is dropped that hero
  could hold.
- **Position mapping is correct.** Hero and the acting seats re-derived from every
  `action_path` independently of the converter: 36 of 36 consistent, no seat swap,
  no off-by-one.
- **All 36 sizings correctly attributed**, and four-bet sizes are internally
  consistent with the three-bet they face (21.5 versus every 8bb, 23.0 versus every
  11bb, 28.5 versus every 13.5bb).
- **All 11 expectation figures match the source exactly.** Open frequency excludes
  the SB limp, defence is call plus three-bet, nothing double-counted.
- **Rake is not overclaimed** anywhere in the repo.
- **Range shapes are credible**: zero monotonicity violations LJ to BTN, BB's
  three-bet bluffs are the low suited kings plus offsuit wheel aces (the
  characteristic blocker construction), SB flats 2.3% versus BTN while BB flats
  26.5%, suited wheel aces are 100% in every opening range.
- **The artifact reproduces byte for byte** from its committed source.

## Mechanical review

Three blockers, each reproduced by the reviewer against the running code, each now
fixed and covered by a test that fails without the fix.

### BLOCKER: stack depth was read from the deepest seat, not from hero

`_table_depth_bb` took `max(stack)` and divided by the big blind. It never looked at
hero. A hero with 12bb opened a 100bb range at 2.5x, and the decision audit accepted
it, as long as one untouched seat sat behind. Judgment call 5 was ruled `exact-only`
and the contract forbids any tolerance band; this was an unbounded one on every seat
except the deepest. The existing test only passed because it set all six stacks to
40bb, the single configuration `max()` gets right.

Fixed by measuring hero's own starting stack, which is the one depth in the query
that can be derived rather than guessed: what hero owes plus what hero has left is
what hero started with. A seat holding more than that refuses under its own code,
because "your table is not flat" and "your depth is ragged" are different problems.

### BLOCKER: the blind-structure guard stopped looking after any action

The straddle test only ran while nothing had raised, and the ante test only ran
while the history was empty. Since folds are recorded, an anted pot refused for the
first seat to act and was chart-backed for the other five. A straddled pot was
accepted from the moment anyone raised, which in a straddled game is always.

Replaced with an arithmetic bound that works at every seat: the largest pot the
blinds and the recorded voluntary actions could possibly have built is the two
blinds plus one full bet each, and anything larger is money the format cannot name.

Residual gap, recorded as `PER-SEAT-CONTRIBUTIONS-IN-QUERY`: the bound is generous,
so a straddled pot with several callers can still slip through. Exact detection
needs each seat's committed chips on the query, which is the same shape of fix as
adding the action history was, and it would also close
`ASYMMETRIC-EFFECTIVE-STACKS`.

### BLOCKER: the seed was untested, and the forbidden seed passed the whole suite

The contract names the failure by hand: a seed of spot and hand class alone would
freeze every mixed cell to one action forever. The reviewer substituted exactly that
and all 68 tests passed, because every frequency assertion routed through
`decide_spot`, which builds its own seed and never touches `_seed`. Fold-to-three-bet
drifted to 65.4% against a chart figure of 59.8% with nothing failing.

Fixed by testing the seed directly and by measuring frequencies through `decide`.

### Non-blockers now covered

Tests were added for the refusal paths the reviewer mutated freely: an action the
chart names that is not legal here, a raise with no committed size, a committed size
below the minimum raise, a ragged depth, and an uneven table. All five refusal codes
previously appeared in no test at all.

Remaining non-blockers recorded but not fixed: `hero_range` in the converter reads
only the first raise label where `build_weights` sums all of them (no effect on the
committed export, since no hand is opened only by shoving); the converter has no
spot-key collision guard of its own and relies on import validation; `action_weights`
key order follows the source's JSON order rather than being sorted; two tests spawn a
bare `python` rather than `sys.executable`; and
`test_no_two_covered_spots_share_a_hand_class_ordering` is tautological.
