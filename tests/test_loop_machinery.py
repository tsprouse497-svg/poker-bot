from __future__ import annotations

import inspect

import yaml

import scripts.check_contracts as check_contracts
import scripts.check_gate_bite as check_gate_bite
import scripts.check_repo_consistency as consistency
import scripts.check_scope as check_scope
import scripts.freeze_tests as freeze_tests
import scripts.loop_stage as loop_stage
import scripts.run_verify as run_verify
from scripts.repo_paths import REPO_ROOT

# --------------------------------------------------------------------------- #
# test freeze
# --------------------------------------------------------------------------- #


def test_counts_module_and_class_test_functions(tmp_path) -> None:
    path = tmp_path / "test_sample.py"
    path.write_text(
        "def test_one():\n    pass\n\n"
        "def helper():\n    pass\n\n"
        "class TestGroup:\n"
        "    def test_two(self):\n        pass\n"
        "    def not_a_test(self):\n        pass\n",
        encoding="utf-8",
    )

    assert freeze_tests.test_function_count(path) == 2


def test_freeze_compare_flags_a_changed_file() -> None:
    lock = {
        "schema_version": 1,
        "test_function_floor": 1,
        "files": {"tests/test_a.py": {"sha256": "old", "test_functions": 1}},
    }
    state = {
        "schema_version": 1,
        "test_function_floor": 1,
        "files": {"tests/test_a.py": {"sha256": "new", "test_functions": 1}},
    }

    errors = freeze_tests.compare(lock, state)

    assert any("changed" in error for error in errors)


def test_freeze_compare_flags_a_test_file_the_lock_never_saw() -> None:
    lock = {"schema_version": 1, "test_function_floor": 0, "files": {}}
    state = {
        "schema_version": 1,
        "test_function_floor": 1,
        "files": {"tests/test_new.py": {"sha256": "x", "test_functions": 1}},
    }

    errors = freeze_tests.compare(lock, state)

    assert any("not in the freeze lock" in error for error in errors)


def test_freeze_compare_flags_a_falling_test_count() -> None:
    lock = {"schema_version": 1, "test_function_floor": 10, "files": {}}
    state = {"schema_version": 1, "test_function_floor": 9, "files": {}}

    errors = freeze_tests.compare(lock, state)

    assert any("fell from the frozen floor" in error for error in errors)


def test_freeze_compare_accepts_an_untouched_suite() -> None:
    state = freeze_tests.current_state()
    lock = yaml.safe_load(freeze_tests.render(state))

    assert freeze_tests.compare(lock, state) == []


# --------------------------------------------------------------------------- #
# gate-bite mutations
# --------------------------------------------------------------------------- #


def test_every_mutation_applies_exactly_once_to_its_file() -> None:
    for mutation in check_gate_bite.load_mutations():
        target = REPO_ROOT / mutation["file"]

        assert target.exists(), mutation["id"]
        assert target.read_text(encoding="utf-8").count(mutation["find"]) == 1, mutation["id"]


def test_every_mutation_names_registered_commands() -> None:
    for mutation in check_gate_bite.load_mutations():
        for command_id in mutation["must_fail"]:
            assert command_id in run_verify.COMMANDS, mutation["id"]


def test_every_mutation_actually_changes_the_source() -> None:
    for mutation in check_gate_bite.load_mutations():
        assert mutation["find"] != mutation["replace"], mutation["id"]


def test_purge_bytecode_drops_only_the_matching_cache(tmp_path) -> None:
    """A same-length mutation leaves mtime and size unchanged, so cached bytecode
    stays 'valid' and keeps running the mutated code after the source is restored.
    Purging the cache is what makes the restore real."""
    source = tmp_path / "thing.py"
    source.write_text("x = 1\n", encoding="utf-8")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    mine = cache / "thing.cpython-313.pyc"
    other = cache / "elsewhere.cpython-313.pyc"
    mine.write_bytes(b"stale")
    other.write_bytes(b"keep")

    check_gate_bite.purge_bytecode(source)

    assert not mine.exists()
    assert other.exists()


def test_purge_bytecode_tolerates_a_missing_cache(tmp_path) -> None:
    source = tmp_path / "thing.py"
    source.write_text("x = 1\n", encoding="utf-8")

    check_gate_bite.purge_bytecode(source)


