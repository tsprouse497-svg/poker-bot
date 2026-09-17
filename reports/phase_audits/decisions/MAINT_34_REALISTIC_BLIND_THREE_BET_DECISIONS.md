# MAINT-34 decisions

Every judgment call this task made, with its reversibility class. `frozen-into-data` means the
answer is committed under `data/artifacts/preflop/**` and a later task cannot revise it without
re-solving.

## 1. The multiplier is per seat, not global or a menu. `frozen-into-data`

Ruled by the coordinator before any solve, because "change one config field" has three readings and
two of them are traps. `raise_mults` is the re-raise TO-amount as a multiple of the current bet,
applied at **every** re-raise level and varied only by seat, never by depth
(`~/projects/GTOpen/crates/solver/src/preflop/mod.rs:54-55`, `mults_of` at `:97-102`).

- **Global `[5.4]`. Rejected.** The three-bet becomes 13.5 and the next rung 72.9, and `mod.rs:2219`
  clamps any raise at or above `allin_threshold * stack` to the stack. At 0.67 and 100bb that is a
  jam, so the sized four-bet stops existing everywhere and all three-bet-facing committed spots
  become fold, call or shove. Verified at the source.
- **Global menu `[3.0, 5.4]`. Rejected.** Phase 14 measured a second global multiplier at 38,828
  action nodes and 112 MB becoming 260,136 and 754 MB; extrapolated here that is roughly 94% of the
  20 MiB artifact cap, which is a halt rather than a budget.
- **`raise_mults_by_seat`, 5.4 on the two blind seats. Ruled.** Blind three-bets 13.5, in-position
  three-bets 7.5, and the button's four-bet survives sized at 40.5.

**The field goes into `RULED_CONFIG` itself, not posted beside it.** `config_errors` iterates
`RULED_CONFIG.items()` and never inspects a posted field the ruling does not name, so a config
supplied on the side is invisible to the card check, the frozen config guards and the whole gate.
Verified live: the export the route D probe produced is **refused by the loader** on this field,
which is the guard doing its job.

## 2. Zero-reach spots are excluded, not admitted. `frozen-into-data`

The re-solve produced selected nodes with no arriving hand class, because under a 13.5bb blind
three-bet the button's cold-call behind two cold-callers goes to zero. A node no hand can be at is
not a decision the bot faces, so the selection rule excludes it and the census counts it under its
own code, `derivation:no-arriving-hand-class`. `schema.py` is not relaxed to admit an empty spot.

This is deliberately **not** the case `test_chart_arrival_probability.py:424-442` rules on. That is
about zero *arrival* - a spot a hand can reach but almost never does - and requires such a spot to
keep its cells, which remains true. Zero *reach* is a different thing and nothing had produced one
before.

The clause is placed **last** in the exclusion order. Thousands of nodes deep in the four-bet family
also have no arriving class, and filed earlier this clause would swallow the depth bucket, which is
the bucket a later phase reads to find the work it is taking up. Verified: zero of the 160 would
have been exposure-refused had the clause run first, and all 160 carry exactly zero arrival, so
coverage does not move.

## 3. The iteration cap rises; the accuracy target does not. `runtime-reversible`

The first re-solve stopped at `SOLVE_ITERATION_CAP` (2,000) with an achieved gap of 0.00033389
against a declared target of 0.00016 - 2.1x the target, where the old solve converged at 1,900.

Raising the cap is **not** the move phase 10 forbids at `:147-149`. What that forbids is widening an
accuracy *target* after seeing the numbers, which buys a pass by lowering the bar. Raising an
iteration cap spends more compute to clear a bar that has not moved. The target stays at 0.00016.

Converged, route C reaches 0.00015588 at iteration **3,800**. The cap is set to **5,000** rather than
3,900 because the gap is not monotone near the target - 0.000162 at 3,615, 0.000164 at 3,720,
0.000156 at 3,800 - and a cap set at the crossing is fitted to one run's noise.

