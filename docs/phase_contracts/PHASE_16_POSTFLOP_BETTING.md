---
phase_id: "16"
title: "Postflop That Can Bet"
depends_on:
  - "14"
required_gate_commands:
  - pytest_postflop_betting
  - generate_postflop_betting_report
required_reports:
  - reports/active/latest_postflop_betting_report.txt
required_phase_audit: reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md
---

# Phase 16: Postflop That Can Bet

## Scope

Replace the conservative postflop fallback with flop play that can bet and raise, driven by
committed solved data, leaving turn and river refusing as an uncovered preflop spot refuses today.

**What is true right now.** `PostflopFallbackStrategy` checks whenever checking is free, calls on
turn and river only a hand `hand_cannot_lose` proves cannot lose, and folds on the flop without
asking; it never returns `bet` or `raise`, and no `StrategyDecision` it builds carries an amount.
There is no postflop key, artifact, directory or `postflop_action_order`.

**All thirteen judgment calls are ruled** (Taylor, 2026-08-19, 2026-09-09 and 2026-09-10) and the
criteria below state them; the decision list holds the reasoning. **One phase, not split**, so the
artifact is committed against a key nothing has been built against yet. **The repo commits an index
plus a three-flop sample, not the solved artifact**, whose bytes live in object storage outside git;
no git LFS. **Solving moves to a rented NVIDIA cloud box** whose specification is deliberately
unruled, so every timing and arena figure here is re-derived there before a run is planned, and none
uses GTOpen's untested CUDA speedup until one flop is solved and timed there.

Nothing here gates on whether the strategy is good poker: the repo has no postflop oracle, and every
shape property below is satisfied by a uniformly wrong strategy.

Phase 16 is limited to the work named by this contract and the active ExecPlan.

## Non-goals

- No PokerNow automation, browser or platform observation, runtime solver calls, LLM-backed poker
  decisions, training UI surfaces, or large hand-history ingestion - `AGENTS.md`'s six V1
  boundaries. The gate must pass with no GTOpen, no Rust toolchain, no network and no fetched solve
  object, against the committed sample rather than a placeholder.
- Do not map an unsolved board onto a solved one by rank texture. Decision 2 defers that as
  `POSTFLOP-BOARD-ABSTRACTION` and `AGENTS.md` forbids heuristic guessing for a missing chart spot;
  decision 6's size finding is not a licence to reopen it. Do not commit turn or river spots;
  decision 1 rules flop only. Do not widen the preflop chart, its key, or its artifact format; this
  phase adds a sibling.

## Acceptance criteria

### The key and the query must be able to express a flop spot

- **`StrategyQuery` gains a postflop action history and `SeatAction` gains `bet`.** Today
  `preflop_actions` is the only history and `SeatAction` rejects `"bet"` against
  `_PREFLOP_HISTORY_ACTIONS`. Flop-only still needs within-street history, and `simulator/run.py`,
  which records history preflop only, records it postflop too. `DECISION_AUDIT_SCHEMA_VERSION` rises
  from 3, and a committed audit at the old version is rejected rather than read as the new one.
- **The postflop spot key is derived and compared, never parsed**, on the preflop key's own pattern:
  one producer, re-derived at import and at lookup, with a mismatch against the stored id refused.
  Changing what the key can express re-derives every committed cell, so it precedes any data.
- **The key carries the board, the preflop line verbatim with its sizes, the flop action so far with
  every bet size named, and the pot and effective stack.** Naming the size makes a later menu change
  fail closed. **Pot and stack are derived from the substituted preflop line, not from the table
  being asked about**, and the substitution is recorded on the committed spot rather than computed
  at query time. **The query refuses when the actual price is outside 20% of the price its cell was
  solved at, inclusive at both ends** - an open of 2.0bb to 3.0bb against an `@2.5` cell, a 3-bet of
  6.0bb to 9.0bb against an `@7.5` one - and never substitutes a nearest value. A test pins both
  endpoints as accepted.
- **The board in the key is the canonical representative of its suit-isomorphism class**, computed
  rather than tabulated, with a test proving all 1,755 classes are distinct and every one of the
  22,100 three-card boards maps into exactly one. It is the only collapse permitted, and two more
  tests run in the gate: a rank-texture neighbour maps to a different key, and on a two-tone board a
  flush-draw combo does not receive the strategy of the same ranks without the draw, hero's two
  cards being permuted by the board's own map.
  `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`.
- **No existing reader may mistake a postflop key for a preflop one.** A test asserts that
  `self_play_reference.py`, which scrapes any token starting with `t` that holds at least three
  slashes, returns no postflop key while still finding every preflop one and still raising on an
  empty inventory, which the key satisfies by not beginning with `t`.
