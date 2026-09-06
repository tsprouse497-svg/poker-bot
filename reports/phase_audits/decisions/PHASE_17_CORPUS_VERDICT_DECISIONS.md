# Phase 17 judgment calls

Written at stage 2 by lane A, 2026-09-06, in the `phase/17-the-corpus-verdict-on-the-committed-char`
worktree, base commit `9bbdcf44ce5508d19d672812fbc1b3484c32c790`. Stage 3 is the human gate that
reads it.

**Revised 2026-09-06 after the stage-2 independent review**
(`reports/phase_audits/reviews/PHASE_17_CORPUS_VERDICT/stage-02-decisions.md`), which raised five
blockers. What changed: item 1 gained the two lines that most directly decide it, and they argue
against its own recommendation; items 6 and 9 are reclassified `frozen-into-data`, because each fixes
a bar this phase's own measurement is graded against; two counts that did not reproduce are corrected
here and everywhere they propagated (the four-bet-facing spot count, and how many of the ExecPlan's
unpublished figures are in fact published); and every file:line citation in this file has been
re-verified against the current bytes, eight of which into
`reports/active/latest_derived_chart_report.txt` had drifted by 2 to 10 lines. Item 8's default is
also changed, per a non-blocker, because it argued against itself.

Every item carries a reversibility class, which `scripts/loop_stage.py` reads at stage 3 to decide
whether it must stop for a human.

- `runtime-reversible`: the choice only changes behaviour at query or report time, so a later edit
  changes it. The loop takes the recorded default, proceeds, and reports what it chose. The `Answer:`
  line carries that default.
- `frozen-into-data`: the choice fixes a bar a later measurement is graded against, or writes a
  committed figure every later phase reads. The loop halts until Taylor answers. The `Answer:` line
  is **empty on purpose**. A recommendation for each is in the item's prose, labelled as one.

**Ten items. Seven are frozen: 1, 2, 3, 4, 6, 9 and 10.** Items 1, 2, 3 and 9 are one chain - which
chart the comparison is graded against, which quantity the band is drawn on, which decisions the band
is graded over, and then the bands themselves - so they are best read together and in that order. Item
3 is the contract's central criterion and its numbers move if item 1 or item 2 is ruled the other way;
the item says by how much. Item 6 is frozen because it is the only item that reaches the gate: it
installs a validator that exits non-zero, and the exact check it installs depends on item 1.

Three are `runtime-reversible` and proceed on a recorded default: 5, 7 and 8.

**The artifact every "committed chart" figure below was taken on.** `data/artifacts/preflop/six_max_100bb_rakefree.json`,
`audit_fields.weights_sha256` = `3511d26eeb4258bd76b2575e5ded3abf07a258795144b3d2ccbcfb085d939063`,
249 spots, `generated_at` 2026-08-27. Its export card is
`data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json`, `export_sha256`
`f7182f4bbcc080c7715d8195cd0552d4604ec9856c8d7d64cd5a52483e0949e7`. The card's `config_posted` reads
`rake_pct: 0.0`, `rake_cap: 0.0`, `open_raises: [2.5]`, `add_allin: false`, `realization: "calibrated"`.

**The one rake sentence this phase is allowed.** The solve is rake-free in its preflop betting and is
**not** rake-free at its heads-up flop terminals: under `realization: "calibrated"` the fit was
measured net-of-rake over the gross pot and the engine skips the rake deduction there, so those leaves
carry the fit's training rake (`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE`, backlog.yml:4316).
No sentence anywhere in this list drops that qualification, and item 10 is about two committed reports
that do.

**How the numbers here were taken.** Every defence, call-share and purity figure below was recomputed
by lane A directly from the two JSON artifacts, combo-weighted (a pair is 6 combinations, a suited
class 4, an offsuit class 12, summing to 1,326), which is the weighting
`solver_artifacts/lookup.py:271` `action_frequency_pct` uses and documents at :274-277. Defence is
`100 x (1 - fold)` over hero's 169 classes at the spot, which is the definition
`solver_artifacts/gtopen_expectations.py:145` and :159 state for the export. Nothing below is copied
out of `backlog.yml` or a report; where a report already carries a figure, the item says so and cites
the line.

---

## 1 Which chart is the retired baseline the refusals and the deltas are measured against

Reversibility: frozen-into-data

Answer:

**The question.** The contract says "The baseline is the retired chart" (:81-82) and asserts two facts
about it: that it "holds 36 keys and not one of them faces a four-bet" (:84-85), and that the small
blind's open reprices "from 3.5bb to 2.5bb" (:56). There are two different retired charts in this
repo's history, and those two sentences are true of one of them and false of the other.

**The two lines that most directly decide this, quoted in full, because they cut opposite ways.**

The contract already names a pin, for one of its own criteria:

    docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md:97-99 - "Where the committed and retired charts
    both answer the same corpus decision, the report says how often they disagree and in which
    direction, reading the retired chart from git history at the pin phase 14's decision 7 names."

Phase 14 decision 7 names `d046ac9`, so that criterion reads on option A. It is the strongest argument
for A anywhere in the tree, and it is a criterion this phase is graded on rather than an inference.

And the committed report hands this phase its inputs, for option B:

    reports/active/latest_derived_chart_report.txt:1309-1311 - "What is printed instead is the delta
    itself, recomputed from the two committed charts, so that the later phase has the measurement its
    band will be drawn on rather than a claim about it:"

