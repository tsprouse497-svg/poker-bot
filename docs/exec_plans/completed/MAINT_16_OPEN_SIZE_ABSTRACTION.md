# MAINT-16: Record The Open-Size Abstraction Ruling

## Objective

`docs/V2_RULING_MITIGATIONS.md` closed with one question for Taylor: whether the solved tree carries more than one opening price.
He has ruled that it does not, and that every opponent open abstracts to the single solved price of 2.5bb.

The ruling was put to him with the evidence against it, specifically the 52.5 against 77.8 percent call-agreement spread across the price range and the 47 of 58 big-blind call disagreements that faced a cheaper open, and reaffirmed.
That is what makes this a decision rather than an oversight, and it is why the cost gets recorded next to the ruling rather than argued about again.

This task records it as ruling 8, states the cost it carries, and records one design point the ruling makes newly important: where the abstraction lives decides whether it can ever be revisited without re-solving.

## Scope

Approved: `docs/V2_RULING_MITIGATIONS.md`, `docs/V2_ROADMAP.md`.

Forbidden: `docs/phase_contracts/**`, `phase_status.yml`, `verification/loop_policy.yml`, `backlog.yml`, `AGENTS.md`, and everything under `src/`.
The ruling has implications for the phase 12 lookup and the phase 14 report, and neither phase exists.

## Delegation Plan

- No-delegation exception: recording a decision made in conversation, into two documents this session wrote. There is no implementation lane, and the content is the ruling plus analysis already produced here.

## Slices

- [x] Slice 1: ruling 8 in `docs/V2_ROADMAP.md`, with the ruling, the reason it keeps the tree as costed, and the one-sided cost it accepts.
- [x] Slice 2: close out issue 3 in `docs/V2_RULING_MITIGATIONS.md`. Mark which of the four answers was taken, keep the ranking and the evidence intact as the record of what was weighed, and replace the open question with the ruling.
- [x] Slice 3: record the design point the ruling creates. Normalising a faced size at lookup keeps the spot key honest and the ruling reversible; folding the abstraction into the key itself does not.
- [x] Slice 4: correct what the ruling changes elsewhere. Phase 14 keeps its full sample and can attribute to rake, but price stays uncontrolled rather than becoming controlled, and phase 15 no longer refuses on price.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

All four slices landed and the gate is green.

`docs/V2_ROADMAP.md` carries ruling 8 at the end of the rulings list, with the reason (one price keeps the solve and the artifact at what the limps ruling already costed) and the cost stated in the same place (the bot answers a 2.25bb open from the 2.5 cell and so under-defends against cheap opens, with the 52.5 against 77.8 percent agreement spread and the 47 of 58 big-blind call disagreements as the measured size of the effect).
The proposed phase 12 section no longer asks how a size key matches an unsolved size; it records that the collision is dissolved and that the phase keeps its full sample while price stays an uncontrolled variable.

`docs/V2_RULING_MITIGATIONS.md` issue 3 is closed rather than trimmed.
The four ranked answers stay as the record of what was weighed, the ruling follows them and is classified honestly as the bucket option with a single unbounded bucket, and three things the ruling asks in return are written down: normalise a faced price at lookup rather than dropping size from the spot key, flag a substituted answer the way a refusal already carries detail, and make proposed phase 14 state that price is uncontrolled.
`What Needs Taylor` is now empty.

One correction beyond the four slices: recording an eighth ruling that carries a consequence left both documents claiming three where the count was four, so the two header sentences and issue 3's owner line were reconciled.
The three mitigation sections are unchanged in number, because rulings 2 and 8 land on the same collision.

## Next Agent Bootstrap

The repo is idle with phases 00 through 09 complete and nothing declared after them.

`docs/V2_ROADMAP.md` proposes seven v2 phases and records eight rulings.
`docs/V2_RULING_MITIGATIONS.md` plans the mitigations for the four rulings that carry a consequence, and has no open questions left.

Adoption is the next task and is mechanical.
The one semantic change owed before any phase starts is the `AGENTS.md` ingestion boundary, which needs a size bound expressed as a number.

Three items in the mitigation plan still need no solve, no ruling, and no phase: recomputing the spot counts and bytes per spot, adding a byte limit covering `data/artifacts/**`, and writing the three expectations-file checks down before a solve exists to tune them against.
The fourth, measuring the corpus opening-price distribution, is no longer needed to choose a price set, but it remains the way to quantify what ruling 8 costs.
