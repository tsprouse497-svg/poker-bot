from __future__ import annotations

import scripts.check_execplan_delegation as delegation


def test_execplan_delegation_plan_accepts_worker_lane() -> None:
    text = """# Plan

## Delegation Plan

- Worker lanes: worker-1 implements the bounded code slice.
- Ownership: worker-1 owns `src/**`; coordinator owns integration.
- Expected outputs: code changes, tests, and changed-file summary.
- Status: assigned before implementation.
- Integration order: coordinator reviews worker output before full gate.
- Review handoff: read-only reviewer inspects contract, reports, and audit.
"""

    assert delegation.validate_execplan_text(text, "PLAN.md") == []


def test_execplan_delegation_plan_requires_section() -> None:
    text = "# Plan\n\n## Objective\n\nShip the phase.\n"

    errors = delegation.validate_execplan_text(text, "PLAN.md")

    assert "missing required '## Delegation Plan' section" in errors[0]


def test_execplan_delegation_plan_requires_fields() -> None:
    text = """# Plan

## Delegation Plan

- Worker lanes: worker-1 implements the bounded code slice.
- Ownership: worker-1 owns `src/**`.
"""

    errors = delegation.validate_execplan_text(text, "PLAN.md")

    assert "Expected outputs" in errors[0]
    assert "Review handoff" in errors[0]


def test_execplan_delegation_plan_accepts_concrete_exception() -> None:
    text = """# Plan

## Delegation Plan

- No-delegation exception: subagent spawning is unavailable in this session.
"""

    assert delegation.validate_execplan_text(text, "PLAN.md") == []


def test_execplan_delegation_plan_rejects_template_field_placeholders() -> None:
    text = (
        "# Plan\n\n"
        "## Delegation Plan\n\n"
        "- Worker lanes: list worker subagents and their bounded implementation lanes.\n"
        "- Ownership: list file/module ownership for each worker and coordinator-owned "
        "integration responsibilities.\n"
        "- Expected outputs: list patches, reports, review notes, or changed-file "
        "summaries expected from each lane.\n"
        "- Status: planned, assigned, integrated, blocked, or completed for each lane.\n"
        "- Integration order: state how the coordinator will review and merge lanes.\n"
        "- Review handoff: state what the independent read-only reviewer must inspect.\n"
    )

    errors = delegation.validate_execplan_text(text, "PLAN.md")

    assert "Worker lanes" in errors[0]
    assert "Review handoff" in errors[0]


def test_execplan_delegation_plan_rejects_template_exception_placeholder() -> None:
    text = """# Plan

## Delegation Plan

- No-delegation exception: concrete reason implementation is coordinator-owned.
"""

    errors = delegation.validate_execplan_text(text, "PLAN.md")

    assert "Worker lanes" in errors[0]
