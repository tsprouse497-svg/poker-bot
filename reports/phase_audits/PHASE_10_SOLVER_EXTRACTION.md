# Phase 10 Audit Packet: Solver Extraction, And A Human Verdict On It

Written for a reviewer who does not read code.

## Summary in plain language

This phase captured one solved preflop tree out of GTOpen and committed it as data anybody
can check offline. It changed nothing about how the bot plays. The bot still reads the same
36-spot chart it read before, and it still refuses the same 22 spots that chart cannot
answer. Deriving a replacement is a later phase.

**What was captured.** Six-handed, 100 big blinds, opens to 2.5bb, no limping, no rake, with
GTOpen's calibrated equity-realization model. Every action node in the solved tree - all
38,828 of them - with no filtering rule anywhere in the extractor, because filtering to what
today's vocabulary can express is the one decision that would have forced doing this again.

**What was proved about it.** The same configuration was solved and walked twice, in separate
processes against a restarted server, and the two results are byte-identical. Every one of
the 38,828 nodes was asked for a second time by its own recorded action sequence and came
back the same node, all 38,828 times. Converted frequencies reproduce the numbers GTOpen
reports for itself to within four ten-thousandths.

**What is checked on every gate run, and what is not.** Two checks gate: later position opens
wider among the four non-blind positions, and the big blind defends more against whoever
opens wider. Both compare the export against itself, so they hold at any rake basis, for any
solver. Nothing grades this solve against GTO Wizard. That was the plan until Taylor ran the
solver himself on 2026-08-18 and re-ruled it: GTO Wizard is a different program solving a
different game, and a threshold over the gap between them measures two products rather than
this extraction. Its eleven numbers are still printed beside ours for a reader to compare by
eye, labelled as gated by nothing.

**What no check can do.** The two gated checks catch a broken pipeline and nothing else - a
solve with every frequency halved passes both, and a test says so on purpose. So the closing
act is a person: load the saved solve in GTOpen's own interface and read its range grids
against the committed report. Taylor did that on 2026-08-19 and judged the extraction sound,
which is what closes this phase. Three nodes had already been read the same way cell by cell
by the coordinator, and matched.

## Pass/fail checklist

| # | Claim | Result |
|---|---|---|
| 1 | The whole solved tree is committed, with no filtering | PASS - 38,828 exported against 38,828 the solver reports, equal, nothing to reconcile |
| 2 | A four-bet node is present, and no node anywhere offers a limp | PASS - both asserted by committed tests |
| 3 | Two identical runs agree | PASS - byte-identical, zero divergence, zero shape differences |
| 4 | A real solve was timed against a target declared before it ran | PASS - 0.00624 bb summed gap at iteration 300 in 60.2 seconds, target 0.01 bb, cap 2,000 |
| 5 | Every node re-resolves from its own recorded action sequence | PASS - 38,828 re-resolved, 0 mismatches |
| 6 | Whether the payload is conditioned on reaching a node is settled by a stated test | PASS - unconditional; 72o at the LJ-vs-3bet node arrives with reach 3.7e-08 and still carries a full uniform strategy row |
| 7 | Every number the gate checks is recomputed from the export on each run | PASS |
| 8 | Opening order holds exactly among LJ, HJ, CO, BTN | PASS - 19.08, 21.64, 27.34, 40.26 |
| 9 | Big-blind defence tracks the opening order | PASS - 27.28, 29.92, 34.12, 36.76, and 49.02 against the widest opener |
| 10 | Nothing gates on the GTO Wizard reference file | PASS - all eleven rows labelled reported; a test fails if a tolerance constant reappears |
| 11 | Every check is exercised against a deliberately broken export | PASS - ten broken exports, plus three wrong configs |
| 12 | The export sits under a byte limit with stated headroom | PASS - 4,094,221 bytes, 15.6 MB of headroom under the ruled 20 MB |
| 13 | The source card records the config, commit, gap, wall clock, determinism and a checksum | PASS - and a committed test fails on a missing or placeholder field |
| 14 | The licence gap is stated as a limitation, not a permission | PASS |
| 15 | The report names which spots it shows and which it omits | PASS - 11 shown, omitted: 38,817 |
| 16 | The gate proves it can fail on this phase's own command | PASS - two canaries, 35 of 35 mutations caught |
| 17 | A human loaded the saved solve and compared named grids | PASS - Taylor read the save and the preflop grids; the coordinator had matched three nodes cell by cell |
| 18 | A human verdict on whether the extraction is faithful poker | PASS - Taylor, 2026-08-19, see below |

## Commands and reports

| Command | What it does |
|---|---|
| `pytest_solver_export` | The export reader, the source card, the expectations checks and the report, 74 tests |
| `check_solver_export_expectations` | Recomputes the eleven aggregates from the committed export and runs both orderings |
| `generate_solver_export_report` | Writes the range grids a person reads |

