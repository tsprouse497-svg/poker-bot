# ExecPlan: Phase 13, Table-State Fidelity

Contract: `docs/phase_contracts/PHASE_13_TABLE_STATE.md`
Lane: worktree `~/projects/poker-bot-worktrees/phase-13`, branch `phase/13-table-state-fidelity`,
opened from `main` at `12469b1`.
Loop pointer: `verification/loop_runs/13.yml`. Driver: `uv run python scripts/loop_stage.py --phase 13`.

## Objective

Take phase 13 from a skeleton contract to a tagged green gate across the full derived verify
gate plus `check_gate_bite`, closing or restating the five `phase: "13"` entries in
`backlog.yml`: `PER-SEAT-CONTRIBUTIONS-IN-QUERY`, `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`,
`ASYMMETRIC-EFFECTIVE-STACKS`, `BLIND-STRUCTURE-VARIANTS`, and
`STRATEGY-QUERY-STREET-BET-NAME`.

The phase changes the runtime query and what the strategy can see through it. It commits no
artifact, no chart, and no sample, and it does not touch the spot key.

## Scope

Approved at stage 1 (`contract-update`), which is where this plan is written:

- `docs/phase_contracts/PHASE_13_TABLE_STATE.md`
- `docs/phase_contracts/PHASE_03_STRATEGY_CONTRACT.md` (two-line amendment)
- `docs/phase_contracts/PHASE_06_POSTFLOP_FALLBACK.md` (two-line amendment)
- `reports/phase_audits/reviews/PHASE_13_TABLE_STATE/**`
- standing scope only for `CURRENT_TASK.yml`, `phase_status.yml`, `backlog.yml`,
  `verification/loop_runs/**`, the generated docs, `docs/exec_plans/**`, `reports/active/**`

Expected at later stages, each needing its own `scope_change_log` entry when it is opened:

- stage 2: `reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`
- stage 4: `tests/test_table_state.py`, the frozen-test migrations across completed phases,
  `verification/mutations.yml`, `scripts/run_verify.py` (command registration only)
- stage 6: `src/poker_training_bot/strategy/contract.py`,
  `src/poker_training_bot/strategy/preflop_chart.py`,
  `src/poker_training_bot/simulator/table.py`,
  `src/poker_training_bot/data_pipeline/comparison.py`,
  `src/poker_training_bot/solver_artifacts/spot_key.py` (docstring correction only),
  `scripts/generate_table_state_report.py` and its measures module, and the four report
  generators that build a query
- stage 9: `reports/phase_audits/PHASE_13_TABLE_STATE.md`

Forbidden throughout: `data/artifacts/**`, `data/samples/**`, the spot key grammar, the
artifact schema, `AGENTS.md`, the check scripts, and `tests/**` from stage 5 onwards.

## Delegation Plan

Subagents are authorized for this phase (Taylor, 2026-08-21). Phases 10, 11 and 12 recorded a
no-delegation exception and self-reviewed every stage, which the phase 12 packet itself names
as the weak link, so `AGENTS.md` step 6 is satisfied properly here and every stage review goes
to an independent read-only reviewer rather than to the coordinator.

- Worker lanes: L1 query shape and validation; L2 producers and the `to_call` cap; L3 the
  preflop strategy's depth, asymmetry and blind-structure detection; L4 the `street_bet`
  rename and the decision-audit version bump; L5 the report generator and its measures; L6 the
  frozen-test migration across completed phases, authored at stage 4 alongside the phase's own
  tests.
- Ownership: L1 owns `strategy/contract.py`. L2 owns `simulator/table.py`,
  `data_pipeline/comparison.py` and the four query-building report scripts. L3 owns
  `strategy/preflop_chart.py` and the `spot_key.py` docstring correction. L4 owns the rename
  sweep across every file naming the field, which crosses all other lanes and therefore runs
  alone. L5 owns `scripts/generate_table_state_report.py` and its measures module. L6 owns
  `tests/**` at stage 4 only. The coordinator owns `CURRENT_TASK.yml`, the contract, this plan,
  `backlog.yml`, `verification/mutations.yml`, command registration in `scripts/run_verify.py`,
  every merge, the gate, and the audit packet.
- Expected outputs: each lane returns a patch confined to the files it owns, the commands it
  ran with their output, a changed-file summary, and the frozen tests it made pass or found
  failing. L5 also returns the report text. L6 returns a per-file verdict saying whether an
  assertion was migrated or rewritten, and why.
- Status: L1 planned; L2 planned; L3 planned; L4 planned; L5 planned; L6 planned. No lane is
  assigned before stage 4 freezes the tests, because a builder must not reach the tests it is
  measured by.
- Integration order: L1 first, alone, because every other lane depends on the field existing.
  Then L2 and L3 in parallel on disjoint files, then L4 alone across the whole tree, then L5
  once the numbers it reports are real. The coordinator runs the phase's own commands after
  each merge and the full gate only after L5.
- Review handoff: an independent read-only reviewer reads the stage diff against the question
  the driver prints, writes to
  `reports/phase_audits/reviews/PHASE_13_TABLE_STATE/stage-NN-name.md` with the three required
  headings, and never edits the code it reviews. Stage 8 gets two: one mechanical, one domain,
  and the domain reviewer is briefed to judge the poker rather than the code's fidelity to the
  contract. The reviewer at stage 4 is the one that matters most, because a wrong test authored
  there survives the freeze and every mechanical check after it.

## Slices

- [x] S1 Contract. Skeleton replaced with criteria written against the five backlog entries,
      plus the two-line amendments to the Phase 03 and Phase 06 contracts. Two independent
      reviewers found six blockers between them, all resolved in the contract; two new backlog
      entries were filed from their findings. Evidence: the contract at 299 of 300 lines with
      every backlog citation resolving, `check_contracts`, `check_file_sizes`, `check_scope`
      and `check_execplan_delegation` green, and the stage-1 review note.
- [ ] S1a Prerequisite, outside this phase's task. `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP`
      is a `contract-update` task of its own: `PHASE_11_ENGINE_FIDELITY.md` is at 300 of 300
      lines, names `street_bet` in three criteria that this phase renames, and asserts an
      all-in-ceiling claim this phase makes false. `AGENTS.md` forbids raising the cap and
      rules the answer is a rewrite folding its amendments into the criteria they amend. This
      phase must not tag before that task has run.
- [ ] S2 Decisions. Judgment calls recorded with a reversibility class before any code:
      the field names and shape, whether the query carries street and hand contributions or
      only one, what a shallower seat's refusal code is called, whether a straddle and an ante
      get one code or two, the rename target, and how far the frozen-test migration reaches.
- [ ] S3 Human gate. Any `frozen-into-data` call answered. This phase should have none; one
      appearing is the signal that scope drifted into the artifact.
- [ ] S4 Tests. `tests/test_table_state.py` authored red, the frozen-test migrations authored
      with it, the mutation canaries authored before any implementation, and both command IDs
      registered.
- [ ] S5 Freeze. `scripts/freeze_tests.py`, then `tests/**` and `verification/**` out of scope.
- [ ] S6 Build. L1 to L5 merged in the integration order above, each command green.
- [ ] S7 Gate. Full `scripts/run_verify.py` plus `check_gate_bite`.
- [ ] S8 Review. Two independent reviewers, mechanical and domain.
- [ ] S9 Audit. Packet with the corpus counts, the producer sweep, and one hand-recomputable
      number.
- [ ] S10 Closeout. Backlog entries settled to `done` or restated, ExecPlan filed, phase
      completed, tag, idle.
- [ ] S11 Advance. Policy says `auto_advance: true` for phase 13.

## Verification

Command IDs this phase adds: `pytest_table_state`, `generate_table_state_report`.
Report it commits: `reports/active/latest_table_state_report.txt`.
Gate: `uv run python scripts/run_verify.py`, which derives the full set from every active or
completed contract, plus `scripts/check_gate_bite.py`.
Every canary must bite, and at least one must prove the pot reconciliation fails the gate when
it is removed.

## Outcome

Not yet complete. Stage 1 finished: the contract carries real criteria, Phase 03 and Phase 06
are amended, and Phase 11's amendment is filed as its own task because its contract is at the
line cap.

What the two stage-1 reviewers changed, since it is more than editing. The corpus turns out to
be one flat structure in all 499 hands, with no ante and no straddle and no unequal stack, so
every table-shape number the first draft promised was structurally zero; the contract now names
constructed fixtures as the discovery surface and the corpus as a zero-delta regression proof.
The straddle detection the first draft specified could not see the straddle it required, and
the criterion now carries all three signals including the minimum-raise-target disagreement.
Refusing on any shallower seat would have refused on folded seats, which is wrong poker, so the
flat-table test is scoped to live seats. The pot reconciliation is a tautology at both live
producers and the contract now says where it actually bites.

## Next Agent Bootstrap

Work only in `~/projects/poker-bot-worktrees/phase-13` on `phase/13-table-state-fidelity`.
Never work in `~/projects/poker-bot` or the main worktree.

Ask the driver and do only what it names:

    uv run python scripts/loop_stage.py --phase 13 [--advance]

Current state: stage 1 complete, `task_mode: contract-update`, `base_commit`
`41ec07a3bcc918312e4c1600a3b842cf9f944a82`, phase 13 `active` in `phase_status.yml`. Next is
stage 2, the decision list at
`reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`, which needs its own
`scope_change_log` entry before it is written.

Read first: this plan, the contract, the five `phase: "13"` entries in `backlog.yml`, and the
Phase 12 audit packet's limitations section, which hands this phase two findings by name.

Two things to keep in view. The spot key is out of scope on purpose: phase 14 re-keys anyway
and re-keying re-seeds every mixed cell (`RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`), so paying that
cost twice buys one result. And the frozen tests of completed phases must be migrated at stage
4, not discovered at stage 6, which is the mistake phases 11 and 12 both made.
