# Phase 04 Audit Packet: Preflop Artifact/Chart Contract, Importer, And Fail-Closed Lookup

## Plain-Language Summary

Phase 04 gives the bot a place to keep preflop charts and a strict way to read
them. Nothing in it decides how to play a hand yet; Phase 05 does that.

Four pieces landed.

The poker core now names positions. `poker_core/positions.py` derives the
position labels from the occupied seats, the button, and the table size, for
every table from heads-up to nine-handed, and it is the only place in the repo
that spells them. Six-handed reads `LJ`, `HJ`, `CO`, `BTN`, `SB`, `BB`.

A chart spot has one canonical name. One function turns table size, stack depth,
hero's position, and the action in front of hero into a spot key such as
`t6/d100/BB/CO:raise`. The importer stamps artifacts with it and the lookup
rebuilds it from game state, so a spot that imports is a spot a query can reach.
Only calls and raises are recorded in a spot: a position that folded adds nothing
beyond its absence, an empty sequence means the pot was folded to hero, and a
preflop check cannot precede hero's decision because it ends the round. The key
must also describe a situation where hero is genuinely the player to act, so a
string that merely parses (`t6/d100/CO/BTN:raise`, where the button acts after
the cutoff) is rejected.

Import is strict. An artifact is either fully valid or rejected with a specific
reason code: nineteen codes cover unreadable files, bad JSON, duplicate JSON
keys, unknown or missing fields at any nesting level, an unsupported schema
version, a position vocabulary that does not match the declared table size, a
spot key that does not match its derived value, duplicate spots, weights for a
spot that does not exist, unknown hand classes or actions, negative or
non-numeric weights, weights that do not sum to one, audit counts that disagree
with the file, and a checksum that does not match the weights it claims to
cover. Nothing partially loaded is ever returned.

Lookup fails closed. A query for an uncovered table size, stack depth, position,
spot, or hand class comes back as an explicit miss carrying a reason code. There
is no default action, no nearest spot, no nearest stack depth, and no
interpolation. Two charts declaring the same spot refuse to load together rather
than one silently winning.

One real chart is committed: `data/artifacts/preflop/six_max_100bb_core.json`,
hand-authored reference ranges for a six-handed 100bb game covering a cutoff
open, a button open, and the big blind defending a cutoff open. It says
`hand-authored` in its own source field, and
`scripts/build_preflop_chart_artifact.py` holds the range spec it was built from
so the ranges can be read as poker rather than as JSON.

## Non-Coding Reviewer Checklist

| Check | Result | Evidence |
| --- | --- | --- |
| Required Phase 04 tests pass | PASS | `pytest_preflop_artifacts` (238 tests: 100 positions/hand classes, 83 schema/importer, 30 lookup, 25 committed chart) |
| Chart coverage report exists | PASS | `reports/active/latest_preflop_chart_report.txt` |
| Strategy query report still fresh | PASS | `reports/active/latest_strategy_query_report.txt` |
| Committed artifact imports cleanly | PASS | `Import: accepted` for `t6/d100/reference-6-max-100bb-core`, plus `tests/test_preflop_committed_charts.py` importing the real file |
| Uncovered queries fail closed | PASS | Five probe lines in the report return `miss -> lookup:...` codes and no action |
| Reports and artifact are deterministic | PASS | Builder and report generator re-run under three `PYTHONHASHSEED` values produced byte-identical files |
| Committed artifact matches its range spec | PASS | `test_committed_file_matches_its_builder` rebuilds the JSON from `scripts/build_preflop_chart_artifact.py` and compares |
| Full derived gate passes | PASS | `reports/active/latest_verify.txt` (22 commands) |
| Scope stayed inside the Phase 04 list | PASS | `check_scope` against base commit `5d12eb0` |
| Forbidden V1 scope avoided | PASS | No solver calls, no LLM decisions, no browser automation, no UI, no playing strategy |
| Delegation performed | PASS | Three worker subagent lanes recorded in the ExecPlan |
| Independent read-only review completed | PASS | Two reviewers, findings recorded below |

## Human Spot-Check Guide

Open `reports/active/latest_preflop_chart_report.txt` next to
`data/artifacts/preflop/six_max_100bb_core.json`. No code reading required.

