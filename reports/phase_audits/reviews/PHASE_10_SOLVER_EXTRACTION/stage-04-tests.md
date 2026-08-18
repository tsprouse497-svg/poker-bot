# Stage 04 Review - Tests (Phase 10)

Question asked: would each test fail against a plausible wrong implementation, and does it
assert on real behaviour rather than on state rebuilt from the code under test? Stage 5
freezes these, so a weak test is preserved perfectly.

Scope: `git diff d088f48838452398ae799d8fdbf9543d8ba3b48a -- backlog.yml
data/artifacts/preflop/exports/gtopen_node_payloads.captured.json
docs/exec_plans/active/PHASE_10_SOLVER_EXTRACTION.md
docs/phase_contracts/PHASE_10_SOLVER_EXTRACTION.md
reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md
scripts/check_file_sizes.py scripts/run_verify.py tests/test_solver_export.py
tests/test_solver_expectations.py`

Reviewer: coordinator, read-only pass, no gate runs. Subagent delegation is switched off in
this operator's sessions, so `AGENTS.md` step 10's self-review fallback applies. The stage's
diff includes the contract correction committed as `008bf36`, so that is reviewed here too
rather than in a note of its own.

## Blocker

- [resolved] **The stage could not author a test against the contract it had.** Four
  acceptance criteria still described the tree as it stood before the human gate narrowed
  ruling 3, and one demanded a committed test asserting a limped node is present in an
  export the ruling forbids from containing one. The loop was halted, the contract corrected
  in `contract-update` mode, and implementation reopened. Recorded in `scope_change_log`.

- [resolved] **The passing baseline made the at-most-one-below clause untestable.** The
  indicative aggregate the expectations tests move one number at a time from had CO opening
  at 27.5 against a reference of 27.89 - already one number below its expectation. The test
  that puts a second number one point below and expects no error would then have seen two
  and failed, and the natural repair when a threshold test fails is to relax the threshold.
  CO moved to 28.5, so the baseline now sits below on nothing and each test moves exactly
  what it claims to move.

- [resolved] **The quantisation test did not discriminate the ruled rule from ordinary
  rounding.** It fed 0.4 basis points, which both the ruled drop-below-one rule and plain
  round-to-nearest send to zero. Fed 0.9 basis points instead: the ruled rule stores zero,
  a naive rounder stores one, and only the ruled rule passes.

- [resolved] **The renderer test forced a test-only branch into production code.** It passed
  `export=None` to `render_solver_export_report`, which would have obliged the implementer to
  carry a None path that only the test ever takes. It now passes a real one-node export.

- [resolved] **Nothing tested that the gate command fails.** Every expectations test called
  the library functions and asserted they return errors. A script that collects those errors
  and returns zero anyway would have passed all of them while the gate stayed green, which
  is the exact shape of a decorative check. `test_the_gate_command_exits_nonzero_when_a_check
  _fails` now runs `check_solver_export_expectations.main` against a deliberately broken
  export written to a temp path.

## Non-blocker

- **The strongest test in the file is the one that compares against the solver rather than
  against the repo.** `test_conversion_preserves_the_solver_s_own_action_frequency` recomputes
  each action's aggregate from the converted node - combo-weighted and reach-weighted per
  decision 7 - and requires it to match the `freq` GTOpen reported for the same action, on
  every captured node. Measured during capture, the two agree to six decimal places, and the
  flat-169 alternative diverges by 15 points at a conditioned node. That is external ground
  truth rather than state rebuilt from the code under test, and it is what makes a transposed
  hand index or a dropped reach fail immediately.

- **The conditioning question is answered, and the answer changes the extractor.** At the
  LJ-versus-three-bet node, 72o carries reach exactly 0.0 and a full, untouched uniform
  strategy row. The payload is therefore unconditional: `reach` is the only thing that
  conditions it, a converter that ignores it produces self-consistent nonsense, and the range
  intersection the GTO Wizard export needed is available from the committed data because
  decision 10 stores reach per node. This was the fourth item on the unverified list and it is
  now a measurement rather than an expectation.

- **Placeholder coverage on the source card is narrower than the criterion reads.** Every
  required block is tested for absence, but the placeholder parametrisation only runs against
  `determinism.result`, plus a separate zero-wall-clock case. Those are the two the contract
  names, so the criterion is met; a card with an empty `conditioning.discriminator` would still
  pass. Worth widening when the checker is written, not worth a blocker now.

- **Nothing in the gate can catch a source card that lies about the walk.** The path encoding
  cannot be re-derived offline, so `walk.reresolved_nodes` and `walk.mismatches` are the
  extractor's own report of its own self-check. The tests require the fields and fail on a
  nonzero mismatch count; they cannot prove the walk ran. That is inherent to a phase whose
  gate must pass with no GTOpen and no network, and it belongs in the packet's limitations.

- **The committed-export tests are currently red for a missing file rather than a wrong
  export.** That is the intended stage-4 state, but it means the assertions in that section
  have never been exercised against anything. The first run after the solve stage is the first
  time they say anything, and a failure there should be read as new information rather than as
  regression.

- **The fixture is six nodes of 38,828.** It covers the root, a folded-to RFI, the small blind
  opening, a big-blind defence, a node behind a three-bet, and a node behind a four-bet, which
  is every structural shape the reader has to parse. It is not a sample of the tree and no
  aggregate in this phase is computed from it; the capture file says so in its own `why` field.

- **`aggregate_frequencies` on a partial export returns partial dictionaries.** The tests never
  hand one to `ordering_errors`, which would raise a `KeyError` rather than report a missing
  position. Fine for the committed export, which is whole by construction, and worth a
  deliberate error message when the function is written.

## Alignment

- `PHASE-10-CONTRACT-MISCOUNTS-THE-FOUR-BET` - the whole-tree criterion glosses a four-bet as
  "the fourth raise, counting the open as the first", which is a miscount: a four-bet is the
  third raise. GTOpen labels the action `4-bet 22.5` and the tests assert on that label, so
  nothing is measured wrongly, but the parenthetical leaves the next reader unable to tell
  which reading the phase meant. Filed in `backlog.yml` for the next contract-update rather
  than halting the loop a second time for a gloss.
