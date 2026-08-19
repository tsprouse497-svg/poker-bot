# MAINT-24 - Record The Board Abstraction Ruling

## Objective

Write down Taylor's ruling on phase 16 judgment call 2 so the next session does not re-ask it.

Ruled 2026-08-19: take the default, keep the fail-closed boundary, and defer board abstraction rather than reject it.
Grouping similar flops so the bot plays them identically will eventually be needed.

## Scope

Approved: the phase 16 decision record and `docs/ROADMAP.md`.
Standing: `backlog.yml` and the generated `docs/BACKLOG.md`.
Forbidden: every phase contract, the loop policy, and any implementation. Phase 16 stays `future` and `needs_human_data`, because judgment call 1 is still open.

## Delegation Plan

- No-delegation exception: this session is instructed not to spawn subagents. Recording a ruling is coordinator work by nature; there is nothing to hand to a lane.

## Slices

- [x] Judgment call 2 carries the ruling, its reason, and the consequence Taylor did not ask about.
- [x] `POSTFLOP-BOARD-ABSTRACTION` filed as deferred beyond v2, stating why it is a boundary amendment rather than an optimisation.
- [x] `docs/ROADMAP.md` deferred list points at it.

## Verification

- `check_scope`, `check_generated_backlog`, `check_file_sizes`
- `scripts/run_verify.py` full gate

## Outcome

The ruling is recorded with the thing it settles indirectly: abstraction buys depth, not breadth.
All 1,755 canonical flops is affordable, so a flop-only solution needs no abstraction at all; 1,755 flops times their turns and rivers is roughly 3.8 million spots and needs it to exist.
So deferring abstraction defers the turn with it, and `POSTFLOP-BOARD-ABSTRACTION` is the item that unblocks depth later.

Judgment call 1, how deep the committed solution goes, is left formally open even though this ruling points hard at flop-only.
Answering it on Taylor's behalf would be a session writing its own frozen-into-data decision, which is the one thing the human gate exists to stop.

### Self-review

No independent subagent review; this session cannot spawn one.

The temptation here was to mark judgment call 1 answered by implication, since deferring abstraction makes flop-only the only affordable depth.
That is a session inferring a frozen-into-data answer from a nearby ruling, which is exactly how a decision list stops being a record of what a human decided.
Left open, and the connection stated in the note so the inference is visible rather than acted on.

One claim in an earlier draft of this note was wrong, and the gate caught it, which is a better outcome than if it had passed.
The draft filed the item under `phase: beyond-v2` and argued that nothing validates that field against a vocabulary.
`quality_checks.NON_PHASE_LABELS` validates it exactly. `backlog integrity` went red and took four gate commands with it.
The item is now `charts`, which is what `STACK-DEPTH-BUCKETS` already uses and is the closest precedent: the other heuristic abstraction over the artifact's key space, also deferred beyond v2.

Worth recording because it is the second time in this session that I asserted an absence of validation or capability instead of checking for one. The gate caught this one; Taylor caught the other.

## Next Agent Bootstrap

Branch `maint/board-abstraction-deferred` off `main` at `f7dc21f`, worked in `~/projects/poker-bot-worktrees/main`.
Phase 10 runs untouched in the primary worktree at loop stage 5; phase 11 is startable.
Next command: `uv run python scripts/loop_fleet.py --plan`.
