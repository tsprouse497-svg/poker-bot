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
  the 5.4 again, 72.9, which clamps to a jam - so 34 of 135 three-bet-facing committed spots offer
  no sized four-bet, split SB 29 and BB 5, re-measured after decision 7 from the 49 of 254 Taylor
  ruled on. That is the MENU count, which is what `offer` asks for; 33 spots have a class that
  actually takes the jam, and decision 4 records which spot separates the two. Caught by the solve lane, measured, and accepted by Taylor as decision 4 after
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

All of it is taken at **one spot**, `t6/d100/BB/BTN:raise@2.5`, and the table did not say so until
2026-09-17:

| at `BB/BTN:raise@2.5` | committed 7.5bb | re-solved 13.5bb | committed reference |
| --- | --- | --- | --- |
| fold / call / 3-bet | 63.35 / 21.09 / 15.57 | 62.67 / 24.41 / 12.91 | 60.57 / 26.54 / 12.89 |
| genuinely mixed classes | 3/169 | 9/169 | 40/169 |
| 3-bet bias on pairs | +0.4025 | +0.0451 | 0 |
| pocket pairs in the call branch | 12.0 of 78 | 39.9 of 78 | 43.4 of 78 |
| sets on `9c8c7c` | **0.00 combos** | **7.40 combos** | 8.34 combos |

**The fix is not uniform over the five spots, and the one it does not reach is the heaviest.** Found
by the independent poker review and re-derived here against `git 19beb97`. Sets on `9c8c7c` in the
big blind's call branch, of a possible 9, with each spot's share of the 6,054,005,282 ppb of
committed arrival:

| opener | sets before | sets after | pairs in call, of 78 | arrival share |
| --- | --- | --- | --- | --- |
| LJ | 6.56 | 9.00 | 43.12 -> 49.74 | 2.230% |
| HJ | 1.59 | 9.00 | 28.87 -> 53.18 | 2.126% |
| CO | 0.00 | 8.99 | 26.03 -> 47.98 | 2.083% |
| BTN | 0.00 | **7.40** | 12.00 -> 39.87 | 2.477% |
| **SB** | 0.00 | **0.00** | 11.52 -> 30.00 | **2.665%** |

At `BB/SB:raise@2.5` the chart raises every pair sevens and up at 1.00 and flats sixes and below at
1.00, so no set reaches that call branch before or after. The shape is still strictly better - the
old chart raised `22` at 1.00 while flatting `44` and `33`, and that inversion is gone - but the
spot went *purer*, 7 mixed classes to 2, where the headline spot went 3 to 9. **Phase 16 picks its
flop cells off this table, not off the row above it**, and a c-bet frequency measured at
BB-versus-SB is not evidence about this fix in either direction. No route re-solves it; the artifact
ships as measured and it was the record that was wrong.

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

- Worker lanes: M1 blast radius, S1 the solve, P1 provenance, T1 the frozen tests, D1 documents,
  and two read-only reviewers - the lock-diff reviewer over `tests/**` and R1 over the poker.
- Ownership: S1 owns `gtopen_config.py`, the export, the source card, the chart and the sizings.
  P1 owns `chart_provenance.py`, `chart_provenance_facts.py` and the three stale docstrings in
  `chart_selection.py`. T1 owns `tests/**`. D1 owns `docs/CORPUS_COMPARISON_LIMITS.md` and
  `docs/GTOPEN_SOLVER_NOTES.md`. M1 and both reviewers own nothing and write nothing. The scope,
  the rulings, every commit, the contract amendments, the two cap-forced extractions recorded
  below, the gate and the closeout are the coordinator's. No two lanes write the same file.
- Expected outputs: M1, the dependency map and the contract headroom table. S1, a converged export
  plus a second full solve in a fresh process proving determinism. P1, an artifact note derived
  from the run that writes it rather than hardcoded. T1, every pinned value corrected against a
  measured number, each reported with what forced it. D1, the two documents. The reviewers,
  findings split into blockers, non-blockers and alignment items with the evidence each checked.
- Status: M1 completed, and its central finding - that the obvious one-field config change jams the
  four-bet - is why this plan has a route section. S1 completed, converged at 3,800 iterations with
  determinism byte-identical. P1 completed. T1 completed; it also found the untrained cells and the
  two-walk disagreement, both of which became rulings. D1 completed. Reviewers in progress.
- Integration order: config and amendments, then the solve, then provenance, then the frozen tests
  and the re-freeze, then the documents. Strictly in that order, because each stage's numbers are
  the next stage's input, and `tests/**` and `verification/freeze.lock` stayed shut until the export
  was on disk so no assertion could be fitted to a figure nobody had measured.
- Review handoff: the lock-diff reviewer was told the risk is a test weakened rather than corrected,
  given the exact two deletions and one exemption the decisions authorise, and asked to cross-check
  changed pins against the artifacts rather than take them on trust. R1 was told to review the poker
  and not the diff: whether the new ranges are better poker measured against the artifacts, and
  whether anything in the repo still states the old ladder as a live fact. Both were told that
  coming back empty with the checks named is a pass.

**No-delegation exception for the two extractions of 2026-09-17.** `chart_provenance_facts.py` and
the move of the validators fixtures into `derived_chart_shape.py` are coordinator work. The lane
that owns those files stalled twice at the same step, running the suite after finishing its edits,
and a third dispatch to re-derive state it had already produced costs more than the extraction. Both
are mechanical moves under a seam already ruled, no behaviour changes, and the independent review
covers them like everything else.

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
- [x] S1 Config and amendments. `raise_mults_by_seat` into `RULED_CONFIG`; three one-line amendments.
- [x] S2 Solve, determinism run, convert. New export, card, chart, sizings.
- [x] S3 Provenance. The artifact stops asserting its own stale ladder.
- [ ] S4 Frozen tests, against measured values, then re-freeze. Corrections done and the suite is
  green; the lock-diff review was re-dispatched after the session loss below and the re-freeze
  waits on it.
- [ ] S5 Documents and the report prose. The generator prose is written; the report itself had
  never been re-run against it and has now been regenerated.
- [ ] S6 Gate, `check_gate_bite`, independent review, packet, closeout.

**Session lost 2026-09-17, and what was recovered.** The coordinator session ended mid-S4 with both
reviewers in flight and their findings unwritten, so neither round survives and both were
re-dispatched from the same briefs. Nothing else was lost: the working tree held the whole of the
test corrections and the generator prose, and `uv run python -m pytest tests` reads 1192 passed, 4
skipped against it. Two things the loss left behind. `reports/active/latest_verify.txt` and
`verify_results.json` hold the output of a SINGLE command, not a gate, and say "All passed: True"
over one line - a partial run's record is not a record, and the S6 gate overwrites both.
`reports/active/latest_derived_chart_report.txt` was stale: `generate_derived_chart_report.py`
carried 103 lines of corrected prose that nothing had run, so the committed report still told a
reader the chart holds 249 spots and no jam. Regenerated here, it reads 156 and names the 34 spots
where a blind's four-bet over the other blind's 13.5 clamps to a shove.

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
