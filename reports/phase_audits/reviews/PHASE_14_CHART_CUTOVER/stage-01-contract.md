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

None new. Round 2's two remain open and are re-measured against the `static` build rather than
assumed to have moved. Stated as prose rather than as a bullet, because a bullet here saying "no
blocker" is counted by `unresolved_blockers` as one.

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

# Round 7, 2026-08-31: decision 19 executed, and what the build says

Coordinator work: the ruling of decision 19 carried out and the build measured. `RULED_CONFIG`
carries `realization: "static"`, the export and the chart are rebuilt from an unmodified GTOpen at
`4aee435`, and round 2's two open blockers are re-measured against the result rather than assumed to
have moved. One worker lane solved, walked and derived, and measured everything below independently
with its own code; the coordinator re-derived every headline figure from the artifact itself, on the
standing rule that a lane's report is not evidence either. Nothing under `data/artifacts/` is
committed: the artifact is writable at stage 6, and the frozen tests that pin the superseded 86-spot
build migrate at stage 4 by the contract's own regression expectation. The build is preserved outside
the tree and the tracked paths are restored.

**The build is sound as a build.** 51 spots from 33,969 action nodes, the census and the three action
menus exactly as the contract states - 35 call/fold/raise, 15 call/fold, 1 fold/raise, prices
`[2.5, 7.5, 22.5, 100.0]`. Achieved gap **0.00015672bb at iteration 1,100** of 2,000 against the ruled
0.00016 target, 0 walk mismatches over 33,969 re-resolved nodes, and the two-process determinism proof
byte-identical at 0 basis points of divergence. The source card names `realization=static` because the
field now derives from `RULED_CONFIG` rather than being typed; it read `realization=calibrated` beside
a `config_posted` saying otherwise until this task, and `config_errors` never reads that sentence.

The build is identified by checksum so a later session can prove it rebuilt the same thing rather than
trusting a number quoted here: export `43a29604b9f99564129390c7622a04dc2fed953bcc6077cfa212accf15fd65be`
by the card's own `export_sha256`, chart weights `de9d62e1342b5add29862393e8f6c4898fde02aee0b8ce3f26c363e92a426d27`
by `audit_fields.weights_sha256`, export file 2,033,258 bytes against the superseded 4,094,221. The
GTOpen save it came from is 98,422,118 bytes at
`2fc257714f8a09cf5275dea6de4549fb0889d33647e317559cca302f37ac07b7`; that file was overwritten by this
build and the `calibrated` save the committed card names, `64d8729a30f758f24e713976ac529bab64c741d22af4b68bdeea424864f27ab5`,
was backed up first and put back, so the committed card still describes a solve a human can load.

**What "preserved" does and does not mean, corrected after round 8.** The chart itself and the 2 MB
export live only in a session-scoped scratch directory that a later session cannot reach, so the two
files committed beside this note are the whole of the in-tree trace, and reproducing the build means
re-solving rather than recovering. The checksums are what make that re-solve *checkable*, which is the
point of quoting them; they are not a copy of the build. The two files are:
`static-build-source-card.json`, the provenance and convergence of the solve, and
`static-build-derived-chart-report.txt`, the human report over the 51 spots. They sit under
`reports/phase_audits/reviews/` rather than `data/artifacts/`, so nothing in the repo reads them as the
committed chart. **One line of that report is false and is left as generated rather than hand-edited:**
its fifth line says the bot "now plays from 86", copied from `chart_provenance.py`'s literal, three
paragraphs above its own census reading 51. That is the defect named under Non-blocker below, and
correcting it inside a generated artefact would hide it.

## Blocker

- **The big blind defends 100.0 percent of hands against a small-blind open, and this build is phase
  10's rejected column.** Measured on the artifact, combo-weighted over all 169 classes, against the
  same figure taken the same way from the superseded chart and from phase 10's decision 2:

  | BB defends vs | this build (`static`) | committed (`calibrated`) | phase 10 `static` | phase 10 `calibrated` | raked expectations |
  |---|---|---|---|---|---|
  | LJ | **76.31** | 27.28 | 72.94 | 27.19 | 22.63 |
  | HJ | **84.51** | 29.92 | - | - | - |
  | CO | **91.46** | 34.12 | - | - | - |
  | BTN | **98.19** | 36.76 | 97.44 | 36.88 | 39.43 |
  | SB | **100.00** | 49.02 | 99.71 | 49.03 | 42.88 |

  The damage is entirely in the flat call: against the small blind, call moves 22.59 to **81.49**
  percent while the three-bet *falls* 26.43 to 18.51; against the lojack, call moves 21.01 to 70.83.
  That is the mechanism phase 10 wrote down - a caller who realizes near-raw equity is almost always
  right to call 2.5 to reach an equity split - and phase 10's decision 2 ruled in as many words that
  **nothing may be committed under this model**, calling it the finding that would otherwise have
  shipped a self-consistent, checksummed, thoroughly reported calling station. Decision 19 does not
  cite that measurement, and the 99.71 figure was sitting in `gtopen_config.py`'s own docstring while
  it was written. **Open, and it is the phase's ruling that has to move, not this measurement.**
- **The jam-composition blocker survives, re-shaped rather than reduced, exactly as decision 19 said
  to expect.** The specific inversion round 2 named is gone - no suited connector five-bets anywhere,
  because they are no longer in hero's three-betting range at all. What replaces it is the same error
  one family across. At `t6/d100/SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` the five-bet range is AA
  at 1.000 and **88 at 0.508 on 9,277bp of arriving reach**, while KK flats 1.000, AKs flats 1.000,
  QQ flats 0.983 and AKo folds 0.937. At `t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5`,
  **55 jams 0.358** at 5,677bp while QQ, JJ, AKs and AKo all flat at 1.000. At
  `t6/d100/BB/HJ:raise@2.5,BB:raise@7.5,HJ:raise@22.5`, **77 jams 0.967** at 4,768bp while KK flats
  1.000 and JJ folds 0.765. A pair of eights stacking off 100bb where kings never do is the error that
  rejected the first cutover, with the ranks changed.
  The sharpest case is not a pair. At all three lojack four-bet lines - `BTN/LJ`, `CO/LJ` and `HJ/LJ` -
  **AQs five-bets for the stack at 0.999 on 10,000, 9,998 and 9,775 basis points of arriving reach,
  while KK, QQ, AKs and AKo every one of them flat at 1.000 on comparable reach.** AJs and ATs jam
  alongside it at 0.74 to 0.999 but arrive at 1 to 345 basis points, so those cells are noise and are
  named separately; AQs is not. A hand that is behind KK, QQ and AKs in every equity ordering that
  exists, taking the most committing action in the game where all three refuse it at full reach, is the
  same defect as the original 44-jam and it is no longer confined to small pairs. **Open.**

Round 2's two blockers stay open and neither is marked resolved, stated as prose because a bullet here
saying so is counted as a third open blocker. The jam-composition one is open on its own terms above.
The rank-dominance one is not marked resolved even though the count improves from 85 to 34, because the
improvement is a property of a build that will not exist if decision 20 answers anything other than
`keep-static-as-solved`, and because what the contract actually gates is the aggregate group form,
which no build has yet been seen to pass. A blocker closed against a discarded artifact is worse than
one left open.

## Non-blocker

- **The four-bet defect the ruling was made to fix is reduced, unevenly, and not by pricing the
  connectors.** Continue frequency at the deep four-bet lines, static against the committed calibrated
  build at comparable arriving reach: at `HJ/LJ`, JJ 0.028 to **0.462** and TT 0.001 to **0.585**; at
  `BTN/LJ`, JJ 0.093 to 0.540 and TT 0.001 to 0.543; at `CO/HJ`, JJ 0.578 to 1.000 and TT 0.002 to
  0.995. No pair sits at 0.000 at any of the fifteen four-bet-facing spots. **Corrected after round
  8's review, because the first draft of this bullet read the best three of fifteen spots as the
  shape.** Over all fifteen, JJ improves at ten, holds at three and **falls at two** - `BB/HJ` 0.289
  to 0.235 and `SB/HJ` 0.409 to 0.166, both of them spots where a low pair jams - and 99 stays under
  0.10 at **nine** of the fifteen, not only at the lojack lines. Round 8 counts seven for that; the
  re-derivation gives nine and the coordinator's figure stands. The connectors were not repriced
  either: 76s is absent from all fifteen and 87s and JTs survive at one, because hero's three-betting
  range no longer holds them - and at that one spot, `BB/SB`, **QJs continues 1.000 on 10,000bp and
  JTs 1.000 on 9,999bp**, so this bullet's original claim that the connectors are absent from those
  spots was false as a general statement and is withdrawn.
- **Strict rank dominance improves, and the improvement cannot be attributed to this ruling alone.**
  Under the relation stated in round 2 - same top card, same suitedness, kickers one rank apart, plus
  adjacent pairs, both classes at 5,000bp or better, wheel-ace family excluded, one point of tolerance
  - measured over the identical 51 spot keys by one implementation run against both charts: **85
  inversions across 31 of 51 on the superseded chart, 34 across 20 of 51 on this build**, from 1,635
  and 1,608 comparisons. The character changes too: the pure 0-versus-1 kicker flips (`J6s` 0.000
  beside `J5s` 0.9978) are gone, and what remains is mixed-frequency pair-ladder inversions at
  four-bet nodes (99 0.040 beside 88 0.731). Two cautions. This implementation does not reproduce
  round 2's coordinator count of 52 on the superseded chart - it gets 85 - so the relation as prose
  admits more than one implementation and only the within-implementation comparison is sound. And the
  `calibrated`/`add_allin: false` chart that scored 54 was never committed, so the only available
  comparison moves two config fields at once and the credit cannot be split between them.
- **The trade this ruling makes, priced by arrival mass rather than by spot count.** Over the 51
  committed spots: the five single-raised big-blind spots carry **57.11 percent** of committed arrival
  mass, the small blind's opening range 25.11, the fifteen three-bet spots 16.00, the fifteen four-bet
  spots **1.58** and the five-bet spots 0.20. So `static` repairs a defect in 1.58 percent of the
  chart's traffic and creates one in 57.11. Both figures come from the artifact's own `arrival_ppb`.
