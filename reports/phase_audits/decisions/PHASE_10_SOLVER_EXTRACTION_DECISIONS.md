# Phase 10 judgment calls

These are the choices that decide what the committed solver export *is*. No test in this
repo settles them, because an export that answers the wrong question passes a schema check
exactly as green as one that answers the right question.

Every item carries a reversibility class, which the loop driver reads at stage 2 to decide
whether it must stop for a human.

- `runtime-reversible`: the choice only changes behaviour at query time, so a later edit
  changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact that every later
  phase is then measured against. The loop halts until a human answers.

## Ruled by Taylor, 2026-08-18

Every item was answered on its recorded default. Three costs were accepted rather than
avoided, and they are listed here so the record says what was given up and not only what was
chosen.

**Ruling 3 is narrowed.** Limps leave the committed solve. The accepted cost is 21 of 3,048
corpus decision points staying refused, the twelve limped rows of
`reports/active/latest_sample_refusal_inventory.txt`, and the committed solve having no
small-blind limp frequency of its own - that number now comes from the parity solve, which
keeps limps. What is bought is that "dump the entire solved tree" can be followed literally:
38,828 action nodes rather than 289,036, with no filtering rule anywhere in the extractor.

**The zero-slack directional bound is given three points of slack.** The accepted cost is
that a genuinely tighter rake-free solve could pass on one number by up to three points. The
at-most-one-below clause is what limits it: a uniformly tighter extraction still fails on
nine of ten.

**The small blind leaves the opening-order check by name.** The accepted cost is that the
tight, tolerance-free ordering check no longer covers the position with the widest range and
the most movement between raising and limping. What replaces it there is a lower bound
against the reference's raise-plus-limp sum, which is weaker.

Two rulings correct documents rather than choosing between options, and both need saying
plainly. `docs/GTOPEN_SOLVER_NOTES.md` records a config body that omits `realization`, and
that omission is the difference between a usable range and a big blind that defends 99.71
percent. `docs/V2_RULING_MITIGATIONS.md` section 1 asserts that rake changes no ordering and
that the directional bound needs no tolerance; both are false, and the corrections live in
decisions 4 and 5 rather than in that document, which this phase may not edit.

## What the probe established first

The decisions below are written against measurements rather than estimates. The probe ran
GTOpen at commit `4aee435`, CPU engine, on this machine. Four of its findings change what
the decisions can even be, so they come first.

### The tree is far larger than anything previously costed

Six-handed, 100bb, `open_raises` `[2.5]`, `limp: true`, rake-free:

| | limps in the tree (ruled) | no limps (the only config previously built) |
|---|---|---|
| `action_nodes` | **289,036** | 38,828 |
| `nodes` | 622,336 | 83,123 |
| `arena_mb` | 841.4 | 112.4 |

Limps are 87 percent of the tree. Every action node carries a strategy row per action
across 169 classes, so at roughly three and a half actions per node the whole tree is on
the order of 170 million frequency values: about 680 MB as raw `f32`, about 340 MB
quantised to 16 bits, over a gigabyte as JSON. `docs/V2_ROADMAP.md` estimated the *derived
chart* at roughly 12 MB. The whole solved tree is two orders of magnitude past that.

### Solve time is not the constraint. Extraction is

The ruled config reached GTOpen's own default target - summed best-response gap below
0.01 bb - at **iteration 400 in 473 seconds**, CPU only. A second run under the corrected
config reached 0.00699 bb at iteration 300 in about the same time. Solves are minutes, not
hours, so a determinism run and a parity solve are cheap.

The walk is the expensive half, and it was not on anyone's list. `/api/preflop/node` walks
from the root on every call, so extracting 289,036 nodes is 289,036 requests whose cost
grows with depth. Node queries also block while a solve runs, because they need the mutex
the solve holds, so a request during a solve hangs rather than erroring.

### The `realization` field was missing from the config, and it decides everything

`PreflopConfig` carries a `realization` field that the accepted config body in
`docs/GTOPEN_SOLVER_NOTES.md` does not mention, so every previous run took its default.
GTOpen's preflop engine has no postflop play in it: flops resolve at a `pot_share`
terminal that splits the pot by equity share, scaled by a per-seat realization weight.
That weight is what the field selects.

- `"raw"`: R = 1. Everyone realizes full raw equity.
- `"static"` (the default): R = 1 +/- 8 percent of positional skew at high SPR. Which is
  very nearly raw.
- `"calibrated"`: loads the fitted model in `cache/realization_fit.json`, which is present.

