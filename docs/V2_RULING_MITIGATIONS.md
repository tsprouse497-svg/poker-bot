# V2 Ruling Mitigations

**A plan, not work done.**
Nothing in this document has been acted on, no phase has been declared, and no check, limit, or solve described below exists.
It is here so the agent that eventually does the work starts from the analysis instead of rediscovering it, or worse, engineering around the symptom.

The seven v2 rulings are recorded at the end of `docs/V2_ROADMAP.md`.
Three of them carry a consequence that will damage a later phase if nobody plans for it.
Each section below states the mechanism, what it costs, what to do, and which phase owns it.

The three are not equally severe.
Issue 3 can silently void a phase's headline measurement and degrade the product phase; issue 1 can quietly retire the repo's only external reference; issue 2 is a cost to manage rather than a defect to avoid.

## 1. The Expectations File Measures Exactly What Rake Moves

**Owner: proposed phase 10. Ruling: rake-free.**

### The mechanism

`data/artifacts/preflop/expectations/six_max_nl25_100bb.json` holds eleven numbers and nothing else: opening frequency for five positions, big-blind defence against five openers, and the small blind's limp frequency.
Its own `notes` field states the job it exists to do, which is to catch a range that is uniformly wrong rather than merely self-consistent.
It is the only set of numbers in the repo that the repo did not produce, and that is the whole of its value.

Every one of those eleven numbers is rake-sensitive.
Phase 08 established the direction and the reason: a raked solution plays tighter because a share of every pot it wins is taken away, and it bites hardest in the blinds, which is where the defence numbers are measured.

So the obvious mitigation is unavailable.
The file cannot be split into a rake-invariant half checked tightly and a rake-sensitive half checked loosely, because there is no rake-invariant half.

What is left is a check whose expected disagreement is unknown, and that is the worst kind to own.
A tolerance wide enough to admit a legitimate rake-free solve is also wide enough to admit an extraction with suited and offsuit transposed.
A tolerance tight enough to catch that transposition fails a correct solve.
The likely outcome is that whoever runs the phase widens the tolerance until it passes, which converts the repo's only external reference into decoration while leaving it looking like a check.

### Mitigation

Three parts, in descending order of value.

**Run a parity solve, and grade the extractor on that.**
GTOpen takes `rake_pct` and `rake_cap` as ordinary config, confirmed by the accepted body in `docs/GTOPEN_SOLVER_NOTES.md`.
So phase 10 can run a second solve at the NL25 basis the expectations file describes, compare its eleven aggregates against the file directly, and only then run the rake-free solve that gets committed.
This is the part worth paying for.
It restores an apples-to-apples comparison, which turns an uninterpretable difference into an interpretable one, and it separates two questions that are otherwise fused: whether the extractor is correct, and whether rake-free differs from raked in the direction and amount expected.
If the parity solve matches, every remaining difference in the committed solve is attributable to rake alone, and the rake-free numbers become a finding rather than an anomaly.

Two qualifications, both of which should be written into the contract rather than discovered afterwards.
GTOpen is not GTO Wizard, so even at a matched rake basis the two will not agree exactly; different solvers, abstractions, and convergence targets guarantee that, and the tolerance has to be set for solver difference rather than for zero.
And the expectations file carries a small-blind limp frequency of 13.73 percent, which means the source solve had limps in its tree, so the parity solve needs `limp: true` to be comparing the same thing.
That is a second point in favour of the limps ruling, arrived at independently.

**Assert the orderings, which rake does not change.**
Rake moves the level of all eleven numbers and the ordering of none of them.
The file states opening frequency as BTN 40.56, SB 34.41, CO 27.89, HJ 21.65, LJ 17.49, and big-blind defence as SB 42.88, BTN 39.43, CO 31.48, HJ 26.20, LJ 22.63.
Later position opens wider, and the big blind defends wider against later position, with the small blind sitting high in both because it is the position acting into one opponent.
Those orderings are structural.
An extraction with a transposed index, a mis-assigned actor, or an unnormalised strategy array breaks them immediately, and a legitimate rake-free solve preserves every one.
This is the tight check the level comparison cannot be, it is derivable from the file as it stands today, and it costs nothing.

**Bound the direction, not just the magnitude.**
Removing rake should widen play everywhere.
A rake-free solve that comes back tighter than the raked expectations on any of the ten opening and defence numbers is wrong regardless of by how much, and that is a one-sided check that needs no tolerance at all.
Exclude the limp frequency from it.
Rake's effect on how often the small blind limps rather than raises is not obviously signed, and a directional check should not be extended to a number whose direction is a guess.

**Write all three down before the solve runs.**
This is the freeze-then-build discipline the loop already applies to tests, pointed at a threshold.
A tolerance authored after the numbers are visible is a tolerance fitted to them.

### What it costs

One extra solve, of unknown duration, on a phase that already owes a solve-time measurement.
Nothing else.

## 2. The Artifact Roughly Doubles, And Nothing Checks Its Size

