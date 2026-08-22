# Phase 13 stage 8 review - the phase

Read-only passes over `git diff phase-12-complete..HEAD`, the working tree on top of it, the
committed `reports/active/latest_table_state_report.txt`, and
`docs/phase_contracts/PHASE_13_TABLE_STATE.md`. Two lenses, as the driver asks: one mechanical,
one poker-domain.

**Delegated, unlike phases 10, 11 and 12.** Two independent read-only subagent reviewers ran
concurrently, neither seeing the other's work or output, and a third costed the competing fixes
for the sharpest mechanical finding before any code moved. That matters for this note's weight:
every prior phase self-reviewed at this stage and the stage-6 note records what that cost. The
two lenses found disjoint things, which is the argument for keeping them separate rather than
asking one reader for both.

## A correction to the record, made first because it changes how this note should be read

An earlier stage-8 poker pass ran and never wrote its note. It left its findings in the tree as
artifacts rather than prose: four backlog filings that cite "the phase 13 stage-8 poker review"
by name, a long addendum to `NORMALISER-MEASURES-DISTANCE-IN-BIG-BLINDS`, and two uncommitted
source fixes. Those findings are real and are kept. But a review whose only record is its own
diff is not reviewable, and one of its two fixes turned out to be half a fix that the mechanical
lens then caught (below). The reviewers for this note were given that earlier pass's filings and
told not to re-report them, so what follows is what those five did not cover.

## Blocker

- [resolved] **The blind ratio is never checked against the structure the charts were solved
  for, so the two commonest live and home structures are answered from a chart solved for a
  third one.** Found by the poker lens. `data/artifacts/preflop/six_max_nl25_100bb.json`
  declares `table_size` and `stack_depth_bb` and says nothing about its blinds.
  `StrategyQuery.blinds` carries the real ratio and nothing reads it for that purpose:
  `contract.py` validates only `0 < sb <= bb`, `SimulationConfig` the same, `corpus.py` accepts
  any two positive blinds, and no comparison of `small_blind` against `big_blind / 2` exists
  anywhere in `src/` or `scripts/`.

  Measured, hero in the small blind facing a 2.5bb button open, all 169 canonical hand classes
  through `weights_for`. At 50/100 hero pays 2.0000bb into 4.0000bb for 33.33% pot odds; at
  $1/$3, 2.1667bb into 3.8333bb for 36.11%; at $2/$5, 2.1000bb into 3.9000bb for 35.00%; at
  $5/$5, 1.5000bb into 4.5000bb for 25.00%. All four ask about the same key
  `t6/d100/SB/BTN:raise@2.5`. Zero of 169 hand classes moved a single weight in any of the
  three, and zero refused. An 11.1-point swing in the price hero is offered, and not one weight
  responds to it.

  It is blocker-grade because it falsifies the phase's own closing claim, and because it is this
  phase's standard applied inconsistently: phase 13 refuses a table where one live opponent's
  starting stack differs by a single chip, an effect of exactly zero, and answers a $5/$5 game
  where the small blind's dead money is doubled. The contract names home games twice, and $1/$3
  and $2/$5 are the dominant live and home structures.

  **Ruled by the coordinator: not fixable in this phase, and the honest half done instead.** The
  check itself is cheap and needs no format change, because the blinds are already on the query.
  What is missing is the other operand. The ratio the artifact was solved at is recorded nowhere,
  so any check written today would hardcode a reconstruction of an undeclared property of a
  committed artifact, which is precisely the defect this phase exists to end appearing inside the
  phase that ends it. `data/artifacts/**` is out of `approved_scope` and is a loop halt condition,
  and declaring the structure is a chart-phase change.

  So the fix is the truth, following the stage-6 precedent where the straddle residual was closed
  by restating it rather than by guarding it. The report's headline claim now reads that a table
  whose **stack depths or forced money** the charts cannot describe is refused, names both
  escapes, and publishes the four-row measurement above with its own validator: the report
  refuses to publish if any structure stops reaching a cell, if two prices coincide, or if any
  class ever answers differently. Falsified in the other direction by monkeypatching `weights_for`
  to be blind-aware, which raises with "47 of 169 hand classes now answer differently at $1/$3".
  The report explicitly does not claim the correct ranges differ, only that they cannot differ
  here because nothing looks. Filed as `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE`
  against phase 14.

## Non-blocker

