# Stage 2 review: the poker in decisions 9, 11 and 12

Independent read-only review of the poker consequences of what phase 16 is about to freeze. I did
not write the contract, the ExecPlan, the decision list, or the two earlier notes in this
directory. Three passes have already run on this phase and none had a poker brief; this one judges
the poker and not the fidelity of anything to any document.

Method, so every number can be re-run rather than trusted. The range strings were pulled out of
the `Appendix data:` lines of `reports/active/latest_postflop_solve_cost.txt` and re-parsed from
scratch; combo counts are 6 per pair, 4 per suited class, 12 per offsuit class; "mass" below means
the sum of `combos x weight`, which is the frequency with which a player actually arrives at the
flop holding something from that set. The tree rows were re-parsed from the same file's `Row data:`
lines. Pot-odds, minimum-defence and geometric-sizing figures are arithmetic I did here from the
pot and stack in the committed configs. Where I am reasoning from poker knowledge rather than from
a repo measurement I say so on the line. No tracked file was modified; `run_verify.py` and
`check_gate_bite.py` were not run.

**Second pass, 2026-09-09: verification of `d98cc09`, and the verdict.**

All five original blockers are addressed in `d98cc09` and I accept all five as written. I checked
each against the data rather than against the commit message: decision 9 now carries the equity and
defence numbers and both corrected costs; decision 11 replaces the 3-bet-pot experiment with the
floored single-raised-pot diff and labels option 3 backwards with the geometry; decision 12's
default is reversed to floor at 0.01 with the mass figure and the not-delicate gap; and the
`donk: ""` / `add_allin: false` finding is in decision 11 in its own right. The two figures the
commit re-derived independently reproduce mine to the digit, 878 of 1,274 combos and 0.199% of
weight. My own note was committed unmodified.

One thing that came back **sharper than I wrote it came back half wrong**, and it is a new blocker
below rather than an accepted item. The rest of this section answers the two questions put to me.

**Third pass, 2026-09-09. I was wrong about `donk`, and the wrong claim is now committed.** The
retraction is the last blocker below, and the verdict that follows survives it with its third
clause replaced. My first pass hedged this correctly by giving two readings; my second pass dropped
the hedge and asserted the wrong one, which is the exact failure this brief warned me about.

**Would a strong player say these cells are playing poker?** On the defaults as they now stand:
the value judgements yes, the frequencies unproven. Which hands bet, which continue and which fold
will look right; a 0.3%-of-pot solve does not get that wrong. But what a strong player reads off a
flop chart is not *which* hands bet, it is *how often*, and mixed frequencies settle well after
exploitability does. Nothing here has solved a cell deep and diffed the frequencies against a
shallower one, both determinism runs stopped at 240 iterations, and that is decision 4's own first
open item. For a training artifact the frequencies **are** the product, so this phase is about to
commit a frequency table that nobody has checked is one. Beyond that, the two things a strong
player would query are narrower than I first said, and both reach the flop only through
continuation values: the out-of-position player cannot lead a turn or river into the previous
street's aggressor, and all-in is never an offered size although the tree still snaps a configured
bet to a stack-off at 85% of the stack behind - which on later streets it does, and on the flop it
does not. The seventh blocker has the arithmetic.

**Does the all-in snap change the verdict? No, and it needs no new field on a cell.** The
replication in blocker 7 finds zero threshold-snaps on the flop under either menu in either pot
type, so a committed flop cell's action set is what its menu says. What it does need is one line of
provenance rather than a per-node flag: the 3-bet pot's deepest flop line sits 3.625 chips, 3.9% of
stack, under the threshold, so `max_raises`, the raise multiplier, the starting pot and the
effective stack decide whether the flop's deepest node is a sized raise or a stack-off. Pin those
four on the committed config, record them on the cell beside the exploitability and the iteration
count the contract already mandates, and re-run the reachability walk if any of them moves. That
rides decision 7's existing default - prove it on the run that is committed, not on a proxy -
rather than adding a condition of its own.

So: worth committing, conditionally, and the condition is one solve. Rule the menu so the finer
tree lands in the single-raised pot, publish the missing turn and river lead and the snap threshold
on every cell, and **solve
one cell to several times 240 iterations and diff the action frequencies against the 240-iteration
version.** If the frequencies have moved materially the phase is committing noise with a good
exploitability number on it, and no amount of board coverage repairs that. That diff is the
cheapest open measurement in the phase and the one I would put in front of a ruling first.

Read this next, because two of the three original items turn on it. **The 68% in decision 12 is a
count of labels, not a quantity of poker.** Flooring the single-raised-pot out-of-position range at 0.01
removes 68.9% of its nonzero-weight combos and **0.199% of its mass**. The other side loses 18.4%
of combos and 0.039% of mass. Those are recomputed, not quoted:

| range | combos | combos at floor 0.01 | mass | mass at floor 0.01 | combo cut | mass cut |
|---|---|---|---|---|---|---|
| SRP out of position `717f36499fb4` | 1,274 | 396 | 300.24 | 299.64 | 68.9% | **0.199%** |
| SRP in position `23642f5e22e7` | 762 | 622 | 533.79 | 533.58 | 18.4% | **0.039%** |
| 3-bet out of position `568ae7b39c57` | 266 | 220 | 188.53 | 188.47 | 17.3% | **0.032%** |
| 3-bet in position `75dddc9d9ce2` | 526 | 278 | 234.92 | 234.52 | 47.1% | **0.170%** |

