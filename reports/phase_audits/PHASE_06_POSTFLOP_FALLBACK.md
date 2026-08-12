# Phase 06 audit packet: Conservative Postflop Fallback For Simulation Continuity

Written for a reviewer who does not read code.
Everything here can be checked from committed files.

## Summary of what changed

The bot can now play a hand to its end.
Phase 05 gave it a preflop strategy read from a real solver chart, and left it with nothing to say the moment a flop came down.
This phase fills that hole with the smallest honest thing: a fallback that checks whenever checking is free, folds to a bet, and puts money in on exactly one path - a board where no holding a villain could possibly have beats hero, whatever card is still to come.

There is no postflop chart in this repo and there will not be one in v1.
So this is a continuity device and not a postflop strategy, and it is named that way in the code, in the report, and here.
It has no pot-odds rule, no hand-strength threshold, and no equity estimate against an assumed range, because each of those needs a number the repo cannot source and a fallback carrying an invented number would be indistinguishable from a strategy.

It also never bets and never raises, on any street, in any spot.
A bet needs a size and the repo's only sizing source is the preflop solver export.

A second object, the composite, routes preflop to the chart and flop through river to the fallback, so Phase 07 hands a hand to one thing instead of reassembling that routing at every call site.
The composite adds no poker of its own: its answer for any query is its component's answer, unchanged, and a preflop chart refusal travels out through it carrying the original reason code rather than being quietly converted into a check.

**What changed after review.** The phase reached a green gate with two rules that a human then overruled, and both changes are the substance of this packet rather than a footnote.
The first version folded a hand that could only be chopped, and called that strict.
It is not strict, it is a certain loss, and the section on judgment calls has the arithmetic.
The first version also only ever put money in on the river; the turn was declined on a cost that belongs to the flop.
Both are fixed.

## Pass/fail checklist

Each line is checkable without reading code.

| # | Check | How to check it | Verdict |
|---|---|---|---|
| 1 | Nothing in the repo calls this a postflop strategy | `reports/active/latest_postflop_fallback_report.txt`, first section | PASS |
| 2 | It never bets and never raises | Same report, "Action chosen": call 12, check 36, fold 24, over 72 states | PASS |
| 3 | It answers every postflop situation the engine can produce | Same report, "States covered: 72 = 4 x 3 x 6", every one a decision | PASS |
| 4 | It never refuses postflop | Same report, "Postflop refusals: 0" | PASS |
| 5 | The situations were not chosen by hand | Same report: the four legal-action sets are what the engine's own `legal_actions` returned, swept over every betting shape it can be put in | PASS |
| 6 | A preflop query is refused rather than answered | `pytest_postflop_fallback`, `TestStreetRouting` | PASS |
| 7 | Money goes in only where the hand cannot lose | Same report, "Where money goes in", eight worked examples with cards | PASS |
| 8 | A hand that can only be chopped calls | Same section: `Kd Qh` on `9c 9d 9h 9s Ac`, 0 beat and 990 tie, calls | PASS |
| 9 | The turn claim survives every river card, not just the board | Same section: `Th Jd` on `9c 8c 7h 6d` folds because 25 of 46 rivers break it; the same cards on `9c 8c 7h 6d 2h` call | PASS |
| 10 | The flop never invests | Same report, "Why the flop is not on this list" | PASS |
| 11 | Every decision is legal poker | 78 committed audit lines, each built through the Phase 03 record that rejects an illegal action; `reports/active/latest_postflop_decision_audit.jsonl` | PASS |
| 12 | The same query decides the same way every run | Report and audit reproduce byte for byte across runs; `TestInvarianceAndDeterminism` | PASS |
| 13 | Suits and hole-card order do not change a decision | Same test class | PASS |
| 14 | A preflop chart refusal is not converted into an action | Same report, composite section: 5 refusals from the chart, 0 from the fallback | PASS |
| 15 | Every judgment call was answered before code existed | `reports/phase_audits/decisions/PHASE_06_POSTFLOP_FALLBACK_DECISIONS.md` | PASS |
| 16 | The gate still fails when the code is deliberately broken | `check_gate_bite`, five mutations against this phase's command | PASS |

