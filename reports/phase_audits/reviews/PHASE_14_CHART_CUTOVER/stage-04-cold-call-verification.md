# Phase 14 stage 4: independent verification of the cold-call finding

Written 2026-08-24 against the halt recorded in `verification/loop_runs/14.yml`. The brief asked for
falsification, not confirmation, and said to write a fresh walk rather than reuse anything. So this
note is measured from a standalone parser of
`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz` that imports nothing from
`src/` and nothing from the scratch scripts: it re-derives the container framing, the 169-class
index from the rule in `equity.rs`, the combo counts, the reach weighting, and each node's action
history from its parents' `actor_pos`. Two independent cross-checks say the walk is reading the file
correctly rather than reading it the same wrong way twice. The root opens 19.08 percent from the
lojack, which is the figure phase 10 published; and the big blind defends 49.02 percent facing a
2.5bb small-blind open, which is the complement of the 50.98 percent fold the contract states for
`REALIZATION-MODEL-UNDERPRICES-POSITION`. Neither number was used to build anything here.

**Nothing was refuted. All five numbered claims and both separate claims reproduce, several to the
basis point.** What the verification adds is the mechanism, which the halt note did not have, and
the mechanism changes what the phase should do about it.

## The five numbered claims

| Claim | Stated | Measured | |
|---|---|---|---|
| 1 | BB defends 27.28% at `[1,0,0,0,0]` | 27.28% (fold 0.7272) | holds |
| 1 | KQo calls 99.9% | 99.93% | holds |
| 1 | AA raises to 7.5 at 99.7% | 99.73% | holds |
| 2 | BB defends 7.44% at `[1,1,0,0,0]` | 7.44% (fold 0.9256) | holds |
| 2 | KQo folds 99.9%, AJo 99.5%, T9s 99.9%, K9s 99.2% | 99.87 / 99.47 / 99.88 / 99.25 | holds |
| 2 | AA jams 100bb at 94.3% | 94.33% | holds |
| 3 | price improves from 27.3% to 18.8% | 1.5/5.5 = 27.27%, 1.5/8.0 = 18.75% | holds |
| 4 | both nodes clear the 2% floor | every one of the 169 classes at 10,000 bp at both | holds |
| 5 | 26 committed spots, max 40.57%, min 4.01%, non-monotone | 26 exactly, 40.57% at HJ open + CO,BTN,SB, 4.01% at LJ open + HJ,CO,BTN | holds |

The 26 enumerate cleanly as choose-1-to-4 callers from the seats between each opener and the big
blind: 15 for the lojack, 7 for the hijack, 3 for the cutoff, 1 for the button. Every one is at full
reach. The non-monotonicity is not noise around a trend, it is a step: with one caller defence runs
7.44 to 16.48 percent and with two it runs 4.60 to 6.63, then three callers jumps to 29.58, 35.88,
36.10 and 40.57 - except the one three-caller line the small blind is not in, which is the lowest
figure in the whole family at 4.01. Every spot that defends above 29 percent has the small blind
among the callers. That pattern is worth a look on its own and is not diagnosed here.

## The two separate claims

**`reach_bp` is the actor's own range survival.** Confirmed constructively rather than by inference.
Predicting each node's `reach_bp` from nothing but the product of that same actor's own upstream
action weights reproduces the stored array to within 2 bp on every node tried, the residual being
integer rounding at 1 bp per multiplication. At `[1,0,0,0,0,2]`, where the lojack faces a three-bet,
the combo-weighted mean reach is 1908.3 bp and the lojack's opening frequency is 19.083 percent -
the same number. So the field carries no information about the opponents' actions at all, and
decision 1's floor is not a rarity filter.

The consequence is larger than the halt note claimed. Of the 5,626 committed nodes, exactly 351 are
nodes where the actor has not yet acted, and those are exactly the 351 at full reach; the floor
cannot drop any of them however rare the line. Carrying arrival probability through the tree
instead: **5,435 of the 5,626 committed nodes sit on lines that occur less than once in 10,000
hands, and 5,123 of them less than once in a million.** Node `[1,1,0,0,0]` itself occurs on 2.28
hands in 10,000 and is kept at a nominal 100 percent reach. (Line probability here is the product of
the reach-weighted action frequencies along the path, which ignores card removal between players;
that is an approximation of a few percent and none of these figures is close to a boundary.)

