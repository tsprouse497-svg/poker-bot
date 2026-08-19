"""Render the committed solver export as range grids a person can read.

The report is this phase's review surface: a human loads the saved solve in GTOpen's own
interface and compares its grids against these. Everything printed says whether a check
covers it or whether it is there to be read.
"""

from __future__ import annotations

import sys

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.gtopen_expectations import (  # noqa: E402
    EXPECTATIONS_PATH,
    aggregate_frequencies,
    load_expectations,
)
from poker_training_bot.solver_artifacts.gtopen_export import (  # noqa: E402
    COMMITTED_EXPORT_PATH,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.gtopen_export_report import (  # noqa: E402
    REPORT_PATH,
    render_solver_export_report,
)


def main() -> int:
    export = load_solver_export(COMMITTED_EXPORT_PATH)
    text = render_solver_export_report(
        export=export,
        measured=aggregate_frequencies(export),
        expectations=load_expectations(EXPECTATIONS_PATH),
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT_PATH.relative_to(REPO_ROOT)} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
