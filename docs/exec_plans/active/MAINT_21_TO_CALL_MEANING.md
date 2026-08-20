# MAINT-21: `to_call` has two readings, and Phase 11's contract says otherwise

Task: `to-call-meaning-contract`. Mode: `contract-update`. Base: `7dc2902`.

## Objective

Phase 11 closed `STREET-BET-MEANING-AMBIGUOUS` by documenting `StrategyQuery.street_bet` as
the street's current bet level, and wrote a corollary into its own acceptance criteria:

> hero's own contribution to the street is recoverable as `street_bet` minus `to_call`

That corollary is false, because `to_call` carries the same two readings `street_bet` did and
nothing in the repo says which is meant.
Two producers pass the price to call as the level owed; two pass it capped at hero's remaining
stack.
Under the capped reading `street_bet - to_call` is not hero's contribution, and two consumers
derive real answers from it.

This task corrects the contract only.
It does not rule which reading is right, does not touch the query, the producers, the ceiling
or the chart, and does not write criteria for the phase that will.
Picking the reading is a design ruling with a human gate, exactly as
`MIN-RAISE-OVER-AN-INCOMPLETE-ALL-IN-BET` was filed to be.

## Why Phase 11's contract and no other

`grep -n to_call docs/phase_contracts/*.md` returns exactly one file.
No other contract makes any claim about the field, so no other contract is contradicted -
Phase 03 owns `StrategyQuery` but never stated what `to_call` means, which is "made no claim"
rather than "made a wrong claim", and Phase 11's own rule leaves those alone.
Phase 13's skeleton is the right home for the *fix* (its proposal is per-seat committed chips
through the query, which is precisely a first-class contributed-chips field), but its criteria
are written by its own stage 1 in `contract-update` mode.
Writing them here would take that phase's decision away from it, which is the rule Phase 11
stated about the spot key and applied to itself.

## Evidence the corollary is false

Five `StrategyQuery` production sites, two readings, and both live inside one file:

| Site | `to_call` | Reading |
|---|---|---|
| `simulator/table.py:159` | `max(0, current_bet - street_bet)` | the level owed |
| `data_pipeline/comparison.py:334` | `max(0, current_bet - street_bet)` | the level owed |
| `generate_postflop_fallback_report.py:335` | `shape.to_call`, uncapped | the level owed |
| `generate_postflop_fallback_report.py:675` | `min(..., player.stack)` | what hero can afford |
| `generate_strategy_query_report.py:45` | `min(..., player.stack)` | what hero can afford |

Phase 06's enumeration depends on the uncapped reading: its `hero_is_short` shape is
`0 < hero_stack < to_call`, a state the capped sites can never produce, and Phase 06's contract
names that hero explicitly.
So the two readings are not one producer being sloppy - each is deliberate and neither is
written down.

Measured consequences, both on the committed tree:

- `DecisionAuditRecord`'s corrected ceiling `(street_bet - to_call) + stack` reopens under the
  capped reading. A hero holding 15 who has contributed nothing to a level of 100 gets a
  ceiling of 100. Two of the eleven records in `reports/active/latest_decision_audit.jsonl`
  are that shape (`phase02-three-way-side-pot`, seats 0 and 1, ceilings 4.4x and 2.2x loose).
  `test_every_committed_decision_audit_record_still_validates` passes over them because the
  reference strategy folds, so the ceiling branch never runs.
- `PreflopChartStrategy._table_depth_bb` uses the same identity. A hero with 150 behind who has
  posted 100 into a level of 300 derives as 25 bb from an uncapped producer and 30 bb from a
  capped one, with no refusal and no signal.

## Scope

Approved: `docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`.

Standing: `CURRENT_TASK.yml`, `backlog.yml`, `docs/BACKLOG.md`, `docs/exec_plans/**`,
`reports/active/**`.

Forbidden here, and deliberately so: `src/poker_training_bot/strategy/contract.py` (the
docstring repeats the corollary and is corrected by whoever fixes the behaviour, in
implementation mode), the two capped producers, `preflop_chart.py`, `tests/**`, and every other
phase contract.

