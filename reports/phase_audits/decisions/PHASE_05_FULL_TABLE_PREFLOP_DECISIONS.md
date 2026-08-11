# Phase 05 judgment calls

These are the domain choices the committed chart cannot settle by itself.
They are recorded before implementation because a wrong answer found at closeout
is already frozen into a checksummed artifact and into tests.

Every item carries a default.
Defaults stand unless changed, so answering nothing is a valid answer.
Answer by replacing the bracketed value on the `Answer:` line.

Every item carries a reversibility class, which is what the loop driver reads at
stage 2 to decide whether it must stop for a human.

- `runtime-reversible`: the choice only changes behavior at query time, so a later
  edit changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact or fixture
  that later phases are then measured against. The loop halts until a human answers.

Status: answered by Taylor on 2026-08-11.
All eight defaults stand.
Items 5, 6, and 7 are accepted as deliberate deferrals rather than as final
behavior; see "Deferral cost" below for why waiting is safe.

Source of the chart under discussion: GTO Wizard preflop solutions, solution
`Cash6mGeneral_6mNL25R25`, six-max cash, 100bb effective, NL25 rake, cold calls
allowed, 2.5x opens.
36 spots extracted: 5 opens, 15 spots facing a single open, 15 spots where the
opener faces a three-bet, and the big blind facing a small-blind limp.

## 1. Retiring the hand-authored chart

Reversibility: frozen-into-data

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

Reversibility: frozen-into-data

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

Reversibility: runtime-reversible

A spot can say raise 74% / call 25% / fold 1% for one hand.
The bot has to do one thing.

Default at the time: take the highest-weight legal action, and refuse on an exact
tie rather than picking.
The cost was recorded as "unbalanced and exploitable, but never illegal", which was
true and useless: nobody had measured it, including whoever wrote this list.
Changing it later invalidates every Phase 07 comparison baseline, which is why it
was settled before any baseline existed.

Options: highest | random-per-hand-by-weight | refuse-on-any-mix
Answer: [random-per-hand-by-weight, seeded]

Re-ruled on 2026-08-11 after the independent domain review measured the cost of
`highest`, which was accepted on a qualitative description that turned out to
understate it badly.

Folding is one bucket while continuing splits across calling and raising, so the
plurality rule folds hands the chart continues with more than half the time, and
only ever in that direction. Sixteen hand classes across the committed spots fold
where the chart's fold weight is below 0.50, and none go the other way. It folds 77
on the button to a 21.7% hijack open.

The aggregate was the real problem. Over the range the bot opens, fold-to-three-bet
measured 72.8% where the solution is 59.8%. An 8bb three-bet over a 2.5x open risks
8 to win 4, so it auto-profits as a pure bluff above 66.7%: the solution sits
deliberately below that line and the bot sat well above it, handing any opponent a
free profitable bluff with any two cards.

Taylor's ruling: sample by weight, and seed the draw so it stays reproducible. The
seed comes from the hand identifier, hero's seat, the spot key, and the hand class.
Seeding on the hand is what makes it a mix rather than a hash-chosen pure strategy,
and excluding the raw cards is what keeps two suit-relabelled queries in agreement.

## 4. Raise sizing

Reversibility: frozen-into-data

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

Reversibility: runtime-reversible

The chart is 100bb only.
Real stacks are 87bb, 143bb, whatever.
Rounding to the nearest depth is a guess, which the repo bans.

Default: refuse unless the stack is exactly 100bb.
If wrong: the bot refuses most real spots and will look broken to you in practice.
This is the decision most likely to make it feel useless, and the honest fix is
more chart depths later, not a tolerance band now.

Options: exact-only | round-to-nearest | you set a tolerance band
Answer: [exact-only]
Taylor: assume everyone is at 100bb for now; add more solver depths, and some
rounding between them, once the bot is off the ground.

## 6. Straddles and antes

Reversibility: runtime-reversible

Your home game straddles.
The artifact format has no blind-structure field, so a straddled pot would read as
an ordinary one even though the correct ranges differ.

Default: refuse at any table with a straddle or an ante.
If wrong: the bot is silently unusable in exactly your game, which is worse than
being loudly unusable.

Options: refuse | treat-as-normal
Answer: [refuse]
Taylor: same approach as item 5, revisit once there is data for it.

## 7. What "full table" claims

Reversibility: runtime-reversible

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
Taylor: can supply more spots later; same approach as item 5.

## 8. Where the raw export lives

Reversibility: frozen-into-data

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

## Deferral cost of items 5, 6, and 7

Taylor asked whether the deferred capabilities are cheap to add later or whether
waiting builds a wall.
Answered against the code as it stands, they fall into three groups.

Purely additive, no code or schema change at all:

- More stack depths. `PreflopChartLibrary` already indexes artifacts by table size
  and stack depth together, and already has a distinct miss code for a depth it
  has no artifact for. A 40bb chart is a new file in `data/artifacts/preflop/`
  and nothing else.
- More spot classes at an existing depth. Squeeze spots and cold four-bet spots
  are already representable in the current spot-key format, so they are more data
  rather than more format.

Localized change, needs a contract-update but not a rewrite:

- Rounding or bucketing between depths. This one is not additive, because it
  changes the fail-closed guarantee itself rather than extending coverage, so it
  needs the contract to change alongside the lookup. It stays confined to the
  lookup, and `STACK-DEPTH-BUCKETS` already records it. Building it now would
  mean shipping the guessing behavior the repo bans before there is any data to
  calibrate the buckets against.

Schema change, cheap only because of how artifacts are built:

- Straddles and antes need a blind-structure field the artifact format does not
  have, and probably need that field inside the spot key, which would change every
  committed key. That would be an expensive retrofit if artifacts were
  hand-maintained files. It is cheap here because this phase requires the artifact
  to be reproducible from a committed source export by a committed converter, and
  requires `spot_id` to be derived and re-verified rather than hand-written. So a
  format change is a converter change plus one regeneration, not a hand edit of
  thousands of keys.
- Facing a four-bet is the one genuinely structural gap. V1 spot keys allow each
  position at most one entry, so no key exists for it at any depth, and adding it
  means a schema version bump. Already recorded as `SECOND-ORBIT-PREFLOP-SPOTS`.

Conclusion: wait. Nothing on that list gets harder by being deferred, and the two
that need format changes would be guesswork today because there is no straddle or
short-stack chart to define the vocabulary against. The reproducible-artifact
requirement in this phase's contract is what keeps the door open.

## Provenance attestation

Not a choice, but a signature.
The importer's checksum covers weights only, so it cannot verify where a chart
came from.
`source.kind: solver-export` is therefore a human claim.

Attested line:

> The ranges in this artifact were exported from GTO Wizard's preflop solutions
> for solution `Cash6mGeneral_6mNL25R25` at 100bb, from Taylor's own logged-in
> account, on 2026-08-11, and reconciled against the frequencies the site
> displayed for each spot.

Attested by: Taylor Sprouse, 2026-08-11, confirmed in the working session that
supplied the solution URL and requested the extraction.

A reviewer should treat this as a human claim, because it is one.
The importer's `weights_sha256` proves the weights have not been edited since the
artifact was stamped; it proves nothing about where they came from.
