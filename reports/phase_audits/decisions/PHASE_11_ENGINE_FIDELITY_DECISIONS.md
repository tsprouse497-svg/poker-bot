# Phase 11 judgment calls

These are the choices that decide what "fixed" means for six defects that were already
diagnosed. The diagnosis is not in question anywhere below; what is in question is how far
each fix reaches, and what it is allowed to break on the way.

Every item carries a reversibility class, which the loop driver reads at stage 2 to decide
whether it must stop for a human.

- `runtime-reversible`: the choice only changes behaviour at query time, so a later edit
  changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact that every later phase
  is then measured against. The loop halts until a human answers.

**Every item here is `runtime-reversible`, and that needs saying out loud rather than being
read as evasion.** This phase commits no data at all - no chart, no artifact, no sample, no
export, no new fixture - which is exactly why `verification/loop_policy.yml` grants it
`auto_advance: true`. There is nothing for a choice to be frozen into. The one place that
came close was a criterion in the stage-1 draft requiring a committed hand fixture carrying
a free fold; the stage-1 review killed it for this reason and the hand is now built inside
the test.

**One call is worth a human's eyes anyway, and the loop will not stop for it: decision 3,
the reopening rule.** It is a poker rule, not an arithmetic identity. The repo has no oracle
for it - no rulebook is checked in, and the corpus is not consulted for rules - so the only
check on it is somebody who knows how a real room rules the spot. It is written in chips
below so that check is possible. If it is wrong, every later measurement that replays a hand
inherits the error, which is the same shape of damage a frozen artifact would do, arriving by
a different road.

## What was measured first

Every claim below was reproduced against this branch's code rather than taken from
`backlog.yml`, because a decision written against a remembered defect is a decision about
the wrong thing.

### The reopening bug, in chips

Four seats, blinds irrelevant, a postflop street. Stacks 100 / 15 / 21 / 100. Seat 0 bets 10,
which sets the current bet to 10 and the minimum raise to 10. Seat 1 moves all-in for 15 - an
increment of 5, half a raise - and seat 0 is barred from raising, correctly. Seat 2 then moves
all-in for 21 - an increment of 6 over seat 1, also short on its own.

The two short all-ins have together advanced the bet from 10 to 21, an increment of 11 against
a minimum raise of 10. Today seat 0's legal actions are `fold, call`. Seat 3, who had not yet
acted, keeps `fold, call, raise`.

`TurnState.apply` computes `full_raise = new_round.current_bet - previous_bet >=
previous_min_raise`, so each all-in is measured against the bet level immediately before it
and never against the level of the last full raise. Nothing accumulates.

### The free fold

A postflop street with no bet in it. `BettingRoundState.legal_actions` returns
`('check', 'bet')`, and applying a fold raises `fold is not legal for seat 0`. Every real
history containing a surrendered river or a timed-out check therefore fails replay at the
action, not at the settlement.

### The all-in ceiling

A query with `street_bet` 20, `to_call` 20, stack 100. Hero's own contribution to the street
is 0, so hero's all-in raise target is 100. `DecisionAuditRecord` accepts a raise to 120 and
rejects 121. The ceiling is loose by exactly `to_call`, as filed.

### What the `street_bet` fix actually buys

`scripts/generate_strategy_query_report.py` runs the reference check-fold strategy, which
never reads `street_bet`, so the report's own counts do not move at all - only the bytes of
`latest_decision_audit.jsonl`, which carries the field. The stage-1 draft said the report's
refusals change; they cannot, because it has none.

Fed the same decision points, the chart does move. The small blind's preflop decision in
`phase02-heads-up-showdown` (hero contribution 5, level 10, price to call 5):

| `street_bet` passed | chart outcome |
| --- | --- |
| 5, hero's own contribution - today | `preflop-chart:blind-structure-not-representable` |
| 10, the street's level - corrected | `preflop-chart:lookup:no-artifact-for-table-size` |

The second is the true miss: a two-handed table against a six-handed chart. The first is the
chart mis-deriving hero's starting stack from a field it read the wrong way and blaming the
blinds for it.

