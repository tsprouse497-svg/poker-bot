# Phase 07 audit packet: Offline Simulator And Bot/Profile Comparison Reports

Written for a reviewer who does not read code.
Everything here can be checked from committed files.

## Summary of what changed

The bot can now be dealt to. Phase 06 gave the repo one strategy object able to play a hand from the first preflop decision to showdown, and nothing that deals one; this phase adds the dealer and the first report that compares two profiles over many hands.

The simulator is a dealer and not a second poker engine. It shuffles, posts blinds, walks the streets, asks each seat's strategy what to do, applies the answer and awards the pot. Every poker rule it appears to know it borrows: legality and betting arithmetic from the Phase 01 engine, turn order and round completion from the Phase 01 turn-order layer, hand ranking and pot splitting from the Phase 01 settlement functions. It decides when to ask, and never what the answer is.

Two profiles exist. `self-play` seats six copies of the Phase 06 composite; `floor` seats one composite against five copies of the Phase 03 reference check-fold strategy. They do different jobs and the report labels each for what it is.

**What this phase measures, and the sentence that matters most.** Phase 06's postflop fallback never bets and never raises, so against another copy of itself every postflop street checks through. A hand is decided preflop by the committed charts and then settled at showdown. Every figure this phase produces is therefore a preflop figure with showdown resolution, and none of them says anything about postflop play.

**What it found that nobody asked for.** Over 600 self-play hands, the committed charts had no answer for 128 of them - 21.3%. That is the first time this repo has been able to count its own preflop coverage gap, and the stage 8 review recovered the shape of it from the decision audit: the misses concentrate in three-bet and four-bet trees. Phase 05 committed 36 spots covering opens, responses to a single open, an opener facing a three-bet, and big blind versus small-blind limp. This is the measured evidence of what that omits in practice.

## Pass/fail checklist

Each line is checkable without reading code.

| # | Check | How to check it | Verdict |
|---|---|---|---|
| 1 | The report says what it does not measure, before any number | `reports/active/latest_profile_comparison_report.txt`, first section | PASS |
| 2 | Chips are conserved in every single hand, not just on average | Self-play net across the table is exactly 0 over 600 hands; a hand whose books do not balance stops the run | PASS |
| 3 | Every hand reaches a terminal state | 121 showdowns, 351 uncontested, 128 refused; 600 total, no other outcome exists | PASS |
| 4 | A refused hand moves no chips and is counted, not converted | Same report, coverage section; `pytest_simulator` pins it | PASS |
| 5 | Refused hands are excluded from the per-hand figures | Report shows 472 measured of 600 dealt | PASS |
| 6 | The simulator agrees with the frozen Phase 02 replayer | 472 of 472 measured hands re-derived, decision points matching | PASS |
| 7 | A run is reproducible from its seed alone | Report prints the seed; two runs of the same config are byte-identical | PASS |
| 8 | A run cannot be disturbed by other randomness in the process | `pytest_simulator` reseeds the global `random` module between runs and demands an identical result | PASS |
| 9 | Any single hand regenerates on its own | Each hand carries its own seed, and a one-hand run at that seed reproduces it exactly | PASS |
| 10 | Position is not an advantage anybody keeps | Report's position table: every seat holds every position exactly 100 times | PASS |
| 11 | Renaming a profile changes nothing about how it plays | Dealt hands name seats, not profiles; `pytest_simulator` pins it | PASS |
| 12 | A table the charts cannot answer is refused at setup | Any table size but six, or any depth but 100bb, raises before a hand is dealt | PASS |
| 13 | The chart bot beats a bot that folds everything | Floor run: +38.67 chips per hand, 14.9 standard errors from zero | PASS |
| 14 | An unseparable difference is not reported as a finding | Self-play names no winner | PASS |
| 15 | Refusal coverage is a headline, not a footnote | Report's coverage section, with counts by reason code | PASS |
| 16 | The gate still fails when the code is deliberately broken | `check_gate_bite`: 14 mutations, all caught | PASS |
| 17 | The refusal figure is the list of uncovered spots it claims to be | Report gives counts by reason code and no spots | **FAIL** |

