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

Replace the conservative postflop fallback with flop play that can bet and raise, driven by a
committed solved artifact, leaving turn and river refusing the way an uncovered preflop spot
refuses today.

**What is true right now, stated first because this phase was declared twice on premises that had
already changed.** `PostflopFallbackStrategy` checks whenever checking is free and otherwise folds;
on the turn and river it calls only a hand `hand_cannot_lose` proves cannot lose, and on the flop it
folds without asking. It never returns `bet` or `raise` on any path, and no `StrategyDecision` it
builds carries an amount. GTOpen's postflop engine was driven end to end on 2026-08-23 and
2026-08-24 over four routes on flop boards, and MAINT-26 measured what a solve costs. There is no
postflop key, no postflop artifact, no postflop directory, and no `postflop_action_order`.

Three of six judgment calls are ruled (Taylor, 2026-08-19): flop only, all 1,755 canonical flops,
a small head of common preflop lines ranked off the corpus. Decision 5 is `runtime-reversible` and
proceeds on its recorded default. Decisions 4 and 6 are `frozen-into-data` and stage 3 halts on
them; decision 6 was filed at this contract stage from a measurement, and until it is answered this
contract cannot name the artifact's encoding, its per-spot byte budget, or how many preflop lines
fit. Those three criteria are the amendment this phase owes after stage 3, in `contract-update`,
and no implementer may choose them.

Nothing in this phase gates on whether the resulting strategy is good poker. The repo has no
postflop oracle, and every shape property below is satisfied by a strategy that is uniformly wrong.

Phase 16 is limited to the work named by this contract and the active ExecPlan.

## Non-goals

- No PokerNow automation, browser or platform observation, runtime solver calls, LLM-backed poker
  decisions, training UI surfaces, or large hand-history ingestion - `AGENTS.md`'s six V1
  boundaries, none of which this phase touches. The gate must pass on a machine with no GTOpen, no
  Rust toolchain and no network.
- Do not map an unsolved board onto a solved one by rank texture. Decision 2 deferred that as
  `POSTFLOP-BOARD-ABSTRACTION` and `AGENTS.md` forbids heuristic guessing for a missing chart spot.
  Decision 6's size finding is not a licence to reopen it.
- Do not commit turn or river spots. Decision 1 rules flop only.
- Do not widen the preflop chart, its key, or its artifact format. This phase adds a sibling.

## Acceptance criteria

### The key and the query must be able to express a flop spot

- **`StrategyQuery` gains a postflop action history and `SeatAction` gains `bet`.** Today
  `preflop_actions` is the only history and `SeatAction` rejects `"bet"` against
  `_PREFLOP_HISTORY_ACTIONS`, so a flop spot has no field to read and no representable action type.
  A flop is not one decision - hero acts, villain answers, hero faces a bet or a raise - so
  flop-only still needs within-street history. `simulator/run.py` records history on preflop only
  and must record it postflop too.
- `DECISION_AUDIT_SCHEMA_VERSION` rises from 3, and a committed audit at the old version is
  rejected rather than read as the new one. A schema that silently accepts both is a schema that
  proves nothing about which one produced a record.
- **The postflop spot key is derived and compared, never parsed**, on the preflop key's own pattern:
  one producer, re-derived at import and at lookup, with a mismatch against the stored id refused.
  Adding spots at a fixed key is additive; changing what the key can express re-derives every
  committed cell, which is why this is the one thing the phase must get right before any data.
- The key carries the board, the preflop line, and the flop action so far. The preflop line is in
  the key because postflop strategy is range against range: the same hand on the same board plays
  differently after `LJ open, BTN call` than after `BTN open, BB 3-bet, BTN call`, so the summary is
  a handle on a pair of ranges rather than history for its own sake.
- **The board in the key is the canonical representative of its suit-isomorphism class**, computed
  rather than tabulated, with a test proving all 1,755 classes are distinct and that every one of
  the 22,100 three-card boards maps into exactly one. Suit isomorphism is exact and is the only
  collapse permitted; a test must show a rank-texture neighbour maps to a different key.
