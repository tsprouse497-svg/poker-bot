# MAINT-25 - Phase 16 Coverage Ruling, And Two Numbers I Got Wrong

## Objective

Record Taylor's rulings on phase 16 judgment calls 1 and 3, take the phase off the pause board, and correct two figures I asserted as facts and wrote into four documents.

## Scope

Approved: the phase 16 decision record, `verification/loop_policy.yml`, `docs/V2_ROADMAP.md`, `docs/ROADMAP.md`.
Standing: `backlog.yml` and the generated `docs/BACKLOG.md`.
Forbidden: every phase contract, and any implementation. No solve is run and no artifact is written. Phase 16 stays `future`.

## Delegation Plan

- No-delegation exception: this session is instructed not to spawn subagents. Recording a ruling and correcting figures is coordinator work with nothing to hand to a lane.

## Slices

- [x] Judgment call 1: flop only, with the accepted cost named.
- [x] Judgment call 3: every canonical flop against a small head of common preflop lines, with the verified reasons growing it later is cheap.
- [x] `needs_human_data` flips to false; `auto_advance` stays false.
- [x] The fan-out counts corrected to 49 and 48, and the affordability claim demoted to an assumption everywhere it appeared.

## Verification

- `check_scope`, `check_generated_backlog`, `check_file_sizes`, `pytest_quality_hardening`
- `scripts/run_verify.py` full gate
- `review_queue.py --list` reports nothing waiting

## Outcome

Phase 16's rulings are made and it leaves the pause board. It still cannot auto-advance, because it commits the solution the bot plays postflop.

The ruling that matters is which axis gets pruned. Preflop lines have a real long tail; canonical flops do not, since the 1,755 classes come up at broadly comparable rates. So the phase prunes lines hard and keeps every flop, which is the shape that needs no board abstraction at all. GTOpen's 47/95/184 subsets turn out to be irrelevant here: they are study sets, and as a lookup table a 47-flop subset covers 2.7% of flops.

Judgment call 4 stays open on purpose. The exploitability target and whether a solve is reproducible are inherited from phase 10's measurements, not ruled here, so stage 3 halts if phase 10 never produced them. That is the human gate doing its job rather than an oversight, and the loop-policy reason says so.

### Two corrections

The fan-out was stated as 47 turns and about 2,160 rivers. That is hero's view, counting cards he cannot see because he holds two of them. A spot in the artifact is keyed by the board, so it is 49 turns and 48 rivers: per preflop line, 1,755 flops, 85,995 turns, 4,127,760 rivers.

"All 1,755 flops is affordable" was stated as established. It is per preflop line, and no solve in this repo has ever been timed to a real exploitability target - only a 300-iteration preflop smoke test, with solve time and determinism both still on phase 10's unverified list. Every conclusion has been rewritten to rest on the ratio instead, which holds whatever a flop costs: the turn is about 49 times a flop, the river about 2,350 times.

### Self-review

No independent subagent review; this session cannot spawn one.

This is the third correction in one session to something I asserted rather than checked, after claiming GTOpen was preflop-only and claiming nothing validates the backlog's phase field. The common shape is stating an absence or a bound as established when it was an inference. The mitigation applied here is structural rather than a resolution to try harder: the decision record now carries a section that separates the counts from what is known about them, so a later reader meets the assumption at the same time as the number.

The claim in this task most worth attacking is that canonical flops come up at broadly comparable rates. That is why pruning the flop axis is rejected, and it is an argument about multiplicity across suit-isomorphic classes rather than a measured distribution. If it is wrong, and some textures are genuinely far more frequent, then a weighted subset becomes defensible and decision 1 should be reopened. Recorded here rather than left implicit, because it is the load-bearing premise under both rulings.

## Next Agent Bootstrap

Branch `maint/postflop-coverage-ruling` off `main` at `f62d603`, worked in `~/projects/poker-bot-worktrees/main`.
Phase 10 runs untouched in the primary worktree at loop stage 5; phase 11 is startable.
Next command: `uv run python scripts/loop_fleet.py --plan`.
