# Phase 16 stage 4 review: the tests, before the freeze

Three independent read-only reviewers, none of whom wrote what they read. Two on the tests as
authored - one mechanical, one on the poker, neither having seen the other's note - and a third on
the repair, because the agent that fixes eight blockers is not the one to certify that the fixes are
real. Their notes are `stage-04-tests-mechanical.md`, `stage-04-tests-poker.md` and
`stage-04-repair-verification.md`; this file is the stage's record and does not replace them.

The driver's question for this stage: *would each test fail against a plausible wrong
implementation, and does it assert on real behaviour rather than on state rebuilt from the code
under test? Stage 5 freezes these, so a weak test is preserved perfectly.*

The diff under review: six new test files carrying the phase's own criteria, three frozen test files
of completed phases migrated to the new query shape, three mutation canaries, two command
registrations, and one new decision.

**Ten blockers across three rounds, every one re-measured by the coordinator before it was acted
on.** A reviewer's report is not evidence either, and two of the ten turned on a number - an equity
and a starting stack - that had to be recomputed rather than read.

## Blocker

- `[resolved]` **Three report tests asserted nothing.** `test_postflop_betting_report.py` at :195,
  :265 and :306 each did `assert owed(generator, "<validator>")(report) is True` for
  `exploitability_lines_are_qualified`, `cost_rows_declare_measured_or_scaled` and
  `vacuous_codes_are_labelled`. Each name occurred exactly once in the repo - its own call site -
  so a stage-6 `return True` passed all three, and they were guarding the three contract criteria a
  reader cannot eyeball. Each test now decides its property over the report text beside the
  validator, with thirteen controls that run and pass today.

- `[resolved]` **The weight-bounds canary could not bite.** Its witness set one entry of a summing
  row to 1.7, which broke the sum-to-one check beside it as well as the bound, so with the bounds
  check disabled the importer refused anyway and `postflop-weight-bounds-not-enforced` survived the
  command it names. `check_gate_bite` catches that at stage 7, which is after stage 5 freezes both
  `tests/**` and `verification/**`. The witness now replaces the whole row with one summing to
  exactly 1.0 outside the bounds, so that line alone can refuse it. The sibling
  `test_a_class_whose_weights_do_not_sum_to_one_is_refused` had the mirror defect, found by the
  repair lane rather than by either review: `[0.5] * len(row)` sums to exactly 1.0 on a two-action
  cell, so on such a cell nothing refused it.

- `[resolved]` **The non-canonical-board test did not test non-canonicality.** It rewrote the board
  to all spades, which changes the board's suit class rather than its dressing, duplicating the
  stored-key test above it; and on a monotone sample cell a correct canonicaliser could have
  rejected a valid file. It now permutes suits, which is a bijection and never leaves the class.

- `[resolved]` **The contract's migration sweep was unstated.** Re-run and recorded: 50 test files,
  23 mentioning the query shape, 3 of them this phase's own, 20 pre-existing in scope, 3 migrated,
  17 unchanged with a reason each. The verification pass re-ran it independently and agreed, and
  corrected one of the six supporting figures.

- `[resolved]` **The pot-odds negative control froze a false poker claim and could never pass.**
  `3c2d` pairs the deuce on `Kc7d2h9s4c` and has 43.54% equity against a 25.0% price - 548 beats,
  22 ties, 420 wins of 990, counted with the repo's own evaluator - while the test's own
  precondition asserted the equity was below the price. `Jd8d` replaces it at 18.64%, 180 wins, 9
  ties, 801 losses, recounted independently at each of three rounds.

- `[resolved]` **Two fixtures built a `StrategyQuery` the repo's own validator rejects**, masked
  only because the missing-module fixtures raised first. The river fixture failed with `pot 1650 is
  not the 1100 the seats put in`. The repair found three more: five fixtures over four conventions
  for what is in the pot, not the two reported.

- `[resolved]` **Nothing required the strategy to play a committed mixture.** `class_weights`,
  `mixture`, `collapse`, `rng` and `random` appeared zero times in the betting tests, so an argmax
  implementation that purifies every solved frequency passed all six files - as did "bet 33% with
  the whole range" and "ignore the weights". `PreflopChartStrategy` had already solved this and its
  own comment says "Not the highest weight". Now pinned by a seeded draw whose tolerance is derived
  rather than picked: a correct implementation fails at 4.84e-05, an argmax one outright.

- `[resolved]` **Nothing pinned that a three-handed flop refuses.** Only the report's wording was
  checked. The spot key has no player-count segment, so `t6/d100/SB/BTN:raise@2.5` is the same key
  whether the big blind folded or called, separated by pot arithmetic alone.

- `[resolved]` **The fixtures described a table that cannot be dealt.** Found in round 2 of the
  repair review, after two rounds had passed over the same lines. Every heads-up fixture listed two
  seats and parked the folded small blind's 50 chips on the big blind so the pot would reconcile.
  Measured off `query()`: `len(stacks)` 2 against a phase whose covered key is `t6`, and starting
  stacks of 10,000 and 10,050 against fixtures whose docstrings say 100bb. `PreflopChartStrategy`
  derives table size as `len(query.stacks)` and a starting stack as `stack + committed_total`, so a
  stage 6 doing either the way this repo already does it refuses **every positive control in the
  phase** - the tests that say the bot bets and raises. A frozen test that fails the correct
  implementation is the worst thing stage 5 can preserve. Every fixture now seats six, marks the
  folded, leaves the small blind its own dead chips, and starts everyone at 10,000. The lane found
  three more in passing: the button betting before hero had acted on a street where the big blind
  acts first, a keyword collision that would have raised `TypeError` on the first stage-6 run, and
  one wrong figure in the sweep. Filed as
  `A-FIXTURE-IN-A-TEST-NEED-NOT-BE-A-TABLE-THE-SIMULATOR-COULD-PRODUCE`.

