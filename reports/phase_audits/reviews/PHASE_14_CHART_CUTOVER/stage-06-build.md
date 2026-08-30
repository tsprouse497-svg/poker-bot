# Phase 14 stage 6 review: the build

Two independent read-only reviewers, one mechanical and one on the poker, neither having written
any of the work and neither having seen the other's notes or the other's remit. The driver's
question for this stage: *does the implementation do the work, or only enough to satisfy the frozen
tests? Name anything that passes for a reason the contract did not intend.*

The diff under review: 30 reviewed paths against `294a2b8`, being the converter and the derived
chart it writes, the committed artifact and its sizing table, the deletion of the retired
`six_max_nl25_100bb.json`, the new report generator and its four validators, the runtime price
draw, and the re-measurement of four completed phases' gate commands that go red once the artifact
is rebuilt.

The coordinator re-measured every blocker independently before acting on it, because a reviewer's
report is not evidence either. Where the coordinator's measurement differs from the reviewer's, the
coordinator's is the one recorded and the difference is stated.

## Blocker

- `[resolved]` **A frozen test could not pass under any implementation, and the fixture was the
  half that was wrong.** `test_a_wrong_artifact_fails_the_command_rather_than_being_rendered[drop-a-spot]`
  builds its corruption by removing a spot from `spots` and `action_weights`, then asserts the
  artifact still imports, because a loader refusal would make the test prove nothing about the
  report's validators. It left the spot's entries in the two other per-spot maps. Two other frozen
  tests require the importer to refuse exactly that: `tests/test_preflop_artifacts.py`'s
  `REJECTIONS` case "reach for an undeclared spot" wants `UNKNOWN_SPOT_WEIGHTS`, and
  `tests/test_chart_arrival_probability.py`'s `IMPOSSIBLE_ARRIVALS` case "a spot the chart does not
  declare" wants a `ValueError`. No implementation satisfies all three, so this was not a build
  failure the implementer could fix in `src/`.
  Cause: a stage-4 cross-lane seam. The lane that authored `test_chart_arrival_probability.py`
  introduced `arrival_ppb`; the lane that wrote this corruption helper never learned of it, and the
  stage-4 review could not see it because the helper only executes once an implementation exists.
  Resolution: Taylor ruled on 2026-08-30 that the repair be authored by a subagent given the
  contract, the two frozen rules and the broken helper and never the implementation, then reviewed
  read-only by a third agent, so the freeze keeps doing its one job. Returning the lane to stage 4
  was rejected as strictly worse, because it unfreezes all 35 files for an agent that has now read
  the implementation. The amendment is 8 insertions inside the `drop-a-spot` branch and moves no
  assertion anywhere in the file; test-function count is 8 before and after; `freeze.lock` was
  re-stamped and still reads 35 files and 892 test functions, unchanged from stage 5's stamp, with
  a one-line hash diff. The mechanical reviewer proved the test retains full power rather than
  reasoning about it: the amended corruption gives rc 1 with no report written, and with
  `validate_spot_count` monkeypatched to a no-op in memory it gives rc 0 and a published report, so
  the test bites on that validator and on nothing else. `pytest_derived_chart` is 112 passed.

