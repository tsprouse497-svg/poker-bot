# MAINT-17: A Reviewer At Every Stage That Produced A Diff

## Objective

The loop has one review and it is stage 8, after the gate is green.
By then the tests are frozen, the implementation is written, and every finding is expensive.

v1's evidence is that the costly defects were all visible earlier.
A Phase 08 test rebuilt stacks from the converter's own output so it could not fail on the thing it existed to check, which a reviewer at stage 4 would have seen before the freeze.
Three committed documents stated an all-in count that counted only preflop shoves, and a pooled figure carried a `humans` label in four places, both of which a reviewer at stage 9 would have caught in the packet rather than in a later maintenance task.
Two phases never canaried the command they were adding.

This task makes the driver require a review at **any stage whose diff touches something a human wrote**.
The trigger is mechanical rather than a list of interesting stages, so it self-adjusts when a stage starts doing work it did not used to, and it never asks for a review of an empty diff.

## Scope

Approved: `scripts/loop_stage.py`, `docs/LOOP.md`, `tests/test_loop_machinery.py`, `verification/freeze.lock`, `verification/mutations.yml`, `reports/phase_audits/reviews/**`, and the five audit packets that cite a review path.

Forbidden: `AGENTS.md`, every phase contract, `phase_status.yml`, `verification/loop_policy.yml`, and everything under `src/`.
`AGENTS.md` is untouched on purpose: it already delegates stage order to `scripts/loop_stage.py`, so the driver adding a check contradicts nothing, and adding a behavior rule to that file is a semantic edit that needs its own `contract-update`.

## Design

**The trigger.** At each advance the driver records `HEAD` in `verification/loop_state.yml` as `stage_base`.
A stage's diff is the working tree against that commit, plus untracked files.
Not every stage ends in a commit, so a diff sometimes spans two stages: wider than the stage, never narrower, which is the safe direction.
A state file with no `stage_base` falls back to the phase branch point, so an in-flight loop cannot silently skip a review by having been started before this existed.

**What does not count.** Six paths are excluded because nobody writes a judgment into them: `verification/loop_state.yml` (the driver's own pointer, which changes on every advance by definition), `verification/freeze.lock` (computed hashes), `CURRENT_TASK.yml` and `phase_status.yml` (bookkeeping already enforced by `check_scope`, `check_frozen`, and `check_closeout`), `reports/active/**` (regenerated every gate run), and `reports/phase_audits/reviews/**` (without which writing a review would demand a review of the review).

**The note.** `reports/phase_audits/reviews/<CONTRACT_STEM>/stage-NN-name.md`, with three fixed headings.
`## Blocker` must read `None.` or list only bullets marked `[resolved]`, and the driver refuses to advance otherwise, which is the rule stage 8 already had.
`## Non-blocker` is findings that do not stop the stage.
`## Alignment` is the new one: long-term drift the stage cannot fix, and each item must carry a `backlog.yml` ID, because that is the difference between a finding and a note nobody reads again.

**The brief.** Each stage carries a one-line `review_focus`, printed by the driver along with the diff command and the note path, so the reviewer's question comes from the loop rather than from whatever the session improvises.

**Stage 8 is unchanged in substance.** Its two reviewers stay mandatory whatever the diff says, since its own output is excluded from the trigger, and its note keeps the mechanical/domain coverage requirement on top of the three headings.

## Delegation Plan

- No-delegation exception: subagent delegation is disabled in this operator's sessions, and this task was specified in conversation slice by slice with the operator ruling on the trigger design. Self-review at the end, recorded in the outcome.

## Slices

- [x] Slice 1: the trigger. `stage_base` in the state file, `changed_paths`, the exclusion list, and the fallback to the branch point.
- [x] Slice 2: the note. Path shape, the three headings, the unresolved-blocker rule, and `check_stage_review` wired into every advance.
- [x] Slice 3: `review_focus` per stage and the driver's printed brief.
- [x] Slice 4: repoint stage 8 at the new path and migrate the five existing review files into per-phase directories, with the audit packets that cite them.
- [x] Slice 5: tests, re-freeze, and a canary that makes the new rule bite.
- [x] Slice 6: `docs/LOOP.md`.

## Verification

- `uv run python scripts/run_verify.py`
- `uv run python scripts/check_gate_bite.py` proves the new canary bites.

## Outcome

All six slices landed, the gate is green, and `check_gate_bite` catches 31 mutations including the two new ones.

The driver now computes each stage's diff from `stage_base`, filters it through `UNREVIEWED_PATHS`, and refuses to advance when what is left has no review note.
Nine paths are excluded, three more than the design named: `STATUS.md`, `docs/PHASE_LEDGER.md`, and `docs/BACKLOG.md` were found by smoke-running the brief against this task's own diff, which asked for a review of three documents the gate regenerates.
A test now ties that list to the generators, so the exclusion has to track the commands rather than someone's memory of them.

Two canaries defend the rule, because both of its failure modes are silent.
`loop-review-trigger-never-fires` makes the trigger stop seeing hand-written work, and `loop-blocker-stops-blocking` lets a recorded blocker advance anyway, which is worse than having no review at all.

Self-review, since delegation is unavailable, found three things and all three are fixed.
The brief kept printing after the review was written, which trains a reader to skip it, so it now goes quiet once the stage's review passes.
The last-resort base was `HEAD`, which would have quietly narrowed a confused diff to uncommitted work only; it is now the empty tree, so a driver that cannot find its bearings asks for more review rather than less.
Stage 8's instruction never named the three headings its own note now has to carry, so a session would have written notes and then been refused for a format nobody told it about.

One known cost, accepted rather than fixed. A stage that leaves work uncommitted hands its diff to the next stage as well, so the next stage is asked for a review that partly covers its predecessor's work. That is wider than the stage and never narrower, which is the safe direction, and the alternative is the driver committing on the session's behalf, which would break the rule that it only instructs and verifies.

## Next Agent Bootstrap

The loop now demands a review note at any stage that produced a hand-written diff, so a phase run after this will stop more often than v1's phases did.
That is the intent; a stage with nothing to review is skipped mechanically rather than by judgment.

The one thing still owed is one line in `AGENTS.md`'s Autonomous Loop section saying the loop reviews per stage, which is semantic and needs its own `contract-update` before the next phase starts.