My combo counts are pre-board and the report's `hands_oop`/`hands_ip` are post-board, which is the
whole of the difference: 1,274 -> 396 pre-board is 1,131 -> 360 on `Kc7d2h`, exactly the figures in
the record. Both sides agree, so the mass column is the new information.

## Blocker

The five below are the original set and `d98cc09` addresses all five; they are left as written
because clearing a blocker is the driver's act and not the reviewer's. The one that follows them,
dated 2026-09-09, is new and open.

- **Decision 12's default is poker-wrong. It should be: floor, at class level, at 0.01.** The item's central sentence is "hero's committed strategy is solved against an opponent who has folded two thirds of what he would really hold." That is false. The opponent holds two thirds fewer *labels* and 99.8% of the *hands*, weighted by how often he holds them. The heaviest class the floor deletes from the single-raised-pot defending range is 87s at weight 0.0099; the next four are KJs 0.0054, AJs 0.0045, 66 0.0043 and 77 0.0041; the bulk sit at 0.0001 to 0.0005 and include 32o at 0.0003 and 72o at 0.0002. Those are not defends. They are regrets the preflop solve never drove to zero, in a range whose real content is 300 combos of mass spread over 1,274 labels. "No floor" is being defended as the fail-closed option, and it is not one: keeping the residue does not make the artifact safer, it costs 2.0x memory (21,663 MB to 10,881 MB, action-node count identical at 2,347,996) and it is the reason the pinned menu cannot be solved in the commonest way to see a flop. The repo's own `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` already says the residue "costs a factor of two in memory and buys nothing", and this item defaults to keeping it.

  The EV argument in the units the item asked for, and this is my reasoning rather than a repo
  measurement. Hero's EV in a spot is linear in the opponent's range weights, so deleting mass
  fraction `f` and re-solving costs hero, to first order, nothing at all: at an optimum the
  envelope theorem makes the loss second order in `f`. With `f = 0.002` that is 4e-6 of the EV
  spread across villain's holdings. Even the crude first-order bound is small: if hero's response
  to the deleted 0.2% of mass were wrong by a full pot, the cost is `0.002 x 5.5 = 0.011` chips
  against a 0.0165-chip target, and "wrong by a full pot" is absurd for hands hero was already
  near-indifferent about. The one honest caveat is the same one decision 6 applies to quantisation:
  the envelope argument is a statement about an optimum, and both determinism runs stopped at 240
  iterations with convergence unproven, so it is weaker for the strategy this phase would actually
  commit than for one at equilibrium. It is still nothing like a 68% truncation.

  The value is also not delicate, which is worth telling whoever picks it. The distinct weights in
  the defending range jump from 0.0114 (AQo) straight to 0.0249 (T9s) with nothing in between, so
  every threshold in [0.0115, 0.0249] deletes the identical 98 classes. Mass lost by floor: 0.005
  -> 0.179%, 0.01 -> 0.199%, 0.02 -> 0.245%, 0.05 -> 0.320%, 0.10 -> 1.093%. The knee is at 0.10,
  an order of magnitude above the proposed value.

  One arithmetic consequence for whoever implements it: arena is linear in the **sum** of the two
  hand counts, not their product. Across all eight unfloored pinned single-raised builds,
  `arena_MB = 5.097e-6 x action_nodes x (hands_oop + hands_ip)` holds to three digits, and the
  floored build reads 5.043. So flooring only the defender gives 1810 -> 1039, about 12,450 MB,
  which is still over the measuring script's 12,026 MB ceiling. Both sides have to be floored to
  reach 10,881 MB, and both sides are near-free by the table above.

- **Decision 12 does not name the floor's real poker cost, and it is not the truncation: the floor makes the preflop solve's pair indifference permanent.** Recomputed from the floored range the record already carries, `config.range_oop@b6fe98063c86`: the 3-bet out-of-position range after flooring holds AA, KK 0.9996, QQ 0.9993, JJ 0.9725, TT 0.9579, 99 0.9982, 88 0.9988, 77 0.9985, 66 0.999, 55 0.9776, 33 0.162, 22 0.9994 - and **no 44**, because 44 sat at 0.0007 and the floor deleted it. A committed artifact in which the big blind 3-bets 22 every time, 33 one time in six and 44 never is visibly wrong to any student, and after flooring hero holding 44 in that 3-bet pot has no cell at all. This is the indifference-artifact half of `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`, which the unfloored range merely hides and the floor hardens into data. The floor should still be ruled yes, but the item must state this, and the class-level smoothing of the small-pair and suited-king indifference has to land before or with the floor rather than after it. Flooring an unsmoothed export is the one version of this decision that is genuinely worse than no floor.

