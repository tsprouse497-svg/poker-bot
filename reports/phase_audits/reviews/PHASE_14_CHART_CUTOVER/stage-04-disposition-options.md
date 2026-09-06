# Phase 14 stage 4: dispositions for the multiway pricing defect

Written 2026-08-24. The halt in `verification/loop_runs/14.yml` and the independent walk in
`stage-04-cold-call-verification.md` settled the facts; this note only lays out what the phase can
do about them. **The answer is Taylor's ruling. Nothing here is a default and no option is
pre-selected**, because the defect is in the extraction source rather than in this repo, and the
loop has no rule that says which way a phase turns when the thing it is converting is wrong.

## What is settled and is not reopened below

- GTOpen prices a multiway pot as the **product of hero's pairwise equities**, stated in
  `crates/solver/src/preflop/mod.rs` line 12, with the calibrated realization fit gated to
  heads-up at line 1127. The product understates true three-way equity by 10.5 points on average
  over the 169 classes, worst by 14 on the suited connectors whose entire value is multiway, and
  by 0.15 on AA.
- The consequence, reproduced independently to the basis point: the big blind defends **7.44
  percent** closing for 1.5 into 6.5 at 4.3 to 1 with two players in. Priced as a product the
  predicted figure is 7.39. Priced correctly the same node defends 65.6 percent.
- **No re-solve and no size menu touches it.** It is the core pricing, not a parameter, not a
  convergence question, and not the size menu. `realization` picks among raw, static and
  calibrated and all three multiply an equity already computed as a product.
- **Heads-up output is unaffected**, because the approximation is exact there by construction. The
  five opens and five big-blind defence frequencies check out against the GTO Wizard reference and
  every delta lands inside decision 9's predicted band.
- **98.0 percent of the 5,626 spots decision 1 selected have two or more opponents already
  invested.** In the 499-hand corpus, 8.3 percent of the 3,054 preflop decision points do.
- `reach_bp` measures the actor's own range survival, not how often a line occurs, so decision 1's
  floor never dropped a node for being rare: 5,435 of the 5,626 sit on lines occurring less than
  once in 10,000 hands, and the 351 at full reach are exactly the nodes where hero has not yet
  acted.
- Adding multiway spots in a later phase is **additive**: the spot key already encodes the action
  sequence, so no key is re-cut and `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL` is not paid twice.
  Excluding multiway now forecloses nothing.

## The question in one sentence

Decision 1 selected 5,626 spots on a reach floor; 98 percent of them are priced by a model that
cannot see multiway equity - so what does phase 14 commit?

## Options

### A. Scope the cutover to heads-up spots

Predicate: keep a node only when at most one opponent has money in beyond the blinds. **110
spots.** Everything else is a lookup miss refused with a code, which is the behaviour the contract
already prescribes for an unselected spot.

- Every committed cell is priced exactly, and the repo's only external oracle agrees with that
  half.
- The bot refuses roughly 8 percent of preflop decisions instead of answering them wrongly, and
  phase 08's comparison loses those from its denominator.
- Decision 1's reach floor becomes moot: 110 spots do not strain a 20 MB cap, so the rule that
  exists to fit under it has nothing left to do, and `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`
  changes character rather than coming due.
- It does not buy depth. 35 of the 110 are at full reach and the rest are three-bet and four-bet
  continuations, and this phase's own plan already flags the published four-bet node as
  unconverged - JJ folded 97 percent, TT and 99 and KJs outright. Heads-up is trustworthy shallow,
  not at every depth. See sub-question 1.

### B. Exclude the cold-call family only

Predicate: drop the 26 measured spots, keep the rest.

- Cheapest edit and the least defensible. The mechanism is generic to every multiway terminal, so
  this commits roughly 5,490 nodes carrying the same defect with none of them measured. It removes
  the evidence rather than the defect.

### C. Replace the reach floor with an arrival-probability floor

Predicate: keep a node when the line reaches it more often than some ruled rate - the product of
the reach-weighted action frequencies along the path, rather than the actor's own survival.

- It fixes the separate defect the walk found, which is real: the current floor cannot express
  rarity at all.
- **But the arrival probabilities are computed from the mispriced solve.** Cold-calling is itself
  priced by the product approximation, so the solve under-produces multiway lines: node
  `[1,1,0,0,0]` arrives on 2.28 hands in 10,000 where the corpus meets a two-invested decision 8.3
  percent of the time. A floor read off those numbers prunes multiway for the wrong reason and
  inherits the defect as its justification.
- It lands near option A in practice while being harder to state and resting on numbers the
  finding says not to trust.

### D. Re-solve with a per-seat squeeze menu

`raise_mults_by_seat` gives the big blind `[3.0, 4.5]` while everyone else stays pinned, at a
fraction of the global blow-up the phase already priced at 38,828 to 260,136 nodes.

