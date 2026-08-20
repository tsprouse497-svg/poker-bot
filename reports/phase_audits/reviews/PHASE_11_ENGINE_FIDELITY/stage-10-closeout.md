# Phase 11 stage 10 (closeout) review

Read-only pass over `git diff 3993f48 -- docs/exec_plans/completed/PHASE_11_ENGINE_FIDELITY.md`.
Question asked: bookkeeping only. A content change here belongs to an earlier stage and
should be named as one.

Reviewer: coordinator, self-review; subagents are unavailable in this session.

## Blocker

None.

## Non-blocker

- The diff is the ExecPlan's five remaining slices marked done, its Outcome filled in, and
  its bootstrap rewritten to say what the next agent has to do - which is the merge, since
  the lane is not integrated by the closeout. All of it is bookkeeping about work the
  earlier stages did and reviewed. No claim in it is new: the Outcome's three paragraphs
  restate the audit packet, and every figure in them appears there first.
- One thing in the Outcome is a judgment rather than bookkeeping, and it is named as one:
  that authoring canaries at stage 4 against text the implementation did not yet contain is
  worth repeating. Four of four matched and bit, against three prior phases that each wrote
  their own canaries after the code and each filed that as the same miss. It belongs in the
  plan's retrospective rather than in a contract, and it changes nothing in this phase.
- The closeout hit `LOOP-STAGE-10-DEMANDS-A-REVIEW-IT-FORBIDS-WRITING` exactly as filed.
  Stage 10 requires `task_mode: idle`, idle carries an empty `approved_scope`, and
  `reports/phase_audits/reviews/**` is not in `standing_scope`, so the note this stage owes
  is out of scope by construction. It passes only because idle leaves `base_commit` null,
  which makes `check_scope` measure against `HEAD` and an already-committed file invisible
  to it. That is a loophole and not a pass, and it is the second phase in a row to lean on
  it. The item is filed against whoever owns `loop_stage.py`.
- One quality-gate failure at this stage, fixed: the bootstrap wrapped a backlog id across
  a line break, so the gate read the fragment before the hyphen as an id nobody created.
  The prose now names the item instead of citing it. Third time this repo has hit the
  capitalised-token rule; the escape hatch lives in a file this phase may not touch.

## Alignment

- `LOOP-STAGE-10-DEMANDS-A-REVIEW-IT-FORBIDS-WRITING` (existing, `phase: contract-update`).
  Unchanged, and now with a second phase's worth of evidence that the loophole is the only
  thing making stage 10 passable.
