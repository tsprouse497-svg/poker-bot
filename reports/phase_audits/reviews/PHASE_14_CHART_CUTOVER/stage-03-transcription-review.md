# Phase 14 stage 3: independent review of the transcription commit

Diff reviewed: `9a8c8c9..11133f3` on `phase/14-chart-cutover` - the pointer edit in `dee8b5e` and the
transcription commit `11133f3`, "Withdraw decision 22 and transcribe the five rulings the list never
carried".

Two independent read-only reviewers, one mechanical and record-fidelity, one poker. Neither wrote any
of the work it read, neither saw the other's findings, and neither ran the verification gate. The
coordinator wrote the commit under review and therefore reviewed none of it; what the coordinator did
do is re-verify each blocker against the export and the source notes before acting, and those
re-derivations are recorded below beside the finding they confirm.

This note exists because the stage owed one and did not have one. `stage-03-human-gate.md` is dated
2026-08-24, is a coordinator self-review of an earlier pass, and says in its own opening that it should
be re-run by an independent reviewer. It covers none of this diff. The driver's shape check was
satisfied by its mere existence, which is exactly the quiet pass `dee8b5e` moved the stage base to
prevent, one level up.

## Blockers, and how each was resolved

**B1 - the decision 5 quotation was doctored, and the clause removed was an obligation this task owed.**
`PHASE_14_CHART_CUTOVER_DECISIONS.md` presented a continuous quotation from
`stage-04-untrained-cell-refusal.md` with two unmarked elisions. The second deleted "The contract's
artifact criterion asks for reach and does not mention arrival; it owes the same sentence." The tell
survived: "the only place *either* is written down" had lost the second of its two antecedents. The
decision-6 transcription 190 lines later does mark its elision with an ellipsis, so this was not the
author's convention.
Coordinator verification: `sed -n '344,350p'` of the note against the decision list, both quoted in
full. Confirmed.
**Resolved.** The quotation is restored in full, the elision is recorded as a correction rather than
silently repaired, and the contract obligation it concealed is discharged - see B2.

**B2 - two contract amendments the notes assigned to "the next `contract-update`" were skipped, in a
`contract-update` task with the contract in `approved_scope` and sixteen lines of headroom.**
`stage-04-test-recut.md` assigns one: "decision 10 and the contract's dominance criterion both owe an
amendment at the next `contract-update`". `stage-04-untrained-cell-refusal.md` assigns the other, the
arrival sentence above. Neither was made, and the contract at line 152 still stated as its gate the
group-order ladder that decision 10 ruled out on 2026-08-26 and that never shipped.
Coordinator verification: contract lines 143-160 and 107 read directly; `grep -in "arrival"` returned
nothing; `wc -l` gave 284 against the 300 cap in `check_file_sizes.py`, so the size excuse did not
apply either.
This is not bookkeeping. Stage 4 authors tests from the contract and stage 5 freezes them, so a
contract asserting a gate that did not ship is the same failure the whole commit exists to correct,
one document over.
**Resolved.** Both amendments made, each two lines with its ruling date and its backlog id, per the
Contract Amendments rule. Contract now 286 lines.

**B3 - the group-discrimination retake was placed where it cannot happen.** Three committed documents
named three different points: the contract "before it is frozen" (stage 5), decision 10's transcription
stage 4, decision 5's stage 6. Only stage 6 is reachable, and it lands after the freeze, which decision
10's own standing rule forbids.
Coordinator verification: `data/artifacts/preflop/six_max_100bb_rakefree.json` holds **86** spots; the
36-spot artifact decision 20 describes has never been derived. Stage 4 is the red-tests stage per
`docs/LOOP.md`, so nothing before stage 6 has 36 spots to measure.
**Resolved by ruling.** Put to Taylor 2026-09-01 as the sequencing question decision 22 raised and
nobody answered. Ruled **build early, then measure** - the derivation runs out of the loop's stage
order, deliberately and recorded, so the discrimination is measured on the real 36 before any test is
authored against it. Recorded as decision 23, which also reconciles the three documents onto that
answer.

**B4 - "a polarised defence is the right shape there" is false, and the shape-versus-fill reconciliation
is circular.** The poker reviewer re-derived every figure in the decision 1 amendment from the committed
export and reproduced all of them exactly, then read the rows cell by cell rather than by group.
Coordinator verification, independently, loading the export with the `add_allin` config assertion
relaxed since the file predates decision 14:

| hand | continues | arriving reach |
|---|---|---|
| KQs | 28.38% | 9,962 |
| 76s | 99.79% | 9,981 |
| QJs | 93.29% | 9,982 |
| TT  | 0.08%  | 9,576 |
| AQs | 49.42%, all jam | 7,424 |

KQs and 76s hold the same equity against the four-betting range, at the same price and the same reach,
and are played 71 points apart; polarisation sorts by equity and these are equal on it, so the
separating variable is the realization model's per-class multiplier and the "shape" IS the fill. KQs
dominates QJs and is played 28 against 93. The justifying sentence - "equity losing to playability is a
standard solver result" - is backwards at SPR 1.667, where the flop is nearly all-in and raw equity
dominates, as decision 20 itself says.
**Resolved.** The gloss is withdrawn in place at decision 1 with the measurements above. Taylor's
2026-08-27 ruling is untouched and stands as what he ruled; what is withdrawn is a later session's
certification of those rows as evidence. Filed
`FOUR-BET-ROWS-WERE-CERTIFIED-BY-GROUP-AND-FAIL-CELL-BY-CELL`. Nothing about the committed 36 moves -
the node is four-bet-facing and decision 20 already refuses it.

**B5 - the convergence rebuttal argues the opposite of its own data.** It cites purity by depth of 88.2,
85.3, 69.3, 67.1, 83.7 and concludes deep nodes "mix more rather than showing degradation" - but rows
sitting nearer uniform at depth is the undertraining signature the hypothesis predicted, and the
sentence concedes it while denying it. Measured over the whole tree at the same reach filter rather than
over the 86, the profile is monotone with no rebound: 87.7 / 87.3 / 81.3 / 68.2 / 53.9 percent pure. The
depth-4 rebound is a menu artifact - two-action nodes are measured against a 1/2 initialisation. The
figure that does bear on it is arrival 0.13 percent against a global gap of 0.0062bb: 4.81bb of
permitted error at a node where hero decides about 15bb.
**Resolved.** Recorded at decision 1 with the rebuttal withdrawn. The hypothesis was correct and
decision 14 conceded it in different words by tightening the target roughly fortyfold.

**B6 - the committed spots never flat a raise.** The first finding in this list about the spots the
phase ships rather than the ones it refuses.
Coordinator verification, re-derived from the export: cutoff facing a lojack open continues **7.35
percent** and flats **0.69**; button facing a cutoff open 8.63 with a 1.65 flat; small blind 10.04 with
4.54. Six-max 100bb rake-free wants roughly 14 to 16 percent with a real flatting range. Cause is known
from `stage-04-cold-call-verification.md` - the tree branches on every cold call, so flatting is priced
against a continuation structure that punishes it. Decision 1's `heads-up-only` kept those families out
of lookup; it did not stop the heads-up spots the phase keeps from pricing their own flat against the
same tree.
**Resolved by ruling.** Put to Taylor 2026-09-01. Ruled **accept and record**, with phase 16 as the
exit, on decision 20's precedent. Recorded as decision 24 and filed
`COMMITTED-SPOTS-NEVER-FLAT-A-RAISE`. The packet now owes the flat frequency at every committed spot
beside the level a human reads.

## Non-blockers corrected in place

- The decision 1 transcription claimed its source note "with a pointer to the next `contract-update`".
  It carries none - four of the five stranded rulings left such a pointer and this one left nothing,
  which makes it the worst case of the family rather than an example of the convention working. The
  header's generalisation was corrected with it.
- "the list carries no occurrence of that date at all", written in the present tense inside the
  amendment that adds six occurrences of it. Now reads "before this amendment".
- Decision 6's "the per-class price weight has one entry everywhere" contradicted the same item's own
  "fifteen offer no raise at all and correctly carry none" and the contract's 21/15. Now "at every spot
  that carries one", with the counts.
- Decision 10's transcription dropped the one detail its note labels load-bearing: the transposed
  reading must take a cell's weights **and its reach** from the swapped class, since taking weights
  alone measures sparsity and prefers the transposed mapping, 41 to 30. Restored.
