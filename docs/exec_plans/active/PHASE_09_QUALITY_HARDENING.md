# ExecPlan: Phase 09, Quality, Drift, Backlog, And Phase-Gate Hardening

## Objective

Close the three ways this repo has already been wrong while every check passed:
a gate command no mutation points at, a number in a document that drifted from the data it describes, and a backlog entry that rots without anything noticing.

The gate is `run_full_quality_gate` plus `check_generated_status`, with a committed quality report and the phase audit packet.

## Scope

Approved, once implementation begins:

- `scripts/run_full_quality_gate.py` and the checks it runs
- `scripts/generate_repo_facts.py` and the committed facts file
- `verification/mutations.yml`, for the two uncovered commands
- `tests/test_quality_hardening.py`
- The command registry, the contract, the decision record, and the audit packet

Forbidden:

- Any change to the engine, replayer, charts, strategies, simulator, converter, or committed artifacts.
  A hardening phase that edits what it measures has proved nothing.
  If a new check goes red against the repo as it stands, that is a finding for its own task, not a reason to move the thing being checked.

## Delegation Plan

- No-delegation exception: subagent delegation is disabled in this operator's sessions for implementation, which is the constraint recorded in the Phase 06, 07 and 08 audit packets.
  It is not the constraint at review time any more: the Phase 08 stage 8 review was run by an independent reviewer with no knowledge of the work, and it found six things two self-review passes had missed.
  Stage 8 of this phase does the same, and the ExecPlan records that as the plan rather than as a bonus.

## Slices

- [ ] Slice 1: mutation coverage. Every registered `pytest_*` command is named by at least one committed mutation, exemptions are by name in the checker with a stated reason, and the two currently uncovered commands get canaries that bite. Evidence: the check fails when a mutation is removed.
- [ ] Slice 2: fact drift. A committed facts file, one generator that recomputes every fact from the repo, and a checker that fails when a document listed for a fact states a value the fact no longer has. Evidence: changing a fact's value reddens the gate until the documents quoting it are updated.
- [ ] Slice 3: backlog integrity. Schema, unique ids, cited ids resolve, phases exist. Evidence: each rule fails on a deliberately malformed entry.
- [ ] Slice 4: phase record agreement. Tag, ExecPlan location, audit packet, and status must agree for every completed phase. Evidence: the check names which phase and which record when they do not.
- [ ] Slice 5: `run_full_quality_gate` aggregates the four, prints per-check results, and writes `reports/active/latest_quality_report.txt` saying what each check covers and what it does not.
- [ ] Slice 6: audit packet, independent review, closeout.

## Verification

- `uv run python scripts/run_verify.py`
- `run_full_quality_gate`, `check_generated_status`
- `check_gate_bite` with the two new canaries

## Outcome

Fill this in before completing the gate.

## Next Agent Bootstrap

The loop is the source of truth for what comes next: `uv run python scripts/loop_stage.py`.
Phase 09 is `active` in `phase_status.yml`, on branch `phase/09-quality-hardening`, and the contract now carries real criteria.
Stage 2 writes the judgment calls; nothing in this phase commits poker data, so `verification/loop_policy.yml` lets it advance unattended once no `frozen-into-data` item is open.
