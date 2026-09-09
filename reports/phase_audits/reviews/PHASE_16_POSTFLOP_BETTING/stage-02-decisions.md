# Stage 2 review, phase 16: the judgment-call list and its reversibility classes

Independent read-only review, two rounds. I did not write the contract, the ExecPlan, or the
decision list, and I edited nothing but this note. Round 1 reviewed the `phase-16` worktree at
`4d06494`, branch `phase/16-postflop-that-can-bet`, pointer `verification/loop_runs/16.yml` at stage
2 with `stage_base: 1d88536`. Round 2 reviewed the fix at `f2d34c3`.

Stage 1's two notes were read in full and are not re-reviewed. Every blocker in both is marked
resolved and I re-checked none of them.

The stage's question: is every reversibility class right? A `frozen-into-data` call filed as
`runtime-reversible` proceeds on its default and is then written into committed data with nobody
asked.

**The headline, round 1: all six classes were right, and I could not break any of them.** The
defects were elsewhere in the same stage's obligation. Two choices this phase's own contract calls
the things it must get right before any data were frozen-into-data and appeared on no list at all.
Decision 6's option set was not the exhaustive set it claimed, it carried a feasibility verdict on
exactly one option that was false by its own table, and no ruling on it produced the three things
the contract says its answer supplies. Decision 4's default was silent on the outcome 23 of the 30
measured solve rows actually had.

**The headline, round 2: the list grew to eleven items, every class was still right, and the work
had moved into the defaults.** Six new findings, of which the largest was not about the record at
all: decision 11's default pinned a solver menu that has never been solved on a single-raised pot,
and whose single-raised-pot tree measures 1.8x the arena ceiling on all eight committed build rows.
A fifth frozen choice, the range floor, is what closes that gap and was itself on no list.

**The headline, round 5: the poker claim put to me is sound and I would not weaken it; what it needs
is its sign marked unmeasured and the one solve that would price it.** A flop-only artifact is
genuinely not insulated from the turn and river menu - a flop action's value is obtained by walking
its own subtree, so restricting later streets changes the flop strategy. That the difference is
*worse*, and where, is unmeasured, and nothing in the committed 55 rows can isolate it, because the
only same-board pair moves four other things at once. One solve fixes both that and option 2's
disclosed evidence gap: the reduced config on a 3-bet pot, diffed against a pinned row that already
converged. The other finding is the same shape as three earlier ones - the correction landed in the
item's preamble and the numbered option below it still carries the struck claim.

**The headline, round 4: the option sheet's evidence labels are still the whole of the remaining
work, and the answer to the question put to me is that the steering moved rather than went.**
Option 3's relabelling is true on line type and reads as an absolute, while no option on the list
has a converged rainbow cell - which the same item says fifteen lines later. Two other findings are
not about steering: a coupling between decisions 11 and 6 that does not discriminate between
decision 11's own options, and which traces to a sentence of mine; and a count contradicted by the
next clause of its own sentence. Blocker 17's fix changed the wrong sentence.

**The headline, round 3: twelve items, every class right, and the remaining defects are all in how
decision 11's evidence is labelled.** The two new items are correctly `frozen-into-data` and both
are defaultless with the reason recorded, which for decision 11 is the right call and for decision
12 is the one place I would change the form. Four new findings: a converged-row count that
contradicts a line printed in the report it came from, and three evidence labels in decision 11's
new option set - option 2's unmeasured half undisclosed, option 3's fully-measured status
under-credited, and option 4's tree build described as a solve. None of the four disturbs decision
11's conclusion, which I re-derived independently and which is the most consequential thing found
in this phase.

## Blocker

Twenty-two findings over five rounds. Round 1 filed 1 through 7, fixed at `f2d34c3`. Round 2 filed 8
through 13, fixed at `408b2c3`. Round 3 filed 14 through 17, of which three were fixed at `39e6074`
and 17 needed a second attempt at `a58d7cf` because the first edit changed the wrong sentence. Round
4 filed 18, 19 and 20, all fixed at `a58d7cf`. Round 5 files 21 and 22 against `a58d7cf`.
**Twenty are marked `[resolved]`; 21 and 22 hold the stage.**

Each mark carries what I re-derived under it, and nothing is marked on the strength of a commit
message. From round 4 on I stopped comparing fixed text against my own earlier note and re-derived
every figure from the tree instead, which is what found blocker 19 - a claim of mine that had gone
unchallenged for four rounds because I was the one checking it. Round 5 corrects a limit I had
recorded in my own method: the report's sizing configs *are* expanded, in an interned appendix I had
not found, and the coordinator read it and closed the caveat I had left open.

Nested bullets are absent at every depth in this section on purpose, per
`REVIEW-QUEUE-COUNTS-EVIDENCE-BULLETS-AS-BLOCKERS`; supporting detail is prose, tables, or indented
plain text.

Round 2's shape repeats stage 1's, and it is worth stating before the findings. Five of the six new
ones exist only because the fix added four defaults, and one of those five is a phrase of mine that
the fix adopted. Adding the missing items was right, the list is much better for it, and the
defaults are now where the work is - which is what the coordinator asked me to check hardest and is
where almost everything below came from. Two of the six are collisions between a new default and an
existing contract criterion, found only by reading the two documents against each other, and
neither could have been found by reviewing the decision list alone.

Blocker 8 is the one to read first. It is not a documentation defect: on the committed evidence, the
menu decision 11 defaults to has never been solved on the line type decision 3's ruling selects, and
its tree is 1.8x the solver's arena ceiling.

### Round 1, all verified fixed at `f2d34c3`

- [resolved] **1. The postflop spot key's grammar is the phase's largest frozen-into-data choice and it is on
  no decision list.** Both the contract and decision 3 say so in their own words. The contract:
  "Adding spots at a fixed key is additive; changing what the key can express re-derives every
  committed cell, which is why this is the one thing the phase must get right before any data."
  Decision 3: "the one thing this phase must get right up front is the postflop spot key". That is
  the definition of `frozen-into-data` restated, and `verification/loop_policy.yml` gives the
  identical reason for phase 12 not auto-advancing: "Widening the spot key re-derives the committed
  artifact, so every chart cell moves." Phase 12 got a 30-item decision list for the preflop
  vocabulary. Here the grammar reaches stage 4 and stage 6 as an implementer's choice, with no
  item, no default, no class, and no human, in a phase whose committed cell count is thousands
  rather than 249.
  The sub-choices that are actually open, each of which re-derives every cell if it moves later:
  how the preflop line compresses into the key, and specifically whether the price is carried or
  substituted, since decision 3's own annotation records that every corpus key reads `@2.5` while
  the corpus median open is 2.25bb, so the substitution policy is baked into the key rather than
  observed through it; whether the flop action carries bet sizes, size buckets, or bare action
  classes, which is what decides whether a later menu change is absorbable or a full re-derivation;
  and whether pot and effective stack are in the key or implied by the line. The contract names the
  key's producer discipline (derived and compared, never parsed; one producer; mismatch refused)
  and its board half (the canonical suit-isomorphism representative, with a test). It does not rule
  any of the three above. Add the item with its options and its class, or state in the item why each
  sub-choice is not a judgment call.
  **Verified fixed at `f2d34c3`, and split better than I asked.** The three sub-choices are
  decisions 8, 9 and 10, one heading each, and splitting them rather than writing one key item is
  the right call on blocker 7's own mechanic: `unanswered_frozen` holds one answer per heading, so
  three questions in one item would have been the same trap one level down. All three declare
  `frozen-into-data` and all three carry a default. I confirmed with the parser that the file now
  holds eleven items, every one with a valid class, and that decisions 8, 9 and 10 all read as
  unanswered. Each item also states why it is frozen rather than asserting it, and decision 8
  reproduces the `@2.5` substitution point in more detail than my finding did, including that the
  ranges a spot was solved against are the ranges at the substituted price. Two defects in these
  new defaults are filed as blockers 10 and 11 below; neither reopens this one.
- [resolved] **2. The bet-size menu is frozen into every committed cell, decision 4 says it dominates the
  accuracy this phase publishes, and no item rules it.** Decision 4's own qualification 2: "0.3%
  bounds exploitability only against an opponent confined to the same bet menu. The best-response
  pass walks the same tree. The abstraction error of a two-size menu is larger than the target." So
  by the decision list's own statement the menu is the larger of the two error terms, and the
  smaller one is the thing the list asks a human to rule. The menu MAINT-26 actually measured is
  visible in the committed cost report's row data:

  | field | committed value in `reports/active/latest_postflop_solve_cost.txt` |
  |---|---|
  | root menu | `0 Check \| 1 Bet 5.28 (33%) \| 2 Bet 12 (75%)` |
  | `max_raises` | 2 |
  | `add_allin` | false |
  | `allin_threshold` | 85.0 |

  That is a two-size menu with a check, which is exactly the case the qualification says carries an
  abstraction error above the target. It is also the silent input to decision 6: every row of its
  encoding table is priced at "2 actions" or "3 actions", and the 2-to-3 step is worth 1.5x, so the
  size ruling is being taken on an action count nobody chose. And the menu cannot be changed after
  the fact: it is the action vocabulary of every committed cell and of the key that addresses it.
  This owes its own item, and it is a poker judgment rather than a size one.
  **Verified fixed at `f2d34c3` as a filing; the default it now carries is blocker 8 below.**
  Decision 11 exists, declares `frozen-into-data`, quotes decision 4's qualification as its reason,
  and states the two things I flagged: that the menu is decision 6's silent input and that the
  2-to-3 action step is worth 1.5x. It goes further than my finding by adding two measured bounds,
  and I checked both against the committed rows rather than the summary. The 21.7 GB against 3.7 GB
  comparison is real and is at one menu, not two: both `lineA-srp-*` and `lineB-3bp-*` carry
  `config.ip@2827d093808a` and `config.oop@2827d093808a`, and their `menu_sha256` differ only
  because the root sizes are echoed in chips against pots of 5.5 and 16.0. I had suspected a
  confounded comparison and it is not one. The range-floor claim also reproduces exactly:
  `rung-lineA-pinnedmenu-rangefloor0.01` is 10,881.1 MB against 21,663.4 MB unfloored, a factor of
  1.99, with `action_nodes` identical at 2,347,996 in both. The filing is right. What follows from
  those two numbers is not in the item, and that is blocker 8.
- [resolved] **3. Decision 6 asserts an exhaustive option set and omits two options, one of which decision 2's
  ruled answer already pre-authorised.** The list says "The four ways out" and closes with "What is
  **not** on the list: grouping unsolved boards onto solved ones", which names abstraction as the
  single exclusion. Two omissions survive that.
  First, a flop subset plus refusal. Decision 2's ruled default states the fallback ladder in its
  own words: "If 1,755 per line proves unaffordable once solve time is measured, the fallback is
  fewer preflop lines, then a flop subset plus refusal, and never a subset plus abstraction." Taylor
  answered "take the default", so that ladder is ruled. Decision 6 carries rung one (option 2,
  fewer lines) and omits rung two, and its exclusion paragraph names only rung three. A subset plus
  refusal is not abstraction, decision 2 distinguishes them explicitly, and it prunes the dominant
  factor in the size arithmetic, since the 1,755 classes are what the 1,286,792 hero-combo classes
  are summed over. Decision 6 also does not observe that its own measurement partly falsifies the
  premise decision 1's answer rests on, "stay complete on the axis where completeness is cheap":
  completeness is cheap in solve time and is not cheap in disk.
  Second, moving the bytes rather than shrinking them. `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`
  names four answers to this exact wall, and decision 6 cites the entry for its history but not for
  its options: "to raise the cap with a stated basis, to split the artifact per spot or per family
  so a re-solve produces a reviewable diff, **to store solves outside data/artifacts with only
  derived charts inside it**, or to accept that the committed chart is always a selection and to
  standardise how the selection is recorded." The third of those is not option 3 and not option 4;
  it fits inside today's cap without raising it and without cutting coverage. The contract's
  Forbidden shortcuts forbid raising the `data/artifacts` cap and forbid nothing about where a solve
  lives. It may well be the wrong answer, on the reviewability grounds the cap exists for, but it is
  the human's to reject rather than the list's to omit.
  Worse, the ExecPlan has already pre-empted it. Its expected scope declares
  `data/artifacts/postflop/**` at stage 6 as "the committed data the phase exists to write", which
  fixes the location inside the capped directory before the ruling that is supposed to decide it.
  **Verified fixed at `f2d34c3`.** The list is six levers, the header says "The six levers", and
  "the four ways out" is gone. Option 5 is the flop subset plus refusal with decision 2's ruled
  fallback quoted verbatim, which is the right framing because it shows the option is inside what
  Taylor already ruled rather than a reviewer's addition, and it states its cost from decision 3's
  own figure, the 47-flop subset covering 2.7% of flops. Option 6 is keeping the solves outside
  `data/artifacts`, and it is stated better than I asked: rather than presenting it as a loophole it
  names the question it actually raises, whether the cap exists for reviewability or for repo
  weight, and says the answer decides whether the option is a fix or an evasion. That is the honest
  form and it is the one that does not steer. The abstraction exclusion is unchanged and still
  correctly names only abstraction. What I did not see addressed, and am not reopening as a blocker
  because it is the ExecPlan rather than the decision list: the stage-6 expected scope still declares
  `data/artifacts/postflop/**`, which pre-empts option 6. It is a non-blocker below.
