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

# Round 3, 2026-08-31: poker review of the decision-list re-cut

Independent read-only reviewer, on the uncommitted change to
`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md` that appends a dated disposition
to each of the 21 items. I wrote none of it and none of the rulings behind it. A separate mechanical
reviewer is checking whether the figures reproduce and whether anything above an appended block was
edited; none of that is repeated here. The questions here are whether the five movers are the right
five, whether the amendments describe what the committed chart will actually do at the table, whether
any disposition takes a decision that is Taylor's, and whether anything the re-cut asserts about
GTOpen's own behaviour is false.

**What I read and what I measured.** Both contracts, the whole decision list, rounds 7 and 10 to 16 of
`stage-01-contract.md`, `stage-02-decisions.md` as it stood, and the static-build evidence beside it.
For the source claims I read GTOpen at the pinned `4aee435` and computed over
`cache/realization_fit.json` with my own code: no repo code run, nothing written outside this note,
nothing in `~/projects/gtopen` touched. Confirmed there and reported here so the re-cut's citations are
not taken on trust: `mod.rs:1122` really does say the fit "was measured as net-of-rake EV over GROSS
pot, so use the gross pot and skip the rake deduction", `AGENTS.md:49` really does say calibrated
"embeds its training rake", `class_r` at `mod.rs:344` really is `class_base[k] x pos_weight` with no
SPR term, the module header at `mod.rs:7` really says "R = 1 when all-in, i.e. those terminals are
exact", `meta.r2` is 0.1885, `rho_cells` carries `f_srp`, `i_srp`, `f_3bp`, `i_3bp` and `limp` and
nothing else, `spr_edges` starts at 2.5, `class_base` runs 0.3632 to 1.2823, and `m5_spots/` contains
no `_4bet` study line of any kind. The pin item 7 names also checks out: `294a2b8` is exactly
`a386c77^`, the retired chart is present there and absent at `a386c77`, and `294a2b8` is an ancestor
of this branch. Item 3's training-rake finding and item 17's sampling-gap diagnosis are both sound and
correctly sourced.

**The five movers are the right five.** Items 7, 9, 11, 12 and 15 are each a claim that cannot be
evaluated without the 499 hands, and nothing that stays is. I checked the other sixteen one at a time
against decision 21's own seam rather than against the re-cut's list: 1, 2, 5, 6, 10, 13 and 14 judge
or shape the file, 3, 4, 8, 16, 17, 18 and 19 record what its source does, and 20 and 21 are the
rulings. Item 12's split is right and is the one I expected to be wrong: the schema half, that no spot
with an empty `action_sequence` carries a call weight, is a rule about what the artifact may hold and
stays; the count of limped decision points is a property of the corpus and goes. Two things the movers
leave behind are in the non-blockers below.

## Blocker

- `[resolved]` **Item 10 settles by prose the one frozen question the contract deliberately left open, and it is
  the wrong half of the gate that ends up gating.** The amendment writes "the aggregate group form
  gated" and "the gate is written at the ruled one-point tolerance and it **gates**", and then reports
  that the suited-row ladder on the only available proxy misses by 23.19 points while a transposition
  makes it *cleaner* and a flat line is its optimum. Those two sentences cannot both be the record's to
  write. What Taylor ruled on 2026-08-24 is a per-cell relation, "a suited hand at least as often as
  the offsuit hand of the same ranks", at one point, and then that the relations are measured per cell
  and gated on aggregates. He did not rule that a ladder over suited rows keyed by high card is that
  relation's aggregate form, and round 14 of the stage-01 note found in terms that it is not: "'suited
  at least as often as the offsuit twin' has no gated form at all, the suited-row ladder is a different
  assertion". The re-cut does not carry that finding. It carries the symptom - the gate rewards a
  transposed index - and then rules that it gates anyway. That ruling is `frozen-into-data` in the
  strict sense the list uses: a stage-4 test asserts it and stage 5 freezes it, before stage 6 can see
  the real number, and item 10's own words are that changing it afterwards is "a task rather than an
  edit". It also decides the phase's outcome, because on the proxy the artifact Taylor ruled to commit
  fails and the artifact he rejected passes. **Decision 22 is owed**, `frozen-into-data`, `Answer: []`,
  and its question is not the tolerance:
  *Now that the suited-row aggregate has been measured twice as scoring the wrong index mapping better
  than the right one - 2,007 nodes against 818 over the 5,626, and cleaner under a full transposition
  over the committed keys - does it gate the committed artifact, or is it published beside the per-cell
  table for a human?*
  Options, each stated as what it ships:
  `gate-both-ladders-at-one-point` - what the re-cut writes. The phase halts at stage 6 on a 23-point
  miss of a relation nobody ruled, and the gate that halts it is one whose optimum is a chart that
  folds nothing.
  `gate-the-pair-band-ladder-only-and-publish-the-suited-row` - keeps the only aggregate form ever
  measured clean (the two-band pair aggregate, over the full-reach nodes) and demotes the anti-diagnostic
  one to a printed number beside the per-cell dominance table decision 10 already publishes.
  `gate-neither-and-publish-both` - makes the range check entirely a human read, consistent with
  decision 2's ship-as-solved and with the defence-level and four-bet-composition reads the contract
  already buys.
  `gate-both-and-halt-if-it-fails` - the re-cut's position, ruled explicitly rather than assumed, so the
  halt is a choice Taylor made rather than one the packet made for him.
  The tolerance itself is not in question and must not be reopened as one: one point is his and item
  10 is right to withdraw the licence to re-derive it. What is in question is which relations that
  tolerance is applied to. One sequencing note, because it decides when this is asked: the ruled
  artifact has not been derived, every figure in item 10 is `a386c77` read as a proxy, and the pipeline
  re-runs in minutes. Derive it and measure the gate on the real file *before* stage 4 authors the gate,
  so the ruling is taken on the artifact rather than on a stand-in - item 10's own rule that no ruling
  may rest on an unlabelled proxy applies to this one too.

