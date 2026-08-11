from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT


ACTIVE_EXECPLAN_DIR = REPO_ROOT / "docs" / "exec_plans" / "active"
REQUIRED_DELEGATION_FIELDS = [
    "Worker lanes",
    "Ownership",
    "Expected outputs",
    "Status",
    "Integration order",
    "Review handoff",
]
PLACEHOLDER_PREFIXES = ("list ", "state ")
PLACEHOLDER_VALUES = {
    "planned, assigned, integrated, blocked, or completed for each lane.",
    "concrete reason implementation is coordinator-owned.",
}


def section_body(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if match is None:
        return None
    return match.group(1).strip()


def has_no_delegation_exception(body: str) -> bool:
    match = re.search(r"(?im)^-\s*No-delegation exception:\s*(.+)$", body)
    if not match:
        return False
    value = match.group(1).strip()
    return bool(value and not is_placeholder_value(value))


def is_placeholder_value(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized.startswith(PLACEHOLDER_PREFIXES) or normalized in PLACEHOLDER_VALUES


def incomplete_required_fields(body: str) -> list[str]:
    missing = []
    for field in REQUIRED_DELEGATION_FIELDS:
        match = re.search(rf"(?im)^-\s*{re.escape(field)}:\s*(.+)$", body)
        if not match or is_placeholder_value(match.group(1)):
            missing.append(field)
    return missing


def pause_declaration(text: str) -> str | None:
    """The reason an active ExecPlan is legitimately idle, if it declares one.

    The loop halts at its human gate: the phase is genuinely unfinished, its plan
    genuinely belongs in `active/`, and no task is open. That state has to be
    expressible, or the only way to pass the gate is to lie about the phase being
    done. Declaring it is the price: a plan resting at idle must say what it waits
    on.
    """
    match = re.search(r"(?im)^-\s*Paused:\s*(.+)$", text)
    if not match:
        return None
    reason = match.group(1).strip()
    return reason if reason and not is_placeholder_value(reason) else None


def validate_execplan_text(text: str, label: str) -> list[str]:
    body = section_body(text, "Delegation Plan")
    if body is None:
        return [f"{label} missing required '## Delegation Plan' section"]
    if has_no_delegation_exception(body):
        return []
    incomplete = incomplete_required_fields(body)
    if incomplete:
        return [f"{label} Delegation Plan missing fields or values: {', '.join(incomplete)}"]
    return []


def validate_execplan(path: Path) -> list[str]:
    try:
        relative = path.relative_to(REPO_ROOT)
    except ValueError:
        relative = path
    text = path.read_text(encoding="utf-8")
    return validate_execplan_text(text, str(relative))


VALID_TASK_MODES = {"idle", "implementation", "contract-update", "maintenance"}


def task_mode() -> str:
    task = yaml.safe_load((REPO_ROOT / "CURRENT_TASK.yml").read_text(encoding="utf-8"))
    mode = task.get("task_mode")
    if mode not in VALID_TASK_MODES:
        raise ValueError(f"task_mode {mode!r} is not one of {sorted(VALID_TASK_MODES)}")
    return mode


def main() -> int:
    paths = sorted(ACTIVE_EXECPLAN_DIR.glob("*.md"))
    errors: list[str] = []
    if task_mode() == "idle":
        for path in paths:
            if pause_declaration(path.read_text(encoding="utf-8")):
                continue
            errors.append(
                f"{path.relative_to(REPO_ROOT)} is still active while task_mode is idle; "
                "move completed ExecPlans to docs/exec_plans/completed/, or declare "
                "'- Paused: <what it waits on>' if the phase is genuinely unfinished"
            )
    elif not paths:
        errors.append("no active ExecPlan markdown files found")
    for path in paths:
        errors.extend(validate_execplan(path))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
