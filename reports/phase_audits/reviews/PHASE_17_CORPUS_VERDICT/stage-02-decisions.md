# Phase 17 stage 2 review: the decision list

Read-only independent review of
`reports/phase_audits/decisions/PHASE_17_CORPUS_VERDICT_DECISIONS.md`, new and uncommitted against
`1853e59b54c8f3674d0deb0fcb723c99d732f74d`. The reviewer did not write it and ran no gate command.

**What reproduced.** Every quantitative figure in the file was recomputed from committed bytes and
matched, most of them exactly:

    claim (decision file line)                            recomputed                     verdict
    per-opener defence, retired A -> committed (:122-127) 22.6326/26.2020/31.4762/       exact
                                                          39.4328/42.8775 ->
                                                          25.6986/28.8804/32.7833/
                                                          36.6526/48.3873
    per-opener call share, same rows (:122-127)           17.5162/19.2140/22.6148/       exact
                                                          26.5433/25.3351 ->
                                                          19.6312/20.9776/22.4389/
                                                          21.0853/20.3007
    quarter-to-one bands, both tables (:189-201)          all ten endpoints              exact
    option-B defence column (:87-88)                      27.2763/29.9216/34.1151/       exact
                                                          36.7568/49.0233
    purity table (:475-479)                               3211 cells, 1.050/95.0 and     exact
                                                          1.324/73.9; 18431 1.170/85.9;
                                                          4521 1.433/64.1
    19 shared keys, 36-19=17 (:481-483)                   19 shared, 17 A-only           exact
    d046ac9 chart: 36 spots, max two raises (:59-62)      36 spots, max 2 raises         exact
    `t6/d100/BB/SB:raise@3.5` and `:call` in A (:61-62)   both present; the only          exact
                                                          first-action-call key in A
    6f15724 chart: 86 spots, 45 with >=3 raises (:69-71)  86 spots, 45 with >=3 raises   exact
    limp count 16 rows / 52 points (:431-432)             16 of 61 rows, 52 of 139        exact
    retired A answers 30 of those 52 (:441-442)           30 (`t6/d100/BB/SB:call`)      exact
    committed artifact sha / 249 spots / export card      all four fields                exact
    (:21-26)

Anchors that hold exactly: `docs/BACKLOG.md:213`; `backlog.yml` 3966, 4316, 6366, 6390;
`comparison.py` 208, 273, 302, 361; `lookup.py:52-57` and `:82-85`;
`vocabulary_corpus_report.py:117`; `run_verify.py:308-311`;
`generate_derived_chart_report.py` 190, 194, 1263, 2974-2975;
`comparison_report.py:53-60`; `latest_sample_comparison_report.txt` 28-35, 46, 106, 115;
`latest_derived_chart_report.txt` 611-612, 1129, 1217-1220, 1243-1280, 1509;
`PHASE_14_CHART_CUTOVER_DECISIONS.md` 1204 and 1286-1288.

**Format.** Running `decision_items()` (`scripts/loop_stage.py:280`) over the file returns ten items,
every one with a valid `Reversibility:` line, and `unanswered_frozen()` blocks on exactly the five
frozen headings. No frozen item carries a pre-filled answer. The format the loop enforces is clean.

**The claim about the two retired charts is true.** `generate_derived_chart_report.py:194` pins
`6f157247cf2217acf358d7cef901a550fc4aae69` (86 spots, 45 with three or more raises, small blind
already at 2.5, no `t6/d100/BB/SB:call`); phase 14 decision 7 at
`PHASE_14_CHART_CUTOVER_DECISIONS.md:1204` pins `d046ac9` (36 spots, no key past two raises, small
blind at 3.5, holds the one limped key). Both halves verified from the bytes. The consequence the
file states is also right: against the 86-key baseline the contract's "no rise at all" at :84-87 is
violated by construction, and there is no small-blind reprice to predict.

**Nothing proposes changing the committed chart**, and no sentence drops the heads-up-flop-terminal
qualification. Item 10's own instances are the only unqualified rake sentences named, and both were
confirmed present in the committed reports.

