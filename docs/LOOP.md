# The Autonomous Phase Loop

`AGENTS.md` holds the behavior rules.
This document explains the loop that drives a phase from a skeleton contract to a tagged gate, and where a human still has to stand.

The loop's state lives in `scripts/loop_stage.py` and `verification/loop_state.yml`, not in a prompt.
A fresh session resumes at the same stage because the driver's output is the only source of truth about what comes next.
Stage order cannot be skipped, because advancing runs a check rather than accepting a claim that the stage is done.
A crash costs one stage rather than a phase.

The driver never changes the repo apart from its own state file.
It instructs and it verifies; the session performs the actions, so every destructive step still goes through the normal permission path.

## Running it

```
uv run python scripts/loop_stage.py --start 06   # begin a phase
uv run python scripts/loop_stage.py              # what stage am I on, what do I do
uv run python scripts/loop_stage.py --advance    # verify this stage and move on
uv run python scripts/loop_stage.py --halt "..." # record a halt and stop
uv run python scripts/loop_stage.py --resume    # return a halted loop to its stage
uv run python scripts/loop_stage.py --phase 11  # pick a lane when several are running
```

The loop body is always the same: read the driver, perform the one stage it names, call it again.
`--advance` refuses to move while its stage's check is failing, and prints why.
It also refuses while the stage owes a review, which is explained below.

## Running several phases at once

`scripts/loop_fleet.py` drives the board rather than a phase.
A lane is a git worktree on its own `phase/NN-slug` branch, holding its own pointer under `verification/loop_runs/`, so two lanes never write the same file and neither can see the other's half-finished work.

```
uv run python scripts/loop_fleet.py --plan          # which phases may start now
uv run python scripts/loop_fleet.py --status        # every lane and its stage
uv run python scripts/loop_fleet.py --tick          # ask every lane what it needs next
uv run python scripts/loop_fleet.py --start-lane 11 # the runbook that opens a lane
uv run python scripts/loop_fleet.py --integrate 11  # the runbook that merges one back
uv run python scripts/review_queue.py --list        # everything waiting on a human
```

Like the stage driver, the fleet driver is read-only.
It computes and it instructs; the session performs every action, so creating a worktree, seeding a task, merging a branch and moving a tag all still pass through the normal permission path.
That is also what makes `--status` and `--tick` safe to run against live lanes.

Eligibility comes from the contracts' `depends_on`, and it is measured against `main` rather than against the local branch.
A dependency counts as met only once it is `completed` on the integration branch, because that is the only place a phase is genuinely finished.
Reading it locally would let a lane start against work that exists nowhere but a sibling's checkout.
`check_repo_consistency` rejects a `depends_on` that names a phase which does not exist or that closes a cycle, because both surface as a fleet reporting nothing eligible and explaining it as ordinary waiting on a dependency.

Integration is deliberately serial.
Lanes collide on `verification/freeze.lock`, `verification/mutations.yml`, `phase_status.yml`, `backlog.yml`, and the generated documents, so one lane merges at a time, the generated files are rebuilt on the merged result, and the full gate plus `check_gate_bite` run again before the tag.
Every other live lane then rebases onto the new `main`.
A lane that goes red because a sibling merged goes back to stage 6; it is not repaired from the integration step.

## The pause board

`scripts/review_queue.py` collects everything across the fleet that is waiting on a human, so a lane stops rather than guessing and the stop is visible from one place.

It is derived, never recorded.
A second file listing the open questions would be a second source of truth about them, and it would go stale the moment someone answered one in the file that actually governs it.
So the queue reads the six places a human ask already lives: an unanswered `frozen-into-data` item in a decision list, an open `## Blocker` bullet in any stage's review notes, an `auto_advance: false` phase that has reached stage 11, a `needs_human_data` phase that cannot start at all, a `- Paused:` reason declared in an active ExecPlan, and a lane pointer sitting at `loop: halted`.
Answering happens in the real file and the entry disappears, because the next run re-derives.

Nothing about the board is committed.
It depends on which worktrees exist on this machine, so a checked-in copy would differ between machines and could never be verified by the gate.
Its shape is covered by `tests/test_loop_fleet.py` instead.

## The eleven stages

| # | Stage | Runner | Advance check |
|---|-------|--------|---------------|
| 0 | precheck | script | lock held, on a `phase/` branch, clean tree |
| 1 | contract | model | `contract-update` mode, contract carries real criteria, ExecPlan active |
| 2 | decisions | model | every judgment call declares a reversibility class |
| 3 | human gate | human | no unanswered `frozen-into-data` item remains |
| 4 | tests | model | the phase's `pytest_*` command fails, on an assertion or on a missing `poker_training_bot` module |
| 5 | freeze | script | `check_test_freeze` green, `tests/` and `verification/` out of scope |
| 6 | build | model | every command the contract declares is green |
| 7 | gate | script | full `run_verify.py` green, `check_gate_bite` green |
| 8 | review | model | review notes exist covering mechanical, domain, and blocker status |
| 9 | audit | model | audit packet names summary, checklist, review, decisions, and a recomputable number |
| 10 | closeout | script | phase completed, ExecPlan filed, tag present, idle, clean tree |
| 11 | advance | script | policy decides: continue, or halt with the one human ask |

## The review every stage owes

Stage 8 is the phase's full review and it is not the only one.
A stage cannot advance while it owes review notes, and it owes them whenever its diff touched something a human wrote.

The trigger is the diff rather than a list of interesting stages.
That way a stage with nothing to review is skipped without anyone judging it uninteresting, and a stage that starts doing real work is caught the first time it does.
Both matter in practice: v1 authored mutation canaries at stage 7 twice, which is work that escaped the stage that was supposed to do it.

