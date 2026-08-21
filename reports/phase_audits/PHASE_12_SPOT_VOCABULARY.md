# Phase 12 audit packet: Spot Vocabulary V2

Contract: `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`
Decisions: `reports/phase_audits/decisions/PHASE_12_SPOT_VOCABULARY_DECISIONS.md`
Reviews: `reports/phase_audits/reviews/PHASE_12_SPOT_VOCABULARY/`
Report: `reports/active/latest_spot_vocabulary_report.txt`
Lane: worktree `~/projects/poker-bot-worktrees/phase-12`, branch `phase/12-spot-vocabulary-v2`, opened from `main` at `beec7d6`.

Written for a reviewer who does not read code.

## Summary in plain language

This phase changed what a spot key is allowed to say, and changed nothing about which hands the bot plays.
It committed no new solve and no new chart.
The one data change is the committed artifact re-written under the new keys, carrying exactly the ranges it already carried.

A spot key is the string that names a poker situation.
It is the artifact's index and it is what a person reads in a refusal inventory, so what it can express is the ceiling on what this repo can measure.
Two things it could not say before, it can say now.

**A raise carries the amount it raised to.**
Before, one cell answered every price: a 2.25bb open and a 4bb open were the same spot, so every agreement rate this repo has ever published was computed across prices the chart could not tell apart.
That is why the Phase 08 finding had to be qualified.

**A position may act more than once.**
A four-bet had no key at all, because the old rule rejected any sequence naming a position twice, in as many words.
Real hands reached that edge 19 times in 3,048 decisions, and the refusal inventory could only file them under a catch-all that named no cell anybody could fill.

The honest headline is what did *not* change.
No agreement rate moved.
Under ruling 8 and Taylor's extension of it, a price the solved tree does not hold is normalised back to the one cell the coarse key would have hit anyway, so the bot answers the same question the same way.
What the finer key bought is that the answer now *says* it was answered at a price it was not asked at, on 969 of 2,758 answered decisions.
That measurement was impossible before, because a key that cannot tell two prices apart cannot tell that one was moved.
Making the chart answer those prices differently is a bigger solve, at proposed phase 14.

### One paragraph per backlog entry closed

**`RAISE-SIZE-IN-SPOT-KEY`.**
A raise entry now renders the amount it raised *to* in big blinds after an `@`, quantized to hundredths with trailing zeros stripped.
A call carries no size, because it pays a level the key already states.
Big blinds rather than chips, because chips do not survive a change of blind level; raise-to rather than a multiple of the previous bet, because a multiple depends on what came before it and would key one spot two ways.
A size the renderer cannot represent exactly is rejected rather than rounded into a neighbouring cell, and a v1 key carrying no size fails import rather than being read as matching any size.

**`SECOND-ORBIT-PREFLOP-SPOTS`.**
`spot_key` accepts a position appearing more than once, and the ordering rule generalises from one pass over the preflop action order to repeated passes over the positions still live.
There is no orbit cap.
What bounds the vocabulary is whether the sequence is a legal preflop order and whether its raises can be paid at the stated depth, which is a check the key could not perform at all until it carried sizes.
Expressible six-handed 100bb spots go from 1,949 to 18,773 with limps.

**`CORPUS-INEXPRESSIBLE-SPOTS`.**
The real-hand refusal inventory has no `(no expressible spot)` row any more, and no corpus decision refuses as `lookup:unrepresentable-spot`.
All 19 of those decision points now name a repeated-position key that a chart phase could fill.
The refusal total is unchanged at 290, which is the expected result rather than a disappointing one: this phase added no chart coverage, so those 19 arrive as `lookup:spot-not-covered` instead, which is a better miss because the vocabulary can now name the cell.

**`PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT`.**
Phase 11 corrected the engine and the query every published number in this repo was measured through, and ruled that a fix phase does not grade its own fixes.
This phase re-ran those measurements with the two causes kept apart, and the answer is that Phase 11 moved none of the corpus figures.
That is reported as a checked non-move rather than as silence.

## Pass/fail checklist for a non-coding reviewer