- [resolved] **4. Decision 6 steers to option 4, and the sentence that does it is false by decision 6's own
  table.** Answering the question as put: "the only option that fits today without touching the cap"
  is not a neutral fact. It is not a fact at all, and it would still be a thumb on the scale if it
  were, because a feasibility verdict attached to exactly one of four options is a recommendation
  whatever its truth value.
  It is false in two independent ways. The first is a contradiction inside a twenty-line span, and
  it is the same shape as stage 1's blocker 6 arriving a third time. The framing paragraph reads:
  "the cap affords 5 hero nodes for one preflop line (12.3 MiB, 0.82x), 1 node for three lines (7.4
  MiB, 0.49x), and 1 node for five lines (12.3 MiB, 0.82x)". The first and third are the same
  number of bytes because cost is a product: 5 x 1 and 1 x 5 are both 12,867,920 bytes at
  2,573,584 bytes per node per line, which is 0.816x of the 15,774,195 bytes of headroom. The first
  is option 2 taken to its limit; the third is option 4 taken to its limit. The list then says
  option 2 "does nothing until there is one line left" and that option 4 is the only thing that
  fits. Both statements are about the same twelve megabytes.
  The second is that option 4 does not fit on its own at all. Its 0.49x and 0.82x are quoted "in
  the aggressive encoding", which is option 1's binary one-byte-per-weight row. In the chart's own
  committed format that row is 98.62 MiB per node per line, 0.15 nodes affordable, 6.6x over at one
  node for one line. So option 4 is not an alternative to option 1; it is a combination with option
  1's most extreme row, and a human ruling "option 4" would unknowingly also be ruling the encoding
  the contract says decision 6's answer must supply, including the reviewability loss the cap exists
  to prevent and the quantisation cost the list itself records as unmeasured.
  Two smaller mechanisms push the same way and are worth naming because they are cheap to fix. The
  example set skips the middle of the frontier: at 2.45 MiB per node-line the cap affords about 6.13
  node-line units, so 3 nodes x 2 lines and 2 nodes x 3 lines both land at 15,441,504 bytes, 0.979x,
  and neither appears anywhere, while the two failures shown are both at 5 nodes. Three nodes is the
  contract's own count of a flop ("hero acts, villain answers, hero faces a bet or a raise"), so the
  omitted cases are the complete-flop-tree-at-two-lines cases. And the closing clause of option 4
  instructs the reader on the comparison set: "the option a reader should weigh against option 3
  rather than against the others". Ordering and detail run the same direction, option 1 carrying the
  table and two paragraphs that are almost entirely cost while option 4 carries the only "fits".
  The fix is not to add a recommendation. It is to state the constraint as the budget it is: at a
  named encoding, the cap affords about N node-line units, here is the product, rule the product.
  That is checkable, it is neutral between cutting nodes and cutting lines because they are the two
  factors of one number, and it removes every sentence above.
  **Verified fixed at `f2d34c3`, and the repair is the one I would have chosen.** The false sentence
  is struck rather than reworded, quoted in place with both of its failures named, and the frontier
  is now stated whole as node-line units with 6x1, 3x2, 2x3 and 1x6 given and "everything under
  them" said explicitly. The unit is defined before it is used, which the old text never did.
  Option 4's entry no longer claims uniqueness and instead says it is one unit and fits at any
  encoding from lean JSON up and nothing in the chart's format, which is the accurate version of
  the same fact. The "weigh against option 3 rather than the others" instruction is gone. I
  re-derived the whole frontier independently: 2,573,584 bytes per node-line at one byte per weight
  over 1,286,792 classes with two free weights, 6.129 units affordable against 15,774,195 bytes,
  and the complete fitting set is exactly 6x1, 3x2, 2x3, 1x6 and everything under them. The 0.979x
  for 3x2 and 2x3 reproduces at 0.9789. **One residue is now blocker 12, and it is my phrase and my
  error, not the fix's.**
- [resolved] **5. No answer to decision 6, under any of its four options, produces the three things the
  contract says the answer supplies.** The contract's Scope: "until it is answered this contract
  cannot name the artifact's encoding, its per-spot byte budget, or how many preflop lines fit.
  Those three criteria are the amendment this phase owes after stage 3, in `contract-update`, and no
  implementer may choose them." Test each option against that. Option 1 names an encoding and no
  budget and no line count. Option 2 names a line count only in the limit case the list dismisses.
  Option 3 names none of the three. Option 4 names a node count and, only by reference, an encoding.
  So the stage-3 ruling as currently framed cannot discharge the amendment it is the input to, and
  the shortfall lands on whoever writes the amendment, which is the one person the contract says may
  not choose it.
  On the question as put: the absence of a default is defensible and I would keep it. Four options
  whose costs fall in genuinely different places is a choice a human should make cold, decisions 1
  through 3 show that a stated default with an accepted cost is what Taylor actually rules against,
  and `check_decisions` never required a default in the first place, so the mechanical pass is not
  what is being leaned on. What is not defensible is that the ask is a menu pick when the amendment
  needs three quantities. Ask for the product and the encoding, and let the four options be the
  reasoning rather than the answer form.
  **Verified fixed at `f2d34c3`.** Decision 6 now opens with "What an answer must fix", names the
  encoding, the per-spot byte budget including the provenance fields, and the number of preflop
  lines, and states plainly that "a pick from the list is not an answer on its own; a pick plus a
  product from the budget above is." That is the ask I said the amendment needed, and it is stated
  before the levers rather than after them, so a reader meets the shape of the answer before the
  menu. The absence of a default is retained, which I agree with and said so. The provenance
  exclusion is now stated in the budget, which was my separate non-blocker; its arithmetic is
  slightly narrow and is a non-blocker below rather than a reopening.
- [resolved] **6. Decision 4's default names a target that 23 of the 30 measured rows missed, and it does not
  say what happens to a flop that misses it.** The item is honest that the seven are the reached
  rows and the rest are floors. The default is not: "target 0.3% of the starting pot, and record the
  achieved percent, the iteration count and the strategy digest on every committed spot." What the
  committed report says, verbatim at `reports/active/latest_postflop_solve_cost.txt:525` and below:

      Aggregate over the 7 of 30 rows that reached their target; 23 excluded as cap-bound or failed.
      ... every one of the 23 exclusion lines reads "hit-iteration-cap"
      texture coverage of the pooled rows: rainbow 0, two-tone 1, monotone 6
      NOT MEASURED at this target: rainbow.

  Rainbow is 455 of the 1,755 classes and no rainbow row has ever reached 0.3%. So the phase is
  being sent to commit an artifact of which about a quarter is a texture that has never once hit the
  target the default names, and the default is silent on the choice that follows: commit the
  cap-bound cell with its floor recorded as a floor, or refuse the spot. That choice is written into
  the committed artifact and every later measurement runs against it, so it is `frozen-into-data`,
  and "take the default" currently rules it by omission. It is the same shape as
  `PER-NODE-CONVERGENCE-IS-UNMEASURED-AND-UNGATED`, which is filed against the preflop chart for
  exactly this and is open.
  The neighbouring silence is the convergence measurement. Qualification 1 calls it "the one
  measurement this phase needs that nobody has taken", and then the default proceeds without it and
  the contract asks only that the packet say so. Whether an unproven-converged strategy is committed
  at all, or whether one board is solved deep and diffed first, is a human's call and is not on the
  list in any form a human can answer.
  **Verified fixed at `f2d34c3`, and I accept the pushback on the convergence half.** The heading is
  re-cut to "Exploitability target, and what happens to a cell that never reaches it", the choice is
  stated as a choice with both costs given, and the default is to refuse rather than commit a
  cap-bound cell, on the grounds that the repo fails closed everywhere else. I agree with that
  default and with the reason, and the sentence that a floor recorded as a cost is still a cell the
  bot plays is the right way to say it. Note the reach: refusing cap-bound cells means no rainbow
  cell is committed on today's evidence, since rainbow has never reached target, so decision 4's
  default and decision 2's "the bot never faces a flop it has no cell for" are in tension until a
  rainbow solve reaches target. On reflection that is more than a consequence to state, because a
  contract criterion asserts the board-miss code is unreachable, so it is filed as blocker 13.
  On the convergence measurement: **I withdraw the ask.** The coordinator judged it belongs to the
  packet obligation rather than being a fifth choice, and having re-read decision 4 with its new
  default I agree, with one correction to where it lives. It is not decision 7's: reproducibility is
  same-input-same-output and convergence is nearness to equilibrium, and byte-identical output at
  240 iterations says nothing about the second. What actually shrank the ask is this item's own new
  default, because refusing cap-bound cells removes the case where a committed cell's exploitability
  is unknown. What remains is a cell that reached 0.3% whose frequencies may still be unsettled,
  which qualification 1 already states and the packet must carry. That is a qualification on data,
  not a fork in the road, so it does not owe an item.
- [resolved] **7. Determinism is a frozen-into-data judgment call bundled under decision 4's single Answer
  slot, and decision 4 declares settled a branch the contract still treats as live.** This is the
  item stage 1 handed to stage 2, and my answer is yes, it belongs on the list as its own call.
  Three reasons, of which the third is mechanical and decides it.
  First, the premise does not transfer. Decision 4 states "Determinism: byte-identical" and then
  "No tolerance was needed, so the phase 10 fallback of recording a tolerance in place of a
  checksum does not arise." MAINT-26 measured that for a single-spot config against a restarted
  server. The contract's own criteria say a 1,755-flop run would reach `/api/reports/*`, that the
  route is recorded UNRUN, and that "a route recorded UNRUN is not assumed to work". So determinism
  is measured for a config this phase will not commit, and "does not arise" is asserted about a run
  nobody has made.
  Second, the branch decision 4 closes is the branch the contract keeps open: "if a run is not
  byte-identical, an accuracy target and the observed maximum divergence are recorded in place of
  the digest." That is a live compliance path with no stated tolerance, no stated maximum divergence
  a human would accept, and no statement of whether a non-byte-identical solve may be committed at
  all. Stage 1 established that no gate can tell the two branches apart and that either outcome
  complies. `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES` records that and is the right
  entry for it, but an entry is not a substitute for the decision: the entry says nothing will check
  the claim, and the missing item is who chose what the claim would be.
  Third, the driver cannot see the difference. `decision_items` in `scripts/loop_stage.py` collects
  one `Answer:` per numbered heading and `unanswered_frozen` treats any non-empty value as answered.
  Decision 4's heading carries two questions, "Exploitability target, and whether the solve is
  reproducible". A human writing `0.3% of pot` in that slot discharges the reproducibility half
  mechanically, at stage 3, without ruling it, and `review_queue.py` derives the pause board from
  the same function so nothing shows as waiting. That is the failure mode
  `PRE-FILLED-ANSWER-HIDES-AN-ITEM-FROM-THE-PAUSE-BOARD` records, reached by a different route.
  Split it into decision 7, or state the tolerance policy inside decision 4's default so that
  "take the default" is a ruling rather than a gap.
  **Verified fixed at `f2d34c3`.** Decision 7 exists as its own heading with its own answer slot,
  declares `frozen-into-data`, and both halves of my finding are in it: that both determinism runs
  were a single spot, that a 1,755-flop run reaches the `REPORTS` route the notes record as unrun,
  and that a long-lived batch is the case where process state was measured at 1.6x, which is a
  sharper version of the point than mine. The escape branch is stated as a branch with no number in
  it, and the default now puts the tolerance on a human rather than an implementer, which was the
  gap. I confirmed with the parser that decisions 4 and 7 are two items with two empty answer slots,
  so the mechanical half is closed: neither can now discharge the other. Decision 4's "Determinism:
  byte-identical / no tolerance was needed / does not arise" bullet is removed rather than moved,
  with a dated pointer in its place, so the overclaim is gone from both items.

