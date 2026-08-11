from __future__ import annotations

import subprocess

import pytest

import scripts.check_scope as check_scope


def test_matches_double_star_directory_patterns() -> None:
    assert check_scope.matches("data/raw/hands.json", "data/raw/**")
    assert check_scope.matches("data/raw", "data/raw/**")
    assert not check_scope.matches("data/rawer/hands.json", "data/raw/**")
    assert not check_scope.matches("docs/raw/hands.json", "data/raw/**")


def test_matches_plain_glob_patterns() -> None:
    assert check_scope.matches("AGENTS.md", "AGENTS.md")
    assert check_scope.matches("STATUS.md", "*.md")
    assert not check_scope.matches("docs/STATUS.md", "STATUS.md")


def _git(repo, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def scoped_repo(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    (tmp_path / "allowed.txt").write_text("a\n", encoding="utf-8")
    (tmp_path / "CURRENT_TASK.yml").write_text(
        "task_id: T\n"
        "task_mode: implementation\n"
        "base_commit: null\n"
        "approved_scope:\n"
        "  - allowed.txt\n"
        "standing_scope:\n"
        "  - CURRENT_TASK.yml\n"
        "forbidden_scope:\n"
        "  - secrets/**\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    monkeypatch.setattr(check_scope, "REPO_ROOT", tmp_path)
    return tmp_path


def test_changes_inside_approved_scope_pass(scoped_repo) -> None:
    (scoped_repo / "allowed.txt").write_text("changed\n", encoding="utf-8")

    assert check_scope.main() == 0


def test_changes_outside_approved_scope_fail(scoped_repo) -> None:
    (scoped_repo / "rogue.txt").write_text("x\n", encoding="utf-8")

    assert check_scope.main() == 1


def test_committed_rename_reports_both_sides(scoped_repo) -> None:
    _git(scoped_repo, "mv", "allowed.txt", "rogue.txt")
    _git(scoped_repo, "commit", "-qm", "rename")
    (scoped_repo / "CURRENT_TASK.yml").write_text(
        (scoped_repo / "CURRENT_TASK.yml")
        .read_text(encoding="utf-8")
        .replace("base_commit: null", "base_commit: HEAD~1"),
        encoding="utf-8",
    )

    assert check_scope.main() == 1


def test_forbidden_file_fails_even_when_committed_before_base(scoped_repo) -> None:
    secrets = scoped_repo / "secrets"
    secrets.mkdir()
    (secrets / "key.txt").write_text("k\n", encoding="utf-8")
    _git(scoped_repo, "add", "-A")
    _git(scoped_repo, "commit", "-qm", "add secret")

    assert check_scope.main() == 1


def test_invalid_base_commit_fails_closed(scoped_repo) -> None:
    (scoped_repo / "CURRENT_TASK.yml").write_text(
        (scoped_repo / "CURRENT_TASK.yml")
        .read_text(encoding="utf-8")
        .replace("base_commit: null", "base_commit: ffffffffffffffffffffffffffffffffffffffff"),
        encoding="utf-8",
    )

    assert check_scope.main() == 1


def test_invalid_task_mode_fails_closed(scoped_repo) -> None:
    (scoped_repo / "CURRENT_TASK.yml").write_text(
        (scoped_repo / "CURRENT_TASK.yml")
        .read_text(encoding="utf-8")
        .replace("task_mode: implementation", "task_mode: implementaton"),
        encoding="utf-8",
    )

    assert check_scope.main() == 1
