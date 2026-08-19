"""Several phase loops at once, one lane per worktree.

`scripts/loop_stage.py` drives one phase. This drives the board: which phases may
start, which are running where, and which have stopped for a human. A lane is a
git worktree on its own `phase/NN-slug` branch, holding its own pointer under
`verification/loop_runs/`, so two lanes never write the same file and neither can
see the other's half-finished work.

Like the stage driver, this script is read-only. It computes and it instructs; the
session performs every action, so creating a worktree, seeding a task, merging a
branch and moving a tag all still pass through the normal permission path. That is
also what makes `--status` and `--tick` safe to run against live lanes: nothing
here can damage one.

Eligibility is measured against `main` rather than against the current worktree.
A dependency counts as met when it is `completed` on the integration branch, which
is the only place a phase is genuinely finished. Reading it from the local branch
would let a lane start against work that exists nowhere but a sibling's checkout.

Usage:
    loop_fleet.py --status         every lane: phase, worktree, stage, who is waiting
    loop_fleet.py --plan           which phases may start now, and what blocks the rest
    loop_fleet.py --start-lane 11  print the runbook that opens a lane
    loop_fleet.py --tick           ask every lane what it needs next
    loop_fleet.py --integrate 11   print the runbook that merges a finished lane
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import loop_stage  # noqa: E402
from check_repo_consistency import cyclic_phases  # noqa: E402

INTEGRATION_REF = "main"
LANE_ROOT = REPO_ROOT.parent / f"{REPO_ROOT.name}-worktrees"
FINISHED = "completed"


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd or REPO_ROOT, text=True, capture_output=True
    ).stdout.strip()


@cache
def show(ref_path: str) -> str:
    """A file as it stands on the integration branch.

    Cached because the graph and the policy are read once per phase while planning,
    and a `git show` per phase per question turns a board into dozens of processes.
    Nothing here writes, so the branch cannot move underneath a single run.
    """
    return git("show", f"{INTEGRATION_REF}:{ref_path}")


# --------------------------------------------------------------------------- #
# the graph
# --------------------------------------------------------------------------- #


def integrated_phases() -> list[dict]:
    text = show("phase_status.yml")
    if not text:
        raise ValueError(f"cannot read phase_status.yml on {INTEGRATION_REF}")
    return list(yaml.safe_load(text)["phases"])


def frontmatter(text: str) -> dict:
    return yaml.safe_load(text.split("---\n", 2)[1]) or {}


def dependencies(phases: list[dict]) -> dict[str, list[str]]:
    """`depends_on` for every phase, read off the integration branch.

    The contracts are the single source for the graph. Holding it anywhere else
    would give the loop a second opinion about the order, and the two would drift
    the first time a contract changed.
    """
    graph: dict[str, list[str]] = {}
    for phase in phases:
        phase_id = str(phase["phase_id"])
        meta = frontmatter(show(phase["contract"]))
        graph[phase_id] = [str(dep) for dep in (meta.get("depends_on") or [])]
    return graph


def unusable(graph: dict[str, list[str]]) -> list[str]:
    """Why this graph cannot be planned against, if it cannot.

    A cycle or a typo both surface as a fleet that reports nothing eligible and
    explains it as unmet dependencies, which is exactly what ordinary waiting looks
    like. Saying which it is turns a mystery back into a bug. `check_repo_consistency`
    enforces the same two rules in the gate; this is the same function, so the
    driver and the gate cannot disagree about what a usable graph is.
    """
    known = set(graph)
    broken = [
        f"{node} depends on {dep}, which is not a phase"
        for node, deps in graph.items()
        for dep in deps
        if dep not in known
    ]
    broken += [f"{node} is on a cycle" for node in sorted(cyclic_phases(graph))]
    return sorted(broken)


# --------------------------------------------------------------------------- #
# the lanes
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Lane:
    phase_id: str
    worktree: Path
    branch: str
    stage: int
    loop: str
    halt_reason: str

    @property
    def stage_name(self) -> str:
        try:
            return loop_stage.stage_by_number(self.stage).name
        except ValueError:
            return "?"

    @property
    def is_here(self) -> bool:
        return self.worktree == REPO_ROOT


def worktrees() -> list[tuple[Path, str]]:
    entries: list[tuple[Path, str]] = []
    path = ""
    for line in git("worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line.removeprefix("worktree ").strip()
        elif line.startswith("branch "):
            branch = line.removeprefix("branch ").strip().removeprefix("refs/heads/")
            entries.append((Path(path), branch))
        elif line.startswith("detached"):
            entries.append((Path(path), "(detached)"))
    return entries


def pointers(worktree: Path) -> list[Path]:
    """Every lane pointer in a worktree, in both layouts the loop has used."""
    runs = worktree / "verification" / "loop_runs"
    found = sorted(runs.glob("*.yml")) if runs.is_dir() else []
    legacy = worktree / "verification" / "loop_state.yml"
    if legacy.is_file():
        found.append(legacy)
    return found


LIVE_LOOPS = {"running", "halted"}


def lanes() -> list[Lane]:
    """Every loop this repo is currently running, across every worktree.

    Only `running` and `halted` count. A pointer left at `idle` or `completed` is
    the record that a phase once ran in that worktree, not a claim that one runs
    there now, and counting it would make a finished phase look like it was
    occupying a lane forever.
    """
    found: dict[tuple[str, Path], Lane] = {}
    for worktree, branch in worktrees():
        # Newest layout first, so a worktree carrying both a per-lane pointer and
        # the single-lane file it was migrated from reports one lane, not two.
        for pointer in pointers(worktree):
            state = yaml.safe_load(pointer.read_text(encoding="utf-8")) or {}
            if state.get("loop") not in LIVE_LOOPS or not state.get("phase_id"):
                continue
            key = (str(state["phase_id"]), worktree)
            found.setdefault(
                key,
                Lane(
                    phase_id=str(state["phase_id"]),
                    worktree=worktree,
                    branch=branch,
                    stage=int(state.get("stage", 0)),
                    loop=str(state.get("loop")),
                    halt_reason=str(state.get("halt_reason") or ""),
                ),
            )
    return sorted(found.values(), key=lambda lane: lane.phase_id)


# --------------------------------------------------------------------------- #
# eligibility
# --------------------------------------------------------------------------- #


def policy() -> dict:
    return yaml.safe_load(show("verification/loop_policy.yml")).get("phases") or {}


def blockers(
    phase: dict, graph: dict[str, list[str]], status: dict[str, str], running: set[str]
) -> list[str]:
    phase_id = str(phase["phase_id"])
    reasons = []
    if status.get(phase_id) == FINISHED:
        reasons.append("already completed")
    if phase_id in running:
        reasons.append("already running")
    unmet = [dep for dep in graph.get(phase_id, []) if status.get(dep) != FINISHED]
    if unmet:
        reasons.append(f"waits on {', '.join(unmet)}")
    if (policy().get(phase_id) or {}).get("needs_human_data"):
        reasons.append("needs an input the repo does not have")
    return reasons


def board(
    graph: dict[str, list[str]], phases: list[dict]
) -> tuple[list[str], dict[str, list[str]]]:
    """Which phases may start, and why the rest may not.

    Finished phases are left out of both lists rather than reported as held. Ten
    completed entries repeating "already completed" would bury the two lines that
    say something.
    """
    status = {str(p["phase_id"]): str(p["status"]) for p in phases}
    running = {lane.phase_id for lane in lanes()}
    ready, held = [], {}
    for phase in phases:
        phase_id = str(phase["phase_id"])
        if status.get(phase_id) == FINISHED:
            continue
        reasons = blockers(phase, graph, status, running)
        if reasons:
            held[phase_id] = reasons
        else:
            ready.append(phase_id)
    return ready, held


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #


def waiting_on_human(live: list[Lane]) -> dict[str, list[str]]:
    """One line per lane that has stopped for Taylor, from the pause board."""
    import review_queue

    grouped: dict[str, list[str]] = {}
    for entry in review_queue.entries(live):
        grouped.setdefault(entry.phase_id, []).append(entry.question)
    return grouped


def print_status() -> None:
    live = lanes()
    if not live:
        print("no lanes running")
        return
    asks = waiting_on_human(live)
    print(f"{len(live)} lane(s)")
    for lane in live:
        here = "  <- this worktree" if lane.is_here else ""
        print()
        print(
            f"phase {lane.phase_id}  ·  stage {lane.stage}/11 {lane.stage_name}"
            f"  ·  {lane.loop}{here}"
        )
        print(f"  branch    {lane.branch}")
        print(f"  worktree  {lane.worktree}")
        if lane.halt_reason:
            print(f"  halted    {lane.halt_reason}")
        for question in asks.get(lane.phase_id, []):
            print(f"  waiting   {question}")
    if asks:
        print()
        print("full pause board: uv run python scripts/review_queue.py --list")


def print_plan(graph: dict[str, list[str]], phases: list[dict]) -> None:
    ready, held = board(graph, phases)
    print(f"integration ref: {INTEGRATION_REF}")
    print()
    if ready:
        print("may start now:")
        for phase_id in ready:
            print(f"  {phase_id}  ->  uv run python scripts/loop_fleet.py --start-lane {phase_id}")
    else:
        print("nothing may start now")
    print()
    print("held:")
    for phase_id, reasons in held.items():
        print(f"  {phase_id}  {'; '.join(reasons)}")


def slug(title: str) -> str:
    """A branch-safe name from a phase title, matching the existing `phase/NN-slug`."""
    keep = [c.lower() if c.isalnum() else "-" for c in title]
    return "-".join(part for part in "".join(keep).split("-") if part)[:40].rstrip("-")


def print_start_lane(phase_id: str, graph: dict[str, list[str]], phases: list[dict]) -> int:
    match = [p for p in phases if str(p["phase_id"]) == phase_id]
    if not match:
        print(f"phase {phase_id} is not in phase_status.yml", file=sys.stderr)
        return 1
    phase = match[0]
    status = {str(p["phase_id"]): str(p["status"]) for p in phases}
    reasons = blockers(phase, graph, status, {lane.phase_id for lane in lanes()})
    if reasons:
        print(f"phase {phase_id} cannot start: {'; '.join(reasons)}", file=sys.stderr)
        return 1
    branch = f"phase/{phase_id}-{slug(str(phase['title']))}"
    tree = LANE_ROOT / f"phase-{phase_id}"
    print(f"lane runbook for phase {phase_id} - {phase['title']}")
    print()
    print(f"  git worktree add {tree} -b {branch} {INTEGRATION_REF}")
    print(f"  cd {tree}")
    print(f"  touch \"$(git rev-parse --absolute-git-dir)/{loop_stage.LOCK_NAME}\"")
    print()
    print("then, in that worktree:")
    print(f"  - set phase {phase_id} to active in phase_status.yml, and only that phase")
    print(f"  - set CURRENT_TASK.yml: task_id, active_phase {phase_id},")
    print("    task_mode contract-update, base_commit to the new HEAD, a narrow approved_scope")
    print(f"  - uv run python scripts/loop_stage.py --start {phase_id}")
    print()
    print("the lane then runs its own eleven stages; come back here with --status.")
    return 0


def print_tick() -> None:
    live = lanes()
    if not live:
        print("no lanes running")
        return
    for lane in live:
        print(f"=== phase {lane.phase_id}  ·  {lane.worktree} ===")
        # The lane runs its own branch's driver, which may predate `--phase`. One
        # pointer is unambiguous without it, and a worktree holding several
        # necessarily runs a driver that has it, because per-lane state and the
        # flag shipped together.
        select = ["--phase", lane.phase_id] if len(pointers(lane.worktree)) > 1 else []
        proc = subprocess.run(
            [sys.executable, "scripts/loop_stage.py", *select],
            cwd=lane.worktree,
            text=True,
            capture_output=True,
        )
        print((proc.stdout + proc.stderr).rstrip() or "(no output)")
        print()


def print_integrate(phase_id: str) -> int:
    live = [lane for lane in lanes() if lane.phase_id == phase_id]
    if not live:
        print(f"no lane is running phase {phase_id}", file=sys.stderr)
        return 1
    lane = live[0]
    others = [other.phase_id for other in lanes() if other.phase_id != phase_id]
    print(f"integration runbook for phase {phase_id} ({lane.branch})")
    print()
    print("Integration is serial. Lanes collide on freeze.lock, mutations.yml,")
    print("phase_status.yml, backlog.yml and the generated documents, so one lane")
    print("merges at a time and the rest rebase onto the result.")
    print()
    print(f"  git -C {REPO_ROOT} checkout {INTEGRATION_REF}")
    print(f"  git -C {REPO_ROOT} merge --no-ff {lane.branch}")
    print("  uv run python scripts/freeze_tests.py          # the lock is rewritten by the")
    print("                                                 # integrator, never by a builder")
    print("  uv run python scripts/generate_status.py")
    print("  uv run python scripts/generate_phase_ledger.py")
    print("  uv run python scripts/generate_backlog.py")
    print("  uv run python scripts/run_verify.py")
    print(f"  git -C {REPO_ROOT} tag phase-{phase_id}-complete")
    print()
    if others:
        print(f"then rebase the remaining lane(s) {', '.join(others)} onto {INTEGRATION_REF}")
        print("and re-run their gate. A lane that goes red after a sibling merges goes")
        print("back to stage 6; it is not fixed from here.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="every lane and its stage")
    parser.add_argument("--plan", action="store_true", help="which phases may start now")
    parser.add_argument("--start-lane", metavar="PHASE_ID", help="print the runbook to open a lane")
    parser.add_argument("--tick", action="store_true", help="ask every lane what it needs next")
    parser.add_argument("--integrate", metavar="PHASE_ID", help="print the merge-back runbook")
    args = parser.parse_args()

    phases = integrated_phases()
    graph = dependencies(phases)
    broken = unusable(graph)
    if broken:
        print("depends_on is not a usable graph:", file=sys.stderr)
        for reason in broken:
            print(f"  - {reason}", file=sys.stderr)
        return 1

    if args.start_lane:
        return print_start_lane(args.start_lane, graph, phases)
    if args.integrate:
        return print_integrate(args.integrate)
    if args.tick:
        print_tick()
        return 0
    if args.plan:
        print_plan(graph, phases)
        return 0
    print_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
