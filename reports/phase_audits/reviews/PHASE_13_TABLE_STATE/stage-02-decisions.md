# Stage 02 review: the phase 13 decision list

Independent read-only review, spawned by the coordinator.
I did not write the document under review and have no stake in defending it.

Diff reviewed: `git diff ff6f92ff76d4c7b2adb322162f617438ba450225 -- reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`.
The file is untracked at that base, so the diff is the whole 367-line document.

The driver's question: *is every reversibility class right?
A frozen-into-data call filed as runtime-reversible proceeds on its default and is then written into a committed artifact that later phases are measured against.*

Read to answer it: `docs/LOOP.md`, `AGENTS.md`, `docs/phase_contracts/PHASE_13_TABLE_STATE.md`,
`reports/phase_audits/decisions/PHASE_12_SPOT_VOCABULARY_DECISIONS.md`,
`reports/phase_audits/reviews/PHASE_13_TABLE_STATE/stage-01-contract.md`,
`verification/loop_policy.yml`, `backlog.yml`, `docs/PREFLOP_ARTIFACT_CONTRACT.md`,
`src/poker_training_bot/strategy/contract.py`, `src/poker_training_bot/strategy/preflop_chart.py`,
`src/poker_training_bot/strategy/postflop_fallback.py`, `src/poker_training_bot/strategy/reference.py`,
`src/poker_training_bot/poker_core/engine.py`, `src/poker_training_bot/simulator/table.py`,
`src/poker_training_bot/data_pipeline/comparison.py`, `scripts/generate_preflop_strategy_report.py`,
`scripts/generate_postflop_fallback_report.py`, `scripts/generate_strategy_query_report.py`,
`scripts/generate_engine_fidelity_report.py`, `CURRENT_TASK.yml`.

## Blocker

- **[resolved] The blanket exemption is argued from a narrower definition of `frozen-into-data` than the one `docs/LOOP.md` gives.**
  `docs/LOOP.md:129` reads: "the choice gets written into a committed artifact **or fixture** that later phases are then measured against."
  This list's own gloss at lines 12-13 drops the word *fixture*, and the exemption at lines 15-20 then argues only that "this phase commits no artifact, no chart and no sample."
  That is true and it answers a different question.
  The contract requires the defaults of decisions 6, 7, 8, 9 and 11 to be pinned by tests authored at stage 4 and locked by `verification/freeze.lock` at stage 5: contract lines 114 ("a test pins that they agree"), 128 ("a test pins that"), 135 ("ruled and pinned by test"), 162 ("The phase pins that arithmetic"), 170 ("pinned by test as detected").
  A frozen test is the fixture `docs/LOOP.md:129` names, and it is the one thing this repo's own known-gaps section says nothing mechanical can catch afterwards: "A test that was wrong when written survives every mechanical check above. Freezing preserves it" (`docs/LOOP.md:167-168`).
  Decision 12 is itself the proof, because it exists only to schedule the repair of frozen tests, at a cost the list describes as two phases having each paid a separate repair task.
  What must change: the list must argue the fixture half explicitly rather than eliding it.
  Either state why a frozen test pinning a refusal rule is not the fixture `docs/LOOP.md:129` means, or reclassify the items it pins.
  The current text cannot be read as having considered it, because the sentence that would have raised it is the one the phase 12 list also wrote and neither list ever quotes `docs/LOOP.md` in full.

- **[resolved] Decision 6 must halt for Taylor, and as written the flag reaches nobody.**
  The list says at line 25 that it is "flagged in place, the way phase 12 flagged its decision 5."
  That is not the same mechanism.
  Phase 12's flag reached a human because `verification/loop_policy.yml` gave phase 12 `auto_advance: false` regardless, which the phase 12 list states in as many words at its lines 20-22.
  Phase 13 has `auto_advance: true` (`verification/loop_policy.yml:81-83`, reason: "It commits no data of its own"), so the loop's only remaining stop for this phase is an unanswered `frozen-into-data` item at stage 3.
  With every item classed reversible, decision 6 advances unread.
  The repo has already recorded that this is the gap and how it was worked around: `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` at `backlog.yml:506` says "Phase 10 filed five such thresholds as frozen-into-data to force the stop, which works and is a stretch of the class."
  Phase 13 has neither phase 10's stretch nor phase 12's policy stop.
  My reasoning for halting rather than proceeding is in the section below.
  What must change: either class decision 6 `frozen-into-data` on the phase 10 precedent, or flip phase 13's `auto_advance` to `false`.
  Leaving the flag as prose is the one option that does nothing.

