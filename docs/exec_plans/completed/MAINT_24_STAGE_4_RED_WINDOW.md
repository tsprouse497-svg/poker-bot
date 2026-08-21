# ExecPlan: MAINT-24 - The stage-4 red window hid its own assertions

Task: `MAINT-24-stage-4-red-window`, `task_mode: maintenance`, opened from `f6b2c84` in the
phase 12 lane worktree.

## Objective

`scripts/loop_stage.py`'s `run_command` returned only the last 4,000 characters of a gate
command's output, and `red_for_the_right_reason` searched that window for an assertion.

pytest ends with its `FAILED` summary list, which names every failing test and quotes none of
them. Phase 12's stage-4 suite produced 57,328 characters containing 38 occurrences of
`assert`, none of them in the final 4,000, so a suite that is nothing but assertion failures
read as "the test file is probably broken rather than describing behavior" and stage 4 refused
to advance.

Second time this check has rejected the exact state it exists to require. MAINT-04 was the
first, when it rejected a red that came from the implementation module not existing yet.

## Scope

Approved: `scripts/loop_stage.py`, `tests/test_loop_machinery.py`, this plan.

Deliberately out of scope:

- `verification/freeze.lock`. Adding a test to `tests/test_loop_machinery.py` does move the
  recorded count, and re-freezing is stage 5's act rather than a maintenance task's.
  `check_test_freeze` stays red until then, which it already was because
  `tests/test_spot_vocabulary.py` is not in the lock yet.
- `docs/LOOP.md`. The clip is an implementation detail of the driver rather than a rule about
  the loop, and the reasoning belongs in the docstring where the next reader of that function
  will be.
- Everything phase 12 owns. This task exists because `docs/LOOP.md` names a builder diff under
  the check scripts as a halt condition, so the fix could not happen inside the phase task.

## Delegation Plan

- No-delegation exception: the standing instruction in this account is not to call the Agent
  tool unless the operator requests it, so `AGENTS.md` step 6 cannot be satisfied and step 10's
  self-review fallback applies. One-function change with two tests; the review is the diff.

## Slices

- [x] **S1.** `run_command` takes `clip: int | None = 4000` and returns the whole output when
      `clip` is None. The default is unchanged, because a reason printed to a human wants the
      end of a failing run and not four thousand characters of its start.
- [x] **S2.** `check_tests_authored` is the one caller that reads the text rather than printing
      it, so it passes `clip=None`.
- [x] **S3.** Two tests. One builds an output whose only assertion sits outside the tail window
      and asserts the check still recognises it; the other pins that the clip is a parameter
      with the old default and that `check_tests_authored` opts out, so a later refactor cannot
      quietly restore the bug by dropping the argument.

## Verification

`pytest_loop_fleet`, `ruff_check`, `check_scope`. `pytest_loop_machinery` is not a registered
command; `tests/test_loop_machinery.py` runs under `pytest_loop_fleet` and the catch-all
`pytest`.

`test_every_mutation_applies_exactly_once_to_its_file` is red before and after this task, and
not because of it: phase 12 authored four canaries at stage 4 against text stage 6 has to
produce. That is the expected mid-phase state and `verification/mutations.yml` says so in its
own header.

## Outcome

Stage 4 of phase 12 can now see that its suite is assertion-red. Nothing else in the driver
changed, and no clipped output that a human reads got shorter or longer.

The finding is filed as `LOOP-STAGE-4-RED-WINDOW-HIDES-ASSERTIONS`, status done, so the next
agent that meets a stage-4 refusal has the diagnosis rather than the symptom.

## Next Agent Bootstrap

The phase 12 lane resumes at stage 4. Restore the phase task before advancing:
`task_id: phase-12-tests`, `task_mode: implementation`, `base_commit` at this task's commit,
and `approved_scope` back to `tests/test_spot_vocabulary.py`,
`verification/mutations.yml`, `verification/freeze.lock`, `scripts/run_verify.py`,
`reports/phase_audits/reviews/PHASE_12_SPOT_VOCABULARY/**`.

```
cd ~/projects/poker-bot-worktrees/phase-12
uv run python scripts/loop_stage.py --phase 12
uv run python scripts/loop_stage.py --phase 12 --advance
```
</content>
