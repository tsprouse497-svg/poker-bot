# ExecPlan: Phase 10 - Solver Extraction, And A Human Verdict On It

Contract: `docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md`
Loop state: `verification/loop_state.yml`, branch `phase/10-solver-extraction`
Policy: `auto_advance: false` - this phase commits data and its closing act is a human
judgement, so it halts before closeout regardless of how green the gate is.

## Objective

Capture a solved six-handed 100bb preflop tree from GTOpen, commit it as reviewable data
with a checkable source card, and produce a report a person can read to say whether the
extraction is faithful. Answer the four unverified questions in
`docs/GTOPEN_SOLVER_NOTES.md` with numbers first, because three of them decide how the
extractor is built and the fourth decides whether the converter needs range intersection.

Nothing downstream changes. The bot still reads the committed 36-spot chart when this
phase closes.

## Scope

Approved for the contract stage (`task_mode: contract-update`):

- `docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md`
- `reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md`

Approved for implementation as of 2026-08-18, `task_mode: implementation`:

- `src/poker_training_bot/solver_artifacts/` - a GTOpen export reader, additive only
- `scripts/extract_gtopen_preflop.py` - the offline one-time extractor
- `scripts/check_solver_export_expectations.py`
- `scripts/generate_solver_export_report.py`
- `scripts/run_verify.py` and `scripts/check_file_sizes.py` - command registration and
  the `data/artifacts/**` byte limit, both authored at stage 4 and frozen before the
  builder starts
- `data/artifacts/preflop/exports/` and its source card
- `tests/test_solver_export.py`, `tests/test_solver_expectations.py`,
  `verification/freeze.lock`, `verification/mutations.yml`

Forbidden throughout:

- `data/raw/**`, `data/processed/**` (existence rule)
- Any change to the committed chart, the converter, the spot key, the strategy, or the
  simulator
- Any runtime call to a solver from library or gate code

## Delegation Plan

- No-delegation exception: subagent delegation is switched off in this operator's
  sessions (the standing instruction is not to call the Agent tool unless it is
  requested), so `AGENTS.md` step 6 cannot be satisfied and step 10's self-review
  fallback applies. Implementation and both stage-8 review passes are coordinator-owned,
  each review written as a separate read-only pass against the diff with the mechanical
  and domain questions kept apart. The offer of delegated reviewers is put to Taylor
  rather than dropped silently.

## Slices

- [x] **S1 - Contract.** Real acceptance criteria replacing the skeleton, phase set
      `active`, this plan created. Evidence: `loop_stage.py --advance` clears stage 1.
- [x] **S2 - Probe the solver.** Runs inside the decisions stage, because three of the
      decisions cannot be made without its numbers. Determinism (one config twice,
      diffed), a timed solve to the declared target, the `/api/preflop/node` path
      encoding read from the Rust source, the node count for the ruled config with limps,
      and the conditioning discriminator: at a node after a raise, does a hand the raiser
      always folds carry a strategy row. Read-only against an external tool; changes no
      repo behaviour. Evidence: the probe section of the decision list, and the audit packet.
      `docs/GTOPEN_SOLVER_NOTES.md` is deliberately not edited here: its config body omits
      `realization`, which is a defect in that document rather than in this phase, and it is
      filed as `GTOPEN-NOTES-OMIT-REALIZATION` for a maintenance task.
- [x] **S3 - Decisions.** Thirteen judgment calls, twelve `frozen-into-data`. Written
      against S2's measurements rather than estimates, which is why the probe precedes them.
      Evidence: stage 2 check green.
- [x] **S4 - Human gate.** Ruled by Taylor on 2026-08-18, all on their recorded defaults,
      with three accepted costs written into the decision list rather than only the answers.
      The load-bearing ruling narrows ruling 3: limps leave the committed solve. Evidence:
      stage 3 check green.
- [x] **S4b - Contract correction, after the ruling.** The loop halted at stage 4 before a
      test was authored: four acceptance criteria still described the pre-ruling tree, and
      one of them required a committed test asserting a limped node is present in an export
      that ruling 1 forbids from containing one. Corrected in `contract-update` mode - the
      scope paragraph, the whole-tree criterion, the by-construction test criterion, the
      format-versus-byte-limit note, plus two the same read surfaced: the small blind gets
      the lower bound decision 4 ruled for it, and the report gains a fourth comparison
      label for the three parity numbers no threshold gates. Evidence: this commit, and the
      stage-4 review note covering it.
- [x] **S5 - Tests, thresholds, and limits.** Two files rather than one, because the
      export with its reader and card is a different subject from the three expectations
      checks and the report, and one file breaks the 700-line cap. Both are authored
      against a real payload captured from a fresh solve at the ruled config - six nodes
      committed as `gtopen_node_payloads.captured.json` - and against deliberately broken
      exports. Command registration and the ruled 20 MB `data/artifacts/**` limit land
      here too. The capture answered the last open question on the unverified list: the
      payload is unconditional, so `reach` is the only thing that conditions it.
      Evidence: `pytest_solver_export` red on a missing module, stage 4 check green.
