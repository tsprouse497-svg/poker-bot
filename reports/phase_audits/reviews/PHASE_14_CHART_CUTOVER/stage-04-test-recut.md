# Phase 14 stage 4: the tests re-cut onto the 86

Written 2026-08-26, in implementation mode, against the contract and decision record committed at
`da05adf`. The loop driver reports stage 4's checks as passing and it is wrong to trust that here:
it verifies only that the tests are red for a missing module or a failed assertion, not that they
describe the specification in force. They did not. Decision 1 was superseded twice after these
files were authored and the tests knew neither change.

Nothing here was advanced. `--advance` is not run, and three blockers below are for Taylor.

## What the tests asserted and must not have

| assertion | ruled state |
|---|---|
| `REACH_FLOOR_BP == 200`, and reach as the selection rule | retired; the predicate needs no threshold |
| a 5,626-spot census | 86 |
| one exclusion code, `DERIVATION_BELOW_REACH_FLOOR` | two codes, and they partition the excluded |
| a per-spot reach floor asserted over the artifact | the two-clause predicate, re-derived from the keys |
| all five opening ranges committed | one, the small blind's |
| every spot facing a single open committed | only the big blind's five |
| the source card records **two** solves and restamped checksums | decision 2 ships as solved; no re-solve is run |
| a traced cell at node `(1,2,1)`, two opponents invested | a committed node: the big blind facing a button open |
| a two-node synthetic export for the perturbation test | six nodes, because four seats must fold first |

The re-solve row is the one the brief did not name and it matters as much as the rest. Decision 2 was
re-ruled to `ship-as-solved` on 2026-08-24 and the contract says in terms that the phase runs no
re-solve. Three tests required one: two solve records on the source card, a changed
`export_sha256`, and a changed `saved_solve.sha256`. They are inverted, so a silent re-solve is now
loud - one solve, 300 iterations, and both checksums pinned to the file phase 10 captured.

## Every number verified by its own walk before it was frozen

Written fresh against `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz` and the
committed 499-hand sample. Nothing below is quoted from `stage-04-eighty-six-coverage.md`; all of it
reproduces it.

| claim | measured |
|---|---|
| export action nodes | 38,828, all deriving distinct legal keys, zero collisions |
| history clause alone | 110 |
| subtree clause alone | 5,472 |
| the conjunction | **86** |
| history but not clean - the 24 | 24, by seat 1 LJ / 3 HJ / 5 CO / 7 BTN / 8 SB / 0 BB |
| the 86 by seat | 15 LJ / 14 HJ / 13 CO / 12 BTN / 12 SB / 20 BB |
| by prior actions | 1 at four, 10 at five, 30 at six, 30 at seven, 15 at eight |
| by prior aggressive actions | 1 / 10 / 30 / 30 / 15 |
| action menus | 50 fold-call, 20 fold-call-raise-jam, 15 fold-call-jam, 1 fold-raise-jam |
| named raise **and** jam / jam only | 21 / 15 |
| at full reach | 11, and they are exactly the spots where hero has not yet acted |
| minimum arriving reach | 261.8 bp, so all 86 clear the retired 200 bp floor |
| corpus preflop decision points | 3,048 over 499 hands, cross-checked against `replay_hand` |
| answered by the 86 | **563**, 18.5 percent |
| answered by the 110 / by the 24 | 2,795 / 2,232 |
| by opponents already invested | 1,629 none, 1,166 one, 243 two, 10 three or more |
| retired chart | 36 spots, 36 pass the history clause, **22** pass the ruled predicate |
| retired spots refused after the cutover | **14**, named individually and all fourteen reproduced |
| retired spots still covered | **21**; the twenty-second is `t6/d100/BB/SB:call`, which passes the predicate and has no node because the solve is `limp: false` |