- [resolved] **`preflop_actions` accepts a betting sequence no street can produce, and the
  earlier pass's fix relocated the defect instead of removing it.** Found by the mechanical lens,
  and the most consequential finding in the round. Both walks in `table_state/forced_money.py`
  start their level at the declared big blind and move it to each recorded raise-to, so a
  raise-to *below* the standing level DROPS the level and corrupts every later increment. The
  earlier pass clamped `predicted_min_raise_target` with `level = max(level, entry.amount)` and
  left `predicted_contributions` unclamped eight lines away, in the same module, under a comment
  that describes exactly the corruption the sibling still performs.

  Measured at 50/100 six-handed, button seat 3, history `LJ fold, HJ raise 250, CO raise 200,
  BTN call, SB fold, BB call` with an offered `min_raise_target` of 400. Before the clamp: the
  min-raise walk predicts 350 against the offered 400 and the strategy announces
  `pot-holds-a-straddle`. After the clamp: that signal goes quiet and the contributions walk
  predicts `{0:0, 1:250, 2:200, 3:200, 4:50, 5:200}`, leaving 50 chips unexplained at each of
  seats 2, 3 and 5, and the strategy announces `blind-structure-not-representable` naming one of
  them. Both are poker claims about a pot with nothing forced in it. One false claim was traded
  for another.

  A costing pass measured three candidate fixes before any code moved, and the result is worth
  recording because the obvious one is wrong. **Clamping both walks is fail-open.** With both
  clamped, all three signals go quiet and the impossible pot reaches the chart. The clamp does
  not repair the history, it launders it. That is the failure mode `forced_money.py`'s own
  docstring names.

  The demonstration in this note and in the canary description originally said the six-action
  history above is then *answered*. **That was false, and the independent verifier caught it.**
  On that history the key-space builder refuses independently, on action order alone:
  `preflop-chart:lookup:unrepresentable-spot`, `BB facing ['HJ:raise@2.5','CO:raise@2',
  'BTN:call','BB:call'] has no spot key; no legal preflop order produces it`. The verifier
  produced a stronger example that does fail open, and it is now the one on the record: a
  sub-level raise whose action *order* looks perfectly legal, `LJ raise-to 80` under a big blind
  of 100. Both walks clamped, `unexplained` is empty and the predicted minimum raise matches the
  offered 200, so the pot reaches `ChartHit(spot_key='t6/d100/BB/LJ:raise@2.5',
  price_substitutions=((0, 0.8, 2.5),))` and the bot returns a real poker decision,
  `preflop-chart:weighted-draw:raise`. A 0.8bb "raise" laundered into the nearest priced open the
  chart holds and answered with the 2.5bb open's range. Unclamped, both histories refuse as
  `pot-holds-a-straddle`, so the rest of the entry stands. Recording this correction matters more
  than the outcome: the wrong example was about to be committed into a permanent registry entry,
  and it was wrong in the direction that made the fix look better justified than its own evidence
  supported.

  **Fixed at the boundary instead.** `StrategyQuery.__post_init__` now walks the level through
  the existing `preflop_actions` loop and refuses a raise-to at or below it, so the impossible
  record cannot construct: `preflop_actions records seat 2 raising to 200, which does not exceed
  the standing level of 250; no betting round produces that`. The clamp is reverted, because
  under the boundary rule it is provably unreachable and a dead guard whose comment claims a live
  threat is a worse artifact than either the bug or the fix. Both walks are now correct by
  construction, and so is the third walk somebody writes next.

  Cost, measured rather than argued: 954 tests pass, 13,556 `StrategyQuery` constructions across
  every producer and both full corpus walks, 199,421 instrumented walk calls, zero non-monotone.
  No frozen test moves. `poker_core/engine.py` already raises `raise target must exceed the
  current bet`, so no live producer can emit one of these and the channel is exactly the
  hand-computing report producers that decision 15 names as the phase's sharpest false-positive
  source.

  **Decision 15 was checked and is orthogonal, and the reasoning is recorded here rather than
  implied.** Its subject is one field, `min_raise_target`, and its answer forbids checking that
  field against a reconstruction, on the stated ground that the correct minimum raise is only
  reconstructable preflop. The boundary rule adds no rule about `min_raise_target` and needs
  nothing the query lacks postflop, because it walks `preflop_actions`, which are either present
  and well-formed or empty. The positive precedent is decision 3, one field over, which rejects a
  query whose pot does not equal the sum of contributions and records honestly that the check
  cannot fail at the live producers and bites only at the hand-computing ones. Decision 15 is
  `runtime-reversible` and no frozen test asserts the behaviour, so this stays an implementation
  edit rather than a `contract-update`. A literal reader could stretch decision 15's phrase "does
  not validate it beyond the existing positivity rule" from the field to the min-raise story
  generally; if that read wants foreclosing, decision 15 takes a `Correcting...` paragraph in the
  style decision 16 already uses, and that needs `reports/phase_audits/decisions/` in scope.

