# ExecPlan: Phase 13, Table-State Fidelity

Contract: `docs/phase_contracts/PHASE_13_TABLE_STATE.md`
Lane: worktree `~/projects/poker-bot-worktrees/phase-13`, branch `phase/13-table-state-fidelity`,
opened from `main` at `12469b1`.
Loop pointer: `verification/loop_runs/13.yml`. Driver: `uv run python scripts/loop_stage.py --phase 13`.

## Objective

Take phase 13 from a skeleton contract to a tagged green gate across the full derived verify
gate plus `check_gate_bite`, closing or restating the five entries in `backlog.yml` that stood
against `phase: "13"` when this plan was written. They did not land the same way. Three closed
and read `done` against phase 13: `PER-SEAT-CONTRIBUTIONS-IN-QUERY`,
`STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS` and `STRATEGY-QUERY-STREET-BET-NAME`. Two did not, and
read `deferred` against `phase: "14"`: `ASYMMETRIC-EFFECTIVE-STACKS` and
`BLIND-STRUCTURE-VARIANTS`, whose titles both ask for a change to the artifact format or the spot
key, which this phase is scoped out of.

The phase changes the runtime query and what the strategy can see through it. It commits no
artifact, no chart, and no sample, and it does not touch the spot key.

## Scope

Approved at stage 1 (`contract-update`), which is where this plan is written:

- `docs/phase_contracts/PHASE_13_TABLE_STATE.md`
- `docs/phase_contracts/PHASE_03_STRATEGY_CONTRACT.md` (two-line amendment)
- `docs/phase_contracts/PHASE_06_POSTFLOP_FALLBACK.md` (two-line amendment)
- `reports/phase_audits/reviews/PHASE_13_TABLE_STATE/**`
- standing scope only for `CURRENT_TASK.yml`, `phase_status.yml`, `backlog.yml`,
  `verification/loop_runs/**`, the generated docs, `docs/exec_plans/**`, `reports/active/**`

Expected at later stages, each needing its own `scope_change_log` entry when it is opened:

- stage 2: `reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`
- stage 4: `tests/test_table_state.py`, the frozen-test migrations across completed phases,
  `verification/mutations.yml`, `scripts/run_verify.py` (command registration only)
- stage 6: `src/poker_training_bot/strategy/contract.py`,
  `src/poker_training_bot/strategy/preflop_chart.py`,
  `src/poker_training_bot/simulator/table.py`,
  `src/poker_training_bot/data_pipeline/comparison.py`,
  `src/poker_training_bot/solver_artifacts/spot_key.py` (docstring correction only),
  `scripts/generate_table_state_report.py` and its measures module, and the four report
  generators that build a query
- stage 9: `reports/phase_audits/PHASE_13_TABLE_STATE.md`

Forbidden throughout: `data/artifacts/**`, `data/samples/**`, the spot key grammar, the
artifact schema, `AGENTS.md`, the check scripts, and `tests/**` from stage 5 onwards.

## Delegation Plan

Subagents are authorized for this phase (Taylor, 2026-08-21). Phases 10, 11 and 12 recorded a
no-delegation exception and self-reviewed every stage, which the phase 12 packet itself names
as the weak link, so `AGENTS.md` step 6 is satisfied properly here and every stage review goes
to an independent read-only reviewer rather than to the coordinator.

- Worker lanes: L1 query shape and validation; L2 producers and the `to_call` cap; L3 the
  preflop strategy's depth, asymmetry and blind-structure detection; L4 the `street_bet`
  rename and the decision-audit version bump; L5 the report generator and its measures; L6 the
  frozen-test migration across completed phases, authored at stage 4 alongside the phase's own
  tests.
- Ownership: L1 owns `strategy/contract.py`. L2 owns `simulator/table.py`,
  `data_pipeline/comparison.py` and the four query-building report scripts. L3 owns
  `strategy/preflop_chart.py` and the `spot_key.py` docstring correction. L4 owns the rename
  sweep across every file naming the field, which crosses all other lanes and therefore runs
  alone. L5 owns `scripts/generate_table_state_report.py` and its measures module. L6 owns
  `tests/**` at stage 4 only. The coordinator owns `CURRENT_TASK.yml`, the contract, this plan,
  `backlog.yml`, `verification/mutations.yml`, command registration in `scripts/run_verify.py`,
  every merge, the gate, and the audit packet.
