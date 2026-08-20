# Stage 3 Review - Phase 12 Human Gate

Read-only pass over `git diff 055227f --
reports/phase_audits/decisions/PHASE_12_SPOT_VOCABULARY_DECISIONS.md`, against the question
the driver printed: does the record now say what was actually ruled, including any cost that
was accepted rather than only the answer?

Coordinator-written self-review under `AGENTS.md` step 10; the no-delegation exception is in
the ExecPlan's Delegation Plan.

## Blocker

None.

The three `frozen-into-data` items carry their answers in the `Answer:` line the driver reads,
and the ruling section states what was chosen, on what date, by whom, and what the choice
costs. Both costs that came with the rendering option are written down rather than dropped once
the answer arrived: ragged column widths in the refusal inventory, and a precision ceiling at
hundredths where a size outside it is rejected rather than rounded. The ruling also records
that Taylor was shown the rendered key strings rather than the option names, which is the part
that makes the record checkable later - a reader can see the same thing he saw.

## Non-blocker

- All three landed on the recorded default. That is worth naming rather than passing over,
  because a record where every question came back as the default is the record most likely to
  be read as never having been asked. The section says what was put to him and how, so the
  agreement is evidence rather than an assumption.
- The ruling section states that the other ten items proceed on their defaults and are reported
  afterwards, which is what `docs/LOOP.md` requires of a `runtime-reversible` call. It does not
  restate all ten, which is right: they are each written out in full below it and duplicating
  them here would give the file two places to disagree.
- Decision 5 was put to Taylor alongside the three blocking items even though the loop would
  not have stopped for it, and the record says so. This is the Phase 11 decision-3 pattern:
  reversible, flagged, and the one a human actually needed to see. What the record cannot show
  is his answer, because the item stands on its default and no ruling was asked for; if he
  reverses it, the item flips to `normalise-the-open-only` and the 185-of-205 refusal figure
  becomes the phase's expected outcome rather than its rejected alternative.

## Alignment

None new. `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD`, cited by decision 13 at stage 2, is
still the open drift this gate sits on: the class vocabulary decides what stops for a human,
and it has two values for at least three kinds of choice.
</content>
