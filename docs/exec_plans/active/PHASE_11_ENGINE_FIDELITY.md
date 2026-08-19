# ExecPlan: Phase 11 - Engine And Query Fidelity

Contract: `docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`
Lane: worktree `~/projects/poker-bot-worktrees/phase-11`, branch `phase/11-engine-and-query-fidelity`,
pointer `verification/loop_runs/phase-11.yml`, opened from `main` at `1b8314c`.
Policy: `auto_advance: true` - the phase writes no committed data and every fix is
provable by a test that fails against today's behaviour.

## Objective

Close six correctness defects that v1's own reviews found, diagnosed, and filed, none of
which the phase that found them could fix.
Every one of them sits under a later measurement, so they are closed before anything
derives a chart or re-measures agreement.

Inherited from `backlog.yml`, all tagged `phase: "11"`:

- `FOLD-WHEN-FREE` - the engine calls a fold illegal when checking is free, so any real
  history containing an open fold does not replay at all.
- `STREET-BET-MEANING-AMBIGUOUS` - `StrategyQuery.street_bet` carries no docstring, has
  two readings, and `scripts/generate_strategy_query_report.py` uses the wrong one, so
  replayed hands reach the chart with a mis-derived stack depth and refuse for the wrong
  reason.
- `DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE` - `DecisionAuditRecord` computes the all-in
  ceiling as `street_bet + stack`, which is too high by exactly `to_call`.
- `FALLBACK-FAIL-CLOSED-CAN-CALL` - `PostflopFallbackStrategy._fail_closed` can invest
  and can return a postflop refusal, both of which the Phase 06 contract says never happen.
- `UNDER-RAISE-ACCUMULATION` - `TurnState` measures each short all-in against the
  immediately preceding bet level, so consecutive short all-ins that together amount to a
  full raise never reopen betting.
- `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK` - the `check_solver_export_expectations`
  entry in the command registry advertises a directional bound withdrawn on 2026-08-18.

Nothing downstream is re-derived here. No chart, no artifact, and no committed sample
changes; the phase commits no data at all.

## Scope

Approved for the contract stage (`task_mode: contract-update`):

- `docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`
- `reports/phase_audits/decisions/PHASE_11_ENGINE_FIDELITY_DECISIONS.md`
- `reports/phase_audits/reviews/PHASE_11_ENGINE_FIDELITY/**`

Expected for implementation, and not approved until the loop reaches stage 4:

- `src/poker_training_bot/poker_core/engine.py`, `poker_core/order.py`
- `src/poker_training_bot/strategy/contract.py`, `strategy/postflop_fallback.py`
- `scripts/generate_strategy_query_report.py`, `scripts/run_verify.py`
- `tests/test_engine_fidelity.py`, `verification/freeze.lock`, `verification/mutations.yml`
- `reports/phase_audits/PHASE_11_ENGINE_FIDELITY.md`

Four upstream contracts state the behaviour some of these fixes change, so they are
amended in `contract-update` mode before the tests are frozen, never during
implementation: Phase 01 (`fold` legality and the reopening rule), Phase 02 (what a
replayable history may contain), Phase 03 (the reopening rule as an acceptance criterion,
the meaning of `street_bet`, and the all-in ceiling), and Phase 06 (what the fail-closed
branch is allowed to return). Which of them actually need text is settled at stage 2 and
recorded there rather than assumed here.

Forbidden throughout:

- `data/raw/**`, `data/processed/**` (existence rule)
- Any change to a committed chart, artifact, sample, or source card. This phase commits
  no data.
- Any re-measurement whose inputs these fixes move. A corrected agreement rate belongs to
  the phase that owns the measurement, not to the phase that fixed the measuring stick.
- Any runtime solver call, browser observation, or LLM-backed poker decision.

## Delegation Plan

- No-delegation exception: the operator declared subagents unavailable for this session
  in the message that started the phase, and the standing instruction in this account is
  not to call the Agent tool unless it is requested. `AGENTS.md` step 6 therefore cannot
  be satisfied and step 10's self-review fallback applies. Implementation, every
  per-stage review the driver demands, and both stage-8 passes are coordinator-owned,
  each review written as a separate read-only pass against the named diff with the
  mechanical and domain questions kept apart.

