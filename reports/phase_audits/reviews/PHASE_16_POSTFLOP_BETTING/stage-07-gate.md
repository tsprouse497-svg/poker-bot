# Phase 16 stage 7 review: the gate, the canary correction, and the record written around it

Independent read-only review by lane R6, 2026-09-21. I wrote none of the work under review and
touched nothing in the lane worktree except this file. Every figure below is one I produced.

Stage 7 changed three reviewed paths and this note covers all three:

- `tests/test_postflop_artifact.py` at `5df2826`, the frozen-test correction, with
  `verification/freeze.lock` behind it.
- `backlog.yml` and `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md` at `d80df13`, which are
  partly a record of my own findings and which I read as a reviewer rather than as their subject.
- `reports/active/verify_results.json` and `reports/active/latest_verify.txt` at `f118b9e`, the
  gate record.

## How the measurements were taken

Everything mutated was run against an rsync copy of the lane worktree in a scratch directory, never
against the worktree itself. The copy's `.git` pointer was repointed at a path that does not exist
before anything ran, so no command inside the copy could reach the real worktree's git
administrative directory. No `git checkout`, no `git stash`, no revert of any kind. The lane tree
was confirmed clean afterwards: `git status --short` empty, and `grep -rn "if False and" src/`
returning nothing.

I did not run `scripts/run_verify.py` or `check_gate_bite` against the lane tree, by instruction and
by judgement - a mutation run against a tree while its stage is closing is the hazard this repo has
already been bitten by.

## The correction itself: the five questions

**1. Does the new test still assert what the old one asserted?** Yes, and more sharply. The
criterion is the contract's - a committed size that cannot be played is refused at import rather
than at the table. The assertion is unchanged (`with pytest.raises(error)`), the inflation factor is
unchanged (`effective_stack_bb * 10`), and only which action gets inflated moved. It is now stronger
in one respect worth stating: on the clean tree the inflated raise is refused by
`check_size_is_playable` and by nothing else, so "it raised" and "the playability check fired" are
now the same statement. Under the old test they were not.

**2. Is the kill set the same or larger?** Larger, strictly. I ran the four-cell matrix myself - old
test file and new test file, against the playability check disabled alone, the on-menu check
disabled alone, both disabled, and neither:

| | no mutation | playability off | on-menu off | both off |
|---|---|---|---|---|
| old test | pass | **pass** | pass | fail |
| new test | pass | **fail** | pass | fail |

Old kill set is {both}. New kill set is {playability, both}. Old is a strict subset of new, so
nothing that used to die to this test can survive it now, and no coverage was traded for the green.

The author's stated premise was wrong, though, in the direction that flatters it. The commit message
at `5df2826` and the scope entry at `4a6752b` both say the old test's whole kill set was the check
the mutation disables. Disabling that check alone left the old test **green**. Its single-check kill
set was empty - the test was vacuous rather than narrow, and it died only when both checks went at
once. The conclusion survives the correction to its premise, but a false premise supporting a true
conclusion is exactly what misled three lanes here in the first place. This is corrected at
`d80df13` and I have checked that correction below.

**3. Is the new fixture selection stable?** Yes, and it fails loudly where the old one went quiet.
`assert raises, "no committed cell offers a raise..."` fires with a named message if the committed
sample ever loses its raise. Only `rainbow-dry-high-facing-a-bet` offers one among the four
committed cells; the other three offer a check and two bets. If a sample is added that sorts earlier
and also offers a raise, `raises[0]` picks a different cell and the behaviour is identical, because
decision 14 exempts every raise from the on-menu check.

**4. Did anything get moved to match the code?** No. One hunk in one file. No expected number moved,
no assertion's meaning changed, no tolerance touched. 700 lines before and 700 after, against the
700-line cap, paid for out of the superseded docstring paragraph.

**5. The freeze lock.** Verified, and that is all that moved. The full-file diff against the parent
is one line: the digest for `tests/test_postflop_artifact.py`. I recomputed it with `shasum -a 256`
and got `5235cbaa814a59c18e8bed391ddbae7bf03860bfa1f67d74691cd5e2ea2c17ae`, exactly what the lock
carries. `test_functions: 38` is unchanged and pytest independently collected 38 in that file - one
selected, 37 deselected. `test_function_floor: 1202` and `schema_version: 1` are unchanged, and no
other file's entry moved.

## The two measurements, reproduced

Full six-file `pytest_postflop_betting` command set, in the scratch copy:

- Unmutated: **238 passed in 5.75s**.
- With `postflop-unplayable-size-imports` applied: **1 failed, 237 passed in 5.60s**. The single
  failure is
  `TestTheImporterRefusesRatherThanRenders::test_a_committed_size_that_cannot_be_played_is_refused_at_import`,
  and it fails as pytest's did-not-raise. Nothing else moved.

Both reproduce what the correction reported, from a run rather than from the report.

## The gate, as a measurement

I read the committed `reports/active/verify_results.json` rather than re-running anything.

- `all_passed` is true, **50 commands**, zero failures, zero duplicate command ids.
- `check_gate_bite` is present and passed, at 825.5 seconds - so the green also says the committed
  mutations make the gate fail.
- `pytest_postflop_betting` passed at 5.99 seconds and `generate_postflop_betting_report` at 3.64.
- `check_scope`, `check_test_freeze` and `check_file_sizes` are all in the run and all passed, which
  is what says the narrowing at `d80df13` is consistent with the diff from its own `base_commit`.
- Timing puts the run on the right tree. The record is stamped 18:43:41 and its durations total
  984.7 seconds, so the run began about 18:27:16 - after `d80df13` at 18:10:58, and recorded by
  `f118b9e` at 18:43:55.

