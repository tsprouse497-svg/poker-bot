# Phase 11 stage 7 (gate) review

Covers the two commits that took the gate green: the file-size and citation repair
`8e6fa9b`, and the report restoration `9786022`.

Reviewer: coordinator, self-review; subagents are unavailable in this session.

## Blocker

- **[resolved]** `8e6fa9b` committed `reports/active/latest_sample_comparison_report.txt`
  from a run that happened while `check_gate_bite` had `comparison.py` mutated. The report
  it wrote shows Pluribus and the human players with identical agreement figures - 2594 of
  2758 for both - which is the pooled-population defect MAINT-09 fixed and judgment call 7
  of Phase 08 forbids by name. A `git add -A` swept it in.

  This is the hazard the `MUTATION-SENTINEL-IS-COMMITTABLE` work was for, arriving by a road
  that work does not cover. The sentinel and `check_scope` between them stop a *mutated
  source file* being committed; nothing stops a *report a mutated run generated* being
  committed, because the report is standing scope and its bytes look like any other
  regeneration. Restored in `9786022`, and the restored file is byte-identical to main's.

  Two things make it worth writing down rather than quietly fixing. The gate run that
  produced it exited non-zero for other reasons, so the mutated report rode in on a red
  gate; and `generate_sample_comparison_report` itself passed during it, which is exactly
  the "mutation survives" condition, seen from the report side rather than the test side.

- **[resolved]** `check_file_sizes` failed: the frozen-test repair pushed
  `tests/test_postflop_fallback.py` to 704 lines against the 700-line cap. Four comment and
  assertion lines reflowed, no assertion changed. Same class as the Phase 08 long line and
  the ruff cache task's unsorted imports: a lint or size failure inside an authored test
  that stage 4's check cannot see, because that check runs the phase's pytest command and
  not the gate.

- **[resolved]** `run_full_quality_gate` failed on backlog integrity: the stage-06 review
  wrote the ruff cache task's identifier in the capitals the quality gate reads as a backlog
  citation, so it reported a finding filed under an id nobody created. Reworded to prose.
  Third time this repo has hit it; the escape hatch is `NOT_BACKLOG_IDS` in
  `scripts/run_full_quality_gate.py`, which this phase may not touch.

## Non-blocker

- The gate is green at 41 commands and `check_gate_bite` passes, which means all four
  canaries this phase authored at stage 4 - against text that did not exist yet - apply and
  bite. That was the experiment: phases 08, 09 and 10 each wrote their own canaries after
  the code, and each recorded it as the same miss. Writing them first cost nothing and the
  find-strings matched the implementation on the first try.
- The restored comparison report being byte-identical to main's is a finding rather than a
  non-event, and the audit packet should carry it: neither the free fold nor the accumulated
  reopening rule moves a single number in the 3,048-decision corpus comparison. Both fixes
  are real - each has a test that fails without it - and neither spot occurs in this corpus.
  That is the honest reading, and it is narrower than "the fixes changed nothing".
- `pytest_sample_comparison`, the `pytest` catch-all and `check_gate_bite` all failed on the
  first gate run for one reason: the live mutation in the tree. They were not three failures.
  A reader of that first log would reasonably have counted five.

## Alignment

- `MUTATION-SENTINEL-IS-COMMITTABLE` (existing, `phase: contract-update`). The blocker above
  is the same defect one step downstream: the existing protections cover a mutated source
  file and not a report a mutated run wrote. The item is filed and belongs to whoever owns
  `check_gate_bite`; this phase records the new road into it rather than widening the item's
  scope from inside a phase that may not touch that script.
