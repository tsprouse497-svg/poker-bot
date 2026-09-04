# Stage 6 build review - poker lane

Independent read-only review of the committed 249-spot chart. I wrote none of this work and
have not seen the other reviewer's notes. Every claim below carries the measurement that
produced it; anything I could not measure is labelled a suspicion.

Reference used throughout: `data/artifacts/preflop/sources/gtowizard_6max_nl25_100bb_preflop.json`,
already committed in this tree. It is a raked NL25 solve, so by the report's own rule (line 566,
"Reading wider than this file is therefore a floor rather than a pass") the rake-free chart should
read WIDER than it at every defence. It carries 25 spots the report never compares against:
10 vs-open spots for the non-big-blind seats, and 15 vs-3bet spots. Its `UTG` is this repo's `LJ`.

## Blocker

**B1. The over-folding the phase accepts as a big-blind defect is also present at 9 of the 10
merged spots the outside reference can reach, and nobody measured it. The packet may not ship a
defect list that names only the big blind.**

The report's accepted defect reads "the big blind over-folds against every opener", and it names
the cause as "the fit's own realization number for facing a bet in a single-raised pot, taken from
raked games where flatting genuinely is worse" (line 557). That same fit prices the 20 merged
spots. The report prints the merged family's band (`min 4.3160 max 14.9820`) with nothing beside
it, and prints the reference comparison for opens and big-blind defence only.

Chart defence is raise+call, combination-weighted over the arriving range. It reproduces the
report's own "defence" column at every one of these spots to three decimals, so this is the
phase's own number placed beside a reference the phase did not place it beside:

| spot | chart defence | raked reference | delta |
|---|---|---|---|
| HJ vs LJ open | 6.875 | 8.50 | **-1.63** |
| CO vs LJ open | 7.697 | 9.30 | **-1.60** |
| BTN vs LJ open | 9.980 | 10.80 | **-0.82** |
| SB vs LJ open | 9.984 | 9.40 | +0.58 |
| CO vs HJ open | 8.942 | 10.30 | **-1.36** |
| BTN vs HJ open | 10.716 | 12.30 | **-1.58** |
| SB vs HJ open | 10.128 | 11.00 | **-0.87** |
| BTN vs CO open | 11.959 | 13.90 | **-1.94** |
| SB vs CO open | 11.725 | 12.80 | **-1.08** |
| SB vs BTN open | 14.982 | 16.10 | **-1.12** |

Narrower than the raked reference at 9 of 10. Mean deficit 1.22 points on defences of 7 to 15
percent, so 10 to 17 percent relatively tight, and in the one direction the phase's own floor rule
says a rake-free solve must not go.

Two possible confounds both push the wrong way for the chart. The reference three-bets to 8bb
where the solve three-bets to 7.5, so the reference is paying a slightly worse price and should be
the TIGHTER of the two. From the small blind the reference three-bets to 11bb against the same
2.5bb open, a far worse price still, and it is wider anyway at three of its four small-blind rows.

Why this is a blocker rather than a non-blocker: it is not a request to re-solve or to change a
weight. It is that the packet, as written, tells a reader the over-folding is a big-blind
phenomenon with a big-blind cause, and the measurement above says it is a property of every seat
that has to answer an open. A reader who takes the defect list at face value would drill the
merged three-bet ranges as sound. The fix is to take this measurement, publish it beside the
merged band, and either extend the accepted defect to name the family or say in poker terms why
the same fit produces a true level here and a false one in the big blind.

**Lane R, 2026-09-04: [resolved]** The table is derived by the generator and published in
`## The derived chart against the GTO Wizard expectations` as ten `vs one open` rows carrying the
chart's defence, the raked reference's raise-plus-call, a per-row wider/narrower verdict and the
signed delta. The prose there says in terms that the same realization fit prices these spots as
prices the big blind, that the direction is the one a rake-free solve must not go, and that no
reader may take the defect list's naming of one seat as clearing the merged three-bet ranges;
pointers were added in `## The big blind's defence and flat, per opener` and `## The menu each
family publishes, and the merged flats` so a reader arriving at either lands on it. The defect
list stays at four rows, because a fifth is a ruling and
`tests/test_derived_chart_report_ranges.py` pins the count at four - the report says that
explicitly rather than leaving it implied.

