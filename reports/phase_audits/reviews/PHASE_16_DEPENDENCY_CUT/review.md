# PHASE_16_DEPENDENCY_CUT - independent review

Reviewer: a read-only subagent that wrote none of this task, briefed to answer one question - was the
`15` edge genuinely free of content, and is `14` the right replacement rather than a value that
happens to satisfy the graph check - and told plainly that "you have broken the phase graph" was the
finding that mattered most. It ran the four read-only checkers and no gate command. Scope reviewed:
`git diff 9bbdcf44ce5508d19d672812fbc1b3484c32c790`.

**Verdict: the graph is not broken.** The `15` edge was free of content, and `14` is a real content
edge whose transitive closure is every phase 00 through 14. But the correction was half done, and the
diagnosis I filed named the wrong cause.

## Blocker

- **[resolved] A second copy of the claim survived, in the document whose job is to carry the graph.**
  `docs/ROADMAP.md` was not in `approved_scope` and was not touched. Its table read
  `| 16 | Postflop That Can Bet | 15 | ... |` and its diagram drew `14 -- 15 -- 16`, thirteen lines
  above its own sentence declaring "`depends_on` in the contracts is the single source for that graph".
  Nothing generates or checks that section, so the repo would have shipped a rendering contradicting
  the file it names as its source - in the document MAINT-21 designated as the graph's home and the one
  a human reads first. My scope entry had said V2_ROADMAP's line 227 "asserts the dependency this
  removes", as though it were the only such line, and that sentence is what produced the miss.
  **Fixed** under a widened scope: row corrected, diagram redrawn as three independent lanes off 14,
  phase 17 added to a table that stopped at 16, and the retracted "cannot start until a postflop source
  exists" removed. Filed as `PHASE-GRAPH-IS-WRITTEN-TWICE-AND-CHECKED-ONCE`.

- **[resolved] The recorded diagnosis named the wrong cause, and the true history is sharper.** I wrote
  that the whole basis for the edge was one roadmap sentence. It was not.
  `docs/exec_plans/completed/MAINT_PHASE_DAG.md` records that the v2 contracts were declared with
  `depends_on` as a straight chain, "sequence rather than semantics: nothing read the field, so nothing
  tested it"; the commit that wrote the edge never cites the roadmap sentence and justifies 16 with a
  claim since retracted; and MAINT-21 then re-derived the edges for 10, 11, 12, 13 and 14 from stated
  arguments while recording that "10, 12, 15 and 16 were already right" and tracing neither 15's nor
  16's. So a review did look, affirmed an edge it had not traced, and was wrong - which makes the lesson
  "an edge must carry the reason it exists" rather than "someone should check". That exec plan's own
  no-delegation exception is the illegitimate kind, about the session rather than the work, which is
  where an untraced edge comes from. **Fixed**: the backlog entry carries the real history, and the
  completed exec plan is left exactly as written, because a packet is a snapshot of what a task
  believed and this entry is the correction. Filed as
  `A-DEPENDS-ON-EDGE-INHERITED-FROM-A-CHAIN-IS-NEVER-RE-EXAMINED`.

- **[resolved] A live ruled input still named the drill.** Phase 16's decision 3 is `frozen-into-data`,
  was ruled by Taylor on 2026-08-19, and its ruled default ranks preflop lines by "how often the corpus
  and the drill actually reach them". That is the method for choosing what goes into phase 16's
  committed artifact, and phase 16's own stage 2 and 3 read that file. The drill produces no data at
  completion, so the ruling would have been inherited pointing at a source that will not exist.
  **Fixed**: annotated, not re-ruled - Taylor's answer stands, and the note records that the corpus half
  drives it, the refusal inventory being the stated precedent and already built from the corpus. Filed
  as `A-RULED-DECISION-CAN-NAME-A-SOURCE-THE-REPO-WILL-NOT-HAVE`.

## Non-blocker

- **[resolved] The reviewer supplied a better argument than mine and it is now in the record.** The
  phase 15 contract deals preflop decisions only, because that is all the chart answers. So a drill
  could not have produced evidence about what an opponent does on a river even in principle, which
  kills the roadmap sentence outright rather than merely reducing it to an optional feature.
- **[resolved] `POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK` never named phase 15 either.** Its own text says
  whether a betting opponent exists is "a Phase 07 and Phase 08 question", both completed, and the
  decision on whether it ships is `runtime-reversible` and never blocked on anyone.
- **[resolved] The ExecPlan claimed the roadmap paragraph was "marked superseded rather than
  rewritten", and I had reworded it.** The backlog entry quotes the original verbatim, so a reader
  following the quote would not have found it. The original sentence is restored and the marker sits
  beneath it.
- **Amendment size rule: compliant.** Exactly two lines plus the backlog id. The phase 16 contract is
  62 lines against a 300 cap.
- **`14` is correct and the closure is complete**, corroborated independently:
  `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` is filed against 14 and says "phase 16 consumes the
  result", and four further entries name 16 as the exit for defects in 14's committed cells. **Carry
  into 16's stage 1**: that conditioning step is still `deferred`, so the edge is met on paper while the
  specific output 16 needs from 14 does not exist yet. Recorded in the ExecPlan outcome.
- **The no-delegation exception is the legitimate kind** - about the work, one indivisible argument with
  no second file set - and it does not waive review. The reviewer noted that
  `check_execplan_delegation.py` only checks the line exists and cannot tell work from session, so its
  pass proves nothing; the `maint/29-review-machinery-reads-shape-not-content` lane already owns that.
- **Scope is clean**, `check_scope` exits 0, and everything outside the two originally approved paths is
  `standing_scope` or entered under the dated widening above.
- **Merge hazard, noted not fixed.** All eight sibling worktrees still carry `depends_on: "15"` and the
  old `docs/ROADMAP.md` row on clean committed branches. They gate nothing, because eligibility is
  measured against `main`, but a merge from one can reintroduce the edge. Integration is serial, so this
  is a thing to watch at integration rather than a defect.
- **Not taken, and named here so it is a decision rather than an oversight.** The reviewer found two
  filed falsehoods thirteen lines from the paragraph I edited - `ROADMAP-CLAIMS-NO-SOLVE-WAS-EVER-TIMED`
  and `POSTFLOP-DEPTH-RATIOS-ARE-INVERTED`, the first tagged `contract-update`, this task's own mode.
  Both stay open. They are unrelated to the dependency, and folding an unrelated correction into a task
  because the file happened to be open is how a narrow scope stops meaning anything.

## Alignment

- `PHASE-GRAPH-IS-WRITTEN-TWICE-AND-CHECKED-ONCE`
- `A-DEPENDS-ON-EDGE-INHERITED-FROM-A-CHAIN-IS-NEVER-RE-EXAMINED`
- `A-RULED-DECISION-CAN-NAME-A-SOURCE-THE-REPO-WILL-NOT-HAVE`
- `AN-AMENDMENT-TO-A-SKELETON-CONTRACT-IS-DELETED-BY-ITS-OWN-STAGE-1` - phase 16's Scope says stage 1
  replaces it, so this task's two-line amendment will be deleted by the phase's own contract stage and
  the durable record is the backlog id alone.
