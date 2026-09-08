"""The mutation sweep's own machinery: what it proves, and what it costs to prove it.

`check_gate_bite` is the only thing in this repo that shows a test would notice a real
defect, and until 2026-09-08 it paid for that twice over: every command a mutation named
ran once with the bug in and once on the restored tree. These tests hold the cheaper
shape in place - a restore proved by comparing the bytes the sweep already held, and one
health pass at the end over the union of everything it ran.

They live apart from `test_loop_machinery.py` only because that file is at its size cap.
"""

from __future__ import annotations

import scripts.check_gate_bite as check_gate_bite
import scripts.run_verify as run_verify

# --------------------------------------------------------------------------- #
# the sweep's restore and its one health run
# --------------------------------------------------------------------------- #


def test_a_restore_that_comes_back_different_is_caught(tmp_path) -> None:
    """The sweep used to infer a good restore from a passing test run.

    That is both expensive and weak: a file whose comments or blank lines came
    back wrong still passes every test. Comparing the bytes it held before is
    exact, instant, and the only thing that notices a half-written file.
    """
    target = tmp_path / "thing.py"
    target.write_text("value = 2\n", encoding="utf-8")
    mutation = {"id": "value-swap", "file": "src/thing.py"}

    errors = check_gate_bite.restore_errors(mutation, target, "value = 1\n")

    assert len(errors) == 1
    assert "value-swap" in errors[0]
    assert "src/thing.py" in errors[0]


def test_a_faithful_restore_reports_nothing(tmp_path) -> None:
    target = tmp_path / "thing.py"
    target.write_text("value = 1\n", encoding="utf-8")

    mutation = {"id": "x", "file": "src/thing.py"}

    assert check_gate_bite.restore_errors(mutation, target, "value = 1\n") == []


def test_a_file_that_cannot_be_read_back_is_a_restore_failure(tmp_path) -> None:
    """A restore that left nothing behind is the worst case, not an exception."""
    missing = tmp_path / "gone.py"
    mutation = {"id": "x", "file": "src/gone.py"}

    errors = check_gate_bite.restore_errors(mutation, missing, "value = 1\n")

    assert len(errors) == 1
    assert "src/gone.py" in errors[0]


def test_the_health_run_covers_every_command_any_mutation_named() -> None:
    """Not one mutation's slice of them, and each one only once.

    The union is what makes a single pass stronger than the per-mutation re-run it
    replaces: it also runs commands the mutation at hand never named.
    """
    mutations = [
        {"id": "a", "must_fail": ["pytest", "check_contracts"]},
        {"id": "b", "must_fail": ["check_contracts"]},
        {"id": "c", "must_fail": ["ruff_check", "pytest"]},
    ]

    assert check_gate_bite.health_command_ids(mutations) == [
        "check_contracts",
        "pytest",
        "ruff_check",
    ]


def test_the_health_run_tolerates_a_mutation_that_names_no_commands() -> None:
    assert check_gate_bite.health_command_ids([{"id": "a"}, {"id": "b", "must_fail": []}]) == []


def test_every_command_the_health_run_will_use_is_registered() -> None:
    """The health run skips an id it cannot look up, because COMMANDS[unknown]
    would raise instead of printing the errors the sweep collected. Nothing in the
    committed set is such an id, so the skip never hides anything today."""
    for command_id in check_gate_bite.health_command_ids(check_gate_bite.load_mutations()):
        assert command_id in run_verify.COMMANDS, command_id


def test_a_mutation_is_run_once_and_leaves_the_file_and_sentinel_as_it_found_them(
    monkeypatch, tmp_path
) -> None:
    """The whole per-mutation path against a fake tree and a fake command.

    `len(during) == 1` is the saving: the old sweep ran each command a second time
    on the restored tree, and ninety of those runs were the whole test suite.
    """
    target = tmp_path / "src" / "thing.py"
    target.parent.mkdir(parents=True)
    target.write_text("value = 1\n", encoding="utf-8")
    sentinel = tmp_path / "verification" / ".mutation_in_progress"
    sentinel.parent.mkdir(parents=True)
    during: list[tuple[str, str, str]] = []

    def fake_run(command_id: str) -> bool:
        during.append(
            (command_id, target.read_text(encoding="utf-8"), sentinel.read_text(encoding="utf-8"))
        )
        return False

    monkeypatch.setattr(check_gate_bite, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(check_gate_bite, "SENTINEL_PATH", sentinel)
    monkeypatch.setattr(check_gate_bite, "COMMANDS", {"fake_command": object()})
    monkeypatch.setattr(check_gate_bite, "run_registered", fake_run)

    errors = check_gate_bite.check_mutation(
        {
            "id": "value-swap",
            "file": "src/thing.py",
            "find": "value = 1",
            "replace": "value = 2",
            "must_fail": ["fake_command"],
        }
    )

    assert errors == []
    assert len(during) == 1
    assert during[0][0] == "fake_command"
    assert during[0][1] == "value = 2\n"
    assert target.read_text(encoding="utf-8") == "value = 1\n"
    assert not sentinel.exists()


def test_the_recovery_advice_swaps_the_strings_back_instead_of_reaching_for_git(
    monkeypatch, tmp_path
) -> None:
    """`git checkout` on the mutated file destroys uncommitted work in it, and in a
    lane worktree that is the work the sweep was called to certify. Every message
    that mentions recovery has to name the swap and warn off the checkout."""
    target = tmp_path / "src" / "thing.py"
    target.parent.mkdir(parents=True)
    target.write_text("value = 1\n", encoding="utf-8")
    sentinel = tmp_path / "verification" / ".mutation_in_progress"
    sentinel.parent.mkdir(parents=True)
    written: list[str] = []

    def fake_run(command_id: str) -> bool:
        written.append(sentinel.read_text(encoding="utf-8"))
        return False

    monkeypatch.setattr(check_gate_bite, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(check_gate_bite, "SENTINEL_PATH", sentinel)
    monkeypatch.setattr(check_gate_bite, "COMMANDS", {"fake_command": object()})
    monkeypatch.setattr(check_gate_bite, "run_registered", fake_run)
    check_gate_bite.check_mutation(
        {
            "id": "value-swap",
            "file": "src/thing.py",
            "find": "value = 1",
            "replace": "value = 2",
            "must_fail": ["fake_command"],
        }
    )
    advice = check_gate_bite.recovery_advice("value-swap", "src/thing.py")

    for message in [advice, written[0]]:
        assert "verification/mutations.yml" in message
        assert "Do not use git checkout" in message
        assert "swap" in message
    assert "restore that file with git checkout" not in written[0]