- **Six contract figures this build falsifies, and the first draft of this bullet said two.** Round 8
  found four more and the re-derivation confirms all of them. (1) The reach-noise illustration, which
  is the criterion whose whole purpose is to let a reader tell a trained cell from a barely-visited
  one: the contract says that at `SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` the classes 99, 88 and
  AQs carry **5, 1 and 1** basis points "- noise -" while AA carries 10,000. On this build they carry
  **10,000, 9,277 and 10,000**. It does not read as stale, it reads as the reverse of the truth, and
  88 at 9,277bp at that spot is the same cell this note's own jam blocker quotes. (2)
  `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`, which the contract says was re-measured "**and it did
  not**" move, at a flat band of 19.63 to 22.44 percent: the band here is **70.83, 78.17, 83.13, 86.73
  and 81.49**. (3) The purity statistic: the contract says the re-sourced chart holds 1.323 nonzero
  actions per cell and is 73.0 percent pure; this build holds **1.264** and is **77.4** percent pure.
  Its superseded half reproduces exactly - 2.209 and 21.0 percent over the 51 shared spots, measured
  20.95 - so the drift is confined to the re-sourced half. (4) The same criterion's opener widths, 6.07
  to 28.09 percent, against a small blind opening **51.06**. (5) The solve-target criterion says the
  trajectory first meets 0.00016 at iteration 1,900 of 2,000 "so the cap binds"; under `static` it
  meets it at **1,100**. (6) The schema note that every committed node ships all 169 hand classes: 6 of
  the 51 carry 169 and the rest carry 9 to 93.
  **What matters more than the count.** Every one of the first four was measured on the
  `calibrated`/`add_allin: false` dry run, and that build is neither committed nor preserved anywhere -
  so no artifact in this repo or beside it demonstrates a single one of the levels the contract states.
  They are left unamended because the ruling that decides whether any of them describes the shipped
  build is open, and enumerating them here is what tells stage 4 where to look. A contract naming
  `realization: static` in its narrative while stating `calibrated` levels in its criteria is
  internally inconsistent until decision 20 is answered, and that is the honest description of it.
- **`GTOPEN-NOTES-OMIT-REALIZATION` is what made this collidable.** The config body in
  `docs/GTOPEN_SOLVER_NOTES.md` omits the field, so its default was invisible; phase 10 found the
  default was `static` and rejected it, phase 14 rediscovered `static` as the fix, and neither
  document reads the other. The docstring of the module holding the field carried both facts at once.
- **The gate is red, it is red for two reasons rather than one, and the second cannot be fixed from
  this task.** Measured after the flip, 45 of the 46 registered commands run: 35 PASS, 10 FAIL. Nine of
  the ten are one cause - `config_errors` now refuses the committed export with *two* messages,
  "config field add_allin is True, ruled False; config field realization is 'calibrated', ruled
  'static'", so every command that loads the chart dies at import. Rebuilding the export answers that,
  and it is not the whole of the red: four frozen assertions name the superseded model by name -
  `tests/test_solver_export.py` at its expected config dict and at the source card's `model` string,
  `tests/test_solver_expectations.py`, and
  `test_the_source_card_still_names_the_calibrated_realization_model` in
  `tests/test_chart_cutover_evidence.py` - and the frozen suite also pins 86 spots in three files and
  169 classes at every spot. `tests/**` is outside `approved_scope` by the freeze and the contract puts
  that migration at stage 4, so **no green gate is reachable from this task**, and the halt note's
  earlier claim that the gate is red "until the export is rebuilt" was true of one field and one
  cause. `check_gate_bite` was not run: it exists to prove a green gate bites, its mutations take over
  an hour of pytest runs, and the one time it ran in this lane it left a live mutation in a file
  carrying uncommitted work. The tenth failure, `run_full_quality_gate`, is inherited and its diagnosis
  is corrected in `BACKLOG-VOCABULARY-IN-USE-IS-NOT-THE-VOCABULARY-THE-GATE-ALLOWS`: it reports
  sixteen errors, not the twelve that entry claims, and the four extra are two id-shaped phrases read
  as citations (`P10-D3`, `JJ-88`) and two stale corpus figures. Two commands went from FAIL to PASS
  here, `generate_backlog` and `check_generated_backlog`.
- **The malformed backlog entry that was masking two gate commands is fixed here.**
  `BACKLOG-VOCABULARY-IN-USE-IS-NOT-THE-VOCABULARY-THE-GATE-ALLOWS` was deliberately filed with no
  `phase` field, to avoid adding a thirteenth vocabulary error. `scripts/generate_backlog.py` indexes
  `item['phase']` unconditionally, so the omission raised `KeyError` and turned `generate_backlog` and
  `check_generated_backlog` from PASS to FAIL - worse than the error it avoided, and hidden by the
  lane's own red. `phase: contract-update` is added, which the constants already allow, and the entry
  records what happened. The twelve status/phase errors themselves stay MAINT-29's.

- **The committed artifact ships prose that this build makes false, including one poker claim.** Found
  by the measurement lane. `solver_artifacts/chart_provenance.py` hard-codes "The chart commits 86 of
  that solve's 38,828 action nodes and excludes 38,742 of them" - 51 of 33,969 excluding 33,918 on this
  build - and, separately, "the big blind here folds 50.98 percent of its range" facing a small-blind
  open, which is **0.00 percent** here. That text is copied verbatim into the artifact's
  `audit_fields.notes` beside a `spot_count` that is computed and correct, and the generated report's
  fifth line repeats "it now plays from 86" three paragraphs above a census reading 51.
  `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS` carries the census half and is
  extended here with the second half: the same module states a *poker* frequency as a literal, which
  is not a census figure and would not be fixed by rendering the census. Neither is repaired in this
  task - `chart_provenance.py` is stage-6 scope and outside this `approved_scope`.
- **Two independent measurements agree, and where they differ the coordinator's is recorded.** The lane
  and the coordinator wrote separate implementations and both report 85 dominance violations on the
  superseded chart over the 51 shared keys, 34 on this build, and 96 over all 86 keys - to the unit, so
  the 52/54 of round 2 is a narrower reading of the same prose rather than a disagreement about the
  chart. The one difference: the lane reports 5 spots carrying all 169 hand classes, and the
  re-derivation gives **6** - the five big-blind spots plus `t6/d100/SB/rfi`, where every class arrives
  by construction. The coordinator's figure stands.

## Alignment

- **An ordering is not a level, and this phase has now been bitten by that twice.** Both orderings the
  export was gated on - later position opens wider, the big blind defends more against whoever opens
  wider - hold under this build: 76.31 < 84.51 < 91.46 < 98.19 < 100.00 is monotone in exactly the way
  27.28 < 29.92 < 34.12 < 36.76 < 49.02 is. Phase 10 said the defence ordering "reproduces exactly"
  under `calibrated`, and it reproduces exactly under a big blind that defends every hand. Every
  gated check in this phase is a shape check - an ordering, a census, a menu, a monotonicity - and
  `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` is the entry that says so. The
  contract now carries a level criterion against the expectations file, and it is the only check in
  the phase that would have caught this build.
- **The option space GTOpen offers is now measured out rather than argued about.** `calibrated`
  inverts the four-bet pots, `static` turns the single-raised pots into a calling station, and `raw`
  sets R to 1 everywhere, which is the same failure as `static` with the positional term removed as
  well. No third setting exists. That is not a reason to reopen decision 17's refit or decision 18's
  fork - both are withdrawn and no work is owed in GTOpen - but it does mean the choice in front of
  this phase is which pot type to price correctly and what to do about the other, and that is a
  ruling rather than a measurement. Filed as decision 20.
- **The method note round 5 wrote applies to the ruling as well as to the repair.** Round 5 said: when
  a fitted table looks wrong, read what was sampled before arguing about what was fitted. The same
  discipline applied to the *replacement* would have surfaced phase 10's decision 2 in one grep -
  `99.71` appears in six committed documents and in the docstring of the module being edited - before
  a ruling was taken on where the alternative had been measured.

# Round 8, 2026-08-31: independent review of round 7

Read-only reviewer, wrote none of round 7 and none of the diff. Every figure below was re-measured
from the preserved build with code written for this note, without reading the lane's `measure_lm.py`
or the coordinator's: the `static` chart, its sizing table, the committed `calibrated` chart and the
new source card. No gate command and no `pytest` was run; `check_scope`, `check_file_sizes` and
`check_contracts` pass and the contract still stands at exactly 300 lines.

**Round 7's headline figures reproduce, to the digit, without exception.** BB defence 76.31 / 84.51 /
91.46 / 98.19 / 100.00 against LJ / HJ / CO / BTN / SB and 27.28 / 29.92 / 34.12 / 36.76 / 49.02 on
the committed chart; the call moving 22.59 to 81.49 against the small blind and 21.01 to 70.83 against
the lojack while the three-bet falls 26.43 to 18.51; zero combos folding to a small-blind open, 72o
calling at 1.000. The jam compositions: 88 at 0.5082 on 9,277bp with KK and AKs flat 1.000, QQ 0.9826
and AKo folding 0.9367; 55 at 0.3582 on 5,677bp; 77 at 0.9665 on 4,768bp with JJ folding 0.7655. The
four-bet continues at `HJ/LJ` 0.028 to 0.462 and 0.001 to 0.585, at `BTN/LJ` 0.093 to 0.540 and 0.001
to 0.543, at `CO/HJ` 0.578 to 1.000 and 0.002 to 0.995. Dominance **34 across 20 of 51 from 1,608
comparisons, 85 across 31 of 51 from 1,635, 96 across 40 of 86** - a third independent implementation
landing on the lane's and the coordinator's counts to the unit. Arrival mass 57.111 / 25.106 / 16.004
/ 1.579 / 0.200. Census 51 + 29,104 + 4,814 + 0 = 33,969. Menus 35 / 15 / 1, prices exactly
`[2.5, 7.5, 22.5, 100.0]`, 36 sizing entries and 15 without, 21 named-price-only and 15 jam-only and
**0** offering both. Six spots at 169 classes and the rest 9 to 93, so the coordinator's 6 stands over
the lane's 5. Source card: gap 0.00015672434 at iteration 1,100 of 2,000, 33,969 exported against
33,969 solver action nodes, 0 walk mismatches, byte-identical determinism at 0bp, `4aee435`,
2,033,258 bytes, `model` reading `realization=static` beside a `config_posted` that agrees. **The
measurement half of round 7 is sound and I found nothing wrong with it.** Everything below is about
what was not measured, what was stated selectively, and one option that does not do what it says.

**The poker conclusion is right, and right for a reason round 7 does not give.** A big blind that
defends 100 percent is unshippable, and the steelman fails on arithmetic rather than on taste. Facing
2.5 with 1.0 posted the big blind risks 1.5 to contest a 5.0 pot, so it needs 30 percent equity, and
against a small blind opening 51.06 percent even 72o holds roughly a third of the pot in raw equity.
The 40-to-50 percent of hands every real solution folds there are folded on **realization**, not on
equity - so a model whose R tends to 1 in a 20-SPR pot must defend everything, and 100.00 percent is
that model's signature rather than a solve that happens to be loose. Two corroborations. The three-bet
*falls* to 18.51 while the call rises to 81.49: under near-raw realization you never need fold equity,
so the model prefers calling to raising out of position, which inverts the polarity of the big blind's
whole strategy and is a second independent tell. And the loss is not the bounded realization gap a
playing bot would pay, because this chart's postflop is phase 06's heuristic fallback, so the equity
those 72o calls actually realize is below even the discounted figure the model assumed - the chart
hands the fallback a range it cannot play. For a training artifact it is worse still: the deliverable
*is* the teaching material, and this one teaches the single most common leak in the games it targets.
By the same token the four-bet repair is real poker for a real reason - at SPR 1.67 realization
genuinely is near-raw, so a model with no per-class term has nothing to get backwards - and that is
precisely why it destroys the SPR-20 pots. Decision 20's diagnosis of the mechanism is correct, which
is what makes it a ruling and not a measurement.

## Blocker

