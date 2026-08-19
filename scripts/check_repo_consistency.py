"""Cross-checks between the repo's separate sources of truth.

Each check here exists because two files can drift apart while both stay
individually valid, and a gate that only validates files one at a time cannot see
it.

- A gate command a contract declares must exist in the registry, or the phase's
  own gate silently shrinks to whatever happens to be registered.
- A `pytest_*` gate command must point at a test file that actually holds tests.
  An empty or renamed test file passes pytest, so the command id would certify
  nothing.
- A phase's status must agree with where its ExecPlan lives. `run_verify.py`
  derives the gate from status alone, so a completed phase whose plan is still
  active, or a future phase whose plan is already filed as completed, means one of
  the two is lying.
- Every `depends_on` must name a real phase and the graph must be acyclic.
  `scripts/loop_fleet.py` decides which phases may start from that graph alone, so
  a typo makes a phase unstartable forever and a cycle makes a whole group of them
  unstartable. Both fail quietly as "waiting on a dependency", which is exactly what
  ordinary waiting looks like.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from freeze_tests import test_function_count  # noqa: E402
from run_verify import COMMANDS, parse_frontmatter  # noqa: E402

PHASE_STATUS = REPO_ROOT / "phase_status.yml"
ACTIVE_PLANS = REPO_ROOT / "docs" / "exec_plans" / "active"
COMPLETED_PLANS = REPO_ROOT / "docs" / "exec_plans" / "completed"
GATE_PHASE_STATUSES = {"active", "completed"}


def phases() -> list[dict]:
    return yaml.safe_load(PHASE_STATUS.read_text(encoding="utf-8"))["phases"]


def check_declared_commands_registered(phase: dict, errors: list[str]) -> None:
    contract = REPO_ROOT / phase["contract"]
    meta = parse_frontmatter(contract.read_text(encoding="utf-8"), phase["contract"])
    for command_id in meta.get("required_gate_commands") or []:
        if command_id not in COMMANDS:
            errors.append(
                f"phase {phase['phase_id']} declares gate command {command_id!r}"
                " which is not registered in scripts/run_verify.py"
            )


def test_paths(command: list[str]) -> list[Path]:
    return [REPO_ROOT / arg for arg in command if arg.startswith("tests/") and arg.endswith(".py")]


def check_pytest_commands_hold_tests(errors: list[str]) -> None:
    for command_id, spec in sorted(COMMANDS.items()):
        if not command_id.startswith("pytest_"):
            continue
        paths = test_paths(spec.command)
        if not paths:
            errors.append(f"gate command {command_id!r} names no test file")
            continue
        for path in paths:
            relative = path.relative_to(REPO_ROOT)
            if not path.exists():
                errors.append(f"gate command {command_id!r} names missing test file {relative}")
            elif test_function_count(path) == 0:
                errors.append(f"gate command {command_id!r} names {relative}, which holds no tests")


def plan_name(phase: dict) -> str:
    return Path(phase["contract"]).name


def check_plan_location(phase: dict, errors: list[str]) -> None:
    name = plan_name(phase)
    status = phase["status"]
    in_active = (ACTIVE_PLANS / name).exists()
    in_completed = (COMPLETED_PLANS / name).exists()
    phase_id = phase["phase_id"]
    if in_active and in_completed:
        errors.append(f"phase {phase_id} ExecPlan {name} exists in both active and completed")
    if status == "completed" and not in_completed:
        errors.append(f"phase {phase_id} is completed but its ExecPlan is not in completed/")
    if status == "completed" and in_active:
        errors.append(f"phase {phase_id} is completed but its ExecPlan is still active")
    if status == "future" and in_completed:
        errors.append(
            f"phase {phase_id} is still future but its ExecPlan is filed as completed;"
            " a future phase is excluded from the derived gate"
        )
    if status == "active" and not in_active:
        errors.append(f"phase {phase_id} is active but has no ExecPlan in active/")


def dependency_graph(all_phases: list[dict]) -> dict[str, list[str]]:
    graph = {}
    for phase in all_phases:
        contract = REPO_ROOT / phase["contract"]
        meta = parse_frontmatter(contract.read_text(encoding="utf-8"), phase["contract"])
        graph[str(phase["phase_id"])] = [str(dep) for dep in (meta.get("depends_on") or [])]
    return graph


def check_dependency_graph(all_phases: list[dict], errors: list[str]) -> None:
    graph = dependency_graph(all_phases)
    known = set(graph)
    for phase_id, deps in sorted(graph.items()):
        for dep in deps:
            if dep not in known:
                errors.append(
                    f"phase {phase_id} depends_on {dep!r}, which is not a phase in phase_status.yml"
                )
    for phase_id in sorted(cyclic_phases(graph)):
        errors.append(f"phase {phase_id} is on a depends_on cycle, so it can never start")


def cyclic_phases(graph: dict[str, list[str]]) -> set[str]:
    """Phases reachable from themselves through `depends_on`."""
    colour: dict[str, int] = {}
    found: set[str] = set()

    def walk(node: str) -> None:
        colour[node] = 1
        for dep in graph.get(node, []):
            if colour.get(dep) == 1:
                found.add(dep)
            elif colour.get(dep) is None and dep in graph:
                walk(dep)
        colour[node] = 2

    for node in graph:
        if colour.get(node) is None:
            walk(node)
    return found


def main() -> int:
    errors: list[str] = []
    check_pytest_commands_hold_tests(errors)
    check_dependency_graph(phases(), errors)
    for phase in phases():
        if phase["status"] in GATE_PHASE_STATUSES:
            check_declared_commands_registered(phase, errors)
        check_plan_location(phase, errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("repo consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
