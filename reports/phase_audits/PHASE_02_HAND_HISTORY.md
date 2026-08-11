# Phase 02 Audit Packet: Normalized Hand-History Schema And Deterministic Replay

## Plain-Language Summary

Phase 02 adds a strict normalized hand-history schema and deterministic replay
path for tiny committed fixtures. The replay uses the Phase 01 NLHE core engine:
street betting actions are validated through `BettingRoundState`, and final
showdown settlement is checked against the expected pot, winners, and payouts.

Implemented evidence:

- `src/poker_training_bot/hand_history/schema.py` defines closed schema parsing
  for normalized hand-history records.
- `src/poker_training_bot/hand_history/replay.py` validates betting action
  legality and settles showdown through the Phase 01 engine.
- `data/samples/phase_02_normalized_hands.json` and `.jsonl` provide tiny
  committed fixtures.
- `tests/test_hand_history.py` covers successful replay, JSONL loading,
  expected-result mismatch, over-commit, action-after-fold, duplicate payout
  seats, and unknown fields.
- `scripts/generate_replay_report.py` writes
  `reports/active/latest_replay_report.txt`.

## Non-Coding Reviewer Checklist

| Check | Result | Evidence |
| --- | --- | --- |
| Required Phase 02 tests pass | PASS | `pytest_hand_history` passed |
| Required replay report exists | PASS | `reports/active/latest_replay_report.txt` |
| Full verifier gate passes | PASS | `reports/active/latest_verify.txt` |
| Generated status docs are fresh | PASS | `check_generated_status`, `check_generated_phase_ledger`, `check_generated_backlog` passed |
| Scope stayed inside Phase 02 | PASS | `check_scope` passed |
| Forbidden V1 scope avoided | PASS | No PokerNow automation, browser observation, runtime solver calls, LLM poker decisions, or UI surfaces added |
| Independent read-only review completed | PASS | Review findings recorded below |

## Human Spot-Check Guide

You can review Phase 02 without reading Python source by comparing the committed
sample hands to the generated replay report.

Open these files:

- Input sample: `data/samples/phase_02_normalized_hands.json`
- Generated report: `reports/active/latest_replay_report.txt`
- Full verification summary: `reports/active/latest_verify.txt`

Spot-check 1: heads-up showdown

- In the sample, hand `phase02-heads-up-showdown` has two players.
- Seat 0 posts 5 and calls 5, so seat 0 commits 10 chips.
- Seat 1 posts 10 and checks, so seat 1 commits 10 chips.
- The total pot should therefore be 20.
- The board is `As Ks Qs Js 2d`, and seat 0 has `Ts 9c`.
- Seat 0 makes an ace-high spade straight flush using `Ts As Ks Qs Js`.
- The report should say total pot 20, seat 0 payout 20, seat 1 payout 0,
  and `Expected result matched: True`.

Spot-check 2: three-way side pot

- In the sample, hand `phase02-three-way-side-pot` has three players with
  starting stacks of 50, 100, and 200.
- Seat 2 raises to 200. Seat 0 can call only 45 more after posting 5, and
  seat 1 can call only 90 more after posting 10.
- The committed chips should be seat 0: 50, seat 1: 100, seat 2: 200.
- The total pot should therefore be 350.
- The side pots should split into 150, 100, and 100.
- The report should show seat 0 winning the main pot with a flush, seat 1
  winning the first side pot with three of a kind, and seat 2 winning the
  final side pot with a pair.
- The report should say payouts are seat 0: 150, seat 1: 100, seat 2: 100,
  and `Expected result matched: True`.

What this does prove:

- The project can read the normalized hand-history format.
- The project can replay the committed examples deterministically.
- The replay output agrees with the expected pot and payout results.
- The Phase 02 gate caught and fixed review issues for illegal action order and
  unknown fields before the phase was closed.

What this does not prove yet:

- It does not prove raw PokerNow import.
- It does not prove large hand-history ingestion.
- It does not prove real strategy quality.
- It does not prove UI behavior or live-play automation.

Reviewer verdict guidance:

- Accept Phase 02 if the sample inputs and generated report match the checks
  above, and `reports/active/latest_verify.txt` says `All passed: True`.
- Reject or question Phase 02 if the report is missing, stale, says expected
  results did not match, or claims work outside the Phase 02 scope.

## Human Review Sign-Off

Reviewer: Taylor

Review date: 2026-06-10

Verdict: SIGNED OFF

Basis:

- Reviewed the Phase 02 human spot-check packet.
- Accepted the phase as on track for the current offline deterministic training
  bot plan.
- Requested future phase packets remain concretely human-verifiable without
  requiring source-code review.

## Command Summary

Full gate command:

```powershell
.\.venv\Scripts\python.exe scripts\run_verify.py
```

