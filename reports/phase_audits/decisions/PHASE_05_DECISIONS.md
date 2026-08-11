# Phase 05 judgment calls

These are the domain choices the committed chart cannot settle by itself.
They are recorded before implementation because a wrong answer found at closeout
is already frozen into a checksummed artifact and into tests.

Every item carries a default.
Defaults stand unless changed, so answering nothing is a valid answer.
Answer by replacing the bracketed value on the `Answer:` line.

Source of the chart under discussion: GTO Wizard preflop solutions, solution
`Cash6mGeneral_6mNL25R25`, six-max cash, 100bb effective, NL25 rake, cold calls
allowed, 2.5x opens.
36 spots extracted: 5 opens, 15 spots facing a single open, 15 spots where the
opener faces a three-bet, and the big blind facing a small-blind limp.

## 1. Retiring the hand-authored chart

The committed `six_max_100bb_core.json` is hand-authored and covers 3 spots.
The new export covers 36 spots at the same table size and stack depth, and the
two overlap on the cutoff open, the button open, and the big blind facing a
cutoff open, which the chart library treats as a duplicate-spot error.
So they cannot both stay.

This matters beyond plumbing.
The hand-authored chart was widened during Phase 04 because a reviewer said the
big blind should defend at least 45% against a cutoff open.
The real solution defends 31.5%, because rake makes big-blind defence much
tighter than the rake-free heuristic implies.
That Phase 04 change was a confident correction in the wrong direction.

If wrong: keeping both breaks the gate; keeping only the hand-authored one throws
away the real data.

Options: retire-hand-authored | keep-both-somehow | you decide per spot
Answer: [retire-hand-authored]

## 2. Rake structure

The solution is solved with NL25 rake.
Raked ranges are tighter than rake-free ones, most visibly in the blinds, so the
bot will fold more from the big blind than a rake-free chart would.
Your home game's rake is probably not NL25's.

If wrong: the bot plays a slightly-too-tight version of correct poker.
That is a much smaller error than the alternatives, but the report and the audit
packet should say out loud which rake the ranges assume.

Options: accept-NL25-rake | you supply a rake-free or different-rake export
Answer: [accept-NL25-rake]

## 3. Mixed frequencies

A spot can say raise 74% / call 25% / fold 1% for one hand.
The bot has to do one thing.

Default: take the highest-weight legal action, and refuse on an exact tie rather
than picking.
If wrong: the bot is unbalanced and exploitable, but never illegal and never
silently arbitrary.
Changing this later invalidates every Phase 07 comparison baseline.

Options: highest | random-per-hand-by-weight | refuse-on-any-mix
Answer: [highest]

## 4. Raise sizing

Spot keys carry no raise size, so the artifact cannot hold one.
But the strategy has to raise some amount, and the export does record what the
solution used: 2.5x opens, 3.5x from the small blind, three-bets of 8bb in
position and 11bb from the small blind and 13.5bb from the big blind, 10.5bb for
the big blind against a small-blind open.

Default: commit those numbers as a sizing table with its own provenance, and
refuse any raise the table does not cover.
This is the difference between sizings that came from the solver and sizings a
model made up, which was the original risk here.

If wrong: every preflop pot is the wrong size, which changes all postflop play.

Options: source-sizings | flat-3x | you give me numbers
Answer: [source-sizings]

## 5. Stacks that are not exactly 100bb

The chart is 100bb only.
Real stacks are 87bb, 143bb, whatever.
Rounding to the nearest depth is a guess, which the repo bans.

Default: refuse unless the stack is exactly 100bb.
If wrong: the bot refuses most real spots and will look broken to you in practice.
This is the decision most likely to make it feel useless, and the honest fix is
more chart depths later, not a tolerance band now.

Options: exact-only | round-to-nearest | you set a tolerance band
Answer: [exact-only]

## 6. Straddles and antes

Your home game straddles.
The artifact format has no blind-structure field, so a straddled pot would read as
an ordinary one even though the correct ranges differ.

Default: refuse at any table with a straddle or an ante.
If wrong: the bot is silently unusable in exactly your game, which is worse than
being loudly unusable.

Options: refuse | treat-as-normal
Answer: [refuse]

## 7. What "full table" claims

Default: every seat at a six-handed 100bb table can be asked and gets either a
chart-backed decision or an explicit refusal, and the report shows which.
It does not claim every situation is covered.

Still uncovered after this phase: squeeze spots (an open, a cold call, then hero),
cold four-bet spots, and anything facing a four-bet, which the spot-key format
cannot express at all.

If wrong: nothing breaks, but the phase title would promise more than the gate
proves.

Options: askable | fully-covered
Answer: [askable]

## 8. Where the raw export lives

`data/raw/**` is forbidden scope, so the GTO Wizard export cannot be committed
there.
But an artifact with no committed input is not reproducible.

Default: commit the export under `data/artifacts/preflop/sources/` next to a
converter script, so re-running the converter reproduces the artifact exactly.
If wrong: the artifact becomes a file nobody can regenerate or diff against its
origin.

Options: commit-under-artifacts-sources | widen forbidden scope to allow data/raw
| artifact only, no committed input
Answer: [commit-under-artifacts-sources]

## Provenance attestation needed

Not a choice, but a signature.
The importer's checksum covers weights only, so it cannot verify where a chart
came from.
`source.kind: solver-export` is therefore a human claim.

Confirm this line for the audit packet, or correct it:

> The ranges in this artifact were exported from GTO Wizard's preflop solutions
> for solution `Cash6mGeneral_6mNL25R25` at 100bb, from Taylor's own logged-in
> account, on 2026-08-11, and reconciled against the frequencies the site
> displayed for each spot.

Attested by: [ ]
