# Phase 16 judgment calls

These are the choices about what a committed postflop solution covers, and what the bot does outside it.
No test in this repo settles them.
A solution that covers the wrong spots passes just as green as one that covers the right ones, and a bot that guesses on an unseen board looks exactly like a bot that knows.

They are recorded ahead of the phase because the phase is gated on them. When this file was
written `verification/loop_policy.yml` marked phase 16 `needs_human_data`; it now reads
`needs_human_data: false`, because the source it was waiting on turned out to exist. What still
gates the phase is every `frozen-into-data` item below that has no answer, which stage 3 halts on
one at a time.

Every item carries a reversibility class, which the loop driver reads at stage 2 to decide whether it must stop for a human.

- `runtime-reversible`: the choice only changes behavior at query time, so a later edit changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact that every later measurement then runs against. The loop halts until a human answers.

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
And no solve in this repo has ever been timed to a real exploitability target: only a 300-iteration preflop smoke test was ever run, and solve time and determinism are both still on phase 10's unverified list.
So affordability at any depth is unmeasured.

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
The cost is not linear: one flop spot is 49 turn spots and 48 rivers below each of those, before
any preflop line is counted, and each has to be solved to a target exploitability rather than
derived. This sentence read 47 and about 2,160 until 2026-09-08, which is hero's view of a board
he holds two cards against; the counts table above had already been corrected and this line had
not.

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

## 2. What the bot does on a board it holds no cell for

Reversibility: frozen-into-data

Any canonical subset smaller than all 1,755 flops guarantees the bot meets boards it has not solved. Suit isomorphism is exact and free; GTOpen already exploits it internally. Rank texture is not: mapping an unsolved `K72r` onto a solved `Q83r` is a heuristic, and `AGENTS.md` forbids heuristic guessing for missing chart spots.

So this is a boundary question, not an implementation detail. Either the rule holds and the bot refuses on an unsolved texture, or the rule is amended for board texture specifically, which is a `contract-update` to `AGENTS.md` in its own right.

Default: **solve all 1,755 flops and keep the boundary.** With a flop-only solution the runout fan-out is gone, so the full canonical set is the thing that removes the question rather than answers it, and the bot never faces a flop it has no cell for. If 1,755 per line proves unaffordable once solve time is measured, the fallback is fewer preflop lines, then a flop subset plus refusal, and never a subset plus abstraction.

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

That also settles what GTOpen's 47, 95 and 184 flop subsets are for here, which is nothing.
They are study sets: a human reads texture patterns off a report. As a bot's lookup table a 47-flop subset covers 2.7% of flops and refuses the rest, so it is only usable with the abstraction decision 2 defers.

Growing this later is cheap and it is the pattern the repo already runs, verified rather than assumed:

- `PreflopChartLibrary.__init__` takes a sequence of artifacts, sorts them, and rejects only a genuine duplicate spot key, so an added artifact file needs no code change.
- The lookup fail-closes, so an added spot strictly adds capability and cannot alter a spot already covered.
- A refusal inventory ranks the gap most-reached first and regenerates every gate run. Which
  inventory matters: the self-play one counts refused *hands*, the corpus one counts refused
  *decision points*, and the grouping key of the self-play one is the whole detail tuple, which
  `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` records as shattering into singleton rows at
  any non-flat table.

What is *not* cheap later is the spot key itself. Adding spots at a fixed key is additive; changing what the key can express re-derives every committed cell, which is why phase 12 sits ahead of phase 14 and why the ordering rule is format before data. So the one thing this phase must get right up front is the postflop spot key, and coverage may start as small as it likes.

## 4. Exploitability target, and whether the solve is reproducible

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
- **Determinism: byte-identical.** Same root-strategy sha256 across two runs in separate processes
  against a restarted server, zero per-action divergence, zero combos present in one run only, and
  the same digest as a row recorded a day earlier. No tolerance was needed, so the phase 10
  fallback of recording a tolerance in place of a checksum does not arise.