- **Decision 11 proposes the wrong measurement, in the pot type where the effect it is measuring is smallest.** The item says to "run the reduced config on a 3-bet pot at `9c8c7c` or `Kc7c2c` and diff the flop strategy against `matrix-01` or `matrix-02`". That experiment is well-controlled and it will systematically understate the thing it is meant to bound, because 75% is almost exactly the geometric size in a 3-bet pot and is nowhere near it in a single-raised pot. Arithmetic from the committed configs: to get all in over three streets the pot must grow by a factor of `(P + 2S)/P` split three ways, which is `(16 + 185)/16 = 12.56`, cube root 2.32, so `b = 66%` of pot in the 3-bet pot at SPR 5.78; and `(5.5 + 195)/5.5 = 36.5`, cube root 3.32, so `b = 116%` of pot in the single-raised pot at SPR 17.7. Three consecutive 75% bets in the 3-bet pot reach a river all-in (16 -> 40 -> 100, with 50.5 behind into a pot of 100). Three consecutive 75% bets in the single-raised pot go 5.5 -> 13.75 -> 34.4 -> 85.9 and leave **57.3 of a 97.5 stack behind**. So in the shallow pot one size is close to the whole job and the second size buys little; in the deep pot the menu is short of the geometric size on every street and the small size is doing genuinely separate work. A small diff measured in the 3-bet pot would then be read as licence for the reduced menu in the single-raised pot, which is exactly the half where the distortion lives and where option 2 would actually be used.

  The right measurement is affordable and the record already prices it. Diff pinned against reduced
  in the **single-raised** pot with both ranges floored at 0.01, board, pot, stack and ranges held:
  pinned floored is the measured 10,881 MB build, and reduced floored comes to `750,792 x 919 x
  4.49e-6 = 3,098 MB` by the arena law above. Both are under the 12,026 MB ceiling, both use the
  same hands, and the pinned 3-bet rows converged at 220 to 260 iterations on a tree of the same
  order. That single pair of solves answers decision 11's open question and decision 12's at the
  same time, which is why the two items should be ruled together rather than in sequence.

- **Option 3 is backwards on poker grounds, and the item ranks it highest.** Option 3 is "pinned for 3-bet pots and reduced for single-raised" and it is presented as the only option measured on both line types. By the geometry above that is the pair that puts the finer turn and river menu in the pot where a single size is nearly sufficient, and the coarser one in the pot where two sizes matter most. It is measured on both halves because the two halves are what happened to fit in memory, not because they are the two halves worth having. My poker reasoning for the direction of the distortion, stated as reasoning: in a 100bb single-raised pot the dominant flop strategy for the preflop raiser is a high-frequency small bet on static high-card boards, and its value comes from being repeatable cheaply on later streets; force the turn to a single 75% and the small flop bet loses its continuation, so weight moves off 33% toward checking and toward 75%. The reduced menu also removes the small turn bet from the **defender**, so hero's flop check-back is punished only by a large turn bet that is easy to defend and never by a cheap stab, which makes checking look better than it is. Both effects push the same way, so the reduced single-raised-pot flop strategy should be expected to bet less, bet small much less, and respond less to texture than the truth. The boards where that bites hardest are the dry rainbow high-card boards - which is also the texture family this repo has never once solved to target.

- **Whatever decision 11 rules also silently rules that the out-of-position player cannot lead and that neither player can ever jam, and no item says so.** Every menu body in the record, pinned and reduced alike, reads `donk: ""` on all three streets, and every config row reads `add_allin: false`. Those are not menu trimmings, they are missing actions. I could not determine from this repo whether GTOpen's "donk" covers only an out-of-position lead into the previous street's aggressor or every out-of-position first-in bet, and the answer changes which nodes exist: under the wide reading the defender never bets first on any street and the committed solve is "in position bets, out of position responds", which is not the game, and decision 9's own premise that hero "can face a 33% bet or a 75% bet" would be unreachable for the in-position seat. Under the narrow reading the missing action is the out-of-position turn lead after a called flop bet, which is still a frequent and strategically important line. Either way hero's flop bet is being valued against an opponent who can never take the betting lead back, which overstates betting; and with no size above 75% and no jam, no bet-bet-bet line in the single-raised pot can threaten the stack, which understates the polar branch. Those two errors push flop betting frequency in **opposite** directions, which is precisely why the sign of the net cannot be settled by argument and why the measurement above is needed rather than optional. Decision 11 is titled "the bet-size menu the committed solve is configured with"; the donk and all-in fields are part of that configuration and belong in its option text.

- **New, 2026-09-09. Decision 12's pair-ladder paragraph is half wrong, and repairing the wrong half would inject a poker error into the input.** The item now says the 3-bet defender keeps every pair except 44 and the single-raised defender keeps only `55 44 33 22`, "losing `TT 99 88 77 66` while the worse pairs survive", and concludes "neither is poker". The first half is right and is the finding. The second half is normal poker described as a defect. Printed from the committed range strings, weight in the range with `K` kept and `d` deleted at a 0.01 floor:

  | range | AA | KK | QQ | JJ | TT | 99 | 88 | 77 | 66 | 55 | 44 | 33 | 22 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | SRP out of position, BB flat-call | - | - | - | - | d | d | d | d | d | K | K | K | K |
  | SRP in position, BTN open | K | K | K | K | K | K | K | K | K | K | K | K | K |
  | 3-bet out of position, BB 3-bet | K | K | K | K | K | K | K | K | K | K | **d** | K | K |
  | 3-bet in position, BTN calls the 3-bet | - | - | d | d | K | K | K | K | K | K | K | K | K |

  The single-raised defender's pattern is a **single threshold in hand strength**: every pair 66 and
  better is absent from the flat-calling range because it 3-bets, and 55 down to 22 flats. Two
  blocks, monotone, no inversion. A big blind that 3-bets 66+ against a button open and flats the
  small pairs is a standard rake-free solution, and the same is visible on the in-position side of
  the 3-bet line, where QQ and JJ are deleted because they 4-bet. Those deletions are the preflop
  strategy showing through, not residue, and telling a reader they are "not poker" invites the one
  repair that would be a regression: smoothing `TT 99 88 77 66` back into a flat-call range they
  correctly sit outside, where they are already counted in the 3-bet range.

  The artifact is `44`, and it is one hand class rather than a block. In the 3-bet defending range
  44 reads 0.0007 while 33 reads 0.162, 22 reads 0.9994 and 55 reads 0.9776. No ordering of hand
  strength produces that, which is what makes it indifference residue rather than strategy - and it
  is the same class on the in-position side, at 0.0194, where it sits between 55 at 0.847 and 33 at
  0.998 and survives the floor by two hundredths. So the honest statement is narrower and stranger
  than the one in the item: **44 is anomalous in both 3-bet ranges, and a 0.01 floor deletes it from
  one side of the same pot type while keeping it on the other.** Hero would then be solved in a
  3-bet pot where he can hold 44 and his opponent provably cannot. That is worth publishing; a
  rank-ordered block of better pairs being cut is not, because it did not happen.

