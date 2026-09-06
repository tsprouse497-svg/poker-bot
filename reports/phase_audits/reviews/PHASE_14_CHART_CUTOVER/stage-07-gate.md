# Stage 7 independent review: the canary repair and the gate repairs

Read-only review by an agent that wrote none of this work and reviewed none of the earlier
stages. Subject: `verification/mutations.yml` at `e36be72`, and the gate repairs at `d097635`.
`scripts/check_gate_bite.py` and `scripts/run_verify.py` were NOT run, on instruction; no
mutation sentinel was present and no source file was mutated at any point during this review.
The working tree carried only `reports/active/latest_verify.txt` and
`reports/active/verify_results.json` as modified, which is a gate run in flight and was left
alone.

Every figure below was measured by a script this reviewer wrote, against the committed export
and the committed artifact, in memory. No file was written except this one. The scripts live in
the session scratchpad, and each finding carries what was run.

## What reproduced

Stated first, because most of it did, and a review that leads with its complaints
misrepresents the work.

**All 74 canaries apply.** Own script, over `verification/mutations.yml` read from `HEAD` rather
than from the working tree so a live mutation could not be mistaken for the committed state: 74
entries, no duplicate ids, and for every one the `find` string occurs **exactly once** in the
file its `file:` field names, with `find` never equal to `replace`. Zero broken. The inventory
was not taken on report.

**Every count in the three new canary descriptions re-derives, exactly.** Measured by patching
the module globals in memory - no file mutated - and recounting off
`load_solver_export(COMMITTED_EXPORT_PATH)`:

| claim | measured |
| --- | --- |
| baseline committed set | 249 spots, 249 nodes |
| census buckets | 33,362 depth / 348 exposure / 10 squeeze, summing with 249 to all 33,969 nodes |
| squeeze clause dropped: 249 to 259 | 259, and the squeeze bucket disappears entirely |
| raise depth 2 to 3: 249 to 2,456 | 2,456, and the depth bucket 33,362 to 29,105 |
| depth clause dropped outright commits 18,789 | 18,789 |
| merge seat test inverted: spots 20 to 5, cells 165 to 276 | 20 to 5, 165 to 276 |
| `exclusion_code`'s 26 squeeze nodes, 16 of them over the threshold | 26 and 16, so the bucket of 10 and the reverse-order 332 both follow |

**The call-site aim is right, and the canary understates its own kill.** `tests/test_chart_derivation.py:569`
does assert `is_big_blind_squeeze_spot(...) is True` on named nodes and `:612` asserts False on a
traced path, so a mutation inside the predicate would indeed die to a test reading the rule back.
Aiming at the call site in `exclusion_code` is the correct response. Separately, the four-bet
canary's self-criticism - that its pytest kill is only a frozen test reading `COMMITTED_RAISE_DEPTH`
back - is true of `:422` but not of `:423` and `:424`, which assert the max over kept nodes and
the min over refused nodes off the walk itself. Those are measured properties, so the kill is
stronger than the description claims. `tests/test_derived_chart.py:690` pins
`len(merged_cells(export))` at 165, and `tests/test_chart_census.py:87` pins 249 / 348 / 10 /
33,362, so all three new canaries have a measured kill and not only a constant read-back.

**Declining the two measured-survivor canaries was right, and the holes are filed.**
`check_gate_bite` requires every canary's `must_fail` commands to fail, so a canary a lane has
already measured would survive is a red stage 7 rather than evidence. The holes are in
`backlog.yml` as `TWO-MEASURED-GATE-HOLES-LIVE-ONLY-AS-YAML-COMMENTS`, status deferred, phase 14,
and that entry states in as many words that declining was correct and that what was owed was the
filing. Nothing to add.

**The four corpus pins re-derive and all four bite.** `measure_corpus(PreflopChartStrategy.from_repo())`
returns hands 499, decisions 3,048, refusals **139**, capped 10 - each equal to its pin. The three
that were supposed to stay put were not touched by the diff and reproduce. Feeding
`checks._validate_corpus` a doctored count for each of the four in turn raises on all four, so the
equality pin is live rather than decorative.

