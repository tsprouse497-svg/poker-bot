# Phase 08 judgment calls

These are the choices about what gets written into a committed sample, and what a
comparison against real players is allowed to mean. No chart in this repo settles
them. They are recorded before implementation so that what the report measures is a
decision somebody made rather than whatever the first draft happened to do.

Every item carries a reversibility class, which the loop driver reads at stage 2 to
decide whether it must stop for a human.

- `runtime-reversible`: the choice only changes behavior at run time, so a later edit
  changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed sample that every later
  measurement then runs against. The loop halts until a human answers.

**Four of the seven below are `frozen-into-data`, and the loop will stop at stage 3
until Taylor rules on them.** That is the correct outcome rather than an obstacle.
`verification/loop_policy.yml` keeps Phase 08 at `auto_advance: false` for exactly this
reason: the phase commits data, and committed data is where a wrong assumption becomes
permanent because everything downstream is then measured against it.

Items with a `frozen-into-data` class carry `Answer: []`, which is what blocks. The
recommendation for each is stated in its own paragraph, so answering "the
recommendation" is a complete answer.

## 1. Which hands the committed sample holds

Reversibility: frozen-into-data

The corpus is 10,000 hands and the committed sample cannot be all of them:
`check_file_sizes` caps `data/samples` at 5 MB in total, and the phase title says
tiny. So a rule has to choose, and the rule matters more than the number, because a
rule that lets anyone pick which hands survive lets them pick the hands the bot does
well on.

Two rules were measured over the real corpus before this was written. Taking the first
500 hands in sorted path order draws from about five consecutive sessions: 7 distinct
players ever hold the button and only 3 hands contain an all-in. Taking every 20th hand
across the whole sorted list gives the same 500 hands' worth of data spread over all 92
sessions: 13 distinct players hold the button, 7 hands contain an all-in, and it yields
3,056 preflop decision points. The stride costs nothing and buys a sample that is not a
handful of consecutive sessions between the same six people.

Recommendation: every 20th hand by a stable lexicographic sort of the corpus's own file
paths, giving 500 hands and roughly 3,000 preflop decision points. Deterministic,
rerunnable, and nobody chose a hand.

What it costs, stated plainly: 500 hands is a sample. Rates computed on it carry real
sampling error, and 7 all-in hands is thin coverage of the all-in settlement path. The
report prints denominators next to every rate so this is visible rather than implied.

Options: every-20th-by-path-500 | first-500-by-path | a different stride or count
Answer: []

## 2. Whether the corpus's own text is committed alongside the conversion

Reversibility: frozen-into-data

The phase rests on a conversion being checkable. If only the converted output is
committed, then a reader who suspects the converter has nothing to check it against
without going back to the network, and the offline-first rule in `AGENTS.md` stops
meaning much.

The selected hands are about 271 KB of plain text, which is cheap. `data/raw/**` stays
forbidden and is not touched: this is a small public slice and it belongs under
`data/samples/` with a name that says what it is.

Recommendation: commit the corpus's own text for exactly the selected hands, unmodified,
next to the normalized hands they produced, with a checksum over the set.

If wrong: nothing breaks, the repo just carries 271 KB it did not need, and the
conversion becomes an assertion rather than something a reader can verify.

Options: commit-the-selected-source-text | commit-checksums-only | commit-nothing-raw
Answer: []

## 3. Where the corpus's hole cards and finishing stacks live

Reversibility: frozen-into-data

The Phase 02 normalized schema rejects unknown fields and only carries hole cards for
players who reached a showdown. This phase needs more than that: it needs every seat's
cards at every decision point, whether or not the hand got there, and it needs the
corpus's own finishing stacks as the settlement oracle.

Widening the Phase 02 schema to hold them was considered and rejected on two grounds.
It is a Phase 02 contract change, which this phase may not make. And it would put the
oracle inside the same record the replayer produces, which is the one arrangement most
likely to end with the oracle quietly being derived from the thing it checks.

Recommendation: a separate committed sidecar keyed by hand id, holding per hand the
source path, the source checksum, each seat's player name, each seat's dealt hole cards,
and the corpus's finishing stacks. The normalized hands stay exactly what Phase 02 says
a normalized hand is.

Options: separate-sidecar | widen-the-phase-02-schema | derive-what-is-missing
Answer: []

## 4. What happens to a hand the converter cannot express

Reversibility: frozen-into-data

This is the one that decides whether the phase can lie. A converter that quietly skips
the hands it cannot handle produces a perfect settlement rate over whatever was left,
and the number means nothing.

The selection rule is ours, so an unconvertible hand is not bad luck; it is either a
converter bug or a finding about this repo's engine, and a finding about the engine is
the most valuable thing this phase could produce.

Recommendation: the gate requires every hand in the committed sample to convert and to
settle to the corpus's own finishing stacks. There is no silent filter. If a hand turns
out to be genuinely unconvertible for a reason that is documented and accepted, it is
removed by a named entry in a committed exclusion list that states the hand and the
reason, and the report prints the exclusion list in full. An exclusion nobody can see is
the failure mode; an exclusion in a committed file that a reviewer reads is not.

Options: no-silent-filter-plus-named-exclusions | fail-the-gate-on-any-exclusion |
exclude-and-report-a-count
Answer: []

## 5. What counts as agreement with a mixed strategy

Reversibility: runtime-reversible

Phase 05 settled that the strategy collapses a mixed spot by seeded weighted sampling.
So on a spot the chart plays as raise 30% / fold 70%, the strategy returns one action,
and the player did one thing, and comparing those two single actions mostly measures the
seed.

A strategy that folds a hand seven times in ten does not disagree with a fold. Scoring
it as one would make a correctly mixed chart look wrong in proportion to how mixed it
is, which is exactly backwards.

Default: agreement means the observed action carries nonzero weight in the strategy's
own distribution for that spot. The sampled-action match rate is also reported, labelled
as the different and lesser thing it is.

If wrong: both numbers are in the report, so a reader who prefers the other definition
can use it without regenerating anything.

Options: nonzero-weight | sampled-action-match | weight-threshold
Answer: [nonzero-weight, with sampled-action-match reported alongside]

## 6. Whether refusals sit in the agreement denominator

Reversibility: runtime-reversible

A spot the chart cannot answer at all and a spot the chart answers differently from the
player are different findings. Putting refusals in the denominator turns missing
coverage into apparent disagreement, and the fix for one is not the fix for the other.

Phase 07 already established the shape here: refusal coverage is a headline number, not
a footnote, and the refused spots get inventoried rather than counted.

Default: refusals are excluded from the agreement rate and reported as their own
headline figure, with the agreement rate stating its denominator out loud.

Options: excluded-and-headlined | counted-as-disagreements | reported-both-ways
Answer: [excluded-and-headlined]

## 7. Whose decisions are compared, and how they are grouped

Reversibility: runtime-reversible

The corpus is not six anonymous players. One seat is Pluribus, a near-equilibrium
machine, and the others are strong human players drawn from a pool that changes between
sessions. Averaging a bot and a set of humans into one agreement rate produces a number
that describes neither.

There is a second reason to keep them apart. Agreement with Pluribus is the closest
thing this repo will ever have to a correctness signal for the chart. Agreement with the
humans is a tendency measurement, and a disagreement there is as likely to be the human
deviating as the chart being wrong.

Default: compare every seat's preflop decisions, and report Pluribus separately from the
human players, with the report saying plainly what each population is and what a
disagreement with each one does and does not establish.

Options: split-pluribus-from-humans | pluribus-only | pooled
Answer: [split-pluribus-from-humans]
