# Phase 13 audit packet: Table-State Fidelity

Contract: `docs/phase_contracts/PHASE_13_TABLE_STATE.md`
Decisions: `reports/phase_audits/decisions/PHASE_13_TABLE_STATE_DECISIONS.md`
Reviews: `reports/phase_audits/reviews/PHASE_13_TABLE_STATE/` (stages 1, 2, 3, 4, 6, 8)
Report: `reports/active/latest_table_state_report.txt`
Lane: worktree `~/projects/poker-bot-worktrees/phase-13`, branch `phase/13-table-state-fidelity`, opened from `main` at `12469b1`. Gate commit `a12bcad`, review commit `781dee9`.

Written for a reviewer who does not read code.

## Summary in plain language

This phase changed what the bot is told about the table, and changed nothing about which
hands it plays where the table is the one the charts were solved for.
It commits no artifact, no chart, and no new sample.

Before this phase the strategy was handed the pot, what each seat held, and hero's price to
call - never what any seat had *put in*, hero's own chips included, so hero's depth was worked
backwards out of the price. That subtraction was exact until Taylor ruled on 2026-08-20 that
the price is capped at what hero can pay, and has been wrong since for every hero whose whole
stack is the price: it hands back the street's bet level instead of the depth.

The query now carries, for every seat at the table, what that seat put in on this street,
what it put in over the hand, whether it has folded, and whether it is all-in.
The pot must equal what those seats put in or the query is rejected outright.
From that the bot recomputes what every seat sat down with, and it refuses a table whose
stack depths or whose forced money the committed charts cannot describe: a live opponent
shorter than hero, a live opponent deeper than hero, a straddle, an ante.

**The honest headline is that this buys no new answers.** Every table it now sees is a table
it now refuses, with a code that says which shape is missing. Making those spots answerable
needs a solve, which is a chart phase. **The second is that the claim does not cover the
whole table.** Two classes still escape and are answered as something else: a straddled pot
with two or more raises in it, and any game whose blinds are not in the chart's own ratio.
Both are measured in the report and filed forward. The second was found by an independent
reviewer at stage 8 and is the largest single finding of the phase.

### One paragraph per backlog entry, and which of the five actually closed

**`PER-SEAT-CONTRIBUTIONS-IN-QUERY`.** `StrategyQuery` carries `seat_states`, one record per
seat in `stacks`, each holding `street_bet`, `committed_total`, `folded` and `all_in` - the
engine's own four names for the same four quantities, so the repo holds one vocabulary
rather than two. A folded seat gets a record like anyone else, because its chips are in the
pot. `pot` is validated against the sum of the hand contributions rather than trusted.

**`STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`.** Every producer now caps `to_call` at hero's
remaining stack, and the query rejects one that does not. It also rejects a query offering
`raise` or `bet` while `to_call` equals hero's whole stack, which is the guard the ruling
was found to be missing: a hero all-in for the call cannot raise, and until now such a query
validated cleanly. The repo's two different all-in ceilings became one, both expressed from
hero's own recorded contribution.

**`ASYMMETRIC-EFFECTIVE-STACKS` - did not close; still `deferred`, now against phase 14.**
Each seat's starting stack is recomputed as what it holds plus what it put in, so a short
opponent and one who has already invested stop being the same picture. The flat-table test
runs in both directions over live seats only: a shallower live seat gets its own refusal code,
a folded seat never makes the table ragged whatever it holds, and the refusal names the
extreme offending seat and the depth it holds, so a tolerance can be set against real data.

**`BLIND-STRUCTURE-VARIANTS` - did not close either; still `deferred`, now against phase 14.**
The arithmetic pot bound that guessed at forced money is deleted and replaced by three exact
signals: what each seat holds against what the declared blinds and its own actions predict, an
unraised pot whose level is not the big blind, and a minimum raise target that disagrees with
the one the blinds and the recorded raises predict. A straddle and an ante get separate codes,
because they change the correct ranges differently. The residual is stated rather than hidden,
and it is larger than the contract expected: see the limitations.

**`STRATEGY-QUERY-STREET-BET-NAME`.** The query's `street_bet` is now `current_bet`, matching
`BettingRoundState.current_bet`, and `street_bet` survives only as the per-seat name it has
always had on the engine. No alias was kept. `DECISION_AUDIT_SCHEMA_VERSION` moved to 3 and
both committed decision-audit files regenerate at that version.

## Pass/fail checklist for a non-coding reviewer

Everything below is checkable from `reports/active/latest_table_state_report.txt`, the other
committed reports named, and this document. Every number was re-measured for this packet
rather than copied from the report.

### What the query now carries, and at what price

