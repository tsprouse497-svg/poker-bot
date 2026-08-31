# Stage 1 review: phase 14 contract

Two independent read-only reviewers, 2026-08-23, neither having seen the other's work. One
briefed on mechanical falsifiability, one briefed to judge the poker rather than the document's
fidelity to a process. Neither edited a file or ran the gate.

Question the driver printed: *"Is any acceptance criterion unfalsifiable, a restatement of the
phase title, or satisfiable without doing the work it names?"*

Scope read: `git diff c68d777 -- docs/exec_plans/active/PHASE_14_CHART_CUTOVER.md
docs/phase_contracts/PHASE_14_CHART_CUTOVER.md`.

Eleven blockers between them. The phase's centre moved as a result: the first draft was written
as "convert the export", and after this round the contract is "select from the export, and say
why" - because the export can neither fit under the byte cap nor be trusted at depth.

## Blocker

- **[resolved] The contract required the expectations file to be rederived from the export.**
  `data/artifacts/preflop/expectations/six_max_nl25_100bb.json` holds eleven aggregates whose own
  `notes` field says they "are the only numbers in this phase that this repo did not produce, so
  they are what catches a range that is uniformly wrong rather than merely self-consistent".
  Rederiving a reference from the thing it checks makes it unable to fail, which is the exact
  failure `V2_RULING_MITIGATIONS.md` warns about. The criterion also named
  `check_solver_export_expectations` as what would prove it, and that script never reads the file.
  Confirmed by the coordinator: its own docstring says every number it checks is computed from
  the export on this run, and the expectations file is read only by
  `generate_preflop_strategy_report.py` and `generate_solver_export_report.py`, for printing.
  Fixed: rederiving it is now a Non-goal with the reason, the sizing table is rederived alone, and
  the report prints the derived chart against the expectations gated by nothing, which is what
  phase 10's decision 6 already ruled.

- **[resolved] Deep nodes carry strategies the solver never converged, and the contract committed
  them as playable cells.** GTOpen's target is a summed best-response gap in big blinds over the
  whole tree, so a 0.01bb target constrains nothing where mass is negligible. The one deep node
  the export publishes: HJ facing a lojack four-bet to 22.5 folds JJ 97 percent, TT outright, 99
  outright and KJs outright, while calling 76s outright and 87s 94 percent - at 64 to 100 percent
  arriving reach, so these are reached cells rather than rounding. Hero is adding 14.5 to a pot of
  32 there and needs 31 percent; JJ has it comfortably and 76s barely. The reviewer ran the two
  airtight dominance relations over all eleven published grids: one violation across the ten
  shallow reference nodes, 42 at that single four-bet node. The export is clean where a human read
  it and unconverged where he did not. Fixed: the selection rule is now the phase's central
  `frozen-into-data` decision and the contract requires it to rest on arriving reach or an
  equivalent convergence measure.

- **[resolved] The node census could not fit the byte limit, so an unplanned filter would have
  decided which poker the chart contains.** The contract required converting all 38,828 nodes and
  separately required `data/artifacts` to stay under 20 MB. Measured by the coordinator
  independently of both reviewers: 272 MiB at the retired chart's own 7,346 bytes per spot, 131
  MiB compacted, 407 MiB if every node keeps all 169 hand classes as a GTOpen node does, and 71
  MiB with each spot filtered to hero's arriving range. Every version is over by between 4.5x and
  26x, against roughly 2,100 spots of headroom. "Inexpressible" was no escape either: the phase 12
  grammar expresses repeated positions and carried sizes, and derives a valid key for all 38,828
  nodes with zero rejections. Fixed by the same change as the item above, and the contract now
  forbids choosing the rule to fit the limit and then justifying it in poker terms.

- **[resolved] Retiring the old chart by duplicate-key collision does not work, and fails
  silently.** The contract made `PreflopChartLibrary`'s duplicate refusal what decides whether the
  retired chart may sit beside the new one. It does not fire where it matters: the retired chart
  three-bets to 8, 11 and 13.5 and opens the small blind to 3.5, while the export three-bets
  uniformly to 7.5 and opens to 2.5, so 17 of its 36 keys collide with nothing. The library would
  build clean with both loaded and the bot would answer every three-bet spot and every small-blind
  open from raked GTO Wizard ranges while believing it plays the rake-free solve. Fixed: deletion
  is required and a test asserts absence.

- **[resolved] The contract never named `REALIZATION-MODEL-UNDERPRICES-POSITION`.** It is the one
  measured range defect already filed against this phase, and every check the contract wrote would
  pass a systematically position-underpricing range - the ordering check is relative and the
  button still opens widest. The number is in the spot the whole measurement turns on: the big
  blind folds 50.98 percent facing a 2.5bb small-blind open from a 54 percent range, closing the
  action with 1.5 to win 3.5 and needing 30 percent in position, and the big blind holds 58 of the
  89 human call disagreements. Fixed: the entry must be settled with one of its three named
  dispositions, the choice is written onto the committed artifact's source card, and it is named
  as a third candidate explanation in the closing measurement.

- **[resolved] "Every raise size comes from the export's own action label, never from a constant"
  was unfalsifiable.** The solved config has exactly one opening size and one raise multiplier, so
  a converter hardcoding 2.5 and 3.0 produces a byte-identical artifact and passes every other
  criterion. Only reading the code distinguishes them, which the stage question names as a
  blocker. Fixed: the contract now requires a test running the same converter over a synthetic
  export whose labels are perturbed, and asserting the keys carry the perturbed sizes.

- **[resolved] The non-monotone criterion's only reachable branch was "write it down".** The entry
  `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` names two remedies - re-solve to a tighter gap, or
  smooth the pair ladder with the reason recorded - and the contract's own Non-goals forbade the
  first and its Forbidden shortcuts forbade the second as a heuristic fill. So the phase would
  have shipped a known leak with a note while the criterion went green. Fixed: those two are now
  the only permitted dispositions.

- **[resolved] "A stated hand-strength order" was not well defined and would have over-fired.**
  Preflop strength is not totally ordered. Plain card-rank dominance gives 61 to 121 violations
  per node over the published grids, and its top hits are correct poker - the lojack opens 76s
  always and T6s never, which is the connector beating the four-gapper as it should. Fixed: the
  contract names the two relations that hold in every preflop spot, a higher pair at least as
  often as a lower pair and a suited hand at least as often as the offsuit hand of the same two
  ranks. Under those, the ten shallow nodes give exactly one violation, which is the filed pair.

- **[resolved] The limps criterion was weaker than the entry it closed.**
  `CHART-HERO-MUST-NEVER-LIMP` asks for a rule and says why: the export enforces it by
  construction, "but that is a property of the data rather than a rule", and phase 14 owns the
  schema. The contract asked only for a measurement over the committed file and then closed the
  entry on it. Fixed: the schema must reject a call weight on a spot with an empty
  `action_sequence`, and the entry closes on that.

- **[resolved] The closing measurement's prediction was falsified in advance on both halves.**
  Directionally, big-blind defence widens 4.65 points against the lojack, 3.72 against the hijack,
  2.64 against the cutoff and 6.14 against the small blind - and comes back 2.67 points *tighter*
  against the button, the opener that generates the most big-blind defending decisions in any
  six-max sample, so an aggregate "defence widens" is wrong on its largest component. The price
  half is false by construction: the cutover reprices hero's own small-blind open from 3.5bb to
  2.5bb, so the big-blind-facing-small-blind family moves against a corpus median open of 2.25.
  And a directional prediction cannot adjudicate the question at all - roughly five points of
  extra defence is about 60 combos of 1,326 against a 39-point call-agreement gap, so any nonzero
  movement confirms it while leaving the gap intact. Fixed: the prediction is now required per
  opener and with a magnitude band computed from those deltas before the run, and it must cover
  price and say which way.

