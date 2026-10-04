# MAINT-43 independent review: declare phase 22, Live Turn And River

- Reviewer: read-only subagent, wrote none of the change
- Diff: `git diff b41621b..HEAD` (one commit, `88c68a6`), worktree `maint-43`
- Read: `AGENTS.md`, the ExecPlan, the phase 22 skeleton, phase 19/20/21 contracts, both roadmaps,
  `docs/LOOP.md` stage table, `backlog.yml`, MAINT-40's declaration (`6eb0de4`), GTOpen's server
  and range/size parsers at `4aee435b`
- Ran (all read-only): `check_contracts`, `check_scope`, `check_repo_consistency`,
  `check_file_sizes` - all exit 0. Gate, gate-bite and pytest not run, per brief.
- Tags: blocker / non-blocker / alignment (alignment needs a `backlog.yml` id when filed)

## Blocker

1. **[blocker] Non-goal on storage goes past the ruling and contradicts the contract's own gate
   paragraph.** `docs/phase_contracts/PHASE_22_LIVE_TURN_AND_RIVER.md:63-64`: "Do not store turn or
   river solutions as committed data ... and a cache that persists across hands is storage."
   (a) Taylor ruled "solved at the table instead of stored", meaning committed artifacts. A
   cross-hand in-memory cache keyed on exact inputs is a runtime-reversible engineering choice he
   never ruled on; the clause pre-rules it. (b) As worded, the non-goal also forbids recorded
   solver answers committed as test fixtures - which is exactly the "likely shape" lines 51-53 name
   for the gate. Stage 1 inherits a contract whose non-goal bans its own suggested gate design.
   Fix: narrow to "as a committed strategy artifact the bot answers from"; drop the cache clause
   or move it to the list of open questions; say test fixtures holding recorded solver replies are
   not this.

2. **[blocker] Rule-of-thumb non-goal makes a false claim about phase 19 and pre-rules
   question 8.** `PHASE_22_LIVE_TURN_AND_RIVER.md:69-70`: "Heuristics are phase 19's, and a refusal
   here is a finding for it." Phase 19's lift is preflop only: `AGENTS.md:146` ("missing preflop
   chart spots") and `PHASE_19_HEURISTICS_AND_MERGED_CHARTS.md:58-59` ("reaches no further"). 19
   does not depend on 22, so it can never see 22's refusals anyway. Combined with
   `LIVE-TURN-AND-RIVER-SOLVING` question 8 (three-or-more-player pots have no GTOpen solve and
   "need their own answer"), the non-goal silently answers 8 as "refuse" with no owner - at a
   six-handed home game where multiway turns are routine, and where 20 now waits on 22 precisely so
   the bot stops refusing turns. Fix: strike the phase-19 sentence; state that what the bot does on
   a turn or river with no live solve (multiway, server missing or slow) is an open question for
   the human gate, not decided here.

## Non-blocker

3. **[non-blocker] Latency line calls an accepted figure a ruled limit.**
   `PHASE_22_LIVE_TURN_AND_RIVER.md:91-92`: "the limits Taylor ruled: the turn at the measured 1.7
   to 2.4 seconds". `AGENTS.md:147` says he *accepted* the turn at that figure and *set* a limit only
   for the river. Read as a ceiling, 2.4 s was measured on un-narrowed preflop ranges, fresh server,
   probably 5 of 10 cores (`docs/GTOPEN_SOLVER_NOTES.md:174,201`), and an off-menu size added to
   the tree (question 5) raises it. Reword: "the turn beside the 1.7-2.4 s he accepted, the river
   beside the one-second limit he set". Also unnamed: question 6 forbids a wall-clock stop, so the
   one-second river limit can only be measured, not enforced at runtime without breaking
   determinism. That tension belongs in the contract or the backlog entry.

