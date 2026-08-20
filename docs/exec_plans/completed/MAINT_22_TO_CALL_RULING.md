# MAINT-22: Taylor's `to_call` ruling, and the amendment-size rule

Task: `to-call-ruling-and-amendment-rule`. Mode: `contract-update`. Base: `f45d11d`.

## Objective

Two rulings arrived on 2026-08-20, both in response to the phase 10/11 review:

1. **`to_call` is what hero would actually pay**, capped at hero's remaining stack.
2. **The contract line cap is answered by capping the amendment, not the file.**

Record both, and record what the first one turns out to settle and not settle. No behaviour
changes here: the implementation of ruling 1 belongs to proposed phase 13.

## Why one task and not two

Ruling 2's rule lands in `AGENTS.md`, which is process documentation rather than implementation,
so a `contract-update` task carrying it breaks no mode rule - the mode's constraint is on mixing
contract edits with unrelated *implementation*. They are also not unrelated: the rule being
stated governs contract amendments, and recording ruling 1 in Phase 11's contract is its first
application. Splitting them would land the rule unexercised and the amendment ungoverned.
Recorded here so a reviewer can disagree on the record rather than find it buried.

## What ruling 1 settles, which is more than expected

The review recommended the opposite reading, so the consequences were re-derived from scratch
against the branch rather than assumed. Measured, not argued:

- **A capped hero can never raise.** `BettingRoundState.legal_actions` offers `raise` only when
  hero's stack exceeds the price owed. Probed: the short seat facing a level of 100 with 15
  behind is offered `('fold', 'call')` and nothing else.
- **So the all-in ceiling becomes sound under this ruling.** `(street_bet - to_call) + stack` is
  only ever applied to a hero who is *not* capped, and for an uncapped hero `street_bet` minus
  `to_call` really is hero's contribution. No new arithmetic is needed - which is the opposite
  of what the review concluded, and the ruling is better than the recommendation on this point.
- **The guard that makes it sound does not exist yet.** `StrategyQuery` must reject a query
  offering `raise` when `to_call` equals `stacks[seat]`. Probed: today such a query validates
  fine, and it is the only route by which the ceiling accepts a raise hero cannot make.
- **The two capped records in `latest_decision_audit.jsonl` are correct** under the ruling and
  need no repair.

## What ruling 1 does not settle

- `PreflopChartStrategy._table_depth_bb` still derives depth as
  `stacks[seat] + (street_bet - to_call)`, and a capped hero can still call or fold, so the chart
  is still consulted. Probed: 30 bb derived where the truth is 25 bb, no refusal, no signal.
  Hero's own contribution still has to become its own field. Phase 14 publishes through this path.
- Phase 06's enumeration describes its short hero as `0 < stack < to_call`, which the ruling makes
  inexpressible. The *situation* survives; its encoding becomes `to_call == stack`. Phase 06's
  contract needs that restated when the ruling is implemented, not now.

## Scope

Approved: `docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`, `AGENTS.md`.

Standing: `CURRENT_TASK.yml`, `backlog.yml`, `docs/BACKLOG.md`, `docs/exec_plans/**`,
`reports/active/**`.

Deliberately untouched: every producer and consumer of `to_call`, `StrategyQuery`, the chart, the
Phase 06 contract, and `tests/**`. Ruling 1 is recorded, not implemented.

## Delegation Plan

- No-delegation exception: subagents are unavailable in this operator's sessions - the standing
  instruction is not to call the Agent tool unless requested - so `AGENTS.md` step 10's
  self-review fallback applies, recorded here and in the review section below.

## Slices

- [x] Slice 1: `AGENTS.md` gains a `Contract Amendments` section stating the two-line rule, the
  rewrite escape hatch, and the prohibition on raising the cap. 132 lines against a 150 cap.
- [x] Slice 2: Phase 11's existing three-line amendment note is rewritten in place to carry the
  ruling, adding no lines. The contract is still at exactly 300 and still amendable, which is the
  rule demonstrating itself.
- [x] Slice 3: `backlog.yml` - `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS` restated under the
  ruling with the derived consequences above, and `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT`
  marked `done` with what resolved it.
- [x] Slice 4: read-only self-review, then the gate.

## Verification

`uv run python scripts/run_verify.py` - full derived gate, 41 commands, no new command IDs. No
behaviour changes, so every report a gate command regenerates must be unchanged apart from the
gate's own records and `docs/BACKLOG.md`.

## Read-only self-review

Reviewer: coordinator, self-review, per the no-delegation exception.

Question asked: does the record now say what was ruled, and does it avoid claiming the ruling
fixed things it did not?

- **No blocker.**
- The backlog entry leads with the ruling and separates settles-this from does-not-settle-this,
  which matters because the ruling closes one of the two consequences outright and leaves the
  other exactly where it was. An entry that only said "ruled: capped" would have read as though
  both were closed.
- The entry names the missing guard as the thing that makes the ruling sound. That is the one
  piece of new work the ruling creates, and it would have been easy to lose, because the ceiling
  arithmetic needs no change and the temptation is to file the whole item as smaller than it is.
- The review's own recommendation was the other reading. It was re-derived rather than defended:
  the ruling turns out to be better on the ceiling, and no worse on the chart. Recorded that way
  rather than as a concession.
- `AGENTS.md` gained 10 lines against a 150-line cap, leaving 18. Worth noticing that the file
  stating the rule about caps is itself capped, and is now closer to its own limit. Not filed -
  18 lines is not a live constraint, and filing every cap that exists would be noise.
- One thing a reader should check rather than take on trust: the claim that a capped hero can
  never be offered `raise` rests on `BettingRoundState.legal_actions` computing its own `to_call`
  uncapped, from the engine's state, independent of whatever a query later carries. If a future
  phase changes the engine to consult a capped figure, the ceiling silently loosens again. That
  coupling is worth a test when phase 13 implements the ruling.

## Alignment

- `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS` (phase 13) - restated under the ruling; the guard and
  the contributed-chips field are the work.
- `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT` (contract-update) - closed by this task.

## Outcome

Both rulings are on the record and neither changed behaviour. Phase 11's contract carries the
`to_call` ruling inside its existing note and is still at 300 lines, so the next amendment to it
is possible under the new rule where it would previously have failed the gate. Gate green across
41 commands.

## Next Agent Bootstrap

Repo is on `main` in `~/projects/poker-bot-worktrees/main`, idle after this task closes. The open
work from ruling 1 is phase 13's: document `to_call` as the capped price, add the
`raise`-implies-`stack > to_call` guard to `StrategyQuery`, bring the three uncapped producers
over, carry hero's own street contribution as its own field so the chart stops subtracting, and
restate Phase 06's short-hero shape as `to_call == stack`. Do not start it outside phase 13's own
stage 1.
