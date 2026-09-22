---
phase_id: "19"
title: "Heuristics And Merged Charts"
depends_on:
  - "16"
  - "18"
required_gate_commands:
  - pytest_strategy_substitution
  - generate_substitution_report
required_reports:
  - reports/active/latest_substitution_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_19_HEURISTICS_AND_MERGED_CHARTS.md
---

# Phase 19: Heuristics And Merged Charts

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Declared by MAINT-35 on 2026-09-21 from Taylor's ruling of that date: fill the refusal gaps by
building heuristics and merging the solved charts with the unsolved spots, rather than refusing. This
is the phase at which the "no heuristic guessing for missing preflop chart spots" line in the
Boundaries section of `AGENTS.md` lifts, and it lifts here and nowhere earlier.

The condition on the lift is that a substituted answer is never silent. Every answer this phase adds
carries, on the decision itself, what produced it and what it stood in for, in the same way a price
substitution is already carried today. A reader of a decision can always tell a solved cell from a
merged one, and a merged one from a heuristic one, without reading the code that produced it. A
substitution that cannot be seen at the decision is a worse outcome than the refusal it replaced,
because a refusal at least announces itself.

It depends on 16 for the flop cells there are anything to merge with, and on 18 because a merge is a
claim that playing something beats playing nothing, and that claim is measured against the yardstick
rather than asserted. A rule that measures no better than refusing does not ship.

Phase 19 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not overwrite a solved cell with a heuristic. Substitution fills what the solve does not answer;
  where the solve answers, the solve wins.
- Do not ship a substitution rule whose measured result against the phase 18 pool is no better than
  refusing. Filling a gap with a worse answer is not filling it.
- Do not emit a substituted answer that reads identically to a solved one. Every substitution names
  itself on the decision, with what it stood in for.
- Do not add PokerNow automation or browser observation. Those are phase 20's.
- Do not add runtime solver calls or LLM-backed poker decisions. A heuristic here is committed,
  deterministic and readable; a model asked at the table is none of those.
- Do not add UI surfaces.
- Do not map an unsolved board onto a solved one. The lift this phase carries is for missing
  *preflop* chart spots and reaches no further. Phase 16's decision 2, ruled by Taylor on
  2026-08-19, says the fallback is fewer preflop lines, then a flop subset plus refusal, and never a
  subset plus abstraction; grouping flops by rank texture is filed as POSTFLOP-BOARD-ABSTRACTION and
  stays deferred in `docs/ROADMAP.md`. Decision 2 says in as many words that amending the boundary
  for board texture is a `contract-update` in its own right, so it is not something this phase's
  lift does by implication.
- Do not re-solve, hand-edit or widen the committed chart to reduce the number of gaps that need
  filling. That is a different task under `contract-update` and it is not this one.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_substitution_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_strategy_substitution`
- `generate_substitution_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- Each substitution rule stated in plain words, with the spots it covers and the measured result of
  covering them beside the measured result of refusing them.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not change this contract during implementation mode.
- Do not let a substituted answer share a reason code, an audit field or a report row with a solved
  one, and do not report coverage as though a filled gap and a solved spot were the same thing.
- Do not tune a heuristic against the same hands the result is then reported on.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- The refusal inventory is expected to shrink, and the report says by which rule rather than by how
  much alone.
