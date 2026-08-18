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

Expected for implementation, to be approved with its own `scope_change_log` entry when
the loop reaches stage 4:

- `src/poker_training_bot/solver_artifacts/` - a GTOpen export reader, additive only
- `scripts/extract_gtopen_preflop.py` - the offline one-time extractor
- `scripts/check_solver_export_expectations.py`
- `scripts/generate_solver_export_report.py`
- `scripts/run_verify.py` and `scripts/check_file_sizes.py` - command registration and
  the `data/artifacts/**` byte limit, both authored at stage 4 and frozen before the
  builder starts
- `data/artifacts/preflop/exports/` and its source card
- `tests/test_solver_export.py`, `verification/freeze.lock`, `verification/mutations.yml`

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

- [ ] **S1 - Contract.** Real acceptance criteria replacing the skeleton, phase set
      `active`, this plan created. Evidence: `loop_stage.py --advance` clears stage 1.
- [ ] **S2 - Probe the solver.** Runs inside the decisions stage, because three of the
      decisions cannot be made without its numbers. Determinism (one config twice,
      diffed), a timed solve to the declared target, the `/api/preflop/node` path
      encoding read from the Rust source, the node count for the ruled config with limps,
      and the conditioning discriminator: at a node after a raise, does a hand the raiser
      always folds carry a strategy row. Read-only against an external tool; changes no
      repo behaviour. Evidence: numbers moved into the verified section of
      `docs/GTOPEN_SOLVER_NOTES.md` and quoted in the audit packet.
- [ ] **S3 - Decisions.** Every judgment call with a reversibility class: the solve config
      as posted, the exploitability target, the three expectations thresholds, the export
      layout and its quantisation step, the `data/artifacts/**` byte limit, and which
      spots the report shows. The thresholds, the target, and the quantisation are
      `frozen-into-data` and stop at the human gate. The layout decision is made against
      S2's measured node count, which is why it follows the probe: at the no-limp figure
      of 38,828 action nodes a dense float dump is already two orders of magnitude past
      committable, so the decision is what layout keeps the whole tree under a defensible
      limit. Evidence: stage 2 check green.
- [ ] **S4 - Human gate.** Taylor rules on the frozen-into-data items, and on the export
      layout if S2's count makes the whole-tree requirement collide with the byte limit.
      Evidence: stage 3 check green.
- [ ] **S5 - Tests, thresholds, and limits.** `tests/test_solver_export.py`, the three
      expectations checks, command registration, and the `data/artifacts/**` byte limit,
      all against a payload fixture captured from the S2 probe and a deliberately broken
      one. Evidence: `pytest_solver_export` red on assertions, then frozen.
- [ ] **S6 - Parity solve.** NL25 rake basis with limps, graded against all eleven
      numbers in the expectations file. Evidence: the comparison in the report. A failure
      here halts rather than widening a tolerance.
- [ ] **S7 - Committed solve and export.** Rake-free, limps in the tree, `open_raises`
      `[2.5]`, whole tree walked, source card written with checksum and the licence gap
      stated. Evidence: node count reconciled against `action_nodes`; limped and
      four-bet nodes asserted present; measured bytes per node and per expressible spot.
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

Branch `phase/10-solver-extraction`, base commit
`f53358220ebb6dcc0bf1ff73f15518ce8eeebce9`. Read `CURRENT_TASK.yml`, then
`uv run python scripts/loop_stage.py` and do the one stage it names.

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
- Everything in the notes file's "Not verified" section is genuinely unverified,
  including solve time and determinism. Do not quote the 300-iteration run as a result.
- The solve config is ruled, not open: six-handed, 100bb, `open_raises` `[2.5]`,
  `limp: true`, rake-free for the committed export. `docs/V2_ROADMAP.md` carries the
  rulings; `docs/V2_RULING_MITIGATIONS.md` section 1 carries the expectations plan and
  section 2 the size measurement Phase 14 is owed.
- Read `docs/V2_RULING_MITIGATIONS.md` before writing any threshold. The two decisions a
  phase could get wrong quietly are named at the end of it, and one of them is this
  phase's: authoring the expectations tolerances before the solve rather than after.