Measured, same tree, same target, only the field changed:

| | default `static` | `calibrated` | expectations file (raked) |
|---|---|---|---|
| BB defends vs LJ | 72.94 | 27.19 | 22.63 |
| BB defends vs BTN | 97.44 | 36.88 | 39.43 |
| BB defends vs SB | **99.71** | 49.03 | 42.88 |
| LJ opens | 14.52 | 18.23 | 17.49 |
| BTN opens | 40.96 | 39.92 | 40.56 |
| SB limps | 60.81 | 1.38 | 13.73 |

Under the default the big blind defends 99.71 percent against a small-blind open, because a
caller realizes its full raw equity and calling 2.5 to reach an equity split is almost
always profitable. That is not a rake effect and it is not poker. Under `calibrated`, four
of the five opening frequencies land within about a point of an independent commercial
solver at a different rake basis, and the big-blind defence ordering reproduces exactly.

**Nothing may be committed under the default.** This is the finding that would have
produced a self-consistent, checksummed, thoroughly reported calling station.

### Two of the three expectations checks are falsified as specified

`docs/V2_RULING_MITIGATIONS.md` section 1 asserts that rake moves the level of all eleven
numbers and the ordering of none, and that the directional bound needs no tolerance at
all. Both claims fail against the measured rake-free solve, and both fail for the same
reason: rake-free changes the small blind's limp-versus-raise mix, and the small blind is
in two of the eleven numbers.

- **Opening order.** Expected BTN, SB, CO, HJ, LJ. Measured SB, BTN, CO, HJ, LJ. Rake-free
  SB opens 53.58 against the raked reference's 34.41, because 12 points of limping became
  raising. The ordering among LJ, HJ, CO, BTN survives exactly.
- **Directional bound.** Nine of the ten opening and defence numbers come back at least as
  wide as the raked reference. BB-versus-BTN defence comes back **tighter**, 36.88 against
  39.43. A 2.55-point miss on one of ten, between a full solver and a preflop-only
  equity-realization model, is solver difference rather than a defect - but the check as
  written calls it a failure and admits no slack in which to say so.
- **SB limp**, 1.38 against 13.73, is a 12-point disagreement that no small tolerance
  admits. It is excluded from the directional bound by design; it is not excluded from the
  parity comparison, and it is the number most likely to fail it.

The corrected checks are decisions 4 and 5 below. They are written before the committed
solve, which is the whole point of authoring them at this stage, and the measurements above
come from a probe solve that is not the one being committed.

## 1. What the committed export contains, and whether limps stay in it

Reversibility: frozen-into-data

These were drafted as two decisions and they are one, because no combination both keeps
limps and commits a whole tree.

`docs/V2_ROADMAP.md` instructs this phase to "dump the entire solved tree rather than the
subset today's vocabulary can express", for a good reason: four-bet nodes are in the solve
and unreachable through a v1 spot key, so an extractor that filters to what fits today
forces a re-extraction after Phase 12. Ruling 3 separately puts limps in the tree.

Held together, those two produce 289,036 action nodes and hundreds of megabytes, in a
repository whose position is that committed data is reviewable and whose gate loads its
artifacts on every run. One of them has to give.

What limps cost, measured: 87 percent of the tree, and 250,208 of its 289,036 action nodes.

What limps buy, measured from `reports/active/latest_sample_refusal_inventory.txt`: 12 rows
and **21 of 3,048 corpus decision points**, 0.7 percent. The raised-pot refusals in the same
inventory are 250 points, and those need Phase 12's vocabulary, not limps. The probe adds a
second cost nobody predicted: under the corrected realization model the solve barely limps
at all - 0.54 percent at LJ, 0.01 percent at BTN, 1.38 percent at SB - so most of that 87
percent of the tree is lines the solution itself never takes.

Ruling 3 was made on an estimate. The measurement says it spends 87 percent of the solve on
0.7 percent of the refusals, in branches the solve almost never enters.

The roadmap's argument against filtering also rests on an assumption the probe undermines,
which is that re-extraction means re-solving. GTOpen's save format (`GTOPREFLOP1`: a magic,
a JSON header carrying the full config, then raw `f32` arenas) travels config and result
together, so a saved solve can be reloaded and re-walked. If save and load work - they are
on the unverified list and must be exercised, not assumed - then any later widening costs a
reload of minutes rather than a re-solve.