- **[resolved] The three-way census had no closed vocabulary and no external denominator.** A node
  the converter merely failed to handle could be filed as "inexpressible" and still reconcile.
  Fixed: committed, excluded, and inexpressible must sum to the export's own published node count,
  and both reasons come from a closed vocabulary the phase's tests enumerate.

## Non-blocker

- **The command IDs were the phase title.** `pytest_chart_cutover` and
  `generate_chart_cutover_report` carry no phase number so they pass the letter of the `AGENTS.md`
  naming rule, but a cutover is an event that happens once while the command runs on every gate
  forever, and every sibling names a durable subject - `pytest_solver_export`,
  `pytest_spot_vocabulary`, `pytest_table_state`. Renamed to `pytest_derived_chart`,
  `generate_derived_chart_report` and `reports/active/latest_derived_chart_report.txt`. Nothing
  referenced the old names, so the rename was free at stage 1 and would not have been at stage 4.
- **Most of the closing-measurement criteria fail only into report prose.** The contract now says
  which four the generator must assert - the node census, the artifact's spot count against the
  walk's, the dominance relations, and the old-versus-new disagreement count - and says the rest
  are prose, so stage 4 knows what a canary can reach.
- **Rake-free is ruled and the contract's silence on the user's own table is defensible**, since
  the corpus is rake-free too. But the headline "small blind enters 19.68 points wider" is mostly
  the limps ruling rather than rake: the retired chart enters from the small blind 48.14 percent
  of the time counting its 13.73 percent limp, against 54.09 percent now, so the honest figure is
  about six points wider entry with twelve points of limping converted to raising. Worth getting
  right in the report; not a contract defect.
- **Hero never limps is free in this phase.** Phase 10's own probe measured the small blind
  raising 53.58 percent with the limp available and limping 1.38 percent, against 54.09 percent
  under the ruled no-limp config - half a point. No measurement is owed. The caveat worth one line
  in the report is that a preflop-only model resolving flops at a scaled equity share is
  structurally unable to price a limp, so "the solve barely limps" is the model agreeing with
  itself rather than independent support for the ruling.
- **Two report definitions were at risk of being dropped by a new generator** - that agreement
  means nonzero weight rather than a matched draw, and that real players are not an oracle - along
  with the stricter sampled-action match rate, 89.0 percent for Pluribus and 85.3 for the humans.
  All three are now required.
- **Three quoted figures did not survive checking as quoted.** The 283/7 refusal split is not in
  the sample-comparison report the contract's sentence implied; it is in the phase 13 packet and
  the table-state report. The "21 decision points facing a limp" traces to the wording of
  `CHART-CANNOT-ANSWER-A-LIMPED-POT`, and recounting the inventory under the obvious definition
  gives 15 rows and 22 points, so the definition behind 12/21 is stated nowhere. And the retired
  chart's 13.73 percent small-blind limp is combo-weighted over 1,326 combos; the unweighted mean
  is 17.32. The contract no longer quotes the first, requires the phase to publish the second with
  its definition, and states the basis of the third.
- **The roadmap's spot counts do reproduce, at a five-entry cap.**
  `ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE` says no variation tried reproduces 1,691 and 848. The
  id is kept on one line deliberately: the quality gate reads every capitalised hyphenated token
  in `docs/` and `reports/` as a backlog id, so a wrapped one becomes a citation of an item nobody
  created. The variation is the entry cap:
  five gives 1,691 and 848 exactly, six - where the v1 vocabulary saturates - gives 1,949 and 977.
  The entry is answerable and has been updated rather than left open.
- **A derived chart cannot be gzipped.** `import_preflop_artifacts` globs `*.json` and reads text,
  so compression is not available as a way under the byte cap. Recorded because it is the first
  thing a reader reaches for on seeing the size measurement.

## Alignment

- `SOLVER-CONVERGENCE-IS-NOT-UNIFORM-OVER-THE-TREE` - a summed best-response target in big blinds
  says nothing about cell-level accuracy at low-mass nodes, and every future solve capture needs a
  per-node convergence or reach statement rather than one tree-wide number.
- `CHART-CELLS-SHOULD-CARRY-ARRIVING-REACH` - the artifact schema has no field distinguishing a
  cell the solver trained from one it never visited, which is the same information a refusal
  carries and the chart currently cannot express.
- `AGREEMENT-RATE-NEEDS-A-DENOMINATOR-POLICY` - scoring against human professionals with "nonzero
  weight counts as agreement" makes the metric monotone in how mixed the chart is, so a noisier
  chart scores higher and the repo has no stated rule about that.
- `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` - the 20 MB directory limit and "commit the whole
  tree" are on a collision course for every future solve rather than only this one, and the
  tradeoff should be ruled once rather than rediscovered per phase.
- `CORPUS-LIMITS-DOC-STILL-SAYS-KEYS-CARRY-NO-SIZE` - `docs/CORPUS_COMPARISON_LIMITS.md` says spot
  keys carry no size at all, which phase 12 made false, and the doc was touched the same day
  without updating it.
- `LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION` - `CHART-CANNOT-ANSWER-A-LIMPED-POT` quotes 12
  rows and 21 decision points and no file states the rule that produced them; the obvious
  recount gives 15 and 22.

---

# Round 2, 2026-08-30: the contract-update that re-sources the phase

The lane was returned from stage 6 to stage 1 by a hand edit of `verification/loop_runs/14.yml`,
because Taylor ruled on 2026-08-30 to re-source the solve with `add_allin: false` and the two
constants that carry it are frozen-into-data. The notes above are the first cutover's stage-1 review
and stand as written; this round reviews the rewrite.

Two independent read-only reviewers, one mechanical and one on the poker. Neither wrote any of the
work, neither saw the other's remit or notes. The diff under review is 8 files against `a386c77`:
the contract rewritten in full, decisions 14 and 15 added and 3 and 6 restated, the two constants,
the ExecPlan, `backlog.yml`, `CURRENT_TASK.yml` and the loop pointer.

The coordinator re-measured every finding before acting on it, on the stage-6 precedent that a
reviewer's report is not evidence either. Where a coordinator measurement differs from a reviewer's,
the coordinator's is recorded and the difference stated.

**A note on how the driver behaved, because it matters for the next restart.** `loop_stage.py`
reported "this stage's checks pass" throughout. It does not know this round happened:
`check_stage_review` tests only that `stage-01-contract.md` exists, and the first cutover's copy
already did. On a restart every stage from 1 to 5 already carries notes, so the driver would wave a
whole re-run through without a single fresh review. Filed under Alignment.

## Blocker

- **The four-bet-facing shape is not fixed by the re-source, and the stage-6 note's `[resolved]` on
  blocker B2 is false.** Found by the poker reviewer, re-measured by the coordinator directly
  against the derived chart. At the `HJ/LJ`, `BTN/LJ` and `CO/HJ` four-bet lines, JJ, TT, 99 and 88
  all continue at **0.000** while 76s, 87s and JTs continue at **1.000** - pure folds of jacks
  beside pure calls of 76 suited, at full reach, so not indifference and not noise. The poker
  reviewer priced it against the villain's own four-bet range and found the ordering backwards by 8
  to 11 equity points on the wrong side of the pot odds, with realization cutting the other way. The
  stage-6 note marked B2 resolved on the reasoning that these spots were re-solved; they were, and
  the defect survived. That note is committed at `a386c77` and stays as written; decision 14 now
  carries the correction. **Open: this is a property of the source, not of anything this task wrote,
  and it needs a ruling.**