The census split is new, and it is what decision 8's second code needs. The two buckets partition
the 38,742 excluded nodes exactly: **33,356** fail the subtree clause, so a multiway terminal is
still reachable and the source misprices them; **5,386** pass it and fail the history clause, so
they are priced exactly from here on and were reached through a cold call. 33,356 + 5,386 + 86 =
38,828. The 24 sit inside the first bucket, which is the ruled precedence and the whole point of it:
they are outside the rule *because* the source misprices them, and the second code is what a later
phase reads to find them by name.

Codes named, since the decision record left the naming open:
`derivation:source-misprices-multiway`, `derivation:outside-selection-rule`, and
`derivation:no-legal-spot-key` unchanged at zero. `DERIVATION_BELOW_REACH_FLOOR` is asserted **gone**
- a code nothing files is a reader being told a selection rule that is not the one in force.

## The canaries

`derivation-reach-floor-drops-to-a-tenth` is replaced by
`derivation-predicate-drops-its-subtree-clause`, which is the canary the contract asks for: it
widens the predicate to admit a multiway node, and it does it in the sharpest available direction by
dropping the clause the 2026-08-25 supersession added. The mutated walk keeps 110 nodes and admits
the 24 - four opening ranges among them. Every one converts, imports, keys legally and answers; the
defect is entirely in the ranges, so nothing but the walk-versus-artifact comparison sees it.
`a-jam-only-spot-goes-back-to-having-no-size` keeps its aim and loses its stale count: 15 committed
spots rather than 4,257 export nodes. The other six are unchanged and still bite.

## Blockers

### 1. Decision 10's aggregate gate does not pass over the 86, so it is not frozen

The contract requires it "re-measured over the 86 before it is frozen" and says "the phase halts
rather than ship a gate it has not seen pass". Measured, at decision 10's own one-point tolerance,
as the number of committed spots violating the group order:

| partition | spots violating |
|---|---|
| pairs, 13 single ranks | 51 |
| pairs, 4 bands (aces down to jacks, tens to eights, sevens to fives, fours to deuces) | 17 |
| pairs, 3 bands | 10 |
| pairs, 2 bands (aces down to eights, sevens to deuces) | **1** |
| suited row over the row below | 41 |

No partition is clean. The single two-band violation is
`t6/d100/LJ/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5,SB:raise@100` - the lojack facing a 100bb
five-bet - playing aces down to eights at 83.13 percent and sevens down to deuces at 86.87, a 3.75-point gap at 3.14 percent
arriving reach. The suited-row half fails much harder and for the reason decision 10 was re-ruled on
in the first place: at `t6/d100/BB/HJ:raise@2.5,BB:raise@7.5,HJ:raise@22.5` the big blind plays 87s
at 99.44 percent and 98s at 1.23, a 98-point gap between two hands the solver is indifferent
between. That is a split, not a leak, and a gate over it rejects correct play.

**Not chosen: the two-band partition.** Decision 10 ruled "each pair band and each suited row"
without fixing the bands, and picking the partition that reads smallest is choosing a threshold to
go green - the move the contract forbids for the selection rule and no more honest here.

What the tests freeze instead is the half of the ruling that measured true. Decision 10 wanted the
aggregate to keep a real check on a transposed hand index or a mis-assigned actor, and over the
5,626 it failed at exactly that: the suited-versus-offsuit aggregate flagged 2,007 nodes as solved
against 818 transposed, rewarding the defect it existed to catch. Over the 86 the discrimination
runs the right way for every partition:

| partition | solved | transposed |
|---|---|---|
| pairs, 13 single ranks | 51 | 77 |
| pairs, 4 bands | 17 | 77 |
| pairs, 3 bands | 10 | 77 |
| pairs, 2 bands | 1 | 77 |
| suited rows | 41 | 70 |

One measurement detail is load-bearing and was got wrong once on the way here. The transposed
reading must take the cell's **weights and its reach** from the swapped class, because a converter
indexing the payload by the grid ordering reads both with the same index. Taking only the weights
compares a full range against a sparse one and measures the sparsity: done that way the suited-row
form gives 41 solved against **30** transposed and prefers the transposed mapping, which is the same
pathology in a new place.

