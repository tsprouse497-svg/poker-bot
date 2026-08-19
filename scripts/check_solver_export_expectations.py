"""Recompute the committed solver export's orderings, and fail on a broken source card.

Every number this checks is computed from the export on this run. Nothing is read back
from a figure some earlier run recorded, because a gate check that reads its own previous
answer is a mirror - which is the defect Phase 09 found in this repo's own settlement
oracle.

Nothing here grades the solve against `six_max_nl25_100bb.json`. That comparison is
printed in the report for a reader and gated by nothing; see decision 6 for why.
"""

from __future__ import annotations

import argparse
import sys

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.gtopen_expectations import (  # noqa: E402
    aggregate_frequencies,
    ordering_errors,
)
from poker_training_bot.solver_artifacts.gtopen_export import (  # noqa: E402
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    export_checksum,
    load_solver_export,
    load_source_card,
    source_card_errors,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", default=str(COMMITTED_EXPORT_PATH))
    parser.add_argument("--source-card", default=str(COMMITTED_SOURCE_CARD_PATH))
    args = parser.parse_args(argv)

    export = load_solver_export(args.export)
    aggregates = aggregate_frequencies(export)
    errors = list(ordering_errors(aggregates))

    card = load_source_card(args.source_card)
    errors += source_card_errors(card)
    checksum = export_checksum(export)
    if card.get("export_sha256") != checksum:
        errors.append(
            f"source card records export_sha256 {card.get('export_sha256')!r},"
            f" but the export checksums to {checksum}"
        )
    if card.get("node_counts", {}).get("exported") != export.node_count:
        errors.append(
            f"source card records {card.get('node_counts', {}).get('exported')} exported"
            f" nodes, but the export holds {export.node_count}"
        )

    print(f"export:        {args.export}")
    print(f"action nodes:  {export.node_count}")
    for position, value in sorted(aggregates.opening_pct.items()):
        print(f"  RFI {position:<4} {value:>7.2f}%")
    for position, value in sorted(aggregates.defence_pct.items()):
        print(f"  BB vs {position:<4} {value:>7.2f}%")
    if errors:
        print("")
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("both orderings hold, and the source card matches the export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
