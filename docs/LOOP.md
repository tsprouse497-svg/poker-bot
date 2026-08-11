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
```

The loop body is always the same: read the driver, perform the one stage it names, call it again.
`--advance` refuses to move while its stage's check is failing, and prints why.

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

Three things this machinery cannot catch, kept here rather than in a commit message.

A test that was wrong when written survives everything above.
Freezing preserves it, and mutation canaries only prove that *something* fails, not that the assertion is right.
The domain-focused reviewer at stage 8 is the only guard, which is why it stays even when the gate is green.

Range and strategy quality has no oracle in this repo beyond a committed solver export.
Every shape property is satisfied by ranges that are uniformly wrong.

Every layer of the loop is the same base model: contract author, test author, builder, and both reviewers.
A shared misunderstanding is invisible to all of them at once.
That is why decision lists are written in poker English rather than in code, so a human's domain knowledge has somewhere to bite.
