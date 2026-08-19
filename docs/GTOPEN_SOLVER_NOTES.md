# GTOpen: Verified Capabilities And Extraction Path

What was established by cloning, building and running GTOpen on 2026-08-13.

**Everything down to "Not verified" was executed, apart from the "Postflop exists" section, which says so in its own first line. Everything in "Not verified" was not.**

That section sits high rather than at the end on purpose. Its absence is what let a later reader infer from an all-preflop note that the tool is preflop-only, and a reader who stops early should meet the correction rather than miss it.

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

## Postflop exists, and none of it was run

Recorded because the absence of this section led a later reader to conclude GTOpen is preflop-only.
Everything in this section is read from the README and the route table, not executed, so it belongs to the same class as "Not verified" below.

Postflop CFR is the tool's primary function and the Preflop Lab is the bolt-on beside it.
The postflop engine is the un-namespaced route surface: `/api/spot`, `/api/solve`, `/api/node`, `/api/runouts`, `/api/reports/*`, `/api/lock`, `/api/exploit`.
A setup takes both ranges on a 13x13 grid, a board of 3, 4 or 5 cards for a flop, turn or river solve, pot, stacks, rake, and per-street bet, raise and donk sizes.
`SEND TO POSTFLOP` carries both conditional ranges, the pot and the stacks out of a Preflop Lab line into that setup, which is the only coupling between the two engines.
Solves target an exploitability percentage of pot, with 0.3% given as study-quality.
`REPORTS` batch-solves one spot across a weighted canonical flop subset of 47, 95, 184, or all 1,755 flops.
Node locking and a best-response mode exist and the README claims both are covered by tests.

Suit isomorphism is exploited internally and described as exact, worth about 1.4x on two-tone flops and 2.2x on monotone. No rank abstraction is claimed.

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

## Not verified

Do not repeat any of these as established.

- **Solve time and convergence.** Only 300 iterations were run and no timing was recorded. Measure a real solve before planning around it.
- **Determinism.** The same config has never been run twice and diffed. Do this before claiming the output is reproducible; if it is not byte-identical, an accuracy target and a tolerance have to be recorded instead.
- **Table sizes other than six-handed**, limps, and antes. The README claims 2 to 9 players with limps and cold calls. Only the six-seat, no-limp config above was built.
- **Save and load.** The format is a `GTOPREFLOP1` magic, then a JSON header holding the full solver config, then raw f32 arenas. Read in `crates/solver/src/preflop/save.rs`, never exercised. If it works as read, config and result travel together in one file.
- **The rest of the API.** Roughly twenty routes exist under `/api/preflop/` including export, lock, profiles and saves. Four were used.
- **GPU.** The README puts CUDA at about ten times faster. Untested, and there is no NVIDIA GPU on this machine.