- **New, 2026-09-09, and this one is mine to retract: `donk: ""` does not remove the out-of-position player's FLOP bet, and the `check 1.00` paragraph now in decision 11 is wrong and must come out.** I read GTOpen's tree builder rather than continuing to infer it. `crates/solver/src/tree.rs:485-489` reads `let donking = st.to_act == OOP && st.street > self.root_street && st.last_aggressor == Some(IP); let size_list = if donking { &sizing.donk } else { &sizing.bet };` and `root_street = (board.len() - 3)` at line 304, so on a flop-rooted solve `st.street > root_street` is **false at the flop** and the out-of-position player uses `sizing.bet`, which is `"33 75"` in every measured config. The build validator says the same in its own words at line 346: `let donk_used = player == "OOP" && street > root_street as usize`. And `last_aggressor` starts `None` at the root (line 390) and is carried unchanged through a check (line 615), so even the turn stab after a flop check-check uses the `bet` list.

  So the out-of-position player bets 33 and 75 on the flop in both pot types, no committed cell is a
  forced single action, no bytes are wasted on `check 1.00`, and nothing should be omitted. The
  paragraph now in decision 11 would tell an implementer to delete or refuse 1,755 cells per line
  of genuine solved strategy, which is a worse outcome than the error it was meant to fix. It must
  be struck, not softened.

  What survives, precisely. The `add_allin: false` half needed the same check and did not get it
  in this item; the next blocker corrects it. The donk half
  survives only in its narrow form: the missing action is the out-of-position player **leading the
  turn or the river when the in-position player was the previous street's aggressor** - the probe
  into a called flop bet. That is a real and frequent line and it does bias hero's flop bet upward,
  because his flop bet is never answered by a turn lead. But it is a continuation-value effect on a
  flop-only artifact, the same channel as decision 11's turn and river size restriction, and not a
  missing flop node. My fifth blocker should be read with its wide reading deleted; its conclusion
  that the sign of the net flop-aggression effect must be measured rather than argued is unchanged,
  because the jam and the missing probe still pull opposite ways.

- **New, 2026-09-09. Seventh blocker, and it retracts my "no jam anywhere" as well: `add_allin: false` does not mean the tree has no all-in, and `allin_threshold` is a fraction of the remaining STACK rather than of the pot, which the solver notes and the contract both state wrongly.** Two source facts. `crates/server/src/main.rs:241` converts the posted field as `allin_threshold: self.allin_threshold / 100.0`, so the posted 85.0 becomes 0.85 - the notes are right that it is a percent rather than the preflop fraction. But `crates/solver/src/tree.rs:435` defines `stack_me = effective_stack - (put[me] - starting_pot / 2.0)`, line 491 sets `max_to = stack_me`, and the snap at lines 468 and 512 reads `if to >= max_to - 1e-9 || to >= self.config.allin_threshold * max_to - 1e-9 { to = max_to; }`. The denominator is the **stack behind**, not the pot. And that snap sits **outside** the `add_allin` guard: `add_allin` controls only whether an *extra* all-in candidate is pushed (lines 459, 504), while every configured bet and raise is silently converted to a stack-off once it reaches 85% of the stack behind. So `add_allin: false` removes all-in as an offered *size*; it does not remove all-in from the tree.

  Where it fires, computed from the committed configs. On the flop it never does, in either pot
  type, and that part of my claim survives:

  | line | deepest flop amount | % of stack behind | snapped? |
  |---|---|---|---|
  | single-raised, 75% then two 2.5x raises | 25.78 | 26.4% | no |
  | 3-bet, 75% then two 2.5x raises | 75.00 | **81.1%** | no, by 3.6 chips |

  The 3-bet pot's deepest flop line misses the 78.625 threshold by under 4% of stack, so a change to
  `max_raises`, to the raise multiplier, or to the 3-bet size flips the flop's action set from a
  sized raise to a stack-off, and no field in the artifact would record which one a cell was solved
  under. That alone is worth a line in decision 11.

  **Amended 2026-09-09 after I replicated the builder rather than hand-computing one line.** I wrote
  the paragraph that stood here from a single hand-worked example plus poker reasoning, and the
  coordinator challenged both. The example is right; the direction I drew from it is wrong. Both
  halves are settled by a faithful re-implementation of `legal_actions` and the four transitions,
  enumerating every reachable betting state under each menu with amounts only, since bet sizes do
  not depend on the cards.

  The example reproduces exactly, and the challenge to it does not. The reachable state
  `bet12.00 raise30.00 call30.00` on the flop leads to a turn with pot 76, stack behind **62.50**,
  and a configured 75% turn bet of 57.00 at 91.2% of stack, which threshold-snaps. The competing
  figure of 70.5 comes from reading `put[me]` as the amount put in on this street. It is
  cumulative and initialised to `starting_pot / 2` for each player: `put: [half, half]` at line 386
  with `half = starting_pot / 2.0`, then `put[me] += to - street_bet[me]` at lines 623 and 635. That
  is why `pot = put[0] + put[1]` returns 16 at the root, which is the 76 both of us used. After each
  player puts 30 in on the flop, `put` is `[38, 38]`, so `stack_me = 92.5 - (38 - 8) = 62.5`.

  **My direction claim is withdrawn: the pinned menu snaps more often than the reduced one, never
  less.** Distinct reachable states at which a size is converted, and the two conversion routes kept
  apart, because only the first is silent - the second is a size simply exceeding the stack, which is
  ordinary poker:

  | line and menu | threshold-snaps, flop / turn / river | over-stack all-ins |
  |---|---|---|
  | single-raised, pinned | 0 / 0 / 24 | 96 |
  | single-raised, reduced | 0 / 0 / 0 | 54 |
  | 3-bet, pinned | 0 / 6 / 9 | 99 |
  | 3-bet, reduced | 0 / 6 / 6 | 36 |

  So "the reduced menu replaces the turn with a jam wherever the flop built a pot" is false, and the
  poker conclusion I drew from it - that hero raises the flop less above the reduced tree - does not
  follow and is withdrawn. The likeliest reason it runs the other way is uninteresting: the pinned
  menu has strictly more lines, so more reachable states and more chances to cross the threshold.
  Which is also the caveat on the table above. **A count of snap states is a measure of tree breadth
  and not of strategic content**, so the 24-against-0 in the single-raised pot should not be read as
  a direction either, in my favour or against.

  What survives, and it is the part that bears on a ruling: **zero threshold-snaps occur on the flop,
  under either menu, in either pot type.** So this mechanism cannot change a committed flop cell's
  own action set as the configs stand, and it reaches the committed flop strategy only through
  continuation values - the same channel as the missing probe and the turn and river sizes. Its
  magnitude is unmeasured and the single-raised-pot pinned-against-reduced diff would carry it along
  with everything else, which is an argument for that experiment rather than a second one.

  The walk's own limits, stated so it is not quoted past them: it reproduces the amount arithmetic
  and the state transitions, dedupes by state, ignores chance nodes because amounts do not depend on
  cards, and counts reachable states rather than probability mass. It settles which conversions exist
  and where; it says nothing about how often a solved strategy visits them.

  What must change: the contract criterion describing `allin_threshold` as "a percent of pot on the
  postflop route" should read a percent of the effective stack behind, and its guard should be
  restated on that quantity. The notes' practical warning survives its own wrong mechanism - posting
  0.67 gives 0.0067, a 33% flop bet of 1.815 exceeds 0.0067 x 97.5 = 0.653, so every bet does become
  a jam - but a driver written to the pot description would compute the guard against the wrong
  number. And the phase should stop describing these trees as having no all-in.