| # | Claim | Result |
|---|---|---|
| 1 | The query carries both a street and a hand contribution for every seat | PASS - the report's seat tables have both columns for all six seats |
| 2 | The per-seat names are the engine's own | PASS - `street_bet`, `committed_total`, `folded`, `all_in`, the four `PlayerState` carries |
| 3 | Every seat in `stacks` has a record, folded seats included, and a mismatch is rejected | PASS - `test_table_state.py`, and the report's tables list folded seats with their chips |
| 4 | The pot is validated against the contributions rather than trusted | PASS - three "chips in equal chips out" blocks in the report; canary `the-pot-stops-having-to-reconcile` |
| 5 | Hero's contribution is read, never re-derived by subtraction | PASS - canary `hero-depth-is-derived-by-subtraction-again` fails three commands when reverted |
| 6 | Every producer supplies contributions from what was recorded, not from a reconstruction | PASS - producer sweep below, seven files, eleven sites; one subtraction found in review and removed |
| 7 | Every producer caps `to_call` at hero's stack | PASS - nine pre-phase sites in six files, all corrected; sweep below |
| 8 | A query offering raise or bet while hero is all-in for the call is rejected | PASS - canary `a-capped-hero-may-raise-again` |
| 9 | The two all-in ceilings become one, expressed from hero's contribution | PASS - `_raise_amount` caps at `hero.street_bet + stack`, the audit's own arithmetic |
| 10 | Phase 06's short hero is restated as `to_call == stack` and still enumerated | PASS - the postflop fallback report now reads "the price to call takes hero's whole stack", to call 10 |

### Table shape: asymmetry, straddles and antes

| # | Claim | Result |
|---|---|---|
| 11 | Each seat's starting stack is recomputed as holdings plus contributions | PASS - "sat down with" column in every report table |
| 12 | Both directions refuse, live seats only, and the shallower one gets its own code | PASS - `a-live-seat-is-shorter-than-hero` is new; both appear in the report |
| 13 | A folded seat does not make the table ragged | PASS - the folded 19.5bb probe is answered, not refused; canary `a-folded-seat-makes-the-table-ragged` |
| 14 | The refusal names the seat and its depth | PASS - and it names the *extreme* seat, not the first in seat order; two canaries |
| 15 | The order the checks fire in is ruled and pinned | PASS - hero ragged, then deeper, then shorter; judgment call 7 |
| 16 | A hero short on the street at a flat table still gets an answer; a hero who bought in short does not | PASS - both rows in the report, stated apart |
| 17 | Every corpus table-shape count is zero, reported as a regression proof | PASS - all six codes zero, re-measured for this packet |
| 18 | One committed fixture moves and is the phase's only live evidence | PASS - `phase02-three-way-side-pot`, all three decisions change code |
| 19 | Forced money is found by reconstruction, and an ante is caught even on a folded seat | PASS - the dead-blind and ante census rows |
| 20 | Two further signals cover the straddler who has already acted | PASS - unraised level, and the minimum-raise disagreement |
| 21 | A straddle and an ante get different codes | PASS - `pot-holds-a-straddle` and `pot-holds-an-ante`, both live in the preflop strategy report |
| 22 | The pot bound is deleted only after the replacement covers it | PASS - frozen test plus `validate_bound_coverage` over 10 probes, 5 of which exercise it |
| 23 | The pot the bound admitted is pinned as detected | PASS - the 1,850 pot under a 1,950 bound, refused on a minimum raise of 1,000 against 1,100 |
| 24 | Both still refuse, because the chart's vocabulary is unchanged | PASS - no artifact, chart or key changed |
| 25 | The residual all three signals miss is stated | **PARTIAL** - stated, and larger than the contract anticipated. A straddled pot with two or more raises is answered with the unstraddled range. Filed as `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE` and demonstrated in the report on a table an ordinary betting round produces |

### One name for the bet level, the migration, and the two Phase 12 findings

