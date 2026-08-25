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

## What the rulings changed about each other

Recorded by the coordinator after stage 3, because four of the eight answers interact and a reader
taking any single item's numbers forward would take a stale one.

**Decision 1's threshold survives; its spot count and size do not.** The rule is "keep a node when
at least 2 percent of hero's range arrives there", and that is a predicate over an export node, so
it is unaffected by anything else here. The 5,626 spots and 10.3 MiB attached to it were measured
against the *current* export at 1,925 bytes per spot, and three later rulings move both. Decision
2 re-solves, which changes the reach values the count was computed from. Decision 5 adds a reach
field to every cell. Decision 4 adds a blind structure to the artifact, which is a fixed cost
rather than a per-spot one. Decision 6 adds a sizing-table entry for each of the 4,257 jam-only
spots the filter keeps, at roughly 55 bytes each measured off the current sizing file.

So **10.3 MiB is a floor rather than an estimate**, and stage 6 measures the real figure before
committing anything. If the 2 percent floor no longer fits under 15.9 MiB once those four are in,
the contract's own rule applies: exceeding the cap is a halt and a decision, and the decision is
Taylor's rather than a quiet re-tightening of the floor to whatever fits. That is decision 1's
ruled threshold being protected from arithmetic, which is why it was ruled as a predicate.

**Decision 2 may make decision 10 a no-op, and that is the intended outcome.** The monotonicity
rule at one point, adjacent ranks, names exactly one violation in the shallow tree today. The
re-solve is expected to remove it. If it does, the rule's job at stage 6 is to prove the chart is
clean rather than to send any cell to decision 2's second branch, and decision 2's ruling is then
satisfied by the re-solve alone.

**Decision 2 also unsettles the numbers every other measured section here rests on.** The reach
table, the 42-versus-1 violation counts, the eleven aggregate frequencies, and the five
blind-defence deltas decision 9's band is built from were all measured against the 300-iteration
export. The band is ruled as a multiple of the deltas rather than as absolute points precisely so
that it survives - stage 6 recomputes the deltas from the new export and the band follows. Every
other figure in this file is a measurement of the old export and stage 6 restates it against the
new one.

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

Options: reach-at-2pct | reach-at-5pct | depth-at-8 | reach-at-2pct-with-a-5-action-floor |
heads-up-only
Answer: [heads-up-only]

**Ruled by Taylor, 2026-08-23: reach at 2 percent.** 5,626 spots and 10.3 MiB against a 15.9 MiB
budget. He took the option that keeps the most coverage while leaving headroom, over the stricter
5 percent floor and over the depth proxy. The cost he accepted: the next solve into this directory
has 5.6 MiB rather than 9.8, and `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` is where that comes
due.

**Superseded by Taylor on 2026-08-24: keep a node only when at most one opponent has voluntarily
put money in beyond the blinds. 110 spots.** The 2026-08-23 ruling was made on a question about
bytes. Stage 4's independent verification changed the question to one about whether the ranges are
right, and the answer is that most of them are not: GTOpen prices a multiway pot as the product of
hero's pairwise equities - `crates/solver/src/preflop/mod.rs` line 12 says so - which understates
true three-way equity by 10.5 points and by 14 on the suited connectors whose entire value is
multiway. The big blind therefore defends 7.44 percent closing at 4.3 to 1 three-handed where
correct pricing gives 65.6, and **98.0 percent of the 5,626 spots the reach floor selected have two
or more opponents already invested**. The predicate that keeps only what the model prices exactly
selects 110 nodes of the 38,828.

**How the four options above now stand.** All four are reach or depth rules over the whole tree,
so all four select mostly multiway nodes and none of them addresses this. The reach floor is not
retuned but retired: measured over the export, every one of the 110 heads-up nodes also clears the
2 percent floor, so conjoining them changes nothing and the floor now selects nothing the new
predicate does not. Recorded because the two rules were nearly confused: 110 is the heads-up count
over the *whole* export, not the heads-up subset of the 5,626, and the earlier note phrasing "110
of 5,626" reads as the second.

