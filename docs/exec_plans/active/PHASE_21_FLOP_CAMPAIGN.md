# Phase 21: The Flop Campaign

- **Branch** `phase/21-the-flop-campaign`, worktree `~/projects/poker-bot-worktrees/phase-21`
- **Base** `553f6f7`, `main` after MAINT-40 declared the phase
- **Authorised by** Taylor, 2026-09-26: trust the solve and get more of it, instead of measuring the
  bot first. Machine picked on cost per solved flop with memory as a hard limit. Nothing re-solved or
  hand-edited to look better.

## Objective

Make GTOpen use every core, pick the rented machine on cost per solved flop, and solve preflop lines
into phase 16's index and object storage, each solved board closed, until a spending cap, the index
budget or the last admitted line stops it. The contract is
`docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md`.

## Scope

Stage 1 and 2, `contract-update`: the contract, the decision list
`reports/phase_audits/decisions/PHASE_21_FLOP_CAMPAIGN_DECISIONS.md`, and this phase's review
directory. Implementation scope is set when stage 4 opens, and is expected to be the solve driver and
its transport and harvest modules, a new report generator, the postflop index and sample, the command
registry entries and this phase's tests. Forbidden throughout: the preflop chart and its artifact,
any code that plays a turn or river decision (stored here, played by the next phase), three-bet pots,
and everything `AGENTS.md` Boundaries forbids.

## Direction from Taylor, 2026-09-26, after stage 3

Move to the cloud now rather than later. The bot will eventually run on AWS next to its stored
solves, so solving work goes to AWS as soon as the code is ready instead of being benchmarked on the
Mac first. Rulings that stand: AWS, a private bucket on his account, the $100 trial, one GPU machine
in the trial, and the exact machine types and hourly prices shown to him before anything is rented.
Also recorded on `TURN-AND-RIVER-PLAY-FROM-THE-SAVED-SOLVES-NEEDS-ITS-OWN-PHASE`.

Where it meets the contract, flagged to Taylor rather than edited, because the contract is at its
300-line cap and wins until a `contract-update` changes it:

- Part 1 times thread counts "on every machine the phase solves on", and the Mac still solves: phase
  16's four boards are re-solved here to prove a changed thread count leaves the answer alone. So the
  Mac's sweep (3, 5, 8 and 10 threads, three interleaved stretches of 100 iterations each) still runs
  here. It costs about an hour of this machine and no money, and it is the only benchmark kept on
  the Mac; every other timing is taken on AWS.
- "Offline-first" in `AGENTS.md` against a bot that plays on AWS beside its solves: not this phase's
  to settle, since this phase does not play the turn or river; carried on the backlog entry above.

## Where the stage 1 numbers came from

Measured 2026-09-26 by a read-only fact-finding lane that wrote nothing in the repo, re-run by the
coordinator where marked. Scratch scripts in the session scratchpad: `tree.py`, `tree2.py` (per-seat flop count) and `nodes.py`
(a Python port of GTOpen `crates/solver/src/tree.rs` `legal_actions`, `apply_action` and
`street_end`, lines 432-760, validated against the August tree of 6,220,932 nodes and 2,347,996
action nodes and against all four committed planned arenas to the byte; re-run by the coordinator),
`vram.py` (GTOpen `game.rs:365-373`), `rank.py` (imports `measure_corpus` and
`arrival_probabilities` from `scripts/generate_postflop_betting_report.py`).

- Threads: `init_rayon` at `~/projects/gtopen/crates/server/src/main.rs:2546-2563`;
  `sysctl -n hw.ncpu hw.physicalcpu hw.memsize hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu`
  gives 10, 10, 34359738368, 4, 6. `SOLVER_THREADS` set nowhere under `scripts/` or `src/`.
- Per-iteration cost: iterations and wall clocks from `data/artifacts/postflop/determinism.json`.
- Memory: `MEMORY_CEILING_FRACTION` at `postflop_solve_driver.py:59`; planned arenas from each
  object's `solve.arena_bytes`; ceiling 13,743,895,347 bytes on this machine.
- Index budget: `index.json` `committed_bytes` 100,845 and `headroom_bytes` 16,032,570, which
  reconciles against `scripts/check_file_sizes.py:29` and the tracked bytes under `data/artifacts`,
  4,938,950. Entry cost (2,866 - 432) / 5 = 486.8 bytes.