| # | Claim | Result |
|---|---|---|
| 26 | `street_bet` on the query is renamed to `current_bet` | PASS |
| 27 | The audit schema version moves with the payload | PASS - version 3 in both committed `.jsonl` files, checked |
| 28 | No completed contract is left naming a field that no longer exists | **PARTIAL** - Phase 03 and Phase 06 amended in the two-line form; Phase 11 sits at exactly 300 of 300 lines and cannot take one. Filed as `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP`, and this phase must not tag until that task runs |
| 29 | No producer, consumer, report or committed audit is left on the old name, and no alias kept | PASS - completed audit packets keep their shipped prose and gain a dated pointer, which is a ruling recorded in the ExecPlan |
| 30 | Frozen tests were migrated at stage 4, not repaired at stage 6 | PASS - and it worked: stage 6 ended at 954 green with no separate repair task, unlike phases 11 and 12 |
| 31 | No frozen assertion was weakened to fit | PASS - the five migrated files hold 59, 55, 37, 52 and 31 tests before and after; the 37 split into 26 plus 11 with none lost. The freeze floor moved 709 to 775, exactly this phase's own 66 |
| 32 | The under-raise finding is answered with a number | PASS - 0 of the 1,386 corpus decisions facing a raise carry a raise below the legal minimum; the key change needed is named and filed |
| 33 | The short-all-in call finding is answered with a number | **PARTIAL** - 0 of 178, and the report says plainly that the zero rests on how the converter tags a call rather than on any level. A live query carrying a short all-in call now refuses before a key exists; the key space itself still merges the two |
| 34 | `spot_key`'s "legal preflop order" overclaim is corrected | PASS - docstring corrected, and the same overclaim in the Phase 12 contract is filed as `SPOT-KEY-LEGAL-ORDER-OVERCLAIM-IN-PHASE-12-CONTRACT` rather than silently left |

### Evidence, reports, and gate

| # | Claim | Result |
|---|---|---|
| 35 | The report shows a non-coding reviewer the table state, the depths, the straddled pot, and the corpus counts | PASS - 800 lines, all four sections present |
| 36 | At least one report number is recomputable by hand from a committed file | PASS - the pot of 260; recomputed below |
| 37 | Both command IDs are declared, registered, and pass | PASS - `pytest_table_state`, `generate_table_state_report` |
| 38 | Both carry a canary authored before the implementation | PASS - five authored at stage 4 (54 mutations at the freeze commit), four more added at stages 6 and 8, 58 in all |
| 39 | At least one canary proves the pot reconciliation bites | PASS - `the-pot-stops-having-to-reconcile` |
| 40 | The gate is green and proves it can fail | PASS - 45 of 45 commands, `all_passed: true`, `check_gate_bite` among them |
| 41 | Every judgment call carries a reversibility class and a recorded outcome | PASS - 16 calls, 1 `frozen-into-data`, outcomes below |
| 42 | Every existing refusal code stays reachable | PASS - `blind-structure-not-representable` is kept and narrowed and appears twice in the report; `lookup:no-artifact-for-table-size` still fires twice in the postflop fallback report |
| 43 | The five backlog entries are marked `done` or restated | PASS - three read `done` against phase 13 (`PER-SEAT-CONTRIBUTIONS-IN-QUERY`, `STRATEGY-QUERY-STREET-BET-NAME`, `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`), each carrying its closing evidence and its original text behind `As filed:`; two are restated and moved to phase 14 (`ASYMMETRIC-EFFECTIVE-STACKS`, `BLIND-STRUCTURE-VARIANTS`), because both ask for a format change this phase is scoped out of. Nothing is left `deferred` against phase 13. See limitations for how close this came to being missed |

## Commands and reports

| Command | What it does |
|---|---|
| `pytest_table_state` | 66 tests over two files: 46 on the query's shape and validation, 20 on what the strategy does once it can see the table |
| `generate_table_state_report` | Writes the before-and-after table state, the depth comparison, the straddle census, the corpus counts, and the two residual measurements - and exits non-zero rather than printing if any of them stops holding |

- `reports/active/latest_table_state_report.txt` - the report a reviewer reads
- `reports/active/latest_verify.txt` and `verify_results.json` - 45 commands, all pass
- `reports/active/latest_postflop_fallback_report.txt` - regenerated; `phase02-three-way-side-pot` changes refusal code on all three preflop decisions
- `reports/active/latest_preflop_strategy_report.txt` - regenerated; the straddle and ante probes now refuse under their own codes
- `latest_engine_fidelity_report.txt`, `latest_decision_audit.jsonl`, `latest_postflop_decision_audit.jsonl` - regenerated at schema version 3

The report is self-checking rather than descriptive. It re-derives hero's depth from hero's own
contribution and compares it against the depth the strategy acted on; reconciles the straddle
census against the minimum raise the blinds predict; recomputes which seat a refusal should
name from the seat states rather than asking the rule that chose it; and re-measures both
residuals. Any of those failing exits non-zero and writes nothing.

## One table state, seat by seat

A six-handed 50/100 game, everyone sat down with 10,000 chips. Hero is the lojack and opened
to 250; the hijack and button folded; the cutoff three-bet to 800.

