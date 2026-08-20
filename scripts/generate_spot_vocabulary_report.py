"""Write the spot vocabulary report a human reads.

Thin on purpose. Everything the report says is derived in
`poker_training_bot.solver_artifacts.vocabulary_report`, which is importable and so
testable; this file exists to put the text on disk and to fail loudly when the module
refuses to publish a measurement it cannot stand behind.
"""

from __future__ import annotations

import sys

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.vocabulary_report import (  # noqa: E402
    VocabularyReportError,
    render_spot_vocabulary_report,
)

REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_spot_vocabulary_report.txt"


def main() -> int:
    try:
        text = render_spot_vocabulary_report()
    except VocabularyReportError as error:
        # The report is evidence, so a measurement it cannot stand behind is a failed
        # command rather than a caveat inside a file that still gets written.
        print(f"spot vocabulary report refused to publish: {error}", file=sys.stderr)
        return 1
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
