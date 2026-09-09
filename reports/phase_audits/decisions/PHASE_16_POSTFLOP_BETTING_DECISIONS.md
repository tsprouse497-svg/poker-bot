# Phase 16 judgment calls

These are the choices about what a committed postflop solution covers, and what the bot does outside it.
No test in this repo settles them.
A solution that covers the wrong spots passes just as green as one that covers the right ones, and a bot that guesses on an unseen board looks exactly like a bot that knows.

They are recorded ahead of the phase because the phase is gated on them. When this file was
written `verification/loop_policy.yml` marked phase 16 `needs_human_data`; it now reads
`needs_human_data: false`, because the source it was waiting on turned out to exist. What still
gates the phase is every `frozen-into-data` item below that has no answer, which stage 3 halts on
one at a time.

Every item carries a reversibility class. Stage 2 checks only that a class is declared; **stage 3
is where the loop stops for a human**, and an earlier version of this paragraph put the stop at
stage 2.

The two classes are quoted from `docs/LOOP.md` rather than paraphrased, because an earlier version
of this list narrowed one of them:

- `runtime-reversible`: "the choice only changes behavior at query time, so a later edit **can**
  change it. The loop takes the recorded default, proceeds, and reports what it chose."
- `frozen-into-data`: "the choice gets written into a committed artifact **or fixture** that later
  phases are then measured against. The loop halts until a human answers."

The words "or fixture" are load-bearing and this file had dropped them.
`LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` records its own resolution on exactly them: a behaviour
default that a contract requires a frozen test to pin is a fixture, so it carries this class even
in a phase that commits no data. A phase taking its definitions from this list rather than from
`docs/LOOP.md` would have called such a threshold reversible and never asked anyone.

## What is being asked

Nine choices are open. Each is `frozen-into-data`, so the loop stops here rather than proceeding
on a default. The full argument for each is in its own section below; this is the index, and no
ruling needs more than its three lines. **Read 13 first**: it asks whether the other eight belong
in one phase, and if they do not, some of them are not yours to rule yet.

**4. Exploitability target, and a cell that never reaches it.** Target 0.3% of the starting pot,
and commit a cap-bound cell with its achieved percent as a floor, or refuse it. The scale is what
makes this consequential: **23 of 30 measured rows missed the target** and rainbow never reached it
at all, so refusing leaves about **455 of 1,755 flop classes with no cell** and makes the
board-miss refusal code live. Default: 0.3%, and refuse.

**6. How the committed artifact is encoded, given that it does not fit.** A budget, not a menu: the
**15.04 MiB of headroom** left under the 20 MiB cap affords about six node-line units at one byte per
weight, and the affordable products are 6x1, 3x2, 2x3, 1x6 and everything under them. But a
complete flop is about **five** hero decision nodes under the ruled menu, so six units is **one**
preflop line at full flop depth, not the two 3x2 suggests. Six levers, none fail-closed.
**No default** - an answer must fix the encoding, the per-spot byte budget including provenance, and
the number of preflop lines, and the six units are quoted at an encoding the answer itself chooses.

**7. Whether the committed solve is reproducible, and what is recorded if not.** Byte-identical was
measured on one spot; a 1,755-flop run reaches a route recorded unrun.
Default: prove it on the committed configuration, and a human sets the tolerance if it is not.

**8. How the preflop line compresses into the postflop key.** Verbatim, or a coarser class; and
whether the price substitution is baked in. Default: verbatim, sizes included, inside a key that
does not begin with `t`, with the substitution recorded on the committed spot.

**9. Whether flop bet sizes appear in the key.** Name the size, or name only the action class.
Facing 33% needs 19.9% equity and facing 75% needs 30.0%; defence frequency goes 75.2% to 57.1%,
so a merged cell overfolds to small bets and overcalls to large ones and an opponent picks his size
to farm it. Naming the size costs **zero** bytes and makes a later menu change fail closed rather
than silently reinterpret cells. Default: name the size. **Rulable without 11.**

**10. Whether pot and effective stack appear in the key.** In the key, or in the payload validated
against the line. Default: payload, validated.

**11. The bet-size menu the solve is configured with.** Four levers with different evidence: pinned
is measured on 3-bet pots only and its single-raised tree is a hard memory wall (21,282-21,715 MB
against a 12,026 MB ceiling, which fails rather than slows); reduced is measured on single-raised
pots only; one-per-pot-type is the only option measured on both, **but the poker says it is
backwards** - a single geometric size is 66% of pot in a 3-bet pot and 116% in a single-raised one,
so it puts two sizes where one nearly suffices; and flooring to fit is a **build, not a solve**.
Rainbow is unmeasured in all four. Whatever is ruled also freezes **no donk bet and no all-in**,
which push flop aggression in opposite directions. **No default**, it collides with decision 3
already ruled, and **rule it with 12** - the settling experiment needs a floor.

**12. Whether the solve floors its input ranges, and at what weight.** A floor at 0.01 halves the
memory needed and deletes 68.9% of the defender's combos - but **0.199% of its weight**: the
heaviest hand cut is `87s` at 0.0099 and the bulk are preflop residue like `32o`. Default,
**reversed 2026-09-09** after the poker review measured the mass: **floor, class-level, at 0.01**.
The cost it does carry is the pair ladder - a 0.01 floor leaves the 3-bet defender every pair
except `44`, and the single-raised defender only `55 44 33 22`. **Rule it with 11.**

**13. Whether this is one phase.** Items 8, 9 and 10 define a key format; 4, 6, 7, 11 and 12 define
a data campaign, and this repo's rule is format before data with a phase boundary as its precedent.
For: phase 14 asked this and answered "split it"; and one phase means up to five rulings share the
contract's sixteen remaining lines. Against: the phase 17 that split created is still unstarted, and
a split is a second contract, gate, packet and human gate, so you are asked twice. **No default.**

Decisions 1, 2 and 3 were ruled on 2026-08-19 and are not reopened; five of their premises are
annotated below as no longer true, none re-ruled. Decision 5 is `runtime-reversible` and proceeds
on its default.

## What changed, and why this file exists

The premise this phase was declared under was wrong.
`docs/V2_ROADMAP.md` said the only sizing source in the repo is a preflop export and that phase 16 is blocked on a source that does not exist.
GTOpen solves postflop as its primary function.
Its README leads with postflop CFR; the Preflop Lab that phase 10 uses is the bolt-on beside it.
The postflop engine is the un-namespaced route surface (`/api/spot`, `/api/solve`, `/api/node`, `/api/runouts`, `/api/reports/*`), it takes per-street bet, raise and donk sizes, it does node locking and best-response, and it batch-solves a weighted canonical flop subset of 47, 95, 184, or all 1,755 flops.
`SEND TO POSTFLOP` carries both conditional ranges, the pot and the stacks out of a preflop line into a flop setup.

`docs/GTOPEN_SOLVER_NOTES.md` did not say otherwise; it recorded only what had been executed, and everything executed happened to be preflop. That is the note working as designed and a reader drawing the wrong inference from it anyway, which is why the note now states the postflop surface exists and is unrun.

One design point follows and it narrows this phase considerably.
A committed postflop artifact does **not** have to be a joint solved tree.
A postflop spot is self-contained: board, both ranges, pot, effective stack, sizes.
So the artifact can be a library of independent per-street spots keyed the way the preflop chart already is, and the bot can evaluate each street from the board, its hand, and a summary of prior action.

