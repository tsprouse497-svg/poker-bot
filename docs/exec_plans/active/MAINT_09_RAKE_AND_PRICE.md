# MAINT-09: Say What The Chart Was Solved For

## Objective

An independent reviewer, told nothing about MAINT-07 or MAINT-08, read Phase 08 again and found that its headline finding is largely a rediscovery of a documented, deliberately accepted property of the artifact it measures.

The committed chart is a raked NL25 solve. This corpus is rake-free.
A raked solution defends the blinds more tightly than a rake-free one, and Phase 05's own strategy report already says so: *"Raked ranges are tighter than rake-free ones, most visibly in the blinds, so the big blind folds more here than a rake-free chart would have it fold."*
The word "rake" appears nowhere in Phase 08's contract, report, audit packet, review notes, or backlog entry.
So the blind-defence gap that MAINT-08 made the headline was attributed to this repo's own over-folding bias when most of it is the artifact behaving as designed.

The same chart solves a 2.5 big blind open.
These players opened to a median 2.25, and only 18.1% of the decisions facing a single raise faced one at or above 2.5.
A cheaper price is a correct reason to continue with more hands, and the sample shows exactly that shape.

Five smaller findings came with them, listed under Slices.

## Scope

Approved:

- `src/poker_training_bot/data_pipeline/comparison.py`
- `tests/test_sample_comparison.py`
- `verification/mutations.yml`, `verification/freeze.lock`
- The three Phase 08 audit documents, and the MAINT-08 plan carrying the pooled figure

Forbidden here:

- The chart, the sizing table, the sample, and the Phase 08 contract.
  The finding is that the phase never said what it was measuring against, not that it measured the wrong thing.

## Delegation Plan

- No-delegation exception: implementation is coordinator-owned. Review was not, and that is the point of this task: the findings it closes came from an independent reviewer with no knowledge of the previous two tasks, which is the first time this repo has had one.

## Slices

- [x] Slice 1: the report states, before any number, that the ranges were solved with rake and these hands carry none, reading the source name from the artifact rather than restating it.
- [x] Slice 2: every decision records the price it faced, banded around the solve's own opening size, and only where the decision faces exactly one raise.
      Evidence: a per-band call agreement table per population, and a test that the effect is monotone and large.
- [x] Slice 3: the sampled-action match rate judgment call 5 ruled would be reported alongside, and never was, is built and reported as the lesser number it is.
- [x] Slice 4: "70 of the 104 human call disagreements" is corrected to 58 of 89 in all four documents carrying it.
      It was a pooled figure under a humans label - the violation MAINT-08 removed from the code, reinstated in the sentence announcing the removal.
- [x] Slice 5: prose in the report, the packet, the backlog, and the MAINT-08 plan that read a disagreement with a human as a verdict on the chart is rewritten.
      The contract's forbidden shortcuts name that exact move, and the gate cannot see prose.
- [x] Slice 6: the decision record's 3,056 decision points is corrected to 3,048, and `CORPUS-INEXPRESSIBLE-SPOTS` carries its diagnosis - all 19 are second-orbit sequences the Phase 04 schema documents as out of scope for v1.
- [x] Slice 7: two canaries, for the price band and for the sampled-action rate, and the tests re-frozen.

## Verification

- `uv run python scripts/run_verify.py` (full derived gate)
- `check_gate_bite` at 27 mutations

## Outcome

Full gate green.
27 mutations applied and all 27 caught, up from 25.
53 tests in `pytest_sample_comparison`, up from 49.

The finding that survives is narrower and more useful than the one it replaces: the committed chart answers a raked table at 2.5x opens, this corpus is a rake-free table at 2.25x, and until now nothing in the repo said so.
Human calls agree 52.5% facing 2.25 or less, 69.0% between 2.26 and 2.50, and 77.8% above 2.50, and 47 of the 58 big-blind call disagreements faced an open smaller than the size the chart was solved for.

## Next Agent Bootstrap

The repo is at `task_mode: idle` with Phase 08 completed and Phase 09 still `future`.
Two findings from the earlier review remain deliberately undone and unfiled: the report lists only the first 20 of 164 disagreements with no committed file holding the rest, and `convert.py` builds `showdown_seats` from the corpus's show records and then discards it, so a normalized hand's `showdown` means "did not fold" rather than "showed".
The independent reviewer also could not verify the committed corpus text against upstream - no network, and no committed check can establish it. That is the one assumption everything downstream rests on and it is unnamed in the packet's limitations.
