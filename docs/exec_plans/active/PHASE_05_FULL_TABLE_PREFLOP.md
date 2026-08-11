# ExecPlan: Phase 05 Full-Table Preflop Strategy

## Objective

Close the Phase 05 gate: a preflop playing strategy that answers only from
committed chart artifacts, backed by a real solver export covering the six-max
100bb first-two-decisions matrix, with frequencies checked against their
published source.

Run in two stages, the same shape Phase 04 used.

- Stage 1, `contract-update`: flesh out the phase contract and record the
  judgment calls a chart cannot settle. This stage is complete when Taylor has
  answered the judgment-call list.
- Stage 2, `implementation`: build the artifact, the strategy, the tests, and the
  report.

## Scope

Stage 1 approved files:

- `docs/phase_contracts/PHASE_05_FULL_TABLE_PREFLOP.md`
- `reports/phase_audits/decisions/PHASE_05_FULL_TABLE_PREFLOP_DECISIONS.md`
- Standing scope only for `CURRENT_TASK.yml`, `docs/exec_plans/**`,
  `reports/active/**`, and the generated human docs.

Stage 2 approved files, to be set when implementation is activated:

- `src/poker_training_bot/strategy/preflop_chart.py`
- `src/poker_training_bot/strategy/preflop_sizing.py`
- `scripts/convert_preflop_export.py`
- `scripts/generate_preflop_strategy_report.py`
- `scripts/run_verify.py` for command registration only
- `data/artifacts/preflop/**`
- `tests/test_full_table_preflop.py`
- `tests/test_preflop_committed_charts.py` for the retirement of the
  hand-authored chart
- `docs/PREFLOP_ARTIFACT_CONTRACT.md` for the sizing-table and provenance notes
- `reports/phase_audits/PHASE_05_FULL_TABLE_PREFLOP.md`

Forbidden throughout: `data/raw/**`, `data/processed/**`, any change to Phase 03
decision validation or Phase 04 import validation that admits the new artifact by
loosening a check, and any contract edit during Stage 2.

## Delegation Plan

- Worker lanes: four Stage 2 lanes plus a review lane. Lane A converts the
  committed source export into the artifact and writes the frequency expectation
  table. Lane B writes the strategy and the sizing table. Lane C authors
  `tests/test_full_table_preflop.py` from the contract alone, before Lane B
  starts, and never sees Lane B's implementation. Lane D writes the preflop
  strategy report generator and registers its command ID. Lane E is a read-only
  reviewer briefed specifically on poker-domain correctness rather than code
  quality.
- Ownership: Stage 1 is coordinator-owned because it is contract authorship and
  judgment-call framing that depends on the extraction session's own context, and
  splitting it would hand a worker a spec it has no way to check. Lane A owns
  `data/artifacts/preflop/**` and `scripts/convert_preflop_export.py`. Lane B owns
  `src/poker_training_bot/strategy/preflop_chart.py` and
  `preflop_sizing.py`. Lane C owns `tests/**`, and Lane B may read those tests but
  may never write to `tests/**`. Lane D owns
  `scripts/generate_preflop_strategy_report.py` and the `COMMANDS` entry in
  `scripts/run_verify.py`. The coordinator owns integration, the retirement of the
  hand-authored chart, `phase_status.yml`, the audit packet, and closeout.
- Expected outputs: Lane A a committed artifact plus committed source export plus
  the expectation table and a converter that reproduces the artifact byte for
  byte. Lane B a strategy satisfying the Phase 03 protocol with a sizing table
  carrying its own provenance. Lane C a test module covering totality by
  enumeration, legality through the decision audit record, suit and order
  isomorphism, byte determinism, exact-depth refusal, blind-structure refusal,
  tie refusal, and the source-frequency expectations. Lane D a report a
  non-coding reviewer can read plus a registered command ID. Lane E written
  findings classified blocker or non-blocker.
- Status: all lanes completed. Lanes A through D were coordinator-owned; lane E ran
  as two read-only review subagents.
- Integration order: Lane C first so the tests predate the implementation, then
  Lane A, then Lane B against the frozen tests, then Lane D, then the coordinator
  retires the hand-authored chart and runs the full gate, then Lane E reviews,
  then the audit packet and closeout.
- Review handoff: Lane E inspects whether the artifact's frequencies match the
  source expectation table, whether any raise size or range value in the repo
  came from somewhere other than the committed export, whether an uncovered spot
  anywhere resolves to an action instead of a refusal, and whether the tie rule
  and depth rule are actually exercised rather than merely present.

## Blocker: the strategy cannot see the action sequence

Found at loop stage 4, while writing the tests and before any implementation
existed. That is what stage 4 is for.

This contract requires the strategy to build its chart query "from game state
through the same derivation Phase 04 ships: table size, stack depth, hero position,
and the ordered preflop action sequence in front of hero."

The first three are derivable from a `StrategyQuery`. The fourth is not.
`StrategyQuery` carries `seat`, `button_seat`, `stacks`, `blinds`, `to_call`,
`street_bet`, `min_raise_target`, and `pot`, and no action history at all. The
Phase 03 protocol is `decide(query)` and nothing else. Every existing `ChartQuery`
in the repo has its action sequence hand-written by a report script.

So a chart-backed strategy has no way to know whether it is facing a cutoff open, a
three-bet, or a limp. Without a spot key there is no lookup, and the whole phase
reduces to refusing every query.

Three ways out, needing a decision before any code:

1. Give the strategy the history. Add an optional preflop action sequence to
   `StrategyQuery`. Architecturally right: a strategy that needs history should be
   handed history, and Phase 07's simulator has it natively, so passing it costs
   nothing. Cost: a `contract-update` on Phase 03, which is a completed phase. The
   field is additive and defaulted, so no existing caller breaks.
