# MAINT-42 audit packet: the turn and river are solved at the table

Taylor asked whether rivers have to be solved and stored, since storing them multiplies the data.
The session measured single turn and river solves on GTOpen and showed him the figures. He ruled on
2026-10-04 to lift the runtime-solver boundary for the turn and river only: preflop and the flop
stay committed artifacts solved offline, the turn and river are solved at the table instead of
stored, the turn is acceptable at the measured figure and the river must answer within one second.
This task changes the rule and the documents that state it. It changes no range, artifact, code
path or test, and builds nothing.

## What shipped

- `AGENTS.md`: the boundary is now "No runtime solver calls before the turn", with the ruling, the
  figures it rests on, the two conditions a live solve keeps (local machine, same answer for the
  same inputs), and a statement that no phase owns building it.
- `docs/GTOPEN_SOLVER_NOTES.md`: a new section with the turn and river rows below; the two places
  that said turn and river roots were never posted are corrected, and the "Not verified" item now
  names what is still unmeasured, which is narrowed ranges.
- `docs/ROADMAP.md` and `docs/V2_ROADMAP.md`: each statement that called the boundary permanent or
  said turn and river cannot exist now carries the exception.
- `backlog.yml`: `LIVE-TURN-AND-RIVER-SOLVING`, which carries the six questions building it must
  answer: an owner, the engine and its missing licence, the gate's no-GTOpen rule, the ranges
  entering the turn, bets off the menu, and determinism.

## How to check it without code

1. Read the boundary in `AGENTS.md` and compare it with the three rulings in the ExecPlan.
2. Compare the figures in it with the river and turn rows below.
3. Search the live documents for "runtime solver": every hit either says preflop and flop, or is a
   phase's own scope limit.

## Measurement

Apple M4, 10 cores, 34.4 GB RAM; GTOpen `4aee435bdeb1` at `~/projects/GTOpen`; `SOLVER_COMPRESS=0`
through the sample script's own `Server` class, which starts a fresh server per solve. Ruled menu,
button-open against big-blind-call ranges from the committed export, floored, target 0.3% of pot
checked every 10 iterations. Pots: flop 5.5bb, a 33% flop bet called gives the turn pot; a 66% turn
bet called gives the river pot. The ranges are preflop ranges, not narrowed by later betting.

### Single solves, wall clock from the solve call to the server reporting done (20 ms poll)

| Root | Board | Pot | Stack | Nodes | Action nodes | Arena MB | Iterations | Exploitability % | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| turn | `Kh7d2c5s` | 9.13 | 95.69 | 12711 | 4862 | 36.55 | 140 | 0.296 | 2.002 |
| turn | `8c8d3c9h` | 9.13 | 95.69 | 12711 | 4862 | 37.23 | 150 | 0.275 | 2.397 |
| turn | `9c8c7cKd` | 9.13 | 95.69 | 12711 | 4862 | 35.74 | 140 | 0.281 | 1.686 |
| river | `Kh7d2c5sAd` | 21.18 | 89.66 | 39 | 14 | 0.10 | 60 | 0.269 | 0.024 |
| river | `8c8d3c9hQs` | 21.18 | 89.66 | 39 | 14 | 0.11 | 60 | 0.254 | 0.026 |
| river | `9c8c7cKd2h` | 21.18 | 89.66 | 39 | 14 | 0.11 | 60 | 0.262 | 0.026 |
| river-checked | `Kh7d2c5sAd` | 9.13 | 95.69 | 39 | 14 | 0.10 | 80 | 0.242 | 0.026 |

### Turn speed levers, wall clock (10 ms poll)

The "about half the combos" rows keep each range's most heavily weighted classes until about half
its combos remain. That is a crude stand-in for a narrowed range, not one.