Default: **target 0.3% of the starting pot, and record the achieved percent, the iteration count
and the strategy digest on every committed spot.**

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

## 6. How the committed flop artifact is encoded, given that it does not fit

Reversibility: frozen-into-data

Filed 2026-09-08 at the contract stage, from a measurement rather than from reading. Decisions 1
and 2 fixed the depth and the breadth on solve-time grounds. Disk was never measured, and the file
that should have caught it said there was no size check. There is one, and the artifact does not
fit it.

The measurement, every input recomputed here rather than quoted:

- `data/artifacts` is capped at 20 MB in `DIRECTORY_BYTE_LIMITS` in `scripts/check_file_sizes.py`,
  since `2430894` on 2026-08-18. The tree holds 5,197,325 bytes, so headroom is 15,774,195.
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
floats and one free weight per class, one two-action node for one line measures 7,740,095 bytes,
which is 0.49x the headroom: it fits, with room for a second node. That same encoding buys 2.04
nodes at two actions, 1.02 at three storing two free weights, and 0.68 storing all three. A flop is
not one decision - hero acts, villain answers, hero faces a bet or a raise - and decision 3 asks
for a head of common preflop lines, plural. Several nodes across several lines is what the phase
needs, and one node for one line is what the cap affords.

The chart's own format is worse, and the figures are given as pairs that recompute from the rates
above rather than from any other rate. One line, one node, only check and bet: 36 MiB compact, 66
MiB as committed, 2.4x and 4.4x. Ten hero nodes at three actions: 544 MiB compact, 986 MiB as
committed, 36.2x and 65.6x. Building the structures directly rather than multiplying the rate gives
43, 76 and 1,007 MiB, so the multiplications err low. Compression is not available:
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

The four ways out, stated without a recommendation because the cost of each falls in a different
place:

1. **A binary encoding.** The repo already commits one, `preflop_eq169.bin` at 114,244 bytes with a
   `.source.json` beside it, so the precedent and the provenance pattern exist. Float32 at one
   node and three actions is 14.7 MB per line, which fits once and leaves nothing. Quantising a
   weight to one byte gets a node-line to about 3.7 MB. It costs the property that a reviewer can
   read the artifact, which is the property `check_file_sizes` says the cap exists to protect.
2. **Fewer preflop lines.** Decision 3 already prunes on this axis and calls it the honest one. But
   even a single line does not fit in JSON, so this alone does not close the gap.
3. **Raise or replace the cap.** `check_file_sizes.py` says in its own comment that exceeding a
   limit here "is a halt and a decision, not a number to raise", which is what this entry is. The
   cost is repo weight, permanently, since git keeps every version of a committed artifact.
4. **Commit fewer nodes per flop.** Store hero's flop root only and refuse every later flop node.
   That is 36 MB compact for one line, still over, and it buys a bot that opens a flop and then
   refuses inside the same street, which is a worse seam than the turn seam decision 1 accepted.

What is **not** on the list: grouping unsolved boards onto solved ones. Decision 2 deferred that as
`POSTFLOP-BOARD-ABSTRACTION` and `AGENTS.md` forbids heuristic guessing for a missing chart spot.
A size problem is not a licence to reopen it.

Answer:

## 5. Whether the pot-odds river call ships alongside

Reversibility: runtime-reversible

`POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK` calls a river bet when equity against the full unseen deck beats the price. It needs no solved data and invents no constant: equity is `(wins + ties/2) / 990` from the enumeration `hand_cannot_lose` already runs, and the price comes off the query.

A uniform unseen deck flatters hero, so this makes the bot over-call as the mirror of its current over-folding. Under the flop-only default it is also the only thing that acts on a river at all.

Default: build it, behind an explicit flag, and report the frequency it fires rather than claiming it is correct. It is runtime-reversible because no committed data records it; it is a rule the query evaluates.

Answer:
