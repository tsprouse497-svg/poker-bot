# Phase 14 stage 4: confirmation review of decisions 54 and 55, the poker

Read-only confirmation review on `phase/14-chart-cutover` at `8006516`, written 2026-09-03 by a reviewer
who wrote none of this work and has not seen the mechanical confirmation reviewer's notes. The remit is
the poker consequences of the two rulings that landed after the stage's poker review was already written:
decision 54 (the rank arm is scored over every spot in its partition) and decision 55 (the fourth relation
reads the merged raise weight, count 27 to 41).

Every figure below was re-derived from
`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz` by a walk written for this pass in a
scratch directory outside the repo, reaching the selection rule through `test_chart_derivation.selected`
so the set under review is the set the stage selects. It reproduces 249 nodes split 5 / 25 / 219.
`check_gate_bite.py` was not run and nothing in the tree was modified.

Confirmed reproducing before anything below was judged: 181 / 433 and all ten partition rows including the
two skipped columns, 19,774 and 20,279; 149 / 260 and 32 / 33 and 42 / 69 on `raises faced 2`; 41 and 25 on
the merged raise weight against 43 and 28 on the raw row; 11 and 9 over the twenty merged spots with the
same three vanishing and the same one appearing; 44 spots rounding to zero arrival in parts per billion and
2 exactly zero; the big blind's five defence, flat and reference rows and the 2.81-point flat spread.

## Blocker

**`[resolved]` 1. The big blind's accepted defect was renamed to the flat and kept the level's price tag. A
human signing the packet is shown up to 13.04 bb per 100 as the cost of a 2.81-point wobble.**

**Resolved 2026-09-03 by the F1 fix lane, and the finding is accepted in full.** The rename was a
coordinator error, not a lane's. The contract bullet is reverted to decision 34's ruled language - the big
blind over-folds, the flat's near-invariance is the fingerprint decision 34 already called it - and the EV
band travels with the over-folding it prices. The wider-than-the-raked-reference measurement is kept, since
it reproduces, but the contract and the frozen tests now require every printed comparison to name the
reference it is read against, and the report must cite `COMMITTED-SPOTS-NEVER-FLAT-A-RAISE` beside
`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT` so the one citation no longer leads away from the level. The
missing measurement this note identifies - that no rake-free reference exists to grade the level against -
is filed as `NOTHING-READS-THE-DEFENCE-LEVEL-AGAINST-A-RAKE-FREE-REFERENCE` rather than fixed here.
`tests/test_chart_cutover_evidence.py:645` already carried the correct name and was left alone; the other
two files were moved onto it.

`tests/test_derived_chart_report_ranges.py:322` now freezes the sentence "**The defect is the flat, not the
level.**" Nine lines later the same docstring freezes the cost, and `test_derived_chart_report.py:124`
freezes `EV_BAND = {0.65: (0.10, 0.70), 0.85: (8.76, 13.04)}`. That band is not the flat's cost. Decision
34 states in its own words what it priced: "at R = 0.65 the **over-folding** costs 0.10 to 0.70 bb per 100
occurrences of the spot, and at R = 0.85 it costs 8.76 to 13.04". It is the level's cost, and decision 34
is unamended at HEAD, still reading "Fifteen to twenty points tight against every opener" and "rake-free
solves are roughly 40 through 65".

The band's own shape says which defect it prices. It rises from 0.10-0.70 to 8.76-13.04 as realization goes
from 0.65 to 0.85, a floor near zero and a 19-to-125-fold climb. That is the signature of a one-sided
fold-too-much error: fold too much and you lose nothing if you cannot realize equity, and a lot if you can.
A flat that is invariant to the opener is a two-sided error - too wide against the lojack, too narrow
against the button and small blind - and a two-sided error does not collapse to 0.10 bb at low realization,
it gets worse there, because the half that is too wide is exactly the half low realization punishes. The
band cannot be pricing what the sentence above it now names.