- `[resolved]` **B1. The committed chart stacks off 100 big blinds preflop with a range inverted against hand
  strength, at spots that arrive constantly.** Found by the poker reviewer, re-measured by the
  coordinator directly against `six_max_100bb_rakefree.json` and its sizing table rather than
  through the runtime sampler.
  At `t6/d100/BTN/BTN:raise@2.5,SB:raise@7.5`, which arrives once in 40 hands, the artifact prices
  aces at 22.5 with weight 1.0 and never at 100, while KK takes the 100bb jam at 0.978, 44 at 1.0,
  AKo at 0.9995 and AKs at 0.9944. At `t6/d100/BB/BTN:raise@2.5`, the second-busiest spot in the
  chart at once in 6.3 hands, aces three-bet to 7.5 with weight 1.0 and never jam, while AKo jams
  0.6641, JJ 0.6313, 44 0.8844 and 65s 0.8781 of its raise volume. That is risking 100 to win 4.
  The coordinator's own sweep over the 36 spots where any hand can jam: aces jam 0.000 at five
  spots where 44 jams up to 0.979. Those five arrive in 24.0 percent of hands, not the 26.1 this
  note first published: summing `arrival_ppb` over the five double-counts
  `t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5`, which is reached only through
  `t6/d100/BB/BTN:raise@2.5` and is worth 2.06 points on its own. A plain prefix test over the
  spot keys over-corrects in the other direction, to 21.5, because the key omits folds and so
  cannot see that `BTN:raise@2.5,SB:raise@7.5` requires the small blind not to have folded while
  `BB/BTN:raise@2.5` requires that it did. 24.0 is the figure with only the genuinely nested line
  removed.
  A stack-off range that is never aces and is 44 almost every time it holds them is not a strategy;
  it is an unconverged branch.
  Why it is not a tuning knob. The source card records `realization: calibrated`, which resolves
  flops by scaled equity share rather than by playing them, and `add_allin: true`. An all-in
  preflop terminal is therefore the one terminal the model prices exactly, and every named raise is
  priced through a modelled flop, so the model has a standing preference for the branch it can
  price. The solve ran 300 of an allowed 2,000 iterations, which does not compete that preference
  away. Filed as `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`.
  Why decision 6's existing ruling does not cover it. The 2026-08-24 restatement dismisses the
  shove on a spot-level aggregate, that only 2 of the 86 exceed 50 percent, which the poker reviewer
  reproduced exactly. The whole reason the schema is per hand class is that the split varies by
  class, so a spot-level aggregate is precisely the statistic that cannot see AKo at 66 percent
  inside a spot whose overall jam rate is 7.61 percent.

- `[resolved]` **B2. Twelve of the sixteen four-bet-facing spots fold TT and 99 outright while calling 76s and
  87s.** At `t6/d100/HJ/LJ:raise@2.5,HJ:raise@7.5,LJ:raise@22.5` hero is in position, adding 15 into
  31.5 and needing 32.3 percent, and folds JJ 97.2, TT 99.9, 99 100.0 and KJs 100.0 while calling
  76s 99.6 and 87s 93.6. The same shape holds at `CO/HJ`, `BTN/LJ`, `CO/LJ`, `SB/LJ|HJ|CO` and
  `BB/LJ|HJ`. The decision record names this node and ruled it ship-as-solved, so the finding is
  not that the node is new. The finding is that the same document justifies committing the 86 by
  saying the kept set "is the part the independent poker review said it would trust", naming the
  blind-versus-blind skeleton, the big blind closing, and the three-bet, four-bet and five-bet
  continuations. Those continuations are where the poker is worst, so the endorsement the ruling
  rests on does not survive being measured.

- `[resolved]` **B3. Strict rank-dominance inversions of 20 points or more in 42 of the 86 spots, including the
  only opening range the bot owns.** The poker reviewer reported 135 across 44 spots. The
  coordinator recounted under a stricter relation, requiring the same top card, the same
  suitedness, and kickers exactly one rank apart, plus adjacent pairs, so that no connectivity or
  gap difference can be confounded with the inversion: **131** such inversions across 42 spots.
  Excluding the wheel-ace family, where preferring A5 over A6 is a real and well-known solver
  result rather than a defect, **111 inversions across 42 of the 86 spots**. That correction is
  worth recording, because two of the five headline pairs the reviewer listed do not survive it:
  K5o over K4o is the correct ordering rather than an inversion, and 87o over 97o trades a rank for
  connectedness and is not strictly dominated either.
  What survives is enough. In `t6/d100/SB/rfi`, the one opening range the chart holds, played once
  in 3.6 hands: T3s opens 99.87 percent and T4s opens 9.72; 83s opens 68.53 and 84s opens 28.05. In
  `t6/d100/BB/SB:raise@2.5`, once in 6.7 hands, T5s plays 99.7 and T6s plays 14.5. In
  `t6/d100/BB/LJ:raise@2.5`, Q6s plays 98.6 and Q7s plays 0.2.
  Why Taylor's 2026-08-24 ruling on per-cell violations does not cover these. That ruling accepted
  violations as the solver's considered answer among near-indifferent hands, and it was made on a
  0.07-versus-99.94 example before this measurement existed over the shipped 86. Nothing in the
  phase establishes indifference: the solve target is a best-response gap summed over the whole
  tree, 0.0062bb, which by the decision list's own argument constrains nothing at a node carrying
  little mass. A human drilling the only opening range the bot has is taught to open T3s and fold
  T4s.

