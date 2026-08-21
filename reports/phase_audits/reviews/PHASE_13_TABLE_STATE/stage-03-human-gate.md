# Stage 03 review: the human gate on decision 6

Independent read-only review, spawned by the coordinator.
I did not write the ruling under review and have no stake in defending it.

Diff reviewed: `git diff 7c1a283f827d87799019a308b46a2f7f5e2a9a8c -- reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`.
It is one added paragraph, `PHASE_13_TABLE_STATE_DECISIONS.md:206-212`, plus the filled `Answer: [exact-equality]` at line 204.

The driver's question: *does the record now say what was actually ruled, including any cost that was accepted rather than only the answer?*

Read to answer it: `reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`,
`reports/phase_audits/decisions/PHASE_12_SPOT_VOCABULARY_DECISIONS.md`,
`docs/phase_contracts/PHASE_13_TABLE_STATE.md`, `backlog.yml`,
`src/poker_training_bot/strategy/preflop_chart.py`, `src/poker_training_bot/strategy/composite.py`,
`src/poker_training_bot/simulator/run.py`, `src/poker_training_bot/simulator/config.py`,
`src/poker_training_bot/simulator/table.py`, `scripts/generate_postflop_fallback_report.py`,
`scripts/generate_strategy_query_report.py`, `scripts/generate_preflop_strategy_report.py`,
`data/samples/normalized_hands.json`, `data/samples/normalized_hands.jsonl`,
`reports/active/latest_postflop_fallback_report.txt`, `verification/mutations.yml`,
`tests/test_full_table_preflop.py`, `tests/test_spot_vocabulary_downstream.py`,
`tests/test_strategy_contract.py`, `tests/test_engine_fidelity.py`.

On the question as asked: **the ruling record is faithful.**
It names what was chosen in the words it was chosen in, says he was shown three live options in poker English with their costs, gives the reasoning he took rather than only the conclusion, and states the cost and who inherits the re-ruling (`PHASE_13_TABLE_STATE_DECISIONS.md:206-212`).
That is the same shape as the phase 12 precedent at `PHASE_12_SPOT_VOCABULARY_DECISIONS.md:24-43`, which also records what he was shown, the rejected reading, and the costs that travelled with the options.
The rest of the list still argues toward this default rather than against it: decision 5's over-refusing preference (lines 181-183), decision 7's check order (lines 244-253), decision 9 (lines 288-309) and decision 16's `a-live-seat-is-shorter-than-hero` code (lines 453-456) all read as settled the same way, and nothing in `docs/phase_contracts/PHASE_13_TABLE_STATE.md:119-145` now contradicts it.

One clause in the new paragraph is wrong, and it is the clause that states the accepted cost.

## Blocker

