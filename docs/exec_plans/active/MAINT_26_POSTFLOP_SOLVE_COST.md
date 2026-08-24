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

An earlier draft of this section carried a no-delegation exception, on the grounds that one
GTOpen server cannot be shared. Taylor asked for worker lanes on 2026-08-23, and the exception is
withdrawn rather than quietly left standing beside work that contradicts it. The constraint it
named is real and survives as the rule below: the solver is a single-writer resource, so exactly
one lane may hold it at a time, and every other lane is designed to need nothing from it.

- Worker lanes: RECON reads the GTOpen Rust source for the postflop request and response types
  and proves them against the live server; DRIVER authors the measurement script against the
  shapes RECON returns; MATRIX designs the measurement set and the form of the cost model with no
  server access at all; VERIFY, added once MATRIX returned claims read out of Rust and never run,
  tries to refute them; MEASURE runs the calibration and then the matrix, holding the server
  alone; MECH and DOMAIN read the finished work independently of each other.
  Every lane name here is a single unhyphenated token on purpose, and the last two were renamed
  on 2026-08-24 from names that paired the word review with a hyphen and a discipline. The
  backlog-integrity check reads any hyphenated all-caps token under `docs/**` as a citation of a
  filed backlog item, so those two names failed the gate as findings filed under ids nobody
  created. Do not hyphenate a lane name. The trap itself is filed as
  `QUALITY-GATE-READS-LANE-NAMES-AS-BACKLOG-IDS` in `backlog.yml`.

VERIFY was not in the original six and is the lane that earned its place. MATRIX argued from the
source that a flop solve already contains the turn and river subgames beneath it, which would make
the ratios behind a ruling a human already took wrong. Accepting that on one agent's reading would
have written a correction into the record on the same kind of evidence that produced the error
being corrected. VERIFY ported the tree builder, validated the port byte-exact against the running
server, confirmed the mechanism, and then refuted MATRIX's own arithmetic in two other places.
- Ownership: RECON owns no repo file and returns findings only. DRIVER owns
  `scripts/measure_postflop_solve_cost.py`. MATRIX owns no file and returns a design. MEASURE owns
  `reports/active/latest_postflop_solve_cost.txt` and is the sole holder of `127.0.0.1:3737` while
  it runs. The coordinator owns `docs/GTOPEN_SOLVER_NOTES.md`, `backlog.yml`, and this plan.
  Nobody but the coordinator writes `CURRENT_TASK.yml`.
- Expected outputs: RECON returns the exact accepted JSON bodies for `/api/spot`, `/api/solve`,
  `/api/status` and `/api/node`, with the source paths that prove them. DRIVER returns the script
  plus the commands it ran. MATRIX returns the flop set with the reason each texture is in it, the
  preflop lines, and the per-unit form the numbers must be reported in. MEASURE returns the raw
  timings, peak memory, and the determinism diff. Reviewers return notes classified as blocker,
  non-blocker, or alignment item.
- Status: RECON completed; MATRIX completed; VERIFY completed, a seventh lane added mid-task to
  refute MATRIX's source-only claims before they entered the record; DRIVER completed after one
  connection failure and a resume; MEASURE completed the build sweep, both calibration probes
  and five of the twelve matrix cells, and is closed at five by the ruling below rather than
  run to completion; the determinism row it still owes is one repeat of a cell already solved,
  not a new spot. Both review lanes are unblocked and unspawned.
- Integration order: RECON and MATRIX run concurrently because neither writes a file and only one
  touches the server. DRIVER follows RECON. MEASURE follows DRIVER and runs alone, calibrating at
  a loose exploitability target first so the matrix is sized against a known order of magnitude
  rather than launched blind at study quality. The coordinator writes the notes from MEASURE's
  numbers, and only then are the reviewers spawned.
- Review handoff: a reader who did not run the solves checks three things. That every number in
  `docs/GTOPEN_SOLVER_NOTES.md` carries the hardware it was measured on and is stated as a
  per-unit cost rather than a total. That no extrapolation to 1,755 flops or to any preflop-line
  count is presented as measured when it is multiplied. And that nothing in the diff commits a
  solve output, touches `phase_status.yml`, or reads as phase 16 having begun. Neither reviewer
  sees the other's notes, and neither wrote any of the work being judged.

## Slices

- [x] **Confirm the postflop routes against a running server.** Build one spot, solve it to a
  loose target, read one node back. Evidence: the request and response shapes recorded in the
  notes, in the same style the preflop config surface is already recorded. This is the part that
  can fail early and cheaply, and everything below assumes it passed.
- [x] **Write the driver.** Takes both ranges, pot, stacks and sizes for one preflop line out of
  the committed export, plus a board and an exploitability target. Returns wall-clock to target,
  iterations, peak resident memory, the solved payload's size on disk, and the machine spec.
  Evidence: one recorded run.
