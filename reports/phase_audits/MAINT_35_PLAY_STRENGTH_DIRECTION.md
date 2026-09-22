# MAINT-35 audit packet: the goal is a bot that plays, not a bot that teaches

Taylor ruled on 2026-09-21 that this repo builds a bot that plays really good poker, and that the
training product is backlogged until it does. His reason was specific rather than general: recent
decisions refused spots the solve takes, or accepted distortions in the committed ranges, because
they would not make sense for a trainee.

This task makes that the repo's stated purpose. It changes no strategy, no artifact, no code and no
test. Every acceptance it names stays accepted and is filed for later; none is reversed.

## What shipped

- `AGENTS.md`, `README.md` and `docs/ARCHITECTURE.md` state the new purpose. The `poker_training_bot`
  package keeps its name, which Taylor ruled.
- `AGENTS.md`'s flat list of six prohibitions became five boundaries that each name the phase that
  lifts them, because two of them now have an answer and a flat list cannot express that.
- `docs/ROADMAP.md` and `docs/V2_ROADMAP.md` rewritten around playing strength, with every figure in
  them re-derived rather than carried.
- Phase 15, The Drill, retired. Phases 18 (The Yardstick), 19 (Heuristics And Merged Charts) and 20
  (The Home Game) declared, with contracts, `depends_on` and loop-policy entries.
- Nine backlog entries filed, plus four alignment items.

## The boundary that moved furthest

`No heuristic guessing for missing preflop chart spots` was ruled **holds permanently**. It now lifts
at phase 19, and holds exactly as written until then.

The permanent framing was written for a tool that reports on hands already played, where refusing
costs nothing. A bot that has to act at a table cannot refuse. Taylor's ruling was that the
heuristics, and the merge of solved charts with unsolved spots, become their own phase rather than a
change made here, which is why fail-closed survives this task untouched.

## The two arguments that were welded together

The clearest instance of what Taylor objected to is the big blind's tight defence. It was accepted on
two arguments in one ruling: the bot has no postflop strategy, **and** a chart that taught wide
big-blind defence would be teaching a student to take marginal hands out of position to flops this
bot cannot help them play. The first still stands. The second has expired.

Taylor ruled that it reopens **after** phase 16 has flop cells, so that it is decided against a
measured number rather than against an argument. The entry records that reopening is blocked twice
over: the phase 14 contract forbids widening the flat by hand, and that contract is at its line cap,
so the amendment cannot land until the fold-in rewrite has run.

The same shape was found in the withheld five-bet jams, which the independent review caught and the
eight original entries had missed.

## What the repo cannot say about itself

Nothing here measures how well the bot plays. Every published number is agreement with somebody
else's decisions, or coverage of a decision space, and neither is a win rate. The profile comparison
report says so in its own words: producing the other kind of number needs an opponent with a
strategy, and this repo does not have one. That gap is why phase 18 exists and why phase 19 depends
on it - a merge of heuristics with solved cells can otherwise only be asserted to help.

## The figures, and why none of them was copied

This repo's prose has gone stale repeatedly, and `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES`
is its own name for it. Every lane was required to re-derive rather than quote, and the independent
reviewer re-derived the lot again. Twenty figures in the two roadmaps were wrong. The ones that
mattered: the committed chart was described as answering 36 spots when it answers 156; its corpus
refusals were described as 290 over 78 rows when they are 194 over 75; a ruling stated that limps are
in the solved tree when the export's own source card has them off; and the postflop fallback was
described as never betting when it does bet on turn and river, the flop being the street where its
path is closed.

Two figures this task wrote were themselves wrong and were caught by the review. The exclusion census
named three buckets where there are five, in the entry whose subject is how that census is read. And
`arrival_ppb` was cited as the source of two different measurements when it contains one.

## Independent review

Recorded in full at `reports/phase_audits/reviews/MAINT_35_PLAY_STRENGTH_DIRECTION/independent-review.md`.
A read-only agent that wrote none of the work; the repairs were made by a fourth agent that wrote
neither the work nor the review. One blocker, eight non-blockers, four alignment items, all resolved
or filed.

The review's most valuable finding was not on its list. The 2026-08-15 ruling kept table automation
out on terms-of-service and account-risk grounds, and those attach to the platform rather than to the
guest list, so narrowing the venue to a private home game does not answer the reason Taylor gave.
It was put to him in those words. He ruled **proceed, risk accepted**, and it is recorded everywhere
as an accepted risk rather than a resolved one.

The same exchange settled a second ambiguity: the bot is handed the game's URL and joins the table.
Taylor said the question may stay open for now, so it is recorded as a working reading for phase 20's
stage 1 to confirm, committing to no platform.

## The correction this packet owes its own reader

A figure in this session's own reporting was wrong before the review caught it. The pruning
experiment that would price the ladder inversions was described as never having been run. It was run
on 2026-09-02 and came back negative: every inversion reproduced with pruning off, at a better
convergence gap than the committed solve. Two shipped backlog entries still tell a reader it has
never been run, which is where the error came from. What is genuinely unrun is the same experiment
against the chart that ships, since 2026-09-02 predates the MAINT-34 re-solve.

## What no reviewer could check

Whether these are the right five phases. The graph after this task is a judgement about what a bot
needs in order to play well, and nothing in the repo can falsify it. What the repo can check is that
the graph is consistent, that nothing dangles, and that every number written down is one somebody
re-derived. Those it checks.

## Filed rather than fixed

Nine backlog entries carrying the teaching-motivated acceptances, and four alignment items: the
packaging metadata, a frozen test docstring, the backlog's cost language, and nine new deferred
entries hanging off phases with nothing that would notice if those phases close without them.
