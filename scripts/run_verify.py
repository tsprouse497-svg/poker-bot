from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT


REPORT_DIR = REPO_ROOT / "reports" / "active"
PHASE_STATUS = REPO_ROOT / "phase_status.yml"
GATE_PHASE_STATUSES = {"active", "completed"}


@dataclass(frozen=True)
class CommandSpec:
    command: list[str]
    description: str


def uv_command() -> list[str] | None:
    if explicit := os.environ.get("UV_BIN"):
        return [explicit]
    if shutil.which("uv"):
        return ["uv"]
    base_python = getattr(sys, "_base_executable", sys.executable)
    if importlib.util.find_spec("uv") is not None:
        return [base_python, "-m", "uv"]
    return None


def uv_python_command() -> list[str]:
    uv = uv_command()
    if uv is not None:
        return uv + ["run", "python"]
    return [sys.executable]


def ruff_command() -> list[str]:
    """Lint the tree, without reading what an earlier run left behind.

    `--no-cache` is not tidiness. Phase 10 shipped a green `ruff_check` past two unsorted
    import blocks in a frozen test, because `.ruff_cache` held a clean verdict for those
    files from a run whose module classification differed. A gate command whose answer
    depends on the machine rather than on the tree is not a check.
    """
    uv = uv_command()
    if uv is not None:
        return uv + ["run", "ruff", "check", "--no-cache", "."]
    return [sys.executable, "-m", "ruff", "check", "--no-cache", "."]


