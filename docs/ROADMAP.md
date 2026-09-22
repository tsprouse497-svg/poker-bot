# Roadmap

## The goal

A bot that plays strong no-limit hold'em.

Taylor ruled that on 2026-09-21. Training and coaching tools - a drill, a leak report, a user interface - come after and are backlogged until the bot plays well. The corollary matters more than the goal, because it reverses decisions already made: a line the solve takes is no longer refused on the grounds that a student would be misled by it, and a cost recorded as "pedagogical, not monetary" stops being a cost anybody may wave through.

The bot does not play yet. Since phase 06 every postflop street checks through in self-play, so a hand is decided preflop by the committed chart and then run out to showdown; `reports/active/latest_postflop_fallback_report.txt` says exactly that about itself. Phase 16 is the only declared phase that changes it.

`docs/V2_ROADMAP.md` holds the argument behind the graph below, the rulings that settle what to build, and which of them still stand.

## Done

Phases 00 through 14 are `completed` in `phase_status.yml`.

They produced a deterministic engine, a replayer that refuses out-of-order hands, a strategy contract that refuses rather than guesses, a fail-closed chart lookup, a self-play simulator, a public-corpus comparison, a verification gate that proves itself by breaking on purpose, a solver export with a human verdict on it, and the chart the bot plays today: 156 spots, six-handed, 100bb, rake-free, counted from `data/artifacts/preflop/six_max_100bb_rakefree.json`.

## Ahead

| Phase | Title | Depends on |
|-------|-------|------------|
| 16 | Postflop That Can Bet | 14 |
| 17 | The Corpus Verdict On The Committed Chart | 14 |
| 18 | The Yardstick | 14 |
| 19 | Heuristics And Merged Charts | 16, 18 |
| 20 | The Home Game | 16, 19 |

**This table is hand-typed and the contracts are the source.** `depends_on` in each contract under `docs/phase_contracts/` is the single source for the graph. Nothing compares the two: there is no generator for this table, and `check_repo_consistency` reads only contract frontmatter, so it catches an edge naming a phase that does not exist and a cycle, and nothing else. This file has already drifted from the contracts once, in this exact table, and a reviewer caught it rather than the gate. The gap is `PHASE-GRAPH-IS-WRITTEN-TWICE-AND-CHECKED-ONCE` in `backlog.yml`. When the answer matters, read the contracts.

Which phases may advance unattended is `verification/loop_policy.yml`, and it is deliberately not restated here for the same reason.

```
14 ─┬─ 17
    │
    ├─ 18 ──┐
    │       ├─ 19 ──┐
    └─ 16 ──┴───────┴─ 20
```

This is a graph rather than a queue, and `scripts/loop_fleet.py` plans from it, so several phases can be in flight at once.

## Why the graph has this shape

The ordering rule is format before data, data before product. A chart is expensive to solve and expensive to re-commit, so nothing that changes what a chart file can express may land after the chart does. That rule shaped phases 10 through 14 and is spent now: the format work is done and the chart is committed.

What orders the rest is measurement before the thing being measured, and playing before anything built on top of playing.

16, 17 and 18 all hang off 14 and off nothing else, so they are three independent lanes. Each reads the committed chart and none writes what another reads.

19 needs 16 because a merge of solved cells with heuristics has to cover flops as well as preflop spots, and it needs 18 because a merge can otherwise only be asserted to help. Nothing in this repo measures how well the bot plays; 18 builds that instrument, and until it exists "the heuristics are an improvement" is an opinion.

20 comes last, and needs 16 and 19, because a bot that folds every flop and refuses every uncovered spot should not sit down anywhere.

## Retired

Phase 15, The Drill. It was a training tool for a human, which is no longer what this sequence is for. It was a bare skeleton with no implementation, nothing depended on it, and its one outgoing edge into phase 16 was already cut on 2026-09-06 when it turned out to carry no content. The work is backlogged rather than deleted.

## Declared is not specified

A contract skeleton carries boilerplate acceptance criteria and placeholder command IDs. Stage 1 of the loop replaces them in `contract-update` mode before the phase can go active, and `docs/LOOP.md` describes the stages.

## Deferred beyond the playing bot

- A training interface, and the drill behind it. Deferred until the bot plays well, which is the reason `AGENTS.md` now gives; it used to be deferred until the drill existed, and the drill is now the thing being deferred.
- Table automation and browser observation outside Taylor's own home games. Phase 20 lifts it for those games and for nothing else; public real-money tables stay forbidden.
- Large corpus ingestion beyond one player's own hands. The bounded lift for a single player's own history is still owed a size bound as a number.
- Runtime solver calls.
- Stack-depth bucketing, which stays a heuristic no matter how many depths get solved (`STACK-DEPTH-BUCKETS`).
- Board abstraction, grouping similar flops so the bot plays them identically (`POSTFLOP-BOARD-ABSTRACTION`). Ruled later rather than never on 2026-08-19. It buys depth, not breadth: a flop-only solution covers every canonical flop and so needs none of it. There are 1,755 canonical flops, the count `docs/GTOPEN_SOLVER_NOTES.md` names for GTOpen's own batch reports and the count an enumeration up to suit isomorphism gives. A turn is 49 cards below each of those, or 85,995 spots per preflop line, and a river 48 below each turn, or 4,127,760, and neither can exist without abstraction. Those are counts of spots and not compute costs; the compute ratios stated alongside them elsewhere run the other way round, and that correction is `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`.
