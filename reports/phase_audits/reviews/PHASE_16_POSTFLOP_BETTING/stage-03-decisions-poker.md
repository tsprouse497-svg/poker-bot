# Stage 3 review: the poker in the rulings taken after stage 2

Independent read-only review of the poker in the rulings dated 2026-09-10 - decision 4's 1%-of-pot
commit bound, decision 6's three-board sample, decision 10's 20% price bands, decision 11's menu and
its machine note, and decision 12's floor in combination with that menu. Filed as
`NO-POKER-REVIEW-HAS-SEEN-THE-RULINGS-TAKEN-AFTER-STAGE-2` in `backlog.yml`.

I did not write the contract, the ExecPlan, the decision list, or any of the four earlier notes in
this directory. I read `stage-02-decisions-poker.md` first and do not re-raise what it caught. I did
not audit whether the record matches the contract; the stage-3 human-gate note spent eight rounds on
that and I have not repeated it.

**Method.** Every number below is computed in this session unless it is labelled poker knowledge.
Board texture shares are brute-forced over all 22,100 three-card boards. Menu geometry, pot odds,
minimum-defence frequencies and stack-off lines are arithmetic from the pots and stacks in the
committed configs in `reports/active/latest_postflop_solve_cost.txt`, re-parsed from its `Row data:`
and `Appendix data:` lines. Corpus figures are parsed directly from the 499 raw PHH hands in
`data/samples/public_corpus/corpus_hands.jsonl`. Range widths are read out of
`data/artifacts/preflop/six_max_100bb_rakefree.json`. Where I reason from poker knowledge rather
than a measurement I say so on the line. No tracked file was modified except this one;
`run_verify.py`, `check_gate_bite.py`, `pytest` and the mutation tooling were not run, and nothing
was checked out, stashed or reverted.

**Headline.** These rulings produce a good flop trainer for single-raised pots and a thin one for
3-bet pots, and none of them is wrong as poker. The menu is defensible at both SPRs, the floor is
close to free and is better than the record says, the price bands are loose but every tighter band
refuses ordinary hands, and the 1% bound is loose in exactly the quantity a chart publishes. The one
ruling I would change is the three-board sample: it is selected against the wrong criterion, and it
is the only frozen choice here that is free to fix today and expensive to fix after a solve.

---

## Blocker