COMMANDS = {
    "generate_status": CommandSpec(
        uv_python_command() + ["scripts/generate_status.py"],
        "Regenerate STATUS.md",
    ),
    "generate_phase_ledger": CommandSpec(
        uv_python_command() + ["scripts/generate_phase_ledger.py"],
        "Regenerate phase ledger",
    ),
    "generate_backlog": CommandSpec(
        uv_python_command() + ["scripts/generate_backlog.py"],
        "Regenerate backlog docs",
    ),
    "check_generated_status": CommandSpec(
        uv_python_command() + ["scripts/generate_status.py", "--check"],
        "Check generated STATUS.md freshness",
    ),
    "check_generated_phase_ledger": CommandSpec(
        uv_python_command() + ["scripts/generate_phase_ledger.py", "--check"],
        "Check generated phase ledger freshness",
    ),
    "check_generated_backlog": CommandSpec(
        uv_python_command() + ["scripts/generate_backlog.py", "--check"],
        "Check generated backlog freshness",
    ),
    "pytest_quality_hardening": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_quality_hardening.py"],
        "Run quality, drift, and phase-gate hardening tests",
    ),
    "run_full_quality_gate": CommandSpec(
        uv_python_command() + ["scripts/run_full_quality_gate.py"],
        "Run the quality checks and write the quality report",
    ),
    "check_contracts": CommandSpec(
        uv_python_command() + ["scripts/check_contracts.py"],
        "Validate phase contracts",
    ),
    "check_scope": CommandSpec(
        uv_python_command() + ["scripts/check_scope.py"],
        "Validate task scope",
    ),
    "check_execplan_delegation": CommandSpec(
        uv_python_command() + ["scripts/check_execplan_delegation.py"],
        "Validate active ExecPlan delegation plan",
    ),
    "check_repo_consistency": CommandSpec(
        uv_python_command() + ["scripts/check_repo_consistency.py"],
        "Cross-check phase status, ExecPlan location, gate commands, and the phase graph",
    ),
    "pytest_loop_fleet": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_loop_fleet.py"],
        "Run parallel-loop eligibility, lane discovery, and pause board tests",
    ),
    "freeze_tests": CommandSpec(
        uv_python_command() + ["scripts/freeze_tests.py"],
        "Rewrite the test freeze lock",
    ),
    "check_test_freeze": CommandSpec(
        uv_python_command() + ["scripts/freeze_tests.py", "--check"],
        "Check tests match verification/freeze.lock",
    ),
    "check_gate_bite": CommandSpec(
        uv_python_command() + ["scripts/check_gate_bite.py"],
        "Prove committed mutations make the gate fail",
    ),
    "check_file_sizes": CommandSpec(
        uv_python_command() + ["scripts/check_file_sizes.py"],
        "Validate file-size limits",
    ),
    "import_smoke": CommandSpec(
        uv_python_command()
        + ["-c", "import poker_training_bot; print(poker_training_bot.__version__)"],
        "Import package smoke test",
    ),
    "pytest": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests"],
        "Run tests",
    ),
    "pytest_poker_core": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_poker_core.py"],
        "Run poker-core tests",
    ),
    "pytest_hand_history": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_hand_history.py"],
        "Run hand-history tests",
    ),
    "generate_golden_hand_report": CommandSpec(
        uv_python_command() + ["scripts/generate_golden_hand_report.py"],
        "Generate golden-hand replay report",
    ),
    "generate_hand_history_replay_report": CommandSpec(
        uv_python_command() + ["scripts/generate_hand_history_replay_report.py"],
        "Generate normalized hand-history replay report",
    ),
    "pytest_strategy_contract": CommandSpec(
        uv_python_command()
        + ["-m", "pytest", "tests/test_strategy_contract.py", "tests/test_action_order.py"],
        "Run strategy-contract and turn-order tests",
    ),
    "generate_strategy_query_report": CommandSpec(
        uv_python_command() + ["scripts/generate_strategy_query_report.py"],
        "Generate strategy query report and decision audit",
    ),
    "pytest_preflop_artifacts": CommandSpec(
        uv_python_command()
        + [
            "-m",
            "pytest",
            "tests/test_preflop_positions.py",
            "tests/test_preflop_artifacts.py",
            "tests/test_preflop_lookup.py",
            "tests/test_preflop_committed_charts.py",
        ],
        "Run preflop position, artifact, and chart-lookup tests",
    ),
    "generate_preflop_chart_report": CommandSpec(
        uv_python_command() + ["scripts/generate_preflop_chart_report.py"],
        "Generate preflop chart coverage report",
    ),
    "pytest_full_table_preflop": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_full_table_preflop.py"],
        "Run full-table preflop strategy tests",
    ),
    "generate_preflop_strategy_report": CommandSpec(
        uv_python_command() + ["scripts/generate_preflop_strategy_report.py"],
        "Generate preflop strategy coverage and frequency report",
    ),
    "pytest_postflop_fallback": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_postflop_fallback.py"],
        "Run postflop fallback and composite strategy tests",
    ),
    "generate_postflop_fallback_report": CommandSpec(
        uv_python_command() + ["scripts/generate_postflop_fallback_report.py"],
        "Generate postflop fallback enumeration report and decision audit",
    ),
    "pytest_simulator": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_simulator.py"],
        "Run offline simulator and profile tests",
    ),
    "generate_profile_comparison_report": CommandSpec(
        uv_python_command() + ["scripts/generate_profile_comparison_report.py"],
        "Generate the bot/profile comparison report",
    ),
    "pytest_sample_comparison": CommandSpec(
        uv_python_command()
        + [
            "-m",
            "pytest",
            "tests/test_sample_comparison.py",
            "tests/test_sample_comparison_report.py",
        ],
        "Run public-corpus ingestion and player comparison tests",
    ),
    "generate_sample_comparison_report": CommandSpec(
        uv_python_command() + ["scripts/generate_sample_comparison_report.py"],
        "Generate the real-hand comparison report and its refusal inventory",
    ),
    "pytest_solver_export": CommandSpec(
        uv_python_command()
        + [
            "-m",
            "pytest",
            "tests/test_solver_export.py",
            "tests/test_solver_expectations.py",
        ],
        "Run GTOpen solver export, source-card, and expectations tests",
    ),
    "check_solver_export_expectations": CommandSpec(
        uv_python_command() + ["scripts/check_solver_export_expectations.py"],
        "Recompute the solver export's two orderings and check its source card against it",
    ),
    "generate_solver_export_report": CommandSpec(
        uv_python_command() + ["scripts/generate_solver_export_report.py"],
        "Generate the solver export range-grid and comparison report",
    ),
    "pytest_engine_fidelity": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_engine_fidelity.py"],
        "Run the engine and strategy-query fidelity tests",
    ),
    "generate_engine_fidelity_report": CommandSpec(
        uv_python_command() + ["scripts/generate_engine_fidelity_report.py"],
        "Generate the engine and query fidelity before/after report",
    ),
    "pytest_spot_vocabulary": CommandSpec(
        uv_python_command() + ["-m", "pytest", "tests/test_spot_vocabulary.py"],
        "Run the sizing-aware and second-orbit spot vocabulary tests",
    ),
    "generate_spot_vocabulary_report": CommandSpec(
        uv_python_command() + ["scripts/generate_spot_vocabulary_report.py"],
        "Generate the spot vocabulary report, key mapping, and price substitution census",
    ),
    "ruff_check": CommandSpec(
        ruff_command(),
        "Run ruff",
    ),
    "uv_import_smoke": CommandSpec(
        uv_python_command() + ["-c", "import poker_training_bot; print('uv import ok')"],
        "Prove uv environment can import the package",
    ),
}

