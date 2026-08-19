# Stage 01 Review - Contract (Phase 10)

Question asked: is any acceptance criterion unfalsifiable, a restatement of the phase
title, or satisfiable without doing the work it names?

Scope: `git diff f53358220ebb6dcc0bf1ff73f15518ce8eeebce9 --
docs/exec_plans/active/PHASE_10_SOLVER_EXTRACTION.md
docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md`

Reviewer: coordinator, read-only pass, no gate runs. Subagent delegation is switched off
in this operator's sessions, so `AGENTS.md` step 10's self-review fallback applies and the
concrete reason is that a read-only review subagent cannot be spawned here. Recorded in
the ExecPlan's Delegation Plan as well.

## Blocker

- [resolved] **The path-encoding criterion named a check that cannot exist.** It asked for
  the encoding to be "confirmed by reaching one node two different ways and getting the
  same node." In a preflop tree a node *is* its action sequence, so there are no two paths
  to one node and the criterion was unsatisfiable as written. Replaced with a criterion
  that has teeth against the failure that actually occurs: a misread encoding does not
  error, it silently returns a different node, so the walk must be self-verifying - every
  node re-resolves from its own recorded action sequence, `actor_pos` and the action list
  match, and the traversal closes with one child per non-terminal action.

- [resolved] **The whole-tree requirement and the byte limit could collide silently, and
  the contract did not admit it.** The contract forbids filtering the export to
  v1-expressible spots and separately requires a byte limit on `data/artifacts/**`. The
  no-limp config already reports 38,828 action nodes, limps make it larger, and each
  action node carries an action-by-169-class strategy row, so a dense float dump is on the
  order of a hundred megabytes - two orders of magnitude past anything committable. A
  session meeting both criteria under pressure would resolve the collision the wrong way,
  by filtering, which is the single decision that would force a re-extraction after Phase
  12. The contract now names the collision, requires the layout and its quantisation step
  to be chosen against the measured node count before the committed solve, and states that
  the phase halts for a ruling rather than dropping branches.

- [resolved] **Two headline numbers were prose nobody checks.** Determinism and solve time
  were required to be "recorded", which the audit packet satisfies by containing a
  sentence. That is precisely the drift defect Phase 09 was built to close. They cannot be
  recomputed in the gate without running the solver, so the fix is structural rather than
  computational: both are now required fields on the committed source card, and a committed
  test fails on an absent or placeholder value.

- [resolved] **The parity solve's result would have been a mirror.** The parity comparison
  was written as a one-time measurement while `check_solver_export_expectations` was left
  undefined between the three checks, which invites a gate command that reads a number an
  earlier run wrote down - the exact defect this repo already found in its own settlement
  oracle. The contract now splits them: the orderings and the directional bound compute
  from the committed export and re-run every gate, and the parity solve's eleven aggregates
  are committed alongside the export so that comparison re-runs too.

- [resolved] **The conditioning question was answered "empirically" with no stated
  discriminator**, which is an instruction to have a look. It now names the test: at a node
  reachable only after a raise, a hand class the raiser folds at full frequency either
  carries no weight (conditional payload, no range intersection needed) or carries a full
  strategy row (unconditional, intersection needed).

- [resolved] **The node-count criterion demanded blind equality** against GTOpen's
  `action_nodes`, whose counting semantics nobody in this repo has read. That would fail a
  correct walk on a naming difference and teach the next session to delete the check.
  Softened to: both numbers on the source card, agreeing or reconciled by a stated
  derivation - what is forbidden is the two sitting side by side unexplained.

- [resolved] **The ExecPlan sequenced the probe after the decisions it feeds.** The export
  layout cannot be decided without the measured node count, and the human gate cannot rule
  on a collision nobody has measured yet. The probe moved to S2, inside the decisions
  stage, with the decisions at S3 and the human gate at S4.

## Non-blocker

- The human verdict criterion is unfalsifiable by code, and deliberately so. A checker
  that could confirm a human read a range grid would be asserting the thing the phase
  exists to obtain. It stays a criterion a reader enforces, and the packet requirement
  asks which grids were read so the claim is at least specific.

- The report is capped at 300 KB like every other `reports/active/*.txt`, so it cannot show
  grids for the whole tree. The contract handles this by requiring a stated, deterministic
  selection and an explicit statement of what is omitted, which is honest but means the
  human verdict covers a sample rather than the export. Worth restating in the audit packet
  as a limitation rather than discovering it at review.

- The exploitability target is not a number in this contract. It is deferred to the
  decision list because nothing in the repo can justify a value before the probe measures
  what a solve to any target costs. The contract's guard is that the target is declared
  before the timed run rather than read off it.

- `check_solver_export_expectations` becomes a gate command that depends on a committed
  export, so it is red for the whole phase until S7 lands. That is the normal
  freeze-then-build shape, not a defect, but it means the phase carries two red gate
  commands across several stages and the driver will say so at each advance.

## Alignment

- None. Nothing here is drift this phase cannot fix; every finding above was inside the
  contract's own scope and was fixed in it.