## Recompute one number by hand

**The number: 10 postflop decision points across the committed sample hands.**

Open `data/samples/normalized_hands.json`.
For each hand, go to `streets` and find the entries named `flop`, `turn` and `river`, ignoring `preflop`.
Count the entries in each one's `actions` list and add them up.

| hand | postflop actions | total |
|---|---|---|
| `phase02-heads-up-showdown` | flop 2, turn 2, river 2 | 6 |
| `phase02-three-way-side-pot` | none | 0 |
| `phase02-preflop-fold-out` | no postflop streets | 0 |
| `phase02-turn-fold-out` | flop 2, turn 2 | 4 |
| | | **10** |

Counting the file by hand gives 10.
Driving the same file through the replayer and the composite reached 10 postflop decision points, which is the figure in the report's own "Check one number by hand" section.
The two blind posts that open every preflop street are deliberately not in this count: they are forced rather than chosen, and the replayer never offers them to a strategy.

A second number a reviewer can check without code: `Kd Qh` on `9c 9d 9h 9s Ac`.
All four nines and the ace are on the board, so hero's best five cards are the board's, and so is every villain's.
The report says 0 of 990 holdings beat hero and 990 tie.
That is why this hand calls.

## The worked call examples, with cards

This is the only place the bot puts money in postflop, so it is written out as cards rather than described.
Full prose for each is in the report; the verdicts are here.

On the river, where the board is complete and the question is 990 possible villain holdings:

| hero | board | beat | tie | verdict |
|---|---|---|---|---|
| Ac Kc | Qc Jc Tc 2d 3h | 0 | 0 | calls - a royal flush, and a tie needs Ac and Kc, which hero holds |
| Ac 2c | As Ah Ad Kc Kd | 0 | 0 | calls - quad aces, no flush is possible, and hero holds the fourth ace |
| Kd Qh | 9c 9d 9h 9s Ac | 0 | 990 | calls - the whole table has quad nines and the ace, so everyone chops |
| 2d 7h | Ac Kc Qc Jc Tc | 0 | 990 | calls - the board is a royal flush and nobody can hold it, so everyone chops |
| Ad Kd | 2d 3d 4d 5h Kc | 1 | 0 | folds - 6d 5d makes a six-high straight flush; one holding out of 990 is enough |

On the turn, where a card is still to come and the claim has to hold after every one of the 46 that could:

| hero | board | rivers that break it | verdict |
|---|---|---|---|
| Ac Kc | Qc Jc Tc 2d | 0 of 46 | calls - the royal flush is already made, so no card can touch it |
| Th Jd | 9c 8c 7h 6d | 25 of 46 | folds - nothing beats the straight yet, but two clubs are showing and a club river hands any two clubs a flush |
| Th Jd | 9c 8c 7h 6d 2h | (river) | calls - the club missed, so nothing beats the straight any more |

The last two rows are the same hand one card apart, and they are the clearest thing in this packet: the turn rule is not the river rule with a shorter board.

## What a hand played by this bot actually looks like

This matters outside the phase, so it is stated rather than left to be discovered.

Against another copy of itself, every postflop street checks through, because neither side ever bets.
So a hand is decided preflop by the committed charts and then settled at showdown.

Phase 07 may therefore measure preflop decisions with equity realised at showdown.
Phase 07 may **not** make any claim about postflop play, because there is none to measure.
That has to appear in Phase 07's own contract rather than be inferred from a report.

One more consequence for Phase 07: a preflop chart refusal arrives as a refusal, not a decision.
The simulator has to handle an outcome that is not an action.
That is more work there and the correct place for it: covering it here would erase the coverage signal Phases 04 and 05 were built to produce, and is the heuristic guessing for a missing chart spot that `AGENTS.md` forbids by name.