- Expected outputs: each lane returns a patch confined to the files it owns, the commands it
  ran with their output, a changed-file summary, and the frozen tests it made pass or found
  failing. L5 also returns the report text. L6 returns a per-file verdict saying whether an
  assertion was migrated or rewritten, and why.
- Status: L6 done at stage 4. L1 done at stage 6, 496 lines, `tests/test_table_state.py` at 45 of
  46 with the one remainder inside L3's file. L2 done, all six producer files and all nine
  construction sites, 137 frozen tests green across three completed phases. L3 running. L4 done
  by the coordinator rather than a worker, see the paragraph below - it shrank to four edits in
  files the coordinator already owns, and dispatching a worker for four edits would have cost
  more coordination than it saved. L5 not yet dispatched, because the numbers it reports are not
  real until L3 lands.
- L2 found the one thing no lane owned: the phase 11 canary
  `all-in-ceiling-loose-by-the-price-to-call-again` targets the exact line decision 11 rewrote,
  so its `find` string no longer occurred and the canary could no longer bite. Left alone it
  would have retired a phase 11 legality claim by accident behind a green gate, which is the
  decorative-gate defect this repo has now fixed three times. Re-pointed with the claim
  unchanged, and `test_every_mutation_applies_exactly_once_to_its_file` proves it applies again.
- L4 is smaller than the plan assumed, measured rather than estimated. Every remaining
  `street_bet` in `src/` outside L1's and L2's files is the *engine's* field and keeps its name:
  `poker_core/engine.py` and `poker_core/order.py` read `PlayerState.street_bet`,
  `hand_history/replay.py` and `simulator/run.py` the same, and `data_pipeline/convert.py` uses it
  as a local while walking a street. That is decision 2's one-vocabulary argument working: the
  per-seat name on the query is the engine's name, so the sweep has nothing left to rename in
  code. What L4 owes is the two dangling test citations and the three dated pointers ruled above.
- Integration order: L1 first, alone, because every other lane depends on the field existing.
  Then L2 and L3 in parallel on disjoint files, then L4 alone across the whole tree, then L5
  once the numbers it reports are real. The coordinator runs the phase's own commands after
  each merge and the full gate only after L5.
- Review handoff: an independent read-only reviewer reads the stage diff against the question
  the driver prints, writes to
  `reports/phase_audits/reviews/PHASE_13_TABLE_STATE/stage-NN-name.md` with the three required
  headings, and never edits the code it reviews. Stage 8 gets two: one mechanical, one domain,
  and the domain reviewer is briefed to judge the poker rather than the code's fidelity to the
  contract. The reviewer at stage 4 is the one that matters most, because a wrong test authored
  there survives the freeze and every mechanical check after it.

## Slices

- [x] S1 Contract. Skeleton replaced with criteria written against the five backlog entries,
      plus the two-line amendments to the Phase 03 and Phase 06 contracts. Two independent
      reviewers found six blockers between them, all resolved in the contract; two new backlog
      entries were filed from their findings. Evidence: the contract at 299 of 300 lines with
      every backlog citation resolving, `check_contracts`, `check_file_sizes`, `check_scope`
      and `check_execplan_delegation` green, and the stage-1 review note.
- [x] S1a Prerequisite, outside this phase's task, run at stage 10 because a contract may only
      be edited in `contract-update` mode. `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` was a
      `contract-update` task of its own: `PHASE_11_ENGINE_FIDELITY.md` was at 300 of 300 lines,
      named `street_bet` in criteria this phase renames, and asserted an all-in-ceiling claim
      this phase makes false. `AGENTS.md` forbids raising the cap and rules the answer is a
      rewrite folding amendments into the criteria they amend. Done: 283 lines from 300, all 39
      acceptance bullets intact and 32 byte-identical, measured with
      `check_contracts.section_bullets`. The debt was thirteen edits rather than the nine listed,
      and the task's own independent review found it had left the struck arithmetic identity
      standing in three documents it had open, including the backlog entry that spawned it.
