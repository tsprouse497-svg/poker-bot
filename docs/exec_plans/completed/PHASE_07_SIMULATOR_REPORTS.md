# ExecPlan: Phase 07, Offline Simulator And Bot/Profile Comparison Reports

## Objective

Pass the Phase 07 gate: `pytest_simulator` and `generate_profile_comparison_report`
green through `scripts/run_verify.py`, with the full derived gate and
`check_gate_bite` green, and the phase tagged `phase-07-complete`.

Phase 06 left the repo with one strategy object that can play a hand end to end and
nothing that deals one. This phase adds the dealer and the first report that compares
two profiles over many hands, with the measurement boundary Phase 06 imposed stated
in the report rather than left to be inferred.

## Scope

Approved for the contract stage:

- `docs/phase_contracts/PHASE_07_SIMULATOR_REPORTS.md`
- `reports/phase_audits/decisions/**`

Expected to be approved at the test stage and then narrowed at the freeze stage,
per the loop:

- `tests/test_simulator.py`
- `verification/mutations.yml`, `verification/freeze.lock`
- `scripts/run_verify.py` (command registration only)
- `src/poker_training_bot/simulator/**`
- `src/poker_training_bot/profiles/**`
- `scripts/generate_profile_comparison_report.py`
- `reports/phase_audits/PHASE_07_SIMULATOR_REPORTS.md`
- `reports/phase_audits/reviews/PHASE_07_SIMULATOR_REPORTS.md`

Forbidden: `data/raw/**`, `data/processed/**`.
No new file under `data/artifacts/**`. The simulator writes reports, not fixtures,
which is what keeps this phase eligible to advance unattended under
`verification/loop_policy.yml`. `poker_core/`, `hand_history/`, `strategy/`, and
`solver_artifacts/` are read-only for this phase: the whole point is that the
simulator consumes them unchanged rather than loosening one to make a hand fit.

## Delegation Plan

- Worker lanes: four bounded lanes. Lane T authors the phase tests from the contract
  alone at loop stage 4, before any implementation exists. Lane A builds the
  simulator - seeded shuffling, hand loop, street progression, pot award, chip
  conservation, and the normalized-hand emission the replay cross-check needs. Lane B
  builds the profiles package and seats the Phase 06 composite and the Phase 03
  reference strategy. Lane C builds the comparison report generator and its decision
  audit. Lane R is two independent read-only reviewers at stage 8, one mechanical and
  one poker-domain.
- Ownership: Lane T owns `tests/test_simulator.py` and nothing else. Lane A owns
  `src/poker_training_bot/simulator/**`. Lane B owns
  `src/poker_training_bot/profiles/**`. Lane C owns
  `scripts/generate_profile_comparison_report.py`. The coordinator owns command
  registration in `scripts/run_verify.py`, the mutation entries in
  `verification/mutations.yml`, `verification/freeze.lock`, `CURRENT_TASK.yml`,
  `phase_status.yml`, the contract, the decision record, the audit packet, and every
  commit. Lanes A, B and C may read `tests/**` and may never write to it; loop stage 5
  removes `tests/` from `approved_scope` so `check_scope.py` enforces that
  mechanically.
- Expected outputs: Lane T returns a test file that fails for the right reason, an
  assertion or a missing `poker_training_bot` module, plus a list of the contract
  criteria each test pins. Lane A returns the simulator package and the
  `pytest_simulator` result it last observed. Lane B returns the profiles package and
  the two seated profiles. Lane C returns a generator plus the report it wrote. Lane R
  returns findings classified blocker or not, written to
  `reports/phase_audits/reviews/PHASE_07_SIMULATOR_REPORTS.md`.
- Status: Lane T landed at stage 4 and was frozen at stage 5. Lanes A, B and C landed
  together in the stage 6 build commit, in that order. Lane R ran at stage 8 as two
  coordinator review passes rather than as delegated read-only subagents, because subagent
  delegation is disabled for this session; `AGENTS.md` step 10 allows that with the reason
  recorded, and it is stated at the top of the review notes.
- Delegation availability: subagent delegation is disabled in this session, so unless
  that changes the coordinator implements each lane in the lane order below and the
  stage 8 reviewers are coordinator passes with the reason recorded, which `AGENTS.md`
  step 10 permits. Phase 06 recorded the same exception; the cost is real and is
  stated at the top of the review notes rather than left implicit.
- Integration order: Lane T lands and is frozen before any builder starts. Lane A
  first because everything consumes it, Lane B second, Lane C last because it reports
  on both. The coordinator runs the phase command after each lane, integrates, and
  commits; a lane that fails its own command twice on the same assertion halts the
  loop rather than being repaired again.