- Buys the AA-jams-100bb artifact, which is real: with only 7.5 available over a cold-called open
  the jam is the better of the two options in the tree, and the chart would teach a 100bb shove
  where the right action is a raise to about 11 or 12.
- **The 92.6 percent fold survives it untouched.** Worth doing whenever a re-solve happens for
  another reason; not worth one on its own, and not an answer to this question.

### E. Ship all 5,626 and record the defect

- Consistent with decision 2's ship-as-solved precedent and with the source card carrying
  `REALIZATION-MODEL-UNDERPRICES-POSITION` already.
- The cost is what the bot teaches: a 92.6 percent fold closing at 4.3 to 1 three-handed, across
  26 spots that are among the most common decisions in real six-max play, plus the same mispricing
  unmeasured across 98 percent of what is committed. A stated caveat on a source card does not
  reach the human at the table, and the contract's own principle is that refusing a spot the bot
  has no trained ranges for is the point.

### F. File the engine work, whatever else is ruled

Already filed as `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`, `phase: v2`, with the scope stated
so nobody plans it as a config edit: true multiway equity at `KIND_POT_SHARE` terminals inside
GTOpen, benchmarked and re-validated, and the calibrated fit cannot be extended to cover it
because the postflop engine behind it is heads-up only. This is a companion to A, C or E rather
than an alternative to them.

### G. Park phase 14 until the engine is fixed

- The bot keeps playing the retired 36-spot chart derived from a raked GTO Wizard export - the
  thing this phase exists to delete - and every phase after 14 keeps measuring against it. The
  known-wrong artifact stays in place to avoid committing a partly-wrong one.

## Sub-questions, live only under some options

1. **Depth, under A or C.** Does the retained set keep the three-bet and four-bet continuations,
   or stop at a ruled depth? The four-bet node is unconverged on this phase's own measurement, and
   110 spots is small enough that the answer visibly changes what the bot covers.
2. **Whether the exclusion is one reason code or two**, under A, B or C. Decision 8 put the codes
   beside the refusal codes in `solver_artifacts/lookup.py` and predicted the inexpressibility
   bucket at zero. "Excluded by the selection rule" and "excluded because the source misprices it"
   are different facts about a node and a reader will want them apart.
3. **Decision 6's sizing table**, under A or C. Its ruling rests on 313 committed spots offering
   both a named raise and a jam, 60.6 percent of aggressive volume being the shove. That
   measurement is over the 5,626 and has to be re-taken over whatever set is retained; the ruling
   may survive on a different number or may lose its premise.
4. **Decision 5's reach field**, under A. With every retained cell at or near full reach, a
   per-cell reach field may have nothing left to distinguish.

## What any answer other than E costs procedurally

Decision 1 is `frozen-into-data` and was ruled on 2026-08-23, and the contract names the ruled
predicate in its acceptance criteria. Changing it is a **`contract-update` task**, not an edit
inside this implementation stage: the decision list is amended, the contract's selection section
and several of its backlog closures are restated, and stage 4's authored tests are re-cut against
the new predicate before the freeze. The contract is also at 298 of 300 lines with
`ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` already filed, so stage 3's note is right that the
next edit is a rewrite rather than an amendment.

The closing measurement moves under A and C as well: the refusal rate rises, the retained sample
shrinks, and `CHART-COVERAGE-EXPANSION`, `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` and
`CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` are each settled against a different denominator than the
contract assumes.

## The coordinator's recommendation, which is not the ruling

**A with F**, and sub-question 1 answered shallow. It is the only option where everything the bot
plays from is priced by a model that is exact for the situation it is pricing, the external oracle
independently agrees with that half, and the multiway family returns later as new keys with no
re-keying and no re-derivation. The cost is honest and small in the shape that matters: the bot
refuses 8 percent of decisions rather than teaching a fold that is wrong by 58 points of range.

