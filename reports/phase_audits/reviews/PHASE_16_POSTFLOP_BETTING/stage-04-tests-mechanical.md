# Phase 16, stage 4: mechanical review of the authored tests

Read-only review of `git diff 58ed4636ed6f744c4938319614d207b2334dd988 HEAD` in the
`phase/16-postflop-that-can-bet` worktree. Reviewer did not write any of it.

The driver's question: *would each test fail against a plausible wrong implementation, and does it
assert on real behaviour rather than on state rebuilt from the code under test?*

Method. Every figure below was computed in this worktree and the method is named beside it. The
test command was run as `uv run python -m pytest` over the six files
`pytest_postflop_betting` registers; the isomorphism counts were brute-forced over the 52-card deck
in a throwaway interpreter; the simulator figures were measured by replaying
`tests/test_postflop_query_recording.py`'s own fixture profiles. No mutation tooling, no
`run_verify.py`, no `check_gate_bite` was run, and no file outside this note was touched.

Current state of the registered command, measured: **22 failed, 21 passed, 152 errors**. The errors
are the fixtures reaching modules stage 6 has not written, which is the intended stage-4 red.

## Blocker

**B1. Three report tests hand their entire assertion to a function the implementation writes, with
no negative control.** `tests/test_postflop_betting_report.py:195` asks the generator
`exploitability_lines_are_qualified(report) is True`; `:265` asks
`cost_rows_declare_measured_or_scaled(report) is True`; `:306` asks
`vacuous_codes_are_labelled(report) is True`. Grepped across `tests/`, `scripts/` and `src/`, each
of those three names occurs exactly once in the repo - at its own call site in this file. So each
test's whole claim is "the code under test says the code under test is fine", and
`def exploitability_lines_are_qualified(report): return True` passes all three. This is the exact
shape the file's own docstring warns about at `tests/test_postflop_betting_report.py:8-13` ("this repo
has twice shipped a validator that could not fail"), and the three criteria they stand for are
three of the ones a reader is least able to check by eye: the menu qualification on every
exploitability line, measured-versus-scaled on every cost row, and a vacuous refusal code being
labelled as one.

A fix has to feed each predicate a **known-bad report string built in the test** and require
`False`, beside the `True` case on the real report: an exploitability line with no menu clause; a
cost row carrying a rainbow figure with no `scaled` label; a code with a zero count and no vacuity
label. Two of the five validators in `TestTheGeneratorRefusesAWrongFigure` already do exactly this
(`:384` with `:392`, and `:408` with `:416`, each pair a refusal with an acceptance) -
these three need the same treatment.

**B2. The canary `postflop-weight-bounds-not-enforced` will not bite, because a second live check
refuses the same payload.** `verification/mutations.yml:1412` disables
`if not 0.0 <= weight <= 1.0:` and names
`tests/test_postflop_artifact.py:345 test_a_weight_outside_zero_to_one_is_refused_rather_than_rendered`
as its witness. That test sets `payload["class_weights"][0][0] = 1.7` and requires a refusal. But
`tests/test_postflop_artifact.py:359 test_a_class_whose_weights_do_not_sum_to_one_is_refused`
requires the importer to hold a **separate** sum-to-one check on the same row, and setting one
element of a row that sums to 1.0 to the value 1.7 leaves the row summing to `1.7 + (1 - original)`,
which is 1.0 only if the original weight was 1.7 - impossible for a bounded weight. So with the
mutation applied, the sum check still refuses the cell, `pytest.raises` is still satisfied,
`pytest_postflop_betting` stays green, and the mutation survives a command it names. This is the
canary the mutation's own description calls "the one that targets this phase's own new command",
and `check_gate_bite` will red on it at stage 7 - after stage 5 has frozen both the test and
`verification/**`.

The fix is to make the witness payload violate the bound and *only* the bound: replace the whole
row with one that still sums to 1.0 but leaves the interval, e.g.
`payload["class_weights"][0] = [1.7, -0.7] + [0.0] * (len(row) - 2)`. Then the sum check passes, the
bounds check is the only thing that can refuse, and disabling it makes the test red.