**The question for Taylor:** decision 10's group form is a proposal that has now failed measurement
twice, over two different committed sets. Does the gate become the transposition discrimination
above - which passes, catches what the item was ruled to catch, and asserts no group order the solve
does not owe - or does something else gate? The tests as written freeze the discrimination and gate
no group order. That is a change to a `frozen-into-data` item's content and is his call, not
stage 4's.

### 2. The multi-size sizing table the contract requires is in no test

Decision 6, extended 2026-08-24 and restated 2026-08-25: "**the sizing table holds every raise size
a spot offers, with the weight hero gives each**", which is how
`CHART-CANNOT-EXPRESS-TWO-RAISE-SIZES-AT-ONE-SPOT` closes. The stage-4 tests never encoded it. They
specify `sizing_payload["raise_to_bb"]` as one float per spot, and this re-cut left that shape
alone rather than inventing a schema for it - so the counts moved onto the 86 and the shape did not.

Freezing it as it stands means stage 6 builds a one-price table, 21 committed spots that offer a
named raise **and** a jam carry one of the two, and the backlog entry closes on a schema that cannot
express what it was closed for.

Specifying it properly needs a ruling that does not exist: a spot offering two prices with mixed
weights has to be answered at the table somehow, and "pick the bigger", "pick the more frequent" and
"refuse the price and give the action" are three different bots. The repo's own precedent - the
`lookup-tie-picks-an-action` canary - says a mixed cell refuses rather than choosing, and the V1
boundary forbids heuristic guessing, so refusal is the likely answer; but it is a `frozen-into-data`
choice about what the bot does, and `PreflopSizingTable.amount_bb` is the runtime API it lands on.
**Recommend a short `contract-update` or an amendment to decision 6 naming the runtime rule, then a
second stage-4 pass on the three files, before the freeze.**

### 3. The migrated frozen tests of completed phases were cut against the 5,626 and are stale twice over

The contract's regression expectation is explicit: every frozen test of a completed phase that
asserts against the chart's contents is migrated "at stage 4 and before the freeze", because phases
11 and 12 each deferred it and each paid a separate repair task. Stage 4 migrated thirteen files on
2026-08-24, before either supersession, so they describe a chart with 5,626 spots. Under the 86 the
bot opens from one seat and faces a single open from one seat, and these assert otherwise:

- `tests/test_full_table_preflop.py` - `test_every_position_that_can_open_has_an_opening_spot`
  enumerates all five openers; `test_every_spot_facing_a_single_open_is_covered` enumerates every
  hero-behind-opener pair, of which only the big blind's five survive; and roughly twenty-five
  decision tests open from the lojack or the button through `strategy.decide(query("LJ", ...))`,
  every one of which is now a refusal. Line 602 pins `t6/d100/BTN/rfi` as a mixed-cell subject.
  Its helpers are fine: `open_to` reads the big blind's arriving prices and `three_bet_spot` names
  `LJ/LJ:raise@2.5,CO:raise@7.5`, both committed.
- `tests/test_preflop_committed_charts.py` - `LJ_OPEN` and `BTN_OPEN` constants,
  `measured_aggregates` reading an opening frequency for all five seats out of the committed
  library, `test_the_lojack_opens_to_the_size_the_solution_used`, and the `TestSourceFrequencies`
  orderings measured over the chart rather than the export.
- `tests/test_table_state_strategy.py` - several lojack and hijack queries; most already assert a
  refusal for another reason and will now refuse for a different one, which is a code change rather
  than an outcome change and still has to be read one by one.
- `tests/test_simulator.py`, `tests/test_sample_comparison.py` - not audited in this pass. Both
  consume the chart at the level the cutover moves, and the self-play figures are expected to move
  by the contract's own regression note.