- **Strict rank dominance did not improve.** Poker reviewer: 93 inversions across 31 of 51 under its
  relation, against 95 across 35 of 86 on the superseded chart. The coordinator recounted under a
  stricter relation - same top card, same suitedness, kickers exactly one rank apart, plus adjacent
  pairs, both classes at reach 5,000bp or better, wheel-ace family excluded - and got **54 on the
  re-sourced chart against 52 on the superseded one over the same 51 spots**. The counts differ; the
  conclusion does not, and it is the conclusion that matters: the re-source produced **no
  improvement and a slight worsening**. Worst cases are pure 0-versus-1 flips between adjacent
  kickers - `J6s` 0.000 beside `J5s` 1.000, `Q7s` 0.000 beside `Q6s` 1.000, `T6s` 0.000 beside `T5s`
  1.000. A per-spot form of the group-dominance gate the contract requires fails **36 of 385**
  adjacent pair-band comparisons at reach 1,000bp or better. The contract says the phase halts rather
  than ship a gate it has not seen pass. **Open.**
- **The jam composition is still inverted, and the check this phase verified the repair against is
  too narrow to see it.** The headline check passes and the coordinator confirms it: 15 spots offer a
  100bb jam, all are five-bet spots, AA takes it at weight 1.000 at every one, and there is no spot
  where a low pair jams and aces do not. But at
  `t6/d100/SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` the five-bet range is **AA at 1.000 and 87s
  at 0.995** (reach 7,053) while KK, QQ and AKs all flat and AKo folds 0.782; A5s, which has the
  blocker that justifies a five-bet bluff, jams 0.045. The poker reviewer found the same shape at
  four more spots. Five-betting a no-blocker connector where AK never does is the same class of
  error as the one Taylor rejected, one family across. **Open.**
- `[resolved]` **The rewrite dropped the only falsifiable clause in the refusal-rate criterion.**
  Found by the mechanical reviewer. The previous contract required that of the retired chart's 36
  spots, 21 stay covered, so the refusal rate must rise on the other 15 **and nowhere else**, a rise
  outside them being a defect rather than the cost of the ruling. The rewrite kept "reported against
  a named baseline and split by cause" and dropped the test. Nothing replaced it, and without it the
  refusal rate has no defect condition at all. The coordinator re-measured the clause against the
  re-sourced artifact: **21 of 36 still covered, 15 not**, unchanged from the 86, so the re-source
  did not falsify it and the drop was accidental rather than a restatement. Restored to the contract
  with the re-measurement noted.
- `[resolved]` **Three `frozen-into-data` decision items had their premises destroyed and were left
  un-amended.** Decisions 2 and 10 both rest on the lojack opening 44 at 72.81 percent, and **the
  lojack opening range is not in the committed 51** - the artifact holds exactly one spot with an
  empty action sequence, `t6/d100/SB/rfi`. Decision 9's pre-registered magnitude bands were computed
  on the superseded export and every delta under them moved. A pre-registration whose numbers were
  fixed against data the phase no longer ships is not a pre-registration. All three amended: 2 and 10
  as premise-superseded with the measurement retaken, 9 with its form kept and its arithmetic void
  until re-registered before the closing measurement runs.
- `[resolved]` **Decision 15 contradicted decision 11 without superseding it.** Decision 11 rules the
  conclusion is read off the permissive agreement rate; decision 15 establishes that rate was
  measuring menu width. Both standing, a report obeying both prints the strict rate and then reads
  its conclusion off the permissive one - the exact failure the contract calls stating the reverse of
  the truth. Decision 11 now carries an explicit supersession: the conclusion is read off the strict
  sampled-action rate, with the permissive rate and cell purity printed beside it.
- `[resolved]` **A planted mutation was left live in the working tree.** The mechanical reviewer's
  gate run left `verification/.mutation_in_progress` and the
  `solver-export-aggregates-ignore-the-arriving-range` defect applied at
  `gtopen_export.py:160`, on a file carrying two uncommitted edits of this task's own. The sentinel's
  instruction is to restore the file with `git checkout`, which would have destroyed both. Reverted
  the single mutated line instead, cleared the sentinel, purged the cached bytecode, and re-measured
  the gate command the reviewer had reported under it. `check_scope` is the thing that caught this,
  which is what it is for.

## Non-blocker

- **Two figures in the rewrite did not reproduce and are corrected.** "17 of its 36 keys collide with
  nothing the new artifact declares" was carried over verbatim from the previous contract and is
  wrong under every reading the coordinator could construct: measured, **31 of 36 collide with
  nothing and only 5 collide exactly** (21 match if prices are stripped). The direction is safe - the
  real number strengthens the deletion argument - but the number was restated without being
  re-measured. And decision 6's "18.6 percent of hero's aggressive volume" is combo-weighted only,
  while the 60.6 and 5.0 it sits beside are defined in that same item as shares of *reach-weighted*
  volume; measured that way it is **13.7 percent** (an independent measurement under a different
  reach normalisation got 12.1). Both corrected, the second with its definition stated so the three
  numbers are not read as a trend.
- **Decision 14's justification for the solve target overstated twice, and both are withdrawn.** It
  claimed "0.00015 is never reached", which nothing measured supports - the run terminated at
  iteration 1,900 on meeting the target, so iterations 1,901 to 2,000 were never observed. And it
  cited `tests/test_chart_cutover_evidence.py:652` as a frozen assertion the target keeps true. The
  line does stay true, but it sits inside
  `test_the_committed_solve_is_the_one_phase_ten_captured_and_no_re_solve_replaced_it`, whose other
  assertions pin `iterations == 300` and both checksums to the superseded export. That test exists,
  in its own docstring's words, to make a silent re-solve loud - so it is designed to fail on exactly
  what decision 14 rules, and its failing is the canary working rather than a constraint on the
  target. The target stands on the cap binding at 1,900 of 2,000 and on nothing else.
- **A second vacuous criterion, of the same class the coordinator flagged for the sizing schema.**
  "Later position opens wider among the four non-blind positions" cannot be violated by an artifact
  holding zero non-blind opening ranges. The contract's own scope paragraph says only the small
  blind's survives, so the contradiction was internal. Now stated: the first half is checked against
  the export, the second half against the artifact, and a test asserting the first over the artifact
  is vacuous. Two smaller instances recorded in the contract too - the inexpressible census bucket
  publishes empty, so the three-bucket partition is really two.
- **The stale docstrings on both changed constants are fixed.** `gtopen_export.py` still described
  `SOLVE_TARGET_GAP_BB` as "GTOpen's own default target and cap" directly under the line that
  changed it away from that default, and `gtopen_config.py` still said "Decision 2 fixes it verbatim"
  with no note of decision 14's supersession of one field.
- **This task cannot commit a passing gate, and that is correct rather than a defect.** Flipping
  `RULED_CONFIG["add_allin"]` makes the committed export unloadable: `config_errors` returns `config
  field add_allin is True, ruled False`, and `pytest_derived_chart` - a gate command of an active
  phase - is red. Re-measured by the coordinator after clearing the mutation above, so the number is
  clean. The export is regenerated in implementation mode at stage 6 and the gate goes green there.
  Recorded so it is not discovered at closeout as a surprise.
