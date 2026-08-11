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
    uv = uv_command()
    if uv is not None:
        return uv + ["run", "ruff", "check", "."]
    return [sys.executable, "-m", "ruff", "check", "."]


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
    "check_file_sizes",
    "import_smoke",
    "uv_import_smoke",
    "pytest",
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