- Closure: 14 flop action nodes per board, seven per seat, from `tree2.py`.
- Memory bar: `review_maxarena.py`, written by the stage 1 reviewer and re-run by the coordinator,
  walks all 22,100 flops on the committed line: largest planned arena 12.87 GB on `2d2h2s`, 32.18 GB
  of RAM at 0.40, 33.69 GB of VRAM, 15.8 percent of flops above 12.24 GB.
- Canonical flops: 1,755 classes over 22,100 flops by brute force over `canonical_board`.
- Ranking: 499 corpus hands, 259 reach a flop, 225 heads-up in band over 32 lines; fourth is
  `SB:call`, a limp.
- GPU: `crates/solver/Cargo.toml:22-23` feature `gpu`; `kernels.cu:143-148` uses `atomicAdd`.

## Delegation Plan

- Worker lanes: stage 1's fact-finding was one read-only lane (done). Stage 1's contract text and
  stage 2's decision list are coordinator-owned, because each criterion transcribes a ruling Taylor
  made in session or a number the lane measured, and the decisions are questions for him that must
  be written by whoever will put them to him. From stage 4: a test-author lane that did not write
  the contract; at stage 6, separate build lanes for the driver (threads, machine record, ranges for
  any line, closure harvest), the report generator, and the campaign runs themselves.
- Ownership: coordinator owns the contract, decision list, ExecPlan and integration. Lanes own the
  files named in their brief and nothing else.
- Expected outputs: stage 1 contract with measured criteria; stage 2 decision list with a class on
  every call; stage 4 frozen tests and canaries; stage 6 driver, generator and campaign data.
- Status: fact-finding completed; stage 1 contract written and reviewed in three rounds.
- Integration order: contract, decisions, human gate, tests, freeze, build, gate, review, packet.
- Review handoff: every stage whose diff touches something a human wrote gets a read-only reviewer
  that wrote none of it, asked also what it held back.

## Slices

- [x] Lane opened at stage 0 from `main` at `553f6f7`.
- [x] Stage 1 facts measured.
- [x] Stage 1 contract criteria for all three parts.
- [x] Stage 1 review: three blockers (closure could pass without the root, phase 16's boards had no
  coherent closing solve, the memory bar was measured on four boards rather than every flop) and ten
  non-blockers, all folded into the contract. Round 2 found a fourth blocker, the benchmark solves
  unpriced and sequenced before any cap, fixed with two caps. Round 3 resolved it and raised four
  non-blockers, which the coordinator fixed after the round: the six texture boards come after the
  box's determinism re-proof and use the configuration stage 2 rules; the sweep counts logical
  processors; a GPU trial is counted in its own ruling; one leftover short line. The coordinator
  also checked the two GPU claims the reviewer could not: `atomicAdd` at
  `crates/solver/src/gpu/kernels.cu:143-148`, and GPU use switched by the `gpu` feature and
  `SOLVER_GPU` at `crates/server/src/main.rs:253-281`.
- [x] Stage 2 decision list: ten questions for Taylor and four defaults. Its review, round 1: four
  blockers (every flop solve already solves the turn and the repo throws it away; decision 8 hid the
  deep convergence result; no call covered other lines' bet sizes; the git budget left out the object
  list), all folded in. Round 2: the turn storage figure assumed a compact format the repo does not
  use, and three-bet pots were neither admitted nor excluded; both folded in. Alignment filed:
  `LINE-RANKING-BY-CLOSING-DECISION-ARRIVAL-COUNTS-LINES-THE-CHART-NEVER-PLAYS`, and notes on three
  existing entries. The coordinator rewrote id-shaped tokens in both review notes mechanically -
  line labels such as "SB v BB" and two proposals the reviewers withdrew - because the citation check
  reads hyphenated capitals as backlog ids. Round 3 pending.
- [x] Stage 3: Taylor ruled all ten on 2026-09-26, in plain-language questions with the
  recommendation first. Two went against the recommendation, both after he was shown the cost:
  keep the river as well as the turn (about 2.5 TB a line by a rough estimate), and try the GPU in
  the trial. Asked a follow-up, he ruled that phase 21 stores the turn and river and a new phase
  plays them, filed as `TURN-AND-RIVER-PLAY-FROM-THE-SAVED-SOLVES-NEEDS-ITS-OWN-PHASE`. The contract
  is amended to the rulings in this stage, before any test is written. The stage 3 review found two
  costs of the river ruling he had not been shown - harvest time and the five-line total - and an
  unasked precision question; he was re-asked and ruled keep the river but measure first, at two
  bytes a number (decision 15). It also found the record adding words he never said and crediting
  him with coordinator procedure; both corrected.