- `[resolved]` **`revert-to-calibrated-and-refuse-the-four-bet-spots` does not do what decision 20 says it does,
  and it is the option presented first and argued for.** Refusing the fifteen four-bet spots removes
  them from *lookup*. It does not remove the four-bet-pot terminals from the *solve that produced the
  committed spots*. Every committed three-bet spot - 16.004 percent of arrival mass - and every
  committed single-raised big-blind spot - 57.111 percent - is backward-induced over four-bet-pot
  terminals, so its strategy carries whatever the model got wrong down there whether or not the
  four-bet node itself is committed. This is not a novel objection: it is this phase's own ruled
  principle, stated in the contract in these words - "the approximation bites at *terminals* and a
  node's strategy is backward-induced over every terminal below it" - citing
  `SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS`. Worse, the option borrows the
  multiway precedent - "this is the shape the phase already uses for multiway pots" - while dropping
  the half that makes the precedent work. The multiway predicate was deliberately *restated over
  terminals* on 2026-08-25, which is what caught the 24 of 110 nodes whose history was heads-up and
  whose terminals were not. Restated over terminals here, "exclude the spots the source misprices"
  excludes every node with a four-bet pot below it, which is the entire chart. So "it commits 98.4
  percent of the arrival mass on the model phase 10 verified against an independent solver" is not a
  clean split: it commits 98.4 percent of the mass computed against terminals the same sentence
  declares mispriced, and the size of that contamination is **unmeasured and not acknowledged**. The
  option is not thereby dead - a bounded, measured contamination may well be acceptable, and the
  alternative options are worse in other ways - but it cannot go in front of a `frozen-into-data`
  ruling stated as a clean 98.4/1.58 split. Restate it with the contamination named and its size
  declared unmeasured, or measure it. And note the shape of the list while doing so: option 2 is
  "stated to be rejected", option 3 carries "phase 10's decision 2 already ruled against it", option
  4 "is honest", and option 1 is the only one argued for and the only one presented first. Three
  argued down and one argued up is a recommendation, and this ruling is Taylor's.
- `[resolved]` **Round 7 says "Two contract figures this build falsifies". There are at least five, and that
  enumeration is the list the next session will migrate from at stage 4.** Measured here:
  (1) the reach-noise illustration. The contract states that at
  `SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5` the classes 99, 88 and AQs carry **5, 1 and 1** basis
  points "- noise -" while AA carries 10,000. On this build they carry **10,000, 9,277 and 10,000**.
  That is the same spot and the same class round 7's own jam blocker quotes at 9,277bp two screens
  earlier, and it is the criterion whose entire purpose is to let a reader tell a trained cell from a
  barely-visited one - so it does not read as a stale number, it reads as the opposite of the truth.
  (2) `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`, which the contract says was "re-measured rather
  than assumed to have moved, **and it did not**", at a flat band of **19.63 to 22.44** percent. On
  this build the flat band is **70.83, 78.17, 83.13, 86.73, 81.49**. (3) the purity statistic. The
  contract says the re-sourced chart "holds **1.323** and is **73.0** percent pure"; this build holds
  **1.264** and is **77.4** percent pure. Its superseded half reproduces exactly - 2.209, 21.0
  percent, 1,669 of 3,985 cells over the 51 shared spots - so the error is confined to the re-sourced
  half. (4) and (5) are the two round 7 names, the iteration-1,900 sentence and the all-169-classes
  schema note. A sixth is adjacent: the same flat criterion says the openers are "6.07 to 28.09
  percent wide", and this build's small blind opens **51.06** percent (54.09 on the committed chart).
  All of these come from the `calibrated` plus `add_allin: false` dry run, and that build is
  **neither committed nor preserved** - the `dryrun_a386c77` directory beside the preserved build is
  the `add_allin: true` committed chart at 86 spots, not the dry run - so no artifact in the repo or
  in the scratchpad demonstrates a single one of the contract's stated levels. Leaving them unamended
  while the ruling is open is defensible; publishing a count of two is not, because a contract that
  now names `realization: static` in its narrative and states `calibrated` levels in its criteria is
  internally inconsistent, and the note is what tells the next session where.
- `[resolved]` **Decision 20's evidence bullets are selectively measured, one of them is false, and the strongest
  finding against `keep-static-as-solved` is in the halt note but not in the ruling.** Three parts.
  (a) *False as written*: "no suited connector calls a four-bet at full reach any more, because none
  is in hero's three-betting range", which round 7 states as "76s, 87s and JTs are absent from those
  spots". At `t6/d100/BB/SB:raise@2.5,BB:raise@7.5,SB:raise@22.5` **QJs continues 1.000 on 10,000bp
  and JTs continues 1.000 on 9,999bp**, and 87s is present on 6,774bp. The spot is not itself bad
  poker - JJ, TT and 99 all continue 1.000 there too, against a blind-versus-blind four-bet range -
  but the sentence is the one that turns "the connectors dropped out of the range" into "the four-bet
  nodes are now priced correctly", and only the first of those is true. (b) *Selective*: "the defect
  decision 19 was ruled to fix is largely fixed" rests on the three best of fifteen spots. Over all
  fifteen four-bet-facing spots JJ's continue frequency improves at ten, is unchanged at three, and
  **falls at two** - `BB/HJ` 0.289 to 0.235 and `SB/HJ` 0.409 to 0.166 - and those two are spots
  where a low pair jams, 77 at 0.9665 and 0.5559 respectively. So at the very spot round 7 uses for
  its jam blocker, JJ got *worse*. And 99 stays under 0.10 at **seven** of the fifteen, not only at
  "the lojack lines". (c) *Omitted*: at three of the **five** lojack four-bet lines - `BTN/LJ`,
  `CO/LJ`, `HJ/LJ` - **AQs five-bets for the full 100bb stack at 0.9998, 0.9992 and 0.9991 on 10,000,
  9,998 and 9,775 basis points of arriving reach, while KK, QQ, AKs and AKo every one of them flat at
  1.000**. Stacking off 100bb with a hand dominated by two of the hands that decline it, at full
  reach, is worse poker than any pair inversion decision 20 lists, and decision 20 lists only 88, 55
  and 77. The ExecPlan and the halt note do carry it, and both misstate it: the ExecPlan says "at all
  three lojack four-bet lines" when there are five and it holds at three, and the halt note cites
  "AQs, ATs and AJs jam near 1.000" without reach, where **ATs carries 8, 52 and 1 basis points and
  AJs carries 2, 345 and 166** - two of the three classes it names are noise cells, which is exactly
  the discipline round 7 applies correctly when it quotes 9,277bp and 5,677bp. Fix the ruling before
  it is answered: it is the document a `frozen-into-data` answer will be written onto.

Round 2's two blockers stay open on their own terms, and round 7 is right to leave the dominance one
open rather than close it against a build that may not exist - stated as prose here because a bullet
under this heading is counted.

## Non-blocker

- **The one check the contract actually gates the ranges on was not measured on the build, and on a
  defensible reading it passes.** The contract gates the *aggregate group* form - "the combo-weighted
  play frequency of each pair band and each suited row is at least that of the band or row below,
  over hero's arriving range" - and requires the phase to halt rather than freeze a gate it has not
  seen pass. Round 7 declines to close the dominance blocker partly because that form is one "no
  build has yet been seen to pass", which is true only because nobody looked. Measured chart-wide,
  weighting each class by combos times arriving reach times spot arrival: on this build the pair
  ladder has **5 adjacent inversions, the largest 0.43 points** (TT over JJ 0.16, 88 over 99 0.22, 77
  over 88 0.33, 55 over 66 0.43, 44 over 55 0.18) and the suited-row ladder has **1, of 0.02 points**
  (7xs over 8xs). On the committed chart over the same 51 spots the pair ladder has 4 inversions up
  to **7.27** points (22 over 33) and the suited-row ladder 3 up to **24.54** (5xs over 6xs). At any
  tolerance above half a point this build passes the gate the phase halted for and the committed one
  fails it heavily. That is a real point in `keep-static-as-solved`'s favour and it is missing from
  decision 20, which matters even though it does not change my verdict - an option sheet that omits
  its rejected option's best evidence is the same defect as one that omits its favoured option's
  worst. Caveat, and it is the reason this is not a blocker: the contract's prose admits at least a
  per-spot and a chart-wide reading and names no tolerance, so this is one implementation's answer,
  not the gate's.
- **The reflow that made room dropped the only prohibitive half of the artifact-size criterion.**
  "`data/artifacts` stays inside the 20 MiB cap, which at 51 spots no longer binds. **Exceeding it is
  a halt and a decision, not a number to raise.**" became "...no longer binds; over it is a halt."
  The clause that survived is the one a future session cannot act on wrongly; the clause deleted is
  the one that forbids the wrong action, and it mirrors `AGENTS.md`'s own "Never raise the cap". This
  is the same species as the finding round 2 recorded and closed about the refusal-rate criterion, in
  the same lane, two contract edits later. Nothing else in the diff loses a criterion: the other five
  deletions are pointer prose ("The criteria below carry the arrival and corpus figures"),
  justification ("These survive any rake basis and any solver"), or restatements covered by a
  surviving non-goal ("so nothing here touches it"). I checked all thirteen hunks line by line.
- **The scope widening is justified and the fix is right, and it left its own twin one line above
  untouched.** `scripts/extract_gtopen_preflop.py` joins `approved_scope` to stop the card's `model`
  field asserting `realization=calibrated` beside a `config_posted` saying `static`, which
  `config_errors` never reads - a real hole, one field, correctly derived from `RULED_CONFIG` now.
  But the `discriminator` field immediately above it, in the same dict, is hard-coded prose stating a
  *measurement* - "72o arrives with a reach of about 3.7e-08, which quantises to zero basis points,
  and it still carries a full uniform strategy row at a quarter per action" - which is likewise never
  re-derived per build and likewise unread by any check. It is the same defect class the widening was
  granted for, at line 265 against line 278. Not repaired here and I am not asking for it inside this
  task; it belongs beside `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS`, which the
  diff already extends for the same reason in `chart_provenance.py`.
- **`halt-until-a-source-prices-both` is priced as if a route existed.** It is stated to cost
  "nothing but time" because the machinery "re-runs in minutes against a corrected source" - but
  decision 20's own preamble forecloses every route to a corrected source: 17 superseded, 18
  withdrawn, "no work is owed in GTOpen by anybody", and a vendor change is not on the list. As
  written it is an indefinite halt with no owner and no path, and it leaves live the retired raked
  chart the contract requires **deleted**, which blocks phase 15 onward rather than merely costing
  time. That is a fair option, but it should be priced as what it is. Two options are also absent
  from a list that presents itself as the space: commit all 51 under `calibrated` with the four-bet
  misprice recorded as an accepted limitation - which the contract's own non-goal forbids in as many
  words, so it should be *named as excluded* rather than silently missing, since it is the state the
  phase was in before decision 19 - and re-solve with `max_raises` reduced so the tree contains no
  four-bet pot at all, which is the only option that removes the contamination blocker 1 describes
  rather than refusing around it, at the price of a capped-tree abstraction and a config field the
  contract's non-goal currently freezes. I am not arguing for either. A frozen-into-data ruling that
  claims to enumerate the space should say why they are out.
