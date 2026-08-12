---
phase_id: "08"
title: "Tiny Normalized Sample Ingestion And Player Tendency Comparison"
depends_on:
  - "07"
required_gate_commands:
  - pytest_sample_comparison
  - generate_sample_comparison_report
required_reports:
  - reports/active/latest_sample_comparison_report.txt
  - reports/active/latest_sample_refusal_inventory.txt
required_phase_audit: reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md
---

# Phase 08: Tiny Normalized Sample Ingestion And Player Tendency Comparison

## Scope
Every number this repo has produced so far was checked against itself.
The engine is checked by the replayer, the simulator is checked by the replayer, and
all three were written from the same understanding of the rules by the same model.
Phase 07's report says its cross-check is the thing that matters most, and it is, but
both sides of that comparison came from inside this tree.

This phase brings in a hand corpus nobody here wrote, converts a small committed slice
of it into the Phase 02 normalized schema, and settles those hands through the Phase 02
replayer against the corpus's own record of what each player finished with.
That is the first check in the repo whose right answer was written by somebody else.

It then asks the second question the phase title names: given the same spot and the
same hole cards, what would this bot have done, and what did the people actually do.

It is limited to the work named by this contract and the active ExecPlan.

## Non-goals
- Do not add PokerNow automation.
- Do not add browser or platform observation.
- Do not add runtime solver calls.
- Do not add LLM-backed poker decisions.
- Do not add training UI surfaces.
- Do not ingest the corpus at scale.
  A tiny committed slice is the whole scope; bulk hand-history ingestion is a V1
  boundary and stays one.
- Do not compare postflop play.
  Phase 06's fallback never bets, so a postflop comparison would measure the fallback's
  known shape rather than anything about these hands.
- Do not change the charts, the strategy, or the engine in response to what the
  comparison finds.
  A finding of this phase becomes a `backlog.yml` entry.
  Editing the thing being measured so it agrees with the sample destroys the
  measurement and leaves nothing behind that says it happened.

## Acceptance criteria

### The corpus is a source with provenance, not a fixture we wrote
- The committed sample carries a source card naming the publisher, the stable public
  identifier the corpus is retrievable by, the licence and the attribution it requires,
  the retrieval date, and a checksum over exactly the committed hands.
  Provenance is the one property of committed data a checksum cannot establish on its
  own, so it is written down and reviewable rather than implied by a filename.
- The selection rule is deterministic, stated in the contract-facing documentation, and
  reproducible: re-running it against the same corpus yields the same hands in the same
  order, byte for byte.
  Hands are not chosen by hand, by sampling, or by anything a rerun cannot repeat.
- The corpus's own settlement record is carried through verbatim and is never derived
  from this repo's replay.
  An oracle computed from the thing it is checking is a mirror, and the whole phase
  rests on it not being one.
- The sample is committed alongside the normalized hands it produced, so a reader can
  see the input, the output, and the rule that connects them without network access.

### Conversion is proved by the corpus, not by us
- Every committed hand converts into the Phase 02 normalized schema and replays through
  the Phase 02 replayer, which is consumed unchanged.
  Nothing in the schema or the replayer is loosened to make a real hand fit; a hand that
  does not fit is a finding about this repo, which is the point of importing it.
- For every hand and every seat, the stack the replayer settles to reproduces the
  corpus's own finishing stack exactly.
  A single seat off by a single chip on a single hand fails the gate.
  This is the phase's central criterion and everything else in it is secondary.
- Conversion is total or it is loud.
  A hand the converter cannot express fails with a named reason, is counted, and is
  reported; it is never dropped quietly, and the reported rates state how many hands
  they were computed over.
- The action-vocabulary mapping is explicit and pinned by tests.
  The corpus's aggressive action becomes a `bet` or a `raise` according to whether the
  street already carried a wager, its passive action becomes a `check` or a `call`
  according to whether anything is owed, and each amount is converted into the Phase 02
  meaning of that field rather than copied across.
  Added chips and a target total are different numbers, and a converter that confuses
  them produces hands that replay and settle wrongly.
- The seat and position mapping is explicit and pinned by a test that names the position
  of every seat in a stated hand.
  The corpus places the blinds, the blinds fix the button, and the button fixes the
  canonical Phase 04 position vocabulary.
  An error here does not raise; it produces a confident comparison against the wrong
  chart cells, which no aggregate number would reveal.

