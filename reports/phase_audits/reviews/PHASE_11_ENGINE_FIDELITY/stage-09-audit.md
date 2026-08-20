# Phase 11 stage 9 (audit) review

Read-only pass over `git diff fd9f682 -- reports/phase_audits/PHASE_11_ENGINE_FIDELITY.md`.
Question asked: is every number recomputable and every claim narrower than the evidence
behind it? A wrong figure in a packet outlives the phase and gets quoted.

Reviewer: coordinator, self-review; subagents are unavailable in this session.

## Every number in the packet, checked against its source

| Figure | Source | Verdict |
|---|---|---|
| 41 gate commands | `reports/active/latest_verify.txt`, counted | correct |
| the reopening table, four rows | recomputed against the engine, and the report prints the same table with the subtraction in its own column | correct |
| 20, the level at which betting reopens | 10 plus 10, from the table itself | correct, and it is the recomputable number the contract requires |
| 31, the reopened seat's smallest raise | 21 plus a minimum raise of 10 | correct |
| 100 accepted, 120 rejected | `(20 - 20) + 100`, and the report prints both lists | correct |
| 0.00% fold at `t6/d100/BB/SB:call` | `PreflopChartLibrary.action_frequency_pct`, printed in the report | correct |
| 3,048 corpus decisions | 502 plus 2,546 in `latest_sample_comparison_report.txt` | correct |
| five canaries naming `pytest_engine_fidelity` | counted in `verification/mutations.yml` | correct |
| 22 minus 5, the short-open case | recomputed against the engine, and the report prints the resulting legal actions | correct |

## Blocker

- **[resolved]** Two claims were wider than their evidence.

  The checklist's row 16 said "five phase 11 canaries, all bite" and pointed a non-coding
  reviewer at `latest_verify.txt`, which shows only that `check_gate_bite` passed. The count
  is not in that file. Rewritten to point at `verification/mutations.yml` for the five
  entries and to say what a passing `check_gate_bite` actually establishes: the command
  fails under every committed mutation that names it.

  "Twenty-eight of the file's tests were red before any implementation existed" was true of
  the file as frozen at stage 5 and read as a claim about the file a reader would open,
  which now holds fifty-two. Rewritten to say twenty-eight of the forty-nine frozen at
  stage 5, and to account for the three added afterwards and why.

## Non-blocker

- The packet's strongest claim is the one it states most narrowly, and that is deliberate:
  the corpus comparison being byte-identical to main's is written as "neither spot occurs in
  this corpus" rather than "the fixes changed nothing", with the reason - six-handed
  Pluribus play has no surrendered rivers and no chains of short all-ins - stated in the same
  place. A reader who quotes only the first half will misreport the phase, and the packet
  cannot prevent that beyond saying so.
- The "was" column of the report, and therefore several "it used to" statements in the
  packet's plain-language section, are stated rather than measured. There is no alternative:
  the old behaviour left the tree at the build commit. The report's own header says this; the
  packet does not repeat it, which is a small asymmetry a careful reader would notice.
- The producer audit table lists six files and calls five correct. That verdict is a reading
  rather than a measurement for four of them - `comparison.py`, `table.py`, and the two sites
  in `generate_postflop_fallback_report.py` all pass `state.current_bet` or an equivalent,
  which is the documented meaning by inspection. What makes it more than a reading is that
  every one of them is exercised by a gate command that builds real queries, so the new
  `street_bet >= to_call` guard runs against all of them on every gate. The packet says this.
- The registry sweep reports one mismatch and no second. That is an honest negative result
  and it is worth knowing it is a reading of 41 descriptions against 41 scripts by one
  reviewer, not a check anything can run.

## Alignment

None new. The four carried items - `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT`,
`STRATEGY-QUERY-STREET-BET-NAME`, `UNDER-SIZED-ALL-IN-BET-DOES-NOT-BAR-PRIOR-CHECKERS`, and
`MUTATION-SENTINEL-IS-COMMITTABLE` - are all named in the packet's limitations section with
the phase that owns each.
