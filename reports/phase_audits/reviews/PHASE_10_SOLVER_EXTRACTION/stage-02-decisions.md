# Stage 02 Review - Decisions (Phase 10)

Question asked: is every reversibility class right? A `frozen-into-data` call filed as
`runtime-reversible` proceeds on its default and is then written into a committed artifact
that later phases are measured against.

Scope: `git diff f53358220ebb6dcc0bf1ff73f15518ce8eeebce9 --
docs/exec_plans/active/PHASE_10_SOLVER_EXTRACTION.md
docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md`, extended to the decision list this
stage wrote, because reviewing the classes means reading the file that declares them.

Reviewer: coordinator, read-only pass, no gate runs. Subagent delegation is switched off in
this operator's sessions, so a read-only review subagent cannot be spawned and `AGENTS.md`
step 10's self-review fallback applies.

## Blocker

- [resolved] **Decision 10, per-node arriving ranges, was filed `runtime-reversible` on a
  false premise.** The draft argued `reach` is exactly recomputable from the strategies along
  the line, because that is how `node_view` builds it, so dropping it loses nothing. Two
  things break that. Under every option in decision 1 except a whole contiguous tree, the
  line from the root is not in the export, so there is nothing to walk and `reach` is not
  recoverable at all. And under decision 8 the committed frequencies are quantised to basis
  points, so even on a contiguous tree a recomputed `reach` is a product of rounded numbers
  rather than the value the solver used. A value that cannot be recovered from what is
  committed is precisely what the frozen class exists for. Reclassified to
  `frozen-into-data`, default changed to stored per exported node.

- [resolved] **The parity solve's rake basis was not a decision at all**, and it is
  load-bearing for decision 6. The parity solve's entire purpose is a like-for-like
  comparison, and `rake_pct: 5.0` with `rake_cap: 3.0` was inherited from the example body in
  `docs/GTOPEN_SOLVER_NOTES.md` with no derivation, against an expectations file that says
  only "NL25 rake". A wrong basis makes the parity comparison measure nothing while looking
  like the tightest check in the phase. Added as decision 6b, with the inference from the
  stake written out and a default that requires the source card to say the basis is inferred
  rather than confirmed.

- [resolved] **Two decisions were drafted as one question each when they are one question
  together.** The export's contents and whether limps stay were separate items, and no
  combination of their defaults was coherent: keeping limps and committing a whole tree is
  289,036 action nodes and hundreds of megabytes. Merged into decision 1 so the human rules
  on the trade rather than on two halves that cannot both be granted.

## Non-blocker

- **Five thresholds are filed `frozen-into-data` on a stretched reading of the class**, and
  it should be visible rather than silent. Decisions 4, 5, 6, 6b and 9 are check thresholds.
  They live in code, not in committed data, and nothing later is measured against them the
  way a chart cell is, so by the letter of the rule they are reversible. They are filed frozen
  because the frozen class is the only mechanism the loop has for stopping on a human, and
  `docs/V2_RULING_MITIGATIONS.md` names authoring these tolerances before the solve as one of
  two things this phase could get wrong quietly. The stretch is deliberate and the
  alternative - proceeding on a default tolerance nobody ruled on - is the failure the
  mitigations doc predicted. Filed as drift below.

- **Decision 11 stays `runtime-reversible` and that is right**, since the report regenerates
  from the export on every gate run. One consequence to carry: the human verdict is taken
  against whatever the report showed, so the audit packet must name the selection it read
  rather than citing "the report", or a later selection change silently re-scopes a recorded
  verdict.

- **Decision 3's target is filed frozen and the reasoning is worth stating**, because a solve
  parameter looks like a runtime knob. The export *is* the solve at that convergence, so the
  target is baked into every number later phases read. Frozen is correct.

- **The determinism method is not a decision but it is not specified either.** Two runs have
  to be two fresh spot builds, ideally in a fresh process, or a shared arena and a warm cache
  could make the second run agree for the wrong reason. Recorded in the ExecPlan rather than
  as a judgment call, since there is no defensible alternative to pick between.

- **The probe overtook the decision list, which is the right order but worth noting.** Three
  of the twelve decisions were unanswerable before measurement, and the measurements changed
  two acceptance criteria in the contract this phase had already written at stage 1. That is
  the loop working, not a defect, but it means the stage-1 review's approval of those criteria
  was given against numbers nobody had yet.

## Alignment

- `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` - the loop has no reversibility class for a
  threshold a human must own. Filed in `backlog.yml` under `maintenance`. This phase worked
  around it by filing five thresholds as `frozen-into-data`; the fix is either a third class
  or an explicit rule that a threshold graded against external data counts as frozen, and
  either way it is loop machinery rather than phase work.
