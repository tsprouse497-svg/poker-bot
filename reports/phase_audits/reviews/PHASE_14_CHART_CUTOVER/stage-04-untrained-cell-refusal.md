# Phase 14 stage 4: the untrained-cell refusal, and what measuring it found

Written 2026-08-27, in implementation mode, as the last pass stage 4 owes before the freeze. The
2026-08-27 investigation that closed the pair-split argument filed
`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY` and left stage 4 one instruction: assert that an
unreached class is refused rather than committed, without depending on the epsilon that rule
uses, because the epsilon is `frozen-into-data` and is Taylor's before stage 6.

That is done, and it is three assertions rather than one. Two independent reviewers, one
mechanical and one on the poker, then read it without having seen each other's work, and the
poker reviewer refuted the argument this note was first written around. **The stage halts.** The
recommendation in the backlog entry - detect the uniform row directly, which needs only an
epsilon rather than a reach cutoff - does not survive; neither did the first draft's replacement
for it. What is now open is a different and larger question, in `## Blocker` below, and it is
`frozen-into-data`.

Every number below is re-derived from `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz`
by a walk written for this pass, not quoted from the entry it is checking.

## What was added

Three tests in `tests/test_derived_chart.py`, which owns the committed chart and what its cells
must not have become. The predicate walk is imported from `tests/test_chart_derivation.py`, which
owns it, rather than copied - the same idiom the other three files in this pair already use.

- `test_a_class_that_never_arrives_is_refused_rather_than_committed`. Over all 86 spots, the
  committed cells are compared class by class against the export's own `reach_bp`. This is the
  substantive half: 7,422 of the 14,534 cells never arrive and not one of them is an answer.
  `test_every_committed_cell_carries_an_arriving_reach` already required a committed cell's own
  reach to be positive, but that is the artifact agreeing with itself - it cannot see a cell the
  converter committed while writing a reach it never read, which is the
  `committed-cells-claim-the-whole-range-arrived` defect one step further along.
- `test_an_untrained_cell_is_refused_at_the_table_rather_than_answered`. Absence from a payload is
  not yet a refusal; the lookup has to turn it into one with a code the caller can log, which is
  the standard the excluded nodes are already held to. The cell asked is the sharpest one in the
  grid and is named below.
- `test_no_committed_cell_sits_at_the_solvers_untouched_initialisation`. The same rule read off the
  strategy row instead of off the reach, at two tolerances that need nobody's ruling.

And one canary, `a-class-that-never-arrives-is-committed-anyway`, authored before the
implementation as the contract requires. It bites by the mechanism the two existing artifact
canaries use: no mutation touches anything under `data/`, so what fails is the disagreement
between the mutated derivation and the unchanged committed file, caught by
`convert_preflop_export.py --check`. It pins the line stage 6 must write, verbatim and including
its eight leading spaces, since `check_gate_bite` requires the find string to occur exactly once:

            if node.reach_bp[gtopen_class_index(hand_class_text)] <= 0:

Written at any other nesting depth it occurs zero times and the canary halts stage 7. It also has
to be the long form rather than a local: `committed-cells-claim-the-whole-range-arrived` pins
`reach_by_class[hand_class_text] = node.reach_bp[gtopen_class_index(hand_class_text)]`, so the
clean implementation that reads the index expression once into a local satisfies neither canary
and stage 6 writes it twice in the one loop body. That is a real cost of the two canaries
together and it is recorded rather than hidden; the alternative is re-aiming a canary that has
already been reviewed.

## The cell that makes the case

`t6/d100/SB/CO:raise@2.5,SB:raise@7.5,CO:raise@100` - the small blind facing a hundred-blind
four-bet jam - holding **72o**. Arriving reach zero, because nobody three-bets 72o. Its row is
the untouched initialisation exactly: **5,000 and 5,000** basis points across fold and call.

Committed, that cell does not read as missing. It reads as a considered coin flip, and the bot
calls off a hundred blinds with 72o half the time and says it with the same confidence it says
fold to a four-bet. That is why a uniform row is worse than a gap rather than merely as bad, and
it is the whole argument for the rule in one cell a poker player can check by eye.

## The census, reproduced, with one correction

