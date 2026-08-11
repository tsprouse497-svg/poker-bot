from __future__ import annotations

import re
import sys

import yaml
from repo_paths import REPO_ROOT

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
    if len(paths) != 10:
        errors.append(f"expected 10 phase contracts, found {len(paths)}")
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
        if statuses.get(phase_id) == "completed":
            audit = REPO_ROOT / meta.get("required_phase_audit", "")
            if not audit.exists():
                errors.append(f"phase {phase_id} audit packet is missing")
            for report in meta.get("required_reports") or []:
                if not (REPO_ROOT / report).exists():
                    errors.append(f"phase {phase_id} required report {report!r} is missing")
    if seen_ids != {f"{idx:02d}" for idx in range(10)}:
        errors.append(f"phase contract IDs are incomplete: {sorted(seen_ids)}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