**What the 110 are**, measured from the committed export by a walk that reproduces the recorded
5,626 exactly under the recorded floor definition, which is the unweighted mean of `reach_bp` over
the 169 classes rather than a combo-weighted one: 5 opens and 30, 30, 30 and 15 spots facing one,
two, three and four prior aggressive actions; 16/17/18/19/20/20 across LJ, HJ, CO, BTN, SB and BB;
35 at full reach; and four action menus - 60 fold/call, 30 fold/call/raise/jam, 15 fold/call/jam
and 5 fold/raise/jam.

**The cost Taylor accepted.** The bot refuses the multiway decisions rather than answering them
from a model that cannot see multiway equity. Those are 8.3 percent of the corpus's 3,054 preflop
decision points, and they leave phase 08's denominator with them; `CHART-COVERAGE-EXPANSION` and
`CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` are settled against 110 spots rather than 5,626, and the
cold-call spots the retired chart already refuses stay refused. What it does not cost is
optionality: the spot key encodes the action sequence, so a multiway family arrives later as new
keys with no re-keying, once `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` is fixed in GTOpen.

**Depth was not cut further.** The recommendation put to him was heads-up with a shallow depth
clause; he ruled "the 110" as counted, which is the full heads-up set including the three-bet,
four-bet and five-bet continuations. The consequence is recorded rather than hidden: this phase's
own measurement flags the published four-bet node as unconverged - JJ folded 97 percent, TT and 99
and KJs outright - and it ships, published in the report as a measurement beside the cells it
describes.

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

Options: re-solve-to-a-tighter-gap | smooth-the-pair-ladder | ship-as-solved
Answer: [re-solve-to-a-tighter-gap]

**Ruled by Taylor, 2026-08-24: re-solve at a tighter gap and let the re-solve decide.** He first
put back the hypothesis that 72.81 percent might be the solver's real answer rather than an
unfinished cell, which is the right question to ask and is why this went round twice.

The argument that it is not, stated because the ruling rests on it. Among pairs in an open-fold
decision 44 dominates 33 and 22 outright - higher set, better equity against overcards, more
overpair boards - and there is no blocker effect at this magnitude. If opening 33 is profitable
enough to do always then opening 44 is more profitable, so it cannot be opened less. And the
committed solve stopped at **300 iterations against a 2,000 cap**, because the target it was given
is a gap summed over the whole tree; `docs/GTOPEN_SOLVER_NOTES.md` says of a 300-iteration run
that marginal hands converge last, and 44 from the lojack is exactly a marginal hand.

What makes this the ruling rather than the argument winning: the re-solve settles it either way.
If 44 moves to roughly 100 percent it was convergence and the chart is clean. If it holds near
72.81 after 2,000 iterations then the hypothesis was right, it is the solver's considered answer,
and it ships as solved with that recorded. Nobody hand-edits a cell in either branch and the
artifact stays purely derived, which was the cost the smoothing option asked for.

**Re-ruled by Taylor on 2026-08-24, onto this item's own third option.** Stage 4 measured the
monotonicity rule over the whole selected set rather than over the eleven grids the export
publishes, and found 1,938 violating nodes of 5,626 - 36 of them among the 351 where hero's whole
range arrives, so not a deep-tail effect. Taylor read the grids in GTOpen and ruled that the
solver's split among near-indifferent hands is its considered answer: at the small blind facing a
button open it plays 22 at 99.94 percent, 33 at 16.20, 44 at 0.07 and 55 at 99.83, and when hands
are indifferent the EV of any split between them is the same, so the individual cells carry no
information and only the aggregate does. That is `ship-as-solved`, which this item already listed.

The argument recorded above for re-solving is not withdrawn and was not wrong on its own terms -
44 does dominate 33 in an open-fold decision. What it missed is that dominance constrains EV, not
frequency, and a solver at indifference is free to put the frequency anywhere. The re-solve is
therefore permitted and no longer required; the contract's re-solve criteria apply only if one is
run. Decision 10 carries the consequence for what is gated.

