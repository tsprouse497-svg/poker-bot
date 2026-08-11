# Phase 03 Audit Packet: Strategy Contract And Deterministic Decision Audit Shape

## Plain-Language Summary

Phase 03 answers two questions the later strategy phases depend on: whose turn
is it, and what exactly does a strategy get asked and answer.

The poker core now owns turn order. `poker_core/order.py` derives the blind
seats from the button, knows who acts first on every street, tracks whose turn
it is while skipping folded and all-in seats, honors the big blind's preflop
option, applies the under-raise rule (an all-in raise below the minimum does
not let players who already acted raise again), and decides when a betting
round is complete. Hand-history replay now enforces all of that fail-closed:
a recorded hand whose actions are out of order, or whose street ends with an
open betting round, does not replay.

The strategy package defines the contract every future strategy must satisfy:
a `StrategyQuery` carries the full decision context (seat to act, cards,
legal actions, prices, pot, stacks, blinds); the strategy answers with a
`StrategyDecision` naming a legal action or with an explicit refusal instead
of a guess. Every query/answer pair serializes to deterministic JSONL for
audits: identical inputs produce identical bytes. A deliberately dumb
reference strategy (check when free, otherwise fold) exercises the whole path
end to end over the committed sample hands.

## Non-Coding Reviewer Checklist

| Check | Result | Evidence |
| --- | --- | --- |
| Required Phase 03 tests pass | PASS | `pytest_strategy_contract` (56 tests across turn order and contract) |
| Strategy query report exists | PASS | `reports/active/latest_strategy_query_report.txt` |
| Decision audit JSONL exists | PASS | `reports/active/latest_decision_audit.jsonl` |
| Reports are deterministic | PASS | Generator run twice produced byte-identical outputs (matching checksums) |
| Full derived gate passes | PASS | `reports/active/latest_verify.txt` (20 commands) |
| Scope stayed inside the Phase 03 list | PASS | `check_scope` against base commit `c15d845` |
| Forbidden V1 scope avoided | PASS | No solver calls, no LLM decisions, no chart strategies, no UI |
| Delegation performed | PASS | Two worker subagent lanes (turn order; strategy contract) recorded in the ExecPlan |
| Independent read-only review completed | PASS | Findings recorded below |

## Human Spot-Check Guide

Open `reports/active/latest_strategy_query_report.txt` next to
`data/samples/normalized_hands.json`.

- Hand `phase02-heads-up-showdown` records eight decisions after the blinds
  (one call, seven checks). The report should show 8 decision points, 8
  queried, and 7 agreements: the reference strategy checks everywhere a check
  was recorded and disagrees only with the opening call (it would fold).
- Hand `phase02-three-way-side-pot` records a raise and two calls. The report
  should show 3 queried and 0 agreements: the reference strategy folds facing
  chips rather than calling or raising.
- The fold-out hands record decisions but no revealed hole cards, so the
  report should show their points as "skipped (no recorded hole cards)" - the
  contract refuses to fabricate unknown cards.
- In `reports/active/latest_decision_audit.jsonl`, every line is one decision:
  find `"hand_id":"phase02-three-way-side-pot"` lines and check each
  `"outcome"` is a fold decision with code `reference:fold-facing-bet`.

## Command Evidence

- `pytest_strategy_contract`: pass (tests/test_strategy_contract.py,
  tests/test_action_order.py)
- `generate_strategy_query_report`: pass, writes both required reports
- Full derived gate: `reports/active/latest_verify.txt`,
  `reports/active/verify_results.json`

## Known Limitations

- The reference strategy is a contract exerciser, not a playing strategy;
  chart-driven play arrives in Phases 04 and 05.
- Strategy queries require known hole cards, so decision points from seats
  that never showed down are counted and skipped, not queried.
- Turn order assumes both blinds are always posted; missed-blind and
  dead-blind states are out of V1 scope.

## Deferred Items

No new deferrals. Existing V2 items remain in `backlog.yml`.

## Independent Review

A read-only review subagent executed the full Phase 03 diff adversarially and
verified two real bugs plus hardening items, all addressed before the gate
commit:

1. Real: a second under-raise all-in overwrote the barred-seat set, silently
   letting an earlier barred seat re-raise. Fixed by accumulating the set
   (`no_raise | acted`); the stricter rule that consecutive short all-ins
   never reopen raising is deferred as backlog item `UNDER-RAISE-ACCUMULATION`.
2. Real (pre-existing since Phase 01): the engine never updated the minimum
   raise after a postflop bet, so a bet of 200 could be "raised" to 210.
   Fixed in `engine.py` (a full bet sets the minimum raise to the bet size);
   scope widening recorded in `CURRENT_TASK.yml`.
3. Hardening from the same review: betting or raising with no live opponent
   is now rejected; `TurnState.legal_actions` exposes the turn-aware action
   set so consumers cannot re-derive it inconsistently; decision audit records
   now validate bet/raise sizing against the minimum raise target and the
   seat's all-in maximum (new `street_bet` query field); replay-level
   enforcement gained direct regression tests (out-of-turn, open round,
   action on an all-in runout); query `to_call` is capped by the acting
   seat's stack.
4. Accepted as documented conventions: a short all-in blind keeps the call
   price at the full blind level (documented in `docs/HAND_HISTORY_SCHEMA.md`),
   and folds while checking is free remain rejected (backlog item
   `FOLD-WHEN-FREE`).

The reviewer verified determinism across hash seeds and confirmed first-to-act
rules, the big-blind option, all-in skipping, and the fixture corrections as
sound.

## Gate Verdict

PASS. Phase 03 satisfies the contract: full derived gate green (20 commands,
110 tests) after independent review fixes, with reports fresh and
deterministic.