Before this phase the strategy was told: pot 1200, bet level 800, price to call 550, and what
each seat held. Hero's own 250 was not in that list; a seat holding 9,200 was
indistinguishable from a seat that bought in for 9,200.

    seat  position   sat down with put in, street  put in, hand  holds now   status
    0     LJ                 10000            250           250       9750     live
    1     HJ                 10000              0             0      10000   folded
    2     CO                 10000            800           800       9200     live
    3     BTN                10000              0             0      10000   folded
    4     SB                 10000             50            50       9950     live
    5     BB                 10000            100           100       9900     live
    in the pot                                             1200

250 + 800 + 50 + 100 = 1,200, and the pot says 1,200. A query where those two disagree is
rejected. Hero holds 9,750 and put in 250, so hero sat down with 10,000, which is 100 big
blinds - read rather than reconstructed. The cutoff now shows as a 100bb seat that has
invested rather than as a 92bb seat, so the table is flat and the chart answers it.

## The producer sweep, by file

No test can prove no producer was missed, so the contract asks for the sweep. Nine
construction sites across six files existed at the branch point; two capped `to_call` and
seven did not. All nine are corrected, all supply contributions from a record rather than a
reconstruction, and this phase's own report adds a seventh file with three more sites.

| Producer | File | Verdict |
|---|---|---|
| Corpus comparison | `data_pipeline/comparison.py:359` | `PlayerState`'s own four fields; `to_call` capped; pot is the sum |
| Simulator | `simulator/table.py:158` | same, from the engine's live state |
| Preflop strategy report | `scripts/generate_preflop_strategy_report.py:157` | probes rebuilt to carry real forced chips; ante in `committed_total` only |
| Postflop fallback report | `scripts/generate_postflop_fallback_report.py:352, 731` | enumeration's 100 unowned chips attributed to villain's earlier street; replay site caps |
| Strategy query report | `scripts/generate_strategy_query_report.py:75` | from the engine; caps |
| Engine fidelity report | `scripts/generate_engine_fidelity_report.py:145, 252` | literal fixtures, each seat stating its own chips. The third pre-phase site now delegates to the second |
| Table-state report | `scripts/generate_table_state_report.py:137, 280, 868` | new; constructions, labelled as such in the report |

One producer shipped a forbidden reconstruction and the stage-6 mechanical reviewer caught it:
the engine fidelity fixtures derived villain's contribution as the pot minus hero's - the
defect this phase exists to end, inside the phase that ends it. Fixed; the docstring says why.

## The corpus counts, as a checked regression proof

All 499 committed corpus hands are six seats at 10,000 chips, no antes, blinds of exactly 50
and 100. The coordinator re-derived that at stage 6 from the raw PHH bodies in
`data/samples/public_corpus/corpus_hands.jsonl`, not any normalized form, finding one distinct
value for each. So every table-shape count is zero before anything is measured, and a number
that moves here is a defect. Re-measured by walking the corpus independently of the report:

    hands compared                                            499
    preflop decision points                                  3048
    refusals                                                  290   (7 hand-class, 283 spot)
    stack-depth-not-a-whole-big-blind                           0
    table-is-not-one-flat-stack-depth                           0
    a-live-seat-is-shorter-than-hero                            0
    pot-holds-a-straddle                                        0
    pot-holds-an-ante                                           0
    blind-structure-not-representable                           0
    decisions priced at hero's whole stack                     10
      of those, where the bet level differs from hero's start   0
    decisions facing a raise                                 1386
      of those, carrying a raise below the legal minimum        0
    decisions whose history holds a call                      178
      of those, carrying a short all-in call                    0

Agreement did not move: Pluribus 439 of 456, humans 2155 of 2302, unchanged from the Phase 12
packet on the same 499 and 3,048. The 10 capped decisions are the population the ruling is
about, and the corpus cannot exercise the defect at all: every seat starts at exactly 100bb, so
a shove is never for more than hero sat down with, and the report's divergence is a
construction. What none of this establishes, and the ExecPlan says so: that those bytes are the
dataset they claim to come from. `docs/CORPUS_COMPARISON_LIMITS.md` records the Phase 08 gap.

## Decision outcomes

Sixteen judgment calls were recorded with a reversibility class before any code was written.
One, decision 6, was `frozen-into-data` and halted the loop for Taylor, who ruled it on
2026-08-21. The other fifteen proceeded on their recorded defaults and are reported below.

