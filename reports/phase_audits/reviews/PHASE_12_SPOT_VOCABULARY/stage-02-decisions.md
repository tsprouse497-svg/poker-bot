# Stage 2 Review - Phase 12 Decision List

Read-only pass over `git diff d0c7c43 -- backlog.yml
reports/phase_audits/decisions/PHASE_12_SPOT_VOCABULARY_DECISIONS.md`, against the question
the driver printed: is every reversibility class right? A `frozen-into-data` call filed as
`runtime-reversible` proceeds on its default and is then written into a committed artifact
that later phases are measured against.

Coordinator-written self-review under `AGENTS.md` step 10; the no-delegation exception is in
the ExecPlan's Delegation Plan.

The pass was done by asking, per item, what committed file the choice reaches and what it
would cost to change afterwards. Two things were checked in the tree rather than reasoned
about: whether any decision audit is committed outside `reports/active/` (none is - the only
committed `.jsonl` files are `data/samples/normalized_hands.jsonl` and
`data/samples/public_corpus/corpus_hands.jsonl`), and what `scripts/convert_preflop_export.py`
writes into the artifact besides weights.

## Blocker

- **[resolved] A `frozen-into-data` choice was missing entirely.**
  `convert_preflop_export.py` hard-codes `GENERATED_AT = "2026-08-11T00:00:00Z"`, and
  re-keying the artifact writes a file whose `generated_at` has to say something. No item
  covered it, so the phase would have inherited whatever the builder happened to type into a
  committed provenance field. Added as decision 13.
  Classed `runtime-reversible` after the check rather than by default, and the reasoning is in
  the item: the artifact is derived and `--check` reproduces it, so changing this field later
  is one converter edit and a regeneration, with no downstream key, sizing entry, report or
  phase-14 derivation moving with it. That is what separates it from the key format, where the
  same edit is a re-derivation of everything. The class vocabulary genuinely does not fit this
  case, which is what `LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` already records, so the item
  says so rather than pretending the fit is clean.

## Non-blocker

- Decisions 1, 2 and 3 are the only `frozen-into-data` items and all three are correct: each
  goes into `spot_id` on all 36 spots, into the sizing table's keys, into the refusal
  inventory, and into whatever proposed phase 14 derives, so changing any of them later is a
  re-derivation rather than an edit.
- Decision 4's `runtime-reversible` class holds only because the default is the permissive
  option. Loosening an orbit cap later is free; imposing one later invalidates keys somebody
  already committed, and proposed phase 14 does commit four-bet cells through this validator.
  The item now says that in as many words, so the class is not read as "a cap is a free choice
  either way".
- Decision 5 is correctly `runtime-reversible` - it is lookup behaviour and the artifact is
  untouched by it - and it is the item that most needs a human despite that, because it
  extends ruling 8 to raises the ruling did not mention. It is flagged in the file's header and
  in the item. Same shape as Phase 11's decision 3, which was reversible, flagged, and turned
  out to be the one Taylor actually ruled on.
- Decisions 7 and 8 touch the decision-audit payload, which looked like it might reach
  committed data. It does not: the only decision audits in the tree are under
  `reports/active/`, which every gate run regenerates. Class confirmed rather than assumed.
- Decision 11's default is not to commit anything, which is the safe direction, so
  `runtime-reversible` is right and the risk is the opposite one: a reader could take "the
  vocabulary now expresses four-bets" as "the bot now answers four-bets". The item states the
  refusal count does not fall, and the contract makes the report say so too.
- Every item carries a default, an options line and an `Answer:` line, and the driver accepted
  all thirteen classes, so the file is mechanically well formed. That is the cheap half of this
  review and it is not the half that matters.

## Alignment

- `ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE` - `docs/V2_ROADMAP.md`'s 1,691 and 848 expressible
  spots do not reproduce from the method the roadmap itself names; enumerating
  `solver_artifacts.schema.spot_key` gives 1,949 and 977. The ratio survives, so it reads as
  one systematic difference, but nothing tried reproduces the published pair. This stage cannot
  fix it: correcting four document quotations includes the artifact-size section of
  `docs/V2_RULING_MITIGATIONS.md`, whose 12 MB estimate is 1,691 multiplied by a measured 7.1 KB
  per spot, and that is a number proposed phase 14 is scoped against. Filed, and decision 10
  commits this phase's report to publishing the measured pair so the correction has evidence
  behind it.
</content>
