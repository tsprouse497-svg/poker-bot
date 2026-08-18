# Phase 05 audit packet: Full-Table Preflop Strategy

Written for a reviewer who does not read code. Everything here can be checked from
committed files.

## Summary of what changed

The bot can now play preflop, six-handed, at exactly 100 big blinds, using a real
solver chart instead of a hand-written one.

A chart exported from GTO Wizard is committed as the input it came from, and a
script turns that input into the chart the bot reads. Thirty-six situations are
covered: every position's opening range, every response to a single open, every
response by an opener facing a three-bet, and the big blind facing a small-blind
limp. Where the chart says nothing, the bot refuses to act and names what was
missing, rather than guessing.

The hand-written chart from Phase 04 is gone. It covered three situations, it
disagreed with the real solution, and two charts claiming the same situation is an
error rather than a choice.

## Pass/fail checklist

Each line is checkable without reading code.

| # | Check | How to check it | Verdict |
|---|---|---|---|
| 1 | The chart came from a real solver, not from a model | `data/artifacts/preflop/six_max_nl25_100bb.json`, field `source.kind`, reads `solver-export` | PASS |
| 2 | The chart can be rebuilt from its committed input | `uv run python scripts/convert_preflop_export.py --check` | PASS |
| 3 | The chart matches the source's own published frequencies | `reports/active/latest_preflop_strategy_report.txt`, `chart` and `source` columns agree on all 11 figures | PASS |
| 4 | The bot's actual play matches the chart it reads | Same table, `bot` column, within 0.3 points everywhere | PASS |
| 5 | The hand-written chart is gone | `data/artifacts/preflop/` holds one artifact | PASS |
| 6 | The bot refuses where the chart is silent | Same report, "Refusals" section | PASS |
| 7 | The bot refuses off 100bb, and on straddles and antes | Same section | PASS |
| 8 | Every decision is legal poker | Enumeration through the Phase 03 audit record: 18,252 outcomes, 0 rejections | PASS |
| 9 | The same hand decides the same way every run | Report reproduces byte for byte across runs | PASS |
| 10 | Every judgment call was answered before code existed | `reports/phase_audits/decisions/PHASE_05_FULL_TABLE_PREFLOP_DECISIONS.md` | PASS |

## Recompute one number by hand

Open `data/artifacts/preflop/six_max_nl25_100bb.json`, find `action_weights` ->
`"t6/d100/BTN/rfi"` -> `"A2o"`. It reads fold 0.9128, raise 0.0872.

So the button folds ace-deuce offsuit about 91% of the time. Nothing in this repo
computed that number, and it contradicts the hand-written chart it replaced, which
opened that hand always.

To recompute an aggregate rather than a cell: the opening frequency for a position
is the share of the 1326 starting hands it raises. Ace-deuce offsuit is 12 of those
1326 combinations, so at a raise weight of 0.0872 it contributes 12 x 0.0872 = 1.05
combinations to the button's opening range. Summing that product over all 169 hand
classes gives 537.88 of 1326, which is 40.56%, the figure in the table below and on
the source site.

## Commands and reports

| Command | What it proves |
|---|---|
| `pytest_full_table_preflop` | 55 tests over the artifact, the strategy, totality, legality, determinism, and refusals |
| `generate_preflop_strategy_report` | `reports/active/latest_preflop_strategy_report.txt` |
| `generate_strategy_query_report` | `reports/active/latest_strategy_query_report.txt` |

Full gate green, including `check_gate_bite`, which proves the gate still fails when
the code is deliberately broken.

## Provenance attestation

The importer's checksum proves the weights have not been edited since the chart was
stamped. It proves nothing about where they came from, so provenance is a human
claim:

> The ranges in this artifact were exported from GTO Wizard's preflop solutions for
> solution `Cash6mGeneral_6mNL25R25` at 100bb, from Taylor's own logged-in account,
> on 2026-08-11, and reconciled against the frequencies the site displayed for each
> spot.

Attested by Taylor Sprouse, 2026-08-11, confirmed in the working session that
supplied the solution URL and requested the extraction.

## Frequencies against the source

From `reports/active/latest_preflop_strategy_report.txt`. `chart` is what the
committed file holds, `source` is what GTO Wizard displayed, `bot` is what the
strategy actually does.