Line 17 is the stage 8 blocker. It is recorded rather than fixed, and the next section says why.

## Recompute one number by hand

**The number: every seat holds every position exactly 100 times.**

The run deals 600 hands at a six-handed table and the button moves one seat every hand. So each seat should hold each of the six positions exactly 600 / 6 = 100 times. Take the hand count out of the report's own header, divide by six, and compare it against every cell of the position table. No code required.

It is worth checking rather than skimming: if any cell disagrees, the rotation is broken and every per-profile figure in the file is contaminated by seat position rather than being a property of a strategy.

A second check, on the normalization rather than the rotation. In the floor table, multiply a profile's per-hand figure by the measured hand count and it reproduces that profile's total: 38.67 x 600 = 23,200. The two profiles' totals are +23,200 and -23,200 and sum to zero. Chips do not appear or vanish at this table, they only change seats.

## What the comparison measures, and what it does not

Carried forward from Phase 06 rather than restated loosely.

- Against another copy of itself the bot checks every postflop street, so a hand is decided preflop and shown down. Preflop decisions can be measured with equity realised at showdown. **Postflop play cannot be measured, because there is none.**
- Stacks reset to exactly 100bb before every hand, so each hand is an independent sample of the same spot. This models no session, no bankroll and no short-stack play, and no hand can show the bot busting or doubling through. That is forced rather than chosen: the committed chart answers one flat depth and refuses any other, so a run carrying stacks would put every hand after the first into the refusal path.
- The floor comparison is a floor check. Five seats that fold to any bet are not weak opponents, they are absent ones: every non-blind preflop seat faces the big blind, so all five fold before the flop unless they are in the big blind. The figure is closer to how often the chart opens than to how well it opens, and the report says so.
- 38.67 chips per hand at 50/100 is 38.7 bb/100. For calibration, a strong human wins a few big blinds per hundred hands. The size of this number is a fact about the opponents, not about the bot.

## Chip conservation and the replay cross-check

Two pieces of evidence, and the second is the one that would be hardest to fake.

**Conservation is per hand.** For every hand, the sum of stack changes across all six seats must be zero and the pot awarded must equal the pot collected. A hand that fails either stops the run rather than being averaged away. This is deliberately not an aggregate check: a run that nets to zero can hide two errors that cancel. Over 600 self-play hands the table nets exactly 0.

**Every measured hand is re-derived by somebody else.** Each dealt hand is written out in the Phase 02 normalized schema as it is played, then handed back to the frozen Phase 02 replayer, which rebuilds the whole hand from that record and compares its own settlement against the recorded result. 472 of 472 measured hands pass. Without this the simulator and the replayer would be two independent stories about the same rules with nothing forcing them to agree.

The 128 refused hands are not in that count, and that gap is the blocker below.

## The judgment calls, and what each answer changed

Seven were recorded before any code existed, all `runtime-reversible`. Taylor read items 1 and 2 at the stage 3 human gate on 2026-08-12 and confirmed both defaults, so all seven stand as written.

**1. Stacks reset every hand - `reset-every-hand`.** Not a bankroll preference. `PreflopChartStrategy` refuses a table that is not one flat stack depth, so carrying stacks would push every hand after the first into the refusal path. What it changed: the figures are chips per hand, and nothing here models a session.

**2. What the comparison compares - `both-self-play-and-floor`.** Self-play carries the mechanical criteria because symmetry gives a known expected answer to check against; the floor run carries one directional number that must come out positive. What it changed: the report has two clearly labelled halves instead of one number pretending to be a ranking.

**3. Hand count and noise - `fixed-count-with-stated-error`.** 600 hands, a hundred orbits, about a fifth of a second. Every figure prints its own standard error and no winner is named unless a figure clears two of them. What it changed: nothing yet, and that is a finding - see the non-blockers.

**4. How a refusal settles - `void-the-hand`.** Stacks restored, nothing moves, counted with its reason code. What it changed: chip conservation holds trivially for a refused hand, and the coverage figure exists at all. This is also the call a mutation canary caught unpinned: every refusal assertion in the frozen tests read "for each refused hand", which passes when no hand is refused, so converting a refusal into a fold was invisible. The repair added the anti-vacuity test that demands the run actually reach refusals.

