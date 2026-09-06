# Phase 14 stage 9: the two independent reviews of the audit packet, and what they found

This is the stage's review record. It is an index and an outcome, not a third opinion: the reasoning
lives in the two notes beside it and is not restated here.

Two read-only reviewers, neither having written any of the packet and neither having seen the other's
notes: one **mechanical**, asking whether every number in the packet is recomputable and every claim
narrower than the evidence behind it, and one **domain** - the poker lens, asking whether the packet
tells the truth about the poker and whether a strong player would come away with an accurate picture.
The question the driver prints for this stage is the mechanical one: *a wrong figure in a packet
outlives the phase and gets quoted.* The domain pass is the one that caught both of the packet's own
overclaims.

| note | blockers | non-blockers | alignment |
|---|---|---|---|
| `stage-09-audit-mechanical.md` | 3 | 9 | 2 |
| `stage-09-audit-poker.md` (the domain lens) | 2 | 5 | 3 |

## Blocker

All five are closed. Every one was found against a packet whose figures had already been re-derived by
five extraction lanes, and three of the five are statements this stage had itself just written.

- **[resolved]** The packet said corpus refusals rise. They fell by about 95 percent, and the sample grew.
  Pluribus refused 430 of 502 decisions before and 27 of 502 after; humans 2,099 of 2,546 before and 112
  of 2,546 after. The packet inherited the sentence from `latest_derived_chart_report.txt`, which also
  compounded it with "an agreement rate over a smaller sample is the shape to expect" where the scored
  sample grows from 72 to 475 and from 447 to 2,434. Written when the committed set was 36 spots and
  false of the 249. Fixed in `scripts/generate_derived_chart_report.py`, which now prints the direction
  it measured and says the passage was corrected, and in the packet's `Republished` section. This was a
  sixth false report statement the stage-9 extraction lane missed. Mechanical note, blocker 1.

- **[resolved]** A sentence this stage wrote to correct a false claim was itself false.
  The new purity wording read "most of what the merge moved was already pure **on calling** before it".
  Re-derived from the export: of the 165 moved cells, 93 were pure before but only 73 were pure on
  calling, so the qualifier turns a true claim into a false one. The packet's own wording was the true
  one. Fixed by dropping the qualifier. Mechanical note, blocker 2.

- **[resolved]** A new `backlog.yml` entry contradicted itself in its own title.
  `A-FROZEN-TEST-DOCSTRING-ASSERTS-WHAT-ITS-TOLERANCE-ADMITS` was titled "tolerance is forty times the
  worst case" where its body measures 0.05 against 0.0268 and says "nearly twice". The body is right at
  a ratio of 1.87. Title corrected. Mechanical note, blocker 3.

- **[resolved]** The packet certified the big blind's three-bet ranges as textbook, and the
  measurement that condemns the four-bet family condemns them too.
  Over the five big-blind spots facing an open, the share of unpaired raising mass in hands holding
  neither an ace nor a king is higher than the raked reference at **5 of 5** - 35.16, 33.55, 38.49,
  42.37 and 48.11 against 13.85, 22.44, 25.99, 30.78 and 29.91. Against a small blind open the chart
  three-bets K8o, Q8o, T8o, 98o, T5s, 53s and 64s at 1.000 and 87o at 0.9997 while flat-calling KQo,
  KJo, QJo and JTo at 1.000. Both re-derived by the coordinator from `action_weights` before the fix.
  Stage 8 had used the big blind as the control showing the signature was local; it is not. The packet
  now publishes the 5-of-5 shares and that grid, and narrows the verdict to *fit as the reference for
  coverage and prices, and not yet fit as the thing a student is drilled on wherever a raise is already
  in.* Poker note, blocker 1.

- **[resolved]** "No premium is mishandled anywhere bar six cells" was measured over three hands.
  The read covers aces, kings and ace-king suited. Under the same rule - cells arriving at half reach
  or better - **ace-king offsuit is folded above 5 percent at 59, more often than not at 33 and
  outright at 16**, and **queens fold 50.40 percent** at `t6/d100/SB/LJ:raise@2.5,HJ:raise@7.5,CO:call`
  while being asked 7.0 into 19.0, with a near-twin at 50.36. The packet now states the read's scope
  and publishes both. Poker note, blocker 2.

## Non-blocker

Fourteen between the two notes, each with its measurement, and none restated here. The three worth
naming because they change what a reader may conclude:

The big blind's defence is **narrower** than the raked reference against a button open, 36.653 against
39.430, so the packet's "a floor cleared" holds at four of the five openers and not the fifth - the one
direction a rake-free solve is not supposed to go. The packet now says so.

The multiway worked example's counterfactual defence **is not published at all**. Two stage-9 walks put
it at 36 and at 70 percent and the difference is the equity source, which neither could see into from
the other side. The poker reviewer's own controls check out - its evaluator matches the committed
169-by-169 table heads-up, and its all-in shares satisfy the conservation identity to 0.0009 - and the
36 would need opponents averaging about 0.287 each, tighter than three copies of an 18.7 percent
opening range. Neither figure is published; only the direction is claimed, and the direction argues for
the refusal either way.

The poker reviewer **corrected its own blocker figure** when challenged: its "ace-king offsuit folds
100 percent at 33 spots" was the above-half count wearing the pure-fold label, carried over from the
head of a sorted printout. Re-measured, the ladder is 59 / 33 / 21 / 16 at reach 5000 or better. The
blocker stands at 16 outright folds; the note carries the correction.

## Alignment

Five between the two notes, every one filed against an existing `backlog.yml` id:
`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`,
`NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL`,
`A-RELATION-THAT-ONLY-COMPARES-NEIGHBOURS-CANNOT-SEE-A-TWO-CELL-HOLE`,
`PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS` and
`THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS`.

Two new entries were filed by this stage rather than as alignment items, because they are defects with
measurements rather than drift: `EXPOSURE-WALK-DROPS-MASS-AT-NODES-NO-HAND-REACHES` and
`A-FROZEN-TEST-DOCSTRING-ASSERTS-WHAT-ITS-TOLERANCE-ADMITS`.

## What reproduced, which matters as much

The mechanical reviewer re-derived and confirmed: coverage and the four-bucket census, the 106 and 81
cold-call spots, ace-king offsuit at 47 of 81 and 6,619 basis points, the six ace-king-suited premium
folds and their exact percentages, the 62-against-63 merged split with its unanimity at every bar from
50 to 99, the hand-index top eight and the 48 never-played classes, the whole purity chain, the exposure
leak, every gate-coverage figure, 219 backlog entries, 55 decisions, and the 16 limped rows summing to
52. It found the contract's packet requirements met in the form the contract demands and all four
prohibitions honoured, with `THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR`
named and `GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE` stated as deferred.

The poker reviewer reproduced the merged-family split and its unanimity, king-queen offsuit folded pure
at all ten, the four-bet 0-of-15 against 10-of-15, the six premium cells, the capped-spot figures with
the four premiums absent by arrival, the 87 wheel-ace split and both named first-in cells, and the
hand-index evidence. Its verdict on placement was that the largest finding is not buried; it was
softened only at the very end, by the two "what went right" claims that became its blockers.

## The correction this stage owes its own record

Three of the five blockers are statements stage 9 wrote or carried while correcting other people's
false statements: the refusal direction, the purity qualifier, and a backlog title. That is the same
failure mode the phase has hit at every stage, and the reason this stage delegated its extraction to
five lanes and its review to two more. `pytest_derived_chart` reads 111 passed and 4 skipped both
before and after every generator edit made here.
