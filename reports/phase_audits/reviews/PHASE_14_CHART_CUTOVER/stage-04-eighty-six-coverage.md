# Phase 14 stage 4: what the 86 actually cover

Written 2026-08-25, before the ruling that follows it, because the ruling was made conditional on
this number existing. The disposition note put the 86 forward without ever measuring what fraction
of real decisions they answer; the figure was inferred from a subtraction and carried as an upper
bound. It is measured here.

Both walks are written fresh against the committed export and the committed sample. Neither imports
`chart_derivation`, which still does not exist, and neither reuses the stage-4 scratch scripts.

## Method

Two predicates, applied to the same two objects.

**Ruled (history).** Keep a node when at most one *opponent* has voluntarily put money in beyond the
blinds. Blinds are forced and do not count; an opener who later folds to a three-bet still counts,
which is the strict reading the predicate-change review settled and did not reopen.

**Terminal-clean (subtree).** Keep a node when at most two players are still live. This is the
restatement the review demanded - the product approximation bites at terminals and a node's strategy
is backward-induced over every terminal below it, so at most two live players is exactly the
condition under which every terminal below the node is heads-up and priced exactly.

**The 86 are the conjunction, and that is the ruling.** Terminal-clean alone is not the rule: it
selects 5,472, admitting 5,386 nodes that are heads-up from here on but were reached through a cold
call and therefore arrive carrying a range the same defect distorted. The ruled predicate is both
clauses at once, which is why the intersection rather than either count is what gets committed.

Over the export the walk descends from the root carrying, per seat, whether it has folded and
whether it has voluntarily invested. Over the corpus the same two counters are carried across each
hand's preflop actions, skipping the two blind posts, and evaluated at each decision point before
the action is applied. The corpus walk's decision-point total is cross-checked against
`replay_hand`'s own `DecisionPoint` stream.

## The export: the prior counts reproduce exactly

| set | nodes |
|---|---|
| the export | 38,828 |
| ruled predicate | 110 |
| terminal-clean | 5,472 |
| both - **the 86** | 86 |
| ruled but not clean - **the 24** | 24 |

All four match the predicate-change review to the node. The 24 are 1 LJ, 3 HJ, 5 CO, 7 BTN and 8 SB
spots and no BB spot, which is the mechanism visible in the arithmetic: the big blind closes the
action, so every one of its 20 spots is clean and no other seat's opening spot is. Four of the five
opens are in the 24; the small blind's open survives because by the time it acts only it and the big
blind are live.

## The corpus: 563 of 3,048, not "at most 568"

| set | corpus preflop decisions | share |
|---|---|---|
| all preflop decision points | 3,048 | 100% |
| ruled predicate - the 110 | 2,795 | 91.7% |
| ruled but not clean - **the 24** | 2,232 | 73.2% |
| both - **the 86** | **563** | **18.5%** |
| multiway, refused under every option | 253 | 8.3% |

By opponents already invested: 1,629 decisions face nobody in the pot yet (53.4%), 1,166 face
exactly one (38.3%), 243 face two and 10 face three or more.

The 2,232 reproduces the predicate-change review exactly. The 563 is new and it is the number the
ruling was waiting on.

## The denominator was wrong by six, in every stage-4 document

The committed sample holds **499 hands and 3,048 preflop decision points**, confirmed two ways: by
this walk and by counting `replay_hand`'s preflop `DecisionPoint`s. Every stage-4 document says
3,054. The difference is one excluded hand - `pluribus/41b/204`, dropped because its finishing
stacks are fractional - whose six preflop decisions were counted into the denominator but not into
the sample. The ExecPlan already used 3,048 for the limped-pot count, so the two figures have been
contradicting each other inside this phase since the cold-call verification.

Nothing concluded on the old denominator changes: 2,232 of 3,048 is 73.2 percent against the 73
percent recorded, and the multiway share is 8.3 percent either way. The number is corrected wherever
it appears rather than left as a footnote, because a later phase reading 3,054 out of this phase's
contract would measure against a corpus that does not exist.

## What the 86 contain, for the rulings that rest on it

Measured over the retained set, because decisions 5, 6 and 10 were each ruled on a count taken over
a set this phase no longer commits.

- **Depth.** 1 spot at four prior actions, 10 at five, 30 at six, 30 at seven, 15 at eight. By prior
  *aggressive* actions the same shape: 1 open, 10, 30, 30 and 15 facing one, two, three and four.
