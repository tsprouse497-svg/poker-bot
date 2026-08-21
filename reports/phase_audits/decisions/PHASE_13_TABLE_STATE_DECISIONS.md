# Phase 13 judgment calls

These are the choices that decide what `StrategyQuery` says about the table and what the
preflop strategy does once it can see it. The five defects are not in question anywhere below;
what is in question is the shape each fix takes.

Every item carries a reversibility class, which the loop driver reads at stage 3 to decide
whether it must stop for a human.

- `runtime-reversible`: the choice only changes behaviour at query time, so a later edit
  changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact **or fixture** that every
  later phase is then measured against. The loop halts until a human answers.

**One item is `frozen-into-data`: decision 6.** The first draft of this list said none were, on
the reasoning that the phase commits no artifact, no chart and no sample. An independent
reviewer showed that reading is too narrow. `docs/LOOP.md` defines the class as a choice written
into a committed artifact **or fixture** that later phases are then measured against, and this
contract requires decision 6's rule to be pinned by tests that stage 5 freezes. Reversing it
afterwards is a task with `tests/` reopened, not an edit, which is exactly the cost the class
exists to make a human pay attention to.

`verification/loop_policy.yml` gives this phase `auto_advance: true`, so nothing else would have
stopped it. That is the whole reason the class matters here: phase 12 could flag a reversible
call for a human because policy already halted it at stage 3, and phase 13 cannot. A flag with
no mechanism behind it reaches nobody.

The other twelve items are `runtime-reversible`. Every one is a field shape, a validation rule,
a refusal rule, or a report choice whose default a later edit changes without re-opening a
frozen test that asserts the *behaviour* rather than the shape.

## What was measured first

Every number below was measured on this branch rather than quoted from `backlog.yml` or
`docs/V2_ROADMAP.md`, because stage 1 found that two of the figures those documents carry are
wrong.

### The corpus cannot exercise any of this

All 499 committed corpus hands parse to `starting_stacks` of `[10000] x 6`, `antes` of all
zeros, and `blinds_or_straddles` of `[50, 100, 0, 0, 0, 0]`. Not one unequal stack, not one
ante, not one straddle. `data_pipeline/corpus.py` rejects at parse time any hand that does not
post exactly two positive blinds in the first two seats, the engine knows no ante, and
`simulator/config.py` forces one starting stack for every seat. So the decisions below are
settled against constructed fixtures and against what the code will do in a live game, not
against a corpus measurement, and `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` records why.

### There are nine query producers, not five

Grepping every `StrategyQuery(` construction gives nine sites across six files. Two cap
`to_call` at hero's stack and seven do not: `data_pipeline/comparison.py`,
`simulator/table.py`, the enumeration site in `scripts/generate_postflop_fallback_report.py`,
`scripts/generate_preflop_strategy_report.py`, and three literal fixtures in
`scripts/generate_engine_fidelity_report.py`. `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS` says
three. Decisions 9 and 10 exist because two of the sites it does not name break under this
phase's own rules.

### The depth error is exactly the bet level

`_table_depth_bb` derives `stacks[seat] + (street_bet - to_call)`. Worked at a big blind of 10,
for a hero holding 150 who has put 100 into a level of 300: uncapped, `to_call` is 200 and the
derivation gives 250, which is 25bb and correct. Capped, `to_call` is 150 and the derivation
gives 300, which is 30bb and wrong. The general form is that a capped hero derives as the bet
level itself, whatever hero actually started with. So the subtraction identity was right until
Taylor's 2026-08-20 ruling and is now wrong for exactly the capped population, which is the
same population an asymmetric table produces.

### The straddle that slips through, and what still sees it

50/100 with a 200 straddle, an open to 600, the straddler and the big blind calling, the small
blind folding. Contributions are 50/600/600/600 for a pot of 1,850, against the current pot
bound of `50 + 100 + 3*600 = 1,950`, so it is admitted today. Per-seat contributions do not
help: an unstraddled pot at the same price predicts 50/600/600/600 too. What still differs is
the minimum raise target, 1000 here against 1100 unstraddled, because the first raise is
measured from the straddle rather than from the big blind. Decision 8 is built on that.

## 1. What per-seat quantities the query carries

Reversibility: runtime-reversible

