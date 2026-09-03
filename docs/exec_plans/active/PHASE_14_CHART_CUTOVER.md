# ExecPlan: Phase 14, Chart Cutover

Contract: `docs/phase_contracts/PHASE_14_CHART_CUTOVER.md`
Lane: worktree `~/projects/poker-bot-worktrees/phase-14`, branch `phase/14-chart-cutover`,
opened from `main` at `28e302d`.
Loop pointer: `verification/loop_runs/14.yml`. Driver: `uv run python scripts/loop_stage.py --phase 14`.

## Objective

Replace the committed 36-spot chart, which was derived from a GTO Wizard export of a raked
game, with one derived from the GTOpen solve phase 10 captured and a human verified. Then rerun
the public-corpus comparison against it and say what the result does and does not establish
about v1's calling gap.

The phase commits data the bot plays from. That is what makes it different from the three
before it: phases 11, 12 and 13 changed what the bot is told and left the ranges alone, and a
wrong range here becomes the reference every later phase is measured against.
`verification/loop_policy.yml` has it `auto_advance: false` for that reason.

## Rulings of 2026-09-02, second batch

Decisions 45 and 46, taken after the fresh review and after the coordinator corrected itself twice in the
course of putting them to Taylor. They supersede parts of 33 and 40 and change the committed set.

**Decision 45, merge.** The bot's flat calls outside the big blind are added to its raise weight rather
than deleted. Deleting was unimplementable: at 9 committed spots the solve puts a hand's whole weight on
`call`, and this chart is 93.9 percent pure so near-indifference offered no way out. Merging loses no
range and lands every non-blind spot inside the standard three-bet band.

**Decision 46, ten percent.** The multiway exposure threshold moves from one percent to ten, measured over
the branches the bot can take. **259** nodes now, 5 first-in / 35 facing an open / 219 facing a three-bet,
carrying **99.09** percent of preflop decisions. It admits the 20 single-cold-caller squeeze spots and
refuses the 22 that already have two or more callers in; there is a real gap in the data between them, 20
under ten percent and the next at 93.

**Two corrections I owed Taylor mid-conversation, both recorded in decision 46.** I said recomputing
exposure over reachable branches would admit the squeeze spots at the same threshold; it admits none,
because the multiway risk there is the two opponents behind rather than hero's flat. And I quoted a
295-node figure that had removed the big blind's call as well, which Taylor keeps. Both were caught before
the ruling was taken, but the pattern is the same one the reviews convicted the earlier codification of:
generalising from one measured node.

**The cap is now a blocker rather than a squeeze.** The contract carries decisions 45 and 46 correctly and
stands at **304 lines against the 300 cap**, at 109 columns with no width left. Five compression passes got
it here and the last three each traded clarity for a line or two, which is what
`PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP` says not to do a third time. The structural fix already
applied - a contract states obligations, the report carries the measurements, the generator validates them
- bought about thirty lines and is genuinely better. It is not enough. This needs a ruling from Taylor
before stage 1 can close: raise the cap, split the contract, or rewrite it at a higher altitude with the
decision record as the authority for specifics.

**Still open, and not to be invented by an implementer.** Taylor has ruled on the pair-ladder inversions
and has NOT ruled on the kicker family, which is 23 real cases after the 43 wheel-ace ones are set aside
as correct poker and the 20 near-ties are discounted. And the `PREFLOP_PRUNE=0` experiment, 200 seconds,
which would show whether any of these inversions are hands the solver left stuck rather than genuinely
preferred, has not been run.

## Re-scoped again after review, 2026-09-02

The 2026-09-01 codification below went to two independent stage-1 reviews, mechanical and poker, and did
not survive. Decisions 40 to 44 are the result and they govern. Read them before anything else here.

**What the reviews broke, and all three were coordinator errors.** The three-clause predicate does not
select 143; two clauses do, and all three select 35. The clauses were never independent - no node fails
the exposure clause while passing the investment clause, so investment is strictly stronger and exposure
inert behind it. The pair-inversion dismissal in decision 32 was checked at one node and is false at two
others, one of them a raise-or-fold menu with no third action to hide in, and the export is 93 percent
pure so mixing was never an available explanation. And decision 32's verdict table was graded on the
passing cases: the three-bet-facing band was a seven-node subset whose omitted member is the family's
largest by arrival and outside the band on two measures.

**What Taylor ruled on 2026-09-02, and decision 44 states it once.** Trust the source except four-bet and
multiway pots. Two filters, 143 nodes, 98.23 percent. The bot never cold-calls a raise; opponents do, so
the solve stays unconstrained. The tight big blind and the pair inversions are both accepted on purpose
with published costs.

**One recommendation of mine was tested and withdrawn.** I proposed narrowing the equity relation to
compare like with like so it could stay a gate. Measured, it fires at 21 of 93 spots narrowed and 22 with
a five-point margin, on `A9s` folded while `87s` and `76s` play - which is correct poker in a three-bet
pot. No form of it is gateable. Decision 42 publishes it un-gated and leaves
`GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE` open, so this phase does not close the gap it was
meant to.

**The contract fits at exactly 300 lines and 109 columns, and how it fits is worth recording.** Three
passes of word-shaving got it to 303 and stalled, which is what
`PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP` predicted. What made it fit was structural: a contract states
obligations, and a measurement pinned in a contract goes stale and forces a rewrite - which is exactly why
this contract has now been rewritten three times. So the measured figures moved to the report, with a
criterion requiring the generator to validate every figure the contract names as an obligation. That is a
better contract, not a compressed one, but it is a convention change that arrived under cap pressure and
it deserves a ruling rather than a precedent set quietly.

**Owed before `--advance`.** A fresh stage-1 review of decisions 40 to 44 and this rewrite, by an agent
that reviewed none of the previous round. The two reviews that produced this are spent: they have seen the
work and are no longer independent of it.

## Unhalted and re-scoped, 2026-09-01 - superseded by the section above

Decision 31 halted the phase on 2026-09-01 and decisions 32 to 39, ruled by Taylor the same day, resume it.
Read those nine items before anything below; the sections after this one describe states that are history.

**What was ruled.** The selection rule cuts by **action**, not by spot (32), which is what supersedes the
withholding cascade of decisions 20, 26 and 28 and the halt taken from it. The chart publishes **no
cold-call answer** outside the big blind, and the solve is deliberately left unconstrained so the villains
in it still flat (33). The big blind's tight defence is **accepted on purpose** (34), because this bot has
no postflop strategy and teaching wide big-blind defence would send a student to flops it cannot help them
play. Facing a four-bet and beyond is **excluded** (35), costing 0.88 percent of decisions. The four-bet
size is left at 22.5 and filed (36), on a ruling that rested on a coordinator error and is put back to
Taylor. The equity relation is **gated with the big blind exempt** and its failing counts published (37).
A chart **ships** (38). Decision 1's live-player clause is replaced by a measured multiway exposure
threshold (39), because the clause excluded four of the five opening ranges to avoid a defect that reaches
at most 0.618 percent of any candidate node.

**What the phase now commits.** 143 nodes - 5 first-in, 15 facing an open, 123 facing a three-bet - carrying
**98.23 percent** of preflop decisions, against the 15.97 percent decision 31 measured for its six spots.
Of the 15 facing-an-open spots the 5 big-blind ones publish fold/call/three-bet and the other 10 publish
fold/three-bet only, which is where decision 33 lives in the artifact.

