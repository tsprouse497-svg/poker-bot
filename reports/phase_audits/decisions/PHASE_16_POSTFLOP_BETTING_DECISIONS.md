# Phase 16 judgment calls

These are the choices about what a committed postflop solution covers, and what the bot does outside it.
No test in this repo settles them.
A solution that covers the wrong spots passes just as green as one that covers the right ones, and a bot that guesses on an unseen board looks exactly like a bot that knows.

They are recorded ahead of the phase because the phase is gated on them: `verification/loop_policy.yml` marks phase 16 `needs_human_data`, and these are the inputs it means.

Every item carries a reversibility class, which the loop driver reads at stage 2 to decide whether it must stop for a human.

- `runtime-reversible`: the choice only changes behavior at query time, so a later edit changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact that every later measurement then runs against. The loop halts until a human answers.

## What changed, and why this file exists

The premise this phase was declared under was wrong.
`docs/V2_ROADMAP.md` said the only sizing source in the repo is a preflop export and that phase 16 is blocked on a source that does not exist.
GTOpen solves postflop as its primary function.
Its README leads with postflop CFR; the Preflop Lab that phase 10 uses is the bolt-on beside it.
The postflop engine is the un-namespaced route surface (`/api/spot`, `/api/solve`, `/api/node`, `/api/runouts`, `/api/reports/*`), it takes per-street bet, raise and donk sizes, it does node locking and best-response, and it batch-solves a weighted canonical flop subset of 47, 95, 184, or all 1,755 flops.
`SEND TO POSTFLOP` carries both conditional ranges, the pot and the stacks out of a preflop line into a flop setup.

`docs/GTOPEN_SOLVER_NOTES.md` did not say otherwise; it recorded only what had been executed, and everything executed happened to be preflop. That is the note working as designed and a reader drawing the wrong inference from it anyway, which is why the note now states the postflop surface exists and is unrun.

One design point follows and it narrows this phase considerably.
A committed postflop artifact does **not** have to be a joint solved tree.
A postflop spot is self-contained: board, both ranges, pot, effective stack, sizes.
So the artifact can be a library of independent per-street spots keyed the way the preflop chart already is, and the bot can evaluate each street from the board, its hand, and a summary of prior action.

What does not decouple is ranges.
Postflop strategy is overwhelmingly range against range rather than a function of hero's two cards, so the same hand on the same board plays differently after `LJ open, BTN call` than after `BTN open, BB 3-bet, BTN call`.
The action summary in a spot key is therefore a handle on a pair of ranges, not history for its own sake, and the preflop line has to compress into it.

And generation stays sequential even though storage does not.
Villain's turn range is whatever he would bet and check with on the flop, which is the flop solution.
So enumerating turn spots requires the flop spots first, and one flop spot fans out to 47 turns and about 2,160 rivers.
That fan-out, rather than the preflop cross product, is what bounds this phase.

## 1. How deep the committed solution goes

Reversibility: frozen-into-data

Flop, flop plus turn, or all three streets.
The cost is not linear: one flop spot is 47 turn spots and about 2,160 river spots, before any preflop line is counted, and each has to be solved to a target exploitability rather than derived.

Committing turns and rivers is also where the artifact stops resembling a chart. The preflop artifact is 7.1 KB per spot and `data/artifacts/**` is currently covered by no size check at all, which `docs/V2_RULING_MITIGATIONS.md` already flags.

Default: **flop only.** The bot gets a real flop strategy that can bet and raise, and turn and river refuse the way an uncovered preflop spot refuses today. That is a smaller artifact, it needs no boundary change, and it makes the phase's own claim narrow enough to be true. It also leaves the turn as a separately fundable phase rather than a thing half-done inside this one.

The cost of that default, stated rather than buried: the bot bets a flop and then goes quiet, which is a worse experience than never betting at all if a drill deals past the flop. Whether that matters is evidence phase 15 produces.

Answer:

## 2. What the bot does on a board it holds no cell for

Reversibility: frozen-into-data

Any canonical subset smaller than all 1,755 flops guarantees the bot meets boards it has not solved. Suit isomorphism is exact and free; GTOpen already exploits it internally. Rank texture is not: mapping an unsolved `K72r` onto a solved `Q83r` is a heuristic, and `AGENTS.md` forbids heuristic guessing for missing chart spots.

So this is a boundary question, not an implementation detail. Either the rule holds and the bot refuses on an unsolved texture, or the rule is amended for board texture specifically, which is a `contract-update` to `AGENTS.md` in its own right.

Default: **solve all 1,755 flops and keep the boundary.** With a flop-only solution the runout fan-out is gone, so the full canonical set is the thing that removes the question rather than answers it, and the bot never faces a flop it has no cell for. If 1,755 proves unaffordable once solve time is measured, the fallback is a subset plus refusal, never a subset plus abstraction.

Answer: [Ruled by Taylor, 2026-08-19] Take the default, and defer abstraction rather than reject it.
Grouping similar flops so the bot plays them identically will eventually be needed, and it is filed as `POSTFLOP-BOARD-ABSTRACTION` rather than left as an unstated intention.
Not now, because at flop-only depth the full canonical set removes the need entirely, and an abstraction built where nothing requires it is a heuristic nobody can measure.

What that ruling also settles, worth stating because it was not asked directly: abstraction is the enabling condition for **depth**, not for breadth.
All 1,755 flops is affordable; 1,755 turns and rivers is roughly 3.8 million spots and is not.
So the turn is not a matter of solving more of the same thing, and deferring abstraction defers the turn with it.

## 3. Which preflop lines get a postflop solution

Reversibility: frozen-into-data

Only lines that see a flop matter, which is far fewer than the 1,691 six-handed 100bb spots the v2 vocabulary can express, but the count is not currently known. It becomes computable off the phase 10 export.

Default: rank the lines by how often the corpus and the drill actually reach them, take the head of that distribution, and record the covered set explicitly so a refusal names a line that was excluded rather than one that was forgotten. `reports/active/latest_refusal_inventory.txt` is the precedent and already works this way preflop.

Answer:

## 4. Exploitability target, and whether the solve is reproducible

Reversibility: frozen-into-data

GTOpen's own README puts 0.3% of pot as a study-quality target. Nothing in this repo has measured a real solve to any target, and determinism across two identical runs is still unverified — both are on phase 10's list, so phase 16 inherits whatever phase 10 establishes.

Default: adopt phase 10's measured answers rather than restating them here. If output is not byte-identical, an accuracy target and a tolerance get recorded in place of a checksum, which is the same fallback phase 10 declares.

Answer:

## 5. Whether the pot-odds river call ships alongside

Reversibility: runtime-reversible

`POSTFLOP-POT-ODDS-AGAINST-UNSEEN-DECK` calls a river bet when equity against the full unseen deck beats the price. It needs no solved data and invents no constant: equity is `(wins + ties/2) / 990` from the enumeration `hand_cannot_lose` already runs, and the price comes off the query.

A uniform unseen deck flatters hero, so this makes the bot over-call as the mirror of its current over-folding. Under the flop-only default it is also the only thing that acts on a river at all.

Default: build it, behind an explicit flag, and report the frequency it fires rather than claiming it is correct. It is runtime-reversible because no committed data records it; it is a rule the query evaluates.

Answer:
