# MAINT-35: Re-aim the repo from a training bot to a bot that plays

## Objective

Taylor ruled on 2026-09-21 that the goal of this repo is a bot that plays strong NLHE, and that the
training product is backlogged until the bot is strong. This task makes that the repo's stated
purpose, retires the training phase from the graph, declares the phases the new goal needs, and
records the teaching-motivated strategy acceptances as work to reopen.

It changes no strategy, no artifact and no runtime behaviour. Every acceptance it names stays
accepted; this task files them, it does not reverse them.

## Taylor's rulings, 2026-09-21

Taken from the session transcript, recorded here because nothing else in the repo carries them yet.

1. **North star.** A bot that plays really good poker. The training product comes after, to help a
   user, and is backlogged until the bot plays well. Some recent decisions refused spots the solve
   takes because they would not make sense for a trainee; that reasoning is retired.
2. **Venue.** The bot will eventually play live, in **Taylor's own home games**. Not public
   real-money tables. This reverses part of the 2026-08-15 ruling that kept table automation out of
   v2 on terms-of-service and account risk, and it reverses it only for private home games.
3. **The big blind's tight defence.** Reopen it **after** phase 16 has flop cells, so the decision is
   made against a measured number rather than against an argument.
4. **The drill.** Backlog it and close the lane.
5. **Refusals.** Fail-closed stays for now. Heuristics, and the merge of solved charts with unsolved
   spots, become **their own later phase** rather than a change made here.
6. **Rename.** Documents only. The `poker_training_bot` package keeps its name.
7. **The terms-of-service risk, ruled 2026-09-21 after the independent review raised it.** The
   2026-08-15 ruling kept automation out on terms-of-service and account-risk grounds, and those
   attach to the platform rather than to who is at the table, so narrowing the venue to a private
   game does not answer the reason Taylor gave. That was put to him in those words. He ruled
   **proceed, risk accepted**. It is recorded everywhere as an accepted risk rather than a resolved
   one, so no later reader takes the narrowing for an answer.
8. **What "plays live" means, ruled the same day.** An online table the bot drives and an in-person
   game it advises across are different phases. Taylor answered that the bot is handed the game's
   URL, joins the table and plays, and said the question may stay open for now. Recorded as the
   working reading for phase 20's stage 1 to confirm, committing to no platform.

## Scope

Approved: `AGENTS.md`, `README.md`, `docs/ROADMAP.md`, `docs/V2_ROADMAP.md`, `docs/ARCHITECTURE.md`,
`docs/phase_contracts/**`, `verification/loop_policy.yml`.

Standing: `CURRENT_TASK.yml`, `backlog.yml`, `phase_status.yml`, `STATUS.md`,
`docs/PHASE_LEDGER.md`, `docs/BACKLOG.md`, `docs/exec_plans/**`, `reports/active/**`.

Forbidden: everything else. In particular this task touches no file under `src/`, `tests/`,
`scripts/`, `data/` or `verification/mutations.yml`. No committed artifact is re-derived and no
completed phase's data moves.

## The phase graph after this task

Retired: **15, The Drill**. It is a bare skeleton with no implementation, nothing depends on it, and
its own dependency edge into phase 16 was already cut on 2026-09-06.

Declared:

| Phase | Title | Depends on | Why the new goal needs it |
|-------|-------|------------|---------------------------|
| 18 | The Yardstick | 14 | Nothing in this repo measures how well the bot plays. Its own report says so: "Producing the other kind of number needs an opponent with a strategy, and this repo does not have one yet." |
| 19 | Heuristics And Merged Charts | 16, 18 | Ruling 5. Fill the refusal gaps by merging solved cells with heuristics, every substitution carried on the decision. Needs 18 so the merge can be shown to help rather than asserted to. |
| 20 | The Home Game | 16, 19 | Ruling 2. A bot that sits down in Taylor's own home games. Last, because a bot that folds every flop should not sit anywhere. |

Unchanged: 16 (Postflop That Can Bet) and 17 (The Corpus Verdict), both already in flight.

## Delegation Plan

Written before implementation. Three worker lanes, no two writing the same file, integrated by the
coordinator.

- Worker lanes: lane A restates the repo's purpose and rewrites the boundary section; lane B
  rewrites both roadmaps around playing strength and re-derives every figure in them; lane C retires
  phase 15, declares phases 18, 19 and 20, and files the backlog entries listed below.
- Ownership: lane A holds `AGENTS.md`, `README.md` and `docs/ARCHITECTURE.md`. Lane B holds
  `docs/ROADMAP.md` and `docs/V2_ROADMAP.md`. Lane C holds `phase_status.yml` in full including its
  `project:` field, `verification/loop_policy.yml`, `docs/phase_contracts/**` and `backlog.yml`. The
  coordinator holds this ExecPlan, `CURRENT_TASK.yml`, and the three generated documents. No file
  appears twice, which is what lets the three lanes run at once in one worktree.