## Blocker

- [resolved] **Item 1 puts the phase's central ruling to Taylor without the two lines that most directly decide
  it.** The item argues option A from phase 14 decision 7 and option B from the generator constant,
  and cites neither of the following.

      docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md:97-99 - "Where the committed and retired
      charts both answer the same corpus decision, the report says how often they disagree and in
      which direction, reading the retired chart from git history at the pin phase 14's decision 7
      names." The contract itself already names the pin, for at least one of its own criteria. Item
      1 (:52-56) quotes only ":82" and ":85-86" and presents the baseline as an open two-way choice.

      reports/active/latest_derived_chart_report.txt:1309-1311 - "What is printed instead is the
      delta itself, recomputed from the two committed charts, so that the later phase has the
      measurement its band will be drawn on rather than a claim about it", immediately above the
      option-B deltas at :1313-1317. That is the committed report telling phase 17 which deltas to
      draw its band on, and it is the strongest argument for option B anywhere in the tree. The
      direction matters: option B's five deltas are -1.578, -1.041, -1.332, -0.104, -0.636, all
      negative, against option A's mostly positive column, so the two baselines pre-register
      opposite predictions at four of five openers.

  A frozen item exists to hand a human the evidence. This one omits the contract line that answers
  it and the report line that argues against the recommendation.

- [resolved] **Item 9 is filed `runtime-reversible` and its own closing sentence states the frozen test.** The
  file defines frozen as "the choice fixes a bar a later measurement is graded against" (:12-13).
  Item 9 closes at :534-535 with "Recorded because it silently decides which decisions the phase's
  headline prediction is graded on." Those two sentences cannot both stand.

      Item 3 registers a per-opener band; item 9 fixes the population each band is graded over, and
      excludes every big blind facing an open plus a caller (:528-530). Choosing the grading
      population is part of the pre-registration, not a report-time detail, and it is the selector
      most available to be quietly widened once a band is missed. Freezing it costs nothing: the
      loop already halts at items 1, 2, 3, 4 and 10, so no additional stop is created.

- [resolved] **Item 6's recorded default is two defaults, and which one applies depends on unruled item 1.**
  The `Answer:` line at :359-361 is unconditional, but :402-408 says "Under option B of item 1 that
  check must be deleted, because the baseline answered 15 four-bet-facing spots." The loop takes a
  recorded default and proceeds; there is no single recorded default here to take. The class is
  wrong for the same reason as item 9.

      The priority order at :386-397 decides the three per-cause coverage costs the contract grades
      at :83, "the rate must rise only where phase 14's two exclusions and the limp account for it,
      and nowhere else. A rise outside them is a defect." Cause 5, the unmatched residual, is
      whatever the four causes above it did not absorb, so the ordering decides whether that
      criterion can report a defect at all. That is a bar this phase's own measurement is graded
      against, which is the file's frozen test. It also installs a generator that "exits non-zero"
      (:406-407), so the choice reaches the gate rather than only the report.

- [resolved] **Two counts inside frozen items do not reproduce, and each contradicts the file's own evidence.**

      "the baseline answered 15 four-bet-facing spots" (:76, repeated at :408). Recomputed from
      6f15724's bytes: 45 spots carry three or more raises. 30 of them have exactly three raises,
      which is hero facing a four-bet - 15 priced at 22.5 and 15 priced at 100. The remaining 15
      carry four raises and are hero facing a five-bet. So the four-bet-facing count is 30, or 45
      including the five-bet spots; 15 is only the `raise@22.5` subset, which is how :69-71 words
      it, and the two later sentences relabel that subset as the whole. Item 6's zero-rise check is
      written against this figure.

      "it publishes three of the four figures the plan calls unpublished" (:248-249). The ExecPlan's
      four unpublished figures are at docs/exec_plans/active/PHASE_17_CORPUS_VERDICT.md:51-56.
      `latest_derived_chart_report.txt` publishes two of them: the per-opener defence delta and band
      (:1313-1317) and the old-versus-new disagreement count and direction (:1509-1512). It does not
      publish cell purity over the shared spots, and it does not publish refusal movement split by
      cause - which is exactly what item 4's own "what survives" list at :275-291 keeps. Two, not
      three.