# --------------------------------------------------------------------------- #
# scope hardening
# --------------------------------------------------------------------------- #


def test_overbroad_patterns_are_rejected() -> None:
    assert check_scope.is_overbroad("*")
    assert check_scope.is_overbroad("**")
    assert check_scope.is_overbroad("*.py")
    assert not check_scope.is_overbroad("src/**")
    assert not check_scope.is_overbroad("docs/phase_contracts/*.md")
    assert not check_scope.is_overbroad("AGENTS.md")


def test_widening_approved_scope_is_a_relaxation() -> None:
    base = {"approved_scope": ["a.py"], "forbidden_scope": ["secrets/**"]}

    notes = check_scope.relaxations(base, ["a.py", "b.py"], ["secrets/**"])

    assert len(notes) == 1
    assert "b.py" in notes[0]


def test_shrinking_forbidden_scope_is_a_relaxation() -> None:
    base = {"approved_scope": [], "forbidden_scope": ["secrets/**"]}

    notes = check_scope.relaxations(base, [], [])

    assert len(notes) == 1
    assert "secrets/**" in notes[0]


def test_narrowing_approved_scope_is_not_a_relaxation() -> None:
    base = {"approved_scope": ["a.py", "b.py"], "forbidden_scope": []}

    assert check_scope.relaxations(base, ["a.py"], []) == []


def test_log_entries_are_compared_by_date_and_reason() -> None:
    task = {"scope_change_log": [{"date": "2026-01-01", "reason": "because"}]}

    assert check_scope.log_entries(task) == {("2026-01-01", "because")}


def test_the_live_task_file_passes_its_own_scope_rules() -> None:
    task = yaml.safe_load((REPO_ROOT / "CURRENT_TASK.yml").read_text(encoding="utf-8"))
    patterns = (task.get("approved_scope") or []) + (task.get("standing_scope") or [])

    assert [p for p in patterns if check_scope.is_overbroad(p)] == []


# --------------------------------------------------------------------------- #
# repo consistency
# --------------------------------------------------------------------------- #


def _plan_dirs(monkeypatch, tmp_path):
    active = tmp_path / "active"
    completed = tmp_path / "completed"
    active.mkdir()
    completed.mkdir()
    monkeypatch.setattr(consistency, "ACTIVE_PLANS", active)
    monkeypatch.setattr(consistency, "COMPLETED_PLANS", completed)
    return active, completed


def test_completed_phase_needs_its_plan_filed_as_completed(monkeypatch, tmp_path) -> None:
    _plan_dirs(monkeypatch, tmp_path)
    errors: list[str] = []

    consistency.check_plan_location(
        {"phase_id": "01", "status": "completed", "contract": "docs/phase_contracts/PHASE_01.md"},
        errors,
    )

    assert any("not in completed/" in error for error in errors)


def test_future_phase_may_not_have_a_completed_plan(monkeypatch, tmp_path) -> None:
    _, completed = _plan_dirs(monkeypatch, tmp_path)
    (completed / "PHASE_07.md").write_text("x\n", encoding="utf-8")
    errors: list[str] = []

    consistency.check_plan_location(
        {"phase_id": "07", "status": "future", "contract": "docs/phase_contracts/PHASE_07.md"},
        errors,
    )

    assert any("filed as completed" in error for error in errors)


def test_future_phase_with_an_active_plan_is_fine(monkeypatch, tmp_path) -> None:
    active, _ = _plan_dirs(monkeypatch, tmp_path)
    (active / "PHASE_05.md").write_text("x\n", encoding="utf-8")
    errors: list[str] = []

    consistency.check_plan_location(
        {"phase_id": "05", "status": "future", "contract": "docs/phase_contracts/PHASE_05.md"},
        errors,
    )

    assert errors == []


def test_pytest_gate_commands_all_hold_tests() -> None:
    errors: list[str] = []

    consistency.check_pytest_commands_hold_tests(errors)

    assert errors == []


# --------------------------------------------------------------------------- #
# loop driver
# --------------------------------------------------------------------------- #

