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

**Recount, 2026-08-31.** The list runs to **22** items, not thirteen: sixteen are
`frozen-into-data` (1 to 6, 9, 10, 14, 16 to 22) and six are `runtime-reversible` (7, 8, 11, 12, 13,
15). The sentence above describes the list as it stood on 2026-08-23.

**No item is open.** Decision 22 was raised on 2026-08-31 by the independent review of this re-cut and
**withdrawn the same day**: a search of the record found that Taylor had ruled the question on
2026-08-26 and that the ruling had shipped and been frozen while living only in a stage-4 review note.
It is transcribed at the foot of decision 10, along with four other rulings this list had never
carried - two on decision 6, one on decision 5, one on decision 1. All of them were taken in
implementation mode, which may not edit a decision record, and each note said in terms that it owed a
transcription at the next `contract-update`. This is that task.

**What this list has been re-cut against, 2026-08-31.** Decisions 20 and 21 are ruled, and between
them they falsify three things every item from 1 to 19 was written on: the phase commits **36** spots
rather than 51, **no committed spot offers a jam**, and the **corpus measurement is phase 17's**.
Every item from 1 to 21 now carries one of three dispositions, added on 2026-08-31: it still holds, it
is amended with what changed, or it moves to phase 17. Items **7, 9, 11, 12 and 15 move**. Nothing here
reopens a ruling and nothing that was committed before this re-cut was edited - a packet is a snapshot
of what a phase believed, so the corrections are additive and each says what is no longer true.

**Two independent read-only reviews read the re-cut before it was committed**, one mechanical and one
on the poker, neither having written any of it and neither having seen the other's work. They are
rounds 3 and 4 of `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-02-decisions.md`. Four
blockers between them: the re-cut had settled item 10's gate question by prose when it is Taylor's,
which is why decision 22 exists; it had over-extended item 3's realization reframing to kicker
inversions realization does not explain; it had reinstated an "`100.0` is not in hero's menu" sentence
that a contract review had already rejected; and it had left item 1 instructing the closing measurement
to publish a spot count the committed 36 falsifies. All four are corrected in place with what the first
draft said.

## What was measured first
**Superseded snapshot, 2026-08-31. Read this section for diagnosis, never for work.** Every figure in
it was measured on the 38,828-node export built with `add_allin: true`. Decision 14 re-sourced the
solve to **33,969** action nodes, decision 20 fixed the committed set at **36** spots, and the
contract requires each of these quantities measured again at stage 6 against the artifact that ships.


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
**Superseded, 2026-08-31.** This section reconciles four rulings against the 5,626-spot reach floor
decision 1 no longer uses. The byte budget it protects has nothing to bite on at 36 spots, decision
2's re-solve was overtaken by decision 14's re-source, and decision 9's bands are void and re-taken
in phase 17. Kept as the record of how the rulings read on 2026-08-24.


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
**Amended 2026-08-31 by decisions 14 and 20: the predicate still selects, it now selects 51, and 36
are committed.** Neither ruling touches the predicate, which is why this is an amendment rather than a
third supersession. Decision 14 re-sourced the solve with `add_allin: false`, and over the smaller
tree - 33,969 action nodes against 38,828 - the same two clauses select **51** rather than 86. That is
a strict subset: 35 lost, none gained, every one of the 35 all-in-facing and existing only because
opponents jammed at nodes no pot size justified. Decision 20 then **withholds the 15 four-bet-facing
spots** of those 51 for a second and different pricing reason - the fit behind `calibrated` has no
four-bet-pot cell - so **36 are committed**. The withholding is a second exclusion standing beside this
item's, not a narrowing of this item's rule, and the contract forbids lifting either to recover
coverage.

**What that does to the coverage cost recorded above.** The 563 of 3,048 corpus decisions was measured
on the 86 and is not the committed set's coverage. What 36 spots answer is measured in **phase 17**,
which owns every corpus figure per decision 21 and whose contract requires each exclusion's cost
reported separately so one ruling is not charged with another's. The cost stated in what the bot can
do is unchanged in kind and larger in degree: only the small blind's opening range survives, and the
bot now also refuses every spot where it faces a four-bet - which is every spot where it could jam.

**One property of the ruling that survived both moves and is worth naming.** This item was ruled twice
on a predicate that turned out to select on a different property than the one it was ruled about, and
`SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS` is the general form. Decision 20's
withholding is stated over spots rather than terminals and knows it: every committed spot is
backward-induced over four-bet-pot terminals whether or not the four-bet node itself is committed, so
refusing those 15 bounds the exposure rather than removing it. That residual is
`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` and it is accepted, not fixed.
**Corrected 2026-08-31 after independent review: the spot arithmetic in the 2026-08-25 block is
falsified by the committed 36, and this block's first draft corrected only the corpus half of it.**
That block says 22 of the retired 36 survive and 14 do not, that the cutover "gains 64 spots and gives
up 14", and instructs the closing measurement to state "14 retired spots refused, 64 gained". Those are
properties of the 86.

**Recomputed against what ships rather than quoted.** The retired chart read at the pin decision 7 names
holds 36 `spot_id`s; intersecting them with the committed 36 gives **5 survivors** - `BB/LJ:raise@2.5`,
`BB/HJ:raise@2.5`, `BB/CO:raise@2.5`, `BB/BTN:raise@2.5` and `SB/rfi`. So **31 retired keys are refused
and 31 spots are new**, and the cutover is **net zero on spot count**, not plus fifty. Phase 14's own
contract already carries the same result from the other side - 31 of the retired 36 collide with
nothing the new artifact declares and only 5 collide exactly - so the contract was right and this list
was the document disagreeing with it.

**What that leaves of the accepted cost.** Only the opening-coverage clause survives unchanged: the
bot's opening coverage falls from five seats to one. The closing measurement states **5 survived, 31
refused, 31 gained, opening coverage five seats to one**. This is a property of two files rather than
of the corpus, so it stays with phase 14 and does not travel to phase 17 under decision 21's seam.
**Transcribed 2026-08-31 from `stage-04-predicate-change-review.md`: Taylor ruled the three
predicate-change blockers on 2026-08-27 and the decision list never recorded it.** Implementation mode
may not edit a decision record, so the ruling was written into the review note with a pointer to the
next `contract-update`. This is that task, and the transcription is owed here rather than left in a
note nobody re-reads.

**Blocker 1 was already answered.** `da05adf` had ruled the cutover onto the 86 a day earlier - both
clauses conjoined, the disposition's third option in full - and did not clear the marker, so the board
went on showing a question that was closed. Nothing new was decided.

**Blocker 2 was withdrawn as a defect, and this is the part later phases must read with its date.** The
four-bet continuation rows were read cell by cell, and Taylor read them by group instead. At
`t6/d100/HJ/LJ:raise@2.5,HJ:raise@7.5,LJ:raise@22.5`, hero adding 15 into 31.5 for 32.26 percent with
77.5 behind, combo and reach weighted: the whole arriving range continues 65.40 percent, the premiums
(AA to QQ, AKs, AKo) 96.15 at 39.1 percent of arriving weight, the suited connectors (JTs to 54s) 99.10
at 12.3 percent, the suited broadways 43.38 at 18.9 percent, and the middling pairs JJ to 22 **1.21** at
20.2 percent. Value continues, the bluffs continue, the middling pairs fold - which is what a polarised
three-bet range does facing a four-bet, and equity losing to playability is a standard solver result.
The reviewer's claim that "no preflop solution plays that" was withdrawn as unchecked, and so was the
convergence hypothesis beside it, which failed its own test: cells at 5 percent reach or better run
88.2, 85.3, 69.3, 67.1 and 83.7 percent pure by depth, so deep nodes mix **more** rather than showing
degradation.

**And the same ruling named this phase's eventual cause, three days before decision 16 found it.** One
number was left standing: whether 65.40 percent is the right total. Taylor ruled that the thing which
would move it is `realization: calibrated`, that a four-bet pot at 1.7 SPR is where that approximation
is weakest, and that this is a question about the model rather than about the derivation - filed
against **phase 16** as `CALIBRATED-REALISATION-PRICES-FOUR-BET-POTS-UNTESTED`, with phase 14 changing
nothing for it.

**How that sits with decisions 16, 19 and 20, which is why the date matters.** The 2026-08-27 reading
is that the four-bet rows are coherent polarised poker. The 2026-08-31 controlled experiment established
that the *class* term is causal for them - one field changed, JJ moving from folding 93.5 percent to a
37 percent continue - and decision 20 withholds those spots. Both hold: a polarised defence is the right
*shape* there, and which hands fill it is what the per-class table gets wrong at SPR 1.67. The
2026-08-27 ruling was made on the shape, before anyone had varied the model, and it is not evidence that
the cells decision 20 refuses are sound.




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
**Still superseded in its premise, 2026-08-31, and the retake moves with the build.** The 2026-08-30
supersession holds under decision 20 for the same reason and with more room: `t6/d100/SB/rfi` is the
only committed spot with an empty action sequence, so the lojack opening range is in neither the 51
nor the 36 and the 44-versus-33 pair this item ruled about is in no shipped cell.

Two things about the retake change. It is taken on the `calibrated` plus `add_allin: false` build
decision 20 ships, not on the `static` build that existed when the supersession was written. And it is
a **published** measurement rather than a gated one, per decision 10's re-ruling: per-cell dominance
is printed for a human and only the aggregate group form gates.
`SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` stays reopened and is retaken over the committed 36.


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
**Amended 2026-08-31: the ruling stands, its measurement is owed again, and this item now carries a
second finding about the same model.**

**The measurement.** The 51.61 percent above was taken on the `calibrated` plus `add_allin: false`
build, which is the build decision 20 ships, so it survives decision 19's round trip through `static`
intact. It is still not a measurement of the committed artifact, which does not exist yet, and the
contract requires this bias retaken over the committed 36 at stage 6 and written onto the source card
there rather than carried forward from here.

**The second finding: `calibrated` carries its own training rake.** Read at the pinned `4aee435`
rather than inferred. The fit was measured as net-of-rake EV over the **gross** pot, so the engine
uses the gross pot and skips the rake deduction at a heads-up flop terminal (`mod.rs:1124`, in the
comment block running 1118 to 1126), and the
source's own `AGENTS.md:49` states the consequence - the rake dial barely moves heads-up flop leaves
under it. So `rake_pct: 0.0` removes rake from the betting and leaves the fit's training rake in every
calibrated flop terminal with chips behind. The solve is **not rake-free where its modelled value is
priced**, and any claim that this cutover strikes rake off phase 08's list of explanations for the
calling gap is weaker than it was written. Filed as `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`;
it is stated on the source card rather than closed, and it binds what phase 17 may claim.

**This item's disposition is now the shape of three limitations rather than one.** The source card
states, each in poker terms with the measurement behind it: the position bias ruled here, the training
rake above, and that the committed three-bet spots weigh hero's four-bet on a terminal the fit has no
cell for (`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`). Accept-and-record was ruled once for
one defect and is now the form of three, which is a heavier load on one mechanism than it was ruled to
carry - the contract answers that by requiring a human to read the defence level and the four-bet
composition before the freeze, because a caveat does not reach the player at the table.