**Owner: proposed phase 14, with a measurement owed by proposed phase 10. Ruling: limps in the tree.**

### The mechanism

The committed chart is 262,713 bytes for 36 spots, which is where the 7.1 KB per spot figure comes from.
The v1 spot vocabulary can express 1,691 six-handed 100bb spots with limps and 848 without, so the limps ruling moves the estimate from roughly 6 MB to roughly 12 MB.

That estimate deserves less confidence than it usually gets.
7.1 KB per spot is measured off a JSON artifact derived from a GTO Wizard export, and a GTOpen export is a different shape carrying a different action set.
The true figure could be materially higher or lower, and every plan that quotes 12 MB is quoting an extrapolation from a 36-spot sample of a different format.

Three costs follow, and only the third is obvious.

Git keeps every version forever.
One large JSON blob of floats deltas poorly, so each re-solve adds close to its full size to the repository permanently, and the chart is a thing that gets re-solved.

The gate runs on every task and loads the library.
A twenty-fold increase in artifact size is a gate that is slower for every future phase, not just for the phase that commits it.

And nobody can review 1,691 range grids.
The repo's standing position is that committed data is reviewable, which is why the current artifact has a builder, a checksum, and a human-readable report.
Scale defeats that quietly: the artifact stays formally auditable while ceasing to be actually audited.

Meanwhile `scripts/check_file_sizes.py` covers `reports/active/*.txt`, `reports/active/*.json`, and phase audit logs.
`data/artifacts/**` appears in neither `LINE_LIMITS` nor `BYTE_LIMITS`.
A 12 MB artifact, or a 40 MB one, commits today with nothing objecting.

### Mitigation

**Measure before phase 14's contract quotes a number.**
Phase 10 writes the export and can report its real bytes per spot.
Phase 14 should set its expectations from that measurement rather than from the extrapolation in the roadmap.

**Add a byte limit covering the artifacts directory.**
A stated number in `BYTE_LIMITS` turns "the artifact got large" from something nobody notices into a gate failure and therefore a decision.
Set it above the measured size with deliberate headroom, and treat exceeding it as a halt rather than as a number to raise.
This is the cheapest item in this document and it does not depend on any other decision here.

**Split the limped spots into their own artifact.**
This was checked rather than assumed.
`PreflopChartLibrary.__init__` takes a sequence of artifacts and refuses to build if two declare the same spot key, and `from_directory` imports every `*.json` under a directory, so two non-overlapping artifacts in the same directory compose with no code change at all.
The limped and unlimped spot sets do not overlap by construction.

That split buys three things.
The common path stays near its original size, since limped pots accounted for 12 rows and 21 decision points of the corpus refusal inventory against 250 points in raised pots.
A limp re-solve produces a diff that does not touch the file every hand reads.
And the limps ruling stays independently revisitable, which matters because it is the one ruling made on a cost estimate that this section has just argued is unreliable.

**Consider per-spot files only if the measurement comes back high.**
One file per spot makes a re-solve touching 40 spots a 40-file diff, which is reviewable in a way a single blob is not, and it deltas well in git.
It costs load time, answerable with an index.
It is a real option but not a default, and it should be decided against a measurement rather than against this paragraph.

### What it costs

The byte limit is minutes.
The split is a builder that writes two files instead of one.
Neither is on the critical path.

## 3. The Solved Price And The Played Price

**Owner: named in proposed phase 12, but it constrains proposed phase 10's solve config.**

This is the severe one.

### The mechanism

Proposed phase 12 puts raise size into the spot key so that a 2.25bb open and a 2.5bb open stop sharing a cell, which is the correct fix for a real defect: today every agreement rate in the repo is computed across prices the chart cannot tell apart.

The solve is ruled at 2.5bb.
The corpus opened to a median 2.25bb, and Phase 08 measured the tail: **only 18.1 percent of the decisions facing a single raise faced one at or above 2.5**.
Under exact size matching, a chart solved only at 2.5 answers at most that 18.1 percent, and in fact fewer, because that figure includes 3bb and 4bb opens which also fail to match exactly.

So proposed phase 14's closing measurement, which is the measurement that decides whether the calling gap was rake and price or a real defect, would run against a single-digit percentage of the sample and report an agreement rate computed on almost nothing.
The failure is not that it produces a wrong answer.
It is that it produces a confident-looking one.

The product cost is larger than the measurement cost and gets less attention.
Proposed phase 15 deals real spots to a human, and a human facing a 2.25bb open would get a refusal.
The roadmap's own argument for putting the drill after the chart cutover was that a trainer which says no opinion teaches nothing.
Exact size matching against a single solved price reintroduces exactly that, after the phase that was supposed to fix it.

### The axis the ruling did not settle

The question Taylor answered was what open size the solve is built at, and the natural reading of that is the price the bot opens to.
Coverage of the prices the bot *faces* is a different axis, and nobody asked about it, because the collision had not been identified when the ruling was made.

Nothing below re-opens the 2.5bb ruling.
The bot opening to 2.5 and the bot being able to answer a 2.25 it did not choose are compatible, and the tree can carry both.