- `[resolved]` **Item 3's reframing rescues the pair-versus-connector reading and then extends the rescue to
  ladders it does not cover, deleting the packet's own explanation for a defect that ships.** The
  reframing is right where it is aimed. `R` is realized EV over raw equity, 76s at 1.1333 above JJ at
  0.7493 is what realization means, and the U-shape across the whole pair ladder is real poker: aces
  and kings are made hands that collect, deuces through fives are set-miners with implied odds, and
  nines through jacks are bluff-catchers that collect least. I reproduce that shape exactly - 22
  0.9102, 33 0.8073, 44 0.7424, 55 0.7672, 66 0.8041, 77 0.7613, 88 0.7514, 99 and TT 0.7196, JJ
  0.7493, QQ 0.8556, KK 1.0473, AA 1.2823. But the sentence the re-cut lands on is that the only defect
  is "applying that table where there is almost no postflop play", and that is not what the table says.
  Sixteen suited rows carry a hand whose *lower* kicker is priced above its higher one, including the
  three this packet has already quoted as chart inversions: J5s 0.8105 over J6s 0.5880, T5s 0.7601 over
  T6s 0.5847, Q6s 0.7899 over Q7s 0.7280. There is no realization story for those. A jack-six suited
  cannot keep a smaller share of its equity than a jack-five suited; same suit, same top card, strictly
  better kicker, and the gaps run to 22 points. A5s over A6s is the one that is real, and the fitter
  says why ("wheel aces unchained"). The rest is a fit at `r2` 0.1885 patched to monotonicity only
  along a hand-picked list, which is `fit_phase_c5.py`'s own description of itself. The same is true
  inside the low pairs, where 33 at 0.8073 sits above both 44 and 55 and no set-mining argument orders
  it that way. This matters at the table and not only in the prose: item 14 records the committed chart
  playing `J6s 0.000 beside J5s 1.000` and `Q7s 0.000 beside Q6s 1.000`, and item 10's failing
  suited-row gate is very plausibly this same noise showing up in aggregate. A student handed a chart
  that folds jack-six suited and calls jack-five suited learns a false ladder, and after this
  reframing the packet no longer contains the sentence that explains why it happens. Fix additively:
  keep the reframing, and add that the table's non-monotonicity splits in two - the pair-versus-connector
  and pair-U-shape orderings are correct realization and were misread, while the within-row kicker
  ladders and the low-pair zigzag are fit noise at `r2` 0.1885 that no SPR argument removes and that
  reaches the committed cells.

