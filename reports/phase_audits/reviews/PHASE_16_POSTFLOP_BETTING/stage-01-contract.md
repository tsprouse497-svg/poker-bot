# Stage 1 review, phase 16: the contract

Independent read-only review. Reviewer did not author the contract, the ExecPlan, or the decision
list, and edited none of them.

Diff reviewed: `git diff 2942e8d -- docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md
docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md
reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` (619 insertions).

The stage's question: is any acceptance criterion unfalsifiable, a restatement of the phase title,
or satisfiable without doing the work it names?

## What checked out

Recorded first, because most of the contract holds and the blockers below should not be read as a
verdict on it. Everything here was re-derived in this worktree rather than accepted from the text.

Every code identifier the contract names exists and is spelled right: `_PREFLOP_HISTORY_ACTIONS`
(`src/poker_training_bot/strategy/contract.py:18`, and it is exactly
`("fold", "check", "call", "raise")`, so `SeatAction` does reject `"bet"`),
`DECISION_AUDIT_SCHEMA_VERSION` (same file line 12, and it is `3`),
`CODE_FOLD_ON_THE_FLOP` (`strategy/postflop_fallback.py:88`, returned at `:264`),
`hand_cannot_lose` (`:188`, and it does raise on a three-card board and does name
`POSTFLOP-UNBEATABLE-EARLIER-STREETS` in its own docstring), `holding_counts`
(`scripts/generate_postflop_fallback_report.py:418`, in a report script as stated),
`ComparisonRow.asked_spot_key` (`data_pipeline/comparison.py:185`, and `:428`/`:453` populate it on
the refusal row and the answered row alike, so "on every keyed row rather than on refusals only" is
right), `import_preflop_artifacts` (`solver_artifacts/importer.py:479`, and it does
`root.glob("*.json")` directly under the directory), `self_play_reference.py` (and it does scrape
`token.startswith("t") and token.count("/") >= 3`, and does raise rather than return empty),
`preflop_action_order` (`poker_core/positions.py:59`, whose docstring already says "postflop order
is different (the blinds act first once the flop is out)" — the criterion's rationale is verbatim
in the module), `test_the_committed_export_sits_under_the_limit_with_stated_headroom`
(`tests/test_solver_export.py:656`), `DIRECTORY_BYTE_LIMITS` (`scripts/check_file_sizes.py:28` —
`DirectoryByteLimits` is not a name in this repo and the contract does not use it), and
`arrival_ppb` (`solver_artifacts/importer.py:112`). `postflop_action_order` correctly does not
exist; the contract says it is added.

All fourteen backlog IDs named across the three files resolve to exactly one entry in `backlog.yml`.

The size-measurement floor reproduces exactly. Recomputed here from first principles: 22,100
three-card boards collapse to 1,755 suit-isomorphism classes, of which 455 are rainbow; summing
each class's own hero-combo orbits gives 1,286,792 classes, mean 733.2. Measured off the committed
chart's `action_weights`: 51,068 leaf weights at 14.78 bytes each compact and 26.79 as committed.
`data/artifacts` totals 5,197,325 bytes, so headroom is 15,774,195. One line, one node, check and
bet, compact is 38,049,009 bytes = 36.3 MiB = **2.41x headroom** — the contract's headline figure,
correct to the digit. (Three of the four derived figures beside it are not; see Blocker 1.)

MAINT-26's numbers reproduce from `reports/active/latest_postflop_solve_cost.txt`: "7 of 30 rows
that reached their target" is its own line 525; the pooled texture split is "rainbow 0, two-tone 1,
monotone 6" at line 555; the five converged matrix cells reached target at 220, 240, 240, 240 and
260 iterations with `quantisation_iterations` 20, so "220 to 260 iterations with a 20-iteration
bracket" and "both determinism runs stopped at 240" are exact; every row posts
`allin_threshold: 85.0`; `arena_mb` 21,663 against `arena_ceiling_mb` 12,026 is the memory-guard
claim in the data. `docs/GTOPEN_SOLVER_NOTES.md:164` does record `REPORTS` as never run. The corpus
figures 499 hands and 3,048 preflop decision points are printed at
`reports/active/latest_sample_comparison_report.txt:44,46`. C(45,2) = 990, so the pot-odds
denominator is right.

