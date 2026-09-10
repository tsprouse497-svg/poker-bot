# Stage 3 review: the contract fold-in rewrite

Reviewer: R3, read-only. Not C1. Lane worktree `~/projects/poker-bot-worktrees/phase-16`, branch
`phase/16-postflop-that-can-bet`, working tree uncommitted, previous contract at `b1f5667`.

## Method

**What I compared.** The working-tree
`docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` (299 lines) against
`git show b1f5667:docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` (289 lines), and both against
`reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` (all thirteen `Answer:`
blocks read in full, plus the machine note under decision 11),
`docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md`,
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-02-decisions-poker.md`, and
`backlog.yml`. I never ran `git checkout`, `git stash`, `git restore` or `git reset`; the old
version came out of `git show` into a scratch file.

**How I diffed obligations rather than lines.** The whole file was re-wrapped, so a line diff is
noise. I did three passes instead.

First, an obligation inventory: I walked the old contract bullet by bullet and wrote down every
falsifiable predicate in it (61 of them), then located each one in the new file or marked it
missing. A predicate that survived only as a softer sentence was to count as missing. None did.

Second, a mechanical token diff as a backstop against a predicate I read past: every backticked
identifier, every `ALL-CAPS-DASH` backlog id and every numeral in each version, set-differenced.
Eleven tokens leave the old file. Three of them (`frozen-into-data`, `runtime-reversible`,
`contract-update`) are the stage-3 bookkeeping the rewrite legitimately supersedes; two
(`LJ open, BTN call`, `BTN open, BB 3-bet, BTN call`) are illustrative prose; `SeatAction(0, "bet")`
and `check_file_sizes.py` are named-source detail whose obligation survives in the sentence around
them; `0`, `7`, `8`, `23` are digits inside dropped rationale. No backlog id and no code identifier
is lost. Every ALL-CAPS id the new file names exists in `backlog.yml` (19 of 19 checked).

Third, the thirteen rulings from the ExecPlan's "What the fold-in rewrite has to absorb", each
traced back to its `Answer:` block in the decision list and forward to the criterion that carries
it, checking the conclusion rather than the neighbourhood of it.

**What I measured rather than accepted.** Brute-forced over all 52-card three-card boards:
22,100 boards, **1,755** suit-isomorphism classes, orbit sizes 24/12/4 at 286/1,170/299 classes,
rainbow **455** classes and 8,788 boards (39.76%), two-tone 1,014 and 55.06%, monotone 286 and
5.18%, paired-and-trips 3,796 (17.18%), **paired-monotone 0**. Re-parsed the 499 raw PHH hands in
`data/samples/public_corpus/corpus_hands.jsonl`: 409 opens with median 2.25bb of which **405
(99.0%)** fall in 2.0-3.0bb, 87 3-bets with median 9.25bb of which **41 (47.1%)** fall in
6.0-9.0bb, 19 4-bets+ with median 25.35bb; and separately **259 of 499 hands see a flop** with
**20 multiway (7.7%)**, 92.3% heads-up. Checked the 20% band endpoints by arithmetic (2.5 x 0.8/1.2
= 2.0/3.0, 7.5 x 0.8/1.2 = 6.0/9.0) and decision 11's stack-off claim by working the two deepest
lines through the ruled menu (`75 125 125` invests 81.47 leaving 16.03 of 97.5, 16.4%;
`33 125 125` leaves 44.33, 45.5%; neither reaches the 85% snap). Read out of the repo rather than
out of a document: `DIRECTORY_BYTE_LIMITS` = `("data/artifacts", 20 * 1024 * 1024)`, so **20 MiB**
is the right label and the new contract's is; `DECISION_AUDIT_SCHEMA_VERSION = 3`;
`_PREFLOP_HISTORY_ACTIONS = ("fold", "check", "call", "raise")`; `self_play_reference.py:57` is
`token.startswith("t") and token.count("/") >= 3` and raises on an empty result; **six** mutations
in `verification/mutations.yml` pin `postflop_fallback.py` or `composite.py`, five witnessed by
`pytest_postflop_fallback` and one (`fail-closed-can-invest-again`) by `pytest_engine_fidelity`.
Every number stated in the contract that I could reach reconciles.

**Commands run.** `uv run python scripts/check_file_sizes.py`, `scripts/check_contracts.py` and
`scripts/check_scope.py` all exit 0 with no output. `check_file_sizes` caps
`docs/phase_contracts/*.md` at 300 lines and the contract is at 299, so it passes with one line
spare. I did not run the full gate; it is red by design here because
`pytest_postflop_betting` and `generate_postflop_betting_report` are declared in the frontmatter and
not registered in `COMMANDS`.

**What I did not check.** I did not verify decision 6's byte-budget arithmetic (the 7,740,095-byte
lean-JSON unit, the 14.76 MiB per node-line, the 8-to-14-line index estimate); the stage-1 numbers
review already held the stage over that material and none of those figures is quoted in the new
contract. I did not re-derive MAINT-26's solve timings, arena figures or iteration counts, which
are machine measurements I cannot reproduce. I did not review the ExecPlan's own diff beyond the
cross-references I was asked about, and I did not read stage-01-contract.md or stage-02-decisions.md
in full.

**Headline.** No obligation from the old contract is gone. All thirteen rulings landed. Two
blockers, both about obligations that are *absent* rather than deleted: one the rewrite created by
stating a split the ruled design cannot produce, one it inherited and did not fix.

## Round 2, 2026-09-10

The contract changed twice after my first read. Both blockers are fixed and I am resolving them.
Nothing new holds the stage. One round-2 cut went further than rationale and is a non-blocker
below, so the writer's claim that nothing falsifiable was cut is very nearly right rather than
right.

**What I compared this pass.** The working-tree contract, still 299 lines, against the exact bytes
I reviewed in round 1, which I had kept in scratch, using `git diff --no-index --word-diff`.
Nothing is committed, so that was the only way to see round 2's edits apart from the fold-in
itself. I re-read every changed criterion in place rather than only in the diff, re-read decision 6
item 4 and decision 4, read all four new `backlog.yml` entries in full, and re-ran the three
checks, which still pass. Round 2 removed no backlog id and no code identifier, confirmed off the
word diff.

**Blocker 1 is satisfiable now, and I checked the three things you asked.** The table at lines
182-187 carries two causes: "no cell for this board or line", which is never-solved and
solved-but-rejected together with the reason given, and "in the index but not fetched on this
machine". Both are decidable offline from the committed index alone - the first is the absence of
an entry, the second an entry whose object is not local - and together they are exhaustive and
mutually exclusive for a miss. That is decision 4's second exit taken exactly, and it keeps
decision 6 item 8's actual requirement, which was only that the fetched cause never be pooled with
never-solved.

The campaign count contradicts neither constraint. Decision 6 item 3's "one entry per solved spot"
and the index criterion's "**Every entry** ... the digest of the stored object" are both statements
about entries; a scalar in the index header is not an entry, adds no entry, and needs no stored
object. Moving it there from "its run record" was the right call, and it is exactly the difference
between a header field and a new committed path decision 6 never ruled. On byte budget: the index
is estimated at 1.14 to 2.02 MB per preflop line, so one integer is below the precision of the
estimate rather than inside its margin.

On whether stage 4 can still freeze a three-way split from either place alone, no. The refusal
criterion says "exactly two causes" and names them; the Evidence list says "by the **two table**
causes" and lists the campaign count separately as a figure. Both carry the word two, and the
refusal criterion pre-empts the mistake in terms - "How many cells the campaign rejected above 1%
of pot is a report figure below, not a third cause here." A stage-4 author would have to read past
"two" in both places.

**Blocker 2 is fixed and the test is gate-failable.** Lines 71-77 state it as one of "two more
tests run in the gate": on a two-tone board a flush-draw combo does not receive the strategy of the
same ranks without the draw. That is an assertion with a witness - pick the board, pick the combo,
pick the same ranks without the draw, compare - not a description. The compressed reasoning,
"hero's two cards being permuted by the board's own map", states the correctness property that
makes the test necessary, and the cited `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`
carries the diagnosis the line has no room for. That is the right split of a long argument against
a short criterion.

**The three non-blockers you acted on all verify.** The vacuous label is conditional now ("any
vacuous one labelled"). The Evidence list carries "the committed configuration was solved twice,
the two strategies compared, and whether they were byte-identical", which gives the halt a surface:
a report saying not-byte-identical beside a phase that did not halt is now a visible contradiction.
The sample criterion names `Kc7d2h` and `9c8c7c` with stage 4 picking only the third, and I checked
the assignment rather than took it - `Kc7d2h` is rainbow and dry-high, `9c8c7c` is monotone and
connected, so the cell left for stage 4 is two-tone paired, the only one remaining. Decision 6 item
4 at line 775 now reads "Stage 4 picks the specific board inside a split and nothing else, and it
picks **one** of the three", so contract and decision list agree. The ExecPlan reads "Six mutation
canaries" and six is what `verification/mutations.yml` holds, one witnessed by
`pytest_engine_fidelity`.

**The compression re-check.** I walked every clause round 2 removed - seventeen by my count too,
plus about six rewordings that change no content. Sixteen of the seventeen are rationale,
provenance, or a mechanism a cited backlog id carries in full: the twice-declared history, the
four-routes fact, "so a cell stays findable", "for the same cost", "rather than inheriting them",
the decorative-gate aside, "rather than the last thing checked", "A predicate, not a count", the
phase-13 canary provenance, the self-play grouping mechanism, the 130-byte LFS pointer figure,
"checking it out discards the work being verified", and the rest. Two are safe for a reason worth
writing down rather than by inspection. "Paired-monotone is impossible" no longer does any work now
that two boards are named and the third cell falls out by elimination. "; none can be recomputed
inside the gate" is covered by the non-goal at line 44, which already requires the gate to pass
with no GTOpen and no network. Dropping the 130-byte figure is an improvement rather than a loss,
by this repo's own rule about figures quoted into prose.

One is not rationale. It is the non-blocker headed "the key-precedence clause" below.

**You were right to decline the Scope sentence at lines 35-36, and it is not a close call.** It is
not rationale; it bounds what the phase may claim. Three things depend on it: the packet
prohibition at line 269 against saying a green gate means good poker, which without it is an
unexplained rule; the stage-8 domain reviewer's brief, whose whole point is the question no shape
check answers; and the honesty of the criteria themselves, every one of which is a shape property.
Cutting the sentence that says the shape checks prove nothing about the poker, in order to make
room for another shape check, is precisely the trade the compression question exists to catch. If a
line is genuinely needed later, restore the key-precedence clause first and cut "MAINT-26 measured
what a solve costs" at line 24, which is provenance the decision list already holds.

**The count you asked me to fix: use 9, and say what it counts.** My "five" was wrong, and it was
wrong by hand-counting - I eyeballed the phase-16 list for ids that looked postflop instead of
set-differencing every id against the contract text. That is the same class of error I filed
`NOTHING-CHECKS-THAT-EVERY-RULING-REACHES-A-CRITERION` about, committed inside the review that
filed it.

Measured with a set difference: **21** backlog entries carry `phase: "16"`, all `deferred`. The
pre-fold-in contract at `b1f5667` named 9 and left **12** unnamed, which is your figure and it is
right for that baseline. The current contract names 12 and leaves **9** unnamed.

The entry should not carry a bare number, because the baseline has moved three times in one day
(12 pre-fold-in, 10 at my first read, 9 now). What it should carry is the split, because the nine
are not one thing. **Four are phase 16's own subject and are the real finding**:
`NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`,
`A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE`,
`POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` and
`POSTFLOP-SOLVE-IS-RAKE-FREE-AND-THE-GAME-IS-NOT`. **Five are phase 14 preflop-chart work assigned
forward**: `CALIBRATED-REALISATION-PRICES-FOUR-BET-POTS-UNTESTED`,
`COMMITTED-SPOTS-NEVER-FLAT-A-RAISE`, `COMMITTED-THREE-BET-SPOTS-INHERIT-AN-EXCLUDED-NODES-RANGE`,
`GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE` and
`A-RELATION-THAT-ONLY-COMPARES-NEIGHBOURS-CANNOT-SEE-A-TWO-CELL-HOLE` - all five filed by phase 14's
own reviews, all five about ladder relations, committed spot ranges and equity tables, none of them
postflop. Phase 16's contract has no business naming those and phase 16 will not do them. Their
`phase: "16"` means "next owner", not "phase 16's subject", which is
`BACKLOG-PHASE-FIELD-MIXES-PHASE-NUMBERS-WITH-CATEGORIES` seen from the other side: that entry
shows the field under-counting what a phase owns, and this shows it over-counting.

So: **9 of 21 as of 2026-09-10 against the post-fold-in contract, of which 4 are phase 16's own
subject and 5 are inherited preflop work the contract should not name.** Two other things in that
entry are now false. Its title says "Five backlog items" and its id says `NAMES-NONE-OF-ITS-OWN`,
while the contract names 12 of the 21 - so it names most of them, and the generalisation the entry
is actually about is that a contract names *some* of its deferred items and nothing checks the rest.

## Blocker

- [resolved] **The three-cause refusal split at lines 184-185 requires a distinction the ruled design cannot make, and stage 4 is about to freeze tests against it.**

  **Resolved 2026-09-10, round 2.** The criterion now carries exactly two causes and says in terms
  that the campaign-rejected count is a report figure and not a third cause. Verified satisfiable,
  verified against decision 6 item 3 and the index criterion, and verified that neither the
  refusal criterion nor the Evidence list reads three-way alone. Detail in the round-2 section
  above. The finding as originally written follows unchanged.

  The criterion reads "A miss is reported under one of three causes and the report never pools
  them: never solved; solved but over 1% of pot; and in the index but not fetched here". Decision 4
  closes with the opposite finding in its own words: telling "never solved" apart from "solved and
  over 1%" is "impossible at query time, because neither cell is in the artifact: both are the same
  miss. Distinguishing them needs a committed list of attempted-and-rejected boards with their
  achieved percents, which no contract criterion requires. Either a criterion is added at stage 4
  or the inventory pools the two causes and says so."

  The rewrite took neither exit. It forbids pooling and it adds no rejected-board list. Worse, its
  own index criterion at lines 87-92 forecloses the list: "Every entry in the committed index
  records the achieved exploitability ..., the iteration count, the strategy digest **and the digest
  of the stored object**". A cell refused for exceeding 1% has no stored object, so by that sentence
  it cannot be an index entry, which matches decision 6 item 3's "one entry per solved spot". With
  no entry, a query meets exactly the same absence for a never-solved board and for a
  rejected-above-1% board, and the report cannot split them.

  Note what decision 6 item 8 actually forbids, because the contract widened it. Item 8 says the
  third cause "is the only one of the three a query can name precisely" and that "Reports must not
  pool it with 'never solved'" - a prohibition on pooling the *third* with the first, stated
  alongside an acknowledgement that the first two are not separable. The contract's "never pools
  them" reads over all three and is therefore stronger than what was ruled.

  Why this holds the stage rather than waiting for stage 6: stage 4 authors the refusal tests and
  stage 5 freezes them. A frozen test asserting a three-way split that no implementation can produce
  is expensive to unwind, and it is precisely the class of defect the loop's freeze exists to
  prevent early.

  Two ways out, and they are not equivalent. The cheap one is decision 4's own second exit: state
  that never-solved and over-1% are reported as one cause with the reason given, and keep
  "in the index but not fetched" strictly separate, which is all decision 6 item 8 demanded. That
  needs no new human ask, because decision 4 already authorised it. The expensive one is to require
  the index to carry attempted-and-rejected entries with their achieved percents and no object
  digest, which changes the shape of committed data that decision 6 ruled `frozen-into-data`, and so
  is Taylor's to answer rather than a lane's.

- [resolved] **The canonical-board criterion at lines 73-76 can pass in full while the phase serves a no-draw strategy to a flush draw, and the new contract does not close it.**

  **Resolved 2026-09-10, round 2.** The flush-draw check is now one of two named gate tests on the
  canonical-board criterion, at lines 71-77, and it cites the backlog id. Verified falsifiable and
  verified that the compressed reasoning still states the property that makes it necessary. Detail
  in the round-2 section above. One observation for stage 4 rather than a reopening: the test as
  specified is necessary but not sufficient, since it catches an identity hand map on a two-tone
  board and would not catch a different non-identity map that happens to preserve draw status.
  Asserting that the canonicaliser applies one permutation to board and hand jointly is strictly
  stronger and no more expensive. The contract states what the poker review specified, so this is
  a note for the test author, not a defect in the fold-in. The finding as originally written
  follows unchanged.

  `stage-02-decisions-poker.md:307` and the backlog entry
  `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS` (status `deferred`, phase `16`) state
  it: suit isomorphism is exact only if hero's two cards are permuted by the **same** map as the
  board. The criterion requires a test that all 1,755 classes are distinct, that each of the 22,100
  boards maps into exactly one, and that a rank-texture neighbour maps elsewhere. I confirmed by
  brute force that all three of those hold of the board map, and that is the problem: they hold
  whatever the hand map does. A hand permuted inconsistently with its board passes every one of
  them and returns a real strategy for a real hand, so no exploitability figure and no shape check
  can see it. On a two-tone flop - 55.06% of flops, the modal texture, and one of the three
  committed sample cells - whether hero's cards share the board's flush suit is most of the
  strategy.

  I am calling this a blocker on the merits rather than because the brief invited it. Three things
  make it one. The contract itself says the key "is the one thing the phase must get right before
  any data" and that this collapse "is the only collapse permitted"; a permitted collapse that is
  unverified on the half that matters is the criterion failing at its own stated purpose. The
  contract is the only place a test obligation can be created before stage 5 freezes `tests/**`, so
  after this stage there is no cheap moment left. And the backlog entry pins it to phase 16 while
  nothing in the phase makes it happen, which is the pattern
  `AN-AMENDMENT-TO-A-SKELETON-CONTRACT-IS-DELETED-BY-ITS-OWN-STAGE-1` was filed about.

  The fix the poker review gives is one clause and is poker-shaped rather than combinatorial: on a
  two-tone board, a flush-draw combo must not receive a strategy identical to the same ranks
  without the draw. It attaches to the existing sentence.

  On where the line comes from, since the file is at 299 of 300. Do not buy it by weakening a
  predicate. The compressible material is rationale, not obligation: the "decorative-gate defect"
  aside at line 175, the phase-13 canary provenance at line 193, and the fresh-clone aside at line
  185 are each a clause that carries no falsifiable content. If the contract cannot absorb two more
  obligations without cutting a predicate, that is `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` arriving
  here, and the answer is the rewrite `AGENTS.md` prescribes rather than a shorter criterion.

## Non-blocker

- **No obligation from `b1f5667` is missing, and I looked for the near-misses specifically.** Six
  places lose a sentence without losing the predicate, listed so a later reader does not have to
  re-derive that judgment. The old determinism bullet's "and records the digest" is gone from lines
  100-103, but the index criterion at lines 87-92 requires a strategy digest per entry. The old byte
  bullet's "each recomputed rather than quoted" is gone, but "the generator exits non-zero on one
  that does not reconcile against the bytes on disk" survives at lines 162-163 and is the stronger
  form. The rationale for the schema bump, the range-against-range rationale for the preflop line in
  the key, the "phases 08 and 09" canary provenance and the two-review provenance on the three
  inverting frozen tests are all reasoning rather than obligation. Twelve criteria are strictly
  stronger than their predecessors, most notably the no-network non-goal (now "no fetched solve
  object, against the committed sample rather than a placeholder"), the "Explicitly not closed" list
  (three ids to six), and the packet qualifications (three to four).

- **All three obligations the writer added beyond the thirteen are genuinely in the record. None is an invention.** The key naming the flop bet size is decision 9, ruled by Taylor 2026-09-09
  ("Name the bet size"), and the old contract did not carry it - so this is a recovered omission
  rather than an addition, and the ExecPlan's list of thirteen simply does not contain it. The bar
  on any winrate or EV figure is stated twice in the decision list in its own voice, at the
  consequence-of-decision-1 paragraph in the index and again in decision 1's 2026-09-09 stage-2
  poker annotation ("no winrate or EV figure may ever be reported over this artifact"). The report
  publishing each committed range's pair weights on both sides is decision 12's explicit condition
  on the default Taylor took, and it is the most falsifiable of the three.

- **Ruling 7's supersession of the old determinism fallback is genuine, not a convenient reading.** Decision 7's answer says it in terms: "The fallback branch in the contract is therefore a halt, not
  a value." The old bullet's accuracy-target-and-maximum-divergence branch existed only as that
  fallback's content, so it dies with it rather than being dropped alongside it. The new text also
  adds "in two processes against a restarted server", which the old bullet had only as a report of
  what MAINT-26 did rather than as an obligation.

- [resolved] **Determinism is now the phase's one halt condition and it has no evidence surface.** **Resolved round 2:** the Evidence list at lines 218-219 now requires the report to record that the committed configuration was solved twice, the two strategies compared, and whether they were byte-identical. Original finding: lines
  100-103 require the two runs and the halt, but the Evidence list at lines 211-217 names no
  determinism figure, and the packet requirements at lines 259-269 do not mention it. The gate runs
  offline and cannot re-solve, so nothing anywhere records that the two runs were compared or that
  they agreed. This is inherited rather than introduced - the old contract had the same hole - but
  the ruling raised the stakes, because a halt that nobody can tell was skipped is a halt on the
  honour system.

- **Ruling 9, the rented machine, landed in Scope prose rather than as an acceptance criterion.** Lines 32-34 carry it correctly and completely, including the CUDA prohibition. But Scope is not
  something a gate or a reviewer fails a phase on, and the ruling's content ("every timing and arena
  figure here is re-derived there before a run is planned") is an obligation with a checkable
  trigger. Contrast ruling 10, whose equivalent obligation - re-check
  `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` against the machine before stage 6 - did land as a
  criterion at lines 120-122. Ruling 8 (one phase, not split) belongs in Scope and is fine there;
  ruling 9 does not obviously.

- [resolved] **The contract hands stage 4 a choice decision 6 already made, and drops what one of those choices was for.** **Resolved round 2:** lines 164-168 now name `Kc7d2h` and `9c8c7c` and leave stage 4 only the two-tone paired board, and decision 6 item 4 at line 775 was corrected to match, so the two documents no longer describe different phases. Original finding: lines 166-168 froze the three sample cells and then say "Stage 4 picks the boards inside
  those cells and nothing else". Decision 6 item 4's ruled assignment names two of the three boards
  and gives each a load-bearing reason: `Kc7d2h` because it "is the single rainbow row the whole 45
  to 85 day campaign estimate extrapolates from, so committing it also puts a number under the
  phase's own cost model", and `9c8c7c` because it is `matrix-03`, already converged with a recorded
  digest, so "half of that experiment is already paid for and the sample board and the experiment
  are the same solve". A stage 4 picking freely inside the cells loses both properties and does not
  know it lost them. In fairness to the writer, decision 6 contradicts itself here - it says stage 4
  picks the boards, then picks two of them - so the contract copied one of two inconsistent
  sentences. Worth the coordinator's call rather than the lane's.

- **Decision 11's stage-6 menu experiment has no criterion anywhere.** Decision 11 files it as
  "one board, pot, stack and both ranges held, only the menu moving - run as `33 75` / `66 125` /
  `66 125` against `33 75` / `66 200` / `66 125`", and says "it is cheap, it belongs at stage 6
  rather than here, and **nothing commits until it runs**". That last clause gates committed data
  and appears in neither contract version. It is not among the thirteen, so this is an observation
  rather than a fold-in defect, but the contract is the gate's only memory of it.

- [resolved] **"with the vacuous one labelled" at line 216 now presupposes a vacuous code the same contract has just argued is live.** **Resolved round 2:** it reads "with **any** vacuous one labelled" at line 216, which is conditional and correct. Original finding: lines 182-184 make the board-miss code live on the ruled design: "all 1,755
  classes are in scope, but a cell over 1% of pot refuses and rainbow has never been solved to
  target". The old contract's hedge ("labelled vacuous only if decision 4 makes it so") was correct
  while decision 4 was open and is now resolved in the direction of "not vacuous". The Evidence
  clause survived the resolution unchanged. It is harmless if read as "label whichever is vacuous",
  and confusing if read as an assertion that one is.

- **The `allin_threshold` compression dropped the sentence that says the source note is wrong.** The
  old bullet ended "the notes' description as a percent of pot is wrong about the quantity even
  though its warning holds". `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE` is on the contract's
  Closed list at line 228, and closing an item filed against a wrong sentence in
  `docs/GTOPEN_SOLVER_NOTES.md` while the contract no longer says the sentence is wrong is the same
  shape as `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`, which the very next bullet guards with "closed
  **only** once no live document still says the turn costs 49 flops". One id gets the guard and its
  sibling lost it in compression.

- **Stale cross-references, still open after round 2, and the targets have moved again.** The brief
  named two; there are seven, in two files, and none is fixed yet. Re-measured 2026-09-10 after
  round 2. In the decision list: `PHASE_16_POSTFLOP_BETTING_DECISIONS.md:514` cites
  `PHASE_16_POSTFLOP_BETTING.md:255` for "No packet may claim", which is now **line 268** (the
  bullet begins at 264) - it was 266 when I first measured it, so this citation has moved twice in
  a day; `:728` cites the contract's "gate must pass ... with no network" at "line 48", now
  **line 44**; `:1629` (was `:1625`, shifted by round 2's own correction to item 4) says "The
  contract is at 284 of 300 lines and its Scope commits it to amending three criteria after stage
  3", and the file is at **299** with the amendment done; `:109` says up to five rulings "share the
  contract's sixteen remaining lines", now **one**. In the ExecPlan: `:199` "the 300-line cap the
  contract sits 11 lines under", now **1 line under**; `:308` "the contract is at 289 of a 300-line
  cap"; `:375` "289 of 300 lines today". All three ExecPlan sites, not two.

  Round 2 made a point worth acting on rather than only re-recording. Two of these targets moved
  while the correction was pending, and one citation's own line number moved because a sibling
  paragraph was edited. Chasing line numbers across files is a losing maintenance game and the
  repo's own rule about figures quoted into prose is the same rule. **Cite the quoted phrase or the
  heading instead of the line**, both here and in the two ExecPlan sites - `grep` finds a phrase
  and no edit invalidates it.

  Two references I would **not** touch. `stage-03-human-gate.md:287` and
  `stage-01-numbers-verification.md:54,110,273` also cite moved contract lines, but a review note is
  a snapshot of what a stage believed and `AGENTS.md` is explicit that such records stay as written.
  Correcting them would falsify the record rather than repair it.

- [resolved] **Outside the brief: the ExecPlan says five mutation canaries pin these files and there are six.** **Resolved round 2:** `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:186` now reads "Six mutation canaries", which I re-counted independently. Original finding: it read "Five mutation canaries pin exact
  lines in `postflop_fallback.py` and `composite.py`". I enumerated `verification/mutations.yml`:
  `fallback-answers-preflop`, `fallback-folds-guaranteed-chops`, `fallback-abandons-the-turn`,
  `fallback-turn-needs-only-one-safe-river`, `composite-routes-preflop-to-the-fallback` and
  `fail-closed-can-invest-again` - **six**, the last one witnessed by `pytest_engine_fidelity`. The
  contract is right to state it as a predicate and not a count, and is right that one has a
  different witness; only the ExecPlan carries the number, and B1 is briefed off the ExecPlan.

- **Outside the brief: the largest accepted cost decision 11 identified is in no packet requirement.** The machine note says metered rented-GPU spend "was the largest unwritten accepted cost in the
  phase, found by the stage-3 review outside its brief". The packet requirements at lines 259-269
  list four qualifications and none of them is money; the nearest cover is the generic "known
  limitations and deferred items" at line 269. It is not among the thirteen, so this is not a
  fold-in miss, but the record went to some trouble to surface it and the contract is where a
  packet obligation lives.

- **Outside the brief: `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS` is now stale in its own text.** Its `reason` says "No contract criterion, report or decision item says so" of the
  multiway share being structural. Contract lines 148-152 now say exactly that. I re-derived the
  entry's figures and they hold: 259 of 499 hands see a flop, 20 multiway (7.7%), 92.3% heads-up.
  The coordinator owns `backlog.yml`; the sentence needs one word changed.

- **Round 2: the key-precedence clause is the one cut that was not rationale.** The version I
  reviewed carried "Changing what the key can express re-derives every committed cell, so it
  precedes any data" on the key criterion, and `b1f5667` carried it as "which is why this is the
  one thing the phase must get right before any data". Round 2 cut it and it is now nowhere in the
  contract - I grepped for the phrase, for "before any data" and for "precede", and the only hit is
  the word "precedent" in the digest-width sentence. That is an ordering obligation, not a
  rationale: it says no cell may be committed against a key that can still change. It is decision
  13's stated reason for accepting the cost of one phase, and decisions 3 and 6 both call the key
  "the one thing this phase must get right up front".

  I am not making it a blocker, for three reasons. Nothing at stage 4 turns on it, since the tests
  are frozen before stage 6 either way. The ExecPlan states the ordering explicitly and
  operationally - "At stage 6, K1 first and alone, because every other lane keys against the shape
  it defines" - and the ExecPlan is a committed living document that governs stage 6 sequencing.
  And Scope still says the artifact is committed against a key nothing has been built against yet,
  which presupposes it. But the writer's claim that nothing falsifiable was cut is not quite true,
  and the consequence is concrete: the contract no longer backs the ExecPlan's integration order,
  so if that order is relaxed at stage 6 nothing objects. Restore this clause before anything else
  if a line frees up.

- **Round 2: the index has a header, and only the report-figures list says so.** The
  campaign-rejected count is specified as "carried in the committed index's header" at lines
  217-218, inside the Evidence bullet. The index criterion at lines 87-92 describes entries and
  never mentions a header. A stage-4 author writing the index schema from the criterion that
  defines the index would not know it has one. The obligation is unambiguous once both are read
  together, so this is a placement point rather than a gap: the index's shape is now specified in
  two sections, one of which is a list of report figures.

- **Round 2: "cause" and "code" are now two axes and only the Evidence list says they cross.** The
  refusal criterion at lines 180-187 requires distinct codes for an uncovered line and an uncovered
  board, then says a miss "carries exactly two causes", the first of which is "no cell for this
  board or line" - which merges, on the cause axis, the two things the previous sentence requires
  distinct codes for. The Evidence list gets it right, asking for counts "by code **and by** the
  two table causes", so the crossing is stated once. Reading the refusal criterion alone, a stage-4
  author could take cause 1 as licence to report board-miss and line-miss together. Low severity
  and easy to close by saying "crossed with the codes" in the criterion itself, but it is the same
  ambiguity class that produced blocker 1 and it is worth not repeating.

- **Round 2: two compressions left prose that says something slightly different from what is
  meant.** At lines 122-125, "snaps any bet reaching `allin_threshold * max_to`, `max_to` being the
  stack behind, to a stack-off outside the `add_allin` guard" now reads as though the *stack-off*
  sits outside the guard; the claim is that the *snap* is not gated by `add_allin`. The
  consequence clause that follows preserves the operative fact, so nothing is lost for a careful
  reader, but this is a `tree.rs` behaviour claim a stage-6 implementer will act on. At line 178,
  "`CODE_FOLD_ON_THE_FLOP` covers the flop today and is answered after this phase" makes the code,
  rather than the flop, the thing that gets answered. Both are wording, not obligation.

- **Round 2: the new backlog entry's own distribution figures were measured before it was filed.**
  `BACKLOG-PHASE-FIELD-MIXES-PHASE-NUMBERS-WITH-CATEGORIES` states `contract-update` at 119 items
  and `maintenance` at 1. I measure **122** and **2** across **277** items; the gap is exactly the
  four entries filed in this round, three of which are `contract-update` and one `maintenance`. So
  the entry excludes itself and its three siblings from its own census. Every other value in its
  list matches mine exactly (14:54, charts:25, 16:21, strategy:14, 12:8, v2:6, 11:6, 15:5,
  simulator:5, 13:4, 17:4, samples:1). Either bump the two numbers or say the census was taken
  before this commit.

- **The three checks all pass.** `check_file_sizes.py`, `check_contracts.py` and `check_scope.py`
  each exit 0 silently. The contract is at 299 of the 300-line cap on
  `docs/phase_contracts/*.md`.

## Alignment

- [filed] **A fold-in brief that enumerates amendments cannot catch the amendment nobody enumerated, which is the same failure one level up.** Filed as `NOTHING-CHECKS-THAT-EVERY-RULING-REACHES-A-CRITERION`; I read the entry and its claims check out, including that `check_contracts.py` reads the contract alone and nothing in `scripts/` reads a decision list against one. Decision 9 was ruled by Taylor on 2026-09-09, never reached the
  old contract, and is not among the thirteen the ExecPlan told C1 to absorb. It is in the new
  contract only because the writer went past its brief. That is `AN-AMENDMENT-TO-A-SKELETON-
  CONTRACT-IS-DELETED-BY-ITS-OWN-STAGE-1`'s "luck rather than design" reappearing in the mechanism
  built to prevent it. The durable fix is not a longer list but a check that every `Answer:` block
  in a phase's decision list resolves to a criterion, run at every contract stage rather than
  recounted by hand. Nothing in `scripts/` does this today.

- [filed] **Nine backlog items sit at `phase: "16"` and `status: deferred` and the contract's backlog section names none of them.** **Corrected round 2 and filed as `A-PHASE-CONTRACT-NAMES-NONE-OF-ITS-OWN-DEFERRED-ITEMS`.** My original count of five was a hand-count error; the measured figure is **9 of 21** against the post-fold-in contract, of which 4 are phase 16's own subject and 5 are inherited phase-14 preflop work. The entry's stated count, its title and its id all need changing - see the round-2 section for the exact figures and the recommended wording. The original finding, with the undercount, follows:
  `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`,
  `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE`,
  `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST`,
  `POSTFLOP-SOLVE-IS-RAKE-FREE-AND-THE-GAME-IS-NOT` and
  `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`. The first is the measurement decision 7
  calls "the cheapest open measurement in the phase" and says "is still owed"; the third is the
  reason decision 6 gives for the sample being three flops rather than two, so the contract depends
  on it while not naming it. The old contract named none of them either, so this is drift rather
  than a rewrite defect, and it is the shape of the known closeout blind spot: a phase can close
  green with its own items still deferred and no check sees it.

- [filed] **The contract is at 299 of 300 with stages 4 through 11 still to run.** Filed as `A-CONTRACT-HAS-A-FIXED-LIFETIME-AMENDMENT-BUDGET-AND-A-BIG-PHASE-SPENDS-IT-EARLY`; I re-measured 299 against the 300-line cap and the entry's reasoning about the valve not refilling is right. Every stage from here can
  produce an amendment and there is one line for all of them.
  `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` records how that ends, and this file has now spent its
  entire fold-in budget before the first test is written. Two of the findings above want a line each
  and there is one available. The structural point is that a 300-line cap and a two-line amendment
  rule together give a contract a fixed lifetime amendment budget that a phase this size exhausts
  mid-phase, and the escape valve `AGENTS.md` offers - a rewrite folding amendments into criteria -
  has just been used and cannot be used again for the same lines.

- [resolved] **The decision list contradicts itself on who picks the sample boards.** **Resolved round 2:** decision 6 item 4 at line 775 now reads "Stage 4 picks the specific board inside a split and nothing else, and it picks **one** of the three" and names the two, which matches the contract. Decision 6 item 4 says
  "Stage 4 picks the specific boards inside these splits and nothing else" and then, forty lines
  later, picks two of the three itself and attaches a required stage-6 experiment to one of them.
  A later reader taking either sentence alone gets a different phase. This is the decision list's
  to fix, not the contract's, and it caused a real ambiguity in the fold-in.

- [filed] **Seven backlog ids the contract lists as this phase's business carry `phase:` values that are not `16`.** Filed as `BACKLOG-PHASE-FIELD-MIXES-PHASE-NUMBERS-WITH-CATEGORIES`. I verified the seven and the distribution, with one correction in the round-2 section: the entry's own counts were taken before it and its three siblings were filed. `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`,
  `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN`,
  `TWO-DOCS-STILL-SAY-DATA-ARTIFACTS-HAS-NO-SIZE-CHECK`,
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE`,
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` and
  `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES` all read `phase: contract-update`, and
  `POSTFLOP-BOARD-ABSTRACTION` reads `phase: charts`. The contract's "Explicitly not closed" and
  "Filed here" lists are the only place these are tied to phase 16, so any report that groups the
  backlog by phase will not show them against it.