- Clean on inspection: `tests/test_spot_vocabulary.py`, `tests/test_spot_vocabulary_downstream.py`,
  `tests/test_preflop_lookup.py`, `tests/test_preflop_artifacts.py`, `tests/test_strategy_contract.py`
  and `tests/test_engine_fidelity.py`. Their uncommitted keys are grammar fixtures and synthetic
  libraries, not claims about what the committed chart covers.

This is a second full lane of work rather than an edit, which is why it is reported rather than
attempted here: the brief scoped this pass to the phase's own three files.

## Alignment items

- **The contract says both 22 and 21 about the retired chart's survivors**, in different sections.
  Both are true - 22 pass the predicate, 21 have a node - and read together they look like a
  contradiction. Worth one sentence in the next `contract-update`; nothing rests on it.
- **`test_the_committed_chart_reproduces_from_the_committed_export` is green before the
  implementation exists**, because the old converter reproduces the old artifact. It is the
  `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` family from the other side: a test that will be
  right at stage 6 and proves nothing now.
- **The committed converter rewrites the external expectations file** with byte-identical content
  and a new mtime, which `test_the_converter_does_not_write_the_expectations_file` catches by
  comparing `st_mtime_ns`. Not a defect in the test; stage 6 owes the fix.

---

## Ruled by Taylor, 2026-08-26: a spot offering two prices seeds the price

Blocker 2 above left the runtime half of decision 6 unruled, and round 1 of the migration proceeded
on a fail-closed default. The independent integration reviewer showed that default is refuted by the
data rather than merely conservative: `t6/d100/SB/rfi` is the only opening range the chart holds and
it offers two prices, so failing closed on a multi-price spot stops the bot opening a hand at all,
from any seat. The question went back with the measurement.

**The ruling: the strategy chooses among a spot's prices with the same deterministic seed it already
uses to choose among a mixed cell's action weights.** `PreflopChartStrategy` has that mechanism; no
second one is introduced. At the small blind's open the bot raises to 2.5 on essentially every hand
and jams 100bb about once in ninety-seven thousand, which is what the solve plays. Rejected: failing
closed, which stops the bot opening; and taking the highest-weight price, which is the heuristic pick
`lookup-tie-picks-an-action` forbids for actions, has no answer at a tie, and would commit a jam
branch to the artifact that the bot never plays.

