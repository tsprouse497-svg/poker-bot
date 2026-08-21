# Phase 11 audit packet: Engine And Query Fidelity

Contract: `docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`
Decisions: `reports/phase_audits/decisions/PHASE_11_ENGINE_FIDELITY_DECISIONS.md`
Reviews: `reports/phase_audits/reviews/PHASE_11_ENGINE_FIDELITY/`
Report: `reports/active/latest_engine_fidelity_report.txt`
Lane: branch `phase/11-engine-and-query-fidelity`, opened from `main` at `1b8314c`.

## What changed, in plain language

Six defects. Every one was found by v1's own reviews, diagnosed, and filed in
`backlog.yml`, and none could be fixed inside the phase that found it. All six sit
underneath a later measurement, which is why they are closed before anything derives a
chart from the solver export or re-measures agreement against real hands.

**A fold is now legal wherever a seat may act.** The engine used to offer only a check and
aggression when there was nothing to call, so applying a fold raised an error. Folding for
nothing is a bad play and a legal one, and treating it as illegal meant no real history
containing a surrendered river or a timed-out check would replay at all - which is what
blocked ingesting anybody's actual hands. Legal is not the same as chosen: no strategy in
this repo folds when checking is free, and that is proved rather than asserted, over the
postflop enumeration, the reference strategy, and the one committed chart spot where
checking is free.

**Betting now reopens when short all-ins add up to a full raise.** If a player moves all-in
for less than a full raise, the players who already acted may call or fold but not raise -
that was right and it stays. What was wrong is that each all-in was measured against the bet
level immediately before it, so two short all-ins that *together* made a full raise still
left betting closed. A real room reopens it. The measurement is now against the last full
bet or raise, and a full bet or raise resets the level it is measured from.

**`StrategyQuery.street_bet` now says which of two things it means.** It is the street's
current bet level, not hero's own contribution to it. Nothing in the repo said so, and one
report generator passed the other reading, so replayed hands reached the chart with a
mis-derived stack depth and refused for the wrong reason. The meaning is now on the field, a
query whose `street_bet` is below its `to_call` is rejected, and the one wrong producer is
corrected.

> Pointer added 2026-08-21 by Phase 13. The field described above no longer exists under that
> name. Phase 13 renamed it to `StrategyQuery.current_bet` and put the engine's `street_bet` -
> one seat's own share of the level - on the new per-seat `seat_states` record, which is what
> made one name carrying two readings unaffordable. This packet keeps the name it shipped with,
> because it is dated evidence of what this phase did rather than a document tracking the
> current tree; see `reports/phase_audits/PHASE_13_TABLE_STATE.md`. The corollary this phase's
> contract drew from the field - that hero's contribution is recoverable as `street_bet` minus
> `to_call` - was withdrawn by MAINT-21 and is false under the capped `to_call` ruling of
> 2026-08-20.

**The decision audit's all-in ceiling is now what hero can actually raise to.** It was the
street's bet level plus hero's stack, which is too high by exactly the price to call: with a
street bet of 20, a price to call of 20 and a stack of 100, it accepted a raise to 120 and
only rejected 121. Hero's real all-in target there is 100. No shipped strategy ever produced
a raise in the gap, so nothing changes in play; what changes is that the legality claim
several phase contracts lean on is now true.

**The postflop fallback's fail-closed branch no longer invests.** It is reached when the
action the rules chose is not on offer, and it used to take the most passive available
action from fold-then-call. Where fold was absent that is a call, so a branch reached
because something unexpected happened answered by putting chips in on a hand it had not
established could not lose. It now folds when folding is legal and refuses otherwise.

**The command registry no longer advertises a check that does not exist.** The
`check_solver_export_expectations` entry said the command recomputes the export's orderings
and directional bound. The directional bound was withdrawn on 2026-08-18 with the parity
solve, and the command never computed it.

## Pass/fail checklist for a non-coding reviewer

Everything here is checkable from `reports/active/latest_engine_fidelity_report.txt` and
this document. No code needs reading.

