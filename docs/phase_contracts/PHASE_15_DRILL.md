---
phase_id: "15"
title: "The Drill"
depends_on:
  - "14"
required_gate_commands:
  - pytest_drill
  - generate_drill_session_report
required_reports:
  - reports/active/latest_drill_session_report.txt
  - reports/active/latest_drill_decision_audit.jsonl
required_phase_audit: reports/phase_audits/PHASE_15_DRILL.md
---

# Phase 15: The Drill

## Scope

The repo's first interactive entry point. It deals a preflop spot, takes a human's action, says what
the committed chart says, records the session, and turns a run of sessions into a leak report. Five
phases produced ranges nobody has used; this is the phase that puts a person in front of them.

**What the chart can support is measured first, because it decides the whole shape of the phase.**
All figures below are recomputed from `data/artifacts/preflop/six_max_100bb_rakefree.json` at
`9bbdcf4` and are re-derived by this phase's report rather than carried as prose.

- **The artifact carries no per-action EV.** A cell is a weight per action summing to one. Prices
  exist (`size_bb`, the blinds, the stack depth) but **no value is attached to an action**, at any
  layer: the export carries frequencies too, the only `evs` in the repo is six whole-game numbers one
  per seat, and the equity matrix prices all-in equity at a tree that offers no shove. So the drill
  **cannot** say what a wrong action costs, and inventing a cost is the heuristic guessing
  `AGENTS.md` forbids. `docs/V2_ROADMAP.md` promises this phase says "what the difference costs"; that
  half of the promise is refused here, with the measurement above as the reason, exactly as the
  ingestion lift is refused below.
- **A quarter of the chart cannot express a call, and it is the quarter the student sees most.**
  4,225 of 18,431 cells carry only `{fold, raise}`: 25 spots - all 5 first-in and the 20 non-big-blind
  spots facing an open, where phase 14 decision 45 merged the flat into the raise - and they are
  **80.2010 percent of arrival**. So on four deals in five the menu has two buttons, and a student who
  calls has taken an action the chart has no weight for. Scoring that as zero would teach that calling
  an open is always a mistake, which is false and is the reading
  `MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED` warns about.
- **The committed set is three families of wildly different size and frequency**: 5 first-in spots
  carrying **52.6637** percent of arrival, 25 facing-an-open carrying **39.0915**, and 219
  facing-a-three-bet carrying **8.2448**. So uniform sampling spends 88 percent of a student's time
  on 8 percent of the decisions, and arrival sampling gives the **median** three-bet spot one deal in
  899,346 - the mean of one in 2,656 is carried by a handful of them. Neither is a training policy
  (`A-SIXTH-OF-THE-COMMITTED-SET-IS-ALMOST-NEVER-DEALT`).
- **44 spots have an arrival of zero parts per billion**, all 44 facing a three-bet.
- **How much of the chart is mixed depends entirely on where the line is drawn, and the repo has not
  drawn one.** Cells below a top weight of 0.90 number 675 (3.66 percent), below 0.99 1,202 (6.52),
  below 0.999 1,820 (9.87), below 0.9999 2,431 (13.19). The committed derived-chart report publishes
  93.48 pure and 3.66 mixed off `PURE_PCT = 99.0` and `MIXED_PCT = 90.0`, leaving 527 cells in a band
  it does not name. This phase pins **one** threshold before it measures anything and uses the repo's
  99, so two committed documents do not state different mixing figures for one artifact. Mixing
  concentrates in the three-bet family: 12.33 percent against 4.02 first-in and 3.27 facing an open.
- **106 of the 249 spots are continuations of a call the bot never makes**
  (`COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY`), carrying 0.0164 percent of arrival. Phase
  14 left the ruling on whether the drill deals them to this phase, and this contract makes it.

**The bounded personal-history ingestion lift is out of scope and this is a ruling, not an
omission.** `docs/V2_ROADMAP.md` puts it here; `AGENTS.md`'s V1 Boundaries still read "No large
hand-history ingestion", the roadmap itself says the file wins until a `contract-update` changes the
wording, and the bound is a number nobody has chosen in three weeks of it being owed. Five further
stops sit under the boundary: the corpus reader is PHH-only, requires `finishing_stacks`, requires
every seat's hole cards - a personal export shows only your own - requires whole chips, and refuses
a straddle. The drill produces its own sessions, so the leak report has real input without the lift.

`verification/loop_policy.yml` gives this phase `auto_advance: false`: it commits session records and
it is the first surface a human uses directly.

## Non-goals
- The standing V1 boundaries: no PokerNow automation, browser or platform observation, runtime solver
  calls, LLM-backed poker decisions, or training UI surfaces. A terminal program is not a UI package;
  `docs/V2_ROADMAP.md` defers that and says to revisit once the drill exists.
