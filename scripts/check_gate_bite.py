"""Prove the gate bites before trusting it to certify anything.

A green gate only means the tests in the repo pass against the code in the repo.
That is worth very little when the same author wrote both, because a test can be
weak from birth and stay green forever. Freezing test hashes cannot catch that: it
preserves a weak test perfectly.

So this check attacks the gate instead of the code. It applies each committed
mutation from `verification/mutations.yml` in place, runs the gate command that
claims to cover that behavior, and requires the command to fail. A mutation that
survives is a gate failure.

Mutations are applied in place and restored in a `finally` block, with a sentinel
file written first. If the process is killed hard enough to skip the restore, the
sentinel stays behind and the next run refuses to start rather than mutating an
already-mutated tree.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_verify import COMMANDS  # noqa: E402

MUTATIONS_PATH = REPO_ROOT / "verification" / "mutations.yml"
SENTINEL_PATH = REPO_ROOT / "verification" / ".mutation_in_progress"
SCHEMA_VERSION = 1


def load_mutations() -> list[dict]:
    data = yaml.safe_load(MUTATIONS_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"mutations.yml schema_version {data.get('schema_version')!r} is not {SCHEMA_VERSION}"
        )
    mutations = data.get("mutations") or []
    if not mutations:
        raise ValueError("mutations.yml declares no mutations, so the gate is unproven")
    return mutations


def purge_bytecode(path: Path) -> None:
    """Drop cached bytecode for one source file.

    Necessary, not tidiness. CPython validates a `.pyc` against the source's
    mtime and size, and a mutation that swaps two equal-length tokens changes
    neither if the write and the restore land in the same clock second. The
    interpreter then keeps executing mutated bytecode after the source has been
    put back, which shows up as an unrelated test failure on some later run. This
    was not hypothetical: it happened on the first full gate run after this check
    was written.
    """
    cache = path.parent / "__pycache__"
    if not cache.is_dir():
        return
    for stale in cache.glob(f"{path.stem}.*.pyc"):
        stale.unlink(missing_ok=True)


def run_registered(command_id: str) -> bool:
    """Run a gate command with bytecode writing disabled, returning pass/fail."""
    spec = COMMANDS[command_id]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(spec.command, cwd=REPO_ROOT, capture_output=True, text=True, env=env)
    return proc.returncode == 0


def check_mutation(mutation: dict) -> list[str]:
    errors: list[str] = []
    mutation_id = mutation["id"]
    target = REPO_ROOT / mutation["file"]
    if not target.exists():
        return [f"mutation {mutation_id!r} names missing file {mutation['file']}"]

    original = target.read_text(encoding="utf-8")
    occurrences = original.count(mutation["find"])
    if occurrences != 1:
        return [
            f"mutation {mutation_id!r} expected exactly one match in {mutation['file']},"
            f" found {occurrences}; the code moved and the mutation no longer applies"
        ]

    unknown = [command for command in mutation["must_fail"] if command not in COMMANDS]
    if unknown:
        return [f"mutation {mutation_id!r} names unregistered commands: {unknown}"]

    SENTINEL_PATH.write_text(
        f"mutating {mutation['file']} for {mutation_id};"
        " if this file exists, restore that file with git checkout\n",
        encoding="utf-8",
    )
    try:
        purge_bytecode(target)
        target.write_text(original.replace(mutation["find"], mutation["replace"]), encoding="utf-8")
        for command_id in mutation["must_fail"]:
            if run_registered(command_id):
                errors.append(
                    f"mutation {mutation_id!r} survived {command_id!r}:"
                    " the gate does not cover this behavior"
                )
    finally:
        target.write_text(original, encoding="utf-8")
        purge_bytecode(target)
        SENTINEL_PATH.unlink(missing_ok=True)

    # Prove the tree is healthy again rather than assuming it. A restore that
    # leaves the repo failing is worse than a surviving mutation, because it looks
    # like a defect somewhere else entirely.
    for command_id in mutation["must_fail"]:
        if not run_registered(command_id):
            errors.append(
                f"after restoring {mutation_id!r}, {command_id!r} is still failing:"
                f" restore {mutation['file']} with git checkout before trusting this run"
            )
    return errors


def main() -> int:
    if SENTINEL_PATH.exists():
        print(
            f"{SENTINEL_PATH.relative_to(REPO_ROOT)} exists, so a previous run was interrupted"
            " while a file was mutated, or a second run is in flight right now. The sentinel"
            f" says: {SENTINEL_PATH.read_text(encoding='utf-8').strip()}."
            " Restore that file with git checkout, delete the sentinel, and run again.",
            file=sys.stderr,
        )
        return 1

    try:
        mutations = load_mutations()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1

    errors: list[str] = []
    for mutation in mutations:
        errors.extend(check_mutation(mutation))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"gate bites: {len(mutations)} mutations all caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