- [resolved] **The committed sample's rank axis is chosen to cover gaps in the solve evidence, and the sample's
  own stated job is defect detection. Those pick different boards, and the ruled three spend a slot
  on the rarest texture in the deck while leaving out the only family a human can check.**

  Decision 6 item 4 rules `rainbow-paired`, `two-tone-connected`, `monotone-disconnected-low`. Its
  own reasoning for why the sample cannot be two monotones is the right reasoning - "the fetched
  bulk covers every paired board anyway, and the sample exists so the gate can see a structural
  defect at all". Both halves of that sentence say the sample is not for coverage. But the three
  cells it then picks are picked off the solver notes' never-reached list, which is a list of
  *solve-evidence* gaps.

  Nothing in the gate can see a strategy defect: the contract says so at line 38 - "Nothing in this
  phase gates on whether the resulting strategy is good poker". So the sample's detection power is
  entirely a human looking at three flop charts. A human can only see a defect on a board where he
  holds an expectation, and there is exactly one flop family where that is true without tooling: the
  unpaired high-card rainbow board, where a button c-betting small at high frequency against a big
  blind is the most published number in poker (poker knowledge). The ruled sample contains no
  unpaired high-card board of any suit.

  The board shares, brute-forced over all 22,100 boards here rather than quoted. Rank families are
  defined as: `paired` includes trips; `connected` is unpaired with a 3-card span of 4 or less;
  `dry-high` is unpaired, top card ten or better, and no two cards within 2 ranks; `dry-low` is
  unpaired with a top card below ten and not connected; `semi-high` is the remainder.

  | rank family | boards | share of flops |
  |---|---|---|
  | dry-high | 8,960 | **40.54%** |
  | semi-high | 3,840 | 17.38% |
  | paired (incl. 52 trips) | 3,796 | 17.18% |
  | connected | 3,712 | 16.80% |
  | dry-low | 1,792 | 8.11% |

  And the fifteen (suit x rank) cells, of which the ruled three are marked:

  | cell | boards | share | |
  |---|---|---|---|
  | two-tone dry-high | 5,040 | 22.81% | |
  | rainbow dry-high | 3,360 | 15.20% | |
  | two-tone semi-high | 2,160 | 9.77% | |
  | two-tone connected | 2,088 | 9.45% | **ruled** |
  | rainbow paired | 1,924 | 8.71% | **ruled** |
  | two-tone paired | 1,872 | 8.47% | |
  | rainbow semi-high | 1,440 | 6.52% | |
  | rainbow connected | 1,392 | 6.30% | |
  | two-tone dry-low | 1,008 | 4.56% | |
  | rainbow dry-low | 672 | 3.04% | |
  | monotone dry-high | 560 | 2.53% | |
  | monotone semi-high | 240 | 1.09% | |
  | monotone connected | 232 | 1.05% | |
  | monotone dry-low | 112 | **0.51%** | **ruled** |
  | monotone paired | 0 | 0.00% | impossible |

  So the ruled sample spends one of its three slots on **monotone dry-low, 112 boards, 0.51% of
  flops - the rarest of the fifteen cells** - and covers 18.66% of flops in total. The reason it is
  there is the notes' never-reached list, and covering a solve-evidence gap is a cost question
  answered by the bulk campaign, not by the sample.

  **What to change, and it is one axis.** Keep the suit split exactly as ruled - one rainbow, one
  two-tone, one monotone, with the monotone slot necessarily unpaired. Change the rank axis from
  `paired / connected / dry-low` to **`dry-high / paired / connected`**, which is legal under the
  same 3x3 arithmetic because paired-two-tone is 1,872 boards:

  - [resolved] **rainbow, dry high-card** - the eyeball board, 15.20% of flops, and the family the stage-2
    poker review named as most sensitive to the turn and river menu. `Kc7d2h` is the record's own
    `rainbow-dry-high` probe.
  - [resolved] **two-tone, paired** - keeps the paired structural gap the solver notes single out, 8.47%.
  - [resolved] **monotone, connected** - `9c8c7c`, 1.05%.

  That covers 24.72% of flops, keeps every suit texture, keeps paired, and adds the largest rank
  family. What it gives up is dry-low, which is the cheapest of the four to give up because the
  low-board signal a reader would look for - the range advantage moving to the caller - is the one
  most masked by a monotone board.

  **Two of the three then come free of a measurement the phase already owes, which is the second
  half of this finding.** `9c8c7c` in the single-raised pot is `matrix-03`: pot 5.5, stack 97.5,
  unfloored ranges `717f36499fb4` / `23642f5e22e7`, reduced menu `33 75 / 75 / 75`, converged to
  0.2845% of pot at iteration 240, digest `a1f9ae952c3f`. Solving that identical cell at the ruled
  menu gives the first and only measurement of what `66 125` does to a committed flop strategy, in
  the pot type the record says the effect is largest, with board, pot, stack and both ranges held
  and only the turn and river moving - which is verbatim the experiment decision 11 defers to stage
  6. Half of it is already paid for. And `Kc7d2h` is the single rainbow row the whole campaign
  estimate extrapolates from (6.23% of pot at 30 iterations, `56fd22b65bd9`), so solving it to
  target at the ruled menu tests the phase's largest unmeasured cost assumption at the same time.

  Marked as a blocker rather than a non-blocker because the sample is `frozen-into-data` by the
  ruling's own words, it is the only postflop data the gate will ever see, and the cost of changing
  it is zero today and a re-solve after stage 6.

  **Resolved 2026-09-10 by the coordinator, and the fix is the one this finding asked for.**
  Decision 6 item 4 now rules the rank axis `dry-high / paired / connected` against the unchanged
  suit split, giving rainbow-dry-high (`Kc7d2h`), two-tone-paired, and monotone-connected
  (`9c8c7c`). Monotone-dry-low is dropped and the item says so under "Knowingly left out", with
  ace-high connected named beside it. The second half of the finding is in as well: the item
  records that `9c8c7c` at the ruled menu *is* the controlled menu experiment decision 11 defers
  to stage 6, and that `Kc7d2h` is the single rainbow row the campaign estimate extrapolates from.
  The superseded "wants its own coverage" reasoning is quoted and struck rather than deleted, and
  the item states the monotone imbalance it leaves behind. Verified against decision 6 item 4 and
  round 8 of `stage-03-human-gate.md`, which read the whole rebuilt item rather than its diff.