- **No personal hand-history ingestion**, per the scope statement above. Do not read, parse, or
  commit any hand history the drill did not itself deal, and do not widen the corpus reader.
- **No postflop.** The drill deals preflop decisions, because that is what the chart answers, and
  every postflop street still checks through.
- Do not re-solve, re-derive, or hand-edit the committed artifact, its sizing table, or the
  expectations file. Do not change the spot key grammar or the chart's selection rule.
- Do not add a confidence interval to any rate. `docs/CORPUS_COMPARISON_LIMITS.md` explains why one
  would be optimistic here: the decisions are clustered, not independent.

## Acceptance criteria

### What the drill deals
- **The sampling policy is stated as data, pinned by a test, and printed with the arrival
  distribution beside it.** Two properties constrain it rather than a name: every family gets a
  **stated minimum share** of the deal, so no family can vanish the way three-bet pots do under
  arrival weighting; and within a family the order is arrival's, so no spot is dealt more often than
  a spot it is rarer than. The report prints what uniform, raw arrival, and the chosen policy would
  each have dealt over one budget, so the choice is visible rather than asserted.
- **Family strata come from the artifact, not from a list.** A spot's family is derived from the
  count of raises in its `action_sequence`, and a test proves the derivation reproduces 5 / 25 / 219
  against the committed set. A hardcoded family map fails.
- **A spot the sampler will never draw is stated, with its count and its reason**, and the drill
  says so rather than leaving the student to infer coverage from what came up.
- **The 106 unreachable spots are ruled on explicitly.** The rule distinguishes the spots that
  publish a priced range hero could draw from and the spots that publish none, because a spot with
  nothing to answer with cannot be scored at all. Whichever way it falls, the drill tells the student
  that these spots answer an opponent's line rather than the bot's own. The report prints two
  distinct splits and does not let one phrase carry both: the 106 split by whether the spot publishes
  a range hero could draw from, and the 106 read once as a tree the bot plays, where they are dead,
  and once as a reference a human is drilled on, where they are legitimate.
- **A dealt hand is real cards, and the session is a pure function of its seed.** The same seed
  replays the same deal, the same order and the same spot, in a fresh process, and a test asserts it.
  The per-hand `Random` is derived from the session seed and the hand index, as `simulator/run.py`
  already does, and nothing touches the global `random` module.

### What the drill says back
- **The answer is the whole mixture, not the top action.** Every action the cell prices is shown with
  its weight, so a student sees that a cell is mixed rather than being told they were wrong. Where the
  menu has no call the drill says the flat was merged into the raise rather than showing two buttons
  and letting the student infer that folding and raising are the only choices.
- **An action the cell does not price is shown and never scored.** A call at one of the 25 merged
  spots is not a zero; the chart has no weight for it because the solve's flat was folded into the
  raise, and a zero would teach that calling an open is always wrong. The same rule covers a small
  blind limp, which the reference file limps 13.73 percent of the time and this tree cannot express.
  These decisions are counted, reported, and excluded from every rate's denominator, on the Phase 08
  refusal precedent.
- **The score has one reading and the contract fixes it here rather than leaving it to a builder.**
  A decision is *graded* when the cell's top weight clears the pinned purity threshold, its arriving
  reach clears the pinned floor, and the student's action is one the cell prices. The session score is
  **the mean of the weights the chart put on the student's action over graded decisions** - so
  "available" is 1.0 per graded decision, not the cell's maximum. Ungraded decisions are counted and
  reported by reason and never folded into the score. Both are re-derived by the report.
- **No EV, no chip cost, no "this cost you N big blinds", anywhere in the drill, the report, or the
  packet.** A criterion, not a caution: the artifact carries no EV, a mixed cell means the actions
  are priced alike, and a zero-weight action may cost a hundredth of a big blind or five. The drill
  states in the student's own words that it measures agreement with a solved strategy and cannot
  price a mistake. The test that enforces this names its predicate rather than pattern-matching for
  chips, which the report legitimately prints as spot keys and raise sizes: no scoring path may read
  the equity matrix, run the simulator, or emit a field whose name or unit is `bb`, `chips`, `ev`, or
  `cost` outside the price of an offered action.