Default: **drop limps from the committed solve, and commit that whole tree.** 38,828 action
nodes satisfies the roadmap's no-filtering instruction literally, at a measured cost of 21
corpus decision points. Save the solve outside the repository and record its path, size,
and checksum on the source card, so a limped solve later is a reload rather than a fresh
run. Keep limps in the parity solve, where they are needed for a like-for-like comparison
against a reference file that reports a limp frequency.

Options: drop-limps-commit-whole-tree | keep-limps-prune-by-arriving-mass |
keep-limps-export-expressible-subset-only | keep-limps-export-uncommitted
Answer: [drop-limps-commit-whole-tree]

The alternatives, so the choice is made against them rather than against the default alone.

*Prune by arriving mass.* Keep a node only when the product of aggregate frequencies along
its line clears a threshold, and record the pruned count and mass. Principled, since an
unreached node has no strategy worth reading, and under the corrected realization model it
would remove nearly all the limped tree anyway. It is still filtering, on a different axis,
and it cannot be sized until after the solve, which means committing to a format before
knowing whether it fits.

*Expressible subset only.* What the roadmap forbids. Cheap and it needs the very vocabulary
Phase 12 has not built yet, so the selection rule would have to be invented here.

*Uncommitted.* Honest about the size and gives up the property that makes every number in
this repo checkable offline. It would be the first data in the tree a reviewer cannot see.

## 2. The solve config, in full, including the field that was missing

Reversibility: frozen-into-data

Rulings 1 through 4 fix rake, opening size, limps, and the licence stance. They do not
mention `realization`, because nobody knew the field existed when they were made, and the
probe shows it matters more than any of them.

Default:

```json
{ "positions": ["LJ","HJ","CO","BTN","SB","BB"], "stack": 100.0,
  "posts": [0,0,0,0,0.5,1.0], "ante": 0.0,
  "limp": false, "open_raises": [2.5], "raise_mults": [3.0], "max_raises": 4,
  "add_allin": true, "allin_threshold": 0.67,
  "rake_pct": 0.0, "rake_cap": 0.0, "no_flop_no_drop": true,
  "realization": "calibrated" }
```

`limp` follows decision 1. `realization: "calibrated"` is the substantive change and it is
not a tuning choice: the default produces a big blind that defends 99.71 percent.

The residual limitation belongs on the source card rather than in a footnote. Even
calibrated, this is a preflop-only model that resolves flops by scaled equity share. It is
not a full solve, and the export should say so where anybody reading the chart will see it.

Options: as-defaulted | calibrated-with-limps | static-realization-as-before
Answer: [as-defaulted]

## 3. The exploitability target and the wall-clock ceiling

Reversibility: frozen-into-data

GTOpen measures convergence as the summed per-player best-response gap in big blinds;
multiway has no exploitability proper. Its own default target is 0.01 bb at a 2,000
iteration cap, and the probe reached it at iteration 300 to 400 in under eight minutes, so
the cap is not binding and neither is any sane wall clock.

A target chosen after seeing what a run achieved is not a target, so it is recorded here
ahead of the committed run.

Default: **target the summed gap at 0.01 bb, cap at 2,000 iterations, and record the
achieved gap either way.** No wall-clock ceiling, because the measurement says one would
never fire. Tightening the target is available and cheap now that the cost is known; it is
not taken, because 0.01 bb is the tool's own default and the honest reference point.

Options: gap-0.01-cap-2000 | gap-0.002-cap-5000 | gap-0.01-and-also-tighter-run-reported
Answer: [gap-0.01-cap-2000]

## 4. The orderings check, corrected

Reversibility: frozen-into-data

The measured falsification is above. Rake moves the small blind's limp-versus-raise mix, so
its position in the opening order is not structural, and the mitigations doc's claim that
rake changes no ordering is wrong for exactly two of eleven numbers.

Default:

- **Big-blind defence order holds exactly, SB then BTN then CO then HJ then LJ, no
  tolerance.** Measured to reproduce exactly under the corrected config. This is the tight
  check, and it is the one that breaks immediately on a transposed hand index, a
  mis-assigned actor, or an unnormalised strategy row.
- **Opening order holds exactly among LJ, HJ, CO, BTN, no tolerance.** Later position opens
  wider is structural and survives removing rake. Measured 18.23, 21.56, 26.90, 39.92.
- **SB is excluded from the opening order, by name, with this reason recorded**: it is the
  only position whose opening frequency competes with a limp, and rake is what decides that
  mix.
- **SB opening frequency is instead bounded below by the reference's raise-plus-limp sum**,
  48.14 percent, since rake-free may reallocate between raising and limping but should not
  play tighter overall. Measured 54.96.

