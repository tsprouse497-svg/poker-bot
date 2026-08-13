# GTOpen: Verified Capabilities And Extraction Path

Notes for whoever picks up the preflop coverage problem.

The binding constraint on this bot is preflop chart coverage: 36 committed spots, 21.3% of self-play hands voided, 78 distinct spots refused against real hands.
Filling it needs a solver this repo can re-run and describe, because a committed artifact whose origin nobody can check is the thing `docs/CORPUS_COMPARISON_LIMITS.md` already names as the weakest claim here.
GTOpen is the candidate. This note records what was established by running it on 2026-08-13, and keeps that separate from what was only read.

**Everything in the first four sections was executed. Everything in the last section was not.**

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

The missing licence is a process problem rather than a legal one for our use.
Running a public tool and keeping your own output is uncontroversial; redistributing its source is the act a missing licence restricts, so reference it by URL and commit hash and do not vendor it into this tree.
A source card can honestly say "unlicensed at time of use" if the author has not answered by then.

## Config surface, as accepted

This exact body was posted to `/api/preflop/spot` and built successfully.
Position names `LJ` and `HJ` are taken as given, so no vocabulary translation is needed between this repo and the solver.

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

Two fields matter more than the rest.
`rake_pct` and `rake_cap` make the rake basis a parameter rather than something inherited from a vendor, and `open_raises` does the same for the opening size.
Those are exactly the two properties the Phase 08 corpus comparison showed the committed chart is mismatched on: it is a raked NL25 solve at 2.5bb read against a rake-free sample whose median open is 2.25bb.
`max_raises` controls whether the tree reaches four-bets, which is the class of spot the Phase 04 artifact schema currently cannot express at all.

## Extraction path

Four calls, all exercised end to end. No Rust is needed to extract; this is drivable from Python inside this repo.

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
**169 hand classes per action is the committed artifact's shape exactly**, so the conversion into `action_weights` is close to mechanical.

Class index, from `crates/solver/src/preflop/equity.rs`: ranks 0 to 12 as `2` through `A`; a pair is `hi*13+hi`; suited is `hi*13+lo`; offsuit is `lo*13+hi`.

That mapping was confirmed empirically as well as read.
A 300-iteration solve returned AA, AKs, AQo and 99 at 1.00 open frequency from LJ, matching the committed chart cell for cell, which is what rules out an index-mapping error.
Nothing else about that run should be read as a result: 300 iterations is a smoke test, and marginal hands are exactly what converges last.

## Not verified

Do not repeat any of these as established.

- **Solve time and convergence.** Only 300 iterations were run and no timing was recorded. How long a real solve takes on this CPU is the single most decision-relevant unknown, and it should be measured before anything is planned around it.
- **Determinism.** The same config has never been run twice and diffed. Do this before any source card claims the output is reproducible; if it is not byte-identical, the card has to pin an accuracy target and state a tolerance instead.
- **Table sizes other than six-handed**, limps, and antes. The README claims 2 to 9 players with limps and cold calls. Only the six-seat, no-limp config above was built.
- **Save and load.** The format is a `GTOPREFLOP1` magic, then a JSON header holding the full solver config, then raw f32 arenas. Read in `crates/solver/src/preflop/save.rs`, never exercised. If it works as read, config and result travel together in one file, which is most of a provenance record for free.
- **The rest of the API.** Roughly twenty routes exist under `/api/preflop/` including export, lock, profiles and saves. Four were used.
- **GPU.** The README puts CUDA at about ten times faster. Untested and irrelevant on this machine.

## What this does not settle

Whether GTOpen and the committed GTO Wizard chart agree at the 36 spots we already hold.
That comparison is the thing that decides whether this becomes a phase, and it needs a converged solve rather than a smoke test.
Run it before committing to a pipeline, and treat a systematic one-directional disagreement as evidence about rake rather than as a defect in either solution.

If the chart is ever re-sourced from here, replace it rather than extending it.
A chart whose cells come from two solution families is not a strategy; it is two half-strategies that assume different opponents, and no check in this repo would notice.
