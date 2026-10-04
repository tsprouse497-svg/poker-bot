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
bracket as answered. Every figure is from the ExecPlan's "Where the stage 1 numbers came from", from
the stage 2 review's scripts, or computed here with the arithmetic shown.

## Words used below

- **Solve**: one run of the solver on one flop for one preflop line. It works out every decision to
  the end of the hand, turn and river included.
- **Decision point**: one moment where one player acts, such as "big blind, first to act on this
  flop".
- **Index**: the list of what has been solved and where to fetch it. Today it lives in git.
- **Object storage**: files kept outside git, fetched by a machine that needs them.
- **Line**: the preflop action that led to the flop, such as "button opens, big blind calls".
- **Single-raised pot**: one player raised before the flop and one called. A **three-bet pot** is
  one where the raise was re-raised and then called.
- **Manifest**: a short list in git of what the full index holds, with a fingerprint that proves
  the full index has not changed.

## What is being asked

Ten questions for Taylor, each with a recommendation. Four more are runtime-reversible and proceed
on their stated default. **Read 1 first**: it decides what the campaign is worth at a table, and it
should be settled before any money is.

A scale figure for the cost questions, from phase 16's four first runs on this Mac at five threads:
the fastest flop took 375.6 seconds and the slowest 1,677.4. At those two rates 1,755 flops cost
between 1,755 x 375.6 = 659,178 seconds, about 183 hours, and 1,755 x 1,677.4 = 2,943,837 seconds,
about 818 hours, for one line. That is a range from the four boards on record, not a ceiling: three of
the six board types have never been timed - two-tone unpaired, rainbow paired and trips - and
closure's harvest and the thread fix are not in it.

## 1. What the campaign buys at a table, given that turn and river still refuse

Reversibility: frozen-into-data

Every solve already works out the turn and river; the repo keeps only the flop and throws the rest
away. Today a hand the bot cannot answer is thrown out rather than played, so a flop-only campaign
moves those throw-outs from the flop to the turn on every line it covers, and the bot still reaches
almost no showdowns. The covered line was 16.88 percent of flops in phase 16's 20,000 hands, so most
throw-outs stay where they are, on lines the campaign has not reached.

Counted from GTOpen's tree rules on the committed line, one flop's solve holds 14 flop decision
points, 6,419 turn ones and 1,507,828 river ones. How much the turn costs to keep depends on the file
format, which is part of this answer. In the format the repo saves today, 21 to 31 KB compressed per
decision point, the turn is about 135 to 200 MB a flop and 240 to 350 GB a line. In a compact format
of about one byte a number, it is about 6.6 MB a flop and 11.6 GB a line. The river is about 1.4 GB
a flop and 2.5 TB a line even compact, which is not worth keeping. GTOpen can also save a whole
solve to a file, but that is the full solver memory, about 11 to 12 GB a flop, not measured here. GTOpen's node query walks through dealt cards
(`node_view` in `crates/solver/src/query.rs:490`), so the turn can be read back from the solve; that
is 6,419 queries a flop, and how long they take is measured in the trial.

Options. (a) Flop only, and a later phase for turn and river, which would have to solve every flop
again to get back what this one threw away. (b) Keep the flop and the turn from the same solve, at no
extra solving; the river still refuses. (c) Option (b), and let the old simple play take the river,
check when free and call only a hand nothing beats; on the old simple play everywhere, phase 16's
same 20,000 hands reached 4,543 showdowns. (d) Flop only, with no later phase planned.

(b) and (c) change the contract, which stage 3 can do in this same lane before tests are written.
(c) also reopens phase 16's ruling that turn and river refuse, and adds play rules to a data phase.

Recommendation: (b), with the turn in the compact format and the flop files kept as they are today. The turn costs storage, not solving, and not keeping it
means paying for every solve twice. Decide (c) once (b) exists and can be measured.