Options: as-defaulted | full-five-position-order-as-originally-specified |
orderings-on-defence-only
Answer: [as-defaulted]

## 5. The directional bound, corrected

Reversibility: frozen-into-data

Removing rake should widen play. Nine of ten measured numbers do. BB-versus-BTN defence
comes back 2.55 points tighter, which between a full solver and a preflop-only
equity-realization model is solver difference, not a defect - but a bound with no slack
cannot say that, and the predictable response to a red check is to delete it.

Default: **each of the ten opening and defence numbers must be at least the raked reference
minus 3 percentage points, and at most one of the ten may sit below the reference at all.**
The slack is small enough that a uniformly tighter extraction still fails on nine counts,
and the at-most-one clause is what keeps the check from degrading into a 3-point tolerance
everywhere. The SB limp frequency stays excluded by name, because rake's effect on limping
is not obviously signed.

Both numbers are authored here, before the committed solve, against a probe solve that is
not the one being committed.

Options: minus-3-points-at-most-one-below | zero-slack-as-originally-specified |
minus-5-points-any-number
Answer: [minus-3-points-at-most-one-below]

## 6. The parity tolerance against the expectations file

Reversibility: frozen-into-data

How far may two different solvers at a matched rake basis legitimately disagree about how
often the big blind defends? The probe answers part of it already: at an *unmatched* basis,
four of five opening frequencies land within about a point, while the SB limp frequency is
out by 12 and SB opening by 19. So the disagreement is concentrated in the small blind, and
a single tolerance across all eleven numbers will be set by its worst member.

Default: **five percentage points absolute on the eight opening and defence numbers for LJ,
HJ, CO and BTN, and the two small-blind numbers plus the limp frequency reported without a
pass/fail threshold.** Absolute rather than relative because the failure this check exists
to catch is a gross error - transposed suited and offsuit, an unnormalised row - which moves
a number by tens of points. The small-blind numbers are reported rather than gated because
the measured difference there is a real property of removing rake and of a limp-versus-raise
tree, and gating on it would mean fitting the tolerance to the one thing already known to
disagree.

Options: 5-points-on-eight-report-sb | 5-points-on-all-eleven | 15-percent-relative
Answer: [5-points-on-eight-report-sb]

## 6b. The parity solve's rake basis

Reversibility: frozen-into-data

The parity solve exists to be a like-for-like comparison, and it is only that if its rake
matches what the expectations file describes. The accepted config body in
`docs/GTOPEN_SOLVER_NOTES.md` carries `rake_pct: 5.0` and `rake_cap: 3.0` with no stated
derivation, and the expectations file says only "NL25 rake". If the basis is wrong the
parity comparison measures nothing while looking like the tightest check in the phase.

NL25 is a 25-dollar-cap game at 0.10/0.25 blinds, so the big blind is 25 cents and a rake
cap stated in big blinds is the dollar cap divided by 0.25. A 3 bb cap is therefore a
75-cent cap, which is in the ordinary range for the stake but is not the same claim as
"whatever GTO Wizard's NL25 solution used".

Default: **`rake_pct: 5.0`, `rake_cap: 3.0`, `no_flop_no_drop: true`, and the source card
states that this basis is inferred from the stake rather than read off the reference
solution, so the parity comparison is a comparison at a plausible matched basis rather than
at a confirmed one.** Recording the inference is what stops the parity result from being
over-read.

Options: 5pct-cap-3bb-inferred | look-up-the-reference-solution-basis-first |
run-parity-at-two-bases-and-report-both
Answer: [5pct-cap-3bb-inferred]

## 7. How the eleven aggregates are computed from the export

Reversibility: frozen-into-data

This is where an extraction is most easily self-consistent and wrong, because every
definition below yields a plausible number and only one is comparable to the reference.

Reading the expectations file for its own semantics: it reports SB opening at 34.41 and SB
limping separately at 13.73, so an open is a raise and excludes the limp, and the source
solve allowed limping at the small blind. It reports big-blind defence against each of five
openers as a single number, which in a solved tree is the complement of folding.

Default:

- **Opening frequency** is the combo-weighted frequency of every `raise` and `jam` action at
  the node where a position acts first with no prior raise and no prior limp, excluding any
  limp action.
- **Big-blind defence** is one minus the big blind's fold frequency at the node reached by
  that position opening to 2.5 with everyone between folding, so call, raise and jam all
  count.
- **SB limp frequency** is the combo-weighted frequency of the limp action at the SB node
  with no prior raise. It is zero by construction if decision 1 drops limps, and it is then
  reported from the parity solve instead.
