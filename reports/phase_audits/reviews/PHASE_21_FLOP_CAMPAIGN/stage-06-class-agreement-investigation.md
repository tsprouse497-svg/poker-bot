# Phase 21 stage 6: why suit variants of one hand get different strategies

Investigation of `THE-SOLVE-DRIFTS-BY-SUIT-INSIDE-A-CLASS-AND-THE-DRIFT-GROWS-WITH-ITERATIONS`, the
cause behind `THE-CLASS-AGREEMENT-RULE-REFUSES-TEN-OF-THE-FOUR-BOARDS-FIFTY-SIX-FLOP-DECISION-POINTS`.
Run 2026-10-10 on Taylor's direct approval that day to read the local GTOpen clone's source and
experiment with it. Everything ran in scratch copies of `~/projects/gtopen-poker-bot` at `c48f437`
with their git remote removed; the committed clone, its build and the solve objects in
`~/poker-bot-solve-objects/postflop-clone-b058335` were only read. Apple M4, five solver threads, f32
arenas unless a row says otherwise. No gate, mutation check or test under `tests/**` was run or
touched. One footprint to declare: `cargo clippy` was run once in the committed clone to count its
existing warnings, which writes check metadata under its untracked `target/`; no source, commit or
release binary there changed.

## Cause

`Solver::chance_node` in `crates/solver/src/cfr.rs` (lines 641-663 at `c48f437`) adds each hand's
value over the dealt cards in card order, in f32. Two suit variants of one hand, say `AdKd` and
`AhKh` on `9c8c7c`, receive the same set of numbers, but in a different order, so their sums can
differ in the last bit or two. Nothing makes them equal again. Each iteration's regret update
(`update_node`) adds that tiny difference, it carries into the next iteration's strategy, and hands
near indifference between two actions turn it into visibly different frequencies. With suit
isomorphism on (the default, and how every campaign solve runs), the representative card of each
orbit is always the lowest one, so the drift lines up with GTOpen's suit order (diamonds, hearts,
spades), which is the pattern the stage 6 review found.

So the defect is f32 rounding at the chance node, amplified by CFR, and oriented by the isomorphism.
It is not unconverged solving and not anything in our harvest.

## Evidence

A scratch harness (a Rust binary linked against the clone's solver crate, not kept) builds a spot,
runs CFR to checkpoints, and reads the average strategy straight out of solver memory. For every
action node above the first chance node it groups hands by the spot's own suit group
(`spot.hand_perm`) and reports the worst gap between members of a group, the count of groups over
the 5e-4 rule and over 1e-5, and how many three-member groups with a gap over 1e-5 are ordered by
suit on their most-moving action. Exploitability comes from GTOpen's own best response.

**1. Our harvest and export reading are not the cause.** Ruled out first, two ways.
- An independent reader written from `export.rs`'s format, grouping combos by the export's own hand
  strings, gives the same refused points as the harvest: 9c8c7c worst 0.001408 (five points over
  5e-4), Ac8c3c worst 0.001440 (four points).
- The harness re-solved 9c8c7c from scratch with the lane's config (menu from
  `data/artifacts/postflop/solve_config.json`, ranges floored at 0.01, 346 and 447 hands, the same
  counts the export header carries) and read solver memory at 300 iterations, the export's own
  iteration count. All 14 flop decision points' worst gaps match the export to four figures (root
  1.381e-4, after a check 2.840e-4, ... the widest, IP after OOP's 33 bet, 1.408e-3), five points
  are over 5e-4 as in the harvest, and 497 of 502 three-member groups are suit-ordered, the stage 6
  review's figure exactly. So the gaps are in the solve itself.

**2. It needs a chance node.** River-root solves have no chance node. On `9c8c7c2c3h` (suit group of
two) and `9c8c7c2c3c` (group of six) the worst in-class gap is exactly 0 at every checkpoint to 1,600
iterations. Showdown and fold values, regret matching and strategy averaging are therefore already
exactly symmetric; they are not the source. A turn root, which has one chance node, shows it at
once:

| Turn root, 800 iterations | Worst gap | Groups over 5e-4 | Suit-ordered | Exploitability |
|---|---|---|---|---|
| `9c8c7c2c`, as shipped | 1.507e-2 | 47 | 479 of 481 | 0.0423% |
| `9c8c7c2c`, isomorphism off | 7.445e-2 | 233 | 273 of 730 | 0.0395% |
| `9c8c7c2c`, chance sum in f64 | 0 | 0 | none to order | 0.0378% |
| `9c8c7c2c`, proposed fix | 0 | 0 | none to order | 0.0370% |

**3. The isomorphism is not applied unevenly; it only orients the drift.** Turning it off makes the
drift larger (worst 0.161 at 100 to 400 iterations), and the ordering falls to 273 of 730, about the
one in three chance gives. With exactly symmetric values (the f64 row) the isomorphism's synthesis of
non-representative branches stays exactly symmetric, gap 0 with it on or off.

**4. Rounding in the card sum is the seed.** Summing the same f32 values, with the same weights and
the same card order, into an f64 accumulator before one rounding makes the gap exactly 0. Nothing
else changed, so the card or turn weighting (`divisor`, the same 1/44 or 1/45 for every card) is not
the cause; the order-dependent f32 sum is.

**5. Reduced-precision storage is not the cause here.** These four boards were solved with f32
arenas (`arena_storage: f32`), and the drift is present in f32. The 16-bit store drifts more (turn,
800 iterations: worst 3.750e-2) and the proposed fix removes that too (0 at 200 and 800).

**6. Tie-breaking in best response or normalisation is not the cause.** Best response never feeds
the strategy, and the strategy is normalised hand by hand with no cross-hand tie-break; the exact 0
on river roots covers both.

