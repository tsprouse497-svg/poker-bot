# Phase 21 stage 4 review: the tests, before the freeze

Reviewer: independent read-only review subagent, which wrote none of the work it reads. Date
2026-10-03. Scope: `git diff 1b0dcc01e288e19939c81bc62d6edc08f453736d HEAD`, HEAD at `50a9410`
(decision 15 re-ruled; that commit touches no test). Eight `tests/test_flop_campaign*.py` files,
the `tests/test_postflop_solve_driver.py` additions, `tests/fixtures/flop_campaign/`, ten canaries
in `verification/mutations.yml`, two commands in `scripts/run_verify.py`, and the backlog and
ExecPlan edits.

The driver's question: *would each test fail against a plausible wrong implementation, and does it
assert on real behaviour rather than on state rebuilt from the code under test? Stage 5 freezes
these, so a weak test is preserved perfectly.*

What I ran: the nine files of `pytest_flop_campaign` through plain `uv run python -m pytest`;
`ruff check` and `ruff format --check` on the new files and on `tests/`; my own port of GTOpen's
`tree.rs` rules (`legal_actions`, `apply_action`, `street_end` at `~/projects/gtopen` `4aee435`) in
a scratch script; the reach and combo figures re-derived from the committed chart in a scratch
script; one import of the borrowed 75 percent cell through `import_postflop_cell`. No gate,
`check_gate_bite` or loop driver was run. I edited nothing tracked.

What I re-derived myself, and found right:

- **Decision point counts.** My port gives 14 flop points, 131 per turn card and 628 per river
  card on a 5.5 pot (6,419 turn, 1,477,056 reachable river, 30,772 under the dealt turn card), and
  14, 134 and 657 on a 5.0 pot (6,566, 1,545,264, 32,193). Every one matches the tests.
- **The flop tree.** `max_raises` counts raises, not the opening bet (`num_raises` grows only on
  `Raise`), so bet, raise, re-raise and then fold or call is right, and the out-of-position seat
  uses its `bet` list on the flop because `donk` applies only after the root street. The fixture's
  fourteen keys are the tree's fourteen. No flop raise is clamped: the largest re-raise, to 25.78bb
  after a 75 percent bet, is far under 0.85 of 97.5 (the server divides the configured 85.0 by
  100).
- **Raise sizes.** GTOpen raises *to* `street_bet[opp] * m`, so a check-raise over 1.815 is to
  4.5375 and a re-raise to 11.34375; the harvest tests read a re-raise against the level faced.
  The server sends `amount` as the raw f64 (`query.rs` around line 386), so a 1e-7 refusal does not
  catch display rounding.
- **Seats and pots.** The small blind raiser is out of position, pot 5.0; every other opener is in
  position, pot 5.5 with the small blind's dead 0.5. Line reach from the chart: 5.5296, 3.6616,
  2.752, 2.7136, 2.4162 percent. Floored combos: small blind open 730, big blind defence against it
  470, button open 498, cutoff open 350, big blind against the button 380.
- **Texture groups.** 286, 858, 156, 156, 286 and 13 classes (1,755); 6,864, 10,296, 1,872, 1,872,
  1,144 and 52 flops (22,100).
- **The registered command fails for the right reason.** 41 failed, 50 passed and 268 errors. Every
  error is a fixture-setup `ModuleNotFoundError` naming a `poker_training_bot.solver_artifacts`
  module, every failure an `AssertionError`, and nothing reads `Interrupted: N errors during
  collection`.

Earlier rounds, checked against the tests rather than the commit messages. Report records are now
exercised (`test_flop_campaign_report_records.py`). The small blind line's card memory is pinned
to the byte (48,503,485,008). Closure counts are tested on the small blind's own tree in both the
tree and manifest files. Posted ranges are checked against the chart for all five lines. The round
3 blocker is closed: `TestAFetchedFlopObjectIsCheckedByItsContents` refuses six wrong objects,
three of which hold fourteen cells, so a count-only check fails.

## Blocker

- **Nothing makes the bot play a decision point after a raise, which is the reason decision 16
  exists.** Decision 16 was ruled because "the bot cannot look up the node after its own raise".
  The frozen tests pin the key, the harvest and the fetch, and none of them asks the strategy to
  answer such a node. Concrete failing scenario: stage 6 adds `FlopAction.multiplier`, the harvest
  and the fetch, and leaves `src/poker_training_bot/strategy/postflop_committed.py:245` building
  `FlopAction(labels[entry.seat], entry.action, fraction * 100)` for a raise. Under the frozen
  `test_a_raise_keyed_as_a_percent_of_pot_is_refused` that call now raises `ValueError`, which
  `:246-260` catch and turn into a miss. Every frozen test passes, and the bot refuses every flop
  node after any raise, its own included. So eight of each closed board's fourteen flop points are
  bought and never played. Fix before the freeze: one test beside `TestAFetchedClosedBoardIsPlayed`
  (`tests/test_flop_campaign_lines.py:517`). Its fetched object holds the button's
  check-raised cell (flop actions `BB:check`, `BTN:bet@33`, `BB:raise@2.5x`), and a table query
  where the button bets the 33 percent chips and the big blind raises to exactly 2.5 times that
  level must return a `StrategyDecision`. Use exactly 2.5 times the chips so the test needs no
  ruling on the raise tolerance.