| Board | Change | Seconds | Iterations | Exploitability % | Action nodes | Arena MB |
|---|---|---|---|---|---|---|
| `Kh7d2c5s` | baseline | 2.167 | 140 | 0.296 | 4862 | 36.6 |
| `Kh7d2c5s` | target 0.5% | 1.725 | 110 | 0.441 | 4862 | 36.6 |
| `Kh7d2c5s` | target 1% | 1.099 | 70 | 0.965 | 4862 | 36.6 |
| `Kh7d2c5s` | one size turn+river | 0.644 | 100 | 0.27 | 1976 | 13.8 |
| `Kh7d2c5s` | ranges ~50% | 0.94 | 120 | 0.284 | 4862 | 16.8 |
| `Kh7d2c5s` | ranges ~30% | 0.709 | 140 | 0.279 | 4862 | 9.8 |
| `Kh7d2c5s` | one size + ranges ~50% + 0.5% | 0.185 | 60 | 0.479 | 1976 | 6.4 |
| `9c8c7cKd` | baseline | 1.798 | 140 | 0.281 | 4862 | 35.7 |
| `9c8c7cKd` | target 0.5% | 1.254 | 100 | 0.472 | 4862 | 35.7 |
| `9c8c7cKd` | target 1% | 0.862 | 70 | 0.823 | 4862 | 35.7 |
| `9c8c7cKd` | one size turn+river | 0.508 | 100 | 0.27 | 1976 | 13.5 |
| `9c8c7cKd` | ranges ~50% | 0.788 | 130 | 0.28 | 4862 | 16.6 |
| `9c8c7cKd` | ranges ~30% | 0.447 | 120 | 0.273 | 4862 | 9.8 |
| `9c8c7cKd` | one size + ranges ~50% + 0.5% | 0.177 | 70 | 0.42 | 1976 | 6.3 |

"ranges ~30%" keeps about 30 percent of the combos the same way.

### Scripts

Run from the repo root with `uv run python <script> <gto-server binary> <log dir>`. Neither is
committed as a script: they are one-off measurements, and `scripts/` is for what the repo runs.

```python
"""Time single turn-root and river-root solves on GTOpen under the ruled menu."""
import json, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, "/Users/taylorsprouse/projects/poker-bot/scripts")
sys.path.insert(0, "/Users/taylorsprouse/projects/poker-bot/src")
import solve_postflop_sample as s
from poker_training_bot.solver_artifacts.postflop_solve_driver import (
    SolvePlan, spot_body, solve_config_document, EXPLOITABILITY_TARGET_PCT_OF_POT)
from poker_training_bot.solver_artifacts.postflop_transport import BASE_URL

def call(path, body=None):
    req = urllib.request.Request(BASE_URL + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="GET" if body is None else "POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())

oop, ip = s.conditional_ranges()
oop_t, ip_t = s.range_text(oop), s.range_text(ip)
line = s.preflop_line_for("BB")
# Flop bet 33% called -> turn pot; turn bet 66% called -> river pot.
flop_pot, stack = line.pot_bb, line.effective_stack_bb
b1 = flop_pot * 0.33; turn_pot, turn_stack = flop_pot + 2 * b1, stack - b1
b2 = turn_pot * 0.66; river_pot, river_stack = turn_pot + 2 * b2, turn_stack - b2
SPOTS = [
    ("turn", "Kh7d2c5s", turn_pot, turn_stack), ("turn", "8c8d3c9h", turn_pot, turn_stack),
    ("turn", "9c8c7cKd", turn_pot, turn_stack),
    ("river", "Kh7d2c5sAd", river_pot, river_stack), ("river", "8c8d3c9hQs", river_pot, river_stack),
    ("river", "9c8c7cKd2h", river_pot, river_stack),
    ("river-checked", "Kh7d2c5sAd", turn_pot, turn_stack),
]
server = s.Server(Path(sys.argv[1]), Path(sys.argv[2]))
results = []
for street, board, pot, eff in SPOTS:
    server.start(f"{street}-{board}")
    try:
        plan = SolvePlan(label=board, board=board, preflop_line=line.rendered, range_oop=oop_t,
                         range_ip=ip_t, starting_pot=pot, effective_stack=eff, config=solve_config_document())
        t0 = time.perf_counter(); built = call("/api/spot", spot_body(plan)); t_build = time.perf_counter() - t0
        t1 = time.perf_counter()
        call("/api/solve", {"max_iterations": 2000, "target_exploit_pct": EXPLOITABILITY_TARGET_PCT_OF_POT, "check_every": 10})
        while True:
            st = call("/api/status")
            if st.get("state") != "running": break
            time.sleep(0.02)
        t_solve = time.perf_counter() - t1
        row = dict(street=street, board=board, pot=round(pot,2), stack=round(eff,2), build_s=round(t_build,3),
                   solve_s=round(t_solve,3), iterations=st.get("iteration"), exploit_pct=st.get("exploit_pct"),
                   arena_mb=built.get("arena_mb"), nodes={k: v for k, v in built.items() if "node" in k})
        print(json.dumps(row), flush=True); results.append(row)
    finally:
        server.stop()
Path(sys.argv[2], "results.json").write_text(json.dumps(results, indent=1))
```

