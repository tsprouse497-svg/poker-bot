# MAINT-40 independent review

- **Reviewer**: read-only subagent. I wrote none of the change under review.
- **Change**: `git diff bb1f5ff..HEAD` on `maint/40-declare-the-flop-campaign`, one commit, `6eb0de4`.
- **Method**: read AGENTS.md, the diff, the phase 21 and 19 contracts, both roadmaps, the loop
  policy, the touched backlog entries, phase 16's audit packet and decision list, the committed
  postflop index, objects list and sample, and GTOpen's server source. I recomputed every figure
  from committed data: I enumerated all 22,100 three-card flops, grouped them by suit isomorphism,
  and read the board sizes; I counted index entries and sample files. I ran only read-only checks:
  `check_contracts`, `check_repo_consistency`, `check_scope`, `check_execplan_delegation`,
  `check_file_sizes`, the three generators with `--check`, and `loop_fleet.py --plan`. All exited 0
  and the tree was clean afterwards. I did not run `run_verify.py` or `check_gate_bite.py`.

Counts: **1 blocker, 8 non-blockers, 1 alignment item.**

## 1. Phase 21 is declared the same way everywhere - passes

- Contract frontmatter `docs/phase_contracts/PHASE_21_FLOP_CAMPAIGN.md:1-13`, `phase_status.yml:100-104`
  (`future`), `verification/loop_policy.yml:146-156` (`auto_advance: false`, `needs_human_data: false`),
  `STATUS.md:32`, `docs/PHASE_LEDGER.md:24`, `docs/ROADMAP.md:24`, `docs/V2_ROADMAP.md:77-83`. The
  title, contract path and audit path match everywhere. All three generators pass `--check`.
  `check_contracts` and `check_repo_consistency` pass.
- Placeholder IDs `pytest_flop_campaign`, `generate_flop_campaign_report` and
  `reports/active/latest_flop_campaign_report.txt` carry no phase number, so they follow the naming
  rule. They are not in `COMMANDS` yet, and neither are the placeholders for phases 18, 19 or 20.
  That is the MAINT-35 pattern and is fine while the phase is `future`.
- The contract is 114 lines, well under 300.
- `loop_fleet.py --plan` run from this worktree plans against `main`, so it cannot list 21 until
  the merge. The ExecPlan's verification line (`MAINT_40...md:61-63`) correctly says to check it
  from `main` after the merge.

## 2. Phase 19's new edge, and the graph drawing

- The edge is stated the same way in `PHASE_19...md:4-7` and `:39-41`, `docs/ROADMAP.md:25` and `:53`,
  and `docs/V2_ROADMAP.md:87` and `:91`.
- The drawing at `docs/ROADMAP.md:32-37` matches every contract's `depends_on`. Checked edges:
  14→16, 14→18, 16→21, 18→19, 21→19, 16→20 and 19→20. The 16→19 edge is drawn through 21, and
  line 39 says so. No cycle.

### N1 (non-blocker) - the first reason given for the new edge conflicts with phase 19's own non-goals

The new sentence (`PHASE_19...md:39-41`, repeated at `ROADMAP.md:53` and `V2_ROADMAP.md:91`) says
19 waits on 21 "so no rule of thumb is written for a spot the campaign then solves". The two
contracts' own scopes make that set empty:

- `PHASE_19...md:56-57`: "The lift this phase carries is for missing *preflop* chart spots and
  reaches no further." Line 56 also forbids mapping an unsolved board onto a solved one.
- `PHASE_21...md:68-69`: phase 21 does not solve missing preflop spots.