The measurement the ruling was made on, re-derived rather than quoted: 21 of the 86 committed spots
offer both a named raise and a jam, 15 offer a jam alone, 1 offers a raise and a jam with no call
(the small blind's open), and 50 offer hero no raise at all. The four smallest second-price shares
of hero's aggressive volume are `SB/rfi` at 1.0317e-05, `LJ/LJ:raise@2.5,SB:raise@7.5` at
2.8919e-05, `BB/SB:raise@2.5` at 3.4810e-05 and `HJ/HJ:raise@2.5,SB:raise@7.5` at 2.4950e-04. The
band that isolates the small blind's open is therefore (1.03e-05, 2.89e-05), which is why no epsilon
rule survives: any round threshold a human would reach for strips three or four spots as well.

**What this owes elsewhere.** Decision 6 is `frozen-into-data` and its record does not carry this
half. Implementation mode may not edit the decision record, so the ruling is recorded here and
decision 6 owes an amendment at the next `contract-update` transcribing it, with the measurement
above. Until that lands this note is the only place it is written down.

---

## Ruled by Taylor, 2026-08-26: the transposition discrimination is the gate

Blocker 1 above measured decision 10's group aggregate over the 86 and no partition passed, so the
contract's own instruction was to halt rather than freeze a gate nobody had seen pass. The question
went to Taylor with all five partitions and the two candidate substitutes.

**The ruling: what gates is that the measure prefers the solved hand index to the transposed one.**
Over the committed set the group measure must flag strictly fewer spots under GTOpen's own class
ordering than under the grid ordering, on every partition. Measured, at decision 10's ruled
one-point tolerance: 51 against 77, 17 against 77, 10 against 77, 1 against 77, and 41 against 70.
No group ORDER is gated at all.

That is the half of decision 10 that survived measurement, and it is the half the item was ruled
for. Its own re-ruling said the aggregate existed "to keep a real check - a transposed hand index or
a mis-assigned actor still failing it - without asserting a per-cell order the solve does not owe".
Over the 5,626 it failed at exactly that, scoring the transposed mapping as the better one; over the
86 it discriminates the right way on every reading. Rejected: gating the two-band pair aggregate
with its one violation named, because two bands is the partition that reads smallest of the five and
choosing it is picking a threshold to go green; and gating nothing, which would leave the transposed
index caught only by the reach-against-export comparison.

One measurement detail is load-bearing and was got wrong once on the way to this ruling. The
transposed reading must take a cell's **weights and its reach** from the swapped class, because a
converter indexing the payload by the grid ordering reads both with the same index. Taking only the
weights compares a full range against a sparse one and measures the sparsity: done that way the
suited-row form gives 41 solved against 30 transposed and prefers the transposed mapping, which is
the same pathology in a new place.

The tests already freeze this, in `test_the_group_dominance_measure_prefers_the_solved_hand_index_to_
the_transposed_one`, so the ruling confirms what stage 4 wrote rather than changing it. The per-cell
measurement stays published and gates nothing, unchanged.

**What this owes elsewhere.** Decision 10 is `frozen-into-data` and the contract still requires the
group ORDER in terms - "the combo-weighted play frequency of each pair band and each suited row is at
least that of the band or row below". That sentence is now superseded and the contract cannot be
edited in implementation mode, so decision 10 and the contract's dominance criterion both owe an
amendment at the next `contract-update`, carrying the five-partition measurement above.

---

## Ruled by Taylor, 2026-08-26: the price weights are per hand class

The 2026-08-26 seeded-price ruling settled *how* the strategy chooses among a spot's prices. It did
not settle what it is choosing from, and decision 6's entry is one weight per price per **spot**.
The independent round-3 reviewer measured what that costs and it is not a rounding matter.

At `t6/d100/BB/BTN:raise@2.5` - the big blind closing against a button open, export node
`(0,0,0,1,0)`, every class at full reach - the jam's share of hero's aggressive volume, per class,
reproduced here by an independent walk rather than quoted:

| class | raise to 7.5 | jam 100 | jam share of aggression |
|---|---|---|---|
| AA | 1.0000 | 0.0000 | 0.0000 |
| KK | 0.9975 | 0.0025 | 0.0025 |
| TT | - | - | 0.0480 |
| JJ | 0.3687 | 0.6313 | 0.6313 |
| AKo | 0.3359 | 0.6641 | 0.6641 |
| 65s | 0.0377 | 0.2715 | 0.8781 |
| 44 | 0.0203 | 0.1553 | 0.8844 |

The spot aggregate is **0.0761**. Over the 53 classes carrying more than one percent of hero's
aggressive volume the per-class share runs from 0.000 to 0.884. So a per-spot draw jams 100bb with
aces about once in every thirteen times it three-bets them, where the solve never jams them at all,
and three-bets 44 to 7.5 more than nine times in ten where the solve stacks off nearly nine times in
ten. That is not a mispriced cell, it is a different strategy - and it is legible poker being
destroyed: the solve three-bets small with the hands that want action and jams the hands that do not
want to play a three-bet pot out of position.

It is also not recoverable later. `schema.PREFLOP_ACTIONS` is `fold, check, call, raise` and has no
jam, so the conversion collapses the jam into the raise weight and the per-class split survives
nowhere else in the artifact.

**The ruling: the sizing entry carries a weight per price per hand class.** Rejected: keeping the
per-spot aggregate and recording the cost; and committing only the named raise, which would leave
the 15 jam-only spots with no aggressive price at all and teach a 7.5 three-bet where the solve
stacks off.

The shape every file must now agree on, replacing the per-spot shape recorded above:

    "schema_version": 2,
    "raise_to_bb": {
      "t6/d100/BB/BTN:raise@2.5": {
        "AA": [{"to_bb": 7.5,  "weight": 1.0}],
        "44": [{"to_bb": 7.5,  "weight": 0.1156},
               {"to_bb": 100.0, "weight": 0.8844}]
      }
    }

- entries ordered by `to_bb` ascending; a class's weights sum to 1.0 over its own aggressive volume
- a class with no aggressive weight at a spot carries no entry, and neither does a spot with none;
  50 of the 86 offer hero no raise at all
- `PreflopSizingTable.sizes_bb(spot_key, hand_class)` returns that class's prices with weights, or
  None
- `amount_bb(spot_key, hand_class)` stays the single-price convenience and returns None where the
  class offers more than one; the strategy draws from `sizes_bb` with the mixed-cell seed instead
- the bytes are free: 36 of the 86 spots carry any price at all, and the artifact is two orders of
  magnitude under the 20 MiB cap

**What this owes elsewhere.** Decision 6 is `frozen-into-data` and its record carries the per-spot
entry, so decision 6 owes this amendment at the next `contract-update` along with the seeded-price
half. Until that lands this note is the only place either is written down.

---

## What stage 6 owes in `src/` and `scripts/`, which no test could write

Found by the migration's own integration reviews and spot-checked here at the exact lines quoted.
None of it is a test defect and none of it was reachable from stage 4's scope, so it is recorded
rather than fixed. **Four gate commands of COMPLETED phases crash once stage 6 rebuilds the
artifact**, which the contract's regression expectations forbid: "previously completed phase gates
remain verifiable".

### The four broken commands

- **`generate_preflop_strategy_report`, phase 05.** `scripts/generate_preflop_strategy_report.py:345`
  pins `spot = "t6/d100/BTN/rfi"` and reads `artifact.weights_for(spot, "A2o")`, which returns None
  for an undeclared spot and raises on the join. `:57` `SAMPLE_SPOTS` names `t6/d100/LJ/rfi`,
  `t6/d100/BTN/rfi` and `t6/d100/LJ/LJ:raise@2.5,CO:raise@8`, all retired; `:265` and `:283` loop
  all five `/rfi` keys and would publish four false 0.00 percent rows; `:348` names the deleted
  `data/artifacts/preflop/six_max_nl25_100bb.json`. No test in the tree covers any of it.
- **`run_full_quality_gate`, phase 09.** `scripts/repo_facts.py:163` formats
  `amount_bb('t6/d100/LJ/rfi')`, which is None twice over after the cutover - the spot is retired,
  and under decision 6's schema `amount_bb` returns None at any multi-price spot anyway, which the
  one surviving opening range is.
- **`generate_spot_vocabulary_report`, phase 12.** Three separate failures.
  `solver_artifacts/vocabulary_report.py:43` names the retired `t6/d100/BTN/CO:raise@2.5` as its
  worked example. `:90` requires the v1-to-v2 key mapping to be a bijection, and the 86 keys strip
  to 51 distinct v1 keys with 35 collisions. `:97` compares against `V1_WEIGHTS_SHA256`
  (`vocabulary_measures.py:55`), pinned to the GTO Wizard weights and unreproducible from a
  rake-free solve. `:372` reads `sizing.raise_to_bb.values()` as floats.
- **`generate_sample_comparison_report`, phase 08.**
  `data_pipeline/comparison.py:84` `OPEN_SIZE_SPOTS` names the retired `t6/d100/LJ/rfi`, and `:490`
  filters on a size coming back, so `solved_open_bb` empties; `comparison_report.py:160` then reads
  `.get("LJ")` and formats None.

### The rest, by file

- `solver_artifacts/chart_derivation.py` is new, and `verification/mutations.yml` requires the line
  `    return invested_opponents(by_path, node) <= 1 and live_players(by_path, node) <= 2` verbatim,
  which fixes both helper names. It must **not** carry `REACH_FLOOR_BP`.
- `scripts/generate_derived_chart_report.py` is new.
- `solver_artifacts/lookup.py` gains `DERIVATION_SOURCE_MISPRICES_MULTIWAY`,
  `DERIVATION_OUTSIDE_SELECTION_RULE`, `DERIVATION_NO_LEGAL_SPOT_KEY` and
  `DERIVATION_INEXPRESSIBILITY_CODES`, and loses `DERIVATION_BELOW_REACH_FLOOR`.
- `solver_artifacts/schema.py` gains `BlindStructure`, `PreflopArtifact.blind_structure`,
  `.arriving_reach_bp` and `.reach_bp_for`, and must accept the two new artifact fields.
- `strategy/preflop_sizing.py` goes to `SCHEMA_VERSION = 2` at the per-class shape ruled above, with
  `sizes_bb(spot_key, hand_class)` and `amount_bb` returning None where a class offers two prices.
- `strategy/preflop_chart.py` currently refuses when `amount_bb` is None; it must draw the price
  from `sizes_bb` with the seed the mixed-cell collapse already uses.
- `scripts/convert_preflop_export.py` must stop rewriting the external expectations file, which it
  does today with identical content and a new mtime.
- `data/artifacts/preflop/six_max_nl25_100bb.json` and its sizing table are deleted.

`vocabulary_report.py`'s `_re_derivation_lines` is the one that needs a judgment rather than an edit:
the v1-to-v2 re-keying it checks was a phase 12 fact about a chart derived from the GTO Wizard
source, and nothing in a rake-free 86-spot chart can reproduce it. Retiring the section with its
premise is the honest reading, and it is phase 12's contract to say so, not this one's.

---

## The migration's five rounds, and what the freeze does not cover

Five orchestrated rounds re-cut the tests onto the ruled predicate and then hardened them, each
lane read by an independent reviewer that was told to refute it. This section is the honest half of
that record: what was closed, and what was left with the implementation that would slip past it.

Rounds 1 and 2 moved the claims - the phase's own three files, then the thirteen frozen files of
completed phases, which had been cut against the retired 5,626-node reach floor and described a
chart with five opening ranges. Rounds 3, 4 and 5 hardened them, and every round found the same
class of defect: an assertion that would pass for an implementation that does nothing. Ten across
the tree by the end, including a determinism test comparing an empty tuple against an empty tuple,
a report claim proved by an unrelated section of the report, and a chart-versus-chart comparison
that said the implementation equals itself.

### Closed after round 5

The four blockers the final integration raised are fixed here rather than in a sixth round:

- The last per-spot sizing fixture, in `tests/test_table_state_strategy.py`, which specified a
  payload no `PreflopSizingTable` could satisfy alongside `tests/test_full_table_preflop.py`.
- `tests/test_simulator.py` could not tell the ruled chart from an empty one. Reproduced by masking
  the library to three charts and rerunning the floor seating: under the 86 the composite refuses
  24 hands and counts 12, and under both the 86-without-the-small-blind's-open and a chart holding
  nothing it refuses 30 and counts 6. The pair is now pinned, which is the assertion that says the
  one surviving opening range survived. `chips_per_hand` reads 50.0 under all three and is
  deliberately not pinned beside them.
- The rake claim in `tests/test_sample_comparison_report.py` was pinned to one sentence's wording,
  so the same false caveat rephrased passed. It now rejects any "rake"/"raked" in the preamble that
  is not part of "rake-free".
- Four frozen figures were wrong, three of them from a brief this coordinator wrote: the jam's
  share of aggression at the small blind's open is 1.0317e-05 rather than 5.58e-06 (that being its
  weight, not its share); 118 of its classes carry the open alone and 45 carry nothing, not 163
  and 6; and 278 cells sit at or above 0.99 raise weight of which 117 are at exactly 1.0, not
  "117 and 278 more".

