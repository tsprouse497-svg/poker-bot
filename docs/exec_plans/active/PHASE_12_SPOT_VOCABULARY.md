# ExecPlan: Phase 12 - Spot Vocabulary V2

Contract: `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`
Lane: worktree `~/projects/poker-bot-worktrees/phase-12`, branch `phase/12-spot-vocabulary-v2`,
pointer `verification/loop_runs/12.yml`, opened from `main` at `beec7d6`.
Policy: `auto_advance: false` - widening the key re-derives the committed artifact, so every
chart cell moves, and the vocabulary is what a later solve is configured against.

## Objective

Widen what a preflop spot key can say, close the two vocabulary gaps v1 filed against it,
and pay the measurement debt Phase 11 deliberately left open.

Inherited from `backlog.yml`, all tagged `phase: "12"`:

- `RAISE-SIZE-IN-SPOT-KEY` - keys record action names without sizes, so a 2.25bb open and a
  4bb open share one spot and every agreement rate is computed across prices the chart
  cannot tell apart.
- `SECOND-ORBIT-PREFLOP-SPOTS` - `solver_artifacts.schema.spot_key` rejects a sequence in
  which a position acts twice, so a four-bet and everything past it has no key.
- `CORPUS-INEXPRESSIBLE-SPOTS` - the measurement of what that costs: 19 of 3,048 real
  decision points, the largest single row of the real-hand refusal inventory.
- `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` - Phase 11 corrected the engine and the query
  every published number was measured through and recomputed none of them, by ruling. This
  is the first phase to re-run those measurements and it owes the restatement.

Ruling 8 of `docs/V2_ROADMAP.md` is settled: one solved opening price, and every other price
answered from it. This phase does not reopen it. What it owes the ruling is the two things
`docs/V2_RULING_MITIGATIONS.md` asks for in return - the size stays in the key and the
abstraction lives in the lookup, and every substituted answer says it was substituted.

Nothing is re-solved. No new chart, no new export, no new sample. The committed artifact is
re-derived from the source already in the tree, carrying the same ranges under new keys.

## Scope

Approved for the contract stage (`task_mode: contract-update`):

- `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`
- `reports/phase_audits/decisions/PHASE_12_SPOT_VOCABULARY_DECISIONS.md`
- `reports/phase_audits/reviews/PHASE_12_SPOT_VOCABULARY/**`

Expected for implementation, and not approved until the loop reaches stage 4:

- `src/poker_training_bot/solver_artifacts/schema.py`, `solver_artifacts/lookup.py`,
  `solver_artifacts/importer.py`
- `src/poker_training_bot/strategy/contract.py`, `strategy/preflop_chart.py`,
  `strategy/preflop_sizing.py`
- `src/poker_training_bot/data_pipeline/comparison.py`,
  `src/poker_training_bot/simulator/run.py`
- `scripts/convert_preflop_export.py`, `scripts/generate_spot_vocabulary_report.py`,
  `scripts/generate_preflop_strategy_report.py`,
  `scripts/generate_postflop_fallback_report.py`, `scripts/run_verify.py`
- `data/artifacts/preflop/six_max_nl25_100bb.json`,
  `data/artifacts/preflop/sizings/six_max_nl25_100bb.json`
- `tests/test_spot_vocabulary.py`, `verification/freeze.lock`, `verification/mutations.yml`
- `reports/phase_audits/PHASE_12_SPOT_VOCABULARY.md`

The re-derived artifact and sizing table are the one data change this phase makes, and they
are a re-keying rather than a re-solve: the bijection and the weight equality are what the
contract asks a test to prove. `docs/LOOP.md` lists any new or changed file under
`data/artifacts/**` as a halt condition, so that pair is expected to stop the loop for a
human look rather than pass silently.

Upstream contracts state the vocabulary this phase changes. Phase 04 declares the artifact
and chart contract, and Phase 05 the chart-backed strategy that reads it, so both are read
at stage 2 and amended in `contract-update` mode if their criteria contradict the widened
key. Which of them actually need text is settled there, not assumed here.

Forbidden throughout:

- `data/raw/**`, `data/processed/**` (existence rule)
- Any new solve, any chart derived from the Phase 10 GTOpen export, and any retirement of
  the 36-spot chart. That is proposed phase 14.
- Any widening of the query's table-state fields. Per-seat contributions, straddles, antes
  and asymmetric stacks are proposed phase 13.
- Any second solved opening price, and any nearest-spot, nearest-depth or
  nearest-hand-class matching. The price normaliser is the single named abstraction and it
  exists because a human ruled it.
- Any runtime solver call, browser observation, or LLM-backed poker decision.

## Delegation Plan

- No-delegation exception: the standing instruction in this account is not to call the Agent
  tool unless the operator requests it, and this phase was started without such a request.
  `AGENTS.md` step 6 therefore cannot be satisfied and step 10's self-review fallback
  applies. Implementation, every per-stage review the driver demands, and both stage-8
  passes are coordinator-owned, each review written as a separate read-only pass against the
  named diff with the mechanical and domain questions kept apart. This is the same exception
  phases 10 and 11 recorded; it must not be quietly dropped, and delegated reviewers are
  offered to Taylor rather than silently skipped.

## Slices

- [x] **S1 - Contract.** Seven criteria groups replacing the boilerplate: the size in the
      key, the second orbit, the ruled price abstraction, the re-derivation proof, the
      corpus inventory, the Phase 11 restatement, and evidence. Command IDs settled as
      `pytest_spot_vocabulary` and `generate_spot_vocabulary_report`, report as
      `reports/active/latest_spot_vocabulary_report.txt`. The skeleton's
      `generate_spot_coverage_report` was dropped because `generate_preflop_chart_report`
      already reports chart coverage and this phase reports what the vocabulary can say.
      Evidence: `loop_stage.py --phase 12 --advance` clears stage 1.
- [ ] **S2 - Decisions.** The judgment-call list, with the key rendering as the
      `frozen-into-data` item, since it goes into the committed artifact phase 14 is measured
      against. Also owed: whether the decision-audit schema version bumps when the query
      payload gains a raise amount, and whether the Phase 04 and Phase 05 contracts need
      amendment. Evidence: stage 2 check green.
- [ ] **S3 - Human gate.** `auto_advance: false`, so this stage halts and asks Taylor
      whatever the decision list files as `frozen-into-data`. Evidence: stage 3 check green
      after his answer lands in the decision record.
- [ ] **S4 - Tests.** `tests/test_spot_vocabulary.py`, authored from the contract alone, red
      on assertions against today's behaviour. Canaries for both new command IDs authored
      here rather than at stage 7, which is the lesson phases 08, 09 and 10 each paid for.
      Evidence: stage 4 check green.
- [ ] **S5 - Freeze.** `tests/` and `verification/` leave `approved_scope`, `base_commit`
      moves to the freeze commit. Evidence: stage 5 check green.
- [ ] **S6 - Build.** Schema and lookup, the substituted-price flag on the answer, the four
      history producers, the converter, the re-derived artifact and sizing table, and the
      report generator. Evidence: stage 6 check green.
- [ ] **S7 - Gate and bite.** Full `run_verify.py` plus `check_gate_bite`, including both new
      canaries. Evidence: stage 7 check green.
- [ ] **S8 - Review.** Two passes, mechanical and domain, written separately. The domain pass
      is pointed at the poker: whether a size-aware key answers the spot a player is actually
      in, and what the substitution census says about how often the chart answers a question
      nobody asked. Evidence: stage 8 check green.
- [ ] **S9 - Audit packet.** Checklist, the before-and-after keys, both checksums, the
      substitution census, the restated Phase 07 and Phase 08 numbers with their cause, and
      one number recomputable by hand. Evidence: stage 9 check green.
- [ ] **S10 - Closeout and tag.** Phase completed, plan filed, `phase-12-complete` tagged,
      task idle, tree clean. Evidence: stage 10 check green.

## Verification

Command IDs: `pytest_spot_vocabulary`, `generate_spot_vocabulary_report`, plus the full base
gate through `scripts/run_verify.py` and `scripts/check_gate_bite.py`.
Reports: `reports/active/latest_spot_vocabulary_report.txt`.

Both command IDs are declared by the contract and registered in `COMMANDS` in
`scripts/run_verify.py` at stage 4, alongside the tests that assert them, on the Phase 10
and Phase 11 precedent. `check_repo_consistency` requires a registered `pytest_*` command to
name a file that holds tests, so registering earlier would fail the gate against a test file
that does not exist yet. Until stage 4 the checker reports both as unregistered, which is
the expected mid-phase state and not a defect.

Regenerated reports this phase is expected to move, none of them hand-edited:
`latest_sample_refusal_inventory.txt` (loses its catch-all row),
`latest_sample_comparison_report.txt`, `latest_refusal_inventory.txt`,
`latest_preflop_chart_report.txt`, `latest_preflop_strategy_report.txt`,
`latest_decision_audit.jsonl`.

## Outcome

Fill this in before completing the gate.

## Next Agent Bootstrap

Work in `~/projects/poker-bot-worktrees/phase-12`, never in `~/projects/poker-bot` (that
worktree holds the finished phase 10 branch) and never in
`~/projects/poker-bot-worktrees/main`, which is where the fleet is driven from. The lane
holds `poker-loop.lock` in its own git dir.

Three lane pointers exist in this worktree (`11`, `12`, and the legacy `loop_state`), so the
driver refuses a bare invocation. Always name the lane:

```
cd ~/projects/poker-bot-worktrees/phase-12
uv run python scripts/loop_stage.py --phase 12
uv run python scripts/loop_stage.py --phase 12 --advance
```

Ask the driver what to do and do only that.

Subagents are unavailable in this operator's sessions, so every review the driver demands is
a coordinator-written read-only pass; the no-delegation exception above is the record of why.

Read before touching anything: `docs/V2_ROADMAP.md` ruling 8, and issue 3 of
`docs/V2_RULING_MITIGATIONS.md`, which is the ruling's reasoning and the two things it asks
of this phase. The failure mode it names is specific and it passes every obvious test:
dropping the size from the key instead of normalising the price at lookup.

State as of this commit: stage 1 complete, `phase_status.yml` has phase 12 `active`,
`CURRENT_TASK.yml` is `contract-update` with the three contract-stage paths approved. Next
is stage 2, the decision list, and stage 3 halts for Taylor because `auto_advance` is false.
</content>
