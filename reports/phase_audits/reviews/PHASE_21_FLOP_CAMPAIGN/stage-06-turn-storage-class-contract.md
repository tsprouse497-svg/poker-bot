# Phase 21 stage 6: storage class after the river was dropped

Read-only review by a subagent that wrote none of the change, 2026-10-04, of the contract's storage
criterion and the decision list after Taylor confirmed the stored turn and live river and answered
"we can do standard on glacier".

## Blocker
None.

## Non-blocker
- True to his words: decision 1's quote matches the contract; every object is now in the standard class, the fetch covers flop objects and the index, each turn object is checked on the solve machine before upload and fetched by the phase that plays the turn, and the flop fetch check survives.
- The figures put to him check: turn only is about 116 GB for five lines, about $2.70 a month standard against about $0.11 in Deep Archive.
- "Standard on glacier" is defensible as the standard class, as recommended, but also fits Glacier's standard retrieval tier. Standard is the safe direction (moving to an archive later is free; the reverse needs a restore). Response: recorded as "read as the standard class" and a one-line confirmation put to Taylor.
- Nothing else in the contract assumes Glacier or a restore.
- The ExecPlan still listed the archive question as open. Response: ticked with the ruling.

## Alignment
- `PEOPLE-ACROSS-THE-US-PLAY-AGAINST-THE-BOT-AND-NO-PHASE-OWNS-IT`: its 13 to 22 TB and cold archive no longer hold. Response: a correction line added.

## Held back
The `AGENTS.md` precondition from the previous review stands: this lane does not merge until `main`
says the turn is stored.
