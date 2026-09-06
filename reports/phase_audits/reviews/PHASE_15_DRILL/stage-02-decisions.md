# Phase 15, stage 2 (decisions) - independent review

Reviewer: a read-only subagent, a different one from stage 1's, which wrote none of this stage's work
and was briefed with the driver's own question and forbidden from running any gate command. Scope:
`git diff d2b59f409d08405977a96321f98a41b4288f2659 --
reports/phase_audits/decisions/PHASE_15_DRILL_DECISIONS.md`.

The question the loop asked: *Is every reversibility class right? A frozen-into-data call filed as
runtime-reversible proceeds on its default and is then written into a committed artifact that later
phases are measured against.*

The reviewer recomputed the measurements rather than reading them, and confirmed all but three:
4,225 of 18,431 cells with no call key across 25 spots at 80.2010 percent of arrival; families
5 / 25 / 219 at 52.6637 / 39.0915 / 8.2448; 44 zero-arrival spots; 83 spots at all 169 classes and
they are exactly the spots where hero has not yet acted; 43 spots at five classes or fewer and 18 at
one; 59.11 against 2.51 percent refusal; the 675 / 1,202 / 1,820 / 2,431 mixing ladder; 527 cells in
the unnamed band; 1,646 below full reach at a median of 1,474 with 406 at ten or less; 106 spots at
0.0164 percent; the openings 21.5649 / 27.1733 / 39.2664. The three it caught are blocker 5.

## Blocker

- **[resolved] Decision 7 was under-classified: it commits new data and was filed
  `runtime-reversible`.** Its own default commits a 358-key exclusion table that every later refusal
  is looked up against, which is the definition the file itself quotes. Its own cost line conceded
  it - "renaming one later is a migration" - and a migration is a task rather than an edit. The
  argument offered against, that deriving a refusal code is a derivation rather than a judgement,
  answers the wrong question: the class is about what gets written, not how much judgement went into
  writing it. Two live sub-choices were buried inside and on no ballot - where the table lives, and
  whether it joins the artifact schema. **Fixed**: 7 is now `frozen-into-data` with an empty answer, a
  ballot of three, and both sub-choices named.

- **[resolved] Decision 6 did not carry the number the contract requires it to carry.** The contract
  says the hand count of the committed session is pinned as data in the decision list before it is
  written. Decision 6 stated no count and none of its three options carried one, so Taylor was being
  stopped on the part the contract had already ruled - one session, six-handed, 100bb, flat depth -
  and not asked the part it left open. The size framing was also wrong in a direction that pushed the
  answer: `data/samples` holds 572 KB against a 5,242,880-byte cap, so 10.9 percent is used and
  4.67 MB is free; the corpus is most of what is there, not most of the cap. **Fixed**: the ballot is
  now the hand count, and the framing carries the real numbers.

- **[resolved] Decision 3 did not make the ruling the contract asks for.** The contract requires the
  106 unreachable spots be split by whether they publish a range hero could draw from; decision 3
  ruled them as one block and the split was not on the ballot. Measured: all 106 publish a non-empty
  range, so on the strict reading the split is empty, while on phase 14's reading 81 of the 106
  publish no hand that ever raises. **Fixed**: `split-deal-the-priced-ones-only` is on the ballot, the
  item states which reading it takes and why, and it records that 42 of the 106 have zero arrival so
  decision 2 already withholds them.

- **[resolved] Decisions 4, 5 and 10 rested on a storage property the contract did not require.**
  All three are classed `runtime-reversible` because "the session record stores the raw weights and
  the student's action, so re-scoring later is a re-render". Nothing in the contract required that.
  The Phase 02 schema records hole cards only in `showdown`, so a hand where hero folds preflop - the
  common case, and the case a threshold decides - had nowhere to record hero's hand class; and the
  committed audit was specified as "every decision the session **scored**", which cannot be re-scored
  at a lower threshold because the decisions the lower threshold admits were never written down.
  Stage 4 authors tests from the contract alone, so a requirement living only in the decision list
  would not have reached them, the freeze would land, and three classes would be retroactively wrong.
  **Fixed in the contract**, which was still editable in `contract-update` mode: the record stores per
  decision the spot key, hero's hand class, the full weight vector, the arriving reach and the
  student's action, for every decision including ungraded ones and hands that end preflop; and the
  audit covers every decision presented, each marked graded or not. Filed as
  `HAND-HISTORY-HAS-NO-PLACE-FOR-A-FOLDED-HERO-S-CARDS`.

