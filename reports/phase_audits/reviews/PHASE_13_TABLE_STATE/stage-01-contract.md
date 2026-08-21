# Stage 1 Review - Phase 13 Contract And ExecPlan

Read-only pass over `git diff 41ec07a3bcc918312e4c1600a3b842cf9f944a82 --
docs/exec_plans/active/PHASE_13_TABLE_STATE.md docs/phase_contracts/PHASE_03_STRATEGY_CONTRACT.md
docs/phase_contracts/PHASE_06_POSTFLOP_FALLBACK.md docs/phase_contracts/PHASE_13_TABLE_STATE.md`,
against the question the driver printed: is any acceptance criterion unfalsifiable, a
restatement of the phase title, or satisfiable without doing the work it names?
The ExecPlan is untracked at this commit and was read from the working tree.

This is an independent read-only review by a subagent spawned by the coordinator, under
`AGENTS.md` step 9.
A second independent reviewer ran in parallel on a poker-and-measurement lens rather than on
the driver's question; its three blockers are recorded below under its own heading, in its own
words, and the coordinator resolved all six in the contract.
Each blocker keeps the reviewer's original text and carries a `[resolved]` line naming what
changed, because deleting a caught defect loses the record of catching it.
It is the first stage review in this repo written by someone other than the author of the text
under review; phases 10, 11 and 12 all recorded a no-delegation exception and self-reviewed.
The reviewer did not write the contract, the amendments, or the ExecPlan, and has not edited
them.
Everything below that is a blocker is stated as what must change, because the reviewer cannot
edit the contract.

