# Phase 07 independent review

Loop stage 8.
Two review passes over the frozen tests, the simulator and profiles packages, the report generator, and the committed report.

- Mechanical review: complete. One blocker, three non-blockers.
- Poker domain review: complete. No blocker, four non-blockers.
- Gate at time of review: `run_verify.py` green across all 31 commands, `check_gate_bite` reporting 14 mutations all caught.

## Reviewer independence

The reviewers were not delegated to read-only subagents.
Subagent delegation is disabled for this session, which `AGENTS.md` step 10 permits with the reason recorded.
Same exception as Phase 06, same cost: the coordinator is reviewing work it wrote, and the guard against that is that every finding below carries a number produced by running the committed code rather than by reading it.

## BLOCKER: a voided hand's record throws away the actions that led to the refusal

`_voided` in `src/poker_training_bot/simulator/run.py` builds its normalized record from `played.streets or blinds_only(config, button_seat)`.
`played.streets` is only appended once a street's betting loop *completes*, and a refusal returns from inside that loop, so on a preflop refusal `played.streets` is always empty and `blinds_only` always wins.

Measured over the committed self-play run, all 600 hands, seed 20260812:

| decisions taken before the refusal | hands |
|---|---|
| 2 | 7 |
| 3 | 24 |
| 4 | 29 |
| 5 | 51 |
| 6 | 11 |
| 7 | 6 |

Every one of those 128 hands records exactly two actions: the two blind posts.
**565 real actions are discarded**, and every refused hand's record is a hand where nobody did anything.

This is not a cosmetic loss. It is exactly the information the phase exists to surface.
The report leads with "hands refused: 128, 21.3%" and calls it "the most actionable number in this file - it is a list of spots the charts do not yet hold".
It is not a list. The refusal codes are static strings that name the *kind* of miss, not the spot, so the only place the spot survives is the action sequence - and that is the thing being thrown away.
The `_voided` docstring makes the claim the code does not deliver: "a reviewer asking which spot the chart refused needs the cards and the action in front of it."

The information does exist. `hand.decisions` keeps every pre-refusal `DecisionAuditRecord`, and reading those back gives the answer the report should have printed:

| hands | preflop action in front of the refusal |
|---|---|
| 17 | fold fold fold raise raise |
| 11 | fold fold fold fold call raise |
| 11 | fold raise raise |
| 9 | fold raise fold raise |
| 9 | fold fold raise fold raise |
| 8 | fold fold raise raise |

Those are three-bets and four-bets, and a three-bet cold-called then raised again. That is a real, specific, closable coverage gap, and it was one function call away from being in the report.

**Second, connected defect: the record cannot be replayed at all.**
`replay_hand` on the first refused hand raises `ValueError: preflop street ends with an open betting round`.
That is correct behaviour from the replayer - the hand genuinely never finished - which means a voided hand is not a completed hand history and calling it a `NormalizedHandHistory` is a category error rather than a bug in the emission.

The report is honest about the consequence without naming the cause: it prints "hands re-derived by the replayer: 472", not 600, so 128 records are carried and never cross-checked. But the prose above that number says "Every dealt hand is written out in the Phase 02 normalized schema as it is played, then handed back to the Phase 02 replayer", and that is true of 79% of them.

**Why it is a blocker rather than a non-blocker.** The phase's stated headline output is a coverage measurement, and the coverage measurement is unusable for its purpose. Fixing it also cannot be done quietly: the frozen `test_every_dealt_hand_is_a_valid_normalized_hand` asserts `isinstance(hand.normalized, NormalizedHandHistory)` for *every* hand including refused ones, so the honest shape - a refused hand carrying its action sequence but not a completed-hand record - needs that test changed. That is a test-and-contract question, not a patch.

## Mechanical non-blockers

### The noise threshold is never exercised anywhere in the middle

`separated_profiles` is the mechanism behind judgment call 3: no winner is named unless a figure clears two standard errors.
It is only ever asked two questions, and both are degenerate.

- Self-play: all six seats are one profile, so the summed figure is identically `0` and the standard error is identically `0.00`. `separated_profiles()` returns `()` because zero is not greater than zero, not because a noise threshold did any work.
- Floor: the composite's figure sits **14.9 standard errors** from zero.

So `test_a_difference_inside_the_noise_is_not_reported_as_a_finding` passes on an arithmetic identity, and nothing anywhere tests a difference that is real but too small to call - which is the only case judgment call 3 was written for. The rule is unpinned in the same way judgment call 4 was, and for the same reason: the assertion is true but vacuous.

