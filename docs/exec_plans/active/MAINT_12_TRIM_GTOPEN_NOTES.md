# MAINT-12: Trim The GTOpen Note To The Tool

## Objective

The note argued this repo's case as well as describing the solver: coverage numbers, the provenance argument, and how a re-sourced chart should be assembled.
All of that already lives in the repo's own documents, and repeating it here dates the note the moment those numbers move.

## Scope

Approved: `docs/GTOPEN_SOLVER_NOTES.md`. Nothing else.

## Delegation Plan

- No-delegation exception: a single documentation edit; there is nothing to delegate.

## Slices

- [x] Slice 1: cut the coverage framing, the provenance argument, the Phase 08 rake explanation, and the closing advice about replacing rather than extending a chart. Keep installed state, config surface, extraction path, payload format, and the not-verified list.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

Full gate green. The note is 40% shorter and every remaining line is about GTOpen.

## Next Agent Bootstrap

The repo is idle with all ten phases complete.
`docs/GTOPEN_SOLVER_NOTES.md` describes the solver; the repo's own case for needing one is in `docs/CORPUS_COMPARISON_LIMITS.md` and `backlog.yml`.
