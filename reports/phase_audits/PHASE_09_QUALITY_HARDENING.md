# Phase 09 Audit Packet: Quality, Drift, Backlog, And Phase-Gate Hardening

Written for a reviewer who does not read code.

## Summary in plain language

Every phase before this one added something the bot can do. This one adds nothing to the
bot at all. It closes three ways this repo has been wrong while every check passed, and
all three had already happened rather than being imagined.

**A gate command can be decorative.** The repo already proves its gate can fail: it keeps
a list of deliberate defects and requires the tests to notice each one. But nothing
required a defect to be aimed at every command. Two commands had none pointed at them,
including the one guarding what the bot opens, calls and folds preflop - the most
consequential decision it makes.

**A number in a document can drift from the data it describes.** The Phase 08 packet said
7 hands contain an all-in where the sample holds 24, said 3,056 preflop decisions where
the comparison produces 3,048, and printed a figure that averaged the machine with the
humans under a sentence saying it never did. Each survived a green gate, because nothing
reads prose.

**A backlog entry can rot.** A finding can be filed under an id nobody created, or against
a phase that does not exist, and the work list slowly stops being a work list.

Four checks now run in the gate. Each one was written to fail first, against a
deliberately broken input, before it was run against this repo.

## Pass/fail checklist

| # | Claim | Result |
|---|---|---|
| 1 | Every command that runs tests has a deliberate defect aimed at it | PASS - 10 of 10, no exemptions |
| 2 | The defect aimed at the preflop strategy changes the poker, not just the code | PASS - it collapses every mixed hand to one action, and four tests fail |
| 3 | Ten numbers quoted across four documents are recomputed and compared | PASS |
| 4 | A document whose sentence no longer matches is an error, not a silent pass | PASS - proved by a test that requires it |
| 5 | Every backlog entry is well formed, uniquely named, and filed against a real phase | PASS - 29 items |
| 6 | Every backlog id cited in a document resolves to an entry that exists | PASS |
| 7 | Every completed phase agrees with its tag, its plan, and its packet | PASS - 9 phases, 4 records each |
| 8 | Each check states what it does not cover, in its own report | PASS |
| 9 | Every check was shown failing before it was shown passing | PASS - 25 tests, each check exercised both ways |
| 10 | No poker behaviour changed | PASS - no engine, chart, strategy, or artifact file is touched |
| 11 | Full verification gate green | PASS - 35 commands |
| 12 | The gate bites: committed mutations make it fail | PASS - 29 of 29 caught |

## What each check covers, and what it does not

| Check | Covers | Does not cover |
|---|---|---|
| Mutation coverage | Every registered `pytest_*` command is named by at least one committed defect | The checkers and generators in the gate, which have no defect demanded of them. It also cannot judge whether a defect is a good one |
| Fact drift | Ten registered numbers, recomputed from committed data and matched against the sentence that states them | Every sentence stating a number nobody registered, which is most of them |
| Backlog integrity | Schema, unique ids, real phases, and citations that resolve | Whether an item is still worth doing, or whether one marked done was finished. A finding described without an id is invisible to it |
| Phase record agreement | Status, ExecPlan location, audit packet and git tag, cross-checked for every completed phase | Whether a phase did what its contract said. The tag check is skipped on a clone with no tags, and says so |

## What the review found

Recorded in full at `reports/phase_audits/reviews/PHASE_09_QUALITY_HARDENING.md`.

The domain question for a phase with no poker in it is whether the checks would have
caught the defects they were built for. **Two of the three: no.**

The decision-point count lived in the Phase 08 decision record, which no fact listed. The
pooled call-disagreement figures had no fact at all. Both are registered now.

Widening the first exposed the finding worth reading. The decision record legitimately
says "roughly 3,000 preflop decision points" a few lines below the exact figure, and the
pattern was written to skip it. It did not skip it: the search backtracked and began
matching in the middle of the number, past the word it was watching for, so the skip
quietly stopped applying. A check that quietly stops applying is the same shape of defect
as a test that cannot fail - and it turned up inside the check written to close that
class of defect.

## Decisions

Six judgment calls were recorded before implementation in
`reports/phase_audits/decisions/PHASE_09_QUALITY_HARDENING_DECISIONS.md`. All six were
`runtime-reversible`, so the loop proceeded on their recorded defaults.

| # | Call | Outcome |
|---|---|---|
| 1 | Generated or hand-written facts file | Generated and committed. A hand-written one is the same bug one step back |
| 2 | How a document declares it quotes a fact | The fact names the files, and matches a sentence shape rather than a bare number |
| 3 | When a value legitimately changes | The gate goes red and a person edits the sentence. A script rewriting prose would produce confident statements nobody made |
| 4 | What mutation coverage is required over | Per registered `pytest_*` command, exemptions by name in the code |
| 5 | What the preflop canary may break | A behavioural rule. It reinstates the plurality collapse Phase 05 re-ruled against |
| 6 | Whether a phase's git tag is required | Required when the clone has tags, skipped and announced when it has none |

The claim that all six are reversible is the one a reviewer should attack, and the
decision record states the counter-argument against it rather than burying it.

## A number you can recompute by hand

**Claim: every command in this gate that runs tests has a deliberate defect aimed at it,
and before this phase two did not.**

Open `verification/mutations.yml`. Each entry ends with a `must_fail:` list naming the
commands that must go red when that defect is applied. Collect every name in every one of
those lists. There are 29 entries.

Now open `reports/active/latest_verify.txt` and find the commands whose names begin with
`pytest`. There are 10.

Every one of the 10 appears somewhere in the collected `must_fail` names. Two of them -
`pytest` and `pytest_full_table_preflop` - appear only because this phase added them, and
you can see both in this phase's diff.

You can also check the drift machinery the same way. `reports/active/repo_facts.yml` lists
ten numbers. Take `corpus_all_in_hands: '24'`, then open
`reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md` and `docs/CORPUS_COMPARISON_LIMITS.md`
and search each for "all-in". Both say 24. Change either to 7, run the gate, and it names
the file, the value it found, and the value the repo computes.

## Known limitations and deferred items

- **The fact check reads ten numbers.** Every other sentence in this repo states things no
  check reads. The three defects that motivated this phase were found by a person reading
  prose, not by a gate. This narrows the gap; it does not close it.
- **Mutation coverage is about commands, not about strength.** One defect aimed at a
  command proves the command can fail. It says nothing about whether its tests are good,
  and a weak test that was wrong when written survives every check in this repo.
- **The exclusion list is the thing to watch.** The citation check excludes two licence
  tokens, a review heading, and task ids by shape. Each is genuinely not a backlog id
  today. A list that grows to fit the repo would make the check decorative, which is what
  this phase is about.
- **No independent reviewer has read this phase.** The Phase 08 independent review found
  six things two self-review passes missed. This packet records a self-review that found
  two real blockers, which is better than that self-review managed, and it is still the
  same mind judging its own work.

Filed in `backlog.yml`:

- `MUTATION-SENTINEL-IS-COMMITTABLE` - a commit taken while the gate was applying a
  deliberate defect captured both the defect and the sentinel announcing it. Two cheap
  fixes, both outside this phase's scope.
