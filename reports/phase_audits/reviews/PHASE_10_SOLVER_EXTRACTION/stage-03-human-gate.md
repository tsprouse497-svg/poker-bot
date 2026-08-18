# Stage 03 Review - Human Gate (Phase 10)

Question asked: does the record now say what was actually ruled, including any cost that was
accepted rather than only the answer?

Scope: `git diff 936ca7123ddccaa7ccb841164b5daa4ec054d175 -- backlog.yml
docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md
reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md`

Reviewer: coordinator, read-only pass, no gate runs. Subagent delegation is switched off in
this operator's sessions, so `AGENTS.md` step 10's self-review fallback applies.

## Blocker

- [resolved] **Thirteen filled-in `Answer:` fields recorded thirteen choices and no costs.**
  The driver's check is satisfied by a bracketed token, so a file that passes it can still be
  silent about what was traded away - which is exactly the failure mode the decision list
  exists to prevent, one indirection further back. A `Ruled by Taylor, 2026-08-18` section now
  names the three accepted costs: 21 corpus decision points and the committed solve's own SB
  limp frequency, given up by narrowing ruling 3; up to three points of legitimate tightness
  admitted by the directional slack; and the loss of tolerance-free ordering coverage on the
  widest-ranged position, given up by excluding SB by name.

- [resolved] **Two of the rulings correct standing documents and the record did not say so.**
  `docs/GTOPEN_SOLVER_NOTES.md` publishes a config body that omits `realization`, and
  `docs/V2_RULING_MITIGATIONS.md` section 1 asserts two things the probe falsified. A reader
  of either document would still be misled. Neither is in this phase's approved scope, so the
  corrections are recorded in the decision list with an explicit note that the documents
  themselves are wrong and were not edited here. Filed as drift below so it is closed rather
  than remembered.

## Non-blocker

- **Narrowing ruling 3 is a narrowing, not a reversal, and the file should keep reading that
  way.** Limps stay in the parity solve, which is where the reference file's limp frequency
  makes them necessary. If a later phase wants limps in the committed chart, the saved solve
  makes it a reload rather than a fresh run, which is the whole reason the save is a
  requirement rather than a convenience.

- **Decision 6b's basis is inferred and the ruling accepted it as inferred.** The parity
  comparison is therefore a comparison at a plausible matched rake basis, not a confirmed one,
  and the source card is required to say so. Worth restating in the audit packet, because a
  parity result reads as the tightest number in the phase and it is not.

- **The probe's measurements were taken under `limp: true`, and the committed solve will not
  have limps.** Every number quoted in the decision list is therefore indicative rather than
  predictive of the committed run: dropping the limp option gives SB's 60.81 percent of limp
  mass somewhere else to go, and the SB opening frequency will move. The two thresholds
  authored in decisions 4 and 5 were set against the probe, which is still the right order -
  they precede the committed solve - but nobody should be surprised when the committed SB
  numbers differ from the table above.

- **One decision is now partly moot and stays in the file.** Decision 7's SB limp definition
  is zero by construction in a no-limp tree, and it is retained because the parity solve still
  needs it. Keeping a definition that computes zero is deliberate rather than an oversight.

## Alignment

- `GTOPEN-NOTES-OMIT-REALIZATION` - `docs/GTOPEN_SOLVER_NOTES.md` publishes a config body with
  no `realization` field, so anyone following it silently gets the `static` default and a big
  blind that defends 99.71 percent. Filed in `backlog.yml`.
- `MITIGATIONS-ORDERING-AND-BOUND-CLAIMS-FALSE` - `docs/V2_RULING_MITIGATIONS.md` section 1
  asserts that rake moves no ordering and that the directional bound needs no tolerance.
  Measurement falsifies both through the small blind. Filed in `backlog.yml`.