**How it behaves with more iterations.** It does not settle, but "grows" is only partly right:

| Flop root `9c8c7c` | 80 | 150 | 160 | 300 | 320 | 600 | 640 | 1,280 |
|---|---|---|---|---|---|---|---|---|
| Full menu, worst gap | | 1.346e-3 | | 1.408e-3 | | 2.012e-3 | | |
| Full menu, groups over 5e-4 | | 6 | | 10 | | 27 | | |
| One bet size a street, worst gap | 1.149e-3 | | 1.055e-3 | | 1.523e-3 | | 4.011e-3 | 5.279e-4 |

On the reduced menu the worst gap rose 2.6 times from 320 to 640 iterations and then fell at 1,280,
while 97 percent of the drifting groups stayed suit-ordered at every checkpoint (320 of 330 at
1,280). Phase 16's 320-to-640 rise is the same effect. The proposed fix gives 0 at every one of these
checkpoints.

## Proposed fix

`reports/phase_audits/reviews/PHASE_21_FLOP_CAMPAIGN/stage-06-suit-orbit-projection.diff`, sha256
`55c69469e66db35ff3ca23d5378e09bc6cb9729d6ded3f1d52134fc37d6131a1`, applies cleanly to `c48f437`
(`git apply --check`). Not applied to the committed clone; that is Taylor's call.

What it does: after `chance_node` returns inside the CFR traversal, every hand takes the value of the
lowest-index hand in its orbit under the suit permutations that fix the board and the cards dealt so
far. Those hands are the same hand, so in exact arithmetic this changes nothing; in f32 it makes them
bitwise equal, and by induction every strategy above stays bitwise symmetric. The orbit tables are
built once when the solver is created. Best response is left alone, so exploitability still measures
the strategy honestly, and the copy is skipped when node locks are set, since a lock can make suit
variants genuinely different. The diff also adds a GTOpen test, `suit_variants_get_identical_strategies`,
which fails on `c48f437` (suit variants 0.20725185 against 0.20725127 at the turn root) and passes
with the fix. Summing the cards in f64 also gave 0 in every run, but only the copy guarantees it.

Measured effect, before and after, same configs:

| Spot | Iterations | Worst gap before | After | Exploitability before | After |
|---|---|---|---|---|---|
| Flop `9c8c7c`, full menu | 300 | 1.408e-3 (10 groups over 5e-4) | 0 | 0.2892% | 0.2897% |
| Flop `9c8c7c`, one size a street | 640 | 4.011e-3 | 0 | 0.0514% | 0.0513% |
| Flop `9c8c7c`, one size a street | 1,280 | 5.279e-4 | 0 | 0.0186% | 0.0185% |
| Turn `9c8c7c2c` | 800 | 1.507e-2 | 0 | 0.0423% | 0.0370% |
| Turn `Ac8c3c2c` | 800 | 1.238e-3 | 0 | 0.0373% | 0.0259% |
| Turn `8c8d3c2c` (group of two) | 800 | 1.532e-3 | 0 | 0.0190% | 0.0191% |

Exploitability is the same or better everywhere. Cost: interleaved runs put it inside this fanless
Mac's heat drift, which adds 1 to 1.5 seconds to whichever run goes second; turn root 800 iterations
4.4 to 4.8 s before against 4.6 to 4.8 s after, reduced flop 80 iterations 28.2, 30.4, 32.6 s before
against 26.7, 29.2, 31.7 s after with the fix run first. GTOpen's whole suite passes with the fix:
`cargo test --release --workspace`, 106 pass (105 before, per `docs/GTOPEN_SOLVER_NOTES.md`, plus the new test) and the
upstream preflop benchmark stays ignored. Clippy reports 24 warnings in the solver crate with or
without the diff.

Not covered: the GPU engine. `up_chance` in `crates/solver/src/gpu/kernels.cu` sums cards in the same
order and folds orbits the same way, so a GPU solve will drift the same way. Before any GPU campaign
solve the kernel needs the same rule (each thread sums for its orbit's lowest-index hand and writes
that to its own slot). That cannot be compiled or run on this Mac and is not in the diff.

Not measured: Ac8c3c and 8c8d3c at full menu on the flop. Their flop drift is the same mechanism on
the evidence of their turn roots, but only 9c8c7c's flop was re-solved here.

## What re-solving the four boards would take

1. Taylor approves applying the diff to `~/projects/gtopen-poker-bot` as a commit on
   `poker-bot/check-through-clears-initiative`; then a release build and the GTOpen suite (106 pass).
   `docs/GTOPEN_SOLVER_NOTES.md` gains a fourth commit row.
2. Re-solve phase 16's four boards on the new commit exactly as decision 17's slice did: run A with
   `--all --threads 10 --export-strategies` (about 45 minutes and 24 GB of exports at ten threads)
   and run B in a scratch copy, then the determinism records, in a window Taylor grants under
   `caffeinate`. Every strategy value moves slightly, so phase 16's five committed spots get new
   digests, `determinism.json` is rewritten, and a board's iteration count may shift by one check
   interval (9c8c7c at 300: 0.2897% against 0.2892%, both under the 0.3% target).
3. Index and byte budget rebuilt, then the harvest. In-class agreement is then exact by
   construction, so the class rule should refuse nothing; that is expected, not yet run through
   `harvest_postflop_closure.py`.
4. The stored turn rows benefit too: they sit under the turn card, where the fix keeps the remaining
   suit swaps exact (turn-root runs above).

The contract forbids re-solving to make numbers look better; this re-solve's reason would be a
solver defect with a measured fix, which is Taylor's ruling to make (frozen into data).

## Independent check

Pending: a read-only subagent that wrote none of this checks the conclusion against the evidence.