### How B1 to B3 were resolved, 2026-08-30

All three were open when this note was first written, because they are properties of the source
solve rather than of anything stage 6 wrote. They are marked resolved by a ruling that re-sources
the phase, not by a repair, and the measurements below are what the ruling was made on. Every one
was taken by the coordinator against a live GTOpen at the pinned commit `4aee435`, using the
prebuilt binary with no rebuild, so it is the same engine that produced the committed export. None
of it wrote anything into the repo.

**First Taylor ruled the full cap, and the measurement refused it.** The committed solve stopped at
300 of an allowed 2,000 iterations because it beat a tree-summed gap target of 0.01, which is the
statistic phase 14's own decision list argues constrains nothing at a low-mass node. Running the
budget out gives `gap_total` 0.0020266 at 2,000 iterations against the committed 0.0062379, in 201
seconds. At `t6/d100/BB/BTN:raise@2.5` that is close to a repair on its own: 44 goes from jamming
88.4 percent to calling 99.9, and 65s from jamming 87.8 to calling 99.6. At the four-bet node it
changes nothing at all. A 10,000-iteration diagnostic then settled it: `gap_total` only reaches
0.0018446, nine percent better for five times the work, and 44 still jams 1.000 at
`t6/d100/BTN/BTN:raise@2.5,SB:raise@7.5`, bit for bit, sitting between 55 at 0.121 and 33 at 0.000.
Convergence has plateaued, so B1 at the four-bet nodes is structural and not noise.

**The mechanism is one config flag, found by reading the solver.** In
`crates/solver/src/preflop/mod.rs:2204`, `add_allin: true` pushes `cfg.stack` onto the raise menu at
every node where a raise is legal, with no reference to the pot, which is why the big blind can shove
100 to win 4. The separate `allin_threshold` at `:2219` only snaps a raise already landing at or above
67bb up to the full stack. The units were checked rather than assumed: the server's `SpotRequest`
documents the threshold as a percent and divides by 100, but that is the postflop endpoint, and
`/api/preflop/spot` deserialises straight into `PreflopConfig`, whose validator at `:2115` requires
`(0, 1]`. The ruled 0.67 is correct and means 67 percent.

**So the flag was tested, and it is the repair.** With `add_allin: false` at 2,000 iterations,
`gap_total` is 0.00014807: 13.7 times better than the full cap with the flag on, and 42 times better
than the committed solve. B1 is gone. At the four-bet node AA, KK, QQ and AKs four-bet to 22.5 at
1.000, JJ mixes 0.544, and TT, 99, 55, 44, 33 and 65s all call. At the big blind node everything 55
and up three-bets to 7.5 and 44, 33 and 65s call. Nothing jams anywhere it should not. Five-bet jams
survive exactly as the code predicts, because the 3.0 multiplier puts the five-bet at 67.5bb and the
threshold snaps it: at `SB` facing the button's four-bet the menu is Fold / Call 22.5 / All-in 100,
with AA and KK jamming 1.000, QQ 0.986 and AKo 0.719. The tree carries 33,969 action nodes rather
than 38,828. B2 is resolved by the same measurement, since the four-bet-facing spots it names are
the ones re-solved above.