### Known weaknesses, filed rather than fixed

Each of these is real. None is worth a sixth round, and each is recorded with what it would let
through.

- **`tests/test_spot_vocabulary_downstream.py`'s second-orbit sum is a Counter identity.** The
  inventory and the rows are built from the same predicate and partitioned by the same key test, so
  the sum equals the row count for any chart and any converter. What actually confines the residue
  is the `MISS_SPOT_NOT_COVERED` filter beside it. **Slips past:** an inventory and a row set that
  disagree about the second-orbit population.
- **Four tests assert reproducibility by running `convert_preflop_export.py --check`**, and all
  four are green before stage 6 and after. **Slips past:** any converter whose defect also produced
  the committed artifact. This is a property of comparing an output against itself, not of these
  tests, and no cheap fix exists inside `tests/`.
- **The seeded price draw is pinned at one spot and one class.** 44 at `t6/d100/BB/BTN:raise@2.5`
  splits 12/88, which is the only place in the chart where eight draws separate a seed from a
  random pick. **Slips past:** an implementation that seeds correctly there and picks by rule
  everywhere else.
- **Several `> 0` bounds survive** where the number is knowable - the substituted-decision census,
  the standard-error positivity, the strategy version. **Slips past:** a constant.
- **Five pinned counts are solve output rather than tree shape** - 117, 531, 1,688, 4,893 and the
  7,112 declared cells. Decision 2 ships as solved so nothing moves them, but the contract still
  permits a re-solve at the ruled config, and a re-solve moves all five while leaving the 86, the
  menus and the price ladder untouched.
