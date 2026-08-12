# ExecPlan: Phase 06, Conservative Postflop Fallback For Simulation Continuity

## Objective

Pass the Phase 06 gate: `pytest_postflop_fallback` and
`generate_postflop_fallback_report` green through `scripts/run_verify.py`, with the
full derived gate and `check_gate_bite` green, and the phase tagged
`phase-06-complete`.

Phase 05 left the bot able to play preflop and unable to continue.
This phase delivers a postflop fallback that never invests unless the investment
cannot lose, and a composite strategy that routes preflop to the chart and
postflop to the fallback so Phase 07 has one object to hand a hand to.

## Scope

Approved for the contract stage:

- `docs/phase_contracts/PHASE_06_POSTFLOP_FALLBACK.md`
- `reports/phase_audits/decisions/**`

Expected to be approved at the test stage and then narrowed at the freeze stage,
per the loop:

- `tests/test_postflop_fallback.py`
- `verification/mutations.yml`, `verification/freeze.lock`
- `scripts/run_verify.py` (command registration only)
- `src/poker_training_bot/strategy/postflop_fallback.py`
- `src/poker_training_bot/strategy/composite.py`
- `scripts/generate_postflop_fallback_report.py`
- `reports/phase_audits/PHASE_06_POSTFLOP_FALLBACK.md`
- `reports/phase_audits/reviews/PHASE_06_POSTFLOP_FALLBACK.md`

Forbidden: `data/raw/**`, `data/processed/**`.
No new file under `data/artifacts/**` or `data/samples/**`, which is what makes
this phase eligible to advance unattended under `verification/loop_policy.yml`.
`src/poker_training_bot/strategy/reference.py`, `contract.py`, `preflop_chart.py`,
and `preflop_sizing.py` are read-only for this phase.

## Delegation Plan

- Worker lanes: four bounded lanes. Lane T authors the phase tests from the
  contract alone at loop stage 4, before any implementation exists. Lane A builds
  the postflop fallback strategy and its river unbeatable enumeration. Lane B
  builds the composite strategy that routes preflop to the chart and postflop to
  the fallback. Lane C builds the report generator and the postflop decision audit
  output. Lane R is two independent read-only reviewers at stage 8, one mechanical
  and one poker-domain.
- Ownership: Lane T owns `tests/test_postflop_fallback.py` and nothing else. Lane A
  owns `src/poker_training_bot/strategy/postflop_fallback.py`. Lane B owns
  `src/poker_training_bot/strategy/composite.py`. Lane C owns
  `scripts/generate_postflop_fallback_report.py`. The coordinator owns command
  registration in `scripts/run_verify.py`, the mutation entries in
  `verification/mutations.yml`, `verification/freeze.lock`, `CURRENT_TASK.yml`,
  `phase_status.yml`, the contract, the decision record, the audit packet, and
  every commit. Lane A, B, and C may read `tests/**` and may never write to it;
  loop stage 5 removes `tests/` from `approved_scope` so `check_scope.py` enforces
  that mechanically.
- Expected outputs: Lane T returns a test file that fails for the right reason, an
  assertion or a missing `poker_training_bot` module, plus a list of the contract
  criteria each test pins. Lane A and Lane B each return a module and the
  `pytest_postflop_fallback` result they last observed. Lane C returns a generator
  plus the two report files it wrote. Lane R returns findings classified blocker or
  not, written to `reports/phase_audits/reviews/PHASE_06_POSTFLOP_FALLBACK.md`.
- Status: Lane T planned. Lane A planned. Lane B planned. Lane C planned. Lane R
  planned.
- Integration order: Lane T lands and is frozen before any builder starts. Lane A
  lands first because Lane B consumes its interface, Lane B second, Lane C last
  because it reports on both. The coordinator runs the phase command after each
  lane, integrates, and commits; a lane that fails its own command twice on the
  same assertion halts the loop rather than being repaired again.
- Review handoff: the mechanical reviewer inspects that the fallback returns a
  decision for every engine-legal postflop action set, that no path can bet or
  raise, that the composite adds no decision of its own, that a preflop chart
  refusal survives the composite unchanged, and that the enumeration in the tests
  is exhaustive rather than sampled. The poker-domain reviewer inspects whether
  "beats every possible holding" is the right and correctly implemented bar for the
  one place this bot puts money in postflop, whether folding a hand that can only
  be tied is defensible, and what the river-only restriction costs.

## Slices

- [ ] Stage 1, contract: real acceptance criteria and this plan. Evidence:
  `loop_stage.py --advance` past stage 1.
- [ ] Stage 2, decisions: judgment-call record with a reversibility class per item.
  Evidence: `--advance` past stage 2.
- [ ] Stage 3, human gate: no unanswered `frozen-into-data` item. This phase writes
  no committed data, so every call is expected to be `runtime-reversible` and
  reported afterwards rather than blocking.
- [ ] Stage 4, tests: Lane T authors `tests/test_postflop_fallback.py`;
  coordinator registers `pytest_postflop_fallback` and
  `generate_postflop_fallback_report`, and adds the mutations that must make the
  new command fail. Evidence: the command is red on assertions or a missing module.
- [ ] Stage 5, freeze: `freeze_tests.py`, then `tests/` and `verification/` leave
  `approved_scope`. Evidence: `check_test_freeze` green.
- [ ] Stage 6, build: Lane A, then Lane B, then Lane C. Evidence: both contract
  commands green.
- [ ] Stage 7, gate: full `run_verify.py` green and `check_gate_bite` green.
- [ ] Stage 8, review: Lane R, two reviewers, findings recorded.
- [ ] Stage 9, audit: audit packet with summary, non-coding checklist, review
  findings, decision outcomes, and one hand-recomputable number.
- [ ] Stage 10, closeout: plan filed as completed, phase completed, tag, idle, gate
  again, merge.

## Verification

Command IDs: `pytest_postflop_fallback`, `generate_postflop_fallback_report`, plus
the full derived gate from `scripts/run_verify.py` and `check_gate_bite`.

Reports: `reports/active/latest_postflop_fallback_report.txt`,
`reports/active/latest_postflop_decision_audit.jsonl`.

## Outcome

Not yet complete.

## Next Agent Bootstrap

The loop drives this phase.
Run `uv run python scripts/loop_stage.py` to see the current stage, do exactly the
one stage it names, then run `uv run python scripts/loop_stage.py --advance`.
State lives in `verification/loop_state.yml`; the branch is
`phase/06-postflop-fallback`; the worktree lock is `.git/poker-loop.lock`.
`uv` is on PATH, so `uv run python ...` works directly.
