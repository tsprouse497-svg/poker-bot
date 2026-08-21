# Stage 6 review: the build

Independent read-only review, 2026-08-21. Question asked: does the implementation do the work,
or only enough to satisfy the frozen tests, and what passes for a reason the contract did not
intend.

**This note carries two independent read-only reviews of the same diff.** Everything below is the
mechanical reviewer's unless it is marked `(poker reviewer)`, which is the second reviewer,
briefed to judge the poker rather than the code's fidelity to the contract; the closing section
`What the poker reviewer confirmed` is entirely its work, as are its items under each of the three
headings. Neither reviewer re-verified the other's findings and neither softened them, so a
disagreement between two items would be a real disagreement rather than an editing artefact.
It also covers two passes: the first over the build as committed, the second over the fixes a
worker landed in answer to it. Blocker verdicts are the second pass's; the section
`Second pass: verifying the fixes` carries what was checked and how, including the two judgment
calls the coordinator asked for.

What I read: the whole 18-path diff against `108406b3`, in full for
`scripts/generate_table_state_report.py`, `src/poker_training_bot/table_state/measures.py` and
`src/poker_training_bot/table_state/forced_money.py`, plus `strategy/contract.py` and
`strategy/preflop_chart.py` end to end; the phase 13 contract, the sixteen decisions, the
ExecPlan's coordinator rulings and stage 4 specification, `verification/mutations.yml`, the four
earlier review notes, the committed `latest_table_state_report.txt`, and the frozen tests in
`tests/test_table_state.py` and `tests/test_table_state_strategy.py`.

What I ran: `pytest` (954 pass), `pytest_table_state` (66 pass), `generate_table_state_report`
(exit 0, byte-identical output on a second run), every `generate_*` command the derived gate
holds, `check_scope`, `check_file_sizes`, `check_contracts`, `check_repo_consistency`,
`check_execplan_delegation`, `run_full_quality_gate.py` and `ruff check .` - all green. I applied
all five phase 13 canaries and the re-pointed phase 11 canary by hand and ran every command each
one names in `must_fail`; all six bite, results below. I hand-checked the report's recomputable
pot against `data/samples/normalized_hands.json`, checked 499/3048 against the committed
`latest_sample_comparison_report.txt` and `latest_spot_vocabulary_report.txt`, and wrote my own
adversarial queries against the built strategy.

What I could not check. I did not run `scripts/run_verify.py` or `scripts/check_gate_bite.py`,
because both mutate the tree; the gate as a whole is therefore unproven by me, though I ran every
command in it individually except the two pytest aggregations I substituted with `pytest`. I did
not verify the 499 and 3,048 by an independent replay of my own - I compared them against two
committed reports this phase does not touch. I did not read the frozen-test migrations across the
five completed phases line by line; the stage 4 review did that and I only checked that the two
test names the Phase 11 packet now cites exist. I did not review the audit packet, which does not
exist yet, so every criterion whose evidence is "the packet says" is unchecked. I did not attempt
to price out `decide_spot` or the simulator paths, and I did not measure performance.

Three things I checked that are stronger than they look, recorded because a review that only
lists faults misreads the phase. The replacement for the deleted pot bound covers it in general,
not only at the two worked examples the frozen test proves: `predicted_contributions` gives each
voluntary seat at most the level and folds a blind seat's post into that same figure, so
`sum(predicted) <= small + big + voluntary * level`, and since the pot must now equal
`sum(held)`, any pot over the old bound necessarily leaves some seat holding more than
reconstruction predicts and refuses. `deleted_bound` and `bound_verdict` in the report are a
faithful reproduction of the code that was removed, both branches. And both canaries that name
`generate_table_state_report` in `must_fail` make it exit 1 with a real diagnostic, not a
coincidence: the depth canary trips `_validate_depth_probes` on the worked example, the straddle
canary trips `_validate_straddle_census` on the absorbed straddle.

## Blocker

