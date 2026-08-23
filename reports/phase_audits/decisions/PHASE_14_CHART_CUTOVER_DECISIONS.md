# Phase 14 judgment calls

These are the choices that decide which ranges the bot plays. Every phase after this one is
measured against what is committed here, so the balance of this list runs the other way from
phase 13's: eight of thirteen items are `frozen-into-data` against that phase's one.

Every item carries a reversibility class, which the loop driver reads at stage 3 to decide
whether it must stop for a human.

- `runtime-reversible`: the choice only changes behaviour at query or report time, so a later
  edit changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact or fixture that every later
  phase is then measured against. The loop halts until a human answers.

`verification/loop_policy.yml` gives this phase `auto_advance: false`, so it stops at stage 11
regardless. The classes still matter, because stage 3 stops it *before* any test is authored,
which is the only point at which a different answer is cheap.

## What was measured first

Every number below was measured on this branch. Stage 1 found that the roadmap's planning figures
for this phase were superseded and that its size estimate was low by half, so nothing here is
quoted from `docs/V2_ROADMAP.md`.

### The export cannot be committed whole, twice over

`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz` holds 38,828 action nodes.
Committing them as chart spots measures 272 MiB at the retired chart's own 7,346 bytes per spot,
131 MiB compacted, 407 MiB keeping all 169 hand classes per node the way a GTOpen node carries
them, and 71 MiB with each spot filtered to hero's arriving range. The cap on `data/artifacts` is
20 MiB and the tree already holds 4.4 MiB, of which 4.0 MiB is the export itself. Deleting the
retired chart frees 0.25 MiB. So the budget is about 15.9 MiB - 2,267 spots at the retired
chart's rate, or 8,650 at the 1,925 bytes per spot a GTOpen node costs once filtered to hero's
arriving range, which is the filtering the retired chart already does. Compression is not a way
out: `import_preflop_artifacts` globs `*.json` and reads text.

Expressibility is not the constraint. Every one of the 38,828 nodes derives a valid v2 spot key,
with zero rejections and no collisions - a clean bijection.

### What reach actually looks like over that tree

Arriving reach per node, as the mean over the 169 hand classes of the fraction of hero's range
that gets there, read out of the export's own `reach_bp` rows. Median 0.19 percent. The sizes are
at 1,925 bytes per spot, hero-range-filtered, against a 15.9 MiB budget.

| reach at least | nodes | filtered size |
|---|---|---|
| 20% | 891 | 1.6 MiB |
| 10% | 1,424 | 2.6 MiB |
| 5% | 3,296 | 6.1 MiB |
| 2% | 5,626 | 10.3 MiB |
| 1% | 9,407 | 17.3 MiB |
| 0.5% | 13,575 | 24.9 MiB |

So a 1 percent floor is the first one that does not fit, and 2 percent leaves 5.6 MiB spare.

### Depth, counted the same way

Nodes by the number of prior actions on their path, folds included, cumulative: 351 at five or
fewer, 880 at six, 2,079 at seven, 4,384 at eight, 8,100 at nine, 13,152 at ten. The tree runs to
20 and is thickest at 11 and 12.

### The export offers all-ins where the old source never did

Action kinds per node: 33,964 nodes offer neither a jam nor a named raise beyond the ones already
counted, 607 offer both a named raise and a jam, and **4,257 offer a jam and no named raise at
all**. The GTO Wizard source this repo converted before has zero of the third kind. That is what
makes decision 6 a live question rather than an inherited rule.

### Convergence is not uniform over that tree

GTOpen's solve target is a best-response gap in big blinds summed over the whole tree, so a
0.01bb target constrains nothing at a node carrying negligible mass. Over the eleven grids the
export publishes, the two dominance relations that hold in every preflop spot - a higher pair
played at least as often as a lower pair, a suited hand at least as often as the offsuit hand of
the same two ranks - separate the shallow tree from the deep one sharply. Comparing adjacent
ranks only, with a tolerance of about one percentage point, the ten shallow reference nodes give
**one** violation and the single deep four-bet node gives **42**.

