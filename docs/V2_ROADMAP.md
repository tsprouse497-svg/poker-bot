# V2 Roadmap (Proposed)

**This is a proposal, not the sequence.**
`phase_status.yml` holds ten completed phases and nothing after them, and it stays that way until someone adopts this document in a separate task.
Nothing here is declared: no contract skeleton exists for any phase below, `verification/loop_policy.yml` has no entry for them, and the V1 boundaries in `AGENTS.md` are unchanged.

A future agent reading this should treat it as an argument to evaluate rather than a plan to execute.

The seven questions this document originally left open were all ruled on by Taylor on 2026-08-15, and the rulings are recorded at the end.
They are decisions about what to build, not adoption of the sequence that builds it, and three of them describe boundaries that `AGENTS.md` still states the old way.

## Where V1 Leaves The Repo

Ten phases produced a deterministic engine, a replayer that refuses out-of-order hands, a strategy contract that refuses rather than guesses, a fail-closed chart lookup, a self-play simulator, a public-corpus comparison, and a verification gate that proves itself by breaking on purpose.
That machinery is the asset and v2 keeps all of it.

The ceiling v1 reached is three things, and they are different in kind.

The committed chart answers 36 spots.
Against the committed public corpus it refuses at 290 of 3,048 decision points, spread over 78 rows of `reports/active/latest_sample_refusal_inventory.txt`.
Of those rows, 65 are raised pots the v1 vocabulary can express (250 decision points), 12 are limped pots (21 points), and one is a catch-all for the 19 points where a seat acts twice and no v1 spot key exists at all.

The postflop fallback never invests unless it cannot lose, so it never bets and is exploitable by any bet whatsoever.

There is no human-facing surface anywhere in the repo.
Every entry point under `scripts/` is a report generator, so nobody can currently use this to get better at poker.

The backlog is where v1 recorded what it could not reach.
Roughly twenty-five deferred entries, and almost every one is a phase below or part of one.

## Boundaries

The V1 boundaries live in `AGENTS.md`, so changing any of them is a `contract-update` and not something a phase does in passing.
Every row below is ruled rather than proposed, as of 2026-08-15.
Only one row moves, and `AGENTS.md` has not moved with it yet.

| V1 boundary | Ruled | Reason |
| --- | --- | --- |
| No heuristic guessing for missing chart spots | Holds permanently | It is the property that makes every number in this repo mean something. |
| No runtime solver calls | Holds permanently | Offline extraction into a committed artifact is a different thing and is already how charts are built. |
| No large hand-history ingestion | Lifts, bounded | A leak report on your own play needs your own hands. The lift is for a single player's own history with a stated size bound, not corpus-scale mining. |
| No UI package | Stays deferred | Revisit once the drill exists. A UI over a training loop nobody has used yet is a commitment made on a guess. |
| No PokerNow automation | Stays out of v2 | Terms of service and account risk are a human ruling rather than an engineering one, and the ruling is to stay out. |
| No browser or platform observation | Stays out of v2 | Same ruling, and it only pays off once there is something worth observing for. |

The ingestion lift is the only change, and it is owed two things before proposed phase 15 can use it: the size bound stated as a number, and the wording in `AGENTS.md`.
Until that `contract-update` lands, the boundary as written forbids what this table says is allowed, and the file wins.

## Ordering Rule

Format before data, data before product.
A chart is expensive to solve and expensive to re-commit, so nothing that changes what a chart file can express may land after the chart does.

There is one deliberate exception and it is the first phase.
A solver export is written in the solver's own vocabulary rather than in this repo's spot keys, so capturing one does not depend on the format work at all.
Whether an extraction is faithful is also a question only a human looking at range grids can answer, and that verification should happen early rather than after three phases of plumbing.
So the export and its human verdict lead; only the derived chart waits for the format.

## The Proposed Phases

### 10. Solver Extraction, And A Human Verdict On It

Commits the export. Would not auto-advance. Changes no chart.

`docs/GTOPEN_SOLVER_NOTES.md` records what was verified about GTOpen by running it, and what was not.
This phase answers the unverified list with numbers: solve time to a stated exploitability target, determinism across two identical runs, the node payload's path encoding, and whether a node's strategy is conditioned on reaching that node.
The last one decides whether the converter needs the range-intersection step the GTO Wizard export required.

It then walks the tree, writes the export, and produces a range report a person reads: grids per spot, opening and defence frequencies, and those same aggregates checked against `data/artifacts/preflop/expectations/six_max_nl25_100bb.json`.
That expectations file is the only set of numbers in the repo that the repo did not produce, which makes it the one thing that can catch an extraction that is uniformly wrong rather than merely self-consistent.
It should be retained for that reason even after the chart it describes is retired.