**The consequence a re-solve would carry, if one is run.** A re-solve produces a *new export*, and
phase 10's human verdict, its determinism proof and its byte-identical claim all attach to the
300-iteration one. So the phase owes: the same determinism check the old export passed, the two
orderings re-asserted, and a published diff of what moved between the two solves. If anything
beyond the marginal cells moved, that is a human read of the grids rather than a number in a
report. The contract's Scope is amended in the same task to permit a re-solve at the ruled config
and nothing else - not a second opening price, not limps, not another depth.

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
Answer: [accept-and-record-on-the-source-card]

**Ruled by Taylor, 2026-08-23: accept it and record it on the source card.** The ranges ship as
solved and the artifact's source card states the bias in poker terms with the measurement behind
it, so every later reader of the chart meets it. The closing measurement then names it as a third
candidate explanation it cannot separate, which is what stops a residual gap being read as price
or as a defect. Rejected: a stated adjustment, which puts a human-authored number inside a file
whose whole value is that it reproduces from the export; and solving elsewhere, which is a new
capture and a new human verdict.

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
Answer: [declare-blind-structure-now]

**Ruled by Taylor, 2026-08-24: declare it now.** The artifact carries the blind structure it was
solved at, so a lookup can refuse a game whose blinds are not in that ratio instead of answering
it silently. Closes `BLIND-STRUCTURE-VARIANTS` and
`BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE`, the second of which was phase 13's
largest single finding. Ruled together with decision 5, which shares the version bump.

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
Answer: [carry-reach-per-cell]

**Ruled by Taylor, 2026-08-24: carry reach per cell.** Ruled together with decision 4, since both
land on the same `ARTIFACT_SCHEMA_VERSION` bump and the marginal cost of the second is bytes only.
The selection rule from decision 1 then lives in the artifact rather than being applied once at
conversion and forgotten, and a later reader can tell a trained cell from one the solver barely
visited. Closes `CHART-CELLS-SHOULD-CARRY-ARRIVING-REACH`.

The bytes are not free and the phase must measure them against the 15.9 MiB budget rather than
assume: decision 1's 10.3 MiB estimate was computed without a reach field. If the two together
breach the cap, that is a halt and a return to this list, not a silent re-tightening of the reach
floor.

**Amended 2026-08-24, because decision 1's supersession removed both halves of the rationale above
and the ruling survives on neither of them.** Two sentences are now false. "The selection rule from
decision 1 then lives in the artifact rather than being applied once at conversion and forgotten"
does not hold: the selection rule is no longer a reach threshold, so a reach field does not encode
it - the predicate is "at most one opponent voluntarily invested", which is a property of the spot
key rather than of a per-cell number. And the byte paragraph is moot: there is no 15.9 MiB budget in
play at 110 spots and no reach floor left to re-tighten.

**The ruling stands, on the half that survives, and the half is smaller than it was.** A reader can
still tell a trained cell from one the solver barely visited, and that is what
`CHART-CELLS-SHOULD-CARRY-ARRIVING-REACH` asked for. But 35 of the 110 are at full reach and none is
near the retired floor, so on the committed set the field distinguishes less than it was ruled to.
The reason to keep it is prospective rather than present: the multiway family that returns once
GTOpen can price it is deep, rare and exactly where the distinction bites, and adding the field then
is a second `ARTIFACT_SCHEMA_VERSION` bump and a re-derivation of everything built on the first.

This item is `frozen-into-data` and the amendment does not reverse it, so it proceeds. Taylor is
told the rationale narrowed rather than asked to re-rule; dropping the field remains his call, and
its cost is a schema bump later instead of now.

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
Answer: [price-the-jam-at-the-stack]

