"""Phase 09: the checks that close the ways this repo can be wrong while the gate is green.

Authored before any of the checks does anything, and frozen before any of them does, so
these are the specification rather than a description of what got built.

Every check is exercised twice: once against a deliberately broken input, which is the
only way to show it can fail at all, and once against this repo, which is the only way
to show it is true here. A check that has only ever been run on a repo that satisfies it
proves nothing, and that is the class of defect this whole phase is about.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.quality_checks import (
    ALLOWED_BACKLOG_STATUSES,
    CHECKS,
    EXEMPT_FROM_MUTATION_COVERAGE,
    backlog_errors,
    fact_drift_errors,
    mutation_coverage_errors,
    phase_record_errors,
    render_quality_report,
)
from scripts.repo_facts import FACTS, Fact, computed_values
from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_verify import COMMANDS  # noqa: E402


def _registered_pytest_commands() -> list[str]:
    return sorted(command for command in COMMANDS if command.startswith("pytest"))


def _committed_mutations() -> list[dict]:
    payload = yaml.safe_load((REPO_ROOT / "verification" / "mutations.yml").read_text())
    return payload["mutations"]


def _phase_status() -> list[dict]:
    payload = yaml.safe_load((REPO_ROOT / "phase_status.yml").read_text())
    return payload["phases"]


def _git_tags() -> set[str]:
    proc = subprocess.run(
        ["git", "tag"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


# --------------------------------------------------------------------------- #
# Every gate command that claims to prove something is proved to bite
# --------------------------------------------------------------------------- #


def test_a_command_no_mutation_points_at_is_reported() -> None:
    """The check's whole reason for existing, shown failing.

    `check_gate_bite` proves a committed mutation is caught. It cannot say anything
    about a command nobody aimed a mutation at, and such a command is an assertion that
    the tests it runs are worth something rather than evidence of it.
    """
    errors = mutation_coverage_errors(
        command_ids=["pytest_covered", "pytest_naked"],
        mutations=[{"id": "m", "must_fail": ["pytest_covered"]}],
        exempt={},
    )

    assert len(errors) == 1
    assert "pytest_naked" in errors[0]


def test_a_covered_command_is_not_reported() -> None:
    errors = mutation_coverage_errors(
        command_ids=["pytest_covered"],
        mutations=[{"id": "m", "must_fail": ["pytest_covered", "pytest_other"]}],
        exempt={},
    )

    assert errors == []


def test_an_exemption_needs_a_reason_and_silences_only_itself() -> None:
    """An exemption is a decision with a reason, not a way to make a check pass."""
    errors = mutation_coverage_errors(
        command_ids=["pytest_naked", "pytest_also_naked"],
        mutations=[],
        exempt={"pytest_naked": "runs every test file, so it is covered by all of them"},
    )

    assert len(errors) == 1
    assert "pytest_also_naked" in errors[0]

    unexplained = [name for name, reason in EXEMPT_FROM_MUTATION_COVERAGE.items() if not reason]
    assert unexplained == []


def test_every_registered_pytest_command_in_this_repo_is_covered() -> None:
    """And the same check against the repo, which is the claim that matters."""
    errors = mutation_coverage_errors(
        command_ids=_registered_pytest_commands(),
        mutations=_committed_mutations(),
        exempt=EXEMPT_FROM_MUTATION_COVERAGE,
    )

    assert errors == []


def test_the_full_table_preflop_canary_changes_the_poker_rather_than_crashing() -> None:
    """A canary that trips on a missing symbol proves the module imports.

    The command this covers guards what the bot opens, calls, and folds. Its mutation
    has to change which hands the chart plays, so it names a strategy module and swaps a
    value rather than deleting a definition.
    """
    aimed = [
        mutation
        for mutation in _committed_mutations()
        if "pytest_full_table_preflop" in mutation["must_fail"]
    ]

    assert aimed, "no mutation targets pytest_full_table_preflop"
    for mutation in aimed:
        assert "/strategy/" in mutation["file"]
        assert mutation["find"].strip()
        assert mutation["replace"].strip()
        assert mutation["find"] != mutation["replace"]


# --------------------------------------------------------------------------- #
# A number stated in a committed document matches the repo it describes
# --------------------------------------------------------------------------- #


def test_a_document_stating_a_stale_value_is_reported_with_both_values(tmp_path) -> None:
    """Naming the file, the stale value and the current one is what makes it actionable."""
    document = tmp_path / "packet.md"
    document.write_text("The sample holds 7 all-in hands.\n", encoding="utf-8")
    fact = Fact(
        name="all_in_hands",
        description="hands where a seat commits its whole stack",
        compute=lambda: "24",
        pattern=r"holds (\d+) all-in hands",
        quoted_in=("packet.md",),
    )

    errors = fact_drift_errors((fact,), {"all_in_hands": "24"}, tmp_path)

    assert len(errors) == 1
    assert "packet.md" in errors[0]
    assert "7" in errors[0]
    assert "24" in errors[0]


def test_a_document_stating_the_current_value_is_accepted(tmp_path) -> None:
    document = tmp_path / "packet.md"
    document.write_text("The sample holds 24 all-in hands.\n", encoding="utf-8")
    fact = Fact(
        name="all_in_hands",
        description="hands where a seat commits its whole stack",
        compute=lambda: "24",
        pattern=r"holds (\d+) all-in hands",
        quoted_in=("packet.md",),
    )

    assert fact_drift_errors((fact,), {"all_in_hands": "24"}, tmp_path) == []


def test_a_sentence_rewritten_past_the_pattern_is_an_error_not_a_pass(tmp_path) -> None:
    """The quiet failure this check exists to avoid becoming.

    If a fact claims a document quotes it and the pattern no longer matches, the number
    has stopped being checked. Passing silently there would rebuild the hole inside the
    fix for it.
    """
    document = tmp_path / "packet.md"
    document.write_text("The sample contains twenty-four all-in hands.\n", encoding="utf-8")
    fact = Fact(
        name="all_in_hands",
        description="hands where a seat commits its whole stack",
        compute=lambda: "24",
        pattern=r"holds (\d+) all-in hands",
        quoted_in=("packet.md",),
    )

    errors = fact_drift_errors((fact,), {"all_in_hands": "24"}, tmp_path)

    assert len(errors) == 1
    assert "packet.md" in errors[0]


def test_every_registered_fact_carries_a_pattern_with_exactly_one_group() -> None:
    assert FACTS, "no facts registered, so no document number is checked"
    for fact in FACTS:
        assert re.compile(fact.pattern).groups == 1
        assert fact.quoted_in
        assert fact.description.strip()


def test_the_committed_facts_file_matches_what_the_code_computes() -> None:
    """A stale committed facts file is the same defect one indirection back."""
    committed = yaml.safe_load((REPO_ROOT / "reports" / "active" / "repo_facts.yml").read_text())

    assert committed["facts"] == computed_values()


def test_no_document_in_this_repo_states_a_stale_fact() -> None:
    assert fact_drift_errors(FACTS, computed_values(), REPO_ROOT) == []


# --------------------------------------------------------------------------- #
# The backlog is a live work list rather than an archive
# --------------------------------------------------------------------------- #


def test_a_malformed_or_duplicated_backlog_item_is_reported() -> None:
    items = [
        {"id": "A", "status": "deferred", "phase": "charts", "title": "t", "reason": "r"},
        {"id": "A", "status": "deferred", "phase": "charts", "title": "t", "reason": "r"},
        {"id": "B", "status": "invented", "phase": "charts", "title": "t", "reason": "r"},
        {"id": "C", "status": "deferred", "phase": "charts", "title": "", "reason": "r"},
    ]

    errors = backlog_errors(items, phase_ids={"charts"}, citations={})

    assert len(errors) == 3
    assert any("A" in error and "duplicate" in error.lower() for error in errors)
    assert any("invented" in error for error in errors)
    assert any("C" in error for error in errors)


def test_a_cited_backlog_id_that_was_never_filed_is_reported() -> None:
    """A packet that files a finding under an id nobody created has recorded nothing."""
    items = [{"id": "REAL", "status": "deferred", "phase": "charts", "title": "t", "reason": "r"}]

    errors = backlog_errors(
        items,
        phase_ids={"charts"},
        citations={"reports/phase_audits/PHASE_08.md": {"REAL", "GHOST"}},
    )

    assert len(errors) == 1
    assert "GHOST" in errors[0]
    assert "PHASE_08" in errors[0]


def test_an_item_filed_against_a_phase_that_does_not_exist_is_reported() -> None:
    items = [{"id": "A", "status": "deferred", "phase": "nowhere", "title": "t", "reason": "r"}]

    errors = backlog_errors(items, phase_ids={"charts"}, citations={})

    assert len(errors) == 1
    assert "nowhere" in errors[0]


def test_this_repo_s_backlog_is_well_formed_and_every_citation_resolves() -> None:
    payload = yaml.safe_load((REPO_ROOT / "backlog.yml").read_text())
    phase_ids = {phase["phase_id"] for phase in _phase_status()}
    ids = {item["id"] for item in payload["items"]}
    citations: dict[str, set[str]] = {}
    for path in sorted(REPO_ROOT.glob("docs/**/*.md")) + sorted(
        REPO_ROOT.glob("reports/**/*.md")
    ):
        cited = {token for token in re.findall(r"\b[A-Z][A-Z0-9-]{4,}\b", path.read_text())}
        cited &= ids | {"GHOST"}
        if cited:
            citations[str(path.relative_to(REPO_ROOT))] = cited

    assert backlog_errors(payload["items"], phase_ids, citations) == []
    assert ALLOWED_BACKLOG_STATUSES


# --------------------------------------------------------------------------- #
# The phase record agrees with itself
# --------------------------------------------------------------------------- #


def test_a_completed_phase_missing_its_tag_is_reported(tmp_path) -> None:
    (tmp_path / "docs" / "exec_plans" / "completed").mkdir(parents=True)
    (tmp_path / "docs" / "exec_plans" / "completed" / "PHASE_01_X.md").write_text("x")
    (tmp_path / "reports" / "phase_audits").mkdir(parents=True)
    (tmp_path / "reports" / "phase_audits" / "PHASE_01_X.md").write_text("phase 01")
    phases = [
        {
            "phase_id": "01",
            "status": "completed",
            "contract": "docs/phase_contracts/PHASE_01_X.md",
            "audit_packet": "reports/phase_audits/PHASE_01_X.md",
        }
    ]

    errors = phase_record_errors(phases, tmp_path, tags={"phase-00-complete"})

    assert len(errors) == 1
    assert "01" in errors[0]
    assert "tag" in errors[0].lower()


def test_a_completed_phase_missing_its_audit_packet_is_reported(tmp_path) -> None:
    phases = [
        {
            "phase_id": "01",
            "status": "completed",
            "contract": "docs/phase_contracts/PHASE_01_X.md",
            "audit_packet": "reports/phase_audits/PHASE_01_X.md",
        }
    ]

    errors = phase_record_errors(phases, tmp_path, tags={"phase-01-complete"})

    assert any("audit" in error.lower() for error in errors)


def test_the_tag_check_is_skipped_rather_than_failed_when_the_clone_has_no_tags(
    tmp_path,
) -> None:
    """A check that fails on a tagless clone is a check about the clone.

    Skipping is only honest if it announces itself, which the quality report does.
    """
    (tmp_path / "reports" / "phase_audits").mkdir(parents=True)
    (tmp_path / "reports" / "phase_audits" / "PHASE_01_X.md").write_text("phase 01")
    phases = [
        {
            "phase_id": "01",
            "status": "completed",
            "contract": "docs/phase_contracts/PHASE_01_X.md",
            "audit_packet": "reports/phase_audits/PHASE_01_X.md",
        }
    ]

    errors = phase_record_errors(phases, tmp_path, tags=set())

    assert not any("tag" in error.lower() for error in errors)


def test_every_completed_phase_in_this_repo_agrees_with_itself() -> None:
    assert phase_record_errors(_phase_status(), REPO_ROOT, _git_tags()) == []


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #


def test_every_check_declares_what_it_does_not_cover() -> None:
    """A report listing passing checks without their limits reads as a guarantee."""
    assert CHECKS
    for check in CHECKS:
        assert check.covers.strip()
        assert check.does_not_cover.strip()


def test_the_report_prints_each_check_with_its_limits_and_its_result() -> None:
    text = render_quality_report([(check.name, []) for check in CHECKS])

    for check in CHECKS:
        assert check.name in text
        assert check.does_not_cover in text
    assert "does not" in text.lower()


def test_the_report_names_a_failing_check_and_its_errors() -> None:
    text = render_quality_report([(CHECKS[0].name, ["a specific thing went wrong"])])

    assert "a specific thing went wrong" in text
    assert "FAIL" in text


@pytest.mark.parametrize("command_id", ["run_full_quality_gate", "pytest_quality_hardening"])
def test_the_phase_commands_are_registered(command_id) -> None:
    assert command_id in COMMANDS


def test_the_committed_quality_report_exists_and_is_the_one_the_gate_writes() -> None:
    report = REPO_ROOT / "reports" / "active" / "latest_quality_report.txt"

    assert report.is_file()
    for check in CHECKS:
        assert check.name in report.read_text(encoding="utf-8")


def test_the_quality_gate_command_passes_against_this_repo() -> None:
    """The end-to-end claim, run as the gate runs it."""
    proc = subprocess.run(
        [sys.executable, str(Path("scripts") / "run_full_quality_gate.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