- Expected outputs: from A, the new boundary section and a changed-file summary. From B, both
  roadmaps plus a table of every stale figure with its old value, its re-derived value and the
  committed file the new value came from. From C, the three contract skeletons with frontmatter, the
  policy entries, the backlog ids verbatim, and the output of `check_repo_consistency`,
  `check_contracts`, `check_scope` and `check_file_sizes`.
- Status: lane A completed and committed; lane B completed; lane C completed. Generated documents
  regenerated by the coordinator. Independent review completed 2026-09-21 by a read-only reviewer
  that wrote none of the work, returning one blocker and eight smaller findings. A fourth lane, the
  repair lane, fixed them; it wrote neither the original work nor the review, and it held
  `backlog.yml`, the phase 19 and phase 20 contracts, `AGENTS.md`, `CURRENT_TASK.yml` and this file,
  with everything else forbidden to it. The full gate is outstanding.
- Integration order: A, then C, then B, because B's phase table has to agree with what C declared.
  B verified its table against C's committed contract frontmatter rather than against this plan. The
  coordinator regenerated `STATUS.md`, `docs/PHASE_LEDGER.md` and `docs/BACKLOG.md` after C, and
  confirmed a second generator run changes nothing.
- Coordinator-owned work: recording a ruling that arrives mid-task is the coordinator's, not a
  lane's, because a lane cannot tell an answer from its own paraphrase of one. Rulings 7 and 8
  above, and their wording in `AGENTS.md`, `docs/V2_ROADMAP.md`,
  `docs/phase_contracts/PHASE_20_HOME_GAME.md` and `verification/loop_policy.yml`, were written by
  the coordinator for that reason. Everything else was delegated.
- Review handoff: the independent read-only reviewer must check that no figure written anywhere in
  this task was carried out of prose instead of re-derived, that no acceptance was reversed rather
  than filed, that the boundary section in `AGENTS.md` and the rulings in `docs/V2_ROADMAP.md` say
  the same thing, and that retiring phase 15 left no dangling `depends_on`, policy entry, registered
  command or orphaned backlog entry. The reviewer must not be a lane that wrote what it reads.

## Backlog entries this task files

Each records a teaching-motivated acceptance to reopen under the new goal. None is reversed here.

- The big blind's tight defence, reopened after phase 16 has flop cells. Ruling 3.
- The pair-ladder and kicker-ladder inversions, accepted twice on the grounds that the cost is
  "pedagogical, not monetary". Corrected after lane C checked it: the experiment that would price
  them, a re-solve with pruning off, WAS run on 2026-09-02 and came back negative, so the inversions
  are a preference the fit holds rather than actions the solver left stuck. Two shipped backlog
  entries still tell a reader it has never been run. What is genuinely unrun is the same experiment
  against the chart that ships, since 2026-09-02 predates the MAINT-34 re-solve.
- The multiway exposure threshold, moved from 1 to 10 percent because "a squeeze is a spot a student
  meets constantly", and measured on a quantity that is circular: multiway flops look rare because
  the model under-flats.
- Coverage is published reach-weighted under the solve's own play. Against real hands it is lower,
  and the exclusions measured on arrival were measured the same flattering way. The excluded nodes
  split five ways, not two and not four; the count and the identity that closes are in the backlog
  entry rather than restated here. See the Outcome section for how many times this plan got that
  number wrong.
- The five-bet jams, withheld partly because keeping them "ships advice a student cannot detect as
  wrong, in a training tool". Filed by the repair lane, not by lane C: the eight entries above and
  below it missed it. Like the big blind it has two legs, and only the trainee one expires.
- The drill, deferred as post-strength work. Ruling 4.

## Slices

- [x] Slice 1: activate the task and write this plan. Evidence: this file, `CURRENT_TASK.yml`.
- [x] Slice 2: Lane A. Evidence: changed-file summary and the new boundary table.
- [x] Slice 3: Lane C. Evidence: `check_repo_consistency` and `check_contracts` green on the new graph.
- [x] Slice 4: Lane B. Evidence: every figure in both roadmaps traced to a re-derivation, not to prose.
- [x] Slice 5: regenerate the generated documents. Evidence: clean diff on a second run.
- [x] Slice 6: independent read-only review. Evidence: review notes under the audit path.
- [x] Slice 7: repair lane. One blocker and eight findings fixed, three alignment items filed.
  Evidence: the Outcome section and the nine entries it names in `backlog.yml`.
- [ ] Slice 8: full gate. Evidence: `reports/active/latest_verify.txt`.

## Verification

`uv run python scripts/run_verify.py`. No new command IDs; this task adds no behaviour to test.
The checks that can actually fail on it are `check_scope`, `check_contracts`,
`check_repo_consistency`, `check_file_sizes`, `check_execplan_delegation` and the fact-drift check.

