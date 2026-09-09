# Stage 1 review: the numbers behind decision 6's size finding

Read-only independent verification of the four assertions the phase 16 contract rests its halting
claim on. I did not write the contract, the ExecPlan, or the decision list, and I did not read the
numbers out of them and check the arithmetic. Every figure below was recomputed from scratch by
throwaway scripts in the session scratchpad, against the committed tree at `35dbeb2`. Where my walk
and the record disagree, both figures are given. No tracked file was modified, and neither
`run_verify.py` nor `check_gate_bite.py` was run.

Method, so the numbers can be re-run rather than trusted. The artifact tree was summed the way
`scripts/check_file_sizes.py:48-49` sums it, `rglob("*")` filtered to `is_file()`. The
combinatorics were brute-forced over all 22,100 three-card boards under all 24 suit permutations,
with hero's combo orbits enumerated explicitly under each board's own stabiliser subgroup rather
than counted by a formula, so a wrong formula could not agree with itself. The byte rates were
measured by re-serializing the committed chart's `action_weights` block. The projections were done
twice: once by transferring the measured byte rate, and once by building the actual nested
structure for all 1,755 flops and measuring it, because a rate transferred across a different key
shape is an estimate and I wanted to know which way it errs.

## What reproduces, to the digit

| claim | record | re-derived |
|---|---|---|
| `data/artifacts` cap | 20 MB | 20,971,520 bytes, `scripts/check_file_sizes.py:27-30` |
| tree currently held | 5,197,325 | 5,197,325 across 9 files |
| headroom | 15,774,195 | 15,774,195 |
| three-card boards | 22,100 | 22,100 |
| canonical flop classes | 1,755 | 1,755 |
| hero combos per flop | 1,176 | 1,176 |
| hero-combo classes, summed | 1,286,792 | 1,286,792 |
| mean classes per flop | 733.2 | 733.2148 |
| stabiliser sizes | {2: 1170, 6: 299, 1: 286} | identical |
| texture split | 455 / 1,014 / 286 | identical, sums to 1,755 |
| bytes per weight, compact | 14.8 | 14.784 (755,012 bytes / 51,068 weights) |
| bytes per weight, as committed | 26.8 | 26.789 (1,368,041 bytes / 51,068 weights) |
| one line, one node, two actions, compact | 36 MB, 2.4x | 36.3 MiB, 2.41x |

Three structural checks that were not asserted and that I ran because they are the ones that would
catch a wrong isomorphism: class sizes sum to exactly 22,100, so every board lands in exactly one
class and none in two; `orbit x stabiliser = 24` holds for all 1,755 classes; and every canonical
representative is its own canonical form. The weight count nobody stated is **51,068**, from 249
spot keys and 18,431 hand entries. The committed chart is `indent=2`, one byte of trailing newline
over `json.dumps`, so "as committed" is the correct label for 26.789.

Sections A, B and C of the finding are sound and they carry the argument. The defects are all in
the step from those measurements to the projection, and in one number imported from another phase.

## Blocker

- **`98x` is wrong; the figure is about `67x`.** `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:141`,
  and the same figure at `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:81` and
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:236`. Ten hero nodes at
  three actions, as committed, is 1,286,792 x 3 x 10 = 38,603,760 weights. At the published 26.789
  bytes per weight that is 1,034,156,127 bytes, 986 MiB, **65.6x** the headroom. Building the
  structure directly at `indent=2` gives 1,055,485,360 bytes, 1,007 MiB, **66.9x**. The asserted
  `1,481 MB` and `98x` are inflated by about 1.47x. This matters beyond tidiness: the packet
  promises a reader a number they can recompute from a committed file, and this one does not
  recompute from the rate the same paragraph publishes.
- **The `99 MB` one-node-as-committed figure is wrong; it is 66 to 76 MiB.**
  `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:80` and
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:234`, both reading "As
  committed, indent and all, it is 99 MB". At 26.789 bytes per weight over 2,573,584 weights it is
  68,943,742 bytes, **65.7 MiB, 4.4x** the headroom; built directly it is 79,812,696 bytes,
  **76.1 MiB, 5.1x**. Not 98.7 MiB and not 6.6x.