DECISIONS_SAMPLE = """# Phase 99 judgment calls

## 1. A frozen choice

Reversibility: frozen-into-data

Options: a | b
Answer: [ ]

## 2. A reversible choice

Reversibility: runtime-reversible

Options: a | b
Answer: [a]
"""


def test_decision_items_read_class_and_answer() -> None:
    items = loop_stage.decision_items(DECISIONS_SAMPLE)

    assert len(items) == 2
    assert items[0][1] == "frozen-into-data"
    assert items[1][2] == "[a]"


def test_only_unanswered_frozen_decisions_block() -> None:
    blocking = loop_stage.unanswered_frozen(DECISIONS_SAMPLE)

    assert len(blocking) == 1
    assert blocking[0].startswith("1.")


def test_answered_frozen_decisions_do_not_block() -> None:
    answered = DECISIONS_SAMPLE.replace("Answer: [ ]", "Answer: [a]")

    assert loop_stage.unanswered_frozen(answered) == []


def test_stage_numbers_are_contiguous_and_ordered() -> None:
    numbers = [stage.number for stage in loop_stage.STAGES]

    assert numbers == list(range(len(numbers)))


def test_every_stage_has_a_runner_and_an_instruction() -> None:
    for stage in loop_stage.STAGES:
        assert stage.who in {"script", "model", "human"}, stage.name
        assert stage.instruction.strip(), stage.name


def test_policy_covers_every_incomplete_phase() -> None:
    """Every phase the loop could still run must declare whether it may auto-advance.

    A completed phase may stay in the policy. Its entry is the record of why it could
    not advance unattended, which is worth more than a tidy file.
    """
    phase_status = yaml.safe_load((REPO_ROOT / "phase_status.yml").read_text(encoding="utf-8"))
    policy = yaml.safe_load(loop_stage.POLICY_PATH.read_text(encoding="utf-8"))["phases"]
    incomplete = {
        str(phase["phase_id"]) for phase in phase_status["phases"] if phase["status"] != "completed"
    }
    known = {str(phase["phase_id"]) for phase in phase_status["phases"]}

    assert incomplete <= set(policy)
    assert set(policy) <= known


def test_policy_entries_declare_a_reason() -> None:
    policy = yaml.safe_load(loop_stage.POLICY_PATH.read_text(encoding="utf-8"))["phases"]

    for phase_id, entry in policy.items():
        assert isinstance(entry.get("auto_advance"), bool), phase_id
        assert isinstance(entry.get("needs_human_data"), bool), phase_id
        assert entry.get("reason", "").strip(), phase_id


def test_phases_that_need_human_data_never_auto_advance() -> None:
    policy = yaml.safe_load(loop_stage.POLICY_PATH.read_text(encoding="utf-8"))["phases"]

    for phase_id, entry in policy.items():
        if entry["needs_human_data"]:
            assert entry["auto_advance"] is False, phase_id


def test_an_assertion_failure_is_a_legitimate_stage_four_red() -> None:
    assert loop_stage.red_for_the_right_reason("E       AssertionError: nope")


def test_a_missing_implementation_module_is_a_legitimate_stage_four_red() -> None:
    """Tests are authored before any implementation, so this import must fail."""
    output = "ModuleNotFoundError: No module named 'poker_training_bot.strategy.preflop_chart'"

    assert loop_stage.red_for_the_right_reason(output)


def test_a_broken_test_file_is_not_a_legitimate_red() -> None:
    assert not loop_stage.red_for_the_right_reason("SyntaxError: invalid syntax")
    assert not loop_stage.red_for_the_right_reason("ModuleNotFoundError: No module named 'reqests'")


def test_the_stage_four_check_reads_the_whole_output_not_its_tail() -> None:
    """MAINT-24: a tail window holds no assertion when the run ends in a FAILED list.

    Phase 12's stage-4 suite produced 57,328 characters with 38 occurrences of `assert`
    and none in the final 4,000, so a clipped output read an assertion-red file as a
    broken one. `check_tests_authored` therefore opts out of the clip, and the clip
    stays the default for every caller that prints a reason to a human instead.
    """
    full = "E       AssertionError: nope\n" + "FAILED tests/test_x.py::test_one\n" * 400

    assert "assert" not in full[-4000:].lower()
    assert loop_stage.red_for_the_right_reason(full)
    assert inspect.signature(loop_stage.run_command).parameters["clip"].default == 4000
    assert "clip=None" in inspect.getsource(loop_stage.check_tests_authored)


