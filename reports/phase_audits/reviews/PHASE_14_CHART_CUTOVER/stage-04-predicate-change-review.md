# Phase 14 stage 4: review of the predicate change

Two independent read-only reviewers read `git diff 9be45bf` over the contract, the decision record,
the ExecPlan and the disposition note, before it was committed. Neither wrote any of it. One was
mechanical, re-measuring every count in the new text against the committed export and checking the
rewrite against the contract it replaced; one was on the poker, asked whether the resulting bot
plays and teaches correctly and told explicitly to ignore the paperwork.

The mechanical pass confirmed every number. The poker pass found that the ruling's premise is
false, and that finding is why this phase is halted again rather than advancing.

## Blocker

- **[resolved] The ruled predicate does not select the nodes the model prices exactly. 24
  of the 110 carry the defect, and they hold 73 percent of the decisions a real player makes.**
  The product approximation bites at **terminals**, and a node's strategy is backward-induced over
  every terminal below it, so the property has to be stated over the subtree rather than over the
  actions already taken. "At most one opponent voluntarily invested" is a statement about the past.
  Recounted over seats that have not folded rather than seats that have acted, and reproduced
  independently by the coordinator: **110 under the ruled predicate, 5,472 terminal-clean, 86 in
  both, 24 in the 110 with a multiway terminal still reachable.** The 24 are four of the five opens
  (the small blind's is clean, only the big blind is left), the RFI-defence decisions with seats
  still behind, and the decisions facing a 100bb open-jam. Mapped onto the corpus that is **2,232 of
  3,054 preflop decisions**.

  It is visible in the cells and the signature is unmistakable - hero's aggressive branch is right
  and hero's passive branch is gone. Flat-call frequency facing a 2.5bb open, measured over hero's
  arriving range:

  | hero | flat | 3-bet or jam |
  |---|---|---|
  | BB, closing, nobody behind | 21.0 to 24.1% | 6.3 to 26.4% |
  | SB, one seat behind | 0.66 to 4.54% | 5.5 to 14.3% |
  | BTN vs CO, two behind | **0.07%** | 11.3% |
  | CO vs HJ, three behind | **0.11%** | 7.8% |
  | HJ vs LJ, four behind | **0.14%** | 6.5% |

  Every three-bet figure is close to right and every flat is between zero and a fifth of what six-max
  play calls for. The gradient runs exactly with how many players can still enter, which is the
  mechanism: flatting invites the multiway terminals the model underprices, so the solver never
  flats. Forward-simulated, the solve walks the blinds on 71.2 percent of hands and reaches a
  multiway flop on 0.18 percent, against 48.1 and 4.01 in the 499-hand corpus. The excluded multiway
  family is not a family this tree even generates, because the same defect deleted the cold calls
  that would create it.

  The claim that the committed half is "priced exactly by construction" is therefore false and has
  been removed from the contract, the disposition note's recommendation and the human vetting
  requirement wherever it appeared. What replaces it is not a coordinator decision: cutting to the
  86 drops four of the five opens, leaving a chart reachable mostly through decisions the bot
  refuses, and shipping the 110 means shipping 24 spots that teach a button never flatting a cutoff.
  Both are Taylor's, and the phase halts here.

  One thing the review settles rather than reopens: the **strict** reading of "invested" is right.
  An opener who later folds to a three-bet still counts. Loosening it to "still live" would admit
  5,386 more nodes whose terminals are genuinely heads-up but which are all reached through a cold
  call and therefore priced against the degenerate calling ranges above. The strict reading costs 7
  of 3,054 corpus decisions.

- **[resolved] The four-bet continuations teach folding JJ at 32 percent pot odds.** At HJ
  facing a lojack four-bet to 22.5, inside the 110, JJ arrives at 96.7 percent reach and folds 97.2
  percent, TT folds 99.9, 99 folds outright, AJs jams 51.4 percent with no call in AQs, and 76s
  calls 99.6. Hero is adding 15 into 31.5 needing 32.3 percent with 77.5 behind. Sub-question 1 was
  answered "the 110 as counted" and the consequence was put on the record rather than in the ranges;
  the reviewer's point is that the record does not reach the person at the table, and a confident
  wrong answer is worse than a refusal because it replaces the student's prior instead of leaving it.

- **[resolved] Adjacent small pairs split 0.07 against 99.94 at full reach, and the
  aggregate-only dominance ruling cannot see it.** Small blind facing a button open, all four pairs
  at full reach: 55 continues 99.83 percent, **44 continues 0.07**, 33 continues 16.20, 22 continues
  99.94. The 2026-08-24 ruling gates dominance on bands where indifference cancels, on the ground
  that a solver's split among near-indifferent hands is its considered answer - which was true of the
  lojack's 44 at 72.81 percent, a genuine mix, and is not true of 99.94 against 0.07. The ruled
  four-band grouping puts 44 and 22 in the same band, so it cannot fire.
  `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` already specifies the remedy and is filed
  against this phase and deferred.

- **[resolved] The refusal-rate direction was stated against the wrong baseline, and backwards
  against the right one.** The contract predicted the refusal rate would rise and said 8.3 percent of
  corpus decisions leave phase 08's denominator. Both were measured against the abandoned 5,626-spot
  plan. All 36 spots of the **retired** chart are heads-up, verified by enumerating its
  `action_sequence` values, so nothing the bot answers today is lost, coverage goes 36 to 110, and
  refusals fall. Fixed in the contract's Scope and closing-measurement criteria and in the ExecPlan,
  and the report must now name its baseline.

- **[resolved] Decision 5 was left frozen-into-data with a rationale made entirely of the retired
  premise.** Both its stated reasons - that the reach field makes decision 1's rule live in the
  artifact, and that the bytes must be measured against a 15.9 MiB budget - died with the reach
  floor. Amended: the ruling stands on the smaller half that survives, prospectively rather than
  presently, and the amendment says so.

- **[resolved] Decision 10 asserted a property the same task's own measurement falsifies.** It said
  the group gate "keeps a real check - a transposed hand index or a mis-assigned actor still fails
  it". Measured over the 5,626, suited-versus-offsuit flagged 2,007 nodes as solved against 818
  transposed, so the gate scores the wrong index mapping as the better one. The claim is withdrawn
  in decision 10 rather than restated, and whether any aggregate form passes over the retained set
  is now an obligation the contract puts before the freeze.

- **[resolved] The ExecPlan contradicted itself and cited a rule the rewrite had deleted.** Its
  design sections still described `REACH_FLOOR_BP = 200`, a single exclusion code, and a live "byte
  budget is not proven" risk invoking a contract rule that no longer existed. All three corrected,
  and the discharged verification brief is marked as history.

- **[resolved] The halt commit shipped a red quality gate that nobody ran.** The stage-4
  verification note tabulates pair bands in the notation a poker player uses, two pair names joined
  by a hyphen, which `run_full_quality_gate`'s backlog integrity check reads as citations of
  backlog ids nobody declared. Four errors. Rewritten as "AA to JJ" and filed, because the next
  phase to write about ranges hits it too.

## Non-blocker

- **Every count in the new text reproduces.** The mechanical reviewer re-measured 38,828 nodes; 110
  heads-up; the reach floor as the unweighted mean of `reach_bp` reproducing 5,626; all 110 clearing
  it; 35 at full reach; 5/30/30/30/15 by prior aggressive actions; 16/17/18/19/20/20 by seat; the
  four menus 60/30/15/5; 35 spots offering both a raise and a jam at 5.0 percent jam volume with the
  majority at 2 and all of it at 0; and the retired 313/60.6/177/35 under the same definition. The
  5.0 percent only reproduces mass-weighted, which is the definition that produced 60.6, so the
  restatement is like-for-like.
- **Decision 6's table survives but is not what its name suggests.** No spot in the 110 offers two
  *named* raise sizes: 75 offer none and 35 offer exactly one plus the all-in. So the second entry
  records a shove frequency rather than a sizing choice, and the chart cannot teach sizing at all,
  because the solve had one opening price and one raise multiplier. It still earns its place - at 7
  of the 35 the jam is 17 to 67 percent of aggressive volume, worst at BTN facing an SB three-bet -
  and at 25 of them it is under 0.05 percent and the row is dead weight. The packet should say what
  the second entry is.
- **20.3 percent of committed cells sit at the solver's untouched uniform initialisation**, every
  action at exactly 1/k, all of them at zero arriving reach; 39.9 percent have zero reach. The
  contract requires the reach field, which is the right field, but recording is not refusing and no
  criterion says the runtime declines a cell the solver never trained. Corpus exposure is 0.5
  percent of matched decisions, so the closing measurement is safe; the training use is not, because
  a student who deviates upstream lands there by construction.
- **QJo is ordered below JTo in three of the five opening cells** (LJ 95/8/0 for JTo/KJo/QJo, HJ
  100/42/1, CO 100/86/11 with A9o at 82). Unlike the lojack opening 76s over T6s this has no
  connectivity story. 24 combos, so small, but these are the most-read cells and it belongs in the
  per-cell worst-case list the contract already publishes.
- **The big blind underdefends the small blind by more than decision 9's band admits.** It continues
  49.02 percent against a 54.09 percent opening range, closing for 1.5 into 5 at 2.67 to 1 in
  position, folding 63 classes at 95 percent or more including Q7o, J8o, T7o, 97o and K2o through
  K4o. The +6.14 defence delta was read as inside the band, but the band was set from the reference's
  defence figure while the small blind's *opening* range moved +19.68 points. This is
  `REALIZATION-MODEL-UNDERPRICES-POSITION`, already accepted and carded, and worth restating in the
  packet in those terms because it is the most common decision in six-max.
- **Blind versus blind is the part of the chart the reviewer would trust.** Every BvB node has at
  most one live opponent by construction, so the small blind open, the big blind defence and the
  three-bet, four-bet and five-bet continuations are all inside the 86 and all exactly priced. Its
  54.09 percent small blind open is right for a rake-free no-limp tree.
- **The ten open-jam nodes are harmless dead coverage.** Formally in the 24, but hero calls 1.5 to
  2.8 percent, which is about the right range, and nobody open-jams 100bb. They pad the count.
- **The re-solve section lost detail to the line cap and was partly restored.** Its five proofs, the
  config and model pins and the human-read clause are back; the per-proof thresholds now live in
  decision 2 rather than in the contract.
- **`CURRENT_TASK.yml` is correct for a contract-update**, with `base_commit` at the main merge, a
  three-path `approved_scope` correctly omitting `tests/**`, `verification/**` and `scripts/**`, and
  a dated log entry naming the defect and why the mode changed.

## Alignment

- `SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS` - a selection rule that claims a
  pricing property must be expressed over the terminals a node's value is computed from, not over
  the actions already taken, and measured before it becomes an acceptance criterion.
- `CHART-MUST-REFUSE-AN-UNTRAINED-CELL` - carrying arriving reach per cell is not using it; the
  runtime needs a per-cell refusal at a ruled threshold so a cell at the uniform initialisation is a
  miss rather than an answer.
- `SOLVE-CAPTURE-NEEDS-A-POT-ENTRY-RATE-CHECK` - walk the solved strategies forward and publish the
  preflop-end rate and the multiway-flop rate beside the corpus's. This solve gives 71.2 and 0.18
  against 48.1 and 4.01, and no range-shape check in the repo can see a defect that lives in the
  aggregate.
- `SELF-PLAY-COVERAGE-PREMISE-RESTS-ON-THE-REACH-FLOOR` - `SELF-PLAY-NO-LONGER-FINDS-COVERAGE-GAPS`
  reasons entirely from the retired 2 percent floor and its conclusion inverts under the new
  predicate.
- `BACKLOG-SWEEP-MISSES-ENTRIES-FILED-UNDER-A-CATEGORY` - a phase's closing sweep is keyed on
  `phase: NN` and cannot see the entries that phase filed under a subject label.
- `LOOP-HAS-NO-RULE-FOR-A-MID-PHASE-CONTRACT-UPDATE` - phase 14 has now flipped implementation to
  contract-update twice on precedent rather than on a rule.
- `PHASE-CONTRACT-LINE-CAP-FORCES-REWRITES-OVER-AMENDMENTS` - the 300-line cap forced a rewrite
  instead of an amendment and the rewrite lost three cross-references, all found by review. The
  contract is back at 300 of 300.
- `BACKLOG-CITATION-SHAPE-MATCHES-POKER-NOTATION` - the citation check reads a hand-range band as a
  backlog id.


---

**Correction, 2026-08-25.** This note's corpus denominator of 3,054 preflop decision points is
wrong by six. The committed 499-hand sample holds **3,048**, confirmed against `replay_hand`'s own
`DecisionPoint` stream; 3,054 counts the six decisions of `pluribus/41b/204`, a hand the sample
excludes. The digits are left as written because this is a dated record of what was measured. No
conclusion in it moves - 2,232 of 3,048 is 73.2 percent and the multiway share is 8.3 percent under
either denominator. See `stage-04-eighty-six-coverage.md`.

---

## Ruled by Taylor, 2026-08-27: all three blockers close, and one of them was a reading error

The three blockers above were raised on 2026-08-25 against the 110-spot plan. All three were put
back to Taylor on 2026-08-27 with the measurements re-derived from the export by an independent
walk that reproduces the published census exactly - 38,828 nodes, 110 under the history clause,
5,472 under the terminal clause, 86 in both, 24 ruled but multiway. He ruled all three.

### Blocker 1: answered on 2026-08-26, a day after it was written

`da05adf` ruled the cutover onto the 86: the predicate is both clauses conjoined, and he took the
disposition's third option in full so the missing spots have a route back. That commit did not
touch this marker, so the answer existed and the board still showed the question. Nothing was
decided today; the marker is corrected to match a ruling already made.

### Blocker 2: withdrawn as a defect. The rows are a coherent polarised four-bet defence

The finding was read cell by cell, which is not the level a solve is answerable at. At
`t6/d100/HJ/LJ:raise@2.5,HJ:raise@7.5,LJ:raise@22.5` - hero in position, adding 15 into 31.5 for
32.26 percent with 77.5 behind - the continue frequency by group, combo and reach weighted:

| group | continue | share of arriving weight |
|---|---|---|
| whole arriving range | 65.40% | 100% |
| premium - AA-QQ, AKs, AKo | 96.15% | 39.1% |
| suited connectors - JTs to 54s | 99.10% | 12.3% |
| suited broadway - AQs, AJs, KQs, KJs, QJs | 43.38% | 18.9% |
| middling pairs - JJ to 22 | 1.21% | 20.2% |

Value continues, the suited bluffs continue, the middling pairs fold. That is what a polarised
three-bet range does against a four-bet, and preflop bluff-continues are the whole point of the
suited connectors being in the three-bet range at all. JJ against a four-betting range of roughly
QQ+ and AK is dominated and flops badly for its equity; 76s in position, rake-free, at 32 percent
pot odds and 1.7 SPR realises well and can win a stack. Equity losing to playability is a standard
solver result and not a broken row.

**The claim "no preflop solution plays that" is withdrawn.** It was the reviewer's claim and this
coordinator repeated and amplified it without checking the aggregate.

The convergence hypothesis offered alongside it is withdrawn too, and it failed its own test.
If the deep nodes carried no real solve their rows would sit nearer uniform. Measured over cells at
reach at least 5 percent, purity runs the other way:

| prior aggressive actions | cells | pure above 99% | mean max action weight |
|---|---|---|---|
| 0 - the open | 169 | 88.2% | 0.976 |
| 1 - facing an open | 1,690 | 85.3% | 0.977 |
| 2 - facing a three-bet | 2,050 | 69.3% | 0.960 |
| 3 - facing a four-bet | 872 | 67.1% | 0.943 |
| 4 - facing a five-bet | 184 | 83.7% | 0.956 |

Deep nodes mix more, not less, and mean max weight moves 0.976 to 0.943 across the whole tree.
There is no depth-dependent degradation to point at.

One number survives and it is not about cell order: whether 65.40 percent is the right total.
Continuing nearly two thirds of a three-bet range against a four-bet is high, and the thing that
would move it is `realization: calibrated` - GTOpen resolves flops by scaled equity share rather
than playing them, and a four-bet pot at 1.7 SPR is where that approximation is weakest. Ruled:
that is a question about the model the chart derives from, not about the derivation, and it is
filed against phase 16 as `CALIBRATED-REALISATION-PRICES-FOUR-BET-POTS-UNTESTED`. Phase 14 changes
nothing for it.

### Blocker 3: reframed. The band is committed, not the cell

The test the note never ran is the individual split against the aggregate of the band it sits in.
The example spot as filed - the small blind facing a button open - is not in the 86 at all, because
the big blind is still live behind it. The pattern is, though: 43 of the 86 spots carry an adjacent
full-reach pair gap over 50 points and 14 carry one over 90. Measured against the bands:

| seat | spot | the two cells | JJ-22 band | all pairs |
|---|---|---|---|---|
| LJ | `LJ:raise@2.5,HJ:raise@7.5` | 33 0.37% / 22 99.67% | 67.12% | 74.87% |
| HJ | `HJ:raise@2.5,BTN:raise@7.5` | 66 99.96% / 55 1.17% | 70.24% | 77.11% |
| CO | `CO:raise@2.5,BB:raise@7.5` | 55 99.16% / 44 0.45% | 89.76% | 92.13% |
| BTN | `BTN:raise@2.5,BB:jam@100` | TT 99.71% / 99 0.19% | 20.61% | 38.93% |

Every band aggregate is a sensible number. The pairs are near-indifferent at these prices, and at
an indifference point every mixture is optimal, including the extreme ones - a solver that puts 33
at zero and 22 at one broke a tie, and any other tie-break scores identically. That is what the
2026-08-24 dominance ruling already said, and this note escalated it by comparing cells without
ever checking the band. **The 2026-08-24 ruling stands and this note was wrong to contradict it.**

It cannot be proved from the export either way: the file carries `path`, `actor_pos`, `actions`,
`strategy_bp` and `reach_bp` and no EV field, so an arbitrary optimal split and a tie broken the
wrong way are indistinguishable. There is also no seed to vary -
`scripts/extract_gtopen_preflop.py` passes only `iterations`, `check_every` and `target_gap`, and
the solve stopped at 300 because it reached the 0.01 bb target at 0.0062 - so the only
discriminating run is a tighter target, which needs the GTOpen server and is not run here.

**The ruling does not depend on that run.** For 22 to genuinely outrank 33 there would have to be a
poker reason, and there is none: 33 dominates 22 when they clash and the two are otherwise near
identical against a three-bet range. So the per-cell number is either an arbitrary tie-break or
wrong, and under both readings it carries no information while the band aggregate is true.
**Ruled: where a class sits in a near-indifferent run, the committed cell carries the run's
aggregate rather than the class's own tie-break.** Rejected: committing the cell, which transcribes
a tie-break into a rule the drill then teaches with the same confidence it teaches folding to a
four-bet, in 43 of 86 spots.

Filed as `COMMIT-THE-BAND-NOT-THE-TIE-BREAK` against phase 14, because it is a conversion-step rule
that stage 6 implements and stage 4's tests must encode.

**What this ruling does not yet pin, and it is `frozen-into-data`.** What counts as a run. Decision
10 failed twice at exactly this - the 13 single ranks, four bands, three bands and two bands all
measured differently and choosing the smallest was rejected as picking a threshold to go green - so
naming bands by hand is the move that has already failed. The recommendation put to Taylor with
this note is pool-adjacent-violators over each family run (the 13 pairs, each suited row, each
offsuit row): it has no threshold and no band list, it preserves each pooled block's reach-weighted
aggregate exactly, it leaves every monotone run untouched, and the run it pools is derived from the
data rather than chosen. Its one assumption is that higher-in-family at least matches
lower-in-family, which is the ordering decision 10 declined to *gate*; conditioning committed data
is not the same act as failing a build, and it only moves cells where the order is violated and
where the cell has been shown to carry nothing. That distinction is his to accept or reject before
stage 4 re-cuts the tests.

---

## Reversed the same day, 2026-08-27: commit the cell, and the investigation found something else

Taylor asked how we know the pair splits are not optimal. The honest answer was that we did not, so
the solver output was investigated directly rather than argued about further. Two of the three
grounds for the band ruling above did not survive it, and the ruling is withdrawn before any
implementation. `COMMIT-THE-BAND-NOT-THE-TIE-BREAK` is closed as withdrawn.

### The consistency argument was invalid

The band ruling was defended by a second measurement: across the 86, 22 continues more than 33 at
ten spots and never fewer, and 33 more than 44 at seven and never fewer, which was read as a
systematic effect rather than a coin flip. That reasoning is wrong. The solver is deterministic -
the source card records the ruled config solved twice in a fresh process against a restarted server,
byte-identical, `max_divergence_bp: 0` - so a deterministic tie-break lands the same way at every
node. Consistency across spots cannot separate a real effect from an arbitrary one, and it was used
as if it could.

### The anomaly is much narrower than the filing said

Measured over the 86 with both classes required at full arriving reach: 71 spots carry four or more
real pair cells, and **56 of those are clean contiguous thresholds** - continue down to some pair,
fold everything below, which is what optimal play looks like when hands are ordered by strength.
Fifteen break contiguity, and all fifteen break it the same way:

| spot | AA-88 | 77 | 66 | 55 | 44 | 33 | 22 |
|---|---|---|---|---|---|---|---|
| `LJ/LJ:raise@2.5,HJ:raise@7.5` | 97-100% | 56% | 100% | 1% | 0% | 0% | 100% |
| `LJ/LJ:raise@2.5,CO:raise@7.5` | 100% | 72% | 97% | 1% | 0% | 1% | 100% |
| `LJ/LJ:raise@2.5,BTN:raise@7.5` | 100% | 68% | 91% | 2% | 0% | 1% | 100% |

Every one has a mixed hand at the threshold. A mixed hand is where the solver found indifference,
and inside an indifference region the total is determined while the allocation across it is not. So
66 and 22 at 100 percent beside 55, 44 and 33 at zero is what an arbitrary allocation of a
determined total looks like. Smoothing it changes nothing that can be shown to be wrong and risks
deleting something that cannot be shown to be right.

**Ruled: commit the cell as solved.** No PAV, no band, no conversion change for this. The export
carries no EV field so nothing in the file settles it, and the run that would - a solve at a tighter
target - needs the GTOpen server and is not run here.

### Two hypotheses closed on the way

Neither is a defect, and both are worth recording so they are not re-opened.

**Not an extraction defect.** `data/artifacts/preflop/exports/gtopen_node_payloads.captured.json` is
a raw per-node capture straight from the solver - `view.reach` as 169 floats, `view.strategy` as 676
- and two of its six captured nodes are the exact spots under argument. Decoded from the raw capture
and compared against the committed `.gtx.gz`, every pair class agrees to the quantisation step at
both: 77 at 55.66 against 55.66, 22 at 99.67 against 99.67. This oracle was in the tree the whole
time and no stage-4 document had used it.

**Not an index artifact.** 22 sits at GTOpen index 0, so the boundary was ruled out directly. Across
the 86, 32o and 42o at indices 1 and 2 mean 0.0 percent continue, AKs at 167 means 69.3, AA at 168
continues at all 86. And 22 is responsive to the spot rather than pinned: at the 43 spots where it
arrives at full reach it continues above 95 percent at 21 and folds below 5 percent at 21.

### What the investigation did find

Filed as `UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`. **3,925 of the 14,534 cells in the
86-by-169 committed grid - 27.0 percent - are untouched initialisation**, every action within two
points of 1/n. The source card describes the mechanism and nothing acted on it: the payload is
unconditional and reach is the only thing conditioning it. The four-bet node shows it for real
hands, where 77 through 22 arrive at 0.0001 to 0.0019 reach and all sit near a third.

A converter that reads a strategy row without asking whether the class arrives commits a quarter of
every spot as an answer the solver never computed, and a uniform row is not a refusal - it reads as
a considered mixed strategy, which is what makes it worse than a gap. Reach separates them almost
perfectly: 3,922 of the 3,925 sit at or below one percent arriving reach and three sit above.
Stage 4's tests must assert that an unreached class is refused rather than committed; the exact
epsilon or cutoff is `frozen-into-data` and wants Taylor's confirmation before stage 6, but it does
not block the freeze.