**Ruled by Taylor, 2026-08-23: price the jam at the stack.** A shove is recorded as a raise to
hero's whole stack, so the chart answers both what to do and how much, and the size is true rather
than absent. `build_sizings` gains an entry for every such spot. Rejected: committing sizeless,
which would train "raise, no idea how much"; and excluding them, which drops real spots the reach
filter would otherwise keep.

**Extended by Taylor on 2026-08-24, after stage 4 measured the case this item never asked about.**
The question above is about the 4,257 nodes offering a jam and *no* named raise. It says nothing
about the nodes offering **both**, and the inherited collapse rule silently takes the named raise
there. Measured over the committed selection: 313 spots offer both, and over hero's arriving range
**60.6 percent of his aggressive volume at them is the shove** - the majority at 177, at least 80
percent at 136, and 100 percent at 35, where the named raise to 22.5 carries no weight at all. So
one price per spot teaches a 22.5bb raise on 136 decisions the solve plays as a stack-off.

**The ruling: the sizing table holds every size a spot offers, with the weight hero gives each.**
Taylor's reason, in his words, is that multiple preflop sizings are better play in some spots
anyway, so the chart should be able to hold them. No re-solve is required and none is implied: the
tree already offers both prices at those 313 spots, and this is the artifact learning to record
what was already solved. The spot key is untouched, because a key states what hero *faces* rather
than what hero does - which is what keeps this out of `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`.

Also corrected here, because this item's original wording asserted it: "a spot absent from the
sizing table has no size stays true because none of these will be absent" is false. **3,865 of the
5,626 committed spots offer hero only fold and call**, so they carry no raise weight and correctly
have no entry. The invariant is two-directional instead - every spot with a positive raise weight
has an entry, and every spot without an entry has no raise weight - and both sets are non-empty.

**Restated on 2026-08-24, because decision 1's supersession moved the measurement under this
ruling and a premise that evaporated must not be left standing.** The 60.6 percent figure is a
property of the multiway spots. Re-measured over the 110 the cutover now commits: **35 spots offer
both a named raise and a jam, and the shove is 5.0 percent of hero's reach-weighted aggressive
volume at them, the majority at 2 and all of it at none.** So the sentence "one price per spot
teaches a 22.5bb raise on 136 decisions the solve plays as a stack-off" is false of what this phase
ships, and the AA-jams-100bb behaviour that produced it was itself a tree artifact of the
cold-called nodes, where the only non-jam raise available prices the whole field in.

**The ruling stands on narrower ground and the ground is stated.** A spot offering two prices is
described by two prices; one price per spot silently drops that 5 percent; the schema is strictly
more expressive and costs bytes the phase now has in abundance; and the multiway family that
returns later is where the 60.6 percent lived, so the schema will be needed then. This is a
restatement rather than a reopening - Taylor is told the premise moved, and reverting to one price
per spot remains his call. The two-directional invariant below is unaffected except in its numbers:
**60 of the 110** committed spots offer hero only fold and call.

What stays out of scope, and is filed rather than done: solving *additional* 3-bet, 4-bet and
5-bet sizes so the tree offers a real choice rather than a raise-or-shove pair. Measured on this
machine through GTOpen's own estimator, a second re-raise multiplier takes the tree from 38,828
action nodes and 112 MB to **260,136 nodes and 754 MB**, a third to 606,378 and 1,758 MB, and two
sizes at `max_raises: 5` to 2,884 MB, which the solver refuses outright. The solver is not the
binding constraint; the 20 MB artifact cap downstream is. That is phase-10-shaped work with its
own human verdict on the ranges, and it is what `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT`
becomes once the schema half lands.

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

**Proceeded on its default and extended, 2026-08-24, reported rather than blocked** because this
item is `runtime-reversible`. Decision 1's supersession makes the exclusion bucket 38,718 nodes, so
one code for all of them carries no information. The vocabulary distinguishes **two** exclusion
reasons: a node outside the selection rule, and a node the source misprices. Every multiway node is
both, and the second is the fact a later phase needs to find them by - filing them under one code
loses which nodes come back when GTOpen can price multiway. Taylor was told this proceeds on the
default rather than asked to rule it.

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
Answer: [quarter-to-one-times-the-delta]