- `postflop_action_order` is added to `poker_core/positions.py`, which already keeps
  `preflop_action_order` separate by name: the blinds act first once the flop is out. Postflop order
  is never derived from the seating order.

### What the committed solve owes

- **Every entry in the committed index records the achieved exploitability as a percent of the
  starting pot, the iteration count, the strategy digest and the digest of the stored object**, and
  a test fails on absence or a placeholder. Digest width is an authentication choice, not a byte
  one: the index carries either a full sha256 or the repo's 16-hex precedent declared as
  authenticating against accident only.
- **The target is 0.3% of the starting pot with a 1,200-iteration cap, and a cap-bound cell is
  committed only when its achieved error is under 1% of pot and refused above it.** Never big
  blinds: phase 10's 0.01bb is preflop and in the wrong unit, and a big-blind criterion will not
  reproduce the measured 220-to-260 iteration counts.
- **1% is the worst a played cell may carry, not an accuracy anyone aimed at**, so the report prints
  the distribution: how many cells sit between 0.3% and 1% of pot, on which boards and lines. No
  report or packet may state an accuracy for the solve as a whole.
- **Determinism is proved by re-solving and diffing, not by checksumming a single run**, on the
  configuration actually committed, in two processes against a restarted server. If they are not
  byte-identical **the phase halts and Taylor is asked**: no tolerance is set here and no
  implementer may pick one.
- **The packet states plainly that a solve at the committed iteration count is not proven to have
  converged**, and it is not reported as settled accuracy. Exploitability was targeted; frequencies
  on indifferent hands settle later and nothing here has diffed a deep solve against a shallow one.
- **The published exploitability is a bound only against an opponent confined to the same bet
  menu**, and the report says so wherever it prints the figure.
- **The solve is configured with two bet sizes on every street - flop `33 75`, turn and river
  `66 125`, `raise: "2.5x"`, `donk` empty** - identically on both seats, and that config is
  committed beside the data. The report states that nothing in the record uses 66% or 125%, and that
  no line this menu offers gets all-in in a single-raised pot.
- The cost model separates measured from scaled. Rainbow, 455 of the 1,755 classes, was never solved
  to target, so every rainbow figure is scaled from an exact orbit factor; paired, ace-high and
  disconnected boards are the same gap by rank, five converged cells covering two rank patterns.
- **A route recorded UNRUN is not assumed to work.** `/api/reports/*`, the batch flop-subset route,
  is recorded in `docs/GTOPEN_SOLVER_NOTES.md` as README-sourced and never executed. The solve
  driver either exercises it and reports what it cost, or does not use it and says so. The solve
  driver carries its own memory ceiling and refuses above it before solving.
  `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` rests on Darwin lacking `/proc/meminfo`; the rented Linux
  box has it, so that entry is re-checked against the machine before stage 6. The driver's ceiling
  is required either way.
- **`allin_threshold` is a percent of the acting player's remaining stack, not of the pot**, and it
  is posted as a percent postflop where preflop takes a fraction. `tree.rs` snaps any bet reaching
  `allin_threshold * max_to`, `max_to` being the stack behind, to a stack-off outside the
  `add_allin` guard, so `add_allin: false` still holds jams by conversion. The driver refuses a
  value below 1.0 rather than silently asking for 0.67%.
  `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`.
- **The input ranges are floored at a weight of 0.01, and the floor is class-level.** One
  suit-specific weight in either range collapses the isomorphism group and forfeits the suit saving
  on every non-rainbow board. The report publishes each committed range's pair weights on both
  sides. `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` owns the `44` asymmetry the floor exposes
  rather than causes, and is this phase's to repair or refuse explicitly.

### Selecting what gets committed

- **The covered set of preflop lines is committed explicitly, so a refusal names a line that was
  excluded rather than one that was forgotten.** The ranking comes from the corpus, via
  `ComparisonRow.asked_spot_key`, populated on every keyed row and not only on refusals, and sorts
  on **servable** arrival frequency: a 3-bet line serves 47.1% of its arrivals against a
  single-raised line's 99.0%. **How many lines are covered is an output rather than a choice**: as
  many as the campaign cost and the index each afford, whichever is smaller, and the report names
  which bound it.
- **The report states two things about that ranking**: the keys are post-substitution, every one
  reading `@2.5` against a corpus median open of 2.25bb, and reaching a decision point is not seeing
  a flop, so the flop-reaching filter is a different query, which this phase computes and publishes.
  The corpus ranking is cross-checked against the committed artifact's own `arrival_ppb` order, and
  the report prints where the two disagree. **The report prints the share of corpus flops this
  artifact can answer and splits the loss by cause**, naming the multiway share as structural rather
  than fundable, since a two-range solve cannot express a three-handed flop at any budget, machine
  or menu. `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`.