- [x] S2 Decisions. Sixteen calls recorded with a reversibility class before any code, one of
      them `frozen-into-data`. The independent reviewer found four blockers, all resolved:
      the field names and shape, whether the query carries street and hand contributions or
      only one, what a shallower seat's refusal code is called, whether a straddle and an ante
      get one code or two, the rename target, and how far the frozen-test migration reaches.
- [x] S3 Human gate. Decision 6 ruled by Taylor on 2026-08-21: a live seat whose starting stack
      differs from hero's at all refuses, no tolerance band. The reviewer corrected the recorded
      cost, which is almost nothing rather than nothing.
- [x] S4 Tests. 66 tests across two files, all red on assertions; five canaries; the frozen
      tests of five completed phases migrated; `test_postflop_fallback.py` split at 718 lines.
      The independent reviewer found six blockers, all fixed.
- [x] S5 Freeze. 28 files, 775 test functions. `tests/**`, `verification/**` and
      `scripts/run_verify.py` out of `approved_scope`; `base_commit` moved to the freeze commit.
- [x] S6 Build. L1 to L5 merged in the integration order above. 954 tests pass, both new command
      IDs run clean, all five phase canaries and the re-pointed phase 11 canary occur verbatim,
      `check_scope`, `check_file_sizes` and the full quality gate green. Two independent
      reviewers read the stage diff, one mechanical and one on the poker.
- [x] S7 Gate. 45 commands green through `scripts/run_verify.py` with the canaries biting under
      `check_gate_bite`.
- [x] S8 Review. Two independent reviewers, mechanical and domain, closed over a verification
      round.
- [x] S9 Audit. Packet with the corpus counts, the producer sweep, and one hand-recomputable
      number. The stage-9 reviewer re-derived every number rather than reading it; all of it
      reproduced and every blocker was a list disagreeing with the file it claimed to copy.
- [x] S10 Closeout. Backlog entries settled to `done` or restated, five alignment items filed
      from the stage-10 review, ExecPlan filed, phase completed, tag, idle.
- [ ] S11 Advance. Policy says `auto_advance: true` for phase 13.

## Coordinator rulings during the build

These are integration decisions too small for the decision list and too load-bearing to leave to
whichever worker reaches them first. They are recorded here rather than in the decision list
because the task is in implementation mode and that list is settled.

**2026-08-21, the per-seat record's container and class names.** Raised by the frozen-test
migration worker, who noticed decisions 1, 2, 5 and 14 fix the record's own fields
(`street_bet`, `committed_total`, `folded`, `all_in`) and name neither the container on
`StrategyQuery` nor the class. Ruled: `seat_states: tuple[SeatState, ...]`, one entry per seat
in `stacks`, sorted ascending by seat.

Rejected `contributions` and `SeatContribution`, which is the better read of the contract's own
noun, because the record carries `folded` and `all_in` and those are not contributions. A field
named for less than it carries is the exact defect this phase exists to end, and repeating it in
the fix would be worse than the original. Rejected a bare `seats` container because it reads as
the seat numbers, and the query already keys `stacks`, `seat` and `button_seat` by seat integer.
`SeatState` is deliberately a near-twin of the engine's `PlayerState` minus name, hole cards and
stack, which is decision 2's one-vocabulary argument carried to the container; the name differs
because the query is seat-oriented where the engine is player-oriented.

All three stage 4 workers were given the ruling at once so none had to coordinate with the
others.

**2026-08-21, where an ante sits, correcting decision 3.** Raised by the same worker, which
found decision 3 ("preflop, each seat's street contribution must equal its hand contribution")
and decision 10 ("the ante probe gives every seat an ante inside its hand contribution") cannot
both hold. Ruled on the poker rather than on the rule count: an ante is dead money, it goes into
the pot, and it does not count toward what a seat owes, so putting it in the street figure would
make an anted seat owe less to call than an unanted one at the same level. The ante lives in
`committed_total` only. The rule is therefore not equality but `committed_total >= street_bet`
on every street, with the difference being that seat's dead money; the only impossible direction
is a seat holding more this street than over the whole hand.