`scripts/check_contracts.py` is satisfied: all six frontmatter fields present, `phase_id` matches
`\d{2}`, and all eight `## ` sections present and spelled exactly. The `### ` subheadings inside
`## Acceptance criteria` do not break `section_bullets` (its terminator is `^## ` with a trailing
space) and the specific-criteria count is far past `MIN_SPECIFIC_CRITERIA`.

The ExecPlan's `Delegation Plan` is real, not template text: ten named lanes with per-lane
ownership down to the file, expected outputs per lane, a status per lane, an integration order that
gives a reason for the sequencing (K1 first because every other lane keys against the shape it
defines), and a review handoff that names the note path and briefs the stage-8 domain reviewer on
the one question no shape check answers. The `Next Agent Bootstrap` section is present. Both
required sections exist.

And the criterion this phase most needed to get right is falsifiable and strong: "**On a covered
flop spot the strategy returns `bet` and `raise` with amounts**, and a test proves at least one
committed spot produces each." That is the one criterion that could have been the phase title
restated, and it names its own test instead.

## Blocker

- **1. Three of the four artifact-size figures do not reproduce, and they are the numbers stage 3
  puts to a human.** The contract, the ExecPlan and decision 6 all state: "one preflop line, one
  hero decision node, compact JSON, and only check and bet is **36 MB, or 2.4x the headroom**. As
  committed, indent and all, it is 99 MB. Ten hero nodes at three actions is 363 MB compact and
  1,481 MB as committed, 24x and 98x." Recomputed from the contract's own stated inputs
  (1,286,792 classes; 14.78 and 26.79 bytes per weight; 15,774,195 bytes of headroom):

  | case | contract | recomputed |
  |---|---|---|
  | 1 node, 2 actions, compact | 36 MB, 2.4x | 36.3 MiB, **2.41x** — correct |
  | 1 node, 2 actions, as committed | 99 MB | **65.7 MiB, 4.37x** |
  | 10 nodes, 3 actions, compact | 363 MB, 24x | **544.3 MiB, 36.2x** |
  | 10 nodes, 3 actions, as committed | 1,481 MB, 98x | **986.2 MiB, 65.6x** |

  The two errors run in opposite directions and both come from the same slip: the 363 figure is
  36.3 x 10, which applies the node factor and drops the 2-to-3 action bump; the 99 figure is
  1,286,792 x 1 x **3** x 26.79 = 98.6 MiB, which applies the action bump the compact case
  explicitly excludes ("only check and bet"); and 1,481 is that 99 x 15, applying the action bump a
  second time. So the compact ten-node case is understated (24x when it is 36x) and both committed
  cases are overstated by about 1.5x.

  This is a blocker rather than a tidiness note because decision 6 is `frozen-into-data`, the loop
  halts on it, and these multiples are the entire evidence Taylor is handed to choose between a
  binary encoding, fewer lines, a raised cap, and fewer nodes. Option 1's own arithmetic is
  measured against them ("Float32 at one node and three actions is 14.7 MB per line"). The
  conclusion survives — nothing fits, minimum 2.41x — so the ruling is not disturbed; the ask is.
  Fix by restating the three figures, or by stating one basis (nodes x actions) and deriving all
  four from it in one line so the next reader can check them the way this review did.

- **2. "The five existing mutation canaries" is six, and the sixth is the one that would break
  differently.** The criterion reads: "**The five existing mutation canaries that pin exact lines
  in `postflop_fallback.py` and `composite.py` are re-pointed with their claims unchanged, never
  retired.**" `verification/mutations.yml` holds six:

  - `fallback-answers-preflop`, `fallback-folds-guaranteed-chops`, `fallback-abandons-the-turn`,
    `fallback-turn-needs-only-one-safe-river` — `postflop_fallback.py`, witness
    `pytest_postflop_fallback`
  - `composite-routes-preflop-to-the-fallback` — `composite.py`, witness `pytest_postflop_fallback`
  - `fail-closed-can-invest-again` — `postflop_fallback.py`, pinning
    `_PASSIVE_ORDER: tuple[str, ...] = ("fold",)` at `postflop_fallback.py:103`, witness
    **`pytest_engine_fidelity`**

  The sixth is the one this criterion most needs to cover. It pins the fail-closed branch's refusal
  to invest — the branch a phase that starts returning `bet` and `raise` will reach for the first
  time — and it is the only one of the six whose witness command belongs to another phase, so
  re-pointing it wrongly reddens `pytest_engine_fidelity` rather than this phase's own command. A
  criterion that counts five leaves it outside the "never retired" obligation, which is exactly the
  accident phase 13 caught. Say "every existing mutation canary that pins a line in
  `postflop_fallback.py` or `composite.py`" and drop the integer: a count fixed in a contract also
  means a seventh canary landing before stage 6 needs a `contract-update` to be covered, which is
  the trap phase 14 hit by fixing its accepted-defect list at four in two places.