**No aggregate form of decision 10's two relations passes over the 5,626.** Measured at the ruled
one-point tolerance, counting nodes with at least one violation:

| Aggregate | over 5,626 committed | over the 351 at full reach |
|---|---|---|
| pairs, 13 single ranks adjacent | 1,185 | 33 |
| pairs, 4 bands AA-JJ / TT-88 / 77-55 / 44-22 | 409 | 4 |
| pairs, 3 bands AA-TT / 99-66 / 55-22 | 251 | 2 |
| pairs, 2 bands AA-88 / 77-22 | 51 | 0 |
| suited row over the row below | 1,145 | 73 |
| suited vs offsuit, per row | 2,102 | 9 |
| suited vs offsuit, whole range in one aggregate | 2,007 | 6 |

The brief's specific figure reproduces exactly: the whole-range suited-versus-offsuit aggregate
gives **6 violating nodes as solved and 97 with suited and offsuit transposed**, over the 351.

Two things this table says that the claim did not. First, over the full 5,626 that discrimination
inverts: as solved it flags 2,007 nodes and transposed it flags 818, so on the committed set the
gate scores the **wrong** index mapping as the better one. A check that prefers the transposed
mapping is worse than no check, because the defect it exists to catch is the one it rewards.
Second, the two-band pair aggregate is clean over the 351 and only the 351. So there is a form that
passes, and it passes by being restricted to the nodes where hero's whole range arrives - which is
6.2 percent of what the phase commits and is not what the criterion says.

## The poker: defect, or correct for a rake-free 100bb six-max game?

**Stated before reading the solver's grid**, as the brief asked. Closing the action for 1.5 into 6.5
at 4.3 to 1 with 98.5bb behind and two players in is one of the widest defending spots in the game.
I would overcall every pair, every suited ace and suited king, suited broadways, suited connectors
and one-gappers down to about 54s, and the offsuit broadways from AJo/KQo up - call it 50 to 60
percent of range - and squeeze roughly 4 to 6 percent for value and as a cap on the field. The
dominant term is implied odds, not raw equity: the pot is offering better than 5 to 1 on a call that
ends the betting, and the hands that flop sets, flushes and straights are the ones that get paid
three-handed.

**What the export does, and why.** The collapse is not unconverged noise and it is not a bug in the
solve. GTOpen states the cause in its own module header, `crates/solver/src/preflop/mod.rs` line 12:

> Multiway equity uses the product approximation (exact heads-up).

Hero's share of a multiway pot is priced as the **product of his pairwise equities** against each
opponent's range taken one at a time. That treats "beats the lojack" and "beats the hijack" as
independent events when they are strongly correlated, because both are driven by the same hand on
the same board. Line 1127 explains why nothing rescues it: the calibrated realization fit is gated
to `nd.live.count_ones() == 2`, and "multiway terminals keep the static heuristic (the postflop
engine that produced the data is HU-only)". The static heuristic is a positional weight of
1 + 0.16 x frac x min(spr,8)/8, which for the out-of-position seat of three is **0.920** - almost
nothing.

Priced that way, hero calls at node 2 when his product exceeds (2.5 - 1.0) / (8.0 x 0.920) = 0.2038.
The fraction of the big blind's range clearing that bar is **7.39 percent against the 7.44 percent
the solver plays.** The mechanism is settled.

What the approximation costs, measured against true three-way equity at 4,000 trials per class:

| | vs LJ alone | vs HJ alone | product | true 3-way | solver folds |
|---|---|---|---|---|---|
| KQo | 0.4756 | 0.3068 | 0.1459 | 0.2534 | 99.87% |
| T9s | 0.4123 | 0.3375 | 0.1391 | 0.2695 | 99.88% |
| K9s | 0.4319 | 0.3297 | 0.1424 | 0.2640 | 99.25% |
| 76s | 0.3678 | 0.3474 | 0.1277 | 0.2648 | 96.07% |
| 22 | 0.4042 | 0.4165 | 0.1684 | 0.2694 | 91.16% |
| AA | 0.8353 | 0.8522 | 0.7118 | 0.7133 | 0.00% |

