# GTOpen: Verified Capabilities And Extraction Path

What was established by cloning, building and running GTOpen: the preflop surface on 2026-08-13, and the postflop engine on 2026-08-23 and 2026-08-24.

**Everything down to "Not verified" was executed, apart from the lines in "Postflop, as run" that are marked as README-sourced. Everything in "Not verified" was not.**

The postflop section sits high rather than at the end on purpose. Its absence is what let a later reader infer from an all-preflop note that the tool is preflop-only, and a reader who stops early should meet the correction rather than miss it. Which is also why that section still separates what was run from what was only read: a blanket claim of execution over it would recreate the same error in the other direction.

## Installed state

| | |
|---|---|
| Location | `~/projects/gtopen`, a sibling of this repo, deliberately outside it |
| Commit | `4aee435bdeb155b25f0c8140e707a8342ce4356f`, dated 23 July 2026 |
| Licence | None. No LICENSE file, and no mention in `README.md` or `Cargo.toml` |
| Toolchain | Rust 1.97.1 |
| Build | `cargo build --release`, 36.6 seconds |
| Binary | `target/release/gto-server`, Mach-O **arm64**, native rather than under Rosetta |
| Serves | `127.0.0.1:3737`, a JSON API and a web UI |
| GPU | `/api/status` reports `"gpu": false` on this machine, so the CPU engine is what runs |

## Postflop, as run

Recorded because the absence of this section led a later reader to conclude GTOpen is preflop-only.

**Driven end to end.** Four routes, on flop boards only: `POST /api/spot` builds the tree and returns node counts and the arena size, `POST /api/solve` runs CFR in the background against an exploitability target, `GET /api/status` carries the iteration counter and the exploitability history, and `POST /api/node` reads a node back. The next section is what they cost. Postflop CFR is the tool's primary function and the Preflop Lab is the bolt-on beside it.

**Read from the README and the route table, never executed.** Same class as "Not verified" below, and listed here only so the surface is known:

- The rest of the route surface: `/api/runouts`, `/api/reports/*`, `/api/lock`, `/api/exploit`.
- Turn and river roots. The route accepts a board of 3, 4 or 5 cards; only 3 was posted.
- `REPORTS`, which batch-solves one spot across a weighted canonical flop subset of 47, 95, 184, or all 1,755 flops.
- `SEND TO POSTFLOP`, said to carry both conditional ranges, the pot and the stacks out of a Preflop Lab line into a postflop setup, which would be the only coupling between the two engines.
- Node locking and a best-response mode, which the README claims are covered by tests.

A setup takes both ranges on a 13x13 grid, a board, pot, stacks, rake, and per-street bet, raise and donk sizes. Solves target an exploitability percentage of pot, with 0.3% given as study-quality; that target was used and reached.

Suit isomorphism is exploited internally and described as exact. No rank abstraction is claimed.
The README's 1.4x and 2.2x are branch counts at the first chance node, not speedups. Measured below, the saving is larger.

**The saving has a precondition, and it is all-or-nothing.** A suit permutation is admitted only if it fixes every board card and maps every combo in each range to an equal-weight combo in the same range. One suit-specific entry anywhere in either range - an `AhKh:0.25`, a per-combo import, a suit-specific node lock - collapses the group to the identity and the entire saving goes to zero on every board that is not rainbow. Every measurement below used class-uniform range strings, so the whole cost model assumes this holds. See `ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS` in `backlog.yml`.

One config trap, because this document records the preflop body above with `"allin_threshold": 0.67`.
The postflop `/api/spot` route reads that field as a **percent of pot**, not the preflop fraction. Posting 0.67 there asks for a 0.67% threshold, which replaces every configured bet with a jam. The measurements below post 85.0.

## Config surface, as accepted

This exact body was posted to `/api/preflop/spot` and built successfully.
Position names `LJ` and `HJ` are taken as given, so no vocabulary translation is needed.

