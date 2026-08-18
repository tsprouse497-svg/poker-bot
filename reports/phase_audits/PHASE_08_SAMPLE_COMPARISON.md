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
| 12 | The gate bites: committed mutations make it fail | PASS - 27 of 27 caught, 11 of them about this phase |

## What the comparison found

The headline figures are 96.3% agreement with Pluribus (439 of 456 scored decisions)
and 93.6% with the human professionals (2,155 of 2,302).

**Both figures are close to meaningless on their own, and the stage 8 review treated
that as a blocker.** 1,975 of the 2,758 scored decisions - 72% - are folds, and folds
agree almost always. Folding a bad hand from early position is the easiest agreement in
poker. Any chart that is not actively broken scores in the nineties on an unsplit rate,
because the pool is mostly junk being thrown away by both sides.

Split by what the player actually did, and by which population did it:

| player's action | Pluribus | rate | humans | rate |
|---|---|---|---|---|
| fold | 332 of 332 | 100.0% | 1616 of 1643 | 98.4% |
| check | 5 of 5 | 100.0% | 16 of 16 | 100.0% |
| raise | 80 of 82 | 97.6% | 385 of 416 | 92.5% |
| call | 22 of 37 | **59.5%** | 138 of 227 | **60.8%** |

The chart and real players disagree about calling four times in ten, and it is not a
quirk of one population: the machine and the humans produce almost the same figure. That
is the phase's real result. The report prints this split and states plainly that the low
figure is the finding, rather than leading a reader to the reassuring one.

**The calling gap is a blind-defence gap.** Split again by the seat the decision was
taken from, the deficit is not spread across the table. Human calls agree 62-77% of the
time in every seat except the big blind, where they agree 66 of 124 times (53.2%); the
big blind alone holds 58 of the 89 human call disagreements. The same seat is also the
one the chart refuses most often, on 96 of its 361 decision points (26.6%) against 1.3%
in the hijack. Those two interact: refusals sit outside every agreement rate, so the big
blind's rate is computed over the subset of its decisions the chart could answer, and
that subset is not a random sample of them. The report prints the per-seat table with
its refusal column beside it for that reason.

**And most of that gap is the chart working as designed.** Two properties of the
committed artifact predict it before anything is measured, and neither was named
anywhere in this phase until 2026-08-13.

The ranges were solved with NL25 rake; this corpus is rake-free. A raked solution
defends the blinds more tightly than a rake-free one, because a share of every pot it
wins is taken away, and the blinds are where that bites hardest. Phase 05's own strategy
report already says so in as many words. So a chart that folds the big blind more often
than these players did is behaving the way a raked solution is supposed to behave.

The ranges were also solved against a 2.5 big blind open. These players opened to a
median 2.25, and only 18.1% of the decisions facing a single raise faced one at or above
2.5. A cheaper price is a correct reason to continue with more hands, and the sample
shows exactly that shape: human calls agree 52.5% facing 2.25 or less, 69.0% between
2.26 and 2.50, and 77.8% above 2.50. The chart is answering a more expensive question
than the one it was asked, and 47 of the 58 big-blind call disagreements faced an open
smaller than the size it was solved for.

What survives as a finding is narrower and more useful than "the chart under-defends":
the committed chart answers a raked table at 2.5x opens, this corpus is a rake-free table
at 2.25x, and nothing in the repo had said so. Whether any of the remaining gap is a
defect is not established here and cannot be, which is what the contract's forbidden
shortcut about human players is for.

This packet previously read the gap as the repo's own over-folding bias appearing
against real opponents - the bias Phase 05's collapse rule showed before it was re-ruled
and Phase 06's fallback still has by construction. That reading is not supported. Both
of those are properties of how this repo collapses or declines a decision; the blind
gap is a property of which solution was committed and at what price it was read. They
are the same shape and not the same cause, and the resemblance is what made the wrong
one easy to reach for.

The second result is coverage. Replaying real hands found **78 distinct spots the chart
cannot answer, against 22 from self-play**, and most of the 78 are new. Self-play only
reaches the spots its own strategy creates, so it was blind by construction to the lines
real opponents take. The self-play inventory has been standing in as the chart work list
since Phase 07; the real-hand inventory should replace it.

## Command summary

| Command | What it proves |
|---|---|
| `pytest_sample_comparison` | 53 tests: the conversion, the oracle, the sample's integrity, and the comparison rules |
| `generate_sample_comparison_report` | Writes both committed reports from the committed sample alone |

Committed reports:

- `reports/active/latest_sample_comparison_report.txt`
- `reports/active/latest_sample_refusal_inventory.txt`

Provenance: `docs/SAMPLE_CORPUS_SOURCE.md`.

## Independent review

