# Stage 8 review - poker lane

Independent read-only review of the committed 249-spot chart before it becomes the reference
later phases are measured against. I wrote none of this work and have not seen the other
stage-8 reviewer's notes. I read the stage-6 poker review first and every finding below is
outside what it found; where I touch a family it already touched, I say so and say what is new.

The question I answered is the driver's: is this a chart a strong player would want a student
drilled on? Not whether it converted cleanly - it did.

Method, so every figure here is recomputable. All chart figures are read straight out of
`data/artifacts/preflop/six_max_100bb_rakefree.json`, combination-weighted by
`arriving_reach_bp` where a frequency is quoted. The weighting reproduces the report's own
published numbers to the digit - `t6/d100/LJ/rfi` 18.740, `t6/d100/SB/rfi` 54.299,
`t6/d100/SB/BTN:raise@2.5` defence 14.982, four-bet 11.41 at `LJ:raise@2.5,BB:raise@7.5`,
18.54 at `SB:raise@2.5,BB:raise@7.5` - so the machinery below is the report's, pointed at
cells the report never points it at. The outside column is
`data/artifacts/preflop/sources/gtowizard_6max_nl25_100bb_preflop.json` read raw, its `UTG`
being this repo's `LJ`. It is RAKED, so by the report's own rule (line 566) this chart reading
WIDER is a floor cleared and reading NARROWER is a direction a rake-free solve is not supposed
to go. Nothing I did re-solves anything or moves a weight.

## Blocker

**B1. At the merged three-bet family the chart folds sixty ace-and-king hands the reference
plays and plays twenty-eight hands with neither that the reference folds, with zero exceptions
in either direction. Stage 6 signed this family off as shape-sound. It is not, and the packet
currently tells a reader the opposite.**

Stage 6 N3 read three of the twenty merged grids by eye and concluded "the merged ranges read
as real three-bet ranges, not as flatting ranges wearing a raise label. The merge's problem is
its level, not its shape." Nobody measured the shape. The report measures this family against
the outside reference in aggregate only - the ten `vs one open` rows - and reserves the
per-hand read for the first-in family.

I ran the per-hand read the report runs on the first-in family over the ten merged spots the
reference reaches, at full-reach cells only (`arriving_reach_bp` > 9000), counting a hand as
folded here when the chart folds it above 90 percent and as played there when the reference
plays it above 50 percent:

| merged spot | folded here, played there | played here, folded there |
|---|---|---|
| `HJ/LJ:raise@2.5` | ATs A9s A3s KTs K5s AQo KQo | QJs JTs |
| `CO/LJ:raise@2.5` | ATs A9s A3s KTs K5s AQo KQo | QTs 87s |
| `BTN/LJ:raise@2.5` | A9s A6s A3s K5s KQo | 87s |
| `SB/LJ:raise@2.5` | A3s | QTs |
| `CO/HJ:raise@2.5` | A9s A8s A7s A3s A2s K7s K5s KQo | QTs JTs 87s 76s |
| `BTN/HJ:raise@2.5` | A9s A8s A7s A3s A2s K7s KQo | T9s 87s 76s |
| `SB/HJ:raise@2.5` | A9s A3s KQo | 87s 76s |
| `BTN/CO:raise@2.5` | A9s A8s A7s A6s A2s K9s KQo AJo KJo | J9s T9s 87s 76s 22 |
| `SB/CO:raise@2.5` | A9s A6s A2s K9s K6s KQo KJo | T9s 87s 76s |
| `SB/BTN:raise@2.5` | A7s A6s K9s K8s KQo KJo | J9s J8s 87s 76s 22 |

**60 classes folded here and played there. All 60 contain an ace or a king.
28 classes played here and folded there. All 28 contain neither.** Not 55 of 60 and not 24 of
28 - every single one, both directions. That is a single-cause signature and it cannot be read
as scatter.

`KQo` is folded pure at 9 of the 10 spots while the reference plays it 0.90 to 1.00. A chart
that folds king-queen offsuit to an open at the hijack, cutoff, button AND small blind is
teaching a student something actively wrong, and it is not one grid - it is the family.

