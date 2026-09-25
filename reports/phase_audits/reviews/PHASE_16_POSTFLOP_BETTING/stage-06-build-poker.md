# Phase 16, stage 6: independent domain review of the build

Read-only. The reviewer wrote none of the work under review and is the domain reviewer: this note
judges the poker, not the code's fidelity to the contract. `stage-06-build-mechanical.md` is the
mechanical pass and is not duplicated here. `stage-04-tests-poker.md` is the previous domain
review; where I touch one of its findings I say which and either extend it or answer it, and I do
not re-file it.

Diff under review: `git diff 01f6ee403de777cd3629702c9c84df939d84630c HEAD` in
`poker-bot-worktrees/phase-16`, branch `phase/16-postflop-that-can-bet`.

Every number below is recomputed in this worktree and the method is stated beside it. Because
`data/artifacts/postflop/` does not exist, the strategy was exercised against a throwaway synthetic
sample built in a scratch directory outside the repo, with the three module constants pointed at it
in memory. Nothing was written under `data/`; `data/artifacts/` holds `preflop` only and
`git status` is clean.

## Blocker

**B1. Inside the two tolerances this phase ruled, the bot makes a flop bet that its own lookup then
refuses to name, and it is a quarter of the corpus rather than an edge case.**

The two bands compose and nobody composed them. Decision 10 admits an open of 2.0bb to 3.0bb onto an
`@2.5` cell, inclusive. The cell's bet is stored in **big blinds** and played as an absolute number
of chips - `PostflopBettingStrategy._amount` reads `cell.bet_sizes_bb` and does `min(round(size *
big_blind), all_in)`, with no reference to the pot in front of it - while the pot segment of the key
is the **nominal** 5.5bb. So a cell holding a 33%-of-pot c-bet at 1.815bb puts 182 chips in whatever
the real pot is. Decision 14 then matches a faced bet by **real** pot fraction inside 0.05.

Measured against the synthetic `@2.5` c-bet cell on `Kh7d2c`, hero BTN, BB having checked:

| open | real pot | the bot's c-bet | as a fraction of the real pot | the other seat's answer |
| --- | --- | --- | --- | --- |
| 2.0bb | 450 | 182 | 40.44% | **refused**, `postflop-betting:flop-size-off-the-committed-menu` |
| 2.25bb | 500 | 182 | 36.40% | matched at 33%, answered |
| 2.5bb | 550 | 182 | 33.09% | matched at 33%, answered |
| 3.0bb | 650 | 182 | 28.00% | matched at 33% **by 1e-17** |

The last row is not rhetoric. `abs(182/650 - 0.33)` evaluates to `0.04999999999999999`; at a pot of
652 it is `0.05085…` and the match fails. Decision 14 wrote down that 154 chips survives its
boundary by the same accident, and did not notice that the top of decision 10's price band lands on
the same knife.

**How often.** Counted over the committed corpus (`scripts/generate_postflop_betting_report.py::
load_committed_sample`, filtered to hands that saw a flop, had exactly one preflop raise and exactly
two live seats): 174 heads-up single-raised flops. All 174 opens sit inside decision 10's band.
**46 of them (26.4%) opened at 2.0bb or 2.1bb**, where the committed 1.815bb bet exceeds 38% of the
real pot and is refused; 18 more (10.3%) opened at exactly 3.0bb and survive only on the float above.

The poker of it, separately from the self-refusal. Across that band the bot's "33% c-bet" is really
anywhere from 28.00% to 40.44% of the pot it is betting into. The caller's required equity runs
`B/(P+2B)`: 17.95% at the bottom and 22.36% at the top against the 19.88% the cell was solved at.
Minimum defence, `1 - B/(P+B)`: 78.1% at the bottom, 71.2% at the top, against 75.2% solved. And the
SPR the cell assumes is 97.5/5.5 = 17.73, where the real spots run 98.0/4.5 = 21.78 down to
97.0/6.5 = 14.92, so the cell is played from 16% under to 23% over the depth it was solved at.
`THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` owns the range and geometry channels of
the substitution and does not own this: that entry is about a strategy solved against slightly wrong
ranges, and this is the bot putting a chip count in that no configuration in the record produced.

**The same shape twice more, both measured.**

