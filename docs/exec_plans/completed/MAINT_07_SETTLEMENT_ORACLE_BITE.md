# MAINT-07: Make The Corpus Settlement Oracle Bite

## Objective

Phase 08's central claim is that this repo's engine settles 499 real hands to a publisher's own finishing stacks.
A post-hoc review found that the test carrying that claim cannot fail on it.

`_settled_stacks` in `tests/test_sample_comparison.py` rebuilds each seat's final stack as
`starting - replay.committed_by_seat + normalized.result.payouts`.
It never reads `replay.settlement`.
And `result.payouts` was itself derived in `convert.py` as `finishing - starting + committed`, straight from the corpus.
The expression therefore collapses back to the corpus's published finishing stacks no matter what the engine computed.

The property does hold, but it is enforced somewhere else: `replay_hand` raises when `passed_expected_result` is false.
That guard lives in Phase 02 code, and no mutation in `verification/mutations.yml` targets it, so `check_gate_bite`
has never proved it fires.

Demonstrated before this task was opened, as a read-only monkeypatched run against the committed sample: with
`passed_expected_result` forced true and both settlement functions rewired to pay every pot to seat 0, the phase's
central test still reports 0 mismatches across all 499 hands.

This task makes the assertion depend on the engine's own output, adds the test that proves the guard fires, and adds the
canaries that make both bite.

## Scope

Approved:

- `tests/test_sample_comparison.py`
- `verification/mutations.yml`
- `verification/freeze.lock`

Forbidden here:

- Any `src/**` change.
  Nothing in the implementation is wrong; the defect is entirely in what the gate proves about it.
- The Phase 08 contract, decision record, and audit packet.
  This is `maintenance` mode, and the phase's claims stay exactly as written; what changes is that they become provable.

## Delegation Plan

- No-delegation exception: subagent delegation is disabled in this operator's sessions, which is the same constraint
  recorded in the Phase 08 audit packet, so implementation and review are both coordinator-owned. The compensating
  control is that the defect being fixed was itself found by a review pass that ignored the contract, and that the fix
  is verified by mutation rather than by assertion alone.

## Slices

- [x] Slice 1: `_settled_stacks` reads `replay.settlement.payouts` instead of `normalized.result.payouts`.
      Evidence: the assertion now compares engine output against publisher output with no converter-derived term on
      either side.
- [x] Slice 2: a test that a misallocated settlement is refused rather than accepted, built from a committed chopped
      pot (`pluribus/41/18`, 2550/2550 of a 5100 pot) with one chip moved between its two winners.
      Winner set and pot are unchanged, so only the payout comparison can catch it.
      Evidence: `replay_hand` raises `does not match expected result`.
- [x] Slice 3: two canaries against `src/poker_training_bot/hand_history/replay.py`, the first mutations in the repo
      to target the replayer at all.
      Evidence: both must fail `pytest_sample_comparison` and `pytest_hand_history`.
- [x] Slice 4: re-freeze the tests and commit the lock diff as the record of what changed.

## What no single mutation can prove

Slice 1 is a structural hardening rather than a behavior change, and there is no mutation that isolates it.
A wrong engine settlement is caught by the Phase 02 guard whether or not the test reads `replay.settlement`, and a
disabled guard changes nothing while the engine is right.
Only both defects together produce the silent pass, and a canary applies one defect at a time.

So the honest statement of what this task buys is: slice 3 proves the guard fires, and slice 1 removes the phase's
dependence on it, which means the two defects no longer have to be found together to be found at all.

## Verification

- `uv run python scripts/run_verify.py` (full derived gate)
- `pytest_sample_comparison`, `pytest_hand_history` via `check_gate_bite`

## Outcome

Full gate green across 33 commands.
22 mutations applied and all 22 caught, up from 20.
`test_every_committed_hand_settles_to_the_corpus_oracle` now fails when the replayer's settlement guard is disabled;
before this task it passed with the engine paying every pot to the wrong seat.

## Next Agent Bootstrap

The repo is at `task_mode: idle` with Phase 08 completed and Phase 09 still `future`.
Phase 09 (`Quality, Drift, Backlog, And Phase-Gate Hardening`) is the natural home for the rest of the review that
produced this task: the agreement split by position, the pooling of Pluribus with the humans in
`agreement_by_observed_action`, the text-scraped self-play cross-reference in `_self_play_spots`, the inert sidecar,
and the all-in count that three committed documents state as 7 when the sample holds 24.
None of those is filed in `backlog.yml` yet.
Start there, or activate Phase 09 with `scripts/loop_stage.py`.
