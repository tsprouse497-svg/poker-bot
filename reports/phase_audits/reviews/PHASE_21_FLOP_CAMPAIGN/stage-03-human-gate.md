# Phase 21 stage 3 review: the human gate

Independent read-only review of `git diff aaaf4d7ae7cc680bceb6ae022c3aa3be469e6be8` over
`backlog.yml`, the active ExecPlan, the contract and the decision list, as committed in `b6baefb`.
The reviewer wrote none of it. Judged against the transcription of Taylor's ten answers of
2026-09-26 given in the review brief, `AGENTS.md`, `docs/LOOP.md:73-116`, GTOpen's source at
`~/projects/gtopen` (commit `4aee435`), and the committed preflop chart. Scratch scripts re-run:
`street_counts.py`, `vram.py`; two new ones written by this review in the same scratchpad,
`rev3_sbbb_vram.py` and `rev3_river_by_line.py`. Below, `CONTRACT.md` is `docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md` and `DECISIONS.md` is the decision list.

The loop's question - does the record say what was ruled, costs included - has a mixed answer. Eight
of the ten answers are faithful and add nothing (decisions 2, 3, 4, 6, 8, 9, 10 and the provider in
5). Decision 1 is faithful on the answer but adds an acceptance he never gave, and decisions 5 and
7 record coordinator additions inside his answer as if ruled. No figure he was shown was wrong
enough to change his ruling, so nothing here needs his answer re-asked; but the river ruling opened
one new frozen-into-data question nobody has asked him, and it left five contract criteria
wrong, unmeetable or untestable as written. Seven blockers, all fixable by edit except the format question.

Mechanics: `unanswered_frozen` (`scripts/loop_stage.py:305-311`) reads every one of the ten brackets
as answered, since each starts `[Ruled by Taylor, 2026-09-26]`; decisions 11 to 14 are
`runtime-reversible` and stay `[ ]`, which is correct. The contract is 293 lines, under the 300 cap,
with 7 lines of room for the fixes below.

## Blocker

- [resolved] **Decision 1's answer adds "whatever the storage costs", which Taylor did not say.**
  `reports/phase_audits/decisions/PHASE_21_FLOP_CAMPAIGN_DECISIONS.md:83`. He picked the option
  "Keep the river too" after being shown "roughly 2.5 TB per opening line by my rough estimate,
  which could shrink a lot once compressed". That is acceptance of about 2.5 TB a line, not of any
  size. The phrase pre-authorises exactly the case the contract's own measurement exists to catch
  (`docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md:213-215`): a measured size several times the
  estimate. Fix by edit, not re-ask: record that he accepted "roughly 2.5 TB a line, a rough
  estimate", and that the measured size goes back to him with the campaign budget.

