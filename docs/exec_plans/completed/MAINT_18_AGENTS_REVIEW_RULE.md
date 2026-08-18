# MAINT-18: State The Per-Stage Review Rule In AGENTS.md

## Objective

MAINT-17 made the driver refuse to advance while a stage owes a review, and left `AGENTS.md` silent about it.
That file says it is the single source for behavior rules and wins over every other document, so a rule that lives only in `scripts/loop_stage.py` and `docs/LOOP.md` is one a reader is entitled to miss.

The edit is semantic rather than mechanical, which is why it is its own `contract-update` rather than part of the implementation task.

## Scope

Approved: `AGENTS.md`.

Forbidden: everything else. No driver change, no test change, no phase declared.

## Delegation Plan

- No-delegation exception: two sentences into the rules file, stating a rule that already exists in code and is already tested. There is no implementation lane and nothing for a worker to build.

## Slices

- [x] Slice 1: the rule itself in the `Autonomous Loop` section - what owes a review, why the single post-gate review is not enough, and what the driver supplies.
- [x] Slice 2: the three finding classes, and that an alignment item is filed in `backlog.yml` rather than left in the note.
- [x] Slice 3: coordinator step 9, which named only the pre-gate review.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

Three slices, four lines of `AGENTS.md`, gate green.

The `Autonomous Loop` section now states the rule where the file states its other loop rules: a stage that changed anything a human wrote owes read-only review notes before `--advance` will move, because a single review after the gate arrives once the tests are frozen and the code is written.
It says the driver decides which stages owe one from their own diff, so a reader does not go looking for a list of stages that does not exist.
It names the three finding classes, and it says an alignment item is filed in `backlog.yml` rather than left in the note, which is the part most likely to be skipped since nothing mechanical enforces it.

Coordinator step 9 named only the pre-gate review and now covers both, which matters because that step is what a session reads when it is coordinating rather than driving the loop.

`AGENTS.md` is 114 lines against its 150-line cap.

## Next Agent Bootstrap

The repo is idle with phases 00 through 09 complete and nothing declared after them.

The loop now reviews per stage, and `AGENTS.md`, `docs/LOOP.md`, and the driver all say so.
Adopting `docs/V2_ROADMAP.md` is the next task: seven `phase_status.yml` entries at `future`, seven contract skeletons, seven loop-policy entries, a rewritten `docs/ROADMAP.md`, and a re-tagged `backlog.yml`.
That is maintenance, since those contract edits are structural.

The one semantic change still owed before any v2 phase starts is the `AGENTS.md` ingestion boundary, which ruling 5 lifts for one player's own hands and which needs a size bound expressed as a number.