- `reports/active/latest_verify.txt` - 38 commands, all pass
- `reports/active/latest_solver_export_report.txt` - the grids, 39,808 bytes
- `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz` - the export
- `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json` - the source card

## The four answers the phase was asked for

These four were on the unverified list in `docs/GTOPEN_SOLVER_NOTES.md`, and answering them
was the phase's first deliverable rather than an aside.

1. **How long does a real solve take?** 60.2 seconds of wall clock, stopping at iteration 300
   when the summed best-response gap crossed 0.01 bb, against a 2,000-iteration cap that never
   came near binding. The walk is the expensive half at roughly six minutes, because
   `/api/preflop/node` re-walks from the root on every call and the export needs one call per
   node per action plus a re-resolution pass.
2. **Do two identical runs agree?** Byte-identical. Solved and walked twice in separate
   processes against a restarted server; the exports were diffed node by node over strategies
   and reach, not merely checksummed. Zero divergence in basis points, zero nodes present in
   one and not the other.
3. **How does `/api/preflop/node` encode a path?** A list of action indices from the root, and
   nothing else. That is read from the solver source and, more usefully, checked: every node
   was asked for again by its own path and 38,828 of 38,828 came back with the same actor and
   the same action list.
4. **Is a node's strategy conditioned on reaching it?** No. At the node where the lowjack
   faces a three-bet, 72o - which the lowjack folds at full frequency - arrives with a reach of
   0.000000037 and still carries a complete strategy row, uniform at a quarter per action. So
   the payload is unconditional, `reach` is the only thing that conditions it, and every
   aggregate is weighted by it.

## One number a reader can recompute by hand

The report prints the lowjack opening 19.08 percent of hands. Here is where that comes from,
without code.

The export's root node holds three actions - fold, raise to 2.5, all-in - and for each of the
169 hand classes it stores how often the lowjack takes each, in hundredths of a percent
summing to 10,000. The opening frequency is every raise and every jam, weighted by how many
card combinations each class is (6 for a pair, 4 for a suited hand, 12 for an offsuit hand,
1,326 in total) and by how often that class arrives at the node - which at the root is always,
so at this one node the weighting simplifies to combinations alone.

Take a shortcut a reader can check on the printed grid. In the "Raise 2.5" grid for RFI LJ,
every pair on the diagonal reads 100 except 44 at 73. Pairs are 6 combinations each, so the
pairs alone contribute `12 x 6 + 0.73 x 6 = 76.4` combinations of the 1,326, which is 5.76
percent. Every remaining opened hand in the grid is suited or offsuit, and adding them the
same way - cell percentage times 4 for a suited cell, times 12 for an offsuit cell - reaches
253 combinations, and `253 / 1326 = 19.08 percent`. GTOpen's own interface reports 19 percent
for the same node in the same save.

## Review findings

Read-only reviews were written at stages 1, 2, 3, 4, 5, 6, 7 and 8 in
`reports/phase_audits/reviews/PHASE_10_SOLVER_EXTRACTION/`. Subagent delegation is switched
off in this operator's sessions, so `AGENTS.md` step 6 could not be satisfied and step 10's
self-review fallback applies; every note records that at its head, and independent reviewers
were offered rather than dropped silently.

Blockers found and fixed:

- **Stage 5.** The contract's Scope section still specified the parity solve its own
  acceptance criteria forbid, and the decision record still told the report to read the small
  blind's limp frequency off that withdrawn solve. Both fixed in contract-update mode before
  the tests were frozen.
- **Stage 6.** A frozen test asserted a reach of exactly 0.0 against a captured payload
  holding 3.7e-08. The finding it makes is right; only the bound changed, and the captured
  payload was left alone.
- **Stage 8.** The report's four-bet spot was the wrong node under a label naming the wrong
  seats. Walking "the next 3-bet, then the next 4-bet" passes the action to the cutoff rather
  than back to the lowjack, so it printed the button facing a cutoff four-bet - a line folded
  99.09 percent of the time - as "HJ vs LJ 4-bet". Since decision 6c's method is a person
  navigating to the named spot, a wrong label is worse than no spot at all. It now folds the
  seats between and lands on the hijack facing the lowjack's four-bet, and reproduces the
  numbers the probe recorded before any code existed: fold 34.60, call 53.56, jam 11.83.

The most useful non-blocking finding, in full in the stage-8 note: **the big blind
under-defends and the button opens tight, and both trace to the model rather than to the
extraction.** GTOpen's preflop engine never plays a flop - it splits the pot by equity share
scaled by a per-seat weight. The button's edge and the big blind's disadvantage are both
almost entirely postflop, so a scalar weight is the only part of them the model can express.
The button opens 40.26 percent where a *raked* reference opens 40.56, which is backwards for
a rake-free solve, and the big blind continues with 570 of 1,326 combinations against a
lowjack opening 19 percent while laying 1.5 to win 4.5. Filed as
`REALIZATION-MODEL-UNDERPRICES-POSITION` against Phase 14, which is where it would be paid
for.

