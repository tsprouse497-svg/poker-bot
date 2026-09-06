# Stage 10 closeout review, phase 14

Independent read-only review. The reviewer wrote none of this phase and edited nothing but this file.

The question this stage asks: bookkeeping only, and a content change here belongs to an earlier stage
and should be named as one.

Diff reviewed: `a55a328c94fed820ce99bb96906e97989c33e51b..HEAD` over `backlog.yml`, the ExecPlan, the
audit packet, `scripts/generate_derived_chart_report.py` and
`src/poker_training_bot/data_pipeline/comparison.py`, plus the uncommitted working tree.

## What was re-measured rather than read

The bisect in the commit message and in `A-CANARY-READS-A-CRASH-AS-A-KILL` was reproduced
independently, outside this worktree, without running the gate. The generator was extracted at four
revisions, the canary's one-line mutation applied to each copy, and each run against artifacts built
by the frozen test's own recipe:

  72efe9d  commit-a-spot-above-the-exposure-threshold  exit 0, report written  (kills the mutation)
  72efe9d  drop-a-spot  exit 1, KeyError t6/d100/BB/BTN:raise@2.5 in orderings_section  (no kill)
  5e119cf  same result on both parameters
  25f0d76  both parameters crash, so nothing kills the mutation
  589e133  commit-a-spot-above-the-exposure-threshold  exit 0, report written  (kills again)

The committed report also regenerates byte for byte from the current script, and the tolerant lookup
was reverted to a strict one in a scratch copy and produced a byte-identical report, so the claim
that the fix changes no published figure is measured, not asserted. `verify_results.json` last
changed at 5e119cf before the closeout, and not at 25f0d76, which corroborates that the regressing
commit landed without a gate run.

## Blocker

- **[resolved]** The closeout is not finished, and two of `check_closeout`'s five conditions fail today: `CURRENT_TASK.yml` still reads `task_id: PHASE_14_BUILD`, `active_phase: "14"`, `task_mode: implementation`, a 30-entry `approved_scope` and `base_commit: d635b492a89ddf2b6bdd7a98855727daa9cd2a6b`, and the working tree is dirty with `STATUS.md`, `docs/PHASE_LEDGER.md`, `phase_status.yml` and the staged ExecPlan rename uncommitted. It must become `task_id: null`, `active_phase: null`, `task_mode: idle`, `approved_scope: []`, `base_commit: null`, with `standing_scope` and `forbidden_scope` untouched, and then the gate re-run and the closeout committed. The three conditions that do hold: phase 14 reads `completed` in `phase_status.yml`, the ExecPlan is filed under `docs/exec_plans/completed/`, and the tag exists. `STATUS.md` reading `Completed phases: 15` is correct arithmetic, phases 00 through 14, not an off-by-one.
- **[resolved]** 23 blocker bullets across 7 review notes are still unmarked, so `scripts/review_queue.py` reports 23 open human asks against phase 14 at the moment it is declared complete. Counted with the loop's own parser: stage-04-confirmation-review 3, stage-04-recut-review-mechanical 6, stage-04-recut-review-poker 4, stage-06-build-review-poker 2, stage-08-review-poker 3, stage-09-audit-mechanical 3, stage-09-audit-poker 2. The last five are exactly the ones the stage-9 commit message calls resolved; they were answered in prose inside `stage-09-audit.md`, but the loop releases a blocker only when the resolved marker sits on the bullet's own first line, and none of them carries it. The marker is the word "resolved" in square brackets, spelled out here rather than written, because writing it would mark this bullet closed. Phases 11, 12 and 13 each closed this directory at zero, so this is a phase-14 regression rather than a convention nobody follows. The reviews directory is inside `approved_scope`, so it is fixable now, and it must be fixed before the reset to idle empties that scope.
- **[resolved]** The ExecPlan was filed under `completed/` without the two sections the template and the closeout checklist require. `docs/exec_plans/TEMPLATE.md` carries `## Verification` and `## Outcome`; `docs/DEFINITION_OF_DONE.md` requires the outcome or retrospective filled in; the filed plan has neither, and its stage-6 and stage-9 lane tables are still headed ACTIVE inside a document that now says the phase is over. Phase 13's completed plan carries both sections and its Outcome is one paragraph, so the bar is small and known.
- **[resolved]** The stage-10 content change is named honestly in three places and missing from the fourth, which is the one that owes it. The commit message states the red gate, the surviving canary, the bisect and the repair; the packet says "Fixed at stage 10"; `A-CANARY-READS-A-CRASH-AS-A-KILL` says the same and adds what is still owed. The ExecPlan says nothing at all: no stage-10 entry, no lane row, and no no-delegation exception for a source fix and two new backlog entries the coordinator implemented itself at a bookkeeping stage. `AGENTS.md` "Coordinator Workflow" item 4 and the "Worker subagents handled implementation by default" line of `docs/DEFINITION_OF_DONE.md` both require that exception to be recorded as a reason about the work, before the work. Phase 13 hit the same situation and wrote a titled section for it, "The fourth fix round, at closeout, and why content arrives there", which is the shape this owes.
- **[resolved]** The tag `phase-14-complete` points at 589e133, a commit whose own tree says the phase is not complete: `phase_status.yml` reads `active`, the ExecPlan sits in `active/`, and `CURRENT_TASK.yml` reads `implementation`. Every prior phase tag points at a commit reachable from `main`, phase 13's Outcome records the tag riding its closeout commit, and `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION` records phase 10's resolution as tagging the closeout commit and then moving the tag onto the merge commit. The tag should move to the closeout commit once it exists, and onto the merge commit at integration.