- **[resolved] Three numbers were wrong in the section a human reads while answering five frozen
  items.** "Only three cells have a top weight under 0.50" - it is **eight**, and they are listed. The
  per-family mixing was quoted at 0.999 two lines after the file pins 0.99; at 0.99 it is **8.11 /
  2.60 / 2.30**, not 12.33 / 4.02 / 3.27, and the identical sentence was in the contract. Decision 2
  quoted the mean rarity of a three-bet spot, one in 2,656, where the **median is one in 899,346** -
  340 times rarer, and it is the number that decides the item, quoted in the direction that flattered
  the option the default rejects. **All three fixed in both documents.** Filed as
  `SPOT-RARITY-QUOTED-AS-A-MEAN`, and the threshold half folded into
  `ONE-PURE-THRESHOLD-CONSTANT-FOR-THE-WHOLE-REPO`.

- **[resolved] Decision 2's ballot was missing the shape its own contract describes.** The contract
  requires a stated minimum share per family plus arrival's order within a family; the ballot offered
  `stratified-then-arrival` as one token with the split fixed at an even three way in the default,
  while the item's own prose called that split "the part of this decision most worth a human
  overriding" and then did not put the override on the ballot. **Fixed**: the split is now the ballot,
  with two named options and an open one, and the four-fold over-weighting an even split gives the
  three-bet family is stated as the cost.

## Non-blocker

- **[resolved] Decisions 1, 8 and 10 offered options the active contract forbids, without saying so.**
  Decision 1's two EV options are barred by a criterion rather than a caution, and it is the dangerous
  one because it is frozen and Taylor answers it: `check_human_gate` accepts any non-empty answer, so
  a forbidden pick would send stage 4 building against a contract that bans it. Each of the three now
  names the conflict and says that picking it reopens stage 1. Filed as
  `DECISION-LIST-OPTIONS-CAN-CONTRADICT-THE-CONTRACT`.
- **[resolved] Decision 9 was over-classified.** Deferring the ingestion lift writes nothing, and the
  stop could not change the outcome because `AGENTS.md` forbids the lift whatever is answered. It is
  now `runtime-reversible` and answered, and the genuine ask underneath - the size bound as a number -
  is raised as a `- Paused:` line in the active ExecPlan, which `scripts/review_queue.py` reads. Filed
  as `DEFERRAL-HAS-NO-REVERSIBILITY-CLASS`.
- **[resolved] Decision 5 published every reach count except the one at the floor it picks.** It is
  **577** at or below 100 basis points; now stated.
- **[resolved] Decisions 2 and 3 collided on 42 spots** - the zero-arrival and unreachable sets
  overlap there - and neither mentioned the other. Both now say decision 2's exclusion wins.
- **[resolved] `derivation:no-legal-spot-key` has zero members** over the committed export, and
  decision 7 called it one of four live codes without saying so. The 358-key argument holds only while
  that stays true, which the item now records.
- The reviewer confirmed the parse read-only: `decision_items` finds all ten with valid classes, and
  after these fixes `unanswered_frozen` blocks on exactly 1, 2, 3, 6 and 7. The five answered items
  parse as non-empty and none blocks accidentally.
- Coordinator's own note, unchanged from stage 1 and now worse: the contract is 292 lines against a
  300-line cap after this stage's fixes took it to 297 and a compression pass pulled it back. Filed as
  `PHASE-15-CONTRACT-IS-NEAR-ITS-LINE-CAP`.

## Alignment

- `DECISION-LIST-OPTIONS-CAN-CONTRADICT-THE-CONTRACT` - `check_decisions` validates that a class
  string is present and never reads the contract, so a frozen ballot can offer a forbidden answer.
- `DEFERRAL-HAS-NO-REVERSIBILITY-CLASS` - a scope cut writes nothing, so neither class fits, and the
  two labels force an author to burn a human stop or hide the cut.
- `HAND-HISTORY-HAS-NO-PLACE-FOR-A-FOLDED-HERO-S-CARDS` - the Phase 02 schema cannot record what hero
  held in a hand that ends preflop, which is every preflop surface's problem and not only the drill's.
- `SPOT-RARITY-QUOTED-AS-A-MEAN` - mean and median per-spot arrival differ by 340x in the three-bet
  family and prose has now quoted the mean as typical once.
- `ONE-PURE-THRESHOLD-CONSTANT-FOR-THE-WHOLE-REPO` - extended rather than re-filed: both of this
  phase's documents pinned 0.99 and then quoted a 0.999 figure in the next breath, so the repair is
  that documents render the figure from an owned constant rather than repeat it by hand.
- `PHASE-15-CONTRACT-IS-NEAR-ITS-LINE-CAP` - 292 of 300 with nine stages left, each of which may
  amend, and the cap is never raised to fit an amendment.