| measured over the committed 86 | count |
|---|---|
| cells in the grid, 86 spots by 169 classes | 14,534 |
| cells that arrive - reach above zero | 7,112 |
| cells refused for never arriving | 7,422 |
| rows within two points of 1/n | **3,925** |
| of those, at zero arriving reach | 3,920 |
| of those, at reach above zero | **5** |
| rows within one basis point of 1/n, the quantisation step | 3,781, all at zero reach |
| rows within two points of 1/n at a menu of three or more actions | 1,516, all at zero reach |
| cells at zero reach whose row is **not** uniform | 3,502 |

The published 3,925 reproduces only under a **strict** reading of "within two points": exactly one
cell sits at a deviation of exactly 200.0 basis points, so an inclusive reading gives 3,926 and
the reach split 3,923/3, against the published 3,922/3. Nothing rests on which is meant, and it is
recorded because a boundary that moves the headline count by one is the kind of thing a later
reader re-derives and thinks they have found a discrepancy.

The last row is the one nobody had measured. 3,502 cells never arrive and carry a perfectly
ordinary row - AJo at the node above sits at 96.87/3.13 with reach zero. Reach and row are
different readings and neither implies the other, so a rule stated only over uniform rows misses
3,502 untrained cells, and a rule stated only over reach misses nothing here but is the cutoff the
ruling wanted to avoid. The tests assert the reach reading as the rule and the row reading as a
corroboration, which is the disposition the backlog entry recommends, arrived at from the other
direction.

## Blocker

- **Does the untrained-cell rule refuse on arriving reach alone, or does it also refuse where the
  solve never trained the node?** `frozen-into-data`, so it blocks on a human. The evidence, the
  three options and the withdrawal of this note's first answer are all below; nothing else in this
  section is a separate ask.

### Withdrawn: the five cells this note called threshold hands are not threshold hands

Raised by the independent poker reviewer, reproduced here by the
  coordinator's own walk, and it inverts the recommendation this note carried.

  The first draft argued that the uniform-row test cannot fire at a two-action node because 1/n is
  50 percent and 50 percent is what an indifferent hand plays, and it led with AKo mixing 51.77
  percent at `t6/d100/BB/BTN:raise@100` inside a clean continue ladder. **The ladder is real and
  the range it is computed against does not exist.** The 100bb open-jam carries zero weight on all
  169 classes at every one of the four opening nodes - measured, `action_frequency` is 0.00000000
  percent and the count of classes with any weight is 0 at LJ, HJ, CO and BTN - so that node's
  arrival probability is exactly zero. Every frequency in it is a strategy against an empty range.
  Reading it as the most instructive cell in the chart was the error, and the "at full reach"
  framing is what hid it: `reach_bp` is hero's own range filter and says nothing about whether the
  node is ever played.

  The test the note should have run is the one the two-action structure hands you. Both actions
  are terminal and the predicate guarantees heads-up, so EV(call) minus EV(fold) is monotone in
  the class's equity against a single fixed range, and **at most one class per node can sit at
  indifference**. Counting arriving classes with a call frequency strictly between 5 and 95:

  | node | arrival probability | interior mixes |
  |---|---|---|
  | `BB/SB:raise@2.5,BB:raise@7.5,SB:raise@100` | 3.8e-03 | **1** |
  | `BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@100` | 1.3e-03 | **1** |
  | `CO/CO:raise@2.5,BB:raise@7.5,CO:raise@22.5,BB:raise@100` | 1.4e-04 | 3 |
  | `LJ/LJ:raise@2.5,CO:raise@7.5,LJ:raise@22.5,CO:raise@100` | 1.6e-04 | 5 |
  | `SB/CO:raise@2.5,SB:raise@7.5,CO:raise@100` | 6.7e-06 | 7 |
  | `BB/BTN:raise@100` | **0** | 6 |
  | `LJ/LJ:raise@2.5,BB:raise@7.5,LJ:raise@22.5,BB:raise@100` | 1.1e-04 | **19** |

  The two nodes the solve actually visits show exactly the one mix theory allows. The five this
  note defended show three to nineteen, and the worst of them is not poker at any reading: facing
  a 77.5bb five-bet jam it calls QQ 86.55, JJ 80.06, TT 76.02, **KK 69.02**, 99 49.22, and then
  K7s 31.80, Q8s 26.37, K5s 19.32 and J8s 5.88. Kings below queens, jacks and tens, and a third
  of the K7s combos stacking off. The 99 at 49.22 percent is sitting in the middle of that row,
  not at a threshold in it. The reviewer priced the other four against the solver's own jam range
  and none is indifferent either: AKs is a call worth about +7.9bb, and QQ, JJ and 99 are folds by
  3.1, 4.7 and 5.8bb - errors 500 to 1,200 times the solve's own achieved gap of 0.0062bb.

  So the general property `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` stands, and the conclusion
  drawn from it does not. It is not that no cell-level rule can work at a two-action node; it is
  that the row shape is the wrong instrument and the node is the right one.