```json
{
  "positions": ["LJ","HJ","CO","BTN","SB","BB"],
  "stack": 100.0,
  "posts": [0,0,0,0,0.5,1.0],
  "ante": 0.0,
  "limp": false,
  "open_raises": [2.5],
  "raise_mults": [3.0],
  "max_raises": 4,
  "add_allin": true,
  "allin_threshold": 0.67,
  "rake_pct": 5.0,
  "rake_cap": 3.0,
  "no_flop_no_drop": true
}
```

It returned `{"nodes": 83123, "action_nodes": 38828, "arena_mb": 112.4}`.

Rake and opening size are parameters rather than properties of a fixed solution: `rake_pct` and `rake_cap` set the rake basis, `open_raises` sets the first-raise amounts, and `max_raises` decides how deep the raise tree goes, with the open counting as the first.

## Extraction path

Four calls, all exercised end to end. Drivable from Python; no Rust needed to extract.

1. `POST /api/preflop/spot` with the config above. Builds the tree and returns node counts.
2. `POST /api/preflop/solve` with `{"iterations": N, "check_every": N, "target_gap": bb}`. Returns `{"ok": true}` and runs in the background.
3. `GET /api/preflop/status` until `state` leaves `"running"`. Carries `iteration`.
4. `POST /api/preflop/node` with `{"path": [...]}`, empty for the root. Returns the node view below; walk the tree by extending `path`.

Preflop solve time and determinism were open questions here until phase 10 settled them, and both are recorded on the committed source card `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json` rather than restated in this file: 300 iterations in 54.2 seconds to a 0.0062 bb gap against a 0.01 bb target, and byte-identical output when the ruled config was solved and walked a second time in a fresh process against a restarted server.

## The payload to convert

A node view carries `kind`, `actor_pos`, `positions`, an `actions` list, and a flat `strategy` array.

```json
"actions":  [{"label":"Fold","kind":"fold","to":0.0,"freq":0.841},
             {"label":"Raise 2.5","kind":"raise","to":2.5,"freq":0.159},
             {"label":"All-in 100","kind":"jam","to":100.0,"freq":3e-07}]

"strategy": [ ... ]
```

`strategy` is `na x 169` floats flattened: the weight for action `k` and hand class `i` is `strategy[k*169 + i]`.

Class index, from `crates/solver/src/preflop/equity.rs`: ranks 0 to 12 as `2` through `A`; a pair is `hi*13+hi`; suited is `hi*13+lo`; offsuit is `lo*13+hi`.
That mapping was confirmed empirically as well as read: a 300-iteration solve returned AA, AKs, AQo and 99 at 1.00 open frequency from LJ, which is what rules out an index-mapping error.
Nothing else about that run is a result, since 300 iterations is a smoke test and marginal hands converge last.

## What a postflop solve costs

Measured 2026-08-23 and 2026-08-24 on an Apple M4, 10 cores, 34.4 GB RAM, CPU engine, GTOpen `4aee435bdeb1`.
Evidence and every row: `reports/active/latest_postflop_solve_cost.txt`.
Read these as per-unit costs with their hardware named, never as a total. A figure for 1,755 flops is a multiplication somebody else does.

Two lines, ranges taken from the committed export rather than invented: a single-raised pot at SPR 17.7 (pot 5.5), and a three-bet pot at SPR 5.78 (pot 16). Both pot and stack figures follow from the export's own opening and 3-bet sizes, which is what ties them to it.
Study quality is GTOpen's own 0.3% of the starting pot.

**Tree size is the first wall, and it is memory rather than time.**
At a 33/75 bet menu with a 2.5x raise on all three streets and `max_raises: 2`, the three-bet flop tree is 2,830,230 nodes and 1,073,702 action nodes, arena 3.7 GB.
The single-raised tree at the same menu is 6,220,932 nodes and 2,347,996 action nodes, arena **21.7 GB**, and was never attempted: the measuring script refused it against its own ceiling of 12,026 MB, 35% of this machine's RAM. That is a policy refusal, not an observed failure, and the solver's own guard would not have stopped it either.
A solve that exceeds RAM fails rather than slows, so the menu is a memory decision before it is a time decision.

