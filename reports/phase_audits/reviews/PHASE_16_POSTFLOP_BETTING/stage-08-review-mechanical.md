# Phase 16 stage 8 review: the phase against its contract, mechanical

Read-only. I wrote none of this work and edited nothing but this file. No `run_verify.py`, no
`check_gate_bite.py`, no mutation tooling, no `git checkout` and no `git stash`. What I ran is
the phase's own `pytest` command and my own scratch arithmetic; scratch lived outside the repo.

Subject: the phase as a whole against `docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md`. I read
the stage 6 and stage 7 notes first and do not re-file what they filed. Every figure below I
computed in this tree, method stated beside it.

## Verdict by criterion family

| family | verdict |
| --- | --- |
| The key and the query must be able to express a flop spot | satisfied |
| What the committed solve owes | satisfied, except the machine the campaign ran on (blocker 3) |
| Selecting what gets committed | satisfied in letter; the byte figures and the line-count bound are blocker 1 and non-blocker 1 |
| What the strategy must do, and where it must refuse | satisfied; the two table causes are pooled where they are counted (blocker 2) |
| The pot-odds river call | satisfied |
| Evidence, reports, and gate | satisfied, except the byte and cause figures above |
| The backlog entries this phase settles | **not satisfied** (blocker 4) |
| Human vetting packet | not yet due; the packet is stage 9 and does not exist |

## What re-derived, and how

Everything in this block I recomputed here. All of it holds.

- **The class census.** Brute-forced `canonical_board` over all 22,100 three-card boards: 1,755
  classes; rainbow 455 classes over 8,788 boards, two-tone 1,014 over 12,168, monotone 286 over
  1,144. Mean orbits 19.314, 12.000, 4.000. Shares 39.76%, 55.06%, 5.18%. `455 x 24 = 10,920`,
  which overstates the rainbow board count by 24.26%. Every one matches the report.
- **The contract's named sample board.** `canonical_board(['Kc','7d','2h'])` returns `Kh7d2c`, which
  is the board committed. The contract names a dressing; the repo commits the representative.
- **The four committed cells.** For each, I enumerated every two-card combination the board leaves,
  weighted it by the seat's own committed range weight, and collapsed it with `canonical_hole_cards`.
  The derived class set equals the committed `hand_classes` exactly on all four (152, 342, 342, 230).
  Every range-weighted and class-mean frequency in the report re-derives to the printed digit:
  70.16/29.51/0.33, 0.12/80.86/19.03, 27.12/44.25/28.63, 84.61/11.83/3.56, and the four class-mean
  triples beside them. Weighted-combination totals 294.86 and 445.08 in the opponent block both
  reproduce.
- **The digests.** All four committed `strategy_digest` values re-derive from the committed cells
  through `postflop_harvest.strategy_digest`, and the fifth from the listed-not-held cell document
  in object storage. All five `object_digest` values re-derive from `shasum -a 256` over the five
  `.gz` objects, including the deep run's. Nothing in the gate does any of this.
- **`determinism.json`.** 5 cells, iterations 280 to 340, identical in both runs, per-combo counts
  447/342/342/350/331 which are exactly each seat's full-weight combination count on that board.
- **`deep_convergence_check.json`.** Recomputed from its own `per_class` block: 152 classes, 0
  unmoved, 79 past 0.05, 16 changing preferred action, mean 0.0816, worst 0.4670; pure 19 / mean
  0.0071, lightly-mixed 32 / 0.0495, mixed 101 / 0.1058; the three reach-weighted aggregate
  frequencies 0.0012, 0.8086, 0.1903 and their deep counterparts. One digit is wrong, below.
- **The corpus.** 499 hands counted off `corpus_hands.jsonl`; 259 of them deal a three-card board,
  counted independently by parsing the `d db` actions. Loss causes 20 / 14 / 175 / 50 and
  `answerable 0` reproduce through `measure_corpus`. Opens 409, median 2.25bb, 405 inside a declared
  band; three-bets 87, median 9.25bb, 62 inside one. Chart prices are 2.5, 7.5 and 13.5.
- **Bytes.** `data/artifacts` totals 4,938,950 bytes; cap less that is 16,032,570, which is what
  both the index and the regenerated solver export source card carry. 3,198 class weights in 19,711
  bytes is 6.164 bytes a weight.
- **The gate.** `reports/active/verify_results.json` records 50 commands, all passed, with
  `check_gate_bite` among them. I re-ran the phase's own `pytest_postflop_betting` file set here:
  238 passed. The committed report is byte-identical to a regeneration on this machine, since
  `git status` shows it unmodified after the recorded gate run.
