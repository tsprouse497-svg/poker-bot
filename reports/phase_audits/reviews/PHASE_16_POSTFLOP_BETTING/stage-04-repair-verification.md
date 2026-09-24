# Phase 16, stage 4: round-2 verification of the repair

Read-only. Reviewer wrote neither the tests nor the repair. Diff under review: `git diff b714120 HEAD`
in `poker-bot-worktrees/phase-16` (commit `23e9c8a`; `edc4486` is unrelated backlog work and is
ignored). The two notes being verified are `stage-04-tests-mechanical.md` and
`stage-04-tests-poker.md`.

Method. Every figure below was recomputed in this worktree. Fixtures were constructed against the
real `StrategyQuery.__post_init__` by stubbing only the modules stage 6 has not written and widening
`SeatAction` to accept `bet` with an amount, which is what the contract requires stage 6 to do; the
equity counts were taken from the repo's own `evaluate_best`; the migration sweep was re-grepped; the
mixture tolerance was integrated exactly rather than approximated. No mutation tooling, no
`run_verify.py`, no `check_gate_bite`, no `git checkout`. No file outside this note was touched.

| # | Blocker | Verdict | Reason |
| --- | --- | --- | --- |
| 1 | Three report tests asserted nothing | **FIXED** | Each test now decides its property over the report text beside the validator call, and all 13 negative controls in `TestThisFileSOwnPredicatesCanFail` construct a violating report and require `False`. They pass today. |
| 2 | Weight-bounds canary could not bite | **FIXED** | `[1.5, -0.5, 0.0...]` sums to exactly 1.0 in binary floating point, so the sum check cannot refuse it; the sibling test was correctly flipped to `[1.0] * len(row)`, which is in-bounds and sums to `len(row)`. The two checks are now isolated. |
| 3 | Non-canonical-board test tested the wrong thing | **FIXED** | A suit permutation is a bijection, so it never duplicates a card and never leaves the class; a moving permutation exists for all three committed textures, and its image cannot be the canonical representative because the committed board already is one. |
| 4 | Migration sweep was unstated | **FIXED** | All five numbers re-measured and correct: 50 files, 23 mentioning the shape, 3 of them this phase's own, 20 pre-existing, 3 migrated, 17 unchanged. No 18th file should have been migrated. |
| 5 | Pot-odds negative control could never pass | **FIXED** | Recounted with `evaluate_best`: `Jd8d` is 180/9/801 = 18.6364%, `AhAd` is 884/1/105 = 89.3434%, 272 of 1,081 holdings under 25%, median 48.3838%. Every docstring figure holds. |
| 6 | Fixtures the validator rejects | **PARTIALLY** | Every fixture now builds - confirmed by constructing all 63 of them. But the convention it was repaired into describes a table that cannot exist: hero sits down with 10,050 chips against villain's 10,000, and `len(stacks) == 2` derives `t2`, not the `t6` the fixture's own docstring claims. See B1. |
| 7 | Nothing required a committed mixture | **FIXED** | Exact binomial: a correct implementation fails with probability 4.84e-05 at the worst weight, and the draw is seeded on the hand id so it is deterministic rather than flaky. Argmax fails the distinct-action test at every weight and the frequency test whenever the dominant weight is under 0.90. |
| 8 | Nothing pinned that a three-handed flop refuses | **FIXED** | Three live seats, a refusal required, the code required to be in the phase's own closed vocabulary, and a heads-up positive control beside it. The contract names no dedicated multiway code, so membership is the right assertion. Its positive control inherits B1. |

## Blocker

**B1. Every heads-up fixture in the phase describes a table that cannot be dealt, and the repair
spread that convention to all of them rather than fixing it.**

`tests/test_postflop_betting.py:74-110` (`query`), `:112-126` (`facing_a_bet`), `:510-540` (`river`),
`tests/test_postflop_query_recording.py:236-263` (`covered_flop`) and `tests/test_postflop_key.py:95`
(`flop_query`) all list **two** seats and park the folded small blind's dead 0.5bb on the big blind's
`committed_total`. `query`'s own docstring at `:80-84` states the convention outright: "a folded seat
is not listed, so the dead half-blind rides on the big blind's `committed_total` while its `stack`
shows only what it put in: seat 1 is 300 committed against a stack of 9750."

Two things follow, both measured:

- [resolved] **The table is not flat and hero is not at 100bb.** `table_state/measures.py:113` defines what a
  seat sat down with as `stacks[seat] + committed_total`. For every fixture above that is 9750 + 250
  = **10,000** for seat 0 and 9750 + 300 = **10,050** for seat 1. Hero sat down with 100.5bb against
  a villain at 100bb. Run through the repo's one existing depth walk,
  `PreflopChartStrategy._table_depth_bb`, every one of them returns
  `preflop-chart:stack-depth-not-a-whole-big-blind`; under the `seat_start` reading the answer is
  `a-live-seat-is-shorter-than-hero` instead. There is no depth derivation that reads this table as a
  flat 100bb one, because it is not one.