---

[resolved] 2026-09-24 by MAINT-38: every blocker above that lacked a marker, bullet or bold paragraph, was audited by an independent lane, and each is shown closed by a fix or, for the c-bet cell, by Taylor's decision 21. A bullet that is evidence inside a finding is marked only because the queue reads it as a finding. Detail, finding by finding: `reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`.

## Non-blocker

### The bet menu, decision 11

- **`33 75` is the right flop pair, and the polar branch does not want more than 75 on the flop in
  either pot type.** Three-street geometric flop size, computed from the committed pots and stacks:
  **66.2% of pot in the 3-bet pot** (16.0 / 92.5, SPR 5.78) and **115.8% in the single-raised pot**
  (5.5 / 97.5, SPR 17.73). In the 3-bet pot 75% already exceeds geometric, so a flop overbet
  over-commits and buys nothing. In the single-raised pot no flop size in any plausible menu reaches
  115.8%, and reaching it is not a property equilibrium play wants at SPR 17.7 - 100bb single-raised
  solutions commit a small fraction of the stack on the flop, and flop overbets by the raiser appear
  at low frequency and on few textures (poker knowledge, not measured here). Taylor's own reason -
  "It's fine to not get full stacks in a single raise pot" - is the correct reason, and the record
  already carries it. `NO-MENU-IN-THE-RECORD-OFFERS-AN-OVERBET` owns the residual flop half.

- **The 75-to-125 jump does distort flop construction, and the way to see it is where each turn size
  sits relative to the two-street geometric rather than relative to the flop size.** Computed:

  | pot type | after flop | pot | behind | 2-street geometric turn size | ruled 66% is | ruled 125% is |
  |---|---|---|---|---|---|---|
  | single-raised | 33% called | 9.13 | 95.69 | **184.3%** | 0.36x geometric | 0.68x |
  | single-raised | 75% called | 13.75 | 93.38 | **140.9%** | 0.47x | 0.89x |
  | 3-bet | 33% called | 26.56 | 87.22 | **87.5%** | 0.75x | 1.43x |
  | 3-bet | 75% called | 40.00 | 80.50 | **62.1%** | **1.06x** | 2.01x |

  The same two sizes sit on opposite sides of geometric in the two pot types. In the 3-bet pot 66%
  is essentially the geometric size and the menu is well centred. In the single-raised pot both
  sizes are below geometric, so the flop's large size loses part of what it is for - setting up a
  turn that can threaten the stack - which pushes weight toward the 33% flop bet and toward
  checking. That is the opposite direction from the missing turn probe, which pushes hero's flop
  betting up. So under the ruled menu the two frozen distortions in the single-raised pot still pull
  opposite ways, which is the stage-2 review's conclusion reproduced with the ruled menu's own
  numbers: the sign cannot be argued and has to be measured.

  The one thing I would not conclude from this table is that `66 125` is a bad turn menu. It is a
  standard simplified turn pair for a 100bb single-raised pot (poker knowledge), and 66% is
  near-exactly geometric in the 3-bet pot. The finding is narrower: **relative to the `33 75` that
  every measured row in the record uses, the ruled menu deletes the turn's small size**, so the
  cheapest continuation of a 33% flop bet doubles in price - minimum defence against it falls from
  75.2% to 60.2% - and that is the specific channel by which the ruling changes the flop strategy it
  commits. The record says the menu is unmeasured on strategy; it does not say which lever moved.

