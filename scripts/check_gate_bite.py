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

Proving the restore is cheap and proving the tree is healthy is not, so the two
are separated. Each restore is proved by comparing the file's bytes to the copy
held in memory, which is exact and instant and catches a half-written file that a
passing test would not. Health is proved once, after the last mutation, over the
union of every command the sweep ran: that is also the pass that rewrites the
reports those commands emitted while a defect was live.
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


def recovery_advice(mutation_id: str, relative_file: str) -> str:
    """Say how to undo a live mutation by hand without destroying anything.

    Every one of these messages used to say "restore that file with git checkout".
    A reader who follows that throws away all uncommitted work in the file, and
    git kept no copy of it, so there is nothing to undo the undo with. In a lane
    worktree that work in progress is usually the very thing the sweep was called
    to certify. Swapping the two strings back is the same repair and loses none of
    it, which is why the safe route is spelled out here rather than left to the
    reader under pressure.
    """
    return (
        f"To undo it by hand, open {relative_file}, swap the {mutation_id!r} 'replace' string"
        " back to its 'find' string from verification/mutations.yml, delete"
        f" {SENTINEL_PATH.relative_to(REPO_ROOT)}, and delete that file's cached .pyc files."
        " Do not use git checkout on it: that silently discards uncommitted work."
    )


def health_command_ids(mutations: list[dict]) -> list[str]:
    """Every command the sweep will have run, listed once, in a stable order.

    The sweep used to re-run one mutation's own commands right after restoring it,
    which is the same evidence collected once per mutation and was most of the three
    hours.
    Once at the end asks for strictly more: the union covers commands this mutation
    never named, so a mutation that corrupts a file some other mutation's command
    reads is caught here and was not caught before.
    """
    command_ids: set[str] = set()
    for mutation in mutations:
        command_ids.update(mutation.get("must_fail") or [])
    return sorted(command_ids)


def restore_errors(mutation: dict, target: Path, original: str) -> list[str]:
    """Compare the restored file to the bytes it held before the mutation.

    This replaces re-running the gate to infer the restore worked. It is stronger
    as well as free: a test suite passing says nothing about a file whose comments
    or blank lines came back wrong, and it cannot run at all if the write left the
    file truncated.
    """
    try:
        restored = target.read_text(encoding="utf-8")
    except OSError as error:
        return [
            f"after restoring {mutation['id']!r}, {mutation['file']} could not be read"
            f" back: {error}. {recovery_advice(mutation['id'], mutation['file'])}"
        ]
    if restored == original:
        return []
    return [
        f"after restoring {mutation['id']!r}, {mutation['file']} does not match the bytes it"
        f" held before the mutation. {recovery_advice(mutation['id'], mutation['file'])}"
    ]


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
        f"mutating {mutation['file']} for {mutation_id}. If this file still exists, that"
        f" mutation may still be live. {recovery_advice(mutation_id, mutation['file'])}\n",
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
        errors.extend(restore_errors(mutation, target, original))
        SENTINEL_PATH.unlink(missing_ok=True)
    return errors


def main() -> int:
    if SENTINEL_PATH.exists():
        print(
            f"{SENTINEL_PATH.relative_to(REPO_ROOT)} exists, so a previous run was interrupted"
            " while a file was mutated, or a second run is in flight right now. The sentinel"
            f" says: {SENTINEL_PATH.read_text(encoding='utf-8').strip()}"
            " Follow that recovery and run again.",
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

    # One health pass, after the last restore, over every command the sweep ran.
    # Several of those commands write reports, and each one wrote its report from
    # mutated source, so this pass is what puts those files back as well as what
    # proves the tree still stands. Ids that are not registered are skipped rather
    # than looked up: check_mutation has already reported each one, and a lookup
    # here would raise a KeyError instead of printing the errors it collected.
    for command_id in health_command_ids(mutations):
        if command_id not in COMMANDS:
            continue
        if not run_registered(command_id):
            errors.append(
                f"the tree did not come back healthy after the sweep: {command_id!r} fails on"
                " the restored tree. Check the working tree for a file left mutated, and swap"
                " that mutation's 'replace' string back to its 'find' string from"
                " verification/mutations.yml rather than reaching for git checkout,"
                " which discards uncommitted work."
            )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"gate bites: {len(mutations)} mutations all caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