What does not decouple is ranges.
Postflop strategy is overwhelmingly range against range rather than a function of hero's two cards, so the same hand on the same board plays differently after `LJ open, BTN call` than after `BTN open, BB 3-bet, BTN call`.
The action summary in a spot key is therefore a handle on a pair of ranges, not history for its own sake, and the preflop line has to compress into it.

And generation stays sequential even though storage does not.
Villain's turn range is whatever he would bet and check with on the flop, which is the flop solution.
So enumerating turn spots requires the flop spots first.

### The counts, and what is actually known about them

An earlier version of this file gave the fan-out as 47 turns and about 2,160 rivers.
That is hero's view, counting cards he cannot see because he holds two of them.
A spot in the artifact is keyed by the board rather than by hero's hand, so the right counts are 49 turn cards and 48 rivers.

Per preflop line covered:

| Depth | Spots |
|---|---|
| Flop | 1,755 |
| Flop + turn | 1,755 + 85,995 |
| All three streets | 1,755 + 85,995 + 4,127,760 |

Two things about that table are assumptions rather than measurements, and both are stated here so nothing downstream quotes them as facts.

The 1,755 is per preflop line and has to be multiplied by however many lines decision 3 covers.

**Corrected 2026-09-08.** This paragraph said no solve in this repo had ever been timed to a real
exploitability target, that only a 300-iteration preflop smoke test was ever run, that solve time
and determinism were both still on phase 10's unverified list, and that affordability at any depth
is unmeasured. All four are false, and the paragraph whose stated job is to stop anything
downstream quoting an assumption as a fact was the last place in the file still carrying them.
Decision 4 corrects the first three by name a hundred lines below, which is the eighth time in this
file a correction has reached one item and not its siblings.

- MAINT-26 reached 0.3% of the starting pot on 7 of 30 solve rows, at 220 to 260 iterations.
- Phase 14 re-solved preflop to 0.00016bb at iteration 1,900 in 200.4 seconds; MAINT-26 ran 30
  postflop solves.
- Determinism is measured and byte-identical across two processes against a restarted server.
- Flop affordability is measured on three axes: disk in decision 6, arena in decisions 11 and 12,
  and per-iteration cost in MAINT-26.

What is still honestly unmeasured, and stays: the 1,755 is per line and the line count is
unruled; rainbow was never solved to target and is 455 of the 1,755 classes; and no solve has been
diffed against a deeper one, so convergence at the committed iteration count is unproven.

What survived that, when this file was written, was a ratio rather than an absolute: the turn was
taken to be about 49 times a flop and the river about 2,350 times, whatever a flop turned out to
cost, and every conclusion below was rewritten to rest on the ratio only.

**The ratio is falsified, 2026-09-08** (`POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`). It runs the other
way. MAINT-26 measured a turn-rooted solve at about 1/212 of a flop solve and a river root at about
1/38,000, because a flop-rooted tree already contains and iterates its own turn and river subgames -
it is 99.5% river nodes and holds 158,466 river subgames. So a turn spot is far cheaper than a flop
spot, not 49 times dearer, and the counts table above is a count of spots rather than a cost.

The rulings are unaffected and are not reopened here. Decision 1 is flop only and it now has a
second, better reason than cost: a flop solve is where the work already is. What the falsified
ratio does change is that no conclusion below may be supported by it, and any sentence that says
the turn is expensive because of the ratio is supported by nothing.

## 1. How deep the committed solution goes

Reversibility: frozen-into-data

Flop, flop plus turn, or all three streets.
The **spot count** is not linear: one flop spot is 49 turn spots and 48 rivers below each of
those, before any preflop line is counted. This sentence read 47 and about 2,160 until 2026-09-08,
which is hero's view of a board he holds two cards against; the counts table above had already been
corrected and this line had not.

It said "and each has to be solved to a target exploitability rather than derived" until the same
date, which is the compute rationale `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` falsifies and which is
struck rather than reworded. A turn is not solved separately from the flop above it: a flop-rooted
tree already contains and iterates its own turn and river subgames. So the spot count is a count of
storage, and it says nothing about compute in either direction.

Committing turns and rivers is also where the artifact stops resembling a chart.

**Corrected 2026-09-08.** This paragraph said `data/artifacts/**` is covered by no size check at
all. It has been capped at 20 MB since `2430894`, 2026-08-18, in `DIRECTORY_BYTE_LIMITS` in
`scripts/check_file_sizes.py` - a third list, which is why a reader checking `LINE_LIMITS` and
`BYTE_LIMITS` concluded there was nothing. `docs/V2_RULING_MITIGATIONS.md` at 103 and 259 and
`docs/V2_ROADMAP.md` at 161 carry the same wrong claim and are corrected with it. The cap is not
a turn-and-river problem: decision 6 measures that the flop artifact alone does not fit.

Default: **flop only.** The bot gets a real flop strategy that can bet and raise, and turn and river refuse the way an uncovered preflop spot refuses today. That is a smaller artifact, it needs no boundary change, and it makes the phase's own claim narrow enough to be true. It also leaves the turn as a separately fundable phase rather than a thing half-done inside this one.

The cost of that default, stated rather than buried: the bot bets a flop and then goes quiet, which is a worse experience than never betting at all if a drill deals past the flop. Whether that matters is evidence phase 15 produces.

Answer: [Ruled by Taylor, 2026-08-19] **Flop only.**

Every flop, against a small head of common preflop lines: prune hard on the axis where pruning is real, and stay complete on the axis where completeness is cheap.
The turn waits on `POSTFLOP-BOARD-ABSTRACTION` from decision 2, which is what makes 85,995 turn spots into a tractable number, and it is deferred with it.

The accepted cost is the one above. A bot that bets a flop and then checks or folds every turn is a bot with a visible seam, and phase 15's drill is where that either matters or does not.

**Annotated 2026-09-08, not re-ruled** (`A-RULED-DECISION-CAN-NAME-A-SOURCE-THE-REPO-WILL-NOT-HAVE`).
Twice above, this item validates its accepted cost against phase 15 - "whether that matters is
evidence phase 15 produces", and the sentence before this one. Phase 15 is `future` in
`phase_status.yml` and its lane is parked at its own human gate, so that evidence does not arrive
before this phase ships and may not arrive at all. Decision 3 carries this exact annotation for the
same source; decision 1 names it for the same kind of claim and was never annotated. The accepted
cost stands and is now accepted **without** the check that was to validate it, which is a harder
thing to accept and is what a reader should be told.

## 2. What the bot does on a board it holds no cell for

Reversibility: frozen-into-data

Any canonical subset smaller than all 1,755 flops guarantees the bot meets boards it has not solved. Suit isomorphism is exact and free; GTOpen already exploits it internally. Rank texture is not: mapping an unsolved `K72r` onto a solved `Q83r` is a heuristic, and `AGENTS.md` forbids heuristic guessing for missing chart spots.

So this is a boundary question, not an implementation detail. Either the rule holds and the bot refuses on an unsolved texture, or the rule is amended for board texture specifically, which is a `contract-update` to `AGENTS.md` in its own right.

Default: **solve all 1,755 flops and keep the boundary.** With a flop-only solution the runout fan-out is gone, so the full canonical set is the thing that removes the question rather than answers it, and the bot never faces a flop it has no cell for. If 1,755 per line proves unaffordable once solve time is measured, the fallback is fewer preflop lines, then a flop subset plus refusal, and never a subset plus abstraction.

**Annotated 2026-09-08, not re-ruled.** Three claims in this item were true when written and are
not now, and the ruling survives all three.

