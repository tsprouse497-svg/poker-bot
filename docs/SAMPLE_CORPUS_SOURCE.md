# Source Card: The Committed Public Hand Corpus

This is the provenance record for `data/samples/public_corpus/`.
A checksum proves a file has not changed; it cannot establish where the file came from or what it is allowed to be used for.
That is what this document is for, and it is written to be read by a reviewer rather than by a script.

## What the corpus is

The Pluribus subset of the Poker Hand History (PHH) dataset: every hand played by the Pluribus agent against human professionals, published as supplementary material to Brown and Sandholm (2019).

- Publisher: Universal, Open, Free, and Transparent Computer Poker Research Group, University of Toronto.
- Stable identifier: Zenodo concept DOI `10.5281/zenodo.10796885`.
- Repository the committed hands were taken from: `https://github.com/uoftcprg/phh-dataset`, path `data/pluribus`.
- Licence: MIT for the GitHub distribution; the Zenodo record reports CC-BY-4.0.
  Both require attribution, which this document provides and the generated report repeats.
- Retrieved: 2026-08-12.

## Why this corpus and not another

The committed preflop chart answers exactly one table: six-handed, no-limit hold'em, 50/100 blinds, one flat stack depth of 100 big blinds.
Every one of the corpus's 10,000 hands is that table.
Starting stacks are 10,000 for all six seats in all 10,000 hands, blinds are 50/100 in all 10,000, and antes are zero throughout.
So these hands land on the chart rather than in the refusal path by construction, and a refusal here is a real coverage gap rather than an artifact of asking the wrong question.

Two further properties decided it.

No hole card is obfuscated. All 60,000 dealt cards are recorded, so a player who folded preflop still has a known holding, and the spot they folded is exactly the spot worth asking the chart about.
The other large subset in the same dataset, the HandHQ logs, is 21.6 million real-money hands with every card replaced by `????`, which permits an aggregate frequency comparison and no decision-level comparison at all.

Every hand carries `finishing_stacks`, and all 10,000 conserve chips.
That is the settlement oracle this phase exists for, and it was written by the publisher rather than by this repo.

## What was committed, and by what rule

The rule is every 20th hand by a stable lexicographic sort of the corpus's own file paths, giving 500 hands.
It is implemented once, in `select_source_paths`, which both the builder and the test that pins it call.

A stride rather than a prefix, because a prefix draws from about five consecutive sessions: only 7 distinct players ever hold the button and just 3 hands contain a preflop shove.
The stride spreads the same 500 hands over 91 of the corpus's 92 sessions, giving 13 distinct button players and 7 hands with a preflop shove.
Nobody chose a hand, and re-running the rule against the same corpus reproduces the sample byte for byte.

Those shove counts were the measure used when the rule was chosen, and they undercount all-ins.
PHH writes an aggressive action as the total its actor's street bet reaches, so counting the ones that read `10000` finds a preflop shove from a full stack and nothing else: not an all-in reached on a later street, and not the caller on the other side of one.
Counted properly - a seat committing its whole 10,000 - the committed sample holds 24 all-in hands, not 7, and `test_the_all_in_coverage_the_documents_claim_is_the_coverage_the_sample_has` pins that number so this paragraph cannot drift from the data again.
The comparison between the prefix and the stride was made on the same undercount for both, so it still favours the stride; only the magnitudes were wrong.

Three files are committed:

- `corpus_hands.jsonl` - the corpus's own text for exactly the selected hands, unmodified.
  Committed so the conversion is checkable offline by a reader who does not trust it.
- `corpus_sidecar.json` - per hand, the source path and checksum, each seat's player name and dealt hole cards, and the published starting and finishing stacks.
  Separate from the normalized hands on purpose: the Phase 02 schema rejects unknown fields, and putting the oracle inside the record the replayer produces is the arrangement most likely to end with the oracle quietly derived from the thing it checks.
- `corpus_exclusions.json` - every selected hand that is not in the sample, named, with its reason.

## The exclusions

One hand of the 500 is excluded.

`pluribus/41b/204` is a chopped pot.
Two players make the same hand on `AcKd6h Qc 3c` and the published settlement splits the pot into half chips, recording finishing stacks of 10162.5.
This repo's engine settles in whole chips, so the hand cannot be expressed rather than being expressed wrongly.
Eight of the corpus's 10,000 hands are like this; exactly one fell in the stride.

The exclusion is a committed file rather than a count, because a hand dropped where a reviewer cannot see it is precisely the failure this phase's central number would otherwise hide.

## What this licence permits and this phase does

The hands are redistributed here under attribution, unmodified, at a scale of 500 out of 10,000.
They are used to check this repo's settlement arithmetic and to compare its preflop decisions against recorded play.
They are not used to fit, tune, or edit any chart, strategy, or artifact - the phase contract forbids it, because editing the thing being measured so it agrees with the sample destroys the measurement.

## Reproducing the sample

```
git clone --filter=blob:none --sparse https://github.com/uoftcprg/phh-dataset
cd phh-dataset && git sparse-checkout set data/pluribus
uv run python scripts/build_sample_corpus.py --corpus <clone>/data/pluribus
```

The builder is deliberately absent from the verification gate.
It needs the full corpus, which is not in this repo and is not going to be, and a builder inside the gate would rewrite its own evidence on every run.
