# MAINT-40: Declare Phase 21, The Flop Campaign

- **Task** `MAINT-40`
- **Mode** `contract-update`
- **Branch** `maint/40-declare-the-flop-campaign`, worktree `~/projects/poker-bot-worktrees/maint-40`
- **Base** `bb1f5fff8ca3e10d7e4c9579fb30f08bfb47f389`, which is `main`
- **Authorised by** Taylor, 2026-09-26, in session

## Objective

Taylor ruled on 2026-09-26 to trust the solve and buy more of it rather than measure the bot first.
Phase 16 built the flop machinery and closed on a sample; nothing declared owns solving the rest.
This task declares phase 21, The Flop Campaign, as a skeleton in the shape MAINT-35 used for 18, 19
and 20, so the loop can start it. Declaring a phase and adding a `depends_on` edge are semantic
contract changes, so this runs in `contract-update`.

## Taylor's rulings, 2026-09-26

1. **Direction.** Trust the solve and get more of it, instead of measuring the bot first. Phase 21
   has three parts in order: use every core, pick the cloud machine, run the campaign. The machine
   is picked on cost per solved flop with the memory a solve needs as a hard limit, and nothing is
   re-solved or hand-edited to look better.
2. **Numbering.** 21. Numbers 15 and 17 are retired and not reused.
3. **Phase 19 waits on 21.** Asked in plain words, with the cost stated (19 starts later) and the
   recommendation first; he chose yes. 19's contract gains the edge and one sentence saying why.

## Scope

Approved: the new phase 21 contract, phase 19's contract (the edge and its sentence), both roadmaps,
`verification/loop_policy.yml`, and this task's packet and review directory. Standing scope covers
`CURRENT_TASK.yml`, `phase_status.yml`, `backlog.yml`, the generated documents and this plan.
Nothing under `data/`, `src/`, `tests/` or `scripts/` changes.

## Delegation Plan

- No-delegation exception: the edits are coordinator-owned because each one transcribes a ruling
  made in this conversation into files that must agree with each other - a contract skeleton, a
  status entry, a policy entry, one edge, two roadmap paragraphs and a dozen backlog re-labels - and a
  lane would be writing down what the coordinator told it. The figures in them were computed by the
  coordinator from committed data, and the review below re-derives them independently.
- Review handoff: one read-only reviewer that wrote none of this checks that phase 21 is declared
  consistently everywhere the repo records a phase; that 19's new edge is stated the same way in its
  contract and both roadmaps and that the graph drawing matches the contracts; that every figure
  written (five decision points, four boards, 44 and 40 of 22,100 flops, the 20,000-hand result) is
  true of the tree; that each adopted backlog entry is one the campaign actually owns and none that
  should have been adopted was missed; and that the skeleton neither anticipates a boundary lift nor
  pre-rules anything stage 2 must ask Taylor. Asked also what it held back.

## Slices

- [x] Activate MAINT-40 in `CURRENT_TASK.yml` with a dated scope entry.
- [x] Phase 21 skeleton contract, `phase_status.yml` entry at `future`, loop-policy entry with
  `auto_advance: false`.
- [x] Phase 19 `depends_on` gains 21, on Taylor's ruling.
- [x] Both roadmaps say where 21 sits and why; both now say what phase 16 shipped, which closes
  `THE-ROADMAPS-STILL-SAY-THE-BOT-DOES-NOT-PLAY`.
- [x] Backlog entries adopted by phase 21: twelve after the review, each with the condition that
  closes it.
- [x] Independent read-only review: one blocker, eight non-blockers, one alignment item. All fixed,
  and the alignment item filed as `PHASE-19-IS-TOLD-THREE-WAYS-WHETHER-IT-FILLS-FLOP-GAPS`.
- [x] Gate, packet, closeout to idle, gate again, merge, push.

## Verification

`uv run python scripts/run_verify.py`, read for its verdict rather than its exit code, and
`uv run python scripts/check_scope.py`. Then `scripts/loop_fleet.py --plan` from `main` lists 21 as
eligible, since 16 is `completed` there.

## Outcome

Phase 21 declared at `future`, phase 19 waits on it, twelve entries adopted, review resolved in
three rounds, gate green 50 of 50.

## Next Agent Bootstrap

Closed. Phase 21 starts from the `main` tree with
`uv run python scripts/loop_fleet.py --start-lane 21`, and stage 1 replaces the skeleton.