**Every per-spot figure reproduced; two summary statistics did not.** All ten chart defences and
all ten reference raise-plus-calls reproduce to the digit, and narrower at 9 of 10 reproduces. The
**mean deficit is 1.1412 points over the ten spots**, not 1.22; over the nine narrower ones it is
1.3329, and I could not construct a reading that gives 1.22. The relative tightness is **6.94 to
19.12 percent**, not 10 to 17. The re-derived figures are what the report publishes, with the
widest shortfall (1.9413, at `BTN/CO:raise@2.5`) and the narrowest (0.8198) beside them. The
finding itself stands on the figures that did reproduce.

**B2. The "87 of the 181 kicker inversions are the wheel-ace premium and correct poker" claim is
made by a name-match with no gap test and no spot-type test, and at the first-in spots the poker
story it rests on does not exist. The packet may not claim it there.**

`kicker_split` in `scripts/generate_derived_chart_report.py:553` exempts a case whenever the
more-played hand is A5/A4/A3/A2, full stop. I re-ran the split independently and reproduce
87 / 29 / 65 = 181 exactly, so the counts are right. What the split does not carry:

- 69 of the 87 exempted cases have a gap of 50 points or wider.
- 53 of the 87 have the better ace played under 5 percent while the wheel ace is played over 95.

At a three-bet, squeeze or defence spot that shape is textbook and I agree with the ruling. A
suited wheel ace is the canonical three-bet bluff: nut-straight potential plus an ace blocker, and
picking A5s over A6s for that job is what a strong player does. `BTN/LJ:raise@2.5` at A6s 0.00 /
A5s 100.00 is correct poker and I would not touch it.

The first-in spots are different, and the exemption cannot tell them apart. At `t6/d100/LJ/rfi`,
with every cell at full reach:

    A8s  opens 0.9902
    A7s  opens 0.0011
    A6s  opens 0.0001
    A5s  opens 1.0000    A4s 1.0000    A3s 1.0000    A2s 1.0000

There is no polarization in a first-in raise. Nobody is selecting bluffs; you open the hands that
show a profit. A7s and A6s dominate A2s on kicker and on high card and give up only the A2345
straight, worth on the order of a point of equity. The reference opens all twelve suited aces at
1.00 from this seat. A 100-point notch across a one-point difference is a solve or extraction
artifact, and the wheel-ace sentence launders it as good play.

The relation machinery also under-counts the hole. Only the A6s-under-A5s step fires, because A7s
and A6s are both at zero and A7s-under-A5s is not an adjacent comparison. So the two-hand notch is
reported as one exempted case. The same seat carries a second notch no relation sees at all:

    55 opens 1.0000    44 opens 0.0059    33 opens 1.0000    22 opens 1.0000

Opening 33 and 22 pure while folding 44 pure. The reference opens 44 at 0.06, 33 at 0.01, 22 at
0.00, monotone. The LJ open is 18.74 percent against the reference's 17.49, so the range is close
to the right size with the wrong contents: A7s, A6s, K7s, K5s and KJo are folded pure where the
reference opens them pure, and 33, 22, 98s, 97s, 87s, 76s, J9s, J8s, JTo and T8s are opened pure
where the reference folds them. The same swap runs through the HJ, CO and BTN opens, always in the
same direction: offsuit broadways and high-card suited hands out, small pairs and suited
connectors in.

That directionality is a single-cause signature rather than noise. I cannot name the cause from
outside the solve, and I am not asserting one. What I am asserting is that the opening ranges are
the most-used and most-drilled surface this chart has, that they carry pure holes at A7s, A6s and
44, and that the packet's one sentence about them says the part that fires is correct poker. Fix
by gating the exemption on the spot type, or on a gap, and by measuring the RFI family against the
reference the way the opens' aggregate frequency already is.

