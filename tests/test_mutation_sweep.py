"""The mutation sweep's own machinery: what it proves, and what it costs to prove it.

`check_gate_bite` is the only thing in this repo that shows a test would notice a real
defect, and until 2026-09-08 it paid for that twice over: every command a mutation named
ran once with the bug in and once on the restored tree. These tests hold the cheaper
shape in place - a restore proved by comparing the bytes the sweep already held, and one
health pass at the end over the union of everything it ran.

They also hold the two other places that cost bought back: the loop's stage 7, which ran
the whole sweep a second time after `run_verify.py` had just run it, and the two pytest
commands long enough to be worth splitting across workers.

They live apart from `test_loop_machinery.py` only because that file is at its size cap.
"""

from __future__ import annotations

import subprocess

import pytest

import scripts.check_gate_bite as check_gate_bite
import scripts.check_repo_consistency as consistency
import scripts.loop_stage as loop_stage
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


# --------------------------------------------------------------------------- #
# what the sweep costs the loop, and the two commands that split their work
# --------------------------------------------------------------------------- #


def test_stage_seven_refuses_a_gate_that_would_not_run_the_sweep(monkeypatch) -> None:
    """The guarantee the deleted second sweep was really providing.

    A command leaves the derived gate silently when its phase's status changes, and a
    stage 7 that only watched `run_verify.py`'s exit code would then pass on a gate
    that never asked whether a defect would be noticed.
    """
    monkeypatch.setattr(loop_stage, "derive_gate", lambda: ["pytest", "ruff_check"])

    reason = loop_stage.sweep_missing_from_gate()

    assert reason
    assert "check_gate_bite" in reason
    assert "decorative" in reason


def test_stage_seven_is_satisfied_by_a_gate_that_contains_the_sweep(monkeypatch) -> None:
    monkeypatch.setattr(loop_stage, "derive_gate", lambda: ["pytest", "check_gate_bite"])

    assert loop_stage.sweep_missing_from_gate() is None


def test_the_committed_gate_is_one_stage_seven_would_accept() -> None:
    """The claim that matters: today's gate really does run the sweep."""
    assert loop_stage.sweep_missing_from_gate() is None


def test_a_gate_that_cannot_be_derived_is_a_reason_and_not_a_traceback(monkeypatch) -> None:
    """Stage 7 answers in reasons. A malformed `phase_status.yml` is one of them."""

    def explode() -> list[str]:
        raise ValueError("phase_status.yml is not a mapping")

    monkeypatch.setattr(loop_stage, "derive_gate", explode)

    reason = loop_stage.sweep_missing_from_gate()

    assert reason
    assert "phase_status.yml is not a mapping" in reason


def test_stage_seven_runs_the_sweep_once_by_running_it_only_inside_run_verify(
    monkeypatch,
) -> None:
    """Until 2026-09-08 this stage paid for the sweep twice.

    `check_gate_bite` is in `BASE_GATE_CHECKS`, so `run_verify.py` had just run it when
    the stage ran it again through `run_command`. Two three-hour sweeps, one attempt,
    and the second collected the evidence the first already had.
    """
    started: list[list[str]] = []
    directly_run: list[str] = []

    def fake_subprocess_run(command, **kwargs):
        started.append([str(part) for part in command])
        return subprocess.CompletedProcess(command, 0, "", "")

    def fake_run_command(command_id: str, clip: int | None = 4000) -> tuple[bool, str]:
        directly_run.append(command_id)
        return True, ""

    monkeypatch.setattr(loop_stage, "derive_gate", lambda: ["pytest", "check_gate_bite"])
    monkeypatch.setattr(loop_stage.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(loop_stage, "run_command", fake_run_command)

    assert loop_stage.check_full_gate(object()) == []
    assert len(started) == 1
    assert started[0][-1].endswith("run_verify.py")
    assert directly_run == []


def test_stage_seven_does_not_spend_the_gate_on_a_run_that_would_not_count(
    monkeypatch,
) -> None:
    """The gate takes hours. A stage that already knows the answer will not count
    should say so before spending them, not after."""
    started: list[object] = []

    monkeypatch.setattr(loop_stage, "derive_gate", lambda: ["pytest"])
    monkeypatch.setattr(
        loop_stage.subprocess, "run", lambda command, **kwargs: started.append(command)
    )

    reasons = loop_stage.check_full_gate(object())

    assert len(reasons) == 1
    assert started == []


def test_a_red_run_verify_still_says_why_a_surviving_mutation_would_matter(
    monkeypatch,
) -> None:
    """The reason text moved from the deleted second call to the one that remains.
    A red gate now covers both a failing test and a surviving mutation, so it has to
    name both rather than leaving the sweep's meaning behind with the call."""
    monkeypatch.setattr(loop_stage, "derive_gate", lambda: ["check_gate_bite"])
    monkeypatch.setattr(
        loop_stage.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 1, "", ""),
    )

    reasons = loop_stage.check_full_gate(object())

    assert len(reasons) == 1
    assert "check_gate_bite" in reasons[0]
    assert "decorative" in reasons[0]