- **A refusal says why, in poker English.** The live vocabulary is the four codes in
  `solver_artifacts/lookup.py` - `derivation:beyond-committed-raise-depth`,
  `derivation:multiway-exposure-above-threshold`, `derivation:big-blind-squeeze-spot`,
  `derivation:no-legal-spot-key` - and **not** the two names `backlog.yml` still quotes, which
  `tests/test_chart_census.py` records as retired for exactly the reason this contract nearly
  repeated. At runtime all of them collapse into `lookup:spot-not-covered`
  (`A-REFUSAL-CANNOT-TELL-THE-HUMAN-WHY`), and the committed artifact carries no exclusion table, so
  **how the reason reaches the table is a ruling this phase makes and not an assumption it starts
  from**: the code is derivable from the key for one bucket and needs the 33,969-node export for the
  others. The decision list settles the mechanism and its cost against the 20 MiB artifact cap before
  a lane builds anything. A drill that ends a hand on a refusal without saying why teaches nothing.
- **A refusal is never scored**, and refusals are counted and reported separately from the
  denominator, on the Phase 08 precedent.

### How the drill is built, because the gate cannot type
- **A gate command cannot read stdin, so the interactive program is not the gateable thing.** The
  drill's core is a pure function from a seed and a sequence of answers to a session. The interactive
  program holds no sampling, scoring or record-building logic of its own, and a test asserts the core
  module imports nothing from it, so the untested surface is reading a line and printing one.
  `AGENTS.md`'s testing ladder has no rung for an interactive loop, and this is how the phase stays on
  the ladder rather than inventing a rung.
- **The chart's opinion is read with `weights_for`, never with `decide`.** `decide` collapses a mixed
  cell to one action by a seeded draw, so grading a student's fold against a cell that folds seventy
  percent of the time would mark a correct answer wrong. A test asserts the drill never calls
  `decide` or `collapse` on the scoring path.
- **The entry point is a script under `scripts/`, in the house style**: `uv run python scripts/...`,
  `main()` returning an int, output relative to `REPO_ROOT`. No `[project.scripts]` entry, because the
  repo has none and one would be a second way to run things.

### The session record
- **A drill session is a normalized hand history plus the student's action at each decision**, on the
  Phase 02 schema, and it replays through the frozen replayer without a new code path.
- **The session record is a new type, and the reason is worth stating.** `DecisionAuditRecord` holds
  one outcome and re-validates it against the query's legal actions, so it cannot hold a student's
  mistake beside the chart's answer. Do not loosen that validation to make it fit.
- **Writing a hand history is new work.** The repo reads `NormalizedHandHistory` and has never
  written one. The writer must round-trip `parse_hand_history`'s exact-key check, including the
  shapes the JSON has and the dataclass does not: a nested `table` object and `result.payouts` as a
  list of `{seat, amount}` objects. A test round-trips a written session back through the parser.
- **Committed sessions are bounded and the report prints the budget.** `data/samples` is capped at
  5 MB by `check_file_sizes.py` and already holds the corpus. The hand count of the committed session
  is pinned as data in the decision list before it is written, and the report prints the bytes it uses
  and the headroom left, so the cap is a measured number rather than a hope.
- **Hand ids are unique across sessions.** `sim-{seed + index}` collides between runs seeded 100 and
  101; a run-scoped prefix fixes it while keeping a hand reproducible from its own seed
  (`SIMULATOR-REPORT-UNITS-AND-IDS`). Every committed report that carries a hand id is regenerated.
- **The win rate the simulator reports is printed in bb/100** alongside chips per hand, that being
  the unit a poker player can calibrate against (`SIMULATOR-REPORT-UNITS-AND-IDS`).
- **One deterministic drill session is committed as a fixture**, six-handed at 100bb and one flat
  stack depth, so it is a hand the committed chart actually answers rather than one it refuses
  (`SAMPLE-HAND-THE-CHARTS-COVER`). Committing it is a `frozen-into-data` decision and is answered in
  the decision list before stage 4 freezes anything.
- **The decision audit is written out, not only held in memory.** A committed JSONL of every decision
  the session scored, on the `latest_postflop_decision_audit.jsonl` precedent, so a reviewer can read
  one decision without running a generator (`SIMULATOR-DECISION-AUDIT-NOT-COMMITTED`).

### The leak report
- **It never leads with a single agreement rate.** Phase 08 paid for this finding: 72 percent of
  scored decisions were folds, folds agreed 98.6 percent of the time, and the pooled number was
  measuring how easy it is to fold trash. The report is broken out by the action the student took and
  by spot family before any pooled figure appears, and a pooled figure that does appear is labelled
  the lesser number.
- **Every rate carries its denominator**, and a rate over a small denominator prints the count rather
  than being suppressed or dressed up. A one-player report is sparse by construction.
- **Per-player narrowing is added without making the population split optional.** `population` stays
  a required argument on every accessor; `player` is a further narrowing. Pooling the two populations
  inside a breakout is the defect MAINT-08 fixed and must not return.