- [resolved] **The stored format of the turn and river is a frozen-into-data choice no one has ruled, and the
  storage he accepted swings by up to thirty times on it.** Both figures he ruled on assume "about
  one byte a number" (`DECISIONS.md:58-60`); the 1.4 GB a flop is `street_counts.py`'s 3,620,708
  river action slots times about 396 hands at one byte. The contract never pins a format: it calls
  1.4 GB "the rough estimate ... in a compact format" (`CONTRACT.md:215`) and leaves the harvest
  method, including GTOpen's whole-solve save of about 11 to 12 GB a flop (`DECISIONS.md:61`), to
  stage 6 (`CONTRACT.md:211-213`). In today's format, 21 to 31 KB a decision point
  (`DECISIONS.md:57`), 1,477,056 river points is 31 to 46 GB a flop, 55 to 81 TB a line; at four
  bytes a number (f32) it is about 5.7 GB a flop, 10 TB a line. One byte a number also rounds every
  frequency to steps of 1/255, about 0.4 percent, and he has ruled against lossy storage before
  (phase 16's decision 20, f32 arenas); he was told "a compact format", never that it rounds. This
  is a new question, not his answer re-asked: add a `frozen-into-data` item for the turn and river
  storage format and precision, with the size a line under each option, and put it to him before
  stage 4 freezes tests that would pin one.

- [resolved] **The river count the contract freezes includes 30,772 decision points that cannot occur.**
  `CONTRACT.md:208` says one flop's solve "holds ... 1,507,828 river decision points" and a test
  asserts the counts per board (`CONTRACT.md:211`). `street_counts.py` multiplies by 49 at both
  card deals, and that matches GTOpen's tree, which builds a river subtree even under the card the
  turn already dealt (`~/projects/gtopen/crates/solver/src/tree.rs:692-697`: "only the static root
  board is excluded ... traversal ... never visits it (~2% of nodes/arena)"). 1,507,828 = 628 x 49
  x 49; the reachable river points are 628 x 49 x 48 = 1,477,056. Those dead slots are never solved
  and `walk_path` cannot deal a dealt card, so a harvest cannot return 1,507,828 and a frozen test
  asserting it forces stage 6 to fail or fake it. State both: 1,507,828 in the tree, 1,477,056
  reachable, and the test asserts the reachable count. The counts are also the committed line's
  only; `CONTRACT.md:204-206` already re-derives per line, so the test must use each line's own.

- [resolved] **Two of the amended criteria cannot be tested offline, and the gate runs offline.**
  `CONTRACT.md:259` requires the gate to pass "with no GTOpen, no network and no fetched object".
  (a) "a test asserts the counts per board" (`CONTRACT.md:211`) on every street: turn and river
  objects live only in the bucket, and git holds only "the flops held and one fingerprint"
  (`CONTRACT.md:220-221`), so offline there is nothing carrying a river count to assert. (b) The
  fingerprint "which the gate checks against the manifest offline" (`CONTRACT.md:221`): the file it
  fingerprints is in the bucket, so offline the gate can check only the manifest's own shape. Both
  are new with this amendment. Fix: the manifest carries per board and per street the decision
  point counts and object digests; the offline test asserts those counts against the tree walk; the
  fingerprint is checked by the fetch command, and the report says so.

- [resolved] **The table re-run needs "a machine that has fetched every object"** (`CONTRACT.md:242`). After the
  river ruling that is about 11.7 TB for five lines (`rev3_river_by_line.py`), and the re-run
  plays no turn or river (`CONTRACT.md:245-246`). As written, the criterion needs a disk this Mac
  does not have and a download out of AWS nobody has priced or ruled. Fix: fetched every flop
  object of the covered lines.

- [resolved] **Cost per solved flop, which picks the machine, still counts only the flop harvest.**
  `CONTRACT.md:166-168`: "harvest of every flop decision point and upload". A closed flop now means
  every street (`CONTRACT.md:207`), and pulling out and uploading about 1.5 million river points is
  likely a large part of that cost (see below). Ranking candidates on a flop-only harvest can pick
  the wrong machine. Fix: "harvest of every decision point the flop closes on, and upload".

- [resolved] **The GPU card size recorded as his ruling is the coordinator's, and it is too small for the
  first line.** Decision 5's answer (`DECISIONS.md:152-153`) and `CONTRACT.md:185` say "a card of 40
  GB or more". Taylor answered "AWS" to a question about CPU machines, and "Try it in the trial" to
  a question with no card size; 40 GB came from decision 7's note on the committed line
  (`DECISIONS.md:185-186`, 33.7 GB). Small blind against big blind, first by his decision 9, needs
  about 47.2 GB of card memory on its largest flop, `2c2d2h` (`rev3_sbbb_vram.py`, by `vram.py`'s
  formula: arena 17.19 GB), so a 40 GB card cannot hold the memory bar `CONTRACT.md:156-162`
  demands. Fix by edit: a card that holds the memory bar of the lines it would solve, about 47 GB for
  small blind against big blind, and mark it as the coordinator's consequence rather than his words.

## Non-blocker

- **Decision 5 and 7's answers carry coordinator process inside his ruling.** "The specific machine
  types and their hourly prices are put to him before anything is rented" (`DECISIONS.md:153-154`)
  and "is not used for the campaign without another ruling" (`DECISIONS.md:194-195`) are sound, and
  the second matches `CONTRACT.md:182`, but he said neither. Move them after the bracket, or prefix
  "Coordinator's consequence:", so a later reader can tell what he ruled. Same for "The candidates
  are as recommended" (`DECISIONS.md:151`): he picked a provider; the three-machine framing was in
  the question, which is fair to carry, but say so.

- **Decision 1's answer does not record the cost of "store now, play next".** The option he picked
  said phase 21's table test would still show hands stopping at the turn. The contract carries it
  (`CONTRACT.md:92-93, 245-247`), but the answer (`DECISIONS.md:85-88`) records only the choice.
  One clause: "accepting that phase 21's table result still voids every hand at the turn".

- **The river re-solve claim he was shown is an unmeasured estimate, and it erred in the direction
  that made his choice look costlier than it may be, not cheaper.** "The river is almost all of a
  solve's work" holds: 1,507,828 of 1,514,261 action nodes, 99.6 percent, and every showdown sits
  under the river. "About as much machine time as this campaign again" is an order of magnitude,
  never measured. "We don't redo whole flops later" is optimistic: re-solving river pieces from a
  saved turn with strategies alone and no saved values is the unsafe kind of re-solve, and its river
  would not be the one solve's river, which the closure rule (`CONTRACT.md:47-48`) forbids mixing.
  That only strengthens his choice, so it is no reason to re-ask; the record should call it an
  estimate (`DECISIONS.md:79-81` states it as fact).

- **Nobody showed him a dollar figure for storing the river, or the five-line total.** 2.5 TB a line
  is fair as an average but the lines differ: at one byte a number and the committed line's slot
  count, small blind about 3.5 TB, button 2.6, cutoff 2.1, hijack 1.9, lojack 1.6, about 11.7 TB in
  all (`rev3_river_by_line.py`; each line's own tree will move these). At AWS's published list
  price for standard storage, around $0.02 a GB a month (not checked today), that is on the order
  of $250 to $300 a month, recurring, and every download out of AWS is billed per GB on top. The
  contract's campaign stop (`CONTRACT.md:240-241`) names only the campaign budget and the fifth
  line, and the vetting packet (`CONTRACT.md:278`) asks only what was spent. Add the monthly storage
  bill and the river's own share of harvest and storage to the campaign-budget ask, so he can
  revisit the river on measured numbers.

- **The $100 trial was sized before the river was in it.** Decision 6's figure, about 8 to 22 hours
  at this Mac's speed (`DECISIONS.md:165-171`), names turn read-back as "extra and unmeasured" and
  never names the river. The trial now harvests and uploads six closed flops at 1.4 GB or more each.
  `CONTRACT.md:154-155` halts at the cap, so no overspend; but the enumerated count beside the cap
  (`CONTRACT.md:148-152`: "14 solves on the chosen box") also leaves out decision 13's six settling
  runs, which decision 6 counts in this budget, and the GPU's CPU-first flop. Restate the count.

- **The ExecPlan still forbids what the ruling now requires.** `docs/exec_plans/active/
  PHASE_21_FLOP_CAMPAIGN.md:21-22`: "Forbidden throughout: ... turn and river cells". Should read
  that turn and river are stored but not played.

- **A line break renders as a list item.** `CONTRACT.md:240-241` breaks "the fifth admitted line" /
  "- and the report names which one" so the second line starts "  - ", which Markdown reads as a
  nested bullet and breaks the bold. Reflow.

- **The line order figures check out.** 5.53, 3.66, 2.75, 2.71, 2.42 (`CONTRACT.md:196`) match
  `DECISIONS.md:225-226`; 830.8 x 14 x 1,755 = 20,412,756 bytes, "20.4 MB" (`CONTRACT.md:222-223`);
  11.6 GB a line for the turn is 6.6 MB x 1,755, so "about 12 GB per opening line in a compact
  format" was honest for the format named. The 240 to 350 GB in today's format was not shown in
  that question, which is why the format question above is a blocker rather than a wording fix.

- **The new backlog entry is accurate** (`backlog.yml:3-16`): the key names only flop boards
  (`src/poker_training_bot/solver_artifacts/postflop_key.py` exports `FLOP_CARDS`,
  `canonical_board`), the refusal-voids-the-hand rule is `simulator/run.py:106-110` and
  `strategy/postflop_betting.py:9-12`, and `phase: contract-update` is a value 159 entries use. It
  leaves out the one constraint the next phase inherits hardest: see Alignment.

## Alignment

- `TURN-AND-RIVER-PLAY-FROM-THE-SAVED-SOLVES-NEEDS-ITS-OWN-PHASE`: add to its reason that the stored
  river for five lines is about 11.7 TB at one byte a number, which no playing machine holds
  locally, and this repo builds an offline-first bot (`AGENTS.md:3`). The play phase has to choose
  between fetching a covered board's river before a session, a much smaller stored form, or a disk
  sized for it, and that choice belongs in its contract, not discovered in its build.
- `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`: the ruling moves this entry from
  megabytes to terabytes. Its adoption note should say the fetch command fetches by street, so a
  flop-only machine does not pull the river.

## What I held back

- **GTOpen's node query may make the river harvest cost more than the solve.** `node_view`
  (`~/projects/gtopen/crates/solver/src/query.rs:490-641`) does not just read a strategy: for each
  player it computes equity and runs `traverse_avg` over the whole subtree below the node, then
  returns every hand of both players with reach, equity, value and per-action values. Asked 1.5
  million times a flop, over HTTP as JSON, that is plausibly an hour or more a flop against a solve
  of 6 to 28 minutes on this Mac. Not measured; the contract measures it on the six trial flops
  (`CONTRACT.md:213-215`), which is right. A patch that dumps average strategies straight from the
  arenas would avoid it. Nobody told Taylor keeping the river costs machine time as well as storage.
- **Suit symmetry could cut the river storage well below 2.5 TB a line.** On two-tone flops, 46.6
  percent of all flops, the two absent suits are interchangeable, and on monotone flops three are,
  so many turn and river branches are copies. `cfr.rs:747` says CFR traverses one representative and
  expands for queries and saves. Storing representatives only is the one collapse the contract
  allows (`CONTRACT.md:95-96`). Worth measuring before any format ask.
- **The river counts are the committed line's tree.** Small blind against big blind starts from a
  pot of 5.0, not 5.5, so its tree differs and 14 / 6,419 / 1,477,056 do not carry to it.
- **AWS prices in this note are from memory, not checked today.** The storage dollar figure is an
  order of magnitude only.

## Round 2

Re-review of `f006ecc` (`git diff HEAD~1..HEAD`), with the coordinator's exact wording of the two
re-asked questions and Taylor's answers: A, "Keep, but measure first (Recommended)"; B, "2 bytes
(Recommended)". Line numbers below are at `f006ecc`. The contract is 298 lines; nothing asked here
needs more than one added line, so none pushes it past 300.

### Blocker

None new. All seven round 1 blockers are fixed and marked `[resolved]` above:

1. "Whatever the storage costs" is gone. Decision 1 now reads "accepting roughly 2.5 TB a line as a
   rough estimate" (`DECISIONS.md:83`), then records question A faithfully: the harvest may take
   longer than the solve, about 11.7 TB for five lines, about $250 a month from memory, and his ruling
   keep but measure first, confirmed with the campaign budget (`DECISIONS.md:84-90`). It matches the
   option he picked, and adds nothing.
2. The format question was asked, not edited in: new decision 15 (`DECISIONS.md:297-309`), class
   `frozen-into-data`, three options with sizes, and his answer "two bytes". The precisions shown were
   right: 1/255 is 0.39 percent, 1/65,535 is 0.0015 percent, and the flop's "0.1 percent" is
   `WEIGHT_SCALE = 1000` (`src/poker_training_bot/solver_artifacts/postflop_harvest.py:66`). The
   contract applies it (`CONTRACT.md:219-220`).
3. The river count is 1,477,056 reachable, with the 30,772 dead slots named and not kept
   (`CONTRACT.md:210-213`).
4. The manifest now carries each board's counts per street and the offline test asserts those; the
   fetch command checks fetched objects and the index fingerprint; the gate checks the fingerprint only
   against the committed sample (`CONTRACT.md:214-215, 226-227`). Both parts are now testable offline.
5. The table re-run needs "every flop object" (`CONTRACT.md:247`).
6. Cost per solved flop now counts "every flop, turn and river decision point, and upload"
   (`CONTRACT.md:169`).
7. The card must hold the memory bar, about 47.2 GB on `2c2d2h` (`CONTRACT.md:186-187`); decisions 5
   and 7 now mark the machine-type ask, the card size and the non-repeating-GPU rule as the
   coordinator's, not his (`DECISIONS.md:157-160, 199-202`).

### Non-blocker

- **Resolved from round 1:** coordinator procedure labelled in decisions 5 and 7; the cost of "store
  now, play next" recorded (`DECISIONS.md:93-94`); the ExecPlan no longer forbids turn and river
  cells, only code that plays them (`docs/exec_plans/active/PHASE_21_FLOP_CAMPAIGN.md:23-24`); the
  $100 count restated with the six settling runs and the GPU's CPU-first flop, and the note that $100
  predates the river (`CONTRACT.md:151-154`); the stray bullet at the campaign stop reflowed
  (`CONTRACT.md:245-246`).
- **Still open, small: the dollar cost at two bytes was never put to him.** Question A gave about $250
  a month at one byte; question B gave only terabytes a line. Two bytes doubles it, about 23 TB, very
  roughly $500 a month on the same unchecked rate. Decision 15's answer (`DECISIONS.md:307-309`)
  records the 23 TB but no bill. Since he confirms the river with the campaign budget, one line in the
  contract fixes it: the campaign-budget ask carries the measured river size and its monthly bill
  checked against AWS's current price. Nothing in `CONTRACT.md` requires a dollar figure for storage
  today (`CONTRACT.md:217-219`, vetting list at `CONTRACT.md:283-286`). One line; it fits.
- **"About 2.9 GB a flop for the river" should be about 2.8.** 1,435.6 MB x 48/49 x 2 = 2.81 GB; 2.9
  uses the count with the dead slots in it (`CONTRACT.md:220`). A word change, no new line.
- **Decision 1 still states the river re-solve cost as fact**, "so about the campaign's machine time
  again" (`DECISIONS.md:80`). It records what he was told, and question A has since superseded it, so
  this is a wording nit only.
- **The contract says nothing about the case where he drops the river at the budget confirmation.**
  "A solved board closes ... on every street" (`CONTRACT.md:209`) would then be wrong, and changing it
  is a `contract-update`. Worth one clause saying so in the ExecPlan, not the contract, so it costs no
  contract line.
- Decision 15's answer bracket has no closing `]` (`DECISIONS.md:309`). The parser reads it as
  answered (`scripts/loop_stage.py:297-298, 308`); cosmetic.

### Alignment

Both round 1 notes landed:
- `TURN-AND-RIVER-PLAY-FROM-THE-SAVED-SOLVES-NEEDS-ITS-OWN-PHASE` now carries the 11.7 TB at one
  byte, about twice at two, and the offline-first constraint (`backlog.yml:17`). It parses (checked
  with `yaml.safe_load` through `uv run`).
- `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT` now says the fetch command fetches by
  street (`backlog.yml:9388`).

### What I held back

- The harvest cost remains the largest unknown in the river ruling. Question A says "may take longer
  than the solve", which is fair; the patch route (dumping average strategies straight from the
  arenas instead of 1.5 million `node_view` calls) is still the likely way to keep it cheap, and the
  contract rightly leaves the choice to a stage 6 measurement.
- Suit symmetry could still cut the stored river well below 23 TB on two-tone and monotone flops; not
  measured, and the contract permits it.
- The per-street counts in the manifest are the committed line's; each line's own tree sets its own
  counts, which `CONTRACT.md:204-206` already requires. The frozen test must read them per line rather
  than hardcode 14 / 6,419 / 1,477,056.
- The dollar figures are still from memory, not checked.