Answer: [Ruled by Taylor, 2026-09-26] **Keep the flop, the turn and the river from every solve.** Asked first
with the four options above, he asked whether the river would have to be solved again later, since
the bot needs it to play a hand end to end. He was told it would: not whole flops, but the river parts
from the saved turn, which is most of a solve's work, so about the campaign's machine time again; and
that keeping it costs roughly 2.5 TB a line by a rough estimate that compression may cut. The
coordinator recommended keeping flop and turn and deciding the river after measuring it on the six
trial flops. He chose "Keep the river too", accepting roughly 2.5 TB a line as a rough estimate.
The stage 3 review then found two costs he had not been shown: reading the river out of a solve is
about 1.5 million node queries a flop and may take longer than the solve itself, and five lines come
to about 11.7 TB at one byte a number, which the coordinator put to him as very roughly $250 a month
at AWS's standard storage rate, from memory and to be checked. Re-asked with both, he ruled **keep the
river, but measure first**: the trial measures the harvest time and the real stored size on the six
trial flops, and he confirms the river together with the campaign budget. Decision 15 rules its
precision. Asked next whether phase 21 also teaches the bot to
look up and play the turn and river, he ruled **store now, play next**: phase 21 stores them and a new
phase right after it makes the bot play them. `TURN-AND-RIVER-PLAY-FROM-THE-SAVED-SOLVES-NEEDS-ITS-OWN-PHASE`
carries that until it is declared. The cost he accepted with it, stated in the question: phase 21's
table re-run still shows hands stopping at the turn.
**Restated by Taylor, 2026-10-04:** "we will need to keep the river... i think it'll be hard to play
w/o it." Told the measured cost first (about 22 TB at decision 15's format, 13.5 TB storing one row
per suit-isomorphic combo; the bulk export makes reading it about 43 s a flop instead of about 0.6
to 0.9 hours), and that it goes to Glacier Deep Archive under decision 4's amendment. The campaign
budget ask still shows the measured size and bill.]

## 2. Whether every flop decision is saved, or only the first

Reversibility: frozen-into-data

A flop on the committed line has 14 decision points, seven per player. Phase 16 saved one or two per
flop and the bot gave up one move later on every flop it held. Saving all 14 costs no extra solving,
only room. In git each saved decision costs 486.8 bytes in the index and about 344 in the object list
beside it, 830.8 together; 14 on 1,755 flops is 20.4 MB against 16.0 MB of room, so not even one full
line fits in git. Saving only the two first decisions fits about 5.5 lines, and the bot still gives
up one move in.

Recommendation: save all 14 (and the turn, if 1 is (b)). Decision 3 is what makes the room.

Answer: [Ruled by Taylor, 2026-09-26] Save all 14 flop decision points, per the recommendation, and with decision 1 every turn and river decision point of the same solve.]

## 3. Where the index lives once it outgrows git

Reversibility: frozen-into-data

The rule is the 20 MiB cap on `data/artifacts`, never raised and no git LFS. By decision 2's figures
git cannot hold one closed line. Options. (a) The full index in object storage beside the solves, and
a small manifest in git: per line, the list of flops held and one fingerprint of the index file, so
the repo proves what it points to and the report can count coverage offline. (b) A more compact index
in git, which buys a small multiple, not lines by the dozen. (c) Stay in git and stop short of one
line.

Recommendation: (a). The gate keeps running offline against the committed sample, as it does today.

Answer: [Ruled by Taylor, 2026-09-26] (a): the full index lives in object storage beside the solves, and git holds a manifest per line - the flops held and one fingerprint of the index file.]

## 4. Where the solved data is stored, and who pays for it

Reversibility: frozen-into-data

Today every object sits in a folder on this Mac, `~/poker-bot-solve-objects/postflop`, with no copy
anywhere else. Each committed object is 21 to 63 KB compressed and holds one or two decision points;
a closed flop is larger, and a flop with its turn is about 6.6 MB in a compact format or 135 to 200
MB in today's, so decision 1's format choice sets the storage bill. The location is
written into the index, and every machine that plays has to fetch from it. Moving later is a scripted
rewrite of the index, not a re-solve, but it is still worth choosing once.