- **The `363 MB compact` row is a two-action figure sitting in a three-action sentence.**
  `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:81` and
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:236` read "Ten hero nodes
  at three actions is 363 MB compact and 1,481 MB as committed, 24x and 98x". 363 MiB is exactly
  1,286,792 x **2** x 10 x 14.784, so the x1.5 for the third action was dropped. At three actions
  the compact figure is 570,717,988 bytes, **544 MiB, 36.2x**, not 24x. Note this error runs the
  other way from the two above: the compact row is understated while the committed rows are
  overstated, so the pair cannot be repaired by scaling the paragraph.
- **The root cause is one substitution, and it should be named in the correction rather than left
  for the next reader to rediscover: the whole-file rate `40.227` was used where `26.789` was
  stated.** The committed chart is 2,054,327 bytes over 51,068 weights, which is 40.227 bytes per
  weight for the file as a whole. Both wrong "as committed" figures reproduce to the digit from
  40.227 and from nothing else: 2,573,584 x 40.227 = 103,527,564 bytes = 98.7 MiB, printed as
  99 MB; 38,603,760 x 40.227 = 1,552,913,454 bytes = 1,481.0 MiB, printed as 1,481 MB. That rate is
  not defensible as a projection rate. It charges the chart's `spots`, `arrival_ppb`,
  `arriving_reach_bp` and `audit_fields` blocks against every weight, but those scale per spot, and
  a flop artifact at ten nodes has about 17,550 spots, which at a few hundred bytes each is single
  digit MB against a figure near a gigabyte. Whichever way decision 6 is ruled, the phase's own
  report is required by the contract to print bytes used, headroom left and per-spot cost and to
  exit non-zero when a figure does not hold, so a per-weight rate that quietly includes non-weight
  bytes will not survive its own generator.
- **The bare "137 frozen tests" is another phase's lane bookkeeping and must not stand.**
  `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:258` asserts "The 137 frozen tests across the
  completed phases that assert the query shape are migrated in this task".
  `git log -S"137 frozen tests" --all` returns exactly two commits: `1ebbbb5` "Build the phase 13
  table-state query, strategy, and report", where it originates, and `35dbeb2` "Write phase 16's
  contract", where it is copied. The source line is
  `docs/exec_plans/completed/PHASE_13_TABLE_STATE.md:76`: "L2 done, all six producer files and all
  nine construction sites, 137 frozen tests green across three completed phases." That is phase
  13's count of frozen tests one of its lanes got **green** after the `street_bet` to `current_bet`
  rename, across the three phases completed at that time. It is not a count of tests asserting
  `StrategyQuery`'s shape, it does not describe phase 16, and phase 16's own ExecPlan and decision
  list never repeat it. The measured replacement is in the Alignment section below. It is a
  blocker rather than a non-blocker because the sentence is a regression expectation: a stage 4
  test author reading it goes looking for 137 migrations, finds one, and has no way to tell whether
  the other 136 are missing or were never real.
- **The framing is a blocker, and this one is my call rather than the coordinator's read of me, so
  I will state the reasoning.** The claim "the committed flop artifact does not fit the existing
  cap, by a wide margin, in the repo's existing JSON format" is true, and I could not break it. But
  it is argued from its most defeatable number, and a human ruling written off the current framing
  could reasonably come back "then change the format", which would send the ruling wrong. A
  plausible and still entirely JSON encoding fits the exact minimal case the 2.4x rests on: hoist
  the action names to a single `actions` array, store hero's classes as a parallel array in
  canonical order instead of a keyed object, three-decimal floats, and one free weight per class
  because two actions have one free parameter. Measured, not estimated: **7,740,095 bytes, 7.38
  MiB, 0.49x the headroom.** It fits, with room for a second node. So the lead number in the
  contract, the ExecPlan and the decision list is answerable by a format change, and a reviewer who
  spots that will conclude the halt was unnecessary.

  What survives, and survives decisively, is the node count, and it does not depend on the format
  at all. In that same leanest plausible JSON the headroom buys **2.04 nodes** at two actions,
  **1.02 nodes** at three actions storing two free weights, and **0.68 nodes** if all three weights
  are stored, and that is for **one** preflop line. The contract itself already says a flop is not
  one decision, at the `StrategyQuery` criterion: "hero acts, villain answers, hero faces a bet or
  a raise". Decision 3 asks for a head of common preflop lines, plural. So the sound statement, and
  the one I would put a human ruling on, is that **15 MB of headroom buys on the order of one hero
  decision node for one preflop line in any JSON encoding, and the phase needs several nodes across
  several lines, so no JSON encoding fits.** That is unanswerable by a format change, it is
  stronger than what is written, and it makes the ruling about coverage and storage location rather
  than about serialization. Argued that way, the halt is clearly right. Argued as 2.4x, it is not.

## Non-blocker

The stage can carry these. They are either correct as written and worth pinning so a later reader
does not "fix" them, or they are conservative in the safe direction.

- **The stabiliser split is not the texture split, and the shared 286 is a coincidence.** The
  cross-tab is: monotone 286 all at stabiliser 6; two-tone 1,014 all at 2; rainbow 455 splitting
  286 / 156 / 13 across stabilisers 1 / 2 / 6 by rank repetition, being distinct ranks, one pair,
  and trips. So {1: 286, 2: 1170, 6: 299} and {rainbow 455, two-tone 1014, monotone 286} are
  different partitions that happen to share the value 286, because rainbow-with-distinct-ranks is
  `C(13,3)` and so is monotone. Anyone who reads the two tables as the same partition will
  "correct" a right number into a wrong one. Worth one sentence wherever both appear.
- **Per-flop orbit counts take exactly five values, which is the cheapest available cross-check on
  the 1,286,792.** They are 1,176 on the 286 stabiliser-1 flops, 744 on the 156 rainbow-pair flops,
  721 on the 1,014 two-tone flops, 378 on the 13 rainbow-trips flops, and 344 on the 286 monotone
  flops. `286*1176 + 156*744 + 1014*721 + 13*378 + 286*344 = 1,286,792` exactly. That is a
  hand-checkable identity, and it is a better candidate for the packet's "one number a reader can
  recompute by hand" requirement than anything currently offered, because it needs no solver, no
  artifact and no script.
- **The direct-build figures run above the rate-derived ones, so the asserted minimum errs
  conservative.** Transferring 14.784 bytes per weight gives 36.3 MiB for one line, one node, two
  actions, compact. Building the real structure for all 1,755 flops, with six-character board keys
  and four-character combo keys, gives 45,057,026 bytes, **43.0 MiB, 2.86x**, which is 17.5 bytes
  per weight. The gap is structural rather than noise: a flop key is longer than a spot key and a
  combo key amortises over two actions where the chart's hand key amortises over three. So the
  transferred rate understates a real flop artifact by roughly 18 percent, and the asserted 2.4x is
  a floor rather than an estimate. This does not need fixing, but it should not be replaced by the
  higher figure without saying which method produced it, or the next reviewer will find two numbers
  for one claim.
- The headroom figure is already independently corroborated inside the committed tree.
  `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json:64` reads
  `"headroom_bytes": 15774195`, produced by `scripts/extract_gtopen_preflop.py:290` against the
  same 20 MB constant. Two producers agree, which is why section A needed no further work.
- The freeze lock is internally consistent right now, which is what let the frozen-test measurement
  below be trusted: `verification/freeze.lock` names 44 files and 961 test functions, every sha256
  matches the file on disk, every declared per-file `test_functions` count matches an AST walk, and
  no file under `tests/` is missing from the lock.

## Alignment

Long-term drift the stage cannot fix, each with an ID.

- **A figure copied out of another phase's completed ExecPlan passed every mechanical check this
  repo has.** Propose a new entry, **`AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE`**,
  which must be filed in `backlog.yml` because nothing existing covers it. The 137 travelled from
  `docs/exec_plans/completed/PHASE_13_TABLE_STATE.md:76` into
  `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:258` and nothing objected.
  `scripts/check_contracts.py` reads frontmatter, counts phase-specific acceptance criteria against
  a minimum, and reconciles contract phase IDs with `phase_status.yml`; it never looks at a number
  in a criterion. `scripts/repo_facts.py` guards ten named figures, all corpus and chart figures,
  none of them a count of tests, a byte total or a combinatorial figure. So a contract may state
  any integer about the repo and no check exists that could disagree. This is adjacent to
  `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` and sharper in one respect: there
  the provenance was absent, here the provenance exists, is traceable by `git log -S`, and points
  at a different phase's lane status. A number whose provenance is another document's bookkeeping is
  worse than one with no provenance, because it reads as measured. It is also an instance of
  `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` and of what
  `FACT-DRIFT-WATCHES-TWO-OF-A-DOCUMENTS-SIX-LIVE-NUMBERS` predicts, and both should be cross-cited
  when the new entry is filed. The cheap partial mechanism, offered because the entry should not be
  filed as an unbounded ask: a check that a phase contract's integers either appear in that phase's
  own decision list or report, or are registered as facts, would have caught this one.
- **A derived figure may be published beside the rate it was not derived from.** Propose a new
  entry, **`A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT`**, which must be filed.
  Three of the four wrong figures in the Blocker section sit in the same paragraph as the 26.789
  rate that contradicts them, in two documents, and one of them also reached the contract. The
  arithmetic is a multiplication of two numbers both published within four lines of the result, and
  nothing checks it. This is the same class as
  `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS`, moved from generated prose to a
  hand-written decision record, and the fix is the same shape: the figure is rendered from its
  inputs by the generator the contract already requires, rather than typed beside them.
- **The measured replacement for the 137, stated as I would want it in the contract.** The honest
  form is a bracket, not a figure, because "assert the query shape" has no crisp definition in this
  repo and any single integer would be a fourth unguarded number. Against
  `verification/freeze.lock` at 44 files and 961 frozen test functions: **exactly 1 frozen test
  must change, 22 name the shape in their own body, and at most 334 could be touched.** The one is
  `tests/test_strategy_contract.py:408`, `test_rejects_a_bet_because_preflop_has_no_bet`, which
  requires `SeatAction(0, "bet")` to raise "unknown history action" and which this phase inverts by
  widening `SeatAction`. The 22 are the frozen test functions whose own body names
  `StrategyQuery`, `preflop_actions` or `SeatAction`: 13 in `tests/test_strategy_contract.py`, 4 in
  `tests/test_spot_vocabulary_downstream.py`, 3 in `tests/test_table_state.py`, 2 in
  `tests/test_engine_fidelity.py`. The 334 are all test functions in the 9 files that reference the
  shape anywhere including module-level helpers, which is the loosest defensible reading. And the
  number that should be stated alongside them is **0**: adding a postflop history field breaks
  nothing if it defaults the way `preflop_actions` does at
  `src/poker_training_bot/strategy/contract.py:149`. Which means the migration this regression
  expectation describes is one test, and the criterion should say so, because a criterion promising
  137 migrations cannot fail in the direction that matters. Related:
  `FROZEN-TESTS-PREDATE-THE-SIZED-SPOT-KEY` is the same miss made by phase 12 and is marked done,
  so this is a recurrence of a closed pattern rather than a new one, and
  `SUBTRACTION-IDENTITY-SURVIVES-IN-FROZEN-TESTS-AND-CODE` is the standing reminder that a frozen
  suite can carry a superseded claim indefinitely.
- **Encoding is the wrong axis for the size question, and the repo will keep rediscovering that.**
  This belongs on the already-open `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`, which the phase 16
  contract correctly restates as not closed. That entry lists the available answers as raising the
  cap with a stated basis, splitting the artifact, storing solves outside `data/artifacts` with
  only derived charts inside, or standardising how a selection is recorded. My measurement adds the
  fact that entry is missing and that decision 6 needs: the four options are the whole option space,
  because **no JSON encoding is an option**. The headroom buys about one hero decision node for one
  preflop line even after every serialization saving available, so re-encoding is not a fifth
  answer and should be recorded as excluded rather than left for a future phase to measure again.
  Phase 14 hit this wall, phase 16 has hit it, and the entry's own prediction that "every later
  solve hits the same wall" is now two for two.
- **The 20 MB constant is stated in three places and the phase's report will be a fourth.**
  `scripts/check_file_sizes.py:29` and `scripts/extract_gtopen_preflop.py:58` each carry
  `20 * 1024 * 1024` independently, `tests/test_solver_export.py:515` restates it as a literal, and
  this phase's report must print bytes used and headroom left. The headroom in the committed source
  card is already a derived copy of a number two scripts compute separately. This is small and
  currently consistent, so it is alignment rather than a defect, but it belongs on
  `A-STALE-TREE-CARRIES-ITS-OWN-COPY-OF-THE-RULES`, which is the existing entry for a rule stated in
  more than one place, and it should be picked up by whichever task acts on decision 6, since that
  task is the one most likely to move the constant.

## What I did not verify

Named so the stage does not read this note as broader than it is. I did not check the solve-cost
figures, the exploitability or iteration counts, the corpus ranking, the arrival figures, or
anything about whether the resulting strategy is good poker. I did not run the gate. I did not
assess the contract's criteria beyond the four assertions and the one regression expectation put to
me. The scripts behind every figure here are in the session scratchpad and were not committed; each
is short enough to rewrite from the method paragraph above, which is the point of stating the
method rather than shipping the script.