| # | Class | Chosen | What it changed in practice |
|---|---|---|---|
| 1 | runtime | street and hand contributions, per seat | Two fields where preflop needs one, and a preflop invariant no rule enforces |
| 2 | runtime | the engine's own names on the per-seat record | One vocabulary across engine and query; forced decision 4 to ship in the same task |
| 3 | runtime | the pot must equal the sum, exactly | Corrected during the build: an ante is dead money, so the rule is `committed_total >= street_bet` per seat, not equality. A raked hand cannot be expressed as a query at all, filed as `QUERY-CANNOT-EXPRESS-RAKE-OR-DEAD-MONEY` |
| 4 | runtime | `current_bet` | Schema version to 3, both committed audits regenerated, frozen tests in five completed phases migrated |
| 5 | runtime | an explicit folded marker | A producer that mis-sets it over-refuses, which is the safe direction; nothing catches it, filed as `SEAT-STATE-MARKERS-AGREE-WITH-NOTHING` |
| 6 | **frozen, ruled by Taylor** | refuse on any difference at all, no tolerance band | The largest behavioural reach in the phase. It refuses essentially every real table once live state arrives. Its only committed evidence is `phase02-three-way-side-pot`, where all three decisions change code |
| 7 | runtime | hero ragged, then deeper, then shorter | A ragged hero masks every table shape behind it, so the inventory under-counts asymmetric tables in exactly the games where they are commonest. Filed as `DEPTH-CHECK-ORDER-HIDES-THE-SHORT-OPPONENT` |
| 8 | runtime | three signals, all required | Catches the pot the bound admitted. Residual is bigger than this list expected; see limitations |
| 9 | runtime | the 100 unowned chips become villain's earlier street | The postflop fallback report's enumeration pot is now a claim about how the hand got here, and that report says so |
| 10 | runtime | both probes carry real forced chips | The preflop strategy report's two refusal lines now name a straddle and an ante instead of one catch-all |
| 11 | runtime | the audit's ceiling, from hero's contribution | The chart can now return a smaller raise for a hero who has already invested. That is the correct amount and a behaviour change with no corpus evidence, so a fixture carries it |
| 12 | runtime | migrate frozen tests at stage 4 | It worked. Phases 11 and 12 each paid a separate repair task; this stage 6 ended green |
| 13 | runtime | schema version 3 | Verified: every record in both committed audit files reads `"schema_version": 3` |
| 14 | runtime | carry an `all_in` marker | Turns the Phase 12 call handoff from a restatement into a measured work list |
| 15 | runtime | `min_raise_target` is a signal, not validated | Re-examined at stage 8 and left alone. The boundary fix that round landed adds no rule about this field and needs nothing the query lacks postflop, so the two are orthogonal; the stage-8 note records the reasoning rather than implying it |
| 16 | runtime | three new codes, and the old one kept and narrowed | The strategy's own inventory is the eleven `REFUSE_*` codes in `preflop_chart.py`, up from eight; the six `lookup:` codes it re-emits are a separate set. Decision 16's "thirteen" counts neither and no set reproduces it, so this row states what is greppable instead. The kept code is reachable and published, which is what the regression expectation asks for |

## Review findings

Read-only reviews were written at stages 1, 2, 3, 4, 6 and 8. **Subagents were authorized for
this phase (Taylor, 2026-08-21), a change from phases 10, 11 and 12 - all three self-reviewed
at every stage, and the Phase 12 packet names that as its weak link.** Every review here went
to an independent reader who did not write the code.

- **Stage 1, two reviewers, six blockers.** The straddle mechanism the first draft specified
  could not detect the straddle the same draft required, because a straddler who has called
  to the level holds exactly what an ordinary caller holds. Every corpus number the draft
  promised was structurally zero. The pot reconciliation is a tautology at both live
  producers. Refusing on any shallower seat would have refused on folded seats, which is
  wrong poker. All six changed the contract before any test existed.
- **Stage 2, one reviewer, four blockers.** The list had exempted itself from
  `frozen-into-data` on too narrow a reading, so nothing would have stopped for a human on a
  phase whose policy is `auto_advance: true`. Decision 6 was reclassified and the loop
  halted. Two whole decisions were missing: the all-in marker, and what `min_raise_target` is
  checked against, which is where the phase's headline detector sits.
- **Stage 3, human gate, one blocker.** Taylor was told decision 6 costs nothing today. It
  costs almost nothing, and the reviewer found the one committed surface where it fires.
- **Stage 4, one reviewer, six blockers.** Including a test that could never pass, and two
  canaries requiring the report generator to exit non-zero with nothing telling the builder
  that its report had to validate its own figures.
- **Stage 6, two reviewers, one mechanical and one on the poker, three blockers, three fix
  rounds.** Both independently found that a straddled pot with two raises reaches the chart
  and is answered with the unstraddled range - the phase's headline claim failing, found by
  nothing the gate runs. Ruled: no guard, restate the truth, file
  `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`. The poker reviewer's two blockers were both
  about the refusal detail: the depth refusal named the first offending seat in seat order
  rather than the shortest, so two physically identical tables reported different depths
  depending on seating, and the ragged-hero code carried no detail at all. Round two then
  found that the fix for the first was itself unguarded - reverting it in both copies left
  all 954 tests green.