BASE_GATE_GENERATORS = [
    "generate_status",
    "generate_phase_ledger",
    "generate_backlog",
]

BASE_GATE_CHECKS = [
    "check_generated_status",
    "check_generated_phase_ledger",
    "check_generated_backlog",
    "check_contracts",
    "check_scope",
    "check_execplan_delegation",
    "check_repo_consistency",
    "check_test_freeze",
    "check_file_sizes",
    # The fleet is repo tooling rather than phase work, so no contract declares it
    # and it belongs in the base gate.
    "pytest_loop_fleet",
    "import_smoke",
    "uv_import_smoke",
    "pytest",
    # After pytest: this one mutates files in place and restores them, so it must
    # not overlap another command reading the same tree.
    "check_gate_bite",
    "ruff_check",
]


def parse_frontmatter(text: str, path) -> dict:
    if not text.startswith("---\n"):
        raise ValueError(f"{path} is missing YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} has malformed YAML frontmatter")
    return yaml.safe_load(parts[1])


def contract_gate_commands() -> list[str]:
    phase_status = yaml.safe_load(PHASE_STATUS.read_text(encoding="utf-8"))
    commands: list[str] = []
    for phase in phase_status["phases"]:
        if phase["status"] not in GATE_PHASE_STATUSES:
            continue
        contract_path = REPO_ROOT / phase["contract"]
        meta = parse_frontmatter(contract_path.read_text(encoding="utf-8"), phase["contract"])
        for command_id in meta["required_gate_commands"]:
            if command_id not in commands:
                commands.append(command_id)
    return commands


def derive_gate() -> list[str]:
    gate = list(BASE_GATE_GENERATORS)
    for command_id in contract_gate_commands():
        if command_id not in gate and command_id not in BASE_GATE_CHECKS:
            gate.append(command_id)
    gate.extend(BASE_GATE_CHECKS)
    return gate


def run_command(command_id: str) -> dict:
    spec = COMMANDS[command_id]
    started = time.time()
    proc = subprocess.run(
        spec.command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return {
        "command_id": command_id,
        "description": spec.description,
        "command": spec.command,
        "returncode": proc.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
        "passed": proc.returncode == 0,
    }


def write_reports(results: list[dict]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at_epoch": int(time.time()),
        "all_passed": all(result["passed"] for result in results),
        "results": results,
    }
    (REPORT_DIR / "verify_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "Latest Verify Report",
        "====================",
        "",
        f"All passed: {payload['all_passed']}",
        "",
    ]
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"- {status} {result['command_id']}: {result['description']}")
    lines.append("")
    lines.append("Generated by scripts/run_verify.py.")
    (REPORT_DIR / "latest_verify.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _setup_failure(command_id: str, message: str) -> dict:
    return {
        "command_id": command_id,
        "description": "Gate setup failure",
        "command": [],
        "returncode": 2,
        "duration_seconds": 0.0,
        "stdout": "",
        "stderr": message,
        "passed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commands", nargs="*", help="Explicit command IDs to run")
    args = parser.parse_args()
    try:
        command_ids = args.commands or derive_gate()
    except Exception as exc:
        message = f"gate derivation failed: {exc}"
        write_reports([_setup_failure("derive_gate", message)])
        print(message, file=sys.stderr)
        return 2
    unknown = [command_id for command_id in command_ids if command_id not in COMMANDS]
    if unknown:
        message = (
            f"Unknown command IDs: {unknown}. "
            "Register new gate commands in COMMANDS in scripts/run_verify.py."
        )
        write_reports([_setup_failure("unknown_command_ids", message)])
        print(message, file=sys.stderr)
        return 2
    results = [run_command(command_id) for command_id in command_ids]
    write_reports(results)
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status} {result['command_id']}")
        if not result["passed"] and result["stderr"]:
            print(result["stderr"], file=sys.stderr)
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