4. **[non-blocker] "Kept outside the repo" reads as Taylor's ruling; he did not say it.**
   `PHASE_22_LIVE_TURN_AND_RIVER.md:32-34` ("He ruled it knowing ... and that it stays a sibling
   clone outside this repo") and `backlog.yml:49-51` ("chosen knowing it has no licence and kept
   outside the repo"). His words were only "use GTOpen, I don't want to build our own solver". The
   outside-the-repo rule and the non-goal at line 66 are existing practice / coordinator choice;
   attribute them as such. Also: the licence problem is not resolved by keeping the clone outside;
   record it as an accepted risk the way `PHASE_20_HOME_GAME.md:37-41` records the platform risk,
   so no stage reads the ruling as having disposed of it.

5. **[non-blocker] Gate paragraph leans, and "stage 1 settles" disagrees with the policy.**
   `PHASE_22_LIVE_TURN_AND_RIVER.md:47-53` names "the likely shape" (recorded answers) then says
   nothing pre-rules it. The lean is honest and disclaimed, so not a blocker, but line 47 says stage
   1 settles the gate and the one-session issue, while `verification/loop_policy.yml:157-165` says
   how it is tested is asked at the human gate (stage 3, `docs/LOOP.md:80`). Pick one: stage 1
   drafts, stage 3 asks. Question 7 (where the solve runs) is marked "Taylor's to rule" in the
   backlog entry; the contract (line 44) lists it as "this phase's" without saying so.

6. **[non-blocker] ASCII graph reads as 22 depending on 18.** `docs/ROADMAP.md:34-37`. The vertical
   bar from 18's `┐` now runs through `├─ 19` and `┤` down to `└─ 22`, so as a merge bus 18 and 21
   both feed 22. The caption at line 41 corrects it in prose, but the picture is the thing a human
   reads. Suggest splitting 21 before the bus:
   ```
   14 ─┬─ 18 ──────────┐
       │               ├─ 19 ──┐
       └─ 16 ─┬─ 21 ─┬─┘       │
              │      └─ 22 ────┤
              └────────────────┴─ 20
   ```
   Table (`ROADMAP.md:23-27`), `V2_ROADMAP.md` headings, `phase_status.yml`, loop policy, STATUS.md
   and PHASE_LEDGER.md otherwise agree with the frontmatter (22 -> 21; 20 -> 16, 19, 22).

7. **[non-blocker] Phase 20: reproducibility now has an unstated precondition.**
   `PHASE_20_HOME_GAME.md:44-46` keeps "a hand played at a table is still reproducible from a record
   afterwards". With a live GTOpen solve that is true only if the record carries the solver commit
   (possibly a patched local clone - phase 21 is patching thread use), the posted config, the
   iteration count, and the thread count/machine, since phase 16 proved byte-identical output on
   one machine only. Neither 20 nor 22 says so. Not a contradiction to strike, but 22's question 6
   should name "what a live decision records to be reproducible". Also line 45-46 "an action the
   offline strategy would not have taken" now reads ambiguously; "the strategy" would do. Lines 44,
   58 and 59 run past the file's wrap width (cosmetic). The three phase-20 edits otherwise remove
   the contradictions and nothing more.

8. **[non-blocker] Adoption is right but thin; MAINT-40 adopted seven, this adopts one.** These
   open entries are things a phase-22 builder will hit, and none is named by the contract:
   - `THE-GATE-ENFORCES-A-SEAM-SENTENCE-THIS-PHASE-MEASURED-AS-FALSE`: frozen
     `tests/test_postflop_betting_report.py:497-499` asserts the report says "refuses every turn",
     `scripts/generate_postflop_betting_report.py:2347` emits it, and phase 16's contract (line 270,
     at its line cap) obliges it. Phase 22 makes it false and must move all three, through a freeze
     re-open and a fold-in rewrite of a completed contract.
   - `A-COMMITTED-CELL-CARRIES-NO-STREET-SO-THE-IMPORTER-CHECKS-EVERY-BET-AGAINST-THE-FLOP-MENU`:
     any turn answer routed through `PostflopCell` is refused as off-menu at 66 percent.
   - `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` and
     `A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED`: both sit at completed phase 16 and are
     closed or changed by a working turn. The first also binds question 5/9: the flop was solved
     against a 66/125 turn menu, so a live turn tree on any other menu breaks consistency with the
     flop above it.
   Adopt or at least cite them. Minor: the entry's title "... and nothing builds it"
   (`backlog.yml:6`) is now stale.

