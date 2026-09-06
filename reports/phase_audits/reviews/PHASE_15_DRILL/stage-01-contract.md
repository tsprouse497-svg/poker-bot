# Phase 15, stage 1 (contract) - independent review

Reviewer: a read-only subagent that wrote none of this stage's work, briefed with the driver's own
question and forbidden from running any gate command. Scope reviewed:
`git diff 098816bd86ba8c49c132ca9894979ca2d8f918ec -- docs/exec_plans/active/PHASE_15_DRILL.md
docs/phase_contracts/PHASE_15_DRILL.md`.

The question the loop asked: *Is any acceptance criterion unfalsifiable, a restatement of the phase
title, or satisfiable without doing the work it names?*

The reviewer recomputed every figure in the contract's Scope from
`data/artifacts/preflop/six_max_100bb_rakefree.json` rather than reading them. All were correct: the
5 / 25 / 219 family counts, the 52.6637 / 39.0915 / 8.2448 arrival shares, 44 zero-arrival spots all
facing a three-bet, 1,820 of 18,431 mixed at 0.999, the per-family mixing, and the 106 hero-call
spots at 0.016416 percent with the BTN 31 / CO 31 / SB 26 / HJ 18 split. The no-per-action-EV claim
was verified against the artifact, the export and the equity source card.

## Blocker

- **[resolved] The refusal criterion named two identifiers that do not exist, and a frozen test
  records them as retired for exactly this reason.** The contract said the converter distinguishes
  `derivation:source-misprices-multiway` from `derivation:outside-selection-rule`. Neither string is
  anywhere in `src/` or `scripts/`. The live vocabulary in `solver_artifacts/lookup.py` is
  `derivation:beyond-committed-raise-depth`, `derivation:multiway-exposure-above-threshold`,
  `derivation:big-blind-squeeze-spot` and `derivation:no-legal-spot-key`, and
  `tests/test_chart_census.py` says in its docstring that the retired pair named a rule decisions 40,
  46 and 48 replaced, so "a later phase reading a bucket by its name would have got the wrong set,
  which is the one job a closed vocabulary has." This contract was that later phase. The names came
  from `backlog.yml`, which is equally stale. Second half of the same blocker: no mechanism existed
  to carry a reason through - the codes are produced by `chart_selection.exclusion_code` against the
  33,969-node export, the committed artifact carries no exclusion table, and the ExecPlan gave lane E
  only `lookup.py`, so no lane owned the path the criterion required. **Fixed**: the criterion now
  names the four live codes, states that the mechanism is a ruling this phase makes rather than an
  assumption it starts from, and the ExecPlan gives lane E `chart_selection.py` and the export-side
  path. The mechanism and its cost are settled in decision 7, which measured the buckets and found
  the cheap answer: 33,362 nodes are derivable from the key alone and the other two buckets are 348
  and 10 keys, a few kilobytes. Filed as `BACKLOG-ENTRIES-QUOTE-RETIRED-REFUSAL-CODES`.

- **[resolved] The Scope's central premise about a cell was false, and it hid a hole in two
  criteria.** The contract said a cell is `{fold, call, raise}` weights "and nothing else". 4,225 of
  18,431 cells carry only `{fold, raise}` - 25 spots, all 5 first-in and the 20 non-big-blind spots
  facing an open, where decision 45 merged the flat into the raise - and those spots are **80.2010
  percent of arrival**. Only the 5 big-blind spots facing an open price a call. So "every action the
  cell prices is shown" is a two-button menu on four deals in five, and "the score is the weight the
  chart puts on the action the student took" was **undefined** when the student calls, which is the
  commonest thing to get wrong facing an open. Scoring it zero would teach that calling an open is
  always a mistake. **Fixed**: the Scope states the measurement, and a new criterion rules that an
  action the cell does not price is shown and never scored, covering the small blind's limp too.
  Decision 10 carries the ruling with its cost. Filed as `A-MERGED-FLAT-TEACHES-A-FALSE-RULE-TO-A-HUMAN`.

- **[resolved] The 0.999 pure threshold contradicted a committed report about the same artifact.**
  The contract wrote "the pure threshold of 0.999" as though it were a repo constant. The repo's
  constant is `PURE_PCT = 99.0`, and the committed derived-chart report publishes 93.48 pure and 3.66
  mixed. Recomputed: 3.66 percent below 0.90, 6.52 below 0.99, 9.87 below 0.999, 13.19 below 0.9999.
  The derived claim "about one deal in ten has no single right answer", repeated as a packet
  requirement in poker English, is false at any threshold a player would recognise - at 90/10 it is
  one in twenty-seven. **Fixed**: the Scope prints the whole ladder, states that the phase pins one
  threshold and uses the repo's 99, and names the 527-cell band the published report leaves unnamed.
  The packet requirement no longer claims one in ten. Filed as
  `ONE-PURE-THRESHOLD-CONSTANT-FOR-THE-WHOLE-REPO`.