- `[resolved]` **Item 6 reintroduces, unqualified, the sentence round 14 opened a blocker on, and then points the
  jam canary away from the only committed cells that can still show the defect.** The amendment says
  "`100.0` is not in hero's price menu anywhere" and "no committed spot can jam". Both are true of hero
  *initiating* a raise and neither is true of what the chart tells a player to do. Fifteen of the
  committed 36 face a five-bet jam with a call/fold menu, and at them the chart puts the last 77.5bb
  in. Round 14 found exactly this in the contract draft, the contract was corrected to read "Hero can
  never initiate the last raise, and the chart still answers 15 call-offs for a full stack", and the
  decision list is now the document that carries the version that was rejected. A reader of the packet
  alone concludes the bot never stacks off preflop. It does, fifteen times, for a hundred blinds.
  The second half is the more useful finding. The re-cut retires the jam-inversion canary from the
  artifact as vacuous and retargets it at the export. But the defect that canary exists to catch - a
  low pair getting a hundred blinds in where aces do not - is fully expressible over the committed 36
  in the *calling* direction, and those fifteen call-off spots are the cleanest cells in the whole
  chart: round 11 measured them at zero model-priced mass, every leaf a fold or an all-in showdown, so
  an inversion there could not be blamed on the realization model and would be a pure converter or
  solver defect. Retargeting the canary at the export trades a check that would bite on the shipped
  file for one that bites on a file nobody plays. Fix additively: correct the two sentences to say hero
  never initiates the last raise while the chart still answers fifteen full-stack call-offs, and state
  the canary over the committed call-offs - at each of the fifteen, no lower pair or weaker class calls
  off more than aces do - keeping the export version as well if it is wanted.

## Non-blocker

- **Item 19's amendment gets `static`'s mechanism backwards on the formula it cites, and asserts
  something decision 20's own measurement contradicts.** It says static's "positional term saturates at
  SPR 8 and it has no per-class term, so it has nothing to get backwards at a four-bet pot's SPR 1.67
  and approaches raw realization at a single-raised pot's SPR 20". GTOpen's `TODO.md:44` gives the term
  as `R = 1 + 0.16 x pos_frac x min(SPR,8)/8` with `pos_frac` in `[-0.5, +0.5]`, so the departure from
  raw *grows* with SPR and is at its maximum, about eight percent, everywhere above SPR 8. Static is
  near raw at SPR 1.67 and furthest from it at SPR 20, which is the opposite of what the amendment
  says. Decision 19's own body states it correctly a few lines earlier ("about plus or minus 8 percent,
  growing with SPR and saturating at 8"), so the amendment contradicts the item it is amending. The
  conclusion survives for a different and simpler reason: static is class-blind at *every* SPR, so
  seventy-two offsuit gets the same realization weight as a suited connector instead of calibrated's
  0.4326, and a big blind closing for 1.5 to win 4 then defends everything. The reason matters, because
  the SPR framing makes static look like a targeted failure confined to single-raised pots, and
  decision 20's own third bullet records static's four-bet ranges as broken too - AQs five-betting the
  full stack at 0.9998 while KK, QQ, AKs and AKo all flat. "Nothing to get backwards at SPR 1.67" is
  not what that measurement shows. Neither model produces a four-bet-facing range fit to show anyone,
  which is round 14's finding and the honest form of the sentence.
- **The bound on `raw` is argued rather than measured, and the sign of the argument is wrong.** Item
  19's amendment closes the option space with "`raw` is `static` with the positional term removed as
  well" and decision 20 concludes it "cannot be better on that axis". Removing a *positive* positional
  term makes raw tighter, not looser, for the player who is in position postflop - which is the big
  blind closing against an open, the exact seat the calling-station failure lives in. Under static that
  seat gets `R` up to 1.08 at SPR 20; under raw it gets 1.00. Raw is also the only one of the three
  that satisfies the module header's own boundary at a four-bet pot's SPR 1.67. It is very unlikely to
  be shippable - realizing 100 percent of raw equity still defends far too wide - but nobody solved it,
  and the packet should say the option was bounded by argument rather than measured. Not a reason to
  reopen decision 20.
- **Item 10 misdates the paragraph it withdraws.** The sentence licensing a re-derived tolerance - "the
  tolerance is therefore calibrated against data this phase does not ship and must be re-derived from
  the re-sourced chart before it is frozen" - is in the 2026-08-30 supersession block, not in anything
  the item carried on 2026-08-24. The 2026-08-24 correction says the opposite, that the phase halts
  rather than freeze a gate it has not seen pass. An amendment has to name precisely what it withdraws
  or the snapshot stops being readable.
