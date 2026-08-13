"""The four checks that close the ways this repo can be wrong while the gate is green.

Each check is a pure function over data rather than a script that reads the repo, so it
can be run against a deliberately broken input as well as against this repo. A check
that has only ever been run on a repo that satisfies it has not been shown to fail, and
that is the class of defect this phase exists to remove.

Every error string names the thing, the value found, and the value expected. A check
that reports a problem a reader cannot act on is a check nobody keeps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Command IDs that no mutation needs to point at, with the reason each is exempt. The
# list is here rather than in a config file so that adding to it appears in a diff a
# reviewer reads. It is empty on purpose: the catch-all `pytest` command could have
# lived here, since every mutation that fails any command fails it too, but naming it in
# a mutation costs one line and an exemption is a claim that something cannot be
# checked.
EXEMPT_FROM_MUTATION_COVERAGE: dict[str, str] = {}

ALLOWED_BACKLOG_STATUSES: frozenset[str] = frozenset({"deferred", "done"})

# Labels a backlog item may carry instead of a phase id, for work that belongs to a
# subsystem rather than to a numbered phase.
NON_PHASE_LABELS: frozenset[str] = frozenset(
    {
        "charts",
        "contract-update",
        "engine",
        "sample-comparison",
        "samples",
        "simulator",
        "strategy",
        "v2",
    }
)

REQUIRED_BACKLOG_FIELDS = ("id", "status", "phase", "title", "reason")


@dataclass(frozen=True)
class CheckSpec:
    """One check, and what it deliberately does not reach.

    The second field is the point. A report that lists passing checks without saying
    what they do not cover reads as a guarantee, and none of these is one.
    """

    name: str
    covers: str
    does_not_cover: str


CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec(
        name="mutation coverage",
        covers=(
            "Every registered pytest_* gate command is named by at least one committed"
            " mutation, so check_gate_bite has something to prove about each one."
        ),
        does_not_cover=(
            "It does not judge whether a mutation is a good one. One canary aimed at a"
            " command says the command can fail, not that its tests are strong."
        ),
    ),
    CheckSpec(
        name="fact drift",
        covers=(
            "Every registered fact is recomputed from the repo and compared against each"
            " document that quotes it, by sentence shape rather than by bare number."
        ),
        does_not_cover=(
            "It reads only the facts it has been given. A number nobody registered is a"
            " number nobody checks, and most sentences here state no registered fact."
        ),
    ),
    CheckSpec(
        name="backlog integrity",
        covers=(
            "Every item is well formed and uniquely identified, every phase it names"
            " exists, and every backlog id cited in docs or reports resolves to an item."
        ),
        does_not_cover=(
            "It cannot tell whether an item is still worth doing, or whether one marked"
            " done was actually finished."
        ),
    ),
    CheckSpec(
        name="phase record agreement",
        covers=(
            "For every completed phase: the status, the ExecPlan's directory, the audit"
            " packet, and the phase-NN-complete tag all agree."
        ),
        does_not_cover=(
            "It reads whether the records exist and match, never whether the phase did"
            " what its contract said. The tag check is skipped on a clone with no tags."
        ),
    ),
)


def mutation_coverage_errors(
    command_ids: list[str],
    mutations: list[dict],
    exempt: dict[str, str] | None = None,
) -> list[str]:
    """Commands no committed mutation points at.

    `check_gate_bite` proves a mutation is caught. It cannot say anything about a
    command nobody aimed a mutation at, and such a command is an assertion that the
    tests it runs are worth something rather than evidence of it.
    """
    exempt = EXEMPT_FROM_MUTATION_COVERAGE if exempt is None else exempt
    targeted = {command for mutation in mutations for command in mutation.get("must_fail", ())}
    errors = []
    for command_id in command_ids:
        if command_id in targeted or command_id in exempt:
            continue
        errors.append(
            f"gate command {command_id!r} is named by no mutation in verification/"
            "mutations.yml, so check_gate_bite proves nothing about it. Aim a mutation"
            " at it, or exempt it by name in EXEMPT_FROM_MUTATION_COVERAGE with a reason"
        )
    return errors


def fact_drift_errors(facts: tuple, values: dict[str, str], root: Path) -> list[str]:
    """Documents stating a value the fact no longer has.

    A missing match is an error rather than a pass. If a fact claims a document quotes
    it and the sentence has been rewritten past the pattern, the number has stopped
    being checked, and passing silently there would rebuild the hole inside the fix for
    it.
    """
    errors = []
    for fact in facts:
        current = values.get(fact.name)
        if current is None:
            errors.append(f"fact {fact.name!r} has no computed value")
            continue
        pattern = re.compile(fact.pattern)
        for relative in fact.quoted_in:
            path = root / relative
            if not path.is_file():
                errors.append(f"fact {fact.name!r} names missing file {relative}")
                continue
            found = pattern.findall(path.read_text(encoding="utf-8"))
            if not found:
                errors.append(
                    f"{relative} no longer matches the sentence shape for fact"
                    f" {fact.name!r}, so its value ({current}) has stopped being"
                    " checked there. Restore the wording or update the fact's pattern"
                )
                continue
            for raw in found:
                if raw.replace(",", "") != current:
                    errors.append(
                        f"{relative} states {raw} for fact {fact.name!r}"
                        f" ({fact.description}); the repo says {current}"
                    )
    return errors


def backlog_errors(
    items: list[dict],
    phase_ids: set[str],
    citations: dict[str, set[str]],
) -> list[str]:
    """Malformed entries, duplicate ids, unknown phases, and citations of nothing."""
    errors = []
    seen: set[str] = set()
    known: set[str] = set()
    for index, item in enumerate(items):
        item_id = str(item.get("id") or "").strip()
        label = item_id or f"item {index}"
        if not item_id:
            errors.append(f"backlog {label} has no id")
        elif item_id in seen:
            errors.append(f"backlog id {item_id!r} is a duplicate; ids must be unique")
        else:
            seen.add(item_id)
            known.add(item_id)

        missing = [
            field for field in REQUIRED_BACKLOG_FIELDS if not str(item.get(field) or "").strip()
        ]
        if missing:
            errors.append(f"backlog {label} is missing {', '.join(missing)}")

        status = str(item.get("status") or "").strip()
        if status and status not in ALLOWED_BACKLOG_STATUSES:
            errors.append(
                f"backlog {label} has status {status!r}, which is not one of"
                f" {sorted(ALLOWED_BACKLOG_STATUSES)}"
            )

        phase = str(item.get("phase") or "").strip()
        if phase and phase not in phase_ids and phase not in NON_PHASE_LABELS:
            errors.append(
                f"backlog {label} is filed against phase {phase!r}, which is neither a"
                " phase in phase_status.yml nor a declared non-phase label"
            )

    for path, cited in sorted(citations.items()):
        for citation in sorted(cited):
            if citation not in known:
                errors.append(
                    f"{path} cites backlog id {citation!r}, which no item declares."
                    " A finding filed under an id nobody created has recorded nothing"
                )
    return errors


def phase_record_errors(phases: list[dict], root: Path, tags: set[str]) -> list[str]:
    """The four places a phase's completion is written down, cross-checked.

    The tag check is skipped when the repository has no tags at all, because a check
    that fails on a tagless clone is a check about the clone. The quality report says
    when it skipped.
    """
    errors = []
    for phase in phases:
        if phase.get("status") != "completed":
            continue
        phase_id = str(phase["phase_id"])
        stem = Path(str(phase["contract"])).name

        plan = root / "docs" / "exec_plans" / "completed" / stem
        if not plan.is_file():
            errors.append(
                f"phase {phase_id} is completed but its ExecPlan is not at"
                f" docs/exec_plans/completed/{stem}"
            )

        packet_relative = str(phase.get("audit_packet") or "")
        packet = root / packet_relative
        if not packet_relative or not packet.is_file():
            errors.append(
                f"phase {phase_id} is completed but its audit packet"
                f" ({packet_relative or 'unnamed'}) does not exist"
            )
        elif phase_id not in packet.read_text(encoding="utf-8"):
            errors.append(
                f"phase {phase_id} audit packet {packet_relative} never names phase"
                f" {phase_id}, so it may belong to a different phase"
            )

        if tags:
            expected = f"phase-{phase_id}-complete"
            if expected not in tags:
                errors.append(
                    f"phase {phase_id} is completed but tag {expected!r} does not exist"
                )
    return errors


def render_quality_report(results: list[tuple[str, list[str]]]) -> str:
    """The committed report, written so a reader can tell a pass from an unchecked claim."""
    by_name = {spec.name: spec for spec in CHECKS}
    lines = [
        "Quality And Drift Report",
        "========================",
        "",
        "Four checks, each with what it covers and what it does not. The second half of",
        "each entry matters as much as the result: a check that passed is not a promise",
        "about everything it did not look at, and this repo has already shipped three",
        "wrong numbers and a decorative gate command past a green run.",
        "",
    ]
    for name, errors in results:
        spec = by_name.get(name)
        lines.append(f"{'PASS' if not errors else 'FAIL'}  {name}")
        if spec is not None:
            lines.append(f"      covers:   {spec.covers}")
            lines.append(f"      does not: {spec.does_not_cover}")
        for error in errors:
            lines.append(f"      ! {error}")
        lines.append("")
    return "\n".join(lines) + "\n"