The same measurement kills a claim the stage-1 draft made about the new guard. Rejecting a
query whose `street_bet` is below its `to_call` catches a producer passing hero's contribution
only when hero has put in less than half the current level. The heads-up small blind has put
in exactly half - 5 of 10 - so the guard passes the very query that motivated it. Both the
contract and the criterion were corrected before this record was written.

## 1. Where a fold becomes legal when checking is free

Reversibility: runtime-reversible

The engine is one definition of legality and the replayer is another view of it. The defect
can be closed in either place, and the choice decides whether the bot's own decision space
grows.

Default: **`legal-actions-everywhere`.** `BettingRoundState.legal_actions` offers `fold` in
every state where the seat to act has any legal action at all, free or not. `StrategyQuery`
loses its assertion that `check` and `fold` are never both legal, because the engine now
produces that set and a query that refuses to describe an engine-legal state is a query that
lies about the game.

Options: legal-actions-everywhere | replay-accepts-only | history-kind-for-a-free-fold
Answer: [legal-actions-everywhere]

The alternatives, so the choice is made against them rather than against the default alone.

*Replay accepts only.* Special-case a recorded fold inside `replay.py` without touching
`legal_actions`. Smallest possible diff, no change to what any strategy sees, and it creates a
second definition of what is legal - which is the identical shape of defect this phase is
fixing in `street_bet`, where two readings of one thing lived in two files. Rejected on that
ground rather than on size.

*A history action kind of its own.* Record a free fold as a distinct `HistoryActionKind` so
the schema says which kind of fold it was. It buys a distinction nobody has asked for, and it
puts the burden on every ingester to classify a fold it may not be able to classify.

The cost the default accepts: every strategy in this repo now sees `fold` on offer in free
spots, including spots where folding is strictly dominated. Decision 2 is what pays it.

## 2. What stops a strategy folding when checking is free

Reversibility: runtime-reversible

Making an action legal and making a bot take it are different things, and only the first is
wanted. The question is whether the second needs code.

Default: **`prove-it-by-enumeration`.** No guard is added anywhere. The property - that no
strategy shipped in this repo ever returns `fold` when `check` is legal - is asserted over
the Phase 06 postflop enumeration and over the preflop chart's answers on every committed
spot. A guard is added only if that proof fails, and if it fails the failure is the finding.

Options: prove-it-by-enumeration | guard-in-each-strategy | strip-fold-from-the-query
Answer: [prove-it-by-enumeration]

*A guard in each strategy.* An explicit "never fold when check is legal" branch in the chart
strategy and in the fallback. Certain, and it is dead code the day it is written unless the
proof would have failed, in which case it hides the real finding behind a correction.

*Strip fold from the query when check is legal.* Keep the engine honest and have the query
present a filtered set. This is the query lying about the game again, one level up, and it
would make `DecisionAuditRecord` unable to validate a legal fold that a real history contains.

The open risk, named rather than assumed away: the preflop chart returns a sampled action from
artifact weights, and whether any committed spot can yield `fold` where `check` is legal has
not been established. The proof is where that gets answered. If a committed spot can, this
phase reports it and does not paper over it - a chart cell that folds a free option is an
artifact finding, and Phase 14 owns the artifact.

## 3. How far betting reopens when short all-ins accumulate

Reversibility: runtime-reversible

**This is the call worth a human's eyes.** It is a poker rule and the repo has no oracle for
it.

Default: **`accumulate-since-the-last-full-raise`.** Raising is reopened for a seat that has
already acted when the current bet has advanced, since the last full bet or raise, by at
least the minimum raise in force at that time. A single short all-in that does not reach that
bar does not reopen - which is today's behaviour and stays. A full bet or raise resets the
level the accumulation is measured from.

In the worked example above: the last full aggression set the level to 10 with a minimum raise
of 10, the two short all-ins carried the bet to 21, and 21 minus 10 is 11, which clears 10.
Seat 0 may raise again. With seat 2 all-in for 20 instead of 21, the accumulation is exactly
10 and still clears; at 19 it is 9 and does not, so the boundary sits between 19 and 20 and
both sides get a test.

