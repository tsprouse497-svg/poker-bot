# Stage 03 Review - Human Gate (Phase 16)

Question asked: does the record now say what was actually ruled, including any cost that was
accepted rather than only the answer?

Scope: `git diff 1541d8fbf020be5806e149b08db6a85be8a4c938 --
reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md`, the rulings dated
2026-09-10 on decisions 4, 6, 7, 10, 11 and 13, plus the 2026-09-09 entries on 5, 8, 9 and 12 that
the same hunk set carries. Worktree `/Users/taylorsprouse/projects/poker-bot-worktrees/phase-16`,
branch `phase/16-postflop-that-can-bet` at `7f2b6ab`, pointer `verification/loop_runs/16.yml` at
stage 3 with `stage_base: 1541d8f`.

Reviewer: an independent read-only worker subagent. I did not write the contract, the ExecPlan, the
decision list or any of these rulings. I edited nothing but this file, ran no gate command, no
`pytest`, no `run_verify.py` and no `check_gate_bite.py`, and checked out, stashed and reverted
nothing. Every figure below was recomputed from `reports/active/latest_postflop_solve_cost.txt`'s
own `Row data:` JSON, from `docs/GTOPEN_SOLVER_NOTES.md`, or from the scripts named, rather than
copied from the diff. The scripts are short enough to rewrite from the method stated beside each
number and were not committed.

**Headline: the answers are recorded, several of the costs are not, and two of the costs that are
recorded are wrong.** The record now names a target, a cap, a commit-or-refuse bound, a storage
mechanism, a key shape, a menu, a floor and a phase count. What it does not say is what the ruled
1,200-iteration cap costs in wall clock, what git LFS costs an offline gate, or what a hand opened
to 2.25bb does against a key that now carries an exact pot. And the two biggest numbers in the new
prose - a 10-day campaign and a 0.3% headline accuracy - are one an arithmetic error against its
own inputs and the other a claim this phase's own contract forbids.

## Round 2, 2026-09-10: verification of the six blockers

Second read-only pass, same reviewer, same constraints. The diff under review grew to
`reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md` (decisions 4, 6, 10 and 11
rewritten, plus a new machine note under 11) and `backlog.yml` (three entries re-pointed, one new
entry filed). `verification/loop_runs/16.yml` also moved. Nothing else in the tree changed and I
edited nothing but this file.

**All six original blockers are resolved and I verified each one rather than taking the new prose on
trust.** Every corrected figure in decision 4 reproduces. Two of the six were answered by Taylor
re-ruling rather than by a correction: git LFS is withdrawn outright, and the decision 8 / decision
10 collision is resolved by naming the solved line's nominal pot and stack in the key with a
query-time tolerance.

**Three new blockers, all introduced by the fixes.** The query-time tolerance is classed
`runtime-reversible` against this file's own preamble and passes the modal spot with exactly zero
margin; decision 6's index sizing understates itself by roughly 5x to 48x and is the feasibility
claim the whole ruling rests on; and the committed sample creates a new `frozen-into-data` choice
handed to stage 4 with no item and no human. The original six bullets follow with their markers, then
the new three.

## Round 3, 2026-09-10: verification of the three new blockers

Third read-only pass, same reviewer, same constraints. Decisions 4, 6, 10 and 11 changed again,
`backlog.yml` gained `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`, and both choices my
new blockers exposed went to Taylor and were ruled. I edited nothing but this file.

**All three new blockers are resolved.** The tolerance was replaced rather than patched and reclassed
`frozen-into-data`; the sample is ruled at three flops with a texture split and the poker reason on
the record; and the index figures are transcribed from my measurement rather than approximated - I
checked each one digit by digit. The two out-of-brief findings are recorded, and the money cost is
recorded the right way: the cost is named, no rate is quoted, and the reason for quoting none is
given.

**Three new blockers again, and one of them is a regression the fix introduced.** The replacement
tolerance is stated only for a 2.5x open and leaves a 3-bet pot's query behaviour undefined, where
the rule it replaced covered every line type; two `backlog.yml` entries still describe the withdrawn
1bb / 0.5bb tolerance, one round after the same defect was found and fixed in the same two entries;
and the contract amendment provably does not fit in the eleven lines the contract has left.

On the two things deliberately not done: **the contract judgment is right and the refusal-cause
judgment answers a different question than I asked** - both below.

## Round 4, 2026-09-10: verification of the three round-3 blockers

Fourth read-only pass, same reviewer, same constraints. Decision 10's tolerance was restated as a
fraction of each substituted price, both stale `backlog.yml` entries were re-pointed, the contract
sequencing was recorded in the ExecPlan's Next Agent Bootstrap, and all three of my out-of-brief
findings were taken with my figures and attributed. I edited nothing but this file.

**All three round-3 blockers are resolved in substance.** The price band covers every price the
chart declares - I re-scanned the whole artifact tree and there are exactly two, `@2.5` and `@7.5`,
so the 3-bet hole is closed and the 7.0bb case lands accepted. No live sentence anywhere still
asserts the withdrawn 1bb / 0.5bb rule, and the record of what was caught survives rather than being
tidied away. The contract sequencing is a **real discharge and not a reschedule**, for the reason
below.

**Three new blockers, and the first is the worst kind: the sentence that states the ruling still
contains the ruling it replaced.** Decision 10 line 1034 kept the withdrawn first draft with an
unclosed `**`, so the file states two incompatible rules in one sentence and renders the withdrawn
one in bold and the live one in plain text. The ExecPlan's Bootstrap says all thirteen decisions are
answered and then says two of them are open. And the ruled sequencing cannot be executed as written,
because closing a task requires a passing gate and this gate cannot pass.

## Round 5, 2026-09-10: verification of the round-4 blockers and of the corpus measurement

Fifth read-only pass, same reviewer, same constraints. I edited nothing but this file.

**The corpus measurement holds. I reproduced every figure from a parser I wrote myself.** Opens
n=409, median 2.2500, and 2.0-3.0bb covers 405/409 = 99.0%. 3-bets n=87, median 9.2500, and
6.0-9.0bb covers 41/87 = 47.1%. 4-bets and beyond n=19, median 25.35. The widening ladder
reproduces exactly: 30% 55.2%, 40% 71.3%, 50% 80.5%, 60% 89.7%. Every definitional risk I could
think of is either absent from this corpus or immaterial, and I checked rather than assumed:

- **The big blind.** `blinds_or_straddles` is `(50, 100, 0, 0, 0, 0)` on all 499 hands - exactly two
  non-zero entries, so there are **no straddles anywhere** and `max(blinds)` is the big blind
  uniformly. `min_bet == max(blinds)` on all 499, an independent confirmation. Antes are zero on all
  499. Variant is `NT` on all 499. So the "divide by that hand's own big blind" step is uniform and
  correct here - though the method would break on a corpus with straddles, and the entry should say
  the check was made rather than that the method is safe in general.
- **Depth.** Every seat starts at exactly 100.0bb on all 499 hands, so the median is directly
  comparable to a 100bb chart. The `100b`, `41b`, `75b` sub-directory names are session ids, not
  blind or stack levels.
- **Blinds as raises.** The blinds are posted through `blinds_or_straddles` and never appear as
  `cbr` actions, so they cannot be counted as raises. First `cbr` = the open (the 2-bet), second =
  the 3-bet is therefore the standard reading, not an artefact.
- **Limped pots.** Only **11 of the 409** raised hands carry a limp before the first raise, 2.7%.
  Those first raises are isolation raises and are still the first raise; excluding them cannot move
  a median of 2.25 or a 99.0%.
- **Jams.** This was my main worry, and it is clean: **zero 3-bet jams.** The 3-bet range runs 5.25
  to 14.0bb, so nothing all-in is inflating the median.
- **Rates.** 409/499 = 82.0% of hands see a raise and 87/409 = 21.3% of opens are 3-bet. The 21.3%
  is high against human 6-max norms of roughly 8 to 12%, and this is a Pluribus dataset - 499 hands,
  one bot among five humans - so I would call it plausible rather than verified. The raise-count
  distribution is internally coherent: 0 raises 90 hands, 1 raise 322, 2 raises 74, 3 raises 8, 4
  raises 4, 5 raises 1, and 74+8+4+1 = 87 is exactly the 3-bet count.
- **Exclusions.** `corpus_exclusions.json` holds one hand, dropped for fractional chips. No size
  bias.

**The deciles sharpen the reading and do not change it, and one of my own round-4 guesses was
wrong.** 3-bet deciles are 7.0, 7.34, 7.5, 8.5, 9.25, 10.0, 10.5, 11.2, 12.07. So **45 of 87
(51.7%) sit strictly above 9.0 and exactly 1 sits below 6.0** - the loss is almost entirely at the
top. I had guessed from the deciles that the band's lower half was empty; I measured it and it is
not: 26 3-bets fall in 6.00-7.50 and 24 in 7.50-9.00. Stating the measurement rather than the
inference.

**Three round-4 blockers resolved, one new one, and it is one phrase.** The doubled clause is gone,
the Bootstrap bullet is replaced, and the sequencing took my remedy with the `COMMANDS` reasoning
written down. The new blocker is the fourth instance of one class: the fold-in bullet's bold lead-in
still says the rewrite "is its own task" while its own body says it happens inside this one.

## Round 6, 2026-09-10: the last pass

Sixth read-only pass, same reviewer, same constraints. I edited nothing but this file.

**The round-5 blocker is fixed and all five round-5 observations are acted on.** "and is its own
task" is gone from the ExecPlan lead-in and I grepped for it - zero hits. The SPR figure is 3.52 in
both places with the earlier 4.0 named as an understatement. The duplication was resolved my way and
better than my way: the cause entry now carries the measurement and the consequence entry
cross-references it.

**One new blocker, and it is the only thing standing between this note and clean.** Decision 6's
item 4 now names three boards that cannot satisfy its own suit split, and the arithmetic that shows
it also answers the paired-board question the brief asks - the two travel together and one fix
closes both.

**On the question you asked at the end.** I have put three held-back items in Alignment with ids,
and one correction to a figure of my own. None of them is a blocker and none of them is new
information about this diff; they are things I noticed across six rounds that never fitted a
bullet. The largest is that no poker review has seen any of the rulings taken after stage 2.

## Round 7, 2026-09-10

Seventh read-only pass, same reviewer, same constraints. I edited nothing but this file.

**The round-6 blocker is resolved and the ruled assignment is right.** Item 4 is rebuilt on the 3x3
shape, the assignment is rainbow-paired / two-tone-connected / monotone-disconnected-low with the
monotone slot forced unpaired, the superseded "wants its own coverage" reasoning is quoted and
struck, the omissions are named, and the monotone imbalance is stated with a reason I had not
thought of - a frequency-weighted three would be two two-tones and rebuild the blind spot. The
sample cost, the entry division's one-way dependence, and decision 3's method-only annotation are
all in and all correct.

**All three held-back items are filed and the wording is faithful.** I checked each against what I
wrote; two of the three are sharper than my version. Details in Alignment, and two small field-level
problems in Non-blocker.

**One new blocker, and it is the seventh instance of a single class.** Item 4's rewrite inserted new
text and left the superseded text standing: its opening clause is spliced in half and three
consecutive sentences still say rank is left open, fourteen lines above the paragraph that rules it.
Every round of this review has found one of these, always the same shape - an insertion whose
surrounding sentences were not re-read. That is a process property rather than seven accidents, and
I say so in the last Alignment item because another review round is not the remedy.

## Round 8, 2026-09-10

Eighth read-only pass, same reviewer, same constraints. I edited nothing but this file.

**The blocker is resolved and I read the whole of item 4 rather than the diff, as asked.** Eight
paragraphs plus a three-bullet assignment, and I checked the boundaries and the cross-item
consistency rather than the sentences that moved. The opener carries the attribution in its first
clause, the superseded "constrains suit and leaves rank open" claim is recorded as superseded rather
than left standing, the cost paragraph is back and correctly labelled "a figure across all lines,
not per line", and every figure still reconciles with my brute force. Item 5's "three committed
flops" and item 8's "1,752 of 1,755" are both consistent with a three-board sample.

**Both field problems are fixed** - the poker-review entry is `phase: contract-update`, and the
round-count id is renamed. My three stale references to the old id are updated below.

**One new non-blocker, and it is the kind of thing only a whole-item read finds.** The item re-reads
the solver notes' five never-reached entries as *rank* structures and silently drops their suit
qualifiers, which is what lets a two-tone connected board count as covering "rainbow-connected".
Internally consistent under its own stated reading, and one clause short of being unambiguous.

**On where the re-read remedy belongs, and a correction to what I told you last round.** Both in
Alignment.

## Blocker

- [resolved] **Decisions 4 and 6 each say in prose that they stay blocking while filling the one field the
  loop reads, so the stage-3 halt is now cleared on both.** Line 439 reads "the slot stays empty
  and this item stays blocking" and line 683 reads "the item stays open and stays blocking"; lines
  466 and 692 are `Answer:` lines. `decision_items` in `scripts/loop_stage.py:283-301` takes the
  last line in each `## <digit>` section that starts with `Answer:` and keeps everything after the
  first colon, and `unanswered_frozen` at 304-310 treats anything outside `{"", "[]", "[ ]"}` as
  answered. Both new answers are long non-empty strings, so `check_human_gate` at 328-330 returns
  nothing for either item and `review_queue.py` stops printing the ask. Either the items are ruled
  and those two sentences are stale drafts that must go, or they are not ruled and the `Answer:`
  slots must be empty; as committed the file asserts both, and the machine reading is the one that
  advances the stage.
  *Fixed by deleting both sentences.* I grepped the file for "stays blocking", "stays open and" and
  "slot stays empty": the only surviving hits are none - both sentences are gone - and the two items
  now read as ruled throughout, which matches what `unanswered_frozen` sees. Decision 4's answer is
  now an explicit three-part split and decision 6's is a complete ruling, so the prose and the
  machine reading agree.

