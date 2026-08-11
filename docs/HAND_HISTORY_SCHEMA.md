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
- Streets must run `preflop`, `flop`, `turn`, `river` in order without gaps.
  A hand that ends early simply stops after its last dealt street.
- Each street must deal its exact board-card count: zero preflop, three on the
  flop, one on the turn, and one on the river.
- Committing actions are `post_blind`, `call`, `bet`, and `raise`; each requires
  a positive `amount`.
- `post_blind`, `call`, and `bet` amounts are added chips for that action.
- Blind seats are derived from `button_seat`: the small blind is the next
  occupied seat after the button (the button itself heads-up) and the big
  blind follows it. The first two preflop actions must be the small-blind and
  big-blind posts by exactly those seats, and `post_blind` may appear nowhere
  else.
- A `post_blind` amount must match the blind that seat owes, unless the player
  posts their entire remaining stack all-in below the owed blind. A short
  all-in blind does not lower the price to call or the minimum raise, which
  stay anchored to the configured blinds.
- `raise` amount is the target total street bet, matching the Phase 01 engine.
- Non-committing actions are `check` and `fold`; these must not include an
  `amount`.
- Betting actions are replayed through the Phase 01 betting state and illegal
  actions fail closed.
- A hand where all but one player folds settles uncontested: the remaining
  player wins the whole pot, including any uncalled final bet, `showdown` must
  be empty, and no further actions or streets may follow the deciding fold.
- Every player must have a positive `starting_stack`; sitting-out or busted
  seats are omitted from `players`.
- Showdown replay requires exactly five accumulated board cards, and every
  active, non-folded player must have exactly two showdown hole cards.
- Duplicate board or hole cards fail validation.
- Replayed committed chips must match `result.pot`.
- Core settlement payouts must match `result.payouts` exactly.

Committed Phase 02 examples live in
`data/samples/phase_02_normalized_hands.json` and
`data/samples/phase_02_normalized_hands.jsonl`.