## Non-blocker

- **Decision 9's default is poker-right and it is not a close call.** Facing 33% and facing 75% on the same board are different strategic problems by every measure that governs the decision. Required equity to call is `b/(1+2b)`: 19.9% against 33%, 30.0% against 75% - a 51% relative jump in the continue threshold. Minimum defence frequency is `1/(1+b)`: 75.2% against 33%, 57.1% against 75% - an 18-point swing in how much of hero's range continues, larger than any other single input in the spot. And the bettor's maximum bluff share is `b/(1+b)`: 24.8% at 33% against 42.9% at 75%, so the *bettor's* range composition at the two sizes differs by design and the "same ranges" premise in the question is false in practice. Composition follows: against a small bet the correct defence is call-heavy and raise-heavy and reaches down to bottom pairs and gutshots; against a large bet it is polarised into strong calls and folds. A merged cell would be an average of a 75%-defence and a 57%-defence, which means the bot **overfolds against small bets and overcalls against large ones** - the two errors an opponent farms by simply choosing his size, and findable in one session by a human. Merging is not "slightly coarse" here, it is a size-selection leak handed to the opponent.

- **Decision 9's stated cost is wrong: naming the size costs no bytes.** The item says naming the size "multiplies the spots by the menu". It does not. "Facing 33%" and "facing 75%" are already two distinct decision nodes in the solved tree, and they are already two of the roughly five hero flop nodes that decision 6's byte budget is priced at. Naming the size in the key labels nodes the solve produced anyway; naming only the action class would *merge* two solved nodes into one cell, which saves bytes by discarding data. So the trade is not exactness against size, it is exactness against a lossy compression, and the compression is the leak above. The coupling to decision 11's menu is likewise not a cost of the key: a cell solved at a 33/75 menu is only valid at a 33/75 menu whether or not the key admits it. A size-named key makes a later menu change fail closed, because the new key is not found and the lookup refuses. A class-only key makes the same change silently reinterpret every committed cell, applying a 33%-solved response to a 50% bet. Naming the size is the fail-closed option as well as the accurate one.

- **The size-named key exposes a coverage cliff nobody has priced: the artifact answers only 33% and 75%, and real opponents bet neither.** The contract already forbids the fix that would hide it ("no nearest-neighbour substitution of board, line, or flop action"), which is the right poker call - mapping a 50% bet onto the 33% cell would have hero defending at 75.2% where 66.7% is correct, and onto the 75% cell would have him defending at 57.1%, so both substitutions are near-9-point MDF errors, far larger than the preflop `@2.5` price substitution the repo already tolerates. But the consequence is that hero's facing-a-bet nodes refuse against any opponent who does not bet exactly a third or exactly three quarters, and nothing in this repo can measure how often that is. Self-play never bets postflop at all (`postflop_fallback.py` returns no bet or raise on any path), and the corpus instrument is preflop-only by its own docstring in `comparison_report.py`. So a phase named Postflop That Can Bet can ship 100% board coverage and a green gate while the bot bets fine and refuses to answer a bet. The covered-set inventory decision 3 mandates should name the bet menu as part of coverage, not only the preflop lines.

