# MAINT-39 independent review - retiring phase 17

Reviewer: read-only subagent, wrote none of the work under review. Reviewed commit `cfafd58` against
base `65e87d2` in the `maint/39-retire-phase-17` worktree. No gate command was run. Commands run:
`git diff`, `git grep`, `git ls-tree`, `git ls-remote`, `scripts/loop_fleet.py` (read-only), the
derived-chart generator with `--output` pointed at a scratch file, and pytest on
`tests/test_derived_chart_report_cutover.py`, `tests/test_derived_chart_report.py`,
`tests/test_derived_chart_report_validators.py` and `tests/test_quality_hardening.py` (51 passed).
The tree was clean after every command.

## Checked and true, not repeated below

- Seven backlog entries carried `phase: 17` at `65e87d2`; none does now, and all seven new labels are
  valid (`scripts/quality_checks.py:41-53` plus `phase_status.yml`, which now lists 00-14, 16, 18-20).
- `pytest_corpus_verdict` and `generate_corpus_verdict_report` appear nowhere under `scripts/`, `src/`
  or `tests/` at `65e87d2`, so they were never in `COMMANDS`. No contract lists `"17"` in
  `depends_on` (phase 18 depends on 14; 19 on 16, 18; 20 on 16, 19).
- The lane's decision list is 742 lines at `7e0dd71`; the tag `retired/phase-17` resolves to
  `7e0dd71`; the committed lane pointer is stage 2 and the uncommitted one stage 3, as the entry says.
- The phase 17 contract is readable at `65e87d2`.
- Phase 14's contract is 300 lines before and after; the amendment replaces one line in place
  (`docs/phase_contracts/PHASE_14_CHART_CUTOVER.md:26`), names the backlog id, and says what is no
  longer true. It follows "Contract Amendments". Lines 57 and 232 still name phase 17, but both are
  phase 14's own rule and record, and line 26 now tells the reader the phase is gone.
- The generator reproduces `reports/active/latest_derived_chart_report.txt` byte for byte, and the
  derived-chart test files pass on it.
- `RETIRED-CHART-PIN-DISAGREES-BETWEEN-GENERATOR-AND-RULING` checks out against the bytes:
  `scripts/generate_derived_chart_report.py:195` pins `6f15724`, `git ls-tree 6f15724` holds
  `six_max_100bb_rakefree.json`, `git ls-tree d046ac9` holds `six_max_nl25_100bb.json`, and phase 14's
  decision 7 (`PHASE_14_CHART_CUTOVER_DECISIONS.md:1204`) says the report reads `d046ac9`.
- Dropping the lane's fifth entry, about a second agreement computation, was right. The generator it
  warned about will never exist, and the one other generator that prints corpus agreement already
  shares the single code path (`scripts/generate_derived_chart_report.py:3604-3605` calls
  `compare_committed_sample`). The four carried items match the lane's stage-01 and stage-02 alignment
  sections one for one. Nothing else on the lane branch needs to be on main: its ExecPlan, decision
  list and two review notes are phase 17 working papers, and the tag keeps them.
- `docs/CORPUS_COMPARISON_LIMITS.md:49` has the "Real players are not an oracle" heading both roadmaps
  cite.

## Blocker

- [resolved] **The derived-chart report still tells a reader that a later phase renders the corpus verdict.**
  `scripts/generate_derived_chart_report.py:3560-3562` (the `PREAMBLE`), committed at
  `reports/active/latest_derived_chart_report.txt:9-11`: "Nothing below is a grade on the new chart.
  ... and the corpus verdict belongs to a later phase." That is the first paragraph of the report, and
  it contradicts the task's own new text at `:1284-1286` of the same report ("so no phase renders
  one"). It is exactly what the ExecPlan names as an expected output
  (`docs/exec_plans/active/MAINT_39_RETIRE_PHASE_17.md:37`, "no live document saying a phase renders
  the corpus verdict"), and the file is inside `approved_scope`. No test pins the phrase (`git grep`
  over `tests/` finds nothing on "belongs to a later phase" or the preamble). Suggested fix: end the
  sentence "... real players are not an oracle, and no phase renders a corpus verdict." Then
  regenerate the report.

## Non-blocker

- [resolved] **A carried entry quotes a sentence this task just deleted.**
  `PREDICTION-CANNOT-BE-BLIND-TO-A-COMMITTED-MEASUREMENT` (`backlog.yml:10350-10352`) says the
  derived-chart report hands phase 17 its deltas "saying so in as many words: 'so that the later phase
  has the measurement its band will be drawn on'". MAINT-39 reworded that line
  (`scripts/generate_derived_chart_report.py:3315-3316`), so the quote is no longer in the tree. The
  defect still stands, because the report still prints the per-opener deltas
  (`reports/active/latest_derived_chart_report.txt:1319-1323`). The carrying note should add one
  clause: MAINT-39 reworded the quoted sentence, but the deltas are still printed.
