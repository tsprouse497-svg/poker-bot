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


def _git(repo, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _task_yaml(base_commit: str, approved: str = "  - allowed.txt\n", log: str = "") -> str:
    return (
        "task_id: T\n"
        "task_mode: implementation\n"
        f"base_commit: {base_commit}\n"
        "approved_scope:\n"
        f"{approved}"
        "standing_scope:\n"
        "  - CURRENT_TASK.yml\n"
        "forbidden_scope:\n"
        "  - secrets/**\n"
        f"{log}"
    )


def _write_task(repo, **kwargs) -> None:
    (repo / "CURRENT_TASK.yml").write_text(_task_yaml(**kwargs), encoding="utf-8")


@pytest.fixture
def scoped_repo(tmp_path, monkeypatch):
    """A repo whose task is activated the way the rules now require.

    The base revision carries a placeholder `base_commit`, then the working tree
    names the real sha of that commit. That is the shape of a genuine activation:
    a task points at the commit it started from.
    """
    _git(tmp_path, "init", "-q")
    (tmp_path / "allowed.txt").write_text("a\n", encoding="utf-8")
    _write_task(tmp_path, base_commit="null")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    sha = _git(tmp_path, "rev-parse", "HEAD")
    _write_task(tmp_path, base_commit=sha)
    monkeypatch.setattr(check_scope, "REPO_ROOT", tmp_path)
    return tmp_path


def test_changes_inside_approved_scope_pass(scoped_repo) -> None:
    (scoped_repo / "allowed.txt").write_text("changed\n", encoding="utf-8")

    assert check_scope.main() == 0


def test_changes_outside_approved_scope_fail(scoped_repo) -> None:
    (scoped_repo / "rogue.txt").write_text("x\n", encoding="utf-8")

    assert check_scope.main() == 1


def test_committed_rename_reports_both_sides(scoped_repo) -> None:
    _git(scoped_repo, "add", "-A")
    _git(scoped_repo, "commit", "-qm", "point at base")
    _git(scoped_repo, "mv", "allowed.txt", "rogue.txt")
    _git(scoped_repo, "commit", "-qm", "rename")

    assert check_scope.main() == 1


def test_forbidden_file_fails_even_when_committed_before_base(scoped_repo) -> None:
    secrets = scoped_repo / "secrets"
    secrets.mkdir()
    (secrets / "key.txt").write_text("k\n", encoding="utf-8")
    _git(scoped_repo, "add", "-A")
    _git(scoped_repo, "commit", "-qm", "add secret")

    assert check_scope.main() == 1


def test_invalid_base_commit_fails_closed(scoped_repo) -> None:
    _write_task(scoped_repo, base_commit="f" * 40)

    assert check_scope.main() == 1


def test_invalid_task_mode_fails_closed(scoped_repo) -> None:
    (scoped_repo / "CURRENT_TASK.yml").write_text(
        _task_yaml(base_commit=_git(scoped_repo, "rev-parse", "HEAD")).replace(
            "task_mode: implementation", "task_mode: implementaton"
        ),
        encoding="utf-8",
    )

    assert check_scope.main() == 1


def test_base_commit_must_be_a_real_sha_while_working(scoped_repo) -> None:
    """`HEAD` or null makes the diff empty for anything already committed."""
    _write_task(scoped_repo, base_commit="HEAD")

    assert check_scope.main() == 1


def test_overbroad_scope_pattern_fails(scoped_repo) -> None:
    _write_task(
        scoped_repo,
        base_commit=_git(scoped_repo, "rev-parse", "HEAD"),
        approved="  - '*'\n",
    )

    assert check_scope.main() == 1


def test_self_widened_scope_without_a_logged_reason_fails(scoped_repo) -> None:
    _write_task(
        scoped_repo,
        base_commit=_git(scoped_repo, "rev-parse", "HEAD"),
        approved="  - allowed.txt\n  - rogue.txt\n",
    )
    (scoped_repo / "rogue.txt").write_text("x\n", encoding="utf-8")

    assert check_scope.main() == 1


def test_self_widened_scope_with_a_logged_reason_passes(scoped_repo) -> None:
    _write_task(
        scoped_repo,
        base_commit=_git(scoped_repo, "rev-parse", "HEAD"),
        approved="  - allowed.txt\n  - rogue.txt\n",
        log="scope_change_log:\n  - date: 2026-08-11\n    reason: rogue.txt is genuinely needed.\n",
    )
    (scoped_repo / "rogue.txt").write_text("x\n", encoding="utf-8")

    assert check_scope.main() == 0


def test_unforbidding_a_path_without_a_logged_reason_fails(scoped_repo) -> None:
    (scoped_repo / "CURRENT_TASK.yml").write_text(
        _task_yaml(base_commit=_git(scoped_repo, "rev-parse", "HEAD")).replace(
            "forbidden_scope:\n  - secrets/**\n", "forbidden_scope: []\n"
        ),
        encoding="utf-8",
    )

    assert check_scope.main() == 1
