# Phase 14 stage 4 review: the tests, before the freeze

Two independent read-only reviewers, one mechanical and one on the poker, neither having written
any of the work and neither having seen the other's notes. The driver's question for this stage:
*would each test fail against a plausible wrong implementation, and does it assert on real
behaviour rather than on state rebuilt from the code under test? Stage 5 freezes these, so a weak
test is preserved perfectly.*

The diff under review: three new test files carrying the phase's own criteria, thirteen migrated
frozen test files of completed phases that the cutover makes false, eight mutation canaries, two
command registrations, and the task and plan metadata.

Both reviewers measured against the committed export rather than reasoning from the contract's
prose, and that is what produced everything below that matters. The coordinator re-measured every
blocker independently before acting on it, because a reviewer's report is not evidence either.

## Blocker

- `[resolved]` **Decision 10's monotonicity criterion cannot be satisfied at the ruled reach floor,
  and the number the contract rests on is a measurement of something else.** Found by the poker reviewer,
  re-measured by the coordinator: over the 5,626 nodes decision 1's 2 percent floor selects, the
  two relations at decision 10's ruled one-point tolerance give **1,938 violating nodes and 8,962
  violations**. Restricted to the 351 nodes where hero's whole range arrives - the shallow tree, on
  any reading - **36 violating nodes carrying 541 violations**. The contract's "one violation in
  the shallow tree" and decision 2's expectation that the re-solve removes it are both derived from
  the **eleven reference grids the export publishes**, not from the shallow tree. Those eleven do
  contain exactly one, which is reproducible and is why nobody saw the rest: the cold-call and
  multiway families were never read by anyone.

  The poker, which is what makes this a blocker rather than a counting dispute. The small blind
  facing a button open, four actions deep, hero's full range arriving, one of the commonest cold
  decisions in six-max, plays **22 at 99.94 percent, 33 at 16.20, 44 at 0.07 and 55 at 99.83**.
  Folding 44 essentially always while opening 22 essentially always is not a strategy at any
  tolerance. Others in the same family: the small blind facing a cutoff open with the button
  calling plays 86s at 0.67 percent and 86o at 34.02; the big blind closing a four-way limped-open
  pot for 1.5 into 11 plays KJs at 0.61 and KJo at 23.66, and the offsuit version more often than
  the suited one across the whole ace-x row.

  So decision 1's premise - "the nodes that are cheap to drop are the nodes that are wrong" - does
  not hold, and no floor rescues it: at 5 percent it is 1,108 violating of 3,296, at 20 percent 346
  of 891, and the shallow 36 survive every floor. Decision 2 permits a re-solve at a tighter gap or
  shipping one cell as solved with that recorded; neither disposition covers 8,962 violations, and
  the second would put 44-at-0.07-percent into the chart the bot plays.

  **Why the stage cannot resolve it.** Decisions 1, 2 and 10 are all `frozen-into-data`. Freezing
  the test as written leaves stage 6 with a red frozen test and only forbidden exits: re-tighten
  the floor (the contract calls that a halt), hand-edit a cell (forbidden in both branches of
  decision 2), or relax a frozen test (impossible after stage 5). Held for Taylor, with the
  substantive question being whether the permitted re-solve moves ahead of the freeze so the count
  is measured rather than guessed. The general lesson is filed as
  `SHALLOW-TREE-CONVERGENCE-WAS-NEVER-MEASURED-BEYOND-ELEVEN-NODES`.

  **Resolved 2026-08-24.** Taylor read the grids in GTOpen and ruled the splits correct: among
  near-indifferent hands every split has the same EV, so the frequency carries no information and a
  per-cell dominance gate rejects correct play. That is decision 2's ship-as-solved branch, so the
  re-solve is permitted and no longer required. Decision 10 is re-ruled to measure the relations per
  cell and publish them, and to gate the same dominance over pair bands and suited rows, where
  indifference cancels. Both are in the contract and the decision record as of this commit. The
  finding stands as recorded: the count was never a property of the shallow tree, and what the
  reviewer caught was a number three documents had quoted forward without a method.