### What the comparison may and may not claim
- The report states, in plain language and before any number, that the comparison is
  preflop only and why, carried forward from Phase 06 rather than restated loosely.
- For every preflop decision point in the sample the comparison records the spot key,
  the acting player, their hole cards, the action they took, and what the strategy
  returns for the same query.
- Agreement means the observed action carries nonzero weight in the strategy's own
  distribution, not that it matched a sampled action.
  A strategy that raises a hand three times in ten does not disagree with a fold, and
  scoring it as a disagreement would measure the seed rather than the strategy.
  The sampled-action match rate may also be reported, labelled as the different thing it
  is.
- A spot the chart refuses is reported as a refusal and is never counted as a
  disagreement.
  A missing chart cell and a wrong chart cell are different findings, and folding the
  first into the second makes absent coverage look like bad strategy.
- The refusals are inventoried the way Phase 07 inventories them: keyed by the refusal's
  own detail rather than re-derived, with the number of decision points that reached
  each spot, most frequent first, in a file of its own so its diff is the record of
  coverage against real hands improving.
- The report says which refused spots also appear in the self-play inventory and which
  are new.
  A gap that only real hands reach is a different priority from one the simulator
  already found, and that comparison is the most actionable thing this phase produces.
- Real players are not an oracle for strategy quality, and the report says so.
  A disagreement means this chart and this player differed in this spot; it does not
  establish that either is wrong.
- Where the corpus distinguishes its players, the report reports them separately rather
  than pooling them, and says what each population is.
  A near-equilibrium machine and a human are different measurements and an average over
  both is neither.
- Every rate is printed with the count it was computed over.
  The report does not present a rate whose denominator it hides.
- At least one number in the report is recomputable by hand from a committed file
  without reading code, and the audit packet says which number and how.

### Reports and gate
- Required command IDs pass through `scripts/run_verify.py`.
- Required reports exist and are fresh for this phase.
- The report is a pure function of the committed sample: the same committed files
  produce the same report byte for byte, with no clock, network, or process input.
- The gate stays within a run time a person will actually wait for, and the number of
  hands the gate ingests is stated in the report rather than tuned silently.
- The phase audit packet includes plain-language pass/fail evidence.
- The judgment calls recorded in
  `reports/phase_audits/decisions/PHASE_08_SAMPLE_COMPARISON_DECISIONS.md` carry a
  reversibility class before implementation begins, and the audit packet records the
  outcome of each one.
- Any deferred work is recorded in `backlog.yml`.

## Required reports
- `reports/active/latest_sample_comparison_report.txt`
- `reports/active/latest_sample_refusal_inventory.txt`

## Required command IDs
- `pytest_sample_comparison`
- `generate_sample_comparison_report`

## Human vetting packet requirements
- Plain-language summary of what changed.
- Pass/fail checklist for a non-coding reviewer.
- Command summary with links to committed reports.
- The source card for the committed sample, including licence and attribution.
- The settlement evidence: how many hands were checked against the corpus's own
  finishing stacks, how many seats that is, and how many disagreed.
- A plain statement of what the comparison measures and what it does not.
- The refusal inventory against real hands, and which of its spots are new relative to
  the self-play inventory.
- The recorded judgment calls and what each one changed.
- Known limitations and deferred items.

## Forbidden shortcuts
- Do not replace deterministic checks with mocked success.
- Do not mock the replayer, the converter, the strategy, or the corpus.
  A conversion checked against a fake corpus has been checked against nothing.
- Do not compute the settlement oracle from this repo's own replay, in whole or in part.
- Do not drop, skip, or exclude a hand the converter cannot handle in order to keep a
  rate clean.
- Do not select hands by how the bot performs on them, or reselect after seeing a
  result.
- Do not report an agreement rate without stating whether refusals are in its
  denominator.
- Do not infer missing strategy, chart, or hand-history behavior.
- Do not present a disagreement with a human player as evidence that the chart is wrong.
- Do not change this contract during implementation mode.

## Regression expectations
- Previously completed phase gates remain verifiable.
- The Phase 02 schema and replayer, the Phase 04 lookup, and the Phase 05 and 06
  strategies are consumed unchanged; none is loosened to make a real hand fit.
- Generated human docs remain current.
- File-size and scope checks continue to pass, including the committed sample size cap.