| Spot | chart | source | bot |
|---|---|---|---|
| LJ opens | 17.49% | 17.49% | 17.59% |
| HJ opens | 21.65% | 21.65% | 21.76% |
| CO opens | 27.89% | 27.89% | 27.81% |
| BTN opens | 40.56% | 40.56% | 40.46% |
| SB opens | 34.41% | 34.41% | 34.28% |
| SB limps | 13.73% | 13.73% | 13.77% |
| BB defends vs LJ | 22.63% | 22.63% | 22.79% |
| BB defends vs HJ | 26.20% | 26.20% | 26.22% |
| BB defends vs CO | 31.48% | 31.48% | 31.42% |
| BB defends vs BTN | 39.43% | 39.43% | 39.31% |
| BB defends vs SB | 42.88% | 42.88% | 43.16% |

The `bot` column differs from `chart` only by sampling noise. It exists because an
earlier version of this phase over-folded by 13 points while a table showing only
the chart said everything was fine.

## Judgment calls and what each answer changed

All eight were answered before any implementation existed. Item 3 was re-ruled
mid-phase after review measured its cost.

| # | Call | Answer | What it changed |
|---|---|---|---|
| 1 | Retire the hand-authored chart | retire | One artifact owns 100bb six-handed; Phase 04's chart and its builder are deleted |
| 2 | Rake structure | accept NL25 | Ranges are tighter than rake-free, said out loud in the report and here |
| 3 | Mixed frequencies | **re-ruled**: weighted draw, seeded | See below |
| 4 | Raise sizing | source sizings | Sizes are committed data from the same solution, not invented |
| 5 | Off-100bb stacks | exact only | The bot refuses any depth but 100bb, measured from hero |
| 6 | Straddles and antes | refuse | The bot refuses rather than reading them as ordinary pots |
| 7 | What "full table" claims | askable | Every seat can be asked; not every situation is charted |
| 8 | Where the raw export lives | under artifacts/sources | The chart is rebuildable from a committed input |

Item 3 was originally ruled "take the highest-weight action", with its cost recorded
as "unbalanced and exploitable, but never illegal". Review measured that cost and it
was much larger than the phrasing implied: folding is one bucket while continuing
splits across calling and raising, so the rule folded hands the chart continues with
more than half the time, and only ever in that direction. Fold-to-three-bet ran
72.8% against the solution's 59.8%, past the point where an opponent's three-bet
auto-profits as a pure bluff with any two cards. Re-ruled to a weighted draw seeded
on the hand, which reproduces the chart's frequencies and stays replayable.

## Independent review

Two read-only reviewers, one on poker correctness and one on mechanics. Full
findings in `reports/phase_audits/reviews/PHASE_05_FULL_TABLE_PREFLOP/stage-08-review.md`.

**Four blockers, all resolved.** None of them would have been caught by the gate,
which is the argument for keeping this stage even when everything is green.

1. The collapse rule over-folded by 13 points (domain review). Fixed by re-ruling
   judgment call 3 and pinned by a regression test.
2. Stack depth was read from the deepest seat rather than from hero, so a 12bb hero
   opened a 100bb range (mechanical). Fixed and pinned.
3. The straddle and ante guard stopped looking after any action, so an anted pot was
   chart-backed for five of six seats (mechanical). Fixed and pinned.
4. The seed was untested, and the seed the contract forbids by name passed the whole
   suite while frequencies drifted (mechanical). Fixed and pinned.

Non-blockers recorded but not fixed: the all-in branch collapses into `raise` and so
loses a real shove strategy in five spots; four suspicious zero cells in the opening
grids (16 combinations) worth reading off the source site; the frequency
expectations are described as an external oracle in three places when they are
derived from the same committed source; committed raise sizes assume the tree's
exact bet sizes.

## Known limitations

- **100bb only, six-handed only.** Anything else refuses. `CHART-COVERAGE-EXPANSION`.
- **Straddle detection is bounded, not exact.** A straddled pot with several callers
  can pass the check. `PER-SEAT-CONTRIBUTIONS-IN-QUERY`.
- **A short villain is invisible.** The query carries no per-seat contributions, so a
  short stack and an already-invested stack look identical.
  `ASYMMETRIC-EFFECTIVE-STACKS`.
- **No squeeze or cold four-bet spots**, and facing a four-bet has no representable
  key at all. `SECOND-ORBIT-PREFLOP-SPOTS`.
- **Sizes are not part of a spot key**, so the chart answers a 4bb open with a range
  solved against 2.5bb. `RAISE-SIZE-IN-SPOT-KEY`.
- **These ranges assume NL25 rake.** They are tighter than rake-free ranges,
  especially in the blinds.

## Human sign-off

Taylor ruled all eight judgment calls before implementation, re-ruled item 3 after
review, and attested the export's provenance. Sign-off on this packet is pending.
