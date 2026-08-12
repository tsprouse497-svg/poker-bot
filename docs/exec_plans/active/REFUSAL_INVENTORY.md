# ExecPlan: Refusal inventory, and teaching a refusal to name what it missed

## Objective

Turn Phase 07's refusal count into a work list.

The committed charts have no answer for 21.3% of self-play hands. That number exists;
the list behind it does not. Two things are in the way, and they are separate problems
that look like one.

A refusal names the *kind* of miss and not the spot. `preflop-chart:lookup:spot-not-covered`
tells a reader that a chart was silent and nothing about where. So the only surviving trace
of which spot was refused was the preflop action sequence that led to it.

And a refused hand's record discards that sequence. `simulator.run._voided` builds its
record from the streets already filed, and a street is only filed once its betting round
completes; a refusal returns from inside the round, so nothing is filed. Measured over the
committed run: 128 refused hands, between two and seven decisions each, 565 actions, none
of them kept.

Done when `reports/active/latest_refusal_inventory.txt` lists every distinct spot the
strategies could not answer, ordered by how many hands reached it, and the full gate is
green with `check_gate_bite` catching a canary aimed at each half of the fix.

## Scope

Approved for the contract stage:

- `docs/phase_contracts/PHASE_03_STRATEGY_CONTRACT.md`
- `docs/phase_contracts/PHASE_07_SIMULATOR_REPORTS.md`

Approved for the implementation stage:

- `src/poker_training_bot/strategy/contract.py` - refusal detail
- `src/poker_training_bot/strategy/preflop_chart.py` - populate it on a chart miss
- `src/poker_training_bot/simulator/**` - keep the pre-refusal actions, stop claiming a
  refused hand is a completed history
- `scripts/generate_profile_comparison_report.py` - write the inventory
- `tests/test_strategy_contract.py`, `tests/test_simulator.py`
- `verification/mutations.yml`, `verification/freeze.lock`

Read-only: `poker_core/**`, `hand_history/**`, `solver_artifacts/**`. The whole point is
that the spot key comes from `ChartQuery.spot_key`, the derivation Phase 04 already shares
between the importer and the lookup, rather than from a second derivation here that could
drift from it.

Not in scope: committing a decision audit file
(`SIMULATOR-DECISION-AUDIT-NOT-COMMITTED`), the bb/100 unit and hand-id prefix
(`SIMULATOR-REPORT-UNITS-AND-IDS`), and the unexercised noise threshold
(`SIMULATOR-NOISE-THRESHOLD-UNPINNED`). All three are real and none of them is this.

## Delegation Plan

- Worker lanes: three. Lane C changes `StrategyRefusal` to carry ordered detail and makes
  the preflop chart populate it from `ChartQuery.spot_key` and `hand_class`. Lane S fixes
  the simulator so a refused hand keeps its partial street and carries no completed
  normalized record. Lane I writes the inventory report. Lane R is the review pass.
- Ownership: Lane C owns `strategy/contract.py` and `strategy/preflop_chart.py`. Lane S
  owns `simulator/**`. Lane I owns the report generator. The coordinator owns the two
  contracts, the mutation entries, the freeze lock, `CURRENT_TASK.yml`, and every commit.
- Status: Lane C planned. Lane S planned. Lane I planned. Lane R planned.
- Delegation availability: subagent delegation is disabled in this session, so the
  coordinator implements each lane in order and performs the review pass itself, with the
  reason recorded here and in the review notes. `AGENTS.md` step 10 permits that. Phases
  06 and 07 took the same exception; the cost is real and is stated rather than implied.
- Expected outputs: Lane C returns a refusal that reports its spot key, plus the Phase 03
  tests that pin the serialization. Lane S returns a refused hand carrying its actions and
  the Phase 07 tests that pin it. Lane I returns the inventory file. Lane R returns
  findings classified blocker or not.
- Integration order: Lane C first, because the other two consume what it produces. Lane S
  second. Lane I last, because it reports on both. The gate runs after each lane.
- Review handoff: the reviewer checks that the spot key is the lookup's own and not
  re-derived; that a refused hand's actions are complete rather than merely present; that
  no test asserting something "for each refused hand" can pass vacuously, which is the
  failure mode this repo has now hit twice; and that the inventory's ordering is by hands
  reached rather than by any incidental dictionary order.

## Slices

- [x] Contract: Phase 03 requires a refusal to carry structured detail naming what was
  missing, with the code left as a groupable vocabulary. Phase 07 requires a refused hand
  to keep its action, to stop claiming to be a completed history, and requires the
  inventory as a report of its own whose diff is the record of coverage improving.
- [ ] Lane C: `StrategyRefusal.detail`, serialized with the record; chart misses report
  spot key and hand class.
- [ ] Lane S: `_play` files the partial street before returning on a refusal;
  `HandResult` carries `streets` always and a completed `normalized` only when settled.
- [ ] Lane I: `reports/active/latest_refusal_inventory.txt`, ordered by hands reached,
  stating that it is a lower bound on the gap rather than a census.
- [ ] Canaries: one per half of the fix - a refusal that forgets its detail, and a
  refused hand that loses its partial street - each proven to make the gate fail.
- [ ] Review, then closeout to idle with the gate green.

## Verification

Command IDs: the existing `pytest_strategy_contract`, `pytest_simulator`, and
`generate_profile_comparison_report`, plus the full derived gate and `check_gate_bite`.
No new command IDs: the inventory is written by the generator that already runs, so the
phase's command surface does not change and a completed phase does not grow a new gate
entry.

Reports: `reports/active/latest_profile_comparison_report.txt` and
`reports/active/latest_refusal_inventory.txt`. The second is red until Lane I lands, which
is the expected mid-task state and the reason `check_contracts` fails in between.

The number to watch: the inventory should account for all 128 refused hands in the
committed self-play run. A total that comes out lower means detail is being dropped
somewhere, which is the whole defect this task exists to fix, wearing a different hat.

## Outcome

Not yet complete. Contract landed; implementation next.

## Next Agent Bootstrap

This is not a loop phase - Phase 07 is closed and tagged, and `verification/loop_state.yml`
records its loop as complete. This task runs under `CURRENT_TASK.yml` alone: contract-update
first, then implementation, then closeout to idle.

Read `reports/phase_audits/reviews/PHASE_07_SIMULATOR_REPORTS.md` before touching the
simulator. The blocker there is the reason this task exists, and it carries the measured
numbers that any fix has to reproduce.

Two things this repo has learned the hard way and will keep re-learning without care.
A test written as "for each refused hand, assert X" passes perfectly when no hand is
refused; both Phase 06 and Phase 07 shipped that shape and only a mutation canary caught
it. And a canary aimed at a defensive assertion, or at a change that is deterministic,
proves nothing; it has to break an observable behaviour.
