# Phase 14 stage 4: independent review, the poker

Read-only review of the uncommitted stage-4 re-cut on `phase/14-chart-cutover`, written 2026-09-03 by a
reviewer who authored none of it and has not seen the mechanical reviewer's notes.

The remit is the poker rather than the code's fidelity to the contract: whether the hands, prices and
refusals these tests pin describe a chart worth playing. Every number below was re-derived from
`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz` by a walk written for this pass in a
scratch directory outside the repo. The selection walk was imported from `tests/test_chart_derivation.py`
so that the set under review is the set the stage selects; it reproduces 249 nodes, split 5 / 25 / 219, at
98.59487 percent coverage. `check_gate_bite.py` was not run and nothing in the tree was modified.

Where I could not put a number on an objection I have said so and filed it as alignment, per the rule that
a solved range is not a defect on intuition.

## Blocker

**[resolved] The fourth relation reads an action the bot does not take at the twenty spots where decision 45
changed what it takes.**

**Resolved 2026-09-03.** Taylor ruled the relation reads the merged weight, what the bot actually plays.
`raise_weight()` now adds the solve's call into its raise at the 20 merged spots, and an independent walk
reproduced this reviewer's figures exactly: 11 inversions pre-merge against 9 post-merge over those spots,
the same three vanishing and the same one at `t6/d100/CO/HJ:raise@2.5` appearing. Over the whole set the
pinned pair moves from 43 and 28 to 41 and 25. Recorded as decision 55; the contract now reads "the
published raise weight (decisions 50, 55), merged as the bot plays it".

`tests/test_chart_cutover_evidence.py` pins the fourth relation's scope as "the solve's raise weight
**before** the merge" (`RELATIONS`, and the docstring under it), and `raise_weight()` implements that by
summing the raw `raise` rows. Decision 50 added this relation for one reason, stated in the contract: the
defect that halted the phase was a pair inversion **on the raise action** that play-not-fold cannot see.
The action the bot takes at the 20 merged spots is the merged raise, not the solve's raise.

Measured over those 20 spots, at the file's own tolerance of one point and reach floor of zero:

| reading | pair inversions on the raise weight |
|---|---|
| pre-merge, what the relation reads | 11 |
| post-merge, what the bot plays | 9 |

Three of the eleven do not exist in play. The merge fills the flat into the raise and the ladder resolves:

- `t6/d100/HJ/LJ:raise@2.5` reads `JJ` 94.66 against `TT` 99.76 pre-merge; both are 100 post-merge.
- `t6/d100/CO/HJ:raise@2.5` reads `JJ` 88.34 against `TT` 100.00 pre-merge; both are 100 post-merge.
- `t6/d100/BTN/HJ:raise@2.5` reads `88` 60.84 against `77` 74.54 pre-merge; both are 100 post-merge.

One that the bot really does play is invisible to the relation as written:

- `t6/d100/CO/HJ:raise@2.5` publishes `77` raising 49.21 and `66` raising 66.23. The bot three-bets the
  worse pair more often than the better one at a spot carrying real traffic, and the relation added to
  catch exactly this reads zero there.

Over the whole 249 the two readings give 43 raise-weight pair inversions pre-merge (28 invisible to
play-not-fold) against 41 post-merge (25 invisible).

The file argues the choice deliberately: decision 50's three named cases do not merge, so either reading
catches them, and reading the merged weight "changes the family's membership without touching what the
decision measured". That argument is backwards for this relation. Changing the membership toward what the
bot plays is the whole point of a relation defined on an action rather than on play-not-fold. The count is
published as an accepted defect with a cost a human signs off on, and as written it hands that human three
inversions the bot never commits and hides one it does.

This is inside stage 4's own scope to fix. It needs no ruled constant moved, no frequency adjusted and no
tolerance touched: it is which weight `raise_weight()` reads at a merged spot. It is a blocker rather than
a non-blocker because stage 5 freezes the file and the count then travels to the packet uncorrectable.

