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
- [ ] Stage 4: tests authored by a lane that did not write the contract (nine files, 365 tests at
  2026-10-04, eleven canaries; counted with `pytest --collect-only` and the `flop-campaign` ids in
  `verification/mutations.yml`). Two independent reviewers, one mechanical and one on the poker, found four blockers
  between them - report records never exercised, the small blind line's card memory unpinned,
  closure counts tested on the button line only, and the posted ranges unchecked for three lines -
  and both confirmed the author's two corrections to the contract's figures, filed as
  `PHASE-21-CONTRACT-CARRIES-THREE-MEMORY-FIGURES-ITS-OWN-TREE-RULES-CONTRADICT`.
- [ ] Stage 6 is not code only. The frozen tests need the committed button-line manifest to list
  phase 16's four boards as closed, so the first green gate waits on the Mac sweep, the re-solve
  of the four boards, and the harvest of every turn and river decision point from that solve. Since
  decision 17 that solve is the new-tree one at 45ff860, not the pin's: its four boards took 360.6 +
  1,804.9 + 821.0 + 330.4 = 3,316.9 seconds at ten threads (run A in `determinism.json`), and each
  kept its whole strategy export, 6 GB a board, from which the harvest reads. A re-solve that does
  not reproduce halts the lane for Taylor; it is never worked around.
- [ ] Stage 4 round 4 (2026-10-03/04), after decisions 16 and 15's re-ruling: the independent review
  raised two blockers, both folded in by the test lane - a fetched point after a raise is played,
  and the turn and river row format is pinned (`postflop_street_rows`, whole counts 0 to 1000 in two
  bytes, little-endian). Little-endian is a coordinator choice with no poker meaning: every
  candidate box (x86 and Graviton) is little-endian, so no reader byte-swaps. Stage 6 builder note:
  the canary `flop-campaign-fetch-counts-flop-cells-instead-of-keys` finds the line
  `if sorted(held_keys) != sorted(expected_keys):` in the fetch, so the fetch must contain it
  verbatim.
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
  since their two-byte format is chosen then. Decision 15 was re-ruled 2026-10-03: turn and river
  frequencies are rounded to a tenth of a percent (the flop's thousandths, residue to the largest
  entry) and still stored at two bytes; the trial flops measure what standard compression saves. The stage 6 review checks the re-solve's own output
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
  RAM) $3.36/h. The 48 GB L40S (g6e) is out: the small blind line needs 51.24 GB of card memory by
  GTOpen's own estimate on the tree decision 17 rules (48.50 on the pin's). A 64 GiB box holds the
  small blind line's 19.62 GB arena, as the driver reads it, under the 0.40 ceiling (27.5 GB).
- [ ] At the campaign budget: Taylor confirms or drops the river on its measured size, harvest time
  and monthly bill. If he drops it, the contract's river criteria become a `contract-update` in this
  lane before the campaign starts, and decision 1 is recorded as re-ruled.

