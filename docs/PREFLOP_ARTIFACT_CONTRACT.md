# Preflop Artifact Contract

Preflop strategy is artifact-backed and imported offline.
Runtime consumption is deterministic.
Missing chart spots must abstain or fail closed in v1.
Heuristic guessing for missing coverage is forbidden.

The machine source of truth is `src/poker_training_bot/solver_artifacts/schema.py`.
This document explains the format for a reader who is not reading the code.

## Required artifact fields

- `artifact_schema_version`
- `source`
- `generated_at`
- `table_size`
- `stack_depth_bb`
- `positions`
- `spots`
- `action_weights`
- `audit_fields`

Import is strict about keys at every level.
An unknown field anywhere in the file is a rejection, not something to ignore, so a chart cannot smuggle in meaning the importer does not understand.

## Positions

Position names come from `poker_core.positions`, which is the only place in the repo that spells them.
The vocabulary is `UTG`, `UTG1`, `UTG2`, `LJ`, `HJ`, `CO`, `BTN`, `SB`, `BB`.
Non-blind seats fill from the button backwards and the under-the-gun run is added as the table grows, so a six-handed table is `LJ`, `HJ`, `CO`, `BTN`, `SB`, `BB` in preflop action order.
Heads-up is `BTN`, `BB`, because the button posts the small blind.

An artifact's `positions` must equal the full table for its declared `table_size`, in that order.
A chart covering only two spots still declares the whole table, so it cannot quietly redefine the vocabulary.

## Spots and the spot key

A spot is one preflop decision: hero's position plus the action in front of hero.
`spot_id` is derived, never hand-written.
One function, `schema.spot_key`, maps table size, stack depth, hero position, and the action sequence to the key, and both the importer and the lookup call it.
That is what makes a spot that imports reachable from real game state.

The format is `t{table_size}/d{stack_depth_bb}/{hero_position}/{tail}`, where the tail is `rfi` for an empty sequence and otherwise `POSITION:action` entries joined with commas.

- `t6/d100/CO/rfi` is a six-handed 100bb cutoff open.
- `t6/d100/BB/CO:raise` is the big blind facing a cutoff open.

Only calls and raises appear in a sequence.
A named position that folded adds no information beyond its absence, and allowing folds would let two different keys mean the same spot.
An empty sequence therefore means the action folded to hero.
A check never appears either: preflop everyone faces the big blind, so the big blind is the only seat that can check, and its check ends the round.

A spot key must describe a situation where hero is genuinely the player to act.
Being well-formed is not enough, so these are all rejected: action from a position that acts after hero when hero has not acted yet (`t6/d100/CO/BTN:raise`), hero acting last in its own sequence (`t6/d100/CO/CO:raise`), hero already acted and facing no later raise (`t6/d100/CO/CO:raise,BB:call`), and folded to the big blind (`t6/d100/BB/rfi`), which ends the hand rather than posing a decision.

V1 allows each position at most one entry, so a spot needing a position to act twice has no key.
In practice that means facing a 4bet or later.
Everything else is representable: opens from every position, facing an open from any earlier position, blind versus blind, limped pots, squeeze spots, cold 4bet-or-fold spots, and the original raiser facing a 3bet (which is how hero appears in its own sequence).
The gap is `SECOND-ORBIT-PREFLOP-SPOTS` in `backlog.yml`, and a lookup for it misses rather than guesses.

Spot keys also carry no raise sizes, so a small open and a large open share a spot (`RAISE-SIZE-IN-SPOT-KEY`).
`stack_depth_bb` is one number for the whole table, so an asymmetric effective stack cannot be expressed (`ASYMMETRIC-EFFECTIVE-STACKS`), and there is no blind-structure field, so an ante or a straddle reads as an ordinary pot (`BLIND-STRUCTURE-VARIANTS`).

## Hand classes and action weights

Hands are the 169 canonical classes: `AA`, `AKs`, `AKo`, high card first.
`solver_artifacts.hand_classes` canonicalizes hole cards to a class regardless of card order or suits.

`action_weights` maps spot key to hand class to action weights.
Action names come from `fold`, `check`, `call`, `raise`: unlike a sequence entry, hero's own action can be a check, because the big blind facing a limp can check.
Weights are non-negative, at least one is positive, and they sum to one within `WEIGHT_SUM_TOLERANCE`.
Ordering of the loaded structure is fixed: spot keys follow `spots`, hand classes follow the 169-class grid order, and actions follow the declared action order.
A stable order is what makes reports and audits byte-comparable.
JSON object order in the file itself is not meaningful, so the importer normalizes it rather than rejecting a differently ordered file.

A spot may cover fewer than 169 classes.
An uncovered class is a lookup miss, never an implied fold.

## Audit fields

`audit_fields` carries evidence a reviewer can recompute:

- `weights_sha256`: sha256 over the canonical serialization of `action_weights`. The importer recomputes it and rejects a mismatch, so an edited chart cannot keep a stale checksum. It covers the weights only, not `source` or `generated_at`, so relabeling a chart's provenance is a review question rather than something the importer can catch.
- `spot_count` and `hand_class_count`: must agree with the file's own contents.
- `notes`: free text, including whether the chart is solver output or hand-authored.

`source.kind` is `solver-export` or `hand-authored`.
Hand-authored ranges must say so.
The committed `data/artifacts/preflop/six_max_100bb_core.json` is hand-authored reference strategy built by `scripts/build_preflop_chart_artifact.py`, which holds the reviewable range spec.

## Lookup

`solver_artifacts.lookup` answers a chart query with a hit or an explicit miss carrying a reason code.
Stack depth must match exactly; there is no bucketing or nearest-depth fallback (`STACK-DEPTH-BUCKETS`).
There is no default action, no nearest spot, and no interpolation.
`reports/active/latest_preflop_chart_report.txt` shows both the coverage and the miss codes.