**Lane R, 2026-09-04: [resolved]**, additively. The exemption itself is untouched, because
`KICKER_WHEEL_ACE = 87` and the 87 + 29 + 65 = 181 split are decision 53's ruled figures and
`tests/test_derived_chart_report_ranges.py` requires 87 in the defects section. What is published
instead is the split the exemption cannot see. A new `wheel_ace_cases()` returns the exempted
cases with the spot each was found at, and `## The four accepted defects, and what each costs` now
carries the gap row (**87 exempted, 69 at a gap of 50 points or wider, 53 with the better ace
under 5 percent and the wheel ace over 95** - all three reproduce your figures exactly), a row per
raises-faced bucket, and both first-in instances named with their weights and gaps. The prose no
longer says the exempted cases are correct poker full stop: it says the bluff-selection story is a
story about a spot where there is bluff selection, that a first-in raise has none, and that the
packet may not carry the first-in ones as correct poker. The defect row itself now reads "of which
87 are exempted as the wheel-ace premium - correct poker at 85 of them and a name match with no
poker story at the 2 first-in spots below".

**The by-spot-type split is much more lopsided than the blocker implies, and that is the number:**
of the 87 exempted cases, **2 are at first-in spots, 12 at facing-an-open spots, 73 at
facing-a-three-bet spots**. The two first-in ones are `t6/d100/LJ/rfi` (`A6s` 0.01 under `A5s`
100.00, gap 99.99 - your notch) and `t6/d100/CO/rfi` (`A6o` 0.00 under `A5o` 26.96, gap 26.96).
So the exemption launders two cases, not a family, and the larger part of the hole at those spots
is what no relation reaches at all.

**The RFI family is now measured against the reference per hand**, in the same expectations
section, as five `first-in` rows counting and naming every hand class whose weight differs by 50
points or more, split by direction. Your composition claim reproduces at that threshold: at LJ,
**8 folded here and opened there (A6s A7s K5s K6s K7s K8s KJo KTo)** and **13 opened here and
folded there (22 33 55 66 76s 87s 97s 98s J8s J9s JTo T8s T9s)**, and the same direction runs
through HJ, CO and BTN. Note that "the reference opens them pure" is loose for `K7s` (0.9691) and
`K5s` (0.9830); at a 99-percent purity threshold the LJ folded-here list is only A6s, A7s and KJo,
which is why the report publishes a 50-point difference threshold and says so.

**One claim did not reproduce.** "The same seat carries a second notch no relation sees at all"
is not right: the 44/33 step **is** seen. `relation_findings` puts
`('t6/d100/LJ/rfi', '44', '33', 0.59, 100.00)` among the 114 pair-ladder cases the defect list
already counts, and it is the only first-in pair-ladder case in the set. What is invisible is the
`A7s`-under-`A5s` step, because it is not an adjacent kicker comparison - which is the two-cells-
wide hole your alignment item A2 describes, and the report now says so where the exemption is
published.

## Non-blocker

**N1. The 106 are 42.6 percent of the spot count and 0.0164 percent of the decision weight, and
the packet must say which reading it is using.**

I confirm the finding as filed: 106 committed spots carry hero's own call in the action sequence,
83 whose predecessor is one of the 20 merged spots (published call weight 0.0), 23 whose
predecessor is not committed, 81 with an empty sizing class map, none in the big blind. My counts
match exactly.

What nobody put a number on is what they are worth. Summing `arrival_ppb` over the committed set
and over the 106:

    committed arrival total   6068788530 ppb
    the 106                       996262 ppb   = 0.0164 percent
    the 81 that price nothing     712000 ppb   = 0.0117 percent

`coverage_pct` at `scripts/generate_derived_chart_report.py:803` is arrival-weighted, so of the
98.5949 points of coverage the chart claims, the 106 buy 0.0162 of a point. Strip every one of
them out and the coverage claim reads 98.579 instead of 98.595.

So the two readings the coordinator asked me to separate come apart cleanly:

- **As the tree the bot plays**, these 106 are dead. The bot cannot reach them and the packet may
  not count them toward what the bot answers. But the overstatement is sixteen thousandths of a
  point, not 42.6 percent. The count framing is arithmetically true and materially misleading, and
  a packet that prints "42.6 percent of what ships" without the weight beside it is the more
  misleading of the two.