Those two numbers are tolerance-dependent and the tolerance is nobody's ruling yet, which is what
decision 10 exists for. At zero tolerance the same comparison gives 11 shallow and 43 deep on
adjacent ranks, and 34 and 73 comparing every higher pair to every lower one. Ten of the eleven
shallow adjacent violations are numerical noise at gaps of 0.01 to 0.19 points - the cutoff opens
44 at 99.91 under 33 at 99.99 - and one is real. The separation between shallow and deep survives
every variation; the counts do not.

The real one, and the deep node beside it. The lojack opens 44 at 72.81 percent while opening 33
at 99.88 and 22 at 99.92. And the hijack facing a lojack four-bet to 22.5 folds JJ 97 percent, TT
outright, 99 outright and KJs outright, while calling 76s outright and 87s 94 percent, at 64 to
100 percent arriving reach. Hero adds 15.0 into a pot of 31.5 there and needs 32.3 percent: JJ has
it comfortably and 76s barely.

Phase 10's human verdict read the shallow grids. It did not read that one.

### The retired chart and the new one barely collide

The retired chart three-bets to 8, 11 and 13.5 and opens the small blind to 3.5; the export
three-bets uniformly to 7.5 and opens to 2.5. **17 of its 36 keys collide with nothing the new
artifact declares** - every three-bet spot and the whole small-blind-open family.

### The deltas the closing prediction has to be built from

Big-blind defence in the new solve against the retired chart: **+4.65** points against the
lojack, **+3.72** against the hijack, **+2.64** against the cutoff, **+6.14** against the small
blind, and **-2.67** against the button. The button generates the most big-blind defending
decisions in any six-max sample, so the aggregate statement "defence widens" is false on its
largest component.

Small-blind entry moves from 48.14 percent - 34.41 raising plus 13.73 limping - to 54.09 percent
raising. That is about six points wider entry with 13.73 points of limping converted to raising,
not the 19.68-point headline the raw open-frequency delta suggests.

---

## 1. Which nodes of the solved tree become committed spots

Reversibility: frozen-into-data

**This is the phase.** Both reasons above force a selection, and whichever rule is chosen decides
which spots the bot can play and which it refuses from here on. A later change is a re-derivation
of the whole artifact and a re-run of every measurement built on it.

The question, in one sentence and with no code in it: the solver produced ranges for 38,828
situations, of which at most a few thousand fit in the space the repo allows and only the
shallow ones are trustworthy - so should the bot get the situations it will actually meet most often, the ones the
solver is most confident about, or the ones a human has already checked?

Each option below is a complete predicate with its threshold named, because a family without a
threshold leaves the implementer choosing what the chart contains, and the contract forbids
picking the number to fit the byte limit and justifying it afterwards. Sizes are hero-range
filtered against a 15.9 MiB budget.

**Reach at 2 percent.** Keep a node when at least 2 percent of hero's range arrives there. 5,626
spots, 10.3 MiB, 5.6 MiB spare. Keeps every open, three-bet and blind-defence line and drops the
deep branches where the strategies are unconverged. The option that answers both constraints at
once, because the nodes that are cheap to drop are the nodes that are wrong.

**Reach at 5 percent.** The same rule, stricter. 3,296 spots, 6.1 MiB. Refuses more and is
further from the size ceiling, which matters because the next solve - another depth, another
table size - lands in the same directory.

**Depth at eight prior actions.** Keep a node when at most eight actions precede it, folds
included. 4,384 spots, 8.0 MiB. Simpler to state and a reader can tell at a glance what the chart
covers, but it is a proxy: it keeps shallow nodes with almost no mass and drops deep ones with
real mass. The reach floor and this one disagree on thousands of nodes.

**Reach at 2 percent with a depth floor.** Keep a node when 2 percent of hero's range arrives
*or* at most five actions precede it, so the whole opening and three-betting skeleton is kept
whatever its mass. At most 5,626 + 351 spots and in practice fewer, since the two overlap. Costs
almost nothing over the first option and guarantees no common line is dropped by an arithmetic
accident.