**One reframing, so this item is not read as a claim about hand strength.**
`REALIZATION-FIT-TABLE-IS-NON-MONOTONE-IN-HAND-STRENGTH` is a misnomer this phase carried for a day
and the halt inherited. `R` is realized EV over raw equity, not strength, so 76s at 1.1333 above JJ at
0.7493 is what realization means rather than an inversion - a suited connector collects more than its
raw equity because it flops well, a middling pair collects less because it cannot improve. The defect
is applying that table where there is almost no postflop play: the engine's `class_r` carries no SPR
term, so a ladder fitted at SPR 20 is applied undiminished at a four-bet pot's SPR 1.67, where - in
decision 20's wording, which is the accurate one - the flop is nearly all-in and the correct `R` is
close to 1. The module header states only that `R` is 1 at an all-in terminal and that those terminals
are exact; extending it to SPR 1.67 is a poker inference rather than the source's own statement. The
fit's `meta.r2` is **0.1885**, which no packet should quote a `calibrated` figure without.
**Corrected 2026-08-31 after independent review: the table's non-monotonicity splits in two, and only
one half is realization.** The reframing above is right where it is aimed. Measured over `class_base`:
22 0.9102, 33 0.8073, 44 0.7424, 55 0.7672, 66 0.8041, 77 0.7613, 88 0.7514, 99 and TT 0.7196, JJ
0.7493, QQ 0.8556, KK 1.0473, AA 1.2823. Aces and kings are made hands that collect, deuces through
fives are set-miners with implied odds, and nines through jacks are bluff-catchers that collect least.
That shape is poker, and the pair-versus-connector ordering is too.

**What no realization story covers.** Sixteen suited rows price a hand above the hand with the same top
card and a strictly better kicker - `J5s` 0.8105 over `J6s` 0.5880, `T5s` 0.7601 over `T6s` 0.5847,
`Q6s` 0.7899 over `Q7s` 0.7280, with gaps running to 22 points - and 33 at 0.8073 sits above both 44
and 55, which no set-mining argument orders. `A5s` over `A6s` is the one real case and the fitter says
why, "wheel aces unchained". The rest is a fit at `r2` 0.1885 patched to monotonicity only along a
hand-picked list of domination chains, which is `fit_phase_c5.py`'s own description of itself.

**That half reaches the committed cells, which is why it is not a curiosity.** Item 14 records the
chart playing `J6s` 0.000 beside `J5s` 1.000 and `Q7s` 0.000 beside `Q6s` 1.000, and item 10's failing
suited-row aggregate is plausibly the same noise in aggregate. A student handed a chart that folds
jack-six suited and calls jack-five suited learns a false ladder. The SPR argument does not remove this
half: it is noise in the fit rather than a table applied outside its pot type, so the reframing must
not be read as saying the table is sound everywhere.

**Two wording corrections that came with it.** "The module's own header says `R` should be near 1" is
an inference rather than a quotation - the header says `R = 1` when all-in and that those terminals are
exact, and decision 20's wording is the accurate form: at a four-bet pot's SPR 1.67 the flop is nearly
all-in and the correct `R` is close to 1. And this item's opening paragraph carries a stale corpus
figure, "the big blind holds 58 of the 89 human call disagreements", against a repo that now computes
42 and 14; restating those is phase 17's by its own contract, and it is flagged here so no reader takes
the first paragraph for a current measurement.



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
**Still holds, 2026-08-31.** Nothing in decisions 14, 19, 20 or 21 touches it. The blind structure is a
property of the solved game, which is unchanged at 0.5/1, six-handed, 100bb, and the
`ARTIFACT_SCHEMA_VERSION` bump this shares with decision 5 is still owed at stage 6. The contract
carries it as "either writes it or records why it waits, by id", so the two entries it closes -
`BLIND-STRUCTURE-VARIANTS` and `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` - stay assigned
to this phase.


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
**Amended 2026-08-31: the ruling stands and its counts are stale for the third time.** "35 of the 110
at full reach" is a property of a set two supersessions old, and the "11 of 86" that replaced it is one
old. No count is put in their place here: the reach distribution over the committed **36** is measured
at stage 6 and printed by the report, which is what the contract asks for rather than a number carried
forward from a discarded build.

**The prospective reason recorded on 2026-08-24 is unchanged and is now the whole of it.** The field
distinguishes little on a small, high-reach committed set, and adding it later is a second schema bump
and a re-derivation of everything built on the first. It also does one job this item did not foresee:
decision 10 publishes a per-cell dominance table for a human, and a reader cannot tell a real inversion
from two cells at five basis points of reach without the reach beside them. That is the same argument
the contract makes for the four-bet composition read, and it makes the field load-bearing on the
committed set rather than only on the multiway family that returns later.
**Transcribed 2026-08-31 from `stage-04-untrained-cell-refusal.md`, which says in terms that this item
owes it: "Decision 5 is `frozen-into-data` and covers the reach field only, so it owes an amendment at
the next `contract-update`. Until they land this note is the only place either is written down."** This
is that task.

**Ruled by Taylor, 2026-08-27: the chart commits the untrained cells and refuses only the classes that
never arrive**, and the reasoning is forward-looking rather than a judgment that those cells are sound -
heuristics for spots with no solver output are wanted eventually, and a spot with no output is precisely
where such a layer belongs, so blanking the cells now is not the route to it.

**One thing was put back to him and taken, because option one as stated defeats its own purpose, and it
adds a second field beside this item's.** A refused cell is visibly empty and a later heuristic layer
can find it; a committed cell that was never computed is indistinguishable from one that was, and
**reach cannot separate them**. At four of the eight never-reached spots it points the wrong way
outright - the big blind facing a 100bb open-jam carries all 169 classes at 10,000 basis points - and at
the other four it looks ordinary, 86 to 95 classes at a mean of 4,753 to 7,654. So **the converter
records each spot's arrival probability on the artifact**, in parts per billion, beside the per-cell
reach this item ruled.

**The two fields are orthogonal and the chart needs both.** Reach is per cell and says whether hero can
hold that class here. Arrival is per spot and says whether the line is one anybody plays. Integers,
because that is what makes the artifact checksum mean something per decision 8, and parts per billion
rather than basis points for a reason the field has to get right: 21 of the 86 spots sat at a nonzero
arrival below one basis point, the smallest at 2.5e-08, so in basis points all 21 would have rounded to
zero and become indistinguishable from the eight the solve genuinely never reaches. No threshold is
asserted anywhere - option one ruled that nothing is refused for arriving rarely - and the field exists
so a later phase can rule on it with the measurement in front of it. Frozen in
`tests/test_chart_arrival_probability.py` with the canary
`every-spot-claims-its-line-is-always-played`.

**What it looks like over the committed set is not yet known.** Every figure above is over the 86. The
eight never-reached spots, the 21 sub-basis-point spots and the five undertrained all-in nodes were
properties of that set, and decision 14's re-source and decision 20's withholding both move it. The
distribution is re-measured over the 36 at stage 6, along with the reach distribution this item's own
amendment already owes.



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
**Amended a fourth time, 2026-08-31, and this time the jam is gone from the committed set entirely.**
Decision 20 withholds the 15 four-bet-facing spots, and those are exactly the 15 spots that offer a
jam: five-betting is only legal facing a four-bet, and the 3.0 multiplier puts the fifth raise at
67.5bb where `allin_threshold` snaps it to the stack. Over the committed **36** the distinct raise
prices are exactly `[2.5, 7.5, 22.5]` and **`100.0` is not in hero's price menu anywhere**. This
item's ruled question - how an all-in offer becomes a schema action - therefore decides nothing about
what ships.

**The two-price schema is not merely unexercised, it is unexercisable.** 0 of the 36 offer two prices.
Twenty-one offer one raise price and carry a sizing entry, fifteen offer no raise at all and correctly
carry none, so the two-directional invariant still has both sets non-empty. The declared menus are 20
call/fold/raise, 15 call/fold and 1 fold/raise. A test asserting that a spot offering two prices is
described by two prices **passes vacuously**, and the contract requires it labelled as such: a check
that cannot fail must not be counted as one that passed.

**Every percentage this item has been ruled and restated on is a property of a tree or a set the phase
no longer ships** - 60.6 over the 5,626, 5.0 over the 110, and 18.6 combo-weighted or 13.7
reach-weighted over the 51. Over the committed 36 the answer is zero. They stay as written because
each was true of what it measured, and they must not be read as a trend, which the 2026-08-30
restatement already warns.

**What is retained, and why it is not the ruling doing the work.** The schema stays for the reason
given on 2026-08-30 and no other: it costs nothing, the multiway family that returns once GTOpen can
price it is where the case for it lived, and reverting a schema to fit a temporary dataset is the wrong
direction. Reverting to one price per spot remains Taylor's call and nothing here forecloses it. One
consequence to carry forward: the jam-inversion canary that rejected the first cutover is vacuous over
the committed artifact - no committed spot can jam - so it is retained against the **export** instead,
and the report prints AA's jam weight at the 15 withheld spots as excluded evidence.
**Corrected 2026-08-31 after independent review: hero never initiates the last raise, and the chart
still answers fifteen call-offs for a full stack.** The two sentences above - "`100.0` is not in hero's
price menu anywhere" and no committed spot offering a jam - are true of hero's own **raise** menu and
false as a description of what the chart tells a player to do. Fifteen of the committed 36 face a
five-bet jam on a call/fold menu, and at them the chart puts the last 77.5bb in. Round 14 of the
stage-01 note opened a blocker on this same sentence in the contract draft and the contract now reads
"Hero can never initiate the last raise, and the chart still answers 15 call-offs for a full stack".
This list must not be the document that keeps the version that was rejected.

**And the canary is stated over those fifteen rather than only over the export.** The defect it exists
to catch - a low pair or a weaker class committing a hundred blinds where aces do not - is fully
expressible over the committed 36 in the **calling** direction. Those fifteen spots are also the
cleanest cells in the chart: round 11 measured them at zero model-priced mass, every leaf a fold or an
all-in showdown, so an inversion there could not be blamed on the realization model and would be a
converter or solver defect. The check is therefore: at each of the fifteen, no lower pair and no weaker
class calls off more often than aces do. The export version is retained beside it, so the phase holds
one check that bites on the file the bot plays and one that bites on the source.
**Transcribed 2026-08-31 from `stage-04-test-recut.md`, which says in terms that this item owes it:
"decision 6 owes an amendment at the next `contract-update` transcribing it ... Until that lands this
note is the only place it is written down."** This is that task, and there are **two** rulings, both
Taylor's on 2026-08-26, neither of which has ever been in this list.

**Ruled 2026-08-26: a spot offering two prices seeds the price.** The runtime half of this item was
unruled and round 1 of the migration proceeded on a fail-closed default, which the independent
integration reviewer showed was refuted by the data rather than merely conservative: `t6/d100/SB/rfi` was
the only opening range the chart held and it offered two prices, so failing closed stopped the bot
opening a hand at all, from any seat. **The strategy chooses among a spot's prices with the same
deterministic seed it already uses to choose among a mixed cell's action weights.** No second mechanism
is introduced; `PreflopChartStrategy` has it. Rejected: failing closed, which stops the bot opening; and
taking the highest-weight price, which is the heuristic pick `lookup-tie-picks-an-action` forbids for
actions, has no answer at a tie, and would commit to the artifact a jam branch the bot never plays.

