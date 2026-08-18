# MAINT-19: Adopt The V2 Phase Sequence

## Objective

`docs/V2_ROADMAP.md` has proposed seven phases since 2026-08-15, all eight of its rulings are made, and its consequences are planned in `docs/V2_RULING_MITIGATIONS.md`.
Nothing in the machinery knows any of that: `phase_status.yml` stops at 09, no contract skeleton exists above it, and `verification/loop_policy.yml` has no entry for a phase the loop could be asked to start.

This task adopts the proposal.
It declares nothing about what those phases must achieve, because acceptance criteria are `contract-update` work that belongs to each phase's own stage 1.

## Scope

Approved: `docs/ROADMAP.md`, the seven new contract skeletons, `verification/loop_policy.yml`, `scripts/check_contracts.py`, `tests/test_loop_machinery.py`, `verification/freeze.lock`.
`phase_status.yml` and `backlog.yml` are standing scope.

Forbidden: `AGENTS.md`, the v1 contracts, and everything under `src/`.
No phase is activated and no acceptance criterion is written.

## Delegation Plan

- No-delegation exception: subagent delegation is disabled in this operator's sessions. The work is a mechanical transcription of a document the operator already ruled on, with one checker change. Self-review at the end, recorded in the outcome.

## Slices

- [x] Slice 1: seven contract skeletons, each carrying boilerplate criteria, placeholder command IDs, and a scope paragraph that says it is a skeleton and points at the proposal.
- [x] Slice 2: seven `phase_status.yml` entries at `future`.
- [x] Slice 3: seven `verification/loop_policy.yml` entries, each deciding auto-advance by the existing rule and saying why.
- [x] Slice 4: `backlog.yml` re-tagged, so every deferred item names the phase that will close it or says why none will.
- [x] Slice 5: `scripts/check_contracts.py`, which hardcoded ten contracts and the ID set `00`-`09`, derived from `phase_status.yml` instead.
- [x] Slice 6: tests for the derived checks, and the re-freeze.
- [x] Slice 7: `docs/ROADMAP.md`.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

Seven slices, gate green, 32 mutations all caught.

Phases 10 through 16 are declared at `future` with contract skeletons, audit packet paths, and loop-policy entries.
Four of the seven stop for a human by the existing rule and three of those commit data: phase 10 the solver export, 12 the re-derived artifact, 14 the chart the bot plays, 15 session records.
Phase 16 is the one marked `needs_human_data`, because there is no postflop solution in the tree and a session must not invent a sizing scheme.
Phases 11 and 13 may auto-advance, since both write no committed data and both have exhaustive oracles.

Twenty backlog items now name the phase that will close them, taken from the roadmap sections that already named each one.
Nine stay deferred, and four of those had their reasons rewritten rather than left stale: PokerNow and the training UI because rulings 7 and 6 keep them out of v2 entirely, large-dataset ingestion because ruling 5's lift has no bound written and no phase owns it, and stack-depth bucketing because more solved depths narrow it without making bucketing anything other than a heuristic.

`scripts/check_contracts.py` carried two hardcoded facts that adoption would have broken: exactly ten contracts, and the ID set `00` through `09`. Both now derive from `phase_status.yml`. The comparison is extracted as `contract_id_errors` so it can be tested and canaried; without that, replacing a hardcoded assertion with a function that reports nothing would look identical from the gate.

Self-review found two things, both fixed.
`check_contracts.py` was the only checker without the `repo_paths` import fallback, which never showed until a test imported it directly rather than through `loop_stage`.
The skeletons claimed `check_contracts.py` refuses to let a phase go active, which it does not: it fails the gate for an active phase whose criteria say only what a generic phase would.

One process note worth recording. Running `check_gate_bite` in the background and then starting a full gate run collided: two mutation runs raced, and the loser left `verification/.mutation_in_progress` beside a mutated `replay.py` in the tree. That is `MUTATION-SENTINEL-IS-COMMITTABLE` happening for the second time in this repo's history, it cost a manual restore, and it is the argument for landing that fix before phase 10 rather than after.

## Next Agent Bootstrap

Phases 10 through 16 are declared at `future` with skeleton contracts and loop-policy entries.
Declared is not specified: every one of those contracts still carries boilerplate criteria, and stage 1 of the loop is where that changes.

Two things are owed before phase 10 can start.
`AGENTS.md` still forbids the ingestion ruling 5 lifts, and the lift needs a bound expressed as a number, which is a `contract-update` waiting on Taylor.
`MUTATION-SENTINEL-IS-COMMITTABLE` should land as its own maintenance task rather than inside a phase.

Phase 10 itself has two unverified inputs that belong to its contract stage: the solver's determinism has never been checked by running one config twice and diffing, and no solve time was ever recorded.