- **In the single-raised pot the ruled menu's largest bet-only line invests 83.6% of the stack and
  the ruled menu never converts a bet to a stack-off there, but all-in remains reachable through
  raises and more of the ruled tree ends in one than of the pinned tree.** `75 / 125 / 125` invests
  81.47 of 97.5 and leaves 16.03 behind, which the record already states. Enumerating every
  reachable bet-raise-call amount sequence under `max_raises: 2` with the 2.5x multiplier and the
  0.85-of-stack snap, my own walk of the size arithmetic: single-raised, 73 of 179 terminal lines
  reach all-in under the ruled menu against 68 of 251 under pinned and 22 of 80 under reduced;
  3-bet, 54 of 95 against 59 of 134 and 19 of 42. **Zero flop conversions under every menu in both
  pot types**, which reproduces the stage-2 result at the ruled menu. As that review said of its own
  version of this table, a count of lines is tree breadth and not strategic content, so read it only
  as: the ruled menu is not a menu without a stack-off, and nobody should infer one from "it does
  not get full stacks in".

- **Two sizes per street was the right call and one of the two reasons put in front of it is wrong.**
  The record's reasoning for dropping 200% from the river is that "on the river a 200% bet is usually
  the stack anyway". Computed over every river node the ruled menu can reach:

  | line | river pot | behind | 200% of pot | all-in? |
  |---|---|---|---|---|
  | check / check | 5.50 | 97.50 | 11.00 | no |
  | 33 / check | 9.13 | 95.69 | 18.26 | no |
  | 33 / 66 | 21.18 | 89.66 | 42.36 | no |
  | 33 / 125 | 31.96 | 84.27 | 63.91 | no |
  | 75 / 66 | 31.90 | 84.30 | 63.80 | no |
  | 75 / 125 | 48.12 | 76.19 | 96.25 | **yes** |

  It is the stack in exactly one of six branches, the largest one. The branch where a river overbet
  is most valuable in real solutions - a small pot after checks, with the stack still behind and
  ranges polarised - is the branch where the claim is furthest from true (poker knowledge for the
  value; the arithmetic is mine). This does not reopen the ruling: two sizes per street is
  defensible on cost - the record's own adjacent datum is that the reduced tree is 750,792 action
  nodes against the pinned tree's 2,347,996, so the second turn and river size accounts for 68.0% of
  the action nodes - and Taylor chose it. What it means is that whoever runs the stage-6
  comparison must not inherit the river argument, because it will steer them to test the overbet on
  the turn only when the checked-through river is where the omission bites.

- **`66 125` against `66 200` is a clean experiment for the overbet question and it is not the
  experiment that settles flop construction.** It never moves the turn's small size, which is the
  lever that actually changed relative to every measurement in the record. The experiment that
  settles flop construction is the one described in the blocker: `9c8c7c` in the single-raised pot
  at the ruled menu, diffed against `matrix-03` at the reduced menu, everything else held. It costs
  one solve if run unfloored against the existing row - the ruled single-raised tree's node count is
  unmeasured, and if it lands near the pinned tree's the arena law in the record puts it around
  21 GB unfloored, which the machine note's new box has to carry anyway - or two cheap solves if run
  floored on both sides, the reduced side coming to about 3.1 to 3.5 GB by that same law. Either way it is cheaper than the
  deferred experiment and it compares the ruled menu to the one the phase's whole evidence base was
  measured on, rather than comparing two unmeasured menus to each other.

- **The missing donk is the smaller of the two distortions, and it is the one with a known sign.**
  Both reach a flop-only artifact through continuation values only; the flop node set is identical
  either way. The menu changes the price of every later action in every line; the empty donk list
  removes one option for one player in the subset of turn and river nodes where the other player was
  the previous street's aggressor. Published solver work puts the out-of-position turn lead at low
  single-digit frequency in most single-raised spots, concentrated on turn cards that swing the nut
  advantage to the caller (poker knowledge, no repo measurement exists). So: smaller in magnitude,
  one-directional in sign - hero's flop bet is never answered by a turn lead, so his flop betting
  frequency is biased up - which for a training artifact is the worse property of the two, because a
  systematic bias is what a student learns.

  **One consequence nobody has drawn: it distorts the out-of-position seat's own committed flop
  cells, and this phase commits them.** With no turn lead available after calling a flop bet, the
  out-of-position player's flop calling range is solved knowing it can never take the betting lead
  back on the turn. That makes flop check-calling worth less relative to check-raising and to
  leading the flop, both of which he does have. So the out-of-position seat's committed flop cells
  should be expected to check-raise slightly too often and check-call slightly too little, on top of
  the in-position seat c-betting too often. Same direction, compounding, and unmeasured.