**B3 is corrected as well as resolved, and the correction is against this note's own first draft.**
Before crediting it the coordinator dumped the full 169-cell SB opening grid under the new config to
rule out a hand-index artifact, since a wrong index would scramble a range rather than dent it. The
grid is coherent: every pair at 100 percent, every suited broadway at 100, and a clean fold boundary
through the offsuit corner. What remains is three isolated single-cell dips in 169 - T4s at 0.2
percent between T5s at 100 and T3s at 99.8, 93s at 6.9 between 94s and 92s at 100, and 84s at 12.9
between 85s at 100 and 83s at 97.7 - at a binary node where near-threshold hands go pure. That is
materially narrower than this note's first draft, which reported 111 inversions across 42 of 86
spots measured on the committed chart, and narrower again than the poker reviewer's 135 across 44.
It is also the case `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` already describes. B3 is carried
into the re-sourced phase as a measurement to retake rather than as a defect the ruling repairs.

**Taylor's ruling, 2026-08-30: adopt `add_allin: false` and restart phase 14.** `add_allin` and the
solve target both live in `RULED_CONFIG`, so both are frozen-into-data and the amendment is a
`contract-update` task rather than anything this one may do. The census moving off 38,828 invalidates
26 assertion sites across six frozen test files, together with the committed 86, both exclusion
counts, the corpus refusal figures, `repo_facts` and `docs/CORPUS_COMPARISON_LIMITS.md`. The stage-6
build recorded in this note is therefore superseded rather than advanced, and the note stays as the
record of what the reviews found and what it cost to establish.

The non-blockers and alignment items below stand. Most of them are about the repo rather than about
the export, and the three that are about the export -
`SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`,
`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT` and
`ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE` - are to be re-measured against the new
solve rather than assumed to have moved with it.

## Non-blocker

- **Three independent implementations of "the named, non-all-in open price", each with a different
  notion of the stack.** `data_pipeline/comparison.py` filters on `RULED_CONFIG["stack"]`,
  `scripts/repo_facts.py` on `min(artifact.stack_depth_bb)`, `scripts/generate_preflop_strategy_report.py`
  on `FULL_DEPTH_BB`. All three agree today because there is one depth and one export, all three
  feed separately published figures, and nothing makes them agree after a second artifact. All
  three files are in `approved_scope`, so one helper with three callers would cost nothing here.
- **`OPEN_SIZE_SPOTS` still spells a seat by name.** `comparison.py` pins `("t6/d100/SB/rfi",)`
  where `repo_facts._solved_open_bb` derives the same set from `library.spot_keys()`. A chart
  holding a second opening range makes `repo_facts` raise correctly while the corpus comparison
  silently grades the whole sample against one seat's price. The comment above the constant says
  spelling a seat by name is what broke that section last time.
- **The artifact describes its own census in prose and nothing checks it.** `chart_provenance.py`
  bakes "86", "38,828" and "38,742" into `ARTIFACT_NOTES`, which ships inside the committed
  artifact; the only check asserts those same string literals appear as substrings, so both sides
  read one constant. The frozen `COMMITTED_SPOTS = 86` in three test files is what actually
  protects this today.
- **Big blind flat-calling is nearly opener-invariant.** Combo-weighted over the full 1,326: 21.01
  vs LJ, 21.89 vs HJ, 24.07 vs CO, 22.64 vs BTN, 22.59 vs SB, a 3-point band against openers
  ranging from 19.1 to 54.1 percent wide, while only the three-bet half moves. Real solutions widen
  the flat sharply against late position. Same root cause as B1, measured on the passive side.
- **Defence against the button moves the wrong way against the external reference.** Against the
  GTO Wizard expectations the rake-free chart defends wider against LJ (+4.65), HJ (+3.72), CO
  (+2.64) and SB (+6.14) and tighter against the button (36.757 vs 39.43, -2.67). Removing rake
  cannot tighten defence. The report prints the row; nothing names it as the anomaly it is, and it
  lands on the same node as B1's AKo shove.