A reopened seat's raise still has to meet the minimum raise the engine already carries, which
under-raises never advance. So the reopened seat must raise to at least 31, not to 22.

Options: accumulate-since-the-last-full-raise | keep-the-current-strict-rule |
reopen-on-any-all-in
Answer: [accumulate-since-the-last-full-raise]

*Keep the current strict rule.* Fail-closed and simple, and it is why the item was filed:
it is stricter than the live rule, so a real history where a room correctly reopened betting
is a history this repo cannot replay. That is the same class of damage as the free fold.

*Reopen on any all-in.* Simplest of all and plainly wrong. A one-chip all-in would hand a
seat that already acted a fresh raise, which is the abuse the under-raise rule exists to stop.

What a human should check, in one sentence: in a real room, when two players move all-in for
short amounts one after the other and their two increments together add up to a full raise,
does the player who already acted get to raise again? The default says yes. If the answer is
no, decision 3 flips to `keep-the-current-strict-rule`, the backlog entry is restated as a
deliberate difference rather than a defect, and nothing else in this phase changes.

## 4. Whether `street_bet` is documented or renamed

Reversibility: runtime-reversible

The contract already rules which reading is meant - the street's current bet level, because
that is what Phase 04, 05 and 06 code and tests use. What is open is whether the name survives.

Default: **`document-and-guard`.** A docstring on the field naming the meaning, the
`street_bet >= to_call` guard, and the one wrong producer corrected. The name stays.

Options: document-and-guard | rename-to-current-bet | carry-both-fields
Answer: [document-and-guard]

*Rename to `current_bet`.* The honest fix. `street_bet` reads as "hero's bet this street",
which is precisely the wrong reading, and the engine already calls this quantity `current_bet`
on `BettingRoundState`, so the rename would leave one vocabulary instead of two. Its cost is
the blast radius: eight producers, the serialized audit payload key and therefore a
`DECISION_AUDIT_SCHEMA_VERSION` bump, the Phase 03 contract text, and frozen tests in four
completed phases. A fidelity phase reaching into four completed phases' frozen tests to change
a name is a bigger act than any of its six fixes, and it would arrive in the same commits as
five behaviour changes, where a review cannot separate them.

*Carry both fields.* Add `hero_street_bet` beside it. Two fields that must agree is a third
reading waiting to happen.

The cost the default accepts: the name still reads wrong, and the docstring is the only thing
standing between a future producer and the same mistake. Filed as
`STRATEGY-QUERY-STREET-BET-NAME` against proposed phase 13, which already opens the query and
the Phase 03 contract, so the rename is a task somebody can pick up rather than a regret.
Measured limit on the guard, from
the section above: it does not catch a hero who has contributed exactly half the level, which
is the heads-up small blind, so the producer audit and not the guard is what closes the defect.

## 5. Whether the tightened all-in ceiling grandfathers anything

Reversibility: runtime-reversible

Default: **`tighten-and-assert-nothing-breaks`.** The ceiling becomes
`(street_bet - to_call) + stack`, and the phase asserts that every record in the committed
decision audits still validates and that every shipped strategy's raise still passes.

Options: tighten-and-assert-nothing-breaks | tighten-with-a-grandfather-clause
Answer: [tighten-and-assert-nothing-breaks]

*A grandfather clause.* Accept the old ceiling for records written under an earlier schema
version. There is nothing to grandfather - the preflop chart caps its own raise at
`street_bet + stack`, which under the corrected reading is exactly its all-in target - so the
clause would be a permanently accepted looseness bought against a risk that was measured at
zero.

This decision depends on decision 4. The arithmetic `(street_bet - to_call) + stack` is only
correct under the level reading; if decision 4 ever flips the field's meaning, this ceiling
flips with it, and the two must move together.

## 6. What the fallback's fail-closed branch does

Reversibility: runtime-reversible

