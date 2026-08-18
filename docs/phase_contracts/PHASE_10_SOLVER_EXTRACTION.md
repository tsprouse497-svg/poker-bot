---
phase_id: "10"
title: "Solver Extraction, And A Human Verdict On It"
depends_on:
  - "09"
required_gate_commands:
  - pytest_solver_export
  - check_solver_export_expectations
  - generate_solver_export_report
required_reports:
  - reports/active/latest_verify.txt
  - reports/active/latest_solver_export_report.txt
required_phase_audit: reports/phase_audits/PHASE_10_SOLVER_EXTRACTION.md
---

# Phase 10: Solver Extraction, And A Human Verdict On It

## Scope
This phase captures a solved preflop tree from GTOpen, commits it as data, and puts a
human in front of range grids to say whether the extraction is faithful.

It is the deliberate exception to format-before-data.
An export is written in the solver's own vocabulary rather than in this repo's spot
keys, so nothing about capturing one waits on the vocabulary work in Phase 12.

`docs/GTOPEN_SOLVER_NOTES.md` records what running GTOpen established and what it did
not, and the unverified list is this phase's first deliverable rather than an aside.
Four things on it decide how the rest of the phase is built: how long a real solve takes
to a stated exploitability target, whether two identical runs agree, how
`/api/preflop/node` encodes a path, and whether a node's strategy is conditioned on
reaching that node. The last one decides whether the converter needs the
range-intersection step the GTO Wizard export required, so it is answered before a
converter is written rather than debugged afterwards.

The solve config is ruled rather than chosen here: six-handed, 100bb, 2.5bb opens,
limps in the tree, and rake-free for the export that gets committed. Those are rulings 1
through 4 in `docs/V2_ROADMAP.md`.

Rake-free is what changes this phase's own verification, and
`docs/V2_RULING_MITIGATIONS.md` section 1 plans it in full.
`data/artifacts/preflop/expectations/six_max_nl25_100bb.json` is the only set of numbers
in this repo that this repo did not produce, which makes it the one thing that can catch
an extraction that is uniformly wrong rather than merely self-consistent. All eleven of
its numbers are rake-sensitive, so against a rake-free solve it is a gross-error check
and not an equality check. What replaces the equality check is a second solve at the
NL25 rake basis the file describes, graded against it directly, so that the question of
whether the extractor is correct stops being fused with the question of whether rake-free
differs from raked as expected.

Phase 10 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
  The gate must pass on a machine with no GTOpen, no Rust toolchain, and no network. The
  extractor is an offline one-time script whose output is committed, which is how the
  existing chart artifact already works.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not derive a chart artifact from the export, and do not change which chart the bot
  plays.
  The bot still reads the committed 36-spot chart when this phase closes. Deriving the
  replacement is Phase 14, and it waits on the Phase 12 vocabulary.
- Do not change the spot key, the chart schema, the converter, or the strategy.
- Do not filter the export to the spots today's vocabulary can express.
  Four-bet nodes are in the solve and unreachable through a v1 spot key. An extractor
  that keeps only what fits today is the one thing that would force a re-extraction
  after Phase 12.

## Acceptance criteria

### The unverified list is answered with measured numbers
- Determinism is settled by running one config twice and diffing the extracted output,
  and the result is recorded either as byte-identical or as a stated per-frequency
  tolerance with the observed maximum divergence.
  Nothing may be planned around reproducibility until this is a number. If the output is
  not stable, the tolerance is what every later comparison is written against.
- A real solve is timed: wall clock, iteration count, and the exploitability actually
  reached against the target declared before the run.
  The only prior measurement is a 300-iteration smoke test with no timing, and marginal
  hands converge last, so no claim about the tree rests on it.
- The determinism result and the timing figures are fields on the committed source card,
  and a committed test fails when any of them is absent or left at a placeholder.
  Neither number can be recomputed inside the gate, because that would mean running the
  solver. Requiring them as structured fields is what stops them from being prose nobody
  checks, which is the drift defect Phase 09 exists to have closed.
- The `/api/preflop/node` path encoding is documented from the solver source, and the
  walk that uses it is self-verifying: every node in the export re-resolves from its own
  recorded action sequence to a node whose `actor_pos` and action list match, and the
  traversal closes, so each node has exactly one child per non-terminal action.
  A misread encoding does not error, it silently returns a different node, and a walk
  that cannot detect that is an extraction nobody can trust.