- [x] **S6 - Withdrawn: the parity solve.** Taylor re-ruled the expectations design on
      2026-08-18 after running the solver himself. Nothing grades this solve's poker against
      GTO Wizard: decisions 6 and 6b are withdrawn with the parity solve, decision 5's
      directional bound goes with them, and decision 4 is restated so both orderings are
      internal to the export. Decision 6c replaces them - the extractor saves the solve and a
      human loads that save in GTOpen's own interface to compare grids against the committed
      report. The slice is struck rather than deleted so the record says what was removed.
- [ ] **S7 - Committed solve and export.** Rake-free, `limp: false`, `open_raises` `[2.5]`,
      `realization: "calibrated"`, whole tree walked - all 38,828 action nodes, no filter.
      Save the solve through GTOpen's save route before walking it and record its path, size
      and checksum - decision 6c makes the save load-bearing rather than a convenience, since
      it is the only way a human can reproduce a config the web form cannot express. Exercise
      save and load rather than assuming they work. Source card carries the config verbatim, the
      commit, the achieved gap, the wall clock, the determinism result, the checksum, the
      licence gap, and the equity-share model note. Evidence: node count reconciled against
      `action_nodes`; a four-bet node asserted present; measured bytes per node.
- [ ] **S8 - Report and gate.** `generate_solver_export_report.py`, full
      `run_verify.py`, `check_gate_bite`. Evidence: `reports/active/latest_verify.txt`
      and `reports/active/latest_solver_export_report.txt`.
- [ ] **S9 - Review, audit, verdict.** Mechanical and domain review passes, audit packet,
      and Taylor's verdict on the range grids recorded as a verdict.

## Verification

Command IDs: `pytest_solver_export`, `check_solver_export_expectations`,
`generate_solver_export_report`, plus the full derived gate from `scripts/run_verify.py`
and `scripts/check_gate_bite.py`.

Reports: `reports/active/latest_verify.txt`,
`reports/active/latest_solver_export_report.txt`.

## Outcome

Fill this in before completing the gate.

## Next Agent Bootstrap

Branch `phase/10-solver-extraction`, at stage 5 of 11 (freeze). Read `CURRENT_TASK.yml`, then
`uv run python scripts/loop_stage.py` and do the one stage it names. Every judgment call is
ruled, so the next stage authors tests against `reports/phase_audits/decisions/
PHASE_10_SOLVER_EXTRACTION_DECISIONS.md` and the contract, and nothing else needs a human
until the range-grid verdict at the end.

Context the next session needs and will not otherwise find:

- GTOpen lives at `~/projects/gtopen`, deliberately outside this repo, at commit
  `4aee435`. `cargo build --release` produced `target/release/gto-server`, which is
  present, and it serves `127.0.0.1:3737`. It is not running by default; start it with
  `start.sh`. `/api/status` reports `"gpu": false`, so the CPU engine is what runs.
- The extraction path is four HTTP calls, all previously exercised end to end and
  recorded in `docs/GTOPEN_SOLVER_NOTES.md`: `POST /api/preflop/spot`, `POST
  /api/preflop/solve`, `GET /api/preflop/status`, `POST /api/preflop/node`. No Rust is
  needed to extract.
- `strategy` in a node payload is `na x 169` floats flattened, action-major:
  `strategy[k*169 + i]`. The class index is ranks 0-12 as `2` through `A`, a pair at
  `hi*13+hi`, suited at `hi*13+lo`, offsuit at `lo*13+hi`. That mapping was confirmed
  empirically as well as read.
- **`realization` is a config field the notes file does not mention, and it decides
  everything.** Its default is `"static"`, which is very nearly raw equity realization,
  and under it the big blind defends 99.71 percent against a small-blind open. Ruled to
  `"calibrated"`, which loads `cache/realization_fit.json` and lands four of five opening
  frequencies within about a point of the raked GTO Wizard reference. Never omit the field.
- Solve time is answered: under the ruled no-limp config the 0.01 bb summed best-response
  gap is reached at iteration 300 in about two minutes, CPU only, measured at stage 4.
  Determinism is still unverified and owes a second identical run diffed against the first,
  in a fresh process.
- The node payload is **unconditional**: at the LJ-versus-3bet node, 72o carries reach 0.0
  and a full uniform strategy row. Aggregates must be weighted by `reach`, and the measured
  reach-weighted numbers reproduce GTOpen's own `freq` to six decimal places while a flat
  169-class average is out by 15 points at that node.
- The server was left running from stage 4: `~/projects/gtopen/target/release/gto-server`
  on 127.0.0.1:3737, with the ruled tree already built and solved. `start.sh` needs cargo
  on PATH; the built binary does not.
- The walk, not the solve, is the expensive half. `/api/preflop/node` re-walks from the
  root on every call, and node queries block while a solve runs because they need the mutex
  the solve holds - a request mid-solve hangs rather than erroring.
- The solve config is ruled, not open: six-handed, 100bb, `open_raises` `[2.5]`,
  `limp: false` for the committed export and `true` for the parity solve, rake-free for the
  committed export, `realization: "calibrated"`. `docs/V2_ROADMAP.md` carries the
  rulings; `docs/V2_RULING_MITIGATIONS.md` section 1 carries the expectations plan and
  section 2 the size measurement Phase 14 is owed.
- Read `docs/V2_RULING_MITIGATIONS.md` before writing any threshold. The two decisions a
  phase could get wrong quietly are named at the end of it, and one of them is this
  phase's: authoring the expectations tolerances before the solve rather than after.