**B3. `test_a_cell_whose_board_is_not_its_canonical_representative_is_refused` does not test
non-canonicality.** `tests/test_postflop_artifact.py:331` takes the committed cell's board and
rewrites every card to spades. On a rainbow or two-tone sample cell that produces a board in a
*different* isomorphism class (or a board with duplicate cards), so the importer refuses on the
stored-key mismatch - which is already what `test_a_stored_id_that_disagrees_with_the_re_derived_key_is_refused`
at `:320` proves, making this a duplicate rather than a second check. On the monotone sample cell
(`9c8c7c`, ruled by decision 6) the all-spades rewrite stays inside the same class, and if the
canonicaliser's representative for a monotone class happens to be the spade dress, the payload is
canonical, nothing is refused, and a **correct** implementation reds. Which of the three cells is
tested is decided by `sample_cell()` at `:292` taking `sorted(sample_dir.glob("*.json"))[0]`, i.e.
by whatever filenames stage 6 picks.

The fix is to construct the non-canonical dress rather than guess at it: take the cell's board, find
a suit permutation whose image is in the same class but is not `canonical_board(board)`, and assert
that cell is refused. That tests the stated claim on every sample board and cannot depend on a glob
order.

**B4. Stage 4 never states the migration set it measured, which this stage's own contract requires.**
`docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:293-297`: "The frozen tests of completed phases
that assert against the query shape are migrated in this task... **Stage 4 measures that set itself
and states it, rather than inheriting a count from here.** Three are known to invert... Three is a
finding rather than a bound, so the obligation is to sweep." The diff migrates exactly the three
files the contract names, and nothing in the diff - not the ExecPlan
(`docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:39-45`, which only restates the obligation),
not `CURRENT_TASK.yml`'s scope entry, not any review note - records what was swept, how, or what the
sweep found. A reader cannot tell a completed sweep that landed on three from an inherited count of
three. The fix is a short statement in the ExecPlan naming the greps run and the set they returned.

For what it is worth, I ran the sweep myself and **the migration is complete**: grepping `tests/`
for `DECISION_AUDIT_SCHEMA_VERSION`, `schema_version`, `SeatAction`, `preflop_actions`,
`to_payload`, `to_json_line` and `dataclasses.fields` turns up no fourth file that inverts. The
things that could have broken and do not: no test pins an exhaustive field list of `StrategyQuery`
(`tests/test_table_state.py:161` and `:174` name fields individually), so a defaulted
`postflop_actions` is invisible to them; `tests/test_engine_fidelity.py:565` rebuilds queries from
the committed audit files but stamps `DECISION_AUDIT_SCHEMA_VERSION` rather than the line's own, so
the bump does not red it; `tests/test_solver_export.py:656` recomputes headroom from the source card
rather than hard-coding it, so regenerating the card (which the contract already requires) is
enough. The finding is the missing statement, not a missing file.

## Non-blocker

**N1. A test that cannot fail.** `tests/test_postflop_artifact.py:511
test_no_postflop_file_sits_directly_under_the_preflop_directory` asserts
`POSTFLOP_DIR.resolve() not in PREFLOP_DIR.resolve().parents`. Both are module constants built as
`ARTIFACT_ROOT / "postflop"` and `ARTIFACT_ROOT / "preflop"` at `:40-41`; the assertion is true of
those two strings whatever any implementation does, and it passes today with no postflop tree in
existence. The criterion it stands for is genuinely covered by the test below it at `:515`, which
imports the preflop library and requires every spot id to start with `t`. Harmless, but it is one of
the 21 passes and it is evidence of nothing.

