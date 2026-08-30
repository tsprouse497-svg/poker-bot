# What The Corpus Comparison Cannot Establish

One place naming the limits of the real-hand comparison, so a reader does not have to reconstruct them from three audit files.
Everything here is a standing property of the measurement, not a defect and not a to-do.
Provenance is in `docs/SAMPLE_CORPUS_SOURCE.md`; results are in `reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md`.

## The one that everything else rests on

**Nothing in this repo can check the committed corpus text against the dataset it says it came from.**

`corpus_hands.jsonl` carries a checksum, and the checksum proves the file has not changed since it was committed.
It cannot prove the file is what the publisher published.
The verification gate has no network by design, so the DOI and the repository URL in the source card are assertions a reader trusts, not claims the gate tests.

Every number in Phase 08 is downstream of this.
If the committed text were wrong, the settlement oracle, the agreement rates, and the refusal inventory would all be internally consistent and all be about hands nobody played.
The only check is the one a reader runs themselves: clone the dataset, re-run `scripts/build_sample_corpus.py`, and diff.
The selection rule is deterministic precisely so that diff is byte for byte.

## What the chart was solved for, and what these hands were played at

**The committed ranges and this corpus are both rake-free.**
This was the largest caveat in this document until the chart cutover, which replaced a raked NL25 GTO Wizard chart with a rake-free GTOpen solve.
A raked solution defends the blinds more tightly than a rake-free one, because a share of every pot it wins is taken away, and every rate published before the cutover carried that gap.
The caveat is retired rather than reduced: the rake is gone from both sides of the comparison.
What replaced it is narrower coverage, two bullets below.

**The ranges were solved against a 2.5 big blind open. These players opened to a median 2.25.**
Only 18.1% of the decisions facing a single raise faced one at or above the solved size.
A cheaper price is a correct reason to continue with more hands, so part of every disagreement is the chart answering a more expensive question than the one it was asked.

**Spot keys carry the raise size they were asked at**, since phase 12: `BTN:raise@2.5` is a button open to two and a half big blinds, and a 2.25bb open and a 4bb open are different keys.
The price abstraction did not go away with the coarse key, it became visible.
A price the tree does not hold is still answered from a price it does, and the answer now records which price it was asked at, so a rate here is still computed partly across substituted prices - the difference is that the substitution is counted rather than invisible.

**The chart answers 86 spots, and exactly one of them is an opening range.**
The cutover's selection rule keeps a spot only where the source prices every terminal below it, which leaves the small blind's open, the big blind's defences, and the heads-up continuations behind them.
Every other seat refuses a pot that is folded to it.
So the agreement rates below are computed over a small and deliberately chosen slice of the sample rather than over most of it, and they are not comparable with the rates published before the cutover, which came from a chart holding five opening ranges.

## What the comparison measures

**Preflop only.**
Phase 06's fallback never bets and never raises, so a postflop comparison would measure the fallback's known shape rather than these hands.

**Real players are not an oracle.**
A disagreement means this chart and this player did different things in this spot.
These are strong professionals, but they are not solvers, and they were playing an opponent pool of one superhuman bot rather than the pool the chart was solved for.
Agreement with Pluribus is the closer thing to a correctness signal, and there it is now 72 scored decisions, which is an illustration rather than a sample.
The human denominator is 447.
Both collapsed at the cutover, from 456 and 2,302, because the decisions the retired chart answered from its four other opening ranges are now refused.

**Refusals sit outside every agreement rate, and they are not spread evenly.**
There are 2,529 refusals, outside every agreement denominator, and they land on **154 distinct spots the chart holds no cell for**.
That is five sixths of the sample, and it is the cutover's own cost rather than a defect: the retired chart held four more opening ranges and ten more spots facing a single open, and every decision that reached one of those refuses now.
The rate runs from 97.3% of the lojack's decision points down to 33.9% of the big blind's, so the one seat the chart was derived for is the only seat it answers most of the time.
The spread also inverted - before the cutover the big blind refused most and the hijack least - which is worth stating because a reader carrying the old shape in mind would read these rates backwards.
That subset is not a random sample of them.

## What the sample is

**499 hands, 3,048 preflop decisions, 14 players, one table configuration.**
Every rate is printed with its denominator, but no confidence interval is computed, and an interval would be optimistic anyway: the decisions are clustered, not independent.
They come from 499 hands, a handful of players, and a small number of chart cells - folding trash from the lojack is one cell reached hundreds of times.

**The all-in settlement path is thinly covered**: 24 of the 499 hands contain an all-in.

**No side pot arises anywhere in the sample.**
Every seat starts each hand on exactly 10,000, so side-pot settlement is not exercised by this oracle at all.

**The one exclusion is not a random miss.**
`corpus_exclusions.json` names 1 hand, and `pluribus/41b/204` is excluded because the published settlement splits a pot into half chips and this engine settles in whole ones.
Half-chip settlements only arise on chopped pots, so the exclusion rule can only ever remove chops - it is correlated with hand type by construction.
The four whole-chip chops that remain do settle exactly, which is a real and otherwise unstated result: this engine's odd-chip rule agrees with the publisher's.

## What the reports depend on beyond the sample

The refusal inventory's "also in self-play" column is recovered by pattern from Phase 07's rendered report, not from the committed sample.
It raises rather than returning nothing when it cannot recognise that file, so the failure is loud, but the column is still a claim about another phase's output rather than about these hands.