| # | Check | Where to look | Result |
|---|---|---|---|
| 1 | A seat with nothing to call is offered a fold | report, section 1, "Now" line | PASS - `fold, check, bet` |
| 2 | Folding for free costs nothing and leaves the pot alone | report, section 1, worked example | PASS - 0 committed, bet level and minimum raise unchanged |
| 3 | No strategy in this repo folds when checking is free | report, section 1, the five lines under "Legal is not chosen" | PASS - three checks, and the one free chart spot folds 0.00% |
| 4 | Two short all-ins that reach a full raise reopen betting | report, section 2, the table | PASS - `no` at 19, `yes` at 20 and above |
| 5 | A short all-in that does not reach it still does not reopen | same table, the 19 row | PASS |
| 6 | A street opened by a short all-in measures from the street's opening level | report, section 2, the paragraph after the table | PASS - seat 1 is offered `fold, call, raise` |
| 7 | Reopening restores the right to raise, not a cheaper price | report, section 2, the sentence after the short-all-in case | PASS - smallest legal raise is to 31, not 22 |
| 8 | A barred seat can still call and fold | report, section 2, last line | PASS - `fold, call` |
| 9 | The two readings of `street_bet` give different chart answers, and the new one is the true miss | report, section 3, worked example | PASS - table-size miss, not blind-structure |
| 10 | A query that contradicts the documented meaning is rejected | report, section 3, "The guard" | PASS |
| 11 | The all-in ceiling accepts 100 and rejects 120 | report, section 4 | PASS |
| 12 | The fail-closed branch never calls | report, section 5, the three rows | PASS - fold, refused, refused |
| 13 | The registry entry names no withdrawn check | report, section 6, "Now" line | PASS |
| 14 | Every fix has a test that fails without it | the table under "Evidence, per defect" below | PASS - six of six |
| 15 | The full gate passes | `reports/active/latest_verify.txt` | PASS - 41 commands |
| 16 | The gate is not decorative | `check_gate_bite` in the same file; the five canary entries naming `pytest_engine_fidelity` are in `verification/mutations.yml` | PASS - the command fails under every one of them, which is what `check_gate_bite` requires to pass |

## Evidence, per defect

Each fix is pinned by a test that fails against the behaviour on `main` at `1b8314c`, and
by a test that the correction is not over-applied. Twenty-eight of the forty-nine tests
frozen at stage 5 were red before any implementation existed, on assertions rather than on
an import error, which the loop's stage 4 check enforced. The file now holds fifty-two: one
test was added at stage 6 repairing an authoring error and two at stage 8 pinning the
blocker that stage found.

| Defect | Fails without the fix | Guards over-application |
|---|---|---|
| `FOLD-WHEN-FREE` | `test_a_free_spot_offers_fold`, `TestReplayAcceptsARecordedFreeFold` (4 tests) | `test_check_stays_legal_exactly_when_the_price_to_call_is_zero`, `test_facing_a_bet_offers_the_same_set_it_always_did` |
| `UNDER-RAISE-ACCUMULATION` | `test_two_short_all_ins_past_the_bar_reopen_betting`, `test_exactly_at_the_bar_reopens`, `test_three_short_all_ins_accumulate`, `test_an_under_sized_all_in_bet_is_not_the_level_advances_are_measured_from` | `test_one_chip_below_the_bar_does_not_reopen`, `test_a_single_short_all_in_still_does_not_reopen`, `test_a_full_bet_does_become_the_level_advances_are_measured_from` |
| `STREET-BET-MEANING-AMBIGUOUS` | `test_the_query_documents_which_reading_it_carries`, `test_a_current_bet_below_the_price_to_call_is_rejected`, `test_the_query_report_generator_writes_the_street_level` | `test_a_current_bet_equal_to_the_price_to_call_is_accepted` |
| `DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE` | `test_a_raise_above_the_corrected_ceiling_is_rejected`, `test_the_old_ceiling_is_no_longer_the_boundary` | `test_a_raise_exactly_at_the_corrected_target_is_accepted`, `test_every_committed_decision_audit_record_still_validates` |
| `FALLBACK-FAIL-CLOSED-CAN-CALL` | `test_a_set_offering_call_but_not_fold_refuses_rather_than_investing` | `test_the_unbeatable_call_is_untouched`, `test_a_preflop_query_still_refuses` |
| `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK` | `test_the_expectations_command_names_no_directional_bound` | `test_every_command_still_carries_a_description` |

