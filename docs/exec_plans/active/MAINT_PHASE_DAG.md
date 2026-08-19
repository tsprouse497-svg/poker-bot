# MAINT-21 - Adopt The V2 Phase Graph

## Objective

Make `depends_on` say what the roadmap argues, so `scripts/loop_fleet.py` can plan more than one phase at a time.

The v2 contracts were declared with `depends_on` as a straight chain `10 -> 11 -> 12 -> 13 -> 14 -> 15 -> 16`.
That was sequence rather than semantics: nothing read the field, so nothing tested it.
The fleet driver now plans from it, and under the chain the fleet is a fleet of one.

`docs/V2_ROADMAP.md` already argues a looser graph phase by phase, and Taylor ruled on 2026-08-18 to adopt it.

## Scope

Approved: the seven v2 phase contracts and `docs/ROADMAP.md`.
Forbidden: any implementation. This task changes declared dependencies and the document that states them, and nothing else.
No acceptance criterion is written and no phase is activated; both belong to each phase's own stage 1.

## Delegation Plan

- No-delegation exception: this session is instructed not to spawn subagents, and the change is three frontmatter edits plus one document section, which is below the threshold where a lane would help. Self-review notes are in the Outcome.

## Slices

- [x] `depends_on` in the seven contracts. Only 11, 13 and 14 actually move; 10, 12, 15 and 16 were already right.
- [x] `docs/ROADMAP.md` carries the graph, the two edges that make it a graph, and the reason each holds.

## Verification

- `check_contracts`, `check_repo_consistency` (which now rejects a dangling edge or a cycle), `check_scope`, `pytest_loop_fleet`
- `scripts/run_verify.py` full gate
- `uv run python scripts/loop_fleet.py --plan` names 11 as startable alongside in-flight phase 10

## Outcome

Three edges changed: 11 moved from 10 to 09, 13 from 12 to 11, and 14 from 13 to the join of 10, 12 and 13.
The other four were already correct, which is worth recording because it means the chain was never uniformly wrong, only wrong where it mattered.

Width is now 3. The fleet's first real use is lane 11 alongside phase 10.

### Self-review

No independent subagent review; this session cannot spawn one, so the pass below is self-review.

The graph is checked against `docs/V2_ROADMAP.md` rather than against convenience, and each edge traces to a stated argument: 10 to lines 58-61, 11 to 120-121, 12 to 135, 13 to 146-147, 14 to 153 and 167.
The one edge worth arguing about is 12 depending on 11.
The roadmap's own proof for 12 is re-deriving the committed GTO Wizard export through `convert_preflop_export.py --check` and losing the catch-all row from the refusal inventory, and the second half of that replays the corpus through the engine.
So 12 needs 11's engine fixes to prove itself, not merely to be correct, and the edge stands.

What this does not do: 12 and 13 both touch preflop query and artifact code, and running them in parallel means their merges can conflict even though their dependencies are satisfied.
That is a merge cost rather than a correctness one, and the serial integration step in `docs/LOOP.md` is where it lands.

## Next Agent Bootstrap

Branch `maint/phase-dag`, cut from `main` at `3284976`, worked in `~/projects/poker-bot-worktrees/maint-loop-fleet`.
Phase 10 is running untouched in the primary worktree at loop stage 5.
Next command: `uv run python scripts/loop_fleet.py --plan`.
