# Phase 21 stage 6: the river is not stored, tests review

Read-only review by a subagent that wrote none of the change, 2026-10-04, of 7af4337: the frozen
tests re-opened for Taylor's re-ruling that the flop and turn are stored and the river never is.

## Blocker
None.

## Non-blocker
- Refusal cases counted before and after: none dropped or loosened. The manifest's 14 inconsistent-manifest cases stay 14, two river cases becoming exact turn cases (6,418 and 6,288); the line cases stay 4; both fetch-short tests became one-turn-card-short with their exact codes; new tests refuse a closed board carrying any river count and a manifest and index that both carry one. Every replacement figure re-derived (6,419 - 131, 6,566 - 134, 134 x 49).
- The removed report test is subsumed by a stricter one: each river figure must print with "not stored" on its own row.
- The new expectations match the contract's closure and storage criteria.
- Past the contract: the report tests still require the unreachable figures printed, which the contract no longer names; harmless. `test_a_fetch_that_asks_for_the_river_is_refused` accepts any `ValueError`, looser than the other fetch refusals' pinned codes. A refused board carrying a river key, and `require_fetched` for the river, are untested. Response: carried into the stage 6 build, where the fetch is written; the test file is at its cap, so a further test needs a split first.
- One river obligation is left in code: `--export-strategies` in `scripts/solve_postflop_sample.py` keeps the whole export, about 6 GB a board and almost all river, and its docstring and failure message say "turn and river". Response: filed as `THE-BULK-STRATEGY-EXPORT-KEEPS-THE-RIVER-THE-RULING-SAYS-NOTHING-KEEPS`, for the build lane at stage 6.
- Mutation descriptions: the dealt-turn canary still bites; its clause about a later phase sizing against the figure is a guess. The closure-count canary's river clause holds only if stage 6 refuses the river inside the disabled equality check. Response: carried to the stage 6 build, which writes those checks.

## Alignment
- `TWO-FLOP-CAMPAIGN-TEST-FILES-SIT-AT-THE-700-LINE-TEST-CAP`: filed from the reviewer's proposal.
- `THE-BULK-STRATEGY-EXPORT-KEEPS-THE-RIVER-THE-RULING-SAYS-NOTHING-KEEPS`: filed from the reviewer's proposal.

## What the reviewer did not look at
The contract commits beyond the closure criterion, the storage-class re-ruling, decision 18's patch,
and the solver notes on turn and river roots. Held back: nothing.
