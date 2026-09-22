# Phase 16 stage 8 review: the phase against its contract, consolidated

Read-only. I wrote none of the work under review; this file and
`stage-08-review-mechanical.md` are the only two I changed. No `git checkout`, no `git stash`, no
`run_verify.py` and no mutation tooling. `verification/.mutation_in_progress` was absent and
`pgrep -f 'loop_stage|check_gate_bite|run_verify'` returned nothing before I started, and the tree
was clean at `fc9a164`. Scratch lives outside the repo. Every figure here I computed in this
worktree; nothing is copied from `backlog.yml`, a report, or either lane note.

**What I read.** `AGENTS.md`; the contract; `stage-08-review-mechanical.md` and
`stage-08-review-poker.md` in this directory; the stage 6 and stage 7 notes, whose findings are not
re-filed; decisions 1 through 25; and the three commits that answer the two notes - `c6ade8d`,
`de7d1b9`, `fc9a164`.

**This note consolidates and does not restate.** The two lane notes hold the measurements and the
reasoning; each blocker below names its note and carries a verdict I checked myself.

The phase's state in one paragraph. The committed data is sound and re-derives: I recomputed the
class census, both cells' class sets, every published frequency, all five strategy digests and all
five object digests, and the whole deep-convergence block, and every one holds. What was wrong was
the reporting around it, and three of the four reporting faults are now repaired in the generator
rather than in prose. What is left is bookkeeping with a truth condition attached: a Closed list the
phase was about to apply without checking, and one sentence about to enter the packet that nobody
measured.

## Blocker

- **[resolved] The byte block labelled the whole postflop directory as the index and the sample,
  and the per-spot cost inherited it.** `stage-08-review-mechanical.md`, blocker 1. Repaired at
  `de7d1b9` and checked here: the report now prints three figures with three labels - whole artifact
  tree 4,938,950, whole postflop directory 100,845, committed index and sample 56,791 - and names
  the 44,054 bytes between the last two as the campaign's own records. Both per-spot rates are
  printed, 14,197.75 for index and sample and 25,211.25 for the directory, with a paragraph saying
  which one answers what a further spot costs and why the deep-convergence record does not grow
  with the next spot. I re-summed all three figures off disk and they are exact. The repair is
  wider than the finding and I would not narrow it.

- **[resolved] The one place the report counted the two table causes, it pooled them, while
  asserting in prose that it never does.** `stage-08-review-mechanical.md`, blocker 2. Repaired at
  `de7d1b9`: the coverage split now prints "lost to no cell for this board: 50 (19.31%)" and "lost
  to in the index and not fetched on this machine: 0 (0.00%)" as separate rows, with a paragraph on
  why the two cost different things to close. 50 and 0 is the division I measured before the repair,
  and the four cause counts still sum to the 259 flop-reaching hands.

- **[resolved] The committed campaign ran on the laptop while the contract's scope says solving
  moves to a rented cloud box, and no committed document said so.**
  `stage-08-review-mechanical.md`, blocker 3. Put to Taylor and ruled as decision 24 at `fc9a164`:
  the scope sentence binds the campaign and not this sample, which he called a test of machinery.
  The wording gap is filed as `A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE`
  rather than amended, which is right while the contract sits at 299 of its 300-line cap. The
  ruling also answers the half of my finding that was not about the contract at all: every timing
  the phase publishes is a laptop figure and the packet now says so.

- **[resolved] The packet was about to carry a sentence describing a bot this repo does not
  build.** `stage-08-review-poker.md`, blocker 1, which is the largest finding of the stage and is
  the domain reviewer's: twenty thousand deals of the composite the repo actually builds give zero
  bets and 5,365 voided hands, no committed cell's successor is committed, and the seam is at
  hero's first flop action rather than at the turn. Ruled as decision 25 at `fc9a164`: the sentence
  does not go in, the packet states what the bot does and prints the coverage number beside it. The
  obligation now sits on the stage-9 packet, which does not exist yet; what discharges it is the
  coverage number and the closure fact in the packet's own words, not this ruling.

