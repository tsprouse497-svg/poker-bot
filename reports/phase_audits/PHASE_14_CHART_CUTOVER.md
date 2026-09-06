# Phase 14 audit packet: Chart Cutover

Contract `docs/phase_contracts/PHASE_14_CHART_CUTOVER.md` · Decisions
`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md` (55 items) · Reviews
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/` (stages 1, 2, 3, 4, 6, 7, 8, 9, 10) · Report
`reports/active/latest_derived_chart_report.txt`, rewritten by the gate on every run · Lane: worktree
`~/projects/poker-bot-worktrees/phase-14`, branch `phase/14-chart-cutover`, opened from `main` at `ada5205`

Written for a reviewer who does not read code. **Every figure says where it comes from**: `report -> Section, "row
label"` names a section heading of the report and the row inside it, both greppable; a hyphenated capitalised id names
the `backlog.yml` entry that re-derives it. Nothing here was typed from memory, and where a stage-9 lane re-measured a
figure and got a different answer from an earlier document, the corrected figure is printed and the correction is said
out loud.

## What the committed set means for the trainee

**The bot answers 98.5949 percent of the preflop decisions it ever faces** (report -> The four-bucket node census,
"coverage"), from **249** spots derived from a GTOpen solve of the game this bot trains for: six-handed, 100 big blinds,
rake-free. It used to play from 86 spots taken out of a superseded reading, every priced one of them costed at a shove
the ruled config cannot produce.

What it will not answer, in the trainee's terms (report -> What this chart does not answer):

- **Everything from the four-bet on is refused**, 33,362 nodes. That is most of the tree and a little over one percent
  of the play, which is why the two readings look so far apart.
- **Every pot going multiway more than one time in ten is refused**, 348 nodes, and so are **the big blind's ten squeeze
  spots**, where it faces an open somebody has already called.
- **The bot never cold-calls outside the big blind.** At the 20 non-big-blind spots facing an open it publishes raise or
  fold only, because the solve's call weight is added into its raise (report -> The menu each family publishes, "family"
  rows). The big blind keeps fold, call and raise: it closes the action.
- Six-handed only, 100 big blinds only, symmetric stacks, no straddle, no ante, one opening price.

**98.5949 percent is decision mass, not spots and not hands**, weighting each node by how often it is actually reached.
A trainee meets cards rather than arrival weights, so the per-seat rate a student would feel is a different quantity
nobody has measured (`COVERAGE-IS-DECISION-MASS-AND-A-TRAINEE-MEETS-A-PER-SEAT-RATE`).

## Summary in plain language

The chart the bot plays has been replaced, and **the conversion itself is exact** - rows 1 to 7 of the checklist below
are the proof, and none of them is close.

**The honest headline is that a faithful conversion is not the same as good poker, and this phase measures the first and
not the second.** Nothing here gates on whether a range is good (decision 42), and the two counterfactual arms that do
gate are extraction checks: they prove the hand index survived the conversion and nothing more, and cannot see
over-folding, a mis-assigned actor or a cross-family inversion, which is what
`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR` says and why the contract requires it named
here. `GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE` stays **deferred** and this phase does not close it.

**The second headline is that the ranges the bot now plays are not uniformly sound, this phase knows where, and Taylor
ruled on 2026-09-05 to publish and ship rather than re-solve or soften.** The coverage, the prices and the opening
ranges are fit to be the reference. **The merged three-bet family, the four-bet ranges and the big blind's own three-bet
ranges all carry the same signature** and are not yet fit to drill a student on. That is set out below under "What this
packet does not bury", and it is placed first there because it is the finding a reader is most likely to miss.

## Pass/fail checklist for a non-coding reviewer

Each row is something a reader can check by opening the named file and finding the named row.

| # | claim | where | verdict |
|---|---|---|---|
| 1 | The four census buckets add to the export's own node count | report -> census; 249 + 33362 + 348 + 10 + 0 = 33969 | PASS |
| 2 | 249 nodes really are 249 distinct keys, checked both ways | report -> census, "artifact keys": invented 0, dropped 0 | PASS |
| 3 | The artifact reproduces byte for byte from the export | `convert_preflop_export.py --check`, inside `pytest_derived_chart` | PASS |
| 4 | Every committed cell matches the export | `pytest_derived_chart`; the 18,431 cells are stated in report -> The four accepted defects | PASS |
| 5 | Each merged spot's published defence equals the solve's raise plus its call | report -> The menu each family publishes; all 20 rows equal | PASS |
| 6 | Every price on a committed key is 2.5, 7.5 or 22.5 and never a shove | report -> census, closing paragraph | PASS |
| 7 | The retired chart is gone and the cutover ledger balances both ways | report -> The cutover ledger; 21 + 65 = 86, 21 + 228 = 249 | PASS |
| 8 | No spot with no action in front of hero carries a call weight | schema-enforced; `CHART-HERO-MUST-NEVER-LIMP` | PASS |
| 9 | Both counterfactual arms refuse the counterfactual on all ten partitions | report -> The two counterfactual arms; every row ends `asserted` | PASS |
| 10 | No partition was dropped and none fell below the five-spot floor | report -> The two counterfactual arms, closing paragraph | PASS |
| 11 | Later position opens wider; the big blind defends more against a wider opener | report -> The two orderings | PASS |
| 12 | The four relations were measured over every cell and published | report -> The four relations, four `relation` rows | PASS, and see 13 |
| 13 | The ladders are in order | report -> The four relations; 114, 7, 181 and 41 violations | **FAIL, accepted by ruling** |
| 14 | The big blind defends at a sound level | report -> The big blind's defence and flat | **FAIL, accepted by ruling** |
| 15 | The merged three-bet family plays the right hands | report -> expectations, "merged family" row: 62 against 63 | **FAIL, published and shipped** |
| 16 | The four-bet ranges pick bluffs that block | report -> expectations, "KTs or KJs" row: 0 of 15 against 10 of 15 | **FAIL, published and shipped** |
| 17 | Any of the above shows the ranges are good poker | nothing here does | **NOT MEASURED, by ruling** |

