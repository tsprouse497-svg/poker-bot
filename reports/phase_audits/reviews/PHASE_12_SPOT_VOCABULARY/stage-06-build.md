# Phase 12 stage 6 review - the build

Read-only pass over `git diff 5b715d6` at the end of stage 6, against
`AGENTS.md` and `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`.
No gate runs inside the review; the figures quoted are from the stage's own run.

Question the driver asked: does the implementation do the work, or only enough to satisfy
the frozen tests, and does anything pass for a reason the contract did not intend?

Coordinator-written, as the phase's no-delegation exception records. Subagents are
unavailable in this operator's sessions and the ExecPlan's Delegation Plan carries the
reason; `AGENTS.md` step 10's self-review fallback applies.

## Blocker

- [resolved] **34 failures and 3 collection errors in frozen tests of phases 03 to 09, and
  the builder cannot touch them.** Every one is a v1-shaped construction or a v1 assertion:
  `PreflopAction("CO", "raise")` with no size, `SeatAction(seat, "raise")` with no amount,
  a literal `t6/d100/BB/CO:raise`, `DECISION_AUDIT_SCHEMA_VERSION == 1`, or
  `test_a_second_orbit_spot_refuses`, which asserts the exact behaviour this phase's
  contract requires removed. None is an implementation defect. Stage 4 authored this
  phase's own tests and none of the migrations the phase forces on earlier ones, which is
  the identical miss phase 11 made and repaired in its own task with the builder files out
  of scope. Filed as `FROZEN-TESTS-PREDATE-THE-SIZED-SPOT-KEY`. Repaired in its own task at
  `dd52b5b`, with tests/ and the freeze lock in scope and every builder file out of it, so
  the pressure ran from the tests to the code rather than the other way. No assertion was
  weakened; three claims were restated rather than re-sized, because a second orbit is
  expressible now and "no key exists" needs a sequence no legal order produces.

- [resolved] **A frozen phase 12 test counts a population this phase deliberately grows.**
  `test_the_squeeze_refusals_are_untouched` asserts 132 two-raise corpus refusals as a
  guard that the normaliser finds no nearer spot. It measures 133. The extra row is
  `t6/d100/BB/SB:call,BB:raise@3,SB:raise@12`, the limped second-orbit decision the
  decision record named at stage 2: it had no key at the branch point, so a filter
  requiring one could not see it, and giving it a key is this phase's own work. The claim
  the test makes is correct and its population is a superset of the claim. Filed as
  `SQUEEZE-REFUSAL-COUNT-INCLUDES-A-SECOND-ORBIT-ROW`. Repaired at `dd52b5b` by narrowing
  the population to the claim - repeated-position keys are excluded - rather than by moving
  132 to 133, which would have been fitting the number to the measurement.

- [resolved] **The quality gate and the contract's forbidden shortcuts now contradict each
  other.**
  This phase moves two registered facts: `corpus_inexpressible_refusals` 19 to 0 and
  `corpus_distinct_refused_spots` 78 to 159. `run_full_quality_gate`'s fact-drift check
  reports `reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md` and `backlog.yml` as
  stating stale numbers. The contract forbids editing a committed audit packet to correct
  a number this phase re-measures, and it is right to: a packet is the record of what a
  phase found, and rewriting it destroys the only evidence a number ever changed. Both
  rules are correct and neither can give way from inside this task, because
  `scripts/repo_facts.py` and `scripts/run_full_quality_gate.py` are check-script
  territory. Filed as `FACT-DRIFT-CANNOT-EXEMPT-A-HISTORICAL-AUDIT-PACKET`; it needed a
  ruling rather than a repair, and Taylor ruled on 2026-08-20 that the packet is a snapshot
  of what phase 08 believed. Closed by MAINT-25 at `36d867a`, which removed the packet from
  every fact's `quoted_in`. No fact was retired: the three it was the only quoter for point
  at `docs/CORPUS_COMPARISON_LIMITS.md`, which MAINT-10 wrote to be the live home for
  exactly these caveats and which now states all three in its own prose, so every number
  stays checked where a reader might act on it.