- [resolved] **The table is not six-handed.** `PreflopChartStrategy._chart_query` at
  `strategy/preflop_chart.py:296-306` takes `table_size=len(query.stacks)`. Derived from these
  fixtures it gives `table_size=2`; `three_handed()` gives 3. The phase's own covered key is
  `A_COVERED_PREFLOP_KEY = "t6/d100/BB/BTN:raise@2.5"` at `tests/test_postflop_key.py:55`, and the
  contract writes every example key as `t6`. The fixtures assert `t6` in prose and derive `t2` from
  the only producer the repo has.

The producer these queries are supposed to imitate does not do this. Replaying
`tests/test_postflop_query_recording.py`'s own simulator profiles and logging every postflop query it
builds, the simulator lists **all six seats** in `stacks` and `seat_states`, with folded seats
carrying their own chips and `folded=True` - for example a 350-chip flop pot as
`((0,0,100),(1,0,100),(2,0,0),(3,0,50),(4,0,100),(5,0,0))`, where seat 3 is the folded small blind
holding its own 50. Under that shape the pot reconciles, every seat sat down with 10,000, and
`len(stacks)` is 6. `StrategyQuery.__post_init__`'s own error text points at the same fix - "dropping
a folded seat is how that stops" - and `SeatState.folded` exists for exactly this.

Why it is stage-holding rather than a note for stage 6. These are the phase's *positive* controls.
"It bets", "it raises", "the amounts are legal", "a real table's rounding is still answered", "the
same board heads-up is answered" and the whole of `TestThePotOddsRiverCall` all require a
`StrategyDecision` from a query whose table size and stack depth contradict the cell it must hit. A
stage 6 that derives either quantity correctly reds every one of them; a stage 6 that makes them pass
has been forced to launder the discrepancy. That is the same shape as the original B2 - a test that
cannot run against a correct implementation - one level below the pot check the repair fixed, and
stage 5 freezes it.

It also lands on blocker 8. `three_handed()` is the only fixture in the phase that *is* a flat 100bb
table (all three seats at 10,000). So the multiway test refuses correctly while the heads-up positive
control beside it is the broken one, which is the worst arrangement of the two.

The repair is mechanical and touches no claim: list every seat in `stacks` and `seat_states`, mark
the folded ones `folded=True`, and give the small blind its own 50 instead of lending it to the big
blind. Pots, prices and stacks are otherwise unchanged.

**B2. Decision 14 is classed `runtime-reversible`, and this decision list's own definition makes it
`frozen-into-data`.**

`reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:17-30` quotes `docs/LOOP.md`
and then states the rule in terms: "The words 'or fixture' are load-bearing... a behaviour default
that a contract requires a frozen test to pin is a fixture, so it carries this class even in a phase
that commits no data." Decision 14's value of 0.01 is pinned by a frozen test -
`test_the_tolerance_is_published_as_a_named_constant` at
`tests/test_postflop_query_recording.py:566` asserts `MENU_FRACTION_TOLERANCE == 0.01` - and stage 5
freezes it. Decision 14's own closing paragraph argues the opposite: "The frozen test pins the
default so that a later change is a deliberate edit rather than a drift, which is what the class asks
for and not what makes it the other one." That is the reading the same file says it had already
corrected, under `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`.

The contrast with the list's other `runtime-reversible` item is the test of it. Decision 5's
pot-odds flag is exercised through explicit `True` and `False` and no test pins what `from_repo()`
defaults to, so nothing freezes it - genuinely reversible. Decision 14's number is frozen. Under
`AGENTS.md` only `frozen-into-data` blocks on a human, so the class is what decides whether Taylor
is asked, and this one was answered by the loop on its own.

The arithmetic itself is right and is not the problem. Recomputed: floor `|180/550 - 0.33| =
0.0027273`; structural ceiling `(0.75 - 0.33)/2 = 0.21`; binding ceiling `|275/550 - 0.33| = 0.17`,
and 275/550 is exactly 0.50; `0.01 / 0.0027273 = 3.667` and `0.17 / 0.01 = 17`. The chip bands
(176-187 and 407-418 on a 550 pot) and `181.5 -> 182` all check out, and the 297-chip midpoint at
54.0% is 0.21 from both entries, which is what makes 0.17 bind. The fix here is the class and the
stop, not the number.

[resolved] 2026-09-24 by MAINT-38: every bullet above that lacked a marker was audited by an independent lane and marked where the fix or ruling is shown, finding by finding, in `reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`.

## Non-blocker

**N1. The vacuity predicate is vacuous if `REFUSAL_CODES` is empty, and only a test in another file
stops that.** `vacuity_labels_match_the_counts` at `tests/test_postflop_betting_report.py:170`
returns `True` for an empty code list (`sorted({}) == sorted(())`, then an empty loop), and the
fixture at `:61-71` accepts `()` because `getattr(..., None)` only rejects a missing name. What closes
it is `test_the_refusal_vocabulary_is_a_closed_list` at `tests/test_postflop_betting.py:340`, which
requires two named codes to be in it. Both run under `pytest_postflop_betting`, so the hole is
covered - but it is covered by a sibling rather than by the predicate, which is the shape this
blocker was about. One line in the fixture (`assert found`) would close it locally.

