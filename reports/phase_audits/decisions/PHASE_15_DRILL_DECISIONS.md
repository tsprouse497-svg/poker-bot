# Phase 15 judgment calls

These are the choices that decide what the drill deals a student, what it tells them when they
answer, and what it records. No test in this repo settles them. A drill that deals the wrong spots
passes exactly as green as one that deals the right ones, and a score that means nothing looks
exactly like a score that means something.

`verification/loop_policy.yml` gives this phase `auto_advance: false` for that reason: "What a drill
asks and how it scores an answer is a product judgement no test settles."

Every item carries a reversibility class, which the loop driver reads at stage 3 to decide whether it
must stop for a human.

- `runtime-reversible`: the choice only changes behaviour at run time, so a later edit changes it.
  The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact **or fixture** that every later
  measurement then runs against. The loop halts until a human answers.

**Five items are `frozen-into-data`: 1, 2, 3, 6 and 7.** Each is written into the committed session
fixture, the committed decision audit, the committed exclusion table, or the shape of the report they
are measured by, so reversing one is a task with `tests/` reopened rather than an edit. The other five
proceed on their recorded defaults and are reported afterwards.

Two of those classes were wrong in the first draft and an independent reviewer moved them. **7 was
filed reversible** on the reasoning that deriving a refusal code is a derivation rather than a
judgement. The class is about what gets written, not how much judgement went into it, and 7's own
default commits a table every later refusal is looked up against. **9 was filed frozen** on the
reasoning that cutting a promised feature is a call a human should make. Deferring writes nothing -
no artifact, no fixture, no test stage 5 freezes - and stopping the loop could not change the outcome,
because `AGENTS.md` forbids the lift whatever is answered here. The real ask underneath 9, the size
bound as a number, is raised as a `- Paused:` line in the active ExecPlan, which
`scripts/review_queue.py` already reads, rather than by borrowing a class that does not describe it.

## What was measured first

Everything below is recomputed from `data/artifacts/preflop/six_max_100bb_rakefree.json` at `9bbdcf4`
and from the committed reports beside it, not quoted from prose. Three of these numbers change the
answer to a decision on their own.

**There is no EV anywhere in the chart.** A cell is a weight per action summing to one.
`arriving_reach_bp` is how often hero holds that class there; `arrival_ppb` is how often the spot is
reached at all. Neither is a value. The upstream export carries frequencies too: the only `evs` in
the repo is `solve_status.evs`, six whole-game numbers, one per seat. The all-in equity matrix prices
all-in equity and the committed tree offers no shove (`add_allin: false`).

**The committed set is three families of wildly different size and frequency.**

| family | spots | share of arrival |
| --- | --- | --- |
| first-in | 5 | 52.6637% |
| facing an open | 25 | 39.0915% |
| facing a three-bet | 219 | 8.2448% |

**Hand-class coverage inside a spot is the real hole, and nothing published says so.** 83 spots carry
all 169 classes - the ones where hero has not yet acted. The other 166 carry only hero's own arriving
range: 43 spots hold five classes or fewer and 18 hold exactly one. Combo-weighted over the 1,326
deals:

| sampling | share of deals the chart can answer | refusal rate |
| --- | --- | --- |
| uniform over the 249 spots | 40.89% | **59.11%** |
| weighted by `arrival_ppb` | 97.49% | **2.51%** |

That is a factor of twenty-four between two policies either of which a reasonable implementer would
have picked, and it is decision 2.

**44 spots have an arrival of zero parts per billion**, all 44 facing a three-bet, and **42 of them
are also among the 106 the bot cannot reach** - so decisions 2 and 3 rule on an overlapping set and
decision 2's exclusion wins where they meet.

**A quarter of the chart cannot express a call, and it is the quarter the student sees most.** 4,225
of the 18,431 cells carry only `{fold, raise}`: 25 spots, being all 5 first-in and the 20
non-big-blind spots facing an open, where phase 14 decision 45 merged the solve's flat into the
raise. Weighted by arrival they are **80.2010 percent** of what the drill will deal. Only the 5
big-blind spots facing an open price a call at all. This is decision 10, and an independent reviewer
found it after the first draft of this file had already been written without it.

