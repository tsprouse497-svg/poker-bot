# Phase 13, stage 4 review: the tests

Independent read-only reviewer, spawned by the coordinator. I wrote none of the tests under
review and I have edited nothing except this file.

Diff reviewed: `git diff bf05ca43ed3f894f85c58008232cfa90223405b6`, eleven paths. Two new test
files (`tests/test_table_state.py`, 45 tests; `tests/test_table_state_strategy.py`, 19 tests),
five migrated frozen test files, `tests/test_postflop_fallback.py` split with
`tests/test_postflop_fallback_components.py` as its companion, plus `verification/mutations.yml`,
`scripts/run_verify.py`, `CURRENT_TASK.yml` and `verification/loop_runs/13.yml`.

The question the driver printed, which is the brief:

> Would each test fail against a plausible wrong implementation, and does it assert on real
> behaviour rather than on state rebuilt from the code under test? Stage 5 freezes these, so a
> weak test is preserved perfectly.

Read: `docs/phase_contracts/PHASE_13_TABLE_STATE.md`;
`reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`, all sixteen items;
`docs/exec_plans/active/PHASE_13_TABLE_STATE.md`, including the four coordinator rulings and the
stage 6 builder specification; `src/poker_training_bot/strategy/contract.py`;
`src/poker_training_bot/strategy/preflop_chart.py`;
`src/poker_training_bot/solver_artifacts/lookup.py` and `positions.py`;
`data/artifacts/preflop/six_max_nl25_100bb.json` and its sizing table;
`verification/mutations.yml`; `scripts/check_gate_bite.py`; the five `phase: "13"` and four
neighbouring entries in `backlog.yml`.

Ran read-only: `uv run python -m pytest tests/test_table_state.py
tests/test_table_state_strategy.py -q` (64 failed, 0 errors, all assertion reds, no collection
error), `uv run ruff check tests/` (clean), `uv run python scripts/check_repo_consistency.py`
(clean), `wc -l` on the touched test files, and a standalone re-run of the engine sweep in
`_engine_shapes()` to enumerate the four postflop shapes. I did not run the gate or any
generator.

## Blocker