**Ruled 2026-08-26: the price weights are per hand class, not per spot.** The seeded-price ruling settled
*how* the strategy chooses; it did not settle what it chooses from, and this item's entry was one weight
per price per **spot**. At `t6/d100/BB/BTN:raise@2.5`, every class at full reach, the jam's share of
hero's aggressive volume runs AA 0.0000, KK 0.0025, TT 0.0480, JJ 0.6313, AKo 0.6641, 65s 0.8781, 44
0.8844 - against a spot aggregate of **0.0761**. A per-spot draw therefore jams 100bb with aces about
once in every thirteen three-bets, where the solve never jams them at all, and three-bets 44 to 7.5 more
than nine times in ten where the solve stacks off nearly nine times in ten. That is not a mispriced cell,
it is a different strategy, and it destroys legible poker: the solve three-bets small with the hands that
want action and jams the ones that do not want to play a three-bet pot out of position. It is also not
recoverable later, since `PREFLOP_ACTIONS` has no jam and the collapse leaves the per-class split
nowhere else in the artifact.

**Both rulings are unexercised over what decision 20 commits, and neither is reversed by that.** No
committed spot offers two prices, so the seed never has a second price to choose between and the
per-class price weight has one entry everywhere. They are transcribed because they are Taylor's, because
the multiway and four-bet families that return later are exactly where they bite, and because a ruling
that lives only in a stage-4 review note is one a later phase re-derives from scratch. They join this
item's own standing caveat: a check over the two-price case passes vacuously here and must be labelled.




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
**Moves to phase 17, 2026-08-31, per decision 21 - and it owes one thing before it goes.** The
old-versus-new comparison is a claim about poker made by comparing a file to 499 real hands, so it
travels with the rest of the corpus work. Phase 17's contract cites "the pin phase 14's decision 7
names". This item named no pin. It does now.

**The pin is `d046ac9`**, which is what the committed derived-chart report already reads the retired
chart from. The first draft of this block named `294a2b8` - `a386c77^`, the last commit on this branch
before the deletion - and the mechanical review of 2026-08-31 showed why that is the worse of two right
answers. The blob is byte-identical at both (`841ada2f`), but `d046ac9` is an ancestor of `main` today
while `294a2b8` is on this branch only and becomes one at the merge, and naming a second commit for the
same bytes is the confusion this item exists to prevent. One commit, named in one place, cited by both
phases.

**Phase 14 reads from the same pin, which this item has to say because two of the phase's own criteria
need it.** That 31 of the retired chart's 36 keys collide with nothing the new artifact declares while
5 collide exactly, and that it limps 13.73 percent from the small blind across 103 classes, are both
measurements over a file this phase deletes. Neither is a corpus claim, so neither moves; both are
recomputed from `d046ac9`.

**The default is otherwise unchanged and both rejections stand.** A copy under
`data/artifacts/preflop/` in a directory the importer's non-recursive glob misses is exactly the
arrangement that makes a reader ask which chart the bot plays, which is the confusion this phase exists
to end; a test fixture copy is a quarter of a megabyte of duplicated derived data under `tests/`.


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
**Extended a second time and proceeded on its default again, 2026-08-31, reported rather than blocked
because this item is `runtime-reversible`.** Decision 20 excludes nodes for a reason neither existing
code covers: the source prices them in a pot type its fit has no cell for. The vocabulary therefore
distinguishes **three** exclusion reasons rather than two - outside the selection rule, mispriced
multiway, and mispriced in a four-bet pot - because one code loses which nodes come back by which
route, and the routes genuinely differ. A solver fix at GTOpen's `KIND_POT_SHARE` terminals returns the
multiway kind; a fitted four-bet-pot cell, or phase 16's real postflop solver, returns the four-bet
kind.

**The census the codes have to produce**, from the ruled build: **36 committed, 15
`source-misprices-four-bet-pot`, 29,104 `source-misprices-multiway`, 4,814 `outside-selection-rule`,
summing to 33,969.** The inexpressible bucket is still empty - every node derives a valid v2 key - and
the report must publish that as a result rather than let a reader take the bucket for populated. Taylor
is told this proceeds on the default rather than asked to rule it.
**One sentence on why this stays `runtime-reversible`, added 2026-08-31 after independent review, since
item 10 reasons oppositely from the same premise.** Item 10 calls itself frozen because a stage-4 test
asserts it over the committed artifact and stage 5 freezes that test. A closed vocabulary is frozen the
same way, so the distinction is not the freeze: it is that **no exclusion code reaches the artifact**.
An excluded node is not in the chart, so the vocabulary lives in `lookup.py` and in a report that
re-derives in minutes, and changing it re-runs a generator rather than re-deriving committed data every
later phase is measured against. What has changed and is worth recording is that phase 17's contract now
requires each exclusion's cost reported separately, which makes the three-way partition load-bearing for
a later phase's measurement even though it is cheap to change here.



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
**Moves to phase 17, 2026-08-31, per decision 21, and the bands are void rather than inherited.** The
form of the ruling survives and travels: per opener, a quarter to one times that opener's defence
delta, written down before the numbers are seen. Phase 17's contract requires it re-registered in
phase 17's own decision list, against deltas recomputed from the chart phase 14 actually commits, and
before its measurement runs.

Every number in this item was fixed against deltas measured on the 38,828-node export. Carrying them
forward would let the closing measurement be graded against whichever set of bands happened to suit
it, which is the failure this item exists to prevent, so they are void. What must travel with the form
is this item's own reclassification: the pre-registration is `frozen-into-data` precisely because a
`runtime-reversible` pre-registration proceeds on a default set by the agent that will interpret the
result.


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
**Amended 2026-08-31: the tolerance stands as ruled, the gate is measured over the committed 36 before
it is frozen, and the build this phase ships is the one that fails it.**

**What is unchanged.** Adjacent ranks at one percentage point, the same tolerance for the
suited-against-offsuit relation, per-cell dominance measured and published for a human, and the
aggregate group form gated. Decision 2's ship-as-solved is what makes the per-cell result a
publication rather than a gate.

**What is stale.** Everything the tolerance was tuned against. It was chosen so that exactly one
violation survived - the lojack opening 44 at 72.81 percent beside 33 at 99.88 - and the lojack
opening range is in neither the 51 nor the committed 36.

**What the measurement now says, and it is the uncomfortable part.** Measured chart-wide over the
committed spot keys, combo-weighted by arriving reach and spot arrival, at this item's own one-point
tolerance: the `calibrated` chart **fails** - 4 pair inversions worst 7.40 points, 3 suited-row
inversions worst 23.19 - while the rejected `static` build passes at 0.06 and 0.00, and a chart edited
to fold nothing scores 0 and 0. Transposing every suited cell with its offsuit twin makes the row
ladder *cleaner*, and setting all 156 non-pair classes to a constant makes it perfect, because ties are
not violations and a flat line is the gate's optimum. So the gate rewards a transposed index rather
than catching one - which is what the 2026-08-24 correction found over the 5,626 and withdrew for want
of a measurement on the committed set - and the artifact decision 20 commits is worse by this gate than
the artifact decision 20 rejects.

**The caveat on those numbers, stated because no ruling may rest on an unlabelled proxy.** They were
taken on `superseded_chart_a386c77.json`, which is `calibrated` with `add_allin: true` - **the first
cutover** - read over the same spot keys as a proxy for the ruled build. **The artifact decision 20 ships
has not been derived**, so its group-gate result is not yet known.

**What this item therefore owes stages 4 and 6.** The gate's definition is pinned as data before
freezing - weighting, reach floor, tolerance, family exclusions, per spot or per chart - the prose
having produced seven counts (`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`). And the
paragraph in this item's 2026-08-30 supersession block licensing the tolerance to be re-derived from
the re-sourced chart is **withdrawn**: a
tolerance widened to 24 points to admit the artifact it judges is not a check, and the contract forbids
it in those terms. If the committed artifact fails the gate at stage 6, that is a **halt and a decision
for Taylor** - not an edit to the tolerance. The contract's regression-detector sentence governs how a
*pass* may be read, never as evidence the ranges are sound, and it is not a licence to publish a
failure.

**Corrected 2026-08-31 after independent review: the first draft of this block took a ruling that is
Taylor's, and that half is withdrawn to decision 22.** It wrote "the gate is written at the ruled
one-point tolerance and it **gates**", and *which relations* that tolerance gates was never ruled. What
Taylor ruled on 2026-08-24 is a per-cell relation - a suited hand played at least as often as the
offsuit hand of the same ranks - and then that the relations are measured per cell and gated on
aggregates. He did not rule that a ladder over **suited rows keyed by high card** is that relation's
aggregate form, and round 14 of the stage-01 note found in terms that it is not: "suited at least as
often as the offsuit twin has no gated form at all, the suited-row ladder is a different assertion".
The block carried the symptom - the aggregate scores a transposed index better than the right one - and
then had it gate anyway. What survives here is the tolerance, which is his and is not reopened, and the
pinning of the definition as data. Which relations it applies to is **decision 22**.

**One correction of fact that came with it.** The licence to re-derive the tolerance sits in this
item's 2026-08-30 supersession block, not in anything it carried on 2026-08-24; the 2026-08-24
correction says the opposite, that the phase halts rather than freeze a gate it has not seen pass. The
withdrawal stands and the first draft misnamed what it was withdrawing.
**Transcribed 2026-08-31 from `stage-04-test-recut.md`, and it answers the question this item's
2026-08-31 amendment was about to put to Taylor a second time.** The re-cut of this list filed a
decision 22 asking which dominance relations gate the committed artifact. They were ruled on
**2026-08-26**, the ruling shipped, and the decision list never recorded it - the list carries no
occurrence of that date at all. Decision 22 is withdrawn to here.

**Ruled by Taylor, 2026-08-26: the transposition discrimination is the gate, and no group ORDER is
gated at all.** The group aggregate this item's 2026-08-24 re-ruling proposed was measured over the 86
and **no partition passed**, so the contract's own instruction was to halt rather than freeze a gate
nobody had seen pass. The question went to Taylor with all five partitions and two candidate
substitutes. What gates is that **the measure prefers the solved hand index to the transposed one**:
over the committed set the group measure must flag strictly fewer spots under GTOpen's own class
ordering than under the grid ordering, on every partition. Measured at this item's ruled one-point
tolerance: 51 against 77, 17 against 77, 10 against 77, 1 against 77, and 41 against 70.

**Why that is the half of this item that survived measurement.** The 2026-08-24 re-ruling gave the
aggregate a job - "to keep a real check, a transposed hand index or a mis-assigned actor still failing
it, without asserting a per-cell order the solve does not owe". Over the 5,626 it failed at exactly
that, scoring the transposed mapping as the better one. Over the 86 it discriminates the right way on
every reading, and the ordering between the two mappings is what is asserted rather than a violation
count - because a count fixes a partition, and choosing the partition that reads smallest is picking a
number to go green. Rejected: gating the two-band pair aggregate with its one violation named, for that
reason; and gating nothing, which would leave a transposed index caught only by the reach-against-export
comparison.

**It shipped and it is frozen.** `validate_group_discrimination` in
`scripts/generate_derived_chart_report.py` refuses on `solved >= transposed`, a tie included, and
`test_the_group_dominance_measure_prefers_the_solved_hand_index_to_the_transposed_one` in
`tests/test_chart_cutover_evidence.py` asserts it over every partition. That test's own docstring states
the other half in terms: "Decision 10's literal group form does **not** hold over the 86 on any
partition, so this file does not gate on it."

**So the 2026-08-31 amendment above is wrong where it says the group order gates**, and that sentence is
withdrawn a second time - once to decision 22 and now to this ruling, which predates both. The
independent review that opened the question was right that the suited-row ladder was never ruled; it was
right for a stronger reason than it knew, which is that the ladder was ruled **out** as a gate five days
earlier and the list never said so.

