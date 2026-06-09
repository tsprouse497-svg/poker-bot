# Hand History Schema

Phase 02 implements the normalized hand-history shape and deterministic replay.

Supported committed formats:

- `.json` for single-hand golden fixtures.
- `.jsonl` for multi-hand sample datasets.

Each hand record must include:

- `schema_version`
- `hand_id`
- `table`
- `players`
- `button_seat`
- `blinds`
- `streets`
- `showdown`
- `result`

## Replay Rules

- `schema_version` must be `1`.
- Unknown fields are rejected at every object level.
- `table.max_seats` must be from 2 through 9.
- Player seats are zero-based stable seat IDs and must be less than
  `table.max_seats`.
- Streets must be ordered `preflop`, `flop`, `turn`, `river`.
- Board cards are accumulated from street `board` fields and showdown replay
  requires exactly five board cards.
- Committing actions are `post_blind`, `call`, `bet`, and `raise`; each requires
  a positive `amount`.
- `post_blind`, `call`, and `bet` amounts are added chips for that action.
- `raise` amount is the target total street bet, matching the Phase 01 engine.
- Non-committing actions are `check` and `fold`; these must not include an
  `amount`.
- Betting actions are replayed through the Phase 01 betting state and illegal
  actions fail closed.
- Every active, non-folded player must have exactly two showdown hole cards.
- Duplicate board or hole cards fail validation.
- Replayed committed chips must match `result.pot`.
- Core settlement payouts must match `result.payouts` exactly.

Committed Phase 02 examples live in
`data/samples/phase_02_normalized_hands.json` and
`data/samples/phase_02_normalized_hands.jsonl`.