## Non-blocker

- The fix belonged where it landed and should not have been sent back to an earlier stage, which is this review's answer to the stage's own question. It is one line in a script already inside `approved_scope`, no test file changed, `pytest_derived_chart` reads the same 111 passed and 4 skipped, and the committed report is byte-identical, measured above. Returning to stage 6 would have reopened a frozen build to repair a rendering helper that publishes nothing. What is missing is the record in the ExecPlan, not the decision.
- The fix cannot hide a genuine error on any path a good artifact reaches, because the disagreement it tolerates is already refused upstream. `measure()` runs `validate_spot_count` over the artifact's spot ids against the walk's spot keys, key by key, and any mismatch lands in `errors`, which `main` prints as `refused:` and exits 1 on before `render` is ever called. A tolerant lookup of the identical shape already sat at line 1690, `measured.walk.arrivals.get(key, 1.0)` in the arrival section, so the pattern is not new to this file.
- The comment above the fixed line, and the commit message, both overstate what changed. They say the heaviest spot is now "chosen over what the walk carries rather than by indexing it with a chart key", but the code still indexes the walk with a chart key: `max(three_bet_family, key=lambda key: measured.walk.arrivals.get(key, 0.0))`. The candidate set is unchanged and still comes from the chart; only the lookup became tolerant. The behaviour is right and the sentence describing it is not.
- No better repair exists inside `approved_scope`. Making `orderings_section` tolerant instead would move the crash one section along to `big_blind_section`, which indexes the same `t6/d100/BB/{opener}:raise@2.5` keys, and a zero default in either place would publish an invented defence frequency rather than refuse. The repair the backlog names, an assertion on the refusal rather than on the exit code, is producible today because `main` already prints `refused: <message>` to stderr; only the frozen test does not read it, which is correctly deferred.
- `verification/mutations.yml` still carries the overstatement its own backlog entry convicts, and the entry mis-attributes it slightly. The free-standing comment at lines 1405 to 1421 says of the killing test "both of its parameters do", which the measurement above refutes; the canary's own `description` at lines 1190 to 1194 says only that both parameters "still reach it", which is true. The backlog entry credits the first sentence to "the canary's own note". The file is outside `approved_scope`, so leaving it and filing instead is the right call, but the false sentence is still what the next reader meets.
- The filed ExecPlan undercounts its own stage-9 build. It says "Four sentences in the report were false" and lists four; the commit message and the packet carry six corrections, adding the corpus refusal rate that falls rather than rises and the over-folding cost multiplier. The diff shows six prose changes plus the source fix.
- The packet's rewritten gate section holds against the evidence on disk. `verify_results.json` carries 47 commands, `all_passed: true`, generated 2026-09-05 21:57:20, with `check_gate_bite` printing "gate bites: 74 mutations all caught"; `latest_verify.txt` lists 47 PASS lines and no failure; 48 command ids are registered and the gate runs 47, which is the difference the packet explains. `latest_derived_chart_report.txt` regenerates byte-identical from the committed script, so the required report is fresh.