**The product understates true three-way equity by 10.5 points on average across the 169 classes**,
and it does so unevenly in exactly the direction that ruins the spot: the error is worst on the
suited connectors and one-gappers that should be the core of a multiway overcall - J7s, 65s, 86s,
85s, 87s and 53s all at 14 points - and near zero on AA, at 0.15 points, because a hand that beats
everything pairwise also beats everything jointly. The hands whose whole value is multiway are the
hands the model cannot see.

Correct the equity and hold everything else fixed - same tree, same ranges, same static R, same
break-even - and the big blind defends **65.6 percent** instead of 7.44. Against the pot's own price
of 18.75 percent, 83.7 percent of the range clears. That brackets what published six-max solutions
defend here and it brackets the range named above before looking.

*Correction to an earlier draft of this note.* I first attributed the collapse to a flat realization
factor of about 0.673, fitted from the solver's own defending frequency at the five
big-blind-versus-single-open nodes. That fit does reproduce the aggregate, but it is a coincidence
of shape rather than the mechanism, and it is withdrawn. Reading the engine rather than fitting it
is what produced the paragraph above. The degenerate hijack cold-call range - 0.137 percent of range,
55 percent of it AQs - is real and is recorded below, but it is a consequence of the same pricing
rather than an independent second cause.

**The AA jam is a tree artifact and should not be read as a leak.** `raise_mults: [3.0]` gives the
big blind exactly one non-jam raise at this node, 7.5, which against a cold-caller lays the lojack 5
to call into 16.5 and the hijack the same - it prices in the entire field. With no squeeze size
between 7.5 and 100 in the tree, jamming is the better of the two options that exist. The defect is
that the solved config has no squeeze size, not that the solver picked wrongly among the sizes it
had. The chart will teach a 100bb shove where the right action is a raise to roughly 11 or 12.

**Verdict.** Correct solver output, wrong chart. The numbers are what the engine's documented
multiway pricing implies, so re-solving at a tighter gap will not move them and neither will any
change to the size menu; nothing here is a convergence question or a sizing question. Committing
them teaches a 92.6 percent fold closing at 4.3 to 1 in a three-way pot, across 26 spots that are
among the most common decisions in real six-max play.

## Is multiway worth extracting from GTOpen at all?

Measured after the fact, on Taylor's read of the above. The take holds, and the ratio is upside-down.

**98.0 percent of the 5,626 committed nodes have two or more opponents already invested. 8.3 percent
of the 3,054 preflop decision points in the 499-hand corpus do.** Real six-max preflop play is
overwhelmingly heads-up: 53.3 percent of corpus decisions face nobody in the pot yet and 38.4 percent
face exactly one. The export inverts that, because the tree branches on every cold call while a reach
floor that measures the actor's own survival never prunes a branch for being rare. Keeping only
at-most-one-invested-opponent spots leaves **110 of 5,626**, which also makes decision 1's whole
reach-floor apparatus moot - 110 spots do not strain a 20 MB cap, so the rule that exists to fit
under it has nothing left to do.

The heads-up half is the part worth keeping, and the repo's only external oracle says so. Against the
raked GTO Wizard reference, rake-free should open and defend wider, and it does:

| | open, solve / ref | delta | BB defence, solve / ref | delta |
|---|---|---|---|---|
| LJ | 19.08 / 17.49 | +1.59 | 27.28 / 22.63 | +4.65 |
| HJ | 21.64 / 21.65 | -0.01 | 29.92 / 26.20 | +3.72 |
| CO | 27.34 / 27.89 | -0.55 | 34.12 / 31.48 | +2.64 |
| BTN | 40.26 / 40.56 | -0.30 | 36.76 / 39.43 | -2.67 |
| SB | 54.09 / 34.41 | +19.68 | 49.02 / 42.88 | +6.14 |

Every big-blind delta lands inside the band decision 9 predicted before the measurement ran,
including the button coming back tighter. The small blind's +19.68 on opens is the limp ruling rather
than a defect: the reference limps 13.73 percent and the solve cannot, so that volume arrives as
opens. And the product approximation is *exact* heads-up by construction, so the mechanism that
destroys the multiway half cannot touch these.

The cost of scoping to heads-up is that the bot refuses roughly 8 percent of preflop decisions
instead of answering them wrongly, and phase 08's comparison loses those from its denominator. The
thing it does not buy is depth: 35 of the 110 are at full reach and the rest are three-bet and
four-bet continuations, and this phase's own plan already flags the published four-bet node as
unconverged. Heads-up is trustworthy at shallow depth, not at every depth.

