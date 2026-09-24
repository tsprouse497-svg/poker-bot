# Phase 16 stage 6 review: the build, mechanical

Read-only. I wrote none of this and edited nothing but this file. No mutation tooling,
`run_verify.py` or `check_gate_bite.py` was run; the canaries below are judged by reading.
`data/artifacts/postflop/` did not exist when I started and does not exist now - I built no
synthetic artifact and wrote nothing under `data/`.

The driver's question: *does the implementation do the work, or only enough to satisfy the frozen
tests?* Three things pass for a reason the contract did not intend, and each is below under
Blocker. Every figure I quote was recomputed here off the repo; the method is stated beside it.

## Blocker

- [resolved] **`canonical_hole_cards` is not canonical. The one collapse the phase permits is applied to the
  board and only half-applied to hero's hand, so which hand class the table produces depends on
  which dressing the dealer dealt.** `src/poker_training_bot/solver_artifacts/postflop_key.py:195`
  moves hero's cards by `board_suit_map(board)` (`:188`), one fixed permutation carrying that
  dressing to the representative. A flop uses at most three suits, so every board has a non-trivial
  stabiliser - the suits it does not use permute freely - and the map is one of several that reach
  the representative. The code never minimises over them.

  Measured, over all 1,176 hero combos on each of the phase's own ruled sample boards, by applying
  all 24 suit permutations to (board, hand) and counting how many combos yield more than one value
  of `canonical_hole_cards`:

  | board (as committed) | hero combos whose class depends on the dressing |
  | --- | --- |
  | `Kh7d2c` rainbow, three suits | 0 of 1,176 |
  | `8c8d3c` two-tone paired | 910 of 1,176 |
  | `9c8c7c` monotone | 1,131 of 1,176 |

  Why that is a miss and not a cosmetic one. Decision 6 budgets the artifact at "1,286,792
  hero-combo classes summed over all 1,755 flops, a mean of 733 per flop". I reproduced both
  figures exactly by enumerating every canonical flop, taking its stabiliser, and collapsing its
  1,176 combos under it: 1,286,792 total, mean 733.2148. That is the collapse the committed cell is
  sized for and it is the collapse `canonical_hole_cards` does not perform. On `8c8d3c` the cell
  holds 721 classes and the table can produce 1,176 distinct strings; on `9c8c7c` it holds 344
  against 1,176. `PostflopBettingStrategy._answer`
  (`src/poker_training_bot/strategy/postflop_betting.py:405`) looks the string up by exact match
  through `PostflopCell.weights_for`
  (`src/poker_training_bot/solver_artifacts/postflop_artifact.py:204`), so the combos that land
  outside the committed list refuse under `postflop-betting:hand-class-not-in-the-cell` on a spot
  the artifact holds a cell for. On the two non-rainbow sample boards that is 455 of 1,176 (38.7%)
  and 832 of 1,176 (70.7%). The alternative - enumerating all 1,176 per cell - is 2,063,880 classes
  against the budgeted 1,286,792, which is 1.604x, and decision 6's own sentence is "That collapse
  is worth 1.6x". So the code either refuses a third to two thirds of hero's range on every
  non-rainbow flop, or it costs the 1.6x the byte model already spent. Nothing in the repo picks.

  The importer cannot catch it either: `postflop_artifact.py:290` requires each committed class to
  satisfy `canonical_hole_cards(representative, item) == item`, and I measured
  `board_suit_map(representative)` to be the identity on each sample representative, so that check
  reduces to "is it sorted" and admits two strings for one class.

  **This is the shaped-around-the-test case.** `tests/test_postflop_key.py:422` and `:435` assert
  `canonical_hand(board, hole) == sorted(apply_suit_map(hole, suit_map(board)))` - a restatement of
  the implementation, not a property of the class. The flush-draw test at `:453` passes because a
  consistent permutation preserves draw status. Not one test asks whether two dressings of one
  board give hero one class. `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS` is the entry
  that predicted exactly this and it is open. Decision 6's 2026-09-15 amendment saw the symptom
  from the fixture side ("a board written in a different dressing makes one file describe the same
  flop two ways") and fixed the committed boards; the table still deals arbitrary dressings.

  The fix is one function: minimise the hand over every permutation carrying the board to its
  representative, which is the same enumeration that reproduces the 733 figure.

- [resolved] **The report prints a "servable" column that is a verbatim copy of the column beside it, and a
  paragraph asserting the two differ.** `scripts/generate_postflop_betting_report.py:619-620`
  increments `measured.arrivals[line]` and `measured.servable[line]` on the same line under the
  same condition, unconditionally. I confirmed by calling `measure_corpus` directly:
  `m.arrivals == m.servable` is `True`, both totalling 215. The ranking at `:981` therefore sorts
  on a Counter identical to arrivals, and the report says at `:929` and in the committed text
  (`reports/active/latest_postflop_betting_report.txt:32-34`) that "the two orders are not the same
  order". Lines 39-51 of the committed report show `servable == arrivals` on every row, including
  the two 3-bet lines at 6 of 6 and 5 of 5.

  The contract's criterion is specific: "sorts on **servable** arrival frequency: a 3-bet line
  serves 47.1% of its arrivals against a single-raised line's 99.0%". Those two ratios are real and
  the generator does compute them (`:950`, `:960`; I recomputed 405/409 = 99.02% and 41/87 = 47.13%
  off the committed corpus and they match the report's lines 57-58) - they are just never applied
  to the ranking. `_substituted_line` (`:632`) drops an out-of-band price before a line is counted,
  so everything that reaches `arrivals` is already 100% servable and the column has nothing left to
  say. The frozen test that should hold this, `tests/test_postflop_betting_report.py:242`, asserts
  only `says(report, "servable")` - the word. That is the second thing that passes for a reason the
  contract did not intend.

- [resolved] **`run_solve` reads three server fields with a default, and each default is the answer that lets
  the run through.** `src/poker_training_bot/solver_artifacts/postflop_solve_driver.py:462`
  `float(built.get("arena_mb", 0.0))` - a response that omits or renames that field plans a 0-byte
  arena, `check_memory_ceiling` passes, and the contract's named guard ("The solve driver carries
  its own memory ceiling and refuses above it before solving") never fires. `:488`
  `float(status.get("exploit_pct", 0.0))` - a missing field reads as 0.0% of pot, which
  `classify_outcome` (`:406`) calls `converged-to-target` and `commit_verdict` (`:424`) accepts,
  printing "0.0000% of pot". `:489` `int(status.get("iteration", 0))` the same way. The module's own
  docstring (`:7-10`) says it exists because "both mistakes this phase already paid for are silent:
  a solve that dies on memory after it has run, and a threshold posted in the wrong unit". These
  three defaults reintroduce the first one and add a new one on the accuracy gate that decides
  whether a cell is committed at all. A field the driver cannot find must refuse, not default.

[resolved] 2026-09-24 by MAINT-38: every bullet above that lacked a marker was audited by an independent lane and marked where the fix or ruling is shown, finding by finding, in `reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`.

## Non-blocker

- `src/poker_training_bot/strategy/postflop_betting.py:451`
  `amount = min(round(size * big_blind), all_in)` clamps a committed size down to hero's stack
  rather than refusing. Reachable: the key carries the *nominal* pot and stack off the substituted
  line, so a table that opened to 3.0bb against an `@2.5` cell leaves hero 0.5bb less behind than
  the cell assumes, and the bot then bets all-in at a size the solve never produced while the
  report counts it as an answered bet. `DecisionAuditRecord` still proves legality, which is why
  this is not a blocker. Proposed `A-COMMITTED-SIZE-IS-CLAMPED-TO-ALL-IN-RATHER-THAN-REFUSED`.
- `scripts/generate_postflop_betting_report.py:814-816` and the validator at `:200`.
  `check_spot_count_matches_index` compares `printed = len(cells)` against
  `in_index = len([cell for cell in cells if cell.spot_key in indexed])`, which is a subset of
  `cells` by construction. It can only ever catch a fetched cell missing from the index; it cannot
  catch the drift its own docstring and `postflop-report-spot-count-drifts` describe (report says
  42, index holds 41), because the index's own count is `indexed_total` at `:864` and is never
  compared to anything. The canary does still bite today, on 1 against 0.
  `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL` (existing).
- Four of the generator's five re-derivation checks pass vacuously with no artifact, and the report
  does not say so, while it does label vacuous refusal codes.
  `check_bytes_reconcile` is skipped entirely (`:838`, guarded on `index is not None`),
  `check_rate_excludes_non_weight_bytes` compares 0.0 to 0.0 (`:840-843`),
  `check_coverage_splits_by_cause` is handed `answerable=1.0, losses={}` when `corpus.flops` is 0
  (`:845-852`), and `check_spot_count_matches_index` compares 0 to 0. Contrast
  `latest_postflop_betting_report.txt:197-212`, where every zero-count refusal code is labelled
  `vacuous` by name. Proposed `A-GENERATORS-RE-DERIVATION-CHECKS-ARE-NOT-LABELLED-WHEN-VACUOUS`.
- `src/poker_training_bot/strategy/contract.py:52` widened `SeatAction` from
  `_PREFLOP_HISTORY_ACTIONS` to `_ACTION_NAMES` for both histories at once, so `preflop_actions` now
  accepts `bet`, which no preflop seat can take (the module's own docstring at `:38` says so). The
  street restriction was dropped rather than moved. It matters because the level-monotonicity walk
  at `:268-280` inspects only `entry.action == "raise"`, so a preflop `SeatAction(seat, "bet", 50)`
  below the big blind is accepted where the same amount as a `raise` is refused - the comment three
  lines above says a clamp "launders an impossible history into a plausible one". `postflop_actions`
  gets no level walk at all. Proposed `SEATACTION-LOST-ITS-STREET-SPECIFIC-VOCABULARY`.
- `src/poker_training_bot/solver_artifacts/postflop_artifact.py:279`
  `actions = tuple(str(item) for item in ...)` coerces any JSON value to a string and validates
  nothing: an action list of `["banana", "zzz"]` imports, and duplicates are not refused even though
  `postflop_betting.py:447-448` does `sized.index(action)` on that list. Caught later at the table
  by the `action not in query.legal_actions` refusal rather than at import, which is the direction
  the module's own docstring argues against. Proposed
  `A-COMMITTED-CELLS-ACTION-NAMES-ARE-NOT-CHECKED-AT-IMPORT`.
- `src/poker_training_bot/solver_artifacts/postflop_key.py:496` `menu_size_chips` uses Python's
  `round`, which is banker's rounding, where decision 14 item 4 rules "rounding to the nearest
  chip". Decision 14's worked example survives by parity - `round(181.5)` is 182 because 182 is even
  - but `round(82.5)` is 82 and `round(180.5)` is 180, both away from nearest. Proposed
  `MENU-SIZE-CHIPS-ROUNDS-HALF-TO-EVEN-NOT-TO-NEAREST`.
- `src/poker_training_bot/solver_artifacts/postflop_artifact.py:475` `indexed_spot_keys` does
  `entry["spot_key"]` with no shape check, and the generator reads `index["covered_preflop_lines"]`,
  `index["line_count_bound_by"]`, `index["cells_solved_and_rejected_above_one_percent"]` and
  `index["committed_bytes"]` the same way (`:823-827`, `:838`). A malformed index raises `KeyError`
  or `TypeError` out of a module whose whole subject is refusing with a named code. Proposed
  `THE-INDEX-BODY-IS-READ-UNGUARDED-BELOW-ITS-STRICT-IMPORTER`.
- `tests/test_postflop_artifact.py:497` - correction (c) replaced `len(files) == 3` with
  `len(files) >= 3`, which is unbounded. The amendment authorises **a** fourth file ("the fourth
  file is a fourth situation on a board already in the sample"); nothing now stops a fifth or a
  fiftieth. The "still three flops" half is preserved by the board-set assertion at `:494`, so this
  is a bound that was widened past its ruling rather than an assertion that was lost. Proposed
  `THE-SAMPLE-FILE-COUNT-IS-NOW-UNBOUNDED-WHERE-THE-RULING-ALLOWED-ONE-MORE`.
- `src/poker_training_bot/strategy/postflop_betting.py:356-377` `_covered_line` returns the first
  committed line all of whose prices fall inside the 20% band, with no check that only one does. The
  committed chart's two prices (2.5 and 7.5) give disjoint bands today, so nothing is ambiguous yet;
  a third price between them would make the walk pick by iteration order and call it a match.
  Proposed `TWO-BANDS-THAT-OVERLAP-WOULD-BE-RESOLVED-BY-ITERATION-ORDER`.
- `src/poker_training_bot/strategy/postflop_committed.py:254-258` matches a faced **raise** against
  `raise_fractions` derived from the fetched cells, using `MENU_FRACTION_TOLERANCE`. Decision 14
  ruled the bet menu only, and the docstring at `:210-212` says so ("That reading is this module's
  own"). A tolerance in behaviour that no decision entry carries is the shape
  `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` and decision 14 itself were filed over. Proposed
  `THE-FLOP-RAISE-TOLERANCE-IS-BORROWED-FROM-THE-BET-MENU-RULING`.
- Both artifact canaries' witnesses currently fail for want of data:
  `test_a_weight_outside_zero_to_one_is_refused_rather_than_rendered` and
  `test_a_committed_size_that_cannot_be_played_is_refused_at_import` are in the 28 reds, because
  every cell fixture loads a committed sample file. `pytest_postflop_betting` is therefore red with
  and without either mutation, so `check_gate_bite` cannot show either bites until the sample lands.
  `A-CANARY-READS-A-CRASH-AS-A-KILL` (existing) is the neighbouring entry.

## Alignment

- `THE-WEIGHTED-DRAW-IS-WRITTEN-TWICE` (proposed). `postflop_betting.py:133-163` is a line-for-line
  copy of `preflop_chart.py:75` and `:109-120` - `_roll` and `collapse` both. The module says so
  itself at `:147-150` and hands it to the coordinator, which is the right thing to do and is why
  this is an alignment item rather than a finding against the lane. The 500-line cap that forced the
  four-module split is the condition that makes a third copy cheaper than a home for it.
- `ONE-FLOP-LINE-WALK-IS-WRITTEN-IN-BOTH-DIRECTIONS` (proposed). `postflop_spot_queries._flop_street`
  (`:77-110`) and `postflop_committed.flop_action_line` (`:195-246`) are the same walk: carry the
  pot forward, take each sized action as chips added over that seat's standing bet, update the level.
  They agree today - I checked the conventions match on both the bet and the raise branch - and
  nothing makes them keep agreeing. A round-trip assertion over a committed cell would.
- `THE-SIZED-ACTION-SET-IS-DEFINED-FOUR-TIMES` (proposed). `frozenset({"bet", "raise"})` at
  `contract.py:16`, `postflop_key.py:129`, `postflop_artifact.py:115` and `postflop_committed.py:58`,
  the last of which exists precisely "so the table side and the cell side agree". `_chips` is a
  second small duplicate, identical at `postflop_committed.py:72` and `postflop_spot_queries.py:62`.
- `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS` (existing). The first blocker is this
  entry arriving, and it names the long-term shape: a test that asserts the implementation's own
  formula cannot see a property of the class the formula is supposed to represent. The stage-3
  review asked stage 4 for something "strictly stronger than the flush-draw check" and stage 4
  delivered something stronger in the same direction rather than in the missing one.
- `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES` (existing). Unchanged by this stage and
  correctly named by `postflop_artifact.py:22-24`; recorded here only so a reader of this note does
  not count it as covered by the importer's re-derivations.

## The three frozen-test corrections, each against the ruling it cites

**(a) `floor_range` drops rather than lifts.** Authorised. Decision 12's own first sentence is
"Flooring means dropping every hand below a weight threshold out of the range before solving", and
the ruling takes the default. Not weaker: the old pair asserted `set(after) == set(before)`, `all
>= FLOOR`, `after["AA"] == 1.0` and that a zero is lifted; the new pair asserts `set(after) <=
set(before)`, the class-level shape of every surviving key (which is what the test is named after
and what set equality never checked), exact dict equality on `{"AA": 1.0, "KK": 0.01}` - which newly
pins the floor as inclusive at exactly 0.01, matching `postflop_artifact.py:171`'s `<` - and two
drop cases. Nothing was lost. `tests/test_postflop_artifact.py:487-499` and `:653-699`.

**(b) the key carries the completed preflop line.** Authorised, and the amendment is a Taylor
ruling of 2026-09-15 with the measurement in it. The assertion got stronger, not weaker:
`test_the_preflop_line_appears_verbatim_with_its_sizes` went from one substring check on a preflop
spot key to two checks, one of them against the producer's own `rendered` output. Seven new tests
were added requiring the raiser to have a flop spot, including the bet test the old suite provably
lacked. I diffed the full test-function name sets of all four touched files at `01f6ee4` against
HEAD: nothing was deleted by this correction, one rename
(`test_the_band_scales_with_the_price_rather_than_being_a_chip_count`).

**(c) the sample test counts boards, not files.** Authorised in substance - the amendment is a
Taylor ruling and it does allow a fourth file - but the new bound overshoots it, which is the
non-blocker above. `test_the_sample_holds_exactly_three_flops` was deleted rather than renamed; its
content was absorbed into `test_the_three_boards_are_the_ruled_three`, and the board-set assertion
does imply three flops. The board constants moved to the canonical dressing; I verified
`canonical_board(("Kc","7d","2h")) == ("Kh","7d","2c")` and
`canonical_board(("8h","8d","3h")) == ("8c","8d","3c")`, and that `9c8c7c` is its own
representative, all off the module rather than off the amendment's prose.

## Canaries, judged by reading

All three `find` strings occur exactly once in their named file (checked with `grep -cF`).

- `postflop-weight-bounds-not-enforced`, `postflop_artifact.py:307`. With the line disabled, the
  witness row `[1.5, -0.5, 0.0, ...]` sums to exactly 1.0, so the sum check at `:314` does not catch
  it, the numeric type check at `:305` does not, and the row-length check at `:301` does not. That
  line is the only thing that refuses it. Sound.
- `postflop-unplayable-size-imports`, `postflop_artifact.py:148`. `check_size_is_playable` has one
  caller (`:404`) and no sibling checks the `bet_sizes_bb` values beyond "is a number" (`:396-398`)
  and "one per sized action" (`:400`). The witness keeps the menu length, so the arity check does not
  cover for it. Sound.
- `postflop-report-spot-count-drifts`, `generate_postflop_betting_report.py:814`. The mutated
  `len(cells) + 1` is compared at `:816` against an independently derived `in_index`, so it does go
  red, and today it goes red on 1 against 0. Bites, but the check it routes through is weaker than
  its name - see the non-blocker above.

## Numbers I recomputed

All of these hold. Method beside each; none was read out of `backlog.yml`, a report or another
phase's plan.

- `data/artifacts` holds 5,197,325 bytes and the 20 MiB cap leaves 15,774,195 - summed with
  `Path.rglob` and `20*1024*1024`, matching report lines 253-256.
- Class census: 455 + 1,014 + 286 = 1,755 classes over 8,788 + 12,168 + 1,144 = 22,100 boards; mean
  orbits 19.3143, 12.000, 4.000; shares 39.76%, 55.06%, 5.18%; 455 x 24 = 10,920 overstates 8,788 by
  24.26%. Brute-forced over `combinations(deck, 3)` through `canonical_board`.
- Corpus: 499 hands, 259 flop-reaching, 20 + 24 + 215 + 0 = 259 with shares 7.72% / 9.27% / 83.01%;
  409 opens with 405 in band (99.02%) and 87 3-bets with 41 in band (47.13%). Called
  `measure_corpus` directly.
- Pot-odds rule fires 12 of 12. Called `_pot_odds_rate` directly.
- Decision 6's 1,286,792 hero-combo classes and mean 733 per flop reproduce exactly (733.2148) under
  the board-stabiliser collapse. This is the figure the first blocker turns on.
- The four committed range blocks in report lines 273-284 match decision 12's quoted weights
  digit-for-digit, and the dropped-class lists are exactly the classes under 0.01 in each.
- `0.33 * 100` is exactly `33.0` in binary floating point, so the percent/fraction conversion at
  `postflop_committed.py:237` does not trip `render_size_bb`'s hundredth-precision refusal. I
  checked this because that path would have raised an uncaught `ValueError` out of the strategy
  rather than refusing.

## Checked and clean

- `verification/freeze.lock` is intact: `freeze_tests.py --check` reports 50 files, no drift, after
  three re-freezes.
- `postflop_action_order` (`positions.py:70`) is a rotation of `table_positions` beginning one seat
  past `BTN`, not a re-derivation from seating order, and the heads-up case it warns about comes out
  right.
- The board canonicaliser itself is sound: `canonical_board` is invariant under all 24 suit
  permutations on every board I tested, and `board_suit_map` always carries the board to it. The
  defect is confined to the hand.
- `DECISION_AUDIT_SCHEMA_VERSION` 3 to 4 with a refusal at `contract.py:458`, and
  `tests/test_table_state.py:197` re-pinned to 4.
- The `_effective_depth_bb` walk (`postflop_betting.py:262`) reads starting stacks off `seat_states`
  rather than `current_bet - to_call`, which is the reading `to_call`'s cap broke.
- The report's own bans hold in the committed text: no single accuracy figure, no EV or chips-won
  figure, no determinism tolerance, every exploitability line carries "menu", every rainbow cost row
  reads `scaled`, and all 16 refusal codes appear once each and are labelled `vacuous` at zero.
