from __future__ import annotations

import fnmatch
import subprocess
import sys

import yaml
from repo_paths import REPO_ROOT


def tracked_or_pending_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    pending = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    files = set(tracked)
    for row in pending:
        name = row[3:] if len(row) > 3 else ""
        if " -> " in name:
            name = name.split(" -> ", 1)[1]
        if name:
            files.add(name.replace("\\", "/"))
    return sorted(files)


def matches(path: str, pattern: str) -> bool:
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-2])
    return fnmatch.fnmatch(path, pattern)


def main() -> int:
    task = yaml.safe_load((REPO_ROOT / "CURRENT_TASK.yml").read_text(encoding="utf-8"))
    approved = task["approved_scope"]
    forbidden = task["forbidden_scope"]
    errors: list[str] = []
    for path in tracked_or_pending_files():
        if path == ".gitignore":
            pass
        if any(matches(path, pattern) for pattern in forbidden):
            errors.append(f"forbidden scope touched: {path}")
        if not any(matches(path, pattern) for pattern in approved):
            errors.append(f"outside approved scope: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
