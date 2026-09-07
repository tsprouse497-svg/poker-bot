# ExecPlan: maint-ask-the-chart-a-hand

Lane: `maint/31-ask-the-chart-a-hand`
Worktree: `/Users/taylorsprouse/projects/poker-bot-worktrees/maint-31`
Base commit: `9bbdcf44ce5508d19d672812fbc1b3484c32c790` (main, "Merge phase 14: chart cutover")
Mode: `maintenance`. No phase is active in this lane and none is being advanced.

## Objective

Taylor asked, 2026-09-06, for a lightweight way to name a hand and a spot and be told what the bot
would do. The answer already exists in `src/poker_training_bot/solver_artifacts/lookup.py`; what does
not exist is a front door onto it. Every caller today is a report generator, so the only way to ask
one question is to write a script.

This lane adds one command:

    uv run python scripts/ask_preflop_chart.py --seat BTN --facing "CO raise 2.5" --hand AhKs

and prints the committed chart's own weights for that spot and hand, or a refusal that says why it
cannot answer. Gate: the base gate stays green. Its `pytest` command id runs `python -m pytest tests`,
which collects the new test file with no command-id registration of its own.

Explicitly not in this lane: postflop (the bot still only checks and folds after the flop - that is
phase 16), any new poker logic, and any change to what the chart says.

## Scope

Approved: `scripts/ask_preflop_chart.py`, `tests/test_ask_preflop_chart.py`,
`verification/freeze.lock`, and this plan. `verification/freeze.lock` is in scope only because adding
a test file changes it; `scripts/freeze_tests.py` regenerates it and the diff is the record.

Not approved, each for its own reason. `src/**` is out because the answer already exists in
`lookup.py` and this is a front door onto it - a change under `src/` means the design was wrong and
the lane stops rather than widens. `scripts/run_verify.py` is out because the base gate already runs
bare `pytest`, and a registered command id would need a phase contract to declare it, which a
maintenance task does not have.

Standing scope carries the task metadata and generated docs as usual.

One dependency is deliberate and worth naming, because it points the wrong way. The new test file
imports its fixture helper from `tests/test_preflop_lookup.py`, which is frozen. Reusing it beats a
fourth copy and is the direction `SOLVED-PRICE-FIXTURE-HELPER-DUPLICATED-ACROSS-TEST-FILES` wants,
but it makes an unfrozen file depend on a frozen one, so a later correction to that helper's
signature breaks this file with no signal until the gate runs.

## Delegation Plan

- Worker lanes: one implementation lane, W, owning the script and its tests end to end. The task is a
  single file over an existing library and splitting it would cost more in handoff than it buys.
- Ownership: W owns `scripts/ask_preflop_chart.py` and `tests/test_ask_preflop_chart.py`. The
  coordinator owns the freeze lock regeneration, `backlog.yml`, and every commit.
- Expected outputs: the script, the test file, a transcript of the command run against at least one
  covered spot and one refused spot, and a changed-file summary.
- Status: W planned.
- Integration order: W lands whole; the coordinator regenerates the freeze lock, runs the gate, and
  commits.
- Review handoff: an independent read-only reviewer that wrote none of it checks that the script adds
  no strategy of its own - no default action, no nearest spot, no invented price, no tie broken - that
  a refusal is passed through with `lookup.py`'s own reason code rather than reworded into something
  friendlier that loses the cause, that a price substitution is visible in the output rather than
  silently applied, and that a mixed hand class prints its full distribution rather than a single
  action picked for the reader. Findings are blocker, non-blocker, or alignment item; an alignment
  item goes to `backlog.yml`.

## Slices

- [x] S1. The script and its tests, from W. Reviewed independently: zero blockers, three non-blockers
      taken by the author.
- [x] S2. Freeze lock regenerated, full gate green including `check_gate_bite`, committed at
      `844edf2`.

## Verification

- `uv run python scripts/run_verify.py` - the full gate, unchanged by this lane.
- `uv run python scripts/ask_preflop_chart.py --help` and one covered and one refused query by hand.

## Outcome

Done. `scripts/ask_preflop_chart.py` answers one hand at one preflop spot from the committed ranges,
with 52 tests behind it and a green full gate at `844edf2`.

What it does not do, and each is deliberate rather than unfinished. It is preflop only, because that
is the only strategy this repo has - postflop is phase 16's. It names the action and not the amount
hero raises to, because sizes are a second artifact and a second failure mode, and reading them in
later is reading rather than deciding, so the door is open. And it is covered only by the base
`pytest` run, never executed end to end by the gate, which is filed as
`A-CONVENIENCE-COMMAND-HAS-NO-GATE-COMMAND-BEHIND-IT` rather than fixed by inventing a report for it
to write.

The review found no blockers. Its three taken non-blockers are in the commit message; two of them
were tests pinning a printed string rather than the property behind it, which is worth remembering
next time a test looks green.

## Next Agent Bootstrap

State: the work is done and committed at `844edf2` on `maint/31-ask-the-chart-a-hand`, on a green
full gate. The lane is not merged; that is a serial integration step against `main` like any other.

What to read before writing anything: `src/poker_training_bot/solver_artifacts/lookup.py` for
`PreflopChartLibrary`, `ChartHit` and `ChartMiss`, and
`src/poker_training_bot/solver_artifacts/chart_query.py` for `ChartQuery`. The library loads from
`data/artifacts/preflop/`.

The one rule that matters: this script asks and prints. It never decides. Every refusal the library
gives is printed as a refusal.