- [ ] Decision 17, ruled (b) on 2026-10-04: take only upstream `85b0a692`'s tree fix, so a street
  both players check clears the initiative. `THE-PINNED-SOLVER-CARRIES-THE-AGGRESSOR-THROUGH-A-CHECKED-STREET`
  carries the diagnosis and every figure. Slices, in order:
  - [x] Solver: branch `poker-bot/check-through-clears-initiative` in `~/projects/gtopen-poker-bot`,
    on the bulk export `3f8bf98`, commit `b058335`: the fix's hunks and upstream's regression test,
    verbatim. Release build and the whole GTOpen test suite green (105 tests pass, one
    preflop benchmark ignored as upstream marks it), `check_through_street_clears_the_initiative` included.
  - [x] Figures re-derived by a tree counter linked against the patched crate, building each spot
    under either rule without solving. The old rule reproduces every frozen figure to the byte; the
    new rule gives every figure decision 17 quoted. No figure differs from the ruling, so nothing
    goes back to Taylor on that ground. The counter is kept, untracked, at
    `~/projects/gtopen-poker-bot/incoming-patches/tree-count/`: `cargo build --release` there, then
    from this worktree `uv run python <dir>/jobs.py <dir>/line_ranges.json > <dir>/jobs.json`,
    `<dir>/target/release/treecount < <dir>/jobs.json > <dir>/counts.json`, and
    `uv run python <dir>/bars.py <dir>/counts.json` for the memory bars over all 22,100 flops.
    `"carry": true` is the pin's rule and `null` the new one.
  - [x] Decision 18's GPU fold patch into the same branch: applied as `c48f437` on Taylor's direct
    approval, 2026-10-04, after the permission check had refused it on the relayed ruling. GPU code
    only; type-checks with the `gpu` feature; the CPU server rebuilt after it is byte-identical. First
    proved by the GPU trial.
  - [x] Contract-update task: phase 21's contract rewritten under its cap (298 lines), folding its
    rulings and the new tree; phase 16's contract amended in one line, now at its cap
    (`PHASE-16-CONTRACT-IS-AT-ITS-LINE-CAP`). Read-only review, three rounds: four blockers found
    (the river confirmation, the settling runs under the cap, Glacier turn and river unchecked by
    the fetch, and the dropped flop fetch check), all fixed and marked resolved by the reviewer.
    Coordinator-owned, as the ExecPlan's stage 1 contract was: it transcribes rulings.
  - [x] Implementation, commit 7ff2a4b. A test lane that wrote no code moved every old-tree pin in
    eight frozen test files and the mutation descriptions, keeping the pin's figures as tests of the
    old rule (`carry_aggressor_through_checks=True`), and added solver-build record tests. A build
    lane that wrote no test made every solve record name its build, read from the binary's own clone,
    refusing a dirty clone or a binary older than its commit; pointed the default server at the
    clone; stopped the cost script labelling runs with the reference clone; corrected the driver's
    note on the empty donk list; and added `--export-strategies`, which keeps every strategy of a
    solve beside its object for the later harvest. The binary was rebuilt from the committed clone
    at 15:01 and hashes the same as the 14:24 build. The coordinator wrote the solver notes' clone
    section and decision 17's scope line.
  - [x] Read-only review of 7ff2a4b, two rounds: two blockers (a binary built on a newer commit
    passed after the clone was checked out to an older one; one report test still pinned the pin's
    river) and one later gap in the cost script, all fixed at 2d6c034 and c32ee78, with a new test
    file on a real git repository and six canaries, each seen to bite by hand. Re-frozen at c32ee78
    (66 files, 1,489 tests), narrowed at 6d1eb66. The suite outside the unbuilt flop campaign tests
    passes but one test, `test_every_mutation_applies_exactly_once_to_its_file`, red because stage 4's
    canaries name modules stage 6 has not built yet, as before this work.
  - [x] One more re-open after the re-solve, for `test_each_committed_cell_document_is_unchanged`,
    which pins the old cells' sha256: moved to the re-solve's hashes and re-frozen at 45ff860. The
    re-solve review's one blocker, the betting report still calling the pin's cell current, fixed at
    0bbb940 and marked resolved by the reviewer.
  - [x] Answered by Taylor 2026-10-04 ("sure"), recorded under decision 5: the GPU machine's own
    processors meet the CPU-first rule. Raised by the contract review: decision 5 starts the trial from a GPU, while
    the contract still wants one flop solved and timed on a CPU of the same provider first. Whether the GPU pod's own processors count as that CPU is his to say before the trial.
  - [x] Phase 16's four boards re-solved on the new tree, on this Mac and before any rented box, so
    the box's determinism finding compares against new-tree digests: about 45 minutes of all-core solving per
    set of four at ten threads, so it waits for a window Taylor grants (lid open, on AC), run under
    `caffeinate -i -s`, `pmset -g log` read afterwards. Then the index, the byte budget and the
    export card rebuilt and the full suite run. Plan: copy the pin's objects aside to
    `~/poker-bot-solve-objects/postflop-pin-4aee435`; run A in this worktree,
    `scripts/solve_postflop_sample.py --all --threads 10 --export-strategies` (about 45 minutes and
    about 24 GB of exports); run B in a scratch copy without `.git`, `--all --threads 10` into an empty
    object folder; then `--determinism-tree` and `--determinism-objects` on run B to write
    `determinism.json`. The sample, `determinism.json` and `solve_config.json` join scope first.
    Done 2026-10-04, 15:50 to 17:32, at 45ff860: every cell passes the commit rule, run B equals run
    A byte for byte with a per-combo gap of 0.0, every recorded arena equals the new tree's planned
    arena, and every export counts 14, 6,419 and 1,549,968. No thermal sleep in `pmset -g log`; the
    Mac went to idle sleep at 17:32 after caffeinate ended. Run A's `Kh7d2c` ran at about 5.3 seconds
    a round against the sweep's 3.24, so no cost figure is taken from it. The flop strategies moved
    the way the fix predicts: the button bets `9c8c7c` about 54 percent where it bet nearly all of it,
    and the big blind's lead on `8c8d3c` fell from about 30 percent to under 1. The 24 GB of exports
    sit only in `~/poker-bot-solve-objects/postflop-clone-b058335` (moved there from the shared folder, which every lane reads, after the first copy turned main red); the pin's objects are back in the shared folder and also in
    `postflop-pin-4aee435`. The re-solve review found the betting report still describing the pin's
    cell as current, which a build lane is fixing.