**The 139's breakdown reproduces under an independent classifier.** Classifying the 61 refused
spot keys by shape from the key text alone, with no reference to the lane's own buckets: 52
decisions in a limped pot over 16 spots, 52 in the big blind facing an open with a caller already
in over 13 spots, 25 four-bet-or-deeper chains over 25 spots - summing to the 129
`spot-not-covered` - and the remaining 10 all facing two raises, which is the
`hand-class-not-covered` bucket the comment describes as "three-bet spots the chart holds but
where hero's hand class sits outside the solved cells". Four buckets, four exact matches.

**Every registered fact reproduces, and so do the document's unguarded numbers.** Running each
`repo_facts` compute function: all ten agree with `reports/active/repo_facts.yml`, including the
four that moved. `docs/CORPUS_COMPARISON_LIMITS.md`'s numbers that no fact watches also check
out - 502 minus 27 gives the 475 Pluribus decisions, 2,546 minus 112 gives the human 2,434,
139 over 3,048 is 4.6 percent, and the per-seat refusal rate does run from the lojack's 1.0
percent to the big blind's 20.3 percent with those being the true min and max. The committed
shape is 5 first-in / 25 facing an open / 219 facing a three-bet, and the five first-in seats
are LJ, HJ, CO, BTN and SB, exactly as the rewritten comment and the rewritten document say.

**The nine re-filed backlog entries were sibling-matched, not swept.** Seven took
`contract-update`, one took `charts`, one kept phase 17 and moved only its status. `main` carries
42 items labelled `contract-update` and they do include the loop items, the review-machinery
items and four separate line-cap items, so the claimed precedent is real. Every one of the nine
carries both the label reasoning and the sentence conceding the gate rather than the argument,
and `BACKLOG-VOCABULARY-IN-USE-IS-NOT-THE-VOCABULARY-THE-GATE-ALLOWS` stays deferred holding the
opposite case. `main` does carry 109 items with zero using the disallowed vocabulary, and all
nine are branch-only, so "every one is ours" holds.

## Blocker

Two.

**B1. Two committed reports the gate regenerates now print the 249 and the 139 while arguing the
abandoned 86-spot coverage story. This is the same defect `d097635` fixed in the two files that
were in scope, left standing in the two that were not.**

`reports/active/latest_preflop_strategy_report.txt` prints `Spots: 249` at line 7 and then at
line 13:

> The selection predicate keeps only the spots the source prices every terminal below, which
> leaves **one opening range** and the big blind's defences, so this chart **answers far fewer
> questions than the retired one** and refuses the rest.

`reports/active/latest_spot_vocabulary_report.txt` prints
`total refusals over the committed sample            139` at line 111 and then, five lines later:

> the ruled selection predicate gives up fifteen spots the retired chart held, including **four
> of the five opening ranges**, so the total above is **higher than the 290** the vocabulary
> phase measured rather than lower.

and again at line 252:

> The **refusal total rises and every agreement denominator falls**, because the ruled selection
> predicate keeps only the spots the source prices every terminal below: **four of the five
> opening ranges and ten of the eleven spots facing a single open are given up**.

Measured against the committed export and the committed sample: the chart holds **five** first-in
ranges (LJ, HJ, CO, BTN, SB) and **25** spots facing a single open. Refusals **fell**, 290 to 139.
Both agreement denominators **rose** - 456 and 2,302 before the cutover, 475 and 2,434 now, so
2,909 scored decisions against 2,758. Every clause quoted above is false, and the second report
states 139 and argues it rose past 290 five lines apart.

