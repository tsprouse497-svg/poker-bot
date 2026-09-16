# MAINT-34: A Realistic Blind Three-Bet

- **Task** `MAINT_34_REALISTIC_BLIND_THREE_BET`
- **Mode** `contract-update`
- **Branch** `maint/34-realistic-blind-three-bet`, worktree `~/projects/poker-bot-worktrees/maint-34`
- **Base** `19beb97f21981ec6fcc18d7635127604f405b9e7`, which is `main`
- **Authorised by** Taylor, 2026-09-16, recorded as phase 16's decision 19 and filed as
  `RE-SOLVE-THE-PREFLOP-CHART-WITH-A-REALISTIC-BLIND-THREE-BET`

## Objective

Re-solve the committed preflop chart so the blinds three-bet a realistic size, and re-derive
everything downstream of it honestly.

## Why, in one measurement

At `t6/d100/BB/BTN:raise@2.5` in the committed export, every pocket pair from aces down to fives
sits at `raise 1.0, call 0.0` - and so does the pair of deuces. Only fours and threes flat. So the
big blind three-bets deuces and calls with fours.

That is an artefact, not a strategy, and it is not a preflop curiosity: the big blind's **call**
branch is the entire out-of-position input to every postflop solve. Phase 16 solved a real flop cell
against it on `9c8c7c` and hero's continuation bet came out at **99.94% of range with no combo
checking more than 20%** - the solver correctly exploiting a caller who can never hold a set or an
overpair. A bot committed on that basis teaches a student to c-bet far too little.

The cause is that `raise_mults` is a single global `[3.0]`, so the big blind's only three-bet against
a 2.5bb open is 7.5bb where a realistic size is 13.5. A three-bet that cheap makes flatting worse
than it is.

## The route, ruled before any solve

`raise_mults` is the "re-raise TO-amount as multiples of the current bet", applied at **every**
re-raise level and varied only by seat, never by depth
(`~/projects/GTOpen/crates/solver/src/preflop/mod.rs:54-55`, `mults_of` at `:97-102`). So "change one
field" has three readings and two of them are traps.

- **Route A, `raise_mults: [5.4]`. REJECTED.** The three-bet becomes 13.5 and the next rung becomes
  13.5 x 5.4 = 72.9. `mod.rs:2219` clamps any raise at or above `allin_threshold * stack` to the
  stack, and the ruled config is `allin_threshold: 0.67`, `stack: 100.0`, so **72.9 is clamped to a
  jam**. The sized four-bet ceases to exist and all 219 three-bet-facing committed spots become
  fold / call / shove. Verified by the coordinator at the source. This is the reading "one config
  field" invites and it would have produced a worse caricature than the one being fixed.
- **Route B, `raise_mults: [3.0, 5.4]`. REJECTED.** Phase 14 already priced a second multiplier:
  38,828 action nodes and 112 MB became 260,136 nodes and 754 MB
  (`PHASE_14_CHART_CUTOVER_DECISIONS.md:1053-1057`). Extrapolated at today's 33,969 nodes and
  75.22 bytes a node that is ~227,600 nodes and ~16.3 MiB, taking `data/artifacts` to about 94% of
  its 20 MiB cap. The cap is a halt, not a budget.
- **Route C, `raise_mults_by_seat` with 5.4 on the two blind seats and everyone else on the global
  3.0. RULED.** Blind three-bets become 13.5, in-position three-bets stay 7.5, and the four-bet
  survives as a sized raise at 40.5 - under the 67 clamp.
  **Corrected 2026-09-16.** That verification covered the button four-betting over a blind and was
  generalised to a case it did not cover. A **blind** four-betting over the other blind's 13.5 gets
  the 5.4 again, 72.9, which clamps to a jam - so 49 of 254 three-bet-facing committed spots offer
  no sized four-bet. Caught by the solve lane, measured, and accepted by Taylor as decision 4 after
  the two-size alternative measured worse. See
  `A-BLIND-CANNOT-FOUR-BET-A-BLIND-WITHOUT-JAMMING-AND-THE-MULTIPLIER-GEOMETRY-SAYS-WHY`.

**Route C carries an obligation that is not optional.** `config_errors` iterates `RULED_CONFIG.items()`
and checks each posted value, so a field that is **not** in `RULED_CONFIG` is invisible to the card
check, the frozen config guards and the gate. `raise_mults_by_seat` must be added to `RULED_CONFIG`
or the export's own origin becomes uncheckable.

## The measurement this rests on, and what it does not fix

Established in phase 16's lane against a baseline solve that reproduced the committed export at
**0 basis points** of strategy and reach divergence, converging at iteration 1,900 to
`0.00015590818199695747` - the source card's own `achieved_gap_bb`, digit for digit. **Every figure
below is re-derived in this task rather than carried across from that lane.**

| | committed 7.5bb | re-solved 13.5bb | committed reference |
| --- | --- | --- | --- |
| fold / call / 3-bet | 63.35 / 21.09 / 15.57 | 62.67 / 24.41 / 12.91 | 60.57 / 26.54 / 12.89 |
| genuinely mixed classes | 3/169 | 9/169 | 40/169 |
| 3-bet bias on pairs | +0.4025 | +0.0451 | 0 |
| pocket pairs in the call branch | 12.0 of 78 | 39.9 of 78 | 43.4 of 78 |
| sets on `9c8c7c` | **0.00 combos** | **7.40 combos** | 8.34 combos |