### The reach rule commits 1,031 cells at eight spots the export says are never reached

Independently measured: `t6/d100/BB/{LJ,HJ,CO,BTN}:raise@100`, `t6/d100/CO/CO:raise@2.5,{BTN,SB}:raise@100`,
  `t6/d100/HJ/HJ:raise@2.5,CO:raise@100` and `t6/d100/LJ/LJ:raise@2.5,HJ:raise@100` all have
  arrival probability exactly zero, because nobody open-jams 100bb and nobody jams over an open
  for 100bb. At the four big-blind nodes every one of the 169 classes carries `reach_bp = 10000`,
  so the ruled rule commits all of them.

  This is the same mistake in a second place, and it is the one that matters for the artifact:
  **arriving reach is hero's own range filter, not a measure of whether the solver trained the
  cell.** A node can have every class at full reach and never be played. The census headline -
  7,422 cells never arrive and none is an answer - is true and is not the whole rule. Beside it,
  1,182 committed cells (16.6 percent) sit at arriving reach below 10 basis points, and the
  reviewer's slack calculation puts 2,474 of the 7,112 committed cells (34.8 percent) at nodes
  where the solve's 0.0062bb global gap constrains local strategy by nothing at all, because
  `gap / P(reached)` exceeds the 100bb stack.

### The three options

The question this note first put - which epsilon, or whether a uniform-row rule fires at a
two-action node - is the wrong question and is withdrawn with the argument behind it. What
replaces it decides what goes into the committed artifact, which is what makes it
`frozen-into-data`.

1. **Ship as ruled.** Refuse the 7,422 cells that never arrive and commit the rest. Simple, and it
   commits 1,031 cells at eight never-reached spots plus the interior noise above.
2. **Add a node-level rule.** At a two-action all-in node, refuse the arriving classes that are
   interior when more than one class is interior - theory caps it at one and the two well-converged
   nodes obey it. It refuses the noise and keeps the pure cells, which are robust: AA and KK call
   at 99.98 percent against any range that could jam, 72o folds at 0.02.
3. **Refuse the never-reached spots**, on arrival probability rather than on reach. One caveat
   that is not a preference: dropping those eight *spots* collides with the ruled 86-spot
   predicate, which is Taylor's 2026-08-25 ruling and a `contract-update` to move, so this option
   has to be read as keeping the spot and refusing every cell in it. Taken that way it is a
   converter rule like the other two.

**The coordinator makes no recommendation between 2 and 3**, having just been wrong about the
poker that would decide it.

The tests were changed before this was filed so that they do not pre-empt any of the three: the
committed cell set is asserted to be inside the arriving set and bounded above by 7,112, and
nothing forces a cell to be committed. Verified by running the frozen assertions against a chart
built each way - ship as ruled 7,112 cells, a one-percent reach cutoff 5,311, a uniform-row
epsilon 7,107, the interior-mix rule 6,844, emptying the never-reached spots 6,081 - all green,
with a converter that commits every class red. An earlier draft asserted `arriving - cells` was a subset
of five named cells, which would have made every option above unimplementable, including the
reach threshold `CHART-MUST-REFUSE-AN-UNTRAINED-CELL` asks for in terms. That was caught by the
independent mechanical review and is removed.

## Non-blocker

- **The refusal itself is right, and its cost on a drilling student is larger than this note
  said.** 6,330 of the 7,422 refused cells - 85 percent - are classes hero held at his own
  immediately preceding decision and took a different action with, so they are one small deviation
  away. At `t6/d100/SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` the chart arrives with 28 classes
  and refuses 141, the standard three-bet bluffs AQo, KQo, AJo, 98s, 65s and 54s among them. A
  student who four-bets JJ and faces a jam gets a lookup miss. Refusing is still correct - a coin
  flip read off an untrained row is worse than a gap - but the packet must say that the
  four-bet-facing family is undrillable for a deviating student, and the miss has to reach him as
  "off tree, no answer" rather than as an error. It compounds with the ruled loss of four opening
  ranges: the chart holds spots whose arriving ranges are defined by opening ranges it does not
  teach.
