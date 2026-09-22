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

- Stage 4: `tests/**`, `verification/mutations.yml`, and `scripts/run_verify.py` for command
  registration only. `check_repo_consistency` requires the test file to exist and hold at least
  one test the moment the command id is registered, so the two land together or neither lands.
  **`tests/**` and not just the new file**, corrected 2026-09-10: the contract requires the frozen
  tests of completed phases that assert against the query shape to be migrated in this task and
  authored at stage 4, and says the set is swept rather than inherited as a count, so the files it
  touches cannot be listed in advance.
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
    `CODE_FOLD_ON_THE_FLOP` path. Six mutation canaries pin exact lines in
    `postflop_fallback.py` and `composite.py`; B1 owns re-pointing each with its claim unchanged,
    the way phase 13's L2 did, never retiring one.
  - **P1 - pot-odds river call.** Decision 5, runtime-reversible, behind an explicit flag,
    reporting the frequency it fires rather than claiming it is right. Needs an equity number that
    does not exist in `src`: `hand_cannot_lose` returns a short-circuiting bool and raises on a
    flop board, and the counting version `holding_counts` lives in a report script.
  - **E1 - report and gate.** `pytest_postflop_betting`, the generator, its self-validation, and
    the `COMMANDS` entry.
  - **F1 - packet.** The prose the phase exists for, under a 500-line cap.
  - **C1 - contract fold-in.** Added 2026-09-10, between stage 3 and stage 4. Rewrites
    `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` so the thirteen rulings listed under
    "What the fold-in rewrite has to absorb" are stated as acceptance criteria, inside the
    300-line cap the contract sits 11 lines under. It is a lane rather than coordinator work
    because the coordinator wrote every one of those thirteen rulings into the decision list,
    and a rewrite that compresses existing criteria to make room is exactly the edit where the
    author's memory of what a sentence was for substitutes for the sentence. C1 writes only the
    contract and copies conclusions from the decision list rather than re-arguing them.
  - **R3 - fold-in review.** Read-only, and it is not C1. One question, taken verbatim from the
    failure that `AN-AMENDMENT-TO-A-SKELETON-CONTRACT-IS-DELETED-BY-ITS-OWN-STAGE-1` records:
    **does every amendment that went in come out**, checked against the decision list and the
    backlog ids rather than against the new contract's own readability. Also asked whether any
    criterion the rewrite compressed lost a falsifiable clause, because 13 rulings into 11 free
    lines is a compression budget and compression is where an obligation becomes a sentiment.
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
- Status, 2026-09-14. R1 done, stage 1, blockers resolved. R2 done, stage 2. Stage 3 ran two
  independent reviews, `stage-03-human-gate.md` over eight rounds and `stage-03-decisions-poker.md`
  over the poker; both are closed and both are on disk. C1 done, three passes: the fold-in, then
  R3's two blockers, then one restored predicate. R3 done, two rounds, both blockers verified fixed
  and no new ones. T1 done, stage 4. Stage 4 then ran **two** independent reviews rather than one -
  `stage-04-tests-mechanical.md` and `stage-04-tests-poker.md`, neither having written the tests
  and neither having seen the other's note - because stage 4 is the stage whose mistakes the freeze
  preserves. Between them they found **eight blockers**, every one re-measured by the coordinator
  before it was acted on. T2 repaired all eight; R4 verified the repair at
  `stage-04-repair-verification.md`. X1 filed seven findings that earlier stages had named in prose
  and never created. Every stage-6 lane is planned and not dispatched.
- Two lanes were added at stage 4 and neither was in the plan written at stage 1. **T2**, repair,
  because the agent that wrote a test is not the one to judge whether the fix to it is real, and
  eight blockers is a rewrite rather than a touch-up. **X1**, backlog, because the gate's
  backlog-integrity check was red on twenty id-shaped tokens resolving to no item and that had to
  be sorted by reading twenty notes rather than by pattern - X1 came back saying six of the
  thirteen the coordinator handed it were already filed under corrected names or deliberately
  withdrawn, which is the result a lane produces and a coordinator working from its own list does
  not.