The rulings this phase needs are the ones baked into the solve itself, and all four are made.

| Ruling | Decided | Consequence for this phase |
| --- | --- | --- |
| Rake | Rake-free | Matches the games this trains for and makes the corpus comparison apples-to-apples. It also means the expectations file describes a different solve than the one being checked against it. |
| Open size | 2.5bb, as today | Only one variable moves at the chart cutover. The corpus median is 2.25bb, so a price gap survives into proposed phase 14. |
| Limps | In the solved tree | Closes the limped-pot refusals rather than deferring them. Larger solve, and roughly double the artifact. |
| Licence | Proceed, and record the gap | GTOpen ships no LICENSE file. The source card must state that plainly as a known limitation rather than leave `source.kind` implying a permission nobody granted. |

Rake-free is the ruling that changes this phase's own verification, so it needs saying in full.
`six_max_nl25_100bb.json` describes a raked NL25 solve, and the whole finding of the Phase 08 review was that rake predicts tighter blind defence.
Checked against a rake-free solve, that file is a gross-error check and not an equality check: a uniform tolerance would either pass an extraction that is badly wrong or fail one that is right, and blind defence is exactly where the legitimate difference lands.
The honest form is a wide bound on the aggregates rake moves and a tight one on the aggregates it does not, with the split stated rather than tuned until it passes.
Its value is unchanged and so is the reason to keep it: it catches an extraction that is uniformly wrong, which is the failure self-consistency cannot see.

Limps being in the tree makes this a bigger solve than the note's 300-iteration smoke test suggests, which is another reason the unverified solve-time and determinism questions get answered here with numbers before anything is planned around them.

What replaces what is deliberately not decided here, because nothing is replaced: the bot still reads the 36-spot chart when this phase closes.

One instruction matters more than it looks.
The extractor must dump the entire solved tree rather than the subset today's vocabulary can express.
Four-bet nodes are present in the solve and unreachable through a v1 spot key, and an extractor that filters to what fits today is the single thing that would force a re-extraction after phase 12.

Closes nothing on its own.
It is the input every chart phase after it reads.

### 11. Engine And Query Fidelity

Commits no data. Could auto-advance. Touches the Phase 01, 02, 03, and 06 contracts.

Five correctness gaps, all found by v1's own reviews and none fixable inside the phase that found them.

The engine treats a fold as illegal when checking is free, so any real history containing an open fold does not replay at all (`FOLD-WHEN-FREE`).
That blocks ingesting anyone's actual hands.
`StrategyQuery.street_bet` has two readings and one consumer uses the wrong one, so replayed hands reach the chart with a mis-derived stack depth and refuse for the wrong reason (`STREET-BET-MEANING-AMBIGUOUS`).
The decision audit's all-in ceiling is too loose by exactly the price to call (`DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE`).
The postflop fallback's fail-closed branch can invest and can refuse postflop, both of which its own contract says never happen (`FALLBACK-FAIL-CLOSED-CAN-CALL`).
Betting is not reopened when consecutive short all-ins amount to a full raise (`UNDER-RAISE-ACCUMULATION`).

Ahead of every measurement, because everything downstream replays through the engine and reads the query.
A phase that fixes measurement bugs after the measurements are taken is a phase that invalidates them.

### 12. Spot Vocabulary V2

Re-derives the committed artifact. Would not auto-advance.

Two changes to what a spot key can say.

Raise sizes enter the key, so a 2.25bb open and a 2.5bb open stop sharing a spot (`RAISE-SIZE-IN-SPOT-KEY`).
Today every agreement rate in the repo is computed across prices the chart cannot distinguish, which is why the Phase 08 finding had to be qualified.
And a position may act twice, which is what four-bets and beyond need (`SECOND-ORBIT-PREFLOP-SPOTS`).
Real hands reach that edge 19 times in 3,048 decisions and the inventory can only file them as no expressible spot (`CORPUS-INEXPRESSIBLE-SPOTS`).

The proof it broke nothing is already built.
The committed GTO Wizard export must re-derive into the new format through `scripts/convert_preflop_export.py --check`, carrying the same ranges under new keys, and the real-hand refusal inventory must lose its catch-all row.

### 13. Table-State Fidelity

Commits no data. Could auto-advance. Touches the Phase 03 and 04 contracts.