*A raise the matcher cannot name.* `flop_action_line` matches a raise against `raise_fractions`,
which `load_library` derives only from raise entries in committed cells' **`flop_actions`** - that
is, from cells sitting at a node *after* a raise. A sample that commits a cell where hero can raise
but no companion cell facing that raise leaves `raise_fractions` empty. Built exactly that way, the
bot raised to 454 and then refused its own raise: `BTN facing a check-raise ->
postflop-betting:flop-size-off-the-committed-menu`.

*An off-menu committed size imports clean.* Nothing checks a cell's `bet_sizes_bb` against decision
11's `33 75` menu. A cell identical to the c-bet cell except `bet_sizes_bb: [3.0]` imports without
complaint; 3.0bb is 54.5% of its own 5.5bb pot, on neither menu entry, and 54.5% is refused by
`match_menu_fraction`. So the artifact can commit a bet that is off the menu the contract says the
solve was configured with, the bot will make it, and the bot will refuse it.

In all three the refusal code blames the *opponent's* sizing. A reader of the refusal inventory sees
`flop-size-off-the-committed-menu` and concludes a villain bet something odd, when the bet was the
bot's own.

What would close it, at stage 6, before any cell is solved: price a committed sized action as a
fraction of the **cell's** pot and convert it at the table against the **real** pot through
`menu_size_chips`; refuse at import any `bet_sizes_bb` that is not a menu entry of the cell's own
pot; and declare the raise menu on the cell rather than inferring it from which nodes happen to be
committed. Doing it after the campaign re-derives every cell, which is the argument decision 8's
2026-09-15 amendment already accepted for a smaller version of the same mistake.

**B2. The key can name a flop node no dealer can produce, the importer certifies it, and the
phase's own evidence loop is structurally unable to notice.**

`postflop_action_order` was added to `poker_core/positions.py` and is correct -
`postflop_action_order(6)` returns `('SB','BB','LJ','HJ','CO','BTN')`, blinds first and button last.
It is also **dead**: `grep -rn postflop_action_order` over `src/` returns the definition and nothing
else. No importer, no key producer and no strategy calls it.

Five impossible flop lines were written as cells and handed to `import_postflop_cell`. All five were
accepted and produced distinct spot keys:

- [resolved] hero `BTN`, flop line empty (`f:none`) - the button acting first on a flop;
- [resolved] hero `BB`, flop line `BTN:bet@33` - the in-position seat betting before the out-of-position seat
  has acted;
- [resolved] hero `BB`, flop line `BB:check` - hero asked to act twice in a row;
- [resolved] hero `BB`, flop line `SB:bet@33` - a seat that folded preflop betting the flop;
- [resolved] hero `BTN`, flop line `BB:check,BTN:bet@33` with hero's own bet already in - a node that is
  villain's turn, not hero's.

The first is the dangerous one and it is exactly the c-bet. A real table puts the BB's check on the
record, so the key a table derives for the raiser's flop is `f:BB:check`, not `f:none`. A campaign
that writes the raiser's cell as `f:none` - the natural reading of "the preflop raiser's flop,
nothing has happened yet", and the reading decision 8's amendment was written to correct one level
up - commits a cell that is never once reachable. Every c-bet would refuse under
`no-cell-for-this-spot` and the report's bet frequency would be a donk-bet frequency.

And the gate could not see it. `committed_spot_queries` rebuilds the table **from the cell**, so the
query it builds carries the same impossible flop line and matches it. Pointed at the `f:none` cell,
the report loop asked two queries and got `postflop-betting:weighted-draw:check` on both. The
strategy answers its own cells in the report and refuses the table.

What would close it: validate a cell's `flop_actions` against `postflop_action_order` at import -
every actor live, in order, hero's own turn at the end, no seat acting twice without a raise in
between. It is the flop analogue of the preflop walk `_closed_preflop_round` already does, and the
contract's own criterion that "a committed size that cannot be played is refused at import rather
than at the table" is the same principle applied to a different field.

[resolved] 2026-09-24 by MAINT-38: every blocker above that lacked a marker, bullet or bold paragraph, was audited by an independent lane, and each is shown closed by a fix or, for the c-bet cell, by Taylor's decision 21. A bullet that is evidence inside a finding is marked only because the queue reads it as a finding. Detail, finding by finding: `reports/phase_audits/reviews/MAINT_38_PHASE_16_SIGN_OFF/blocker-audit.md`.