## Delegation Plan

- No-delegation exception: subagents are unavailable in this operator's sessions - the standing
  instruction is not to call the Agent tool unless it is requested - so `AGENTS.md` step 10's
  self-review fallback applies. The review below is a read-only self-review pass recorded as
  such.

## Slices

- [x] Slice 1: amend Phase 11's contract. The false clause is struck from the `street_bet`
  criterion and replaced by a three-line `Amended by MAINT-21` note pointing at the backlog id.
  Retraction only - no requirement is added that nothing satisfies, because a completed
  contract asserting an unimplemented criterion is the same drift in the other direction.
- [x] Slice 2: file `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS` against phase 13, and
  `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT` against contract-update; regenerate
  `docs/BACKLOG.md`.
- [x] Slice 3: read-only self-review, then the gate.

## The amendment came out smaller than planned, and why

The plan called for three amendment notes, one per affected criterion. The contract was 298
lines against a 300-line cap in `check_file_sizes`, and three notes took it to 320, which
failed the gate.

Rather than widen the cap - the shortcut this repo forbids - or delete rationale a completed
phase wrote, the correction was compressed into one note on the criterion that carries the
false clause, and the diagnosis moved into the backlog entry where there is no cap. The two
consequences the other notes would have carried, the reopened ceiling and the mis-derived chart
depth, are named in that one note and documented in full in `backlog.yml`.

The cap itself is now a live constraint on Phase 11's contract, which sits at exactly 300, so
the next amendment to it halts. Filed as `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT`.

## Read-only self-review

Reviewer: coordinator, self-review. Subagents are unavailable in this operator's sessions, per
the no-delegation exception above.

Question asked: does this task change anything it was not opened to change, and does the
amended contract now say something true?

- **No blocker.**
- The diff touches one contract file, `backlog.yml`, its generated doc, `CURRENT_TASK.yml`, and
  this plan. No source, no test, no fixture, no report the gate regenerates. `check_scope`
  agrees.
- The amendment retracts and does not require. It states that a clause is struck, why it is
  false, and where the diagnosis lives. Nothing in it obliges code that does not exist, which
  is the failure mode an eager contract-update has.
- The reading is deliberately not ruled. Both capped and uncapped are defensible - Phase 06's
  enumeration needs uncapped for `hero_is_short`, and a strategy deciding whether to call is
  better served by what hero can afford - so picking one here would settle a design question
  behind a human's back. Same shape as `MIN-RAISE-OVER-AN-INCOMPLETE-ALL-IN-BET`, filed the
  same way.
- One thing worth a reader's attention: the struck clause is *quoted* in the amendment rather
  than left in place, so the contract no longer asserts it anywhere while still recording that
  it was asserted. That is the only way to keep both the correction and the history inside a
  capped file.

## Alignment

- `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS` (phase 13) - the defect itself.
- `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT` (contract-update) - found by paying it.

## Verification

`uv run python scripts/run_verify.py` - full derived gate, 41 commands. No new command IDs.
No behaviour changes, so every existing report must be byte-identical apart from the gate
records themselves and the regenerated backlog doc.

## Outcome

Phase 11's contract no longer asserts that hero's own contribution is recoverable from
`street_bet` and `to_call`. The defect that clause papered over is filed against phase 13 with
its measured consequences, and the fix is left to the phase whose stated scope is per-seat
committed chips through the query. No behaviour changed and no measurement moved: the gate is
green across 41 commands and every report a gate command regenerates is unchanged apart from
the gate's own records and `docs/BACKLOG.md`.

## Next Agent Bootstrap

If this task is interrupted: the repo is on `main` in
`~/projects/poker-bot-worktrees/main` at base `7dc2902`, mode `contract-update`, approved scope
one contract file. Finish the slices above, run the gate, commit, move this plan to
`docs/exec_plans/completed/`, reset `CURRENT_TASK.yml` to idle, then run the gate again and
commit the closeout. Do not implement the fix - it is filed for phase 13 and needs a ruling
first.