- **[resolved] "The weight captured against the weight available" had two readings and the contract
  picked neither.** If "available" is 1.0 the session score is mean agreement weight; if it is the
  cell's maximum, a student who always takes the top action scores 100 percent and the score stops
  measuring mixed play. This is the phase's headline output and the criterion was satisfiable either
  way, so it could not fail. **Fixed**: the contract now defines a *graded* decision - top weight
  clears the pinned purity threshold, arriving reach clears the pinned floor, and the student's
  action is one the cell prices - and fixes the score as the mean weight on the student's action over
  graded decisions, with ungraded decisions counted by reason and never folded in.

## Non-blocker

All of these were raised by the reviewer and all were fixed in the same pass, because they were
cheap and the contract is easier to read for it.

- "One deal in 2,600" was a mean over a distribution whose median is one in 899,346, and it
  understated the contract's own argument by a factor of about 340. Both figures are now given.
- "There is no chip number anywhere in it" was false: the artifact carries `size_bb`, the blind
  structure and the stack depth. The true claim - no value attached to an action - now stands in its
  place.
- The no-EV test's predicate was undefined and would have collided with the report's own spot keys
  and raise sizes. The predicate is now named: no scoring path may read the equity matrix, run the
  simulator, or emit a field whose name or unit is `bb`, `chips`, `ev` or `cost` outside the price of
  an offered action.
- "Four further stops" then listed five. All five are real; the count is corrected.
- The contract handled the roadmap's ingestion conflict explicitly and was silent on the other one,
  that the roadmap promises this phase says "what the difference costs". The silence read as an
  oversight. It is now refused in the same paragraph, with the measurement as the reason.
- The sampling criterion defined the policy only negatively, so any third policy passed. It now
  carries two positive properties: a stated minimum share per family, and arrival's order within a
  family.
- "Both readings" in the 106-spot bullet carried two different splits in one phrase. Both are now
  named separately.
- "A thin shell over it" and "the smallest set that makes the report mean something" were bounds that
  could not fail. Both are now measurable.
- The `sim-NNN` migration criterion was vacuous: nothing in `tests/`, `reports/active/` or `data/`
  asserts a `sim-` id today. The contract now says the set is empty rather than claiming a migration,
  and the ExecPlan no longer disagrees with it about which stage the id change lands in.
- A line number into `AGENTS.md` goes stale on the next edit. The boundary is quoted instead.
- The backlog sweep quoted `phase: "15"`, and `A-REFUSAL-CANNOT-TELL-THE-HUMAN-WHY` is written
  `phase: '15'`. The sweep is now on the parsed value.

One thing the reviewer did not raise and the coordinator records anyway: the contract is 283 lines
against `check_file_sizes`'s 300-line cap, and this phase has nine stages left, each of which may
amend. `AGENTS.md` warns that amendments only ever add lines. If an amendment does not fit, the
answer is the rewrite that folds amendments into the criteria they amend, never a raised cap.

The reviewer judged the Delegation Plan real rather than decorative: six lanes with genuinely
disjoint file ownership, an integration order argued from real coupling, reviewers named and excluded
from authorship, and an adversarial verifier. It found two gaps, both now closed - no lane owned the
export-side derivation path, and no lane owned the `drill/` package skeleton.

## Alignment

- `BACKLOG-ENTRIES-QUOTE-RETIRED-REFUSAL-CODES` - a test guards the retired code names in the code
  and nothing guards them in `backlog.yml`, which is where this contract got them.
- `ONE-PURE-THRESHOLD-CONSTANT-FOR-THE-WHOLE-REPO` - the mixed share swings from 3.66 to 13.19
  percent across plausible thresholds and no module owns the constant.
- `A-MERGED-FLAT-TEACHES-A-FALSE-RULE-TO-A-HUMAN` - phase 15 can rule how the drill behaves and
  cannot fix a chart that prices no flat on 80.2 percent of arrival.
- `OPENING-FAMILY-CALLED-PASSING-AGAINST-A-RULE-IT-BREAKS` - filed by the coordinator rather than by
  this reviewer, against phase 14. Not that the comparison gates nothing, which is a ruling under
  decision 6, but that the report states a direction rule, three of five opening rows break it, and
  the same report calls the family passing.
- `ROADMAP-RULING-3-SAYS-LIMPS-ARE-IN-THE-TREE-AND-THEY-ARE-NOT` - also the coordinator's. The
  roadmap rules limps into the tree, `RULED_CONFIG` sets `"limp": False`, and the limped pot is the
  largest refusal family the drill inherits.
- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` - the reviewer noted that "every entry whose phase is
  15 is closed, restated or moved forward" is verified by nobody. That existing entry already records
  the blind spot, so nothing new is filed against it.