What the query can carry, as against what the chart can express.
Per-seat committed chips make three currently-approximated things exact at once: a straddle, an ante, and an asymmetric effective stack (`PER-SEAT-CONTRIBUTIONS-IN-QUERY`, `BLIND-STRUCTURE-VARIANTS`, `ASYMMETRIC-EFFECTIVE-STACKS`).
This matters more than it sounds for the home games this bot targets.
A straddled pot currently reads as an ordinary one, so the bot confidently answers a question nobody asked.

Separate from phase 12 rather than merged with it because 12 changes the artifact format and this changes the runtime query.
The loop's freeze-then-build discipline works better on one axis at a time.

### 14. Chart Cutover

Commits a chart. Would not auto-advance.

Derive the artifact from the export committed at phase 10, at the v2 vocabulary, and retire the 36-spot chart.
Smaller than it would otherwise be, because the solve and the human verdict on it already happened.
What is left is the conversion, the sizing table, and the one decision held back from phase 10: that a new six-handed 100bb artifact replaces the GTO Wizard one rather than sitting beside it, since `PreflopChartLibrary` rejects duplicate spot keys.

The v1 spot vocabulary can express 1,691 six-handed 100bb spots, 848 of them without limps, against the 36 committed today.
Both counts are recomputable by enumerating `solver_artifacts.schema.spot_key` over action sequences.
At 7.1 KB per spot, the limps-included ruling puts this at 1,691 spots and roughly 12 MB rather than the 848 and 6 MB a no-limp solve would have cost.
That is the price of closing the limped-pot refusals, and it is worth restating at the contract stage against whatever the phase-10 export actually weighs, since 7.1 KB per spot is measured off the current artifact and not off a GTOpen export.

This phase carries its own closing measurement.
Rerunning the corpus comparison against the new chart either resolves the calling gap or re-diagnoses it as a real defect (`CORPUS-CALL-AGREEMENT-IS-THE-WEAK-SPOT`, `CHART-COVERAGE-EXPANSION`, `CORPUS-INVENTORY-SHOULD-DRIVE-CHART-WORK`).
The rake-free ruling removes one of the two explanations the evidence offered, so what this measurement can attribute is narrower and cleaner than the earlier framing suggested: rake is gone as a variable, and open size is not.

Open size is not gone, and it collides with proposed phase 12 in a way that phase has to settle before this one runs.
Phase 12 puts raise size in the spot key so that a 2.25bb open and a 2.5bb open stop sharing a spot.
The solve is ruled at 2.5bb and the corpus median is 2.25bb.
Taken literally, those two facts mean corpus decisions facing a 2.25bb open would find no matching key at all and arrive as refusals, which would convert the calling gap from a measured disagreement into an empty sample and quietly destroy this phase's closing measurement.
So phase 12 must decide how a size key matches a size that was not solved: a bucket with a stated tolerance, a nearest-price rule, or an explicit refusal.
Any of the three is defensible and the failure mode is choosing none of them and discovering the consequence here.
More depths and table sizes get cheap here in machinery terms, but each one is another solve, so they follow the same phase-10-then-phase-14 shape rather than landing inside this phase.

`STACK-DEPTH-BUCKETS` is narrowed rather than closed: solving more depths means more exact matches, and bucketing stays deferred because it is a heuristic.

### 15. The Drill

Commits session records. Would not auto-advance. First CLI entry point in the repo.

Deal a spot, take the player's action, say what the chart says and what the difference costs, record the session, and turn a run of sessions into a leak report.
Very little of this is new code.
A training session is a hand history, and a leak report is the Phase 08 agreement measurement pointed at one player instead of a corpus.
The bounded-ingestion boundary lift belongs here, so the same report can run over an exported personal history rather than only over hands the drill dealt.

After phase 14 because a drill against a 36-spot chart refuses most of what it deals, and a trainer that says no opinion teaches nothing.
This is the phase that makes the previous five worth having.

Also the natural home for `SAMPLE-HAND-THE-CHARTS-COVER`, `SIMULATOR-DECISION-AUDIT-NOT-COMMITTED`, and `SIMULATOR-REPORT-UNITS-AND-IDS`.

### 16. Postflop That Can Bet

Commits a solution or a rule. Would not auto-advance. Gated on a source that does not exist yet.

The honest one, and bigger than everything above it combined.
A bet needs a size, a size needs a source, and the only sizing source in the repo is a preflop export.
So this phase opens the way Phase 08 did, blocked on an input the repo does not have, and its contract stage is where that source gets chosen rather than assumed (`V2-POSTFLOP-STRATEGY`).