*"The bot never faces a flop it has no cell for"* no longer follows. Decision 4's default refuses a
cell that never reaches the exploitability target, and rainbow - 455 of the 1,755 classes - has
never been solved to target at all, so uncovered boards are possible from inside this phase's own
choices rather than from a subset. The contract was amended for this; this item, where the claim
originates, is amended here.

*"All 1,755 flops is affordable"* is false on both axes this phase measured, and it is the stated
reason abstraction is deferred rather than needed. Decision 6 measures that the flop artifact does
not fit 20 MB in any encoding at the depth and breadth ruled; decision 11 measures the
single-raised-pot tree at 21.7 GB against a 12.0 GB ceiling. The deferral still holds, because
decision 6 says a size problem is not a licence to reopen abstraction and its lever 5 answers
without one - but a reader taking the affordability sentence as current cannot see why decision 6
exists.

*"Roughly 3.8 million spots"* is 1,755 x 47 x 46 = 3,794,310, hero's view of a board he holds two
cards against. Decision 1 corrected that fan-out to 49 and 48 on 2026-09-08; board-keyed it is
1,755 x 49 x 48 = **4,127,760**, which is what `POSTFLOP-BOARD-ABSTRACTION` already says. Two
committed documents disagreed and nothing compares them.

Answer: [Ruled by Taylor, 2026-08-19] Take the default, and defer abstraction rather than reject it.
Grouping similar flops so the bot plays them identically will eventually be needed, and it is filed as `POSTFLOP-BOARD-ABSTRACTION` rather than left as an unstated intention.
Not now, because at flop-only depth the full canonical set removes the need entirely, and an abstraction built where nothing requires it is a heuristic nobody can measure.

What that ruling also settles, worth stating because it was not asked directly: abstraction is the enabling condition for **depth**, not for breadth.
All 1,755 flops is affordable; 1,755 turns and rivers is roughly 3.8 million spots and is not.
So the turn is not a matter of solving more of the same thing, and deferring abstraction defers the turn with it.

## 3. Which preflop lines get a postflop solution

Reversibility: frozen-into-data

Only lines that see a flop matter, which is far fewer than the 1,691 six-handed 100bb spots the v2 vocabulary can express, but the count is not currently known. It becomes computable off the phase 10 export.

Default: rank the lines by how often the corpus and the drill actually reach them, take the head of that distribution, and record the covered set explicitly so a refusal names a line that was excluded rather than one that was forgotten. A refusal inventory is the precedent and already works this way preflop.

Answer: [Ruled by Taylor, 2026-08-19] Take the default. **A small head of common lines, grown later by adding artifacts.**

**Annotated 2026-09-06, not re-ruled** (`A-RULED-DECISION-CAN-NAME-A-SOURCE-THE-REPO-WILL-NOT-HAVE`).
Taylor's answer stands and the method is unchanged. One of the two sources it names will not exist:
the drill produces no data at its own completion, only through a human using it over time, and phase
15 is now parked at its human gate and no longer sits ahead of this phase. **So the corpus is what
ranks the lines**, which is the half that already works. If drill sessions ever accumulate they are
added to the ranking; nothing waits for them.

**Corrected 2026-09-08, method only; the ruling is untouched.** This annotation named
`reports/active/latest_refusal_inventory.txt` as the corpus precedent. That file is built from
self-play - seed 20260812, 600 hands, two seatings out of `profiles/seating.py`, written by
`scripts/generate_profile_comparison_report.py`. The corpus-fed sibling is
`reports/active/latest_sample_refusal_inventory.txt`. Neither is the right instrument anyway,
because both rank only what was *refused* and this ruling needs what was *reached*. That already
exists: `ComparisonRow.asked_spot_key` is populated on every keyed row rather than on refusals
only, and over the committed 499-hand corpus it gives 3,048 decision points across 127 distinct
spot keys, whose head agrees with the artifact's own `arrival_ppb` order on the top ten but for two
swaps. Two things the covered set must state rather than inherit: those keys are
post-substitution, since the corpus's median open is 2.25bb and every key reads `@2.5`; and
reaching a decision point is not seeing a flop, so the filter this ruling actually needs is a
different query and nothing in the repo computes it yet.

This is the axis where pruning is honest, and it is the opposite of the flop axis.
Preflop lines have a real long tail: some come up constantly and most almost never, which the refusal inventory already demonstrates for preflop spots.
Canonical flops do not. The 1,755 classes come up at broadly comparable rates, so there is no head to solve, which is why decision 1 keeps all of them and this one keeps very few lines.

**Annotated 2026-09-08, not re-ruled.** "Broadly comparable" understates a **6x spread**, measured
here by brute force over all 22,100 boards under all 24 suit permutations rather than argued.
Orbit sizes are 24, 12 and 4: **286 classes (16.3%) cover 6,864 boards (31.1% of flops)**, 1,170
(66.7%) cover 63.5%, and 299 (17.0%) cover 5.4%. So the most-multiple sixth of the classes is
over-represented 1.91x and the least 0.32x. The ruling survives - a 6x spread over a flat-ish bulk
is still not the long tail the preflop-line axis has, and 63.5% of flops sit in one orbit class -
but "no head to solve" is a stronger statement than the measurement supports.

That also settles what GTOpen's 47, 95 and 184 flop subsets are for here, which is nothing.
They are study sets: a human reads texture patterns off a report. As a bot's lookup table a 47-flop subset covers 2.7% of flops and refuses the rest, so it is only usable with the abstraction decision 2 defers.

**Annotated 2026-09-08, not re-ruled.** Two errors in that sentence, and they pull opposite ways.
**2.7% is 47/1,755, a share of *classes*, not of flops.** Because orbit sizes are 24, 12 and 4 the
board share of 47 classes lies between **0.85% and 5.10%**, and GTOpen's subsets are weighted, so
it cannot be inferred from the count at all. And **"only usable with the abstraction decision 2
defers" is wrong**: a subset plus refusal borrows no solved board for an unsolved one, which
decision 6's lever 5 states in its own words and which decision 2's own ruled fallback names
before abstraction. As written, a reader meets the discouragement before the option, in the item
that lever 5 cites for that lever's cost.

Growing this later is cheap and it is the pattern the repo already runs, verified rather than assumed:

- `PreflopChartLibrary.__init__` takes a sequence of artifacts, sorts them, and rejects only a genuine duplicate spot key, so an added artifact file needs no code change.
- The lookup fail-closes, so an added spot strictly adds capability and cannot alter a spot already covered.
- A refusal inventory ranks the gap most-reached first and regenerates every gate run. Which
  inventory matters: the self-play one counts refused *hands*, the corpus one counts refused
  *decision points*, and the grouping key of the self-play one is the whole detail tuple, which
  `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` records as shattering into singleton rows at
  any non-flat table.

What is *not* cheap later is the spot key itself. Adding spots at a fixed key is additive; changing what the key can express re-derives every committed cell, which is why phase 12 sits ahead of phase 14 and why the ordering rule is format before data. So the one thing this phase must get right up front is the postflop spot key, and coverage may start as small as it likes.

## 4. Exploitability target, and what happens to a cell that never reaches it

Reversibility: frozen-into-data

GTOpen's own README puts 0.3% of pot as a study-quality target.

**Premise corrected 2026-09-08.** This item said nothing in the repo had measured a real solve to
any target, that determinism was unverified, and that phase 16 inherits whatever phase 10
establishes. All three are now wrong, and the third was wrong when written.

