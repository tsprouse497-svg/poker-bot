# Phase 12 judgment calls

These are the choices that decide what a spot key can say. The two defects are not in
question anywhere below; what is in question is the shape the fix takes, and three of those
choices go into a committed artifact that proposed phase 14 is then measured against.

Every item carries a reversibility class, which the loop driver reads at stage 2 to decide
whether it must stop for a human.

- `runtime-reversible`: the choice only changes behaviour at query time, so a later edit
  changes it. The loop takes the default, proceeds, and reports what it chose.
- `frozen-into-data`: the choice is written into a committed artifact that every later phase
  is then measured against. The loop halts until a human answers.

Three items are `frozen-into-data`, and all three are the rendered form of the key itself.
The key is stamped on every spot in the artifact and re-derived from live game state on every
lookup, so a later change to it is a re-derivation of the whole chart rather than an edit.
Everything else here is a lookup rule or a report choice and can be changed later.

`verification/loop_policy.yml` gives this phase `auto_advance: false` regardless, so stage 3
halts even for the items that would not have blocked. Decision 5 is the one that most needs
a human's eyes despite being `runtime-reversible`, and it is flagged as such below.

## Ruled by Taylor, 2026-08-20

All three `frozen-into-data` items stand on their defaults, so the committed key is `raise-to`
in big blinds, rendered as an `@` suffix quantized to hundredths with trailing zeros stripped,
and a call entry carries no size. A key therefore reads
`t6/d100/LJ/LJ:raise@2.5,BTN:raise@8`, where 8 is the total the button raised to and not the
increment.

He was shown the rendered key under each option rather than the option names, because the
question is what a string will look like in a refusal inventory for the rest of this repo's
life. The costs went with them: ragged column widths from stripping trailing zeros, and a
precision ceiling at hundredths that a future solve exceeds by being rejected rather than
rounded.

Decision 5 was ruled the same day and it is the one that mattered most. It was put to him
alongside the three above even though it is `runtime-reversible` and the loop would not have
stopped for it, because it extends ruling 8 rather than reading it. **His answer was that
three-bets have to be accommodated**, so normalisation reaches every raise in the sequence and
not only the open, and the 185-of-205 refusal figure is the rejected alternative rather than
this phase's expected outcome.

The remaining nine items proceed on their recorded defaults and are reported afterwards.

## What was measured first

Every number below was measured on this branch rather than taken from `backlog.yml`,
`docs/V2_ROADMAP.md`, or `docs/V2_RULING_MITIGATIONS.md`, because two of the figures those
documents quote do not reproduce.

### The 36 committed spots already carry every size the key needs

`data/artifacts/preflop/sizings/six_max_nl25_100bb.json` holds hero's raise-to size for all
36 spots, so the size of a raise by position P after prefix S is the sizing entry for the
spot `(P, S)`. Nothing has to be invented and no size has to come from the source's action
labels a second time.

Worked through: `t6/d100/BTN/CO:raise` becomes `t6/d100/BTN/CO:raise@2.5`, because
`t6/d100/CO/rfi` is sized 2.5. `t6/d100/LJ/LJ:raise,BTN:raise` becomes
`t6/d100/LJ/LJ:raise@2.5,BTN:raise@8`, because `t6/d100/LJ/rfi` is 2.5 and
`t6/d100/BTN/LJ:raise` is 8.0.

The ten distinct sizes in the table are 2.5, 3.5, 8.0, 10.5, 11.0, 13.5, 21.5, 22.0, 23.0,
28.5. Every one is a whole tenth of a big blind.

**The tree already carries two opening prices, not one.** LJ, HJ, CO and BTN open to 2.5; the
small blind opens to 3.5. So a single global solved price would be wrong today rather than
only after some future solve, which settles decision 6 on measured grounds.

**Sizes in the key do not multiply the artifact.** Each size-stripped prefix admits exactly
one solved size, so re-keying the 36 spots produces 36 spots. The key gains the ability to
distinguish prices at no cost in cells, which is the property ruling 8 asked for.