Recommendation: a private storage bucket at the same cloud provider as the machine (decision 5), on
your account, read by a fetch command the repo commits.

Answer: [Ruled by Taylor, 2026-09-26] A private storage bucket at the same provider as the machine, on his account, read by a fetch command the repo commits. With decision 5, that is AWS.
**Amended by Taylor, 2026-10-04:** the bucket stays AWS and stays his, but the turn and river
objects are stored in the Glacier Deep Archive class (about $22 a month for about 22 TB, against
about $500 in the standard class), written straight from the solve machines, and the flop objects and
index stay in the standard class. Reading a turn or river object back needs an archive restore first
(bulk, about $55 for all of it, 12 to 48 hours); serving them to players is a later phase's design
(`PEOPLE-ACROSS-THE-US-PLAY-AGAINST-THE-BOT-AND-NO-PHASE-OWNS-IT`). He answered "for turn/river in
glacier deep archive that prolly works."]

## 5. Which cloud provider, and which machines to try

Reversibility: frozen-into-data

The machine is written into every committed solve record, and the proof that a solve repeats exactly
holds only on the machine it ran on, so the choice is part of the data. Every candidate must have the
memory for the biggest flop of every line admitted. On the committed line that is 12.87 GB on
`2d2h2s`, about 32.2 GB of RAM under the repo's 40 percent guard; on small blind against big blind,
first by decision 9's recommended order, it is roughly 18.0 GB, about 45 GB of RAM.

Recommendation: a provider you already have an account with, and three CPU machines of 64 GB of RAM
or more, with at least one Intel or AMD and one ARM, since GTOpen's own comment says the work is
limited by memory speed rather than core count. The names are yours to pick; I have no prices I can
vouch for.

Answer: [Ruled by Taylor, 2026-09-26] **AWS.** The question proposed three CPU machines of 64 GB of RAM or
more, at least one Intel or AMD and one ARM, and he picked the provider on that proposal; decision 7
adds one GPU machine. Coordinator's procedure, not his ruling: the specific machine types and their
hourly prices go to him before anything is rented, because renting is spend.
**Re-ruled by Taylor, 2026-10-04: RunPod** for the trial, starting from a GPU large enough for the
small blind line. AWS's new-account quota was refused (5 to 32 vCPU, appeals open since 2026-09-26),
and a comparison of providers on what a new account can run at once put RunPod first: card-only
sign-up, an $80 an hour default spend cap, no egress charge. Lambda Cloud is his standing backup
account; on 2026-10-04 every Lambda type large enough was out of capacity. He has funded the RunPod
account with $150. The specific machine type and hourly price still go to him before anything is
rented. Whether the trial cap is $100 or $150 is unanswered.]

## 6. The trial budget

Reversibility: frozen-into-data

Where the campaign stops is what gets committed, so a budget shapes the data. No honest campaign
total can be asked yet: the only costs on record are laptop figures. So the contract asks two
budgets. This one covers every rented solve before the campaign: on each candidate machine at most 15
short timing runs of 100 rounds and one full solve of the benchmark flop; then on the chosen machine
eight solves to prove it repeats itself (phase 16's four flops twice), six flops of the six board
types, which become the campaign's first six, and the six longer settling runs of decision 13. At
this Mac's rates of 1.34 to 4.93 seconds a round, with three candidates: 3.1 to 7.6 hours of timing
and benchmark across the three; 2.1 hours for the eight repeat solves, from their recorded times; 0.6
to 2.8 hours for the six flops; and 2.7 to 9.9 hours of settling runs. About 8 to 22 hours in all. A
rented machine may be faster; the trial measures that. Reading the turn back out of the six flops,
6,419 queries each, is extra and unmeasured. A graphics-card trial, if 7 is yes, comes out
of this budget too. The campaign budget is asked separately, once the six flops have priced a line.

Recommendation: an amount you would be comfortable losing on a trial, since it buys measurements
rather than coverage. The figure is yours; I cannot price a machine you have not picked.

Answer: [Ruled by Taylor, 2026-09-26] **$100** trial budget, covering every rented run before the campaign, the GPU trial included. The campaign budget is asked separately once the trial has priced a line.
**Confirmed for RunPod by Taylor, 2026-10-04:** the cap stays $100 although he funded the RunPod
account with $150; "100 cap seems reasonable."]