**Mixing is real but lopsided, and the threshold moves the answer.** Of 18,431 cells, 15,836 (85.92
percent) price exactly one action. At a 0.999 pure threshold 1,820 cells are mixed (9.87 percent); at
the report's own 0.99 threshold - the one this phase pins in decision 4 - it is 1,202 (6.52 percent),
of which the report counts only the 675 below 0.90 as mixed and leaves 527 in a band it does not name.
**Eight** cells in the whole chart have a top weight under 0.50. At 0.99, mixing concentrates in the
three-bet family: **8.11 percent against 2.60 first-in and 2.30 facing an open**. The 12.33 / 4.02 /
3.27 split is the same measurement read at 0.999, and quoting it beside a pinned 0.99 is exactly the
defect decision 4 cites.

**1,646 cells sit below full arriving reach**, median 1,474 basis points, and **406 sit at 10 basis
points or less** - a tenth of one percent. Grading a student on those is grading the solver's noise.

**106 spots are continuations of a call the bot never makes**, carrying 0.0164 percent of arrival.
Phase 14 measured them and left the ruling on whether the drill deals them to this phase.

**The chart's opening ranges read narrower than the raked reference at three of five seats**: HJ
21.5649 against 21.65, CO 27.1733 against 27.89, BTN 39.2664 against 40.56. A rake-free solve reading
narrower than a raked one is the direction the derived-chart report itself says a solve is not
supposed to go, and the same report calls the opening family one of "the two that pass". Phase 14
ships these ranges as solved and this phase does not reopen them. It does have to say what it is
teaching, which is decision 8.

## 1. What unit the drill scores in

Reversibility: frozen-into-data

Default: **strategy weight. The drill reports the weight the chart puts on the action the student
took, and the gap to the weight it puts on its own top action, and it says in the student's own words
that it cannot price a mistake.**

Options: strategy-weight | simulated-ev | committed-ev-artifact
Answer:

**Two of these three are forbidden by the active contract**, which states "No EV, no chip cost, no
'this cost you N big blinds', anywhere in the drill, the report, or the packet" as a criterion rather
than a caution. They stay on the ballot because this is the item that ruling rests on, but picking
either reopens stage 1 and rewrites the contract before anything is built.

The question, in one sentence and with no code in it: when you fold a hand the solve raises, should
the trainer tell you "the solve raises this 100 percent of the time and never folds it", or should it
tell you "that fold cost you 0.8 big blinds"?

*Strategy weight.* Everything needed is committed and exact. The cost is that a student naturally
wants to know what a mistake cost, and this answer never gives them that. It also flattens two very
different errors: folding a hand the solve raises 100 percent of the time and folding one it raises
51 percent of the time both read as a gap, and only the first is really a mistake.

*Simulated EV.* Run the hand forward from the spot many times and difference the outcomes. This is
the only route to a chip number without new solver work, and it is noisy, slow, and measured against
a bot whose every postflop street checks through - so the number would price hero's preflop choice
inside a game nobody plays. Phase 06's standing constraint forbids claiming anything about postflop
from those figures, and an EV that depends on postflop play is such a claim.

*Committed EV artifact.* Re-extract from GTOpen with per-action EVs, bump the artifact schema to 3,
and commit it. This is honest and it is a phase-14-sized piece of work: a new extraction, a new
schema, a new set of range gates. It is the right answer eventually and it is not this phase.

The cost the default accepts: the drill's headline promise in `docs/V2_ROADMAP.md` - "say what the
chart says **and what the difference costs**" - is delivered by half. This contract states that
plainly rather than dressing a frequency gap as a price.

## 2. How the drill picks which spot to deal

Reversibility: frozen-into-data