**5. Table size and depth - `six-max-100bb-only`.** Rejected at setup with a named reason. What it changed: a misconfigured run fails immediately instead of producing 600 hands of refusals.

**6. Button rotation - `rotate-the-button`.** What it changed: the position table comes out exactly even, which is what makes a per-profile figure a property of a strategy.

**7. Dealt hands stay in memory - `in-memory-only`.** A run is a pure function of its seed and the seed is in the report, so a hand is regenerated rather than stored, and no fixture is created for later phases to be measured against. What it changed: this phase writes no committed data, which is what made it eligible to advance unattended.

## Independent review

Recorded in full at `reports/phase_audits/reviews/PHASE_07_SIMULATOR_REPORTS.md`. One mechanical blocker, seven non-blockers, no domain blocker.

**The blocker, in plain terms.** The phase's headline output does not contain the information it claims. A refused hand's record is built from the streets already filed, and a street is only filed once its betting round finishes - a refusal aborts the round part way, so nothing is filed and the record keeps only the two blind posts. Measured: those 128 hands took between two and seven real decisions each, 565 actions in total, and every record kept none of them. Because Phase 05's refusal codes name the kind of miss rather than the spot, that action sequence was the only place the identity of the refused spot survived. So the report's 21.3% is a count, and a count cannot be acted on.

The data is recoverable: the pre-refusal decision audit records kept everything, which is how the review produced the three-bet and four-bet breakdown. Connected to it, a voided record cannot be replayed at all - correctly, because the hand stops mid betting round, which means a voided hand is not a completed hand history and the real question is what a refused hand's evidence should be instead. That collides with the frozen test asserting every hand carries a `NormalizedHandHistory`, so it is a contract question rather than a patch. Filed as `SIMULATOR-VOIDED-HAND-RECORD`.

**Also caught during the phase, and worth reading as evidence about the loop.** Three of the four mutation canaries survived their first run. Two were authoring errors in the canaries: one shifted a seed deterministically, so a canary meant to prove reproducibility was itself reproducible, and one switched off a defensive assertion that never fires while the books balance. The third was correct and exposed the vacuous refusal tests described under judgment call 4. Fixing them needed the test file and the mutation list back in scope, which the freeze had deliberately removed, so it landed as its own task rather than as a reach around the freeze.

The reviewers were not delegated to read-only subagents; subagent delegation is disabled for this session, which `AGENTS.md` step 10 permits with the reason recorded. Same exception and same cost as Phase 06.

## Known limitations and deferred items

- **The refusal figure is a count and not a list.** `SIMULATOR-VOIDED-HAND-RECORD`. The blocker above. Being addressed next, together with teaching a refusal to name the spot it missed so an inventory can be keyed to a chart cell.
- **The noise rule is unexercised.** `SIMULATOR-NOISE-THRESHOLD-UNPINNED`. `separated_profiles` is only ever asked about a figure that is identically zero or one 14.9 standard errors from zero, so the case it exists for is never tested.
- **The win rate is not in the vernacular, and hand ids repeat across runs.** `SIMULATOR-REPORT-UNITS-AND-IDS`.
- **No decision audit is committed.** `SIMULATOR-DECISION-AUDIT-NOT-COMMITTED`. Every decision becomes a Phase 03 record and the set is regenerable, but nothing is written out, unlike Phase 06.
- **The floor is the only opponent that exists.** Nothing in the repo can rank the bot against a real strategy. That needs either Phase 08's player tendencies or a postflop strategy to play against, and `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK` records the cheapest opponent that could be built.
- **The gate grew.** Phase 07 adds a 600-hand run per report generation and a full test run per mutation. Recorded so nobody later reads it as a regression.

## Human sign-off

Judgment calls 1 and 2 ruled by Taylor on 2026-08-12 at the stage 3 human gate.
Remaining sign-off: read the position table in the comparison report, divide 600 by 6, and confirm every cell reads 100. That one check validates the claim that every per-profile figure is a property of a strategy rather than of a chair.
