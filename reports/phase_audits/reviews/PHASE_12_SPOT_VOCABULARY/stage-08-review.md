# Phase 12 stage 8 review - the phase

Read-only pass over `git diff phase-11-complete..24daf06`, the committed
`reports/active/latest_spot_vocabulary_report.txt`, and
`docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`.
Two lenses, as the driver asks: one mechanical, one poker-domain.
No gate runs inside the review and nothing outside this note and `backlog.yml` was touched.

Coordinator-written, both lenses, as the phase's no-delegation exception records: subagents are
unavailable in this operator's sessions, so `AGENTS.md` step 10's self-review fallback applies.

The poker lens is the one that found things, which is the point of keeping it separate.
The mechanical findings are about how the report reads, not about whether the code does what the
contract says - that question was answered at stages 6 and 7.

## Blocker

None.

## Non-blocker

- [resolved] **The substitution census cannot be reconciled by the reader it was written for.**
  Fixed on 2026-08-21 at Taylor's instruction, rather than shipped as a stated limitation.
  Each table now names the population it counts, the 56 decisions carrying both a moved open
  and a moved later raise are printed, and the distance split carries its total, so the two
  figures reconcile on the page.
  `_validate_census` also now fails the gate when the decision splits do not reconcile by
  inclusion-exclusion, or when the distance or direction split disagrees with the
  substituted-raise total, so this class of gap cannot be published again.
  The heading says 969 decisions were answered at a price they were not asked at.
  Both tables under it sum to 1,025: the open-against-later split is 959 + 66, and the distance
  histogram is 554 + 412 + 22 + 34 + 3.
  Neither is wrong. 969 counts *decisions* and 1,025 counts *substitutions*, so 56 decisions
  carried two - a moved open and a moved raise behind it - and nothing in the report says a
  decision can carry more than one.
  A non-coding reviewer adding a column and getting 1,025 under a heading that says 969 has no
  way to tell a labelling gap from an arithmetic error, and this is the report criterion that
  asks for exactly that reader.
  Fix is one word per table caption plus a line stating the 56.

- [resolved] **`asked 2.5 → answered 3.5` reads as a bug and is not one.**
  Fixed on 2026-08-21 by the sentence option rather than the position column, because parsing
  the opener out of every spot key to reshape a table risks a bug in the report the phase is
  measured by, and the sentence closes the misreading exactly.
  The table now states that it aggregates openers whose solved prices differ, that the small
  blind's solved open is 3.5 and every other position's is 2.5, and that a row reading
  `2.5 -> 3.5` is therefore a small-blind open answered from the small-blind cell rather than
  a solved price that was moved.
  The opening-price table aggregates every position into one column pair, so the small blind's
  solved open of 3.5 appears alongside everyone else's 2.5.
  That is why one asked price maps to two answered cells (`3 → 2.5` twice, `3 → 3.5`
  thirty-four times) and why a price the tree genuinely holds appears in a table of prices it
  does not.
  Per-location candidates are the correct design and the module says why.
  The table needs the position column that makes it legible, or a sentence saying the column is
  aggregated across openers with different solved prices.

- **The report is honest where it would have been easy not to be.**
  Worth recording because it is the failure mode this stage usually catches: the roadmap's
  1,691 and 848 do not reproduce, the report says so, says no variation tried reproduced them,
  and files the correction rather than quietly publishing new numbers over the old ones.
  The same is true of the self-play figures moving for a re-seeding reason with no coverage
  content, which is stated in the report before a reader could mistake it for a result.

## Poker-domain findings

- [resolved] **The price substitution is one-directional, and the report's distance histogram hides that.**
  Fixed on 2026-08-21, in the same pass as the two report findings above, because the fix this
  note named was a column in the census and the census was already being opened.
  The report now carries the direction split: of 1,025 substituted raises, 1,010 were answered
  above the price asked and 15 below, with the poker reason stated in the report rather than
  only here.
  Of the 959 opener substitutions, 949 move the price *up* and 10 move it down.
  Hero is therefore answered, in 98.9% of substituted opens, with the strategy solved for a
  larger open than the one actually faced: 2 → 2.5 in 233 decisions, 2.25 → 2.5 in 541.
  The poker content of that is not symmetric noise.
  A smaller open gives the defender a better price and a lower risk-reward on a three-bet, so
  the correct response to a 2bb open is a wider continue than the correct response to a 2.5bb
  open, and the chart hands back the tighter one every time.
  The distance histogram reports how far, never which way, so the report as written says the
  abstraction is small without saying it is biased.
  Non-blocker because ruling 8 and the 2026-08-20 extension both priced this deliberately, and
  because the fix is a column in a census rather than anything in the lookup.

