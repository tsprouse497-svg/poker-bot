# Phase 21 judgment calls

The choices the campaign cannot make for itself. No test settles them: a campaign that solves the
wrong lines, stores its data somewhere nobody can fetch it, or spends past what Taylor meant passes
as green as one that does not.

Every item carries a class, quoted from `docs/LOOP.md`:

- `runtime-reversible`: "the choice only changes behavior at query time, so a later edit can change
  it. The loop takes the recorded default, proceeds, and reports what it chose."
- `frozen-into-data`: "the choice gets written into a committed artifact or fixture that later
  phases are then measured against. The loop halts until a human answers."

A `frozen-into-data` item's `Answer:` bracket stays empty until Taylor rules; the loop reads a filled
bracket as answered. Every figure below is from the ExecPlan's "Where the stage 1 numbers came from"
or is computed here from those, with the arithmetic shown.

## What is being asked

Nine questions for Taylor, each with a recommendation. Four more are runtime-reversible and proceed
on their stated default. **Read 1 first**: it is about what the campaign can buy at a table at all,
and it should be settled before a spending cap is.

A scale figure for every cost question below, from phase 16's four committed first runs on this Mac
at five threads: the fastest board took 375.6 seconds and the slowest 1,677.4. At those two rates,
1,755 flops cost between 1,755 x 375.6 = 659,178 seconds, about 183 hours, and 1,755 x 1,677.4 =
2,943,837 seconds, about 818 hours, for one preflop line. That is solve time only, before closure's
harvest and before the thread fix, and it is why the machine question matters.

## 1. What the campaign buys at a table, given that turn and river still refuse

Reversibility: frozen-into-data

Phase 16's decision 1 ruled flop only, and turn and river refuse by their own codes. A refusal voids
the hand. So a perfectly covered and closed flop moves every voided hand from the flop to the turn:
the table re-run in the contract will still show almost no showdowns, as phase 16's showed none. The
campaign is the prerequisite for a bot that plays postflop, and on its own it does not make one.

Options. (a) Keep phase 21 flop-only, say so in its report, and declare a follow-on phase for turn
and river play to run right after it. (b) Widen phase 21 to let the old check-through fallback play
turn and river after a closed flop, so hands reach showdown; that reopens phase 16's decision 1 and
adds behaviour work to a data phase. (c) Accept flop-only with no follow-on for now.

Recommendation: (a). The campaign is worth running because every later postflop phase needs it, but
you should not set a spending cap believing it makes the bot play hands to the end.

Answer: [ ]

## 2. Whether every flop decision is saved, or only the first

Reversibility: frozen-into-data

A flop on the committed line has 14 decision points, seven for each seat. Phase 16 saved one or two
per board and the bot gave up one move later on every board it held. Saving all 14 costs no extra
solving - they come out of the same solve - but it costs index space: at 486.8 bytes an entry, 14
entries on 1,755 flops is 11.96 MB a line against 16,032,570 bytes of room in git, so about 1.3
lines fit; saving only the two first decisions fits about 9.4 lines, and the bot still gives up one
move in.

Recommendation: save all 14. Nine lines the bot cannot play past one move are worth less than one
it can. Decision 3 is what removes the space limit.

Answer: [ ]

## 3. Where the index lives once it outgrows git

Reversibility: frozen-into-data

The rule is the 20 MiB cap on `data/artifacts`, no raising it and no git LFS. Options. (a) Keep the
full index in object storage beside the solves, and commit a small manifest in git: each covered
line, its counts, and one digest of its index file, so the repo still proves what it points to.
(b) Keep the index in git in a more compact form, which buys a small multiple, not lines by the
dozen. (c) Stay within git's room and stop at about 1.3 closed lines.

Recommendation: (a). The gate keeps running offline against the committed sample, as it does today.

Answer: [ ]

## 4. Where the solved data is stored, and who pays for it

Reversibility: frozen-into-data

Today every object sits in a folder on this Mac, `~/poker-bot-solve-objects/postflop`, and no remote
store exists. Each committed object is 21 to 63 KB compressed and holds one or two decision points;
a closed board holds 14, so its size is measured in part 2 rather than guessed here. The location is
written into the index, and every machine that plays has to fetch from it.

Recommendation: a storage bucket at the same cloud provider as the machine (decision 5), on your
account, private, read by a fetch command the repo commits. Moving it later means rewriting every
index entry, which is why it is asked now.

Answer: [ ]

## 5. Which cloud provider, and which machines to try

Reversibility: frozen-into-data

