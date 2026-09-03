# Stage 4 re-cut, independent mechanical review

Read-only. The reviewer wrote none of the work under review and has not read the parallel poker
review. Worktree `~/projects/poker-bot-worktrees/phase-14`, branch `phase/14-chart-cutover`,
tree at HEAD `4a57531` plus the uncommitted re-cut. Nothing in the repo was modified except
this file.

**What was run.** `pytest_derived_chart`'s eleven files; every migrated file, individually and
together; `ruff check --no-cache .` (clean); `check_file_sizes.py` (clean); `check_scope.py`
(clean); `tests/test_loop_machinery.py`; `tests/test_execplan_delegation.py`,
`test_command_registry.py`, `test_import_smoke.py` (20 passed);
`scripts/generate_derived_chart_report.py` against the unmodified tree; `scripts/loop_stage.py
--phase 14` read-only. `check_gate_bite.py` was **not** run, per the brief.

**Every number below was measured in this tree**, including the ones the brief supplied.

## What reproduces

- `pytest_derived_chart`: **57 failed / 52 passed / 3 skipped**. Matches.
- The migrated set (nine files plus `test_simulator_reports.py`): **258 passed / 31 failed**,
  not "roughly 119 more passes", and not "all nine are green today" as the ExecPlan hand-off
  says. Every one of the 31 reds I inspected is chart-dependent (`assert 86 == 249`,
  `t6/d100/LJ/rfi` absent, a price of `100.0` in the ladder) rather than a migration error. The
  red is correct; the hand-off's baseline is the hazard, because it makes the greens read as
  coverage and the reds as breakage, which is backwards on both halves.
- **All six new files are registered** in `scripts/run_verify.py` and no registered path in any
  command is missing or misspelled (checked by resolving every `tests/` and `scripts/` argument
  in `COMMANDS`). Question 7 is clean.
- The canary bookkeeping is as its author recorded: `MULTIWAY_EXPOSURE_THRESHOLD_PCT = 10.0`
  occurs **zero** times in `chart_derivation.py`; `    if validation_errors:` occurs **exactly
  once** in `generate_derived_chart_report.py`; 72 mutation ids, none duplicated; the only
  consequence is `test_every_mutation_applies_exactly_once_to_its_file` failing on `assert 0 ==
  1`, which I reproduced, and which runs under no command but the catch-all `pytest`.
- **M1 is correct.** Re-derived from the export: `given_up` is exactly
  `{("BB", ("SB:call",))}` and `len(kept)` is exactly 35 against the 36-shape set the test
  builds. All fifteen opener-facing-a-single-three-bet shapes are inside the 219. The
  arithmetic holds - see B4 for the baseline it holds against.
- **M2 is sound.** The counterfactual is a real probe: today's floor run reports
  `{composite: 24, reference-check-fold: 0}` and `hands_counted() == 12`, the docstring's
  figures to the digit. The five reference check-folds never raise or call, so hero is only
  ever asked first-in and is not asked in the big blind; all five first-in spots are committed,
  so zero refusals and `hands_counted() == RUN_HANDS` follow. The `decided_at ==
  FIRST_IN_POSITIONS` line is a live guard. Its limit is real but stated: all three assertions
  pass for any chart with five correct openers and 244 wrong spots.
- **No surviving fragments of the superseded sets.** `143` and `123` appear nowhere in the
  re-cut files. Every occurrence of 86, 36, 5,626 or "six-spot" is a docstring about history or
  a constant about the retired chart on purpose (`RETIRED_SPOTS = 86`,
  `RETIRED_REACH_FLOOR_BP = 200`). The superseded module constants (`COMMITTED_SPOTS = 86`,
  `BASELINE_REFUSALS = 290`, `REACH_FLOOR_BP = 200` as a live floor) are gone.
  `test_chart_derivation.py`'s ruled-number block reproduces the contract exactly and
  re-derives every entry by its own walk of the export. Question 1 is clean.

---

## Blocker

### B1. [resolved] `tests/test_chart_counterfactual_arms.py:198` is permanently red, and the figure behind it is wrong in four documents

