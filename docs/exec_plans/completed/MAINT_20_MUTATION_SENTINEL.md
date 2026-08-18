# MAINT-20: A Live Mutation Must Not Be Committable

## Objective

`check_gate_bite` proves the gate is not decorative by planting a defect in a source file, requiring the named command to go red, and restoring the file.
For the length of each of those 32 windows, the working tree genuinely holds a deliberate bug.

`verification/.mutation_in_progress` guards that, but only in one direction: the next run refuses to start when it finds one.
The window itself is unguarded, and a commit taken during it captures both the planted defect and the sentinel announcing it.

This is not hypothetical and has now happened twice.
On the Phase 09 branch a commit captured the cutoff and hijack labels swapped, and the gate went red on the next scope check rather than on the swap, so the symptom pointed away from the cause.
During MAINT-19 a backgrounded gate-bite run and a full gate run raced; the loser was interrupted and left a mutated `hand_history/replay.py` beside its sentinel, which cost a manual restore.

## Scope

Approved: `.gitignore`, `scripts/check_scope.py`, `scripts/check_gate_bite.py`, `tests/test_loop_machinery.py`, `verification/freeze.lock`, `verification/mutations.yml`.
`backlog.yml` is standing scope.

Forbidden: everything else. No phase is declared and no phase contract changes.

## Design

Two fixes, deliberately not exclusive, because each covers what the other cannot.

**The sentinel is gitignored**, so `git add -A` during a run physically cannot stage it.

**`check_scope` refuses while it exists.** Ignoring the sentinel also hides it from the scope diff, which is what caught it by accident during MAINT-19, so the state is asserted directly instead of relying on a side effect. The failure quotes the sentinel, so the operator is told which file to restore rather than being told a file is out of scope.

`check_gate_bite`'s own refusal now quotes the sentinel too, and names the second cause: not only an interrupted run, but a second run in flight right now, which is what actually happened.

## Delegation Plan

- No-delegation exception: subagent delegation is disabled in this operator's sessions. Two small guards on a defect this session reproduced first-hand. Self-review at the end, recorded in the outcome.

## Slices

- [x] Slice 1: gitignore the sentinel.
- [x] Slice 2: `mutation_sentinel_errors` in `check_scope`, wired into `main`.
- [x] Slice 3: `check_gate_bite`'s refusal quotes the sentinel and names the concurrent-run case.
- [x] Slice 4: tests, including that the writer and the checker name the same path.
- [x] Slice 5: a canary, so a guard that stops guarding fails the gate.
- [x] Slice 6: close `MUTATION-SENTINEL-IS-COMMITTABLE` in `backlog.yml`.

## Verification

- `uv run python scripts/run_verify.py`
- By hand: write a sentinel, confirm `check_scope` fails naming the file, confirm `git status` cannot see it, then delete it.

## Outcome

Six slices, gate green, 33 mutations all caught.

Verified by hand rather than only by test: writing a sentinel makes `check_scope` exit 1 quoting the file to restore, `git status` cannot see the sentinel at all, and `check_gate_bite` refuses with the same quote. Deleting it returns the repo to green.

The two fixes cover different failures and neither is sufficient alone.
Gitignoring stops a commit from capturing the sentinel, but on its own it would have made things worse, because the accidental catch that saved MAINT-19 was `check_scope` reporting the sentinel as an out-of-scope untracked file, and ignoring it removes exactly that.
So the scope check now asserts the tree's state directly instead of depending on a side effect, and it says which file to restore rather than reporting a stray path.

One test exists only to stop the guard drifting apart: `check_gate_bite.SENTINEL_PATH` and `check_scope.MUTATION_SENTINEL` are two literals in two files, and if they ever disagree the guard watches nothing while looking entirely healthy.

The canary breaks the sentinel check rather than the sentinel itself, since a guard that silently stops guarding is this defect's own failure mode.

Self-review found nothing further. The one judgement worth recording is what was deliberately not built: `check_gate_bite` could restore the mutated file itself, since the sentinel names it, but a `git checkout` would also discard any legitimate uncommitted work in that file, which during a phase build is the normal state. Refusing and naming the file leaves the destructive step with the operator.

## Next Agent Bootstrap

Phases 10 through 16 are declared at `future` with skeleton contracts, and the repo is idle.

One thing is still owed before phase 10 can start: `AGENTS.md` forbids the ingestion that ruling 5 lifts, and the lift needs a bound expressed as a number, which is a `contract-update` waiting on Taylor.

Phase 10's own contract stage inherits two unverified inputs: GTOpen's determinism has never been checked by running one config twice and diffing, and no solve time was ever recorded.