If the objection to the merged reading is that at a merged spot the menu is fold-or-raise, so relation four
would duplicate relation one there, that is true and is not a cost. A duplicated true count is better than
a distinct false one, and the 20 spots can be reported as the relation's redundant partition rather than
measured on a phantom action.

## Non-blocker

**1. The stated argument for the third clause does not separate the ten spots it refuses from ten it
commits.**

`tests/test_chart_derivation.py` pins `BB_SQUEEZE_FOLD_PCT = 93.33` and says it is asserted "because it is
the whole argument for the third clause": the big blind's fold is what makes the exposure filter blind
there. On the identical action sequence the argument holds at least as strongly at three committed
siblings.

| spot | status | measured exposure | hero folds |
|---|---|---|---|
| `t6/d100/BB/LJ:raise@2.5,HJ:call` | refused | 3.737% | 93.33% |
| `t6/d100/SB/LJ:raise@2.5,HJ:call` | committed | 3.787% | 95.50% |
| `t6/d100/BTN/LJ:raise@2.5,HJ:call` | committed | 5.138% | 95.44% |
| `t6/d100/CO/LJ:raise@2.5,HJ:call` | committed | 6.195% | 95.68% |

The refused spot has the lowest measured exposure and the smallest fold of the four. "The fold suppressed
the exposure" is true of all of them, so it does not name the set.

The rule that does name it is different and is not the one written down: the big blind is the only
facing-an-open seat whose published chart still offers a call, so it is the only one whose exposure figure
is priced through the multiway model at all. At the other seats decision 46 removes hero's cold call from
the measurement and decision 45 removes it from the chart, so the branch the model cannot price is one the
bot never takes. That is a sound reason to refuse the ten and commit the others. I am not asking for the
set to move. I am saying the reason frozen beside it is measurably not the reason, and the contract
requires the report to give this reason to a non-coding reviewer.

**2. "The big blind defends too tight" is the wrong name for the defect the phase measured.**

Against `expectations/six_max_nl25_100bb.json`, which is a raked game and so should be the tighter of the
two:

| opener | chart defends | reference | direction |
|---|---|---|---|
| SB | 48.39% | 42.88 | wider |
| BTN | 36.65% | 39.43 | narrower |
| CO | 32.78% | 31.48 | wider |
| HJ | 28.88% | 26.20 | wider |
| LJ | 25.70% | 22.63 | wider |

Four of five read wider, which is the expected direction for a rake-free solve, and only the button reads
narrower. `test_the_big_blind_defence_and_flat_are_published_with_the_band_at_both_ends` is well built and
recomputes each row's own wider/narrower verdict, so the report will print "wider" four times under a
heading that says the big blind over-folds. The measured defect is the one the same test pins as the flat
spread: the flat is 19.63, 20.30, 20.98, 21.09, 22.44 percent across openers whose own ranges span 18.74
to 54.30. A 2.81-point spread against a 35-point spread in what it is answering is a range that is not
responding to the opener at all. That is a shape defect, and an EV band computed on the level does not
measure it. The fix here is what the packet calls the defect, not the numbers.

**3. The merge manufactures traffic into the family the chart refuses, and nothing measures it.**

At the 20 merged spots the published raise is the solve's raise plus its call: 165 cells move, 40 of them
pure on the entire-weight reading, 73 at 99 percent or more. I reproduce all three counts. The 40 pure
cells are the hands you would expect a solver to flat and not three-bet:

`AJs` (5 spots), `TT` (6), `AQs` (5), `AQo` (4), `99` (4), `A9s`, `ATo`, `ATs` (2), `A3s`, `JJ`, `88` (2),
`77` (2), `66` (2). Each was a 100 percent flat in the solve and is a 100 percent three-bet in the chart.

Conditional on hero taking that raise, a four-bet comes back 7.01 to 18.73 percent of the time depending on
the spot, and at that four-bet the solve's own answer for these hands is to fold between 10.0 and 98.5
percent, weighted around 70. The bot cannot execute either answer, because the four-bet node is refused.

The traffic that creates, per hand dealt, against the seat's existing four-bet refusal rate:

| seat | added by the merge | existing four-bet refusals | relative increase |
|---|---|---|---|
| SB | 0.2282% | 1.032% | +22% |
| BTN | 0.1386% | 1.032% | +13% |
| CO | 0.0841% | 0.690% | +12% |
| HJ | 0.0049% | 0.510% | +1% |

The accepted defect as filed is `MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED`, and the
tests pin the cells moved and each spot's defence against the solve's raise-plus-call. Neither reaches the
consequence. Decision 45 and the four-bet exclusion are each defensible alone; together they take a hand
the solve wanted to see a flop with and route it, one time in eight, to a spot the trainer answers with a
refusal. That is the phase's largest single change to how the bot plays and the number above is not
published anywhere.

To be fair to the merge: the resulting ranges are well shaped. `t6/d100/BTN/CO:raise@2.5` publishes 11.96
percent carrying `A5s`, `A4s`, `A3s`, `87s`, `76s`, `T9s`, `J9s` as bluffs beside the value hands, and
`t6/d100/SB/BTN:raise@2.5` 14.98 percent with the same shape. "Merging loses no range and lands every
non-blind spot inside the standard three-bet band" survives measurement. The cost is downstream, not in
the range.

**4. The cheap-against-dear narrowing is arithmetically right and attributes the finding to the wrong
side of the comparison.**

Narrowing the band to the big blind is sound as far as it goes. The 20 merged spots publish raise-or-fold,
so a human flat there is a disagreement at every price alike, and pooling them would add a
price-independent block to both bands and compress a ten-point margin that had not changed. That reasoning
holds.

What the docstring then claims is that "a chart answering at 2.5 is answering a more expensive question
than the one it was asked", which reads the gap as a fact about the chart. At the five spots the split is
now measured over, the chart's call frequency is 19.63 to 22.44 percent whoever opened, which is the
near-invariance the neighbouring test pins as a defect. A near-constant cannot produce a price-sensitive
gap. The gap the assertion measures is human price sensitivity scored against a constant, which is a real
finding and a different one. Naming the seat was right; the sentence above it should say whose sensitivity
is being measured.

## Alignment

**1. The chart's only external reference check sits on the five spots that kept a call.**
`expectations/six_max_nl25_100bb.json` gives an opening frequency per seat and a big-blind defence per
opener, and nothing else. So of the 25 facing-an-open spots, the 5 big-blind ones are checked against an
outside number and the 20 merged ones are not. Those 20 are where the solve's cold call runs at 0.13 to
4.65 percent, against the big blind's 19.63 to 22.44 at the same 2.5 price, even though the big blind has
the worst postflop realization of the six seats and every merged seat has a better one. A model in which
the worst-realizing seat flats forty times more often than the best-realizing one is a model artifact, and
this repo holds no reference that would catch it. `PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS`
is already filed; it should carry that magnitude and the observation that the one seat with an external
check is the one seat that matches it.

**2. The ladder inversions are published as counts, and the count is not the cost.**
I reproduce 114 pair inversions on play-not-fold, 181 kicker inversions, 87 wheel-ace and 94 with no story.
Two measurements say more about them than the totals do.

Weighted by how often the bot is actually dealt the hand on the wrong side, 0.39 percent of preflop
decisions find it holding the dominant, under-played class of a non-wheel inversion of 50 points or more
(0.51 percent at any magnitude). That is about one decision in 256, on threshold hands, so as an EV matter
the acceptance is fine and I am not disputing it.

Direction is the number that says whether the ladder carries information. Among adjacent comparisons the
chart decides past the one-point tolerance, 28.1 percent of pair comparisons and 15.2 percent of kicker
comparisons run the wrong way, against 0.7 percent on the suited-over-offsuit relation in the same export
at the same tolerance. The suit dimension of this solve is clean and the rank dimension is forty times
less so. Publishing 114 and 181 tells a reader neither of these things.