- [resolved] **Decision 4's `Answer:` line attributes the coordinator's own iteration cap to Taylor.** Line
  441 is careful and correct: "The iteration cap is 1,200, delegated to the coordinator by Taylor",
  with the delegation quoted verbatim. Line 466 then reads `Answer: [Ruled by Taylor, 2026-09-10]
  **Target 0.3% of the starting pot with a 1,200-iteration cap; ... commit a cap-bound cell whose
  achieved error is under 1% of pot and refuse one above it.**` That bracket is the only part of
  the item a later reader skims and the only part any script reads, and it presents a delegated
  number and a coordinator-recommended third option as a human ruling. Decision 6 sets the right
  standard 226 lines later - "The three figures below were taken by the coordinator on the strength
  of that ruling and are flagged for Taylor rather than presented as his" (line 692) - so the file
  disagrees with itself about its own convention inside one diff. Fix is mechanical: the bracket
  says which of the three parts is Taylor's, which is delegated, and which was a recommendation he
  accepted.
  *Fixed exactly as asked, and the fix is better than the ask.* Lines 433-445 now split the ruling
  into three parts with three provenances - target confirmed by Taylor with his words quoted, cap
  chosen by the coordinator under the delegation quoted verbatim, cap-bound rule a coordinator
  recommendation Taylor accepted with "i'll go with your rec on 4" quoted. The `Answer:` bracket at
  line 484 now carries the same three-way attribution rather than `[Ruled by Taylor]`, so the one
  line any script reads no longer launders anything. Decision 10's bracket at line 952 and decision
  11's at line 1184 adopted the same convention unprompted, which is the right generalisation.

- [resolved] **The campaign figure is wrong by about 2x against its own inputs, wrong by about 6x against the
  record's own texture factors, and the cost the ruled cap actually buys is never stated.** Line
  457 says "1,755 flops is on the order of 10 days per preflop line". Recomputed from the inputs
  the same paragraph names: the floored single-raised tree is 2,347,996 action nodes and 559 + 360
  = 919 hands (`latest_postflop_solve_cost.txt`, row `rung-lineA-pinnedmenu-rangefloor0.01`), the
  product is 2,157,808,324, and at 1.7 to 2.0 ns that is 3.67 to 4.32 s per iteration - so "about 4
  seconds" and "about 16 minutes per flop" at 240 iterations are both right. But 1,755 x 240 x 4 s
  is 1,684,800 s, which is **17.9 to 21.0 days**, not 10. Three further things the paragraph owes:
  - [resolved] The 1.7 to 2.0 ns band is **monotone only**. Re-normalising every solve row as gross wall
    clock / (action nodes x total hands), the four cells in that band are `matrix-01` through
    `matrix-04`, boards `9c8c7c` and `Kc7c2c`. Every rainbow row in the record reads 7.34 to 8.71
    ns and the two-tone converged cell reads 4.28. The paragraph names the cost notes' 2x pooled
    deflation in the same sentence and does not apply it; applying it gives 36 to 42 days.
    Weighting the notes' own factors - rainbow 3.05x to 3.22x monotone per iteration, 455 rainbow /
    1,014 two-tone / 286 monotone classes - and the notes' own iteration counts gives about 56 to
    66 days per line.
  - [resolved] **The ruled 1,200 cap is never priced.** 1,755 x 1,200 x 4 s is **89 to 105 days per preflop
    line** at the monotone rate, before either deflation. That number is the accepted cost of the
    delegated choice and it does not appear anywhere in the record.
  - [resolved] Lines 454 and 460 contradict each other: "The cap is not the binding constraint and a reader
    should not treat it as one" against "At a 1,200 cap the campaign is bounded by the cap rather
    than by the target". Both cannot hold. My own extrapolation from `matrix-02`'s committed curve
    says the intended reading is defensible - at the late exponent (I measure 1.02 to 1.29 from the
    curve, matching the stated 1.0 to 1.3) a converging cell hits 0.3% at 220 to 260 and never sees
    the cap, and the one rainbow row in the record, 6.23% at 30 iterations, extrapolates to target
    at roughly 305 to 760 - but that is the arithmetic the record needed to show and did not, and as
    written the two sentences leave a reader unable to say whether choosing 1,200 cost anything.
  *Fixed, and every corrected figure reproduces independently.* Recomputed from the row JSON again:
  2,347,996 x 919 = 2,157,808,324 action-node-hands, x 1.7 to 2.0 ns = **3.668 to 4.316 s** (stated
  3.67 to 4.32); x 240 x 1,755 / 86,400 = **17.88 to 21.04 days** (stated 17.9 to 21.0); x 2 =
  **35.8 to 42.1** (stated 36 to 42); x my texture weighting of 3.15 = **56.4 to 66.3** (stated 56 to
  66); x 1,200 instead of 240 = **89.4 to 105.2 days** (stated 89 to 105). The decay band is now
  "roughly 5.9x to 10x", which is 10^(1/p) at p = 1.3 and p = 1.0 exactly. The "How those two figures
  coexist" paragraph at lines 471-477 does discharge the contradiction: it says plainly that a
  converging cell stops at 220 to 260 and never sees the cap, that the cap prices the tail, and that
  the tail is "expected to be small rather than measured to be" - which is the right label for an
  extrapolation off one 30-iteration rainbow row. Lines 479-482 add that all of it is M4 CPU arithmetic
  and cross-references the machine note. Two residual imprecisions are non-blockers below.

- [resolved] **Decision 4's answer states an accuracy claim its own contract forbids, and justifies the 1%
  bound against a band the same diff contradicts.** Line 475 reads "the artifact's headline
  accuracy is 0.3% and its guarantee is 1%, so every report and every packet this phase produces
  states both". `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md:255` reads "No packet may claim
  the committed solve is accurate to 0.3%". Those are directly opposed, and the contract is right:
  the 0.3% figure is an exploitability target measured by a best response walking the same bet menu
  (contract line 107, and the notes' "Not verified" second entry), and no cell has been diffed
  against a deeper solve. Separately, line 434 says the 0.3% target is reasonable "against the 0.1%
  to 0.5% band that study work normally uses" and line 470 says "1% of pot is the outer edge of the
  band study work uses". 1% is twice the upper edge the same diff states. One of the two sentences
  is wrong and the 1%-commit ruling rests on the second.
  *Both halves fixed.* Lines 491-494 now read "**1% is not a study-quality figure and this file must
  not imply it is** ... twice the upper edge of the 0.1% to 0.5% band stated above, chosen as an
  outer bound on how wrong a played cell may be rather than as a target anyone would aim at", and
  name the earlier wording as the contradiction it was. Lines 496-501 replace the headline-accuracy
  sentence with "**No packet may state an accuracy for the committed solve as a whole**", citing
  contract line 255 by path and line. I grepped the whole file for "accurate to", "headline
  accuracy", "stated accuracy" and "settled accuracy": the two surviving hits are line 398, which is
  the original item body describing what committing floors would mean, and line 501, which is the
  correction itself. No live accuracy claim remains.

- [resolved] **The git LFS ruling is recorded without either of its two costs, and one of them
  defeats a contract criterion outright.** *Resolved by withdrawal, not by disclosure: Taylor
  withdrew LFS on the strength of this finding and ruled object storage outside git plus a committed
  index plus a committed sample, with the 20 MiB cap untouched. Verified that `.gitattributes` is
  unchanged and holds no `filter=lfs` entry, that there is no `.lfsconfig`, and that
  `DIRECTORY_BYTE_LIMITS` in `scripts/check_file_sizes.py:28-31` is untouched at
  `("data/artifacts", 20 * 1024 * 1024)`. Each sub-finding is marked separately below because
  `unresolved_blockers` in `scripts/loop_stage.py:168-185` strips each line before testing for `- `,
  so a nested bullet counts as its own blocker.*
  - [resolved] *The 20 MiB cap is not "left alone".* Line 699 says `DIRECTORY_BYTE_LIMITS` gains a 1 GB entry
    for the LFS-tracked flop artifact path "and the existing 20 MiB `data/artifacts` cap is left
    alone so the preflop chart keeps the guard it has". `scripts/check_file_sizes.py:48-54` sums
    `root.rglob("*")` per entry, so both limits apply to a nested path and the 20 MiB one still
    fails. The ExecPlan declares the artifact path as `data/artifacts/postflop/**`
    (`docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:48`). So either the artifact leaves
    `data/artifacts`, which is decision 6's own lever 6 and which that lever calls "an evasion" if
    the cap exists for reviewability, or the ruling is unimplementable as written. The record does
    not say which, and the path is now a fourth thing the item leaves unfixed alongside the
    encoding, the budget and the line count.
    *Resolved.* Lines 710-716 quote this finding back and withdraw the draft. The cap does not move
    and no nested exemption is added, so the `rglob` behaviour no longer bites, and the artifact
    simply does not enter `data/artifacts` at all. The path question is answered rather than left
    fourth on the list: object storage for the solve, `data/artifacts` for the index and sample.
  - [resolved] *LFS puts the committed data behind a network fetch.* `AGENTS.md` opens with "offline-first"
    and the contract requires at line 48 that "The gate must pass on a machine with no GTOpen, no
    Rust toolchain and no network". An LFS-tracked artifact is a ~130-byte pointer until a clone
    fetches its object, so on a fresh offline clone the strategy library reads a pointer and
    `check_file_sizes.py` measures 130 bytes against both caps - the byte-budget criterion at
    contract line 148 passes vacuously and the phase's own report prints the pointer's size. Also
    note `.gitattributes` has no `filter=lfs` entries today and the repo has no `.lfsconfig`, so
    nothing about the mechanism is in place yet. None of this is a reason to overturn the ruling,
    and it is squarely the cost the record owes.
    *Resolved, and this is the finding that changed the ruling.* Decision 6 item 4 commits a couple
    of flops in full and says "The gate, the tests and the byte-budget criterion run against those,
    so they pass offline with no GTOpen, no network and no fetched blob". That is a real answer
    rather than a relabelling: bytes that exist in a fresh offline clone are what the gate measures.
    The residual - that the *bot's* full flop capability now needs a fetch - is a non-blocker below,
    not a return of this one.
  - [resolved] Smaller, same item: "1 GB rather than a larger round number because LFS storage and bandwidth
    are metered and sold in 1 GB units" (line 700). GitHub's LFS free allowance is 1 GB of storage
    and 1 GB/month of bandwidth; paid data packs are sold in 50 GB units. The number is defensible
    as the free ceiling and the stated reason for it is not the reason.
    *Moot.* The 1 GB cap is withdrawn with the LFS ruling, so there is no billing-unit claim left in
    the file. The two per-GB node figures survive as history at lines 757-759 and are correctly
    labelled as corrections to a withdrawn draft; I re-checked them at 64.6 per decimal GB and 69.4
    per binary GB.

- [resolved] **Decision 10 plus decision 8 leave the modal corpus hand undefined, and it is the hand decision
  3's ruled ranking is built out of.** Decision 10 (line 903) puts pot and effective stack in the
  key with no nearest-value substitution; decision 8 (line 831) puts the preflop key in verbatim,
  including the `@2.5` the preflop lookup substitutes a 2.25bb open onto. Decision 8's own table at
  line 802 gives what a 2.25bb open really is: pot 5.00, effective 97.75, against the committed
  cell's 5.50 and 97.50. The contract says the key is "derived and compared, never parsed ...
  re-derived at import and at lookup" (line 68). So a hand opened to 2.25bb either derives
  `pot5.0/eff97.75`, misses, and refuses - and decision 3's annotation at line 325 says the corpus
  median open **is** 2.25bb and every corpus key reads `@2.5`, so the artifact would refuse the head
  of its own coverage list - or the pot and stack segments are derived from the substituted line, in
  which case they restate the preflop key and decision 10's stated reason ("a key that cannot say
  which depth it was solved at cannot refuse a spot it has no cell for") is not achieved on the one
  channel decision 8 flagged as unbounded. The record picks neither. This is a `frozen-into-data`
  key-format question, and the contract calls the key "the one thing the phase must get right
  before any data".
  *Resolved on the frozen half.* Lines 959-964 state the collision in the file's own words and lines
  966-970 pick the second branch explicitly: "the key names the line the cell was solved for, not the
  table it is being asked about", so the pot and stack segments are derived from the substituted line
  and a cell is always findable. Lines 981-986 then state the accepted cost honestly - on the
  substituted hands the segments "restate the preflop line rather than adding information", and the
  benefit "earn[s] their place when the phase covers a second depth". That is the narrower claim the
  finding asked for, and the `frozen-into-data` half of the question is now answered. The
  substitution rule that makes it work is a separate `runtime-reversible` default, and its class and
  its boundary are the first new blocker below.

- [resolved] **NEW in round 2. Decision 10's query-time tolerance is classed `runtime-reversible`, and this file's own
  preamble says it is not.** The default at lines 972-979 is "refuse when effective stack differs by
  more than 1bb or pot by more than 0.5bb", classed reversible because no committed cell records it
  and it is a rule the query evaluates. This file's preamble at lines 22-30 quotes `docs/LOOP.md:135`
  on "a committed artifact **or fixture**" and then says, citing
  `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`: "a behaviour default that a contract requires a frozen
  test to pin is a fixture, so it carries this class even in a phase that commits no data. A phase
  taking its definitions from this list rather than from `docs/LOOP.md` would have called such a
  threshold reversible and never asked anyone." That is this threshold, and that backlog entry
  records the reading as already settled rather than open. Three things make it bite here rather than
  in principle.
  **First, it decides coverage, and coverage is what a frozen ruling turns on.** Pot = 2 x open + 0.5
  on this line, so a pot bound of 0.5bb admits opens of 2.25 to 2.75 only, while the stack bound of
  1bb admits 1.5 to 3.5. The pot bound is therefore **4x tighter and is the only one that ever
  binds** at 100bb, and an open to 2.2bb gives pot 4.90, a 0.60bb gap, and refuses. Decision 3's
  ruled coverage list is built from corpus keys whose median open is 2.25bb.
  **Second, the modal case passes with exactly zero margin.** 5.50 - 5.00 = 0.50bb against a "more
  than 0.5bb" rule. The record states the arithmetic correctly and does not state that it is the
  boundary. A stage-6 implementer writing `>=` rather than `>`, or normalising the pot through one
  float rounding, flips the corpus's most common flop spot from played to refused, and because no
  committed cell records the rule nothing goes red. That is precisely the harm the reversible class
  is being used to wave through.
  **Third, a frozen test will pin it anyway.** The contract already requires the report to print "the
  refusal counts by code with the vacuous one labelled" and re-derive them, so a stage-4 test pins
  this threshold whether or not anybody planned to freeze it.
  What I am asking for is either the class corrected to `frozen-into-data` so Taylor sets the two
  numbers, or - if the class stands - the record stating that the bound is inclusive at 0.50bb, that
  the pot bound is the binding one, and that a 2.2bb open refuses.
  *Resolved by replacing the rule, which is the better of the two options I offered.* Lines 997-1026
  withdraw the pair, reclass the tolerance `frozen-into-data` citing the preamble and
  `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` by name, and record Taylor's replacement: accept a
  preflop open from **2.0bb to 3.0bb inclusive** against a cell solved at 2.5x. I confirm the
  preamble reclassification is right - a stage-4 test will pin this threshold through the refusal
  counts the contract makes the generator re-derive, which is the file's own "or fixture" reading.
  Arithmetic checked: the band is 1.0bb wide and 2.25 sits 0.25 inside it, so "a quarter of the way
  inside" is exact, and the zero-margin boundary is gone. I also verified the rule's unstated premise
  rather than assuming it: the committed chart declares exactly **one** open size across its 249
  keys, `raise@2.5`, and one 3-bet size, `raise@7.5`, so every open in 2.0 to 3.0 really does
  substitute onto the `@2.5` cell and the band is reachable end to end. The `>=`/`>` hazard is
  reduced and relocated rather than eliminated, and the width is defensible on coverage rather than
  derived from sensitivity - both non-blockers below - and the silence on the 3-bet price is a new
  blocker.

- [resolved] **NEW in round 2. Decision 6's index sizing is understated by roughly 5x to 48x, and it is the feasibility
  claim the whole ruling rests on.** Item 3 at lines 727-731 says "At 24 to 120 bytes of provenance a
  spot, 1,755 spots is 42 KB to 211 KB per preflop line, so an index for a realistic line count sits
  comfortably inside 20 MiB". Two inputs are wrong and they compound.
  **1,755 is boards, not spots.** The file's own node-line unit is "hero's strategy at one flop
  decision node, over all 1,755 flops, for one preflop line" (line 590), and line 601 measures about
  five hero flop decision nodes under the ruled menu. Decision 9 puts the faced bet size in the key,
  so facing-33 and facing-75 are separate keys and separate index entries. Entries per line are
  therefore about **1,755 x 5 = 8,775**, not 1,755.
  **The budget also omits the largest field in the entry, the key.** 24 to 120 bytes prices
  exploitability, iteration count and digest, per this file at line 610. It does not price the key,
  and I measured the committed preflop keys: 249 distinct keys in `data/artifacts/preflop`, length 14
  to 78 characters, median 45, longest
  `t6/d100/SB/LJ:raise@2.5,HJ:call,CO:call,BTN:call,SB:call,BB:raise@7.5,BTN:call`. A postflop key
  adds the board, the flop action, the pot and stack segments and a non-`t` prefix, so about 75
  characters at the median. A compact JSON entry with short field names is then about **130 bytes**
  with the repo's own 16-hex digest precedent (`ca16cf82eeb9c96e` in
  `latest_postflop_solve_cost.txt`) and about **230 bytes** with a full sha256 plus decision 11's
  four pinned config fields.
  **Corrected: 8,775 x 130 to 8,775 x 230 = 1.14 to 2.02 MB per preflop line.** Against the
  15,774,195 bytes of headroom I measured on disk today, that is **roughly 8 to 14 preflop lines**,
  which is the same order as the line count decision 6's own object-storage arithmetic affords and
  the same order as what decision 4's campaign affords. So the index does not sit "comfortably"
  inside the cap; it sits inside it by about one coverage decision's worth of margin, and being wrong
  about whether something fits is what created this item. The committed sample is not the problem -
  two flops at five nodes for one line is about 88 KB by the same rate.
  The ruling itself survives; the sentence that says it is affordable does not, and it must be
  re-derived before the index is designed.
  *Resolved, and transcribed rather than approximated.* Item 3 at lines 731-744 now carries every
  figure I measured and I checked each against my own working: 8,775 entries per line, keys "14 to 78
  characters with a median of 45" and a postflop key "about 75", "roughly 130 bytes an entry with the
  repo's own 16-hex digest, or about 230 with a full sha256 plus decision 11's four pinned config
  fields", 1.14 to 2.02 MB per line, 15,774,195 bytes free, "about 8 to 14 lines". Every one matches
  and nothing was rounded into a friendlier number. It also draws a conclusion the finding did not
  ask for and should have - "the index is a real constraint to design against and the digest width is
  a byte decision rather than a detail". On whether the digest width deserves its own frozen choice:
  yes, and it belongs inside the per-spot byte budget the Scope section already owes rather than in a
  new human gate, for a reason neither of us gave. Non-blocker below.