**Ruled by Taylor, 2026-08-24: a quarter to one times the delta, per opener.** So big-blind call
agreement is predicted to move by +1.16 to +4.65 points against the lojack, +0.93 to +3.72 against
the hijack, +0.66 to +2.64 against the cutoff, +1.54 to +6.14 against the small blind, and to
*worsen* by 0.67 to 2.67 against the button. Recorded here before the measurement runs, which is
the whole point of the item. A miss in either direction is a result and the report states which.

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
Answer: [adjacent-at-1-point]

**Ruled by Taylor, 2026-08-24: adjacent ranks, one percentage point.** A pair is compared to the
next one down and a gap over one point is a violation. That catches the real 44-versus-33 pair at
27 points and ignores the ten cells sitting at gaps of 0.01 to 0.19 points, which are two cells a
solver plays almost always rather than a leak. The suited-versus-offsuit relation takes the same
tolerance.

The interaction with decision 2 is now benign: the re-solve is expected to remove the one
violation this rule names, so the rule's job at stage 6 is to prove that rather than to send cells
to be rewritten.

**Re-ruled by Taylor on 2026-08-24: the relations are measured per cell but gated on aggregates.**
The sentence above is the one this phase got most wrong, and it is worth saying why rather than
just replacing it. "The one violation this rule names" was never a property of the shallow tree.
It was a property of the eleven range grids the export publishes, which is what phase 10's human
verdict read and what every later document quoted forward without a method. Measured over the
whole selected set at this item's own ruled tolerance: **1,938 violating nodes of 5,626, and 36 of
the 351 nodes where hero's whole range arrives.** The families nobody had looked at - cold calls
and multiway pots - are where it concentrates.

Taylor read those grids and ruled the splits correct: among near-indifferent hands a solver may
put the frequency anywhere, because every split has the same EV, so a per-cell dominance gate
rejects correct play. The tolerance and the adjacency choice above are unchanged and still
describe what gets *measured*; what changes is that the per-cell result is published for a reader
rather than gating the artifact.

What gates instead is the same dominance taken over **groups**, where indifference cancels: the
combo-weighted play frequency of each pair band and each suited row, over hero's arriving range,
must be at least that of the band or row below. That is meant to keep a real check - a transposed
hand index or a mis-assigned actor still failing it - without asserting a per-cell order the solve
does not owe.

**Corrected 2026-08-24: the sentence above claims a property that was then measured and is false.**
The independent walk in `stage-04-cold-call-verification.md` ran every aggregate form over the 5,626
at this item's ruled tolerance. The suited-versus-offsuit relation flagged **2,007 nodes as solved
against 818 with suited and offsuit transposed**, so the gate scores the *wrong* index mapping as
the better one - it does not catch a transposed index, it rewards one, which is worse than having no
gate for that defect at all. Only the two-band pair aggregate came out clean, and only over the 351
full-reach nodes. So no aggregate form of this rule had been shown to pass over what the phase was
going to commit.

**What that means now that decision 1 commits the 110 instead.** The measurement above is over the
5,626 and does not transfer: the contract requires the aggregate gate re-measured over the 110
before it is frozen, and the phase halts rather than freeze a gate it has not seen pass. Until that
measurement exists, this item's group gate is a proposal rather than a proven check, and the
transposed-index claim is withdrawn rather than restated - whether it holds on the 110 is one of the
things stage 4 now owes.

Two things this ruling does not settle, recorded so nobody reads them as settled. It was given
against the pair ladder, and 6,990 of the violations are suited-versus-offsuit, where the offsuit
twin is played *more* systematically across whole rows rather than in isolated cells - the same
indifference argument covers it, but nobody has read those grids. And it makes
`NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` sharper, because one more property
moves from gated to printed.

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