- **Decision 15's re-ruled rounding is frozen into data and nothing tests it, and stage 6 cannot
  add the test.** Since 2026-10-03, turn and river frequencies are rounded to a tenth of a percent,
  with the largest entry paying the residue, and stored at two bytes. The ExecPlan
  (`docs/exec_plans/active/PHASE_21_FLOP_CAMPAIGN.md`, the stage 6 builder-notes bullet) calls the
  turn and river format "stage 6's to write and test". But `AGENTS.md` forbids an implementer to
  write `tests/**`, and stage 5 takes it out of scope, so stage 6 can write the format and never
  test it. Concrete failing scenario: stage 6 reads "two bytes a number" as IEEE half precision.
  Near 1.0 that steps in about 0.05 percent, so rows are neither thousandths nor exactly one in
  sum, and 23 TB of river is committed in a format the ruling does not describe while every frozen
  test passes. Fix before the freeze: an owed row codec in the
  style of the other owed modules. Pin that a solver row encoded and decoded equals
  `postflop_harvest._rounded(row)` (thousandths, sum exactly 1000, residue on the largest entry,
  the flop's rule), that each stored number is a whole count from 0 to 1000 in two bytes, and that
  an object's decision-point count can be read back, so the fetch's turn and river count check has
  something frozen to stand on. Today `published_line()` gives the turn and river stand-in bytes
  that are checked only by digest.

## Non-blocker

- **Held-back item 1, `fetched_machine` holds one cell while its counts say 14**
  (`tests/test_flop_campaign_lines.py:441-495`). This freezes the closure check at fetch time only.
  A stage 6 that also checks closure, or `strategy_digests`, when the strategy loads breaks
  `test_a_machine_that_fetched_the_board_answers_the_node`, and the manifest-side fixtures (cells
  borrowed with only `spot_key` changed) likewise forbid a soundness import at fetch time. One check
  in one place is a defensible design, but nothing then ties what is on disk to what was checked: no
  test asks the strategy to refuse a fetched flop object whose bytes are not the index's digest. A
  strategy that reads whatever JSON sits at the object key passes every test. Recommend one
  added test before the freeze: a fetched object altered after the fetch is not played.
- **Held-back item 4.** The round-trip test pins `HarvestedNode`'s keyword fields, which already
  exist under those names, and the cell field `multiplier`, which is decision 16's data format.
  Both are right to freeze.
- **Held-back item 5: no canary on the raise key or on the content check.** None of the ten
  canaries attacks `render_flop_action`'s `x`, the harvest's menu check, or the fetch's
  `DECISION_POINTS_MISMATCH` comparison, which was the round 3 blocker's whole subject. The
  contract asks only for one canary per command, so this is not owed, but `verification/**`
  freezes at stage 5 too. Recommend one canary that compares the flop object's cell count instead
  of its key set, witnessed by `pytest_flop_campaign`.
- The ExecPlan's stage 4 line still says "six files, 256 tests, ten canaries"; there are eight
  files plus the driver file now.
- `linux_arm_graviton.cpuinfo.txt` gives CPU part `0xd40`, Neoverse V1, which is Graviton3. The
  ExecPlan's ARM candidate, c8g, is Graviton4 (Neoverse V2, `0xd4f`). It pins the parse only, but
  the test's message names V1 as if it were the candidate.
- `test_every_script_that_starts_gto_server_builds_its_environment_through_the_guard` matches
  only `Popen(`. A launcher written with `subprocess.run` escapes it.
- `test_the_ceiling_is_the_ruled_fraction_of_this_machine_s_memory` asserts
  `MEMORY_CEILING_IS_MEASURED is True`, a flag the code sets about itself. The next line, which
  compares with `os.sysconf`, is the real test.
- `test_every_fixture_key_is_one_the_key_producer_derives` says it "proves every one is a node a
  dealer reaches". It proves only that the key producer accepts each one. The proof that the tree
  builds them is the fixture's derivation, which my port confirms.
- Decision 14 stays `runtime-reversible`. The margin test computes the margin from
  `arena_bytes` rather than pinning 4.86 percent, and `phase_16_reading` in the tree tests is the
  test's own arithmetic.

## Alignment

- Held-back item 3: turn and river sizes clamped to all-in have no name in any key, and decision
  16 covers only the flop's raises. By my port, on the button's line 24 of the 131 decision points
  per turn card and 206 of the 628 per river card come after a bet or raise GTOpen clamped to
  all-in. On the small blind's line it is 24 of 134 and 212 of 657. Such a size is neither 66 nor
  125 percent nor 2.5x, and almost never a hundredth of either unit. Nothing frozen here blocks a
  ruling, because `FlopAction` and `flop_line` are flop-only and no flop raise on either tree is
  clamped. But whoever keys the turn and river meets the round 3 blocker again. This needs a new
  backlog id, proposed title: "Turn and river sizes clamped to all-in have no name in any spot
  key". It belongs beside `TURN-AND-RIVER-PLAY-FROM-THE-SAVED-SOLVES-NEEDS-ITS-OWN-PHASE`.
- Held-back item 2, second half: at the table, how far from exactly 2.5x a faced raise may sit and
  still match is still unruled, and no test owns it.
  `THE-FLOP-RAISE-TOLERANCE-IS-BORROWED-FROM-THE-BET-MENU-RULING`.
- Held-back item 6: `ruff format --check tests/` now reports 40 of 64 files. Every new
  `test_flop_campaign*.py` file is formatted. `tests/test_postflop_solve_driver.py` was already
  unformatted at the base commit and its new hunks did not change that. It is the existing drift,
  not a new lint failure, and `ruff check` passes.
  `THE-REPO-S-FORMATTER-IS-NOT-IN-THE-GATE-AND-THIRTY-NINE-TEST-FILES-DIVERGE`.
