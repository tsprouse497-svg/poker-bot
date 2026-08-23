# Phase 13 stage 9 review - the audit packet and the backlog settlement

Read-only pass by an independent subagent reviewer over `git show b3e3cd8`: the new audit packet
`reports/phase_audits/PHASE_13_TABLE_STATE.md`, the `backlog.yml` settlement of the five entries
filed against this phase, the three alignment items filed alongside them, and the corrections
made to the stage-8 note. The reviewer wrote none of what it reviewed.

An audit packet is read as evidence by someone deciding whether the phase did what its contract
said, so its failure mode is a claim that sounds checked and is not. The brief was therefore to
re-derive rather than to read: take the packet's load-bearing numbers back to the code, the
committed reports and the corpus, and state at the top which were re-run and which were only
read, so the coordinator knows the coverage of the pass rather than guessing at it.

## What the pass actually established, and what it did not

The reviewer re-derived, by writing its own walk rather than calling the phase's own
`table_state.measures`: 3,048 preflop decision points over 499 hands, 290 refusals in a 7/283
hand-class/spot split, all six table-shape codes at zero, 10 decisions priced at hero's whole
stack with 0 diverging, 1,386 facing a raise with 0 under-raises, 178 holding a call with 0
short all-in calls, and 183 call entries of which 0 come from a seat marked all-in. It rebuilt
the four blind structures from scratch and recomputed all 169 hand classes at each: 200, 650,
1,050 and 750 chips, 33.33 / 36.11 / 35.00 / 25.00 percent, 0 classes moving and 0 refusing
anywhere, and the 11.11-point swing as the difference of the outer two. It re-grepped the
producer sweep at both ends - 9 sites in 6 files at the branch point, of which exactly 2 capped
`to_call`, against 11 in 7 now - and confirmed every line number in the packet's table. It did
the recompute-by-hand section by hand from `normalized_hands.json`, getting 5 + 10 + 200 + 45 =
260 and finding it printed where the packet says. It checked the freeze floor moving 709 to 775
with each migrated file keeping its exact count, the mutation registry at 54 then 58, all 45
gate commands green, and the line counts of six files.

Every one of those reproduced. No cited backlog id was fabricated, none of the 40 PASS rows was
a partial rounded up, and the three PARTIAL rows are correctly marked.

What it did not establish, and said so: the per-stage blocker counts in the Review findings
section, the narrative of what each earlier reviewer found, `check_gate_bite`'s behaviour (it
was instructed not to run it), and the poker content of the stage-6 engine-fidelity fix. Naming
the uncovered part is what makes the covered part worth anything.

## Blocker

- [resolved] **Three of the packet's lists were stale against the very commit that contained
  them.** This is one finding in three places and it is the stage's real lesson, because the
  packet's numeric spine held under attack and its bookkeeping did not.

  The "backlog entries this phase filed" section said twenty-one and enumerated twenty-one,
  under a sentence advertising that its ids are copied from `backlog.yml` rather than written
  from memory. The true figure was twenty-three: the two alignment items filed by that same
  commit, `LOOP-ADDS-NO-CANARY-FOR-A-FIX-FOUND-AFTER-STAGE-4` and
  `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL`, were missing from a list that claimed
  to be copied from the file they were in.

  The contract-update debt list said seven edits and missed an eighth: this contract's own Scope
  sentence, "All five are `phase: "13"` entries in `backlog.yml`, and this contract is written
  against them", which the stage-9 backlog pass made false by moving two of the five to phase
  14. That sentence is how a future reader finds the entries, and the debt list is what gates
  the tag, so an edit missing from it is an edit the `contract-update` task will not make. The
  reviewer found the same staleness in two further places that were in scope and fixed them
  there rather than listing them: the ExecPlan's own naming of all five as `phase: "13"`, and a
  sentence inside `SECOND-ORBIT-PREFLOP-SPOTS` reading "waits on `ASYMMETRIC-EFFECTIVE-STACKS`
  at proposed phase 13", which propagated into the generated `docs/BACKLOG.md` so that one file
  named two different phases for one item.

  And the section headed "One paragraph per backlog entry closed" gave closing paragraphs to the
  two entries that pointedly did not close, describing what the phase built and saying nothing
  about their staying `deferred`, with the correction 340 lines away. The packet is written for a
  reader who does not read code, and its headline section stated the opposite of the single
  distinction the whole backlog pass turned on.

  All three fixed: the counts corrected to twenty-four and nine after a further pass found more,
  the section retitled and both paragraphs marked at their heads, and the two in-scope staleness
  instances repaired directly.

- [resolved] **The fix round for the above introduced a fabricated backlog id into the packet.**
  Recorded because it is the exact defect the section it landed in warns against, and because
  the mechanism is worth knowing. The agent making the corrections wrote the packet as though it
  had already filed the alignment item the stage-9 review asked for, then stalled before filing
  it. The packet cited `CONTRACT-UPDATE-IS-THE-LABEL-OF-LAST-RESORT` and `backlog.yml` did not
  contain it. Caught by the coordinator reconciling the packet's claimed counts against the
  actual id set rather than trusting either. Closed by filing the entry, which is the right
  direction: the citation was correct about what should exist.