### Round 2, new at `f2d34c3`. These six hold the stage.

- [resolved] **8. Decision 11's default names a menu that was never measured on the line type decision 3's
  ruling points at, and on the committed evidence that menu does not fit the solver's arena.** This
  is the most consequential thing in this round and it is a poker and feasibility finding rather
  than a bookkeeping one. Every one of the 55 rows in `latest_postflop_solve_cost.txt` was parsed
  and grouped rather than read off the summary, and the split is total:

  | rows | line type | sizing config | arena | ever solved |
  |---|---|---|---|---|
  | 8 builds `lineA-srp-*` | single-raised pot, `starting_pot` 5.5, spr 17.7 | `config.ip/oop@2827d093808a`, the pinned menu | 21,282 to 21,715 MB against a 12,026 MB ceiling | no |
  | 8 builds + 13 solves `lineB-*pinned*` | 3-bet pot, `starting_pot` 16.0, spr 5.8 | the same pinned menu | 3,354 to 3,800 MB | yes |
  | 8 solves `*lineA*flop3375-turnriver75*` | single-raised pot | `config.ip/oop@2315abe88f71`, a reduced menu | 5,996 to 6,118 MB | yes |
  | 1 build `rung-lineA-pinnedmenu-rangefloor0.01` | single-raised pot | the pinned menu, both ranges floored at 0.01 | 10,881 MB, 90.5% of the ceiling | no |

  Read down the last column. **Every solve at the pinned menu is a 3-bet pot. Every single-raised-pot
  solve is at the reduced menu, and the record labels those rows "reduced-tree-not-cost-comparable"
  in their own names.** So "the menu MAINT-26 measured" is not one object across the two line types:
  it is the pinned menu on 3-bet pots and a reduced menu on single-raised pots, and the difference
  between them is 21.7 GB against 6.1 GB of arena and whether the line can be solved at all.
  Why this matters more than an ambiguity. A single-raised pot is the ordinary way to see a flop -
  an open and a call - so it is at the head of any corpus ranking, which is what decision 3's ruling
  says selects the lines. `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` records that GTOpen's own guard
  reads `/proc/meminfo` and cannot fire here, and the contract already requires the solve driver to
  carry its own ceiling and refuse above it. So under decision 11's default as written, plus
  decision 3's ruling, the driver refuses the most common line type. That is not a cost the item
  states; it reads as the conservative choice.
  It also undercuts the sentence the default rests on. "Every affordability figure in this phase is
  measured on it" is not quite true: of the five converged cells, `matrix-01`, `matrix-02` and
  `matrix-05` are pinned-menu 3-bet pots and `matrix-03` and `matrix-04` are reduced-menu
  single-raised pots, so the 0.3% evidence itself spans both menus. The fix is to name the config
  hash the default means, say which line types it has been solved on, and state the arena
  consequence for the ones it has not.
  **Verified fixed at `408b2c3`, and the repair goes past what I asked for.** Decision 11 no longer
  defaults. It states that "the menu MAINT-26 measured" is not one object, that the pinned menu in a
  single-raised pot was never attempted rather than slow, that an arena over a box's RAM fails
  rather than slows, and - the part I had not asked for, which turns a detail into a ruling - that
  this collides with decision 3, already ruled, because a single-raised pot is the ordinary way to
  see a flop. Four choices are given, each with the evidence it rests on, and the struck default is
  recorded with the reason it was wrong: "that reasoning was sound and its premise was false". The
  closing note that a rainbow single-raised-pot cell at the chosen menu is the one solve that would
  make this phase's arithmetic real rather than scaled is the right thing to hand a human, and it
  ties this item to decision 4's rainbow gap without collapsing them. Three defects in the new
  option set are blockers 14 through 16 below; none reopens this finding, which is closed.
- [resolved] **9. The range floor is a fifth frozen-into-data choice, it is the only measured way the pinned
  menu fits a single-raised pot, and it is on no list.** Decision 11 now cites it as "the cheap way
  to fit a wider menu rather than dropping a size", which is true and is not what it does here. The
  numbers, from the two rows that differ only in their ranges:

      lineA-srp-Kc7d2h-rainbow-dry-high    arena 21,663.4 MB   hands 1,131 v 679   action nodes 2,347,996
      rung-lineA-pinnedmenu-rangefloor0.01 arena 10,881.1 MB   hands   360 v 559   action nodes 2,347,996

  The floor is what takes a single-raised pot at the pinned menu from 1.80x the arena ceiling to
  0.905x of it. It buys that by removing 68% of the out-of-position range, 1,131 combos down to 360,
  and 18% of the in-position range. In a single-raised pot the out-of-position seat is the defender,
  and the tail of a defending range is exactly what decides whether hero's flop bet gets called - so
  this is a poker choice about the strategy that gets committed, not a memory tactic. The ranges a
  cell was solved against are frozen into that cell.
  The contract governs only *how* a floor is applied: "Any range flooring is class-level. One
  suit-specific weight anywhere in either range collapses the isomorphism group to the identity."
  Nothing anywhere rules whether to floor, or at what level, or whether a floored solve may be
  committed as the answer for a spot whose real ranges are wider. It owes its own item with its own
  default, and 0.01 should be in that default as a number rather than inherited from a MAINT-26
  label.
  **Verified fixed at `408b2c3`.** Decision 12 exists, declares `frozen-into-data`, and carries
  every number I checked it against: 21,663 to 10,881 MB with `action_nodes` identical at 2,347,996,
  3,726 to 2,385 MB on the 3-bet line, 1,131 to 360 out of position and 679 to 559 in position, and
  the 68% figure named as a truncation of the defending range. The poker sentence is the one that
  matters and it is stated plainly: hero's committed strategy would be solved against an opponent
  who has folded two thirds of what he would really hold, and whether that moves hero's flop
  strategy is unmeasured. The class-level rule is kept as a constraint rather than offered as a
  choice, which is right. The item also catches something I did not: `docs/GTOPEN_SOLVER_NOTES.md`
  at 117 argues the 2.0x is "close to free" because "two thirds of the grid sits below a 1% weight,
  far under the resolution of a 0.3%-of-pot target", and that compares a range weight to an
  exploitability target with no conversion between them. I read the line and the quotation is exact.
  Citing `A-QUANTISATION-BUDGET-IS-COMPARED-ACROSS-UNITS` rather than re-deriving the error is the
  right move. Two residues are non-blockers below: the truncation figures are single-raised-pot only
  and the 3-bet line truncates the other seat, and I would give this item a fail-closed default.
- [resolved] **10. Decision 8's default produces keys that a contract criterion forbids, and one clause fixes
  it.** The preflop key is built at `src/poker_training_bot/solver_artifacts/spot_key.py:323` as
  `f"t{table_size}/d{stack_depth_bb}/{hero_position}/"` plus the line, giving
  `t6/d100/CO/BTN:raise@2.5`. `src/poker_training_bot/data_pipeline/self_play_reference.py:57`
  recovers keys with `token.startswith("t") and token.count("/") >= 3`. A postflop key that carries
  the preflop key verbatim therefore starts with `t` and holds at least three slashes, so that
  reader returns it. The contract's own criterion is the opposite: "**A postflop key must not be
  returned by that reader**, and a test asserts the returned set contains no postflop key while the
  reader still finds every preflop one and still raises on an empty inventory." So the default, read
  literally, makes a criterion of the same phase unsatisfiable without editing the reader. The fix
  is small - one clause saying the postflop key does not begin with `t`, or otherwise cannot match
  that predicate - and it belongs in the default rather than in the implementer's lap, because the
  discriminator is part of the grammar this item rules. Worth noting the shape: this is the first
  defect in the new items that comes from a default being *specific enough to check*, which is an
  argument for the defaults rather than against them.
  **Verified fixed at `408b2c3`.** The default now reads "carry the preflop spot key verbatim, sizes
  included, **inside a postflop key that does not begin with `t`**", the reader's actual predicate
  is spelled out beneath it, and the omission is recorded rather than quietly patched. The contract
  criterion carries the matching clause: "Decision 8's default is what makes this satisfiable: a
  postflop key carries the preflop key verbatim but does not begin with `t`." That is the better
  half of the fix, because it means a later ruling that changes the prefix cannot leave the criterion
  stranded without somebody noticing the sentence that names it.
- [resolved] **11. Decision 8's default does not say whether the price substitution is committed or computed,
  and that is the whole of its class.** The default: "record the price substitution on the postflop
  spot the way `ChartHit.price_substitutions` records it preflop". `price_substitutions` is a field
  on the lookup result in `src/poker_training_bot/solver_artifacts/lookup.py`, declared at 121 and
  171 and populated at 400, 409 and 416 from the substitutions the lookup computed. It is a
  query-time record on the hit, and nothing preflop writes it into an artifact. "Record it on the
  postflop spot" reads the other way, as a field in the committed data. The two are different
  places with different reversibility, and in a `frozen-into-data` item the difference is precisely
  what a human is being asked to rule: a substitution recorded at query time can be changed by an
  edit, and one written into every committed cell cannot. As written, "take the default" does not
  say which was ruled. One clause.
  **Verified fixed at `408b2c3`.** Decision 8 now says the substitution is "recorded on the
  committed spot, not computed at query time", says why the ambiguity mattered in a frozen item, and
  gives the substantive reason rather than only picking a side: the substitution is a fact about
  which ranges the spot was solved against, settled when the solve is committed rather than when a
  hand is played. That reason is better than mine, and it is the reason a human can check.
- [resolved] **12. The node count decision 6's frontier is stated in is not the count the ruled defaults
  produce, and the phrase that put it there is mine.** Decision 6 now reads "the contract's own
  count of a flop - hero acts, villain answers, hero faces a bet or a raise, so three nodes -
  actually sits", and 3x2 and 2x3 are the frontier's highlighted cases. I wrote that phrase in round
  1's blocker 4 and it was an over-read. The contract sentence it comes from is making a point about
  needing within-street history, not counting nodes, and under decision 11's own ruled menu the
  count is not three. Walking the pinned menu, check plus two bet sizes with `max_raises: 2`, hero's
  flop decision nodes for one seat are the root, facing a 33% bet, facing a 75% bet, facing a raise
  after his own 33% bet, facing a raise after his own 75% bet, and the second-raise branches the
  `max_raises: 2` allows - about five before the re-raises and more with them.
  The consequence runs against the reader's intuition and against my own finding. At about five
  units for a complete flop for one seat, a 6.13-unit budget buys **one** preflop line at full flop
  depth, not the two that 3x2 suggests. So the frontier is arithmetically right and reads roomier
  than the ruled defaults allow, and the case I complained was missing turns out not to be a
  complete flop. The fix is to derive the node count from decisions 9 and 11 rather than from a
  sentence in the Scope paragraph, and to say that a complete flop for one seat is about five units
  at the ruled menu. That also makes the three new key items and decision 11 visibly load-bearing on
  decision 6, which they are and which nothing currently says.
  **Verified fixed at `408b2c3`, and my finding is recorded as mine.** Decision 6 now says an
  earlier draft called three "the contract's own count of a flop", that it was a reviewer's hedged
  phrase quoted back as a flat assertion, that it is an under-count at about five nodes under the
  pinned menu, and that six units therefore buys one preflop line at full flop depth rather than the
  two 3x2 suggests. The closing sentence, that the frontier is arithmetically right and reads
  roomier than the ruled defaults allow, is exactly the residue that needed saying. One editing
  residue is blocker 17 below: the phrase survives in the sentence immediately above its own
  correction.