- **[resolved]** at `7254a50`, re-measured against `main` rather than taken on report: the backlog
  now carries **exactly five status changes and no others** - the four I ruled close plus
  `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`, which closes because its condition was met rather than
  waived. Both refusals stand as `deferred` with the reasoning written into the entries, including
  the sentence saying the contract's list expected otherwise. Every closing note carries the ground
  I gave and both caveats survived - capability rather than coverage on the strategy entry, and the
  never-arrived precondition on the pot-odds one - and the three coverage entries that make the
  first closure honest are all still open. The stale 32 GB in the memory-guard entry now reads 34.4.
  The original diagnoses are appended to rather than replaced, so the pointers into them still
  resolve.

  **The contract's Closed list, ruled entry by entry. Four close, three do not, and the three are
  the point.** `stage-08-review-mechanical.md`, blocker 4, measured: this lane adds 90 entries to
  `backlog.yml`, all deferred, and changes the status of none. Below is a verdict and the evidence
  per entry. A status change is implementation and is the coordinator's to apply; this is the
  ruling it applies from.

  **Close - `V2-POSTFLOP-STRATEGY`.** The entry names its own condition: what was missing was a
  ruling on how deep the committed solution goes and on what the bot does on a board it holds no
  cell for. Decision 1 rules flop only and decision 2 rules the full canonical set with abstraction
  deferred, so both are answered. A strategy that can bet and raise exists, is the composite's
  postflop component rather than an import, and is exercised by frozen tests that require a
  committed spot to produce each with an amount. Close it on capability, not on coverage: the
  coverage gap the domain note measures keeps three live entries of its own -
  `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`,
  `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN` and
  `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS` - and the closure is honest only
  while all three stay open and the packet carries decision 25's number.

  **Close - `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK`.** The entry specifies the rule down to the
  arithmetic and the repo ships exactly it: `river_pot_odds.py:87` is `(wins + ties/2) / 990` and
  `:98` is `to_call / (pot + to_call)`, both off the query, behind the explicit flag decision 5
  ruled, with the firing rate published and the over-calling cost stated as the entry demanded. One
  thing the closing note should carry, because the entry raised it and it is still true: the entry
  said the rule was worth building only once something bets at the bot, and nothing does - the
  domain note measures zero bets in twenty thousand hands of self-play, and the 12 of 12 rate is
  over this repo's own river enumeration rather than over a table. It ships correct and untested
  against a betting opponent.

  **Do not close - `POSTFLOP-UNBEATABLE-EARLIER-STREETS`. The work it describes was not done.** The
  entry asks for the unbeatable call to be extended from the turn back to the flop, costed at
  1,081 holdings against 990 runouts and answered by a faster evaluator rather than a new rule.
  `postflop_fallback.hand_cannot_lose:194` still raises on a flop board and its docstring still
  states that cost unchanged. Nothing about the enumeration moved. What did move is the entry's
  surroundings, and this is worth restating rather than closing on: `composite.decide:136` routes
  every postflop street to the betting strategy, so the fallback is no longer the bot's postflop
  component at all and the flop fold the entry was filed against no longer happens - the bot
  refuses instead. The entry's subject survives that move, because on the 22,060 board classes with
  no cell the bot now refuses where an unbeatable hand could still call. Closing it would record as
  done a piece of work nobody did.

  **Close - `SOLVER-ALLIN-THRESHOLD-UNITS-DIFFER-BY-SURFACE`.** The entry's residual is "any future
  solve script needs its own [guard]", and the one future solve script carries one:
  `postflop_solve_driver.py:154` declares the minimum by name and `:158` refuses below it, citing
  this entry. The committed `solve_config.json` posts 85.0. The hazard itself is external and
  permanent, so what matters for closing is whether the knowledge survives the closure, and it
  does: `docs/GTOPEN_SOLVER_NOTES.md:43-44` records the trap durably, including that the postflop
  route reads the field as a percent and that the measurements post 85.0.

  **Close - `ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS`.** Both halves are discharged in the document
  the entry names. `docs/GTOPEN_SOLVER_NOTES.md:39` states that the README's two figures are branch
  counts rather than speedups, and `:41` carries the precondition the entry asked for - that one
  suit-specific weight anywhere in either range collapses the group and the whole saving goes to
  zero - and cites the entry by id. The phase then acts on it rather than only recording it: the
  cost model uses exact per-class orbit factors, which I re-derived by brute force over all 22,100
  boards as 19.314, 12.000 and 4.000 boards a class, the report prints the warning against taking
  the orbit as one number with the 24.26% overstatement beside it, and the class-level floor is the
  mechanism that protects the precondition - I checked the smallest surviving weight on each side,
  0.0147 and 0.7865, both above the 0.01 floor.

  **Do not close - `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS`, and restate it against Darwin.** The
  contract expected this entry to leave the Closed list because the rented Linux box has
  `/proc/meminfo`. Decision 24 has now ruled that the sample was solved on the Apple M4, so the
  premise did not dissolve - it holds, for the machine actually used. Half the entry is discharged:
  phase 16's driver carries its own ceiling, `MEMORY_CEILING_FRACTION = 0.40` at
  `postflop_solve_driver.py:59`. The other half is untouched and I checked it rather than assuming -
  `scripts/extract_gtopen_preflop.py` contains no occurrence of a memory ceiling, a RAM figure or
  any memory handling at all. The restatement is the opposite of the one the contract drafted, and
  one figure in the entry is stale: it says "this 32 GB machine" where the machine is 34.4 GB.

  **Closed after the sweep, 2026-09-22.** The survivor was fixed at `7254a50` and I re-ran the
  sweep: no live document now offers the falsified ratio as a basis for reasoning. The ruling as
  first written follows, and it was "do not close" only while that one line stood.

  **Do not close - `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`. Its condition is checkable and it is not
  met.** The contract closes it only once no live document still says the turn costs 49 flops.
  `docs/V2_ROADMAP.md:216` still reads "only the ratio is safe to reason from: the turn is about 49
  times a flop and the river about 2,350 times", which is not a historical mention but the sentence
  offering the falsified ratio as the safe basis for reasoning. The other document the entry names
  is swept: the decision list carries the dated falsification and says no conclusion below it may
  rest on the ratio. The remaining hits are completed exec plans, which are snapshots of what a
  phase believed and are not live documents. So this is one line in one file, in a document at 307
  of its 500-line cap with room for the correction, and the entry closes the moment that line is
  fixed. It does not close before.