- **3. The contract declares `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` closed while the diff leaves the
  falsified claim standing in a file it rewrote.** That entry's own text names its remedy: "What
  must change is the stated compute rationale in both documents" — the phase 16 decision list and
  `docs/V2_ROADMAP.md` — "and that is a contract-shaped edit phase 16 owns." The decision list is in
  `approved_scope`, was rewritten at length in this diff (four other stale claims were corrected in
  it), and still says, verbatim: "What survives that is the ratio rather than the absolute: the
  turn is about 49 times a flop and the river about 2,350 times, whatever a flop turns out to cost.
  **Every conclusion below rests on the ratio only.**" MAINT-26 measured a turn-root solve at about
  1/212 of a flop solve and a river-root solve at about 1/38,000, because a flop-rooted tree is
  99.5 percent river nodes. The ratio is inverted, not imprecise, and the decision list declares it
  load-bearing for everything under it. Decision 1's "one flop spot is 49 turn spots and 48 rivers
  below each of those, before any preflop line is counted, and each has to be solved to a target
  exploitability rather than derived" is the same rationale stated as cost. Either correct both in
  the decision list, or move this ID from `Closed` to the explicitly-not-closed list with the
  reason. `docs/V2_ROADMAP.md` is in no scope this ExecPlan declares, so the second half cannot be
  done here in any case and needs saying.

- **4. "Filed here" filed nothing.** The criterion reads: "Filed here: the three stale claims that
  `data/artifacts/**` has no size check, in `docs/V2_RULING_MITIGATIONS.md` at 103 and 259 and
  `docs/V2_ROADMAP.md` at 161, corrected in this phase's decision list and owed elsewhere." It sits
  under `### The backlog entries this phase settles` and names no ID. `git show 35dbeb2 -- backlog.yml`
  is empty — the contract commit filed nothing — and no entry in `backlog.yml` covers either file's
  claim. Both files are outside `approved_scope` and outside every stage's expected scope in the
  ExecPlan, so the two wrong claims survive the phase with nothing tracking them and no ID a
  closeout could check. `docs/LOOP.md` is explicit that an item without an ID "is a note nobody
  reads again". File the entry and name its ID in the criterion (proposal in Alignment below), or
  put the two files in scope and correct them.

- **5. A criterion states an obligation and then names a check that does not test it.** "**A
  postflop key must not be mistaken for a preflop key by any existing reader.**
  `self_play_reference.py` recovers keys from the self-play inventory by scraping any token starting
  with `t` that holds at least three slashes, and it raises rather than returning empty. **A test
  pins what that reader does when a postflop key is present.**" The reading is confirmed —
  `self_play_spots()` adds every `t`-prefixed token with three or more slashes, so a postflop key
  shaped like `t6/...` is swallowed silently. But "a test pins what that reader does" is satisfied
  by a test asserting the reader swallows it. The bold obligation and the named check are different
  claims, and the weaker one is the falsifiable one, so this criterion is satisfiable without doing
  the work its own headline names. Restate the check as the obligation: with a postflop key present
  in the inventory, `self_play_spots()` returns no postflop key (or raises), and a test asserts
  that.

## Non-blocker

- **Determinism cannot be checked by anything, and both branches of its escape clause are satisfied
  by writing one field.** "**Determinism is proved by re-solving and diffing, not by checksumming a
  single run.** ... This phase repeats it for whatever config it commits and records the digest; if
  a run is not byte-identical, an accuracy target and the observed maximum divergence are recorded
  in place of the digest." Non-goals require the gate to pass with no GTOpen and no network, so
  nothing in the gate can distinguish two runs that agreed from one run whose digest was written
  twice, and the fallback branch makes either outcome compliant. The contract concedes this for the
  sibling criterion ("None of the three can be recomputed inside the gate") and not here. A
  falsifiable form: commit two separately labelled root-strategy digests from two runs plus the
  per-action divergence count as data fields, and gate that both fields are present and either
  equal or accompanied by a divergence figure. MAINT-26 already produces exactly those fields
  (`root_strategy_sha256` per run), so this costs the phase nothing.