**What is genuinely open, and it is a measurement rather than a ruling.** The 2026-08-26 discrimination
was measured over the **86**. The committed set is now **36**, and the one comparable figure available on
the committed keys runs the other way: round 14 of the stage-01 note reports that transposing every
suited cell with its offsuit twin makes the suited-row ladder *cleaner*, 2 inversions to 0. That is a
count of ladder inversions on one partition rather than the shipped gate's count of flagged spots over
all five, so it does not refute the ruling - it is a warning that the ruling's premise must be re-taken
before the freeze. **The discrimination is re-measured over the committed 36 at stage 4, and if it fails
on any partition that is a halt and a decision for Taylor**, on this item's own standing rule that the
phase does not freeze a gate it has not seen pass. `PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP`
carries the other half: the contract still states the superseded group-order form and owes the amendment.



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
**Moves to phase 17, 2026-08-31, per decision 21.** This item is already superseded by decision 15 -
the conclusion is read off the strict sampled-action rate, with the permissive rate and the cell-purity
statistic printed beside it - and the report that would state either is phase 17's. Phase 17's contract
carries the rule in its own criteria, so nothing is left here to apply. Kept rather than struck because
decision 15 and `AGREEMENT-RATE-NEEDS-A-DENOMINATOR-POLICY` both cite it, and because the reason it was
superseded is the thing worth carrying: a rate that a chart scores better on by being less converged is
not a rate a conclusion may be read off.


## 12. How the limped-decision-point count is defined

Reversibility: runtime-reversible

`CHART-CANNOT-ANSWER-A-LIMPED-POT` quotes the accepted cost of the limps ruling as twelve
inventory rows and 21 of 3,048 decision points, and no file states the rule that produced those.
Recounting under the obvious definition - the first recorded action in the spot key is a call -
gives 15 rows and 22 points.

Default: this phase publishes its own count under the stated definition and does not attempt to
reproduce 12 and 21. Filed as `LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION`, because the older
figure appears in three committed documents and correcting them is not this phase's scope.
**Moves to phase 17, 2026-08-31, per decision 21.** `CHART-CANNOT-ANSWER-A-LIMPED-POT` is one of the
four corpus-facing entries that move, and phase 17's contract owes the count with the definition it was
counted by. The default travels unchanged: the phase that publishes the count publishes its own
definition and does not attempt to reproduce the undefined 12 and 21.
`LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION` stays filed.

**What phase 14 keeps is the schema half, which is a different assertion.** No spot with an empty
`action_sequence` carries a call weight, enforced by the artifact schema rather than measured over one
file. That is a rule about what the artifact may hold; this item is a count of what the corpus contains.


## 13. Whether the sizing table stays one file

Reversibility: runtime-reversible

The sizing table is 1,974 bytes for 36 spots today and scales with whatever decision 1 selects.
Default: one file, matching the artifact, because it is small and because splitting it would need
its own composition rule where the chart library already has one for artifacts. Revisit only if
the selected spot count makes it large enough to matter, which at the measured rate it will not.
**Still holds, 2026-08-31, by a wider margin than when it was ruled.** The committed set is 36 spots
carrying 21 sizing entries, against the 36-spot, 1,974-byte table this item was ruled on, so the
"revisit only if the selected spot count makes it large" clause has nothing to trigger it. One file,
matching the artifact.


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
**Amended 2026-08-31: the ruling stands untouched and two of its findings now describe spots that are
not committed.** Decision 20 does not reopen this item. `add_allin: false` and the `0.00016` target
both stand, and decision 19's round trip through `static` returned to the config this item ruled, so
the build that ships is the one this item measured. What moves is which of its findings reach the
artifact.

The 15 spots that "still offer a 100bb jam" are exactly the 15 decision 20 withholds, so the surviving
five-bet jams are **excluded rather than committed**. The jam-composition finding recorded here - AA at
1.000 beside 87s at 0.995 at `SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` - sits in a withheld spot,
which is how decision 20 closes it: by refusing the cells, not by repairing them. The predicate's 51
becomes **36 committed**.

**The rank-dominance figures are unchanged as measurements and are not comparable as stated.** 54
against 52 is one implementation of a relation that a second implementation counts as 85 against 34
over the same keys. That is not a disagreement about the chart, it is
`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`, and it is why decision 10 pins the gate's
definition as data before anything is frozen.

**One thing this item said that is now settled elsewhere.** Its closing paragraph keeps the
no-low-pair-jams check as a regression canary and calls it too narrow to have caught the surviving
defects. Over the committed 36 it is not narrow, it is **vacuous** - no committed spot offers a jam -
so decision 6 retargets it at the export.


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
**Moves to phase 17, 2026-08-31, per decision 21.** Every rate this item governs is measured against
the corpus, and phase 17 owns the corpus. Its contract carries this item's default as a criterion in
its own words: the permissive rate is never reported alone, the strict sampled-action rate and the
cell-purity statistic are printed beside it, and a fall is what a converged chart looks like rather
than a regression. It adds one thing this item could not - every rate is measured on the chart phase 14
commits, with the artifact checksum stated, and none is carried forward.

**The purity figures quoted above do not describe the committed chart.** 2.209 nonzero actions per cell
at 21.0 percent pure, and 1.323 at 73.0, were both measured over the 51 spots the superseded and
re-sourced charts share, not over the committed 36.
`AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART` moves with this item.
**One thing corrected 2026-08-31 after independent review: cell purity does not move.** "2.209 nonzero
actions per cell at 21.0 percent pure" against "1.323 at 73.0" needs no hand history to compute. It is
read off the chart alone, and it is the single number that says whether the solve converged to answers
or to menus, so on decision 21's own seam it is a claim about the file and stays with phase 14. What
moves is its use as context for an agreement rate, which is phase 17's. Phase 14's contract carries no
purity criterion today; the report already prints per-cell dominance and arriving reach, and purity
belongs beside them. Recorded here as owed at the contract's next touch rather than added by this
stage, which may not write criteria.



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

Amendment, 2026-08-31: the cause named above is confirmed by controlled experiment, and the exit
condition stated here is superseded by item 17. The ruling to halt stands; what changes is the test
the lane restarts against. The fitter citation in this item is also wrong - the shipped table is
version 5 from `m5_spots/fit_phase_c5.py`, not v4 from `fit_phase_c.py` - and the corrected reading
is in round 3 of the stage-01 review note.
**The halt this item imposed was lifted by decision 20 on 2026-08-31, and the item stays exactly as
written.** Recorded here additively so that no reader takes "The chart is not committed" or "the bot
keeps playing the retired raked `six_max_nl25_100bb.json`" as current. Taylor ruled that the phase
reverts to `calibrated`, withholds the 15 four-bet-facing spots and commits the remaining **36**.

**The exit condition this item set was the wrong test twice over.** Item 17 superseded it once; the
second reason arrived on 2026-08-31 with the source's own documentation. "Postflop pricing monotone in
hand strength" asks a realization table to be ordered by strength, and `R` is realized EV over raw
equity rather than strength, so the ordering it demands is false poker. What replaced the test is not a
repair at all but a refusal: the spots priced outside the fit's support are excluded the way multiway
spots already are.

**What survives from this item unchanged.** Its diagnosis, and both of its rejections.
Ship-as-solved does not survive several separately-ruled findings being traced to one cause with a
measurement, and a chart whose own flag says do not study it is a training chart that cannot be used
for training. Decision 20 rejects neither of those conclusions: it accepts a **measured and bounded**
residual - 4.96 percent of the mass the model prices, 1.38 percent of total value, concentrated on the
premium classes at the three-bet spots - with an id and an exit rather than a caveat.


## 17. What the source has to satisfy before the phase re-sources

Reversibility: frozen-into-data

**SUPERSEDED by decision 19, 2026-08-31, the same day. Read 19 first; nothing below is work to do.**
This item asked how to repair GTOpen's realization model. That was never this phase's question. GTOpen
ships three realization models and the config selecting one lives in this repo, so the live question
is which model to solve with - decision 19 - and no solver work is owed by anybody. What survives from
this item is its diagnosis, which decision 19 rests on: the `calibrated` model's per-class numbers were
never measured in a four-bet pot, and that is why the chart folds JJ and calls 76s there.

Decision 16 halted the phase "until a source exists whose postflop pricing is monotone in hand
strength". That test does not work, and this item replaces it. The halt is not reopened.

**The defect.** GTOpen's preflop solver does not play flops. It prices each flop terminal
`pot x equity x R`, where `R` is how much of its equity a hand is assumed to keep. `R` is 169 numbers
in `cache/realization_fit.json`, and the engine applies them unchanged at every stack depth. In a
four-bet pot at SPR 1.67 only 1.67 bets remain, so there is almost nothing left to adjust for, yet JJ
is still priced at 0.749 of its equity and 76s at 1.133. The solve therefore folds JJ at 40.8 percent
equity into a 32.3 percent price while calling 76s at 29.6.

**Why the numbers are like that, established 2026-08-31 after Taylor asked how any of this reaches
postflop.** They are not guesses and they are not unordered by accident. `m5_spots/phase_b.py` is a
closed loop - "preflop lab solves -> HU flop exports -> realization runs" - in which
`solve-cli realization` (`solve_cli.rs:242`) **solves each flop exactly** and records what each class
actually collected, and `fit_phase_c5.py` fits those observations per pot-type cell. That is the
preflop/postflop fixed point, already built. But every study line it samples is an open, a call or a
three-bet: **there are zero `_4bet` lines, and there never have been.** So the absent four-bet-pot
cell is a sampling gap, not a modelling oversight, and the number applied at SPR 1.67 is a marginal
over pot types that excludes the pot it is being used in. v5 acquired its three-bet-pot axis by
exactly this route - its docstring requires "round-2 data (phase_b.py --round2: dense 3-bet-pot
lines)".

**Why decision 16's test does not work.** Read as a test on the 169 numbers it demands they be
ordered by hand strength, which is false poker - a suited connector really does keep more of its
equity than a middling pair when money is behind, and v5 left 88-22 free "for legitimate set-miner
premium" on purpose. Read as a test on the price it is satisfiable at low SPR but unsatisfiable if
quantified over every SPR. Two earlier drafts of this item proposed replacements that independent
review defeated; rounds 4 and 5 of the stage-01 review note carry them and neither is on the table.

**The evidence that the class term is causal.** One field changed, `realization` from `calibrated` to
`static`, same 38,828-node tree, `add_allin: true` and `allin_threshold: 0.67` held, both arms 400
iterations at BR gap 0.0046 against 0.0047. JJ goes from folding 93.5 percent to a 37 percent
continue, 76s from a pure call to 53; LJ's four-betting range loses 87s and 76s entirely, 18.6 percent
of it, in favour of A5s; continue-share falls 65.6 to 57.4 percent. Two limits: the intervention does
**not** move round 2's jam-composition blocker, and both arms hold `add_allin: true` while round 2's
blockers were measured on `false`.

**Options.**
`extend-the-fit-to-four-bet-pots` - add `_4bet` study lines to `phase_b.py`, run the realization
stage, and fit a v6 carrying a four-bet-pot cell. This is the pipeline's own documented extension
pattern rather than a one-off; it is simultaneously the repair and the played-flop measurement, since
the realization run solves the flops exactly; it yields a measured number where every alternative
yields an argued one; and it closes the preflop/postflop loop rather than patching around the break.
Cost is real and unmeasured: 100 flops in the subset and about 12 spots produced 59,786 three-bet-pot
rows, so a four-bet round is that scale of postflop solving on a CPU-only box.
`shrink-the-adjustment-in-short-pots` - make `R` fade toward 1 as SPR falls, `R = 1 + s(SPR)(R - 1)`,
one argument and one line at `mod.rs:344`. Cheap and directionally right, and at a threshold of 2.5 it
clears the inversion. But it substitutes an argument for the measurement the option above produces,
and the fit's own SPR coefficients point the other way. Rule it as a **stopgap** if the refit's cost
is unacceptable, or as a **constraint the refit must also satisfy**, since `R` must reach 1 as SPR
reaches 0 whatever the data says and a model violating its own boundary condition is wrong regardless.
`reorder-the-table` - force the 169 numbers into hand-strength order, decision 16 read literally. It
deletes a real measurement and a reviewer showed it does not even fix the pair-versus-connector case.
Listed to be ruled out rather than because it works.