### The 19 inexpressible corpus decisions, in full

All 19 are a position acting twice, across 16 distinct sequences. The deepest is five raises:
`HJ:raise,CO:raise,HJ:raise,CO:raise,HJ:raise`. Three are four-raise sequences. One is a
limped pot that got raised and re-raised, `SB:call,BB:raise,SB:raise`.

So a two-orbit cap would cover this corpus and a real hand already went past it, which is
what decision 4 is about.

### The price the corpus actually opened to

1,156 decisions faced exactly one raise. The faced price, in big blinds:

| price | points | share | cumulative |
| --- | --- | --- | --- |
| 2.00 | 248 | 21.5% | 21.5% |
| 2.10 | 94 | 8.1% | 30.0% |
| 2.22 | 22 | 1.9% | 32.4% |
| 2.25 | 560 | 48.4% | 80.8% |
| 2.50 | 152 | 13.1% | 95.1% |
| 3.00 | 36 | 3.1% | 99.7% |
| other | 44 | 3.8% | 100.0% |

Twenty distinct prices in all. **Only 13.1 percent of them are the 2.5 the tree solves**, and
80.8 percent are at or below 2.25. At or above 2.5 is 18.1 percent, which reproduces the
Phase 08 figure exactly and is the one quoted number here that did check out.

This is the measurement `docs/V2_RULING_MITIGATIONS.md` lists first under what could be done
before any solve. It quantifies ruling 8 rather than reopening it.

### The prices past the open, which nobody had measured

205 decisions faced exactly two raises. The second raise took 34 distinct sizes from 5.25bb
to 14.0bb. The solved three-bet sizes are 8.0 in position, 10.5 and 11.0 from the blinds
against a late open, and 13.5 from the big blind. **Twenty of the 205 landed exactly on the
solved size for that three-bettor against that opener.** One fourth raise appears in the
sample, at 19.0bb, against a solved 21.5.

Exact size matching past the open would therefore refuse 185 of those 205 decisions. That is
decision 5, and it is why it is a decision at all.

### Two roadmap numbers do not reproduce

`docs/V2_ROADMAP.md` states 1,691 expressible six-handed 100bb spots with limps and 848
without, and says both are recomputable by enumerating `solver_artifacts.schema.spot_key`
over action sequences. Doing exactly that gives **1,949 and 977**.

The ratio is the same to within a percent, so this looks like one systematic difference rather
than two errors, but no variation tried reproduces the published pair: 1,586 of the 1,949 have
hero already acting, 363 do not, and 184 of the no-limp spots have hero not yet acting. The
mitigation document already suspected these were extrapolations nobody had recently run. They
are quoted in four places, so decision 10 is about where the correction lands.

## 1. What unit a size in the key is measured in

Reversibility: frozen-into-data

Default: **`raise-to-bb`.** The key records the amount the raiser raised *to*, in big blinds.

Options: raise-to-bb | raise-to-chips | multiple-of-the-previous-bet
Answer: [raise-to-bb]

*Chips.* What the history actually contains, and it does not survive a change of blind level:
the same spot at 25NL and at 100NL would key two ways, and the artifact is already keyed by
depth in big blinds rather than in chips.

*A multiple of the previous bet.* How players talk - a 3x open, a 2.5x three-bet - and it is
relative, so the same key means different chips depending on what came before it. It also
makes a limped pot's first raise undefined, since there is no previous bet to multiply.

The cost the default accepts: a raise-to in big blinds is not how a player describes a
three-bet, so `BTN:raise@8` needs the reader to know that 8 is the total and not the increment.
The report states it once in those words.

## 2. How a size renders inside the key string

Reversibility: frozen-into-data

The key is a string a human reads in a refusal inventory, and it is also the artifact's
primary index, so its rendering has to be unique per value and legible.