- **[resolved] No decision covers whether the per-seat record carries the all-in marker, and the contract asks the phase to answer exactly that.**
  Decision 5 takes three per-seat fields from `PlayerState`: `street_bet`, `committed_total` (decision 2) and `folded`.
  `PlayerState` carries a fourth, `all_in`, at `src/poker_training_bot/poker_core/engine.py:34`, immediately beside `folded` at line 33.
  Copying three of four adjacent fields is a choice, and nothing in the list makes it.
  It is not an idle one.
  `SeatAction.__post_init__` forbids an amount on a call (`src/poker_training_bot/strategy/contract.py:75-76`), so a seat that called all-in for less is recorded identically to a full caller.
  Phase 12's decision 3 deferred precisely this to phase 13: "an all-in call short of the level would carry no record of being short. That is a per-seat contribution question ... and it belongs to proposed phase 13" (`PHASE_12_SPOT_VOCABULARY_DECISIONS.md:204-206`).
  Contract lines 217-219 restate it as a criterion this phase must answer.
  With no decision item, stage 6 decides it in code and nobody reviews it.
  What must change: add an item choosing whether the per-seat record carries `all_in`, with the cost of each way stated, since it is what closes or restates the phase 12 handoff.

- **[resolved] No decision covers what `min_raise_target` is validated against, and the phase puts its headline detector on that field.**
  Contract line 167 deletes the generous pot bound.
  Decision 8's third signal then carries the whole raised-pot straddle case, and it works by comparing the query's `min_raise_target` against a reconstruction from the declared blinds and the recorded raise-to amounts.
  `min_raise_target` is producer-supplied and today validated only as `> 0` (`src/poker_training_bot/strategy/contract.py:171-172`).
  Both live producers derive it as `state.current_bet + state.min_raise` (`simulator/table.py:161`, `data_pipeline/comparison.py:367`), but the report and fixture producers compute it by hand: `generate_postflop_fallback_report.py:337` uses `shape.current_bet + MIN_RAISE`, `generate_preflop_strategy_report.py:80,95` walks it out of the actions, and the three fixtures in `generate_engine_fidelity_report.py` state it literally.
  Those are the producers this phase rewrites.
  The asymmetry matters: decision 3 makes a wrong `pot` a hard `ValueError` at construction, while a wrong `min_raise_target` becomes a silent false "straddle detected" refusal from inside the strategy.
  Decision 8 never says which side of that line the reconstruction sits on.
  What must change: add an item deciding whether `min_raise_target` is validated in `StrategyQuery.__post_init__` against the contributions and the recorded raises now that the query can reconstruct the level, or is left to the strategy as a signal.
  Whichever is chosen, the false-positive channel has to be named, because a validator that turns a producer bug into a poker claim is worse than no validator.

### What the coordinator changed

All four blockers are resolved in the decision list, and one of them changed the contract too.

The class definition at the head of the list now quotes `docs/LOOP.md` in full, artifact **or
fixture**, and the contract's own sentence saying a `frozen-into-data` call would signal scope
drift is replaced: the class reaches a behaviour default this contract requires a frozen test
to pin, even in a phase that commits no artifact.

**Decision 6 is reclassified `frozen-into-data`, so the loop now halts at stage 3.** The item
carries the reviewer's one-sentence question verbatim, since the point of halting is that a
human can answer without reading code. Its second argument is corrected in place rather than
deleted: the nearest-depth prohibition is about hero's own depth, and the record now says the
argument was tried and does not reach a villain's stack, which is itself part of why the
question goes to a human.

Two new items are added. Decision 14 carries an `all_in` marker on the per-seat record, which
is the phase 12 handoff the contract asks this phase to answer. Decision 15 rules that
`min_raise_target` stays a signal read by the strategy rather than a query validation, because
the reconstruction it would be validated against only exists preflop, and it names the
false-positive channel the reviewer identified.

Decision 16 is added from the non-blockers: the three new refusal codes are named here rather
than in code, and `preflop-chart:blind-structure-not-representable` is kept for the residual
decision 8 has to name, which settles the contradiction with the regression expectation.

The file count is corrected to six in both the decision list and the contract.

## Non-blocker