Default: **both the street contribution and the hand contribution, per seat.**

Options: street-and-hand | street-only | hand-only
Answer: [street-and-hand]

*Street only.* Enough for the bet level and enough for every preflop question, because preflop
the two coincide. It fails the moment a postflop caller wants the pot to reconcile, since the
pot is made of hand contributions and the street figure resets to zero at every street. The
engine already carries both for the same reason.

*Hand only.* Reconciles the pot and derives every starting stack, and cannot say what a seat
owes to be square with the current bet, which is the quantity every legality rule is written
against.

The cost the default accepts: two fields where a preflop-only phase needs one, and a preflop
invariant (they are equal) that no rule enforces, so a producer can set them inconsistently
preflop and nothing notices. Decision 3 is where that gets caught.

## 2. What the per-seat fields are called

Reversibility: runtime-reversible

Default: **the engine's own names, `street_bet` and `committed_total`, on a per-seat record.**

Options: engine-names | new-names | qualified-names
Answer: [engine-names]

`PlayerState` already carries exactly these two quantities under exactly these two names. Using
them means the repo holds one vocabulary; inventing `street_contribution` and `hand_total`
would mean a reader translating at the boundary, which is how `STREET-BET-MEANING-AMBIGUOUS`
started.

This only works because decision 4 renames the query's own `street_bet`. Carried out of order,
the query would hold `street_bet` meaning the level and a per-seat `street_bet` meaning a
contribution, which is the collision this phase exists to end, made worse. The two decisions
ship together or neither ships.

The cost the default accepts: a reader who knows the old query and not the engine will read the
per-seat `street_bet` as the old field for a moment.

## 3. How the pot is reconciled

Reversibility: runtime-reversible

Default: **`pot` must equal the sum of the per-seat hand contributions, exactly, or the query
is rejected.** Preflop, each seat's street contribution must equal its hand contribution.

Options: exact-equality | equality-with-a-dead-money-field | advisory-warning
Answer: [exact-equality]

*A dead-money field.* Would admit rake taken preflop, a forfeited dead blind, and the postflop
fallback enumeration's 100 unattributed chips. It is also a hole exactly the size of the defect
this rule exists to catch: any producer that cannot make its arithmetic work can put the
difference in the field and pass.

*Advisory.* A validation nobody fails is documentation.

The cost the default accepts, stated plainly: a raked hand cannot be expressed as a query at
all. That is a hard stop for any later ingestion of real online hands, it is the right
direction for now because this repo's charts are rake-free by ruling, and it is filed rather
than solved here.

Also recorded honestly: at the two live producers this check cannot fail, because both already
build the pot as the same sum they would supply as contributions. It bites at the report
producers that supply an independent pot, and at every producer written after this phase.

## 4. What the query's bet-level field is renamed to

Reversibility: runtime-reversible

Default: **`current_bet`**, matching `BettingRoundState.current_bet`.

Options: current_bet | bet_level | keep-street_bet
Answer: [current_bet]

*`bet_level`.* Reads well and is a third name for a quantity that already has two.

*Keep it.* Was phase 11's choice and was right then, because the collision was latent. Decision
2 makes it live.

The cost the default accepts: the serialized payload key changes, so
`DECISION_AUDIT_SCHEMA_VERSION` moves to 3, every committed decision audit regenerates, and
frozen tests in four completed phases have to be migrated. Decision 12 covers the migration.

## 5. Where the strategy learns which seats are still live

Reversibility: runtime-reversible

Default: **an explicit per-seat folded marker on the query**, beside the two contributions.

Options: explicit-marker | derive-from-preflop_actions | derive-from-zero-contribution
Answer: [explicit-marker]

*Derive from `preflop_actions`.* Works preflop, which is the only street the chart is consulted
on, and stops working the moment anything postflop asks. The query already carries no postflop
history and this phase is not adding one.

*Derive from a zero contribution.* Wrong in both directions: a seat that folded to a raise has
a positive contribution, and a seat yet to act in an unopened pot has none.

The cost the default accepts: a third per-seat field, and a producer that forgets to set it
reports a folded seat as live, which over-refuses rather than under-refuses. Over-refusing is
the safer failure and the reconciliation will usually catch it anyway.

