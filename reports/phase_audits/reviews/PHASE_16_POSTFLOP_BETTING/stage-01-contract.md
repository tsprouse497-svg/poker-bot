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

Seven findings over four rounds. **All seven are verified fixed and marked `[resolved]`**, each with
the evidence recorded under it, so nothing in this section holds the stage. Round 1 filed blockers
1-5, fixed at `92c4f39`. Round 2 filed blocker 6, a contradiction the fix to blocker 1 introduced,
fixed at `62d8237`. Round 3 filed blocker 7, a units error the fix to blocker 6 introduced, fixed at
`161377f`. Round 4 verified that fix and found nothing new that holds.

Three of the seven were defects in a fix rather than in the original draft, which is worth recording
as a fact about this contract's history: each repair was smaller and more local than the one before,
and the last two were caught only because the reviewer re-derived the replacement figures instead of
reading the commit message. Every marked item was re-derived in this worktree; none is marked on the
strength of a coordinator's summary. A form note at the end of this section explains why blocker 2's
evidence is a table rather than a nested list.

Open non-blockers and alignment items remain below and are the stage's to carry, not to clear.

- **1. [resolved] Three of the four artifact-size figures do not reproduce, and they are the numbers stage 3
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

  **Verified fixed at `92c4f39`.** Decision 6 now gives the four cases as pairs and all four
  reproduce against my independent recomputation to the digit: 36 / 66 MiB at one node and two
  actions (I get 36.3 / 65.7), 2.4x / 4.4x (2.41 / 4.37); 544 / 986 MiB at ten nodes and three
  actions (544.3 / 986.2), 36.2x / 65.6x (36.18 / 65.56). The stated cause checks out exactly:
  `2,054,327 / 51,068 = 40.227`, the whole committed file over its leaf-weight count, which charges
  the per-spot `spots`, `arrival_ppb`, `arriving_reach_bp` and `audit_fields` blocks against every
  weight. The new lean-JSON chain is internally consistent and reproduces: 7,740,095 bytes against
  my structural estimate of 7,740,057, `0.49x` headroom (0.4906), and 2.04 / 1.02 / 0.68 nodes at
  two / three-with-two-free / three-with-all-three weights (2.038, 1.019, 0.679). Two residues are
  filed below as non-blockers rather than reopened here: the "43, 76 and 1,007 MiB" direct-build
  trio, which I could not reproduce and which covers three of the four cases; and blocker 6, which
  is the new framing colliding with option 2 of the same ask.

  On the framing question the coordinator asked: **yes, I would put the new framing to a human and
  not the old one.** The node count is the right axis because it is the one quantity no encoding
  moves, and the old lead invited the wrong ruling — a reader told "2.4x over" answers "change the
  format", and the fix's own measurement shows a format change defeats 2.4x while leaving the phase
  just as stuck. Re-arguing off "15 MB buys about one hero decision node for one preflop line, in
  any JSON" states the constraint at the altitude the ruling has to be made at.