- **Seats.** 15 LJ, 14 HJ, 13 CO, 12 BTN, 12 SB, 20 BB.
- **Action menus.** 50 fold/call, 20 fold/call/raise/jam, 15 fold/call/jam, 1 fold/raise/jam.
- **Arriving reach.** 11 at full reach, against 35 in the 110. The minimum over the 86 is 2.62
  percent, so all 86 still clear the retired 2 percent floor and conjoining it would again change
  nothing.
- **Decision 6's premise moves.** 21 of the 86 offer a named raise and a jam and 15 offer a jam with
  no named raise, against the 35 and the 5.0 percent jam volume the ruling was written on. The
  ruling has to be restated against 21 or it is resting on a set that is not being committed.
- **Decision 5's premise moves further.** With 11 of 86 at full reach rather than 35 of 110, a
  per-cell reach field distinguishes more rather than less, so the amendment holding it on
  prospective grounds now has a present reason as well.

## The one open exposure this measurement does not close

The single fold/raise/jam spot in the 86 is the small blind's open, and it is the only opening range
the chart will hold. `SOLVE-CAPTURE-NEEDS-A-POT-ENTRY-RATE-CHECK` remains the right check to build,
but with four of five opens refused the pot-entry rate this chart produces is no longer comparable
to the corpus's at all: the bot cannot enter a pot from LJ, HJ, CO or BTN. The closing measurement
must say that in those terms rather than publishing a rate against a corpus figure it cannot be
compared to.

---

## Addendum, same day: the retired chart is not a subset of the 86

Found while reviewing the ruling's own paperwork, not by the walk above, and it is the same class of
error a third time: a claim about heads-up-ness stated over the action history when the property it
asserts lives over the reachable subtree.

Every stage-4 document says **"all 36 spots of the retired chart are heads-up too, so nothing the bot
answers today is lost."** That was verified by enumerating the retired chart's `action_sequence`
values, which is a history reading, and it is true - all 36 pass the history predicate. It is not
true of the predicate that was ruled. Live-seat counts computed from the same keys, folds restored by
the seats the sequence omits:

| | spots |
|---|---|
| retired chart | 36 |
| pass the history predicate (the 110) | 36 |
| **pass terminal-clean (the 86)** | **22** |
| **lost - answered today, refused after the cutover** | **14** |

The 14 are `LJ/rfi`, `HJ/rfi`, `CO/rfi` and `BTN/rfi`; the RFI defences with seats still behind -
`HJ/LJ:raise@2.5`, `CO/LJ`, `CO/HJ`, `BTN/LJ`, `BTN/HJ`, `BTN/CO`; and all four small-blind defences
against a non-blind open. The 22 that survive are every big-blind defence, every three-bet
continuation, `SB/rfi` and the blind-versus-blind pair - **though only 21 end up covered**, because
`t6/d100/BB/SB:call` passes the predicate and still has no node to derive from: the solve is
`limp: false` and the tree holds no limp branch. That one was already accounted for under
`CHART-CANNOT-ANSWER-A-LIMPED-POT`; it is counted here so the two ledgers agree.

So the cutover **gains 64 spots and gives up 15** - 14 to the predicate and the limped pot to the
solve - rather than gaining 50 and giving up one, and the bot's opening coverage falls from five
positions to one. Two things follow. The sentence the contract's closing measurement was built on,
that nothing currently answered is lost, is false under this ruling and has been removed rather than
softened. And **the refusal-rate criterion reverses sign**: it predicted a fall against the retired
baseline and called a rise a defect, where the rise is now the ruled cost. Restated in the contract
as a rise confined to those 15 named spots, with a rise anywhere else still a defect - which is the
form that can actually catch something.

**This was carried to Taylor as a blocker rather than absorbed.** He ruled on 2026-08-25 having been
told four of the five opens vanish from the new chart, which was accurate. He was not told that four
of them are ranges the bot answers today, because the disposition note and the contract both still
carried the 110's version of the cost. The trade is larger than the one that was put to him, so it
went back rather than being written up as a footnote.

**Resolved, 2026-08-25: the ruling stands.** Put to him as "does the ruling stand knowing the bot
loses its LJ, HJ, CO and BTN opening ranges until the engine fix lands", he confirmed it does. So the
cutover ships a chart that cannot open from four of six seats, and the bot refuses an early-position
RFI where today it answers one. What that buys is that it stops answering from cells where the
solver flats a 2.5bb open 0.07 percent of the time, and the reasoning is the one the disposition
note already carried: a refusal beats a range wrong by 58 points of defence, whether or not the bot
used to answer it. The regression is a cost of the ruling, not a defect in it, and the closing
measurement must report it in those terms - opening coverage five positions to one, 14 retired spots
refused, 64 gained - rather than as a coverage rise.