The size of the mis-attribution, at the table. The five big-blind facing-an-open spots carry 70.12 percent
of hands dealt between them (13.053, 12.804, 13.460, 15.496, 15.307), the most-arrived family in the tree.
Converted, the published band is 0.07 to 0.49 bb per 100 hands at R = 0.65 and **6.14 to 9.14 bb per 100
hands at R = 0.85**. Six to nine big blinds per hundred hands is a winrate, not a rounding item, and it is
now printed under a heading that says the defect being accepted is a flat that moves 2.81 points instead of
more.

Why the rename does not carry the level with it. The evidence for the rename is that the chart defends
wider than `expectations/six_max_nl25_100bb.json` at four of five openers, which I reproduce exactly (SB
48.39 vs 42.88, CO 32.78 vs 31.48, HJ 28.88 vs 26.20, LJ 25.70 vs 22.63, BTN 36.65 vs 39.43). But the same
test asserts, four paragraphs above, that the reference is a **raked** game and that "a rake-free solve
should defend wider than a raked reference, so a chart reading wider is expected rather than
contradictory". By that test's own words, beating the raked reference is not evidence the level is right;
it is the minimum a rake-free solve must do. The chart sits between the raked reference and any rake-free
expectation, and the repo's own uncited rake-free figure of 40 to 65 puts it 14 to 21 points tight at all
five openers. `backlog.yml` is honest about this - the level entry is still open, still names the
big blind's over-folding, and its own extension says the name is settled only by
`REFERENCE-RANGES-HAVE-NO-CITED-SOURCE`. The frozen test is not honest about it: it cites
`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT` and nothing else, so a reader following the packet's one
citation never reaches the level entry or its 14-to-21-point figure.

The frozen tests also now disagree with each other on the name.
`tests/test_chart_cutover_evidence.py:645` still reads "the big blind's over-folding being decision 34's
accepted defect", and `tests/test_derived_chart_report.py:131` reads "'the big blind over-folds' is not
what this phase measured". Both freeze at stage 5.

This is a blocker rather than a non-blocker because stage 5 freezes both files and the price of an accepted
defect then travels to the packet attached to the wrong defect, where the human who signs it cannot see the
substitution. It needs no ruled constant moved and no measurement retaken: the band has to say which
quantity it prices, and the section has to cite the level entry beside the flat entry, or decision 34's
band has to be withdrawn as no longer describing an accepted defect.

**On the new name itself, separately from the price.** "Near-invariance of the flat" is an accurate
description of what I measured and a weak defect. The flat is 19.63 / 20.98 / 22.44 / 21.09 / 20.30 against
openers whose ranges span 18.74 to 54.30, so it is not merely flat, it is non-monotone: it peaks against
the cutoff and is smallest against the two widest openers. That shape is what you get when the three-bet
absorbs the whole response - the three-bet moves 6.07 to 28.09, a 22.02-point spread, and total defence
moves 22.69 against the reference's own 20.25. A flat whose width barely moves is defensible poker on its
own: the price is 2.5 at all five spots, hero closes the action at all five, and pot odds are the first
thing a flat's width answers. What is not defensible is that the flat ignores the one structural change in
the family - hero is out of position against the four non-blind openers and **in position** against the
small blind, and the flat moves 0.67 points across that flip (19.63 to 20.30) while realization changes
completely. I am not asking for the name to move back. I am saying the thing now named the defect is the
smaller of the two and carries the larger one's price.

## Non-blocker

**1. At the twenty merged spots the fourth relation is not a second reading of anything. It is relation one,
to fourteen decimal places, and nine of the published 41 are duplicates of the published 114.**

Decision 55 is right that the merged weight is what the bot plays, and the three inversions it removes are
real removals: `HJ/LJ:raise@2.5` `JJ` 94.66 against `TT` 99.76, `CO/HJ:raise@2.5` `JJ` 88.34 against `TT`
100.00, `BTN/HJ:raise@2.5` `88` 60.84 against `77` 74.54, all three reading 100.00 against 100.00 after the
merge. Those are three inversions the bot never commits and removing them is a straight gain.