- **Committing nothing under `data/artifacts/` is the right call, and the build is less preserved
  than four documents say it is.** The reasoning holds on both legs - three of four decision-20
  answers discard this chart, and the frozen tests that pin 86 spots migrate at stage 4 by the
  contract's own regression expectation - and `git status` confirms it: no tracked path under
  `data/artifacts/` moved, the tracked paths were restored, and the GTOpen save the committed card
  pins was backed up and put back. But round 7, decision 20, the ExecPlan and the halt note all say
  the build is "preserved outside the tree" by checksum and none of them mentions that the two
  untracked files now sitting in this reviews directory -
  `static-build-derived-chart-report.txt` and `static-build-source-card.json` - are the only in-tree
  trace of it, or that the chart and the 2 MB export themselves live only in a session-scoped
  scratchpad a later session cannot reach. `keep-static-as-solved` therefore means a re-solve, not a
  recovery. The checksums make that re-solve *checkable*, which is the point and is enough - but say
  which of the two it is, and say the two files are there.
- **This phase's own jam test passes on this build.** Verified: fifteen spots offer the 100bb jam,
  all fifteen are five-bet spots, and **AA takes it at weight 1.000 at every one**, so the criterion
  written to catch the error that rejected the first cutover - "no committed spot where a low pair
  takes the jam and aces do not" - is green on a chart where 88 jams 0.508 at 9,277bp while KK flats.
  Round 7's alignment bullet makes the general case that every gated check in this phase is a shape
  check; the sharp instance is that the one check authored *specifically* against the first
  cutover's rejection does not catch the second cutover's version of it, and this is the second time
  the same test has been confirmed green beside the same error one family across.

## Alignment

- The dominance relation is prose loose enough that this lane has now produced 93, 95, 52, 54, 85, 34
  and 96 from it depending on who implemented it, and the *aggregate* form the contract actually
  gates admits at least a per-spot and a chart-wide reading with no tolerance stated at all. Round 7
  half-notes this ("the relation as prose admits more than one implementation"). The remedy is a
  pinned definition - weighting, reach floor, tolerance, and whether the aggregate is per spot or per
  chart - authored as the gate rather than as prose, and that is stage-4 work on the answer to
  decision 20. **Belongs in `backlog.yml`, not in this note.**
- Every falsified figure in my second blocker has one root cause: a contract criterion that states a
  measured *level* while naming no artifact the level was measured on, so the number outlives the
  build silently. `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` covers the absence of
  an external check; this is the adjacent gap, that an internal level is stated without provenance.
  The general rule worth filing is the one the diff already reaches for in
  `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS`: any number in a governing document
  either names the artifact and checksum it came from or is computed by the run that publishes it.
  **Belongs in `backlog.yml`, not in this note.**

# Round 9, 2026-08-31: what round 8 changed, before the diff was committed

Coordinator, responding to the independent review of round 7 rather than reviewing anything. Round 8's
three blockers are marked `[resolved]` above and this is what was done, so the marker is checkable.
Round 8's own text is untouched.

**Decision 20 is rewritten, not patched.** Its first draft argued for one of its four options and
described that option doing something it does not do, which is the worst combination available in a
`frozen-into-data` item. Fixed: `revert-to-calibrated-and-refuse-the-four-bet-spots` now carries the
contamination round 8 identified - refusing a spot removes it from lookup, not from the solve, and
every committed shallow spot is backward-induced over four-bet-pot terminals, which is this phase's
own `SELECTION-PREDICATE-MUST-BE-STATED-OVER-REACHABLE-TERMINALS` principle turned on the option that
borrowed the multiway precedent without it - and states in as many words that the size of that
contamination is **unmeasured**, along with what would measure it and why the 1.58 percent arrival
figure is not that quantity. The list no longer argues: three options were argued down and one up, and
the item now says it does not recommend one. `halt-until-a-source-prices-both` is repriced as an
indefinite halt with no route and a retired chart left live, rather than as costing "only time". The
two options round 8 found missing are named as deliberately excluded with the reason - committing all
51 under `calibrated` with a caveat, which the contract's non-goal forbids in as many words, and
re-solving at a reduced `max_raises`, which is the only route that removes the contamination rather
than refusing around it and which the non-goals freeze. And the aggregate group dominance gate is now
in the item as evidence *for* `keep-static-as-solved`, which round 8 was right that its absence was
the mirror of the defect it was complaining about.

**Two claims of round 7 were false or selective and are withdrawn in place, marked as such.** The
four-bet bullet read the best three of fifteen spots as the shape: over all fifteen, JJ improves at
ten, holds at three and falls at two, both of the two being spots where a low pair jams. And "the
connectors are absent from those spots" is false at `BB/SB`, where QJs continues 1.000 on 10,000bp and
JTs on 9,999bp. The falsified-contract-figure count went from two to six, with the four round 8 found
re-derived here and one thing added that matters more than the count: all four of the new ones were
measured on the `calibrated`/`add_allin: false` dry run, which is neither committed nor preserved, so
no artifact anywhere demonstrates a level this contract states.

**Two figures where the re-derivation disagrees with round 8, recorded because a reviewer's report is
not evidence either.** Round 8 counts 99 continuing under 0.10 at seven of the fifteen four-bet spots;
measured here it is **nine** - `BB/CO` 0.033, `BB/LJ` 0.064, `BTN/HJ` 0.002, `BTN/LJ` 0.005, `CO/HJ`
0.003, `CO/LJ` 0.005, `HJ/LJ` 0.005, `SB/CO` 0.082, `SB/LJ` 0.040. And round 8's worst suited-row
aggregate inversion on the committed chart is 24.54 points against **23.10** here, on the same
5xs-over-6xs pair; the pair-ladder figures agree exactly at 0.43 and 7.27. Both differences are
weighting choices inside prose that names none, which is the alignment item round 8 filed and which is
now in `backlog.yml` as `DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS`.

**Three things round 8 raised that this task did not fix, and why.** The artifact-size criterion's
prohibitive clause is restored - "exceeding it is a halt and a decision, never a raise" - inside one
line, so the cap is not raised to make room and the informational half about 51 spots went instead.
The `discriminator` field in `extract_gtopen_preflop.py`, which hard-codes a measurement thirteen lines
above the `model` field this task fixed, is left alone and filed: repairing it needs the reach figure
re-derived per build, which is implementation work on a script whose one field this task was scoped to
correct. And the aggregate gate's missing definition is filed rather than authored, because the gate is
frozen at stage 4 against whatever decision 20 answers and authoring it now would freeze it against a
build that may not exist.

# Round 10, 2026-08-31: what GTOpen documents about its own realization models

Not a review round. Taylor asked what the source's authors say about `static` versus `calibrated` and
what each is for. Reading the repository at the pinned `4aee435` answered most of what this lane spent
three weeks deriving, and it moves one contract claim. The evidence and the citations are in decision
20 under "What the source's authors document"; this round records what it changes and files the rest.

Nobody was contacted - `~/projects/gtopen` is a read-only clone with no licence and no contact path -
so "what the owners say" here means what they wrote in `AGENTS.md`, `README.md`, `TODO.md`, the fit's
own metadata and the engine's comments.

## Blocker

None. Stated as prose because a bullet here is counted as one.

## Non-blocker

- **The chart is not rake-free where most of its value is priced, and the contract says it is.** Under
  `calibrated` the engine prices a heads-up flop terminal with chips behind off the **gross** pot and
  skips the rake deduction, because the fit "was measured as net-of-rake EV over GROSS pot"
  (`mod.rs:1122`); `AGENTS.md:49` states the consequence, that the rake dial barely moves heads-up flop
  leaves. So `rake_pct: 0.0` removes rake from the preflop betting and leaves the fit's training rake
  in every calibrated flop terminal. The contract asserts the solve is rake-free and that this removes
  one of phase 08's three explanations for the calling gap; phase 10's decision 2 rests on the same
  premise. Filed as `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` and deliberately not amended
  into the contract yet, because it is true of `calibrated` and false of `static` and decision 20
  decides which ships.
- **`REALIZATION-FIT-TABLE-IS-NON-MONOTONE-IN-HAND-STRENGTH` is a misnomer and the halt inherited its
  framing.** R is realized EV over raw equity, not strength, so 76s at 1.1333 over JJ at 0.7493 is
  correct rather than inverted - a connector collects more than its equity because it flops well, a
  middling pair collects less because it cannot improve. The defect is applying that table where there
  is no postflop play: the module header says R is exactly 1 at an all-in terminal, a four-bet pot at
  SPR 1.67 is nearly one, and the engine path carries no SPR term. The entry is reframed in place with
  its measurements kept; retitling it is deferred because the id is cited from the contract, three
  rounds of this note and two decision items.
- **Two corrections of fact that this note and the halt have both had wrong.** `calibrated` does not
  price every postflop terminal: `mod.rs:1129` gates it on exactly two live players with chips behind,
  multiway keeps the static heuristic because the postflop engine that produced the fit is heads-up
  only, and all-in terminals are R = 1 exact. And the fit's `meta.r2` is **0.1885**, so it explains
  about a fifth of the variance in observed realization - a real signal and a weak one, which no packet
  should describe as a measured model without that number beside it.
- **The author's own caveat names this phase's defect, and it is the strongest argument for the option
  the phase is weighing.** `AGENTS.md:94` tells every study to carry: "calibrated realization is
  pessimistic on no-initiative flatting (call ranges are the soft numbers; folds and value-raises are
  robust)." The four-bet defect is entirely a no-initiative flat-or-fold by a medium pair. Refusing the
  fifteen four-bet spots refuses exactly the decisions the model's author flags as soft.

## Alignment

