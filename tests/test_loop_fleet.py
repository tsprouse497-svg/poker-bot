from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import scripts.check_repo_consistency as consistency
import scripts.loop_fleet as loop_fleet
import scripts.loop_stage as loop_stage
import scripts.review_queue as review_queue

# --------------------------------------------------------------------------- #
# the dependency graph
# --------------------------------------------------------------------------- #


def test_a_cycle_is_named_rather_than_reported_as_waiting() -> None:
    broken = loop_fleet.unusable({"a": ["b"], "b": ["a"], "c": []})
    assert [reason for reason in broken if "cycle" in reason]


def test_a_dependency_on_a_phase_that_does_not_exist_is_rejected() -> None:
    broken = loop_fleet.unusable({"11": ["09"], "12": ["11"]})
    assert broken == ["11 depends on 09, which is not a phase"]


def test_a_chain_is_usable() -> None:
    assert loop_fleet.unusable({"a": [], "b": ["a"], "c": ["b"]}) == []


def test_a_diamond_is_usable() -> None:
    assert loop_fleet.unusable({"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}) == []


def test_the_committed_graph_is_usable() -> None:
    """The real contracts, whatever they currently declare."""
    phases = yaml.safe_load(
        (consistency.PHASE_STATUS).read_text(encoding="utf-8")
    )["phases"]
    assert loop_fleet.unusable(consistency.dependency_graph(phases)) == []


def test_consistency_and_the_driver_agree_on_what_a_cycle_is() -> None:
    graph = {"a": ["b"], "b": ["a"]}
    assert consistency.cyclic_phases(graph)
    assert loop_fleet.unusable(graph)


# --------------------------------------------------------------------------- #
# eligibility
# --------------------------------------------------------------------------- #

GRAPH = {"10": ["09"], "11": ["09"], "12": ["11"], "13": ["11"], "14": ["10", "12", "13"]}
STATUS = {"09": "completed", "10": "future", "11": "future", "12": "future", "13": "future"}


def phase(phase_id: str, status: str = "future") -> dict:
    return {"phase_id": phase_id, "status": status, "title": f"Phase {phase_id}"}


def test_a_phase_whose_dependencies_are_completed_may_start(monkeypatch) -> None:
    monkeypatch.setattr(loop_fleet, "policy", dict)
    assert loop_fleet.blockers(phase("11"), GRAPH, STATUS, set()) == []


def test_a_phase_waiting_on_an_unmerged_dependency_may_not_start(monkeypatch) -> None:
    monkeypatch.setattr(loop_fleet, "policy", dict)
    assert loop_fleet.blockers(phase("12"), GRAPH, STATUS, set()) == ["waits on 11"]


def test_a_join_names_every_dependency_it_is_still_waiting_on(monkeypatch) -> None:
    monkeypatch.setattr(loop_fleet, "policy", dict)
    assert loop_fleet.blockers(phase("14"), GRAPH, STATUS, set()) == ["waits on 10, 12, 13"]


def test_a_phase_already_running_may_not_start_twice(monkeypatch) -> None:
    monkeypatch.setattr(loop_fleet, "policy", dict)
    assert loop_fleet.blockers(phase("11"), GRAPH, STATUS, {"11"}) == ["already running"]


def test_a_phase_needing_human_data_may_not_start(monkeypatch) -> None:
    monkeypatch.setattr(loop_fleet, "policy", lambda: {"11": {"needs_human_data": True}})
    assert loop_fleet.blockers(phase("11"), GRAPH, STATUS, set()) == [
        "needs an input the repo does not have"
    ]


def test_siblings_are_both_eligible_once_their_shared_dependency_lands(monkeypatch) -> None:
    """The whole point of the fleet: 12 and 13 wait on 11 and on nothing else."""
    monkeypatch.setattr(loop_fleet, "policy", dict)
    monkeypatch.setattr(loop_fleet, "lanes", list)
    status = dict(STATUS, **{"11": "completed"})
    phases = [phase(p, status.get(p, "future")) for p in ("09", "10", "11", "12", "13", "14")]
    ready, held = loop_fleet.board(GRAPH, phases)
    assert ready == ["10", "12", "13"]
    assert held == {"14": ["waits on 10, 12, 13"]}


def test_completed_phases_are_left_off_the_board_entirely(monkeypatch) -> None:
    monkeypatch.setattr(loop_fleet, "policy", dict)
    monkeypatch.setattr(loop_fleet, "lanes", list)
    ready, held = loop_fleet.board({"09": []}, [phase("09", "completed")])
    assert (ready, held) == ([], {})


# --------------------------------------------------------------------------- #
# lanes and the worktree lock
# --------------------------------------------------------------------------- #


def test_the_lock_lives_in_a_directory_that_exists() -> None:
    """The bug this replaced: in a linked worktree `.git` is a file, not a directory,
    so a lock path built from REPO_ROOT could not be written at all."""
    assert loop_stage.lock_path().parent.is_dir()
    assert loop_stage.lock_path().name == loop_stage.LOCK_NAME


def test_the_lock_follows_the_worktree_git_dir(monkeypatch) -> None:
    monkeypatch.setattr(loop_stage, "git", lambda *args: "/repo/.git/worktrees/phase-11")
    assert loop_stage.lock_path() == Path("/repo/.git/worktrees/phase-11/poker-loop.lock")


def write_pointer(worktree: Path, phase_id: str, **fields) -> None:
    runs = worktree / "verification" / "loop_runs"
    runs.mkdir(parents=True, exist_ok=True)
    state = {"schema_version": 1, "phase_id": phase_id, "stage": 4, "loop": "running"}
    state.update(fields)
    (runs / f"{phase_id}.yml").write_text(yaml.safe_dump(state), encoding="utf-8")


def test_only_running_and_halted_pointers_are_lanes(monkeypatch, tmp_path) -> None:
    write_pointer(tmp_path, "11")
    write_pointer(tmp_path, "12", loop="halted", halt_reason="a blocker survived")
    write_pointer(tmp_path, "09", loop="completed")
    write_pointer(tmp_path, "08", loop="idle")
    monkeypatch.setattr(loop_fleet, "worktrees", lambda: [(tmp_path, "phase/11-x")])
    assert [(lane.phase_id, lane.loop) for lane in loop_fleet.lanes()] == [
        ("11", "running"),
        ("12", "halted"),
    ]


def test_a_lane_carries_its_stage_name() -> None:
    lane = loop_fleet.Lane("11", Path("/tmp"), "phase/11-x", 5, "running", "")
    assert lane.stage_name == "freeze"


# --------------------------------------------------------------------------- #
# per-lane state selection
# --------------------------------------------------------------------------- #


def test_a_named_phase_reads_its_own_pointer(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(loop_stage, "RUNS_DIR", tmp_path / "loop_runs")
    monkeypatch.setattr(loop_stage, "LEGACY_STATE_PATH", tmp_path / "loop_state.yml")
    assert loop_stage.state_path_for("11") == tmp_path / "loop_runs" / "11.yml"


def test_a_lane_started_before_per_lane_state_keeps_its_own_file(monkeypatch, tmp_path) -> None:
    """Migrating a live lane would move a file its own task never approved."""
    legacy = tmp_path / "loop_state.yml"
    legacy.write_text(yaml.safe_dump({"phase_id": "10", "loop": "running"}), encoding="utf-8")
    monkeypatch.setattr(loop_stage, "RUNS_DIR", tmp_path / "loop_runs")
    monkeypatch.setattr(loop_stage, "LEGACY_STATE_PATH", legacy)
    assert loop_stage.state_path_for("10") == legacy
    assert loop_stage.state_path_for("11") == tmp_path / "loop_runs" / "11.yml"


def test_several_lanes_refuse_to_be_guessed_at(monkeypatch, tmp_path) -> None:
    runs = tmp_path / "loop_runs"
    runs.mkdir()
    for phase_id in ("11", "12"):
        (runs / f"{phase_id}.yml").write_text("loop: running\n", encoding="utf-8")
    monkeypatch.setattr(loop_stage, "RUNS_DIR", runs)
    monkeypatch.setattr(loop_stage, "LEGACY_STATE_PATH", tmp_path / "loop_state.yml")
    with pytest.raises(ValueError, match="--phase"):
        loop_stage.state_path_for(None)


def test_one_lane_needs_no_naming(monkeypatch, tmp_path) -> None:
    runs = tmp_path / "loop_runs"
    runs.mkdir()
    (runs / "11.yml").write_text("loop: running\n", encoding="utf-8")
    monkeypatch.setattr(loop_stage, "RUNS_DIR", runs)
    monkeypatch.setattr(loop_stage, "LEGACY_STATE_PATH", tmp_path / "loop_state.yml")
    assert loop_stage.state_path_for(None) == runs / "11.yml"


# --------------------------------------------------------------------------- #
# the pause board
# --------------------------------------------------------------------------- #

STEM = "PHASE_11_ENGINE_FIDELITY"


def build_worktree(tmp_path: Path) -> Path:
    (tmp_path / "phase_status.yml").write_text(
        yaml.safe_dump(
            {"phases": [{"phase_id": "11", "status": "active", "contract": f"docs/{STEM}.md"}]}
        ),
        encoding="utf-8",
    )
    return tmp_path


def lane_for(worktree: Path, stage: int = 3, loop: str = "running") -> loop_fleet.Lane:
    return loop_fleet.Lane("11", worktree, "phase/11-x", stage, loop, "")


def test_an_unanswered_frozen_decision_reaches_the_board(tmp_path) -> None:
    worktree = build_worktree(tmp_path)
    decisions = worktree / "reports" / "phase_audits" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / f"{STEM}_DECISIONS.md").write_text(
        "## 1 Which rake basis\nReversibility: frozen-into-data\nAnswer:\n\n"
        "## 2 Report units\nReversibility: runtime-reversible\nAnswer:\n",
        encoding="utf-8",
    )
    asks = review_queue.entries([lane_for(worktree)])
    assert [(ask.kind, ask.question) for ask in asks] == [
        ("decision", "rule on: 1 Which rake basis")
    ]


def test_an_answered_frozen_decision_leaves_the_board(tmp_path) -> None:
    worktree = build_worktree(tmp_path)
    decisions = worktree / "reports" / "phase_audits" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / f"{STEM}_DECISIONS.md").write_text(
        "## 1 Which rake basis\nReversibility: frozen-into-data\nAnswer: rake-free\n",
        encoding="utf-8",
    )
    assert review_queue.entries([lane_for(worktree)]) == []


def test_an_open_blocker_reaches_the_board_and_a_resolved_one_does_not(tmp_path) -> None:
    worktree = build_worktree(tmp_path)
    reviews = worktree / "reports" / "phase_audits" / "reviews" / STEM
    reviews.mkdir(parents=True)
    (reviews / "stage-04-tests.md").write_text(
        "## Blocker\n- the all-in bound test asserts on rebuilt state\n"
        "- an earlier one [resolved]\n## Non-blocker\nNone.\n## Alignment\nNone.\n",
        encoding="utf-8",
    )
    asks = review_queue.entries([lane_for(worktree)])
    assert [ask.question for ask in asks] == ["the all-in bound test asserts on rebuilt state"]
    assert asks[0].answer_in.endswith("stage-04-tests.md")


def test_a_halted_lane_reports_the_reason_it_halted(tmp_path) -> None:
    worktree = build_worktree(tmp_path)
    lane = loop_fleet.Lane(
        "11", worktree, "phase/11-x", 6, "halted", "second failure on one command"
    )
    asks = review_queue.entries([lane])
    assert [(ask.kind, ask.question) for ask in asks] == [
        ("halted", "second failure on one command")
    ]


def test_a_phase_that_cannot_auto_advance_asks_for_sign_off_at_stage_eleven(tmp_path) -> None:
    worktree = build_worktree(tmp_path)
    (worktree / "verification").mkdir()
    (worktree / "verification" / "loop_policy.yml").write_text(
        yaml.safe_dump({"phases": {"11": {"auto_advance": False}}}), encoding="utf-8"
    )
    assert review_queue.entries([lane_for(worktree, stage=10)]) == []
    asks = review_queue.entries([lane_for(worktree, stage=11)])
    assert [ask.kind for ask in asks] == ["policy"]


def test_a_phase_that_may_auto_advance_asks_for_nothing(tmp_path) -> None:
    worktree = build_worktree(tmp_path)
    (worktree / "verification").mkdir()
    (worktree / "verification" / "loop_policy.yml").write_text(
        yaml.safe_dump({"phases": {"11": {"auto_advance": True}}}), encoding="utf-8"
    )
    assert review_queue.entries([lane_for(worktree, stage=11)]) == []


def test_a_declared_execplan_pause_reaches_the_board(tmp_path) -> None:
    worktree = build_worktree(tmp_path)
    plans = worktree / "docs" / "exec_plans" / "active"
    plans.mkdir(parents=True)
    (plans / f"{STEM}.md").write_text(
        "## Delegation Plan\n\n- Paused: waiting on the rake ruling\n", encoding="utf-8"
    )
    asks = review_queue.entries([lane_for(worktree)])
    assert [(ask.kind, ask.question) for ask in asks] == [
        ("paused", "waiting on the rake ruling")
    ]


def test_a_phase_gated_on_human_data_is_listed_before_it_can_start() -> None:
    asks = review_queue.gated_phases(
        [{"phase_id": "16", "status": "future"}],
        {"16": {"needs_human_data": True, "reason": "no postflop source exists"}},
    )
    assert [(ask.phase_id, ask.question) for ask in asks] == [("16", "no postflop source exists")]


def test_a_completed_phase_is_never_listed_as_gated() -> None:
    assert review_queue.gated_phases(
        [{"phase_id": "16", "status": "completed"}], {"16": {"needs_human_data": True}}
    ) == []


def test_an_empty_board_says_so_rather_than_printing_a_header() -> None:
    assert review_queue.render([]) == "nothing is waiting on you."


def test_a_branch_slug_never_ends_in_a_separator() -> None:
    assert loop_fleet.slug("Solver Extraction, And A Human Verdict On It").endswith("on")
    assert not loop_fleet.slug("Quality, Drift, Backlog, And Phase-Gate Hardening").endswith("-")


def test_lanes_are_siblings_of_the_repository_not_of_the_current_worktree() -> None:
    """Run from a lane, deriving this from REPO_ROOT would nest the next lane
    inside it, and a level deeper on every phase after that."""
    repo = loop_fleet.primary_worktree()
    root = loop_fleet.lane_root()
    assert root.parent == repo.parent
    assert root.name == f"{repo.name}-worktrees"
    assert repo not in root.parents and root != repo


def test_the_primary_worktree_is_found_from_the_shared_git_dir(monkeypatch) -> None:
    monkeypatch.setattr(loop_fleet, "git", lambda *args: "/Users/x/projects/poker-bot/.git")
    assert loop_fleet.primary_worktree() == Path("/Users/x/projects/poker-bot")
    assert loop_fleet.lane_root() == Path("/Users/x/projects/poker-bot-worktrees")
