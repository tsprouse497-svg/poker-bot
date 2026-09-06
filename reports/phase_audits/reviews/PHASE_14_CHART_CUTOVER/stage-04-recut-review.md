# Phase 14 stage 4: the re-cut against the 249, and its two independent reviews

This is the stage's review record. It is an index and an outcome, not a third opinion: the reasoning lives
in the two notes beside it and is not restated here.

## What the stage was

The frozen tests described a six-spot set, and before that a 143-node one and an 86-spot one. All are
superseded by the committed 249 - 5 first-in, 25 facing an open, 219 facing a three-bet - so this was a
re-cut rather than a repair. Nine frozen tests of already-completed phases were migrated in the same stage,
which the contract requires before the freeze rather than after it.

Six worker lanes did the re-cut, one owner per file, no lane reviewing its own work. A seventh and eighth
lane took the corrections that followed the reviews.

## The two reviews

Two read-only reviewers, one mechanical and one on the poker, neither having written any of the work and
neither having seen the other's notes.

| note | blockers | non-blockers | alignment |
|---|---|---|---|
| `stage-04-recut-review-mechanical.md` | 4 | 15 | 5 |
| `stage-04-recut-review-poker.md` | 1 | 4 | 4 |

## The five blockers, and what closed each

All five are marked `[resolved]` in their own notes with the detail. In brief:

- **The fourth relation read an action the bot does not take.** Decision 50 added it to catch a defect on
  the raise action, but it read the solve's raw raise weight, which at the 20 merged spots is not what the
  bot plays. Taylor ruled 2026-09-03 that it reads the merged weight. Decision 55.
- **`test_chart_counterfactual_arms.py:198` was permanently red on a false claim.** Taylor ruled the rank
  arm is scored over every spot in its partition. Contract criterion rewritten in place, decision 54.
- **`:258` was permanently red** because thirteen committed spots fold every hand. The assertion was wrong,
  not the fixture.
- **`RAISE_ACTION_INVERSIONS = 27` did not reproduce.** It is 41, with 25 invisible to every other check.
  Taylor ruled the acceptance stands at the true count. Decision 55.
- **The cutover's cost was measured against a chart deleted before the phase restarted.** The helper now
  reads the retired 86-spot chart at a git pin. True split 21 kept, 30 given up.

Alignment items went to `backlog.yml`: six ids created and five existing entries extended rather than
duplicated. The non-blockers were triaged individually; eleven were fixed in the stage and the rest are
recorded in the mechanical note against the lane or stage that owns them.

## What a follow-up measurement pass found that the reviews did not

A ninth lane re-derived every contested figure from the export, independently, because this repo does not
correct a published number on one reviewer's word. It confirmed all three, and went past them twice.

**It corrected the mechanical reviewer's diagnosis of the first finding.** "149 against 69" is not a single
mis-measurement. It splices two comparison rules: 149 is the solved side of the skip rule, 69 the
counterfactual side of the common-cell rule. Under either rule taken whole the unrestricted arm passes -
149 against 260, or 42 against 69. The conclusion stood; the explanation did not, and the corrected
explanation is why the fix publishes two skipped counts rather than one. Collapsing them is the operation
that produced the splice.

**It found that decision 50's second named case is not in the committed set.** The record offers `99` at
0.0 against `88` at 71.8 as evidence read off the 249. That node is `t6/d100/BB/CO:raise@2.5,SB:call`,
which decision 48 refuses as a big-blind squeeze spot. The committed spot the record names carries `33`
over `22` at 0.00 against 8.13 instead, a gap of eight points rather than seventy-two. The arithmetic was
right and the label was wrong. Two of decision 50's three cases stand exactly as written, and the severity
claim behind the acceptance survives through the hijack case at 70.15, which is committed.

## Where the reviewers were wrong, and it mattered once

The triage lane disputed four reviewer claims with its own measurements and was right each time. One of
them prevented a new defect: the mechanical note proposed tightening the de-rake check to
`min(gaps) > 0.5`, and the hijack's rake-free open sits 0.085 from the raked reference, so that assertion
could never pass. Implementing it as written would have frozen a fourth permanently-red test inside the
fix for a finding about permanently-red tests. It was rewritten as a per-row check pinning the hijack as
the single known exception, so a second one turns it red.

The other three: a vacuity gap the note overstated, where the rule is proved and only the label and the
count of three were wrong; a per-reason split assigning an exposure figure to the big blind when the
measured share there is zero and the figure belongs to the small blind; and a confirmation that the
strongest contrast in either note reproduces to two decimals.

## The through-line

Five defects, one cause. Every figure that failed here was hand-typed into a committed document that no
generator re-derives, and each was correct over the set it was taken on before that set moved. The rank
arm's justification survived four reviews and was quoted in six live places. The 27 was walked against a
chart that no longer exists. One of the three cases behind it was walked over a node the selection rule
now discards. The cutover ledger described a chart deleted two weeks earlier.

`HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` already names this and is still open. The contract
requires the report to re-derive every figure it publishes; the decision record and the backlog carry
dozens more that nothing checks, and that is where all five of these lived.
