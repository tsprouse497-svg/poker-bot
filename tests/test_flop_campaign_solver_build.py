"""Phase 21: the solver build a solve record names is the binary that ran.

Decision 17 put two GTOpen trees side by side - the pin's, which carries the last aggressor through
a checked-through street, and the clone's, which clears it - and the contract requires every solve
record to carry the solver build, so a cell solved on the pin's tree can never pass for one solved
on the clone's. `tests/test_flop_campaign_threads.py` pins what a record carries and what
`read_solver_build` reads, through an injected git. This file pins the part an injected git cannot:
that the binary is the commit the record names.

**git is used for real here, in a repository under `tmp_path`.** git is a hard external boundary,
and the defect the review found lives in how a real checkout leaves files behind: a binary built
on a later commit, then `git checkout` of an earlier commit, leaves a clean tree whose HEAD is
older than the binary - every check on git's own answers passes, and the binary is not that
commit. Only file times can see it. So the repository is real, the times are set with `os.utime`,
and the commit times with git's own date variables, so no test depends on how fast it runs.

The interface, in `solver_artifacts.postflop_machine`:

- `check_binary_is_current(binary, run_git=None)` refuses, with `ValueError` or
  `transport.SolveDriverError`, a binary that is missing, one whose modification time is older
  than HEAD's commit time, and one older than any file git tracks under `crates/` or `Cargo.lock`.
- `solver_build_for(binary, run_git=None)` runs that check, then `read_solver_build`.
- `recorded_repository(repository, home=None)` names the clone home-relative (`~/...`) when it sits
  under the home folder, and as given otherwise.

The export's own check, `check_strats_file` in `scripts/solve_postflop_sample.py`, is here too:
it is the other place a solve's output is tied to what the server says it wrote.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from poker_training_bot.solver_artifacts import postflop_machine as machine
from poker_training_bot.solver_artifacts import postflop_transport as transport

REFUSED = (ValueError, transport.SolveDriverError)
BRANCH = "poker-bot/check-through-clears-initiative"
NOW = int(time.time())
LONG_AGO = NOW - 100_000
"""Every source file's time unless a test moves it: older than every commit and every binary."""


def owed(name: str):
    found = getattr(machine, name, None)
    assert found is not None, (
        f"{machine.__name__} must publish {name}; phase 21's contract requires every solve record"
        " to carry the solver build, and no implementation has been written yet"
    )
    return found


