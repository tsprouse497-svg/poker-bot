# Phase 14 stage 11 (advance) review

Independent read-only pass. The reviewer wrote no part of phase 14 and no part of any lane in this
diff, and edited nothing but this file. The session that requested the note wrote one of the merged
lanes below (`maint-30` / `PHASE_14_OPENING_RANGE_HONESTY`); that lane was checked against the
report and the git record rather than taken on its own account.

Question asked: bookkeeping only. A content change here belongs to an earlier stage.

Diff reviewed: `git diff ceff5e1a2d0621d29da73498af00c7fac517030c` in
`/Users/taylorsprouse/projects/poker-bot`, on `main` at `db882dd`, 40 paths.

No gate was run. `scripts/run_verify.py` and `scripts/check_gate_bite.py` plant live source
mutations, and a reviewer running them dirties the tree it is judging.

## What the diff actually is, before anything is judged

**Thirty-nine of the forty paths are not stage 11's work.** They arrived on `main` from five
separately scoped tasks that merged after phase 14 did. Measured per path with
`git log --oneline ceff5e1..HEAD -- <path>`:

    MAINT-27  locate the live lane                 242feda, abc9420
    MAINT-28  primary checkout holds main          5a47e06, 77c7954
    phase 16  dependency cut                       7ae33c0, dc5baf5
    maint-31  ask the chart a hand                 7ab939e, 844edf2, 7fd0fd1
    maint-33  cheaper mutation sweep               919eab9 .. ddfd069 (12 commits)
    maint-30  phase 14 opening-range honesty       4114a98, a1644f3, 9e70901, ff66c12, ce874ea
    gate records on main                           50d25ee, 38845d7, 48371ea, db882dd

**Stage 11 owns exactly one path.** `verification/loop_runs/14.yml`, changed by one commit,
`57b3ea0`, whose entire content is two lines: `stage: 10` to `stage: 11`, and `stage_base` to
`ceff5e1`. Nothing else. `git show --stat 57b3ea0` reads `1 file changed, 2 insertions(+),
2 deletions(-)`.

**Why the diff is forty paths anyway.** `check_stage_review` measures from `stage_base`, and stage
11 is the last stage, so it never advances and its base never moves again. `ceff5e1` is phase 14's
pre-merge lane closeout; `9bbdcf4` merged the lane into `main`; five more lanes merged after that.
So the diff spans every sibling integration since. `docs/LOOP.md` anticipates a diff "wider than the
stage, never narrower", but it describes one lane's stages, not a serial-integration board where the
extra width is other phases' finished work.

**So the stage's own question is a category error as applied to this diff.** There is no content
change here that stage 11 made. Asking whether the content belongs to an earlier stage presumes
stage 11 wrote it, and it wrote a two-line pointer move.

## Blocker

- [resolved] Phase 14 is `auto_advance: false` in `verification/loop_policy.yml`, and the human sign-off that gate exists for is recorded nowhere. `scripts/review_queue.py` prints the ask today - "sign off before the fleet moves past phase 14" - and `scripts/loop_fleet.py --status` shows it against this lane. `--advance` at stage 11 sets `loop: completed`; `loop_fleet.lanes()` counts only `running` and `halted`, so the lane leaves the board and the ask disappears with it, unanswered. `check_advance` in `scripts/loop_stage.py` returns `[]` unconditionally, so this note is the only thing that can hold the stage. `AGENTS.md` is explicit that a phase writing new committed data "always stops", and phase 14 commits the chart the bot plays. I grepped the packet, the closeout review and the filed ExecPlan for "sign off", "sign-off" and "signed off" and found nothing. The nearest thing in the record points the other way: Taylor's 2026-09-06 ruling in `CURRENT_TASK.yml`'s `scope_change_log` is a post-completion finding that the report told a reader something false, which `maint-30` then repaired. That is a human catching a defect, not a human clearing the phase. Advancing this pointer is correct bookkeeping only once the sign-off exists and is written down where a reader can find it; a reviewer cannot supply it and neither can a coordinator.

  [resolved] 2026-09-22 by MAINT-36. Taylor signed phase 14 off as shipped, in session, and the verdict is written where
  `docs/DEFINITION_OF_DONE.md` puts one: `## Human sign-off` at the foot of `reports/phase_audits/PHASE_14_CHART_CUTOVER.md`.
  It rests on his 2026-09-05 and 2026-09-06 rulings, keeps all five accepted defects, and settles decision 36 as deferred
  under `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`. The resolution was written by the coordinator and checked by an
  independent reviewer in `reports/phase_audits/reviews/MAINT_36_PHASE_14_SIGN_OFF/review.md`; the sign-off is Taylor's.

## Non-blocker

