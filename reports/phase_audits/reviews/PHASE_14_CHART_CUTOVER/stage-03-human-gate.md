# Stage 3 review: phase 14 human gate

**This is a coordinator self-review, and the reason is concrete rather than a preference.** Three
attempts to spawn an independent read-only reviewer failed on the API: one `ECONNRESET` and two
`529 Overloaded`. `AGENTS.md` step 10 requires the concrete reason recorded and a self-review
performed in that case. Every stage of this phase so far has gone to an independent reader and this
one should be re-run by one when the API recovers; it is the weakest note in the phase for exactly
that reason, and stage 4's reviewer should read this stage's diff alongside its own.

Question the driver printed: *"Does the record now say what was actually ruled, including any cost
that was accepted rather than only the answer?"*

Scope read: `git diff cfd8eba -- docs/phase_contracts/PHASE_14_CHART_CUTOVER.md
reports/phase_audits/decisions/PHASE_14_CHART_CUTOVER_DECISIONS.md`.

## Blocker

- **[resolved] The re-solve criteria re-established two of the five proofs the current export
  carries, not all of them.** Written from memory of what phase 10 proved rather than from the
  source card, the first draft required the two-process determinism check and the node-count
  reconciliation and stopped there. Enumerating
  `data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.source.json` gives five distinct
  claims a new export invalidates: `determinism` (zero divergence, zero shape differences), `walk`
  (all 38,828 nodes re-resolved by their own recorded action sequence with zero mismatches),
  `node_counts` (exported equals the solver's own count), `export_sha256` together with the
  saved-solve checksum, and the `size` block. The walk is a separate proof from the determinism
  check - one asks whether two processes agree, the other whether the tree can be re-navigated by
  action sequence - and it was the one most easily lost, because the packet's prose runs them
  together. Fixed: the criterion now enumerates all five and says it does so from the source card
  rather than from memory.

- **[resolved] Nothing pinned the re-solved config to the ruled one.** Decision 2 permits a
  re-solve "at the ruled config at a tighter gap", and the contract's Non-goals forbid a second
  opening price, limps, another depth and another table size - but no criterion compared the new
  `config_posted` against the old. A re-solve that quietly changed `open_raises` or `max_raises`
  would have satisfied every other criterion in the section. Fixed: `config_posted` must be
  byte-identical apart from the solve target, asserted rather than trusted, and the contract says
  that is the only thing standing between the ruling and a second opening price arriving by
  accident.

- **[resolved] `model` was unguarded, which would have falsified decision 3's ruling.** Taylor
  ruled the realization bias accepted and recorded onto the artifact's source card. That statement
  is about `realization=calibrated`. A re-solve under a different realization model does not fix
  the bias, it makes the recorded description of it false while leaving the sentence in place.
  Fixed: the criterion pins the model.

## Non-blocker

- **Decision 2's record does show the pushback, which is the thing most worth having.** It states
  that Taylor first declined to pick and why - that 72.81 percent might be the solver's real answer
  - then gives the two facts that changed it: the dominance argument among pairs in an open-fold
  decision, and the committed solve stopping at 300 iterations against a 2,000 cap while this
  repo's own GTOpen notes say marginal hands converge last at that count. And it records the thing
  that made re-solving the ruling rather than the argument winning: the re-solve settles it in both
  directions, and if 44 holds near 72.81 after 2,000 iterations then the hypothesis was right and
  it ships as solved. A record showing only "re-solve" would have lost all of that.
- **Decision 9's arithmetic checks out.** A quarter-to-one multiple of the deltas +4.65, +3.72,
  +2.64, +6.14 and -2.67 gives +1.16 to +4.65, +0.93 to +3.72, +0.66 to +2.64, +1.54 to +6.14 and
  -0.67 to -2.67. All five recorded bands match to the digit, and the small blind's quarter figure
  rounds 1.535 to 1.54 correctly.
- **Every answered item records a cost.** Decision 1 names the 5.6 MiB left for the next solve
  against 9.8 under the stricter floor, and points at
  `ARTIFACT-SIZE-LIMIT-VERSUS-SOLVE-COVERAGE`. Decision 2 names the invalidated proofs. Decisions 4
  and 5 name the shared schema bump and, for 5, that the bytes are not free and may breach the cap.
  Decision 6 names what the two rejected options would have cost. Decision 3 names why a stated
  adjustment and solving elsewhere were rejected. Decision 10 names what a wrong tolerance does in
  each direction.
- **The "What the rulings changed about each other" section was written by the coordinator rather
  than found by a reviewer, and that is worth saying plainly.** It records that decision 1's
  threshold survives while its 5,626 spots and 10.3 MiB do not, because decision 2 re-solves and
  changes the reach values, decision 5 adds bytes per cell, decision 4 adds a fixed cost, and
  decision 6 adds roughly 4,257 sizing entries at about 55 bytes each. It also records that
  decision 9's band survives the re-solve *because* it is ruled as a multiple of the deltas rather
  than as absolute points. An independent reader should test whether that reconciliation is
  complete; I wrote it, so my finding it complete is worth little.
- **One consequence of decision 2 the record states but does not fully price.** If the re-solve
  moves anything beyond the marginal cells, the contract says that is a human read of the range
  grids rather than a number in a report. That is right, and it means this phase can stop for
  Taylor a second time at stage 6. The ExecPlan should say so, since a lane that unexpectedly needs
  a human is worse than one that expected to.

- **The contract is at 298 of 300 lines and that is two lines of headroom, not comfort.** The
  amendment this stage added pushed it to 301, and getting back under took four compressions of
  prose that had nothing to do with the ruling. That is the same trap phase 13 hit twice, filed as
  `ENGINE-FIDELITY-CONTRACT-IS-AT-ITS-LINE-CAP` and `PHASE-AUDIT-PACKET-AT-ITS-LINE-CAP`, arriving
  in a contract three days old. Stage 6 will owe this contract at least one correction and there is
  no room for it, so the next edit is a rewrite rather than an amendment - which is what `AGENTS.md`
  prescribes, and which this phase should plan for rather than discover.

## Alignment

- `EXPORT-SOURCE-CARD-HAS-NO-REQUIRED-PROPERTY-LIST` - the properties an export must establish
  live only as prose in a packet and a source card written by the same task, so a later phase
  replacing an export re-derives the list from memory; this stage lost the walk proof that way and
  caught it by enumerating the file, and the list belongs somewhere a check can read it.
- `RESOLVE-PERMISSION-HAS-NO-CONFIG-EQUALITY-CHECK` - `check_solver_export_expectations` recomputes
  the orderings and validates the source card but never compares a new export's `config_posted`
  against the ruled configuration, so "the same game solved longer" and "a different game" are
  indistinguishable to the gate.
- `STAGE-REVIEW-HAS-NO-RETRY-RECORD` - the loop requires a review note per stage and accepts a
  self-review with a recorded reason, but nothing records that a self-review is outstanding or
  prompts a later stage to re-run it independently, so an API outage silently downgrades a stage's
  review quality for the rest of the phase.