- **Offline.** Nothing under `tests/` or `src/` reads the object store; only the report generator
  does, and `object_for` answers `None` when the manifest or the file is absent, after which the
  generator prints a named paragraph in place of the block. No `requests`, `urllib` or socket use
  in the solve driver or its tests. The non-goal holds: the gate needs no GTOpen, no Rust
  toolchain, no network and no fetched object.

## Blocker

Status added 2026-09-22, after `de7d1b9` and `fc9a164` answered four of the five. The findings
below stand as first written; each carries its verdict at the head of the bullet.

- **[resolved]** at `de7d1b9`, verified: three figures now carry three labels, both per-spot rates
  are printed, and the 44,054 bytes between the directory and the index-and-sample are named as the
  campaign's own records.

  **The byte block labels the whole postflop directory as the index and the sample, and the
  per-spot cost inherits it.** `reports/active/latest_postflop_betting_report.txt` prints "of which
  the postflop index and sample: 100,845" and, lower down, "reconciled against the postflop index
  and sample bytes above". Measured here by summing file sizes: `index.json` is 2,866 bytes and
  `sample/` is 53,925, a total of **56,791**. The printed 100,845 is `postflop_bytes()`
  (`scripts/generate_postflop_betting_report.py:1444`), which is `POSTFLOP_DIR.rglob("*")`, so it
  also carries `deep_convergence_check.json` 32,920, `determinism.json` 5,334, `solve_config.json`
  3,623 and `objects.json` 2,177 - **44,054 bytes, 43.7% of the figure, that are neither index nor
  sample**. "per spot: 25,211.2 bytes" is that total over 4 spots; the index and sample alone give
  **14,197.75**, so the printed per-spot cost is **overstated by 77.6%**.

  Why this is not cosmetic. The contract makes the line count an output of two bounds - "as many as
  the campaign cost and the index each afford, whichever is smaller, and the report names which
  bound it" - and the per-spot byte cost is precisely the number that decides whether the index
  bound binds. The deep convergence record is a one-off measurement of one cell and does not scale
  with spots at all, so it is the same class of error the phase built a checker against on the
  other side of the page: `check_rate_excludes_non_weight_bytes` exists so that a per-weight rate
  cannot charge non-weight bytes, and the per-weight figure is correct because
  `weight_bytes_and_count` cuts the weight block out of the file. Nothing does the equivalent for
  the per-spot figure. `check_bytes_reconcile` compares the index's declared number against the
  same whole-directory sum, so it agrees with the mislabel rather than catching it, and the frozen
  tests that would hold this are word checks: `test_the_per_spot_cost_is_printed` asserts the
  string "per spot", and `test_the_budget_says_it_covers_the_index_and_the_sample_not_the_object_storage`
  asserts the words "index", "sample" and "object storage" appear somewhere. Both pass on the
  present text and would pass on any number at all. The fix is to print the index and sample sum
  beside the tree sum and divide the former by the spot count, or to relabel both lines; note that
  `scripts/solve_postflop_sample.py:1754` already labels the same number honestly as "in
  data/artifacts/postflop", so only the report is wrong.

- **[resolved]** at `de7d1b9`, verified: the coverage split prints the two causes as separate rows
  at 50 and 0, with a paragraph on why they cost different things to close.

  **The one place the report counts the two table causes, it pools them, and the report says it
  never does.** The contract: "At the table a miss carries exactly two causes and the report never
  pools them: no cell for this board or line ... and in the index but not fetched on this machine."
  The report's coverage split prints "lost to no cell for this board, or in the index and not
  fetched: 50 (19.31%)" - one row, both causes - and its refusal section then asserts "At a table a
  miss carries exactly two causes, and this report never pools them" and lists the two causes with
  **no counts beside either**. So the causes are named without numbers in one block and given a
  number only pooled in the other.

  The split is available and I measured it: re-running `measure_corpus` with the index-listed,
  unfetched `Ac8c3c` class added to the fetched set leaves all four cause counts unchanged, so the
  true division of the 50 is **50 to "no cell for this board" and 0 to "in the index and not
  fetched"** - no corpus flop lands on that class. Printing one row of 50 rather than two rows of
  50 and 0 is a labelling defect rather than a hidden mixture, which is why the correction is one
  line at `CAUSE_BOARD` (`:1238`) and why leaving it is a report that contradicts itself in prose.
  Nothing catches it: the generator's own module docstring lists "a coverage share that pools two
  loss causes" as one of the four failures it exists to refuse, but
  `check_coverage_splits_by_cause` (`:203`) only checks the shares sum to 1, and
  `test_the_two_table_causes_are_printed_and_never_pooled` asserts that the phrases "no cell for
  this board or line" and "not fetched" appear.