This improves the phase rather than patching it. Preflop, `committed_total - street_bet` is
forced dead money by arithmetic the query already carries, on a live seat and a folded one
alike, and it can never be absorbed the way a straddle can. So decision 8's ante signal becomes
that difference: uniform across seats is an ante, non-uniform is a dead blind and takes the kept
residual code. The strategy-side worker reached the same uniformity reading independently.

**This makes a clause in the phase 13 contract false.** Line 75 says the two figures "coincide"
preflop. Contract edits are forbidden in implementation mode, and the phase 13 contract is at
exactly 300 lines so it cannot take an added amendment either. The fix is a reword inside the
existing line budget, folded into the `contract-update` task this phase already owes for
`ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP`, which must run before the phase tags.

**2026-08-21, how `seat_states` serializes.** The two workers defaulted differently. Ruled: a
seat-keyed mapping, `{"0": {...}}`, with the inner object carrying `street_bet`,
`committed_total`, `folded` and `all_in` and not repeating the seat. It mirrors `stacks`, the
field it is validated seat-for-seat against, and a test pins that the two key sets are
identical. A list of objects would store the seat twice, which is where drift starts.

**2026-08-21, a requirement carried to the stage 6 builder.** The rewritten `StrategyQuery`
class docstring must contain the phrase "current bet level" and must name both `current_bet` and
the per-seat `street_bet`. A migrated frozen test in `tests/test_engine_fidelity.py` asserts it,
and the point of the rename is that one name now has one meaning.

**2026-08-21, where the per-seat impossibility is rejected.** Raised by lane L1, which had been
told to put `committed_total >= street_bet` in `StrategyQuery.__post_init__`. Ruled: it moves to
`SeatState.__post_init__`. The invariant is per-seat, so a standalone record that holds more on
this street than over the whole hand is impossible on its own terms and should not need a query
wrapped around it to be caught. No test or canary distinguishes the two placements - the frozen
test wraps the whole query construction in `pytest.raises`, which the record's own error
satisfies, and L1 verified that rather than assuming it.

**2026-08-21, the order the forced-money signals fire in.** Not raised by a worker: derived by
the coordinator from the stage 4 fixtures before lane L3 was briefed, because a builder who gets
it wrong reads a passing specification as a broken test. Ruled: the two straddle signals fire
*before* unexplained money is classified. Unraised-level first, then the minimum-raise
disagreement, and only then is a seat's unexplained money read as an ante when it is uniform
across every seat and as the kept residual code when it is not.

The fixture that forces the order is `test_every_pot_the_deleted_arithmetic_bound_refused_still_refuses`.
Its straddled table has 200 unexplained chips sitting on one seat, so classified first it would
take `blind-structure-not-representable`, and the test requires `pot-holds-a-straddle`. What
names it is the minimum-raise disagreement, which is decision 8's third signal doing exactly the
job it was added for. Forced money as a whole still runs before the depth checks, keeping the
position the deleted pot bound already held, so no spot changes which code it refuses with
unless this phase genuinely changed the answer for it.

**2026-08-21, what the rename owes a completed phase's audit packet.** The contract says no
committed audit is left on the old name. Ruled: a completed packet is dated evidence rather than
live vocabulary, so its prose keeps the name it shipped with and gains a dated pointer saying the
field was renamed here. Rewriting the record would falsify it - the Phase 11 packet's claim that
it documented `street_bet` and left the name was true when it was written.

What is not history is a citation that no longer resolves. Stage 4 renamed the two frozen tests
`test_a_street_bet_below_the_price_to_call_is_rejected` and
`test_a_street_bet_equal_to_the_price_to_call_is_accepted`, and the Phase 11 packet cites both by
name, so it now sends a reader to tests that do not exist. Those two citations are corrected.
Nothing mechanical catches this: `run_full_quality_gate.py` checks backlog ids in `reports/`, not
test names, so it is a finding rather than a red gate.

**2026-08-21, lane L1 died mid-task.** The worker authoring `tests/test_table_state.py` was
terminated by an API error while applying the naming ruling. The file it had written was
complete and parsed, so the coordinator finished the rename and then owned that file for the
ante correction above. Recorded because the Delegation Plan says L1 is a worker lane and it was
not, for the last edits.

## What stage 4 specified for the stage 6 builder

The tests are the specification, and so are the five canaries in `verification/mutations.yml`.
Each canary's `find` string must occur exactly once in the built code or `check_gate_bite` fails
at stage 7, so these identifiers are not suggestions:

- `contributed_total`, the sum the pot is validated against, in `strategy/contract.py`, used as
  `if self.pot != contributed_total:`
- `hero_stack` and `aggressive` in the capped-hero guard, used as
  `if self.to_call == hero_stack and aggressive:`
- `hero_start = stacks[query.seat] + hero.street_bet` in `_table_depth_bb`
- `if state.folded:` as the live-seat filter in the flat-table test
- `predicted_min_raise` in the straddle detector, used as
  `if query.min_raise_target != predicted_min_raise:`

The builder must also keep the phrase "current bet level" in the `StrategyQuery` class docstring
and name both `current_bet` and the per-seat `street_bet` there, because a migrated frozen test
in `tests/test_engine_fidelity.py` asserts it.

**`generate_table_state_report.py` must validate its own figures and exit non-zero when they do
not hold.** Two canaries name it in `must_fail`, and `check_gate_bite` requires every command it
names to fail with the mutation applied, so a report that merely prints whatever it is handed
would leave both surviving. Phase 12 set the pattern with `_validate_census`, which fails the
gate when the census splits do not reconcile. Here the two figures that must be self-checked are
hero's derived depth, which has to agree with hero's own recorded contribution rather than with
the bet level minus the price, and the straddle census, which has to reconcile against the
minimum-raise prediction the detector used. This is the stage 4 reviewer's sixth blocker and it
is a real requirement rather than a bookkeeping fix: a report nobody can break is a report
nobody has tested.

## What the stage 6 review round changed

Two independent reviewers read the build, one on mechanical fidelity and one on the poker. They
found three blockers between them and neither had seen the other's work. That is the per-stage
review rule earning its keep: phases 10, 11 and 12 each self-reviewed and each paid for it later.

Both reviewers independently found the same hole, and the mechanical one found the half that
makes it a blocker rather than a footnote. Signal 3's prediction is the final level plus the last
increment, and a straddle perturbs only the FIRST increment, so past one raise the prediction is a
difference of two recorded amounts and is identical straddled or not. It then built a straddled
table with two raises where `chart_lookup` returns a hit and `weights_for` hands back the
UNSTRADDLED range. That is the phase's headline claim failing and the forbidden shortcut about
reaching for a neighbouring cell, found by nothing the gate runs.

**Ruled: no guard, and the residual is restated instead.** The straddle's trace is genuinely
destroyed once its poster raises, because a raiser's predicted contribution is its own raise-to
amount and that absorbs the forced money. Only a declared blind structure on the query recovers
it, and decision 8 considered that and declined it as the format change this phase is scoped out
of; any guard written without it over-refuses ordinary unstraddled tables. So the fix is the
truth: `forced_money.py`, `_forced_money_refusal` and the report's limitations now all say signal
3 fires only on single-raise pots, and say plainly that a table inside that residual is *answered*
with the wrong range rather than merely mis-coded. Filed as
`STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`. A report that hides this is worse than one that never
claimed it.

The poker reviewer's two blockers were both about the refusal detail, which is this phase's whole
non-answer deliverable. The depth refusal reported the first offending seat in ascending seat
order, so two physically identical tables reported 90bb or 20bb depending on seat numbering, when
the number that caps hero's effective stack is the *shortest* live opponent - somebody reading an
inventory of those rows would have set a tolerance band against the wrong number. And the
ragged-hero code, which decision 7 puts first and which therefore swallows the majority of live
spots, carried no detail at all. Both fixed and both behaviour-preserving on the frozen suite.

One correction to my own earlier judgment, recorded because the reasoning matters more than the
outcome. I filed the short-all-in false straddle as a deferred alignment item on the builder's
argument that flooring the minimum-raise walk would also hide a genuine one-big-blind straddle.
The poker reviewer showed that argument is wrong - a straddle's first increment is a full raise
measured from a level above the declared big blind, so it never sits below the floor - which made
the fix free. It is fixed, the walk now mirrors `BettingRoundState.apply`, and the backlog entry
is `done` against phase 13 rather than deferred, keeping its wrong reason on the record because an
unreachable defect with a plausible argument for leaving it is exactly what a review is for.

