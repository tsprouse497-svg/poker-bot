# Stage 08 Review (Phase 10)

Two read-only passes, kept apart on purpose. The mechanical pass asks whether the code does
what it claims. The domain pass ignores the contract entirely and asks whether the poker is
poker, which is the only question a green gate cannot answer.

Reviewer: coordinator, both passes. Subagent delegation is switched off in this operator's
sessions - the standing instruction is not to call the Agent tool unless it is requested - so
`AGENTS.md` step 6 cannot be satisfied and step 10's self-review fallback applies. Two
independent reviewers were offered to Taylor rather than dropped silently.

Evidence read: the committed export, its source card,
`reports/active/latest_solver_export_report.txt`, `reports/active/latest_verify.txt`, the
decision record, and the saved solve loaded in GTOpen's own interface at 127.0.0.1:3737.

## Blocker

- [resolved] **The report's four-bet spot was the wrong node and carried a label that named
  the wrong seats.** It was found by walking LJ's open, then the next 3-bet, then the next
  4-bet, and labelled "HJ vs LJ 4-bet". After HJ three-bets the action passes to CO, not back
  to LJ, so that walk landed on `[1, 2, 2]` - the button facing a four-bet from the cutoff,
  in a line the solution folds 99.09 percent of the time - and printed it under a heading
  claiming the hijack was facing the lowjack. This is worse than showing no four-bet: decision
  6c's whole method is a person navigating GTOpen to the named spot and comparing grids, and
  they would have navigated somewhere else and called it a mismatch. Fixed: the walk folds the
  seats between the three-bettor and the opener, so it lands on `[1, 2, 0, 0, 0, 0, 2]`, HJ
  facing LJ's four-bet, and the label is built from the seats the walk actually reached rather
  than asserted. The node it now shows is the one decision 2 recorded from the probe - fold
  34.61, call 53.56, jam 11.83 - and the committed export reproduces it at 34.60, 53.56,
  11.83. It is also the better spot for a human: 31 distinct arriving-range values instead of
  a uniform one, so the reach handling is visible in the grid.

## Non-blocker

### Mechanical pass

- **The grid comparison decision 6c specifies has been performed, and it matched.** The save
  `six-max-100bb-rakefree.gtop` was loaded through GTOpen's own loader; the header restored
  six seats, 100bb, `calibrated`, and the status line read "83,123 nodes · 112 MB · loaded
  six-max-100bb-rakefree at iter 300", which is the tree the export was walked from. Three
  nodes were read cell by cell against the committed report:
  - **RFI LJ.** GTOpen: Fold 81%, Raise 2.5 19%. Report: 80.92 / 19.08 / 0.00. Cells: 44 reads
    Fold 27.2 / Raise 72.8 in GTOpen against 72.81 in the report; A6s reads Raise 8.9 against
    9.
  - **HJ facing LJ's open** (`[1]`). GTOpen: 93 / 0 / 6 / 0. Export: 93.37 / 0.14 / 6.49 /
    0.00.
  - **BB vs LJ** (`[1, 0, 0, 0, 0]`). GTOpen: 73 / 21 / 6 / 0. Report: 72.72 / 21.01 / 6.26 /
    0.01. A5s reads Fold 0.0 / Call 0.5 / 3-bet 99.5 against the report's 1 and 99, and the
    irregular signature in that row matches: Q7s folds while Q6s and Q5s call, in both.
  That last one is the check with teeth. A transposed index or a mis-sorted grid reproduces
  monotone patterns by luck and never reproduces a hole at Q7s between two calling neighbours.
  What it does **not** establish is that GTOpen's poker is right, because both sides come from
  one solved arena. That is the verdict below, and it is Taylor's.

- **The form disagrees with the load, exactly as decision 6c warned.** After loading, the
  scenario panel reads "tree ≈ 145,590 nodes · 197 MB" while the solve panel reads "83,123
  nodes · 112 MB · loaded". The form has no control for `allin_threshold` and shows its own
  estimate at the server default of 0.85; the loaded tree is the ruled 0.67. Pressing Build or
  Re-solve would silently replace one with the other. The report says so in its own header,
  which is where a reviewer will actually read it.