## Non-blocker

**N1. Decision 14's bucket costs less than it looks, and the number that matters is not the
caller's.** `NO-FIGURE-REPORTS-HOW-FAR-A-MATCHED-BET-SAT-FROM-ITS-MENU-ENTRY` (existing) owns the
reporting half. The poker half, in numbers, on the 550-chip pot the ruling itself uses.

*The caller's side is small.* Calling B into a pot P needs `B/(P + 2B)`: 154 chips wants 17.95%,
181.5 wants 19.88%, 209 wants 21.59%. The bot plays the 19.88% strategy across all of it, so the
threshold is wrong by at most 1.93 points at the bottom and 1.71 at the top. Compare decision 9's
own cross-menu gap, 33% against 75%, which is 19.88% to 30.00%, 10.12 points: the within-bucket
spread of 3.64 points is 36% of the gap the sized key exists to prevent. The EV at stake is bounded
and tiny. A hand sitting exactly on the 33% threshold, called against 154, gains
`0.0193 x (550 + 2 x 154) = 16.6` chips, **0.166bb**, and that is the maximum over the window; a
hand at either edge of the window gains nothing, so the mean over the misplayed hands is under
0.083bb. Set beside the 1.815bb the bet itself risks, the caller-side cost of the ruled width is
second order and the ruling reads as sound on the half it examined.

*The bot's own side is larger and was not examined.* The raise is stored in big blinds too, so it
does not move with the bet it is raising. Measured against the synthetic raising cell (`4.5375bb`,
454 chips):

| faced bet | as % of pot | the bot raises to | which is |
| --- | --- | --- | --- |
| 154 | 28.00% | 454 | **2.95x** |
| 182 | 33.09% | 454 | 2.49x |
| 209 | 38.00% | 454 | **2.17x** |

Decision 11 configured the solve's raise as `2.5x`. Inside one bucket the bot plays 2.17x to 2.95x
and calls all of it the same cell. The price it lays villain moves with it: the final pot is 1458
chips in all three rows, and villain's call is 300, 272 and 245, so villain's break-even equity to
continue runs 20.58%, 18.66% and 16.81% - a 3.77-point swing, slightly wider than the caller-side
swing the ruling did price, and in the half of the bucket the ruling did not look at.

**N2. `postflop-fallback:fold-facing-bet-on-the-flop` is reported as taken over, and it is not, in
the only build `from_repo` produces.** `NOTHING-MEASURES-POSTFLOP-ACTION-COVERAGE-AGAINST-REAL-BET-SIZES`
(existing) is adjacent and does not cover this.

`CompositeStrategy.from_repo` still returns `postflop=PostflopFallbackStrategy()`
(`strategy/composite.py:75-84`). Nothing in `src/` constructs a composite around
`PostflopBettingStrategy`; the union type was widened and the default was not moved. The report's
line "Fallback refusal codes now unreachable for a committed flop spot" is derived by
`unreachable_fallback_codes`, which reads the fallback module's own constants and never asks which
component a composite actually holds. So the report states a takeover that the repo's own default
strategy does not perform. The poker consequence is the plain one: the bot a caller gets from
`from_repo` today still folds the flop without asking, which is the behaviour this phase exists to
replace.

**N3. The pot-odds river rule is not one rule with a known cost, it is two failures with opposite
signs, and the rate the report prints measures neither.** `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`
(existing, and the contract closes it) carries the uniform-deck concession; the numbers are mine.

The report prints "fired 12 of 12 river spots facing a bet (100.0%)" and says, correctly, that the
population came from the fallback report's enumeration and is heavy in hands ahead of the deck. What
it does not say is that the rule as coded **can only ever produce a call**: `_river` returns
`StrategyDecision("call", ...)` when equity beats the price and `REFUSE_NO_RIVER_SOLUTION`
otherwise. There is no fold. So a "firing rate" of 12 of 12 is a rate over a population whose other
outcome is the hand being voided, not a rate against folding, and it can never be read as a measure
of over-calling.

