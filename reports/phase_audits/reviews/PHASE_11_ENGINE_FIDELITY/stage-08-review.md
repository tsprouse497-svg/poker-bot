# Phase 11 stage 8 review

Two read-only passes over the whole phase, `1b8314c..fa97133` plus the blocker fix this
stage produced. Both are coordinator-written: subagents are unavailable in this session, so
`AGENTS.md` step 10's self-review fallback applies. They were written as separate passes
with the questions kept apart, and the domain pass was written first and against the poker
rather than against the contract, because a domain review that checks the code against the
contract is a second mechanical review wearing a hat.

## Domain pass: is this the poker a real room plays?

The question this phase turns on is decision 3, and it is a rules question with no oracle in
this repo. Everything else is arithmetic or plumbing.

**The reopening rule is right, and it was implemented against the wrong reference.** The
rule the phase adopted - betting reopens for a seat that has already acted once the bet has
advanced, since the last full bet or raise, by at least the minimum raise in force - is the
rule cardrooms use, and the implementation measures against the last full *raise* correctly.
It did not measure against the last full *bet* correctly, and the case is reachable. That is
the blocker below.

**A free fold changes nothing about how this bot plays, and that was worth checking rather
than assuming.** Folding for nothing is strictly dominated by checking, so the risk of
making it legal is that some strategy takes it by accident - a sampled chart action, a
fail-closed branch reaching for the first passive action in a list. Checked all three:
the fallback checks in every free shape on all three streets, the reference strategy checks,
and the one committed chart spot where checking is free (`t6/d100/BB/SB:call`, the big blind
against a small-blind limp) carries 0.00% fold. The last one is the interesting one, because
it is the chart and not the code: a solver does not fold a free option, and the committed
artifact agrees.

**The all-in ceiling correction is right and the direction matters.** The old ceiling let a
strategy claim a raise it could not pay for. Nothing shipped ever did, so the tightening
costs nothing today; what it buys is that the legality claim several contracts lean on is
now true. A loose ceiling in a legality *proof* is worse than a loose ceiling in a strategy,
because the proof is what other phases cite.

**The fail-closed branch is right to fold rather than call, and the reasoning is about
money and not about tidiness.** The branch is reached when the action the rules chose is
unavailable. Folding costs nothing already in the pot; calling puts chips in on a hand the
module has not established cannot lose. A continuity device that invests on a path it does
not understand is no longer conservative in the one direction that matters.

**What this phase does not touch, checked and left alone.** The fallback's investment rule -
call only when no villain holding beats hero, turn and river only - is unchanged, and it
should be: widening it is proposed phase 16's decision and needs a solve this repo does not
have. The chart's own play is untouched. No sizing appears anywhere.

**Restoring the corpus report produced the phase's own poker finding.** With all six fixes
in, `latest_sample_comparison_report.txt` is byte-identical to main's: neither the free fold
nor the accumulated reopening rule moves a single number across 3,048 corpus decisions. The
honest reading is not "the fixes changed nothing" - each has a test that fails without it -
but "neither spot occurs in this corpus". Pluribus play is six-handed 100bb with no
surrendered rivers and no chains of short all-ins, which is exactly the sample where these
two rules never bind. It is real hands from a real room where they would.

## Mechanical pass

Read the whole phase diff for defects the domain pass would not surface.

**`TurnState.reopen_level` carries a default of 0.** The correct initial value is the
street's opening bet level, which both factory methods set. A default is wrong in principle
and necessary in practice, because `TurnState` is constructed directly elsewhere and a
required field would break those callers. A hand-built `TurnState` therefore measures its
accumulation from zero. Both factories are the only construction paths in this repo.

**The frozen tests could not have caught the blocker.** Every reopening test authored at
stage 4 opens its street with a full bet, so `reopen_level` and the street's opening level
coincide and the two rules agree. That is the loop's known gap - a test that was wrong when
written survives every mechanical check - and it is why stage 8 exists after a green gate.

**The report's "was" column is stated, not computed**, and says so in its own header. There
is no honest alternative: the old behaviour is out of the tree by the time the generator
runs.

**One presentation defect, fixed.** The reopening table ran straight into the following
paragraph with no blank line after the short-all-in case was added, so the table and the
prose read as one block.

## Blocker

- **[resolved]** The reopening reference was set from an under-sized all-in *bet*, which is
  a legal bet and not a full one, so a street opened by a short all-in measured every later
  advance from that short amount.

  Reproduced before it was written up. Minimum bet 20. Seat 0 is all-in for 5. Seat 1 calls.
  Seat 2 is all-in for 22. The street has advanced 22 from nothing, which is past a full
  bet, and no full bet was ever made on it - so seat 1 should be able to raise. It was
  offered `['fold', 'call']`, because the advance was being measured as 22 minus 5.

  The phase 11 contract already requires the measurement to be "against the last full bet or
  raise", so this is the implementation not matching a criterion it already carries, and no
  contract change was needed. Fixed in `poker_core/order.py`: the `BET` branch resets the
  reference only when the bet is a full bet. Pinned by two tests - the short-open case, and
  a full-bet open that still resets, so the fix is not a rule that never resets - and by a
  canary of its own, because nothing else in the gate reaches the branch.

  Worth saying what found it. Not a test, not the gate, and not a re-reading of the
  contract: it came from asking what happens when a street *opens* with a short all-in
  rather than when one interrupts an established bet, which is a poker question about a
  spot, not a code question about a function.

## Non-blocker

- The minimum raise after an accumulated reopening stays the largest single prior full
  increment, not the accumulated total. With the level at 21 and a minimum raise of 10, the
  reopened seat must raise to 31 and not 22. That is the standard reading and it is pinned
  by a test, but it is a judgment inside the fix that decision 3 did not spell out, and a
  reader of the decision record should not have to infer it from a test.
- Whether an under-sized all-in *bet* should also bar the seats that already checked is a
  separate question this phase deliberately did not answer. `TurnState.apply` clears
  `no_raise` on every `BET`, which predates this phase and which no phase 11 criterion
  names. Filed rather than fixed, because a fix would be behaviour no criterion asked for.
  See `UNDER-SIZED-ALL-IN-BET-DOES-NOT-BAR-PRIOR-CHECKERS` in `backlog.yml`.
- Four of the five canaries were authored at stage 4 against text that did not exist yet,
  and all four matched the implementation on the first try and bit. The fifth is this
  stage's. The experiment is worth repeating: phases 08, 09 and 10 each wrote their own
  canaries after the code, and each filed that as the same miss.

## Alignment

- `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` (proposed phase 12). Unchanged by this stage,
  and narrowed by one measurement: the corpus comparison is now known not to move, so what
  remains to re-measure is whatever a corpus containing free folds or all-in chains would
  show, plus everything the corrected `street_bet` reaches.
- `STRATEGY-QUERY-STREET-BET-NAME` (proposed phase 13). Unchanged.
- `MUTATION-SENTINEL-IS-COMMITTABLE` (contract-update). Recorded at stage 7: the existing
  protections cover a mutated source file and not a report a mutated run wrote.
