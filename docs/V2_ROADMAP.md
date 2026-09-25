# V2 Roadmap: The Argument Behind The Phase Graph

`docs/ROADMAP.md` is the short form: the goal, the phase table, the graph, and the warning that the table is hand-typed while the contracts are the source. This file is the reasoning underneath it, the rulings that settle what to build, and the costs each ruling accepts.

**This is no longer a proposal, and the label is worth a sentence because the label is what let the file rot.** It was written on 2026-08-15 as an argument to evaluate rather than a plan to execute, and it kept that framing long after the sequence it proposed was adopted, its contracts declared and five of its phases completed. A document nobody has to be right about stays wrong, and this one did: it described a repo of ten completed phases with no contracts, no policy entries and no human-facing surface, none of which had been true for weeks. It carries the project's direction, so it is the document that most needs to be right.

Every figure below is recomputed from committed data or from a generated report, and each one names where it came from. Nothing here is carried out of older prose.

`docs/V2_RULING_MITIGATIONS.md` planned the consequences of four of the 2026-08-15 rulings and is still worth reading for rulings 2 and 8, but read it with its date in hand: it opens by saying nothing in it has been acted on and no phase has been declared, which stopped being true in August, and its section 1 was withdrawn at phase 10's human gate. Correcting that file is its own task.

## The goal, ruled 2026-09-21

A bot that plays strong no-limit hold'em. The training product comes after, to help a person, and is backlogged until the bot plays well.

That reverses a reason rather than a fact. Several decisions in `reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md` refused a line the solve takes, or accepted a distortion in the committed ranges, on the grounds that a student would be misled or that the cost was pedagogical rather than monetary. Those acceptances stand as shipped; what is retired is the argument for them. Each one is filed in `backlog.yml` to be reopened against a measured number under the new goal, and reopening them is not this document's decision to pre-empt.

Two boundary movements come with the goal and are recorded under **Rulings** below.

## Where the repo actually is

Phases 00 through 14, and 16, are `completed` in `phase_status.yml`.

**The chart the bot plays.** `data/artifacts/preflop/six_max_100bb_rakefree.json` holds 156 spots at six-handed, 100bb, rake-free. The chart it replaced answered 36. Those 156 are what `reports/active/latest_derived_chart_report.txt` reports as committed out of the solve's 30,609 action nodes, and they carry 98.7380 percent of the preflop decisions the bot faces under the solve's own play.

That 98.74 is reach-weighted by the solve, which is a flattering measure, and the same report is explicit that the two readings of coverage are far apart. Weighted by nodes it is 156 of 30,609, because 30,002 of the excluded nodes are the four-bet family: almost all of the tree and a little over one percent of the play. Measured against real hands rather than against the solve's own reach, the chart refuses 194 of 3,048 preflop decision points, spread over 75 distinct spot keys: 6.4 percent refused and 93.6 percent answered. Both numbers are true and they are not the same claim.

**What the refusals are.** Of the 75 rows in `reports/active/latest_sample_refusal_inventory.txt`, 59 are raised pots carrying 142 decision points and 16 are limped pots carrying 52. The limped rows exist because ruling 3 was narrowed after this document was written; see below. The catch-all is gone: `reports/active/latest_spot_vocabulary_report.txt` records 0 rows reading `(no expressible spot)` where the v1 vocabulary filed 19, and those 19 now arrive as an uncovered spot with a name rather than as a refusal naming nothing.

**Where the chart is weak.** `reports/active/latest_sample_comparison_report.txt` puts both populations at 90.0 percent agreement overall, which is mostly a measurement of how easy it is to fold trash. Split by what the player did, folds agree at 97.6 percent for humans and 98.9 for Pluribus, and calls agree at 89 of 232 for humans, 38.4 percent, and 8 of 37 for Pluribus, 21.6 percent. Calling is the weak spot and has been since phase 08. No phase renders a verdict on it any more: phase 17 was that phase and is retired, below.

**Postflop.** There is still no postflop strategy. `reports/active/latest_postflop_fallback_report.txt` describes a continuity device: it checks whenever checking is free, folds to a bet, and puts money in on exactly one path, a board on which no holding a villain could have beats hero whatever card is still to come. That path is open on the turn and the river and closed on the flop, so a flop bet always takes the pot from this bot, and against another copy of itself every postflop street checks through. Phase 16 is the only declared phase that changes this.

