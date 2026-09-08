# MAINT-33 independent review

Read-only review of `b5eb610..5d3281d` by a subagent that wrote none of the work, on
2026-09-08. The question it was given: does the sweep still refuse a bug that no test
catches?

**Its verdict.** The narrowing is sound for 70 of the 75 mutations. The green sweep at
`b5eb610` required every command in each `must_fail` list to go red, so for the 41 lists
that only dropped `pytest` the surviving command was already measured red under that exact
mutation, against source this task does not touch. The design is self-policing: the sweep
still demands red from every named command, so a witness that stops biting turns the sweep
red rather than quiet. What would have changed its mind: evidence that the 2026-09-07
sweep was partial or ran against different `find` targets. It was neither.

The five mutations pointed at the new `pytest_loop_machinery` were the exception, and the
blocker below.

## Blocker

- [resolved] **`pytest_loop_machinery` was a witness that could not fail to fire, for the
  exact reason `pytest` was exempted.** The command ran `tests/test_loop_machinery.py`,
  which holds `test_every_mutation_applies_exactly_once_to_its_file`. That test counts each
  mutation's `find` string in the file it names, so it is red while any mutation at all is
  applied, whatever that mutation does. Five mutations rested on it, including this task's
  own new canary for the check that makes the whole narrowing safe: the safety net's alarm
  was unfalsifiable. Real behaviour tests do cover all five, so nothing was broken, but the
  sweep's verdict on them carried no information, and two sentences in the diff claimed
  otherwise. Fixed by deselecting that one test from `pytest_loop_machinery` in
  `scripts/run_verify.py`, with the reason in a comment beside it. The test still runs, in
  the base `pytest`. `test_the_narrow_machinery_witness_cannot_answer_before_it_is_asked`
  in `tests/test_mutation_sweep.py` holds the fix in place. The reviewer verified the
  collateral before proposing it: `check_pytest_commands_hold_tests` filters on a `.py`
  suffix, so the `::` argument is ignored and both files are still seen.
  The original finding was reasoned rather than run, because the reviewer was barred from
  applying a mutation to the tree. On the verification pass it applied all five in a copy of
  the worktree in scratch, never the live tree, and ran the registered command with the
  deselect: all five exit 1, and in every case the first failure is a behaviour test rather
  than the bookkeeping one. For the new canary the whole claim rests on a single test,
  `test_a_witness_the_derived_gate_does_not_run_is_reported`, because the two sibling tests
  that call the same check assert an empty error list and so pass when it is made vacuous.
  One thread, and it is the right one.

- [resolved] **A detected bad restore deleted the sentinel that says the tree is broken.**
  `restore_errors` is the first thing in the repo that can know a restore came back wrong,
  and the `finally` block recorded the error and then unlinked the sentinel unconditionally.
  The sentinel is what `check_scope` reads to refuse a commit while a defect is live, added
  after `MUTATION-SENTINEL-IS-COMMITTABLE` bit twice. The one moment the guard is provably
  needed was the one moment the code removed it. Fixed in `scripts/check_gate_bite.py`: the
  sentinel is unlinked only when the restore verified, and the sweep now stops at that point
  rather than applying the next mutation to a tree whose state nobody knows.
  `test_a_failed_restore_keeps_the_sentinel_that_blocks_a_commit` and
  `test_the_sweep_stops_rather_than_mutating_a_tree_it_no_longer_understands` cover both
  halves. On the verification pass the reviewer added the reason this is better rather than
  merely safer: `check_mutation` reads its `original` fresh from disk, so the mutation after
  a bad restore would have adopted the corrupt file as its baseline and restored to it,
  laundering the damage into what the sweep believes is clean and reporting 70 downstream
  verdicts taken against an unknown tree.
  Two follow-ups came out of that pass and are fixed at `f317014` and after it: the stop left
  the end-of-sweep health pass running over the tree it had just disclaimed, which would have
  written reports derived from defective source, and the test that proved the stop gave its
  fake mutations no witness, so it could not have noticed. The health pass is now skipped on a
  stop, the stop message says the reports were not rewritten, and the test asserts no command
  runs afterwards.

## Non-blocker