@pytest.fixture(autouse=True)
def plain_git(monkeypatch, tmp_path):
    """git with no user or system configuration, so a hook or a setting on this machine cannot
    change what the tests see."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "no-global-gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def git(repo: Path, *args: str, at: int | None = None) -> str:
    env = dict(os.environ)
    if at is not None:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"@{at} +0000"
    completed = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.invalid"]
        + list(args),
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return completed.stdout


def age(path: Path, at: int) -> None:
    os.utime(path, (at, at))


def tracked_sources(repo: Path) -> list[Path]:
    return [repo / "crates" / "solver" / "src" / "x.rs", repo / "Cargo.lock"]


def make_clone(tmp_path: Path, *, committed_at: int) -> tuple[Path, Path]:
    """A clone the way the solve path sees one: sources under `crates/`, a `Cargo.lock`, and the
    server binary under the ignored `target/`. One commit, on a branch; every source dated long
    ago. Returns the repository and the binary, which a test then dates."""
    repo = tmp_path / "gtopen-poker-bot"
    (repo / "crates" / "solver" / "src").mkdir(parents=True)
    (repo / "crates" / "solver" / "src" / "x.rs").write_text("fn tree() {}\n", encoding="utf-8")
    (repo / "Cargo.lock").write_text("# lock\n", encoding="utf-8")
    (repo / ".gitignore").write_text("target/\n", encoding="utf-8")
    git(repo, "init", "-q", "-b", BRANCH)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "first", at=committed_at)
    binary = repo / "target" / "release" / "gto-server"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"\x7fELF not really\n")
    for source in tracked_sources(repo):
        age(source, LONG_AGO)
    return repo, binary


@pytest.fixture
def fresh(tmp_path):
    """Committed 1,000 seconds ago, built 500 seconds ago: the build is newer than the commit
    and than every tracked source."""
    repo, binary = make_clone(tmp_path, committed_at=NOW - 1_000)
    age(binary, NOW - 500)
    return repo, binary


class TestABinaryIsTheCommitItNames:
    def test_a_build_after_the_last_commit_passes_and_names_the_branch_and_commit(
        self, fresh
    ) -> None:
        repo, binary = fresh

        owed("check_binary_is_current")(binary)
        build = owed("solver_build_for")(binary)

        assert build["branch"] == BRANCH
        assert build["commit"] == git(repo, "rev-parse", "HEAD").strip()
        assert len(build["commit"]) == 40

    def test_a_missing_binary_is_refused(self, fresh) -> None:
        _, binary = fresh
        binary.unlink()

        with pytest.raises(REFUSED):
            owed("check_binary_is_current")(binary)
        with pytest.raises(REFUSED):
            owed("solver_build_for")(binary)

    def test_a_binary_older_than_the_commit_is_refused(self, tmp_path) -> None:
        """Built 1,000 seconds ago, committed 100 seconds ago: the tree is clean and the binary
        predates what it would name."""
        _, binary = make_clone(tmp_path, committed_at=NOW - 100)
        age(binary, NOW - 1_000)

        with pytest.raises(REFUSED):
            owed("check_binary_is_current")(binary)
        with pytest.raises(REFUSED):
            owed("solver_build_for")(binary)

    def test_a_checkout_of_an_earlier_commit_after_the_build_is_refused(self, tmp_path) -> None:
        """The review's case. The binary is built on the second commit; then the first commit,
        whose `x.rs` differs, is checked out on a branch. HEAD is older than the binary and the
        tree is clean and on a branch, so only the checked-out source's time can show the binary
        is not HEAD."""
        repo, binary = make_clone(tmp_path, committed_at=NOW - 2_000)
        first = git(repo, "rev-parse", "HEAD").strip()
        (repo / "crates" / "solver" / "src" / "x.rs").write_text(
            "fn tree() { clear_initiative(); }\n", encoding="utf-8"
        )
        git(repo, "commit", "-q", "-am", "second", at=NOW - 1_500)
        for source in tracked_sources(repo):
            age(source, LONG_AGO)
        age(binary, NOW - 1_000)
        owed("check_binary_is_current")(binary)

        git(repo, "checkout", "-q", "-b", "older", first)

        assert git(repo, "status", "--porcelain", "--untracked-files=no") == ""
        with pytest.raises(REFUSED):
            owed("check_binary_is_current")(binary)
        with pytest.raises(REFUSED):
            owed("solver_build_for")(binary)

    def test_an_untouched_lock_passes_and_a_touched_one_is_refused(self, fresh) -> None:
        """Only the time moves, so git still calls the tree clean: the refusal is the time
        check's and nothing else's."""
        repo, binary = fresh
        owed("check_binary_is_current")(binary)

        age(repo / "Cargo.lock", NOW - 100)

        assert git(repo, "status", "--porcelain", "--untracked-files=no") == ""
        with pytest.raises(REFUSED):
            owed("check_binary_is_current")(binary)

    def test_a_touched_tracked_source_is_refused(self, fresh) -> None:
        repo, binary = fresh

        age(repo / "crates" / "solver" / "src" / "x.rs", NOW - 100)

        with pytest.raises(REFUSED):
            owed("check_binary_is_current")(binary)

    def test_an_ignored_file_newer_than_the_binary_does_not_refuse(self, fresh) -> None:
        """`target/` holds every build product, all newer than the sources; only what git
        tracks under `crates/` and `Cargo.lock` is compared."""
        repo, binary = fresh
        other = repo / "target" / "release" / "deps.d"
        other.write_text("built\n", encoding="utf-8")
        age(other, NOW)

        owed("check_binary_is_current")(binary)


class TestTheCloneMustBeOnABranchAndClean:
    def test_a_dirty_tracked_file_is_refused(self, fresh) -> None:
        """Dated long ago, so the time check passes and only the clean-tree check can refuse."""
        repo, binary = fresh
        source = repo / "crates" / "solver" / "src" / "x.rs"
        source.write_text("fn tree() { uncommitted(); }\n", encoding="utf-8")
        age(source, LONG_AGO)

        owed("check_binary_is_current")(binary)
        with pytest.raises(REFUSED):
            owed("read_solver_build")(repo)
        with pytest.raises(REFUSED):
            owed("solver_build_for")(binary)

    def test_a_detached_head_is_refused(self, fresh) -> None:
        repo, binary = fresh
        git(repo, "checkout", "-q", "--detach")

        owed("check_binary_is_current")(binary)
        with pytest.raises(REFUSED):
            owed("solver_build_for")(binary)


class TestTheRepositoryIsRecordedWithoutAUsername:
    def test_a_clone_under_home_is_recorded_home_relative(self, tmp_path) -> None:
        home = tmp_path / "home"
        clone = home / "projects" / "gtopen-poker-bot"

        assert owed("recorded_repository")(clone, home=home) == "~/projects/gtopen-poker-bot"

    def test_a_clone_elsewhere_is_recorded_as_given(self, tmp_path) -> None:
        home = tmp_path / "home"
        clone = tmp_path / "elsewhere" / "gtopen-poker-bot"

        assert owed("recorded_repository")(clone, home=home) == str(clone)

    def test_a_build_names_the_clone_the_binary_sits_in(self, fresh) -> None:
        repo, binary = fresh

        recorded = owed("solver_build_for")(binary)["repository"]

        assert Path(recorded).expanduser().resolve() == repo.resolve()


# --------------------------------------------------------------------------- #
# The export is the file the server says it wrote
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def sample():
    import scripts.solve_postflop_sample as module

    return module


def export_file(sample, path: Path, records: int, body: bytes = b"rows") -> dict[str, int]:
    """A bulk export as the clone writes it: magic, rows, trailer and a little-endian record
    count; returned with the summary a truthful route would answer."""
    path.write_bytes(
        sample.STRATS_MAGIC + body + sample.STRATS_TRAILER + records.to_bytes(8, "little")
    )
    return {"bytes": path.stat().st_size, "records": records}


class TestTheExportIsCheckedBeforeItIsKept:
    def test_an_export_that_matches_its_summary_passes(self, sample, tmp_path) -> None:
        path = tmp_path / "x.strats"
        summary = export_file(sample, path, 14)

        assert sample.check_strats_file(path, summary) == summary["bytes"]

    @pytest.mark.parametrize(
        ("why", "change"),
        [
            ("a size the route did not report", {"bytes": 1}),
            ("a record count the trailer does not hold", {"records": 15}),
        ],
    )
    def test_an_export_that_disagrees_with_its_summary_is_refused(
        self, sample, tmp_path, why, change
    ) -> None:
        path = tmp_path / "x.strats"
        summary = export_file(sample, path, 14) | change

        with pytest.raises(REFUSED):
            sample.check_strats_file(path, summary)

    def test_an_export_cut_short_is_refused(self, sample, tmp_path) -> None:
        path = tmp_path / "x.strats"
        summary = export_file(sample, path, 14)
        path.write_bytes(path.read_bytes()[:-12] + b"\0" * 12)

        with pytest.raises(REFUSED):
            sample.check_strats_file(path, summary)
