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
