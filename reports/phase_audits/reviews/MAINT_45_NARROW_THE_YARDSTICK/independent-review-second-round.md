# MAINT-45 independent review, second round

Read-only pass over the first round's fixes and the phase 20 change, by a reviewer that wrote none of
it. No tests or gate run. Resolution marks added by the coordinator after fixing.

## Blocker
None.

## Non-blocker
- [resolved] "A preflop refusal voids the hand" was too narrow: a refusal on any street voids it
  (`src/poker_training_bot/simulator/run.py`). Now "a refusal on any street".
- [resolved] "Mostly decision 51's withheld four-bet family" was a size claim with no count. Now
  "among them".
- [resolved] The ladder-inversions note named only small blind spots as merged; every seat but the
  big blind facing one raise merges. Corrected.
- [resolved] "Ruled again" was strong for "keep this open ended"; now "said". "Nothing for him to
  answer today" is the coordinator's conclusion from his words and stays.

## Alignment
- [resolved] THE-REVIEW-QUEUE-LISTS-A-PHASE-WHOSE-DEPENDENCIES-ARE-NOT-MET-AS-WAITING-ON-YOU filed:
  the queue still counts phase 20 as waiting on Taylor because it ignores `depends_on`. The fix is
  code in `scripts/review_queue.py`, outside this task's scope.

## Checks with no finding
- Every first-round fix checked against the code and decision files and holds; the phase 19 phrase
  is fixed and the roadmap matches the contract.
- Phase 20 edits are faithful to Taylor's two quotes and commit to nothing; nothing else on the
  branch presents phase 20's inputs as owed now.
- Only capitalised hyphenated token added is MAINT-45; no em dashes; scope log covers phase 19 and
  20's contracts; contracts well under the line cap.

## Held back
- Did not run `scripts/review_queue.py`; the printed board is inferred from the code.
- No count of four-bet against multiway refusals.

## Verdict
Merge-ready after the wording fixes, all folded in.