- Four lanes were added on 2026-09-16, when a fresh coordinator picked the stage up. **W4**, the
  report's fabricated `servable` column. **W5**, the solve driver's fail-open defaults. **C2**, a
  read-only diagnosis of the seven red frozen tests, which is a lane rather than coordinator work
  for the reason the whole phase turns on: the coordinator does not get to decide that a test its
  own stage reddened was wrong. **V1**, the consolidated stage-6 review, which is none of the four.
  W4 and W5 each returned a finding outside its brief and both were real. W4: the ranking was never
  sorted on `servable` either, so the prose claiming the two orders differ was false twice over and
  fixing the count alone would have left it false. W5: `state` is read with the same fail-open
  `.get` as the two named, and an absent `state` ends the poll on its first look, so a solve still
  running commits as converged - worse than either defect on the list. Neither was on the list a
  coordinator working from the previous session's notes would have handed out, which is the
  argument for the lane and against the checklist.
- Four lanes are added on 2026-09-20, when the halt lifted and the lane resumed. **D1**, the solve
  campaign: run the four planned cells against the merged chart, commit the cells and the index,
  and report measured wall clock, peak memory and achieved exploitability per cell against
  MAINT-26's figures. **D2**, decision 15's deep convergence check: one cell re-solved to the 1,200
  cap with its frequencies diffed against its 240-iteration run, which is a measurement whose
  answer the campaign's own driver must not be allowed to supply. **D3**, the solver export source
  card, whose `headroom_bytes` counts the whole artifact tree and reds six tests the moment a flop
  artifact lands. **V1**, the consolidated stage-6 review, which is none of D1, D2 or D3 and none
  of the lanes that built any of this.
- **D1 is coordinator-owned and D2 and D3 are not.** The campaign writes no code: it runs a
  committed script, and what it produces is bytes whose correctness is judged by the frozen tests
  and by D2's independent measurement, not by whoever typed the command. A lane there would own
  nothing it could get wrong that the gate does not already catch. D2 and D3 both produce a number
  this lane's own record then rests on, which is the shape that needs an author who is not quoting
  their own campaign back to themselves.
- Status: 2026-09-21. **D4 done**: decision 18b's fifth cell, code only, committed at `52fa2f9`.
  It returned two corrections from outside its brief, both re-measured before they were believed -
  `check_file_sizes` has no pattern covering `scripts/` at all, so the cap three earlier extractions
  in this stage were paid against does not exist for that file; and this plan's "four files at
  exactly their cap" is six under `src` at 500 and ten test files at 700. **D5 done**: the harvest
  refusal is arithmetic, not a group mismatch, and the docstring that said otherwise was wrong about
  the solver's own guarantee. **W6 done**, committed at `7b712c3`: full-precision arenas, verified
  rather than asked for, plus decision 20 and five filed findings. **D1 done**, committed at
  `479aaf2`: four cells and the listed-not-held fifth, all converged. **D3 done**, committed at
  `7d6866f`: the source card restamped and `base_commit` moved past the merge. **R2 done**,
  committed at `de62604`: the last red, plus two more vacuous checks in the same file that nobody
  asked about. **D2 running**: determinism and decision 15's deep convergence check. **V1 not
  dispatched**, and it is the stage's own review - none of the seven above may write it.
- **Each of the four lanes asked one question returned a finding outside its brief, and all of them
  were real** - D4 two, D5 one, W6 three, R2 four. The two that cost the most were on no list a
  coordinator would have handed out. W6 found that the memory guard which decided the arena question
  over-reads its own input by 4.86%, so the 0.13% overage Taylor ruled on was partly our own
  arithmetic, and the decision is open again on that ground. R2 found that the refusal
  reconciliation in the report was `sum(x) == sum(x)` and could not fail on any input, having been
  asked only about the byte figure beside it. The pattern held at stage 4 too, where W4 and W5 each
  returned one. A brief is a floor rather than a scope.
- **What the merge settled, and the one thing it did not.** MAINT-34's re-solve landed on this lane
  at `d7712d5`. Re-measured here rather than taken on report: at `t6/d100/BB/BTN:raise@2.5` the big
  blind's call branch now holds 88, 77, 66, 55, 44 and 22 outright and splits 99 and 33, where every
  pair from aces down to fives read raise 1.0 before. That is the line all four planned cells solve -
  `BTN_OPEN_BB_CALL` in `scripts/solve_postflop_sample.py:370-379` - so the cells sit on the side of
  the fix that worked. The spot the fix did not reach, `t6/d100/BB/SB:raise@2.5`, raises every pair
  sevens and up and flats sixes and below, before and after; no planned cell uses it, and
  `RE-SOLVE-THE-PREFLOP-CHART-WITH-A-REALISTIC-BLIND-THREE-BET` is explicit that a c-bet frequency
  measured there is not evidence about the fix either way. If the campaign ever grows a second
  preflop line, that entry is the table it picks from.
- W5's repair took `postflop_solve_driver.py` from 500 to 527 against a 500-line cap that compares
  `> limit`, so the module had zero headroom before it was touched. Ruled: extract, do not compress,
  which is the third extraction in this stage and the third one a lane reported rather than slipped
  in. The seam is what a server answer is and how to read one, against what a solve is and how to
  drive one.
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
- [x] S1 Contract. Real criteria, this plan, decision 6 filed, the four stale claims corrected,
      R1's review with every blocker resolved.
- [x] S2 Decisions. Every judgment call carries a reversibility class; R2 reviews.
- [x] S3 Human gate. Halted as expected, then all thirteen decisions ruled. Two reviews closed
      the stage; the contract fold-in and its own review are folded in here rather than deferred,
      because the gate cannot pass between stage 1 and stage 4 and closing out through it to run
      the rewrite as a separate task is not available.
- [x] S4 Tests. Six new files, three migrated, three canaries, both command ids registered. Two
      independent reviews, eight blockers, all repaired and verified. 54 tests execute assertions,
      22 failing on assertions and 32 passing against what already exists; no collection error, so
      nothing is frozen having never run. Decision 14 filed and taken on its recorded default.
- [x] S5 Freeze. `tests/**` and `verification/**` leave scope.
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

Not yet. Stage 4 closed 2026-09-14; stage 5, the freeze, next.

## Next Agent Bootstrap

**Rewritten 2026-09-22 at stage 9, replacing one that was accurate on 2026-09-16 and wrong by the
end of that session. The lane is no longer halted and the sample is committed.**

- Worktree `~/projects/poker-bot-worktrees/phase-16`, branch `phase/16-postflop-that-can-bet`.
  Never work in `~/projects/poker-bot`, which holds `main`.
- Next command: `uv run python scripts/loop_stage.py --phase 16`. Several lanes have pointers here,
  so always name the phase.
- **Stage 9 of 11, running.** `task_mode: implementation`. Stages 0 through 8 are closed: the gate
  went green on all 50 commands with `check_gate_bite` among them, and every blocker across the five
  review notes in `reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/` is marked resolved
  against a measurement.
- What is left is bookkeeping and one gate run. Stage 10 is the closeout - `phase_status.yml` to
  `completed`, the ExecPlan filed to `completed/`, the tag, `CURRENT_TASK.yml` back to idle, and the
  gate run again on the result. Stage 11 merges the lane into `main`. The gate recorded in
  `reports/active/verify_results.json` is the stage-7 run and `generate_postflop_betting_report.py`
  changed after it during the stage-8 repairs, so **the closeout run is the one that counts**.

### What this phase shipped, and the sentence it is not allowed to say

Four committed flop cells on three boards plus a fifth the index lists and this clone does not hold,
all at full precision against the chart MAINT-34 re-solved, all converged inside the ruled 0.3% of
pot, all re-imported clean, and all proved reproducible by re-solving in a second process against a
restarted server.

**The bot still does not bet at a table, and the packet says so.** Twenty thousand deals give zero
bets, zero showdowns and two postflop decisions, both check. Three boards are 40 of 22,100 flops,
and nine of the eleven successors to the committed cells' own actions are flop nodes nobody solved,
so there is no two-move sequence in the artifact. Decision 25 is Taylor's ruling to close on
machinery rather than coverage and to state that plainly; the sentence "the bot bets a flop and then
refuses every turn" is **struck** and must not reappear, because the turn is never reached.