- [resolved] **Line anchors into `reports/active/latest_derived_chart_report.txt` are wrong in four items,
  including the quote item 10 asks Taylor to rule on.** The report is byte-identical between
  `9bbdcf4` and this worktree, so the drift is in the citations, not in a stale copy.

      cited                                    quoted text actually at    where the cited range lands
      :1315-1319 (:88, :131, :255)             1313-1317                  four of the five delta rows
      :1386-1387 (:562, item 10)               1376-1377                  the "What this chart does
                                                                          not answer" heading
      :1385-1396 (:267, three explanations)    1376-1381                  the bounds list
      :1398-1408 (:269, bounds paragraph)      1389-1410                  partial
      :1420-1427 (:280, miss-code split)       1424-1429                  stops one line before the
                                                                          2527 -> 129 row it quotes
      :1421-1423 (:282)                        1420-1422                  off by one
      generate_derived_chart_report.py:1306    1304, docstring 1307-1308  a blank line
      (:520)

  Item 10 also derives "a report contradicting itself 170 lines apart" (:559) from the wrong anchor;
  the true distance is 159. The quoted text is correct everywhere, so no conclusion moves, but item
  10 is a ruling request whose evidence a reader is meant to open at the named line.

## Non-blocker

- Item 8's recorded default takes option (a), the 19 shared chart keys, while the item's own
  consequence paragraph at :491-493 says option (b) "is the population the contract's sentence is
  about". Option (c), both with a primary named, is listed at :489 and not taken. The item argues
  against its own default, and because the item is `runtime-reversible` nobody is asked. Either
  publish both rows or drop the sentence conceding (b). (Reading "shared spots" at contract :62-63
  as shared spot keys is defensible, which is why this is not a blocker.)
- Item 9's `Answer:` spans two lines, :511-512. `decision_items()` (`scripts/loop_stage.py:290-291`)
  keeps only the last line that starts with `Answer:`, so the default the loop records and reports
  is "off the spot key the lookup asked about, matching" with the regex silently dropped. Put the
  regex on the `Answer:` line.
- Item 3's denominator paragraph (:224-229) estimates "several cells will hold three to five calls"
  from the pooled 57/125 and 7/20. The exact per-opener counts are already committed at
  `reports/active/latest_derived_chart_report.txt:1323-1332`: humans 15/20/27/43/20, Pluribus
  5/none/3/7/5. Only the Pluribus cells are that thin. The item also requires the report to "decline
  to read a band on a cell below a stated minimum" without stating the minimum, so the item leaves
  the one number a stage-9 author would want fixed in advance unfixed.
- Contract anchors are off by one or two in two places: ":82" for "The baseline is the retired
  chart" (:52) is 81-82, and ":85-86" for the 36-key sentence (:53) is 84-85.
- The header says "Written at stage 3 by lane A" (:3). The lane is at stage 2; stage 3 is the human
  gate that reads the file. The preamble's own sentence at :6-7 has this right.
- Item 4's claim that "Nothing in `reports/active/` uses" the option-A baseline (:277-278) holds.
  `latest_derived_chart_report.txt:656` mentions `expectations/six_max_nl25_100bb.json`, which is the
  GTO Wizard expectations column and a different file from the retired chart of the same stem. Worth
  a clause in the item so a later reader who greps does not think the claim is false.

## Alignment

- The retired-chart pin disagrees between two committed records, and one of them asserts they agree.
  `generate_derived_chart_report.py:194` pins `6f15724`; phase 14 decision 7 at
  `PHASE_14_CHART_CUTOVER_DECISIONS.md:1204-1205` pins `d046ac9` and says it is "what the committed
  derived-chart report already reads the retired chart from", which is verifiably false. Item 1
  :100-103 already commits to filing this and should. Proposed id:
  `RETIRED-CHART-PIN-DISAGREES-BETWEEN-GENERATOR-AND-RULING`. This is drift phase 17 cannot fix from
  inside its scope, since the generator is phase 14's.