Phase 10 did deliver both numbers and **neither transfers**. Its target is a summed
best-response gap of 0.01bb, preflop; the committed card now reads 0.00016bb reached at iteration
1900 in 200.4 seconds after phase 14 re-solved. Postflop targets a percent of the starting pot
instead, and `docs/GTOPEN_SOLVER_NOTES.md` is explicit that a criterion written in big blinds
rather than percent of pot will not reproduce the postflop iteration counts. Phase 10's own
decision 3 also records that multiway has no exploitability proper. Different engine, different
tree, different unit.

What actually answers this item is MAINT-26, on 2026-08-23 and 2026-08-24, for the flop:

- **Target reached: 0.3% of the starting pot**, on 7 of 30 solve rows, at 220 to 260 iterations
  with a 20-iteration bracket. The other 23 rows stopped on an iteration cap and are floors.

Reproducibility moved to decision 7 on 2026-09-08. It shared this heading, and
`decision_items` in `scripts/loop_stage.py` collects one `Answer:` per heading, so answering the
target here would have discharged reproducibility at stage 3 without anyone ruling it - invisibly
to `review_queue.py`. Two frozen questions cannot share one answer slot.

**A second frozen choice this item was hiding, and it is not the target.** 23 of the 30 measured
rows never reached 0.3%; every one reads `hit-iteration-cap`, and rainbow - 455 of the 1,755
classes and the expensive end - was never solved to target at all. So a real run produces cells
that hit the cap first. **What happens to a cap-bound cell is frozen into the data and nobody has
been asked**: commit it with its achieved percent recorded as a floor, or refuse the spot the way
an uncovered preflop spot refuses. Committing floors means the artifact's stated accuracy is a
claim about its best cells rather than all of them; refusing means a bot that has no answer on the
boards it will most often see.

Default: **target 0.3% of the starting pot, record the achieved percent and the iteration count on
every committed spot, and refuse rather than commit a cell that hit the cap** - refusing because
this repo fails closed everywhere else and a floor recorded as a cost is still a cell the bot
plays.

Three things that default does not cover, stated because a packet that quoted 0.3% as settled
accuracy would be claiming more than the measurement supports:

1. **It is not known whether the strategy has converged.** Exploitability was targeted; frequencies
   on indifferent hands settle later, and nothing was solved deep and diffed against a shallower
   solve. Both determinism runs stopped at 240 iterations. This is the first entry on the notes'
   "Not verified" list, and it matters here more than anywhere: this phase commits the result, so
   if frequencies need several times 240 iterations then every cost figure is off by the same
   multiple and the committed data is unproven. It is the one measurement this phase needs that
   nobody has taken.
2. **0.3% bounds exploitability only against an opponent confined to the same bet menu.** The
   best-response pass walks the same tree. The abstraction error of a two-size menu is larger than
   the target.
3. **Rainbow was never measured at the target**, and rainbow is 455 of the 1,755 classes and the
   expensive end. Every rainbow figure in the cost model is scaled from an exact orbit factor
   rather than measured, filed as `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`. So is every paired,
   ace-high and disconnected board: the five converged cells cover two rank patterns.

Answer:

## 5. Whether the pot-odds river call ships alongside

Reversibility: runtime-reversible

`POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK` calls a river bet when equity against the full unseen deck beats the price. It needs no solved data and invents no constant: equity is `(wins + ties/2) / 990` from the enumeration `hand_cannot_lose` already runs, and the price comes off the query.

A uniform unseen deck flatters hero, so this makes the bot over-call as the mirror of its current over-folding. Under the flop-only default it is also the only thing that acts on a river at all.

Default: build it, behind an explicit flag, and report the frequency it fires rather than claiming it is correct. It is runtime-reversible because no committed data records it; it is a rule the query evaluates.

Answer:
## 6. How the committed flop artifact is encoded, given that it does not fit

Reversibility: frozen-into-data

Filed 2026-09-08 at the contract stage, from a measurement rather than from reading. Decisions 1
and 2 fixed the depth and the breadth on solve-time grounds. Disk was never measured, and the file
that should have caught it said there was no size check. There is one, and the artifact does not
fit it.

The measurement, every input recomputed here rather than quoted:

- `data/artifacts` is capped at 20 MB in `DIRECTORY_BYTE_LIMITS` in `scripts/check_file_sizes.py`,
  since `2430894` on 2026-08-18. The tree holds 5,197,325 bytes, so headroom is 15,774,195.
  **Units, once, because this file already carries a cross-unit finding.** The cap is
  `20 * 1024 * 1024` = 20,971,520 bytes, so "20 MB" throughout this file and in the script's own
  comment means 20 MiB; headroom is 15,774,195 bytes = 15.04 MiB = 15.77 MB. Every ratio below is
  computed from the byte figures, so it is unaffected either way, and the MiB reading is the one
  that makes the labels consistent.
- 1,755 canonical flops. 1,176 hero combos per flop. Collapsing each flop's own suit symmetry -
  exact, free, and the only collapse decision 2 permits - leaves **1,286,792 hero-combo classes
  summed over all 1,755 flops**, a mean of 733 per flop against the preflop chart's 169 per spot.
  That collapse is worth 1.6x, not the 7x that would make a flop cell chart-sized.
- 14.8 bytes per action weight, measured off the committed chart's own `action_weights` block in
  compact JSON; 26.8 as actually committed with `indent=2`.

**The finding is the node count, not a ratio against one encoding.** Fifteen megabytes of headroom
buys, for **one** preflop line, on the order of **one hero decision node** - and that holds in any
JSON encoding, which is why no format change answers it. In the leanest plausible JSON, action
names hoisted to one array, hero's classes as a parallel array in canonical order, three-decimal
floats and one free weight per class, one two-action node for one line measures 7,740,095 bytes -
two independent builds agreed to within 38 bytes, both at 0.4907x -
which is 0.49x the headroom: it fits, with room for a second node. That same encoding buys 2.04
nodes at two actions, 1.02 at three storing two free weights, and 0.68 storing all three. A flop is
not one decision - hero acts, villain answers, hero faces a bet or a raise - and decision 3 asks
for a head of common preflop lines, plural. Several nodes across several lines is what the phase
needs, and one node for one line is what the cap affords.

The chart's own format is worse, and the figures are given as pairs that recompute from the rates
above rather than from any other rate. One line, one node, only check and bet: 36 MiB compact, 66
MiB as committed, 2.4x and 4.4x. Ten hero nodes at three actions: 544 MiB compact, 986 MiB as
committed, 36.2x and 65.6x. Building the structures directly rather than multiplying the rate gives
43, 76 and 1,007 MiB, so the multiplications err low; those three are the independent numbers
verification's builds, recorded in its note beside this stage's. Compression is not available:
`import_preflop_artifacts` globs `*.json` and reads text.

