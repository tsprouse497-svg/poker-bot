# MAINT-13: Write The Proposed V2 Sequence Down

## Objective

V1's phase sequence is finished rather than paused: `phase_status.yml` holds ten completed phases and no future ones, and `docs/ROADMAP.md` says only that the v1 sequence is locked.
Work proposed now therefore has no arc to sit in, and arrives as one-off phases bolted onto a closed v1.
This task records the proposed v2 sequence as a document a future agent can read, evaluate, and argue with.

It proposes and does not declare.
`phase_status.yml`, `verification/loop_policy.yml`, the phase contracts, and the V1 boundaries in `AGENTS.md` are all untouched, because declaring phases and lifting boundaries are decisions this task is not authorised to make.

## Scope

Approved: `docs/V2_ROADMAP.md`, `docs/ROADMAP.md`.

Forbidden here, and named because the temptation is real: `phase_status.yml`, `verification/loop_policy.yml`, `docs/phase_contracts/**`, `backlog.yml`, `AGENTS.md`.
A document that describes a plan and a repo that has adopted one are different states, and this task produces only the first.

## Delegation Plan

- No-delegation exception: two documentation files, written from a plan already reviewed with Taylor across this session. There is no lane to bound and nothing an independent implementer would own.

## Slices

- [x] Slice 1: `docs/V2_ROADMAP.md`, carrying the starting position, the boundary rulings still open, the seven proposed phases in dependency order with the backlog ids each would close, and what adopting it would involve.
- [x] Slice 2: a pointer from `docs/ROADMAP.md`, so an agent that starts where the roadmap lives finds the proposal instead of concluding there is no further work.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

Full gate green.
The proposal is committed and marked as a proposal in its own first lines, so no later reader can mistake it for the locked sequence.

## Next Agent Bootstrap

The repo is idle with phases 00 through 09 complete and nothing declared after them.
`docs/V2_ROADMAP.md` proposes seven phases; `phase_status.yml` knows about none of them, which is the honest state and not an oversight.

Three boundary questions in that document are Taylor's and are unanswered: whether large hand-history ingestion lifts for a single player's own hands, whether the UI package stays deferred, and whether PokerNow automation stays out of v2.
Four more are unanswered inside proposed phase 10: rake, open size, whether limps are in the solved tree, and whether an unlicensed solver can be the origin of committed ranges.

Adopting the sequence is a separate task and needs `contract-update` for the `AGENTS.md` boundary changes before any phase starts.
