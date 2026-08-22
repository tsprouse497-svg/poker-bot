# Contract update: spawning a subagent is always permitted

Task: `delegation-rule-update`. Mode: `contract-update`. Base: `12469b1`.

## Objective

Taylor ruled on 2026-08-22 that creating a subagent is always fine - not necessary, but always
acceptable. Four process documents state the opposite premise as a condition on their rules.

Both rules lose that condition. Delegation of implementation stays a default and keeps an
exception, now required to be about the work rather than about the session. Independent review
loses its exception entirely: the independent review of this task found that every exception
wording on offer could be satisfied by the party the rule exists to constrain, so the honest form
is that the agent who wrote something is never the only one who judges it.

That is narrower than this plan set out to write, and the reasoning is under `## Independent
review` rather than here, because it was not the author's call.

## Why this is contract-update and not maintenance

`AGENTS.md` is the single source for behaviour rules and this changes what those rules require.
`AGENTS.md` steps 6, 9 and 10, `docs/DEFINITION_OF_DONE.md`'s three delegation bullets, the
fourth known gap in `docs/LOOP.md`, and the Delegation Plan wording in
`docs/exec_plans/TEMPLATE.md` are all semantic, so the mode is `contract-update` and no
implementation rides along with it.

## The premise being retired

It was never a capability limit. The standing session instruction is not to call the Agent tool
unless asked, which is an opt-in nobody had opted into, and it was recorded as a fact about the
environment in about twenty ExecPlans and audit packets across phases 05 to 12 in four different
wordings - "disabled", "switched off", "unavailable", "instructed not to spawn subagents".

The cost is visible in the filesystem rather than argued. Phases 00 to 04 have no
`reports/phase_audits/reviews/` directory at all, phases 05 to 09 have one note each, and phases
10 to 12 have nine or ten each - every one of them written by the agent whose work it judged.
Phase 13 is the control: its stage 8 ran two independent readers, one mechanical and one on the
poker, and an adversarial verifier caught a blocker fix that was guarded only by a report
validator no canary covered, so reverting both left all 45 gate commands green while the report
published a false seat.

`MAINT-25`'s own no-delegation exception is the sentence this task retires, which is a fair
measure of how settled the false premise had become.

## Scope

Approved: `AGENTS.md`, `docs/DEFINITION_OF_DONE.md`, `docs/LOOP.md`,
`docs/exec_plans/TEMPLATE.md`.

Standing: `CURRENT_TASK.yml`, `backlog.yml`, `docs/BACKLOG.md`, `STATUS.md`,
`docs/exec_plans/**`, `reports/active/**`.

`TEMPLATE.md` is approved explicitly rather than left to ride `docs/exec_plans/**`. It is
neither task metadata nor a generated output, and this task adds a rule to it.

Deliberately untouched: `scripts/check_execplan_delegation.py` and `tests/**`. The checker's
`PLACEHOLDER_VALUES` still carries the template's former wording as a literal, and
`tests/test_execplan_delegation.py` still pins the retired sentence as a valid exception. Both
are implementation, the test is frozen, and both are filed.

Also deliberately untouched: every completed ExecPlan and audit packet carrying the old claim.
A packet is a snapshot of what a phase believed, and rewriting one destroys the only evidence
that a premise ever changed. The phase 12 review notes saying "coordinator-written self-review
under `AGENTS.md` step 10" are now the evidence the new wording rests on.

## Delegation Plan

- Worker lanes: none. One reviewer lane, read-only.
- Ownership: coordinator owns all four document edits; they are four coupled sentences across
  four files and splitting them across lanes would cost more in integration than it saves.
- Expected outputs: a read-only review note answering whether the new wording says what Taylor
  ruled, and whether it leaves a hole the old wording did not have.
- Status: build completed, reviewed, three blockers fixed, findings recorded below.
- Integration order: no lanes to integrate. Reviewer reads the committed working tree.
- Review handoff: the reviewer inspects the four document diffs, the two backlog entries flipped
  to `done`, and the new backlog entry, against `check_execplan_delegation.py` as it stands.
- No-delegation exception: the *implementation* is coordinator-owned because it is four sentences
  of coupled wording in four files, which is below the size where a lane pays for itself. This is
  a reason about the work, which is the form the rule this task writes now requires. The review
  is delegated, because a task whose whole subject is "the author must not be the only judge"
  cannot be the one that judges itself.

## Slices

- [x] Slice 1: `AGENTS.md` - steps 6, 9 and 10 lose the availability condition, and a new
  `## Subagents` section states the permission, the limit of the permission, and the correction.
- [x] Slice 2: `docs/DEFINITION_OF_DONE.md` - the three delegation bullets restated.
- [x] Slice 3: `docs/LOOP.md` - the fourth known gap rewritten from a fact about the loop into a
  choice the loop now has, with what remains after separate agents named.
- [x] Slice 4: `docs/exec_plans/TEMPLATE.md` - the placeholder line reworded onto the `state `
  prefix its sibling fields already use, and the review exemption closed in the same place.
- [x] Slice 5: `DELEGATION-EXCEPTION-IS-NEVER-CHECKED` filed; two phase 12 entries closed by
  `dd52b5b` flipped from `deferred` to `done` with their closing evidence.
- [x] Slice 6: independent read-only review, `docs/BACKLOG.md` regenerated, full gate.

## Verification

`uv run python scripts/run_verify.py` - the full derived gate, no new command ids and no
behaviour change, so nothing in `reports/active/` may move apart from the gate's own records and
`docs/BACKLOG.md`.

## Independent review

