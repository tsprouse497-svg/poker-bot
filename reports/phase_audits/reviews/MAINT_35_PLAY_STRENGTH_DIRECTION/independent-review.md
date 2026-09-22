# MAINT-35 independent read-only review, and what was done about it

The reviewer was a read-only agent that wrote none of the work it read and did not write this
resolution. The repairs were made by a fourth agent that wrote neither the original work nor the
review. The coordinator wrote only the two rulings that came back from Taylor, for the reason the
ExecPlan's Delegation Plan gives.

The reviewer re-derived every figure in the diff from `data/artifacts/preflop/six_max_100bb_rakefree.json`,
its sizing table, its export source card, the retired GTO Wizard source, and the reports under
`reports/active/`. It reproduced all of them except where noted below. It ran `check_scope`,
`check_contracts`, `check_repo_consistency`, `check_file_sizes`, `check_execplan_delegation`,
`run_full_quality_gate` and `--check` on the three generators, all green. It was told not to run
`run_verify.py` or anything applying `verification/mutations.yml`, because a review agent running the
gate in this repo has previously left live mutations in the working tree.

## Blocker

**B1. The exclusion census was wrong, in the one entry whose subject is how that census is read.**
`COVERAGE-IS-PUBLISHED-UNDER-THE-SOLVES-OWN-PLAY-AND-A-HUMAN-DOES-NOT-PLAY-IT` named three exclusion
buckets, called the largest "the remaining", and asserted an identity over "all four counts". There
are five buckets. The two dropped were multiway exposure and the big-blind squeeze, which are the
subject of the sibling entry filed three items earlier. The same miscount was in the ExecPlan as a
finding the task claimed to have made.

**Resolved.** The repair lane re-derived all five from the artifact's own computed notes and from the
derived chart report, which prints the arithmetic verbatim and states that five clauses can refuse a
node and all five do. The entry now names five and closes on `node_counts.exported`. The ExecPlan's
Outcome records that the count was wrong twice and that the review found it.

The lesson, recorded in the entry rather than here: a closing total is no evidence. Folding any two
buckets together still sums to the same number, so a census can be wrong about which repair returns
which spots while its total looks right.

## Non-blockers, all resolved

- **N1.** `arrival_ppb` was cited as the source of two figures when it contains only one of them. The
  field holds 53 zeros; the other figure is read off the unrounded product, and only that one means a
  spot nobody plays. Sourcing fixed in both entries, each now warning a re-deriver not to read the
  field's count as a bug.
- **N2.** The ladder entry published a raw relation count as the size of an accepted defect. The repo
  already carries a standing obligation that no packet may do this, because a large share of that
  relation is the wheel-ace premium and is correct poker. Re-derived and split. The worst case
  attached to that relation is itself a wheel-ace case, so the headline gap is not an instance of the
  defect at all, and the entry now says so.
- **N3.** A teaching-motivated refusal the task should have filed and did not: the withheld five-bet
  jams, rejected on the grounds that keeping them "ships advice a student cannot detect as wrong, in
  a training tool". Filed as a ninth entry, with the same two-legged treatment the big-blind entry
  gets: the trainee argument expired, the pricing argument stands.
- **N4.** Phase 19's non-goals did not exclude board abstraction, so the phase declared to lift
  heuristic guessing read as authorization for the one heuristic separately ruled out. Non-goal added.
- **N5.** Phase 20's non-goals carved out UI surfaces that `AGENTS.md` does not lift. Resolved in the
  contract rather than in `AGENTS.md`: the phase adds no UI package and no UI surface, its session
  runs from the CLI, and a stage that finds it cannot be driven from a terminal raises a blocker
  rather than adding a screen.
- **N6.** The hand-history boundary loosened in text while naming no phase and having no owner, since
  its owner was the phase this task retired. Fixed in place, and the scope-change entry now declares
  it as a third semantic boundary movement rather than two.
- **N7.** A backlog entry still said the UI waits on the drill, which is now the thing being deferred.
  Corrected.
- **N8.** An entry title still carried counts from the retired chart while its body had been corrected.
  Retitled, following the precedent this repo set for exactly this, with the id left alone.
- **Nit.** Two sibling entries were quoted as carrying the same sentence when only one does.

## What the review raised that the brief did not ask for

**The venue ruling narrowed the scope and never answered the reason.** The 2026-08-15 ruling kept
automation out on terms-of-service and account-risk grounds. Those attach to the platform, not to the
guest list: a private club is the same account and the same ban exposure as a public table, so
"home games only" changes who loses money to the bot rather than the risk that was named. Put to
Taylor in those words on 2026-09-21. **He ruled proceed, risk accepted.** Recorded in `AGENTS.md`,
`docs/V2_ROADMAP.md` and the phase 20 contract as an accepted risk rather than a resolved one.

**"Plays live" read two ways and the contract assumed one.** An online table the bot drives and an
in-person game it advises across are different phases. Put to Taylor the same day. He answered that
the bot is handed the game's URL, joins the table and plays, and said the question may stay open for
now. Recorded as the working reading for stage 1 to confirm, committing to no platform.

**Retiring a phase orphans rulings that name it as an input, and nothing checks for that.** The task
checked for dangling `depends_on` edges, policy entries, registered commands and backlog phases, and
all were clean. It did not check for a ruled decision that names the retired phase as a source.
Phase 16 has one, it is `frozen-into-data`, and phase 16 is the next lane to open. The pre-existing
entry that held half of this was extended rather than duplicated.

**The ladder acceptances may be priced with the wrong instrument.** The chart is overwhelmingly
all-or-nothing, so an inversion does not arrive as a frequency, it arrives as a rule the bot follows
every time. Against the fixed opponent pool a home game is, the cost of that is exploitation rather
than expected value at the node, and a head-to-head chips-per-100 figure is the measurement least
likely to see it. Phase 18's contract does promise a best-response exploitability figure, so the
instrument is being built; the entry now points at that rather than at chips.

## Alignment items, filed rather than fixed

Three, each out of this task's approved scope: the packaging metadata is the last live prose
statement of the retired purpose; a frozen test docstring names the retired phase; and the backlog's
cost language is still written for a student rather than for a table, including in the two largest
live strategy defects.

The repair lane added a fourth of its own. Nine new deferred entries now hang off phases 16 and 18
with nothing that would notice if either closes without them, which is the closeout blind spot this
repo already has a name for.

## What the reviewer got wrong

Nothing that changed a decision. Where it understated a finding it understated B1, which is worse
than it reported: the dropped bucket count was wrong and so was calling the largest bucket a
remainder.
