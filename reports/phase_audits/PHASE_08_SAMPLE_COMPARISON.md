# Phase 08 Audit Packet: Tiny Normalized Sample Ingestion And Player Tendency Comparison

Written for a reviewer who does not read code.

## Summary in plain language

Until this phase, every number this repo produced was checked against something this
repo wrote. The engine was checked by the replayer, the simulator was checked by the
replayer, and all three were written from the same understanding of the rules by the
same model. A shared misunderstanding would have been invisible to all of them.

This phase brings in 500 real hands that nobody here wrote, published by a university
research group, and checks our arithmetic against theirs.

The corpus is the set of hands the Pluribus agent played against human poker
professionals in 2019. It was chosen because it is an exact match for the one table this
bot can play: six-handed, 50/100 blinds, everyone starting with exactly 100 big blinds.
Every hand shows all six players' cards, and every hand records what each player finished
with. That last number is the point of the whole exercise - it is an answer somebody else
wrote down, which our engine can be wrong against.

Two things were measured.

**Does our engine settle a real hand correctly?** 499 of the 500 hands settle to the
published finishing stacks exactly, for every seat, with no tolerance. The one that does
not is a chopped pot the corpus records in half chips, which this engine cannot express
because it settles in whole chips; it is excluded by name in a committed file rather than
dropped quietly.

**Does our chart play like real players do?** Across 3,048 preflop decisions, the answer
depends entirely on which decisions you look at, and that turned out to be the finding.

## Pass/fail checklist

| # | Claim | Result |
|---|---|---|
| 1 | Every committed hand settles to the corpus's own published finishing stacks | PASS - 499 of 499 |
| 2 | The settlement oracle is never computed from our own replay | PASS - built from the published numbers, and the engine never sees them |
| 3 | No hand is dropped without a committed, named reason | PASS - 1 exclusion, named, with its reason printed in the report |
| 4 | The selection rule is deterministic and nobody chose a hand | PASS - every 20th hand by a stable sort, rerunnable |
| 5 | The corpus's own text is committed so the conversion is checkable offline | PASS - 300 KB alongside the conversion |
| 6 | The comparison is preflop only and says so before any number | PASS |
| 7 | Refusals are reported separately and never counted as disagreements | PASS - 290 refusals, outside every agreement denominator |
| 8 | Every rate carries the count it was computed over | PASS |
| 9 | The machine and the human players are never averaged together | PASS - reported as two populations |
| 10 | Nothing this phase measured was used to edit the thing it measured | PASS - three findings went to `backlog.yml`, no chart changed |
| 11 | Full verification gate green | PASS - 33 commands |
| 12 | The gate bites: committed mutations make it fail | PASS - 20 of 20 caught, including 4 authored here |

## What the comparison found

The headline figures are 96.3% agreement with Pluribus (439 of 456 scored decisions)
and 93.6% with the human professionals (2,155 of 2,302).

**Both figures are close to meaningless on their own, and the stage 8 review treated
that as a blocker.** 1,975 of the 2,758 scored decisions - 72% - are folds, and folds
agree 98.6% of the time. Folding a bad hand from early position is the easiest
agreement in poker. Any chart that is not actively broken scores in the nineties on a
pooled rate, because the pool is mostly junk being thrown away by both sides.

Split by what the player actually did:

| player's action | agreed | of | rate |
|---|---|---|---|
| fold | 1948 | 1975 | 98.6% |
| check | 21 | 21 | 100.0% |
| raise | 465 | 498 | 93.4% |
| call | 160 | 264 | **60.6%** |

The chart and real players disagree about calling four times in ten. That is the
phase's real result. The report now prints this split and states plainly that the low
figure is the finding, rather than leading a reader to the reassuring one.

It is also consistent with what this repo already knows about itself. Phase 05's
original collapse rule over-folded by 13 points against three-bets before it was
re-ruled, and Phase 06's postflop fallback over-folds by construction. The calling gap
is the same bias appearing against real opponents instead of against our own simulator.

The second result is coverage. Replaying real hands found **78 distinct spots the chart
cannot answer, against 22 from self-play**, and most of the 78 are new. Self-play only
reaches the spots its own strategy creates, so it was blind by construction to the lines
real opponents take. The self-play inventory has been standing in as the chart work list
since Phase 07; the real-hand inventory should replace it.

## Command summary

| Command | What it proves |
|---|---|
| `pytest_sample_comparison` | 40 tests: the conversion, the oracle, the sample's integrity, and the three comparison rules |
| `generate_sample_comparison_report` | Writes both committed reports from the committed sample alone |

Committed reports:

- `reports/active/latest_sample_comparison_report.txt`
- `reports/active/latest_sample_refusal_inventory.txt`

Provenance: `docs/SAMPLE_CORPUS_SOURCE.md`.

