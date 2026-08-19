# Stage 05 Review - Freeze (Phase 10)

Question asked: is the scope narrowing real, and does its log entry say honestly why?

Scope: `git diff c893478f19f738c242dc768d57abf4d9b9718581 --
docs/exec_plans/active/PHASE_10_SOLVER_EXTRACTION.md
docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md
reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md`

Reviewer: coordinator, read-only pass, no gate runs. Subagent delegation is switched off in
this operator's sessions - the standing instruction is not to call the Agent tool unless it
is requested - so `AGENTS.md` step 6 cannot be satisfied and step 10's self-review fallback
applies. The stage opened with only the ExecPlan bootstrap in its diff; the contract and the
decision record entered it because this review put them there, and they are reviewed here
rather than in a note of their own.

## Blocker

- [resolved] **The contract's Scope section still specified the parity solve its own
  acceptance criteria forbid.** The 2026-08-18 re-ruling rewrote the criteria and left Scope
  saying that `docs/V2_RULING_MITIGATIONS.md` section 1 "plans it in full" and that "what
  replaces the equality check is a second solve at the NL25 rake basis the file describes,
  graded against it directly". Four lines of criteria below, the same document says no second
  solve is run and no gate check grades against that file, and the forbidden shortcuts name
  reintroducing a threshold over it by hand. This is not a wording slip: the builder about to
  be measured against a frozen test file reads the contract for what to build, and a
  contract that specifies a thing in Scope and bans it in Acceptance can be satisfied either
  way. The ExecPlan bootstrap in this stage's own diff is what surfaced it - it tells the
  next session that section 1 is superseded, which the contract it points at contradicts.
  Fixed in `contract-update` mode as `74fdb11`, with a `scope_change_log` entry, before the
  freeze.

- [resolved] **The decision record still instructed the report to read a number off the
  withdrawn solve.** Decision 7's small-blind bullet said the limp frequency "is zero by
  construction if decision 1 drops limps, and it is then reported from the parity solve
  instead". Both halves of that condition are settled and the second source does not exist,
  so an implementer following it either builds a second solve or invents a fallback. It now
  says the number is zero and printed beside the reference's 13.73 under the same
  gated-by-nothing label as every other reference row, which is what
  `test_every_reference_row_is_labelled_as_gated_by_nothing` already froze. Fixed in the same
  commit.

## Non-blocker

- Three further parity-solve references in the decision record are historical rather than
  operative: the accepted cost of the directional bound's three points of slack, the small
  blind's withdrawn lower bound, and the probe finding that argued the SB limp number was
  most likely to fail the parity comparison. They were annotated as superseded rather than
  deleted, on the same principle the ExecPlan used when it struck slice S6 - the record
  should say what was ruled and then unruled, not read as though it was never ruled. Left as
  annotations because rewriting a dated ruling to look correct in hindsight is worse than a
  stale sentence that says it is stale.

- The narrowing itself is real and mechanical rather than declarative: `tests/` and
  `verification/` leave `approved_scope`, and `scripts/check_scope.py` fails the gate on any
  diff that touches them from here on. `scripts/run_verify.py` and
  `scripts/check_file_sizes.py` leave with them, because both were authored at stage 4 and
  their contents are what stage 4's tests assert - the command registry entries and the
  ruled 20 MB `data/artifacts` limit are already in place, so the builder has no reason to
  reach either file and every reason not to. `verification/mutations.yml` leaves too; it
  comes back at the gate-bite stage under its own log entry, which is the pattern phases 08
  and 09 both used.

- `base_commit` moves to the freeze commit for the same reason it did in phases 05 through
  09: the diff has to be measured from the narrowing, or work that was legitimately in scope
  at stage 4 reads as out of scope for the rest of the phase. The one difference here is that
  it also passes through the contract-update commit above, so the contract correction is
  measured against the task that was authorised to make it rather than against the builder's.

- The ExecPlan bootstrap is honest about what it is claiming. It says determinism is still
  unverified and owes a second identical run in a fresh process, rather than implying the
  stage-4 timing settled it, and the frozen `complete_card()` fixture demands a
  `determinism` block that fails on a placeholder - so the one measurement this stage cannot
  make is the one the gate will refuse to let pass unanswered.

## Alignment

- None. The two findings above are this phase's own drift and were fixed inside it. No
  long-term repo drift surfaced in this diff that a backlog item should carry.
