from __future__ import annotations

import scripts.run_verify as run_verify


def test_base_gate_commands_are_registered() -> None:
    base = run_verify.BASE_GATE_GENERATORS + run_verify.BASE_GATE_CHECKS

    assert set(base).issubset(run_verify.COMMANDS)


def test_gate_includes_contract_commands_for_completed_phases() -> None:
    gate = run_verify.derive_gate()

    assert "generate_golden_hand_report" in gate
    assert "generate_hand_history_replay_report" in gate
    assert "pytest_poker_core" in gate
    assert "pytest_hand_history" in gate
    assert "pytest_strategy_contract" in gate
    assert "generate_strategy_query_report" in gate


def test_gate_includes_contract_commands_for_the_active_phase() -> None:
    gate = run_verify.derive_gate()

    assert "pytest_preflop_artifacts" in gate
    assert "generate_preflop_chart_report" in gate


def test_completed_phase_contract_commands_are_registered() -> None:
    unknown = [
        command_id
        for command_id in run_verify.contract_gate_commands()
        if command_id not in run_verify.COMMANDS
    ]

    assert unknown == []


def test_gate_generates_reports_before_freshness_checks() -> None:
    gate = run_verify.derive_gate()

    assert gate.index("generate_status") < gate.index("check_generated_status")
    assert gate.index("generate_phase_ledger") < gate.index("check_generated_phase_ledger")
    assert gate.index("generate_backlog") < gate.index("check_generated_backlog")


def test_gate_has_no_duplicate_commands() -> None:
    gate = run_verify.derive_gate()

    assert len(gate) == len(set(gate))


def test_gate_includes_the_loop_machinery_checks() -> None:
    gate = run_verify.derive_gate()

    assert "check_repo_consistency" in gate
    assert "check_test_freeze" in gate
    assert "check_gate_bite" in gate


def test_the_freeze_writer_is_not_in_the_gate() -> None:
    """A gate that rewrites the lock every run is not a freeze."""
    gate = run_verify.derive_gate()

    assert "freeze_tests" in run_verify.COMMANDS
    assert "freeze_tests" not in gate


def test_mutation_check_runs_after_the_suite_it_mutates() -> None:
    gate = run_verify.derive_gate()

    assert gate.index("pytest") < gate.index("check_gate_bite")