## Outcome

Pending the gate. What the lanes changed, what this plan had wrong, and what the independent review
found that all three lanes and the coordinator had missed.

**The lanes.** A restated the purpose in `AGENTS.md`, `README.md` and `docs/ARCHITECTURE.md` and
replaced the flat prohibition list with boundaries that each name the phase that lifts them. B
rewrote both roadmaps and re-derived twenty figures rather than carrying them. C retired phase 15,
declared 18, 19 and 20, and filed eight backlog entries.

**The review, and the repair lane it ordered.** A read-only reviewer that wrote none of the work
returned one blocker and eight smaller findings on 2026-09-21. A fourth lane, which wrote neither
the original work nor the review, fixed them. What it changed: the exclusion census in the coverage
entry and in this plan, both wrong in the same way; the sourcing of two arrival figures that credited
one artifact field with a measurement it does not hold; a raw relation count published as the size of
an accepted defect, against a standing obligation another entry already carries; a misquotation of a
sibling entry; the ninth backlog entry, for the withheld five-bet jams; a non-goal in each of the
phase 19 and phase 20 contracts; the hand-history boundary bullet in `AGENTS.md`, which this task had
left with no owning phase; and the reason `V2-TRAINING-UI` gives for waiting, which named the drill
this task had just deferred. It also filed three alignment items rather than fixing them, one of them
by extending an entry that already held half the problem.

**The pruning experiment had already been run, and this plan said it had not.** The plan's own
backlog bullet called it the cheapest unanswered question in the repo. It was run on 2026-09-02 and
came back negative: every ladder inversion reproduced with pruning off, at a better convergence gap
than the committed solve, so the inversions are a preference the fit holds rather than actions the
solver left stuck. The record is in the "Open, and not to be invented" section of
`docs/exec_plans/completed/PHASE_14_CHART_CUTOVER.md`. Two shipped backlog entries still tell a
reader it has never been run, which is how this plan came to repeat it. What is genuinely unrun is
the same experiment against the chart that ships, because 2026-09-02 predates the MAINT-34 re-solve,
and the committed solve's own wall clock is 188.4 seconds, so a re-run is cheap.

**The excluded-node buckets are five, and this plan got the count wrong twice before the
independent review got it right.** The first wording here was "the 128 spots dropped as
zero-arrival", which fuses two exclusions into one. The correction to that said four. The
independent review of 2026-09-21, which wrote none of the work it read, found that four was wrong
too: the backlog entry whose whole subject is how this census is read named three buckets, called
the largest "the remaining", and asserted an identity over four counts that does not close. The
correction is the reviewer's finding and not this lane's.

There are five, and the artifact says so itself. `audit_fields.notes` in
`data/artifacts/preflop/six_max_100bb_rakefree.json` reads "5 clauses can refuse a node and 5 of
them do here", and `reports/active/latest_derived_chart_report.txt` prints every one with its count:
`derivation:beyond-committed-raise-depth` 30,002, `derivation:multiway-exposure-above-threshold`
154, `derivation:big-blind-squeeze-spot` 9, `derivation:no-arriving-hand-class` 160 and
`derivation:terminal-split-does-not-close` 128. The two that kept being dropped are the multiway and
squeeze buckets, which are the subject of a sibling entry this same task filed three items earlier.
The identity that closes: 30,002 + 154 + 9 + 160 + 128 = 30,453 excluded, plus 156 committed and 0
inexpressible, gives the 30,609 action nodes on the export's own source card. The counts are
re-derived in the backlog entry rather than restated as fact here.

The lesson is narrower than "check the arithmetic". A total that closes is not evidence a census is
right: fold any two of the five together and it still sums to 30,609. Only naming the buckets
catches it, which is exactly what the report says on the line above the census, and this plan read
past it twice.

**Retiring a phase orphans its backlog entries and nothing warned about it.** Five entries were
filed against phase 15 and turned `run_full_quality_gate` red the moment the phase left
`phase_status.yml`. They were re-filed one at a time against their bodies rather than their titles,
and two of them did not go where the coordinator guessed.

## Next Agent Bootstrap

The lane is `/Users/taylorsprouse/projects/poker-bot-worktrees/maint-35` on
`maint/35-play-strength-direction`, branched from `main` at `1d89158`. `task_mode` is
`contract-update`, so contract edits are allowed and must not mix with implementation.

Open, and not to be invented:

- Whether the phase-15 branch and worktree are deleted or kept. The branch holds a decision list and
  an ExecPlan for the retired drill. Ask Taylor before deleting either. Until one of them goes,
  `scripts/loop_fleet.py` keeps printing phase 15 as a halted lane, because a lane's live pointer
  lives in its own tree and retiring the phase here does not retire it there.
- Phase 14 is still at loop stage 11 waiting on Taylor's sign-off, and phase 17 is waiting on six
  rulings from him. Neither is this task's to answer.