- Line anchors into gate-regenerated reports go stale the next time the generator's prose moves, and
  six of them in this file are already wrong at the commit they were written against. A decision
  list should cite a report by section heading or by the quoted line's own text. Proposed id:
  `A-DECISION-LIST-CITES-A-REPORT-BY-LINE-AND-THE-LINE-MOVES`. Neighbours exist
  (`A-GENERATED-REPORT-CAN-GO-STALE-WITH-THE-GATE-STILL-GREEN`, backlog.yml:5356;
  `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`, backlog.yml:5418) but neither covers a
  citation into a regenerated file.
- `PREDICTION-CANNOT-BE-BLIND-TO-A-COMMITTED-MEASUREMENT` (backlog.yml:6366) should be extended with
  the fourth file item 4 found, as item 4 :310-314 proposes. The sharpest instance is
  `latest_derived_chart_report.txt:1295-1311`, which names the phase 14 pre-registration, voids its
  numbers, and then hands phase 17 the deltas its band is to be drawn on. A pre-registration whose
  inputs are printed for it by the report it will be graded against is the general defect, stated
  more plainly than the entry currently states it.
- `CALIBRATED-REALIZATION-CARRIES-ITS-TRAINING-RAKE` (backlog.yml:4316) should carry item 10's two
  instances by file and line, as item 10 :595-599 proposes. Confirmed at
  `comparison_report.py:53-60` and `generate_derived_chart_report.py:2974-2975`, which are the
  generators; the committed text is at `latest_sample_comparison_report.txt:28-35` and
  `latest_derived_chart_report.txt:1376-1377`.


## Coordinator resolution, 2026-09-06

All five blockers were fixed by lane A, the author of the decision list, not by the reviewer and not
by the coordinator. The reviewer's text above is unedited apart from the `[resolved]` markers the
driver requires on every bullet inside `## Blocker`.

- Blocker 1. Item 1 gains a section quoting both lines in full - the contract's :97-99, which names
  the pin through phase 14 decision 7 and so reads for option A, and
  `latest_derived_chart_report.txt:1309-1311`, which instructs the later phase to draw its band on the
  other baseline. The sign consequence is stated: option B's five deltas are all negative against
  option A's mixed signs, so the two baselines pre-register opposite predictions at four of five
  openers.
- Blocker 2. Item 9 reclassified `frozen-into-data`, `Answer:` emptied.
- Blocker 3. Item 6 reclassified `frozen-into-data`, `Answer:` emptied, and its single conditional
  default replaced by three named options with the zero-rise check stated as deleted rather than
  relaxed under item 1's option B.
- Blocker 4. Both counts corrected. The coordinator re-derived the four-bet count independently from
  `6f15724:data/artifacts/preflop/six_max_100bb_rakefree.json`: the histogram of `raise@` tokens over
  the 86 spot ids is {0:1, 1:10, 2:30, 3:30, 4:15}, so 30 spots face a four-bet and 15 face a five-bet,
  and the file's earlier 15 was the `raise@22.5` subset. The reviewer's figure and lane A's correction
  agree with that recount.
- Blocker 5. All 41 explicit `file:line` citations re-verified against current bytes; sixteen were
  wrong and are corrected.

Format re-validated by the coordinator against the real parser rather than a reimplementation
(`scripts/loop_stage.py` `decision_items` and `unanswered_frozen`): ten items, every one classed, and
the human gate blocks on seven - 1, 2, 3, 4, 6, 9 and 10 - each with an empty `Answer:`.

Lane A also reports a parser trap worth carrying forward: `decision_items` reads only the first line
of an `Answer:`, so a wrapped answer is silently truncated. Both remaining reversible answers are now
single lines.
