# ExecPlan: Phase 08 - Tiny Normalized Sample Ingestion And Player Tendency Comparison

## Objective

Pass the Phase 08 gate: `pytest_sample_comparison` and
`generate_sample_comparison_report` green through `scripts/run_verify.py`, with
`reports/active/latest_sample_comparison_report.txt` and
`reports/active/latest_sample_refusal_inventory.txt` committed and fresh, and the audit
packet at `reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md` written for a
non-coding reviewer.

The phase brings in the first oracle this repo did not write.
A committed slice of the public Pluribus corpus is converted into the Phase 02
normalized schema and settled through the Phase 02 replayer, and the settlement must
reproduce the corpus's own `finishing_stacks` for every seat of every hand.
Then, for every preflop decision point in the slice, the bot is asked what it would do
with the same cards in the same spot and the answers are compared.

## The source

- Corpus: the Pluribus subset of the PHH dataset, published by the Universal, Open,
  Free, and Transparent Computer Poker Research Group (University of Toronto).
- Public identifiers: Zenodo concept DOI `10.5281/zenodo.10796885`; GitHub mirror
  `uoftcprg/phh-dataset` (MIT); the hands are the supplementary data of Brown and
  Sandholm (2019).
- Shape, surveyed over all 10,000 hands before this plan was written:
  - every hand has exactly 6 players, starting stacks of 10,000 each, blinds 50/100,
    `min_bet` 100 and zero antes - which is exactly the one spot the committed chart
    answers, so these hands land on the chart rather than in the refusal path by
    construction;
  - `finishing_stacks` is present on all 10,000 and conserves chips on all 10,000;
  - no hole card is obfuscated: all 60,000 dealt cards are known, so a decision can be
    compared with the actual holding;
  - the action vocabulary is three verbs (`f`, `cc`, `cbr`) plus deals and showdown
    declarations, and hands run to 7 aggressive actions, so 4-bet and 5-bet legality is
    genuinely exercised;
  - 81 hands contain a raise to the full stack, and equal starting stacks mean no side
    pots arise;
  - the six seat names rotate across 120 orderings, so Pluribus's own decisions can be
    separated from the five human players'.

## Scope

Approved for the contract-update task (stages 1-3):

- `docs/phase_contracts/PHASE_08_SAMPLE_COMPARISON.md`
- `reports/phase_audits/decisions/PHASE_08_SAMPLE_COMPARISON_DECISIONS.md`

Expected for the implementation task (stages 4-9), to be approved when that task is
activated and narrowed again at stage 5:

- `tests/test_sample_comparison.py`
- `verification/mutations.yml`, `verification/freeze.lock`
- `scripts/run_verify.py` (command registry entries only)
- the sample-ingestion package under `src/poker_training_bot/`
- `scripts/generate_sample_comparison_report.py`
- the committed sample and its source card under `data/samples/` and `docs/`
- `reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md` and its logs

Forbidden throughout:

- `data/raw/**` and `data/processed/**` (existence rule, unchanged)
- the Phase 02 schema and replayer, the Phase 04 lookup, and the Phase 05 and 06
  strategies: consumed, never loosened
- the charts themselves, in response to anything this phase measures

## Delegation Plan

- No-delegation exception: subagent delegation is disabled in this operator's sessions
  ("do not call the Agent tool unless the user requested it"), which overrides the
  coordinator default in `AGENTS.md`. `AGENTS.md` step 10 permits coordinator-owned
  implementation and self-review when the concrete reason is recorded, so this plan
  records it here and the stage 8 review notes repeat it at the top.
- Ownership: coordinator owns every lane - conversion, comparison, report generation,
  tests, and both review rounds.
- Compensating control for the missing independent reviewer: the stage 8 review is run
  as two separate passes with different questions, mechanical then domain, and the
  domain pass reviews the poker rather than the code's fidelity to this contract.
- Review handoff: were a reviewer available, the first thing to inspect is the seat and
  position mapping, because an error there produces a confident comparison against the
  wrong chart cells rather than a failure.

## Slices

- [x] Stage 1: contract carries real acceptance criteria; this ExecPlan is active.
- [x] Stage 2: seven judgment calls recorded, four of them `frozen-into-data`.
- [x] Stage 3: Taylor ruled on all four frozen items and took the recommendation on each.
- [x] Stage 4: `pytest_sample_comparison` authored, red on the missing modules.
- [x] Stage 5: tests frozen; `tests/` and `verification/` left approved scope.
- [x] Stage 6: converter, comparison, and report generator built. Two halts, both
      authoring defects in frozen tests (an attribute name, a line length), each
      repaired in its own task with the tests re-frozen.
- [x] Stage 7: full gate green; 20 of 20 mutations caught including the four authored
      here.
- [x] Stage 8: mechanical pass found nothing the gate had not. Domain pass found the
      headline agreement rate was dominated by folds and treated it as a blocker.
- [x] Stage 9: audit packet, with one hand's settlement recomputable by pencil.
- [x] Stage 10: closeout, tag, idle.

## Verification

- `pytest_sample_comparison`
- `generate_sample_comparison_report`
- `reports/active/latest_sample_comparison_report.txt`
- `reports/active/latest_sample_refusal_inventory.txt`
- Full gate: `uv run python scripts/run_verify.py`

## Outcome

The phase did what it was for: 499 of the 500 selected hands settle to the corpus's
own published finishing stacks, every seat, no tolerance. That is the first claim in
this repository whose right answer came from outside it. The single exclusion is a
chopped pot the corpus records in half chips, named in a committed file.

The comparison half produced a result the gate could never have found. The pooled
agreement rate looked reassuring at 96.3% against Pluribus, but 72% of scored decisions
are folds and folds agree 98.6% of the time. Split by the player's own action, folds
agree 98.6%, raises 93.4%, and calls 60.6%. The chart and real players disagree about
calling four times in ten, which is the same over-folding bias Phase 05 measured at 13
points and Phase 06 built in by construction, now visible against real opponents.

Coverage was the second result: 78 distinct spots the chart cannot answer against real
play, versus 22 from self-play, most of them new. Self-play is blind by construction to
lines its own strategy never takes.

Nothing measured here was used to edit what it measured. All three findings went to
`backlog.yml`.

Two process notes worth carrying forward. Stage 4 checks the phase's pytest command
rather than the gate, so a lint defect in a frozen test stayed latent until stage 7.
And the phase was left at `status: future` in `phase_status.yml` through the whole
build, which silently kept both new commands out of the derived gate until closeout -
`check_gate_bite` exercised them directly, so the canaries were real, but the standing
gate was not running them.

## Next Agent Bootstrap

State: Phase 08 complete, tagged `phase-08-complete`, merged to `main`, repo idle and
clean. Phases 00-08 done; Phase 09 (quality, drift, backlog, and phase-gate hardening)
is next and `verification/loop_policy.yml` marks it `auto_advance: true`.

The most useful artifact the repo now has is
`reports/active/latest_sample_refusal_inventory.txt`: 78 chart spots real hands reached
that the committed charts cannot answer, ordered by frequency and flagged for whether
self-play had already found them. It should replace the self-play inventory as the work
list for whatever chart phase comes next.

Next command: `uv run python scripts/loop_stage.py --start 09`
