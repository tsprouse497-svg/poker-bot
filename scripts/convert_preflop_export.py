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

- `six_max_100bb_rakefree.json`, the chart: the spots `chart_derivation` selects out of the
  export's solved action nodes. Neither count is written here. Both have already moved -
  36 spots became 249 at the phase 14 cutover and then 156 over MAINT-34, whose re-solve also
  took the tree from 33,969 nodes to 30,609 - and a literal here is a number nothing recomputes.
- `sizings/six_max_100bb_rakefree.json`, every price a spot offers hero per hand class.
- the export's own source card, whose `size` block is restamped with the export's own size
  and the per-node and per-spot costs, and nothing else. The card used to carry the headroom
  left under the `data/artifacts` cap, which is a figure about every file in the tree, so any
  artifact committed anywhere made the card stale and this script's `--check` red
  (`SOLVER-EXPORT-CARD-HEADROOM-COUNTS-THE-WHOLE-ARTIFACT-TREE`). The tree total and the cap
  are `scripts/check_file_sizes.py`'s business, measured when the gate runs.

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

WHOLE_TREE_FIGURES = ("headroom_bytes", "limit_bytes")
"""Keys a card once carried about the tree rather than the export, dropped on restamp so a
card committed before MAINT-41 comes back without them."""

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


def build_source_card(spot_count: int, node_count: int) -> str:
    """The committed card with its `size` block recomputed, and nothing else touched.

    Every other field on the card belongs to whoever ran the solver. This script never has a
    solver in front of it, so restamping a solve record here would be inventing one:
    `scripts/extract_gtopen_preflop.py` writes the iteration count, the achieved gap, the
    wall clock, the checksums and the determinism result, and this script leaves all of them
    alone. MAINT-34 did re-solve, which is why the figures this docstring used to quote are
    gone rather than corrected - a solve record copied into prose goes stale at the next one.
    """
    card = json.loads(COMMITTED_SOURCE_CARD_PATH.read_text(encoding="utf-8"))
    size = card["size"]
    for key in WHOLE_TREE_FIGURES:
        size.pop(key, None)
    export_bytes = COMMITTED_EXPORT_PATH.stat().st_size
    size["bytes"] = export_bytes
    size["bytes_per_node"] = round(export_bytes / node_count, 2)
    size["bytes_per_expressible_spot"] = round(export_bytes / spot_count, 2)
    size["bytes_per_expressible_spot_note"] = EXPRESSIBLE_SPOT_NOTE.format(count=spot_count)
    return render_card(card)


def outputs() -> list[tuple[Path, str]]:
    """Every committed file this script owns, with the text it should hold."""
    export = load_solver_export(COMMITTED_EXPORT_PATH)
    chart = derive_chart(export)
    artifact_text = render(chart.artifact_payload)
    sizing_text = render(chart.sizing_payload)
    card_text = build_source_card(len(chart.artifact_payload["spots"]), export.node_count)
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