- **"Strictly more" was too strong, and is corrected.** The end-of-sweep health pass is
  more commands and later, not strictly more. The removed per-mutation run put the whole
  suite on the restored tree after every mutation; the union no longer contains `pytest` at
  all. Byte comparison covers the mutated source file but not side-effect state: mutation
  A's commands write reports from defective source, and mutation B's verdict is then taken
  against whatever A left. No live instance was found and the risk is structural. The
  docstring in `health_command_ids` now says what it does and what it does not.
- **The worker flags can turn a non-catch into a catch, not the reverse.** A real failure
  on any worker still exits non-zero, so a red cannot look green. The open direction is a
  worker that dies of something unrelated, which the sweep would read as caught. Recorded
  in the comment beside `PARALLEL_WORKER_FLAGS` as the thing to suspect if a mutation ever
  looks caught for a reason nobody can reproduce serially.
- **`must_fail` was read three different ways.** `check_mutation` indexed it, the other two
  readers used `.get(...) or []`, and an empty list passed the new consistency check
  vacuously. Aligned by validating at the point the file is read: `load_mutations` now
  refuses a mutation that names no command, because that is not a weak claim but no claim.
  `test_a_mutation_that_names_no_witness_is_refused_when_the_file_is_read` covers it.
- **The phase-14 comment block in `verification/mutations.yml` stated two false things in
  the present tense.** The reviewer's ruling was to keep the history and date it, as the
  four sibling descriptions in the same file were dated, because left as written it was the
  most misleading passage in the repo for the next person deciding whether a narrow pytest
  command is a safe witness. Done, both sentences.
- **`docs/LOOP.md` stage 7 table row** still read as two criteria. Rewritten to match the
  stage's actual check.
- **The backlog amendment restated a clause its own change falsified.** "Of which none
  begins `pytest`" stopped being true the moment `pytest` joined the unnamed set. Corrected,
  and the correction says what the figure no longer means.
- **The ExecPlan did not describe the tree it sits beside.** Lane statuses, slices, the test
  file that moved, and the Outcome were all stale. Updated at closeout.
- **The Outcome then recorded the saving with the wrong number.** It said 148 command runs
  before, which is 74 times 2, a mutation count where a command-run count belongs. Measured at
  `b5eb610`: 74 mutations carrying 125 `must_fail` entries, each run twice, so 250. After: 104.
  Caught on the verification pass, and worth being right because it is the figure the saving is
  recorded as.
- **The claim that every reader can now index `must_fail` reached further than the change.**
  `load_mutations` validates, and the sweep can index. `check_repo_consistency` and
  `tests/test_quality_hardening` load the file themselves and still tolerate an absent list. The
  comment says so now.

## Alignment

- `MERGE-INTEGRATION-STILL-RUNS-THE-SWEEP-TWICE`: `AGENTS.md` and `docs/LOOP.md` both still
  prescribe "the full gate plus `check_gate_bite` run again" at merge integration, which is
  the same duplicate this task deleted from stage 7. Left alone because the ruling named
  stage 7 and `AGENTS.md` is not in this task's scope; correcting the doc alone would
  manufacture a contradiction, since `AGENTS.md` wins where they disagree.
- `A-NARROW-COMMAND-CAN-HOLD-A-TEST-THAT-REDDENS-FOR-EVERY-MUTATION`: the blocker above was
  an instance of a shape nothing detects. Any narrow `pytest_*` command whose files happen
  to include a registry-wide assertion becomes an unfalsifiable witness, and mutation
  coverage checks only that a command is named, never that it could pass under a mutation.

## Verification pass

The same reviewer re-read `5d3281d..f317014` after the fixes and reported no blockers. Its
verdicts: stopping on a bad restore is strictly better than continuing rather than a new risk;
the deselect is enough, on the single-thread evidence above; and nothing in the fixes is worse
than what it replaced. Its three findings on that pass are folded into the non-blocker list
above and all three are fixed.

## Checked and clean

Exactly four mutations have a report generator as their only witness, and they are the four
already filed under `SEAT-ORDER-REFUSALS-HAVE-NO-TEST`; no fifth. No mutation has an empty
`must_fail`. No named witness sits outside the derived gate. `check_gate_bite` is in
`BASE_GATE_CHECKS` after `pytest`, so removing stage 7's second call removed no check that
`run_verify.py` does not make, and asking before the gate rather than after is a straight
improvement given what the gate costs. `tests/test_loop_machinery.py` is byte-identical to
`b5eb610`. Only that one test file contains an assertion that fires on an arbitrary
mutation, so the contamination was confined to the one command.