- **2. [resolved] "The five existing mutation canaries" is six, and the sixth is the one that would break
  differently.** The criterion reads: "**The five existing mutation canaries that pin exact lines
  in `postflop_fallback.py` and `composite.py` are re-pointed with their claims unchanged, never
  retired.**" `verification/mutations.yml` holds six. Given as a table rather than as nested bullets
  because the advance gate reads any indented bullet under this heading as a finding of its own —
  see the form note at the end of this section:

  | canary id | file | witness |
  |---|---|---|
  | `fallback-answers-preflop` | `postflop_fallback.py` | `pytest_postflop_fallback` |
  | `fallback-folds-guaranteed-chops` | `postflop_fallback.py` | `pytest_postflop_fallback` |
  | `fallback-abandons-the-turn` | `postflop_fallback.py` | `pytest_postflop_fallback` |
  | `fallback-turn-needs-only-one-safe-river` | `postflop_fallback.py` | `pytest_postflop_fallback` |
  | `composite-routes-preflop-to-the-fallback` | `composite.py` | `pytest_postflop_fallback` |
  | `fail-closed-can-invest-again` | `postflop_fallback.py:103`, pinning `_PASSIVE_ORDER: tuple[str, ...] = ("fold",)` | **`pytest_engine_fidelity`** |

  The sixth is the one this criterion most needs to cover. It pins the fail-closed branch's refusal
  to invest — the branch a phase that starts returning `bet` and `raise` will reach for the first
  time — and it is the only one of the six whose witness command belongs to another phase, so
  re-pointing it wrongly reddens `pytest_engine_fidelity` rather than this phase's own command. A
  criterion that counts five leaves it outside the "never retired" obligation, which is exactly the
  accident phase 13 caught. Say "every existing mutation canary that pins a line in
  `postflop_fallback.py` or `composite.py`" and drop the integer: a count fixed in a contract also
  means a seventh canary landing before stage 6 needs a `contract-update` to be covered, which is
  the trap phase 14 hit by fixing its accepted-defect list at four in two places.

  **Verified fixed at `92c4f39`.** The criterion is now a predicate — "Every mutation in
  `verification/mutations.yml` whose `find` string pins a line in `postflop_fallback.py` or
  `composite.py` is re-pointed with its claim unchanged, never retired" — which covers all six
  today and any seventh without a `contract-update`, and it says why it is a predicate. The
  six-not-five count survives only as a historical note, which is the right place for it.

  On the coordinator's question, whether the `pytest_engine_fidelity` point belongs in the
  contract: **yes, and as one clause on this criterion rather than a criterion of its own.** The
  predicate now guarantees `fail-closed-can-invest-again` is re-pointed; what it does not say is
  why a wrong re-point of that one is the hard case to notice. Five of the six are witnessed by
  `pytest_postflop_fallback`; that one alone is witnessed by `pytest_engine_fidelity`, so a builder
  running this phase's own command after re-pointing sees green, and the damage surfaces only in
  another phase's gate at stage 7 — or not at all, if the `find` string silently stops matching,
  which is the phase 13 accident this criterion exists to prevent. Suggested clause: "one of the
  six is witnessed by `pytest_engine_fidelity` rather than this phase's own command, so re-pointing
  is verified by running each canary's own declared witness, not this phase's." That is one line
  and it is the difference between an obligation and a checkable one.

