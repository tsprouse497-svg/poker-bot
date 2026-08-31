# MAINT-29: the review machinery reads shape, not content

Three checks pass by looking at the form of a file rather than at what it says. All three were found
while phase 14 sat halted, two of them by an independent reviewer, and all three must land before any
phase restarts: they are the checks that decide whether a stage may advance.

## Scope

`task_mode: maintenance`. `approved_scope` is `scripts/loop_stage.py`, `scripts/quality_checks.py`
and their two test files; `backlog.yml` is standing. No contract is touched, so no semantic contract
change is in play and `contract-update` is not needed.

## The three defects

**1. `RESOLVED-MARKER-MATCHES-INSIDE-A-BLOCKER-S-OWN-PROSE`.** `loop_stage.unresolved_blockers`
(`scripts/loop_stage.py:180`) closes a bullet when `RESOLVED_MARKER` appears anywhere in its first
line, including inside backticks and including a sentence whose point is that the marker was wrongly
applied elsewhere. Phase 14's stage-01 note opens a blocker with "the stage-6 note's `[resolved]` on
blocker B2 is false", so the driver and `review_queue` have counted that open finding closed since
2026-08-30 - and it is the one that says the defect survived the re-source. Nothing advanced on it
only because two sibling blockers were genuinely open.

The same line reads only the bullet's first line, so the defect also runs the other way: a marker
written on a continuation line is missed and an actually-closed blocker holds its stage forever.

Fix: gather each bullet across its continuation lines, and recognise the marker as a leading token on
the bullet rather than as a substring.

**2. `LOOP-REVIEW-CHECK-IS-BLIND-TO-A-RESTART`.** `check_stage_review` asks only whether
`reports/phase_audits/reviews/<PHASE>/stage-NN-name.md` exists and parses. On a restart every stage
from 1 to 5 already carries a note, so a whole re-run advances without one fresh review - the
opposite of what the per-stage review rule exists for. Phase 14 hit this when it was returned from
stage 6 to stage 1 and the driver reported "this stage's checks pass" throughout.

Fix: compare the note's newest round against the current `stage_base`. A note whose newest round
predates `stage_base` is a note about a different diff.

**3. `BACKLOG-VOCABULARY-IN-USE-IS-NOT-THE-VOCABULARY-THE-GATE-ALLOWS`.**
`quality_checks.ALLOWED_BACKLOG_STATUSES` is `{deferred, done}` and `NON_PHASE_LABELS` excludes
`tooling` and `source`, while eleven entries already carry `open` and five carry those phases -
twelve fatal errors from `backlog_errors`, which `run_full_quality_gate.py:121` treats as fatal at
`:137-139` and which `run_verify.py` registers as a gate command. Phase 14's deliberate `add_allin`
red has been masking the whole set, so the first green-gate attempt after any halt lifts would fail
on inherited state.

Fix is a judgment call this task must make and record: either declare `open`, `tooling` and `source`
in the constants, or re-file eleven entries. Declaring is the smaller change and matches what the
repo actually does; re-filing pretends the vocabulary was never in use. Whichever is chosen, the test
must assert the committed `backlog.yml` passes, so the constants and the file cannot drift apart
again.

## Delegation Plan

| lane | owner | output | status |
|---|---|---|---|
| A: blocker-marker parsing | worker subagent | `unresolved_blockers` gathers whole bullets, leading-token match, tests covering the quoted-marker and continuation-line cases | not started |
| B: restart-aware stage review | worker subagent | `check_stage_review` compares the note's newest round against `stage_base`, tests covering a stale note and a fresh one | not started |
| C: backlog vocabulary | worker subagent | constants reconciled with the committed file, test asserting `backlog.yml` passes its own gate | not started |
| D: independent review | read-only reviewer, not any of A-C | review notes before the gate | not started |

Lanes A and B touch the same file and are sequenced A then B rather than run in parallel. Lane C is
independent. The coordinator owns integration, the gate, and closeout, and implements none of A-C.

## Verification

Each fix owes a test that fails before it and passes after. Two are directly demonstrable against
committed evidence rather than synthetic fixtures: phase 14's stage-01 note is a real file whose
first round-2 blocker must count as open, and the committed `backlog.yml` is a real file that must
pass its own gate. Prefer those over invented ones - a checker that only ever sees fixtures is how
all three of these defects survived.

`uv run python scripts/run_verify.py` must pass on `main` after the merge, and `check_gate_bite` must
prove the mutations bite.

## Next Agent Bootstrap

Worktree `/Users/taylorsprouse/projects/poker-bot-worktrees/maint-29` on
`maint/29-review-machinery-reads-shape-not-content`, cut from `main` at `38845d7`. Read
`CURRENT_TASK.yml`, then this plan. The three backlog entries carry the full diagnosis with
file:line. Phase 14 is halted and unaffected by this work; do not touch its lane.

The one thing to know before starting: defect 1 currently hides a real blocker in
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/stage-01-contract.md`. Fixing it will make that
note report one more open blocker than it does today. That is the fix working, not a regression, and
phase 14's lane is expected to see its queue count rise.
