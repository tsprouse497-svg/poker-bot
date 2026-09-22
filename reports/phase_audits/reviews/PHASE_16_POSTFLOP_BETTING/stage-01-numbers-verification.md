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

All six were addressed at `92c4f39`. I re-derived every replacement figure before marking, from the
same scratchpad scripts and not from the commit message. All six are marked `[resolved]`, each with
the number I checked it against.

- **[resolved]** **`98x` is wrong; the figure is about `67x`.** `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:141`,
  and the same figure at `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:81` and
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:236`. Ten hero nodes at
  three actions, as committed, is 1,286,792 x 3 x 10 = 38,603,760 weights. At the published 26.789
  bytes per weight that is 1,034,156,127 bytes, 986 MiB, **65.6x** the headroom. Building the
  structure directly at `indent=2` gives 1,055,485,360 bytes, 1,007 MiB, **66.9x**. The asserted
  `1,481 MB` and `98x` are inflated by about 1.47x. This matters beyond tidiness: the packet
  promises a reader a number they can recompute from a committed file, and this one does not
  recompute from the rate the same paragraph publishes.

  Resolved. The contract criterion no longer carries a multiple at all, and the ExecPlan and
  decision list now read "986 MiB as committed ... 65.6x". Against my walk: **986.24 MiB, 65.56x**
  by the published 26.789 rate, and **1,006.59 MiB, 66.91x** built directly, which the documents
  also now state as 1,007. Reproduces.
- **[resolved]** **The `99 MB` one-node-as-committed figure is wrong; it is 66 to 76 MiB.**
  `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:80` and
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:234`, both reading "As
  committed, indent and all, it is 99 MB". At 26.789 bytes per weight over 2,573,584 weights it is
  68,943,742 bytes, **65.7 MiB, 4.4x** the headroom; built directly it is 79,812,696 bytes,
  **76.1 MiB, 5.1x**. Not 98.7 MiB and not 6.6x.

  Resolved. Both documents now read "36 MiB compact, 66 MiB as committed, 2.4x and 4.4x". Mine:
  68,943,742 bytes = **65.75 MiB, 4.37x**, so 66 and 4.4x are the correct roundings, and the 76 is
  stated alongside as the direct build. Reproduces.
