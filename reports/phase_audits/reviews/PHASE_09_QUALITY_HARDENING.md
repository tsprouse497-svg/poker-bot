# Phase 09 Review Notes

Two passes, as this repo has done since Phase 05. The mechanical pass asks whether the
thing works. The domain pass ignores the contract and asks whether the work is right,
which is the only question a green gate cannot answer.

This phase has no poker in it, so the domain question is not about the poker. It is:
**would these checks have caught the defects they were built for?** A hardening phase
that passes its own gate while missing the exact bugs it was written after is the
purest possible version of the failure it exists to close.

The answer, before the fixes below, was no for two of the three.

## Mechanical pass

- Full gate green. 29 mutations applied, all 29 caught.
- The two commands that had no canary now have one each. The full-table preflop canary
  replaces the seeded weighted draw with a roll of zero, collapsing every mixed cell to
  the artifact's first action, and takes four tests down. That is the plurality rule
  Phase 05 shipped and re-ruled against, so the canary is a defect this repo has
  actually had rather than an invented one.
- The catch-all `pytest` command is named in a mutation rather than exempted. Both were
  defensible; naming it costs one line and leaves the exemption list empty, which is a
  better place for it to start.
- 26 tests, each check exercised against a broken input and against this repo.
- One process failure, recorded because it is the interesting part. A commit taken while
  a background stage advance was still running `check_gate_bite` captured the mutated
  `positions.py` and the sentinel announcing it. The restore in the `finally` block
  worked; the commit simply happened inside the window. The gate caught it, but on
  `check_scope` reporting an out-of-scope file rather than on the swapped labels, so the
  message was two steps from the defect. Filed as
  `MUTATION-SENTINEL-IS-COMMITTABLE` rather than fixed here, because `.gitignore` and
  `check_scope.py` are outside this phase and a phase must not edit the checks it is
  measured by.

## Domain pass

### Blocker found and fixed: the drift check did not cover the file where the drift happened

Three defects motivated this phase. The check as first built would have caught one.

**The all-in count (7 against 24).** Caught. The original sentence read "7 of the 500
hands contain an all-in", and the registered pattern expects `of the 499`, so the file
would have failed on a missing match rather than on a wrong value. Red either way, and
the message names the file.

**The decision-point count (3,056 against 3,048).** Not caught. That number lived in
`reports/phase_audits/decisions/PHASE_08_SAMPLE_COMPARISON_DECISIONS.md`, and the fact
listed only the audit packet and the limits document. The file where the drift actually
happened was outside the check's reach.

**The pooled call disagreements (70 of 104 against 58 of 89).** Not caught. No fact was
registered for it at all, in any file.

Both are fixed. The decision record is now a quoted file for the decision-point fact,
and two facts are registered for the human call disagreements, in the packet and in
`backlog.yml`. Ten facts now, across four documents.

Widening the first of those exposed a second defect in the check itself, which is the
one worth reading. The decision record legitimately says "roughly 3,000 preflop decision
points" a few lines below the exact figure, and the pattern was written with a
`(?<!roughly )` lookbehind to skip it. That did not work: the regex engine backtracked
and started matching at `000`, where the preceding character is a comma rather than the
word being watched for, and the skip silently stopped applying. The check then reported
the document as stating `,000`. A second lookbehind forbidding a digit or comma before
the match fixes it. **A lookbehind that quietly stops applying is the same shape of
defect as a test that cannot fail**, and it appeared inside the check written to close
that class.

### Second finding: the citation check could only see one namespace

The backlog citation check recovers ids from prose by shape. As first wired it filtered
to tokens already known plus anything starting with `CORPUS-`, which means a finding
filed under an id nobody created would have been caught only in that one namespace. The
check would have been about spelling rather than about whether the finding was filed.

Widened to the full id shape, with two named exclusions and one shape rule: the corpus
licence tokens, a Phase 05 review heading, and task ids such as `MAINT-07` or
`PHASE-09`, which name a unit of work rather than a filed finding and appear in every
ExecPlan. Each exclusion carries its reason in the code.

The widened check then caught a ghost citation in this file, minutes after it was
written: these notes originally described the excluded task ids with placeholders, and a
placeholder is exactly a citation of an id nobody filed. The document was reworded and
the check left alone, which is the order the contract requires.

That list is the thing to watch on any future review. The contract forbids exempting
something to make a check pass, and the difference between a true exclusion and a
convenient one is only visible to a reader. Three entries and one shape rule, each of
which is genuinely not a backlog id, is where it starts.

### Third finding: mutation coverage only looks at pytest commands

Every checker and generator in the gate - `check_scope`, `check_contracts`,
`check_generated_*`, the report writers - has no canary demanded of it, and several have
none. The contract asked for `pytest_*` coverage and got it, so this is a limit rather
than a miss, but a limit nobody wrote down is indistinguishable from a claim. It is now
stated in the check's own `does_not_cover` line and printed in the committed report.

### What this phase does not establish

A check that passes says the property held at this commit. None of these four says the
repo is correct, and the report says so above every result.

The fact check reads ten numbers in four documents. Every other sentence in this repo
states things no check reads, and the three defects that motivated this phase were found
by a person reading prose, not by a gate. This phase narrows that gap; it does not
close it.

## Blocker status

One blocker was found in the domain pass and fixed inside the phase: the drift check did
not reach the file where one of its three motivating defects lived, and had no fact for
another. Fixing the first exposed a broken lookbehind that had been silently disabling
part of the check.

No blocker remains open. `MUTATION-SENTINEL-IS-COMMITTABLE` is recorded work, not a gate.

## Independent review

Not yet run. The Phase 08 stage 8 review was performed by a reviewer with no knowledge
of the work, and it found six things two self-review passes had missed, including that
the phase's headline finding was mostly explained by a property of the artifact nobody
had named. This phase's Delegation Plan records the same intention.

The self-review above found two real blockers, which is better than the Phase 08 self
review managed, and it is still the same mind that wrote the checks judging whether the
checks are right. That weakness should be read as real until an independent pass runs.