There is a cheap intermediate that needs no new data: call a river bet when equity against the unseen deck beats the price (`POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`).
It is an assumption rather than a fact about the hand, and it would make the bot over-call the way it currently over-folds, so it is worth building only if real opponents bet at it.
That evidence arrives in phase 15, which is another reason the drill comes first.

`POSTFLOP-UNBEATABLE-EARLIER-STREETS` belongs here too, and is a faster evaluator rather than a new rule.

## Carried Forward From V1

Two lessons that cost a phase each to learn.

**Canary the phase's own new command at stage 4.**
Phases 08 and 09 both authored mutation canaries for every command except the one the phase was adding, and both were caught at stage 7 by a gate that would otherwise have been decorative for exactly the behavior the phase existed to add.

**Point stage 8 at the poker, not at the code's fidelity to its contract.**
The findings that changed v1's direction were domain findings: that folding a hand nothing can beat is a certain loss, that a single headline agreement rate mostly measures how easy it is to fold trash, that a raked solve explains a blind-defence gap.
None came from checking whether an implementation matched its contract.

One loose end sits outside the sequence.
`MUTATION-SENTINEL-IS-COMMITTABLE` lets an interrupted mutation run commit a deliberate defect, and it is tooling rather than phase work, so it should land as a maintenance task before the next phase rather than inside one.

## Adopting This

Mechanically: rewrite `docs/ROADMAP.md`, add seven entries to `phase_status.yml` at `future`, create seven contract skeletons under `docs/phase_contracts/`, add seven `verification/loop_policy.yml` entries, and re-tag `backlog.yml` so every deferred item either names the phase that will close it or stays honestly deferred.
That is a maintenance task, since those contract edits are structural rather than semantic.

Then the boundary change in `AGENTS.md`, which is semantic and needs its own `contract-update` before any phase starts.
After the rulings below it is a single line rather than a set: large hand-history ingestion lifts for one player's own hands with a stated bound, and the other five boundaries stay exactly as written.
The bound itself is the open part, and it is a number rather than a question of principle.

## Rulings

Seven questions were open when this document was written, none of them answerable from the repo.
Taylor ruled on all seven on 2026-08-15.
They are recorded here because a decision that lives only in a conversation is a decision the next agent re-opens.

Four are about the solve, and they bind proposed phase 10 rather than the adoption task.

1. **Rake: rake-free.**
   It matches the games this trains for and makes the corpus comparison apples-to-apples, since the committed corpus is rake-free too.
   The cost is that the expectations file describes a raked solve, which is worked through in proposed phase 10 above.
2. **Open size: 2.5bb, as today.**
   Only one variable moves at the chart cutover.
   The measurement-only 2.25bb second solve that was floated alongside this is not adopted, so the corpus median stays 2.25bb against a chart solved at 2.5, and proposed phase 12 has to say how a size key matches a size that was not solved.
3. **Limps: in the solved tree.**
   1,691 expressible spots rather than 848, and roughly 12 MB rather than 6.
   Real hands reached limped spots on 12 inventory rows, and this is what stops those arriving as refusals.
4. **Licence: proceed, and record the gap.**
   GTOpen ships no LICENSE file, and `source.kind` is a provenance claim no checksum can verify.
   The ruling is to commit the ranges anyway with the missing licence stated plainly in the source card, as a known limitation of the artifact rather than an omission.
   It belongs in `docs/CORPUS_COMPARISON_LIMITS.md`'s successor for the chart, alongside the limit that nothing in this repo can check a committed artifact against the tool that produced it, because the gate has no network by design.

Three are boundaries, and they change what `AGENTS.md` should say rather than what any phase does.

5. **Large hand-history ingestion: lifts, bounded.**
   For a single player's own exported history with a stated size bound, not corpus-scale mining.
   The bound is a number nobody has chosen yet, and proposed phase 15 cannot use the lift until both it and the `AGENTS.md` wording exist.
6. **UI package: stays deferred past v2.**
   Revisit once the drill exists and has been used.
7. **PokerNow automation and browser observation: stay out of v2.**

None of these seven adopt the sequence.
`phase_status.yml` still holds ten completed phases and nothing after them, no contract skeleton exists for any phase above, `verification/loop_policy.yml` has no entry for them, and `AGENTS.md` still states all six V1 boundaries in their original form including the one ruling 5 lifts.
That last point is the one a reader is most likely to get wrong: until the `contract-update` lands, the file forbids what ruling 5 permits, and the file wins.
