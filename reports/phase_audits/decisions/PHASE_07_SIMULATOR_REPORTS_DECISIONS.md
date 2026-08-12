# Phase 07 judgment calls

These are the choices about what a simulation *is* that no chart in this repo can
settle. They are recorded before implementation so that what the comparison measures
is a decision somebody made rather than whatever the first draft happened to do.

Every item carries a default.
Defaults stand unless changed, so answering nothing is a valid answer.
Answer by replacing the bracketed value on the `Answer:` line.

Every item carries a reversibility class, which is what the loop driver reads at
stage 2 to decide whether it must stop for a human.

- `runtime-reversible`: the choice only changes behavior at run time, so a later edit
  changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact or fixture that
  later phases are then measured against. The loop halts until a human answers.

Status: every item below is `runtime-reversible`. This phase writes reports, not
fixtures, and `verification/loop_policy.yml` marks Phase 07 `auto_advance: true` for
that reason.

**But the list is going to Taylor anyway, before stage 4.** Phase 06 is the argument.
Two of its calls were reversible, the loop proceeded on their defaults, the gate went
green, and by the time the stage 8 domain review reached them the wrong rule had three
frozen tests pinning it and a mutation canary defending it. Reversible means cheap to
reverse, not unlikely to need reversing. Items 1 and 2 below decide what every number
this phase prints actually means, which is exactly the kind of thing worth thirty
seconds of a human's attention now instead of a re-ruling later.

## 1. Whether stacks reset between hands

Reversibility: runtime-reversible

This is not really about bankrolls. It is about whether the bot can play at all.

`PreflopChartStrategy._table_depth_bb` derives hero's starting depth exactly and
refuses two ways: `stack-depth-not-a-whole-big-blind`, and
`table-is-not-one-flat-stack-depth` when any seat holds more than hero started with.
The only committed artifact is six-handed at exactly 100 big blinds.

So if stacks carry over, hand 1 plays and hand 2 onward mostly does not. Whoever won
hand 1 now holds more than 100bb, so for every other hero at the table
`any(stack > hero_start)` is true and the chart refuses. A session model does not
produce a worse measurement here; it produces almost no measurement.

Default: reset every seat to exactly 100bb at the start of every hand, and measure
chips won or lost per hand rather than a running stack.
That is the standard shape for comparing strategies against a solver baseline - each
hand is an independent sample of the same spot - and here it is also the only shape
the committed chart can answer.

What it costs, stated plainly: this simulation models no session, no stack dynamics,
no short-stack play, and no bankroll. It cannot ever show the bot busting or doubling
through. `ASYMMETRIC-EFFECTIVE-STACKS` in `backlog.yml` is the related gap.

If wrong: nothing breaks, but a reader who assumes a session would misread every
number. The report has to say "chips per hand, stacks reset" wherever it prints a
figure.

Options: reset-every-hand | carry-stacks-and-accept-refusals | rebuy-to-100bb-when-short
Answer: [reset-every-hand]

## 2. What the comparison actually compares

Reversibility: runtime-reversible

The honest problem with this phase, and the item most worth reading.

Two copies of the same strategy at the same table have zero expectation against each
other by symmetry. So a self-play run measures nothing about strategy quality; it
measures variance and it proves the machinery works.

To get a directional number, the profiles have to differ, and the only other strategy
in the repo is the Phase 03 reference `CheckFoldStrategy`, which folds to any bet and
checks whenever it can. Against opponents who fold every hand preflop, the composite
collects blinds. So the number that falls out is closer to "how often does the chart
open" than to "how good are the chart's ranges", and calling it a strategy evaluation
would be dressing up a smoke test.

Default: run both, and label each for what it is.
Self-play carries the mechanical criteria, because symmetry gives a known expected
answer to check against: zero net chips, chips conserved every hand, every hand
terminal, and the replayer agreeing about every decision point. The floor comparison
against check-fold carries one directional number, reported as a floor check - the
chart-driven bot must beat a bot that folds everything, and if it does not, something
is broken.

What it does not do, and the report must say so: it does not rank the bot against any
real opponent, and it does not measure the quality of the ranges. That needs an
opponent with a strategy, which the repo does not have until either Phase 08 supplies
player tendencies or a postflop strategy exists to play against.

If wrong: the risk is not a wrong number, it is a number read as more than it is. The
mitigation is in the contract already - a chip difference smaller than the run's own
variation is not printed as a finding.

Options: both-self-play-and-floor | floor-only | self-play-only
Answer: [both-self-play-and-floor]