- **[resolved] `tests/test_table_state.py:616-647` can never pass.**
  `test_a_short_all_in_caller_and_a_full_caller_do_not_serialize_alike` builds both queries with
  `stacks=((0, 9950), (1, 9900), (2, 9700))` and `seat_states` carrying four entries including
  `seat_state(3, 300, ...)`. The same file's `test_a_contribution_entry_for_a_seat_that_is_not_at
  _the_table_is_rejected` at `tests/test_table_state.py:220-229` requires exactly that shape to
  raise `ValueError`, so both constructions raise before either `to_payload()` call is reached
  and the test errors whatever stage 6 builds. It is red today for the same reason every other
  test in the file is red, which is how it got here.
  This is not cosmetic: it is the only test in the phase that pins the contract's Phase 12
  handoff at `docs/phase_contracts/PHASE_13_TABLE_STATE.md:218-220` ("a call entry carries no
  record of being all-in for less") and the only behavioural use of decision 14's `all_in`
  marker anywhere. Frozen as written, that criterion has no test at all.
  Must change: add `(3, 9700)` to `stacks` in both queries. The stated `pot=750` already
  reconciles against `50 + 100 + 300 + 300`, so nothing else moves.

- **[resolved] Nothing in the repo can tell hero's contribution being read from a wrong implementation that
  subtracts, so the phase's headline criterion is unpinned and one canary is decorative.**
  `docs/phase_contracts/PHASE_13_TABLE_STATE.md:90-91` requires that hero's contribution "is read
  from the new field and never re-derived by subtraction", and
  `verification/mutations.yml` canary `hero-depth-is-derived-by-subtraction-again` replaces
  `hero_start = stacks[query.seat] + hero.street_bet` with
  `stacks[query.seat] + (query.current_bet - query.to_call)` and lists `pytest_table_state` and
  `pytest` in `must_fail`.
  In every query any frozen test builds, those two expressions are equal. I checked each builder:
  `tests/test_table_state_strategy.py:128` sets `to_call = min(max(current_bet - paid[hero], 0),
  hero_stack)` and the cap never binds at any fixture in that file; `tests/test_full_table_preflop
  .py:133` is the same shape and never binds; `tests/test_strategy_contract.py:44-56` and
  `:71-105` both satisfy the identity (2150 = 3500 - 1350); `tests/test_engine_fidelity.py:79-99`
  and its overrides at `:527-556` all satisfy it; `tests/test_spot_vocabulary_downstream.py:322-
  348` satisfies it; `tests/test_postflop_fallback.py:203-227` is postflop and never reaches
  `_table_depth_bb`.
  The one fixture that would break the identity, `_capped_hero_query` at
  `tests/test_table_state.py:451-472` (hero holds 150, put in 100, level 300, `to_call` capped at
  150), is never handed to `PreflopChartStrategy` or to `DecisionAuditRecord`. The three tests
  that use it, `tests/test_table_state.py:474-505`, recompute both depths inside the test body
  from query fields, so they assert an arithmetic identity rather than anything the code does.
  `test_the_depth_the_contribution_gives_is_25bb_and_the_subtraction_gives_30bb` at `:485-494` is
  the clearest case: it passes against an implementation that has never been written.
  The arithmetic in that fixture is correct and matches the decision list at
  `reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md:65-73`. The defect is that
  nothing measures the code with it.
  Must change: drive a capped hero through `PreflopChartStrategy` so the two readings produce
  different outcomes. Note when building it that a capped hero cannot exist at a flat table
  (`current_bet` would have to exceed hero's starting stack, which means some seat started
  deeper), so the reachable pin is hero's own raggedness, which `_table_depth_bb` evaluates
  before any villain comparison: choose numbers where the true starting stack is not a whole big
  blind and the subtracted one is, and assert `preflop-chart:stack-depth-not-a-whole-big-blind`.
  Until such a test exists the canary should not be committed as-is, because `check_gate_bite`
  requires every command in `must_fail` to fail.

- **[resolved] The chart-side all-in ceiling, decision 11 and
  `docs/phase_contracts/PHASE_13_TABLE_STATE.md:111-114`, has no test that can fail.**
  The change is to `PreflopChartStrategy._raise_amount`, `src/poker_training_bot/strategy/
  preflop_chart.py:252`, which today caps at `query.street_bet + stacks[query.seat]` and must
  move to hero's own recorded contribution plus the stack. The contract says in as many words
  "a test pins that they agree on a hero who has already invested this street".
  The test that claims to be it, `test_the_two_ceilings_differ_by_exactly_the_price_to_call` at
  `tests/test_table_state.py:531-538`, computes `chart_ceiling` and `audit_ceiling` in the test
  body from `query.current_bet`, `query.to_call` and `hero.street_bet` and asserts their
  difference. It never calls `_raise_amount` or `decide`. Its neighbours at `:514-529` exercise
  only `DecisionAuditRecord`, which is the half that already had the correct arithmetic before
  this phase. A grep across `tests/` finds no assertion on a chart raise amount other than
  `tests/test_full_table_preflop.py:354`, which pins the sizing table value and not the cap.
  There is a real obstacle here and the note should record it rather than pretend otherwise: at
  the only committed depth, `d100`, the largest sizing is 28.5bb against a hero stack near 100bb,
  so the cap never binds through `decide` and the two formulas cannot be separated that way. The
  honest fixes are a direct test of `_raise_amount` against a `PreflopChartStrategy` constructed
  with a sizing table whose amount exceeds hero's true target, or a recorded statement in the
  ExecPlan that the criterion is unpinnable and why. Freezing an in-test identity that reads like
  a pin is the outcome to avoid.

- **[resolved] The ante fixtures in `tests/test_table_state_strategy.py` put the ante where the coordinator
  ruled it must not go, and make hero owe less than he owes.**
  The ExecPlan ruling at `docs/exec_plans/active/PHASE_13_TABLE_STATE.md:144-151` is explicit:
  an ante is dead money, it lives in `committed_total` only, and "putting it in the street figure
  would make an anted seat owe less to call than an unanted one at the same level".
  `tests/test_table_state_strategy.py:73-95` sets `street_bet=contributed` and
  `committed_total=contributed` from one argument, and the two ante fixtures at `:399-406` and
  `:559-563` pass the ante through it. The consequence is at `:128`: hero's `to_call` computes as
  `100 - 10 = 90`. Frozen, the repo's only strategy-level ante fixtures encode an ante buying
  hero ten chips off the price, which is the exact error the ruling exists to prevent.
  The migration worker got this right in the other file:
  `tests/test_full_table_preflop.py:126-134` keeps the ante out of `street_bet` and out of
  `to_call`, and `tests/test_table_state.py:312-347` asserts the ruled rule directly. So stage 5
  would freeze two incompatible ante models authored in parallel.
  It is also a live trap for stage 6. Under the ruled ante signal, `committed_total - street_bet`
  uniform across seats, both `tests/test_table_state_strategy.py:389-406` and `:550-587` see zero
  dead money on every seat and go red; they pass only if the builder classifies from the
  blinds-and-actions reconstruction instead. The ExecPlan tells the builder to do the former and
  asserts at `:157` that "the strategy-side worker reached the same uniformity reading
  independently", which is not the case: that worker's uniformity is over unexplained
  contributions, not over the street/total gap.
  Must change: put the ante in `committed_total` alone in both fixtures and leave `to_call` at
  the full 100, and reconcile the two ante signals in one place before the freeze.

- **[resolved] The `three_bet_table` fixture's worked numbers are wrong, in the fixture two criteria rest
  on.** `tests/test_table_state_strategy.py:186-204` says "hero holds 75bb, the cutoff holds
  20bb, and the blinds hold 99.5bb and 99bb", and `:294-301` says "Hero holds 7,500 chips".
  With `BIG_BLIND = 100` and `FULL_STACK = 10000`, hero contributes `OPEN_TO = 250` and holds
  9,750, which is 97.5bb; the cutoff contributes `THREE_BET_TO = 800` and holds 9,200, which is
  92bb. The two blind figures are right, which is what makes the other two read as checked.
  The assertions themselves still bite, because held-chip depth for hero is 9,750 and not a whole
  big blind, so a naive implementation still refuses. But this is the fixture the audit packet is
  meant to quote as the asymmetric-table evidence, and phase 12's stage-4 review blocked on a
  number that was simply wrong for the same reason. Must change: correct both docstrings to
  97.5bb and 92bb.

- **[resolved] Two canaries require `generate_table_state_report` to exit non-zero, and nothing tells the
  builder that.** `scripts/check_gate_bite.py:106-112` runs every entry in a mutation's
  `must_fail` and reports a survival if any of them succeeds. Canaries
  `hero-depth-is-derived-by-subtraction-again` and `an-absorbed-straddle-goes-unseen` in
  `verification/mutations.yml` both list `generate_table_state_report` alongside the pytest
  commands. A report generator that renders a number and writes a file exits 0 whatever the
  number says, so both canaries fail at stage 7 unless `scripts/generate_table_state_report.py`
  self-checks its own worked examples and returns non-zero when they move.
  The ExecPlan section "What stage 4 specified for the stage 6 builder"
  (`docs/exec_plans/active/PHASE_13_TABLE_STATE.md:182-199`) names the five `find` strings and
  the docstring phrase, and says nothing about this. Must change: either add the requirement to
  that section in the words the builder needs, or drop `generate_table_state_report` from the two
  `must_fail` lists.


### What the coordinator changed, blocker by blocker

All six are fixed in the tests, and one of them changed the ExecPlan as well. Every fix was made
by a worker reading this note as its specification; the note's own arithmetic and file:line
citations are what made that possible.

1. The short-all-in-caller fixture now seats the fourth player in `stacks` as well as in
   `seat_states`, with the button at seat 3 so there is a caller sitting behind the raiser for a
   short all-in to happen to. It asserts what it always claimed: one identical `SeatAction`
   record in both tables, and the marker as the only thing left saying which is which.
2. A test now drives a capped hero through `PreflopChartStrategy` and asserts the refusal code,
   rather than computing both derivations in the test body. The reviewer was right that a flat
   table cannot show the difference, since a capped hero there has `current_bet - to_call`
   exactly equal to `street_bet`. The way through is the ragged-depth branch, which fires first:
   a hero holding 145 having put in 100 truly started with 245, which is not a whole big blind,
   while the subtraction gives a clean 300 and sails past. The canary is no longer decorative.
3. The chart-side ceiling is pinned through the public path in the strategy file, on the only
   hero the two ceilings disagree about. The query-side file keeps the audit half and says in its
   class docstring where the other half lives.
4. The ante moved to `committed_total` alone, so hero owes the same at an anted table as at an
   unanted one. That is the coordinator's ruling and it is now what the fixtures build; the
   module docstring states the gap between the two figures as the signal the detector reads.
5. The `three_bet_table` docstrings are corrected to the arithmetic, 97.5bb and 92bb, rather than
   the arithmetic to the docstrings.
6. Both canaries keep `generate_table_state_report` in `must_fail` rather than dropping it, which
   would have made them weaker. Their descriptions now say the report validates its own figures
   and exits non-zero when they do not hold, and the ExecPlan carries it as a named requirement
   for the stage 6 builder, in the shape phase 12 set with `_validate_census`.

Counts after the fixes: 46 and 20 tests, 700 and 693 lines, ruff clean, all 66 still failing for
the right reason.

## Non-blocker

- A cluster of tests assert values the test itself supplied or arithmetic the test itself
  performed, and cannot fail against any implementation: `tests/test_table_state.py:254-260`
  (a folded seat's own `folded` and `committed_total`), `:496-505` (starting stacks summed in the
  test), `:519-524`, `:531-538`, and `:649-664`, where `broke.all_in is False` restates a
  constructor argument on a frozen dataclass. They read well as documentation and I am not asking
  for their removal, but they should not be counted as coverage of decisions 6, 11 or 14 in the
  audit packet. The behavioural pins for those decisions are the strategy file's, and for
  decision 11 there is none (see the blocker above).
- `tests/test_table_state.py:262-268`, `test_dropping_a_folded_seat_is_how_a_pot_stops_
  reconciling`, says "Both halves fail: the seat is missing an entry and the pot no longer adds
  up." Only the pot half fails. The fixture drops seat 0 from `stacks` and from `seat_states`
  together, so the two seat sets still agree and only the `pot` rule bites. The bare
  `pytest.raises(ValueError)` will pass either way, so the docstring is the only thing that is
  wrong, but it is the docstring a reader trusts to know which rule is under test.
- `tests/test_table_state.py:188-192` pins the per-seat field names as a literal list rather than
  against `PlayerState`. Decision 2's whole argument is "the engine's own names", and this test
  goes green if the engine renames one of them tomorrow. Comparing against
  `dataclasses.fields(PlayerState)` minus the three fields the query does not carry would make
  the one-vocabulary claim self-enforcing.
- `tests/test_table_state_strategy.py:550-587`. The 1,850-chip straddle fixture at `:433-477`
  states plainly that its betting order is not one a straddled street literally produces, and
  that the claim under test is the arithmetic. The button-straddle fixture in this test has the
  same irregularity (a button straddle puts the small blind first to act and the button last,
  yet the lojack has raised while both blinds are still sitting on their posts) and says nothing.
  The arithmetic is right: over a 200 straddle a raise to 600 leaves a minimum of 1,000, against
  1,100 unstraddled, and the two bound figures quoted, 210 against 150 and 950 against 750, both
  reproduce against `_blind_structure_is_representable` at
  `src/poker_training_bot/strategy/preflop_chart.py:164-172`. One added sentence, matching the
  other fixture's, is all that is missing.
- `test_every_pot_the_deleted_arithmetic_bound_refused_still_refuses` proves two pots where the
  contract at `docs/phase_contracts/PHASE_13_TABLE_STATE.md:167-169` says the replacement must
  refuse "every pot the bound refuses". Two worked examples is the practical reading and I am not
  asking for more, but the audit packet should claim what the test proves rather than what its
  name says.
- Nothing validates `to_call` against `current_bet` and hero's own `street_bet`, so a producer
  can supply a price that contradicts the level and the seat record and no rule notices. This is
  the same class of producer defect decision 3 closes for the pot, and it is also the reason the
  subtraction identity is untestable. Deliberately out of scope as far as I can tell (the
  contract asks only for the cap), but the phase's own thesis is that a reconstructable field is
  a field a consumer guesses behind, and this is one.
- `tests/test_engine_fidelity.py` is at exactly 700 lines and `tests/test_full_table_preflop.py`
  at 699, against the 700-line cap, with `tests/**` leaving scope at stage 5. Neither can take a
  line at stage 6 without a scope change and a split. Worth knowing before the freeze rather than
  during a repair.

Migration and split, checked and clean otherwise. I diffed the behavioural rewrites against what
they asserted before and found no weakened assertion: the all-in ceiling tests at
`tests/test_engine_fidelity.py:518-556` keep both bounds and both controls; the docstring test at
`:449-458` gained an assertion rather than losing one; `Shape.hero_is_short` at
`tests/test_postflop_fallback.py:81-86` is correctly restated as `0 < hero_stack == to_call`,
which I confirmed is still satisfied by the engine's `('fold', 'call')` shape (current bet 20,
hero street bet 0, stack 10), so Phase 06's short hero survives rather than being quietly
dropped. The three rebuilt fixtures each reconcile and each is legal poker:
`_uncovered_spot_query` at `tests/test_strategy_contract.py:70-105` is a legal 250/800/2150/3500
ladder summing to its own pot, `uncovered_preflop_query` is now flat at 40bb rather than leaving
4,000 in front of a posted blind, and the postflop enumeration's orphan 100 chips are attributed
to villain's earlier street per decision 9. The `test_postflop_fallback.py` split loses nothing:
`TestOutcomeCodes`, all eight `UNBEATABLE_EXAMPLES` plus the malformed-board test, and all seven
`TestComposite` tests moved intact, the harness is imported rather than copied, and
`pytest_postflop_fallback` in `scripts/run_verify.py` now names both files.

The other four canaries bite, and I name the test for each. `the-pot-stops-having-to-reconcile`
fails `tests/test_table_state.py:272-287`. `a-capped-hero-may-raise-again` fails
`tests/test_table_state.py:394-413` and `:415-426`. `a-folded-seat-makes-the-table-ragged` fails
`tests/test_table_state_strategy.py:307-339`. `an-absorbed-straddle-goes-unseen` fails
`tests/test_table_state_strategy.py:433-477`, which falls through to a flat 100bb table and an
uncovered `t6/d100/BTN/CO:raise@6` lookup, and `:550-587`, whose non-uniform unexplained money
would then take the residual code instead of the straddle code.

## Alignment

- The capped hero the phase is built around cannot be constructed at a flat table, because
  `to_call` exceeding what hero holds requires the bet level to exceed hero's starting stack,
  which requires a deeper seat, which decision 6 now refuses. So the capped population and the
  refusing population are the same population, and the arithmetic this phase corrects is only
  ever exercised on tables the chart declines to answer. That is drift this stage cannot fix and
  it belongs to the existing `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` (`backlog.yml:144`), whose
  reason should gain a sentence saying so: whoever produces real table state will be the first
  reader for whom `_table_depth_bb`'s capped branch and decision 11's chart ceiling do anything
  observable.
- A new backlog id is needed for the stage-4 failure mode this review found twice. It should say:
  at stage 4 every test in a new file is red, so a test that is red because the code is missing
  and a test that is red because it can never pass (a fixture the file's own validation rules
  reject, as at `tests/test_table_state.py:616`) are indistinguishable to `loop_stage.py`,
  to the driver, and to a reader of the failure list. `scripts/freeze_tests.py` then preserves it
  and `check_gate_bite` cannot see it, because a mutation only proves something fails. A cheap
  partial check exists: at stage 4, assert that no test fails inside a fixture or helper rather
  than at an `assert` or a `pytest.raises` boundary. File it next to
  `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` (`backlog.yml:691`), which is the neighbouring
  item about a red nobody can read and stays open.
- A new backlog id is needed for test files sitting on the 700-line cap with `tests/**` frozen
  behind them, naming `tests/test_engine_fidelity.py` at 700 and
  `tests/test_full_table_preflop.py` at 699. The precedent to follow is
  `VOCABULARY-MEASURES-AT-ITS-LINE-CAP` (`backlog.yml:1078`), which records the same landmine for
  a source module: it passes today and the next line fails the gate, in whatever task happens to
  need it, and for a frozen test file that task also has to reopen `tests/**`. This phase already
  paid the cost once, splitting `tests/test_postflop_fallback.py` at stage 4 for exactly this
  reason.