- **Checked and found sound, recorded so the absence of a finding is not read as an absent check.**
  The mechanical reviewer re-derived every headline figure independently from the serialised export
  and its derived artifact is JSON-identical to the coordinator's: the census, the spot and cell
  counts, the price ladder, the three menus, the 0-spots-offer-both claim, the strict subset and the
  arrival split, the blind-defence bands, the agreement and purity figures, and the solve facts all
  reproduce exactly. `config_posted` differs from the re-sourced config in exactly one field. Phase
  10's decision record was **not** edited - `git diff a386c77` against it is empty - which is right,
  because a completed phase's packet is a snapshot of what that phase believed. Decision 14's
  frozen-into-data class and decision 15's runtime-reversible class are both correct. The
  `CHART-HERO-MUST-NEVER-LIMP` schema rule is enforced in code at `schema.py:283` rather than only
  asserted. The hand-class index is a clean bijection over 0 to 168 with AA at 168, so the
  suited/offsuit transposition the extractor warns about did not happen. The jam retest is
  falsifiable rather than vacuous - it is precisely the assertion that failed on the first cutover.
  And on the poker side: the aggregate five-bet frequency is opener-ordered and sane at 11 to 23
  percent, KK and QQ flatting a lojack four-bet rather than stacking off is defensible on the
  reviewer's own EV numbers, the 2.5/7.5/22.5/100 price ladder is a real consequence of the ruled
  config rather than a bolted-on jam, and `arrival_ppb` for `SB/rfi` reconciles to six significant
  figures with the product of the four upstream fold frequencies.

## Alignment

- A restarted lane re-runs stages that already have review notes, and `check_stage_review` tests only
  that the note file exists. Every stage from 1 to 5 would advance without a fresh review on any
  restart. `LOOP-REVIEW-CHECK-IS-BLIND-TO-A-RESTART`
- The decision record has no supersession discipline. Items 2, 9, 10 and 11 all rested on
  measurements the re-source invalidated, and the only mechanism for correcting them is a coordinator
  remembering to append a restatement - which happened for 3 and 6 and not for the other four until a
  reviewer found them. Nothing reads a decision list and asks whether a frozen-into-data item's
  stated measurement still holds against the committed data.
  `DECISION-RECORD-HAS-NO-SUPERSESSION-DISCIPLINE`
- "Decision N" is ambiguous across phases in prose. This contract references phase 10's decisions 3
  and 6 alongside phase 14's own decisions 3 and 6, all four disambiguated only by context.
  `DECISION-REFERENCES-ARE-AMBIGUOUS-ACROSS-PHASES`
- The contract is pinned at exactly 300 of its 300-line cap even after a fold-in rewrite that
  deliberately cut rationale. A contract that cannot hold its own criteria inside the cap is a
  structural signal rather than a writing problem, and shaving words is not the answer twice running.
  `PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP`
- One realization model drives nearly every poker finding above. `realization: "calibrated"` prices
  postflop with a per-class coefficient rather than a solve, and its signature is in all of it:
  connectors over-continue, medium pairs and offsuit broadways under-continue, the blinds
  under-defend, cold calls nearly vanish, and four-bet bluffs are chosen by playability rather than
  blockers. No flag change and no re-selection of spots moves it.
  `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`
- The three-bet size is one number for every seat. `raise_mults: [3.0]` makes the big blind's
  three-bet 7.5bb out of position where real solutions use 11 to 13, and **45 of the 51 committed
  spots sit downstream of that 7.5**, so most of the chart answers a node the trainee's game does not
  contain. `ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE`
- The big blind under-defends by roughly half at every opener, folding **63.35 percent** to a button
  open where a 2.5x steal needs 62.5 percent folds to be free - the chart hands the button a
  profitable any-two open. The error is one-directional: the poker reviewer found 78 to 79 hands per
  opener folded above the break-even price and **zero** continued below it.
  `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`

## Root cause of the three open blockers, found 2026-08-30

The three poker blockers above are **left unmarked deliberately**. They are not resolved, and the
lane halts on them; the driver refusing to advance is the correct behaviour and not something to be
cleared by a marking. What follows is the cause, which was found after the blockers were written.

They have a single cause, and it is neither the solver nor the config. Under
`realization: "calibrated"` GTOpen prices every postflop terminal `pot x equity x R`, where `R` is
`class_base` from `cache/realization_fit.json` - 169 numbers, one per hand class, constant across the
whole tree. That table rates **76s 1.1333 above KK 1.0473, QQ 0.8556, JJ 0.7493, TT 0.7196 and 99
0.7196**, and **22 at 0.9102 above every pair from 33 through JJ**. Mean pair base 0.8398 against
mean connector base 0.9539.

The link is causal. Sorting the four-bet node by `class_base` sorts the fold decision - continuing
hands mean `R` 1.0129, folding hands 0.7918, with 76s the second-highest-`R` hand at that node. And
every inversion blocker 2 lists appears in the table as an inversion of the table: J6s 0.5880 under
J5s 0.8105, T6s 0.5847 under T5s 0.7601, Q7s 0.7280 under Q6s 0.7899. The chart is a correct CFR
solve of a wrong payoff function.

The table's own fitter explains why: `r2` **0.1885** over 153,321 observations, with "equity itself
still deliberately excluded as a model input", and monotonicity patched along a hand-picked list of
PAVA chains - broadway aces, K/Q kickers, suited-over-offsuit - whose gaps are exactly the J-kicker,
T-kicker and pair-versus-connector ladders that invert. Filed as
`REALIZATION-FIT-TABLE-IS-NON-MONOTONE-IN-HAND-STRENGTH`.

**Taylor ruled on 2026-08-30 to halt phase 14 and fix the source.** Decision 16 carries the ruling
and what it does and does not invalidate. The blockers stay open until a source exists whose
postflop pricing is monotone in hand strength; at that point the phase re-sources and they are
re-measured rather than marked.

This also retires two things this note said earlier. The poker reviewer's Alignment item attributing
the findings to the realization model "showing through" was right in direction and understated in
kind - it is not a bias in an otherwise sound model, it is a specific non-monotonicity in a specific
committed table, and it is addressable. And the coordinator's framing of "fix the source" as
unscoped work of unknown size was wrong: it is a 169-number table and the ladder list in its fitter.

# Round 3, 2026-08-31: the controlled experiment the halt was missing

Round 2 traced the four-bet defects to `class_base` in GTOpen's `cache/realization_fit.json` by
reading the table and correlating it with the decisions. That correlation reproduces exactly - every
figure in it was re-measured here and none moved. What it never did was vary the suspected cause and
watch the defect move, so "the chart is a correct CFR solve of a wrong payoff function" stood on
inference rather than on an experiment. This round runs the experiment.

**Provenance, stated plainly because it bears on what this round can release.** The measurements
below were taken by the coordinator, not by an independent reviewer. Under the Subagents rule the
agent that produced work is never the only one that judges it, so nothing here marks a blocker
resolved and this round owes a read-only independent review before it does. What it establishes is
evidence; what it asks for is a ruling.

## The experiment

One variable. The tree was rebuilt from the config the committed save carries verbatim, with
`realization` changed from `"calibrated"` to `"static"` and every other field held, including
`add_allin: true` and `allin_threshold: 0.67`. Holding `add_allin: true` is deliberate: it matches
the artifact on screen, so the comparison is against the grids the reviews actually measured rather
than against the re-source.

    POST /api/preflop/spot   with the config below
    POST /api/preflop/solve  {"iterations": 400, "check_every": 25, "target_gap": 0.0001}
    POST /api/preflop/node   {"path": [1, 0, 2, 0, 0, 0, 2]}