- **A postflop key must not be mistaken for a preflop key by any existing reader.**
  `self_play_reference.py` recovers keys from the self-play inventory by scraping any token starting
  with `t` that holds at least three slashes, and it raises rather than returning empty. **A
  postflop key must not be returned by that reader**, and a test asserts the returned set contains
  no postflop key while the reader still finds every preflop one and still raises on an empty
  inventory.
- `postflop_action_order` is added to `poker_core/positions.py`, which already keeps
  `preflop_action_order` separate by name and says why: the blinds act first once the flop is out.
  Deriving postflop order from the seating order is the defect this criterion exists to prevent.

### What the committed solve owes

- **Every committed spot records the achieved exploitability as a percent of the starting pot, the
  iteration count, and the strategy digest**, and a test fails on absence or a placeholder. None of
  the three can be recomputed inside the gate, because that would mean running the solver.
- The target is a percent of the starting pot, never big blinds. Phase 10's 0.01bb figure is
  preflop, in the wrong unit, and against a tree where multiway has no exploitability proper; a
  criterion written in big blinds will not reproduce the measured 220-to-260 iteration counts.
- **Determinism is proved by re-solving and diffing, not by checksumming a single run.** MAINT-26
  found byte-identical output across two processes against a restarted server. This phase repeats
  it for whatever config it commits and records the digest; if a run is not byte-identical, an
  accuracy target and the observed maximum divergence are recorded in place of the digest.
- **The packet states plainly that a solve at the committed iteration count is not proven to have
  converged**, and it is not reported as settled accuracy. Exploitability was targeted; frequencies
  on indifferent hands settle later, and nothing in the repo has solved deep and diffed against a
  shallower solve. This phase commits the result, so the qualification belongs on the data.
- **The published exploitability is a bound only against an opponent confined to the same bet
  menu**, because the best-response pass walks the same tree. The report says so wherever it prints
  the figure.
- The cost model this phase reports separates measured from scaled. Rainbow was never solved to
  target and is 455 of the 1,755 classes and the expensive end, so every rainbow figure is scaled
  from an exact orbit factor. Paired, ace-high and disconnected boards are the same gap by rank:
  five converged cells cover two rank patterns.
- **A route recorded UNRUN is not assumed to work.** `/api/reports/*`, the batch flop-subset route,
  is the one a 1,755-flop run would reach for, and `docs/GTOPEN_SOLVER_NOTES.md` records it as
  README-sourced and never executed. The solve driver either exercises it and reports what it cost,
  or does not use it and says so.
- The solve driver carries its own memory ceiling and refuses above it before solving.
  `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` records that GTOpen's guard reads `/proc/meminfo` and
  cannot fire here, so the arena is a hard wall a solve fails against rather than slows.
- `allin_threshold` is posted as a percent of pot on the postflop route and as a fraction preflop.
  The driver refuses a value below 1.0 rather than silently asking for a 0.67% threshold, which
  replaces every configured bet with a jam. `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`.
- Any range flooring is class-level. One suit-specific weight anywhere in either range collapses
  the isomorphism group to the identity and forfeits the whole suit saving on every non-rainbow
  board. `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`.

### Selecting what gets committed

- **The covered set of preflop lines is committed explicitly, so a refusal names a line that was
  excluded rather than one that was forgotten.** The ranking comes from the corpus, via
  `ComparisonRow.asked_spot_key`, which is already populated on every keyed row rather than on
  refusals only.
- **The report states two things about that ranking rather than inheriting them.** The keys are
  post-substitution, because the corpus's median open is 2.25bb and every key reads `@2.5`; and
  reaching a decision point is not seeing a flop, so the filter decision 3 needs is a different
  query that nothing in the repo computes today. This phase computes it and publishes the count.
- The corpus ranking is cross-checked against the committed artifact's own `arrival_ppb` order, and
  the report prints where the two disagree. They agree on the top ten but for two swaps today.
- The artifact does not land in `data/artifacts/preflop/`. `import_preflop_artifacts` globs `*.json`
  directly under that directory, so a postflop file there is read as a preflop chart and fails
  import. A test pins that the preflop library ignores the postflop tree.