**What is not being asked here.** Any threshold or band a stopgap needs is `runtime-reversible`: it
proceeds on a measured default and is reported. So is the arriving-reach floor any per-cell check
needs, without which the 77-through-22 block reads as a catastrophic inversion until you see it
arrives at reach 0.000 to 0.005. The repair lives in GTOpen, so whatever is ruled becomes a re-pin of
`/solver/commit` away from `4aee435bdeb155b25f0c8140e707a8342ce4356f` and owes its own item before an
export is committed; the blast radius of that re-pin is three constants in this phase's own
`tests/test_chart_cutover_evidence.py`, and no completed phase breaks. `SOLVE_TARGET_GAP_BB` at
`0.00016` and `add_allin: false` both stand; decision 14 is not reopened. And no option here accounts
for round 2's jam-composition blocker, which survives the intervention and still owes its own cause.

**Recommendation:** `extend-the-fit-to-four-bet-pots`, with the shrink's boundary condition - `R` to 1
as SPR to 0 - asserted against the refitted table rather than shipped as a patch.

**Ruled by Taylor, 2026-08-31: measure it.** The source is repaired by running GTOpen's existing
realization loop on four-bet pots and refitting, not by correcting the output of a loop that was never
run there. The shrink is not adopted as the repair; `R -> 1 as SPR -> 0` stays as a boundary condition
to assert against the refitted table, because a model that violates its own limit is wrong whatever
the new data says.

**What this ruling does not settle, stated so nothing reads as unblocked.** It does not lift the halt:
round 2's jam-composition blocker survives the static intervention and still owes its own cause, and
round 2's rank-dominance blocker is unaddressed by any option here. It does not fix multiway - the
committed set stays at 51 of 86 spots on
`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`. It does not authorise a re-pin: moving
`/solver/commit` off `4aee435bdeb155b25f0c8140e707a8342ce4356f` owes its own frozen item once a v6
exists. And it does not price the work - the four-bet round's cost is unmeasured, so the first task is
to scope it rather than to start solving.

Options: extend-the-fit-to-four-bet-pots | shrink-the-adjustment-in-short-pots | reorder-the-table
Answer: [extend-the-fit-to-four-bet-pots]
**Still superseded, 2026-08-31, and its ruled option is not work anybody owes.** The banner at the head
of this item says so; it is repeated at the foot because the item's own `Answer:` line reads
`extend-the-fit-to-four-bet-pots`, which a reader arriving from the bottom could take for scheduled
work. It is not. No work is owed in GTOpen by anybody, `~/projects/gtopen` is a read-only reference
clone pinned at `4aee435` with nothing in it modified, and decision 20 handles the four-bet pots by
refusing the spots that live in them rather than by repairing the model.

**What is still load-bearing is this item's diagnosis**, which decision 20 rests on: the fit has no
four-bet-pot cell because `phase_b.py` samples no `_4bet` study lines, so the number applied at SPR
1.67 is a marginal over pot types that excludes the pot it is being used in. The boundary condition it
established - `R` to 1 as SPR to 0 - is not asserted anywhere by this phase, because no refit happens
here; it is what a later phase or a fitted pot-type cell has to satisfy.


## 18. Where the solver fix lives, and what the source card pins

Reversibility: frozen-into-data

**Withdrawn 2026-08-31, the same day it was written, before any work rested on it.** This item forked
`MatthewPDingle/GTOpen` and cut a branch for the four-bet study lines. Taylor withdrew it: he does not
want work in GTOpen, the bot is what is being built here, and phase 14 was expected to need tweaks
rather than a solver project. The fork, its remote and its worktree are removed; `~/projects/gtopen`
is a reference clone at `4aee435` again and nothing in it was modified.

The coordinator's error is worth keeping, because it is the same one three times over. Decision 17
asked how to repair GTOpen's realization model. That was never phase 14's question. GTOpen ships
**three** realization models - `calibrated`, `static`, `raw` - and the config that selects one is
`RULED_CONFIG` in this repo, in this phase's own approved scope. The real question is which of the
three this phase solves with, or whether the affected spots are excluded by the selection rule the
phase already owns. Both are poker-bot decisions requiring no solver work at all.

Options: fork-and-pin-the-fork | pin-a-local-build | pin-an-upstream-merge
Answer: [withdrawn-see-decision-19]
**Still withdrawn, 2026-08-31.** Nothing in decisions 19, 20 or 21 revives it. The `/solver/commit` pin
stays at `4aee435bdeb155b25f0c8140e707a8342ce4356f`, GTOpen is unmodified, and moving that pin would
owe its own `frozen-into-data` item before any export built against it could be committed.


## 19. Which realization model the committed solve uses

Reversibility: frozen-into-data

Supersedes decisions 17 and 18. Both asked how to repair GTOpen's `calibrated` realization model - 17
by refitting it on four-bet-pot data, 18 by forking the solver to hold that work. Neither was this
phase's question, and Taylor withdrew both on 2026-08-31: the bot is what is being built here, no work
is wanted in GTOpen, and phase 14 was expected to need a tweak rather than a solver project.

**The question this phase actually faces.** GTOpen ships three realization models - `calibrated`,
`static` and `raw` - selected by one field of the config, and that config is `RULED_CONFIG` in
`src/poker_training_bot/solver_artifacts/gtopen_config.py`, inside this phase's approved scope. So the
choice is which model to solve with, on GTOpen unmodified at the pinned `4aee435`.

`calibrated` prices each flop terminal `pot x equity x R` with `R` from 169 per-class numbers fitted
only on single-raised and three-bet pots. Applied unchanged in a four-bet pot at SPR 1.67 it prices JJ
at 0.749 of its equity and 76s at 1.133, and the solve folds JJ at 40.8 percent equity into a 32.3
percent price while calling 76s at 29.6.
`static` keeps a positional term only - about plus or minus 8 percent, growing with SPR and saturating
at 8 - and carries no per-class term at all. Measured 2026-08-31 on the same 38,828-node tree with one
field changed and both arms at 400 iterations: JJ moves from folding 93.5 percent to a 37 percent
continue, 76s from a pure call to 53, LJ's four-betting range drops 87s and 76s entirely in favour of
A5s, and continue-share falls 65.6 to 57.4 percent.
`raw` sets `R` to 1 everywhere, discarding position as well.

**Ruled by Taylor, 2026-08-31: `static`.** It removes the defect that stopped the phase, needs no
change to GTOpen, and is one field in a config this phase already owns - the same shape as decision
14, which flipped `add_allin`.

**The cost, stated plainly rather than discovered later.** `static` is a blunter postflop model. It
does not know that a suited connector realizes its equity better than a middling pair in a deep pot,
which is real poker that `calibrated` was trying to capture and sometimes did. What is bought is that
it has no per-class term to get backwards at low SPR. Whether that trade holds across the committed
spots is measured at stage 6, not assumed here.

**Two things this does not settle.** Round 2's jam-composition and rank-dominance blockers are
re-measured against the new build rather than assumed fixed; the static arm still showed 87s and 76s
jamming while KK and QQ flat, so the jam blocker in particular should be expected to survive. And the
committed export was built with `add_allin: true` and `calibrated`, while the ruled config now carries
`add_allin: false` and `static` - **that combination has never been solved.** The 2026-08-31 experiment
deliberately held `add_allin: true` to isolate one variable, so the numbers above do not describe the
build this ruling produces. `SOLVE_TARGET_GAP_BB` stays at the ruled `0.00016`.

Options: calibrated | static | raw
Answer: [static]

**A third thing this does not settle, found 2026-08-31 by the lane executing the ruling and recorded
here additively rather than by editing the ruling above.** This item argues `static` from the four-bet
pots. `static` is also the model phase 10 rejected, and it rejected it on the single-raised pots this
item does not discuss. Phase 10's decision 2 ran the same tree with only this field changed and
recorded a big blind defending **99.71** percent against a small-blind open under the `static`
default, 97.44 against a button open and 72.94 against the lojack, against 49.03, 36.88 and 27.19
under `calibrated` and 42.88, 39.43 and 22.63 in the raked expectations file. It ruled that **nothing
may be committed under the default**, in those words, and called it the finding that would otherwise
have shipped a self-consistent, checksummed, thoroughly reported calling station. That measurement is
not cited here, and the figure sat in `gtopen_config.py`'s own docstring while this item was written.

Both readings can hold, and the mechanism says how: `static`'s positional term saturates at SPR 8 and
there is no per-class term, so at a four-bet pot's SPR 1.67 it has nothing to get backwards, while in
a single-raised pot it approaches raw realization, where calling 2.5 to reach an equity split is
almost always profitable. That would make `static` right where `calibrated` is broken and wrong where
`calibrated` was sound - and the second of those is the busiest part of the chart.

Two qualifiers, so this is read as a measurement owed rather than a result claimed. Phase 10's
`static` probe ran with `limp: true`, and the same table has the small blind limping 60.81 percent, so
that tree is not this one. And the contract's gated orderings cannot separate the two: 72.94 < 97.44 <
99.71 is monotone in exactly the way 27.19 < 36.88 < 49.03 is, so the ordering phase 10 said
"reproduces exactly" passes under a calling station too. The defence level per opener is therefore
measured on this build and read by a human before anything derived from it is committed. The contract
carries that as a criterion, and `STATIC-REALIZATION-UNMEASURED-IN-SINGLE-RAISED-POTS` carries the
diagnosis. If the level lands near phase 10's `static` column, this ruling needs re-taking against a
question it was not asked, and that is a new item for Taylor rather than a caveat for this one.
**Superseded by decision 20, 2026-08-31, the same day this was ruled.** The addendum above says that if
the single-raised defence level landed near phase 10's `static` column this ruling would need re-taking
against a question it was not asked, and that this would be a new item for Taylor. That is exactly what
happened, and decision 20 is the item.

**What the level was.** On the `static` build the big blind defends **76.31, 84.51, 91.46, 98.19 and
100.00** percent against the lojack, hijack, cutoff, button and small blind, folding **zero** combos
against a small-blind open, against phase 10's 72.94, 97.44 and 99.71 for the three openers it measured
and 22.63 to 42.88 in the raked expectations file. The damage is in the flat call: against the small
blind, call moves 22.59 to 81.49 while the three-bet *falls* 26.43 to 18.51. GTOpen's own author
recorded the same comparison - the big blind defends 50 percent with textbook composition under
`calibrated` "vs static's junk-loving 94%" - so three independent takes agree.

**Taylor ruled decision 20 back to `calibrated`**, withholding the 15 four-bet-facing spots instead.
`RULED_CONFIG["realization"]` reads `calibrated`. Nothing derived under `static` is committed; that
build survives only as evidence beside the stage-01 review note, in
`static-build-source-card.json` and `static-build-derived-chart-report.txt`.

