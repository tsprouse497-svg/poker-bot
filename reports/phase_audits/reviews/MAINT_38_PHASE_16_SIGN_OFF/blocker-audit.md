# Phase 16 sign-off: audit of the 18 unmarked blocker bullets

Read-only audit for MAINT-38. I wrote none of phase 16 and none of its review notes. Tree: the
`maint-38` worktree at `2d90379` (main). Nothing was run that writes files: no `run_verify.py`, no
`check_gate_bite.py`, no pytest, no `git checkout`. Four throwaway `python -c` measurements were run
against the repo's own modules with `PYTHONDONTWRITEBYTECODE=1`; each is named where it is used.
This file is the only file written.

The 18 hits were reproduced first by re-implementing `scripts/loop_stage.py::unresolved_blockers`
(strip, `- ` prefix, no `[resolved]`, inside `## Blocker`) over every note in
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/`. Same 18, same lines.

Classes: **A** = list item inside another finding's prose; **B** = real blocker, fixed, never
marked; **C** = still open, or closed by a ruling rather than a fix.

## Table

| note | line | class | evidence |
| --- | --- | --- | --- |
| stage-03-decisions-poker.md | 97 | A | Sub-bullet of the `[resolved]` blocker at :35; owner's fix is in the committed sample |
| stage-03-decisions-poker.md | 100 | A | Same owner |
| stage-03-decisions-poker.md | 101 | A | Same owner |
| stage-04-repair-verification.md | 40 | A | Sub-bullet of paragraph blocker B1 (:28); B1 fixed at `e67104d` |
| stage-04-repair-verification.md | 48 | A | Same owner |
| stage-04-tests-poker.md | 37 | A | Sub-bullet of paragraph blocker B2 (:32); B2 fixed at `23e9c8a`, finished at `e67104d` |
| stage-04-tests-poker.md | 41 | A | Same owner |
| stage-06-build-mechanical.md | 14 | B | `canonical_hole_cards` minimises over the stabiliser, `dbffd03`; 0 of 1,176 unstable re-measured |
| stage-06-build-mechanical.md | 66 | B | `servable` counted after both gates plus a guard, `abc6603` |
| stage-06-build-mechanical.md | 86 | B | Server fields read through refusing `answered`/`numeric`, `abc6603` |
| stage-06-build-poker.md | 97 | A | Evidence list inside paragraph blocker B2 (:86); B2 fixed at `dbffd03` |
| stage-06-build-poker.md | 98 | A | Same owner (a wrapped line of the :97 list) |
| stage-06-build-poker.md | 100 | A | Same owner |
| stage-06-build-poker.md | 101 | A | Same owner |
| stage-06-build-poker.md | 102 | A | Same owner |
| stage-06-cells-poker.md | 41 | C | Closed by decision 21, marked as Taylor's ruling, not by a fix; the reporting duty it sets is met |
| stage-08-review-mechanical.md | 153 | B | `[resolved]` is there, but on :156 not :153; backlog sweep done at `7254a50` |
| stage-08-review-poker.md | 45 | B | Asked for a packet paragraph; packet :57-81 has it; decision 25 (Taylor) sets how |

Counts: **A 12, B 5, C 1.** Sweep for paragraph blockers the parser cannot see: **12 found, all
B** (table at the end).

## Per-item detail

### stage-03-decisions-poker.md :97, :100, :101 (A)

These are wrapped lines of the "Resolved 2026-09-10 by the coordinator" paragraph. Some are
rank-family bullets (`- **rainbow, dry high-card**`, `- **two-tone, paired**`,
`- **monotone, connected**` at :97-:101 of the owner's text) inside the proposal of the blocker
that starts at :35. That blocker is marked `- [resolved]` on its first line.

Owner re-checked in the current tree rather than taken from its own resolution paragraph. Decision
6 item 4 (`PHASE_16_POSTFLOP_BETTING_DECISIONS.md:823-837`) rules the rank axis dry-high / paired /
connected and names `Kc7d2h` and `9c8c7c`. The committed sample is
`data/artifacts/postflop/sample/{rainbow-dry-high-*,two-tone-paired-donk,monotone-connected-cbet}.json`
on boards `Kh7d2c` (canonical form of `Kc7d2h`), `8c8d3c` and `9c8c7c`. Monotone-dry-low is not
committed. The owner is fixed.

### stage-04-repair-verification.md :40, :48 (A)

Both are the two "measured consequences" bullets of **B1** ("Every heads-up fixture in the phase
describes a table that cannot be dealt"), a bold paragraph with no marker. B1 is fixed:
`tests/test_postflop_betting.py:82-104` (`seated`) now lists all six seats, marks folded seats
`folded=True`, gives the small blind its own 50, and derives stacks as `STARTING_STACK -
committed_total`, so every seat starts at 10,000 and `len(stacks)` is 6. Its docstring names the
old convention and why it was wrong. `tests/test_postflop_query_recording.py:280-293` uses the same
`seated`. Introduced by `e67104d` ("Seat six players at the table, and take decision 14 to Taylor"),
confirmed with `git log -S`. It was consolidated as `[resolved]` in `stage-04-tests.md`.

### stage-04-tests-poker.md :37, :41 (A)

The two fixture bullets of **B2** ("Two frozen fixtures build a `StrategyQuery` the repo's own
validator rejects"), a paragraph with no marker. Fixed: every heads-up fixture now builds its pot as
`sum(state.committed_total ...)` inside `seated`, so pot and seats cannot disagree by
construction. First repaired at `23e9c8a`; `e67104d` replaced the convention after the repair
verification's B1. Consolidated as `[resolved]` in `stage-04-tests.md`.

### stage-06-build-mechanical.md :14 (B): `canonical_hole_cards` not canonical

Fixed at `dbffd03`. `src/poker_training_bot/solver_artifacts/postflop_isomorphism.py:139-165` now
returns `min(...)` over `board_suit_maps(table)`, i.e. over the whole stabiliser. Re-measured here
with the repo's function: for all 1,176 hero combos on `Kh7d2c`, `8c8d3c` and `9c8c7c`, under all
24 suit relabellings of board plus hand together, **0, 0 and 0** combos gave more than one class
(the note measured 0, 910, 1,131). Distinct classes per board: **1,176, 721, 344**. That matches
the note's cell sizes, so the table's labels and the committed labels agree.

### stage-06-build-mechanical.md :66 (B): fabricated `servable` column

Fixed at `abc6603`. `scripts/generate_postflop_betting_report.py:1436-1448` increments `arrivals`
before the covered-line and fetched-board gates and `servable` only after both.
`check_servable_never_exceeds_arrivals` (:311) refuses a column above arrivals or one that does not
sum to `answerable`, and it is called at :1740. Ranking goes through `servable_ranking` (:1844).

### stage-06-build-mechanical.md :86 (B): fail-open server reads

Fixed at `abc6603`. `postflop_solve_driver.py:460` and `:488-489` read `arena_mb`, `exploit_pct`
and `iteration` through `numeric`. That calls `answered` (`postflop_transport.py:68-78`), which
raises `SolveDriverError` on a missing field, and `numeric` also refuses a non-number or a bool.
The remaining `.get` calls in the driver (:257-316) read our own config, not a server answer.

### stage-06-build-poker.md :97-:102 (A)

The five "impossible flop lines" in **B2**'s evidence ("The key can name a flop node no dealer can
produce"), a paragraph with no marker. :98 and :102 are wrapped lines of those bullets. B2 fixed at
`dbffd03`: `postflop_action_order` now has a production caller at
`solver_artifacts/postflop_key.py:356`, inside the reachability walk at :345 onward. The committed
data is the check that matters. The button's continuation-bet cell is keyed
`f/b:9c8c7c/.../BTN/.../f:BB:check/...` (`sample/monotone-connected-cbet.json`), not `f:none`, and
every `f:none` key in `index.json` belongs to BB, the seat first to act. `stage-06-build.md:91-100`
rebuilt all five impossible cells and saw each one refuse. I did not repeat that rebuild.

### stage-06-cells-poker.md :41 (C): the 99.88% continuation bet

A real blocker. By its own words ("A human ruling is what closes this, not a re-solve") it could
only close by ruling. Closed by **decision 21**, `PHASE_16_POSTFLOP_BETTING_DECISIONS.md:2277-2320`,
headed "Ruled by Taylor, 2026-09-21. `frozen-into-data`". Recorded at `671bd3c`, whose message
says "Taylor ruled two things tonight". The ruling accepts the flop-leading caller and keeps the
cells as solved. It rejects re-solving without the out-of-position flop bet.

The obligation the ruling sets is met in the current tree: `reports/active/latest_postflop_betting_report.txt:283-300`
prints the other seat's line beside hero's frequencies ("plays that line 47.32% of the time, so
52.68% of its range does something else"), with the composition shift. `PHASE_16_POSTFLOP_BETTING.md:235`
and `:302` carry the pairing too.

Two caveats. (1) Decision 21 quotes none of Taylor's words, while decision 24 does. So "Taylor's"
rests on the heading, the commit message and the ExecPlan (`docs/exec_plans/completed/PHASE_16_POSTFLOP_BETTING.md:416`),
not on a quote. (2) No later note marks this bullet. `stage-06-build.md` consolidated the other
five stage-6 blockers and does not mention it. `stage-09-audit.md:321-326` saw it unmarked and
said so. The poker defect stays as ruled: the committed c-bet cell answers a node that a 52.68%
lead has already filtered.

### stage-08-review-mechanical.md :153 (B): backlog closures never swept

The bullet opens `- **Open.**`, and its `**[resolved]** at 7254a50` is on :156, a continuation
line, so the parser misses it. Fixed. Measured in `backlog.yml` now: `V2-POSTFLOP-STRATEGY`,
`POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`, `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`,
`ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS` and `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` are `done`.
`POSTFLOP-UNBEATABLE-EARLIER-STREETS` and `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` stay `deferred`.
Those two refusals are the stage-8 reviewer's verdicts (`stage-08-review.md:102`, `:133`), not
Taylor's rulings. Their reasoning is in the packet (`PHASE_16_POSTFLOP_BETTING.md:370-387`). The
finding asked for the sweep, and the sweep happened.

### stage-08-review-poker.md :45 (B): the seam is at hero's first flop action

The finding asked for "a paragraph in the stage-9 packet". `PHASE_16_POSTFLOP_BETTING.md:57-81`
carries the coverage number (40 of 22,100, 0.1810%, about once in fourteen thousand hands), the
closure fact (none of the eleven successor nodes is committed or indexed), and strikes the "bets a
flop and then refuses every turn" sentence. Re-measured: canonicalising all 22,100 flops with
`postflop_key.canonical_board` gives 1,755 classes, with `Kh7d2c` 24, `8c8d3c` 12, `9c8c7c` 4, for
40 in all. **Decision 25** (Taylor, `:2424`) decides that the phase closes on machinery. The fix
itself is the packet text, so this is B. `stage-08-review.md:54-61` marks it `[resolved]` in the
consolidated note, just not in its own file.

## Sweep: paragraph blockers the parser cannot see

Every `## Blocker` section in the 22 notes was listed by finding head (`**`, `###`, `- **`,
numbered). Blockers in `stage-01-*`, `stage-02-*`, `stage-03-*`, `stage-06-build.md`,
`stage-08-review*.md` (except the two above) and `stage-09-audit.md` all carry `[resolved]` on their
first line. `stage-07-gate.md`, `stage-10-closeout.md` and `stage-11-advance.md` say "None.".
`stage-01-contract.md:360` ("A form note") and `stage-09-audit.md:168` ("Note on shape") say they
are not findings. These 12 paragraph blockers have no marker:

| note | finding | class | evidence |
| --- | --- | --- | --- |
| stage-04-tests-mechanical.md | B1 report tests assert nothing | B | `TestThisFileSOwnPredicatesCanFail` at `tests/test_postflop_betting_report.py:613`; `23e9c8a` |
| stage-04-tests-mechanical.md | B2 weight-bounds canary cannot bite | B | Witness `[1.5, -0.5, 0...]` at `tests/test_postflop_artifact.py:380`, sibling `[1.0] * len(row)` at :399; `23e9c8a` |
| stage-04-tests-mechanical.md | B3 non-canonical-board test | B | `a_different_dressing` keeps the class, `tests/test_postflop_artifact.py:339-359`; `23e9c8a` |
| stage-04-tests-mechanical.md | B4 migration sweep unstated | B | Figures recorded; repair verification re-measured 50/23/3/20/3/17; `stage-04-tests.md` marks it. Not re-derived by me |
| stage-04-tests-poker.md | B1 `3c2d` negative control | B | `Jd8d` at `tests/test_postflop_betting.py:613-631`, docstring names the old hand; `23e9c8a` |
| stage-04-tests-poker.md | B2 fixtures the validator rejects | B | See :37/:41 above; `23e9c8a` + `e67104d` |
| stage-04-tests-poker.md | B3 nothing requires the mixture | B | `TestTheCommittedMixtureIsPlayedRatherThanPurified`, `tests/test_postflop_query_recording.py:305-392`, all three tests the note asked for; `23e9c8a` |
| stage-04-tests-poker.md | B4 three-handed flop | B | `TestAThreeHandedFlopRefuses`, same file :415-478, with a heads-up control; `23e9c8a` |
| stage-04-repair-verification.md | B1 table cannot be dealt | B | See :40/:48 above; `e67104d` |
| stage-04-repair-verification.md | B2 decision 14 misclassed | B | Decision 14 now `frozen-into-data` (:1704); `e67104d` reclassed and halted; Taylor then ruled 0.05 (`postflop_key.py:100`) |
| stage-06-build-poker.md | B1 size in bb against a pot in chips | B | `_amount` converts a pot fraction via `menu_size_chips(..., query.pot)`, `strategy/postflop_betting.py:464-491`; `price_menu` refuses off-menu sizes, `postflop_sizing.py:123-162`; `dbffd03`. Third sub-finding only half fixed, see Non-blocker |
| stage-06-build-poker.md | B2 impossible flop nodes | B | See :97-:102 above; `dbffd03` |

