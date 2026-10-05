# MAINT-44: Store The Turn, Solve Only The River

- **Task** `MAINT-44`
- **Mode** `contract-update`
- **Branch** `maint/44-store-the-turn`, worktree `~/projects/poker-bot-worktrees/maint-44`
- **Base** `0f46d46`, which is `main` after MAINT-43
- **Authorised by** Taylor, 2026-10-04 in phase 21's session and confirmed 2026-10-05 in this one

## Objective

MAINT-42 and MAINT-43 put on `main` that the turn and river are both solved at the table, and
declared phase 22 to build it. Taylor then re-ruled: the turn is stored like the flop and only the
river is solved at the table. Phase 21's lane already carries the stored turn and will not merge
until `main` agrees. This task corrects `main`. Moving a boundary and re-scoping a declared phase are
semantic contract changes, so this runs in `contract-update`.

## Taylor's rulings

1. **Store the flop and the turn; solve only the river live.** His words in phase 21's session: "keep
   saving turn and solve only river line in real time ... idea is to store flop and turn and then
   dynamically solve the river." Asked in this session whether `main` should change to match, he
   answered yes.

## Coordinator's assignment, not a ruling

Phase 21's contract says the stored turn is "played by a later phase". Phase 22 already owned making
the bot answer a turn, so it keeps that job, now from stored strategy, and is renamed Turn And River
Play. This is `runtime-reversible`: a later `contract-update` can move turn play elsewhere, and the
packet reports it so Taylor can.

## Scope

Approved: `AGENTS.md`, phase 22's contract under its old and new names, phase 20's contract, both
roadmaps, `docs/GTOPEN_SOLVER_NOTES.md`, `verification/loop_policy.yml`, and this task's packet and
review directory. Phase 21's contract is left to phase 21's lane. Nothing under `data/`, `src/`,
`tests/` or `scripts/` changes.

## Delegation Plan

- No-delegation exception: the edits transcribe one ruling into documents that must agree with each
  other and with phase 21's unmerged contract, and a lane would be writing down what the coordinator
  told it.
- Review handoff: one read-only reviewer that wrote none of this checks that every live document on
  `main` now says the turn is stored and only the river is live; that nothing contradicts phase 21's
  branch (`82422cb` on `phase/21-the-flop-campaign`); that phase 22's re-scope is faithful and its
  turn-play assignment is reported as an assignment; and that the corrected backlog entries are
  right. Asked also what it held back. No gate runs: the machine is shared.

## Slices

- [x] Activate MAINT-44 with a dated scope entry.
- [x] Correct the boundary in `AGENTS.md`.
- [x] Re-scope and rename phase 22; update `phase_status.yml` and the loop-policy reason.
- [x] Correct phase 20, both roadmaps and the GTOpen notes.
- [x] Correct the three backlog entries that assumed a live turn.
- [ ] Independent read-only review, findings fixed or filed.
- [ ] Gate, packet, closeout to idle, gate again, merge, push, and tell phase 21's lane.

## Verification

`uv run python scripts/run_verify.py`, sequenced with the other lanes on this machine, read for its
verdict rather than its exit code.

## Outcome

Pending review and gate.

## Next Agent Bootstrap

Work in `~/projects/poker-bot-worktrees/maint-44`. Edits are done; review and gate are open. Ask the
other lanes before running the gate.