Five mutation canaries make the phase's own gate command bite: four authored at stage 4
against text the implementation did not yet contain, and one added at stage 8 for the
blocker that stage found. All five apply and all five make `pytest_engine_fidelity` fail.

## The reopening worked example, in chips

Four seats. Seat 0 bets 10, which sets the bet level to 10 and the minimum raise to 10.
Seat 1 is all-in for 15 - five over the bet, half a raise - and seat 0 is correctly barred
from raising. Seat 2 is then all-in for the amount in the first column.

| Seat 2 all-in to | Advance since the last full raise (10) | May seat 0 raise? |
|---|---|---|
| 19 | 9 | no |
| 20 | 10 | yes |
| 21 | 11 | yes |
| 30 | 20 | yes |

The bar is the minimum raise of 10, so the level has to reach 20. Reopening gives seat 0
the right to raise and not a cheaper price for it: with the level at 21 and the minimum
raise still 10, seat 0's smallest legal raise is to 31.

Separately, a street that *opens* with a short all-in has had no full bet on it, so the
reference stays where the street opened. Minimum bet 20, seat 0 all-in for 5, seat 1 calls,
seat 2 all-in for 22: the street has advanced 22 from nothing, which is past a full bet, so
seat 1 may raise.

## The number a reader can recompute by hand

**20.** The level at which betting reopens in the table above. The last full bet set the
level to 10 and the minimum raise to 10, and betting reopens once the level has advanced by
a full raise since that bet - so at 10 plus 10. Every row of the table is that one
subtraction and that one comparison; no code is involved in checking it. The report prints
the same table with the subtraction in its own column.

## Upstream contract amendments

Two completed contracts stated behaviour this phase deliberately changed, and both were
amended in `contract-update` mode before any test was frozen against them.

| Contract | Criterion it replaced | What it now says |
|---|---|---|
| Phase 03 | "a reopening rule where an all-in raise below the minimum does not reopen raising for seats that already acted" | The same, plus: the test is against the last full bet or raise, so consecutive short all-ins whose increments together reach the minimum raise do reopen, and a full bet or raise resets the level |
| Phase 06 | "It never refuses postflop, never raises an exception, and never returns nothing." | The same, restated as what its enumeration proves: it never refuses from a legal-action set the engine can produce. A contract-valid query carrying `("raise",)` does get a refusal, and the fail-closed branch folds or refuses and never calls |

`docs/V2_ROADMAP.md` also expected this phase to touch the Phase 01 and Phase 02 contracts.
It could not: both carry only boilerplate criteria under the `CONTRACT-CRITERIA-BACKFILL`
exemption, so they contradict nothing, and backfilling them is not this phase's work. Read
and left alone.

## The producer audit

Every `StrategyQuery` producer in the repo was read against the documented meaning of
`street_bet`. The prose list is the record; the mechanical half is that each one is reached
by a gate command that builds real queries, so the new guard runs against all of them on
every gate.

| File | Passes | Verdict |
|---|---|---|
| `src/poker_training_bot/data_pipeline/comparison.py` | `state.current_bet` | correct |
| `src/poker_training_bot/simulator/table.py` | `state.current_bet`, with a comment already naming the meaning | correct |
| `scripts/generate_postflop_fallback_report.py` (two sites) | `state.current_bet` and `shape.current_bet` | correct |
| `scripts/generate_preflop_strategy_report.py` | the big blind, which is the preflop level, and `2 x` it for the straddle probe | correct |
| `scripts/generate_strategy_query_report.py` | `player.street_bet` | **wrong, corrected** |
| `scripts/generate_engine_fidelity_report.py` | levels, this phase's own | correct |

## The registry sweep

Every entry in `COMMANDS` was read against what its script does. One mismatch, the one filed
as `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK`, now corrected. No second mismatch was
found. The nearest thing to one is `pytest`, described as "Run tests", which is accurate and
uninformative rather than wrong.