## 6. Whether a live seat shallower than hero refuses, and at what tolerance

Reversibility: frozen-into-data

**This is the one item the loop must stop for.** It is filed `frozen-into-data` because the
contract requires the rule pinned by frozen tests, so stage 5 locks it and a later change is a
task rather than an edit. Nothing else in the phase would have stopped for it, since policy
gives phase 13 `auto_advance: true`.

Default: **any live seat whose starting stack differs from hero's at all refuses, with no
tolerance band.** A seat that has already folded never refuses, whatever it holds.

The question, in one sentence and with no code in it: at a real table no two stacks are ever
exactly equal, so should the bot refuse a hand whenever any opponent still in it has a
different stack from hero's by even one chip, or should it answer normally as long as hero's
own depth matches the chart and refuse only when an opponent is short enough to change the
price hero is being offered?

Options: exact-equality | tolerance-band | shallower-only-beyond-a-threshold | no-check
Answer: [exact-equality]

This is the decision with the largest behavioural reach in the phase, and the honest statement
of its cost is that **it refuses essentially every real table.** Committed data cannot show
that, because all 499 corpus hands are exactly 100bb, but in a live 1/2 game no two stacks are
equal and almost none is a whole number of big blinds. A bot given real table state would
answer almost nothing.

Two things make exact-equality the default anyway. `_table_depth_bb` already refuses a hero
whose own depth is not a whole big blind, so exactness is the standing rule rather than a new
severity. And the alternative is a tolerance nobody can derive: 5bb and 10bb are both
defensible and neither is measurable against anything this repo holds.

A third argument was tried and does not hold, recorded because it is the one a reader will
reach for. `docs/PREFLOP_ARTIFACT_CONTRACT.md` forbids nearest-depth matching by name, but that
rule is about matching hero's own depth to a neighbouring cell, and a tolerance here would
still look hero's exact cell up. The V1 no-heuristic-guessing boundary probably still reaches
it, and probably is why this is a question for a human rather than a ruling this list can make.

What it costs in practice is therefore a coverage collapse that only appears when real table
state arrives, which is after `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` is solved. Whoever solves
that is the one who will want this re-ruled, and the refusal detail names the offending seat
and its depth so the re-ruling has data behind it.

The folded-seat exclusion is not a tolerance and is not negotiable: effective stack is pairwise
and against seats that can still act, so a folded 40bb seat cannot change a chip of hero's
decision. Refusing on it would be a regression this phase introduced.

## 7. What order the depth checks fire in

Reversibility: runtime-reversible

Default: **hero's depth ragged, then a live seat deeper than hero, then a live seat shallower
than hero.** First match wins and the rest are not evaluated.

Options: hero-first | villain-first | report-all-findings
Answer: [hero-first]

Hero first because a hero whose own depth is not a whole big blind has no depth to compare
anything against, so the other two checks are not even well defined. Deeper before shallower
because deeper is the check that exists today and keeping its precedence means no spot changes
which code it refuses with unless this phase genuinely changed the answer for it.

*Report all findings.* Would make the refusal inventory more informative and would change the
shape of `StrategyRefusal`, which carries one code. Not worth a contract change here.

The cost the default accepts: at a ragged real table, hero's own raggedness masks every table
shape behind it, so the inventory will under-count asymmetric tables in exactly the games where
they are most common. Stated in the report rather than fixed.

## 8. How a straddle is detected once its poster has acted

Reversibility: runtime-reversible

Default: **three signals, all required.** A seat holding more than the declared blinds and its
own recorded actions predict. An unraised pot whose bet level is not the big blind. And, after
a raise, a minimum raise target disagreeing with the one the declared blinds and the recorded
raise-to amounts predict.

Options: three-signals | reconstruction-only | declare-a-blind-structure-on-the-query
Answer: [three-signals]

*Reconstruction only.* Catches every ante, including on a folded seat, and catches a straddler
who has not yet acted. It cannot catch a straddler who has called to the level, because that
seat holds exactly what an ordinary caller holds. This was the first draft of the contract and
an independent reviewer showed it would have frozen a fixture proving nothing.

*A declared blind structure on the query.* The clean answer, and it is the format change this
phase is scoped out of. It also has no producer: nothing in the repo can emit a straddled hand,
so the field would be set only by fixtures.