- [resolved] **The GTOpen source card's stated headroom no longer matches the tree.** The re-keyed
  artifact is 1,918 bytes bigger, and `headroom_bytes` on
  `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json` is the 20 MB
  limit less the total bytes under `data/artifacts/**`, so a phase committing any artifact
  invalidates a card belonging to a different one. Regenerating it needs
  `scripts/extract_gtopen_preflop.py` and the exports directory, neither in scope. Filed
  as `SOLVER-EXPORT-CARD-HEADROOM-COUNTS-THE-WHOLE-ARTIFACT-TREE`. Re-settled at `d31d3ef`
  by the extractor's own fixed-point rule rather than by hand, with the card in scope for
  that one field. The design defect - a card stating a number about a directory it does not
  own - stays filed, because fixing it means editing the phase 10 extractor.

## Non-blocker

- **The shortcut the contract named was not taken, and the check for that is arithmetic
  rather than a promise.** The size is in the key and the abstraction is in the lookup:
  `spot_key` renders `CO:raise@2.5`, and `SolvedPriceIndex.normalise` moves an observed
  price to the nearest one the loaded keys declare, per exact prefix. Dropping the size
  from the key would still have passed every lookup test in the frozen file; what makes it
  visibly not taken is that `price_substitutions` is non-empty on 969 of 2,758 answered
  corpus decisions, which is only measurable because the key can tell two prices apart.

- **The corpus agreement rates did not move at all, and that is the result rather than an
  absence of one.** 499 hands, 3,048 decision points, 290 refusals, 439 of 456 and 2,155
  of 2,302 - identical to the branch point and to the Phase 08 packet. A finer key would
  have moved them only if it changed which cell a decision reached, and it does not,
  because an unsolved price normalises back to the one cell the coarse key hit. The report
  says this in those words rather than presenting a null result as a clean bill.

- **The self-play figures did move, for a reason a reader will otherwise misread.** 128
  refused hands became 126 and 472 measured became 474. `PreflopChartStrategy._seed`
  hashes the spot key into the seeded draw, so re-keying re-seeds every mixed cell and the
  run walks a different path through the same distributions. It is not a coverage change.
  The report attributes it and says why; the audit packet must repeat it, because the two
  reports sit next to each other and the number looks like coverage.

- **Four modules crossed the 500-line cap and were split, and the cap was right each
  time.** `schema.py` was holding the vocabulary and the artifact container;
  `lookup.py` the resolution walk and the ruled abstraction; `importer.py` strict JSON
  reading and poker validation; `vocabulary_report.py` measurement and rendering. Each
  seam is a real one on the MAINT-09 precedent. `schema.py` re-exports the vocabulary
  because every caller has always reached for it there and there is still exactly one
  derivation behind the name - worth watching, since a re-export is how a second
  derivation would eventually hide.

- **The refusal inventory grew from 78 distinct spots to 159, and it is not a regression.**
  A spot the chart holds no candidate price for keeps the price it was actually asked at,
  so one uncovered squeeze at eleven different three-bet sizes is now eleven rows rather
  than one. That is more actionable, not less - the rows name the real prices a chart
  phase would have to solve - but it is a fact about a committed report that changed
  shape, and the packet should say so.

- **Two probe labels in `generate_preflop_chart_report.py` were already wrong before this
  phase.** One read "uncovered spot: cutoff facing a lojack open" against a spot the
  committed report shows as a hit, and the four-bet probe was labelled by a limitation
  this phase removes. Both corrected in the same edit that gave the probes their sizes,
  and recorded here because the file entered scope for a mechanical reason.

## Alignment

- `DOCS-CARRY-STRAY-WRITE-TOOL-CLOSING-TAGS` - the phase 12 contract ends with a literal
  `</content>` and `</invoke>`, and the decision record, the active ExecPlan, four phase 12
  stage review notes and one completed MAINT ExecPlan each end with a stray `</content>`.
  Tool markup that a previous session's writes leaked into committed documents. It renders
  as text to every reader and nothing in the gate looks for it. Not fixable from
  implementation mode for the contract and the decision record, and not this stage's work
  for the rest.