- **Non-goals cover five of `AGENTS.md`'s six V1 boundaries.** PokerNow automation, browser and
  platform observation, runtime solver calls and the UI package are in the first bullet; heuristic
  guessing for a missing chart spot is in the second. "No large hand-history ingestion" appears
  nowhere in the section, and this is a phase that consumes a corpus to rank preflop lines, so it
  is the one boundary a reader might wonder about.
- **The ExecPlan says "Three of the five judgment calls are ruled"; the contract says "Three of six".**
  Six decisions exist once decision 6 is filed. The ExecPlan number predates the filing it describes
  two sentences later.
- **The ExecPlan miscounts the driven routes and contradicts the contract in the same diff.** The
  ExecPlan: "Three of its four routes were driven end to end ... the batch `REPORTS` route ... is
  recorded UNRUN". `docs/GTOPEN_SOLVER_NOTES.md` line 26: "**Driven end to end.** Four routes ...
  `POST /api/spot` ... `POST /api/solve` ... `GET /api/status` ... `POST /api/node`", and lists
  `/api/reports/*` and `REPORTS` separately under "Read from the README ..., never executed". Four
  of four were driven; `REPORTS` is a fifth route, never one of the four. The contract's Scope gets
  this right ("over four routes on flop boards"), so the two documents disagree.
- **The export-card criterion names no regenerator, and neither candidate is clean.** "The solver
  export's source card is regenerated in the same task." The card is
  `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json`. Of the two scripts
  that restamp its `headroom_bytes`, `scripts/extract_gtopen_preflop.py` talks to
  `http://127.0.0.1:3737`, which Non-goals forbid; and `scripts/convert_preflop_export.py` — the
  offline path — also rewrites `six_max_100bb_rakefree.json` and `sizings/six_max_100bb_rakefree.json`,
  which Regression expectations forbid moving ("A moved preflop number is a defect in this phase,
  not a result"). The converter is derived and should be byte-idempotent on the chart, so this is
  resolvable rather than contradictory, but the contract should name the script and constrain the
  edit to the card's `size` block. Related: neither script, nor the card, nor
  `data/artifacts/preflop/exports/**` appears in `approved_scope` or in any stage's expected scope
  in the ExecPlan, so as written the criterion has nowhere to land.
- **One of the three stale-claim line numbers is off by one.** In
  `docs/V2_RULING_MITIGATIONS.md`, line 103 is "Meanwhile `scripts/check_file_sizes.py` covers
  `reports/active/*.txt` ..."; the stale claim itself is line **104**, "`data/artifacts/**` appears
  in neither `LINE_LIMITS` nor `BYTE_LIMITS`", with its consequence on 105. Line 259 and
  `docs/V2_ROADMAP.md:161` are right.
- **"The refusal inventory keeps working at a non-flat table" names no measurement, and the backlog
  says it does not work there today.** `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` records the
  self-play inventory shattering into singleton rows at any non-flat table, which the criterion
  itself restates. So "keeps working" preserves a behaviour the repo has already recorded as broken
  and cannot fail. State what must hold instead — the generator does not raise, and the report
  prints the row count and the distinct-detail count so the fragmentation is visible.
- **Two figures in the contract have no producer yet.** "They agree on the top ten but for two
  swaps today" and, in the decision list, "3,048 decision points across 127 distinct spot keys". I
  verified 499 hands and 3,048 decision points against
  `reports/active/latest_sample_comparison_report.txt:44,46`; nothing in the tree publishes the
  127, the top-ten ordering, or the two swaps, and the contract's own neighbouring criterion says
  the filter it needs is "a different query that nothing in the repo computes today". Prefer stating
  the derivation and letting the phase's own report be the source, per
  `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT`.
- **`ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS` and `POSTFLOP-UNBEATABLE-EARLIER-STREETS` are listed
  as closed with no criterion doing the work.** The first is already fixed in the tree:
  `docs/GTOPEN_SOLVER_NOTES.md:39` says "The README's 1.4x and 2.2x are branch counts at the first
  chance node, not speedups", line 151 carries the 455/1,014/286 split, and the all-or-nothing
  precondition has its own paragraph — so it is closeable by a status flip, not by phase work. The
  second asks for the unbeatable call to be extended from the turn back to the flop; no criterion
  does that, and it becomes moot only because the flop is answered from a chart instead. Both are
  fine outcomes, but the `Closed:` list gives a reader no way to tell "settled by this phase's
  criteria" from "already landed" from "obsoleted". Say which, per the standing blind spot that a
  closing phase leaves its own entries un-reconciled and nothing checks.
- **"a test fails on absence or a placeholder" does not say what a placeholder is.** A test can
  only reject named sentinels. Name them (null, 0.0, empty string) or drop the word.
- **"five converged cells" and "7 of 30 solve rows" sit in the same decision list on different
  denominators without saying so.** Both are right — the five are `matrix-01` through `matrix-05`,
  the seven rows add the two determinism repeats, and `matrix-03`/`04` are reduced-tree duplicates
  of the same two boards — and the five do cover two rank patterns (connected and high). One clause
  saying "five distinct configs, seven rows including the determinism repeats" removes the reading
  where one of the two is wrong.
- **The contract is at 262 of the 300-line cap and owes a three-criterion amendment after stage 3.**
  The encoding, the per-spot byte budget and how many preflop lines fit are all still to be written,
  in `contract-update`, into 38 lines. Tight but not yet a blocker; flagged so it is not a surprise
  at stage 3.
- Two criteria carry structural claims nothing mechanical can check: "one producer, re-derived at
  import and at lookup" (the mismatch-refusal half is testable; "one producer" is not) and "Any
  range flooring is class-level" (assertable against the committed range payload, but no test is
  named). Both are worth a named test rather than a rewrite.

