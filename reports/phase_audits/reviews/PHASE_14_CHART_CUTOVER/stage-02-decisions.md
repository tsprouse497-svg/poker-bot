# Stage 2 review: phase 14 decision list

Independent read-only reviewer, 2026-08-23. No file edited, no gate run by the reviewer.

Question the driver printed: *"Is every reversibility class right? A frozen-into-data call filed
as runtime-reversible proceeds on its default and is then written into a committed artifact that
later phases are measured against."*

Scope read: `git diff f6266a6 -- reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md`.

Five blockers. Two were misclassifications, one was an answer that should never have been
pre-filled, one was a question a human could not implement an answer to, and one was a whole
decision the list had left out. The list went from eleven items with five frozen to thirteen with
eight.

## Blocker

- **[resolved] Item 9, the closing prediction's magnitude band, was filed
  `runtime-reversible`.** The item argued it was "a number in a report written before a
  measurement, not a number in the artifact" and then conceded in the next clause that writing it
  afterwards is not reversible. Both cannot hold. Under `runtime-reversible` the loop proceeds on
  the recorded default, so the same agent that runs and interprets the closing measurement would
  also set the bar it is graded against, and `auto_advance: false` surfaces that only at stage 11,
  after the number is known. The pre-registration exists to stop exactly that, and the phase's
  whole conclusion on `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` rests on it. Fixed: reclassified
  `frozen-into-data` and left unanswered.

- **[resolved] Item 9's default was two incompatible bands.** It defined the band first as the
  measured defence delta halved and doubled, in points of defence frequency, and then restated the
  prediction as movement "by somewhere between half and twice the share those combos represent of
  that opener's defending decisions", which is a share of decisions. Different quantities on
  different scales, with no line saying which the measurement would be checked against. A
  pre-registration that reads two ways is worse than none. Fixed: one unit, points of big-blind
  call agreement, with the per-opener numbers written out.

- **[resolved] Item 6's pre-filled answer was a new decision wearing an old ruling's clothes.**
  The item answered itself on the claim that collapsing `jam` into `raise` was already ruled by
  `scripts/convert_preflop_export.py` and the phase 04 schema. The rule does exist and the schema
  does forbid a fifth action kind - but the old ruling was made against a source where the case
  that matters never arose. Measured: the GTO Wizard source has **zero** spots offering an all-in
  and no named raise; this export has **4,257**, which the coordinator reproduced independently
  (33,964 nodes offer neither, 607 offer both). `raise_size_bb` deliberately skips the all-in when
  taking a size and `build_sizings` writes an entry only when a size comes back, so importing the
  rule unchanged commits 4,257 spots carrying a `raise` weight the sizing table cannot price - the
  chart says raise and cannot say how much. Fixed: the answer is blanked and the item now asks the
  real question, price the jam at the stack, commit sizeless and refuse on price, or exclude those
  spots.

  This is also the mechanism failing, not only the judgment. `unanswered_frozen` in
  `scripts/loop_stage.py` treats any non-empty `Answer:` as answered, so a pre-filled
  `frozen-into-data` item never reaches stage 3 and never appears on the derived pause board.
  Filed as `PRE-FILLED-ANSWER-HIDES-AN-ITEM-FROM-THE-PAUSE-BOARD`.

- **[resolved] Item 1's options were families, not predicates, so answering it would not have
  settled anything.** The contract requires the selection rule "expressed as a predicate over an
  export node, not as a spot count and not as a byte budget". The item offered "reach" with no
  threshold, "depth" with no number, and a fourth option in its `Options:` line that the prose
  never defined or costed. Whichever the human picked, the implementer would still choose the
  cutoff, and the cutoff is what decides which spots exist - which is the shortcut the contract
  forbids by name. Fixed: four complete predicates, each with its threshold, its measured spot
  count and its measured size, computed by the coordinator from the export's own `reach_bp` rows
  (reach at 2 percent: 5,626 spots, 10.3 MiB; at 5 percent: 3,296, 6.1 MiB; depth at eight prior
  actions: 4,384, 8.0 MiB; reach at 2 percent with a five-action floor). The reach table and the
  depth histogram are published in the list so the human can see what the thresholds buy.

- **[resolved] The monotonicity comparison rule and its tolerance was a missing
  `frozen-into-data` decision, and the counts the list rested on did not reproduce.** The list
  quoted one shallow violation and 42 deep as if they were properties of the export. Recomputed at
  zero tolerance the same comparison gives 11 shallow and 43 deep on adjacent ranks, and 34 and 73
  comparing every higher pair to every lower one; the quoted pair reproduces only on adjacent
  ranks with a tolerance of roughly one percentage point, which no file stated. Ten of the eleven
  shallow violations are numerical noise at gaps of 0.01 to 0.19 points - the cutoff opens 44 at
  99.91 under 33 at 99.99 - and one is real, the lojack's 44 at 72.81 against 33 at 99.88. Since
  the contract requires the committed cells monotone and decision 2 hand-edits whatever the rule
  names, a zero-tolerance test would send ten noise cells to be rewritten and a hidden tolerance
  would assert a threshold nobody ruled. Fixed: new decision 10 carries the comparison rule and
  the tolerance as `frozen-into-data`, decision 2 now applies to whatever it names, and the
  measured section states that the shallow-versus-deep separation survives every variation while
  the counts do not.

