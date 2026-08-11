from __future__ import annotations

import yaml

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
    phase_status = yaml.safe_load((REPO_ROOT / "phase_status.yml").read_text(encoding="utf-8"))
    policy = yaml.safe_load(loop_stage.POLICY_PATH.read_text(encoding="utf-8"))["phases"]
    incomplete = [
        str(phase["phase_id"]) for phase in phase_status["phases"] if phase["status"] != "completed"
    ]

    assert sorted(policy) == sorted(incomplete)


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