**What this item established and decision 20 kept.** The option space is measured out rather than
argued: GTOpen ships three realization models, `calibrated` gets four-bet pots backwards, `static`
turns single-raised pots into a calling station, `raw` is `static` with the positional term removed as
well, and there is no fourth setting. That is what makes decision 20 a ruling rather than a
measurement. The mechanism this item's addendum proposed was confirmed and is why the two models fail
in complementary pot types: `static`'s positional term saturates at SPR 8 and it has no per-class term,
so it has nothing to get backwards at a four-bet pot's SPR 1.67 and approaches raw realization at a
single-raised pot's SPR 20, where calling 2.5 to reach an equity split is almost always profitable.
**Two corrections 2026-08-31 after independent review, both inside the amendment above rather than in
the ruling.**

**The SPR direction is backwards and the conclusion survives on a simpler reason.** GTOpen's `TODO.md:44`
gives the positional term as `R = 1 + 0.16 x pos_frac x min(SPR, 8) / 8` with `pos_frac` in
`[-0.5, +0.5]`, so the departure from raw realization **grows** with SPR and is at its maximum,
about eight percent, everywhere above SPR 8. `static` is therefore nearest raw at a four-bet pot's SPR
1.67 and furthest from it at a single-raised pot's SPR 20 - the opposite of what the amendment says,
and the opposite of this item's own body, which states it correctly. The reason `static` defends
everything is not SPR at all: it is **class-blind at every SPR**, so 72o gets the same realization
weight as a suited connector instead of `calibrated`'s 0.4326, and a big blind closing for 1.5 to win 4
then defends the whole deck. And "nothing to get backwards at SPR 1.67" is contradicted by decision
20's own measurement, where `static` five-bets AQs for the stack at 0.9998 while KK, QQ, AKs and AKo all
flat. Neither model produces a four-bet-facing range fit to show anyone; that is round 14's finding and
the honest form of the sentence.

**`raw` was bounded by argument rather than measured, and the sign of the argument is wrong.** "`raw` is
`static` with the positional term removed as well, so it cannot be better on that axis" does not follow.
Removing a positive positional term makes `raw` **tighter** than `static` for the seat that is in
position postflop, which is the big blind closing against an open - the exact seat the calling-station
failure lives in - and `raw` is the only one of the three that satisfies the module header's boundary at
SPR 1.67. It is very unlikely to be shippable, since realizing 100 percent of raw equity still defends
far too wide, but nobody solved it. The option was closed by argument and the packet says so. This is
not a reason to reopen decision 20.



## 20. Which pot type the committed chart prices correctly, now that no model prices both

Reversibility: frozen-into-data

Raised 2026-08-31 by the lane that executed decision 19, on the build that ruling produces, and
rewritten the same day after an independent review found the first draft argued for one of its own
options and stated it doing something it does not do. It does not reopen decision 19 by argument; it
reports what decision 19 turned out to do and asks the question the measurement leaves. Decisions 17
and 18 stay superseded and withdrawn, and no work is owed in GTOpen by anybody.

**What the build says.** `add_allin: false` with `static`, solved on an unmodified GTOpen at
`4aee435` to 0.00015672bb at iteration 1,100 of 2,000, byte-identical across two processes, 0 walk
mismatches, 51 spots from 33,969 nodes. Every figure below was measured by a worker lane, re-derived
by the coordinator and re-derived again by an independent reviewer, all three from their own code.

- **The defect decision 19 was ruled to fix is reduced, unevenly, and not by pricing the connectors.**
  At the deep four-bet lines JJ goes from continuing 0.028 to 0.462 and TT from 0.001 to 0.585, and no
  pair sits at 0.000 at any of the fifteen four-bet-facing spots. But over all fifteen, JJ improves at
  ten, holds at three and **falls at two** - `BB/HJ` 0.289 to 0.235 and `SB/HJ` 0.409 to 0.166 - and
  99 stays under 0.10 at **nine** of the fifteen. The connectors did not get repriced: 76s is absent
  from all fifteen and 87s and JTs survive at one, because they are no longer in hero's three-betting
  range. Where they do survive, `BB/SB`, **QJs continues 1.000 on 10,000bp and JTs 1.000 on 9,999bp**,
  so "no connector calls a four-bet at full reach" is false as a general claim.
- **The big blind now defends 76.31, 84.51, 91.46, 98.19 and 100.00 percent** against the lojack,
  hijack, cutoff, button and small blind, against 27.28 to 49.02 on the committed chart and 22.63 to
  42.88 in the raked expectations file. It folds **zero** combos against a small-blind open; 72o calls
  at 1.000. The damage is in the flat call, not the raise: against the small blind, call moves 22.59
  to 81.49 while the three-bet *falls* 26.43 to 18.51. Phase 10's decision 2 measured 72.94, 97.44 and
  99.71 for the three openers it took and ruled that nothing may be committed under this model.
- **Round 2's jam-composition blocker survives with new ranks.** 88 five-bets 0.508 at 9,277bp while
  KK and AKs flat 1.000 and AKo folds 0.937; 55 jams 0.358 at 5,677bp while QQ flats; 77 jams 0.967 at
  4,768bp while KK flats and JJ folds 0.765. Worse than any of those: at **three of the five lojack
  four-bet lines** - `BTN/LJ`, `CO/LJ`, `HJ/LJ` - **AQs five-bets for the whole 100bb stack at 0.9998,
  0.9992 and 0.9991 on 10,000, 9,998 and 9,775 basis points of arriving reach, while KK, QQ, AKs and
  AKo every one of them flat at 1.000** on comparable reach. AJs and ATs jam beside it but arrive at 2
  to 345 and 1 to 52 basis points, so those cells are noise and are not part of the finding. AQs is
  not: a hand dominated by two of the hands that decline the jam, taking it at full reach, is the
  44-jam defect that rejected the first cutover with the ranks changed.
- **The aggregate group dominance gate - the one check the contract actually gates the ranges on, and
  the one the phase halted rather than freeze unproven - passes on this build and fails on the
  committed one.** Combo-weighted by arriving reach and spot arrival, chart-wide: this build's pair
  ladder has 5 adjacent inversions with a largest gap of **0.43** points and its suited-row ladder 1 at
  **0.02**, all inside decision 10's ruled one-point tolerance. The committed chart over the same 51
  spots has 4 pair inversions up to **7.27** points (22 over 33) and 3 suited-row inversions up to
  **23.10** (5xs over 6xs), which fails it heavily. Strict per-cell dominance improves the same way,
  85 violations to 34 over the same 51 keys. This is the strongest evidence in favour of the build and
  it is recorded here for that reason. What it also shows is that these gates cannot see the defect
  above: a chart where the big blind defends every hand has a nearly flat pair ladder precisely
  *because* everything continues.
- **Priced by the artifact's own arrival mass**, `static` repairs 1.58 percent of the chart's traffic
  and breaks 57.11. The five single-raised big-blind spots are 57.11 percent, the opening range 25.11,
  the fifteen three-bet spots 16.00, the fifteen four-bet spots 1.58, the five-bet spots 0.20.

**Why this is a ruling and not a measurement.** GTOpen ships three realization models and all three
are measured or bounded. `calibrated` applies a per-class table with no four-bet-pot cell and gets
four-bet pots backwards. `static` drops the per-class term and turns single-raised pots into a calling
station - and the mechanism explains both halves at once, which is what makes it a real finding rather
than two coincidences: `static`'s positional term saturates at SPR 8 and there is no per-class term,
so at a four-bet pot's SPR 1.67 it has nothing to get backwards, while at a single-raised pot's SPR 20
it approaches raw realization, where calling 2.5 to reach an equity split is almost always profitable.
`raw` is `static` with the positional term removed too, so it cannot be better on that axis. There is
no fourth setting, and repairing the model is out of scope by Taylor's ruling of 2026-08-31. So the
phase cannot get a source that prices both pot types, and what is left is a choice.

**What the source's authors document, read at the pinned commit rather than inferred.** Nobody asked
GTOpen's author anything - `~/projects/gtopen` is a read-only clone with no licence and no contact -
but the repository states its own position clearly, and it answers most of what this phase spent three
weeks deriving.

- **`calibrated` is the shipped default and the only mode described as measured.** `AGENTS.md:48`:
  `"calibrated" (default, measured) / "static" (positional) / "raw"`. `README.md:226` has `static` and
  `raw` "remain as a dropdown for **sensitivity checks**". `static` is the pre-M5 heuristic that
  `calibrated` replaced, not an alternative production model: `TODO.md:44` gives it as
  `R = 1 + 0.16 x pos_frac x min(SPR,8)/8`, "Class-independent - 76s and Q2o get the same R", and adds
  "This makes the model too fond of offsuit junk and too cool on suited/connected playability hands."
- **The author ran this phase's own experiment and recorded the same result.** `TODO.md:17`, on
  shipping `calibrated`: "Validated on a raked HU game: SB becomes raise-or-fold (67%, no limps -
  modern HU theory), BB defends 50% vs 2.5x with textbook composition (**vs static's junk-loving
  94%**)." Measured here: 49.02 percent under `calibrated`, **100.00** under `static`. Phase 10
  measured 49.03 and 99.71. Three independent takes of the same comparison agree, so which model
  defends the big blind sanely is not an open question and decision 19 was ruled against it.
- **The author's caveat names this phase's defect before this phase found it.** `AGENTS.md:94`, in the
  caveats every study is told to carry: "calibrated realization is pessimistic on **no-initiative
  flatting** (call ranges are the soft numbers; folds and value-raises are robust)." Phase 14's entire
  four-bet defect is a no-initiative flat-or-fold by a medium pair facing a four-bet. It is a
  documented soft spot of the model, not a bug in it, and the author says which outputs to trust.
- **The gap is the author's own unfinished work, not an oversight.** `cache/realization_fit.json`
  `meta.note`: "v5 = v4 + pot-type axis: class x (role, pot-type) cells ... **unsupported 3BP mass
  folds back to SRP per class** ... **Requires round-2 data (3-bet pots + 4-max game)**", with
  `n_3bp_spots: 12`. `TODO.md:31` lists as remaining refinement "per-context tables once multi-context
  class coverage improves". There is no four-bet-pot cell and the engine collapses to one pot-type-blind
  169-vector regardless.
- **The repair rounds 3 to 5 proposed was tried upstream and rejected as unsound.** The fit carries SPR
  and initiative coefficients, and `mod.rs:1120` says they are "deliberately NOT applied: those are
  equilibrium correlates, and feeding them back causally lets the solver BUY the aggressor premium -
  validation showed 100% open rates". `TODO.md:27` is the postmortem. An SPR shrink of `class_r` is the
  same move.

**Reading `class_base` correctly, because this phase has been reading it as a strength table.**
`REALIZATION-FIT-TABLE-IS-NON-MONOTONE-IN-HAND-STRENGTH` is a misnomer and the halt inherited it. R is
realized EV over raw equity, not strength. Verified against the engine's own class index
(`equity.rs:35`): AA 1.28, KK 1.05, QQ 0.86, JJ 0.75, TT and 99 0.72, against 76s **1.13**, JTs 1.06,
87s 1.02 and 72o 0.43. That ordering is correct and is what realization means - a suited connector
collects more than its raw equity because it flops well, a middling pair collects less because it is a
bluff-catcher that cannot improve. **The table is not wrong. Applying it where there is no postflop
play is.** The module header states the boundary itself: "R = 1 when all-in, i.e. those terminals are
exact". At a four-bet pot's SPR 1.67 the flop is nearly all-in and the correct R is close to 1 for
every class, which is neither 0.75 nor 1.13 - and the engine path, `class_r` at `mod.rs:344`, is
`class_base[k] x pos_weight` with **no SPR term at all**, so a table measured at SPR 20 is applied
undiminished at 1.67. That single fact explains both models: `calibrated` is right where R matters and
wrong where it does not, `static` is wrong where R matters and roughly right where it does not, and
they fail in complementary pot types for one reason.

