# ExecPlan: Phase 15 - The Drill

Lane: `phase/15-the-drill`, worktree `~/projects/poker-bot-worktrees/phase-15`.
Contract: `docs/phase_contracts/PHASE_15_DRILL.md`. Pointer: `verification/loop_runs/15.yml`.
Policy: `auto_advance: false` - this phase commits session records and makes product judgements,
so it stops at stage 11 for Taylor whatever the gate says.

## Objective

Close the phase 15 gate: the repo's first interactive entry point. It deals a preflop spot from the
committed chart, takes a human's action, says what the chart says, says what the gap is in the only
unit the committed data supports, records the session as a hand history, and turns a run of sessions
into a leak report broken out by spot family and by action.

This is the phase that makes phases 10 through 14 worth having. Everything before it produced ranges
nobody has used.

## Scope

Approved, by stage. Widening mid-task needs a dated `scope_change_log` entry in `CURRENT_TASK.yml`.

- Stage 1 (contract-update, current): `docs/phase_contracts/PHASE_15_DRILL.md`,
  `reports/phase_audits/reviews/PHASE_15_DRILL/**`.
- Stage 2: adds `reports/phase_audits/decisions/PHASE_15_DRILL_DECISIONS.md`.
- Stage 4: adds `tests/**`, `verification/mutations.yml`.
- Stage 5: removes `tests/**` and `verification/**` - the freeze, enforced by `check_scope.py`.
- Stage 6: adds `src/poker_training_bot/drill/**`, `scripts/drill.py`,
  `scripts/generate_drill_session_report.py`, `scripts/run_verify.py` (the `COMMANDS` entries only),
  `src/poker_training_bot/hand_history/**` (the writer), `src/poker_training_bot/data_pipeline/**`
  (the per-player narrowing), `src/poker_training_bot/simulator/**` (hand ids and bb/100),
  `src/poker_training_bot/solver_artifacts/lookup.py` (the refusal reason), and the committed fixture
  session under `data/samples/`. **No `pyproject.toml` change**: the repo has no `[project.scripts]`
  table and adding one would be a second way to run things.
- Stage 9: adds `reports/phase_audits/PHASE_15_DRILL.md`.

Standing scope carries `CURRENT_TASK.yml`, `phase_status.yml`, `backlog.yml`, `verification/loop_runs/**`,
`docs/exec_plans/**`, `reports/active/**`, and the generated docs.

Forbidden, and these are existence rules: `data/raw/**`, `data/processed/**`.

Out of scope by ruling, not by omission:
- **The bounded personal-history ingestion lift.** `docs/V2_ROADMAP.md` puts it here, and it cannot
  land here. `AGENTS.md` V1 Boundaries still reads "No large hand-history ingestion", the roadmap
  itself says "the file wins" until a `contract-update` changes that wording, and the lift is owed a
  size bound stated as a number that only Taylor can give. Two blockers, one of them a human input.
  The drill produces its own sessions, so the leak report has real input without it. Carried as a
  decision with a stated default of *defer*, for Taylor at the stage 3 gate.
- Any UI. `docs/V2_ROADMAP.md` defers the UI package explicitly and says to revisit once the drill
  exists. A terminal program is not a UI surface.
- Postflop. The drill deals preflop decisions only, because that is what the committed chart answers.

## Delegation Plan

Complete before implementation begins. Reviewers are never the agent that wrote the work
(`AGENTS.md`, Subagents). All build lanes are read/write on their own files only and return a patch
plus the commands they ran; none of them runs `run_verify.py` or `check_gate_bite.py`, which plant
mutations in the shared tree.