- **As a training reference a human is drilled on**, they are legitimate, and this is the reading
  the packet may claim. The range at each is the solve's own range for a cold-caller, and a human
  student does cold-call. Teaching a cold-caller's range at a spot reached by cold-calling is the
  right range at the right spot; the fact that this particular bot took a different branch upstream
  does not make the reference wrong for the student.

The one thing the packet may not do is use one sentence for both. The artifact's audit note says
"the bot never cold-calls" as the justification for the merge, and 106 spots downstream of a cold
call are committed under the same note. Say plainly that the merge is a bot-play rule and the 106
are a reference-only family, or drop them.

**N2. Never four-betting at the 106 is correct poker, and I checked rather than assumed.**

The 81 spots with an empty class map have a maximum raise weight of exactly 0.000000 over every
hand class; the other 25 max out between 0.0001 and 0.017 at any spot with non-trivial arrival.
Facing a three-bet after cold-calling, hero never four-bets with anything.

That is right, because the range is capped by construction. Arriving reach at the cold-caller's
own node:

    SB/CO:raise@2.5,SB:call,BB:raise@7.5     AA 0bp  KK 0bp  QQ 0bp  AKs 0bp  AKo 0bp  AQs 0bp
    BTN/LJ:raise@2.5,BTN:call,BB:raise@7.5   AA 0bp  KK 0bp  QQ 0bp  AKs 0bp  AKo 2bp  AQs 10000bp
    CO/LJ:raise@2.5,CO:call,BTN:raise@7.5    AA 0bp  KK 0bp  QQ 0bp  AKs 0bp  AKo 32bp  AQs 9993bp

Every premium three-bets at the previous node, so the flatting range that arrives has no nut hand
to four-bet for value and no reason to four-bet as a bluff into a range that has just three-bet
it. A capped range that calls and folds is the standard result. This is good poker and the packet
should say so rather than leaving it as an open question.

The ranges themselves also read correctly for the spot. `BTN/LJ:raise@2.5,BTN:call,BB:raise@7.5`
calls AQs, AJs, QTs, 99-66 pure and splits AQo 49/51 while closing the action in position getting
about 13-to-5, needing roughly 28 percent. That is a defensible defence, not a solver artifact.

**N3. The merged ranges read as real three-bet ranges, not as flatting ranges wearing a raise
label. The merge's problem is its level, not its shape.**

The widest, `SB/BTN:raise@2.5` at 14.98 percent: AA down to TT, 99-66, 55, 22, all suited aces, ATo-AKo,
KQs/KJs/KTs/QJs/QTs/Q9s/JTs/J9s/J8s/T9s/87s/76s. A small blind that plays three-bet-or-fold against
a button open at about 15 percent, with suited wheel aces and suited connectors as the bluffs, is
what a strong player would recognise, and merging is the right call in that seat specifically
because flatting out of position with the big blind behind is the line solvers cut.

The narrowest, `CO/LJ:raise@2.5,HJ:call` at 4.32 percent: AA down to TT and AKs/AKo pure, JTs 0.92,
76s 0.85, AQs 0.30, KQs 0.25, QJs 0.24, 99 0.15. Recognisable as a squeeze, though tight.

The intermediate `HJ/LJ:raise@2.5` at 6.88 percent is a textbook HJ-vs-UTG three-bet: premiums plus
A5s/A4s/76s/87s.

The one shape complaint is the pair notch that B2 and the accepted pair defect both touch:
`SB/BTN:raise@2.5` three-bets 55 and 22 pure and folds 44 and 33 pure, and `BTN/CO:raise@2.5` does
the same at 22 against 33 and 44. Inside a bluff-selection argument that is defensible for hands
the solve prices alike, and I am not reopening the ruled defect. It is worth one sentence in the
packet that the pair notch is visible in the two widest merged grids a student would actually read.

Suspicion, not a measurement: the three merged spots that face an open plus a cold call defend
4.32 to 6.48 percent, and I have no outside reference for that shape, so I cannot say whether a
4.3 percent CO squeeze against an LJ open and an HJ flat is too tight. Somebody should look.

**N4. The big blind's flat does not merely fail to move with the opener. It moves backwards.**

