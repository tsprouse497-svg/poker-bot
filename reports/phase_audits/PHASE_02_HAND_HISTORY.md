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