- `[resolved]` **Decision 6 priced the jam only where it was hero's sole aggressive option, and a
  frozen test would settle the rest by omission.** Found by the poker reviewer, re-measured by the coordinator.
  At the **313** committed spots where the solve offers both a named raise and a jam, **60.6 percent
  of hero's aggressive volume over his arriving range is the shove**. It is the majority at **177**
  spots, at least 80 percent at **136**, and at **35** spots the named raise carries no weight at
  all. The chart would price hero's raise at the named size regardless, so at 136 committed spots
  the bot is taught to put in 22.5bb on a decision the solve plays as a stack-off.

  Decision 6 asked only about the 4,257 jam-only nodes, and its own stated reason - "the size is
  true rather than absent" - points the other way here. `test_a_jam_only_spot_is_priced_at_heros_whole_stack`
  currently generalises past its ruling in a comment. `frozen-into-data`, so held for Taylor. The
  schema limit underneath it, which survives whichever way he rules, is filed as
  `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT`.

  **Resolved 2026-08-24.** Taylor extended decision 6: the sizing table holds every size a spot
  offers with the weight hero gives each, on the reasoning that multiple preflop sizings are better
  play in some spots anyway. No re-solve is implied - the tree already offers both prices at those
  313 spots - and the spot key is untouched, since a key states what hero faces rather than what
  hero does, which keeps it clear of `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`. The same amendment
  corrects the original item's false claim that no committed spot would be absent from the sizing
  table; 3,865 of the 5,626 offer hero only fold and call. Solving *additional* 3, 4 and 5-bet
  sizes stays out of scope and is what the backlog entry now carries: measured through GTOpen's own
  estimator, a second re-raise multiplier takes the tree from 38,828 action nodes to 260,136 and a
  third to 606,378, so the artifact byte cap binds long before the solver does.

- `[resolved]` **Six exact measurements of the 300-iteration export were frozen in a file whose
  sibling mandates replacing that export.** Found by the mechanical reviewer, all six verified
  correct today and all six functions of the iteration count rather than the tree's shape. Removed
  with their claims intact: the one-percent comparison is now expressed as `floor / 2`, so it is a
  function of decision 1's ruling instead of a memory of a count, and the traced row is read off
  the node. `EXPORTED_NODES = 38_828` stays, because a re-solve at the ruled config builds the
  identical tree. The excluded probe went further than asked and is now derived at run time as the
  lowest-reach node, which resolves to 0.0 bp against a 200 bp floor with 5,266 nodes tied there,
  so no tightening of the gap can lift it over the floor and rob two tests of their subject.

- `[resolved]` **A fifth, undisclosed weakening: the price-substitution census test was vacuous.**
  Found by the mechanical reviewer. The migration dropped `assert "72" in report` and left only a
  check that the section heading exists - measured, `"substitution"` occurs once in the committed
  report and `"open"` twenty times - while its docstring still claimed "the split is what is
  asserted". A vacuous test in a frozen file is worse than a deleted one, because it reads as
  coverage. Now recomputes the opener-versus-later split from `ComparisonRow.price_substitutions`
  and parses all three figures out of the report by label, with both sides asserted non-empty.

- `[resolved]` **A canary that would not have bitten the command it named.** Found by the
  mechanical reviewer. `the-old-versus-new-comparison-reads-the-new-chart-twice` leaves
  `disagreements` at 0 over a nonzero overlap, which passed every case the report's validator
  specified, so `generate_derived_chart_report` would have rendered and exited 0. The repair at
  stage 7 would then have been to drop the command from `must_fail`, loosening the gate instead of
  the code. Closed on the test side rather than by rewording the canary, because the claim is right
  on its own terms: the two charts share no three-bet price and no small-blind opening price, so
  they cannot agree on a thousand shared corpus decisions. The report lane verified the new case
  bites by implementing the plausible incomplete validator in a stub, watching the test go red on
  that case alone, then adding the guard.

## Non-blocker

- **A concretely wrong chart passes all three new files, and the fix is free.** The poker reviewer
  built it: move ten points of weight from hero's most aggressive action to fold at every committed
  cell whose play frequency lies between 15 and 85 percent, which reaches 53.2 percent of the
  343,850 committed cells. Both dominance relations survive, both orderings survive because every
  position tightens together, every reach assertion is untouched, and `--check` passes because the
  converter did it. The result is a bot folding ten points too much in every mixed spot - decision
  3's accepted realization bias, doubled, and invisible. The proposed fix needs no new threshold:
  assert the chart's five opening and five defence frequencies equal
  `aggregate_frequencies(committed_export)`, export against chart rather than chart against chart.
  The reviewer checked the weighting agrees exactly at those ten nodes, where hero's reach is
  uniformly 10,000. Deferred into the same pass as the two blockers, because it touches the files
  their ruling will reopen and two edit rounds on a 700-line-capped file is how an authoring error
  gets in. Filed as `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL`.

