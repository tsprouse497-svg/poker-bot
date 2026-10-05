# MAINT-44 independent review

Read-only pass over `git diff 0f46d46..HEAD` (14 files). No tests or gate run.

## Findings

1. Non-blocker. `backlog.yml:31-32` (NO-PHASE-OWNS-A-TURN-REACHED-AFTER-A-HEURISTIC-ANSWER): "the turn is stored rather / solved" is missing "than".
2. Alignment. `docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md:95` on main still says "Do not commit turn or river spots", while `AGENTS.md:147`, `docs/ROADMAP.md`, `docs/V2_ROADMAP.md:63,91` and phase 22's contract (line 27, "Phase 21 now solves and stores the turn") say phase 21 stores the turn. True only of the phase 21 lane, which has not merged (exec plan lines 13, 26, 44). Until it merges main contradicts itself; confirm 21's lane carries the amendment, and file it in `backlog.yml` if not already.
3. Non-blocker. `backlog.yml` LIVE-TURN-AND-RIVER-SOLVING keeps questions (4), (8), (9) worded for the turn; the added re-ruling note maps (4), (9), (10) to the river but not (8) (pots with 3+ players, "those turns"). Turn is now stored, so (8) should read river and turn-lookup. Minor.
4. Non-blocker. The old ids with "TURN"/"TURN-AND-RIVER" in them (LIVE-TURN-AND-RIVER-SOLVING, THE-FLOP-CAMPAIGN-...-TURN-RANGE-SOURCE, NO-PHASE-OWNS-A-TURN-...) still name the turn as a live or range target; the phase 22 contract (lines 47-48) says the id predates the re-ruling. Acceptable, ids are not renamed.

## Checks with no finding
- Live-turn grep: no live doc still says the turn is solved at the table. Remaining hits are history ("first ruled", "re-ruled") or the river.
- Rename consistent: `phase_status.yml:106-109`, `STATUS.md:33`, `docs/PHASE_LEDGER.md:25`, `docs/ROADMAP.md:26`, `docs/V2_ROADMAP.md:87` all say Turn And River Play. Only remaining "Live Turn And River" is the deliberate history line at contract line 23. No stale PHASE_22_LIVE path.
- Phase 22 contract states the re-ruling faithfully (stored turn, river live, one-second limit, 25 ms) and lines 41-42 present "plays the stored turn" as the coordinator's assignment, not Taylor's ruling. Nothing pre-ruled: gate, where the solve runs, and fallback stay human-gate questions.
- Backlog edits accurate to the re-ruling; the third entry correctly says the re-ruling changes nothing for a line phase 19 answered by rule of thumb.
- Figures: 1,755 x 49 = 85,995; 85,995 x 48 = 4,127,760. Correct everywhere seen.
- ALL-CAPS hyphenated phrases in changed prose are all real backlog ids (all seven grep as `id:` once). No R2-1 style labels found.
- Loop policy and phase 20 edits (turn and river -> river) consistent with AGENTS.md.

## Held back
- Did not open the other backlog entries that mention the turn but were not edited (A-FLOP-ONLY-STRATEGY..., A-VOIDED-TURN...); their text may still assume a live turn.
- Did not verify the exec plan's claim that the phase 21 lane carries the stored turn; that is in a different worktree.
- Generated docs (STATUS.md, BACKLOG.md, PHASE_LEDGER.md) not checked for freshness against generators.

## Verdict
No blockers; approve after fixing the typo and confirming the phase 21 lane carries the contract change.