- Worker lanes: **A - sampling and dealing** (the stated sampling policy over the 249 spots, seeded
  dealing, reusing `simulator/table.py` and `run.py`'s pure-function-of-seed shape); **B - scoring**
  (a student's action against a `weights_for` cell, the refusal path, the captured-against-available
  score); **C - the session record and its writer** (the new record type plus the first
  `NormalizedHandHistory` writer in the repo, round-tripping `parse_hand_history`'s exact-key check),
  and the thin interactive shell over B's pure core; **D - the leak report**
  (`generate_drill_session_report.py`, broken out by action and family before any pooled figure, plus
  the per-player narrowing in `data_pipeline/comparison.py` that keeps `population` required);
  **E - the inherited fixes** (run-scoped hand ids and bb/100 in the simulator, and carrying the
  converter's `derivation:*` reason through `solver_artifacts/lookup.py`); **F - the backlog sweep**
  (every entry reading `phase: "15"` plus the drill asks filed against other phases).
- Ownership: A owns `src/poker_training_bot/drill/sample.py` and `drill/deal.py`. B owns
  `drill/score.py`. C owns `drill/session.py`, `hand_history/write.py`, and `scripts/drill.py`. D owns
  `scripts/generate_drill_session_report.py`, `drill/report.py`, and `data_pipeline/comparison.py`.
  E owns `simulator/run.py`, `simulator/measure.py`, `solver_artifacts/lookup.py`, and - this was
  missing until the stage-1 review found it - `solver_artifacts/chart_selection.py` plus whatever
  reads the export, because the four `derivation:*` codes are produced there and not in `lookup.py`,
  so nothing else could have carried a refusal reason to the table. F owns `backlog.yml` only. The
  coordinator owns `scripts/run_verify.py`'s `COMMANDS` entries, the `drill/` package skeleton and its
  `__init__`, the committed fixture session, integration, and every stage's advance.
- Expected outputs: from each lane, a patch confined to its owned files, the exact commands it ran
  with their output, and a changed-file summary. From A and B additionally a worked example computed
  against the committed artifact rather than described.
- Status: A planned, B planned, C planned, D planned, E planned, F planned. Nothing assigned before
  stage 5 freezes the tests.
- Integration order: E first, at stage 6 rather than stage 4 - the contract's stage-4 migration
  clause is dormant because no committed test or report asserts a `sim-` id today, so there is nothing
  to migrate before the freeze; run-scoped hand ids and the split refusal codes change strings
  every later lane records; then B, because the scoring unit decides what a session record stores;
  then A and C in parallel on disjoint files; D last, because a report over numbers that are still
  moving proves nothing. F runs throughout and touches no code.
- Review handoff: two independent read-only reviewers at stage 8, neither having written any lane -
  one mechanical (does the code do what the contract says) and one on the poker (is what it teaches
  correct, and does the score mean what a trainee will read it as). A third adversarial verifier
  reverts each stage-6 and stage-8 fix in place and records which gate command notices; phase 13
  proved that role finds what the other two miss. Every stage whose diff touched hand-written work
  owes its own read-only note under `reports/phase_audits/reviews/PHASE_15_DRILL/` before `--advance`
  will move.

## Pauses

- Paused: a size bound for a personal hand-history import, stated as a number, which only Taylor can
  give. It is not this phase's to answer and does not block it - decision 9 cuts the ingestion lift
  out of phase 15 - but it is the input the lift has been owed since 2026-08-15, five maintenance
  tasks have recorded it as owed, and nobody has ever proposed a figure. It is raised here rather than
  as a decision because deferring writes nothing and neither reversibility class describes a scope cut
  (`DEFERRAL-HAS-NO-REVERSIBILITY-CLASS`). The bound needs to say whether it governs hands ingested,
  bytes committed, or both; the only anchor in the repo is the committed corpus at 499 hands and about
  1.1 KB of committed text per hand.

## Slices

- [x] Stage 0 - lane opened, worktree claimed, clean tree, `phase/15-the-drill` cut from `9bbdcf4`.
- [ ] Stage 1 - contract carries real criteria; this plan is active. Evidence: `loop_stage.py --phase 15`
      reports no outstanding stage-1 item.
- [ ] Stage 2 - decision list, every judgement declaring `frozen-into-data` or `runtime-reversible`.
- [ ] Stage 3 - human gate. Taylor answers the frozen-into-data items; the reversible ones proceed on
      their recorded defaults and are reported afterwards.
- [ ] Stage 4 - tests authored first and red, with a mutation canary for each new command ID authored
      in the same stage. Evidence: `pytest_drill` fails on an assertion or on a missing module, and
      `verification/mutations.yml` carries a canary per new command.
- [ ] Stage 5 - freeze. Evidence: `check_test_freeze` green, `tests/**` out of `approved_scope`.
- [ ] Stage 6 - build, delegated across lanes A to E. Evidence: every command the contract declares green.
- [ ] Stage 7 - gate. Evidence: full `run_verify.py` green **and** `check_gate_bite` proving the new
      canaries bite.
- [ ] Stage 8 - two independent reviews plus the adversarial verifier.
- [ ] Stage 9 - audit packet with a number a human can recompute by hand.
- [ ] Stage 10 - closeout to idle, plan filed, tag.
- [ ] Stage 11 - halt for Taylor. Policy says this phase never advances unattended.

## Verification

Command IDs (declared in the contract frontmatter, registered in `COMMANDS` in `scripts/run_verify.py`):
`pytest_drill`, `generate_drill_session_report`.

Reports: `reports/active/latest_drill_session_report.txt`, plus the standing
`reports/active/latest_verify.txt`.

Every figure the contract names as an obligation is re-derived by the generator, which exits non-zero
when one does not hold. No count is hand-typed (`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`).

## Outcome

Fill in before completing the gate.

## Next Agent Bootstrap

You are the coordinator of the phase 15 lane. Read, in order: `AGENTS.md`, this plan,
`docs/phase_contracts/PHASE_15_DRILL.md`, then run

    cd ~/projects/poker-bot-worktrees/phase-15
    uv run python scripts/loop_stage.py --phase 15

and do the one stage it names. Do not run any gate command in the primary checkout
`~/projects/poker-bot`; two sessions planting mutations in one tree is what corrupted it on
2026-09-06. Brief every review subagent "read-only, no gate runs" - `check_gate_bite` is not
read-only in effect, it edits `src/**` in place.

The open human ask, for the stage 3 gate: whether the bounded personal-history ingestion lift stays
deferred out of this phase (the recorded default) or blocks it. It needs both an `AGENTS.md` wording
change and a size bound as a number.
