# MAINT-26: What A Real Postflop Solve Costs

## Objective

Measure what one postflop solve actually costs, and record it as a cost model rather than as a
verdict.

`docs/GTOPEN_SOLVER_NOTES.md` carries an unverified list whose first entry reads "Only 300
iterations were run and no timing was recorded. Measure a real solve before planning around it."
Every count phase 16 is planned against rests on that gap. The decision record says so in its own
words: the turn is about 49 times a flop and the river about 2,350 times, *whatever a flop turns
out to cost*. Flop-only, all 1,755 canonical flops over GTOpen's 47-flop study subset, and how
many preflop lines get covered are three decisions taken against a number nobody has.

This task is not phase 16 and does not start it. It commits no chart data, moves no phase status,
adds no gate command, and leaves the bot playing exactly the chart it plays today. It is the same
shape `docs/V2_ROADMAP.md` used when it carved the solver extraction out ahead of the chart
cutover: verify the expensive input early, with a human reading the result, rather than after
three phases of plumbing.

The machine running this is not the machine that will solve. Taylor builds the bot on this Mac
and the real solve happens elsewhere, so an absolute wall-clock figure from here answers nothing
on its own. What transfers is a per-unit cost with its hardware recorded beside it, plus the peak
memory that decides which box can run the thing at all. A solve that exceeds a box's memory does
not run slowly, it fails, so memory is a separate axis from time and not a footnote to it.

## Scope

Approved:

- `scripts/measure_postflop_solve_cost.py` - the offline driver. Never run by the gate, the same
  way `scripts/extract_gtopen_preflop.py` is never run by the gate, so the gate keeps passing on a
  machine with no GTOpen server, no Rust toolchain and no network.
- `docs/GTOPEN_SOLVER_NOTES.md` - where the answers land, in the "Not verified" list they close.

Through standing scope: `CURRENT_TASK.yml`, `backlog.yml`, `docs/exec_plans/**`, and
`reports/active/**` for the measurement report.

Forbidden, and worth naming because the neighbouring work is tempting:

- No entry in `phase_status.yml`, no phase contract, no `depends_on` edge. This is `MAINT-26`, not
  phase 16, and `check_repo_consistency` should have no reason to think a phase started.
- No committed postflop artifact, no solved ranges, no chart. The moment a solve output is
  committed, every later measurement is taken against it, and that is a phase decision with a
  human ruling attached.
- No change to the bot's runtime behaviour, and no new gate command ID.

## Delegation Plan

- No-delegation exception: the binding resource is one GTOpen server on one machine, and the
  deliverable is the timing of solves run against it. Concurrent lanes would contend for that
  server and contaminate the very numbers being measured, so splitting the work across lanes
  costs accuracy and buys no parallelism. The driver itself is one file modelled directly on
  `scripts/extract_gtopen_preflop.py`, which four HTTP calls already describe.

The exception covers implementation only. An independent read-only reviewer is owed before the
gate commit regardless, and the handoff is stated here so it is not invented later.

- Review handoff: a reader who did not run the solves checks three things. That every number in
  `docs/GTOPEN_SOLVER_NOTES.md` carries the hardware it was measured on and is stated as a
  per-unit cost rather than a total. That no extrapolation to 1,755 flops or to any preflop-line
  count is presented as measured when it is multiplied. And that nothing in the diff commits a
  solve output, touches `phase_status.yml`, or reads as phase 16 having begun.

## Slices

- [ ] **Confirm the postflop routes against a running server.** Build one spot, solve it to a
  loose target, read one node back. Evidence: the request and response shapes recorded in the
  notes, in the same style the preflop config surface is already recorded. This is the part that
  can fail early and cheaply, and everything below assumes it passed.
- [ ] **Write the driver.** Takes both ranges, pot, stacks and sizes for one preflop line out of
  the committed export, plus a board and an exploitability target. Returns wall-clock to target,
  iterations, peak resident memory, the solved payload's size on disk, and the machine spec.
  Evidence: one recorded run.
- [ ] **Measure across textures and lines.** Exploitability at GTOpen's stated study-quality
  0.3% of pot. Texture varies deliberately, because the notes already record isomorphism gains of
  about 1.4x on two-tone flops and 2.2x on monotone, so texture is a variance driver rather than
  noise and a single flop's timing would be a mean nobody can use. At least one single-raised pot
  and one three-bet pot, since narrower ranges and a shallower SPR should move cost more than the
  board does. Evidence: `reports/active/latest_postflop_solve_cost.txt`.
- [ ] **Determinism.** One config solved twice and diffed, which is still unverified for postflop
  exactly as it was for preflop before phase 10 checked it. Evidence: byte-identical, or a
  recorded accuracy target and tolerance instead.
- [ ] **State the cost model.** Per-unit cost and peak memory as functions of texture and line,
  with the measuring hardware named, so another box can be reasoned about without re-running
  anything. Any GPU claim stays marked unrun unless GPU hardware is actually available; the
  README's ten-times figure is not evidence.
- [ ] **Record and file.** Update the "Not verified" list in `docs/GTOPEN_SOLVER_NOTES.md` to say
  what is now known. Anything the numbers invalidate - the flop-only ruling, the full-1,755
  choice, the preflop-line head - goes to `backlog.yml` as a deferred item naming phase 16, not
  as a decision taken here.
- [ ] **Independent read-only review**, per the handoff above, before the gate commit.

## Verification

No new command IDs and no new reports required by any contract, because this task has no contract.
The gate is the existing derived gate and it must stay green:

- `uv run python scripts/run_verify.py`

The measurement driver is deliberately absent from `COMMANDS` in `scripts/run_verify.py`. A gate
command that needs a GTOpen server would make the gate unrunnable on any machine without one,
which is the same reason the preflop extractor was left out.

Evidence produced rather than gated: `reports/active/latest_postflop_solve_cost.txt`, and the
closed entries in the notes' "Not verified" list.

## Outcome

Not yet complete. Opened 2026-08-23.

## Next Agent Bootstrap

Context: the repo is on `maint/26-postflop-solve-cost` in the worktree
`~/projects/poker-bot-worktrees/maint-26`, branched from `main` at `7ad2030`. `CURRENT_TASK.yml`
holds `MAINT-26` in `maintenance` mode. This lane is invisible to `scripts/loop_fleet.py --status`,
which only recognises `phase/NN-slug` branches; that is expected and not a fault. Phase 13 is
closing out in `~/projects/poker-bot-worktrees/phase-13` and merges to `main` first. This lane
integrates after it, and rebases onto the result if `main` has moved.

This is not a loop phase, so `scripts/loop_stage.py` does not drive it. Work the slices above in
order.

State: task opened, no implementation written, gate green at the base commit.

Next command:

    uv run python scripts/run_verify.py

Then slice 1, which needs a running GTOpen server and cannot start without one.