## Non-blocker

- [resolved] **A superlative that was false.** The packet called its recompute table "the only
  table in the report read off a committed file rather than constructed". The report holds six
  seat tables, three of them the `phase02-three-way-side-pot` rows read off
  `normalized_hands.json`. The 260 and its recipe were right; only the claim around them was
  wrong.

- [resolved] **The Phase 11 staleness was undercounted, and one item misclassified in a way that
  would have shipped a false formula.** The debt list said the contract names `street_bet` in
  three criteria; it is five, plus a section heading and a Scope bullet, and a rewrite briefed on
  three leaves two behind. More seriously, the list filed `:161` as a rename. That line states
  the all-in maximum as `(street_bet - to_call) + stack`, and under Taylor's capped `to_call`
  ruling that formula is false rather than misnamed - the code is
  `hero.street_bet + stacks[seat]`, and `current_bet - to_call` is precisely the subtraction this
  phase's own forbidden shortcuts bar from any comment, docstring or report. Rewritten as a
  rename it would have emitted `(current_bet - to_call) + stack` into a contract. Reclassified.

- [resolved] **A closing evidence line said four completed phases were migrated; it was five.**
  Inside `STRATEGY-QUERY-STREET-BET-NAME`, inherited from that entry's own pre-phase estimate,
  and contradicting the packet's checklist which said five. Verified by diffing the branch point:
  exactly five pre-existing frozen test files lost the old name and gained the new one, being
  phases 03, 05, 06, 11 and 12. Corrected, without touching the preserved `As filed:` text.

- [resolved] **The packet stated a correction to another backlog entry and did not make it**,
  saying `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE`'s count "should now read four phases rather
  than the one it argues from" while the entry still opened "Phase 11 fixed six defects". The
  same shape as the stage-8 note asserting three alignment items were filed when they were not: a
  document describing a change to the record instead of making it. The entry is now rewritten
  with all four instances, and the sentence deleted from the packet because it has been done.
  Its live-instance paragraph was verified rather than asserted, and reports honestly that this
  branch is behind `main` - the three phase-12 items still read `deferred` here while `main` has
  two of them `done` as of 2026-08-22.

- [resolved] **An unverifiable number in an evidence document.** The packet said "sixteen codes in
  the inventory", echoing decision 16's "thirteen". The reviewer could construct neither: the
  declared set that `_validate_verdict_coverage` scans holds 11, and `lookup.py` declares 6,
  giving 17 now and 14 before. Replaced with a count that can be checked against a named set.

## Alignment

- **`CONTRACT-UPDATE-IS-THE-LABEL-OF-LAST-RESORT`** (contract-update), filed. Five entries now
  carry `phase: contract-update` that are not contract edits at all -
  `MUTATION-DRILL-CHECKOUT-DESTROYS-UNCOMMITTED-WORK`,
  `TABLE-STATE-REPORT-RENDERER-HAS-NO-SIZE-CAP`, `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE`,
  `LOOP-ADDS-NO-CANARY-FOR-A-FIX-FOUND-AFTER-STAGE-4` (which is `loop_stage.py` work) and
  `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL` (which says of itself that it belongs
  beside `check_gate_bite`). The label is forced rather than chosen: `NON_PHASE_LABELS` in
  `scripts/quality_checks.py` offers no `tooling` or `process` value, which the reviewer verified
  before recommending against relabelling. The consequence is that whoever schedules a
  `contract-update` task finds a queue that is half check-script work, so the label no longer
  predicts what the task involves. The entry is its own sixth instance, which is the point.

- **Decision 8's stated cost is stale the way decision 3's is**, filed as debt item 9 rather than
  fixed, because `reports/phase_audits/decisions/` is out of this task's scope. It names only a
  big-blind-sized straddle and a straddler who acted with no raise, "which cannot occur in a
  legal preflop street", and omits `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE` - which occurs in a
  perfectly legal one and is this phase's headline residual. The reviewer flagged that the packet
  was treating decision 3's equivalent staleness as debt while leaving decision 8's unrecorded,
  which is an inconsistency in the list rather than in the phase.

- **The packet has more verified content than its cap allows.** `reports/phase_audits/*.md` is
  capped at 500 lines and this packet has now been trimmed three separate times to stay under it,
  each time to make room for a correction. Nothing was lost, because prose was tightened rather
  than evidence removed, but the pattern is the one
  `TABLE-STATE-REPORT-RENDERER-HAS-NO-SIZE-CAP` already records from the other side: a file at
  its cap converts every later one-line fix into a refactor. Both that entry and
  `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` are the same shape, and the warning-band fix the
  former asks for would cover this too.

## The finding under the findings

The packet's measurements survived a reviewer actively trying to break them, and its bookkeeping
did not survive a first read. Every blocker in this stage is a list that disagreed with the file
it claimed to be copied from, and the stage-8 note's unfiled alignment items were the same defect
one stage earlier. The repo has a check that every backlog id cited in prose resolves to a real
item, which is why no id was invented until an agent wrote one it intended to file - and nothing
anywhere checks that a count is a count of what it says, or that a list is complete against its
source. That is where this phase's remaining errors have all been.