- **The committed tree stays inside the 20 MB `data/artifacts` cap, and the phase's own report
  prints the bytes used, the headroom left, and the per-spot cost, each recomputed rather than
  quoted.** Decision 6 measured that the headroom buys on the order of one hero decision node for
  one preflop line in any JSON encoding, against a phase that needs several nodes across several
  lines. Whichever way out decision 6 rules, this criterion is what proves it worked. No figure
  here is a per-weight rate that includes non-weight bytes; the generator exits non-zero on one
  that does not reconcile against the bytes on disk.
- The solver export's source card is regenerated in the same task, because its `headroom_bytes`
  counts the whole artifact tree and `test_the_committed_export_sits_under_the_limit_with_stated_headroom`
  reds the moment any flop artifact lands.

### What the strategy must do, and where it must refuse

- **On a covered flop spot the strategy returns `bet` and `raise` with amounts**, and a test proves
  at least one committed spot produces each. A phase called Postflop That Can Bet whose gate is
  green while nothing ever bets is the decorative-gate defect this repo has now fixed three times.
- Every amount satisfies `DecisionAuditRecord`'s legality proof: at or above `min_raise_target`
  unless exactly all-in, and never above `hero.street_bet + stack`. A committed size that cannot be
  played is refused at import rather than at the table.
- **Turn and river refuse by their own codes rather than folding by default.** Today the flop folds
  silently under `CODE_FOLD_ON_THE_FLOP`; after this phase the flop is answered and the two later
  streets carry the refusal. A refusal is not an action: the composite returns it untouched and the
  simulator voids the hand.
- **An uncovered preflop line refuses with a code that names the line**, and an uncovered board
  cannot occur, because decision 2 keeps all 1,755 classes. A test asserts the board-miss code is
  unreachable and labels it vacuous wherever it is reported, never counted as a check that passed.
- The lookup fails closed on the preflop library's own walk: coarsest gap first, so the code names
  the first thing actually missing rather than the last thing checked. No nearest-neighbour
  substitution of board, line, or flop action.
- **Every mutation in `verification/mutations.yml` whose `find` string pins a line in
  `postflop_fallback.py` or `composite.py` is re-pointed with its claim unchanged, never retired.**
  Stated as a predicate rather than a count, because a count is a second place to keep the number
  right. One of them is witnessed by `pytest_engine_fidelity` rather than this phase's own command,
  so re-pointing is verified by running each canary's own declared witness and not this phase's. Phase 13 found a
  phase 11 canary whose `find` string had stopped matching, which would have retired a legality
  claim by accident behind a green gate.
- The refusal inventory keeps working at a non-flat table. `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL`
  records that the self-play inventory groups on the whole detail tuple and shatters into singleton
  rows; a postflop code carrying board or line detail makes that visible for the first time.

### The pot-odds river call

- Decision 5's default ships: call a river bet when equity against the full unseen deck beats the
  price, behind an explicit flag, **reporting the frequency it fires rather than claiming it is
  correct**. It is `runtime-reversible` because no committed data records it.
- The equity number moves into `src` rather than being recomputed. `hand_cannot_lose` returns a
  short-circuiting bool and raises on a flop board, and the counting version `holding_counts` lives
  in a report script. Equity is `(wins + ties/2) / 990` and the price is `to_call / (pot + to_call)`,
  both off the query.
- **The report states that a uniform unseen deck flatters hero, so this makes the bot over-call as
  the mirror of its current over-folding.** It is an assumption about the hand, not a fact about it.

### Evidence, reports, and gate

- **Every figure this contract names as an obligation is printed by the report and re-derived by the
  generator, which exits non-zero when one does not hold**: the covered lines and their corpus
  ranks, the flop-reaching count, the committed spot count, bytes used and headroom left, per-spot
  achieved exploitability and iteration count, the bet and raise frequencies, the refusal counts by
  code with the vacuous one labelled, and the pot-odds firing rate. A report that renders whatever
  number it is handed exits 0 however wrong the number is.
- Both new command IDs carry a mutation canary in `verification/mutations.yml` authored at stage 4
  before any implementation exists, and `check_gate_bite` proves each bites. **One canary must
  target this phase's own new command**, which is the omission phases 08 and 09 each made and each
  had caught at stage 7.