### The rulings a later phase must not quietly undo

- **Decision 20**: solves run at full precision, `SOLVER_COMPRESS=0`, verified off the built tree
  rather than assumed, with the memory ceiling at 0.40. Quantized arenas put a floor near 0.3% of
  pot under every exploitability this phase measured.
- **Decision 21**: the continuation-bet frequency never appears without the caller's lead frequency
  beside it. On the monotone board that is 99.88% against a caller who has already bet 52.68% of
  its range, and the first number alone misleads.
- **Decision 23**: the small-pair ladder is not smoothed. We ship what the solver produced.
- **Decision 24**: the rented box binds the campaign, not this sample. Every timing here is a laptop
  timing, and the determinism proof constrains this machine and nothing else.
- **Decision 25**: closed on machinery. A later phase funds the campaign.

### What a later phase picks up first

1. The nine uncommitted flop successors, which are what closure costs and are cheaper than new
   boards.
2. A second preflop line. The stage-8 domain review argues for the small blind's open rather than
   the cutoff's: the cutoff buys a replicate of the same positional lesson, the small blind buys the
   only frequent single-raised pot where the raiser is out of position.
3. Three contract sentences that read as false now the work is done, all unamendable because the
   contract is at 299 of 300 lines: `A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE`,
   `A-CONTRACT-CLAUSE-ASSERTS-A-GAP-ITS-OWN-PHASE-THEN-CLOSED` and
   `A-CONTRACT-CLOSED-LIST-ASSERTS-A-CLOSURE-ITS-PHASE-REFUSED-ON-EVIDENCE`. One fold-in rewrite
   clears all three.
4. `NOTHING-TESTS-THE-MODULE-THAT-DECIDES-WHAT-EVERY-COMMITTED-CELL-CONTAINS` and
   `NOTHING-CATCHES-THE-IMPORT-CHECK-THAT-REFUSES-A-BET-OFF-THE-COMMITTED-MENU`, which are the two
   places this phase found the gate looking rather than seeing.


### Things that will bite you

- **Four files sit at exactly their cap** with zero headroom: `postflop_artifact.py`,
  `postflop_betting.py` at 500, `test_postflop_artifact.py`, `test_simulator.py` and
  `test_postflop_query_recording.py` at 700. The next line added to any of them reds
  `check_file_sizes`. Extraction is ruled and has happened four times this stage; never compress prose.
- **`ruff format` is not in the gate** and 39 of 50 test files fail it. A file "at its cap" may have
  headroom the formatter would surface - that is how `test_postflop_key.py` got its two corrections.
- **Backlog integrity reads any hyphenated all-caps token in prose as a backlog citation.** It cost
  three gate reds in one session: a hand range written as a pair of capitalised ranks, and twice the
  name of a poker action written in capitals - once inside the sentence warning about it. There is no
  escape syntax, so the only defence is to write such things in lower case or in words. Any warning
  about this that names an example is itself a gate failure, which is why this one does not.
- **`postflop_betting.py` has no mutation canary at all** - the module that decides whether the bot
  bets. And `postflop-unplayable-size-imports` cannot bite on a `bet`: the on-menu and unplayable
  checks are jointly unsatisfiable there. `check_gate_bite` will find the second at stage 7.
  **Corrected 2026-09-21, after stage 7 found exactly that and lane C3 measured why.** The first half
  is right and now has numbers: on-menu caps the added amount at 0.80 of the pot before, unplayable
  needs it above what is behind, so both want a pot over 1.25 times the stack, and every committed
  cell is 5.5 or 7.315 against 97.5 - short by 16 to 22 times, over the whole committed domain of two
  single-raised lines. The conclusion drawn from it was wrong. Decision 14 ruled the menu check onto
  bets only, because a flop raise is `2.5x` the bet it answers rather than a pot fraction, so **a
  raise is exempt and nothing else catches it**: with the mutation applied
  `rainbow-dry-high-facing-a-bet` imports clean at any size, and without it the same cell is refused
  at 1.0001 times the stack. The canary bites exactly as the contract wrote it; the test was
  inflating the wrong kind of action. A prediction that a check cannot bite is a prediction to
  measure per action, not per module.
  **And the old test was worse than narrow, which the correction's own commit got wrong.** The
  stage-7 reviewer ran the matrix - old and new test against each check disabled alone and together -
  and the old test stayed **green** with the playability check disabled by itself. Its single-check
  kill set was empty rather than small: it died only when both checks went at once, so "it raised"
  never said which check had fired. The new test's kill set is a strict superset, so no coverage was
  traded, but the premise written into 5df2826 and its scope entry was false and is corrected here
  rather than left to mislead the next reader the way this canary's own description did.