What I have verified is the internal consistency and the timing of a record the coordinator's own
run produced. I did not observe the run. That distinction is stated rather than smoothed, and the
freeze digest I recomputed by hand is what ties the run to the corrected test file.

## The record written around the correction

**The scope narrowing at `d80df13` is right, including the part that was my finding.** All seven
distinct test paths leave `approved_scope` - artifact, key, fallback components, simulator, query
recording, solve driver, betting - along with both listings of `verification/freeze.lock`. I counted
the removed lines against the previous version rather than taking the number: seven distinct test
paths, each of which was writable by an implementer until this commit. `base_commit` moves to
`5df2826`, which puts the corrected test outside the diff that scope is measured over, so the
narrowing does not read from here on as the builder writing its own tests.

**Both corrections to the coordinator's own record are accurate in substance and in the numbers.**
The first - that the re-open granted permission already granted and left each path listed twice - is
what I found, and the reason it matters is stated correctly: a mechanical guard cannot object to a
path that is listed, which is why a narrowing owed from an earlier re-open stayed invisible. The
second states the matrix result correctly, including that the old single-check kill set was empty
rather than small, and that the new one is {playability, both} against the old {both}. The ExecPlan
correction under "Things that will bite you" carries the same result and does not overstate it.

**The two backlog entries say what I measured and not more.** The first correctly limits itself to
prose - it states that `check_gate_bite` reads the file, find, replace and witness fields and that
all four are correct, which is true and is why nothing is red on it. The second attributes the
figure to me and states it as mine: disabling the on-menu refusal in `postflop_sizing.py` alone
leaves the whole `pytest_postflop_betting` set at 238 passed. That is my measurement, taken in the
isolated copy, and it is reported at the strength I took it. Its supporting figures check out too -
3.0bb into a 5.5bb pot is 54.5 percent, on neither the 33 nor the 75 entry; no mutation in
`verification/mutations.yml` points at `postflop_sizing.py`; and grepping the artifact test file for
the word menu returns only the two docstring lines the correction added.

## Blocker

None.

The correction preserves intent, enlarges the kill set strictly, moves no expected number and no
tolerance, and moves exactly one digest in the lock. The gate record is green on all fifty commands
with the mutation sweep among them. The two findings I raised outside the original brief are filed
with backlog ids rather than left in a commit message, and the two errors I found in the
coordinator's own record are corrected in the places a later reader will actually look.

## Non-blocker

- The corrected test asserts the error **class**, `PostflopArtifactError`, rather than the
  `postflop:unplayable-size` refusal code. Today that is harmless, because nothing but the
  playability check refuses an oversized raise - which is exactly what the matrix above proves. But
  if a later phase ever puts a check on raises as well, this test goes vacuous again in precisely
  the old way, and the new assertion that a raise cell exists will not catch it, because a raise
  cell will still exist. The fix is to bind the assertion to the code. It is not applied here
  because it costs a line and `tests/test_postflop_artifact.py` is at 700 of its 700, so it would
  have to buy the line from somewhere else in a file that is now correctly out of scope. Recorded
  for whichever task next opens that file with room in it.
- The positive control for the cell the corrected test inflates is cross-file rather than in-class.
  `test_the_good_committed_sample_imports` imports the first sample alphabetically, which is a bet
  cell, not the raise cell. An importer that refused the raise cell unconditionally would satisfy
  the corrected test. It would not survive the command set, because
  `test_at_least_one_committed_spot_produces_a_raise_with_an_amount` in `tests/test_postflop_betting.py`
  requires that cell to load cleanly, and it is the only committed cell offering a raise. So the
  control is real, just further away than it was. Worth knowing if either file is ever split.
- The scope narrowing is the right fix but it is discipline, not enforcement, until the next stage
  measures it. `check_scope` passed in the recorded gate, which says the current diff obeys the
  narrowed list; it says nothing about the seven files that were writable before it. Nothing
  suggests they were written - the freeze digests would have moved - but the guarantee for that
  window comes from the freeze check rather than from scope.

## Alignment

- `A-MUTATION-DESCRIPTION-ARGUES-THE-DEFENCE-THAT-FAILED` - the canary's own description in
  `verification/mutations.yml` opens with the word bet where it means raise, never uses the word
  raise at all, and closes with the menu-arity paragraph arguing that a canary refused by a check
  other than the one it disables survives the command it names. That sentence describes what then
  happened. I ruled that it does not clear the bar for a seventh scope re-open and a full gate
  re-run on its own, since no check reads the prose and all four executable fields are correct, but
  that it must not stay in a commit message either, because the next lane whose canary misfires
  reads the description and not the git log. Filed, with the correction it needs written into the
  entry, to ride to whatever task next opens that file.
- `NOTHING-CATCHES-THE-IMPORT-CHECK-THAT-REFUSES-A-BET-OFF-THE-COMMITTED-MENU` - disabling the
  on-menu refusal in `postflop_sizing.py` alone leaves the whole `pytest_postflop_betting` set at
  238 passed. No test catches its removal and no mutation points at that module. This is the check
  that silently absorbed the unplayable-size canary for the whole of stage 6, which is how that
  canary came to survive, and it is a better candidate for the missing canary that
  `THE-PHASE-S-CENTRAL-MODULE-HAS-NO-MUTATION-CANARY` asks for than anything currently proposed.
  Neither the test nor the canary can be written in this task now that the stage-5 narrowing is
  correctly back on both paths, which is the right trade and the reason this is an alignment item
  rather than a repair.
