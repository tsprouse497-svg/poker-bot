"""The loop's state machine.

Holding the loop's state in a script rather than in a prompt buys three things a
long instruction cannot. A fresh session resumes at the same stage, because this
script's output is the only source of truth about what comes next. Stage order
cannot be skipped, because advancing runs a check rather than accepting a model's
opinion that it is done. And a crash costs one stage instead of a phase.

The driver deliberately does not touch the repo apart from
`verification/loop_state.yml`. It instructs and it verifies; the session performs
the actions, so every destructive step still passes through the normal permission
path. `--advance` refuses to move the pointer while its stage's check is failing.

Usage:
    loop_stage.py                 show the current stage and what to do
    loop_stage.py --start 06      begin the loop for a phase
    loop_stage.py --advance       verify this stage is done and move on
    loop_stage.py --halt "reason" record a halt and stop
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_contracts import (  # noqa: E402
    BOILERPLATE_CRITERIA,
    MIN_SPECIFIC_CRITERIA,
    section_bullets,
)
from run_verify import COMMANDS  # noqa: E402

STATE_PATH = REPO_ROOT / "verification" / "loop_state.yml"
POLICY_PATH = REPO_ROOT / "verification" / "loop_policy.yml"
TASK_PATH = REPO_ROOT / "CURRENT_TASK.yml"
PHASE_STATUS_PATH = REPO_ROOT / "phase_status.yml"
ACTIVE_PLANS = REPO_ROOT / "docs" / "exec_plans" / "active"
COMPLETED_PLANS = REPO_ROOT / "docs" / "exec_plans" / "completed"
LOCK_PATH = REPO_ROOT / ".git" / "poker-loop.lock"
SCHEMA_VERSION = 1


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True
    ).stdout.strip()


def tree_is_clean() -> bool:
    return git("status", "--porcelain") == ""


def run_command(command_id: str) -> tuple[bool, str]:
    spec = COMMANDS[command_id]
    proc = subprocess.run(spec.command, cwd=REPO_ROOT, text=True, capture_output=True)
    return proc.returncode == 0, (proc.stdout + proc.stderr)[-4000:]


@dataclass(frozen=True)
class Context:
    state: dict
    task: dict
    phase_id: str

    @property
    def phase(self) -> dict:
        for phase in load_yaml(PHASE_STATUS_PATH)["phases"]:
            if str(phase["phase_id"]) == self.phase_id:
                return phase
        raise ValueError(f"phase {self.phase_id} is not in phase_status.yml")

    @property
    def contract_path(self):
        return REPO_ROOT / self.phase["contract"]

    @property
    def plan_name(self) -> str:
        return self.contract_path.name

    @property
    def decisions_path(self):
        stem = self.contract_path.stem
        return REPO_ROOT / "reports" / "phase_audits" / "decisions" / f"{stem}_DECISIONS.md"

    @property
    def audit_path(self):
        return REPO_ROOT / self.phase["audit_packet"]

    def contract_commands(self) -> list[str]:
        text = self.contract_path.read_text(encoding="utf-8")
        meta = yaml.safe_load(text.split("---\n", 2)[1])
        return list(meta.get("required_gate_commands") or [])

    def new_pytest_commands(self) -> list[str]:
        return [c for c in self.contract_commands() if c.startswith("pytest_")]


# --------------------------------------------------------------------------- #
# stage checks: each returns the reasons this stage is not finished
# --------------------------------------------------------------------------- #


def check_precheck(ctx: Context) -> list[str]:
    reasons = []
    if not LOCK_PATH.exists():
        reasons.append(f"no {LOCK_PATH.name}; claim the worktree before starting")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if not branch.startswith("phase/"):
        reasons.append(f"on branch {branch!r}; cut phase/{ctx.phase_id}-slug first")
    if not tree_is_clean():
        reasons.append("working tree is dirty; commit or stash before the loop starts")
    return reasons


def check_contract(ctx: Context) -> list[str]:
    reasons = []
    if ctx.task.get("task_mode") != "contract-update":
        reasons.append(f"task_mode is {ctx.task.get('task_mode')!r}, expected contract-update")
    bullets = section_bullets(ctx.contract_path.read_text(encoding="utf-8"), "Acceptance criteria")
    specific = [b for b in bullets if b not in BOILERPLATE_CRITERIA]
    if len(specific) < MIN_SPECIFIC_CRITERIA:
        reasons.append(
            f"{ctx.contract_path.name} has {len(specific)} phase-specific criteria,"
            f" needs {MIN_SPECIFIC_CRITERIA}"
        )
    if not (ACTIVE_PLANS / ctx.plan_name).exists():
        reasons.append(f"no active ExecPlan at docs/exec_plans/active/{ctx.plan_name}")
    return reasons


def decision_items(text: str) -> list[tuple[str, str, str]]:
    """Return (heading, class, answer) for each numbered decision in the file."""
    items = []
    heading = ""
    reversibility = ""
    answer = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and stripped[3:4].isdigit():
            if heading:
                items.append((heading, reversibility, answer))
            heading, reversibility, answer = stripped[3:], "", ""
        elif stripped.lower().startswith("reversibility:"):
            reversibility = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Answer:"):
            answer = stripped.split(":", 1)[1].strip()
    if heading:
        items.append((heading, reversibility, answer))
    return items


def unanswered_frozen(text: str) -> list[str]:
    blocking = []
    for heading, reversibility, answer in decision_items(text):
        answered = answer not in {"", "[]", "[ ]"}
        if reversibility == "frozen-into-data" and not answered:
            blocking.append(heading)
    return blocking


def check_decisions(ctx: Context) -> list[str]:
    if not ctx.decisions_path.exists():
        return [f"no decision list at {ctx.decisions_path.relative_to(REPO_ROOT)}"]
    text = ctx.decisions_path.read_text(encoding="utf-8")
    items = decision_items(text)
    if not items:
        return ["decision list holds no numbered items"]
    reasons = [
        f"decision {heading!r} declares no reversibility class"
        for heading, reversibility, _ in items
        if reversibility not in {"frozen-into-data", "runtime-reversible"}
    ]
    return reasons


def check_human_gate(ctx: Context) -> list[str]:
    text = ctx.decisions_path.read_text(encoding="utf-8")
    return [f"awaiting a human answer on: {heading}" for heading in unanswered_frozen(text)]


def red_for_the_right_reason(output: str) -> bool:
    """Is this red about missing behavior, or about a broken test file?

    Two reds are legitimate at this stage. An assertion failure is the obvious one.
    The other is a module the phase has not written yet: tests are authored before
    any implementation exists, so importing it is *supposed* to fail, and the first
    version of this check wrongly rejected exactly the state it was built to
    require.

    Anything else, a syntax error or a typo in a fixture, means the test file is
    broken rather than describing behavior, and that red proves nothing.
    """
    if "AssertionError" in output or "assert" in output:
        return True
    return "ModuleNotFoundError" in output and "poker_training_bot" in output


def check_tests_authored(ctx: Context) -> list[str]:
    reasons = []
    if ctx.task.get("task_mode") != "implementation":
        reasons.append(f"task_mode is {ctx.task.get('task_mode')!r}, expected implementation")
    commands = ctx.new_pytest_commands()
    if not commands:
        reasons.append("the contract declares no pytest_* gate command for this phase")
    for command_id in commands:
        if command_id not in COMMANDS:
            reasons.append(f"gate command {command_id!r} is not registered yet")
            continue
        passed, output = run_command(command_id)
        if passed:
            reasons.append(
                f"{command_id} already passes, so the tests do not yet describe missing behavior"
            )
        elif not red_for_the_right_reason(output):
            reasons.append(
                f"{command_id} fails for neither an assertion nor a missing"
                " poker_training_bot module, so the test file is probably broken"
                " rather than describing behavior"
            )
    return reasons


def check_frozen(ctx: Context) -> list[str]:
    reasons = []
    passed, output = run_command("check_test_freeze")
    if not passed:
        reasons.append(f"check_test_freeze is failing: {output.strip().splitlines()[-1:]}")
    approved = ctx.task.get("approved_scope") or []
    if any(pattern.startswith("tests/") for pattern in approved):
        reasons.append("approved_scope still includes tests/; narrow it before building")
    if any(pattern.startswith("verification/") for pattern in approved):
        reasons.append("approved_scope still includes verification/; narrow it before building")
    return reasons


def check_build(ctx: Context) -> list[str]:
    reasons = []
    for command_id in ctx.contract_commands():
        if command_id not in COMMANDS:
            reasons.append(f"gate command {command_id!r} is not registered")
            continue
        passed, _ = run_command(command_id)
        if not passed:
            reasons.append(f"{command_id} is red")
    return reasons


def check_full_gate(ctx: Context) -> list[str]:
    reasons = []
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "run_verify.py")],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        reasons.append("run_verify.py is red")
    passed, _ = run_command("check_gate_bite")
    if not passed:
        reasons.append("check_gate_bite is red: a mutation survived, so the gate is decorative")
    return reasons


def check_review(ctx: Context) -> list[str]:
    review = REPO_ROOT / "reports" / "phase_audits" / "reviews" / ctx.plan_name
    if not review.exists():
        return [f"no review notes at {review.relative_to(REPO_ROOT)}"]
    text = review.read_text(encoding="utf-8").lower()
    missing = [word for word in ("mechanical", "domain", "blocker") if word not in text]
    if missing:
        return [f"review notes do not cover: {', '.join(missing)}"]
    return []


AUDIT_SECTIONS = ("summary", "checklist", "review", "decision", "recompute")


def check_audit(ctx: Context) -> list[str]:
    if not ctx.audit_path.exists():
        return [f"no audit packet at {ctx.audit_path.relative_to(REPO_ROOT)}"]
    text = ctx.audit_path.read_text(encoding="utf-8").lower()
    missing = [word for word in AUDIT_SECTIONS if word not in text]
    if missing:
        return [f"audit packet does not mention: {', '.join(missing)}"]
    return []


def check_closeout(ctx: Context) -> list[str]:
    reasons = []
    if ctx.phase["status"] != "completed":
        reasons.append(
            f"phase {ctx.phase_id} status is {ctx.phase['status']!r}, expected completed"
        )
    if not (COMPLETED_PLANS / ctx.plan_name).exists():
        reasons.append(f"ExecPlan is not filed under completed/: {ctx.plan_name}")
    if ctx.task.get("task_mode") != "idle":
        reasons.append(f"task_mode is {ctx.task.get('task_mode')!r}, expected idle")
    tag = f"phase-{ctx.phase_id}-complete"
    if tag not in git("tag", "--list", tag).splitlines():
        reasons.append(f"tag {tag} does not exist")
    if not tree_is_clean():
        reasons.append("working tree is dirty; the closeout commit is missing")
    return reasons


@dataclass(frozen=True)
class Stage:
    number: int
    name: str
    who: str
    instruction: str
    check: object


def check_advance(ctx: Context) -> list[str]:
    return []


STAGES: tuple[Stage, ...] = (
    Stage(
        0, "precheck", "script",
        "Claim the worktree, cut phase/NN-slug, confirm a clean tree.",
        check_precheck,
    ),
    Stage(
        1, "contract", "model",
        "In contract-update mode, turn the phase skeleton into real acceptance"
        " criteria, and create the active ExecPlan.",
        check_contract,
    ),
    Stage(
        2, "decisions", "model",
        "Write the judgment-call list. Every item needs a default and a"
        " 'Reversibility:' line of frozen-into-data or runtime-reversible.",
        check_decisions,
    ),
    Stage(
        3, "human-gate", "human",
        "Only frozen-into-data items block. Everything else proceeds on its"
        " default and is reported afterwards.",
        check_human_gate,
    ),
    Stage(
        4, "tests", "model",
        "In implementation mode, author tests from the contract alone. No"
        " implementation exists yet, so they must fail on assertions.",
        check_tests_authored,
    ),
    Stage(
        5, "freeze", "script",
        "Run scripts/freeze_tests.py, then drop tests/ and verification/ from"
        " approved_scope with a dated scope_change_log entry.",
        check_frozen,
    ),
    Stage(
        6, "build", "model",
        "Implement against the frozen tests. One repair attempt per failing"
        " command, then halt.",
        check_build,
    ),
    Stage(
        7, "gate", "script",
        "Full run_verify.py green, then check_gate_bite to prove the gate"
        " actually catches the mutations.",
        check_full_gate,
    ),
    Stage(
        8, "review", "model",
        "Two read-only reviewers, one mechanical and one poker-domain. Write"
        " findings to reports/phase_audits/reviews/, classified blocker or not.",
        check_review,
    ),
    Stage(
        9, "audit", "model",
        "Write the audit packet: summary, non-coding checklist, review findings,"
        " decision outcomes, and one number a reader can recompute by hand.",
        check_audit,
    ),
    Stage(
        10, "closeout", "script",
        "File the ExecPlan as completed, set the phase completed, tag"
        " phase-NN-complete, reset to idle, gate again, commit, merge the branch.",
        check_closeout,
    ),
    Stage(
        11, "advance", "script",
        "Consult verification/loop_policy.yml: continue into the next phase, or"
        " halt with the one thing a human must supply.",
        check_advance,
    ),
)


def stage_by_number(number: int) -> Stage:
    for stage in STAGES:
        if stage.number == number:
            return stage
    raise ValueError(f"unknown stage {number}")


def default_state() -> dict:
    return {"schema_version": SCHEMA_VERSION, "loop": "idle", "phase_id": None, "stage": 0}


def read_state() -> dict:
    if not STATE_PATH.exists():
        return default_state()
    return load_yaml(STATE_PATH) or default_state()


def write_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(yaml.safe_dump(state, sort_keys=True), encoding="utf-8")


def policy_for(phase_id: str) -> dict:
    return (load_yaml(POLICY_PATH).get("phases") or {}).get(phase_id) or {}


def report(ctx: Context, stage: Stage, reasons: list[str]) -> None:
    print(
        f"stage {stage.number}/11  {stage.name}"
        f"  ·  phase {ctx.phase_id}  ·  runner: {stage.who}"
    )
    print(
        f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')}"
        f"  ·  task_mode {ctx.task.get('task_mode')!r}"
    )
    print()
    print(f"do: {stage.instruction}")
    print()
    if reasons:
        print("not done yet:")
        for reason in reasons:
            print(f"  - {reason}")
    else:
        print("this stage's checks pass; run --advance to move on")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", metavar="PHASE_ID", help="begin the loop for a phase")
    parser.add_argument("--advance", action="store_true", help="verify and move to the next stage")
    parser.add_argument("--halt", metavar="REASON", help="record a halt and stop")
    args = parser.parse_args()

    state = read_state()
    task = load_yaml(TASK_PATH)

    if args.start:
        policy = policy_for(args.start)
        if policy.get("needs_human_data"):
            print(f"phase {args.start} cannot start: {policy.get('reason')}", file=sys.stderr)
            return 1
        write_state(
            {
                "schema_version": SCHEMA_VERSION,
                "loop": "running",
                "phase_id": args.start,
                "stage": 0,
                "auto_advance": bool(policy.get("auto_advance")),
            }
        )
        print(f"loop started for phase {args.start} at stage 0")
        return 0

    if args.halt:
        state["loop"] = "halted"
        state["halt_reason"] = args.halt
        write_state(state)
        print(f"halted at stage {state.get('stage')}: {args.halt}")
        return 1

    if state.get("loop") != "running":
        print(f"loop is {state.get('loop')!r}; start it with --start PHASE_ID")
        return 0

    ctx = Context(state=state, task=task, phase_id=str(state["phase_id"]))
    stage = stage_by_number(int(state["stage"]))
    reasons = stage.check(ctx)

    if not args.advance:
        report(ctx, stage, reasons)
        return 0

    if reasons:
        print(f"cannot advance past stage {stage.number} ({stage.name}):", file=sys.stderr)
        for reason in reasons:
            print(f"  - {reason}", file=sys.stderr)
        return 1

    if stage.number == 11:
        state["loop"] = "completed"
        write_state(state)
        print(f"phase {ctx.phase_id} loop complete")
        return 0

    state["stage"] = stage.number + 1
    write_state(state)
    nxt = stage_by_number(state["stage"])
    print(f"advanced to stage {nxt.number} ({nxt.name}, runner: {nxt.who})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