**The human-facing surface.** `scripts/ask_preflop_chart.py` asks the committed chart one question from a terminal and prints what it says, including a refusal's own reason code and a shouted label when ruling 8's price abstraction substituted a cell. It never decides. Everything else under `scripts/` is a report generator, a check, or loop and conversion tooling, so the repo has exactly one front door onto the strategy and it is preflop-only.

**What nothing measures.** How well the bot plays. Every number above is agreement with somebody else's decisions or coverage of a decision space, and neither is a win rate. That gap is phase 18.

## Boundaries

`AGENTS.md` holds the boundaries and is the authority on them; the table that used to live here duplicated that file and disagreed with it. Each boundary there states what it forbids and which phase lifts it, and two of them moved on 2026-09-21: table automation and browser observation lift at phase 20 for Taylor's own home games and nothing else, and no heuristic guessing lifts at phase 19. Both are recorded in full under **Rulings**.

Changing a boundary is a semantic change and needs `contract-update`. Nothing before the named phase may anticipate a lift.

## The ordering rule

Format before data, data before product. A chart is expensive to solve and expensive to re-commit, so nothing that changes what a chart file can express may land after the chart does.

There was one deliberate exception and it was the first phase. A solver export is written in the solver's own vocabulary rather than in this repo's spot keys, so capturing one did not depend on the format work at all, and whether an extraction is faithful is a question only a human looking at range grids can answer. So the export and its human verdict led, and only the derived chart waited for the format.

The rule is spent. The format work is done and the chart is committed. What orders the rest is measurement before the thing being measured, and playing before anything built on top of playing.

## The phases ahead

### 16. Postflop That Can Bet

Commits a postflop solution or a rule. Depends on 14, the chart its flop solve is keyed against.

The honest one, and bigger than everything before it combined. It is the phase that makes this a bot that plays rather than a bot that answers a preflop question and runs the hand out.

A committed postflop artifact does not have to be a joint solved tree. A spot is self-contained in its board, both ranges, pot, stacks and sizes, so the artifact can be a library of independent per-street spots keyed the way the preflop chart already is. What does not decouple is ranges: postflop strategy is range against range rather than a function of hero's two cards, so the same hand on the same board plays differently after `LJ open, BTN call` than after `BTN open, BB 3-bet, BTN call`, and the action summary in a spot key is a handle on a pair of ranges rather than history for its own sake.

Ruled flop only on 2026-08-19, over every canonical flop against a small head of common preflop lines, with turn and river refusing the way an uncovered preflop spot refuses today. Flop-only is what dissolves the board-texture question rather than answering it: mapping an unsolved `K72r` onto a solved `Q83r` was the heuristic guessing `AGENTS.md` forbade, and covering all 1,755 canonical flops means never needing the map. Suit isomorphism is exact and GTOpen exploits it internally; rank texture is not.

An earlier draft of this section said no solve in this repo had been timed to a real exploitability target. That is no longer true and the correction is `ROADMAP-CLAIMS-NO-SOLVE-WAS-EVER-TIMED`. `reports/active/latest_postflop_solve_cost.txt` measures 30 solve rows, of which 7 reached their target and are pooled: every pooled row targets 0.3 percent of the starting pot, and the pooled per-unit costs are a median 1.37873 seconds per iteration and a peak resident set between 3,951.1 and 10,864.9 MB. Twenty-three rows are excluded as cap-bound, which is a floor rather than a cost, and the pooled rows are six monotone and one two-tone with rainbow unmeasured at that target, so a rainbow figure taken from that block is scaled rather than measured. The affordability question is now a measured one, which is the point.

There is a cheap intermediate that needs no new data: call a river bet when equity against the unseen deck beats the price (`POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`). It is an assumption about the deck rather than a fact about the hand, and it would make the bot over-call the way it currently over-folds. It once claimed the drill as its evidence, which it never could have had, so it is built on its own argument or not at all.

`POSTFLOP-UNBEATABLE-EARLIER-STREETS` belongs here too, and is a faster evaluator rather than a new rule.

### 18. The Yardstick

Depends on 14.