- [ ] Stage 4: tests authored by a lane that did not write the contract (six files, 256 tests, ten
  canaries). Two independent reviewers, one mechanical and one on the poker, found four blockers
  between them - report records never exercised, the small blind line's card memory unpinned,
  closure counts tested on the button line only, and the posted ranges unchecked for three lines -
  and both confirmed the author's two corrections to the contract's figures, filed as
  `PHASE-21-CONTRACT-CARRIES-THREE-MEMORY-FIGURES-ITS-OWN-TREE-RULES-CONTRADICT`.
- [ ] Stage 6 is not code only. The frozen tests need the committed button-line manifest to list
  phase 16's four boards as closed, so the first green gate waits on the Mac sweep, the four
  re-solves at the chosen count reproducing the committed cells, and the harvest of every turn and
  river decision point from those solves (about 5.9 million river points across the four). From
  phase 16's recorded first runs at five threads the four solves alone are 375.6 + 1,677.4 + 1,035.9
  + 616.0 = 3,704.9 seconds, about an hour, in `determinism.json`; harvest time is unmeasured and is one of the things the contract measures. A
  re-solve that does not reproduce halts the lane for Taylor; it is never worked around.
- [ ] Stage 6 runs every solve through `postflop_lines.plan_for` and `seat_labels`, never through
  `scripts/solve_postflop_sample.py`'s button-line code. The stage 4 poker review found four places
  there that hardcode the button line and no frozen test covers: `seat_of_player` (big blind always
  out of position), `conditional_ranges` (button-line export paths), `preflop_line_for`
  (`BTN_OPEN_BB_CALL`) and `write_solve_config` (seat-named keys `oop_bb_call` and `ip_btn_open`).
  The stage 6 review checks that no campaign solve reached them.
- [ ] Stage 6 builder notes from the stage 4 review: every determinism record keeps wall clocks
  unrounded, because the frozen copy rule refuses two runs tied to the microsecond and a rounded
  clock could trip it; the frozen tests pin a flop object as uncompressed JSON `{"cells": [...]}` at
  its object key under the fetched folder, so the flop is not compressed; and the fetch's check that
  a turn or river object holds the decision points its counts claim is stage 6's to write and test,
  since their two-byte format is chosen then. The stage 6 review checks the re-solve's own output
  against the committed cells, since copying `index.json`'s digests into a manifest cannot be told
  apart offline from reproducing them.
- [ ] Before any candidate is ranked: GTOpen builds (does not solve) one small blind tree, and its
  node count and arena are compared with the port's 4,109,130 nodes and planned arena. A difference
  is a finding for Taylor, not a test edit. On each rented box the machine record is compared with
  the server's printed "solver threads" line, since the record counts processors from
  `/proc/cpuinfo` and GTOpen counts the ones it may use
  (`THE-MACHINE-RECORD-COUNTS-PROCESSORS-GTOPEN-MAY-NOT-BE-ALLOWED-TO-USE`).
- [ ] Before any spend: the specific AWS machine types and hourly prices go to Taylor. Read from
  instances.vantage.sh on 2026-09-26, us-east-1 on demand, to be confirmed on AWS's own page: CPU
  c8g.8xlarge (Graviton4, 32 vCPU, 64 GiB) $1.276/h, c7i.8xlarge (Intel Sapphire Rapids) $1.428/h,
  c7a.8xlarge (AMD EPYC 9R14) $1.642/h; GPU g7e.2xlarge (RTX PRO 6000 Blackwell, 96 GiB card, 64 GiB
  RAM) $3.36/h. The 48 GB L40S (g6e) is out: the small blind line needs 48.50 GB of card memory by
  GTOpen's own estimate. A 64 GiB box holds the small blind line's 18.53 GB arena under the 0.40
  ceiling (27.5 GB).
- [ ] At the campaign budget: Taylor confirms or drops the river on its measured size, harvest time
  and monthly bill. If he drops it, the contract's river criteria become a `contract-update` in this
  lane before the campaign starts, and decision 1 is recorded as re-ruled.

## Verification

Stage checks through `uv run python scripts/loop_stage.py --phase 21`. The full gate is expected red
from stage 1 until stage 6 registers the two new command IDs, as for every phase before it.

## Outcome

Not yet.

## Next Agent Bootstrap

Worktree `~/projects/poker-bot-worktrees/phase-21`, loop at stage 1 in `contract-update` mode. Run
`uv run python scripts/loop_stage.py --phase 21` for the next action. Nothing may be spent on a cloud
account until stage 3 records Taylor's rulings on provider, candidates and a spending cap.