So 19 writes heuristics only for preflop spots, and 21 solves only flop spots. No spot is both. The
reason holds only if 19 also fills flop gaps. Its own contract (line 37, "the flop cells there are
anything to merge with") and `V2_ROADMAP.md:91` ("so flop gaps are in scope alongside preflop ones")
lean that way. Its non-goal at line 56 leans the other way. The second reason, measuring the merge
against the bot the campaign leaves, stands on its own.

Fix: lead with the second reason, or make the first conditional ("if 19 fills flop gaps at all").
Also add this sentence to the ROADMAP line.

### A1 (alignment item) - whether phase 19 fills flop gaps is stated three ways

Before this commit, `PHASE_19...md:37` and `V2_ROADMAP.md:91` already said flop gaps are in 19's
scope, and `PHASE_19...md:56-62` already said its lift is preflop-only. MAINT-40 rewrote the
`ROADMAP.md:53` and `V2_ROADMAP.md:91` sentences and carried the claim forward. Settling it is phase
19's stage-1 job, not this task's. It should be filed in `backlog.yml` so stage 1 meets it; I found
no entry that owns it.

## 3. Figures - every number is true of the tree; two wordings are not

Recomputed:

- `data/artifacts/postflop/index.json` has 5 entries (five decision points) on 4 boards: `9c8c7c`,
  `Kh7d2c` twice, `8c8d3c` and `Ac8c3c`. They cover one action sequence, BTN opens 2.5 and BB calls,
  seen from two seats (`covered_preflop_lines` lists two keys).
- Suit-isomorphism class sizes: 4 + 24 + 12 + 4 = **44** of **22,100**. The sample's boards give
  4 + 24 + 12 = **40**.
- `data/artifacts/postflop/sample/` holds 4 files on 3 boards. `Ac8c3c` is in the index and in
  `objects.json` `listed_not_held`, and there is no sample file for it.
- `reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md:43-53`: seed 777, 20,000 hands, 2 postflop
  decisions both a check, 0 bets, 0 showdowns, 5,365 voided. The old fallback reached 4,543
  showdowns. All match.
- Decision numbers in `reports/phase_audits/decisions/PHASE_16_POSTFLOP_BETTING_DECISIONS.md`:
  - 1 is flop only (line 197, ruling at 12).
  - 20 is f32 arenas and 0.40 (line 2142).
  - 22 is 0.40 stands (line 2318).
  - 24 is that the rented box binds the campaign, and that the specification was left open
    (line 2379).
  - 25 is closing on machinery rather than coverage (line 2424).

  All five are cited correctly.

### B1 (blocker) - the campaign is framed as buying more boards, and the packet says boards were only half the cause

The packet names two causes of the null result (`PHASE_16_POSTFLOP_BETTING.md:55-75`):

- **Coverage**: 40 of 22,100 flops.
- **Closure**: "not one of those eleven is committed or indexed". Nine uncommitted situations are
  still on the flop. There is no two-move sequence in the artifact. Both decisions the run produced
  die at the very next situation.

The skeleton and both roadmaps carry only the first cause:

- `PHASE_21...md:30` and `ROADMAP.md:9` say the bot refuses "on every other flop". That implies it
  plays the 40 flops it holds. It does not: it refuses one action later on those flops too.
- Part 3 (`PHASE_21...md:44-46`) solves down lines "as many as cost and index allow". Nothing says a
  solved board must commit every flop situation in its tree. A campaign could meet this skeleton
  with many more boards and the same voided hands. That is exactly the outcome Taylor's "get more of
  it" ruling is meant to avoid, and the roadmap's own table result would repeat.
- `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN` owns this gap. It is still
  `deferred` against completed phase 16 and was not adopted.

The fix is cheap and is prose only:

1. Adopt that entry.
2. Name closure in part 3, for example "every flop situation reachable from a committed one is
   committed or refused by name".
3. Reword the "every other flop" clause in `PHASE_21...md:30` and `ROADMAP.md:9`, for example "and
   on those it refuses one action later, because the next situation is not committed".

### N2 (non-blocker) - `Ac8c3c`'s bytes are described wrongly

`PHASE_21...md:29-30` says the fifth cell "is indexed with its object held outside git". Every
object is held outside git: `objects.json` gives each `object_path` under
`/Users/taylorsprouse/poker-bot-solve-objects/postflop/`. What sets `Ac8c3c` apart is that its
**cell document** is outside git (`listed_not_held.cell_document`) and it has no sample file, so a
fresh clone cannot play it. Reword to say that.

## 4. Backlog adoptions

All seven exist, and each is re-labelled to `"21"` with a dated note. `docs/BACKLOG.md` is
regenerated.

The campaign clearly owns four of them:

- `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`
- `EVERY-ARENA-FIGURE-IN-THE-COST-RECORD-IS-A-QUANTIZED-ARENA-AND-FULL-PRECISION-ROUGHLY-DOUBLES-IT`
- `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`
- `THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR` (the driver's ceiling tracking
  the rented box's memory matters there, and 21's stage 4 can write the tests that bite)

### N3 (non-blocker) - three adoptions are weak or misfiled

- **`A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE`** (`backlog.yml:705`).
  The only open part is phase 16's contract wording. That contract is at 299 of 300 lines, so fixing
  it needs the fold-in rewrite. AGENTS.md (Contract Amendments) says that rewrite "is its own
  `contract-update` task". The new note (`backlog.yml:732`) instead plans for phase 21's stage 1 to
  do it. That also splits a family: the siblings that need the same rewrite stay `contract-update`.
  They are `A-CONTRACT-CLOSED-LIST-ASSERTS-A-CLOSURE-ITS-PHASE-REFUSED-ON-EVIDENCE`,
  `A-CONTRACT-CLAUSE-ASSERTS-A-GAP-ITS-OWN-PHASE-THEN-CLOSED` and
  `THE-GATE-ENFORCES-A-SEAM-SENTENCE-THIS-PHASE-MEASURED-AS-FALSE`. The half phase 21 carries (rented
  box, determinism re-proved) is already in 21's own contract. Recommend leaving this entry at
  `contract-update` with its siblings, with a note that 21's contract carries the campaign half.
- **`SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS`** (`backlog.yml:4495`). Its own 2026-09-22 restatement
  says the driver half is discharged, and the half left open is `scripts/extract_gtopen_preflop.py`.
  That is the preflop extractor, and phase 21's non-goal (`PHASE_21...md:68-69`) forbids preflop
  solves. On a Linux rented box the postflop premise (no `/proc/meminfo`) goes away. So phase 21
  can at most confirm that, and cannot close the open half.
- **`THE-COST-MODEL-S-RANGES-ARE-RECORDED-ONLY-AS-DIGESTS-OF-DATA-THAT-IS-NOT-HERE`**. Its stated fix
  is a repo-wide rule, that a measurement report commits the inputs it was measured on. That is not
  campaign work, even though the campaign should follow the rule.
- All five notes from phase 16 or `contract-update` share one boilerplate sentence ("the flop
  campaign is the work this entry waits on"). None says what phase 21 does to close its entry.

### N4 (non-blocker) - entries the campaign should own that were missed

49 deferred entries are still filed against completed phase 16. There were 53 before this commit,
and it moved 4. `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` already records the general blind
spot. Besides B1's `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`, these bear
directly on the campaign:

- `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL` (phase 16). Rainbow flops are 455 of the 1,755 classes
  and are the costliest per iteration. Part 2 prices cost per solved flop, so that price is biased
  low without a rainbow timing.
- `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY` (phase 16). The campaign is what closes it.
- `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS` (phase 16). This is the coverage
  ceiling (multiway is structural). The vetting line at `PHASE_21...md:100-101` asks how many flops
  the bot can play, and it needs this ceiling.
- `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT` (`contract-update`). A campaign that
  puts everything in object storage makes "fresh clone versus provisioned machine" the headline
  distinction in that same vetting line.
- `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT` (phase 16). It counts lines
  and seats under one word. The vetting line counts "preflop lines", and the index already lists 2
  for one line.
- `QUANTIZED-ARENAS-PUT-A-FLOOR-UNDER-EVERY-EXPLOITABILITY-THIS-PHASE-MEASURED` and
  `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED` (phase 16). The campaign
  is the first f32 run at scale, and whether frequencies settle is a question about every cell it
  commits.

Adopt them or name them. At minimum, adopt the rainbow cost entry and the fresh-clone entry.

### N5 (non-blocker) - closing `THE-ROADMAPS-STILL-SAY-THE-BOT-DOES-NOT-PLAY` is only partly earned

- The entry names `docs/ROADMAP.md` opening with "The bot does not play yet" as a defect
  (`backlog.yml:424`). That sentence survives unchanged at `ROADMAP.md:9`, and the closing note
  (`backlog.yml:432`) does not mention it. It may now be defensible, since 0 bets in 20,000 hands is
  not playing. If so, the closing note should say it was kept on purpose and why. Otherwise reword
  it.
- `docs/V2_ROADMAP.md:51-67` still lists "### 16. Postflop That Can Bet" under "The phases ahead",
  in the future tense ("It is the phase that makes this a bot that plays"; "Commits a postflop
  solution or a rule"). `ROADMAP.md` dropped 16 from its Ahead table in this same commit, so the two
  roadmaps now disagree on whether 16 is ahead. That section still describes the postflop state from
  before phase 16 landed, which is the entry's own title.
- The two paragraphs the entry named were restated correctly, and the figures are cited.

## 5. Boundaries and stage-2 questions

- No boundary lift is anticipated. The non-goals (`PHASE_21...md:67-78`) restate every AGENTS.md
  boundary, keep suit isomorphism as the only collapse allowed, and forbid spending before Taylor
  rules the provider, the candidates and a cap.
- Nothing names a provider, CUDA, a storage location or payer, or an exploitability target.

### N6 (non-blocker) - two rulings are stated as settled that stage 2 may need to ask

- `PHASE_21...md:48-50` says the 0.40 ceiling (decisions 20 and 22) is "not reopened here".
  - Decision 22 is `runtime-reversible`.
  - The 0.40 is a fraction of the laptop's physical memory. A GPU box's binding limit is a
    different memory entirely.
  - The adopted `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT` entry says its fix "belongs in the same task as any future
    move of `MEMORY_CEILING_FRACTION`, because the two numbers multiply".

  Adopting that entry while declaring the ceiling closed is a contradiction. Say instead that 0.40
  stands unless stage 2 asks Taylor on the chosen machine.
- `PHASE_21...md:43` says the machine is chosen "on cost per solved flop with the memory a solve
  needs as a hard limit". That is a selection rule, and the ExecPlan's record of Taylor's rulings
  (`MAINT_40...md:17-23`) does not contain it. Either record it as his, or mark it as the proposed
  default for stage 2 to ask.

### N7 (non-blocker) - "the ranked list of preflop lines phase 16 defined" does not exist as a list

- Decision 3 (`DECISIONS.md:298-333`) rules a method, not a list: rank by how often lines are
  reached, and the 2026-09-10 annotation adds "sort on servable arrival frequency".
- `reports/active/latest_postflop_betting_report.txt:40-44` says "every servable count is zero and
  there is no servable order to read". What it prints is the arrival order from the 499-hand public
  corpus. That order disagrees with the chart's own `arrival_ppb` order at rank 1 (line 80).
- The line at rank 4 is `SB:call`, a limped pot, which 21's own non-goal excludes.
- Phase 17 was retired because the bot is not judged by how real players play, yet this ranking is
  the corpus's.

Which order ranks the campaign is a stage-2 question. The skeleton should say that, not imply that
the list is settled.

### N8 (non-blocker) - part 1's "find out why" is already answered in the repo

- Decision 24's 2026-09-22 correction (`DECISIONS.md:2412-2415`) records the cause: GTOpen takes
  half of `available_parallelism()` unless `SOLVER_THREADS` overrides it.
- GTOpen's source confirms it (`~/projects/gtopen/crates/server/src/main.rs:2546-2562`). It halves
  on purpose, with the comment "SMT hurts this memory-bound workload; default to physical cores".
  SMT is hyperthreading, two logical cores per physical core.
- Apple's M4 has no SMT, so the halving is wrong there, and an environment variable fixes it with no
  patch.
- On an SMT x86 rented box the halving may be right.

`PHASE_21...md:34-39` and `V2_ROADMAP.md:81` ("every timing on record may be at half speed") assume
more threads means faster, and the source's own comment says this workload is memory-bound. The
wording should be "measure 5 against 10", as the adopted entry itself says. The phrase "a patch
lives in a local clone" should become "set `SOLVER_THREADS`, or patch if that is not enough".

## 6. Other lines this commit touched

- `CURRENT_TASK.yml`: the scope and dated `scope_change_log` entry are consistent. `check_scope`
  passes.
- ExecPlan: the Delegation Plan exception is about the work (transcribing rulings), not the session,
  so it qualifies. The Next Agent Bootstrap `--start-lane 21` form matches `loop_fleet.py` output.
- Loop policy reason (`loop_policy.yml:149-156`): accurate. `needs_human_data: false` is right,
  because part 1 can start on the laptop.

## What I held back

- `A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE`'s reason, which this commit appended to, still says "floating-point
  summation order differs between machines". Decision 24's 2026-09-22 correction retracted that
  mechanism. It is stale, but it predates this commit.
- `ROADMAP.md:55` says a bot "that folds every flop". The shipped bot refuses and voids the hand;
  it does not fold. That line predates this commit and was not touched.
- `ROADMAP.md:9`, "Phase 21 is the declared phase that buys more of it": "it" has no clear
  antecedent. V2 says "more coverage", which is clearer.
- "one preflop line" against the index's two `covered_preflop_lines` is correct per the packet and
  `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`, but a reader of `index.json` alone will count 2. The contract could say
  "one line, seen from both seats".
- `generate_flop_campaign_report` names the effort, not the content (a coverage report). It is a
  placeholder, so I only mention it.
- Phase 16's contract (`PHASE_16...md:29-31`) says no run uses GTOpen's untested CUDA speedup until
  one flop is solved and timed on the box. Phase 21's skeleton does not carry that condition. That
  may be deliberate, leaving CUDA to stage 2, but it is a binding phase-16 clause, and 21's contract
  names the phase-16 rulings it keeps and leaves this one out.
- The code constant `EXPLOITABILITY_TARGET_PCT_OF_POT = 0.3` (`postflop_artifact.py:71`) will
  silently become the campaign's target unless stage 2 asks. The skeleton rightly does not rule it,
  but nothing flags that the default is already in code.

Questions outside the brief the coordinator could have asked:

- Does the campaign's line ranking stay corpus-based after MAINT-39 retired the "copy real players"
  view (N7)?
- Is closure (committing every flop situation reachable from a solved one) part of "get more of the
  solve", or a separate ask for Taylor (B1)? He may have meant boards and lines only. If so, he
  should be told the measured table result will not move much on boards alone.

## Round 2

- **Checked**: `git diff 6eb0de4..3b7771c`, the whole diff, read-only.
- **Checks rerun**: `check_contracts`, `check_repo_consistency`, `check_scope`, `check_file_sizes`,
  `check_execplan_delegation`, and the three generators with `--check`. All exit 0. The contract is
  now 136 lines. This file is byte-identical to the committed version, apart from the three ids the
  coordinator expanded. The tree was clean before I appended this section.
- **Counts**: B1 still open (one short edit left). Of N1 to N8, 6 fixed and 2 partly fixed. A1 filed.
  Three new non-blockers.

### B1 - partly fixed in round 2

[resolved] Resolved in round 3 by commit 236df43: the escape clause now requires a reason other than not having been committed, in both `PHASE_21_FLOP_CAMPAIGN.md` part 3 (lines 55-58) and the adoption note on `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`. See Round 3.

What is fixed:

- The framing now names both causes, in `PHASE_21...md:30-33` and `ROADMAP.md:9`.
- Part 3 demands closure (`PHASE_21...md:54-56`).
- The owning entry is adopted (`backlog.yml:10157`, note at the end of the entry).
- `V2_ROADMAP.md:83` states it the strong way: "every flop decision point that follows a committed
  one".

What still lets the campaign repeat phase 16's null result is **the escape clause, which is my own
round-1 wording, and I was wrong to offer it**. The contract (`:55`) and the adoption note both say
closure is met when every reachable decision point is "committed **or refused by name**". Phase 16's
sample already refuses every successor by name. The packet says "The refusal even names the key it
could not find" (`PHASE_16_POSTFLOP_BETTING.md:75`). So a campaign that commits root cells only, as
phase 16 did, meets the criterion as written and voids the same hands. The contract and V2 also now
disagree: V2 has no "or refused" clause.

Fix, one phrase in both places: "committed, or refused by name for a reason other than not having
been committed - for example the exploitability ceiling or an off-menu size".

### N1 to N8 and A1

| Finding | Status | Evidence |
| --- | --- | --- |
| N1 | Fixed | The reason now reads "any rule of thumb written for a flop covers only what the campaign could not solve". That holds whichever way 19's flop question is settled. See `PHASE_19...md:39-43`, `ROADMAP.md:53`, `V2_ROADMAP.md:93` and `PHASE_21...md:83-85`. |
| N2 | Fixed | `PHASE_21...md:29-30`: "indexed but its cell document is not in git". |
| N3 | Mostly fixed | `A-SCOPE-SENTENCE-BINDS-THE-CAMPAIGN-AND-READS-AS-BINDING-THE-SAMPLE` is back at `contract-update`, with a note that also records the retracted mechanism (`backlog.yml:721-749`). `THE-COST-MODEL-S-RANGES-ARE-RECORDED-ONLY-AS-DIGESTS-OF-DATA-THAT-IS-NOT-HERE` is back at `contract-update`, with its adoption note removed. Every adopted entry now carries its own closing condition. `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` went back to `"16"` - see R2 N3. |
| N4 | Fixed | All seven entries I named are adopted and listed in `PHASE_21...md:67-78`, twelve in all. |
| N5 | Fixed | The closure note explains why "The bot does not play yet" stays (`backlog.yml:448`). `V2_ROADMAP.md:55` marks 16 completed. `ROADMAP.md:55` and `V2_ROADMAP.md:101` no longer say "folds". |
| N6 | Fixed | `PHASE_21...md:59-65`: stage 2 may reopen a ruling through its own decision, the ceiling is marked `runtime-reversible` and tied to the over-read, the CUDA clause is carried, and the 0.3% constant is flagged to ask. The cost-per-flop rule is now recorded as Taylor's (`MAINT_40...md:19-22`). I cannot verify what Taylor said in session; I note it as recorded by the coordinator. |
| N7 | Partly fixed | The contract (`:49-54`) says decision 3 rules a method, not a list, and makes the order a stage-2 question. `V2_ROADMAP.md:83` still says "in the order phase 16's decision 3 ruled" with no such caveat. That is minor, and it is the same claim the contract now qualifies. The rank-4 limped line and the corpus-versus-MAINT-39 question are not mentioned. Both are stage-2 material, so this is acceptable. |
| N8 | Fixed | `PHASE_21...md:37-44` and `V2_ROADMAP.md:83` give the source's reason, say the gain is unmeasured, and make the patch conditional. |
| A1 | Filed | `PHASE-19-IS-TOLD-THREE-WAYS-WHETHER-IT-FILLS-FLOP-GAPS` (`backlog.yml:3`) is `deferred`, phase `"19"`. Its quotes match `PHASE_19...md:37`, `:56-57` and `V2_ROADMAP.md:93`, and its closing condition is concrete. It is also cited from `PHASE_19...md:42-43`. |

### New findings from round 2

**R2 N1 (non-blocker).** `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT` has a closing
condition that is not the entry's own ask. The note (`backlog.yml`, end of the entry at 9334)
closes it "when where the object storage lives, who pays for it and how a machine fetches it are
ruled and recorded". The entry asks for the fresh-clone-versus-provisioned distinction "stated
wherever coverage is claimed". The storage rulings could all land while every coverage figure still
reads as the repo's. Add "and every coverage figure the campaign publishes gives both counts".

**R2 N2 (non-blocker).** The `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`
closing condition (`backlog.yml:691`) covers the refusal wording only. It drops the entry's second
half: "count lines and seats under different words". That second half is the part phase 21's own
vetting line (`PHASE_21...md`, "How many preflop lines ...") depends on.

**R2 N3 (non-blocker).** `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` was re-labelled from `"21"` back
to `"16"` (`backlog.yml:4513`). Phase 16 is completed, so this is again an entry deferred against a
completed phase, which is what `BACKLOG-DEFERRED-AGAINST-A-COMPLETED-PHASE` records as a blind spot.
Its open half is the preflop extractor, so `contract-update` or `charts` would be a truthful home.

The other adoption notes' closing conditions are concrete and match their entries:

- `GTOPEN-USES-HALF-THE-CORES-AND-NO-TIMING-RECORD-MENTIONS-IT`: five against ten threads, with
  machine and thread count on every timing.
- `EVERY-ARENA-FIGURE-IN-THE-COST-RECORD-IS-A-QUANTIZED-ARENA-AND-FULL-PRECISION-ROUGHLY-DOUBLES-IT`:
  f32 figures on the chosen box.
- `THE-MEMORY-GUARD-COMPARES-AN-ARENA-FIGURE-IT-DELIBERATELY-OVER-READS-BY-FIVE-PERCENT`: "one of
  the three repairs above". I checked that the entry does list exactly three.
- `THE-SOLVE-DRIVER-GUARD-TESTS-PIN-A-TYPE-RATHER-THAN-A-BEHAVIOUR`
- `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`
- `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`
- `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`
- `QUANTIZED-ARENAS-PUT-A-FLOOR-UNDER-EVERY-EXPLOITABILITY-THIS-PHASE-MEASURED`
- `NOTHING-MEASURES-WHETHER-THE-COMMITTED-POSTFLOP-FREQUENCIES-HAVE-SETTLED`

### What I held back in round 2

- The `QUANTIZED-ARENAS-PUT-A-FLOOR-UNDER-EVERY-EXPLOITABILITY-THIS-PHASE-MEASURED` closing
  condition ("every campaign cell records f32") is nearly free. Phase 16's own five cells already
  record `f32` (`index.json`). The entry's real point, that the 0.3% target was set against a floored
  record, is covered by the contract's stage-2 question on the target (`:63-65`), so I did not raise
  it.
- The new entry says it was "Filed ... by MAINT-40's independent review". The review found it and
  the coordinator filed it, since I am read-only. This is trivial.
- `ROADMAP.md:9`, "refuses one action later, because no decision point that follows a committed one
  is committed", is true of immediate successors, which is the packet's "eleven". `Kh7d2c`'s
  facing-a-bet cell is committed two moves below the donk cell, with an uncommitted move between
  them, so "no committed decision point is reachable" would be false. The sentence as written is
  fine.
- The `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY` closing condition also allows "or states
  why the limit it hit stopped short". That escape is honest, not vacuous, because the campaign
  report must name its limit anyway.

## Round 3

- **Checked**: `git diff 1344523~2..236df43`, plus `236df43..1344523`, read-only.
- **Checks rerun**: `check_contracts`, `check_repo_consistency`, `check_scope`, `check_file_sizes`,
  `check_execplan_delegation`, and the three generators with `--check`. All exit 0. The contract is
  138 lines.
- **Quality report**: `reports/active/latest_quality_report.txt` now reads PASS for backlog
  integrity.
- **Commit 1344523**: its edit to this file is mechanical, as described. The wording changed and
  the substance did not.

### Status

**B1: resolved.** Two places now say that naming a refusal alone closes nothing:

- `PHASE_21_FLOP_CAMPAIGN.md:55-58` says closure is "committed, or refused by name for a reason
  other than not having been committed, such as the exploitability ceiling or an off-menu size",
  and adds that phase 16's sample already refuses by name, so naming alone closes nothing.
- The `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN` adoption note says the
  same.

`V2_ROADMAP.md:83` states the stronger form, "every flop decision point that follows a committed
one". That is consistent, because the contract's allowed refusals are exceptions a roadmap summary
need not list.

**N7: fixed.** `V2_ROADMAP.md:83` now reads "ranked by the method phase 16's decision 3 ruled, with
which order to use left to the phase's own decisions", which matches `PHASE_21_FLOP_CAMPAIGN.md:49-54`.

**R2 N1: fixed.** The `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT` note now also
requires every published coverage figure to give fresh-clone and fetched-machine counts side by
side. That is the entry's own ask.

**R2 N2: fixed.** The `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT` note now
adds "every coverage figure counts lines and seats under different words".

**R2 N3: fixed.** `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` is re-filed to `charts`, a label other
entries already use. The note gives the reason: the open half is the preflop extractor, and the
rented box's premise is Linux, with phase 21's own driver ceiling as the fallback.

The `PHASE-19-IS-TOLD-THREE-WAYS-WHETHER-IT-FILLS-FLOP-GAPS` attribution now reads "Found ... by
MAINT-40's independent review and filed by the coordinator", which is accurate.

**New errors: none found.** Every hyphenated-capital token in this file is either a declared
backlog id or a task id (MAINT-35, MAINT-39, MAINT-40), which the quality report passes.

### What I held back in round 3

- `PHASE_21_FLOP_CAMPAIGN.md:58` is 127 characters and a few other lines are 101-104. No check caps
  line width and the contract's other lines wrap near 100. It is cosmetic.
- The `SOLVER-MEMORY-GUARD-IS-ABSENT-ON-MACOS` re-file note asserts the rented box "is expected to
  be Linux". That depends on the provider, which stage 2 has not ruled. The note already covers the
  other case ("if it is not, phase 21's own driver ceiling still applies"), so it is hedged, not
  pre-ruled.
- Open questions for stage 2 remain for Taylor and are not defects in this task: which order ranks
  the lines, and whether that order still uses the public corpus after MAINT-39.