Recorded because nothing would have caught it: **no gate command compares the card's achieved gap to
the target the same card declares.** `test_solver_export.py:183` makes that comparison against a
captured fixture of a superseded solve rather than against the card.
`A-SOLVE-THAT-MISSES-ITS-DECLARED-TARGET-SHIPS-WITH-NOTHING-OBJECTING`.

## 4. The blind-versus-blind jam is accepted and filed. `frozen-into-data`

**Ruled by Taylor, 2026-09-16, on the measurement below.**

When a blind four-bets over the other blind's 13.5 it gets the 5.4 multiplier again - 72.9bb - which
clamps to a jam. So **49 of 254 three-bet-facing committed spots offer no sized four-bet**, split
SB 34 / BB 15, carrying **1.4364% of committed arrival**.

**Re-measured 2026-09-17, after decision 7.** The ruling stands and the arrival figure is exactly
unchanged, because decision 7 only ever removed zero-arrival spots. The counts are not: **34 of 135**
three-bet-facing committed spots are jam-only, split **SB 29 / BB 5**. The proportion went the wrong
way, 19.3% to 25.2%, since the spots decision 7 refused were mostly not the jam-only ones. The
figures above are what Taylor ruled on and are left as the record of that; these are what ships.

**Corrected 2026-09-17, same day, by both independent reviews agreeing separately.** This paragraph
first read 33 / SB 28 / BB 5, which is a different question's answer. The word this ruling turns on
is **offer**, and a menu is what a spot offers: counted that way it is 34 and SB 29. Counting instead
the spots where some arriving class actually *takes* the jam gives 33 and SB 28, and the one spot
between the two readings is
`t6/d100/SB/LJ:raise@2.5,HJ:call,BTN:call,SB:call,BB:raise@13.5,LJ:call`, whose menu is jam-only and
whose sizing map is empty because nothing arriving there raises. Both numbers are true of different
things and neither is wrong; what was wrong was publishing one of them under a sentence asking for
the other, in two documents, with nothing naming the reading.

This is structural for a single multiplier: a 13.5 three-bet needs `m = 5.4` and a sized four-bet
needs `13.5m < 67`, so `m < 4.96`. Both cannot hold.

**The coordinator's own ExecPlan asserted the opposite** - that the four-bet "survives as a sized
raise at 40.5, under the 67 clamp, verified" - without qualification. That verification covered the
button four-betting over a blind and was generalised to a case it did not cover. The solve lane
caught it. The plan is corrected rather than quietly left.

**Route D, a two-size blind menu `[3.0, 5.4]`, was measured rather than argued about, and loses.**

| | route C | route D |
| --- | --- | --- |
| jam-only three-bet-facing committed spots | 49 | **0** |
| exported nodes | 30,609 | 62,107 |
| `data/artifacts` total | 6.46 MB, 30.8% of cap | 9.30 MB, 44.3% of cap |
| iterations to the 0.00016 target | **3,800, reached** | **20,000, not reached** (0.00018780) |
| big blind's three-betting on the 7.5 size | n/a | **0.00%** |

It fixes the jam completely and buys nothing else. The solver, handed both sizes, **declines the
small one entirely** - 0.00 combos at the headline spot, verified by the coordinator against the
probe export, and a mean of 0.04 points against 8.25 across all fifteen committed blind three-bet
spots. The second size is not poker here; it is a way to get 40.5 onto the four-bet menu underneath
the clamp, and it costs twice the tree, twice the bytes, five times the iterations, and a chart that
misses the accuracy this repo declares. Shipping an unconverged solve is the defect decision 3 just
removed.

Two qualifications recorded because they cut the other way. The route D solve is unconverged and an
unconverged CFR run concentrates rather than mixes, so a converged one might spread more onto 7.5;
nobody knows what cap that would take. And `realization: calibrated` prices a flop from 169
per-class numbers with no size-dependent term, so the model has limited machinery for preferring one
three-bet size over another - the 0.5% may describe the realization model rather than the poker.

