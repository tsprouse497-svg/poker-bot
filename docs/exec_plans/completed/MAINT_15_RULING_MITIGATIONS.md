# MAINT-15: Plan The Mitigations For The Three Ruling Consequences

## Objective

MAINT-14 recorded the seven v2 rulings and, in doing so, named three consequences that will damage a later phase if nobody plans for them: the expectations file measures exactly the quantities rake moves, the committed artifact roughly doubles with nothing checking its size, and the solved opening price collides with the played one once raise size enters the spot key.

Naming a consequence without a mitigation is a trap rather than a warning.
A future agent opening proposed phase 10 would find three sentences telling it something is wrong and no analysis of what to do, and would either rediscover the analysis or, worse, engineer around the symptom.

This task writes the mitigation plan.
It does not execute any of it, because every mitigation belongs to a phase that has not been declared.

## Scope

Approved: `docs/V2_RULING_MITIGATIONS.md`, `docs/V2_ROADMAP.md`.

Forbidden here, and each is a real temptation because the mitigation for it is already worked out: `scripts/check_file_sizes.py` (the artifact byte limit), `src/poker_training_bot/solver_artifacts/**` (the artifact split), `data/artifacts/**`, `docs/phase_contracts/**`, `phase_status.yml`, `verification/loop_policy.yml`, `AGENTS.md`.
Knowing what to do is not authorisation to do it, and a mitigation applied outside the phase that owns it is a change nothing measures.

## Delegation Plan

- No-delegation exception: one documentation file, whose content is an analysis produced in this session from evidence already in the repo. There is no implementation lane to bound, and the reasoning is the deliverable rather than a means to it.

## Slices

- [x] Slice 1: the rake mitigation. Establish that all eleven expectations numbers are rake-sensitive, so the split-tolerance approach is unavailable, and set out the parity solve, the ordering assertions, and the directional bound.
- [x] Slice 2: the artifact-size mitigation. Ground the estimate against the measured 7.1 KB per spot, show that no size check covers `data/artifacts/**`, and set out the limped-spot split against the verified library behaviour.
- [x] Slice 3: the opening-price mitigation. Quantify the collision from the Phase 08 evidence, separate the axis the ruling settled from the axis it did not, and rank the four available answers.
- [x] Slice 4: the work that needs no solve and no ruling, and the one question for Taylor.
- [x] Slice 5: a pointer from `docs/V2_ROADMAP.md` at the three places the consequences are named.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

Full gate green.
`docs/V2_RULING_MITIGATIONS.md` plans all three, and `docs/V2_ROADMAP.md` points at it from the top and from each of the three places a consequence is named.

Writing the plan corrected two things the roadmap had asserted a day earlier, which is the argument for having written it.

The rake mitigation the roadmap proposed does not exist.
It said to bound the aggregates rake moves loosely and the ones it does not tightly, but the expectations file holds eleven numbers and every one of them is rake-sensitive, so there is no tight half.
What replaces it is a parity solve at the NL25 basis to grade the extractor on, plus the position orderings and a one-sided direction bound, which are the parts rake genuinely leaves alone.
That also turned up a second reason for the limps ruling, arrived at independently: the file reports a small-blind limp frequency, so the solve it describes had limps.

The price collision has a fourth answer better than the three the roadmap listed, and it is owned by the wrong phase.
`open_raises` is a list, so the facing prices can go in the tree, which dissolves the problem instead of managing it.
And because that list is set before the solver runs, the decision belongs at phase 10's contract stage even though phase 12 implements it.
The roadmap's format-before-data exception for phase 10 rests on the export's vocabulary being independent of the format work, which is true, while the solve's config is not.

Two smaller findings worth keeping.
`data/artifacts/**` is covered by neither `LINE_LIMITS` nor `BYTE_LIMITS`, so a 12 MB artifact would commit today with nothing objecting, and that gap exists now rather than arriving with a future phase.
`PreflopChartLibrary` takes a sequence of artifacts and `from_directory` imports every `*.json` under a directory, so splitting limped spots into their own file needs no code change; that was checked rather than assumed.

## Next Agent Bootstrap

The repo is idle with phases 00 through 09 complete and nothing declared after them.

`docs/V2_ROADMAP.md` proposes seven v2 phases and records Taylor's rulings on all seven of its former open questions.
`docs/V2_RULING_MITIGATIONS.md` plans the mitigations for the three rulings that carry a consequence.
Neither document declares anything.

Four items in the mitigation plan need no solve, no ruling, and no phase, and any of them could be done as a maintenance task tomorrow: measuring the corpus opening-price distribution beyond its median, recomputing the spot counts and bytes per spot, adding a byte limit covering `data/artifacts/**`, and writing the three expectations-file checks down before a solve exists to tune them against.

One question is Taylor's and it is stated at the end of the mitigation plan: whether the solved tree carries more than one facing price.
It is not a re-opening of the 2.5bb ruling, which settled what the bot opens to.