- `[resolved]` **Decision 14 was filed `runtime-reversible` and it is not.** Its tolerance is pinned
  by a frozen test, and this repo's class definitions say `frozen-into-data` covers a choice written
  into "a committed artifact **or fixture** that later phases are then measured against".
  `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` resolves exactly that wording, and the paragraph
  recording it names this failure in advance: a phase reading the definitions loosely "would have
  called such a threshold reversible and never asked anyone". Reclassified, and the loop halted and
  asked. **Ruled by Taylor 2026-09-15: match within five points of pot.** The decision entry carries
  the options as they were put, the arithmetic recomputed against the ruled value, and what the
  chosen width costs.

## Non-blocker

- The orbit docstring at `test_postflop_key.py` said rainbow boards have a 24-element orbit,
  two-tone 12, monotone 4. False for paired and trips boards, and about to be frozen as a reference:
  brute-forced over all 22,100 boards, 169 of the 455 rainbow classes are not orbit-24. The
  histogram constant itself was right; only the explanation was wrong. The same error has a cost
  the mechanical pass did not carry - the contract tells stage 6 to scale every rainbow cost figure
  from "an exact orbit factor", and 455 x 24 overstates rainbow by 24.3% against a true mean of
  19.314 boards per class.
- `holding_counts` exists in a report script returning `(beats, ties, hero_label)`, where `beats`
  counts holdings that **beat** hero, and the new test unpacked the same name as `(wins, ties,
  losses)`. A stage-6 implementer lifting the existing function inverts the equity. Now pinned on
  the numbers - `(884, 1, 105)` for `AhAd` - so an inverted lift fails on the value rather than on
  the type.
- The vacuity predicate returned `True` for an empty `REFUSAL_CODES`; the hole was covered by a
  test in another file, which is the same shape as the first blocker. The predicate now refuses an
  empty vocabulary itself.
- A frozen docstring had the big blind acting first on a three-handed flop. It is the small blind,
  and the error was in the file whose subject is recording postflop action order.
- Two contract criteria have no test: the refusal inventory at a non-flat table, which the repair
  added, and decision 6's lean-JSON encoding, whose byte budget is checked only as a total.

## Alignment

- `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL` (existing). The first blocker is that entry
  from the other end: not a generator's validator being unfalsifiable, but a test delegating its
  whole assertion to one, which is worse because the validator now has a passing test beside it.
- `LOOP-ADDS-NO-CANARY-FOR-A-FIX-FOUND-AFTER-STAGE-4` (existing). The canary blocker is the mirror
  the entry does not cover: a canary authored **at** stage 4 that is wrong, found at stage 7 once
  stage 5 has frozen both the tests and the mutations.
- `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` (existing). Decision 14 is that entry recurring after
  it recorded its own resolution. The resolution lives in prose in one phase's decision list;
  nothing mechanical reads it, and "is this default pinned by a frozen test" is a question a script
  can answer.
- `SEAT-STATE-MARKERS-AGREE-WITH-NOTHING` (existing) and
  `A-FIXTURE-IN-A-TEST-NEED-NOT-BE-A-TABLE-THE-SIMULATOR-COULD-PRODUCE` (filed 2026-09-15). The
  table-shape blocker from the producer side and in general.
- `A-COMMITTED-AUDIT-FILE-IS-NEVER-CHECKED-AGAINST-ITS-OWN-SCHEMA-VERSION` and
  `A-PACKET-FIGURE-BAN-IS-ONLY-CHECKED-IN-THE-REPORT` (both filed 2026-09-14).
- `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`,
  `NO-FIGURE-SPLITS-THE-FLOP-BET-FREQUENCY-INTO-VALUE-AND-BLUFF` and
  `ONE-FLOP-RAISE-SIZE-AND-NO-SIZE-BETWEEN-33-AND-75` (all filed 2026-09-14), from the poker pass.
- `NO-FIGURE-REPORTS-HOW-FAR-A-MATCHED-BET-SAT-FROM-ITS-MENU-ENTRY` (filed 2026-09-15), from
  decision 14's ruled width.

## What the poker reviewer answered that nothing asked it

Decision 1 rules flop-only, so the bot bets a flop and then refuses every turn and river. Asked
whether that is better or worse at the table than never betting, the domain reviewer answered
**worse**, with the arithmetic. A 33% c-bet in the `@2.5` pot risks 1.815bb to win 5.5bb, so as a
pure bluff it needs 24.81% immediate folds to break even; minimum defence against 33% is 75.2%, so
against correct defence the bluffing half is break-even before the barrel and losing against anyone
who defends more. Everything above break-even is the turn bet that never comes. The value half is
worse off again: 33% is the first leg of a three-street plan and taken alone collects 1.815bb where
the plan collects up to 97.5bb.

This is a ruled design and not a defect, and the decision accepted the seam in terms. It is recorded
here because the phase publishes a bet frequency and a raise frequency and splits neither into value
and bluff, whose losses have opposite signs - so the one number that would show the size of the
donation is not computed by anything this phase builds.
