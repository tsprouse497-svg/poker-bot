# MAINT-36 independent review

I am a read-only review subagent and wrote none of this task. I read `git diff 40b53f6 1c585bf` in the
`maint-36` worktree (five files), phase 14's packet in full around the cited lines, decision 36 in
`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md`, the full backlog entry
`PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`, the MAINT-34 ExecPlan, `docs/DEFINITION_OF_DONE.md`,
and `unresolved_blockers`, `decision_items` and `unanswered_frozen` in `scripts/loop_stage.py`. I ran
`check_scope.py`, `check_file_sizes.py` and `quality_checks.py` (all exit 0) and called
`loop_stage.unresolved_blockers` on the stage-11 note directly. I did not run `run_verify.py`,
`check_gate_bite.py`, pytest or `--advance`. What Taylor said is taken from the coordinator's brief; I
did not see the session.

## Blocker

- [resolved] The backlog note extends Taylor's ruling past what he was asked, unless the session question named
  the MAINT-34 prices. The new paragraph at `backlog.yml:6483-6486` says Taylor "accepted the four-bet
  size shipping as known defect 4" and that "the entry stays deferred on that ruling". Defect 4 is the
  phase 14 chart's four-bet: 22.5bb, "a quarter oversized", 3.00x at 15 spots
  (`reports/phase_audits/PHASE_14_CHART_CUTOVER.md:184-188`). But the entry this note now closes on is
  no longer about that chart. The paragraph immediately above it, `backlog.yml:6466-6482`, added
  2026-09-17 by MAINT-34, says the shipped chart now carries three four-bet prices, that "a quarter
  oversized is now the mildest of the three", that 40.5bb at 40 spots is 42 percent over a standard
  price, and that 26 spots where a blind cold-four-bets a 7.5 three-bet are priced at 5.4x, "roughly
  double a standard four-bet", which "appears in no column of any committed report" and which route C
  was "never" ruled on as priced like poker. Per the brief, the question put to Taylor was about
  decision 36 and defect 4. If it did not mention the 40.5bb and 5.4x prices, then "stays deferred on
  that ruling" records an acceptance of a roughly-double price he was not shown - the same shape of
  error decision 36 itself records, a ruling resting on a description that understated the facts.
  The fix is wording only: scope the note to what was asked (the phase 14 chart's 22.5bb four-bet,
  defect 4) and say plainly that the MAINT-34 prices in the paragraph above were not put to him and
  remain unruled. The ExecPlan's "The sign-off, as given" section
  (`docs/exec_plans/active/MAINT_36_PHASE_14_SIGN_OFF.md:21-31`) should carry the same one-line scope.
  If the coordinator did name those prices in the question, record that in the ExecPlan and this
  blocker is resolved as written. The packet's own sign-off lines (`PHASE_14_CHART_CUTOVER.md:497-499`)
  are fine: they sign off phase 14 as shipped, and phase 14 shipped the 22.5bb chart.

  [resolved] 2026-09-22: the coordinator confirmed the question named only the 22.5bb four-bet, and the
  uncommitted backlog paragraph and ExecPlan now limit the ruling to it and say the 40.5bb and 5.4x
  prices are unruled, filed as `BLIND-COLD-FOUR-BET-PRICED-AT-DOUBLE-STANDARD-IS-UNRULED`; re-read in
  the diff, with `generate_backlog.py --check`, quality, scope and size checks all exiting 0.

## Non-blocker

- Items 1 and 2, otherwise verified. The 2026-09-05 publish-and-ship ruling is at packet lines 48-49
  and 209; the 2026-09-06 opening-range ruling adding the fifth defect is at lines 50-51 and 196.
  Defect 4 is the four-bet (packet line 184, under `## The five accepted defects` at line 132), and
  decision 36 is "Whether the re-raise size is corrected" (decisions file line 3319), ruled "fix it"
  on 2026-09-01 on a wrong coordinator statement, left at 3.0 and filed under the same backlog id.
  "All five accepted defects standing" claims no more than the record: defects 1 to 3 and 5 rest on
  earlier rulings (decisions 34, 41, 47, 45 and the 2026-09-06 task), and "the content had already
  been decided" is a fair basis for that. The packet does not quote Taylor's words; the ExecPlan does
  (line 28), which is enough given the packet has no room.
