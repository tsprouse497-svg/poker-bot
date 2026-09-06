# Phase 14, stage 9: independent mechanical review of the audit packet

Read-only. The reviewer wrote none of `reports/phase_audits/PHASE_14_CHART_CUTOVER.md`, none of the
stage-9 generator edits, and none of the two new `backlog.yml` entries. Nothing in the tree was
changed except this file.

**Question answered:** is every number recomputable and every claim narrower than the evidence behind it?

**What was re-derived rather than read off a document.** From
`data/artifacts/preflop/six_max_100bb_rakefree.json` and the committed export: the hand-index top eight
and the 48 never-played classes; the 106 cold-call-downstream spots at 42.5703 percent by count and
0.016416 percent by arrival, factor 2593; the 81 spots no arriving class raises and that all 81 are
inside the 106; AA/KK/QQ/AKs at zero reach at all 81 and AKo at 47 of 81 with 6,619 bp its maximum at
`t6/d100/SB/LJ:raise@2.5,BTN:call,SB:call,BB:raise@7.5`; the six premium-fold cells, all AKs, all at
full reach, 28.14 / 9.59 / 7.98 / 7.26 / 6.65 / 5.04; the big blind's 6.0674 percent three-bet against
a lojack open; AA and KK at exactly 1.000 and AKs at 0.9978 minimum over the 15 opener-versus-three-bet
spots; the 62/63 merged-family split with its 17 and 16 distinct classes, unanimous per spot and
100-to-0 at every integer bar from 50 to 99; the 165 moved cells with 93 pure before, 144 after and 51
turned pure; the exposure leak at 8,660 all-zero nodes, 15,536 non-closing outcomes and a widest
shortfall of 0.026759 at the key the backlog names; 74 mutations against 58 at merge base `ada5205`,
16 new and none removed, nothing naming `table_state/`; 2,755 of 7,546 added lines under `src/` and
`scripts/` in 19 files, largest `scripts/generate_preflop_equity_matrix.py` at +634, and 2,740 of 7,175
at `72efe9d`; 48 registered gate commands, 47 derived, 29 and 28 unnamed by any mutation with no test
command among them; 219 backlog entries, 193 deferred, 26 done; 55 decision items with 38 correction
notices; 16 limped inventory rows summing to 52 decision points. `pytest_derived_chart` re-run: 111
passed, 4 skipped. All of those reproduce exactly.

## Blocker

- **The packet says corpus refusals RISE and the numbers in the same sentence show them collapsing by an order of magnitude.** Packet line 387: "Refusals rise on both populations, the ruled cost rather than a regression: Pluribus 430 of 502 decisions refused before against 27 of 502 after; humans 2,099 of 2,546 before against 112 of 2,546 after". 430 to 27 and 2,099 to 112 are falls of 94 percent and 95 percent, which is the whole point of going from 86 spots to 249. The report carries the same false sentence at `reports/active/latest_derived_chart_report.txt:1282` - "The refusal rate rises, on both populations" - and then compounds it two lines later with "an agreement rate over a smaller sample is the shape to expect", where the after sample is larger on both populations (475 against 72, and 2,434 against 447). `reports/active/latest_derived_chart_report.txt:1405` confirms the direction independently: `lookup:spot-not-covered` goes 2527 to 129. This is a sixth false statement in the report that stage 9's E4 lane did not catch, and the packet republished it rather than re-measuring it. Fix the report's paragraph in `corpus_section` and the packet bullet together.

- **The report's new purity sentence is false: 73 of the 165 moved cells were pure on calling, not "most".** `scripts/generate_derived_chart_report.py:2002-2003` now prints "so most of what the merge moved was already pure on calling before it" (`reports/active/latest_derived_chart_report.txt:618-620`). Re-derived from the export over `merged_cells(export)`: of the 165, **93 were pure at 99 percent before the merge and 73 of those 93 were pure on `call`** (16 pure on raise, 4 pure on fold); 144 are pure after, so exactly 51 turned pure, which is the figure the generator derives correctly. 73 of 165 is 44 percent and is not "most". The packet's own wording at line 438 - "most of the 165 were already pure" - is true at 93 of 165 and is the sentence the report should carry. This one was introduced by the very edit whose job was to remove a false statement from that paragraph.