```json
{"add_allin":true,"allin_threshold":0.67,"ante":0.0,"call_only_seats":[],"limp":false,
 "max_raises":4,"no_flop_no_drop":true,"open_raises":[2.5],"open_raises_by_seat":null,
 "positions":["LJ","HJ","CO","BTN","SB","BB"],"posts":[0.0,0.0,0.0,0.0,0.5,1.0],
 "raise_mults":[3.0],"raise_mults_by_seat":null,"rake_cap":0.0,"rake_pct":0.0,
 "realization":"static","stack":100.0}
```

Both runs are 38,828 action nodes and 83,123 total, so the tree shape is identical and only the
terminal pricing differs. Convergence is comparable: BR gap 0.004635 against the baseline's 0.0047.
The node is CO facing LJ's four-bet to 22.5 - pot 31.5, 15.0 to add, 77.5 behind, SPR 1.67,
break-even 32.3 percent. Equity is GTOpen's own `preflop_eq169.bin` against each run's own four-bet
range, weighted by strategy x reach x combos.

| hand | R | eq (calib) | calibrated | eq (static) | static |
|---|---|---|---|---|---|
| AA | 1.282 | 75.7% | jam 100% | 76.5% | jam 100% |
| KK | 1.047 | 59.5% | call 99% | 57.1% | call 100% |
| QQ | 0.856 | 46.3% | call 100% | 39.4% | call 100% |
| JJ | 0.749 | 40.8% | **fold 97%** | 31.6% | fold 63 / call 37 |
| TT | 0.720 | 40.9% | fold 100% | 31.7% | fold 58 / call 42 |
| 99 | 0.720 | 40.9% | fold 100% | 31.7% | fold 75 / call 25 |
| 88 | 0.751 | 40.5% | fold 100% | 31.8% | fold 63 / call 37 |
| A5s | 1.009 | 34.9% | call 97% | 30.4% | fold 61 / call 36 / jam 3 |
| 87s | 1.016 | 33.2% | call 97% | 28.1% | fold 48 / call 39 / jam 12 |
| 76s | 1.133 | 29.6% | **call 100%** | 27.9% | fold 47 / call 30 / jam 23 |

LJ's four-bet range moves further than the defence does. Calibrated: AA 19.4, KK 19.3, QQ 17.8,
AKs 12.9, **87s 11.7, 76s 9.0**, A5s 4.4. Static: QQ 25.0, KK 24.7, AA 20.4, AKs 16.6, **A5s 7.1**,
44 3.2, 66 1.5. Removing the class term removes the suited connectors from the four-betting range
entirely and replaces them with the wheel ace. Twenty-one percent of four-bets being 87s and 76s is
not a shape any published solve produces; A5s as the four-bet bluff is the standard one. Nothing was
tuned to get that - one config field changed.

Share of hero's arriving range continuing against the four-bet: 67.1 percent calibrated, 57.4
percent static. `CALIBRATED-REALISATION-PRICES-FOUR-BET-POTS-UNTESTED` recorded 65.4 as the figure
its group measurement could not defend.

## Blocker

