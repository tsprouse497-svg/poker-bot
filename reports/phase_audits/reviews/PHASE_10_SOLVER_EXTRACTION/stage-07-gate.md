# Stage 07 Review - Gate (Phase 10)

Question asked: hand-written work at this stage escaped an earlier one. A canary added here
is a canary nobody reviewed at stage 4, so review it now.

Scope: the two canaries added to `verification/mutations.yml`, the two frozen-test repairs
that had to precede a green gate, and the prose changes the quality gate forced.

Reviewer: coordinator, read-only pass over the diff plus the `check_gate_bite` transcript.
Subagent delegation is switched off in this operator's sessions, so `AGENTS.md` step 6 cannot
be satisfied and step 10's self-review fallback applies.

## Blocker

None.

## Non-blocker

- **The first canary is aimed at the defect the module's own docstring warns about, and it is
  silent by construction.** `solver-export-hand-index-uses-the-grid-ordering` reverses
  `_GTOPEN_RANKS` so the class index is built high to low, which is this package's chart-grid
  ordering rather than GTOpen's. The mapping stays a bijection, so every strategy row still
  sums to 10,000, every node still re-resolves from its own path, the export still writes and
  reloads, and both gated orderings still hold - the range is simply wrong. That is the exact
  failure mode the phase exists to guard against, and it takes `pytest_solver_export` down on
  the index test and on the frequency test that compares against GTOpen's own `freq`.

- **The second canary is aimed at reach, and its `must_fail` list is short for a reason worth
  reading.** Dropping reach from the aggregate weighting fails `pytest_solver_export` and
  `pytest`, and it does not fail `check_solver_export_expectations` - which was the first
  version of the entry and was wrong. All eleven aggregates are read at nodes where the actor
  has not yet acted: the five first-in nodes, and the five big-blind nodes where the big blind
  has not acted either. Their reach is uniformly 1, so the mutation moves none of the eleven
  numbers by so much as a basis point. The reason is recorded on the mutation itself rather
  than in this note alone, because the next person to widen that list needs to know why it is
  short. It is also the sharpest thing this stage learned: decision 7's reach weighting, which
  the record calls the difference between an extraction that is right and one that is
  self-consistent and wrong, has no effect on any number the gate checks. What covers it is
  one frozen test against the captured payload, at a node behind a three-bet.

- **Two frozen-test repairs preceded the green gate, and both were latent since stage 4.** The
  reach bound (`== 0.0` against a captured `3.6852573e-08`) and an unsorted import block that
  fails ruff. Neither is a defect the implementation could fix, and both share one cause: the
  stage-4 check runs the phase's own pytest command and accepts a `ModuleNotFoundError` as a
  legitimate red, so no assertion in either file had executed and no linter had read them.
  Phase 08 shipped the same class of defect as a 101-character line. Each repair landed in its
  own task with the builder files out of `approved_scope`, so neither could reshape the
  implementation to suit the test it was repairing, and the freeze lock was rewritten with the
  file both times.

- **The quality gate's citation check reads prose, and three documents lost an argument to
  it.** `BACKLOG_ID` matches any capitalised hyphenated token in `docs/` or `reports/`, and
  GTOpen's re-solve button is written in the capitals its UI uses, so the gate reported a
  finding filed under an id nobody created. The escape hatch is `NOT_BACKLOG_IDS` in
  `scripts/run_full_quality_gate.py`, which this phase may not touch, so the prose changed
  instead. The check is behaving as designed - it is deliberately blind to whether a token is
  an id - and the cost is that a document cannot name an all-caps UI control.

- **`check_gate_bite` reports 35 mutations all caught.** That is the whole committed set, not
  a subset, and it includes the two added here. The number it proves is narrow: each named
  command can fail on the behaviour its mutation names. It says nothing about whether the
  tests behind those commands are strong, which is the limitation the quality report already
  prints beside the mutation-coverage check.

## Alignment

- `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` - the stage-4 blind spot named twice above.
  The driver accepts a missing module as a valid red by an explicit MAINT-04 ruling, which is
  right, and the consequence is that no assertion runs and no linter reads the file before it
  is frozen. Phase 08 paid once, this phase paid twice. Tightening it is a change to
  `loop_stage.py` and belongs to whoever owns the loop, not to a phase that noticed it.

- The three items filed earlier in this phase still stand and nothing here added to them:
  `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`, `DEFENCE-RELATION-NARROWER-THAN-THE-CONTRACT`
  and `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK`.
