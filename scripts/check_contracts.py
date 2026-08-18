from __future__ import annotations

import re
import sys

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

REQUIRED_FRONTMATTER = {
    "phase_id",
    "title",
    "depends_on",
    "required_gate_commands",
    "required_reports",
    "required_phase_audit",
}
REQUIRED_SECTIONS = [
    "Scope",
    "Non-goals",
    "Acceptance criteria",
    "Required reports",
    "Required command IDs",
    "Human vetting packet requirements",
    "Forbidden shortcuts",
    "Regression expectations",
]


def parse_frontmatter(text: str, path) -> dict:
    if not text.startswith("---\n"):
        raise ValueError(f"{path} is missing YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} has malformed YAML frontmatter")
    return yaml.safe_load(parts[1])


VALID_PHASE_STATUSES = {"future", "active", "completed"}

# The skeleton criteria every contract starts with. They are true of any phase, so
# a contract made only of these says nothing about what this phase must do: the
# gate would be asserting that the gate passed.
BOILERPLATE_CRITERIA = {
    "Required command IDs pass through `scripts/run_verify.py`.",
    "Required reports exist and are fresh for this phase.",
    "The phase audit packet includes plain-language pass/fail evidence.",
    "Any deferred work is recorded in `backlog.yml`.",
}
MIN_SPECIFIC_CRITERIA = 3

# Phases 00 through 02 were closed before this check existed, against contracts
# that carry only the boilerplate above. That is a real gap, not a false positive:
# those gates asserted little more than that the gate passed. Backfilling their
# criteria is a semantic contract change and so needs `contract-update` mode, which
# a maintenance task may not do. The exemption is explicit and tracked as
# CONTRACT-CRITERIA-BACKFILL in `backlog.yml`, and no new phase can join it.
CRITERIA_BACKFILL_EXEMPT = {"00", "01", "02"}


def section_bullets(text: str, heading: str) -> list[str]:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return []
    bullets: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        elif bullets and stripped and not stripped.startswith("#"):
            bullets[-1] = f"{bullets[-1]} {stripped}"
    return bullets


def check_criteria_are_specific(text: str, label: str, errors: list[str]) -> None:
    """An activated phase must say something a generic phase would not.

    Only enforced once a phase is active or completed. A future phase is allowed
    to still be a skeleton; that is what the contract-update stage is for.
    """
    specific = [
        bullet for bullet in section_bullets(text, "Acceptance criteria")
        if bullet not in BOILERPLATE_CRITERIA
    ]
    if len(specific) < MIN_SPECIFIC_CRITERIA:
        errors.append(
            f"{label} has only {len(specific)} phase-specific acceptance criteria;"
            f" an active or completed phase needs at least {MIN_SPECIFIC_CRITERIA}."
            " Criteria that merely restate the gate cannot fail."
        )


def contract_id_errors(seen_ids: set[str], declared_ids: set[str]) -> list[str]:
    """The two sides of the phase sequence, required to be the same set.

    This used to assert ten contracts numbered 00 through 09, so declaring a new
    phase meant editing the checker, and a contract that nobody declared could hide
    behind a matching count. Both sides now come from `phase_status.yml`.
    """
    errors = []
    undeclared = sorted(seen_ids - declared_ids)
    uncontracted = sorted(declared_ids - seen_ids)
    if undeclared:
        errors.append(
            f"contracts carry phase IDs nobody declares: {undeclared};"
            " a contract nothing declares is a phase nothing runs"
        )
    if uncontracted:
        errors.append(f"phase_status.yml declares phases with no contract: {uncontracted}")
    return errors


def check_phase_status(errors: list[str]) -> dict[str, str]:
    phase_status = yaml.safe_load((REPO_ROOT / "phase_status.yml").read_text(encoding="utf-8"))
    statuses: dict[str, str] = {}
    for phase in phase_status["phases"]:
        status = phase.get("status")
        if status not in VALID_PHASE_STATUSES:
            errors.append(
                f"phase_status.yml phase {phase.get('phase_id')!r} has invalid status "
                f"{status!r}; valid statuses are {sorted(VALID_PHASE_STATUSES)}"
            )
        statuses[str(phase.get("phase_id"))] = status
        if not (REPO_ROOT / str(phase.get("contract"))).exists():
            errors.append(f"phase_status.yml names missing contract {phase.get('contract')!r}")
    return statuses


def main() -> int:
    errors: list[str] = []
    statuses = check_phase_status(errors)
    contract_dir = REPO_ROOT / "docs" / "phase_contracts"
    paths = sorted(contract_dir.glob("PHASE_*.md"))
    declared = len(statuses)
    if len(paths) != declared:
        errors.append(
            f"phase_status.yml declares {declared} phases but"
            f" docs/phase_contracts/ holds {len(paths)} contracts;"
            " a contract nobody declares is a phase nothing runs"
        )
    seen_ids: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        try:
            meta = parse_frontmatter(text, path.relative_to(REPO_ROOT))
        except Exception as exc:
            errors.append(str(exc))
            continue
        missing = REQUIRED_FRONTMATTER - set(meta)
        if missing:
            errors.append(
                f"{path.relative_to(REPO_ROOT)} missing frontmatter fields: {sorted(missing)}"
            )
        phase_id = str(meta.get("phase_id"))
        if not re.fullmatch(r"\d{2}", phase_id):
            errors.append(f"{path.relative_to(REPO_ROOT)} has invalid phase_id {phase_id!r}")
        seen_ids.add(phase_id)
        for section in REQUIRED_SECTIONS:
            if f"## {section}" not in text:
                errors.append(f"{path.relative_to(REPO_ROOT)} missing section {section!r}")
        if (
            statuses.get(phase_id) in {"active", "completed"}
            and phase_id not in CRITERIA_BACKFILL_EXEMPT
        ):
            check_criteria_are_specific(text, str(path.relative_to(REPO_ROOT)), errors)
        if statuses.get(phase_id) == "completed":
            audit = REPO_ROOT / meta.get("required_phase_audit", "")
            if not audit.exists():
                errors.append(f"phase {phase_id} audit packet is missing")
            for report in meta.get("required_reports") or []:
                if not (REPO_ROOT / report).exists():
                    errors.append(f"phase {phase_id} required report {report!r} is missing")
    errors.extend(contract_id_errors(seen_ids, set(statuses)))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
