# MAINT-34 decisions

Every judgment call this task made, with its reversibility class. `frozen-into-data` means the
answer is committed under `data/artifacts/preflop/**` and a later task cannot revise it without
re-solving.

## 1. The multiplier is per seat, not global or a menu. `frozen-into-data`

Ruled by the coordinator before any solve, because "change one config field" has three readings and
two of them are traps. `raise_mults` is the re-raise TO-amount as a multiple of the current bet,
applied at **every** re-raise level and varied only by seat, never by depth
(`~/projects/GTOpen/crates/solver/src/preflop/mod.rs:54-55`, `mults_of` at `:97-102`).

- **Global `[5.4]`. Rejected.** The three-bet becomes 13.5 and the next rung 72.9, and `mod.rs:2219`
  clamps any raise at or above `allin_threshold * stack` to the stack. At 0.67 and 100bb that is a
  jam, so the sized four-bet stops existing everywhere and all three-bet-facing committed spots
  become fold, call or shove. Verified at the source.
- **Global menu `[3.0, 5.4]`. Rejected.** Phase 14 measured a second global multiplier at 38,828
  action nodes and 112 MB becoming 260,136 and 754 MB; extrapolated here that is roughly 94% of the
  20 MiB artifact cap, which is a halt rather than a budget.
- **`raise_mults_by_seat`, 5.4 on the two blind seats. Ruled.** Blind three-bets 13.5, in-position
  three-bets 7.5, and the button's four-bet survives sized at 40.5.

**The field goes into `RULED_CONFIG` itself, not posted beside it.** `config_errors` iterates
`RULED_CONFIG.items()` and never inspects a posted field the ruling does not name, so a config
supplied on the side is invisible to the card check, the frozen config guards and the whole gate.
Verified live: the export the route D probe produced is **refused by the loader** on this field,
which is the guard doing its job.

## 2. Zero-reach spots are excluded, not admitted. `frozen-into-data`

The re-solve produced selected nodes with no arriving hand class, because under a 13.5bb blind
three-bet the button's cold-call behind two cold-callers goes to zero. A node no hand can be at is
not a decision the bot faces, so the selection rule excludes it and the census counts it under its
own code, `derivation:no-arriving-hand-class`. `schema.py` is not relaxed to admit an empty spot.

This is deliberately **not** the case `test_chart_arrival_probability.py:424-442` rules on. That is
about zero *arrival* - a spot a hand can reach but almost never does - and requires such a spot to
keep its cells, which remains true. Zero *reach* is a different thing and nothing had produced one
before.

The clause is placed **last** in the exclusion order. Thousands of nodes deep in the four-bet family
also have no arriving class, and filed earlier this clause would swallow the depth bucket, which is
the bucket a later phase reads to find the work it is taking up. Verified: zero of the 160 would
have been exposure-refused had the clause run first, and all 160 carry exactly zero arrival, so
coverage does not move.

## 3. The iteration cap rises; the accuracy target does not. `runtime-reversible`

The first re-solve stopped at `SOLVE_ITERATION_CAP` (2,000) with an achieved gap of 0.00033389
against a declared target of 0.00016 - 2.1x the target, where the old solve converged at 1,900.

Raising the cap is **not** the move phase 10 forbids at `:147-149`. What that forbids is widening an
accuracy *target* after seeing the numbers, which buys a pass by lowering the bar. Raising an
iteration cap spends more compute to clear a bar that has not moved. The target stays at 0.00016.

Converged, route C reaches 0.00015588 at iteration **3,800**. The cap is set to **5,000** rather than
3,900 because the gap is not monotone near the target - 0.000162 at 3,615, 0.000164 at 3,720,
0.000156 at 3,800 - and a cap set at the crossing is fitted to one run's noise.

Recorded because nothing would have caught it: **no gate command compares the card's achieved gap to
the target the same card declares.** `test_solver_export.py:183` makes that comparison against a
captured fixture of a superseded solve rather than against the card.
`A-SOLVE-THAT-MISSES-ITS-DECLARED-TARGET-SHIPS-WITH-NOTHING-OBJECTING`.

## 4. The blind-versus-blind jam is accepted and filed. `frozen-into-data`

**Ruled by Taylor, 2026-09-16, on the measurement below.**

When a blind four-bets over the other blind's 13.5 it gets the 5.4 multiplier again - 72.9bb - which
clamps to a jam. So **49 of 254 three-bet-facing committed spots offer no sized four-bet**, split
SB 34 / BB 15, carrying **1.4364% of committed arrival**.

This is structural for a single multiplier: a 13.5 three-bet needs `m = 5.4` and a sized four-bet
needs `13.5m < 67`, so `m < 4.96`. Both cannot hold.

**The coordinator's own ExecPlan asserted the opposite** - that the four-bet "survives as a sized
raise at 40.5, under the 67 clamp, verified" - without qualification. That verification covered the
button four-betting over a blind and was generalised to a case it did not cover. The solve lane
caught it. The plan is corrected rather than quietly left.

**Route D, a two-size blind menu `[3.0, 5.4]`, was measured rather than argued about, and loses.**

| | route C | route D |
| --- | --- | --- |
| jam-only three-bet-facing committed spots | 49 | **0** |
| exported nodes | 30,609 | 62,107 |
| `data/artifacts` total | 6.46 MB, 30.8% of cap | 9.30 MB, 44.3% of cap |
| iterations to the 0.00016 target | **3,800, reached** | **20,000, not reached** (0.00018780) |
| big blind's three-betting on the 7.5 size | n/a | **0.00%** |

It fixes the jam completely and buys nothing else. The solver, handed both sizes, **declines the
small one entirely** - 0.00 combos at the headline spot, verified by the coordinator against the
probe export, and a mean of 0.04 points against 8.25 across all fifteen committed blind three-bet
spots. The second size is not poker here; it is a way to get 40.5 onto the four-bet menu underneath
the clamp, and it costs twice the tree, twice the bytes, five times the iterations, and a chart that
misses the accuracy this repo declares. Shipping an unconverged solve is the defect decision 3 just
removed.

Two qualifications recorded because they cut the other way. The route D solve is unconverged and an
unconverged CFR run concentrates rather than mixes, so a converged one might spread more onto 7.5;
nobody knows what cap that would take. And `realization: calibrated` prices a flop from 169
per-class numbers with no size-dependent term, so the model has limited machinery for preferring one
three-bet size over another - the 0.5% may describe the realization model rather than the poker.

**Raising `allin_threshold` was named as a third lever and is rejected on measurement.** Letting the
72.9bb four-bet through leaves the caller an SPR of **0.19**, so it is a jam wearing a sized-raise
label, and it would pass every check in the repo while hiding the problem an honest jam displays.
It also changes the clamp for every seat at every depth, which phase 14's decision 14 tuned
deliberately.

Filed as `A-BLIND-CANNOT-FOUR-BET-A-BLIND-WITHOUT-JAMMING-AND-THE-MULTIPLIER-GEOMETRY-SAYS-WHY`.