Default: **stratified by family, then weighted by `arrival_ppb` within the family, with the 44
zero-arrival spots reachable only behind an explicit flag.**

Options: uniform | arrival-weighted | log-arrival | floor-then-arrival-at-33/33/33 |
floor-then-arrival-at-50/30/20 | floor-then-arrival-at-another-split-you-name
Answer:

**The split is the live part of this question and it is on the ballot rather than buried in the
default.** A floor per family plus arrival on the remainder is the shape; what it is set to is the
training judgement. At an even three-way split, first-in falls from 52.66 percent of real decisions to
33.3 percent of the deal and facing-a-three-bet rises from 8.24 to 33.3, which is a four-fold
over-weighting of the family a player meets least - defensible as training, since that is the family
you get least practice at in real play, and a real choice rather than a fact.

The question, in one sentence and with no code in it: should a training session show you the
situations you actually meet at the table in the proportions you meet them, which means more than
half your hands are the same five first-in decisions - or should it spread your time evenly over
every situation the chart knows, which means nine hands in ten are three-bet pots you meet once a
session?

*Uniform.* 219 of the 249 spots face a three-bet, so 88 percent of the deal would be a family that is
8.2 percent of real decisions. It also refuses 59.11 percent of what it deals, because the thin spots
are exactly the ones it over-samples. Both numbers make it indefensible.

*Arrival-weighted.* Refuses only 2.51 percent and shows you the game you actually play. But 52.66
percent of the deal is five spots, and the **median** three-bet spot arrives once in **899,346**
hands - the mean of one in 2,656 is carried by a handful of them and describes almost none - so a
student would never be drilled on a three-bet pot at all. The backlog entry
`A-SIXTH-OF-THE-COMMITTED-SET-IS-ALMOST-NEVER-DEALT` rejects both of these by name.

*Stratified then arrival.* Guarantees all three families appear, and inside a family shows the common
spots more often. It needs one number nobody has: how to split time between the three families. The
default splits it evenly three ways, which is a training judgement rather than a fact about poker,
and it is the part of this decision most worth a human overriding.

*Log-arrival.* One smooth rule, no strata. It buys smoothness with an invented constant, and this
repo does not invent constants.

The cost the default accepts: an even three-way family split is a guess. It is stated as data, the
report prints what all three policies would have dealt over the same budget, and it is one line to
change.

## 3. Whether the drill deals the 106 spots the bot can never reach

Reversibility: frozen-into-data

Default: **deal them, labelled, and never let a session imply the bot would have arrived there.**

Options: deal-labelled | never-deal | deal-only-behind-a-flag | split-deal-the-priced-ones-only
Answer:

**The active contract requires the 106 be split rather than ruled as one block**, and the first draft
of this item did not offer the split, which an independent reviewer caught. Measured: all 106 publish
a non-empty range, so on the strict reading none "publishes nothing" and the split is empty. On phase
14's reading, **81 of the 106 publish no hand that ever raises** - their menu offers a raise and no
class takes it. This phase takes phase 14's reading, because "can the student be shown a choice" is
the question a drill asks, and 18 of the 106 publish exactly one hand class. `split-deal-the-priced-ones-only`
deals the 25 and withholds the 81. Note also that **42 of the 106 have zero arrival**, so decision 2
already withholds them whichever way this falls.

The question, in one sentence and with no code in it: 106 of the chart's spots are situations you can
only be in because you called a raise - which is a call the bot itself never makes, since its own
strategy raises or folds instead - so should the trainer drill you on them anyway, given a human
player calls raises all the time?

*Deal labelled.* The range at each of these spots is the solve's real answer to a real situation, and
a human meets them constantly. Phase 14's own measurement says the two readings come apart cleanly:
"as the tree the bot plays these spots are dead, and as a training reference a human is drilled on
they are legitimate." Under the default sampling policy they are 0.0164 percent of arrival, so this
changes almost nothing about what comes up; it changes what the drill is allowed to say.