### Evidence, reports, and gate
- **Every figure this contract names as an obligation is printed by the report and re-derived by the
  generator, which exits non-zero when one does not hold**: the family counts and arrival shares, the
  zero-arrival count, the mixed-cell share overall and per family, the three sampling policies over
  one budget, the unreachable-spot count under both readings, the refusal split by reason, the
  captured-against-available weight, and every leak-report breakout with its denominator. No count is
  hand-typed (`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`). One number is recomputable by
  hand and the packet says which and how.
- **The report regenerates byte for byte** and carries a `--check` mode that writes nothing and fails
  the gate when it would have changed anything. `render_*` stays a pure function returning a string,
  reading no clock, no environment and no random source, as every generator here already does.
- Both command IDs are declared in this frontmatter, registered in `COMMANDS` in
  `scripts/run_verify.py`, and **each carries a mutation canary authored at stage 4, before the
  implementation**, with `check_gate_bite` proving it bites. Phases 08 and 09 each authored canaries
  for every command except the one the phase was adding; this phase does not repeat that.
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

### The backlog entries this phase settles
Every entry whose `phase` **value** is 15 is closed, restated with a measurement, or moved forward
with a reason, and so is every entry naming the drill from another phase. The sweep is on the parsed
value, not on a quoted string: `A-REFUSAL-CANNOT-TELL-THE-HUMAN-WHY` is written `phase: '15'` and a
literal search for the double-quoted form misses the entry carrying this phase's hardest criterion.
- Closed here: `SAMPLE-HAND-THE-CHARTS-COVER`, `SIMULATOR-DECISION-AUDIT-NOT-COMMITTED`,
  `SIMULATOR-REPORT-UNITS-AND-IDS`, `A-SIXTH-OF-THE-COMMITTED-SET-IS-ALMOST-NEVER-DEALT`,
  `A-REFUSAL-CANNOT-TELL-THE-HUMAN-WHY`.
- Answered from another phase's docket: `COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY`,
  whose remaining ask on phase 15 is the sampler ruling above.
- **Explicitly not closed**: `V2-LARGE-DATASET-COMPARISON` and the ingestion half of
  `BLIND-STRUCTURE-VARIANTS`, both of which wait on the `AGENTS.md` boundary change and a bound
  stated as a number. Restated with what they wait on; neither marked done.
- `V2-TRAINING-UI` is restated, not closed: it unblocks once the drill has been *used*, which this
  phase cannot assert on its own behalf.

## Required reports
- `reports/active/latest_drill_session_report.txt`
- `reports/active/latest_drill_decision_audit.jsonl`

## Required command IDs
- `pytest_drill`
- `generate_drill_session_report`

## Human vetting packet requirements
- Plain-language summary of what changed, a pass/fail checklist for a non-coding reviewer, a command
  summary linking the committed reports, and known limitations.
- **What the drill teaches, stated first and in poker terms**: which decisions it will deal and how
  often, which it will never deal and why, that about one cell in ten is mixed so two different
  answers can both be right, and that the score is agreement with a solved strategy rather than a
  price on a mistake.
- **The sampling policy in one paragraph a player can argue with**, beside the numbers for what
  uniform and arrival-weighted would have dealt instead.
- A source-code-free spot-check path: a seed, the hand it deals, the cell it lands in, and the
  published mixture, so Taylor can check one decision against the artifact by hand.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success, infer missing strategy or chart behavior,
  or change this contract during implementation mode.
- **Do not invent an EV, an equity proxy, or any chip-denominated cost for a preflop mistake**, and
  do not present a strategy weight as though it were one.
- **Do not score a refusal**, do not substitute a neighbouring cell, and do not soften a refusal into
  a default action so that a session has an answer for every hand.
- Do not choose the sampling policy to make an agreement rate look better, and do not exclude a spot
  family from the deal because the student scores badly on it.
- Do not lead the leak report with a pooled rate, and do not pool the two populations inside a
  breakout.
- Do not read or commit a hand history the drill did not deal.
- Do not run a gate command in a worktree another lane is using. `check_gate_bite` edits `src/**` in
  place, and two runs in one tree corrupted the primary checkout on 2026-09-06.

## Regression expectations
- Previously completed phase gates remain verifiable, generated human docs remain current, and
  file-size and scope checks continue to pass.
- **Hand ids change shape, and that is the point.** The collision is real - `hand_seed = seed + index`
  puts a hand called `sim-101` in both a run seeded 100 and a run seeded 101 - but **no committed test,
  report or fixture asserts a `sim-` id today**, so the migration set is empty and the phase says so
  rather than claiming a migration it did not perform. If the set stops being empty before stage 5,
  the migration happens at stage 4 and before the freeze, as phases 11 and 12 each learned.
- The simulator report gains a bb/100 figure beside its chips-per-hand figure. The existing figure
  stays, so nothing that reads it breaks.