Isolated by a control: the same multiplier applied to the **button only** reproduces route C's 40.5bb
four-bet while leaving the three-bet at 7.5, and shows no gain at all - 0.00 sets, bias +0.3816. The
three-bet size is what moves the pairs.

**Not fixed, and not to be reported as fixed.** The big blind still over-folds: total defence moves
36.65% to 37.33% against a rake-free reference band of roughly 40 to 65. And the realization model is
still blind to SPR - `class_r(h, posw)` takes the hand class and a static positional weight and
nothing else, while the SPR-aware `seat_mult` is marked KEPT FOR ANALYSIS ONLY and is off the solve
path - so threes still three-bet while fours and deuces flat, and 9 mixed classes against a
reference's 40 is still far too pure.

## The two things that will go wrong quietly

1. **`chart_provenance.py` is hardcoded prose that no check recomputes.** `ARTIFACT_NOTES` states
   "249 of that solve's 33,969 action nodes", "98.59 percent", and "every committed spot offers
   exactly one raise: 2.5 to open, 7.5 to three-bet, 22.5 to four-bet". `chart_derivation.py` writes
   it into the committed chart's `audit_fields.notes`. After the re-solve the chart ships a note
   stating the old ladder as fact, `convert_preflop_export.py --check` reproduces it happily because
   it reproduces whatever the code emits, and **no gate command disagrees**. This is the maint-30
   failure - a document telling a reader something false - moved inside the data.
2. **Re-keying re-seeds every mixed cell.** 219 of the 249 committed keys embed `raise@7.5`, and
   `preflop_chart.py:485` builds the draw seed from the spot key text, so every mixed cell
   re-randomises. `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL` records phase 12 moving a profile comparison
   from 128/472 to 126/474 for exactly this reason. Every self-play and comparison figure will move
   for a reason that is not poker, and a real regression arriving in the same task is
   indistinguishable from the re-seed unless the two are separated deliberately.

## Contract amendments

`check_file_sizes` caps a contract at 300 lines and compares `> limit`, so 300 passes. Phase 14 is at
**299**, phase 10 at 294, phase 13 at 295. AGENTS.md allows an amendment of **at most** two lines
plus the backlog id, so a one-line amendment fits phase 14 and **no fold-in rewrite is required** -
the blast-radius map concluded one was, by assuming two lines.

Phase 14's `:45` reads, verbatim, "**No re-solve at all.**" That is the standing prohibition this
task reverses, and it is amended rather than left asserting the opposite.

## Delegation Plan

Lanes are worker subagents in this one worktree; the coordinator owns every commit, the scope, the
rulings and the integration. No two lanes write the same file.

- **M1 - blast radius.** Done, read-only. Produced the dependency map, the producer order, the gate
  categorisation, the frozen-test inventory and the contract headroom table. Its central finding -
  that route A jams the four-bet - is the reason this plan has a route section. Its conclusion that
  phase 14 needs a rewrite was re-measured by the coordinator and corrected.
- **S1 - the solve.** Adds `raise_mults_by_seat` to `RULED_CONFIG`, runs the extraction, runs
  `--determinism-only` as a second full solve in a fresh process, and runs `convert_preflop_export.py`.
  Owns `gtopen_config.py`, the export, the card, the chart and the sizings.
- **P1 - provenance.** Owns `chart_provenance.py`. Makes the artifact's own note either derived from
  the export or checked against it, so finding 1 above cannot recur silently.
- **T1 - the frozen tests.** Opens `tests/**` and the lock ONLY after the new export exists, and
  corrects each pinned value against a measured number. Never against a number a lane wishes were
  true. Reports every change with what forced it.
- **D1 - documents.** `CORPUS_COMPARISON_LIMITS.md`, `GTOPEN_SOLVER_NOTES.md` and the two stale
  docstrings M1 found.
- **R1 - independent review.** Read-only, and none of the above. Briefed on the poker rather than on
  the diff: whether the new ranges are better poker, and whether anything in the repo still claims
  the old ladder.

## Slices

- [x] S0 Precheck. Lane opened from `main` at `19beb97`, blast radius mapped, route ruled.
- [ ] S1 Config and amendments. `raise_mults_by_seat` into `RULED_CONFIG`; three one-line amendments.
- [ ] S2 Solve, determinism run, convert. New export, card, chart, sizings.
- [ ] S3 Provenance. The artifact stops asserting its own stale ladder.
- [ ] S4 Frozen tests, against measured values, then re-freeze.
- [ ] S5 Documents and the report prose.
- [ ] S6 Gate, `check_gate_bite`, independent review, packet, closeout.

## Next Agent Bootstrap

- Worktree `~/projects/poker-bot-worktrees/maint-34`, branch `maint/34-realistic-blind-three-bet`.
  Never work in `~/projects/poker-bot`, which holds `main`.
- `task_mode: contract-update`. `base_commit` `19beb97f21981ec6fcc18d7635127604f405b9e7`.
- **Route C is ruled. Do not re-open it, and above all do not simplify it to `raise_mults: [5.4]`** -
  that clamps the four-bet to a jam and is the single most likely way to wreck this task.
- **`tests/**` and `verification/freeze.lock` are not in scope until the new export is on disk.**
  Roughly 142 numeric assertions across 24 test files read the chart. Correcting one before the
  number exists is how a test gets fitted to a hope.
- Phase 16 is halted at stage 6 in its own worktree waiting for this. Its decision 19 carries the
  reasoning and its lane holds the harvest, the writer and the solve driver, all built and green.