- **Item 7's pin is correct and phase 14 needs it too, which the item does not say.** `294a2b8` is
  right and phase 17 is right to read from it. But two of phase 14's own criteria are measurements over
  the retired chart taken after phase 14 deletes it: that 31 of its 36 keys collide with nothing the
  new artifact declares while 5 collide exactly, and that it limps 13.73 percent from the small blind
  across 103 classes. Both are in the contract and neither is a corpus claim. As written, an
  implementer reading item 7 learns the pin exists for phase 17 and has nothing telling him where phase
  14's own two figures are recomputed from. One clause.
- **The cell-purity statistic moves with item 15 and it is a property of the file, not of the
  corpus.** "2.209 nonzero actions per cell at 21.0 percent pure" against "1.323 at 73.0" needs no hand
  history to compute; it is read off the chart alone, and it is the single number that says whether the
  solve converged to answers or to menus. On decision 21's own seam - a claim about a file against a
  claim about poker made by comparing that file to 499 hands - it stays. Phase 14's contract has no
  purity criterion, so as the re-cut stands the phase commits the ranges every later phase is measured
  against without publishing how mixed its cells are, and phase 17 publishes it only as context for a
  rate. The report already prints per-cell dominance and arriving reach; purity belongs beside them.
- **Item 3 stays and its opening rationale carries a stale corpus figure forward.** "The big blind
  holds 58 of the 89 human call disagreements" is what put this item on the list, and phase 17's
  contract records that the repo now computes 42 and 14. Item 3's amendment restates its measurement
  and its dispositions but says nothing about that, so the one number a reader takes from the item's
  first paragraph is one the repo has already contradicted. Item 15 and item 9 both got a "these
  figures do not describe the committed chart" line; this deserves the same.
- **"The module's own header says `R` should be near 1" is an extrapolation, not a quotation.** The
  header says `R = 1` when all-in, and those terminals are exact. Extending that to a flop at SPR 1.67
  is a poker inference and a good one - with 1.67 pots left behind there is very little play to
  realize - but it is the reviewer's inference and not the source's statement. Decision 20 states it
  more carefully ("the flop is nearly all-in and the correct R is close to 1"); item 3 should borrow
  that wording.

## Alignment

- `SUPERSEDED-FROZEN-ITEM-STILL-PARSES-AS-ANSWERED` - item 17 needed a whole appended paragraph whose
  only job is to stop a reader taking its `Answer: [extend-the-fit-to-four-bet-pots]` line for
  scheduled work, and item 18 needed one to say a withdrawn item is still withdrawn. The list has no
  machine-readable way to mark a `frozen-into-data` item superseded or withdrawn, so the only
  instrument is prose that a bottom-up reader misses and that `loop_stage.py` cannot see at all. This
  is the mirror of `PRE-FILLED-ANSWER-HIDES-AN-ITEM-FROM-THE-PAUSE-BOARD`, which round 1 of this note
  filed: there a pre-filled answer hid a live question, here a live-looking answer advertises dead
  work. A status field the driver reads would retire both.
- `OPTION-SHEETS-SHOULD-SAY-WHICH-OPTIONS-WERE-MEASURED` - decision 20's option space was closed with
  three models "measured or bounded", and one of the three was bounded by an argument this note finds
  sign-wrong. An option sheet put to a human should mark each option as measured, bounded by argument,
  or unexamined, so a ruling can tell which of its rejections rest on a number. Round 12 already asked
  option sheets to state what each option removes from the artifact and round 14 asked them to state
  the stake; this is the third property in the same family and they should be filed as one rule.
- `A-DECISION-LIST-RE-CUT-FOUR-TIMES-IS-A-CONTRACT-REWRITE-IN-DISGUISE` - five of the twenty-one items
  now carry more amendment than ruling, and three of them have been superseded twice on premises that
  evaporated rather than on arguments that lost. The append-only rule is right and must not change, but
  `AGENTS.md` has a remedy for exactly this shape on the contract side - a rewrite that folds
  amendments into the criteria they amend, taken as its own task - and no equivalent for a decision
  list. The right time for that fold is when the phase closes and the list becomes history, not
  mid-phase, and the repo should say so rather than leave each session to decide.

# Round 4, 2026-08-31: mechanical review of the decision-list re-cut