**Raising `allin_threshold` was named as a third lever and is rejected on measurement.** Letting the
72.9bb four-bet through leaves the caller an SPR of **0.19**, so it is a jam wearing a sized-raise
label, and it would pass every check in the repo while hiding the problem an honest jam displays.
It also changes the clamp for every seat at every depth, which phase 14's decision 14 tuned
deliberately.

Filed as `A-BLIND-CANNOT-FOUR-BET-A-BLIND-WITHOUT-JAMMING-AND-THE-MULTIPLIER-GEOMETRY-SAYS-WHY`.

## 5. An untrained cell refuses. `frozen-into-data`

**Ruled by Taylor, 2026-09-16.**

The re-solve commits 284 spots, of which **181 carry zero arrival** - lines the solve's own strategy
never enters - and **17 publish rows that were never trained**. Measured by the coordinator against
the committed chart: **187 cells of 25,273 (0.74%) read `0.3333 / 0.3333 / 0.3334`**, which is CFR's
uniform initialisation surviving to publication because no iteration ever visited them. One spot,
`t6/d100/SB/LJ:raise@2.5,HJ:call,CO:call,BTN:call,SB:call,BB:raise@13.5`, is **167 of its 169 cells**
- almost its entire published range is an even three-way split.

For a training bot that is the worst kind of wrong answer. It is not a gap a reader can see; it is a
strategy-shaped object that says "randomise evenly" with the same authority as a solved cell.
`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY` predicted it and this is the first solve to fire it.

**Ruled: an untrained cell refuses by its own code**, the way every other gap in this bot does. Not
dropped from the chart, and not answered.

Why refusing beats dropping the spots, which was the cheaper option and was put to Taylor as such.
The standing ruling at `test_chart_arrival_probability.py:424-442` keeps a zero-arrival spot's cells
deliberately, and its reasoning survives this: arrival is measured under the **solve's own play**, and
a human opponent takes lines the solver never does, so a trained cell at a zero-arrival spot is worth
having. What is not worth having is an **untrained** one. Dropping the 17 spots would also drop the
two trained cells in the worst of them. Refusing separates the two cases exactly.

It also costs almost nothing in coverage, because these spots carry near-zero arrival by
construction - which is why they were never trained.

## 6. Four rulings the test lane asked for

**`ROWS_THE_RAKE_DID_NOT_MOVE` is a snapshot and is labelled as one.** It asserted that the
rake-free solve matches the raked reference on exactly one of ten rows; it is now two, and the lane's
diagnosis is accepted: `defence/CO` crossed the half-point line because the **blind three-bet size**
moved the big blind's range, not because anything about the rake moved. Half a point is a round
number nobody ruled and membership is where two different solves happen to cross. The measured
two-row set ships with a docstring saying plainly that it is a snapshot rather than a criterion.
Replacing it with what it actually wants to prove - that de-raking is not a no-op, which the
1.08-to-19.43 spread carries on its own - is a follow-up and not this task.

**The captured payload keeps a second exemption and loses its convergence assertions.**
`gtopen_node_payloads.captured.json` is a hand-captured fixture of a superseded solve and cannot be
re-captured without a server. A second exemption for `raise_mults_by_seat` is defensible because the
capture is a **shape** fixture - what a node payload looks like on the wire - and the new field
changes which sizes a node offers rather than the shape the assertions read. The two convergence
assertions are deleted outright: the capture's own target is `0.01`, sixty times looser than the
`0.00016` this repo declares, and it converged at iteration 300 against a cap now at 5,000. A test
reading "the solve converged" off a solve we no longer ship is worse than no test, because it
occupies the place where the real check should be - the one decision 3 filed as
`A-SOLVE-THAT-MISSES-ITS-DECLARED-TARGET-SHIPS-WITH-NOTHING-OBJECTING`.

**The two walks round before comparing.**

**This ruling was first recorded on a diagnosis that was wrong, and the correction is the lane's.**
The original account - that the generator and the test spell the comparison differently, `high < low
- TOLERANCE_PCT` against `low - high > TOLERANCE_PCT` - was reported, accepted here without being
checked, and ruled on. It is false: `chart_relations.py:179` and `test_chart_cutover_evidence.py:336`
both spell it the second way and there was never a second spelling. The lane found this itself before
shipping the fix it had been authorised to make, which is the outcome the review model exists for.