Nothing in this repo measures how well the bot plays. Every published number is agreement with somebody else's decisions, or coverage of a decision space, and a bot can score well on both while losing money. The other kind of number needs an opponent with a strategy, and this repo does not have one.

It comes before 19 because a merge of solved cells with heuristics can otherwise only be asserted to help.

### 19. Heuristics And Merged Charts

Depends on 16 and 18.

Fail-closed refusal was the right property for a tool that reports on hands already played, where refusing costs nothing and a guessed answer contaminates every measurement downstream. A bot at a table cannot refuse; folding is an action and it is usually the wrong one.

So this phase fills the gaps by merging solved cells with heuristics, with every substitution carried on the decision rather than hidden in the lookup - the discipline `scripts/ask_preflop_chart.py` already applies to ruling 8's price abstraction, generalised. It needs 18 so the merge is shown to help rather than asserted to, and it needs 16 so flop gaps are in scope alongside preflop ones. It is the phase that lifts the heuristic-guessing boundary in `AGENTS.md`, and nothing before it may anticipate that.

### 20. The Home Game

Depends on 16 and 19.

A bot that sits down in Taylor's own home games. Table automation and browser observation lift here, bounded to those games; public real-money tables stay forbidden. The terms-of-service and account-risk reasoning that kept both out of v2 is not answered by the narrowing, because it attaches to the platform and not to who is at the table; Taylor was shown that and accepted the risk knowingly, which is a different thing from the reason having gone away.

Last, because a bot that folds every flop and refuses every uncovered spot should not sit anywhere.

## Retired: 15, The Drill

The drill was a training tool for a human: deal a spot, take the player's action, say what the chart says and what the difference costs, and turn a run of sessions into a leak report. Under the goal ruled on 2026-09-21 it is not what the sequence is for, so it is backlogged rather than built.

Nothing depended on it. Its one outgoing edge, into phase 16, was cut on 2026-09-06 after a review found the edge had never been argued at all: it was a leftover from the straight chain the v2 contracts were first declared as, affirmed once without being traced, and it held the only phase that makes the bot play behind a training tool. `PHASE-16-WAITED-ON-PHASE-15-FOR-A-REASON-THAT-WAS-NOT-A-DEPENDENCY` carries the diagnosis and `A-DEPENDS-ON-EDGE-INHERITED-FROM-A-CHAIN-IS-NEVER-RE-EXAMINED` carries the general repair.

The bounded hand-history lift of ruling 5 was scoped to this phase and now has no owner until a leak report is built on top of a bot that plays.

## Retired: 17, The Corpus Verdict On The Committed Chart

Phase 17 was to re-run the real-hand comparison against the committed chart and say whether the calling gap is rake, price, or a defect in the ranges. Taylor ruled on 2026-09-25 that the bot is judged by how well it plays, which phase 18 measures, and not by how closely it copies real players, so the verdict is not worth a phase. Agreeing with these players more was never playing better, which `docs/CORPUS_COMPARISON_LIMITS.md` argues under "Real players are not an oracle".

Nothing depended on it. The comparison report stays in the gate as a measurement, and no phase reads it as a grade. Where the lane's work is kept and where its seven backlog entries went is `THE-CORPUS-VERDICT-PHASE-IS-RETIRED`.

## Carried forward from v1

Two lessons that cost a phase each to learn.

**Canary the phase's own new command at stage 4.** Phases 08 and 09 both authored mutation canaries for every command except the one the phase was adding, and both were caught at stage 7 by a gate that would otherwise have been decorative for exactly the behaviour the phase existed to add.

**Point the review at the poker, not at the code's fidelity to its contract.** The findings that changed v1's direction were domain findings: that folding a hand nothing can beat is a certain loss, that a single headline agreement rate mostly measures how easy it is to fold trash, that a raked solve explains a blind-defence gap. None came from checking whether an implementation matched its contract.

## Rulings

### The eight of 2026-08-15, and where they stand

Seven questions were open when this document was written and none was answerable from the repo. Taylor ruled on all seven that day, and on an eighth that only became visible once the first seven were written down. They are recorded because a decision that lives only in a conversation is a decision the next agent reopens.