- [resolved] **A blocker fix that nothing in the gate could catch, for the second time in this
  phase.** Found by the mechanical lens. The earlier pass's other fix changed
  `preflop_chart.py:208` from `min(forced.items())` to
  `max(forced.items(), key=lambda pair: (pair[1], -pair[0]))`, so a blind-structure refusal names
  the seat holding the most forced chips rather than the lowest-numbered seat. Nothing
  distinguished the two: the only residual probe had exactly one unexplained seat, the only
  behavioural test asserts the code alone, and the published line `(seat 0, forced_chips 100)` is
  identical under either rule. Reverting it left every test green.

  This is the same defect this phase already paid for at stage 6 round two, where reverting the
  extremal-seat selection in both copies left all 954 tests green because no frozen test put two
  live seats on the same side of hero. Closed the same way: a new census probe with two dead
  blinds of different sizes (lojack owes 50, hijack owes 100), and `validate_residual_seat`
  recomputes the expected seat from the seat states and refuses to publish unless a distinguishing
  probe exists. Verified by hand in both directions - with the fix the generator exits 0 and
  publishes `(seat 1, forced_chips 100)`; with `min(forced.items())` restored it exits 1 naming
  the seat it should have picked.

- [resolved] **The merged-key demonstration verified a pair of English labels, and its published
  claim was false for one table in each pair.** Found by the mechanical lens.
  `measures.merged_key` raised only when its two arguments were equal - two string literals
  written by the caller eight lines away - and then returned a key composed from a literal
  action sequence with no reference to either table. The report published `the key both render
  t6/d100/BB/CO:raise@2.5,BTN:call`, and the short-all-in table never renders it: it is refused
  `a-live-seat-is-shorter-than-hero` before any lookup happens. The under-raise pair was worse -
  only one of its two tables was ever constructed.

  The section's substantive conclusion was right and was shown; it was the sentence and the guard
  behind it that asserted something nothing measured. Replaced with `one_key_two_tables`, which
  checks the pair rather than the labels: the two tables must agree on all four things a spot key
  is made of, the key is read off the lookup that actually happened rather than composed, and the
  two refusals are named. The missing second table of the under-raise pair is now constructed. All
  four outcomes are on the page, and the report says plainly that one of the two rendering the key
  and the other not **is the finding closing** rather than the demonstration failing.

- [resolved] **The census printed the deleted arithmetic bound beside the new verdict and never
  compared them.** Found by the mechanical lens. `bound_verdict` reproduces the retired rule for
  every probe, which reads as a checked coverage comparison, and nothing related the two columns;
  the contract's requirement that the replacement refuses every pot the bound refused rested
  entirely on one frozen test covering two pots. `validate_bound_coverage` now asserts the
  implication the report's own data supports, `bound refused` implies `verdict is not CLEAN`, with
  a non-vacuity clause requiring the antecedent to fire. It holds on all 10 probes, 5 of which
  exercise it. Falsified by monkeypatching `unexplained_contributions` to return `{}`, which
  raises on the ante row.

- [resolved] **Two guards inside the validators could not fail for any input or any
  implementation.** Found by the mechanical lens, the third instance in this file after the
  stage-6 note found one. `under_raises > facing_a_raise` and
  `short_all_in_calls > with_a_recorded_call` hold pointwise by construction, because the
  predicates that increment the numerator each require the entry the denominator counts. The
  census `accounted == len(probes)` is the same shape: `forced_money_verdict` is a `.get` with a
  default over four names and can return nothing else. Strengthened rather than deleted, after
  confirming no canary reaches the gate through them: the corpus comparisons become
  `under_raises == 0` and `short_all_in_calls == 0`, which is what the report's prose already
  claims and what the committed figures show, and the census check becomes
  `_validate_verdict_coverage`, which enumerates every `REFUSE_*` the strategy declares and fails
  on any code in neither the verdict map nor an explicit hand-listed exemption - so a refusal code
  added later cannot be silently counted as a clean pot.

- [resolved] **The fix round pushed two modules past the 500-line cap** (`measures.py` to 613,
  `contract.py` to 515), which fails `check_file_sizes`. Split on a named seam rather than at a
  line number, with the canary `find` strings verified to still occur exactly once in their
  declared files.