**Done in this task, all inside the `contract-update` scope already approved:** decisions 32 to 39 appended;
the contract rewritten to the new selection rule at 300 of 300 lines; three backlog entries filed
(`PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS`, `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`,
`MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`); the loop pointer unhalted at stage 1.

**Owed before `--advance`, and not done here.** The stage-1 independent review, mechanical and poker, by an
agent that wrote none of this. `AGENTS.md` is unconditional that the writer never reviews its own work, and
this session was instructed not to spawn subagents, so it is reported as a blocker rather than waived or
self-certified. The reviewer should start at decision 39, which is the newest reasoning and the one whose
weakness is recorded in its own backlog entry, and at the contract's census, whose four buckets are the only
counts here derived by the coordinator rather than by committed code.

**Also owed, and flagged rather than fixed:** the contract sits at 300 of 300 lines and 109 columns, and
`CONTRACT-LINE-CAP-COUNTS-LINES-AND-MEANS-CONTENT` says that width is how a contract buys room under a cap
that counts lines. At 100 columns this text is roughly 330 lines. The rewrite did not widen further than the
one that item was filed against, but it does rely on the same width, and it has no headroom left at all.

## The restart, 2026-08-30

The phase reached stage 6 and was sent back to stage 1. What follows is why, so a fresh reader does
not mistake the earlier sections for the current specification.

