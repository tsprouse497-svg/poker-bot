# Phase 08 Review Notes

**No independent reviewer was available.** Subagent delegation is disabled in this
operator's sessions, which overrides the coordinator default in `AGENTS.md`. Step 10
of that file permits self-review when the concrete reason is recorded, so this is a
self-review and its weakness should be read as real: the same mind wrote the contract,
the tests, and the implementation, and a shared misunderstanding is invisible to all
three at once.

The compensating control is two passes with different questions. The mechanical pass
asks whether the thing works. The domain pass ignores the contract entirely and asks
whether the poker is right, which is the only question a green gate cannot answer.

## Mechanical pass

- Full gate green across 33 commands. 20 mutations applied and all 20 caught, including
  the four authored for this phase.
- The four Phase 08 canaries were checked individually rather than trusted in
  aggregate: the call-amount conversion, the button derivation, the nonzero-weight
  agreement rule, and refusals staying out of the disagreement count all make
  `pytest_sample_comparison` fail when broken and pass when restored.
- 499 of 500 selected hands convert and settle to the corpus's published finishing
  stacks, every seat, no tolerance. The one exclusion is committed with its reason.
- The settlement check is not circular. `result` is built from the corpus's published
  numbers, and `replay_hand` raises when the settlement it computes from the engine
  disagrees with `result`. The engine never sees the finishing stacks.
- The reports regenerate byte-identically. No clock, no network, no seed of their own.
- Two frozen tests needed repair mid-phase, both authoring defects rather than
  behavior: an attribute name and a line length. Each was repaired in its own task with
  the tests re-frozen, and neither weakened an assertion. Recorded here because the
  freeze is meant to make exactly that visible.

## Domain pass

This pass ignored the contract and looked only at the poker.

### Blocker found and fixed: the headline number was measuring the wrong thing

The report led with 96.3% agreement against Pluribus and 93.6% against the human
professionals. Both figures are arithmetically correct and both are close to
meaningless as stated.

1,975 of the 2,758 scored decisions - 72% - are folds, and folds agree 98.6% of the
time. Folding a bad hand from early position is the easiest agreement in poker. Any
chart that is not actively broken will score in the nineties on a pooled rate, because
the pool is mostly junk being thrown away by both sides.

Split by what the player actually did, the picture changes:

| player's action | agreed | of | rate |
|---|---|---|---|
| fold | 1948 | 1975 | 98.6% |
| check | 21 | 21 | 100.0% |
| raise | 465 | 498 | 93.4% |
| call | 160 | 264 | **60.6%** |

**The chart and real players disagree about calling four times in ten.** That is this
phase's actual finding, and the first version of the report buried it under a number
that looked reassuring. The report now prints the split above the disagreement listing
and says in plain language that the low figure is the finding.

This is consistent with what the repo already knows about itself. Phase 05's original
plurality collapse over-folded by 13 points against three-bets before it was re-ruled,
and Phase 06's fallback over-folds postflop by construction. A 60.6% agreement rate on
calls is the same bias showing up against real opponents rather than against the
simulator.

### Second finding: the largest single refusal bucket has no spot key

19 refusals carry `(no expressible spot)` - the position and action sequence do not
describe a spot the chart vocabulary can express at all, which is a different miss from
a spot that is expressible and uncovered. It is the biggest single entry in the
inventory and the one entry nobody can act on, because there is no cell to fill. Filed
as `CORPUS-INEXPRESSIBLE-SPOTS` rather than fixed here: diagnosing it means changing the
Phase 04 spot vocabulary, which is outside this phase.

### Third finding: real hands find three times the coverage gap the simulator does

78 distinct refused spots against real play, versus 22 from self-play, and most of the
78 are marked NEW. The self-play run only reaches the spots its own strategy creates, so
it is blind to the lines real players take. This is the single most useful output of the
phase and it argues that the refusal inventory against real hands, not the self-play
one, should drive whatever chart work comes next.

### What this phase does not establish

A disagreement with a human is not evidence the chart is wrong; these are strong players
but they are not solvers, and the corpus records them playing an opponent pool of one
superhuman bot, which is not the pool the chart was solved for. Agreement with Pluribus
is the closer thing to a correctness signal, and even there 456 scored decisions is a
sample, not a proof.

The 500 hands are a slice. Rates on them carry real sampling error that the report
states denominators for but does not compute intervals around.

## What this review missed, found later

A second review on 2026-08-13, after the phase had closed, read the same work with the
contract set aside again. It found six things this pass did not, which is the honest
measure of what a self-review is worth even when it is done twice with different
questions. They are recorded in the audit packet under `Corrections after the phase
closed` and fixed in MAINT-07 and MAINT-08.

Two of them bear directly on the pass above.

The table in this section pools Pluribus with the human professionals. That is the
averaging judgment call 7 exists to forbid, and this review installed it while fixing the
fold-dominated headline. Split properly the finding survives intact - calls agree 59.5%
for the machine and 60.8% for the humans - which is why it was not caught: the number was
right for the wrong reason.

The gap was also never split by position, and that is where it lives. Human calls agree
53.2% in the big blind and 62-77% everywhere else, and the big blind is also the seat the
chart refuses most often, at 26.6% of its decision points against 1.3% in the hijack.
Refusals sit outside every agreement rate, so the big blind's rate is computed over the
subset of its decisions the chart could answer. This pass asked what the low number
meant and stopped before asking where it was.

A third review on 2026-08-13, by a reviewer told nothing about either of the first two,
went one step further and asked why. The chart is a raked NL25 solve and this corpus is
rake-free, and a raked solution defends the blinds more tightly by construction; Phase
05's own strategy report says so. The chart also solves a 2.5 big blind open against a
sample whose median open is 2.25. Between them those explain most of the gap both
earlier passes treated as a finding about the chart's quality. Written up in the audit
packet and fixed in MAINT-09.

## Blocker status

One blocker was found in the domain pass and fixed inside this phase: the headline
agreement rate was dominated by folds and is now split by the player's action. No rule,
test, or measurement changed - only what the report puts in front of the reader.

No blocker remains open. The two backlog items above are recorded work, not gates.