The cost of the uniform deck, measured. Board `AhKh7h2h3c`, a pot-sized river bet, so the price is
`to_call / (pot + to_call) = 1/3`. Hero holdings: 1,081. The rule calls with **709 of them
(65.6%)**. Give villain a real betting range - his top 25% by `evaluate_best` for value plus his
bottom 10% as bluffs, 378 of 1,081 holdings - and **453 of those 709 calls (63.9%) are losing**. The
mean overstatement of equity on a called hand is **24.99 points**, and the mean loss on a losing call
is **0.151 of the pre-bet pot**.

*The holding type it gets most wrong: the small flush on a four-flush board.* `5h6c` on that board
makes an A-K-7-5-2 heart flush. Counted against the uniform unseen deck with
`poker_core.evaluate_best`, its equity is **74.85%**; against the betting range above it is
**27.19%**, below the 33.33% price. A 47.66-point gap, and the rule calls. Every worse hand in the
same family behaves the same way, because on a four-flush board a single heart makes a flush and the
flush is ranked entirely by that one card, so "beats most of the deck" and "beats what bets" come
apart completely. The class beneath it is worse still without being a flush at all: 703 of the 1,081
holdings contain no heart, the rule calls with **331 of them (47.1%)**, and every one of those loses
to any heart villain holds.

Second, and not the same failure: `river_equity` counts a chop as half a pot, which is right, and on
`9h8h7d6c5s` every holding therefore reads exactly 50% and the rule calls with **1,081 of 1,081**.
Against a bettor who only ever bets a ten that is a disaster, and in a vacuum it is correct, because
calling a pot bet to chop returns 1.5 pots for one. The report's single "firing rate" cannot tell
those two boards apart.

**N4. The pot-odds price itself is right, and I checked it rather than assuming.**
`pot_odds_price` is `to_call / (pot + to_call)`, with `query.pot` already holding villain's bet
because every seat's `committed_total` is in it. That is the correct denominator: hero risks
`to_call` to win the whole final pot. No finding; recorded so the question shows as asked. The
orientation hazard the module's docstring names is real and is handled the right way round -
`holding_counts(("Ah","Ad"), ("Kc","7d","2h","9s","4c"))` returns `(884, 1, 105)`, wins first.

**N5. The three stage-4 poker blockers that were about behaviour are answered in the build, and one
of them well.** Extending `stage-04-tests-poker.md` B3 and B4 rather than repeating them.

B3 asked that the committed mixture be played rather than purified. `collapse` does a seeded
weighted draw with a hashed roll and the docstring gives the poker argument. Measured against a
synthetic cell: `5c4c` weighted `check=0.0, bet=1.0` bets, `QsJd` weighted `check=0.8, bet=0.2`
checks, and the `class_weights` vector travels on the decision detail so a reader can tell a pure
cell from a mixed one that drew alike. That is the right answer and it is better than the test
asked for.

B4 asked that a three-handed flop refuse. `_flop` refuses `more-than-two-live-players` before the
walk begins, and `completed_preflop_line` independently raises when fewer than two seats reach the
flop. Answered in code rather than in a report string.

## Alignment

**A1. Voiding a refused hand does not hide the seam's cost, it selects for the c-bets that worked.**
`A-VOIDED-TURN-SELECTS-FOR-THE-FLOP-BETS-THAT-WORKED` (**proposed**).
`A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` (existing) owns the seam itself
and `NO-FIGURE-SPLITS-THE-FLOP-BET-FREQUENCY-INTO-VALUE-AND-BLUFF` (existing) owns the missing split.
Neither owns this.

`stage-04-tests-poker.md` A2 answered "is a bot that bets and abandons worse than one that never
bets" with the arithmetic and concluded worse, paying 1.8bb a time. Now that the c-bet exists I can
say what the built code does to that answer, and it moves in both directions at once.

