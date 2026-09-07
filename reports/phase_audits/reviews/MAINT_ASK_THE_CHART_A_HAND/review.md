# Independent review: maint-ask-the-chart-a-hand

Read-only review of `scripts/ask_preflop_chart.py` and `tests/test_ask_preflop_chart.py`, by an
agent that wrote neither. Base `9bbdcf4`, worktree `maint-31`.

Method. The script was read against `solver_artifacts/lookup.py`, `chart_query.py` and
`price_normalisation.py`, then run by hand on a pure cell, a mixed cell, a substituted price, an
uncovered spot, and eight malformed inputs. `uv run python -m pytest tests/test_ask_preflop_chart.py`
passes, 48 tests. Twelve mutations were then injected into the loaded module through a pytest plugin
outside the worktree - no file under review was edited - to find out which claims the tests actually
hold. `run_verify.py` and `check_gate_bite.py` were not run, by instruction.

## Blocker

None.

  The one rule the plan sets - it asks and prints, it never decides - holds everywhere I could
  reach. There is no default action: an uncovered spot returns `EXIT_REFUSED` with no weights at all
  (`scripts/ask_preflop_chart.py:403-419`, confirmed on the four-bet spot, which exits 1). There is
  no nearest spot, no nearest seat and no nearest depth: the script never searches for a cell, it
  hands one `ChartQuery` to `library.lookup` and renders whatever comes back
  (`scripts/ask_preflop_chart.py:512-522`). No price is invented or rounded here - `parse_size_bb`
  rejects anything that is not a number and passes the rest to `PreflopAction` unchanged, so
  `2.505`, `-2.5`, `nan` and `inf` all come back as bad input rather than as a nearby cell
  (`scripts/ask_preflop_chart.py:156-172`, checked by running each). No tie is broken: the headline
  is `hit.best_action` and nothing else, which is `lookup`'s own one-positive-action rule
  (`scripts/ask_preflop_chart.py:390-399` against `lookup.py:147-157`).

  A refusal keeps its cause. `refusal_lines` prints `miss.code`, the plain-English line, and
  `miss.detail`, and the plain line is additional rather than a replacement
  (`scripts/ask_preflop_chart.py:403-419`). Probed: replacing the code with the friendly wording
  alone turns 8 tests red, so the code is genuinely pinned rather than incidentally present. A code
  `PLAIN_ENGLISH` has not been taught prints a placeholder that says it is a placeholder rather than
  a guess (`scripts/ask_preflop_chart.py:406-410`), and
  `test_every_reason_code_has_a_plain_english_line` fails when `lookup` grows a seventh code.

  A substituted answer cannot be mistaken for an exact one. The substitution block is printed above
  the weights, on hits and on misses alike, and carries the asked price, the answered price, and the
  `price_substitution_N` spelling the audit reports use (`scripts/ask_preflop_chart.py:324-362`,
  `432-448`). `answer_lines` additionally prints `answered at <key>` whenever the answering key is
  not the asked key (`scripts/ask_preflop_chart.py:376-377`). Probed three ways: deleting the block
  entirely, and reducing it to its header alone, each turn
  `test_a_price_substitution_is_visible` and `test_a_refusal_also_carries_its_substitution` red.
  Run by hand, `--facing "CO raise 2.3"` shouts the 2.3 to 2.5 move and `--facing "CO raise 100"`
  shouts a 100 to 2.5 one, so ruling 8's deliberate absence of a distance bound is visible rather
  than silent.

  A mixed class keeps its whole distribution. `22` in `t6/d100/HJ/HJ:raise@2.5,BB:raise@7.5` prints
  0.5003 call and 0.4997 raise with no headline and the word `Mixed`
  (`scripts/ask_preflop_chart.py:389-399`, run by hand). Probed: picking the heavier action there
  turns `test_a_mixed_class_prints_its_whole_distribution_and_no_headline` red.

  The weights are the artifact's own. They are read straight off `hit.action_weights`, in the
  artifact's order, with no sort, no filter and no renormalisation
  (`scripts/ask_preflop_chart.py:381-388`). Probed: sorting heaviest-first, rounding to two places,
  and dropping the zero-weight actions each turn tests red. The percentage beside each weight is
  rounded to two places but the raw weight is printed next to it, and `schema.py:213` holds every
  cell to summing to 1.0 within tolerance, so the percentage is a display of the number rather than
  a second one.

  Nothing is mocked. The tests read `data/artifacts/preflop/six_max_100bb_rakefree.json` directly
  and compare printed numbers with committed ones (`tests/test_ask_preflop_chart.py:122-135`), and
  the only synthetic artifacts are the two written to `tmp_path` for the ambiguous-depth case
  (`tests/test_ask_preflop_chart.py:340-359`). No core poker state, strategy legality or replay is
  mocked, so the testing ladder is respected. Style matches the surrounding scripts: `ruff check`
  passes on both files, and the docstring density is the repo's own house style. `ruff format
  --check` would reformat both, but it would also reformat 80 other files and is not a gate command,
  so that is not a finding against this lane.

## Non-blocker

- A recommendation added *beside* the mixed distribution would pass the whole suite. The mixed-cell
  test asserts `"Mixed" in out` and `"One action carries weight" not in out`
  (`tests/test_ask_preflop_chart.py:195-196`), which pins the two strings the current code prints
  but not the property they stand for. I appended `"  If you must pick one: call."` to
  `answer_lines` for a mixed hit and all 48 tests still passed. The code today does not do this;
  what is missing is the assertion that stops it arriving later, and this is exactly the defect the
  plan names, so the gap matters more than usual. The property to state is that a mixed answer names
  no action outside the weight table - the printed body after the table mentions no action name at
  all.

- Nothing tests the table-size half of the never-pick-a-default rule. `default_table_size` refuses
  when the loaded charts cover two sizes (`scripts/ask_preflop_chart.py:259-271`), and the depth
  twin of that rule is tested (`tests/test_ask_preflop_chart.py:340-359`), but the size one is not.
  I replaced `default_table_size` with one that silently takes the smallest size and all 48 tests
  passed. Only one table size is committed today, so nothing is wrong now; the branch that will
  matter the day a second chart lands is unheld.

- The one sentence in the file that the artifacts cannot say. The module docstring claims "Nothing
  here is hand-typed that the loaded artifacts could say instead"
  (`scripts/ask_preflop_chart.py:30`), and `scope_lines` then states the bot's postflop behaviour as
  a hardcoded string: "After the flop this repo still checks and folds"
  (`scripts/ask_preflop_chart.py:425-427`). That is true at this base commit and false the day phase
  16, `Postflop That Can Bet`, lands - it is `future` in `phase_status.yml:87`. Worse,
  `test_every_run_says_it_covers_preflop_only` asserts the string is printed
  (`tests/test_ask_preflop_chart.py:388-389`), so when the claim goes false the test pins it in
  place rather than catching it, and a reader is told the bot checks and folds by a command that
  cannot know. The scope note only needs to say what this command asks - the committed preflop
  chart, and nothing else - without also asserting what happens after the flop.

- `tests/test_ask_preflop_chart.py:38` imports `make_artifact` from `test_preflop_lookup`, which is
  frozen (`verification/freeze.lock:83`). Reusing it beats a fourth copy, but it points an unfrozen
  file at a frozen one, so a later frozen-test correction to that helper's signature breaks this
  file with no signal until the gate runs. Worth a sentence in the plan saying the dependency is
  deliberate.

- A reader who runs `pytest tests/test_ask_preflop_chart.py` rather than `python -m pytest` gets
  `ModuleNotFoundError: No module named 'scripts'`, because `scripts` is importable only through the
  working directory that `python -m` adds. The gate is unaffected - the `pytest` command id is
  `python -m pytest tests` (`scripts/run_verify.py:138-140`) - and 16 existing test files share the
  pattern, so this is pre-existing and not this lane's to fix. The plan's Gate sentence, "including
  bare `pytest`", reads as the invocation rather than as the command id and is worth rewording.

## Alignment

- `HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES` (deferred, phase 14). That entry is about
  counts typed into committed documents; the postflop sentence above is the same failure with a
  behaviour claim instead of a number, and it is now in a script rather than in prose, with a test
  holding it in place. If the entry is taken up, the sweep it describes should cover load-bearing
  claims about what the bot does, not only figures - the third non-blocker is a live instance.

- `SOLVED-PRICE-FIXTURE-HELPER-DUPLICATED-ACROSS-TEST-FILES` (deferred, phase v2). This lane is the
  first file to reuse a frozen test's helper rather than copy it, which is the direction that entry
  wants, and it also shows why the shared helpers need a home outside `tests/test_*.py`: the reuse
  currently works by importing a frozen module by name. Worth recording as evidence on the entry.

- Proposed new id `A-CONVENIENCE-COMMAND-HAS-NO-GATE-COMMAND-BEHIND-IT`. This script is a front door
  onto the committed ranges and its correctness now rests entirely on the base `pytest` run. It
  generates no report, so `run_verify.py` never executes it end to end, and the one test that runs
  it as a person runs it checks exit codes only (`tests/test_ask_preflop_chart.py:401-413`). That is
  adequate for a command this small and is not a finding against the lane; it is the kind of thing
  that should be decided deliberately rather than by default if more such commands arrive.