## Non-blocker

- **Item 8's class is right but its cost was understated.** The reason codes are not written into
  `data/artifacts/**`, so the `frozen-into-data` definition does not catch them, but the contract
  republishes the refusal inventory by reason, so a later rename breaks the comparability of a
  committed report and requires editing a frozen test of a completed phase. Reversible at that
  price rather than freely.
- **Item 5 offered an answer the contract does not permit.** Its `Options:` line included
  `carry-reach-per-spot`, where the contract permits only per-cell or a stated reason the schema
  cannot with the entry filed. Fixed: two options, and the prose says why a spot-level summary
  cannot answer the ask.
- **Decisions 4 and 5 share one schema version bump and presented their costs as independent.**
  `ARTIFACT_SCHEMA_VERSION` is 1; the blind structure, the reach field and the empty-sequence call
  rule all land on the same bump. If 4 is answered yes, 5's marginal cost is bytes only, and the
  human should be told. Not fixed in this round; it is a framing note for stage 3 rather than a
  defect in the items.
- **A missing item on which rate the conclusion is read off.**
  `AGREEMENT-RATE-NEEDS-A-DENOMINATOR-POLICY` says explicitly that the gap is a stated rule for
  when each rate is the right denominator, and this phase reads its conclusion off one of the two
  the contract publishes side by side. Added as decision 11, `runtime-reversible`, defaulting to
  the agreement rate because every prior figure in the series was published as that and switching
  denominators mid-series makes the before-and-after meaningless.
- **The frozen-test migration is a judgment call nobody recorded.** The contract requires every
  frozen test asserting against chart contents migrated at stage 4, and whether such a test is
  rewritten, re-pointed or deleted decides the fixture later phases are measured against. Not
  added here because the migration set is not known until decision 1 is ruled; it belongs on stage
  4's own list and the ExecPlan carries it.
- **Numbers confirmed against the repo:** 38,828 nodes; 7,346 bytes per spot and therefore 272 MiB
  for the whole export; 4.4 MiB in `data/artifacts` with 4.0 in `exports/` and 0.25 in the retired
  chart; the five blind-defence deltas; 48.14 = 34.41 + 13.73 against 54.09; the big blind folding
  50.98 percent facing a 2.5 small-blind open from a 54.09 percent range; the button at 40.26
  against 40.56; the four-bet node's cell frequencies and reach; and **17 of 36** retired keys
  colliding with nothing, reproduced exactly as the 15 three-bet keys plus the two small-blind
  ones.
- **Numbers that were wrong and are fixed.** "Twelve points of limping converted to raising" is
  13.73. The four-bet pot arithmetic said hero adds 14.5 into 32 needing 31 percent; the captured
  payload gives 15.0 into 31.5 needing 32.3, and the conclusion that JJ has it comfortably and 76s
  barely survives. "Roughly 2,100 spots" read 15.9 MiB as 15.9 million bytes; it is 2,267 at the
  retired chart's rate and 8,650 filtered. "Opening 33 and 22 outright" is 99.88 and 99.92. And
  the single-orbit option's "1,651 nodes, about 7.9 MiB" could not be reproduced under any stated
  definition, so that option was replaced rather than repaired - the reach and depth options carry
  counts the coordinator computed from the export in this round.

## Alignment

- `DOMINANCE-VIOLATION-COUNT-HAS-NO-DEFINITION` - `SOLVER-CONVERGENCE-IS-NOT-UNIFORM-OVER-THE-TREE`
  publishes 1 and 42 with no comparison rule and no tolerance, which is the same defect decision 12
  correctly files for the limps count, and the repo should require every measured count quoted in
  a contract or decision list to carry the definition it was counted by.
- `DECISION-OPTION-SETS-MUST-BE-COMPLETE-PREDICATES` - an `Options:` line may not offer an answer
  the prose does not define and cost, and a selection-rule option must name its threshold, so that
  a stage 3 ruling is implementable without a second round.
- `PRE-FILLED-ANSWER-HIDES-AN-ITEM-FROM-THE-PAUSE-BOARD` - `unanswered_frozen` and therefore
  `review_queue.py` derive the human ask from an empty `Answer:`, so any `frozen-into-data` item
  written with its own answer is invisible at stage 3 whether or not the pre-fill was justified,
  and the loop needs a distinct marker for "already ruled elsewhere" that still shows on the board.