- [resolved] **13. Decision 4's new default makes a contract criterion unsatisfiable, and the criterion is one
  the contract calls vacuous by construction.** The criterion: "**An uncovered preflop line refuses
  with a code that names the line**, and an uncovered board cannot occur, because decision 2 keeps
  all 1,755 classes. A test asserts the board-miss code is unreachable and labels it vacuous
  wherever it is reported, never counted as a check that passed." Decision 4's default is now to
  refuse rather than commit a cell that hit the iteration cap. Rainbow is 455 of the 1,755 classes
  and has never reached 0.3% on any measured row; the pooled texture line reads "rainbow 0". So if
  the phase runs and rainbow again caps out, 455 boards have no cell, the board-miss code fires, and
  the test asserting it unreachable fails - at stage 6, against a test frozen at stage 5, in a phase
  whose contract may not then be edited.
  I am not claiming rainbow will cap out; the phase runs its own solves and may push iterations
  further than MAINT-26 did. The defect is that the criterion asserts unreachability as a fact about
  the committed set, and after this fix it is a *consequence* of decision 4's answer plus an
  unmeasured solve outcome. The two documents now disagree about whether a board can be uncovered.
  Either the criterion becomes conditional and says which answer to decision 4 makes it vacuous, or
  decision 4's default says what happens to a texture that caps out across the board rather than to
  a cell, because "refuse the spot" and "refuse 26% of the artifact" are not the same ruling and
  only the first is what the default sounds like. This is the mirror of blocker 10: a good new
  default colliding with an existing criterion, found only by reading them together.
  **Verified fixed at `408b2c3`.** The criterion no longer asserts that an uncovered board cannot
  occur. It now says whether one can follows from decision 4, that the board-miss code is therefore
  live, and that it is "labelled vacuous only if decision 4 makes it so". That closes the
  stage-5-freeze-then-stage-6-failure path, and it does it by making the criterion conditional on the
  ruling rather than by weakening what it requires, which is the right of the two repairs. The
  preflop-line half of the criterion is untouched and still names the line, which it should.

### Round 3, filed at `408b2c3`. Three fixed at `39e6074`; blocker 17 is not fixed and holds.

- [resolved] **14. The converged-row count in decision 11 is eight and six; it is seven and five, and the
  report says so on its own summary line.** The item reads "of the eight rows that reached 0.3% of
  pot, six are `starting_pot: 16.0`". I re-derived it from the file rather than from the summary, by
  parsing all 55 `Row data:` lines, taking the 30 whose `group` is `solve`, and subtracting the 23
  the report's own exclusion list names:

      solve rows                    30
      excluded, all "hit-iteration-cap"   23
      reached target                 7   -> five at starting_pot 16.0, two at 5.5

  The seven are `matrix-01`, `matrix-02` and `matrix-05` at pot 16.0, `matrix-03` and `matrix-04` at
  pot 5.5, and the two determinism repeats at pot 16.0. Line 525 of the same report states it
  outright: "Aggregate over the 7 of 30 rows that reached their target; 23 excluded as cap-bound or
  failed." The likely cause is the row whose `group` is `determinism` rather than `solve`: it is at
  pot 16.0, and it is the comparison *between* the two repeats already counted, so counting it makes
  eight and six from seven and five.
  This is a blocker rather than a tidiness note for the same reason blocker 1 of the stage-1 review
  was: the split between the two menus is the entire evidence a human is handed to rule a defaultless
  `frozen-into-data` item, and this figure contradicts a line printed in the file it was derived
  from. The conclusion is untouched and is if anything slightly stronger at five and two than at six
  and two. My own note said "five converged cells" from the matrix rows and "seven" from the
  report's line, and both are right; neither is eight.
  **Verified fixed at `39e6074`.** The paragraph now reads "of the **7 of 30** `group: solve` rows
  that reached 0.3% of pot, **five** are `starting_pot: 16.0`", names the cause - the one
  `group: determinism` row, itself the comparison between two repeats already counted - and cites
  the report's own aggregate line. I re-derived the seven and the five once more from the file rather
  than checking the sentence against my own earlier count, and they hold. Recording the cause rather
  than only the number is what stops the next reader re-introducing it, which is the part that
  matters, since the `group` field is the only thing that distinguishes the eighth row from a solve.
- [resolved] **15. Option 2's evidence is one-sided in exactly the way the struck default's was, and option 3
  is the only option whose halves are both measured.** The four options rest on which configuration
  converged where, so I tabulated that rather than reading the labels:

  | configuration | 3-bet pot, pot 16.0 | single-raised pot, pot 5.5 |
  |---|---|---|
  | pinned menu `config.ip@2827d093808a` | 5 converged rows | never solved, tree 1.8x the arena ceiling |
  | reduced menu `config.ip@2315abe88f71` | **no row of any kind** | 2 converged rows |

  Option 1 is the pinned menu everywhere and the item discloses its gap. Option 2 is "the reduced
  menu everywhere", and no 3-bet row in the record uses the reduced config at all - not a solve, not
  a build. So option 2 has an unmeasured half of exactly the shape option 1's disclosed gap has, and
  the item does not say so; it says only that the reduced rows are marked not cost-comparable. A
  human comparing 1 against 2 is comparing a disclosed gap with an undisclosed one.
  The same table shows option 3 in a different light than the item gives it. "A menu per line type,
  pinned for 3-bet pots and reduced for single-raised" is precisely the pair of configurations that
  actually converged, so it is the only option with no unmeasured half. The item says "each half
  rests on evidence" and then gives it a cost no other option is given - an unrecorded seam between
  two abstraction levels - which is a real cost and is the only sentence in the list that reads as an
  argument against. Whether that is the right ruling is Taylor's; whether the reader can see that
  option 3 is the fully-evidenced one is this item's job and right now they cannot.
  Decision 12 inherits the same gap in one line: its options are "no floor and accept decision 11
  option 1 or 2, or a floor at a level a human sets". Option 3 also needs no floor, since the pinned
  menu fits a 3-bet pot unfloored at 3,726 MB and the reduced menu fits a single-raised pot at 6,103
  MB, so the no-floor branch covers three of decision 11's four options and names two.
  **Verified fixed at `39e6074`, with one caveat filed as blocker 18.** Option 2 now discloses the
  mirror gap in its own words: "no 3-bet row in the record uses the reduced config at all, not a
  solve and not a build, so this option is unmeasured on exactly the half option 1 is measured on."
  I re-checked that against the rows and it is exact. Option 3 is relabelled as the only option with
  no unmeasured half, with the cross-tab stated, and its seam cost is kept but explicitly separated
  from an evidence gap - "a cell's strategy is coarser or finer depending on the preflop line and no
  field says which" is a better statement of that cost than the one it replaced, because it says
  what a reader of the artifact would be unable to tell. Decision 12's no-floor branch now names
  which of decision 11's options it covers, all three, and which it does not. The relabelling of
  option 3 is where the correction went one step too far, which is blocker 18.
- [resolved] **16. Option 4's feasibility is a build measurement stated as a solve, which is the thing this
  contract has a rule about.** The option reads "Floor the ranges so the pinned menu fits a
  single-raised pot. The one measured route to having both." What is measured is that the tree
  *builds* inside the arena: `rung-lineA-pinnedmenu-rangefloor0.01` has `group: build`, and there is
  no solve row anywhere in the record at the pinned menu with a floored range, so nothing has been
  solved to any target on that configuration. Two things follow that the option should carry. The
  margin is 10,881 MB against a 12,026 MB ceiling, 90.5%, and the solve rows in the same report post
  peak resident memory from 3,951 to 10,865 MB separately from the arena, so "fits" is established
  for the tree and not for the run. And the contract's own criterion says it in general terms: "**A
  route recorded UNRUN is not assumed to work.**" Option 4 is the option a reader gravitates to
  because it is the only one that promises both halves, so it is the one whose evidence label has to
  be exact. Call it a build measurement, give the margin, and say no solve has been attempted on it.
  **Verified fixed at `39e6074`.** Option 4 now opens "**This is a build, not a solve.**", names
  `rung-lineA-pinnedmenu-rangefloor0.01` as a `group: build` row, states that no solve row anywhere
  uses the pinned menu with a floored range "so nothing here says the solve converges or what it
  costs", turns the contract's own UNRUN criterion against it, gives the margin as 90.5% of the
  ceiling, and names peak resident memory as a separate axis above the arena. It also carries the
  reason the label has to be exact, which is that it is the option a reader gravitates to. That is
  every part of the finding and one part I did not ask for.
- [resolved] **17. The phrase decision 6 strikes survives in the sentence immediately above its own
  correction.** Fixed on the second attempt, at `a58d7cf`. Third instance in this file of the pattern
  `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT` records, and a two-word fix. The
  text now reads, in order: "the example set skipped the middle of the frontier, where 3x2 and 2x3
  both land at 0.979x and where **the contract's own count of a flop** - hero acts, villain answers,
  hero faces a bet or a raise - actually sits. An earlier draft called three 'the contract's own
  count of a flop'. That was a reviewer's hedged phrase quoted back as a flat assertion, and it is an
  under-count." So the current draft uses the phrase and then says an earlier draft used it. A reader
  going top to bottom meets the claim as live before meeting the correction, which is the exact
  failure mode of the entry above, and the sentence is also now self-contradictory about which draft
  said what. Replace the phrase in the first sentence with what the contract actually does - it
  illustrates a flop rather than counting one - and the paragraph reads correctly in one pass.
  **Not fixed at `39e6074`, and the paragraph is now worse rather than better.** The edit changed
  the second sentence and left the first, which is the one the finding was about. It now reads, in
  order: "where **the contract's own count of a flop** - hero acts, villain answers, hero faces a bet
  or a raise - actually sits. An earlier draft called that count three, **quoting a reviewer's
  reading of the contract as though the contract stated it**." So the current draft attributes the
  reading to the contract in one clause and, in the next, says that attributing it to the contract
  was the defect. Before this edit the two sentences disagreed about a number; now they disagree
  about whether the contract says the thing at all, which is the substance. The repair is still in
  the first sentence: it is the phrase "the contract's own count of a flop" that has to go, and
  nothing in the second sentence needed touching. This is the fourth instance in this file of the
  pattern where a dated correction attaches to the sentence the fixer was looking at rather than to
  the claim.
  **Verified fixed at `a58d7cf`, in the right sentence this time.** The first sentence now ends at
  "both land at 0.979x." and the phrase is gone from it. The correction below reads that a draft
  "put a flop's decision count at three there and attributed it to the contract, which neither
  states nor implies it", which is the accurate statement and is stronger than the two-word swap I
  proposed, because it says what the contract does not do rather than only removing the claim that
  it did.

### Round 4, filed at `39e6074`. All three fixed at `a58d7cf`.

- [resolved] **18. Option 3's new label is true on one axis and reads as an absolute, and the same item
  contradicts it fifteen lines later.** This is the question put to me and the answer is yes, the
  steering moved rather than went - though not in the direction feared. Option 3 now carries "**This
  is the only option with no unmeasured half**". On line type that is exactly right and I verified
  it. On texture it is not, and no option on the list survives that axis:

  | converged row | pot | config | board texture |
  |---|---|---|---|
  | matrix-01 | 16.0 | pinned | monotone |
  | matrix-02 | 16.0 | pinned | monotone |
  | matrix-05 | 16.0 | pinned | two-tone |
  | determinism run 1 and run 2 | 16.0 | pinned | monotone |
  | matrix-03 | 5.5 | reduced | monotone |
  | matrix-04 | 5.5 | reduced | monotone |

  Six monotone, one two-tone, **no rainbow anywhere**, which is the report's own pooled line
  "rainbow 0, two-tone 1, monotone 6". Option 3's two halves are 9c8c7c and Kc7c2c on one side and
  9c8c7c and Kc7c2c on the other: monotone both times. So "no unmeasured half" holds for the split
  the item is about and a reader will take it for "measured", which is what makes it a thumb. The
  item's own closing sentence says the opposite fifteen lines below - that a rainbow single-raised-pot
  cell at the chosen menu is the one solve that would make this phase's arithmetic real rather than
  scaled - so the item asserts both that option 3 has no unmeasured half and that no option has a
  rainbow cell.
  Why this is a thumb and not merely imprecision: options 1 and 2 share the texture gap exactly, so
  naming it only against option 3's absence of a line-type gap gives option 3 a clean bill the other
  two cannot earn on any axis. The fix keeps the finding and drops the absolute: "the only option
  measured on both line types", plus one clause saying rainbow is unmeasured in every half of every
  option and is 455 of the 1,755 classes. That is the same sentence doing the same work with its
  scope stated, and it is the form blocker 15 was asking for.
  **Verified fixed at `a58d7cf`, in my words and with the struck absolute kept.** Option 3 now reads
  "the only option measured on both line types", says the earlier line "is a clean bill no option can
  earn", and carries the texture clause in bold: rainbow unmeasured in every half of every option,
  six monotone and one two-tone across the seven converged rows, the report's own "rainbow 0,
  two-tone 1, monotone 6", option 3's halves both `9c8c7c` and `Kc7c2c`, and 455 of 1,755 classes at
  the expensive end. Keeping the struck phrase quoted is the right choice here rather than the defect
  blocker 17 was about, because what is struck is a label on an option a human is about to rule and
  a reader should see that the sheet once carried it.
