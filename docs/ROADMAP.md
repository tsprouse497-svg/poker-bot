# Roadmap

## V1

Phases 00 through 09 are complete.
The sequence is locked by `phase_status.yml` and the contracts under `docs/phase_contracts/`, and it is finished rather than paused.

It produced a deterministic engine, a replayer that refuses out-of-order hands, a strategy contract that refuses rather than guesses, a fail-closed chart lookup, a self-play simulator, a public-corpus comparison, and a verification gate that proves itself by breaking on purpose.

## V2

Phases 10 through 16 are declared at `future` in `phase_status.yml`, each with a contract skeleton, an audit packet path, and an entry in `verification/loop_policy.yml`.

| Phase | Title | Auto-advance |
|-------|-------|--------------|
| 10 | Solver Extraction, And A Human Verdict On It | no, commits the export |
| 11 | Engine And Query Fidelity | yes |
| 12 | Spot Vocabulary V2 | no, re-derives the artifact |
| 13 | Table-State Fidelity | yes |
| 14 | Chart Cutover | no, commits the chart the bot plays |
| 15 | The Drill | no, commits session records |
| 16 | Postflop That Can Bet | no, and cannot start until a postflop source exists |

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