- [resolved] **NEW in round 2. The committed sample is a new `frozen-into-data` choice, handed to stage 4 with no item and
  no human.** Item 4 at lines 732-734 says "A couple of flops are committed in full, chosen at stage
  4". Those flops are a committed fixture that every later measurement of this phase runs against -
  the gate, the tests and the byte-budget criterion all run on them by the same sentence - which is
  `docs/LOOP.md:135`'s "committed artifact **or fixture** that later phases are then measured
  against", word for word. The contract's own Forbidden shortcuts say the criteria decision 6 leaves
  unnamed are "amended in `contract-update` after stage 3, not filled in by a builder", and this is a
  fifth thing decision 6 now leaves unnamed. It is not a formality, because the choice has a poker
  constraint the record does not state: the phase's entire converged evidence base is six monotone
  rows and one two-tone, `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` is
  already filed against exactly that, and rainbow is 455 of 1,755 classes and 39.76% of boards with
  zero converged rows. A sample of two monotone flops would reproduce the phase's known blind spot in
  the one artifact the gate can actually see. The sample needs an item, or the record needs to say
  which textures it must contain and why.
  *Resolved on the axis that carried the defect.* Item 4 at lines 745-756 rules three flops, one
  rainbow, one two-tone and one monotone, attributes the ruling to Taylor, names
  `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` as the reason it cannot be two,
  and says why rainbow in particular must be in the committed sample rather than only in the fetched
  bulk. "The specific boards are a stage-4 choice inside this ruling; the texture split is not" is
  the right line to draw and is **not** the same deferral wearing a hat: the suit-texture axis was
  the whole of the defect I raised, and it is now ruled rather than delegated. What the residual
  stage-4 choice still carries is a second axis the ruling does not constrain, which is a
  non-blocker below rather than a return of this one.

- [resolved] **NEW in round 3, and it is a regression. The replacement tolerance is stated only for the opening
  size, so a 3-bet pot's query behaviour is now undefined - and the rule it replaced covered every
  line type.** Lines 1016-1021 read "Accept a preflop open from 2.0bb to 3.0bb inclusive against a
  cell solved at 2.5x; refuse outside that." A 3-bet pot cell carries two substituted prices, not
  one: I measured the committed chart and it declares `raise@2.5` for the open and `raise@7.5` for
  the 3-bet across its 249 keys, and the cost report's 3-bet rows read `starting_pot: 16.0`, which is
  2.5 + 7.5 + 7.5 + 0.5 dead. The ruled band says nothing about the 7.5. A 3-bet to 7.0 gives pot
  15.0, a full big blind off the cell, and a 3-bet to 8.5 gives 17.5; under the ruled rule as written
  both are neither accepted nor refused, because the rule's antecedent - a preflop open against a
  2.5x cell - does not describe the query being asked.
  **This is worse than an omission, because the withdrawn rule did cover it.** The 1bb-of-stack /
  0.5bb-of-pot pair was stated on pot and effective stack in chips, so it applied to any line
  including a 3-bet pot at pot 16.0. Replacing it with a rule on the open narrowed the rule's domain
  and nothing recorded that. The exposure is not hypothetical: the phase's **entire** converged
  evidence base is 3-bet pots - five of the seven converged rows are `starting_pot: 16.0` and
  decision 11 says so at lines 1147-1148 - and decision 3's corpus-ranked coverage will reach 3-bet lines.
  The item is `frozen-into-data` and ruled, so a rule with an undefined case on the pot type the
  phase measured is a stage-3 question rather than a stage-4 one. What it needs is one more band, on
  the 3-bet size, stated the same way and with the same endpoints written down.
  *Resolved, and by a better rule than the one I asked for.* Restating the band as a fraction of the
  cell's own price closes the hole for every price the chart declares now **or later**, which a
  second hard-coded band would not have. Arithmetic checked: 2.5 x 0.8 = 2.0 and 2.5 x 1.2 = 3.0;
  7.5 x 0.8 = 6.0 and 7.5 x 1.2 = 9.0 - both bands fall out of one 20% rule exactly, with no
  rounding. On whether the chart declares more than the two prices I found, I re-scanned the whole
  artifact tree rather than only the spot keys: 7 JSON files, and every `@` price in any field is
  `@2.5` (1,220 occurrences) or `@7.5` (1,095). There are no others, so the two concrete bands the
  record states are complete. The 7.0bb case now lands definitely: 7.0 / 7.5 is 6.67% below the
  price, inside the band, accepted - and the record's own "pot 15.0 against the solved 16.0"
  reproduces. Whether 6.0-9.0 is defensible or merely symmetric is a non-blocker below, and the
  sentence that states this ruling is a new blocker below.

- [resolved] **NEW in round 3. Two `backlog.yml` entries still describe the withdrawn 1bb / 0.5bb tolerance, one
  round after the same defect was found and fixed in the same two entries.**
  `POSTFLOP-CELLS-ARE-STACK-FRAGILE-WHERE-THE-PREFLOP-CHART-IS-NOT` at `backlog.yml:7306` reads "the
  refusal is a query-time tolerance of 1bb of stack and 0.5bb of pot", and
  `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` at `backlog.yml:7359-7360` reads "a
  query-time tolerance refuses a spot more than 1bb of effective stack or 0.5bb of pot away". Both
  describe a rule decision 10 withdrew on the same day, in the same diff, on this review's finding.
  They are not incidental: decision 8's answer and decision 10's own "What it still does not bound"
  paragraph both point a reader at the second entry, so following the ruled record's own pointer
  hands the reader a rule that no longer exists. The second entry's substantive claim also moves -
  it says the tolerance "bounds the **geometry** channel", and the replacement admits about four
  times the geometric spread the old one did (see the non-blocker below for the figures). This is a
  blocker rather than drift because the record now contradicts itself about what was ruled, which is
  the question this stage exists to answer, and because it is the second occurrence in two rounds.
  *Resolved, and not overcorrected.* I grepped `backlog.yml`, the decision list and the ExecPlan for
  every `1bb` and `0.5bb`. Five hits survive and **none is a live assertion**: decision 10 lines
  1016, 1021 and 1059 sit inside the "Why the two bounds were wrong" and "Boundaries" paragraphs,
  which exist to record the withdrawal; `backlog.yml:7307-7308` reads "An intermediate draft of this
  re-pointing named a 1bb stack and 0.5bb pot tolerance; that pair was withdrawn the same day and no
  rule of that shape exists"; and `backlog.yml:7364` names the pair in parentheses with the reason it
  went. Collapsing the two same-day re-pointings into one was the right call - a reader now meets the
  live rule first and the withdrawn one as history, which is the opposite of the order that made this
  a blocker - and the diagnosis of what was caught is preserved in both entries rather than deleted.
  `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` also correctly keeps its own substance:
  it says the band narrows it "only slightly", carries the 20.45 of 26.97 points, and states that the
  range channel is untouched.

- [resolved] **NEW in round 3. The contract amendment does not fit, and the record plans it as though it does.**
  Decision 6 says the index-plus-sample restructure is "part of the three the Scope section already
  owes", and the coordinator's position is that every amendment is stage-4 work. I measured the
  contract: **289 of the 300 lines** `scripts/check_file_sizes.py:12` allows, so eleven free. What
  the contract must now say and does not: the encoding; the per-spot byte budget including the digest
  width; the line count as an output; object storage plus index plus sample in place of "the
  committed tree" at line 148; the three sample flops and their texture split; the 1,200 cap; the 1%
  commit-or-refuse bound and its distribution reporting; decision 7's halt replacing the tolerance
  branch at line 102; the ruled menu; the class-level 0.01 floor; pot and effective stack in the key;
  the 2.0-3.0 open tolerance; and the refusal causes. That is thirteen amendments into eleven lines,
  and `AGENTS.md` is explicit on both halves: an amendment is "at most two lines plus the
  `backlog.yml` id", and "Never raise the cap to fit an amendment." Its prescribed remedy is a
  rewrite folding existing amendments into the criteria they amend, which "is its own
  `contract-update` task".
  I am calling this at stage 3 rather than leaving it, for one reason: stage 4 authors the phase's
  tests against the contract and stage 5 freezes them. A contract that cannot state what the phase
  was just ruled to build is a contract the frozen tests will be authored against anyway, and this
  repo has already been round that loop - `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` is the entry for it
  and it records two amendments that waited on a rewrite that never came. The judgment call is
  whether "after stage 3" means "after this gate" or "at stage 4"; I think the arithmetic settles it,
  because there is no version of stage 4 in which thirteen amendments fit eleven lines.
  *Resolved as a stage-3 obligation. It is a real discharge, not a reschedule.* What stage 3 owed was
  that the plan of record must not assume an impossible amendment, and the ExecPlan's Next Agent
  Bootstrap at lines 279-287 now says the opposite of what it said: it states the arithmetic, applies
  `AGENTS.md`'s prescribed remedy rather than inventing one, cites
  `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` as the precedent, and orders the rewrite **before** stage 4
  with my reason written down as the reason. That ordering is the whole of what the finding required;
  the amendment itself was always later work. A reschedule would have been "we will make it fit at
  stage 4", and this is not that. **Yes, the fold-in rewrite needs its own review before stage 4**,
  and the specific thing to review for is already a filed entry: see the alignment item on
  `AN-AMENDMENT-TO-A-SKELETON-CONTRACT-IS-DELETED-BY-ITS-OWN-STAGE-1`. Whether the sequencing can be
  *executed* as written is a separate and new blocker below.