The mechanical reviewer also caught a forbidden reconstruction that had shipped: a fixture producer
derived villain's contribution as the pot minus hero's, by subtraction, which is the defect this
phase exists to end appearing inside the phase that ends it.

### The three fix rounds, and the one figure the packet must get right

Round one fixed the three blockers. The verifying reviewer then found that the fix for one of them
was itself unguarded: reverting the new extremal-seat selection in BOTH copies left all 954 tests
green, because no frozen test puts two live seats on the same side of hero and the report's
validator only pinned that the two copies AGREE. A blocker fix that nothing can catch is this
repo's most-repeated defect arriving inside the remedy, so round two closed it two ways - the
validator now recomputes the extreme offending seat from the seat states and asks neither copy, and
refuses to publish unless a distinguishing row exists in each direction. Verified by the
coordinator by hand rather than taken on report: both copies reverted in both directions leaves
every test green and `generate_table_state_report` exits 1 naming the seat it should have picked.

Round two also replaced the phase's most important admission with a table that can actually happen.
The demonstration that a straddled pot reaches the chart had the lojack straddling and then making
the first raise, and a straddler acts last, so it was unreachable. It now rests on a big-blind
straddle to 200, a cutoff open to 500 and a big-blind three-bet to 1,350, every price legal at the
straddled table's own minimums, verified reaching `t6/d100/CO/CO:raise@2.5,BB:raise@13.5` and
returning a real raise.

Round three is coordinator work on the last three findings. The canary added in round two credited
the wrong one of the validator's two rules, so its description now says which rule kills which
mutation and states plainly that `pytest` is named but is not what notices - all 66 frozen tests
pass under it, and the registry check is the only thing that reddens. A second canary was added for
the SHORTER direction, which had none: that is the direction this phase created and the one that
matters in poker, since effective stack is the minimum of hero and villain. And a sentence in the
report claiming one committed row was the only place the two rules differ now says it covers the
deeper direction only and names the constructed probe covering the other.

**The figure the audit packet must not inherit wrong.** The report's own prose was corrected for
this and the plan carries it too, because a packet written from the plan would otherwise repeat the
error. On `phase02-three-way-side-pot` at 5/10 blinds, only ONE row changed behaviourally: from
seat 0's chair, `table-is-not-one-flat-stack-depth (seat 1, stack_depth_bb 10)` became
`(seat 2, starting_chips 200, stack_depth_bb 20)`. The button's chair and seat 1's chair each only
GAINED `starting_chips`; their seat and depth were already the extremal ones. The first fix report
attributed the move to the button's chair, which is wrong.

## Coordinator verification the reviews could not do

The stage 6 mechanical reviewer listed, honestly, what it had not checked, and one item on that
list is load-bearing: it compared the 499 hands and 3,048 decision points against two committed
reports rather than re-deriving them, so the phase's whole "the corpus cannot exercise any of
this" premise rested on documents this repo wrote about itself.

Re-derived by the coordinator from the raw committed source text in
`data/samples/public_corpus/corpus_hands.jsonl`, parsing each hand's own PHH body rather than any
normalized form: 499 hands, and across all of them exactly one distinct `starting_stacks`
(`[10000] x 6`), one distinct `antes` (all zeros), and one distinct `blinds_or_straddles`
(`[50, 100, 0, 0, 0, 0]`). Not one unequal stack, not one ante, not one straddle, measured at the
source. That is the contract's Scope claim and decision 2's "what was measured first" section
confirmed against the bytes the dataset shipped, and it is what makes every zero in the report a
checked regression proof rather than an assertion.

What it does not establish, and the packet must say so: that those bytes are the dataset they
claim to come from. The gate has no network by design, so the provenance claim stays unchecked
here exactly as `docs/CORPUS_COMPARISON_LIMITS.md` already records for phase 08.

## The fourth fix round, at closeout, and why content arrives there

Stage 10 is bookkeeping by the driver's own question, and this phase's stage 10 carried content,
because S1a - the `ENGINE_FIDELITY_CONTRACT_REWRITE` task - is a `contract-update` task nested
inside the closeout, and `contract-update` is the only mode that may edit a contract. The stage-1,
stage-2 and stage-6 findings that needed a contract edit could not be made when they were found.
They queued here. The stage-10 reviewer read the whole task diff against that question and found
three blockers; all three are fixed and the note is
`reports/phase_audits/reviews/PHASE_13_TABLE_STATE/stage-10-closeout.md`.

