from __future__ import annotations

import scripts.run_verify as run_verify


def test_phase_00_registry_contains_required_commands() -> None:
    required = {
        "check_scope",
        "check_contracts",
        "check_generated_status",
        "check_file_sizes",
        "import_smoke",
        "pytest",
        "ruff_check",
        "uv_import_smoke",
    }

    assert required.issubset(run_verify.COMMANDS)
    assert required.issubset(run_verify.PHASE_00_GATE)