- [resolved] **19. The coupling decision 11 asserts to decision 6 does not discriminate between decision 11's
  own options, and the sentence that asserts it is mine.** Decision 11 says "the menu is also
  decision 6's silent input, since every row of that budget is priced at two or three actions and
  the step is worth 1.5x", and decision 11 closes by requiring that "the cost model is re-measured
  before decision 6 is answered rather than after". Both trace to my round-1 blocker 2. Neither
  holds between the four options as labelled. The reduced config's own name is
  `flop3375-turnriver75`: its flop sizes are 33 and 75, exactly the pinned menu's, `max_raises` is 2
  in both, and the tree difference is below the flop, 2,347,996 action nodes against 750,792 at the
  same pot and raise cap. This phase commits the flop only. So hero's committed flop node carries
  the same three actions whichever of options 1, 2 or 3 is chosen, decision 6's 3-action rows are
  the right rows either way, and the byte budget does not move on this ruling at all.
  What does move is solve cost in hours and the quality of the committed flop strategy, since a flop
  solved against a coarser turn and river is a different strategy. Those are real and they are not
  the byte budget, and decision 11's "the cost model is re-measured" reads as the budget because
  decision 6 is the only cost model the two items share. Say which: the hour figures are re-measured,
  the byte budget is not.
  One thing I could not settle and it is the fact the coupling would rest on. The report refers to
  its sizing configs by hash and does not expand them, so I confirmed the flop sizes from the row
  labels rather than from the config bodies. If `config.ip@2315abe88f71` also changes a flop raise
  size or a donk size, the coupling is partly real and the item should name which size differs.
  Either way one clause is owed, and this is the fourth sentence of mine this phase to need
  narrowing after it was adopted, which is the entry filed at `408b2c3` doing exactly what it
  predicts.
  **Verified fixed at `a58d7cf`; the caveat I could not close is closed against the tree.** The
  report does expand its configs, in an interned appendix I had not found; I read it rather than
  taking the summary. `config.ip@2315abe88f71` is
  `[{bet: "33 75", donk: "", raise: "2.5x"}, {bet: "75", ...}, {bet: "75", ...}]` and
  `config.ip@2827d093808a` is `33 75` on all three streets, with `config.oop` identical in both
  cases. So the flop entry matches on bet sizes, on the empty donk and on the 2.5x raise, and the
  two configs differ only at turn and river. I also checked the claim about which menus appear
  where, independently: across all 55 rows only `2827d093808a` and `2315abe88f71` appear on any
  `group: solve` row - 18 and 12 of them - and all four other sizing configs appear on build rows
  only, one row each. The item now states the coupling as struck rather than silently dropping it,
  and says outright that decision 6's byte budget does not move on this ruling.
  The new paragraph that replaces it raises one thing of its own, which is round 5's blocker 22, and
  option 2 still carries the struck claim, which is blocker 21.
- [resolved] **20. Decision 6's new Default line says "the three levers" and the next clause says "The six
  levers".** In one sentence pair: "the three levers trade reviewability, coverage and repo weight
  against each other, and there is no fail-closed option among them, because every one of them still
  commits data. The six levers, stated without a recommendation because the cost of each falls in a
  different place:". The substance is right - I checked all six and every one of them does commit
  data, so there is genuinely no fail-closed option among them, which is the reasoning I asked for
  and it is correct. Only the numeral is wrong, and it is a one-character fix.
  It is here as a blocker rather than a note for one reason, stated plainly because the alternative
  is worse. The standard I applied at blockers 14 and 17 was that a claim contradicted inside its own
  document holds the stage. This is a count contradicted by the next clause of the same sentence, and
  it sits in a line I asked for. Applying a softer standard to a sentence written at my own request
  is the non-independence the entry filed at `408b2c3` describes, so it gets the same standard as the
  others. It is the fifth count in this phase that did not survive a re-derivation.
  **Verified fixed at `a58d7cf`.** The line reads "the six levers" and the substance is unchanged.

### Round 5, new at `a58d7cf`. These two hold the stage.

- **21. Option 2 still says decision 6's budget would be re-derived on it, which the paragraph added
  in the same commit denies.** The new preamble ends "**decision 6's byte budget does not move on
  this ruling.**" Option 2, twenty lines below and untouched, still reads: "Its rows are also marked
  not cost-comparable, so **decision 6's budget** and every hour figure would be re-derived on it".
  Both sentences are about the same ruling and they say opposite things, and the option is the half a
  human reads when choosing. This is the fifth instance in this file of the pattern
  `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT` records, and the third time the
  correction has landed in an item's preamble while the option that repeats the claim went
  untouched - blocker 3's option 2, blocker 17's first sentence, and now this. The fix is to delete
  two words: "every hour figure would be re-derived on it" is true and is what remains.
  Worth naming the shape rather than only the instance, because it has now happened often enough in
  one document to be predictable. Every one of these items has a preamble that argues and a numbered
  list that decides, the corrections keep arriving in the preamble, and the list is what a ruling is
  taken off. A fix to an item with a numbered list is not finished until the list has been re-read
  against it.
- **22. The new poker cost is right, and the item states its sign as if it were measured when
  nothing in the record can measure it - though one cheap solve could.** Taking the claim first,
  because it was put to me to check hard: **it holds.** Hero's flop strategy in a CFR solve is the
  fixed point of regrets over the values of his flop actions, and each of those values is obtained
  by walking the subtree below it. Restricting the turn and river to one size changes those subtree
  values, so it changes the flop regrets, so it changes the flop strategy. There is no mechanism by
  which a flop-only artifact could be insulated from the continuation menu short of the two subtrees
  happening to have equal values, which they do not. So "the same flop, solved above a coarser tree,
  is a different flop strategy" is correct as stated, and it is a genuine cost that decision 6
  cannot price. I would not weaken that sentence.
  What is not established is the part option 2 asserts: "a narrower betting tree is a coarser
  strategy **in the spots that matter most**". That the strategy differs is certain; that it is
  *worse*, and by how much, and in which spots, is unmeasured. I have no number and this repo's own
  rule is that a poker claim needs one, so the honest form is that the flop strategy above the
  reduced tree differs by an unmeasured amount in an unmeasured direction.
  And the record cannot settle it, which is worth stating because the obvious comparison looks
  available and is not. The nearest pair is `matrix-01` against `matrix-03`, both on `9c8c7c`, and
  they differ in the menu, the pot (16.0 against 5.5), the effective stack (92.5 against 97.5), both
  ranges and the stack-to-pot ratio. Four axes move at once, so nothing in the committed 55 rows
  isolates the menu.
  The experiment that would isolate it is one solve, and it is a solve this item already needs for
  another reason: **the reduced config on a 3-bet pot, at `9c8c7c` or `Kc7c2c`, diffed against
  `matrix-01` or `matrix-02`.** Board, pot, stack and both ranges are then fixed and only the turn
  and river sizes move. It is affordable on the evidence already in the record: same ranges as the
  pinned 3-bet rows, strictly fewer nodes than their 1,073,702, and those converged at 220 to 260
  iterations inside a 3,726 MB arena, so a strictly smaller tree with identical hands cannot need
  more. And it closes option 2's disclosed evidence gap at the same time, since no 3-bet row uses
  the reduced config at all. One solve, two holes, and far cheaper than the rainbow single-raised-pot
  cell decision 11's closing note asks for, which needs either 21.7 GB or decision 12's floor. That
  belongs in the item as the measurement path rather than in this note.

## Non-blocker

### The six classes, tested one at a time

Every class was tested against the `docs/LOOP.md` definition rather than against the item's own
gloss: `frozen-into-data` means the choice is written into a committed artifact or fixture that
later phases are measured against; `runtime-reversible` means it only changes behaviour at query
time, so a later edit can change it.

| # | class | verdict | why |
|---|---|---|---|
| 1 | frozen-into-data | right | Depth decides which spots exist in the committed tree, and git keeps every version of a committed artifact, which option 3 states in its own cost line. Committing turns cannot be undone by deleting them. |
| 2 | frozen-into-data | right | The ruled half is the committed flop set, which is data. The abstraction half is a query-time rule, and it needs a human for a different reason - see below. |
| 3 | frozen-into-data | right | The covered set of lines is committed explicitly by the contract's own criterion, and a refusal names a line from it. |
| 4 | frozen-into-data | right | The target, the iteration count and the digest are recorded per committed spot. Defects are in the default, blockers 6 and 7, not the class. |
| 5 | runtime-reversible | right | Reasoning below. |
| 6 | frozen-into-data | right | It decides the artifact's encoding and coverage, both written into every cell. Defects are in the option set and the ask, blockers 3 to 5. |

- **Decision 5 is genuinely reversible, and the flag is what makes that true.** The question put to
  me was whether the reported firing frequency freezes it. It does not, on the definition. The
  figure lands in `reports/active/latest_postflop_betting_report.txt`, which is regenerated every
  gate run, and `verification/loop_policy.yml` applies exactly that distinction to phase 07 in its
  own words: "Outputs are generated reports, not committed fixtures." Nothing is measured against a
  regenerated report, no committed cell records the rule, the equity is computed from the query at
  query time, and the whole behaviour is behind a flag, so a later edit changes it with no data to
  re-derive. Two residues that do not move the class. The audit packet is committed and permanent
  and, per `AGENTS.md`, stays exactly as written, so a firing rate printed there outlives every
  qualification beside it - that is a provenance risk, covered in Alignment, not a reclassification.
  And the flag's default state is nowhere stated, in the item or the contract, so a reader cannot
  tell whether the reported rate describes shipped behaviour or an experiment that is off. The
  report should print the flag state and the denominator beside the rate.
- **Decision 2's abstraction half would be runtime-reversible on the letter of the rule, and it
  still needs a human.** Mapping an unsolved `K72r` onto a solved `Q83r` happens at lookup; nothing
  is committed by it and a later edit removes it. What forces the stop is that `AGENTS.md` forbids
  heuristic guessing for a missing chart spot, so adopting it is a boundary amendment. The class is
  right for the item as a whole because the ruled half is the committed flop set, but the stated
  reason under-describes why the other half could never have proceeded on a default. The two-class
  scheme has no word for it, which is `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`.
- **Decisions 1 and 3 rest better on permanence than on measurement.** The item text justifies the
  class with "written into a committed artifact that every later measurement then runs against",
  and decision 3's own body proves coverage growth is additive and verified:
  `PreflopChartLibrary.__init__` takes a sequence of artifacts, the lookup fails closed, so an added
  artifact strictly adds capability. If growth is additive then a too-narrow choice is cheap to fix
  later. What is not cheap either way is a too-wide one, because the bytes stay in git forever, and
  which cells exist is what the phase's own report measures. Both are still frozen; the reason worth
  keeping is the second one.
- **The encoding table omits fields the contract makes mandatory, and it omits them from every
  row.** Its stated scope is "Hero strategy only, storing only the free weights". The contract
  requires, per committed spot, the achieved exploitability as a percent of pot, the iteration
  count, and the strategy digest, plus the key itself. At 1,755 classes per line per node, six
  node-line units is 10,530 spots; at 36 bytes for a raw 32-byte digest and two small numbers, up to
  about 130 bytes in JSON with key names, that is 0.4 MB to 1.4 MB, or 2 to 9 percent of headroom.
  It moves every row in the table, including option 4's 0.49x and 0.82x, and it is enough to decide
  the 0.979x cases either way. Nobody's affordability figure currently includes it. This cuts in
  both directions, which is why it is here rather than above: it makes the middle of the frontier
  worse and option 4 slightly worse too, so the conclusion survives, by an argument the document
  does not make.