1. **Rake: rake-free.** Stands, and is what the repo committed: the export's source card posts `rake_pct` 0 and `rake_cap` 0. The corpus hands are rake-free too, so the comparison is like for like and rake explains nothing in it.
2. **Open size: 2.5bb.** Stands. Recomputed from the committed chart's own opening ranges rather than stored: `chart_solved_open_bb` in `scripts/repo_facts.py` reads every price the opening ranges offer below the all-in and requires exactly one, and it is 2.5.
3. **Limps: in the solved tree.** Narrowed at phase 10's human gate, and the narrowing is now what the repo does: the posted config in `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json` has `limp` false, so limps left the committed solve entirely. The narrowing was made on a measurement rather than on a preference. The cost is that no spot where an opponent limped can be answered from this export, and that cost is visible: 16 of the 75 real-hand refusal rows are limped pots, carrying 52 of the 194 refused decision points.
4. **Licence: proceed, and record the gap.** Done. GTOpen ships no LICENSE file and the source card says so in its own `licence` field, as a known limitation of the artifact rather than a permission anybody granted.
5. **Large hand-history ingestion: lifts, bounded.** Stands, for a single player's own exported history with a stated size bound and not corpus-scale mining. `AGENTS.md` now states it that way. The bound is still owed as a number, and the lift is not usable until the number exists.
6. **UI package: stays deferred.** Stands as a deferral and its reason has changed. It used to wait on the drill existing and being used; the drill is now backlogged, so it waits on the bot playing well.
7. **PokerNow automation and browser observation: stay out of v2.** **Superseded 2026-09-21 for private home games only.** Both lift at phase 20 and are bounded to Taylor's own home games; public real-money tables stay forbidden. The original reasoning was terms of service and account risk, and narrowing the venue does not address it: a private club on a platform is the same account and the same ban exposure as a public table there. It was put to Taylor in those words on 2026-09-21 and he ruled proceed, risk accepted. Recorded as accepted rather than resolved, so no later reader takes the narrowing for an answer.
8. **Opponent opening sizes abstract to the single solved price.** Stands, and is implemented. The tree carries 2.5bb and nothing else, and an open at any other size is answered from the 2.5 cell, with the substitution carried on the answer rather than hidden.

   The cost is known and accepted rather than overlooked, and it is bigger than the figure this document used to carry. `reports/active/latest_sample_comparison_report.txt` scores 1,156 decisions facing exactly one raise, median and mean size 2.25bb, with only 209 of them at or above the solved 2.5. Split by the price faced, humans calling at or under 2.25bb agree with the chart 39 of 121 times, 32.2 percent, against 14 of 18, 77.8 percent, facing over 2.50bb. Of the 60 big-blind human call disagreements, 46 faced an open cheaper than the solved size. So the bot under-defends against cheap opens, which is most opens, and that is a chosen approximation rather than an open defect.

### The boundary the old table called permanent

**No heuristic guessing for missing chart spots** was ruled here as holding permanently, on the grounds that it is the property that makes every number in this repo mean something. **Superseded 2026-09-21.** It lifts at phase 19. The permanent framing was written for a tool that reports on hands already played, where refusing costs nothing; a bot that has to act at a table cannot refuse, and a fold is not a null answer. Until phase 19 lands it holds exactly as written, and `AGENTS.md` is the authority on that.

**No runtime solver calls** was the other permanent row and is unchanged. Offline extraction into a committed artifact is a different thing and is already how charts are built.

### Spot counts this document used to state

It stated 1,691 expressible six-handed 100bb spots with limps and 848 without, and said both were recomputable by enumerating `solver_artifacts.schema.spot_key` over action sequences. They are not. Phase 12 ran exactly that enumeration and published the measured pair in `reports/active/latest_spot_vocabulary_report.txt`: the v1 single-orbit vocabulary expresses 1,949 spots with limps and 977 without, and the v2 vocabulary, in which positions may repeat, expresses 18,773 and 9,389 to a bound of six recorded actions. The correction is `ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE`.

The artifact-size estimate built on the wrong pair goes with it. The committed chart is 1,616,156 bytes for 156 spots, about 10.1 KB per spot, and `data/artifacts` totals 4,838,105 bytes against the 20 MB directory limit in `scripts/check_file_sizes.py`. A per-spot cost measured on one chart format does not transfer to another, which is what the retired 7.1 KB figure assumed.