## Commands and reports

| Command | What it proves |
|---|---|
| `pytest_postflop_fallback` | 44 cases over street routing, totality, legality, the two call bars, invariance, determinism, and the composite |
| `generate_postflop_fallback_report` | `reports/active/latest_postflop_fallback_report.txt` and `reports/active/latest_postflop_decision_audit.jsonl` |

Full gate green across all 29 commands, including `check_gate_bite`.

Five mutations must make `pytest_postflop_fallback` fail, and do:

| Mutation | What it breaks |
|---|---|
| `fallback-answers-preflop` | the fallback accepts a preflop query, so a chart gap becomes a quiet passive action |
| `fallback-folds-guaranteed-chops` | a tie counts against calling again - this is the review blocker itself, reinstalled as a canary |
| `fallback-abandons-the-turn` | the call reverts to river-only |
| `fallback-turn-needs-only-one-safe-river` | the turn claim becomes existential rather than universal, which is the difference between a fact and a hope |
| `composite-routes-preflop-to-the-fallback` | the committed charts stop being consulted at all |

The gate now runs in about 65 seconds rather than 5.
Nearly all of the increase is `check_gate_bite` re-running this phase's tests once per mutation, each paying for one full turn sweep at 45,540 hand evaluations.
That is the measured price of extending the call to the turn, and it was accepted with the ruling.

## The judgment calls, and what each answer changed

Seven were recorded before any code existed, all `runtime-reversible`, so the loop proceeded on their defaults and reports them here.
Two of them were overruled at review; those are first.

**2. Whether a hand that can only be tied calls - ruled `strict-no-ties`, re-ruled to `allow-guaranteed-chops`.**
The original ground was that "a guaranteed chop pays a full call to win half a pot, so whether calling is right depends on the price".
That is false, and it was the whole ruling.
The pot that gets chopped holds the villain's bet and the dead money as well as hero's call, so facing a bet of B into a pot of P that already contains B, a hand nothing can beat returns at least (P + B) / 2 for a payment of B: a gain of at least (P - B) / 2, and P always exceeds B because a postflop pot holds the preflop money.
In the state the report enumerates - pot 120, of which the villain's bet is 20, and 20 to call - folding gave up 50 chips.
What changed: two of the five river examples flipped from fold to call, one of them a royal flush on the board where every player has the nuts and calling is free money no human declines.
"Strict" was doing the opposite of what its name promised.

**3. Which streets the exception covers - ruled `river-only`, re-ruled to `extend-to-turn`.**
The original cost objection gave the flop as "903 runouts against 990 villain holdings", and both figures were the river's own shifted by a card: 903 is C(43,2), and on the flop the unseen deck is 47, not 45.
Measured, the streets are nothing alike.
A river decision is 990 evaluations and 0.09 seconds.
A turn decision is 46 river cards against 990 holdings, 45,540 evaluations and 3.6 seconds.
A flop decision is 1,081 holdings against 990 runouts, 1,070,190 evaluations and 83 seconds.
The turn is affordable inside an exhaustive sweep and the flop is not, and the turn also decomposes into 46 river checks, so it reuses the river test rather than needing an enumeration of its own.
What changed: the bot now calls turn bets it cannot lose to, and the flop gap narrowed to the flop alone in `backlog.yml`.

**1. What the fallback does when facing a bet - `fold-except-unbeatable`.**
Fold, with the one exception above. Every alternative needs a number the repo cannot source.
What it changed: the bot folds to postflop aggression far more than any real player should, so it loses money to anyone who bets. That is loudly bad rather than quietly bad, which is the point of calling it a fallback.