def test_only_the_two_measured_commands_are_split_across_workers() -> None:
    """`-n 4 --dist loadfile` is not free: it costs four interpreter startups and it
    reorders the output a human reads. It is worth that on the whole suite and on the
    eleven chart files, which were measured at 95.4s and 69.5s on one core, and worth
    nothing on a command that finishes in a second. Anything else carrying the flags
    is a copy-paste, and anything that stops carrying them is a lost measurement.
    """
    split = [
        command_id
        for command_id, spec in run_verify.COMMANDS.items()
        if "-n" in spec.command or "--dist" in spec.command
    ]

    assert sorted(split) == ["pytest", "pytest_derived_chart"]


def test_each_split_command_carries_the_whole_flag_group_at_the_end() -> None:
    """`-n 4` without `--dist loadfile` is the default split, which does not keep a
    file's tests on one worker; that grouping is the reason these flags are safe for a
    suite whose files write into a shared tree."""
    for command_id in ["pytest", "pytest_derived_chart"]:
        command = run_verify.COMMANDS[command_id].command
        tail = command[-len(run_verify.PARALLEL_WORKER_FLAGS) :]
        assert tail == run_verify.PARALLEL_WORKER_FLAGS, command_id


def test_the_worker_count_is_a_number_and_not_the_machine_it_ran_on() -> None:
    """`auto` would make the gate's cost, and its oversubscription when several lanes
    gate at once on this machine, depend on which machine that is."""
    assert run_verify.PARALLEL_WORKER_FLAGS == ["-n", "4", "--dist", "loadfile"]


# --------------------------------------------------------------------------- #
# a tree that did not come back, and a witness that answers before it is asked
# --------------------------------------------------------------------------- #


