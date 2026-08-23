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
- **The roadmap's spot counts do reproduce, at a five-entry cap.** `ROADMAP-SPOT-COUNTS-DO-NOT-
  REPRODUCE` says no variation tried reproduces 1,691 and 848. The variation is the entry cap:
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