The other half of the argument does not survive measurement. At all twenty merged spots the only action
kinds present are fold, call and raise, so the merged raise weight equals play-not-fold exactly: I checked
every cell at all twenty and found **0 cells differing, maximum difference 1.4e-14**. Relation four is
therefore relation one restricted to those spots, by definition rather than by coincidence. Of the 41, **9
sit at merged spots and all 9 are visible to play-not-fold**, which means all 9 are already among the 114
pair-ladder inversions. The case the record names as the merge's gain - `CO/HJ:raise@2.5` publishing `66`
at 66.23 against `77` at 49.21 - is one of those 9. It was invisible to relation four before the merge and
it was never invisible to relation one, so the family already knew about it; the merge moved a known case
into a second column rather than finding a new one.

The cost is to the count a human reads. "41 accepted inversions on the raise action" reads as 41 things
wrong with how often the chart raises. 25 of them are genuinely only visible on the raise action, 16 are
also pair-ladder cases, and 9 of those 16 are structurally guaranteed duplicates. The 25 is published
beside the 41 and is the honest number; nothing publishes that 20 of the 249 spots are a partition on which
the relation has no independent content. That should be one line in `RELATIONS[3]`, which is the file's own
place for a relation's scope.

**2. Six of the 41 sit at spots that round to zero arrival in parts per billion, and they include the
biggest-looking gaps in the tail.**

Against the same definition the report pins (`round(arrival * 1e9) == 0`, which reproduces the pinned 44
of 249 exactly), 6 of the 41 sit at zero-arrival spots, combined arrival 1.4e-12 percent of decisions:

| spot | pair | published |
|---|---|---|
| `t6/d100/HJ/LJ:raise@2.5,HJ:call,CO:call,BTN:call,SB:raise@7.5` | `TT` over `99` | 0.23 against 59.27 |
| `t6/d100/HJ/LJ:raise@2.5,HJ:call,CO:call,BTN:call,SB:raise@7.5` | `99` over `88` | 59.27 against 65.96 |
| `t6/d100/HJ/LJ:raise@2.5,HJ:call,CO:call,BTN:call,BB:raise@7.5` | `TT` over `99` | 0.23 against 46.92 |
| `t6/d100/HJ/LJ:raise@2.5,HJ:call,CO:call,BTN:call,BB:raise@7.5` | `99` over `88` | 46.92 against 57.64 |
| `t6/d100/HJ/LJ:raise@2.5,HJ:call,CO:call,SB:call,BB:raise@7.5` | `JJ` over `TT` | 0.02 against 1.25 |
| `t6/d100/BB/HJ:raise@2.5,CO:raise@7.5,SB:call` | `KK` over `QQ` | 92.56 against 99.96 |

Two of those gaps are 59 and 47 points, so they will be among the worst cases any severity claim reads off
the 41, and both are at four-way and five-way nodes a player is never dealt. A further 6 of the 41 sit
within one point of the one-point tolerance (gaps 1.03, 1.23, 1.37, 1.42, 1.80, 1.94), which are real
readings and negligible poker. No inversion of the 41 sits at a cell arriving below 0.24 percent reach, so
there are no reach artefacts.

Against that, **the 41 are broadly the right 41**. 35 of them sit at spots carrying at least 0.0026 percent
of decisions and 30 at 0.12 percent or more, both sides at 100 percent reach, and the head of the list is
severe and real: `LJ/rfi` publishes `44` opening 0.59 against `33` opening 100.00 at **16.2 percent of all
preflop decisions**, `SB/BTN:raise@2.5` `33` at 0.03 against `22` at 100.00 at 2.96 percent, and
`BTN/CO:raise@2.5` `33` at 0.00 against `22` at 100.00 at 2.81 percent. Weighted by how often the bot is
dealt the under-raised better pair at an inverted spot, the exposure is **0.2852 percent of preflop
decisions**, and 0.1530 percent restricted to inversions of 50 points or more - about one decision in 350,
on threshold pairs. As an EV matter the acceptance is fine and I am not disputing it. What needs saying in
the report is that 6 of the 41 are at spots that never occur, because 41 is published as a count and a
reader prices a count by its worst entries.

**3. The closed-spot reading the ruling withdrew is still a live assertion, and 52 of its 53 spots tie.
Its entire margin is one cell at one spot.**

