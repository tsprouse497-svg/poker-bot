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
- [ ] Before any spend: the specific AWS machine types and hourly prices go to Taylor.

## Verification

Stage checks through `uv run python scripts/loop_stage.py --phase 21`. The full gate is expected red
from stage 1 until stage 6 registers the two new command IDs, as for every phase before it.

## Outcome

Not yet.

## Next Agent Bootstrap

Worktree `~/projects/poker-bot-worktrees/phase-21`, loop at stage 1 in `contract-update` mode. Run
`uv run python scripts/loop_stage.py --phase 21` for the next action. Nothing may be spent on a cloud
account until stage 3 records Taylor's rulings on provider, candidates and a spending cap.
