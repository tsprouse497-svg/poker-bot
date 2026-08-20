# Phase 11 stage 11 (advance) review

Read-only pass over `git diff e51dda1 -- backlog.yml
reports/phase_audits/PHASE_11_ENGINE_FIDELITY.md
reports/phase_audits/decisions/PHASE_11_ENGINE_FIDELITY_DECISIONS.md`.

Question asked: bookkeeping only. A content change here belongs to an earlier stage.

Reviewer: coordinator, self-review; subagents are unavailable in this session.

## Blocker

None.

## Non-blocker

- **This stage's diff is not bookkeeping, and the driver is right to ask.** It carries a human
  ruling and two substantive corrections. Both arrived after the phase closed, and neither
  could have been produced by an earlier stage:

  Taylor ruled decision 3 on 2026-08-19, after the tag. The loop had already passed its human
  gate at stage 3 without stopping, correctly, because the call is `runtime-reversible`. A
  record that keeps asking a question somebody answered elsewhere is a question the next agent
  re-asks, so the ruling belongs in the record whenever it arrives. It confirms the default,
  so no code, test, contract or number moves.

  The two corrections came out of writing the full assumption inventory for him, which nothing
  in the loop asks for. That is the honest finding of this stage: the phase's own machinery -
  nine review passes, a decision record, an audit packet with a limitations section - did not
  surface either item, and one pass at listing every assumption surfaced both in an hour.
  Worth considering whether the loop should demand that inventory at stage 9 rather than
  leaving it to a question a human happens to ask.

- **The packet's corrected sentence is now narrower and stronger at once**, which is the shape
  a correction like this should take. It was "neither spot occurs in six-handed Pluribus play",
  a claim about a 10,000-hand dataset nobody counted. It is now a claim about the 499 committed
  hands, with the argument that makes it near-proof for those - one recorded exclusion, and
  that one for fractional chips, so a hand carrying either spot would have failed replay under
  the old rules and appeared as an exclusion of its own - and an explicit statement that the
  full subset is unmeasured.

- **Three limitations were added to the packet rather than two.** The third is the inventory
  itself: nine of this phase's assumptions were recorded only in review notes or code comments
  and so never reached the human gate. The one that matters most is named there, because it
  sits directly under the ruling: the ruling covers who may raise, not what the raise must
  cost, and the price - 31 rather than 22 - was settled by the implementation and pinned by a
  test without ever being asked.

- **The review notes from stages 7 and 8 still carry the wider phrasing** and were deliberately
  left. A review note is the record of what a reviewer thought at the time; amending one to
  match a later correction is the same move as deleting a resolved blocker. The packet is the
  document readers quote, and it is the one that was fixed.

- Two backlog filings, both `contract-update` rather than assigned to a phase, because each
  needs a contract to say what the behaviour should be before anything implements it. The
  first, `MIN-RAISE-OVER-AN-INCOMPLETE-ALL-IN-BET`, records my reading and says explicitly
  that whoever fixes it owes the ruling its own human gate rather than taking the reading on
  trust - it is the same class of rules question decision 3 was.

## Alignment

- `MIN-RAISE-OVER-AN-INCOMPLETE-ALL-IN-BET` (filed this stage). The engine's raise bar over an
  incomplete all-in bet diverges from the live rule, on the branch this phase edited.
- `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS` (filed this stage). One schema version
  now spans two readings of a field, so an audit line does not say which produced it.
- `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` (phase 12), `STRATEGY-QUERY-STREET-BET-NAME`
  (phase 13), `UNDER-SIZED-ALL-IN-BET-DOES-NOT-BAR-PRIOR-CHECKERS` and
  `MUTATION-SENTINEL-IS-COMMITTABLE` and `LOOP-STAGE-10-DEMANDS-A-REVIEW-IT-FORBIDS-WRITING`
  (contract-update). All carried unchanged.
