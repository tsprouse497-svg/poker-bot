# MAINT-34 independent review: the coordinator's own repairs

## Reviewer independence

Read-only lane that wrote none of this and is neither of the two earlier reviewers. Its target was
the single commit `f2ba791`, 68 files - specifically **the repairs made in response to the first two
rounds**, which were themselves unreviewed. It left the worktree byte-identical, ran no gate
command, and where it needed a mutation it copied the file into its own scratch space and mutated
the copy.

## Verdict: no blockers. Every load-bearing repair reproduces exactly.

Recomputed from the shipped artifacts against `git show 19beb97:`, all matching:

- **The per-spot sets table**, every figure and both denominators. Arrival shares 2.2298 / 2.1256 /
  2.0835 / 2.4774 / 2.6651 percent over a `sum(arrival_ppb)` of 6,054,005,282, which the documents
  name. The combinatorics check out: three combos of each of `99`/`88`/`77` survive that board, so 9
  is the true ceiling, and 78 is 13 pair classes at 6 combos.
- **The exposure re-pin.** At 11.4 the committed set goes 156 to 157, the exposure bucket 154 to 152
  and the squeeze bucket 9 to 10, and the one spot added is the named one at 11.3681. The old 10.05
  moves zero spots, so the vacuity claim is true. It independently confirmed that the narrowest
  refused node overall is a big-blind squeeze spot and therefore admissible by no threshold at all.
  The other four re-measured mutations reproduce exactly, and **all 75 `find:` strings in the file
  resolve exactly once in their target**, checked programmatically.
- **The jam canary, both walks reimplemented.** The old rule really did pick a node with a
  `(fold, call)` menu and print 0.00; the new one picks a withheld node offering a jam and prints
  100.00; the new bound fails against the dead case.
- **The new convergence test.** The card posts `0.00015587719683285103` against a target of
  `0.00016` at 3,800 iterations of a 5,000 cap - a real 2.6 percent margin, not a tautology - and a
  grep confirms nothing else in the repo made that comparison, including the extractor.
- **The `refused:` / `Traceback` assertion**, verified by running the actual mutation on a copy:
  base prints `refused:` with no traceback, mutated prints a traceback with no `refused:`, and both
  exit non-zero with no report, which is why the old pair of assertions could not tell them apart.
- **The backlog re-measurements**: the opening frequencies both sides, the four-bet 40/26 split at
  3.00x and 5.4x, all three price counts under both readings, and the 33-to-34 jam correction with
  the single differing spot identified.
- **The three cap-forced extractions.** It diffed every removed line against the new modules and the
  survivors: the only pre-existing reasoning that moved is the `uniform_node` note, now a module
  docstring. Nothing was lost.

## Six non-blockers, all fixed

Every one is the same defect this task keeps finding - a figure the re-solve falsified that no check
watches - and three of them are in repairs this task made.

1. **`tests/corrupted_artifacts.py` carried `10.0234` across the extraction**, four lines under a
   new module docstring claiming the one figure it carries is read from a constant rather than
   typed. The true value is `NARROWEST_REFUSED_EXPOSURE_PCT`, 10.4362.
2. **`verification/mutations.yml` sent a reader to the wrong file for that same figure** and said
   the file was "not this lane's to change" - untrue twice over, since the prose had moved and
   `tests/**` is in `approved_scope`. Self-sealing: it told a reader to look where the defect was
   not, and that nobody could fix it.
3. **`the-old-versus-new-comparison-reads-the-new-chart-twice` stated a falsified ladder** - "the
   derived one holds only 2.5, 7.5, 22.5 and 100" - inside an argument the file asks a reader to
   trust. Six prices ship.
4. **`self_play_reference.py` was half-repaired.** The price list above was fixed and the sentence
   below it left reading "SEEN at 7 of the 61 gap spots and NEW at 54". The inventory regenerated in
   the same commit reads 75 spots, 8 SEEN and 67 NEW. The same figures were stale in `backlog.yml`,
   `docs/BACKLOG.md` and a frozen test's docstring, and `comparison_report.py` renders the
   inventory's own explanation of its SEEN/NEW column with "the three prices the solved tree holds"
   in it - so the shipped report told its reader something this task made false, directly under the
   reasoning it was meant to support. `comparison_report.py` joined `approved_scope` for that one
   sentence under a dated entry.
5. **The `UNGUARDED-PROSE` entry's own new paragraph went stale inside its own commit.** Written on
   2026-09-16 to record that three unwatched figures in `CORPUS_COMPARISON_LIMITS.md` had moved, it
   gave the new values as 2,432, a low end of 1.2 percent and a high end of 20.3 percent said to
   have survived. Decision 7 landed in the same task and the document as shipped reads 2,383, 1.3
   and 20.6 - so two were stale within a day and the third did not survive. The entry whose whole
   subject is figures nothing watches going stale, going stale, unwatched, in its own commit.
6. **One gap in the opening-range repair mixed two readings of the reference.** The hijack's
   before-gap was carried from the older aggregate-file reading; on the combo-weighted grid the new
   column uses, it is -0.088 rather than -0.085. Immaterial to "roughly tripled" and corrected.

## Alignment items

- **Three canaries went vacuous in one task and only one was caught by a machine.** `check_gate_bite`
  caught the report canary; the exposure canary was caught by a reviewer noticing a key with `@7.5`
  in it, and the jam canary by someone reading the number under the prose. Nothing in the gate can
  notice a canary whose gap has gone empty - `check_gate_bite` sees only a command exiting 0, which
  reads like a flaky run. The 11.4 re-pin sits in a 0.456-point window defined by two nodes a
  re-solve moves wholesale, so the next re-solve owes this again. `mutations.yml` says "re-measured
  per solve" and nothing enforces it.
- **The corpus sample's figures are a second unwatched surface**, restated by hand in three or four
  places. The chart side has entries naming this; the sample side has none.

## What the reviewer was asked at the end, and answered

**Not looked at.** The contract amendments, `phase_status.yml`, the generated status documents and
the decision list as documents in their own right - out of brief and covered by the earlier rounds
and the gate. Most of the report generator outside the jam walk, the ladder and `main`. `src/**` as
code except where a checked figure pointed into it. It did not re-solve or check determinism, so the
export is taken as given, and it ran no gate command, so "48 commands green" is the committed record
rather than its own measurement.

**A finding it is holding back.** The `refused:` assertion is the right repair but it pins a *string*
in stderr across a subprocess boundary, and nothing else in the repo asserts that `main` prints its
refusals with that prefix. A later rename of that one f-string silently re-vacuates both cases and
the test still passes on exit code plus no-traceback. A latent shape in a check this task improved,
not a defect in the change.

**What would mislead a reader six months out.** All three are non-blockers 1, 2, 4 and 5 above, and
all are fixed: the `10.0234` pair that pointed at the wrong file while saying it was out of scope;
the `UNGUARDED-PROSE` entry being wrong about its own subject; and the 61-spot, three-price
description of the sample that a reader reconciling against a 75-spot inventory would take for a
different run rather than a stale sentence.