- Review handoff: the mechanical reviewer inspects that the simulator adds no poker
  rule of its own, that every applied action came from a `StrategyDecision`, that
  chips are conserved per hand rather than in aggregate, that the seed fully determines
  the run with no clock or global `random` state anywhere, that a refusal ends a hand
  as a counted outcome, and that the replay cross-check compares real decision points
  rather than counting them. The poker-domain reviewer inspects whether the comparison
  measures what the report claims, whether the hand count is enough for the difference
  it prints, whether the noise threshold is honest, and whether a reader could
  mistake any figure for a statement about postflop play.

## Slices

- [x] Stage 1, contract: real acceptance criteria and this plan. Evidence:
  `loop_stage.py --advance` past stage 1.
- [x] Stage 2, decisions: judgment-call record with a reversibility class per item.
  Evidence: `--advance` past stage 2.
- [x] Stage 3, human gate: no unanswered `frozen-into-data` item. This phase writes
  reports rather than fixtures, so every call is expected to be `runtime-reversible`.
  Phase 06 is the argument for putting the list to Taylor anyway: two reversible calls
  there proceeded on their defaults, went green, and cost a re-ruling at stage 8.
- [x] Stage 4, tests: Lane T authors `tests/test_simulator.py`; coordinator registers
  `pytest_simulator` and `generate_profile_comparison_report`, and adds the mutations
  that must make the new command fail. Evidence: the command is red on assertions or a
  missing module.
- [x] Stage 5, freeze: `freeze_tests.py`, then `tests/` and `verification/` leave
  `approved_scope`. Evidence: `check_test_freeze` green.
- [x] Stage 6, build: Lane A, then Lane B, then Lane C. Evidence: both contract
  commands green.
- [x] Stage 7, gate: full `run_verify.py` green and `check_gate_bite` green.
- [x] Stage 8, review: Lane R, two reviewers, findings recorded.
- [x] Stage 9, audit: audit packet with summary, non-coding checklist, review
  findings, decision outcomes, and one hand-recomputable number.
- [x] Stage 10, closeout: plan filed as completed, phase completed, tag, idle, gate
  again, merge.

## Verification

Command IDs: `pytest_simulator`, `generate_profile_comparison_report`, plus the full
derived gate from `scripts/run_verify.py` and `check_gate_bite`.

Reports: `reports/active/latest_profile_comparison_report.txt`.

Watch the gate's run time. Phase 06 took it from 5 seconds to 65 because the turn
enumeration runs once per mutation, and a simulation of many hands can do worse. The
hand count belongs in the report as a stated number, and if the gate cannot afford the
count the comparison needs, that is a finding for the decision record rather than a
number to quietly shrink.

## Outcome

Complete, with one finding recorded rather than fixed.

The bot can now be dealt to. The simulator borrows every poker rule from Phase 01 and
decides only when to ask; the profiles name what is being compared; the report leads with
what it cannot claim. Self-play nets exactly zero over 600 hands, every measured hand was
re-derived by the frozen Phase 02 replayer, and the floor run puts the chart bot 14.9
standard errors above a bot that folds everything.

Two things went wrong on the way and both are worth keeping.

Three of four mutation canaries survived their first run. Two were errors in the canaries
themselves - a seed shift that was deterministic, and a disabled assertion that never
fires - and the third was correct and exposed that every refusal assertion in the frozen
tests passed vacuously when no hand was refused. Repairing them needed the test file and
the mutation list back in scope, so it landed as its own task rather than as a reach
around the freeze.

Stage 8 then found the phase's real defect: a voided hand's record keeps only the blind
posts, because a street is filed only once its betting round finishes and a refusal aborts
the round. So 565 real actions across 128 hands are discarded, and the report's headline
21.3% refusal figure is a count where it claims to be a list of uncovered spots. Taylor
chose to close the phase with that recorded and address it next, together with teaching a
refusal to name the spot it missed. `SIMULATOR-VOIDED-HAND-RECORD`.

The phase's most valuable output is the one nothing in the contract asked for: the charts
have no answer for 21.3% of self-play hands, concentrated in three-bet and four-bet trees.
That is the first countable measurement of this repo's own preflop coverage gap.

## Next Agent Bootstrap

The loop drives this phase.
Run `uv run python scripts/loop_stage.py` to see the current stage, do exactly the
one stage it names, then run `uv run python scripts/loop_stage.py --advance`.
State lives in `verification/loop_state.yml`; the branch is
`phase/07-simulator-reports`; the worktree lock is `.git/poker-loop.lock`.
`uv` is on PATH, so `uv run python ...` works directly.

Read `reports/phase_audits/reviews/PHASE_06_POSTFLOP_FALLBACK.md` before stage 8.
Phase 06's blocker was a rule the contract specified correctly and the code
implemented correctly, and that was wrong at the table. Nothing mechanical can catch
that class of error, so the stage 8 domain pass has to argue the poker from first
principles rather than check the code against the contract.
