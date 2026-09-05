# Stage 8 independent review, mechanical: does the phase's record match the tree

Read-only review by an agent that wrote none of this work, reviewed none of the earlier stages,
and read none of the other reviewers' notes before measuring. Subject: every committed document
this phase wrote or changed between `c45013b` and `72efe9d`, measured against the artifact that
actually shipped.

`scripts/check_gate_bite.py` and `scripts/run_verify.py` were NOT run, on instruction. No
`verification/.mutation_in_progress` sentinel was present at any point and no source file was
mutated. The working tree carried `reports/active/verify_results.json` (epoch and per-command
durations only) and `verification/loop_runs/14.yml` (stage 7 to 8) as modified; both were left
alone. No file was written except this one. Every figure below was produced by a script this
reviewer wrote into the session scratchpad, run against the committed export and the committed
artifact in memory.

## What reproduced

Stated first, and it is most of it.

**The census, the coverage and the split.** Own walk over `load_solver_export(COMMITTED_EXPORT_PATH)`:
249 committed, 33,362 depth, 348 exposure, 10 squeeze, summing to 33,969; raises faced 5 / 25 / 219;
arrival-weighted coverage **98.5949** percent, split 51.9237 / 38.5422 / 8.1290 by raises faced.
Widest admitted exposure **9.8642**, narrowest refused **10.0234**. 26 big-blind squeeze spots inside
the depth clause, 16 of them also over the exposure threshold, so the bucket of 10 and the
reverse-order 332 both follow. The inexpressible bucket is empty. Every one of these matches the
contract, the ExecPlan and the report.

**The sizing table.** 249 entries, **81** empty and 168 not; every list one entry long; every weight
exactly 1.0; distinct prices exactly 2.5 (5 spots), 7.5 (25) and 22.5 (138), and 138 + 81 = 219, so
the 81 empty maps are all three-bet-facing. `SIZING_NOTES` is true in every particular I could
measure.

**The merge.** 20 merging spots, **165** cells moved, **40** of them carrying a hand's entire weight
and **73** at 99 percent or more. `merged_cells` and the report agree.

**186.** 186 of the 249 committed nodes still have three or more seats live at the node, so the
seat-count reading would have refused every one. Pinned in a frozen test as well.

**Arrival.** 44 of 249 round to zero in parts per billion and exactly **2** are zero on the unrounded
product. The stepwise-versus-once rounding docstring reproduces at **31** disagreements. The 106
downstream-of-a-cold-call family is 996,262 of 6,068,788,530 ppb, 0.0164 percent, and the count and
weight rows differ by a factor of 2,593 as printed.

**The equity matrix and its source card.** 114,244 bytes = 169 x 169 x 4; sha256 matches the card;
`row_0` is `22` and `row_168` is `AA` under `gtopen_class_index`; the diagonal is exactly 0.5
everywhere; max symmetry deviation 2.9802e-08 as stated; all six named equity checks reproduce to
the hundredth (22 vs AKo 52.65, 88 vs AKo 55.16, AA vs 72o 88.20, AA vs KK 81.95, AKo vs QQ 43.24,
AKs vs QQ 46.05).

**The freeze.** `verification/freeze.lock` names **42** files summing to **905** test functions; every
sha256 matches the tree; the tree holds exactly those 42 files and no others. Comparing the test
function names at `c45013b` against `HEAD` by AST: **zero lost and zero added** across all three
re-freezes. `check_scope` is satisfied - nothing in the diff from `base_commit` `d635b49` falls
outside `approved_scope` plus `standing_scope`. The six test files and `verification/mutations.yml`
that fall outside it were changed before that base and each is covered by a dated
`scope_change_log` entry.

**The canaries.** `verification/mutations.yml` holds **74** entries, no duplicate ids, and for every
one the `find` string occurs exactly once in the file its `file:` field names, with `find` never
equal to `replace`. Zero broken against the current tree.