- **`A-FROZEN-TEST-DOCSTRING-ASSERTS-WHAT-ITS-TOLERANCE-ADMITS` contradicts itself between its title and its body.** `backlog.yml:2791` titles it "its tolerance is forty times the worst case it must not admit"; the body of the same entry says "0.05 is nearly twice today's widest shortfall of 0.0268". Checked against the test: `tests/test_derived_chart_report.py:476` asserts `pytest.approx(100.0, abs=0.05)` and the measured worst shortfall is 0.026759, so the ratio is 1.87 and the body is right. Forty reproduces under no reading of those two numbers. A backlog title is what gets quoted - stage 8's own non-blocker 5 was about exactly that - so this outlives the phase in the wrong form.

## Non-blocker

- **"about 125 times as much" reproduces under no pairing of the band it is drawn from.** Packet line 148 and `reports/active/latest_derived_chart_report.txt:717`. The published band ends are 0.10 to 0.70 at R = 0.65 and 8.76 to 13.04 at R = 0.85. The four ratios are 87.6 (8.76/0.10), 130.4 (13.04/0.10), 12.5 (8.76/0.70) and 18.6 (13.04/0.70); the midpoint ratio is 27.25. `PHASE_14_CHART_CUTOVER_DECISIONS.md:3278-3279` carries the band and no ratio at all. The sentence says "the same fold costs about 125 times as much", which asks for a per-spot ratio the phase never published. Either publish the per-spot ratio or drop the multiplier.

- **Checklist row 4 cites nothing.** Packet line 65: "| 4 | Every committed cell matches the export | 18,431 cells at non-zero reach, 0 mismatches | PASS |". The packet's own preamble promises `report -> Section, "row label"` for every figure. The report prints 18431 only inside running prose at lines 609, 618 and 1054 and never prints a mismatch count anywhere; no backlog id is named. The claim is almost certainly true - `convert_preflop_export.py --check` is inside `pytest_derived_chart`, which passes - but a non-coding reviewer cannot open a named row and find it, which is the row's stated job.

- **The equity-matrix provenance figures have no source in the repo.** Packet line 411: "computed here rather than taken from GTOpen - exactly, in 1m35s, cross-checked four ways including a brute force using none of its three reductions". `data/artifacts/preflop/equity/preflop_eq169.source.json` records the exhaustive method and eight named checks and no runtime; `scripts/generate_preflop_equity_matrix.py:31` names three reductions but documents no brute-force run that omits them; nothing under `reports/`, `docs/`, `backlog.yml`, `src/` or `tests/` contains "1m35" or "brute". Two numbers here were typed from somewhere the packet does not name.

- **The exposure backlog entry's 70 / 13 / 57 decomposition mixes two rules.** `EXPOSURE-WALK-DROPS-MASS-AT-NODES-NO-HAND-REACHES` says "70 of the 249 committed spots leak some mass ... Only 13 leak enough to show at the four decimal places the report prints; the other 57 leak under half of a ten-thousandth". Re-measured: 109 committed spots have any positive leak, 76 leak above 1e-12, and 70 is the count above 1e-9, an unstated float-noise cutoff. Under "at or above half a ten-thousandth" the count is 12, not 13; 13 is the count under the generator's own rule of rounding each printed column to four places and comparing the sum to 100.0. So 13 + 57 = 70 holds only by taking each term from a different rule. Everything else in the entry reproduces to the digit, including 8,660, 15,536, 0.0268 and the named widest key.

