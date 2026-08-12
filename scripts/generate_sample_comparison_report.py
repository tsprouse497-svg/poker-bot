"""Write the real-hand comparison report and its refusal inventory.

Both files are a pure function of the committed sample: no clock, no network, no
seed of its own. Regenerating them on any machine from the same commit produces the
same bytes, which is what makes a number in them arguable rather than merely
asserted.
"""

from __future__ import annotations

import sys

from repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.data_pipeline.comparison import (  # noqa: E402
    compare_committed_sample,
    render_comparison_report,
    render_refusal_inventory,
)
from poker_training_bot.data_pipeline.sample import load_committed_sample  # noqa: E402

REPORT_DIR = REPO_ROOT / "reports" / "active"
COMPARISON_PATH = REPORT_DIR / "latest_sample_comparison_report.txt"
INVENTORY_PATH = REPORT_DIR / "latest_sample_refusal_inventory.txt"


def main() -> int:
    result = compare_committed_sample(load_committed_sample())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_PATH.write_text(render_comparison_report(result), encoding="utf-8")
    INVENTORY_PATH.write_text(render_refusal_inventory(result), encoding="utf-8")
    print(f"wrote {COMPARISON_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {INVENTORY_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
