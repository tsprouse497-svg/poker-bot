# MAINT-39 audit packet: phase 17 retired

Phase 17, The Corpus Verdict On The Committed Chart, was to compare the committed preflop chart with
real players' hands and say whether the calling gap is rake, price, or a defect in the ranges. Taylor
was told phase 18 measures how well the bot plays and ruled on 2026-09-25: "idc what real people do.
you can remove it." This task removes it. It changes no range, artifact, code path or test.

## What shipped

- `docs/phase_contracts/PHASE_17_CORPUS_VERDICT.md` deleted; phase 17 removed from
  `phase_status.yml` and `verification/loop_policy.yml`. Its two command ids were never registered,
  so the gate loses no command. No contract depends on 17.
- Phase 14's contract, at its 300-line cap, has its one live pointer to phase 17 amended in place and
  stays at 300 lines.
- Both roadmaps list phase 17 under Retired and drop it from the graph; the "Phases 00 through 14"
  line in each now includes 16.
- `scripts/generate_derived_chart_report.py` no longer tells a reader a later phase renders the corpus
  verdict or reads the prediction band; the report is regenerated.
- Backlog: seven entries re-homed off phase 17, four findings carried from the lane's unmerged
  branch, dated corrections on two older entries, and four new entries -
  `THE-CORPUS-VERDICT-PHASE-IS-RETIRED` (the record of all of this),
  `THE-ROADMAPS-STILL-SAY-THE-BOT-DOES-NOT-PLAY`,
  `FROZEN-TESTS-STILL-NAME-PHASE-17-AS-OWNER-OF-THE-REPORT-TEXT` and
  `THE-FLEET-BOARD-SHOWS-A-LANE-WHOSE-PHASE-WAS-RETIRED`.
- The lane tip `7e0dd71` is tagged `retired/phase-17` and pushed to origin; the branch and worktree
  are removed after merge.
- Phase 15's parked lane, retired by MAINT-35, is removed the same way on Taylor's word of
  2026-09-25: tip `730dfba` tagged `retired/phase-15` and pushed, then worktree and branch deleted.

## Independent review

One read-only reviewer that wrote none of this, no gate runs, note at
`reports/phase_audits/reviews/MAINT_39_RETIRE_PHASE_17/independent-review.md`.

- **Blocker, resolved.** The derived-chart report's opening paragraph still said the corpus verdict
  belongs to a later phase, contradicting the new text further down. Reworded and regenerated.
- **Non-blockers, resolved.** A carried entry quoted a sentence this task deleted; the retirement
  entry claimed the worktree gone before it was, and the tag was not on origin; one entry filed under
  phase 16 still named phase 17 as the measurement that would catch it; the limped-pot entry claimed
  the chart answers a limped spot, which a frozen test disproves. Each has a dated note, and the tag
  is pushed. A fifth, a borderline label, needed no change.
- **Alignment, filed.** Frozen tests still name phase 17 as the report's owner, and the fleet board
  shows lanes for retired phases, phase 15 included.

## Gate

Green, 50 of 50, `check_gate_bite` included, on the review fixes. The phase 15 note and this
packet landed after that run and are covered by the closeout gate.
