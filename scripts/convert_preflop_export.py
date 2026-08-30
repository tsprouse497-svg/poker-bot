"""Turn the committed GTOpen export into the chart, its sizing table, and a restamped card.

The chart is derived, never hand-edited. Everything this writes is reproducible from
`data/artifacts/preflop/exports/`, which is what makes `--check` meaningful: a chart nobody
can regenerate is a chart nobody can diff against its origin, and a hand edit to a derived
file is a number with no origin.

The rule that decides *which* solved nodes become spots lives in
`solver_artifacts.chart_derivation`, not here, and this script is deliberately thin. The
predicate, the census, the walk that says whose action is whose, the per-cell reach and the
per-spot arrival are all `src/` code because the frozen tests hold them to it and because a
report has to be able to re-derive them without shelling out to a script.

Three files come out and one that used to is now excluded on purpose.

- `six_max_100bb_rakefree.json`, the chart: 86 spots of the 38,828 solved action nodes.
- `sizings/six_max_100bb_rakefree.json`, every price a spot offers hero per hand class.
- the export's own source card, whose `size` block is restamped. Deleting the retired chart
  and writing a smaller one both move the `data/artifacts` total, so the card's headroom is
  stale the moment this runs. `headroom_bytes` counts the card itself, so it settles to a
  fixed point rather than assuming one pass is enough - the same loop
  `scripts/extract_gtopen_preflop.py` uses, and for the same reason.

What this must **not** write is `expectations/six_max_nl25_100bb.json`. It holds the only
numbers in this phase that this repo did not produce, which is what catches a range that is
uniformly wrong rather than merely self-consistent, and a reference regenerated from what it
checks cannot fail. Rewriting it with identical content is still rewriting it: on the day the
numbers behind it move, nobody would notice. `sources/` is left alone for the same reason -
it is the raked GTO Wizard extraction the retired chart came from, kept as evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.chart_derivation import derive_chart  # noqa: E402
from poker_training_bot.solver_artifacts.gtopen_export import (  # noqa: E402
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    load_solver_export,
)

ARTIFACTS_DIR = REPO_ROOT / "data" / "artifacts"
PREFLOP_DIR = ARTIFACTS_DIR / "preflop"
ARTIFACT = PREFLOP_DIR / "six_max_100bb_rakefree.json"
SIZINGS = PREFLOP_DIR / "sizings" / "six_max_100bb_rakefree.json"

BYTE_LIMIT = 20 * 1024 * 1024
"""Phase 10's ruled cap on `data/artifacts`, enforced by `scripts/check_file_sizes.py`.
At 86 spots it no longer binds, and it stays a halt and a decision rather than a number to
raise - which is what the card's headroom figure is for."""

SETTLING_PASSES = 8

EXPRESSIBLE_SPOT_NOTE = (
    "the whole export divided by the {count} spots the committed chart expresses today, so"
    " it is what keeping the entire tree costs per spot currently usable rather than the"
    " size of a derived chart. The roadmap's 7.1 KB per spot was measured off the GTO"
    " Wizard chart format and is not comparable"
)


def render(payload: dict) -> str:
    """The chart and the sizing table, in the shape the importer reads back."""
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def render_card(card: dict) -> str:
    """The source card, in the shape `extract_gtopen_preflop.py` writes it."""
    return json.dumps(card, indent=1, sort_keys=True) + "\n"


def directory_bytes(overrides: dict[Path, str]) -> int:
    """What `data/artifacts` would total with these files holding this text.

    Measured against the text rather than against the disk, so `--check` computes the same
    headroom a write pass would produce without writing anything. Reading the disk for the
    files this script owns would make `--check` agree with whatever is already committed.
    """
    total = sum(
        path.stat().st_size
        for path in ARTIFACTS_DIR.rglob("*")
        if path.is_file() and path not in overrides
    )
    return total + sum(len(text.encode("utf-8")) for text in overrides.values())


def build_source_card(
    spot_count: int, node_count: int, artifact_text: str, sizing_text: str
) -> str:
    """The committed card with its `size` block recomputed, and nothing else touched.

    Decision 2 ships the solve as it stands and this phase runs no re-solve, so every other
    field on the card describes a solve that has not moved: one solve record, 300 iterations,
    both checksums where phase 10 left them. Restamping any of those would be a re-solve
    nobody ruled, which carries five separate obligations of its own.
    """
    card = json.loads(COMMITTED_SOURCE_CARD_PATH.read_text(encoding="utf-8"))
    size = card["size"]
    export_bytes = COMMITTED_EXPORT_PATH.stat().st_size
    size["bytes"] = export_bytes
    size["limit_bytes"] = BYTE_LIMIT
    size["bytes_per_node"] = round(export_bytes / node_count, 2)
    size["bytes_per_expressible_spot"] = round(export_bytes / spot_count, 2)
    size["bytes_per_expressible_spot_note"] = EXPRESSIBLE_SPOT_NOTE.format(count=spot_count)
    for _ in range(SETTLING_PASSES):
        text = render_card(card)
        headroom = BYTE_LIMIT - directory_bytes(
            {ARTIFACT: artifact_text, SIZINGS: sizing_text, COMMITTED_SOURCE_CARD_PATH: text}
        )
        if size["headroom_bytes"] == headroom:
            return text
        size["headroom_bytes"] = headroom
    raise SystemExit("the source card's headroom figure will not settle")


def outputs() -> list[tuple[Path, str]]:
    """Every committed file this script owns, with the text it should hold."""
    export = load_solver_export(COMMITTED_EXPORT_PATH)
    chart = derive_chart(export)
    artifact_text = render(chart.artifact_payload)
    sizing_text = render(chart.sizing_payload)
    card_text = build_source_card(
        len(chart.artifact_payload["spots"]), export.node_count, artifact_text, sizing_text
    )
    return [
        (ARTIFACT, artifact_text),
        (SIZINGS, sizing_text),
        (COMMITTED_SOURCE_CARD_PATH, card_text),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed files match what this script produces",
    )
    args = parser.parse_args(argv)

    produced = outputs()
    if not args.check:
        for path, text in produced:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        print(f"wrote {', '.join(path.name for path, _ in produced)}")
        return 0

    stale = [
        str(path.relative_to(REPO_ROOT))
        for path, text in produced
        if not path.exists() or path.read_text(encoding="utf-8") != text
    ]
    if stale:
        for name in stale:
            print(f"{name} does not reproduce from the committed export", file=sys.stderr)
        return 1
    print("the committed chart, its sizings and the source card reproduce from the export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