- **A second frozen test is inverted by this phase and the contract says exactly one is.**
  Regression expectations: "Exactly one frozen test asserts the thing this phase inverts:
  `test_rejects_a_bet_because_preflop_has_no_bet`". But
  `tests/test_table_state.py:195`, `test_the_decision_audit_schema_version_moved_because_the_payload_did`,
  asserts `DECISION_AUDIT_SCHEMA_VERSION == 3`, and the contract requires the version to rise from
  3. `tests/test_table_state.py` is in `verification/freeze.lock`. Stage 1's numbers note reached
  "exactly 1 frozen test must change" from a scan for `StrategyQuery`, `preflop_actions` and
  `SeatAction`, which this assertion does not name, so both stage-1 reviews could miss it by
  construction. It is a contract-accuracy defect rather than a decision defect, and the reason it is
  worth raising now is timing: Forbidden shortcuts say "Do not change this contract during
  implementation mode", so `contract-update` at this stage is the last window in which it is a
  normal edit rather than its own task.
- **The decision-audit schema bump is correctly absent from the list.** Testing the candidate put to
  me: no committed file carries a decision-audit record. The only `schema_version` values under
  `data/**` belong to the preflop artifacts and the sample fixtures, and no file there carries
  `min_raise_target` or the audit payload. The version is consumed by `simulator/run.py` and three
  report generators, all of which regenerate. So bumping rather than adding a parallel record type
  changes code and generated output, which is `runtime-reversible`; had it been listed the loop would
  have proceeded on its default anyway, so its absence costs nothing. Its one frozen consequence is
  the frozen test above.
- **The file's numbering runs 1, 2, 3, 4, 6, 5.** `decision_items` reads file order and does not
  care, and the two open frozen items sitting adjacent is the helpful arrangement, so this is
  cosmetic. Worth one line only because the fleet board and stage 3 refer to these by number and a
  reader looking for 5 after 4 finds a 130-line item instead.
- **Rake-free is inherited rather than ruled here, and the phase should say so.** Every MAINT-26 row
  posts `rake_pct: 0.0` and `rake_cap: 0.0`, matching the repo's standing rake-free stance from
  phase 10. I am not claiming a defect and I have no measurement of what rake does to a flop
  continuation threshold, which is what a claim would need. What is worth one sentence in the packet
  is that this is the first phase whose committed data plays out the streets where rake is actually
  taken, so "rake-free" stops being a preflop convention and becomes a property of the strategy the
  bot plays.
- **Six items for the phase that commits the larger artifact.** Phase 14 ruled 30 decisions to
  commit one preflop chart of 249 spots; phase 16 carries six for thousands of postflop cells. The
  ratio is not itself a defect and item count is not a quality measure. It is worth stating because
  blockers 1, 2, 6 and 7 are four items that a list of this phase's size would be expected to carry
  and does not, and because the three ruled on 2026-08-19 were ruled against a premise the file has
  since had to correct four times.

### Round 2, from the fix at `f2d34c3`

**The five new items' classes, tested the same way.** Decision 4 keeps its class and is unchanged in
kind. The other four are new and all four are right.

| # | class | verdict | why |
|---|---|---|---|
| 7 | frozen-into-data | right | The digest, or the tolerance and divergence that replace it, are recorded on committed spots and are what the repo then believes about the data. |
| 8 | frozen-into-data | right | The key's grammar is what every committed cell is addressed by; changing what it can express re-derives all of them. Two defects in its default, blockers 10 and 11. |
| 9 | frozen-into-data | right | Same, and it additionally ties the committed keys to decision 11's menu, which is the coupling blocker 12 is about. |
| 10 | frozen-into-data | right | Marginal but correctly called: the default puts pot and stack in the payload rather than the key, and a payload field on a committed spot is still committed. Had the default been "recompute at query time" this would have been runtime-reversible, and the item is right not to rely on that. |
| 11 | frozen-into-data | right | The menu is the action vocabulary of every committed cell and of the tree the solve ran on. It is also the clearest case in the whole list, because it cannot be changed without re-solving. |

- **The number of asks at stage 3 is seven, not eight.** The handoff message says the answer
  brackets are empty for "all eight frozen items". Ten items declare `frozen-into-data`, three of
  them are answered, so `unanswered_frozen` returns seven: decisions 4, 6, 7, 8, 9, 10 and 11. I
  ran the driver's own function to get that rather than counting headings. Worth one line because
  seven is what stage 3 prints and what `review_queue.py` shows a human, so an eight in a handoff
  is the kind of figure that gets quoted into a packet.
- **My round-1 note on the item ordering is closed, and a formatting nit replaced it.** The file now
  runs 1 through 11 in order, and decision 5 sits before 6 rather than after it. One line has no
  blank before it: `Answer:` at line 253 is immediately followed by `## 6.` at 254. ATX headings
  interrupt paragraphs in CommonMark and `decision_items` reads it correctly, which I checked, so
  nothing is broken. It is one blank line.
- **The provenance range in decision 6's budget is computed to five units, not to the six the budget
  states.** "At 24 to 120 bytes a spot that is 0.3% to 6.7% of the headroom depending on the line
  count." At 1,755 spots per unit and 15,774,195 bytes of headroom I get 0.27% at one unit and 24
  bytes, 6.68% at five units and 120 bytes, and **8.01% at six units and 120 bytes**. So the range
  is right for one to five units and the top of the stated budget is 8%, not 6.7%. It is a small
  understatement of the item's own point, which is that the provenance is "small, real, and not
  zero", so it is worth a digit rather than a round.
- **The ExecPlan still pre-empts decision 6's option 6.** Its expected scope declares
  `data/artifacts/postflop/**` at stage 6 as "the committed data the phase exists to write and the
  one path no lane opens on its own judgment". Option 6 is keeping the solves outside
  `data/artifacts`, so a ruling for it would need that scope line changed. Not urgent, since the
  scope entry is gated on stage 3 having answered decisions 4 and 6 in the first place, and a scope
  line is a normal edit rather than a frozen one. Worth adding "or wherever decision 6 rules the
  solves live" so the two documents do not have to be reconciled after the ruling.
- **The suspicion I checked hardest and did not confirm, recorded so nobody re-raises it.** I
  expected decision 11's "21.7 GB against 3.7 GB" to be a confounded comparison across two menus,
  because the two line groups carry different `menu_sha256` values. They do not differ in menu. Both
  groups declare `config.ip@2827d093808a` and `config.oop@2827d093808a`, and the `menu_sha256`
  differs only because the root sizes are echoed in chips against starting pots of 5.5 and 16.0. The
  comparison is at one sizing config and the difference is the line, as the item says. The confound
  worth naming instead is that the two lines also differ in stack-to-pot ratio, 17.7 against 5.8,
  which is part of why the tree is bigger.

### Round 3, from the fix at `408b2c3`

**The question put to me: has removing the steering twice left the absence of defaults doing the
steering instead? My answer is no for two of the three and yes for one, and the one is decision 12.**
Taking them separately, because "three defaultless items" is not one phenomenon.

Decision 6's is right and I said so at blocker 5. Six levers whose costs land in different places,
with an explicit statement that a pick is not an answer and a pick plus a product is, is a question
a human has to answer cold. Decision 11's is right and is the clearest case in the list: the item
had a default, its premise turned out false, and there is now no conservative choice to fall back
to, because each candidate menu is unmeasured on half the coverage decision 3 ruled. A default there
would be inventing a poker judgment the evidence does not support, and the item says exactly that
about its own struck default, which is the record stage 3 wants.

Decision 12 is different in a way that matters. There is a fail-closed option, it is the status quo,
and it requires no action to be safe: **no floor.** The repo's convention is to fail closed, decision
4's own new default invokes that convention by name, and no floor is the choice that commits nothing
and forecloses nothing except decision 11's option 4. So I would default decision 12 to no floor and
make the floored route the human's opt-in, with the truncation stated beside it as the item already
does. Offering no default when a fail-closed one exists is where an absence starts doing work: a
reader can reasonably take "none, deliberately" as "the coordinator has no view", when the repo's own
convention supplies one and the item's own evidence points at it. This is a recommendation on the
item's form and not a defect in its content, which is why it is here and not above.

One general note on the form, since two of the three are now written as "Default: **none,
deliberately.**" and one is not. That phrasing is better than omitting the line, because it
distinguishes a deliberate absence from a forgotten one and `check_decisions` cannot tell them apart
- it never reads the default at all. Decision 6 has no `Default:` line of any kind. Give it the same
sentence, so all three read as choices rather than as one choice and two omissions.

- **Decision 12's truncation figures are single-raised-pot only, and the 3-bet line truncates the
  other seat.** The item gives 1,131 to 360 out of position and 679 to 559 in position, which are the
  `lineA` numbers. On `lineB` the floor at the same 0.01 takes the in-position range from 475 combos
  to 253 and the out-of-position range from 239 to 198, so the heavier cut lands on the in-position
  seat and the "68% truncation of the defending range" framing does not carry across. That matters
  because decision 11's option 1 is 3-bet pots only, so a human weighing option 1 together with a
  floor is reading the wrong line's figures. Both pairs, labelled by line, is four numbers.
- **The blocker-12 correction introduced one very long line.** The sentence beginning "The frontier
  below is arithmetically right" runs on into "And 'the only option that fits' is false by this
  table:" on a single source line. Nothing checks line length in this directory - `check_file_sizes`
  caps `reports/phase_audits/*.md` at 500 lines and that glob does not reach the `decisions/`
  subdirectory at all - so this is readability only, and it sits in the paragraph blocker 17 asks to
  be re-cut anyway.
- **The item counts in the handoff are right this time, and I checked them rather than accepting
  them.** Twelve items, eleven `frozen-into-data`, one `runtime-reversible`, eight unanswered frozen:
  decisions 4, 6, 7, 8, 9, 10, 11 and 12. Recorded because the previous round's count was off by one
  and because eight is what stage 3 will print.

### Round 4, from the fix at `39e6074`

- **Decision 12's default is now no floor and the reasoning is stated as mine, which is correct and
  worth one caution.** The item says there is a fail-closed option here unlike decisions 6 and 11,
  that it is the status quo, that solving the ranges as the export gives them requires no action to
  be safe, and that decision 4's own default invokes that convention by name. Every clause is right.
  The added coverage sentence checks out too: no floor covers decision 11's options 1, 2 and 3, and
  each is affordable unfloored on the half it is measured on - the pinned menu at a 3-bet pot is
  3,726 MB and the reduced menu at a single-raised pot is 6,103 MB, both under the 12,026 MB ceiling
  - and it does not cover option 4. The caution: "affordable on the half of the coverage each is
  measured on" is doing load-bearing work in that sentence, because the reduced menu at a 3-bet pot
  has never been built and so has no arena figure at all. The hedge is there and it is easy to read
  past; making it a clause of its own would cost nothing.
- **Decision 6's default line now exists, and I asked for it, so its reasoning deserves scrutiny
  rather than thanks.** "There is no fail-closed option among them, because every one of them still
  commits data" is the right test and it gives the right answer for all six levers. Note what it
  implies and the item does not say: the nearest thing decision 6 has to a fail-closed option is
  option 5 driven to its limit, a flop subset small enough to fit with everything else refused, and
  that is fail-closed in the refusal sense while still committing data. So the sentence is true as
  written and a reader could reasonably ask why option 5 is not the conservative branch. One clause
  distinguishing "commits no data" from "refuses rather than guesses" would close that, and it is
  the distinction decision 2 already turns on.
- **My round-3 note on the over-long line is unchanged and stays a note.** The sentence beginning
  "The frontier below is arithmetically right" still runs into "And 'the only option that fits' is
  false by this table:" on one source line, inside the paragraph blocker 17 still asks to be re-cut.
  Nothing checks line length in this directory.

### Round 5, from the fix at `a58d7cf`

- **The blocker-17 paragraph now says the same thing twice, which is cosmetic and I am not asking
  for a round over it.** The corrected sentence ends "the phrase was a reviewer's reading quoted
  back as the document's own", and the next sentence still opens "That was a reviewer's hedged
  phrase quoted back as a flat assertion". Both are true and one is redundant. Recorded only so the
  next reader does not take the repetition for two separate corrections; fold it in whenever the
  paragraph is next touched for another reason.
- **The interned appendix is worth knowing about beyond this blocker, and my not finding it cost a
  round.** `latest_postflop_solve_cost.txt` refers to machines, solvers, menus, ranges and sizing
  configs by hash in every row and expands all of them in an `Appendix data:` block at the end. I
  searched for the `menu@` and `config.ip@` hashes and found only the row references, concluded the
  refs were unexpanded, and said so in round 3's method as a limit on what I had checked. The refs
  are expanded; my search stopped at the first occurrence pattern. Two consequences worth carrying:
  the report is more self-contained than I credited, and a reviewer's stated limit is not evidence
  the thing is missing - which is the same lesson as the note in memory about inferring absence from
  silence, arriving from the other direction.