- **The tree's shape is consistent with a six-handed no-limp game and nothing was quietly
  dropped.** Depth histogram runs 1, 3, 9, 27, 80, ... to 16 nodes at depth 20, at most four
  actions anywhere, 38,828 action nodes total against the 38,828 `/api/preflop/spot` reports.
  The branching of 3 at the first three levels is right: a fold in six-handed play passes the
  action rather than ending the hand, so all three of the lowjack's actions lead to action
  nodes. The first shortfall appears at depth 4 (80 rather than 81), which is where a line
  first terminates.

- **The report is 39,808 bytes against a 300 KB cap, and the export 4.09 MB against 20 MB.**
  Both have room, and neither number was chosen after seeing what landed.

### Domain pass: is this poker

- **The direction is right almost everywhere, and the one exception points at the model.**
  Against the raked GTO Wizard reference, rake-free opens wider at LJ (19.08 against 17.49)
  and the big blind defends wider against LJ, HJ, CO and SB. The button opens **tighter**:
  40.26 against 40.56. Removing rake should not make the widest-opening non-blind position
  tighter, so this is the equity-realization model rather than rake. GTOpen prices flops at a
  `pot_share` terminal scaled by a per-seat realization weight instead of playing them, and
  the button's edge is almost entirely postflop positional. A scalar weight is the one part of
  that edge the model can express, and it evidently under-prices it.

- **The big blind under-defends, and it is the same cause seen from the other side.** Closing
  the action against a 2.5x open, the big blind is laying 1.5 to win 4.5 and needs 25 percent
  raw equity. It defends 27.28 percent against a lowjack range that is itself only 19 percent
  - 570 of 1,326 combos ever continue - and 49.02 percent against a small blind opening 54
  percent. A full postflop solve at these prices defends materially wider in both spots. The
  big blind's disadvantage is entirely postflop and out of position, which is precisely what
  the realization weight is standing in for, so a model that over-charges it produces a
  tight-defending big blind that is nevertheless internally consistent and passes both gated
  orderings. This is the single most important thing for whoever derives a chart from this
  export to know, and the source card's `model` field names the mechanism without naming this
  consequence.

- **One cell is convergence noise rather than strategy.** The lowjack raises 44 at 72.81
  percent while raising 33 at 99.88 and 22 at 99.92 - a pocket pair opening less often than
  both pairs beneath it. GTOpen's own interface shows the same 27.2 / 72.8 split, so it is the
  solve rather than the extraction. The summed best-response gap crossed the ruled 0.01 bb at
  iteration 300 and marginal hands converge last. Every other pair in every other opening spot
  sits above 99.8. Filed as `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR`.

- **What the two gated checks are worth, stated plainly.** They catch a broken pipeline and
  nothing else. A frozen test halves every frequency and passes them both, by design. The
  reach weighting that decision 7 calls the difference between right and self-consistently
  wrong moves none of the eleven aggregates, because all eleven are read at nodes where the
  actor has not yet acted. So the assurance that this export is a faithful copy of what GTOpen
  solved rests on the frequency test against the captured payload, the zero-mismatch
  re-resolution of all 38,828 nodes, the byte-identical second run, and the grid comparison
  above - not on the gate's two orderings.

- **Nothing downstream changed, which is the right answer.** The bot still plays the committed
  36-spot chart. No chart is derived, no spot key moves, and the 22 refused spots in
  `latest_refusal_inventory.txt` are still refused. This phase produced data and a way to
  check it, and stopped there.

## Alignment

- `SOLVE-TARGET-LEAVES-A-NONMONOTONE-PAIR` - the ruled 0.01 bb target leaves one pocket pair
  non-monotone; it belongs to whoever derives a chart, not here.
- `REALIZATION-MODEL-UNDERPRICES-POSITION` - the button opens tighter than a raked reference
  and the big blind defends tight in absolute terms, both traceable to a preflop-only model
  pricing postflop by a scalar weight. Phase 14 is where it would be paid for.
- `DEFENCE-RELATION-NARROWER-THAN-THE-CONTRACT` - the contract's "for every pair of positions"
  is broader than the frozen tests allow.
- `GATE-COMMAND-DESCRIPTION-NAMES-A-WITHDRAWN-CHECK` - the registry still advertises the
  withdrawn directional bound.
- `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` - an import-error red at stage 4 means no
  assertion ran and no linter read the file before it was frozen.