- **[resolved]** by decision 24 at `fc9a164`: the scope sentence binds the campaign and not this
  sample, the wording gap is filed as
  `A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE`, and the packet states that
  every timing the phase publishes is a laptop figure.

  **The committed campaign ran on the laptop, the contract says it moves to a rented cloud box, and
  no committed document says which machine any published cost figure came from.** The contract's
  Scope: "Solving moves to a rented NVIDIA cloud box whose specification is deliberately unruled,
  so every timing and arena figure here is re-derived there before a run is planned." The only
  machine named anywhere in `data/artifacts/postflop/` is
  `deep_convergence_check.json`'s "Apple M4, 10 cores, 34.4 GB RAM, CPU engine", and decision 20
  records the arena measurements as taken "on the Apple M4 the rest of the phase measured on" while
  still describing 0.35 as "the number meant to travel to the rented box the contract names". So
  the campaign the repo commits was solved on the machine the contract said it would move off, and
  the cost block publishes 759.7s, 853.0s and 248.2s a class with no machine attached at all -
  while the source it draws from, `reports/active/latest_postflop_solve_cost.txt:6`, does name the
  machine and even warns that a battery-powered row reads as a slower box. A later phase funding a
  campaign from those figures has no way to know what they were measured on. I found no backlog
  entry that owns this; the nearest,
  `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`, is about thread count rather than
  about the machine the phase was ruled onto. Two fixes, both small: file it, and carry the machine
  line into the cost block beside the numbers it qualifies.

- **Open.** Ruled entry by entry in `stage-08-review.md`: four close, three do not, and the three
  are `POSTFLOP-UNBEATABLE-EARLIER-STREETS`, `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` and
  `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`. The evidence per entry is there rather than here.

  **Every backlog entry the contract says this phase closes is still open, and nothing looks.** The
  contract's closing section names five entries as Closed - `V2-POSTFLOP-STRATEGY`,
  `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`, `POSTFLOP-UNBEATABLE-EARLIER-STREETS`,
  `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`, `ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS` - and
  a sixth, `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`, conditionally. Measured against `main`: this lane
  adds **90 entries to `backlog.yml`, all `deferred`, and changes the status of exactly zero**. All
  56 entries carrying phase 16 are `deferred`, the six above among them. No script in `scripts/`
  reads a contract's Closed list, so the gate is green with the criterion wholly unmet.

  I record this as a blocker rather than an alignment item because it is fixable inside the phase
  and is due before the gate closes at stages 9 and 10, not because the sweep should have happened
  at stage 8. What makes it worth holding the stage for is that nothing will raise it later: this
  is the shape `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` predicts, and that entry describes the
  gate's blindness rather than prompting the sweep.

## Non-blocker

- `line_count_bound_by` is the literal string `"campaign-cost"` at
  `scripts/solve_postflop_sample.py:788`. Nothing anywhere compares what the campaign cost afforded
  against what the index afforded, so the contract's "whichever is smaller, and the report names
  which bound it" is satisfied by a constant that would read the same if the index had been the
  binding one. Related to but distinct from the byte blocker above, which is what would make the
  index bound computable.
- "covered preflop lines committed: 2" counts hero seats, not lines. The two entries are
  `t6/d100/BTN/BTN:raise@2.5,BB:call` and `t6/d100/BB/BTN:raise@2.5,BB:call`: one preflop action
  line seen from both chairs. The ranking table twelve lines further down counts the same thing as
  one line with 50 arrivals, so the report uses two units for one word on one page. **One** distinct
  preflop line is covered out of the twelve the corpus reaches.
- The deep block prints "median: 0.0530" where the measured median of the 152 per-class movements
  is **0.0535**. `deep_convergence_check.json` stores `median: 0.053` correctly rounded to three
  decimals and the report re-pads it to four, which invents a digit. The neighbouring figures are
  right: stored `mean: 0.08157` prints as 0.0816 and stored `max: 0.467` prints as 0.4670.
