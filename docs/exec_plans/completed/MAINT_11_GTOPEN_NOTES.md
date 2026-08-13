# MAINT-11: Record What Was Verified About GTOpen

## Objective

The preflop coverage gap needs a solver this repo can re-run and describe.
GTOpen was cloned, built and exercised on 2026-08-13, and what that established should not live in a chat log.

## Scope

Approved: `docs/GTOPEN_SOLVER_NOTES.md`.

Forbidden: anything else.
No code, no artifact, no contract. GTOpen is a candidate, not an adopted dependency, and nothing here commits this repo to it.

## Delegation Plan

- No-delegation exception: a single documentation file recording work already performed in this session; there is nothing to delegate.

## Slices

- [x] Slice 1: the note, with everything executed separated from everything only read, and the not-verified list written as instructions rather than as caveats.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

Full gate green. Documentation only; no code, test, data, or measurement changed.

## Next Agent Bootstrap

The repo is idle with all ten phases complete.
`docs/GTOPEN_SOLVER_NOTES.md` is the starting point for the preflop coverage work, and its "Not verified" section is the work list: measure a real solve's time, then check determinism, then compare a converged solve against the 36 committed spots before anything becomes a phase.