Everything here is checkable from `reports/active/latest_spot_vocabulary_report.txt` and this document.

| # | Claim | Result |
|---|---|---|
| 1 | A raise entry in a key carries its raise-to size in big blinds | PASS - `t6/d100/BTN/CO:raise@2.5`, 36 of 36 mapped keys shown in the report |
| 2 | A call entry carries no size | PASS - `t6/d100/BB/SB:call` unchanged across the re-keying |
| 3 | Two sequences differing only in a raise size derive different keys | PASS - pinned literally by test, both strings |
| 4 | A four-bet has a key, from both sides | PASS - `t6/d100/BTN/LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5` |
| 5 | A sequence needing a seat to act out of turn across an orbit has no key | PASS - asserted by test, and the test was rewritten at stage 7 because the first one passed off a neighbouring rule |
| 6 | A raise nobody can pay at the stated depth is rejected | PASS - a five-bet to 300bb in a 100bb game has no key |
| 7 | Exactly one place in the codebase derives a key | PASS - sweep recorded below, one definition, ten call sites, all importing it |
| 8 | Every producer of the query's preflop history supplies the raise amount | PASS - four producers, listed by file with a verdict each, below |
| 9 | A v1 key with no sizes fails import rather than matching any size | PASS - asserted by test |
| 10 | The committed artifact re-derives from its source at the new vocabulary | PASS - `convert_preflop_export.py --check` reproduces artifact and sizing table |
| 11 | The ranges did not move | PASS - strip the sizes back out and the pre-phase checksum reproduces exactly, both printed below |
| 12 | 36 spots before, 36 after | PASS - each size-stripped prefix admits exactly one solved size |
| 13 | Every size in a key came from the source export's own action label | PASS - provenance stated per size in the report |
| 14 | The inventory has no catch-all row and no unrepresentable-spot refusals | PASS - both counts zero, asserted by test over the committed sample |
| 15 | The refusal total did not fall | PASS - 290 before and after; a drop would have been a finding to explain |
| 16 | No corpus decision refuses for a price the chart does not hold | PASS - stated as zero rather than described as a mechanism |
| 17 | Every substituted answer says so on the answer | PASS - `StrategyDecision` carries the price asked and the price answered; an exact answer carries no such entry |
| 18 | Normalising a price is not finding a nearer spot | PASS - an uncovered table size, depth, or sequence still refuses at every price |
| 19 | The expressible-spot counts are enumerated rather than quoted | PASS - and the roadmap's published pair does not reproduce; see limitations |
| 20 | Every Phase 07 and Phase 08 number is restated with its cause | PASS - three-column table, packet against branch against now |
| 21 | No committed audit packet was edited | PASS - stale figures named where they sit; MAINT-25 was needed first |
| 22 | Both new command IDs are declared, registered, and pass | PASS - `pytest_spot_vocabulary`, `generate_spot_vocabulary_report` |
| 23 | Both new command IDs carry a canary authored before the implementation | PASS - four canaries, all authored at stage 4 |
| 24 | The gate proves it can fail on this phase's own commands | PASS - 43 of 43 commands green, every canary bites |
| 25 | Every judgment call carries a reversibility class and a recorded outcome | PASS - 13 calls, 3 `frozen-into-data`, outcomes below |
| 26 | The four inherited backlog entries are settled | PASS - all four `done`, three of them settled at this stage; see limitations |

## Commands and reports

| Command | What it does |
|---|---|
| `pytest_spot_vocabulary` | 69 tests over two files: what a key can say, and what the repo does once it can say it |
| `generate_spot_vocabulary_report` | Writes the before-and-after keys, the mapping, the counts, the census, and the restatement |

- `reports/active/latest_spot_vocabulary_report.txt` - the report a reviewer reads
- `reports/active/latest_verify.txt` - 43 commands, all pass
- `reports/active/latest_sample_refusal_inventory.txt` - 159 distinct spots, no catch-all row
- `data/artifacts/preflop/six_max_nl25_100bb.json` - the re-keyed artifact
- `data/artifacts/preflop/sizings/six_max_nl25_100bb.json` - the re-keyed sizing table