## 7. Whether to try GTOpen's graphics-card path

Reversibility: frozen-into-data

GTOpen can solve on an NVIDIA graphics card, and the engine is written into every solve record. Two
things count against it here. Its graphics-card code adds numbers in an order that is not fixed
(`atomicAdd` in `kernels.cu`), so two runs of the same flop may not match, and this repo requires
that they do. And by GTOpen's own estimate the biggest committed-line flop needs about 33.7 GB of card
memory, so only cards of 40 GB and up qualify. Its speed claims are in its README and have never been
measured here.

Recommendation: not now. Run on ordinary processors, and try a card only if their projected cost is
too high; that trial would test repeatability before speed.

Answer: [Ruled by Taylor, 2026-09-26] **Try it in the trial**, against the recommendation, out of the $100.
Repeatability is tested first, as the option he chose said. Coordinator's reading, not his ruling: the
card must hold the memory bar, about 47.2 GB by GTOpen's estimate for small blind against big blind,
so 48 GB or more; and a GPU that does not repeat itself is recorded as a finding and goes back to him
before it is used for the campaign.]

## 8. How accurate each flop must be

Reversibility: frozen-into-data

Phase 16 ruled a target of 0.3 percent of the pot, a cap of 1,200 rounds, and refusal of any flop
worse than 1 percent. All four of its flops reached the target in 280 to 340 rounds. The one test of
going further, `deep_convergence_check.json`, ran `9c8c7c` to 1,200 rounds: 0.048 percent, 4.8 times
as long (1,812.6 seconds against 375.6). Hands that always bet or always check barely moved, at most 0.042. Hands
that mix did: 79 of the 152 hand groups moved by more than 0.05, the largest by 0.467. So at 0.3
percent the bot knows what to do and is still rough on how often to mix.

Options. (a) Keep 0.3 percent, 1,200 and 1 percent. (b) A tighter target, costing several times the
solving per flop, which buys fewer flops for the same money.

Recommendation: (a) for this campaign, since more flops beats finer mixing on the flops you have,
with decision 13's settling runs measuring the gap.

Answer: [Ruled by Taylor, 2026-09-26] (a): keep 0.3 percent of the pot, the 1,200-round cap and refusal above 1 percent.]

## 9. Which preflop lines go first

Reversibility: frozen-into-data

Phase 16 ruled a method: rank lines by how often they reach a flop and can be served. Two sources
disagree. The public set of real hands ranks button-open, big-blind-call first, but real players were
retired as a yardstick with phase 17, and its counts past sixth place are six hands or fewer. The
committed chart only ever calls an open from the big blind, so the single-raised lines it plays are
the five where the big blind defends. How often each whole line happens under the chart, as a share
of all hands: small blind opens and big blind calls 5.53 percent, button 3.66, cutoff 2.75, hijack
2.71, lojack 2.42.

Recommendation: rank by the chart's own figures, print the real-hand order beside them, and admit
only the five single-raised lines in this phase. Three-bet pots need new range work and their own
bet sizes, so they are not admitted here; a later decision or phase adds them.

Answer: [Ruled by Taylor, 2026-09-26] Rank by the chart's own line figures and admit only the five single-raised lines: small blind, button, cutoff, hijack and lojack opening against the big blind, in that order. Three-bet pots are not admitted in this phase.]

## 10. The bet sizes for lines other than the committed one

Reversibility: frozen-into-data