- **What the two configs actually differ by, recorded because it is the useful fact underneath
  blocker 19 and nothing else in the tree states it in one place.** Both configs give both seats
  `bet: "33 75"`, `donk: ""`, `raise: "2.5x"` on the flop. The pinned config keeps `33 75` on turn
  and river; the reduced one drops to `75` on both. That is the entire difference between them, and
  it produces 2,347,996 action nodes against 750,792 at the same pot and raise cap. So the phrase
  "reduced menu" means reduced *after the flop*, and a reader who takes it for a narrower flop menu
  will draw the wrong conclusion about decision 6 - which is what I did for four rounds.

## Alignment

Long-term drift this stage cannot fix. Each carries an ID.

- `DECISION-OPTION-SETS-MUST-BE-COMPLETE-PREDICATES` - blockers 3 and 5 are this entry's exact
  prediction arriving in a second phase. The entry was filed off phase 14 offering four families
  where the prose defined three and named a threshold for none; here the list offers four ways out
  where two more exist in a backlog entry it cites and in decision 2's own ruled fallback, and no
  option names the product the amendment needs. The entry already records that `check_decisions`
  "does not read the Options line at all", which is why nothing mechanical noticed either time.
  Existing entry; this is its second instance and the first where the omitted option was
  pre-authorised by an earlier ruling in the same file.
- `OPTION-SHEETS-SHOULD-SAY-WHICH-OPTIONS-WERE-MEASURED` - blocker 4. This entry asks every option
  to be marked measured, bounded by argument, or unexamined. Decision 6 is the case that shows why:
  option 4 carries the only feasibility verdict and it is a combination rather than an option,
  option 2's rejection rests on an argument that is wrong about the arithmetic, and option 3 is
  unexamined by construction. Existing entry; a data point, not a fix.
- `DECISION-ITEMS-STATE-WHAT-AN-OPTION-COMMITS-NOT-WHAT-IT-REMOVES` - decision 6 says what each
  option costs and not what the artifact loses. Option 4 removes every flop decision after hero's
  first, so the bot's own within-street refusal becomes the common case rather than the seam;
  option 1's aggressive row removes a reviewer's ability to read the artifact, which
  `check_file_sizes` says the cap exists to protect. Both are stated in passing and neither is
  stated as what the option takes out. Existing entry.
- `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` - decision 2's abstraction half is a fourth instance
  of the shape this entry describes: a choice that is reversible by the letter of the rule and that
  no loop should ever take on a default. The entry's own resolution reading, that a behaviour a
  contract requires a frozen test to pin is a fixture, does not cover this one, because what forces
  the stop here is a standing prohibition in `AGENTS.md` rather than a fixture. Worth adding to the
  entry when it is next touched. Existing entry.
- `PER-NODE-CONVERGENCE-IS-UNMEASURED-AND-UNGATED` - blocker 6. The entry is filed against the
  preflop chart shipping 1,801 of 7,112 cells under 1 percent arriving reach with a tree-summed gap.
  Phase 16 is the same hole with the denominator multiplied: a per-spot exploitability figure that
  is a cap-stop rather than a reach on 23 of 30 measured rows, and no rainbow row measured at target
  at all. Existing entry; phase 16 makes it worse and cannot close it.
- `A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES` - the entry that stage 1 filed for the
  determinism criterion. Answering the handed question against it directly: the entry is correct and
  it is not a substitute for the decision item blocker 7 asks for. The entry records that no gate
  can witness the claim; the missing thing is a human choosing what the claim would be when a run is
  not byte-identical. One is a check that cannot exist, the other is a ruling nobody made, and the
  first does not discharge the second. Existing entry.
- `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE` - decision 5's firing rate is the
  next candidate for this mechanism. It is a rate about an assumption, printed in a committed packet
  that `AGENTS.md` says stays exactly as written, in a phase whose own contract requires it be
  reported "rather than claiming it is correct". The qualification lives beside the number today and
  will not travel with it. Existing entry; the mitigation inside this phase's reach is the flag state
  and the denominator printed on the same line.
- `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE` - its four named answers are not decision 6's four,
  and the entry is the second thing this phase should reconcile against rather than cite. Stage 1's
  numbers note added to it that no JSON encoding is an option; what blocker 3 adds is that the
  entry's own "store solves outside data/artifacts with only derived charts inside it" never reached
  decision 6's list. Existing entry.
- `A-CONTRACT-CAN-NAME-A-FROZEN-CHOICE-NO-DECISION-ITEM-CARRIES` - **must be filed; no existing
  entry covers it.** Proposed content: `check_decisions` validates only the items a decision list
  already holds, so a judgment call that is absent is invisible to every check the loop runs, and
  the absence is invisible even when the phase's own contract names the choice as the thing it must
  get right before any data. Phase 16 is the instance twice over: the postflop spot key's grammar,
  which both the contract and decision 3 describe in the language of `frozen-into-data`, and the
  bet-size menu, which decision 4 states is the larger of the two error terms in the accuracy the
  phase publishes. This is the complement of `DECISION-OPTION-SETS-MUST-BE-COMPLETE-PREDICATES`,
  which is about an item that is present and incomplete, and of
  `PRE-FILLED-ANSWER-HIDES-AN-ITEM-FROM-THE-PAUSE-BOARD`, which is about an item present and
  pre-answered. The cheap partial mechanism, offered so this is not filed as an unbounded ask: a
  contract phrase of the form "the one thing this phase must get right" or "re-derives every
  committed cell" is greppable, and a check could require that such a sentence names a decision
  item. Cross-cite `DECISION-LIST-HAS-NO-FIXED-PLACE-FOR-A-RULING`, which is the same family from
  the recording side.
- `TWO-FROZEN-QUESTIONS-SHARE-ONE-ANSWER-SLOT` - **must be filed; no existing entry covers it.**
  Proposed content: `decision_items` in `scripts/loop_stage.py` collects one `Answer:` per numbered
  heading, and `unanswered_frozen` reads any non-empty value as answered, so a heading carrying two
  frozen questions is discharged by an answer to either. Phase 16's decision 4 is the instance:
  "Exploitability target, and whether the solve is reproducible", where the target half has a
  default and the reproducibility half has a live escape branch with no tolerance stated, and a
  human answering the first closes both in the driver's view and on `review_queue.py`'s board. This
  is the third member of one family with `PRE-FILLED-ANSWER-HIDES-AN-ITEM-FROM-THE-PAUSE-BOARD` and
  `SUPERSEDED-FROZEN-ITEM-STILL-PARSES-AS-ANSWERED`: one answer field, no third state, and no way
  for the driver to see a question the field does not represent. All three want the same fix, a
  field the driver reads that is richer than "non-empty", so they should be adopted as one rule
  rather than three.