- **Eight committed spots have arrival probability exactly zero**, all of them open-jam
  continuations whose export frequency is 0.00000000. Fifteen more arrive rarer than one in a
  million, 47 of 86 rarer than one in a thousand. Those ranges have no basis and nobody will drill
  them.
- **The refusal experience after the cutover.** Refusals go from 9.2 to 85.7 percent of Pluribus
  decisions and 9.6 to 82.4 percent of human decisions; the four most-refused keys are the four
  retired opening ranges. In the simulator a `StrategyRefusal` ends the hand, so a driller loses
  roughly five hands in six at the first hero decision.
- **Checked and found sound, recorded so the absence of a finding is not read as an absent check.**
  The mixed-strategy and price draws are correct: `_roll` is sha256-derived and process-stable,
  `collapse` is a cumulative walk normalised by the positive weights so it reproduces artifact
  frequencies rather than a plurality rule, and over 200,000 seeds per cell the realized frequencies
  match the committed ones to within 0.0005. The seed carries `hand_id`, so a mixed cell does not
  freeze for a session, and the price draw's `price|` tag decorrelates it from the action draw,
  which matters because `collapse` returns the last entry on a high roll and a shared roll would
  have made every raise take the top price. Separately, the mechanical reviewer re-derived the whole
  census from the export with its own predicate and reproduced every published figure: 38,828 action
  nodes, 110 and 5,472 for the two clauses alone, 86 committed, 33,356 and 5,386 for the two
  exclusion codes, 7,112 cells, and corpus refusals 290 to 2,529. It also verified the contract's
  sharpest criterion by scoring the corpus twice and diffing row by row: all 2,259 decisions that
  move from answered to refused reach one of the 15 named spots, zero outside them. `walk_export`
  takes `exported_nodes` from the source card rather than from `len(export.nodes)`, so
  `validate_census` is not circular, and the completed phases were re-measured rather than re-pinned,
  with `vocabulary_measures.py` deleting the v1-checksum check rather than re-pinning it on the
  ground that a check which cannot pass is not evidence.

## Alignment

- A calibrated-realization solve prices the all-in terminal exactly and every named raise through a
  model, giving it a standing bias toward the jam that no predicate over the tree removes.
  `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`
- The verification gate has no measure that can fail on a bad range; the only committed dominance
  check is a transposition canary. `NO-GATE-MEASURE-CAN-FAIL-ON-A-BAD-RANGE`
- Per-node convergence is unmeasured and ungated, and a tree-summed best-response gap constrains
  nothing at a low-mass node. `PER-NODE-CONVERGENCE-IS-UNMEASURED-AND-UNGATED`
- Only one non-all-in price exists per betting round in the solved tree, so the per-hand-class
  sizing schema, which is the right shape, is currently recording a raise-or-shove caricature.
  `ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE`
- The flat-call half of blind defence does not respond to opener width, which is the realization
  model showing through on the passive side. `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`
- The derivation reason exists in the converter and the report and never reaches the answer the
  human sees, so two very different refusals read identically at the table.
  `A-REFUSAL-CANNOT-TELL-THE-HUMAN-WHY`
- Phase 12's completed contract asserts a bijection and a checksum that phase 14 deliberately
  removed, and nothing in the gate detects a completed contract asserting a criterion its own
  module no longer implements. `PHASE-12-CONTRACT-ASSERTS-A-REMOVED-BIJECTION`
- Phase 14's own contract states a pair-band and suited-row monotonicity gate that did not ship,
  and publishes a spot-gain figure its own committed report contradicts.
  `PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP`
- "The named open price" has three implementations against three notions of the stack, and
  `OPEN_SIZE_SPOTS` spells a seat by name. `THE-NAMED-OPEN-PRICE-HAS-THREE-IMPLEMENTATIONS`
- The artifact's own census notes are literals that only a substring test reads.
  `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS`
- `repo_facts` watches two of `CORPUS_COMPARISON_LIMITS.md`'s six live numbers.
  `FACT-DRIFT-WATCHES-TWO-OF-A-DOCUMENTS-SIX-LIVE-NUMBERS`
