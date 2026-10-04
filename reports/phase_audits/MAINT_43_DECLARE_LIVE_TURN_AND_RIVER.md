# MAINT-43 audit packet: phase 22 declared

MAINT-42 lifted the runtime-solver boundary for the turn and river, and nothing owned building it.
Taylor ruled on 2026-10-04 that it gets its own phase, that the phase waits for the flop campaign,
that it drives GTOpen rather than a solver of the repo's own, and that phase 20 waits on it. This
task declares phase 22, Live Turn And River, as a skeleton the loop can start. It changes no range,
artifact, code path or test.

## What shipped

- `docs/phase_contracts/PHASE_22_LIVE_TURN_AND_RIVER.md`: skeleton, `depends_on: ["21"]`,
  placeholder command ids `pytest_live_turn_river_solve` and `generate_live_solve_report`, which are
  not registered and so add nothing to the gate while the phase is `future`. It states the rulings,
  records GTOpen's missing licence as an accepted risk, names the gate and GTOpen's single session as
  the two questions ruling 1 sharpens, and leaves each open question to stage 1's draft and the
  human gate.
- `phase_status.yml` gains 22 at `future`; `verification/loop_policy.yml` gains 22 with
  `auto_advance: false`.
- Phase 20's `depends_on` gains 22, with one sentence saying why; its statements that every decision
  comes from the committed strategy, and that it adds no runtime solver calls, now except phase 22's
  live solve.
- `AGENTS.md`: the boundary names phase 22 as the builder.
- Both roadmaps place 22 in the table, the graph and the argument.
- Backlog: `LIVE-TURN-AND-RIVER-SOLVING` and four entries a phase 22 builder will meet are adopted by
  22; two alignment items from the review are filed.

## How to check it without code

1. Open `docs/phase_contracts/PHASE_20_HOME_GAME.md` and read `depends_on`: 16, 19 and 22.
2. Open `docs/phase_contracts/PHASE_22_LIVE_TURN_AND_RIVER.md` and read `depends_on`: 21.
3. Compare both with the table and the drawing in `docs/ROADMAP.md`.
4. Open `phase_status.yml`: the last entry is 22, `future`.

## Independent review

One read-only reviewer that wrote none of this and ran no gate, note at
`reports/phase_audits/reviews/MAINT_43_DECLARE_LIVE_TURN_AND_RIVER/independent-review.md`.

- **Blocker, resolved.** A non-goal said a cache that persists across hands is storage. Taylor never
  ruled that, and as worded it also banned recorded solver replies committed as test fixtures, the
  very gate design the contract leans toward. It now forbids committing turn or river solutions as
  a strategy artifact the bot answers from, and says test fixtures are not that.
- **Blocker, resolved.** A non-goal said heuristics for a turn the live solve cannot answer are
  phase 19's. Phase 19's lift is preflop only and 19 does not depend on 22, and the line quietly
  answered the multiway question as "refuse, no owner". It is struck; what the bot does on a turn
  the live solve cannot answer is now a human-gate question.
- **Non-blockers, fixed.** The vetting line called the turn figure a limit Taylor ruled; he accepted
  it and set a limit only on the river, and since the solve may not stop by the clock the river
  limit is shown by measurement. "Kept outside the repo" was written as his ruling and was not; the
  licence is now an accepted risk and vendoring an open question, and the non-goal against copying
  GTOpen in is removed. The contract said stage 1 settles the gate while the loop policy says the
  human gate asks; it now says stage 1 drafts and the human gate asks, and that where the solve runs
  is Taylor's. The drawing read as 22 depending on 18 and is redrawn. Phase 20's reproducibility
  requirement now names what a live answer's record must carry, in 22's contract. Four open entries
  a builder will meet are adopted, and the adopted entry's title is no longer stale.
- **Alignment, filed.** `THE-FLOP-CAMPAIGN-IS-NOT-TOLD-ITS-CELLS-ARE-THE-TURN-RANGE-SOURCE`, owned by
  21 since it is best settled while 21 runs, and `NO-PHASE-OWNS-A-TURN-REACHED-AFTER-A-HEURISTIC-ANSWER`.
- **Round 2:** one blocker - the four adopted entries kept their old owner field - fixed by moving
  each to 22. Three non-blockers fixed: the heuristic alignment item now covers a preflop spot 19
  fills, which is the certain case; the campaign item points at 21's decision list rather than a
  stage 2 it has passed; and 22's contract lists the four adopted ids.
- **Held back:** the turn timings were probably taken on five of ten cores, which phase 21 is
  measuring; GTOpen's server never frees memory, so a long table session slows; whether running
  unlicensed code is itself a legal problem; duplicate entries in the scope-change log; and
  `loop_fleet --plan` was not run.

## Gate

Pending, and held until phase 21's all-core solve on this laptop finishes.