Regenerated rather than hand-edited, and expected to move: the sample comparison report, both refusal inventories, the preflop chart and strategy reports, and the committed decision audit.

## One spot key before and after, and one that could not be written at all

    raised spot     before   t6/d100/BTN/CO:raise
                    after    t6/d100/BTN/CO:raise@2.5

    four-bet spot   before   (no key exists - the rule rejected a repeated position)
                    after    t6/d100/BTN/LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5

The four-bet key reads: the lojack opened to 2.5, the button three-bet to 8, the lojack four-bet to 21.5, and the button is to act.
Every number is the total that player put in, not the increment.
A player would call `raise@8` over a `raise@2.5` a 3.2x, and the report states that once in those words because the key does not.

The deepest sequence the committed sample actually reached, now expressible:

    t6/d100/CO/HJ:raise@2.5,CO:raise@6.81,HJ:raise@19.93,CO:raise@36.67,HJ:raise@100

## Both checksums, and why a changed one is evidence

Spot ids are inside the weights checksum, so re-keying the artifact had to change it.
That makes the file's own checksum useless as proof the ranges held, and the proof is the third line.

    checksum the file carried before this phase   eaf2c6cc...150482f7
    checksum recomputed under the old keys        eaf2c6cc...150482f7
    checksum the file carries now                 d2d5c3fa...c179ad60

Both are printed in full in the report, and the first two are the same 64 characters.

The middle line is the test that matters: strip every `@size` back out of the committed keys, recompute the weights checksum over the result, and it reproduces the pre-phase value exactly.
So the whole of the change in the file's checksum is accounted for by the spot ids inside it, and none of it by a weight.
A bijection between old and new keys is asserted by test, and the report prints all 36 rows of the mapping so a reviewer can check any one against the source by hand.

## What ruling 8 costs in this sample

Ruling 8 says the solved tree carries one opening price and every other price is answered from it.
Taylor extended it on 2026-08-20 to every raise in the sequence, because exact matching past the open would have refused 72 of the 79 three-bet decisions this chart can answer at all.

    decisions the chart answered                    2758
    answered at the price they were asked at        1789
    answered at a price they were not asked at       969   (35.1%)

      of those, the opener's price was moved         959    <- what ruling 8 itself costs
      of those, a later raise's price was moved       66    <- what extending it costs
      of those, both                                  56    <- why the two lines above overlap

    substituted raises in all                       1025    <- not 969; the 56 carried two each
      answered above the price asked                1010
      answered below the price asked                  15
    substitutions within 0.5bb                       966 of 1025
    substitutions over 3bb                             3 of 1025

The two totals are the thing to read carefully, and the report now labels them.
969 counts *decisions*; 1,025 counts *substituted raises*, because a decision facing several raises can have more than one moved, and 56 did.

Two things a reader should carry away, both first found by the stage-8 domain review.

The substitution is one-directional.
Across all substituted raises, 1,010 of 1,025 were answered **above** the price asked.
Narrowed to the opens, which is what ruling 8 itself governs, 949 of 959 move up and 10 move down.
A smaller open gives the defender a better price, so the correct response to a 2bb open is a wider continue than the correct response to a 2.5bb open, and the chart hands back the tighter one every time.
The abstraction is small in this sample and it is biased.

And the thin tail belongs to this corpus, not to the abstraction.
This sample is Pluribus and a human corpus whose sizes sit near a solve.
The home games this bot is eventually pointed at open to 3bb, 4bb and 5bb routinely, and the same census against that data would move most of its weight into the two rows that currently hold 34 and 3.
The census is the right instrument and it has only been run against the friendly sample.

## Every number restated, with its cause

The packet column is what the phase published.
The branch column is what the committed report said when this lane opened, which already carried Phase 11's corrections.
So packet-to-branch isolates Phase 11 and branch-to-now isolates this phase, and neither is asserted.