## Adding a squeeze size

Options exist and one is cheap, but **none of them fixes the overfold**, because the overfold is the
equity model rather than the size menu. Read from `PreflopConfig` rather than inferred:

- `raise_mults: Vec<f64>` already takes a list. `[3.0, 4.5]` gives a squeeze to 11.25 over a 2.5
  open. Global, and this is the option the phase already priced at 38,828 to 260,136 action nodes.
- `raise_mults_by_seat: Option<Vec<Vec<f64>>>` and `open_raises_by_seat` give **per-seat size menus**,
  with an empty inner list meaning "use the global menu". The field's own doc comment states this use
  case: "lets one seat explore a wide sizing menu while modeled opponents stay pinned". Giving the big
  blind `[3.0, 4.5]` and everyone else the global `[3.0]` costs a fraction of the global blow-up, and
  the solver picks between them by context - 7.5 heads-up, 11.25 as a squeeze - because that is what
  a size menu is for. The exact node count is one `POST /api/preflop/spot` away and was not measured
  here.
- `allin_threshold` (0.85 by default, 0.67 as ruled) decides when a named raise collapses into a jam,
  so it is the other lever on the AA-jams-100bb artifact.
- `call_only_seats` drops every raise and jam from named seats. Not useful here, recorded because it
  is the fourth sizing-shaped field and a reader will find it.

What a squeeze size buys is the AA-jams-100bb artifact, which is real: with only a 3x re-raise
available the big blind's sole non-jam raise over a cold-called open is 7.5, which lays the lojack 5
to call into 16.5 and prices the whole field in, so the jam is the better of the two options that
exist. Fixing that is worth doing whenever a re-solve happens for another reason. It is not worth a
re-solve on its own, because the 92.6 percent fold survives it untouched.

## Solving multiway later

Possible, and clean at the chart level. Blocked on the engine, not on the config.

Clean at the chart level because the spot key already encodes the action sequence, so a multiway spot
carries a key of its own. Adding those spots in a later phase is additive - new keys, no re-keying -
which keeps it clear of `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`, and the contract's existing rule that
an unselected spot is a refusal with a code is exactly the behaviour a deferred family needs in the
meantime. Nothing about excluding multiway now forecloses adding it.

Blocked on the engine because the product approximation is in the core pricing rather than in a
parameter. There is no config value that turns it off: `realization` chooses among `raw`, `static`
and `calibrated`, and all three multiply an equity that has already been computed as a product.
Making multiway usable means computing true multiway equity at `KIND_POT_SHARE` terminals, which is
not a table lookup - three-way equity is not decomposable into pairwise terms, which is the whole
finding. And the calibrated fit cannot be extended to cover it, for the reason the source gives:
the postflop engine that produced the fit is heads-up only.

So the honest shape of a later multiway phase is a change to GTOpen, benchmarked and re-validated,
not a second extraction run. Worth filing with that scope stated, so nobody plans it as a config
edit.

## What this does not settle

The equity figures are Monte Carlo at 4,000 to 12,000 trials per class, so roughly plus or minus 0.5
to 0.9 points, and they are all-in-to-the-river equity rather than realized EV. None of the
conclusions turns on a number closer than three points to a boundary. The 7.39-against-7.44 match is
the strongest single result here and it is one node; the mechanism is read from the source and the
source states it plainly, but the reproduction was not repeated across the other 25 spots in the
family.

The pairwise equities used to form the product are this note's own Monte Carlo rather than GTOpen's
169-class equity table, so the two agree in mechanism and only approximately in value. Reading the
table directly would tighten the match and was not done.

The small-blind step in the 26-spot family is still not explained. What can be said is that those
lines occur at probabilities between 1e-10 and 1e-13 and their strategies are sharp rather than
near-uniform, so they are neither obviously untrained nor a measurement of anything a player will
meet. The per-seat squeeze menu's node count was not measured, and it is one `POST
/api/preflop/spot` away for whoever wants it.

Which disposition the phase takes - scope to heads-up, exclude the cold-call family only, replace the
reach floor with an arrival-probability floor, re-solve with a per-seat squeeze menu, file the
multiway engine work for later, or ship and record - is Taylor's, not this note's.
