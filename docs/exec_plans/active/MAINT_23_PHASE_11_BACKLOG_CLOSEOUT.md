# MAINT-23: the six defects Phase 11 shipped are still filed as deferred

Task: `phase-11-backlog-closeout`. Mode: `maintenance`. Base: `47684d7`.

## Objective

Phase 11 fixed six defects, went green across 41 commands, was tagged `phase-11-complete` and
merged to `main`, and left all six sitting at `status: deferred` in `backlog.yml`.
Flip them to `done`, each saying what closed it and where the evidence is.

The six are `FOLD-WHEN-FREE`, `UNDER-RAISE-ACCUMULATION`, `FALLBACK-FAIL-CLOSED-CAN-CALL`,
`STREET-BET-MEANING-AMBIGUOUS`, `DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE`, and
`GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK`.

## Why this is worth a task rather than a quiet edit

`backlog.yml` is the only place this repo records what it knows is wrong with itself, and a
`deferred` entry is a claim that the work is still outstanding.
Six false claims of outstanding work is the same class of defect as a stale contract clause:
the next agent to read the backlog plans around defects that were fixed a phase ago, and the
one item in the list that genuinely is outstanding gets no more attention than the six that
are not.

## Why the gate could not see it

`backlog_errors` in `scripts/quality_checks.py` validates ids, required fields, the status
vocabulary, and that every cited id resolves.
Nothing compares an item's `phase` against that phase's status in `phase_status.yml`, so an
item filed against a *completed* phase and still marked `deferred` is a contradiction no check
can reach.
That is not specific to Phase 11: every phase from here closes the same way unless the check
exists.

It is filed here rather than written here, and filed as `contract-update` rather than as tooling.
`AGENTS.md`'s Task Closeout does not tell a phase to settle the backlog items it just fixed
either, so the process rule is missing before the check is, and something has to say what the
rule is before a check enforces it.
Doing both in one task would also put a bookkeeping correction and a new gate check in one
commit, and the check would then be reviewing the correction that motivated it.

## Scope

Approved: nothing beyond standing scope. Every file this task touches is already standing.

Standing: `backlog.yml`, `docs/BACKLOG.md`, `CURRENT_TASK.yml`, `STATUS.md`,
`docs/exec_plans/**`, `reports/active/**`.

Deliberately untouched: `scripts/quality_checks.py`, every phase contract, every audit packet,
and every review note. A `done` status is not a licence to rewrite the diagnosis - each entry
keeps what it said when it was filed and gains only what closed it.

## Delegation Plan

- No-delegation exception: subagents are unavailable in this operator's sessions - the standing
  instruction is not to call the Agent tool unless asked - so `AGENTS.md` step 10's self-review
  fallback applies, recorded here and performed below.

## Slices

- [x] Slice 1: the six entries flipped to `done`, each keeping its original diagnosis and
  gaining the fix that closed it plus the audit packet that evidences it.
- [x] Slice 2: `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` filed as `contract-update` for the
  missing rule and the missing cross-check.
- [x] Slice 3: one stale sentence in `PER-SEAT-CONTRIBUTIONS-IN-QUERY` corrected. It still said
  hero's own contribution is recoverable as `street_bet` minus `to_call`, which is the exact
  clause MAINT-21 struck from Phase 11's contract and MAINT-22 ruled on. Correcting the record
  about `to_call` in the contract while leaving the same false claim standing two entries away in
  this file would have been the drift this task exists to remove.
- [x] Slice 4: `docs/BACKLOG.md` regenerated, read-only self-review, full gate.

## Verification

`uv run python scripts/run_verify.py` - the full derived gate, 41 commands, no new command ids.
Bookkeeping only, so no report a gate command regenerates may move apart from the gate's own
records and `docs/BACKLOG.md`.

## Read-only self-review

Reviewer: coordinator, self-review, per the no-delegation exception above.

Question asked: does each `done` entry name something that actually shipped, and does the flip
hide anything that is still open?

- **No blocker.**
- Each of the six was checked against `reports/phase_audits/PHASE_11_ENGINE_FIDELITY.md` rather
  than against the commit subjects. The packet's per-defect evidence table names, for each one,
  a test that fails without the fix and a test that guards against over-applying it, so "done"
  here means pinned by a test and not merely edited.
- The one that needed care is `STREET-BET-MEANING-AMBIGUOUS`. Phase 11 closed it, and the field
  beside it turned out to carry the same defect, which is `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`
  and is still open for phase 13. Marking this one `done` while that one stays `deferred` is
  correct and reads wrong at a glance, so the entry says so explicitly. The same entry also
  carries the measured limit on the guard that shipped - it misses the heads-up small blind, who
  has contributed exactly half the level - which is `STRATEGY-QUERY-STREET-BET-NAME`, also open.
- `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK` is the smallest of the six and the only one
  that is pure text. It still gets a test naming it, which is why it is `done` rather than
  quietly deleted.
- The stale sentence in slice 3 is the finding that says the drift is not one-off. MAINT-21 struck
  that clause from a contract and MAINT-22 ruled on it, and both tasks looked at `backlog.yml`
  while doing it - `PER-SEAT-CONTRIBUTIONS-IN-QUERY` was even cited by the entry MAINT-22
  rewrote. A false claim survives being read when nothing asks the reader to check it.
- Worth stating rather than leaving implicit: this task changes no behaviour and fixes no defect.
  It corrects the record about defects already fixed. If the gate had a check for it, the task
  would not exist, which is the argument for slice 2.

## Alignment

- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` (filed this task, `contract-update`). Neither the
  closeout rule nor the gate check exists, so nothing catches a completed phase leaving its own
  items open. Long-term drift this task cannot fix, because the rule is contract work and the
  check is implementation.

## Outcome

Six entries flipped to `done`, each keeping its diagnosis and gaining the tests that pin the fix
and the canary that makes the gate bite. One stale sentence corrected. One item filed. Gate green
across 41 commands with no source, test, fixture, or committed report changed.

## Next Agent Bootstrap

Repo is on `main` in `~/projects/poker-bot-worktrees/main`, idle after this task closes.
Phase 11 is closed and its record is now honest. The open work it left is
`PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` for phase 12, `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`
and `STRATEGY-QUERY-STREET-BET-NAME` for phase 13, and four `contract-update` items of which
`MIN-RAISE-OVER-AN-INCOMPLETE-ALL-IN-BET` and `UNDER-SIZED-ALL-IN-BET-DOES-NOT-BAR-PRIOR-CHECKERS`
both need a human ruling before anything implements them, because the repo has no rules oracle
for either.