**Three ways this phase is outside the envelope the fit was validated in, all of which favour
narrowing what is committed rather than changing the model.**

1. *Pot type.* No four-bet-pot cell, per the fit's own note. This is the defect.
2. *Rake.* `AGENTS.md:49`: "Calibrated embeds its training rake - the rake dial barely moves HU flop
   leaves under it (documented limitation)." The engine comment at `mod.rs:1122` is concrete: the fit
   "was measured as net-of-rake EV over GROSS pot, so use the gross pot and **skip the rake
   deduction**". So a `rake_pct: 0.0` solve is **not rake-free at its heads-up flop terminals** under
   `calibrated`; those leaves carry the fit's training rake. The contract asserts the solve is
   rake-free and that this removes one of phase 08's three explanations for the calling gap. That claim
   is weaker than stated and is filed as `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`. It is not
   amended into the contract here because it is true of `calibrated` and false of `static`, so it waits
   on this ruling.
3. *Table size.* The shipped fit is v5.1, commit `ed6393b`, and its validation reads "12 gates pass;
   4-max validation holds (JJ 99.9, monotone ace gradient, **no pair inversions**)". The author's own
   gate asserts the absence of the defect this phase found. It was run on 4-max; phase 14 is six-handed,
   rake-free, at a pot type with no cell. We are outside it on three axes at once, which is a better
   description of what happened than "the table is wrong".

Also worth carrying into any packet: `meta.r2` is **0.1885**. The fit explains about a fifth of the
variance in observed realization. It is a real signal and a weak one, and nothing downstream should
read a `calibrated` chart as precise.

**The options, stated as what each would ship. This item does not recommend one.**

`revert-to-calibrated-and-refuse-the-four-bet-spots` - restore `realization: "calibrated"` and extend
the exclusion vocabulary so the fifteen four-bet-facing spots are excluded with a code rather than
committed, the way multiway pots already are. Commits the 98.4 percent of arrival mass that is not a
four-bet spot on the model phase 10 verified against an independent solver.
**What the source's own caveats say about this option, which is the strongest argument for it.** The
author's standing instruction is that under `calibrated` "call ranges are the soft numbers; folds and
value-raises are robust", and the defect is entirely a no-initiative flat-or-fold facing a four-bet.
Refusing those fifteen spots refuses precisely the decisions the model's author flags as soft. It is
also the only option that uses the table inside the pot types it was fitted on, since the fit's cells
are single-raised and three-bet pots.
**The limit of that argument, since the measurement below found it.** The author's robustness claim was
made about outputs inside the fitted envelope. It does not extend to a terminal the fit has no cell
for, and the premium hands' value four-bets at the *kept* three-bet spots are weighed entirely on such
terminals. So "folds and value-raises are robust" supports keeping the shallow spots' fold and
value-raise decisions where they are priced in support, and says nothing about the four-bet branch that
the measurement shows is 100 percent out of it.
**The contamination, measured 2026-08-31 rather than left unquantified.** A lane solved the config
this option ships - `calibrated` with `add_allin: false`, everything else as ruled - and walked all
33,969 action nodes, classifying every leaf below each committed spot by how it is priced. It reached
0.00015591bb at iteration 1,900 of 2,000, which is the figure decision 14 recorded for this build, so
it reproduces. Arrival-weighted over the 36 spots this option keeps:

| how the leaf is priced | share of value |
|---|---|
| fold-win: everyone folds, no flop, no model | **71.69%** |
| all-in showdown: R = 1, exact | 0.55% |
| heads-up flop terminal, single-raised or three-bet pot: model, inside the fitted region | 26.39% |
| heads-up flop terminal, four-bet pot: model, **outside** the fitted region | **1.38%** |

So of the mass the realization model prices at all, **4.96 percent** is priced outside the pot types
the fit covers, and as a share of the committed chart's whole value it is **1.38 percent**. The
coordinator re-derived both from the per-spot splits independently of the lane's aggregation.

In aggregate the exposure is **smallest where the traffic is**: the five big-blind-versus-open spots,
56 percent of committed arrival, run 1.45 to 3.65 percent, and `t6/d100/SB/rfi` at 22.6 percent of
arrival runs 3.65; the worst kept spots are three-bet spots at 8.17 to **14.62** percent
(`LJ/LJ:raise@2.5,HJ:raise@7.5`), each carrying under 1.5 percent of arrival. The fifteen
five-bet-jam-facing spots this option also keeps have **zero** model-priced mass - every leaf is a fold
or an all-in showdown - so they are priced exactly. There is no five-bet-pot flop terminal anywhere,
because the 3.0 multiplier puts the fifth raise at 67.5bb and `allin_threshold` snaps it, so the
out-of-support region is exactly the four-bet pots at SPR 1.667.

**And 4.96 percent is the wrong statistic to rule on: read per hand class, the same measurement argues
against this option.** At **all fifteen** three-bet-facing kept spots, AA, KK and AKs sit at **100
percent** contamination, and QQ at 100 percent in twelve of them. The only way those hands reach a flop
with chips behind from those spots is by four-betting, and four-bet-versus-call with the top of the
range is the one decision those spots exist to answer - so the branch that decision is weighed on is
priced entirely out of support. Over the 1,134 cells at 5,000bp of reach or better in the kept spots,
100 sit at 90 percent contamination or above. The busiest spots are not clean either: `t6/d100/SB/rfi`,
28.19 percent of arrival, puts **21.8** percent of AA, KK, QQ, AKs and JJ's flop mass in a four-bet
pot, and `t6/d100/BB/SB:raise@2.5` puts **41.5** percent of 76s's there. The low spot aggregates come
from the offsuit trash that folds, not from the classes the chart is consulted about. Both statements
are true - small and concentrated in low-traffic three-bet spots by mass, landing on the premium
holdings at the busiest spots by class - and the second is the one a ruling has to price. The lane that
took the measurement was asked for its own verdict on it and gave **not shippable on this measurement**.

**What would settle it, and why it is not available.** Mass bounds the exposure without measuring the
error. The decisive test is an EV comparison: reprice only the four-bet-pot terminals defensibly -
`R = 1` below SPR 2, which is what the engine already does at an all-in terminal and what the module
header calls exact - and see whether the kept cells move by more than the solve's own noise, one basis
point of quantisation against a 0.000156bb gap. **No config reaches that.** `realization` is tree-wide,
so `static` reprices the single-raised terminals too and confounds the shallow spots; `max_raises: 3`
removes the four-bet terminals but also removes four-betting as an option, changing the strategy space
rather than the pricing. Repricing one pot type means editing GTOpen, which is out of scope by the
ruling of 2026-08-31. So this may be a question the phase cannot answer from inside its own
constraints, which is an input to this ruling rather than a reason to prefer the flattering reading.

Two supporting facts, so "out of support" is exact rather than inferred: the fit's own `meta.rho_cells`
carries cells for `f_srp`, `i_srp`, `f_3bp`, `i_3bp` and `limp` and nothing else, and its SPR buckets
start at an edge of 2.5, so a four-bet pot at SPR 1.667 sits below the lowest bucket the fit was
estimated on - while `class_r` applies the full 0.363-to-1.282 ladder there with no SPR or pot-type
term, where it ought to compress toward 1.

**What this does not do, stated because the first draft of this item claimed otherwise.** Refusing a
spot removes it from *lookup*, not from the *solve*. Every committed three-bet spot and every committed
single-raised spot is backward-induced over four-bet-pot terminals, so it carries whatever the model
gets wrong down there whether or not the four-bet node itself is committed. That is this phase's own
ruled principle - the contract says the approximation bites at *terminals* and a node's strategy is
backward-induced over every terminal below it, citing
`SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS` - and it is the half of the multiway
precedent this option would be borrowing without. Stated over terminals, "exclude what the source
misprices" excludes every node with a four-bet pot below it, which is the whole chart. So the question
is not whether the kept spots inherit the misprice - they do - but how much, and the table above is
that measurement: **4.96 percent of the mass the model prices, 1.38 percent of total value.** Note it
is a different quantity from the 1.58 percent of *arrival* mass the four-bet spots carry, which is
what the first draft of this item wrongly leaned on.

`keep-static-as-solved` - commit the build measured above, with the defence level stated on the source
card as an accepted limitation. What ships is a chart that flat-calls a button open with every hand
dealt, and it ships to a bot whose postflop is phase 06's heuristic fallback, so the equity those
calls realize is below even what the model assumed. Phase 10's decision 2 ruled against this model on
the same figures. In its favour: it is the only option under which the aggregate dominance gate has
been seen to pass, and the four-bet ranges are better poker than the committed chart's.

`keep-static-and-refuse-the-single-raised-spots` - the mirror of the first option. Refuses 57 percent
of the chart's traffic and, on the same reasoning about terminals, the opening range with it, leaving
the bot answering the rare spots and refusing the common ones. Carries the same unmeasured
contamination in the other direction, since a three-bet pot's terminals include single-raised-pot
turns of play only through folds - it is stated for completeness rather than as a near thing.

`halt-until-a-source-prices-both` - what decision 16 did. The derivation machinery is proven and
re-runs in about seven minutes, so a corrected source costs only the solve. **What it costs is not
"only time".** Decision 20's own preamble forecloses every route to a corrected source - 17
superseded, 18 withdrawn, no work owed in GTOpen, no vendor change - so as written this is an
indefinite halt with no owner and no path, and it leaves live the retired raked GTO Wizard chart the
contract requires **deleted**, which phases 15 onward are then measured against. That is a real
option; it is not a cheap one.

**Two options deliberately excluded, named so the list is not read as the whole space.** Committing
all 51 under `calibrated` with the four-bet misprice recorded as a caveat is forbidden by the
contract's own non-goal - a caveat does not reach the human at the table - and it is the state the
phase was in before decision 19, which two independent reviews rejected. And re-solving with
`max_raises` reduced so the tree holds no four-bet pot at all is the only route that removes the
contamination rather than refusing around it, but it changes the solved tree, which the non-goals
freeze, and it buys that by abstracting away a line real opponents take. Either could be ruled in;
neither is offered as an option here without Taylor saying so.

Options: revert-to-calibrated-and-refuse-the-four-bet-spots | keep-static-as-solved | keep-static-and-refuse-the-single-raised-spots | halt-until-a-source-prices-both
Answer: [revert-to-calibrated-and-refuse-the-four-bet-spots]

**Ruled by Taylor, 2026-08-31: revert to `calibrated` and refuse the four-bet-facing spots.** The
residual is accepted rather than dismissed - his words were "can figure out later" - so what "later"
means is written down here rather than left as a feeling. It is the three-bet spots' contamination:
16.00 percent of committed arrival, at which AA, KK and AKs weigh four-bet-versus-call on terminals the
fit has no cell for. It is not measurable from inside this phase's constraints, because separating it
needs one pot type repriced and no config reaches that. Two things resolve it and neither is phase 14's:
an EV comparison that would require editing GTOpen, which stays out of scope; or **phase 16**, whose
postflop solver plays flops exactly and carries no realization model, at which point every cell in this
chart is re-derivable against a source that does not have the defect. Filed as
`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` so the acceptance has an id and an exit rather than
living in a decision item nobody re-reads.

