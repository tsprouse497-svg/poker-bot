# Phase 11 stage 4 (tests) review

Read-only pass over `git diff 0adb6ec -- docs/phase_contracts/PHASE_03_STRATEGY_CONTRACT.md
docs/phase_contracts/PHASE_06_POSTFLOP_FALLBACK.md scripts/run_verify.py
tests/test_engine_fidelity.py tests/test_poker_core.py tests/test_strategy_contract.py
verification/mutations.yml`.

Question asked: would each test fail against a plausible wrong implementation, and does it
assert on real behaviour rather than on state rebuilt from the code under test? Stage 5
freezes these, so a weak test is preserved perfectly.

Reviewer: coordinator, self-review; subagents are unavailable in this session.

## Blocker

- **[resolved]** `test_the_query_report_generator_passes_the_street_level` asserted on the
  generator's **source text** - that the string `street_bet=state.current_bet,` appears in
  the file. That is not behaviour. It passes for a correct line on an unreachable path and
  it freezes a formatting choice as though it were a rule. Replaced with a test that runs
  the generator the way the gate runs it and reads what it actually wrote: every preflop
  record in `latest_decision_audit.jsonl` must carry a `street_bet` of at least the big
  blind, because preflop the street's level is never below the blind that posted it while
  hero's own contribution can be - the small blind's is half of it. That separates the two
  readings on the one record that distinguishes them, and it is red today.
- **[resolved]** `test_every_committed_decision_audit_record_still_validates` recomputed the
  corrected ceiling inside the test with the same formula the implementation will use, then
  compared the record against it. A test that rebuilds the rule it is checking agrees with
  the code whatever the code says - the exact defect MAINT-07 found in the settlement
  oracle, where `_settled_stacks` rebuilt each stack from the converter's own payouts.
  Replaced: the test reconstructs the `StrategyQuery` from the committed payload and hands
  it to the real `DecisionAuditRecord`, so the validator under test is the thing doing the
  validating, and asserts it checked something rather than passing vacuously on an empty
  file.
- **[resolved]** `test_a_set_without_fold_does_not_call` asserted only the negative - not a
  call - which a refusal, a fold, or a check would all satisfy. Under the fix, a set of
  `("call", "raise")` offers no passive action at all, so the outcome is determined:
  tightened to assert a `StrategyRefusal` carrying `REFUSE_NO_PASSIVE_ACTION`.
- **[resolved]** Three tests asserted truthiness on an amount rather than the amount
  (`assert record.outcome.amount`), which passes for any non-zero value and would not catch
  a ceiling that clamps. Tightened to exact equality, and the one that checks hero's higher
  ceiling now also checks the chip above it is rejected, so it pins a boundary rather than a
  single accepted value.
- **[resolved]** Four helper misuses built a `BettingRoundState` with `current_bet=20` and
  then applied a `BET`, which the engine rejects outright ("bet is only legal before a bet
  exists"). Those tests were failing on the wrong thing - a malformed fixture rather than
  the behaviour under test - which at stage 4 reads as red and would have frozen as noise.
  Rebuilt against real states.

## Non-blocker

- `test_the_query_documents_which_reading_it_carries` asserts on a class docstring, which is
  the weakest kind of test in this file: it pins prose. It is here because the phase 11
  contract makes the docstring an acceptance criterion, and it is there because the field
  had two readings precisely for want of a sentence saying which was meant. Kept with that
  understanding rather than promoted to something it is not.
- The four canaries are authored against text that does not exist yet - the lines the
  implementation must produce. They therefore cannot apply until stage 6 lands, and
  `check_gate_bite` would fail if run before then. That is deliberate and it is the fix for
  a miss phases 08, 09 and 10 each recorded separately: each wrote its own phase's canaries
  at stage 7, after the code, which is a canary shaped to the code. The cost is that a
  builder who names a variable differently gets a stage 7 failure; the pressure runs the
  right way, since the find-string is part of the frozen specification.
- No canary targets `generate_engine_fidelity_report`. That is consistent rather than an
  omission: no `generate_*` or `check_*` command anywhere in `verification/mutations.yml` is
  a canary target, because a generator's gate role is that it runs and writes, and there is
  no assertion inside it for a mutation to break. Named so the stage-7 reviewer does not
  read it as this phase's gap.
- Two frozen tests of completed phases moved: `test_rejects_check_and_fold_together` becomes
  `test_accepts_check_and_fold_together`, and the big-blind-option legal-action tuple gains
  `fold`. Both are inversions of assertions this phase's contract deliberately reverses, and
  both carry a comment naming the backlog ID and the reason. This is the one move that most
  resembles weakening a test to pass, so it is worth stating what makes it not that: the
  invariant became false about the game, the removal is named in the phase 11 contract as
  the single permitted one, and the replacement protection - that no shipped strategy folds
  when checking is free - is asserted over the fallback, the reference strategy, and every
  committed chart spot.
- The free-fold replay hand is built in the test rather than committed to
  `data/samples/`, per the stage-1 blocker. One consequence worth knowing: it is a
  two-handed hand with no showdown, so it exercises `settle_uncontested` and not
  `settle_showdown`. A free fold on a hand that goes to showdown is not covered, and the
  engine path is the same one either way.
- 21 of 49 tests pass today. Every one of them is an over-application guard, which is what
  they are for - a fix that goes one step too far is a defect the red tests cannot see - but
  a reader counting greens at stage 4 should know none of them is evidence of anything yet.

## Alignment

None. The two long-term items this phase carries were filed at stage 2 and neither moved
here.