## Slices

- [x] **S1 - Contract.** Seven criteria groups replacing the boilerplate: one per inherited
      defect, one for the upstream contract amendments, and one for evidence and reports.
      Command IDs settled as `pytest_engine_fidelity` and `generate_engine_fidelity_report`,
      report as `reports/active/latest_engine_fidelity_report.txt`. The stage-1 review found
      three problems in the contract it reviewed and all three were fixed inside it, which
      is why the notes and the contract land in the same commit. Evidence:
      `loop_stage.py --advance` clears stage 1.
- [ ] **S2 - Decisions.** The judgment calls each fix carries, with a reversibility class
      on every one. The load-bearing ones are how far the reopening rule goes, whether a
      free fold is accepted everywhere or only on replay, and whether the fail-closed
      branch folds or refuses. Evidence: stage 2 check green.
- [ ] **S3 - Human gate.** Any `frozen-into-data` call ruled by Taylor. Expected to be
      thin: the phase writes no data, so most calls should be `runtime-reversible`.
      Evidence: stage 3 check green.
- [ ] **S4 - Upstream contract amendments.** Whatever S2 shows is contradicted in the
      Phase 01, 02, 03, and 06 contracts, in `contract-update` mode, before any test is
      authored against it. Evidence: the amended contracts and their review note.
- [ ] **S5 - Tests.** Authored before implementation, one file, each defect pinned by a
      test that fails against today's behaviour and a test that the corrected behaviour
      is not over-applied. Evidence: `pytest_engine_fidelity` red at stage 4, on
      assertions rather than on an import error.
- [ ] **S6 - Freeze.** `tests/` and `verification/` leave `approved_scope`. Evidence:
      stage 5 check green.
- [ ] **S7 - Build.** The six fixes. Evidence: every command the contract declares green.
- [ ] **S8 - Gate and bite.** Full `run_verify.py`, plus canaries aimed at this phase's
      own command so the new coverage is proved to bite. Evidence: stage 7 check green.
- [ ] **S9 - Review.** Mechanical and domain passes. The domain question here is poker
      rules rather than code: does the reopening rule match the rule real rooms use, and
      does accepting a free fold change any hand the bot itself would play.
- [ ] **S10 - Audit packet and closeout.**

## Verification

Command IDs: `pytest_engine_fidelity`, `generate_engine_fidelity_report`, plus the full
base gate through `scripts/run_verify.py` and `scripts/check_gate_bite.py`.
Reports: `reports/active/latest_engine_fidelity_report.txt`.

Both command IDs are declared by the contract and registered in `COMMANDS` in
`scripts/run_verify.py` at stage 4, alongside the tests that assert them, on the Phase 10
precedent. Until then `check_repo_consistency` reports both as unregistered, which is the
expected mid-phase state and not a defect. The one-line
`GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK` fix lives in the same file and
therefore lands at stage 4 with them, because stage 5 removes `run_verify.py` from
`approved_scope`.

## Outcome

Not yet complete.

## Next Agent Bootstrap

Work in `~/projects/poker-bot-worktrees/phase-11`, never in `~/projects/poker-bot` (that
worktree holds the finished phase 10 branch) and never in `~/projects/poker-bot-worktrees/main`.
The lane holds `poker-loop.lock` in its own git dir.

Ask the driver what to do and do only that:

```
cd ~/projects/poker-bot-worktrees/phase-11
uv run python scripts/loop_stage.py --phase 11
uv run python scripts/loop_stage.py --phase 11 --advance
```

Subagents are unavailable in this operator's sessions, so every review the driver demands
is a coordinator-written read-only pass; the no-delegation exception above is the record
of why, and it must not be quietly dropped.

State as of this commit: phase 11 set `active`, task seeded as `phase-11-contract` in
`contract-update` mode from `1b8314c`, loop started, stage 0 precheck.