def test_resume_returns_a_halted_loop_to_its_stage() -> None:
    """A halt must be recoverable; --start rewinds and re-runs finished stages."""
    halted = {"loop": "halted", "phase_id": "05", "stage": 4, "halt_reason": "blocked"}

    state = loop_stage.resumed(halted)

    assert state["loop"] == "running"
    assert state["stage"] == 4
    assert "halt_reason" not in state


def test_resume_refuses_a_loop_that_is_not_halted() -> None:
    import pytest

    with pytest.raises(ValueError, match="not halted"):
        loop_stage.resumed({"loop": "running", "stage": 4})


# --------------------------------------------------------------------------- #
# per-stage review
# --------------------------------------------------------------------------- #


def context_for_stage(state: dict) -> loop_stage.Context:
    return loop_stage.Context(state=state, task={"task_mode": "implementation"}, phase_id="09")


def test_reviewable_paths_drops_generated_and_bookkeeping_files() -> None:
    """A stage whose whole diff is machine output has nothing for a human to read.

    The driver's own pointer moves on every advance, so counting it would demand a
    review of every stage and put us back where a fixed list of stages started.
    """
    paths = [
        "verification/loop_state.yml",
        "verification/freeze.lock",
        "CURRENT_TASK.yml",
        "phase_status.yml",
        "reports/active/verify_results.json",
        "reports/phase_audits/reviews/PHASE_09_QUALITY_HARDENING/stage-08-review.md",
        "STATUS.md",
        "docs/PHASE_LEDGER.md",
        "docs/BACKLOG.md",
    ]

    assert loop_stage.reviewable_paths(paths) == []


def test_generated_documents_are_named_by_their_generators() -> None:
    """The exclusion list has to track the generators rather than a memory of them.

    Every document a gate command regenerates is machine output, and a stage that
    regenerates one has not asked a human to decide anything.
    """
    generated = {
        "STATUS.md": "generate_status",
        "docs/PHASE_LEDGER.md": "generate_phase_ledger",
        "docs/BACKLOG.md": "generate_backlog",
    }
    for path, command_id in generated.items():
        assert command_id in run_verify.COMMANDS, command_id
        assert path in loop_stage.UNREVIEWED_PATHS, path


def test_reviewable_paths_keeps_hand_written_work() -> None:
    paths = [
        "verification/loop_state.yml",
        "src/poker_training_bot/strategy/preflop_chart.py",
        "tests/test_full_table_preflop.py",
        "verification/mutations.yml",
        "docs/phase_contracts/PHASE_09_QUALITY_HARDENING.md",
    ]

    assert loop_stage.reviewable_paths(paths) == paths[1:]


def test_unresolved_blockers_reads_only_the_blocker_section() -> None:
    text = (
        "## Blocker\n\n- the freeze hides a weak assertion\n\n"
        "## Non-blocker\n\n- naming nit\n\n## Alignment\n\n- LOOP-DRIFT-1\n"
    )

    assert loop_stage.unresolved_blockers(text) == ["the freeze hides a weak assertion"]


def test_a_resolved_blocker_releases_the_stage() -> None:
    """The finding stays in the note; deleting it would lose what the reviewer caught."""
    text = (
        "## Blocker\n\n- [resolved] the freeze hid a weak assertion\n\n"
        "## Non-blocker\n\nNone.\n\n## Alignment\n\nNone.\n"
    )

    assert loop_stage.unresolved_blockers(text) == []


def test_validate_review_requires_all_three_sections(tmp_path) -> None:
    path = tmp_path / "stage-06-build.md"
    path.write_text("## Blocker\n\nNone.\n\n## Non-blocker\n\nNone.\n", encoding="utf-8")

    reasons = loop_stage.validate_review(path)

    assert len(reasons) == 1
    assert "## Alignment" in reasons[0]


def test_validate_review_accepts_a_complete_note(tmp_path) -> None:
    path = tmp_path / "stage-06-build.md"
    path.write_text(
        "## Blocker\n\nNone.\n\n## Non-blocker\n\n- altitude\n\n## Alignment\n\nNone.\n",
        encoding="utf-8",
    )

    assert loop_stage.validate_review(path) == []