- [resolved] **NEW in round 4. The sentence that states decision 10's ruling still contains the ruling it
  replaced, and the markdown bolds the withdrawn half.** Lines 1034-1036 read, verbatim:
  `*The ruling:* **state the tolerance on the opening size itself, not on quantities derived from
  it.` / `**a band around each substituted price, stated as a fraction of that price: accept an
  actual size` / `within 20% of the price the cell was solved at, inclusive at both ends, and refuse
  outside.**`. The first clause is the withdrawn first draft. It is not merely redundant, it is the
  **opposite** of what was ruled twice over: the live rule is a band on each substituted price, and
  a price band is by construction a quantity derived from the cell rather than the opening size
  itself - and "the opening size" is the exact wording whose silence on the 3-bet price was the
  round-3 regression. So the ruling line now asserts the rule and its withdrawn predecessor in one
  sentence.
  It is also broken as markdown, and in the direction that matters. The `**` opened on 1034 is
  closed by the `**` at the start of 1035, so a renderer bolds "state the tolerance on the opening
  size itself, not on quantities derived from it." and leaves the actual ruling in plain text until
  the `**` after "refuse outside." opens a new run. The emphasis is inverted on the one line a
  reader skims for what was ruled. The fix is deleting the stale clause, and nothing else in the
  paragraph needs to move.
  *Resolved.* Line 1034 now opens `*The ruling:* **a band around each substituted price ...` and I
  grepped the file for "on the opening size itself" - **zero hits**, the clause is gone entirely
  rather than reworded. The `**` opened on 1034 now closes against `outside.**` on 1036, so the
  emphasis lands on the live rule. The 1034/1035 line break is a rewrap artefact and renders as one
  sentence.

- [resolved] **NEW in round 4. The ExecPlan's Next Agent Bootstrap says all thirteen decisions are answered and
  then says two of them are open, in the section whose own header calls it the single source for
  what is true now.** Line 276 reads "All thirteen decisions are answered as of 2026-09-10"; lines
  288-292, two bullets down, read "Open, and not to be invented: decision 4, the exploitability
  target and whether a solve reproduces ... and decision 6, the artifact encoding ... Both are
  `frozen-into-data`. Neither a reviewer nor a coordinator can supply either." That second bullet is
  a stage-1 leftover and both items were ruled on 2026-09-10. This is the round-1 blocker's exact
  shape - a stale sentence asserting an item is open beside a statement that it is answered - moved
  from the decision list into the ExecPlan, and it is worse here because `AGENTS.md` sends the next
  agent to this section first and the section claims to be authoritative about it. Decision 4's
  description in that bullet is also stale twice over: it says the target is "inherited from phase
  10's measurements", which decision 4 spends a corrected paragraph establishing is false.
  *Resolved, and it names its own failure.* The replacement bullet reads "**Nothing in the decision
  list is open.**", records that an earlier version listed decisions 4 and 6 as open after they were
  ruled, calls it "the same divergence between a summary and the record that the stage-3 review made
  its first blocker, relocated into the file `AGENTS.md` sends the next agent to first", and strikes
  the phase-10 inheritance claim with decision 4's reason - "Different engine, different tree,
  different unit." It also adds a bullet distinguishing what *is* open and is not a decision. That
  is more than the finding asked for.

- [resolved] **NEW in round 4. The ruled sequencing cannot be executed as written, and it is the sequencing
  that discharges the round-3 blocker.** The plan is "close this task at stage 3, run the fold-in
  rewrite as its own task, then activate stage 4". `AGENTS.md`'s Task Closeout is steps 1 and 2:
  "Run the full gate: `uv run python scripts/run_verify.py`" and "Commit the passing gate". That
  gate cannot pass here, and I established it by reading rather than running: `phase_status.yml:87`
  has phase 16 at `status: active`, `run_verify.py` derives the gate from `required_gate_commands`
  of every active or completed phase's contract, the phase 16 contract's frontmatter declares
  `pytest_postflop_betting` and `generate_postflop_betting_report`, and **neither string appears
  anywhere in `scripts/run_verify.py`** - they are unregistered, which is the red state the Bootstrap
  itself says is by design between stage 1 and stage 4. So the closeout the plan opens with is
  blocked by the very condition the plan exists to reach stage 4 and fix.
  I am not asking for a different remedy, only an executable one, and the simplest is already in
  hand: **this task is already in `task_mode: contract-update` with
  `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` in `approved_scope`.** `AGENTS.md`'s "the
  rewrite is its own `contract-update` task" exists to stop a rewrite being done mid-amendment to
  make room; doing it here as a distinct, declared piece of work in a task already in the right mode
  honours that and needs no closeout across a red gate. Whichever way it goes, the Bootstrap should
  say how the closeout clears the gate, because a successor following it literally will stop at step
  1.
  *Resolved, and my remedy taken.* The Bootstrap now records the closeout as unavailable with the
  reasoning spelled out - `phase_status.yml:87` active, the two command IDs unregistered in
  `COMMANDS`, `AGENTS.md` Task Closeout steps 1 and 2 requiring a passing gate - and moves the
  rewrite inside this task on the argument that `AGENTS.md`'s "its own task" rule aims at a rewrite
  done mid-amendment to make room. It states the order as "fold in, review, then stage 4", requires
  a read-only review of the rewrite, names
  `AN-AMENDMENT-TO-A-SKELETON-CONTRACT-IS-DELETED-BY-ITS-OWN-STAGE-1` as the failure mode, and
  writes my review question in as the question. Nothing left open here except the lead-in phrase
  above that bullet, which is the new blocker below.

- [resolved] **NEW in round 5, and it is one phrase. The fold-in bullet's bold lead-in still says the rewrite
  "is its own task" while its own body says it happens inside this one.**
  `docs/exec_plans/active/PHASE_16_POSTFLOP_BETTING.md:279` reads "**A contract fold-in rewrite
  blocks stage 4 and is its own task.**", and lines 291-295 of the same bullet read "The rewrite
  therefore happens **inside this task** ... `AGENTS.md`'s 'its own task' rule exists to stop a
  rewrite being done mid-amendment to make room; this one is declared ahead of any amendment, in a
  task already in the right mode, which is the case the rule is not aimed at." Those cannot both be
  read as current.
  I am raising it because of what it is rather than how big it is. This is the **fourth** instance
  in this stage of one class - a stale summary standing above a corrected body - after the decision
  list's two `Answer:` slots in round 1 and the Bootstrap's own "open, and not to be invented"
  bullet in round 4, and it is in the bullet that was just rewritten to fix the third instance, in
  the section that calls itself "the single source for what is true now". Deleting "and is its own
  task" from the lead-in is the whole fix.
  *Resolved.* Line 279 now reads "**A contract fold-in rewrite blocks stage 4.**" and I grepped the
  ExecPlan for "is its own task" - zero hits. The lead-in and the body agree.

- [resolved] **NEW in round 6. Decision 6's item 4 names three boards that cannot satisfy its own suit split,
  and paired boards are excluded by an argument the arithmetic does not support.** The item rules
  "One rainbow, one two-tone and one monotone" and then rules "**The three committed boards take
  rainbow-dry, rainbow-connected and disconnected-low**". Two of those three labels are rainbow by
  name, so the assignment contradicts the split in the same paragraph, on the only postflop data the
  gate will ever see.
  **The arithmetic that fixes it also settles the paired question, because rank and suit are not
  competing for the same three slots.** I brute-forced all 22,100 boards. Rank structure and suit
  texture are independent with exactly one forbidden cell: paired-rainbow is 1,872 boards (8.47% of
  flops), paired-two-tone is 1,872 (8.47%), and **paired-monotone is zero** - two cards of one rank
  cannot share a suit, so a paired board is never monotone, and trips are always rainbow (52 boards,
  0.24%). So the monotone slot must be an unpaired board, and paired can take either of the other
  two. Three boards can therefore carry three suit textures **and** three rank structures at once,
  one of them paired. The item treats five structures as competing for three slots when the real
  shape is a 3x3 assignment with one dead cell.
  **So yes, paired is the more important omission, and it does not have to displace anything.**
  Paired and trips together are 3,796 of 22,100 boards, **17.18% of flops**; ace-containing boards
  are 4,804, 21.74%, and ace-high *connected* is a small subset of that. The reason given for
  leaving paired out - that it "wants its own coverage rather than one of three sample slots" - has
  it backwards for a sample: the fetched bulk covers every paired board anyway, and the sample's
  whole job is to be structurally diverse enough that the gate can see a defect. A structure that
  wants its own coverage is exactly the one whose absence from three boards nobody will notice. And
  the notes single paired out precisely because no other structure substitutes for it: "a paired
  board is a structural gap rather than a suit one."
  I am not naming the three boards - that is the ruling's to make. What the ruling needs is a
  satisfiable assignment of one rank structure to each suit texture, with paired in the rainbow or
  two-tone slot and an unpaired structure in the monotone slot, and the two structures it then
  leaves out named as now.
  *Resolved, and the ruling is better than the finding asked for.* Lines 780-810 rebuild the item on
  the 3x3 shape with my figures - paired-rainbow 1,872 (8.47%), paired-two-tone 1,872 (8.47%),
  paired-monotone impossible, trips always rainbow at 52 (0.24%) - and rule **rainbow-paired,
  two-tone-connected, monotone-disconnected-low**, which is satisfiable and puts paired in without
  displacing anything. The superseded reasoning is quoted and struck rather than deleted. The
  omissions are named (ace-high connected, and the rainbow-dry pairing). And the monotone imbalance
  carries a reason I had not reached: a frequency-weighted three would be two two-tones and would
  rebuild the blind spot the sample exists to remove. Two-tone-connected is also the right second
  slot on the item's own terms, since connectedness is where the polar branch is built.

- [resolved] **NEW in round 7. Item 4's rewrite left the text it superseded standing, in two places.** This is
  the seventh instance in this stage of one class and the fix is one editing pass over one item.
  **First, the opening clause is spliced in half.** Line 761 to 763 now reads `4. **The committed sample is
  three flops, one per texture** - and it costs **1.06 to 1.85 MB across the 8 to 14 lines the index
  affords**, 7 to 12% of the free bytes, not the per-line figure it might be mistaken for. That
  belongs in the same budget as item 3's index rather than beside it. - ruled by Taylor 2026-09-10,
  and recorded as an item rather than handed to a builder.` The cost sentence was inserted inside the
  item's opening clause, so the attribution - "ruled by Taylor 2026-09-10" - now dangles after a full
  stop behind a stray dash, and the one thing a reader needs from the first line of a frozen ruling
  is who ruled it. The cost sentence is correct and belongs in the item; it does not belong inside
  that clause.
  **Second, three sentences still say rank is left open, and the item rules it.** Lines 773 to 776
  read "The specific boards are a stage-4 choice inside this ruling; the texture split is not.
  **This ruling constrains suit and leaves rank open** ... so three unpaired, non-ace-high boards
  would satisfy the letter of this and still cover two rank patterns." Fourteen lines later the item
  rules one rank structure per suit texture, and three unpaired boards no longer satisfy anything.
  Line 777 was updated in the same edit - "the two splits below are ruled here, not there" - so the
  three sentences above it are a partial-edit remainder rather than a considered qualification. As
  committed, a `frozen-into-data` item says both that rank is open and that rank is ruled, which is
  the defect I made this stage's first blocker in round 1 and its fifth, sixth and seventh since.
  *Resolved, and the item was rewritten in one pass rather than patched again, which is the right
  response to the finding.* Read whole rather than as a diff. The opener is `4. **The committed
  sample is three flops - ruled by Taylor 2026-09-10**, and recorded as an item rather than handed
  to a builder.` - attribution in the first clause, no stray dash, nothing dangling. The three
  stale sentences are replaced by one line that does the job properly: "An earlier draft of this
  item said the ruling 'constrains suit and leaves rank open'; that is superseded by the assignment
  below, which rules both." That records what was superseded without the superseded claim standing
  as current, which is the distinction the whole class turns on. The cost paragraph is back on its
  own, reading "a figure across all lines, not per line". Dropping "one per texture" from the
  opening heading is a small improvement rather than a loss, since both splits are now ruled and
  naming only one in the heading would have been the same defect in miniature.
  Checked across the item rather than within it: the 3x3 figures still match my brute force
  (paired-rainbow 1,872 / 8.47%, paired-two-tone 1,872 / 8.47%, paired-monotone impossible, trips
  52 / 0.24%), the share figures still match (paired and trips 17.18%, two-tone 55.06%, monotone
  5.18%, ace-containing 21.74%), the three-space continuation indent is consistent so the nested
  assignment renders inside the item, nothing in the item starts with `Answer:` so `decision_items`
  is unaffected, item 5's "three committed flops" agrees with the ruling, and item 8's "1,752 of
  1,755" is exactly 1,755 minus three. No paragraph in the item now contradicts another.

## Non-blocker

## Non-blocker

## Non-blocker

- **"the seven converged cells" (line 446) should be seven rows or five cells.** The report's
  aggregate says 7 of 30 rows reached target; those seven rows carry one distinct config sha for
  `matrix-02` and both determinism runs, so they are **five** distinct cells, which is what the
  same file says twice elsewhere ("the five converged cells cover two rank patterns", line 431).
  Decision 11 at lines 1027 and 1075 records this exact row-versus-cell correction being made once
  already, striking an "eight and six" draft that had counted the determinism row.

- **The `65 nodes per 1 GB` figure is right in decimal GB and 69 in binary, and the file has a
  standing rule about saying which.** Recomputed: the lean three-action node-line unit is 2 x
  7,740,095 = 15,480,190 bytes = 14.763 MiB = 15.48 MB, so 15.5 MB (line 707) is right; 1e9 /
  15,480,190 = 64.6 and 2^30 / 15,480,190 = 69.4. `DIRECTORY_BYTE_LIMITS` writes its existing entry
  as `20 * 1024 * 1024`, and decision 6 itself stops to state units "once, because this file already
  carries a cross-unit finding". A one-clause fix.

- **Decision 6's item 3 describes the two-action encoding and prices the three-action one.** Line
  705 names "one free weight per class", which is the encoding under which "one two-action node for
  one line measures 7,740,095 bytes" (line 522). The 15.5 MB it then calls the per-spot budget is
  that figure doubled - three actions, two free weights. The two sentences cannot both describe the
  same encoding, and the encoding is the thing the item said an answer must fix.

- **Item 3 calls itself the per-spot byte budget "including the provenance fields" and it excludes
  them.** Decision 6's own body (line 610) prices the provenance separately at 24 to 120 bytes a
  spot and says a per-spot cost has to include it. Over 1,755 spots that is 42 KB to 211 KB per
  line, 0.3% to 1.4% of one node-line unit - small, real, and not what item 3 states.