- **[resolved]** **The `363 MB compact` row is a two-action figure sitting in a three-action sentence.**
  `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:81` and
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:236` read "Ten hero nodes
  at three actions is 363 MB compact and 1,481 MB as committed, 24x and 98x". 363 MiB is exactly
  1,286,792 x **2** x 10 x 14.784, so the x1.5 for the third action was dropped. At three actions
  the compact figure is 570,717,988 bytes, **544 MiB, 36.2x**, not 24x. Note this error runs the
  other way from the two above: the compact row is understated while the committed rows are
  overstated, so the pair cannot be repaired by scaling the paragraph.

  Resolved. Both documents now read "544 MiB compact ... 36.2x". Mine: 570,717,988 bytes =
  **544.28 MiB, 36.18x**. Reproduces, and the opposite-direction point is kept in both documents,
  which is what stops a later reader from "simplifying" the correction back into a single scaling.
- **[resolved]** **The root cause is one substitution, and it should be named in the correction rather than left
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

  Resolved. Named in both the ExecPlan and the decision list, with the per-spot argument intact and
  the 40.227 identified as the whole file over its weight count. The contract's criterion also now
  carries the forward guard: "No figure here is a per-weight rate that includes non-weight bytes;
  the generator exits non-zero on one that does not reconcile against the bytes on disk." That is
  more than I asked for and it is the half that keeps working after this stage.
- **[resolved]** **The bare "137 frozen tests" is another phase's lane bookkeeping and must not stand.**
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

  Resolved, and resolved better than I specified. The regression expectation now states the bracket
  rather than any single figure, names `test_rejects_a_bet_because_preflop_has_no_bet` in
  `tests/test_strategy_contract.py`, states the 0 for a defaulted field, records where the 137 came
  from, and tells stage 4 to measure the set again rather than trust the three numbers. Two things
  I checked rather than assumed. The test name is unique in the tree: one definition at
  `tests/test_strategy_contract.py:408` and no other reference, so citing it by name resolves, and
  by name rather than by line is the right call for the reason given, since the line moves whenever
  the file above it changes and the name does not. And the instruction to re-measure is the part
  that matters most, because my own three figures are a snapshot of the freeze lock at `35dbeb2`
  and this phase's stage 4 will add to `tests/**` before it migrates anything.
- **[resolved]** **The framing is a blocker, and this one is my call rather than the coordinator's read of me, so
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

  Resolved, and I was asked to check whether my argument was represented at full strength rather
  than softened. It is. All three documents now lead with the node count, and each of the four
  parts that make the argument unanswerable is present: that it holds in **any** JSON encoding and
  so no format change answers it; the lean encoding's measured 7,740,095 bytes at **0.49x**, stated
  plainly as fitting with room for a second node rather than buried, which is the fact that defeats
  the old lead and is the harder thing to publish; the **2.04 / 1.02 / 0.68** node counts; and both
  halves of the "several nodes across several lines" premise, the flop not being one decision and
  decision 3 asking for lines plural. The 2.4x is demoted to a secondary observation about the
  chart's own format, which is the right place for it, and the superseded draft is recorded with
  the reason it was wrong rather than quietly overwritten. Nothing was weakened. One phrase is
  stronger than I would have written and I think correctly so: "which is why no format change
  answers it" states the load-bearing consequence in the same sentence as the claim, where a
  reviewer cannot read the claim without it.

  **This blocker is resolved but it has an open consequence elsewhere, and the `[resolved]` above
  should not be read as clearing it.** Publishing my lean-encoding figure made a sentence further
  down decision 6 false. Option 2 of the ways-out list, at
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md:289-290`, still reads
  "even a single line does not fit in JSON, so this alone does not close the gap", which is
  contradicted by the 0.49x forty lines above it. The sibling review at
  `reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-01-contract.md` filed that as its
  blocker 6 while I was verifying this commit, and I agree with it: the sentence was true of the
  chart's format, the fix introduced a second format, and the option list was left describing the
  first. It is not a reopening of my blocker, which was about what the argument leads with and is
  genuinely fixed, but the stage should stay held until that one is closed, and a reader of this
  note alone would not know it exists.

  Two figures worth reconciling while both notes are open. That reviewer's independent build of the
  same lean encoding gives **7,740,057** bytes against my **7,740,095**, a difference of 38 bytes
  and 0.0005 percent, both 0.4907x the headroom. The agreement is close enough to treat the
  conclusion as robust and the gap is a reminder of what the number is: "the leanest plausible JSON"
  is an encoding *choice*, not a canonical quantity, so two careful people will land a few dozen
  bytes apart on key spelling or float formatting. Whichever figure the documents keep, they should
  keep one and say whose build produced it. I have no preference between them and would not spend a
  stage on 38 bytes.

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
  for one claim. Carried correctly at `92c4f39`: both documents now give 43, 76 and 1,007 MiB
  beside the multiplied pairs and say "the multiplications err low", which names the method for
  each of the two numbers rather than leaving a reader to guess which is which.
- **New at `92c4f39`, and a non-blocker because it weakens only the filing and not the finding:
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` attributes the unreconciled pair to
  the contract, and the contract is the one document where it was not checkable.** The entry opens
  "Phase 16's first contract draft published 26.789 bytes per action weight and, two clauses later,
  projections that only reproduce from 40.227". The 26.789 and the projections sat together in
  `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md` and
  `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md`; the contract at `:141`
  carried only the bare multiples, `2.4x` and `98x`, and published no rate at all. That distinction
  cuts both ways rather than just being a slip. In the two documents that published both, the
  arithmetic was checkable from the page and nothing checked it, which is the entry's thesis
  exactly. In the contract, the multiple had no divisor anywhere near it, so a reader could not have
  checked it at any effort, which is arguably the worse failure and is a second finding the entry
  currently folds into the first. Worth one sentence when the entry is next touched: a governing
  document that states a multiple without the rate it came from is not a reconciliation failure but
  an unfalsifiable claim.
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

Both proposed IDs were filed at `92c4f39` with my reasoning and my ID strings, and I was asked
whether either is really a duplicate of `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT`,
since the contract reviewer judged that existing entry sufficient. **Neither is, and the two
distinctions are different from each other.** The existing entry is about a number that *cannot* be
re-derived, because the build it was measured on is neither committed nor preserved, so its fix is
provenance. `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` is the opposite failure:
the provenance is intact, `git log -S` finds it in two commits, and the number is correctly
attributable to a document that was never talking about this phase. Adding provenance would not
have helped, because the provenance is what is wrong. `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT`
is a third thing again: the number was re-derivable from its own paragraph and nothing re-derived
it, so the fix is neither provenance nor attribution but rendering the figure from its inputs.
Three failure modes, three fixes, three entries. Folding them into one would produce an entry whose
remedy is "be careful with numbers", which resolves by assertion.

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

## The question put back to me: should the contract name the headroom figure

Asked at `92c4f39`: the decision record now carries 20 MB and 15,774,195 as a dated measurement,
but the contract's criterion deliberately does not repeat the headroom and instead requires the
phase's own report to recompute bytes used and headroom left and to exit non-zero when a figure does
not reconcile. Is leaving it out right, or does the contract lose something falsifiable?

**Leaving it out is right, and the rule underneath it is worth stating so the next contract does not
have to re-decide: name the constant, never the derivative.** The cap is a constant. It is
`20 * 1024 * 1024` at `scripts/check_file_sizes.py:29`, it has not moved since `2430894` on
2026-08-18, and a criterion asserting it is falsifiable forever, because the only thing that could
falsify it is somebody raising the cap, which is precisely the act the contract's Forbidden
shortcuts already prohibit. The headroom is a derivative: it is the cap minus the current tree, and
the current tree is the thing this phase exists to change. A criterion asserting 15,774,195 would be
false at this phase's own closeout, by construction and by design, because the phase succeeds
exactly by putting bytes into that tree. That is the failure mode
`COMPLETED-CONTRACT-ASSERTS-THE-CURRENT-TREE` is filed against, and writing the number in would be
signing up for it deliberately in a document capped at 300 lines where amendments only add.

Nothing falsifiable is lost, and I would go further: what replaced it is strictly stronger. A number
in a contract is inert. It sits there and no command reads it, which is the whole of
`AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` filed one section above. What the
criterion now requires is a generator that recomputes and **exits non-zero when a figure does not
reconcile**, which is a check that can fail, on every gate run, against the bytes actually on disk.
`AGENTS.md` makes the same distinction about criteria that merely restate the gate: they cannot
fail, so they prove nothing. A stated headroom would have been that, and the recomputation is its
opposite. There is also already a second, independent witness in the tree, which is why I raised the
corroboration as a non-blocker rather than as a gap:
`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json:64` carries
`"headroom_bytes": 15774195`, and the contract's own criterion notes that
`test_the_committed_export_sits_under_the_limit_with_stated_headroom` reds the moment any flop
artifact lands. So the number is pinned by a test and by a committed card, in the two places that
can actually go red, and the contract does not need to hold a third copy that cannot.

One caution rather than a change. The forward guard says no figure is "a per-weight rate that
includes non-weight bytes", and the same criterion asks for a **per-spot** cost. Those pull in
opposite directions and both are correct: a per-weight rate must exclude per-spot metadata, while a
per-spot cost must include it, since metadata is exactly what a spot costs. Whoever implements the
generator should not read the guard as forbidding a per-spot figure that divides total bytes by spot
count, because that division is right for that figure and wrong only for the other one. That is a
note for the implementer, not a defect in the criterion, and it does not hold the stage.

## What I did not verify

Named so the stage does not read this note as broader than it is. I did not check the solve-cost
figures, the exploitability or iteration counts, the corpus ranking, the arrival figures, or
anything about whether the resulting strategy is good poker. I did not run the gate. I did not
assess the contract's criteria beyond the four assertions and the one regression expectation put to
me. The scripts behind every figure here are in the session scratchpad and were not committed; each
is short enough to rewrite from the method paragraph above, which is the point of stating the
method rather than shipping the script.