### The 1%-of-pot commit bound, decision 4

- **At 1% of pot the aggregate frequencies are trustworthy to a couple of points and the per-hand
  mixes are not bounded at all.** Two separate quantities, and the record treats them as one.

  Aggregate first. If hero over-folds by `d` against a bet of `B` into a pot of `P`, every bluff
  villain can add gains `d x (P + B)`, so exploitability `e` caps `d` at `e / (m x (P + B))` where
  `m` is the mass of villain's range that becomes a profitable bluff. At `m = 0.30`, and because the
  bound is a percent of pot the answer is the same in both pot types:

  | bound | facing 33% | facing 75% |
  |---|---|---|
  | 0.3% of pot | 0.75 MDF points | 0.57 points |
  | 1.0% of pot | **2.51 points** | **1.90 points** |

  Against a correct minimum defence of 75.2% and 57.1%, two and a half points is a number a training
  artifact can publish. The percent-of-pot convention earns its keep here: it makes the slack
  identical across pot types even though 1% is 0.055 chips in the single-raised pot and 0.160 in the
  3-bet pot.

  Per-hand mixes are the other quantity and no exploitability figure constrains them. A hand is
  mixed precisely because the EV gap between its actions is near zero, and a frequency error on a
  hand whose actions differ by nothing costs nothing and so is invisible to a best-response bound at
  1%, at 0.3%, or at any target. That is not an argument against the 1% bound; it is the reason the
  frequency-convergence diff is the measurement the phase actually needs, which decision 7 already
  says and `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED` already owns.

- **The magnitude the record says is unmeasured is reachable from the curves it already commits, and
  it is an iteration count.** Reading each converged row's own `curve` block for the first check at
  which exploitability goes under 1.0% and under 0.3%:

  | row | board / pot | <1% at | <0.3% at | ratio |
  |---|---|---|---|---|
  | matrix-01 | 9c8c7c, 16.0 | 120 | 220 | 0.55 |
  | matrix-02 | Kc7c2c, 16.0 | 100 | 240 | 0.42 |
  | matrix-03 | 9c8c7c, 5.5 | 120 | 240 | 0.50 |
  | matrix-04 | Kc7c2c, 5.5 | 120 | 240 | 0.50 |
  | matrix-05 | Kc7d2d, 16.0 | 120 | 260 | 0.46 |

  **A cell committed at the 1% bound is a cell stopped at 42% to 55% of the iterations a converged
  cell runs**, median 0.50. That is the honest way to state what the bound accepts, and it is
  stronger than "three times the target", because frequencies settle after exploitability does: the
  cells the bound admits are stopped at roughly half the iteration count, in the regime where the
  mixes are least settled. Nothing here measures how much a mix moves between iteration 120 and 240,
  and that is the same one solve the phase already owes.

- **One concrete recommendation that follows, and it is stage-4 work rather than a re-ruling.** The
  committed sample is the only cell any human will ever look at. A sample cell committed at 0.9%
  would put the phase's single demonstrable artifact at the weakest accuracy the rules permit, at
  about half the iteration count of the rows the phase cites as evidence. Require the three sample
  cells to reach 0.3%, not merely 1%. The 1,200 cap and the sample's three boards make that a
  requirement the phase can meet or report failing, and it costs nothing to state.

- **A second, cheaper mitigation for the same risk.** For a cell between 0.3% and 1%, publish the
  action set and the direction rather than a precise mix, and reserve printed mixed frequencies for
  cells at or under the target. Decision 4 already requires the distribution of achieved
  exploitability to be reported; this is the same information used at the point where a reader would
  otherwise take a two-decimal frequency off a 100-iteration solve. It is a report rule, not a data
  rule, so it costs no re-solve and can be reversed.

### The range floor, decision 12

- **The floor is right, it is cheaper than the record says, and in combination with the ruled menu
  it changes no flop strategy that matters.** The mass figures are the stage-2 review's and I do not
  re-derive them. What the combination adds: the floor's cost is 0.199% of the defender's arrival
  mass in the single-raised pot, and the accuracy the phase already accepts is 1% of pot. The floor
  is an order of magnitude below the error the commit bound admits, so it cannot be the binding error
  in any committed cell. Class-level is not a granularity choice, it is forced - one suit-specific
  weight collapses the isomorphism group - and it is also harmless at this mass.

