# Stage 10 review: phase 13 closeout

Reviewer: independent read-only subagent, 2026-08-23. No file edited, no gate run by the reviewer.
Question the driver printed: *"Bookkeeping only. A content change here belongs to an earlier stage
and should be named as one."*

Scope read:

    git diff 53038140e72592ad0fc4209e0eed9c86c494f973 -- backlog.yml \
      docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md \
      docs/phase_contracts/PHASE_13_TABLE_STATE.md \
      reports/phase_audits/PHASE_13_TABLE_STATE.md \
      reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md

That is commit `a47195e` (the `ENGINE_FIDELITY_CONTRACT_REWRITE` contract-update task) plus the
working-tree edits it had not yet committed. The stage is not bookkeeping-only by design: this
phase's contract forbids tagging until the Phase 11 contract rewrite has run, and a contract may
only be edited in `contract-update` mode, so the content lands here. The test applied was therefore
whether each content change is *true* and *named*, not whether it is late.

## Blocker

- **[resolved] The decision list stated the big-blind-sized straddle case without the precondition
  that makes it true.** `PHASE_13_TABLE_STATE_DECISIONS.md:328-330` read "a straddle equal to the big
  blind is invisible to all three signals, because it raises no bet level and leaves no seat holding
  more than its own recorded actions explain." The second half is false while the poster has not
  acted. The reviewer measured it on the committed pure functions and the coordinator reproduced the
  measurement rather than taking it: with `seats=(0..5)`, `button=3`, `blinds=(50,100)` and seat 0
  holding 100, `unexplained_contributions(..., actions=(), held={0:100,...})` returns `{0: 100}`, so
  `_forced_money_refusal` (`src/poker_training_bot/strategy/preflop_chart.py:202-210`) refuses
  `blind-structure-not-representable`; add `SeatAction(0, "call")` and the same call returns `{}` and
  the pot is answered. The same shape is already pinned as refusing at
  `tests/test_table_state_strategy.py:568`. Both the code
  (`src/poker_training_bot/table_state/forced_money.py:37-51`) and this phase's packet
  (`reports/phase_audits/PHASE_13_TABLE_STATE.md`, "Smaller residuals") keep the precondition; only
  the decision list had dropped it, in the very paragraph rewritten to remove an over-general claim.
  Fixed: decision 8's residual paragraph now states the precondition, says what happens before the
  poster acts, and says that only a big-blind-sized straddle clears signal 1 at all.

- **[resolved] The contract's Scope enumerated two escapes and there are three.**
  `docs/phase_contracts/PHASE_13_TABLE_STATE.md:42` said "Two classes escape that", naming the
  two-or-more-raises straddle and the off-ratio blind structure. The big-blind-sized straddle whose
  poster has acted is a third: the level equals the big blind so signal 1 is silent
  (`preflop_chart.py:180-186`), nothing has raised so `predicted_min_raise_target` returns `None`,
  and `unexplained_contributions` returns `{}`, so `decide` proceeds to the chart. The phase's own
  packet already listed it under "Smaller residuals", so the standing definition of done disagreed
  with the evidence document beside it. Fixed: Scope now reads three classes and names the new one
  with the condition that makes it invisible. The packet's plain-language summary said "two" for the
  same reason and now says three.

- **[resolved] Four content edits sat in the working tree with nothing accounting for them.** The
  packet's limitations section told the story to three rounds - the task's thirteen edits, then the
  review's three missed instances of the subtraction identity - and the dead-money reword, the
  "full first raise" qualifier, the evidence-criterion reword and decision 8's rewrite were outside
  that account. Only the last stated its own reason. The reviewer checked all four for truth and
  found all four true, so this was a bookkeeping defect rather than a factual one. Fixed: the packet
  now carries a fourth-round paragraph naming all five edits (the Scope count above is the fifth),
  saying which stage each belongs to and why `contract-update` is the only mode that could make
  them, and the ExecPlan carries the working.

## Non-blocker

- **The commit message's bullet counts are wrong; the backlog entry's are right.** `a47195e` claims
  "59 acceptance bullets in, 59 out, 51 byte-identical". Counted with the repo's own
  `check_contracts.section_bullets` over `a47195e~1` and the current file: 39 in, 39 out, 32
  byte-identical - exactly what `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` says. 59 is not
  reconstructible under any reading. The commit message cannot be rewritten without a rebase of a
  pushed-nowhere but reviewed commit; the backlog entry, the packet and this note all carry the
  right number, and the commit is wrong in the direction of claiming more work verified, not less.
  The rest of that message's arithmetic is exact: +233 words, -17 lines, both reproduced.
- **Nothing was dropped or weakened in the Phase 11 rewrite, with one bullet worth naming.**
  Section-by-section: Scope 6/6 (3 reworded), Non-goals 9/9 (1 reworded), Acceptance criteria 39/39
  (7 reworded); Required reports, Required command IDs, Human vetting packet, Forbidden shortcuts
  and Regression expectations byte-identical as sets; frontmatter byte-identical. Of the 7 reworded
  criteria, 4 are pure renames, 2 restate the ceiling as "what hero still owes to match the level"
  (correct under the capped `to_call` ruling, with the pinned 20/20/100 test numbers unchanged), and
  1 narrows: "rejects nothing that any shipped strategy produces" became "rejects no record any
  shipped strategy has produced." The universal present-tense form was the false claim the task
  existed to strike and the enforceable half survives byte-identical, so this is legitimate - but it
  is the one place the rewrite demands less than before, and it is named here rather than left in a
  diff nobody reads again.