- **A depth refusal names one side of a pairwise quantity.** Found by the poker lens.
  `_depth_refusal` emits `seat`, `starting_chips` and `stack_depth_bb` for the offending villain
  and hero's own depth appears nowhere, for either `a-live-seat-is-shorter-than-hero` or
  `table-is-not-one-flat-stack-depth`. Effective stack is `min(hero, villain)` and a tolerance is
  a ratio or a difference, so both need both numbers: a 20bb opponent against a 100bb hero and a
  20bb opponent against a 25bb hero are one row today and are different tables. The detail's
  stated purpose is to carry a figure that cannot be backfilled, and half of it cannot be
  backfilled either.

  **Not fixed here, and the reason is that it pulls against a finding the earlier pass already
  filed.** Adding `hero_starting_chips` and `hero_stack_depth_bb` is additive and changes no
  refusal code, but `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` says the tuple is already
  too high-cardinality to group, so fixing the completeness half alone deepens the fragmentation
  half. One design answers both - a per-code grouping key plus a complete pairwise detail, ruled
  once - and it lives in `simulator/measure.py`, which this phase has no business in. Appended to
  that existing entry rather than filed separately, so whoever picks it up sees both halves.

- **Pre-existing and not this phase's**: `uv run pytest` fails collection with
  `No module named 'scripts'` on 13 modules. The gate invokes `uv run python -m pytest`, which is
  fine, so this bites only a human running the short form by hand.

## Alignment

Filed in `backlog.yml` rather than left here, as the loop requires.

- `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` (phase 14) - the blocker above, with
  its measurement. The fix needs the artifact to declare its blind structure first.

- `COVERING-STACK-REFUSES-WITH-NO-POKER-CONTENT` (strategy) - found by the poker lens. Effective
  stack is pairwise and is the minimum, so a 100bb hero against opponents who all cover is playing
  exactly the 100bb game the committed chart solves, and the bot refuses. Measured at 50/100 with
  hero pinned at exactly 100bb over 4,000 six-handed tables with the other five stacks uniform in
  40-300bb: 3,997 (99.9%) refuse `table-is-not-one-flat-stack-depth`, 3 (0.1%) refuse
  `a-live-seat-is-shorter-than-hero`, and 1,046 (26.1%) are tables where every live opponent
  covers hero. A villain one chip deeper is enough. This is a stronger claim than the stage-6
  note's decision-7 finding, which argued about ordering: it says the deeper branch should not be
  a refusal at all. Alignment rather than blocker because Taylor ruled decision 6 at exact
  equality on 2026-08-21 and frozen tests pin it. What the record should carry is that the
  question he was shown framed its alternative entirely around an opponent "short enough to
  change the price hero is being offered" - the covering case was never put to him, and the
  deeper check inherited exact equality from a pre-existing rule rather than by ruling.

- `LIVE-BLIND-LEVELS-MAKE-ORDINARY-OPENS-UNRENDERABLE` (phase 14) - found by the poker lens.
  `_size_bb` refuses a raise-to that is not an exact hundredth of a big blind, a property of the
  blind level rather than of the poker. At 50/100 it never fires. In a $1/$3 game a $10 open, the
  standard live open, renders as 3.333bb and is refused, while $9, $12 and $15 all render exactly
  and are answered by substituting down to the solved 2.5bb; in $2/$5 nothing refuses at all and
  every open from 3bb to 6bb collapses onto one cell. So the only price guard in the chart path
  fires on a divisibility accident, uncorrelated with how far the asked price is from anything
  solved. Same fix as the addendum on `NORMALISER-MEASURES-DISTANCE-IN-BIG-BLINDS`: a bound on
  substitution distance. The two should be taken together.

- **Appended to `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL`** - the pairwise-detail finding
  above, for the reason given there.

- **The loop adds no canary for a fix landed after stage 4.** Raised by the mechanical lens.
  `verification/mutations.yml` is authored before implementation by design, which is right; the
  consequence is that every fix found at stage 6 or 8 arrives with whatever coverage happened to
  exist. This phase alone produced three instances - the stage-6 extremal-seat hole, and both
  earlier-pass fixes in this note - and each was closed only because a reviewer asked for a canary
  by hand. It is loop-process work, not phase 13's.

- **`preflop_actions` was validated as a bag of seats rather than as an action sequence.** Raised
  by the mechanical lens as the shared root of the boundary finding and decision 15's
  "sharpest false-positive channel": the query accepted a history no betting round can produce,
  and three consumers each reconstructed their own inconsistent defence against it. The boundary
  rule closes it for this class, and the general point belongs beside
  `SEAT-STATE-MARKERS-AGREE-WITH-NOTHING`, since the answer is one validation rule rather than
  three patches.

- **Unfalsifiable guards inside report validators recur here.** Raised by the mechanical lens:
  three found in this one file across two stages. A cheap mechanical check exists - a validator
  whose predicate is provable from the types of its inputs - but building it is not phase 13's.

