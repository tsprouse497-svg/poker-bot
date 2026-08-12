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

**Stage 8 update, 2026-08-12.** Items 2 and 3 came back and were re-ruled by Taylor
after the domain review measured them. That is what deferring a `runtime-reversible`
call costs: the loop proceeds, the gate goes green around the default, and the
correction arrives at review with tests and a mutation canary already defending the
wrong rule. It is still the right trade for a rule that lives in a Python module -
the fix was one contract-update and one edit, not a regenerated artifact - but the
two re-rulings are the evidence that "reversible" means cheap to reverse and not
unlikely to need reversing.

## 1. What the fallback does when facing a bet

Reversibility: runtime-reversible

The bot has no postflop range model, no board texture model, and no read.
Three rules are available, and only one of them rests on a fact.

Default: fold, with a single exception when no holding a villain could possibly have
beats hero, whatever cards are still to come, which is decidable by enumerating the
unseen deck.
Item 3 decides which streets that exception reaches and item 2 decides where the bar
sits; this item only decides that the exception is a fact and not a price.
Everything else needs a number the repo cannot source.
A pot-odds rule needs an equity estimate, an equity estimate needs a range to be
against, and a made-hand threshold ("call top pair or better") is a number somebody
made up and then tests would freeze.

If wrong: the bot folds to postflop aggression far more than any real player should,
so it loses money to anyone who bets. That is loudly bad rather than quietly bad,
which is the point, and it is exactly why the phase title says fallback.

Options: fold-except-unbeatable | pure-check-fold | pot-odds-and-thresholds
Answer: [fold-except-unbeatable]

Renamed from `fold-except-river-unbeatable` at stage 8, because item 3 no longer
restricts the exception to the river. The ruling itself is unchanged.

## 2. Whether a hand that can only be tied calls

Reversibility: runtime-reversible

**Re-ruled at stage 8 to `allow-guaranteed-chops`. The original ruling and the reason
given for it are below, because the reason was wrong and that is the part worth
keeping.**

The unbeatable test has two possible bars.
The strict one is "no possible holding beats or ties hero", so calling wins the pot
with certainty.
The loose one is "no possible holding beats hero", which admits hands where the best
villain can hold is a chop.

Originally ruled: strict, on this ground -

> A guaranteed chop pays a full call to win half a pot, so whether calling is right
> depends on the price, and the price is where this phase has no oracle.

That sentence is false, and it was the whole ruling.
Calling a guaranteed chop does not depend on the price, because the pot that gets
chopped contains the villain's bet and the dead money as well as hero's call.
Facing a bet of B into a pot of P that already contains B, a hand no holding can beat
returns at least (P + B) / 2 for a payment of B, so the call gains at least
(P - B) / 2, and P exceeds B always because a postflop pot holds the preflop money.
Multiway does not change the sign: chopping three ways returns P/3 + B for a payment
of B.

In the exact state the committed report enumerates - pot 120, of which the villain's
bet is 20, and 20 to call - folding gives up 50 chips.
Two of the five worked examples are that case, and one of them is a royal flush on
the board, where every player at the table has the nuts and calling is free money
that no human declines.

So the loose bar is not the looser of two defensible rules.
It is the correct one, and it is correct for the reason this phase already gives for
wanting the exception at all: it invests only where the investment cannot lose, and a
hand that can only be chopped cannot lose.
"Strict" was doing the opposite of what its name promised.

If wrong: it is not wrong. The arithmetic is three lines and needs no oracle. What the
change costs is that the bot now puts money in on more river and turn spots, all of
them spots where its share of the pot is guaranteed to at least return the call.

Options: strict-no-ties | allow-guaranteed-chops
Answer: [allow-guaranteed-chops]

Ruled by Taylor on 2026-08-12, on the stage 8 domain review.
The original answer was accepted on a qualitative claim nobody checked, including the
session that wrote this list.

## 3. Which streets the exception covers

Reversibility: runtime-reversible

**Re-ruled at stage 8 to `extend-to-turn`. The original ruling was `river-only`, on a
cost that only the flop actually carries, and on arithmetic that was a card off.**

The same claim can be made on the flop and the turn, but it means something
stronger there: not "no holding beats me now" but "no holding beats me after any
runout".
That is still enumerable, and it is still a fact rather than a read.

Originally ruled: river only, on this ground -

> On the flop the enumeration is 903 runouts against 990 villain holdings for a
> single decision, which is too slow to run inside an exhaustive test sweep.

Both numbers are the river's own, shifted.
On the flop hero can see five cards, so the unseen deck is 47 and not 45: fixing a
villain holding first gives C(47,2) = 1,081 holdings, each against C(45,2) = 990
runouts. 903 is C(43,2), and 990 is the river count, so two river-shaped figures got
multiplied together.

Measured on this machine, at roughly 78 microseconds per seven-card evaluation:

| street | villain holdings | runouts | evaluations | one decision |
|---|---|---|---|---|
| river | 990 | 1 | 990 | 0.09 s |
| turn | 990 | 46 rivers | 45,540 | 3.6 s |
| flop | 1,081 | 990 | 1,070,190 | 83 s |

The conclusion survives for the flop and does not survive for the turn.
A flop decision is roughly a thousand river checks and has no place in an exhaustive
sweep. A turn decision is roughly forty-six of them, and the turn claim decomposes
into exactly that - hero is unbeatable after every river iff hero is unbeatable on
each of the 46 completed boards - so it reuses the river test and its memo rather than
needing a second enumeration.

The second original reason, that almost nothing qualifies, is true on the flop and
overstated on the turn: a made straight flush, quads above the board's reach, and a
nut flush on a rainbow-paired-free board all qualify on the turn.

Default now: turn and river. The flop stays out, and
`POSTFLOP-UNBEATABLE-EARLIER-STREETS` narrows to the flop alone rather than covering
both streets under one cost objection that only one of them earns.

If wrong: the gate gets slower, which is the only price. A turn decision that the
sweep enumerates twice costs 3.6 seconds the first time and nothing afterwards, and
`check_gate_bite` re-runs the phase command once per mutation.

Options: river-only | extend-to-turn | extend-to-flop-and-turn
Answer: [extend-to-turn]

Ruled by Taylor on 2026-08-12, on the stage 8 domain review.

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
see: the full deck minus hero's two cards and the board.
On the river that is 45 cards and 990 holdings. On the turn the same count is taken
against each of the 46 possible river cards, so a river card hero might be dealt is
never also a card a villain holds.
In a multiway pot that set is a superset of what any single villain can hold, and it
ignores that folded players took cards out of it.
So the test is conservative in the only direction that matters: it can refuse to
call a hand that was in fact unbeatable, and it can never call one that was
beatable.

Default: enumerate the full unseen deck, and do not try to narrow it by seat count
or by folded players.

Options: full-unseen-deck | narrow-by-seat-count
Answer: [full-unseen-deck]