```python
"""Time turn-root solves under the levers that might make them faster."""
import json, sys, time, urllib.request, copy
from pathlib import Path
sys.path.insert(0, "/Users/taylorsprouse/projects/poker-bot/scripts")
sys.path.insert(0, "/Users/taylorsprouse/projects/poker-bot/src")
import solve_postflop_sample as s
from poker_training_bot.solver_artifacts.postflop_solve_driver import SolvePlan, spot_body, solve_config_document
from poker_training_bot.solver_artifacts.postflop_transport import BASE_URL

def call(path, body=None):
    req = urllib.request.Request(BASE_URL + path, data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="GET" if body is None else "POST")
    with urllib.request.urlopen(req, timeout=600) as r: return json.loads(r.read())

oop, ip = s.conditional_ranges()
def top_share(rng, share):
    # Crude stand-in for a narrowed range: keep the classes the range holds most heavily, by
    # combo count, until `share` of its combos remain. Not a real post-flop range; a size probe.
    combos = lambda h: 6 if len(h) == 2 else (4 if h.endswith("s") else 12)
    total = sum(w * combos(h) for h, w in rng.items())
    kept, acc = {}, 0.0
    for h, w in sorted(rng.items(), key=lambda kv: -kv[1]):
        if acc >= share * total: break
        kept[h] = w; acc += w * combos(h)
    return kept
line = s.preflop_line_for("BB")
pot, stack = line.pot_bb, line.effective_stack_bb
b1 = pot * 0.33; tpot, tstack = pot + 2 * b1, stack - b1
base = solve_config_document()
one = copy.deepcopy(base)
for seat in one["seats"].values():
    for st in ("turn", "river"): seat[st]["bet"] = [seat[st]["bet"][0]]
RUNS = [  # label, config, range share, target pct
    ("baseline", base, 1.0, 0.3), ("target 0.5%", base, 1.0, 0.5), ("target 1%", base, 1.0, 1.0),
    ("one size turn+river", one, 1.0, 0.3), ("ranges ~50%", base, 0.5, 0.3), ("ranges ~30%", base, 0.3, 0.3),
    ("one size + ranges ~50% + 0.5%", one, 0.5, 0.5),
]
server = s.Server(Path(sys.argv[1]), Path(sys.argv[2]))
for board in ("Kh7d2c5s", "9c8c7cKd"):
    for label, cfg, share, target in RUNS:
        server.start("lever")
        try:
            plan = SolvePlan(label=label, board=board, preflop_line=line.rendered,
                range_oop=s.range_text(top_share(oop, share)), range_ip=s.range_text(top_share(ip, share)),
                starting_pot=tpot, effective_stack=tstack, config=cfg)
            built = call("/api/spot", spot_body(plan))
            t = time.perf_counter()
            call("/api/solve", {"max_iterations": 3000, "target_exploit_pct": target, "check_every": 10})
            while (st := call("/api/status")).get("state") == "running": time.sleep(0.01)
            print(json.dumps(dict(board=board, run=label, solve_s=round(time.perf_counter()-t, 3),
                iters=st.get("iteration"), exploit=round(st.get("exploit_pct"), 3),
                action_nodes=built.get("action_nodes"), arena_mb=round(built.get("arena_mb"), 1))), flush=True)
        finally: server.stop()
```

## Independent review

Pending.

## Gate

Pending.