- **Stage 8, two independent reviewers running concurrently and seeing neither each other's
  work nor each other's output, a third agent costing the competing fixes for the sharpest
  finding before any code moved, and a fourth adversarial verifier that tried to break the
  fix round having seen none of the three.** The verifier's method was to revert each
  behavioural change in place and record which commands noticed. It found one real hole - a
  blocker fix guarded by a validator that nothing guarded, closed with the canary
  `the-residual-refusal-names-the-lowest-chair` - and two false statements in the round's own
  evidence, including a worked example one commit from being permanent in the mutation
  registry, wrong in the direction that made the fix look better supported than it was.

An earlier stage-8 poker pass ran and never wrote its note, leaving its findings in the tree as
four backlog filings and two source fixes. They are kept and the correction sits at the head of
the stage-8 note, because a review whose only record is its own diff is not reviewable - and
one of its fixes was half a fix the mechanical lens then caught. That was the round's most
consequential finding: `preflop_actions` accepted a betting sequence no street can produce, the
half-fix clamped one of two walks and traded one false poker claim for another, clamping both
proved fail-open, and it was fixed at the boundary so the record cannot construct at all.

### The blocker, and why it was not fixed

**Nothing anywhere compares the table's blind ratio against the structure the committed chart
was solved for.** The artifact declares a table size and a stack depth and says nothing about
its blinds. `StrategyQuery.blinds` carries the real ratio and no code reads it for this
purpose: validation checks only that `0 < sb <= bb`.

Measured, hero in the small blind facing a 2.5bb button open, all 169 canonical hand classes,
everything a spot key is made of held still. Hero pays 33.33% pot odds at 50/100, 36.11% at
$1/$3, 35.00% at $2/$5, and 25.00% at $5/$5. All four ask about the same key
`t6/d100/SB/BTN:raise@2.5`. Zero of 169 hand classes move a single weight in any of them, and
zero refuse. An 11.1-point swing in the price hero is offered, and nothing responds.

It is blocker-grade because it falsifies the phase's own closing claim, and because it is
this phase's own standard applied inconsistently: phase 13 refuses a table where one live
opponent's stack differs by a single chip, an effect of exactly zero, and answers a $5/$5
game where the small blind's dead money is doubled. $1/$3 and $2/$5 are the dominant live and
home structures, and the contract names home games twice.

**Ruled unfixable in scope, and the honest half done instead.** The check is cheap; the
missing operand is not. The ratio the artifact was solved at is recorded nowhere, so a check
written today would hardcode a reconstruction of an undeclared property of a committed
artifact - precisely the defect this phase exists to end, appearing inside the phase that
ends it. `data/artifacts/**` is out of scope and a loop halt condition. So the report's
headline claim was narrowed to name both escapes, the four-row measurement is published with
its own validator, and the finding is filed as
`BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` against phase 14. The report does
not claim the correct ranges differ; it states that they cannot differ here, because nothing
looks.

Recorded because a review that lists only hits is not calibrated: the mechanical lens found no
committed code giving a wrong answer on an input the engine or replay can produce, and the
poker lens found no refusal wrong in the short-stack direction, which decision 6 exists for.

## Known limitations and deferred items

**`ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` has now run as its own `contract-update`
task, which this phase's contract required before it could tag.** `PHASE_11_ENGINE_FIDELITY.md`
was at exactly 300 of 300 lines and `AGENTS.md` forbids raising the cap, so it took a rewrite
folding its appended amendments into the criteria they amend rather than an amendment it had no
room for. It is now 283 lines with every acceptance criterion intact; this contract is 290.
Both have headroom, which was the point: a document at its cap turns every later one-line
correction into a refactor.

**The debt was thirteen edits, not the nine this section listed.** That number is the lesson
worth keeping. The list was assembled from the ExecPlan's four, plus five found by checking the
phase's documents at stages 8 and 9 - and the executor found four more while doing the work:
an eighth `street_bet` site inside an amendment body the list of seven missed, a line stating
the old all-in ceiling was "too loose by exactly `to_call`" which the capped ruling made false
in the same way as its neighbour, decision 1 carrying the same dead preflop-equality invariant
as decision 3, and this contract's own claim that Phase 11 names the field "in three criteria"
when it was more. Every list of stale statements this phase produced was itself incomplete, at
every stage that produced one.

