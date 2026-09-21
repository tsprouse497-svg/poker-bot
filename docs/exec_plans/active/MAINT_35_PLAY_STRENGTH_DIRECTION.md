# MAINT-35: Re-aim the repo from a training bot to a bot that plays

## Objective

Taylor ruled on 2026-09-21 that the goal of this repo is a bot that plays strong NLHE, and that the
training product is backlogged until the bot is strong. This task makes that the repo's stated
purpose, retires the training phase from the graph, declares the phases the new goal needs, and
records the teaching-motivated strategy acceptances as work to reopen.

It changes no strategy, no artifact and no runtime behaviour. Every acceptance it names stays
accepted; this task files them, it does not reverse them.

## Taylor's rulings, 2026-09-21

Taken from the session transcript, recorded here because nothing else in the repo carries them yet.

1. **North star.** A bot that plays really good poker. The training product comes after, to help a
   user, and is backlogged until the bot plays well. Some recent decisions refused spots the solve
   takes because they would not make sense for a trainee; that reasoning is retired.
2. **Venue.** The bot will eventually play live, in **Taylor's own home games**. Not public
   real-money tables. This reverses part of the 2026-08-15 ruling that kept table automation out of
   v2 on terms-of-service and account risk, and it reverses it only for private home games.
3. **The big blind's tight defence.** Reopen it **after** phase 16 has flop cells, so the decision is
   made against a measured number rather than against an argument.
4. **The drill.** Backlog it and close the lane.
5. **Refusals.** Fail-closed stays for now. Heuristics, and the merge of solved charts with unsolved
   spots, become **their own later phase** rather than a change made here.
6. **Rename.** Documents only. The `poker_training_bot` package keeps its name.

## Scope

Approved: `AGENTS.md`, `README.md`, `docs/ROADMAP.md`, `docs/V2_ROADMAP.md`, `docs/ARCHITECTURE.md`,
`docs/phase_contracts/**`, `verification/loop_policy.yml`.

Standing: `CURRENT_TASK.yml`, `backlog.yml`, `phase_status.yml`, `STATUS.md`,
`docs/PHASE_LEDGER.md`, `docs/BACKLOG.md`, `docs/exec_plans/**`, `reports/active/**`.

Forbidden: everything else. In particular this task touches no file under `src/`, `tests/`,
`scripts/`, `data/` or `verification/mutations.yml`. No committed artifact is re-derived and no
completed phase's data moves.

## The phase graph after this task

Retired: **15, The Drill**. It is a bare skeleton with no implementation, nothing depends on it, and
its own dependency edge into phase 16 was already cut on 2026-09-06.

Declared:

| Phase | Title | Depends on | Why the new goal needs it |
|-------|-------|------------|---------------------------|
| 18 | The Yardstick | 14 | Nothing in this repo measures how well the bot plays. Its own report says so: "Producing the other kind of number needs an opponent with a strategy, and this repo does not have one yet." |
| 19 | Heuristics And Merged Charts | 16, 18 | Ruling 5. Fill the refusal gaps by merging solved cells with heuristics, every substitution carried on the decision. Needs 18 so the merge can be shown to help rather than asserted to. |
| 20 | The Home Game | 16, 19 | Ruling 2. A bot that sits down in Taylor's own home games. Last, because a bot that folds every flop should not sit anywhere. |

Unchanged: 16 (Postflop That Can Bet) and 17 (The Corpus Verdict), both already in flight.

## Delegation Plan

Complete before implementation. Three worker lanes, no shared files, integrated by the coordinator.

- **Lane A - identity and boundaries.** Owns `AGENTS.md`, `README.md` and `docs/ARCHITECTURE.md`.
  `phase_status.yml` belongs to lane C in full, including its `project:` field, so that no two lanes
  write the same file. Output: the purpose restated as playing strength, the
  boundary table rewritten so each boundary says what it is and when it lifts, and the two rulings
  above that move a boundary written in. Status: planned.