The real cause is a value landing exactly on the tolerance. At
`t6/d100/HJ/HJ:raise@2.5,BTN:call,BB:raise@13.5` the pair of nines plays 0.84% and the pair of eights
1.84%, a gap of exactly the one-point tolerance, which a strict `>` must **not** flag. Re-derived
here: the report subtracts the chart's four-decimal weights and gets `1.0000000000000009`, which is
greater than 1.0; the walk subtracts the export's whole basis points and gets `1.0`, which is not.
**149 is the correct count and 150 was the floating-point artefact.**

Ruled: both paths round to a shared six decimals before comparing - finer than the data, which is
whole basis points, so it can only remove representation noise and cannot change a real answer. Both
walks now read 149, and the suit arm converged with it, 18 to 17.

**The test files are split, not compressed, and the cap does not move.** Three files went over the
700-line cap and four more sit at exactly 700. `test_chart_derivation.py` cannot reach 700 even with
every word of new prose deleted, because decision 2's fourth clause costs about nine lines of
**code** in a file that had no headroom. Compressing pre-existing reasoning to fit is the move
`AGENTS.md` forbids in the same breath as raising a cap. The walk helpers in
`test_chart_derivation.py` are imported by four sibling files and are the honest seam.

This is the fourth cap-forced extraction in two days of work across two lanes, and the pattern is
filed: a correction only ever adds lines, so the files that have been corrected most are the first
that cannot be corrected at all.

## 7. A spot whose multiway exposure cannot be measured is not committed. `frozen-into-data`

**Ruled by Taylor, 2026-09-16.**

Clause two refuses a spot where more than a tenth of the decision mass reaches a multiway flop. It
is the rule that keeps the bot out of pots it has no strategy for. Measured on the committed chart:
**it measures nothing at 128 of 284 committed spots.**

The mechanism is the re-solve's, not the clause's. `action_frequency` returns 0.0 for a zero-reach
node, so mass flowing into the 9,079 zero-reach nodes this solve created simply disappears from the
terminal split. **109 of the 128 lose their split entirely** and read exposure exactly 0.0 - not
because hero is heads-up, but because every branch vanished. The clause then admits them, having
measured nothing. The frozen tripwire at `SPLIT_LEAK_PCT = 0.05` caught it, and its own docstring
says it is "pinned as a tolerance so that a build losing a whole branch cannot hide inside it".
Widening it is precisely what it forbids.

Of the 19 that partly close, renormalising the exposure over the mass that actually closes puts
**exactly one** over the line: a small-blind spot at **11.1904** against a threshold of 10. So the
chart commits one spot the clause would refuse if it could see it.

**Every one of the 128 carries zero arrival**, verified. Under the solve's own play nobody reaches
them, so both fixes cost **0 ppb of 6,054,005,282** - no coverage at all.

**Ruled: refuse all 128.** When the guard cannot measure its own input, fail closed. That is how this
bot handles every other gap, and it is the same posture as decision 5 one level up: there an
untrained cell refuses rather than publishing its initialisation, here an unmeasurable spot is not
committed rather than admitted on a measurement that did not happen.

The narrower option - renormalise and refuse only the one spot over the line - was on the table and
was rejected. It keeps the chart's size and leaves 109 spots admitted by a clause that measured
nothing, which is the state a later reader would have no way to detect.

**What it costs is rework, not poker.** Committed spots go 284 to about 156. The census, the coverage
figure and roughly thirty test pins move again, having just been moved. Zero arrival mass is lost.

**What it does not close.** Zero arrival is measured under the *solve's own play*. A human opponent
takes lines the solver never does, so these 128 are spots a person could still put the bot in - it
will now refuse there rather than answer from a guard that never checked. That is the intended
outcome and not a residual defect, but it is the reason the count of refusable spots rises.
