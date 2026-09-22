# Architecture

The product is an offline-first deterministic bot that plays strong no-limit
hold'em. Today the only way to reach it is the CLI scripts under `scripts/`;
training and coaching surfaces are backlogged until the bot plays well. Runtime
poker decisions are deterministic and cannot rely on LLM reasoning.

## Package Boundaries

- `poker_core`: NLHE state, legality, turn order, positions, and hand outcomes.
  The engine owns whose turn it is: `poker_core.order` derives blind seats and
  first-to-act from the button, tracks next-to-act and the big-blind option,
  applies the under-raise reopening rule, and decides round completion.
  Callers never supply action order. `poker_core.positions` is the only source
  of position names in the repo and derives them from occupied seats, the
  button, and table size.
- `hand_history`: normalized schema and replay. Replay enforces turn order
  fail-closed; a recorded hand whose actions are out of order does not replay.
- `strategy`: deterministic strategy contract and decision audits. A strategy
  answers a `StrategyQuery` with a `StrategyDecision` naming a legal action or
  with an explicit refusal; it never guesses. Every query/outcome pair is
  recordable as deterministic JSONL for audits.
- `solver_artifacts`: committed preflop chart artifacts, strict offline import,
  and fail-closed lookup. One derived spot key is shared by the importer and the
  lookup, so a spot that imports is reachable from game state, and an uncovered
  spot returns an explicit miss code instead of a guessed action. See
  `docs/PREFLOP_ARTIFACT_CONTRACT.md`.
- `simulator`: offline bot-vs-bot simulation and reports.
- `table_state`: pure arithmetic over a table's own chips, shared by reports and
  strategies so neither re-derives a price or a depth. It refuses nothing and
  reads no chart.
- `profiles`: bot profile metadata and comparison labels.
- `data_pipeline`: tiny normalized sample ingestion.

What this repo may not build yet, and what lifts each of those limits, is
stated in `AGENTS.md` under `Boundaries`. The sequencing behind them lives in
`docs/ROADMAP.md` and `backlog.yml`.