### The four available answers, ranked

**Solve the prices. Recommended.**
`open_raises` is a list in the config surface recorded in `docs/GTOPEN_SOLVER_NOTES.md`, exercised as `[2.5]` but typed as an array, so one tree can carry several opening sizes.
Putting the prices real hands actually use into the tree dissolves the problem rather than managing it, keeps the spot key exact, keeps the fail-closed property intact, and needs no new rule anywhere.
It costs a larger tree and more spots, on top of the limps ruling which already enlarged both.
That interaction is the reason it needs deciding at phase 10 rather than phase 12.

**Nearest solved price, with the substitution recorded.**
Answer from the nearest solved size and refuse beyond a stated maximum distance.
The saving property is not the rule but the record: the answer carries a flag saying it was asked at 2.25 and answered at 2.5, so every downstream number can be filtered on it and no measurement silently mixes exact answers with substituted ones.
That is the same idea as the structured `detail` a `StrategyRefusal` already carries, applied to the branch that answers instead of the branch that declines.
Viable as a fallback, and strictly better than a bucket because the approximation stays visible per decision rather than being dissolved into the key.

**Buckets with a stated tolerance. Not recommended, and the evidence is specific.**
A bucket declares that two prices are the same spot, which is the exact claim phase 12 exists to stop making.
The repo has already measured what that claim costs across this particular boundary: human calls agree with the chart 52.5 percent facing 2.25 or less, 69.0 percent between 2.26 and 2.50, and 77.8 percent above 2.50.
A bucket spanning 2.25 and 2.5 therefore merges populations that differ by 16.5 points of agreement, and 47 of the 58 big-blind call disagreements sat below the solved size.
It would also sit uncomfortably against the boundary ruled to hold permanently, that there is no heuristic guessing for missing chart spots.

**Refuse. Honest, and too expensive.**
Purest against the fail-closed ethos, and it is what the current design does by default.
It voids the phase 14 measurement and cripples the phase 15 drill, as above.
Worth stating explicitly as the do-nothing baseline so that choosing anything else is a deliberate act.

### The sequencing fix

The roadmap's ordering rule is format before data, with proposed phase 10 as the deliberate exception on the grounds that a solver export is written in the solver's own vocabulary and so does not depend on the format work.

That exception has a limit, and this is it.
The export's vocabulary is indeed independent, but the solve's **config** is not: how the spot key matches a price determines which prices `open_raises` must contain, and `open_raises` is set before the solver runs.
Discovering the answer at phase 12 means either re-solving or living with whichever answer the already-committed export permits.

So the recommendation is that the size-matching decision is made and recorded at **phase 10's contract stage**, even though phase 12 implements it.
That is one line in a contract, and it is the difference between choosing this and inheriting it.

### The guard worth adding whichever answer is chosen

Proposed phase 14's closing measurement should report the retained sample and the refusal rate beside the agreement rate, with a stated floor below which the measurement is declared void rather than published.
An agreement rate computed on 6 percent of the sample and one computed on 90 percent look identical in a report and mean entirely different things.
The refusal inventory that Phase 08 built already produces the input, so this is a reporting requirement rather than new machinery.

## What Can Be Done Before Any Solve

Four items, none of which needs a ruling, a solver, or a declared phase.
Any of them could be a maintenance task tomorrow, and all four make the phases that follow cheaper.

1. **Measure the corpus opening-price distribution properly.**
   The repo has a median and one tail figure. What the price decision needs is the shape: how much of the sample sits at each price, and whether it clusters at 2.25 or spreads across 2.0 to 3.0.
   Clustered means two solved prices cover almost everything; spread means no small set does and the nearest-price fallback becomes necessary.
   This is the single measurement that most changes the answer to issue 3, and the corpus to measure it on is already committed.
2. **Recompute the spot counts and bytes per spot as facts rather than extrapolations.**
   The 1,691 and 848 counts are recomputable by enumerating `solver_artifacts.schema.spot_key` over action sequences, and 7.1 KB per spot is measurable from the committed artifact.
   Both are quoted throughout the roadmap and neither has been checked recently.
3. **Add the `data/artifacts/**` byte limit to `scripts/check_file_sizes.py`.**
   Independent of every other decision here, and it is the only mitigation in this document that closes a gap which exists right now rather than one that arrives with a future phase.
4. **Write the three expectations-file checks down.**
   The orderings, the directional bound, and the parity-solve comparison, stated as prose before any solve exists to tune them against.

## What Needs Taylor

One question, and it is not a re-opening of a ruling already made.

**Does the solved tree carry more than one opening price?**
The 2.5bb ruling settled what the bot opens to and that stands.
This is about what prices it can answer when it is facing an open rather than making one, and the evidence says a single solved price answers under a fifth of the decisions real hands presented.
The recommendation is that it does, with the exact set chosen from the distribution measurement in item 1 above.

Everything else in this document is an engineering decision that belongs to the phase that owns it.