- **`tests/test_spot_vocabulary_downstream.py` pins the restatement row the cutover does not move**
  (3,048 preflop decision points, "unchanged") and not the one it does (refusals, 290).
  **Slips past:** a stage-6 report that updates the census and leaves the restatement publishing
  290 as unchanged.

### One more thing stage 6 owes, which no test will tell it

`src/poker_training_bot/table_state/measures.py` pins `CORPUS_REFUSALS = 290`, and
`table_state/checks.py` raises unless the measured count **equals** it. `generate_table_state_report`
is phase 13's required gate command and phase 13 is `completed`, so it is in the derived gate. The
contract requires the refusal rate to **rise**, and phase 14's own frozen tests assert it does. Run
against an 86-key chart the command exits 1. `tests/test_table_state.py` pins no refusal count and
was never migrated, so nothing in `tests/` records this. Stage 6 re-measures `CORPUS_REFUSALS` over
the 86, and re-checks `CORPUS_CAPPED_DECISIONS` in the same walk.

Two readings a stage 6 builder needs, moved here out of a frozen docstring: forced money is an ante
when every seat carries the same unexplained amount measured against `committed_total`, so preflop
it is a uniform gap between that and `street_bet`, and money that is not uniform and that neither
straddle signal claims is the residual `preflop-chart:blind-structure-not-representable` keeps. A
refusal naming a seat uses `_miss_detail`'s vocabulary: `seat`, and `stack_depth_bb`.

### A mutation leaked into the working tree twice, and only ruff saw it the first time

Twice during the migration a canary from `verification/mutations.yml` was left applied in the
working tree: once in `src/poker_training_bot/strategy/preflop_chart.py` after a round-5 lane ran
the suite, and once in `src/poker_training_bot/strategy/contract.py` after this coordinator ran two
pytest invocations concurrently. Both are restored and `verification/.mutation_in_progress` is
deleted.

`check_scope.py` does catch it - it names the sentinel file, says which canary is live and which
source file to restore, and exits 1 - which is the check working exactly as designed. What is worth
recording is that the first leak was found by `ruff` noticing an unused local, because the scope
check had been run before the leak rather than after. The operational rule that falls out: run
`check_scope.py` **after** any command that may apply a mutation, and never run two mutating test
invocations at once. The second leak was self-inflicted by doing precisely that.

A leaked mutation is not merely untidy here. It is a source file quietly holding a deliberate
defect, so a test run against it measures the wrong program, and a commit taken in that state ships
the canary. The sentinel exists to make that loud, and it did.