- The report says `Artifacts imported: 1` and lists three spot keys:
  `t6/d100/CO/rfi` (cutoff opens), `t6/d100/BTN/rfi` (button opens), and
  `t6/d100/BB/CO:raise` (big blind facing a cutoff open).
- The report prints `Import: accepted` and the weights checksum. Search the JSON
  for `weights_sha256` and confirm it is the same string. If someone edits a
  weight in the JSON without rebuilding, the import fails, the report says
  `Import rejected` with a reason code, and the gate goes red.
- In the JSON, find `"t6/d100/CO/rfi"` then `"AA"`: it should read
  `{"raise": 1.0}`. Find `"72o"` in the same spot: it should read
  `{"fold": 1.0}`. That matches the first two probe lines in the report.
- The last five probe lines are misses. Confirm none of them names an action.
  A nine-handed table, a 40bb game, a position that does not exist six-handed,
  a cutoff facing a lojack open, and a big blind facing a four-bet all get a
  reason code instead of a guess. That is the intended answer.
- The range spec in `scripts/build_preflop_chart_artifact.py` reads as poker
  shorthand: the cutoff opens 25.5% of hands, the button 45.1%, and the big
  blind continues against a cutoff open with 45.7% (7.1% three-betting, 38.6%
  calling). The cutoff range is a strict subset of the button range, which is
  what a later position should look like.

## Command Evidence

- `pytest_preflop_artifacts`: pass (`tests/test_preflop_positions.py`,
  `tests/test_preflop_artifacts.py`, `tests/test_preflop_lookup.py`,
  `tests/test_preflop_committed_charts.py`)
- `generate_preflop_chart_report`: pass, writes
  `reports/active/latest_preflop_chart_report.txt`
- `generate_strategy_query_report`: pass, Phase 03 reports remain fresh
- Full derived gate: `reports/active/latest_verify.txt`,
  `reports/active/verify_results.json`

## Known Limitations

- Coverage is deliberately thin: one chart, three spots. Broad coverage is
  Phase 05 work, and this phase only had to prove import and lookup.
- Every hand in the committed chart takes one pure action. Mixed frequencies are
  representable in the format (weights are floats summing to one) but the first
  chart does not use them, so it is a labeled reference chart, not GTO output.
  One consequence: `ChartHit.best_action` never returns `None` against the
  committed chart, so the mixed-strategy branch is exercised only by tests.
- `ChartHit.best_action` uses no epsilon, so a solver export carrying a `1e-9`
  weight would read as mixed and abstain. It fails in the safe direction.
- The weights checksum covers the weights only, not `source` or `generated_at`.
  Relabeling a hand-authored chart as a solver export is a review question, not
  something the importer can catch.
- Stack depth must match exactly. A 40bb spot at a 100bb-only library is a miss.
- Spot keys carry no raise sizes, so a small open and a large open share a spot.
- Spots needing a position to act twice (hero facing a 4bet or later) have no
  representation and always miss. Limped pots, squeeze spots, blind-versus-blind,
  cold four-bet-or-fold, and the opener facing a three-bet are all representable.
- Stack depth is one table-wide number and there is no blind-structure field, so
  asymmetric effective stacks, antes, and straddles cannot be expressed.
- Nothing consumes the lookup yet. The strategy contract is untouched by this
  phase.

## Deferred Items

New backlog entries: `SECOND-ORBIT-PREFLOP-SPOTS`, `STACK-DEPTH-BUCKETS`,
`ASYMMETRIC-EFFECTIVE-STACKS`, `BLIND-STRUCTURE-VARIANTS`, and
`RAISE-SIZE-IN-SPOT-KEY`. Existing V2 and engine items are unchanged.

## Independent Review

Two read-only review subagents inspected the full Phase 04 diff, one on
fail-closed correctness and one on poker domain correctness. Between them they
raised eleven findings and one blocker. Everything real was fixed before the gate
commit; the coordinator implemented the fixes because they cut across all three
worker lanes at once.

Fixed after review:

1. Real, both reviewers: `spot_key` accepted spot keys that no real preflop
   situation can produce. `t6/d100/CO/BTN:raise` (the button acts after the
   cutoff), `t6/d100/CO/CO:raise` (hero acted last and is somehow to act),
   `t6/d100/CO/CO:raise,BB:call` (the round is closed), and `t6/d100/BB/rfi`
   (folded to the big blind ends the hand) all imported cleanly and were counted
   as covered while no query built from game state could reach them. `spot_key`
   now requires hero to be the player to act, with the rule stated and tested:
   an unacted hero can only face earlier positions, an acted hero needs a later
   raise, and the last position cannot have a folded-to-hero spot.