- Whether a node's strategy is conditioned on reaching that node is answered by a stated
  discriminator rather than by inspection: at a node reached only after a raise, a hand
  class the raiser folds at full frequency either carries no weight, which makes the
  payload conditional, or carries a full strategy row, which makes it unconditional.
  A conditional payload needs no range intersection; an unconditional one does, and
  getting this backwards produces ranges that are self-consistent and wrong.

### The expectations checks are written down before any solve runs
- The three checks in `docs/V2_RULING_MITIGATIONS.md` section 1 exist as code with stated
  thresholds, and are frozen by `scripts/freeze_tests.py`, before the committed solve is
  run. The thresholds are recorded in the phase decision list with their reasoning.
  A tolerance authored once the numbers are visible is a tolerance fitted to them. The
  loop already enforces this ordering mechanically for tests: thresholds authored at the
  test stage and frozen at the next one cannot be edited by the stage that runs the
  solve, so this criterion points at that machinery rather than at good intentions.
- `check_solver_export_expectations` computes the orderings and the directional bound
  from the committed export itself, so it re-runs on every gate. The parity comparison is
  a one-time measurement, and its eleven aggregates are committed alongside the export so
  that comparison re-runs too.
  A gate check that reads a number some earlier run recorded is a mirror, which is the
  defect Phase 09 already found in this repo's own settlement oracle. What makes the
  parity solve worth its cost is that its result stays checkable, not that it once
  passed.
- The big-blind defence ordering holds exactly and carries no tolerance, descending SB,
  BTN, CO, HJ, LJ, and the opening ordering holds exactly among LJ, HJ, CO, BTN with the
  small blind excluded by name and the exclusion's reason recorded.
  `docs/V2_RULING_MITIGATIONS.md` claims rake moves the level of all eleven numbers and
  the ordering of none. The probe falsified that for the small blind: rake-free reallocates
  twelve points of small-blind limping into raising, which moves SB from second in the
  opening order to first. Later position opens wider is structural and survives; the small
  blind's place in that order is a limp-versus-raise mix that rake decides. A transposed
  hand index, a mis-assigned actor, or an unnormalised strategy row still breaks the
  surviving orderings immediately, which is what they are for.
- The directional bound is one-sided with a stated slack, authored before the committed
  solve: each of the ten opening and defence numbers is at least the raked expectation
  minus a declared margin, and at most one of the ten may sit below its expectation at all.
  The small-blind limp frequency is excluded by name, because rake's effect on how often
  the small blind limps rather than raises is not obviously signed.
  A zero-slack bound was the original specification and the probe failed it on one number
  by 2.55 points, which between a full solver and a preflop-only equity-realization model
  is solver difference rather than a defect. The at-most-one clause is what stops the slack
  from degrading into a blanket tolerance: a uniformly tighter extraction still fails on
  nine counts.
- A parity solve at the NL25 rake basis, with limps in the tree, is run and compared to
  all eleven numbers with a tolerance set for solver difference rather than for zero.
  The expectations file reports a small-blind limp frequency, so the solve it describes
  had limps; a no-limp parity solve would not be comparing the same thing. GTOpen is not
  GTO Wizard, so exact agreement is not the expectation at any rake basis.
- A tolerance may not be widened after the numbers are visible. If a check fails, the
  phase halts and the disagreement is diagnosed, and any change to a threshold is a
  ruling recorded with its reason.

### The export is the whole solved tree, and it is auditable data
- Every action node in the solved tree appears in the export, including limped branches
  and four-bet-and-beyond nodes. The source card records both the export's own node count
  and the `action_nodes` figure `/api/preflop/spot` reports for the same config, and
  either they agree or the difference is reconciled by a stated derivation.
  What GTOpen counts as an action node is read rather than assumed, so demanding blind
  equality would fail a correct walk on a naming difference. What may not happen is the
  two numbers sitting side by side unexplained.
- Committed tests assert by construction that a limped node and a four-bet node - the
  fourth raise, counting the open as the first - are both present in the committed export.
  Requiring the whole tree in prose is not the same as failing when a branch is missing.
