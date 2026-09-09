# Stage 2 review, phase 16: the judgment-call list and its reversibility classes

Independent read-only review. I did not write the contract, the ExecPlan, or the decision list, and
I edited none of them. Reviewed in the `phase-16` worktree at `4d06494`, branch
`phase/16-postflop-that-can-bet`, pointer `verification/loop_runs/16.yml` at stage 2 with
`stage_base: 1d88536`. Stage 2's own diff against that base changes only the ExecPlan's expected
scope and the pointer, so the document under review is the decision list as stage 1 left it.

Stage 1's two notes were read in full and are not re-reviewed. Every blocker in both is marked
resolved and I re-checked none of them.

The stage's question: is every reversibility class right? A `frozen-into-data` call filed as
`runtime-reversible` proceeds on its default and is then written into committed data with nobody
asked.

**The headline: all six classes are right, and I could not break any of them.** The defects are
elsewhere in the same stage's obligation. Two choices this phase's own contract calls the things it
must get right before any data are frozen-into-data and appear on no list at all. Decision 6's
option set is not the exhaustive set it claims, it carries a feasibility verdict on exactly one
option that is false by its own table, and no ruling on it produces the three things the contract
says its answer supplies. Decision 4's default is silent on the outcome 23 of the 30 measured solve
rows actually had.

## Blocker

Seven findings. None is marked resolved; the coordinator fixes and then asks me to verify. Nested
bullets are absent at every depth in this section on purpose, per
`REVIEW-QUEUE-COUNTS-EVIDENCE-BULLETS-AS-BLOCKERS`; supporting detail is prose, tables, or indented
plain text.

- **1. The postflop spot key's grammar is the phase's largest frozen-into-data choice and it is on
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
- **2. The bet-size menu is frozen into every committed cell, decision 4 says it dominates the
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
- **3. Decision 6 asserts an exhaustive option set and omits two options, one of which decision 2's
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
- **4. Decision 6 steers to option 4, and the sentence that does it is false by decision 6's own
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
- **5. No answer to decision 6, under any of its four options, produces the three things the
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
- **6. Decision 4's default names a target that 23 of the 30 measured rows missed, and it does not
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
- **7. Determinism is a frozen-into-data judgment call bundled under decision 4's single Answer
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

Not verified: anything about whether the resulting strategy is good poker, the solve cost model
beyond the seven-of-thirty and rainbow lines quoted, the corpus ranking, and every stage-1 finding
marked resolved.