## Alignment

- `SOLVER-EXPORT-CARD-HEADROOM-COUNTS-THE-WHOLE-ARTIFACT-TREE` — the export card's headroom is a
  property of the directory, so every phase committing any artifact invalidates a card it never
  touched. Phase 16 is the second phase to pay this and the first for which the payment is a
  contract criterion. Existing entry; no new ID needed.
- `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT` and
  `PHASE-CONTRACT-LINE-CAP-FORCES-REWRITES-OVER-AMENDMENTS` — the 262-of-300 position above is
  these two entries arriving before the amendment rather than after it. Existing entries.
- `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` — the inventory criterion cannot be made
  falsifiable without deciding what the grouping key should be, which is this entry and not this
  phase. Existing entry.
- `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` — the pattern behind Blocker 1
  and the two producerless figures above: a contract states a measured level, nothing in the gate
  re-derives it, and the number outlives the build that produced it. Blocker 1 is the strongest
  instance yet, because the arithmetic was checkable from the contract's own stated inputs and no
  check exists that would have done it. Existing entry; this phase is another data point on it, not
  a fix.
- **New ID must be filed** — propose `TWO-DOCS-STILL-SAY-DATA-ARTIFACTS-HAS-NO-SIZE-CHECK`. Owner
  `contract-update` or `maintenance`. Content: `docs/V2_RULING_MITIGATIONS.md:104-105` and `:259`
  and `docs/V2_ROADMAP.md:161` state that `data/artifacts/**` is covered by no size check; it has
  been capped at 20 MB in `DIRECTORY_BYTE_LIMITS` since `2430894`, 2026-08-18. Neither file is in
  phase 16's scope. This is the ID Blocker 4's criterion should name.
- **New ID must be filed** — propose `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`.
  Content: this phase commits per-spot exploitability, iteration count and strategy digest that the
  gate cannot recompute by design, and its determinism criterion has an escape clause satisfied by
  either outcome. The general shape sits beside
  `AN-UNCHECKED-BINARY-IS-DESCRIBED-BY-A-CARD-NOTHING-READS` and
  `EQUITY-MATRIX-SHIPS-WITH-NO-COMMAND-THAT-READS-IT`, both of which are the same argument about
  committed data whose only witness is its own producer. Phase 16 cannot close it — it is the phase
  that makes it worse — so it needs an entry rather than a criterion.

## Method

Read-only throughout. Commands used: `git diff`, `git log`, `git show`, `git worktree list`,
`grep`, `sed -n`, `cat`, `wc`, `ls`, `find`, and `uv run python` for four read-only computations
(the flop isomorphism enumeration, the `action_weights` byte measurement, the converged-row scan
over `latest_postflop_solve_cost.txt`, and the artifact-tree byte total). No tracked file was
modified. `scripts/run_verify.py` and `scripts/check_gate_bite.py` were not run.