- **The report test excludes the small blind from the defence ordering on the strength of the wrong
  chart's numbers.** Its comment cites 42.88 percent defence against a 34.41 percent open; those
  are the small-blind entries in the raked GTO Wizard reference. In the solve this phase commits the
  small blind opens 54.09 and the big blind defends 49.02, so the relation holds with twelve points
  of room and there was nothing to exclude. The reasoning is sound poker about a different chart.
  It also leaves two frozen files asserting different versions of one ruled ordering - the artifact
  file runs the full cross product, the report file only the four non-blind openers - so a re-solve
  that moved the small blind would turn one red and leave the other green. Deferred into the same
  pass, one tuple and a comment.

- **Adjacent-only at a point blesses a ladder that is not poker, and decision 10's reason for
  choosing it has since lapsed.** A grid drifting 0.9 points per rank passes, which over twelve
  steps is a chart opening 22 ten points more often than AA - and the report test deliberately
  asserts that it passes. Decision 10 chose adjacent over all-pairs to avoid sending ten noise
  cells to be hand-edited, and decision 2 then removed hand-editing from the phase entirely, so the
  reason no longer applies. All-pairs at the same tolerance gives 10,489 violations over 1,233
  nodes against adjacent's 1,975 over 1,185: 48 more nodes, strictly stronger, not materially
  noisier. The reviewer also checked the relations left out and agreed they should stay out -
  same-high-card adjacent kickers would over-fire on the A5s-over-A6s wheel inversion, which is
  correct poker. Belongs with the blocker-1 ruling since both concern decision 10.

- **Two of the eight canaries were re-aimed after review, and both would have failed silently.**
  The jam-pricing canary named `scripts/convert_preflop_export.py` while the frozen tests put the
  collapse rule in the `src/` module, and `check_gate_bite` requires the find string to occur
  exactly once in the file it names, so stage 7 would have halted on zero occurrences. The
  blind-structure canary replaced a line in `PreflopArtifact.to_payload()` and would have bitten
  only if the derived payload happened to be assembled through it; the one committed test that
  exercises `to_payload` round-trips it, so both dumps would have carried the same wrong structure
  and agreed. Both now target the derivation. The blind mutation triples the big blind rather than
  inverting the two, deliberately: an inverted structure the schema already rejects fails loudly,
  where 0.5/3.0 is a structure the schema accepts and only a comparison against the export's own
  `config_posted.posts` can catch. A third canary replaced a value with `QUANTISATION_SCALE`, which
  nothing requires that module to import, so it would have "bitten" by raising `NameError` rather
  than by publishing wrong reach; now a literal.

- **The header comment in `verification/mutations.yml` described a mechanism that does not run.**
  Written by the coordinator and caught by the mechanical reviewer. It claimed two canaries prove a
  wrong artifact fails the gate by leaving a bad file behind. No mutation touches anything under
  `data/` and `check_gate_bite` never regenerates the artifact, so the committed file stays correct
  throughout. What bites is the symmetric disagreement between mutated derivation code and the
  unchanged artifact, caught by `--check` and by the report's spot-count validation. The contract's
  criterion is still met - the comparison cannot tell which side moved - but a comment stronger than
  its check is how the next reader stops looking. Rewritten to describe what happens.

- `[resolved]` **Decision 5's reach field was checked as a property of the committed file, not as a
  rule.** The mutation helper repaired reach after every mutation, so no case could produce a
  reach/weights mismatch, and no rejection case targeted the field at all. The blind structure got
  five rejection cases and the limp rule one; reach, added in the same version bump, got none -
  which is exactly the objection `CHART-HERO-MUST-NEVER-LIMP` raises, honoured for limps and not for
  reach. Four cases added, and the helper now repairs reach only when the mutation left it alone, so
  there is no flag to forget.

- `[resolved]` **Two frozen-file hygiene items and a claim silently dropped for space.** A test
  asserted a list was empty and then looped over it, with a docstring claiming the loop still fires;
  the loop is gone and the docstring corrected. A migrated file loaded the library at module scope,
  where every other file this stage touched defers it into a fixture, so mid-cutover it would have
  failed collection and taken its twenty assertions with it - now behind a call. And the migration
  lane, making room under the line cap, found in its own diff that it had dropped the only assertion
  in `tests/` that a valid spot key exists at another table size and depth; restored, with the point
  stated that the grammar is not the coverage.

- **The stage's own red was hiding everything, and that is now fixed.** The first integration run of
  `pytest_derived_chart` died at collection with `Interrupted: 2 errors during collection`, so not
  one assertion in any of the three files executed, and the failure was an `ImportError` rather than
  the `ModuleNotFoundError` the driver accepts. That is `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`
  arriving exactly as filed, and phase 10 paid two separate repair tasks to it. All three files now
  reach not-yet-existing names through module attributes or function-body imports, which lint
  identically on both sides of stage 6. Result: 38 failed, 11 passed, 29 errors, zero collection
  errors, and 31 of the phase's tests now execute a real assertion against committed data instead of
  none. The same shape was hiding `tests/test_preflop_lookup.py` entirely - 32 tests that would have
  been frozen having never run once, seven of which now pass.