Reviewer: read-only subagent, no write access, which authored none of the wording and read the
diff, the checker, the frozen tests, and the two commits the backlog flips rest on.

Three blockers, all upheld and all fixed before the gate.

- **Blocker 1 [resolved].** The first draft of step 10 replaced an escape gated on an external
  fact with one gated on the author's own judgement - "why that work did not warrant a separate
  reader" - which is always assertable and never falsifiable. Since the ruling makes the old
  condition permanently false, the old sentence read against the ruling left no route to
  self-review at all, so the draft *widened* the hole the task exists to close, in the one step
  that decides whether a review happens. Step 10 now says a coordinator pass over its own work
  never stands in for a review, and `docs/DEFINITION_OF_DONE.md` says the same.
- **Blocker 2 [resolved].** `AGENTS.md` contradicted itself: the new section said a review stage
  may be answered by the coordinator while step 9 was a flat imperative with no exception. The
  section now separates the two - "permitted is not required" applies to implementation, and
  review carries no exemption - and step 9 names the requirement that was implicit: the reviewer
  must not be whoever wrote the work.
- **Blocker 3 [resolved].** This plan recorded the review as completed while the reviewer was
  still running and this section was a single line. That is the defect class the task exists to
  correct, appearing in the task's own plan.

Two non-blockers, both fixed rather than deferred.

- "No session is without them" asserted a capability fact about every future session, and then
  forbade recording an accurate observation if one ever lacks the tool - the same error class as
  the premise being retired, pointed the other way. The wording now carries only the normative
  half, and says a session that genuinely cannot spawn one has a blocker rather than an
  exception.
- The stated reason for leaving the template line alone was false. `is_placeholder_value` also
  matches the `list ` and `state ` prefixes, which five of the six sibling fields in that file
  already use, so the line could be reworded safely and now is. The false claim is corrected in
  `CURRENT_TASK.yml` and the backlog entry rather than quietly dropped.

One finding this task cannot fix, folded into `DELEGATION-EXCEPTION-IS-NEVER-CHECKED`:
`tests/test_execplan_delegation.py:45` asserts that "subagent spawning is unavailable in this
session." is a valid concrete exception. It is live, gate-run and frozen, so `AGENTS.md` now says
that sentence does not qualify while a frozen test says the machinery accepts it. `tests/**` is
outside this task's scope and the file is frozen; naming it in the entry means the follow-on task
knows before it starts that its fix needs a re-freeze.

The reviewer also verified the two backlog flips against the commits rather than against this
plan's description of them, including the detail that `6f6ba49` later moved the squeeze test to a
different file, which makes `git log` on the current path look like a contradiction and is not.

### Second round: a generalisation offered, and refused

Blocker 1 looked like it generalised - the failure was an exception gated on the author's own
judgement rather than on an external fact - so a falsifiability test was added to the
implementation exception and sent back to the same reviewer rather than shipped. It came back a
blocker and the clause is gone.

Three reasons, and the first is the one that settles it. The retired excuse was *perfectly*
falsifiable: "subagent delegation is switched off in this operator's sessions" names something
anyone could check by trying, and it was false for twelve phases. Falsifiability did not save
anyone, because nobody checked. The clause that actually excludes it is the one already there and
already reviewed - a statement about the session rather than about the work does not qualify.

Second, it banned the plan it shipped with. This plan's own exception rests on "below the size
where a lane pays for itself", which is a claim about a lane that was never opened, so no state of
the world contradicts it. Most honest reasons not to open a lane are economic claims about a
counterfactual, and economics about a counterfactual is never falsifiable.

Third, the asymmetry already in the section is the whole fix. On the implementation side the
independent review still runs over the result, so "this should have been a lane" is precisely a
finding a reviewer can make, and an author's judgement there is contestable by construction. It
was only on the review side that the author's judgement removed its own reviewer.

Filed rather than lost: `AGENTS.md`'s own pattern for a judgement is a class declared from a fixed
vocabulary that a second reader can contest - blocker, non-blocker, alignment;
`frozen-into-data`, `runtime-reversible` - and a closed set of exception classes is the shape a
future tightening should take. That went into `DELEGATION-EXCEPTION-IS-NEVER-CHECKED` alongside
the observation that "concrete" in step 4 and "not a placeholder string" in the checker are
already two different bars for one line.

## Outcome

Four documents restated, one backlog entry filed, two closed. No source, no tests, no fixtures,
no committed reports beyond the gate's own records and `docs/BACKLOG.md`.

The rule that came out is narrower than the one that went in, in both directions. Delegation of
implementation stays a default with a work-shaped exception; independent review becomes a
requirement with no exception at all, because the review found that every exception wording it
was offered could be satisfied by the party the rule exists to constrain. And the one
generalisation this task tried to draw from that finding was refused by the same reviewer,
because it would have banned honest exceptions while still admitting the dishonest one the task
exists to retire.

Every committed report regenerated byte-identical across the gate; only `reports/active/
verify_results.json` moved, which is the gate's own timing record. That is the evidence that no
behaviour changed.

## Next Agent Bootstrap

Repo is on `main` in `~/projects/poker-bot-worktrees/main`, idle after this task closes.
Phase 13 is live in `~/projects/poker-bot-worktrees/phase-13` at stage 9 and picks this change up
on its next merge from `main`; its lane confirmed none of these files are in its approved scope.

The obvious follow-on is `DELEGATION-EXCEPTION-IS-NEVER-CHECKED`, which is implementation and
wants its own task: teach `check_execplan_delegation.py` to reject an exception claiming
unavailability, and take the template's wording out of the checker's literal placeholder set.
Until that lands, the rule written here is enforced by reading and nothing else.