- **[resolved] A straddled pot with two or more recorded raises is invisible to all three
  signals, and the residual the phase states does not include it.** Resolved by stating the truth,
  not by a guard - the distinction a later reader needs, and the one that cannot live inside the
  bracket. The code still answers such a table; what changed is that the phase stops claiming
  otherwise, says so in three places, demonstrates it on a table an ordinary betting round
  produces, refuses to publish if the demonstration stops holding, and files it.
  `predicted_min_raise_target`
  (`src/poker_training_bot/table_state/forced_money.py:100-109`) walks the recorded raises and
  uses `big_blind` only as the level standing before the *first* one. With two or more raises the
  final increment is the difference of two recorded raise-to amounts, so the prediction stops
  depending on the declared blind entirely and is identical for a straddled and an unstraddled
  reading of the same table. Signal 3 can therefore only ever fire on a pot holding exactly one
  recorded raise. Signal 1 cannot apply once anything has raised. Signal 2 is absorbed the moment
  the straddler calls or raises to the level, which is the case decision 8 exists for. So the
  three signals together miss every straddled pot with a second raise whose straddler has acted.
  Worked example, all committed code and no mutation. 50/100 declared, the big blind straddles to
  200, the cutoff raises to 500, everyone folds round to the big blind, the big blind three-bets
  to 2,700, the cutoff is deciding. Contributions are 50/500/2,700, which is exactly what 50/100
  blinds and those two recorded raises predict, so `unexplained_contributions` returns `{}`. The
  table offers a minimum re-raise to 4,900 and the prediction is 4,900. `chart_lookup` returns a
  `ChartHit` on `t6/d100/CO/CO:raise@2.5,BB:raise@13.5`, reached by substituting the prices down
  from 5.0bb and 27.0bb, and `weights_for` returns `(('call', 0.0029), ('raise', 0.9971))` - the
  unstraddled chart's range, handed to a straddled table. `decide` does refuse, but at
  `preflop-chart:committed-size-below-minimum-raise`, because the charted 28.5bb size happens to
  sit under the straddled table's own minimum; nothing recognised the straddle. `weights_for` is
  the path the corpus comparison reads and the one phase 14 will publish through, and it answers.
  A second shape, an ordinary UTG straddle: 50/100, the lojack straddles 200, the hijack raises to
  400, the cutoff three-bets to 800, the blinds and button fold, the straddler calls 800, the
  hijack is deciding. Again nothing unexplained and the two minimums agree at 1,200; this one is
  refused, but with `preflop-chart:lookup:unrepresentable-spot`, whose detail reads "no legal
  preflop order produces it" about a table a legal preflop street produces every night.
  Why this is a blocker rather than a limitation. The contract's straddle criterion requires the
  phase to state "the residual, if any, that all three signals together still miss", and the
  residual stated in the contract, in `_forced_money_refusal`'s docstring, in `forced_money.py`'s
  module docstring and in the report's "What this still misses" section is only two cases: a
  straddle equal to the big blind, and a straddler who has acted in a pot where nothing has
  raised. A non-coding reviewer reading the committed report concludes the blind spot is one
  degenerate case. It is instead every raised, straddled pot past the first raise - which is most
  of them, because a straddle makes the first raise large and a three-bet normal. The phase's own
  headline sentence, "a table this bot's charts cannot describe is now seen and refused for what
  it is, rather than answered as something else", is false for this population.
  Every fixture, probe and test the phase uses for signal 3 has exactly one recorded raise:
  `absorbed_straddle_table`, `raised_straddle`, `test_a_straddler_who_has_called_to_the_level_is_
  caught_by_the_minimum_raise_target`, and `test_every_pot_the_deleted_arithmetic_bound_refused_
  still_refuses`. That is the shape of the answer to the driver's question: the signal was built
  and demonstrated on exactly the population in which it can fire, and nothing in the phase says
  that population is single-raise pots.
  Inside stage 6's reach: say it in the report's limitations section and in the two docstrings,
  and file it. The detection itself is decision 8's ruled shape and is not stage 6's to redesign.
  **Resolved on the second pass, in the only way available.** No guard was attempted, by the
  coordinator's ruling, and I agree with it: once the straddler raises, its chips are explained by
  its own recorded amount and the prediction stops depending on the declared blind, so the trace is
  destroyed rather than hidden, and nothing short of a declared blind structure recovers it. What
  changed is that the phase stops claiming otherwise. `forced_money.py`'s module docstring and
  `_forced_money_refusal` now state it, the report's limitations section leads with it, and the
  report's own headline sentence now names its exception in the same paragraph that makes the
  claim. I re-derived the residual myself on post-fix code and the prose is true rather than
  approximately true: the signal fires only on single-raise pots, and such a table is answered
  rather than mis-coded. Filed as `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`. Two things about the
  demonstration it publishes are new findings, under Non-blocker below.

- **[resolved] (poker reviewer) The depth refusal names the first offending seat in seat order
  rather than
  the one that decides the hand.** `_table_depth_bb` walks `seat_states` ascending and keeps the
  first live seat on each side of hero, so hero at 100bb with a live 90bb in seat 1 and a live
  20bb in seat 3 refuses with `seat=1, stack_depth_bb=90`; swap those two stacks and the same
  physical table refuses with `seat=1, stack_depth_bb=20`. One table, two reported depths,
  decided by seat numbering. In poker the number that matters is the shortest live opponent,
  because that is what caps hero's effective stack and it is the one that makes a 100bb chart the
  wrong chart. The detail exists so that whoever re-rules decision 6 has data; somebody reading an
  inventory of these rows would conclude a 10bb tolerance covered tables that in fact held 20bb
  stacks. **Resolved and verified against the artifact.** The shallower branch now takes the
  minimum starting stack among live seats and the deeper branch the maximum, ties to the lowest
  seat. I ran the reviewer's own swap: 90bb in seat 1 with 20bb in seat 3 reports
  `seat 3, starting_chips 2000, stack_depth_bb 20`, and swapped it reports
  `seat 1, starting_chips 2000, stack_depth_bb 20` - same depth from either seating, and it is the
  20bb one. Ties resolve to the lowest seat in both directions (two 200bb seats report seat 2; two
  50bb seats report seat 1). Decision 7's precedence survives: a table with a deeper and a shorter
  live seat still takes `table-is-not-one-flat-stack-depth`, and folded offenders are still
  ignored. `measures.independent_depth_verdict` agrees with the strategy on all eight tables I
  tried. The stated reason for changing the oracle too is not only sound, it was already forced: a
  committed probe has two same-direction offenders, so leaving the oracle on seat order would have
  made `_validate_depth_probes` fail the report command rather than "the first time a probe had
  two".

- **[resolved] (poker reviewer) `REFUSE_RAGGED_DEPTH` carries no detail at all.** The two villain
  codes were given `seat` and `stack_depth_bb` in this phase on the stated argument that the
  re-ruling needs the numbers, and decision 7 puts the ragged check first, so this is the code that
  swallows the majority of live spots and it is the one that records nothing. **Resolved and
  verified.** All three depth codes now run through `_depth_refusal` and carry `seat`,
  `starting_chips` and `stack_depth_bb`; the ragged branch passes hero's own seat. A 10,050-chip
  hero at 50/100 reports `stack_depth_bb 100.5` and a 10,033-chip hero reports `100.33`, so the
  figure is rendered exactly rather than rounded into the whole number the refusal exists to deny.
  I checked what the coordinator asked about: no frozen test asserts that refusal's detail is
  empty (`tests/test_strategy_contract.py:450` builds its own bare `StrategyRefusal`), no test
  reads detail by index anywhere in `tests/`, and
  `test_detail_is_readable_by_name_rather_than_by_position` requires the opposite. 954 tests pass.

## Non-blocker

- **[fixed]** `measures.hero_start`'s docstring said "`to_call` is read nowhere in this module".
  It is read
  twice, in `priced_at_heros_whole_stack` eight lines below, at
  `src/poker_training_bot/table_state/measures.py:106`. The intended claim - no contribution is
  derived from the price - is true and worth keeping; as written it is a docstring stronger than
  the file, in the phase whose thesis is that those are how the next reader stops looking.