## Blocker

None.

## Non-blocker

- The 18 hits are a parser artefact plus a record that was never consolidated, not open work. Of
  the 18, 12 are evidence lines (A) and 5 are fixed. The one C is closed by a ruling attributed to
  Taylor. The parser defect is already filed as `REVIEW-QUEUE-COUNTS-EVIDENCE-BULLETS-AS-BLOCKERS`
  (deferred, `contract-update`). `stage-01-contract.md:360-376` and `stage-09-audit.md:168-174`
  describe it too. `stage-08-review-mechanical.md:153` is a different shape: the marker is present
  but on a continuation line. A parser fix that only looked at the first line of each bullet would
  still miss it.
- `stage-09-audit.md:321-326` already found that four of these notes had unmarked blockers, and
  that the ExecPlan's "every blocker ... is marked resolved" was false. That was stage 9, before
  close, and phase 16 closed with the notes unchanged. Snapshot notes should stay as written, per
  `AGENTS.md`'s record-keeping stance. A sign-off record like this one is the right place to close
  them.
- Decision 21 is recorded as Taylor's but quotes none of his words, unlike decision 24. If Taylor
  signs off, confirming decision 21 in his own words would close the only item here that rests on
  attribution.
- The third sub-finding of `stage-06-build-poker.md` B1 (the raise menu inferred from which nodes
  are committed) was moved to a non-blocker in `stage-06-build.md:232` onward as "half repaired, the
  remaining half is filed". `raise_fractions` now comes off the cell's own actions
  (`strategy/postflop_committed.py:143`, `:203`), but the note says a 62.03%-of-pot raise still
  cannot be keyed. I did not re-measure that half.
