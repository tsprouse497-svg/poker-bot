"""Everything across the fleet that is waiting on a human, in one place.

The queue is derived, never recorded. A second file listing the open questions
would be a second source of truth about them, and it would go stale the moment
someone answered one in the file that actually governs it. So this reads the six
places a human ask already lives and renders them; answering happens in the real
file and the entry disappears because the next run re-derives.

    decision list      an unanswered `frozen-into-data` judgment call
    review notes       an open `## Blocker` bullet at any stage
    loop policy        `auto_advance: false`, reached at stage 11
    loop policy        `needs_human_data: true`, before the phase can start
    active ExecPlan    a declared `- Paused:` reason
    lane pointer       `loop: halted`, with the reason recorded at the halt

Nothing here is committed. The board depends on which worktrees exist on this
machine, so a checked-in copy would differ between machines and could never be
verified by the gate. Its shape is covered by tests instead.

Usage:
    review_queue.py --list    print the board
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import loop_stage  # noqa: E402
from check_execplan_delegation import pause_declaration  # noqa: E402

AUTO_ADVANCE_STAGE = 11


@dataclass(frozen=True)
class Ask:
    phase_id: str
    kind: str
    question: str
    answer_in: str
    blocks: str


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def contract_stem(worktree: Path, phase_id: str) -> str | None:
    """The contract filename a phase's decision list and reviews are named for."""
    status = worktree / "phase_status.yml"
    if not status.is_file():
        return None
    for phase in load(status).get("phases") or []:
        if str(phase["phase_id"]) == phase_id:
            return Path(str(phase["contract"])).stem
    return None


def frozen_asks(worktree: Path, phase_id: str, stem: str) -> list[Ask]:
    path = worktree / "reports" / "phase_audits" / "decisions" / f"{stem}_DECISIONS.md"
    if not path.is_file():
        return []
    relative = path.relative_to(worktree)
    return [
        Ask(
            phase_id=phase_id,
            kind="decision",
            question=f"rule on: {heading}",
            answer_in=str(relative),
            blocks="stage 3; the answer is written into committed data",
        )
        for heading in loop_stage.unanswered_frozen(path.read_text(encoding="utf-8"))
    ]


def blocker_asks(worktree: Path, phase_id: str, stem: str) -> list[Ask]:
    directory = worktree / "reports" / "phase_audits" / "reviews" / stem
    if not directory.is_dir():
        return []
    found = []
    for note in sorted(directory.glob("stage-*.md")):
        for item in loop_stage.unresolved_blockers(note.read_text(encoding="utf-8")):
            found.append(
                Ask(
                    phase_id=phase_id,
                    kind="blocker",
                    question=item,
                    answer_in=str(note.relative_to(worktree)),
                    blocks=f"{note.stem}; mark it [resolved] once it is fixed",
                )
            )
    return found


def policy_asks(worktree: Path, phase_id: str, stage: int) -> list[Ask]:
    path = worktree / "verification" / "loop_policy.yml"
    if not path.is_file() or stage < AUTO_ADVANCE_STAGE:
        return []
    entry = (load(path).get("phases") or {}).get(phase_id) or {}
    if entry.get("auto_advance"):
        return []
    return [
        Ask(
            phase_id=phase_id,
            kind="policy",
            question=f"sign off before the fleet moves past phase {phase_id}",
            answer_in="verification/loop_policy.yml (the reason it cannot auto-advance)",
            blocks="stage 11; this phase writes committed data",
        )
    ]


def pause_asks(worktree: Path, phase_id: str, stem: str) -> list[Ask]:
    path = worktree / "docs" / "exec_plans" / "active" / f"{stem}.md"
    if not path.is_file():
        return []
    reason = pause_declaration(path.read_text(encoding="utf-8"))
    if not reason:
        return []
    return [
        Ask(
            phase_id=phase_id,
            kind="paused",
            question=reason,
            answer_in=str(path.relative_to(worktree)),
            blocks="the ExecPlan declares itself idle until this is settled",
        )
    ]


def entries(lanes) -> list[Ask]:
    """Every ask the running lanes are stopped on."""
    found: list[Ask] = []
    for lane in lanes:
        stem = contract_stem(lane.worktree, lane.phase_id)
        if lane.loop == "halted":
            found.append(
                Ask(
                    phase_id=lane.phase_id,
                    kind="halted",
                    question=lane.halt_reason or "halted without a recorded reason",
                    answer_in=f"resume with loop_stage.py --phase {lane.phase_id} --resume",
                    blocks=f"stage {lane.stage}",
                )
            )
        if not stem:
            continue
        found.extend(frozen_asks(lane.worktree, lane.phase_id, stem))
        found.extend(blocker_asks(lane.worktree, lane.phase_id, stem))
        found.extend(policy_asks(lane.worktree, lane.phase_id, lane.stage))
        found.extend(pause_asks(lane.worktree, lane.phase_id, stem))
    return found


def gated_phases(phases: list[dict], policy: dict) -> list[Ask]:
    """Phases that cannot start at all until a human supplies something."""
    return [
        Ask(
            phase_id=str(phase["phase_id"]),
            kind="input",
            question=str((policy.get(str(phase["phase_id"])) or {}).get("reason", "")).strip(),
            answer_in="verification/loop_policy.yml, once the input exists",
            blocks="the phase cannot start; a session must not invent the input",
        )
        for phase in phases
        if str(phase["status"]) != "completed"
        and (policy.get(str(phase["phase_id"])) or {}).get("needs_human_data")
    ]


def render(asks: list[Ask]) -> str:
    if not asks:
        return "nothing is waiting on you."
    lines = [f"{len(asks)} item(s) waiting on you", ""]
    for ask in asks:
        lines.append(f"phase {ask.phase_id}  ·  {ask.kind}")
        lines.append(f"  {ask.question}")
        lines.append(f"  answer in  {ask.answer_in}")
        lines.append(f"  blocks     {ask.blocks}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="print the board")
    parser.parse_args()

    import loop_fleet

    phases = loop_fleet.integrated_phases()
    asks = entries(loop_fleet.lanes()) + gated_phases(phases, loop_fleet.policy())
    print(render(asks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