What the task corrected, in one line each: the query-level `street_bet` sites across five
acceptance criteria, a heading and a Scope bullet; the all-in ceiling, restated as the quantity
rather than as `(street_bet - to_call) + stack`, which under the capped ruling is a false
formula and is also the subtraction this contract's forbidden shortcuts bar from any comment,
docstring or report; the claim that the chart's raise cap is that same ceiling, when it is
higher by what hero still owes; this contract's "coincide" line, which the ante ruling replaced
with `committed_total >= street_bet`; its straddle criterion, where the gap is the straddle less
the big blind rather than the straddle; its un-narrowed Scope claim, now naming both escapes by
id; its statement that all five backlog entries read `phase: "13"`, when two now read `"14"`;
decision 6's stated cost, where all three `phase02-three-way-side-pot` decisions change refusal
code rather than two; decision 8's, which omitted this phase's headline residual; and decisions
1 and 3's dead invariant. Decision 15 took the optional `Correcting...` paragraph.

**And it missed three, which is why that entry closes on a review rather than on this section.**
An independent review found the identity still standing in three documents the task had open: this
contract's two-ceilings criterion, decision 11 of the decision list, and
`ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` itself. All three now state the gap as what hero
still owes to match the level, uncapped and therefore not `to_call` for a capped hero: 100 in, a
level of 300 and 150 behind gives `to_call` 150 and a gap of 200. Seven more statements survive
outside any of these scopes - frozen tests, a `preflop_chart.py` comment, the canary description, a
generated report - as `SUBTRACTION-IDENTITY-SURVIVES-IN-FROZEN-TESTS-AND-CODE`, and the rewrite's
own claim about what the tree holds today is `COMPLETED-CONTRACT-ASSERTS-THE-CURRENT-TREE`.

**The five backlog entries this contract is written against are now settled, and how they got
settled is the finding.** Each was audited against the code rather than against the phase's own
description of itself, and the five did not land the same way. Three closed and read
`status: done` against phase 13: `PER-SEAT-CONTRIBUTIONS-IN-QUERY`,
`STRATEGY-QUERY-STREET-BET-NAME` and `STRATEGY-QUERY-TO-CALL-HAS-TWO-READINGS`. Two did not
and now read `deferred` against phase 14: `ASYMMETRIC-EFFECTIVE-STACKS` and
`BLIND-STRUCTURE-VARIANTS`.

The distinction that decided both is the one a reader skimming the summary would get wrong.
This phase MEASURES table state and REFUSES what the charts cannot describe, which is not the
same as putting a thing into the artifact format or a spot key, and both deferred entries ask
for the latter. `ASYMMETRIC-EFFECTIVE-STACKS` is titled "Per-seat effective stack depth in
chart spots" and the diff to `spot_key.py` is docstring-only; `BLIND-STRUCTURE-VARIANTS` is
titled "Antes and straddles in the artifact format" and the artifact has no match for
`blind_structure`, `straddle` or `ante`. Six other entries name those two as what they wait
on, so a `done` would have silently retargeted six open items.

**It very nearly closed with them unsettled, and no check would have said so** - a peer session
caught it, not the gate. `backlog_errors` in `scripts/quality_checks.py` never compares an
item's `phase` against that phase's status in `phase_status.yml`, which is
`BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE`; that entry now argues from phase 13 as well as
phase 11. The same pass found three alignment items the stage-8 note asserted were filed and
were not. Both misses are one shape: a claim about the record that nothing checks against it.

**The two residuals, restated.** A straddled pot with two or more recorded raises is *answered*
with the wrong range rather than mis-coded, because a straddle perturbs only the first
increment and past one raise the prediction is a difference of two recorded amounts. And four
games reach one cell. Both wait on the same format change - a declared blind structure on the
artifact and on the query - which is a chart phase.

**Smaller residuals.** A straddle equal to the big blind, once its poster has acted, is
invisible to all three signals and is counted as such in the census truth column rather than
omitted. A ragged hero masks every table shape behind it. Refusing on any difference at all
refuses almost every real table once live state arrives.

**Line caps.** `preflop_chart.py` now sits at exactly 500 of 500, so the next edit to it
forces a split, and `scripts/generate_table_state_report.py` is 1,889 lines against a
`scripts/` cap of nothing at all. `TABLE-STATE-REPORT-RENDERER-HAS-NO-SIZE-CAP` records the
pattern; its own title and figures are stale, saying 1,135 lines.

**What a spot key would have to carry for the two Phase 12 findings.** For the under-raise, a
marker on each raise entry saying whether it was a legal full raise or an all-in for less,
because without it an under-raise and a short all-in render one string and any cell filled from
it mixes two prices. For the short call, the same marker on a call entry. Both are format
changes this phase is scoped out of. What leaving them open costs is not a wrong answer today -
it is a wrong denominator later, when the first artifact built from real hands fills one cell
from two different tables and nothing says so.