- `stage-03-human-gate.md` has three consecutive `## Non-blocker` headings (:740, :742, :744).
  This is harmless to the parser and is only a form note.

## Alignment

- `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:229-231` still lists
  `POSTFLOP-UNBEATABLE-EARLIER-STREETS` as Closed, but `backlog.yml` holds it `deferred`, a refusal
  the packet explains. `AGENTS.md` says a completed contract that a later fact contradicts is
  amended. This is filed as
  `A-CONTRACT-CLOSED-LIST-ASSERTS-A-CLOSURE-ITS-PHASE-REFUSED-ON-EVIDENCE` (deferred,
  `contract-update`), so it is already owned. It is not a sign-off blocker, but the completed
  contract asserts something false until that entry lands.

## What I looked at outside the brief, and what I held back

Outside the brief: I re-derived the owning finding's fix for every A item, not only the parser
hits. I ran the whole-note sweep for unmarked bold-paragraph blockers and found 12. I checked the
committed spot keys in `index.json` and the sample files, not just the code. I re-counted flop
coverage (1,755 classes, 40 of 22,100). I checked the contract's Closed list against the backlog
statuses, and checked whether decisions 21 and 25 carry Taylor's own words.

Held back: I did not re-derive the roughly 90 blockers already marked `[resolved]` in the other
notes; I only confirmed that each carries the marker. I did not rebuild the five impossible flop
cells, re-run the 20,000-hand simulation, or re-measure the raise sub-finding's remaining half. I
relied on the notes and the current code shape for those. I did not re-derive decision 14's chip
bands or the stage-4 migration-sweep figures.