**`docs/CORPUS_COMPARISON_LIMITS.md`.** The refusal partition reproduces exactly: 139 refusals =
**52** limped-pot decisions (the asked key opens with a call) + **52** big blind facing an open with a
cold-caller + **25** four-bet-or-deeper chains + **10** `lookup:hand-class-not-covered`, all ten at
raises-faced 2. Refusal rate 20.3 percent in the big blind and 1.0 percent at the lojack, as
published. Scored denominators 2,434 human and 475 Pluribus, summing with 139 to the 3,048 in
`repo_facts.yml`. 4.6 percent of the sample.

**The retired raked chart's shape.** `git show a386c77^:data/artifacts/preflop/six_max_nl25_100bb.json`:
36 spots, split 6 with no raise (5 first-in plus `t6/d100/BB/SB:call`), 15 facing one raise, 15
facing a three-bet - which is the vocabulary report's "five first-in ranges, 15 facing a single
raise, 15 facing a three-bet, and the big blind facing a small-blind limp" exactly.

**Both counterfactual arms, all ten partitions.** Every one of the ten rows the ExecPlan lists
matches the report's rendered row, including the whole-set 7/167 and 181/433 over 208 scored with
19,774 and 20,279 skipped.

**`repo_facts.yml`, `phase_status.yml`, `STATUS.md`.** 139 refusals, 61 distinct refused spots, 3,048
decisions, 499 committed hands: all measured live. Phase 14 is `active`. 213 backlog entries, none
at `status: open`. The 22 committed keys naming a seat twice reproduce at 22. The chart does not
limp: zero call weight at any first-in spot, and no first-in cell names `call` at all.

## Blocker

**1. The committed artifact's notes give the excluded nodes the committed set's coverage figure, and
it is the one sentence a later phase reads first.**

`data/artifacts/preflop/six_max_100bb_rakefree.json`, `audit_fields.notes`, first paragraph, written
by `src/poker_training_bot/solver_artifacts/chart_provenance.py:19-22`:

> The chart commits 249 of that solve's 33,969 action nodes and **excludes 33,720 of them, which is
> 98.59 percent of the preflop decisions the bot ever faces.**

98.5949 percent is what the **committed** 249 carry. Measured, summing `node_arrival_ppb` over the
export:

    committed 6,068,788,530 ppb of 6,155,278,160  ->  98.5949 percent
    excluded                                       ->   1.4051 percent

The excluded 33,720 carry **1.4051** percent of the decisions the bot ever faces. Read the sentence
the other available way - 33,720 as a share of 33,969 nodes - and it is 99.2670 percent, which is
not 98.59 either. There is no reading on which the sentence is true.

The phrase is not ambiguous by accident: `reports/active/latest_derived_chart_report.txt:1227` uses
the identical wording for the opposite quantity - "What a trainee gets is the other side of the same
sentence: 98.5949 percent of the preflop decisions the bot ever faces". The artifact hands the
excluded family the trainee's number.

This is the file every later phase is measured against, nothing re-derives the prose, and the
paragraph's own next line is "Every absence is a decision, and a reader who cannot see why would
read a missing range as a gap in the conversion". A reader who takes it at face value concludes the
chart answers 1.4 percent of preflop play.

Commands: `python -c` over the artifact for the notes text;
`sum(node_arrival_ppb(bp, n) for n in ex.nodes)` against the same sum over
`[n for n in ex.nodes if is_committed_node(bp, n)]`.

[resolved] Re-measured independently at 98.5949 committed / 1.4051 excluded / 99.2670 of nodes, and
`chart_provenance.ARTIFACT_NOTES` rewritten so each figure is stated over the set it was measured on
before the artifact was regenerated by the converter; `latest_derived_chart_report.txt:1227` needed
no change, its 98.5949 being derived from `Walk.coverage_pct` and already on the committed side.

**2. Three committed sites say nine spots hold a hand whose whole weight is on calling. It is
fifteen.**

`chart_provenance.py:41`, shipped inside the artifact:

