# Stage 6 build review - MECHANICAL

Independent, read-only. I wrote none of this work and have not read the poker reviewer's note.
Range reviewed: `c45013b..HEAD` (14 commits, 40 files) in
`/Users/taylorsprouse/projects/poker-bot-worktrees/phase-14`, branch `phase/14-chart-cutover`.

`scripts/check_gate_bite.py`, `scripts/run_verify.py` and a bare whole-suite `pytest` were not run.
No planted mutation was encountered; the working tree held no modification at any point (only the
poker reviewer's own untracked note appeared, and it was not opened).

Every finding below carries the command I ran and its output. Where I am guessing I say so.

## What reproduced clean

- `uv run python -m pytest` over the eleven named files: **111 passed, 4 skipped**.
- The six re-opened test files together: **126 passed**.
- `uv run python scripts/convert_preflop_export.py --check`: reproduces.
- `uv run python scripts/generate_preflop_equity_matrix.py --check`: reproduces
  (`sha256 d982b854...5779`, matching the card).
- `check_file_sizes.py`, `check_scope.py`, `ruff check --no-cache .`: all three clean.
- All 74 canaries in `verification/mutations.yml`: every `find` string occurs **exactly once** in the
  file its `file:` field names, no missing files, no no-op replaces, no duplicate ids. Measured with
  my own script, not `check_gate_bite`.
- No duplicate top-level definition in any new or rewritten module. The six `# noqa` added are five
  `E402` (the repo's existing `sys.path`-before-import convention in `scripts/`) and one `BLE001`
  with a stated reason.

## Blocker

### 1. The equity matrix's companion card names the wrong first row

`data/artifacts/preflop/equity/preflop_eq169.source.json` publishes:

    "class_order": { "index": "gtopen_class_index, ...", "row_0": "AA" }

The matrix is indexed by `gtopen_class_index` - `scripts/generate_preflop_equity_matrix.py:511`
reads its own check cells as `matrix[gtopen_class_index(first)][gtopen_class_index(second)]` - and
under that index **AA is row 168, not row 0. Row 0 is `22`.**

Read straight out of the committed bytes with no repo report in the loop:

    bytes: 114244 expected 169*169*4 = 114244
    gtopen_class_index('AA') = 168
    index of the class at row 0: ['22']
    HAND_CLASSES[0] = AA

The cause is `scripts/generate_preflop_equity_matrix.py:538`, `"row_0": HAND_CLASSES[0]`.
`HAND_CLASSES` is a different ordering from the matrix's, so the field is derived from the wrong
source. `--check` reproduces the wrong string and therefore cannot see it.

Why this is a blocker rather than a note. The file is a 114,244-byte **headerless** binary; the card
is the only thing that says how to read it, and this phase computed the table rather than importing
GTOpen's precisely so a reader could open the bytes and check. A reader who takes `row_0: AA` and
reads the first 169 floats gets `22`'s row. The card also contradicts itself: the `note` beside
`row_0` states the index formula correctly (I verified all three forms - `AA` 168, `AKs` 167,
`AKo` 155), so the two fields cannot both be right.

Fix is one line plus a card regeneration, inside `approved_scope`. Mark with the bare literal
`[resolved]` when done.

**Lane R, 2026-09-04: [resolved]** Re-derived the finding from the committed bytes before touching
anything - 114,244 bytes, `gtopen_class_index('AA') = 168`, the class at row 0 is `22`, and
`row0 vs AKo` reads 52.65, which is `22`'s figure - so the reviewer's measurement reproduces
exactly. `HAND_CLASSES[0]` is replaced by a new `class_by_row()` that inverts
`gtopen_class_index` itself, refuses if that index does not cover rows 0 to 168 exactly once, and
names **both ends** rather than one, on the reviewer's suggestion: the card now publishes
`"row_0": "22"` and `"row_168": "AA"`, so a reader can check the first 169 floats and the last 169
against the note's own formula. The matrix bytes are unchanged (the `.bin` did not appear in the
diff and the sha256 on the card is the same `d982b854...5779`), and
`generate_preflop_equity_matrix.py --check` reproduces both files. The card grew by 19 bytes, which
stales the export card's `headroom_bytes`, so `convert_preflop_export.py` was re-run to restamp
15775496 to 15775477 and `--check` reproduces again.

**A related hole, reported rather than fixed.** Nothing in the gate runs this script:
`required_gate_commands` in the phase 14 contract is `pytest_derived_chart` and
`generate_derived_chart_report`, and no test in `tests/**` reads `preflop_eq169.bin` or its card at
all. `--check` is the only thing that ever looks, and as the finding says it reproduces a wrong
string. Registering `generate_preflop_equity_matrix --check` as a gate command is a contract edit
and not this lane's to make.

## Non-blocker

### 1. The report labels vacuous the criterion the corrected frozen test now measures 81 times

`reports/active/latest_derived_chart_report.txt`, "The three criteria with no instance in the
committed set":

    vacuous  the no-raise half of the sizing invariant: no committed spot offers hero zero
    raises, so the half of the rule saying such a spot carries no key and makes the
    strategy refuse has nothing to refuse here.

The frozen test corrected in this same range,
`tests/test_spot_vocabulary.py::test_exactly_the_spots_that_raise_carry_a_sizing_entry`, now says of
the same invariant: *"So the no-raise half has 81 instances and is measured here rather than
labelled vacuous."*

Both readings are individually true and I measured both:

    committed nodes whose MENU offers no raise/jam: 0
    raising (action_frequency_pct>0): 168   covered-raising: 81
    spots with >=1 priced class: 168

So the menu reading is vacuous and the `sizes_bb` reading fires 81 times, and the two artifacts use
the same words for different predicates without either saying which. This is the section whose own
closing sentence is *"a vacuous criterion is not a check that passed... a packet counting one would
be claiming coverage the phase does not have"* - here the error runs the other way, telling a reader
a real 81-instance measurement is empty. The report never prints the 168/81 split that would let a
reader tell the two apart; `COMMITTED-SPOTS-THE-BOT-CANNOT-REACH-BY-ITS-OWN-PLAY` already records
that the report owes it. Not held as a blocker because no figure is wrong and the prose is defensible
under its own reading, but the packet must not repeat "vacuous" for this one without the split beside
it.

### 2. 81 committed spots ship as `{}`, and the spot-level half of the invariant is now false and unasserted

    empty entries in the committed sizing JSON: 81
    example: t6/d100/BTN/CO:raise@2.5,BTN:call,BB:raise@7.5 -> {}
    sizing entries: 249   non-empty: 168   spots with no entry at all: 0

Before the correction, `covered - raising == set()` made the spot-level and class-level readings of
"exactly the spots that raise carry a sizing entry" coincide. After it they diverge: 249 spots carry
an entry, 168 raise. The corrected test asserts only the class-level direction
(`{spot for spot, classes in priced.items() if classes} == raising`) plus structure on the 81. The
spot-level direction went from vacuously true to **false**, and nothing asserts it either way.

Separately, the docstring carried over this sentence unrevised: *"Absence is still `sizes_bb`
returning None rather than an empty list, because an empty list is a spot that raises for no price
wearing the shape of a spot that cannot raise."* At the spot level the artifact now ships exactly
that shape 81 times - key present, nothing under it - and the warning has an uncaught instance.

I did **not** judge this a test bent to fit the code, and I want to be explicit about why. The
docstring's argument (menu vs arriving classes) is sound and I verified both halves independently;
the correction adds real structure rather than only moving a literal - all 81 are asserted to face
exactly two raises and to contain hero's own call, and I measured **0 violations** of that shape. A
bent test would have changed 249 to 168 and stopped. What is owed is the retained sentence and the
missing spot-level direction, not a re-litigation of the count.

### 3. The ExecPlan's ruled-numbers list still publishes rank-arm counts under a withdrawn rule

`docs/exec_plans/active/PHASE_14_CHART_CUTOVER.md`, "The numbers a lane may use, and where each is
ruled" - a section headed *"No lane invents a count"* - lists rank-arm figures "over closed spots".
Against the committed report's own rows:

| partition | ExecPlan rank arm | report rank arm |
|---|---|---|
| whole set | 64/206 over 83 closed | 181/433 over 208 |
| raises 2 | 32/33 over 53 | 149/260 over 178 |
| LJ | 1/9 over 1 | 75/96 over 32 |
| HJ | 3/14 over 2 | 23/59 over 36 |
| CO | 6/21 over 5 | 22/72 over 32 |
| BTN | 9/33 over 12 | 14/66 over 33 |
| SB | 15/54 over 25 | 17/65 over 37 |
| raises 0, raises 1, BB | match | match |

Every suit-arm figure in the list matches the report exactly; only the rank arm moved, which is
consistent with the paragraph directly beneath announcing that decision 54 withdrew the arm's
restriction on 2026-09-03. The bullet is self-labelled "over closed spots", so it is not lying about
what it measured - but it sits under a heading offering numbers a lane may use, and the seven rows
are numbers no lane may now use. The ExecPlan was rewritten in this range (`35730df`, "Bring the
ExecPlan up to where the build actually is") and this section was not touched.

Sharper, and the part I would fix: the withdrawal paragraph's own replacement figure is wrong.
It reads *"Scored over every spot it reads 149 against 260 and passes wide."* The report's whole-set
row is **181 against 433**; 149 against 260 is the report's **raises-faced-2** row. So the one figure
offered as the post-withdrawal truth names a partition rather than the whole set.
`reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md:4085` gets this right - *"No
partition rows are typed here"* - which makes the ExecPlan the only place carrying them.

### 4. Two measured gate holes live only as YAML comments, not in `backlog.yml`

The canary-debt triage in `verification/mutations.yml` struck six inherited items. Four are moot and
struck correctly. Two are struck as FINDINGS, and both are real:

- The generator's per-partition validation loop could validate the **first partition only** and every
  gate command would stay green. I confirmed the mutation is writable: `    for figures in
  arms.values():` occurs exactly **1** time in `scripts/generate_derived_chart_report.py`.
- The jam-section test *"only requires a weight between 0 and 100 printed at a spot outside the
  committed set"*, so reading the raise weight instead of the jam weight would satisfy it. I
  confirmed the one-token surface exists: `_menu_weights(node, ("jam",))` at line 752 beside
  `_menu_weights(node, ("raise", "jam"))` at 766.

**Declining to write either canary was right**, and I want that on the record separately from the
filing complaint. `check_gate_bite` requires every canary to be killed by its `must_fail` commands;
a canary the lane had already measured would survive is a red stage 7 rather than evidence. Writing
them would have been the worse choice.

What is owed is the filing. `AGENTS.md` says an alignment item *"must be filed in `backlog.yml`
rather than left in the note"*, and I searched: neither hole appears there (`grep -in "per
partition|first partition|validate_group_discrimination|jam weight|_menu_weights" backlog.yml`
returns only pre-existing unrelated lines). They are recorded as comments in the same block that
says *"An aspirational comment nobody re-reads is how this block came to carry five stale counts, so
nothing is left here as inherited intent"* - which is precisely where they were left.

### 5. Two hand-typed counts survive in the rewritten generator's prose

Scanned every non-f-string literal in `scripts/generate_derived_chart_report.py` with an AST walk.
Two carry counts nothing re-derives:

- line 1203: `"And 249 nodes are not self-evidently 249 keys..."` - true today (I measured 249 nodes,
  249 distinct keys, 0 invented, 0 dropped), and the derived line three rows below prints the same
  figures. The prose can go stale while the derived line moves.
- line 1251: `"The ten big-blind squeeze spots passed this clause BECAUSE..."` - true today
  (`derivation:big-blind-squeeze-spot` bucket = 10, measured).

Both are on the open `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`, in a file this stage
rewrote from scratch. Every other count in the report that I could re-derive is derived and correct
(see the verification list at the end).

### 6. The ruling named five test paths; six were written

`verification/freeze.lock` re-hashes six files, and the scope log's own 2026-09-04 entry says
*"the next `check_test_freeze` reports six files"*. The sixth,
`tests/test_spot_vocabulary_report.py`, was opened on the lane's own reading that Taylor's 2026-09-03
ruling *"covers this one on its own terms... it folds in rather than becoming a second ask about an
identical question"*.

I think the reasoning is right - it is the same claim in the same words as the
`test_spot_vocabulary_downstream.py` correction, and I measured the shared premise directly (**22**
committed keys name a seat twice, **0** keys carry more than two raises) - and the coordinator brief
already counts it among the nine, so nobody was surprised. Recording it only because a test edit is
frozen into data, and the extension of a ruling to a path the ruling did not name was decided by the
lane rather than asked.

`test_functions` counts are unchanged in all six (14, 46, 8, 31, 27, 7), so no test was deleted.

## Alignment

### 1. The exposure rows publish one figure under two labels, and the test freezes it there

Every row in "Multiway exposure, per committed spot" prints `exposure` and `multiway` as the same
number, because the f-string at `scripts/generate_derived_chart_report.py:1261` interpolates
`multiway` into both:

    f"  {key}  exposure {multiway:.4f}  multiway {multiway:.4f}"
    f"  heads-up {folded + heads_up:.4f}"

    t6/d100/BB/BTN:raise@2.5,SB:raise@7.5  exposure 0.1750  multiway 0.1750  heads-up 99.8250

This is not a stage-6 slip - `tests/test_derived_chart_report.py:477` requires it
(`assert float(multiway) == pytest.approx(float(exposure), abs=0.0002)`), so the stage cannot fix it
without writing a frozen test. Filing it as drift rather than as a finding against the build.

The drift is that the section's prose promises a split - *"The two are the halves of one mass and add
to a hundred, so a row publishing exposure alone could be over any denominator at all"* - and what
is printed is one gated figure, a duplicate of it, and its complement. The two the prose names do
add to a hundred; a reader adding the three printed columns gets 100.175. And the report warns two
sections later that *"this phase has already shipped one figure under two meanings"*, which is what
the row does under two labels. Whether the second column was meant to be a genuinely different
measurement - the un-renormalised exposure with hero's cold call left in, say - I do not know and am
recording as a **suspicion, not a measurement**; `terminal_split_pct` returns
`(folded, heads_up, multiway)` and `multiway_exposure_pct` is index `[2]`, so as the code stands
they are the same quantity by definition.

### 2. Four files now sit exactly on their cap, with the corrections having bought the lines back

    tests/test_sample_comparison.py                 700 -> 700
    tests/test_spot_vocabulary_downstream.py        700 -> 700
    tests/test_derived_chart_report_validators.py   700 -> 700
    src/.../vocabulary_measures.py                  499 -> 500

The three test files were already at exactly 700 before this stage; the nine corrections added
docstring prose and paid for it by reflowing comprehensions. **I verified mechanically that those
reflows changed nothing.** I tokenised each of the six re-opened files at `c45013b` and at HEAD,
dropped layout, comments and docstrings, and diffed the token streams: every surviving difference is
one of the nine ruled corrections and there is nothing else. The reflows contributed **zero** token
differences.

The drift is that a test file pinned at exactly its cap cannot take the next honest docstring
correction without a split, and this phase has now needed nine such corrections. The Contract
Amendments section makes the identical argument about the 300-line contract cap; the same squeeze
is now on `tests/**` and on `vocabulary_measures.py`.

## What I measured, for the record

Independently re-derived, none of it read out of a repo report:

- Chart: 249 spots, 33,969 export nodes, census `33362 / 348 / 10`, raises-faced `5 / 25 / 219`,
  18,431 cells all at non-zero reach, 44 spots rounding to zero in ppb.
- 168 raising / 81 not; all 81 face exactly two raises and contain hero's own call, 0 violations.
- 22 committed keys name a seat twice; 0 keys carry more than two raises; max raises in a key = 2.
- Decision 48: BB keys facing exactly one raise are exactly the five
  `t6/d100/BB/{LJ,HJ,CO,BTN,SB}:raise@2.5`. 23 BB keys carry a call somewhere, and none of those
  faces exactly one raise - so the withdrawn `":call" in key` reader was false and the set equality
  that replaced it is the ruled clause, stated so it cannot pass by naming nothing.
- Self-play cross-reference: 61 gap spots; overlap on **keys 0**, on **shapes 7**; inventory reads
  7 SEEN / 54 NEW; `seen == shared` exactly; all 7 are four-bet spots (3 raises in). The committed
  `latest_sample_refusal_inventory.txt` agrees (61 rows, 7 `yes`, 54 `NEW`), so it is not stale.
- Match rates: Pluribus 475 scored, 475 drawn, 0 undrawn, 9 diverged, gap 1.8947. Humans 2,434
  scored, 2,432 drawn, **2 undrawn**, 40 diverged, gap 1.6529, `stranded` empty. The two undrawn
  carry substitutions `(2, 13.5, 7.5)` and `(1, 13.25, 7.5)` - exactly the 13.5 and 13.25 the
  docstring names. Every figure in that corrected docstring checks out to the digit.
- Validators boundaries: `monotone` is a pure test-local fixture, unchanged by this diff, giving
  `55 = 71.2`, `44 = 68.0`, `33 = 64.8`. The old literals (44 at 90.0, 33 at 91.0) violate the
  ladder against `55` on a full grid, so `== {0}` and `== 1` were both false as authored; the new
  literals sit inside the ladder and preserve all three stated boundaries - a gap of exactly 1.0
  counts 0, 1.01 counts 1, and the 27-point case counts 1 with `55` lifted to keep it above `44`.
  A repair, not a bend.
- The three new canaries, effects measured **in memory** (no file written, no mutation planted):
  squeeze clause dropped at the call site → **249 to 259** spots and the squeeze bucket **10 to
  gone**; `COMMITTED_RAISE_DEPTH = 3` → **249 to 2,456** and the depth bucket **33,362 to 29,105**,
  with the clause dropped outright committing **18,789**; merge seat inverted → merged cells
  **165 to 276** at **20 to 5** spots. Every number in all three descriptions is right.
  Judgement on the three: the squeeze canary is aimed at the `exclusion_code` call site rather than
  inside the predicate specifically so a frozen test reading the predicate back cannot kill it, and
  it moves 10 spots - that is the strong shape. The depth canary attacks a constant and its own
  description says so plainly, naming `generate_derived_chart_report` as the load-bearing kill; it
  moves 2,207 spots. The merge canary moves 165 cells and deliberately does **not** name the report,
  stating that the report's key-by-key comparison is blind to a cell move - which I confirmed is
  true, the spot set is unchanged at 249 under it. None of the three is killable by a constant
  readback alone.
- Equity matrix: 114,244 bytes = 169x169 float32 with no header; diagonal exactly `0.5` at all 169;
  max `|e[i][j]+e[j][i]-1|` = 2.98e-08. All six of the card's `checks` figures reproduce from the
  bytes to the digit.
- The `88` vs `AKo` override. **The lane is right and the published 52 does not belong to `88`.**
  Checked with my own pure-Python Monte Carlo, my own 7-card evaluator, no repo code, 120,000 boards
  per case: `22` vs `AKo` **53.25**, `88` vs `AKo` **55.84**, `AA` vs `KK` **81.21**, `AA` vs `72o`
  **87.48**, `AKo` vs `QQ` **42.69**, `AKs` vs `QQ` **46.15**. Mine are single suit layouts and the
  card's are class averages over the ordered combination pairs, which is why they differ by a few
  tenths in both directions; the ordering and the magnitudes agree throughout. `88` vs `AKo` is
  nowhere near 52 on any reading. Overriding the anchor was correct, and the card says so in the
  right place rather than quietly.
- `numpy>=2.0` is in the **dev** group only, with a comment saying why; `dependencies = []` is
  untouched.
- Cutover ledger balances both ways: 21 + 65 = 86, 21 + 228 = 249.
- The report has 26 `##` sections, which is the count the mutations.yml coverage note claims.