- **Flooring hero's own range creates a refusal hole, and its size is 0.2%, not 68%.** The floor removes hands from both ranges, so hero's own deleted classes have no committed strategy. Because mass is arrival frequency, the refusal fires on 0.199% of flop arrivals for the single-raised out-of-position seat and 0.039% for the in-position seat, not on 68% of them. That is small and it is fail-closed, but it must be written down, because an implementer who meets 99 missing hero hand classes and does not know their arrival weight will be tempted to fall back on the nearest hand class, which is the heuristic `AGENTS.md` forbids by name.

- **The converged evidence base is the least generalisable texture family there is.** Five solve rows plus two determinism repeats reached target; six are monotone and one is two-tone, on two rank patterns. Monotone flops are the worst possible sample for a flop-sizing artifact, because the flush possibility dominates range interaction and suppresses exactly the small-bet-heavy strategies that the other 84% of boards use. Never reached target: rainbow-dry, rainbow-connected, paired, ace-high connected, disconnected-low. Rainbow is 455 of 1,755 classes. So the untested set is the pedagogically central set, and by the reasoning in the option-3 blocker it is also the set most sensitive to the turn and river menu. The evidence gap and the abstraction-sensitivity gap sit on the same boards, which means neither can be used to reassure about the other.

- **Hero-strategy-only storage covers one seat of a line, so decision 6's "one preflop line" is one line-seat pair.** A postflop key inherits the preflop key's position segments, so a spot names one seat. To play "button opens, big blind calls" the bot needs the button's cells and the big blind's cells, or it refuses on whichever seat it happens to occupy. That doubles the node-line units per line the bot can actually play, and it should be stated in decision 6's budget rather than discovered when half the drills refuse.

**Outside the three items I was given, 2026-09-09.**

Decisions 1, 2, 4, 6, 8, 10 and 13 have had no poker pass. These are the poker consequences I saw
while working on 9, 11 and 12 and did not write because they were out of brief.

- **Decision 4's refusal exposure is 39.8% of flops, not the 25.9% its own class count implies.** The record states rainbow as "455 of the 1,755 classes" and never converts it. Brute-forced over all 22,100 boards: rainbow is 8,788 boards, **39.76%**; two-tone 12,168, 55.06%; monotone 1,144, **5.18%**. Rainbow classes carry more boards each (19.3 against 12.0 and 4.0) because their suit orbits are larger, so the class count understates rainbow's real weight by 1.53x. Under decision 4's default a cell that hits the iteration cap is refused, and rainbow has never been solved to target at all, so the worst case for that default is a flop trainer that refuses two flops in five - and specifically the plainest, most common ones, which is where a student needs it most. Nothing has measured whether the cap binds on rainbow; the point is that "455 of 1,755" is the wrong number to rule against.

- **The same conversion says the converged evidence base covers 5.18% of flops.** Six monotone rows and one two-tone. Monotone is 16.3% of classes and 5.18% of boards, and it is also the texture whose solution transfers least, because a flush draw on board dominates range interaction and suppresses the small-bet-heavy strategies the other 95% of flops use. So the phase's entire proof that a flop solve works sits on one twentieth of the flops it will commit, at the far end of the texture distribution from the ones it most needs to be right about.

- **Decision 1's flop strategy is solved for a game the bot will not play.** The item calls the flop-only seam "a visible seam" and "a worse experience". The poker is stronger than that. A flop bet's value at SPR 17.7 comes largely from the leverage it creates on later streets - hero bets a wide range small precisely because he can barrel - so a flop frequency solved above a full turn and river tree is not the correct frequency for an agent whose turn does not exist. The correct flop strategy for "bet, then never bet again" is far more value-heavy and far less bluff-heavy than the solved one. Under the contract the refusal voids the hand rather than checking it down, which is the better of the two behaviours and rescues the training use: a cell displayed at the flop and then stopped is teaching a real frequency in isolation. But it also means no winrate, EV or profile-comparison figure may ever be reported over a bot using this artifact, because the hands that reach a turn do not finish. That should be stated in the phase's own claims rather than discovered by a report generator.

- **Decision 10's default is right in mechanism and the item understates how stack-fragile a postflop cell is.** Pot and effective stack are recoverable from the preflop line at a flat 100bb table, so payload plus validation is the correct call. What the item does not say is that a flop cell is far more sensitive to effective stack than a preflop cell is. Computed from the single-raised pot's own pot of 5.5, the geometric three-street bet size moves 103.9% of pot at 77.5bb effective, 115.8% at 97.5, and 130.9% at 127.5; SPR moves 14.1 to 17.7 to 23.2. A preflop chart at 100bb is roughly usable at 85bb or 120bb. A flop strategy at SPR 14 is a different strategy from one at SPR 23 - different bet-size mix, different check-raise frequency, different commitment threshold. So the flat-table refusal that decision 10 inherits has to be strict rather than tolerant, and the validation must refuse a near-miss rather than round it, which is the opposite of the preflop chart's nearest-price substitution.

- **RETRACTED 2026-09-09, see the retraction blocker.** This item said a cell whose only legal action is check should not be committed, on the premise that `donk: ""` leaves the out-of-position player no flop bet. The premise is false: the donk list is not consulted on the root street, so the out-of-position player bets 33 and 75 on the flop. There is no forced-check cell and nothing to omit. Left in place rather than deleted because it is quoted in `af0cdce`.

**Poker pass on decisions 2, 6, 8 and 13, 2026-09-09.** These four had none. Decision 8 is the one
that matters.

