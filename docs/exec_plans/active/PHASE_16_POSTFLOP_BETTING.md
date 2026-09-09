# ExecPlan: Phase 16, Postflop That Can Bet

Contract: `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md`
Lane: worktree `~/projects/poker-bot-worktrees/phase-16`, branch `phase/16-postflop-that-can-bet`,
opened from `main` at `19beb97`.
Loop pointer: `verification/loop_runs/16.yml`. Driver: `uv run python scripts/loop_stage.py --phase 16`.

**Never work in `~/projects/poker-bot`.** That checkout holds `main` and is the integration tree.

## Objective

Replace the conservative postflop fallback with flop play that can bet and raise, driven by a
committed solved artifact, and leave turn and river refusing the way an uncovered preflop spot
refuses today.

Three of the five judgment calls are ruled (Taylor, 2026-08-19): flop only, all 1,755 canonical
flops, a small head of common preflop lines. Decision 4 is unanswered and `frozen-into-data`, so
stage 3 halts on it. Decision 6 is new, filed at stage 1 from a measurement rather than from
reading, and halts with it.

The gate this phase closes is `pytest_postflop_betting` plus whatever the contract adds, with
`check_gate_bite` proving each new command's canary bites.

## Scope

Approved at stage 1 (`contract-update`), which is where this plan is written:

- `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` - a skeleton, here to be written rather
  than corrected.
- `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` - carries the three
  rulings, two blank answers, and three claims this lane has measured to be false.
- `reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/**`.

Standing scope covers `CURRENT_TASK.yml`, `phase_status.yml`, `backlog.yml`, the loop pointer, the
generated documents, `docs/exec_plans/**`, and `reports/active/**`.

Expected at later stages, each needing its own dated `scope_change_log` entry when it is opened:

- Stage 4: `tests/test_postflop_betting.py`, `verification/mutations.yml`, and
  `scripts/run_verify.py` for command registration only. `check_repo_consistency` requires the
  test file to exist and hold at least one test the moment the command id is registered, so the
  two land together or neither lands.
- Stage 5: `tests/**` and `verification/**` leave scope. The freeze is what stops the thing being
  tested and the test for it being written by the same mind.
- Stage 6: the postflop key module, the artifact schema and importer, the strategy, the solve
  driver, the report generator, and the query-shape extension the phase needs.
- Stage 6 or later, and only after stage 3 has a human answer on decisions 4 and 6:
  `data/artifacts/postflop/**`. This is the committed data the phase exists to write and the one
  path no lane opens on its own judgment.
- Stage 6, with the artifact and not before it:
  `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json`. The contract requires
  that card regenerated because its `headroom_bytes` counts the whole artifact tree, and the
  stage-1 review found the obligation had no scope to land in. It is a preflop path serving a
  postflop obligation, which is why it needs naming rather than assuming.
- Stage 9: `reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md`.

Forbidden throughout: `data/raw/**` and `data/processed/**` as an existence rule; PokerNow
automation; browser or platform observation; runtime solver calls; LLM-backed poker decisions; a
training UI; and any rank-texture mapping of an unsolved board onto a solved one, which decision 2
deferred as `POSTFLOP-BOARD-ABSTRACTION` rather than rejected.

## What stage 1 measured, and why it changes the phase

Four things were read as established and are false or incomplete. Each is a number this lane
computed rather than a reading of prose, because `docs/V2_ROADMAP.md` already records one wrong
premise about this phase being quoted into two files and read back as fact.

**1. The committed artifact does not fit, and by more than a margin.** Three files still say
`data/artifacts/**` is covered by no size check: this phase's own decision list, line 67;
`docs/V2_RULING_MITIGATIONS.md` at 103 and 259; `docs/V2_ROADMAP.md` at 161. It has been capped at
20 MB since `2430894`, 2026-08-18, in `DIRECTORY_BYTE_LIMITS`. The tree holds 5,197,325 bytes, so
headroom is 15,774,195 bytes.

Against that, the exact size of a flop artifact in the format the preflop chart uses:

- 1,755 canonical flops, recomputed here rather than quoted.
- 1,176 hero combos per flop, and 1,286,792 hero-combo classes summed over all 1,755 flops once
  the board's own suit symmetry is collapsed. That collapse is exact and free; it is the only one
  decision 2 permits. It saves 1.6x, not the 7x that would make a flop cell chart-sized. The mean
  is 733 classes per flop against the preflop chart's 169 per spot.
- 14.8 bytes per action weight measured off the committed chart's `action_weights` block in
  compact JSON, 26.8 as actually committed with `indent=2`.

