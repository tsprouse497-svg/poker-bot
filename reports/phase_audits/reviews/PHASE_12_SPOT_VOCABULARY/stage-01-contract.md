# Stage 1 Review - Phase 12 Contract And ExecPlan

Read-only pass over `git diff bbfc306 -- docs/exec_plans/active/PHASE_12_SPOT_VOCABULARY.md
docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md`, against the question the driver printed:
is any acceptance criterion unfalsifiable, a restatement of the phase title, or satisfiable
without doing the work it names?

Subagents are unavailable in this operator's sessions, so this is a coordinator-written
self-review under `AGENTS.md` step 10. The no-delegation exception is recorded in the
ExecPlan's Delegation Plan. Both findings below were fixed inside the contract, which is why
these notes land in the same commit as the text they reviewed.

Reading was against the code rather than against the backlog's prose:
`solver_artifacts/schema.py` (the `spot_key` derivation and its single-orbit rejection),
`solver_artifacts/lookup.py` (`ChartQuery.spot_key` returning `None` and
`MISS_UNREPRESENTABLE_SPOT`), `strategy/contract.py` (`SeatAction` carries no amount),
`strategy/preflop_chart.py`, `strategy/preflop_sizing.py`,
`scripts/convert_preflop_export.py`, and the committed source export's action labels.

## Blocker

- **[resolved] The price criteria silently generalised ruling 8 from opens to every raise.**
  Ruling 8 says an opponent *open* at any size is answered from the 2.5 cell. The criteria as
  first written said "the observed price is normalised to the nearest solved price", which
  covers three-bets and four-bets too. That generalisation is almost certainly the right
  engineering answer - the corpus's three-bet sizes vary as much as its opens, and exact
  matching there would collapse the raised-pot sample exactly the way the mitigation document
  warns exact open matching would have collapsed the opened-pot one - but a phase that widens
  somebody else's ruling without saying so has taken the decision away from them, which is
  the specific failure the decision list exists to prevent. Fixed: the extension is now named
  as an extension in the criteria, it is required to be carried as a judgment call in the
  decision list, and the substitution census must split the open from the later raises so a
  reader can see how much of the measured cost belongs to the ruling and how much to this
  phase's widening of it.

- **[resolved] The absent-position rule was wrong as written and a test author would have
  frozen the error.** The criterion said a position absent from an earlier orbit cannot
  appear in a later one. Within a single orbit that is false: after `LJ` opens and `BTN`
  three-bets, `SB` and `BB` are absent because their turn has not come, not because they
  folded, and `t6/d100/LJ/LJ:raise,BTN:raise` is a key v1 already accepts on exactly that
  reading. A test authored from the original wording would have asserted a rejection that
  must not happen, and stage 5 would have frozen it. Fixed: the rule is now stated over
  positions the action has already passed, with the still-to-act case named as legal.

## Non-blocker

- `schema.spot_key` staying the only place a key is derived is review-checkable and not
  test-checkable; no test can prove a second derivation does not exist. The criterion now
  asks for the sweep in the audit packet, which is the shape Phase 11 used for its command
  registry.
- The producer criterion originally hard-coded "all four producers" off a grep. A count in a
  contract fails for a bookkeeping reason if a fifth producer exists or a test constructs
  one, so the criterion is now the sweep and the four names are given as what is there at the
  branch point.
- The stack-depth affordability check is new work that only becomes possible once the key
  carries sizes, and it was implicit in "a legal preflop order at the stated stack depth".
  Now its own bullet, so it is chosen rather than smuggled in. It is also what keeps an
  uncapped orbit count honest.
- "Every number the Phase 07 and Phase 08 audit packets quote" is unbounded until somebody
  enumerates it. Not weakened, because that scope is what
  `PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT` was filed as; stage 2 owes the enumeration so
  the criterion has a countable denominator before any test is authored against it.
- The skeleton's `generate_spot_coverage_report` was replaced by
  `generate_spot_vocabulary_report`. `generate_preflop_chart_report` already reports chart
  coverage, and this phase reports what the vocabulary can say rather than what the chart
  holds. The reason is recorded in the ExecPlan's S1 slice so the dropped placeholder is not
  read later as an omission.

## Alignment

- `LOOP-LANE-POINTERS-NEVER-RETIRE` - opening this lane made a bare `loop_stage.py` refuse
  with "3 lanes in this worktree (11, 12, loop_state)" while `loop_fleet.py --status`
  correctly reported no lanes running. `run_paths()` calls its result `live` but returns every
  pointer under `verification/loop_runs/` plus the legacy `loop_state.yml`, and nothing
  retires a pointer at closeout, so the count only grows. This stage cannot fix it: the fix is
  a ruling about what retires a pointer and what `live` means, and `docs/LOOP.md` still
  documents the bare invocation as the ordinary way to ask what stage you are on. Filed.
</content>