- `[resolved]` **Decision 16's exit condition cannot be met by the fix this experiment points at, so the lane
  cannot restart even once the source is corrected.** Withdrawn as framed by round 4's independent
  review: "postflop pricing" is the priced terminal, not the table, so a shrink satisfies it on the
  literal reading. The real ambiguity is quantifier and scope, and it lives in decision 17, which the
  review queue surfaces as an unanswered frozen-into-data item. The withdrawn argument follows as round 3 wrote it. The ruling says the bot waits "until a source
  exists whose postflop pricing is monotone in hand strength". Read literally that demands
  `class_base` be monotone, which is a claim about the wrong object: R is an equity-realization
  multiplier and is not monotone in hand strength in correct poker either, because a suited connector
  genuinely out-realizes a middling pair in a pot with money behind. v5's own fitter says so in as
  many words - "88-22 left free for legitimate set-miner premium" - and the low pair bases are a
  measured, conditioned result rather than an oversight. A fix that shrinks R toward 1 at low SPR
  removes the defect while leaving the table exactly as non-monotone as it is now, so it would not
  satisfy the condition; a fix that satisfies the condition would flatten a measurement the fitter
  deliberately preserved. The exit condition needs restating over the priced terminal instead of over
  the table. Raised as decision 17, `frozen-into-data`, unanswered. (Round 3 ended this bullet
  "Open: needs Taylor's ruling"; the ruling is still owed, on decision 17's restated question rather
  than on this bullet's claim.)

## Non-blocker

- **Round 2 and the backlog entry cite the wrong fitter, and the correct one changes the
  prescription.** Both name `m5_spots/fit_phase_c.py`. The shipped table is `version 5`, produced by
  `m5_spots/fit_phase_c5.py`. The quoted chain list - "broadway aces, K/Q kickers, suited>=offsuit;
  wheel aces unchained" - is v4's and has no pair chain at all. v5 adds
  `["AA","KK","QQ","JJ","TT","99"]`, which is why TT and 99 are pooled at an identical 0.7196: that
  is the PAVA tie, and it is visible proof the chain is live and binding. So the pair ladder is
  chained and **terminates at 99**, and the inversions sit at and below that boundary - 88 at 0.7514
  above JJ at 0.7493, and 22 at 0.9102 above every pair from 33 through JJ. "Pairs are unchained" is
  wrong and points at a different repair than "the chain stops one rung too high".
- **`class_base` is a fixed-reference-mix marginal, and four-bet pots carry zero weight in that
  mix.** `std[k] = pik @ leaf` collapses five cells - facing-SRP, init-SRP, facing-3BP, init-3BP,
  limped - against `pi5 = [0.3341, 0.3341, 0.1432, 0.1432, 0.0454]`. `NCELL` is 5 and there is no
  four-bet-pot cell, so the number applied at SPR 1.67 is a population average that is 67 percent
  single-raised pots, and unsupported 3BP mass even folds back into SRP. The engine at
  `mod.rs:1137` then calls `class_r(k, posw)`, discarding the pot-type axis that was v5's entire
  contribution. This is the mechanism behind the correlation round 2 found.
- **Round 2's dismissal of the discarded SPR coefficients is right for the wrong reason.** It calls
  them class-independent and therefore level-only, which holds for `b_spr` as implemented inside
  `seat_mult`. But `spr0` is exactly `0.0` - low SPR is the fit's reference level - so wiring
  `b_spr` in would raise R at mid SPR and do nothing at 1.67. A shrink toward 1 is not multiplicative
  and does change ordering, which is what the experiment demonstrates.
- **The calibrated branch drops a clamp the static branch keeps.** `mod.rs:1137-1141` bounds
  `share` by nothing; the fallback at `:1149` keeps `.min(pot_eff)`. With `clip` at `[0.2, 2.5]`,
  equity x R exceeds 1 for AA and its flop terminal prices above the whole pot. It is also a mild
  confound in this experiment, disclosed rather than hidden: static restores the cap as well as
  removing the class term, though the cap only binds when equity x R exceeds 1.
- **`base_gates` guards the pair ladder in one direction only.** "mid pairs vs set-miners sane
  (66 <= 1.15 x 99)" passes at 0.8041 against 0.8275, barely, and never asserts 99 >= 66. The gate
  list permits the inversion it reads as guarding.
- **GTOpen's `AGENTS.md` documents the 169-vector index transposed.** It states `index = lo*13+hi`
  suited. Under that reading 76o returns reach 0.998 at a four-bet node and AKo out-plays AKs. The
  correct convention is the fitter's own `class_of`, suited at `hi*13+lo`. This is the exact
  transposition `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` and the extractor warn about, sitting
  in the file an agent reads first.
- **A blocker in this very note has been invisible since 2026-08-30.**
  `loop_stage.unresolved_blockers` closes a bullet when `[resolved]` appears anywhere in its first
  line. Round 2's first blocker opens by quoting that marker in order to say it was wrongly applied -
  "the stage-6 note's `[resolved]` on blocker B2 is false" - so the driver and `review_queue` have
  both counted the open finding as closed. Nothing advanced on it, because two sibling blockers were
  genuinely open and held the stage, so this was silent under-reporting rather than a false green.
  Filed as `RESOLVED-MARKER-MATCHES-INSIDE-A-BLOCKER-S-OWN-PROSE`. The bullet stays exactly as
  written; the checker is what changes.
- **Two UI defects found while reproducing this, both capable of producing a wrong reading of a
  committed artifact.** The `Scenario` preset label does not reset when a save is loaded, so the
  panel reads `HU 10bb push/fold` over a six-handed 100bb game. And `cfg-allinthr` is a hidden input
  with zero width and height defaulting to 85 against the ruled 67, so a rebuild through the form
  silently solves a different tree. The second confirms `extract_gtopen_preflop.py`'s docstring that
  loading the save is the only way to put the exact ruled tree on screen.

## Alignment

- **This question was already filed correctly, three days before the halt, and the halt lost the
  framing.** `CALIBRATED-REALISATION-PRICES-FOUR-BET-POTS-UNTESTED`, status deferred, phase 16, from
  Taylor's 2026-08-27 ruling: "GTOpen resolves flops by scaled equity share rather than playing them,
  and a four-bet pot at 1.7 SPR is where that approximation is weakest." That is this round's
  conclusion. Decision 16 then re-diagnosed the same symptom as a non-monotone table, which points at
  169 numbers instead of at the stack depth they are applied at, and the SPR framing dropped out. The
  entry is not new work waiting on phase 16; it is the diagnosis phase 14 turned out to depend on.
- **What let it slip was reporting the four-bet defence as aggregates.** The 08-27 measurement -
  "96.15 percent of premiums, 99.10 of suited connectors, 43.38 of suited broadway and 1.21 of
  middling pairs" - reads as a coherent polarised range, and polarised four-bet defence is real. But
  1.21 percent of middling pairs is JJ, TT and 99 as pure folds, and 99.10 of suited connectors is
  76s calling on 30 percent equity into a 32.3 percent break-even. Banding a rank inversion turns it
  into a shape that looks like theory. The general lesson is the one
  `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE` already carries: a band aggregate cannot see an
  ordering defect inside the band, so a dominance finding has to be reported at the cells too.
- **The residual, and why this round does not claim the class term is the whole cause.** Under static
  76s still continues 53 percent against JJ's 37. The four pairs carry equities of 31.6, 31.7, 31.7
  and 31.8 - identical - and mix 37, 42, 25 and 37, so the noise floor at this convergence is about
  17 points and the leftover gap is 16. It is inside the noise, where the calibrated gap of 97 points
  is not. That is a bound, not a proof, and the way to close it is the played-flop comparison the
  phase 16 entry asks for rather than a tighter preflop target.
- **The strongest single discriminator is purity, not magnitude, and it is worth stating as a
  reusable test.** Under static these hands sit on the indifference point and mix, and four hands
  with identical equity choosing different mixes is arbitrary tie-breaking working as the 2026-08-24
  dominance ruling describes. Under calibrated, JJ at 40.8 percent equity is a pure fold and 76s at
  29.6 is a pure call. Indifference cannot produce two pure opposite decisions between hands 11
  equity points apart, so "solves have unique strategies" does not cover this shape. A future
  dominance gate could test exactly that: a pure decision on the wrong side of break-even is a defect
  in a way an extreme mixture never is.

# Round 4, 2026-08-31: independent review of round 3

Round 3 was coordinator work and said it owed an independent read-only review before anything it
held could be released. This is that review. The reviewer wrote none of round 3, worked read-only,
ran no gate, planted no mutation, and was fenced off from every endpoint that would have destroyed
the live session. Round 3 stands as written above, per the convention that a round is a
snapshot of what it believed, with one exception stated because round 4 was initially wrong about it:
round 3's own blocker bullet was edited in place to carry a `[resolved]` marker and a pointer here,
which is what `unresolved_blockers` needs in order to close it. That edit is mechanical rather than
revisionist; round 3's prose is otherwise untouched and every correction below is additive.

**The reviewer agreed with round 3's central poker conclusion** - the calibrated four-bet shape is a
mispricing rather than a legitimate polarised defence, and the experiment is real evidence for it -
and independently confirmed the mechanism: every `class_base` value quoted anywhere in the diff, the
v5 pair chain terminating at 99 with 88-22 left free, `std[k] = pik @ leaf` marginalising five
pot-type cells with no four-bet-pot cell, `mod.rs:1137` applying the result undiminished,
`spr0` exactly `0.0`, `base_gates` one-directional, the marker defect in `loop_stage.py:180` in both
its halves, the `AGENTS.md` index transposition, and the node's prices. It also established that the
one confound round 3 disclosed is numerically inert here: the `.min(pot_eff)` clamp binds only when
`eqp * rp > 1`, which under static needs equity above 0.984 while AA's is 0.757, and the gross-pot
versus `pot_eff` difference is inert too because `rake_pct` and `rake_cap` are both 0. It found no
undisclosed mechanical confound. And it recorded a non-finding worth keeping: 77 through 22 continue
21-33 percent at this node while JJ-88 fold pure, which reads as a catastrophic within-family
inversion until you see their arriving reach is 0.000 to 0.005 - they are round 1's unreached cells
and the selection rule already excludes them.

## Blocker

- `[resolved]` **Round 3 misread the object of decision 16's exit condition, and its new blocker was
  wrong as framed.** Decision 16 says "until a source exists whose **postflop pricing** is monotone
  in hand strength". Postflop pricing is the priced terminal - `share = nd.pot * eqp * r` at
  `mod.rs:1138` - not the table. Under an SPR shrink `r` goes to about 1 at SPR 1.67 and the price
  becomes `pot x equity`, which is monotone. So the shrink satisfies decision 16 on the literal
  reading, and round 3's claim that "the lane cannot restart even once the source is corrected" does
  not hold. What is genuinely ambiguous is **quantifier and scope, not object**: universally
  quantified over every SPR the condition is not satisfiable by anything, because at SPR 15 a suited
  connector legitimately out-prices a middling pair and should. Decision 17 is rewritten to ask that
  question instead. The finding is the reviewer's; the rewrite is the coordinator's and has not been
  independently reviewed.
- `[resolved]` **`price-monotone-within-family` was the wrong condition and would have released the
  halt on a chart carrying the identical defect.** Round 3 recommended it. JJ is in the pair ladder
  and 76s is in the 7-high suited ladder, so the JJ-pure-fold against 76s-pure-call comparison - the
  entire reason for the halt - is cross-family and explicitly exempted by the condition's own
  wording. Worse, the prescription the same diff withdrew as damaging, extending the PAVA chains
  over pairs and kicker ladders, satisfies it: chaining makes `class_base` monotone within each
  family, equity already is, so `eq x R` is monotone within family and the gate passes while JJ stays
  at 0.7493 and 76s at 1.1333 and folds jacks exactly as before. The reviewer verified the condition
  is at least not vacuous today - 88 prices at 0.3088 above 99 at 0.2996 and TT at 0.3018, and J6s at
  0.175 under J5s at 0.234 - but necessary is not sufficient, and round 3 presented it as the test
  that releases the halt. The option set in decision 17 is replaced.
- `[resolved]` **The experiment's control arm is unidentified and does not reproduce against the
  committed baseline.** Round 3 says the calibrated arm "matches the artifact on screen, so the
  comparison is against the grids the reviews actually measured" and cites "the baseline's 0.0047".
  The committed export header records `iterations: 300` and `achieved_gap_bb: 0.006237862`; there is
  no 0.0047 in the repo. The reviewer re-measured the live 300-iteration session and got JJ folding
  93.5 percent at the CO node against round 3's 97, continue-share 65.55 against 67.1, and 76s at
  6.97 percent of LJ's four-bet range against 9.0, while the equity column reproduced throughout.
  The reviewer offered, and could not confirm, that the control arm is the session
  **after** the operator re-solved it to iteration 400 rather than the committed 300-iteration export.
  The coordinator confirms it from its own session record - that is a coordinator statement, not a
  review conclusion, and it happens to be the one that most repairs the coordinator's position. That makes the comparison better matched
  than round 3 claimed - 400 against 400, gap 0.0046 against 0.0047 - and makes round 3's sentence
  about matching the reviews' grids false, since those grids are the 300-iteration solve. Both arms
  are 400 iterations of DCFR on the same tree. Recorded here rather than by editing round 3.

## Non-blocker

- **The intervention does not move round 2's third blocker, and round 3 did not say so.** The
  five-bet composition inversion survives: round 3's own static column has KK calling 100 and QQ
  calling 100 while 87s jams 12 and 76s jams 23. The calibrated analogue at the CO node is starker -
  A4s at reach 0.949 jams 54.5 percent while KK jams 2.0 and QQ 0.0. So the experiment moves the
  four-bet defence and leaves the jam composition where it was, which weakens any claim that one
  cause explains all three held-over blockers. The backlog rewrite calling the phase 16 entry "the
  diagnosis phase 14 halted on" is too strong by exactly this much.
- **The residual is bounded by the wrong instrument, and part of it is a known-sign error rather
  than scatter.** Round 3's noise floor came from four pairs mixing 25 to 42 at identical equity. But
  those cells arrive at reach 0.958, 0.881, 0.697 and 0.449 against 76s's 0.998, so the floor is
  estimated from cells with half the traffic of the one under test. The suited family is ordered
  rather than scattered - A5s equity 30.4 continues 39, 87s 28.1 continues 51, 76s 27.9 continues 53,
  so continue rises 14 points as equity falls 2.5. And at least 23 of 76s's 53 continue points sit on
  a jam worth about **-40bb** against -7.5 for folding, robust even if QQ folds to it entirely. That
  is a sign-known error invisible to a tree-wide BR gap because the node arrives about 0.15 percent
  of the time, which is this phase's own `SOLVER-CONVERGENCE-IS-NOT-UNIFORM-OVER-THE-TREE`. Round 3's
  conclusion that a tighter preflop target cannot close this stands; its "inside the noise" does not,
  and its own hedge - "a bound, not a proof" - should have been the claim.
- **Both experiment arms hold `add_allin: true` while the blockers being diagnosed were measured on
  `add_allin: false`, and this is load-bearing for the two findings above.** Round 2's three open
  blockers come from the re-sourced chart, where JJ-88 continue at exactly 0.000 and 76s/87s/JTs at
  exactly 1.000. Round 3 justified holding `true` as matching "the grids the reviews actually
  measured", which is round 1's export rather than round 2's. Under `add_allin: false` there is no jam
  at the four-bet-facing node at all, so 76s's 23 static jam points become calls - which moves the
  residual arithmetic in the finding above it and moves the jam-composition comparison in the one
  before that. The diagnosis probably transfers; nothing has shown that it does.
- **The driver and `review_queue` under-report this note until the tooling item lands, and that is a
  mitigation this task can state even though it cannot fix it.** `unresolved_blockers` closes round
  2's first blocker because it quotes `[resolved]` in its opening line, so the queue's count is low by
  one and the missing one is the blocker that says the defect survived the re-source. Anyone reading
  the queue should read this note's `## Blocker` sections directly. `scripts/` is outside this task's
  `approved_scope`, so the fix is a maintenance lane, not a scope widening.
- **Round 3 leaned on the source for a shrink the source does not support.** "Realization is near 1
  by construction" is true at SPR 0, which is what `mod.rs:7` says; it is not a statement about SPR
  1.67, and the engine gates the calibrated branch on `spr > 1e-9` with no interpolation. More
  pointedly the fit's own `ctx` has `spr1 -0.2283` and `spr2 -0.0469` against the `spr0 0.0`
  reference, so it **measured** the multiplier as higher below SPR 2.5 than between 2.5 and 8 - the
  opposite direction to the shrink round 3 advocates. Round 3's "wiring `b_spr` in would raise R at
  mid SPR" is therefore wrong for buckets 1 and 2. The load-bearing half is still exactly right:
  `spr_bucket(1.67)` is 0 and `b_spr[0]` is 0.0, so wiring it in changes nothing where the defect
  lives. The shrink is a proposal that has to be argued on the poker and settled by a played-flop
  comparison, not something the fit already implies.
- **The backlog rewrite fixed one v4 quotation and left the other, keeping an inference that is false
  of v5.** Both quoted strings came from `fit_phase_c.py:366-369`. The filename was corrected and
  "equity itself still deliberately excluded as a model input" was kept, together with "so nothing
  makes it monotone in hand strength structurally". v5 does anchor on equity: `load_strength()` at
  `fit_phase_c5.py:154-158` is equity against a random hand, `feats` carries
  `[1, s, s^2, suited, pair, straight_windows, hi]`, and every class shrinks toward
  `clip(feats @ beta, 0.35, 1.45)` at `LAMN = 40`. Equity anchoring is structural but weak, which is
  a different and defensible claim. Corrected in `backlog.yml`.
- **Round 3's second UI finding named the wrong element and mechanism.** `cfg-allinthr`
  (`web/index.html:78`) belongs to the **postflop** setup panel and is only read by
  `currentSpotRequest()` at `web/js/app.js:296`; it measures zero because its tab is `display:none`
  while the Preflop Lab is showing, not because it is a hidden input. The real mechanism is that the
  Preflop Lab has no all-in-threshold control at all - `web/js/preflop_lab.js:232` sends `add_allin`
  and nothing else - so serde falls back to `default_allin_threshold()` = **0.85** at
  `mod.rs:108-110` against the ruled 0.67. The conclusion holds and matters, since a five-bet to 67.5
  stays a raise at 0.85 and becomes a jam at 0.67; a fix aimed at round 3's description would have
  edited the wrong file.
- **Two figures were restated without re-measuring, the pattern round 2 flagged twice.** Decision
  16's 1.0129 continuing against 0.7918 folding re-measures at 0.9849 against 0.8022 reach-and-combo
  weighted at the CO node; round 3's "twenty-one percent of four-bets being 87s and 76s" measures
  18.6. Direction and magnitude survive in both cases and no conclusion moves. Both differences are
  consistent with the 300-versus-400 iteration gap in the resolved blocker above.

## Alignment

- **The reusable purity test as round 3 distilled it would over-fire, and the half that makes it
  correct was dropped.** "A pure decision on the wrong side of break-even is a defect in a way an
  extreme mixture never is" is not safe as a gate: a small pair facing a four-bet has raw all-in
  equity above the naive pot-odds threshold and folds pure in correct solves, because it cannot
  realize at low SPR. The sound discriminator is the **inversion** - a pure fold above break-even
  while a strictly lower-equity hand pure-calls at comparable arriving reach. Any dominance gate
  built from this should carry the second clause.
- **Purity answers one of the two counter-arguments, and round 3 credited it with both.** It kills
  the indifference and tie-breaking defence decisively, and the static arm's mixing is what
  indifference actually looks like. It does not kill equity-loses-to-playability, because a large
  playability gap produces pure decisions too. What answers that one is the arithmetic round 3 had
  and did not write down: JJ folding at 40.8 percent into a 32.3 percent price requires JJ to realize
  under **79** percent of its equity, and 76s calling at 29.6 requires over **109**, a 30-point
  spread in the wrong direction at SPR 1.67 - which is just `1.1333 / 0.7493 = 1.51`. Stated that
  way the 2026-08-27 ruling is answered on its own terms, and the whole argument stops depending on
  anyone's read of a grid.
- **The reviewer's independent poker judgment, recorded because it is the thing least reducible to a
  measurement.** SPR 1.67 is where implied odds are smallest and showdown value largest, so the
  correct gradient runs toward pairs and away from speculative hands, and the model has it backwards
  in both directions at once.
- **The band-aggregate lesson is the durable output of this whole exercise.** Reporting four-bet
  defence as "1.21 percent of middling pairs, 99.10 of suited connectors" is what let a rank
  inversion read as theory for three days. Already carried by
  `UNIFORM-ROW-TEST-IS-BLIND-AT-A-BINARY-NODE`.

# Round 5, 2026-08-31: the sampling gap, found by Taylor's question

Not a review round. Taylor asked how any of this reaches postflop, and whether preflop and postflop
being interconnected means a one-off correction for preflop can ever be sound. Chasing that down
found the cause one level below where rounds 3 and 4 stopped, and it changes what the repair is.

## Blocker

- `[resolved]` **Rounds 3 and 4 prescribed a repair that substitutes an argument for a measurement the
  pipeline can already produce.** The shrink is reasoning about what realization must be at SPR 1.67.
  `m5_spots/phase_b.py` can measure it. Its own docstring describes a closed loop - "preflop lab
  solves -> HU flop exports -> realization runs" - in which `solve-cli realization`
  (`solve_cli.rs:242`, "solve each board and append per-class realization") **solves each flop
  exactly** with the postflop CFR solver and records what each class actually collected, and
  `fit_phase_c5.py` fits those observations into `class_base` per pot-type cell. That is the
  preflop/postflop fixed point, already built and already run twice.
  What it has never been run on is a four-bet pot. Every study line in `phase_b.py` is an open, a call
  or a three-bet - `co_open_btn_3bet`, `btn_open_bb_call`, `utg_open_sb_3bet` and the rest - and
  `grep -c _4bet` returns **0**. So the missing four-bet-pot cell that rounds 3 and 4 correctly
  identified is a **sampling gap, not a modelling oversight**, and the repair is to run the existing
  loop on four-bet lines rather than to bolt a correction onto its output. v5 acquired its
  three-bet-pot axis by precisely this route: "Requires round-2 data (phase_b.py --round2: dense
  3-bet-pot lines + the 4-max 7.5x game)". Decision 17 is rewritten with
  `extend-the-fit-to-four-bet-pots` as the primary option and the shrink demoted.

