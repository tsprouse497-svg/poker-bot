"""The four checks that close the ways this repo can be wrong while the gate is green.

Stage 4 stub: the tests are authored against these signatures before any of them does
anything, so every one returns no errors and every test that demands an error fails.
The logic lands at stage 6, and the test file is frozen before it does.

Each check is a pure function over data rather than a script that reads the repo, so it
can be run against a deliberately broken input as well as against this repo. A check
that has only ever been run on a repo that satisfies it has not been shown to fail.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Command IDs that no mutation needs to point at, with the reason each is exempt. The
# list is here rather than in a config file so that adding to it appears in a diff a
# reviewer reads.
EXEMPT_FROM_MUTATION_COVERAGE: dict[str, str] = {}

ALLOWED_BACKLOG_STATUSES: frozenset[str] = frozenset()
NON_PHASE_LABELS: frozenset[str] = frozenset()


@dataclass(frozen=True)
class CheckSpec:
    """One check, and what it deliberately does not reach.

    The second field is the point. A report that lists passing checks without saying
    what they do not cover reads as a guarantee, and none of these is one.
    """

    name: str
    covers: str
    does_not_cover: str


CHECKS: tuple[CheckSpec, ...] = ()


def mutation_coverage_errors(
    command_ids: list[str],
    mutations: list[dict],
    exempt: dict[str, str] | None = None,
) -> list[str]:
    return []


def fact_drift_errors(facts: tuple, values: dict[str, str], root: Path) -> list[str]:
    return []


def backlog_errors(
    items: list[dict],
    phase_ids: set[str],
    citations: dict[str, set[str]],
) -> list[str]:
    return []


def phase_record_errors(phases: list[dict], root: Path, tags: set[str]) -> list[str]:
    return []


def render_quality_report(results: list[tuple[str, list[str]]]) -> str:
    return ""
