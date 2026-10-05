# MAINT-45: Narrow The Yardstick

- **Task** `MAINT-45`
- **Mode** `contract-update`
- **Branch** `maint/45-narrow-the-yardstick`, worktree `~/projects/poker-bot-worktrees/maint-45`
- **Base** `22280ec`, which is `main` after MAINT-44
- **Authorised by** Taylor, 2026-10-05 in this session

## Objective

Phase 18's skeleton contract promised an opponent pool, a head-to-head win rate and an exploitability
figure. Taylor asked whether that still made sense after ruling to trust the solve, and was offered
three options: keep it narrower, retire it, or keep it as written. He chose the first. Re-scoping a
declared phase is a semantic contract change, so this runs in `contract-update`. Phase 18 has not
started, so the ruling lands in its skeleton for stage 1 to build on, the way MAINT-43 and MAINT-44
recorded phase 22's rulings.

## Taylor's rulings

1. **Phase 18 stays, narrower.** Offered as "Keep it, but narrower (my recommendation). Drop anything
   that second-guesses the solver, and measure only what the bot's departures from solver play cost,
   in chips." He answered "1".

## Coordinator's reading, not a ruling

- The departures listed today: refused spots and the check-fold behind them, off-size opens answered
  from the 2.5bb cell, and bets matched to the nearest menu size; later, phase 19's rules of thumb.
- The skeleton's exploitability figure is dropped, because over the bot's whole strategy it charges
  the solve's own convergence gap to the bot.
- The lean that the solve is also the opponent is stated as a lean; whether other opponents are
  needed is left to stage 1 and the human gate.
- `THE-LADDER-INVERSIONS-WERE-ACCEPTED-AS-A-TEACHING-COST-AND-NOTHING-HAS-PRICED-THEM-IN-CHIPS` is
  read as no longer phase 18's to price, and left for its stage 1 to close.

All four are `runtime-reversible` in the loop's sense: they are text in a skeleton that phase 18's own
stage 1 rewrites, and nothing is committed into data.

## Scope

Approved: phase 18's contract, both roadmaps, `verification/loop_policy.yml`, and this task's packet
and review directory; `backlog.yml` through standing scope. Phase 19's dependency on 18 is unchanged.
Nothing under `data/`, `src/`, `tests/` or `scripts/` changes.

## Delegation Plan

- No-delegation exception: the edits transcribe one ruling into four documents that must agree, and
  a lane would be writing down what the coordinator told it.
- Review handoff: one read-only reviewer that wrote none of this checks that the ruling is stated
  faithfully and no further than Taylor went; that the coordinator's readings are marked as such;
  that every live document on `main` describing phase 18 agrees; that the listed departures exist in
  the repo; and that phase 19's reason for waiting on 18 still holds. Asked also what it held back.
  No gate runs: the machine is shared.

## Slices

- [x] Activate MAINT-45 with a dated scope entry.
- [x] Record the ruling in phase 18's contract, both roadmaps, the loop-policy reason and one backlog
  entry.
- [ ] Independent read-only review.
- [ ] Gate, packet, closeout to idle, gate again, merge, push.

## Verification

`uv run python scripts/run_verify.py`, sequenced with the other lanes on this machine, read for its
verdict rather than its exit code.

## Outcome

Not yet.

## Next Agent Bootstrap

Worktree `~/projects/poker-bot-worktrees/maint-45`. Next: the independent review, then the gate.
