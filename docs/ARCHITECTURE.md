# Architecture

The v1 product is a CLI and report-driven offline training system. Runtime
poker decisions are deterministic and cannot rely on LLM reasoning.

## Package Boundaries

- `poker_core`: NLHE state, legality, and hand outcomes.
- `hand_history`: normalized schema and replay.
- `strategy`: deterministic strategy contract and decision audits.
- `solver_artifacts`: offline preflop chart artifacts and import checks.
- `simulator`: offline bot-vs-bot simulation and reports.
- `profiles`: bot profile metadata and comparison labels.
- `data_pipeline`: tiny normalized sample ingestion.

Deferred platform automation and UI work belongs in `docs/ROADMAP.md` and
`backlog.yml`.
