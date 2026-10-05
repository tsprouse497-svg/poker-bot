---
phase_id: "22"
title: "Live Turn And River"
depends_on:
  - "21"
required_gate_commands:
  - pytest_live_turn_river_solve
  - generate_live_solve_report
required_reports:
  - reports/active/latest_live_solve_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_22_LIVE_TURN_AND_RIVER.md
---

# Phase 22: Live Turn And River

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Declared by MAINT-43 on 2026-10-04 from Taylor's rulings of that date. MAINT-42 lifted the
runtime-solver boundary in `AGENTS.md` for the turn and the river: they are solved at the table
instead of stored, because storing them is 85,995 turn and 4,127,760 river spots per preflop line
while one live solve measured 1.7 to 2.4 seconds on the turn and about 25 milliseconds on the river.
Taylor accepted the turn at that figure and set the river's limit at one second. Today the bot
refuses on every turn and river. This phase makes it answer them.

Taylor's rulings that shape it:

1. **The engine is GTOpen.** This repo does not write a solver of its own. He ruled it after being
   told that GTOpen carries no licence - no LICENSE file and no mention in its README or
   `Cargo.toml` - so the missing licence is recorded here as an accepted risk, not a resolved one,
   the way phase 20 records its platform risk. Whether GTOpen stays a sibling clone outside this
   repo, as it is for the offline solves, was not ruled; stage 1 drafts it and the human gate asks.
2. **It waits for the flop campaign.** A turn solve needs both players' ranges at the turn, and
   those come from the committed flop strategy walked along the line actually played. Phase 21 is
   what commits that strategy at scale, so this phase depends on 21.
3. **Phase 20 waits on it.** A bot that refuses every turn and river should not sit down at
   Taylor's table, so 20 depends on this phase.

What it has to answer is `LIVE-TURN-AND-RIVER-SOLVING` in `backlog.yml`, adopted here. Four more are
adopted with it, each one a place a builder meets the turn:
`THE-GATE-ENFORCES-A-SEAM-SENTENCE-THIS-PHASE-MEASURED-AS-FALSE`,
`A-COMMITTED-CELL-CARRIES-NO-STREET-SO-THE-IMPORTER-CHECKS-EVERY-BET-AGAINST-THE-FLOP-MENU`,
`A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` and
`A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED`. Two of `LIVE-TURN-AND-RIVER-SOLVING`'s ten
questions are answered by the rulings above - the owner is this phase, and the engine is GTOpen -
and the rest are this phase's: the gate, the ranges entering the turn, bets off the menu,
determinism, where the solve runs, pots with three or more players, anchoring a turn re-solve to
the committed flop strategy, and whether the river is read from the turn solve or solved again.
Where the solve runs is Taylor's to rule, as the backlog entry says.

A live answer must also stay reproducible from a record, which phase 20 requires of every hand. For a
live solve that record has to carry what produced it: the GTOpen commit, the config, the iteration
count, and the thread count and machine.

Two of the questions are sharpened by ruling 1. Stage 1 drafts an answer to each and the human gate
asks Taylor, as `verification/loop_policy.yml` says:

- **The gate.** Phase 10's contract requires the gate to pass on a machine with no GTOpen, no Rust
  toolchain and no network. A live path that needs a GTOpen server cannot run there. `AGENTS.md`
  allows mocks at hard external boundaries, and a separate solver process is one, so the likely
  shape is a gate that tests everything up to the solver call against recorded solver answers, with
  the live solves proved outside the gate. That is a lean, not a ruling.
- **One session at a time.** GTOpen serves one global session, and posting a new spot drops the one
  in progress, so a bot that solves while another solve is running on the same server loses one.

`river_pot_odds.py` stays as a fallback for a river the live solve cannot answer. What the bot does
on a turn the live solve cannot answer - a pot with three or more players, a missing server, a solve
that runs too long - is not ruled, and is a human-gate question rather than something a stage chooses.

Phase 22 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not write a solver. Ruling 1 chose GTOpen.
- Do not commit turn or river solutions as a strategy artifact the bot answers from. The boundary in
  `AGENTS.md` chose live solving over storage. Recorded solver replies committed as test fixtures
  are not that.
- Do not solve preflop or the flop at the table. That half of the boundary holds permanently.
- Do not add PokerNow automation, browser or platform observation, UI surfaces, large hand-history
  ingestion or LLM-backed poker decisions. `AGENTS.md` Boundaries.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_live_solve_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_live_turn_river_solve`
- `generate_live_solve_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- How long a turn and a river decision take at the table, on which machine and thread count, beside
  what Taylor ruled: he accepted the turn at the measured 1.7 to 2.4 seconds and set the river's limit
  at one second. The solve stops by a rule that does not read the clock, so the river limit is shown
  by measurement rather than enforced by a timer.
- What share of turns and rivers the bot now answers, and what it does with the rest.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success. A recorded solver answer stands in for
  GTOpen only at the call boundary, and never for the poker logic around it.
- Do not change this contract during implementation mode.
- Do not report a latency without the machine, the thread count and whether the server was freshly
  started.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- The gate still passes on a machine with no GTOpen, no Rust toolchain and no network.
- Every committed preflop and flop answer is unchanged.
