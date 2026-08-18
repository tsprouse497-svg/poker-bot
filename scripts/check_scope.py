from __future__ import annotations

import fnmatch
import re
import subprocess
import sys

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT


VALID_TASK_MODES = {"idle", "implementation", "contract-update", "maintenance"}

# check_gate_bite writes this while a source file is deliberately broken, and removes
# it in a finally block. An interrupted run leaves both behind.
MUTATION_SENTINEL = "verification/.mutation_in_progress"


def mutation_sentinel_errors() -> list[str]:
    """Refuse the whole gate while a planted defect is live in the tree.

    The sentinel used to protect only the next mutation run, which refuses to start
    when it finds one. That leaves the dangerous window unguarded: while a run is in
    flight the tree genuinely holds a deliberate defect, and a `git add -A` in that
    moment commits it. That has happened twice, and the second time the symptom
    surfaced as an unrelated scope error rather than as the planted bug.

    The sentinel is gitignored now, so it can never be staged. This check is what
    replaces the accidental catch that gave: a file git cannot see is a file the
    scope diff cannot report either, so the tree's state is asserted here instead.
    """
    sentinel = REPO_ROOT / MUTATION_SENTINEL
    if not sentinel.exists():
        return []
    return [
        f"{MUTATION_SENTINEL} exists, so a mutation is live in the working tree:"
        f" {sentinel.read_text(encoding='utf-8').strip()}."
        " Nothing may be committed until that file is restored and the sentinel deleted"
    ]


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


def is_overbroad(pattern: str) -> bool:
    """Reject patterns that authorize far more than they appear to.

    `fnmatch` does not treat `/` as a separator, so `*` crosses directories: a
    scope of `*` or `*.py` silently authorizes the whole tree. A pattern has to be
    anchored to a directory to mean what a reader thinks it means.
    """
    cleaned = pattern.strip()
    if cleaned in {"", "*", "**", "/**", "./**", "*/**"}:
        return True
    return cleaned.startswith("*") and "/" not in cleaned


def base_task(base_commit: str) -> dict:
    """The task file as it stood at `base_commit`.

    Scope is only meaningful if it can be compared to something the current task
    did not write. Reading the base revision is what makes a task's own widening
    of its own scope visible instead of free.
    """
    proc = subprocess.run(
        ["git", "show", f"{base_commit}:CURRENT_TASK.yml"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return {}
    return yaml.safe_load(proc.stdout) or {}


def log_entries(task: dict) -> set[tuple[str, str]]:
    entries = set()
    for entry in task.get("scope_change_log") or []:
        if isinstance(entry, dict):
            entries.add((str(entry.get("date")), str(entry.get("reason"))))
    return entries


def relaxations(base: dict, approved: list[str], forbidden: list[str]) -> list[str]:
    """Ways the current task loosened the limits it inherited.

    Widening `approved_scope` and shrinking `forbidden_scope` are both relaxations
    and both need a reason on the record. Narrowing either is always allowed.
    """
    widened = sorted(set(approved) - set(base.get("approved_scope") or []))
    unforbidden = sorted(set(base.get("forbidden_scope") or []) - set(forbidden))
    notes = [f"approved_scope widened to include {pattern!r}" for pattern in widened]
    notes += [f"forbidden_scope no longer covers {pattern!r}" for pattern in unforbidden]
    return notes


def main() -> int:
    task = yaml.safe_load((REPO_ROOT / "CURRENT_TASK.yml").read_text(encoding="utf-8"))
    mode = task.get("task_mode")
    if mode not in VALID_TASK_MODES:
        print(f"task_mode {mode!r} is not one of {sorted(VALID_TASK_MODES)}", file=sys.stderr)
        return 1
    approved = task.get("approved_scope") or []
    standing = task.get("standing_scope") or []
    forbidden = task.get("forbidden_scope") or []
    raw_base = task.get("base_commit")
    base_commit = str(raw_base or "HEAD")

    if subprocess.run(
        ["git", "cat-file", "-e", f"{base_commit}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
    ).returncode != 0:
        print(f"base_commit {base_commit!r} is not a known commit", file=sys.stderr)
        return 1

    errors: list[str] = mutation_sentinel_errors()

    # A task that measures itself against HEAD has no scope at all: anything it
    # already committed is invisible to the diff.
    if mode != "idle" and not re.fullmatch(r"[0-9a-f]{40}", str(raw_base or "")):
        errors.append(
            f"base_commit must be a full 40-character commit sha while task_mode is {mode!r},"
            f" got {raw_base!r}"
        )

    for pattern in approved + standing:
        if is_overbroad(pattern):
            errors.append(
                f"scope pattern {pattern!r} is over-broad;"
                " '*' crosses directory separators, so anchor the pattern to a directory"
            )

    if raw_base:
        base = base_task(base_commit)
        loosened = relaxations(base, approved, forbidden)
        if loosened and not (log_entries(task) - log_entries(base)):
            for note in loosened:
                errors.append(
                    f"{note} without a new scope_change_log entry;"
                    " a task may not quietly widen the limits it started from"
                )
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
