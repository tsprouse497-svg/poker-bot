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
import scripts.check_repo_consistency as consistency
import scripts.quality_checks as quality_checks
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


# --------------------------------------------------------------------------- #
# what each mutation names as its witness
# --------------------------------------------------------------------------- #


def test_no_committed_mutation_names_the_whole_test_suite() -> None:
    """45 of the 74 named `pytest`, and that was 2h22m of a 3h sweep for nothing.

    `test_every_mutation_applies_exactly_once_to_its_file` counts each mutation's find
    string in its file and wants exactly one, so applying any mutation at all makes the
    whole suite red before a single behaviour is examined. Measured under four mutations
    in turn, that bookkeeping test was the only new failure each time. A witness that
    cannot fail to fire says nothing about the defect it is pointed at.
    """
    named_by = {
        mutation["id"]: mutation.get("must_fail") or []
        for mutation in check_gate_bite.load_mutations()
    }

    assert [name for name, commands in named_by.items() if "pytest" in commands] == []


def test_every_committed_mutation_still_names_a_witness() -> None:
    """The narrowing removed a command from 45 lists; it must have emptied none.

    A mutation with nothing in `must_fail` is applied, restored, and asserted about by
    nobody, which is worse than the catch-all it replaced.
    """
    unwitnessed = [
        mutation["id"]
        for mutation in check_gate_bite.load_mutations()
        if not (mutation.get("must_fail") or [])
    ]

    assert unwitnessed == []


def test_a_witness_the_derived_gate_does_not_run_is_reported() -> None:
    """The check's reason for existing, shown failing.

    `pytest_shelved` is registered and runnable, so `check_gate_bite` would still prove
    the mutation is caught. What nothing would catch is the real regression: the gate
    never runs that command, and the mutation registry goes on claiming otherwise.
    """
    errors: list[str] = []

    consistency.check_mutation_witnesses_run_in_the_gate(
        [
            {"id": "in-the-gate", "must_fail": ["pytest_run"]},
            {"id": "off-the-gate", "must_fail": ["pytest_run", "pytest_shelved"]},
        ],
        ["pytest_run", "check_scope"],
        errors,
    )

    assert len(errors) == 1
    assert "off-the-gate" in errors[0]
    assert "pytest_shelved" in errors[0]


def test_a_mutation_with_no_witness_reaches_the_gate_check_without_raising() -> None:
    """The two checks are separate: this one judges the commands named, not whether
    any were. An entry with no `must_fail` key at all must not crash it."""
    errors: list[str] = []

    consistency.check_mutation_witnesses_run_in_the_gate(
        [{"id": "bare"}, {"id": "empty", "must_fail": []}], [], errors
    )

    assert errors == []


def test_every_committed_witness_is_a_command_this_gate_runs() -> None:
    """And the same check against the repo, which is the claim that matters."""
    errors: list[str] = []

    consistency.check_mutation_witnesses_run_in_the_gate(
        check_gate_bite.load_mutations(), run_verify.derive_gate(), errors
    )

    assert errors == []


def test_the_catch_all_suite_is_exempt_by_name_and_says_why() -> None:
    """An exemption is a decision with a reason, not a way to make a check pass.

    `pytest` is the one command that cannot be a witness, so it is the one command the
    coverage rule may skip, and the reason has to be in the diff a reviewer reads.
    """
    reason = quality_checks.EXEMPT_FROM_MUTATION_COVERAGE.get("pytest")

    assert reason
    assert "bookkeeping test" in reason


def test_the_exemption_silences_only_the_catch_all() -> None:
    """Every other pytest command still owes a mutation, exemption or no exemption."""
    errors = quality_checks.mutation_coverage_errors(
        command_ids=["pytest", "pytest_naked"],
        mutations=[],
        exempt=quality_checks.EXEMPT_FROM_MUTATION_COVERAGE,
    )

    assert len(errors) == 1
    assert "pytest_naked" in errors[0]
