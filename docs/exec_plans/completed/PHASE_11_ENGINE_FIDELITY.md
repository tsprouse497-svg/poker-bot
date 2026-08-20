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
- [x] **S2 - Decisions.** Nine judgment calls, every one `runtime-reversible`, which is
      right because the phase commits no data. Written against measurements taken on this
      branch rather than against the backlog's prose, and two of those measurements
      contradicted a stage-1 criterion, so the contract was corrected here. Two deferrals
      filed as backlog entries. Evidence: stage 2 check green.
- [x] **S3 - Human gate.** Nothing blocks: no `frozen-into-data` call exists. Decision 3,
      the reopening rule, is flagged in the record as the one call worth a human's eyes
      that the loop will not stop for, and is reported to Taylor rather than buried.
      Evidence: stage 3 check green.
- [x] **S4 - Upstream contract amendments.** Phase 03's reopening criterion and Phase 06's
      "never refuses postflop" criterion, both amended in `contract-update` mode before any
      test was authored against them. The Phase 01 and Phase 02 contracts, which the roadmap
      also expected, carry only boilerplate under the `CONTRACT-CRITERIA-BACKFILL` exemption
      and so contradict nothing. Evidence: commit `62b5dd7`.
- [x] **S5 - Tests.** `tests/test_engine_fidelity.py`: 49 tests, 28 red on assertions
      against today's behaviour and 21 green as the over-application guards. Two frozen
      tests of completed phases moved with them, because this phase's fixes make them
      assert the old behaviour. Four canaries authored here rather than at stage 7,
      against the text the implementation must produce - which is the miss phases 08, 09
      and 10 each recorded. Evidence: stage 4 check green.
- [x] **S6 - Freeze.** 49 tests and 23 files in `verification/freeze.lock`. `tests/`,
      `verification/` and `scripts/run_verify.py` left `approved_scope`; `base_commit` moved
      to the freeze commit. Evidence: stage 5 check green.
- [x] **S7 - Build.** The six fixes, plus the report generator. The stage halted once: ten
      frozen tests failed and none was an implementation defect, so the repair landed in its
      own task with the builder files out of scope. Evidence: stage 6 check green.
- [x] **S8 - Gate and bite.** Full `run_verify.py` green at 41 commands, `check_gate_bite`
      green. The four canaries authored at stage 4 against text that did not yet exist all
      matched the implementation and bit. Evidence: stage 7 check green.
- [x] **S9 - Review.** Two passes, mechanical and domain, written separately. The domain
      pass found a blocker no frozen test reaches: every reopening test opens its street
      with a full bet, so the reference level and the street's opening level coincide and
      two different rules agree. They do not agree when the street opens with a short
      all-in. Fixed, pinned by two tests and a fifth canary, with a second finding filed
      rather than fixed. Evidence: stage 8 check green.
- [x] **S10 - Audit packet and closeout.** Sixteen-row checklist, the reopening example in
      chips, one number recomputable by hand, and the phase's own finding: the corpus
      comparison does not move. Evidence: stage 9 check green, and this closeout.

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

All six inherited defects closed, and a seventh found by the stage-8 domain review and
closed with them. The phase commits no data, so `auto_advance: true` held throughout and
no judgment call blocked on a human.

What the phase bought, stated as narrowly as the evidence allows. Each fix has a test that
fails without it, so each is real. None of them moves a number in the 3,048-decision corpus
comparison, which is byte-identical to main's - because six-handed Pluribus play contains
no surrendered rivers and no chains of short all-ins. Both spots occur in the real-room
hands this repo now wants to ingest, which is what the phase was for.

Two process results worth carrying forward. Authoring mutation canaries at stage 4, against
text the implementation did not yet contain, worked: four of four matched on the first try
and bit, where phases 08, 09 and 10 each wrote their own canaries after the code and each
filed that as the same miss. And the per-stage review earned its keep three times over -
stage 1 caught a criterion that would have revoked the phase's own auto-advance permission,
stage 4 caught five weak tests before the freeze preserved them, and stage 8 caught a poker
rule the whole frozen suite agreed with.

Four items deferred, each filed with the phase that owns it:
`PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` (12), `STRATEGY-QUERY-STREET-BET-NAME` (13),
`UNDER-SIZED-ALL-IN-BET-DOES-NOT-BAR-PRIOR-CHECKERS` (contract-update), and the new road
into `MUTATION-SENTINEL-IS-COMMITTABLE` recorded at stage 7.

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

State as of this commit: phase 11 `completed` and tagged `phase-11-complete`,
`CURRENT_TASK.yml` reset to idle, the lane at stage 11. The lane still has to be merged
back: run `uv run python scripts/loop_fleet.py --integrate 11` from
`~/projects/poker-bot-worktrees/main` and follow the runbook it prints. Integration is
serial by design, and this is the only live lane.

One open question for Taylor, which the loop did not stop for because it is
`runtime-reversible`: decision 3, the reopening rule. In a real room, when two players move
all-in for short amounts one after the other and their two increments together add up to a
full raise, does the player who already acted get to raise again? This phase says yes. If
the answer is no, decision 3 flips to `keep-the-current-strict-rule`, the accumulation
backlog item is restated as a deliberate difference rather than a defect, and nothing else
in the phase changes.
