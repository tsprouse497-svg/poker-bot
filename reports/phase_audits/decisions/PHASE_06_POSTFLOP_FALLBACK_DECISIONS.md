# Phase 06 judgment calls

These are the domain choices no chart in this repo can settle, because there is no
postflop chart and there will not be one in v1.
They are recorded before implementation so that what the bot does postflop is a
decision somebody made rather than whatever the first draft happened to do.

Every item carries a default.
Defaults stand unless changed, so answering nothing is a valid answer.
Answer by replacing the bracketed value on the `Answer:` line.

Every item carries a reversibility class, which is what the loop driver reads at
stage 2 to decide whether it must stop for a human.

- `runtime-reversible`: the choice only changes behavior at query time, so a later
  edit changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact or fixture
  that later phases are then measured against. The loop halts until a human answers.

Status: every item below is `runtime-reversible`, because this phase writes no
committed data and no fixture.
Nothing here is frozen: each one is a rule in a Python module that a later edit
changes, and `verification/loop_policy.yml` marks Phase 06 `auto_advance: true` for
exactly that reason.
So the loop proceeded on the defaults and reports them at closeout rather than
blocking.
Taylor can overrule any of them after reading the audit packet, and the cost of
doing so is one edit plus a gate run, not a regenerated artifact.

The one thing worth reading before Phase 07 starts is item 4, because it decides
what a simulated hand actually looks like and therefore what a comparison report
can honestly claim.

## 1. What the fallback does when facing a bet

Reversibility: runtime-reversible

The bot has no postflop range model, no board texture model, and no read.
Three rules are available, and only one of them rests on a fact.

Default: fold, with a single exception on the river when hero's hand beats every
holding a villain could possibly have, which is decidable by enumerating the unseen
deck against a complete board.
Everything else needs a number the repo cannot source.
A pot-odds rule needs an equity estimate, an equity estimate needs a range to be
against, and a made-hand threshold ("call top pair or better") is a number somebody
made up and then tests would freeze.

If wrong: the bot folds to postflop aggression far more than any real player should,
so it loses money to anyone who bets. That is loudly bad rather than quietly bad,
which is the point, and it is exactly why the phase title says fallback.

Options: fold-except-river-unbeatable | pure-check-fold | pot-odds-and-thresholds
Answer: [fold-except-river-unbeatable]

## 2. Whether a hand that can only be tied calls

Reversibility: runtime-reversible

The unbeatable test has two possible bars.
The strict one is "no possible holding beats or ties hero", so calling wins the pot
with certainty.
The loose one is "no possible holding beats hero", which admits hands where the best
villain can hold is a chop.

Default: strict.
A guaranteed chop pays a full call to win half a pot, so whether calling is right
depends on the price, and the price is where this phase has no oracle.
Folding there is wrong in most real spots and costs almost nothing in practice,
because the boards where hero's hand can be tied but not beaten are rare.

If wrong: the bot folds a small number of river spots it should call. The cases are
countable and the report shows them, so a later change is measurable rather than
speculative.

Options: strict-no-ties | allow-guaranteed-chops
Answer: [strict-no-ties]

## 3. Why the exception is the river only

Reversibility: runtime-reversible

The same claim can be made on the flop and the turn, but it means something
stronger there: not "no holding beats me now" but "no holding beats me after any
runout".
That is still enumerable, and it is still a fact rather than a read.

Default: river only.
Two reasons, and the honest one is first.
On the flop the enumeration is 903 runouts against 990 villain holdings for a
single decision, which is too slow to run inside an exhaustive test sweep, and a
sampled version of it would turn the fact back into a guess.
The second is that almost nothing qualifies: on the flop only a hand no runout can
catch, which is essentially the top straight flush, so the rule would fire close to
never while costing the most to compute.

If wrong: the bot folds turn and flop hands that cannot lose. Same shape of loss as
item 2, and `POSTFLOP-UNBEATABLE-EARLIER-STREETS` records it.

Options: river-only | extend-to-turn | extend-to-flop-and-turn
Answer: [river-only]

## 4. Never betting or raising, and what that makes a simulated hand

Reversibility: runtime-reversible

This is the item with consequences outside this phase.

Default: the fallback never bets and never raises, at any street.
A bet needs a size, a size needs a source, and the repo's only sizing source is the
preflop solver export.
Inventing a postflop sizing scheme would produce a bot whose postflop play looks
deliberate and is not, which is worse than one that visibly declines to act.

What that means concretely: against another copy of itself, every postflop street
checks through, so a hand is decided preflop and then shown down. Phase 07 can
therefore measure preflop decisions with equity realized at showdown, and cannot
make any claim about postflop play, because there is none to measure. That has to
be said out loud in Phase 07's own contract rather than discovered from a report.

If wrong: nothing breaks and no test changes shape, but every Phase 07 baseline
computed before a real postflop strategy exists is a preflop baseline wearing a
full-hand label.

Options: never-aggress | bet-a-fixed-fraction-of-pot | you supply postflop sizings
Answer: [never-aggress]

## 5. What the composite does with a preflop chart refusal

Reversibility: runtime-reversible

Phase 05's strategy refuses whenever the committed charts are silent: an uncovered
spot, a depth that is not exactly 100bb, a straddled pot, a second-orbit spot.
The composite could quietly hand those to the fallback and the simulation would
never stop.

Default: the refusal passes through unchanged, carrying its original reason code.
Covering it would erase the coverage signal Phases 04 and 05 were built to produce,
and it is the specific thing `AGENTS.md` names as forbidden: no heuristic guessing
for missing preflop chart spots. A refusal that becomes a check is a guess with the
evidence deleted.

If wrong: Phase 07's simulator has to handle a refusal rather than assuming a
decision always arrives, which is more work there and the correct place for it.

Options: pass-through | fall-back-to-passive | refuse-the-whole-hand
Answer: [pass-through]

## 6. Whether the fallback may answer a preflop query directly

Reversibility: runtime-reversible

Separate from item 5.
Item 5 is about the composite; this is about what happens if somebody hands a
preflop query to the fallback itself.

Default: refuse, with its own code.
A preflop spot always has either a chart answer or a chart gap, and the fallback is
neither. Letting it answer would give the repo a second, silent preflop strategy
reachable by mistake.

If wrong: nothing, beyond a caller having to route correctly, which the composite
already does.

Options: refuse | answer-passively
Answer: [refuse]

## 7. What the unseen deck means when more than one villain remains

Reversibility: runtime-reversible

Not really a choice, recorded because it looks like one.

The unbeatable test enumerates every two-card combination from the cards hero cannot
see: the full deck minus hero's two cards and the five board cards.
In a multiway pot that set is a superset of what any single villain can hold, and it
ignores that folded players took cards out of it.
So the test is conservative in the only direction that matters: it can refuse to
call a hand that was in fact unbeatable, and it can never call one that was
beatable.

Default: enumerate the full unseen deck, and do not try to narrow it by seat count
or by folded players.

Options: full-unseen-deck | narrow-by-seat-count
Answer: [full-unseen-deck]
