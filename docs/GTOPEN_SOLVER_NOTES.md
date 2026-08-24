# GTOpen: Verified Capabilities And Extraction Path

What was established by cloning, building and running GTOpen: the preflop surface on 2026-08-13, and the postflop engine on 2026-08-23 and 2026-08-24.

**Everything down to "Not verified" was executed. Everything in "Not verified" was not.**

The postflop section sits high rather than at the end on purpose. Its absence is what let a later reader infer from an all-preflop note that the tool is preflop-only, and a reader who stops early should meet the correction rather than miss it.

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
It was written from the README alone; the routes below have since been driven end to end and a real solve measured, which is the next section.

Postflop CFR is the tool's primary function and the Preflop Lab is the bolt-on beside it.
The postflop engine is the un-namespaced route surface: `/api/spot`, `/api/solve`, `/api/node`, `/api/runouts`, `/api/reports/*`, `/api/lock`, `/api/exploit`.
A setup takes both ranges on a 13x13 grid, a board of 3, 4 or 5 cards for a flop, turn or river solve, pot, stacks, rake, and per-street bet, raise and donk sizes.
`SEND TO POSTFLOP` carries both conditional ranges, the pot and the stacks out of a Preflop Lab line into that setup, which is the only coupling between the two engines.
Solves target an exploitability percentage of pot, with 0.3% given as study-quality.
`REPORTS` batch-solves one spot across a weighted canonical flop subset of 47, 95, 184, or all 1,755 flops.
Node locking and a best-response mode exist and the README claims both are covered by tests.

Suit isomorphism is exploited internally and described as exact. No rank abstraction is claimed.
The README's 1.4x and 2.2x are branch counts at the first chance node, not speedups. Measured below, the saving is larger.

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

Two lines, both with ranges taken from the committed export rather than invented: a single-raised pot at SPR 17.7, and a three-bet pot at SPR 5.78.
Study quality is GTOpen's own 0.3% of the starting pot.

**Tree size is the first wall, and it is memory rather than time.**
At a 33/75 bet menu with a 2.5x raise on all three streets, the three-bet flop tree is 2,830,230 nodes and 1,073,702 action nodes, arena 3.7 GB.
The single-raised tree at the same menu is 6,220,932 nodes and 2,347,996 action nodes, arena **21.7 GB**, and was refused before solving on a 34.4 GB machine.
Reducing turn and river to a single bet size brings it to 750,792 action nodes and a 6.1 GB arena, which fits.
A solve that exceeds RAM does not run slowly, it fails, so the menu is a memory decision before it is a time decision.

**Iteration count to study quality is nearly line-independent: 220 to 260 iterations**, across both lines and every texture measured.
Cost differences between spots come from tree size and board texture, not from needing more iterations. The single-raised line is node-hungry, not iteration-hungry.

**Board texture is the largest per-iteration driver.**
On one identical tree at fixed iterations: rainbow 4.570 s/iteration, two-tone 2.967, monotone 1.410.
So a rainbow flop costs about **1.54x a two-tone and 3.24x a monotone**, which is well above the README's 1.4x and 2.2x.

**Per iteration, 0.85 to 3.28 seconds** on this machine, over five converged cells plus the determinism pair.
That spread is mostly thermal, not spot: the same config measured 1.379 s/iteration on a loaded machine and 0.852 on a cool one with a freshly restarted server, so machine state alone is worth about 1.6x and no single timing here is better than that.

**Peak resident memory is the arena plus about 5%.**
On a freshly restarted server a three-bet flop solve peaked at 3,951 MB against a 3,742 MB arena.
The 10.2 to 10.9 GB peaks in the matrix rows are high-water marks carrying earlier spots in the same process, and overstate one solve by about 2.6x. Only a fresh server gives a figure worth quoting.

**Convergence is front-loaded and then flat.**
One three-bet cell: 11.84% of pot at 20 iterations, 3.55% at 40, 0.87% at 100, 0.33% at 220, 0.295% at 240.
Estimating the iteration count from a short early window under-predicts it by a median of 22% and by 27% on the deeper line, because the local exponent is still steepening there. Add about a quarter to any thirty-iteration estimate, and do not use a short window at all on a deep tree.

**Determinism: byte-identical.**
One config solved twice gives the same root strategy digest `ca16cf82eeb9c96e`, a largest per-action frequency divergence of 0, no combo present in only one run, and 240 iterations to the same 0.2948% both times.
The digest also matches the run recorded a day earlier, so it survives a server restart and a change of process. No accuracy target or tolerance is needed.

Two biases run in opposite directions and must not be netted against each other. The timings above were taken on a warm machine, which inflates them. The five converged cells are four monotone and one two-tone with no rainbow among them, which deflates them against any real flop set. See `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL` in `backlog.yml`.

## Not verified

Do not repeat any of these as established.

- **Rainbow flops at study quality.** No rainbow board reached 0.3% of pot on either line; the five converged cells are monotone or two-tone. The texture ratio above comes from a fixed-iteration comparison, so a rainbow cost is scaled rather than measured.
- **Turn- and river-rooted solves.** Only flop roots were built and solved. A flop solve already contains its turn and river subgames, but a separately configured turn spot is a different game and its cost is unmeasured.
- **Batch reports.** `REPORTS` claims a weighted canonical subset of 47, 95, 184 or all 1,755 flops. None of the four was run, and nothing here says what the batch costs beyond one solve times a count.
- **Table sizes other than six-handed**, limps, and antes. The README claims 2 to 9 players with limps and cold calls. Only the six-seat, no-limp config above was built.
- **Save and load.** The format is a `GTOPREFLOP1` magic, then a JSON header holding the full solver config, then raw f32 arenas. Read in `crates/solver/src/preflop/save.rs`, never exercised. If it works as read, config and result travel together in one file.
- **The rest of the API.** Roughly twenty routes exist under `/api/preflop/` including export, lock, profiles and saves. Four were used. On the postflop side `/api/runouts`, `/api/lock` and `/api/exploit` were not.
- **GPU.** The README puts CUDA at about ten times faster. Untested, and there is no NVIDIA GPU on this machine. Every figure above is the CPU engine.
- **Its own memory guard.** GTOpen's tree-size guard reads `/proc/meminfo`, which does not exist on Darwin, and falls through to a flat 48,000 MB. It cannot fire before this machine thrashes, so the arena ceilings above are the measuring script's own and not the solver's.