The report prints `flat spread 2.81 points` and calls the flat "nearly invariant". The reference's
own big-blind call frequencies are LJ 17.5, HJ 19.2, CO 22.6, BTN 26.5, SB 25.3: a 9.0-point
spread, monotone through the four non-blind openers. The chart's are LJ 19.63, HJ 20.98, CO 22.44,
BTN 21.09, SB 20.30. It rises to the cutoff and then falls for the button and the small blind, the
two widest openers of the five, where a correct chart's flat rises fastest.

That is stronger than the phase's own claim, and it points the same way, so it belongs in
`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT` rather than anywhere new. A direction reversal is a
different symptom from a flat line and is worth naming, because an invariant flat could be a
tolerance artifact and an inverted one cannot.

**N5. Hero's four-bet weight at the 219 three-bet-facing spots is 5 to 11 points below the raked
reference, uniformly, and worst against the blinds. Nobody printed it.**

The reference's 15 vs-3bet spots against the chart's, four-bet weight including its all-in leg:

    LJ vs HJ 3bet   chart 12.38  ref 22.20      CO vs BTN 3bet  chart 13.63  ref 23.50
    LJ vs CO 3bet   chart 12.00  ref 23.10      CO vs SB 3bet   chart  9.94  ref 19.30
    LJ vs BTN 3bet  chart 11.90  ref 24.20      CO vs BB 3bet   chart 10.16  ref 17.60
    LJ vs SB 3bet   chart 10.48  ref 17.50      BTN vs SB 3bet  chart  9.74  ref 16.10
    LJ vs BB 3bet   chart 11.41  ref 15.30      BTN vs BB 3bet  chart 11.29  ref 15.10
    HJ vs CO 3bet   chart 11.88  ref 22.70      SB vs BB 3bet   chart 18.54  ref 26.00
    HJ vs BTN 3bet  chart 12.82  ref 24.20
    HJ vs SB 3bet   chart 10.41  ref 17.90
    HJ vs BB 3bet   chart 11.85  ref 15.90

Below at 15 of 15, by 35 to 47 percent relatively. Total defence goes the other way, 44.6 to 63.1
against the reference's 28.4 to 39.0, wider at 15 of 15, which clears the floor. So the chart
answers a three-bet by calling far more and four-betting far less.

This is consistent with `PREFLOP-FOUR-BET-SIZE-IS-A-QUARTER-OVERSIZED` and I read it as that entry
showing up in the output rather than as a new defect. It is worth publishing because the report
says only that "a comfortable four-bet frequency here would show nothing at all" (line 632) and
then prints none. An uncomfortable one is informative in a way a comfortable one is not, and this
one is uncomfortable at every spot the reference reaches. It is also the number a later phase
taking up the four-bet family will want as its starting point.

## Alignment

**A1. This repo commits one outside reference and reads two families off it.**

`data/artifacts/preflop/sources/gtowizard_6max_nl25_100bb_preflop.json` carries full per-hand
strategies for 36 spots: 5 RFI, 15 vs-open, 15 vs-3bet, and the blind-versus-blind limp. The
report reads open frequency and big-blind defence off it and nothing else, and
`expectations/six_max_nl25_100bb.json` distils it down to exactly those two families before the
report ever sees it.

Everything in B1, N5 and the RFI composition work in B2 came from spots already in the tree that
nothing reads. This is not phase 14's to fix; the reference is raked, the comparison is a floor
rather than a pass, and building it into a gate is a phase of its own. But the pattern is that the
one measurement in this repo capable of catching a range that is uniformly wrong is being applied
to two of the five committed families, and the two it is applied to are the two that pass.

File as backlog: read the committed reference against every committed family it can reach, per
hand rather than per aggregate, and publish the per-hand disagreements as a measurement that gates
nothing. That is what turned up the LJ opening-range notch, and no relation in this phase can see
it.

**A2. The four published relations are all internal, and all four measure a grid against its own
other cells.**

The report says this plainly for the two counterfactual arms
(`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR`) and it is equally true
of the four ladder relations. The consequence I measured: a hole that removes two adjacent cells
at once is invisible, because a ladder only compares neighbours and both neighbours are zero. The
LJ opening range loses A7s and A6s together and the machinery reports one exempted case. Any
future relation family should include at least one comparison that spans a gap rather than only
adjacent ranks. Not this phase's to build.