The two cells a student would meet most often, both at full reach:

    t6/d100/CO/LJ:raise@2.5    arrival 174,514,269 ppb    menu fold/raise
      ATs   fold 0.9573  raise 0.0427        reference plays 0.95
      KTs   fold 0.9994  raise 0.0006        reference plays 0.58
      AQo   fold 1.0000  raise 0.0000        reference plays 0.99
      KQo   fold 1.0000  raise 0.0000        reference plays 0.90
      QTs   fold 0.0706  raise 0.9294        reference plays 0.00
      JTs   fold 0.0000  raise 1.0000        reference plays 0.00

    t6/d100/SB/BTN:raise@2.5   arrival 182,263,564 ppb    menu fold/raise
      K9s   fold 1.0000  raise 0.0000        reference plays 1.00
      K8s   fold 1.0000  raise 0.0000        reference plays 0.71
      KQo   fold 1.0000  raise 0.0000        reference plays 1.00
      KJo   fold 1.0000  raise 0.0000        reference plays 1.00
      Q9s   fold 0.0000  raise 1.0000        reference plays 0.15
      J9s   fold 0.0005  raise 0.9995        reference plays 0.00
      J8s   fold 0.0000  raise 1.0000        reference plays 0.00

Three-betting QTs and JTs from the cutoff against an under-the-gun open while folding ATs, KTs,
AQo and KQo has no story behind it. Bluff selection does not reach it: ATs, KTs, AQo and KQo
block the opener's continuing range strictly better than QTs and JTs do, and they hold more
equity as well, so the polarization argument the packet uses for the wheel aces points the
other way here. `SB/BTN:raise@2.5` is the grid stage 6 held up as "what a strong player would
recognise"; it folds K9s, K8s, KQo and KJo pure and three-bets J8s and 22 pure.

Three things this is NOT, each checked rather than assumed:

- **Not the merge.** The fold weight at these spots is the solve's own fold weight with the
  call branch still available - the report says so ("hero folds exactly as often as the solve
  folds"), and the merge only moves call into raise. The solve folds ATs at the cutoff against
  an under-the-gun open with a cold call on the menu.
- **Not the rake.** Rake makes a cold call worse, so the raked reference is the one that should
  be dropping the marginal aces and kings. The direction here is backwards, which is the one
  direction the report's own floor rule says a rake-free solve is not supposed to go.
- **Not the big blind's accepted defect.** I ran the same read over the five big-blind vs-open
  spots as a control: 19 folded here and played there, of which only 4 contain an ace or a
  king, and 27 the other way. The signature is absent exactly where hero keeps a call branch,
  which is what makes it a property of these spots rather than of the chart's general tightness.

What I am not asserting is a new cause. `PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS`
already names the mechanism - the export prices a cold call against a continuation structure
that punishes it. What that entry and the report say about its size is "opening and
three-betting therefore look slightly better than they are". The measurement is 60 hand classes
at 10 spots with no exceptions, including ATs at a 96 percent fold. "Slightly" is not
supportable and the packet should not carry it.

Why this is a blocker and not an alignment item: it does not ask for a re-solve or a weight
change. It is that the packet, as it stands, carries a stage-6 sign-off saying this family's
shape is sound, publishes the family's aggregate beside a reference and nothing else, and
describes the known cause as slight. A reader is being told to drill these ranges. The fix is
the one B1 and B2 took at stage 6 - take the measurement, publish it per hand beside the ten
`vs one open` rows the report already prints, and either extend what the defect list names or
say in poker terms why the contents are right at this family while the same read condemned the
contents at the first-in one.

[resolved] The per-hand read now runs over the merged family as the fourth block of `## The
derived chart against the GTO Wizard expectations`, a row per spot with the ace-and-king split
counted on both directions, the big-blind control row beside it, and prose saying plainly that
standard theory three-bets the blockers and this does the reverse, naming the three things it is
not; re-derived under the report's own fifty-point rule the counts come out 62 folded here and
played there with all 62 holding an ace or a king, against 63 played here and folded there with
none holding either.

**B2. The four-bet ranges at the 219 three-bet-facing spots - 88 percent of the chart - select
bluffs with no blockers. Nobody has measured the four-bet's composition at all; the report
publishes only its frequency, and hands that frequency forward as where a later phase starts.**

The report declines to publish a band over this family and prints one row per spot carrying the
four-bet weight, total defence and the four-bet as a multiple of the three-bet. Stage 6 N5
found the frequency is below the reference at 15 of 15. Neither asks which hands are doing the
four-betting.

The reference's four-bet bluff at these spots is a king-blocker hand:

| spot | chart KTs / KJs four-bet | reference KTs / KJs |
|---|---|---|
| UTG_vs_HJ_3bet | 0.000 / 0.000 | 0.855 / 0.836 |
| UTG_vs_CO_3bet | 0.000 / 0.000 | 0.797 / 0.937 |
| UTG_vs_BTN_3bet | 0.000 / 0.000 | 0.964 / 0.924 |
| UTG_vs_SB_3bet | 0.001 / 0.000 | 0.661 / 0.546 |
| HJ_vs_CO_3bet | 0.000 / 0.000 | 1.000 / 0.982 |
| HJ_vs_BTN_3bet | 0.000 / 0.000 | 0.984 / 0.977 |
| HJ_vs_SB_3bet | 0.000 / 0.000 | 0.998 / 0.788 |
| CO_vs_BTN_3bet | 0.000 / 0.000 | 0.963 / 0.989 |
| CO_vs_SB_3bet | 0.000 / 0.000 | 0.784 / 0.010 |

**KTs or KJs four-bets above 50 percent at 9 of the reference's 15 spots and at 0 of the
chart's 15.** Across all 15 the chart's KTs and KJs four-bet weight is 0.000 except one cell at
0.001 and one at 0.013.

What carries the load instead. Excluding pairs entirely, so that the ruled pair-ladder defect
cannot be doing the work, the share of each spot's four-bet mass held by hands containing
neither an ace nor a king:

    UTG_vs_HJ_3bet    chart 40.2%   ref  0.0%      CO_vs_BTN_3bet   chart  7.3%   ref  0.9%
    UTG_vs_CO_3bet    chart 48.5%   ref  0.0%      CO_vs_SB_3bet    chart 50.1%   ref  0.0%
    UTG_vs_BTN_3bet   chart 51.8%   ref  0.0%      CO_vs_BB_3bet    chart 36.2%   ref  0.0%
    UTG_vs_SB_3bet    chart 22.3%   ref  0.0%      BTN_vs_SB_3bet   chart 18.3%   ref  3.6%
    UTG_vs_BB_3bet    chart 24.9%   ref  0.0%      BTN_vs_BB_3bet   chart 16.6%   ref  0.0%
    HJ_vs_CO_3bet     chart 43.8%   ref  0.0%      SB_vs_BB_3bet    chart 38.6%   ref 11.7%
    HJ_vs_BTN_3bet    chart 26.0%   ref  0.0%
    HJ_vs_SB_3bet     chart 40.6%   ref  0.0%
    HJ_vs_BB_3bet     chart 39.6%   ref  0.0%

Higher at 15 of 15. The reference's non-pair four-bet range is pure ace-and-king hands at 13 of
the 15 spots. Over all 219 three-bet-facing spots, 138 of which carry any four-bet mass at all,
the arrival-weighted share of four-bet mass in hands with neither an ace nor a king is
**30.39 percent**, and 52 spots sit above 25 percent.

The worst grid is also the family's heaviest, at 42,992,724 ppb of arrival:

    t6/d100/SB/SB:raise@2.5,BB:raise@7.5     four-bets 18.54, defends 44.64
      four-bets to 22.5 pure:   98s 97s 86s   96s 0.991  J7s 0.985  T7s 0.990  Q8s 0.992
      four-bets to 22.5 pure:   KJo 0.975
      calls 7.5 pure:           AJs ATs A9s A8s A7s A6s A5s A4s A3s A2s KQs KJs KTs 76s
      folds pure:               65s

Four-betting J7s, T7s, 86s and 96s to 22.5 big blinds while flat-calling every single suited
ace and every suited king, and folding 65s outright, is bluff selection run backwards. A
four-bet bluff is chosen because it blocks the hands that continue - the aces and the kings -
and J7s and 86s block nothing at all. The same shape recurs at the lighter spots: at
`t6/d100/LJ/LJ:raise@2.5,BB:raise@7.5` 87s four-bets 0.9477 while 76s calls 0.9765 and A3s and
A2s call pure, and at `t6/d100/LJ/LJ:raise@2.5,CO:raise@7.5` 87s four-bets 0.997 while A4s, A3s
and A2s all call pure.

Price does not explain it. At the six spots where the reference's own three-bet is 8bb against
this chart's 7.5 - UTG_vs_HJ, UTG_vs_CO, UTG_vs_BTN, HJ_vs_CO, HJ_vs_BTN, CO_vs_BTN - the two
are being charged within half a big blind of each other, and the chart's non-pair no-blocker
share is 40.2, 48.5, 51.8, 43.8, 26.0 and 7.3 percent against the reference's 0.0, 0.0, 0.0,
0.0, 0.0 and 0.9.

Why this is a blocker. The packet already argues bluff selection in poker terms, and argues it
with blockers: the wheel-ace exemption is defended as "nut-straight potential plus an ace
blocker, and picking A5s over A6s for that job is what a strong player does at a three-bet".
The chart's own four-bet, at the family that is 88 percent of it, does the opposite of that at
15 of 15 measurable spots, and the packet publishes a frequency beside it and calls that
frequency "the number a later phase taking up the four-bet family starts from". A later phase
starting from a frequency, with the composition unmeasured and pointing this way, starts from
the wrong number. The fix is additive and needs no re-solve: publish the four-bet's composition
beside its frequency, and stop letting the wheel-ace bluff-selection argument stand in the same
packet as a four-bet range that has no blockers in it.

[resolved] The four-bet's composition is now published beside its frequency as the fifth block of
`## The derived chart against the GTO Wizard expectations`, a row per spot carrying the KTs/KJs
weight and the unpaired no-blocker share against the reference's, the figure over all 219 spots,
the six spots priced within half a big blind, the heaviest grid's own raise and call lists, and
prose naming the tension with the wheel-ace exemption the defects section argues on blocker
logic; re-derived, KTs or KJs four-bets above 50 percent at 0 of 15 spots here against 10 of 15
there, and the no-blocker share is higher here at 15 of 15.

## Non-blocker

**N1. Nine of the fifteen `vs one three-bet` rows put this chart's 7.5bb three-bet beside a
reference facing 11 or 13.5, and the report reads the resulting width as a floor cleared.**

The report prints "total defence wider at 15 of 15 spots", "the defence column clears the floor
at every spot", and attributes the price confound to one thing only - the four-bet as a
multiple of the three-bet. The bigger price difference is the three-bet itself. Read off the
reference's own `action_path` fields:

| three-bettor | chart three-bet | reference three-bet | equity hero needs to continue |
|---|---|---|---|
| HJ, CO or BTN | 7.5 | 8 | chart 32.26% / ref 33.33% |
| SB | 7.5 | 11 | chart 32.26% / ref 36.96% |
| BB | 7.5 | 13.5 | chart 32.26% / ref 40.00% |

Eight of the fifteen rows are a blind three-betting, so the reference's opener is being asked
for 8.5 or 11 more where this chart's opener is asked for 5, needing 4.7 to 7.7 points more
equity. The fifteenth, `SB_vs_BB_3bet`, is not the same tree at all: the reference's small
blind opens 3.5 and faces 10.5. That is where the doubled defence comes from - 58.02, 58.71,
57.04 and 58.96 against 29.30, 28.40, 30.20 and 31.10 - and it is not rake and not the ranges.

The report's general caveat is intact; what is missing is per-row. A reader arriving at "wider
at 15 of 15" reads a floor cleared when at eight rows the comparison cannot establish a floor,
and the four-bet gap the report hands forward is confounded by the same mismatch on top of the
four-bet ratio it does name. The fix is one column: print the reference's three-bet size beside
each row. It does not change a finding, it changes what the finding can be read to mean.

**N2. What is right, said plainly, because the packet is entitled to it.**

- **No premium is mishandled anywhere.** Over all 249 spots and every cell at 50 percent reach
  or better, AA, KK and AKs are folded above 5 percent at exactly 6 cells out of thousands, all
  of them AKs and all at spots arriving below 300 ppb. At all 15 opener-versus-three-bet spots
  AA and KK four-bet at exactly 1.000, AKs at 0.9978 or better, and QQ never folds - it splits
  between four-betting and flatting, 1.000 four-bet at 8 of the 15 and a pure call at
  `LJ/LJ:raise@2.5,SB:raise@7.5`, which is ordinary poker rather than a hole. The value half of
  every four-bet range is right; B2 is about the other half.
- **The big blind's three-bet ranges are recognisable.** Against a lojack open the big blind
  three-bets AA KK QQ JJ TT 99 AKs AKo A5s KQs KJs QJs JTs 87s 76s at 6.07 percent - premiums
  plus a wheel ace plus two suited connectors, which is the textbook shape. Against the small
  blind it three-bets 28.09 percent with a wide offsuit and suited-connector bluff wing. Both
  are hands a strong player would recognise.
- **The defence ordering against a three-bet respects position.** Hero defends 58.96 and 63.09
  against the two blinds, who will be out of position for the rest of the hand, and 57.94,
  55.35 and 52.44 against the button, cutoff and hijack, who will not. Monotone in the right
  direction at all five of the lojack's spots.
- **The big blind's defence family does not carry B1's signature**, measured as the control
  above. Whatever is wrong at the merged spots is not a property of the chart everywhere.

**N3. One cell folds AKs 28.1 percent, which nothing in the chart should do.**

`t6/d100/BB/LJ:raise@2.5,BTN:raise@7.5,SB:call` puts AKs at fold 0.281 with reach 10000. The
big blind is being asked for 6.5 into a pot of 18.5 - the lojack is still live behind, so this
is not the closing call, but nothing about that makes ace-king suited a fold at nearly three to
one. It arrives at 35 ppb so it costs the bot nothing, but a student drilling a grid meets a
card and not an arrival weight. Worth one line in the packet's own voice rather than leaving it
for a reader to find.

## Alignment

**A1. Every relation this repo owns compares within a row, a column of pairs, or a suited
twin. Nothing compares across the high-card column, and a relation that does fires 179 times.**
File under `A-RELATION-THAT-ONLY-COMPARES-NEIGHBOURS-CANNOT-SEE-A-TWO-CELL-HOLE`, which records
the same structural gap from the adjacency side.

The four published relations are the pair ladder, the pair ladder on the raise weight, suited
over its offsuit twin, and the row kicker ladder - fixed high card, walking the kicker. None of
them compares K9s against Q9s, or ATs against QTs: same low card, same suitedness, different
high card. That is the direction B1's instances live in and no measurement in this phase can
see them.

I built the relation the disciplined way rather than asserting it. First I validated it on the
outside reference: of the 153 same-low-card, same-suitedness, higher-high-card pairs the
reference exercises at 10 or more of its 36 spots, **99 are never violated by the reference by
more than 10 points at any spot**. Those 99 are the pairs where the poker claim is not mine but
the reference's. Scoring only those 99, only at cells where both hands are at 90 percent reach
or better:

    chart violations                179
    at a gap of 50 points or wider  131
    distinct committed spots         59

Worst by arrival: `SB/BTN:raise@2.5` K9s 0 under Q9s 100 and K9s 0 under J9s 100;
`CO/LJ:raise@2.5` KTs 0 under QTs 93 and ATs 4 under QTs 93; `BTN/CO:raise@2.5` K9s 0 under
J9s 100 and Q9s 0 under J9s 100; `LJ/rfi` Q8s 0 under J8s 100 and K8s 10 under T8s 100.

Not this phase's to build and not this phase's to gate. What it is: the next relation family
should include one comparison that walks the high card, because the four in the tree cannot,
and validating a candidate relation on the committed outside reference before scoring the chart
with it is the method that keeps it from being prose.

**A2. The per-hand reference read still has not reached the merged or three-bet-facing
families, and B1 and B2 are what it finds when it does.** File under
`NO-ABSOLUTE-FREQUENCY-IS-CHECKED-AGAINST-ANYTHING-EXTERNAL`, whose 2026-09-04 extension
already names exactly this as what remains unread: "per-hand comparison for the merged and
three-bet-facing families, which are still aggregate only, the five big-blind vs-open spots per
hand".

That entry predicted the value of the read from the first-in family, where 21 classes differ at
the lojack while the aggregate agrees to about a point. The same thing holds at the merged
family, harder: `CO/LJ:raise@2.5` measures 7.70 against the reference's 9.35, close, while
seven ace-and-king classes are folded here and played there. Three of the five committed
families now measure the right size with the wrong contents in the same direction, and only one
of the three has that published.

**A3. `PUBLISHED-RANGES-ANSWER-A-FIELD-THAT-UNDER-COLD-CALLS` carries the mechanism with the
word "slightly" and the measurement does not support it.** File under that id. The entry says
the export's cold-call pricing makes "opening and three-betting look slightly better than they
are". The size of it, measured for the first time here, is 60 ace-and-king classes folded pure
across 10 spots with zero exceptions, ATs at 96 percent fold from the cutoff against an
under-the-gun open, and KQo folded pure at 9 of 10 seats facing an open. A qualifier that a
reader can weigh belongs in that entry in place of the adverb.