### `hand_id` is not unique across runs

`hand_seed = config.seed + index` and `hand_id = f"sim-{hand_seed}"`, with `table_id` a constant `"sim"`.
So a run seeded 100 and a run seeded 101 both contain a hand called `sim-101`, and nothing on the record distinguishes them.
That is the price of making a hand reproducible from its own seed - a genuinely good property, and the two are in tension rather than one being wrong. Worth a note in the audit packet so nobody later assumes hand ids are globally unique.

### The decision audit is never committed

The contract says "every decision the simulation applies is recorded as a Phase 03 `DecisionAuditRecord`, and the recorded audit for a simulation is regenerable from its seed". Both are true in memory. But unlike Phase 06, no audit file is written, so a reviewer cannot inspect a single decision without running the generator and reaching into the result object. Phase 06 committed `latest_postflop_decision_audit.jsonl` for exactly this reason. Not a criterion violation - the contract only requires the comparison report - but an inconsistency between two adjacent phases' evidence.

## Domain non-blockers

### The floor figure is right, and it is not in a unit a poker player thinks in

The composite wins **38.67 chips per hand** against five check-fold seats. Checked against first principles rather than taken on trust: every hand puts 150 chips of blinds on the table, all five reference seats fold to any bet, so from its four non-blind positions the composite collects 150 whenever it opens and folds for nothing when it does not. At a plausible average opening frequency the four-in-six share alone lands near 30 chips a hand, plus the big-blind spots where the small blind folds, minus its own posted blinds when it declines. 38.67 is the right order of magnitude, so the number is not an artifact.

But 38.67 chips per hand at 50/100 is **38.7 bb/100**, and that is the figure a poker player can calibrate against - it is roughly four to eight times what a strong human wins in a real game, which is the correct and useful shock. The report satisfies the contract's "normalized per hand at a stated stake" and misses the chance to say it in the vernacular.

### Every reference seat folds preflop, so the floor is shallower than it looks

`CheckFoldStrategy` folds whenever `to_call > 0`, and every non-blind preflop seat faces the big blind, so all five reference seats fold every hand before the flop unless they are in the big blind. The report says the figure is "closer to how often the chart opens than to how well it opens", which is the right warning, but the mechanism is stronger than that phrasing suggests: the opponents are not weak, they are absent. Only the big-blind seat ever sees a flop, which is also why the floor run shows 2 showdowns in 600 hands and zero refusals.

### The self-play refusal rate is the phase's real finding and deserves promoting out of this phase

21.3% of self-play hands reach a spot the committed charts do not hold, and the breakdown above shows them concentrated in three-bet and four-bet trees. Phase 05 committed 36 spots covering opens, responses to a single open, an opener facing a three-bet, and BB versus SB limp. This run is the first evidence of what that omits in practice, and it is a bounded, closable list rather than an open-ended one. It belongs in `backlog.yml` as a sized piece of work, not only inside a report.

### Nothing here is a strategy evaluation, and the contract's wording holds

Checked deliberately, because this is the phase where a reader most wants to over-read a number. The report states the postflop-checks-through consequence before any figure, repeats the stacks-reset caveat where the figures appear, and labels the floor run as a floor check twice. No figure in the file is expressible as a claim about postflop play. That criterion is met.

## What the review confirmed

- The simulator adds no poker rule of its own: legality, turn order, ranking and pot splitting all come from Phase 01, and every applied action came out of a `StrategyDecision`.
- Chips are conserved per hand, not in aggregate, and a hand whose books do not balance stops the run. `simulator-forgets-what-players-put-in` proves the check bites.
- The run is a pure function of seed, seating and profiles, including independence from the `random` module's global state, which `simulator-seeds-from-global-random` now proves.
- A hand regenerates from its own seed alone, cards, button and play identical, because the button is derived from the seed rather than from the index.
- 472 of 472 measured hands were re-derived by the frozen Phase 02 replayer with matching decision points.
- Self-play nets exactly zero across the table over 600 hands.
- Position coverage is exactly even: every seat holds every position 100 times in 600 hands, and the report gives that as the hand-checkable number.
- Renaming a profile changes no byte of a dealt hand, because dealt hands name seats rather than profiles.
- All 14 mutations are caught, including the three that survived at first.