Reading was against the code rather than against the prose.
Source read: `strategy/contract.py` (`StrategyQuery` fields and `__post_init__`, `to_payload`,
`DecisionAuditRecord`'s `max_target`, `DECISION_AUDIT_SCHEMA_VERSION`),
`strategy/preflop_chart.py` (`_blind_structure_is_representable`, `_table_depth_bb`,
`_raise_amount`, the refusal codes), `poker_core/engine.py` (`PlayerState.street_bet` and
`committed_total`, `BettingRoundState.current_bet`, `legal_actions`, `_commit`),
`simulator/table.py`, `data_pipeline/comparison.py`, `data_pipeline/corpus.py`,
`solver_artifacts/spot_key.py` (`_validate_sizes`, `_validate_stack_depth`, the module
docstring), and all four query-building report generators.
Also read: `AGENTS.md`, `docs/LOOP.md`, the five `phase: "13"` backlog entries,
`reports/phase_audits/PHASE_12_SPOT_VOCABULARY.md`, `docs/V2_ROADMAP.md` section 13,
`verification/loop_policy.yml`, and the phase 12 stage-1 note.

## Blocker

- **[resolved] The straddle mechanism the criteria name cannot detect the straddle the criteria require.**
  Line 123 says forced money "is identified by what a seat has put in without having acted".
  Line 133 then requires "a straddled pot with several callers" to be pinned by test as
  detected, and calls it "the case the bound admits today".
  Those two cannot both hold.
  The bound at `preflop_chart.py:164-172` only admits a straddled pot once somebody raises: with
  no raise, `if not raised and query.street_bet != big_blind` (line 166) refuses immediately,
  because in a straddled limped pot the level is the straddle and not the big blind.
  So the slipping case is necessarily a raised pot, and the worked example is 50/100 with a 200
  straddle, UTG raising to 600, BB and the straddler calling, SB folding: contributions
  50/600/600/600 give a pot of 1850 against a bound of `50 + 100 + 3*600 = 1950`, so it is
  admitted today, exactly as the contract says.
  But in that hand the straddler *has* acted, and its contribution is 600, which is precisely
  the level any other caller reaches.
  Per-seat contributions carry no trace of the straddle at all, whether read as "put in without
  having acted" or reconstructed from the declared blinds plus the recorded history: the
  reconstruction predicts 50/600/600/600 and the actual is 50/600/600/600.
  The quantity that still betrays it is `min_raise_target`, which is 1000 here and would be 1100
  in an unstraddled pot at the same price, and that is not a contribution.
  A stage 4 author will satisfy line 123 with a fixture where the straddler has not yet acted,
  which the existing bound already catches at line 166, freeze it, and the case the phase exists
  to close will still slip.
  The same reading also loses antes whenever every seat has a recorded fold or call, which in a
  completed preflop street is usual; antes survive reconstruction, straddles do not.
  What must change: either state the detection rule as a reconstruction of each seat's expected
  contribution from the declared blinds and the recorded history, and separately name what
  detects a continued straddle (`min_raise_target` disagreeing with the reconstructed level, or
  a declared preflop starting level on the query), or drop line 133 and say plainly that a
  straddle whose poster has already acted is not closable from contributions and is filed
  forward with the format half.
  Silently keeping both is how a wrong test gets frozen at stage 5.
  Resolved by taking the first branch and going further than it.
  The criterion now states the detection rule as a reconstruction from the declared blinds and
  each seat's own recorded actions, says in as many words that reconstruction alone is not
  enough and why, and requires two further signals: an unraised pot whose level is not the big
  blind, and a minimum raise target disagreeing with the one the declared blinds and the
  recorded raise-to amounts predict.
  The reviewer's own worked example is now the fixture the contract pins, with its 1,850 pot
  against the bound's 1,950 and the 1000-against-1100 minimum, so the case that slips through
  today is the case a test has to catch.
  The phase also has to state whatever residual all three signals still miss.

- **[resolved] Two completed contracts are contradicted and neither is amended, and one has no room.**
  Line 150 requires the Phase 03 text to be amended "rather than left describing a field that no
  longer exists", and the diff does amend it.
  But `PHASE_11_ENGINE_FIDELITY.md` names the same field in three acceptance criteria - line 133
  ("`StrategyQuery.street_bet` is documented on the field as the street's current bet level"),
  line 140 ("rejects a query whose `street_bet` is less than its `to_call`") and line 222 ("a
  `street_bet` that is still allowed to equal `to_call`") - and none of them is in scope.
  Worse, Phase 11 line 166 asserts as a criterion that "the preflop chart already caps its raise
  at `street_bet + stack`, which under the corrected reading is its own all-in target".
  That is already false - `preflop_chart._raise_amount` line 252 does cap at `street_bet +
  stack`, and `DecisionAuditRecord` line 387 caps at `(street_bet - to_call) + stack`, so the
  chart's cap is too high by exactly `to_call` - and phase 13's own line 96 is the criterion that
  fixes it.
  `PHASE_12_SPOT_VOCABULARY.md` line 105 carries the same "legal preflop order" overclaim that
  line 180 corrects in the `spot_key` docstring, so correcting only the docstring leaves the
  contract asserting what the check does not do.
  `AGENTS.md` "Contract Amendments" says a completed contract a later phase contradicts is
  amended rather than left asserting the opposite, so as written line 150 is satisfiable in full
  while three completed criteria are left false.
  The hard part: `PHASE_11_ENGINE_FIDELITY.md` is 300 lines against the 300-line cap in
  `scripts/check_file_sizes.py`, so it cannot take a two-line amendment at all, and `AGENTS.md`
  forbids raising the cap and says the answer is a rewrite as its own `contract-update` task.
  What must change: the criteria must name Phase 11 and Phase 12 as owing amendments alongside
  Phase 03, both files must enter `approved_scope` in the ExecPlan, and stage 1 must decide now
  whether the Phase 11 rewrite happens as a separate `contract-update` task before this phase's
  build or whether the amendment is folded into the criteria it corrects.
  Discovering this at stage 6 is the same failure mode the contract's own lines 155-160 are
  written to prevent.
  Resolved by deciding it here rather than deferring it.
  The rename criterion now reads that no completed contract is left naming a field that no
  longer exists, names Phase 11's three criteria and its false all-in-ceiling claim, and
  states that Phase 11 cannot take an amendment at the cap.
  `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` is filed as a `contract-update` task, the
  ExecPlan carries it as slice S1a outside this phase's own task, and the contract forbids
  tagging phase 13 before it has run.
  Phase 12's "legal preflop order" overclaim is folded into the docstring criterion, which now
  requires the phase to amend Phase 12 or file the mismatch by id; Phase 12 has headroom, so
  it needs no separate task.

- **[resolved] "The three uncapped producers" is factually wrong at the branch point.**
  Line 90 says three producers do not cap `to_call` and two do, inherited verbatim from
  `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`.
  Grepping every `StrategyQuery(` construction in `src` and `scripts` gives nine sites in seven
  files.
  Two cap: `generate_strategy_query_report.py:45` and `generate_postflop_fallback_report.py:675`.
  Five do not: `comparison.py:355`, `simulator/table.py:151`,
  `generate_postflop_fallback_report.py:335` (the Phase 06 enumeration, via `Shape.to_call`),
  `generate_preflop_strategy_report.py:93` (`level - committed.get(hero, 0)`), and the three
  literal fixtures in `generate_engine_fidelity_report.py` at lines 98, 189 and 296.
  The contract's own line 83 defines a producer as anything that supplies a query and asks for a
  sweep by file, so the narrow reading that makes three correct is not the one the contract uses.
  This matters beyond bookkeeping, because two of the missed sites are load-bearing.
  `generate_preflop_strategy_report.py:120-121` builds its "uncovered: straddled pot" probe by
  overriding `street_bet` alone and its "uncovered: anted pot" probe by overriding `pot` alone;
  under line 77's pot reconciliation the ante probe becomes unconstructible and under line 130's
  deletion of the bound the straddle probe stops refusing, so both probes must be rebuilt or the
  phase 05 report loses the two refusals it exists to show.
  And `generate_postflop_fallback_report.py:335` is the gated Phase 06 enumeration whose
  `pot = 100 + shape.current_bet + shape.hero_street_bet` attributes 100 chips to no seat, which
  cannot reconcile against per-seat contributions without deciding where that dead money sits.
  What must change: follow the phase 12 precedent and make the criterion the sweep, giving the
  site list above as what is there at the branch point rather than a count, and name the two
  report rebuilds so they are chosen rather than discovered.
  Resolved exactly as asked.
  The `to_call` criterion is now the sweep, records that the backlog entry says three while
  stage 1 measured nine sites across seven files of which two cap, and names both report
  rebuilds and the enumeration's 100 unattributed chips as work chosen here rather than found
  at stage 6.

## Blocker, second reviewer

Three findings from the parallel poker-and-measurement reviewer, in its words, each with what
the coordinator changed.

- **[resolved] Every corpus number the contract promises is provably zero, and the contract
  does not say so.**
  All 499 committed corpus hands parse to `starting_stacks` of `[10000] x 6`, `antes` all zero,
  and `blinds_or_straddles` of `[50, 100, 0, 0, 0, 0]`; `data_pipeline/corpus.py:117-121`
  rejects anything else at parse time.
  On a flat table `_table_depth_bb`'s `stacks[seat] + (street_bet - to_call)` returns 10000 at
  every decision point, so the derived depth is never wrong and `REFUSE_UNEVEN_TABLE` needs a
  stack above 10000, which is impossible.
  Corroborated from the committed reports without running anything: all 290 refusals in
  `latest_sample_refusal_inventory.txt` carry a spot key beginning `t6/d100/`, and a depth or
  blind-structure refusal produces no spot key at all, so zero corpus refusals today come from
  any check this phase touches.
  Capping `to_call` binds only when the level exceeds 10000, which never happens; the boundary
  case `to_call == stack` occurs in 7 hands and 16 decision points and even there the formula
  returns 10000.
  The first draft asserted the opposite in the scope, in the asymmetric criterion, and in the
  vetting packet, and pre-declared a rise in refusals as the expected result.
  Resolved.
  The scope now settles the evidence surface before any criterion is read, the asymmetric
  criterion states the corpus counts as expected zeros and a moving one as a defect rather
  than a discovery, the vetting packet asks for the fixtures beside the zeros, and the
  regression expectation now says agreement rates are expected not to move.
  Filed as `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` with the measurement.

- **[resolved] The pot-reconciliation oracle is a tautology at both runtime producers.**
  `comparison.py:368` and `simulator/table.py:162` both already set the pot to the sum of
  `committed_total`, so if the contributions come from the same place the equality cannot fail
  there by construction.
  It can only bite at the report producers that pass an independent pot.
  An unattended-advance justification resting on an oracle that is vacuous at the two producers
  that matter is the wrong justification.
  Resolved in the contract, which now says the check is a tautology at both live producers and
  names where it does bite.
  `verification/loop_policy.yml` still gives the auto-advance reason as "chips in equal chips
  out, checked against the frozen replayer", which is a stronger oracle than the code will
  have; that file is out of this task's scope and is recorded under Alignment below.

- **[resolved] Refusing on any shallower seat is wrong poker, and the contract mandated exactly
  that.**
  Effective stack is pairwise and only against seats that can still act.
  A hero at 100bb opening with a 40bb seat that has already folded is a 100bb spot, and the
  folded seat cannot affect a chip of the decision.
  The first draft required folded seats to keep contribution entries and therefore recomputed
  starting stacks, so it refused; today's check reads current stacks and never fires on a
  folded seat, so this was a regression the fix would have introduced.
  Resolved: the flat-table test is scoped to the seats still live in the hand, folded seats
  keep their chips in the pot and in the reconciliation, and a test pins that a folded short
  seat does not refuse.
  The same reviewer's point that refusal-code precedence is unspecified is also taken: the
  contract now requires the order to be ruled and pinned, because a ragged hero is tested first
  today and in a live 1/2 game almost no stack is a whole number of big blinds.

## Non-blocker

- Line 78's claim that pot reconciliation "is exhaustive" and "is the reason the loop policy
  lets this phase advance unattended" is stronger than the check will be.
  Both live producers already set `pot=sum(player.committed_total ...)` (`table.py:151`,
  `comparison.py:355`), so if the contributions come from the same `committed_total` the equality
  is a tautology at every real producer and can only fail on a hand-built query.
  `loop_policy.yml` line 85 gives the auto-advance reason as "chips in equal chips out, checked
  against the frozen replayer", which is a different and stronger oracle than the one the
  criteria describe.
  Worth reconciling the two sentences, or the audit packet will claim an oracle the code does not
  have.
- Lines 108-111 and lines 114-116 can be read as contradicting each other, and a stage 4 author
  could freeze both.
  Once starting stacks are recomputed, a hero who bought in short is by construction a table
  where some seat is deeper than hero, so `_table_depth_bb`'s uneven-table branch fires and hero
  refuses; only a hero who is short *on the street* at a flat-start table reaches a decision.
  The distinction is real and the contract is right about both halves, but it is not stated, and
  "a hero who cannot cover the price still reaches a decision" reads as unconditional.
- Lines 177-179 are not an acceptance criterion.
  They restate why the spot key is out of scope, citing `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`,
  and there is nothing a test or a reviewer could fail.
  The reasoning is good and belongs in the Scope section, where the same argument already appears
  at lines 42-47.
- Line 134 attributes "a straddled pot with several callers" to `BLIND-STRUCTURE-VARIANTS`.
  It is named in `PER-SEAT-CONTRIBUTIONS-IN-QUERY`; `BLIND-STRUCTURE-VARIANTS` is the artifact
  format half.
  Trivial, but the two entries are deliberately split and the citation blurs the split the phase
  is relying on.
- `docs/V2_ROADMAP.md:139` predicts this phase touches the Phase 03 and Phase 04 contracts, and
  the contract amends 03 and 06 instead.
  Checked: `PHASE_04_PREFLOP_ARTIFACTS.md` names neither `street_bet` nor `to_call`, so no
  amendment is owed there and the roadmap's guess was simply wrong.
  Recording it so a later reader does not read the divergence as an omission.
- The claim at lines 92-95 checks out.
  `BettingRoundState.legal_actions` offers `raise` only when `player.stack > to_call`
  (`engine.py:82`) and returns an empty set when `player.stack == 0` (`engine.py:67-68`), so the
  engine genuinely never
  offers a raise to a hero whose stack equals the price, and `StrategyQuery.__post_init__` today
  has no rule that would reject it.
  Line 101's restatement of Phase 06's short hero also checks out against
  `generate_postflop_fallback_report.py:132`, where `hero_is_short` is literally
  `0 < self.hero_stack < self.to_call`.
- The two amendments are each exactly two lines plus their backlog ids, inside the `AGENTS.md`
  cap, and Phase 03 at 112 lines and Phase 06 at 223 lines both have headroom.
  The Phase 06 amendment is accurate.
  The Phase 03 amendment is attached to a bullet that lists the query's contents without ever
  naming `street_bet`, so "`street_bet` is now `current_bet`" corrects a sentence that did not
  say it; harmless, but the corresponding sentences that do say it are the Phase 11 ones in the
  blocker above.
- The regression numbers at line 250 verify: `reports/active/latest_sample_comparison_report.txt`
  reads 499 hands compared and 3048 preflop decision points.
- Coordinator note on the four items above that asked for something.
  The hero-short contradiction is now two bullets that state the flat-start case and the
  bought-in-short case apart.
  The non-criterion re-keying bullet is deleted; the argument already sits in Scope.
  The straddled-pot-with-several-callers citation moves to `PER-SEAT-CONTRIBUTIONS-IN-QUERY`.
  The roadmap's Phase 04 guess is left as the reviewer found it, since no amendment is owed.
- From the second reviewer, all carried rather than blocking.
  The backlog's "30bb where the truth is 25bb" is confirmed by hand in two worked cases, and
  the sharper statement is that the derivation collapses to the bet level whenever hero is
  capped; the subtraction identity was right until the 2026-08-20 ruling and is now wrong for
  exactly the capped population.
  The replacement derivation, stack plus hand contribution, is correct for a hero who posted a
  blind, a hero who is all-in, and a table where somebody else went all-in short, and it is
  correct for an ante only because the reconciliation forces the ante onto the posting seat
  rather than into dead money.
  The new `to_call == stack` guard costs nothing on the corpus: `comparison.py:340` takes its
  legal actions from the frozen replayer, and the engine never offers a raise at that price,
  so the 16 boundary decision points survive and the 3,048 denominator is safe.
  Side pots stay outside the phase: contributions make the split derivable but the query still
  carries one pot total, and a short all-in is exactly the table this phase says it now sees,
  so the audit packet owes a sentence on whether it is derived or deferred.

## Alignment

- `BLIND-STRUCTURE-VARIANTS`, plus **a new id must be filed**.
  Nothing in this repo can represent a straddle or an ante anywhere except in a hand-built query.
  `data_pipeline/corpus.py:117-121` rejects any corpus hand whose `blinds_or_straddles` does not
  hold exactly two positive entries, the engine posts only two blinds, and the normalized history
  carries `blinds` as a small/big pair.
  So the "straddle and ante counts" the vetting packet requires at line 220 are structurally zero
  before anything is measured, and every straddle and ante test in this phase is a synthetic
  fixture with no producer behind it.
  `BLIND-STRUCTURE-VARIANTS` covers the artifact-format half only.
  The new entry should say that the ingestion and engine layers cannot produce a straddled or
  anted hand at all, so detection built in phase 13 has no live caller until they can, and it
  should carry the corpus-loader line number as the evidence.
- **A new id must be filed** for `PHASE_11_ENGINE_FIDELITY.md` sitting at exactly the 300-line
  contract cap.
  `CONTRACT-LINE-CAP-BLOCKS-ITS-OWN-AMENDMENT` is `done` and its resolution was the two-line
  amendment rule, which explicitly anticipated this: a contract that reaches the cap even under
  that rule is due for a rewrite that folds its amendments into the criteria they amend, as its
  own `contract-update` task.
  Phase 11 has now reached it and phase 13 is the first phase that needs to amend it.
  The entry should name the rewrite as owed, note that phase 13 is blocked on it for the
  `street_bet` rename and the all-in-ceiling correction, and record that no check reports a
  contract at the cap that owes an amendment.
- `ASYMMETRIC-EFFECTIVE-STACKS`.
  This phase closes the detection half and correctly restates the format half, but nothing in the
  roadmap after it owns that half.
  Phase 14 derives a chart at the phase 12 vocabulary and `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`
  is the stated reason not to re-key twice, which means per-seat depth in a key has no phase at
  all once 14 has run.
  The refusals this phase adds are therefore permanent until somebody schedules that work, and
  the entry's restatement at closeout should say which phase, if any, is expected to take it.
- Coordinator note on the three items above.
  The first two ids are filed: `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` (phase `samples`) carries
  the full measurement over all 499 corpus hands rather than only the loader line, since the
  second reviewer parsed the data and found the same wall from the other side, and
  `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` (phase `contract-update`) carries the Phase 11
  rewrite.
  The third stays open as the reviewer wrote it: no phase after 14 owns per-seat depth in a
  key, and closeout owes a restatement saying which one is expected to take it.
- `verification/loop_policy.yml` gives phase 13 an auto-advance reason the code will not have.
  It reads "chips in equal chips out, checked against the frozen replayer", where the check the
  contract can actually specify is a pot equal to the sum of contributions, which is a tautology
  at both live producers.
  The policy file is out of this task's scope and its reason text is not what decides the
  advance, so this is drift rather than a defect, and it belongs with the same rewrite that
  settles `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` or with a task of its own.
