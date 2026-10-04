# Phase 21 stage 6, decision 17: contract-update review

Read-only review by a subagent that wrote none of the work, 2026-10-04, of the contract-update task
for decision 17: phase 21's contract rewritten under its cap, phase 16's one-line amendment, and two
backlog entries. Round 1 found three blockers and round 2 confirmed all three fixed and found one more, which round 3 confirmed fixed. Findings are kept as written; the coordinator's response follows each heading,
and only the reviewer marks a blocker resolved.

## Blocker
- [resolved] **The river confirmation was dropped without a ruling.** Decision 1 says Taylor "confirms the river together with the campaign budget"; the rewrite changed "when Taylor confirms the river" to "when Taylor sees the river's cost again" and deleted "since Taylor confirms the river then". Fix: restore both. Response: restored in the closure criterion ("when Taylor confirms or drops the river (decision 1)") and in the campaign-budget criterion.
- [resolved] **The six settling runs have fallen out of the $100 trial cap.** Decisions 6 and 13 count them in the trial budget, and the old cap criterion stated them beside the cap. Response: restored, "the six texture solves and the six settling runs below, stated beside the cap".
- [resolved] **Decision 4's amendment is named in Scope but not folded into the storage criterion it changes.** Turn and river objects go to Glacier Deep Archive and a read needs a 12 to 48 hour restore, so a fetch cannot check them. Response: the storage criterion now says the fetch covers the flop objects and the index in the standard class, and each turn and river object is checked against its board's counts and digest on the solve machine before it is archived; the closure criterion no longer claims the fetch checks them.

- [resolved] **Round 2: the rewrite dropped the check on fetched flop objects.** HEAD's closure criterion said the fetch command checks every fetched object against the per-street counts; the rewrite removed the whole clause where it should only have taken turn and river out. Response: the closure criterion now says "The fetch command checks every fetched flop object against its board's counts and its digest."

## Non-blocker
- Figures re-derived with the tree counter re-run against the patched crate; all match, including deuce trips as the card-memory maximum on every line and 44 of 94 (button) and 45 of 97 (small blind) check-only river starts per card under the new rule.
- "No 48 GB card qualifies" did not follow: 48 GiB exceeds 51,239,107,576 bytes by about 0.3 GB. Response: now "within 0.3 GB of a 48 GiB card before CUDA's own use, too thin to rent on".
- "The pin's rule reproduces this contract's earlier figures" was false for the never-reproduced 47.2 GB. Response: now "every figure the frozen tests pinned".
- The box-versus-M4 digest finding needs new-tree M4 digests committed first. Response: now "the M4's new-tree digests, committed first". The M4 re-solve runs on the Mac before any rented box (ExecPlan), and the box's eight determinism solves are its own, counted in the cap.
- Decision 15 was folded only into Scope. Response: the closure criterion now carries two bytes a number, the tenth of a percent, the residue on the largest entry and compression measured before any custom format.
- Decision 5 (RunPod, from a GPU) sits against the CPU-first rule. Response: not resolved in the contract, because which CPU Taylor meant is his to say; carried to him as an open question in the ExecPlan.
- Decision 18 is ruled but not applied, and blocks every solve under "do not solve on any build the notes do not record" if read as a requirement on CPU solves. Response: the contract now says the fold changes GPU code only and is required before the first GPU solve; the solver notes will say its GPU code is first proved at the GPU trial.
- Dropped figures and records: justified; `deep_convergence_check.json` is now named as kept as the pin's own record, and "the slowest board on record" now reads "the slowest board phase 16 solved".
- The tree figures' commands are not in the ExecPlan. Response: the ExecPlan records the counter's path and commands.
- The not-repeated thread proof should cite why. Response: the criterion now says decision 17's commit changes the tree builder, the save loader and the server's request, never the summation.
- Re-solving phase 16's four boards replaces committed data. Response: Taylor's handoff for decision 17, given in session on 2026-10-04, states "Re-solving them is part of this ruling", so it is ruled rather than open.
- The phase 16 amendment's "that river" had no antecedent. Response: now "could not lead a river after the turn checked through".
- The backlog entry repeated "the 44 that follow a called turn bet". Response: now names the turns on which in position bet or raised last and out of position called, and says out of position may lead after its own called turn bet under both rules.

- Round 2: a reflow put a dash at the start of an indented line, read as a nested bullet. Response: rewritten as commas.
- Round 2: the phase 16 amendment still overstated. Response: now "could not lead the river after in position's flop bet was called and the turn checked through".
- Round 2: Taylor's re-solve ruling is not in the repo's record. Response: the decision list is out of this task's scope; it is added to decision 17's answer in the implementation task, where the decision list is in scope.
- Round 2: decision 5 against CPU-first must be answered before any rental. Carried in the ExecPlan.

## Alignment
- `PHASE-16-CONTRACT-IS-AT-ITS-LINE-CAP`: correct as filed.
- `AN-AMENDMENT-WRITTEN-AS-ONE-LONG-LINE-DEFEATS-THE-CONTRACT-LINE-CAP`: filed from the reviewer's proposal.
- Phase 21's rewritten contract has little room left: carried by the existing `PHASE-CONTRACT-LINE-CAP-FORCES-REWRITES-OVER-AMENDMENTS`.
- `THE-PINNED-SOLVER-CARRIES-THE-AGGRESSOR-THROUGH-A-CHECKED-STREET`: phrase corrected as above.

## What the reviewer did not look at, when asked
How the frozen tests get re-opened under the freeze lock; whether phase 16's own tests and report
survive replacing its cells and `determinism.json`; the bulk export commit beyond its file list; the
decision 18 patch's content; the ExecPlan's machine notes, which rest on the old 48.50 GB figure;
decision 17's unmeasured 10 to 18 percent reach estimate. Each is carried into the implementation
review's brief.
