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
Nothing took its place: the coverage bullet three below reports more of this sample answered than before the cutover, not less.

**The ranges were solved against a 2.5 big blind open. These players opened to a median 2.25.**
Only 18.1% of the decisions facing a single raise faced one at or above the solved size.
A cheaper price is a correct reason to continue with more hands, so part of every disagreement is the chart answering a more expensive question than the one it was asked.

**Spot keys carry the raise size they were asked at**, since phase 12: `BTN:raise@2.5` is a button open to two and a half big blinds, and a 2.25bb open and a 4bb open are different keys.
The price abstraction did not go away with the coarse key, it became visible.
A price the tree does not hold is still answered from a price it does, and the answer now records which price it was asked at, so a rate here is still computed partly across substituted prices - the difference is that the substitution is counted rather than invisible.

**The chart answers 249 spots, and five of them are opening ranges.**
The cutover's selection rule keeps a spot only where the source prices every terminal below it, and every seat that can open the pot survives it: the lojack, hijack, cutoff, button and small blind each have a first-in range, and behind them sit 25 spots facing a single open and 219 where a three-bet is already in.
What the rule does not keep is the limped pot and the big blind's multiway defence, and the four-bet family is withheld on purpose for a later phase.
So the agreement rates below are computed over almost all of the sample - slightly more of it than the rates published before the cutover, which came from a raked chart holding 36 keys - and what separates the two is the rake and the tree rather than how much of the sample each could reach.

## What the comparison measures

**Preflop only.**
Phase 06's fallback never bets and never raises, so a postflop comparison would measure the fallback's known shape rather than these hands.

**Real players are not an oracle.**
A disagreement means this chart and this player did different things in this spot.
These are strong professionals, but they are not solvers, and they were playing an opponent pool of one superhuman bot rather than the pool the chart was solved for.
Agreement with Pluribus is the closer thing to a correctness signal, and there 475 scored decisions is a sample rather than a proof.
The human denominator is 2,434.
Both grew at the cutover, from 456 and 2,302, because the committed chart answers more of this sample than the retired one did.

**Refusals sit outside every agreement rate, and they are not spread evenly.**
There are 139 refusals, outside every agreement denominator, and they land on **61 distinct spots the chart holds no cell for**.
That is 4.6% of the sample, and it is what the solve does not contain rather than a defect: 52 of them are decisions in a limped pot, which no first-in range in this solve ever enters, 52 are the big blind facing an open with a cold-caller behind it, which the tree has no branch for, 25 are four-bet-or-deeper chains the phase withheld, and 10 are three-bet spots the chart holds but where hero's hand class is outside the solved cells.
The refusal rate runs from 1.0% of the lojack's decision points up to 20.3% of the big blind's, so the seat the chart answers least is the one that acts after a limp and the one whose multiway defence is missing.
That is the shape the raked chart had as well - it refused 26.6% in the big blind against 1.3% in the hijack - so a reader carrying the pre-cutover reading in mind is not being misled here.
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