- Decision 6's transcription elided its measurement. The per-class spread (AA 0.0000 to 44 0.8844
  against a 0.0761 aggregate), the four smallest second-price shares at 1.03e-05 to 2.89e-05 and why no
  epsilon rule survives, and the `schema_version: 2` shape stage 6 implements are all restored.
- Decision 6's poker gloss approved of play the phase re-sourced away - JJ jamming 100bb over a 2.5x
  button open 63.13 percent while AA and KK three-bet to 7.5. Corrected; moot over the committed 36.
- Every figure in the decision 1 amendment is taken on the superseded `a386c77` build and was labelled
  by model maturity rather than by build. Now labelled, under decision 10's rule that no ruling may
  rest on an unlabelled proxy.
- "None of item 22's four options names it" was slightly overstated: option three gets the ladders
  right and the consequence wrong. Refined; the withdrawal stands.
- Five amendment headers read "Transcribed 2026-08-31" and were written on 2026-09-01. Left as written
  rather than restamped - an append-only record is not edited to look tidier - with a dating note in the
  header so nobody reads them as evidence of when anything was known. The ruling dates themselves are
  correct.
- The recount said 22 items; the list now runs to 24.

## Findings that needed no action

- The mechanical reviewer's sixth outstanding pointer, "the contract says both 22 and 21 about the
  retired chart's survivors", is stale: the 2026-08-31 re-cut already replaced that passage with the
  31/5 collision framing. Verified by grep - no survivor count of 22 or 21 remains in the contract.
- Two further 2026-08-27 items in `stage-04-predicate-change-review.md` - the aggregate-of-the-run
  ruling and its same-day reversal onto "commit the cell as solved" - are untranscribed, but they
  re-affirm decision 2's existing `ship-as-solved` and are tracked as `COMMIT-THE-BAND-NOT-THE-TIE-BREAK`.
  Nothing is lost; named here so the completeness claim is honest.
- Literals: the mechanical reviewer checked every figure the diff introduces against the notes, the
  contract and the code and found no disagreement. The census sums to 33,969, matching the contract and
  the re-sourced node count.
- `validate_group_discrimination` refuses on a tie, so a chart that folds nothing is rejected and so is
  one that folds everything. That is a real improvement over the ladder it replaced and both reviewers
  said so.
- Stage hygiene: `verification/loop_runs/14.yml` well formed, `stage_base` resolves, scope sufficient
  and not over-wide, everything in the commit belongs to `contract-update`.

## Alignment items filed

- `FOUR-BET-ROWS-WERE-CERTIFIED-BY-GROUP-AND-FAIL-CELL-BY-CELL` - a group aggregate hid a 71-point
  inversion, a dominance violation and six untrained classes inside two headline numbers.
- `COMMITTED-THREE-BET-SPOTS-INHERIT-AN-EXCLUDED-NODES-RANGE` - contamination is measured on the
  terminals below a committed spot and never on the range arriving at it.
- `THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR` - the shipped gate is a good
  extraction check and the record claims it checks the ranges.
- `DECISION-ANSWER-FIELDS-DIVERGE-FROM-THE-RULINGS-BELOW-THEM` - two conventions at once in a field the
  driver parses.
- `COMMITTED-SPOTS-NEVER-FLAT-A-RAISE` - filed as the accepted residual decision 24 names.

## Status

All six blockers resolved: four by correction, two by Taylor's rulings of 2026-09-01, recorded as
decisions 23 and 24. Stage 3 may advance, and decision 23 makes the next action an out-of-order
derivation rather than stage 4 test authoring.

## Addendum, 2026-09-01: the out-of-order build decision 23 ruled

Run from this worktree at stage 3, before any stage-4 test authoring, exactly as decision 23 rules.
GTOpen was started locally at `127.0.0.1:3737` from the read-only clone at `~/projects/gtopen`; the
solve is offline and one-time and the gate never runs it.

**The re-solve.** `scripts/extract_gtopen_preflop.py --save-name six-max-100bb-rakefree`. Every figure
the contract's "What the re-solve owes" section states is met, and none was assumed:

| what the contract says | measured |
|---|---|
| `add_allin` is `False` | `false` in `config_posted` |
| target `0.00016` at a 2,000-iteration cap | `target_gap_bb` 0.00016, `iteration_cap` 2000 |
| first meets it at iteration 1,900, so the cap nearly binds | `iterations` 1900, achieved 0.000155908 |
| determinism walk reports 0 mismatches | walked 33,969 action nodes, 0 mismatches |
| node count equals the census sum 33,969 | `action_nodes` 33,969 |
| `data/artifacts` inside the 20 MiB cap | 2,555,076 bytes, headroom 17,793,920 |

The solve took 294.7 seconds. The re-source is what the gate has been red on since decision 14 - the
committed export carried `add_allin: true` against a `RULED_CONFIG` of `False` - and that mismatch is
now the only thing standing between this phase and a green gate that is about the phase rather than
about an inherited config.

**The census reproduces the contract exactly**, on the re-sourced tree rather than the retired one:
51 committed by the predicate, 29,104 `source-misprices-multiway`, 4,814 `outside-selection-rule`,
summing to 33,969.

**The withholding, stated so the next reader does not repeat the coordinator's first error.** Decision
20 withholds the spots where hero **faces a four-bet**, which is *three* raises in the action sequence.
Four raises is hero facing a five-bet jam, and those stay committed - the contract says so in terms
("fifteen committed spots face a five-bet jam, and at them the chart puts the last 77.5bb in"). The
raise-count histogram over the 51 is 0→1, 1→5, 2→15, 3→15, 4→15, so the committed 36 are
1 + 5 + 15 + 15 and the withheld 15 are exactly the `raises == 3` bucket. A first pass filtered on
`raises >= 3`, which wrongly drops the five-bet spots and gives 21 committed; it was caught because 21
is not 36. Anything measuring this set should assert the count.

**The measurement decision 23 ordered.** `spots_violating_twins` under the solver's own class ordering
against the same measure under `transpose_hand_index`, over the real committed 36, on every partition:

| partition | solved | transposed | verdict |
|---|---|---|---|
| committed 36, all | 0 | 26 | pass |
| hero=BB (5) | 0 | 5 | pass |
| hero=BTN (4) | 0 | 2 | pass |
| hero=CO (6) | 0 | 6 | pass |
| hero=HJ (8) | 0 | 6 | pass |
| hero=LJ (10) | 0 | 5 | pass |
| hero=SB (3) | 0 | 2 | pass |
| raises faced 0 (1) | 0 | 1 | pass |
| raises faced 1 (5) | 0 | 5 | pass |
| raises faced 2 (15) | 0 | 15 | pass |
| raises faced 4 (15) | 0 | 5 | pass |

**Every partition passes and no partition ties**, so decision 10's premise holds on the artifact the
phase actually commits rather than on the 86 it was ruled over. No halt, and no decision is owed to
Taylor here. Round 14 of the stage-01 note warned that transposing made the *suited-row ladder* cleaner
over the committed keys; that warning was about a different relation and does not carry to the twins
measure, which is what the coordinator was checking for and did not find.

Worth stating plainly because it is the one number that could be read as too good: the solved count is
**0** on every partition, meaning no committed spot holds a suited-under-offsuit cell beyond the
one-point tolerance. That is the measure passing, not the measure being blind - the transposed arm
flags 26, so it can tell the two mappings apart. What it still cannot see is everything
`THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR` names.

**Nothing was committed from this build, and that is deliberate.** The four files it wrote - the export,
its source card, the chart and the sizing table - were reverted after the measurement. Two reasons.
The chart it produced holds **51** spots, not 36, because decision 20's third exclusion reason
(`source-misprices-four-bet-pot`) is not implemented; committing it would commit an artifact the
contract does not describe. And `data/artifacts/**` is outside this task's `approved_scope`, correctly,
because writing new committed data is stage 6's job in `implementation` mode and not a
`contract-update` task's. Decision 23 bought a measurement taken early, not a shipping build taken
early, and the distinction is what keeps the loop's ordering meaningful.

**What stage 6 inherits from this.** The build machinery is proven end to end on the ruled config, the
re-solve reproduces deterministically, the census is confirmed against the contract, and the gate's
premise is confirmed on the real 36. What stage 6 still owes is the third exclusion reason and its
census line, after which the same measurement is retaken on the committed artifact rather than on a
filtered derivation of it.
