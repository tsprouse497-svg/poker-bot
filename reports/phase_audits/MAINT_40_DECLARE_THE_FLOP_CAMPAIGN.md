# MAINT-40 audit packet: phase 21 declared

Taylor ruled on 2026-09-26 to trust the solve and buy more of it rather than measure the bot first.
Phase 16 built the flop machinery and closed on a sample, so nothing owned solving the rest. This
task declares phase 21, The Flop Campaign, as a skeleton the loop can start, and makes phase 19 wait
on it, which Taylor ruled the same day after being asked in plain words. It changes no range,
artifact, code path or test.

## What shipped

- `docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md`: skeleton, `depends_on: ["16"]`, placeholder
  command ids `pytest_flop_campaign` and `generate_flop_campaign_report`, which are not registered
  and so add nothing to the gate while the phase is `future`. Its scope names the three parts in
  order - use every core, pick the rented machine, run the campaign - and requires each solved board
  to close: every flop decision point reachable from a committed one is committed, or refused for a
  reason other than not having been committed.
- `phase_status.yml` gains 21 at `future`; `verification/loop_policy.yml` gains 21 with
  `auto_advance: false`, since it commits data and spends money.
- Phase 19's `depends_on` gains 21, with one sentence saying why.
- Both roadmaps place 21 in the table, graph and argument, and now say what phase 16 shipped:
  five flop decision points on four boards for one preflop line, 44 of 22,100 flops, 40 in the
  committed sample, and phase 16's measured table result of 20,000 hands with two postflop decisions,
  no bet and 5,365 voided hands. That closes `THE-ROADMAPS-STILL-SAY-THE-BOT-DOES-NOT-PLAY`.
- Backlog: twelve entries adopted by phase 21, each with the condition that closes it;
  `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` re-filed from completed phase 16 to `charts`;
  `A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE` left as `contract-update`
  with a note that 21's contract carries its terms; one new entry,
  `PHASE-19-IS-TOLD-THREE-WAYS-WHETHER-IT-FILLS-FLOP-GAPS`.

## How to check it without code

1. Open `data/artifacts/postflop/index.json` and count `entries`: five, on four distinct boards.
2. Open `docs/phase_contracts/PHASE_19_HEURISTICS_AND_MERGED_CHARTS.md` and read `depends_on`: 16,
   18 and 21. Compare with the table in `docs/ROADMAP.md`.
3. Open `phase_status.yml`: the last entry is 21, `future`.

## Independent review

One read-only reviewer that wrote none of this and ran no gate, three rounds, note at
`reports/phase_audits/reviews/MAINT_40_DECLARE_THE_FLOP_CAMPAIGN/independent-review.md`.

- **Blocker, resolved in round 3.** The skeleton framed the campaign as buying more boards, while
  phase 16's packet names two causes of its null result: too few boards, and no committed decision
  after any committed one. Part 3 now requires closure, and round 2 caught that "or refused by name"
  was satisfied by the sample that failed, so the refusal must have a reason other than not having
  been committed.
- **Non-blockers, all fixed.** Phase 19's new reason conflicted with its preflop-only lift; the
  `Ac8c3c` wording; three weak adoptions reverted and seven missed ones adopted; the roadmap closure
  was only partly earned; two rulings stated as settled that stage 2 may reopen, now carried as
  defaults with the CUDA clause and the code's 0.3% target named; the ranked list is a method and
  its order a stage-2 question; the five-thread cause is already in GTOpen's source, so part 1 now
  measures five against ten instead of assuming half speed. Round 2 added three closing-condition
  refinements and one re-file, all fixed.
- **Alignment, filed.** `PHASE-19-IS-TOLD-THREE-WAYS-WHETHER-IT-FILLS-FLOP-GAPS`.
- **Held back, and carried to phase 21's stage 2:** whether the line order should still come from
  the public set of real hands after phase 17 was retired, and whether "get more of the solve"
  includes closing each board or means boards and lines only.
- The coordinator made one mechanical edit to the review note, twice: id-shaped tokens the reviewer
  abbreviated were spelled out, because the citation check reads them as backlog ids.

## Gate

Green, 50 of 50, `check_gate_bite` included, on the review fixes and this packet. The closeout
edits are covered by the closeout gate.
