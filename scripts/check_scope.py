from __future__ import annotations

import fnmatch
import subprocess
import sys

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT


VALID_TASK_MODES = {"idle", "implementation", "contract-update", "maintenance"}


def git_lines(*args: str) -> list[str]:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()


def tracked_or_pending_files() -> list[str]:
    files = set(git_lines("ls-files"))
    for row in git_lines("status", "--porcelain"):
        name = row[3:] if len(row) > 3 else ""
        if " -> " in name:
            name = name.split(" -> ", 1)[1]
        if name:
            files.add(name.replace("\\", "/"))
    return sorted(files)


def changed_files(base_commit: str) -> list[str]:
    files = set(git_lines("diff", "--no-renames", "--name-only", base_commit))
    for row in git_lines("status", "--porcelain"):
        name = row[3:] if len(row) > 3 else ""
        if " -> " in name:
            old, new = name.split(" -> ", 1)
            files.add(old.replace("\\", "/"))
            files.add(new.replace("\\", "/"))
        elif name:
            files.add(name.replace("\\", "/"))
    return sorted(files)


def matches(path: str, pattern: str) -> bool:
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-2])
    return fnmatch.fnmatch(path, pattern)


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(matches(path, pattern) for pattern in patterns)


def main() -> int:
    task = yaml.safe_load((REPO_ROOT / "CURRENT_TASK.yml").read_text(encoding="utf-8"))
    mode = task.get("task_mode")
    if mode not in VALID_TASK_MODES:
        print(f"task_mode {mode!r} is not one of {sorted(VALID_TASK_MODES)}", file=sys.stderr)
        return 1
    approved = task.get("approved_scope") or []
    standing = task.get("standing_scope") or []
    forbidden = task.get("forbidden_scope") or []
    base_commit = str(task.get("base_commit") or "HEAD")

    if subprocess.run(
        ["git", "cat-file", "-e", f"{base_commit}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
    ).returncode != 0:
        print(f"base_commit {base_commit!r} is not a known commit", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in tracked_or_pending_files():
        if matches_any(path, forbidden):
            errors.append(f"forbidden scope touched: {path}")
    for path in changed_files(base_commit):
        if matches_any(path, forbidden):
            continue
        if not matches_any(path, approved) and not matches_any(path, standing):
            errors.append(f"outside approved scope: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