- One canary proves a wrong committed weight fails the command rather than being rendered, and one
  proves a spot whose size cannot be played is refused at import.
- Required reports exist and are fresh, required command IDs pass through `scripts/run_verify.py`,
  the audit packet carries plain-language pass/fail evidence, and deferred work is in `backlog.yml`.

### The backlog entries this phase settles

- Closed: `V2-POSTFLOP-STRATEGY`, `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`,
  `POSTFLOP-UNBEATABLE-EARLIER-STREETS`, `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`,
  `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS`, `ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS`.
- `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` is closed **only** once no live document still asserts the
  ratio it falsifies. Closing it while a sentence somewhere still says the turn costs 49 flops is
  the defect it was filed against.
- **Explicitly not closed**: `POSTFLOP-BOARD-ABSTRACTION`, deferred by decision 2 and not reopened
  by decision 6's size finding; `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`, which needs a solve this
  phase may not perform; `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`, which decision 6 answers for
  the flop only. All three restated, none marked done.
- Filed here, with IDs rather than a promise, each carrying its own diagnosis:
  `TWO-DOCS-STILL-SAY-DATA-ARTIFACTS-HAS-NO-SIZE-CHECK`, outside every scope this phase declares;
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` and
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT`, both raised by this stage's own
  reviews; and `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`, which this phase makes
  worse rather than closes.

## Required reports

- `reports/active/latest_postflop_betting_report.txt`

## Required command IDs

- `pytest_postflop_betting`
- `generate_postflop_betting_report`

## Human vetting packet requirements

- Plain-language summary of what changed, and one number a reader can recompute by hand from a
  committed file, with the packet saying which file and how.
- Pass/fail checklist for a non-coding reviewer, with a source-code-free spot-check path.
- **The three qualifications on the committed data as qualifications, never as caveats**: that
  convergence at the committed iteration count is unproven, that the published exploitability binds
  only against the same bet menu, and that rainbow and three rank patterns were never measured at
  target. No packet may claim the committed solve is accurate to 0.3%, that a vacuous check passed,
  or that a green gate says the strategy is good poker.
- The seam decision 1 accepted, stated: the bot bets a flop and then refuses every turn.
- Command summary with links to committed reports, and known limitations and deferred items.

## Forbidden shortcuts

- Do not replace deterministic checks with mocked success.
- Do not change this contract during implementation mode. The three criteria decision 6 leaves
  unnamed are amended in `contract-update` after stage 3, not filled in by a builder.
- Do not infer a missing board, preflop line, or flop action. Refuse.
- Do not raise the `data/artifacts` cap to fit the artifact. `check_file_sizes.py` says exceeding a
  limit there is a halt and a decision; decision 6 is that halt, and only Taylor closes it.
- Do not undo a mutation with `git checkout`. Swap that mutation's `replace` string back to its
  `find` string at the line the sentinel names, because a canary is applied to a file already
  modified against HEAD and checking it out discards the work being verified.
- Do not report a scaled figure as measured, or a capped solve's wall clock as a cost.

## Regression expectations

- Previously completed phase gates remain verifiable, generated human docs stay current, and
  file-size and scope checks continue to pass.
- The preflop chart, its key, its artifact and its refusal codes are unchanged. A moved preflop
  number is a defect in this phase, not a result.
- **The frozen tests of completed phases that assert against the query shape are migrated in this
  task**, authored at stage 4 with this phase's own tests, because this phase changes the shape they
  assert against. Exactly one frozen test asserts the thing this phase inverts:
  `test_rejects_a_bet_because_preflop_has_no_bet` in `tests/test_strategy_contract.py`, which
  requires `SeatAction(0, "bet")` to raise. At most 334 frozen tests sit in files that reference the
  query shape at all, and none breaks from adding a postflop history field that defaults the way
  `preflop_actions` does. Stage 4 measures the set itself rather than trusting either figure.
- The postflop fallback's turn and river behaviour is preserved where this phase does not replace
  it, and the report says which of its codes are now unreachable.