- **The "two or more recorded raises" residual is stated wider than it measures.** The straddle
  cancels out of signal 3's prediction only when every raise after the first is a *full* raise. The
  reviewer worked it on committed code: 50/100 with a 200 straddle, a raise to 600 then a short
  all-in to 800 leaves the straddled table's own walk at 1,200 and `predicted_min_raise_target(100,
  [600, 800])` at 1,300, a gap of exactly the straddle less the big blind, so the pot still refuses
  `pot-holds-a-straddle`. With two full raises both walks agree and the pot is genuinely invisible,
  which is the case stage 6 measured. The error is in the conservative direction - the phase claims
  to miss more than it misses. Filed as an alignment item rather than fixed, because the wording
  appears in four artifacts including code comments this task may not touch.
- **"After a full first raise" describes where the arithmetic holds, not when the signal fires.**
  The comparison branch at `preflop_chart.py:186-193` runs on any recorded raise. In a straddled pot
  with a short first raise it still refuses, by a different amount. So "full" is the right qualifier
  for the sentence's own claim about the size of the disagreement, and the stage-6 floor fix - which
  made the walk mirror `BettingRoundState.apply` - is what keeps the unstraddled short-raise case
  from becoming a false positive. Checked because the qualifier was one of the unaccounted edits.
- **The Phase 13 contract's line count was stale in two places.** The packet and the commit message
  both said 290. It was 291 at `a47195e`, 293 with the first round of working-tree edits, and 295
  after this stage's fixes. The packet now says 295. Phase 11 at 283 was correct. Caps are 300, so
  the "both have headroom" claim held throughout; the number did not.
- **Decision 8 cited a stage-10 reviewer whose note was not on disk.** It is now - this file. The
  underlying defect is the already-filed `LOOP-STAGE-10-DEMANDS-A-REVIEW-IT-FORBIDS-WRITING`
  (deferred, `contract-update`): stage 10 requires `task_mode: idle`, idle carries an empty
  `approved_scope`, and this directory is not in `standing_scope`. This closeout writes the note
  *before* resetting to idle, which is the third of the three remedies that entry lists.
- **The evidence-criterion reword moves the contract toward the packet rather than the reverse.**
  `PHASE_13_TABLE_STATE.md:221-225` folds "the pot reconciled seat by seat" into a modifier and adds
  "without reading code", matching the house wording in the Phase 12 contract. Checked for a false
  pass and found none: the report does carry the seat-by-seat reconciliation
  (`reports/active/latest_table_state_report.txt`, "What it is told now, seat by seat:"). But the
  packet's checklist row for this criterion already enumerated four items where the criterion had
  five, so the direction of the edit is criterion-to-packet.
- **The backlog is consistent.** 91 items, no duplicate ids, every id cited anywhere in this diff
  exists, and all eight file:line references inside
  `SUBTRACTION-IDENTITY-SURVIVES-IN-FROZEN-TESTS-AND-CODE` resolve to the text they quote. No
  phase-13 entry is closed on a document rather than on code:
  `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` is a `contract-update` entry whose deliverable *is*
  a document, and the `committed_total >= street_bet` claim its closing reason leans on is enforced
  at `src/poker_training_bot/strategy/contract.py:101-108`.
- **The packet was reflowed to make room for the fourth-round paragraph.** It stood at 498 of its
  500-line cap, so ~120 lines of surrounding prose were rewrapped from ~88 to ~98 characters and two
  filler sentences dropped; the file now sits at 499. Every reflowed paragraph is word-for-word what
  it was apart from the five semantic changes named above and the stale 290. This is the same
  manoeuvre the Phase 11 rewrite used and it buys almost nothing here, which is why the packet's own
  cap is filed below rather than left as a win.

## Alignment

- `STRADDLE-RESIDUAL-BOUNDARY-IS-STATED-WIDER-THAN-MEASURED` - four artifacts
  (`table_state/forced_money.py` module docstring, `strategy/preflop_chart.py`, decision 8, and the
  `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE` entry) all say the straddle is invisible past one raise,
  when it survives any later raise that is short of a full one; one sweep should state the boundary
  as "every raise after the first is a full raise."
- `FORCED-MONEY-SIGNALS-ARE-NUMBERED-THREE-WAYS` - the code numbers the signals
  level/min-raise/contributions, the frozen tests number them contributions/level/min-raise, and the
  contract lists them in a third order, so "signal 3" means a different rule depending on which file
  the reader arrived from.
- `CONTRACT-SCOPE-ENUMERATES-RESIDUALS-WITH-NOTHING-CHECKING-THE-COUNT` - the Scope sentence asserts
  a closed list of escapes while the packet keeps its own list in two tiers, and no check compares
  the two; this stage found the two lists disagreeing by one, which is the same shape as the filed
  `COMPLETED-CONTRACT-ASSERTS-THE-CURRENT-TREE` on the residual side rather than the tree side.
- `FORCED-MONEY-DOCSTRING-DROPS-THE-STRADDLE-POSTER-PRECONDITION` - the same over-general sentence
  this stage struck from decision 8 stands in the `forced_money.py` module docstring, which says a
  big-blind-sized straddle "moves no level, predicts what a limp predicts, and shifts no minimum"
  without the condition that its poster has acted; `src/**` is outside a `contract-update` task's
  scope, so it could not be fixed here.
- `PHASE-AUDIT-PACKET-AT-ITS-LINE-CAP` - `PHASE_13_TABLE_STATE.md` is 499 of 500 after this stage,
  so the next correction to a completed phase's own evidence document forces a rewrite; the packet
  cap has no equivalent of the contract rewrite rule `AGENTS.md` gives for contracts.