**The twenty-four backlog entries this phase filed,** by the phase each is assigned to. Ids
are copied from `backlog.yml` rather than written from memory; a fabricated one already
failed the backlog-integrity check once in this phase.

*Phase 14:* `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE` (the blocker above),
`LIVE-BLIND-LEVELS-MAKE-ORDINARY-OPENS-UNRENDERABLE` (the only price guard in the chart path
fires on a divisibility accident: a $10 open at $1/$3 is refused for rendering as 3.333bb).

*Strategy:* `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`, `COVERING-STACK-REFUSES-WITH-NO-POKER-CONTENT`
(a 100bb hero whose live opponents all cover is playing exactly the solved game and is
refused; 1,046 of 4,000 sampled tables), `DEPTH-CHECK-ORDER-HIDES-THE-SHORT-OPPONENT`,
`BIG-BLIND-ANTE-CLASSIFIES-AS-THE-RESIDUAL`, `ANTE-WITH-A-SHORT-ALL-IN-CALLER-TAKES-THE-RESIDUAL`,
`STRADDLE-REFUSAL-DOES-NOT-SAY-WHICH-GAME-IT-IS`, `SEAT-STATE-MARKERS-AGREE-WITH-NOTHING`,
`ALL-IN-SEATS-COUNT-AS-SEATS-THAT-CAN-ACT`, `QUERY-CANNOT-EXPRESS-RAKE-OR-DEAD-MONEY`,
`QUERY-CANNOT-EXPRESS-A-DEAD-BLIND`, `SIDE-POTS-NOT-EXPRESSIBLE-ON-THE-QUERY`.

*Elsewhere:* `CORPUS-CANNOT-EXPRESS-A-TABLE-SHAPE` (samples),
`REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` (simulator), and eight `contract-update`
items - `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP`,
`SPOT-KEY-LEGAL-ORDER-OVERCLAIM-IN-PHASE-12-CONTRACT`,
`DECISION-LIST-HAS-NO-FIXED-PLACE-FOR-A-RULING`, `TABLE-STATE-REPORT-RENDERER-HAS-NO-SIZE-CAP`,
`MUTATION-DRILL-CHECKOUT-DESTROYS-UNCOMMITTED-WORK`,
`LOOP-ADDS-NO-CANARY-FOR-A-FIX-FOUND-AFTER-STAGE-4`,
`REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL`,
`CONTRACT-UPDATE-IS-THE-LABEL-OF-LAST-RESORT`. The last three were filed after the gate, two by
the stage-8 verifier and one by the stage-9 review.

One is already `done`: `STRADDLE-SIGNAL-MISREADS-A-SHORT-ALL-IN-RAISE`, filed as a deferred
alignment item during the build and then fixed, after the poker reviewer showed the argument
for deferring it was wrong. Its wrong reason is kept on the record.

## One number a reader can recompute by hand

**The number the report picks: the pot of 260, at seat 1's decision in
`phase02-three-way-side-pot`.** It is printed in the third seat table of the moving-fixture
section, one of the three tables in the report read off a committed file rather than
constructed - all three are this fixture, and the report's other three are constructions. Open `data/samples/normalized_hands.json`, find the hand whose `hand_id` is
`phase02-three-way-side-pot`, and in its `preflop` street read the `amount` of every action
listed before seat 1's own `call`. A blind post and a raise record the total that seat then
has in front of it; a call records what that seat added. Add them:

    5 + 10 + 200 + 45 = 260

Checked against the file for this packet: the four actions are seat 0 posting 5, seat 1
posting 10, seat 2 raising to 200, and seat 0 calling 45. Seat 0's 5 plus 45 is 50, the whole
of what that seat sat down with, which is why the report's table shows it all-in.

**A second one, because it carries the blocker and needs only a calculator.** Take the $1/$3
row of the four-row blind-structure table at the end of the report. The blinds are 100 and
300 chips, the button opens to 2.5 big blinds, and hero is the small blind:

    the button's open      2.5 x 300              =  750
    hero has already paid  the small blind        =  100
    hero's price to call   750 - 100              =  650   = 2.1667bb
    the pot hero faces     100 + 300 + 750        = 1150   = 3.8333bb
    hero's pot odds        650 / (1150 + 650)     = 36.11%

Do the same at 50/100 and the price is 200 into 400, which is 33.33%; at $5/$5 it is 750 into
2,250, which is 25.00%. That is the 11.1-point spread the report publishes, and it is
arithmetic a reader can do on the page. I re-ran all four structures against the committed
chart for this packet: 0 of 169 hand classes answer differently in any of them, and all four
ask about the same spot key.