## Committed numbers these fixes move, and who re-measures them

By decision 9, this phase names them and recomputes none of them: a fix phase that grades
its own fixes puts a moved number and a mistaken one in the same commit.

| What | Why it moves | Who owns the re-measurement |
|---|---|---|
| `latest_decision_audit.jsonl` | `street_bet` changes on every preflop record where hero had not matched the level | regenerated by its own gate command; no finding rests on the raw bytes |
| Phase 08 agreement rates | measured through the uncorrected query and replayer | proposed phase 12 |
| Phase 08 refusal inventory | the same | proposed phase 12 |
| Phase 07 simulator counts | replayed through the old reopening rule | proposed phase 12 |

**Measured, and worth more than the list above.** With all six fixes in,
`reports/active/latest_sample_comparison_report.txt` is byte-identical to the version on
`main`. Not one of the 3,048 corpus decisions moves. The honest reading is not that the fixes
changed nothing - each has a test that fails without it - but that neither the free fold nor
the all-in chain occurs in **the 499 hands this repo committed**.

That is close to proof for those 499 and it is not a claim about Pluribus play. The sample
carries exactly one recorded exclusion, and it is for fractional chips, so a hand containing
either spot would have failed replay under the old rules and appeared as an exclusion of its
own. What was never done is counting either spot across the full 10,000-hand subset, which
needs the corpus clone and is not in this repo. Both spots occur in real-room hands, which is
the case this phase was closed for; how often they occur in this dataset is unmeasured.

## Judgment calls and what each one changed

Nine calls, every one `runtime-reversible`, which is right because the phase commits no
data. `verification/loop_policy.yml` grants it `auto_advance: true` on that ground, and the
stage-1 review killed the one draft criterion that would have made it false.

| # | Call | Answer | What it changed |
|---|---|---|---|
| 1 | Where a free fold becomes legal | `legal-actions-everywhere` | One definition of legality instead of two. Cost: every strategy now sees `fold` in free spots |
| 2 | What stops a strategy taking it | `prove-it-by-enumeration` | No guard written. The proof passed, including on the committed chart |
| 3 | How far betting reopens | `accumulate-since-the-last-full-raise` | The rule cardrooms use. **The one call worth a human's eyes**, and the loop does not stop for it |
| 4 | Document `street_bet` or rename it | `document-and-guard` | The name stays and reads wrong; filed as `STRATEGY-QUERY-STREET-BET-NAME` |
| 5 | Grandfather the old ceiling | `tighten-and-assert-nothing-breaks` | Nothing to grandfather; every committed audit record still validates |
| 6 | What the fail-closed branch does | `fold-then-refuse` | Never calls |
| 7 | Phase 06's refusal claim | `restate-as-from-engine-legal-sets` | Contract text only |
| 8 | Amend upstream contracts here | `amend-in-this-phase` | Two amendments, above |
| 9 | The numbers these fixes move | `name-and-defer` | Named, not recomputed; filed as `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` |

**Decision 3 in one sentence a poker player can answer without reading code:** in a real
room, when two players move all-in for short amounts one after the other and their two
increments together add up to a full raise, does the player who already acted get to raise
again? This phase says yes. If the answer is no, decision 3 flips to
`keep-the-current-strict-rule`, the backlog entry is restated as a deliberate difference
rather than a defect, and nothing else in this phase changes.

## Review findings

No subagent review ran: subagents are unavailable in this operator's sessions, and the
standing instruction is not to call the Agent tool unless it is requested. `AGENTS.md` step
10's self-review fallback applies, and the ExecPlan records it as the no-delegation
exception. Every stage that produced a diff was reviewed as a separate read-only pass, and
stage 8 was written as two passes with the mechanical and domain questions kept apart.

Blockers found and resolved, by stage:

- **Stage 0** - none.
- **Stage 1** - three. A criterion required a committed hand fixture, which would have
  revoked the phase's own `auto_advance` permission; two criteria pointed opposite ways
  about whether a validator could be removed; a third was satisfiable by writing a list.
