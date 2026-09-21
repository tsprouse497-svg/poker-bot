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

**One measurement is worth taking before any of this is ruled, and it is one solve.** A
0.3%-of-pot target gets *which* hands bet right; what a reader takes off a flop chart is **how
often**, and mixed frequencies settle well after exploitability does. Nothing here has solved a
cell deep and diffed the frequencies - both determinism runs stopped at 240 iterations - so this
phase would commit a frequency table nobody has checked is one. Take one cell to several times 240
iterations and diff the frequencies. If they have moved, the rulings below are being made about
noise with a good accuracy number on it. Decision 7 carries the detail.

**4. Exploitability target, and a cell that never reaches it.** Target 0.3% of the starting pot,
and commit a cap-bound cell with its achieved percent as a floor, or refuse it. The scale is what
makes this consequential: **23 of 30 measured rows missed the target** and rainbow never reached it
at all. Rainbow is 455 of 1,755 classes but **39.8% of actual flops**, because rainbow classes
carry 19.3 boards each against monotone's 4.0 - so refusing risks a trainer that refuses **two
flops in five**, and the plainest ones. The converged evidence covers 5.18% of flops. Default:
0.3%, and refuse.

**6. How the committed artifact is encoded, given that it does not fit.** A budget, not a menu: the
**15.04 MiB of headroom** left under the 20 MiB cap affords about six node-line units at one byte per
weight, and the affordable products are 6x1, 3x2, 2x3, 1x6 and everything under them. But a
complete flop is about **five** hero decision nodes under the ruled menu, so six units is **one**
preflop line at full flop depth, not the two 3x2 suggests. And **which** nodes is a poker question:
a student's leaks are in facing a bet and facing a raise, not at the flop root, so root-only spends
the budget on the most published number in poker. Six levers, none fail-closed.
**No default** - an answer must fix the encoding, the per-spot byte budget including provenance, and
the number of preflop lines, and the six units are quoted at an encoding the answer itself chooses.

**7. Whether the committed solve is reproducible, and what is recorded if not.** Byte-identical was
measured on one spot; a 1,755-flop run reaches a route recorded unrun.
Default: prove it on the committed configuration, and a human sets the tolerance if it is not.

**8. How the preflop line compresses into the postflop key.** Verbatim, or a coarser class. There
are **two** price substitutions: recording that a spot was solved at `@2.5` is honest, but a hand
actually opened to 2.25bb querying that cell meets a defender who is really wider and weaker, so
hero c-bets too little, and an SPR 10.3% higher than the cell assumes. Nothing validates that,
because decision 10 checks the payload against the line rather than the query. Default: verbatim,
sizes included, inside a key that does not begin with `t`, substitution recorded on the spot.

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
Rainbow is unmeasured in all four. Whatever is ruled also freezes **no out-of-position probe on the
turn or river**, which pushes hero's flop betting up. Jams are **not** absent, contrary to two
earlier drafts: any bet reaching 85% of the stack behind is snapped to a stack-off regardless of
`add_allin`. On the flop that never fires under either menu, so a committed flop cell's actions are
what its menu says; the deepest 3-bet flop line sits 3.9% of stack under the line, so four config
values decide it and are pinned on the cell. **No default**, it
collides with decision 3 already ruled, and **rule it with 12** - the settling experiment needs a
floor.

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

One consequence of decision 1 that no ruling below changes and a reader should have: because a flop
bet's value at this depth is largely the leverage it creates later, and this artifact's turn
refuses, **no winrate or EV figure may ever be reported over it**. The training use survives - a
refusal voids the hand rather than playing on - but the number does not exist.

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

**Annotated 2026-09-09 by the stage-2 poker review: the seam is worse than "a visible seam", and it
bars a claim.** At the single-raised pot's SPR of 17.7 a flop bet's value is largely the leverage it
creates on later streets, so a betting frequency solved above a full turn and river tree is not the
right frequency for an agent whose turn refuses. The training use survives, because a refusal voids
the hand rather than checking it down, so the bot never plays out the strategy it did not solve for.
What does not survive is measurement: **no winrate or EV figure may ever be reported over this
artifact**, because the hands it would be computed from are the ones that ended at the refusal.

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

**Annotated 2026-09-09 by the stage-2 poker review: the ruling is poker-correct and its test has a
poker-shaped hole.** The contract requires a test proving every *board* maps into exactly one
canonical class. A hand permuted inconsistently with its board passes that test and is invisible to
exploitability, while serving a no-draw strategy to a flush draw on a two-tone flop - suit
isomorphism is exact only if hero's cards are permuted by the same map as the board. The check is
one line: a flush-draw combo must not receive a strategy identical to the same ranks without the
draw.

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

**Annotated 2026-09-10 by the stage-3 review; method only, the ruling is untouched and is not
re-ruled.** This ranking orders lines by how often the corpus reaches them, and decision 10's
measurement shows that is the wrong quantity. A 3-bet line costs the same 45 to 85 days as a
single-raised one and can serve only 47.1% of its arrivals against 99.0% for a single-raised line,
because the committed chart's one 3-bet price sits below the corpus median. **Sort on servable
arrival frequency.** The derivation is in decision 10; the entries are
`THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` and
`ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE`. This pointer exists because the ranking
is computed at stage 6 by someone reading this item, not that one.

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

**The exposure is 39.8% of flops, not 25.9%.** Rainbow is 455 of 1,755 classes, which is 25.9% of
classes and where an earlier draft of this file stopped - but rainbow classes carry 19.3 boards
each against monotone's 4.0, so rainbow is **8,788 of 22,100 boards, 39.76% of flops**, brute-forced
here rather than argued. Refusing a cap-bound cell while rainbow has never reached target risks a
flop trainer that refuses **two flops in five**, and the plainest ones. The same conversion cuts
the other way on the evidence: the converged rows are six monotone and one two-tone, so the
evidence base covers **5.18% of flops**, on the texture that generalises worst.

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

**Ruled by Taylor, 2026-09-10, in three parts with three different provenances**, separated here
because the stage-3 review found an earlier draft of this item's `Answer:` bracket presenting all
three as his:

1. **The target, 0.3% of the starting pot** - confirmed by Taylor ("i think for 4, going with .3 is
   pretty reasonable here") against the 0.1% to 0.5% band study work normally uses. That band is
   poker knowledge, not a measurement taken here.
2. **The iteration cap, 1,200** - chosen by the coordinator under an explicit delegation: "i'm fine
   with you just making the final call here on good volume to start on". A delegated number, not a
   human ruling and not a default the coordinator helped itself to.
3. **What happens to a cap-bound cell** - a coordinator recommendation that Taylor accepted ("i'll
   go with your rec on 4"): commit it if its achieved error is under 1% of pot, refuse it above.

**Why 1,200.** Recomputed from the cost notes rather than quoted: the **five** distinct converged
cells - seven rows, of which `matrix-02` and both determinism runs share one config - reached 0.3%
of pot at 220 to 260 iterations, and the recorded convergence curve for a three-bet cell reads
11.84% of pot at 20 iterations, 3.55% at 40, 0.87% at 100, 0.33% at 220 and 0.295% at 240. The late
local decay exponent is 1.0 to 1.3, so halving the error from 0.3% costs roughly 1.9x the iterations
and a tenfold improvement roughly 5.9x to 10x. 1,200 is about 5x the observed count, which leaves
room for a rainbow board needing several times a monotone one, and a cap in the tens of thousands
would buy a fraction of a tenth of a percent for an order of magnitude of compute.

**What the campaign costs, corrected 2026-09-10 by the stage-3 review.** An earlier draft of this
paragraph said "on the order of 10 days per preflop line" and never priced the ruled cap at all.
Both are fixed here; every figure is the coordinator's multiplication, stated as rough, and is
exactly the multiplication the cost notes decline to make.

- Per iteration, floored single-raised tree: 2,347,996 action nodes x 919 hands x 1.7 to 2.0 ns =
  **3.67 to 4.32 seconds**, so about 16 minutes per flop at 240 iterations. Both of those survive.
- At 240 iterations over 1,755 flops: **17.9 to 21.0 days per preflop line**, not 10.
- That rate is **monotone only**. Re-normalised, every rainbow row in the record reads 7.34 to 8.71
  ns and the converged two-tone cell reads 4.28. Applying the cost notes' own 2x pooled deflation
  gives **36 to 42 days**; weighting the notes' texture factors and iteration counts over the 455
  rainbow / 1,014 two-tone / 286 monotone classes gives **about 56 to 66 days** at a fixed rainbow
  iteration count. That band's width is the wrong uncertainty and the stage-3 review said so: the
  dominant unknown is how many iterations a rainbow board needs, and letting it range over this
  item's own 305 to 760 extrapolation widens the honest band to **about 45 to 85 days**. The 56 to 66
  figure assumed 500 without declaring it.
- **The cap's own worst case, which the record owed and did not state:** if every cell ran to 1,200
  iterations, 1,755 flops is **89 to 105 days per preflop line** at the monotone rate, before either
  deflation.

**How those two figures coexist**, since an earlier draft asserted both that the cap does not bind
and that the campaign is bounded by it. A cell that converges never sees the cap: it stops at 220 to
260. The cap prices the **tail** - cells that do not converge - and the record's one rainbow row,
6.23% of pot at 30 iterations, extrapolates to target at roughly 305 to 760 iterations, so the tail
is expected to be small rather than measured to be. So the honest reading is that the campaign cost
sits near the texture-weighted 56 to 66 days with a tail bounded above by 89 to 105, and what forces
a smaller flop set or fewer preflop lines is the campaign rather than this cap.

**All of the above is CPU-engine arithmetic on an Apple M4, 10 cores, 34.4 GB RAM.** Re-derive the
seconds per iteration on the ruled menu and on the machine actually used before anyone plans a run
against these figures; nothing in the record uses the `66 125` turn and river sizes, and the machine
note below decision 11 records that solving moves off this hardware.

Answer: [Target confirmed by Taylor 2026-09-10; cap delegated by him to the coordinator; cap-bound
rule a coordinator recommendation he accepted - see the three-part split above] **Target 0.3% of the
starting pot with a 1,200-iteration cap; record the achieved percent and the iteration count on every
committed spot; commit a cap-bound cell whose achieved error is under 1% of pot and refuse one above
it.** This is a third option the item did not offer: neither commit-every-floor nor
refuse-every-floor, but a floor with a stated worst case.

**1% is not a study-quality figure and this file must not imply it is.** It is twice the upper edge
of the 0.1% to 0.5% band stated above, chosen as an outer bound on how wrong a played cell may be
rather than as a target anyone would aim at. An earlier draft called it "the outer edge of the band
study work uses", which contradicted the band this same item states.

**What this accepts.** A cell at 0.9% is three times the target and it plays, so the committed set
is not uniform in accuracy and every report and packet states the distribution: how many committed
cells sit between 0.3% and 1%, and where. **No packet may state an accuracy for the committed solve
as a whole** - the contract forbids exactly that in the criterion reading "No report or packet may
state an accuracy for the solve as a whole", and an earlier draft of this answer
asserted a "headline accuracy of 0.3%" in direct breach of it. 0.3% is what was aimed at, the
per-cell recorded percent is what was reached, and 1% is the worst a played cell may carry.

**One thing this ruling wants that nothing in the phase yet builds.** Telling a "never solved" refusal
apart from a "solved and over 1%" refusal is impossible at query time, because neither cell is in the
artifact: both are the same miss. Distinguishing them needs a committed list of attempted-and-rejected
boards with their achieved percents, which no contract criterion requires. Either a criterion is
added at stage 4 or the inventory pools the two causes and says so; filed rather than asserted.

## 5. Whether the pot-odds river call ships alongside

Reversibility: runtime-reversible

`POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK` calls a river bet when equity against the full unseen deck beats the price. It needs no solved data and invents no constant: equity is `(wins + ties/2) / 990` from the enumeration `hand_cannot_lose` already runs, and the price comes off the query.

A uniform unseen deck flatters hero, so this makes the bot over-call as the mirror of its current over-folding. Under the flop-only default it is also the only thing that acts on a river at all.

Default: build it, behind an explicit flag, and report the frequency it fires rather than claiming it is correct. It is runtime-reversible because no committed data records it; it is a rule the query evaluates.

Answer: [Confirmed by Taylor, 2026-09-09] Take the default. This item is `runtime-reversible` and
would have proceeded on its default regardless; the confirmation is recorded so a later reader does
not read the empty bracket as an unasked question.
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

**Which nodes to spend the budget on is a poker question, not an arithmetic one**, and the
stage-2 poker review put it more sharply than the seam argument does. A student's leaks are not at
the flop root: c-bet frequency is the most published number in poker and the easiest thing to learn
elsewhere. The leaks are in **facing a bet** and **facing a raise**. So lever 4, root only, spends
the whole budget on the cheapest decision to learn anywhere else, and 3x2 is not equivalent to 6x1
in usefulness even where it is equivalent in bytes.

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

**Ruled by Taylor, 2026-09-10.** An earlier draft of this block ruled **git LFS** and the stage-3
review found that unworkable: `scripts/check_file_sizes.py:48-54` sums `rglob` per entry so the
20 MiB `data/artifacts` cap still applies to a nested path, and an LFS blob is a ~130-byte pointer
until a clone fetches it, which puts committed data behind a network fetch against `AGENTS.md`'s
offline-first opening and the contract's own "The gate must pass with no GTOpen, no Rust
toolchain, no network and no fetched solve". On an
unfetched clone the byte-budget criterion would pass vacuously against a pointer. That draft is
withdrawn. LFS is not used and no `.gitattributes` filter is added.

**What was ruled instead** - Taylor, 2026-09-10: "The real solve can live in something like object
storage that makes sense, and we can leave the cap. Basically, just grab a couple of flops to run
some initial testing on before going for it."

1. **The cap does not move.** `DIRECTORY_BYTE_LIMITS` is untouched: `data/artifacts` stays at
   20 MiB and keeps guarding the preflop chart. This item's premise - the artifact does not fit -
   is answered by not putting the artifact there rather than by raising the number, and the
   `rglob` behaviour above is why a nested exemption was never available.
2. **The full solve output lives in object storage** (S3 or Cloudflare R2), outside git.
3. **The repo commits an index, not the artifact**: one entry per solved spot carrying its key, its
   content digest, its achieved percent and its iteration count, plus the provenance decision 11
   requires and a fetch script. **Sized correctly here after the stage-3 review found an earlier
   draft understating it by 5x to 48x.** That draft counted 1,755 *boards* and priced only
   provenance. Entries are per **spot**, not per board: this file measures about five hero flop
   decision nodes at line 601 and decision 9 makes facing-33 and facing-75 distinct keys, so a line
   carries on the order of 8,775 entries. And the omitted field was the largest one, the key itself:
   the committed preflop keys run 14 to 78 characters with a median of 45, and a postflop key adds
   board, pot and stack segments for about 75. At roughly 130 bytes an entry with the repo's own
   16-hex digest, or about 230 with a full sha256 plus decision 11's four pinned config fields,
   that is **1.14 to 2.02 MB per preflop line**, so the 15,774,195 bytes free under the existing cap
   holds an index for about **8 to 14 lines**. The same order as the coverage this phase can afford,
   not comfortably inside it - so the index is a real constraint to design against. **The digest
   width is not a byte decision and stage 4 must not treat it as one.** The 16-hex precedent in this
   repo is a *determinism* digest, compared against a rerun of the same computation; this one
   authenticates an object fetched from storage the repo does not control. Against accident 64 bits
   is ample - about 123,000 objects gives a collision probability near 4e-10 - and against deliberate
   substitution it is about 2^32 work, which is not a security margin. So the choice is full sha256
   at 1.75x the index size, or a stated decision to authenticate against accident only.
   Raised by the stage-3 review outside its brief.
4. **The committed sample is three flops - ruled by Taylor 2026-09-10**, and recorded as an item
   rather than handed to a builder. An earlier draft said "a couple of flops, chosen at stage 4",
   which the stage-3 review correctly called a `frozen-into-data` choice with no item: the sample is
   the only postflop data the gate can ever see, so it is a fixture later phases are measured
   against.

   **It cannot be two, and the reason is poker rather than arithmetic.** The phase's entire
   converged evidence is six monotone rows and one two-tone, and
   `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` says monotone generalises
   worst, so a two-monotone sample would reproduce that defect inside the one artifact the gate
   measures. Rainbow is the expensive end and has never been solved to target, which is precisely
   why it must be in the sample rather than only in the fetched bulk.

   **Both splits are ruled here rather than at stage 4**, because stage 4 authors the tests and
   stage 5 freezes them. Stage 4 picks the specific board inside a split and nothing else, and it
   picks **one** of the three: the assignment below names `Kc7d2h` and `9c8c7c` outright, because
   each of those two is already owed as a measurement and the sample board and the measurement are
   the same solve. Corrected 2026-09-10 by the stage-3 fold-in review, which found this sentence
   and the assignment forty lines below it describing different phases.
   An earlier draft of this item said the ruling "constrains suit and leaves rank open"; that is
   superseded by the assignment below, which rules both.

   **Amendment, 2026-09-15, two rulings by Taylor.** Both were forced by the decision 8 amendment,
   which gave the preflop raiser a flop spot and so added a fourth situation the sample has to
   carry.

   *A fourth file is allowed.* One file is one cell - `test_the_three_boards_are_the_ruled_three`
   reads one `board` per file - so three files are three situations, and the frozen tests now need
   four: a caller first to act producing a bet, a caller facing a bet producing a raise, a two-tone
   board separating a flush draw from the same ranks without one, and a cell where hero was the
   preflop raiser, which is the c-bet. **Still three flops.** The fourth file is a fourth situation
   on a board already in the sample, not a fourth board, so both splits above stand untouched and
   `test_the_sample_holds_exactly_three_flops` becomes a count of boards rather than of files.

   *The boards are committed as canonical representatives.* `Kc7d2h` canonicalises to `Kh7d2c` and
   `8h8d3h` to `8c8d3c`; only `9c8c7c` is its own. A cell's hand classes are written in
   representative space, so a board written in a different dressing makes one file describe the
   same flop two ways, and pairing a class with it hands hero a card that is already on the board -
   `StrategyQuery` refuses it as a duplicate. Taylor's ruling: **the ruling named the flops, not
   the suit letters.** The same three flops are committed, in the representative dressing, and
   `THE-RULED-SAMPLE-BOARDS-ARE-NOT-THEIR-OWN-REPRESENTATIVES` is answered by taking its first
   disposition.

   **Rank structure and suit texture are independent, so three boards carry three of each.** An
   earlier draft of this item treated the five never-reached rank structures as competing for three
   slots and then named two rainbow boards among the three, contradicting its own suit split in the
   same paragraph. The stage-3 review brute-forced all 22,100 boards and the real shape is a 3x3
   assignment with exactly one forbidden cell: paired-rainbow is 1,872 boards (8.47%),
   paired-two-tone is 1,872 (8.47%), and **paired-monotone is impossible** - two cards of one rank
   cannot share a suit. Trips are always rainbow (52 boards, 0.24%).

   **The rank axis is chosen for defect detection, not from the solve-cost list.** A first version
   of this assignment took its rank structures from the solver notes' never-reached list, and the
   stage-3 poker review showed that is the wrong list for this purpose: that list records where
   solves were expensive, and the fetched bulk covers those anyway. The sample exists so a human can
   see a wrong strategy, the contract is explicit that no gate check can, and **a human sees a
   defect only where he holds an expectation.** Brute-forced over all 22,100 boards, the first
   version spent a slot on monotone-dry-low - 112 boards, 0.51% of flops, the rarest of the fifteen
   suit-by-rank cells - and contained no unpaired high-card board at all, which is the 40.54% rank
   family and the only one with a published number to check a strategy against.

   **The ruled assignment.** The suit split is unchanged; the rank axis is dry-high, paired,
   connected, with paired necessarily off the monotone slot:

   - **rainbow, dry-high** - the family a reader can actually check, and the texture never solved to
     target. Take `Kc7d2h`, which is the single rainbow row the whole 45 to 85 day campaign
     estimate extrapolates from, so committing it also puts a number under the phase's own cost
     model.
   - **two-tone, paired** - paired and trips are 17.18% of flops and the solver notes single paired
     out as "a structural gap rather than a suit one", so it takes a slot rather than waiting for
     its own coverage. An earlier draft left it out on the reasoning that it wants separate
     coverage, which runs backwards for a sample: the fetched bulk covers every paired board anyway,
     and the sample exists so a defect is visible at all. Two-tone is 55.06% of flops, the modal
     texture, so the modal texture carries the structural gap.
   - **monotone, connected** - forced unpaired by the arithmetic above, and connectedness is where a
     flop's polar branch is built. Take `9c8c7c` in the single-raised pot, which is `matrix-03`:
     already converged, digest recorded, at the reduced menu. **Re-solving it at the ruled menu is
     the controlled menu experiment decision 11 defers to stage 6** - same board, pot, stack and
     ranges, only the menu moving - so half of that experiment is already paid for and the sample
     board and the experiment are the same solve.

   Two of the three boards therefore come out of measurements this phase already owes, which is a
   property the first version did not have.

   **Knowingly left out: disconnected-low, and ace-high connected.** Disconnected-low was in the
   first version and is dropped deliberately - at monotone it is 0.51% of flops and it is the cell a
   reader has least to say about. Ace-high boards are 21.74% of flops and ace-high *connected* a
   small subset of that; a fourth board would be needed and the sample is three. Both named rather
   than omitted silently, on decision 3's own principle that a refusal names a line that was
   excluded rather than one that was forgotten.

   **And the solve-cost list is only partly covered, which is a different question from the one
   above.** The solver notes list rainbow-dry, rainbow-connected, paired, ace-high connected and
   disconnected-low as never reached, and two of those name a suit as well as a rank pattern. This
   sample takes rainbow-dry as a cell, so the most expensive never-reached cell is committed;
   rainbow-connected is not, because the connected slot is monotone. Paired, which the notes list
   unqualified, is covered here at two-tone. Stated so a reader can see which of the five failures
   the sample touches rather than reconstructing it.

   **What the sample costs.** 1.06 to 1.85 MB across the 8 to 14 lines the index affords, 7 to 12%
   of the free bytes - a figure across all lines, not per line, and it belongs in the same budget as
   item 3's index rather than beside it.

   **One imbalance worth stating.** A third of the sample is monotone, which is 5.18% of flops and
   where six of the seven converged rows already sit, while two-tone at 55.06% gets the same single
   slot. That is deliberate - the sample is chosen for structural spread rather than for frequency,
   because a frequency-weighted sample of three would be two two-tones and reproduce the blind spot
   the sample exists to remove - but a reader comparing the sample to the flop distribution should
   not have to work it out.
5. **The gate runs on the sample.** The tests and the byte-budget criterion measure the three
   committed flops and the index, so they pass offline with no GTOpen, no network and no fetched
   object. Nothing the gate checks is a placeholder.
6. **The encoding**, stated once and correctly, because an earlier draft named the two-action
   encoding and priced the three-action one: the lean JSON measured in this item - action names
   hoisted to one array, hero's classes as a parallel array in canonical order, three-decimal
   floats - at **two free weights per class for a three-action node**. That unit is 2 x 7,740,095 =
   15,480,190 bytes = 15.48 MB = 14.76 MiB per hero decision node per preflop line, and the
   per-spot budget adds the 24 to 120 bytes of provenance the item prices separately at line 610.
   Two independent builds agreed to within 38 bytes on the two-action figure, which is why this and
   not a new format is the budget's basis.
7. **The number of preflop lines stays an output, not a choice.** Cover as many as the campaign and
   the index together afford, taken in decision 3's already-ruled corpus order, and record the
   covered set explicitly so a refusal names a line that was excluded rather than one that was
   forgotten. **Both constraints bind and an earlier draft of this item said only one did**: item 3
   measures the index at 8 to 14 lines, and decision 4's campaign at 45 to 85 days a line puts its
   own limit in the same range. Whichever is smaller decides, and neither can be assumed to be the
   campaign.
8. **A third refusal cause arrives with this ruling and the record must carry it.** Decision 4 names
   two - never solved, and solved but over 1%. Object storage adds **in the index, under 1%, not
   fetched on this machine**, and it is the only one of the three a query can name precisely, since
   the index says the cell exists. On a fresh clone it is also the common case: 1,752 of 1,755
   classes. Reports must not pool it with "never solved", which would understate coverage by the
   whole artifact.

**What this accepts, and it is a real reduction in what the phase promises.** What the repo commits
is an index plus a sample, not the solved artifact. So this phase's committed data is no longer the
thing the bot plays in full, and a later phase measuring "the committed chart" has to say which it
means. The contract's criteria that speak of the committed artifact and its byte budget must be
amended at stage 4 to say index-plus-sample, and that amendment is part of the three the Scope
section already owes. A reader who wants the whole solve fetches it; a reader who wants to verify
the gate does not have to.

**Two smaller corrections the review made to the withdrawn draft, kept because the figures survive.**
The lean unit is 64.6 nodes per decimal GB and 69.4 per binary GB - this file states units once by
its own rule, and the earlier "about 65" said neither. And the illustration that put ten hero flop
decision nodes in a line contradicted this file's own measurement of about five at line 601, which
decision 11's ruling leaves unchanged since the flop menu is still `33 75`.

Answer: [Ruled by Taylor, 2026-09-10] **The solve output lives in object storage outside git; the
repo commits an index plus a committed sample of a couple of flops; the 20 MiB `data/artifacts` cap
does not move; no git LFS.** Encoding is the lean JSON at 15,480,190 bytes per three-action hero
decision node per preflop line plus 24 to 120 bytes of provenance a spot, and the covered line count
is an output of decision 4's campaign cost rather than a number chosen here. The accepted cost is
that this phase's committed data becomes an index plus a sample rather than the artifact the bot
plays, which the contract must be amended to say.

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

**The measurement this phase most needs is not reproducibility, and the stage-2 poker review named
it.** A 0.3%-of-pot solve does not get *which* hands bet wrong. What a reader takes off a flop chart
is **how often**, and mixed frequencies settle well after exploitability does. Nothing in this repo
has solved a cell deep and diffed the frequencies; both determinism runs stopped at 240 iterations.
For a training artifact the frequencies **are** the product, so as things stand this phase would
commit a frequency table nobody has checked is one.

**The check is one solve and it is the cheapest open measurement in the phase: take one cell to
several times 240 iterations and diff the action frequencies against the 240-iteration version.**
If they have moved materially, this commits noise carrying a good exploitability number, and no
amount of board coverage repairs that. It belongs before a ruling rather than after.

Default: **prove it on the run that is committed, not on a proxy** - solve the committed
configuration twice in separate processes against a restarted server, diff the strategies rather
than compare checksums, and record the digest. If it is not byte-identical, the tolerance is a
number a human sets here rather than one an implementer picks, because it becomes the accuracy the
artifact claims.

Answer: [Ruled by Taylor, 2026-09-10] Take the default, **minus the pre-agreed tolerance**. Solve
the committed configuration twice in separate processes against a restarted server, diff the
strategies rather than compare checksums, and record the digest. If it is not byte-identical, the
phase **halts and Taylor is asked** rather than falling back to a tolerance: a number nobody has a
basis for would become the accuracy the artifact claims. The fallback branch in the contract is
therefore a halt, not a value.

The frequency-convergence diff this item names as the cheapest open measurement is unaffected by
this ruling and is still owed.

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

**There are two price substitutions and an earlier draft of this item addressed only one.** The
committed one is honest provenance: a spot recorded as solved at `@2.5` ranges says what it is. The
**query-time** one is not bounded by anything. A hand actually opened to 2.25bb looks up an `@2.5`
cell, and the two differ in more than a label:

| | pot | effective | SPR | geometric size | big blind's price |
|---|---|---|---|---|---|
| `@2.5`, what the cell holds | 5.50 | 97.50 | 17.73 | 115.8% | 27.3% |
| `@2.25`, what was played | 5.00 | 97.75 | 19.55 | 121.1% | 25.0% |

Two channels, and because the corpus's median open is *below* 2.5 both run the same way on every
hand, so neither averages out. The **range** channel is the larger: 2.25bb is a cheaper price, so
the real defender is wider and weaker than the range the cell was solved against, and hero
therefore c-bets and bluffs **too little**. The **geometry** channel is smaller and opposite in
character: the real SPR is 10.3% higher than the cell assumes, so the cell reads as too willing to
commit.

Neither is visible to decision 10's validation, which checks the payload against the **line** the
spot names rather than against the query being asked - so the artifact is checked against itself.
And the preflop chart's nearest-price tolerance does not transfer: preflop, 0.25bb barely moves a
range, while postflop the same 0.25bb moves the pot, the SPR and both ranges at once.

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

Answer: [Ruled by Taylor, 2026-09-09] **Verbatim.** Take the default: the postflop key carries the
preflop spot key entire, sizes included, inside a key that does not begin with `t`, and the price
substitution is recorded on the committed spot.

The query-time substitution this item raises is **not** settled by that ruling and is not closed by
it. `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` carries it: a hand opened to 2.25bb
served an `@2.5` cell meets a defender who is really wider and weaker, so hero c-bets and bluffs
too little, and decision 10's validation cannot see it. Verbatim keys make that visible rather than
fixing it, which is the honest reading of what was ruled.

### Amendment, 2026-09-15: a preflop *spot key* cannot name the raiser's flop

**What was not true.** The default above says "carry the preflop spot key verbatim" and the ruling
took it. A preflop spot key names a decision hero is **about to make**; every flop is reached with
the preflop betting closed. So the only seat a postflop key could name was the one whose last
preflop decision was facing a bet - the caller. Measured against `spot_key.py` directly: hero `BB`
facing a 2.5bb button open keys as `t6/d100/BB/BTN:raise@2.5`, while hero `BTN` after that call is
refused with "BTN already acted and faces no later raise, so the betting round is closed", and hero
`BTN` with an empty line keys as `rfi` and derives a 2.5bb limped pot rather than the 5.5 the line
makes.

**What that cost.** The bot could never continuation-bet. That is roughly half of all flops and the
single spot this phase most obviously exists for - and this item's own argument assumes it
throughout, reasoning at length about hero c-betting too little at a substituted price. No frozen
test caught it: the one requiring a committed spot to produce a bet is satisfied by the caller's
donk bet.

**What replaces it.** The postflop key carries the **completed preflop line**, verbatim and with its
sizes, rendered in the preflop key's grammar - not a preflop spot key object, which carries a
validator requiring a pending decision. The contract was already written this way and needs no
amendment: its criterion says "the key carries the board, the preflop line verbatim with its
sizes". Everything the original ruling asked for survives - verbatim, sizes included, no invented
compression, the non-`t` prefix, and the substitution recorded on the committed spot. What changes
is the object the prefix is built from.

Answer: [Ruled by Taylor, 2026-09-15] **Fix it now.** Taken at stage 6, before any cell is solved or
committed, on the ground this item states itself: changing what the key can express re-derives every
committed cell, so the cost is a rework now against a full re-solve later.

Found by the stage-6 betting lane, which measured it while building against the key rather than
inferring it from the prose.

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

Answer: [Ruled by Taylor, 2026-09-09] **Name the bet size.** Take the default. It costs no bytes,
and it means a later menu change makes the lookup refuse a size it holds no cell for rather than
silently answering it from a cell solved against a different one.

## 10. Whether pot and effective stack appear in the postflop spot key

Reversibility: frozen-into-data

Filed 2026-09-08 by the stage-2 review.

A postflop spot is self-contained in its board, both ranges, pot, effective stack and sizes. Pot
and stack are determined by the preflop line at 100bb symmetric stacks, so under decision 8's
default they are recoverable from the key and putting them in it is redundant. They stop being
recoverable the moment the phase covers a depth other than 100bb or a table that is not flat -
which the preflop key already handles with its `d100` segment and its flat-table refusals.

**A flop cell is far more stack-sensitive than a preflop cell, which the stage-2 poker review
measured and this item understated.** The geometric three-street size moves 103.9%, 115.8% and
130.9% of pot at 77.5, 97.5 and 127.5bb effective. So the same board and the same ranges at a
slightly different depth is a materially different strategy, where a preflop cell at a nearby depth
is nearly the same one.

Default: **leave them out of the key and carry them in the spot's payload, validated against the
preflop line they come from**, so a spot whose pot does not follow from its line is refused at
import rather than played. The `d` segment inherited from decision 8's verbatim preflop key is
what carries depth. And the validation **refuses a near-miss rather than rounding it** - the
opposite of the preflop chart's nearest-price substitution, because the sensitivity above is what
makes rounding safe preflop and unsafe here.

Answer: [Ruled by Taylor, 2026-09-10; the substitution rule below is a coordinator proposal he
accepted in the same exchange] **Both go in the key.** Pot and effective stack are named in the
postflop spot key rather than carried in the payload, against the default. The stack sensitivity
this item measures is the reason: the same board and ranges at a nearby depth is a materially
different strategy, and a key that cannot say which depth it was solved at cannot refuse a spot it
has no cell for.

**The collision with decision 8, found by the stage-3 review, and how it resolves.** Decision 8
carries the preflop key verbatim, including the `@2.5` that the preflop lookup substitutes a 2.25bb
open onto - and decision 3's own annotation records 2.25bb as the corpus **median** open. A 2.25bb
open really produces pot 5.00 with 97.75 behind (decision 8's own table), against the solved cell's
5.50 and 97.50. With an exact pot in the key and no substitution, that hand misses and refuses, so
the artifact would refuse the head of the coverage list decision 3 already ruled.

The resolution: **the key names the line the cell was solved for, not the table it is being asked
about.** The pot and stack segments are derived from the substituted preflop line, so they are
stable and a cell is always findable. The real table pot and stack are then compared against them at
query time, and the query refuses when the gap is too wide rather than silently answering from a
cell solved at a different depth.

**The tolerance, ruled by Taylor 2026-09-10 and classed `frozen-into-data`.** An earlier draft of
this paragraph set two bounds - 1bb of effective stack and 0.5bb of pot - and classed the pair
`runtime-reversible` on the grounds that no committed cell records it. The stage-3 review broke both
halves and Taylor took the replacement.

*Why the two bounds were wrong.* Pot and effective stack are not independent: pot is
`2 x open + 0.5`, so a 0.5bb pot bound admits opens of 2.25 to 2.75 while a 1bb stack bound admits
1.5 to 3.5. The pot bound is four times tighter and is the only one that ever binds, which the draft
did not notice - so a 2.2bb open, an ordinary size, would have refused. Worse, the corpus's median
2.25bb open passed with **exactly zero margin**: 5.50 minus 5.00 is 0.50 against a "more than 0.5"
test, so a stage-6 implementation writing `>=` instead of `>` flips the commonest flop spot in the
corpus to refused with nothing in the gate going red.

*Why `runtime-reversible` was wrong.* This file's own preamble, quoting `docs/LOOP.md:135` and
`LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`, says a behaviour default that a contract requires a
frozen test to pin is a fixture and therefore frozen. The contract makes the generator re-derive the
refusal counts, so a stage-4 test pins this threshold whether or not a cell records it. Classing it
reversible is exactly the error the preamble was written to stop.

*The ruling:* **a band around each substituted price, stated as a fraction of that price: accept an
actual size
within 20% of the price the cell was solved at, inclusive at both ends, and refuse outside.** The
committed chart declares two prices, so the band is concrete: an open of **2.0bb to 3.0bb** against
an `@2.5` cell, and a 3-bet of **6.0bb to 9.0bb** against an `@7.5` cell.

*Why a fraction and not a chip count.* A first draft of this ruling said "2.0bb to 3.0bb against a
cell solved at 2.5x" and stopped there, and the stage-3 review found the hole: a 3-bet pot cell
carries a second substituted price, the chart's `@7.5`, and that sentence neither accepted nor
refused it - its antecedent did not describe the query at all. A 3-bet to 7.0 gives pot 15.0 against
the solved 16.0 and fell through the rule. Five of the seven converged rows are 3-bet pots, so the
silence covered most of the measured evidence. Stating the band as a fraction of the cell's own
price closes it for every price the chart declares now or later.

*What the band is chosen for, said plainly because the previous draft implied otherwise.* **This is
a coverage rule, not a sensitivity-derived one.** It is set to admit the opens the corpus actually
contains and refuse the ones it does not; it is not derived from the depth sensitivity decision 10
cites. And it admits a lot of that sensitivity: at 2.0bb the three-street geometric size is 127.26%
of pot and at 3.0bb it is 106.81%, against the solved cell's 115.79%, so the band admits **20.45
points of geometry** against the 26.97 points (103.94% to 130.91%) this item quotes to argue that
depth must be refusable - **75.8% of the spread it exists to refuse**. A tighter band is not the fix,
because every tighter band refuses ordinary opens, which is the failure this replacement exists to
correct. The fix is saying so, which this paragraph is.

*Boundaries.* The endpoints are inclusive and written down, because the previous draft's failure was
a boundary nobody stated: 2.25bb passed a "more than 0.5bb" pot test by exactly zero margin. The
hazard is reduced rather than removed - 2.0bb is a min-open and 3.0bb a standard 3x, so real hands
still land exactly on the endpoints, and inclusivity is what makes that safe rather than the width
being chosen to avoid them.

*Measured 2026-09-10, after the stage-3 review pointed out the 3-bet half of this band rested on no
number at all.* Parsed directly from the 499 raw PHH hands in
`data/samples/public_corpus/corpus_hands.jsonl` - preflop raises only, each divided by that hand's
big blind, first raise counted as the open and second as the 3-bet:

- **Opens, n=409, median 2.25bb.** The 2.0-3.0bb band covers **405 of 409, 99.0%**. The open half of
  this rule does what it was chosen to do.
- **3-bets, n=87, median 9.25bb.** The 6.0-9.0bb band covers **41 of 87, 47.1%**. The band's top is
  below the corpus median, so the rule as ruled refuses **most real 3-bet pots**.
- **4-bets and beyond, n=19, median 25.35bb.** Outside every band and outside the chart, which
  declares no 4-bet price. Those spots refuse for a different reason and are not this item's.

**One consequence for decision 3, which nobody had drawn.** Decision 3's ruled ranking orders
preflop lines by how often the corpus reaches them. A 3-bet line costs the same 45 to 85 days as a
single-raised one and serves 47.1% of its arrivals against 99.0%, so the quantity that ranking
should sort on is **servable** arrival frequency rather than arrival frequency. Five of the seven
converged rows in the cost report are 3-bet pots, so the phase is best measured exactly where it
will answer least. Decision 3 is ruled and is not reopened here; its ranking is computed at stage 6
and this is the correction that computation needs.

**The diagnosis is not the band's width, and widening it is not the fix.** No band centred on 7.5
covers this corpus: ±30% reaches 55.2%, ±40% reaches 71.3%, ±50% reaches 80.5%, and ±60% - a
3.00-12.00bb band, which would call a 3bb raise a 3-bet - still reaches only 89.7%. The cause is
that **the committed chart's single 3-bet price of 7.5bb sits below the corpus median of 9.25bb**,
so the cell 3-bet pots substitute onto is mis-centred and no tolerance around it can be both tight
and covering. Answering a 12bb 3-bet pot from a 7.5bb cell is not a rounding error: SPR moves from
5.78 to 3.52 and the strategy is a different one.

**Ruled: keep the 20% band and record the gap rather than widen it.** This phase covers
single-raised pots well and 3-bet pots poorly, it says so, and it fails closed on the ones it cannot
answer - which is what this repo does everywhere else. Closing the gap properly means a second
solved 3-bet price, which is coverage rather than tolerance and belongs to decision 3 and a future
phase, filed as `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` in `backlog.yml`.

*A second asymmetry the review found, kept because it compounds the above.* One 20% rule is not
neutral between pot types. At a 3-bet of 6.0 the geometric three-street size is 74.56% of pot and at
9.0 it is 59.76%, against the cell's 66.23% - 14.80 points, fewer than the open band's 20.45, but on
a much smaller base: 22.35% of the solved size against the open's 17.66%, and the pot moves ±3.0bb
against the open band's ±1.0bb. So the same fraction is looser where SPR is lower.

*What it still does not bound.* This is a chip test and the larger channel is ranges: a 2.25bb open
faces a wider, weaker defender than the 2.5x cell was solved against, and no tolerance on price sees
that. `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` in `backlog.yml` owns it and stays
open.

**What this accepts.** The pot and stack in the key are nominal rather than observed, so on the
substituted hands they restate the preflop line rather than adding information, and the honest
statement of decision 10's benefit is narrower than the default's rejection implied: the segments
earn their place when the phase covers a second depth, not on the 100bb-only set this phase
commits. The gain today is that a future depth cannot be silently answered by a 100bb cell.

**No nearest-value substitution on the cell itself.** A depth or pot outside the tolerance refuses.
That is deliberately the opposite of the preflop chart's nearest-price behaviour, and the
sensitivity above is what makes rounding safe there and unsafe here.

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
because every measured config carries them.** They are stated carefully, because the first version
of this paragraph got one of them wrong in a way that would have destroyed real data.

**`add_allin: false` does not mean the tree has no all-in, and two earlier drafts of this item said
it did.** Read in `crates/solver/src/tree.rs` rather than inferred: `add_allin` controls only
whether an extra all-in *candidate* is appended (lines 459 and 504). Separately and outside that
guard, every configured bet and raise is snapped to a stack-off by
`if to >= max_to - 1e-9 || to >= self.config.allin_threshold * max_to - 1e-9 { to = max_to; }`
(lines 468 and 512). So jams exist in these trees; they arrive by conversion rather than by menu.

**And `allin_threshold` is a percent of the stack behind, not of the pot.** `max_to = stack_me` and
`stack_me = effective_stack - (st.put[me] - starting_pot / 2.0)`, so at 85.0 - which the server
divides to 0.85 - the snap fires when a bet reaches 85% of what the acting player has left, and the
pot is not in that comparison at all. `docs/GTOPEN_SOLVER_NOTES.md` calls it a percent of pot; its
practical warning survives its wrong mechanism, since 0.67 becomes 0.0067 and every bet then
exceeds the threshold, but a driver written to the pot description computes the guard against the
wrong quantity.

**On the flop the snap never fires under either menu**, which is the part of the earlier claim that
survives. Deepest flop line at `max_raises: 2`: single-raised reaches 25.78, **26.4%** of the 97.5
behind; 3-bet reaches 75.00, **81.1%** of the 92.5 behind against a 78.625 threshold - under it by
3.625 chips, under 4% of stack. That margin is thin enough that a change to `max_raises`, the raise
multiplier or the 3-bet size flips a sized raise into a stack-off, and no field on a committed cell
would record which it was solved under.

**On later streets it does fire, and no direction can be read off how often.** Two drafts of this
paragraph got this wrong in opposite ways and the record of both is kept, because the second was
mine and it corrected something that was right.

The worked line is `bet 12.00, raise 30.00, call` on the flop, giving a turn with pot 76 and a
stack behind of **62.50**, where a 75% turn bet of 57.00 is 91.2% of stack and snaps. A draft of
mine put that stack behind at 70.5 and concluded the bet does not snap. **62.50 is correct.** `put`
in the builder is cumulative and initialised to `starting_pot / 2` per player - `put: [half, half]`
at `tree.rs:386`, then `put[me] += to - street_bet[me]` at 623 and 635 - so after each player has
30 in, `put` is `[38, 38]`, `pot = put[0] + put[1]` is the 76 both drafts agreed on, and
`stack_me = 92.5 - (38 - 8) = 62.5`. My draft read `put[me]` as the street contribution, which is
also why its own pot and its own stack figure could not both be right.

**And the direction claim is withdrawn from both sides.** Counting distinct reachable
threshold-snap states, flop/turn/river: single-raised pinned 0/0/24 against reduced 0/0/0; 3-bet
pinned 0/6/9 against reduced 0/6/6. So the pinned menu snaps more often, never less, which is the
opposite of the first draft's claim - and it is not evidence for anything, because **a count of snap
states measures tree breadth rather than strategic content.** The pinned menu has strictly more
lines and therefore more chances to cross the threshold. Neither menu's snap count says which
distorts hero's play.

**What survives and bears on a ruling: zero threshold-snaps on the flop, under either menu, in
either pot type.** A committed flop cell's action set is what its menu says. The mechanism reaches
the committed flop strategy only through continuation values - the same channel as the missing probe
and the turn and river sizes.

**What it needs is provenance rather than a new field on a cell.** The 3-bet pot's deepest flop line
sits 3.625 chips, 3.9% of stack, under the threshold, and which side of it that node falls on is
decided by `max_raises`, the raise multiplier, the starting pot and the effective stack. Pin those
four on the committed config, record them on the cell beside the exploitability and iteration count
the contract already requires, and re-run the reachability walk if any of them moves. That rides
decision 7's default - prove it on the run that is committed, not on a proxy - rather than adding a
condition of its own.

**`donk: ""` does not mean the out-of-position player never bets the flop**, and an earlier draft of
this item said it did, then went further and said the out-of-position flop root has one legal
action, so 1,755 cells per line would read `check 1.00` and should be omitted. **That was wrong and
following it would have discarded 1,755 cells per line of genuine solved strategy.** GTOpen's tree
builder sets `root_street = (board.len() - 3)` and gates the donk list on
`st.to_act == OOP && st.street > self.root_street && st.last_aggressor == Some(IP)`, so on a
flop-rooted solve `street > root_street` is false at the flop and the out-of-position player uses
the `bet` list, `"33 75"`, exactly as in position. The build validator says the same in its own
words: `donk_used = player == "OOP" && street > root_street`. Verified in
`crates/solver/src/tree.rs` rather than inferred from the field's name, which is the same trap
`SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE` already records for a neighbouring field.

**What the empty donk list does remove is narrower and still real:** the out-of-position player
leading the **turn or river** when the other player was the previous street's aggressor - the probe
into a called flop bet. That is a frequent line, its absence biases hero's flop betting upward, and
it reaches a flop-only artifact through continuation values, the same channel as the turn and river
size restriction rather than a missing flop node.

So what remains is the missing probe, pushing hero's flop betting up. The "missing jam" half is
withdrawn: jams exist by conversion. The net sign still has to be measured rather than argued, and
the reason is now the probe against the turn and river size restriction rather than the probe
against a jam that is not absent.

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

Answer: [Ruled by Taylor, 2026-09-10. He confirmed the count and the sizes in his own words -
"Keep 2 per street ... We can just do 66-125 for turn and river. That's fine." - after the
coordinator proposed them; the coordinator's own stack-off rationale for them is struck below.]
**Two bet sizes on every street: flop `33 75`, turn and river `66 125`.** Raise stays `2.5x` and
`donk` stays empty, so the missing turn and river probe is unchanged and still biases hero's flop
betting upward.

This is none of the four options as listed. It takes the pinned menu's *shape* - two sizes
everywhere, so the coverage decision 3 asks for is reachable in single-raised pots - and re-chooses
the later-street sizes, which no option did. What ruled out the pinned menu in a single-raised pot
was 21,282 to 21,715 MB of arena against a 12,026 MB ceiling; the machine note below retires that
ceiling, so it is not what decides this and decision 12's floor is not what makes it fit.
Re-measure the arena against the new machine's ceiling before decision 6's index is designed.

**The coordinator's stack-off rationale for these sizes is struck, and Taylor's reason replaces
it.** That draft argued 125% "brackets 116% from above where 75% cannot reach it", where 116% is the
three-street geometric size at the single-raised pot's SPR of 17.73. The stage-3 review showed the
argument is about a size the ruled menu never offers on the flop. Recomputed and confirmed: through
the ruled menu's deepest line, `75 125 125` invests 81.47 and leaves **16.03 of 97.5 behind, 16.4%
of stack**; through the small branch, `33 125 125` leaves **44.33 behind, 45.5%**. Only 125% on all
three streets stacks off, and the menu does not offer it on the flop. So the ruled menu does **not**
give the ordinary pot a line that gets all-in, and this file must not claim it does.

Taylor's own reason, and it is sufficient: "It's fine to not get full stacks in a single raise pot.
That doesn't have to happen every time." Getting stacks in is one property of a bet menu, not a
requirement, and no measurement here says a menu that reaches all-in plays better than one that does
not.

**The 200% turn overbet was raised by Taylor, considered, and not taken.** He asked what three sizes
would buy and floated 200% of pot, then settled on two sizes at `66 125`.

**One of the two reasons the coordinator put in front of that choice was wrong, and the stage-3
poker review measured it.** The claim was that a 200% river bet is usually the stack anyway, worked
through one line - `33` called, `200%` called, then 200% of the river pot at about 91 against
roughly 77 behind, converting to all-in under the `allin_threshold` snap. That line is real and it
is **one of six river branches the ruled menu can reach**. In the other five a 200% river bet is not
the stack, and it is furthest from the stack in the checked-through branch - which is precisely the
branch where a river overbet earns most, because neither player has built the pot and the polar
range is at its widest. So the reason given for confining the overbet to the turn does not hold on
the river, and it was reasoning presented as such rather than a measurement, which is how it
survived to be ruled on. **Taylor's choice is not disturbed** - it was two sizes per street, and the
stage-6 comparison this item files is what settles the turn size - but the record must not keep a
justification the measurement contradicts.

**The reason that does hold** is cost: a third size per street compounds across three streets, and
the record's only adjacent datum is that cutting turn and river from two sizes to one bought 750,792
action nodes of 2,347,996, **32.0%** - an earlier draft said 24%, which is neither the node ratio nor
the 28.2% arena ratio. So a third size is the expensive direction. What is now unsupported is the
narrower claim that the overbet's value sits on the turn rather than the river; on the review's
reading it sits on both, and the river branch it was dismissed from is the one where it is worth
most.

**Filed rather than dropped**, because `NO-MENU-IN-THE-RECORD-OFFERS-AN-OVERBET` in `backlog.yml`
already owns the gap and the ruled menu closes only half of it: 125% on turn and river is an overbet
of the pot, so the item is falsified on its later-street half and still stands on the flop. The
experiment that would settle whether a turn overbet is worth its cost is the same one this item
already asks for - one board, pot, stack and both ranges held, only the menu moving - run as
`33 75` / `66 125` / `66 125` against `33 75` / `66 200` / `66 125`. It is cheap, it belongs at stage
6 rather than here, and nothing commits until it runs.

**Nothing in the record uses 66%, 125% or 200%.** Every measured row is `33 75` or `75`, so this menu
is unmeasured on both cost and strategy, which is a wider evidence gap than any of the four listed
options carried. Bigger sizes do reach the all-in conversion sooner, so the tree may be smaller
rather than larger, but that direction is reasoned rather than measured. The single-raised-pot solve
this item already asks for is the first solve of the phase and it runs at this menu.

### Machine note, recorded here because decision 11 and decision 4 both rest on it

**Ruled by Taylor, 2026-09-10.** Solving moves off the machine every figure in this phase was
measured on. The stage-3 review was right that an earlier draft buried this in a subordinate clause
while letting it retire the ceiling every arena verdict depends on.

- **What was ruled:** a rented cloud machine with an NVIDIA GPU, hourly rather than purchased
  ("i think we'll need a virtual computer", and separately that no hardware is bought to start the
  phase). Nothing is rented until the phase needs a solve; stages 4 through 6 need none.
- **What is not ruled and must not be invented:** the provider, the instance type, the core count,
  the RAM and the GPU model. Every timing, every arena figure and the 12,026 MB ceiling in
  `latest_postflop_solve_cost.txt` are "Apple M4, 10 cores, 34.4 GB RAM" and none of them transfers.
- **The one figure this note deliberately does not carry:** GTOpen's README puts CUDA at about ten
  times the CPU engine, and `docs/GTOPEN_SOLVER_NOTES.md` records it as untested with no NVIDIA GPU
  on the measuring machine. It is not used in any cost figure in this file and must not be until one
  flop has been solved on the rented machine and timed. That solve is the first thing the machine is
  for.
- **What has to be re-derived on it before a run is planned:** seconds per iteration at the ruled
  menu, the arena for the single-raised tree against the new box's own memory ceiling, and therefore
  decision 4's campaign figures and decision 6's covered line count.
- **The cost is money, and this is the first place the phase says so.** Rented by the hour against
  decision 4's 17.9 to 105 days of continuous compute per preflop line means metered spend scaling
  with a line count decision 6 deliberately leaves as an output, and even the untested CUDA speedup
  leaves a texture-weighted line in the range of days rather than hours. **No rate is quoted here on
  purpose**: no provider or instance type is ruled, and inventing a dollar figure would be the same
  defect as inventing the speedup. What this note fixes is that the cost exists and is unbounded
  until the machine is named - it was the largest unwritten accepted cost in the phase, found by the
  stage-3 review outside its brief.
- **One closed contract item reopens on Linux.** `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` sits on
  the contract's Closed list because GTOpen's guard reads `/proc/meminfo`, "which does not exist on
  Darwin". A rented cloud box is almost certainly Linux, where it does exist and the guard goes
  live, which removes the premise the closure rests on. Re-check that item against the machine
  before stage 6 rather than after a run dies.

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

**Flooring an unsmoothed export does carry a poker cost, and it is one hand class rather than a
ladder.** An earlier draft of this paragraph, written on 2026-09-09, said the floor cuts a
rank-ordered block out of the defender's pair ladder in both pot types. **That was half wrong and
the poker review caught it.**

The single-raised-pot pattern is **normal poker**, not a defect. `config.range_oop@717f36499fb4`
reads `TT 0.0002, 99 0.0011, 88 0.0016, 77 0.0041, 66 0.0043`, then `55 0.5712, 44 0.8244,
33 0.9474, 22 0.8064`. That is a single monotone threshold, not an inversion: every pair 66 and
better is essentially absent from the big blind's **flat-calling** range because it 3-bets instead,
and 55 and below flat. Two blocks, one boundary. The same thing happens at the top of the
3-bet-calling range, where `AA KK QQ JJ` are absent because they 4-bet. Calling that "not poker"
would invite smoothing `TT 99 88 77 66` back into a range they correctly sit outside, where they
are already counted in the 3-bet range - an error injected by a repair.

The real artifact is **one class, 44**, and it is stranger than a ladder. In the 3-bet defending
range `config.range_oop@568ae7b39c57` it reads **0.0007** while `55` reads 0.9776, `33` reads
0.1620 and `22` reads 0.9994. No strength ordering produces that. And the same class survives on
the in-position side at **0.0194**, two hundredths above the floor. So a 0.01 floor deletes 44 from
one side of the 3-bet pot and keeps it on the other, leaving hero solved in a pot where he can hold
44 and his opponent provably cannot.
`EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` owns it, and the floor makes it visible rather
than causing it - unfloored, 44 is present at a weight that does nothing.

Default: **floor, class-level, at 0.01** - reversed on 2026-09-09 from "no floor" after the
stage-2 poker review measured the mass. The earlier default was chosen because this repo fails
closed and no floor requires no action to be safe; that reasoning was right in form and rested on
the 68% figure being a quantity of range, which it is not. Class-level remains a constraint rather
than a choice, because one suit-specific weight collapses the isomorphism group.

The condition on that default names an owner rather than an entry, because the entry it would have
named had none: `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` held the pair-ladder smoothing
this default depends on and was filed against phase 14, which is `completed`. It is re-pointed to
phase 16. **So the smoothing is this phase's to do or to refuse explicitly, not a thing it waits
on.** The rest of the condition: the 44 asymmetry above is stated as a known defect of the input,
not repaired by this phase unless the smoothing lands, and the report publishes each committed range's pair weights on both sides
so a reader can see what hero was solved against - and can see that the pairs missing from a
flat-calling range are missing because they 3-bet, which is the reading a repair would destroy.

Answer: [Ruled by Taylor, 2026-09-09] **Floor at 1 percent, class-level.** Take the default.
Taylor's reasoning, recorded because it is narrower than the default's and worth keeping: a hand the
solve holds at a 1% weight is a hand whose call-or-fold decision makes no difference, so removing it
costs nothing. That is the mass argument rather than the combo argument, which is what reversed this
item.

What the ruling does **not** settle is the pair asymmetry below. It is a defect of the input rather
than of the floor, and the smoothing it needs now has an owner.

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

**One argument for splitting that nobody made**, from the stage-2 poker review: a split puts the
frequency-convergence diff in the data half, where it belongs, instead of gating the key format on
a measurement that has nothing to do with it. As one phase, the format rulings wait on a solve.

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

Answer: [Ruled by Taylor, 2026-09-10] **One phase. Do not split.** The format half and the data
half are ruled together here, accepting the cost this item names: the artifact gets committed
against a key format that nothing has been built against yet.

## 14. How a chip bet at the table is matched to the ruled pot-fraction menu

Reversibility: frozen-into-data

Filed 2026-09-14 by stage 4's two independent reviews, after the nine items the index above counts
were ruled.

**It was filed `runtime-reversible` and that was wrong.** The round-2 verification review caught it
the same day: the tolerance's value is pinned by a frozen test, and the class definitions quoted at
the top of this file say `frozen-into-data` covers a choice written into "a committed artifact **or
fixture** that later phases are then measured against". `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`
resolves exactly that wording - a behaviour default a frozen test pins is a fixture, so it carries
this class even in a phase that commits no data - and the paragraph recording it closes by naming
this failure in advance: "a phase taking its definitions from this list rather than from
`docs/LOOP.md` would have called such a threshold reversible and never asked anyone." That is what
happened here, and the loop asked.

**What is unpinned.** Decision 11's flop menu is `33 75` as a percent of pot. The table is in
chips, and the arithmetic does not come out even: the `@2.5` single-raised pot at 50/100 blinds is
550 chips, and 33% of 550 is 181.5, which no dealer can push. The stage-4 fixtures already use two
readings without saying so - the facing-a-bet fixture bets 180, which is 32.7273%, and the
off-menu fixture bets 275, which is 50.0% and is required to refuse. Nothing between them was
pinned, so stage 6 could have taken either of two opposite rules and nothing would have gone red.

**What each of those rules costs.** A strict equality match means every faced-bet node refuses at
a real table, because no real table produces 181.5 chips - so the whole raise branch of the
committed artifact is dead on arrival, and the report's raise frequency reads 0 with no code
saying why. A match with no stated ceiling is the mirror: a tolerance wide enough to be safe can
swallow a 40% bet into the 33% cell, which is the nearest-neighbour substitution this contract
forbids by name and which decision 9 measured the cost of - a caller needs 19.9% equity against
33% and 30.0% against 75%, and merging them overfolds to small bets and overcalls large ones.

**The options as they were put, in chips on the 550-chip `@2.5` pot rather than in fractions,
because what is actually being chosen is which real bets the bot can answer.**

| tolerance | 33% bucket | answered | refused |
| --- | --- | --- | --- |
| 0.01 | 176-187 | 180, 182, 185 | 175, 190, **200** |
| 0.02 | 171-192 | 175, 180, 190 | **200** |
| **0.05** | **154-209** | 160, 175, 180, **200**, 205 | 275, 300 |
| exact | 182 only | 182 | everything else |

Answer: [Ruled by Taylor, 2026-09-15] **Within 5 points of pot.** The rule is:

1. A faced bet is matched to the menu **by pot fraction, not by chips**. `bet_chips / pot_chips`
   is compared against each menu entry and the match holds only inside the tolerance.
2. The tolerance is a **named module-level constant**, `MENU_FRACTION_TOLERANCE` in
   `solver_artifacts.postflop_key`, so a later re-ruling moves one number in one place.
3. Its value is **0.05**, five percentage points of pot, compared **inclusively**: a bet exactly
   0.05 away matches. Recorded because `<` and `<=` are two different rules and the phase should
   not leave stage 6 to pick. No tested case actually separates them: 154 chips is 28.000% of this
   pot, the nearest thing to the boundary a whole chip reaches, and in binary floating point its
   distance evaluates to 0.04999999999999999, inside under either reading. The frozen tests pin
   154 in and 153 out, which is the sharpest whole-chip pair the pot allows, and they are a test of
   the rule rather than of the arithmetic.
4. A committed artifact size converts to chips by **rounding to the nearest chip**.
5. A bet matching no entry inside the tolerance **refuses**; it is never snapped to the nearer one.

**The arithmetic, every figure recomputed against the ruled value rather than carried over from the
version of this entry that proposed 0.01.**

- *Floor.* It has to admit what a real table bets. The fixture bets 180 into 550, which is
  32.7273%, so the tolerance must exceed `|0.327273 - 0.33| = 0.002727`. **0.05 is 18.3 times it.**
- *Ceiling, structural.* Two menu entries must not share a bet. Half the distance between them is
  `(0.75 - 0.33) / 2 = 0.21`.
- *Ceiling, binding.* The phase separately requires a 50% bet to refuse, so the tolerance must stay
  below `|0.50 - 0.33| = 0.17`. **0.05 is 3.4 times inside it**, which is the margin this ruling
  spends and the one a later re-ruling has left to spend.
- In chips on the 550 pot: **154 to 209** into the 33% bucket and **385 to 440** into the 75% one.
  The two do not touch - 38% and 70% - so no bet lands in both. 181.5 rounds to 182, inside the
  first.

The 275-chip bet the phase requires to refuse is 50.0% and still refuses. So does 297, which is
54.0% and exactly halfway between the entries; that case keeps its own frozen test, because it is
the one a nearest-neighbour rule answers silently and a fail-closed rule refuses.

**What this ruling costs, stated because the ruling was taken with it on the table.** At 0.05 a
28%-of-pot bet and a 38%-of-pot bet both get the strategy solved for 33%, and those are not the
same spot: decision 9 measured a caller as needing 19.9% equity against 33% and 30.0% against 75%,
and the same gradient runs inside this bucket. The phase buys reach with it - the bot answers the
round numbers people actually bet, 175 and 200 among them, instead of refusing them - and pays for
it in fidelity at the edges of each bucket. Nothing in the phase reports how often a matched bet
sat near a bucket edge rather than near its centre, which is the figure that would show the size of
this cost; that is `NO-FIGURE-REPORTS-HOW-FAR-A-MATCHED-BET-SAT-FROM-ITS-MENU-ENTRY`, filed against
this decision.

## 15. Whether the sample solve also measures that the frequencies have settled

**Ruled by Taylor, 2026-09-16. `frozen-into-data`**: what this decides is committed under
`data/artifacts/postflop/**` and a later phase cannot revise it without re-solving.

**Ruling.** The sample runs, and it runs with the deep check. Four cells at the 240-iteration
working point, then one of them re-solved to the 1,200-iteration cap and its action frequencies
diffed against its own 240-iteration strategy. The diff is committed beside the sample.

**The question, which is a poker question and not a cost one.** Every convergence figure this phase
rests on is an **exploitability** figure - 0.295% of pot at 240 iterations on the recorded
three-bet cell. Exploitability says how much a perfect opponent wins against the strategy. It does
not say the strategy has stopped moving. What a reader takes off a flop chart is *how often* to bet
a hand, and the hands the solver has driven to indifference - the ones whose two actions are worth
the same, which is most of a mixed flop range - keep trading frequency back and forth long after
the exploitability number has flattened, because moving them costs nothing by the measure that is
being minimised. So a cell can be 0.3%-of-pot accurate and still publish a frequency table that a
deeper run would contradict.

Nothing in this repo has ever checked. `docs/GTOPEN_SOLVER_NOTES.md:145` says so in as many words -
both determinism runs stopped at 240 iterations, and reproducibility "says nothing about whether the
strategy at 240 iterations has settled". The stage-2 independent poker review made this the single
condition on its verdict that the phase is worth committing at all, and it is filed as
`NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`, owned by phase 16 and
still open. Committing the sample without it would close a phase on its own reviewer's one
condition unmet, which is the shape
`BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` describes.

**The cost, re-derived here rather than carried from the ExecPlan's bootstrap, which understated
it.** The bootstrap says "about 16 minutes a flop". That figure is the **monotone** rate and the
sample is deliberately one board of each texture. Per iteration the floored single-raised tree is
2,347,996 action nodes x 919 hands, and decision 11's machine note gives the per-node-hand cost by
texture:

| board | ns/node-hand | s/iteration | 240 iterations |
| --- | --- | --- | --- |
| monotone `9c8c7c` | 1.7 - 2.0 | 3.67 - 4.32 | 15 - 17 min |
| two-tone `8c8d3c` | 4.28 | 9.24 | 37 min |
| rainbow `Kh7d2c` | 7.34 - 8.71 | 15.84 - 18.79 | 63 - 75 min |

Three boards is **1.9 to 2.2 hours**, and the fourth cell is a second preflop line on one of them,
so the sample is about **2.2 to 2.8 hours** rather than the 48 minutes three times sixteen implies.
The deep check re-solves the monotone cell, the cheapest of the three, from 240 to the 1,200 cap:
`1200 x 3.67-4.32 s` = **73 to 86 minutes**. Total about **3.5 to 4.2 hours**.

**What the answer is worth either way.** If the frequencies have settled, the phase has the
evidence its own reviewer asked for and the 240-iteration working point is ruled rather than
assumed - which is what makes the 45-to-85-day campaign estimate a plan instead of a guess, since
that estimate is 240 iterations multiplied by 1,755 flops. If they have not, the phase has found
that out on four cells costing four hours rather than on a full campaign costing weeks, and the
working point moves before anything is committed at scale. The cheap version of this measurement
does not exist: exploitability is already measured and is already the wrong quantity.

**What is not decided here.** Whether a frequency divergence, if one appears, halts the phase or is
recorded and accepted. Nothing is committed against that yet; the diff is measured first and the
question asked with a number in hand rather than in advance of one.

## 16. The composite still calls itself the fallback, and what the fifth freeze re-open covers

**Ruled by Taylor, 2026-09-16.** Two rulings, taken together because the first needs the second.

### 16a. The name follows the behaviour. `runtime-reversible`

`CompositeStrategy.from_repo` was rewired to `PostflopBettingStrategy` at `dbffd03`. `component_for`,
`POSTFLOP_COMPONENT` and `strategy_id` were not, so the bot that bets a flop reports itself as the
one that folds every flop. Measured: the postflop component object is `PostflopBettingStrategy`,
`component_for('flop')` returns `postflop-fallback`, and `strategy_id` is
`composite-preflop-chart-postflop-fallback`.

`composite.py:52-56` argues the mismatch is acceptable because "the code prefix on each answer is
what actually says which one replied". That reasoning does not survive its consumers.
`generate_postflop_fallback_report.py` is a gate command and a completed phase's required report,
and it labels every row with `component_for`. Regenerated on today's code it prints, in this order:

```
Broken out by which component answered. Preflop is the chart, flop through river is the
fallback, and no query reaches both.
                                               preflop              postflop
                                         preflop-chart     postflop-fallback
...
Refusal codes, all of them from the chart and none from the fallback:
  postflop-betting:no-cell-for-this-preflop-line           2
  postflop-betting:no-committed-river-solution             2
  postflop-betting:no-committed-turn-solution              2
```

A sentence saying none of these came from the fallback, with three of them underneath it, under a
column headed with the fallback's name. The committed copy on disk is dated 2026-09-15 14:52, before
the rewiring, so nothing is wrong in the repo *today*; it becomes wrong the moment closeout
regenerates it, inside a phase that is already marked completed. That is the shape maint-30 was
opened for on phase 14's opening ranges, and the ruling is the same one: the report tells the truth
or the report changes.

**Ruled: the name and the id both move.** The string lives in exactly two places -
`composite.py:71` and `tests/test_simulator.py:68` - which is why this is ruled now rather than
filed. It is the last moment it is a two-line change.

The poker reason it is not cosmetic: a reader of that report is deciding whether the bot's flop play
is worth studying. "postflop-fallback" names a component whose whole behaviour is to fold the flop.
A reader who believes the column has no reason to look at the flop rows at all.

### 16b. The fifth freeze re-open, and why it is wider than the four before it

The four previous re-opens were each one named correction. This one is **eleven corrections across
four files plus four added cases**, and the width is the finding rather than a convenience.

**It is ten red behaviour tests, not the seven the bootstrap names.** Three more sit in
`test_postflop_query_recording.py::TestThePreflopRaiserHasAFlopSpotAtAll`, failing on
`ValueError: this line ends at BB's turn rather than BTN's` - the action-order check, not missing
data. They were being counted among the data reds. The irony is exact: the class decision 8's own
amendment added, to prove the preflop raiser has a flop spot at all, is the class the new
action-order check refuses, because its helper passes an empty flop line for both heroes and the
raiser's spot is reached only after BB checks. The code is right and says so in
`postflop_key.py:340-343`.

**One of the seven is not a test correction at all.** `test_a_refusal_names_the_spot_the_chart
could_not_answer` asserts a refusal carries `hand_class`; the detail now carries board and preflop
line and no hand class. No ruling anywhere licenses that. The one contract line on the subject
(line 196-197) points the other way, and the backlog entry it cites lifts `hand_class` **out** of
the inventory grouping key, so it cannot fragment the inventory - which was the only argument for
dropping it. Measured: 10 of 11 postflop inventory rows now read `classes: ()`, and three refusal
codes carry no detail whatsoever. **That is a code defect and is repaired in the code.** The
vocabulary it must use - the 169 preflop-style labels the inventory column already speaks, not the
1,176-combo postflop label - is `runtime-reversible` and proceeds on that recorded default.

**One test is green and asserting something false**, which is worse than any of the reds:
`test_component_for_routes_preflop_to_the_chart_and_the_rest_to_the_fallback` passes while
asserting the label 16a corrects. It is in the re-open.

**The four added cases.** Nothing in this repo calls `run_solve`, so none of the four fail-closed
guards repaired today is covered by anything. Measured rather than argued: restore the
`.get(key, default)` defaults and `pytest tests/test_postflop_solve_driver.py` still reports 15
passed and 6 errors, unchanged. A mutation canary cannot help, because a canary is only as good as
the test it points at and there is no test to point at. Four cases against a dict-returning
transport, no server and no network, are the cheapest real proof and the only one; the solve run
itself is a positive control showing the guards do not refuse a healthy server, and is recorded in
the packet as that and nothing more.

**What this costs at the table if it is skipped**, which is the reason it was ruled rather than
filed: a `/api/status` that omits `exploit_pct` used to read as 0.0% of pot - better than the 0.3%
target - so a cell that was never solved committed as converged, and the bot would play it as
studied strategy. The guard against that is now the only thing standing between a silent server and
a committed cell, on a machine where GTOpen's own memory guard cannot fire at all.

## 17. The big blind's calling range is a known defect, and every flop cell is solved against it

**Ruled by Taylor, 2026-09-16.** `frozen-into-data` for the sample; the measurement it adds is
`runtime-reversible`.

**Ruling.** The sample is solved against the committed range, and the phase additionally re-solves
one cheap cell against a widened big-blind calling range and diffs the flop strategy, so the cost of
the defect is a number rather than an acknowledgement.

**What was found, measured by the coordinator at the exact export node this phase reads.** The big
blind facing a 2.5bb button open, from `gtopen_six_max_100bb_rakefree.gtx.gz`:

| action | weighted combos | share of all hands |
| --- | --- | --- |
| fold | 840.0 | 63.3% |
| call | 279.6 | **21.1%** |
| 3-bet | 206.4 | 15.6% |

Total defence **36.7%**. Only the call branch becomes the postflop out-of-position range, so the
solve's OOP input is 21.1% of hands, 49 classes after the 1% class-level floor.

**This is already a recorded defect of the committed chart, not a new discovery.** The derived chart
report's own accepted-defects list says it outright:

> defect · the big blind over-folds against every opener · it defends 25.70 to 48.39 percent where
> rake-free solves are roughly 40 through 65, and its flat barely moves with who opened

36.7% sits inside that band and below the reference floor. The measurement above is the same defect
read at the one node phase 16 consumes, which nothing had done.

**Why this is the phase's central poker risk rather than an inherited annoyance.** The four committed
cells are hero's flop strategy *against this range*. A range that folds too much preflop does not
merely arrive smaller; it arrives **stronger**, because the hands it dropped are the weak half -
suited gappers, weak broadways, the small suited aces that are not wheel aces. A solver facing a
range that is too strong produces a specific and predictable distortion, and it is not a rounding
error:

- the button continuation-bets **less** often and smaller, because a stronger caller folds less to a
  c-bet;
- the big blind check-raises **more**, because its range supports it;
- both errors point the same way, and a student drilling against the committed cells learns to
  c-bet too little against a field that in fact defends too wide.

That is the opposite of the leak most players have, so the training value is not merely reduced, it
is inverted at the decision the phase exists to teach.

**Why the sample still runs.** The defect is the preflop chart's and phase 16 cannot fix it; the
conditioning work is already filed as `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`, which phase
16 owns and which decision 12's floor already depends on. Halting the sample would leave the
harvest, the writer and the strict importer unproven while changing nothing about the range. The
sample proves the pipeline; it does not certify the poker, and the report must not let a reader
confuse the two.

**Why the extra measurement was ruled rather than filed.** Nothing in this repo knows how far a flop
strategy moves when the calling range widens. The claim "the committed cells are distorted" is
currently an argument from first principles, and this phase has twice found that an argument from
first principles was worth less than one measurement. The cost is one solve on the cheapest board -
the monotone cell converged at 318 iterations in 450 seconds, so about eight minutes - and the output
is a per-action frequency diff against a cell already in hand. If the flop strategy barely moves, the
inherited defect is a preflop problem and the committed cells are worth studying. If it moves a lot,
the phase has the number that says the sample is a pipeline proof and nothing more, and the next
phase has its brief.

**What is not decided here.** What counts as "widened", beyond that it is the same node read with the
fold branch's near-miss hands returned to the call branch, and that the widening is a measurement
input rather than a committed range. Nothing derived from the widened range is committed under
`data/artifacts/postflop/**`; only the diff is reported.

## 18. Two frozen tests the sample cannot satisfy at once, and the index that has nothing to list

**Ruled by the coordinator, 2026-09-16, both `runtime-reversible`.** Neither changes committed data;
both decide what the sample must contain before it is solved. Measured by the stage-6 sample lane
and re-verified here.

### 18a. The fourth-file amendment reached one test of two

`tests/test_postflop_artifact.py:469` asserts `len(paths) == 3` over the sample directory.
`tests/test_postflop_artifact.py:497` asserts `len(files) >= 3`. Taylor's 2026-09-15 amendment to
decision 6 item 4 - a fourth file is allowed, on a board already present, so item 4's texture and
rank splits are untouched - landed in the second and not the first.

The sample therefore reds a test either way. Three files cannot hold the four spots the frozen
tests require: a caller first to act producing a bet, a caller facing a bet producing a raise, a
two-tone board separating a flush draw from the same ranks without one, and a cell where hero was
the preflop raiser. Four files red line 469.

**Ruled: line 469 becomes `>= 3`, authorised by the 2026-09-15 amendment itself rather than by
anything a lane wrote.** The assertion's own subject is that every committed cell records its
substitution, and the count is a guard against an empty directory satisfying a per-file loop
vacuously, which `>= 3` still provides.

This is `NOTHING-CHECKS-THAT-EVERY-RULING-REACHES-A-CRITERION` happening again, sixteen days after
it was filed, to the ruling immediately after the one that prompted it. The amendment was applied
where it was noticed rather than everywhere it was true, and nothing looked.

### 18b. "In the index but not fetched" needs a spot that is in the index and not fetched

`test_a_spot_the_index_holds_but_this_machine_has_not_fetched_says_so` needs
`an_indexed_but_unfetched_query` to name a spot the index lists and the sample does not hold. Its
docstring assumes the full campaign - "on a fresh clone this is the common case, 1,752 of 1,755
classes". The campaign has not run. The sample solves three boards and commits all three, the index
may list only spots actually solved and stored, with four real figures and no placeholder, so the
index and the sample are the same set and the query has nothing to name. The lane reported that it
has no honest answer rather than inventing one, which is the correct outcome and the reason this is
ruled rather than patched.

**Ruled: solve one cell on a fourth board, record it in the index with its own four measured
figures, store its object outside the repo, and do not write it into `sample/`.**

This is not a workaround, it is decision 6's design stated at sample scale. Decision 6 rules the
artifact as object storage outside git plus a committed index plus a committed three-flop sample,
which means the index is deliberately larger than the sample. The refusal inventory has three
causes and this is the third; a sample where index and sample coincide exercises two of the three
and leaves the one that will be overwhelmingly the most common on a real clone untested.

The fourth board is chosen for cost rather than poker - it is outside the frozen texture and rank
splits, which govern the sample and not the index - so it is a monotone board, about eight minutes.
It is the cheapest honest answer available and the only one that does not either commit boards the
sample rules forbid or write digests of nothing.

### Amendment to decision 11, arising from the same measurements

Decision 11 reported the ruled menu's arena as 10,881 MB against a 12,026 MB ceiling - **90.5%**,
which it called thin and reasoned about accordingly. Re-measured on the live tree at the menu that
was actually ruled: **5,442 MB, 45% of the driver's ceiling.**

The cause is that the record's figures were taken on a different menu. Three builds on one board
with one range pair: the ruled menu (flop `33 75`, turn and river `66 125`, no donk) gives
1,514,261 action nodes and 5,442 MB; adding donk sizes gives 2,288,902 and 8,674 MB; `33 75` on all
three streets with no donk gives 2,347,996 and 8,847 MB, which is the record's node count exactly.
So the record's "pinned menu" was `33 75` everywhere, not the menu decision 11 ruled. Scaling the
third build by the record's 919/747 hand counts reconciles to 10,886 against its 10,881, which is
the check that this is the same arena model and not a different one.

**The memory headroom is therefore twice what the phase has been reasoning with**, and
`SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` is correspondingly less urgent than decision 11 treated it.

**Iterations went the other way and partly cancel it.** The monotone cell took **320** iterations to
reach 0.2954% of pot, against the record's 220-260 bracket. The ruled menu buys a 35% smaller tree
and pays back about 33% more iterations, so the saving per solve is far smaller than the node count
suggests, and **every campaign estimate in this phase built on 240 iterations is low.** The 45-to-85
day band in decision 11 is not corrected here, because correcting it needs a rainbow measurement
this phase has not taken; it is flagged as low rather than restated.

## 19. The preflop chart is re-solved, and phase 16 halts until it is

**Ruled by Taylor, 2026-09-16.** `frozen-into-data`, and the data is a completed phase's.

**Ruling.** The committed preflop chart is re-solved with a realistic blind 3-bet size. Phase 16
does not solve its cells against a range the repo's own chart does not produce, and does not commit
a sample until that chart exists.

**The measurement this rests on.** `raise_mults_by_seat = [[], [], [], [], [5.4], [5.4]]` on the
ruled config - one field, leaving every other seat on the global `[3.0]` - puts the big blind's
3-bet at 13.5bb against a 2.5bb open instead of 7.5bb:

| | committed 7.5bb | re-solved 13.5bb | committed reference |
| --- | --- | --- | --- |
| fold / call / 3-bet | 63.35 / 21.09 / 15.57 | 62.67 / **24.41** / **12.91** | 60.57 / 26.54 / 12.89 |
| pure classes | 153/169 | 144/169 | - |
| genuinely mixed | 3/169 | 9/169 | 40/169 |
| 3-bet bias, pairs | +0.4025 | **+0.0451** | 0 |
| pocket pairs in the call branch | 12.0 of 78 | **39.9 of 78** | 43.4 of 78 |
| **sets on `9c8c7c`** | **0.00 combos** | **7.40 combos** | 8.34 combos |

The experiment is trustworthy because the baseline was reproduced first: a fresh solve of the
committed config returned **0 basis points** of strategy and reach divergence against the committed
export, converging at iteration 1900 to a gap of 0.00015590818199695747 - the source card's recorded
`achieved_gap_bb`, digit for digit.

It was also controlled. The same field pushes the button's 4-bet from 22.5bb to 40.5bb, which points
the same way as the effect being measured. A third run applying the 5.4x to the **button only**
reproduces the 40.5bb 4-bet while leaving the 3-bet at 7.5bb, and shows **no gain at all**: 0.00
sets, pair bias +0.3816. The 13.5bb 3-bet is what moves the pairs.

**Why the cells are not solved against the new range with the chart left alone.** That was the
cheaper option and it was put to Taylor as such. It produces a bot whose preflop play 3-bets 7.5bb
while its own flop cells are solved assuming the opponent 3-bet 13.5bb, so a student drills correct
flop play against a preflop opponent this bot is not. The inconsistency would live inside one
artifact tree and be invisible at the table, which is the kind that survives.

**What is not fixed by this and must not be read as fixed.** The big blind still over-folds:
total defence moves 36.65% to 37.33% against a rake-free reference band of roughly 40 to 65. That is
a separate and larger defect of the chart, already on the derived chart report's accepted-defects
list, and one point is not a repair. And the SPR blindness is structural and survives - 33 still
3-bets 79% while 44 and 22 flat, and 9 genuinely mixed classes against the reference's 40. A bigger
3-bet costs more chips; it does not teach the model what an SPR is.

**A wart the adopting task must rule on rather than inherit.** `raise_mults_by_seat` is per *seat*,
not per raise depth, so one multiplier sets a seat's 3-bet, its 5-bet and everything between. There
is no setting that gives the big blind a 13.5bb 3-bet, the button a sane 4-bet, and both an
undistorted opening range at once. The run above carries a 40.5bb 4-bet it should not have, and the
button opens 37.36% against the committed 39.27%, which flatters the result slightly in the
direction that makes flatting better. The effect is far too large to be explained by two points of
opening range, but it is not zero and the adopting task re-derives it rather than quoting this
table.

**Why phase 16 halts rather than doing it.** `data/artifacts/preflop/**` is a completed phase's
committed data and is not in this task's `approved_scope`. Re-solving it re-derives the export, the
source card, the derived chart, the committed charts and every downstream report - phases 10 and 14
- and widening a stage-6 implementation task into that is exactly the move the scope model exists to
stop. It is its own task, in `contract-update` then implementation, and phase 16 resumes when it has
a range worth solving against.

**What phase 16 keeps.** Everything except the data. The spot key, the artifact schema and its
strict importer, the solve driver with its four guards, the harvest, the writer, the runner, the
betting strategy, the report, and eleven corrected frozen tests. The pipeline was proven end to end
on a real solve that converged in 7.7 minutes to 0.2954% of pot; the cell it produced was discarded
because of its input, not its machinery.

## 20. The arena the committed campaign solves in, and the memory ceiling that admits it

**Ruled by Taylor, 2026-09-20.** `frozen-into-data`, because the arena a cell was solved in is a
property of the numbers in that cell and cannot be changed afterwards without re-solving it.

**Ruling.** The flop campaign solves with GTOpen's uncompressed arenas - full-precision f32 regrets
and strategy sums rather than the 16-bit quantized ones the server defaults to - and
`MEMORY_CEILING_FRACTION` in `postflop_solve_driver` moves from 0.35 to 0.40 to admit it. Taylor was
told, and accepted, that 0.35 is the number meant to travel to the rented box the contract names, so
this loosens the guard there too and is done deliberately rather than nudged to fit.

### How the solver picks an arena, and why asking is not enough

`storage_from_env` in `crates/server/src/main.rs` is four lines: the environment variable
`SOLVER_COMPRESS` read as a string, full precision when it is exactly `"0"`, and the quantized arena
for everything else. Everything else means the variable absent, `"false"`, `"no"`, `"0.0"`, a value
with a space in it, or a name typed one character wrong. There is no error, no warning and no log
line, and **no route the server serves reports which arena it allocated**: `/api/status` carries the
solve state and `/api/spot` carries the tree's geometry, and neither names the storage mode.

So a campaign that asks for full precision and silently gets quantized arenas is indistinguishable
on the wire from one that got what it asked for, and every number it produces is a real measurement
of the wrong computation. That is the failure this decision exists to remove, so the campaign
**verifies rather than assumes**, and the verification is arithmetic rather than a field:

- `Spot::arena_bytes_for` is `entries * 8` at full precision and `entries * 4 + nodes * 16` when
  quantized (`crates/solver/src/game.rs`).
- `Spot::vram_estimate_bytes` is
  `nodes * (hands_oop + hands_ip + max of the two) * 4 + entries * 8 + 512 MiB`, and its arena term
  is full precision whatever the storage actually is.
- `/api/spot` answers `nodes`, `hands_oop`, `hands_ip`, `arena_mb` and `vram_mb` in one `TreeInfo`.

The entry count therefore comes out of `vram_mb`, and the two candidate arenas are then arithmetic.
They differ by nearly a factor of two, so the answer is never in doubt, and a reading that
reconciles to neither - or to both, on a degenerate tree - is refused rather than guessed.
`arena_storage` and `check_arena_storage` in `postflop_transport` hold that, and
`scripts/solve_postflop_sample.py` runs every built tree through them before `/api/solve` is called.

**This was checked against the record rather than only against the source.** Run over all 55 build
rows in `reports/active/latest_postflop_solve_cost.txt`, the quantized formula reproduces the
reported `arena_mb` exactly - to the byte, on every row - and the full-precision formula reproduces
none of them. That is both a self-test of the method and a finding in its own right: every arena and
timing figure this phase has published was taken on quantized arenas, and nothing said so.

### The measurements the ruling rests on

Measured by the stage-6 arena lane on `9c8c7c` in the single-raised pot, on the Apple M4 the rest of
the phase measured on. These are that lane's readings and are not re-derivable from anything
committed, so they are recorded here as measurements rather than as figures a later task can check:

| arenas | iterations | exploitability | largest in-class gap | classes whose committed row differs |
| --- | --- | --- | --- | --- |
| quantized | 320 | 0.3203% | 5.03e-04 | 5 of 152 |
| quantized | 1200 | 0.3152% | 2.48e-03 | 38 of 152 |
| full | 320 | 0.2293% | 7.15e-05 | 2 of 152 |
| full | 640 | 0.0800% | 1.40e-04 | 1 of 152 |

Two things in that table decide the ruling. **The quantized rows do not converge**: four times the
iterations buys 0.005 points of exploitability while the combos of one suit-isomorphism class drift
five times further apart, which is what an accuracy floor looks like rather than a slow solve. And
**the drift reaches the committed data**: at 1200 iterations 38 of 152 classes would commit a
different row depending on which of their combos the collapse happened to take first.

**It is free in wall clock.** 640 iterations took 11.9 minutes under either arena. What it costs is
memory, and the same arithmetic above prices that: on an identical tree the full-precision arena is
just under twice the quantized one, the node term being about one percent of the total.

### The ceiling, and exactly what 0.40 buys

On the 32 GiB machine the phase measured on, `MEMORY_CEILING_BYTES` is 12,025,908,428 at 0.35 and
13,743,895,347 at 0.40. The campaign's planned arena at full precision reads as 12,041,846,784
bytes, which is over the old ceiling by 0.13 percent and sits at about 88 percent of the new one.

Two qualifications belong on that, both re-derived by this lane rather than quoted:

- **The planned arena is deliberately over-read.** `arena_bytes` multiplies the server's `arena_mb`
  by 2^20 where the server computes it as a division by 10^6, which inflates every planned arena by
  4.86 percent. In the server's own unit the same campaign sits at about 95.5 percent of the *old*
  ceiling and would not have been refused at all. The over-read is deliberate and is not changed
  here; it is filed as
  `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`, because a
  guard 4.86 percent wide decided a question whose true margin was 4.5 percent the other way.
- **A ceiling is not a headroom figure for anything but this campaign.** The four flops the sample
  solves are the ones the ruling admits; nothing here says a wider campaign fits, and the driver
  builds each tree and reads its arena back before solving, so a plan that does not fit is refused
  rather than discovered.

### What was rejected, and why

- **Raise `CLASS_AGREEMENT_TOLERANCE` instead.** The tolerance is what refuses a cell whose combos
  disagree, and admitting the 1200-iteration quantized cell would take roughly 6e-4 - and buys a
  property that is unattainable at any value, because a committed row is rounded to thousandths and
  two values astride a thousandth boundary round apart at any separation whatever. The tolerance's
  own docstring claimed the opposite, that anything it tolerates cannot change a committed number,
  and that claim is corrected in this task: 0.7724 and 0.7726 are 2e-4 apart and round to 0.772 and
  0.773. Loosening the check would hide the drift rather than price it, so the value is unchanged.
- **Solve deeper on quantized arenas.** Measured, and it makes the disagreement worse rather than
  better: the in-class gap grows from 5.03e-04 to 2.48e-03 between 320 and 1200 iterations while
  exploitability barely moves. There is nothing at the bottom of that well.
- **Leave the ceiling at 0.35 and shrink the tree.** Every lever left is a poker decision already
  ruled - the menu is decision 11, the range floor is decision 12, the covered lines are decision 3 -
  so buying memory here means reopening a ruling to fit a guard, which is the move the decision list
  exists to stop.

### What this does not fix, and must not be read as fixing

The phase's own claim about why two combos of one class agree was wrong, and correcting it is part
of this task rather than a consequence of the ruling. `Solver::ensure_symmetric` transports solved
data between *chance* branches; `symmetrize_node`'s action arm walks its children and writes nothing
into an action node's own per-hand arrays, so the flop node the harvest reads - which sits above
every chance node - is never touched by it. **Nothing in the solver makes the combos of one class
agree at the harvested node.** They agree because the game is symmetric under the board's own suit
map and a converging solve approaches that, which is a fact about a particular run. Full-precision
arenas make the run converge; they do not install a guarantee, and the check remains the only thing
that would see a real mismatch between the solver's suit group and this repo's.

Three findings this ruling surfaced are filed rather than fixed here:
`QUANTIZED-ARENAS-PUT-A-FLOOR-UNDER-EVERY-EXPLOITABILITY-THIS-PHASE-MEASURED`,
`EVERY-ARENA-FIGURE-IN-THE-COST-RECORD-IS-A-QUANTIZED-ARENA-AND-FULL-PRECISION-ROUGHLY-DOUBLES-IT`,
and `THE-COMMITTED-ROW-IS-ONE-COMBO-RATHER-THAN-AN-AGREED-ANSWER`, which is the one the table's last
column is about and which this ruling shrinks rather than closes. So is
`NOTHING-TESTS-THE-MODULE-THAT-DECIDES-WHAT-EVERY-COMMITTED-CELL-CONTAINS`, found while reading the
harvest for this decision.

### What the committed record now carries

`data/artifacts/postflop/solve_config.json` gains `arena_storage`, from `RULED_SOLVE_CONFIG`, so the
configuration a reader reconstructs a cell from names the arena the same way it names the bet menu,
and `solve_config_errors` refuses a plan that disagrees with it. Every index entry gains
`arena_storage` too, carrying the reading taken off that cell's own built tree rather than the
constant the run asked for - per entry rather than in the header, because a cell is solved one board
at a time and a run can be resumed later against a server somebody else started, so the arena is a
property of the solve that produced a cell in the same way its iteration count is.

## 21. The out-of-position caller leads the flop, and what the phase does about it

**Ruled by Taylor, 2026-09-21. `frozen-into-data`**: what it decides is the committed cells, which a
later phase cannot revise without re-solving.

**Ruling. The flop-leading caller is accepted as the opponent this artifact models, and the phase
records it rather than re-solves.** The cells are a correct solution to the game as configured, that
game lets the out-of-position seat bet first, and betting first out of position is legal poker. The
obligation the ruling creates is a reporting one: the continuation-bet frequency is never published
without the lead frequency it is conditioned on beside it.

**Why it was asked.** The phase halted on 2026-09-16 because a flop cell solved against a broken
caller's range produced a continuation bet at 99.94% of range. The chart was re-solved, the lane
resumed, and the committed cell on `9c8c7c` bets **99.88%** of range with check at 0.0012, which the
deep run drives to 0.0000. The number did not move.

**The preflop re-solve is not the cause, and that is measured rather than argued.** The caller's
call branch on this line now holds 7.399 set combinations of a possible 9, which is the figure
`RE-SOLVE-THE-PREFLOP-CHART-WITH-A-REALISTIC-BLIND-THREE-BET` predicted. On this board the caller
holds a larger share of flushes than the raiser, 8.67% against 6.29%, and a larger share of sets,
2.51% against 2.02%.

**The cause is the node above.** The big blind leads 52.68% of its range on this flop, taking 73.9%
of its flushes and 74.0% of its sets with it, so what reaches the button is a range whose flushes
have fallen to 4.79% and whose sets have fallen to 1.38%. Betting almost everything into that is
close to coherent. The lead is documented behaviour rather than a tree defect - `RULED_SOLVE_CONFIG`
in `postflop_solve_driver.py` records that GTOpen gates the donk list on street above root, so a
flop-rooted solve lets the out-of-position seat use the ordinary bet list - but its poker
consequence had never been measured, and three of the four committed cells are that node.

**What was rejected.** Re-solving with the out-of-position seat unable to bet the flop. It needs a
patch to our own copy of GTOpen and one to two hours of solving plus repeating determinism and the
deep check, and it buys a continuation-bet number comparable to a published chart by modelling a
game in which a player may never bet a flop out of position. That is a different wrong answer, not a
right one.

**What this obliges.** The report publishes the button's continuation bet, the caller's lead, and the
composition of the range that therefore reaches the button, in one place. A reader who is shown the
first without the other two is being misled, and closing this phase with the record implying the
preflop re-solve fixed the continuation bet would be the false statement the phase is currently set
up to make.

## 22. The memory ceiling stays at 0.40 after the over-read was found

**Ruled by Taylor, 2026-09-21. `runtime-reversible`**: it is a guard on what may be planned, and
changing it re-plans rather than re-derives.

**Ruling. 0.40 stands.** Decision 20 raised it from 0.35 on a 0.13% overage. W6 then found that
`arena_bytes` reads `arena_mb` as 2^20 while the server computes it as 1e6, an over-read of
1.048576 exactly, so in the server's own unit the deep run sits at 95.49% of the **old** ceiling and
would never have been refused. Taylor was told this and kept 0.40.

**It is not purely an artefact, which is what decides it.** The four boards planned 11.60 to 12.24 GB
as the guard reads them, and the paired board's 12.24 GB is above the 0.35 ceiling of 12,025,908,428
bytes however the unit argument comes out, so 0.35 would have refused that board. The over-read is
filed as `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`
and stays open: a guard that is conservative by an undeclared five percent is a guard whose margin
nobody can state, and `scripts/measure_postflop_solve_cost.py` guards the same quantity in the
server's unit at 0.35, making the driver 9.0% looser than the script its own docstring claims to
match.

## 23. The conditioning entry the contract makes this phase repair or refuse

**Ruled by Taylor, 2026-09-21. `frozen-into-data`**: smoothing the input would change every
committed cell.

**Ruling, in his words: "idk if we need to solve for this. if it's what the solver says we should
stick with it."** So the smoothing is **refused explicitly**, which is the second of the two things
the contract allows, and the packet says so with the numbers below beside it rather than leaving a
reader to find them. The backlog entry stays open and unowned by this phase; a later phase that
wants a studyable range picks it up.

This is the repo's standing position rather than a new one: we ship GTOpen's output as solved, and
the burden is on the objection. Hand-smoothing a ladder the solver produced is us overriding a
judgement it actually made, on hands it measured as equal, with nothing measured to put in its
place.

The contract says `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` "is this phase's to repair or
refuse explicitly". The entry holds two problems and the phase has discharged one of them.

**Repaired: the unfloored residue.** Decision 12 ruled the 0.01 class-level floor and the committed
solves ran under it - `range_weight_floor` is 0.01 in `solve_config.json`, and the ranges it wrote
are 65 classes and 380 combos out of position against 84 and 498 in position.

**Not repaired, and still present after MAINT-34: the indifference artifacts.** Measured on the
committed ranges every cell was solved against, the caller's pair ladder reads 88 at 0.9993, 77 at
1.0, 66 at 1.0, 55 at 1.0, 44 at 0.9997, **33 at 0.208** and 22 at 0.9713, with 99 at 0.4672. Threes
call about a fifth as often as fours and deuces for no strategic reason, which is the exact shape
the entry describes. It has a board-dependent cost rather than a cosmetic one: on any flop holding a
three the caller arrives with roughly four fifths of its sets of threes missing, and `Ac8c3c` - the
listed-not-held cell committed last night - is such a board.

**What the packet must therefore say**, and it is the whole of what the refusal costs: the committed
cells are solved against a caller whose small pairs are an arbitrary pick among options the preflop
solve judged equal, and on a flop holding a three that caller arrives with about four fifths of its
sets of threes missing.

Decision 12 carries a do-not-smooth argument and this ruling does **not** rest on it.
`DECISION-12-S-DO-NOT-SMOOTH-ARGUMENT-DESCRIBES-A-RANGE-THAT-WAS-SUPERSEDED` is this lane's own
finding that the argument was made about a range MAINT-34 replaced, so it could not be leant on as
it stands and was not put in front of Taylor as a reason. The ruling above was taken on the
measurement, not on the older argument, and that entry stays open on its own account.