- **[resolved] "It costs nothing today because all 499 committed hands are exactly 100bb" is false, and the report that proves it is already committed.**
  `PHASE_13_TABLE_STATE_DECISIONS.md:207-209` rests the whole accepted cost on the corpus.
  The corpus half is correct.
  But the preflop chart has a second live caller that is not the corpus, and it is asymmetric today.
  `scripts/generate_postflop_fallback_report.py:729-768` drives every hand in `data/samples/normalized_hands.json` through `CompositeStrategy`, whose preflop component is `PreflopChartStrategy` (`src/poker_training_bot/strategy/composite.py:69`).
  One of those four hands, `phase02-three-way-side-pot`, has starting stacks of 50, 100 and 200 at blinds of 5/10 - the only unequal table committed anywhere in the tree.
  All three of its preflop decision points reach the chart and refuse today with `preflop-chart:lookup:no-artifact-for-table-size`, at `reports/active/latest_postflop_fallback_report.txt:192-194`.

  They reach the lookup only because the depth check cannot see the table.
  `_table_depth_bb` derives hero's start as `stacks[seat] + (street_bet - to_call)` (`src/poker_training_bot/strategy/preflop_chart.py:196`), and that generator caps `to_call` at hero's stack (`scripts/generate_postflop_fallback_report.py:675`), so the capped hero derives as the bet level itself - exactly the arithmetic decision 6's own list already worked out at `PHASE_13_TABLE_STATE_DECISIONS.md:58-66`.
  Seat 0 derives 45 + (200 - 45) = 200, seat 1 derives 90 + (200 - 90) = 200, seat 2 derives 200 + (10 - 10) = 200.
  Three different real depths - 5bb, 10bb, 20bb - all present as 20bb, no stack exceeds 200, the check passes, and the lookup refuses on table size instead.

  Once this phase recomputes each seat's start as what it holds plus what it has put in (`docs/phase_contracts/PHASE_13_TABLE_STATE.md:121`), the depth check runs before the lookup (`src/poker_training_bot/strategy/preflop_chart.py:287-302`) and all three codes move.
  Seats 0 and 1 see a deeper live seat and get `table-is-not-one-flat-stack-depth`, which is decision 7's existing branch.
  Seat 2 is the deep seat acting first with two live shallower seats behind, so it gets the new `preflop-chart:a-live-seat-is-shorter-than-hero`.
  That is decision 6, biting today, on a committed gate-regenerated report, with no live table state anywhere in sight.

  What must change: the ruling paragraph at `PHASE_13_TABLE_STATE_DECISIONS.md:206-212` must stop saying the rule costs nothing today.
  It should say that the corpus is unaffected, and that the one committed non-corpus surface the chart reaches - the `phase02-three-way-side-pot` sample hand - changes three refusal lines in `reports/active/latest_postflop_fallback_report.txt`, one of them to the new shorter-than-hero code, which is the first and only live evidence the phase has that decision 6 fires at all.
  I checked the other candidate surfaces and they are clean, so the correction is bounded to this one: the simulator resets stacks every hand (`src/poker_training_bot/simulator/run.py:104`, and `src/poker_training_bot/simulator/config.py:43-49` forbids any depth but 100bb), the preflop strategy report's probes derive every stack as `100 * BIG_BLIND - committed` so they all recompute flat (`scripts/generate_preflop_strategy_report.py:97`), `generate_strategy_query_report.py:58` uses `CheckFoldStrategy` and never touches the chart, the unequal fixtures in `tests/test_engine_fidelity.py:508-535` are `DecisionAuditRecord` validation rather than chart queries, and `tests/test_spot_vocabulary_downstream.py:333` recomputes to a flat 10000 once its contributions are added back.

  This is a correction to the record, not to the ruling.
  Nothing here suggests he would have answered differently: three lines in one report is a smaller cost than the coverage collapse he already accepted.
  It matters because the ruling paragraph is the thing a later reader will quote when deciding whether decision 6 was ever exercised, and as written it says "never".

  Resolved as asked, and the reviewer's own arithmetic is carried into the record.
  The ruling paragraph now says almost nothing rather than nothing, names the fixture, its
  stacks, the three refusal lines it moves, and that this is the phase's only live evidence
  decision 6 fires at all. The contract's asymmetric measurement criterion says the same, so a
  stage 4 author expecting an unchanged postflop fallback report is corrected before authoring.
  `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` is corrected too, and keeps its conclusion.

### What else the coordinator changed, from the non-blockers

The ruling now has a `## Ruled by Taylor, 2026-08-21` section before any decision body, matching
the phase 12 precedent, so the document reads as answered from its header.
Decision 16's Default no longer retires `blind-structure-not-representable`; it is kept and
narrowed to forced money the three signals cannot classify, which is the residual decision 8
already owes and which satisfies the contract's regression expectation.
The item count is corrected from twelve to fifteen.
Decision 5's mitigation sentence is the one item left as the reviewer wrote it rather than
edited, and is answered in the Non-blocker section below.

## Non-blocker

- The ruling is invisible from the top of the document.
  `PHASE_13_TABLE_STATE_DECISIONS.md:15-26` still reads "The loop halts until a human answers", and decision 6 still opens with "**This is the one item the loop must stop for**" at line 189, both present tense.
  Phase 12 put its ruling in a top-level `## Ruled by Taylor, 2026-08-20` section at `PHASE_12_SPOT_VOCABULARY_DECISIONS.md:24`, before any decision body, which is why that document reads as answered and this one does not.