## 3. How many hands, and how a difference is separated from noise

Reversibility: runtime-reversible

Three different criteria want three different hand counts. Chip conservation and
determinism need very few. The coverage criterion - every seat having occupied every
position - needs at least six button rotations. A directional chip figure needs enough
hands that its standard error is smaller than the difference it reports.

The binding constraint is the gate. Phase 06 took the gate from 5 seconds to 65
because `check_gate_bite` re-runs a phase's tests once per mutation, and a simulation
multiplies the same way.

Default: a fixed hand count, chosen as the smallest that satisfies the coverage
criterion with margin, with the standard error of the chips-per-hand figure printed
beside it. If the observed difference does not clear that error, the report says the
run cannot separate them rather than naming a winner.
The count goes in the report as a stated number, and the contract forbids tuning it
until a comparison comes out a particular way.

If wrong: too few hands and the floor check cannot resolve even a large edge, which
the printed error makes visible rather than hiding. Too many and the gate becomes
something nobody waits for, which is how gates get skipped.

Options: fixed-count-with-stated-error | run-until-separated | large-fixed-count
Answer: [fixed-count-with-stated-error]

## 4. How a refusal settles the chips

Reversibility: runtime-reversible

A preflop chart refusal is a real outcome, and the contract forbids converting it into
an action. But the blinds are already in the middle when it happens, so something has
to be done with them, and chip conservation has to survive whatever that is.

Default: void the hand. Restore every seat to its starting stack, count the hand as
refused with its reason code, and exclude it from the chips-per-hand figure while
including it in the refusal coverage figure.
Chip conservation then holds trivially for a voided hand, and the alternative -
treating the refusing seat as folding - would quietly convert a refusal into an action
in the accounting even while the strategy layer refused, which is the same erasure the
contract forbids one level up.

Note this is an accounting decision for a measurement instrument, not a poker rule.
No real game gives blinds back.

If wrong: a voided hand that should have counted makes the denominator smaller and the
refusal figure larger, both of which are printed, so the effect is visible rather than
silent.

Options: void-the-hand | treat-as-fold | abort-the-run
Answer: [void-the-hand]

## 5. Table size and depth

Reversibility: runtime-reversible

Recorded because it looks like a choice and is not.

The only committed chart artifact is six-handed at exactly 100 big blinds. Any other
table size or depth makes the composite refuse every preflop decision, so a run at any
other configuration measures the refusal path and nothing else.

Default: six seats, exactly 100bb, cash-game blinds, no antes and no straddle. A run
configured otherwise is rejected at setup with a named reason rather than producing a
report full of refusals.

If wrong: nothing, until a second artifact is committed at another depth, at which
point this becomes a real choice.

Options: six-max-100bb-only | allow-any-configuration
Answer: [six-max-100bb-only]

## 6. Whether the button rotates, and whether hero is a fixed seat

Reversibility: runtime-reversible

Default: the button advances one seat per hand, and profiles stay in their seats.
So over any multiple of six hands every profile has played every position an equal
number of times, which is what makes a chips-per-hand figure comparable between two
profiles instead of an artifact of who sat where.

The alternative - fixing the button and rotating the profiles - measures the same thing
and makes the per-hand records harder to read, because a seat number would stop meaning
one profile.

If wrong: an uneven number of hands leaves the last partial orbit unbalanced. The
report prints the per-position counts, so the imbalance is visible; the default hand
count is a multiple of six so it does not arise.

Options: rotate-the-button | fix-the-button-and-rotate-profiles
Answer: [rotate-the-button]

## 7. Whether dealt hands are written to disk

Reversibility: runtime-reversible

The contract requires every dealt hand to be expressible in the Phase 02 schema and to
reproduce its own decision points through the Phase 02 replayer. It does not require
those hands to be committed.

Default: the cross-check runs in memory, and nothing is written under `data/`.
A run is a pure function of its seed and the seed is in the report, so any hand can be
regenerated rather than stored. Writing hands under `data/artifacts/` or `data/samples/`
would also make this phase ineligible to advance unattended under
`verification/loop_policy.yml`, and it would create a fixture that later phases get
measured against - which is exactly the `frozen-into-data` situation this phase does
not otherwise have.

If wrong: a reviewer who wants to read a dealt hand has to run the generator to get it.
That is one command, and it is the same command the gate runs.

Options: in-memory-only | write-a-sample-under-reports | commit-a-fixture-under-data
Answer: [in-memory-only]