**N2. `test_the_postflop_history_does_not_leak_across_streets` is weaker than its name.**
`tests/test_postflop_query_recording.py:125` asserts only that the seats named in a non-flop query's
`postflop_actions` are a subset of the seats not marked folded. An implementation that never clears
the history between streets satisfies that whenever every flop actor is still in the hand. It does
have incidental bite: replaying the file's own fixture profiles at seed `20260812`, I measured **16
of 24 hands** in which a seat folded on the flop and the hand still reached the turn, and in those
a leaked flop action would name a folded seat and fail the assertion. So it is not vacuous - but the
bite is accidental and will move the first time the reference profiles change behaviour, which is
what this phase does to them. A direct form (a turn query's recorded bet amounts for a seat must
not exceed that seat's current `street_bet`) would say the thing outright.

**N3. The equity formula is rebuilt from the path under test.**
`tests/test_postflop_betting.py:495` computes the expected value as `(wins + ties/2) / 990` from the
same `holding_counts` call it then compares against, so it agrees with `river_equity` for any
consistent orientation. The orientation is saved elsewhere - `:523` requires AA's equity to exceed
the price and `:537` requires `3c2d`'s not to - so the pair is not vacuous overall. Worth flagging
because of a live trap for stage 6: today's `holding_counts` at
`scripts/generate_postflop_fallback_report.py:418` returns `(beats, ties, hero_label)`, where
`beats` is the count of holdings that **beat** hero. The new test at `:486` unpacks that first
element as `wins`. A literal move of the existing function into `src` inverts the equity, and only
`:523`/`:537` will say so.

**N4. The second canary's payload may also be refused by something other than the line it
disables.** `verification/mutations.yml:1434` disables
`if size_chips > hero_street_bet + hero_stack:`, witnessed by
`tests/test_postflop_artifact.py:370`, which sets `payload["bet_sizes_bb"]` to a **one-element**
list. Decision 6's lean JSON keeps class weights as arrays parallel to the action list, so a
one-element size menu is likely to trip an arity check as well - and if it does, the mutation
survives for the same reason as B2. Keeping the list's length and inflating a single entry removes
the risk at no cost.

**N5. Nothing pins that the report's printed spot count is routed through its own validator.**
`tests/test_postflop_betting_report.py:429` exercises `check_spot_count_matches_index` in isolation;
no test requires the generator to call it on the number it printed. The mutation at
`verification/mutations.yml:1457` therefore bites only if stage 6 wires it that way, which its own
description already concedes. `check_gate_bite` catches this at stage 7 rather than here, so it is
not stage-holding, but it is the third of three canaries whose bite rests on stage-6 discipline.

**N6. Four of the 21 passes are the test file checking its own constant table.**
`tests/test_postflop_artifact.py:459`, `:471`, `:478` and `:492` all evaluate the file's `texture()`
and `rank_structure()` helpers over `SAMPLE_BOARDS`, a literal at `:57`. No implementation can move
them. `:478` is the exception worth keeping - it brute-forces all 22,100 boards to establish that
paired-monotone is impossible, which is a fact about the deck rather than about the table - but the
other three are documentation. The load-bearing test is `:451`, which compares the committed sample
against that table, and it currently fails as it should.

**N7. The at-the-table flush-draw test has an escape hatch that a plausible implementation walks
through.** `tests/test_postflop_betting.py:444` passes if the two hands differ in
`(action, amount)` **or** in `detail`. If `detail` names the spot key plus the hero hand - a natural
thing for a refusal/decision detail to carry - the second disjunct is true for any pair of distinct
holdings and the test proves nothing. The disjunct exists for a real reason (a correct solve can
play both hands the same way after argmax), but the honest form is to compare the two hands' class
weight vectors rather than the sampled action. The general property is proved properly in
`tests/test_postflop_key.py:382`, so the loss here is the table-level statement only.

**N8. The re-pointed-canary class checks less than its name claims.**
`tests/test_postflop_betting.py:566` verifies that the six ids still exist, that each `file` ends in
one of three filenames, that `fail-closed-can-invest-again` keeps `pytest_engine_fidelity`, and that
none names bare `pytest`. It does not check that the `description` claim is unchanged (the
criterion's actual wording), and it does not pin the other five to `pytest_postflop_fallback` - I
read those five witnesses out of `verification/mutations.yml` and they are all
`pytest_postflop_fallback` today. A stage 6 that re-pointed a canary at a trivial line in the right
file, or that quietly moved a witness, passes all four tests.

**N9. The orbit-size docstring misattributes the sizes to textures.**
`tests/test_postflop_key.py:314-318` says "Rainbow boards have a 24-element orbit, two-tone 12,
monotone 4". Brute-forcing the deck, the true breakdown by (texture, orbit size) is rainbow-24: 286,
two-tone-12: 1014, rainbow-12: 156, monotone-4: 286, rainbow-4: 13 - so 169 of the 455 rainbow
classes do **not** have a 24-element orbit, and 13 of the 299 orbit-4 classes are rainbow trips
rather than monotone. The assertion itself uses the right numbers (`ORBIT_HISTOGRAM` at `:47` is
exactly `{24: 286, 12: 1170, 4: 299}`, which I confirmed) and the test is correct; only its
explanation is wrong. It is a frozen test's prose, so a later reader will take it as the authority.

**N10. Coverage holes against the contract.** Walking the acceptance criteria, every one is reached
by a named test except these:

- *"The refusal inventory keeps working at a non-flat table"* (contract `:195-197`,
  `REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL`). No test in the six files touches the inventory
  generator; `tests/test_postflop_key.py:618-668` only writes a fake inventory file to exercise the
  preflop scraper. Nothing pins that a postflop code carrying board or line detail does not
  fragment the grouping.
- *Decision 6's lean JSON shape* (contract `:158-160`: hoisted action names, classes as a parallel
  array in canonical order, three-decimal floats, free weights only). Grepped the six files for
  "hoisted", "parallel array" and "three-decimal": no test. The byte budget is checked as a total,
  so an artifact that blows the encoding but stays under 20 MiB passes everything.
- *"re-derived at import and at lookup"* (contract `:60-62`). The import half is pinned at
  `tests/test_postflop_artifact.py:320`. Nothing exercises the lookup half; a strategy that trusts
  the id it read at import satisfies every test here.
- *"a committed audit at the old version is rejected rather than read as the new one"*
  (contract `:58-59`). Pinned at construction (`tests/test_postflop_key.py:210`), not at read. The
  one place the repo reads committed audit lines back, `tests/test_engine_fidelity.py:565`,
  discards each line's own `schema_version` and rebuilds at the current constant - so an old-version
  file is, literally, read as the new one there.
- *"No report **or packet** may state an accuracy for the solve as a whole"* (contract `:99`). The
  regex at `tests/test_postflop_betting_report.py:183` reads the report only. The packet half is
  unchecked by anything mechanical.

**N11. A contract sentence is read two ways, and the test freezes the less literal one.**
Contract `:203-205` reads "The equity number moves into `src`: `hand_cannot_lose` returns a
short-circuiting bool and raises on a flop board, and the counting `holding_counts` lives in a
report script." `tests/test_postflop_betting.py:486` takes `holding_counts` out of
`strategy.postflop_betting`, i.e. out of `src`, which is the opposite of what that clause says on
its face. The test's reading is the sensible one - a strategy cannot import from `scripts/` - but
it is a reading, it is about to be frozen, and contract edits are forbidden from here.

**N12. Import-shape nit.** `tests/test_postflop_betting.py:576-584` does a `sys.path.insert` inside
a fixture and then `import check_gate_bite` flat, where five other test files do the insert at
module scope and the rest of the repo uses `import scripts.check_gate_bite`. Both work; the flat
form creates a second module object for a module other tests import as `scripts.check_gate_bite`.
Read-only here, so harmless, but it is two conventions in one phase.

**The 21 passes, classified.** All 21 assert about something that already exists, and I found no
pass that asserts nothing real except N1. Real regression pins of existing behaviour, passing
because the behaviour is already correct and the test's job is to keep it: the preflop action order
(`test_postflop_key.py:263`), the preflop library still holding only preflop charts
(`test_postflop_artifact.py:515`), the whole artifact tree inside the cap (`:538`), the old fallback
still unable to bet (`test_postflop_betting.py:147`), `hand_cannot_lose` still refusing a flop board
(`:553`), the simulator still reaching a flop and still recording preflop history
(`test_postflop_query_recording.py:100`, `:136`), and both command ids being registered
(`test_postflop_betting_report.py:88`). Four pass on `verification/mutations.yml` as it stands today
(`test_postflop_betting.py:586`, `:591`, `:598`, `:605`) - see N8 for what they do not cover. Four
are the constant-vs-constant sample-table checks of N6. Four pass for a **different reason than they
will after stage 6** and are worth knowing about: `test_postflop_key.py:149` and `:155` require a
bare `ValueError` from `SeatAction(0, "bet")` and `SeatAction(0, "check", 300)`, which today comes
from `"bet"` not being in `_PREFLOP_HISTORY_ACTIONS` at all rather than from a missing amount - the
same is true of the migrated `tests/test_strategy_contract.py:432`, which dropped the old
`match="unknown history action"`; the paired acceptance tests (`test_postflop_key.py:143`,
`test_strategy_contract.py:417`) are what stop that being a hole. `test_postflop_key.py:218` asserts
`record.outcome.amount == 180` on a record built two lines above, so its only real content is that
`DecisionAuditRecord` did not raise on a postflop bet - which is the legality proof and is fine, but
the assertion as written is the input read back.

**The migrated tests.** All three edits are genuine migrations, not weakenings.
`tests/test_table_state.py:195` and `:623` and `tests/test_spot_vocabulary_downstream.py:253` move
`3` to `4` and nothing else; `test_a_record_at_the_old_schema_version_is_rejected` at
`test_table_state.py:625` still uses `2`, so the rejection claim is untouched.
`tests/test_strategy_contract.py:295` keeps the byte-exact JSON line and adds `"postflop_actions":[]`
in sort order plus `"schema_version":4` - strictly more pinned than before, and it is one of the two
files the contract's own list of three did not name, so the sweep found it.
`tests/test_strategy_contract.py:417` inverts `test_rejects_a_bet_because_preflop_has_no_bet` into
an acceptance and adds `test_rejects_a_bet_without_the_amount_it_bet` beneath it, which keeps the
"a size is required where the price lives" half of the original claim; the closed-vocabulary half
stays at `:413`. The only loss is the `match=` on the new rejection (N-classified above).

## Alignment

- `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL` (existing, `backlog.yml`). B1 is this entry
  from the other end and the entry does not yet name the shape. The entry is about a *generator's*
  validator being unfalsifiable; B1 is about a *test* delegating its whole assertion to such a
  validator, which is strictly worse - the validator now has a passing test beside it saying it was
  checked. When that tooling work happens, the check should flag both: a predicate decidable from
  its inputs, and a test whose only assertion is `predicate(x) is True` with no `False` case.
- `LOOP-ADDS-NO-CANARY-FOR-A-FIX-FOUND-AFTER-STAGE-4` (existing, `backlog.yml`). B2 and N4 are the
  mirror case the entry does not cover: a canary authored **at** stage 4 that is wrong, discovered
  at stage 7 by `check_gate_bite`, when stage 5 has frozen both `tests/**` and `verification/**`.
  The loop has no cheap path from "the canary does not bite" back to "fix the canary", and the cost
  lands on the phase that followed the rule.
- `A-COMMITTED-AUDIT-FILE-IS-NEVER-CHECKED-AGAINST-ITS-OWN-SCHEMA-VERSION` (**proposed**). From
  N10: the constructor refuses an old version, but the one reader of committed audit lines
  (`tests/test_engine_fidelity.py:565`) drops the line's `schema_version` and rebuilds at whatever
  the constant currently is. Every schema bump makes the stale committed `.jsonl` files in
  `reports/active/` readable as the new shape until they are regenerated, which is exactly the
  defect `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS` was filed against, one level up.
  This phase makes it worse by bumping the version again; it is not this phase's to fix.
- `A-PACKET-FIGURE-BAN-IS-ONLY-CHECKED-IN-THE-REPORT` (**proposed**). From N10: several of this
  contract's bans are written "no report **or packet** may...", and every mechanical check the phase
  authors reads the report. The packet is prose a human writes at stage 9 against a checklist,
  which is the surface the bans exist for.
