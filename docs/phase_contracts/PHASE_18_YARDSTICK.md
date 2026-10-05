---
phase_id: "18"
title: "The Yardstick"
depends_on:
  - "14"
required_gate_commands:
  - pytest_playing_strength
  - generate_playing_strength_report
required_reports:
  - reports/active/latest_playing_strength_report.txt
  - reports/active/latest_verify.txt
required_phase_audit: reports/phase_audits/PHASE_18_YARDSTICK.md
---

# Phase 18: The Yardstick

## Scope
**Skeleton.** This contract carries boilerplate acceptance criteria and nothing phase-specific yet.
The command IDs and reports above are placeholders from the proposal, not commitments; stage 1 of the
loop replaces this section and the criteria below in `contract-update` mode, and `check_contracts.py`
fails the gate for any active phase whose criteria say only what a generic phase would.

Declared by MAINT-35 on 2026-09-21, when Taylor ruled that the goal of this repo is a bot that plays
strong poker. Nothing here measures how well it plays, and the repo says so itself: the committed
`reports/active/latest_profile_comparison_report.txt` reports its one directional figure against five
copies of a check-fold strategy and then states, in its own words, "Producing the other kind of number
needs an opponent with a strategy, and this repo does not have one yet." Every other strength-shaped
figure in the repo is agreement with a chart or distance from a reference range, which is fidelity to a
source rather than money won.

Taylor narrowed it on 2026-10-05: the solve is taken as good play, as phase 14's decision 51 already
takes the preflop export and his 2026-09-26 ruling to trust the solve takes the flop. So this phase
measures one thing: what it costs, in chips per 100 hands with error bars, wherever the bot does not
play what the solve says. The coordinator's list of those places today, a reading and not a ruling:

- Spots the chart refuses, among them decision 51's withheld four-bet family and the multiway spots
  it refuses. A refusal on any street voids the hand in the simulator, so no chips move, and how a
  refusal is priced is stage 1's to draft; phase 19's "no better than refusing" waits on the same
  answer.
- Postflop, the check-fold fallback, the flop bettor refusing every turn, and a faced bet outside
  every menu bucket, which refuses rather than snapping to the nearer size (phase 16's decision 14).
- Prices the tree does not hold, answered from the solved price for every raise in the sequence (the
  v2 roadmap's ruling 8, extended 2026-08-20), and postflop only inside phase 16's decision 10 band.
- The chart's own merge of a cold call into the raise (phase 14's decision 45), which is the chart departing
  from the solve rather than the solve's play.

Once phase 19 lands the list includes every rule-of-thumb answer, which is why 19 waits on this.

Anything whose result could only be read as the solve being wrong is out: no exploitability figure
for the solve or for the bot's whole strategy, which would charge the solve's own gap, its
convergence and its simplified postflop model, to the bot; no opponent built to find the solve's
leaks; no comparison with reference ranges or with real players. The skeleton's opponent pool and
exploitability figure are dropped on that ground.

The lean, not a ruling, is that the solve is the opponent too: the bot against seats playing the
solve, read against the solve playing itself, which nets zero rotated and rake-free, so the
difference is the departures' cost. Three limits stage 1 must state. Seats playing the solve only open
2.5bb and only bet menu sizes, so pricing the price and menu departures needs opponents that size off
the solve, which the paragraph above does not forbid. Postflop there is no complete solve for the
seats to play until phases 21 and 22 land. And in a six-handed game a departure can come out ahead of
fixed solve seats by taking chips from the third seat, so a positive figure is not evidence the bot
played better. Whether other opponents are needed, stage 1 drafts and the human gate asks.

It depends on 14 because 14 commits the strategy there is anything to measure. It does not depend on 16:
a yardstick that can only read a bot with postflop play could not be built before the postflop play it
is meant to judge, and what the departures cost today, with a check-fold postflop, is the baseline every
later phase is read against.

Phase 18 is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not measure whether the solve is right. It is taken as good play; see Scope.
- Do not change the committed chart, its sizing table or its expectations file to improve a number.
  This phase measures what is committed; a measurement that says the chart departs from the solve at
  a cost is a finding.
- Do not add PokerNow automation or browser observation. Those are phase 20's and stay out here.
- Do not add runtime solver calls or LLM-backed poker decisions.
- Do not add UI surfaces.
- Do not fill a refusal with a heuristic to keep a match running. A refused spot is a measurement of
  coverage and it is phase 19 that answers it.
- Do not report a chips-per-100 figure without its error bar, and do not call an opponent a
  strategy when it is a stub.

## Acceptance criteria
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The phase audit packet includes plain-language pass/fail evidence.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_playing_strength_report.txt`
- `reports/active/latest_verify.txt`

## Required command IDs
- `pytest_playing_strength`
- `generate_playing_strength_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- Known limitations and deferred items.
- What each opponent actually does, in plain words, so a reader can judge whether beating it means
  anything.
- Which departure from the solve each part of the cost comes from.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not change this contract during implementation mode.
- Do not publish a strength number taken over too few hands to clear its own noise, and do not quote a
  result against one opponent as though it held against another.

## Regression expectations
- Previously completed phase gates remain verifiable.
- Generated human docs remain current.
- File-size and scope checks continue to pass.