- **[resolved]** at `7254a50`, and it did not overstate my finding in the other direction, which
  was the thing to check. Decision 24's ruling now says only that two runs in two processes on this
  Mac constrain this machine and nothing else. The dated correction under it scopes itself to "the
  one path it could trace", says the evidence available argues against the mechanism rather than
  that the mechanism is ruled out, and claims nothing about the reduction sites I did not read. It
  does not assert that thread count is harmless. That is exactly the certainty I offered and no
  more.

  **The determinism proof is machine-local, and the reason the packet is about to give for it is
  not the one the code supports.** The conclusion is right and I would keep it: `determinism.json`
  records two processes on one Mac, so nothing in it constrains a different machine, and that holds
  whatever the mechanism. The stated mechanism - that floating-point summation order differs
  between machines - is not established, and the one path I read argues against it. In GTOpen's CFR
  recursion (`crates/solver/src/cfr.rs:632`) the parallel branch is
  `reps.par_iter().map(run_child).collect()` into an ordered `Vec`, and the results are then merged
  by a sequential loop over `cards` in a fixed order through a `by_card` table keyed by card, so
  the accumulation order in that path does not follow the thread count at all. Thread count is
  machine-derived - `init_rayon` in `crates/server/src/main.rs:2546` takes
  `available_parallelism() / 2` unless `SOLVER_THREADS` overrides it, which is five on this ten-core
  machine and is what `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT` already records -
  but I have not traced the other reduction sites, so I can neither assert summation order is the
  cause nor that it is harmless everywhere.

  What is established, and is what the packet should say instead: a proof taken twice on one
  machine constrains that machine and nothing else, and the rented box would differ in ways larger
  than an addition order. It is a different instruction set, where a compiler may contract a
  multiply and an add into one fused operation on one target and not the other, which is a
  different rounding rather than a different order. More to the point, the box exists to use the
  CUDA backend the contract's own scope names as untested - `crates/solver/Cargo.toml` carries a
  `gpu` feature on `cudarc`, and `crates/solver/src/gpu` and `crates/solver/tests/gpu_bench.rs`
  exist - and a GPU solve is not the CPU computation with the sum reordered. Name that, not
  summation order, or the packet carries a mechanism nobody measured into the document whose whole
  job this stage has been to keep free of them.

## Non-blocker

Both lane notes carry their own non-blocker lists and I endorse them as written rather than
repeating them: `stage-08-review-mechanical.md` has seven, of which the two byte and cause items are
now resolved above and the rest stand; `stage-08-review-poker.md` has five, of which N1 on where the
deep solve landed and N5 on which preflop line comes second are the two a later phase should read
before it funds anything. New here:

- **[done at `7254a50`]** The fix to `docs/V2_ROADMAP.md:216` is a one-line edit and it is the only
  thing between `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED` and closure. Checked for truth and for a second
  falsified figure, which was the risk: the replacement is true and it removes two wrong things
  rather than one. Its "node counts are not costs and the ratio above is not one either" names the
  actual origin of the error, since the 49 in the line above is the count of turn cards after a
  three-card board and the old sentence read that count as a cost multiple. The surrounding
  arithmetic survives the edit and I re-derived it: 1,755 x 49 = 85,995 and 85,995 x 48 = 4,127,760,
  both as printed, and both are genuine spot counts. The 99.5% re-derives from the entry's own node
  counts, 1,239,749 of 1,245,971 = 99.50%. The old sentence's premise was falsified too - it opened
  "No solve in this repo has been timed to a real exploitability target", which the committed
  campaign's own wall clocks contradict - and the replacement drops it. The file is 307 lines
  against its 500-line cap, unchanged, since one line replaced one line.
- The roadmap's replacement points a reader at "the phase 16 decision list for the costs", and that
  pointer is thin rather than wrong. The decision list's cost figures are a mix: real wall clocks
  from the committed campaign, and projections at a 240-iteration working point that no run ever
  produced - `deep_convergence_check.json` says so in its own words, and decision 20 records that
  every arena and timing figure published before it was taken on quantized arenas. All of them are
  laptop figures, which only decisions 20 and 24 say. A reader following the pointer cannot tell
  the three apart without reading all three decisions.
- The contract's Closed list now names an entry the phase deliberately did not close, and no entry
  owns that shape. `POSTFLOP-UNBEATABLE-EARLIER-STREETS` records the refusal at its own end, which
  is where a reader of the backlog will find it, but a reader of the contract will not: its Closed
  list still asserts the closure. This is the same shape as
  `A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE` and
  `A-CONTRACT-CLAUSE-ASSERTS-A-GAP-ITS-OWN-PHASE-THEN-CLOSED`, and the nearest existing entry,
  `CONTRACT-SCOPE-ENUMERATES-RESIDUALS-WITH-NOTHING-CHECKING-THE-COUNT`, is about a count
  disagreeing rather than about a closure being refused on evidence. Proposed as its own entry, and
  not a blocker: the substance is recorded and the stage-9 packet will carry it.
- Decision 24's correction names "pin the thread count" as the wrong fix it invited, without saying
  why anyone would reach for it - that GTOpen derives the thread count from the machine, half of
  `available_parallelism()` unless `SOLVER_THREADS` overrides, which is five on this ten-core box.
  One clause would make the sentence self-explaining, and
  `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT` already owns the fact.
- `docs/GTOPEN_SOLVER_NOTES.md:41` cites `ISOMORPHISM-FACTORS-MISREAD-AS-SPEEDUPS` by id. Closing
  that entry leaves the citation pointing at a closed entry, which still resolves - a closed entry
  keeps its diagnosis and stays in the file - but the coordinator should decide knowingly rather
  than discover it.
- Of the packet's own obligations, the report already carries the four qualifications as
  qualifications and the coverage figures decision 25 requires. Still owed at stage 9: the one
  number a reader can recompute by hand with the file and the method named, and the
  source-code-free spot-check path. The recomputable number is easy to get wrong in the direction
  this phase has already been caught in twice; the per-weight rate, 19,711 bytes over 3,198 weights,
  is a good candidate because both operands are visible in one committed place.

## Alignment

- `NOTHING-CHECKS-THAT-EVERY-RULING-REACHES-A-CRITERION`. Re-run over the two rulings added since
  the mechanical note: decisions 24 and 25 both declare a reversibility class and both are
  `runtime-reversible`, correctly - one decides where a future run happens and the other is
  bookkeeping, and neither writes a committed cell. Neither reaches a contract criterion and both
  are right not to try, since the contract cannot take the lines. That makes five of the
  twenty-five rulings now held by a decision entry alone.
- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE`. The gate blindness the Closed-list blocker runs
  into. This stage's ruling is a human reading seven entries; nothing repeatable was added, so the
  next phase's list gets the same treatment only if someone remembers.
- `BACKLOG-SWEEP-MISSES-ENTRIES-FILED-UNDER-A-CATEGORY`. Unchanged and still the larger half of the
  same problem: 45 of the 90 entries this lane filed sit under `contract-update` and no
  phase-scoped sweep sees them.
- `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES`. Unchanged by the repairs. I re-derived
  all ten digests by hand across the two rounds of this review and every one holds; the gate
  re-derives none of them.
- `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT`. The depth-ratio verdict is a
  clean instance from the other side: the decision list was swept and the roadmap was not, which is
  exactly the shape this entry describes, and it is why the closure condition was worth checking
  rather than assuming.
- `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`. Named here because it is the entry
  that already owns the machine-derived thread count, which is the one part of the summation-order
  argument that is true.