The cost of getting this wrong is not a wrong answer at the table - an excluded spot is refused,
not guessed - it is the bot refusing hands it could have played, or answering from cells the
solver never trained. Refusing too much is recoverable by a later phase; answering from an
untrained cell is what this decision exists to prevent.

Options: reach-at-2pct | reach-at-5pct | depth-at-8 | reach-at-2pct-with-a-5-action-floor
Answer: []

## 2. What happens to the non-monotone pair

Reversibility: frozen-into-data

The lojack opens 44 at 72.81 percent while opening 33 at 99.88 and 22 at 99.92. It is the only
violation in the shallow tree that is not numerical noise - the other ten sit at gaps of 0.01 to
0.19 points - and it sits in the most-played cell family in the chart.
`SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` names two remedies and the contract permits only those
two, so shipping it with a note is not on the list. Which cells count as violations at all is
decision 10, and this item's answer applies to whatever that rule names.

In poker English: folding 44 more than a quarter of the time from the lojack while always opening
22 is not a strategy, it is a cell the solver had not finished. Either run the solve longer before
converting - it took 54 seconds for 300 iterations, so this is minutes rather than a project - or
write 44 up to match its neighbours and record that a human did it.

The first keeps the artifact purely derived, which is the property that lets anyone regenerate and
diff it. The second is faster and is a hand edit to a derived file, which this repo has spent
three phases learning to distrust.

Options: re-solve-to-a-tighter-gap | smooth-the-pair-ladder
Answer: []

## 3. What is done about the realization model underpricing position

Reversibility: frozen-into-data

`REALIZATION-MODEL-UNDERPRICES-POSITION`. GTOpen prices postflop with a scalar realization weight
rather than a solve, and the effect is measured: the big blind folds 50.98 percent facing a 2.5bb
small-blind open from a 54 percent range, closing the action with 1.5 to win 3.5 and needing 30
percent in position. That is far tighter than a real postflop solve gives, and the button opens
40.26 percent against a *raked* GTO Wizard reference's 40.56 - removing rake should not make the
widest-opening non-blind position tighter.

Why it is on this list rather than deferred: the big blind holds 58 of the 89 human call
disagreements, and this phase's closing measurement is about exactly those calls. If the residual
gap is read as price or as a real defect while this is unnamed, the conclusion is wrong and
nothing in the repo can catch it.

The entry names three dispositions. Accept it and write it onto the committed artifact's source
card, so every later reader of the chart meets it. Correct it with a stated adjustment, which
means a human-authored number in a derived file. Or solve elsewhere, which is a new solve and a
new human verdict, so it is phase-10-shaped work rather than this phase's.

Options: accept-and-record-on-the-source-card | correct-with-a-stated-adjustment | solve-elsewhere
Answer: []

## 4. Whether the artifact declares its blind structure

Reversibility: frozen-into-data

`BLIND-STRUCTURE-VARIANTS` and `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` both want
a declared blind structure on the artifact, and this is the one phase that rewrites the artifact.
Phase 13 built the detection half - a straddled or anted table is now seen and refused - and
found it could not check a table's blind ratio against the solved one because the artifact
records no ratio at all. That was phase 13's largest single finding.

In poker English: the chart was solved at 0.5/1. Nothing stops it being asked about a 1/3 game,
where the same hand at the same stack depth is a different decision, and nothing anywhere would
notice.

Adding the field is cheap now and expensive later, because a schema version bump re-validates
every committed artifact. Declining it means the two entries stay open through phase 15 and 16.

Options: declare-blind-structure-now | defer-to-a-later-schema-change
Answer: []

## 5. Whether committed cells carry arriving reach

Reversibility: frozen-into-data

`CHART-CELLS-SHOULD-CARRY-ARRIVING-REACH`. If decision 1 rules on reach, the reach numbers exist
during conversion and are then thrown away. Keeping them per cell would let a later reader tell a
cell the solver trained from one it barely visited - which is the same information a refusal
carries and the chart currently cannot express - and would let the selection rule live in the
artifact rather than being applied once and forgotten.

