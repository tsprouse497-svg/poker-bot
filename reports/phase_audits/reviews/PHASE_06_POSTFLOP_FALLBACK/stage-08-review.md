# Phase 06 independent review

Loop stage 8.
Two review passes over the frozen tests, the two strategy modules, the report generator, and the committed reports.

- Poker domain review: complete. One blocker, two non-blockers.
- Mechanical review: complete. No blockers, five non-blockers.
- Gate at time of review: `run_verify.py` green across all 29 commands, including `check_gate_bite` and `ruff_check`.

## Resolution

The blocker and the turn non-blocker were both ruled on by Taylor on 2026-08-12 and are fixed.
The loop halted at stage 8, judgment calls 2 and 3 were re-ruled in a `contract-update` task, and the implementation followed in its own task.

- Judgment call 2 is now `allow-guaranteed-chops`. `_villain_beats` counts only an outright loss, the contract forbids the strict bar by name, and the `fallback-calls-guaranteed-chops` mutation is replaced by `fallback-folds-guaranteed-chops`, which reinstalls the blocker as a canary.
- Judgment call 3 is now `extend-to-turn`. `hand_cannot_lose` answers on the turn as 46 memoised river checks, and two new canaries cover it: `fallback-abandons-the-turn` reverts to river-only, and `fallback-turn-needs-only-one-safe-river` turns the universal claim into an existential one.
- `POSTFLOP-UNBEATABLE-EARLIER-STREETS` now names the flop alone and carries the corrected arithmetic.
- The fail-closed finding below is filed as `FALLBACK-FAIL-CLOSED-CAN-CALL` rather than fixed, because the conservative version needs a test and this task's own scope is the two re-rulings.
- The gate is green after the fix, and it now runs in about 65 seconds rather than 5. Nearly all of that is `check_gate_bite` re-running the phase tests once per mutation, each paying for one full turn sweep. That is the measured price of the turn extension and it was accepted with the ruling.
- Collected test cases in `tests/test_postflop_fallback.py` went from 38 to 44. The freeze lock's `test_functions` count fell from 38 to 36 because eight worked-example tests became one parametrised table; the number of assertions rose and the number of `def`s fell, so the drop in that field is not a drop in coverage.

## Reviewer independence

The reviewers were not delegated to read-only subagents this round.
Subagent delegation is disabled for this session, which `AGENTS.md` step 10 provides for as long as the concrete reason is recorded, so both passes were performed by the coordinator against the frozen tests rather than against its own recollection of writing them.
That is weaker than the loop intends, and it is weaker in exactly the direction that matters: the domain blocker below is a claim about poker, not about code, and a second domain reader would either confirm it in a line of arithmetic or refute it.
Taylor can ask for delegated reviewers before the phase closes.

## BLOCKER: folding a guaranteed chop is not conservative, it is a certain loss

`_villain_at_least_ties` in `src/poker_training_bot/strategy/postflop_fallback.py` counts a tie against calling.
Judgment call 2 ruled that bar `strict-no-ties`, and the recorded reason is:

> A guaranteed chop pays a full call to win half a pot, so whether calling is right depends on the price, and the price is where this phase has no oracle.

That reason is false, and it is the load-bearing sentence of the ruling.
Whether calling a guaranteed chop is right does not depend on the price, because the pot that gets chopped contains the villain's bet and all the dead money as well as hero's call.

Take the state the committed report actually enumerates.
The `fold/call/raise` shape carries `pot` 120 and `to_call` 20, and the 120 already includes the villain's 20.
Hero folds: hero receives nothing further.
Hero calls: the pot is 140, hero is guaranteed at least half of it because no holding beats hero, so hero receives at least 70 having paid 20.
Calling is worth at least +50 chips against folding, in that exact state, with no equity estimate and no read anywhere in the arithmetic.

The general form: facing a bet of B into a pot of P that already contains B, a hand no holding can beat returns at least (P + B) / 2 for a payment of B, and P > B always because `StrategyQuery` requires a positive pot and a postflop pot always holds the preflop money.
So the gain is at least (P - B) / 2, which is strictly positive.
Multiway does not rescue the strict bar either: chopping three ways returns P/3 + B for a payment of B, still strictly better than folding.

So the loose bar - call when no holding beats hero - is not the looser of two defensible rules.
It is the correct rule, and it is correct for exactly the reason this phase says it wants: it invests only where the investment cannot lose.
A hand that can only be chopped cannot lose.
The strict bar declines free money, and it declines it on the one path this module was built to have.