**Resolved 2026-09-03.** Confirmed by an independent measurement agent, which also corrected the diagnosis:
"149 against 69" is not one bad measurement but two comparison rules spliced together, and reproduces under
neither. The skip rule gives 149 against 260 and the common-cell rule 42 against 69, both passing. Taylor
ruled the arm is scored over every spot in its partition; the contract criterion was rewritten in place,
recorded as decision 54 and diagnosed in `RANK-ARM-RESTRICTION-RESTED-ON-A-SPLICED-FIGURE`. All ten
partitions were re-measured and all pass, the tightest margin now being hero=LJ at 75 against 96, so no
partition sits one cell from red. The restated test asserts both self-consistent readings pass, so
reinstating the restriction requires making one of them fail first.

```python
assert arm_refuses(loose_solved, loose_permuted), (
    "the unrestricted reading now passes, so the restriction to closed spots has stopped"
    f" being load-bearing ...: {loose_solved} against {loose_permuted}"
)
```

Measured: **149 against 260**. `arm_refuses(solved, other)` is `solved >= other`, so this is
`False` and the assertion fails.

Every name in that expression is defined inside `tests/` - `inversions`,
`reverse_hand_ranks`, `ROW_KICKERS`, `play_not_fold`, `partitioned`, `arm_refuses` in
`test_chart_cutover_evidence.py`, `selected` in `test_chart_derivation.py` - and the committed
export is not rewritten by stage 6. **There is no implementation that turns this green.**
Stage 5 freezes it, `pytest_derived_chart` and `pytest` are red forever, and the gate can never
close.

The figure it was written against is **149 against 69**, and that is wrong. It appears in four
places, all wrong together:

- `docs/exec_plans/active/PHASE_14_CHART_CUTOVER.md`, ruled-numbers section: "over all 219
  spots the arm reads 149 against 69 and fails"
- the same claim in `## Next Agent Bootstrap`, under "Open, and not to be invented"
- `tests/test_chart_counterfactual_arms.py` module docstring
- `tests/test_derived_chart_report.py:132-134`, in `ARM_ROWS`'s docstring

The solved side reproduces (149). The counterfactual side does not: this file's own
`inversions(reverse_hand_ranks(cells), ROW_KICKERS)` over the 219 gives 260, so the
unrestricted reading **passes**, and passes wide. The 69 came from a different comparison rule
- restricting to pairs present in both the original and the reversed grid - and under that rule
both sides move together, to 42 against 69, which also passes. "149 against 69" takes the
solved side from one rule and the counterfactual side from the other.

**Two things follow, and the second is worse than the red.** The assertion cannot pass. And the
claim repeated all through this phase - that restricting the rank arm to spots closed under
reversal is the only thing between the gate and a red - is unsupported under either
self-consistent reading. The Bootstrap says "Anyone touching the tolerance, the closed-spot
definition, or which comparisons count is touching the only thing between that gate and a red."
Measured, the arm passes with the restriction and without it.

This is a halt and a decision, not a lane edit: the contract and the Bootstrap both forbid
adjusting the tolerance, the closed-spot definition or which comparisons count to clear a red
here, and any repair touches one of the three.

### B2. [resolved] `tests/test_chart_counterfactual_arms.py:258` is permanently red: thirteen committed spots fold every hand

**Resolved 2026-09-03** by correcting the assertion rather than the fixture. No over-folding map can move a
grid that already folds every hand, so the fixture was right and the assertion was wrong to assume every
grid holds a non-zero cell. It now asserts the fixture differs at exactly 249 minus 13 spots, with
`SPOTS_FOLDING_EVERY_HAND = 13` pinned and confirmed: eleven SB, one CO, one BTN.

```python
over_folding = [{name: value * 0.5 for name, value in cells.items()} for cells in grids]
...
assert sum(1 for before, after in zip(grids, over_folding, strict=True) if before != after) == len(grids)
```

Measured: **236 == 249** fails. Thirteen of the 249 have a `play_not_fold` grid that is `0.0`
at all 169 classes, so halving them is the identity. Measured paths, all at `raises faced 2`:
one CO, one BTN, eleven SB - for example `(1,1,1,2,0,1,0,0)` and `(1,1,1,1,1,2,0,0,0,0)`.