## Judgment calls and what each one changed

Thirteen were recorded in
`reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md` before any code, and
Taylor ruled on all of them on 2026-08-18, then re-ruled three of them the same day after
running the solver himself.

| # | Ruling | What it changed |
|---|---|---|
| 1 | Drop limps, commit the whole tree | 38,828 nodes instead of 289,036; no spot where an opponent limped can be answered from this export, filed as `CHART-CANNOT-ANSWER-A-LIMPED-POT` |
| 2 | The config as defaulted, including `realization: calibrated` and `allin_threshold: 0.67` | The realization field is the difference between this export and a big blind that defends 99.71 percent; the threshold is the field GTOpen's web form cannot set, which is why verification loads the save |
| 3 | Target 0.01 bb, cap 2,000 | Reached at iteration 300; one pocket pair left non-monotone, filed |
| 4 | Orderings restated as internal | Both gated checks now need no external file |
| 5 | Directional bound withdrawn | Removed a check that was already failing on a hundredth of a point |
| 6, 6b | Parity solve withdrawn | Removed the most expensive and softest thing in the phase |
| 6c | Verify by loading the saved solve | The extractor saves before walking; the save's path and checksum are on the card |
| 7 | Aggregates combo-weighted and reach-weighted | Reproduces GTOpen's own frequencies to four decimal places |
| 8 | Basis points, 0 to 10,000, renormalised | 105 bytes per node; a plain float dump would not have fit |
| 9 | 20 MB across `data/artifacts` | The export uses 4.09 MB of it |
| 10 | Reach stored per node | Recomputing it from quantised strategies would not recover it |
| 11 | Ten reference spots plus one four-bet line | The report shows 11 and states 38,817 omitted |
| 12 | The card states the licence gap and the model as facts | Both present, both checked by a test |

## The human verdict

**Given by Taylor on 2026-08-19: the save and the preflop grids check out, and the extraction
is faithful.** He loaded
`/Users/taylorsprouse/projects/gtopen/saves/preflop/six-max-100bb-rakefree.gtop`, sha256
`64d8729a30f758f24e713976ac529bab64c741d22af4b68bdeea424864f27ab5`, in GTOpen's own Preflop
Lab and read the opening range grids against
`reports/active/latest_solver_export_report.txt`. He was shown the two things the domain
review flagged before he looked - the big blind continuing with 570 of 1,326 combinations
against a lowjack opening 19 percent while laying 1.5 to win 4.5, and the lowjack raising 44
at 72.8 percent while raising 33 and 22 at about 99.9 percent - and neither disqualified the
solve. Both stay filed rather than closed: `REALIZATION-MODEL-UNDERPRICES-POSITION` and
`SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`, both against Phase 14, which is the phase that
would pay for either.

State the verdict's reach honestly, because it is the phase's closing evidence. It says the
committed export is a faithful copy of what GTOpen solved and that the poker in it is good
enough to keep. It does not say GTOpen agrees with any other solver, and nothing in this
phase measures that. What backs the faithfulness half mechanically: the coordinator's own
cell-by-cell comparison at three nodes, the converted frequencies reproducing GTOpen's own
`freq` to within four ten-thousandths, 38,828 of 38,828 nodes re-resolving from their own
action sequences, and two solves coming back byte-identical.

The operating note that goes with reloading it: after loading, do not press Build or
Re-solve. The web form has no control for `allin_threshold` and re-posting it reverts the
tree from the ruled 0.67 to the server default of 0.85.

## Known limitations and deferred items

- GTOpen's preflop engine resolves flops by scaled equity share rather than by playing them.
  This is a preflop-only model and not a full solve, and it is on the source card.
- GTOpen ships no LICENSE file, and neither its README nor its Cargo.toml mentions licensing.
  Recorded as an unresolved limitation rather than a permission.
- The export's container is this repo's own format, so the committed file is not readable
  without this repo's reader. What buys that back is the report.
- Nothing in this repo can check the committed export against GTOpen without running GTOpen,
  which the gate deliberately cannot do. The source card is the record, and its determinism
  and timing figures can never be recomputed inside the gate.
- Deferred: `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`, `REALIZATION-MODEL-UNDERPRICES-POSITION`,
  `DEFENCE-RELATION-NARROWER-THAN-THE-CONTRACT`, `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK`,
  `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`, `CHART-HERO-MUST-NEVER-LIMP`,
  `CHART-CANNOT-ANSWER-A-LIMPED-POT`.
