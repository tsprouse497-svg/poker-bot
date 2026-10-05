# Phase 21 stage 6: river not stored, contract-update review

Read-only review by a subagent that wrote none of the change, 2026-10-04, of the contract-update for
Taylor's re-ruling of decision 1: the turn is stored, only the river is solved at the table. Findings
as written; responses follow.

## Blocker
None in the contract text. Precondition outside this task: `AGENTS.md`, merged from `main`, still says
the turn and the river are solved at the table, and by its own rule `AGENTS.md` wins over a contract;
phase 22 on `main` was declared with a live turn too. The lane should not leave this re-ruling's
work for a merge until that correction is on `main`. Response: the correction belongs to the session
declaring phase 22 (MAINT-43), and Taylor has been asked to give it his turn ruling; this lane's merge
waits on it, recorded in the ExecPlan.

## Non-blocker
- The contract says what was ruled, no more and no less; no river obligation survives and no turn obligation was dropped (decision 4's archive, decision 15's two-byte rows, the trial measurement, the closure manifest, the check before archiving). The memory bar and card memory stay right, since the solve still builds the whole tree.
- "The manifest carries each board's counts per street" read as if the manifest still carried a river count. Response: now "each board's flop and turn counts".
- "until the next phase" disagreed with "a later phase" elsewhere. Response: now "in this phase".
- Decision 4's Glacier choice was justified by about 22 TB, mostly river; turn only is about 116 GB for five lines, a few dollars a month in the standard class with no 12 to 48 hour restore. The contract states the ruling correctly; whether Taylor still wants the archive at this size is his. Response: put to him.

## Alignment
- `TURN-AND-RIVER-PLAY-FROM-THE-SAVED-SOLVES-NEEDS-ITS-OWN-PHASE`: its title is now false for the river; restated as turn only.
- `LIVE-TURN-AND-RIVER-SOLVING`: lives on `main` with the turn live; the same correction as `AGENTS.md`, owned by the session declaring phase 22.
- `TURN-AND-RIVER-SIZES-CLAMPED-TO-ALL-IN-HAVE-NO-NAME-IN-ANY-SPOT-KEY`: still holds for stored turn keys; the river half moves to the live-solving work.

## What the reviewer did not look at
The rest of the decision list, the ExecPlan's turn slices, and the live river timing `AGENTS.md`
cites. Frozen tests it expects to re-open: `tests/test_flop_campaign_manifest.py` (river in the
closure counts and their mutations), `tests/test_flop_campaign_report.py` (the one-river-point-short
and dealt-turn-river tests), `tests/test_flop_campaign_street_rows.py` (river rows), and
`tests/test_flop_campaign_tree.py` only if `closure_counts` stops returning the river.