- **A third note-versus-report disagreement is left unreconciled while two others are reconciled by name.** The packet's "Two committed documents disagree" section fixes the 60/28-versus-62/63 pair and the 30.39-versus-19.78 pair. It does not mention that `stage-08-review-poker.md:150` says "KTs or KJs four-bets above 50 percent at 9 of the reference's 15 spots" where the report and the packet both say 10. The note's table at lines 138-148 lists only nine rows and omits `SB_vs_BB_3bet`, whose reference reads 78.270 in the report. The packet quotes the right number; it just leaves a reader who opens the note with an unexplained gap.

- **The "165 mixed cells pure" falsehood also survives in a frozen test docstring the packet does not name.** `tests/test_derived_chart_report_ranges.py:218` still reads "the merge turns 165 mixed cells pure, so the chart this phase writes reads 93.48". The packet's known-limitations section names exactly one thing that "could not be fixed here" - the exposure test's docstring - which reads as the complete list of surviving instances and is not.

- **The ExecPlan marks the stage-9 independent reviews as landed before either existed.** `docs/exec_plans/active/PHASE_14_CHART_CUTOVER.md:270-271` gives R1 and R2 status "landed"; the packet header line 5 lists reviews for "stages 1, 2, 3, 4, 6, 7, 8, 9". At the time both were written `reports/phase_audits/reviews/PHASE_14_CHART_CUTOVER/` held no stage-9 file. The ExecPlan is a committed living document and R1 is the stated check that the coordinator's no-delegation exception was not self-certified, so recording it green in advance is the one status that cannot be pre-filled.

- **The equity relation is described as measuring the thing the packet elsewhere says nothing measures.** Packet line 408: "**The equity relation**, the one measurement here that asks whether a range is good poker". Packet line 431: "Nothing here measures whether a range is good poker." The report carries the reconciling qualifier - "a measurement toward that gap is not the gap filled" - and the packet drops it. The prohibition is met on the letter, since "asks" is not "measures", but a reader gets the two sentences four pages apart with nothing joining them.

- **The big blind's three-bet range is named as fifteen classes and priced at the frequency of twenty-two.** Packet line 487: "against a lojack open it three-bets AA KK QQ JJ TT 99 AKs AKo A5s KQs KJs QJs JTs 87s 76s at 6.07 percent". Re-derived at `t6/d100/BB/LJ:raise@2.5`: the combination-weighted raise frequency is 6.0674 percent and it is taken over 22 classes with non-zero raise weight, including ATs at 27.67 percent and A4s at 9.16 percent. The fifteen named are those at 80 percent or better. The list is a fair description of the shape; the frequency beside it is not that list's frequency.

## Alignment

- `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` - the big blind's cost band and the "125 times" multiplier are the last figures in a gate report that no command re-derives. `reports/active/latest_derived_chart_report.txt:719-720` says so out loud: "These two rows are quoted from ... item 34 ... every other figure in this report is re-derived by the command that prints it". The contract's own rule at the Evidence section is that no count in a packet may be hand-typed. Whatever fixes the multiplier should also decide whether an EV band a generator cannot compute belongs in a generated report at all, or in the packet citing the decision item.

- `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS` - the same shape produced blocker 1 above. The corpus paragraph in `corpus_section` is prose asserting a direction beside numbers the generator computed, and nothing compares the two. The four false statements this stage fixed and the fifth it found were all of this kind; a check that reads a direction word beside the pair of numbers it describes would have caught every one of them, including the one that got through.

- `COVERAGE-IS-DECISION-MASS-AND-A-TRAINEE-MEETS-A-PER-SEAT-RATE` - the packet is careful about this at line 33 and then spends four sections on findings whose weight is per cell and per spot rather than per arrival: the six premium folds, the 62/63, the four-bet composition. The per-seat rate nobody has measured is the denominator all of those want, and until it exists a reader has to hold two weightings in their head to read the packet's own findings against its own coverage claim.
