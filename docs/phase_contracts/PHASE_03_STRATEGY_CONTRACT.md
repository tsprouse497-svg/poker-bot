---
phase_id: "03"
title: "Strategy Contract And Deterministic Decision Audit Shape"
depends_on:
  - "02"
required_gate_commands:
  - pytest_strategy_contract
  - generate_strategy_query_report
required_reports:
  - reports/active/latest_strategy_query_report.txt
  - reports/active/latest_decision_audit.jsonl
required_phase_audit: reports/phase_audits/PHASE_03_STRATEGY_CONTRACT.md
---

# Phase 03: Strategy Contract And Deterministic Decision Audit Shape

## Scope
Phase 03 delivers the deterministic strategy query/decision contract, the
decision audit record shape, and the turn-order layer those require. It is
limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not add chart-based or postflop playing strategies; those are Phases
  04 through 06. The reference strategy here exists only to exercise the
  contract.

## Acceptance criteria
- The poker core gains a turn-order layer: button-derived blind seats,
  first-to-act per street, next-to-act tracking with folded and all-in seats
  skipped, the big-blind option, betting-round completion, and a reopening
  rule where an all-in raise below the minimum does not reopen raising for
  seats that already acted (they may still call or fold).
- Hand-history replay enforces turn order fail-closed: every recorded action
  must come from the seat to act, and a street with live action cannot end
  with its betting round open. Committed fixtures are corrected where rounds
  previously ended without explicit checks.
- The strategy package defines the versioned contract: `StrategyQuery`
  captures the full decision context (seat to act, hole cards, board, street,
  legal actions, price to call, minimum raise target, pot, stacks, blinds,
  button); `StrategyDecision` must name a legal action; a first-class refusal
  outcome lets a strategy decline rather than guess.
- `StrategyQuery` carries the preflop action history as an ordered sequence of
  seat and action pairs, because price to call and stack sizes cannot tell a
  strategy who raised. Without it an artifact-backed strategy cannot name the
  spot it is in, and reconstructing the sequence from committed amounts would be
  the heuristic guessing this repo forbids. The field is seat-based, not
  position-based: positions are derived from the button, and the query stays the
  raw decision context. It records folds as well as voluntary actions, so it is
  game state rather than an already-canonicalized chart key. It defaults to empty
  so existing callers are unaffected, and an empty history means the action folded
  to hero.
- A refusal names what was missing, not only that something was.
  `StrategyRefusal` carries a code and, alongside it, structured detail: an
  ordered sequence of name and value pairs describing the thing the strategy
  could not find. The code stays a stable, groupable vocabulary so refusals can
  be counted by kind; the detail carries the specifics so they can be acted on.
  A chart miss therefore reports the spot key and the hand class it looked for,
  which is enough to name a chart cell somebody can fill.
  Detail defaults to empty, so a refusal with nothing useful to add stays as
  simple as it was, and existing callers are unaffected.
  This exists because a count of refusals is not a work list. A phase that
  measures coverage can only report which kinds of spot are missing, and closing
  a gap needs to know which spots.
- Refusal detail is ordered and serialized with the record, so two runs producing
  the same refusal produce the same bytes, and a reader of the committed audit can
  recover the specifics without rerunning anything.
- Decision audit records serialize query, outcome, and strategy identity to
  deterministic JSONL: identical inputs produce identical bytes.
- A deterministic reference strategy (check when free, otherwise fold)
  exercises the contract end to end over the committed normalized hands.
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_strategy_query_report.txt`
- `reports/active/latest_decision_audit.jsonl`

## Required command IDs
- `pytest_strategy_contract`
- `generate_strategy_query_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
