# MAINT-14: Record The Seven V2 Rulings

## Objective

`docs/V2_ROADMAP.md` closes with seven open questions and states that none of them are answerable from the repo.
Taylor has now answered all seven.
A proposal whose blocking questions were settled in conversation and nowhere else is a proposal the next agent re-opens, so this task writes the rulings into the document that raised them.

Three of the rulings carry consequences for phases that already have text, and recording a ruling without its consequence is the same failure in a slower form.
Rake-free changes what the one external expectations file can prove.
Limps in the tree roughly doubles the artifact that proposed phase 14 already costed.
2.5bb leaves a known price gap against the corpus median that proposed phase 14's closing measurement has to account for.

It records and does not adopt.
`phase_status.yml`, `verification/loop_policy.yml`, `docs/phase_contracts/**`, `backlog.yml`, and `AGENTS.md` stay untouched.
Ruling on a boundary and editing the file that states the boundary are separate acts, and only the first has happened.

## Scope

Approved: `docs/V2_ROADMAP.md`.

Forbidden here, and named because the temptation is real now that the boundary questions are answered: `AGENTS.md`, `phase_status.yml`, `verification/loop_policy.yml`, `docs/phase_contracts/**`, `backlog.yml`.
The three boundary rulings change what `AGENTS.md` should eventually say, and that edit is a semantic contract change needing its own `contract-update` task.

## Delegation Plan

- No-delegation exception: a single documentation file, recording seven decisions that were made in conversation with Taylor in this session and exist nowhere else yet. There is no lane to bound, and an independent implementer would have to be handed the rulings verbatim to write them down, which is the whole of the task.

## Slices

- [x] Slice 1: replace the Open Questions section with the rulings, each carrying its date and the reason given.
- [x] Slice 2: mark the boundary table as ruled rather than proposed, and say plainly that `AGENTS.md` still states the old boundaries.
- [x] Slice 3: fold the four solve rulings into proposed phase 10, including what rake-free does to the expectations check and what the missing licence obliges the source card to say.
- [x] Slice 4: correct proposed phase 14's spot count and artifact size for limps being in the tree, and name the 2.5bb-against-2.25bb price gap its closing measurement inherits.

## Verification

- `uv run python scripts/run_verify.py`

## Outcome

Full gate green across 35 commands.
All seven rulings are recorded in `docs/V2_ROADMAP.md` with the date they were made, and the three consequences that are not merely bookkeeping are written into the phases that inherit them.

Recording the rulings surfaced one thing the proposal did not contain.
Proposed phase 12 puts raise size in the spot key, the solve is ruled at 2.5bb, and the corpus median is 2.25bb, so a literal size key would turn proposed phase 14's closing measurement into an empty sample of refusals rather than a measured disagreement.
That is now named in phase 14 as something phase 12 has to settle, with the three defensible answers listed, because the failure mode is choosing none of them and finding out at the cutover.

The document remains a proposal.
No phase is declared, no contract skeleton exists, and `AGENTS.md` still states the ingestion boundary the way ruling 5 supersedes.

## Next Agent Bootstrap

The repo is idle with phases 00 through 09 complete and nothing declared after them.
`docs/V2_ROADMAP.md` proposes seven phases and now carries Taylor's rulings on all seven of its former open questions; `phase_status.yml` still knows about none of the phases, which remains the honest state.

The next task is adoption, and it is mechanical rather than semantic: rewrite `docs/ROADMAP.md`, add seven `future` entries to `phase_status.yml`, create seven contract skeletons under `docs/phase_contracts/`, add seven `verification/loop_policy.yml` entries, and re-tag `backlog.yml` so every deferred item either names the phase that closes it or stays honestly deferred.

Two things must happen around it rather than inside it.
The `AGENTS.md` boundary edits are semantic and need their own `contract-update` before any phase starts: large hand-history ingestion lifts for a single player's own hands with a stated bound, and the other five boundaries stay as written.
`MUTATION-SENTINEL-IS-COMMITTABLE` is tooling rather than phase work and should land as its own maintenance task before the first v2 phase.