**The finding is the node count, not a ratio against one encoding.** Fifteen megabytes of headroom
buys, for **one** preflop line, on the order of **one hero decision node** - and that holds in any
JSON encoding, which is why no format change answers it. In the leanest plausible JSON, action
names hoisted to one array, hero's classes as a parallel array in canonical order, three-decimal
floats and one free weight per class, one two-action node for one line measures 7,740,095 bytes -
two independent builds agreed to within 38 bytes, both at 0.4907x -
which is 0.49x the headroom: it fits, with room for a second node. That same encoding buys 2.04
nodes at two actions, 1.02 at three storing two free weights, and 0.68 storing all three. A flop is
not one decision - hero acts, villain answers, hero faces a bet or a raise - and decision 3 asks
for a head of common preflop lines, plural. Several nodes across several lines is what the phase
needs, and one node for one line is what the cap affords.

The chart's own format is worse, and the figures are given as pairs that recompute from the rates
above rather than from any other rate. One line, one node, only check and bet: 36 MiB compact, 66
MiB as committed, 2.4x and 4.4x. Ten hero nodes at three actions: 544 MiB compact, 986 MiB as
committed, 36.2x and 65.6x. Building the structures directly rather than multiplying the rate gives
43, 76 and 1,007 MiB, so the multiplications err low; those three are the independent numbers
verification's builds, recorded in its note beside this stage's. Compression is not available:
`import_preflop_artifacts` globs `*.json` and reads text.

