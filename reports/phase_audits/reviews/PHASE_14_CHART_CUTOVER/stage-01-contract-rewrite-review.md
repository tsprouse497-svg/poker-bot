# Phase 14 stage 1: independent review of the contract rewrite, and the halt it produced

Diff reviewed: `09c23a1..ece0e48` - the phase contract rewritten from scratch for six committed spots,
and decision items 25 to 30 transcribing the seven rulings taken in implementation mode that day.

Two independent read-only reviewers, one mechanical and record-fidelity, one poker. Neither wrote any
of the work it read; neither saw the other's findings; neither edited a file. The coordinator wrote
none of the diff either - both halves were worker lanes - but re-derived every load-bearing figure from
the export before acting on it.

**The outcome is a halt.** Taylor ruled on 2026-09-01 that no chart ships. Decision 31 carries the
ruling and its evidence. This note records what the reviews found, including the parts the halt does
not resolve.

## The finding that ended the phase

The poker review's third finding, verified independently by the coordinator before it was escalated:
**the criterion that took the chart from 51 spots to 6 still fires, at full severity, on three of the
six that survived.** Decision 28 withheld fifteen three-bet-facing spots for pocket-pair inversions.
Measured on the raise action at the committed six, `BB vs BTN` reads 44 = 0.0, 33 = 0.0, 22 = 100.0 -
character for character the shape decision 28 quotes as its own evidence. `BB vs SB` and `BB vs HJ`
carry the same shape at 99.5 and 68.4 point gaps.

The phase did not see it because its three relations are defined over play-not-fold, and once every
pocket pair is played 100 percent on that decision the measure reads nothing while the pathology sits
in the raise. The contract had listed the pair ladder among its vacuous criteria on exactly that
evidence. **The phase stopped withholding when the instrument went blind, not when the defect stopped**,
and the blindness flattered the phase rather than being neutral.

The second load-bearing finding, also verified: decision 24 blames the over-folding on the export's
tree branching after a cold call, and at all five committed big-blind nodes `call` is **terminal**.
There is no cold-call branch below a committed flat, so the named cause cannot reach the spots it is
named about. The committed defence is priced end to end by the `calibrated` fit at a single-raised-pot
terminal - the pot type decision 20's architecture declares the fit is right in. It is wrong there by
19 to 30 points, and shaped rather than directional: A7o folded at 50.2 percent equity while 53s is
called at 36.5.

## What the halt does not resolve, and what the next attempt inherits

The mechanical review raised six blockers against the rewrite itself. The halt makes four of them moot -
there is nothing to freeze and no stage to advance - but two are findings about the record rather than
about the artifact and survive:

- **No list of deliberate drops exists in any committed file.** The rewrite dropped six criteria and the
  contract records only the eight it retained as vacuous. The reviewer grepped the contract, the
  ExecPlan, every review note, `CURRENT_TASK.yml` and the decision record and found no list. A phase
  asserting that its drops were ruled, with no artifact for the assertion, is the same failure this
  session opened on one level up. **This note is where that list now lives** - see below.
- **The dropped rule is cited by the ruling that depended on it.** Old contract line 192, "A shape like
  that is a halt and a decision, not a caveat," was removed by the rewrite, and decision 28 cites the
  contract for exactly that sentence as its justification for withholding fifteen spots. The rewrite
  deleted the rule its own transcribed ruling rests on, in the same commit. Decision 31 restates the
  rule in its own body, so the citation is repaired rather than left dangling.

### The six deliberate drops, recorded here because nothing else records them

1. The five-bet call-off paragraph. Subject became a withholding reason rather than committed data.
2. "The refusal rate must not rise there at all." Now simply false - the cutover refuses 29 keys the
   retired chart answered. Replaced by the measured ledger.
3. The human read of hero's four-betting range at committed three-bet spots. No such spot exists.
4. `THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL` as a limitation of committed data. It now
   defines an exclusion reason instead.
5. The group-gate regression detector with its figures, all taken on a discarded build over 36 spots.
6. The "five things arrive ruled" paragraph, which was never a criterion; its load-bearing clauses were
   folded into the criteria they govern.

Plus two the reviewer found that the lane had not listed: the eleven-named-backlog-entries obligation
with its three re-measurements, reduced to a general sweep; and "movement beyond the marginal cells is a
human read of the range grids".

### Two more the halt does not touch

- **The premise justifying every withholding is unmeasured.** "The fit behind `calibrated` has cells for
  single-raised and three-bet pots and none for a four-bet pot" is stated as fact, and nothing in
  `tests/`, `src/` or `scripts/` inspects GTOpen's realization fit. Every withholding rests on it. The
  poker review's finding two is what happens when an unmeasured premise turns out to be wrong in the
  half nobody questioned.
- **The contract says three relations; `tests/test_derived_chart_report.py` asserts two.** A direct
  contract-versus-test contradiction, in the rewrite whose purpose was to end exactly those.

## The check this phase owed and never had

Both gated arms catch a permuted or transposed hand index - extraction defects. Nothing in the phase
measures whether a range is right, and the contract says so itself. The poker review specifies the
cheap fix and the coordinator agrees it is the single highest-value thing a successor can add: commit a
169-by-169 preflop all-in equity matrix, roughly 85 KB, and gate one relation that needs no model
constant - at a spot where hero closes the action, no class folded above 99 percent may hold strictly
more equity than any class played above 99 percent. Pure internal consistency, no realization model can
excuse violating it, and it currently fires on 27 to 55 classes at every committed big-blind spot. It
would have caught this phase's defect on the day the first chart was derived. Filed as
`GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE`.

## The column-width judgement, and a coordinator correction

The lane reflowed the contract to 110 columns to fit the 300-line cap, and flagged it as a judgement
call. The coordinator checked it against the other contracts, found two at 155 and 151 columns, and
cleared it. **That check was wrong and the lane's instinct was right.** Those two files are 59 and 60
line skeletons with a few long lines; every contract that has actually been worked sits at 93 to 104
columns, and this one at 110 is the widest, and the only one where the width is what keeps it under the
cap. The reviewer's verdict - that widening the line by ten percent buys ten percent more assertion at
the same line count, which is materially the same act as raising a cap AGENTS.md says never to raise -
is correct. Filed as `CONTRACT-LINE-CAP-COUNTS-LINES-AND-MEANS-CONTENT`.

## What stands

The re-solve and its evidence: `add_allin: false`, 33,969 action nodes, target 0.00016 achieved at
0.00015590818 first at iteration 1,900 of 2,000, two-process determinism proof byte-identical at 0
divergence and 0 shape differences, written onto the card by the script. The predicate and its census.
The derivation. The two-armed range gate, both arms verified to discriminate. The frozen tests. Phase 16
inherits all of it.

The mechanical review also verified, independently and to the unit, every numeric claim the rewritten
contract makes about the export - the census, the ledger, the arrival sums, both coverage percentages,
the menus, the prices, the reach, the cells. None disagreed. The contract was accurate about the
artifact; the artifact was not fit to ship.