The cost the default accepts: three rules where one would be nicer, and a residual the phase
has to name. A straddle equal to the big blind is invisible to all three, and so is one in a
pot where the straddler has acted and no raise has happened, which cannot occur in a legal
preflop street but is expressible as a query.

## 9. Where the postflop enumeration's unattributed chips go

Reversibility: runtime-reversible

Default: **they become villain's earlier-street contribution**, so the two-seat pot reconciles.

Options: villain-prior-street | split-between-both-seats | a-third-non-acting-seat
Answer: [villain-prior-street]

`scripts/generate_postflop_fallback_report.py` builds its enumeration pot as
`100 + current_bet + hero_street_bet`, with the 100 belonging to nobody. The enumeration is
about hero's action given a legal-action set, and nothing in it reads the pot, so any
attribution that reconciles is behaviour-neutral for the enumeration and the choice is about
which one a reader finds least surprising.

Villain's prior street is the one that describes a real hand: money went in on the flop and the
turn is being played. Splitting it invents a hero contribution that contradicts the shape's own
`hero_street_bet`. A third seat changes the enumeration's table size.

The cost the default accepts: the enumeration's stated pot is now a claim about how the hand
got here, where before it was an arbitrary constant. If a reviewer reads it as data it is
misleading, so the report says it is a construction.

## 10. How the straddle and ante probes are rebuilt

Reversibility: runtime-reversible

Default: **both probes carry real per-seat forced chips.** The straddle probe seats a straddler
holding two big blinds it never acted for; the ante probe gives every seat an ante inside its
hand contribution.

Options: real-forced-chips | keep-the-overrides-and-exempt-the-probes | delete-the-probes
Answer: [real-forced-chips]

`scripts/generate_preflop_strategy_report.py` builds its straddle probe by overriding the bet
level alone and its ante probe by overriding the pot alone. Under decision 3 the ante probe
cannot be constructed at all, and under the deletion of the pot bound the straddle probe stops
refusing. These two probes are the only straddle and ante evidence the repo has, so exempting
or deleting them would leave the phase's headline detection with nothing showing it works
outside its own test file.

The cost the default accepts: a phase 05 report generator changes for a phase 13 reason, and
its two refusal lines will read slightly differently. Both are regenerated by a gate command,
so the diff is visible and reviewable.

## 11. Which all-in ceiling the repo keeps

Reversibility: runtime-reversible

Default: **hero's own contribution plus hero's stack**, which is what `DecisionAuditRecord`
already uses, expressed from the new field rather than by subtraction.

Options: audit-ceiling | chart-ceiling | leave-them-different
Answer: [audit-ceiling]

`PreflopChartStrategy._raise_amount` caps at the bet level plus hero's stack, which is too high
by exactly `to_call` for a hero who has already invested this street. The audit's is the correct
arithmetic and it is the one that already rejects an illegal amount, so moving the chart to it
is a bug fix rather than a preference. Leaving them different is what the Phase 11 contract
asserts is fine, and it is wrong.

The cost the default accepts: the chart can now return a smaller raise than it used to for a
hero who has posted a blind or already raised. That is the correct amount, and it is a
behaviour change with no corpus evidence behind it, so a fixture carries it.

## 12. How far the frozen-test migration reaches

Reversibility: runtime-reversible

Default: **every frozen test that constructs a `StrategyQuery`, asserts on its payload, or
asserts on its class docstring is migrated at stage 4**, mechanically where the change is a
field name and by rewriting the assertion to the claim it was making where the old behaviour is
now genuinely wrong.

Options: migrate-at-stage-4 | repair-at-stage-6 | migrate-only-what-goes-red
Answer: [migrate-at-stage-4]

*Repair at stage 6.* What phases 11 and 12 both did, not by choice: each discovered dozens of
red frozen tests after the freeze and paid a separate repair task with `tests/` re-opened. A
third time is a process failure rather than bad luck.

*Migrate only what goes red.* Cannot be done at stage 4, because nothing is red until the
implementation exists, which is the whole reason the previous two phases were caught out.

The cost the default accepts: stage 4 has to predict which frozen tests the change breaks
before the change exists, so it will over-touch some and still miss some. Missing one shows up
at stage 6 as a red gate, which is the outcome this default is trying to make rare rather than
impossible.