- [resolved] **The retirement entry says something is done that has not happened yet, and "kept under the tag"
  currently means kept on one disk.** `backlog.yml:387` says "the worktree is removed", but
  `git worktree list` still shows `poker-bot-worktrees/phase-17` on its branch, and the ExecPlan lists
  that removal as an open slice (`MAINT_39_RETIRE_PHASE_17.md:56`). More important,
  `git ls-remote origin` shows neither `refs/tags/retired/phase-17` nor the phase 17 branch. After
  the branch is deleted, the lane's decision list and review notes exist only in this one local
  repository. Push the tag before deleting the branch (`git push origin retired/phase-17`), and do
  both before the merge, or reword the entry to say what will happen.
- [resolved] **One backlog entry still names phase 17 as the measurement that would catch it.**
  `COMMITTED-SPOTS-NEVER-FLAT-A-RAISE` (`backlog.yml:6211-6212`): "the corpus measurement that would
  catch it is phase 17's". It is filed against phase 16, so a sweep by label could not find it. Add a
  dated sentence saying phase 17 is retired and that phase 18's playing-strength measurement, or a
  re-solve, is now what would show it. Separately, phase 16 is completed and this entry is still
  deferred under its label. That problem predates this task.
- [resolved] **A re-homed entry states a fact a frozen test disproves.** `CHART-CANNOT-ANSWER-A-LIMPED-POT`
  (`backlog.yml:2244-2246`) says "today's chart answers exactly one limp-facing spot,
  t6/d100/BB/SB:call". `tests/test_spot_vocabulary_downstream.py:630-650` asserts that the chart holds
  no `:call` key and refuses all 52 limped decisions. The claim is older than this task, but the task
  just moved the entry to phase 19, which will use it as a work list. It needs a dated correction.
- [resolved] **`CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` under `sample-comparison` is acceptable but borderline.**
  Its closing paragraph asks for work on the chart itself (a rake-free or 2.25bb-open solve, starting
  with refused big-blind spots), which fits `charts` as well as the report. No change is needed. It is
  recorded so the choice is visible.

## Alignment

- [resolved] **Frozen tests still make phase 17 the owner of the report's text.**
  `tests/test_derived_chart_report_cutover.py:150-154` (docstring: "phase 17 re-registers the
  arithmetic"), `:172-174` (failure message: "the verdict is phase 17's") and `:177-179` (the
  assertion requires the prediction section to match `phase\s*17`, with the message "without saying
  which phase re-registers and reads it"). Also `tests/test_spot_vocabulary_downstream.py:640` ("the
  contract moves it to phase 17"). The assertion passes today only because the new text still spells
  "PHASE 17 was to". So the report can never drop the name of a retired phase without turning a frozen
  test red, and the failure message asks for something no phase now does. This task cannot open
  `tests/**`. It should file one `maintenance` entry that lists these four locations, beside
  `A-VOCABULARY-ASSERTION-WENT-VACUOUS-WHEN-THE-LADDER-MOVED`, so a task that may edit tests restates
  them.
- [resolved] **The fleet view still shows retired phases as live lanes, and nothing flags it.** Running
  `scripts/loop_fleet.py` shows two lanes: phase 17, still waiting on seven rulings, and phase 15,
  which MAINT-35 retired on 2026-09-21 and which still shows as a halted lane with rulings owed to
  Taylor. Neither phase is in `phase_status.yml`. So removing the phase 17 worktree fixes this task's
  ExecPlan check (`MAINT_39_RETIRE_PHASE_17.md:60-61`), but it leaves the phase 15 lane, and the
  review queue built from these lanes, asking Taylor questions about a phase that no longer exists.
  File an entry saying that `loop_fleet.py` and `review_queue.py` should flag or drop a lane whose
  `phase_id` is not in `phase_status.yml`. Whether to remove the phase 15 worktree the way this task
  removes phase 17's is Taylor's call.

## Resolution

2026-09-25, by the coordinator. The blocker is fixed: the report's opening paragraph now says no
phase renders a corpus verdict, regenerated. Non-blockers 1 to 4 are fixed with dated notes in the
entries named, and the tag is pushed to origin before the branch is deleted. Non-blocker 5 needs no
change. Both alignment items are filed in backlog.yml as
FROZEN-TESTS-STILL-NAME-PHASE-17-AS-OWNER-OF-THE-REPORT-TEXT and
THE-FLEET-BOARD-SHOWS-A-LANE-WHOSE-PHASE-WAS-RETIRED.