## Non-blocker

- **Postflop does not inherit the defect, which is worth recording because it bounds the damage.**
  `realization`, `class_base` and `RealizationFit` appear only under `crates/solver/src/preflop/`
  plus `query.rs` and `solve_cli.rs`. The postflop solver - `cfr.rs`, `tree.rs`, `game.rs`,
  `best_response.rs`, `evaluator.rs`, `range.rs` - carries no realization model and plays flops
  exactly. `R` is preflop's stand-in for postflop and is used in that direction only, so a wrong `R`
  cannot corrupt a postflop solve. Phase 16 does not inherit it.
- **The shrink keeps a narrower job.** As SPR reaches 0 the terminal becomes all-in and realization is
  exactly 1, which `mod.rs:7` already states. A model that violates its own boundary condition is
  wrong independently of what any refit measures, so `R -> 1 as SPR -> 0` is worth asserting against a
  refitted table as a check. It is a constraint, not the repair.

## Alignment

- **The real objection to the whole approach, stated in Taylor's terms because it is sharper than the
  rounds above.** Preflop and postflop are a fixed point: preflop ranges decide which postflop spots
  arise, and postflop EVs decide which preflop actions pay. Substituting `R` for playing the flop
  breaks that loop, so preflop ranges derived from an `R` that was never measured in the pot type they
  are used in are not consistent with **any** postflop strategy. Once phase 16 gives the bot postflop
  play that can bet, it would be playing preflop ranges premised on one postflop future and then
  playing a different one. That is a better reason to distrust the chart than anything rounds 3 or 4
  argued, and it is the reason the refit beats the patch: the refit closes the loop, the patch adjusts
  one end of a loop that stays open.