Commissioned as the round-2 mechanical review of the same working-tree change round 3 read as poker.
It is numbered 4 because round 3 was already in this file when it was written and this note is
appended rather than inserted; round 1 and round 3 are untouched. Independent read-only reviewer,
wrote none of the re-cut and none of the rulings behind it. No file edited but this one, no
`run_verify.py`, no `check_gate_bite.py`, no bare `pytest`, no write-side git command, nothing in
`~/projects/gtopen` modified. `verification/.mutation_in_progress` is absent.

Round 3 read whether the dispositions are right about poker. This note reads whether the paperwork is
sound: whether the change is append-only, whether every appended figure reproduces from a source
rather than from another document, and whether any item is left asserting something the rulings have
made false. Round 3's three blockers are not restated here; I agree with them on the evidence I
checked and one of its non-blockers is confirmed below.

**The change is append-only, and mechanically so.** The diff is 373 insertions and zero deletions -
the single line in it beginning with a minus is the `--- a/` header. It lands as 24 blocks: three
banners in the front matter and one disposition at the foot of each of the 21 items. Every item block
sits immediately before the next `## ` heading with one blank line between, so nothing was inserted
mid-item and nothing above an appended block was reworded. No `Reversibility:`, `Options:` or
`Answer:` line was added or changed, so `loop_stage.py`'s `decision_items` parse is unchanged: 21
items, each declaring a class, each with a non-empty answer, `unanswered_frozen` empty.

**The reversibility recount is exactly right.** Reading the `Reversibility:` lines rather than the
banner: frozen-into-data 1 to 6, 9, 10, 14, 16 to 21, which is fifteen; runtime-reversible 7, 8, 11,
12, 13, 15, which is six. The superseded sentence it corrects also reproduces - over items 1 to 13 as
the list stood on 2026-08-23, eight are frozen. Item 9 is correctly frozen and correctly carries its
own reclassification to phase 17; the four runtime movers (7, 11, 12, 15) each govern what a report
prints rather than what a file holds, and item 13 is a packaging choice that a re-derivation reverses.
Item 8 is the one class worth a sentence and it is in the non-blockers.

**What I recomputed, from sources rather than from the prose.**

- Census. `calibrated-build-contamination.json` gives `counts.action_nodes` 33,969 and 51 committed
  spots on the ruled config; the derived-chart report gives 29,104 `source-misprices-multiway` and
  4,814 `outside-selection-rule`. 36 + 15 + 29,104 + 4,814 = 33,969, and the two exclusion counts are
  structural properties of the tree, which the realization field does not move, so carrying them from
  the `static` build to the ruled one is sound.
- The committed 36 and their menus, from the contamination walk's own `per_spot` rows rather than from
  any summary. One spot with no prior raise (`t6/d100/SB/rfi`), five facing one, fifteen facing two,
  and fifteen facing a five-bet jam; the fifteen withheld are exactly the `faces_four_bet` rows. So the
  menus are 20 call/fold/raise, 15 call/fold and 1 fold/raise, 21 spots carry a raise price and 15 do
  not, hero's distinct prices are exactly 2.5, 7.5 and 22.5, and 100.0 appears only in the villain's
  history at the jam-facing spots and in hero's own menu only at the fifteen that are withheld. Item
  6's amendment is right in every count.
- The contamination table. Kept-36 arrival-weighted split 0.716882 fold-win, 0.005472 all-in showdown,
  0.263877 single-raised or three-bet flop terminal, 0.013769 four-bet flop terminal. So 1.38 percent
  of total value and 1.377 / (26.388 + 1.377) = 4.96 percent of the mass the model prices. Both figures
  the ruling rests on reproduce.
- The group-gate figures item 10 reports - calibrated 4 pair inversions worst 7.40 and 3 suited-row
  worst 23.19, `static` 8 pair inversions worst 0.06 and none suited-row, a fold-nothing chart 0 and 0 -
  are round 14's, taken over the committed keys, and item 10 carries the `superseded_chart_a386c77.json`
  proxy caveat that round 14 attaches to them. The item does not overstate what has been measured.
- Decision 7's pin. `294a2b8` is exactly `a386c77^`, `data/artifacts/preflop/six_max_nl25_100bb.json`
  is present in its tree and absent at `a386c77`, and `294a2b8` is an ancestor of this branch. See the
  non-blocker below for the part of the sentence that is narrower than it reads.
- `RULED_CONFIG` reads `realization: "calibrated"` and `add_allin: False`, with `allin_threshold: 0.67`
  and `max_raises: 4`, which is what makes a fifth raise at 67.5bb snap to the stack.