Immediately beneath it, at :1313-1317, are the option-B deltas: `vs LJ -1.578`, `vs HJ -1.041`, `vs CO
-1.332`, `vs BTN -0.104`, `vs SB -0.636`. That is a committed, gate-generated report telling phase 17
in terms which deltas its band is to be drawn on, and it is the strongest argument for B anywhere in
the tree. **The direction is what makes this a ruling rather than a technicality: all five of option
B's deltas are negative, against option A's +3.07 / +2.68 / +1.31 / -2.78 / +5.51 (item 2's table), so
the two baselines pre-register opposite predictions at four of the five openers - every one except the
button.** Taylor is choosing between two prediction sets that disagree in sign, not between two
citations.

**Option A, `d046ac9:data/artifacts/preflop/six_max_nl25_100bb.json`.** This is the pin phase 14's
decision 7 names (`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md:1204`, "The pin
is `d046ac9`"). Blob `841ada2fd7c9b106f71269d0948945a069990e78`. Verified by lane A: it holds exactly
**36** spots; the most raises on any key is **two**, so **no key faces a four-bet**; it holds
`t6/d100/BB/SB:raise@3.5`, so the small blind opens at 3.5; and it holds `t6/d100/BB/SB:call`, the one
limped answer the committed chart does not carry. Both of the contract's assertions hold.

**Option B, `6f15724:data/artifacts/preflop/six_max_100bb_rakefree.json`.** This is the chart the
committed, gate-generated `reports/active/latest_derived_chart_report.txt` actually uses as its
baseline: `scripts/generate_derived_chart_report.py:194` sets
`RETIRED_CHART_COMMIT = "6f157247cf2217acf358d7cef901a550fc4aae69"` and :190 sets
`RETIRED_CHART_PATH = "data/artifacts/preflop/six_max_100bb_rakefree.json"`, and the report prints the
pair at line 1129. Blob `9bde32b4631d6c266b521b4b4c90653126a7d587`. Verified by lane A: it holds
**86** spots, of which **45 carry three or more raises**; and it already opens the small blind at
2.5 (`t6/d100/BB/SB:raise@2.5` is present, `t6/d100/SB/rfi` is priced `[2.5, 100.0]` in its sizing
table at the same commit). Against this baseline **both** of the contract's assertions are false.

**The four-bet-facing count, with the rule it is counted under, because an earlier draft of this item
got it wrong.** Counting the `raise@` tokens in a spot key's action-sequence tail, the 86 keys split
`{0 raises: 1, 1: 10, 2: 30, 3: 30, 4: 15}`. **Three raises in front of hero is hero facing a
four-bet: 30 spots** - 15 of them priced at `raise@22.5` and 15 at the all-in `raise@100`. **Four
raises is hero facing a five-bet: 15 spots.** So the four-bet-facing count is **30**, or **45**
including the five-bet-facing spots, and **not 15** - 15 is only the `raise@22.5` subset. The
committed 249-spot chart holds **zero** keys with three or more raises, and `d046ac9`'s 36-spot chart
holds zero as well.

**The consequence, which is not cosmetic.** Under option B the four-bet withholding must show a rise,
because the baseline answered 30 four-bet-facing spots (45 counting the five-bet ones) and the
committed chart answers none. The contract calls exactly that "a measurement error" (:84-87). So
option B makes a contract criterion
unsatisfiable by a correct measurement, and a lane that took the derived-chart report's pin without
reading it would spend stage 6 chasing a defect that is the baseline's definition. Under option B
there is also no small-blind reprice at all, so the contract's "the prediction covers price and its
direction" (:56) has nothing to be about.

**The consequence the other way.** Option A means this phase's baseline is *not* the one the committed
derived-chart report used, so its before-columns and this phase's are over different charts and must
never be quoted beside each other without saying so. Two of them are far apart: over the five
big-blind-versus-open spots, option A defends 22.63 / 26.20 / 31.48 / 39.43 / 42.88 percent against
LJ / HJ / CO / BTN / SB, where the derived-chart report prints 27.276 / 29.922 / 34.115 / 36.757 /
49.023 for option B (`reports/active/latest_derived_chart_report.txt:1313-1317`). Lane A reproduced the
option-B column exactly from `6f15724`'s bytes, so the report is not wrong about its own baseline - it
is a measurement of a different chart.

**Recommendation, not an answer, and the case against it is above rather than buried.** Option A,
`d046ac9`. The contract cites that pin at :97-99 for its own old-versus-new criterion; it is the only
baseline both of the contract's stated facts hold for; and it is the chart that was actually retired
*by phase 14* - `6f15724` is an intermediate build from phase 14's own lane, three days before the
merge, which no phase ever shipped. What weighs the other way is real and is not a formality: the
committed report at :1309-1311 hands this phase the option-B deltas as "the measurement its band will
be drawn on", so ruling option A means overriding a gate-generated instruction, and doing it after
seeing that the two sign-disagree at four openers. That ordering is uncomfortable and is the reason
this is Taylor's to rule rather than a lane's to assume. If option A is ruled, this phase's report must
say in terms that its before-column differs from the derived-chart report's and why, because two
committed reports printing different "retired" numbers is the confusion this whole family of items
exists to prevent. That disclosure is cheap; leaving it out is the defect.

**Filed either way.** The disagreement between `generate_derived_chart_report`'s pin and phase 14
decision 7's pin is a live inconsistency in `main` that neither document acknowledges, and one of them
asserts they agree: `PHASE_14_CHART_CUTOVER_DECISIONS.md:1204-1205` says `d046ac9` is "what the
committed derived-chart report already reads the retired chart from", which is verifiably false. It
belongs in `backlog.yml` regardless of which option is ruled, because the loser of this ruling is still
cited somewhere as "the retired chart", and phase 17 cannot fix it from inside its scope since the
generator is phase 14's. Proposed id, from the stage-2 review:
`RETIRED-CHART-PIN-DISAGREES-BETWEEN-GENERATOR-AND-RULING`.

## 2 Which delta the per-opener band is drawn on: total defence, or its call component

Reversibility: frozen-into-data

Answer:

**The question.** Phase 14's decision 9 fixed the *form* of the prediction and phase 17 inherits it:
"big-blind call agreement moves in the same direction as that opener's defence delta, by between one
quarter and one times the delta in points"
(`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md:1286-1288`). The outcome being
predicted is agreement on decisions where the **player called**. The predictor is the chart's **total
defence**, which is call plus raise. Those two are not the same quantity and on this chart they point
opposite ways at two of the five openers.

**The evidence.** Lane A recomputed both, combo-weighted, from the committed artifact and from
`d046ac9`'s bytes. Percentages of the full 1,326 combinations.

    opener   defence: retired -> committed   delta      call share: retired -> committed   delta
    LJ           22.6326 -> 25.6986         +3.0660        17.5162 -> 19.6312           +2.1150
    HJ           26.2020 -> 28.8804         +2.6784        19.2140 -> 20.9776           +1.7636
    CO           31.4762 -> 32.7833         +1.3071        22.6148 -> 22.4389           -0.1759
    BTN          39.4328 -> 36.6526         -2.7802        26.5433 -> 21.0853           -5.4581
    SB           42.8775 -> 48.3873         +5.5098        25.3351 -> 20.3007           -5.0344

Retired keys: `t6/d100/BB/{LJ,HJ,CO,BTN}:raise@2.5` and `t6/d100/BB/SB:raise@3.5`. Committed keys: all
five at `:raise@2.5`. The committed column is checkable against a committed report - the
`derived` numbers at `reports/active/latest_derived_chart_report.txt:1313-1317` are 25.699, 28.880,
32.783, 36.653, 48.387, which is this column to three decimals.

**Say it in poker.** Against the small blind the committed chart defends **5.51 points wider** and
**flats 5.03 points narrower**: it converts flats into three-bets and adds range on top. Phase 14's
decision 45 is why - the bot's pure calls are merged into its raises rather than published as calls
(`PHASE_14_CHART_CUTOVER_DECISIONS.md`, item 45, and
`MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED` in `backlog.yml`). So at the small blind
and the cutoff, a chart that defends more will agree with the corpus's **calls** less, and the
defence-delta prediction is pointing the wrong way at the two openers where the mechanism is strongest.
That is a real poker fact about this chart, not an artefact of the arithmetic.

**Option A, keep total defence as the predictor.** It is what decision 9 ruled and what travels under
"the form of the ruling stands" (`PHASE_14_CHART_CUTOVER_DECISIONS.md:1310-1315`). It predicts a rise
at CO and SB where the flat says a fall, so it is a genuinely falsifiable prediction that this lane
expects to miss at two of five openers - and a miss is a result the contract requires reported rather
than explained away (:140-141 of the contract, :1305 of decision 9).

**Option B, draw the band on the call component instead.** It matches the predictor to the outcome:
the thing being predicted is agreement on calls, so the thing predicting it should be how much the
chart calls. It is the honest predictor of the mechanism. It is also a change to the inherited form of
the ruling rather than only its arithmetic, which decision 9 said would travel unchanged.

**Option C, register both, and say which is the primary.** Two bands per opener, the defence band as
the inherited form and the call band as the mechanism, with the primary named now so it cannot be
chosen after the numbers land. Costs nothing but width in the report.

**Consequence of getting this wrong.** Under option A a report author who sees a fall at SB has an
inherited prediction that says "rise", and the temptation at stage 9 is to reach for the flat
explanation *after* seeing the number. Registering it now is the only thing that stops that, which is
the entire reason decision 9 is `frozen-into-data`.

**Recommendation, not an answer.** Option C, with the **defence** band as primary. It keeps decision
9's inherited form intact and unweakened, and it puts the call-component band on the record before the
measurement so that a miss at CO and SB is a pre-registered expectation rather than a post-hoc excuse.
Item 3 registers the numbers for both.

## 3 The prediction, per opener, with its magnitude band

Reversibility: frozen-into-data

Answer:

**The question.** The contract requires "The prediction ... written into this phase's decision list
before the measurement runs, per opener and with a magnitude band - a quarter to one times that
opener's defence delta - with the deltas recomputed from the committed chart" (:50-53), and requires it
to cover "price and its direction - the small-blind open reprices from 3.5bb to 2.5bb" (:56). Phase
14's decision 9 bands are void, not inherited (`PHASE_14_CHART_CUTOVER_DECISIONS.md:1316-1320`), and
none of its numbers appears below.

**What is predicted.** The change in big-blind call agreement - agreed calls over scored calls, on
decisions where the big blind faced exactly one open from that seat - measured against the same corpus
scored twice, once with the committed chart and once with the retired chart of item 1. Per opener, per
population, never pooled. Points, not percent-of-percent.

**The bands, on the total-defence delta (item 2's option A / primary).** A quarter to one times the
delta in the table in item 2, sign included:

    vs LJ    +0.77 to +3.07 points        (delta +3.0660)
    vs HJ    +0.67 to +2.68 points        (delta +2.6784)
    vs CO    +0.33 to +1.31 points        (delta +1.3071)
    vs BTN   -0.70 to -2.78 points        (delta -2.7802, a predicted worsening)
    vs SB    +1.38 to +5.51 points        (delta +5.5098)

**The bands, on the call-component delta (item 2's option B / secondary).**

    vs LJ    +0.53 to +2.11 points        (delta +2.1150)
    vs HJ    +0.44 to +1.76 points        (delta +1.7636)
    vs CO    -0.04 to -0.18 points        (delta -0.1759, a predicted worsening)
    vs BTN   -1.36 to -5.46 points        (delta -5.4581, a predicted worsening)
    vs SB    -1.26 to -5.03 points        (delta -5.0344, a predicted worsening)

The two disagree in **sign** at CO and SB. That is the point of registering both, and whichever is
ruled primary, the report prints both columns beside the outcome.

**Price, and its direction.** The small blind is the one opener whose price moved: the retired chart
answers `t6/d100/BB/SB:raise@3.5` and the committed chart answers `t6/d100/BB/SB:raise@2.5`, verified
in both files by lane A. A cheaper open is a better price and the correct response is to continue with
more hands, so the committed chart **must** defend the small blind wider than the retired one or the
reprice did not reach the ranges: it does, by 5.51 points, the largest move of the five and the only
one that carries a price change as well as a solve change. The direction is therefore **predicted
positive for total defence at the small blind, and it is the one opener where the sign is
overdetermined** - the price alone forces it. That is also why the small blind's band says least about
the solve: its delta confounds the reprice with everything else that changed, and no measurement in
this phase separates the two. The report must say so rather than reading the largest delta as the
strongest evidence.

**Direction at the other four, and what would falsify it.** LJ, HJ and CO are predicted to widen and
BTN to tighten, all at one unchanged price of 2.5. A miss high - movement larger than the delta - is
the informative direction, because it means something other than the defence change is driving
agreement. A miss in sign at LJ, HJ or BTN would say the defence delta does not predict call agreement
at all, which is a result about the metric rather than about the chart.

**Denominators, and the minimum, both fixed now so a thin cell cannot be read as a result.** The exact
per-opener call counts are already committed at
`reports/active/latest_derived_chart_report.txt:1323-1332`, so this does not have to be estimated from
the pooled 57 of 125 at `latest_sample_comparison_report.txt:115` and 7 of 20 at `:106`:

    opener   humans   Pluribus
    LJ         15         5
    HJ         20        none faced that opener
    CO         27         3
    BTN        43         7
    SB         20         5

Those counts are the option-B run's, so the option-A denominators will differ; the shape will not,
because the corpus is the same 499 hands and the scored-call population moves only where a chart's
coverage moves. **Only the Pluribus cells are that thin.** So: **the minimum is 10 scored calls.** A
cell below it gets its count and its raw rate printed and **no band verdict at all** - not a hit, not a
miss, the word "unresolved" - because a band a point wide cannot be read on five decisions. On these
counts that rules out every Pluribus cell and none of the human cells, which is stated now rather than
discovered at stage 9. Every rate carries its count under it regardless.

**Recommendation, not an answer.** Register both tables as printed above, defence primary, and treat
the small-blind row as confounded by the reprice in both.

**A miss is a result.** Whatever lands, the report prints the prediction beside the outcome and reports
a miss in either direction as a finding, per the contract (:140-141). Nothing in this item is edited after
stage 4 for any reason; if it needs correcting, the correction is dated, additive, and says what it
supersedes.

## 4 What may be called pre-registered, when four committed reports already publish the analogue

Reversibility: frozen-into-data

Answer:

**The question.** The ExecPlan's section "What is already committed, and what the prediction may
therefore cover" lists three files that already publish part of the outcome and, at
`docs/exec_plans/active/PHASE_17_CORPUS_VERDICT.md:51-56`, four figures it calls "genuinely
unpublished". Lane A was told to verify that split rather than trust it. **It does not hold**, though
not as badly as an earlier draft of this item said.

**The count, corrected, with the rule it is counted under.** The ExecPlan's four are: (1) each opener's
defence delta and the per-opener band, (2) cell purity over the shared spots, (3) refusal movement
split by cause and the three coverage costs separately, (4) the old-versus-new disagreement count and
its direction. There is a fourth committed file the plan does not name, and it publishes **two** of
those four - (1)'s deltas and (4) - **not three**. An earlier draft said three; it does not publish (2)
or (3), which is exactly what the "what survives" list below keeps, so that draft contradicted itself
two paragraphs later. Counting rule: a figure counts as published only if the committed file prints
that quantity, not a neighbour of it. On that rule (1) is a half - the report prints the **deltas** and
does not print the **band**, and it prints them against option B's baseline rather than option A's.

**What the miscount does not change, and this is the sharper point.** The plan's list of four does not
mention the per-opener big-blind call agreement move at all, and the report publishes that too. That is
the **outcome the prediction is about**, split by opener and by population, already on disk. So the
honest summary is not "three of four" or "two of four" but this: the plan's inventory of what is
already public is itself incomplete, and the figure it misses is the one the pre-registration is graded
on.

**The file the plan misses.** `reports/active/latest_derived_chart_report.txt`, generated by the
registered gate command `generate_derived_chart_report` (`scripts/run_verify.py:308-311`) and committed
at `9bbdcf4`. What it already publishes:

- **The per-opener defence deltas.** Lines 1313-1317: `vs LJ retired 27.276 derived 25.699 delta
  -1.578` and four more. Against option B's baseline, not option A's, but it is the same figure the
  plan calls unpublished.
- **The per-opener big-blind call agreement move, with counts.** Lines 1323-1332: `humans, vs LJ: 15
  calls, 73.3 to 60.0 percent`, and nine more rows. **This is the outcome the prediction is about**,
  already on disk, split by opener and by population.
- **The old-versus-new disagreement count and its direction.** Lines 1503 and 1509-1512: `decisions both charts
  answer 499`, `disagreed 7`, `derived continues, retired folds 2`, `retired continues, derived folds
  5`.
- **The limp count with its counting rule.** Lines 1431-1436: the rule `the first recorded action in
  the spot key is a call` and the count `16 inventory rows 52 decision points`. Item 7 is about what
  is left to decide there.
- **The three explanations and which survive.** Lines 1370-1381, with `rake separated`, `price
  uncontrolled`, `realization uncontrolled`.
- **The bounds paragraph**, lines 1387-1405.

Lane A reproduced the option-B delta column from `6f15724`'s bytes and the limp count from
`reports/active/latest_sample_refusal_inventory.txt` (16 rows, 52 points, independently) rather than
taking either on trust.

**What survives as genuinely unpublished at `9bbdcf4`**, checked by lane A against all four files:

- Any figure at all measured against **option A's baseline**, `d046ac9`'s 36-spot chart. Nothing in
  `reports/active/` uses it. If item 1 rules option A, the whole before-column of this phase is new.
  One thing a reader who greps will hit and should not misread:
  `latest_derived_chart_report.txt:656` names `expectations/six_max_nl25_100bb.json`, which shares the
  stem but is the GTO Wizard **expectations** file, a different artifact from the retired chart. The
  claim above is about the chart.
- **The refusal movement split by cause** - the multiway ruling's, the re-source's, the four-bet
  withholding's. `reports/active/latest_derived_chart_report.txt:1424-1429` splits refusals by
  **runtime miss code** (`lookup:spot-not-covered` 2527 -> 129, `lookup:hand-class-not-covered` 2 ->
  10) and says in terms at :1420-1422 that the derivation vocabulary "does not appear in this section
  at all". `reports/active/latest_sample_refusal_inventory.txt` lists 61 spots by key with no cause at
  all. So the three coverage costs are unpublished. Item 6 is about how to take them.
- **Cell purity over the shared spots.** `docs/BACKLOG.md:213` publishes 2.209 nonzero actions per cell
  at 21.0 percent pure against 1.323 at 73.0, and those are two *derived* builds over their whole
  charts, neither of them the retired chart of item 1. `latest_derived_chart_report.txt:611-612`
  publishes a different statistic again (pure-at-99-percent, before and after the flat merge). Purity
  restricted to the spots both charts answer is unpublished. Item 8 is about what "shared" means.
- The prediction of item 3 as a **band**, per opener, against option A's deltas. The deltas themselves
  are published against option B and are not published against option A.

**Options.**

- **A, proceed and disclose.** Register item 3's bands, and have the report and the packet state
  plainly which of this phase's figures were pre-registered blind, which were quoted from a committed
  file as a starting point, and which are new only because the baseline changed. A stage-8 reviewer
  can then check the claim against these four files rather than take it.
- **B, drop the pre-registration language.** Report the deltas and the outcome side by side and stop
  calling it a prediction, on the ground that too much of the analogue is already on disk for the word
  to mean anything.
- **C, re-scope the prediction to what is genuinely blind** - the per-cause refusal split and the
  shared-spot purity - and predict those instead of call agreement.

**Consequence.** Under A, the contract's central criterion is satisfied with an honest asterisk and a
reader can audit it. Under B, the contract criterion at :50-53 is not met and needs amending, which is
a `contract-update` task this phase is not in. Under C, the phase pre-registers things nobody named as
the question and the calling gap - the thing this phase exists to speak to - has no prediction at all.

**Recommendation, not an answer.** Option A. The prediction is not blind and saying so is the fix; the
general defect is already filed as `PREDICTION-CANNOT-BE-BLIND-TO-A-COMMITTED-MEASUREMENT`
(backlog.yml:6366) and this phase discloses its instance rather than pretending otherwise. That entry
should be extended with the fourth file this item found, because the stage-1 review named three and
there are four, and the one it missed is the one that publishes the outcome itself.

## 5 Whether the measurement builds on `comparison.py` or reimplements with a cross-check

Reversibility: runtime-reversible

Answer: build on `data_pipeline/comparison.py`; add no second scoring path.

**The question.** `CORPUS-AGREEMENT-HAS-NO-SINGLE-SOURCE` (backlog.yml:6390) says either lane C builds
on `comparison.py` or the phase asserts the two generators agree, and that the choice is recorded here
rather than made silently.

**Why the default is the first, and it is not close.** `compare_committed_sample`
(`src/poker_training_bot/data_pipeline/comparison.py:361`) already takes the chart as a parameter, and
its own docstring says what the parameter is for: "the same comparison has to run against the RETIRED
chart, read out of git history rather than out of `data/`, so that 'the refusal rate rose' is a
measurement over one corpus and one comparison rather than two runs of different code a reader has to
trust agree. Passing a strategy in is the only way to get that without a second copy of this function,
and a second copy is how the two numbers would drift." The seam this phase needs was built for this
phase's job. Beside it, `ComparisonResult.agreement_within` (:273) already narrows by population,
action, position and price band; `sampled_action_match` (:302) is the strict rate; `price_band_for`
(:208) is the price split; and `scripts/generate_derived_chart_report.py:1263`
`load_retired_chart_from_git` already loads a retired chart through the repo's own importer at a pin.

**What reimplementing would cost.** The repo would carry **three** gate-registered commands publishing
corpus agreement over the same corpus - `generate_sample_comparison_report`,
`generate_derived_chart_report` (which prints the corpus before-and-after at
`reports/active/latest_derived_chart_report.txt:1243-1280`) and the new
`generate_corpus_verdict_report` - with nothing checking any against any. The backlog entry says two;
it is already two today and phase 17 would make it three.

**Why this is reversible.** It is where code lives. No committed data records the choice, no figure
changes because of it, and moving the computation later re-runs a generator. It is recorded rather than
blocked because the drift it prevents is real, not because the choice is expensive.

**What the default commits the phase to.** `corpus_verdict.py` imports `compare_committed_sample` and
adds the narrowings phase 17 needs on top of `ComparisonResult` - per-opener, per-cause, purity - rather
than rescoring anything. If a new narrowing genuinely cannot be expressed over `ComparisonResult`, the
fallback is to extend `comparison.py` under this phase's scope, not to fork it. `CORPUS-AGREEMENT-HAS-NO-SINGLE-SOURCE`
closes on that landing, and the packet says which of the two routes it took.

## 6 How a corpus refusal is attributed to one of the three coverage causes

Reversibility: frozen-into-data

Answer:

**Reclassified from `runtime-reversible` on 2026-09-06, by the stage-2 review, and it was right.** An
earlier draft filed this reversible and put an unconditional rule on the `Answer:` line, then said four
paragraphs later that the rule's central check "must be deleted" under option B of item 1 - which is
unruled. That is two defaults, and the loop can only take one. Two independent reasons make it frozen
under this file's own test at the top: the priority order below decides the three per-cause coverage
costs the contract grades at :82-83 ("the rate must rise only where phase 14's two exclusions and the
limp account for it, and nowhere else. A rise outside them is a defect"), and cause 5 is defined as
whatever the four causes above it did not absorb - so the ordering decides whether that criterion can
report a defect at all. That is a bar this phase's own measurement is graded against. And unlike every
other classification item here, this one **reaches the gate**: it installs a validator that exits
non-zero, so a wrong order is a red build rather than a wrong sentence.

**The question.** The contract requires each exclusion's coverage cost reported separately - the
multiway ruling's, the re-source's, and the four-bet withholding's (:88-89) - and requires the four-bet
withholding to show **no rise at all** against the baseline (:84-87). Nothing in the repo attributes a
*corpus* refusal to a *derivation* cause. The two vocabularies are deliberately disjoint: a runtime
refusal carries `lookup:spot-not-covered` and friends (`solver_artifacts/lookup.py:52-57`), a
derivation exclusion carries `derivation:beyond-committed-raise-depth`,
`derivation:multiway-exposure-above-threshold`, `derivation:big-blind-squeeze-spot` and
`derivation:no-legal-spot-key` (:82-85), and
`reports/active/latest_derived_chart_report.txt:1420-1422` says in terms that folding the two together
"is how an excluded node gets filed as a lookup failure". So the mapping has to be built, and building
it is where the error would go in.

**The problem that makes this a judgment call.** A refused key can match more than one cause. Read off
the committed inventory (`reports/active/latest_sample_refusal_inventory.txt`), `t6/d100/BB/LJ:raise@2.5,BTN:call`
is a big-blind squeeze spot *and* a spot with multiway exposure; `t6/d100/BB/SB:call` is a limp and
nothing else; `t6/d100/CO/HJ:raise@2.5,CO:raise@6.81,HJ:raise@19.93,CO:raise@36.67,HJ:raise@100` is
beyond the committed raise depth *and* would be a price the chart never solved. Counting a decision
point once per cause makes the causes sum past the total; counting it under the first match makes the
order load-bearing. Either way the order is a choice and it must be published, or a later reader cannot
tell whether the four-bet column is small because the withholding is cheap or because another cause
took its rows first.

**Option A, the recommended order, stated in full.** One cause per decision point, assigned in this
order, which is argued by what the fix would be rather than by convenience:

1. **limp** - the first recorded action in the key is a call. This is not one of the three costs; it is
   separated first so it cannot be charged to any of them, which is what the contract's "phase 14's two
   exclusions **and the limp**" (:81-83) requires.
2. **four-bet withholding** - three or more raises on the key. Placed above the others because the
   contract makes a falsifiable claim about it and burying it under a lower cause would make that claim
   untestable in the safe direction.
3. **big-blind squeeze / the re-source** - hero is the big blind and a call precedes the last raise.
4. **multiway exposure** - what remains that the export excluded for exposure.
5. **unmatched key** - anything none of the four reaches, which the report prints even at zero, because
   a residual here is the defect the contract's "a rise outside them is a defect" (:83) is about.

Under option A the report also publishes, for every cause, both the first-match count and the count of
decision points that *also* matched it but lost to a higher cause, so a reader can add them back.

**Option B, causes counted independently and allowed to overlap.** Every decision point is counted
under every cause it matches, no order at all, and the report prints the overlap matrix and states that
the columns do not sum to the total. Nothing is charged to the wrong ruling because nothing is charged
exclusively. The cost: the contract's :83 defect test has no residual bucket to read, since "outside
them" is not a set any more, so the criterion has to be restated as "every refused point matches at
least one of the four" - which is a weaker claim and arguably the honest one.

**Option C, order by frequency rather than by argument** - largest cause first. Rejected here and
listed because it is what a lane would drift into: it makes the biggest number bigger and the
falsifiable four-bet claim unfalsifiable, since the multiway family would absorb the rows the four-bet
check is meant to see.

**The check that makes the four-bet claim mean something, and why it cannot be written before item 1.**
Under **option A of item 1** the retired chart holds 36 keys, none with more than two raises (verified
by lane A). So no decision point the retired chart *answered* can be in cause 2, the four-bet column's
rise must be exactly **zero**, and the generator exits non-zero rather than printing anything else, per
the contract's self-validation requirement (:107-108). Under **option B of item 1** that check must be
deleted rather than relaxed, because the baseline answered 30 four-bet-facing spots (45 counting
five-bet-facing; see item 1's counting rule) and a rise there is the truth rather than an error. Those
are two different gates. This is the sharpest reason item 1 has to be ruled before stage 6, and the
reason this item cannot proceed on a default of its own.

**Recommendation, not an answer.** Option A, with the zero-rise check conditional on item 1 landing on
option A. If item 1 lands on option B, this item needs re-answering rather than reinterpreting, and the
contract criterion at :84-87 needs a `contract-update` before stage 6 rather than a generator that
cannot satisfy it.

## 7 How "decision points facing a limp" is counted, and over which denominator

Reversibility: runtime-reversible

Answer: the first recorded action in the spot key is a call, counted over all preflop decision points in the sample, with the refused subset printed beside it and both denominators named.

The `Answer:` line above is deliberately one long line: `decision_items()` (`scripts/loop_stage.py:290-291`) keeps only the last line starting `Answer:`, so a wrapped default is silently truncated to its first line in whatever the loop records and reports.

**The question.** The contract requires "its own count of decision points facing a limp with the
definition it counted by, because `CHART-CANNOT-ANSWER-A-LIMPED-POT` does not carry one" (:94-96).
Phase 14's decision 12 already ruled the *form* - publish your own count under your own definition and
do not try to reproduce the undefined 12 and 21
(`PHASE_14_CHART_CUTOVER_DECISIONS.md:1576-1590`) - and the default there was "the first recorded
action in the spot key is a call".

**What is already published, and what is not.** `reports/active/latest_derived_chart_report.txt:1431-1436`
already prints that rule and the count `16 inventory rows 52 decision points`. Lane A reproduced it
independently from `reports/active/latest_sample_refusal_inventory.txt`: 16 of the 61 distinct refused
spots have a call as the first action in the key, and they carry 52 of the 139 refused decision points.
So the count exists. What it is *over* is the open question: 52 is the count of **refused** decision
points reaching a limp-first key, not the count of limped decision points in the corpus. The
denominator that reads naturally from the contract is the sample's 3,048 preflop decision points
(`reports/active/latest_sample_comparison_report.txt:46`), and 52 is not a count over that.

**Why the gap is probably small but must still be stated.** Lane A checked both charts: the committed
249-spot chart holds **no** key whose first action is a call, and `d046ac9`'s 36-spot chart holds
exactly one, `t6/d100/BB/SB:call`. So under the committed chart every limped decision point is refused
and 52 is also the corpus count, while under the retired chart 30 of those 52 were answered - which is
why the limp is a genuine rise in item 6's cause 1 rather than an artefact.

**Options.** (a) Publish over all 3,048 decision points, with the refused subset beside it. (b) Publish
the refused subset only, as the committed report does. (c) Define a limp off the corpus hand history
rather than off the spot key - a voluntary call at the opening price with no raise before it - which
would also catch a limp that a later raise pushed out of hero's key.

**Consequence.** (b) is what exists and it under-reports whenever a chart answers a limped spot, which
is exactly the retired chart's case, so the before-column would be wrong. (c) is the more honest
definition of the poker event and is more work, and it would produce a third number that does not
reproduce either published one, which is the drift `LIMPED-DECISION-POINT-COUNT-HAS-NO-DEFINITION`
already complains about. (a) reproduces the committed 52 as a stated subset and adds the denominator
the contract asks for.

**Why this is reversible.** A counting rule in a report over data that does not move. It is recorded
because two committed documents already carry an undefined 21 and this phase's number will be read
against them.

## 8 What "cell purity over the shared spots" is computed over

Reversibility: runtime-reversible

Answer: both rows, shared chart keys primary - the 19 keys both charts declare, and beside it the same statistic restricted to the corpus decisions both charts answered; a cell is one hand class at one spot; purity is the share of cells with exactly one nonzero action, with mean nonzero actions per cell printed beside each.

**The question.** The contract requires "the strict sampled-action rate and the cell-purity statistic
beside it, over the shared spots" (:62-63). Neither "shared spots" nor "purity" has one obvious
meaning, and the numbers differ by a lot between readings, so the reading has to be published with the
figure.

**The evidence.** Lane A computed, from the committed artifact and `d046ac9`'s bytes:

    scope                                    cells   mean nonzero actions/cell   pure
    committed chart, the 19 shared keys       3211            1.050              95.0%
    retired chart, the 19 shared keys         3211            1.324              73.9%
    committed chart, all 249 keys            18431            1.170              85.9%
    retired chart, all 36 keys                4521            1.433              64.1%

The 19 shared keys are the intersection of the two charts' `spot_id` sets. 36 minus 19 is 17, which
matches `src/poker_training_bot/solver_artifacts/vocabulary_corpus_report.py:117`, "Seventeen of the
retired chart's 36 keys are absent from the committed set". Every cell here is one of the 169 hand
classes at one spot, counted whether or not it arrives with reach.

**Options.** (a) Shared **chart keys**, the 19 above. (b) Shared **corpus decisions** - the decisions
both charts answered, which the derived-chart report puts at 499 for option B's baseline
(`latest_derived_chart_report.txt:1509`) - which weights each cell by how often the corpus reached it
and is the population the agreement rates are actually over. (c) Both, primary named.

**Consequence, and why the default moved to (c) on 2026-09-06.** (a) is a property of the charts and is
stable; it can include cells the corpus never reached, so it does not describe the sample the agreement
rate is computed on. (b) is the population the contract's sentence is about - "over the shared spots"
sits inside a paragraph about what the agreement rate rewards - but it is a much smaller and lumpier
sample. An earlier draft took (a) while conceding in this paragraph that (b) is what the contract
means, which is an item arguing against its own default with nobody asked, because the item is
reversible. The stage-2 review called that out. The fix is (c): print both, name (a) primary because
"shared spots" reads most naturally as shared spot keys and because it is the stable one, and let a
reader who prefers (b) read it off the same table rather than regenerate anything. Two rows is the
whole cost.

**The reason the contract wants this at all, restated so the report cannot invert it.**
`AGREEMENT-RATE-REWARDS-AN-UNCONVERGED-CHART` (backlog.yml:3966, `docs/BACKLOG.md:213`) is that
agreement means nonzero weight, so a cell with every action live cannot disagree with anything, and a
chart converging to purer cells scores **worse while playing better**. The table above says the
committed chart is purer than the retired one over the same 19 keys - 1.050 actions per cell against
1.324, 95.0 percent pure against 73.9 - so a fall in the permissive rate is what a converged chart
looks like. Printing the fall without the purity beside it states the reverse of the truth, which is
what the contract's :64-65 forbids.

**Why this is reversible.** A statistic recomputed by a generator from files that do not move.

## 9 How a corpus decision is assigned to an opener

Reversibility: frozen-into-data

Answer:

**Reclassified from `runtime-reversible` on 2026-09-06, by the stage-2 review, and it was right.** An
earlier draft filed this reversible and then closed it with "Recorded because it silently decides which
decisions the phase's headline prediction is graded on" - which is this file's own definition of frozen
at the top, written into the item that denied it. Item 3 registers a band per opener; this item fixes
the population each band is graded over. Choosing the grading population is part of the
pre-registration, not a report-time detail, and it is the selector most available to be quietly widened
once a band is missed. Freezing costs nothing: the loop already halts on items 1, 2, 3, 4, 6 and 10, so
no additional stop is created.

**The question.** Item 3's prediction is per opener, and `ComparisonResult.agreement_within`
(`comparison.py:273`) narrows by population, action, position and price band but not by opener. The
narrowing has to be added, and there is more than one place to read the opener from: the key the lookup
asked about (`ComparisonRow.asked_spot_key`), the key it refused on (`ComparisonRow.spot_key`), or the
raw corpus history on `ComparisonRow`'s decision point.

**Option A, the recommended selector: the key the lookup asked about.**
`scripts/generate_derived_chart_report.py:1304` already defines exactly this narrowing,
`OPENER_KEY = re.compile(r"^t6/d\d+/BB/(LJ|HJ|CO|BTN|SB):raise@")`, and its docstring at :1307-1308
states the reason: "Read off the key the lookup asked about rather than off either chart's coverage, so
the before and after columns are over the same decisions." Reusing it keeps this phase's per-opener
rows comparable with the committed report's, which matters under item 4's disclosure.

**What option A excludes, said plainly, because this is the part that decides the grade.** A big-blind
decision facing an open **plus a caller** is in no opener's row, because it is a squeeze spot the
committed chart refuses by ruling. Those go to the refusal split of item 6, not to the prediction.
Whatever is ruled, the report states how many decisions fell outside every opener row, so nobody reads
a per-opener rate as covering the big blind's whole sample.

**Option B, read the opener off the raw corpus history** - the first voluntary raiser in the hand,
regardless of what key the lookup reached. It is the more natural reading of "vs LJ" in poker and it
covers the squeeze spots. It also makes the before and after columns cover different decisions,
because the two charts refuse different sets, which is the failure `generate_derived_chart_report`'s
docstring says the existing rule exists to prevent.

**Option C, the refused key rather than the asked key** (`ComparisonRow.spot_key` instead of
`asked_spot_key`). Named only to be rejected: it is populated on refusals and reads differently from
option A on exactly the decisions where the two charts differ, which is the population the whole
comparison is about.

**Recommendation, not an answer.** Option A. It is the rule already in the tree, it keeps the two
columns over one population, and it is the narrower claim - which is the safe direction for a
pre-registration, since the widening is what a missed band invites.

## 10 Phase 14's two committed reports make the rake claim this phase's contract forbids

Reversibility: frozen-into-data

Answer:

**The question.** Correcting another phase's committed, gate-generated report is a ruling, not a fix,
and it is Taylor's rather than this lane's. Two committed files at `9bbdcf4` state that rake is
eliminated, without the heads-up-flop-terminal qualification that
`CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` (backlog.yml:4316) requires and that this phase's
contract makes a forbidden shortcut (:151) and a false claim (:75).

**Instance one, and the plainest.** `reports/active/latest_sample_comparison_report.txt:28-35`: "The
committed ranges are solved rake-free, and these hands were played rake-free, so the two settings agree
on that point and **nothing below is explained by it** ... The committed solve takes no share, so **that
explanation is gone** and it was doing real work - where this chart continues less than these players
do, the difference is between the chart and the players and **has nothing to excuse it**." The text is
not in the report, it is in the generator, at
`src/poker_training_bot/data_pipeline/comparison_report.py:53-60`, so the report reproduces it on every
gate run and editing the committed file alone would be undone by the next `generate_sample_comparison_report`.

**Instance two, which is a report contradicting itself 159 lines apart.**
`reports/active/latest_derived_chart_report.txt:1217-1220` carries the qualification correctly - "The
solve is rake-free at the table and is NOT rake-free at its heads-up flop terminals ... the rake it was
trained on comes back in at every flop it does not play out" - and then at :1376-1377 the explanations
table drops it: "rake  separated: the committed solve is rake-free at the table, so a raked-solve
explanation for a residual gap no longer applies to this chart". Generator lines
`scripts/generate_derived_chart_report.py:2798-2801` and :2974-2975 respectively. A reader who reads the
verdict table and not the limitations list gets the false version, and the verdict table is the part
this phase's own report has to restate.

**Why it lands here rather than in a backlog entry alone.** Phase 17 is the phase that measures the
rake explanation and republishes the three-explanations paragraph. It cannot write a qualified verdict
while two gate-generated reports in the same tree say the opposite unqualified, and a reader comparing
them will take the older confident sentence over the newer careful one.

**Options.**

- **A, leave both and disclose.** Phase 17's own report states the qualified version, names both
  instances by file and line, and says they are phase 14's record. Nothing outside this phase's scope
  is touched. Cost: three committed reports in one tree disagree about rake, and the two that are wrong
  are the ones a reader reaches first.
- **B, correct the generators inside phase 17.** Add the qualification at
  `src/poker_training_bot/data_pipeline/comparison_report.py:53-60` and
  `scripts/generate_derived_chart_report.py:2974-2975` and regenerate. Both
  files are outside this phase's approved scope and both are guarded by frozen phase-14 tests
  (`tests/test_sample_comparison_report.py`, `tests/test_derived_chart_report*.py`), so this needs a
  dated `scope_change_log` entry and may need a frozen test amended - which an implementer may not do.
- **C, a separate maintenance task.** A `maint/NN` lane owns the two generator edits and the
  regeneration, phase 17 discloses in the meantime, and the two land in whichever order they finish.
- **D, treat the contradiction inside the derived-chart report as a defect and only fix that one**,
  since a single report stating both the qualified and the unqualified version is wrong on its own
  terms regardless of what phase 17 says.

**Consequence.** A leaves a reader with the wrong headline. B is the fastest correct text and the
worst process: it widens an implementation phase's scope onto another phase's frozen surface, which is
how the phase-14 scope failures happened. C is slowest and cleanest. D is the narrowest true statement
and does not touch `comparison_report.py`, which is the instance the stage-1 review actually found.

**Recommendation, not an answer.** C, with A's disclosure in phase 17's own report in the meantime, and
the `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` entry extended now with both file-and-line
instances so the maintenance lane has the diff already written. What this lane will not do is quietly
edit either file: the contract's forbidden shortcuts and this phase's scope both say a finding about
another phase's committed output is a ruling and a backlog entry, not an edit made in passing.
