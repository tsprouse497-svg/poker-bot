# Phase 14 stage 8: the two independent reviews, and what they found

This is the stage's review record. It is an index and an outcome, not a third opinion: the reasoning
lives in the two notes beside it and is not restated here.

Two read-only reviewers, neither having written any of the work and neither having seen the other's
notes: one **mechanical**, asking whether the phase's own record is true, and one **domain** - the
poker lens, asking whether the ranges are any good. The domain pass is the one the driver says exists
because it "ignores the contract and asks whether the work is right, which is the only question a
green gate cannot answer", and at this stage it is what found both range defects.

| note | blockers | non-blockers | alignment |
|---|---|---|---|
| `stage-08-review-mechanical.md` | 2 | 5 | 2 |
| `stage-08-review-poker.md` (the domain lens) | 2 | 3 | 3 |

The stage-8 question is not the stage-6 or stage-7 question. Stage 6 asked whether the build did what
it said and stage 7 whether the canaries and the gate repairs were sound. Stage 8 asks whether the
phase's record is true and whether the ranges are any good - which the driver puts as "the only
question a green gate cannot answer". The gate was green at 47 of 47 with all 74 canaries biting
before either reviewer started, and both found things anyway.

## Blocker

All four were found against a gate already green at 47 of 47 with all 74 canaries biting, and all four
are closed. The detail is in the two notes beside this one.

- **The artifact told the trainee the wrong thing about its own coverage.** **[resolved]**
  Its notes said the chart "excludes 33,720 of them, which is 98.59 percent of the preflop decisions
  the bot ever faces". The committed 249 carry 98.5949 percent; the excluded 33,720 carry 1.4051 and
  are 99.2670 percent of the *nodes*. False on every reading, in the file every later phase is
  measured against. Fixed at 5e119cf: each figure now sits with the set it describes, and the notes
  say that a share of nodes and a share of decisions are different measurements. The coordinator had
  checked those figures and passed them, having checked whether the numbers were real rather than
  whether the sentences were true. Mechanical note, blocker 1.

- **Nine spots that are fifteen.** **[resolved]**
  Three committed sites gave decision 45's argument for merging rather than deleting as "at nine of
  these spots a hand's whole weight sits on calling". Over the 20 merged spots it is 15 spots and 40
  cells; over all 249 it is 108 and 748. The 40 is what the frozen tests carry, so only the spot count
  was wrong, and the ambiguity about which set is what produced it. The nine came from counting one
  seat: 9 of the 15 are the small blind. Fixed at 5e119cf, and the report's pair now interpolates from
  a walk rather than being a literal. Mechanical note, blocker 2.

- **The merged three-bet family folds the aces and kings and plays the connectors.** **[resolved]**
  Under the report's own fifty-point rule, 62 classes are folded here and played by the raked
  reference and every one holds an ace or a king; 63 are played here and folded there and not one
  holds either. Unanimous per spot at all ten, and 100-to-0 at every threshold from 50 to 99, so it
  does not depend on where the line is drawn. King-queen offsuit is folded pure at 10 of 10. The big
  blind is a control and the signature is absent there. Taylor ruled on 2026-09-05 to publish and ship
  rather than re-solve or soften; published at 25f0d76. Poker note, blocker 1.

- **The four-bet ranges pick bluffs with no blockers.** **[resolved]**
  At the 219 three-bet-facing spots, 88 percent of the chart. King-ten or king-jack suited four-bets
  above half at 0 of 15 spots here against 10 of 15 in the reference, and the unpaired no-blocker
  share is higher at 15 of 15. The heaviest grid four-bets 86s, 96s, 97s, 98s and Q8s to 22.5 while
  flat-calling every suited ace and suited king but two. Published at 25f0d76 with the tension named:
  the packet defends the wheel-ace exemption on blocker logic while the four-bet does the reverse.
  Poker note, blocker 2.

## Non-blocker

Eight between the two notes, each with its measurement, and none restated here. The two worth naming
because they change what a reader may conclude: the report's hardcoded claim that the big blind folds
93 percent of its range at the squeeze spots, against a measured 84.99 to 93.33 with 5 of 10 spots
below 90; and that 9 of the report's 15 `vs one three-bet` rows compare this chart's 7.5bb three-bet
against a reference facing 11 or 13.5, so "total defence wider at 15 of 15" cannot mean what it is
read to mean.

## Alignment

Five between the two notes, every one filed against an existing `backlog.yml` id rather than a new
one: `A-RELATION-THAT-ONLY-COMPARES-NEIGHBOURS-CANNOT-SEE-A-TWO-CELL-HOLE`,
`NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL`,
`PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS`, and the two the mechanical note names.

## What the poker reviewer said is right, which matters as much

No premium is mishandled anywhere in the 249. The big blind's three-bet ranges are textbook. Defence
against a three-bet is monotone in position. The reviewer's verdict was that the chart is fit to be
the reference for coverage, prices and the opening and big-blind families, and not yet fit as the
thing a student is drilled on at the merged three-bet and four-bet families - and that the packet
currently claims the opposite of the first of those, stage 6 having signed that family off as
shape-sound after reading three grids by eye.

## The mapping fault that was ruled out rather than assumed away

The same one-direction signature now appears in three separate families - the opening ranges at stage
6, and the merged three-bet and four-bet families here - and this codebase confused two hand-class
orderings once already this phase, in the equity table's own card. So it was checked rather than
argued about. Aggregated over all 249 committed spots the most-played classes are AA, KK, AKs, QQ,
AKo, JJ, A5s, JTs and the least-played are the eight worst offsuit trash hands, with AA and KK at
1.000 and 72o and 32o at 0.000. A permuted index scrambles that completely. **The hand index is
sound and the ranges are the solve's own**, which is what makes the poker finding a statement about
what this phase ships rather than about how it read it.