`reports/phase_audits/reviews/PHASE_08_SAMPLE_COMPARISON/stage-08-review.md`.

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

## Corrections after the phase closed

A post-hoc review on 2026-08-13 read this phase again with the contract set aside. It
found six things, all of them invisible to a green gate, and two maintenance tasks fixed
them. Nothing about the corpus, the selection rule, or the committed sample changed; what
changed is what the gate proves and what this packet is allowed to claim.

**MAINT-07, the settlement oracle.** The test carrying this phase's central criterion
could not fail on it. It rebuilt each seat's stack from the converter's own
`result.payouts`, which was itself derived from the corpus's finishing stacks, so the
comparison collapsed back to those stacks whatever the engine computed. Forcing the
replayer's guard true and paying every pot to seat 0 left it reporting 0 mismatches
across all 499 hands. The claim held only because `replay_hand` raises internally, and no
mutation had ever targeted the replayer. The assertion now reads the engine's own
settlement, a chopped pot with one chip moved between its two winners proves the guard
fires, and two canaries stand behind it.

**MAINT-09, what a second independent reviewer found.** A reviewer with no knowledge of
the two tasks above read the phase again and verified MAINT-07's fix by its own method:
with the replayer's guard disabled and every pot paid to seat 0, the phase's central
test now reports 433 mismatches of 499 where the old formulation reported none. It then
found the rake and the opening size described above, which between them explain most of
the blind-defence gap this packet had attributed to the repo's own over-folding bias.
It also found that "70 of the 104 human call disagreements" was itself a pooled figure
in four documents - humans-only is 58 of 89 - which is the violation MAINT-08 removed,
reinstated in the sentence announcing the removal. Alongside those: prose in three
places that read a disagreement with a human as a verdict on the chart, which the
contract forbids in as many words; judgment call 5's sampled-action match rate, ruled to
be reported and never built; a decision-point count of 3,056 against 3,048 actual; and
`CORPUS-INEXPRESSIBLE-SPOTS`, filed as undiagnosable, whose 19 refusals are all one
thing - fourth-bet-and-beyond sequences where a seat acts twice, which the Phase 04
schema documents as out of scope for v1. All fixed.

**MAINT-08, the five findings that were left.** The comparison never recorded the
position a decision was taken from, so the calling gap above was never localised. The
action split pooled Pluribus with the humans, which is the one operation judgment call 7
forbids, reintroduced by the fix for a different problem. The self-play cross-reference
would have degraded silently to "every spot is new" if the report it scrapes had moved.
The committed sidecar, the largest file in the sample, was checked by nothing. And the
all-in count in three documents counted preflop shoves only. All five are fixed, with
three more canaries and eight more tests.

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

The full list is `docs/CORPUS_COMPARISON_LIMITS.md`, which collects in one place what
this comparison cannot establish. The ones a reader of this packet most needs:

- **Nothing in this repo can check the committed corpus text against the dataset it
  says it came from.** The checksum proves the file has not changed since it was
  committed, not that it is what the publisher published, and the gate has no network by
  design. Every number here is downstream of that. The only check is the one a reader
  runs: clone the dataset, re-run the builder, and diff, which the deterministic
  selection rule makes byte for byte.
- **The chart was solved with rake and at a 2.5bb open; these hands carry no rake and
  open to a median 2.25.** Both differences push in the same direction as the
  blind-defence gap, and neither is a defect in either side.
- **500 hands is a sample.** Every rate carries its denominator, but the report computes
  no confidence intervals, so the gap between 96.3% and 93.6% is not established as real.
- **A disagreement with a human is not evidence the chart is wrong.** These are strong
  players, but they are not solvers, and they were playing an opponent pool of one
  superhuman bot rather than the pool the chart was solved for.
- **Postflop is not measured at all.** The fallback never bets, so comparing it to real
  postflop play would measure the fallback's known shape.
- **The all-in settlement path is thinly covered**: 24 of the 499 committed hands contain
  an all-in. This packet and two other documents said 7 until 2026-08-13; that count
  scanned for a preflop shove of a full stack and missed both the all-in reached on a
  later street and the caller facing one. A test now pins the number to the sample.
- **Equal starting stacks mean no side pot arises anywhere in the sample**, so side-pot
  settlement is not exercised by this oracle at all.

Filed in `backlog.yml`:

- `CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT` - the calling agreement, now localised to
  blind defence, and what a rake-free or 2.25bb-open solve would settle about it.
- `CORPUS-INEXPRESSIBLE-SPOTS` - 19 refusals that name no spot at all, all of them
  second-orbit sequences the Phase 04 schema documents as out of scope for v1.
- `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK` - the real-hand inventory should replace the
  self-play one as the chart work list.
