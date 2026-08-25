# Phase 14 stage 4: review of the predicate change

Two independent read-only reviewers read `git diff 9be45bf` over the contract, the decision record,
the ExecPlan and the disposition note, before it was committed. Neither wrote any of it. One was
mechanical, re-measuring every count in the new text against the committed export and checking the
rewrite against the contract it replaced; one was on the poker, asked whether the resulting bot
plays and teaches correctly and told explicitly to ignore the paperwork.

The mechanical pass confirmed every number. The poker pass found that the ruling's premise is
false, and that finding is why this phase is halted again rather than advancing.

## Blocker

- **[open, for Taylor] The ruled predicate does not select the nodes the model prices exactly. 24
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

- **[open, for Taylor] The four-bet continuations teach folding JJ at 32 percent pot odds.** At HJ
  facing a lojack four-bet to 22.5, inside the 110, JJ arrives at 96.7 percent reach and folds 97.2
  percent, TT folds 99.9, 99 folds outright, AJs jams 51.4 percent with no call in AQs, and 76s
  calls 99.6. Hero is adding 15 into 31.5 needing 32.3 percent with 77.5 behind. Sub-question 1 was
  answered "the 110 as counted" and the consequence was put on the record rather than in the ranges;
  the reviewer's point is that the record does not reach the person at the table, and a confident
  wrong answer is worse than a refusal because it replaces the student's prior instead of leaving it.

- **[open, for Taylor] Adjacent small pairs split 0.07 against 99.94 at full reach, and the
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