- **`maint-30`'s numbers hold, checked against the report rather than against its own commit
  message.** `reports/active/latest_derived_chart_report.txt` prints `gap opens HJ -0.085 narrower`,
  `CO -0.717`, `BTN -1.294`, and `narrower at opens 3 of 5 seats worst BTN 39.266 against 40.560`.
  Those match the three pairs the lane cites (HJ 21.565/21.650, CO 27.173/27.890, BTN
  39.266/40.560), and -0.085 is HJ's stated tie. The claim that no range, weight, price, artifact
  or selection rule moved is true of the whole diff range, not just that lane: no path under
  `data/` appears in the 40, so nothing the bot plays changed. The contract now reads 299 lines
  against its 300 cap, so the re-wrap it claims did fit.

- **`maint-30` swept three falsified backlog entries and missed a fourth of the same shape.** Its
  own review filed `NOTHING-SWEEPS-DEFERRED-BACKLOG-ENTRIES-A-LATER-TASK-FALSIFIED` for exactly
  this, and `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` was properly updated with an `OVERTAKEN
  2026-09-06` paragraph. Its twin `CHART-CUTOVER-CONTRACT-IS-AT-ITS-LINE-CAP` was not touched in
  this diff range and still tells the next lane the contract "sits at exactly 300 of 300 lines and
  cannot take another amendment" and that "Phase 14 should not tag until this has run". Both are
  now false: the file is 299 lines, one more amendment did fit, and phase 14 is tagged. These
  entries are what a future lane reads as its instructions, so a stale one stops work rather than
  merely misleading.

- **The audit packet and the report name different sets of five accepted defects.** The packet's
  `## The five accepted defects` numbers them 1 big blind, 2 pair/kicker/raise-action inversions
  as one item, 3 merged flats, 4 four-bet a quarter oversized, 5 opening ranges. The report's
  `## The five accepted defects, and what each costs` prints five rows: big blind, opening ranges,
  pair ladder, kicker ladder, merged flats - and no four-bet row at all. The contract's Scope
  paragraph matches the report; its vetting-packet bullet matches the packet. This is pre-existing,
  not `maint-30`'s doing: at `ceff5e1` the packet's four were big blind, inversions, merged flats,
  four-bet, and the report's four were big blind, pair ladder, kicker ladder, merged flats. The two
  lists already disagreed about the four-bet, and `maint-30` appended a fifth to each without
  reconciling them. It belongs to whoever folds the contract, not to stage 11.

- **The contract's `Closed:` bullet is falsified for four of the five ids it names.**
  `PHASE-14-CONTRACT-DOES-NOT-FIT-ITS-OWN-CAP` reads `done`; `CHART-HERO-MUST-NEVER-LIMP`,
  `BLIND-STRUCTURE-VARIANTS`, `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` and
  `PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP` all read `deferred`. Pre-existing: no
  phase-14 item's status or phase changed anywhere in this diff range (the only status change in
  the range is `MUTATION-DRILL-CHECKOUT-DESTROYS-UNCOMMITTED-WORK`, `deferred` to `done`, from
  `maint-33`). The stage-10 closeout review already disclosed three of the four by name.

- **On the 53-odd phase-14 items: 55 exist, 51 `deferred` and 4 `done`, and that is consistent with
  the contract's own sweep sentence.** The sentence permits "closed, restated with a measurement, or
  moved forward with a reason", which is a disjunction, so a deferred item with a reason satisfies
  it. I checked every one: no `deferred` phase-14 item has an empty or missing `reason`. The four
  ids the contract says moved to phase 17 all read `phase: "17"`, and the two it says are
  explicitly not closed are both still `deferred`, as it requires. What fails is not the sweep
  sentence but the specific `Closed:` list above.

- **The tag sits on the lane closeout rather than the merge, and phase 13 did the same.**
  `phase-14-complete` is on `ceff5e1`, which is not on `main`'s first-parent line.
  `phase-11-complete` and `phase-12-complete` are both on their merge commits and both are on the
  first-parent line; `phase-13-complete` is on `3aec2a1`, a lane commit, and is not. So phase 14
  follows phase 13, and `AGENTS.md` line 111 - freeze lock and generated docs rebuilt on the merged
  result, full gate plus `check_gate_bite` again "before the tag" - matches phases 11 and 12
  instead. I nearly filed this as a blocker and it is not one: the stage-10 closeout review raised
  it, and the coordinator's recorded answer chose phase 13's convention deliberately and said so.
  It is a disagreement already written down, not an unfinished action.

- **No post-merge gate was recorded for the phase 14 merge.** Every `maint` merge in this range
  carries a follow-up commit - `50d25ee`, `38845d7`, `48371ea`, `db882dd`, each "Record the gate on
  main after the X merge". `9bbdcf4` has none, and neither does the `maint-31` merge `b5eb610`. The
  substance is nonetheless evidenced downstream: `db882dd` records a green gate on a `main` that
  contains phase 14, so `main` does pass with the chart in it. What is missing is the gate at the
  point the tag was placed.