- Every one is weighted by `class_combos` - 6 for a pair, 4 suited, 12 offsuit - **and by
  the arriving range**, using the payload's `reach`, not over a flat 169 classes. A flat
  average is the mistake that makes an extraction look uniformly reasonable and be wrong.

Options: as-defaulted | fold-complement-for-opens-too | flat-169-average
Answer: [as-defaulted]

## 8. The frequency quantisation step in the export

Reversibility: frozen-into-data

Storing `f32` verbatim doubles the export against a 16-bit encoding and keeps precision the
solve does not have, since the achieved gap is measured in thousandths of a big blind. A
quantisation step is a threshold, so it belongs here rather than in whatever the extractor's
first draft happened to do.

Default: **frequencies stored as integers in basis points, 0 to 10,000**, values below one
basis point stored as zero, and each class's row renormalised to sum to 10,000. One basis
point is finer than any decision a chart will make and coarser than the noise the solve
carries.

Options: basis-points-0-10000 | f32-verbatim | per-mille-0-1000
Answer: [basis-points-0-10000]

## 9. The byte limit on `data/artifacts/**`

Reversibility: frozen-into-data

`scripts/check_file_sizes.py` covers `reports/active/*` and the phase audit logs, and
`data/artifacts/**` appears in neither `LINE_LIMITS` nor `BYTE_LIMITS`. Today a 40 MB
artifact commits with nothing objecting. The limit is coupled to decision 1, which is why it
is a ruling rather than a number picked to fit whatever lands.

Default: **a 20 MB total cap across `data/artifacts/**`**, with the measured export size and
the remaining headroom recorded on the source card. Exceeding it halts for a decision rather
than being raised to fit, which is the only way a size limit means anything.

Options: 20MB-total | 50MB-total | per-file-limit-instead
Answer: [20MB-total]

## 10. Whether the export stores per-node arriving ranges

Reversibility: frozen-into-data

`reach` is 169 more values per node. It looked redundant, because `node_view` computes it as
a running product of the strategies along the line, so a reader could recompute it. Two
things break that.

Under any option in decision 1 other than a whole contiguous tree, the line from the root is
not present in the export, so there is nothing to walk and `reach` is not recoverable at
all. And under decision 8 the committed strategies are quantised, so even on a contiguous
tree a recomputed `reach` is a product of rounded numbers rather than the value the solver
had.

Reclassified from `runtime-reversible` on those grounds: a value that cannot be recovered
from what is committed is exactly what the frozen class is for.

Default: **stored per exported node**, so the export is self-contained and every aggregate
in every later phase is computed against the same arriving range the solver used.

Options: stored-per-node | not-stored | stored-at-terminals-only
Answer: [stored-per-node]

## 11. Which spots the human-readable report shows

Reversibility: runtime-reversible

`reports/active/*.txt` is capped at 300 KB, so the report cannot show grids for the whole
export whatever decision 1 settles. The selection must be stated rather than emergent, or
the human verdict covers whatever happened to fit.

Default: **the five opening spots and the five big-blind-versus-open spots the expectations
file names, plus one four-bet line**, in the 169-class grid layout, with the count of
omitted spots stated. Those ten are the spots the only external reference in this repo
speaks about, so they are where a human's read and an outside number can disagree. The
four-bet line is there because it is the part of the tree no reference covers and no v1 spot
key reaches, which makes it the part most likely to be wrong unnoticed.

Options: expectations-ten-plus-one-four-bet-line | expectations-ten-only |
all-rfi-and-vs-rfi
Answer: [expectations-ten-plus-one-four-bet-line]

## 12. What the source card claims about provenance

Reversibility: frozen-into-data

GTOpen ships no LICENSE file, and no mention of licensing in its `README.md` or
`Cargo.toml`. Ruling 4 is to proceed and record the gap. A `source.kind` resembling
"licensed" or "permitted" would be a claim nobody granted.

Default: **`source.kind` records the tool, the commit, and the extraction method as fact; a
`licence` field states in plain words that no LICENSE file exists upstream and that this is
an unresolved limitation rather than a permission; and a `model` field states that GTOpen's
preflop engine resolves flops by scaled equity share rather than by playing them, naming
the `realization` setting used.** The existing GTO Wizard source card is the shape to follow
for everything else. The model limitation is on the card rather than in a doc because the
probe showed it is the difference between a usable range and a calling station.

Options: as-defaulted | omit-licence-field | defer-to-a-separate-notice-file
Answer: [as-defaulted]