*Never deal.* Consistent with "the drill teaches the committed strategy", and it throws away 42.6
percent of the committed set to protect a consistency nobody asked for.

*Behind a flag.* Splits the difference and leaves the default silently inconsistent with the label.

The cost the default accepts: a student can be drilled on a spot the bot would not have reached, and
the label is the only thing stopping that reading. The report prints the count under both readings.

## 4. Where the line between right and wrong falls on a mixed cell

Reversibility: runtime-reversible

Default: **the session record stores the raw weights and the threshold is applied when the report is
rendered, pinned at a top weight of 0.99 to match the derived-chart report.**

Options: 0.9999 | 0.999 | 0.99 | no-threshold-report-the-split
Answer: [0.99]

Storing raw weights is what makes this reversible at all, and it is the reason this item is not
`frozen-into-data`. The repo already carries two different thresholds - 0.999 in one place and 0.99
in the derived-chart report, which additionally leaves 527 cells in an unnamed band between 0.90 and
0.99 - so this phase pins one before it measures anything, which is the lesson
`DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS` cost a phase to learn.

The cost the default accepts: at 0.99, 6.52 percent of cells have no wrong answer and the drill says
so instead of grading.

## 5. Whether the drill grades a cell the solver barely trained

Reversibility: runtime-reversible

Default: **no. A cell below 100 basis points of arriving reach is shown and not graded, and the count
is published.**

Options: grade-everything | floor-at-10bp | floor-at-100bp | floor-at-1000bp
Answer: [floor-at-100bp]

**577 cells sit at or below 100 basis points**, which is the floor this default picks; 406 sit at ten
or less, a tenth of one percent; and 1,646 sit below full reach with a median of 1,474. A weight the solver visited a handful of times is not a strategy, and
telling a student they were wrong against one is teaching them noise. `arriving_reach_bp` is on every
cell already, so this costs nothing to read.

The cost the default accepts: a student sometimes gets no grade on a hand they wanted graded, and the
floor is a round number rather than a measured one.

## 6. Committing a drill session as a fixture

Reversibility: frozen-into-data

Default: **one deterministic six-handed 100bb session, at one flat stack depth, committed under
`data/samples/`.**

Options: 1-session-of-50-hands | 1-session-of-200-hands | 1-session-of-1000-hands |
commit-none-and-generate-at-gate-time
Answer:

**The hand count is the question, and the first draft did not ask it.** The active contract requires
"the hand count of the committed session is pinned as data in the decision list before it is written",
and the phase-shape part - one session, six-handed, 100bb, one flat depth - the contract already rules.
So the ballot is the size.

`SAMPLE-HAND-THE-CHARTS-COVER` says committing sample data is a decision that needs a human, and it
also says why one is owed: all four committed sample hands are two- and three-handed, so the six-max
chart refuses every preflop point in them and no committed hand in this repo is one the chart can
answer. The session must be one flat stack depth or phase 13 decision 6 refuses it outright.
`data/samples` holds **572 KB against a 5,242,880-byte cap**, so 10.9 percent is used and 4.67 MB is
free. The corpus is most of what is *there*, not most of the cap, and a first draft of this item said
otherwise in a way that made a larger session look constrained when it is not. At the corpus's
roughly 1.1 KB per hand, even a thousand hands is about a megabyte.

The cost the default accepts: a small session is a thin fixture and the leak report over it is
correspondingly thin - the phase 08 finding was that breakouts by action and family are what make an
agreement number mean anything, and every breakout divides the hands further. 50 hands will not fill a
six-seat by four-action grid.

## 7. What a refusal says to the student, and where the reason is stored

Reversibility: frozen-into-data

Default: **the converter's derivation reason is carried through to the runtime refusal, so
"the source cannot price a three-way pot" and "outside the committed selection rule" read
differently at the table.**

Options: carry-the-derivation-reason-with-a-committed-table | derive-only-the-depth-bucket-and-refuse-the-rest |
keep-one-code-and-explain-in-the-report
Answer:

**This item is `frozen-into-data` because its default writes a new committed file**, and an
independent reviewer moved it here from `runtime-reversible`. The first draft argued that deriving a
refusal code is a derivation rather than a judgement; the class is about what gets written, and a
table every later refusal is looked up against is written. Its own cost line already conceded it:
renaming a code afterwards is a migration, and a migration is a task rather than an edit. Two live
sub-choices ride on the answer and neither was on the first ballot - where the table lives, and
whether it becomes part of the artifact schema.

`A-REFUSAL-CANNOT-TELL-THE-HUMAN-WHY`: today every excluded spot refuses as
`lookup:spot-not-covered`. A drill that ends a hand on a refusal without saying why teaches nothing.

**The live vocabulary is four codes, and it is not the two the backlog names.**
`solver_artifacts/lookup.py` publishes `derivation:beyond-committed-raise-depth`,
`derivation:multiway-exposure-above-threshold`, `derivation:big-blind-squeeze-spot` and
`derivation:no-legal-spot-key`. `backlog.yml` still quotes `derivation:source-misprices-multiway` and
`derivation:outside-selection-rule`, which `tests/test_chart_census.py` records as retired because
they named a rule that decisions 40, 46 and 48 replaced. The first draft of this contract copied the
retired pair straight out of the backlog, which is the failure that test exists to catch.

**The mechanism is cheap, which is why the default is easy, not why it does not block.** The committed artifact carries no
exclusion table, and the codes are produced by `chart_selection.exclusion_code` against the
33,969-node export. But the buckets are lopsided: `beyond-committed-raise-depth` is 33,362 nodes and
is derivable from the key alone (three or more raises in the sequence), while
`multiway-exposure-above-threshold` and `big-blind-squeeze-spot` are only 348 and 10 - a table of 358
keys, a few kilobytes against a 20 MiB cap. So the default derives the depth bucket and commits a
small table for the other two, generated by a committed script with a `--check` mode, the way the
sizing table already is. `derivation:no-legal-spot-key` is the fourth live code and has **zero**
members over the committed export - the census is 249 + 33,362 + 348 + 10 + 0 = 33,969 - and the
358-key argument holds only while that stays true.

The cost the default accepts: the codes are stamped into committed refusal inventories, so renaming
one later is a migration, and a third small bucket appearing later means regenerating the table.

## 8. What the packet tells the student about the ranges themselves

Reversibility: runtime-reversible

Default: **publish the measurement and do not reopen the ranges.** The packet states that the chart
opens narrower than the raked reference at HJ, CO and BTN, that a rake-free solve is not supposed to
read narrower, and that phase 14 shipped these ranges as solved.

Options: publish-the-measurement | say-nothing | halt-and-reopen-phase-14
Answer: [publish-the-measurement]

The other two options are both forbidden by the active contract - `say-nothing` by the packet honesty
criteria, `halt-and-reopen-phase-14` by the non-goal against re-deriving the committed artifact - so
picking either reopens stage 1.

A trainer that teaches a range has to say what the range is known to be. It does not get to relitigate
a ruled phase, and the numbers are phase 14's to answer. The alignment item is narrower than it first
looked: that the comparison gates nothing is a **ruling**, not an oversight - phase 14 decision 6 says
so and `check_solver_export_expectations.py` carries the words in its own docstring - so the finding
is not "nothing gates on it". The finding is that the report states a direction rule, three of five
opening rows break it, and the same report then calls the opening family one of "the two that pass",
which is the only prose a reader gets about the opens.

The cost the default accepts: a student is drilled towards an opening range that measures narrower
than a reference, and is told so rather than protected from it.

## 9. Whether the bounded personal-history ingestion lift is in this phase

Reversibility: runtime-reversible

Default: **out. The drill reads no hand history it did not itself deal.**

Options: defer-to-a-later-phase | land-the-boundary-change-first-then-build-it | build-it-now
Answer: [defer-to-a-later-phase]