## Independent review

`reports/phase_audits/reviews/PHASE_08_SAMPLE_COMPARISON.md`.

No independent reviewer was available: subagent delegation is disabled in this
operator's sessions, which overrides the coordinator default in `AGENTS.md`. Step 10 of
that file permits self-review when the reason is recorded, and it is recorded there and
here. The weakness is real and should be read as real - the same mind wrote the
contract, the tests, and the implementation.

The compensating control was two passes with different questions. The mechanical pass
found nothing the gate had not already caught. The domain pass ignored the contract
entirely and found the fold-dominated headline described above, which the gate was never
going to catch because the arithmetic was correct throughout.

Two frozen tests needed repair mid-phase - an attribute name and a line length. Both
were authoring defects rather than behavior, both were repaired in dedicated tasks with
the tests re-frozen, and neither weakened an assertion. They are recorded because the
freeze exists to make exactly that visible.

## Decisions

Seven judgment calls were recorded before implementation in
`reports/phase_audits/decisions/PHASE_08_SAMPLE_COMPARISON_DECISIONS.md`. Four were
`frozen-into-data` and blocked the loop until Taylor ruled on them at the stage 3 human
gate on 2026-08-12. He took the recommendation on all four.

| # | Call | Outcome |
|---|---|---|
| 1 | Which hands the sample holds | Every 20th by sorted path, 500 hands. Spreads across all 92 sessions instead of five consecutive ones |
| 2 | Commit the corpus's own text | Yes, 300 KB, so the conversion is checkable without the network |
| 3 | Where the hole cards and finishing stacks live | A separate sidecar, so the oracle never sits inside the record the replayer produces |
| 4 | Hands the converter cannot express | No silent filter; one named exclusion, printed in full |
| 5 | What agreement means | Nonzero weight in the chart's distribution, not a matching draw |
| 6 | Refusals in the agreement denominator | Excluded and headlined |
| 7 | Who is compared | Pluribus separate from the humans |

Calls 5, 6 and 7 were `runtime-reversible` and proceeded on their recorded defaults.
All three are defended by mutation canaries, so reversing one silently is not possible.

## A number you can recompute by hand

**Claim: the first hand in the committed sample settles to the corpus's published
finishing stack for seat 0, and our engine agrees to the chip.**

Open `data/samples/public_corpus/corpus_hands.jsonl` and find `pluribus/100/0.phh`. It
records six players starting with 10,000 each, blinds of 50 and 100, and this sequence:

- p4 raises to 210. p5, p6, p3 and p2 fold.
- p1, who had already posted the small blind of 50, calls.
- Flop and turn check through.
- On the river p1 bets 230 and p4 folds.

Add up what each player put in:

- p1: 50 (small blind) + 160 (the extra needed to reach 210) + 230 (river bet) = **440**
- p2: 100 (big blind)
- p4: 210

Pot = 440 + 100 + 210 = **750**. Everyone but p1 has folded, so p1 wins all of it,
including their own uncalled river bet.

p1 finishes with 10,000 - 440 + 750 = **10,310**.

Now look at the same hand's published `finishing_stacks` line in the corpus text:
`[10310, 9900, 10000, 9790, 10000, 10000]`. The first number is 10,310.

The corpus was written in 2019 by somebody with no knowledge of this repo. Our engine
replays the hand independently and settles to the same number, and the same check holds
for all six seats of all 499 hands. That is the only claim in this repository whose
right answer came from outside it.

You can also check the sample's own arithmetic: `corpus_hands.jsonl` has 499 lines and
`corpus_exclusions.json` names 1 hand. 499 + 1 = 500, which is what the selection rule
chose out of 10,000.

## Known limitations and deferred items

- **500 hands is a sample.** Every rate carries its denominator, but the report computes
  no confidence intervals, so the gap between 96.3% and 93.6% is not established as real.
- **A disagreement with a human is not evidence the chart is wrong.** These are strong
  players, but they are not solvers, and they were playing an opponent pool of one
  superhuman bot rather than the pool the chart was solved for.
- **Postflop is not measured at all.** The fallback never bets, so comparing it to real
  postflop play would measure the fallback's known shape.
- **The all-in settlement path is thinly covered**: 7 of the 500 hands contain an all-in.
- **Equal starting stacks mean no side pot arises anywhere in the sample**, so side-pot
  settlement is not exercised by this oracle at all.

Filed in `backlog.yml`:

- `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` - the 60.6% calling agreement and what would
  settle whether it is our ranges, our pricing, or real players calling too wide.
- `CORPUS-INEXPRESSIBLE-SPOTS` - 19 refusals that name no spot at all, the largest single
  bucket and the only one nobody can act on.
- `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` - the real-hand inventory should replace the
  self-play one as the chart work list.