**N2. `cost_rows` claims more of the report than the cost model.** `tests/test_postflop_betting_report.py:124`
takes every line anywhere in the report that holds a texture word and any digit, and
`every_cost_row_declares_measured_or_scaled` then requires each to carry `measured` or `scaled`, with
rainbow rows required to carry `scaled` and forbidden `measured`. A per-cell exploitability line that
happens to name its board's texture - "Kc7d2h, rainbow, exploitability 0.42% ... menu" - is caught by
that net and reds. The failure direction is safe (stage 6 sees it and adds a word), but it couples
the report's prose to a cost-model rule, and it is frozen.

**N3. The sweep's sixth number is off.** The block comment at
`tests/test_postflop_query_recording.py:35` says "Four of the six files calling `to_json_line` never
assert on its bytes" and then names three. Grepped: six files actually call it - `test_full_table_preflop.py:611`,
`test_postflop_fallback.py:687`, `test_simulator.py:451`, `test_strategy_contract.py`, `test_table_state.py`
and this phase's own `test_postflop_key.py:206` - and three of the six do assert on the bytes, the two
migrated ones plus `test_postflop_key.py`. So it is three of six, not four, and the sixth caller is
one of this phase's own files rather than a pre-existing one. The five headline numbers (50 / 23 / 20
/ 3 / 17) are all correct and the conclusion - the migration was complete at three - holds.

**N4. Decision 14 does not say which pot the fraction is over, and the query carries the wrong one.**
The rule is written `bet_chips / pot_chips`. `facing_a_bet()` has `pot=730`, which already includes
the 180 faced bet, so reading the query's own `pot` field gives 24.66% and refuses; the intended
32.73% needs the pot *before* the bet, 550, which the test supplies as a literal
(`SINGLE_RAISED_POT_CHIPS`) and a live query has to derive by subtracting the street bets. Derivable,
but unstated in the decision and unpinned by any test.

**N5. A wrong poker sentence in a frozen docstring.** `tests/test_postflop_query_recording.py:398`
says of the three-handed fixture "the big blind is first to act postflop". Hero there is seat 2 with
`button_seat=0`, so seat 1 is the small blind and acts first on the flop; the fixture gives hero an
empty `postflop_actions` while sitting second in order. The three-handed claim the test makes is
unaffected - it is a refusal either way - but the fixture is a flop where the first actor's check was
never recorded, in the file whose whole subject is recording postflop history.

**N6. `mixed_spot`'s 0.05 threshold admits a cell where the frequency test cannot see argmax.**
`tests/test_postflop_query_recording.py:299` accepts any cell with two actions at weight >= 0.05, so
a 0.95/0.05 cell qualifies; argmax there observes 1.00 against 0.95 and 0.00 against 0.05, both
inside the 0.10 tolerance. The distinct-action test at `:310` is what actually excludes argmax in that
case, and it does (0.95^400 is about 1e-9). Worth knowing that the two tests carry different halves
of the claim depending on which spot `committed_spot_queries()` returns first.

## Alignment

- `SEAT-STATE-MARKERS-AGREE-WITH-NOTHING` (existing, `backlog.yml:1784`). B1 is this entry from the
  test side and the entry does not name the shape. The entry is about a producer setting `folded`
  or `all_in` wrongly with nothing to catch it; B1 is a whole phase's fixtures omitting folded seats
  entirely and redistributing their chips, which no validator objects to because the pot still
  reconciles. Whatever cross-validation closes the entry - markers against `stacks`, against the
  recorded history - would have caught this at authoring time.
- `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` (existing, `backlog.yml:731`). B2 is this entry
  recurring after the entry recorded its own resolution. The resolution lives in prose inside one
  phase's decision list; nothing mechanical reads it, so the next decision list re-derives the class
  by argument and lands where phase 16 landed. `scripts/loop_stage.py` checks that a class is
  declared, not that it is the right one, and "is this default pinned by a frozen test" is a
  question a script can answer.
- `A-FIXTURE-IN-A-TEST-NEED-NOT-BE-A-TABLE-THE-SIMULATOR-COULD-PRODUCE` (**proposed**). The general
  form of B1, which is not this phase's to fix. Hand-built `StrategyQuery` fixtures are checked
  against `__post_init__` and nothing else, and `__post_init__` deliberately checks only what can be
  checked locally - the pot against the listed seats. Nothing anywhere compares a hand-built query
  against the shape the simulator actually emits, so a fixture can carry a seat count, a stack
  distribution or a dead-money placement no hand reaches, and every test built on it passes while
  proving something about a table that does not exist.
  `SOLVED-PRICE-FIXTURE-HELPER-DUPLICATED-ACROSS-TEST-FILES` (`backlog.yml:2908`) is the neighbouring
  entry and covers duplication rather than fidelity. A shared builder that starts every seat at the
  same stack and derives `stacks` from the recorded actions would make this class of defect
  unwritable.