Same shape as B1: `grids` comes from `play_not_fold` over the frozen export, so no stage-6 work
moves the count. It reads 236 forever.

The test's substantive claims - that both arms accept a mis-assigned chart and an over-folded
one - already passed on the two lines above this one. Only the "the fixture is actually
different" guard is wrong, and it is wrong because it assumed every committed grid has a
non-zero cell.

**Both B1 and B2 are invisible to the driver.** `check_tests_authored` asks only that the
command is red on an assertion. `scripts/loop_stage.py --phase 14` prints "this stage's checks
pass; run --advance to move on" against this tree.

### B3. [resolved] `RAISE_ACTION_INVERSIONS = 27` does not reproduce under the relation the phase pinned

**Resolved 2026-09-03.** Two further independent walks confirmed this reviewer: 43 pre-merge total, 28
pre-merge visible-only, 41 and 25 post-merge. Taylor ruled the same day that the relation reads the merged
weight, what the bot plays, and that his acceptance stands at the true count. Pinned as
`RAISE_ACTION_INVERSIONS = 41` and `RAISE_ACTION_INVERSIONS_INVISIBLE = 25`, and now re-derived from the
export by a frozen test rather than substring-matched in the report, which closes the hazard this finding
named. Recorded as decision 55, with two supersession notices on decision 50.

`tests/test_derived_chart_report.py:98`, used at `tests/test_derived_chart_report_ranges.py:221-227`.

The fourth relation is pinned as data at `tests/test_chart_cutover_evidence.py:98-104`:
`Relation("pair ladder on the raise weight", "raise-weight", 12)`, comparisons
`ADJACENT_PAIRS`, tolerance `TOLERANCE_PCT = 1.0`, over all 249. I ran that exact definition:

| relation | measured | pinned constant |
|---|---|---|
| pair ladder | 114 | `PAIR_INVERSIONS = 114` ✓ |
| suited over its offsuit twin | 7 | (the suit arm's 7, `ARM_ROWS`) ✓ |
| row kicker ladder | 181 | `KICKER_INVERSIONS = 181` ✓ |
| **pair ladder on the raise weight** | **43** | **`RAISE_ACTION_INVERSIONS = 27`** ✗ |

Its three siblings in the same constant block are the pinned relations' cell counts and all
three reproduce. The fourth does not, and no scoping I could construct reaches 27:

```
all cells 43 | spots 34 | invisible to play-not-fold 28 | both hands played >=99  26
both played ==100  22 | invisible, counted as spots 24 | both >=99 as spots  22
tolerance 0.5 -> 45 | tolerance 2.0 -> 37 | three-bet family only 26
```

The nearest readings are 26 and 28. The **28** is decision 50's own words - "27 pair inversions
are visible only on the raise action, invisible to every relation and both counterfactual arms"
- measured here as `inversions(raise_weight) not also found in play-not-fold`, which is 28, not
27. `tests/test_chart_cutover_evidence.py:511` asserts that quantity is `> 0` and does not pin
it, so nothing in the suite catches the gap.

**Failure scenario.** The contract requires the generator to re-derive every figure it prints
and forbids a hand-typed count (`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`). A
stage-6 generator that re-derives the fourth relation prints 43; `assert 27 in numbers` then
fails unless 27 happens to appear elsewhere in the section. The only way to satisfy the frozen
test is to type 27, which is the thing the contract names.

This needs Taylor, not a lane: 27 is decision 50's figure and decision 50 is `frozen-into-data`.
Either the constant is mislabelled - it is an invisible-to-play-not-fold count, not a relation
count, and even then it is 28 - or the figure is wrong. Both are decisions.

### B4. [resolved] The cutover's cost is measured against a chart deleted before this phase restarted

**Resolved 2026-09-03.** Confirmed: the helper reproduced the deleted 36-spot GTO Wizard chart byte for
byte. It now reads the retired 86-spot chart at a git pin rather than off disk, deliberately, because stage
6 replaces that path in place and a working-tree read would compare the new chart against itself. The true
split is 21 kept and 30 given up, and the 30 are exactly the retired shapes with three or more raises in
front of hero, asserted as that characterisation rather than as a bare count. The false claim that the
retired chart answered 30 limped decisions is gone: it declares no `:call` key at all.

`tests/test_spot_vocabulary_downstream.py:303-316`, used at `:463-468`.

`retired_chart_shapes()` builds the **36 spots of `six_max_nl25_100bb.json`**, the GTO Wizard
chart, "reproducing its spot ids at `da05adf`". The contract says plainly what phase 14
retires: "The GTO Wizard chart is **already deleted**, and what is committed is
`six_max_100bb_rakefree.json`, **86 spots from the superseded export**", and decision 53 pins
"Retired chart: 86 spots, 36 carrying a sizing entry".

Measured against the artifact actually on disk:

| baseline | shapes | kept by the 249 | given up |
|---|---|---|---|
| the 36-spot GTO Wizard chart (what the test uses) | 36 | 35 | **1** (`BB/SB:call`) |
| the 86-spot chart the contract retires | **51** | 21 | **30** |

The 30 given up are the four-bet family. The test's own enclosing docstring at `:447` says
"the chart answers 249 nodes where the retired one declared **86** keys" and then measures
against 36 shapes of a different file - the contradiction sits inside one docstring.

Its downstream claim is false of the chart on disk. `:458-460` says "the retired chart declared
`t6/d100/BB/SB:call` and answered 30 of the corpus's 52 limped decisions from it", so
"`CHART-CANNOT-ANSWER-A-LIMPED-POT` moves from a guard to a claim". The 86-spot chart contains
**no `:call` key at all** (measured: zero keys containing `:call`), so it answered none of the
52 and the entry was already fully true before this phase.

**Failure scenario.** The test goes green at stage 6 and the packet cites "the cutover gives up
the limped pot and nothing else" as the measured cost to the trainee. The true cost against the
chart being replaced is 30 of 51 shapes. That is the packet requirement "the exclusions in
poker terms, each with the evidence that took it" answered with the wrong evidence, frozen.

Note the same file's sibling `ruled_cost_shapes()` was deleted by this migration and this one
was left, which is how it survived. The phase's own report lane gets this right -
`test_derived_chart_report.py:108` has `RETIRED_SPOTS = 86` and reads
`six_max_100bb_rakefree.json` out of git history - so the two halves of the same stage disagree
about which chart is being retired.

---

## Non-blocker

### N1. Four passing tests establish nothing, because the command they run is already red

`tests/test_derived_chart_report_validators.py:619-638` (`--retired-commit`, two parameters) and
`:688-700` (`--artifact`, two parameters). Each is `assert result.returncode != 0` plus
`assert not (tmp_path / "report.txt").exists()`.

I ran the generator on the **unmodified** tree: it exits 1 and writes nothing ("refused: the
artifact's 86 spots disagree with the walk's 51"). All four pass today without the bad pin or
the corrupted artifact contributing anything. There is **no positive control** in the file
asserting that `run_report` with good arguments exits 0.

Scenario after stage 6: the generator ships without a `--retired-commit` or `--artifact` flag,
argparse exits 2 on every invocation, all four stay green, and the packet records that the
command refuses a bad pin and a wrong artifact when it in fact refuses everything. One
`run_report(tmp_path)` expecting `returncode == 0` closes it.

This matters more than the usual silent pass, because
`test_a_wrong_artifact_fails_the_command_rather_than_being_rendered[commit-a-spot-above-the-exposure-threshold]`
is the contract's named kill for the canary "one commits a spot above the exposure threshold".

### N2. One vacuous skip has no size guard and can skip over an empty walk

`tests/test_chart_conversion.py:294-299`. `assert len(unpriced) == SPOTS_OFFERING_NO_PRICE`
where the constant is `0`; the stated premise is "every committed spot offers hero a raise" but
what is asserted is "no committed spot lacks one", true of an empty set. Line 298 then
intersects an empty set with anything. If `selected()` ever returns nothing, the test skips as
VACUOUS having measured nothing.

It is the only one of the four vacuous sites missing the guard. The three that have it are the
model: `test_derived_chart.py:514` asserts `len(first_in) == 5` first;
`test_chart_conversion.py:264` asserts `len(priced) == SPOTS_OFFERING_A_PRICE == len(keyed)`;
`test_spot_vocabulary.py:559` asserts `offered` before claiming `two_priced == []`. One line -
`assert len(keyed) == spec.COMMITTED_NODES` - fixes it.

The sibling at `:314-321` (`assert lengths == {1}`) is guarded against a wholly empty payload,
because `set() != {1}`, but not against a payload holding one entry.

### N3. The suite's three vacuous criteria are not the contract's three

The contract names the two-price sizing schema, the no-raise half of the sizing invariant, and
**the jam-and-named-raise collapse rule**. `test_derived_chart_report_validators.py:578`
enforces exactly that on the report's rows.

The frozen tests label a different three: `test_chart_conversion.py:302` (two-price, "the
first"), `:280` (no-price, "the second"), and `test_derived_chart.py:499`, labelled "The third
vacuous criterion" - but that is the **limp** criterion, which is not one of the contract's
three. The collapse rule has no frozen test at all; `grep -rn collapse tests/` returns one hit,
in a docstring.

Stage 6 can satisfy both, so this is not a contradiction. What is missing is a test asserting
the collapse rule's premise still holds - that under `add_allin: false` no committed node
offers both a jam and a named raise - which is the whole point of the convention: a premise
that goes false must turn something red rather than leave a stale label.

### N4. The only check that the equity relation never became a gate holds of an empty list

`tests/test_chart_cutover_evidence.py:635-639`. `validators = [n for n in dir(report) if
n.startswith("validate_")]` is never asserted non-empty, and the claim is `assert not [n for n
in validators if "equity" in n]`. If stage 6 names its validators anything but `validate_*` at
module scope - a leading underscore, a `check_` prefix, methods on a class - the list is empty
and decision 42's only enforcement holds vacuously.

### N5. Three published tables are held up by per-row checks that cannot fail

- `tests/test_derived_chart_report_ranges.py:95` - `assert int(solved) >= 0 and int(transposed)
  >= 0`. `LADDER_ROW` captures `(\d+)`, which cannot match a sign, so this is true of every
  string the regex can produce. A generator printing `solved 0 transposed 0` on all fifty group
  ladders passes.
- `tests/test_chart_cutover_evidence.py:611` - `assert isinstance(value, int) and 0 <= value <=
  len(groups[name])`. `value` is incremented by `any(...)` once per node, so the bound holds by
  construction. The only real check on the fifty figures is `:612 assert
  any(published.values())`, which one non-zero cell out of fifty satisfies.
- `tests/test_chart_counterfactual_arms.py:191` - `assert all(count >= 0 ...)` where the count
  is `len(nodes) - closed` and `closed` counts a subset.

`tests/test_chart_cutover_evidence.py:510` is the same shape but decorative rather than
load-bearing: the real check in that test is `:511 assert invisible_to_play_not_fold > 0`,
which does bite.

### N6. The merged-flat defence check compares two columns of the same printed row

`tests/test_derived_chart_report_ranges.py:449-452`. Both `defence` and `raise_plus_call` come
from `MERGED_ROW.findall(body)` - the line the generator printed. Nothing in this test reads the
export or the artifact. A generator computing one number and printing it into both columns
passes, as does one printing `0.0 0.0` for all twenty merged spots.

The real merge check exists against the export at `tests/test_derived_chart.py:605-651`, so
decision 45 is covered. This assertion is decoration wearing the shape of a check, and its
message ("the merge has to preserve the range to the basis point") reads as if it were the one.

### N7. Two report checks match digits anywhere in a section

- `tests/test_derived_chart_report_ranges.py:219-227` - `numbers = [int(v) for v in
  re.findall(r"\b(\d+)\b", body)]` then `assert count in numbers` for 114, 181, 87 and 27. Any
  appearance of the digits satisfies it, in any role; `\b(\d+)\b` also splits `93.20` into `93`
  and `20`, contributing stray tokens. This is the assertion B3's wrong constant hides behind.
- `tests/test_derived_chart_report_cutover.py:230-232` - `"100"` is satisfied by `100bb` or
  `1000`; `"2.5"` by `12.5` or `2.50`. Two of the seven bounds tokens are noise.
- `:235` - `str(report.MERGED_CELLS) in body` is a bare substring, so `165` matches inside
  `1650`.

### N8. Two disjunctions that are effectively unfalsifiable

- `tests/test_derived_chart_report_ranges.py:78` - `assert "noise" not in body.lower() or "not
  noise" in body.lower()`. A section calling the mixed-cell family "mixing noise" passes as long
  as the phrase "not noise" appears anywhere in it, which the prose the docstring describes
  would naturally contain. This is decision 51's whole enforcement in the rendered report.
- `tests/test_derived_chart_report_cutover.py:341-345` - `assert "does not" in text or "not
  establish" in text`, over a report of several thousand characters.

### N9. The band-size check is skipped for any band whose label the generator spells differently

`tests/test_derived_chart_report_ranges.py:384-396`. `assert {name.strip() for name, *_ in rows}
& set(sizes)` needs one published band to name a family this file can size; every other band
whose label does not match a key skips `:392` and is held only to `int(over) > 1`. A report
publishing one correct band plus nine bands over two members each, all mislabelled, passes the
test whose stated job is the contract's "Do not publish a band measured over a subset of the
family it names".

### N10. Widening the de-rake check from six rows to ten made it weaker, not stronger

`tests/test_preflop_committed_charts.py:478-499`. This stage changed the docstring from
"Measured over the six of the reference's eleven rows the chart still holds a cell for" to
"Measured over all ten of the reference's frequency rows now" and widened `gaps` accordingly.
The assertion is unchanged: `assert max(gaps) > 0.5`.

With ten gaps instead of six, one row over half a point still satisfies it, and there are now
four more chances for that one row to exist. A conversion that widened the small blind's open
and left the other nine rows identical to the raked reference passes the test whose docstring
says "a chart still within half a point of a raked reference would mean the conversion moved
nothing". `min(gaps) > 0.5`, or a per-row loop, is what the docstring claims.

### N11. `93.20` and `3.85` are the pre-merge figures and nothing says so

`tests/test_derived_chart_report.py:75-76` pins `PURE_AT_99_PCT = 93.20` and
`MIXED_BELOW_90_PCT = 3.85`, and `test_derived_chart_report_ranges.py:235` only checks the
strings appear in the report. Measured over the 18,431 cells at non-zero reach:

- **pre-merge (the solve's own grid): 93.20 pure at 99 percent or more, 3.85 mixed below 90** -
  the pinned figures, exactly.
- **post-merge (the chart the phase publishes): 93.48 and 3.66.**

A stage-6 generator that computes purity off the artifact it just wrote prints 93.48 and the
report test fails. Which grid the figure is measured over is not stated anywhere, and it is the
one place in the phase where the merge changes a published number.

### N12. `RETIRED_SIZINGS` names two different files in two frozen files

- `tests/test_derived_chart_report.py:50` = `.../sizings/six_max_100bb_rakefree.json`, read out
  of git at a pin and asserted to **exist** there.
- `tests/test_preflop_committed_charts.py:54` = `.../sizings/six_max_nl25_100bb.json`, asserted
  at `:193` to **not exist**.

Both are satisfiable, because they are different paths. But one identifier means "the table the
report reads from history" in one file and "the table that must be gone" in the other, and the
first names the path stage 6 rewrites with the new sizing table. Same shape as the raise-action
/ raise-weight clash that was already caught, one level down.

Related and load-bearing for stage 6: `scripts/generate_derived_chart_report.py:109-113` still
points `RETIRED_CHART_PATH`, `RETIRED_SIZING_PATH` and `RETIRED_CHART_COMMIT` at
`six_max_nl25_100bb.json`, while `test_derived_chart_report_validators.py:627` forces the chart
and its sizing table to share a basename. Stage 6 must repoint all three.

### N13. The exposure canary's own docstring gives an amount that would not bite

`verification/mutations.yml:1272` replaces `10.0` with `10.05`, and explains why: the node it
must admit measures 10.0234, the next refused node is at 10.1189, so any value in that gap
admits exactly one spot.

`tests/test_derived_chart_report_validators.py:694-695` describes the same artifact as what a
converter produces "with the threshold nudged by **two hundredths** of a point". Two hundredths
is 10.02, **below** 10.0234, so a threshold moved by that amount admits nothing and the canary
does not bite. Five hundredths is right; the docstring is arithmetically wrong, and it is the
docstring a stage-7 reader would follow when the canary is questioned.

**The author's own recorded concern is correct and should be carried forward.**
`tests/test_chart_derivation.py:463` kills the canary by reading
`module.MULTIWAY_EXPOSURE_THRESHOLD_PCT` back, which proves the constant is pinned, not that the
predicate uses it. If stage 6 declares the constant and hardcodes ten in the predicate beside
it, the pytest commands go red and `generate_derived_chart_report` does not, because the
report's walk would never see the moved threshold. That is a finding about stage 6's
implementation shape, not a reason to drop the command from `must_fail`. The decision not to
author a second wrong-artifact canary, because
`the-derived-chart-report-renders-whatever-it-is-handed` already attacks the same line, is
right.

### N14. Three assertions in the migrated files that a wrong stage-6 chart still passes

- `tests/test_postflop_fallback_components.py:286-292` - `assert
  composite.decide(request).code.startswith(CHART_PREFIX)` where `CHART_PREFIX =
  "preflop-chart:"`. Both outcomes carry it: I have seen
  `StrategyRefusal(code='preflop-chart:lookup:spot-not-covered')` and
  `StrategyDecision(code='preflop-chart:weighted-draw:raise[...]')` in this tree's own failure
  output. The assertion cannot tell a decision from a refusal, and it is applied to
  `first_in_preflop_query()`, the query the whole migration turns on. Ship a 249 with every key
  misspelled and this stays green, exactly as it is green now against the 86.
- `tests/test_full_table_preflop.py:696-700` - `test_no_two_covered_spots_share_a_hand_class_ordering`
  calls `library.hand_classes_for(spot_key)` twice with one argument and asserts they are
  equal. It cannot fail for any return value, including `()`, and it visits 5 of 249 spots. The
  defect is pre-existing, but **this stage edited that exact line** (it inlined `second`) and
  left it, and stage 5 freezes it.
- `tests/test_sample_comparison.py:701-702` - `assert entry.seen_in_self_play in {True, False}`
  is the whole body, satisfied by `True`, `False`, `1`, `0`, `1.0`, and by an empty inventory.

Worth recording on the other side: the `any(...)` tightening at
`tests/test_sample_comparison.py:395-407` is real and does bite. The pair was replaced with
`seen == named & reached` / `unseen == named - reached` against a recomputed read, plus
non-emptiness on both halves.

### N15. Stale present-tense docstrings that stage 5 freezes

- `tests/test_spot_vocabulary.py:148` - "every price in every committed menu carries weight for
  at least one class, the small blind's 100bb jam included, which six classes take at SB/rfi."
  The next paragraph of the same docstring says the 100bb stack went with the cutover and the
  test's own assertion at `:169` is `prices == [2.5, 7.5, 22.5]`. Self-contradictory in one
  docstring.
- `tests/test_simulator.py:22` and `tests/test_simulator_reports.py:15` both say
  `test_simulator_reports.py` "is not registered yet". `scripts/run_verify.py:207-213`
  registers it in this same working tree.

---

## Alignment

### A1. Three test files land at exactly 700 lines against the 700-line cap

`tests/test_derived_chart_report_validators.py`, `tests/test_full_table_preflop.py` and
`tests/test_sample_comparison.py` are all exactly 700; `tests/test_chart_arrival_probability.py`
and `tests/test_postflop_fallback.py` are 699. `check_file_sizes` passes, so this is not a
finding against the stage. It is drift: N1's positive control lands in the 700-line validator
file, so the fix forces a split first. This is the contract's "300 of 300 lines" problem
reproduced in the test tree, and the ExecPlan already records what it costs. Belongs in
`backlog.yml`: the cap and the convention of long explanatory docstrings are in tension, and
the resolution is splitting early rather than compressing.

### A2. The stage-4 driver cannot see anything in this review

`check_tests_authored` asks only that the phase's `pytest_*` command is red on an assertion. It
cannot tell a test describing 249 spots from one describing six; it cannot tell a red stage 6
can clear from one it cannot (B1, B2); and `check_file_sizes` is not among the stage's driver
checks, which is how two files got past 700 lines on the first pass and was found only by
running the script by hand. The driver printed "this stage's checks pass; run --advance to move
on" against a tree holding two permanently red assertions.

A cheap discriminator exists and would have caught both: for each red, ask whether the failing
expression reads anything outside `tests/` and the frozen export. If it does not, the red is
not waiting on stage 6. Belongs in `backlog.yml` against
`LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`, which already owns the neighbouring defect.

### A3. Nothing records which previously green gate commands the migration turned red

The migration is required at stage 4 and is correctly done, but it reddens completed phases'
commands: `pytest_preflop`, `pytest_simulator`, and the commands covering
`test_full_table_preflop.py`, `test_spot_vocabulary.py`, `test_table_state_strategy.py`,
`test_sample_comparison.py` and `test_postflop_fallback_components.py`. Measured: 31 failures
against 258 passes across the ten migrated files.

That is the right state. What is missing is a list of it. The ExecPlan's "The gate is red by
design until stage 6" section names only the phase's own commands, so a stage-7 reader has no
way to tell a command the migration reddened from one that regressed, and the contract's
"Previously completed phase gates remain verifiable" has nothing to check against. Belongs in
`backlog.yml`: a migrating stage should record the commands it reddens and the count it expects
back.

### A4. Eleven counts are copied across files instead of imported from one owner

The brief's convention is that a count has one owner and siblings import it. It holds for the
reason codes, the exposure threshold and its two extremes, and the arms' permutation and
parameter names - all owned once in `test_chart_derivation.py` or
`test_chart_cutover_evidence.py` and imported. It does not hold for: the ten-partition arm table
(`test_chart_cutover_evidence.py:201` `PARTITIONS` and `test_derived_chart_report.py:114`
`ARM_ROWS`, the same forty figures as literals in different column orders, agreeing today - I
checked all ten rows); 249; 18,431; 165; 132; the rank-arm floor of 5; the four relation names;
the 5/5/20/219 family split; the price list; 86; and the one-point tolerance.

All agree today. It is one point of drift each, and B1 shows the failure mode already realised:
the wrong "149 against 69" figure sits in `ARM_ROWS`'s docstring as well as in the arms file and
the ExecPlan, so correcting one leaves two stale. Belongs in `backlog.yml` as the convention
this phase adopted and did not finish applying.

### A5. Two names for one set of ten spots, and a third name with the same value

`tests/test_chart_derivation.py:102` `COMMITTED_WITH_A_CALLER_ALREADY_IN = 10` and
`tests/test_preflop_committed_charts.py:66` `NON_BLIND_SQUEEZE_SPOTS = 10` are the same set: the
committed spots where hero is not the big blind and a cold caller is already in. Neither imports
the other. The word "squeeze" is also the contract's term for the **refused** bucket
`derivation:big-blind-squeeze-spot`, whose count is also 10
(`BB_SQUEEZE_REFUSED_NODES`). Three constants, two meanings, one value, in a phase whose third
selection clause is about exactly this distinction. Nothing breaks; a later reader wires the
wrong one.

---

## Stage-5 checklist item, not a finding

`verification/freeze.lock` is unmodified and lists none of the six new files. That is expected
mid-stage-4 and `freeze_tests.py` rewrites it, but it is the one thing that must be regenerated
after the blockers above are resolved and before the freeze, or the new files are frozen at the
wrong content or not at all.