- **Lane B - the roadmaps.** Owns `docs/ROADMAP.md` and `docs/V2_ROADMAP.md`. Output: both rewritten
  around playing strength, every stale figure re-derived from the committed artifact rather than
  copied, and the new phase table above. `docs/V2_ROADMAP.md` still describes a repo of ten
  completed phases with no contracts declared, which has been false since phase 10 landed.
  Status: planned.
- **Lane C - the graph and the backlog.** Owns `phase_status.yml` (phase entries),
  `verification/loop_policy.yml`, `docs/phase_contracts/**`, and `backlog.yml`. Output: phase 15
  retired, phases 18, 19 and 20 declared as contract skeletons with `depends_on` and policy entries,
  and the backlog entries listed below. Status: planned.
- **Integration order.** A, then C, then B, because B's phase table has to match what C declared.
  The coordinator regenerates `STATUS.md`, `docs/PHASE_LEDGER.md` and `docs/BACKLOG.md` after C.
- **Review handoff.** An independent read-only reviewer, not any lane that wrote what it reads, must
  check: that no figure written in this task was copied from prose rather than re-derived; that no
  acceptance was silently reversed; that the boundary table says the same thing as `AGENTS.md`'s
  prose; and that the retirement of phase 15 leaves no dangling `depends_on`, policy entry or
  gate command.

## Backlog entries this task files

Each records a teaching-motivated acceptance to reopen under the new goal. None is reversed here.

- The big blind's tight defence, reopened after phase 16 has flop cells. Ruling 3.
- The pair-ladder and kicker-ladder inversions, accepted twice on the grounds that the cost is
  "pedagogical, not monetary". The repo names a roughly 200-second experiment that would say
  whether they are a solver pruning artefact costing real money instead, and it has never been run.
- The multiway exposure threshold, moved from 1 to 10 percent because "a squeeze is a spot a student
  meets constantly", and measured on a quantity that is circular: multiway flops look rare because
  the model under-flats.
- Coverage is published reach-weighted under the solve's own play. Against real hands it is lower,
  and the 128 spots dropped as zero-arrival were dropped on the same flattering measure.
- The drill, deferred as post-strength work. Ruling 4.

## Slices

- [ ] Slice 1: activate the task and write this plan. Evidence: this file, `CURRENT_TASK.yml`.
- [ ] Slice 2: Lane A. Evidence: changed-file summary and the new boundary table.
- [ ] Slice 3: Lane C. Evidence: `check_repo_consistency` and `check_contracts` green on the new graph.
- [ ] Slice 4: Lane B. Evidence: every figure in both roadmaps traced to a re-derivation, not to prose.
- [ ] Slice 5: regenerate the generated documents. Evidence: clean diff on a second run.
- [ ] Slice 6: independent read-only review. Evidence: review notes under the audit path.
- [ ] Slice 7: full gate. Evidence: `reports/active/latest_verify.txt`.

## Verification

`uv run python scripts/run_verify.py`. No new command IDs; this task adds no behaviour to test.
The checks that can actually fail on it are `check_scope`, `check_contracts`,
`check_repo_consistency`, `check_file_sizes`, `check_execplan_delegation` and the fact-drift check.

## Outcome

Pending.

## Next Agent Bootstrap

The lane is `/Users/taylorsprouse/projects/poker-bot-worktrees/maint-35` on
`maint/35-play-strength-direction`, branched from `main` at `1d89158`. `task_mode` is
`contract-update`, so contract edits are allowed and must not mix with implementation.

Open, and not to be invented:

- Whether the phase-15 branch and worktree are deleted or kept. The branch holds a decision list and
  an ExecPlan for the retired drill. Ask Taylor before deleting either.
- Phase 14 is still at loop stage 11 waiting on Taylor's sign-off, and phase 17 is waiting on six
  rulings from him. Neither is this task's to answer.
