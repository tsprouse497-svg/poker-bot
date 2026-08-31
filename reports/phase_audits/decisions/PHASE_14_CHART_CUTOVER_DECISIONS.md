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
from a model that cannot see multiway equity. Those are 8.3 percent of the corpus's 3,048 preflop
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

**Superseded again by Taylor on 2026-08-25: keep a node when at most one opponent has voluntarily
invested beyond the blinds *and* at most two players are still live. 86 spots.** The 2026-08-24
ruling was made on the understanding that the history clause alone selects the nodes GTOpen prices
exactly. It does not. The approximation bites at *terminals* and a node's strategy is
backward-induced over every terminal below it, so a statement over the still-reachable subtree is
**conjoined** with the history one rather than replacing it. Counting seats that have not folded as
well as seats that have acted: 110 pass the history clause, 5,472 pass the subtree clause, **86 pass
both, and 24 of the 110 have a multiway terminal still reachable**.

**Why both clauses and not just the subtree one.** The subtree clause alone admits 5,386 further
nodes whose remaining terminals are genuinely heads-up but which are reached through a cold call.
Every one of those arrives with a range the same defect produced - the solver almost never cold-calls
because cold-calling invites the terminals it misprices - so the node is priced correctly from here
on and fed a distorted range to price. The predicate-change review settled the strict reading of
"invested" for the same reason and this is that reading's consequence, not a new rule.
Those 24 are four of the five opens, the RFI defences with seats still behind, and the decisions
facing a 100bb open-jam, and the defect is visible in their cells - flatting a 2.5bb open runs 21 to
24 percent for the big blind, who closes the action, and 0.07 to 4.5 percent for every seat with
players still to act. Every three-bet frequency is close to right. Hero's aggressive branch survives
the mispricing and hero's passive branch does not, because flatting is what invites the multiway
terminals the model underprices.

`SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS` is the general form of the error and
is filed. This is the second time this decision has been superseded and both supersessions ran the
same way: a predicate that was ruled on one property turned out to select on a different one.

