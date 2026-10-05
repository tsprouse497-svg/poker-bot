# MAINT-42 independent review: the turn and river solved at the table

- **Reviewer**: read-only subagent; wrote none of the diff.
- **Reviewed**: `git diff 553f6f7..6c99f73` in `~/projects/poker-bot-worktrees/maint-42`.
- **Read in full**: `AGENTS.md`, the ExecPlan, the audit packet, the diff; phase contracts 10, 18, 19, 20, 21; `docs/GTOPEN_SOLVER_NOTES.md`; GTOpen at `~/projects/GTOpen` (`4aee435b`).
- **Ran, read-only**: `check_contracts`, `check_scope`, `check_execplan_delegation`, `check_repo_consistency`, `check_file_sizes`, the three `generate_* --check` freshness checks (all exit 0, tree left clean), and the backlog citation function `_citations` from `scripts/run_full_quality_gate.py` called directly against `backlog.yml` (no uncited ids anywhere under `docs/` or `reports/`). Not run: the verify gate.

## Findings

1. **[blocker] The boundary adds one condition Taylor did not rule.** `AGENTS.md:147`: "A live solve runs on the bot's own machine with nothing sent over a network, and gives the same answer for the same inputs, because this is a deterministic bot."
   - The determinism half is already law: `AGENTS.md:3` says "an offline-first deterministic bot". The sentence attributes it to that, so it is a restatement, not a new rule. Fine.
   - The local-machine, no-network half is not derivable. "Offline-first" is not "offline-only"; phase 20 plays an online table; phase 21 rents cloud machines for solves. The clause closes off a remote or rented solve box, which is a real lever on the 1.7 to 2.4 s turn, and nobody ruled that. It also reads ambiguously against GTOpen itself, which is driven over local HTTP (`scripts/solve_postflop_sample.py` `Server`, `postflop_transport.BASE_URL`): a builder can argue a loopback socket is or is not "a network".
   - Fix: either get Taylor's yes on the clause and record it as his ruling, or drop it from `AGENTS.md` and add "where the solve runs" as an open question in `LIVE-TURN-AND-RIVER-SOLVING`. Keep the determinism half, tied to line 3.

2. **[non-blocker] Every quoted figure re-derives from the packet rows, with one bad explanation.** Checked against `reports/phase_audits/MAINT_42_LIVE_TURN_AND_RIVER_SOLVES.md:44-72`:
   - Turn 2.002 / 2.397 / 1.686 s gives 1.7 to 2.4 s. River 0.024 / 0.026 / 0.026 / 0.026 gives 24 to 26 ms, "about 25 ms". Turn iterations 140 to 150, river 60 to 80. Turn arena 35.74 to 37.23 rounds to 36 to 37 MB; river 0.10 to 0.11. Nodes 12,711 / 4,862 and 39 / 14. All correct in `AGENTS.md:147`, `backlog.yml:9-12`, `docs/GTOPEN_SOLVER_NOTES.md:176-179`, `docs/V2_ROADMAP.md:146` ("about two seconds", "millions of spots", since 85,995 + 4,127,760 is about 4.2 million).
   - Lever table `docs/GTOPEN_SOLVER_NOTES.md:185-192`: baseline 2.167 / 1.798 gives 1.8 to 2.2; 0.5% gives 1.725 / 1.254, so 1.3 to 1.7; 1% gives 1.099 / 0.862, so 0.9 to 1.1; one size gives 0.644 / 0.508, so 0.5 to 0.6, with 1,976 action nodes; half the combos gives 0.94 / 0.788, so 0.8 to 0.9; all three gives 0.185 / 0.177, "about 0.18". All correct.
   - 85,995 = 1,755 x 49 and 4,127,760 = 85,995 x 48. Correct.
   - Pots: 5.5 + 2(0.33 x 5.5) = 9.13 and 9.13 + 2(0.66 x 9.13) = 21.18; stacks 97.5 to 95.69 to 89.66. Correct.
   - **The wrong part**, `docs/GTOPEN_SOLVER_NOTES.md:181`: "A turn tree holds roughly 325 river subgames, 12,711 nodes over 39, which is why it costs about 80 times a river." 12,711 / 39 = 325.9 is a node ratio, not a count of river subgames (river subgames inside a turn tree have different stack depths and so different sizes). And 325 cannot be "why" the cost is 80x: if subgame count drove cost, it would predict about 325x. The 80x itself (mean turn 2.03 s over 0.025 s) divides by a river figure that the same paragraph says is inflated by a 20 ms poll, so the true ratio is unknown and probably larger. Fix: state the node ratio and the time ratio as two separate facts and drop "which is why", or drop the 80x.