Five edits landed, each measured against the committed code rather than argued:

1. **The contract's gap line** (stage 1's clause, falsified by stage 6's ante ruling). It said the
   gap between `committed_total` and `street_bet` "is an ante". It is preflop dead money, of which
   an ante is the case this phase classifies - uniform across seats is an ante, non-uniform takes
   the residual code - and a gap alone does not settle which. The old wording made the classifier's
   own distinction disappear into a definition.
2. **The straddle criterion's "after a full first raise"** (stage 6's floor fix). Signal 3's
   arithmetic - the disagreement is the straddle less the big blind - holds for a full first raise.
   The branch itself fires on any recorded raise, and after a short first raise it still refuses but
   by a different amount. Verified: at 50/100 with a 200 straddle and an all-in to 250 the table
   offers 350 and `predicted_min_raise_target(100, [250])` returns 400.
3. **The evidence criterion**, reworded to the house form the Phase 12 contract uses. No claim
   changed; the report already carries the seat-by-seat reconciliation it now reads as demanding.
4. **The Scope escape count, two to three.** The contract enumerated the escapes as a closed list
   and missed the big-blind-sized straddle whose poster has acted, which the packet's own "Smaller
   residuals" paragraph already named. Filed the shape as
   `CONTRACT-SCOPE-ENUMERATES-RESIDUALS-WITH-NOTHING-CHECKING-THE-COUNT`.
5. **Decision 8's first edge case.** An earlier draft generalised the big-blind-sized straddle's
   invisibility to any straddle whose poster has acted; the stage-10 reviewer measured that false,
   and the correction then dropped the other half. Both halves are now stated and both were run:
   with `blinds=(50,100)`, `button=3` and seat 0 holding 100, `unexplained_contributions` with no
   recorded actions returns `{0: 100}` and the pot is refused `blind-structure-not-representable`;
   with `SeatAction(0, "call")` it returns `{}` and the pot is answered. And a 200 straddle whose
   poster has called returns `{0: 100, 5: 100}` but is refused `pot-holds-a-straddle` first, because
   the level signal fires before unexplained money is classified. So only a straddle sized at the
   big blind clears signal 1 at all, and only after its poster acts.

The reviewer also measured the residual one raise wider than it is. The straddle cancels out of
signal 3 only when every raise after the first is a *full* raise: at 50/100 over a 200 straddle,
an open to 600 then a short all-in to 800 leaves the table offering 1,200 against a prediction of
1,300, so the pot still refuses. Two full raises - 600 then 1,500 - agree at 2,400 and the pot is
genuinely invisible. The wide wording sits in four artifacts including code this task may not
touch, and the error is in the conservative direction, so it is
`STRADDLE-RESIDUAL-BOUNDARY-IS-STATED-WIDER-THAN-MEASURED` against phase 14 rather than a fix here.

Making room for the packet paragraph cost more than the paragraph. The packet stood at 498 of 500,
so about 120 lines of surrounding prose were rewrapped from ~88 to ~98 characters to buy 8 lines,
producing a 250-line diff. Every rewrapped paragraph is word-for-word what it was apart from the
five changes above and a stale contract line count. Filed as `PHASE-AUDIT-PACKET-AT-ITS-LINE-CAP`,
because a completed packet has no rewrite rule to fall back on the way a contract does, and nothing
reports one approaching its cap.

## Verification

Command IDs this phase adds: `pytest_table_state`, `generate_table_state_report`.
Report it commits: `reports/active/latest_table_state_report.txt`.
Gate: `uv run python scripts/run_verify.py`, which derives the full set from every active or
completed contract, plus `scripts/check_gate_bite.py`.
Every canary must bite, and at least one must prove the pot reconciliation fails the gate when
it is removed.

## Outcome