def test_a_failed_restore_keeps_the_sentinel_that_blocks_a_commit(monkeypatch, tmp_path) -> None:
    """The one moment the guard is provably needed is the one it used to be removed.

    `check_scope` refuses a commit while the sentinel exists, which is what stopped a
    live mutation reaching history twice. A restore that comes back wrong is the case
    where that refusal is not precautionary, so the sentinel stays and the sweep says
    it did.
    """
    target = tmp_path / "src" / "thing.py"
    target.parent.mkdir(parents=True)
    target.write_text("value = 1\n", encoding="utf-8")
    sentinel = tmp_path / "verification" / ".mutation_in_progress"
    sentinel.parent.mkdir(parents=True)

    monkeypatch.setattr(check_gate_bite, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(check_gate_bite, "SENTINEL_PATH", sentinel)
    monkeypatch.setattr(check_gate_bite, "COMMANDS", {"fake_command": object()})
    monkeypatch.setattr(check_gate_bite, "run_registered", lambda command_id: False)
    monkeypatch.setattr(
        check_gate_bite,
        "restore_errors",
        lambda mutation, path, original: ["the file did not come back"],
    )

    errors = check_gate_bite.check_mutation(
        {
            "id": "value-swap",
            "file": "src/thing.py",
            "find": "value = 1",
            "replace": "value = 2",
            "must_fail": ["fake_command"],
        }
    )

    assert errors == ["the file did not come back"]
    assert sentinel.exists()


def test_the_sweep_stops_rather_than_mutating_a_tree_it_no_longer_understands(
    monkeypatch, tmp_path
) -> None:
    """Carrying on would report later verdicts against an unknown tree as if it were clean."""
    sentinel = tmp_path / ".mutation_in_progress"
    seen: list[str] = []
    health: list[str] = []

    def fake_check(mutation: dict) -> list[str]:
        seen.append(mutation["id"])
        if mutation["id"] == "second":
            sentinel.write_text("left behind\n", encoding="utf-8")
        return []

    def fake_run(command_id: str) -> bool:
        health.append(command_id)
        return True

    monkeypatch.setattr(check_gate_bite, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(check_gate_bite, "SENTINEL_PATH", sentinel)
    monkeypatch.setattr(check_gate_bite, "check_mutation", fake_check)
    monkeypatch.setattr(check_gate_bite, "COMMANDS", {"fake_command": object()})
    monkeypatch.setattr(check_gate_bite, "run_registered", fake_run)
    monkeypatch.setattr(
        check_gate_bite,
        "load_mutations",
        lambda: [
            {"id": name, "must_fail": ["fake_command"]} for name in ("first", "second", "third")
        ],
    )

    assert check_gate_bite.main() == 1
    assert seen == ["first", "second"]
    assert sentinel.exists()
    # The health pass is skipped too: on a tree known to be wrong every failure it
    # produced would describe the damage rather than the gate, at the cost of running
    # every witness once.
    assert health == []


def test_a_mutation_that_names_no_witness_is_refused_when_the_file_is_read(
    monkeypatch, tmp_path
) -> None:
    """A mutation with an empty `must_fail` asserts nothing and would pass by naming nothing."""
    path = tmp_path / "mutations.yml"
    path.write_text(
        "schema_version: 1\n"
        "mutations:\n"
        "  - id: names-nothing\n"
        "    file: src/thing.py\n"
        "    find: a\n"
        "    replace: b\n"
        "    must_fail: []\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check_gate_bite, "MUTATIONS_PATH", path)

    with pytest.raises(ValueError, match="names-nothing"):
        check_gate_bite.load_mutations()


def test_the_narrow_machinery_witness_cannot_answer_before_it_is_asked() -> None:
    """The command five mutations name must not contain the registry-wide assertion.

    `test_every_mutation_applies_exactly_once_to_its_file` counts each mutation's find
    string in the tree, so it is red while any mutation is applied, whatever that
    mutation does. A witness that fires for every defect distinguishes none of them,
    which is why the catch-all suite is exempt from mutation coverage rather than named.
    """
    command = run_verify.COMMANDS["pytest_loop_machinery"].command

    assert "--deselect" in command
    deselected = command[command.index("--deselect") + 1]
    assert deselected.endswith("::test_every_mutation_applies_exactly_once_to_its_file")
    assert deselected.split("::")[0] in command


def test_the_recovery_advice_names_the_line_because_a_repair_can_hit_the_wrong_one() -> None:
    """`spot-key-drops-the-raise-size` is the case that proved this ambiguous.

    It deletes a rendered size, which makes the mutated line identical to the line
    below it, so the `replace` string then occurs twice and "swap it back" does not
    say which one. This was found by repairing a real interrupted sweep by hand.
    """
    original = 'a = 1\nif x:\n    return "plain"\nreturn "plain"\n'
    find = '    return "plain"'

    assert check_gate_bite.mutated_line_number(original, find) == 3
    assert "line 3" in check_gate_bite.recovery_advice("some-id", "src/thing.py", 3)
    assert "identical to another one" in check_gate_bite.recovery_advice("some-id", "src/thing.py")