- **Decision 8 is a poker question wearing a format question's clothes, and its default is right while the thing it exposes is not ruled.** Carrying the preflop key verbatim is correct: it names exactly the ranges a spot was solved from and invents no compression. But there are **two** price substitutions here and the item addresses only one. The committed one - recording that a spot was solved at the `@2.5` ranges - is honest provenance and the default handles it. The **query-time** one is where the poker error enters: a hand actually opened to 2.25bb looks up an `@2.5` key, and nothing bounds what that costs. Computed from the corpus's own median open against the key's price:

  | | pot | effective | SPR | geometric 3-street size | BB's price to call |
  |---|---|---|---|---|---|
  | `@2.5`, the key | 5.50 | 97.50 | 17.73 | 115.8% of pot | 27.3% |
  | `@2.25`, what was played | 5.00 | 97.75 | 19.55 | 121.1% of pot | 25.0% |

  Two channels, both systematic and both in one direction across every corpus hand, which matters
  more than either magnitude because neither averages out. The **range** channel is the larger:
  2.25bb is a cheaper price, so the true defending range is wider and weaker than the `@2.5` range
  the cell was solved against, and hero's committed strategy therefore c-bets and bluffs too little
  for the spot he is actually in. The **geometry** channel is smaller and opposite in character: the
  real pot is 9.1% smaller and SPR 10.3% higher, so the cell is solved at a lower SPR than the hand
  sits at and reads as too willing to commit. Neither is visible to decision 10's validation, which
  checks the payload against the **line** rather than against the query - so a spot can be served
  for a pot it was not solved at and the validation passes, because the artifact is being checked
  against itself. The poker conclusion: the preflop chart's nearest-price tolerance does not
  transfer. Preflop, 0.25bb barely moves a range. Postflop the same 0.25bb moves the pot, the SPR
  and both ranges at once, so the query-time substitution should refuse, or at minimum surface its
  SPR delta as a strategy substitution rather than a price one.

- **Decision 6 is treating a poker question as arithmetic: which nodes to spend the budget on.** The frontier is stated as products of nodes and lines with no view on which nodes. There is one. A student's leaks are not in the flop root - c-bet frequency is the single most widely published number in poker - they are in what to do **facing** a bet and facing a raise. So the poker ranking of the roughly six node-line units is: hero facing 33% and facing 75% first, hero facing a raise second, hero's root last. Option 4, "store hero's flop root only and refuse every later flop node", therefore spends the entire budget on the cheapest decision to learn elsewhere and refuses the two that carry the training value. That is a stronger objection to option 4 than the seam argument the item gives it, and it also says a 2x3 or 3x2 point on the frontier is not equivalent to 6x1 in usefulness even though it is in bytes.

- **Decision 2's ruling is poker-correct and its test does not cover the failure that would be poker-visible.** Suit isomorphism is exact, so the collapse costs nothing, and refusing rank abstraction is right. But the contract's test proves the **board** maps into exactly one class and that a rank-texture neighbour maps elsewhere. The error that survives that test is a hand permuted inconsistently with its board: on a two-tone flop, whether hero's two cards share the board's flush suit is most of the strategy, and a mis-mapped suit permutation would serve a no-draw strategy to a flush draw. It would be legal, plausible, and invisible to every exploitability number, because the cell is a correct cell for a different hand. The cheap check is poker-shaped rather than combinatorial: on a two-tone board, hero's flush-draw combos must not receive a strategy identical to the same ranks without the draw.

- **Decision 13's split has one poker argument nobody made.** Format before data means the key ships without cells, so the bot refuses everything in between, which costs no poker. What it buys is that the frequency-convergence diff the verdict above asks for belongs in the data half and would otherwise gate the key format on a measurement that has nothing to do with it. Splitting therefore lets the one measurement this phase actually needs happen where it belongs rather than blocking the part that is ready.

## Alignment

- `A-RANGE-TRUNCATION-IS-REPORTED-IN-COMBOS-WHERE-THE-COST-IS-IN-MASS` (new). Three committed documents now describe the 0.01 floor by its combo count - "68% truncation of the defending range", "hands from 1131v679 to 360v559" - and none states the mass. The combo figure is 345x the poker quantity (68.9% against 0.199%), it is the figure the no-floor default rests on, and it is the same class of error as `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS`, filed against this same file at stage 1. A range truncation reported in labels rather than in arrival frequency will mislead every future reader the same way.

- `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` (exists, deferred, phase 14). Its own text reaches the conclusion decision 12 declines: the residue "costs a factor of two in memory and buys nothing". It also holds the smoothing half that the second blocker above says must land before the floor. The entry is filed against phase 14, which is completed, so on current status this conditioning step has no owner and phase 16 consumes an unsmoothed export.

- `NO-MENU-IN-THE-RECORD-CAN-STACK-OFF-A-SINGLE-RAISED-POT` (**withdrawn 2026-09-09; do not file it**). I wrote this from the bet-bet-bet geometry: three 75% bets in a 100bb single-raised pot do leave 57.3 of a 97.5 stack behind, and the conclusion I drew from it is still wrong, because raises reach the stack even when bets do not. Replicating the builder finds all-in reachable everywhere - 96 distinct states in the single-raised pinned tree, 54 reduced, 99 and 36 in the 3-bet pot - by a configured size exceeding the stack, which is ordinary poker and needs no entry. What is left is the narrower `allin_threshold` finding, which the seventh blocker carries and the contract has already taken. Filing this as written would put a false claim in the backlog permanently, which is the failure `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT` records. Real solutions at SPR 17.7 use overbets on polarising turn and river cards, and the flop's polar branch exists partly to set them up. This is not a discriminator between decision 11's four options, since all four share it, which is exactly why it needs its own entry: it is the abstraction error none of the options can fix and none of them discloses.

