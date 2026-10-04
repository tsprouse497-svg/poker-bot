# MAINT-43: Declare Phase 22, Live Turn And River

- **Task** `MAINT-43`
- **Mode** `contract-update`
- **Branch** `maint/43-declare-live-turn-and-river`, worktree `~/projects/poker-bot-worktrees/maint-43`
- **Base** `b41621bfecdfbee97475bcf3030cad62af37fc5d`, which is `main`
- **Authorised by** Taylor, 2026-10-04, in session

## Objective

MAINT-42 lifted the runtime-solver boundary for the turn and river, and nothing owns building it.
Taylor ruled the same day that it gets its own phase. This task declares phase 22, Live Turn And
River, as a skeleton in the shape MAINT-40 used for 21, so the loop can start it. Declaring a phase
and adding `depends_on` edges are semantic contract changes, so this runs in `contract-update`.

## Taylor's rulings, 2026-10-04

1. **A phase owns it.** Asked in plain words whether to put the work on the schedule; yes.
2. **It waits for the flop campaign.** Phase 22 depends on 21.
3. **The engine is GTOpen.** "I don't want to build our own GTO solver." He had been told the same
   day that GTOpen carries no licence.
4. **Phase 20 waits on 22.** Asked with the cost stated and the recommendation first; he chose yes.

## Scope

Approved: the new phase 22 contract, phase 20's contract (the edge, and the three sentences that
said every decision comes from the committed strategy or that it adds no runtime solver calls),
`AGENTS.md` (the boundary names its owner), both roadmaps, `verification/loop_policy.yml`, and this
task's packet and review directory. Standing scope covers `CURRENT_TASK.yml`, `phase_status.yml`,
`backlog.yml`, the generated documents and this plan. Nothing under `data/`, `src/`, `tests/` or
`scripts/` changes.

## Delegation Plan

- No-delegation exception: the edits transcribe rulings made in this conversation into files that
  must agree with each other - a contract skeleton, a status entry, a policy entry, two edges, one
  boundary sentence, two roadmaps and one backlog adoption - and a lane would be writing down what
  the coordinator told it.
- Review handoff: one read-only reviewer that wrote none of this checks that phase 22 is declared
  consistently everywhere the repo records a phase; that both new edges agree across contracts,
  roadmaps and the graph drawing; that the skeleton states the four rulings and pre-rules nothing
  stage 2 must ask Taylor, in particular how the gate is tested; that phase 20's edits remove every
  contradiction with live solving and nothing more; and that the adoption is right. Asked also what
  it held back.

## Slices

- [x] Activate MAINT-43 with a dated scope entry.
- [x] Phase 22 skeleton contract, `phase_status.yml` entry at `future`, loop-policy entry with
  `auto_advance: false`.
- [x] Phase 20 gains the edge to 22 and stops saying every decision comes from the committed strategy.
- [x] `AGENTS.md` and both roadmaps name phase 22 as the owner; the graph gains 22.
- [x] `LIVE-TURN-AND-RIVER-SOLVING` adopted by 22.
- [ ] Independent read-only review, findings fixed or filed.
- [ ] Gate, packet, closeout to idle, gate again, merge, push. The gate waits until phase 21's
  all-core solve on this laptop has finished; two at once have crashed the machine.

## Verification

`uv run python scripts/run_verify.py`, read for its verdict rather than its exit code, and
`uv run python scripts/check_scope.py`. Then `scripts/loop_fleet.py --plan` from `main` shows 22 as
not yet eligible, since 21 is not `completed`.

## Outcome

Pending review and gate.

## Next Agent Bootstrap

Work in `~/projects/poker-bot-worktrees/maint-43`. Edits are done; the review and gate are open.
Before running the gate, confirm with the phase 21 lane that its laptop solve has finished.