- **The menu-of-three corroboration is sound with room to spare, for a better reason than the one
  given.** The closest arriving cell to 1/n at a menu of three or more is T8s at 1,183 basis
  points against a 200-point tolerance. The margin is what carries it; the stated reason - that
  1/3 and 1/4 are not frequencies trained play lands on - is weaker than the measurement, since a
  four-way menu can legitimately sit near a quarter.
- **The two chart_derivation canaries jointly specify duplicated code.** Recorded above at the
  canary. Stage 6 writes the 47-character index expression twice in one loop body, because the
  clean form that reads it into a local satisfies neither find string.
- **`check_gate_bite` proves nothing about the three assertions this stage added.** All 67
  mutations touch `src/` or `scripts/`; the three new tests read only `data/`, so they are
  insensitive to every one of them. The new canary bites through the pre-existing
  `--check` subprocess in `test_the_committed_chart_reproduces_from_the_committed_export`. That is
  the framework rather than this stage, and it is said rather than implied.
- **`test_no_committed_cell_sits_at_the_solvers_untouched_initialisation` cannot fail unless the
  test above it does**, since all 3,781 and all 1,516 cells it names sit at zero reach. It is
  corroboration by design and its two count assertions guard the export rather than the converter.
- **98 pair-ladder and 74 suited-over-offsuit dominance inversions among committed cells**, worst
  at `LJ/LJ:raise@2.5,HJ:raise@7.5` playing 33 at 0.37 percent and 22 at 99.67. Taylor ruled these
  non-gating on 2026-08-27 and that is not reopened here. Recorded because this addition is
  presented as the untrained-cell detector and does not see them.
- **The mechanical review's fourth blocker does not hold.** It reported
  `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` as absent from `backlog.yml`; it is present, and
  `run_full_quality_gate`'s backlog integrity check - which fails on a cited id that resolves to
  nothing - passes. The reviewer read the file before the entry was written.

## Alignment

- `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` - a "did the solver train this cell" test built on
  distance from 1/n cannot work where n is 2, because the initialisation and the indifference
  point are the same distribution. It is a general property of the test rather than a fact about
  this export, and any later phase adding a cell-level trained-ness check inherits it. Amended
  after the poker review: the remedy is not to fall back on reach, it is the node-level test
  below.
- `INTERIOR-MIX-COUNT-BOUNDS-A-TWO-ACTION-NODE` - at a node offering two terminal actions in a
  heads-up subtree, at most one hand class can be indifferent, so counting arriving classes with
  an interior frequency is a convergence test that needs no epsilon and no threshold. Measured
  over phase 14's 86 it separates the two well-converged all-in nodes (one mix each) from five
  undertrained ones (three to nineteen). It is the instrument a later phase should reach for.
- `ARRIVING-REACH-IS-NOT-A-TRAINED-NESS-MEASURE` - `reach_bp` filters hero's own range and says
  nothing about whether a node is ever played. Eight of phase 14's committed spots have arrival
  probability exactly zero while carrying every class at full reach. The computable proxy is node
  arrival probability, or `achieved_gap_bb / P(node reached)` against the pot, neither of which
  anything in this repo reads.

## Independent review

Two read-only reviewers, mechanical and poker, neither of whom wrote any of this and neither of
whom saw the other's work. Both re-derived the census from the committed export with their own
decoder and walk, and both reproduced it exactly, including the strict-versus-inclusive boundary
at 200 basis points.

The mechanical review found four blockers. Three are fixed above: the two-sided cell bound that
foreclosed every reach-threshold answer, a tautology asserting `GRID_CELLS - COMMITTED_CELLS`
against its own definition, and a `mutations.yml` comment that said "two of the eight" over nine
entries while naming a canary id renamed on 2026-08-25. The fourth does not hold and is recorded
under `## Non-blocker`. Its non-blockers are all accepted and appear above, including the false
sentence in this note's own text and the wrong worked example in
`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`, both corrected at the source.

The poker review found the blocker that halts the stage. Its central measurements were
reproduced independently by the coordinator before being acted on: the 100bb open-jam carries
zero weight on all 169 classes at all four opening nodes, the interior-mix counts are 1 and 1 at
the two well-converged all-in nodes against 3, 5, 6, 7 and 19 at the five this note defended, and
eight committed spots holding 1,031 cells have arrival probability exactly zero.