**The cheapest memory lever is flooring the range, not dropping a bet size.**
Arena scales with the number of hands in the tree, not with its action nodes. Flooring both ranges at 0.01 leaves the single-raised action-node count at 2,347,996 - identical - while hands fall from 1131v679 to 360v559 and the arena from 21,663 MB to **10,881 MB**. On the three-bet line it is 3,726 MB to 2,385 MB. Two thirds of the grid sits below a 1% weight, far under the resolution of a 0.3%-of-pot target, so that 2.0x is close to free.
Reducing turn and river to a single bet size is the other lever and it is not free: it buys 750,792 action nodes and a 6.1 GB arena at the cost of a real bet size. Reach for the floor first.

**Iterations to study quality land in 220 to 260 across everything measured, and texture moves that too.**
Each count carries a 20-iteration bracket, since exploitability is only checked every 20 iterations. Holding line, menu and ranks fixed, monotone `Kc7c2c` reached target at 240 and two-tone `Kc7d2d` at 260, and `9c8c7c` monotone at 220. So iteration count is not texture-independent; it rises with texture and compounds with the per-iteration factor below, which makes rainbow worse than that factor alone implies.
Two caveats on "line-independent". The target is a percent of pot, so it is 0.0165 chips on the single-raised line against 0.0480 on the three-bet line - a 2.9x difference in absolute accuracy, and a criterion written in bb rather than percent of pot will not reproduce these counts. And the single-raised cells ran the reduced menu while the three-bet cells ran the full one, which is why the report labels those rows `not-cost-comparable`.

**Board texture is the largest per-iteration driver: budget a rainbow flop at 1.65x a two-tone and 3.48x a monotone.**
Those are exact orbit reductions over the full tree, computed from the solver's own representative rule, and they are hardware-independent, which is why they and not a timing belong in a budget. The README's own timings give 1.68x and 3.44x, matching.
The measurements are the noisy realisation of that, and the report derives them from its own rows: comparing only rows that share a tree size, a menu and an iteration count, so texture is the one thing left differing, rainbow costs 1.46x to 1.52x a two-tone and 3.05x to 3.22x a monotone. Both sit a little under theory, and the reason is visible in the rows: the rainbow probe ran first from a cool start against fully-warm comparators, its drift reading +79.5% against +7.4% and +9.4% on its partners. Prefer the exact factor to any of these.

**Per action node per hand per iteration, 1.7 to 2.0 nanoseconds** across four cells spanning both lines and both tree sizes.
This is the figure that rescales to another tree or another range, which is what this section is for; a bare seconds-per-iteration does not, since it carries whatever tree it was measured on. For reference the gross figure ranged 0.85 to 3.28 seconds per iteration.
Two things still move the normalised figure: texture, which puts the two-tone cell at 4.28 ns, and machine state, which put a freshly restarted server at 1.11 ns on the same config that read 1.79 ns late in a long session.

**Machine state is worth about 1.6x, and the cause is process state rather than heat.**
The same config measured 1.379 s/iteration on AC late in a long session whose drift probe read +149.5%, and 0.852 on battery against a freshly restarted server at +20.6%. Battery throttles, so power was not the cause. What differed was a server carrying a 10.3 GB high-water mark versus one starting at 1.4 GB, and the server never returns freed pages to the OS. The remedy is therefore free: restart the server between solves, which matters most for exactly the long-lived batch process a 1,755-flop run would use.

**Peak resident memory is the arena plus about 5% on the first solve after a restart, and grows from there.**
Freshly restarted, a three-bet flop solve peaked at 3,951 MB against a 3,742 MB arena. The identical config solved again in the same process peaked at 4,731 MB, arena plus 26%. That overhead is tree structure, a fixed cost rather than a percentage, so do not scale the 5% up to a 21.7 GB arena. Provision above the arena, not at it, and this is one observation of a fresh server, not a law.
The 10.2 to 10.9 GB peaks in the matrix rows are high-water marks over every spot that process had held. They overstate one solve by about 2.6x on the three-bet tree and 1.7x on the reduced single-raised tree.