Options: A | B | C | D | E | G, with F alongside whichever is chosen
Answer: [A, with F]
Sub-question 1 (depth under A or C): [no further cut - the 110 as counted]
Sub-question 2 (one exclusion code or two): [two, on the runtime-reversible default]
Sub-question 3 (decision 6's sizing table): [kept, restated on the re-measured 5.0 percent]
Sub-question 4 (decision 5's reach field): [kept, on prospective grounds; see decision 5's amendment]

## Ruled by Taylor, 2026-08-24: A, the 110 heads-up spots

"Let's move forward with just the 110." The cutover commits only the spots where at most one
opponent has money in beyond the blinds. Everything else is a lookup miss refused with a code,
and the multiway family returns in a later phase as new keys once GTOpen can price it.

**What he accepted.** The bot refuses roughly 8 percent of preflop decisions rather than answering
them from a model that misses three-way equity by 10.5 points, and phase 08's comparison loses
those from its denominator. `CHART-COVERAGE-EXPANSION` and
`CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` are settled against 110 spots rather than 5,626, and
the cold-call spots the retired chart already refuses stay refused.

**Sub-question 1 is answered by the count.** He ruled the 110 as counted, which is the full
heads-up set including the three-bet and four-bet continuations, so no depth clause is added.
The consequence is on the record rather than in the ranges: this phase's own measurement flags
the published four-bet node as unconverged - JJ folded 97 percent, TT and 99 and KJs outright -
and it ships. The report publishes that as a measurement beside the cells it describes, which is
what decision 6 already ruled for a solver answer a human has read.

**Sub-question 2 proceeds on its default and is reported rather than blocked**, because decision 8
filed the reason vocabulary `runtime-reversible`. Two codes, not one: a node excluded because the
selection rule did not pick it and a node excluded because the source misprices it are different
facts about that node, and a later phase adding multiway needs to find the second set by name.

**What this does not change.** Decision 1's reach-at-2-percent floor is superseded rather than
retuned - the heads-up predicate selects the 110 outright and no byte cap is in play at that size,
so the rule that existed to fit under 20 MB has nothing left to do. That is the halt the contract
demanded: the predicate changed on the poker, not on the bytes.



## Ruled by Taylor, 2026-08-25: the 86, and the engine work with it

The 2026-08-24 ruling above rests on a premise the independent poker review falsified, so the
question came back with the terminal-clean measurement in hand. Four dispositions were put: ship the
110 as ruled, cut to the 86, cut to the 86 *and* schedule the engine fix so the rest returns, or park
the phase until the engine is fixed. **He took the third in full**, including its condition that the
86's real corpus coverage be measured before the ruling was written rather than inferred from a
subtraction. The 86 are the *conjunction* of the two clauses - at most one opponent invested and at
most two players live - not the subtree clause substituted for the history one, which would select
5,472 and admit every cold-called line back in.

**The measurement came first and it is 563 of 3,048 preflop decisions, 18.5 percent** - close to the
568 the subtraction predicted, and now a number rather than a bound. It also found that every
stage-4 document's denominator was six too large. Both in
`stage-04-eighty-six-coverage.md`.

**What he accepted.** The chart holds one opening range, the small blind's. The bot cannot open from
LJ, HJ, CO or BTN and refuses those decisions with a code, which is 2,232 corpus decisions the 110
would have answered - from cells where the solver flats a 2.5bb open 0.07 to 4.5 percent of the time
because flatting invites terminals it misprices. What ships whole is the blind-versus-blind skeleton,
the big blind closing against an open, and the three-bet, four-bet and five-bet continuations - the
half the poker review said it would trust.

**Correction to what was put to him, filed the same day.** This note and the contract both told him
coverage rises 36 to 86 with all 36 retired spots retained. That is the 110's version of the cost and
it does not survive the terminal-clean predicate: only **22 of the retired 36 are terminal-clean**, so
the cutover gains 64 and gives up 14, four RFI ranges among them. Measured in the addendum to
`stage-04-eighty-six-coverage.md` and carried back to him as a blocker, because the trade is larger
than the one he agreed to even though the reasoning behind the ruling is untouched. **He confirmed
the same day that it stands**, knowing the bot loses its LJ, HJ, CO and BTN opening ranges until the
engine fix lands. So the correction changes what the phase reports, not what it commits.

**The other half of the ruling is that the source gets fixed.** He did not take the plain cut. The
86 ship now *because* the missing spots have a route back:
`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` moves off the deferred v2 pile and becomes scheduled
work, and the 24 return as new keys once GTOpen can price them, with no re-keying and no
re-derivation of what this phase commits. Option F is therefore not a companion filing any more; it
is the second half of what was ruled.

**What still rides to him separately.** The two remaining stage-4 blockers are unaffected by this
choice and neither is answered here. The four-bet continuations folding JJ at 32 percent pot odds are
inside the 86, so that one is still live and still his. The small blind's 0.07-against-99.94 split on
adjacent small pairs is inside the 86 as well, and `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`
remains its filed remedy.

**Sub-questions, restated against the retained set.** Sub-question 1 is moot: the terminal-clean
predicate cuts depth by itself and there is no further clause. Sub-question 2 stands as answered -
two exclusion codes, and the second one is how a later phase finds the 24 by name. Sub-question 3
must be re-taken: decision 6 was ruled on 35 spots offering both a named raise and a jam, and over
the 86 that is 21. Sub-question 4 is settled the other way from before - with 11 of 86 at full reach
against 35 of 110, the reach field distinguishes more rather than less, so it is kept on present
grounds.

---

**Correction, 2026-08-25.** This note's corpus denominator of 3,054 preflop decision points is
wrong by six. The committed 499-hand sample holds **3,048**, confirmed against `replay_hand`'s own
`DecisionPoint` stream; 3,054 counts the six decisions of `pluribus/41b/204`, a hand the sample
excludes. The digits are left as written because this is a dated record of what was measured. No
conclusion in it moves - 2,232 of 3,048 is 73.2 percent and the multiway share is 8.3 percent under
either denominator. See `stage-04-eighty-six-coverage.md`.