- [ ] **Measure across textures and lines.** Exploitability at GTOpen's stated study-quality
  0.3% of pot. Texture varies deliberately, because the notes already record isomorphism gains of
  about 1.4x on two-tone flops and 2.2x on monotone, so texture is a variance driver rather than
  noise and a single flop's timing would be a mean nobody can use. At least one single-raised pot
  and one three-bet pot, since narrower ranges and a shallower SPR should move cost more than the
  board does. Evidence: `reports/active/latest_postflop_solve_cost.txt`.
  **Bounded at five of twelve cells, and closed rather than resumed.** See the ruling of
  2026-08-24 under Decisions. What the five leave unmeasured is not evenly spread: the cells ran
  cheapest texture first, so all five that converged are monotone or two-tone and no rainbow board
  reached the 0.3% target on either line. Rainbow is the expensive end and the common one, so
  every pooled figure in the report's aggregate is biased low against the population of 1,755
  flops. The report now says so in a line derived from its own rows rather than in prose a later
  run would overwrite, and the gap is filed to `backlog.yml` as
  `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`.
- [x] **Determinism.** One config solved twice and diffed, which is still unverified for postflop
  exactly as it was for preflop before phase 10 checked it. Evidence: byte-identical, or a
  recorded accuracy target and tolerance instead.
  **Byte-identical, and reproducible beyond what the slice asked.** The `matrix-02` config solved
  twice on 2026-08-24 gives the same root strategy digest `ca16cf82eeb9c96e`, a largest
  per-action frequency divergence of 0, no combo present in one run only, and 240 iterations to
  the same 0.2948% exploitability both times. That digest also equals the one the original
  `matrix-02` row recorded on 2026-08-23, so the solve reproduces across a server restart and
  across days rather than only twice in a row. No accuracy target or tolerance is needed. Wall
  clock is the one figure that moved, 206.0 and 204.6 seconds against the original run's 330.9,
  which is thermal drift on a loaded machine and is no part of the claim.
- [ ] **State the cost model.** Per-unit cost and peak memory as functions of texture and line,
  with the measuring hardware named, so another box can be reasoned about without re-running
  anything. Any GPU claim stays marked unrun unless GPU hardware is actually available; the
  README's ten-times figure is not evidence.
- [ ] **Record and file.** Update the "Not verified" list in `docs/GTOPEN_SOLVER_NOTES.md` to say
  what is now known. Anything the numbers invalidate - the flop-only ruling, the full-1,755
  choice, the preflop-line head - goes to `backlog.yml` as a deferred item naming phase 16, not
  as a decision taken here.
- [ ] **Independent read-only review**, per the handoff above, before the gate commit.

## Decisions

- **Stop the matrix at five of twelve cells** - *runtime-reversible*. Ruled by Taylor on
  2026-08-24, asked because the remaining seven are about two more hours of solving on this
  machine and the run had already halted itself mid-cell-six when the Mac came off AC. Nothing is
  frozen into committed data by stopping: no solve output is committed, the driver takes a cell
  per invocation, and the seven can be run later on this or any other box by re-invoking it. What
  it costs is texture coverage, recorded in slice 3 and in the backlog rather than left implicit.
- **Report the cost model from five cells rather than withholding it** - *runtime-reversible*.
  The per-unit costs, the peak memory and the convergence shape are what the task owed, and all
  three are measured on real study-quality solves. The figure that must not be stated flat is a
  per-flop mean over all textures, and the report's aggregate now names the textures it rests on.

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

Not yet complete. Opened 2026-08-23. Measurement closed 2026-08-24 at five matrix cells by
Taylor's ruling; the determinism row, the cost-model write-up into the notes, and both reviews
are still owed.

## Next Agent Bootstrap

Context: the repo is on `maint/26-postflop-solve-cost` in the worktree
`~/projects/poker-bot-worktrees/maint-26`, branched from `main` at `7ad2030`. `CURRENT_TASK.yml`
holds `MAINT-26` in `maintenance` mode. This lane is invisible to `scripts/loop_fleet.py --status`,
which only recognises `phase/NN-slug` branches; that is expected and not a fault. Phase 13 is
closing out in `~/projects/poker-bot-worktrees/phase-13` and merges to `main` first. This lane
integrates after it, and rebases onto the result if `main` has moved.

This is not a loop phase, so `scripts/loop_stage.py` does not drive it. Work the slices above in
order.

State: slices 1 and 2 are done and slice 3 is closed short by ruling. The driver exists and
works, `reports/active/latest_postflop_solve_cost.txt` holds 52 rows - 24 builds, 28 solves - of
which five reached the 0.3%-of-pot target. Four findings are already filed to `backlog.yml`. The
GTOpen server may still be up at `127.0.0.1:3737` holding a killed cell six; a determinism run
should start from a freshly restarted server, because the report states about itself that peak
resident is a high-water mark over everything that process has ever held.

Do not resume matrix cells six through twelve. That was asked and answered on 2026-08-24; see
Decisions. Adding cells is not wrong, it is simply not this task's remaining work, and a later
task that wants rainbow coverage should re-invoke the driver rather than reopen this one.

What is left, in order: the determinism row (slice 4), the cost model written into the "Not
verified" list in `docs/GTOPEN_SOLVER_NOTES.md` (slices 5 and 6), then two independent read-only
reviewers per the handoff above (slice 7), then the gate and closeout.

Next command, one repeat of a cell already solved, on a freshly restarted server:

    uv run python scripts/measure_postflop_solve_cost.py --determinism --report ...

Read `--help` for the spot flags, and match them to the `matrix-02` row's config in the report so
the diff is taken against a solve that is already recorded.