These are not stale committed bytes. The sentences are hardcoded report text at
`scripts/generate_preflop_strategy_report.py:590` and
`src/poker_training_bot/solver_artifacts/vocabulary_corpus_report.py:73` and `:234`, and
`generate_preflop_strategy_report` and `generate_spot_vocabulary_report` are both registered gate
commands - so the gate re-emits them on every run, and `latest_preflop_strategy_report.txt` was
regenerated inside `d097635` itself with the false paragraph intact. `d097635`'s own commit
message identifies exactly this claim as "false in a way that mattered" and corrects it in
`table_state/measures.py` and `docs/CORPUS_COMPARISON_LIMITS.md`; the correction stopped at the
edge of `approved_scope`. `docs/CORPUS_COMPARISON_LIMITS.md` now says the chart answers "almost
all of the sample - slightly more of it than the rates published before the cutover", and
`latest_preflop_strategy_report.txt` says it "answers far fewer questions than the retired one".
Two published documents, opposite claims, and the gate maintains the wrong one.

Neither generator is in the current `approved_scope`, so the fix needs a dated
`scope_change_log` entry. Three internal statements of the same withdrawn reality should go with
it, since they are what a later reader will build on: the docstring at
`scripts/generate_preflop_strategy_report.py:18`, the comment at `:274` ("the one opening range
the committed chart holds"), and `src/poker_training_bot/strategy/preflop_price.py:12`
("86 committed spots ... and the one committed opening"). `src/poker_training_bot/solver_artifacts/solve_conditions.py:53`
carries a stale count of the same vintage, "21 of the 86 committed spots".

[resolved] Lane H rewrote the coverage prose in both generators against the measured shape - 5
first-in, 25 facing a single raise, 219 facing a three-bet, 249 total, refusals 290 to 139 - and
replaced the hardcoded direction words with values derived from the counts printed beside them, so
the paragraph can no longer contradict its own table; the two internal statements inside those two
files went with it, both reports regenerated byte-identical on a second run, and the four statements
outside them are reported to the coordinator unfixed because they are outside this lane's files.

**B2. The decision record's quotation of the scope-log flag was falsified by the citation
reword, and the commit message's "no finding or meaning changed" does not hold for it.**

Eight occurrences in `reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md` of the
backticked literal ending `AT THE NEXT CONTRACT` plus a hyphen plus `UPDATE` were rewritten to
the same words with a space in place of the hyphen. The string actually written into
`CURRENT_TASK.yml`'s `scope_change_log` is the hyphenated one: five occurrences today, identical
at `8006516`, none of them touched. So the record now quotes, as "the literal flag", a string
that appears nowhere in the repo. Line 3074 says it outright:

> Every one of the seven rulings carried the flag `...` in `CURRENT_TASK.yml`'s
> `scope_change_log`

which is a directly checkable claim and is now false as written. The mitigation this discharges
has exactly one mechanism - a greppable string in a file - and the record of it no longer names
the string. A reader who greps for the quoted literal concludes the flags were never written.

The lane's stated reason for moving the prose rather than the checker is sound and I am not
disputing it: a phase may not edit a gate command it is measured against. But the fix does not
require editing the checker. `NOT_BACKLOG_IDS` in `scripts/run_full_quality_gate.py` is the
designed escape hatch and already carries a phase-05 review heading for this exact reason, and
`QUALITY-GATE-READS-LANE-NAMES-AS-BACKLOG-IDS` is filed against the trap; failing that, the
in-scope repair is to stop purporting to quote the whole literal - `OWES A DECISION ITEM` alone
matches nothing in the checker and stays true. Either way the record must not assert a quotation
it does not have.

[resolved] Lane H took the in-scope repair: all eight backticked quotations in the decision record
now stop at the head, which is the string a reader can grep and find, and each says in prose that
the tail is withheld because the citation check reads it as an id nobody filed. Re-measured while
fixing it, this finding is larger than written: the two assertion lines were false in count as well
as in quotation, because six of the seven rulings carry the flag and the seventh - item 30, the one
that opened this task - carries none, its entry naming the other six's instead; both lines now say
that, with the 5 flagged scope-log entries and the one entry holding two rulings named. The quality
gate passes all four checks.

## Non-blocker

Seven.

**N1. "Thirteen false citations" is off by one, in the direction that matters least.**
Reproducing `_citations` and `backlog_errors` against `bcf956a`: the check emits one error per
(file, token) pair, and there were **14**, across 12 distinct tokens and 25 occurrences. The
hyphenated flag alone appeared 8 times, not the 7 the hunks suggest. All 14 are cleared at `HEAD`
- I re-ran the check's logic and it returns zero - so the repair is complete; only the count is
wrong, and it lives in a commit message rather than in a document anything re-derives.

**N2. One of the two review-note edits loses the finding it was recording.**
`stage-06-build-review-poker.md`'s two edits are clean: a hand range written as AA-with-a-hyphen-TT
became "AA down to TT", meaning preserved, and the neighbouring 99-66 and ATo-AKo were correctly
left alone. `stage-01-contract.md` is different. The note was recording *which two id-shaped
phrases the checker misread as citations*, and it now names them in their spaced forms - `P10 D3`
and `JJ 88`. Neither spaced form can match the checker's pattern, which requires a hyphen. So the
sentence now describes a mechanism that cannot happen, and the strings that actually tripped the
check are no longer recoverable from the note. Not a blocker because the note's conclusion is
unaffected and the register is a parenthetical, but a review note is a snapshot and this one lost
a fact.

**N3. A code comment still reasons from the withdrawn number.** `scripts/repo_facts.py:242`:
"The chart cutover took this fact from three digits to four, and this repo writes a four-digit
count as 2,529; a bare `\d+` would capture '529' out of that". The fact is 139 - three digits
again. The pattern is still correct and still matches, so nothing is broken; the justification
beside it now describes a state that was reverted.

**N4. The pin's own error text now misstates where the phase started.** `table_state/checks.py`
renders "refusals measured 140 against the 139 this phase started from". This phase started from
290, then 2,529. Cosmetic, but it is the string a future reader sees when the pin fires.

**N5. The `charts` label is thinner than its reasoning sounds.**
`REALIZATION-FIT-TABLE-IS-NON-MONOTONE-IN-HAND-STRENGTH`'s note says `charts` "is the label its
siblings carry" and cites `SOURCE-PRICES-THE-JAM-EXACTLY-AND-EVERY-RAISE-THROUGH-A-MODEL`. That
sibling is branch-only, filed by this same lane, so the precedent is the lane's own filing rather
than an established one. `main`'s only two `charts` items are `STACK-DEPTH-BUCKETS` and
`POSTFLOP-BOARD-ABSTRACTION`, neither about a solve source. Not false as written, and the
disposition is still the right one; the seven `contract-update` moves are the ones with real
precedent on `main`.

**N6. The stage-6 fact-drift finding now cites four strings that no longer exist.**
`FACT-DRIFT-WATCHES-TWO-OF-A-DOCUMENTS-SIX-LIVE-NUMBERS` quotes "72 scored decisions", "the human
denominator is 447", "from 456 and 2,302" and the 97.3-to-33.9 rate span, and says all were
reproduced correct at stage 6. Its prediction came true inside its own phase: those four numbers
moved in `d097635` and only the two registered facts would have gone red. I re-derived the four
replacements - 475, 2,434, and the 1.0-to-20.3 span - and all four are currently correct and
still unguarded. The entry's diagnosis stands; a reader grepping for its quoted strings will find
none of them.

**N7. The committed all-in equity matrix is not reached by any gate command, test, or canary.**
`scripts/generate_preflop_equity_matrix.py` is 634 new lines; `data/artifacts/preflop/equity/preflop_eq169.bin`
is 114,244 committed bytes; its source card carries a sha256 and a documented
`--check` recipe. No entry in `COMMANDS` runs the script in any mode - I enumerated all 48 and
none mentions it - no file under `tests/` names it, and no canary attacks it.
`load_equity_matrix` in the report validates the byte length and nothing else, so it would accept
114,244 bytes of anything. The contract's own criterion calls the matrix "committed and
deterministic". The mechanism to close this already exists and was written by this phase; only
the registration is missing. Filed as alignment below rather than as a repair here, because
registering a command ID means declaring it in the contract frontmatter, which this phase cannot
do in `implementation` mode.

## Alignment

One, and it is the answer to the question this stage most wanted judged.

**The 74 is a comfortable number over an uncomfortable gap, and the gap is measurable.**

The claim `check_gate_bite` makes is narrower than "gate bites: 74 mutations all caught" sounds,
in three separate ways, and only the first is disclosed anywhere.

*Whose work the 74 attack.* Diffing the canary ids against the merge-base `ada5205`: **16 of the
74 are new on this branch, and 58 predate the phase entirely.** So 22 percent of the number
attacks the work phase 14 built. The 16 land on `chart_derivation.py` (7),
`chart_selection.py` (3), `chart_relations.py` (3), `generate_derived_chart_report.py` (2) and
`schema.py` (1). That is honest coverage of the selection rule and the relations - one canary per
clause, as the triage comment claims and as I verified - and it is not coverage of the phase.

*What the 74 do not touch.* Phase 14 added **7,009 lines** under `src/` and `scripts/`, of which
**2,574 - 37 percent - sit in files no canary names at all.** The zero-canary list, by lines
added: `generate_preflop_equity_matrix.py` 634, `solve_conditions.py` 277,
`vocabulary_corpus_report.py` 253, `chart_query.py` 105, `preflop_price.py` 96,
`decision_query.py` 95, `chart_provenance.py` 73, and the changed
`generate_preflop_strategy_report.py` +288, `vocabulary_report.py` +199, `preflop_sizing.py` +135,
`convert_preflop_export.py` +124, `vocabulary_measures.py` +58, `table_state/measures.py` +31.
**Nothing anywhere in the 74 attacks anything under `src/poker_training_bot/table_state/`** - which
is precisely why `CORPUS_REFUSALS`, the pin this stage deliberately moved, has no canary of its own:
the pin is a live equality check, I proved it bites, but nothing proves the guard reading it is
still wired in. That is the shape `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL` already
describes. And the two reports carrying B1's false prose are two of the zero-canary files, which
is not a coincidence: no canary anywhere attacks a report's rendered text.

*What a canary proves at all.* `mutation_coverage_errors` demands a canary only for commands whose
id starts with `pytest`, with `EXEMPT_FROM_MUTATION_COVERAGE` empty. **29 of the 48 registered gate
commands are named by no mutation** - every generator and every checker. This one is disclosed:
the check's own `does_not_cover` field says it reads pytest commands only and that "one canary
aimed at a command says the command can fail, not that its tests are strong". The repo is honest
about it. The packet should be too, because "74 mutations all caught" read beside a 48-command
gate invites the opposite reading.

None of this is a reason to hold the stage. The 74 are all applicable, the new canaries are
well aimed, and their arithmetic is exact. But the sentence "gate bites: 74 mutations all
caught" should not appear in the audit packet without the three numbers beside it: 16 of 74 aimed
at this phase, 37 percent of the phase's new lines in files no canary names, and 29 of 48
commands with no canary demanded of them.

Filed under `TWO-MEASURED-GATE-HOLES-LIVE-ONLY-AS-YAML-COMMENTS`, which already carries the
zero-canary census for `chart_provenance.py`, `chart_query.py`, `price_normalisation.py`,
`schema.py` and `lookup.py` and already records that no canary attacks the report's sections as
text. What that entry must gain is the rest of the census measured here - the equity matrix
generator and its committed artifact, `solve_conditions.py`, `vocabulary_corpus_report.py`, and
the whole of `table_state/` including the four corpus pins - plus the 16-of-74 and 29-of-48
figures, since the entry is the place a later phase will look for what the gate does not reach.
The equity matrix wants an id of its own as well, because its repair is a specific and available
one: register the generator's existing check mode as a gate command. That id is not yet filed and
this note deliberately does not spell it in the id form, so as not to create the false citation
it would be.

I have NOT verified that the 74 are caught. `check_gate_bite` was not run, on instruction. What
is measured here is that all 74 apply - every `find` string occurs exactly once in the file it
names - which is the precondition `check_gate_bite` refuses on, and nothing more.