**Measured before the ruling, not after.** The 86 answer **563 of the corpus's 3,048 preflop
decision points, 18.5 percent**, against 2,795 for the 110 and 2,232 for the 24 alone. The
disposition put to Taylor carried this as an upper bound of 568 derived by subtraction; he made the
ruling conditional on the real figure, and it is 563. Method and full tables in
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-eighty-six-coverage.md`, which
reproduces 110, 5,472, 86, 24 and 2,232 exactly from a fresh walk.

**The corpus denominator is 3,048, not 3,054.** Every stage-4 document said 3,054, which counts the
six preflop decisions of `pluribus/41b/204` - a hand the committed sample excludes for fractional
finishing stacks. Corrected wherever it appears in this phase. No conclusion moves: 2,232 of 3,048
is 73.2 percent and the multiway share is 8.3 percent under either denominator.

**What the 86 are.** 1 spot at four prior actions, 10 at five, 30 at six, 30 at seven and 15 at
eight; 15/14/13/12/12/20 across LJ, HJ, CO, BTN, SB and BB; 11 at full reach; four menus - 50
fold/call, 20 fold/call/raise/jam, 15 fold/call/jam and 1 fold/raise/jam. The minimum arriving reach
over the set is 2.62 percent, so all 86 clear the retired 2 percent floor too and conjoining it
changes nothing for the third time.

**The cost Taylor accepted, stated in what the bot can do.** Only the small blind's opening range
survives; the bot cannot open from LJ, HJ, CO or BTN and refuses those decisions with a code. What
it keeps whole is the blind-versus-blind skeleton, the big blind closing against an open, and the
three-bet, four-bet and five-bet continuations - the part the independent poker review said it would
trust. Against the 110 coverage falls by 2,232 corpus decisions, every one of which the 110 would
have answered from a mispriced cell.

**Against the artifact being replaced it is not a pure gain, and the 2026-08-24 wording said it was.**
The retired chart's 36 spots are all heads-up under the superseded history predicate, which is what
made "nothing the bot answers today is lost" true of the 110. Under the terminal-clean predicate only
**22 of the 36 survive and 14 do not**: the LJ, HJ, CO and BTN opening ranges, every RFI defence with
seats still behind (`HJ/LJ:raise@2.5`, both CO spots, the three BTN spots) and all four small-blind
defences against a non-blind open. What survives whole is every big-blind defence, every three-bet
continuation, the small-blind open and the blind-versus-blind pair. So the cutover gains 64 spots and
gives up 14, rather than gaining 50 and giving up none, and the bot's opening coverage goes from five
positions to one. This was measured on 2026-08-25 while reviewing the ruling's own paperwork and is
carried to Taylor as a blocker rather than absorbed, because the cost he accepted was stated in the
form that was true of the 110. **He confirmed on 2026-08-25 that the ruling stands** with the bot's
opening coverage falling from five positions to one until the engine fix lands. The consequence is
therefore a ruled cost rather than an open question, and the closing measurement states it as one:
14 retired spots refused, 64 gained, opening coverage five seats to one.

**This is half a ruling; the other half is the engine.** Taylor took the disposition's option 3
rather than its option 2: ship the 86 now, fix the source, and add the rest back as new keys.
`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` therefore stops being a deferred v2 note and becomes
scheduled work that the missing 24 spots are waiting on. It is an engine change inside GTOpen - true
multiway equity at `KIND_POT_SHARE` terminals, benchmarked and re-validated - and the calibrated
realization fit cannot be extended over it, because the postflop engine behind that fit is heads-up
only. Adding the spots afterwards costs no re-keying: the spot key already encodes the action
sequence, so `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL` is not paid twice.

**What this moves in the rulings below.** Decision 5's reach field gains a present reason rather than
a prospective one, since 11 of 86 sit at full reach against 35 of 110. Decision 6's sizing table was
ruled on 35 spots offering both a named raise and a jam; over the 86 that is 21, with 15 more
offering a jam and no named raise, and the ruling must be restated against those counts before the
freeze. Decision 8's two exclusion codes stand and now separate a larger set: the second code, for a
node the source misprices, is what a later phase reads to find the 24 by name. Decision 10's
obligation to show that some aggregate form of its two relations passes over the retained set is
unchanged in kind and is now owed over 86 nodes rather than 5,626.

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

**Superseded in its premise on 2026-08-30, by decision 14.** This item ruled ship-as-solved on the
lojack opening 44 at 72.81 percent. **The lojack opening range is not in the committed 51** - the
re-sourced artifact holds exactly one spot with an empty action sequence, `t6/d100/SB/rfi`, and no
non-blind opening range at all. So the pair this item was ruled about is not in the shipped chart and
its ruling now decides nothing. The contract accordingly reopens
`SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` rather than closing it here, and the measurement is retaken
on whatever non-monotone pairs the re-sourced chart actually contains. Taylor is told the premise
evaporated rather than asked to re-rule a spot that no longer ships.

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

**Re-measured on the re-sourced solve, 2026-08-30, per decision 14.** The ruling stands and so does
the effect: against a 2.5bb small-blind open the big blind now folds **51.61 percent** where it
folded 50.98 before, from a small blind opening **54.30 percent** where it opened 54.09. Removing
`add_allin` did not touch the realization bias, which is the expected result - the bias is in how
flops are priced, not in which raises are offered - and it is recorded here so the source card's
number is the one this phase measured rather than the one it inherited.

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

**Restated a third time on 2026-08-30, and this time the premise is gone entirely.** Decision 14
re-sourced the solve with `add_allin: false`, which removes the jam everywhere it was offered
without reference to the pot. Measured over the 51 spots this phase now commits: **no spot offers
both a named raise and a jam.** Twenty-one offer a named raise only, fifteen offer a jam only - all
fifteen being five-bet spots, where the 3.0 multiplier puts the raise at 67.5bb and
`allin_threshold` snaps it to the stack - and fifteen more offer no raise at all. The shove is 18.6
percent of hero's aggressive volume across the committed set when that is measured combo-weighted -
but never as an alternative to a named price at the same spot.

The 18.6 figure is stated with its definition because it is **not** like-for-like with the 60.6 and
5.0 above, both of which this item defines as shares of hero's *reach-weighted* aggressive volume.
Measured that way the shove is **13.7 percent**; an independent measurement under a slightly
different reach normalisation got 12.1. The three numbers must not be read as a trend.

So the 60.6 percent that the 2026-08-24 extension was ruled on, and the 5.0 percent it was restated
to, are both properties of trees this phase no longer ships. **The multi-size schema is retained and
is now entirely unexercised by the committed data.** It is retained because it costs nothing,
because the multiway family that returns later is where the case for it lived, and because reverting
it would be a schema change made to fit a temporary dataset. But the contract must say so plainly:
a test asserting that a spot offering two prices is described by two prices **passes vacuously over
this artifact**, and a phase that lets such a test stand unlabelled has a check that cannot fail.
That is the honest cost of keeping the schema, and it is recorded rather than left for a later
reader to discover. Taylor is told the premise is gone; reverting to one price per spot remains his
call and nothing here forecloses it.

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

**The ruled bands are void as stated, 2026-08-30, and must be re-registered before the measurement
runs.** Every band above is a quarter to one times an opener's defence delta computed on the
superseded export, and decision 14 moved every one of those deltas. A pre-registration whose numbers
were fixed against data the phase no longer ships is not a pre-registration; leaving it in place
would let the closing measurement be read against whichever set of bands happened to suit it, which
is the exact failure this item was written to prevent. **The form of the ruling stands** - per
opener, a quarter to one times that opener's defence delta, written down before the numbers are
seen - and only the arithmetic is redone. The re-registration happens against the re-sourced export
and before the closing measurement is run, not after.

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

**Premise superseded on 2026-08-30, same cause as decision 2.** The violation rule and its one-point
tolerance were tuned so that exactly one violation survived at the lojack's 44-versus-33 pair. That
pair is in no committed spot, because the lojack opening range is not in the 51. The tolerance is
therefore calibrated against data this phase does not ship and must be re-derived from the
re-sourced chart before it is frozen - which is also what the contract's requirement to re-measure
the aggregate gate over the 51 before freezing it demands.

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

**Superseded by decision 15, 2026-08-30.** This item ruled that the conclusion is read off the
agreement rate, meaning the permissive one. Decision 15 then established that the permissive rate
was substantially measuring menu width and fell 24.0 and 16.2 points as the chart improved. Both
rulings standing together would have a report print the strict rate beside the permissive one and
then read its conclusion off the permissive one, which is precisely what the contract calls stating
the reverse of the truth. **The conclusion is read off the strict sampled-action rate, with the
permissive rate and the cell-purity statistic printed beside it as context.** Recorded here rather
than only in decision 15 so that this item cannot be cited on its own.

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

## 14. Whether the solve is re-sourced with `add_allin: false`

Reversibility: frozen-into-data

Added 2026-08-30, after the phase reached stage 6 and its build was rejected on the poker. This
item supersedes **phase 10's decisions 2 and 3 for this phase**, which fixed the config verbatim
with `add_allin: true` and set a 0.01 bb target at a 2,000-iteration cap. Phase 10 is completed and
its decision record is left exactly as written; a packet is a snapshot of what a phase believed,
and the correction belongs here rather than inside it.

**What was found.** Two independent stage-6 reviewers, one mechanical and one on the poker, found
the committed chart stacking off 100bb with a range inverted against hand strength. At
`t6/d100/BTN/BTN:raise@2.5,SB:raise@7.5` aces never jammed and 44 jammed at 1.0; at
`t6/d100/BB/BTN:raise@2.5` aces three-bet to 7.5 and never jammed while AKo jammed 0.66. Across the
36 spots where any hand could jam, aces jammed 0.000 at five spots where 44 jammed up to 0.979, and
those five arrive in 24.0 percent of hands.

**The mechanism, read out of the solver rather than inferred.** In
`crates/solver/src/preflop/mod.rs:2204`, `add_allin: true` pushes `cfg.stack` onto the raise menu at
every node where a raise is legal, with no reference to the pot, which is how the big blind comes to
shove 100 to win 4. The separate `allin_threshold` at `:2219` only snaps a raise already landing at
or above 67bb up to the stack. The units were checked rather than assumed: the percent-valued
threshold documented on `SpotRequest` is the postflop endpoint, while `/api/preflop/spot`
deserialises into `PreflopConfig`, whose validator at `:2115` requires `(0, 1]`. The ruled 0.67 is
correct and means 67 percent.

**Convergence, tree-summed best-response gap in bb.** Committed solve 0.0062379 at iteration 300 of
2,000, having stopped early on beating the 0.01 target. With the flag on at the full cap, 0.0020266.
At 10,000 iterations, 0.0018446 - nine percent better for five times the work, with the bad cell
bit-identical, so the defect is structural rather than unconverged noise. With `add_allin: false` at
the cap, **0.00015591 at iteration 1,900**, roughly forty times better than the committed solve.

Options: keep-add-allin-and-run-the-full-cap | re-source-with-add-allin-false | exclude-jam-spots
Answer: [re-source-with-add-allin-false]

**Ruled by Taylor, 2026-08-30: re-source with `add_allin: false` and restart the phase.** Rejected:
running the full cap with the flag on, which the 10,000-iteration diagnostic refutes; and excluding
the jam-bearing spots, which would treat a source defect as a coverage decision and would drop
genuine five-bet spots along with the artefacts.

**The solve target becomes `0.00016` at the same 2,000-iteration cap.** The number is chosen against
the measured trajectory rather than picked for roundness: the run first meets it at iteration 1,900
of 2,000, so the cap very nearly binds and the phase does not stop early the way the committed solve
did at iteration 300. That is the whole justification and it is worth stating what is *not* part of
it, because an earlier draft of this item got it wrong twice.

First, this item previously said "0.00015 is never reached". That is not supported by anything
measured. The run terminated at iteration 1,900 on meeting the 0.00016 target, so the trajectory
over iterations 1,901 to 2,000 was never observed; `status.json` records `iteration: 1900` and
nothing beyond it. A lower target might or might not be reached inside the cap, and this phase does
not know which.

Second, it cited `tests/test_chart_cutover_evidence.py:652` - `achieved_gap_bb < target_gap_bb` - as
a frozen assertion the target choice keeps true. The line does stay true, but the citation was
misleading and is withdrawn. That assertion sits inside
`test_the_committed_solve_is_the_one_phase_ten_captured_and_no_re_solve_replaced_it`, whose other
assertions pin `iterations == 300` and both checksums against the superseded export. The test exists,
in its own docstring's words, to make a silent re-solve loud - so it is *designed* to fail on exactly
what decision 14 rules. It failing is the canary working, not a constraint on the target, and it must
be migrated at stage 4 under the contract's regression expectation. Nothing about the target choice
depends on it.

**What the re-source did and did not fix, measured.** The tree goes from 38,828 action nodes to
33,969, and the predicate selects 51 rather than 86 - a strict subset, 35 lost and none gained, all
35 of them all-in-facing spots that existed only because opponents jammed at arbitrary nodes. The
inversion is gone: 15 spots still offer a 100bb jam and every one is a five-bet spot, with AA taking
it at weight 1.000 at all fifteen and no spot where a low pair jams and aces do not. Five-bet jams
survive exactly as the code predicts, because the 3.0 multiplier puts a five-bet at 67.5bb and the
threshold snaps it.

**What the re-source did NOT fix, and the stage-6 note is wrong about one of them.** That note marks
blocker B2 `[resolved]` on the reasoning that the four-bet-facing spots it named were re-solved. They
were, and the defect survived: at `HJ/LJ`, `BTN/LJ` and `CO/HJ` four-bet lines, JJ, TT, 99 and 88 all
continue at **0.000** while 76s, 87s and JTs continue at **1.000**, pure folds of jacks beside pure
calls of 76 suited, at full reach. **B2 is not resolved and the note's `[resolved]` mark is false.**
It is committed at `a386c77` and stays as written, because a packet is a snapshot of what a phase
believed; this is the correction.

Also unfixed. `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`, re-measured rather than assumed, still
holds at a 19.63 to 22.44 percent flat band against openers 6.07 to 28.09 wide. Strict rank
dominance did not improve: the same relation over the same 51 spots gives **54 inversions on the
re-sourced chart against 52 on the superseded one**, with pure 0-versus-1 flips between adjacent
kickers (`J6s` 0.000 beside `J5s` 1.000, `Q7s` 0.000 beside `Q6s` 1.000). And the jam *composition*
is still inverted even though the headline check passes: at
`SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` the five-bet range is AA at 1.000 and **87s at 0.995**
while KK, QQ and AKs all flat and AKo folds 0.782.

The check this item's ruling was verified against - no spot where a low pair jams and aces do not -
passes, and is too narrow to have caught any of that. It is kept as a regression canary and is not
evidence that the ranges are sound.

## 15. How the corpus agreement rate is reported after the re-source

Reversibility: runtime-reversible

Added 2026-08-30. Scoring the same corpus against both charts showed the permissive agreement rate
**falling** as the chart improved - Pluribus 94.4 to 70.4, humans 89.3 to 73.1 - while the strict
sampled-action rate barely moved, 70.8 to 66.2 and 69.8 to 68.5.

The cause is the definition. Agreement means the chart gives the observed action nonzero weight, so
a cell with every action nonzero cannot disagree with anything. Over the 51 spots both charts share,
the superseded chart held 1,669 of 3,985 cells in that state, averaging 2.209 nonzero actions per
cell at 21.0 percent pure; the re-sourced chart averages 1.323 at 73.0 percent pure. The old rate
was substantially measuring menu width.

Default: **the permissive rate is never published alone.** The report prints the strict
sampled-action rate and the cell-purity statistic beside it, and states that the fall is what a
converged chart looks like rather than a regression. Filed as
`AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`.

Runtime-reversible because it changes what a report prints rather than what the artifact holds, so
it proceeds on this default and is reported afterwards. It does bear on a frozen-into-data question
this phase must still answer - whether `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` closes - and the
contract now requires that entry to be restated against the strict rate rather than the permissive
one.

## 16. Whether the phase ships a chart derived from this source at all

Reversibility: frozen-into-data

Added 2026-08-30, after the stage-1 reviews of the re-sourced contract. This item exists because the
re-source succeeded at what it was ruled to do and the chart was still not fit to ship, which is a
different question from any this record had asked.

**What the re-source fixed, and what it did not.** Decision 14 removed `add_allin`, and the defect it
was ruled against is gone: no committed spot jams where aces do not, the 15 surviving jams are all
genuine five-bet spots, and convergence improved roughly forty-fold. What survived, all re-measured
by the coordinator rather than taken on a reviewer's report: at the `HJ/LJ`, `BTN/LJ` and `CO/HJ`
four-bet lines, JJ, TT, 99 and 88 continue at **0.000** while 76s, 87s and JTs continue at **1.000**;
strict rank dominance did not improve, at **54 inversions against the superseded chart's 52 over the
same 51 spots**; and the five-bet composition is inverted, with 87s jamming 0.995 at
`SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` while KK, QQ and AKs flat and AKo folds 0.782.

**The cause was then found, and it is neither the solver nor the config.** Read out of GTOpen at
pinned commit `4aee435`. Under `realization: "calibrated"` every postflop terminal is priced
`pot x equity x R`, with `R` taken from `class_base` in `cache/realization_fit.json`: 169 numbers,
one per hand class, constant across the entire tree. The table assigns **76s 1.1333, JTs 1.0641,
KK 1.0473, 87s 1.0162, 22 0.9102, QQ 0.8556, JJ 0.7493, TT 0.7196, 99 0.7196**. So it rates 76s a
better realizer than JJ, TT, 99, QQ and KK, and 22 better than every pair from 33 through JJ. Mean
pair base 0.8398 against mean connector base 0.9539.

**The link is causal, not circumstantial.** Sorting the four-bet node by `class_base` sorts the fold
decision: continuing hands have mean `R` 1.0129 and folding hands 0.7918, and 76s is the
second-highest-`R` hand at that node, above KK. Every inversion the reviews found in the chart is
present in the table as an inversion of the table - J6s 0.5880 under J5s 0.8105, T6s 0.5847 under
T5s 0.7601, Q7s 0.7280 under Q6s 0.7899, 22 over 33/44/55. **The chart is a correct CFR solve of a
payoff function that is wrong**, and folding jacks to a four-bet while calling 76 suited is the
rational response to that input.

**Why the table is like that, from its own fitter.** `m5_spots/fit_phase_c.py` and the table's meta
block: `r2` is **0.1885** over 153,321 observations, and "equity itself still deliberately excluded
as a model input", so nothing makes the table monotone in hand strength structurally. Monotonicity
is patched along a hand-picked list instead - "weighted-PAVA domination chains (broadway aces, K/Q
kickers, suited>=offsuit; wheel aces unchained)" - and the ladders off that list are exactly where it
inverts: J kickers, T kickers, and pairs against connectors. Filed as
`REALIZATION-FIT-TABLE-IS-NON-MONOTONE-IN-HAND-STRENGTH` with the secondary finding that the engine
path also discards the fit's own SPR coefficients.

Options: ship-as-solved | ship-flagged-not-for-study | halt-and-fix-the-source
Answer: [halt-and-fix-the-source]

**Ruled by Taylor, 2026-08-30: halt phase 14 and fix the source.** The chart is not committed. The
bot keeps playing the retired raked `six_max_nl25_100bb.json` until a source exists whose postflop
pricing is monotone in hand strength.

Rejected, and the reasons are worth keeping. **Ship-as-solved** was the standing disposition for
each of these findings taken separately - decision 2 ruled the non-monotone pair ship-as-solved,
decision 6 ruled the four-bet continuations ship-as-solved, decision 3 accepted the realization bias
onto the source card - and it does not survive them being traced to one cause with a measurement.
Those rulings were made on spot-level aggregates and single examples, before any measurement over a
shipped set existed; what is now on the table is an `r2` of 0.19 with known, only-partially-patched
monotonicity failures, proposed as the reference every later phase is measured against.
**Ship-flagged-not-for-study** was rejected as the worse of the two ship options rather than a
compromise: it commits the ranges anyway, and an artifact whose own flag says do not study it is a
training chart that cannot be used for training.

**What this does not invalidate.** Decision 14 stands: `add_allin: false` fixed a real defect and
`SOLVE_TARGET_GAP_BB` stays at the ruled `0.00016`, so a later re-source starts from the corrected
config rather than rediscovering it. The derivation pipeline is proven end-to-end on real solver
output - census, schema, provenance, sizing table, refusal path, determinism - and re-runs in about
four minutes against a corrected source. What is withheld is the artifact, not the machinery.

**The gate stays red while halted, and that is deliberate.** `RULED_CONFIG["add_allin"]` is `False`
while the committed export was built with `True`, so `config_errors` refuses it and
`pytest_derived_chart` fails. Reverting the constant to make the gate green would erase the one
correction this restart established. The lane is halted, not closing out, so it owes no green gate;
`main` is unaffected.