Default: **`at-suffix-hundredths`.** An `@` separates the action from its size, the value is
quantized to hundredths of a big blind, and trailing zeros are stripped: `CO:raise@2.5`,
`BTN:raise@8`, `SB:raise@2.25`. A size that is not exactly a hundredth is rejected rather
than rounded into a neighbouring cell.

Options: at-suffix-hundredths | colon-suffix-two-decimals | integer-hundredths-token
Answer: [at-suffix-hundredths]

*Two fixed decimals after a colon.* `CO:raise:2.50`. Uniform width, and it puts three
colon-separated fields in an entry that already uses the colon to separate position from
action, so `CO:raise:2.50` reads as three things rather than two things and a size.

*An integer count of hundredths.* `CO:raise@250`. Unambiguous with no decimal point anywhere
and unreadable, which matters because the whole reason the refusal inventory is useful is that
a person can scan it.

The cost the default accepts: stripping trailing zeros means `@8` and `@2.5` sit next to each
other at different widths, so the inventory column is ragged. Quantizing at hundredths also
puts an upper bound on precision that a future solve could exceed, and exceeding it is a
rejection rather than a rounding, which is the intended direction.

## 3. Whether a call or limp entry carries a size

Reversibility: frozen-into-data

Default: **`no-size-on-a-call`.** A call entry renders as it does today, `SB:call`. A call has
no price of its own; it pays the level the preceding raise already states, and in a limped pot
it pays the big blind, which the key's own prefix states.

Options: no-size-on-a-call | size-on-every-entry
Answer: [no-size-on-a-call]

*A size on every entry.* Uniform, and it writes a number into the key that is derivable from
the rest of the key. Two spot keys that describe one spot is the defect the single derivation
in `schema.spot_key` exists to prevent, and a redundant field is the cheapest way to get one.

The cost the default accepts: an all-in call short of the level would carry no record of being
short. That is a per-seat contribution question rather than a spot question, and it belongs to
proposed phase 13 with `ASYMMETRIC-EFFECTIVE-STACKS`.

## 4. What bounds the second orbit

Reversibility: runtime-reversible

Once a position may act twice, something has to say when to stop, or the key space is
infinite.

Default: **`legality-and-stack-depth`.** No orbit cap. A sequence is rejected when it is not a
legal preflop order, or when its raise sizes cannot be paid at the stated stack depth. The
depth bound is a check the key could not perform before it carried sizes.

Options: legality-and-stack-depth | cap-at-two-orbits | cap-at-a-stated-raise-count
Answer: [legality-and-stack-depth]

*A two-orbit cap.* Enough for the committed corpus, and a real hand in that corpus already
went to five raises, so the cap would be set one raise below evidence the repo already holds.

*A stated raise count.* The same objection with a number chosen instead of implied.

This is `runtime-reversible` because this phase commits no second-orbit spot. The GTO Wizard
source holds no four-bet node, so nothing about a cap would be frozen into the artifact here;
adding one later is an edit to a validator.

The class holds only because the default is the permissive option, and that is worth saying.
Loosening a cap later costs nothing, while imposing one later invalidates keys somebody has
already committed. Proposed phase 14 does commit four-bet cells through whatever this
validator then says, so a restrictive choice here would reach data by a road the class does
not measure.

## 5. Whether price normalisation extends past the open

Reversibility: runtime-reversible

**Ruled by Taylor on 2026-08-20: three-bets have to be accommodated.** So this stands on its
default, and it is his ruling rather than a default the loop took because nothing stopped it.

It was the call worth a human's eyes and the loop would not have stopped for it, because it
extends a ruling he made rather than implementing one. Ruling 8 says an opponent *open* at any
size is answered from the 2.5 cell. It does not say what happens to a three-bet at 6.25
against a solved 8.0, because nobody had asked. Ruling 8 now reaches every raise in the
sequence.