| number | packet | branch | now | cause |
|---|---|---|---|---|
| hands compared | 499 | 499 | 499 | unchanged, checked against both |
| preflop decision points | 3048 | 3048 | 3048 | unchanged, checked against both |
| refusals | 290 | 290 | 290 | unchanged, checked against both |
| Pluribus agreement | 439/456 | 439/456 | 439/456 | unchanged, checked against both |
| human agreement | 2155/2302 | 2155/2302 | 2155/2302 | unchanged, checked against both |
| human calls agreeing | 138/227 | 138/227 | 138/227 | unchanged, checked against both |
| human raises agreeing | 385/416 | 385/416 | 385/416 | unchanged, checked against both |
| inventory decisions naming no spot | 19 | 19 | 0 | moved by this phase |

Two changes that look like results and are not.

The self-play profile comparison moved: 128 refused hands became 126, and 472 measured became 474.
`PreflopChartStrategy._seed` hashes the spot key into the seeded draw that collapses a mixed cell, so re-keying re-seeds every mixed decision and the run walks a different path through the same distributions.
No coverage changed.
Filed as `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL`, because phase 14 re-keys again and every self-play figure will move again for the same non-reason, which makes self-play useless as a regression signal across exactly the phases most likely to want one.

The refusal inventory grew from 78 distinct spots to 159.
A spot the chart holds no candidate price for keeps the price it was actually asked at, so one uncovered squeeze at eleven different three-bet sizes is eleven rows now rather than one.
More actionable rather than less, since the rows name the real prices a chart phase would have to solve, but it is a committed report that changed shape.

No committed audit packet was edited.
The Phase 07 and Phase 08 packets are the record of what those phases found and believed.
Making that possible needed MAINT-25 first, because the quality gate's fact-drift check was policing a finished phase's packet against numbers this phase moved, and Taylor ruled on 2026-08-20 that a packet is a snapshot rather than a live document.

## The two sweeps the contract asked for by name

No test can prove a second key derivation does not exist, so the contract asks for the sweep instead.

**One derivation.**
`def spot_key` appears once, in `solver_artifacts/spot_key.py`.
Ten call sites across seven files reach it, and every one imports it rather than reimplementing it: the importer, the lookup twice under the alias `derive_spot_key`, the schema's own re-derivation check, the vocabulary report and its measures, the preflop strategy report, and the converter three times.
Two names that look like a seventh are not: `ChartLookup.spot_key` and `simulator.measure.spot_key` are properties reading a key someone else already derived.
The re-export from `schema.py` is worth watching, because a re-export is how a second derivation would eventually hide, and the stage-6 review says so.

**Four history producers, each supplying the size.**

| Producer | File | Verdict |
|---|---|---|
| Corpus comparison | `data_pipeline/comparison.py:371` | supplies raise amounts from the replayed hand |
| Simulator | `simulator/table.py:167` | supplies them from the engine's own action record |
| Preflop strategy report | `scripts/generate_preflop_strategy_report.py` | supplies them as explicit chip amounts per probe |
| Postflop fallback report | `scripts/generate_postflop_fallback_report.py:684` | supplies them from the constructed preflop history |

That is the set the contract predicted at the branch point, and the sweep found no fifth.

## Judgment calls and what each one changed

Thirteen were recorded before any code, each with a reversibility class.
Taylor ruled on the three `frozen-into-data` items and on decision 5 on 2026-08-20; the other nine proceeded on their recorded defaults and are reported here.