**This was filed `frozen-into-data` in the first draft and an independent reviewer moved it back.**
Deferring writes nothing: no artifact, no fixture, no test stage 5 freezes. And stopping the loop
could not have changed the outcome, because `AGENTS.md` forbids the lift whatever anyone answers
here - so the stop would have spent a human's attention on a question the rules had already settled.
The genuine ask underneath it is a different question, and it is not this phase's to answer: **what
number bounds a personal-history import.** That is raised as a `- Paused:` line in the active
ExecPlan, which `scripts/review_queue.py` surfaces, and it belongs to whichever phase builds the
import.

The question this item does settle, in one sentence: the roadmap promises this phase can run a leak
report over your own exported hands and `AGENTS.md` forbids reading them, so the drill ships over the
hands it deals itself and the personal-history report becomes its own later piece of work.

Two things block it and only you can supply the first. `AGENTS.md` line 148 reads "No large
hand-history ingestion" and has never been edited since the repo was created; the lift needs a size
bound stated as a number, which five separate maintenance tasks have recorded as owed and nobody has
ever proposed. `docs/V2_ROADMAP.md` says the file wins until a `contract-update` changes it.

Four technical stops sit underneath the boundary, and they matter to how much the lift is worth. The
corpus reader parses PHH TOML only; it requires `finishing_stacks` per seat; it requires **every**
seat's hole cards, and a personal export shows only your own; it requires whole chips; and it refuses
a straddle, which `BLIND-STRUCTURE-VARIANTS` notes is common in exactly the home games this would
read. So the lift is not one boundary line, it is a second ingestion path.

The cost the default accepts: the phase delivers the drill and a leak report over drill sessions, and
the roadmap's "run it over your own history" stays unbuilt. This is the one scope cut in the phase.

## 10. What the drill does when the student takes an action the chart cannot price

Reversibility: runtime-reversible

Default: **show it, never score it, and say the flat was merged.**

Options: show-and-never-score | score-it-zero | score-it-at-the-merged-raise-weight
Answer: [show-and-never-score]

The other two are forbidden by the active contract, which states "An action the cell does not price is
shown and never scored"; picking either reopens stage 1.

This is reversible because the session record stores, per decision, the spot key, hero's hand class,
the chart's full weight vector, the arriving reach and the student's action, for every decision
including the ungraded ones - which the active contract now requires as a criterion rather than
leaving it to a builder, because decisions 4, 5 and 10 are classed reversible on the strength of it.
Re-scoring a recorded session is then a re-render rather than a re-collection.

The question, in one sentence and with no code in it: on four hands out of five the chart offers only
fold or raise, because the solve's flat was folded into the raise when the chart was built - so when a
student calls, should the trainer tell them the chart gives that zero, or tell them the chart cannot
separate a call from a raise here and decline to grade it?

Measured: 4,225 of 18,431 cells carry no `call` key at all. They are 25 spots - all 5 first-in and the
20 non-big-blind spots facing an open - and **80.2010 percent of arrival**. Only the 5 big-blind
spots facing an open price a call. The same hole covers the small blind's limp, which the reference
file limps 13.73 percent of the time and this tree has no branch for.

*Score it zero.* Simple, and it teaches that calling an open is always a mistake. It is not, and
`MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED` is the record of why: the weight is not
absent because the solve rejects the call, it is absent because the call was added to the raise.

*Score it at the merged raise weight.* Treats a call and a raise as the same answer. They are not -
they play differently from the flop on, which is the whole content of that backlog entry - and a
trainer that marks them identical teaches a student that the difference does not matter.

*Show and never score.* Fail-closed, matching how this repo treats every other thing it cannot answer,
and consistent with decision 5's reach floor. The student is told the truth: the chart merged the flat
and cannot grade this.

The cost the default accepts: the commonest mistake in the game - flatting an open too wide - is the
one the drill cannot grade, on four deals in five. That is a real limit on what this trainer teaches
and the packet states it first rather than in a limitations section.