*In chips, at the only table this repo has, the donation is exactly zero.* `simulator/run.py`
returns `stack_deltas={seat: 0 ...}` and `pot_collected=0` on a refusal, so the flop bet is given
back along with everything else. The previous review had half of this ("the simulator voids the hand
at a refusal"); the consequence it did not draw is the one that matters.

*What is left is a filter, and it runs the wrong way.* A c-bet that gets **folded** to ends the hand
on the flop, settles uncontested and is recorded with a real stack delta. A c-bet that gets
**called** reaches the turn, refuses, and the whole hand is erased. Those are exactly the two
outcomes that decide whether a c-bet was good. A 33% bet risking 0.33P to win P breaks even as a
pure bluff at `0.33/1.33 = 24.81%` folds, so against correct defence 24.81% of the bot's c-bets are
recorded as wins of the whole pot and the other 75.19% leave no trace at all. The surviving record
of the bot's c-betting is a record of the times it worked, with no counter-observation anywhere in
it.

The contract's ban on a winrate or EV figure "over this artifact" is the right guard and it is not
this one: the hand histories themselves are committed, they carry `outcome=REFUSED` on the voided
hands, and nothing anywhere says that dropping those is not dropping a random subset. A later phase
computing anything over completed hands on a covered flop inherits the bias silently.

*And the pedagogical cost is worse than the chips one.* A student floating the bot's c-bet does not
get to punish the missing barrel; the hand vanishes instead. A bot that bet the flop and then checked
the turn down would at least teach the student to float. This one deletes the lesson.

**A2. The four situations the sample carries are not closed under the bot's own actions, so the bot
voids hands on the **flop**, one street earlier than the seam anyone accepted.**
`THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY` (existing, from stage 4) owns which boards are
in; `THREE-SAMPLE-FILES-CANNOT-HOLD-THE-SPOTS-THE-FROZEN-TESTS-NEED` (existing) owns the file count.
Neither owns closure. `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`
(**proposed**).

The four ruled situations are a caller first to act betting, a caller facing a bet raising, a
two-tone board separating a flush draw, and a raiser c-betting. Walk the flop tree they describe on
one board, measured against a synthetic sample holding exactly those situations:

- BB donks, BTN faces a donk bet: **refused**, `no-cell-for-this-spot`.
- BB checks, BTN c-bets, BB raises, BTN faces the check-raise: **refused**.
- BB checks, BTN c-bets, BB calls: turn, refused.
- BB checks, BTN checks: turn, refused.

Only the fold branches complete. The deepest flop line the sample can carry is check-bet-raise, and
the node after the raise has nobody in it. The sample cannot have all of it - four cells is four
cells - but the consequence is worth stating plainly because the phase documents its seam as being
at the turn and it is not: **every time the bot donk-bets or check-raises, the hand dies on the flop
against its own other seat**, and the donk cell is one of the four the sample is required to carry.
The seam decision 1 accepted is "bets a flop, then refuses every turn". What ships is "bets a flop,
then refuses the flop too, from the other chair".

**A3. What a reader of the report learns about flop play today is nothing, and what they would learn
with the sample committed is a claim about the bot answering itself.**
`A-SAMPLE-CHOSEN-FOR-SOLVE-EVIDENCE-GAPS-IS-NOT-A-SAMPLE-CHOSEN-FOR-DEFECT-DETECTION` (existing)
owns the sample-choice half. The report half is
`THE-BEHAVIOUR-SECTION-ASKS-THE-STRATEGY-ONLY-ABOUT-SPOTS-IT-CHOSE` (**proposed**); it extends
`stage-04-tests-poker.md` N5, which found the same self-selection in the tests, into the report,
where the same function is now the sole source of a published figure.

`reports/active/latest_postflop_betting_report.txt` as committed prints `spots asked: 0`, `bet
frequency: 0 of 0 asked`, `refusals counted: 0` and all sixteen refusal codes labelled `vacuous`.
Every behaviour figure in it is empty, correctly, because no cell is committed. That is honest and
it is also the whole of what a reader learns about the bot's flop play: nothing.

With the sample committed the section fills in from `measure_behaviour`, which iterates
`committed_spot_queries()` - tables rebuilt from the committed cells, asking about three hand
classes per committed action chosen by `_sample_classes` for weighing that action highest. So the
published bet frequency would be taken over spots the artifact chose, on boards the artifact chose,
with hands chosen to draw the action being counted. A reader would wrongly conclude they were
reading a bet frequency; what the number would actually say is that the cells round-trip. B2 above is
the sharp end of this - the same loop cannot detect a flop line that cannot happen - and the fix
there is not the fix here. What is missing is one independently constructed query per committed
situation, built from a table rather than from a cell, which is also the only thing that would have
caught B1.
