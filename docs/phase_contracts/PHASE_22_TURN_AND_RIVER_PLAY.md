---
phase_id: "22"
title: "Turn And River Play"
depends_on:
  - "21"
required_gate_commands:
  - pytest_turn_and_river_play
  - generate_turn_and_river_play_report
required_reports:
  - reports/active/latest_turn_and_river_play_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_22_TURN_AND_RIVER_PLAY.md
---

# Phase 22: Turn And River Play

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Declared by MAINT-43 on 2026-10-04 as Live Turn And River, and re-scoped by MAINT-44 the same day.
Taylor first ruled that the turn and river are both solved at the table. He then re-ruled: the turn
is stored like the flop, and only the river is solved at the table, because storing the river is
4,127,760 spots per preflop line while one live river solve measured about 25 milliseconds. He set the
river's limit at one second. `AGENTS.md` states the boundary. Phase 21 now solves and stores the turn
beside the flop and leaves playing it to a later phase; today the bot refuses on every turn and river.
This phase makes it answer both: the turn from phase 21's stored strategy, the river by a live solve.

Taylor's rulings that shape it:

1. **The engine for the river is GTOpen.** This repo does not write a solver of its own. He ruled it
   after being told that GTOpen carries no licence - no LICENSE file and no mention in its README or
   `Cargo.toml` - so the missing licence is recorded here as an accepted risk, not a resolved one,
   the way phase 20 records its platform risk. Whether GTOpen stays a sibling clone outside this
   repo, as it is for the offline solves, was not ruled; stage 1 drafts it and the human gate asks.
2. **It waits for the flop campaign.** The turn it plays is the one phase 21 stores, and a river
   solve needs both players' ranges at the river, walked from the stored flop and turn strategy
   along the line actually played. So this phase depends on 21.
3. **Phase 20 waits on it.** A bot that refuses every turn and river should not sit down at
   Taylor's table, so 20 depends on this phase.

Playing the stored turn is this phase's by assignment rather than by ruling: phase 21's contract says
a later phase plays it, and this is the phase that already owned making the bot answer a turn.

What it has to answer is `LIVE-TURN-AND-RIVER-SOLVING` in `backlog.yml`, adopted here; its id predates
the re-ruling. Four more are adopted with it, each one a place a builder meets the turn:
`THE-GATE-ENFORCES-A-SEAM-SENTENCE-THIS-PHASE-MEASURED-AS-FALSE`,
`A-COMMITTED-CELL-CARRIES-NO-STREET-SO-THE-IMPORTER-CHECKS-EVERY-BET-AGAINST-THE-FLOP-MENU`,
`A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` and
`A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED`. The backlog entry's questions that the rulings
leave open are this phase's: the gate, the ranges entering the river, bets off the menu,
determinism, where the solve runs, pots with three or more players, and anchoring a river re-solve
to the stored turn strategy. Where the solve runs is Taylor's to rule, as the backlog entry says.

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
on a turn or river it cannot answer - a turn phase 21 did not store, a pot with three or more
players, a missing server, a solve that runs too long - is not ruled, and is a human-gate question
rather than something a stage chooses.

Phase 22 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not write a solver. Ruling 1 chose GTOpen.
- Do not commit river solutions as a strategy artifact the bot answers from. The boundary in
  `AGENTS.md` chose live solving over storage for the river. Recorded solver replies committed as
  test fixtures are not that.
- Do not solve preflop, the flop or the turn at the table. That half of the boundary holds.
- Do not solve or store turns phase 21 did not. Coverage of the turn is phase 21's.
- Do not add PokerNow automation, browser or platform observation, UI surfaces, large hand-history
  ingestion or LLM-backed poker decisions. `AGENTS.md` Boundaries.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_turn_and_river_play_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_turn_and_river_play`
- `generate_turn_and_river_play_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- How long a river decision takes at the table, on which machine and thread count, beside the
  one-second limit Taylor set. The solve stops by a rule that does not read the clock, so the limit
  is shown by measurement rather than enforced by a timer.
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
- Every committed preflop, flop and turn answer is unchanged.
