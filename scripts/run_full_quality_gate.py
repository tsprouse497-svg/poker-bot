"""Run the quality checks and write the quality report.

Each check is a pure function in `quality_checks`; this script is what feeds them the
repo and prints the result. It is the gate command, so it exits non-zero on any error,
and it writes the committed report either way - a report that only appears when
everything passed is a report nobody can use to see what failed.
"""

from __future__ import annotations

import re
import subprocess
import sys

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from quality_checks import (  # noqa: E402
    CHECKS,
    EXEMPT_FROM_MUTATION_COVERAGE,
    backlog_errors,
    fact_drift_errors,
    mutation_coverage_errors,
    phase_record_errors,
    render_quality_report,
)
from repo_facts import FACTS, computed_values  # noqa: E402
from run_verify import COMMANDS  # noqa: E402

REPORT_PATH = REPO_ROOT / "reports" / "active" / "latest_quality_report.txt"
FACTS_PATH = REPO_ROOT / "reports" / "active" / "repo_facts.yml"
BACKLOG_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+){1,}\b")


def _load(relative: str) -> dict:
    return yaml.safe_load((REPO_ROOT / relative).read_text(encoding="utf-8"))


def _git_tags() -> set[str]:
    proc = subprocess.run(
        ["git", "tag"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def _citations(known: set[str]) -> dict[str, set[str]]:
    """Backlog ids cited in prose, keyed by the file citing them.

    Only tokens shaped like a backlog id are considered, and only files under docs/ and
    reports/ are read. A citation of an id nobody filed is the error; a sentence that
    happens to contain capital letters is not.
    """
    citations: dict[str, set[str]] = {}
    for pattern in ("docs/**/*.md", "reports/**/*.md"):
        for path in sorted(REPO_ROOT.glob(pattern)):
            cited = set(BACKLOG_ID.findall(path.read_text(encoding="utf-8")))
            cited = {token for token in cited if token in known or token.startswith("CORPUS-")}
            if cited:
                citations[str(path.relative_to(REPO_ROOT))] = cited
    return citations


def main() -> int:
    facts_errors: list[str] = []
    values = computed_values()
    if not FACTS_PATH.is_file():
        facts_errors.append(
            f"{FACTS_PATH.relative_to(REPO_ROOT)} does not exist;"
            " run scripts/generate_repo_facts.py"
        )
    else:
        committed = _load(str(FACTS_PATH.relative_to(REPO_ROOT))).get("facts") or {}
        if committed != values:
            facts_errors.append(
                "the committed facts file disagrees with what the code computes;"
                " run scripts/generate_repo_facts.py and update the documents it names"
            )
    facts_errors.extend(fact_drift_errors(FACTS, values, REPO_ROOT))

    backlog = _load("backlog.yml")["items"]
    known = {str(item.get("id")) for item in backlog}
    phases = _load("phase_status.yml")["phases"]
    tags = _git_tags()

    results = [
        (
            CHECKS[0].name,
            mutation_coverage_errors(
                sorted(command for command in COMMANDS if command.startswith("pytest")),
                _load("verification/mutations.yml")["mutations"],
                EXEMPT_FROM_MUTATION_COVERAGE,
            ),
        ),
        (CHECKS[1].name, facts_errors),
        (
            CHECKS[2].name,
            backlog_errors(
                backlog,
                {str(phase["phase_id"]) for phase in phases},
                _citations(known),
            ),
        ),
        (CHECKS[3].name, phase_record_errors(phases, REPO_ROOT, tags)),
    ]

    report = render_quality_report(results)
    if not tags:
        report += "Note: this clone has no git tags, so the phase tag check was skipped.\n"
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    failed = [name for name, errors in results if errors]
    print(report)
    print(f"wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    if failed:
        print(f"quality gate failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