3. **[non-blocker] "Ceilings" overclaims.** `docs/GTOPEN_SOLVER_NOTES.md:174` ("these are ceilings"), `:201` ("a table's turn latency is bounded above"), `backlog.yml:11` ("so both are ceilings").
   - What is a ceiling is the hand count. A narrowed range is the preflop range times reach probabilities of 1 or less, so under the same floor it has no more hands.
   - Time is not bounded by that. Iterations to the 0.3% target depend on the game, and a polarised narrowed range can take more of them. Also, flop strategies mix, so most combos keep a non-zero weight after flop betting. Real narrowing may remove far fewer hands than the "about half the combos" lever does.
   - The figures also come from a freshly started server. The same document (`:142-145`) measured a long-running server up to 1.6x slower per iteration. A table bot that keeps one server alive would land nearer 2.7 to 3.8 s on the turn unless it restarts, and the restart's cost is unmeasured (`Server.start` polls readiness every 0.25 s).
   - Fix: say "hand counts are ceilings; time was measured on a fresh server and is not a ceiling". This matters because Taylor accepted the turn "at that figure".

4. **[non-blocker] The river's one-second limit is safe on this evidence. The 20 ms poll is not a problem.** The poll can only make the measured 24 to 26 ms too high, never too low. Even adding the 1.6x drift, tree build (1 to 3 ms) and HTTP round trips, the river is 20x or more inside a second. Pot 21.18 and stack 89.66 (river SPR, stack-to-pot ratio, about 4.2) is a normal single-raised-pot river. Button open against big-blind call is the widest heads-up preflop line, so it is a fair hand-count ceiling for heads-up pots. Still unmeasured, and better listed than implied: a server cold start inside the one-second budget, and other SPRs. A deeper SPR adds raise layers to the river tree. The 39-node tree is so small that neither is likely to break the limit.

5. **[non-blocker] Question (1) of `LIVE-TURN-AND-RIVER-SOLVING` misses phase 21.** `backlog.yml:17` says phases 18, 19 and 20 forbid runtime solver calls. That is true: `docs/phase_contracts/PHASE_18_YARDSTICK.md:47`, `PHASE_19_HEURISTICS_AND_MERGED_CHARTS.md:55`, `PHASE_20_HOME_GAME.md:57`. But phase 21, also `future` in `phase_status.yml`, says the same at `docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md:100`, and adds "Do not commit turn or river spots" at `:95`. The list should read 18, 19, 20 and 21. The other verified claims hold:
   - GTOpen has no licence: `docs/GTOPEN_SOLVER_NOTES.md:15`, and confirmed in the clone, which has no LICENSE file and no licence text in `README.md` or `Cargo.toml`.
   - It serves one global session: `crates/server/src/main.rs:51` (`session: Mutex<Option<Session>>`), also `postflop_solve_driver.py:455`.
   - The gate needs no GTOpen, no Rust toolchain and no network: `docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md:65`.
   - Determinism was byte-identical: `docs/GTOPEN_SOLVER_NOTES.md:155-157`.

6. **[non-blocker] Three questions a builder would hit are missing from the entry.**
   - (a) *Heads-up only.* GTOpen's postflop engine is heads-up (`~/projects/GTOpen/README.md:3-4`), so a multiway turn or river cannot be solved live by it at all. Six-handed home games will reach multiway turns. Who answers those: refusal, the fallback, or something else?
   - (b) *Re-solving safety.* A turn re-solve built from reach ranges alone, with no constraint tying it to the committed flop strategy's values, is the textbook way re-solving becomes exploitable: the opponent's counterfactual values are not protected. Whether the solve needs that constraint, or how much it costs if it skips it, is a design question, not an implementation detail.
   - (c) *River after a live turn.* The turn solve already contains every river subgame. Is the river read from it, re-solved from scratch, or re-solved only off the menu? (5) touches this, but not the on-menu case.