Phase 16 ruled one set of bet sizes, for button against big blind: a third and three quarters of the
pot on the flop, two thirds and one and a quarter on turn and river, raises of two and a half times.
No ruling covers any other line, and the sizes are written into every solve. Using the same sizes
everywhere keeps every line comparable; tuning sizes per line is a research project of its own.

Recommendation: the same sizes and the same settings for every single-raised line, the `donk`
setting included, which is empty in `solve_config.json` today; it may play differently when the
raiser acts first after the flop, as the small blind does against the big blind.

Answer: [Ruled by Taylor, 2026-09-26] The same bet sizes and settings as `solve_config.json` for every single-raised line, the empty `donk` setting included.]

## 11. How many solves run at once on one machine

Reversibility: runtime-reversible

Default: one. Two at once would split the machine's threads and make every saved timing describe a
half machine. It changes only how fast the campaign runs, not what it commits.

Answer: [ ]

## 12. The thread count

Reversibility: runtime-reversible

Default: the fastest count measured on each machine, as the contract requires, recorded beside every
timing. That it does not change the answer is proved on this Mac; on the rented machine it is assumed
from GTOpen's code, and the repeat solves there run at the chosen count only.

Answer: [ ]

## 13. How settling is measured

Reversibility: runtime-reversible

Default: one flop of each of the six board types solved on to the 1,200-round cap, its mixing
compared with the committed flop, printed as a finding and never used to reject a flop. Counted in
decision 6's budget.

Answer: [ ]

## 14. The memory guard's five percent over-read

Reversibility: runtime-reversible

The guard reads the server's memory figure in megabytes of 1,048,576 bytes where the server means
1,000,000, which over-reads by 4.86 percent. Default: keep the reading and the 0.40 ceiling, and state the margin in
every refusal, the third of the three repairs its backlog entry names. It stays runtime-reversible
only if stage 4's frozen tests do not pin the reading; if they do, it is reclassified before the
freeze.

Answer: [ ]

## 15. How precisely the turn and river are stored

Reversibility: frozen-into-data

Raised by the stage 3 review: the storage figures Taylor ruled decision 1 on assume about one byte a
number, which rounds every frequency to steps of about 0.4 percent, coarser than the flop files'
thousandths, and no one had asked him. Put to him with three options: one byte, about 2.5 TB of river
a line; two bytes, precise to about 0.002 percent, about 5 TB a line; four bytes, the solver's full
precision, about 10 TB a line. The flop keeps today's format. Recommendation: two bytes.

Answer: [Ruled by Taylor, 2026-09-26] **Two bytes a number** for the turn and river. The review's
per-line figures at one byte are 3.48, 2.57, 2.10, 1.88 and 1.62 TB for the five lines, 11.65 TB in
all, so about 23 TB at two bytes, measured on the trial flops before the campaign budget.
**Re-ruled by Taylor, 2026-10-03:** every turn and river frequency is rounded to a tenth of a
percent, which is the flop's thousandths, with the flop's rule that the largest entry pays the
rounding residue so a decision still sums to one. Storage stays two bytes a number. He proposed the
tenth himself and asked for it to be evaluated; he was told the solve's own noise is far coarser
(decision 8's deep convergence moved a mixing group by up to 0.467), that 1,001 levels do not fit
one byte so the saving comes only from compression or a custom packing of about 10 bits (roughly 14
TB against 23 TB for the five lines), and was recommended to keep two bytes and measure standard
compression on the trial flops before any custom format. He answered "yes".]


## 16. How a raise is named in a spot key

Reversibility: frozen-into-data

Raised by the stage 4 round 3 review as its one blocker: a flop object cannot be checked by its
contents while some of its decision points have no key. The solve is configured with
`raise: "2.5x"`, and a spot key carries every size as a percent of pot to a hundredth, refusing
anything finer (`size_pct` in `solver_artifacts/postflop_harvest.py`, `render_size_bb` in
`solver_artifacts/spot_key.py`). A 2.5x raise over the committed 33 percent bet is 4.5375bb into
7.315bb, 62.030075... percent of pot, so every decision point after a raise is unnameable and the
bot cannot look up the node after its own raise.
`THE-KEY-CANNOT-NAME-A-RAISE-THE-COMMITTED-MENU-HOLDS` carries the diagnosis.