The cost is bytes, in a phase whose binding constraint is bytes, and a schema field that every
later artifact must then carry.

The contract permits two outcomes only: reach carried per cell, or a stated reason the schema
cannot carry it with the entry filed forward. A per-spot summary is not on that menu, because a
spot-level number cannot tell one cell from another, which is the whole ask.

Options: carry-reach-per-cell | do-not-carry-reach-and-file-the-reason
Answer: []

## 6. How the export's four action kinds become the schema's four

Reversibility: frozen-into-data

An earlier draft of this item answered itself, on the reading that the collapse rule was already
ruled and only being recorded. The stage-2 reviewer showed that is wrong, and the measurement
above is why: the old ruling was made against a source where the case that matters never arose.

The rule as it stands. `PREFLOP_ACTIONS` in the artifact schema is `fold, check, call, raise` and
forbids repeating an action, so `raise` and `jam` cannot both survive as distinct entries.
`scripts/convert_preflop_export.py` collapses them - at the spot hero is deciding, an all-in offer
and a named raise are both `raise` and their weights add, because the artifact holds what hero
does rather than at what price - and the size goes to the sizing table, where the strategy reads
it. `raise_size_bb` deliberately skips the all-in when taking that size, and `build_sizings`
writes an entry only when a size comes back, with the note that a spot absent there has no size
and the strategy refuses rather than inventing one.

The GTO Wizard source has zero spots offering an all-in and no named raise. **This export has
4,257.** Import the rule unchanged and those 4,257 spots carry a `raise` weight the sizing table
cannot price, so the chart says raise and cannot say how much.

The question, in one sentence and with no code in it: at a spot where the solver's only aggressive
option is shoving all in, should the chart record that as a raise priced at hero's whole stack,
record it as a raise with no price and let the strategy refuse when asked how much, or leave the
spot out of the chart entirely?

Options: price-the-jam-at-the-stack | commit-sizeless-and-refuse-on-price | exclude-jam-only-spots
Answer: []

## 7. Where the old-versus-new comparison reads the retired chart from

Reversibility: runtime-reversible

The contract requires the report to say how often the derived chart and the retired one disagree
on the same corpus decision, and separately requires the retired chart deleted from the tree. So
the comparison needs it from somewhere.

Default: **read it out of git history at a pinned commit**, named in the report. Nothing is
committed twice, the pin makes the comparison reproducible, and a reader can fetch the same bytes.

Rejected: keeping a copy under `data/artifacts/preflop/` in a subdirectory the importer's
non-recursive glob does not reach. It works, and it is exactly the arrangement that makes a
reader ask which chart the bot plays - which is the confusion this phase exists to end. Also
rejected: a test fixture copy, which is 264 KB of duplicated derived data under `tests/`.

## 8. What the exclusion and inexpressibility reasons are called

Reversibility: runtime-reversible

The contract requires every export node to land in exactly one of committed, excluded by the
selection rule, or inexpressible in the vocabulary, with both reasons drawn from a closed
vocabulary the tests enumerate. The point of the closure is that a node the converter merely
failed to handle cannot be filed as a property of the grammar.

Default: the reason codes live beside the existing refusal codes in
`solver_artifacts/lookup.py`, in the same `namespace:reason` shape the chart lookup already uses,
so a reader meets one vocabulary rather than two. Measured today, the vocabulary needs no
inexpressibility code at all - all 38,828 nodes derive a key - so the census will publish that
bucket at zero, which is a result rather than an omission.

## 9. What the closing prediction's magnitude band is

Reversibility: frozen-into-data

An earlier draft filed this `runtime-reversible` on the argument that it is a number in a report
rather than in the artifact, and then conceded in the next clause that writing it afterwards is
not reversible. Both cannot be true. Under `runtime-reversible` the loop proceeds on the recorded
default, so the same agent that runs and interprets the closing measurement would also set the bar
it is graded against, and `auto_advance: false` surfaces that only at stage 11, after the number
is known. The pre-registration exists to stop exactly that.

