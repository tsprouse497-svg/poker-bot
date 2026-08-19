# Phase 11 stage 6 (build) review

Covers the build commit `5d0c8c8` and the frozen-test repair that follows it. The stage
halted between the two, which is why one note covers both.

Reviewer: coordinator, self-review; subagents are unavailable in this session.

## Blocker

- **[resolved]** The build went green on nothing: ten frozen tests failed and the builder
  could not reach any of them, because `tests/` left `approved_scope` at the freeze. The
  loop's answer is a halt and a repair task with the builder files out of scope, which is
  what happened - `phase-11-frozen-test-repair`, seeded from the build commit, holding
  `tests/` and `verification/freeze.lock` and nothing else. The pressure has to run that
  way: a task that can reach both the test and the implementation will always find it
  easier to move the implementation.

  What the ten were, and why none is an implementation defect:

  Six were in `tests/test_postflop_fallback.py`. Its enumeration derives the engine's own
  postflop legal-action sets and then names two of them by hand, `("check", "bet")` and
  `("check", "raise")`. Fold joins both. The repair adds it at every `shape_with` call site
  and in the assertion that guards the sweep; the sweep itself is still derived from the
  engine rather than listed, so it follows the engine rather than describing it.
  One was in `tests/test_strategy_contract.py`, asserting an all-in target of `20 + 940`,
  which is the old ceiling - the assertion *was* the defect, stated as a test. Repaired to
  `(20 - 20) + 940`, written as the subtraction rather than as `940`, so the arithmetic a
  reader has to check is on the page.
  Three were in this phase's own `tests/test_engine_fidelity.py`, all authoring errors
  caught by the implementation rather than the other way round. Two built an accumulation
  that does not reach the bar - `19 - 10` is 9 against a minimum raise of 10 - and asserted
  it reopens. One applied a raise from a seat that was not next to act, so it failed on
  "cannot act out of turn" while claiming to test a minimum raise.

- **[resolved]** The third of those, `test_a_full_raise_resets_the_level...`, was wrong
  about the poker and not only about the arithmetic, so it is worth stating separately. It
  asserted that after a full raise to 30 and a short all-in to 35, seat 0 is barred from
  raising. Seat 0 is not barred and should not be: seat 1's full raise gave seat 0 its
  raising right back, and a later short all-in does not take it away. The seat the short
  all-in must not reopen for is seat 1, the one that has acted since the last full raise.
  Repaired to assert that, plus that seat 0 is *not* barred, which makes it a stronger test
  than the one authored: it now pins both halves of the rule instead of one wrong half.

- **[resolved]** `ruff --no-cache` failed on a 105-character line the repair itself
  created, in a frozen Phase 06 test. Caught before the commit rather than at stage 7,
  which is the defect Phase 08 and MAINT-RUFF-CACHE both shipped. Split into two lines; no
  assertion changed.

## Non-blocker

- No assertion was weakened in the repair. Every repaired test makes the same claim it made
  before, against the behaviour the phase 11 contract requires. The one that looks most like
  a weakening - the all-in ceiling - is the case where the test was asserting the defect,
  and the contract names that reversal in its own criteria.
- The full suite is green at 814 passing, up from 803 plus 10 failures: the repair added one
  test rather than only fixing three, because splitting the three-all-in case into a clears
  and a does-not-clear pair was the honest way to fix the one that did not clear.
- `TurnState` gained a field with a default (`reopen_level: int = 0`). A default is wrong
  for it in principle - the correct initial value is the street's current bet level, which
  both constructors set - but a required field would break any caller constructing a
  `TurnState` directly, and the replayer does. Worth knowing that a hand-built `TurnState`
  gets 0 and therefore an accumulation measured from zero. Both factory methods are the only
  paths in the repo, and both set it.
- The report's "was" column is stated rather than computed, and says so in its own header.
  There is no way to compute it: the old behaviour is out of the tree by the time the
  generator runs. Every "now" is computed on the run.

## Alignment

None. Nothing surfaced here that a later phase has to carry.