- **Nobody made the strongest argument for the floor, and it is the one that bears on this phase's
  largest risk.** Cost per iteration scales with action nodes times hands, and the floor leaves the
  action-node count identical at 2,347,996 while the hand count falls from 1131+679 = 1,810 to
  360+559 = 919. That is **1.97x**, so at fixed wall clock the floor buys 1.97 times the iterations.
  On the record's own late decay exponent of 1.0 to 1.3, 240 iterations becoming 473 takes a cell
  from about 0.30% of pot to about 0.13% to 0.15%. The floor is not only a memory lever; it is the
  cheapest convergence lever in the phase, and convergence is the thing decision 7 and the solver
  notes both name as unproven. That argument is stronger than the memory one and it is missing from
  decision 12, from the solver notes, and from
  `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`.

- **The 44 asymmetry is the only real cost and the stage-2 review has it.** I checked nothing new
  there and do not restate it.

### The price bands, decision 10

- **The geometry channel is already measured and I do not re-raise it. The range channel is the one
  the record says nothing bounds, and it is measurable off the committed chart.** Minimum defence
  against a steal to `r` with 1.5 dead is `1.5 / (r + 1.5)`. At the solved 2.5x that is **37.50%**,
  and the committed chart's `t6/d100/BB/BTN:raise@2.5` continues **36.65% of combos, 486.0 of
  1,326** - 0.85 points under the bound, which is what a rake-free out-of-position defence should
  look like and which makes minimum defence a usable proxy here rather than a bound quoted at
  something it does not describe.

  | actual open | min defence | vs the 2.5x cell | implied combos at the chart's own 0.977 ratio | vs 486 |
  |---|---|---|---|---|
  | 2.00bb (band floor) | 42.86% | +5.36 pts | 555 | **+14.3% wider** |
  | 2.10bb | 41.67% | +4.17 | 540 | +11.1% |
  | 2.25bb (corpus median) | 40.00% | +2.50 | 518 | +6.6% |
  | 2.50bb (solved) | 37.50% | 0 | 486 | - |
  | 3.00bb (band ceiling) | 33.33% | -4.17 | 432 | -11.1% |

  So the band admits a real defender anywhere from 11% narrower to 14% wider than the range the cell
  was solved against, and the extra combos are all at the bottom of the range, where hero's thin
  value bets and bluff-catchers live.

  **Weighted by what the corpus actually plays into a flop, the error does not average out.** Over
  the 194 corpus opens that reach a flop in a single-raised pot, the mean *signed* minimum-defence
  error is **+2.04 points** and the mean absolute error 2.97 points, range -4.17 to +5.36. Positive
  and systematic, because 84.6% of corpus opens are not 2.5bb and the distribution sits below it -
  2.00bb 17.6%, 2.10bb 7.1%, 2.25bb 42.8%, 2.50bb 15.4%, 3.00bb 8.8%. **The typical cell is being
  asked about a defender roughly 5.4% wider and weaker than the one it was solved against, every
  time, in one direction.** That confirms the direction the record asserts - hero c-bets and bluffs
  too little - with a corpus-weighted number, and it belongs in
  `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP`, which currently carries only the
  2.25-against-2.5 single case.