Rows 13 to 16 are failures that ship on purpose, each with a ruling behind it, and row 17 is the honest answer to the
question a reader most wants answered. Three further criteria had no instance to fire on - the two-price sizing schema,
the no-raise half of the sizing invariant, the jam-and-named-raise collapse rule - and are labelled vacuous wherever
reported, **never counted as checks that passed**.

## The exclusions, in poker terms

Each exclusion names a different way back, and a census folding two of them together would balance perfectly while being
wrong about which fix returns which.

**Everything from the four-bet on**, 33,362 nodes. Taken because a four-bet pot is 1.70 stack-to-pot, below every
observation the solve's flop-pricing fit has, so the source cannot price the flops those spots run to
(`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`). It returns when a later phase takes up the four-bet family.
**Hero's own shove lives only here**, which is why the jam canary that rejected the first cutover is kept against the
export rather than the chart: at `t6/d100/BB/SB:raise@2.5,BB:raise@7.5,SB:raise@22.5`, the most-played spot of the
withheld family, **AA jams 100.00** (report -> Hero's own jam). The aces take the whole stack there and the chart this
phase ships has no opinion about it.

**Every pot multiway more than one time in ten**, 348 nodes. Taken because GTOpen values a pot with three or more
players as the product of hero's equity against each opponent separately (`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`);
it returns when the source can price a three-way pot. The threshold is ten percent of a spot's decision mass reaching a
multiway flop, measured by walking the node to its leaves rather than by counting live players; the widest admitted is
**9.8642** and the narrowest refused **10.0234** (report -> Multiway exposure), so the rule bites at the boundary rather
than dividing an empty gap.

**Why that family is refused, checkably.** The report does not print this, so it is derived here and labelled a packet
measurement rather than a re-read of an artifact. Take `(1,1,1,0,0)` - the lojack opens to 2.5, the hijack and cutoff
both flat, the blinds fold - one of the 348. The big blind is asked for **1.5 big blinds into a pot of 9.0**, needing
`1.5 / (10.5 x 0.920) = 0.155` to break even, the 0.920 being the solve's positional factor for the out-of-position
seat of four. Take 65s:

    price offered                  1.5 into 9.0, break-even 0.155
    equity the model assigns 65s   0.027 by the solve's own walk, about 0.037 rebuilt from the committed table
    equity 65s actually holds      0.198, four-way, all-in
    fold the solve publishes       100.00 percent
**A hand that is a clear call at that price is published as a pure fold.** Across all 169 classes the understatement is
about eleven points at that node and about ten and a half at a three-way one, worst on the suited connectors whose whole
value is playing a multiway pot and near zero at the top of range, where a hand that beats everything pairwise also
beats everything jointly. Correcting only the equity and holding the tree, the ranges and the positional factor fixed
turns the solve's 96.7 percent fold there into a large defence. **That is the fix that returns the family**: a source
that can price a pot with three or more players in it. Three honesties. **The size of that counterfactual defence is not
published here**: two stage-9 walks put it at 36 and at 70 percent and the difference is unresolved, so only the
direction is claimed, and the direction is the one that argues for the refusal either way. **The true multiway equity is
not readable from any committed artifact** - the committed 169-by-169 table is exact and strictly pairwise, and
three-way equity does not decompose into pairwise terms, which is the defect itself - so it was simulated for this
packet at 100,000 deals per class, the engine validated against the repo's own hand evaluator and five cells of the
committed table. And `stage-04-cold-call-verification.md`'s worked example may not be cited here: it reads an export the
repo no longer holds, at a node not among the 348.

**The big blind's ten squeeze spots.** These passed the exposure clause **because** the big blind folds most of its
range there, so almost nothing of its mass reaches the three-way flop; its fold rate at those ten runs **84.9857 to
93.3284 percent, with 5 of the 10 under 90** (report -> Multiway exposure). The filter is blindest exactly where the
mispricing has already turned a call into a fold, which is why they are refused by a clause of their own
(`MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`). They return when the flats are repaired.

## The four accepted defects

These are defects. They are not caveats and not small print, and the report's own list refuses the word. Each ships with
the measurement it was accepted on (report -> The four accepted defects).

**1. The big blind defends too tight against every opener.** It defends **25.699 to 48.387 percent** where rake-free
solves are roughly 40 through 65 (report -> The big blind's defence and flat). The cause is the fit's own realization
number for facing a bet in a single-raised pot, taken from raked games where flatting genuinely is worse. **The
reference it is read against is a raked game** - `expectations/six_max_nl25_100bb.json`, GTO Wizard 6-max NL25 100bb
with rake - and rake is a toll on every contested pot, so **this chart reading wider than that file is expected rather
than contradictory, and is a floor cleared rather than a level confirmed**. It clears it at four of the five openers and
**not against the button, where it reads 36.653 against 39.430**, which is the one direction a rake-free solve is not
supposed to go. This repo commits no rake-free reference to read the level against at all
(`NOTHING-READS-THE-DEFENCE-LEVEL-AGAINST-A-RAKE-FREE-REFERENCE`). The cost is published **at both ends of the
realization range and never at a midpoint**, a midpoint being a measurement this phase did not take: at R = 0.65 it is
**0.10 to 0.70 bb per 100**, at R = 0.85 **8.76 to 13.04** - 12.5 to 130 times as much depending which end of each band
is read against which, and this packet publishes the four pairings rather than the single multiplier the report carried
until stage 9. The fingerprint is the flat, which barely moves with who opened - **2.81 points of spread against the
reference's 9.00** - and which falls rather than rises against the button and the small blind, the two widest openers
(`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`). **This defect is not confined to the big blind**; see below.

**2. The pair, kicker and raise-action ladders invert.** Measured on every cell at a one-point tolerance, gaps strictly
wider counted (report -> The four relations): pair ladder on play-not-fold **114** violations of 2,988 comparisons;
suited over its offsuit twin **7** of 19,422; row kicker ladder **181** of 32,868; and pair ladder **on the published
raise weight 41** of 2,988, **25 of them invisible to play-not-fold**. The fourth relation exists because the inversion
that halted this phase sits where both hands are played 100 percent and every play-not-fold reading is blind there
(`RAISE-ACTION-INVERSIONS-WERE-INVISIBLE-TO-EVERY-RELATION`).

**The wheel-ace cases are separated out.** Of the 181 kicker inversions, **87 are exempted** as the wheel-ace premium,
**29 have no poker story at a 50-point gap or wider and 65 below it**; the three parts add back to 181. A suited wheel
ace makes the nut straight and is less dominated than a middling suited ace, so choosing it is bluff selection, and
bluff selection is what a strong player does at a three-bet, a squeeze or a defence. **Of the 87, 85 sit where a raise
is already in and the exemption's argument applies. Two sit at first-in spots, where nobody polarises an opening range
and there is no bluff selection at all**. It reaches fewer than 85 even so: at 2 of them the wheel ace's whole weight is
a call, so there is no bluff to select either, and 3 of the 87 are offsuit rows where the suited story does not apply.
**The argument reaches 83.** The two first-in cases are named because a reader owed the claim is owed the instances:

    t6/d100/CO/rfi   A6o played 0.00   under A5o played 26.96   gap 26.96
    t6/d100/LJ/rfi   A6s played 0.01   under A5s played 100.00  gap 99.99

**This packet does not call those two correct poker.** Two further honesties: the exemption is a **name match only**
- it asks whether the more-played hand is A5, A4, A3 or A2 and tests neither the gap nor the spot, so "85 are
textbook" would overstate it and the true sentence is that at 85 the argument applies and this phase did not reopen
them; and the gap it is not testing is usually large, **69 of the 87 at 50 points or wider, and 53 with the better ace
under 5 percent while the wheel ace is over 95**.

**3. The merged flats play differently, not just differently labelled.** **165 cells move at 20 spots.** The range is
preserved to the basis point and the money is not: a hand that flatted for 2.5 now three-bets for 7.5 and can be
four-bet off it, where the solve would have seen a cheap flop
(`MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED`). Deleting rather than merging was unimplementable: at
**15 of the 20 spots, over 40 of the 165 moved cells, a hand's whole weight sits on calling**, and the solve barely
mixes - **93.20 percent of the 18,431 cells pure at 99 percent or better before the merge, 3.85 percent mixed below
90**. **The merge preserving the range is not the same claim as the range being right**, which is the next section.

**4. The four-bet is solved a quarter oversized**, at 22.5 big blinds where a standard sizing is nearer 18, and every
committed three-bet-facing spot prices hero's own four-bet through it (`PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED`).
In the output it is a price of **3.00x at all 15 spots the outside reference reaches against that reference's 2.09x to
2.69x**. A dearer four-bet is four-bet less often by construction, so part of the frequency gap in the next section is
price rather than strategy, which is why the frequency is published and not accepted as a fifth defect.

**The list of four is known to be incomplete.** Taylor ruled on 2026-09-04 to publish and defer the contract amendment.
A frozen test pins **the report's** defect list at exactly four rows (`tests/test_derived_chart_report_ranges.py:225`)
and the contract is at 300 of 300 lines (`PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP`), so extending the list is a
`contract-update` task and not something an implementer does. What the list is missing is named below.

## What this packet does not bury

### The chart three-bets and four-bets the wrong hands

**This is the largest finding of the phase, and Taylor ruled on 2026-09-05 to publish and ship it.**

At the 10 merged spots the outside reference reaches, under the report's fifty-point rule - a class counts when the two
grids' "puts money in" weights differ by 50 points or more, either direction - **62 cases are folded here and played by
the raked reference, and every one holds an ace or a king; 63 are played here and folded there, and not one holds
either** (report -> The derived chart against the GTO Wizard expectations, "merged family" row). Re-derived at stage 9:
**unanimous at each of the ten spots taken alone, and 100-to-0 at every integer threshold from 50 to 99**, so it does
not turn on where the line is drawn. Stated precisely, 62 and 63 are spot-and-class cases summed over ten grids; the
distinct classes are **17** folded-here, every one an ace or a king, and **16** played-here, not one of them either, and
the report names them spot by spot.

Standard theory three-bets the hands that block the opener's continuing range, the aces and the kings, and folds or
flats the connectors that block nothing. **This chart does the reverse at every one of those ten grids.** King-queen
offsuit is folded pure at all ten. A student drilled on them is being taught to fold king-queen offsuit to an open at
the hijack, the cutoff, the button and the small blind.

At the four-bet, the same shape. At the 15 spots of the 219-spot three-bet-facing family that the reference reaches,
**king-ten suited or king-jack suited - the reference's own four-bet bluff - four-bets above half at 0 of 15 spots here
against 10 of 15 there**, and the share of unpaired four-bet mass held by hands with neither an ace nor a king is higher
here at 15 of 15. At the family's heaviest grid the chart four-bets 86s, 96s, 97s, 98s and Q8s to 22.5 big blinds while
flat-calling every suited ace and every suited king it holds bar AKs and AQs. **Price does not explain it**: at the 6
spots where the two solves answer three-bets within half a big blind of each other the gap is as wide as anywhere. Filed
as `FOUR-BET-BLUFFS-ARE-CHOSEN-WITHOUT-BLOCKERS`.

**The tension a reader is owed rather than left to find**: this packet defends the wheel-ace exemption above on blocker
logic, and the four-bet family, which is 88 percent of this chart, selects its bluffs by the opposite rule. Both
statements are in this packet and only one of them can be how this chart picks a bluff.

**And the big blind's own three-bet ranges are not the exception two earlier documents took them for.** Stage 6 signed
the merged family off as shape-sound after reading three grids by eye, and stage 8 used the big blind as the control
that showed the signature was local. Neither holds. Measured at stage 9 over the five big-blind spots facing an open,
the share of unpaired raising mass in hands holding neither an ace nor a king is higher than the raked reference at **5
of 5** - 35.16, 33.55, 38.49, 42.37 and 48.11 against 13.85, 22.44, 25.99, 30.78 and 29.91. Against a small blind open
this chart three-bets **K8o, Q8o, T8o, 98o, T5s, 53s and 64s at 1.000 and 87o at 0.9997, while flat-calling KQo, KJo,
QJo and JTo at 1.000** - re-derived here from `action_weights` at `t6/d100/BB/SB:raise@2.5`. So the verdict this packet
carries is narrower than the one stage 8 wrote: **the chart is fit to be the reference for coverage and prices, and not
yet fit as the thing a student is drilled on wherever a raise is already in.** The top of every range is right and the
bluff half is chosen backwards. **What such a student would be taught wrong, in one list**: fold king-queen offsuit to
an open at ten spots; fold ace-king offsuit outright at 16 and more often than not at 33; fold queens about half the
time at five; three-bet offsuit junk out of the big blind against a small blind open while flat-calling king-queen and
king-jack offsuit; and pick four-bet bluffs that block nothing.

**The hand index was ruled out, not assumed away.** A reader's first thought should be that the chart was read wrong - a mis-indexed hand grid would produce exactly this
one-direction signature, and this codebase got an index wrong once already this phase. So it was measured. Averaged over
the committed grids each class appears in, the most-played are **AA and KK tied at exactly 1.000, then AKs 0.9949, QQ
0.9799, AKo 0.6709, JJ 0.5865, A5s 0.5718, JTs 0.5299**, and **48 classes are never played anywhere**, 45 offsuit and 3
suited. A permuted index scrambles that completely, so **the hand index is sound and the ranges are the solve's own** -
which is what makes the finding above a statement about what this phase ships rather than about how it read it. Two
stage-9 corrections to the stage-8 record on the way: it gave the top eight starting "AA, KK" without saying the two are
tied, and the least-played as "the eight worst offsuit trash hands" where it is 48 classes, three of them suited.

### 106 of the 249 committed spots continue a call the bot never makes

**42.57 percent by count, and 0.0164 percent by decision weight - a factor of 2,593** (report -> The arrival grain,
"downstream of hero's own call" and "the same family by arrival"). **State both or neither.** The count alone is the
more misleading of the two.

The predicate: a committed spot whose key records hero's own seat calling a single open with nothing of hero's own in
beyond the blinds - the one action the merge deleted. Re-checked at stage 9 over all 106: hero had never raised earlier
in the line, the call always came with exactly one raise in front, and hero is never the big blind, whose calls are
defence rather than cold calls.

**The packet must say which reading it claims, and it claims both, separately.** As the tree the bot plays, these spots
are dead and none of them counts toward what the bot answers. As a training reference a human is drilled on they are
legitimate, because the range at each is the solve's own range for a cold-caller and a human student does cold-call
(`COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY`). Stripping all 106 moves the coverage claim from 98.595 to
98.579. Phase 15 rules on whether its drill sampler draws from them.

### Never four-betting at those spots is correct poker, not a defect

**81 of the 106 publish nothing at all**: their menu offers hero a raise and no hand he can be holding there ever takes
it (report -> The three criteria with no instance, "sizing keys ... with an empty price list  81"). That is right, and a
later phase reading those zeros needs the sentence saying so or it will spend a stage repairing them. The arriving range
is **capped by construction**: at all 81, AA, KK, QQ and AKs arrive at **zero reach**, every premium having three-bet at
the node before, so the flatting range that arrives holds no value hand to four-bet and no reason to bluff into a range
that has just re-raised it. A capped range that calls and folds is the standard result.

**AKo is not at zero.** It arrives at **47 of the 81** spots, up to **6,619 basis points**, and never four-bets there
either - also defensible, flatting AKo in a capped range being a line rather than an absence. That is the limit of what
the measurement establishes: the four zero-reach classes are absent by arrival and not by choice, and the AKo row is a
judgment this packet states rather than a number that settles it.

**The over-folding is present at nine of the ten merged spots too.** The same realization fit prices every seat that has
to answer an open, and at 9 of the 10 merged spots the reference reaches, this chart is narrower than a solve that is
paying rake** (report -> expectations, "narrower at  9 of 10 spots"), mean shortfall 1.1412 points over all ten and
1.3329 over the nine. **A reader who takes the defect list's naming of one seat as clearing the merged three-bet ranges
is being misled.** The list naming one seat is known to be incomplete, for the reason given at the end of the defects
section.

**Where a premium is folded.** Aces and kings are never folded above 5 percent anywhere in the 249**, and at all 15 opener-versus-three-bet spots
they four-bet at exactly 1.000 with ace-king suited at 0.9978 or better. **Ace-king suited slips at six cells**,
published here because the report does not print them: over all 249 spots, at every cell arriving at half reach or
better, aces, kings and ace-king suited are folded above 5 percent at exactly **6 cells**. All six are ace-king suited
and all six at full reach. The worst folds AKs **28.14 percent** at `t6/d100/BB/LJ:raise@2.5,BTN:raise@7.5,SB:call`,
arriving at 35 parts per billion, where the big blind is asked 6.5 into 18.5 with the lojack still live behind, so it is
not even the closing call; the other five fold 9.59, 7.98, 7.26, 6.65 and 5.04 percent. Re-derived from the shipped
artifact in `SIX-CELLS-FOLD-A-PREMIUM-AND-THE-PACKET-NAMES-NONE-OF-THEM`. The cost to the bot is nil, well under a
thousandth of the committed set's decision mass; the cost is to a student, who meets a card and not an arrival weight.

**That read covers three hands and must not be taken as covering the premiums.** Under the same rule, **ace-king offsuit
is folded above 5 percent at 59 cells, folded more often than not at 33 and folded outright at 16**, and **queens fold
50.40 percent** at `t6/d100/SB/LJ:raise@2.5,HJ:raise@7.5,CO:call` while being asked 7.0 into 19.0, with a near-twin at
50.36 percent, both at full reach. So the true sentence is narrower than the one an earlier review wrote: the top two
hands are handled correctly everywhere, ace-king suited slips at six cells, and ace-king offsuit and queens were never
inside that read.

## What the gate proves, and what it does not

The gate is 47 commands and `check_gate_bite` proves **74 deliberate sabotages of the source all make it fail**. **The
closeout run first came back red at 46 of 47**, and what it caught is worth saying, because it is the one check that
judges the other 46. One sabotage survived: it switches off the single line deciding whether a refused report is
published anyway, and the test that should have noticed did not, because a report section added three commits earlier
crashed on the deliberately wrong input before the disabled gate could publish - and a crash looks identical to a
refusal to a test that asks only for a non-zero exit. Fixed at stage 10, with the committed report byte-identical
either way and the sabotage caught again. **The earlier run's record does reproduce**: an isolated lane rebuilt the
tree there and watched the sabotage die, so this was a real regression rather than a false record.
`A-CANARY-READS-A-CRASH-AS-A-KILL` carries what is still owed, which is an assertion on the refusal itself rather than
on the exit code, and that is a frozen-test change needing a ruling. The coverage this proof does and does not have: **Only 16 of the 74 mutations are new on this
branch** - the merge base carries 58, 16 were added and none removed, so 22 percent of the canaries attack this phase's
own work. **2,755 of the phase's 7,546 new lines under `src/` and `scripts/` sit in files no mutation names**, 36.5
percent across 19 files, the largest being the equity-matrix generator at +634 lines; the pair published earlier in this
phase, 2,740 of 7,175, was exact at `72efe9d` and is stale against the tree this packet ships with, and both are printed
so a reader can see which is which. **Nothing attacks `table_state/` at all** - no mutation names a path in that
package, and it appears only on the catching side, which proves those commands can fail on somebody else's mutation and
says nothing about the guards inside it. **29 of the 48 registered gate commands are named by no mutation**, or 28 of
the 47 the gate actually runs, both true of different sets; all 29 are generators or checkers, because the coverage
check reads test commands only. The 48 and the 47 differ by `freeze_tests`, the writer that rewrites the freeze lock,
whose `--check` sibling is what the gate runs, since a gate that rewrote the lock could never fail on it.

No stage-9 lane re-ran `check_gate_bite` - it plants live mutations and has no argument parser - so the 74-caught figure
is this phase's record and a count of the mutation file, not an independent re-measurement. The closeout gate run is
where it is re-measured.

## Decision outcomes

The record is 55 items with 38 dated correction notices. **Do not read it front to back to find out what the bot does**;
four restarts began that way. The live rule set is the ExecPlan's `Next Agent Bootstrap`, and the record's own header
carries the live and superseded tables.

Live and load-bearing: **44** the rule set as amended by 45 to 47; **46** the two filters and the ten percent threshold;
**48** the squeeze spots and the set at 249; **35** four-bet pots and deeper excluded; **32** cut by action, not by
spot; **33** the bot never cold-calls while opponents do; **45** flats merged rather than deleted; **34** the tight big
blind accepted with a published band; **41** and **47** the ladder inversions accepted; **42** the equity relation
published, gating nothing; **19** and **20** `realization: calibrated`; **49** and **53** the corrected figures; **50**
and **55** the fourth relation; **51** what ships; **54** the rank arm over every spot in its partition. Superseded, for
diagnosis only: 1, 17, 18, 22, 26, 28, 31, 37, 39, and the partially superseded traps 32, 33, 35, 40, 46, 50 and 53,
each carrying a ruling that stands and a figure that does not. **Every count in items 1 to 48 was taken over a set that
has since moved.** Decision 36 was ruled and not executed, on a coordinator error, and is back with Taylor.

Two judgment calls stopped for a human rather than proceeding on a default: **publish and ship the merged three-bet and
four-bet findings** (2026-09-05), and **publish the over-folding at the merged family, deferring the contract
amendment** (2026-09-04).

## Review findings

Every stage that changed human-written work has read-only review notes written by an agent that wrote none of it, under
`reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/`, indexed for stage 8 by `stage-08-review.md` and stage 9 by
`stage-09-audit.md`. The reasoning lives in the notes and is not restated here.

Stage 8 ran two independent reviewers - one mechanical, asking whether the phase's own record is true, and one domain,
the poker lens, asking whether the ranges are any good. The gate was already green at 47 of 47 with all 74 canaries
biting before either started, and **both found things anyway**: four blockers, each `[resolved]` with the commit that
closed it, being the artifact telling the trainee the wrong coverage and three sites saying nine spots where it is
fifteen (both `5e119cf`), and the two range findings above (`25f0d76`). Eight non-blockers and five alignment items,
every alignment item filed against an existing `backlog.yml` id. The two that change what a reader may conclude: the
report's hardcoded claim that the big blind folds 93 percent of its range at the squeeze spots against a measured 84.99
to 93.33 with 5 of 10 below 90; and that 9 of the 15 `vs one three-bet` rows set this chart's 7.5bb three-bet beside a
reference facing 11 or 13.5, so "total defence wider at 15 of 15" cannot mean what it is read to mean.

Stage 9 ran the same two lenses over the packet and found five more blockers, three of them in sentences stage 9 had
itself just written while correcting other people's; all are closed and `stage-09-audit.md` carries them. Its lanes are
in the ExecPlan's Delegation Plan. `backlog.yml` holds 219 entries, 193 deferred and 26 done.

## Commands and reports

| command ID | what it does |
|---|---|
| `pytest_derived_chart` | the selection, conversion, artifact and report tests over 11 files: 111 passed, 4 skipped, the skips being criteria the files label vacuous themselves |
| `generate_derived_chart_report` | writes the report every figure above cites, exiting non-zero rather than printing when one of them stops holding |

Both are declared in the contract frontmatter, registered in `COMMANDS` in `scripts/run_verify.py`, and carry a mutation
canary authored before the implementation: one proves a wrong artifact fails the command rather than being rendered, one
commits a spot above the exposure threshold. Reports to read beside this packet: `latest_derived_chart_report.txt`
(nearly every figure above), `latest_verify.txt` and `verify_results.json` (the gate),
`latest_preflop_strategy_report.txt` and `latest_spot_vocabulary_report.txt` (what the cutover moved downstream),
`latest_sample_comparison_report.txt` and `latest_refusal_inventory.txt` (the corpus and the refusals), and
`latest_quality_report.txt` (fact drift, mutation coverage, backlog integrity).

## Republished, gating nothing

**None of this is a verdict and none of it gates. The corpus verdict is phase 17's.**

- **The corpus comparison.** Refusals **fall** on both populations and the scored sample grows, which is the cutover
  buying coverage: Pluribus 430 of 502 decisions refused before against 27 of 502 after; humans 2,099 of 2,546 before
  against 112 of 2,546 after (report -> The corpus, before and after). The report said these **rose** until stage 9 - a
  sentence written when the committed set was 36 spots, false of the set this phase ships, and corrected here.
- **The pre-registered prediction and its band**, registered 2026-08-24 before any of this was measured: per opener,
  big-blind call agreement was to move in the same direction as that opener's defence delta, by a quarter to one times
  the delta in points (decision 9). **Its numbers are void and are not reprinted**; the form travels and phase 17
  re-registers the arithmetic. The deltas measured run -1.578 to -0.104 points, and the per-rate moves are published
  unpooled with their samples of 3 to 43 calls, a rate over three decisions being unable to resolve a band a point wide.
- **The price the corpus was played at.** 1,156 decisions faced exactly one raise at a median opening price of **2.25
  big blinds** against this solve's 2.5, so where the corpus opened cheaper the chart is systematically a little tighter
  than the spot deserves - a bias with a known direction, not noise.
- **What the measurement cannot separate.** **Rake, separated** - the committed solve is rake-free at the table.
  **Price, uncontrolled** - the lookup abstracts an opponent's open to the solved size. **Realization, uncontrolled** -
  the model underprices position and this phase accepts it. **Two of the three survive the cutover untouched, so a
  residual disagreement cannot be read as a defect in the ranges.**
- **The limped-decision-point count**, with the definition it was counted by, because the figure quoted elsewhere
  carries none and does not reproduce (`LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION`): under the rule "the first
  recorded action in the spot key is a call", **16 inventory rows and 52 decision points**. And over the 499 decisions
  both charts answer they disagree at **7**, two the derived chart continues and five the retired one did.
- **The equity relation**, the one measurement here that *asks* whether a range is good poker, which is not the same as
  measuring it - a measurement toward that gap is not the gap filled: it fires at **39 of 120 spots** where hero closes
  the action. **A correct chart fails it**, which is why it gates nothing and
  `GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE` stays **deferred**. Its 169-by-169 all-in matrix was computed
  here rather than taken from GTOpen, exhaustively rather than by sampling, with the eight checks its own card names.

## One number a reader can recompute by hand

**33,969 action nodes in the committed export.**

    the file        data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json
    the arithmetic  249 + 33362 + 348 + 10 + 0 = 33969

Add the four census buckets from the report's first section in the order printed and check the sum against that card's
`node_counts.exported`. If they do not add to it, a solved node has gone missing between the export and the report, and
**no other check in this phase would notice**.

## Known limitations and deferred items

**Nothing here claims the committed set is priced exactly.** The four-bet and multiway pots are refused because the
source cannot price them, and what ships is priced through a realization model fitted on raked games, so a rake-free
solve is not rake-free at its heads-up flop terminals (`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`). No vacuous
check is counted as a pass, neither arm passing is evidence the ranges are sound, and nothing here measures whether a
range is good poker.

**Six statements in the report were false and are corrected in this stage**, each found by a stage-9 read-only lane and
re-measured before it was touched. (i) The exposure rows were said to add to a hundred; they do at 236 of 249 and fall
short at 13, by up to 0.0268 points, because the walk drops mass reaching a node no hand class arrives at - the report
now publishes the shortfall and `EXPOSURE-WALK-DROPS-MASS-AT-NODES-NO-HAND-REACHES` carries the bound, that it can only
admit a spot it should have refused and none changes side here. (ii) "The merge turned 165 mixed cells pure" was wrong
twice: most of the 165 were already pure, some still are not, and the purity share moves 0.28 points, about 51 cells.
(iii) One sentence said all 87 wheel-ace exemptions are not a defect where the section around it says 85. (iv)
King-queen offsuit was said to be folded at ten "seats" that are ten spots at four seats. (v) The corpus refusal rate
was said to rise where it falls by about 95 percent on both populations, with the scored sample growing rather than
shrinking. (vi) The over-folding cost was given one multiplier of "about 125 times", which no pairing of the published
band ends produces; the four pairings run 12.5 to 130. **A seventh stands on purpose**: the multiway understatement of
"ten and a half points, and fourteen on the suited connectors" is hand-typed and nothing here re-derives it, filed under
`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`; a stage-9 simulation puts the connector figure nearer thirteen
three-way and fifteen four-way, and it ships in the artifact's notes too, so correcting it needs a rule rather than a
reword. **Two could not be fixed at all, both frozen-test docstrings** - the exposure closure with a tolerance nearly
twice today's worst shortfall, and `tests/test_derived_chart_report_ranges.py:218` still carrying "the merge turns 165
mixed cells pure" - because `tests/**` is outside `approved_scope`. Filed as
`A-FROZEN-TEST-DOCSTRING-ASSERTS-WHAT-ITS-TOLERANCE-ADMITS`.

**Committed documents disagree on three measurements, and a reader deserves to be told why.** The stage-8 poker note
reads the merged family as 60 and 28 where the report carries 62 and 63: the report uses one even-handed test, 50
points of daylight either direction, while the note sets fixed bars and in its second direction quietly tightens the
reference bar from "folds more than half the time" to "folds almost every time", so under its own stated rule its pair
is **60 and 58** and its 28 needs the unstated bar. **The poker conclusion is untouched under every rule tried.** The
second pair reads the same way: the four-bet no-blocker share is 19.78 percent over 134 spots in the report and 30.39
over 138 in the note, because the report leaves pocket pairs out and pools the family into one ratio while the note
counts pairs in and averages each spot's own percentage - four spots four-bet only with pairs, which is the whole gap.
The third is smaller and stands: the note says king-ten or king-jack suited four-bets above half at 9 of the reference's
15 spots where this packet says 10, its own table listing nine rows and omitting `SB_vs_BB_3bet`. The `backlog.yml`
entry that recorded the no-blocker pair as failing to reproduce is corrected here.

**A review note is a snapshot, and one carries a mechanism that can no longer happen.** `stage-01-contract.md` recorded
which two id-shaped literals the quality gate's citation check misread; a later edit of that note (`d097635`) rewrote
them into spaced forms, and since the checker's pattern requires a hyphen the note now describes something the strings
it names cannot produce. Correctly left unfixed, and already filed as stage-07 non-blocker N2.

**Three backlog entries the contract lists as closed are still deferred, deliberately.** `CHART-HERO-MUST-NEVER-LIMP`
was retitled rather than closed: the shipped artifact's five first-in spots carry zero cells with call weight and none
names `call` at all, but its diagnosis - that no schema rule forbids a limp, only the data - is still owed.
`BLIND-STRUCTURE-VARIANTS` and `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` keep their non-artifact halves.
`PHASE-14-CONTRACT-STATES-A-GROUP-GATE-THAT-DID-NOT-SHIP` moved to a `contract-update` task rather than closing here,
because the contract is at its cap. The contract's sweep sentence allows closed, restated, or moved forward with a
reason; these are the third.

**Explicitly not closed, accepted rather than fixed**: `GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE`,
`REALIZATION-MODEL-UNDERPRICES-POSITION`. **Moved to phase 17**: `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`,
`AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART`, `CHART-CANNOT-ANSWER-A-LIMPED-POT`,
`CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK`. **Filed by this phase and open**, and named where each is measured above:
`FOUR-BET-BLUFFS-ARE-CHOSEN-WITHOUT-BLOCKERS`, `SIX-CELLS-FOLD-A-PREMIUM-AND-THE-PACKET-NAMES-NONE-OF-THEM`,
`COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY`, `PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS`, the two
ladder entries, `RAISE-ACTION-INVERSIONS-WERE-INVISIBLE-TO-EVERY-RELATION`,
`MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED`,
`MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`, `NOTHING-MEASURES-HOW-MUCH-THE-SOLVE-MIXES`,
`REFERENCE-RANGES-HAVE-NO-CITED-SOURCE` and `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`.

**What went right, which belongs here too.** Aces and kings are never folded above 5 percent anywhere in the 249, and
the top of every range is right: against a lojack open the big blind three-bets AA KK QQ JJ TT 99 AKs AKo A5s KQs KJs
QJs JTs 87s 76s at 80 percent or better, the textbook shape, its total three-bet frequency of 6.07 percent being taken
over the 22 classes carrying any raise weight there - it is the bluff half, lower down and against the small blind, that
is chosen backwards. Defence against a three-bet is monotone in position, 58.96 and 63.09 against the two blinds who
play out of position against 57.94, 55.35 and 52.44 against the button, cutoff and hijack.