**4. Never betting or raising - `never-aggress`.**
The item with consequences outside the phase; see "What a hand played by this bot actually looks like".
What it changed: nothing in this phase breaks, but every Phase 07 baseline computed before a real postflop strategy exists is a preflop baseline, and must not be labelled otherwise.

**5. What the composite does with a preflop chart refusal - `pass-through`.**
What it changed: Phase 07 has to handle an outcome that is not a decision.

**6. Whether the fallback may answer a preflop query - `refuse`.**
What it changed: nothing, beyond a caller having to route correctly, which the composite already does. It closes off a second, silent preflop strategy reachable by mistake.

**7. What the unseen deck means multiway - `full-unseen-deck`.**
The enumeration is every two-card combination hero cannot see, not narrowed by seat count or by which cards folded players took.
What it changed: the test is conservative in the only direction that matters. It can decline to call a hand that was in fact unbeatable; it can never call one that was beatable.

## Independent review

Recorded in full at `reports/phase_audits/reviews/PHASE_06_POSTFLOP_FALLBACK.md`.
One domain blocker, seven non-blockers, no mechanical blocker.

The blocker is judgment call 2 above.
It is worth reading as evidence about the loop rather than only about the bug: the wrong rule had a green gate, three frozen tests pinning it, and a mutation canary defending it.
Nothing mechanical could have caught it, because the code did exactly what the contract said and the contract said the wrong thing.
The domain review at stage 8 is the only guard against that, which is why `docs/LOOP.md` keeps it even when the gate is green.

The reviewers were not delegated to read-only subagents this round.
Subagent delegation was disabled for the session that reached stage 8, which `AGENTS.md` step 10 permits with the reason recorded.
It is weaker than the loop intends and weaker in the direction that mattered here, since the blocker is a claim about poker rather than about code.
The arithmetic is three lines and checkable, which is the mitigation, not a substitute.

Resolved: the blocker and the turn finding, both by ruling plus implementation.
Filed rather than fixed: `FALLBACK-FAIL-CLOSED-CAN-CALL`, and the duplication between the frozen tests and the report generator.

## Known limitations and deferred items

- **A flop bet always takes the pot from this bot.** `POSTFLOP-UNBEATABLE-EARLIER-STREETS`. The honest claim there is 1,070,190 evaluations for one decision; a sampled version would turn the fact back into a guess. The fix is a faster evaluator, not a new rule.
- **No postflop strategy exists.** `V2-POSTFLOP-STRATEGY`. The bot never bets or raises after the flop, so it takes no value with the nuts and applies no pressure ever. It calls a river bet holding the stone nuts and does not raise it.
- **The fail-closed branch can invest, and can refuse postflop.** `FALLBACK-FAIL-CLOSED-CAN-CALL`. Where fold is not among the legal actions the module calls instead, and where neither fold nor call is legal it returns a postflop refusal. Both contradict a contract criterion; neither is reachable from a legal-action set the engine produces, and both are reachable from a hand-built query. Found by this phase's mechanical review.
- **Two readings of `street_bet` are now both committed.** `STREET-BET-MEANING-AMBIGUOUS`. This phase's generator uses the street's bet level, which is the reading the preflop chart needs; the Phase 03 generator still passes hero's own contribution.
- **The frozen tests and the report generator hold the same hundred lines twice** - the betting-shape sweep, the named scenarios, and the query builder. Deliberate under the loop, since a builder may not write to `tests/`, but the two copies can drift and what they would drift about is the one spot where money goes in. The fix is a shared module, in a task where `tests/` is legitimately in scope.
- **The turn extension made the gate about a minute long.** Accepted with the ruling and recorded here so nobody later treats it as a regression.

## Human sign-off

Judgment calls 2 and 3 ruled by Taylor on 2026-08-12, on the stage 8 review.
Remaining sign-off: read the two turn rows in "The worked call examples" and confirm that folding `Th Jd` on `9c 8c 7h 6d` and calling it on `9c 8c 7h 6d 2h` is the behaviour you want.