## The verification round

A fourth independent read-only subagent then tried to break the fix round, having seen none of
the three workers' reports. Its brief was the failure mode this phase has already produced twice:
a fix for a blocker that nothing in the gate can catch. Its method was mechanical - for every
behavioural change, revert just that behaviour in place, run the commands that should notice, and
record which ones did. That table is the round's real evidence and it found one hole.

- [resolved] **The extremal-seat fix was guarded by a validator that nothing guarded.** Reverting
  `preflop_chart.py:207` alone is caught, by `validate_residual_seat` and by nothing else: all 954
  tests stay green. But no canary named either line, so `check_gate_bite` proved nothing about
  the pair, and reverting the fix *and* dropping the validator call leaves the entire gate green
  while the report publishes `(seat 0, forced_chips 50)` against the truth
  `(seat 1, forced_chips 100)`, contradicting its own prose four lines above. The phase canaries
  both *sibling* extremal-seat rules; the third one, which is the one that actually reverted
  green at stage 6, got a validator and no canary. Closed with
  `the-residual-refusal-names-the-lowest-chair`, whose `must_fail` list was chosen by experiment
  rather than assumption - `pytest_table_state`, `pytest_strategy_contract` and
  `pytest_full_table_preflop` all stay green under the mutation, so only
  `generate_table_state_report` is listed as noticing the behaviour, with `pytest` named honestly
  as reddening solely through the registry-uniqueness test. Verified biting in both directions.

- [resolved] **The fail-open justification was right in its conclusion and false in its cited
  evidence.** Corrected in this note and in the registry entry, as recorded above. This is the
  finding that most justifies the verification round: a wrong worked example was one commit away
  from being permanent, and it erred toward making the fix look better supported than it was.

- [resolved] **A report sentence overstated what its own zero proves.** "Every corpus all-in is
  for the exact level" rests on `short_all_in_calls == 0`, and the verifier showed that check is
  insensitive to its own comparison: loosening `street_bet < current_bet` to `<=` changes nothing,
  because 0 of 183 recorded corpus call entries come from a seat marked all-in and the corpus
  holds only 10 all-in seat-states out of 18,288. The zero is carried entirely by the flag, not by
  the level. The report now says what the zero actually shows, keeps the regression as a
  converter and replay tripwire, and says plainly that it is not a statement about levels.

- [resolved] **A docstring in `checks.py` was wrong in both halves**, claiming the canary names
  the validator as living in `measures.py` and that the registry entry could not be edited outside
  a contract update. The registry says `checks.py` and the entry was written in this same round.

- **`validate_bound_coverage` is shadowed, and is kept anyway.** `_validate_straddle_census` runs
  first and pins every probe's verdict to its declared truth, so the implication follows from that
  check plus two hardcoded columns of the same static table. Recorded rather than removed, because
  the verifier proved shadowed is not tautological - it fires with the census check disabled - so
  it is the check that survives if the census's declared truths are ever loosened. Its docstring
  now says exactly that, including that it is falsifiable only by a probe-table data edit.

What the verifier confirmed as sound, since a verification that only lists hits is not calibrated.
`git diff HEAD -- tests/` is empty and `verification/freeze.lock` is unchanged, so nothing was
weakened to pass; `mutations.yml` is additions only with no existing `must_fail` list touched; no
skip, xfail or ignore was added. The module split dropped nothing - an AST inventory of the
pre-split file against `measures.py` plus `checks.py` accounts for all 41 top-level names, with
only the deliberately deleted `merged_key` and one rename, and the import graph is acyclic. The
boundary rule rejects nothing legitimate across a battery of awkward-but-legal sequences: an
incomplete raise, an all-in raise for less followed by a legal re-raise, two consecutive all-in
raises for less, a straddle recorded and not recorded as an action, a re-raise over a straddle,
a big-blind option raise, a four-bet war, and a short big blind posting only 60 of a 100 big
blind. That last is the case that should break it and does not, because `replay.py` and
`simulator/table.py` both set the preflop level from the *configured* blind, so the engine's level
and the contract's walk cannot diverge downward. And the report's new published claims reproduce:
the four-row blind-structure table was rebuilt from the package independently of the report's own
helper and matches to the digit.

## What the reviewers did not find

Recorded because a review that only lists hits is not calibrated. The mechanical lens found no
case where committed code produces a wrong answer on an input the engine or the replay can
produce, and said so plainly: every finding above is reachable only from a hand-computing
producer, from a table the committed corpus cannot contain, or from a claim on a page. The poker
lens found no refusal that is wrong poker in the *short*-stack direction, which is the direction
decision 6 was created for.