## 13. What the decision-audit schema version becomes

Reversibility: runtime-reversible

Default: **3.**

Options: 3 | leave-at-2
Answer: [3]

The payload gains per-seat contributions and a folded marker, and renames a key. Version 2
bytes and version 3 bytes would otherwise be indistinguishable at an unchanged version number,
which is `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS` recorded a second time in the
same repo.

The cost the default accepts: every committed decision audit regenerates, and any reader
holding version 2 bytes has to know what changed. The audit packet says.

## 14. Whether the per-seat record carries an all-in marker

Reversibility: runtime-reversible

Default: **yes, an `all_in` marker beside the folded marker**, matching the fourth field
`PlayerState` already carries.

Options: carry-all_in | derive-from-a-zero-stack | omit-it
Answer: [carry-all_in]

This is the phase 12 handoff the contract asks this phase to answer. `SeatAction` forbids an
amount on a call, so a seat that called all-in for less is recorded identically to a full
caller, and phase 12 deferred that to phase 13 by name. The marker does not close it inside the
spot key, which stays out of scope, but it makes the situation visible to the strategy and
measurable in the report, which is what turns a restatement into a work list.

*Derive from a zero stack.* Almost right and wrong at the edges: a seat all-in for its exact
stack holds zero, but so does a seat that was already at zero when the hand began, and a seat
all-in on an earlier street has a zero stack with no all-in this street.

*Omit it.* Leaves the phase 12 handoff answered with "we did not look", which the contract
forbids in as many words.

The cost the default accepts: a fourth per-seat field, and one more thing every producer must
supply correctly. `PlayerState.all_in` exists at both live producers, so the cost falls on the
report producers.

## 15. What `min_raise_target` is checked against

Reversibility: runtime-reversible

Default: **the strategy reads it as a signal and `StrategyQuery` does not validate it beyond
the existing positivity rule.** A disagreement produces a refusal, never a silent answer.

Options: signal-only | validate-in-the-query | validate-and-signal
Answer: [signal-only]

Decision 8 puts the whole raised-pot straddle case on this field, and the field is
producer-supplied and today checked only for being positive. The two live producers derive it
from the engine, but the report and fixture producers compute it by hand, and those are exactly
the producers this phase rewrites. So a producer bug becomes a poker claim: the strategy reports
a straddle that is not there.

*Validate in the query.* Turns that class of producer bug into a construction error, which is
what decision 3 does for the pot and is tempting for the same reason. It cannot be done: the
correct minimum raise is only reconstructable when the query carries the recorded raise-to
amounts, which it does preflop and does not postflop, so the rule would reject every legitimate
postflop query.

The cost the default accepts, named because it is the phase's sharpest false-positive channel:
a report producer that computes `min_raise_target` carelessly makes the strategy claim a
straddle. The mitigation is that both rewritten producers derive it from the same reconstruction
the detector uses, and a test asserts an unstraddled pot at every price the probes cover reports
no straddle.

## 16. What the new refusal codes are called

Reversibility: runtime-reversible

Default: **`preflop-chart:a-live-seat-is-shorter-than-hero`,
`preflop-chart:pot-holds-a-straddle`, and `preflop-chart:pot-holds-an-ante`.**
`preflop-chart:blind-structure-not-representable` is retired, because both of its branches
become one of the two new codes and it would otherwise have no trigger left.

Options: named-above | keep-one-blind-structure-code | reuse-table-is-not-one-flat-stack-depth
Answer: [named-above]

These strings are stamped into the committed refusal inventories, quoted in backlog entries,
and are the vocabulary a human reads coverage in, so they are chosen here rather than in code.
They follow the existing house style at `preflop_chart.py`: a plain-English phrase, hyphenated,
saying what is wrong rather than which check fired.

Retiring `blind-structure-not-representable` contradicts the contract's regression expectation
that every existing refusal code stays reachable, so the phase either keeps it as the code for a
pot that holds forced money it cannot classify, or amends that expectation. The default is to
keep it for exactly that residual, which decision 8 says has to be named anyway.

The cost the default accepts: three more codes in an inventory that already has thirteen, and a
grouping question for whoever reads the inventory next.