- The export format is chosen against the measured node count, and the whole-tree
  requirement is reconciled with the byte limit before the committed solve runs.
  This is the one place two instructions in this contract can collide. The no-limp tree
  already reports 38,828 action nodes, limps make it larger, and every action node carries
  a row per action across 169 classes, so a plain array-of-floats dump is two orders of
  magnitude past anything committable. A sparse or quantised layout is expected, and the
  quantisation step is itself a threshold that must be declared before the solve. If the
  whole tree cannot fit under a limit the phase is willing to defend, the phase halts for
  a ruling. It does not quietly drop the branches today's vocabulary cannot reach, because
  that is the one decision that would force a re-extraction after Phase 12.
- The committed export is produced with `realization` set explicitly, and the source card
  names the setting and states that GTOpen's preflop engine resolves flops by scaled equity
  share rather than by playing them.
  This field is absent from the accepted config body in `docs/GTOPEN_SOLVER_NOTES.md`, so
  every run before the probe took its default of `static`, which is very nearly raw equity
  realization. Under it the big blind defends 99.71 percent against a small-blind open. That
  is not a rake effect and it is not poker, and it would have produced a self-consistent,
  checksummed, thoroughly reported calling station. The limitation belongs on the card
  rather than in a document, because it is what anybody reading the chart needs to know
  about what made it.
- A source card records the exact config body posted to the solver, the GTOpen commit
  hash, the achieved exploitability, the wall clock, the determinism result, and a
  checksum over the export, so the origin is checkable rather than asserted.
- The source card states plainly that GTOpen ships no LICENSE file and that this is a
  known limitation, rather than letting a provenance field imply a permission nobody
  granted.
- A byte limit covering `data/artifacts/**` is added and the committed export sits under
  it with stated headroom.
  That directory is covered by no size check at all today, so a 12 MB artifact or a 40 MB
  one commits with nothing objecting. Exceeding the limit is a halt and a decision, not a
  number to raise.
- The export's measured bytes per node and bytes per expressible spot are reported, so
  Phase 14 sets its expectations from a measurement rather than from the roadmap's 7.1 KB
  per spot, which is measured off a different format.

### A human can reach a verdict from the report
- `reports/active/latest_solver_export_report.txt` shows range grids in the 169-class
  layout for a deterministic, stated selection of spots, plus opening frequency per
  position and big-blind defence per opener.
  The report is a human review surface and is capped like every other report, so it
  cannot hold the whole tree. It must name which spots it shows and which it omits.
- The report puts the eleven aggregates from the committed rake-free solve, the parity
  solve, and the expectations file side by side, and labels each comparison as an
  ordering check, a directional bound, or a tolerance comparison.
  A reader must be able to tell which numbers are being held to equality and which are
  only bounded, because that distinction is the whole content of the rake-free ruling.
- The audit packet records the human verdict as a verdict: which grids were read, and
  whether the extraction is faithful.
  This phase's stated purpose is a judgement no check performs, so a green gate without
  that line has not closed it.

### Reports and gate
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Every check this phase adds is unit-tested against a deliberately broken export as
  well as against the committed one.
  A check that has only ever run against data satisfying it has not been shown to fail.
- The judgment calls recorded in
  `reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md` carry a
  reversibility class before implementation begins, and the audit packet records the
  outcome of each one.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_verify.txt`
- `reports/active/latest_solver_export_report.txt`

## Required command IDs
- `pytest_solver_export`
- `check_solver_export_expectations`
- `generate_solver_export_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- The four answers from the unverified list, each as a number or a stated finding.
- The solve config as posted, and the licence gap stated as a limitation.
- The human verdict on the range grids, naming which grids were read.
- The recorded judgment calls and what each one changed.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not mock the solver payload in place of extracting a real one.
  A fixture written by the same session that wrote the converter agrees with it by
  construction. Fixtures may stand in for a running solver in tests only once they are
  captured from a real solve and committed as such.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not widen an expectations tolerance, drop a check, or narrow a comparison to make
  the extraction pass.
- Do not treat the 300-iteration smoke test in `docs/GTOPEN_SOLVER_NOTES.md` as a
  result.
- Do not commit an export produced by a config other than the one the source card
  records.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- No poker behavior changes: the engine, replayer, converter, charts, strategies,
  simulator, and every previously committed artifact are byte-identical at the end of
  this phase.
- Generated human docs remain current.
- File-size and scope checks continue to pass, including the new limit on
  `data/artifacts/**`.