- **"If a flop needs ten of them, that is six lines and no more" (line 716) uses a node count the
  same file measures at five.** Line 601 says "under decision 11's pinned menu with `max_raises: 2`
  hero has about five flop decision nodes", and decision 11's ruling keeps the flop menu at `33 75`,
  so five still holds. At five nodes 1 GB is about 13 lines, not six. The direction is conservative
  and the conclusion survives, but the illustration contradicts the file's own measurement.

- **Decision 11's stack-off arithmetic is right and does not apply to the menu it justifies.**
  Recomputed at pot 5.5 and effective 97.5 (SPR 17.727 from the report's own rows): the three-street
  geometric size is 115.79%, so 116% is right; three 75% bets invest 40.219 and leave 57.281 behind,
  so 57.3 is right; 66.23% at the 3-bet pot's SPR 5.781 is right; and 103.9 / 115.8 / 130.9 at 77.5
  / 97.5 / 127.5bb all reproduce. But the ruled menu tops out at 75% on the flop. Running its
  deepest bet line, 75 then 125 then 125, invests 81.47 and leaves **16.03 of 97.5 behind, 16.4% of
  stack** (the 85% `allin_threshold` does not fire: the river bet is 79.0% of the stack behind).
  Through the small branch, 33 then 125 then 125 leaves **44.33 behind, 45.5%**. Only 125% on all
  three streets stacks off. So "125% brackets 116% from above where 75% cannot reach it" is a true
  sentence about a size the ruled menu never offers on the flop, and the ruling does not in fact
  give the ordinary pot a line that gets stacks in. The evidence gap on `66 125` is disclosed well
  (line 1124, "Nothing in the record uses 66% or 125%", called a wider gap than any option carried);
  it is the poker rationale that overreaches, not the labelling.

- **A ruling that retires the ceiling every arena verdict rests on is recorded in a subordinate
  clause.** Line 1115: "Taylor's ruling of 2026-09-10 moves solving to a larger machine, so that
  ceiling is not what decides this". No item carries it, no machine or RAM figure is named, and it
  retires the 12,026 MB ceiling that ruled out the pinned single-raised tree - which I confirm is
  21,281.9 to 21,715.1 MB across exactly eight `group: build` rows, as lines 1030 and 1114 state. Every
  timing in the phase is "Apple M4, 10 cores, 34.4 GB RAM"; a different machine moves all of them.
  Decision 11 does say to re-measure arena and ceiling, and decision 4 does say to re-derive the
  seconds per iteration, so the consequence is flagged even though the ruling is not recorded.
  Relatedly, and unlike decision 6, decision 11 never says whether Taylor named 66 and 125 or
  approved a coordinator proposal.

- **The two refusal causes decision 4 names cannot be told apart by anything this phase builds.**
  Line 477 requires the `refused` inventory to distinguish "a line or board never solved" from "a
  cell solved but over the 1% bound". A cell over 1% is not committed, so at query time both are the
  same miss. Distinguishing them needs a committed list of attempted-and-rejected boards with their
  achieved percents - new committed data that no contract criterion requires. The contract commits
  the covered set of *lines* explicitly (line 135) and says nothing about boards.

- **Decision 13 records one of the two costs its own item put up.** Line 1281 accepts the format
  cost squarely: "the artifact gets committed against a key format that nothing has been built
  against yet". The item's other measured cost, at line 1266, is that the contract was at 284 of 300
  lines and owes amendments from up to five rulings. It is now at **289 of 300**
  (`scripts/check_file_sizes.py:12` caps `docs/phase_contracts/*.md` at 300), and the amendment now
  owed is larger than when that line was written: decision 6's three unnamed criteria, plus the
  1,200 cap, the 1% commit bound, the new menu, the floor, pot and stack in the key, the artifact
  path, decision 7's halt replacing the tolerance branch at contract line 102, and the criterion at
  contract line 148 that requires the committed tree to stay inside 20 MB. `AGENTS.md` forbids
  raising the cap to fit an amendment. Eleven lines is the constraint the ruling accepted and did
  not record.

- **Decision 7's ruling contradicts a live contract line and the record says so; the edit is still
  owed in this task.** Line 766 rules a halt where contract line 102 still records "an accuracy
  target and the observed maximum divergence ... in place of the digest", and line 767 flags exactly
  that. `CURRENT_TASK.yml` is in `contract-update` with the contract in `approved_scope`, so this is
  a note about sequencing rather than a defect: the amendment can be made here and has not been.

- **"a tenfold improvement costs roughly 7x" (line 451) hides one end of its own band.** At the
  stated exponent 1.0 to 1.3 the factor is 10^(1/p), which is 5.88x to 10x. The halving claim is
  fine: 2^(1/p) is 1.70x to 2.00x, and "roughly 1.9x" sits inside it. I confirmed the exponent band
  itself from `matrix-02`'s committed curve: 1.02 over iterations 160 to 200 and 1.29 over 220 to
  240. I also confirmed the curve is one config, not spliced - 11.84 at 20, 3.55 at 40, 0.87 at 100,
  0.3297 at 220 and 0.2948 at 240 all come from config `410d61b135e3`.

- **Nit: no blank line before the `## 6.` heading at line 493.** It parses (the loop's own reader is
  line-oriented and CommonMark lets an ATX heading interrupt a paragraph), and it reads as though
  decision 5's answer runs into decision 6's title.

### Round 2 additions

- **NEW. The `about 24%` in decision 11's overbet reasoning is 32.0%.** Line 1219 says cutting turn
  and river from two sizes to one "bought 750,792 action nodes of 2,347,996, about 24%". 750,792 /
  2,347,996 = **31.98%**, and the arena ratio is 6,103.1 / 21,663.4 = 28.2%, so neither reading gives
  24. The argument the figure supports - a third size per street is the expensive direction - is
  strengthened rather than weakened by the right number, so the conclusion is unaffected.

- **NEW. The texture-weighted 56 to 66 days takes its width from the wrong uncertainty, and the
  original figure was mine.** Its band comes only from the 1.7 to 2.0 ns spread. The much larger
  unknown is rainbow's iteration count, which no row measures: at the 305 the same item extrapolates,
  the weighted campaign is about 45 to 52 days; at 760 it is about 72 to 85. So the honest band is
  roughly **45 to 85 days**, and 56 to 66 is the midpoint dressed as a range. I stated 56 to 66 in
  round 1 on a 500-iteration assumption I did not declare, so this correction is against my own
  number as much as the record's.

- **NEW. The 1bb stack tolerance is justified by a cross-unit comparison this file has already
  flagged twice, and the 0.5bb pot bound is not justified at all.** Lines 975-979 derive 1bb from
  "about 0.54 percentage points of size per bb of depth" - which I confirm, (130.9 - 103.9) / 50 =
  0.54 - and then conclude 1bb "is well inside the noise of a 0.3%-of-pot solve". Those are
  percentage points of **bet size** against a percent-of-pot **exploitability** bound, with no
  conversion between them; `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS` is filed against this
  same file for this same move, and decision 12 flags the solver notes for it a third time. The
  0.5bb pot bound, which is the one that actually binds, carries no derivation of any kind.

- **NEW. The tolerance bounds the geometry channel at exactly the error the entry it cites
  documents.** The re-pointed `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` says the
  tolerance "bounds the **geometry** channel". It does, in the sense that a bound now exists, but the
  bound admits the whole of the error the entry was filed about: the 2.25bb case is inside it by
  construction, and that case is pot 5.00 against 5.50 (9.09%), SPR 19.55 against 17.73 (10.27%) and
  geometric size 121.1% against 115.8% (5.3 points), all of which I recomputed. The entry is right
  that the range channel is untouched and larger; it should also say the geometry bound is set at the
  error rather than inside it.

- **NEW. A rented hourly GPU box against a 56-to-66-day campaign is a money cost, and nothing says
  so.** The machine note rules "a rented cloud machine with an NVIDIA GPU, hourly rather than
  purchased". Decision 4's own campaign figures are 17.9 to 105 days of continuous compute per
  preflop line, and even at the untested ~10x CUDA speedup the note correctly refuses to use, a
  texture-weighted line is about 5 to 7 days of continuously rented GPU. Multiply by the covered line
  count, which decision 6 makes an output. I have no price to put on it and must not invent one, but
  a phase whose ruled hardware is metered by the hour and whose campaign is measured in weeks owes
  the reader that sentence. This is the largest accepted cost in the phase that is still unwritten.

- **NEW. `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` is on the contract's Closed list on a premise the
  machine ruling removes.** The contract closes it, and the reason recorded everywhere is that
  GTOpen's guard reads `/proc/meminfo`, "which does not exist on Darwin". The machine note moves
  solving to a rented cloud box, which will almost certainly be Linux, where `/proc/meminfo` exists
  and the guard becomes live with real readings rather than the flat 48,000 MB fallback. That changes
  the contract criterion "The solve driver carries its own memory ceiling and refuses above it before
  solving", whose stated justification is that the solver's own guard cannot fire. Neither the
  machine note nor the contract's Closed list mentions it.

- **NEW. The refusal inventory now has three causes, not the two decision 4 names.** Decision 4's
  closing paragraph (lines 504-508) already concedes that "never solved" and "solved and over 1%"
  cannot be told apart at query time and files it. Decision 6 adds a third that is distinguishable
  and unmentioned: **solved, under 1%, and not fetched** - a spot whose cell is in object storage and
  not on this machine. That is a refusal a fresh clone will produce constantly, it is the one of the
  three the bot can actually name, and no criterion covers it.

- **NEW. "part of the three the Scope section already owes" understates the amendment.** Decision 6's
  accepted-cost paragraph says the index-plus-sample restructure is part of the three criteria the
  contract already owes. It is not: beyond the encoding, the byte budget and the line count, it also
  moves contract line 148 (the committed tree inside 20 MB, bytes used and headroom printed), the
  criterion requiring every committed spot to record its exploitability, iteration count and digest -
  now the index rather than the artifact - and the criterion that the artifact does not land in
  `data/artifacts/preflop/`. With the contract at 289 of 300 lines that is the constraint decision 13
  accepted and did not record, and it is now larger than when I first raised it.

- **NEW, and it is a positive finding because it was asked.** The reading of "We can just do 66-125
  for turn and river. That's fine." as the ruling is defensible, and decision 11 records it honestly:
  it says Taylor raised 200%, quotes him, says the coordinator's reasoning was put in front of the
  choice, labels that reasoning as reasoning rather than measurement, and files the settling
  experiment - `66 125` against `66 200` on the turn, one board and both ranges held - as stage 6
  before anything commits. The river arithmetic behind it checks out: after `33` called and a 200%
  turn called, 200% of the river pot is 91.30 against 77.43 behind, so it converts to all-in. One
  sentence would improve it: Taylor did not reject 200% on evidence, he accepted the coordinator's
  reasoning about it, and the menu is frozen into the first solve before the experiment runs.

### Round 3 additions

- **The 2.0-3.0 band is a coverage rule, not a sensitivity-derived one, and it admits about
  three-quarters of the spread the item cites to justify refusing at all.** Computed at each end:
  an open of 2.0bb gives pot 4.50, effective 98.00, SPR 21.778 and a three-street geometric size of
  **127.26%**; 3.0bb gives pot 6.50, effective 97.00, SPR 14.923 and **106.81%**; the cell sits at
  115.79%. So the band admits **20.45 points** of geometric size. Decision 10's own justification for
  putting pot and stack in the key is the spread 103.94% to 130.91% at 77.5 to 127.5bb effective,
  which is **26.97 points** - so the tolerance lets through **75.8%** of exactly the variation the
  item calls "a materially different strategy". The record argues the band purely from coverage
  ("every ordinary open size in the corpus is inside; a limp-raise or a 4bb open is out") and gives no
  sensitivity derivation, which is honest as far as it goes but leaves a reader thinking the bound
  was measured. I am not asking for a tighter band - tighter is what refuses ordinary opens, which is
  the thing Taylor correctly rejected - and this does not hold the stage because the tolerance is a
  query-time rule whose later change costs a frozen-test edit rather than a re-solve. What it needs
  is one sentence saying the band is chosen for coverage, that it admits up to 20.45 points of
  geometric size, and that this is why decision 10's key segments refuse almost nothing on the
  100bb single-raised set - which the "What this accepts" paragraph already half-says.

- **The `>=`/`>` hazard is reduced and relocated, not eliminated, and the relocation lands on two
  ordinary sizes.** 2.25 is now 0.25bb inside the band, which is the fix. But the endpoints are 2.0
  and 3.0, and both are ordinary opens - a min-open and a standard 3x - so the boundary case is still
  reachable by real play rather than only by a limp-raise. Writing "The endpoints are inclusive and
  stated so" is the right mitigation and the reason given for it is the wrong one: the record says it
  is because "the previous draft's whole failure was a boundary nobody wrote down", when the reason it
  matters here is that real hands land exactly on 2.0 and 3.0. One clause.

- **The 16-hex digest precedent is mine and it does not transfer, which is the real argument for
  making the digest width a declared choice.** `ca16cf82eeb9c96e` in
  `latest_postflop_solve_cost.txt` is a **determinism** digest, compared against a second run of the
  same computation on the same machine. Decision 6's index digest does a different job: it
  authenticates an object fetched from third-party storage the repo does not control. Against
  accidental corruption 64 bits is ample - at 8,775 entries x 14 lines, about 123,000 objects, the
  birthday collision probability is roughly 123,000^2 / 2^65, about 4e-10 - but against a deliberate
  substitution 64 bits is roughly 2^32 work to collide, which is feasible. So the width is a security
  choice wearing a byte-budget hat, and the 1.75x it costs in coverage (8 lines at full sha256
  against 14 at 16 hex) is the cheaper half of the question. It belongs in the per-spot byte budget
  amendment with this arithmetic beside it, not in a new human gate, because there is only one
  defensible answer once the purpose is named.

- **Items 3 and 7 of decision 6 now disagree about which constraint binds coverage.** Item 3 ends
  "the index is a real constraint to design against"; item 7 says "With object storage the binding
  constraint is decision 4's campaign cost, not bytes". At the corrected sizing the index caps
  coverage at 8 to 14 lines, and a GPU campaign at even the untested 10x puts a texture-weighted line
  at 4.5 to 8.5 days, so a few months of rented compute buys more lines than the index can hold. Item
  7 is the stale half and item 3 is right; leaving both means the phase designs coverage against
  whichever sentence a reader met first. Same shape as the cap-versus-campaign contradiction I raised
  in round 1, one level down.

- **The sample ruling constrains the suit axis and leaves the rank axis, which the notes call a
  separate gap.** `docs/GTOPEN_SOLVER_NOTES.md`'s "Not verified" list says "Most board structures,
  not only rainbow. Five cells converged, on two rank patterns. Never reached the target:
  rainbow-dry, rainbow-connected, paired, ace-high connected, and disconnected-low. **A paired board
  is a structural gap rather than a suit one.**" Decision 4's own third qualification repeats it -
  "So is every paired, ace-high and disconnected board: the five converged cells cover two rank
  patterns". One rainbow, one two-tone and one monotone satisfies the suit split and can still be
  three unpaired, non-ace-high boards, which reproduces the rank-pattern gap inside the only artifact
  the gate measures. The stage-4 choice is genuinely narrower than before and this is not the old
  deferral back again, but it still carries a frozen consequence on an axis the record names
  elsewhere as distinct. One clause in item 4 would close it.

- **The third refusal cause is still unnamed, and the judgment about the contract is right while the
  answer misses the finding.** I agree that a contract criterion for the refusal inventory is stage-4
  work; that was never what I asked. What is missing is in the ruling itself: decision 6's design
  produces a refusal the record never mentions - a spot that is in the index, under 1%, and not on
  this machine. It is the only one of the three causes the bot can actually name, a fresh clone will
  produce it for 1,752 of 1,755 classes, and nothing says whether it has its own code or whether the
  strategy refuses to start unprovisioned. Decision 4's closing paragraph still says two causes.
  One sentence in decision 6, not a contract criterion.

### Round 4 additions

- **6.0-9.0 is symmetric in form and the looser of the two bands in effect, and the coverage-rule
  paragraph carries only the open's numbers.** Computed with the record's own pot structure - the
  3-bet pot is `2 x price + 1.0`, which reproduces its committed 16.0 at 7.5 and the 15.0 it quotes
  at 7.0. At a 3-bet of 6.0: pot 13.00, effective 94.00, SPR 7.231, three-street geometric size
  **74.56%**. At 9.0: pot 19.00, effective 91.00, SPR 4.789, **59.76%**. Against the cell's 66.23%
  that is **14.80 points** admitted. Fewer points than the open band's 20.45, but on a much smaller
  base: **22.35% of the solved size against the open band's 17.66%**. The SPR ratio across the band
  is 1.51 against the open's 1.46, and the pot moves +/- 3.0bb against the open's +/- 1.0bb. So a
  single 20% rule is not neutral between the two pot types; it is looser where SPR is lower and the
  strategy is more sharply determined by it. The new coverage-rule paragraph is written entirely
  about the open - 127.26 / 106.81 / 115.79, 20.45 of 26.97, 75.8% - and stops there. It should
  carry the 3-bet row too.
  **And the coverage justification has no measurement behind its 3-bet half.** The stated reason for
  the band is that it admits "the opens the corpus actually contains"; the record gives the corpus
  median open, 2.25bb, and gives **no corpus figure at all for 3-bet sizes**. So for the half of the
  rule that covers most of the phase's measured evidence, the only justification is a poker claim
  with no number, which this repo treats as a defect. One query over
  `ComparisonRow.asked_spot_key` would settle it, the same instrument decision 3 already uses.

- **Item 7's new "the campaign puts its own limit in the same range" has no divisor.** It says
  "decision 4's campaign at 45 to 85 days a line puts its own limit in the same range" as the
  index's 8 to 14 lines. Turning a per-line duration into a line count needs a total time budget,
  and nobody has stated one: 8 to 14 lines at 45 to 85 days is 360 to 1,190 days of compute, or 36
  to 119 at the untested 10x the machine note correctly refuses to use. Either could be the intent
  and neither is written. The conclusion - both constraints bind, neither can be assumed smaller -
  is right and is the fix I asked for; it is the "same range" clause that asserts more than the page
  supports. Drop the clause or state the budget.

- **Three sample boards cannot cover the five rank structures the notes name.** Item 4 now says
  "Stage 4 picks boards that vary rank structure as well as suit", which takes the finding. The
  solver notes' "Not verified" list names five structures never reached at target - rainbow-dry,
  rainbow-connected, paired, ace-high connected, disconnected-low - against three sample boards and
  three suit textures already spoken for. The sample necessarily leaves some, so "vary rank
  structure" is the most that fits and the record should say which structures it is knowingly
  leaving out rather than implying both axes are covered.

- **"within 20%" has two readings and the concrete endpoints are what settle it.** Price x (1 +/-
  0.2) gives 2.0 to 3.0; a ratio band [price / 1.2, price x 1.2] gives 2.083 to 3.0. The record
  states both bands concretely, so no ambiguity survives in practice - but the general form is what
  a later price inherits, and only the first reading reproduces the stated endpoints. A note for
  whoever implements it, not a defect in the ruling.

### Round 5 additions

- **The new backlog entry duplicates a filed one, and the filed one has the better diagnosis.**
  `ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE`, filed by phase 14's stage-6 poker
  review, already records this defect and names its **cause**: "The source solves `open_raises:
  [2.5]` with `raise_mults: [3.0]`, which yields exactly four prices in the whole artifact - 2.5,
  7.5, 22.5 and the 100bb jam ... the big blind three-bets to 7.5 out of position against a 2.5
  button open, laying 2.1 to 1 where a real out-of-position three-bet is **10 to 11bb**". Its
  closing sentence is the new entry's conclusion: the schema "does not become a sizing strategy
  until the solved tree carries more than one non-all-in price per round."
  So `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` re-derives a filed finding without
  citing it, and frames it one level shallower - as a *price* that is mis-centred rather than a
  *multiplier* that is wrong. The measurement I took gives the parameter-level number the existing
  entry lacked: **the corpus 3-bet is a median 4.00x and mean 4.077x of that same hand's own open**
  (n=87), against the chart's `raise_mults: [3.0]`. That is the thing to change, and it is one
  config field rather than a coverage choice. Fold the measurement into the existing id and
  cross-reference from the new one, or retire the new one; and correct the existing entry's "10 to
  11bb" estimate, which the corpus puts slightly lower at a 9.25 median.

- **The 4-bet half of the same existing entry can now be checked, and it is roughly right and
  slightly overstated.** The entry says "the four-bet at 22.5 is 3x where real four-bets are 2.2x to
  2.5x". Measured: the corpus 4-bet median is 25.35bb against a 3-bet median of 9.25, so **2.74x** -
  above the entry's estimated range and below the chart's 3.0x. And a 20% band around the chart's
  22.5, 18.0 to 27.0, would cover **11 of 19, 57.9%** - better centred than the 3-bet price is. n=19,
  so this is a direction rather than a figure to plan against.

- **Re-centring alone does not fix the 3-bet band either, which strengthens the ruling's
  conclusion.** Holding the same 20% width and moving the centre: 7.5 gives 47.1%, 8.0 gives 50.6%,
  8.5 gives 57.5%, 9.0 gives **60.9%** at best, 9.25 gives 59.8%, 10.0 gives 56.3%. So the best
  centred 20% band still refuses about two 3-bet pots in five, because the real distribution runs
  5.25 to 14.0bb around a 9.25 median and no 20% band holds it. The record says widening does not
  rescue it; the sharper statement is that **neither widening nor centring rescues it, because one
  price cannot serve this distribution** - which is precisely the existing entry's conclusion,
  reached independently.

- **One figure in the new entry does not reproduce.** It says answering "a 12bb 3-bet pot from a
  7.5bb cell moves SPR from 5.78 to about 4.0". Using the pot structure the entry's own 16.0 and
  15.0 figures imply, `pot = 2 x price + 1.0`: at a 12bb 3-bet the pot is 25.00, the effective stack
  88.00, and SPR is **3.52**, not about 4.0. The slip is in the direction that makes the defect look
  milder, and the point it supports survives at the right number.

- **The measurement has a consequence for decision 3 that nobody has drawn.** Decision 3 ranks the
  covered preflop lines by how often the corpus reaches them. A 3-bet line costs the same campaign
  time as a single-raised line - decision 4's 45 to 85 days either way - and serves 47.1% of its
  arrivals against 99.0%. So the ranking is by arrival frequency where the thing that matters is
  **servable** arrival frequency, and a 3-bet line buys roughly half the coverage per solved line.
  Decision 3 is ruled and I am not reopening it; what needs a sentence is that the ranking method
  now has a known distortion, in the pot type where five of the seven converged rows sit.

- **On item 7's "same range" clause, which you did not act on: it does not need to be in the record
  before stage 4, and it does need to be in the fold-in rewrite.** No stage-4 test reads that
  clause, so freezing tests against it is not a risk; the harm is a campaign planner believing both
  constraints are equally quantified when only the index is. The rewrite is restating the line-count
  criterion anyway, so that is where the divisor or the deletion belongs. Not stage-holding.

- **On the sample's rank structures, which you also did not act on: this one does need to be in the
  record before stage 4, and the reason is the phase's own principle.** Stage 4 picks the three
  boards and authors the tests that pin them; stage 5 freezes them. If the record does not say which
  rank structures three boards are knowingly leaving out - the notes name five never reached at
  target, rainbow-dry, rainbow-connected, paired, ace-high connected and disconnected-low - then a
  later reader cannot tell whether the omission was chosen or forgotten. That is the distinction
  decision 3 and decision 6 both insist on for preflop lines, in the phase's own words: "a refusal
  names a line that was excluded rather than one that was forgotten". One sentence in item 4 naming
  the structures the sample will not carry, written before stage 4 rather than after the boards are
  frozen.

### Round 6 additions

- **The two-entry division is right, and its stated justification is the wrong one.** Keeping
  `ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE` as the cause and
  `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` as the consequence passes the only test that
  matters: the consequence survives the cause's closure. Fix `raise_mults`, re-solve the preflop
  chart, and the cause entry closes - but every postflop cell phase 16 commits is already keyed to
  `@7.5` and still refuses the new prices, so the consequence entry stays open until the postflop
  3-bet cells are re-solved. Different fix, different owner, different phase. Do **not** withdraw the
  newer entry into the older one.
  What is wrong is the symmetry: both entries say "neither closes without the other". That is true
  in one direction only. The cause can close while the consequence stands, and it is exactly that
  asymmetry that justifies two ids. Say so in both, and the division stops needing defence.

- **The servability correction is in the right item for its derivation and the wrong one for its
  reader.** Decision 10 lines 1086-1092 are the right place to derive it, because that is where the
  47.1% lives. But whoever computes the ranking at stage 6 reads decision 3 and the contract's
  covered-set criterion, not decision 10, and decision 3 already carries four dated "Annotated /
  Corrected ... not re-ruled" blocks - one of them, 2026-09-08, is this exact shape: "method only;
  the ruling is untouched". A servability correction is a method correction with the ruling
  untouched, so the file's own convention puts it there. Leaving it only in decision 10 is the
  failure this file names about itself: "the eighth time in this file a correction has reached one
  item and not its siblings." A pointer in decision 3 is enough; the derivation stays where it is.

- **Correcting a figure of my own.** In round 4 I said the three-flop sample is "about 88 KB by the
  same rate". That is per preflop line. At three boards x about five hero nodes x 15,480,190 / 1,755
  bytes a board-node it is 132,300 bytes a line, and across the 8 to 14 lines the index affords it
  is **1.06 to 1.85 MB**, or 7% to 12% of the 15,774,195 bytes free. Not negligible against the
  index's own 1.14 to 2.02 MB a line, and it belongs in the same budget rather than beside it.

- **The sample gives a third of its slots to the texture that is already measured.** Monotone is
  1,144 boards, 5.18% of flops, and it is the texture six of the seven converged rows already sit
  on; two-tone is 12,168 boards, 55.06%, and gets the same one slot. Defensible - the sample exists
  so the gate sees one of each class, and monotone is the cheapest to solve - but worth one sentence,
  because a reader who meets "one per texture" will not guess that the split is 39.76 / 55.06 / 5.18
  and that the phase's existing evidence is concentrated in the smallest of the three.

### Round 8 additions

- **Item 4 re-reads the solver notes' five never-reached entries as rank structures and drops their
  suit qualifiers, which is what lets the sample count "connected" as covered.** The notes' "Not
  verified" list names five *cells*: rainbow-dry, rainbow-connected, paired, ace-high connected and
  disconnected-low. Item 4 calls them "the five never-reached rank structures" and re-cuts them as
  dry, connected, paired, ace-high-connected and disconnected-low, which is what makes the ruled
  assignment cover three of five. Under that reading the item is internally consistent and its
  "knowingly left out" enumeration is right. But the cell that never reached target was
  **rainbow**-connected, and the sample's connected board is **two-tone**, so a solved two-tone
  connected board says nothing about the cell that failed. The same applies in the other direction
  to paired, which the notes list unqualified and the sample takes at rainbow. One clause fixes it:
  say that the list is being read as rank structures, that the suit pairings the notes actually
  recorded as never-reached are not the pairings in the sample, and that rainbow-connected is
  therefore left out as a cell even though connected is covered as a structure. Not a
  contradiction, and the sample is not worse for it - three boards cannot do better - but a reader
  should not have to reconstruct which of the five failures the sample actually touches.

- **[Round 8: both fixed.] `NO-POKER-REVIEW-HAS-SEEN-THE-RULINGS-TAKEN-AFTER-STAGE-2` is filed as `phase: "16"` and its own
  text says it is not a phase-16 item.** The entry closes with "This is the general defect rather
  than phase 16's instance: the loop places its poker review after the point at which its poker
  choices stop being reversible." Its siblings in that family -
  `A-CONTRACT-CAN-NAME-A-FROZEN-CHOICE-NO-DECISION-ITEM-CARRIES`,
  `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`, `TWO-FROZEN-QUESTIONS-SHARE-ONE-ANSWER-SLOT` - are
  all `phase: contract-update`, which is where a loop defect belongs. Left as `"16"` it gets swept
  when phase 16 closes, and either closed on the phase's own poker review having happened or left
  deferred against a completed phase, which is the blind spot
  `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` records. One field.

- **[Resolved in round 8 by renaming to `A-REVIEW-NOTE-RECORDS-ITS-FINDINGS-BUT-NOT-ITS-ROUNDS`.]
  `A-STAGE-THAT-TOOK-SIX-REVIEW-ROUNDS-LOOKS-LIKE-ONE-THAT-TOOK-ONE` hard-codes a count that is
  already wrong.** This is round seven. `AGENTS.md`'s naming rule is that names describe what the
  thing does rather than which phase or count produced it, and the general defect needs no number:
  something like `A-REVIEW-NOTES-ROUND-COUNT-IS-NOT-RECORDED` says the same thing and cannot go
  stale. The body should keep the count, because the count is the evidence. Its factual claim checks
  out as written - at least one blocker in each of rounds 3 through 6 was found in text written to
  fix the previous round's, and the round-7 blocker above makes it four rounds of five.

## Alignment

- `DECISION-ANSWER-FIELDS-DIVERGE-FROM-THE-RULINGS-BELOW-THEM` - the general form of the first
  blocker. That entry was filed against phase 14 for an `Answer:` field naming a superseded option
  while the body recorded a re-ruling; here the field says ruled and the body says blocking, which
  is the same divergence with the polarity flipped. The entry's own prescription still fits: either
  the field always carries the current answer or the driver reads something else.

- `TWO-FROZEN-QUESTIONS-SHARE-ONE-ANSWER-SLOT` - decision 4 still holds two frozen questions, the
  target and the fate of a cap-bound cell, and one `Answer:` line now discharges both. The entry
  records the stage-2 fix as splitting reproducibility out into decision 7; the pair that remained
  inside decision 4 was not split, and lines 437-439 show the coordinator knowing that and writing
  the answer anyway. The entry's proposed keyword check (a heading containing " and what ") would
  flag this heading - "Exploitability target, and what happens to a cell that never reaches it".

- `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` - the 10-day campaign figure is this
  entry's exact shape a second time in the same document: every input is published in the same
  paragraph, the arithmetic is checkable from the page, and nothing checked it. The entry notes it
  matters because the projection is the whole evidence for a `frozen-into-data` decision that halts
  on a human. That is true again, and this time the direction understates the cost.

- `THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` and
  `POSTFLOP-CELLS-ARE-STACK-FRAGILE-WHERE-THE-PREFLOP-CHART-IS-NOT` - both entries describe
  "decision 10's payload validation", and decision 10's ruling removed the payload validation. Both
  reason texts are now stale in the same clause, and the first is the entry decision 8's answer
  points a reader at (line 836). Same family as
  `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT`, and the phase cannot close
  either while its diagnosis names a mechanism that no longer exists.

- `NO-MENU-IN-THE-RECORD-OFFERS-AN-OVERBET` - the entry says "Every menu in the record caps at 75%
  of pot on every street" and that all four options share the gap. The ruled menu overbets at 125%
  on turn and river, so the entry is falsified on its later-street half and still true on the flop,
  where the top size stays 75%. It needs re-pointing rather than closing.

- `A-SIZE-BUDGET-EXCLUDES-THE-PROVENANCE-THE-CONTRACT-MANDATES` - decision 6's ruled item 3 repeats
  the omission the entry was filed for, one stage later and now inside an answer rather than a
  default.

- `DECISION-LIST-HAS-NO-FIXED-PLACE-FOR-A-RULING` - covers the machine-change ruling at line 1115.
  The entry's diagnosis is that a list with no convention for where a ruling goes can hold a ruling
  its own headers do not show; a ruling that belongs to no item at all is the limiting case, and the
  entry's proposed fix - a summary section at the head plus the full record beside the item it
  settles - would give it a home.

- **Proposed, not filed:** `COMMITTED-DATA-BEHIND-A-NETWORK-FETCH-BREAKS-AN-OFFLINE-GATE`. Nothing
  in `backlog.yml` covers the general defect the LFS ruling opens: this repo's gate is required to
  pass with no network, `check_file_sizes.py` measures whatever bytes are on disk, and any
  smudge-filtered or fetched-on-demand artifact makes both the gate's verdict and every byte figure
  a function of how the clone was made. It is a rule question rather than a phase-16 question, which
  is why it wants its own entry rather than a line in decision 6.
  **Round 2: filed, and it describes the defect rather than the instance.** I read the committed
  entry. It states the general rule first, names git LFS as the concrete case and any smudge-filter
  or fetch-on-read scheme as the general one, puts phase 16's own history in its own paragraph, and
  asks for the rule in `AGENTS.md` beside the offline-first sentence: "committed data means bytes
  present in a fresh offline clone, and a mechanism that defers the bytes is not a way to commit
  data." Attribution is correct - proposed by this review, filed by the coordinator. Accepted as
  written.

### Round 2 additions

- `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` - carries the first new blocker. The entry already
  records the reading as settled ("the class says 'committed artifact or fixture', and a behaviour
  default a contract requires a frozen test to pin is a fixture"), and phase 16 has now produced the
  fourth instance and classed it reversible anyway. The entry says the remaining fix "may be a
  documentation clarification rather than a third class"; this instance is the argument for doing it,
  because the class was applied to a threshold that decides whether the corpus's median open is
  played.

- `A-CONTRACT-CAN-NAME-A-FROZEN-CHOICE-NO-DECISION-ITEM-CARRIES` - carries the third new blocker. The
  entry was filed because phase 16's key grammar and bet menu were frozen choices on no list; the
  committed sample's texture is the same shape one stage later, created by a ruling rather than by an
  omission, which is if anything harder to catch.

- `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` - the constraint the sample
  choice has to satisfy. Six monotone rows and one two-tone, 5.18% of boards, and rainbow at 39.76%
  of boards with zero converged rows. A two-flop monotone sample would put the phase's known blind
  spot into the only artifact the gate can see.

- `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` - third and fourth occurrences in this
  one document: decision 6's index sizing and decision 11's "about 24%". Both have every input on the
  same page, and in both cases nothing checked the arithmetic. The entry's own diagnosis - "an
  inflated multiple sends a ruling in the wrong direction as surely as a deflated one" - applies to
  the index figure, which is deflated and is the ruling's feasibility claim.

- `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS` - the 1bb tolerance's justification compares
  percentage points of bet size to a percent-of-pot exploitability bound. Third appearance of this
  move in this file, and the first inside a ruling rather than a default or a quoted note.

- `A-SIZE-BUDGET-EXCLUDES-THE-PROVENANCE-THE-CONTRACT-MANDATES` - now inverted and worth re-pointing.
  The entry was filed because a budget priced the payload and omitted the provenance; decision 6's
  index budget prices the provenance and omits the key, which is the largest field in the entry. Same
  failure, opposite half.

- `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` - closed by this contract on the premise that GTOpen's
  guard cannot fire on Darwin, while the machine ruling moves solving to a box where it can. It needs
  re-reading before the contract's Closed list ships.

- **Proposed, not filed:** `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`. The new
  `COMMITTED-DATA-BEHIND-A-NETWORK-FETCH-BREAKS-AN-OFFLINE-GATE` entry covers the **gate**, and
  decision 6's resolution genuinely fixes that. What no entry covers is the product: after this phase
  a fresh clone holds a flop strategy for a couple of sample boards and an index of digests for the
  rest, so the bot's advertised capability needs a provisioning step the repo does not perform. Git
  still holds the digests, so integrity survives - that is the mitigation and the record should say
  it is the mitigation. `AGENTS.md`'s "Git is the source of truth" and "offline-first" both want a
  sentence about what they mean once the artifact the bot plays lives elsewhere.
  **Round 3: filed**, and the round-3 entry below records what I checked in it.

### Round 3 additions

- `NOTHING-SWEEPS-DEFERRED-BACKLOG-ENTRIES-A-LATER-TASK-FALSIFIED` - carries the second new blocker
  and is now on its third occurrence. The entry's own words: these entries "are the instructions the
  next lane reads, so a falsified one does not merely mislead", and "All three were corrected by hand
  because someone read them, which is not a mechanism." Two rounds ago I found the same two entries
  stale against a mechanism decision 10 had removed; they were re-pointed by hand; the mechanism was
  then withdrawn again and they are stale again. That is the argument for the mechanism the entry
  asks for, made twice inside one stage.

- `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` - the precedent for the third new blocker, and the entry
  records how it ends: two amendments named as waiting on a fold-in rewrite that has not happened,
  and a contract that only stayed under the cap by re-wrapping its own paragraphs. Phase 16 is at 289
  of 300 with thirteen amendments owed, which is worse than the state that entry describes. A phase-16
  sibling is **proposed, not filed**: `PHASE-16-OWES-MORE-AMENDMENT-THAN-ITS-CONTRACT-HAS-LINES`,
  unless the coordinator prefers to extend the existing entry, which would keep one place for the
  rule rather than two instances of it.

- `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT` - **filed, and accepted as written.** It
  states the general shape, judges the trade acceptable rather than wrong, names the digests as the
  mitigation, tracks the sample ruling correctly ("bet on 3 of 1,755 flop classes"), and asks for the
  distinction wherever coverage is claimed. Attribution is right. This is also the entry that should
  pick up the unnamed third refusal cause if decision 6 does not.

- `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL` - carries the rank-axis half of the sample gap. It is the
  entry the contract already cites for "every paired, ace-high and disconnected board", and it is
  where the constraint on the stage-4 board choice belongs if item 4 does not take it.

- `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS` - **discharged for this stage.** The cross-unit
  justification I raised in round 2 is gone with the two-bound tolerance; the replacement is stated
  in big blinds of opening size throughout and compares nothing across units. The general entry
  stands on its earlier instances.

- `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` - **the reading held under test.** Phase 16 produced the
  fourth instance, classed it reversible, and the class was corrected to `frozen-into-data` on the
  entry's own settled reading rather than by stretching anything. That is evidence for the
  documentation clarification the entry proposes and against a third class, and it is worth recording
  on the entry that the reading survived an adversarial use.

### Round 8 additions

- **Where the re-read remedy belongs: `docs/LOOP.md`, as a stage obligation, not `backlog.yml`.**
  You asked. `backlog.yml` is where a diagnosed defect waits for someone to own it, and this is not
  waiting for anything - the remedy is known, costs nothing, and has no owner precisely because it
  is a practice rather than a task. `docs/LOOP.md` already encodes practices as stage obligations
  in exactly this shape: "a stage that changed anything a human wrote owes read-only review notes
  before `--advance` will move", and the driver "prints the question to ask, where to write the
  answer, and what it must contain". The sibling obligation is one line: **an edit that supersedes
  existing prose owes a re-read of the containing paragraph before the stage advances, by whoever
  made the edit.** In `docs/LOOP.md` it is part of what a stage is; in `backlog.yml` it is a note
  nobody is assigned. `AGENTS.md` is the fallback if `docs/LOOP.md` is judged the wrong file - its
  Contract Amendments section already carries a rule from this same family, and for the same
  reason.
  I will say the uncomfortable half too. A rule that depends on somebody remembering it is the
  weakest form of this, and eight rounds of this stage are the evidence: the rule was stated in
  round 7, agreed in round 8, and broken in the round-8 edit that produced the blocker above. So
  write it down, and do not expect writing it down to be what fixes it.

- **Correcting myself on whether a check is possible, because I said no too flatly.** In round 7 I
  said no check catches this class and I did not propose one. That is right about detecting the
  **defect** - a script cannot tell a superseded sentence from a deliberate qualification - and it
  is too flat about detecting the **risk condition**. A pure insertion into an existing paragraph,
  additions with no deletions inside a block that already had text, is computable from a diff and
  would have flagged three of the seven outright, including the round-7 splice and the round-1
  `Answer:` slots. A looser form - a paragraph left untouched while an adjacent paragraph in the
  same section was rewritten - would reach most of the rest and would be noisy. Neither is a check
  that fails a gate; both are the sort of thing the driver could print as a prompt at the point of
  the edit, which is where the remedy actually has to land. That is a better answer than the one I
  gave and it is a correction to my own note rather than to yours.

### Round 7 additions

- **All three held-back items are filed, and I checked the wording against what I wrote rather than
  against the summary.** `NO-POKER-REVIEW-HAS-SEEN-THE-RULINGS-TAKEN-AFTER-STAGE-2` is faithful and
  states the general defect better than I did: "the loop places its poker review after the point at
  which its poker choices stop being reversible." It keeps my own admission of what I cannot judge,
  which is the part that makes it honest rather than a complaint about somebody else.
  `A-REVIEW-NOTE-RECORDS-ITS-FINDINGS-BUT-NOT-ITS-ROUNDS`, filed in round 7 under a name carrying
  the count and renamed in round 8, is faithful and adds a concrete
  mechanism I had not proposed - a round count and a per-round finding count in the note's own header
  - and its list of what a single pass would have shipped is accurate to this note. The extension to
  `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` is faithful and sharper than
  my version: "The turn overbet comparison decision 11 files for stage 6 is the only planned
  measurement that would see it at all, and it compares two menus rather than testing either." I did
  not write that and it is the better sentence. Two field-level problems on the first two are in
  Non-blocker above; neither is about the wording.

- `DECISION-ANSWER-FIELDS-DIVERGE-FROM-THE-RULINGS-BELOW-THEM` - **the entry's scope is too narrow
  by a factor this stage has now measured, and this is the last thing I want on the record.** The
  entry is written about a decision item's machine-read `Answer:` field diverging from its body.
  Across seven rounds this stage produced **seven** instances of the wider class, and only the first
  was in an `Answer:` field: the two `Answer:` slots against "stays blocking" in round 1; decision
  10's ruling sentence keeping its withdrawn predecessor in round 4; the ExecPlan Bootstrap's "open,
  and not to be invented" bullet in round 4; the fold-in bullet's bold lead-in in round 5; item 4's
  two rainbow boards against its own suit split in round 6; and item 4's spliced opener and three
  stale rank sentences in round 7. Every one has the same mechanism: **new text was inserted and the
  sentences around it were not re-read.** None of the last six is visible to any parser, so
  `unresolved_blockers` and `unanswered_frozen` cannot catch them and neither can a check of that
  shape.
  I am not proposing a check, because I do not think one exists for this. What I would put on the
  entry is the measurement and the mechanism, because they change what the entry is for: it reads
  now as a convention problem about one field, and what it describes is the dominant defect class in
  a stage that took seven rounds. The remedy that would have caught all seven is a re-read of the
  whole paragraph after every insertion, by the writer, before the reviewer sees it - which is
  cheaper than a review round and is the one thing seven review rounds could not substitute for.

### Round 6 additions - what I had been holding back

These are not findings about this diff. They are things I noticed across six rounds that never fitted
a bullet, put here because the stage is closing and the coordinator asked. **Round 7: all three are
now filed in `backlog.yml`**; the round-7 note above records what I checked in each.

- **Proposed, and filed 2026-09-10:** `NO-POKER-REVIEW-HAS-SEEN-THE-RULINGS-TAKEN-AFTER-STAGE-2`. This phase's
  only poker review is the stage-2 one, dated 2026-09-09. Everything decided since is unreviewed as
  poker: the bet menu `33 75` / `66 125` including the withdrawn stack-off rationale and the declined
  200% turn size, the range floor's interaction with that menu, the 20% price bands, the three-board
  sample and its textures, and the 1% commit-or-refuse bound. Those are the phase's poker content,
  and the reviews that have touched them - all six of mine - are mechanical and arithmetic. I can
  check that 116% is the geometric size and that a paired board is never monotone; I cannot tell you
  whether `66 125` plays better than `66 200`, and this repo has no oracle that can. The loop's
  domain review arrives at stage 8, after the artifact is committed against every one of these. The
  stage-2 note already made this argument once for a different reason - "the loop's poker-facing
  review arrives at stage 8, after the artifact is committed against rulings taken at stage 3" - and
  the rulings it was worried about have now all been taken. Nothing in `backlog.yml` owns it;
  `A-CONTRACT-CAN-NAME-A-FROZEN-CHOICE-NO-DECISION-ITEM-CARRIES` is about whether a choice gets an
  item, not about who reads it.

- `A-FLOP-ONLY-STRATEGY-IS-SOLVED-ABOVE-A-TURN-THE-BOT-DOES-NOT-HAVE` - **worth extending, because
  the ruled turn and river sizes cannot be found wrong inside this phase.** The entry says the
  committed frequencies assume a continuation the bot refuses. The sharper version, which the menu
  ruling makes live: `66 125` is frozen into every committed flop cell through continuation values,
  and this phase commits no turn data, publishes no turn strategy, and has no oracle for flop
  frequencies. So there is no observable inside phase 16 that a wrong turn menu could move. It is
  the only frozen choice in the list with no failure mode the phase can detect, and the record
  should say so where the entry already says the neighbouring thing.

- **Proposed, and filed 2026-09-10 as `A-REVIEW-NOTE-RECORDS-ITS-FINDINGS-BUT-NOT-ITS-ROUNDS`**
  (filed first under a name carrying the count, renamed in round 8).
  Sibling of `STAGE-REVIEW-HAS-NO-RETRY-RECORD`, which records that a self-review satisfies a stage
  identically to an independent one and that "a note is not a queue". The same blindness runs the
  other way. This stage took six rounds; every round found blockers, including rounds 3 through 6,
  which found them in text written to fix the previous round's blockers. `validate_review` checks
  three headings and unresolved blockers, so a note that was clean on the first pass and this one
  are indistinguishable to the driver, and no later stage is told which it got. That matters here
  because the things a single pass would have shipped are on the record above: a campaign figure
  wrong by 2x to 6x, a storage mechanism that breaks the offline gate, a frozen threshold classed
  reversible, a price band serving 47.1% of real 3-bet pots, and a closeout that cannot execute.
  What would fit the existing machinery is the same shape that entry proposes - the review queue
  already derives from six places, and a round count is derivable from the note itself.

### Round 5 additions

- `ONE-NON-ALLIN-PRICE-PER-ROUND-MAKES-SIZING-A-CARICATURE` - **this is the id that already owns the
  3-bet price defect**, and the round-5 non-blocker above is the case for folding the new
  measurement into it rather than carrying the same defect under two ids with two diagnoses. The
  entry names the cause (`raise_mults: [3.0]`), covers the 4-bet with it, and states the fix. What
  the measurement adds is the multiplier the corpus actually plays, a median 4.00x of the hand's own
  open against the chart's 3.0x, and a correction to the entry's own "10 to 11bb" estimate.

- `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` - sixth occurrence, and this one is
  in a brand-new entry rather than in the decision list: the SPR-at-12bb figure reads "about 4.0"
  where its own pot structure gives 3.52. Every input is on the page. The entry is also where item
  7's divisor-less "same range" clause still sits unfixed, which is the other half of the same id.

- `NOTHING-SWEEPS-DEFERRED-BACKLOG-ENTRIES-A-LATER-TASK-FALSIFIED` and the duplication above are two
  ends of the same missing mechanism: nothing sweeps a *stale* entry and nothing checks for a
  *duplicate* one before a new id is filed. The first half is filed; I am not proposing a second id
  for the second half, because a check that asks "does an existing entry already cover this" is the
  same read a human does when they sweep, and the entry already says that read "is not a mechanism".

- `DECISION-ANSWER-FIELDS-DIVERGE-FROM-THE-RULINGS-BELOW-THEM` - now on its fourth instance in this
  one stage, and the last two were in the ExecPlan rather than the decision list. The entry is
  scoped to a decision item's `Answer:` field; the pattern it describes is plainly wider than that,
  and the round-5 blocker is the same defect in a bullet's bold lead-in where no parser reads it and
  only a reader is misled. Worth widening the entry's own statement of scope when it is next
  touched, since that is where a future check would have to look.

### Round 4 additions

- `AN-AMENDMENT-TO-A-SKELETON-CONTRACT-IS-DELETED-BY-ITS-OWN-STAGE-1` - this is the answer to
  "does the fold-in rewrite itself need review before stage 4", and it is yes with a named failure
  mode rather than yes on principle. The entry records phase 16's own two-line amendment being
  deleted by the phase's own contract stage, with "the only durable record is the backlog id the
  amendment cites", and calls that "luck rather than design". A fold-in rewrite absorbing thirteen
  amendments into 289 lines is the same operation at thirteen times the scale, and the review that
  matters is not "is the new contract good" but "does every amendment that went in come out",
  checked against the decision list and the backlog ids rather than against the writer's memory.
  The entry's own proposed fix - "a requirement that stage 1 carries forward any amendment it finds
  before replacing the section around it" - is the rule this rewrite should be run under.

- `PHASE-14-CONTRACT-IS-AT-THE-SIZE-CAP` - now cited in the ExecPlan's Bootstrap, which is the right
  place for it. Nothing further to add beyond the round-3 note; the proposed phase-16 sibling is
  moot if the rewrite happens, and should be filed only if it slips.

- `NOTHING-SWEEPS-DEFERRED-BACKLOG-ENTRIES-A-LATER-TASK-FALSIFIED` - **discharged for this stage.**
  I re-checked both entries and the sweep was done properly, including collapsing the two same-day
  re-pointings so a reader is not handed a withdrawn rule as current. The entry stands on its
  general claim, and this stage is now evidence on both sides of it: the defect recurred twice
  inside one stage and was caught both times by a human reading, which is the entry's own point.

- `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` - fifth occurrence, and this one is
  the entry's own closing precision rather than its headline: item 7 states a limit with no divisor
  anywhere near it, which the entry distinguishes as "not a reconciliation failure but an
  unfalsifiable claim, and it needs a different fix from rendering a figure off its inputs".

- `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST` and
  `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL` - between them they carry the residual sample gap. The
  suit axis is ruled, the rank axis is instructed but not bounded, and the count does not close:
  three boards against five never-reached structures.

## What I did not verify

Named so the stage does not read this note as broader than it is. I did not verify anything about
whether the resulting flop strategy is good poker beyond the sizing arithmetic above; I have no
oracle for the ruled menu and neither does the repo. I did not check the 5.18% / 39.76% board-share
conversions, the orbit-size measurements, the 1,286,792 hero-combo-class figure, the range-floor
mass figures, the `tree.rs` readings on `add_allin` and `allin_threshold`, or the snap-state counts;
all are outside this diff and were verified by the stage-1 and stage-2 reviews. I did not run the
gate, `pytest`, or any mutation tooling, and I did not read `tests/**`. I did not check whether the
1% commit bound is reachable by a real cap-bound cell on any texture other than by extrapolating the
one rainbow curve in the record. I did not edit the decision list, `backlog.yml`, the contract or the
ExecPlan.

### Round 2

I re-derived every figure decision 4 now states and every figure I introduced, and I measured
`data/artifacts` on disk again (5,197,325 bytes used, 15,774,195 free) and the committed preflop key
lengths (249 keys, 14 to 78 characters, median 45). I did **not** verify anything about object
storage as a service: no bucket exists, no provider is named, no credentials or retention policy are
recorded, and nothing in the tree implements a fetch script, so item 2 of decision 6 is a direction
rather than a mechanism and I judged only the record. I did not price the rented GPU box and did not
look up any hourly rate, because inventing one is the defect I am reporting. I did not verify the
GTOpen tree-builder readings behind decision 11's snap arithmetic, which stage 2 covered. I did not
verify the `A-CONTRACT-CAN-NAME-A-FROZEN-CHOICE-NO-DECISION-ITEM-CARRIES`,
`A-SIZE-BUDGET-EXCLUDES-THE-PROVENANCE-THE-CONTRACT-MANDATES` or `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`
entries beyond reading them. I ran no gate command, no `pytest`, no mutation tooling, and no `git
checkout`, `stash` or `restore`, and I edited no file but this one in either round.

### Round 3

I re-derived the three-street geometric size at every open in 2.0 to 3.0 and the item's own 77.5 /
97.5 / 127.5bb window, and I read the committed preflop artifacts to count declared raise sizes (249
keys, `raise@2.5` and `raise@7.5` only) rather than assuming the chart has one open size. I checked
every figure the coordinator transcribed from my round-2 measurement against my own working. I did
**not** re-verify the round-1 or round-2 findings already marked resolved. I did not verify anything
about object storage as a service, which still has no provider, bucket, credentials or fetch script
in the tree. I did not price the rented machine and looked up no rate. I did not read `tests/**` and
did not open the contract for editing - I measured its length and read the criteria I cite, nothing
more. I ran no gate command, no `pytest`, no mutation tooling, and no `git checkout`, `stash` or
`restore`, in any of the three rounds, and this file is the only one I edited.

### Round 4

I re-scanned every JSON file under `data/artifacts/preflop` for `@` prices rather than only the spot
keys, and computed the 3-bet band's pot, effective stack, SPR and three-street geometric size at
6.0, 7.0, 7.5 and 9.0 using the pot structure the record's own 16.0 and 15.0 figures imply. I read
`phase_status.yml` and grepped `scripts/run_verify.py` for the two command IDs to establish the
gate's state **by reading, not by running it**. I did not re-verify anything already marked resolved
in rounds 1 to 3. I did not verify the fold-in rewrite, which does not exist yet, and I have not
judged what it should contain beyond the ordering and the review requirement. I still have no
independent basis for whether the ruled menu, the ruled floor or the ruled sample produce good
poker; nothing in this repo does. I ran no gate command, no `pytest`, no mutation tooling, and no
`git checkout`, `stash` or `restore`, in any of the four rounds, and
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-03-human-gate.md` is the only file I
have written to.

### Round 5

I wrote my own PHH parser from the raw `source_text` of all 499 hands rather than reading the
coordinator's, and reproduced every published figure plus the deciles, the band-recentring sweep and
the 4-bet coverage. I verified the blind structure, the ante vector, the variant, the stack depth,
the straddle count, the jam count, the limped-pot count and the exclusion list, all named above. I
did **not** verify the corpus against its upstream source, so this is a check of the parse and not
of the data; and 499 Pluribus hands with 87 3-bets is one bot-heavy dataset, so the medians are the
corpus's and not the population's. I did not re-verify anything marked resolved in rounds 1 to 4. I
did not read the fold-in rewrite, which does not exist yet. I ran no gate command, no `pytest`, no
mutation tooling, and no `git checkout`, `stash` or `restore`, in any of the five rounds, and
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-03-human-gate.md` is the only file I
have written to.

### Round 6

I brute-forced all 22,100 three-card boards for the rank-by-suit cross-tab behind the sample
finding, and re-checked the paired, trips, ace-containing and texture shares against the figures
this file already carries: rainbow 8,788 / 39.76%, two-tone 12,168 / 55.06%, monotone 1,144 / 5.18%,
all three matching the record. I re-read both 3-bet backlog entries in full and the ExecPlan
bootstrap. I did **not** re-verify anything marked resolved in rounds 1 to 5, I did not re-run the
corpus parse, and I did not read the fold-in rewrite, which still does not exist. I have never had
any basis for judging whether the ruled menu, floor, sample or bands produce good poker, and the
held-back alignment item above says so as plainly as I can. I ran no gate command, no `pytest`, no
mutation tooling, and no `git checkout`, `stash` or `restore`, in any of the six rounds, and
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-03-human-gate.md` is the only file I
have written to.

### Round 7

I re-read decision 6's item 4 in full, decision 3's new annotation, both 3-bet backlog entries, and
the three newly filed entries, and I re-derived nothing because nothing new was measured this round -
the item 4 figures are the ones I brute-forced in round 6 and they are transcribed correctly. I have
not read the independent poker review that is now running against the post-stage-2 rulings, and this
note does not stand in for it: everything I have signed off is arithmetic, internal consistency and
attribution, and the question of whether these rulings are good poker is the one thing six rounds of
my reviewing could not touch. I ran no gate command, no `pytest`, no mutation tooling, and no `git
checkout`, `stash` or `restore`, in any of the seven rounds, and
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-03-human-gate.md` is the only file I
have written to.

### Round 8

I read decision 6's item 4 whole rather than as a diff, checked its paragraph boundaries,
continuation indent and cross-item consistency, and re-checked every figure in it against the
brute force I ran in round 6. I verified the two backlog field changes and the rename. I re-derived
nothing new. I have still not read the independent poker review running against the post-stage-2
rulings, and nothing in this note covers the question it exists to answer. I ran no gate command,
no `pytest`, no mutation tooling, and no `git checkout`, `stash` or `restore`, in any of the eight
rounds, and `reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-03-human-gate.md` is the
only file I have written to.
