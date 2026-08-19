# MAINT-20 - Parallel Phase Loop (Fleet)

## Objective

Let several phases run at once, each in its own worktree, and make every point that waits on a human visible in one place so a lane pauses rather than guesses.

The loop today runs exactly one phase.
`verification/loop_state.yml` holds a single `phase_id`, `.git/poker-loop.lock` claims the one worktree, and `depends_on` is validated as a required frontmatter key in `scripts/check_contracts.py` and enforced nowhere.

This task builds the machinery.
It does not change any contract's `depends_on`, because relaxing the declared chain is a semantic contract change that belongs in its own `contract-update`.

## Scope

Approved:

- `scripts/loop_fleet.py`, `scripts/review_queue.py` - new
- `scripts/loop_stage.py` - per-lane state, `--phase`, worktree-resolved lock
- `scripts/run_verify.py` - register the two new command IDs
- `scripts/check_repo_consistency.py` - `depends_on` must be acyclic and name real phases
- `tests/test_loop_fleet.py` - new, because `tests/test_loop_machinery.py` sits at 680 of its 700-line cap
- `verification/mutations.yml`, `verification/freeze.lock`
- `docs/LOOP.md`, `AGENTS.md`

Forbidden: `data/raw/**`, `data/processed/**`, and every phase contract.
Phase 10 is live in the primary worktree at stage 5 and is not touched by this task.

## Delegation Plan

- No-delegation exception: this session is explicitly instructed not to spawn subagents, so implementation and review are both coordinator-owned. Self-review notes stand in for the independent read-only pass and are recorded in the Outcome section.

## Slices

- [x] Per-lane state: `verification/loop_runs/<phase>.yml` and `loop_stage.py --phase`. The live phase-10 pointer is deliberately **not** migrated; `state_path_for` writes back to whichever file the lane already uses, because moving it would touch a path phase 10's own task never approved.
- [x] Worktree lock resolved through `git rev-parse --absolute-git-dir`.
- [x] `scripts/loop_fleet.py`: `--plan`, `--status`, `--tick`, `--start-lane`, `--integrate`.
- [x] `scripts/review_queue.py`: the pause board, derived from six existing sources.
- [x] Registry, `depends_on` consistency check, four canaries, re-freeze.
- [x] `docs/LOOP.md` and `AGENTS.md`.

## Verification

- `pytest_loop_fleet` (32 tests), `check_repo_consistency`, `check_test_freeze`, `check_scope`, `check_gate_bite`
- `scripts/run_verify.py` full gate: 36 commands, all green, `check_gate_bite` catching all 37 mutations
- `reports/active/latest_verify.txt`

One planned command was dropped. `check_review_queue` cannot exist: the board is derived from whichever worktrees happen to be on the machine, so a committed copy would differ between machines and CI could never verify it. The board's shape is pinned by `tests/test_loop_fleet.py` instead, and `docs/LOOP.md` says why nothing about it is committed.

## Outcome

The fleet runs. `--plan` reads the contract graph off `main`, `--status` and `--tick` read the live phase-10 lane in the primary worktree at stage 5 without disturbing it, and `review_queue.py --list` reports the one real ask the repo currently has, which is phase 16's missing postflop source.

Parallelism is built but not yet available: every contract still declares the straight chain `10 -> 11 -> ... -> 16`, so `--plan` correctly reports one eligible phase at a time. Adopting the roadmap's looser graph is a semantic contract change and is the next task, in `contract-update` mode.

### Self-review

No independent subagent review: this session is instructed not to spawn subagents, so the pass below is self-review over the task's own diff.

Five findings, all fixed in this task:

- `--tick` shelled out with `--phase` unconditionally, which broke against the live phase-10 lane because that branch runs a driver predating the flag. Fixed by passing `--phase` only where a worktree holds more than one pointer. This was caught by running `--tick` against the real lane rather than a fixture, which is the only place it could have shown up.
- `lanes()` would report one phase twice in a worktree holding both a per-lane pointer and the single-lane file it came from. Now deduplicated on `(phase, worktree)`.
- `loop_stage.py --halt` with no lane running would have written `verification/loop_runs/None.yml`. Now refuses with a message.
- `blockers()` re-read the policy off `main` once per phase, so planning spawned a `git show` per phase per question. `show()` is cached.
- A branch slug could end in `-` after truncation.

Two things this task does not resolve, both stated rather than hidden:

- Merging a lane rewrites `verification/freeze.lock`, which softens the freeze. Filed as the fourth known gap in `docs/LOOP.md` with the argument for why integrator-owned rebuild is still safe.
- Real simultaneity needs one session per worktree. The driver coordinates lanes; it does not run them.

## Next Agent Bootstrap

Work happens in the linked worktree `/Users/taylorsprouse/projects/poker-bot-worktrees/maint-loop-fleet` on branch `maint/loop-fleet`, cut from `main` at `4688033`.
The primary worktree holds phase 10 at loop stage 5 and must be left alone.
Next command: `uv run python scripts/run_verify.py` from the maint worktree.