## Alignment

- `A-CANARY-READS-A-CRASH-AS-A-KILL` is filed correctly and every claim in it reproduces, including the one that mattered most: at 72efe9d only `commit-a-spot-above-the-exposure-threshold` killed the canary, and `drop-a-spot` was already inert on a KeyError in `orderings_section`. The canary therefore still hangs by one thread after this repair, and will lose that thread the next time a render section indexes a chart key, which is ordinary code to write.
- `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION` already names the tag ordering this closeout tripped over: stage 10 instructs tag then merge, `--integrate` prints the tag after the merge, and phase 10's resolution was never written down as the intended one. Until it is, each lane resolves it again by hand.
- `LOOP-STAGE-10-DEMANDS-A-REVIEW-IT-FORBIDS-WRITING` applies to this very file. It is in scope only while the task is still `implementation`, so it and the resolved-blocker marks must be committed before `CURRENT_TASK.yml` is reset to idle.
- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` covers the sweep this phase leaves behind. The contract lists `CHART-HERO-MUST-NEVER-LIMP` among the entries this phase closes and it is still `deferred`, along with the non-artifact halves of the two blind entries and a long tail of items filed against phase 14 that stay deferred against a phase now marked completed. The packet discloses the three by name and gives a reason for each, so nothing is hidden; what is missing is any check that could see it.
- `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` applies to `verification/loop_runs/14.yml`, which will sit at stage 11 and `loop: completed` after this phase closes and be counted as a live lane by the bare stage driver in this worktree.

## What closed each of these, written by the coordinator rather than the reviewer

The reviewer wrote the five findings above and none of what follows; this block records what was
done about them, so a reader is not left to infer it from a commit message.

1. The closeout finished in the two commits after this note: the ExecPlan is filed, phase 14 is
   `completed`, the tag is placed, `CURRENT_TASK.yml` is reset to idle and the gate is re-run green
   on the idle tree.
2. The five real open blockers - three in `stage-09-audit-mechanical.md`, two in
   `stage-09-audit-poker.md` - are marked resolved in their own notes rather than only in the index.
   The other 18 are evidence bullets inside earlier notes' blocker sections, not findings: "Not the
   merge.", "Not the rake.", "69 of the 87 exempted cases have a gap of 50 points or wider." Marking
   those resolved would write a closure onto lines nobody raised, in five committed notes belonging
   to earlier stages, so they are filed as
   `AN-EVIDENCE-BULLET-INSIDE-A-BLOCKER-SECTION-COUNTS-AS-A-BLOCKER` instead. The board reads 18
   rather than zero and the reason is written down.
3. The ExecPlan now carries `## Verification` and `## Outcome`, and the stage-6 and stage-9 lane
   tables no longer read ACTIVE.
4. The ExecPlan now carries a stage-10 entry naming the content change, the three lanes it ran, and
   why the coordinator made the one-line fix rather than delegating it.
5. The tag is moved onto the closeout commit, whose tree says `completed`, the plan is filed and the
   task is idle - which is where phase 13 put its own tag.