The diff is measured from the commit the driver recorded at the last advance, kept in `verification/loop_state.yml` as `stage_base`.
Not every stage ends in a commit, so a diff sometimes spans two stages: wider than the stage, never narrower.
A state file with no recorded base falls back to the phase's branch point, so a loop started before this rule existed cannot skip its reviews by predating them.

Six paths never count, because no human writes a judgment into them: `verification/loop_state.yml`, `verification/freeze.lock`, `CURRENT_TASK.yml`, `phase_status.yml`, `reports/active/**`, and the review notes themselves, without which writing a review would demand a review of the review.
`CURRENT_TASK.yml` and `phase_status.yml` are bookkeeping that `check_scope`, `check_frozen`, and `check_closeout` already enforce exactly.

Notes go to `reports/phase_audits/reviews/<CONTRACT_STEM>/stage-NN-name.md` and carry three headings.

- `## Blocker` must read `None.` or list only bullets marked `[resolved]`. Anything else refuses the advance. A fixed blocker stays in the note and gets marked, because deleting it loses the record of what the reviewer caught.
- `## Non-blocker` is everything the stage can carry.
- `## Alignment` is long-term drift the stage cannot fix, and each item needs a `backlog.yml` ID. Without the ID it is a note nobody reads again.

Each stage declares the one question its reviewer should ask, and the driver prints it with the diff scope and the note path, so the brief comes from the loop rather than from whatever the session improvises.
Stage 8 keeps its own rule: two reviewers, mechanical and domain, required whatever the diff says.

Review notes written before this existed are single files named for the phase; they were moved to `stage-08-review.md` inside their phase's directory and keep their original prose.

## Why the ordering matters

Tests are authored at stage 4, before any implementation exists, and frozen at stage 5.
The builder at stage 6 may read `tests/**` but cannot write to it, because stage 5 removes it from `approved_scope` and `check_scope.py` enforces that mechanically.
This is the loop's central protection: without it, the thing being tested and the test for it are written by the same mind, agreeing with each other, both possibly wrong.

Stage 7 does not stop at a green gate.
`check_gate_bite` applies each mutation in `verification/mutations.yml` and requires the gate to notice.
A surviving mutation means the gate is decorative for that behavior, which a green run cannot otherwise reveal and a test freeze cannot catch, because freezing preserves a weak test perfectly.

## Reversibility, and when a human is required

Every judgment call in a decision list declares one of two classes.

- `runtime-reversible`: the choice only changes behavior at query time, so a later edit can change it. The loop takes the recorded default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice gets written into a committed artifact or fixture that later phases are then measured against. The loop halts until a human answers.

`verification/loop_policy.yml` applies the same rule at phase granularity.
A phase may auto-advance when it writes no new committed data.
`needs_human_data` marks a phase that cannot start at all until Taylor supplies an input the repo does not have, and the driver refuses `--start` for it rather than letting a session invent the input.

## Halt conditions

The loop stops rather than pushing through:

- dirty tree, wrong task mode, or another session in this worktree
- an unanswered `frozen-into-data` decision
- a phase whose inputs are not in the tree
- a second failure on the same gate command, because a model failing twice on one assertion is usually about to weaken it
- any builder diff under `tests/**`, `verification/**`, `AGENTS.md`, the check scripts, the command registry, or the scope keys
- any new or changed file under `data/artifacts/**` or `data/samples/**`
- a falling test count or a changed frozen hash
- a surviving mutation
- a blocker finding that survives a second review round

## The machinery

- `scripts/loop_stage.py`: the state machine described above.
- `scripts/freeze_tests.py`: writes `verification/freeze.lock`; `--check` verifies it. The writer is deliberately absent from the gate, because a gate that refreshes the lock every run is not a freeze.
- `scripts/check_gate_bite.py`: applies `verification/mutations.yml` in place, requires the named command to fail, restores, and then re-runs the command to prove the restore worked. It purges cached bytecode around each mutation, because CPython validates a `.pyc` by mtime and size and an equal-length mutation changes neither.
- `scripts/check_repo_consistency.py`: cross-checks that declared gate commands are registered, that every `pytest_*` command names a file holding tests, and that phase status agrees with where the ExecPlan lives.
- `scripts/check_scope.py`: reads the scope the task started from out of `base_commit`, so widening `approved_scope` or shrinking `forbidden_scope` needs a new `scope_change_log` entry. It also rejects patterns where `*` crosses a directory separator, and requires a real commit sha while a task is open.
- `scripts/check_contracts.py`: requires an active or completed phase to carry acceptance criteria that are not gate boilerplate.

## Known gaps

Four things this machinery cannot catch, kept here rather than in a commit message.

Merging a lane rewrites `verification/freeze.lock`, which is a real softening of the freeze.
Two lanes each froze their own suite, so the merged lock describes a suite neither of them locked, and the rebuild is the only way to get one that does.
What keeps it honest is who does it and when: the integrator, on a branch whose tests were already frozen at stage 5, built against at stage 6, and reviewed at stage 8, never a builder and never before stage 5 in any lane.
The freeze still does its one job, which is stopping the thing being tested and the test for it from being written by the same mind.

A test that was wrong when written survives every mechanical check above.
Freezing preserves it, and mutation canaries only prove that *something* fails, not that the assertion is right.
The reviewers are the only guard: the one stage 4 owes before the freeze, and the domain-focused pass at stage 8, which is why stage 8 stays even when the gate is green.

Range and strategy quality has no oracle in this repo beyond a committed solver export.
Every shape property is satisfied by ranges that are uniformly wrong.

Every layer of the loop is the same base model: contract author, test author, builder, and both reviewers.
A shared misunderstanding is invisible to all of them at once.
That is why decision lists are written in poker English rather than in code, so a human's domain knowledge has somewhere to bite.