- **Advancing this pointer will not clear the board on its own.** The `phase-14` worktree carries
  its own `verification/loop_runs/14.yml`, still reading `loop: running`, `stage: 11`, and
  `loop_fleet.lanes()` keys on `(phase_id, worktree)`, so it contributes a second phase-14 lane.
  `--status` today lists phase 14's asks twice for that reason. Setting `main`'s copy to `completed`
  leaves the stale copy live.

- **The pointer says `running` where the commit that set it says "halts".** `57b3ea0`'s message is
  "Move the phase 14 lane pointer to stage 11, where it halts for a human", and `docs/LOOP.md` names
  `loop: halted` with a recorded reason as the mechanism for that. The pointer reads
  `loop: running`. Nothing is lost in practice - `policy_asks` keys on `stage >= 11` and
  `auto_advance: false`, not on the halt state, so the ask is on the board either way - but the two
  records disagree about what happened.

- **`review_queue.py` reports 166 asks, and phase 14's one real ask is buried in them.** Most of the
  phase-14 entries are not findings. `unresolved_blockers` counts every line beginning `- ` under a
  `## Blocker` heading, so evidence bullets inside sections whose own heading is already marked
  `[resolved]` are reported as open asks - for instance stage-04-confirmation-review's three `git
  for-each-ref` / `git ls-remote` measurement lines, which sit under a heading reading
  `### `[resolved]``. The stage-10 closeout review counted 18 of these and filed them rather than
  writing a closure onto lines nobody raised, which was the right call. This note keeps its own
  Blocker section to a single bullet and puts its evidence in prose for the same reason.

## Alignment

- `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION` - names both halves of the stage-11 problem
  found here: that `--advance` writing `loop: completed` drops the lane from `loop_fleet.lanes()`
  and locks it out of its own integration runbook, and that stage 10 says tag-then-merge while
  `--integrate` prints the tag after the merge, with phase 10's resolution never written down as
  the intended one. Phases 11 and 12 tagged the merge, phases 13 and 14 tagged the lane closeout;
  four phases have now resolved this by hand and the ruling is still owed.
- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` - covers the 51 `deferred` items and the four
  falsified `Closed:` entries above. `backlog_errors` in `scripts/quality_checks.py` never compares
  an item's phase against that phase's status in `phase_status.yml`, so a completed phase's own open
  items are unreachable by the gate. Phase 14 is now the fourth phase to close this way.
- `NOTHING-SWEEPS-DEFERRED-BACKLOG-ENTRIES-A-LATER-TASK-FALSIFIED` - the live instance is
  `CHART-CUTOVER-CONTRACT-IS-AT-ITS-LINE-CAP`, still asserting a 300-of-300 cap and a
  do-not-tag-yet instruction that this diff's own contract edit disproved.
- `A-PACKET-POINTER-TO-A-REPORT-SECTION-IS-NEVER-RESOLVED` and
  `A-HEADING-COUNT-IS-CHECKED-AGAINST-NOTHING-IN-ITS-OWN-BODY` - between them are the mechanism by
  which the packet's five defects and the report's five drifted into being different sets. Nothing
  resolves a `report -> Section` pointer, and nothing compares a heading's number word to the rows
  beneath it.
- `AN-EVIDENCE-BULLET-INSIDE-A-BLOCKER-SECTION-COUNTS-AS-A-BLOCKER` - why the pause board reads 166
  and why phase 14's genuine ask is hard to find in it.
- `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED` - the `phase-14` worktree's own pointer will stay at
  `running` after this one is advanced, so the lane does not leave the board.
- `STAGE-REVIEW-CHECK-READS-ONE-FILENAME-PER-STAGE` - phase 14 wrote 29 review notes and
  `check_stage_review` opens one filename per stage, so most of them can never hold a stage. It also
  explains why this note is the only thing standing between `--advance` and `loop: completed`.
- `MERGE-INTEGRATION-STILL-RUNS-THE-SWEEP-TWICE` - `AGENTS.md` and `docs/LOOP.md` are both in this
  diff and both still describe the integration sweep that `maint-33` changed.

## What was not checked

- No gate run: neither `scripts/run_verify.py` nor `scripts/check_gate_bite.py`, by instruction. No
  pytest file was run either, and no report was regenerated. Every number quoted above was read out
  of a committed file or computed with `git`.
- No poker judgment. The chart, the 249 committed spots, the solve, the exposure filter and every
  frequency in the report are outside this stage and were not re-derived. `maint-30`'s rows were
  checked for agreement with the committed report, not for whether the reading is the right one.
- The five sibling lanes were attributed to their commits and not reviewed on their merits.
  MAINT-27, MAINT-28, phase 16's dependency cut, `maint-31` and `maint-33` each carry their own
  review notes and their own gate records.
- Of phase 14's 29 review notes, `stage-10-closeout.md` was read in full and
  `stage-04-confirmation-review.md`'s blocker section was sampled to establish the parser artifact.
  The other 27 were not read.