Rejected, and why, so the ruling is not re-litigated. `keep-static-as-solved`: the big blind defends
100.00 percent against a small-blind open and folds zero combos, which phase 10's decision 2 already
ruled uncommittable on the same measurement.  `keep-static-and-refuse-the-single-raised-spots`: refuses
82 percent of the chart's traffic to keep the rare spots.  `halt-until-a-source-prices-both`: a
defensible choice and the one this ruling trades against - it was declined because a provisional chart
that is right in the common spots beats another cycle on the retired raked GTO Wizard chart, and
because phase 16 will re-source this anyway.

A fifth cut was priced and offered before the ruling and not taken: refusing the three-bet spots as
well, which keeps 82.4 percent of arrival and drops every cell that is 100 percent out of support, at
the cost of the bot refusing every three-bet spot. Recorded because the contamination is a gradient
rather than a cliff at the four-bet boundary, and a later phase reopening this should know the option
existed and was declined rather than missed.
**Still current, 2026-08-31.** This item and item 21 are the two rulings the rest of this list has been
re-cut against, and nothing supersedes either. Two consequences are carried into the items above rather
than repeated here: the committed count of 36 lands in items 1, 6, 8, 10 and 14, and the accepted
residual `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` lands in item 3 beside the two other
limitations the source card states.


## 21. Whether this phase is one phase

Reversibility: frozen-into-data

Raised and answered 2026-08-31. It is a structural question rather than a poker one, and it is here
because it was forced by this phase's own contract failing to fit the cap the repo puts on a contract.

**What forced it.** With decision 20's criteria written in - a third exclusion reason and its census,
the disappearance of every jam from the committed set, the training-rake qualification, the unfitted-
terminal caveat - plus the two criteria the stage-01 reviews asked for and the corrections they found,
the contract measured **305 lines against a 300 cap**. That was after the Scope narrative was cut to
orientation, every stated level measured on a build the phase discarded was replaced by its criterion
and the stage it is taken at, bullets were merged and the document reflowed: 323 to 305, while the
content that had to be added kept pace. `AGENTS.md` forbids raising the cap and prescribes a rewrite
folding amendments into the criteria they amend. That rewrite was done. It still did not fit, which is
the point at which the size stops being an editing problem and becomes a scope one.

**Ruled by Taylor, 2026-08-31: split it.** Phase 14 derives and commits the artifact and checks the
ranges it holds. **Phase 17** measures that artifact against the public corpus and says what the result
does and does not establish about v1's calling gap. The seam is the one the content already had: one is
a claim about a file, the other is a claim about poker made by comparing that file to 499 real hands,
and they have different failure modes, different evidence and different readers. Phase 14 lands at 284
lines with everything the reviews asked for and phase 17 at 158.

**What moves.** The closing-measurement criteria in full; the corpus half of the report and its
old-versus-new disagreement validator; the four corpus-facing backlog entries
(`CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`, `AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`,
`CHART-CANNOT-ANSWER-A-LIMPED-POT`, `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK`); and the
pre-registration decision 9 owes, which is re-taken in phase 17's own decision list against the chart
phase 14 actually commits rather than inherited from bands fixed on discarded builds.

**What does not move, and this is the part to get right.** Phase 14 keeps every check on the ranges
themselves - the two dominance relations, the two orderings, the defence level read by a human, the
no-limp rule, the arriving-reach field - because those judge the artifact rather than the corpus. It
also keeps the four-bet-composition read the stage-01 poker review asked for, which is a range check.
A phase that commits ranges and defers every judgement about them to a later phase would be the
failure this split is meant to avoid.

**One risk, stated because splitting is not free.** Phase 14 can now reach a green gate without any
corpus evidence that its ranges resemble how people play, and the closing measurement is what caught
v1's calling gap in the first place. Phase 17 is `auto_advance: false` and depends on 14, so the
verdict is owed before the roadmap moves past it; what it cannot do is block phase 14's own tag. That
is the trade the split makes and it is the reason `CHART-COVERAGE-EXPANSION` and the corpus entries
stay open rather than closing with phase 14.

Options: keep-one-phase-and-drop-criteria | split-into-two-phases | change-what-the-cap-covers
Answer: [split-into-two-phases]
**Still current, 2026-08-31, and executed.** Phase 17, "The Corpus Verdict On The Committed Chart", is
declared `future` in `phase_status.yml` at `docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md`, 158
lines, `depends_on: ["14"]`, with `auto_advance: false` in `verification/loop_policy.yml`. Phase 14's
contract is at 284 lines against the 300 cap.

**The five items this list moves there are 7, 9, 11, 12 and 15**, and each is marked at the foot of its
own item rather than only here. Decision 9's bands are void rather than inherited: phase 17 re-registers
them against the chart phase 14 commits, before its measurement runs. Decision 7's pin is named here
first, because phase 17's contract cites it and phase 14 is the phase that deletes the file.

**What did not move, checked item by item rather than assumed.** Every item that judges the artifact
stays: 1 and 20 select it, 2, 5, 6, 10, 13 and 14 shape what it holds, 3, 4, 8, 16, 17, 18 and 19 record
what its source does and what was ruled about it. That is the seam decision 21 names - a claim about a
file against a claim about poker made by comparing that file to 499 real hands - and this re-cut is the
first time it has been applied to this list.

## 22. Which dominance relations gate the committed artifact (withdrawn: ruled 2026-08-26)

Reversibility: frozen-into-data

Raised 2026-08-31 by the independent poker review of this list's re-cut, which found that item 10's
2026-08-31 amendment settled by prose a question nobody has ruled. The tolerance is not in question and
is not reopened: one percentage point, adjacent ranks, is Taylor's from 2026-08-24, and item 10's
withdrawal of the licence to re-derive it stands. What is in question is **which relations that
tolerance is applied to**, as a gate.

**What was actually ruled, and what was assumed.** On 2026-08-24 Taylor ruled two per-cell relations - a
higher pair played at least as often as the pair one rank below, and a suited hand at least as often as
the offsuit hand of the same two ranks - and then re-ruled that they are measured per cell and **gated
on aggregates**, because among near-indifferent hands the solver's split is its considered answer and a
per-cell gate rejects correct play. He did not rule what the aggregate form of the second relation is.
The phase has been using a ladder over **suited rows keyed by high card** - the combo-weighted play
frequency of each suited row at least that of the row below. Round 14 of the stage-01 review note found
in terms that this is not that relation's aggregate form: "suited at least as often as the offsuit twin
has no gated form at all, the suited-row ladder is a different assertion."

**Why that matters rather than being a naming quarrel.** The suited-row ladder has now been measured
twice as scoring the **wrong** index mapping better than the right one. Over the retired 5,626 it
flagged 2,007 nodes as solved against 818 with suited and offsuit transposed. Over the committed spot
keys, transposing every suited cell with its offsuit twin makes the ladder *cleaner*, 2 inversions to 0,
and setting all 156 non-pair classes to a constant makes it perfect, because ties are not violations and
a flat line is its optimum. A gate that rewards a transposed hand index does not catch one. The pair-band
ladder is the only aggregate form ever seen clean, and only over the full-reach nodes.

**And it decides the phase's outcome.** Measured chart-wide at the ruled one-point tolerance, the
`calibrated` chart fails - 4 pair inversions worst 7.40 points, 3 suited-row inversions worst 23.19 -
while the `static` build Taylor rejected passes at 0.06 and 0.00, and a chart edited to fold nothing
scores 0 and 0. So under the reading item 10's amendment wrote, the artifact ruled in fails the gate by
23 points and the artifact ruled out passes it. This is `frozen-into-data` in the strict sense: a stage-4
test asserts it, stage 5 freezes it, and item 10's own words are that changing it afterwards is a task
rather than an edit.

**The options, stated as what each ships. This item does not recommend one.**

`gate-both-ladders-at-one-point` - the pair-band ladder and the suited-row ladder both gate. On the
evidence available the phase then halts at stage 6 on a 23-point miss, and the check that halts it is
one whose optimum is a chart that folds nothing and which prefers a transposed index.

`gate-the-pair-band-ladder-only-and-publish-the-suited-row` - gate the only aggregate form ever measured
clean, and demote the anti-diagnostic one to a printed number beside the per-cell dominance table
decision 10 already publishes. Keeps a real regression detector for a mis-assigned actor or a broken
converter; gives up any gated statement about suited against offsuit, which is the relation phase 10's
export was checked on.

`gate-neither-and-publish-both` - the range check becomes entirely a human read, consistent with decision
2's ship-as-solved and with the defence-level and four-bet-composition reads the contract already buys
before the freeze. Costs the phase every automated check on the ranges; leaves `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` with nothing at all beside it.

`gate-both-and-halt-if-it-fails` - what item 10's amendment wrote, ruled explicitly instead of assumed,
so the halt is a choice rather than one the packet made for him. Distinct from the first option only in
that it is taken knowingly.

**Sequencing, because it decides when this is best answered rather than what the answer is.** Every
figure above is taken on `superseded_chart_a386c77.json`, which is `calibrated` with `add_allin: true`,
read over the same spot keys as a proxy. **The artifact decision 20 ships has not been derived.** The
build machinery is proven and re-runs in about seven minutes. So one reply available here is "derive it
and measure the gate on the real file first, then rule" - which would put a stage-6 build ahead of
stage 4's test authoring, out of the loop's order, and is named so it can be chosen rather than
discovered. Item 10's own rule that no ruling may rest on an unlabelled proxy applies to this ruling
too.

Options: gate-both-ladders-at-one-point | gate-the-pair-band-ladder-only-and-publish-the-suited-row |
gate-neither-and-publish-both | gate-both-and-halt-if-it-fails
Answer: [withdrawn-already-ruled-2026-08-26-see-decision-10]

**WITHDRAWN 2026-08-31, hours after it was filed, because the question was already ruled.** Taylor
ruled it on **2026-08-26** and the ruling shipped; this decision list never recorded it, and a search
of the record was what found that. The transcription is at the foot of decision 10 and it is the
authority - read it rather than this item.

**What he ruled, in one sentence.** No group **order** is gated at all. What gates is that the group
measure **prefers the solved hand index to the transposed one**: over the committed set it must flag
strictly fewer spots under GTOpen's own class ordering than under the grid ordering, on every
partition. That is a fifth answer, and none of this item's four options names it.

**Why this item was written anyway, recorded because the failure is worth keeping.** The re-cut of
this list on 2026-08-31 asserted that the group order gates. An independent poker review caught that
the suited-row ladder underneath it was never ruled and asked for a decision item, correctly on what
it could see. Neither the re-cut nor the review knew the ladder had been ruled **out** as a gate five
days earlier, because the ruling lived only in `stage-04-test-recut.md`: implementation mode may not
edit a decision record, so a stage-4 ruling is written into a review note with a pointer to the next
`contract-update`, and this list had four such pointers outstanding. So a question that was settled,
implemented and frozen was hours from going back to Taylor with an option set that omitted his own
answer. `RULINGS-TAKEN-IN-IMPLEMENTATION-MODE-LIVE-ONLY-IN-A-REVIEW-NOTE` carries the general form.

**What is genuinely open is a measurement, not a ruling, which is why nothing here blocks stage 3.**
The 2026-08-26 discrimination was measured over the **86**. The committed set is **36**. Decision 10's
transcription states the retake and where it halts: stage 4 re-measures the discrimination over the
36, and a failure on any partition is a halt and a decision for Taylor rather than an edit to the
measure. Decision 10's one-point tolerance is not reopened by anything here.