- **"nine sites across seven files" is six files.**
  Line 45.
  `grep -rn "StrategyQuery(" --include="*.py" src scripts` gives nine sites in six distinct files: `generate_preflop_strategy_report.py:102`, `generate_postflop_fallback_report.py:327` and `:667`, `generate_strategy_query_report.py:37`, `generate_engine_fidelity_report.py:98`, `:189` and `:296`, `data_pipeline/comparison.py:355`, `simulator/table.py:151`.
  The error is traceable: the stage 01 note at line 123 says "nine sites in seven files" while its own body lists **seven uncapped sites** in five bullets, so the seven is a site count read as a file count.
  Everything downstream of the number is right.
  The two capping sites are `generate_strategy_query_report.py:45` and `generate_postflop_fallback_report.py:675`, both `min(max(0, state.current_bet - player.street_bet), player.stack)`, and this list's enumeration of the seven uncapped is exactly correct.
  Contract line 100 carries the same "seven files".
  The task is in `contract-update` mode with both files in `approved_scope`, so both can be corrected now.
  It matters because the audit packet owes a "producer sweep, by file, with the verdict for each" (contract line 262), which will list six files beside prose claiming seven.

- **Every other measurement in the list checks out.**
  Stating this so the coordinator knows what was verified rather than skimmed.
  Depth arithmetic (lines 55-58): `_table_depth_bb` derives `stacks[seat] + (street_bet - to_call)` at `preflop_chart.py:196`; at bb 10, hero holding 150, contribution 100, level 300, uncapped `to_call` 200 gives 250 (25bb, correct) and capped `to_call` 150 gives 300 (30bb, wrong).
  The general form is right too: when capped, `to_call == stack`, so the derivation collapses to `stack + level - stack`, the bet level itself.
  Ragged-hero refusal (line 200): `preflop_chart.py:197` returns `REFUSE_RAGGED_DEPTH` on `hero_start % big_blind`.
  Straddle example (lines 64-70): `_blind_structure_is_representable` bounds at `small_blind + big_blind + voluntary * street_bet` (`preflop_chart.py:171`), which for three voluntary actions at a level of 600 is 1,950 against a pot of 1,850, so it is admitted; the min-raise figures of 1000 straddled against 1100 unstraddled are both correct.
  Two ceilings (lines 311-321): `preflop_chart.py:252` uses `query.street_bet + stacks[query.seat]` and `contract.py:387` uses `(street_bet - to_call) + stacks[seat]`, differing by exactly `to_call`.
  I also checked the worry that the audit's ceiling is itself wrong for a capped hero; it is not, because `DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE` at `backlog.yml:315-320` records that a capped hero is never offered raise, and this phase's own guard closes the last route.
  Enumeration pot (line 272): `generate_postflop_fallback_report.py:338` is `pot=100 + shape.current_bet + shape.hero_street_bet`.
  Probe overrides (lines 297-298): `generate_preflop_strategy_report.py:120` passes `street_bet=2 * BIG_BLIND` alone and line 121 passes `pot=SMALL_BLIND + BIG_BLIND + 60` alone.
  Decision 3's honesty about the two live producers (lines 138-140): both build `pot` as `sum(committed_total)` (`table.py:162`, `comparison.py:368`), so the check is indeed a tautology there.
  Decision 9's premise that nothing in the enumeration reads the pot: `postflop_fallback.py` touches only `street`, `legal_actions`, `hole_cards` and `board` (lines 241-281).

