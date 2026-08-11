# Architecture

The v1 product is a CLI and report-driven offline training system. Runtime
poker decisions are deterministic and cannot rely on LLM reasoning.

## Package Boundaries

- `poker_core`: NLHE state, legality, turn order, and hand outcomes. The
  engine owns whose turn it is: `poker_core.order` derives blind seats and
  first-to-act from the button, tracks next-to-act and the big-blind option,
  applies the under-raise reopening rule, and decides round completion.
  Callers never supply action order.
- `hand_history`: normalized schema and replay. Replay enforces turn order
  fail-closed; a recorded hand whose actions are out of order does not replay.
- `strategy`: deterministic strategy contract and decision audits. A strategy
  answers a `StrategyQuery` with a `StrategyDecision` naming a legal action or
  with an explicit refusal; it never guesses. Every query/outcome pair is
  recordable as deterministic JSONL for audits.
- `solver_artifacts`: offline preflop chart artifacts and import checks.
- `simulator`: offline bot-vs-bot simulation and reports.
- `profiles`: bot profile metadata and comparison labels.
- `data_pipeline`: tiny normalized sample ingestion.

Deferred platform automation and UI work belongs in `docs/ROADMAP.md` and
`backlog.yml`.
