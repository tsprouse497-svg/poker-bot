# MAINT-25: a task whose whole output is one backlog entry still has to invent an ExecPlan

Task: `maint-execplan-for-a-filing`. Mode: `maintenance`. Base: `db626b5`.

## Objective

File `EXECPLAN-REQUIRED-FOR-A-TASK-WITH-NO-IMPLEMENTATION`, and correct one false sentence
MAINT-24 wrote while deciding not to file it.

`check_execplan_delegation.py` requires at least one plan in `docs/exec_plans/active/` for every
`task_mode` that is not `idle`.
MAINT-24's whole output was a single backlog entry, and it still had to write a plan whose
Delegation Plan is a no-delegation exception and whose slices were complete before the plan
existed.
This plan is the second instance of the same shape, which is the argument for the entry.

## Why it is worth filing after all

MAINT-24 declined to file it as "process shape rather than a defect".
That was too generous, on evidence MAINT-24 did not have.

`9eec03d`, the seam filing, was committed with `task_mode: maintenance` and nothing but
`.gitkeep` tracked in `docs/exec_plans/active/`.
The check has been byte-identical since `4d4d528` built it, so that commit either had a red gate
or had an untracked plan that is now gone.
`AGENTS.md`'s Task Closeout requires a passing gate before the commit, so both readings are
process failures, and neither was noticed for a day.

A requirement that gets skipped and not caught is a defect in the requirement or in the gate's
reach, not a matter of taste.

## The correction MAINT-24 needs

MAINT-24's Alignment section says MAINT-23 passed the same gate without a plan only because a
paused phase plan happened to be sitting in `active/`.
That is false. `fd77388` tracks `MAINT_23_PHASE_11_BACKLOG_CLOSEOUT.md` in `active/`, and
MAINT-23 satisfied the check the ordinary way.

Leaving it would put a false claim about how the gate behaves inside the record of a task about
being misled by a file that reads as current state.
The sentence is corrected in place, marked as corrected, and the real evidence named.

## Scope

Approved: nothing beyond standing scope. Every file this task touches is already standing.

Standing: `backlog.yml`, `docs/BACKLOG.md`, `CURRENT_TASK.yml`, `STATUS.md`,
`docs/exec_plans/**`, `reports/active/**`.

Deliberately untouched: `scripts/check_execplan_delegation.py`, `AGENTS.md`, and
`docs/DEFINITION_OF_DONE.md`.
The fix is a ruling about which of three directions the repo wants, and the check and `AGENTS.md`
have to move together or not at all.

## Delegation Plan

- No-delegation exception: subagents are unavailable in this operator's sessions - the standing
  instruction is not to call the Agent tool unless asked - so `AGENTS.md` step 10's self-review
  fallback applies, recorded here and performed below.

## Slices

- [x] Slice 1: `EXECPLAN-REQUIRED-FOR-A-TASK-WITH-NO-IMPLEMENTATION` filed as `contract-update`,
  naming the three candidate directions and the `9eec03d` evidence.
- [x] Slice 2: MAINT-24's false sentence about MAINT-23 corrected in place and marked as
  corrected.
- [x] Slice 3: `docs/BACKLOG.md` regenerated, read-only self-review, full gate.

## Verification

`uv run python scripts/run_verify.py` - the full derived gate, no new command ids.
Filing only, so no report a gate command regenerates may move apart from the gate's own records
and `docs/BACKLOG.md`.

## Read-only self-review

Reviewer: coordinator, self-review, per the no-delegation exception above.

Question asked: is the `9eec03d` evidence solid enough to carry the entry, and does the entry
overstate the problem?

- **No blocker.**
- The evidence was read from git rather than inferred: `git ls-tree 9eec03d docs/exec_plans/active/`
  returns `.gitkeep` alone, `git show 9eec03d:CURRENT_TASK.yml` says `maintenance`, and
  `git log -- scripts/check_execplan_delegation.py` shows no commit after `4d4d528`.
  The `elif not paths` branch at that commit was read directly and is identical to today's.
- Which of the two readings of `9eec03d` is true cannot be settled from the repo, and the entry
  says so instead of picking the more damning one. Both are process failures, so the entry does
  not need the stronger claim.
- The entry deliberately records that MAINT-23 passed honestly. Without that line the entry reads
  as "this requirement cannot be met", which is untrue and would push the ruling toward removing
  the check rather than deciding what a filing owes.
- This task is its own second data point, which is worth being uneasy about: a task that files a
  complaint about ExecPlan overhead while producing an ExecPlan could be talking itself into a
  finding. The check against that is `9eec03d`, which was committed by neither this task nor
  MAINT-24 and which nobody was looking for.
- Worth stating rather than leaving implicit: this task changes no behaviour and fixes no defect.
  It files one and corrects one sentence.

## Alignment

- Three `contract-update` items now wait on the same owner and overlap in subject:
  `FLEET-AND-STAGE-DRIVERS-DISAGREE-ABOUT-INTEGRATION`,
  `COMPLETED-LANE-POINTERS-ARE-NEVER-RETIRED`, and this one.
  Ruling on them one at a time invites three inconsistent answers about what the loop's
  bookkeeping is for. Long-term drift no filing task can fix, because the fix is the ruling.

## Outcome

One item filed. One false sentence in MAINT-24 corrected in place. `docs/BACKLOG.md` regenerated.
Gate green with no source, test, fixture, pointer, or committed report changed apart from the
gate's own records.

## Next Agent Bootstrap

Repo is on `main` in `~/projects/poker-bot-worktrees/main`, idle after this task closes.
Phase 12 is live in `~/projects/poker-bot-worktrees/phase-12` at stage 8 and is not this task's
business.
The three `contract-update` items above want one ruling between them, from whoever owns
`scripts/loop_stage.py`, `scripts/loop_fleet.py`, and `scripts/check_execplan_delegation.py`.
Nothing here blocks phase 13.