Options. (a) Name a raise in the key by the multiplier the solve configures, such as `2.5x`, which
is exact. Bets keep their percent of pot. (b) Round a raise's percent of pot to a hundredth, the
rounding the repo has twice refused by name because two different sizes could share a key.

Recommendation: (a).

Answer: [Ruled by Taylor, 2026-10-03] (a): a raise is named by its multiplier. Put to him in plain
words, he answered "if path A is recommended here that's fine."]

## 17. Whether a checked-through street clears the initiative

Reversibility: frozen-into-data

Found 2026-10-04 by comparing our pinned GTOpen (`4aee435`, 2026-07-23) with its upstream. At the
pin, `tree.rs` carries the last aggressor through a street both players check, and treats an out of
position bet into that aggressor as a donk, whose list the committed configuration leaves empty. So
when in position bets the flop, out of position calls and the turn checks through, out of position
can only check the river. Upstream fixed this in `85b0a692` (2026-09-03, its author's "round-2 audit
high finding"): a checked-through street clears the initiative, so that river bet uses the normal
sizes. Measured by a port of the tree builder that matches the Rust build to the byte: per river
card, 6 of 94 river street starts change; button-line nodes rise 3,921,411 to 4,144,704 (+5.7%),
river decision points 1,477,056 to 1,549,968, turn unchanged; the small blind line's worst flop
needs 51.24 GB of GPU memory against 48.50. The 44 river starts that follow a called turn bet stay
check-only under both rules, by design. Reach share of the changed spots is estimated at 10 to 18
percent of hands on `Kh7d2c`, not measured.

Options. (a) Keep the pin's tree. (b) Apply only upstream's tree fix to a local clone, about 40
lines, leaving every other upstream change out. (c) Allow every OOP turn and river lead through the
donk lists, +59% arena and 75.64 GB of GPU memory on the small blind line.

Recommendation: (b), because a gap baked into every campaign solve costs the whole campaign again to
remove.

Answer: [Ruled by Taylor, 2026-10-04] (b). Shown the three options with their costs and the exact
change, he answered "ah ok. yes" and asked for the fix to be made in every place that matters, with
each phase and document that needs it updated, carefully and within the repo's practices. Whether to
also take upstream's deterministic GPU fold sum is a separate question, ruled as decision 18.
**What the ruling covers, from the handoff Taylor gave the session that carried it out, 2026-10-04:**
phase 16's four committed cells, index, objects list and `determinism.json` were solved on the old
tree and cannot reproduce on the new one, and "re-solving them is part of this ruling". True donks,
a lead straight after calling a bet, stay out by design (option (c) declined).]

## 18. Whether to take upstream's deterministic GPU fold sum

Reversibility: frozen-into-data

At the pin, GTOpen's postflop GPU kernel `up_fold` (`gpu/kernels.cu:143-148`) sums with float
`atomicAdd` in shared memory, so the order is not fixed and two GPU runs will likely differ in the
last bits; the contract makes a GPU that does not repeat itself a finding, not a campaign machine.
Upstream `8ff89f42` (2026-09-07) replaced it with per-card sums in fixed hand order and a fixed-shape
total, and its own test asserts two GPU runs give equal arenas on one card. The fix isolates to two
files, about +42/-18, and does not touch the CPU engine. Untested here: it compiles only on a CUDA
machine at run time, and nothing claims repeatability across GPU models.

Recommendation: take it into the same local clone as decision 17's tree fix, and prove it on the
first rented GPU by solving one flop twice.

Answer: [Ruled by Taylor, 2026-10-04] Take it. "yea for graphics card repeat i'm fine with that."]
