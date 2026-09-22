---
phase_id: "20"
title: "The Home Game"
depends_on:
  - "16"
  - "19"
required_gate_commands:
  - pytest_table_client
  - generate_table_session_report
required_reports:
  - reports/active/latest_table_session_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_20_HOME_GAME.md
---

# Phase 20: The Home Game

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Declared by MAINT-35 on 2026-09-21 from Taylor's ruling of that date: the bot sits down and plays,
and the table it sits at is one of **Taylor's own home games**. Not a public real-money table. That
bound is the whole of the permission: this is the phase at which the PokerNow-automation and
browser-or-platform-observation lines in the Boundaries section of `AGENTS.md` lift, and they lift
only for a private game Taylor names.

What "plays" means was put to Taylor on 2026-09-21, because an online table the bot drives and an
in-person game it advises across are different phases with different work in them. He answered that
the bot is handed the game's URL, joins the table and plays, and said the question may stay open for
now. So the working reading is an online table joined by link, and stage 1 confirms it rather than
inheriting it. Nothing here commits to a platform.

The terms-of-service and account-risk reasoning behind the 2026-08-15 ruling is not answered by
naming a private game, because it attaches to the platform and not to the guest list: a private club
carries the same account and the same ban exposure as a public table. That was put to Taylor in
those words on the same day and he ruled proceed, risk accepted. It is recorded here as an accepted
risk rather than a resolved one, so no stage reads the narrowing as having disposed of it.

Reading a table and acting at one are the two halves of it, and neither is poker. The decision still
comes from the committed strategy exactly as it does offline, and a hand played at a table is still
reproducible from a record afterwards. A seat this phase adds that could take an action the offline
strategy would not have taken is a defect in this phase, not a feature of it.

It depends on 16 and 19 because a bot that folds every flop, or refuses a spot with money already in,
should not sit anywhere at all. The order is the point: play well, then play somewhere.

Phase 20 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not play a public real-money table, a ring game the house runs, or any table Taylor has not
  named as his own home game. The lifted boundary is that narrow and a stage may not widen it.
- Do not let observation become a second strategy. What is read from the table becomes a query
  against the committed strategy; a table-side rule that changes an action is out of scope.
- Do not add runtime solver calls or LLM-backed poker decisions. Runtime poker decisions never rely
  on model reasoning and this phase does not become the exception.
- Do not add a UI package, and do not add a UI surface of any size. The `No UI package` boundary in
  `AGENTS.md` names no phase-20 exception and this phase does not become one. The session is started,
  watched and stopped from the CLI, and what it did is read from the committed session report, the
  same as every other entry point in this repo. That is checked against what this phase actually
  needs rather than assumed: reading a table, acting at one, and recording the session are a client,
  a strategy query and a report, none of which is a screen. If a stage finds that it genuinely cannot
  be driven from a terminal, that is a blocker to raise with Taylor and a boundary move to rule on,
  not a surface to add here.
- Do not add large hand-history ingestion. Reading a session this bot played is not that.
- Do not let the bot act unattended beyond whatever Taylor has explicitly permitted, and do not infer
  that permission from silence.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_table_session_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_table_client`
- `generate_table_session_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- A plain statement of which game the bot may sit in, what it may do there without being asked, and
  how a human stops it.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not change this contract during implementation mode.
- Do not test against a live table in place of a deterministic harness, and do not treat a hand that
  happened to go well at a real table as evidence the seat is correct.
- Do not guess at a table state the observer could not read. An unreadable table is a refusal to act,
  the same way an uncovered spot is.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
- Every hand the bot plays at a table is recorded in the normalized schema and re-derives through the
  replayer, the same as a simulated one.