- **The thin tail is a property of this corpus, not of the abstraction.**
  966 of 1,025 substitutions land within 0.5bb and three exceed 3bb, which is a genuinely cheap
  measured cost and is fair evidence that the absent distance bound costs little *here*.
  It should not be read further than that.
  This sample is Pluribus and a human corpus whose sizes sit near a solve; the games this bot is
  eventually pointed at open to 3bb, 4bb and 5bb routinely, and the same census run against that
  data would move most of its weight into the two rows that currently hold 34 and 3.
  The census is the right instrument and it has only been run against the friendly sample.

- **The key admits raise sizes no legal preflop action produces.**
  `_validate_sizes` requires a raise to exceed the one it faces and to fit `stack_depth_bb`, and
  nothing checks the minimum raise: a three-bet to 2.6 over a 2.5 open has a key, though the
  smallest legal three-bet there is 4.
  I do not think this should change yet, and the reason is poker rather than effort.
  An all-in for less than a full raise *is* legal, so a minimum-raise rule in the key would
  reject real spots, and the key cannot tell an under-raise from a short all-in because it holds
  one table-wide depth and no per-seat stacks.
  The same limit makes payability weaker than it looks: a five-bet to 100 is admitted at 100bb
  because the deepest seat could pay it, not because the seat facing it can.
  Both wait on `ASYMMETRIC-EFFECTIVE-STACKS`, which is phase 13, and the module docstring's
  "legal preflop order" is a stronger claim than the check behind it.

- **Nearest is measured in big blinds, and the quantity that decides hero's range is a ratio.**
  Latent today: every location in the committed artifact holds exactly one solved price, so the
  normaliser never chooses between candidates and the metric is unexercised.
  It goes live the moment a second price is committed at one location, which is what phase 14
  does.
  Concretely: with three-bets solved at 8 and 11 over a 2.5 open, an observed three-bet to 12
  over an observed 4bb open is a 3.0x, and absolute-bb nearest answers it from 11, a 4.4x, when
  8 at 3.2x is the closer price in the only unit hero's continuing range responds to.
  Filed rather than fixed, because changing the metric now would change the committed keys this
  phase exists to freeze.

- **Re-keying re-randomises every mixed cell, so no self-play number survives a vocabulary
  change.**
  `PreflopChartStrategy._seed` hashes the spot key, so the 128 → 126 refused and 472 → 474
  measured hands in the profile comparison moved for no poker reason at all.
  The report attributes it correctly and the phase is not wrong to ship it.
  The cost is that phase 14 re-keys again when it derives a chart, and every self-play figure
  will move again for the same non-reason, which makes self-play useless as a regression signal
  across exactly the phases most likely to need one.
  Filed as an alignment item.

## Alignment

Three items filed in `backlog.yml` rather than left here, per the loop's rule that an alignment
finding is drift the stage cannot fix:

- `NORMALISER-MEASURES-DISTANCE-IN-BIG-BLINDS` (`contract-update`, phase 14 is when it bites).
- `RE-KEYING-RE-SEEDS-EVERY-MIXED-CELL` (`contract-update`, same).
- `TWO-LANES-CAN-FILE-ONE-DEFECT-TWICE` (`contract-update`). Evidence is this review: the main
  lane filed the unretired-lane-pointer defect under its own id at `14fa982` on 2026-08-20,
  hours after this lane had already filed it as `LOOP-LANE-POINTERS-NEVER-RETIRE` at `d0c7c43`.
  Two worktrees both hold `backlog.yml` in standing scope, neither sees the other's filings
  until the merge, and no check compares them.
  The main-lane id is deliberately not written out here: it does not resolve against this
  lane's `backlog.yml`, and the citation check would be right to reject it.