Against that, the training cost is real and unmeasured by anything here. `t6/d100/BTN/CO:raise@2.5` carries
2.81 percent of all preflop decisions and publishes `22` three-betting 100 percent while `33` and `44` fold
100 percent and `55` three-bets 56. `t6/d100/CO/rfi` carries 10.35 percent and opens `Q6s` 100 percent
while folding `Q7s`. Decision 51 is right that picking among hands the solve prices alike is bluff
selection and costs nothing. It is still an anti-pattern to drill into a human, and nothing in this phase
measures legibility as distinct from EV. That is a product question, not a phase-14 one.

**3. The wheel-ace exemption is one comparison, and the trough it describes is wider than the exemption.**
All 87 exempted cases are `A6s` over `A5s` (84) and `A6o` over `A5o` (3). Preferring the wheel ace there is
correct poker and the exemption is right. But `A8s` over `A7s` (15) and `A7s` over `A6s` (12) are filed
under "no poker story", and they sit in the same `A6s` to `A9s` trough whose existence is the reason the
wheel aces are unchained. The 94 is therefore an upper bound on the family with no story, and 27 of it has
at least a partial one. The residue that genuinely has none includes `KQo` over `KJo` at eight spots, one
of them severe (`t6/d100/LJ/LJ:raise@2.5,HJ:call,CO:raise@7.5,BTN:call` folds `KQo` 99.73 percent and calls
`KJo` 55.76), and `AQs` over `AJs` at five. A dominated hand played and its dominator folded is the one
kicker case that cannot be bluff selection, and it is worth naming apart from the rest.

**4. Coverage as decision mass is not the number a trainee experiences.** The 98.5949 percent is correct
and it is concentrated: the top 20 of the 249 spots carry 90.17 percent, the top 50 carry 97.53, and the 44
spots that round to zero in parts per billion carry 3.6e-9 percent between them. Carrying those 44 is
harmless and I would not remove them; it does mean the selection rule is not measuring what makes the chart
useful, and the arrival grain the contract requires is the right place to say so.

The number a human at the table meets is per hand and per seat, and it is not published:

| seat | hands containing a refused preflop decision | of which |
|---|---|---|
| BB | 4.900% | squeeze 3.024, four-bet 1.818, exposure 0.058 |
| SB | 1.091% | four-bet 1.032 |
| BTN | 1.054% | four-bet 1.032 |
| CO | 0.728% | four-bet 0.690 |
| HJ | 0.512% | four-bet 0.510 |
| LJ | 0.351% | four-bet 0.320 |

A bot that refuses one hand in twenty in the big blind is playable, and I would answer the phase's own
question that way. But 4.9 percent in one seat is a different statement from 1.4 percent of decisions, and
the packet asks a non-coding reviewer to accept the exclusions on the second figure. Publish both.

## What I checked and found sound

Recorded so that a later reader knows these were measured rather than skipped.

- The 249 and its 5 / 25 / 219 split, the 98.59487 coverage, the 165 / 40 / 73 merge counts, the 114 / 181
  / 87 / 94 inversion counts, and the 44 spots at zero arrival with 2 exactly zero all reproduce from the
  export by an independently written walk.
- The untouched-uniform-initialisation criterion holds and holds for the right reason. Of 42,081 possible
  committed cells, 18,431 have non-zero reach and 23,650 do not; 14,410 uniform rows exist and every one
  sits at zero reach, so none is committed. At a three-bet-facing spot a class's reach equals hero's own
  opening weight for it (169 of 169 classes match at `t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5` bar one
  rounding unit), so dropping a zero-reach class is exactly dropping a hand hero folded preflop. The bot
  cannot end up playing one of those cells at the table.
- The merged three-bet ranges are polarised and sized like real ranges, 8.94 to 14.98 percent, with wheel
  aces and suited connectors as the bluffs. Decision 45's claim about the standard band survives.
- The migrated completed-phase tests read honestly. `test_postflop_fallback.py` declines to assert that
  `t6/d100/BB/BTN:raise@2.5` is committed and moves every chart claim to the lojack's first-in spot, which
  is the right instinct; the four-bet fixture is replaced by a refusal at
  `t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5` and the two-price draw is labelled vacuous with
  its premise asserted rather than assumed. Opening at 2.5 from all five first-in seats, the big blind's
  squeeze refused, and every seat behind an opener covered are all true of the 249.