- **A method note the next lane should carry.** Three successive repairs were proposed and defeated -
  extend the PAVA chains, price-monotone-within-family, price-follows-equity - before anyone read the
  data generator. Each was a proposal about the shape of the output. The generator explains why the
  output has that shape, and it took one question about mechanism to reach it. When a fitted table
  looks wrong, read what was sampled before arguing about what was fitted.

# Round 6, 2026-08-31: what is live, and what to ignore above

Rounds 3 to 5 stand as written, per the convention that a round is a snapshot. But they converged on
repairing GTOpen's `calibrated` realization model, and Taylor withdrew that whole direction on
2026-08-31: no work is wanted in GTOpen, the bot is what is being built here, and phase 14 was
expected to need a tweak. He was right, and this round is the correction.

**Live:** decision 19. GTOpen ships **three** realization models - `calibrated`, `static`, `raw` -
and the field selecting one is `RULED_CONFIG` in
`src/poker_training_bot/solver_artifacts/gtopen_config.py`, inside this phase's approved scope. Ruled:
solve with `static`. The restart is a contract-update flip of one field on decision 14's precedent,
then a re-export and a re-measure. No solver work by anybody.

**Ignore, as work:** decision 17's refit of the fit, decision 18's fork (deleted the same day), the
SPR shrink of `class_r`, the PAVA chain extensions, the four-bet study lines, and the
`price-monotone` / `price-follows-equity` / `price-inversion-margin` conditions. Every one of them
answered a question this phase does not have to ask.

**Keep, as diagnosis:** why `calibrated` fails here. Its 169 per-class numbers were fitted only on
single-raised and three-bet pots - `NCELL` is 5 with no four-bet cell, and `grep -c _4bet` in the data
generator is 0 - and the engine applies them unchanged at SPR 1.67. That is what makes `static` the
fix rather than a downgrade: the term being dropped is one that was never measured where this phase
uses it. Everything in rounds 3 to 5 that establishes this is sound and independently reviewed.

## Blocker

- No new blocker. Round 2's two remain open and are re-measured against the `static` build rather than
  assumed to have moved.

## Non-blocker

- **The experiment's numbers do not describe the build this ruling produces.** It held
  `add_allin: true` to isolate `realization`, while the ruled config now carries `add_allin: false`
  **and** `static`. That combination has never been solved. Expect the four-bet defence to improve and
  do not expect the reported 37 / 53 percent figures to reproduce.
- **The jam-composition blocker should be expected to survive.** The static arm still had 87s jamming
  12 percent and 76s 23 while KK and QQ flat. `static` addresses the per-class term, and nothing in
  this ruling explains the jam shape.

## Alignment

- **The coordinator's failure here is worth more than the finding.** Three rounds proposed repairs to
  a fitted table, then a refit of it, then a fork to hold the refit, then a change of solver vendor -
  and the answer was a config field in this repo, in this phase's own approved scope, selecting a
  model the solver already ships. Nobody asked what the options were before asking how to build one.
  Rounds 3 to 5 read as escalating competence at answering the wrong question.