`test_chart_counterfactual_arms.py:275-281` keeps the old restriction as a second assertion so that "a
later hand that wants the restriction back has to make one of them fail first". Measured, that second
reading is not a second opinion. Over the 53 three-bet-facing spots carrying a full grid the per-spot pairs
are: **21 spots at 0 against 0, 31 spots at 1 against 1, and exactly one spot at 1 against 2**. The one is
`t6/d100/BB/BTN:raise@2.5,SB:raise@7.5`. Remove that single spot from the committed set and the assertion
goes red; removing any of the other 52 leaves it passing. That is one spot out of 249 standing between a
green gate and a halt.

The reason is poker rather than arithmetic and is worth writing down: at a three-bet-facing spot hero's
continuing range is tiny, so these grids average **1.6 percent mixed cells** and are otherwise pure 0 or
100. A monotone pure row scores no kicker inversion, and the rank reversal carries the ace row onto the
deuce-kicker column, which in a three-bet-facing range is empty of continues, so it scores none either.
Both sides read near zero and tie. The rank arm is close to blind on the family that is 88 percent of the
committed set when it is restricted to full grids.

I am not asking for the assertion to be removed; keeping the withdrawn rule visible is the right instinct.
I am asking that the file stop describing it as a second reading that has to fail before the restriction
comes back. It is a coin flip that has landed the right way once, and the sentence at line 246 should carry
the 52-of-53 tie rather than the 32 against 33, which reads like a measurement with content.

**4. The test that proves the rank arm discriminates is an algebraic identity and cannot fail while the
gate passes. A test that would prove it is not in the file.**

`test_the_rank_arm_discriminates_where_the_suit_arm_cannot` builds the counterfactual chart by applying
`reverse_hand_ranks` to every grid, then asserts the suit arm scores it identically and the rank arm
refuses it. Both halves are guaranteed by construction. The reversal is its own inverse, so the reversed
chart's rank pair is exactly the solved pair swapped - I measured (7, 167, 181, 433) against (7, 167, 433,
181) - and the rank arm refuses it if and only if the gate passes on the real chart. The suit half is
likewise forced: rank reversal carries a suited hand and its offsuit twin together, so the multiset of twin
value-pairs per spot is unchanged and the suit arm's two figures cannot move. The contract at line 158
requires "a test proving it discriminates where the others cannot", and what is frozen proves nothing the
gate does not already assert about itself. That was equally true under the withdrawn restriction, so
decision 54 did not create it, but decision 54 changed the arm's scope and nobody rechecked what the test
is worth at the new scope.

The arm does discriminate, and here is a case that shows it rather than restating it. Apply a one-rank
rotation to the hand index (A reads K, K reads Q, down to 2 reads A), which is the classic off-by-one
extraction bug and is not the arm's own permutation. That chart scores (7, 167, 494, 555) on the whole set,
which the whole-set assertion **ships**, and is refused by 5 of the 10 partitions - `raises faced 0` at 90
against 40, `raises faced 1` at 218 against 107, `hero=BTN` at 84 against 68, `hero=SB` at 122 against 83,
`hero=BB` at 169 against 120. Because the gate asserts every partition, the family catches it. That is the
demonstration the file is missing, and it also shows why "dropping a partition is forbidden" is load
bearing: the whole-set row alone would have let this one through.

## Alignment

**1. The rank arm reads the wide grids and is nearly blind on the narrow ones, and the published figures do
not say so.** Split by grid, the arm's whole-set score of 181 against 433 decomposes into 64 against 206
over the 83 full grids and 117 against 227 over the 166 sparse ones. Inside the full grids the signal is
concentrated in the 30 wide spots: the 5 first-in read 11 against 61 and the 25 facing-an-open read 21
against 112, while the 53 full three-bet grids read 32 against 33. So the arm is strongest exactly where the
chart is a real opening or defending range and weakest where the range has collapsed to a handful of
continues. That is worth a line in the report because a reader who sees ten partitions all passing will
assume the arm looked equally hard at all of them; it did not, and the two skipped columns say how much it
could look at but not how much it saw. The entry to carry it is
`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR`.