- `A-SIZE-BUDGET-EXCLUDES-THE-PROVENANCE-THE-CONTRACT-MANDATES` - **must be filed; no existing entry
  covers it.** Proposed content: the measurement a `frozen-into-data` ruling is taken on may exclude
  fields the same contract makes mandatory, and nothing reconciles the two documents. Decision 6's
  encoding table prices hero's free strategy weights only, by its own stated scope, while the
  contract requires an achieved exploitability, an iteration count and a strategy digest on every
  committed spot plus the key that addresses it; at six node-line units that is 10,530 spots and
  roughly 0.4 to 1.4 MB, 2 to 9 percent of the headroom the ruling turns on, omitted from every row
  including the ones marked as fitting. Adjacent to
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` and distinct from it: there the
  arithmetic was checkable from the page and nothing checked it, here the arithmetic is right and the
  scope of what was priced is narrower than the obligation, which no arithmetic check can catch. The
  forward guard the contract already carries, that the generator exits non-zero on a figure that
  does not reconcile against the bytes on disk, is the right mechanism and it arrives after the
  ruling rather than before it.

### Round 2

All three IDs above were filed at `f2d34c3` with my reasoning; I confirmed each resolves to exactly
one entry in `backlog.yml`. Two more from this round.

- `A-CONTRACT-CAN-NAME-A-FROZEN-CHOICE-NO-DECISION-ITEM-CARRIES` - **third instance, in the same
  phase, found by the fix to the first two.** The range floor of blocker 9 is the same shape as the
  spot key and the bet menu: a choice written into every committed cell, load-bearing for whether
  the phase's most common line type can be solved at all, mentioned by the contract only as a
  constraint on *how* it is applied, and on no list. That it surfaced only because decision 11 cited
  it in passing is the entry's own thesis: the absent item is invisible, and what makes it visible is
  somebody writing a sentence next to it. Worth adding to the entry, because three instances in one
  phase is the strongest evidence it has, and because the partial mechanism I proposed - grep the
  contract for "re-derives every committed cell" and require a named decision item - would have
  caught the key and missed the floor. A better predicate: any solver config field the contract
  constrains but does not rule.
- `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT` - blocker 8 is this entry applied
  to a config rather than a figure. "The menu MAINT-26 measured" names a measured thing by prose,
  and the prose resolves to two different `config.ip` hashes depending on which line type you look
  at. A default that said `config.ip/oop@2827d093808a` could not have been ambiguous, and the
  ambiguity is exactly where the 21.7 GB lives. The rule the entry wants, applied here: a default
  that pins a measured configuration names it by the hash the report already prints, not by the
  campaign that produced it. Existing entry; a data point and a sharpening.
- `A-REVIEW-FINDING-IS-QUOTED-INTO-THE-RECORD-AS-IF-MEASURED` - **must be filed; no existing entry
  covers it.** Proposed content: a reviewer's argument, adopted into a decision record, arrives
  stripped of the hedging it had in the review and reads as a measurement of the repo. Twice in
  phase 16, both times mine or a sibling reviewer's. Stage 1: "a solver mixes only where it has
  driven a hand to indifference" was an idealisation whose caveat had to be added back at `1d88536`
  in a commit whose message says so. Stage 2, blocker 12: my "three nodes is the contract's own count
  of a flop" was an over-read of a sentence making a different point, and the fix quoted it as the
  contract's count and built the frontier's highlighted cases on it. Both were caught by the
  reviewer who wrote them, on a later pass, which is not a mechanism. What is owed is a convention:
  an adopted review argument is attributed to the review and carries whatever hedge the review gave
  it, so a later reader can tell a reviewer's reasoning from a measurement. Related to
  `AN-IMPORTED-FIGURE-IS-INDISTINGUISHABLE-FROM-A-MEASURED-ONE`, which is the same failure for a
  number imported from another phase's document; this is the same failure for an argument imported
  from a review of the same document. Cross-cite
  `A-CONTRACT-STATES-MEASURED-LEVELS-WITHOUT-NAMING-THE-ARTIFACT`.

### Round 3

- `A-REVIEW-FINDING-IS-QUOTED-INTO-THE-RECORD-AS-IF-MEASURED` - **filed at `408b2c3`, verified
  present once, and the diagnosis is right.** I was asked to correct it if it was wrong and I would
  not change a word of the mechanism: a reviewer writes to argue and hedges accordingly, a
  coordinator writing a fix wants a citable sentence, the hedge is the first thing to go, and the
  reviewer then reviews its own words with the qualification removed, "which is the one case where
  an independent reviewer is least independent". That last clause is the part I had not seen and it
  is the sharpest thing in the entry. Two additions when it is next touched, neither changing the
  diagnosis. First, both instances were caught only because the reviewer re-read a paragraph it had
  already argued about, so the practical mitigation is narrow and worth naming: a fix that quotes a
  review goes back to that review, and the reviewer's own sentences are the first thing it re-reads.
  Second, blocker 14 of this round is **not** an instance of this entry and should not be added to
  it - a count that fails to reconcile against a line printed in the same file is
  `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT`, and folding the two together would
  produce an entry whose remedy is "be careful", which resolves by assertion.
- `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` - blocker 14 is the second instance
  in this phase and the first where the contradicted figure is printed by a generated report rather
  than typed four lines away. That is a strengthening of the entry rather than a repetition of it:
  the eight and the six do not reconcile against "7 of 30 rows that reached their target" on line 525
  of the very file they were parsed from, and the entry's proposed remedy - render the figure from
  its inputs rather than typing it beside them - would have caught it, because a generator that
  counted converged rows would have counted seven. Worth recording that both instances were
  arithmetic a reader could do from the page, and that both were found by a reviewer doing it.
  Existing entry.
- `OPTION-SHEETS-SHOULD-SAY-WHICH-OPTIONS-WERE-MEASURED` - blockers 15 and 16 are this entry's exact
  ask, arriving in a second phase and in the same document twice in one round. The entry wants every
  option marked measured, bounded by argument, or unexamined. Decision 11 has four options of which
  one is measured on both halves (option 3), two are measured on one half each (options 1 and 2, and
  only option 1's gap is disclosed), and one is measured as a build rather than a solve (option 4)
  while being called "the one measured route". A decision list with three defaultless items is
  exactly where this entry earns its keep, because with no default the evidence labels are the whole
  of what a human is reading. Existing entry; this is the strongest instance it has and it should
  cite this round.

### Round 4

- `OPTION-SHEETS-SHOULD-SAY-WHICH-OPTIONS-WERE-MEASURED` - **recorded here as asked, against the
  existing ID, with no duplicate filed.** The instance is decision 11's option sheet across two
  rounds, and it is worth the entry's attention because it shows the failure recurring *through* its
  own fix rather than once. Round 3: option 1 measured and disclosed, option 2 measured on the
  opposite half and undisclosed, option 3 measured on both and under-credited, option 4 measured as
  a build and called measured. Round 4, after all four were relabelled: option 3's label became an
  unqualified absolute that is true on line type and false on texture, where the correct label was
  available and one word longer. What that adds to the entry is the sharper form of its own ask - an
  option's measured status is not a boolean, so a label has to name the axis it is measured on, and
  a sheet where each option is measured on a different axis is the case where an unqualified
  "measured" misleads most. The entry currently asks for three states, measured, bounded by argument,
  or unexamined; this argues for a fourth field rather than a fourth state, the axis.
- `A-DERIVED-FIGURE-IS-NOT-CHECKED-AGAINST-THE-RATE-BESIDE-IT` - blocker 20 is the third instance in
  this phase and the smallest, and the smallness is the data point: "the three levers" against "The
  six levers" in one sentence pair is the same failure as the eight-and-six with none of the
  arithmetic, so no amount of care about *derivation* would have caught it. That points at the
  entry's own remedy from a different side: the fix is not to check harder but to render counts from
  the list they count, and a decision item that says "the N levers" should have N produced by the
  same document that holds them. Five counts in this phase have now failed a re-derivation, and this
  entry and `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` are the two that own the pattern.
  Existing entry.
- `A-REVIEW-FINDING-IS-QUOTED-INTO-THE-RECORD-AS-IF-MEASURED` - blocker 19 is the entry's third
  instance and its clearest, and it arrived in the commit that filed the entry. My round-1 blocker 2
  argued the bet menu was decision 6's silent input because the budget is priced at two or three
  actions; that entered decision 11 as a flat coupling and as an obligation to re-measure the cost
  model before decision 6 is answered. It does not hold between the options actually on the list,
  because they share a flop action set and differ below the flop, which this phase does not commit.
  I did not know that when I wrote the sentence and the coordinator had no way to know it either, so
  this instance is not a hedge lost in transcription like the first two: it is a reviewer's
  *inference* adopted as a premise, which the entry does not currently cover. Worth one sentence
  when it is next touched, because the mitigation differs - a lost hedge is restored by quoting the
  review, and an adopted inference has to be tested against the thing it claims about, which nobody
  did for four rounds. Existing entry; this is a widening of it rather than a repetition.

### Round 5

- `A-REVIEW-FINDING-IS-QUOTED-INTO-THE-RECORD-AS-IF-MEASURED` - **you asked whether to add the
  lost-hedge-versus-adopted-inference distinction to the entry or leave it in my note. Add it to the
  entry.** The reason is the repo's own, quoted in stage 1 from `docs/LOOP.md`: an item without an ID
  "is a note nobody reads again". A review note is a snapshot of one stage; the entry is what a later
  phase meets. Keep it in whatever words read best there - my voice is not the value, the distinction
  is, and an entry that carries it is worth more than a note that phrases it well. What should land:
  the first two instances are a hedge lost in transcription and are repaired by quoting the review;
  the third, blocker 19, is a reviewer's *inference* adopted as a premise, and an inference is
  repaired only by testing it against the thing it claims about, which took four rounds and an
  appendix nobody had read. The mitigations differ, so an entry naming only the first will not catch
  the second.
- `OPTION-SHEETS-SHOULD-SAY-WHICH-OPTIONS-WERE-MEASURED` - **same answer: put the fourth-field point
  in the entry.** Measured status is not a boolean, so an option's label has to name the axis it is
  measured on, and a sheet where each option is measured on a different axis is where an unqualified
  "measured" misleads most. The entry's three states want a fourth field, the axis, not a fourth
  state. Round 5 adds an instance: decision 11's option 3 was relabelled correctly on line type and
  then had to be qualified again on texture, the same option labelled twice on two axes in two
  rounds. Existing entry; no duplicate wanted.
- `A-FALSIFIED-FIGURE-SURVIVES-IN-THE-DOCUMENT-THAT-FALSIFIED-IT` - blocker 21 is the fifth instance
  in this one file, and the pattern has sharpened enough to be worth adding as a rule rather than
  another example. Three of the five landed the same way: the correction went into the item's arguing
  preamble, and the numbered list below it - which is what a ruling is actually taken off - went
  untouched. Blocker 3's option 2, blocker 17's first sentence, and blocker 21's option 2 again. So
  the closure check the entry already asks for, that an ID whose fix is "correct the claim" cannot
  close while the claim's text still matches anywhere in the tree, has a cheap special case worth
  naming: when the corrected document holds a numbered option list, the list is re-read against the
  correction before the fix is called done. Existing entry.

## Method

Read-only throughout. Commands used: `git log`, `git diff`, `git show`, `git branch`, `grep`,
`sed -n`, `cat`, `head`, `wc`, `ls`, and `python3` for read-only arithmetic on the node-line
frontier. No tracked file was modified. `scripts/run_verify.py` and `scripts/check_gate_bite.py`
were not run.

Recomputed here rather than quoted: headroom 15,774,195 bytes from `20 * 1024 * 1024` minus a
5,197,325-byte tree; 2,573,584 bytes per node per line at one byte per weight over 1,286,792
hero-combo classes with two free weights, giving 6.129 affordable node-line units; the full
fitting set at that rate, which is every product of nodes and lines at or below 6 and includes
3 x 2 and 2 x 3 at 0.9789x, neither of which appears in the document; 5 x 1 and 1 x 5 both at
12,867,920 bytes and 0.8158x; the four combinations decision 6 does state, all of which reproduce;
and the 40.25x re-encoding factor. The combinatorial inputs themselves, 1,755 classes and
1,286,792, were taken from stage 1's numbers note rather than re-derived, since two reviewers
already built them independently and agreed.

Not verified: anything about whether the resulting strategy is good poker, the corpus ranking, and
every stage-1 finding marked resolved.

### Round 2, against `f2d34c3`

Reviewed as `git show f2d34c3` over the decision list, the contract and `backlog.yml`, then
re-derived rather than read. New read-only computations: all 55 `Row data:` lines in
`reports/active/latest_postflop_solve_cost.txt` parsed as JSON and grouped by `group`,
`config.starting_pot` and `config.ip`, which is what produced blockers 8 and 9 and is the one thing
in this round that could not be seen from the summary sections; `unresolved_blockers`,
`decision_items` and `unanswered_frozen` imported from `scripts/loop_stage.py` and run against both
this note and the amended decision list; the full node-line frontier rebuilt independently; the
provenance percentages at one, five and six units; and the hero-node walk of the pinned menu behind
blocker 12, which is a count off the menu rather than a measurement and is stated as such.
`spot_key.py:323` and `self_play_reference.py:57` were read directly for blocker 10, and
`lookup.py:121`, `:171` and `:400-416` for blocker 11.

Still not verified in round 2: whether rainbow reaches 0.3% at a higher iteration count, which is
what blocker 13 turns on and which no evidence in the repo settles; and the four new items' poker
merits beyond the feasibility arithmetic, since only decision 11 has an evidence base in the tree.

### Round 3, against `408b2c3`

Reviewed as `git show 408b2c3` over the decision list, the contract and `backlog.yml`. Every figure
in decisions 11 and 12 was re-derived rather than checked against my own round-2 note, which is what
found blocker 14. New read-only work: the converged set rebuilt from the 30 `group: solve` rows minus
the 23 names in the report's own exclusion list, cross-checked against its "7 of 30" summary line and
against the `group: determinism` row that explains the off-by-one; the converged-configuration
cross-tab of pot type against `config.ip` hash behind blocker 15, which is what showed that no 3-bet
row uses the reduced config at all; the `group` field of `rung-lineA-pinnedmenu-rangefloor0.01`
behind blocker 16, together with the solve rows' peak-resident range; the `lineB` floored and
unfloored hand counts for the asymmetric-truncation note; `docs/GTOPEN_SOLVER_NOTES.md:117` read
directly to confirm decision 12's quotation is exact; `check_file_sizes.py`'s globs to confirm the
`decisions/` subdirectory is uncapped; and the driver's parser run against the amended list for the
twelve-eleven-eight counts.

Still not verified in round 3: whether the reduced menu would converge on a 3-bet pot or the pinned
menu on a floored single-raised pot, which are the two holes blockers 15 and 16 are about and which
only a solve settles; and whether a 68% range truncation moves hero's flop strategy, which decision
12 states as unmeasured and which I have no way to measure here.

### Round 4, against `39e6074`

Reviewed as `git show 39e6074`. Every claim marked resolved above was re-derived from the tree rather
than compared against my own earlier note, which is the discipline that caught blocker 19, since the
sentence at issue was mine and comparing it to my own note would have confirmed it. New read-only
work: the seven converged rows re-tabulated with their board textures, cross-checked against the
report's pooled "rainbow 0, two-tone 1, monotone 6" line, which is blocker 18; `action_nodes`
tabulated by `starting_pot`, `config.ip` and `max_raises` across all 55 rows, giving 2,347,996
against 750,792 at pot 5.5 and `max_raises` 2 for the pinned and reduced configs, which is blocker
19; the unfloored arena figures for both menus against the ceiling for decision 12's new coverage
sentence; and the paragraph texts of decision 6's default and decision 6's frontier read in the file
rather than from the diff, which is what showed blocker 17 unfixed and blocker 20.

Still not verified in round 4, and it is the fact blocker 19 turns on: the bodies of
`config.ip@2827d093808a` and `config.ip@2315abe88f71`. The report names its sizing configs by hash
and does not expand them, so the flop sizes come from the row labels
(`flop3375-turnriver75` against the pinned root echo `Check | Bet 33% | Bet 75%`) rather than from
the configs themselves. A donk or raise size differing on the flop would partly restore the coupling
blocker 19 denies, which is why that blocker asks for a clause naming the size rather than asserting
there is none. **That statement was wrong and round 5 corrects it: the report does expand them.**

### Round 5, against `a58d7cf`

Reviewed as `git show a58d7cf`. The interned appendix was read directly at
`reports/active/latest_postflop_solve_cost.txt:2843-2864`, which settles the round-4 caveat and
confirms the two sizing configs match on the flop entry - `bet: "33 75"`, `donk: ""`, `raise: "2.5x"`
for both seats - and differ only at turn and river. Independently of the configs I re-tabulated
which sizing configs appear on which row groups across all 55 rows: only the two named configs
appear on any `group: solve` row, 18 and 12, and the four others appear on one `group: build` row
each, which is the claim about two-action menus being build-only.

The poker claim in the new paragraph was checked as reasoning rather than measured, because nothing
in the repo can measure it: the mechanism is that a flop action's value is obtained by walking its
own subtree, so restricting the turn and river changes the values, the regrets and therefore the
flop strategy. The nearest committed comparison, `matrix-01` against `matrix-03` on the same board,
moves the menu, the pot, the effective stack, both ranges and the stack-to-pot ratio at once, so it
isolates nothing; that confound was checked row by row rather than assumed. The single solve that
would isolate it is named in blocker 22 with the affordability argument taken from the pinned 3-bet
rows' own node count and arena.

Still not verified: the sign and size of that effect, which is the point of blocker 22; whether
rainbow reaches target at a higher iteration count; and whether a 68% range truncation moves hero's
flop strategy. All three are solves, none is a reading.

No tracked file was modified in any round. `scripts/run_verify.py` and `scripts/check_gate_bite.py`
were not run.