**Convergence is front-loaded and then flattens.**
One three-bet cell: 11.84% of pot at 20 iterations, 3.55% at 40, 0.87% at 100, 0.33% at 220, 0.295% at 240.
The local decay exponent falls as the solve runs - about 1.74 over iterations 20 to 40, then settling near 1.0 to 1.3 - so a fit taken early is too steep and extrapolates to too few iterations. A log-log fit over the 15-to-30 window under-predicts the true count by a median of 22% and by 27% on the deeper line; fitting the whole 5-to-30 window instead brings the median to about 5%. The rule is about the window, not a universal correction: do not anchor on the tail of a short probe, and do not use a short probe at all on a deep tree.

**Determinism: byte-identical.**
One config solved twice gives the same root strategy digest `ca16cf82eeb9c96e`, a largest per-action frequency divergence of 0, no combo present in only one run, and 240 iterations to the same 0.2948% both times.
The digest also matches the run recorded a day earlier, so it survives a server restart and a change of process. No accuracy target or tolerance is needed. This is reproducibility of the same computation; it says nothing about whether the strategy at 240 iterations has settled.

**Three biases sit on the figures above, and the deflation is the larger one.**
They must not be netted casually, but a reader is entitled to know which way the total leans.

1. *Inflation, at most 1.6x.* Timings were taken on a machine carrying session state, as above.
2. *Deflation, about 2x.* The converged cells are six monotone and one two-tone. Weighting the texture factors over the 1,755 canonical classes, which split 455 rainbow, 1,014 two-tone and 286 monotone, the pooled set is about 1.9 to 2.2x cheaper than a real flop set. GTOpen's own 47, 95 and 184-flop subsets sample on raw isomorphism weight, so they carry a still more rainbow-heavy mix.
3. *Deflation, about 1.4 to 1.8x.* Every per-iteration figure normalises on total hands, and these ranges carry the full unfloored grid, so a floored range would show lower cost per solve.

See `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL` in `backlog.yml`.

## Not verified

Do not repeat any of these as established.

- **Whether the strategy has settled at 220 to 260 iterations.** Only exploitability was targeted, and action frequencies on indifferent hands converge later than exploitability does - this document already says so for preflop and it was never checked for postflop. Nothing was solved deep and diffed against a shallower solve. The determinism result does not cover this: both runs stopped at 240. If frequencies need several times that, every cost figure here is off by the same multiple, and anything committed as chart data from a 240-iteration solve is unproven.
- **Exploitability against an unrestricted opponent.** The 0.3% target is measured by a best response walking the same tree, so it bounds exploitability against an opponent confined to the same bet menu. It is not a bound against one who can bet any size, and the abstraction error of a two-size menu is larger. A 3.7 GB three-bet tree is comfortable on a laptop only at this menu and these ranges.
- **Most board structures, not only rainbow.** Five cells converged, on two rank patterns. Never reached the target: rainbow-dry, rainbow-connected, paired, ace-high connected, and disconnected-low. A paired board is a structural gap rather than a suit one.
- **Turn- and river-rooted solves.** Only flop roots were built and solved. A flop solve already contains its turn and river subgames, but a separately configured turn spot is a different game and its cost is unmeasured.
- **Batch reports.** `REPORTS` claims a weighted canonical subset of 47, 95, 184 or all 1,755 flops. None of the four was run, and nothing here says what the batch costs beyond one solve times a count.
- **The solved payload's size on disk.** Never measured, and artifact size is one of the grounds the flop-only ruling rests on.
- **Table sizes other than six-handed**, limps, and antes. The README claims 2 to 9 players with limps and cold calls. Only the six-seat, no-limp config above was built.
- **Save and load.** The format is a `GTOPREFLOP1` magic, then a JSON header holding the full solver config, then raw f32 arenas. Read in `crates/solver/src/preflop/save.rs`, never exercised. If it works as read, config and result travel together in one file.
- **GPU.** The README puts CUDA at about ten times faster. Untested, and there is no NVIDIA GPU on this machine. Every figure above is the CPU engine.
- **Its own memory guard.** GTOpen's tree-size guard reads `/proc/meminfo`, which does not exist on Darwin, and falls through to a flat 48,000 MB. It cannot fire before this machine thrashes, so every arena ceiling above is the measuring script's own and not the solver's.