def test_a_stage_with_no_reviewable_diff_owes_no_review(monkeypatch) -> None:
    monkeypatch.setattr(
        loop_stage, "changed_paths", lambda base: ["verification/loop_state.yml"]
    )

    reasons = loop_stage.check_stage_review(
        context_for_stage({"stage_base": "abc123"}), loop_stage.stage_by_number(5)
    )

    assert reasons == []


def test_a_stage_that_touched_source_must_write_a_review(monkeypatch) -> None:
    monkeypatch.setattr(
        loop_stage,
        "changed_paths",
        lambda base: ["src/poker_training_bot/strategy/preflop_chart.py"],
    )

    reasons = loop_stage.check_stage_review(
        context_for_stage({"stage_base": "abc123"}), loop_stage.stage_by_number(6)
    )

    assert len(reasons) == 1
    assert "preflop_chart.py" in reasons[0]
    assert "stage-06-build.md" in reasons[0]


def test_an_existing_review_is_still_checked_for_shape(monkeypatch, tmp_path) -> None:
    """Writing a file is not the bar; an open blocker holds the stage."""
    note = tmp_path / "stage-06-build.md"
    note.write_text(
        "## Blocker\n\n- the implementation only satisfies the test\n\n"
        "## Non-blocker\n\nNone.\n\n## Alignment\n\nNone.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(loop_stage, "changed_paths", lambda base: ["src/anything.py"])
    monkeypatch.setattr(loop_stage, "review_path", lambda ctx, stage: note)

    reasons = loop_stage.check_stage_review(
        context_for_stage({"stage_base": "abc123"}), loop_stage.stage_by_number(6)
    )

    assert reasons == ["unresolved blocker in stage-06-build.md: the implementation"
                       " only satisfies the test"]


def test_stage_eight_is_exempt_from_the_diff_trigger(monkeypatch) -> None:
    """Its own output is excluded, so the trigger would always answer no.

    check_review requires stage 8's notes whatever the diff says, which is the
    stronger rule, and asking twice would only produce a second confusing reason.
    """
    monkeypatch.setattr(loop_stage, "changed_paths", lambda base: ["src/anything.py"])

    reasons = loop_stage.check_stage_review(
        context_for_stage({"stage_base": "abc123"}), loop_stage.stage_by_number(8)
    )

    assert reasons == []


def test_stage_base_falls_back_to_the_branch_point(monkeypatch) -> None:
    """A loop started before this rule existed must not skip its reviews.

    The branch point makes the diff the whole phase so far: wider than one stage,
    never narrower, which is the safe direction to be wrong in.
    """
    monkeypatch.setattr(loop_stage, "git", lambda *args: "branchpoint")

    assert loop_stage.stage_base({}) == "branchpoint"
    assert loop_stage.stage_base({"stage_base": "recorded"}) == "recorded"


def test_a_lost_branch_point_widens_rather_than_narrows(monkeypatch) -> None:
    """Falling back to HEAD would quietly drop every committed change from the diff.

    A review rule that goes quiet when it cannot find its bearings is the exact
    failure it exists to stop, so the empty tree is the fallback and everything
    tracked counts as changed.
    """
    monkeypatch.setattr(loop_stage, "git", lambda *args: "")

    assert loop_stage.stage_base({}) == loop_stage.EMPTY_TREE


def test_review_path_is_named_for_its_phase_and_stage() -> None:
    path = loop_stage.review_path(
        context_for_stage({}), loop_stage.stage_by_number(4)
    )

    assert path.parent.name == "PHASE_09_QUALITY_HARDENING"
    assert path.name == "stage-04-tests.md"


def test_every_stage_declares_what_its_reviewer_should_ask() -> None:
    for stage in loop_stage.STAGES:
        assert stage.review_focus.strip(), stage.name


def test_the_brief_goes_quiet_once_the_review_is_written(monkeypatch, tmp_path) -> None:
    """A brief that keeps asking for work already done teaches the reader to skip it."""
    note = tmp_path / "stage-06-build.md"
    note.write_text(
        "## Blocker\n\nNone.\n\n## Non-blocker\n\nNone.\n\n## Alignment\n\nNone.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(loop_stage, "changed_paths", lambda base: ["src/anything.py"])
    ctx = context_for_stage({"stage_base": "abc123"})
    stage = loop_stage.stage_by_number(6)

    absent = loop_stage.REVIEWS_ROOT / "PHASE_99_NOT_A_PHASE" / "stage-06-build.md"
    monkeypatch.setattr(loop_stage, "review_path", lambda c, s: absent)
    assert loop_stage.review_brief(ctx, stage)

    monkeypatch.setattr(loop_stage, "review_path", lambda c, s: note)
    assert loop_stage.review_brief(ctx, stage) == []


# --------------------------------------------------------------------------- #
# declared phases and their contracts
# --------------------------------------------------------------------------- #


def declared_phases() -> list[dict]:
    text = (REPO_ROOT / "phase_status.yml").read_text(encoding="utf-8")
    return yaml.safe_load(text)["phases"]


def test_contracts_and_declarations_are_the_same_set() -> None:
    """Neither side may grow without the other.

    A contract nobody declares is a phase nothing runs, and a declaration with no
    contract is a phase the loop cannot start. The check that enforces this used to
    hardcode ten contracts and the id set 00-09, which meant adopting v2 required
    editing the checker; it now derives both from phase_status.yml.
    """
    declared = {str(phase["phase_id"]) for phase in declared_phases()}
    contracts = {
        path.name.split("_")[1]
        for path in (REPO_ROOT / "docs" / "phase_contracts").glob("PHASE_*.md")
    }

    assert declared == contracts


def test_a_contract_nobody_declares_is_an_error() -> None:
    errors = check_contracts.contract_id_errors({"09", "10"}, {"09"})

    assert len(errors) == 1
    assert "10" in errors[0]


def test_a_declared_phase_with_no_contract_is_an_error() -> None:
    errors = check_contracts.contract_id_errors({"09"}, {"09", "10"})

    assert len(errors) == 1
    assert "no contract" in errors[0]


def test_matching_sides_pass() -> None:
    assert check_contracts.contract_id_errors({"09", "10"}, {"09", "10"}) == []


def test_every_declared_phase_names_files_where_this_repo_keeps_them() -> None:
    for phase in declared_phases():
        phase_id = str(phase["phase_id"])
        contract = REPO_ROOT / str(phase["contract"])
        packet = str(phase["audit_packet"])

        assert contract.is_file(), phase_id
        assert packet.startswith("reports/phase_audits/"), phase_id
        assert contract.stem in packet, phase_id


# --------------------------------------------------------------------------- #
# the mutation sentinel
# --------------------------------------------------------------------------- #


def test_a_live_mutation_fails_the_scope_check(monkeypatch, tmp_path) -> None:
    """While a mutation is applied, the tree holds a deliberate defect.

    The sentinel used to protect only the next mutation run. The window it left
    unguarded is the one that matters: a commit taken during a run captures the
    planted bug, which is how a swapped-label defect reached the Phase 09 branch.
    """
    monkeypatch.setattr(check_scope, "REPO_ROOT", tmp_path)
    sentinel = tmp_path / check_scope.MUTATION_SENTINEL
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("mutating src/thing.py for label-swap\n", encoding="utf-8")

    errors = check_scope.mutation_sentinel_errors()

    assert len(errors) == 1
    assert "src/thing.py" in errors[0]


def test_a_clean_tree_passes_the_sentinel_check(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(check_scope, "REPO_ROOT", tmp_path)

    assert check_scope.mutation_sentinel_errors() == []


def test_the_sentinel_can_never_be_committed() -> None:
    """Gitignored, so `git add -A` during a mutation run cannot stage it.

    Ignoring it also hides it from the scope diff that caught it by accident, which
    is why mutation_sentinel_errors asserts the tree's state directly.
    """
    ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert check_scope.MUTATION_SENTINEL in [line.strip() for line in ignored]


def test_the_two_sides_name_the_same_sentinel() -> None:
    """The writer and the check must agree, or the guard watches nothing."""
    written = check_gate_bite.SENTINEL_PATH.relative_to(REPO_ROOT)

    assert str(written) == check_scope.MUTATION_SENTINEL