- **3. [resolved] The contract declares `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` closed while the diff leaves the
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

  **Verified fixed at `92c4f39`.** The ID is out of the `Closed:` list and now carries its own
  bullet making closure conditional: closed "**only** once no live document still asserts the ratio
  it falsifies", which is the correct condition and also the one that carries the out-of-scope
  `docs/V2_ROADMAP.md` half. In the decision list the sentence is now in the past tense ("was taken
  to be about 49 times a flop") followed by a dated falsification naming the measurement — 1/212 of
  a flop solve for a turn root, 1/38,000 for a river root, 99.5% river nodes, 158,466 river
  subgames — and stating that no conclusion below may rest on it. Decision 1 gains a second reason
  that does not depend on the ratio. One live residue remains at decision-list line 82 and one at
  `docs/V2_ROADMAP.md:215-216`; both are now governed by the closure condition rather than hidden
  by a closure claim, so they are non-blockers below rather than a reopened blocker.

- **4. [resolved] "Filed here" filed nothing.** The criterion reads: "Filed here: the three stale claims that
  `data/artifacts/**` has no size check, in `docs/V2_RULING_MITIGATIONS.md` at 103 and 259 and
  `docs/V2_ROADMAP.md` at 161, corrected in this phase's decision list and owed elsewhere." It sits
  under `### The backlog entries this phase settles` and names no ID. `git show 35dbeb2 -- backlog.yml`
  is empty — the contract commit filed nothing — and no entry in `backlog.yml` covers either file's
  claim. Both files are outside `approved_scope` and outside every stage's expected scope in the
  ExecPlan, so the two wrong claims survive the phase with nothing tracking them and no ID a
  closeout could check. `docs/LOOP.md` is explicit that an item without an ID "is a note nobody
  reads again". File the entry and name its ID in the criterion (proposal in Alignment below), or
  put the two files in scope and correct them.

  **Verified fixed at `92c4f39`.** Four entries exist in `backlog.yml`, one occurrence each, and the
  contract names all four under "Filed here, **with IDs rather than a promise**":
  `TWO-DOCS-STILL-SAY-DATA-ARTIFACTS-HAS-NO-SIZE-CHECK`,
  `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`,
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` and
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT`. The criterion also states that the
  three stale-claim sites are outside every scope this phase declares, which was the half of the
  finding that had no home.

  On whether the two new IDs duplicate `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT`:
  **I accept the split and withdraw the duplication concern.** That entry's mechanism is a level
  stated with no artifact named, so the repair is provenance. Neither new entry has that shape.
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` is the opposite failure — the 137
  had intact provenance, it was simply provenance to a different question, and naming the artifact
  harder would not have caught it. `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` is
  checkable from the page it appears on with no artifact at all, which is why this review caught it
  by arithmetic rather than by lookup. Distinct mechanisms, distinct repairs; each entry says so.

- **5. [resolved] A criterion states an obligation and then names a check that does not test it.** "**A
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

  **Verified fixed at `92c4f39`.** The criterion now reads "**A postflop key must not be returned by
  that reader**, and a test asserts the returned set contains no postflop key while the reader still
  finds every preflop one and still raises on an empty inventory", and it names the defeated reading
  explicitly: "A test that merely records whatever the reader does today would be satisfied by the
  reader swallowing a postflop key, which is the defect." That is stronger than my proposed form —
  it keeps both of the reader's existing guarantees under test, so a fix that empties the reader to
  pass the new assertion is caught too.

- **6. [resolved] Decision 6's ways-out list now contradicts decision 6's own measurement, in the direction of
  foreclosing one of the four options.** Introduced by the fix to blocker 1 and not present in
  round 1. The new framing paragraph states, of the leanest plausible JSON: "one two-action node for
  one line measures 7,740,095 bytes, which is 0.49x the headroom: **it fits, with room for a second
  node**." Option 2 of the list a human rules on, unchanged, still states: "**Fewer preflop lines.**
  Decision 3 already prunes on this axis and calls it the honest one. But **even a single line does
  not fit in JSON**, so this alone does not close the gap."

  Both sentences are about one line in JSON and they say opposite things. I verified the new one:
  `7,740,095 / 15,774,195 = 0.4906`, and my own structural build of that encoding gives 7,740,057
  bytes, so "it fits" is right and "even a single line does not fit in JSON" is now false as stated.
  The old sentence was true against the chart's format, which is the only format that existed when
  it was written; the fix introduced a second format and left the option describing the first.

  This is a blocker on the same grounds as blocker 1 and not a lesser one. Decision 6 is
  `frozen-into-data`, the loop halts on it, and this is the option list Taylor chooses from. Option
  2 is the axis decision 3 already calls the honest one, and it is currently annotated as unable to
  close the gap on its own — which the measurement above it contradicts. A human reading the list
  top to bottom is being told to discount the option the phase's own breadth ruling already favours.
  Fix by qualifying option 2 to the encoding it is true of ("even a single line does not fit in the
  chart's format") and saying what the lean-JSON measurement does to it: fewer lines plus a leaner
  JSON is a combination that reaches one node for one line, which is the actual frontier the other
  three options are being weighed against.

  **Verified fixed at `62d8237`, and the fix is better than what I asked for.** Rather than patching
  option 2, decision 6 now opens its options with a measured encoding table in nodes-per-line, which
  removes the soft spot instead of correcting one sentence. Every cell reproduces against my own
  walk (1,286,792 classes, 15.043 MiB of headroom, free weights only from the lean rows down): 98.62
  MiB/node/line and 0.15 nodes for chart-as-committed, 54.43 and 0.28 compact, 14.73 and 1.02 lean
  at three actions (stated 14.76 — a 0.2% rounding difference, and the affordable-node figure it
  drives is identical), 7.36 and 2.04 lean at two, 9.82 and 1.53 float32, 2.45 and 6.13 one-byte at
  three, 1.23 and 12.26 one-byte at two. The derived claims reproduce too: re-encoding worth "about
  40x" is 40.18; 5 nodes x 1 line = 12.27 MiB / 0.82x; 1 x 3 = 7.36 / 0.49x; 1 x 5 = 12.27 / 0.82x;
  3 lines x 5 nodes = 2.45x; 5 x 5 = 4.08x. Option 2 is qualified to the chart's format with the
  correction dated, and option 4 is marked as the only one that fits today without touching the cap
  and pointed at option 3.

  I also accept the stronger framing and do not think it overreaches. "No encoding, text or binary,
  fits several hero decision nodes across several preflop lines inside 20 MB" is exactly what the
  table shows, it is stated over the most favourable entry rather than a middling one, and the
  conclusion it draws — that the ruling is a choice between the coverage decisions 1-3 fixed and the
  cap — is the honest reduction. One residue, filed as blocker 7 rather than folded in here, because
  it is a new claim of its own rather than a defect in this one.

- **7. [resolved] The one-byte quantisation caution compares two different quantities and reads as a
  measurement.** New at `62d8237`. The table's most aggressive row is annotated: "binary, one byte
  per weight, which quantises a frequency to about 0.4% and so sits at the edge of the 0.3%-of-pot
  target it would be storing". The coordinator flagged this as their own claim and asked for it to be
  checked. The arithmetic half is right — one byte over [0,1] is a step of 1/255 = 0.392%, or
  0.391% at 1/256, so "about 0.4%" is correct. The inference is not.

  The two numbers are in different units and do not meet. 0.4% is a granularity in **action
  frequency**, a probability. 0.3% of pot is an **exploitability** bound, in pot fractions.
  Rounding a frequency by ε does not add ε of exploitability, and there is no general rate that
  converts one into the other; the loss depends on the EV gap between the actions whose frequency
  moved.

  Worse for the claim, the reasoning runs the wrong way where it matters most. Frequency rounding is
  cheapest exactly where frequencies are mixed, because a solver mixes only at hands it has driven
  to indifference, and at indifference the EV gap between the mixed actions is by definition near
  zero — so perturbing that split costs almost nothing in exploitability. And a pure strategy is
  lossless under this encoding in both directions, since 0 and 255/255 are exactly representable.
  What one-byte quantisation actually threatens is neither of those: it is the many near-zero
  weights, where rounding 0.002 to 0 or to 0.004 changes a rare action's frequency by a large
  relative amount — which is a different and smaller concern than the annotation states, and it is
  the one a reader should be told about.

  Why this is a blocker and not a non-blocker: it sits in the `frozen-into-data` ask, it is the only
  cost attached to the single table row the whole "40x is not enough" argument is anchored on, and
  it argues against that row on grounds that do not hold. A human weighing option 1 against option 3
  is being told the aggressive encoding is already at the edge of the accuracy target, which nothing
  measures. Fix by stating it as unmeasured — "the exploitability cost of one-byte quantisation is
  not measured anywhere in this repo; the granularity is 0.39% of frequency, which is not
  commensurable with the 0.3%-of-pot exploitability target and must not be read as approaching it" —
  or by dropping the clause and leaving the row's cost as the reviewability loss option 1 already
  names.

  **Verified fixed at `161377f`.** The clause is struck from the table's annotation rather than
  reworded, which is the better of the two repairs I offered: the row now carries no accuracy claim
  at all, and the correction lives in its own paragraph where it can be read as a correction. I
  checked each assertion in the replacement and each holds — 1/255 = 0.392%; the two percentages
  named as a frequency granularity against a pot-fraction exploitability bound with no conversion;
  "rounding a frequency does not add its own size to exploitability"; indifference implying a
  near-zero EV gap between the mixed actions; 0 and 255/255 exactly representable so pure
  strategies are lossless; and the near-zero tail named as the real exposure with `0.002 → 0`
  removing a rare action outright. Option 1's cost is back to the reviewability loss and nothing
  else, and the exposure is stated as the condition on option 1 rather than as an argument against
  it, which is the distinction that matters for a human reading four options.
  `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS` is filed and verified present, so every ID this
  note names now resolves.

  One refinement of my own argument, filed as a non-blocker below rather than held here: "a solver
  mixes only at hands it has driven to indifference" is an idealisation, and this phase's own
  decision 4 is the reason it matters.

### A form note the machinery requires

Not a finding, recorded here because it governs how this section must be written. `unresolved_blockers`
in `scripts/loop_stage.py:179-181` calls `line.strip()` before testing `startswith("- ")`, so an
**indented** bullet under `## Blocker` is indistinguishable from a top-level finding. I confirmed
this by importing the function and running it against this note: before the fix above it reported
four open items, of which three were mutation-canary names from blocker 2's evidence list and only
one was a real finding. Those three could not honestly be marked `[resolved]`, because a canary's
name was never a finding and marking it would assert a closure that never existed. Blocker 2's list
is therefore a table now, and no bullet appears at any depth under this heading. Every word of every
finding is unchanged. The defect is the coordinator's to carry, filed as
`REVIEW-QUEUE-COUNTS-EVIDENCE-BULLETS-AS-BLOCKERS`; the extension it now records — that this bites
the advance gate and not only the derived queue — is the part that matters, because a queue that
miscounts is noise a human filters, while an advance gate that miscounts refuses a stage for a
reason no one can resolve. Also worth stating: evidence tables are not a general substitute for
evidence, so the right long-term fix is the parser, not a house style that forbids sub-structure in
review notes.

## Non-blocker

### Round 3, from the fixes at `62d8237` and `161377f`

- **"A solver mixes only where it has driven a hand to indifference" is an idealisation, and
  decision 4 is why that matters here.** This is my own reasoning, now quoted into the decision
  record, and it should carry its caveat. At a *converged* equilibrium the claim holds and the
  argument built on it is sound. At a finite iteration count it is weaker: a hand can be mixed in
  the average strategy because regrets have not settled, not because the actions are genuinely
  EV-equal — and decision 4 states plainly that convergence at the committed iteration count is
  unproven, with both determinism runs stopping at 240 iterations. Where a mix is an artifact of an
  unconverged average rather than true indifference, the EV gap between the mixed actions need not
  be near zero, so "perturbing that split costs almost nothing" is not guaranteed for the strategy
  this phase would actually commit. This does not reverse anything: the paragraph's conclusion is
  that the cost is unmeasured, and this makes it more unmeasured rather than less. Worth one clause
  so the two paragraphs of decision 6 and decision 4 do not quietly disagree — something like "at a
  converged equilibrium; a mix in an unconverged average may not be a true indifference, which
  decision 4 leaves open."
- **The 14.73 versus 14.76 MiB rounding: leave the table as it stands.** The coordinator asked.
  Mine is 14.73 and the difference is 0.2%, the affordable-node column it drives is 1.02 either way,
  and the table exists to carry that column. Not worth a round, and re-touching a table that four
  people have now checked to move a figure by 0.03 MiB is a worse trade than the imprecision.

### Round 2, from the fix at `92c4f39`

- **Three of the four cases get a direct-build figure and I could not reproduce any of them.**
  Decision 6 now adds: "Building the structures directly rather than multiplying the rate gives 43,
  76 and 1,007 MiB, so the multiplications err low." Four cases are stated as pairs above it, so one
  — ten nodes at three actions, compact, the 544 MiB figure — has no direct-build partner and the
  reader cannot tell which three the trio covers. I built the chart-shaped structure directly and
  got 45 / 88 / 626 / 1,178 MiB, which agrees on direction for all three but on no value. The
  difference is my model rather than theirs, and I can now say so rather than guess: the parallel
  numbers-verification note in this directory carries the walk, and its 76.1 MiB / 79,812,696 bytes
  and 1,006.59 MiB are the source of the contract's 76 and 1,007. So the trio is derived, just not
  where it is stated. The fix is a citation, not a recomputation — name the note or the structure so
  the figures stop being three bare integers, and give the fourth case or say why it is omitted.
  The four rate-multiplied figures reproduce exactly and carry the argument on their own.
- **"So the multiplications err low" quietly moves the floor and the paragraph does not say where
  to.** If the direct build is the honest figure, the chart-format minimum is about 43 MiB and
  2.7-2.9x rather than 36 MiB and 2.4x. Nothing downstream depends on it now that the finding is
  argued off the node count, but 2.4x is still the number printed, and it is the one a later reader
  will quote.
- **One live sentence still states the falsified cost ratio inside the phase's own decision list.**
  Line 82, in decision 1: "**The cost is not linear:** one flop spot is 49 turn spots and 48 rivers
  below each of those, before any preflop line is counted, and **each has to be solved to a target
  exploitability rather than derived**." Both emphasised halves are what MAINT-26 falsified — a
  flop-rooted solve already contains and iterates its 158,466 river subgames, so those spots are
  derived rather than separately solved. The falsification 12 lines above covers the counts table
  and the ratio paragraph; this sentence is framed as cost and survives. It is a non-blocker only
  because the contract's new closure condition now governs it: `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`
  cannot be closed while it stands, so it cannot be lost. Worth fixing here rather than at closeout,
  since the file is in scope today and this is the sentence a later reader quotes.
  `docs/V2_ROADMAP.md:215-216` carries the same claim and is out of scope, which
  `TWO-DOCS-STILL-SAY-DATA-ARTIFACTS-HAS-NO-SIZE-CHECK`'s sibling problem now has no entry for —
  see Alignment.
- **"Twenty-two frozen tests name the query shape in their own body" does not reproduce; I get 21.**
  Counting test functions whose own body mentions `preflop_actions`, `StrategyQuery(` or
  `SeatAction(`: 13 in `test_strategy_contract.py`, 4 in `test_spot_vocabulary_downstream.py`, 3 in
  `test_table_state.py`, 1 in `test_engine_fidelity.py` — 21. Twenty-two is reachable under a
  slightly different predicate, which is the point: the number is not checkable because the
  predicate is not stated. The contract already says "Stage 4 measures the set again rather than
  trusting these three numbers", which is the right guard, so state the predicate or drop the count.
  The other two figures in that sentence do reproduce: "at most 334 sit in files that reference it
  anywhere" is exactly my count, and `test_rejects_a_bet_because_preflop_has_no_bet` is real
  (`tests/test_strategy_contract.py:408`) and is the only frozen test asserting that `SeatAction`
  rejects `"bet"` — every other `"bet"` in `tests/**` is a `legal_actions` tuple or a
  `StrategyDecision`, not a history action.
- **The 137 finding is otherwise fully repaired.** Regression expectations now state the obligation
  as a predicate over "the frozen tests of completed phases that assert against the query shape",
  name the one test that actually inverts, and record what the 137 was — phase 13's count of tests a
  lane got green after an unrelated rename — with the mechanism filed as
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE`.
- **Non-goals now names all six V1 boundaries** including large hand-history ingestion, and says so
  ("`AGENTS.md`'s six V1 boundaries"). My round-1 non-blocker is closed.
- **The `docs/V2_RULING_MITIGATIONS.md` line number is still 103 where the claim is on 104.**
  Unchanged from round 1 and still a non-blocker; noted only so it is not read as fixed. Line 103 is
  the "Meanwhile `scripts/check_file_sizes.py` covers ..." preamble; 104 carries the claim, 105 its
  consequence.
- **The contract is at 287 of 300 lines, and 13 lines is not enough. Tighten now, before the
  ruling.** The coordinator asked for a judgement and this is it. Three reasons.

  First, the arithmetic. Stage 3 produces two `frozen-into-data` answers, and the contract's own
  Scope paragraph commits to what they buy: the artifact's encoding, its per-spot byte budget, and
  how many preflop lines fit — three criteria, not one — plus decision 4's target and reproduction
  terms. Each of the existing criteria in that section runs three to six lines. Thirteen lines does
  not hold three criteria written to the standard of the ones already there, and the failure mode is
  that they get written to a lower standard because that is what fits, which is the stage-1 question
  arriving again at stage 3 with no reviewer scheduled for it.

  Second, `AGENTS.md` forbids the alternative. Its Contract Amendments section says a contract that
  reaches the cap "is a contract due for a rewrite that folds its amendments into the criteria they
  amend; that rewrite is its own `contract-update` task and **is not done to make room
  mid-amendment**", and "Never raise the cap to fit an amendment". So tightening after the ruling is
  the one route explicitly closed. Right now the phase is still at stage 1, still in
  `contract-update`, and no ruling exists yet — this is the only window where the tightening is a
  normal edit rather than a rewrite done under pressure to fit an answer already in hand.

  Third, the room is there and it costs no obligation. What has accumulated is the contract
  narrating its own review history, which now has backlog IDs to live in. Candidates I read as
  removable without dropping a single requirement: "not the five an earlier draft of this contract
  asserted" in the canary criterion; the "A test that merely records whatever the reader does today
  ..." sentence in the self-play criterion; the four-line "An earlier draft asserted 137, which is
  phase 13's count ..." passage in Regression expectations; and the phase 08/09 narration in the
  canary-coverage criterion. Every one of those is now recorded either in
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE`, in this note, or in the phase's own
  git history, and each leaves the criterion's predicate untouched. That is on the order of ten to
  twelve lines, which turns 13 of headroom into 23-25 and makes the stage-3 amendment writable at
  the standard the rest of the contract holds. Filed against
  `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT` in Alignment.

### Round 1, carried

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
- ~~**Non-goals cover five of `AGENTS.md`'s six V1 boundaries.**~~ **Fixed at `92c4f39`**; all six
  are now named. Original finding: PokerNow automation, browser and platform observation, runtime
  solver calls and the UI package were in the first bullet, heuristic guessing for a missing chart
  spot in the second, and "No large hand-history ingestion" appeared nowhere — in a phase that
  consumes a corpus to rank preflop lines.
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
  `PHASE-CONTRACT-LINE-CAP-FORCES-REWRITES-OVER-AMENDMENTS` — the line-cap position above is these
  two entries arriving before the amendment rather than after it. Round 1 measured 262 of 300; the
  fix at `92c4f39` took it to 287, so headroom fell from 38 lines to 13 while the stage-3 amendment
  it has to hold did not shrink. The lane-level recommendation is in Non-blocker round 2; what
  belongs to these entries rather than to phase 16 is the underlying shape, which these two rounds
  demonstrate cleanly: fixing review findings honestly *grows* a contract, because each fix records
  what was wrong as well as what is required, so the contracts that have been corrected most are the
  first to run out of room to be corrected again. Existing entries; this is a data point for them.
- `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` — the inventory criterion cannot be made
  falsifiable without deciding what the grouping key should be, which is this entry and not this
  phase. Existing entry.
- `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` — the pattern behind Blocker 1
  and the two producerless figures above: a contract states a measured level, nothing in the gate
  re-derives it, and the number outlives the build that produced it. Blocker 1 is the strongest
  instance yet, because the arithmetic was checkable from the contract's own stated inputs and no
  check exists that would have done it. Existing entry; this phase is another data point on it, not
  a fix.
- ~~**New ID must be filed**~~ `TWO-DOCS-STILL-SAY-DATA-ARTIFACTS-HAS-NO-SIZE-CHECK` — **filed at
  `92c4f39`** and named in the contract. Proposed content was: `docs/V2_RULING_MITIGATIONS.md:104-105`
  and `:259` and `docs/V2_ROADMAP.md:161` state that `data/artifacts/**` is covered by no size check;
  it has been capped at 20 MB in `DIRECTORY_BYTE_LIMITS` since `2430894`, 2026-08-18, and neither
  file is in phase 16's scope. Verified: one entry, one occurrence.
- ~~**New ID must be filed**~~ `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES` — **filed at
  `92c4f39`** and named in the contract as an entry this phase "makes worse rather than closes",
  which is the right framing. Verified: one entry, one occurrence. The determinism criterion itself
  is unchanged and stays a non-blocker above.
- `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` and
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` — filed at `92c4f39` from the
  parallel numbers review, both verified present. I raised whether either duplicates
  `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` and, having read all three,
  **withdraw the concern**; the reasoning is under blocker 4. The 137 and the 99-MB figure are the
  two instances, and both were caught by a reader doing arithmetic rather than by anything in the
  repo, which is what makes them worth entries.
- `REVIEW-QUEUE-COUNTS-EVIDENCE-BULLETS-AS-BLOCKERS` — filed and verified present, extended by the
  coordinator to record that the miscount reaches the advance gate and not only the derived queue,
  and named as the half of MAINT-29 that lands first. I agree with that ordering and with the
  diagnosis. What I would add to the entry, from having been the note it bit: the fix must key on
  the bullet's indent rather than on a house rule against sub-structure, because the alternative is a
  review format in which evidence cannot be listed, and the three lines this defect flagged as
  unresolved blockers were the six-canary inventory that made blocker 2 checkable. A parser that
  cannot tell a finding from its support pushes reviewers toward vaguer notes, which is the opposite
  of what the review stages exist for. Existing entry; nothing owed by phase 16.
- ~~**New ID must be filed**~~ `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT` —
  **filed at `5e7ef7f`/`62d8237`** with both instances, and verified present. Proposed content was:
  `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` was falsified in the phase 16
  decision list on 2026-09-08, and eleven lines below the dated falsification the same file still
  says "The cost is not linear: one flop spot is 49 turn spots ... each has to be solved to a target
  exploitability rather than derived", while `docs/V2_ROADMAP.md:215-216` states the ratio outright
  with no falsification anywhere near it. The general shape is that a dated correction attaches to
  the paragraph a reviewer was looking at rather than to the claim, so the claim survives wherever
  else it was restated — and this repo restates claims across documents by habit, which
  `THE-SAME-MEASUREMENT-IS-STATED-IN-TWO-COMMITTED-DOCUMENTS-AND-NOTHING-COMPARES-THEM` already
  records from the other direction. What is owed is a grep-shaped closure check: an ID whose fix is
  "correct the claim" cannot be closed while the claim's own text still matches anywhere in the
  tracked tree. Phase 16's contract now imposes exactly that condition on itself by hand, for one
  ID; nothing generalises it, and nothing would have caught it here if this review had stopped at
  the paragraph the fix touched.
- ~~**New ID must be filed**~~ `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS` — **filed at
  `161377f`** and verified present, with the `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`
  cross-reference. Proposed content was: blocker 7 above. An encoding
  choice's accuracy cost was stated by comparing a frequency granularity (0.39%, one byte over
  [0,1]) against an exploitability target (0.3% of pot) as though the two were the same scale. They
  are not commensurable, and the comparison happened inside a `frozen-into-data` option list where
  it argues against a specific encoding. The general shape is that this repo's solve vocabulary
  carries at least four percentages — exploitability as percent of pot, action frequency, range
  weight, and `allin_threshold` as percent of pot — and
  `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE` already records one unit confusion among them
  reaching committed config. What is owed is a habit rather than a check: any percentage stated
  next to another names its unit. Related to
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` but distinct — that entry is a
  figure that fails to reconcile against a rate in the same units; this is two figures in different
  units compared as if they reconciled, which no arithmetic check catches because the arithmetic on
  each side is right.

## Method

Read-only throughout, all three rounds. Commands used: `git diff`, `git log`, `git show`,
`git worktree list`, `grep`, `sed -n`, `cat`, `wc`, `ls`, `find`, and `uv run python` for ten
read-only computations — round 1: the flop isomorphism enumeration (22,100 boards, 1,755 classes,
455 rainbow, 1,286,792 hero-combo classes), the `action_weights` byte measurement, the converged-row
scan over `latest_postflop_solve_cost.txt`, and the artifact-tree byte total; round 2: the 40.227
whole-file-over-weights rate, a direct structural build of the chart-shaped payload at both node
counts and both indent settings, the lean parallel-array encoding, and a per-test-function scan of
`tests/**` for query-shape references; round 3: the full seven-row encoding table with its
affordable-node column and the five node-by-line combinations, and the one-byte quantisation step.
No tracked file was modified in any round. `scripts/run_verify.py` and `scripts/check_gate_bite.py`
were not run.

Rounds reviewed: `92c4f39` (round 2), `62d8237` with `5e7ef7f` (round 3), and `161377f` (round 4),
each against `git show` plus `git diff` over the three stage documents and `backlog.yml`. Round 3
also imported `unresolved_blockers` from `scripts/loop_stage.py` and ran it against this note, both
to confirm the parser defect and to confirm the restructured note reports only real findings; round
4 re-ran it and confirmed zero open items. Round 4 also re-checked that every backlog ID this note
names resolves to exactly one entry — seventeen IDs, all present.

Marks are mine and cover only what I re-derived here. No blocker is open. Nothing in this note
holds the stage; the non-blockers and alignment items are the stage's to carry.