2. Infer it from committed amounts. Per-seat commitment is visible in `stacks`
   against a known starting depth, so who put in what is recoverable. Order within
   the first orbit follows position order. But two different sequences can produce
   the same commitments, and resolving that is exactly the heuristic guessing
   `AGENTS.md` forbids. Viable only if every ambiguous reconstruction refuses,
   which needs its own proof.
3. Keep it outside the protocol. A separate entry point takes the sequence
   explicitly and `decide(query)` always refuses. Honest and fail-closed, but it
   means the phase ships a strategy the Phase 03 protocol cannot actually drive,
   and Phase 07 has to special-case it.

Recommended: option 1.

Resolved on 2026-08-11 by option 1. `StrategyQuery` now carries `preflop_actions`,
an ordered tuple of `SeatAction`, defaulted to empty. Phase 03's contract requires
it (`de8467a`) and the field ships with twelve tests (`3e78007`). The strategy at
stage 6 derives hero's position from the button and maps the seat-based history onto
chart positions, dropping folds when it builds the spot key.

While it was unsettled, `phase_status.yml` kept phase 05 at `future` and the two
new command IDs stayed unregistered, so the repo rested at idle with a green gate
rather than carrying a red one. Both are re-applied when the loop resumes at
stage 4.

## Slices

- [x] Stage 1: contract fleshed out with artifact, oracle, strategy, totality,
  and report criteria. Evidence: `docs/phase_contracts/PHASE_05_FULL_TABLE_PREFLOP.md`.
- [x] Stage 1: judgment-call list recorded before implementation. Evidence:
  `reports/phase_audits/decisions/PHASE_05_DECISIONS.md`.
- [ ] Stage 1 gate: `uv run python scripts/run_verify.py` green and committed.
- [ ] Human gate: Taylor answers the eight judgment calls and attests the export's
  provenance.
- [ ] Stage 2: implementation activated with the Stage 2 scope and
  `phase_status.yml` phase 05 set to `active`.
- [ ] Stage 2: lanes C, A, B, D delivered and integrated.
- [ ] Stage 2: hand-authored chart retired with the Phase 04 gate still green.
- [ ] Stage 2: independent review recorded, audit packet written, gate green,
  tagged `phase-05-complete`.

## Verification

Stage 1 runs the base gate only, because phase 05 is still `future` in
`phase_status.yml` and the derived gate therefore does not yet include its
commands.

Stage 2 command IDs:

- `pytest_full_table_preflop`
- `generate_preflop_strategy_report`
- `generate_strategy_query_report`

Stage 2 reports:

- `reports/active/latest_preflop_strategy_report.txt`
- `reports/active/latest_strategy_query_report.txt`

## Outcome

Gate green and tagged `phase-05-complete`. Thirty-six spots committed, 55 phase
tests, 318 test functions frozen across the suite.

The phase was driven through `scripts/loop_stage.py` and halted twice, both times
for reasons the gate could not have found.

**Halt one, stage 4.** Writing the tests before any implementation exposed that
`StrategyQuery` carried no action history, so a chart-backed strategy could not name
the spot it was in. Resolved by a Phase 03 contract-update adding `preflop_actions`.
Had the implementation been written first, it would have reconstructed the sequence
from committed amounts, which is the heuristic guessing this repo forbids, and it
would have passed a green gate.

**Halt two, stage 8.** Independent review found four blockers, none visible to the
gate. The domain reviewer measured the cost of the ruled collapse rule: taking the
highest-weight action folded hands the chart continues with more than half the time,
because folding is one bucket while continuing splits across calling and raising.
Fold-to-three-bet ran 72.8% against the solution's 59.8%, past the point where an
opponent's three-bet auto-profits as a pure bluff. Judgment call 3 was re-ruled to a
seeded weighted draw. The mechanical reviewer then found that stack depth was read
from the deepest seat rather than hero (a 12bb hero opened a 100bb range), that the
straddle and ante guard stopped looking after any action (an anted pot was
chart-backed for five of six seats), and that the seed was untested to the point
where the seed the contract forbids by name passed the whole suite.

Three of the four blockers were introduced by the coordinator. All four survived a
green gate including mutation checks. That is the case for keeping stage 8.

Deferred and recorded: `PER-SEAT-CONTRIBUTIONS-IN-QUERY` (exact straddle, ante, and
asymmetric-stack detection needs each seat's committed chips on the query),
`CHART-COVERAGE-EXPANSION`, and four non-blocking review findings listed in the
audit packet.

## Next Agent Bootstrap

State: complete. Superseded by the audit packet.

Historical note, kept because it is what the plan said mid-flight:
`CURRENT_TASK.yml` is `task_mode: contract-update`, `active_phase: "05"`,
`base_commit: e0ba4773ec7e73a679ba4540ce4adab4a2cf52ee`, with
`docs/phase_contracts/PHASE_05_FULL_TABLE_PREFLOP.md` and
`reports/phase_audits/decisions/PHASE_05_DECISIONS.md` approved.
Phase 05 is deliberately still `future` in `phase_status.yml`, exactly as Phase 04
did during its own contract stage, so the Stage 1 gate does not demand Phase 05
commands or reports.

The extracted chart is not yet in the repo. It sits outside the tree at
`~/Downloads/gtowizard_6max_nl25_100bb_preflop.json`, 36 spots, verified against
the source's own displayed combo counts by a checker that was run outside the
browser. Stage 2 Lane A commits it under `data/artifacts/preflop/sources/`.

Next command: `uv run python scripts/run_verify.py`, then commit Stage 1.

Do not activate Stage 2 until the judgment-call list has answers. The defaults are
written in; the point of the gate is that a human ruled on them.