- GTOpen, read at `4aee435` with a clean working tree. `class_base` via the engine's own index
  (`preflop/equity.rs` `class_parts`): 76s 1.13325 and JJ 0.74935, and item 16's whole list - AA 1.28227,
  KK 1.04726, QQ 0.85557, TT and 99 0.71956, 22 0.91023, JTs 1.06415, 87s 1.01619, 72o 0.43256, J6s
  0.58801 under J5s 0.81051, T6s 0.58468 under T5s 0.76011, Q7s 0.72798 under Q6s 0.78992. `meta.r2`
  0.1885, `n_obs` 153,321, `n_3bp_spots` 12, `rho_cells` exactly `f_srp`/`i_srp`/`f_3bp`/`i_3bp`/`limp`,
  `spr_edges` starting at 2.5, `class_base` running 0.36316 to 1.28227, `class_r` at `mod.rs:344`
  carrying no SPR term, `AGENTS.md:49` on the embedded training rake.
- Every backlog id cited in the appended text exists in `backlog.yml`: all twelve of them.
- The two contracts. Phase 14 is 284 lines and phase 17 is 158, phase 17 is `future` in
  `phase_status.yml` at `docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md` with `depends_on: ["14"]` and
  `auto_advance: false` in `verification/loop_policy.yml`. Every criterion an appended block attributes
  to a contract is in that contract, several word for word: the vacuous-check label and the export-
  retargeted jam canary (phase 14, lines 126 to 127 and 138 to 139), the gate definition pinned as data
  (159 to 160), "either writes it or records why it waits, by id" (238), the four-bet composition and
  defence-level human reads (254), the pre-registration (phase 17, 51 to 52), the permissive rate never
  alone (59 to 62), the limp count with its definition (95), and the pin decision 7 names (98 to 99).

## Blocker