- **A measurement that overturned its own author's edit.** The migration lane raised the simulator's
  frozen run length from 6 orbits to 20 to keep an anti-vacuity guard alive, then, asked for
  evidence, measured the per-hand refusal probability under the derived chart at **0.00046** against
  about 0.21 today - a tree walk carrying arrival probability, agreeing with a 200,000-hand Monte
  Carlo, with the probability leak checked at 2e-17. No sane run length rescues the guard: 1,506
  hands for a coin flip, 10,009 for 99 percent. Reverted to 6 orbits with the measurement in the
  comment, and the guard made deterministic instead - a limping seat produces a spot that has no
  node at any reach floor, so the refusal is certain by construction and carries
  `lookup:spot-not-covered` rather than a table-shape code. It runs through `run_simulation` and
  `_refused_hand`, so both canaries aimed at refused-hand accounting stay guarded. The named gap is
  stated in the test: this driver cannot reach the table-shape codes, because the config rejects
  those before a hand is dealt.

- **A gate command that would have died three runs in four.** Following that measurement, the lane
  found `generate_sample_comparison_report` reads the self-play refusal inventory through a helper
  that raises on an empty read, and at 600 hands per run the derived chart expects 0.28 refusals -
  `P(zero) = 0.759`. A gate command whose answer depends on whether a run happened to find a refusal
  is not a check, and it would have surfaced as an intermittent stage 7 rather than as a finding.
  Filed as `SELF-PLAY-NO-LONGER-FINDS-COVERAGE-GAPS`, with the non-deferrable half named as phase 14
  stage 6 work.

- **Monotonicity is thinnest where the ranges are least trustworthy.** 530 of the 5,626 committed
  spots cover fewer than ten of the 169 classes and 192 offer two or fewer adjacent-pair
  comparisons, because a pair is skipped when either class is uncovered. The non-vacuity counter
  added this stage is pinned to the full-coverage spots, so it proves the relations ran somewhere
  rather than everywhere. Not closable at stage 4: a spot covering four classes genuinely has few
  comparisons to make.

## Alignment

- `SHALLOW-TREE-CONVERGENCE-WAS-NEVER-MEASURED-BEYOND-ELEVEN-NODES` - a solve capture owes a
  convergence statement over the nodes it selects, not over the grids a human read.
- `CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` - the schema cannot say "raise, at these two
  prices, this often each", and the solve mixes them at 313 committed spots.
- `ARRIVING-REACH-HAS-TWO-DEFINITIONS` - a threshold stated as a fraction of a range must state its
  weighting; class mean and combo mean differ by 770 nodes in one direction.
- `NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL` - the repo's only external reference
  is gated by nothing, which has become checked for nothing.
- `TEST-FILES-PINNED-AT-THE-LINE-CAP` - six frozen test files at exactly 700 lines, so every repair
  is its own task and must be net-negative.
- `SOLVED-PRICE-FIXTURE-HELPER-DUPLICATED-ACROSS-TEST-FILES` - one unwritten rule about which
  solved price is the named raise, stated in four frozen files and owned nowhere.

## What the reviewers confirmed rather than faulted

Recorded because a review that only lists problems tells a reader nothing about what was checked.

Every hardcoded stage-4 constant either reproduces against the committed export or was removed as a
solve property. The four disclosed weakenings in the migration were each judged handled honestly,
including the one that matters most: `TestSourceFrequencies` asserted ten frequencies within half a
point of a raked reference, which is false of a rake-free chart, and rather than widening the
tolerance to fit or deleting the repo's only external oracle, the lane split it into the part that
depends on the rake basis and the part that does not - keeping the two orderings, which hold at any
rake and any solver and break the moment a hand index is transposed, and adding the falsifiable
consequence that a rake-free chart matching a raked one everywhere within half a point would mean
the conversion moved nothing. The reviewer independently confirmed `ordering_errors` returns `[]`
on the reference. Command registration is clean, the two classes moved between files landed under a
command that still carries four mutations, nothing became ungated, `check_scope` and
`check_repo_consistency` pass, `base_commit` is the stage-3 close, and the six canaries not
mentioned above were judged to bite as described - including the two that deliberately omit a
command from `must_fail` and explain why, both of which the reviewer verified are true rather than
convenient.