Complete. The phase closes on a green gate with `check_gate_bite` proving the canaries bite, and
the closeout commit that follows it carries the tag `phase-13-complete`, sets phase 13 `completed`,
resets `CURRENT_TASK.yml` to idle and files this plan under `docs/exec_plans/completed/`. Two
commits rather than one because `check_execplan_delegation` requires an active plan while a task is
open and `check_scope` measures an idle task's diff against HEAD, so the closeout can only move
files the standing scope already covers. Every stage that produced a diff owes and has an
independent read-only review note under `reports/phase_audits/reviews/PHASE_13_TABLE_STATE/`,
stages 1, 2, 3, 4, 6, 8, 9 and 10, and no blocker is left open in any of them.

What it bought, stated as the packet states it: no new answers. Every table the query can now see
is a table the strategy now refuses with a code naming the missing shape, and three classes still
escape and are answered as something else - a straddled pot past a full second raise, a straddle
sized at the big blind once its poster has acted, and a game whose blinds are not in the chart's
own ratio. All three are filed forward, the last of them as the phase's largest single finding.

What stage 1 finished, kept because the reviews changed more than the wording. The corpus turns out to
be one flat structure in all 499 hands, with no ante and no straddle and no unequal stack, so
every table-shape number the first draft promised was structurally zero; the contract now names
constructed fixtures as the discovery surface and the corpus as a zero-delta regression proof.
The straddle detection the first draft specified could not see the straddle it required, and
the criterion now carries all three signals including the minimum-raise-target disagreement.
Refusing on any shallower seat would have refused on folded seats, which is wrong poker, so the
flat-table test is scoped to live seats. The pot reconciliation is a tautology at both live
producers and the contract now says where it actually bites.

## Next Agent Bootstrap

Work only in `~/projects/poker-bot-worktrees/phase-13` on `phase/13-table-state-fidelity`.
Never work in `~/projects/poker-bot` or the main worktree.

Ask the driver and do only what it names, then `--advance`:

    uv run python scripts/loop_stage.py --phase 13 [--advance]

**Current state: the phase is complete.** The closeout commit tags `phase-13-complete`, sets phase
13 `completed` in `phase_status.yml`, resets `CURRENT_TASK.yml` to idle and files this plan under
`docs/exec_plans/completed/`. There is no further work in this lane. Nothing here needs continuing;
what follows is what the next phase should carry out of it.

Phase 14 is the next lane, and it is the phase most of this one's residuals were filed against.
Its policy entry is `auto_advance: false`, so it stops for Taylor at stage 11 and its
`frozen-into-data` decisions stop earlier: it commits the chart the bot plays, which is where a
wrong range becomes the reference for everything after it.

What phase 14 inherits by id, all in `backlog.yml`:

- `ASYMMETRIC-EFFECTIVE-STACKS` and `BLIND-STRUCTURE-VARIANTS` - the two entries this phase was
  written against and did not close. Both ask for a change to the artifact format or the spot key,
  which this phase was scoped out of, and six other entries wait on them.
- `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE` and
  `STRADDLE-RESIDUAL-BOUNDARY-IS-STATED-WIDER-THAN-MEASURED` - the headline residual and the fact
  that it is stated one raise too early. Both need a declared blind structure to fix properly.
- `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` - the largest single finding of this
  phase. The ratio the committed artifact was solved at is recorded nowhere, so nothing can compare
  a table's blinds against it.
- `SUBTRACTION-IDENTITY-SURVIVES-IN-FROZEN-TESTS-AND-CODE`,
  `FORCED-MONEY-DOCSTRING-DROPS-THE-STRADDLE-POSTER-PRECONDITION` and
  `FORCED-MONEY-SIGNALS-ARE-NUMBERED-THREE-WAYS` - three sweeps through
  `strategy/preflop_chart.py`, `table_state/forced_money.py` and the frozen tests, which phase 14
  is the next phase to open.

Three process lessons this phase paid for, worth carrying rather than rediscovering. Every list of
stale statements this phase produced was itself incomplete, at every stage that produced one, so
audit against the tree rather than against a list. A blocker fix that nothing can catch is this
repo's most-repeated defect arriving inside the remedy - stage 6's round two found one and closed
it two ways. And subagents were authorized here and every stage review went to an independent
reader, which is what phases 10 to 12 skipped and paid for; two workers died mid-task on API
errors during stage 4, so verify a worker's output against the artifact rather than its report.