An earlier draft of this paragraph led with the 2.4x, gave 99 MB and 1,481 MB for the two
as-committed figures and 24x and 98x for the ten-node row, and the independent numbers review at
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-01-numbers-verification.md` held the
stage over all of it. The two as-committed figures had silently used 40.227 bytes per weight, the
whole committed file over its weight count, in place of the 26.789 stated one line above; that rate
charges the chart's `spots`, `arrival_ppb`, `arriving_reach_bp` and `audit_fields` blocks against
every weight when those scale per spot. The ten-node compact figure had dropped the third action
and so ran low while the other two ran high, which is why the paragraph could not be repaired by
scaling. And leading with 2.4x invited the one ruling that would be wrong, since a format change
defeats 2.4x and does not touch the node count.

`ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` already records phase 14 measuring 4.5x to 26x over
the same cap for a different reason, so this is the second phase to meet it and the first to be
stopped by it. `SOLVER-EXPORT-CARD-HEADROOM-COUNTS-THE-WHOLE-ARTIFACT-TREE` means any flop
artifact also reds `test_the_committed_export_sits_under_the_limit_with_stated_headroom` until the
export's source card is regenerated.

**What an answer must fix**, because the contract needs three things from it and no single option
below supplies them: the **encoding**, the **per-spot byte budget** including the provenance
fields, and the **number of preflop lines**. A pick from the list is not an answer on its own; a
pick plus a product from the budget above is.

Default: **none, deliberately.** Not an omission and not a coordinator declining to think: the
six levers trade reviewability, coverage and repo weight against each other, and there is no
fail-closed option among them, because every one of them still commits data. The six levers,
stated without a recommendation because the cost of each falls in a different place:

First, what encoding is worth, measured, so no option below rests on a format argument. Hero
strategy only, storing only the free weights, over all 1,755 flops, and read as **how many hero
decision nodes 15.04 MiB buys for ONE preflop line**:

| Encoding | MiB per node per line | Nodes affordable |
|---|---|---|
| chart JSON as committed, 3 actions | 98.62 | 0.15 |
| chart JSON compact, 3 actions | 54.43 | 0.28 |
| lean JSON (hoisted actions, parallel class array, 3-decimal floats), 3 actions | 14.76 | 1.02 |
| same, 2 actions | 7.38 | 2.04 |
| binary float32, 3 actions | 9.82 | 1.53 |
| binary, one byte per weight, 3 actions | 2.45 | 6.13 |
| binary, one byte per weight, 2 actions | 1.23 | 12.26 |

**Re-encoding is worth about 40x, and what it buys is a budget rather than a yes or no.** Read the
right-hand column as **node-line units**: one unit is hero's strategy at one flop decision node,
over all 1,755 flops, for one preflop line. Cost is the *product* of nodes and lines, so five
nodes for one line and one node for five lines are the same 12,867,920 bytes. At the most
aggressive row the cap affords **about 6 units**, and the whole affordable frontier is: 6x1, 3x2,
2x3, 1x6, and everything under them. At lean JSON it is 1 unit. At the chart's committed format it
is 0.15.

An earlier draft of this entry gave 5x1, 1x3 and 1x5 as its examples and called option 4 "the only
option that fits today without touching the cap". Both were wrong and the stage-2 review held the
stage over them. The example set skipped the middle of the frontier, where 3x2 and 2x3 both land at
0.979x. An earlier draft put a flop's decision count at three there and attributed it to the
contract, which neither states nor implies it; the phrase was a reviewer's reading quoted back as
the document's own.
That was a reviewer's hedged phrase quoted back as a flat assertion, and it is an under-count:
under decision 11's pinned menu with `max_raises: 2` hero has about five flop decision nodes, so
about six units buys **one** preflop line at full flop depth, not the two that 3x2 suggests. The
frontier below is arithmetically right and reads roomier than the ruled defaults allow. And "the only option that fits" is false by this table:
5x1 *is* option 2 driven to its limit, and option 4's 0.49x and 0.82x are quoted in the aggressive
encoding, so ruling option 4 alone silently also rules the encoding. In the chart's own format
option 4 is 98.62 MiB per node-line, 6.6x over, and fits nothing.

The budget also excludes something the contract mandates. Every committed spot must carry its
achieved exploitability, its iteration count and its strategy digest, and the table prices hero's
free weights only. At 24 to 120 bytes a spot that is 0.3% to 6.7% of the headroom depending on the
line count - small, real, and not zero, and it is what a per-spot cost has to include.

So the finding is not about serialization at all: **no encoding, text or binary, fits several hero
decision nodes across several preflop lines inside 20 MB.** What an answer has to fix is below.

What one byte per weight costs is **unmeasured, and it is not the 0.3% target.** An earlier draft
of this paragraph said one byte quantises a frequency to about 0.4% and so sits at the edge of the
0.3%-of-pot target it would be storing. The arithmetic is right - one byte over [0,1] is 1/255,
0.392% - and the comparison is meaningless: 0.4% is a granularity in *action frequency* and 0.3%
of pot is an *exploitability* bound, there is no conversion between them, and rounding a frequency
does not add its own size to exploitability. Struck rather than reworded, and filed as
`A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS`, because this repo has already shipped one
cross-unit percentage confusion into committed config.

The real exposure runs the other way from where that draft pointed it, and stating it is the
condition on option 1. A solver mixes only where it has driven a hand to indifference, and at
indifference the EV gap between the mixed actions is near zero, so perturbing that split costs
almost nothing - at a converged equilibrium. A mix in an unconverged average may not be a true
indifference but an artifact of regrets that have not settled, and there the EV gap need not be
near zero at all; decision 4 leaves exactly that open, since both determinism runs stopped at 240
iterations and nothing has solved deep and diffed. So this argument is weaker for the strategy
this phase would actually commit than for one at equilibrium, which pushes the cost further into
unmeasured rather than out of it. Pure strategies are lossless, since 0 and 255/255 are exactly representable. What
quantisation actually damages is the long tail of near-zero weights, where rounding 0.002 to 0
removes a rare action outright and moves it by a large relative amount. Whether that matters is a
question about the committed strategy, nobody has measured it, and it is smaller than the
struck claim implied.

1. **A leaner encoding, text or binary.** Real, bounded, and already costed above. The repo commits
   a binary artifact today, `preflop_eq169.bin` at 114,244 bytes with a `.source.json` beside it, so
   the precedent and the provenance pattern exist. It buys a factor of about 40 over the chart's
   committed format and it costs the property that a reviewer can read the artifact, which is what
   `check_file_sizes` says the cap exists to protect. On its own it moves the phase from a fraction
   of one node to a handful, and decision 3 asks for lines plural.
2. **Fewer preflop lines.** Decision 3 already prunes on this axis and calls it the honest one, but
   it is the wrong axis for this constraint: the table above is *per line*, so cutting lines does
   nothing until there is one line left, and one line still affords about 5 nodes at the most
   aggressive encoding. An earlier draft of this list said even a single line does not fit in JSON.
   That was true of the chart's format and false of a lean one, which fits one node at 0.49x, and
   the correction is dated 2026-09-08.
3. **Raise or replace the cap.** `check_file_sizes.py` says in its own comment that exceeding a
   limit here "is a halt and a decision, not a number to raise", which is what this entry is. The
   cost is repo weight, permanently, since git keeps every version of a committed artifact.
4. **Commit fewer nodes per flop.** Store hero's flop root only and refuse every later flop node.
   One unit, so it fits at any encoding from lean JSON up and fits nothing in the chart's format.
   It buys a bot that opens a flop and then refuses inside the same street, a worse seam than the
   turn seam decision 1 accepted, and it spends the whole budget on breadth.
5. **A flop subset plus refusal.** Decision 2's *ruled* text names this as its own second fallback -
   "if 1,755 per line proves unaffordable once solve time is measured, the fallback is fewer preflop
   lines, then a flop subset plus refusal, and never a subset plus abstraction" - so it is inside
   what Taylor already ruled and was omitted from an earlier draft of this list. It is not
   abstraction: an unsolved board refuses rather than borrowing a solved one. It scales the unit
   directly, and its cost is bounded rather than quoted: decision 3 says a 47-flop subset covers
   2.7% of flops, which is 47/1,755 and a share of *classes*; because orbit sizes are 24, 12 and 4
   the board share of 47 classes is between 0.85% and 5.10%, and GTOpen's subsets are weighted so
   the count does not give it. A subset's real cost is a refusal rate somebody measures on the
   chosen subset.
6. **Keep the solves outside `data/artifacts` and commit only what the bot reads.**
   `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` names this and nothing in the contract forbids it.
   The cap is on a directory, not on the concept of committed data, so the question it raises is
   what the cap is for: if the answer is reviewability, moving the bytes elsewhere and calling them
   not-an-artifact is an evasion; if the answer is repo weight, it is a real fix. That is a ruling
   about the rule rather than about this phase, which is why it is last and why it is stated as the
   uncomfortable option rather than the clever one.

What is **not** on the list: grouping unsolved boards onto solved ones. Decision 2 deferred that as
`POSTFLOP-BOARD-ABSTRACTION` and `AGENTS.md` forbids heuristic guessing for a missing chart spot.
A size problem is not a licence to reopen it.

Answer:


## 7. Whether the committed solve is reproducible, and what is recorded if it is not

Reversibility: frozen-into-data

Split off decision 4 on 2026-09-08 by the stage-2 review. It shared that heading, and
`decision_items` reads one `Answer:` per heading, so ruling the target there would have discharged
this without anyone ruling it.

MAINT-26 found byte-identical output: the same root-strategy sha256 across two runs in separate
processes against a restarted server, zero per-action divergence, zero combos present in one run
only, and the same digest as a row recorded a day earlier. Phase 10 found the same preflop, diffed
node by node rather than checksummed.

What that does **not** settle is the run this phase would actually make. Both were a single spot.
A 1,755-flop run reaches the batch `REPORTS` route, which `docs/GTOPEN_SOLVER_NOTES.md` records as
README-sourced and never executed, and a long-lived batch process is exactly the case where
MAINT-26 measured process state to be worth 1.6x and recommended restarting the server between
solves. Determinism across two single solves is not determinism across two batches.

The contract keeps a fallback branch alive with no number in it: if a run is not byte-identical, an
accuracy target and the observed maximum divergence are recorded in place of the digest. Nothing in
the gate can tell those branches apart, because the gate must pass with no GTOpen and no network,
so whichever is written is what the repo believes.

Default: **prove it on the run that is committed, not on a proxy** - solve the committed
configuration twice in separate processes against a restarted server, diff the strategies rather
than compare checksums, and record the digest. If it is not byte-identical, the tolerance is a
number a human sets here rather than one an implementer picks, because it becomes the accuracy the
artifact claims.

Answer:

## 8. How the preflop line compresses into the postflop spot key

Reversibility: frozen-into-data

Filed 2026-09-08 by the stage-2 review, which found the key's grammar on no list at all. The
contract and decision 3 both call the key "the one thing this phase must get right before any
data" and say that changing what it can express re-derives every committed cell. That is this class
restated, and it is the same reason `verification/loop_policy.yml` gives for phase 12 not
auto-advancing. Phase 12 got thirty decisions for the preflop vocabulary; this had none.

Postflop strategy is range against range, so the key's action summary is a handle on a pair of
ranges rather than history for its own sake. The open part is what that handle keeps. The preflop
key already renders `CO:raise@2.5` with its size, and `t6/d100/CO/HJ:raise@2.5` is the whole
grammar; a postflop key could carry the preflop key entire, or a coarser class of it.

One sub-choice is not obvious and is easy to freeze by accident. The corpus's median open is
2.25bb and every corpus-derived key reads `@2.5`, because the lookup normalises a price to the
nearest one the artifacts declare and records the substitution. If the postflop key carries the
preflop raise size, it inherits that normalisation, and the ranges a spot was solved against are
then the ranges at the *substituted* price rather than the one the hand was actually played at.

Default: **carry the preflop spot key verbatim, sizes included, inside a postflop key that does not
begin with `t`**, so a postflop spot names exactly the preflop spot whose ranges it was solved from,
no compression is invented, and no existing reader mistakes one for the other. The prefix is not
cosmetic: `self_play_reference.py` recovers keys by taking any token that starts with `t` and holds
at least three slashes, and a verbatim preflop key inside a postflop one would satisfy that and be
returned as a preflop spot. An earlier draft of this default omitted the prefix and collided with
the contract criterion requiring that reader to return no postflop key.

And the substitution is **recorded on the committed spot, not computed at query time.** The preflop
`price_substitutions` field is a query-time field on the lookup result; naming it here without
saying which side of the line it falls on would leave the class itself ambiguous, since a committed
field is frozen data and a computed one is not. Committed, because the substitution is a fact about
which ranges the spot was solved against, and that is settled when the solve is committed rather
than when a hand is played.

Answer:

## 9. Whether flop bet sizes appear in the postflop spot key

Reversibility: frozen-into-data

Filed 2026-09-08 by the stage-2 review.

Within a flop, hero can face a 33% bet or a 75% bet, and those are different spots with different
ranges. The key either names the size, the way the preflop key names a raise size, or it names only
the action class and lets the size live in the spot's payload.

**The poker is not close, and the stage-2 poker review measured it.** Against a 33% bet a caller
needs 19.9% equity; against 75% he needs 30.0%. Minimum defence frequency goes from 75.2% to 57.1%,
and the bettor's maximum bluff share from 24.8% to 42.9%. A cell that merged the two would overfold
against small bets and overcall against large ones, and an opponent farms that by choosing his size
- which is the one exploit a bot with a fixed strategy cannot adapt away from.

**Two costs an earlier draft of this item claimed, and both are wrong.**

It said naming the size multiplies the spots by the menu. It costs **zero** bytes: facing-33 and
facing-75 are already distinct nodes in decision 6's own budget, because they are distinct nodes in
the tree. Naming only the action class would not buy a cheaper key, it would perform a lossy merge
of two cells that already exist separately.

It said naming the size ties the committed data to decision 11's menu, so a later menu change
re-derives every key. The tie is a property of the **data**, not of the key: a cell solved at
33/75 describes a spot facing 33 or 75 whatever the key says. Naming the size means a later menu
change makes the lookup **fail closed** on a size it holds no cell for; naming only the class means
the same change silently reinterprets every cell as though it answered the new size. The
size-named key is the safer one under a menu change, not the more brittle one.

Default: **name the size**, on the preflop key's own precedent, on the equity and defence numbers
above, and because it is the option that fails closed when the thing it depends on moves.

Answer:

## 10. Whether pot and effective stack appear in the postflop spot key

Reversibility: frozen-into-data

Filed 2026-09-08 by the stage-2 review.

A postflop spot is self-contained in its board, both ranges, pot, effective stack and sizes. Pot
and stack are determined by the preflop line at 100bb symmetric stacks, so under decision 8's
default they are recoverable from the key and putting them in it is redundant. They stop being
recoverable the moment the phase covers a depth other than 100bb or a table that is not flat -
which the preflop key already handles with its `d100` segment and its flat-table refusals.

Default: **leave them out of the key and carry them in the spot's payload, validated against the
preflop line they come from**, so a spot whose pot does not follow from its line is refused at
import rather than played. The `d` segment inherited from decision 8's verbatim preflop key is
what carries depth.

Answer:

## 11. The bet-size menu the committed solve is configured with

Reversibility: frozen-into-data

Filed 2026-09-08 by the stage-2 review, which found this on no list while decision 4's own second
qualification says it dominates the accuracy the phase publishes: the 0.3% bound is measured by a
best response walking the same tree, so "the abstraction error of a two-size menu is larger than
the target". **This item claimed to be decision 6's silent input and it is not.** The claim was that the budget
is priced at two or three actions so the step is worth 1.5x. The stage-2 review retracted its own
argument for it and the config bodies settle the part it could not: `config.ip@2315abe88f71` and
`config.oop@2315abe88f71`, the reduced pair, read `bet: "33 75"`, `donk: ""`, `raise: "2.5x"` **on
the flop**, identical to the pinned `2827d093808a` on both sides; they differ only at turn and
river, where `33 75` becomes `75`. Every converged row's observed flop root menu is the same three
actions - check, 33%, 75% - pinned and reduced alike, and the two-action menus in the record belong
to build-only ladder rows. So no flop raise or donk size changes, hero's committed flop node
carries three actions under options 1, 2 and 3, and **decision 6's byte budget does not move on
this ruling.**

What does move is hours, and something the retraction did not reach: **strategy quality on the
flop, even though only the flop is committed.** Hero's flop betting frequencies are solved against
the continuations available below them, and the reduced tree gives both players one turn and river
size instead of two. A flop-only artifact is therefore not insulated from the turn and river menu -
the same flop, solved above a coarser tree, is a different flop strategy. That is the real cost of
option 2 and of option 3's cheaper half, and it is not a cost decision 6 can price.

**Whatever is ruled here also freezes two things nobody raised until the stage-2 poker review,
because every measured config carries them.** `donk: ""` on all three streets means the
out-of-position player never leads - he checks or he does nothing - so hero's flop strategy is
solved against an opponent with no lead. And `add_allin: false` means neither player can jam. The
two omissions push hero's flop betting frequency in **opposite** directions, no donk letting hero
bet more freely in position and no jam capping what either can threaten, which is why the net sign
has to be measured rather than argued and why neither belongs in a ruling as an unstated side
effect.

**"The menu MAINT-26 measured" is not one object, and an earlier draft of this item said it was.**
The stage-2 review parsed all 55 committed rows and I re-derived it: of the **7 of 30** `group:
solve` rows that reached 0.3% of pot, **five** are `starting_pot: 16.0` - a 3-bet pot, at the pinned
menu `Check | Bet 33% | Bet 75%` with `max_raises: 2` - and the only two at `starting_pot: 5.5`, a
single-raised pot, carry `reduced-tree-not-cost-comparable` in their own row labels. An earlier
draft of this paragraph said eight and six, which counted the one `group: determinism` row, itself
the comparison between two repeats already counted; the report's own aggregate line says 7 of 30. **The pinned
menu has never been solved to target in a single-raised pot.** It was not slow; it was never
attempted, because that tree measures 21,282 to 21,715 MB of arena on all eight build rows against
the measuring script's 12,026 MB ceiling, and an arena over a box's RAM fails rather than slows.

That collides with decision 3, which is already ruled. A single-raised pot is the ordinary way to
see a flop, and the head of the corpus ranking decision 3 says to cover is dominated by them. So
the pinned menu plus decision 3's ruling produces a bot that refuses the head of its own coverage
list, which is the opposite of what either decision intends.

The choice, therefore:

1. **The pinned menu, 3-bet pots only.** Fully measured, and it abandons the commonest way to see
   a flop. Decision 3's head would have to be re-read as "the head of the 3-bet lines".
2. **The reduced menu everywhere.** The only menu with a converged single-raised-pot solve, so the
   coverage decision 3 wants is reachable. **It has the mirror image of option 1's gap and an
   earlier draft of this list did not disclose it**: no 3-bet row in the record uses the reduced
   config at all, not a solve and not a build, so this option is unmeasured on exactly the half
   option 1 is measured on. Its rows are also marked not cost-comparable, so every hour figure
   would be re-derived on it - the byte budget would not, per the preamble above, and an earlier
   draft of this line said it would.

   **The one thing this option turns on is unmeasured, and it is a poker claim, so it needs a
   number.** That a narrower turn and river tree changes hero's flop strategy is certain and is
   argued above. That the change is *worse*, by how much, and in which spots, is not established,
   and an earlier draft asserted the sign - "a coarser strategy in the spots that matter most" -
   with nothing behind it. The record cannot settle it: the only same-board pair, `matrix-01`
   against `matrix-03`, moves the menu, the pot from 16.0 to 5.5, the effective stack from 92.5 to
   97.5, both ranges and the SPR at once.

   **The measurement, corrected 2026-09-09 by the stage-2 poker review.** An earlier draft proposed
   running the reduced config on a **3-bet pot** and diffing against `matrix-01` or `matrix-02`.
   That comparison is clean and it answers the wrong question: 75% is near the geometric size in a
   3-bet pot, so restricting turn and river to it there is close to harmless, the diff would come
   back small, and it would be read as licence for the pot where the same restriction is largest.

   The experiment that settles it is the **single-raised** pot, floored on both sides so the pinned
   menu fits at all: floored pinned against floored reduced at one board, pot, stack and both
   ranges held and only turn and river moving. Both fit the ceiling - about 10,881 MB and about
   3,098 MB against 12,026 - so it is affordable, and it is the only comparison that measures the
   thing being ruled. It needs decision 12 to permit a floor, which is why **decisions 11 and 12
   are ruled together rather than in sequence.**
3. **A menu per line type**, pinned for 3-bet pots and reduced for single-raised. **This is the only
   option measured on both line types**, because it is precisely the pair that converged: the
   record's solve rows are pinned at pot 16.0 and reduced at pot 5.5 and nothing else. It is not
   measured everywhere, and an earlier draft of this line said "the only option with no unmeasured
   half", which is a clean bill no option can earn. **Rainbow is unmeasured in every half of every
   option**: the seven converged rows are six monotone and one two-tone, and the report's own
   texture line reads "rainbow 0, two-tone 1, monotone 6". Option 3's two halves are `9c8c7c` and
   `Kc7c2c`, monotone both times. Rainbow is 455 of the 1,755 classes and the expensive end.

   **And the poker runs the other way from the evidence.** A single geometric size that gets all-in
   over three streets is **66% of pot** at the 3-bet pot's SPR of 5.78 and **116%** at the
   single-raised pot's 17.73. So one 75% size is nearly right in a 3-bet pot and nowhere near right
   in a single-raised one, where three 75% bets leave 57.3 of a 97.5 stack behind. This option
   therefore puts **two sizes in the pot where one nearly suffices and one size in the pot where
   two matter most**, which is backwards from what its evidence recommends it for. Its cost is real and
   it is not an evidence gap - the artifact carries two abstraction levels with a seam between them
   that nothing in the repo would record, so a cell's strategy is coarser or finer depending on the
   preflop line and no field says which.
4. **Floor the ranges so the pinned menu fits a single-raised pot.** **This is a build, not a
   solve.** `rung-lineA-pinnedmenu-rangefloor0.01` is a `group: build` row; no solve row anywhere
   uses the pinned menu with a floored range, so nothing here says the solve converges or what it
   costs. This contract's own criterion applies to it - a route recorded UNRUN is not assumed to
   work. The margin is also thin where it is measured: 10,881 MB of arena against the script's
   12,026 MB ceiling is 90.5% of it, and solve rows post peak resident memory of 3,951 to 10,865 MB
   as a separate axis above the arena. It is the option a reader gravitates to, which is why its
   label has to be exact. The poker cost is decision 12's.

Default: **none, deliberately.** An earlier draft defaulted to "the menu MAINT-26 measured" on the
grounds that every affordability figure rests on it; that reasoning was sound and its premise was
false, since the figures rest on two different menus depending on the pot. Whatever is chosen,
the cost model is re-measured before decision 6 is answered rather than after, and a rainbow
single-raised-pot cell at the chosen menu is the one solve that would make this phase's arithmetic
real rather than scaled. The poker review's expected direction, from poker reasoning rather than a
repo measurement and flagged as such: a single 75% turn and river size pushes hero **away from the
33% flop bet and toward checking**, worst on dry rainbow high-card boards - the texture family
never once solved to target here.

Answer:

## 12. Whether the solve floors its input ranges, and at what weight

Reversibility: frozen-into-data

Filed 2026-09-08 by the stage-2 review, which found it to be the only measured way decision 11's
pinned menu fits a single-raised pot and therefore a load-bearing choice with no item.

Flooring means dropping every hand below a weight threshold out of the range before solving.
MAINT-26 measured it at 0.01: the single-raised-pot arena falls from 21,663 MB to 10,881 MB with
the action-node count **identical** at 2,347,996, because what shrinks is the number of hands and
not the shape of the tree. On the 3-bet line it is 3,726 MB to 2,385 MB.

**"A 68% truncation of the defending range" is a count, not a quantity of range, and an earlier
draft of this item led with it.** Recomputed here from the range strings the cost report commits,
for the single-raised-pot out-of-position range `config.range_oop@717f36499fb4`: the 0.01 floor
deletes 99 of its 162 labels, which is **878 of 1,274 combos, 68.9%** - and **0.199% of its
weight**. The heaviest hand deleted is `87s` at 0.0099. The bulk sit at 0.0002 to 0.0005 and
include `32o` and `72o`, which are not defends; they are residue from the preflop solve, hands the
solver left a rounding of a percent in rather than hands the defender holds.

So the poker answer, from the stage-2 poker review and reproduced here, is the opposite of that
draft's: **flooring at 0.01 removes two hundredths of one percent of the range hero must beat.** It
is close to free in the units that matter, and the units argument the notes give for it is still
the wrong argument. The floor value is also not delicate: the weights straddling it run
0.0099, then 0.0114, then 0.0249, so a gap sits just above the threshold.

`docs/GTOPEN_SOLVER_NOTES.md` argues the 2.0x is "close to free" because "two thirds of the grid
sits below a 1% weight, far under the resolution of a 0.3%-of-pot target". Treat that as an
argument rather than a measurement, and note that it compares a **weight** threshold to an
**exploitability** target - two percentages in different units with no conversion between them,
which is exactly the shape filed as `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS` after the same
reasoning was caught in this file at stage 1. It may well be right. Nothing has measured it.

One constraint is not a judgement: the floor must be class-level. A single suit-specific weight
anywhere in either range collapses the suit-isomorphism group to the identity and forfeits the
entire saving on every board that is not rainbow, which is what
`EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` records.

**But flooring an unsmoothed export has a cost this item never named, and it is a poker cost.** The
floor does not only delete residue; it cuts a rank-ordered block out of the defender's pair ladder,
and differently in each pot type. Measured here over every committed range:

- The **3-bet-pot** out-of-position ranges (`568ae7b39c57`, `b6fe98063c86`) keep every pair after a
  0.01 floor **except 44**.
- The **single-raised-pot** out-of-position ranges (`1f1afe475a98`, `717f36499fb4`) keep only
  `55 44 33 22`, deleting `TT 99 88 77 66` - the better pairs, while the worse ones survive.

Neither is poker. Both are the preflop solve's own indifference frozen into the postflop input, and
they are the same pair-ladder inversion phase 14 accepted and published a cost for, now arriving
where it changes what hero is solved against. `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`
is the entry that owns it, and the floor is what makes it visible rather than what causes it -
unfloored, those pairs are present at a weight that does nothing.

Default: **floor, class-level, at 0.01** - reversed on 2026-09-09 from "no floor" after the
stage-2 poker review measured the mass. The earlier default was chosen because this repo fails
closed and no floor requires no action to be safe; that reasoning was right in form and rested on
the 68% figure being a quantity of range, which it is not. Class-level remains a constraint rather
than a choice, because one suit-specific weight collapses the isomorphism group.

The condition on that default: the pair ladders above are stated as a known defect of the input,
not repaired by this phase, and the report publishes which pairs each committed range holds so a
reader can see what hero was solved against.

Answer:

## 13. Whether this is one phase

Reversibility: frozen-into-data

Filed 2026-09-09 by the stage-2 independent decisions review, which observed that nothing asked -
and that phase 14 carried exactly this item, as its own decision 21, classed `frozen-into-data` and
described there as "a structural question rather than a poker one". Taylor answered it "split it"
on 2026-08-31, and phase 17 exists because of that answer.

The shape of the problem. Of the eight other open items, **three define a format**: how the preflop
line compresses into the key (8), whether flop bet sizes are in it (9), whether pot and stack are
(10). **Five define a data campaign**: the accuracy target and what happens to a cell that misses
it (4), the encoding and the size budget (6), reproducibility (7), the bet-size menu (11), the range
floor (12).

This repo's ordering rule is quoted in decision 3 and it is this file's own words: "What is *not*
cheap later is the spot key itself. Adding spots at a fixed key is additive; changing what the key
can express re-derives every committed cell, which is why phase 12 sits ahead of phase 14 and why
the ordering rule is format before data." **The precedent that sentence cites is a phase boundary,
not a stage boundary.** Phase 12 set the vocabulary and closed; phase 14 committed the chart against
it. Ruling both halves in one sitting means a format mistake surfaces after the artifact has been
committed against it, which is the exact cost that sentence names.

What forced the question in phase 14 was mechanical - five contract lines over a 300-line cap. A
decision list has no cap, so nothing forced it here, and this phase has twice phase 14's open
frozen count.

**The argument against splitting is weaker than an earlier draft of this item claimed, and the
measurement is fifty lines above.** That draft said decision 9's key would name sizes decision 11
chooses, so the format half is not independent of the data half. But all four of decision 11's
levers carry the **same flop menu**: the appendix gives both configs as `bet: "33 75"`, `donk: ""`,
`raise: "2.5x"` on the flop, identical on both seats, differing only at turn and river, and the four
levers are combinations of those two plus a floor. So among the options actually on the table,
decision 9 does not wait on decision 11. The coupling bites only if some lever widens the *flop*
menu, and none does.

**The real costs of splitting, which that draft omitted, and one of them is the precedent's own
outcome.** Phase 17 is `status: future` in `phase_status.yml` and has never been started, so what
phase 14's split has produced to date is that the deferred half has not happened. An earlier draft
of this item said "phase 17 exists because of that answer" and stopped at the cheerful reading. And
the process cost is real: a split is a second contract under the 300-line cap, a second decision
list, a second gate, a second audit packet and a second human gate, so Taylor is asked twice and the
second ask waits on the first phase closing.

**One measured fact cuts the other way and is stated here rather than left out.** The contract is at
284 of 300 lines and its Scope commits it to amending three criteria after stage 3. If this stays
one phase, the menu and floor rulings land in that same amendment, so up to five rulings share
sixteen lines - which is the arithmetic that forced phase 14 to ask this question, five lines over
its own cap.

Default: **none.** Both answers are defensible and the choice is about how much is committed before
anything is checked, which is a judgement about risk appetite rather than about poker or arithmetic.
It is `frozen-into-data` on phase 14's own reasoning: not because a split writes anything to disk,
but because not splitting is what allows an artifact to be committed against a format nobody has
built against yet, and that artifact is the thing later phases are measured on.

This item was raised by the stage-2 reviewer, and an earlier draft of it was written by the
coordinator with five arguments for splitting and one against, closed in its own sentence. The
reviewer flagged that itself and declined to answer the question it had raised.

Answer:
