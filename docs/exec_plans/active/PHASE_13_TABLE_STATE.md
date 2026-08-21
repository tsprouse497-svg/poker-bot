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

## Coordinator rulings during the build

These are integration decisions too small for the decision list and too load-bearing to leave to
whichever worker reaches them first. They are recorded here rather than in the decision list
because the task is in implementation mode and that list is settled.

**2026-08-21, the per-seat record's container and class names.** Raised by the frozen-test
migration worker, who noticed decisions 1, 2, 5 and 14 fix the record's own fields
(`street_bet`, `committed_total`, `folded`, `all_in`) and name neither the container on
`StrategyQuery` nor the class. Ruled: `seat_states: tuple[SeatState, ...]`, one entry per seat
in `stacks`, sorted ascending by seat.

Rejected `contributions` and `SeatContribution`, which is the better read of the contract's own
noun, because the record carries `folded` and `all_in` and those are not contributions. A field
named for less than it carries is the exact defect this phase exists to end, and repeating it in
the fix would be worse than the original. Rejected a bare `seats` container because it reads as
the seat numbers, and the query already keys `stacks`, `seat` and `button_seat` by seat integer.
`SeatState` is deliberately a near-twin of the engine's `PlayerState` minus name, hole cards and
stack, which is decision 2's one-vocabulary argument carried to the container; the name differs
because the query is seat-oriented where the engine is player-oriented.

All three stage 4 workers were given the ruling at once so none had to coordinate with the
others.

**2026-08-21, where an ante sits, correcting decision 3.** Raised by the same worker, which
found decision 3 ("preflop, each seat's street contribution must equal its hand contribution")
and decision 10 ("the ante probe gives every seat an ante inside its hand contribution") cannot
both hold. Ruled on the poker rather than on the rule count: an ante is dead money, it goes into
the pot, and it does not count toward what a seat owes, so putting it in the street figure would
make an anted seat owe less to call than an unanted one at the same level. The ante lives in
`committed_total` only. The rule is therefore not equality but `committed_total >= street_bet`
on every street, with the difference being that seat's dead money; the only impossible direction
is a seat holding more this street than over the whole hand.

This improves the phase rather than patching it. Preflop, `committed_total - street_bet` is
forced dead money by arithmetic the query already carries, on a live seat and a folded one
alike, and it can never be absorbed the way a straddle can. So decision 8's ante signal becomes
that difference: uniform across seats is an ante, non-uniform is a dead blind and takes the kept
residual code. The strategy-side worker reached the same uniformity reading independently.

**This makes a clause in the phase 13 contract false.** Line 75 says the two figures "coincide"
preflop. Contract edits are forbidden in implementation mode, and the phase 13 contract is at
exactly 300 lines so it cannot take an added amendment either. The fix is a reword inside the
existing line budget, folded into the `contract-update` task this phase already owes for
`ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP`, which must run before the phase tags.

**2026-08-21, how `seat_states` serializes.** The two workers defaulted differently. Ruled: a
seat-keyed mapping, `{"0": {...}}`, with the inner object carrying `street_bet`,
`committed_total`, `folded` and `all_in` and not repeating the seat. It mirrors `stacks`, the
field it is validated seat-for-seat against, and a test pins that the two key sets are
identical. A list of objects would store the seat twice, which is where drift starts.

**2026-08-21, a requirement carried to the stage 6 builder.** The rewritten `StrategyQuery`
class docstring must contain the phrase "current bet level" and must name both `current_bet` and
the per-seat `street_bet`. A migrated frozen test in `tests/test_engine_fidelity.py` asserts it,
and the point of the rename is that one name now has one meaning.

**2026-08-21, lane L1 died mid-task.** The worker authoring `tests/test_table_state.py` was
terminated by an API error while applying the naming ruling. The file it had written was
complete and parsed, so the coordinator finished the rename and then owned that file for the
ante correction above. Recorded because the Delegation Plan says L1 is a worker lane and it was
not, for the last edits.

## What stage 4 specified for the stage 6 builder

The tests are the specification, and so are the five canaries in `verification/mutations.yml`.
Each canary's `find` string must occur exactly once in the built code or `check_gate_bite` fails
at stage 7, so these identifiers are not suggestions:

- `contributed_total`, the sum the pot is validated against, in `strategy/contract.py`, used as
  `if self.pot != contributed_total:`
- `hero_stack` and `aggressive` in the capped-hero guard, used as
  `if self.to_call == hero_stack and aggressive:`
- `hero_start = stacks[query.seat] + hero.street_bet` in `_table_depth_bb`
- `if state.folded:` as the live-seat filter in the flat-table test
- `predicted_min_raise` in the straddle detector, used as
  `if query.min_raise_target != predicted_min_raise:`

The builder must also keep the phrase "current bet level" in the `StrategyQuery` class docstring
and name both `current_bet` and the per-seat `street_bet` there, because a migrated frozen test
in `tests/test_engine_fidelity.py` asserts it.

**`generate_table_state_report.py` must validate its own figures and exit non-zero when they do
not hold.** Two canaries name it in `must_fail`, and `check_gate_bite` requires every command it
names to fail with the mutation applied, so a report that merely prints whatever it is handed
would leave both surviving. Phase 12 set the pattern with `_validate_census`, which fails the
gate when the census splits do not reconcile. Here the two figures that must be self-checked are
hero's derived depth, which has to agree with hero's own recorded contribution rather than with
the bet level minus the price, and the straddle census, which has to reconcile against the
minimum-raise prediction the detector used. This is the stage 4 reviewer's sixth blocker and it
is a real requirement rather than a bookkeeping fix: a report nobody can break is a report
nobody has tested.

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