The band is stated in one unit, points of big-blind call agreement, because the earlier draft
offered two on different scales and a pre-registration that reads two ways is worse than none.

The proposal, per opener, against the measured defence deltas: big-blind call agreement moves in
the same direction as that opener's defence delta, by between one quarter and one times the delta
in points. So versus the lojack, between +1.16 and +4.65 points; the hijack +0.93 to +3.72; the
cutoff +0.66 to +2.64; the small blind +1.54 to +6.14; and the button between -0.67 and -2.67,
which is a predicted *worsening*.

The question for a human: is that band wide enough to be honest and narrow enough to be worth
writing? A quarter-to-one band cannot be missed low if the effect is real, and it can be missed
high, which is the direction that would say something. The alternative is a band that only claims
a sign, which the contract already argues cannot settle anything, since any nonzero movement
confirms it while the 39-point call gap stands.

Options: quarter-to-one-times-the-delta | half-to-twice-the-delta | sign-only
Answer: []

## 10. What counts as a monotonicity violation, and at what tolerance

Reversibility: frozen-into-data

The contract requires the committed cells monotone under two relations, and decision 2 rules what
happens to the cells that violate them. Neither is implementable until this is settled, and the
answer decides which cells get hand-written under decision 2's second option.

Two axes, and the measured counts show both matter. Whether a pair is compared only to its
immediate neighbour or to every lower pair: adjacent gives 11 shallow and 43 deep violations at
zero tolerance, all-pairs gives 34 and 73. And what gap counts: at zero tolerance ten of the
eleven shallow adjacent violations are noise at 0.01 to 0.19 points, and at a one-point tolerance
exactly one survives, the real 44-versus-33 pair.

In poker English: a solver that plays 44 at 99.91 percent and 33 at 99.99 percent has not made a
mistake, it has not finished converging on two cells it plays almost always. A rule with no
tolerance calls that a leak and sends ten cells to be hand-edited. A rule with too much tolerance
stops seeing the real one at 27 points.

The choice is frozen because a stage-4 test asserts it over the committed artifact and stage 5
freezes that test, so changing it later is a task rather than an edit.

Options: adjacent-at-1-point | adjacent-at-half-a-point | adjacent-at-zero | all-pairs-at-1-point
Answer: []

## 11. Which rate the closing conclusion is read off

Reversibility: runtime-reversible

The contract requires both the agreement rate and the stricter sampled-action match published for
both populations. It does not say which one the conclusion about the calling gap is read off, and
`AGREEMENT-RATE-NEEDS-A-DENOMINATOR-POLICY` says the repo has no rule for that either - nonzero-
weight agreement is monotone in how mixed the chart is, so a noisier chart scores higher.

Default: the conclusion is read off the **agreement rate**, because that is the rate every prior
figure in this comparison was published as and switching denominators mid-series would make the
before-and-after meaningless. The sampled-action match is published beside it and any divergence
between the two directions is called out, since a chart that got more mixed would move them apart.

Reversible because it is which of two published numbers a paragraph cites. The backlog entry asks
for the general rule, which is not this phase's to write.

## 12. How the limped-decision-point count is defined

Reversibility: runtime-reversible

`CHART-CANNOT-ANSWER-A-LIMPED-POT` quotes the accepted cost of the limps ruling as twelve
inventory rows and 21 of 3,048 decision points, and no file states the rule that produced those.
Recounting under the obvious definition - the first recorded action in the spot key is a call -
gives 15 rows and 22 points.

Default: this phase publishes its own count under the stated definition and does not attempt to
reproduce 12 and 21. Filed as `LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION`, because the older
figure appears in three committed documents and correcting them is not this phase's scope.

## 13. Whether the sizing table stays one file

Reversibility: runtime-reversible

The sizing table is 1,974 bytes for 36 spots today and scales with whatever decision 1 selects.
Default: one file, matching the artifact, because it is small and because splitting it would need
its own composition rule where the chart library already has one for artifacts. Revisit only if
the selected spot count makes it large enough to matter, which at the measured rate it will not.