What the ruling does and does not buy, because the two are easy to conflate. It makes a
three-bet at any price *answerable* wherever the chart holds a cell for that spot, which is
the six vs-three-bet spots where hero was the opener. It adds no coverage: a squeeze or a
cold four-bet is expressible today and uncovered today, and stays uncovered here. Those are 65
rows and 250 decision points of `latest_sample_refusal_inventory.txt`, and they belong to
`CHART-COVERAGE-EXPANSION` at proposed phase 14, which is the phase that commits a chart
derived from an export holding those nodes.

Default: **`normalise-every-raise`.** Each raise in the sequence is normalised to the nearest
size the artifact holds for that position after the already-normalised prefix.

Options: normalise-every-raise | normalise-the-open-only | normalise-the-open-and-refuse-past-it
Answer: [normalise-every-raise]

*Normalise the open only.* Literal to the ruling. Measured, it refuses 185 of the 205
three-bet decisions in the corpus, because only 20 of them landed exactly on a solved size.
Proposed phase 14's closing measurement would then be computed over opened pots alone, which
is the collapse the mitigation document was written to prevent, arriving on a different axis
from the one it watched.

*Normalise the open and refuse past it, deliberately.* The same numbers, chosen rather than
inherited. Honest, and it hands phase 14 a measurement with no three-bet sample and phase 15 a
drill that refuses every three-bet spot it deals.

The cost the default accepts is the same cost ruling 8 accepted, one layer deeper and larger.
A three-bet to 6.25 is answered as though it cost 8, so the bot under-defends against cheap
three-bets, and the corpus sits mostly below the solved size there too. The substitution
census the contract requires is what measures it, split by whether the substituted raise was
the open or a later one, so the part attributable to the ruling stays separable from the part
attributable to this extension.

## 6. Where the set of solved prices comes from

Reversibility: runtime-reversible

Default: **`derived-from-loaded-keys`.** The candidate sizes for an entry are the sizes the
loaded artifacts' own keys carry at that position after the same normalised prefix. No price
appears in code.

Options: derived-from-loaded-keys | constant-in-the-normaliser | field-in-the-artifact-header
Answer: [derived-from-loaded-keys]

*A constant.* Already wrong: the committed artifact opens the small blind to 3.5 and every
other position to 2.5, so one constant cannot be right today, never mind after a second solve.

*A declared header field.* A second statement of something the keys already say, which can
disagree with them.

## 7. How a substituted price is recorded on the answer

Reversibility: runtime-reversible

Default: **`detail-on-the-decision`.** `StrategyDecision` gains the same kind of ordered,
structured `detail` that `StrategyRefusal` already carries, naming the price asked and the
price answered for each substituted entry. An exact answer carries no such entry.

Options: detail-on-the-decision | flag-in-the-rationale-string | separate-decision-type
Answer: [detail-on-the-decision]

*In the rationale string.* Free, and it makes every consumer parse a private format to find
out whether a number is exact, which the Phase 03 contract already had to fix once.

*A separate return type.* Every caller learns a third case, and a substituted decision is a
decision.

## 8. Whether the decision-audit schema version moves

Reversibility: runtime-reversible

Default: **`bump-to-2`.** The query payload gains a raise amount in its preflop history and
the outcome may gain a detail block, so version 1 bytes and version 2 bytes would be
indistinguishable at an unchanged version number.

Options: bump-to-2 | keep-version-1
Answer: [bump-to-2]

*Keep version 1.* This is exactly the defect
`DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS` already records, and repeating it
knowingly in the phase that reads that entry would be worse than the original.

## 9. Whether a v1 keyless artifact stays importable

Reversibility: runtime-reversible

Default: **`reject-a-sizeless-raise-entry`.** An artifact whose raise entries carry no size
fails import rather than being read as matching any size.

Options: reject-a-sizeless-raise-entry | accept-as-a-wildcard
Answer: [reject-a-sizeless-raise-entry]

*Accept as a wildcard.* A format that admits both is a format where a lookup can silently
match the wrong cell, and a wildcard is a bucket with no stated tolerance, which is the thing
proposed phase 12 exists to stop the repo doing.