| # | Class | Ruling | What it changed |
|---|---|---|---|
| 1 | frozen | raise-to in big blinds | Survives a blind-level change; costs the reader knowing `@8` is a total, not an increment |
| 2 | frozen | `@` suffix, hundredths, trailing zeros stripped | Legible in an inventory; costs ragged columns and a precision ceiling that rejects rather than rounds |
| 3 | frozen | no size on a call | One derivation stays one derivation; a short all-in call carries no record of being short, which is phase 13 |
| 4 | runtime | no orbit cap, bounded by legality and depth | A real corpus hand already reached five raises, so a two-orbit cap would have been set below existing evidence |
| 5 | runtime, **ruled** | normalise every raise, not only the open | Kept 72 of 79 answerable three-bet decisions in the sample instead of refusing them |
| 6 | runtime | solved prices derived from the loaded keys | A constant was already wrong: the small blind opens to 3.5 and everyone else to 2.5 |
| 7 | runtime | structured detail on the decision | A substituted answer stays distinguishable downstream without parsing a rationale string |
| 8 | runtime | decision-audit schema version to 2 | The payload gained a raise amount and may gain a detail block, so v1 and v2 bytes would otherwise be indistinguishable at an unchanged version |
| 9 | runtime | reject a sizeless raise entry | A format admitting both is one where a lookup can silently match the wrong cell |
| 10 | runtime | publish the measured counts, file the correction | The roadmap keeps its wrong pair until a `contract-update` fixes it, rather than an implementation phase editing a semantic document |
| 11 | runtime | vocabulary only, no four-bet cells | The 19 move to `spot-not-covered` and are not answered; deriving them is phase 14's whole job |
| 12 | runtime | read Phase 04 and 05, amend only a contradiction | Both were read and **both were left alone**; the widened key makes their criteria more true, not false |
| 13 | runtime | stamp the re-derivation date | A file cannot claim to predate the vocabulary it is written in, and `_artifact_sort_key` breaks ties on that field |

## Review findings

Read-only reviews were written at stages 1, 2, 3, 4, 6, 7 and 8 in `reports/phase_audits/reviews/PHASE_12_SPOT_VOCABULARY/`.
Subagent delegation is switched off in this operator's sessions, so `AGENTS.md` step 6 could not be satisfied and step 10's self-review fallback applies.
Every note records that at its head, and delegated reviewers were offered rather than dropped silently.

Blockers found and fixed, none of them an implementation defect:

- **Stage 4.** The number justifying Taylor's ruling was wrong. Exact matching past the open costs 72 of the 79 three-bet decisions the chart can answer, not 185 of 205, because 125 of those 205 already refuse for coverage that no price rule touches. The conclusion is sharper under the correction, not weaker. Also a test that could never fail.
- **Stage 6.** 34 failures and 3 collection errors in the frozen tests of phases 03 to 09, every one a v1-shaped construction or assertion. Stage 4 authored this phase's own tests and none of the migrations the phase forces on earlier ones, which is the identical miss phase 11 made. Repaired in its own task with `tests/` in scope and every builder file out of it, so the pressure ran from the tests to the code. No assertion was weakened.
- **Stage 6.** A frozen phase 12 test counted a population this phase deliberately grows, and was narrowed to its claim rather than having its number moved to fit the measurement.
- **Stage 6.** The quality gate's fact-drift check and the contract's forbidden shortcuts contradicted each other, since both were right and neither could give way from inside the task. Needed Taylor's ruling, then MAINT-25.
- **Stage 6.** The GTOpen source card's stated headroom counts the whole artifact tree, so committing any artifact invalidates a card belonging to a different one. Re-settled by the extractor's own fixed-point rule; the design defect stays filed.
- **Stage 7.** A canary survived, and it was a real finding. `test_a_seat_the_action_already_passed_cannot_act_later` put hero on the button, so the ring walk reached hero before the folded seat and the rejection came from a neighbouring rule. Repaired with a test that puts hero out of the walk's path, checked in both directions. An assertion passing off a rule other than the one it names is invisible at stage 4 by construction, and `check_gate_bite` is the argument for itself stated as a result.

The most useful non-blocking finding is the one-directional substitution, above.

Three stage-8 report findings were fixed after the packet was first written, on Taylor's instruction that the report be legible before the phase is tagged rather than carry the defects as stated limitations.
The census now says which population each table counts, prints the 56 decisions that carried both a moved open and a moved later raise, and totals the distance split so the two figures reconcile on the page.
The reconciliation is also enforced: `_validate_census` fails the gate if the decision splits do not reconcile by inclusion-exclusion, or if either the distance or the direction split disagrees with the substituted-raise total.
The opening-price table now says it aggregates openers whose solved prices differ, and that a row reading `2.5 -> 3.5` is a small-blind open answered from the small-blind cell rather than a solved price that was moved.
And the direction split the domain review asked for is in the report rather than only in a review note: of 1,025 substituted raises, 1,010 were answered above the price asked and 15 below, so the report now states the bias instead of only the distance.