- Item 3. The packet is 499 lines against the 500 cap in `scripts/check_file_sizes.py:16`, and the
  diff to it is four added lines at the foot (a blank line, the heading, two lines of text) and
  nothing else. It now has one line of headroom.
- Item 4. The only change to `stage-11-advance.md` is the `[resolved]` prefix on the single blocker
  bullet plus an indented resolution paragraph; no other section moved. `unresolved_blockers` returns
  `[]` on the committed text. Two small points: the resolution paragraph says the resolution was
  "checked by an independent reviewer in" this file, which was written before this review existed
  and is only true once the blocker above is settled; and `unresolved_blockers`'s docstring
  (`scripts/loop_stage.py:171-174`) intends the reviewer rather than the writer to mark a finding
  closed. Here the coordinator marked it, which is disclosed in the paragraph and is reasonable since
  the blocker asked for a human fact a reviewer cannot supply.
- Item 5. `CURRENT_TASK.yml` is `maintenance`, `task_id: MAINT-36`, `active_phase: null`,
  `base_commit` equal to `40b53f6` (the `main` HEAD the branch starts from), four narrow approved
  paths, and a dated 2026-09-22 `scope_change_log` entry naming all four. `backlog.yml`, the ExecPlan
  and `verification/loop_runs/**` pass through `standing_scope`. `check_scope.py` exits 0.
- `docs/BACKLOG.md` is stale: the generator carries each entry's full reason (the MAINT-34 paragraph
  is in it) but the new 2026-09-22 paragraph is not, because the commit did not regenerate it. The
  closeout gate should catch this; regenerate before running it rather than after a red.
- Item 6, stale lines the sign-off now falsifies. Packet lines 349-350 ("is back with Taylor"), the
  decisions file's supersession table at line 56 ("back with Taylor") and decision 36's answer at line
  3350 ("pending Taylor") are all now false. All three are correctly left as snapshots: the packet
  corrects itself at its own foot (line 499), and the decision list is a phase record in the same
  sense. The recorded answer bracket there, `[leave-at-3.0-and-file]`, is exactly the option Taylor
  has now chosen, so the snapshot and the ruling agree on substance. The phase 14 contract line 52
  ("decision 36 declined a depth-aware re-raise multiplier") stays true and needs no amendment. The
  completed phase 14 ExecPlan does not mention decision 36's status. Nothing here needs fixing now.
- Held back as outside the brief: decision 36 is the case the memory note on answer brackets warns
  about. `unanswered_frozen` treats any non-empty bracket as answered, so the coordinator's own
  pre-filled default with "(pending Taylor)" beside it satisfied the human gate and nothing ever put
  the question to Taylor until this task, three weeks later. That trap is already known; this is one
  more instance of it.

## Alignment

- `PHASE-AUDIT-PACKET-AT-ITS-LINE-CAP` (existing): phase 14's packet is now at 499 of 500, so the next
  correction to it, including any follow-up to the blocker above, cannot be written into it. Add phase
  14's packet to that entry's list.
- Proposed `BLIND-COLD-FOUR-BET-PRICED-AT-DOUBLE-STANDARD-IS-UNRULED`: the 5.4x blind cold-four-bet at
  26 spots lives only as a paragraph inside a backlog entry whose title and phase 14 defect number
  describe a milder defect, appears in no committed report, and has never been put to Taylor. It is
  likely to keep being accepted under the older, smaller description unless it has its own id.
- Proposed `A-PRE-FILLED-ANSWER-WITH-A-PENDING-NOTE-PASSES-THE-HUMAN-GATE`, or fold into whatever id
  already carries the answer-bracket trap if one exists: `unanswered_frozen` should treat an answer
  line that also says "pending" as unanswered.

## What was not checked

- The full gate, `check_gate_bite`, pytest, and whether `--advance` at stage 11 actually sets
  `loop: completed` from this worktree.
- What was said in session beyond the brief, including whether the four-bet question named the
  MAINT-34 prices, which is what the blocker turns on.
- Whether `loop_fleet.py` reads the phase 14 pointer from this tree or the `phase-14` worktree, and so
  whether removing that worktree is needed for the lane to leave the board.
- The poker content of any of the five defects; this task changes none of it.