2. Real: `check` was allowed in a recorded action sequence, but preflop only the
   big blind can check and its check ends the round, so a check can never precede
   hero's decision. `SEQUENCE_ACTIONS` is now `call` and `raise` only.
3. Real: an artifact declaring zero spots imported cleanly and then registered
   its table size and stack depth as covered, downgrading a
   `lookup:no-artifact-for-table-size` miss into `lookup:spot-not-covered`.
   Rejected now with `artifact:invalid-value`.
4. Real: the contract requires the committed artifact to be exercised by tests
   and nothing did. Every test built payloads in `tmp_path`, and the builder
   script was not gated, so the range spec and the committed JSON could drift
   with the gate green. `tests/test_preflop_committed_charts.py` now imports the
   real directory, asserts known chart entries, and rebuilds the JSON from the
   range spec to prove they match.
5. Real: a query naming a position that does not exist at the table inside its
   action sequence returned `lookup:unrepresentable-spot` with a misleading
   explanation. It now returns `lookup:position-not-at-table`.
6. Real: the chart report's `Checksum verified: yes` line was a tautology,
   because import had already validated the checksum and would have raised. The
   report now says `Import: accepted` with the recomputed checksum, and a
   rejected directory writes an `Import rejected` report with the reason code and
   exits non-zero instead of only raising.
7. Real: the docs, the backlog reason, and the report's own probe all claimed
   that facing a raise after limping is unrepresentable. It is representable
   (`t6/d100/SB/SB:call,BB:raise`), and the probe that "proved" the fail-closed
   path used a sequence that cannot occur at a poker table rather than one that
   is merely unsupported. The rule is now stated accurately (a position cannot
   act twice, so a 4bet or later has no key) and the probe is a real four-bet
   spot.
8. Real, poker quality (raised as a blocker): the big blind folded 76% against a
   23.98% cutoff open while closing the action at roughly 27% pot odds, where
   reference defense is 45% or more. Every suited hand below `K8s` and a long
   offsuit tail were folded, and `AQo` was a pure call. The defense range is now
   38.6% call plus 7.1% three-bet, with `AQo`, `AJs`, `ATs`, `KJs`, `A3s`, and
   `A2s` moved into the three-bet. The cutoff range traded its offsuit tail for
   the suited hands it was missing (`K8s-K5s`, `Q8s`, `J8s`, `T7s`, `97s`, `86s`,
   `75s`, `54s`), and the button widened from 41.5% to 45.1%. The cutoff range
   remains a strict subset of the button range.
9. Real, unrecorded gaps: a table-wide `stack_depth_bb` cannot express an
   asymmetric effective stack, and the format has no blind-structure field, so a
   straddled or anted pot reads as an ordinary one. Both are now backlog items
   (`ASYMMETRIC-EFFECTIVE-STACKS`, `BLIND-STRUCTURE-VARIANTS`).

Accepted without change, recorded in Known Limitations: `best_action` has no
epsilon (it abstains, which is the safe direction); the weights checksum does not
cover `source`; several schema branches are unreachable through the importer
because the importer normalizes ordering first (harmless defense in depth for
direct construction); and the heads-up `BTN`/`BB` labeling leaves no label for
"the seat posting the small blind heads-up", which was judged clearer than
inventing a second name for one seat.

Verified sound by the reviewers: no code path returns an action the artifact did
not declare (a 138,720-query fuzz produced 12 hits, all on declared spots with
weights byte-equal to the JSON); no default, nearest-spot, nearest-depth, or
interpolation path exists; the 169 hand classes are a strict partition of all
1326 two-card combinations, order- and suit-canonical; `seat_positions` agrees
with `order.blind_seats` for every table size and button seat including
non-contiguous seat numbers; preflop action order matches
`order.TurnState.start_preflop`; import is total, with duplicate JSON keys caught
at every nesting level and nothing partial ever returned; and generators are
byte-identical across `PYTHONHASHSEED` values.

## Gate Verdict

PASS. Phase 04 satisfies the contract: full derived gate green (22 commands, 349
tests) after nine review-driven fixes, with the committed chart imported by tests
rather than only by a script, and reports fresh and deterministic.