- Decision 16 contradicts itself about `blind-structure-not-representable`.
  The Default at `PHASE_13_TABLE_STATE_DECISIONS.md:456` says it "is retired, because both of its branches become one of the two new codes"; line 469 says "The default is to keep it for exactly that residual."
  The Answer bracket is `[named-above]`, which resolves to the Default, so a stage 4 author reading the bracket retires a code that the contract's regression expectation at `docs/phase_contracts/PHASE_13_TABLE_STATE.md:297` requires to stay reachable.
  The Default paragraph should be rewritten to say the code is kept as the code for forced money the phase cannot classify.
- The header's item count is wrong.
  `PHASE_13_TABLE_STATE_DECISIONS.md:28` says "The other twelve items are `runtime-reversible`"; the document has sixteen decisions and one is `frozen-into-data`, so it is fifteen.
  The number matters here because it is the count of items being reported to Taylor after the fact rather than asked about.
- Decision 5's mitigation does not hold.
  Line 183 says a producer that forgets the folded marker "over-refuses rather than under-refuses" and "the reconciliation will usually catch it anyway."
  Decision 3's reconciliation sums per-seat hand contributions against the pot (lines 125-126), and a folded seat's chips are in that sum either way (`docs/phase_contracts/PHASE_13_TABLE_STATE.md:79-81`), so the reconciliation cannot see a wrong folded marker at all.
  Under exact-equality that mitigation is the only thing standing between a mis-set marker and a refusal, so the sentence should be deleted rather than softened.
- On the fourth question - was there a second item he should plainly have been asked about - the honest answer is decision 3, and it is close.
  Its accepted cost at lines 138-141 is that "a raked hand cannot be expressed as a query at all", which is the same shape of permanent fail-closed rule as decision 6 and reaches further: it is a hard stop for any later ingestion of real hands, which is the very thing `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` says this repo needs next.
  It is correctly classed `runtime-reversible` - lifting it is a validator edit, not a re-derivation - and it is already filed forward as `QUERY-CANNOT-EXPRESS-RAKE-OR-DEAD-MONEY` (`backlog.yml:102`), so nothing is lost.
  Recorded as the one he had the best claim to be shown while he was already being asked, not as something the stage owes.

## Alignment

- `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` (`backlog.yml:131`) states two things this review measured to be false.
  Its reason text says the `phase02-three-way-side-pot` fixture "can never reach the six-max chart" (`backlog.yml:142`) and that "the detection that phase builds has no live caller, and its tests are synthetic fixtures with no producer behind them" (`backlog.yml:144-145`).
  The fixture does reach `PreflopChartStrategy.decide` through the composite at `scripts/generate_postflop_fallback_report.py:729-768`, and the resulting refusals are committed at `reports/active/latest_postflop_fallback_report.txt:192-194`.
  Both sentences should be corrected to say the chart is reached and refuses at the lookup today, and refuses on table shape after this phase.
  The entry's conclusion - that no *six-max 100bb* table shape exists to measure, and that data is needed - survives the correction intact.
- No existing id covers where a ruling is recorded in a decision list, and phase 12 and phase 13 answered it two different ways (`PHASE_12_SPOT_VOCABULARY_DECISIONS.md:24` versus `PHASE_13_TABLE_STATE_DECISIONS.md:206`).
  A new id should be filed, `DECISION-LIST-HAS-NO-FIXED-PLACE-FOR-A-RULING`, saying that a decision list has no convention for where a human ruling lands, so a document can hold an answered question whose header and body still read as open, and that `docs/exec_plans/TEMPLATE.md` or `docs/LOOP.md` should name one place.
- `SIDE-POTS-NOT-EXPRESSIBLE-ON-THE-QUERY` (`backlog.yml:118`) already hands the side-pot question to whoever re-rules decision 6, and its text matches the ruling as filed.
  No action; recorded so the next reader does not file it twice.