Two of the five worked examples in the committed report are that case, and the report prints the numbers that prove it:

| hero | board | beat | tie | current verdict | correct verdict |
|---|---|---|---|---|---|
| Kd Qh | 9c 9d 9h 9s Ac | 0 | 990 | folds | calls |
| 2d 7h | Ac Kc Qc Jc Tc | 0 | 990 | folds | calls |

Both are ordinary poker situations, not curiosities.
The second is playing the board with a royal flush on it, where every player has the nuts and calling a bet is free money that any human takes without thinking.
This bot folds it.

**Why this is a blocker rather than a recorded cost.** Judgment call 2 is `runtime-reversible`, so the loop was right to proceed on its default, and one edit plus a gate run reverses it.
What makes it a blocker is that a human ruled on it after being told the choice turned on a price the repo cannot source, and it does not.
That is the failure mode `docs/LOOP.md` names under known gaps: a test that was wrong when written survives freezing, and mutation canaries only prove that something fails.
Here the wrong rule is pinned three times over - `test_it_folds_on_the_river_when_the_best_villain_hand_is_a_chop`, `test_a_hand_that_can_only_be_chopped_can_lose`, `test_a_royal_flush_on_the_board_can_lose` - and the `fallback-calls-guaranteed-chops` mutation makes the gate defend it.
The gate is working exactly as designed and is defending the wrong thing.

**Why it cannot be fixed inside this task.** The strictness is not only code.
It is an acceptance criterion in the phase contract ("A hand that some possible holding ties folds") and a named forbidden shortcut ("Do not relax the strictness of that test to include hands that can be tied in order to make the bot call more often").
The contract has to change first, in `contract-update` mode, and the frozen tests and the mutation entry change with it.
That is the same shape as the Phase 05 blocker: review measures the cost of a ruling, the ruling changes, the contract changes ahead of the code.

## Domain non-blockers

### The nuts calls but never raises, and that is worth saying in the audit packet

Judgment call 4 rules out betting and raising everywhere, so a hand that beats every possible holding calls a river bet and takes no more.
That follows from the ruling and no sizing source exists, so there is nothing to fix here.
It deserves a sentence in the audit packet anyway, because "the one place this bot invests" reads as a strong claim and the investment is capped at the villain's own bet.

### The cost argument for river-only holds on the flop and does not hold on the turn

Judgment call 3 rejects extending the unbeatable call to earlier streets on cost, and gives the flop as "903 runouts against 990 villain holdings", which `backlog.yml` repeats as 894 thousand evaluations for one decision.
The figures are one card off in both places.
On the flop hero sees five cards, so the unseen deck is 47, not 45: fixing a villain holding first gives C(47,2) = 1081 holdings, each against C(45,2) = 990 runouts, so 1,070,190 evaluations. 903 is C(43,2) and 990 is the river's own count, so the two river-shaped numbers were multiplied together.

The conclusion still holds for the flop - a million evaluations per decision is roughly a thousand river checks, which does not belong in an exhaustive sweep.
It does not hold for the turn.
There the unseen deck is 46, a villain holding is one of C(46,2) = 1035, and one card completes the board, so the cost is 1035 x 44 = 45,540 evaluations: about 46 river checks, not a thousand.
`backlog.yml` already states the turn as "every one of 44 runouts" and then folds the turn in with the flop under one cost objection that only the flop earns.

So `extend-to-turn` was available at a price the phase could have paid, and was declined on the flop's arithmetic.
Not a blocker: the ruling is `runtime-reversible`, the second reason given for river-only is that almost nothing qualifies, and a turn bet folding is the same shape of loss the backlog already records.
It does mean `POSTFLOP-UNBEATABLE-EARLIER-STREETS` should split the turn from the flop, because the turn is a cheap change and the flop needs a faster evaluator first.

## Mechanical non-blockers

### `_fail_closed` can invest with a losing hand, and can refuse postflop

`_PASSIVE_ORDER` is `("fold", "call")`, so if the wanted action is not on offer the module takes the most passive legal action - and where fold is absent that is a call.
Both fail-closed outcomes contradict a contract criterion:

- calling with a hand that can lose is an investment that can lose, which the phase forbids everywhere
- `REFUSE_NO_PASSIVE_ACTION` is a postflop refusal, and the contract says it never refuses postflop

The module documents both as unreachable from the engine's own `legal_actions`, and the enumeration confirms zero postflop refusals, so nothing in the tree reaches them today.
They are reachable from a contract-valid `StrategyQuery`, which is what a reviewer can construct and what Phase 07 will eventually build by hand:

```
legal_actions=("call", "raise"), to_call=20   ->  call   postflop-fallback:wanted-action-not-legal-here
legal_actions=("raise",),        to_call=20   ->  refusal postflop-fallback:no-passive-action-is-legal
```

Neither line is covered by a test or by a mutation.
The conservative fail-closed is fold-or-refuse, never call, and both codes want a direct unit test.
Filed as `FALLBACK-FAIL-CLOSED-CAN-CALL` in `backlog.yml` rather than fixed: the re-ruling task that reopened `tests/` was scoped to the chop bar and the turn extension, and widening it to carry an unrelated behavior change is how a task stops being reviewable.

### The report generator and the frozen tests are the same hundred lines twice

`Shape`, `engine_shapes`, `Scenario`, the per-street board slicing, the query builder, and all five named scenarios with their prose exist independently in `tests/test_postflop_fallback.py` and `scripts/generate_postflop_fallback_report.py`.
The duplication is deliberate under the loop - a builder may not write to `tests/`, and tests importing from `scripts/` would be worse - but the two copies can now drift, and the thing they would drift about is the one spot where money goes in.
A shared module under `src/` that both import is the fix, and it belongs in a task where `tests/` is legitimately in scope.

### `street_bet` now has two committed readings, visibly

`scripts/generate_postflop_fallback_report.py:build_query` passes `street_bet=state.current_bet`, the street's bet level.
`scripts/generate_strategy_query_report.py:build_query` passes `street_bet=player.street_bet`, hero's own contribution.
Phase 06 picked the reading `preflop_chart._table_depth_bb` needs, so it is the correct one, and `STREET-BET-MEANING-AMBIGUOUS` in `backlog.yml` already records the disagreement.
What is new is that two committed generators now build the same field two different ways, which makes the ambiguity something a reader trips over rather than something a backlog entry describes.

### Capping `to_call` at hero's stack breaks the documented derivation

Both generators write `to_call=min(max(0, current_bet - street_bet), stack)`.
Under the street-level reading of `street_bet`, hero's own contribution is recoverable as `street_bet - to_call`, which the docstring says and the chart relies on - but once `to_call` is capped by a short stack that subtraction returns a number hero never put in.
No committed sample hand reaches a short postflop caller, so nothing is wrong in the tree today.
It belongs on `STREET-BET-MEANING-AMBIGUOUS` rather than as a separate item.

### Two small ones

`UNSEEN_HOLDINGS = 990` is a hardcoded denominator in the report while the counts beside it are computed from the actual unseen deck; deriving it would make the row self-consistent by construction.
`river_hand_cannot_lose` is annotated `hole_cards: tuple[str, str]` and is called with `tuple[str, ...]` from both the tests and the generator.

## What the review confirmed

These were checked rather than assumed, and each one holds.

- The enumeration reads its shapes from `BettingRoundState.legal_actions` rather than from a list, in both the tests and the report, so a new engine action set widens the sweep instead of escaping it. Four shapes, and the test guards the derivation itself.
- No path in either module returns a bet or a raise. The report's action census over 72 states shows call 4, check 36, fold 32, and nothing else.
- Every decision is routed through `DecisionAuditRecord`, so legality is proved by the Phase 03 validator rather than by eye, and the 78 committed audit lines could not have been written if any of them were illegal.
- The composite adds no decision of its own: `decide` returns its component's outcome as the same object, with no inspection of it and nowhere for a passive substitute to be added later.
- A preflop chart refusal reaches the caller with its original code. The committed report shows five of them from the sample hands and zero fallback refusals.
- The unbeatable enumeration is exhaustive over all 990 holdings from the full unseen deck, ranks villains with the same evaluator as hero, and is not narrowed by seat count or folded cards, which is conservative in the only direction that matters.
- The recomputable number checks out by hand: counting `flop`, `turn` and `river` actions in `data/samples/normalized_hands.json` gives 6 + 0 + 0 + 4 = 10, and the replayer reached 10.
- `check_gate_bite` is green, so all three Phase 06 mutations make `pytest_postflop_fallback` fail.

## Housekeeping the phase still owes

- The active ExecPlan is stale. Every slice is unchecked, every delegation lane still reads `planned`, and `## Outcome` still reads "Not yet complete", although stages 1 through 7 have landed. `AGENTS.md` requires it to be updated after meaningful slices, and as written it does not record whether the lanes ran or who ran them.
- `verification/loop_state.yml` and `reports/active/verify_results.json` are uncommitted at stage 8.