- **[resolved]** at `de7d1b9`: the table now prints "solved trees the committed spots come out of:
  3", says the accuracy is not one measurement a row, and names the shared tree on both rows that
  share it. Two of the four rows in the per-spot accuracy table are one measurement printed twice. The two
  `Kh7d2c` spots share an object, an `object_digest`, an exploitability of 0.283013340119407, an
  iteration count of 340 and a wall-clock pair of 1677.4s / 2523.9s, because exploitability is a
  property of the solved tree and those two spots are two nodes of one solve. The report introduces
  the table as "Each row is one committed hero decision node ... The accuracy is that cell's own
  achieved figure", which is false for those two rows, and the determinism table repeats the same
  wall clocks on two lines without saying why. Four committed spots rest on **three** solved trees
  held here.
- The board-miss code is live where the contract asked and vacuous only where this phase's own
  report looks. `reports/active/latest_refusal_inventory.txt` carries **26** rows under
  `no-cell-for-this-board` and **113** under `no-cell-for-this-preflop-line`, so the criterion
  "the board-miss code is live rather than vacuous" is met at the simulated table. The betting
  report labels all sixteen codes vacuous because `measure_behaviour` asks only
  `committed_spot_queries()`, which is stage 6's finding and is not re-filed here. What is worth
  adding is that no document connects the two: a reader of the betting report alone concludes the
  code has never fired anywhere.
- Decision 14's ruling reaches no criterion and no contract text. Matching a table bet to the menu
  by pot fraction, `MENU_FRACTION_TOLERANCE = 0.05` compared inclusively, is `frozen-into-data` and
  appears nowhere in the contract, whose only tolerance is the 20% preflop price band. It is held
  by two assertions in `tests/test_postflop_solve_driver.py:349` and `:366` and by nothing else.
- Decision 21's ruling is held by nothing at all. It says the continuation-bet frequencies must
  never travel without the block stating what the other seat did first, and that block exists in
  the report; no contract criterion requires it and no frozen test asserts it - a grep of
  `tests/test_postflop_betting_report.py` for the block's subject returns nothing. The gate stays
  green if a future regeneration drops it. The same is true of decision 15's deep-solve block,
  except that there the contract asserts the opposite of what was ruled, which is already owned by
  `A-CONTRACT-CLAUSE-ASSERTS-A-GAP-ITS-OWN-PHASE-THEN-CLOSED`.
- The audit packet named in the contract frontmatter,
  `reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md`, does not exist. That is correct for stage 8 -
  the packet is stage 9 - and is recorded only so the next reader does not take its absence for a
  miss. Of the packet's own obligations, the report already carries the four qualifications as
  qualifications and the seam decision 1 accepted; the recomputable-number requirement and the
  source-code-free spot-check path are still owed.

## Alignment

- `NOTHING-CHECKS-THAT-EVERY-RULING-REACHES-A-CRITERION`. I ran the check the entry says nothing
  runs. All 23 judgment calls declare a reversibility class, including the split items 16a, 16b,
  18a and 18b. Of the 23, twenty reach a contract criterion; decision 14 reaches none, decision 21
  reaches none, and decision 15 reaches a criterion that asserts the opposite of its ruling. The
  pattern is dates: everything ruled before the contract was frozen reaches it, and three of the
  ten ruled after it do not, because the contract sits at 299 of its 300-line cap and cannot take
  the lines.
- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE`. The gate's blindness that blocker 4 runs into. The
  entry is accurate as filed and describes the check that does not exist rather than prompting the
  sweep that is owed.
- `BACKLOG-SWEEP-MISSES-ENTRIES-FILED-UNDER-A-CATEGORY`. Measured on this lane: of the 90 entries
  added against `main`, 42 carry phase 16, **45 carry `contract-update`**, 2 carry `maintenance` and
  1 carries `v2`. A closing sweep scoped by phase id sees fewer than half of what this phase filed.
- `BACKLOG-PHASE-FIELD-MIXES-PHASE-NUMBERS-WITH-CATEGORIES`. Two of the 56 phase-16 entries store
  the phase as an integer rather than a string, `THE-UNPLAYABLE-SIZE-CANARY-CANNOT-BITE-ON-A-BET-IT-ONLY-BITES-ON-A-RAISE`
  and `DECISION-12-S-DO-NOT-SMOOTH-ARGUMENT-DESCRIBES-A-RANGE-THAT-WAS-SUPERSEDED`. Any consumer
  comparing against the string misses both.
- `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`. I re-derived all five strategy digests
  and all five object digests by hand in this review and every one holds; the point stands that the
  gate re-derives none of them, and four of the five objects live under one home directory.
- `REPORT-VALIDATORS-CAN-HOLD-GUARDS-THAT-CANNOT-FAIL`. `check_coverage_splits_by_cause` is another
  instance: it proves the shares sum to the population, which is arithmetic over the causes the
  loop chose, and cannot see that one of those causes is two causes wearing one label.