- **Stage 2** - none, but two stage-1 criteria were corrected here because the measurements
  contradicted them. The `street_bet` guard misses a hero who has contributed exactly half
  the level, which is the heads-up small blind and therefore the exact case that motivated
  it; and the strategy query report has no refusals to change, because it runs the reference
  check-fold strategy.
- **Stage 4** - five weak tests, found before the freeze could preserve them. One asserted on
  a generator's source text rather than on what it wrote. One recomputed the ceiling it was
  checking, which is the defect MAINT-07 found in the settlement oracle. One asserted only a
  negative. Three asserted truthiness on an amount. Four built malformed fixtures.
- **Stage 6** - ten frozen tests failing with no implementation defect among them, repaired
  in their own task with the builder files out of scope. One of the three authoring errors
  was wrong about the poker: it asserted that a short all-in bars the seat whose raising
  right an earlier full raise had just restored.
- **Stage 7** - a comparison report committed from a run that happened while
  `check_gate_bite` held `comparison.py` mutated, swept in by a `git add -A`.
- **Stage 8** - the reopening reference was set from an under-sized all-in *bet*, which is a
  legal bet and not a full one. Found by asking what happens when a street *opens* with a
  short all-in rather than when one interrupts an established bet.

## Known limitations and deferred items

- **The reopening rule has no oracle in this repo.** No rulebook is checked in and the
  corpus is not consulted for rules. The only check on it is a person who knows how a room
  rules the spot, which is why it is written in chips above.
- **`street_bet` still reads as the opposite of what it holds.** The docstring and the guard
  are mitigations, not a fix, and the guard misses the heads-up small blind by construction.
  `STRATEGY-QUERY-STREET-BET-NAME`, proposed phase 13.
- **Every published measurement in this repo was taken through the instrument this phase
  corrected, and none is re-taken here.** `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT`,
  proposed phase 12.
- **An under-sized all-in bet still clears the no-raise set**, so seats that already checked
  keep a right cardrooms take away. No phase 11 criterion names it, and fixing it would be
  behaviour nobody asked for. `UNDER-SIZED-ALL-IN-BET-DOES-NOT-BAR-PRIOR-CHECKERS`,
  contract-update.
- **The raise bar over an under-sized all-in bet is measured from the all-in amount.** On a
  street whose minimum bet is 20, after an all-in bet of 5, the engine demands a raise to 25
  and rejects 20; most rooms allow 20, because an incomplete bet does not set the raise
  increment. This phase edited the same branch and did not file it, which is the finding as
  much as the behaviour is. `MIN-RAISE-OVER-AN-INCOMPLETE-ALL-IN-BET`, contract-update.
- **The decision-audit schema version stayed at 1** although one producer's `street_bet`
  values changed, so nothing on an audit line says which reading wrote it. The field's name
  and type did not change, so this is defensible rather than obviously right, and it was
  treated as obvious. `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS`, contract-update.
- **Nine of the assumptions this phase rests on were recorded only in review notes or code
  comments, never as judgment calls**, so they never reached the human gate. The reopening
  rule's price is the one that matters most: the ruling covers who may raise, not what the
  raise must cost. The full inventory is the reason the two items above are filed at all.
- **`TurnState.reopen_level` carries a default of 0.** The correct initial value is the
  street's opening bet level, which both factory methods set; a required field would break
  callers that construct a `TurnState` directly. A hand-built one measures from zero.
- **A report generated during a live mutation is committable.** The sentinel and
  `check_scope` stop a mutated *source file* being committed; nothing stops the *report a
  mutated run wrote*. `MUTATION-SENTINEL-IS-COMMITTABLE`, contract-update.
- **The free-fold replay hand goes to an uncontested settlement**, not a showdown, because
  it is a two-handed hand built inside the test. The engine path is the same either way.

## Command summary

Run `uv run python scripts/run_verify.py`. 41 commands, all passing, recorded in
`reports/active/latest_verify.txt` and `reports/active/verify_results.json`.

This phase's own commands:

| Command ID | What it does | Output |
|---|---|---|
| `pytest_engine_fidelity` | Runs the phase's tests | - |
| `generate_engine_fidelity_report` | Writes the before/after report | `reports/active/latest_engine_fidelity_report.txt` |
