# Phase 12 stage 7 review - the gate and the bite

Read-only pass over `git diff 772e283 -- scripts/run_verify.py tests/test_spot_vocabulary.py
tests/test_spot_vocabulary_downstream.py`, against `AGENTS.md` and
`docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`. No gate runs inside the review.

Question the driver asked: hand-written work at this stage escaped an earlier one, so a
canary added here is a canary nobody reviewed at stage 4 - review it now.

The literal answer is that no canary was added here. All four were authored at stage 4 and
reviewed then, which is the miss phases 08, 09 and 10 each made and this phase did not. What
this stage added is a *test*, and it arrived for the reason the driver's question is really
about: `check_gate_bite` proved the suite was not covering a behaviour it appeared to.

Coordinator-written, as the phase's no-delegation exception records.

## Blocker

None.

## Non-blocker

- **The surviving canary was a real finding, and the repair went the right way.**
  `a-folded-seat-may-act-again` survived `pytest_spot_vocabulary`.
  `test_a_seat_the_action_already_passed_cannot_act_later` aims at the fold rule with hero
  on the button, so the ring walk reaches hero before it reaches the folded seat and the
  rejection comes from the neighbouring rule that hero can never be one of the seats the
  walk folds. Both rules are correct; the test could not tell them apart. The repair is a
  test that puts hero out of the walk's path rather than a canary aimed at something easier
  to catch, and it was checked in both directions before being written: with the rule in
  place the sequence raises, with the rule mutated away it returns
  `t6/d100/LJ/LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5,BB:raise@50`. That is the shape a
  canary repair should have, and it is worth contrasting with Phase 07, where two of three
  surviving canaries turned out to be authoring errors in the canaries themselves.

- **A test passing for the wrong reason is a defect stage 4 cannot see, and this is the
  second kind of it this phase has met.** Stage 4's check requires the phase's pytest
  command to be red, and a suite red on a missing module is red without any assertion
  running - `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`. This is the other half: an
  assertion that does run, and passes off a rule other than the one it names. Nothing at
  stage 4 could have caught it, and `check_gate_bite` did, which is the argument for the
  bite check stated as a result rather than as a principle.

- **The file split is structural and the seam is real.** `test_spot_vocabulary.py` now pins
  what a key can say; `test_spot_vocabulary_downstream.py` pins what the repo does once it
  can say it - the normaliser, the query and the answer, the corpus, the report. That is
  the same seam the source split took between `spot_key.py` and everything reading it, and
  between `vocabulary_measures.py` and `vocabulary_report.py`, so the tests are now
  organised the way the code is. No test was deleted, renamed or weakened in the move: 68
  before, 69 after, and the one added is the isolating test above.

- **`scripts/run_verify.py` entered scope for one command entry, and that is worth naming
  rather than passing over.** The registry is what a phase is measured by, and a phase task
  editing it is a phase editing its own gate. What this edit does is name a second file for
  a command that already existed, on the precedent `pytest_preflop_artifacts` and
  `pytest_solver_export` both set. No command was added, removed, or had its meaning
  changed, and `check_repo_consistency` still holds. Worth watching only in the sense that
  the precedent makes the next such edit easier to wave through.

- **The gate is green across all 43 commands and every canary now bites.** Including the
  two this phase declared, `pytest_spot_vocabulary` and `generate_spot_vocabulary_report`,
  which is the thing phases 08, 09 and 10 each shipped without.

- **Two concurrent verify runs raced during stage 6 and left a mutated
  `scripts/loop_stage.py` in the tree.** Operator error rather than a repo defect, and the
  guard `MUTATION-SENTINEL-IS-COMMITTABLE` produced worked exactly as designed:
  `check_scope` refused the commit until the sentinel was cleared and named the file to
  restore. Recorded because the incident is evidence about that guard, and because the
  earlier `check_gate_bite` failure it caused could have been mistaken for this stage's real
  finding.

## Alignment

None. The stage-6 alignment item, `DOCS-CARRY-STRAY-WRITE-TOOL-CLOSING-TAGS`, is still open
and unchanged by anything here.