- [ ] Rebase note from MAINT-41, 2026-10-04: it removes the whole-tree `headroom_bytes` from the
  preflop source card and the postflop index (index schema 2). When it merges, this lane's rebase
  conflicts on the card, `index.json`, the betting report, `freeze.lock` and `mutations.yml`: take
  MAINT-41's card, rebuild the index with `solve_postflop_sample.py --index-only`, regenerate the
  report, keep both sides' mutations, re-freeze.

- [ ] Decision 1 re-ruled 2026-10-04: the turn is stored, only the river is solved at the table.
  - [x] Contract-update: closure is the flop and the turn, the river never stored; reviewed read-only,
    no blocker in the text.
  - [ ] Precondition before this lane merges: `AGENTS.md` and phase 22 on `main` still say the turn is
    solved live. Owned by the session declaring phase 22 (MAINT-43); Taylor asked to give it his
    ruling. `AGENTS.md` wins over a contract, so this lane does not merge until `main` agrees.
  - [x] Decision 4 re-ruled: every object in the standard class ("we can do standard on glacier",
    read as standard instead of Glacier, as recommended; confirmed "what you recommended").
    Contract's storage criterion changed; reviewed read-only, no blocker.
  - [x] Implementation: the closure, manifest, fetch, report and street-row tests re-opened by the
    test lane for a flop and turn closure (7af4337), every river figure kept as a tree fact; reviewed
    read-only with no blocker; re-frozen at 6649062. Left for the stage 6 build:
    `THE-BULK-STRATEGY-EXPORT-KEEPS-THE-RIVER-THE-RULING-SAYS-NOTHING-KEEPS` and
    `TWO-FLOP-CAMPAIGN-TEST-FILES-SIT-AT-THE-700-LINE-TEST-CAP`.

## Verification

Stage checks through `uv run python scripts/loop_stage.py --phase 21`. The full gate is expected red
from stage 1 until stage 6 registers the two new command IDs, as for every phase before it.

## Outcome

Not yet.

## Next Agent Bootstrap

Worktree `~/projects/poker-bot-worktrees/phase-21`, loop at stage 6 (build) in `implementation`
mode, `base_commit` at the merge of `main` (fd1bb89). Run `uv run python scripts/loop_stage.py --phase
21` for the next action. Part 1 is built. Decisions 17 and 18 are done: the clone at `c48f437`
carries both fixes, the contract and tests state the new tree, phase 16's four boards are re-solved on
it, and its objects live in `~/poker-bot-solve-objects/postflop-clone-b058335`, never the shared
`postflop` folder every lane reads. Taylor re-ruled decision 1 on 2026-10-04: the turn is stored and
only the river is solved at the table. Phase 21's contract, river criteria and closure and street-row
tests still describe a stored river, and `AGENTS.md` on `main` says both turn and river are solved
live; both need a `contract-update` and a test re-open before stage 6 builds the harvest. The stage 6
review note `stage-06-build.md` is still owed for the whole stage, beside the decision 17 notes.