> Merged and not deleted: **at 9 of those spots** a hand's whole weight sits on calling, and deleting
> would leave a hand with no answer at all.

`src/poker_training_bot/solver_artifacts/chart_derivation.py:164`, the docstring that justifies
merging rather than deleting:

> merged and not deleted, because **at nine of these spots** a hand's whole weight is on calling and
> deleting would leave a row of zeroes

And `scripts/generate_derived_chart_report.py:2055`, rendered into
`reports/active/latest_derived_chart_report.txt:749`, which is where a non-coding reviewer meets it:

> Merged and not deleted, and the difference is a hand with an answer against a hand with none: **at
> nine of these spots** a hand's whole weight sits on calling, so deleting would leave a row of
> zeroes

Measured over the 20 merging spots, counting cells where `_flat_bp(node, column) == 10000` (every
strategy row in the family sums to exactly 10000, checked):

    cells at a hand's entire weight on calling:  40
    spots holding at least one:                  15

The 15 are `BTN/CO:raise@2.5`, `BTN/HJ:raise@2.5`, `BTN/HJ:raise@2.5,CO:call`, `BTN/LJ:raise@2.5`,
`BTN/LJ:raise@2.5,CO:call`, `BTN/LJ:raise@2.5,HJ:call`, `SB/BTN:raise@2.5`, `SB/CO:raise@2.5`,
`SB/CO:raise@2.5,BTN:call`, `SB/HJ:raise@2.5`, `SB/HJ:raise@2.5,BTN:call`, `SB/HJ:raise@2.5,CO:call`,
`SB/LJ:raise@2.5`, `SB/LJ:raise@2.5,BTN:call`, `SB/LJ:raise@2.5,CO:call` (all `t6/d100/`).

