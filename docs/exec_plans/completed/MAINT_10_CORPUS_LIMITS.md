# MAINT-10: Write Down What The Corpus Comparison Cannot Establish

## Objective

The independent reviewer's one unfixed point: nothing in this repo can check the committed corpus text against the dataset it says it came from.
The checksum proves the file has not changed since it was committed, not that it is what the publisher published, and the gate has no network by design.
Every number in Phase 08 is downstream of that, and it was not in the packet's limitations.

Several other standing limits were also spread across three audit files, so a reader had to reconstruct the list.
This task collects them into one short document and points the packet and the source card at it.

## Scope

Approved:

- `docs/CORPUS_COMPARISON_LIMITS.md`
- `docs/SAMPLE_CORPUS_SOURCE.md`
- `reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md`

Forbidden here: any code, test, or data change.
Nothing measured is wrong; what was missing is the statement of what the measurement does not reach.

## Delegation Plan

- No-delegation exception: a documentation task with no implementation lanes, and the review that produced it has already happened.

## Slices

- [x] Slice 1: `docs/CORPUS_COMPARISON_LIMITS.md`, leading with the provenance limit and the one check a reader can actually run - clone the dataset, re-run the builder, diff, which the deterministic selection rule makes byte for byte.
- [x] Slice 2: the packet's limitations section leads with the same two items and points at the full list.
- [x] Slice 3: the source card points at it too, since a reader who wants provenance is the reader who needs the limit.

## Verification

- `uv run python scripts/run_verify.py` (full derived gate)

## Outcome

Full gate green. No code, test, data, or measurement changed.

## Next Agent Bootstrap

The repo is at `task_mode: idle` with Phase 08 completed and Phase 09 still `future`.
Two findings from the earlier reviews remain deliberately undone and unfiled: the report lists only the first 20 of 164 disagreements with no committed file holding the rest, and `convert.py` builds `showdown_seats` from the corpus's show records and then discards it, so a normalized hand's `showdown` means "did not fold" rather than "showed".
