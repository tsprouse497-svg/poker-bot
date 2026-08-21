# Stage 4 Review - Phase 12 Tests

Read-only pass over the stage-4 diff, against the question the driver printed: would each
test fail against a plausible wrong implementation, and does it assert on real behaviour
rather than on state rebuilt from the code under test? Stage 5 freezes these, so a weak test
is preserved perfectly.

Coordinator-written self-review under `AGENTS.md` step 10; the no-delegation exception is in
the ExecPlan's Delegation Plan.

The diff is wider than the stage: it also carries the contract and decision-record edits that
recorded Taylor's three-bet ruling, which landed after stage 3 advanced. `docs/LOOP.md` expects
that. 62 tests, 53 red, 9 green, 6 errored on a fixture importing a module that does not exist.

## Blocker

- **[resolved] A test that could never fail.**
  `test_no_corpus_decision_refuses_for_a_price_the_chart_does_not_hold` scanned refusal codes
  for the substring `price`. No refusal code in the repo contains it, and none would after the
  implementation either, so the test passed at the branch point and would pass against every
  wrong implementation of the thing it claimed to check. Stage 5 would have frozen a test that
  asserts nothing. Replaced by two that bite: `test_every_refusal_names_a_spot_key`, which is
  271 of 290 today and therefore red on an assertion, and
  `test_the_squeeze_refusals_are_untouched`, which pins the 132 two-raise refusals that must
  *not* move because normalising a price is not finding a nearest spot.

- **[resolved] The number justifying Taylor's ruling was wrong, in the contract and in the
  decision record.**
  Both said exact three-bet matching would refuse 185 of the 205 three-bet decisions in the
  corpus. Measured properly, the 205 break down as 1 inexpressible, 125 expressible but
  uncovered, and 79 the chart actually holds a cell for. The 125 already refuse and are
  unaffected by any price rule, so the real cost of exact matching is **72 of those 79**, which
  is 91 percent of the answerable three-bet sample rather than 90 percent of all two-raise
  decisions. The conclusion is unchanged and if anything sharper; the arithmetic behind it was
  not. Corrected in the contract, the decision record, and the test docstrings that quoted it.
  The contract edit needed `contract-update` mode, so it landed as its own task with its own
  `scope_change_log` entry rather than inside this one.

## Non-blocker

- 53 of the 62 tests are red on a `TypeError` or `AttributeError` rather than on an assertion,
  because `PreflopAction` gains a field and constructing one is the first thing most of them do.
  That is `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` exactly: the assertion never runs, so a
  wrong expected string would survive the freeze untouched. Three things were done about it
  rather than noting it. Every expected key string was written out by hand from
  `sizings/six_max_nl25_100bb.json` instead of derived from anything. Five of them are
  independently re-asserted against the committed artifact in
  `test_the_committed_keys_are_the_measured_ones`, so a hand-transcription error in those five
  shows up as a second failure rather than as a silent pass later. And `ruff --no-cache` was run
  over the file, because a stage-4 red does not read the file with a linter.
- The six report tests error rather than fail, since the `report` fixture imports a module that
  does not exist. Red either way, but it means nothing has parsed those six for correctness
  except a reader.
- The report tests assert on substrings, which is the weakest assertion shape in the file: a
  report could contain `72` for an unrelated reason. Deliberate. The alternative is pinning the
  report's layout, which fails on every wording change and teaches a builder to write the report
  the test wants rather than the report a person needs.
- The four canaries name `find` strings that do not exist yet, so today they are a
  specification for stage 6 rather than a check. Phase 11 did the same and matched five of five,
  and the header comment in `mutations.yml` says plainly that a mismatch at stage 7 is the
  builder having drifted rather than the canary being wrong.
- One canary, `price-substitution-not-recorded`, names `generate_spot_vocabulary_report` in
  `must_fail`, which no mutation in this repo has ever done - `quality_checks.py` only demands
  canaries for `pytest_*` commands. Satisfying it requires the report generator to validate its
  own census total against the substitutions it counted. That is a real design constraint this
  stage imposes on stage 6, it makes the generator non-decorative in the gate, and it is
  recorded here so it is not discovered as a surprise at stage 7.
- `test_a_short_all_in_re_raise_is_still_an_increase` accepts a raise to 3.0 over a 2.5 open,
  which is legal only if the raiser was all-in. The key carries no per-seat stacks, so it cannot
  check that and should not try; the test name and docstring carry the reason, and the guard it
  provides is against a monotonicity rule implemented as a minimum-raise rule.
- Nine tests are green at the branch point and all nine are over-application guards, including
  `test_the_artifact_re_derives_from_its_source`, which is the property that makes the re-keying
  auditable at all.

## Alignment

None new. `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` is the standing drift this stage sat on
top of, and it bit here harder than it did in phase 11 because this phase changes a constructor
signature rather than behaviour behind one.
</content>