## Known limitations and deferred items

- **`vocabulary_measures.py` now sits at exactly its 500-line cap.** The reconciliation checks took it from 459 to 500, so the next edit to that file forces a split. It has three real seams - the expressible-spot enumeration, the census, and the restatement - so the split is available rather than awkward, but it is a landmine for whoever edits next and was not worth spending this task on. Filed as `VOCABULARY-MEASURES-AT-ITS-LINE-CAP`.
- **The key admits raise sizes no legal preflop action produces.** Nothing checks the minimum raise, so a three-bet to 2.6 over a 2.5 open has a key. Deliberately not fixed: an all-in for less than a full raise is legal, and the key cannot tell an under-raise from a short all-in because it holds one table-wide depth and no per-seat stacks. The same limit makes payability weaker than it looks. Both wait on `ASYMMETRIC-EFFECTIVE-STACKS` at phase 13, and the module docstring's "legal preflop order" is a stronger claim than the check behind it.
- **Nearest is measured in big blinds, and the quantity that decides hero's range is a ratio.** Latent today, because every location in the committed artifact holds exactly one solved price, so the normaliser never chooses. It goes live the moment phase 14 commits a second price at one location. Filed as `NORMALISER-MEASURES-DISTANCE-IN-BIG-BLINDS`.
- **The roadmap's expressible-spot counts do not reproduce.** `docs/V2_ROADMAP.md` states 1,691 and 848 and says both are recomputable by enumerating `spot_key`; doing exactly that gives 1,949 and 977. The ratio survives to within a percent, so it reads as one systematic difference rather than two errors, but no variation tried reproduces the published pair. It matters because the numbers are load-bearing: the 12 MB artifact estimate in `docs/V2_RULING_MITIGATIONS.md` is 1,691 times a measured 7.1 KB, and phase 14 is scoped against both. Filed as `ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE`, `contract-update`.
- **Seven committed documents end with stray write-tool markup.** This contract ends with a literal `</content>` and `</invoke>`, and the decision record, the ExecPlan, four stage review notes and one completed MAINT ExecPlan each end with a stray `</content>`. It renders as text to every reader and nothing in the gate looks for it. Filed as `DOCS-CARRY-STRAY-WRITE-TOOL-CLOSING-TAGS`.
- **Three of the four inherited backlog entries were still `deferred` at stage 9.** `d83405b` closed `CORPUS-INEXPRESSIBLE-SPOTS` during the build and missed the phase's three headline deliverables. Settled at this stage. This is the second consecutive phase to do it - `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` records phase 11 leaving all six of its own items deferred through tag and merge - and the check that entry asks for would not have caught this one either, because it fires on a completed phase and phase 12 was still active. The gap is the closeout rule, not the check.
- **Two lanes can file one defect twice.** Both worktrees hold `backlog.yml` in standing scope, neither sees the other's filings until the merge, and no check compares them. Filed as `TWO-LANES-CAN-FILE-ONE-DEFECT-TWICE`.

## One number a reader can recompute by hand

**The number: the committed tree carries two opening prices, not one.**

Open `data/artifacts/preflop/sizings/six_max_nl25_100bb.json` and read the five entries whose key ends in `/rfi`.
Four of them - LJ, HJ, CO, BTN - read 2.5, and `t6/d100/SB/rfi` reads 3.5.
No code required.

It settles a question the roadmap left open.
A single constant for "the solved opening price" would already be wrong today rather than only after some future solve, which is why decision 6 derives the normaliser's candidate prices from the keys the loaded artifacts declare instead of from a number in code.

The same file holds ten distinct raise-to sizes in all, and every one is a whole tenth of a big blind: 2.5, 3.5, 8, 10.5, 11, 13.5, 21.5, 22, 23, 28.5.
Those ten are the entire price vocabulary the committed chart can answer at, which is the plainest available statement of what phase 14 has to widen.
