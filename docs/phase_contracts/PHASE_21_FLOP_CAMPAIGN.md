---
phase_id: "21"
title: "The Flop Campaign"
depends_on:
  - "16"
required_gate_commands:
  - pytest_flop_campaign
  - generate_flop_campaign_report
required_reports:
  - reports/active/latest_flop_campaign_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_21_FLOP_CAMPAIGN.md
---

# Phase 21: The Flop Campaign

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Declared by MAINT-40 on 2026-09-26 from Taylor's ruling of that date: trust the solve and get more
of it, rather than measuring the bot first. Phase 16 built the machinery - the postflop key, the
index, the object storage format, the solve driver - and closed on a sample rather than on coverage,
which its decision 25 states. `data/artifacts/postflop/index.json` holds five flop decision points on
four boards for one preflop line, the button opening and the big blind calling, seen from both
seats; those four board classes are 44 of the 22,100 three-card flops. `data/artifacts/postflop/sample/`
carries four of the five cell documents, on three boards and 40 flops, and the fifth, `Ac8c3c`, is
indexed but its cell document is not in git. On every other flop the bot refuses, and on the flops it
holds it refuses one action later, because no decision point that follows a committed one is
committed. Phase 16's packet names both causes of its null table result: too few boards, and no
closure.

Three parts, in this order, because each one prices the next:

1. **Use every core.** GTOpen's server prints "solver threads: 5" on a ten-core Apple M4. The cause
   is in its source: it takes half of `available_parallelism()` on purpose, to skip hyperthreads on
   what its comment calls a memory-bound workload, unless `SOLVER_THREADS` overrides it. The M4 has
   no hyperthreads, so five is half the machine; whether ten is faster is unmeasured. Measure five
   against ten, set the thread count explicitly on every machine, and record it beside every timing
   from here on. `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`. If the setting is
   not enough, GTOpen is a read-only clone; a patch lives in a local clone and is recorded the way
   earlier phases recorded theirs.
2. **Pick the cloud machine.** Phase 16's decision 24 rules that the campaign runs on a rented box
   whose specification was left open. Solve and time one flop on a few candidates, re-prove
   determinism on the one chosen, since phase 16's proof holds only on the Mac it ran on, and choose
   on cost per solved flop with the memory a solve needs as a hard limit.
3. **Run the campaign.** Solve preflop lines in the order phase 16's decision 3 ruled, by how often a
   line is reached and can be served, into the index and object storage format phase 16 built, as
   many lines as cost and index allow, with the report naming which limit applied. Decision 3 rules a
   method rather than a list, and the order phase 16's report prints comes from the public corpus and
   disagrees with the chart's own arrival order at rank 1, so which order ranks the campaign is a
   stage-2 question. A solved board must also close: every flop decision point reachable from a
   committed one is committed or refused by name, or the campaign buys boards the bot still cannot
   play. `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`. Nothing is re-solved
   or hand-edited to look better.

Phase 16's rulings carry into this phase: full-precision f32 arenas (decision 20), the 0.40 memory
ceiling (decisions 20 and 22), an index plus object storage with no git LFS, the rented box governing
the campaign (decision 24), and no run on GTOpen's untested CUDA path until one flop is solved and
timed on the box. Stage 2 may reopen one only through a decision of its own; the memory ceiling is
`runtime-reversible` and moves together with the over-read the adopted memory-guard entry names. The
0.3%-of-pot target is already a code constant, `EXPLOITABILITY_TARGET_PCT_OF_POT`, and would become
the campaign's target silently, so stage 2 asks rather than inherits it.

Adopted from `backlog.yml`, each to be closed or carried by this phase, and each entry's adoption
note says what closes it: `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`,
`EVERY-ARENA-FIGURE-IN-THE-COST-RECORD-IS-A-QUANTIZED-ARENA-AND-FULL-PRECISION-ROUGHLY-DOUBLES-IT`,
`THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`,
`THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR`,
`A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`,
`A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`,
`POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`, `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`,
`THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`,
`THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`,
`QUANTIZED-ARENAS-PUT-A-FLOOR-UNDER-EVERY-EXPLOITABILITY-THIS-PHASE-MEASURED` and
`NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`.
`A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE` stays a `contract-update` task
for phase 16's own wording; this contract carries its two terms, that the rented box governs the
campaign and that determinism is re-proved on that box.

It depends on 16 alone, because 16 is the machinery it runs. Phase 19 depends on it, ruled by Taylor
on 2026-09-26, so that any rule of thumb 19 writes for a flop covers only what this campaign could
not solve, and 19 measures its merge against the bot this campaign leaves.

Phase 21 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not solve preflop spots the chart is missing - four-bets, limped pots, other stack depths. They
  need a re-solve of the preflop chart and are a separate phase.
- Do not commit turn or river spots. Phase 16's decision 1 rules flop only.
- Do not group similar flops so that one solve answers several. `POSTFLOP-BOARD-ABSTRACTION` stays
  deferred in `docs/ROADMAP.md`, and suit isomorphism remains the only collapse permitted.
- Do not re-solve, hand-edit or drop a cell because its numbers look wrong. A solved cell is
  committed as solved or refused by the rule phase 16 ruled, and a finding about it is a finding.
- Do not add runtime solver calls, LLM-backed poker decisions, PokerNow automation, browser or
  platform observation, UI surfaces or large hand-history ingestion. `AGENTS.md` Boundaries.
- Do not spend on a cloud account, or provision anything outward-facing, before Taylor has ruled the
  provider, the machine candidates and a spending cap.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_flop_campaign_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_flop_campaign`
- `generate_flop_campaign_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- What was spent, on which machine, against the cap Taylor ruled, and what each solved flop cost.
- How many preflop lines and flops the bot can now play, beside how many it could before, and which
  limit stopped the campaign where it stopped.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not change this contract during implementation mode.
- Do not carry a laptop timing or a laptop determinism proof to the rented box as though it had been
  measured there.
- Do not report a campaign figure without the machine and thread count it was measured at.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- Every cell phase 16 committed stays byte-identical unless this contract names why it moves.
