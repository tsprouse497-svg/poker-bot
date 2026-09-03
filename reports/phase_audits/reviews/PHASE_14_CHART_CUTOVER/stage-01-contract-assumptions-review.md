# Stage 1 review: the assumptions in the rewritten contract

Read-only review of the working-tree contract (299 lines) against the export it describes.
Every number below was re-derived from `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz`
by a throwaway script, not read out of the decision record. Where the record and my walk
disagree, both figures are given.

## What reproduces

The census is right, to the last digit.

| claim | contract | re-derived |
|---|---|---|
| action nodes | 33,969 | 33,969 |
| at most two raises in | - | 607 (5 first-in, 57 facing an open, 545 facing a three-bet) |
| beyond that depth | 33,362 | 33,362 |
| exposure at or above ten percent | 348 | 348 |
| big-blind squeeze spots | 10 | 10 |
| committed | 249 (5 / 25 / 219) | 249 (5 / 25 / 219) |
| coverage | 98.5949% | 98.5949% (51.9237 + 38.5422 + 8.1290) |
| widest admitted / narrowest refused exposure | 9.8642 / 10.0234 | 9.8642 / 10.0234 |
| squeeze nodes, exposure spread | min 3.74, p25 5.79, median 93.40, max 99.74 | 3.74 / 5.79 / 93.39 / 99.74 |
| big-blind spots keeping the call / spots merging | 5 / 20 | 5 / 20 |
| cells moved by the merge | 165 (decision 45) | 165 |

Also checked and true:

- **249 nodes really are 249 keys.** No two committed nodes derive the same spot key.
- **Prices are exactly 2.5, 7.5, 22.5** on the committed set, one price per spot. Hero's own
  jam appears only at the four-bet-facing nodes the phase excludes, so the jam canary does
  have to run against the export rather than the chart.
- **The three vacuous labels are all correct.** No committed spot offers zero raises; no node
  anywhere offers a named raise and a jam together; the five first-in spots offer no call at
  all, so "hero never limps" cannot be violated.
- **Zero untouched-initialisation rows** among cells the bot can actually hold, on both the
  exact and the near-equal reading.
- 93.20 percent of cells are pure at 99 percent or more, 3.85 percent mix below 90 - decision
  49's corrected figures, confirmed.
- `RULED_CONFIG` equals the posted config field for field, all fourteen fields.
- All forty backlog ids the contract names exist in `backlog.yml`.
- Both counterfactual arms pass on all ten partitions (details in finding 5).

## Findings

### 1. Withdrawn: the defence level facing an open is not a defect

I first reported the non-blind seats' defence facing an open (4.32 to 14.98 percent) as an
unlisted defect. Taylor rejected it and he is right. Checked against his own viewer on the
`BTN` facing an `LJ` open node, the export reads fold 90, call 3, three-bet 7, over exactly
these 25 classes: AA AKs AQs AJs ATs A5s A4s AKo KK KQs KJs KTs AQo QQ QJs QTs JJ JTs TT 99
88 87s 77 76s 66. That is a normal button response to an early open. My "standard" bands were
uncited, which is the same fault this review flags in the contract, and the level is not
evidence of anything.

I then narrowed the claim to the pair ladder at `BTN` facing a **`CO`** open - `66` through
`TT` at 100, `55` at 56, `44` and `33` at 0, `22` at 100, all pure three-bets at full reach -
and Taylor rejected that too, on the ground that the four small pairs are near-indifferent
bluff candidates and which one the solve picks carries no EV. That is right, it is the same
ground decisions 41, 47 and 50 stand on, and I had no measurement behind the objection. The
claim is withdrawn in full; nothing in the composition of the committed ranges is reported
here as a defect.

Worth a question rather than a finding, running the opposite way: if picking `22` over `33`
is free choice among equivalent hands, then decision 47's "23 have no poker story" may be
over-calling as defects what is really the solver's arbitrary bluff selection. The
`PREFLOP_PRUNE=0` experiment decision 47 names is what would tell those two apart and has
still not been run. That is a question for the packet's wording, not a blocker.

**Ruled 2026-09-02 (decision 51): not a blocker, ship with what we have.** The value-gap walk was
offered and declined. The contract's inversion criterion now carries the ruling in one line.

The one thing worth carrying forward from the original claim is the citation problem, and it
cuts the other way from how I first put it. Against `expectations/six_max_nl25_100bb.json`
the committed big blind defends **wider** than the raked reference at four of five openers
(25.70 vs 22.63, 28.88 vs 26.20, 32.78 vs 31.48, 48.39 vs 42.88), narrower only against the
button. Decision 34's "15 to 20 points too tight" has no source in the repo, and rake at NL25
does not span that gap. That is an alignment item under
`REFERENCE-RANGES-HAVE-NO-CITED-SOURCE`, not a blocker.

### 2. Blocker: "the branches the bot can take" is worth 102 spots

The rule as written admits four readings. Re-derived counts:

| reading | committed |
|---|---|
| no restriction at all | 257 (5 / 33 / 219) |
| drop hero's call only where it would be a **cold** call, big blind exempt | **259 (5 / 35 / 219)** |
| same, big blind included | 259 (5 / 35 / 219) |
| drop hero's call at every hero node | 361 (5 / 35 / 321) |