**2. The repo has no external reference for the quantity the phase now names as its accepted defect.**
`expectations/six_max_nl25_100bb.json` carries three fields: opening frequency per seat, the small blind's
limp, and the big blind's **total** defence per opener. It carries no flat-versus-three-bet split. So the
old name pointed at a quantity the repo can check against an outside number and the new one points at a
quantity nothing outside the repo can check at all. That is a step away from checkability, not toward it,
and it compounds the earlier reviewer's alignment item that the one seat with an external check is the one
seat that matches it. `REFERENCE-RANGES-HAVE-NO-CITED-SOURCE` should carry the observation that the
reference now fails to cover the phase's own headline defect.

**3. The withdrawn restriction made the gate more set-dependent, not less, and that is measurable and worth
recording where the group-ladder ruling is recorded.** The contract refuses the group ladders as a gate
because "the family returned a different verdict on every committed set it has been run over". I ran the
same test on the rank arm by resampling the committed set. Over 2,000 random subsets of 50 of the 249, the
skip rule refuses **0.00 percent** of draws and the withdrawn full-grid restriction refuses 0.10 percent; at
subsets of 20 the split is 1.20 percent against 5.70 percent. The rule Taylor withdrew was between five and
infinitely times more likely to return a different verdict on a different set than the rule that replaced
it. The group-ladder objection therefore does not transfer to the rank arm, and the reason it does not is
worth one sentence beside the ladder ruling, so that the next reader who notices both are set-sensitive has
the numbers that separate them.

## The answer to the question the stage put to me

**Did the withdrawn restriction have a good unstated reason? No, and it had the opposite.** I measured the
`raises faced 2` partition three ways and every one passes: the skip rule at 149 against 260, an
apples-to-apples control that scores both sides only over comparisons present on both grids at 42 against
69, and the withdrawn restriction at 32 against 33. All ten partitions pass under all three rules. The skip
rule is the most robust of the three and the restriction is the fragile one, and it is far more fragile
than the published 32 against 33 suggests, because 52 of its 53 spots tie and the whole margin is a single
cell at `t6/d100/BB/BTN:raise@2.5,SB:raise@7.5`.

**Is an arm that skips most of its comparisons still measuring the hand index?** Yes, and the skipping is
not what buys the pass. Two measurements settle it. First, the solved side scores **more** comparisons than
the permuted side at every partition (13,094 against 12,589 on the whole set, 9,134 against 8,629 on the
three-bet family, 1,000 against 814 at `hero=LJ`), so the solved side has more chances to be caught out and
is caught out less; normalizing by comparisons scored widens the margin rather than closing it, 1.38
percent against 3.44 percent on the whole set. Second, the control that removes the composition question
entirely - score both sides only over the comparisons present on both grids, so the two are looking at the
same cells - passes on all ten partitions, 74 against 242 on the whole set. The group-ladder objection does
not apply here: those ladders pool cells into bands whose membership changes with the set, whereas this arm
compares a fixed cell against a fixed cell and drops the pair when one of them is not in the range. It is
measuring the hand index.

## What I checked and found sound

- The 249 and its 5 / 25 / 219 split, all ten partition rows of `PARTITIONS` including both skipped
  columns, the 44 zero-arrival spots and the 2 exactly zero, and the 13 spots folding every hand, all
  reproduce from the export by an independently written walk.
- Decision 55's arithmetic is exact: 11 pre-merge and 9 post-merge over the twenty merged spots, three
  vanishing and one appearing, the same four cases named, and 41 / 25 over the whole set against 43 / 28 on
  the raw raise row.
- The five-spot floor is real and has no instance: `raises faced 0` scores exactly five and every other
  partition scores more.
- The 41's three most-arrived cases are correctly labelled and severe. The record's correction of decision
  50's second case reproduces: `t6/d100/BB/CO:raise@2.5` publishes `33` at 0.00 against `22` at 8.13, and
  the severity claim survives through `t6/d100/BB/HJ:raise@2.5` at `33` 1.80 against `22` 70.15.
- The big blind's five rows, the 2.81-point flat spread, and the wider/narrower verdicts against the raked
  reference all reproduce to two decimals, and the test that publishes them recomputes each row's own
  verdict rather than asserting a fixed list, which is the right build.