- The artifact does not land in `data/artifacts/preflop/`: `import_preflop_artifacts` globs `*.json`
  directly under it, so a postflop file there is read as a preflop chart and fails import, and a
  test pins that the preflop library ignores the postflop tree. **The committed index and the
  three-flop sample stay inside the 20 MiB `data/artifacts` cap, and the report prints the bytes
  used, the headroom left and the per-spot cost.** The budget covers the index and the sample, not
  the object storage, and includes provenance at 24 to 120 bytes a spot. Hero strategy is decision
  6's lean JSON: hoisted action names, classes as a parallel array in canonical order, three-decimal
  floats, free weights only. No figure is a per-weight rate that includes non-weight bytes, and the
  generator exits non-zero on one that does not reconcile against the bytes on disk. The solver
  export's source card is regenerated in the same task, since its `headroom_bytes` counts the whole
  artifact tree and `test_the_committed_export_sits_under_the_limit_with_stated_headroom` reds the
  moment any flop artifact lands.
- **The committed sample is three flops and its texture and rank splits are frozen here**: rainbow
  and dry high-card, two-tone and paired, monotone and connected. Two boards are named here and
  stage 4 picks only the third inside its split: `Kc7d2h`, which the campaign estimate extrapolates
  from, and `9c8c7c` in the single-raised pot, which is `matrix-03` and half of decision 11's menu
  experiment. Disconnected-low and ace-high connected are named as excluded rather than forgotten.

### What the strategy must do, and where it must refuse

- **On a covered flop spot the strategy returns `bet` and `raise` with amounts**, and a test proves
  at least one committed spot produces each. Every amount satisfies `DecisionAuditRecord`'s legality
  proof - at or above `min_raise_target` unless exactly all-in, never above
  `hero.street_bet + stack` - and a committed size that cannot be played is refused at import rather
  than at the table.
- **Turn and river refuse by their own codes rather than folding by default.**
  `CODE_FOLD_ON_THE_FLOP` covers the flop today and is answered after this phase. A refusal is not
  an action: the composite returns it untouched and the simulator voids the hand.
- **An uncovered preflop line refuses with a code that names the line, and an uncovered board
  refuses with its own.** The board-miss code is live rather than vacuous: all 1,755 classes are in
  scope, but a cell over 1% of pot refuses and rainbow has never been solved to target. **At the
  table a miss carries exactly two causes and the report never pools them**: no cell for this board
  or line, which is never-solved and solved-but-rejected together because neither is in the artifact
  and the query meets one absence - the report says so rather than let a reader think the phase
  never looked; and in the index but not fetched on this machine. How many cells the campaign
  rejected above 1% of pot is a report figure below, not a third cause here.
- The lookup fails closed on the preflop library's own walk: coarsest gap first, so the code names
  the first thing missing. No nearest-neighbour substitution of board, line, flop action, pot or
  stack.
- **Every mutation in `verification/mutations.yml` whose `find` string pins a line in
  `postflop_fallback.py` or `composite.py` is re-pointed with its claim unchanged, never retired.**
  One is witnessed by `pytest_engine_fidelity` rather than this phase's command, so each canary is
  verified against its own declared witness.
- The refusal inventory keeps working at a non-flat table;
  `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` records the grouping defect that a postflop code
  carrying board or line detail makes visible for the first time.

### The pot-odds river call

- Decision 5's default ships: call a river bet when equity against the full unseen deck beats the
  price, behind an explicit flag, **reporting the frequency it fires rather than claiming it is
  correct**. The equity number moves into `src`: `hand_cannot_lose` returns a short-circuiting bool
  and raises on a flop board, and the counting `holding_counts` lives in a report script. Equity is
  `(wins + ties/2) / 990` and the price is `to_call / (pot + to_call)`, both off the query. **The
  report states that a uniform unseen deck flatters hero, so this makes the bot over-call as the
  mirror of its current over-folding.**

### Evidence, reports, and gate

- **Every figure this contract names as an obligation is printed by the report and re-derived by the
  generator, which exits non-zero when one does not hold**: the covered lines, their servable corpus
  ranks and which constraint bound the count; the flop-reaching count and the servable share of
  corpus flops by loss cause; the committed spot count; bytes used and headroom left; per-spot
  achieved exploitability and iteration count with the 0.3%-to-1% distribution; the bet and raise
  frequencies; the refusal counts by code and by the two table causes, with any vacuous one
  labelled; the count of cells the campaign solved and rejected above 1% of pot, carried in the
  committed index's header; and the pot-odds firing rate. The report also records that the committed
  configuration was solved twice, the two strategies compared, and whether they were byte-identical.
