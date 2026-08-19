# MAINT-23 - Phase 16 Is Gated On A Ruling, Not A Source

## Objective

Correct the premise phase 16 was declared under, and record the rulings it is actually gated on.

The roadmap said the only sizing source in the repo is a preflop export, so phase 16 is blocked on a source that does not exist.
GTOpen solves postflop as its primary function; the Preflop Lab that phase 10 uses is the bolt-on beside it.
The wrong claim had been quoted into `verification/loop_policy.yml` and `backlog.yml`, where it read as established rather than as an inference.

## Scope

Approved: `docs/GTOPEN_SOLVER_NOTES.md`, `docs/V2_ROADMAP.md`, `verification/loop_policy.yml`, and a new decision file under `reports/phase_audits/decisions/`.
Forbidden: every phase contract, and any implementation. No solve is run, no artifact is written, no acceptance criterion is authored. Phase 16 stays `future` and `needs_human_data`.

## Delegation Plan

- No-delegation exception: this session is instructed not to spawn subagents. The work is four document corrections and one decision record, all coordinator-owned. Self-review is in the Outcome.

## Slices

- [x] `docs/GTOPEN_SOLVER_NOTES.md` records the postflop route surface and marks it unrun, high in the file rather than at the end, because its absence is what allowed the inference.
- [x] `docs/V2_ROADMAP.md` section 16 rewritten: the correction stated as a correction, the per-street spot design, the runout fan-out, and the two open rulings.
- [x] `verification/loop_policy.yml` phase 16 reason replaced. It stays `needs_human_data: true`, because a ruling is still an input the repo does not have.
- [x] `backlog.yml` `V2-POSTFLOP-STRATEGY` reason replaced (standing scope).
- [x] `PHASE_16_POSTFLOP_BETTING_DECISIONS.md`: five judgment calls with reversibility classes and defaults.

## Verification

- `check_scope`, `check_file_sizes`, `check_contracts`, `check_repo_consistency`
- `scripts/run_verify.py` full gate
- `review_queue.py --list` still reports phase 16, now with the corrected reason

## Outcome

Phase 16's board entry now says what it is actually waiting for. Nothing else moves: the phase stays `future`, five phases downstream, and no contract is touched.

The substantive design finding, which came out of Taylor pushing back on my framing rather than out of a check: a committed postflop artifact does not have to be a joint solved tree. A spot is self-contained in its board, both ranges, pot, stacks and sizes, so the artifact can be a library of independent per-street spots keyed the way the preflop chart already is. That reframing is what makes flop-only viable and turns an unbounded phase into a bounded one.

Two things survive the reframing and both are recorded rather than resolved. Ranges do not decouple, because postflop strategy is range against range rather than a function of hero's two cards, so the preflop line has to compress into the spot key. And generation stays sequential even where storage does not, because villain's turn range is whatever he would bet and check with on the flop, which puts one flop spot at 47 turns and roughly 2,160 rivers.

### Self-review

No independent subagent review; this session cannot spawn one.

The failure worth naming is mine, not the note's. `docs/GTOPEN_SOLVER_NOTES.md` was correct: it documented what had been executed and claimed nothing about what had not. I inferred a capability limit from an absence and then stated it as fact twice. The note is edited anyway, because a document that is technically silent on the question a reader keeps asking will keep producing that reader.

The check this repo cannot perform is the one that would have caught it: nothing in the gate reads the solver, so a claim about GTOpen's capabilities is prose either way. What replaces a check here is the note's executed-versus-read line, which is why the new section states its own class in its first sentence rather than relying on the header.

Defaults chosen over alternatives, so a reviewer can attack them: flop-only over full-street, and all 1,755 flops over a subset. Both trade artifact breadth for keeping the fail-closed boundary intact, which is the trade this repo has made every time it has come up. The cost of the first is a bot that bets a flop and then goes quiet, and that is stated in decision 1 rather than left for phase 15 to discover.

## Next Agent Bootstrap

Branch `maint/postflop-source` off `main` at `86db059`, worked in `~/projects/poker-bot-worktrees/main`.
Phase 10 runs untouched in the primary worktree at loop stage 5; phase 11 is startable.
Next command: `uv run python scripts/loop_fleet.py --plan`.