No committed file needs the tolerance: the one artifact in the tree is re-derived to the new
keys in this phase.

## 10. Where the corrected spot counts land

Reversibility: runtime-reversible

Default: **`publish-measured-and-file-the-correction`.** The report publishes 1,949 and 977 as
measured, states that the roadmap's 1,691 and 848 do not reproduce, and a backlog entry owns
correcting the four places that quote them. The roadmap and the mitigation document are not
edited here, because both are `contract-update` territory and this is `implementation` from
stage 4 on.

Options: publish-measured-and-file-the-correction | correct-the-roadmap-in-this-phase |
report-only
Answer: [publish-measured-and-file-the-correction]

*Correct the roadmap here.* Mixes a semantic document edit into an implementation phase.

*Report only.* Leaves four documents asserting a number this phase measured to be wrong,
which is how the wrong number got quoted as established in the first place.

## 11. Whether the second-orbit spots get chart coverage here

Reversibility: runtime-reversible

Default: **`vocabulary-only`.** The 19 corpus decisions move from
`lookup:unrepresentable-spot` to `lookup:spot-not-covered` and are not answered. The GTO
Wizard source holds no four-bet node, so there is nothing to commit, and the total refusal
count does not fall.

Options: vocabulary-only | derive-four-bet-cells-from-the-gtopen-export
Answer: [vocabulary-only]

*Derive them from the Phase 10 export.* That export does hold four-bet nodes, deliberately, so
this is possible. It is proposed phase 14's whole job, it commits a chart, and doing it here
would put a new solve-derived range into the phase whose point is the format.

## 12. Whether the Phase 04 and Phase 05 contracts need amending

Reversibility: runtime-reversible

Default: **`read-both-and-amend-only-a-contradiction`.** Phase 04 declares the artifact and
chart contract and Phase 05 the chart-backed strategy. Both are read at stage 2 and amended in
`contract-update` mode only where a criterion asserts something the widened key makes false. A
contract merely made more true is left alone and the audit packet says which ones were read
and left alone.

Options: read-both-and-amend-only-a-contradiction | amend-both-preemptively | amend-neither
Answer: [read-both-and-amend-only-a-contradiction]

*Amend both preemptively.* Spends the contract line cap on text nothing required, and
`AGENTS.md` caps a contract at 300 lines with amendments only ever adding.

*Amend neither.* Leaves a completed contract asserting the opposite of what the code does,
which is the state Phase 11 had to fix twice.
</content>

## 13. What the re-derived artifact stamps as its generation time

Reversibility: runtime-reversible

`scripts/convert_preflop_export.py` hard-codes `GENERATED_AT = "2026-08-11T00:00:00Z"`, which
is when the ranges were extracted. Re-keying the artifact writes a new file, and the field has
to say something.

Default: **`stamp-the-re-derivation-date`.** `generated_at` moves to the date this phase
re-derives, and `source.notes` states that the ranges are the 2026-08-11 extraction re-keyed
at the v2 vocabulary rather than a new solve.

Options: stamp-the-re-derivation-date | keep-the-extraction-date
Answer: [stamp-the-re-derivation-date]

*Keep the extraction date.* Truthful about the ranges and false about the file, which then
claims to have been generated before the vocabulary it is written in existed. It also makes
two artifacts with the same timestamp and different keys, and `_artifact_sort_key` in
`lookup.py` breaks ties on exactly that field.

The class needs a caveat rather than a defence. This value goes into committed data, so
`runtime-reversible` fits it only by the letter: the artifact is derived and `--check`
reproduces it, so changing the field later is one converter edit and a regeneration, and no
downstream key, sizing entry, report, or phase-14 derivation moves with it. That is the
opposite of the key format, which is why the two are classed differently.
`LOOP-NO-CLASS-FOR-A-HUMAN-OWNED-THRESHOLD` is the entry that records the class vocabulary
being too coarse for cases like this one.