- **A unit trap.** The key renders a bet as a percent (`@33`); `FLOP_BET_MENU` and
  `match_menu_fraction` are fractions (`0.33`); `CellAction` now carries `size_bb` as well. Three
  units, all pinned by frozen tests. `postflop_committed.py:237` is the seam.
- **Re-measure every finding before acting on it**, including every figure in this section. Two of
  this session's largest moves came from re-measuring something a previous session had written down
  correctly at the time: the "about 16 minutes a flop" was the monotone rate only, and decision 11's
  arena at 90.5% of the ceiling is 45% at the menu actually ruled.

### What the fold-in rewrite has to absorb

The thirteen amendments the stage-3 review counted, as the criteria they land on rather than as a
list of edits. Every one has its full reasoning in the decision list or a `backlog.yml` entry, and
the rewrite copies conclusions rather than re-arguing them:

1. Accuracy: target 0.3% of pot, cap 1,200 iterations, commit a cap-bound cell under 1% of pot and
   refuse above. **No criterion may state an accuracy for the solve as a whole** - the existing line
   forbidding a 0.3% claim stays and now has a 1% guarantee beside it.
2. Storage: object storage outside git, a committed index, a committed three-flop sample, the
   20 MiB `data/artifacts` cap unmoved, no git LFS. The byte-budget criterion measures the index and
   the sample, not the artifact.
3. The refusal inventory has **three** causes: never solved, solved but over 1%, and in the index
   but not fetched on this machine.
4. The spot key carries pot and effective stack, derived from the substituted line, and the
   query-time price band is within 20% of the cell's own price.
5. The menu: flop `33 75`, turn and river `66 125`, raise `2.5x`, no donk.
6. The range floor: 1%, class-level.
7. Reproducibility: two runs of the committed configuration, strategies diffed rather than
   checksummed; if not byte-identical the phase halts for Taylor rather than falling back to a
   tolerance.
8. One phase, not split.
9. The machine: a rented NVIDIA cloud box, no provider or spec named, and every timing and arena
   figure in the phase re-derived on it before a run is planned.
10. `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` sits on the Closed list on a Darwin premise the rented
    Linux box removes. Re-open or restate it.
11. The covered line count is an output of both the campaign and the index, whichever is smaller.
12. Coverage is bounded at 74.9% of corpus flops and 7.7% of that loss is multiway, which is
    structural rather than fundable - see `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`.
13. The committed sample's own texture and rank splits, which are frozen and which stage 4 picks
    boards inside rather than choosing.

The rewrite folds the contract's **existing** amendments into the criteria they amend to make room,
which is the part `AGENTS.md` prescribes and the part that carries the deletion risk.
**Done 2026-09-10 and reviewed.** All thirteen landed, plus decision 9, which was ruled on
2026-09-09, never reached the contract, and was not on this list - it is in only because C1 read
the decision list past its brief, and that near-miss is filed as
`NOTHING-CHECKS-THAT-EVERY-RULING-REACHES-A-CRITERION`. The contract is **299 of 300 lines with
zero headroom**: the two obligations R3's review added cost seventeen rationale cuts between them,
one of which took out an ordering predicate that had to be restored. The next obligation this
phase discovers cannot be added by compressing - see
`A-CONTRACT-HAS-A-FIXED-LIFETIME-AMENDMENT-BUDGET-AND-A-BIG-PHASE-SPENDS-IT-EARLY`.