- **What happens to `REFUSE_BLIND_STRUCTURE` is undecided and the contract contradicts itself about it.**
  Contract lines 164-165 give the straddle and the ante each their own code.
  Contract line 296 says "Every existing refusal code keeps its meaning and stays reachable."
  `REFUSE_BLIND_STRUCTURE` (`preflop_chart.py:47`) is raised only at lines 291 and 348, both gated on `_blind_structure_is_representable`, whose two branches are the unraised-level test (which becomes decision 8's signal 2 and gets the straddle code) and the pot bound (which contract line 167 deletes).
  After the change it has no trigger left unless something is decided to keep it.
  The list should say whether it becomes a residual fallback, is retired with the regression expectation amended, or keeps a branch.

- **The new refusal code names are not chosen anywhere.**
  The phase adds at least three (shallow live seat, straddle, ante) to the seven at `preflop_chart.py:46-53`.
  Those strings are stamped into `reports/active/latest_refusal_inventory.txt` and `latest_sample_refusal_inventory.txt`, quoted in backlog entries and audit packets, and are the vocabulary a human reads the inventory in.
  The list makes vocabulary decisions elsewhere (decision 2, decision 4) and skips this one.

- **Decision 6's second argument cites the wrong rule.**
  Lines 198-200 argue that a tolerance band is ruled out because `docs/PREFLOP_ARTIFACT_CONTRACT.md` "forbids nearest-depth matching by name."
  It does, at line 94, but that rule is about matching *hero's* depth to a neighbouring cell.
  Decision 6 is about whether a *villain's* stack difference makes the table undescribable, which is a different quantity, and a tolerance there would still look up hero's exact cell.
  The V1 no-heuristic-guessing boundary probably still reaches it, but the argument as written does not, and it is one of only three reasons given for the most consequential default in the phase.

- **The postflop fallback and the reference strategy need no change, and that should be a recorded verdict rather than an omission.**
  `CheckFoldStrategy.decide` reads only `legal_actions` (`reference.py:23-28`) and `ConservativePostflopFallback` reads only the four fields listed above.
  Neither touches `street_bet`, `to_call`, `pot` or `stacks`, so decision 4's rename cannot reach them.
  The producer sweep the audit packet owes should say so explicitly, since "we looked and there is nothing" and "we did not look" are indistinguishable from a packet that lists neither.

## Alignment

- `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` (`backlog.yml:506`).
  This phase is the third instance of the gap that entry describes, and the first to hit it with no workaround available.
  Phase 10 stretched `frozen-into-data`; phase 12 had `auto_advance: false`; phase 13 has neither, which is why the blocker above exists at all.
  The entry's `reason` should gain phase 13 as evidence that the two-class vocabulary now silently drops a call rather than merely straining, and its proposed fix ("a third class, or an explicit rule that a threshold graded against external data counts as frozen") should be widened to cover a behaviour default pinned by a frozen test.

- `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` (`backlog.yml:102`).
  Already owns the fact that decisions 6, 7 and 8 have no live caller and no measurable evidence.
  Nothing to add beyond noting that it is the entry decision 6's re-ruling depends on, which the list states correctly at its lines 206-208.

- **A new id must be filed for the rake and dead-money hard stop that decision 3 creates.**
  Line 133 says plainly that "a raked hand cannot be expressed as a query at all" and that this is "filed rather than solved here", but no such entry exists.
  I grepped `backlog.yml` for an id covering rake, dead money or a dead-blind forfeit and found none; rake appears only inside the phase 05 chart-provenance entries at lines 453-465 and 530-540, which are about the solve, not the query.
  The new entry should say: `StrategyQuery` requires `pot` to equal the sum of per-seat hand contributions exactly, with no dead-money field by deliberate choice at phase 13 decision 3, so any later ingestion of real online hands must first decide where rake, a forfeited dead blind, and any other unattributed chips sit, and that decision is a query-format change rather than a validation relaxation.
  Without an id this is a paragraph in a decision list that nobody will read again when the ingestion phase starts.

- **Side pots are neither derived nor deferred anywhere, and a new id should say which.**
  Per-seat contributions plus a capped `to_call` plus decision 6's shallow-seat refusal are exactly the state in which a side pot exists, and the query still carries one scalar `pot`.
  Refusing every asymmetric table (decision 6) hides the question for now, which is precisely why it will be missed when decision 6 is re-ruled.
  The entry should record that the query models one undivided pot, that a short all-in creates a main and a side pot the query cannot express, and that whoever loosens decision 6 owns deciding whether the pot becomes a list of pots or the refusal survives for the all-in case alone.

---

## On decision 6, since the brief asks for a plain yes or no

**Yes, this phase should halt for Taylor on decision 6, even though the class does not force it.**

Three reasons.

The list's own text is the strongest argument for halting.
Line 194 says the default "refuses essentially every real table", and lines 206-208 say the person who later solves `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` "is the one who will want this re-ruled."
A default whose own author predicts a re-ruling is a deferred human question wearing the clothes of a taken decision.

The reversibility is smaller than the class suggests.
Contract line 128 requires the folded-seat case pinned by test and line 135 requires the check order pinned by test, so the exact-equality rule lands in `verification/freeze.lock` at stage 5.
Reversing it later is not an edit; it is a task with `tests/` reopened, which is the cost decision 12 spends its whole item describing.

The question is cheap for him and expensive for the loop.
It is a poker question with no code in it, and Taylor has ruled on two adjacent ones inside the last two days: `to_call` as the capped price on 2026-08-20, and the phase 12 key the same day.
There is no plausible reading on which asking costs more than shipping a bot that answers nothing at a real table.

The one honest counter-argument is that the alternatives may all be forbidden, so there is nothing to rule on.
I do not think that survives.
The artifact contract forbids nearest-depth matching of *hero's* depth (`docs/PREFLOP_ARTIFACT_CONTRACT.md:94`), not a rule about when a *villain's* stack makes the table undescribable, and the list's own third argument, that "the alternative is a tolerance nobody can derive", is an argument for asking rather than for choosing.

The question to put to him, answerable without reading any code:

> At a real table no two stacks are ever exactly equal, so should the bot refuse a hand whenever any opponent still in it has a different stack from yours by even one chip, or should it answer normally as long as your own depth matches the chart and refuse only when an opponent is short enough to change the price you are being offered?