Passing command IDs recorded in `reports/active/latest_verify.txt`:

- `generate_status`
- `generate_phase_ledger`
- `generate_backlog`
- `generate_replay_report`
- `check_generated_status`
- `check_generated_phase_ledger`
- `check_generated_backlog`
- `check_contracts`
- `check_scope`
- `check_file_sizes`
- `import_smoke`
- `uv_import_smoke`
- `pytest_poker_core`
- `pytest_hand_history`
- `pytest`
- `ruff_check`

Required Phase 02 report:

- `reports/active/latest_replay_report.txt`

## Independent Read-Only Review

Reviewer: subagent `019eaab3-84b4-7bd3-b155-8bb864ed99bf`.

Initial findings:

- HIGH: Replay was settlement-only and did not reject impossible action
  sequences such as a folded player calling later.
- HIGH: This audit packet did not exist yet.
- MEDIUM: The schema parser accepted unknown fields.

Fixes before closeout:

- Betting actions now replay through `BettingRoundState.apply`.
- `tests/test_hand_history.py` includes an action-after-fold regression.
- Schema parsing now rejects unknown fields via closed key validation.
- `tests/test_hand_history.py` includes an unknown-field regression.
- This audit packet records pass/fail evidence and review results.

Read-only recheck verdict:

- No remaining implementation or verifier findings.
- Action-after-fold was rejected with `ValueError: call is not legal for seat 0`.
- Top-level and nested unknown fields were rejected.
- Saved full-gate report showed all commands passing.

## Known Limitations

- Phase 02 supports normalized schema version `1` only.
- Replay requires a complete five-card showdown board.
- The committed sample set is intentionally tiny and offline.
- No raw or processed hand-history ingestion is added in this phase.

## Deferred Items

No Phase 02 contract work is deferred. Existing V2 deferrals remain in
`backlog.yml`.

## Gate Verdict

PASS. Phase 02 satisfies the contract after the independent review fixes and
full verifier gate.

## Addendum (2026-08-10): Uncontested Hands And Replay Hardening

Plain-language summary: hands that end when all but one player folds can now
be recorded and replayed. Previously only hands reaching a five-card showdown
were representable, which excluded the most common way real poker hands end.

What changed:

- A hand with exactly one non-folded player settles uncontested: that player
  wins the whole pot (including any uncalled final bet), no hand ranking is
  evaluated, `showdown` must be empty, and no streets may follow the deciding
  street (`settle_uncontested` in `src/poker_training_bot/poker_core/engine.py`,
  uncontested path in `src/poker_training_bot/hand_history/replay.py`).
- Streets must now run preflop, flop, turn, river without gaps, and each street
  must deal its exact board-card count (`schema.py`).
- A player may post a blind for their whole remaining stack when it is below
  the big blind (short-stack all-in blind).
- The Phase 01 golden-hand report now writes
  `reports/active/latest_golden_hand_report.txt`; it previously shared
  `reports/active/latest_replay_report.txt` with the Phase 02 report, which
  overwrote it on every gate run. Contract text cleanup is deferred as backlog
  item `CONTRACT-REPORT-PATHS`.

Spot-check for a non-coding reviewer: in
`data/samples/phase_02_normalized_hands.json`, hand `phase02-preflop-fold-out`
posts blinds of 5 and 10, then both other players fold. The report
`reports/active/latest_replay_report.txt` should show total pot 15, payout 15
to seat 1 with zero to the others, the pot marked "uncontested", and
`Expected result matched: True`.

Verification: full Phase 02 gate passed on 2026-08-10 (see
`reports/active/latest_verify.txt`); 31 tests pass including seven new
fold-out, street-shape, and short-blind tests.

Independent review: a read-only review subagent audited the addendum diff and
confirmed three real bugs, all fixed before commit:

1. A blind post equal to the player's stack was accepted even when the stack
   covered the owed blind. Fixed by deriving blind seats from `button_seat`
   and requiring each post to match the owed blind or be a genuine short
   all-in below it.
2. A short all-in blind lowered `current_bet`, letting later players call or
   min-raise below the legal price. Fixed by anchoring `current_bet` to the
   owed blind rather than the posted amount.
3. Actions recorded after the deciding fold within the same street were still
   replayed. Fixed by failing on any action after the hand is decided.

The review also prompted defense-in-depth hardening: preflop must open with
both blind posts by the correct seats, `post_blind` is rejected anywhere else,
`settle_uncontested` asserts the winner is the largest committer, and
`starting_stack` must be positive. Two regression tests pin the blind-pricing
and post-fold-action exploits. Remaining review notes were accepted as
documented limitations: the uncontested pot is reported as a single pot
including any uncalled bet, and stale contract report paths stay deferred as
backlog item `CONTRACT-REPORT-PATHS`.