An earlier draft of this paragraph led with the 2.4x, gave 99 MB and 1,481 MB for the two
as-committed figures and 24x and 98x for the ten-node row, and the independent numbers review at
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-01-numbers-verification.md` held the
stage over all of it. The two as-committed figures had silently used 40.227 bytes per weight, the
whole committed file over its weight count, in place of the 26.789 stated one line above; that rate
charges the chart's `spots`, `arrival_ppb`, `arriving_reach_bp` and `audit_fields` blocks against
every weight when those scale per spot. The ten-node compact figure had dropped the third action
and so ran low while the other two ran high, which is why the paragraph could not be repaired by
scaling. And leading with 2.4x invited the one ruling that would be wrong, since a format change
defeats 2.4x and does not touch the node count.

This does not overturn a ruling. Decision 1 fixed the depth and decision 2 the breadth, both on
solve-time grounds, and disk was never measured. What it says is that the artifact's *format*
cannot be the preflop chart's format, and every way out is a human's call rather than a lane's:
a binary encoding on the `preflop_eq169.bin` precedent, fewer lines, a raised cap, or a narrower
per-node commitment. Filed as decision 6, `frozen-into-data`. `check_file_sizes.py` says in its
own comment that exceeding a limit here "is a halt and a decision, not a number to raise", and
`ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` already records phase 14 measuring 4.5x to 26x over
the same cap for a different reason.

**2. The query cannot express a flop spot.** `StrategyQuery` carries `preflop_actions` and no
postflop history at all, and `SeatAction` rejects `"bet"` because
`_PREFLOP_HISTORY_ACTIONS` is `("fold", "check", "call", "raise")`. `simulator/run.py:227` appends
history only on preflop. A flop is not one decision: hero acts, villain answers, hero faces a bet
or a raise, so flop-only still needs within-street history. Extending the query is a change to a
shape phase 03 froze and phase 13 last widened, and it bumps
`DECISION_AUDIT_SCHEMA_VERSION` from 3. The contract owns this as its first criterion group,
because it is the "format before data" obligation decision 3 names: adding spots at a fixed key is
additive, changing what the key can express re-derives every committed cell.

**3. The precedent decision 3 names is the wrong file.** The 2026-09-06 annotation says the
corpus is what ranks the lines and points at `reports/active/latest_refusal_inventory.txt`. That
file is built from self-play - seed 20260812, 600 hands, two seatings out of
`profiles/seating.py` - by `scripts/generate_profile_comparison_report.py`. The corpus-fed sibling
is `reports/active/latest_sample_refusal_inventory.txt`. The ruling's substance survives intact and
its method does not: what ranks corpus lines is `ComparisonRow.asked_spot_key`, which is already
populated on every keyed row rather than on refusals only. Over the committed 499-hand corpus that
is 3,048 decision points across 127 distinct spot keys, and the head agrees with the artifact's own
solve-derived `arrival_ppb` order on the top ten but for two swaps - a cross-check worth keeping.
Two caveats belong in the contract: those keys are post-substitution, since the corpus's median
open is 2.25bb and every key reads `@2.5`; and reaching a decision point is not seeing a flop, so
the filter decision 3 actually needs is a different query and nothing computes it today.

**4. A postflop key can break a reader that nobody would think to look at.**
`self_play_reference.py` recovers spot keys from the self-play inventory by scraping any token that
starts with `t` and holds at least three slashes, and it raises rather than returning empty. A
postflop key shaped like the preflop one pollutes that reader; one shaped differently may break it.

## Delegation Plan

Complete before implementation. Subagents are authorized and `AGENTS.md` is explicit that review
is never the writer's own, whatever a session records about its own capability. Lanes are worker
subagents in this one worktree; the coordinator owns every commit.

- Worker lanes: R1 contract review (stage 1), R2 decision review (stage 2), T1 tests (stage 4),
  K1 the postflop key and query shape (stage 6), A1 the artifact schema, importer and library
  (stage 6), S1 the solve driver and the committed artifact (stage 6, gated on stage 3), B1 the
  betting strategy and the refusal boundary (stage 6), P1 the pot-odds river call (stage 6,
  decision 5), E1 the report generator and command registration (stage 6-7), F1 the audit packet
  (stage 9). Each is one bounded worker subagent.
  - **R1 - contract review.** Read-only against the question the driver prints: is any acceptance
    criterion unfalsifiable, a restatement of the phase title, or satisfiable without doing the
    work it names. Must also re-derive the four numbers in the section above from the repo rather
    than accept them, because a contract written on a miscounted floor is a contract that commits
    the phase to the wrong artifact.
  - **R2 - decision review.** Read-only over the decision list once decision 6 is filed: whether
    each item's reversibility class is right, and whether decision 6 states the options without
    steering to one.
  - **T1 - tests.** Authors the phase's tests before any implementation exists, expected red.
    Includes the canary for this phase's own new command, which phases 08 and 09 both omitted and
    both had caught at stage 7.
  - **K1 - key and query.** The postflop spot key, its validator, the query-shape extension, the
    audit schema bump, and `postflop_action_order` in `poker_core/positions.py`, which
    `positions.py:59-67` already anticipates by name and does not provide.
  - **A1 - artifact.** Schema, strict importer, library, fail-closed lookup, and the checksum. In
    whatever encoding decision 6 rules, which is why A1 cannot start before stage 3.
  - **S1 - solve driver and data.** Drives GTOpen's postflop routes and writes the artifact. Three
    of its four routes were driven end to end on 2026-08-23 and 2026-08-24; the batch `REPORTS`
    route over a canonical flop subset is recorded UNRUN in `docs/GTOPEN_SOLVER_NOTES.md` and must
    not be assumed to work.
  - **B1 - strategy.** Flop play that bets and raises, with turn and river refusing by code rather
    than folding by default, replacing `PostflopFallbackStrategy`'s
    `CODE_FOLD_ON_THE_FLOP` path. Five mutation canaries pin exact lines in
    `postflop_fallback.py` and `composite.py`; B1 owns re-pointing each with its claim unchanged,
    the way phase 13's L2 did, never retiring one.
  - **P1 - pot-odds river call.** Decision 5, runtime-reversible, behind an explicit flag,
    reporting the frequency it fires rather than claiming it is right. Needs an equity number that
    does not exist in `src`: `hand_cannot_lose` returns a short-circuiting bool and raises on a
    flop board, and the counting version `holding_counts` lives in a report script.
  - **E1 - report and gate.** `pytest_postflop_betting`, the generator, its self-validation, and
    the `COMMANDS` entry.
  - **F1 - packet.** The prose the phase exists for, under a 500-line cap.
- Ownership: R1 and R2 write only under `reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/`
  and never touch what they review. T1 owns `tests/**` at stage 4 only. K1 owns
  `solver_artifacts/postflop_key.py`, `strategy/contract.py` and `poker_core/positions.py`. A1
  owns the postflop schema, importer and lookup modules. S1 owns the solve driver and
  `data/artifacts/postflop/**`. B1 owns `strategy/postflop_fallback.py` and `strategy/composite.py`.
  P1 owns the equity helper it lifts into `src`. E1 owns
  `scripts/generate_postflop_betting_report.py` and the `COMMANDS` block in `scripts/run_verify.py`.
  F1 owns the audit packet. The coordinator owns `CURRENT_TASK.yml`, the contract, this plan,
  `backlog.yml`, `verification/mutations.yml`, the loop pointer, every merge, the gate, and the
  regeneration of the solver export source card, whose `headroom_bytes` counts the whole artifact
  tree and will red `test_the_committed_export_sits_under_the_limit_with_stated_headroom` the moment
  any flop artifact lands. No two lanes write the same file at the same time.
- Expected outputs: each lane returns a patch confined to the files it owns, the commands it ran
  with their output, a changed-file summary, and the frozen tests it made pass or found failing.
  R1 and R2 return notes with the three required headings, blockers marked as blockers. T1 returns
  a per-test statement of the behaviour asserted and the canary that proves it bites. S1 returns
  measured solve time and peak memory per flop against MAINT-26's figures, and says plainly when a
  route it needed was one of the unrun ones. E1 returns the report text.
- Status: R1 planned, dispatched once the contract is drafted. R2 planned, stage 2. Every other
  lane planned and not dispatched, because stage 3 halts on decisions 4 and 6 and four of them
  build against whatever those answers are.
- Integration order: R1 before stage 1 advances. R2 before stage 2 advances. T1 alone at stage 4,
  then the freeze. At stage 6, K1 first and alone, because every other lane keys against the shape
  it defines; then A1; then S1 and B1, S1 first where they share the artifact's read path; then P1
  and E1 in parallel on disjoint files. The coordinator runs the phase's own commands after each
  merge and the full gate only after E1.
- Review handoff: an independent read-only reviewer reads each stage's diff against the question
  the driver prints, writes to
  `reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-NN-name.md` with the three required
  headings, and never edits what it reviews. Stage 8 gets two, one mechanical and one domain, and
  the domain reviewer is briefed to judge the poker rather than the code's fidelity to this
  contract. The reviewer that matters most is T1's at stage 4, because a wrong test authored there
  survives the freeze and every mechanical check after it. The domain reviewer at stage 8 is asked
  one question no shape check can answer: whether a bot that bets a flop and then refuses every
  turn is better or worse at the table than one that never bets, since decision 1 accepted that
  seam explicitly.

## Slices

- [x] S0 Precheck. Lane opened from `main` at `19beb97`, lock held, tree clean, scope seeded with
      its `scope_change_log` entry.
- [ ] S1 Contract. Real criteria, this plan, decision 6 filed, the four stale claims corrected,
      R1's review with every blocker resolved.
- [ ] S2 Decisions. Every judgment call carries a reversibility class; R2 reviews.
- [ ] S3 Human gate. Decisions 4 and 6. Expected to halt.
- [ ] S4 Tests. Red on assertions, frozen after. Canaries include this phase's own command.
- [ ] S5 Freeze. `tests/**` and `verification/**` leave scope.
- [ ] S6 Build. Every command the contract declares green.
- [ ] S7 Gate. Full `run_verify.py` plus `check_gate_bite`.
- [ ] S8 Review. Two reviewers, mechanical and domain.
- [ ] S9 Audit. Packet with a number a reader can recompute by hand.
- [ ] S10 Closeout. Phase completed, plan filed, tag, idle, clean.
- [ ] S11 Advance. Policy says `auto_advance: false` for phase 16.

## Verification

- Command IDs this phase adds: `pytest_postflop_betting`, plus a `generate_*` id for the report
  once E1 names it. Both go in `COMMANDS` in `scripts/run_verify.py` and in the contract's
  frontmatter, and nowhere else.
- Report: `reports/active/latest_verify.txt` plus this phase's own report, under the 300 KiB cap
  that binds `reports/active/*.txt`.
- Gate: `uv run python scripts/run_verify.py`, which derives the gate from `phase_status.yml` and
  every active or completed contract's frontmatter.
- Canary obligation: every new command id carries a mutation in `verification/mutations.yml`
  authored at stage 4, and `check_gate_bite` must prove each bites. A `must_fail` id that the
  derived gate does not run is rejected by `check_repo_consistency`.

## Outcome

Not yet. Stage 1.

## Next Agent Bootstrap

**This section is the single source for what is true now.**

- Worktree `~/projects/poker-bot-worktrees/phase-16`, branch `phase/16-postflop-that-can-bet`.
  Never work in `~/projects/poker-bot`.
- Next command: `uv run python scripts/loop_stage.py --phase 16`. Six lanes have pointers in this
  worktree, so `--phase 16` is required rather than optional.
- Current state: stage 1, `task_mode: contract-update`, `base_commit` `19beb97`. The contract is
  being written for the first time. The gate is red on two things by design between stage 1 and
  stage 4: `pytest_postflop_betting` is declared in the contract's frontmatter and not registered
  in `COMMANDS`, and that is the same state the phase 17 lane sits in.
- Open, and not to be invented: decision 4, the exploitability target and whether a solve
  reproduces, which the loop policy says is inherited from phase 10's measurements and halts if
  they were never produced; and decision 6, the artifact encoding, filed at stage 1 from the
  measurement above. Both are `frozen-into-data`. Neither a reviewer nor a coordinator can supply
  either.
- What this phase must get right up front is the postflop spot key. Adding spots later is additive;
  changing what the key can express re-derives every committed cell.