The 40 is the figure the frozen tests carry (`tests/test_derived_chart.py:622`, "165 cells move, 40 of
them a hand's entire weight"), so the cell count is right everywhere and only the spot count is
wrong. It is robust to every reading I tried: filtering on arriving reach at 0, 10 and 100 basis
points all give 15 spots and 40 cells. Nine reproduces under nothing.

All three sites need the same one-word fix and a chart rebuild. `data/artifacts/preflop/**`,
`solver_artifacts/chart_*.py` and `scripts/generate_derived_chart_report.py` are all in
`approved_scope`; the report line is a plain string literal, so nothing re-derives it either.

[resolved] Re-measured independently at 15 spots / 40 cells over the 20 merging spots and 108 spots
/ 748 cells over all 249, and all three sites now say fifteen and name the set both figures are
over; the report's pair is no longer a literal at all but derived from a new `Walk.whole_call_cells`,
so a later set change moves it by itself.

## Non-blocker

**3. `chart_selection.cold_call_index`'s counterfactual does not reproduce, and it is the evidence for
keeping an exemption.** The docstring at `chart_selection.py:223` says dropping the
already-invested exemption "commits **361** nodes with **321** three-bet-facing spots instead of 219".
Measured by patching `cold_call_index` in a fresh process to keep only the big-blind exemption and
recounting: **346** committed, split 5 / 25 / **316**. The argument survives - the exemption still
moves 97 nodes and the direction is unchanged - but the two numbers offered as its proof are both
wrong, and a later phase re-running the counterfactual will read this as a regression.

**4. "The big blind folds 93 percent of its range there" is the top of a range presented as the
figure.** `scripts/generate_derived_chart_report.py:1468`, rendered into
`latest_derived_chart_report.txt`, explains why the exposure clause admits the 10 squeeze spots.
Measured per spot with `action_frequency` over the fold branches (combo- and reach-weighted, which is
what "of its range" means):

    0.8499  0.8573  0.8787  0.8899  0.8928  0.9095  0.9133  0.9163  0.9286  0.9333

Mean 89.70 percent, and **5 of the 10 fall below 90**. 93 is the maximum. The sibling claim in
`chart_selection.is_big_blind_squeeze_spot`'s docstring, "the big blind folds better than nine times
in ten here", holds at 5 of the 10. What is load-bearing does survive: the same docstring's "leaves
that branch carrying under nine points" is exact, with exposures running 3.7368 to **8.9845**. That
this literal is un-derived is already filed under
`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`; that its value does not hold is not, and the
filing should carry the measurement so the fix is a re-derivation rather than a re-typing.

**5. Two `backlog.yml` titles describe a chart this phase retired, and titles are what
`docs/BACKLOG.md` renders into its table.**

`KICKER-LADDER-INVERSIONS-ARE-PUBLISHED-AS-SOLVED` is titled "The chart plays a weaker kicker more
than a stronger one **at 23 committed cells**". Its own 2026-09-03 extension re-derives the family
over the committed 249 at **181** with 87 exempted, leaving 94 with no story; 23 was the count over
the retired 86-spot cut. The entry corrects itself in the body and not in the line a reader scans.

`CHART-HERO-MUST-NEVER-LIMP` is titled "Nothing forbids a committed chart from limping, **and today's
chart does**". Measured against the shipped artifact: the five first-in spots carry **zero** cells with
call weight, and not one of them names `call` in its menu at all. The body is explicit that the
limping chart was the GTO Wizard one, so only the title is stale - but the diagnosis it carries (no
schema rule forbids it) is still owed and still correct, so this is a retitle rather than a closure.

**6. "The retired chart" names two different artifacts in two gate-regenerated reports.**
`latest_preflop_strategy_report.txt:12` says "The retired chart held 36 spots", which is the GTO
Wizard raked chart and is true - I measured it at 36. `generate_derived_chart_report.py:194` says in
terms "**The retired chart is the 86-spot `six_max_100bb_rakefree.json`**, not the GTO Wizard NL25
chart". A reader moving between the two reports gets 249-against-36 in one and 249-against-86 in the
other for the same phrase. Neither sentence is false; the collision is. Worth naming because the
36-spot sentence was introduced by `511b3c3`, the commit whose subject is "Stop two gate reports
arguing against their own figures".

**7. The multiway mispricing figure ships in the artifact and in the report and is re-derived by
nothing in this repo.** "understates real three-way equity by about 10.5 points and by 14 on the
suited connectors" appears in `ARTIFACT_NOTES`, at
`generate_derived_chart_report.py:1392` and again at `:2435`, all three as plain string literals. Its
only source is `PHASE_14_CHART_CUTOVER_DECISIONS.md:377-378`, a stage-4 reading of GTOpen's own
source taken over the 38,828-node tree. It is the stated reason two of the three selection clauses
exist, and the contract's rule is "No count in this contract or in a packet may be hand-typed rather
than re-derived". The repo now commits a 169x169 all-in equity matrix but it is heads-up, so this
figure cannot be re-derived here at all - which is the thing to record rather than to fix in this
phase.

## Alignment

- `THE-ARTIFACT-DESCRIBES-ITS-OWN-CENSUS-IN-PROSE-NOTHING-CHECKS` - the two blockers above are this
  entry's failure mode firing for the third time, and this is the first pass that measured the notes
  rather than reading them. The entry is accurate as filed, and its own staleness - the three
  literals it quotes are gone from `chart_provenance.py`, which now ships about a dozen different
  hand-typed figures - is already recorded in the 2026-09-04 stage-7 extension on
  `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`, so neither needed re-finding. What this
  pass adds is that a spot check is not enough: 186, 165, 20, 81, 51.61, 44 and 2 all reproduce, and
  the two that do not sit between them.

- `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` - covers items 3, 4, 5 and 7. Its diagnosis
  is exactly right and its proposed cheap fix reaches none of them: a docstring counterfactual, a
  report string literal, a backlog title and a decision-record measurement are all outside what a
  generated-report comparison can see. The entry already says the honest minimum is that a count in
  prose cites the field it came from; items 3 and 5 are the case for extending that to titles and to
  counterfactual claims, which cite nothing by construction because the state they describe does not
  exist.
