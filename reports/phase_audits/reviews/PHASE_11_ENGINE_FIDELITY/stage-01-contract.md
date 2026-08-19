# Phase 11 stage 1 (contract) review

Read-only pass over `git diff 0da4ba3 -- docs/phase_contracts/PHASE_11_ENGINE_FIDELITY.md`,
extended to the ExecPlan because the same stage changed it.
Question asked: is any acceptance criterion unfalsifiable, a restatement of the phase
title, or satisfiable without doing the work it names?

Context read: `AGENTS.md`, `docs/LOOP.md`, `verification/loop_policy.yml`, the six
`phase: "11"` entries in `backlog.yml`, the Phase 03 and Phase 06 contracts, and the five
source files the criteria constrain. No gate run.

Reviewer: coordinator, self-review. Subagents are unavailable in this session, so
`AGENTS.md` step 10's fallback applies; recorded again here rather than assumed from the
stage-0 note.

## Blocker

- **[resolved]** The free-fold criterion required "a committed fixture carries such a
  hand", and the committed hand fixtures are `data/samples/normalized_hands.json(l)`. That
  contradicts this contract's own Scope paragraph ("This phase commits no data") and, worse,
  contradicts `verification/loop_policy.yml`, which grants phase 11 `auto_advance: true` on
  the ground that it writes no committed data. A criterion that quietly revokes the phase's
  own auto-advance permission is the kind of thing that surfaces at stage 11 as a halt
  nobody planned. Fixed in the contract: the hand is constructed inside the test, and the
  criterion says why - a new committed sample is also a new input every later measurement
  silently inherits.
- **[resolved]** Two criteria pointed opposite ways. The free-fold group requires
  `StrategyQuery` to stop asserting that `check` and `fold` are never both legal; the
  forbidden shortcuts forbid fixing a defect by weakening a validator, and name
  `StrategyQuery` validation first. As written, an implementer could satisfy either one by
  citing the other. Fixed in the contract: the removal is named as the single permitted
  exception, with the reason (the invariant became false) and the replacement protection
  (no shipped strategy folds for free) stated in the same place, and the forbidden shortcut
  now says that any other loosening is the shortcut whatever the justification.
- **[resolved]** "Every other producer of a `StrategyQuery` is checked ... and the audit
  packet lists them by file with the verdict for each" was satisfiable by writing a list.
  A sweep recorded in prose is exactly the criterion shape this question is asking about.
  Fixed: the criterion now says the prose list is the record and not the proof, and points
  at the mechanical backing - every producer named is reached by a gate command that
  constructs real queries, so the new `street_bet >= to_call` guard runs against all of
  them on every gate.

## Non-blocker

- "Every command description in the registry is checked against what its script does, and
  the audit packet records the sweep" is still a prose sweep with no mechanical backing, and
  unlike the producer sweep there is no honest mechanical version of it - a check that a
  description matches a script's behaviour is a check that reads English. Carried as an
  audit-packet requirement rather than dropped, because the alternative is fixing only the
  one description a reviewer happened to notice, which leaves the class open.
- The criterion that every defect is pinned by a test failing against `main` at the branch
  point is verified in aggregate by the loop rather than per defect: stage 4's advance check
  requires this phase's pytest command to be red before any implementation exists. Per-defect
  attribution stays prose in the audit packet. That is the strongest available form and it is
  worth naming as a limit rather than reading the criterion as fully mechanical.
- "No strategy shipped in this repo ever chooses to fold when checking is free" is the
  criterion most likely to turn into real work rather than a check. The preflop chart returns
  a sampled action from artifact weights, and whether any committed spot can produce `fold`
  in a free spot has not been established. If one can, this phase has to decide between
  suppressing it at lookup and treating it as an artifact defect, and that is a stage-2
  judgment call rather than something the contract should pre-empt. Named so stage 2 does not
  discover it late.
- The contract requires the report to state which committed numbers these fixes move without
  recomputing them. That boundary is right - re-measuring belongs to the phase that owns the
  measurement - but it means the phase closes with several published numbers known to be
  stale and not corrected. The criterion makes that visible rather than silent, which is the
  best a fix-only phase can do, but a reader of the audit packet should not have to infer it.
- The contract lands at 298 lines against `check_file_sizes.py`'s 300-line cap for docs, and
  it first came in at 301 and was tightened rather than the cap raised. Two lines of headroom
  is not enough for a later correction, so any stage-2 or stage-4 amendment to this contract
  will have to buy its space by cutting. Named because the alternative - editing the cap from
  inside the phase the cap is constraining - is the shortcut this repo has refused before.
- `check_repo_consistency` fails from this commit until stage 4, because the contract now
  declares two command IDs that are not yet in `COMMANDS`. That is the Phase 10 ordering
  (command IDs are authored at stage 4 and frozen before the builder starts) and not a
  defect, but it is worth having written down: the next agent will run the gate, see it red,
  and needs to know that is expected. Recorded in the ExecPlan's Verification section.

## Alignment

None. The one systemic issue in view - that a fix phase cannot re-measure what it moves -
is a property of how the phases were cut rather than drift this contract introduces, and it
is already carried as a criterion and a forbidden shortcut inside the phase.