Two independent stage-6 reviewers, one mechanical and one on the poker, found that the chart the
build committed stacks off 100 big blinds preflop with a range inverted against hand strength.
At `t6/d100/BTN/BTN:raise@2.5,SB:raise@7.5` aces never jam and 44 jams at 1.0; at
`t6/d100/BB/BTN:raise@2.5`, the second-busiest spot in the chart, aces three-bet to 7.5 and never
jam while AKo jams 0.66 and 44 jams 0.88. Across the 36 spots where any hand can jam, aces jam
0.000 at five spots where 44 jams up to 0.979, and those five arrive in 24.0 percent of hands.
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-06-build.md` carries the full
measurement and is the record of what the reviews found.

The cause is the solve config rather than anything the phase wrote. `add_allin: true` pushes a
full-stack jam onto the raise menu at every node where a raise is legal, with no reference to the
pot, so the big blind can shove 100 to win 4. Running the full 2,000-iteration budget with the flag
still on does not repair it: at 10,000 iterations the bad cell is bit-identical, so it is structural
and not noise. With the flag off the defect is gone and the solve converges roughly forty times
better.

**Taylor ruled on 2026-08-30 to re-source with `add_allin: false` and restart the phase.** The two
constants that carry it, `RULED_CONFIG["add_allin"]` and `SOLVE_TARGET_GAP_BB`, are both
frozen-into-data, so this is a `contract-update` task rather than implementation work.

The superseded stage-6 build is committed rather than discarded, at `a386c77`, on Taylor's ruling.
It is real work and the only record of the two reviews that caught the defect. Its commit message
says it is evidence rather than a base to build on.

**The contract is rewritten rather than amended.** It sits at exactly 300 of the 300 lines
`check_file_sizes.py` allows a contract, so no amendment of any length fits, and about 27 of its
lines carry figures the new source falsifies. Its dormant "What a re-solve owes, if one is run"
section becomes binding, because "no re-solve is run" stops being true. AGENTS.md's remedy for a
contract at the cap is a rewrite that folds its amendments into the criteria they amend; Taylor
ruled on 2026-08-30 that this task perform it. The cap is not raised.

The loop pointer was hand-edited from stage 6 back to stage 1 in `verification/loop_runs/14.yml`,
because the driver has no reverse gear. `stage_base` moves to `a386c77` so the stage-1 review sees
exactly the contract-update diff and nothing of the build behind it.

Two things the restart does not change. The multiway pricing defect stands: only spots with at most
two live players are committed, because the source misprices multiway pots, and that is why the
chart holds so few opening ranges. And `B3`, the rank-dominance inversions, is carried forward as a
measurement to retake rather than as a defect the ruling repairs.

## Halted, 2026-08-30 - resolved, and folded away 2026-09-01

The lane was halted at stage 1 on 2026-08-30 pending a fix to GTOpen's calibrated realization table.
Decisions 19, 20 and 21 resolved it: `calibrated` was reverted to and kept, the four-bet-facing spots
are withheld rather than repriced, and the corpus verdict became phase 17's. The halt narrative was
~130 lines describing a state no longer true, and it was folded away here so the plan fits the 800-line
cap that `check_file_sizes.py` enforces.

Nothing is lost. The full narrative, its measurements and its checksums are in git history at 5793926
and earlier, in the decision record at items 16 to 21, and in the stage-01 and stage-02 review notes
under `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/`. Two facts from it are still live and are
kept here rather than buried: the discarded `static` build's source card and human report are committed
under that review directory, so a re-solve of it is checkable against its checksums; and the GTOpen save
the committed card names was backed up before the re-solve overwrote it and put back afterwards.

## What is already settled, and must not be reopened here

Four things arrive ruled. A phase that relitigates them spends its budget on decisions that
already have answers.

- **Limps leave the solve.** Taylor narrowed roadmap ruling 3 at phase 10's human gate on a
  measurement: limps are 87 percent of the tree, and hero never limps. The committed export is
  `"limp": false`, confirmed in `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json`.
  So the roadmap's 1,691-spot and 12 MB figures are superseded - they were the limps-included
  estimate - and every count in this contract is a no-limp count. The accepted cost is 21 of
  3,048 corpus decision points staying refused, filed as `CHART-CANNOT-ANSWER-A-LIMPED-POT`.
- **Rake-free.** The solve carries `rake_pct: 0.0`, `rake_cap: 0.0`. This is what removes one of
  the two explanations phase 08 offered for the calling gap.
- **Opponent prices abstract to the solved price.** Phase 12's ruling 8, not reopened: the size
  lives in the spot key and the abstraction lives in the lookup, so no corpus decision is lost to
  a price the chart was not solved at. `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md` says in
  as many words not to reopen it and not to add a second solved opening price.
- **The export is not graded against GTO Wizard.** Phase 10 re-ruled that after Taylor ran the
  solver himself: a threshold over the gap between two programs measures two products. The
  closing verdict on the solve was a human reading range grids, and it has already happened.

## What this phase must decide, and what it must not

The judgment calls go in `reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md`
at stage 2, each declaring `frozen-into-data` or `runtime-reversible`. Stage 1's two independent
reviewers found six between them that the first draft of the contract had left implicit:

- **The selection rule, and it is the phase.** The export cannot be committed whole and should
  not be. It holds 38,828 action nodes against roughly 2,100 spots of headroom under the 20 MB
  cap, and its deep nodes are unconverged: GTOpen's target is a summed best-response gap over the
  whole tree, so a 0.01bb target constrains nothing where mass is negligible. The published
  four-bet node folds JJ 97 percent, TT and 99 and KJs outright, and calls 76s outright, at 64 to
  100 percent arriving reach. One dominance violation across the ten shallow reference nodes;
  42 at that one node. `frozen-into-data`, and it rests on reach rather than on bytes.
- **The non-monotone pair**, `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`: the lojack opens 44 at
  72.81 percent while opening 33 and 22 outright. The contract now permits only that entry's own
  two remedies, so this decision is which one.
- **The realization bias**, `REALIZATION-MODEL-UNDERPRICES-POSITION`: the big blind folds 50.98
  percent facing a 2.5bb small-blind open from a 54 percent range, needing 30 percent in
  position. Accept and record on the source card, correct with a stated adjustment, or solve
  elsewhere. It is the third candidate explanation for the calling gap and the measurement cannot
  separate it.
- **The prediction, per opener and with a magnitude band.** The aggregate version is falsified in
  advance: defence widens against four openers and comes back 2.67 points tighter against the
  button, which generates the most defending decisions in the sample.
- **Whether the artifact declares a blind structure**, which `BLIND-STRUCTURE-VARIANTS` and
  `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` both want and which is cheapest in the
  one phase that rewrites the artifact.
- **Whether cells carry arriving reach.** The schema has no field distinguishing a cell the
  solver trained from one it barely visited, which is the same information a refusal carries.

Settled by the contract rather than left to this list: the retired chart is deleted rather than
left to a duplicate-key collision, because 17 of its 36 keys do not collide - it three-bets to 8,
11 and 13.5 and opens the small blind to 3.5 where the export uses 7.5 and 2.5 - so the library
would build clean with both loaded and the bot would answer every three-bet spot from raked GTO
Wizard ranges while believing it plays the rake-free solve.

## Scope

Approved at stage 1 (`contract-update`), which is where this plan is written:

- `docs/phase_contracts/PHASE_14_CHART_CUTOVER.md`
- `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/**`
- standing scope only for `CURRENT_TASK.yml`, `phase_status.yml`, `backlog.yml`,
  `verification/loop_runs/**`, the generated docs, `docs/exec_plans/**`, `reports/active/**`

Expected at later stages, each needing its own `scope_change_log` entry when it is opened:

- stage 2: `reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md`
- stage 4: `tests/**`, `verification/mutations.yml`, `verification/freeze.lock`, and
  `scripts/run_verify.py` (command registration only). `tests/**` as a whole rather than this
  phase's own three files, because the contract's regression expectation requires every frozen
  test of a completed phase that asserts against the chart's contents to be migrated here, before
  the freeze, rather than repaired afterwards - which phases 11 and 12 each deferred and each paid
  a separate repair task for.
- stage 6: `scripts/convert_preflop_export.py` and whatever module the conversion grows into,
  the report generator this phase declares, and `data/artifacts/preflop/**` - the one stage in
  this phase's life where the committed artifact is writable
- stage 9: `reports/phase_audits/PHASE_14_CHART_CUTOVER.md`

Forbidden throughout: `AGENTS.md`, the check scripts, `data/samples/**`, and `tests/**` from
stage 5 onwards. The corpus is evidence and this phase does not get to edit it.

## Delegation Plan

### Stage 4 re-cut against the 249, 2026-09-02 - ACTIVE

The frozen tests describe a six-spot set, and before that a 143-node one and an 86-spot one. Both are
superseded. Nearly every module constant in this phase's eight files is now false: the committed count, the
raises-faced histogram, the refusal vocabulary (three `derivation:*-four-bet-*` codes replaced by
`multiway-exposure-above-threshold`, `big-blind-squeeze-spot`, `beyond-committed-raise-depth`), the retired
chart's name, the price list, the relation count and the arm count. This is a re-cut, not a repair.

**The driver cannot see this.** `check_tests_authored` asks only that the phase's `pytest_*` command is red
on an assertion, which it already is. It has no way to tell a test that describes the 249 from one that
describes six. Do not read "this stage's checks pass" as the stage being done.

**Six worker lanes, one owner per count, no lane reviews its own file.** Each lane owns whole files and
rewrites them against the contract, keeping the conventions the earlier cuts earned: a file's docstring
states what it owns; counts are recomputed from the export by a walk written in the test file rather than
imported from the rule under test; `vacuous()` is called only after an assertion that the vacuity premise
still holds; sibling files import a count's owner rather than copying it.

| lane | files | owns |
|---|---|---|
| L1 selection and census | `test_chart_derivation.py` | the two filters each alone, the third clause, no clause co-extensive with another, the four-bucket census summing to 33,969, the closed reason vocabulary and its disjointness from the runtime miss codes, exposure measured by a walk to leaves with the admitted and refused extremes |
| L2 artifact shape | `test_derived_chart.py`, `test_chart_conversion.py` | byte-for-byte reproduction and `--check`, the retired chart absent from the directory, its glob and `sizings/`, 249 keys checked key by key, the two-directional sizing invariant, prices exactly `[2.5, 7.5, 22.5]`, sizes read from action labels via a perturbed synthetic export, the blind-structure refusals, the merged-flat menu shapes 5/20/219 and defence to the basis point, the no-limp schema rule, zero uniform-initialisation rows under both readings, zero-reach classes dropped |
| L3 arrival and reach | `test_chart_arrival_probability.py` | reach as the plain mean over 169 classes with no reach floor selecting cells, arrival as one left-to-right product rounded once at the end, arrival above one refused at construction, arrival claimed for an undeclared spot refused, the grain printed with its zero count, and the zero-arrival case asserted non-vacuous |
| L4 relations and arms | `test_chart_cutover_evidence.py` | the four relations at one point tolerance with 132 row comparisons on a full grid, the fourth on the raise weight, none gated as an order, both arms strict with a tie refusing, ten partitions, the rank arm scored only over spots closed under reversal with the unscored count published, the five-spot floor publishing rather than asserting, and the discrimination test where a rank-reversed chart passes the suit arm and fails the rank arm |
| L5 report and validators | `test_derived_chart_report.py`, `test_derived_chart_report_validators.py` | every figure the contract names as an obligation being printed and re-derived, the generator exiting non-zero when one does not hold, the three vacuous labels, the equity relation labelled as gating nothing, the cutover ledger balancing, the refusal inventory, the old-versus-new disagreement count with its direction rows |
| L6 migration and canaries | `test_preflop_committed_charts.py`, every frozen test of a completed phase that asserts against the chart's contents, `verification/mutations.yml`, `scripts/run_verify.py` | the migration the contract requires before the freeze rather than after it, and the two mutation canaries authored before the implementation - one proving a wrong artifact fails the command rather than being rendered, one committing a spot above the exposure threshold |

**Reviews.** Two read-only reviewers at the end of the stage, one mechanical and one on the poker, neither
having written any of it and neither having seen the other's work, writing to
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-recut-review.md` under `## Blocker`,
`## Non-blocker` and `## Alignment`. A blocker holds the stage until it is marked with the bare literal
`[resolved]`; an alignment item goes to `backlog.yml`.

### The numbers a lane may use, and where each is ruled

No lane invents a count. Anything not on this list is measured by the test's own walk of the export.

- **249 committed** = 5 first-in + 25 facing an open + 219 facing a three-bet. Census 249 + 348 + 10 +
  33,362 = **33,969**. Coverage **98.5949** percent = 51.9237 + 38.5422 + 8.1290. Contract, decision 49.
- Exposure threshold **ten percent**; widest admitted **9.8642**, narrowest refused **10.0234**. Decision 46.
- Of the 25 facing an open, **5** are big blind and publish fold/call/raise; **20** merge and publish
  raise-or-fold; the merge moves **165** cells, **40** of them pure on the entire-weight reading and **73**
  at 99 percent or more. Decisions 45, 53.
- Cells at non-zero reach **18,431**; pure-call **748** entire-weight, **1,179** at 99 percent or more;
  **93.20** percent of cells pure at 99 percent or more, **3.85** percent mixed below 90. Decisions 49, 53.
- Prices exactly **2.5, 7.5, 22.5**, one per spot. Hero's own jam lives only at the excluded four-bet-facing
  spots, so the jam canary runs against the export.
- Arrival: **44** of the 249 round to zero in parts per billion under `round(p * 1e9) == 0`; only **2** are
  exactly zero. Decision 53, `A-SIXTH-OF-THE-COMMITTED-SET-IS-ALMOST-NEVER-DEALT`.
- Arms, ten partitions, solved against counterfactual - suit arm on spots, rank arm on cells over closed
  spots: whole set 7/167 and 64/206 over 83 closed; raises 0, 0/5 and 11/61 over 5; raises 1, 0/25 and
  21/112 over 25; raises 2, 7/137 and **32/33** over 53; LJ 7/32 and 1/9 over 1; HJ 0/15 and 3/14 over 2;
  CO 0/18 and 6/21 over 5; BTN 0/28 and 9/33 over 12; SB 0/36 and 15/54 over 25; BB 0/38 and 30/75 over 38.
  LJ and HJ fall under the five-spot floor and publish rather than assert. Decision 53.
- Solve card: target **0.00016**, cap **2,000**, first met at **1,900**, achieved **0.00015591**.
- Retired chart: **86** spots, **36** carrying a sizing entry, all 36 priced at a jam. Decision 53.

**The rank arm's one-cell margin is the fragile thing in this stage.** It passes the 219-spot partition 32
against 33. Its restriction to spots closed under reversal is load-bearing - over all 219 spots it reads
149 against 69 and fails. A lane that finds the arm red does not adjust the tolerance, the closed-spot
definition, or which comparisons count. It halts and says so.

### The import shape, which is not optional

Stage-4 tests import names stage 6 will create, and there is one shape that is red for a reason the driver
accepts without freezing a lint error. For a name being added to a module that already exists, import the
**module** and reach the attribute at the point of use: a missing attribute is a per-test `AttributeError`
rather than a collection error. For a module that does not exist at all, put `import ... as module` in the
**function body**, which isort does not sort, so it lints identically on both sides of stage 6 and raises
the `ModuleNotFoundError` naming `poker_training_bot` that `red_for_the_right_reason` accepts.
`from pkg.sub import missing_module` raises `ImportError`, which the driver refuses **and** which
interrupts collection so that no assertion in any file runs - which is how a previous cut froze a completed
phase's 32 tests having never executed them once. Every lane runs the registered command itself and greps
for `Interrupted: N errors during collection`. `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`.

### Stage 4 re-cut, 2026-09-01 - superseded, folded away 2026-09-01

The four-lane stage-4 re-cut against the six-spot set ran and landed at 30 failed / 82 passed / 4 skipped,
every red an assertion. It is superseded: decisions 32 to 39 replace the six-spot set with 143 nodes, so the
tests are re-cut again against the new selection rule. Nothing is lost - the lane assignments, the three
findings the lanes returned against the coordinator, and the two conventions adopted from them (a `vacuous()`
helper placed after an assertion that the vacuity premise still holds, and one owner per count) are in git
history at 09c23a1 and earlier and in the stage-04 review notes. The R4 no-delegation exception and the
argument for it stand as written and are not re-argued.

### The phase-level lanes, as originally written


- Worker lanes: L1 the GTOpen tree walk, the three-way node census, and the reach statistics the
  selection rule is ruled against; L2 the converter, from node payloads to artifact rows at the
  v2 vocabulary, plus the retirement of the old chart; L3 the sizing table rederived from the new
  source - the expectations file is external and stays put; L4 the corpus comparison rerun and
  its report; L5 the phase's own tests and canaries, authored at stage 4 before any
  implementation.
- Ownership: L1 owns the walk and the census it publishes; L2 owns
  `scripts/convert_preflop_export.py`, the artifact it writes, and the deletion of
  `six_max_nl25_100bb.json`; L3 owns the sizings file under `data/artifacts/preflop/`; L4 owns the
  closing measurement and the report generator; L5 owns `tests/**` at stage 4 only. The
  coordinator owns `CURRENT_TASK.yml`, the contract, this plan, `backlog.yml`,
  `verification/mutations.yml`, command registration in `scripts/run_verify.py`, every merge, the
  gate, and the audit packet.
- Expected outputs: each lane returns a patch confined to the files it owns, the commands it ran
  with their output, a changed-file summary, and the frozen tests it made pass or found failing.
  L1 also returns the enumeration as data rather than as prose, because every later lane's
  denominators come from it. L4 returns the measurement with its prediction stated before the
  numbers.
- Status: stages 1 to 3 were coordinator work by construction - a contract, a decision list and a
  human gate are each a single document, and splitting their authorship produces a document with
  two voices and no owner - and two independent read-only reviewers read the contract before
  stage 2 opened. Stage 4 is the first delegated stage. Four lanes ran concurrently on disjoint
  files: three authoring one new test file each, and a fourth migrating the frozen tests of
  completed phases that the cutover makes false. The coordinator kept `CURRENT_TASK.yml`, the
  command registration, `verification/mutations.yml`, this plan and the review.
- Integration order: L1 first and alone, because the census and the reach distribution are what
  the selection rule is ruled against at stage 3 and what every other lane counts against. Then
  L2, then L3 in parallel with L2 once the artifact's shape is fixed, then L4 last, because the
  closing measurement is not real until the artifact it measures is committed. The coordinator
  runs the phase's own commands after each merge and the full gate only after L4.
- Status, second contract-update (2026-08-24): coordinator work by the same argument as stages 1
  to 3 - the contract, the decision record and this plan are single documents. Two independent
  read-only reviewers ran concurrently on the finished diff before it was committed, one
  mechanical (re-measuring every count in the new text against the committed export, and checking
  the rewrite dropped no criterion the previous contract carried) and one on the poker (whether
  "at most one opponent voluntarily invested" is the right line, whether the unconverged four-bet
  continuations should ship, and whether decision 6 still makes sense on the new set).
- Status, stage 6 (2026-08-27): five lanes, run in three waves because the dependencies are
  real rather than stylistic. Wave 1 is one lane on the container - `lookup.py`'s two exclusion
  codes, `schema.py` at version 2 with `BlindStructure`, `arriving_reach_bp`, `arrival_ppb` and
  the no-limp rule, the importer that reads them, and `preflop_sizing.py` at the per-class
  shape - because every other lane imports those names and two lanes inventing them
  concurrently produces two shapes. Wave 2 is one lane on `chart_derivation.py`, the converter,
  the committed artifact, the sizing table, the deletion of the retired chart and the source
  card's restamped size block; it is one lane rather than three because the artifact, its
  sizings and its census come out of one `derive_chart` call the frozen tests read as a unit.
  Wave 3 is three lanes on disjoint files over the artifact wave 2 committed: L3C the report
  generator and its four validators, L3D the runtime price draw in `preflop_chart.py` plus
  phase 08's `comparison.py`, L3E the three other completed-phase gate commands
  (`generate_preflop_strategy_report.py`, `repo_facts.py`, `vocabulary_report.py`) and the
  re-measured `CORPUS_REFUSALS` in `table_state/measures.py`.
- Ownership at stage 6: L1 owns `solver_artifacts/{schema,lookup,importer}.py` and
  `strategy/preflop_sizing.py`; L2 owns `solver_artifacts/chart_derivation.py`,
  `scripts/convert_preflop_export.py`, `data/artifacts/preflop/**`; L3C owns
  `scripts/generate_derived_chart_report.py`; L3D owns `strategy/preflop_chart.py` and
  `data_pipeline/{comparison,comparison_report}.py`; L3E owns
  `scripts/generate_preflop_strategy_report.py`, `scripts/repo_facts.py`,
  `solver_artifacts/{vocabulary_report,vocabulary_measures}.py` and `table_state/measures.py`.
  The coordinator owns the waves, the integration, the gate, `CURRENT_TASK.yml`, this plan and
  the review notes, and writes no implementation itself.
- Operational rules given to every lane: `tests/**`, `verification/mutations.yml` and
  `verification/freeze.lock` are read-only and outside `approved_scope`; the canary `find`
  strings in `verification/mutations.yml` are a specification and are written verbatim,
  indentation included; no lane runs a bare `pytest` or two mutating invocations at once, and
  `check_scope.py` runs after anything that may apply a mutation.
- Review handoff: an independent read-only reviewer reads the stage diff against the question
  the driver prints, writes to
  `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-NN-name.md` with the three required
  headings, and never edits what it reviews. Stage 6 gets two, one mechanical and one on the
  poker, and the poker reviewer is briefed to judge the ranges rather than the code's fidelity
  to the contract - a chart that converts cleanly and plays badly passes every mechanical check
  in this repo.

- Status, restart (2026-08-30): the contract rewrite, the two constants and the decision-record
  amendments are coordinator work on the same argument stages 1 to 3 used - a contract and a
  decision record are single documents, and splitting their authorship produces a document with
  two voices and no owner. What is delegated from this stage is the measurement the rewrite is
  written against: a lane solves the re-sourced tree against the live GTOpen at `4aee435`, walks
  it, and returns the census, the chart, the action menus, the relationship to the superseded 86,
  the blind-defence comparison and the jam retest, writing nothing into the repo because
  `approved_scope` holds five paths and none of them is `data/artifacts/**`. The coordinator
  re-derives the headline figures from the lane's serialised export rather than taking them on
  report, on the stage-6 precedent that a reviewer's report is not evidence either. Independent
  read-only review of the finished contract-update diff before it is committed, as at stage 1 and
  at the 2026-08-24 contract-update.

- Status, decision 19's execution (2026-08-31): the one-field flip, the contract's two clauses naming
  `calibrated`, the decision-record addendum, decision 20 and this plan are coordinator work on the
  standing argument that a contract and a decision record are single documents. One worker lane owned
  the build and its measurements - it started the GTOpen server, ran the extraction, the determinism
  proof, the converter and the report, and wrote its own measurement code with the coordinator's
  explicitly withheld, so that the two measurements are two measurements. It was told to write nothing
  outside `data/artifacts/` and its own scratch directory, to run no gate command and no bare
  `pytest`, and to leave the tracked artifact paths dirty for the coordinator to restore rather than
  clean up after itself. One lane rather than three because the solve, the walk and the derivation are
  one sequential pipeline through a single server on one port and a single writable path. The
  coordinator re-derived every headline figure from the artifact itself; the two agree to the unit on
  the dominance counts and differ on one census figure, where the coordinator's stands and both are
  recorded. An independent read-only reviewer reads the finished diff before it is committed, as at
  every previous contract-update in this lane.

- Status, decision 20's evidence (2026-08-31): the source reading and the two document findings are
  coordinator work, because they are a read of four files in a third-party repo and a correction to
  this repo's own prose. One worker lane owned the contamination measurement: it solved
  `calibrated` plus `add_allin: false` against the live GTOpen by posting the config to the API
  directly rather than through `extract_gtopen_preflop.py`, so no tracked path could move, walked
  33,969 nodes, classified every leaf below every committed spot by pricing mechanism, and wrote its
  own analysis code. The coordinator re-derived the headline from the lane's per-spot splits
  independently of its aggregation and the two agree at 4.959 percent; the lane's leaf classification
  carries its own label cross-check at 0 mismatches and per-spot masses summing to 1 within 5e-8.
  Delegated rather than coordinator-owned because it is a measurement whose number decides a ruling,
  and this lane's standing rule is that the agent that computes a number is not the only one that
  checks it.

- Status, the stage-2 re-cut (2026-08-31): the decision record is a single document and is
  coordinator-owned on the standing argument that splitting its authorship produces a document with
  two voices and no owner. Review is not: two independent read-only reviewers ran concurrently on the
  finished working-tree diff, neither having written any of it and neither having seen the other's
  work - one mechanical, asked whether every reversibility class is right, whether every appended
  figure reproduces and whether any block edited a prior ruling rather than appending to it; one on
  the poker, asked whether the five movers are the right five, whether any amendment misdescribes
  what the committed chart does at the table, and whether item 10's withdrawal of its own
  tolerance-re-derivation licence is an amendment the record may make or a ruling only Taylor can
  take. Both wrote to `stage-02-decisions.md` as new rounds beside the 2026-08-23 round, which is
  left untouched. Both were told not to run `run_verify.py`, `check_gate_bite.py` or a bare
  `pytest`, on the mutation hazard, and not to touch `~/projects/gtopen`.

## Slices

- [x] S1 Contract. Skeleton replaced with criteria written against the backlog entries this phase
      is assigned. Two independent reviewers, one mechanical and one on the poker, found eleven
      blockers between them and neither had seen the other's work; all are resolved in the
      contract and the two that could not be are filed. The phase's centre moved as a result,
      from converting the export to selecting from it.
- [x] S2 Decisions. Thirteen judgment calls recorded with a reversibility class before any code,
      eight of them `frozen-into-data` against phase 13's one, because this phase commits the
      ranges every later phase is measured against. The stage-2 reviewer overturned one item that
      had answered itself: the export offers a jam and no named raise at 4,257 nodes where the
      GTO Wizard source had zero, so the inherited collapse rule had been ruled against a source
      where the case never arose.
- [x] S2 re-cut, 2026-08-31. All 21 items re-taken against decisions 20 and 21, which falsify three
      premises items 1 to 19 rest on: the phase commits 36 spots rather than 51, no committed spot
      offers a jam, and the corpus measurement is phase 17's. Every item carries a dated disposition
      and nothing above one was edited, corrections in a decision packet being additive. Items 7, 9,
      11, 12 and 15 move to phase 17, decision 9's bands void rather than inherited. Items 1, 3, 6
      and 10 are amended; 16 to 19 keep their rulings and gain a correction each, 19 recording that
      decision 20 reverted `static` to `calibrated` the same day. Decision 7 names its pin for the
      first time, `d046ac9`, because phase 17's contract cites it and phase 14 deletes the file. Two
      independent reviews of the re-cut, mechanical and poker, neither having seen the other's work,
      found four blockers. Three are corrected in place. The fourth is **decision 22**: the re-cut had
      settled by prose which dominance relations gate the artifact, and Taylor ruled a per-cell relation
      and that it is gated on aggregates without ever ruling that the suited-row ladder is that
      relation's aggregate form. Filed `frozen-into-data` with an empty answer, so the lane halts at the
      stage-3 human gate.
- [x] S3 Human gate. Cleared 23 to 24 August. All eight `frozen-into-data` items ruled, five
      `runtime-reversible` items proceeding on their recorded defaults. Decision 1 stands as plain
      reach-at-2-percent with no depth floor. Decision 2 went round twice, because Taylor first
      put back the hypothesis that 72.81 percent is the solver's real answer rather than an
      unfinished cell, and the ruling rests on the argument that it is not. None of the thirteen
      is reopened by any later stage.
- [ ] S4 Tests. Authored before implementation, and **held short of the freeze on two blockers**.
      Four lanes wrote three new test files and migrated thirteen frozen files of completed phases.
      Two independent reviewers, mechanical and poker, found five blockers between them and neither
      had seen the other's work; three are resolved in the tests and the canaries, and two need a
      human because they move `frozen-into-data` rulings. The poker reviewer's finding is the
      phase's centre: decision 10's monotonicity criterion cannot be satisfied at the ruled reach
      floor, and the "one violation in the shallow tree" it rests on is a measurement of the eleven
      grids the export publishes rather than of the shallow tree.
- Not paused. All three stage-4 blockers in
      `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-predicate-change-review.md` are
      resolved as of 2026-08-27. Blocker 1 was answered by `da05adf` a day after it was written;
      blocker 2 is withdrawn as a defect, with the four-bet realisation question filed against
      phase 16; blocker 3 is ruled to commit the cell as solved, and the band ruling taken earlier
      the same day was withdrawn before any implementation once the solver output was investigated.
      Stage 4's last pass is written and **halted on one blocker for Taylor**, 2026-08-27. Three
      tests in `tests/test_derived_chart.py` assert that a class the solver never trained is
      refused rather than committed - at the artifact over all 86 spots, at the table as a coded
      lookup miss, and off the strategy row at two tolerances that need nobody's ruling - plus the
      canary `a-class-that-never-arrives-is-committed-anyway`. Two independent reviewers, mechanical
      and poker, neither having seen the other's work, both reproduced the census exactly and found
      five blockers between them. Three mechanical ones are fixed: a two-sided cell bound that
      foreclosed every reach-threshold answer, a tautology, and a `mutations.yml` comment that was
      false twice over. The poker one is the halt and it refutes this pass's own first argument:
      the five near-uniform cells it called threshold hands are undertrained rows, the 100bb
      open-jam carries zero weight at every opening node so one of them is a strategy against a
      range that does not exist, and eight committed spots holding 1,031 cells have arrival
      probability exactly zero while reach flags none of them - four carry every class at full
      reach and four look like an ordinary range facing a four-bet. Arriving reach is hero's
      own range filter, not a measure of whether the solver trained the node. The open question -
      does the rule refuse on arriving reach alone, or also where the solve never trained the
      node - was put to Taylor and ruled the same day: **option one, the chart commits the
      untrained cells and refuses only the classes that never arrive**, because heuristics for
      spots with no solver output are wanted later and a spot with no output is where such a layer
      belongs. One addition was put back to him and taken, since option one as stated defeats its
      own purpose: a committed cell that was never computed is indistinguishable from one that
      was, so **the converter records each spot's arrival probability on the artifact** in parts
      per billion, beside the per-cell reach. The eight never-reached spots read zero; nothing the
      bot answers today changes. Frozen in `tests/test_chart_arrival_probability.py`, a seventh
      file in the family because two of the six are at the 700-line cap and the rest have no room,
      with the canary `every-spot-claims-its-line-is-always-played`. A third independent review of
      that file found three blockers, all fixed: a false "every one of their 169 classes reads full
      reach" in six places, which holds at four of the eight spots and which the file's own cell
      count contradicted; a canary description naming a detector that cannot see the defect; and a
      band that included one of the eight zeros. Decision 5 and the contract's artifact
      criterion both owe an amendment at the next `contract-update`.
- [ ] S5 Freeze.
- [ ] S6 Build. The walk and its census, the converter, the artifact, the retirement of the old
      chart, the sizings, the comparison rerun. The expectations file is external and is not
      rebuilt. Two things arrive owed rather than discovered: the known list in
      `stage-04-test-recut.md` under "What stage 6 owes in `src/` and `scripts/`" - four gate
      commands of completed phases crash once the artifact is rebuilt, and `table_state/measures.py`
      pins `CORPUS_REFUSALS = 290` which must be re-measured - and the arrival-probability field
      ruled on 2026-08-27, which `schema.py` and `chart_derivation.py` both have to carry.
- [ ] S7 Gate. Full `scripts/run_verify.py` plus `check_gate_bite`.
- [ ] S8 Review. Two independent reviewers, mechanical and poker.
- [ ] S9 Audit. Packet with the closing measurement and what it does not establish.
- [ ] S10 Closeout.
- [ ] S11 Advance. Policy says `auto_advance: false`, so this lane stops for Taylor here.

## Measurements this plan is written against - SUPERSEDED, retired export

**Every figure in this section describes the pre-decision-14 export**: 4,094,221 bytes, 38,828 action
nodes, `add_allin: true`, 300 iterations to 0.0062bb. The committed export is 2,555,076 bytes, 33,969
nodes, `add_allin: false`, target 0.00016 met at iteration 1,900. Read for history, never for work.


Taken from the committed files rather than from the roadmap, because the roadmap's own
mitigations document says its estimates do not reproduce.

- The export: `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz`, 4,094,221
  bytes, 38,828 action nodes, 105.45 bytes per node. Solved in 54.2 seconds over 300 iterations
  to an achieved gap of 0.0062bb against a 0.01bb target, and byte-identical across two runs in
  separate processes against a restarted server.
- The config solved: six-handed, 100bb, `open_raises: [2.5]`, `raise_mults: [3.0]`,
  `max_raises: 4`, `add_allin: true` at a 0.67 threshold, `ante: 0.0`, `limp: false`,
  rake-free, calibrated realization.
- The chart it replaces: `data/artifacts/preflop/six_max_nl25_100bb.json`, 264,462 bytes, 36
  spots, so 7,346 bytes per spot in the artifact format - which is what the roadmap's "7.1 KB"
  is, and it is measured off a GTO Wizard-shaped source rather than a GTOpen one.
- The directory cap: `data/artifacts` is limited to 20 MB in `scripts/check_file_sizes.py`, and
  the tree holds 4.4 MB of which 4.0 MB is the gzipped export itself. Deleting the retired chart
  frees 0.25 MB, so the budget is about 15.9 MB - roughly 2,100 spots at the retired chart's own
  rate, against 38,828 nodes.
- What committing the whole export would cost, measured three ways rather than extrapolated:
  272 MiB at the retired chart's 7,346 bytes per spot, 131 MiB at its compact-JSON rate, and 407
  MiB if every node keeps all 169 hand classes the way a GTOpen node carries them. Filtering each
  spot to hero's own arriving range, which is what the retired chart does, brings the whole export
  to 71 MiB. All four are over the cap by between 4.5x and 26x. There is no version of "commit
  the tree" that fits.
- Convergence is not uniform over that tree. The solve target is a summed best-response gap in
  big blinds, so it says nothing about a node carrying negligible mass. Over the eleven grids the
  export publishes, the two airtight dominance relations give one violation across the ten
  shallow reference nodes and 42 at the single deep four-bet node.
- The corpus today: 499 hands, 3,048 preflop decision points, 290 refusals across 159 distinct
  spots, 206 of the 290 in the two blinds. Calls agree 59.5 percent for Pluribus on 37 decisions
  and 60.8 percent for humans on 227, against a 96.3 and 93.6 percent headline dominated by the
  72 percent of decisions that are folds. The stricter sampled-action match is 89.0 and 85.3.
- The deltas the closing measurement's prediction must be built from: big-blind defence widens
  4.65 points against the lojack, 3.72 against the hijack, 2.64 against the cutoff and 6.14
  against the small blind, and comes back 2.67 points tighter against the button.

## Next Agent Bootstrap

**This section is the single source for what is true now.** The decision record is 47 items with 64
supersession notices and four restarts have begun with someone reconstructing the rules from it. Read
this, then the contract, then only the decision items named below.

Work only in `~/projects/poker-bot-worktrees/phase-14` on `phase/14-chart-cutover`. Never in
`~/projects/poker-bot`. Ask the driver and do only what it names, then `--advance`:

    uv run python scripts/loop_stage.py --phase 14 [--advance]

### The rule set, as of 2026-09-02

1. **Source.** GTOpen's committed export, `add_allin: false`, `realization: calibrated`, 33,969 nodes.
   Not re-solved. `static` turns the big blind into a calling station and `raw` was never run; there is no
   fourth setting (decisions 19, 20).
2. **Trust it everywhere except four-bet pots and multiway pots.** A four-bet pot is SPR 1.70, below every
   observation the flop-pricing fit has; multiway terminals use a product approximation the fit never
   covered (decisions 35, 46).
3. **Selection is three clauses.** At most two raises already in; multiway exposure under **ten percent**
   over the branches the bot can take (46); and not a big-blind squeeze spot (48). **249 nodes**: 5
   first-in, 25 facing an open, 219 facing a three-bet, **98.5949 percent** of preflop decisions. Census
   249 + 348 + 10 + 33,362 = 33,969. Do **not** reinstate decision 1's opponent clause (40).
4. **The bot never cold-calls; opponents do.** The solve is deliberately left unconstrained, so villains
   still flat (decision 33). Every seat but the big blind is raise-or-fold facing an open.
5. **The bot's flats are merged into its raises, not deleted** (decision 45). At the 20 non-big-blind
   facing-an-open spots the published raise weight is the solve's raise plus its call. The big blind keeps
   fold, call and raise. Deleting was unimplementable: the solve puts some hands' whole weight on calling
   and this chart is **93.20** percent pure at 99 percent or more (decision 49).
6. **Defects accepted on purpose, each with a published cost.** The big blind defends too tight (34). The
   pair ladder inverts (41), the kicker ladder inverts (47) - its wheel-ace cases being **correct poker and
   not defects** - and 27 pair inversions sit on the raise action where play-not-fold is blind, now
   measured by a fourth relation (50). Merged flats play differently from flats (45). **Decision 49 carries
   every corrected count; earlier items state figures taken over sets that have since moved.**
7. **Nothing gates on whether a range is good poker** (42). Three relations and two counterfactual arms are
   measured; the arms catch extraction defects only. `GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE`
   stays open and this phase does not close it.
8. **Also load-bearing and not superseded**, because the contract's criteria implement them and no summary
   named them before: **4** blind structure, **5** arriving reach, **6** the two-price schema and the
   un-gated expectations comparison, **8** the closed `namespace:reason` vocabulary, **10** the one-point
   tolerance and the pinned relation definition, **14** `add_allin: false`.

### Open, and not to be invented

- **The `PREFLOP_PRUNE=0` experiment was run on 2026-09-02 and came back negative.** Re-solved at 1,900
  iterations to a better gap than the committed solve (0.000149 against 0.000156); every inversion
  reproduced identically, `44` at 0.6 percent from the lojack and the rest unmoved. Pruning is not the
  cause, so there is nothing stuck to free and the acceptances stand on a measured property of the source.
- **The stage-1 review of the 2026-09-02 rewrite is done**, in
  `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-01-contract-assumptions-review.md`. It found
  one blocker (decision 52) and five figures that do not reproduce; a second, independent measurement agent
  re-derived all five and confirmed every one, and decision 53 corrects them. Nothing from that review is
  still open except finding 5, which is a recorded margin and not a task.
- **The rank counterfactual arm passes the 219-spot partition by one cell**, 32 against 33, on the
  partition holding 219 of the 249. Its restriction to spots closed under reversal is load-bearing: over
  all 219 spots the arm reads 149 against 69 and fails. Anyone touching the tolerance, the closed-spot
  definition, or which comparisons count is touching the only thing between that gate and a red. Do not
  soften it to buy margin; a failure there is a halt and a decision for Taylor (decision 53).

### Do not

- Do not touch, fork, branch or build anything in `~/projects/gtopen`. It is a read-only reference clone at
  `4aee435` with no licence and no push access, and decisions 33 and 36 both declined to patch it.
- Do not revert a ruled constant to green the gate. Do not commit under `data/artifacts/`: the artifact is
  writable at stage 6, and the frozen tests migrate at stage 4 first.
- Do not adjust a published frequency by hand. Do not raise the exposure threshold again.

### The gate is red by design until stage 6

`tests/**` is frozen against the superseded six-spot and 143-node specifications, so the phase's own
commands fail on assertions. That is expected and is stage 4's to re-cut against the **249**. The committed
`data/artifacts/preflop/six_max_100bb_rakefree.json` in the tree is still the retired 86-spot chart; stage 6
replaces it and it is not writable before then. Reverting a ruled constant to
clear it erases the correction that produced it. Separately, twelve backlog entries fail
`run_full_quality_gate`'s status and phase constants, which is MAINT-29's, not this lane's
(`BACKLOG-VOCABULARY-IN-USE-IS-NOT-THE-VOCABULARY-THE-GATE-ALLOWS`).

## What stage 4 froze as a specification for stage 6 - SUPERSEDED, retired export and retired rule

**Also pre-decision-14.** It carries `REACH_FLOOR_BP = 200`, an 86-spot selection, 5,626 committed nodes
and a `DERIVATION_BELOW_REACH_FLOOR` code. There is no reach floor now, the committed set is 249, and the
exclusion codes are the four decision 48 names. Read for history, never for work.


Tests authored before an implementation are a specification, and so are the canaries. Both were
written against names the builder has to produce, on the phase 11, 12 and 13 precedent: a canary
written after the code can only describe what was already written, which is how phases 08, 09 and
10 each ended up with no canary for the one behaviour their phase existed to add. A `find` string
that does not occur at stage 6 is the builder having drifted, not the canary being wrong.

Five of the eight canaries target `chart_derivation.py`, one `schema.py`, and two the report
generator. Two were re-aimed at stage 4 after an independent mechanical review, and both would
otherwise have failed silently rather than loudly, which is worth recording because it is the
failure mode a canary is least able to report about itself. The jam-pricing canary named
`scripts/convert_preflop_export.py` while the frozen tests put the collapse rule in the `src/`
module, and `check_gate_bite` requires the find string to occur exactly once in the file it names,
so stage 7 would have halted on zero occurrences. The blind-structure canary replaced a line in
`PreflopArtifact.to_payload()` and would have bitten only if the derived payload happened to be
assembled through it; the one committed test that exercises `to_payload` round-trips it, so both
dumps would have carried the same wrong structure and agreed with each other.

**New module `solver_artifacts/chart_derivation.py`.** *Superseded in part on 2026-08-24: the
selection predicate is no longer a reach floor, so `REACH_FLOOR_BP = 200` and everything that reads
it are stage-4 work to be re-cut, not a design to build to.* What survives unchanged:
`node_action_sequence` walks a node's path into a `PreflopAction` sequence, taking each action's
actor from the **parent** node's `actor_pos` and dropping folds; `census(export)` returns a
`NodeCensus` whose buckets sum to the source card's own node count; and it is verified on the
committed export that all 38,828 nodes derive a valid key, 38,828 distinct, with zero collisions.
What replaces the floor is a two-clause predicate needing no threshold constant at all: at most one
non-actor seat has taken a call, raise or jam, **and** at most two seats are not yet folded. Together
they select 86. *Do not build either clause on its own: the history clause was ruled on 2026-08-24,
selects 110, and was superseded on 2026-08-25 because 24 of those 110 still reach a multiway
terminal; the subtree clause alone selects 5,472, admitting nodes reached through a cold call whose
arriving ranges the same defect already distorted.* The
reach mean stays as a *published measurement* rather than a filter, and note its definition: the
plain unweighted mean over the 169 classes, which is what reproduced 891 / 1,424 / 3,296 / 5,626 /
9,407 / 13,575 at the 20, 10, 5, 2, 1 and 0.5 percent floors. A combo-weighted reading gives 4,856
at 2 percent and is a different number for the same words.

**Reason codes in `lookup.py`**, which is decision 8's ruling that a reader meets one vocabulary
rather than two. `DERIVATION_NO_LEGAL_SPOT_KEY` stands and its bucket publishes at zero, which is a
result rather than an omission. `DERIVATION_BELOW_REACH_FLOOR` is superseded: decision 8's amendment
requires **two** exclusion codes rather than one - a node outside the selection rule, and a node the
source misprices - because one code cannot say which of the 38,742 excluded nodes come back when
GTOpen can price multiway. The two codes now genuinely differ: the 24 that the 2026-08-25 ruling
drops are outside the rule *because* the source misprices them, and 5,386 terminal-clean nodes are
outside the rule for the separate reason that they are reached through a cold call.

**Schema at version 2**, carrying `BlindStructure` (decision 4) and `arriving_reach_bp` per cell
(decision 5), plus the rule that a spot with an empty `action_sequence` may not carry a positive
`call` weight. That last one is `CHART-HERO-MUST-NEVER-LIMP`, and it closes on the schema rather
than on a measurement: the export enforces it by construction, but that is a property of the data
and this phase owns the schema.

**Paths.** The artifact becomes `data/artifacts/preflop/six_max_100bb_rakefree.json` with its
sizings alongside; `six_max_nl25_100bb.json` and its sizing table are deleted; the expectations
file and the GTO Wizard source it came from stay untouched, because a reference regenerated from
what it checks cannot fail.

**What the cutover does to coverage, measured rather than assumed.** The kept chart holds exactly
four raise prices - 2.5, 7.5, 22.5 and 100 - so none of the retired chart's 3.5, 8, 11 or 13.5
survives, which is the 17-of-36 non-collision the contract cites. *Revised 2026-08-24:* the squeeze
after an open and a cold call is no longer gained - it is the family the ruling excludes. Gained is
the big blind facing a four-bet and the rest of the heads-up three-bet and four-bet skeleton, 86
spots against the retired chart's 36 - *revised again 2026-08-25, and four of the five opening
ranges are now excluded with it, leaving only the small blind's.* The retired 36 are all heads-up by
the superseded history predicate but **only 22 of them are terminal-clean**, so 14 spots the bot
answers today are refused after the cutover and the "nothing currently answered is lost" claim dies
with the 110. Beyond those 14 the limped pot is lost too, absent from the tree because the solve is
`limp: false`, so
`t6/d100/BB/SB:call` moves from covered to refused. That is the accepted cost of phase 10's human
gate, filed as `CHART-CANNOT-ANSWER-A-LIMPED-POT`, and stage 4 migrated the tests to assert the
refusal rather than deleting the claim. So of the retired 36, **22 pass the ruled predicate but only
21 are actually covered** - `BB/SB:call` passes it and still has no node, because the tree has no limp
branch to hold one. **Spot count rises 36 to 86 and the refusal rate rises with it**, on those 15 and
on nothing else; a rise outside the 15 named spots is a defect rather than the cost of this ruling.
The 2026-08-25 note reversing the direction of this criterion is in
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-eighty-six-coverage.md`.

## What stage 6 will have to face that stage 4 could not settle

Two things are known to be waiting and neither is a reason to stop now.

**~~The byte budget is not proven.~~ Retired 2026-08-24.** This was a live risk while the phase
committed 5,626 spots. At 86 it is not: the artifact is two orders of magnitude under the 20 MiB
cap and no field the schema gains can close that gap. The contract's rule still stands - exceeding
the cap is a halt and a decision for Taylor, not a number to raise - it simply has nothing to bite
on here. Any plan that reasons from the byte budget is reasoning from a retired premise.

**The registered facts will drift.** `scripts/repo_facts.py` computes ten facts from the
committed chart and pins them into live documents, and the cutover moves several of them. That is
`quality_checks`'s fact-drift check doing its job rather than a failure, but it is check-script
territory a phase task may not reach, so it is likely to need its own maintenance task between
stage 6 commits, on the MAINT-24 and MAINT-25 precedent.

## Verification brief for the next agent: the cold-call finding

**Discharged 2026-08-24.** This brief was executed; the result is
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-04-cold-call-verification.md`, which
reproduced all seven claims and found the mechanism. It is kept as the record of what was asked,
and it is history rather than instruction - in particular its item 4, that both cold-call nodes
clear the 2 percent floor and are therefore committed spots, is no longer true of what this phase
commits.

Written at the stage-4 halt, 2026-08-24. Everything below is a claim to be **falsified**, not a
result to be confirmed. It was measured by the agent that also wrote the tests, which is exactly
the arrangement this repo distrusts, so recompute rather than quote.

    Work only in ~/projects/poker-bot-worktrees/phase-14 on phase/14-chart-cutover. The loop is
    halted at stage 4; do not advance it. Read reports/phase_audits/reviews/
    PHASE_14_CHART_CUTOVER/stage-04-tests.md and verification/loop_runs/14.yml first.

    Verify or refute, independently, from
    data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz. Write your own walk;
    do not import chart_derivation, which does not exist yet, and do not reuse the scratch
    scripts.

    1. At node path [1,0,0,0,0] the big blind faces a 2.5bb lojack open and defends 27.28% of
       its range, combo-weighted, with KQo calling 99.9% and AA raising to 7.5 at 99.7%.
    2. At node path [1,1,0,0,0], the same spot plus one hijack cold-call, it defends 7.44%,
       KQo folds 99.9%, AJo 99.5%, T9s 99.9%, K9s 99.2%, and AA jams 100bb at 94.3%.
    3. The price improves from needing 27.3% equity to needing 18.8%.
    4. Both nodes clear the ruled 2% reach floor, so both are committed spots.
    5. Across the 26 committed spots where the big blind faces one 2.5bb open plus one to four
       cold calls, defence never rises above 40.57% and falls as low as 4.01%, and is not
       monotone in the number of callers.

    Then answer the question the numbers cannot: is this a defect, or is it correct for a
    100bb six-max game with no rake? State which hands you would defend at node 2 and why, in
    poker terms, before you look at what the solver did.

    Two claims to check separately, because they change what the phase does rather than what it
    believes. First: `reach_bp` in the export is the ACTOR's own range survival, not the
    probability the line occurs, so decision 1's floor keeps every node where hero has not yet
    acted however rare the line. Second: no aggregate form of decision 10's two relations passes
    over all 5,626 committed nodes, and over the 351 full-reach nodes the suited-versus-offsuit
    aggregate gives 6 violations as solved against 97 with suited and offsuit transposed.

    Report findings only. Change no test, contract or artifact.
