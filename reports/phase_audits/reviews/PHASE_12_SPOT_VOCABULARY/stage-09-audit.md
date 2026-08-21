# Phase 12 stage 9 review - the audit packet

Read-only pass over `git diff b6a0958 -- backlog.yml reports/phase_audits/PHASE_12_SPOT_VOCABULARY.md`,
against `AGENTS.md` and `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`.
No gate runs inside the review.

Question the driver asked: is every number recomputable and every claim narrower than the evidence behind it?
A wrong figure in a packet outlives the phase and gets quoted.

Coordinator-written, both lenses, as the phase's no-delegation exception records.
Subagents are unavailable in this operator's sessions, so `AGENTS.md` step 10's self-review fallback applies.
This stage was picked up by a session that did not run stages 1 to 8, which is worth stating: every figure below was checked against the committed reports rather than against a memory of having measured it.

## Blocker

- [resolved] **Two figures in the packet were wrong on first write, and both were the kind that gets quoted.**
  The pre-phase weights checksum was written `eaf2c6cd` where the artifact and the report both carry `eaf2c6cc`.
  A checksum is the one number in this packet whose whole purpose is exact comparison, and a reader checking the packet against the file would have found a mismatch and had no way to tell a typo from a broken re-derivation.
  Corrected, and a line added saying the first two lines are the same 64 characters, which is the claim the three-line block exists to make.
  The key-derivation sweep said six call sites; there are ten, across seven files, and the enumeration in the packet had omitted `generate_preflop_strategy_report.py` entirely.
  That one matters more than a miscount looks, because the sweep is what stands in for a test that cannot exist: the contract asks for it precisely because no test can prove a second derivation does not exist, so an undercount is a sweep that did not sweep.
  Both corrected before this note.

## Non-blocker

- **Every other figure reproduces from a committed file.**
  Checked one at a time against `reports/active/latest_spot_vocabulary_report.txt`, `latest_verify.txt`, `latest_sample_refusal_inventory.txt`, and the sizing table: 969 of 2,758 substituted, the 959/66 open-against-later split, 966 of 1,025 within 0.5bb and 3 over 3bb, 1,949 to 18,773 expressible, 72 of 79 three-bet decisions, 290 refusals unchanged, 78 to 159 distinct refused spots, 128 to 126 and 472 to 474 in self-play, ten distinct raise-to sizes, and the restatement table's three columns.
  Two were recomputed rather than copied: 966 is 554 plus 412 from the distance histogram, and 69 tests is `pytest --collect-only` on the two files the command names.
  43 of 43 gate commands and four canaries were counted from the tree rather than taken from the ExecPlan.

- **The packet carries the two report defects stage 8 found rather than passing them off.**
  The census reconciliation gap and the aggregated opening-price column are in Known limitations, named as report defects, not folded into a sentence that implies the report is clean.
  This is the right disposition for a packet whose contract asks the report to be legible to a non-coding reviewer and whose own reviewer found it is not, in two specific places.
  It should be said plainly that this stage did not fix them.
  Both fixes are inside `scripts/generate_spot_vocabulary_report.py`, which is a builder file and out of this task's scope by design, and regenerating the report from a writing task would let the packet's author reshape the evidence the packet describes.
  So they ship as stated limitations, and a reader who wants the census to add up has to read this packet beside the report.

- **The checklist claims and the contract criteria line up, and where a criterion is met by a sweep rather than a test the checklist says so.**
  Rows 7 and 8 are sweeps, and both name their method.
  Row 19 passes the criterion while reporting that the roadmap's published pair does not reproduce, which is the criterion being satisfied by a correction rather than by agreement, and the row says which.

- **The three backlog closures assert only what the phase actually did.**
  `RAISE-SIZE-IN-SPOT-KEY` explicitly records that closing it moved no agreement rate, which is the thing a later reader would most likely assume it did.
  `SECOND-ORBIT-PREFLOP-SPOTS` records that the depth check is table-wide rather than per-seat, so the payability bound is weaker than "legal preflop order" sounds.
  `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` records the non-move as a checked result and separates the one figure that moved for a re-seeding reason with no poker content.
  Each cites `d046ac9` as the commit that closed it, which is the build commit and is where the behaviour actually landed.

- **The recomputable number is genuinely recomputable and settles something.**
  Five `/rfi` entries in a committed JSON file, four reading 2.5 and one reading 3.5, no code.
  It is also the evidence for decision 6 rather than a decorative arithmetic exercise: a single constant for "the solved opening price" is already wrong today, not merely after some future solve.

## Alignment

- `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` - amended rather than newly filed.
  Three of the four inherited entries were still `deferred` at stage 9, two stages from closeout, and they were the phase's three headline deliverables.
  Phase 11 did the same thing with all six of its own items and was caught only because somebody read the backlog and the audit packet side by side; this lane was caught the same way and for the same reason.
  The entry already asks for a check comparing an item's `phase` against that phase's status in `phase_status.yml`.
  What this stage adds as evidence is that the check as described would not have fired here: it triggers on an item filed against a *completed* phase, and phase 12 was `active` the whole time it was wrong.
  So the check would catch the state only after closeout had already committed it, which makes the missing closeout rule the load-bearing half rather than the missing check.

- `TWO-LANES-CAN-FILE-ONE-DEFECT-TWICE` - unchanged and still open, and this stage is a second instance of the same shape.
  The stale primary checkout at `~/projects/poker-bot` reports 11 completed phases while `main` has 12, because a parked lane's `phase_status.yml` is as committed as the live one.
  Filed under the existing id rather than a new one, since it is the same root: per-lane copies of shared bookkeeping with nothing comparing them.