The machine is written into every committed solve record, and the determinism proof only holds on
the machine it ran on, so the choice is part of the data. Every candidate must hold the memory bar:
the largest planned solve on the committed line is 12.87 GB, on `2d2h2s`, which needs about 32.2 GB
of RAM under the repo's 40 percent guard. Each candidate solves the same benchmark flop, `Kh7d2c`,
and is ranked on cost per closed flop.

Recommendation: a provider you already have an account with, and three CPU machines of 64 GB of RAM
or more, at least one x86 and one ARM, since GTOpen's own comment says the work is limited by memory
speed rather than core count. The provider and machine names are yours to pick; I have no prices I
can vouch for.

Answer: [ ]

## 6. The benchmark cap

Reversibility: frozen-into-data

Where the campaign stops is what gets committed, so a cap shapes the data. No honest campaign total
can be asked yet: the only costs on record are laptop figures. So the contract asks two caps. This
one covers every rented solve before the campaign: on each candidate machine at most 15 short timing
runs of 100 rounds and one full solve of the benchmark flop; then on the chosen machine 14 solves -
phase 16's four flops twice, to prove the machine repeats itself, and one flop of each of the six
board types, which become the campaign's first six flops. At this Mac's rates - 1.34 to 4.93
seconds a round, one full solve 6 to 28 minutes - that is about 5 to 14 hours of machine time with
three candidates: 1,500 timing rounds and a 28-minute benchmark on each, 0.6 to 2.1 hours plus 0.5,
and 14 solves of 6 to 28 minutes on the chosen one, 1.5 to 6.5 hours. A rented machine may be
faster; that is what the trial measures. The campaign cap is asked
separately, once those six flops have priced a whole line.

Recommendation: a cap you would be comfortable losing on a trial, since it buys measurements rather
than coverage. The figure is yours; I cannot price a machine you have not picked.

Answer: [ ]

## 7. Whether to try GTOpen's GPU path

Reversibility: frozen-into-data

GTOpen can solve on an NVIDIA card, and the engine is written into every solve record. Two things
count against it here. Its GPU code adds numbers in an order that is not fixed (`atomicAdd` in
`kernels.cu`), so two runs of the same flop may not match, and this repo requires that they do. And
by GTOpen's own estimate the largest flop needs about 33.7 GB of card memory, so only 40 GB-and-up
cards qualify. Its speed claims are in its README and have never been measured here.

Recommendation: not now. Run the campaign on CPU, and try the GPU only if the CPU projection comes
in too expensive; that trial would test repeatability before anything else.

Answer: [ ]

## 8. How accurate each flop must be

Reversibility: frozen-into-data

Phase 16 ruled a target of 0.3 percent of the pot, a cap of 1,200 rounds of solving, and refusal of
any flop that finishes worse than 1 percent. All four of its boards reached the target in 280 to 340
rounds. These are code constants today and would carry over silently.

Recommendation: keep all three. Changing them now would make campaign flops and phase 16's flops
different kinds of answer.

Answer: [ ]

## 9. Which preflop lines go first

Reversibility: frozen-into-data

Phase 16 ruled a method: rank lines by how often they reach a flop and can be served. Two sources
disagree. The public set of real hands ranks button-open, big-blind-call first; the committed chart's
own reach puts other lines higher. Real players were retired as a yardstick with phase 17, and the
real-hand counts past sixth place are six hands or fewer, too few to rank on. The fourth real-hand
line is a small-blind limp the chart cannot supply, so it is excluded either way.

Recommendation: rank by how often the committed chart itself reaches each two-player flop line,
print the real-hand order beside it, and start with single-raised pots. Three-bet pots need new range
work and follow once the single-raised lines are done.

Answer: [ ]

## 10. How many solves run at once on one machine

Reversibility: runtime-reversible

Default: one, unless the box has room for the memory bar twice over, in which case two, with the
guard applied to their sum. It changes only how fast the campaign runs, not what it commits.

Answer: [ ]

## 11. The thread count

Reversibility: runtime-reversible

Default: the fastest count measured on each machine, as the contract requires, recorded beside every
timing. The answer does not depend on it; the part 1 re-solve proves that on this Mac.

Answer: [ ]

## 12. How settling is measured

Reversibility: runtime-reversible

Default: one flop from each of the six board types solved on to the 1,200-round cap, and its action
frequencies compared with the committed cell, printed as a finding and never used to reject a cell.

Answer: [ ]

## 13. The memory guard's five percent over-read

Reversibility: runtime-reversible

The guard reads the server's memory figure as binary megabytes where the server means decimal, which
over-reads by 4.86 percent. Default: keep the reading and the 0.40 ceiling, and state the margin in
every refusal, the third of the three repairs its backlog entry names. Loosening the guard is a
separate call and is not made here.

Answer: [ ]
