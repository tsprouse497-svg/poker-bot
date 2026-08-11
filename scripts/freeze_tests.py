"""Freeze the test suite so an implementer cannot weaken its own checks.

Writing the lock is deliberate and separate from checking it. `--check` belongs in
the gate; writing does not, because a gate that refreshes the lock every run is
not a freeze.

The lock records three things per run: a content hash for every test file, the
number of test functions in it, and a suite-wide floor for that count. The hash
catches an edit. The floor catches the subtler move of rewriting a file so it is
smaller than it was, which a per-file hash cannot notice once the hash is
legitimately updated.

A test change is not forbidden, only visible: re-run this script and the lock diff
is the record of what changed. The loop driver halts on that diff rather than
letting it pass unremarked.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import sys
from pathlib import Path

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

LOCK_PATH = REPO_ROOT / "verification" / "freeze.lock"
TEST_DIR = REPO_ROOT / "tests"
SCHEMA_VERSION = 1


def test_files() -> list[Path]:
    return sorted(path for path in TEST_DIR.glob("test_*.py") if path.is_file())


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_function_count(path: Path) -> int:
    """Count test functions, module level and inside `Test*` classes.

    Counted from the syntax tree rather than from a pytest collection run so the
    number is stable, fast, and does not depend on the environment pytest happens
    to import.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    count = 0
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
            "test_"
        ):
            count += 1
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for member in node.body:
                if isinstance(
                    member, ast.FunctionDef | ast.AsyncFunctionDef
                ) and member.name.startswith("test_"):
                    count += 1
    return count


def current_state() -> dict:
    files = {}
    total = 0
    for path in test_files():
        relative = str(path.relative_to(REPO_ROOT))
        count = test_function_count(path)
        total += count
        files[relative] = {"sha256": file_digest(path), "test_functions": count}
    return {"schema_version": SCHEMA_VERSION, "test_function_floor": total, "files": files}


def render(state: dict) -> str:
    return yaml.safe_dump(state, sort_keys=True)


def load_lock() -> dict | None:
    if not LOCK_PATH.exists():
        return None
    return yaml.safe_load(LOCK_PATH.read_text(encoding="utf-8"))


def compare(lock: dict, state: dict) -> list[str]:
    errors: list[str] = []
    if lock.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"freeze.lock schema_version {lock.get('schema_version')!r} is not {SCHEMA_VERSION}"
        )
    locked_files = lock.get("files") or {}
    current_files = state["files"]
    for relative, entry in sorted(locked_files.items()):
        if relative not in current_files:
            errors.append(f"frozen test file is gone: {relative}")
            continue
        if current_files[relative]["sha256"] != entry.get("sha256"):
            errors.append(
                f"frozen test file changed: {relative}"
                " (re-run scripts/freeze_tests.py and review the lock diff)"
            )
    for relative in sorted(set(current_files) - set(locked_files)):
        errors.append(
            f"test file is not in the freeze lock: {relative}"
            " (an implementer must not add its own tests)"
        )
    floor = lock.get("test_function_floor")
    if isinstance(floor, int) and state["test_function_floor"] < floor:
        errors.append(
            "test function count fell from the frozen floor:"
            f" {state['test_function_floor']} < {floor}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the working tree against verification/freeze.lock",
    )
    args = parser.parse_args()
    state = current_state()

    if not args.check:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOCK_PATH.write_text(render(state), encoding="utf-8")
        print(
            f"froze {len(state['files'])} test files,"
            f" {state['test_function_floor']} test functions"
        )
        return 0

    lock = load_lock()
    if lock is None:
        print(
            f"{LOCK_PATH.relative_to(REPO_ROOT)} is missing;"
            " run scripts/freeze_tests.py to create it",
            file=sys.stderr,
        )
        return 1
    errors = compare(lock, state)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"test freeze intact: {len(state['files'])} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