7. **[non-blocker] The setup sentence is inaccurate.** `docs/GTOPEN_SOLVER_NOTES.md:172`: "The setup is the committed flop campaign's in every field but the board". Pot and stack also differ (9.13 / 95.69 and 21.18 / 89.66 against the flop's 5.5 / 97.5). And "the committed flop campaign" reads as phase 21, which is `future`; what is meant is phase 16's ruled config (`solve_config_document`). Fix: "phase 16's ruled config in every field but the board, pot and stack".

8. **[non-blocker] Nothing anticipates building it, and no contract was touched.** The diff touches no file under `docs/phase_contracts/`, `src/`, `scripts/`, `tests/` or `data/`. `check_scope` passes. Two lines lean toward pre-deciding design, and both are runtime-reversible rather than frozen-into-data, so neither blocks:
   - `backlog.yml:31-32`: "re-solved with the size added, which the river's cost allows". It is offered as one option of two. Fine.
   - `backlog.yml:35`: "`river_pot_odds.py` stays as a fallback". That describes shipped code. It is consistent with ExecPlan ruling 2, "No river rule of thumb is needed as the plan". Fine.

9. **[non-blocker] Stale wording that is still true.** `scripts/solve_postflop_sample.py:3-4` and `backlog.yml:8685` (`A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`) say "`AGENTS.md` forbids runtime solver calls". Both are about flop solves, which are still forbidden at runtime, and both lean mainly on the phase 10 gate rule, so neither is false. `scripts/` is outside approved scope anyway. No live document calls the boundary permanent without the exception: the grep found only completed contracts 00 to 16, which are snapshots, and future contracts 18 to 21, which are scope limits. Nothing outside the corrected lines says turn or river roots were never run.

10. **[non-blocker] The rulebook now carries measured figures in four places.** The same timings appear in `AGENTS.md:147`, `backlog.yml:9-12`, `docs/V2_ROADMAP.md:146` and `docs/GTOPEN_SOLVER_NOTES.md`. The first narrowed-range or long-session measurement will falsify three copies, and no check reads them. Consider letting `AGENTS.md` state the ruled limits (turn accepted as measured, river under one second) and pointing to the notes for the numbers.

11. **[alignment] A lift with no owner.** `AGENTS.md:149` says of ingestion that "a lift with no owner and no number is not a lift". This boundary is now lifted with no owner, and four future contracts forbid the work. The task does not claim otherwise, and `LIVE-TURN-AND-RIVER-SOLVING` already carries it as question (1), so no new backlog entry is needed, only the phase-21 correction in finding 5.

12. **[non-blocker] Repo checks are clean.** All read-only checks listed above exit 0. The citation scan finds no id-shaped token in the new prose that `backlog.yml` lacks. `LIVE-TURN-AND-RIVER-SOLVING` is declared, and `SOLVER_COMPRESS` has no hyphen. No ALL-CAPS hyphenated phrase appears in the new prose.

## Held back

Outside the brief, noticed and not pursued:

- The packet's measurement scripts hard-code `/Users/taylorsprouse/projects/poker-bot/...` on `sys.path`, which is the primary checkout and not the task's worktree. I checked that it sat on `main` at `553f6f7`, clean, so the rows are valid for this base. But the scripts are not reproducible from the worktree as written.
- Each board was solved once. The lever baselines (2.167 and 1.798) against the single-solve rows (2.002 and 1.686) suggest run-to-run spread of about 10%. That is fine for this ruling, but it is not a distribution.
- "85,995 turn and 4,127,760 river spots per preflop line" understates storage. Each flop betting line gives different turn ranges, so it is also per flop line. That favours the ruling and was pre-existing in `docs/ROADMAP.md:74`.
- `docs/V2_ROADMAP.md:67` still offers river pot-odds as "a cheap intermediate". The entry it cites is done, and with live river solves it now reads as a past plan rather than a forward one.
- The packet's "Independent review" and "Gate" sections still read "Pending", which is expected at this stage.

**Verdict:** the figures are sound and the river ruling is well supported; one blocker, the unruled local-machine and no-network clause in `AGENTS.md:147`, needs Taylor's yes or removal before the gate.

## Round 2

Reviewed `git diff 6c99f73..7364fca`, read-only. No gate was run. The read-only checks were rerun and all exit 0: the three generated-doc freshness checks, `check_contracts`, `check_scope`, `check_execplan_delegation`, `check_repo_consistency`, `check_file_sizes`, and the backlog citation scan.

1. **Blocker resolved.** `AGENTS.md:147` no longer says anything about a machine or a network; only the determinism sentence remains, tied to the deterministic-bot rule. Where the solve runs is now question (7) of `LIVE-TURN-AND-RIVER-SOLVING` and is left to Taylor to rule.
2. **Ratio wording fixed and true.** `docs/GTOPEN_SOLVER_NOTES.md:181` now gives 325 as a node ratio and 80x as a wall-clock ratio. It says the polling makes the 80x too small, which is correct because the river time is inflated, and that neither number counts subgames.
3. **Ceiling wording fixed and true.** `docs/GTOPEN_SOLVER_NOTES.md:174` now says the hand count is a ceiling and the wall clock is not, because iterations on narrower ranges were not measured, mixed flop strategies remove fewer hands, solves ran on a fresh server (up to 1.6x faster, as measured at `:142-145`), and start-up was not timed. `backlog.yml:11-13` now points to that passage.
4. **Owner list fixed.** Question (1) names phases 18 to 21, which matches `PHASE_21_FLOP_CAMPAIGN.md:100`.
5. **Missing questions added.** Questions (8) to (10) are accurate as stated. GTOpen's postflop engine is two-player (`README.md:3-4`). The entry now closes on "all ten".
6. **Setup sentence fixed.** `GTOPEN_SOLVER_NOTES.md:172` now says the setup is the flop sample's except for the board, the pot and the stack.
7. **River pot-odds fixed.** `docs/V2_ROADMAP.md:67` now calls river pot-odds a fallback, which matches `backlog.yml`'s line that `river_pot_odds.py` stays as a fallback.
8. **[non-blocker] Small miscount.** The packet's review section reports the findings faithfully, including the blocker, its reason and its resolution, the alignment item, and the held-back points. The ExecPlan line "eight non-blockers fixed or accepted" miscounts: the note tagged ten. Four of them (4, 8, 9 and 12) were confirmations that needed no change, and the packet rightly does not list them as fixes. Cosmetic only.

No new false claim found. **Verdict: clear.**
