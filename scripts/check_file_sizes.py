from __future__ import annotations

import sys
from pathlib import Path

from repo_paths import REPO_ROOT

LINE_LIMITS = [
    ("AGENTS.md", 150),
    ("STATUS.md", 120),
    ("docs/*.md", 500),
    ("docs/phase_contracts/*.md", 300),
    ("docs/exec_plans/**/*.md", 800),
    ("src/**/*.py", 500),
    ("tests/**/*.py", 700),
    ("reports/phase_audits/*.md", 500),
]
BYTE_LIMITS = [
    ("reports/active/*.txt", 300 * 1024),
    ("reports/active/*.json", 1024 * 1024),
    ("reports/phase_audits/logs/**/*.log", 500 * 1024),
]
# Total bytes across a committed data directory, not per file. A tree of artifacts is
# reviewable or it is not, and splitting one into ten files does not make it smaller.
# `data/artifacts` was covered by nothing until Phase 10 ruled it at 20 MB, so a 40 MB
# solver export committed with nothing objecting. Exceeding a limit here is a halt and a
# decision, not a number to raise.
DIRECTORY_BYTE_LIMITS = [
    ("data/artifacts", 20 * 1024 * 1024),
    ("data/samples", 5 * 1024 * 1024),
]


def count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    errors: list[str] = []
    for pattern, limit in LINE_LIMITS:
        for path in REPO_ROOT.glob(pattern):
            if path.is_file() and count_lines(path) > limit:
                errors.append(f"{path.relative_to(REPO_ROOT)} exceeds {limit} lines")
    for pattern, limit in BYTE_LIMITS:
        for path in REPO_ROOT.glob(pattern):
            if path.is_file() and path.stat().st_size > limit:
                errors.append(f"{path.relative_to(REPO_ROOT)} exceeds {limit} bytes")
    for relative, limit in DIRECTORY_BYTE_LIMITS:
        root = REPO_ROOT / relative
        if not root.exists():
            continue
        total = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
        if total > limit:
            errors.append(f"{relative} totals {total} bytes, over its {limit} byte limit")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
