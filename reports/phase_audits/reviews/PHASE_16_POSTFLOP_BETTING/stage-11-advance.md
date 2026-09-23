# Stage 11 advance review: the integration of phase 16 into main

Lane R9b, independent, read-only. 2026-09-22.
Reviewed diff: `git diff 78804ce HEAD` in `/Users/taylorsprouse/projects/poker-bot-worktrees/phase-16`,
13 reviewed paths of the 21 the diff names. I wrote none of this and ran no gate; the only file I
wrote is this one.

Topology I re-derived rather than took on trust:

- `eb28319` has parents `78804ce` (lane) and `7d10624` (main's tip at the time).
- `1cdae37` has parents `7d10624` and `891fdd9`, so the integration merge is main-first, lane-second.
- The three-way merge base of the two sides is `1d89158`.
- `phase-16-complete` is an annotated tag whose target is `1cdae37`. It resolves to the merge.
- Lane `HEAD` tree `f2f87d6` and `main` tree `5270a6e` differ in exactly one path,
  `reports/active/verify_results.json`, which is main's own re-gate at `b1f8864`. Nothing else in
  this review's subject differs between the lane and what is pushed.

## Blocker

None.

## Non-blocker

### 1. The roadmap resolution is sound, and it is not a content change

*Checked: does the falsified ratio survive in any live document, and did taking main's file whole
discard a phase 16 correction main's rewrite does not cover.*

**The closing condition is met, and met more strictly than the closing note claims.** I swept the
tracked tree at `HEAD` for the two figures the falsified claim is made of, "about 49 times a flop"
and "2,350". Across `docs/ROADMAP.md`, `docs/V2_ROADMAP.md`, every file under
`docs/phase_contracts/`, `docs/ARCHITECTURE.md`, `docs/V2_RULING_MITIGATIONS.md`, `AGENTS.md`,
`README.md` and `STATUS.md` there are zero hits. The surviving occurrences in the tracked tree are
these and only these, and none of them offers the ratio as a basis for reasoning:

- `backlog.yml` and its generated `docs/BACKLOG.md` - the diagnosis entry itself, which has to
  quote the claim it falsifies.
- `CURRENT_TASK.yml` scope log, quoting the sentence it authorised the edit to remove.
- `docs/exec_plans/completed/MAINT_26_POSTFLOP_SOLVE_COST.md` and
  `docs/exec_plans/completed/MAINT_POSTFLOP_COVERAGE_RULING.md` - completed plans, snapshots.
- `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` at lines 183 and 190.

I checked that last one rather than accepting "the decision list was already clean", because it is
the one live-ish document in the list. It is clean. Line 183 is past tense and explicitly scoped to
when the file was written - "what survived that, when this file was written, was a ratio" - and it
is followed eight lines later by a dated, bolded falsification giving MAINT-26's 1/212 and 1/38,000
and stating that no conclusion below may be supported by the ratio. Line 190 is inside that
falsification. The claim in the closing note is accurate.

**Nothing of phase 16's was discarded.** Phase 16 touched `docs/V2_ROADMAP.md` in exactly one commit
on the lane, `7254a50`, and the diff `1d89158..78804ce` for that path is a single hunk replacing a
single sentence - the ratio sentence and nothing else. MAINT-35's rewrite at `3cdacf5` deletes the
entire paragraph that sentence lived in, along with the "one flop spot is 49 turn spots" counts
sentence above it. So the lane's whole contribution to that file is contained in what main removed.
There is no second phase 16 edit to that file for main's rewrite to have missed.

**On the driver's question, this one is bookkeeping.** It is the honest candidate and I looked hard
at it, but taking main's side wholly changed no content that phase 16 owned: phase 16 owned one
sentence, and the resolution's effect on it is deletion by a commit that was already on main before
the lane saw it. A content change belonging to an earlier stage would be one where the merge
decided something about phase 16's own material. This decided nothing; it accepted a sibling's
deletion of the only line at issue and then verified the condition that line was closed under.

Two smaller things I checked while here and found correct. The new `docs/V2_ROADMAP.md` does not
re-ground the flop-only ruling in compute, which is the trap a rewrite could have walked back into -
it grounds it in board texture and the heuristic-guessing boundary, and its compute paragraph cites
`reports/active/latest_postflop_solve_cost.txt` with pooled measured figures and names its own
earlier draft's error. And the closing note's concession that "absent" beats "corrected" is the
right way round for this entry's condition, which is about what a live document still offers rather
than about whether a correction is recorded somewhere.

### 2. The backlog merge is exactly as claimed, on every figure

*Re-derived from the four blobs with a YAML parse, not from the diff.*

| Side | Items | Distinct ids | Duplicate ids |
| --- | --- | --- | --- |
| merge base `1d89158` | 250 | 250 | none |
| lane `78804ce` | 344 | 344 | none |
| main `7d10624` | 261 | 261 | none |
| merged `HEAD` | 355 | 355 | none |

Every claim holds. The lane added 94 ids, main added 11, neither side removed any, and
250 + 94 + 11 = 355, which is both the union size and the merged count. Nothing in the union is
missing from the merged file and nothing in the merged file is absent from the union, so nothing
was dropped and nothing was invented. Thirteen items were edited on the lane only and seven on main
only, and no item was edited on both.

I then ran the stricter test the id-level one does not cover, because an edit made on one side can
survive as a valid-looking item while silently reverting to the base text. For every one of the 355
ids I compared the merged item against the sides that hold it: an id added on one side must match
that side verbatim, an id edited on one side must match that side, and an id neither side touched
must match the base. **Exactly one item fails that test, and it is the one declared:**
`POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`, base and main at `deferred` with a 1,491-character reason,
the lane at `done` with 2,007, the merged file at `done` with 2,246. The mid-merge rewrite is the
whole of the difference. Every other item in the file is a byte-faithful take from one side.

On the closing note itself, which I read rather than counted: it is accurate. It states the
condition, names the one survivor the stage-8 sweep found, says the sweep's edit was superseded by
main's deletion, and concedes the decision list was already clean and that completed exec plans are
snapshots. I confirmed all four of those independently in finding 1. The note does not overclaim,
and its concession that "absent" satisfies the condition better than "corrected" is the right way
round for a condition written about what a live document still offers.

### 3. The scope log merged correctly, but "deduplicated" describes the merge, not the file

*Re-derived by parsing `scope_change_log` at all four revisions and comparing entries by full
content, date and reason together.*

The merged `CURRENT_TASK.yml` has **399** entries, which matches. `standing_scope` (10 paths) and
`forbidden_scope` (2 paths) are byte-identical at all four revisions - base, lane, main and merged -
so neither was touched. `task_mode` is `idle` with `task_id`, `active_phase` and `base_commit` all
null and `approved_scope` empty on every side, so the closeout state survived the merge intact.

The merge itself is right. The union of distinct entries across the three sides is 221; the merged
file holds 221 distinct entries, with zero dropped and zero introduced. It took the lane's 397 and
added exactly main's two new ones. Nothing about this resolution is wrong.

**But the file is not deduplicated, and the review brief's description of it is the one figure in
the brief I could not confirm.** Of the 399 entries, only 221 are distinct: 175 entries appear
twice, one appears four times, and 45 appear once. That is 178 redundant entries in an audit record
of scope widenings, which is close to half the file.

This merge did not cause it. I bisected the lane's history of that file and the duplication appears
in a single step: the log runs at 177 entries with one accidental repeat from `2942e8d` ("Open the
phase 16 lane at stage 0") and jumps to 391 entries with 178 redundant at `d7712d5` ("Merge main
into the phase 16 lane: the re-solved chart lands"). **An earlier lane-into-main merge concatenated
the shared history instead of merging it by content, and every merge since has faithfully carried
the doubled log forward, including this one.** The 2026-09-22 resolution did the thing the earlier
one should have done.

It is on `main` right now and a fix goes forward. It is not a gate risk: `check_file_sizes` caps
`docs/*.md` at 500 lines, `docs/phase_contracts/*.md` at 300 and `reports/phase_audits/*.md` at
500, and `CURRENT_TASK.yml` is under no line cap at all, so nothing objects as the file grows. That
is the reason it went 214 entries unnoticed. The cost is that anyone reading the scope record to
reconstruct what a phase was allowed to touch reads most widenings twice and has no way to tell a
genuine repeat authorisation from a merge artifact.

**This needs a `backlog.yml` id and does not have one.** I grepped the whole backlog and nothing
covers a duplicated scope log or a merge that concatenates one; the nearest entries are about
`CURRENT_TASK.yml` reading `idle` misleadingly and about a single dated entry's disclosure, neither
of which is this. I am read-only and cannot file it, so it stays a non-blocker here with the
measurement attached, and the driver owes it an id before stage 11 advances. Without one it cannot
be an alignment item under this note's own rules.

### 4. The push came before this review because the loop is built that way, not because someone skipped a step

*The coordinator asked me not to soften this. I am not going to, and the thing I found is worse
than a lapse of discipline would have been.*

What is true first: nothing shipped ungated. `reports/active/verify_results.json` on the lane holds
50 commands, all `passed`, generated at epoch 1790093812; main's holds the same 50 command ids in
the same order, all `passed`, at epoch 1790095168, 22.6 minutes later. `check_gate_bite` is one of
those 50 and passed in both, so the `AGENTS.md` requirement that the full gate plus `check_gate_bite`
run again on the merged result before the tag is satisfied inside the gate itself. The freeze lock
is unchanged across the reviewed diff, which is correct rather than skipped: no path under `tests/`
appears in the merge, so a rebuild reproduces the same lock.

Now the finding. **The loop places the merge inside stage 10's instruction and gives stage 11 the
diff that contains it, so the first independent look at any merge resolution is structurally after
the merge.** `scripts/loop_stage.py` stage 10 reads "File the ExecPlan as completed, set the phase
completed, tag phase-NN-complete, reset to idle, gate again, commit, merge the branch". Stage 11
reads only "Consult `verification/loop_policy.yml`: continue into the next phase, or halt". So the
merge is the last item on stage 10's list, and the review that can see it is stage 11's, which by
construction cannot run until stage 10 is finished. The pointer bears this out: `loop_runs/16.yml`
carries `stage_base: 78804ce`, and the merge commits sit inside that window.

That means the coordinator did not get the order wrong. The order is the design. And the design is
wrong, because a review whose only possible verdict is "fix it forward" is a weaker instrument than
one that can say "do not merge this". This repo's own `AGENTS.md` names the failure it is trying to
prevent - phases 05 through 12 self-certified review and that discretion is what failed - and an
ordering that guarantees the reviewer arrives after the irreversible step is the same weakness by
a different route. The push is the smaller half of it; the tag and the merge onto `main` were
already the point of no return before the push made it public.

**It is worth filing, and it needs an id it does not have.** I searched the backlog for it. The
closest live entry is `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION`, which records that
stage 10 says tag-then-merge while the fleet driver prints the tag after the merge, and that phase
10 resolved it by moving the tag onto the merge commit with nothing recording that as intended.
That is about tag order and lane lockout. It is not about when the review happens, and it does not
cover this.

**On whether the other order would have caught anything here: no.** I checked every claim the
resolution makes and all of them hold. The roadmap resolution discarded nothing, the backlog merge
is faithful on all 355 items, and the scope log's union is exactly preserved. The one defect I found
predates this merge by several commits and would not have changed the decision to push. So the
ordering cost nothing on this integration, and that is precisely the argument that will be made the
next time, which is why the entry should be filed on the structure rather than on the outcome.

One piece of evidence that the ordering is not theoretical. The doubled scope log in finding 3 was
introduced by `d7712d5`, an earlier main-into-lane merge in this same phase, and survived 214
entries and several subsequent merges without anyone noticing. Merge resolutions in this lane have
not, before today, had an independent reader. This is the first one that did, and it found
something - just not something from this merge.

### 5. The rest of the 13 reviewed paths

Checked and correct, stated briefly because nothing in them is contested.

**`phase_status.yml` is a fourth resolution the brief does not name, and it is the cleanest one.**
It is the only reviewed path whose merged content matches no single side, and that is correct
rather than suspect: both sides changed it and neither change is generated. Main renamed the
project from the training reading to the playing one, deleted the phase 15 row, and appended 18, 19
and 20. The lane's entire contribution is one line, phase 16 going from `future` to `completed`. I
diffed the merged file against main's and the difference is exactly that one line and nothing else,
so every main change survived and the lane's flip was applied on top. Minimal and faithful.

The two generated documents agree with it row for row: `docs/PHASE_LEDGER.md` and
`STATUS.md` both list the same 20 phases with the same statuses and no phase 15 row, and
`STATUS.md` reads idle with no active phase, which matches `CURRENT_TASK.yml`. `docs/BACKLOG.md`
holds 355 data rows, matching `backlog.yml` exactly.

`verification/loop_policy.yml` has no phase 15 key and has gained entries for 18, 19 and 20, all
three `auto_advance: false`, with 20 additionally `needs_human_data: true`. Phase 16 remains
`auto_advance: false`, which is what stage 11 must consult, so the advance decision for this phase
is a halt for a human rather than an unattended continue.

The deleted `docs/phase_contracts/PHASE_15_DRILL.md` leaves nothing dangling. No file in the tracked
tree references it except `backlog.yml` and its generated `docs/BACKLOG.md`, which mention the drill
historically, and no command id in `scripts/run_verify.py` or in either `verify_results.json`
belongs to it. The gate derives from contracts whose phase is active or completed, and a retired
phase contributes none.

`docs/exec_plans/active/` is empty and both `PHASE_16_POSTFLOP_BETTING.md` and
`MAINT_35_PLAY_STRENGTH_DIRECTION.md` are filed under `completed/`. Both audit packets exist at the
paths `phase_status.yml` names.

`phase-16-complete` resolves to `1cdae37`, the integration merge, which is where the fleet runbook
wants it.

## Alignment

Three, all with live ids, none fixable by this stage.

- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` - **this merge made it 53 items worse and nothing
  objected.** Setting phase 16 to `completed` turned every backlog item filed against phase 16 and
  still at `deferred` into the self-contradiction that entry describes. I counted them by parsing
  `backlog.yml` against `phase_status.yml`: 53 for phase 16, 50 for phase 14, 1 for phase 12, 104
  in total across the three completed phases that have any. The entry was written when there were
  four. The gate has no check that compares an item's phase against that phase's status, so the
  number can only grow, and it grew by more than half at the moment this phase closed.
- `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT` - the entry
  `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` is now itself an instance. Its `reason` still opens in the
  present tense with "`reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` and
  `docs/V2_ROADMAP.md` both state that the turn is about 49 times a flop", and neither document
  states it any more. The correction is real but it is twenty lines below, in the closing note, and
  a reader who greps the roadmap from that opening sentence finds nothing and has no way to tell
  whether the file was swept or the claim was wrong. This is the exact shape the alignment entry
  describes: the correction lands where the author was looking and the assertion above it stands.
- `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION` - its unresolved half recurred verbatim.
  That entry records that phase 10 tagged the closeout commit and then moved the tag onto the merge
  commit, and that nothing records this as the intended resolution. Phase 16 has now done the same
  thing: `phase-16-complete` is an annotated tag resolving to `1cdae37`, the merge, not to the
  closeout. Two phases have now independently converged on the same workaround for the same
  disagreement between the two drivers, and the entry is still `deferred` with the resolution still
  unwritten. A third phase will guess again.


