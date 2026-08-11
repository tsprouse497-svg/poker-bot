# Phase 01 Core Engine ExecPlan

## Objective

Implement the deterministic 2-9 player NLHE core engine, synthetic golden-hand
fixtures, required replay report, and Phase 01 audit packet.

## Scope

Approved scope is defined in `CURRENT_TASK.yml`. Phase 01 is limited to
`poker_core` rules/state/outcomes, deterministic golden hands, tests, verifier
commands, generated reports, generated status docs, and the audit packet.

Forbidden scope remains `data/raw/**` and `data/processed/**`. This plan also
excludes PokerNow automation, browser/platform observation, UI, runtime solver
calls, strategy logic, preflop charts, and broad hand-history ingestion.

## Delegation Plan

- No-delegation exception: Phase 01 implementation was completed before the
  mandatory early delegation checkpoint existed; its late independent review
  drove the rule that future active ExecPlans must document worker lanes or a
  concrete exception before implementation starts.

## Slices

- [x] Activate Phase 01 task metadata and coordinator ExecPlan.
- [x] Add card, deck, hand-evaluation, betting-state, and settlement primitives.
- [x] Add synthetic 2-9 player golden hands and replay report generation.
- [x] Add focused poker-core tests and verifier command IDs.
- [x] Regenerate status docs and write the Phase 01 audit packet.
- [x] Run required verification and commit the passing gate.

## Verification

Run these command IDs through `scripts/run_verify.py`:

- `pytest_poker_core`
- `generate_phase_01_replay_report`

Then verify the repo with the full Phase 01 gate, including generated docs,
scope, file-size, import, and ruff checks.

Required report:

- `reports/active/latest_replay_report.txt`

## Outcome

Phase 01 implementation, audit packaging, generated docs, and verification are
complete. The local git commit records the passing gate.

## Next Agent Bootstrap

Phase 01 is complete. Start Phase 02 only when `CURRENT_TASK.yml` is updated by
an explicit task request, then read `docs/phase_contracts/PHASE_02_HAND_HISTORY.md`.

```powershell
python scripts/run_verify.py
```
