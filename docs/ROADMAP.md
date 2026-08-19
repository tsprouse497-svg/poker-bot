# Roadmap

## V1

Phases 00 through 09 are complete.
The sequence is locked by `phase_status.yml` and the contracts under `docs/phase_contracts/`, and it is finished rather than paused.

It produced a deterministic engine, a replayer that refuses out-of-order hands, a strategy contract that refuses rather than guesses, a fail-closed chart lookup, a self-play simulator, a public-corpus comparison, and a verification gate that proves itself by breaking on purpose.

## V2

Phases 10 through 16 are declared at `future` in `phase_status.yml`, each with a contract skeleton, an audit packet path, and an entry in `verification/loop_policy.yml`.

| Phase | Title | Depends on | Auto-advance |
|-------|-------|------------|--------------|
| 10 | Solver Extraction, And A Human Verdict On It | 09 | no, commits the export |
| 11 | Engine And Query Fidelity | 09 | yes |
| 12 | Spot Vocabulary V2 | 11 | no, re-derives the artifact |
| 13 | Table-State Fidelity | 11 | yes |
| 14 | Chart Cutover | 10, 12, 13 | no, commits the chart the bot plays |
| 15 | The Drill | 14 | no, commits session records |
| 16 | Postflop That Can Bet | 15 | no, and cannot start until a postflop source exists |

This is a graph rather than a queue, and `scripts/loop_fleet.py` plans from it, so up to three phases can be in flight at once.

```
09 ─┬─ 10 ──────────────┐
    │                   │
    └─ 11 ─┬─ 12 ───────┼── 14 ── 15 ── 16
           └─ 13 ───────┘
```

The two edges the sequence does not have are the point of it.
Phase 10 hangs off 09 rather than off the format work because a solver export is written in the solver's own vocabulary, so capturing one depends on nothing this repo has yet decided.
Phase 11 hangs off 09 because it sits ahead of every measurement: a phase that fixes measurement bugs after the measurements are taken invalidates them.
Phases 12 and 13 then split, one changing what the artifact can express and the other what the runtime query can carry, which the loop's freeze-then-build discipline handles better one axis at a time.
Phase 14 is where they rejoin, because deriving the chart needs the export, the vocabulary, and the query all at once.

`depends_on` in the contracts is the single source for that graph.
`check_repo_consistency` rejects an edge naming a phase that does not exist and any cycle, because both would surface as a fleet reporting nothing eligible and calling it ordinary waiting.

Declared is not specified.
Every contract above carries boilerplate acceptance criteria and placeholder command IDs, which stage 1 of the loop replaces in `contract-update` mode before the phase can go active.

`docs/V2_ROADMAP.md` holds the argument behind the sequence, the eight rulings that settle what to build, and the consequences four of them carry.
`docs/V2_RULING_MITIGATIONS.md` plans those consequences.
Read both before writing any contract above.

Two things are owed before phase 10 starts.
`AGENTS.md` still forbids the large hand-history ingestion that ruling 5 lifts, and the lift needs a bound expressed as a number, which is a `contract-update`.
`MUTATION-SENTINEL-IS-COMMITTABLE` lets an interrupted mutation run commit a deliberate defect; it is tooling rather than phase work, so it should land as a maintenance task rather than inside a phase.

## Deferred beyond v2

- PokerNow automation and browser observation, which ruling 7 keeps out of v2.
- A training UI, which ruling 6 defers until the phase 15 drill exists and has been used.
- Large corpus ingestion beyond one player's own hands.
- Runtime solver calls.
- Stack-depth bucketing, which stays a heuristic no matter how many depths get solved.
- Board abstraction, grouping similar flops so the bot plays them identically (`POSTFLOP-BOARD-ABSTRACTION`). Ruled later rather than never on 2026-08-19. It buys depth, not breadth: all 1,755 canonical flops is affordable, so a flop-only solution needs none of it, while the turn and river cannot exist without it.