Default: **`fold-then-refuse`.** `_PASSIVE_ORDER` stops at `fold`. When `fold` is legal the
branch folds; when it is not, it refuses. It never calls.

Options: fold-then-refuse | refuse-always | raise-an-exception
Answer: [fold-then-refuse]

*Refuse always.* Arguably cleaner: the branch is unreachable from the engine's own
`legal_actions`, so any arrival is a bug and a refusal is the loudest honest answer. It gives
up a legal, free, conservative action in the case where folding is available, for the sake of
being loud, and the module's whole posture is to take the conservative legal action when one
exists.

*Raise an exception.* Turns an unreachable branch into a crash in a simulation that may be
thousands of hands deep, which is worse than a refusal that gets counted.

Note the interaction with decision 1: once `fold` is legal wherever a seat can act, the
"fold is not available" half of this branch becomes even harder to reach, and the refusal
survives only for a legal-action set carrying no fold at all - `("raise",)`. Both halves get a
direct unit test built from a contract-valid query rather than from an engine state, because
neither is reachable from the engine and that is exactly why neither was covered.

## 7. How Phase 06's "never refuses postflop" claim is amended

Reversibility: runtime-reversible

Default: **`restate-as-from-engine-legal-sets`.** The criterion becomes what its enumeration
always actually proved: the fallback never refuses from any legal-action set the engine can
produce. The enumeration still finds zero postflop refusals and the gate still asserts it.

Options: restate-as-from-engine-legal-sets | delete-the-claim | make-the-branch-always-fold
Answer: [restate-as-from-engine-legal-sets]

*Delete the claim.* Loses a property the gate genuinely proves.

*Make the branch always fold.* Impossible against a legal-action set of `("raise",)`, which is
the case decision 6 exists for.

## 8. Whether this phase amends the upstream contracts or files them

Reversibility: runtime-reversible

Default: **`amend-in-this-phase`.** Every completed contract whose acceptance criteria,
forbidden shortcuts, or regression expectations are contradicted by one of these six fixes is
amended here, in `contract-update` mode, before any test is frozen against it. The known one
is Phase 03's reopening criterion; the read is not finished until the amendment stage, and
contracts that are merely made more true are left alone and recorded as read-and-left.

Options: amend-in-this-phase | file-each-as-its-own-contract-update-task
Answer: [amend-in-this-phase]

*File each separately.* Keeps this phase's diff smaller, and leaves a window in which the code
and the contract governing it disagree, adjudicated by whoever reads them next.
`docs/V2_ROADMAP.md` says phase 11 touches the Phase 01, 02, 03 and 06 contracts, so the work
was scoped here from the start.

The mechanical cost, named because it bit Phase 10: the loop has no stage for an upstream
amendment. Stage 1 is the contract stage and stage 4 is tests, so the amendment lands as its
own `contract-update` task with the lane pointer rewound, exactly as Phase 10's S4b did.

## 9. What the phase does about the committed numbers these fixes move

Reversibility: runtime-reversible

Default: **`name-and-defer`.** The phase names every committed number these fixes move and
recomputes none of them. Regenerated reports under `reports/active/` move as a mechanical
consequence of running their gate commands, which is unavoidable and is not re-measurement;
the findings built on them - Phase 08's agreement rates, the refusal inventory's rows - are
not re-derived, re-argued, or re-baselined here.

Options: name-and-defer | recompute-here | recompute-and-rebaseline
Answer: [name-and-defer]

*Recompute here.* Tempting, because the numbers are now known to be stale. It would put a
fix phase in the position of grading its own fixes, and it would arrive in the same commits as
the fixes, where nobody can tell a moved number from a mistaken one.

The cost the default accepts, stated plainly: this phase closes with several published numbers
known to be measured through a corrected instrument and not re-measured. The contract requires
the report to list them with the phase that owns each re-measurement, which is the most a
fix-only phase can honestly do. Filed as `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` against
proposed phase 12, which already re-runs the comparison for its own reasons, so the deferral
is an entry somebody will read rather than a paragraph in a decision record.