- **On poker grounds 20% is about five times too wide, and that is not an argument for narrowing
  it.** Inverting the same formula, holding the defender's minimum defence within 1 point of the
  solved 37.50% needs an open between 2.40 and 2.61 - a band of about **plus or minus 4%** of the
  price. A ±4% band covers a handful of corpus opens. So there is no width that is both poker-tight
  and coverage-adequate against one solved price, which is exactly the diagnosis the record reaches
  for the 3-bet half and explicitly declines for the open half ("the open half of this rule does what
  it was chosen to do"). It does what it was chosen to do on coverage; on poker it is the same defect
  as the 3-bet half, one order of magnitude smaller, and the same fix applies - a second solved open
  price, not a tolerance. The 99.0% coverage figure is a true statement about a rule whose accuracy
  it says nothing about.

- **The measurement that would bound this is affordable and nobody has proposed it.** Re-solve the
  preflop chart at `open_raises: [2.0]` and at `[3.0]` - phase 14's committed card puts a preflop
  re-solve at 1,900 iterations in 200.4 seconds, so both cost about seven minutes - export the big
  blind's defence range at each, and solve one flop board against each of the three ranges with
  board, pot and stack held to the 2.5x cell's. Diff the flop bet frequency. That is the only way to
  turn "hero c-bets too little" into a number, and it is cheaper than any other open measurement in
  the phase apart from the frequency diff.

- **The 3-bet half, measured on flop-reaching hands rather than on all 3-bets.** Of the 39 corpus
  hands that reach a flop in a 3-bet pot, **20 are inside the 6.0-9.0 band, 51.3%** - slightly
  better than the 47.1% over all 87 3-bets, and the same conclusion. Decision 3's annotation to sort
  on servable arrival frequency is right and the number it needs is below.

### Coverage, decision 3's ranking, and one thing nothing in the repo had counted

- **The flop-reaching query the contract says nothing computes, computed here.** Of the 499 corpus
  hands, **259 see a flop (51.9%)**. Of those flops, **194 (74.9%) come from a single-raised pot, 39
  (15.1%) from a 3-bet pot, and 26 (10.0%) from a limped or 4-bet pot**. **239 of 259 (92.3%) are
  heads-up**; 19 are three-handed and 1 four-handed. Hand this to whoever computes the ranking at
  stage 6 rather than re-deriving it from decision points.

- **The ceiling on what this artifact can ever answer, over the corpus, is three flops in four.**
  Taking the losses in order: 20 multiway flops the two-range solve cannot express at all (7.7%), 26
  limped or 4-bet flops the chart declares no price for (10.0%), and 19 three-bet flops outside the
  6.0-9.0 band (7.3%). **194 of 259 = 74.9% of corpus flops** are servable, before any limit from
  the covered line count. No figure like this exists anywhere in the record, and the phase's reports
  will otherwise state board coverage as 1,755 of 1,755 beside a preflop-line count, with nothing
  saying what fraction of real flops the pair of them reaches.

- **7.7% of that loss is multiway and it is structural, not a coverage choice.** GTOpen's postflop
  setup takes two ranges; phase 10's own decision 3 records that multiway has no exploitability
  proper. So the artifact cannot answer a three-handed flop at any coverage, and nothing in the
  decision list says so. Small, real, and the covered-set inventory should name it rather than
  letting it arrive as a refusal nobody predicted.

---

## Alignment

- `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` (exists,
  `backlog.yml:7441`). The entry carries the single 2.25-against-2.5 case. Extend it with the band's
  own range channel measured here: minimum defence 42.86% / 40.00% / 37.50% / 33.33% at opens of
  2.00 / 2.25 / 2.50 / 3.00, against the committed chart's own 36.65% and 486 combos at 2.5x, so the
  band admits a defender 11% narrower to 14% wider; and the corpus-weighted signed error over the
  194 flop-reaching single-raised opens is **+2.04 minimum-defence points**, one-directional. Also
  record the bounding measurement, which the entry says does not exist and which costs two preflop
  re-solves of about 200 seconds each plus one flop solve per range.

- `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` (exists, `backlog.yml:7505`). Add the
  flop-reaching figure, which is the one decision 3's ranking needs: **20 of 39 corpus 3-bet flops,
  51.3%**, are inside the 6.0-9.0 band, against 194 of 194 single-raised ones. So a covered 3-bet
  line is worth 7.7 points of corpus flops against a single-raised line's 74.9 divided among however
  many lines it takes.

- `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED` (exists,
  `backlog.yml:7267`). Add the iteration reading of the 1% commit bound: read off the committed
  curves, 1% of pot is reached at 100 to 120 iterations against 220 to 260 for 0.3%, so a cell
  committed at the bound is stopped at **42% to 55%** of a converged cell's iterations - median 0.50
  - which is the regime the entry says nothing has measured. The bound and the entry are the same
  question and neither cites the other.

- `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` (exists, `backlog.yml:7287`,
  already extended for the `66 125` menu). Add the two things this pass found about the ruled menu
  specifically: the turn sizes sit at 0.36x to 0.89x of the two-street geometric in the single-raised
  pot and 0.75x to 2.01x in the 3-bet pot, so one menu cannot be centred in both; and the ruled menu
  deletes the turn's *small* size relative to every measured row, which is the lever that reprices
  the 33% flop bet's continuation. The entry currently says the menu is frozen with no failure mode
  the phase can detect, which stays true - this is which part of the menu carries it.

- `NO-MENU-IN-THE-RECORD-OFFERS-AN-OVERBET` (exists, `backlog.yml:7583`). The entry is already
  re-pointed to the flop half. Add the river arithmetic, because the reason the river overbet was
  dropped will otherwise be inherited: 200% of pot is the stack in only 1 of the 6 river branches
  the ruled menu can reach, and it is furthest from the stack in the checked-through branch where a
  river overbet is most valuable.

- `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` (exists) and
  `A-TEXTURE-FAMILYS-CLASS-COUNT-IS-NOT-ITS-BOARD-SHARE` (exists, `backlog.yml:7248`). Both are the
  right entries for the fifteen-cell board-share table above, which extends the existing suit-only
  conversion to the rank axis: dry-high is 40.54% of flops and the sample's monotone dry-low cell is
  0.51%, the rarest of the fifteen.

- `A-SAMPLE-CHOSEN-FOR-SOLVE-EVIDENCE-GAPS-IS-NOT-A-SAMPLE-CHOSEN-FOR-DEFECT-DETECTION`
  (**proposed, not filed** - propose it only if the blocker's swap is refused, since it is the same
  finding). The general drift is beyond this phase: whenever a repo commits a small sample of a large
  generated set, the temptation is to pick the cases the evidence lacks, and the cases the evidence
  lacks are chosen by cost. A sample that exists so a human can see a defect must be picked for
  where a human holds an expectation, which is usually the commonest case rather than the rarest.

- `NO-FIGURE-STATES-THE-SHARE-OF-CORPUS-FLOPS-THE-ARTIFACT-CAN-ANSWER` (**proposed, not filed**).
  Board coverage will be reported as classes and preflop coverage as lines, and neither is the
  quantity a reader wants. Measured here over the 499-hand corpus: 259 flops, of which 194 (74.9%)
  are servable at the ruled key and bands - the losses being 20 multiway (7.7%), 26 limped or 4-bet
  (10.0%) and 19 out-of-band 3-bets (7.3%) - before any limit from the covered line count. Sibling
  of `NOTHING-MEASURES-POSTFLOP-ACTION-COVERAGE-AGAINST-REAL-BET-SIZES`, which measures the same gap
  on the postflop action axis; this one is the preflop-arrival axis and neither covers the other.

- `A-TWO-RANGE-SOLVE-CANNOT-ANSWER-A-MULTIWAY-FLOP-AND-NOTHING-COUNTS-THEM` (**proposed, not
  filed**). GTOpen's postflop setup takes two ranges and phase 10's decision 3 already records that
  multiway has no exploitability proper, so multiway flops are outside this artifact at any
  coverage. 20 of 259 corpus flops, 7.7%, are three- or four-handed. Structural rather than fixable,
  which is why it is an alignment item: what it needs is naming in the covered-set inventory so the
  refusal is one that was excluded rather than one that was forgotten, which is decision 3's own
  principle.

- `THE-RANGE-FLOOR-IS-COSTED-AS-MEMORY-AND-IT-IS-ALSO-A-CONVERGENCE-LEVER` (**proposed, not
  filed**). `docs/GTOPEN_SOLVER_NOTES.md`, decision 12 and
  `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` all price the 0.01 floor as a 2.0x memory saving
  with a cost in range fidelity. The action-node count is identical at 2,347,996 and only the hand
  count moves, 1,810 to 919, so at fixed wall clock the floor buys **1.97x the iterations** - which
  on the record's own decay exponent takes a cell from about 0.30% of pot to about 0.13% to 0.15%.
  The phase's largest unproven claim is convergence, and the lever it already ruled is a partial
  answer to it that nothing says out loud. Drift rather than a defect: the figure exists in the
  notes and is used for the wrong conclusion.
