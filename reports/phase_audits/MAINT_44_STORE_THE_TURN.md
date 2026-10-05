# MAINT-44 audit packet: the turn is stored, only the river is live

MAINT-42 and MAINT-43 put on `main` that the turn and river are both solved at the table. Taylor
re-ruled on 2026-10-04 in phase 21's session that the turn is stored like the flop and only the river
is solved at the table, and confirmed in this session on 2026-10-05 that `main` should change to
match. Phase 21's lane already carries the stored turn and waits on this. It changes no range,
artifact, code path or test.

## What shipped

- `AGENTS.md`: the boundary is now "No runtime solver calls before the river". Preflop, the flop and
  the turn come only from artifacts solved offline; the river is solved at the table, limit one
  second; the first ruling and its same-day reversal are both stated.
- Phase 22 renamed Turn And River Play, moved to `PHASE_22_TURN_AND_RIVER_PLAY.md`, with
  phase-free command ids `pytest_turn_and_river_play` and `generate_turn_and_river_play_report`. It
  plays the turn from phase 21's stored strategy and solves the river live with GTOpen. Playing the
  stored turn is the coordinator's assignment, not Taylor's ruling: phase 21's contract says a later
  phase plays it, and 22 already owned answering a turn. It is reversible by a later
  `contract-update`.
- Phase 20, both roadmaps, the GTOpen notes, the loop-policy reason, `phase_status.yml` and three
  backlog entries follow.
- Phase 21's contract on `main` still says it commits no turn spots. Its lane carries the amendment
  (`82422cb`), and the two agree once it merges, which it will only do after this.

## How to check it without code

Read the boundary in `AGENTS.md` and phase 22's Scope, and compare both with Taylor's words in the
ExecPlan: store the flop and the turn, solve the river live.

## Independent review

Three reviewer runs stalled with no output and were replaced; the fourth, a read-only reviewer that
wrote none of this, completed. Note at
`reports/phase_audits/reviews/MAINT_44_STORE_THE_TURN/independent-review.md`.

- **No blocker.**
- **Non-blockers, fixed.** A missing "than" in `NO-PHASE-OWNS-A-TURN-REACHED-AFTER-A-HEURISTIC-ANSWER`;
  question 8 of `LIVE-TURN-AND-RIVER-SOLVING`, pots with three or more players, still read for the
  turn and now reads for the river.
- **Alignment, resolved by sequencing.** Phase 21's contract on `main` contradicts the stored turn
  until phase 21 merges; its branch carries the amendment, confirmed by reading it.
- **Held back by the reviewer:** the unedited entries
  `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` and
  `A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED`, the phase 21 lane itself, and generated-doc
  freshness, which the gate checks.

## Gate

Pending.