Only the second reproduces the contract's 249 and its published margin. The fourth - the
reading a plain-English reader gets, since the bot cannot cold-call - commits 321
three-bet-facing spots instead of 219. The contract needs one clause saying the branch that
is removed is hero's cold call, not hero's call.

Related: the reachability half of decision 46 is worth exactly **two** spots (257 against
259). The contract says "threshold and reachability together, neither alone", which is true
but reads as though the clause were load-bearing. It buys two spots out of 249.

### 3. The exclusion code names the rule that was declined

`derivation:hero-closes-into-a-multiway-pot` describes "hero closes the action and hero's
call creates a multiway flop", which decision 48 measured at 68 nodes and explicitly did not
take. The bucket holds the ten big-blind squeeze spots. A later phase reading the bucket by
its name gets the wrong set. Rename to something that says what it holds, e.g.
`derivation:big-blind-squeeze-spot`.

### 4. Two sentences contradict each other

Line 95: "It does **not** refuse spots reached through a cold call." Line 80: the third
clause refuses a node when hero is the big blind, faces an open, "and a cold caller is
already in". Those ten spots are refused for having a cold call in front of them. Qualify
line 95 or drop it.

### 5. The rank arm passes the largest partition by one cell

Both arms pass everywhere, under my reconstruction of the definitions:

```
partition      n   suit arm (spots)   rank arm (cells, full grids only)
all          249      7 vs 167          64 vs 206     over 83 spots
seat LJ       32      7 vs  32           1 vs   9     over  1 spot   - unasserted
seat HJ       36      0 vs  15           3 vs  14     over  2 spots  - unasserted
seat CO       44      0 vs  18           6 vs  21     over  5 spots
seat BTN      47      0 vs  28           9 vs  33     over 12 spots
seat SB       52      0 vs  36          15 vs  54     over 25 spots
seat BB       38      0 vs  38          30 vs  75     over 38 spots
raises 0       5      0 vs   5          11 vs  61     over  5 spots
raises 1      25      0 vs  25          21 vs 112     over 25 spots
raises 2     219      7 vs 137          32 vs  33     over 53 spots
```

Two things follow. The five-spot rule is doing real work - the lojack and hijack partitions
score one and two spots and would otherwise be coin flips, exactly as the contract predicts.
And the three-bet-facing partition passes **32 against 33**: one cell of margin on the
partition that holds 219 of the 249 spots. Any change to the tolerance, to which grids count
as full, or to whether non-adjacent kickers are compared can turn that into a tie, and a tie
refuses. Worth knowing before the gate is frozen; it is not an argument for softening it.

### 6. Three figures in the decision record that do not reproduce

None of these is in the contract, so none of them blocks; all three are quoted in arguments
the packet will carry.

- Decision 46: "All 348 refused nodes together carry 0.89 percent of preflop decisions."
  They carry **0.0342 percent**. 0.89 percent is the mass of the four-bet-and-deeper family.
  The ruling gets stronger, not weaker - raising the threshold cost even less than claimed.
- Decision 49: "pure-call cells 1,179 (6.40 percent)". That is the count of cells at
  **99 percent or more** on call. Decision 45 defined a pure call as the hand's entire weight
  on call, which is **748 (4.06 percent)**. Two measures under one name; the denominator
  (18,431 cells with non-zero reach) is right in both.
- Decision 45: "165 cells ... 73 of them pure calls". The 165 reproduces exactly on the final
  set; the pure count is **40** on the entire-weight reading.

### 7. Smaller things

- Line 21: "86 spots ... half of them priced at a jam". Measured: the sizing table covers
  **36** of the 86 spots and **every one of those 36** carries a jam price. "Half" is loose in
  a contract that forbids loose counts.
- Line 66: "a lower target would make `achieved < target` false". The achieved gap is
  0.00015591 against a target of 0.00016, so any target above 0.00015591 is still met. What
  is true is that the gap sits 2.6 percent under the target and the cap nearly bound.
- **44 of the 249 committed spots have an arrival that rounds to zero** in parts per billion.
  The contract asks for that count to be printed, which is right; phase 15 should know that a
  sixth of the committed set is never dealt in practice before it builds a drill on top.

### 8. Structural: the contract is one line from the cap and carries about twenty-five typed counts

The contract states, as obligations, roughly twenty-five numbers that stage 6 must reproduce.
Every one I checked reproduces today. But the same document has been rewritten four times
because a number moved, `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` is filed
against exactly this, and the file now sits at 299 lines against a 300-line cap with an
amendment rule that only ever adds lines. If any count moves at stage 6, the only legal move
is a fifth rewrite.

The cheapest protection is to state the fewest counts the criteria genuinely need - the
census buckets, the committed total, the coverage figure - and let the generator carry the
rest, which is what the contract already demands of the packet.

## Blockers, non-blockers, alignment

- **Blockers**: finding 2 - **resolved 2026-09-02**, decision 52.
- **Non-blockers**: findings 3 and 4 **fixed 2026-09-02** (decision 52); 5, 6 and 7 stand.
- **Withdrawn**: finding 1, on Taylor's objection, re-checked against the export.
- **Alignment**: finding 8, and the uncited big-blind band in finding 1. `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` already
  carries it; nothing in this stage can fix it.