9. **[non-blocker] Naming is clean.** `pytest_live_turn_river_solve`, `generate_live_solve_report`,
   `latest_live_solve_report.txt` are phase-free and descriptive. The only ALL-CAPS hyphenated
   tokens added are `LIVE-TURN-AND-RIVER-SOLVING` (a real id) and `MAINT-40/42/43` task ids.
   `LICENSE` at contract line 33 is unhyphenated.

## Alignment

10. **[alignment] Phase 21 is in flight and does not know 22 reads its output as a range source.**
    A committed flop cell is one decision node, one player's per-class strategy
    (`data/artifacts/postflop/sample/*.json`: `hand_classes`, `class_weights`), and
    `docs/ROADMAP.md:9` says no node that follows a committed one is committed. A turn range needs
    every flop node on the line played, both players, including the call node. Objects that might
    hold the whole tree live at a local directory with "no remote store provisioned"
    (`index.json` `object_storage`), so the table machine would need them too. Phase 21's contract
    has no criterion to commit lines closed through the turn. Cheapest to settle while 21 is
    running; file a backlog entry and tell the phase 21 lane.

11. **[alignment] Nobody owns a turn reached through a heuristic line.** 19 fills preflop (maybe
    flop) gaps with rules of thumb and does not depend on 22; 22 does not depend on 19. A turn
    after a substituted preflop or flop answer has no solved range to start from. Only phase 20
    integrates both. File it so 22's or 20's stage 1 owns it.

## Checked and fine

- Phase 22 recorded consistently in frontmatter, `phase_status.yml:105-109` (future),
  `verification/loop_policy.yml:157-165` (`auto_advance: false`, `needs_human_data: false`),
  both roadmaps, generated STATUS.md and PHASE_LEDGER.md. Shape matches MAINT-40's declaration of 21.
- The four rulings are present and faithful in contract lines 30-39, the ExecPlan and roadmaps.
- No other live document contradicts 22: phases 18, 19, 21 still forbid runtime solver calls for
  themselves, which is right; `AGENTS.md:147` names the owner; `V2_ROADMAP.md:63,67,85,152` agree.
- GTOpen engineering: ranges are per-combo strings (`crates/solver/src/range.rs:1-13`, e.g.
  `AhKh:0.5`), so narrowed turn ranges can be posted exactly. Bet sizes are arbitrary positive pot
  percentages and raise multiples > 1 (`crates/solver/src/tree.rs:24-54`), so an off-menu size can
  be added. But every root starts at the start of a street with OOP to act, and a size added to a
  street list becomes an option at every node of that player on that street, so "re-solve with the
  size added" changes the whole street's tree, not one branch. Worth one line in question 5.
- Edges: 22 reaches 16 through 21, so it has the postflop machinery. Whether it also needs 18 to
  measure off-menu mapping and anchoring (the argument 19 uses) was not ruled, and adding the edge
  would itself be a pre-ruling, so not raised as a finding.

## Held back

- Turn latency figures were measured at likely half the cores
  (`GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`, phase 21's); the 1.7-2.4 s
  baseline may move when 21 fixes thread use, and AGENTS.md quotes it as the accepted figure.
- GTOpen's server never returns freed memory (`GTOPEN_SOLVER_NOTES.md:145`); a long-lived table
  server will drift slower across a session, which bears on both latency and the one-session issue.
- The legal side of running an unlicensed public repo at all (not just shipping it) is untested;
  outside a review's competence.
- `scope_change_log` keeps growing with duplicate-shaped entries
  (`THE-SCOPE-CHANGE-LOG-IS-NEARLY-HALF-DUPLICATES-AND-A-MERGE-PUT-THEM-THERE`), unchanged here.
- Did not run `loop_fleet.py --plan` from `main` to confirm 22 shows ineligible.

## Verdict

Two blockers, both in the phase 22 non-goals (storage clause, phase-19 heuristic clause); fix
those and the declaration is sound.
