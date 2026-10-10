# MAINT-45 independent review, first round

Read-only pass over `git diff 22280ec..6d92100` by a reviewer that wrote none of it. No tests or gate run.
Resolution marks added by the coordinator after fixing.

## Blocker
- [resolved] Phase 19's contract gated a substitution rule on "the phase 18 pool", which the narrowed
  phase 18 drops. Now "the phase 18 measurement", with phase 19's contract added to scope by a dated entry.

## Non-blocker
- [resolved] The lean cannot price the price and menu departures: seats playing the solve only open
  2.5bb and only bet menu sizes. Stated in phase 18's Scope, with opponents that size off the solve
  not forbidden.
- [resolved] "The check-fold behind them" was wrong for preflop: a preflop refusal voids the hand
  (`src/poker_training_bot/simulator/run.py`), so how a refusal is priced is now named as stage 1's.
- [resolved] "Matched to the nearest menu size" was false: an off-menu bet refuses (phase 16's decision
  14). Corrected in the contract and `docs/V2_ROADMAP.md`.
- [resolved] Missing departures added: the cold-call merge (phase 14's decision 45), ruling 8 covering
  every raise, the decision 10 band, and decision 51's withheld four-bet family and multiway spots.
- [resolved] No postflop solve for the seats to play yet; stated as a limit.
- [resolved] The baseline paragraph described an absolute figure; reworded to the departures' cost.
- [resolved] The two non-goals pulled against each other; the chart one now reads as a departure.
- [resolved] The ladder-inversions note now asks stage 1 to check merged small blind spots against
  the unmerged export before closing.
- [resolved] A six-handed caveat: a departure can beat fixed solve seats by taking from the third
  seat; stated.
- Cosmetic line length, no check enforces it; reflowed.

## Alignment
- [resolved] COVERAGE-IS-PUBLISHED-UNDER-THE-SOLVES-OWN-PLAY-AND-A-HUMAN-DOES-NOT-PLAY-IT: dated note added.
- [resolved] THE-BACKLOGS-COST-LANGUAGE-IS-STILL-WRITTEN-FOR-A-STUDENT-RATHER-THAN-A-TABLE: dated note added.
- The proposed size-departure id is not filed: the limit is now in phase 18's contract, which is
  where stage 1 reads it.

## Checks with no finding
- Ruling stated faithfully and no wider; coordinator readings labelled as readings.
- Dropping the exploitability figure is sound, and its gap is more than convergence.
- The self-play reference nets zero rotated and rake-free.
- Roadmaps, loop policy and ExecPlan agree; no em dash; the one backlog id cited exists.

## Held back
- No gate, no count of how many of the 73 raise-weight violations sit on merged spots.
- Outside the brief: if stage 1 lands on solve-only opponents, the loop-policy stop's main reason
  shrinks to the error-bar judgement; the stop should stay.

## Verdict
Hold for the phase 19 blocker, then merge after the departure fixes. All addressed.