- **[fixed in both docstrings; the contract line still stands]** "the gap is exactly the straddle"
  is wrong by one big blind, in
  `forced_money.predicted_min_raise_target`'s docstring and in
  `preflop_chart._forced_money_refusal`'s. Over a 200 straddle the offered minimum is 1,000 and
  the prediction 1,100, so the gap is 100. The algebra is `gap = straddle - big_blind`, which the
  committed report states correctly ("the straddle less the big blind"). The error is inherited
  verbatim from contract line 160, so the `contract-update` task that already owes this contract a
  reword should take both docstrings with it.
- **[fixed]** `generate_engine_fidelity_report._seats` built villain's `committed_total` as
  `_POT - hero_street_bet`. That is a contribution reconstructed from an independently stated pot,
  which is the direction the forbidden-shortcut list names ("the pot as an independently supplied
  number that the contributions merely agree with"). It is a literal fixture and nothing in that
  report reads the pot, so no figure moves - but the producer sweep the audit packet owes must
  record that verdict rather than claiming all sites carry what the engine or the replay recorded.
- After this phase the pot reconciliation is a tautology at all ten construction sites, not the
  two live ones the contract names. The two report producers that supplied an independent pot were
  changed to supply the sum instead (`generate_strategy_query_report.build_query`, the
  sample-replay site in `generate_postflop_fallback_report.build_query`), and I verified
  `point.pot` already equalled `sum(committed_total)` on every committed record in both audits, so
  nothing moved and no figure is wrong. Only the frozen tests can make the rule fail. That is what
  the contract's own wording permits; the packet should not claim the check bites at a producer.
- **[resolved by the coordinator]** Running the gate's own generators dirtied two files the
  stage-6 tree did not carry:
  `STATUS.md`, which still reads `Current task: PHASE_13_CONTRACT` / `Task mode:
  contract-update`, and `docs/BACKLOG.md`, which is missing the three entries this stage added.
  Both are standing scope so `check_scope` passes, and nothing in the gate *fails* on the
  staleness - the generators simply rewrite it - so stage 7 has to commit them.
- **[fixed]** The census row `straddled, and invisible to all three signals   counted  0` was a
  literal in
  `census_lines`, not a measurement. `forced_money_verdict` can only ever return one of the four
  named classes, so the row is true by construction rather than by observation. The paragraph
  under the table hardcodes "four pots ... only three hold none" beside a measured table, so a
  future probe would leave the prose wrong and the table right.
- **[fixed]** `_validate_straddle_census` asserted nothing at all about a probe whose `truth` is
  `INVISIBLE`:
  the truth-versus-verdict rules cover only `STRADDLED`, `ANTED`, `RESIDUAL` and `CLEAN`. If the
  big-blind-sized straddle started being reported as anted, the census would still reconcile and
  the report would still publish.
- `_table_depth_bb` uses two formulas for one quantity: hero's starting stack is
  `stack + street_bet`, every other seat's is `stack + committed_total`. Preflop with an ante the
  two disagree and hero reads as the ante shorter than everyone else; the only thing keeping that
  unreachable is that the forced-money check refuses an ante first. The contract's criterion is
  written as one rule, "what it holds plus what it has put in". `measures.hero_start` and
  `measures.seat_start` mirror the split, so the report's "sat down with" column and its "hero sat
  down with" sentence are two different derivations of hero's own row. Stage 4 froze the hero
  formula in a canary `find` string, so this was not the builder's choice to make.
- `SeatState.all_in` is validated against nothing and read by no decision path. The engine sets
  `all_in` exactly when a stack reaches zero, so `all_in=True` beside a positive stack cannot
  happen in the engine and constructs fine here; decision 14 rejected *deriving* the marker from a
  zero stack, which is a different thing from checking that the two agree. The phase 12 handoff
  the marker was added for is answered by the depth check instead (report lines 481-486), so the
  field currently earns its keep only in the report's status column and its short-all-in census.
- **[fixed]** `spot_key.py`'s new docstring said the three unchecked things "wait on
  `ASYMMETRIC-EFFECTIVE-STACKS`" - the phase 13 entry this phase closes. The quality gate's
  backlog-integrity check reads ids cited in `docs/` and `reports/`, not `src/`, so nothing will
  notice when that sentence starts pointing at a `done` item. What those three actually wait on is
  a spot-key format change, nearer `RAISE-SIZE-IN-SPOT-KEY`.
- **[fixed, and it was live rather than latent]** `generate_strategy_query_report.build_query`
  passed no `preflop_actions`, so every query
  it builds carries an empty history. Harmless today because that report drives
  `CheckFoldStrategy` - but under the new rules an empty history in a raised pot makes
  `_forced_money_refusal` take the unraised-level branch and report `pot-holds-a-straddle`. It is
  a trap set for the next producer, and the query validates such a state without complaint.
- **[fixed by labelling]** The report's "a hero who bought in short" probe is a table where hero
  has raised to 250 and is
  then asked to act again with `to_call` 0 and `check` legal, which no street produces. The claim
  it carries is right and is pinned elsewhere by
  `test_a_hero_who_bought_in_short_refuses_because_a_live_seat_is_then_deeper`; the table it is
  carried on is not one poker produces, and the stage 4 reviewer asked for exactly this sentence
  on a sibling fixture.
- **(poker reviewer) A short all-in in front of hero makes the bot announce a straddle**, because
  the minimum-raise walk has no floor. 50/100, the lojack opens to 250, a 300-chip stack shoves to
  300; the engine correctly offers a minimum re-raise of 450, the walk predicts 350, and the
  strategy answers `preflop-chart:pot-holds-a-straddle` on a pot with nothing forced in it.
  Measured unreachable on committed data: 0 of 515 preflop raises across the 499 corpus hands has
  an increment below the running minimum raise. Being **fixed rather than deferred**, because the
  builder's stated reason for leaving it visible - that a floor would also hide a real straddle -
  is wrong: a straddle perturbs only the first increment, and the first increment is always a full
  raise.
- **(poker reviewer) A big-blind ante, the standard modern tournament structure, is classified as
  `blind-structure-not-representable` rather than as an ante**, because the ante rule requires
  every seat to be holding its own unexplained chips. Explicitly **not fixable in this phase**: a
  single-seat ante and a folded seat's dead blind are indistinguishable without the declared blind
  structure decision 8 declined to add, and a frozen test pins the latter to the residual code.
  Worth stating in the report rather than fixing.
- **(poker reviewer) Decision 7's deeper-before-shallower order is a compatibility choice standing
  in front of a poker one.** Measured over 4,000 plausible live $1/$2 tables,
  `table-is-not-one-flat-stack-depth` fires on 40.3% and `a-live-seat-is-shorter-than-hero` on
  8.8%, so the code decision 6 exists to create fires only when hero happens to be the deepest
  player, and the shortest-opponent depth that a future tolerance would be set against is recorded
  in fewer than one spot in eleven.
- **(poker reviewer) A dead big blind cannot be expressed at all.** `StrategyQuery.blinds` is a
  two-tuple of live blinds with no way to say one of them is dead, so the reviewer could not
  construct the case; a gap in what the query can say rather than in what it validates.

Found on the second pass, verifying the fixes:

- **[fixed in the published report; the ExecPlan still carries nothing]** The build report named
  the wrong moved figure. It says the one printed figure that
  moved is the side-pot hand "from the button's chair", now `seat 0, starting_chips 50,
  stack_depth_bb 5`. That row already said `seat 0, stack_depth_bb 5` before the fix; all it
  gained is `starting_chips`. The figure that actually moved is the other side-pot row, seat 0's
  own chair, from `table-is-not-one-flat-stack-depth (seat 1, stack_depth_bb 10)` to
  `(seat 2, starting_chips 200, stack_depth_bb 20)` - the deeper branch switching from the first
  offender in seat order to the deepest. The new value is right and is the whole point of the fix,
  so this is a reporting error rather than a code one, but the audit packet must not inherit it:
  the one behavioural move in the committed report is the 10bb-to-20bb switch, and every other
  change is an added `starting_chips`.
- **[fixed]** The report's headline exception was demonstrated on a table no betting round
  produces.
  The limitations section builds it as "a 200 straddle posted by the lojack, the lojack opening to
  400, the cutoff three-betting to 700". A lojack that posts a straddle acts *last* in the first
  orbit, so it cannot be the first raiser: everyone from the hijack round to the big blind would
  have to have folded, and then there is no decision for the lojack to make. The prices and the
  contributions in that table are all legal and the hit is real - I reproduced it, and it is
  stronger than my own example, because `decide` returns an actual `StrategyDecision(raise to
  2150)` rather than refusing late - but the table is unreachable, and the same fix labelled the
  short-buy-in probe for exactly this. A reachable table exists and I verified it hits: a
  *big-blind* straddle to 200, the cutoff opening to 500, folds round, the big blind three-betting
  to 2,700, the cutoff deciding. The big blind acts last anyway, so the order is ordinary; the key
  `t6/d100/CO/CO:raise@2.5,BB:raise@13.5` is accepted, and `weights_for` returns the unstraddled
  range. The phase's single most important admission should rest on that one, or on both.
- **[closed by the report's own validator and a canary, not by the tests]** Nothing in `tests/**`
  pins the new seat-selection rule. No frozen test has two
  offenders in one direction - `test_each_depth_refusal_names_the_seat_and_the_depth_it_holds`
  uses one short seat and one deep seat - so reverting both copies to first-in-seat-order would
  leave 954 tests green and no canary covers it. `_validate_depth_probes` pins only that the two
  copies *agree*, which a symmetric revert satisfies. `tests/**` is frozen and out of scope, so
  this is a fact to record rather than a fix to ask for.
- **[fixed]** `independent_depth_verdict`'s "an oracle rather than a second implementation" was
  false in the letter as well as the spirit. After the fix it is verbatim the strategy's own
  three lines - the same `max` with the same key, the same `min`, the same two comparisons. It
  still catches the depth canary, because the canary mutates only `preflop_chart`, but a reader
  told there is an oracle here will not go looking for the reason the two agree.
- **[fixed]** The report had lost its only worked demonstration of decision 15's false-positive
  channel. Decision 15 accepts, in as many words, that "a report producer that computes
  `min_raise_target` carelessly makes the strategy claim a straddle", and the under-raise row was
  the one place a reader could see that happen. With the walk floored and the fixture corrected,
  that row is a coverage miss and the cost decision 15 signed for is now asserted by nothing. The
  channel is still open - `min_raise_target` is still producer-supplied and still unvalidated by
  anything but positivity.
- **[fixed]** A gate-failure diagnostic was truncated into a broken sentence paying for the line
  cap: `_validate_straddle_census` raised "...so the pot the deleted bound let through is again".
  It is the message a human reads at the moment the report refuses to publish.

Found on the third pass, verifying round two of the fixes:

- **[new] The new canary's description credits the wrong check with killing it.** It says the
  report "recomputes the offending seats from the seat states rather than asking either copy of the
  rule, and exits non-zero when the seat the strategy named is not the extreme one". That is rule
  four, and rule four is not what fires: the mutation touches `preflop_chart` only, so the two
  copies of the selection rule disagree and rule *one* raises first. I applied the canary and read
  the diagnostic - it is "phase02-three-way-side-pot, seat 0 to act: hero started with 50 chips by
  its own seat record, so this table is ... and the strategy acted on ...", which is the
  copies-disagree message. Rule four is the one that catches a *symmetric* revert of both copies,
  which is the case the coordinator tested by hand and which no canary covers. Both cases are
  genuinely covered, by different checks; the description swaps them. Nothing is overstated about
  what fails, only about why.
- **[new] Only the deeper branch has a canary; the shorter branch has the validator alone.** The
  mutation rewrites `deep = max(...)` and leaves `short = min(live)` untouched, and its description
  says so plainly. A shorter-branch revert would still be caught - rule four covers both
  directions, and the 90bb/20bb probe is the row that makes it bite - but nothing in
  `verification/mutations.yml` proves that, so the two directions are not equally attested.
- **[new] "It is the only committed row where the two rules differ" is loose.** In the
  moving-fixture section that sentence is about the side-pot fixture and is true of it; the
  constructed 90bb/20bb row is also a committed row where the two rules differ, and the depth
  section says so correctly two pages earlier ("The 90bb-and-20bb row above supplies the shorter
  direction; `phase02-three-way-side-pot`, further down, supplies the deeper one"). Read literally
  the later sentence contradicts the earlier one and suggests the shorter direction is unpinned,
  which is the opposite of what round two added.
- **[new] The line cap has changed hands rather than eased.** `measures.py` is now at 500 of 500
  and `preflop_chart.py` at 499, where before the move it was 499 and 500. Moving
  `moving_fixture_probes` out bought a module 26 lines and the new fourth rule spent 27, so the
  file the relocation was meant to relieve is the one now at the cap.
  `TABLE-STATE-REPORT-RENDERER-HAS-NO-SIZE-CAP` already covers the shape of this; the specific
  fact worth recording is that two consecutive fixes have both ended with one of the two modules
  unable to take another line.

## Alignment

- `STRADDLE-SIGNAL-MISREADS-A-SHORT-ALL-IN-RAISE`, **closed `done` against phase 13 by the
  coordinator rather than left deferred, and that is the right call.** The entry's filed reasoning
  was that a floor could not be added because it would hide a real straddle; the poker reviewer
  overturned exactly that, and I verified the overturning independently. A straddle perturbs only
  the first increment, and the first raise over a straddle of `S` is at least `2S`, so its
  increment measured from the declared big blind is `2S - BB > BB` and is never below the floor the
  walk starts at. Every straddle the unfloored rule caught, the floored one still catches: I
  re-derived the 200-straddle detection (offered 1,000 against a predicted 1,100) and the
  unstraddled control at the same price (1,100 against 1,100), and the short all-in now predicts
  the 450 the engine offers instead of 350. Closing it `done` beside evidence is better than the
  alternative this repo has twice shipped, which is a phase tagging with its own item deferred
  (`BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE`).
- `MIN-RAISE-OVER-AN-INCOMPLETE-ALL-IN-BET`. Same root: this repo has no oracle for the minimum
  raise over an incomplete bet, and phase 13 has now built a poker claim on top of that gap.
- `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE`. Confirmed from the other side: every straddle, ante and
  asymmetry figure in the committed report is a construction, the corpus contributes only zeros
  and two live denominators, and the report says so in three places. Nothing to add beyond the
  sentence the stage 4 review already proposed. The poker reviewer's entry against the same id
  below is the harder measurement and should be the one the coordinator files against.
- `TABLE-STATE-REPORT-RENDERER-HAS-NO-SIZE-CAP`. Confirmed as filed: 1,135 lines in
  `scripts/generate_table_state_report.py`, `measures.py` at 499 of 500, and the cap chose which
  file would be large rather than preventing it.
- `MUTATION-DRILL-CHECKOUT-DESTROYS-UNCOMMITTED-WORK`. Hit it myself; every restore below came
  from a checksummed scratch copy, never from `git checkout --`.
- `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`, filed by the coordinator for the first blocker above,
  because the coordinator can state and file it but cannot redesign decision 8's ruled shape. It
  should say that the minimum-raise signal is structurally blind past the first raise, name the two
  worked tables, record that `weights_for` returns unstraddled ranges on one of them, and say the
  fix is a declared blind structure on the query - decision 8's rejected option, which has no
  producer today and is a format change.
- `SEAT-STATE-MARKERS-AGREE-WITH-NOTHING`, filed by the coordinator. Two facts under one roof:
  `all_in` may contradict the seat's own stack, and `to_call` may contradict `current_bet` and
  hero's own `street_bet` - the second was recorded as a stage 4 non-blocker and still had no id.
  Both are the producer-error class decision 3 closes for the pot, left open for the fields the
  depth and forced-money derivations now read.
- `SPOT-KEY-LEGAL-ORDER-OVERCLAIM-IN-PHASE-12-CONTRACT`, filed by the coordinator. **This was
  blocker 2 of this note's first draft and is no longer a blocker**, because the contract's own
  criterion offers filing by id as the alternative to amending Phase 12, and filing it satisfies
  the criterion as written. The facts unchanged: the `spot_key` docstring correction landed and now
  says in as many words that the checks never ask whether a price is legal, while
  `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md:105` still asserts "What bounds the vocabulary
  is whether the sequence is a legal preflop order". Phase 12's contract is not in this task's
  `approved_scope` and contract edits are forbidden in implementation mode, so filing was the only
  route available to stage 6 in the first place.
- **(poker reviewer)** `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE`. Measured over 4,000 plausible live
  $1/$2 tables the bot answers **zero** spots, and that is not decision 6 alone: even a flat live
  table needs hero at exactly 100bb, because `d100` is the only committed chart. Worse, the refusal
  a spot now gets is less informative than the one it used to get - a flat 93bb table returned
  `lookup:no-artifact-for-stack-depth (stack_depth_bb 93)`, a work-list row naming a chart somebody
  could go and solve, where a ragged table returns a code naming no depth at all. So a spot the
  chart could never have answered is now refused earlier and with less information than before.
  Separately, and the reviewer's own judgment: refusing a hero at 93.5bb at an otherwise flat table
  teaches a trainee nothing, so the check that costs the most training value is the one with the
  least poker content behind it.

## The mutation drill

Applied by hand, one at a time, with a checksummed scratch copy of the target file taken first
and restored from in a `finally` block. `find` string occurrence counted in the target file
before each application: exactly 1 in every case. Bytecode purged after write and after restore.
Aggregate `pytest` runs used `-q -x`, so the exit code is the whole claim and the named test is
the first failure rather than the only one.

| canary | command | exit | first failure |
|---|---|---|---|
| `the-pot-stops-having-to-reconcile` | `pytest_table_state` | 1 | `test_dropping_a_folded_seat_is_how_a_pot_stops_reconciling` |
| | `pytest` | 1 | `test_every_mutation_applies_exactly_once_to_its_file` |
| `a-capped-hero-may-raise-again` | `pytest_table_state` | 1 | `test_a_hero_all_in_for_the_call_cannot_be_offered_a_raise` |
| | `pytest` | 1 | `test_every_mutation_applies_exactly_once_to_its_file` |
| `hero-depth-is-derived-by-subtraction-again` | `pytest_table_state` | 1 | `test_the_chart_refuses_the_depth_hero_actually_has_rather_than_the_subtracted_one` |
| | `generate_table_state_report` | 1 | "the worked example: a capped hero at 5/10: hero's own seat record says it started with 250 chips..." |
| | `pytest` | 1 | `test_every_mutation_applies_exactly_once_to_its_file` |
| `a-folded-seat-makes-the-table-ragged` | `pytest_table_state` | 1 | `test_a_folded_seat_shallower_than_hero_does_not_make_the_table_ragged` |
| | `pytest` | 1 | `test_every_mutation_applies_exactly_once_to_its_file` |
| `an-absorbed-straddle-goes-unseen` | `pytest_table_state` | 1 | `test_a_straddler_who_has_called_to_the_level_is_caught_by_the_minimum_raise_target` |
| | `generate_table_state_report` | 1 | "a 200 straddle already called to the level: the table offers a minimum raise of 1000 where the blinds and the recorded raises predict 1100..." |
| | `pytest` | 1 | `test_a_straddled_pot_refuses_after_someone_raises` |
| `all-in-ceiling-loose-by-the-price-to-call-again` | `pytest_engine_fidelity` | 1 | `test_a_raise_above_the_corrected_ceiling_is_rejected` |
| | `pytest` | 1 | `test_a_raise_above_the_corrected_ceiling_is_rejected` |

All six bite. Worth noticing for the packet rather than for this stage: `must_fail: pytest` is
satisfied for four of the six by `test_every_mutation_applies_exactly_once_to_its_file` alone,
which fails because the mutation changed the file rather than because any behaviour broke. The
phase-specific command is the one carrying the proof in every case, and it does.

Tree restored. Every one of the 26 dirty or new files matches its pre-review checksum; the two
generated docs my regeneration sweep dirtied (`STATUS.md`, `docs/BACKLOG.md`) were clean against
HEAD beforehand and were restored with `git checkout --`, which is safe only because they were
unmodified. `git status --short` is the 21 modified plus 3 untracked paths it was when I started,
and `check_scope` is green.

## The report's numbers, checked

- The hand-recomputable pot. `data/samples/normalized_hands.json`, `phase02-three-way-side-pot`,
  preflop actions in order: post 5, post 10, raise 200, call 45, call 90. The actions before seat
  1's own call are 5, 10, 200, 45, summing to 260, which is the pot the report prints and the
  recipe it prints. Correct, and `recomputed_pot` executes the recipe rather than describing it.
- 499 hands and 3,048 preflop decision points match `latest_sample_comparison_report.txt` and
  `latest_spot_vocabulary_report.txt`, neither of which this diff touches; `_validate_corpus`
  fails the command on either moving. `latest_sample_comparison_report.txt` regenerates
  byte-identical, so the agreement rates did not move either.
- 290 refusals reconciles internally against the by-code table (7 + 283) and the six table-shape
  codes are all zero, which is what the corpus can produce.
- 10 of 3,048 decisions priced at hero's whole stack, 0 of them diverging. I confirmed the reason
  the report gives is the real one: every corpus seat starts at exactly 100bb, so a shove is never
  for more than hero started with and the two readings of hero's depth cannot come apart.
- The 18 `to_call` values that moved in `latest_postflop_decision_audit.jsonl` are the cap
  landing, and no pot moved in either committed audit.

## Second pass: verifying the fixes

A fix worker landed after the first draft of this note and left the tree. I verified its work
against the artifact rather than against its report, by diffing every file it touched against my
own pre-fix checksummed copy and then re-deriving each claim. What I ran: the full 954-test suite
(green), `ruff check .` (clean), `check_file_sizes`, `check_scope`, all five report generators
(every committed report regenerates byte-identical, so the committed state is the generated
state), and the three `preflop_chart` canaries applied by hand again, since that file was
rewritten. I did not run `run_verify.py` or `check_gate_bite.py`. I did not verify the worker's
claim that 200 such straddled tables exist in the range it swept; it is a sweep-dependent number,
it is not printed in any committed report, and nothing rests on it.

| claim | verdict |
|---|---|
| the two-raise residual is now stated in three places, and truly | **holds.** Re-derived: the signal fires only on single-raise pots, and such a table is answered rather than mis-coded. The report's headline paragraph now names its own exception. |
| the shallower branch names the shortest live seat, the deeper the deepest, ties to the lowest seat | **holds.** Verified on eight tables including the reviewer's 90/20 swap and ties in both directions. |
| the strategy and `measures.independent_depth_verdict` now agree | **holds**, on every table I tried, and the change to the oracle was not optional: a committed probe already has two same-direction offenders. |
| all three depth codes carry `seat`, `starting_chips`, `stack_depth_bb`, ragged included, rendered exactly | **holds.** `100.5` and `100.33` both print exactly. No frozen test asserted an empty detail and none reads detail positionally. |
| one printed figure moved, for the better | **half true.** A figure did move and it is better; the report names the wrong row. See the new non-blocker. |
| `_seats` no longer subtracts, `pot_of` sums, and the regenerated report is byte-identical | **holds.** The internal pot moved 60 to 80 in one section and the report text is unchanged, which also proves that figure was never printed. The illegal table is gone: both seats now state a preflop 20, where before villain read 40 preflop against hero's 20 with both live. |
| the floored walk reproduces the offered-versus-predicted pairs | **holds** at every pair I re-derived, and I confirmed the floor against `BettingRoundState.apply` and against `replay.py`, which starts `min_raise` at the big blind exactly as the walk does. |
| `generate_strategy_query_report` was reading 2 of 5 preflop decisions as straddled | **holds exactly.** I rebuilt both query sets: 2 straddle refusals with the empty history, 0 with the history. No count in that report moved, its text is byte-identical, and in `latest_decision_audit.jsonl` the only field that changed on any of the 11 records is `preflop_actions`, on 9 of them, with no outcome changed. |
| the three canaries still bite after the rewrite | **holds.** Each `find` string still occurs exactly once in its file; `pytest_table_state` fails on all three and `generate_table_state_report` exits 1 on both that name it, with real diagnostics from the rewritten validators. |

### (a) The fixture change from 400 to 450: the argument holds

Plainly: this is a wrong fixture being corrected, not evidence being fitted to a claim, and I
checked it against the engine rather than against the argument. `BettingRoundState.apply` keeps
`new_min_raise = self.min_raise if raise_size < self.min_raise else raise_size`, so an incomplete
raise does not reset the increment. Walking 50/100 with an open to 250 and a shove to 300: the
open sets `min_raise` to 150, the shove's increment of 50 is below it and leaves it at 150, so
`min_raise_target` is 300 + 150 = 450. The old fixture's 400 is `current_bet + big_blind`, which
is the number the engine holds only while nothing has raised. No state of this engine produces
400 there, so the fixture was stating an impossible table and the report was reading a refusal off
it.

Two things keep me from softening that. The change is load-bearing - with the floored walk and the
old 400 the report would still print a straddle refusal - so it is not cosmetic, and it deserved
exactly this scrutiny. But the direction of the argument is the test, and it runs the right way:
450 is derivable from the engine without reference to the fix, and it would have been the correct
value before the fix existed. Had the worker moved the fixture to some number that merely made the
disagreement vanish, or had it moved `min_raise_target` on a *reachable* fixture whose value the
engine did produce, I would be calling it evidence-fitting. It did neither.

What the change does cost is real and is the new non-blocker above: the report no longer
demonstrates decision 15's false-positive channel anywhere, and decision 15 signed for that cost
explicitly. The channel is still open, and after this fix nothing published shows it.

### (b) The line-cap squeeze: nothing factual left, one diagnostic broke

`preflop_chart.py` is at 500 of 500 and `measures.py` at 499 of 500; `check_file_sizes` passes and
neither can take another line. I read every removed docstring line in both files against what
survives. Nothing factual was removed, and the two the worker flagged are the two worth naming:

- `level_as_depth` lost "for a hero whose whole stack was the price" for "for a capped hero". Same
  fact, one indirection added; "capped" is defined by `priced_at_heros_whole_stack` a few lines up.
- `chart_lookup` delegated its two alternatives to `weights_for`. `weights_for` does carry both,
  but it names the first one differently: it says "parsing the weight vector back out of the
  rationale string", where `chart_lookup` had said "parsing the numbers back out of a decision's
  detail strings". Those are two different strings and two different fields. The cross-reference is
  approximately right rather than exactly right, which is a small thing to have paid for a line.

Two more I found that the worker did not name:

- `_forced_money_refusal`'s old residual paragraph carried two cases. The big-blind-sized straddle
  moved into `forced_money.py` intact. The second - a straddle in a pot where the straddler has
  acted and nothing has raised, impossible in a legal street but expressible as a query - now
  survives only in the report's prose and has left the code entirely.
- `_validate_straddle_census`'s error message was cut to "...so the pot the deleted bound let
  through is again", which is not a sentence. It is the text a human sees when the gate stops.

Neither is worth a line of code on its own; together they are the answer to the question the cap
raises, which is that the squeeze cost precision in the diagnostics and in one cross-reference
rather than facts. The structural point stands and is already filed as
`TABLE-STATE-REPORT-RENDERER-HAS-NO-SIZE-CAP`: the cap did not prevent large files, it chose which
files would be large, and both capped modules are now within one line of refusing the next edit.

Tree left as found. Every file in my post-fix checksum set matches, the five regenerated reports
came out byte-identical, and the three hand-applied mutations were restored from a checksummed
scratch copy with the checksum re-verified each time. The only file that differs from my snapshot
is `docs/exec_plans/active/PHASE_13_TABLE_STATE.md`, which the coordinator edited while I worked.

## Third pass: verifying round two of the fixes

Same method: diff every file the worker touched against my own checksummed copy of the round-one
tree, then re-derive each claim rather than read its report. Ran the full suite (954 green),
`ruff` (clean), `check_file_sizes`, `check_scope`, the report generator (byte-identical on a second
run), and the new canary applied by hand. Did not run `run_verify.py` or `check_gate_bite.py`. Did
not repeat the coordinator's symmetric-revert experiment, which is recorded below on their word.

**G1, the reachable demonstration - holds, in every particular.** The new table is 50/100 with the
big blind straddling to 200, lojack and hijack folding, cutoff opening to 500, button and small
blind folding, big blind three-betting to 1,350, cutoff deciding. The order is legal for the
reason the docstring gives, and it is the right reason: a straddler must act last in the first
orbit, and the big blind already does, so unlike the lojack version nothing acts out of turn. Both
prices are legal at the straddled table's own minimums - over a 200 level the smallest open is
400 and the cutoff makes it 500 (increment 300), then the smallest re-raise is 800 and the big
blind makes it 1,350 (increment 850). The table offers 2,200 and the declared blinds plus those
two recorded raises predict 2,200, so the one live signal agrees exactly; `unexplained_contributions`
returns `{}` because the straddler's 200 is absorbed into the 1,350 it raised to; the level is
unreadable behind two raises. `forced_money_verdict` says "no forced money". The lookup is a
`ChartHit` on `t6/d100/CO/CO:raise@2.5,BB:raise@13.5` with weights `call=0.0029, raise=0.9971` and
exactly one substitution, 5.0 to 2.5 - the 13.5bb three-bet is charted as it stands - and `decide`
returns `StrategyDecision(action='raise', amount=2850)`. Every figure the coordinator relayed
matches what I got.
**The guard is real, not decorative.** I called `limitations_lines` with a strategy whose library
returns a miss and it raised `TableStateReportError`: "the straddled pot this report admits is
answered rather than refused no longer reaches a chart cell". The second half, the census having to
still call the pot clean, is the same shape one line below.

**G2, the canary's honesty - the description is accurate and, if anything, under-claims.** I
applied the mutation and ran `pytest_table_state` as well as the two commands it names: 66 of 66
frozen phase-13 tests **pass** under the mutation, so the description's central claim - that
`pytest` is named but is not what notices this - is true, and I verified it independently rather
than inferring it. `generate_table_state_report` exits 1. What the description leaves out is why
`pytest` goes red at all under the mutation: `test_every_mutation_applies_exactly_once_to_its_file`
fails because the find string is gone, which is a registry fact rather than a behavioural one. A
reader who takes "pytest cannot be what notices this" literally will wonder why it is in
`must_fail`; one sentence naming the registry test would close that. Nothing in the description
overstates what fails. It does misattribute which check kills it, which is the new finding above.

**G3 - the published report says it correctly.** The moving-fixture section now reads "From the
50-chip chair two live seats are deeper, holding 100 and 200, and the seat reported is the 200 -
the deepest - so this row would read 10bb rather than 20bb under a rule that stopped at the first
offender in seat order", and the committed row is
`table-is-not-one-flat-stack-depth (seat 2, starting_chips 200, stack_depth_bb 20)`. The
button's-chair row is `(seat 0, starting_chips 50, stack_depth_bb 5)`, which is the round-one value
plus `starting_chips`, as it should be. One gap: the ExecPlan carries no mention of any of this -
`grep starting_chips` finds nothing in it - so an audit packet written from the plan rather than
from the report could still inherit the original misattribution.

**G4 - holds, and the sweep was real.** I extracted all 27 `TableStateReportError` messages across
both modules and read them: every one is a sentence. The fragment is now "...so the pot the deleted
bound let through goes unseen here too", and the three others it says it found are visible in the
diff - the straddle count, both corpus inequalities, and the missing-stack-depth message all read
as prose now.

**G5 - the humbler claim is also the accurate one.** `chart_lookup` names its own pair of
alternatives again and says explicitly that they are not the pair `weights_for` names, which is
better than either the delegation or the original. The "straddler acted, nothing raised" residual
is back in `forced_money.py` and expanded into the general statement that the level is the only
signal left in that position, which is a better fact than the one I said had been lost.
`independent_depth_verdict` now says it is a second copy, that two copies cannot show the rule is
right, and that the extremal property is asserted separately - and that last clause is accurate
rather than merely humbler: `_validate_depth_probes` gained a fourth rule that recomputes the
extreme offending stack from the seat states, compares it against the seat the strategy actually
named, and additionally refuses to publish unless a row exists **in each direction** where the
extreme seat is not the first one in seat order. That is the check that closes the hole I found in
round one, and it is written so that it cannot pass vacuously - the same pattern as the existing
`diverges` requirement. The 90bb/20bb probe supplies the shorter direction, the side-pot fixture
the deeper one, and I confirmed the strategy names seat 2 at 2,000 chips on the former rather than
seat 1 at 9,000.

**G6 - restored and better than it was.** The two tables differ only in `min_raise_target`, 1,000
against 1,100, and the report prints the strategy's actual answer to each side by side:
`pot-holds-a-straddle` against `lookup:unrepresentable-spot`. It is a stronger demonstration of
decision 15 than the under-raise row was, because it shows the channel in both directions from one
field rather than only the false positive.

**The relocation - behaviour-neutral, and the consistency argument holds.** `moving_fixture_probes`
moved into the script unchanged except for `measures.` prefixes on the three constants: same
fixture, same `_query_for(point, ("Ah", "Kh"))`, same label format, same guard, same order. The
report regenerates byte-identical, and the only figure that moved anywhere in it is the deeper-branch
seat, which is G3 rather than the move. The argument that the script is where probes belong is
right on its own terms - every other probe in the report is built there, and `measures` now measures
and checks without constructing. What it did not buy is headroom; see the new finding above.

Tree left as found. Every file in my round-two checksum set matches, the report regenerated
byte-identical, and the hand-applied canary was restored from a checksummed scratch copy with the
checksum re-verified. `check_scope` green.

## What the poker reviewer confirmed

All of this is the second reviewer's work, recorded as checked rather than assumed because a
review that lists only faults leaves the next reader unable to tell what was tested. I did not
re-verify any of it. Each was settled against constructed tables rather than against the code.

- The ante ruling is right poker. An anted game's price to call and its pot both come out correct
  with the ante in `committed_total` and out of `street_bet`, and the placement is coherent with
  the raise cap rather than merely consistent with the validator.
- The straddle arithmetic matches how a real room computes a minimum re-raise: from the last full
  increment. The 1,000-against-1,100 figure is what a live table would actually offer.
- Signal 1 fires correctly on all three shapes that lift the level without a recorded action: a
  button straddle, a mandatory straddle, and a third blind posted above the big blind.
- The folded-seat exemption is safe, but for a better reason than the decision list gives. A
  folded seat's dead money *does* change hero's pot odds, so "it cannot change a chip of hero's
  decision" is not the reason; what makes the exemption safe is that voluntary dead money reaches
  the spot key as a different cell.
- The raise cap lands on hero's true buy-in in every case probed and is never too low.
- No straddled, anted or asymmetric table reaches a chart answer, **except** through the two-raise
  hole in the first blocker above. That is the independent confirmation that makes the blocker a
  single hole rather than one instance of a general leak.
