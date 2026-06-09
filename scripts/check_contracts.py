from __future__ import annotations

import re
import sys

import yaml
from repo_paths import REPO_ROOT

REQUIRED_FRONTMATTER = {
    "phase_id",
    "title",
    "status",
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


def main() -> int:
    errors: list[str] = []
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
        audit = REPO_ROOT / meta.get("required_phase_audit", "")
        if phase_id == "00" and not audit.exists():
            errors.append("Phase 00 audit packet is missing")
    if seen_ids != {f"{idx:02d}" for idx in range(10)}:
        errors.append(f"phase contract IDs are incomplete: {sorted(seen_ids)}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