- `[resolved]` **Item 1 still tells the closing measurement to publish a spot-count that the committed 36 falsifies,
  and the re-cut's amendment corrects only the corpus half of the same paragraph.** The 2026-08-25
  block says "only **22 of the 36 survive and 14 do not**", "the cutover gains 64 spots and gives up 14,
  rather than gaining 50 and giving up none", and closes "the closing measurement states it as one: 14
  retired spots refused, 64 gained, opening coverage five seats to one". Those figures are the 86 minus
  the 22 retired keys it kept. Recomputed here against the committed set rather than quoted: the retired
  chart read at `294a2b8` holds 36 `spot_id`s, and intersecting them with the 36 non-`faces_four_bet`
  rows of `calibrated-build-contamination.json` gives **5 survivors** - `BB/LJ:raise@2.5`,
  `BB/HJ:raise@2.5`, `BB/CO:raise@2.5`, `BB/BTN:raise@2.5` and `SB/rfi` - so **31 retired keys are
  refused and 31 spots are new**. The cutover is net zero on spot count, not plus fifty. Only the
  opening-coverage clause survives. This is not a corpus claim and does not travel to phase 17 under
  decision 21's own seam: it is a property of two files, and phase 14's own contract already carries the
  right numbers at lines 114 to 116 ("**31 of its 36 keys collide with nothing the new artifact
  declares** and only 5 collide exactly"). So the contract and the decision list now state different
  results for one measurement, and the list is the document that instructs the report. Item 1's
  appended amendment addresses the paragraph directly - it is headed "What that does to the coverage
  cost recorded above" - and moves the 563-of-3,048 corpus figure to phase 17 and restates the
  qualitative cost, then leaves the spot arithmetic standing. Fix additively, in the same block: 5 of
  the retired 36 survive, 31 are refused, 31 are gained, and the closing measurement states those.

## Non-blocker

- **`mod.rs:1122` does not point at the sentence item 3 quotes from it.** At `4aee435` the comment block
  runs 1118 to 1126; line 1122 is "and feeding them back causally lets the solver BUY the", and "the fit
  was measured as net-of-rake EV over GROSS pot, so use / the gross pot and skip the rake deduction" is
  at **1124 to 1125**. Item 3's new training-rake finding cites 1122 for it, item 20 cites 1122 for it,
  and round 3 above confirms 1122 "really does say" it, so three documents now carry the same off-by-two.
  The finding itself is sound and `AGENTS.md:49` is exact. Cite 1124, or cite the block as 1118 to 1126.
- **Item 7's pin is right and its superlative is narrower than it reads.** "The last commit at which
  `data/artifacts/preflop/six_max_nl25_100bb.json` exists" is true along this branch, because `294a2b8`
  is `a386c77^`. It is not true of the repository today: the file is present at `main`'s tip and in the
  phase 11, 12 and 13 trees, which is why the item's own next clause has to say the pin "becomes an
  ancestor of `main` at the merge". Second half of the same point: the blob is byte-identical at
  `d046ac9` (`841ada2fd7c9b106f71269d0948945a069990e78`), and `d046ac9` is the commit the committed
  `static-build-derived-chart-report.txt` already names as the pin it read the retired chart from. Two
  committed documents naming different commits for the same bytes is the confusion decision 7 exists to
  prevent. One clause fixes both: the last commit on this branch before the deletion, identical bytes to
  `d046ac9`, and the report is regenerated to name the same one.
- **Item 8 proceeds on its default for the third exclusion code, and its `runtime-reversible` class is
  defensible but is no longer self-evident.** No exclusion code reaches the artifact - excluded nodes are
  not in it - so the vocabulary lives in `lookup.py` and in a report that re-derives in minutes, and on
  that reading the class is right and I would not halt on it. What has changed is that phase 17's
  contract now requires each exclusion's cost reported separately so one ruling is not charged with
  another's, which makes the three-way partition load-bearing for a later phase's measurement, and the
  vocabulary is closed by tests that stage 5 freezes. That is word for word the argument item 10 gives
  for calling itself frozen: "a stage-4 test asserts it over the committed artifact and stage 5 freezes
  that test, so changing it later is a task rather than an edit". The item should say in one sentence
  why that argument does not apply to it, rather than leave the two items reasoning oppositely from the
  same premise.
- **Round 3's misdating finding is confirmed mechanically.** The paragraph item 10 withdraws - the
  tolerance "must be re-derived from the re-sourced chart before it is frozen" - is in the block headed
  "Premise superseded on 2026-08-30", not in anything the item carried on 2026-08-24; the 2026-08-24
  correction says the opposite, that the phase halts rather than freeze a gate it has not seen pass. An
  amendment that misnames what it withdraws makes the snapshot unreadable in the one direction the
  append-only rule is supposed to protect.

## Alignment

- `THE-SAME-MEASUREMENT-IS-STATED-IN-TWO-COMMITTED-DOCUMENTS-AND-NOTHING-COMPARES-THEM` - the blocker
  above is one instance and round 3's item-3 finding (58 of 89 human call disagreements against phase
  17's 42 and 14) is another, and both are the shape
  `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS` already names inside the artifact: a
  figure written as a literal in one committed document and recomputed in another, with no check that
  reads both. The contract, the decision list, the ExecPlan and the generated report all restate the
  same census, menus, prices and collision counts today. The remedy is not more diligence; it is that
  one of them is generated and the others cite it, or a check compares the literals.

# Round 5, 2026-08-31: dispositions of rounds 3 and 4

Coordinator, recording what was done with the four blockers the two independent reviews opened and
with the non-blockers worth acting on. Rounds 3 and 4 stand exactly as written; each blocker is marked
in place above.

**Round 3's blocker on item 10 is closed by filing decision 22, not by argument.** The review was right
that the re-cut settled by prose a question Taylor has not answered: he ruled two per-cell relations and
that they are gated on aggregates, and never ruled that a ladder over suited rows keyed by high card is
the aggregate form of the suited-against-offsuit one. The sentence "the gate is written at the ruled
one-point tolerance and it gates" is withdrawn from item 10, which now keeps only what is his - the
one-point tolerance, and the withdrawal of the licence to re-derive it - and the question of which
relations that tolerance gates is **decision 22**, `frozen-into-data`, `Answer: []`, four options,
recommending none. The lane therefore halts at the stage-3 human gate rather than advancing past it.
The review's sequencing point is carried inside the item rather than dropped: every figure it reports
is the `a386c77` proxy, the ruled artifact has never been derived, and "derive it and measure the gate
on the real file first, then rule" is named as a reply Taylor can give.

**Round 3's blockers on items 3 and 6 are closed by the additive corrections they asked for.** Item 3
now splits the table's non-monotonicity in two - the pair-versus-connector ordering and the pair
U-shape are correct realization and were misread, while the sixteen within-row kicker inversions and the
low-pair zigzag are fit noise at `r2` 0.1885 that no SPR argument removes and that reaches the committed
cells as `J6s` 0.000 beside `J5s` 1.000. Item 6 now says hero never initiates the last raise **and** the
chart still answers fifteen full-stack call-offs, which is the contract's own corrected wording, and
states the jam canary over those fifteen committed call-offs as well as over the export.

**Round 4's blocker on item 1 is closed by recomputation.** Verified independently of the review before
acting on it: the retired chart at the pin holds 36 `spot_id`s, the committed set is the 36
non-`faces_four_bet` rows of the contamination walk, and the intersection is **5** - the four big-blind
defences against a non-blind open, plus `SB/rfi`. So 31 retired keys are refused, 31 spots are new, and
the cutover is net zero on spot count rather than plus fifty. The closing measurement is instructed to
state 5, 31, 31 and the opening coverage falling from five seats to one.

**Non-blockers acted on.** The `mod.rs` citation moves from 1122 to 1124 with its comment block named,
in item 3; item 20 and round 3 carry the same off-by-two and are left as written, being committed and a
reviewer's own note respectively. Item 7's pin changes from `294a2b8` to **`d046ac9`**: the blobs are
byte-identical (`841ada2f`), `d046ac9` is already an ancestor of `main` while `294a2b8` is on this
branch only, and `d046ac9` is what the committed derived-chart report already names - two documents
naming different commits for the same bytes is what decision 7 exists to prevent. Item 7 also now says
phase 14 reads from that pin for its own two retired-chart measurements. Item 8 states in one sentence
why it is `runtime-reversible` where item 10 is not: no exclusion code reaches the artifact. Item 15
keeps cell purity with phase 14, since it is read off the chart alone. Item 19 corrects `static`'s SPR
direction, which its own body already had right, and records that `raw` was bounded by an argument
whose sign is wrong and was never solved.

**Four alignment items filed**, since the loop requires an alignment finding to leave the note and enter
`backlog.yml`: `SUPERSEDED-FROZEN-ITEM-STILL-PARSES-AS-ANSWERED`,
`OPTION-SHEETS-SHOULD-SAY-WHICH-OPTIONS-WERE-MEASURED`,
`A-DECISION-LIST-RE-CUT-FOUR-TIMES-IS-A-CONTRACT-REWRITE-IN-DISGUISE` and
`THE-SAME-MEASUREMENT-IS-STATED-IN-TWO-COMMITTED-DOCUMENTS-AND-NOTHING-COMPARES-THEM`. `docs/BACKLOG.md`
is regenerated.

## Blocker

None open. All four are marked in place above and dispositioned here. Stated as prose because a bullet
under this heading is counted as an open blocker.

## Non-blocker

- **Two off-by-two citations are knowingly left.** Decision 20 cites `mod.rs:1122` for the
  net-of-rake-over-gross-pot sentence and is committed, so correcting it inside a ruling would be an
  edit to a snapshot; round 3 above repeats it and is a reviewer's own note. Item 3 carries the correct
  citation and this bullet is the cross-reference. Nothing downstream reads a line number.
- **Item 20's option-space sentence inherits round 3's `raw` finding and is not amended.** "raw is
  static with the positional term removed, so it cannot be better on that axis" is argued with the sign
  backwards, per round 3. The ruling does not move - realizing 100 percent of raw equity still defends
  far too wide, and nobody has proposed shipping it - so the correction lives in item 19's amendment and
  in `OPTION-SHEETS-SHOULD-SAY-WHICH-OPTIONS-WERE-MEASURED` rather than as an amendment to a ruled item.

## Alignment

- `THE-SAME-MEASUREMENT-IS-STATED-IN-TWO-COMMITTED-DOCUMENTS-AND-NOTHING-COMPARES-THEM` - round 4's
  blocker and round 3's stale 89-and-58 finding are the same shape, one level up from
  `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS`. Filed with the remedy the review
  named: one document generated and the others citing it, or a check that compares the literals the way
  `scripts/repo_facts.py` already does for ten facts.
- `A-DECISION-LIST-RE-CUT-FOUR-TIMES-IS-A-CONTRACT-REWRITE-IN-DISGUISE` - this stage is the fourth re-cut
  of one list and the second in two days. The append-only rule is right and stays; what is missing is
  `AGENTS.md`'s folding rewrite for the decision-list side, taken as its own task when the phase closes
  rather than mid-phase.