- `NOTHING-MEASURES-POSTFLOP-ACTION-COVERAGE-AGAINST-REAL-BET-SIZES` (new). Board coverage will be reported at 1,755 of 1,755 while action coverage against any real distribution of bet sizes is unmeasured and unmeasurable in this repo today: self-play never bets postflop, and the corpus comparison is preflop-only by design. The refusal inventory ranks preflop gaps; there is no postflop equivalent.

- `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` (new). `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL` covers the cost consequence of the converged set being six monotone and one two-tone. The strategy consequence is separate and larger: monotone boards are the texture whose solution transfers least to the rest of the set, so the phase's entire converged evidence base says close to nothing about the strategies it will commit on the other 1,469 classes.

- `A-TEXTURE-FAMILYS-CLASS-COUNT-IS-NOT-ITS-BOARD-SHARE` (new, 2026-09-09). Rainbow is 25.9% of canonical classes and 39.76% of boards; monotone is 16.3% of classes and 5.18% of boards. Every statement in this phase about texture coverage, texture cost weighting and texture evidence is written in classes, and the two figures differ by 1.53x for the family that drives the refusal risk and by 3.1x for the family the phase's evidence sits on. Same shape as `A-RANGE-TRUNCATION-IS-REPORTED-IN-COMBOS-WHERE-THE-COST-IS-IN-MASS`: a count of equivalence classes standing in for the frequency a player meets them. The cost model already weights by orbit factor, so the conversion exists in the repo and is simply not applied where the coverage claims are made.

- `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED` (new, 2026-09-09). Decision 4 lists this as its first uncovered item and the solver notes list it first under "Not verified", but no entry owns it and no command would produce it. A training chart's product is its action frequencies, not its exploitability bound, and frequencies on indifferent hands converge later than exploitability. The measurement is one solve at several times 240 iterations diffed against the 240-iteration strategy on the same config, and it is cheaper than every other open measurement in the phase. `NOTHING-MEASURES-HOW-MUCH-THE-SOLVE-MIXES` is its preflop sibling.

- `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` (new, 2026-09-09). The committed flop frequencies are correct for an agent that can barrel and this agent refuses the turn, so they are not the correct frequencies for the game it plays. Decision 1 accepted a seam; this is the narrower statement that the artifact's own numbers assume a continuation that does not exist, plus the reporting consequence that no winrate or EV figure may be computed over a bot whose turn voids the hand.

- `POSTFLOP-CELLS-ARE-STACK-FRAGILE-WHERE-THE-PREFLOP-CHART-IS-NOT` (new, 2026-09-09). The geometric three-street size in the single-raised pot moves from 103.9% to 130.9% of pot across 77.5bb to 127.5bb effective. Decision 10's payload validation therefore has to refuse an off-depth spot rather than tolerate it, which is a stricter rule than the preflop chart's nearest-price substitution applies, and the difference should be stated where both live.

- `A-SOLVER-CONFIG-FIELD-IS-READ-FROM-ITS-NAME-AND-NOT-FROM-THE-BUILDER` (new, 2026-09-09; the ID reads right and `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE` at `backlog.yml:3020` is the correct sibling to file it under). Three instances now, two of them mine. I asserted that `donk: ""` removed the out-of-position flop bet, from the field's name; the builder does not consult that list on the root street. I then asserted that `add_allin: false` removed every all-in; the flag governs only whether an extra all-in *candidate* is pushed, while the snap that converts a configured size to a stack-off sits outside it. And the existing entry has `allin_threshold` reading as a fraction preflop and a percent postflop - to which the seventh blocker adds that its denominator is the stack behind and not the pot, so that entry needs the correction too. GTOpen is a local clone; any claim about which actions a committed config admits belongs in `crates/solver/src/tree.rs` and not in a field name. Three for three says this is the failure mode of reading a solver config as English.

- `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` (new, 2026-09-09). Decision 8's default correctly commits the substitution as provenance, and the substitution that happens at lookup is a different object with no bound on it: a 2.25bb open served an `@2.5` cell moves the pot 9.1%, the SPR 10.3%, the geometric size 5.3 points and both ranges, and decision 10's validation cannot see it because it compares the payload to the line rather than to the query. The preflop chart's tolerance for the same 0.25bb is defensible and does not transfer.

- `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS` (new, 2026-09-09). The contract's suit-isomorphism test proves every board maps into exactly one class and that rank neighbours stay distinct. A hand permuted inconsistently with its board passes it and produces a legal, plausible strategy for the wrong hand - a flush draw played as a no-draw on a two-tone flop. Exploitability cannot catch it. The poker-shaped check is one line and belongs beside the board test.

- `POSTFLOP-SOLVE-IS-RAKE-FREE-AND-THE-GAME-IS-NOT` (new). Every measured row is `rake_pct: 0.0, rake_cap: 0.0`, consistent with the rake-free preflop export, so the convention is coherent and the ranges match the solve. The consequence for a training bot is the postflop mirror of `OPENING-RANGES-READ-NARROWER-THAN-A-RAKED-REFERENCE`: a rake-free flop solution continues and bets marginally wider than correct play in the raked game a student actually sits in, and the effect concentrates on exactly the thin continue decisions a flop chart is consulted for. Direction stated, magnitude unmeasured; this is poker reasoning, not a repo number.