- **Three weeks of derivation reproduced what four files in the source already said.** The
  `static`-versus-`calibrated` comparison was run and recorded by the author, in a sentence that gives
  the same answer as phase 10's and as this lane's build ("BB defends 50% vs 2.5x ... vs static's
  junk-loving 94%"). The missing four-bet-pot cell is in the fit's own `meta.note` as unfinished work
  requiring round-2 data. The SPR shrink rounds 3 to 5 converged on is in `TODO.md`'s v3 postmortem as
  a causal trap that produced 100 percent open rates. None of that needed an experiment. Round 5's
  method note said "when a fitted table looks wrong, read what was sampled before arguing about what
  was fitted"; the stronger form is to read what the authors documented before deriving it. Filed
  nowhere because it is not a repo defect - it is the reason this round exists.
- **What actually put this phase outside the model's envelope is three things at once, and none is a
  bug.** No four-bet-pot cell; a fit that embeds a training rake this solve does not charge; and a
  validation run on 4-max whose gate asserts "no pair inversions", against a six-handed tree. A phase
  that states which envelope it is inside would have caught this at phase 10's contract stage. There
  is no check anywhere in this repo that compares a committed artifact's config against the conditions
  its source was validated under, and `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` is
  the nearest thing to it.

# Round 11, 2026-08-31: the four-bet contamination, measured

Round 8's first blocker was that `revert-to-calibrated-and-refuse-the-four-bet-spots` was written as a
clean 98.4/1.58 split when refusing a spot removes it from lookup and not from the solve, so the kept
spots are backward-induced over four-bet-pot terminals the fit has no cell for. That was right, and the
size of it was unknown. Taylor asked for the number before ruling. This is it.

A worker lane solved the config that option ships - `calibrated` with `add_allin: false`, everything
else as ruled - against an unmodified GTOpen, walked all 33,969 action nodes, and classified every leaf
below each committed spot by the mechanism that prices it. It reached **0.00015591bb at iteration 1,900
of 2,000** in 240 seconds, which is the figure decision 14 recorded for this build, so it reproduces.
The coordinator re-derived the headline from the lane's per-spot splits independently of its
aggregation, and the two agree at 4.959 percent. Nothing was written into the repo.

**The four-way split of the 36 spots the option keeps, arrival-weighted.** Fold-win **71.69** percent -
somebody folds preflop, there is no flop and the realization model is not consulted at all. All-in
showdown 0.55 percent, priced `R = 1` and exact. Heads-up flop terminal in a single-raised or three-bet
pot, inside the region the fit covers, 26.39. Heads-up flop terminal **in a four-bet pot, outside it,
1.38**. So of the mass the model prices at all, **4.96 percent** is priced outside its fitted region.

**In aggregate it is smallest where the traffic is.** The five big-blind-versus-open spots carry 56
percent of committed arrival and run 1.45 to 3.65 percent contamination; `t6/d100/SB/rfi` carries 22.6
percent of arrival and runs 3.65. The worst kept spots are three-bet spots -
`LJ/LJ:raise@2.5,HJ:raise@7.5` at **14.62**, `HJ/HJ:raise@2.5,CO:raise@7.5` at 14.05,
`LJ/LJ:raise@2.5,CO:raise@7.5` at 13.11 - and each carries under 1.5 percent of arrival. The fifteen
five-bet-jam-facing spots the option also keeps have **zero** model-priced mass: every leaf is a fold or
an all-in showdown, so they are priced exactly. That also corrects the option's own arithmetic - it
refuses 15 spots and keeps 36, and 15 of the 36 need no realization model at all. There is no
five-bet-pot flop terminal anywhere in the tree, because the 3.0 multiplier puts the fifth raise at
67.5bb and `allin_threshold` snaps it, so the out-of-support region is exactly the four-bet pots at
SPR 1.667.

**And the aggregate is the wrong statistic, which is the finding of this round.** Read per hand class
it does not hold, and the direction is the bad one. The measuring lane's verdict on its own number was
**no, not shippable on this measurement**, and it is right.

## Blocker

None new. Stated as prose because a bullet here is counted as one.

## Non-blocker

## Blocker

- **The 5 percent averages the defect out of exactly the part of the range the chart is consulted
  about, and the coordinator's first draft of this round called that "structural rather than
  alarming".** That was wrong and this is the correction. At **all fifteen** three-bet-facing kept
  spots, AA, KK and AKs sit at **100 percent** contamination, and QQ at 100 percent in twelve of them:
  the only way those hands reach a flop with chips behind from those spots is by four-betting, and
  four-bet-versus-call with the top of the range is the one decision those spots exist to answer. Over
  the 1,134 (spot, class) cells at reach 5,000bp or better in the kept spots, 100 cells sit at 90
  percent or above and 116 at 50 or above; the classes are AA at 15 spots, AKs 15, KK 15, QQ 12, 87s 9,
  A5s 9. Nor are the busiest spots clean per class: `SB/rfi`, 28.19 percent of arrival, puts **21.8**
  percent of AA, KK, QQ, AKs and JJ's flop mass in a four-bet pot, and `BB/SB:raise@2.5`, 15.31 percent
  of arrival, puts **41.5** percent of 76s's there. The low spot aggregates come from offsuit trash
  that folds, not from the hands the chart is asked about. **Open: decision 20's revert option cannot be
  put to Taylor as a 4.96 percent exposure without this beside it, and the item is corrected to carry
  it.**
- **The experiment that would settle it needs the one thing that is out of scope.** Mass bounds the
  exposure without measuring the error. What would settle it is an EV comparison: reprice only the
  four-bet-pot terminals defensibly - `R = 1` below SPR 2, which is what the engine already does at an
  all-in terminal and what the module header says is exact - and see whether the kept cells move more
  than the solve's own noise, one basis point of quantisation against a 0.000156bb gap. **No config
  reaches that.** `realization` is tree-wide, so `static` reprices the single-raised terminals too and
  the shallow spots' movement is then confounded; `max_raises: 3` removes the four-bet terminals but
  also removes four-betting as an option, so it changes the strategy space rather than the pricing.
  Repricing one pot type requires editing GTOpen, which Taylor ruled out on 2026-08-31 and which stays
  out. So this may be a question the phase cannot answer from inside its own constraints, and that is
  itself an input to the ruling rather than a reason to prefer the reading that flatters the option.
  **Open.**

## Non-blocker

- **Two supporting facts from the fit that make the out-of-support claim exact rather than inferred.**
  `cache/realization_fit.json`'s `meta.rho_cells` carries cells for `f_srp, i_srp, f_3bp, i_3bp, limp`
  and nothing else - so five cells, no four-bet-pot cell, which is what `NCELL is 5` in round 6 meant.
  And the fit's own SPR buckets start at an edge of **2.5**, so a four-bet pot at SPR 1.667 sits below
  the lowest bucket the fit was estimated on. The applied formula carries neither term: `class_r` is
  `clamp(class_base[k] * pos_weight, 0.2, 2.5)`, and at SPR 1.667 `pos_weight` is 1 within 1.7 percent,
  so a ladder spanning 0.363 to 1.282 is applied at its full spread where it ought to compress toward 1.
- **The `calibrated` plus `add_allin: false` build now exists and is preserved.** Round 8's blocker
  noted that four of the contract's stated levels were measured on a build neither committed nor
  preserved. That build has now been reproduced - same config, same tree at 33,969 nodes, same gap at
  the same iteration - and its full walk is serialised at
  `scratchpad/contamination/walk_calibrated.jsonl.gz`. One of the six figures round 7 lists is thereby
  confirmed rather than orphaned: the solve-target criterion's "first meets it at iteration 1,900 of
  2,000" is exactly right for this build and is falsified only by `static`, which meets it at 1,100.
  The other three orphaned levels - the flat band, the purity pair, the opener widths - are now
  checkable against a real artifact, and that check belongs at stage 4 with the test re-cut rather than
  here.
- **The lane's method, recorded because the number rests on it.** Leaf classification is by the count
  of raises on the path from the root, read off the action labels rather than assumed from depth, with
  a label cross-check that reported **0** mismatches; per-spot probability masses sum to 1 within 5e-8;
  opponents propagate by their reach-weighted average action frequencies at their own nodes while
  hero's own per-class strategy propagates exactly, which is the standard mean-field simplification and
  is why the per-class figures above are hero-side only.

## Alignment

- **A chart that is 72 percent fold equity is a fact worth carrying past this ruling.** Under any
  realization model, most of what the committed chart is worth comes from opponents folding preflop,
  which no model prices. That bounds how wrong any R can make this artifact, and it is the first
  quantity anyone should have asked for when the phase started arguing about realization tables three
  weeks ago. It also says where the model *does* bite - the 26 percent that reaches a heads-up flop -
  and that is exactly the mass phase 16's real postflop solver will eventually price properly.

# Round 12, 2026-08-31: decision 20 ruled, and what it costs

Not a review round. Taylor ruled decision 20 - solve with `calibrated`, refuse the four-bet-facing
spots, commit 36 of the 51 - and said of the residual "can figure out later". This records what was
executed, what the ruling costs in coverage, and the one thing it is blocked on.

**Executed.** `RULED_CONFIG["realization"]` is back to `"calibrated"`. The module docstring now records
`static` as ruled-and-reverted with the measurement that reverted it, so the next reader who reaches
for that field finds the experiment already run. Decision 20 carries the answer, the rejected options
with their reasons, and the fifth cut that was offered and declined - refusing the three-bet spots as
well, which would keep 82.4 percent of arrival and drop every cell that is 100 percent out of support.
The two things the ruling accepts are filed with exits rather than left in prose:
`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` and `CHART-CANNOT-ADVISE-A-FIVE-BET`.

**What the ruling costs, measured on the ruled build rather than assumed.** 36 spots committed, 15
withheld. The menu census over the committed set is **20 call/fold/raise, 15 call/fold, 1 fold/raise**,
21 spots carry a sizing entry and 15 do not, and the distinct raise prices are **`[2.5, 7.5, 22.5]`**.
The census is 36 committed, 15 `source-misprices-four-bet-pot`, 29,104 `source-misprices-multiway`,
4,814 `outside-selection-rule`, summing to 33,969. These are structural properties of the tree, so they
hold under either realization model, and both builds agreed on them.

**The consequence worth stating loudest, because it was not obvious when the ruling was taken.** Hero
can only five-bet where he faces a four-bet, so withholding those fifteen spots removes **every jam
from the committed chart**. The bot will refuse rather than advise a 100bb stack-off. Three things
follow: the jam-inversion canary that rejected the first cutover is vacuous over the committed set and
must be retained against the export instead, or it becomes a check that cannot fail counted as one that
passed; the report prints AA's jam weight at those fifteen as excluded evidence rather than committed
ranges; and the sizing table's two-price schema stays entirely unexercised, since the spot shape that
would exercise it is exactly the one refused.

## Blocker

- **The contract cannot say what decision 20 ruled inside its 300-line cap, and this session tried to
  make it fit incrementally, which is the thing `AGENTS.md` warns against.** The contract must now say
  36 committed rather than 51, carry a third exclusion reason and its census, state that no jam
  survives, qualify the rake-free claim under `calibrated`, and pin the dominance gate's definition. It
  stands at exactly 300 of 300; the draft that says all of it is **323**, after cutting every stated
  level that was measured on a build the phase discarded. `AGENTS.md`'s remedy for a contract at the cap
  is a rewrite that folds its amendments into the criteria they amend, as its own `contract-update`
  task, and never a raised cap - and the previous such rewrite, on 2026-08-30, was Taylor's call rather
  than a coordinator's. **So it is put to him rather than taken.** The draft is preserved at
  `contract-draft-decision-20.md` beside this note, with a header stating what it is, why it does not
  fit and what the rewrite still owes; it is working material and nothing in the repo reads it. The
  committed contract is restored to its last coherent state, so `check_file_sizes` passes and the
  contract's disagreement with the ruling is visible rather than papered over. **Open: needs a yes.**

## Non-blocker

- **Reverting `realization` narrows the gate's red rather than widening it.** `config_errors` now
  reports one mismatch instead of two - `add_allin` only - and the four frozen assertions that name the
  calibrated model by name go back to passing. The gate is still red by design until stage 6 rebuilds
  the export, and no constant was reverted to achieve that.
- **One figure this ruling makes checkable was confirmed rather than left orphaned.** The contract's
  solve-target criterion says the trajectory first meets 0.00016 at iteration 1,900 of 2,000. The
  `calibrated` plus `add_allin: false` build reproduced exactly that - 0.00015591bb at iteration 1,900 -
  so of round 7's six falsified figures, that one is true of the build this ruling ships and was
  falsified only by `static`. The other three orphaned levels are now checkable against a real artifact
  at stage 4.

## Alignment

- **The ruling was taken on a two-line summary and its largest consequence was three levels down.**
  "Everything but four-bet pots" is the right call on the evidence, and it also removes every jam from
  the chart, voids a canary written specifically against the defect that rejected the first cutover,
  and leaves a schema criterion unexercisable - none of which was in front of the person ruling. The
  option sheet in a `frozen-into-data` item should state what each option *removes from the artifact*,
  not only what it commits and what it costs in arrival mass. That is a defect in how decision 20 was
  written, not in the ruling, and it belongs in `backlog.yml` as a rule for future decision items.

# Round 13, 2026-08-31: mechanical review of the contract rewrite

Read-only review of the working-tree rewrite of `docs/phase_contracts/PHASE_14_CHART_CUTOVER.md`
against `git show HEAD:`, by a reviewer who wrote none of it and who is not the poker reviewer running
in parallel. The question asked was the narrow one: **did the rewrite lose or weaken any criterion?**
Every assertion in the old version was traced to where it lives in the new one or established as gone,
and every structural figure was recomputed from the build rather than taken from the contract's word.
Both versions are exactly 300 lines; `check_contracts`, `check_file_sizes` and `check_scope` pass on
the new one. `run_verify`, `check_gate_bite` and bare `pytest` were not run, per the mutation hazard,
and no git command that writes was used.

**What reproduced, computed from `six_max_100bb_rakefree.json` and its sizing table.** 51 selected, 15
ending `:raise@22.5`, 36 committed. Over the committed 36 the declared menu census is **20
call/fold/raise, 15 call/fold, 1 fold/raise**; **21 spots carry a sizing entry and 15 do not**; the
distinct raise prices are exactly **`[2.5, 7.5, 22.5]`**; **no committed spot offers two prices and
none offers a jam**, so `100.0` does leave hero's price menu. The census arithmetic holds: 36 + 15 +
29,104 + 4,814 = **33,969**, and 29,104, 4,814 and 33,969 are the derived-chart report's and the source
card's own numbers rather than the contract's. The tree is 33,969 action nodes and 72,798 total against
the previous card's 38,828, all three confirmed from `extract_stdout.txt` and the two cards. `static`
defends the big blind **100.00** percent, confirmed in `measurements_lm.txt`. The solve target
`0.00016` and the 2,000-iteration cap are on the card. Twenty-four backlog-shaped tokens are cited and
**every one exists in `backlog.yml`**, checked with the gate's own regex and exclusion list; no id the
old version cited was dropped, and five were added.

**One carried-forward figure that could have gone stale and did not.** Line 111 keeps "31 of its 36
keys collide with nothing the new artifact declares and only 5 collide exactly" unchanged while the
artifact shrank from 51 spots to 36. Recomputed against the retired chart at `a386c77~1`: 31 and 5 hold
for both, because none of the 5 colliding keys is four-bet-facing. The figure is right.

**Where the menu census is measured.** 20/15/1 is the **declared-key** census - which actions the spot
offers - not the positive-weight one, which on the `static` build reads 19 call/fold/raise, 1
call/raise, 15 call/fold, 1 fold/raise. That is the same reading the old version's 35/15/1 used, so the
figure is stated consistently and is a property of the tree rather than of the realization model. Worth
knowing at stage 4 so a test is not written against the other reading.

## Blocker

- **The rewrite deleted a prohibition and did not relocate it: "Do not fix the multiway pricing here."**
  Old line 62 forbade two things in one bullet - repairing the source's multiway pricing inside this
  phase, and committing a mispriced spot with the defect recorded as a caveat. New lines 52 to 56 keep
  the second and replace the first with a **different** prohibition, "Do not repair a pricing defect by
  changing `realization`", which is the right bar for decision 20 and is not the same bar. The multiway
  fix now survives only descriptively - "The multiway fix changes GTOpen's `KIND_POT_SHARE` terminals
  and no config turns it off" - which explains why refusal is the answer without forbidding the
  alternative. Nothing else in the new contract closes it: the "and **nothing else**" clause at line 50
  and the `config_posted` criterion at lines 69 to 73 both constrain the posted config, not the solver
  source, and a solver change would show only in `solver.commit` on the card, which no criterion pins.
  Decision 20's own text records the ruling that should be here - "repairing the model is out of scope
  by Taylor's ruling of 2026-08-31" - so the ruling exists and the governing document is now the one
  place it is not written down, which is the split a contract exists to close. This is the **only**
  prohibition the rewrite removed without moving it somewhere else; every other one was checked and is
  present, including the two with history (`never a raise` at line 105, and `A rise outside them is a
  defect, not the cost of a ruling` at line 203). It is not actionable today, since GTOpen is a
  read-only clone, which is why the fix is cheap rather than why it can be skipped: "Do not repair a
  pricing defect here, by changing `realization` or by editing the solver, and do not commit ...".

## Non-blocker

- **Line 96 to 97: "the first" and "the second" mis-refer inside a three-item list.** The sentence
  before enumerates three exclusion reasons - outside the selection rule, mispriced multiway, mispriced
  in a four-bet pot - and then says "One code loses which nodes come back when GTOpen prices each kind:
  a solver fix for the first, a fitted pot-type cell for the second." Read literally, "the first" is
  *outside the selection rule*, which no solver fix returns. The phrasing is lifted from line 238, where
  the antecedent is two backlog ids and is correct. Fix in place: "a solver fix for the multiway one, a
  fitted pot-type cell for the four-bet one."
- **Line 149 wraps mid-word at a hyphen: "suited-versus-" / "offsuit", which renders as "suited-versus-
  offsuit".** New in this reflow; the old version wrapped after the complete word. It is the only such
  wrap in the file, checked mechanically over both versions.
- **The dominance-gate pinning list carries four of the five dispositions the entry it cites names.**
  Line 152 to 154 pins "weighting, reach floor, tolerance, per spot or per chart".
  `DOMINANCE-RELATION-IS-PROSE-AND-HAS-PRODUCED-SEVEN-COUNTS` names those four plus **family
  exclusions** - whether the wheel-ace family is excluded and how - which is one of the four open things
  the entry blames for the seven counts. Adjacency, the entry's other open item, is already ruled by
  decision 10, so family exclusions is the one genuine gap. This is new content, not a loss, but the
  criterion is the one thing standing between the phase and freezing a gate whose definition is prose.
- **The source-card limitation at line 171 to 173 is scoped to "the committed three-bet spots" while the
  entry it cites measures the contamination over every committed spot.**
  `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` says "every committed spot is backward-induced
  over the terminals below it", and reports `t6/d100/SB/rfi` - 25 percent of committed arrival - putting
  21.8 percent of the premium classes' flop mass in a four-bet pot. The contract's wording mirrors the
  entry's title rather than its body, and could be satisfied by naming 15 of the 36. The packet
  criterion at line 275 to 276 ("named individually ... No packet may claim the committed set is priced
  exactly") catches the rest, which is why this is not a blocker; "the committed spots" for "the
  committed three-bet spots" would close it at no cost in lines.
- **Line 163 to 165: 100.00 percent reproduces exactly, and it is the maximum of five rather than a
  level.** Under `static` the big blind defends 76.31, 84.51, 91.46, 98.19 and 100.00 percent against
  the lojack, hijack, cutoff, button and small blind. The contract states 100.00 unqualified. The old
  version's 99.71 had the same shape, so this is not a regression, and the criterion it supports - an
  ordering is not a level - is unaffected. Naming the opener would make it checkable.
- **The solve-target level was deleted under a rationale that does not apply to it.** Old lines 90 to 92
  said the trajectory first meets `0.00016` at iteration 1,900 of 2,000, so the cap binds; the new line
  81 to 82 defers to decision 14. The rewrite's stated method was to drop levels measured on builds the
  phase discarded, but **round 12 of this note recorded that one as reproduced exactly on the ruled
  build** - 0.00015591bb at iteration 1,900 under `calibrated` plus `add_allin: false`. Deleting it is
  permitted by `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT`'s second disposition
  (state a shape rather than a level), and the surviving criterion still requires the card to record the
  achieved gap and iteration, so nothing is unfalsifiable. But the phase paid to verify that number one
  round ago and has now spent it, and the reason given for spending it is not this number's reason.
- **"36" now names two different things and the contract never says so.** It is the retired chart's spot
  count at lines 19 and 111 and the committed count at lines 88, 98, 120, 126, 148, 182, 193 and 240.
  Under the old version, 36 was unambiguously the retired chart. Line 111 - "31 of its 36 keys collide
  with nothing the new artifact declares" - is the confusable one; "its" is doing all the work.
- **Packet requirement lost its specifier without gaining one.** Old line 276 asked for the inheriting
  spots "with the flat-call frequencies as evidence"; new line 275 says "with the frequencies as
  evidence". The change is forced - the inherited defect is now a four-bet terminal, not a flat call -
  but "the frequencies" names nothing, and the criterion is the one that stops a packet claiming exact
  pricing. "with the four-bet-pot mass as evidence" would restore the anchor.
- **The `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` settlement bullet does not carry what ruling
  `calibrated` does to it.** `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` says that if
  `calibrated` is ruled, that entry "gains back part of the explanation phase 14 was going to strike
  off". The rewrite correctly removed the old Scope claim that the rake-free solve removes one of phase
  08's explanations, and correctly added the qualification to the three-explanations criterion at line
  196 to 197, so the substance is carried. The settlement bullet at line 234 to 236 still reads as
  though only the rate changed. Presentation, not a lost criterion.
- **Round 12's blocker is the one this rewrite answers and is still machine-counted as open.** It ends
  "**Open: needs a yes.**" and carries no `[resolved]` marker, so `loop_stage.unresolved_blockers` still
  returns it (one of seven currently open in this file). Whoever holds Taylor's answer should mark that
  bullet, not this one.

**Deliberate absences, judged sound.** The first-cutover narrative and its 24.0 percent and
bit-identical-at-10,000 figures; the multiway equity magnitudes (10.5 points, 14 on the connectors), now
carried as a packet obligation at line 273 to 274; the 5/1/1 basis-point reach example, which sat at a
spot decision 20 withholds and is replaced by a report obligation; the 111-inversions-across-42-of-86
figures; the big-blind-flat band and its deltas, replaced by an explicit "whether it survives is a
result either way"; every agreement-rate and purity level, replaced by "measured at stage 6 against the
committed 36 and none carried forward"; the re-source coverage-cost figures against the superseded 86;
59.5 and 60.8 percent; decision 19 and the five-bet-survival mechanism, both superseded. In each case
the obligation survived and only the level went, which is the sanctioned form.

**Prohibitions and falsifiability clauses checked one at a time and present.** "exceeding it is a halt
and a decision, never a raise" (105); "A rise outside them is a defect, not the cost of a ruling" (203);
"the report must not imply it is populated" (100); "a check that cannot fail must not be counted as one
that passed" (123); "No packet may claim the committed set is priced exactly" (276); "printing the fall
alone states the reverse of the truth" (192); "A caveat does not reach the human at the table; a spot
with no trusted ranges is refused" (54 to 55); "Do not pool the two populations" and "do not read a
residual disagreement as a chart defect while price and realization are uncontrolled" (287 to 289);
"a rate is not a reason to commit one" (288 to 289). "Do not widen the predicate ... to recover
coverage" moved from Forbidden shortcuts to Non-goals (61 to 62) and gained "or lift decision 20's
withholding"; it is relocated, not lost. The jam-inversion canary was retargeted from the artifact to
the export rather than dropped (132 to 133), which is the only move available once no committed spot
jams.

**One change that is a correction rather than a compression.** Line 69 narrows "byte-identical to the
previous card apart from `add_allin` **and `realization`**" to "apart from `add_allin`". That is right:
the committed card at HEAD posts `realization: "calibrated"`, which is what decision 20 restores, so
the ruled re-solve differs from the previous card in `add_allin` alone. The rewrite made the criterion
stricter, and did so correctly.

## Alignment

- **The contract's opening sentence is false of the tree it governs, in both versions.** "The bot plays
  from `data/artifacts/preflop/six_max_nl25_100bb.json`" and "The retired `six_max_nl25_100bb.json` is
  **deleted**" describe a state `a386c77` already left: that file is gone and
  `six_max_100bb_rakefree.json` is committed in its place. Identical in the old version, so not a
  rewrite regression, but the Scope's present tense and the deletion criterion now read as owed work
  that is done, and a reader cannot tell which. It belongs to whatever task reconciles the superseded
  build with the ruled one, not to this rewrite.
- **"Taylor judged its range grids sound" was dropped from Scope, and it is more load-bearing now than
  when it was written.** That judgment was made on phase 10's `calibrated` build. Decision 19 moved off
  `calibrated`, at which point the sentence was stale; decision 20 moved back, at which point it is the
  human vetting behind the ruled model. Losing it costs the contract its only record that a person
  looked at the ranges this phase commits from. Half a line, and a candidate if any line is freed.

# Round 14, 2026-08-31: poker review of the contract rewrite

Independent read of the rewritten `PHASE_14_CHART_CUTOVER.md` as poker, by a reviewer who wrote none
of it and none of the rulings behind it. A separate mechanical reviewer is checking whether the
rewrite dropped a criterion; that is not repeated here. The question here is whether what the contract
commits is fit to put in front of a player, whether the line decision 20 draws is in the right place,
whether the criteria can reject a bad chart, and whether anything the contract asserts about poker is
false.

**What was measured, and on which builds, because the ruled artifact does not exist yet.** The chart
decision 20 ships - `calibrated`, `add_allin: false`, the 36 - has not been derived. Three artifacts
do exist and each answers a different question. `calibrated-build-contamination.json` is a walk of the
ruled solve and settles every structural and terminal-mass fact. `scratchpad/build/six_max_100bb_rakefree.json`
is the ruled tree under `static`, the rejected model, and settles what the shape gates do on the
alternative. `superseded_chart_a386c77.json` is `calibrated` under `add_allin: true`, the first
cutover, and is the only artifact anywhere that shows what the `calibrated` per-class table does to
committed cells. Every number below tagged *(a386c77)* carries that caveat, is a proxy for the ruled
build rather than the ruled build, and reproduces the figures decision 20 and round 11 took from it
where they overlap - LJ's four-bet range at 18.6 percent connectors, the 4 pair inversions at 7.27,
the 3 suited-row inversions at 23.10, BB defence 27.28 to 49.02. The reviewer's own code, no repo code
run, nothing written outside the scratchpad.

**Structural claims checked and true.** The census sums (36 + 15 + 29,104 + 4,814 = 33,969). The menus
over the committed 36 are exactly 20 call/fold/raise, 15 call/fold, 1 fold/raise. 21 carry a sizing
entry and 15 do not, 0 offer two prices, and the distinct prices are exactly `[2.5, 7.5, 22.5]` over
the 36 and gain `100.0` over the 51. The 51 are a strict subset of the 86 with 35 lost and all 35
all-in-facing. Only `SB/rfi` survives as an opening range, so the artifact holds zero non-blind opening
widths. The retired chart limps 13.73 percent from the small blind combo-weighted across exactly 103
classes, and 31 of its 36 keys collide with nothing in the new 36 while 5 collide exactly.
`flop-terminal-5bet-pot` is 0.0 at every node, so the out-of-support region really is exactly the
four-bet pots. Arrival: the 15 withheld spots are 2.92 percent of deals, about one four-bet-facing
decision per 34 deals at the table and one per 205 hands for a given seat.

## Blocker

- **The committed three-bet spots four-bet suited connectors instead of wheel aces, and no criterion
  requires anyone to look before they are frozen.** This is the misprice one node up from the refused
  ones, and it is visible in the cells rather than only in a terminal-mass statistic. At
  `LJ/LJ:raise@2.5,CO:raise@7.5`, a committed spot *(a386c77)*: **JJ four-bets 0.000 and flats 0.999
  while 87s four-bets 0.892 and 76s four-bets 0.534**, AKo four-bets 0.037, and the four-betting range
  is **23.3 percent suited connectors against 3.4 percent wheel aces**. At `LJ/LJ:raise@2.5,HJ:raise@7.5`
  it is 21.3 against 8.6. Under `static` the same two spots four-bet zero connectors. Round 3 already
  said 21 percent connectors "is not a shape any published solve produces"; what is new is that the
  spots carrying it are *committed*, not refused. The contract handles this with a source-card line
  (`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`) and a packet line naming which spots inherit a
  defect. A note about unfitted terminals does not stop a student learning to four-bet 87s. The
  contract already knows the remedy for a level nobody can gate: `STATIC-REALIZATION-UNMEASURED-IN-SINGLE-RAISED-POTS`
  buys the defence level a **human read before the artifact is committed**. The four-bet composition at
  the 15 committed three-bet spots is the cell group the phase's own measurement puts at 100 percent
  out of support, and it gets no such read. Ask for the same thing: print, per committed three-bet
  spot, hero's four-betting range by class with reach, and have a person read it before stage 6
  freezes. If it four-bets 87s at 0.89 while jacks flat at 0.999, that is a halt and a decision, not a
  caveat. Cheap, uses evidence that already exists, and it is the only proposed check anywhere in this
  phase that would catch what decision 20 accepted.
- **"The bot refuses rather than advising a stack-off" is false, and the 15 spots that make it false
  are best responses to the ranges the phase declares unfit to publish.** Criterion at line 129-134.
  Hero cannot *initiate* the last raise, true. But 15 of the committed 36 are five-bet-jam-facing, menu
  call/fold, and at them the chart tells hero to put the last 77.5bb in: at
  `BTN/BTN:2.5,BB:7.5,BTN:22.5,BB:100` it calls AA 1.000, KK 1.000, AKs 0.431, JJ 0.163 under `static`
  and AA/KK/AKs/QQ/JJ at 0.99+ *(a386c77)*. That is advising a 100bb stack-off. Worse than the wording:
  a call-off is nothing but a response to the villain's jam range, and the villain's jam range is
  computed at exactly the four-bet-facing nodes this ruling refuses because it does not trust them.
  Under `calibrated` that jam range is ATs 0.745, TT 0.422, A4s 0.132, 87s 0.240 beside KK 0.995
  *(a386c77)*; under `static` it is AA and AQs at 1.000 while KK, QQ and AKs flat. Round 11's "zero
  model-priced mass, so they are priced exactly" is true of hero's own terminals and does not make the
  cells trustworthy, and decision 20 carried it forward as if it did. Two fixes, both small: correct
  the sentence to say hero can never initiate the last raise while the chart still answers 15 call-offs
  for a full stack, and name the jam-facing 15 as a **second** inheritance beside the three-bet spots,
  so the packet criterion at line 275 cannot be satisfied by listing 21 spots and calling 15 exact.
- **Every gated range check in this phase passes on a chart that never folds, and the build being
  shipped fails the only ranged gate at its own ruled tolerance while the rejected build passes it.**
  Measured chart-wide over the committed 36, combo-weighted by arriving reach and spot arrival, rows
  keyed by high card, which reproduces decision 20's figures over the 51 exactly. **`calibrated`: 4
  pair inversions worst 7.40 points, 3 suited-row inversions worst 23.19 (6xs under 5xs). `static`: 8
  pair inversions worst 0.06, 0 suited-row inversions. A chart edited to fold nothing anywhere: 0 and
  0.** Decision 10's ruled tolerance is one point, so on the only available proxy the artifact decision
  20 ships fails the gate by 23 points and the calling station passes it perfectly. Two further
  adversaries pass it: transpose every suited cell with its offsuit twin and the suited-row ladder gets
  *cleaner* (2 inversions to 0), and set all 156 non-pair classes to a constant 0.5 and the suited-row
  ladder is perfect, because ties are not violations and a flat line is the gate's optimum - `static`'s
  own 8xs through 3xs rows sit at exactly 69.5 each. The rest of the criteria do not compensate: the
  census, the menus and the sizing invariant are structural and hold whatever the weights are; the
  position ordering is checked against the export; the limp rule binds on one spot; and the one level
  check is ungated by construction (line 117, "gated by nothing") and human-read. So the concrete
  wrong chart that passes everything is **the chart this phase already built and rejected**, and it is
  not a hypothetical adversary. Three things the contract must say rather than one. That decision 10's
  tolerance is not met by the artifact and what the phase does about it - the criterion says the phase
  halts rather than freeze an unproven gate, but decision 10's closing paragraph licenses re-deriving
  the tolerance *from* the re-sourced chart, and a tolerance chosen at 24 points to admit the artifact
  it judges is not a check. That the group relation the contract calls "the same dominance over groups"
  is not the group form of the second relation: "suited at least as often as the offsuit twin" has no
  gated form at all, the suited-row ladder is a different assertion, and decision 10 records that the
  aggregate form of the real relation *rewards* a transposed index. And that a flat chart is the gate's
  maximum, so the gate must be read as a regression detector for later phases and never as evidence
  that these ranges are good.

## Non-blocker

- **The strongest argument for refusing the 15 is not the one the contract makes, and it is checkable
  by a non-coding reviewer.** The contract refuses them because the fit has no four-bet-pot cell. True,
  and abstract. The concrete version, at `BTN/LJ:2.5,BTN:7.5,LJ:22.5` *(a386c77)*: **JJ folds 0.907 and
  TT folds 0.999 on ten thousand basis points of reach, while 76s calls 0.997 and 87s calls 0.976**; at
  the CO line JJ folds 0.935 and TT 0.998. And the alternative model is no better in a different way -
  under `static` at the same node **AQs jams the full 100bb at 1.000 while KK, QQ and AKs all flat at
  1.000**, which is round 2's jam-composition defect with the ranks changed. Neither model produces a
  four-bet-facing range fit to show anyone. The packet criterion at line 273-274 already demands the
  multiway exclusion be justified checkably - price offered, equity the model assigns, equity the hand
  has, fold produced. Extend the same sentence to the four-bet exclusion. The table exists in round 3.
- **`CHART-CANNOT-ADVISE-A-FIVE-BET` is not coverage this ruling spends.** Scope and the criterion both
  read as though a capability is being surrendered. The retired chart has 36 keys and **not one of them
  faces a four-bet** - its deepest lines are three-bet-facing. So the bot refuses every four-bet spot
  today, refuses every four-bet spot after this phase, and the refusal rate does not rise there. What
  the ruling forgoes is a capability the phase could have added and did not. That is a materially
  easier thing to defend and the contract should claim it, and it also sharpens the refusal-rate
  criterion at line 200-205, which requires the rate to rise only where the two exclusions and the limp
  account for it: the four-bet exclusion should produce **no** rise against the retired baseline, and a
  rise there would be a defect rather than the cost of a ruling.
- **"The second half is checkable over the artifact and is where the gate belongs" is not true as
  written.** Line 159-162. "The big blind defends more against whoever opens wider" needs the opener
  widths, and the artifact holds zero non-blind opening ranges by the sentence immediately before it.
  The gate must read widths from the export and defences from the artifact, or it is not evaluable. It
  also fails outright on the repo's own external reference, where the button opens 40.56 percent
  against the small blind's 34.41 while the big blind defends 39.43 against the button and 42.88
  against the small blind - because what drives big-blind defence is position and players left to act,
  not the opener's width. It probably survives on this solve, where the small blind opens 54.09 percent
  *(a386c77)* and 51.06 under `static`, wider than any button range this tree will hold. State the
  restriction the first clause already carries, or state that the relation is asserted over the four
  non-blind openers and that the small blind is exempt for a poker reason.
- **The one external level check prints two 20-point gaps that are not defects, and nothing tells the
  reader so.** The expectations file gives SB open 34.41 with a 13.73 limp and BB-versus-SB defence
  42.88 at a **3.5bb** open. The committed chart will show the small blind opening near 54 percent with
  no limp, and defending the big blind against a **2.5bb** small-blind open. Both differences are the
  no-limp ruling, rake-free betting and the price change, and a non-coding reviewer reading line 218's
  "chart against the GTO Wizard expectations" has no way to tell that from a 20-point miss. The report
  already owes named explanations for a residual corpus gap; owe the same for this comparison, and say
  which of the five openers is price-comparable and which is not.
- **The expectations file is the retired chart's own aggregates.** Its five defence figures and its SB
  open and limp rates reproduce the retired artifact exactly to the decimal. That is fine - both came
  from GTO Wizard and it is still the only number this repo did not produce - but the contract's
  "which is what catches a uniformly wrong range" reads as an independent oracle and it is a summary of
  the file being deleted. Worth one qualifying clause wherever the line is next touched.
- **"About 60 combos of 1,326" is 66.3.** Five percentage points of a full 1,326-combo range. The
  rounding runs against the argument the sentence is making rather than for it, so it is imprecision
  and not spin, but the number is used to justify a magnitude band and should be right.
- **The build artifact's own `audit_fields.notes` is templated, not computed.** Both scratchpad charts
  say "commits 86 of that solve's 38,828 action nodes and excludes 38,742" while one of them carries 51
  spots from a 33,969-node tree. Harmless in a scratchpad build, not harmless in a committed one, and
  the census criterion at line 92-100 is about exactly this class of mistake.

## Alignment

- **This repo has no absolute level check on a range anywhere in any gate, and phase 14 is where that
  stops being survivable.** Every gated poker property here is a shape: an ordering, a census, a menu,
  a monotonicity. Shapes are invariant to the two failure modes that have actually occurred - a chart
  that continues with everything and a chart that continues with the wrong things - and both of this
  phase's rejected builds were caught by a person reading grids, not by a check. The nearest existing
  entry is `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL`; it should be restated with
  this phase's evidence attached, because the gate now demonstrably ranks a calling station above the
  artifact being shipped. What would fix it is not more shape checks: it is one gated band per
  headline frequency (SB open width, BB defence per opener, four-bet frequency by class) with the band
  derived from something outside this repo and the derivation recorded. Not phase 14's work.
- **Excluding a spot moves a defect one node up rather than removing it, and the repo can only express
  absence at spot granularity.** Decision 20 states the terminal half of this and the two blockers
  above are the range half: the four-bet composition at the kept three-bet spots and the call-off at the
  kept jam-facing spots are both pure functions of the strategy at the refused nodes. There is no way in
  the artifact to say "this spot's fold and call are trusted and its raise is not", so the phase's only
  instruments are commit-all or refuse-all, and decision 20's option sheet was necessarily a choice
  between two blunt ones. A cell-level or action-level trust annotation is the general fix and it is a
  schema question for whichever phase re-derives this chart against a source that plays flops.
- **The option sheet priced arrival mass and terminal mass and never priced stake.** Facing a four-bet
  is 2.92 percent of deals and roughly one hand in 205 for a given seat, which reads as negligible until
  you note that the EV spread between the best and worst action there is tens of big blinds, against
  fractions of one at the big-blind-versus-open spots that carry 56 percent of arrival. Arrival-weighting
  is the right denominator for a coverage cost and the wrong one for a training artifact's value, and
  every measurement in this phase used the first. Round 12 already filed that an option sheet should
  state what each option removes from the artifact; add that it should state the stake at the decisions
  it removes, not only their frequency.

# Round 15, 2026-08-31: the rewrite does not fit, and what the two reviews found

Coordinator, closing out the rewrite Taylor approved. Rounds 13 and 14 stand as written and their
blockers are open. This records what was fixed, what the reviews changed about the ruling's evidence,
and why the contract is back at its last committed state rather than carrying the rewrite.

**Round 13 found one lost criterion and it was a real loss.** The rewrite deleted **"Do not fix the
multiway pricing here"** and replaced it with a different prohibition about `realization`, so the
governing document became the one place the multiway bar was not written. That is the third time
compression in this lane has eaten a prohibition rather than a description - after the refusal-rate
clause in the 2026-08-30 rewrite and "not a number to raise" in the 2026-08-31 reflow - and it is the
reason this review exists. Restored in the draft, along with the solve-target level round 13 correctly
said was deleted under a rationale that did not apply to it: iteration 1,900 of 2,000 reproduced
exactly on the ruled `calibrated` build, so it is a live figure rather than an orphaned one.

**Round 14 found a sentence of the rewrite that was false, and the coordinator had told Taylor the same
thing.** The draft said the bot "refuses rather than advising a stack-off". Hero can never *initiate*
the last raise, which is what was checked. But **15 of the committed 36 face a five-bet jam** with a
call/fold menu, and at them the chart puts the last 77.5bb in - AA and KK at 1.000, AKs 0.431, JJ 0.163.
So the chart answers fifteen full-stack call-offs. Worse, a call-off is nothing but a response to the
villain's jam range, and that range is computed at exactly the four-bet-facing nodes this ruling refuses
for being untrustworthy. Round 11's "zero model-priced mass, so they are priced exactly" is true of
hero's own terminals and does not make the cells trustworthy; decision 20 carried it forward as if it
did, and so did the summary the ruling was taken on. Corrected in the draft as a **second inheritance**
beside the three-bet spots. `CHART-CANNOT-ADVISE-A-FIVE-BET` is also re-framed on round 14's finding
that it is not coverage spent at all: the retired chart has no four-bet-facing key either, so the
refusal rate must **not rise there**, which is a sharper criterion than the one it replaces.

**Neither review disputes the ruling and the poker reviewer endorses it** - "in a training artifact a
confident wrong answer at the one decision where a stack goes in is far worse than silence, and the
retired chart is silent there too" - while pushing back on what it *keeps*. That pushback is round 14's
first blocker and it is the substantive open item: the 15 committed three-bet spots exist to answer "do
I four-bet", they weigh that branch entirely on the unfitted terminal for AA, KK, AKs and QQ, and on the
only calibrated artifact that exists the answer four-bets **87s at 0.892 and 76s at 0.534 while JJ
four-bets 0.000 and flats 0.999**, a four-betting range 23.3 percent suited connectors against 3.4
percent wheel aces. Its remedy is not to refuse those spots but to buy a human read of the four-bet
composition before stage 6 freezes them, exactly as the contract already buys one for the defence level.

**Round 14's third blocker is the uncomfortable one.** Measured chart-wide at decision 10's ruled
one-point tolerance, the build this ruling ships has 4 pair inversions worst **7.40** points and 3
suited-row inversions worst **23.19**; the rejected `static` build has 8 pair inversions worst 0.06 and
none in the rows; a chart edited to fold nothing scores 0 and 0. So the artifact fails the phase's only
ranged gate by 23 points while the calling station passes it perfectly, a suited/offsuit transposition
makes the row ladder *cleaner*, and setting all 156 non-pair classes to a constant passes outright. The
gate is a regression detector and nothing more, and the contract must say so rather than let a later
reader take a pass for evidence that the ranges are sound.

## Blocker

- **The rewrite does not fit and this is the second session to hit that wall.** With round 13's
  restoration and round 14's corrections the draft is **305** lines against a 300-line cap, and it still
  owes the two criteria round 14 asks for - the human read of four-bet composition, and the honest
  statement of what the dominance gate is - which are another eight or so. Compression is exhausted:
  this session cut the Scope narrative to orientation, replaced every level measured on a discarded
  build with the criterion and the stage it is taken at, merged bullets and reflowed the whole document,
  and the total moved from 323 to 305 while the content that must be added kept pace. `AGENTS.md` says
  never raise the cap and says a contract at the cap is due a rewrite folding its amendments into the
  criteria they amend; that rewrite has now been done and the result is still over. **The remaining
  moves all need a ruling rather than an edit**: drop criteria and say which, split what phase 14
  commits into two phases, or change what the cap covers. The draft is preserved at
  `contract-draft-decision-20.md`; the committed contract is restored to its last coherent state, which
  passes `check_file_sizes` and does not contain the false sentence. **Open: needs Taylor.**

## Non-blocker

- **What the committed contract now asserts that the ruling contradicts, listed so nobody reads the
  restoration as agreement.** It says the predicate's 51 are committed, not 36; it carries two exclusion
  reasons, not three; its census, menu, price and sizing figures are the 51's; and it says nothing about
  the jam, the training rake or the unfitted terminal. All of it is corrected in the draft. Until the
  cap question is settled the decision record is the accurate document and the contract is not.
- **Round 13's remaining findings, all carried into the draft**: the dominance-pinning list gains
  `family exclusions`, the `first`/`second` mis-reference inside a three-item list is rewritten, the
  mid-word hyphen wrap is fixed, and the packet's "the frequencies" goes back to naming flat-call
  frequencies. Its two out-of-scope notes stand: the contract still describes `six_max_nl25_100bb.json`
  as live when `a386c77` already removed it, which belongs to whatever task reconciles the superseded
  build; and round 12's blocker is still counted open, correctly, since the cap question replaced it.
- **Two figures the reviews corrected in passing.** "About 60 combos of 1,326" is 66.3. And facing a
  four-bet is **2.92 percent of deals**, about one such decision per 205 hands for a given seat, which
  is the number the coverage argument should be made on rather than the 1.58 percent of committed
  arrival mass - they measure different things and the contract should not confuse them.

## Alignment

- **Three sessions have now spent their endgame fighting this contract's line cap rather than the
  poker.** The cap is right in general and this contract is a genuine outlier: two re-sources, a
  withholding ruling and four reviews' worth of corrections, all of which are criteria rather than
  narrative. The structural answer is probably that phase 14 is two phases - derive and commit the
  artifact, then run the closing corpus measurement - since the closing-measurement section is 30 lines
  of criteria about a report rather than about the ranges. That is a roadmap question and belongs in
  `backlog.yml` rather than in this note, filed as `PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP`, which
  already exists and should be restated with this measurement rather than closed.
