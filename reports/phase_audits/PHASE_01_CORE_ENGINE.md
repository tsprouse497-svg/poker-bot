# Phase 01 Core Engine Audit Packet

## Summary

Phase 01 added a deterministic offline NLHE core engine for two to nine players.
The implementation covers card parsing and uniqueness checks, five-to-seven-card
hand evaluation, betting-round legality validation, showdown ranking, side-pot
settlement, synthetic golden hands, and the required replay report.

No PokerNow automation, browser/platform observation, UI, runtime solver calls,
strategy logic, preflop charts, or broad hand-history ingestion was added.

## Plain-Language Checklist

- Pass: The engine rejects duplicate cards and invalid player counts.
- Pass: The evaluator ranks major made hands and ace-low straights.
- Pass: Betting legality rejects checking while facing a bet and undersized
  raises that are not all-in.
- Pass: Showdown settlement handles two-player, nine-player side-pot, and split
  pot synthetic hands.
- Pass: The required replay report is generated at
  `reports/active/latest_replay_report.txt`.
- Pass: Required Phase 01 command IDs pass through `scripts/run_verify.py`.
- Pass: Generated status docs are current.
- Pass: Scope, file-size, import, full test, and ruff checks pass.

## Command Evidence

Latest generated command results are committed at:

- `reports/active/verify_results.json`
- `reports/active/latest_verify.txt`
- `reports/active/latest_replay_report.txt`

The final full verifier command was:

```powershell
python scripts/run_verify.py
```

Required Phase 01 commands in that verifier run:

- `pytest_poker_core`: pass
- `generate_phase_01_replay_report`: pass

## Human Replay Evidence

The committed replay report covers:

- Heads-up royal flush versus full house.
- Nine-player all-in settlement with main and side pots.
- Three-player split pot on a board straight.

## Review

Independent read-only subagent review completed after initial Phase 01 closeout.

- Finding: The heads-up golden hand was described as royal flush over full house
  but originally produced royal flush over three of a kind.
- Resolution: Updated the synthetic board so the losing hand is aces full of
  kings while seat 0 still has the royal flush.
- Finding: The audit packet originally recorded self-review because the
  independent reviewer had not been spawned.
- Resolution: Replaced that fallback with this independent review summary.
- No forbidden scope, PokerNow automation, browser/platform observation,
  runtime solver call, LLM-backed decision, UI, strategy implementation,
  preflop chart behavior, or broad hand-history ingestion was found.
- Residual risk: Betting-round primitives validate individual actions but do
  not model full turn order or complete hand-history replay; that remains
  outside Phase 01 and belongs to later phases.

## Known Limitations

- Phase 01 does not implement strategy decisions, preflop charts, solver calls,
  UI, browser automation, or platform observation.
- Golden hands are synthetic core-engine evidence, not a hand-history ingestion
  feature.
- Betting-round state validates individual actions but does not yet provide a
  full hand-history replay schema; that belongs to Phase 02.