- Both new command IDs carry a mutation canary in `verification/mutations.yml` authored at stage 4
  before any implementation exists, and `check_gate_bite` proves each bites. **One must target this
  phase's own new command.** One proves a wrong committed weight fails the command rather than being
  rendered, and one proves a spot whose size cannot be played is refused at import.
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`,
  the audit packet carries plain-language pass/fail evidence, and deferred work is in `backlog.yml`.

### The backlog entries this phase settles

- Closed: `V2-POSTFLOP-STRATEGY`, `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`,
  `POSTFLOP-UNBEATABLE-EARLIER-STREETS`, `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`,
  `ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS`.
- `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` leaves the Closed list: its premise is Darwin having no
  `/proc/meminfo`, and the rented Linux box has one, so it is restated against the machine used.
- `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` is closed **only** once no live document still says the turn
  costs 49 flops, which is the defect it was filed against.
- **Explicitly not closed**: `POSTFLOP-BOARD-ABSTRACTION`, deferred by decision 2 and not reopened
  by its size finding; `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`, unsolved here;
  `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`, sidestepped rather than settled;
  `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS` and
  `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN`, stated and not fixed;
  `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP`, not bounded by the 20% band. All
  restated, none marked done.
- Filed here with IDs rather than a promise, each carrying its own diagnosis in `backlog.yml`:
  `TWO-DOCS-STILL-SAY-DATA-ARTIFACTS-HAS-NO-SIZE-CHECK`, outside every scope this phase declares;
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` and
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT`, from this stage's reviews; and
  `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`, which this phase makes worse rather than
  closes.

## Required reports

- `reports/active/latest_postflop_betting_report.txt`

## Required command IDs

- `pytest_postflop_betting`
- `generate_postflop_betting_report`

## Human vetting packet requirements

- Plain-language summary of what changed, and one number a reader can recompute by hand from a
  committed file, with the packet naming the file and the method.
- Pass/fail checklist for a non-coding reviewer, with a source-code-free spot-check path.
- **The four qualifications on the committed data as qualifications, never as caveats**: convergence
  at the committed iteration count is unproven; the published exploitability binds only against the
  same bet menu; rainbow and three rank patterns were never measured at target; and the repo holds
  an index plus a sample rather than the artifact the bot plays, so a later phase measuring "the
  committed chart" must say which. No packet may claim the solve is accurate to 0.3%, claim a
  vacuous check passed, or say a green gate means good poker.
- The seam decision 1 accepted, stated: the bot bets a flop and then refuses every turn. Command
  summary with links to committed reports, and known limitations and deferred items.

## Forbidden shortcuts

- Do not replace deterministic checks with mocked success. Do not change this contract during
  implementation mode.
- Do not report a winrate or an EV figure over this artifact: the hands it would come from are the
  ones that ended at the turn refusal, so the number does not exist.
- Do not infer a missing board, preflop line, flop action, pot or stack. Refuse.
- Do not raise the 20 MiB `data/artifacts` cap, and do not slip bytes under it with git LFS, whose
  pointer would pass the byte budget vacuously on an unfetched clone.
- Do not undo a mutation with `git checkout`. Swap that mutation's `replace` string back to its
  `find` string at the line the sentinel names, since a canary is applied to a file already modified
  against HEAD. Do not report a scaled figure as measured, or a capped solve's wall clock as a cost.

## Regression expectations

- Previously completed phase gates remain verifiable, generated human docs stay current, and
  file-size and scope checks continue to pass. The preflop chart, its key, its artifact and its
  refusal codes are unchanged. A moved preflop number is a defect in this phase, not a result.
- **The frozen tests of completed phases that assert against the query shape are migrated in this
  task**, authored at stage 4 with this phase's own tests. **Stage 4 measures that set itself and
  states it, rather than inheriting a count from here.** Three are known to invert:
  `test_rejects_a_bet_because_preflop_has_no_bet` in `tests/test_strategy_contract.py`, and the two
  pinning `DECISION_AUDIT_SCHEMA_VERSION == 3` in `tests/test_table_state.py` and
  `tests/test_spot_vocabulary_downstream.py`. Three is a finding rather than a bound, so the
  obligation is to sweep.
- The postflop fallback's turn and river behaviour is preserved where this phase does not replace
  it, and the report says which of its codes are unreachable.
