"""Apply the committed selection rule to a local corpus clone.

Deliberately not part of the gate. It needs the full corpus, which is not in this
repo and never will be; the gate reads only what this script committed. The same
argument as `scripts/build_preflop_chart_artifact.py`: a committed artifact needs a
reproducible origin, and a builder in the gate would be a builder that rewrites its
own evidence on every run.

Usage:
    uv run python scripts/build_sample_corpus.py --corpus /path/to/phh-dataset/data/pluribus
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.data_pipeline.convert import ConversionError, convert_hand  # noqa: E402
from poker_training_bot.data_pipeline.corpus import (  # noqa: E402
    CorpusParseError,
    parse_corpus_hand,
)
from poker_training_bot.data_pipeline.sample import (  # noqa: E402
    EXCLUSIONS_PATH,
    SAMPLE_DIR,
    SIDECAR_PATH,
    SOURCE_TEXT_PATH,
    checksum_for,
    select_source_paths,
)

CORPUS_PREFIX = "pluribus"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        required=True,
        type=Path,
        help="Directory holding the corpus's .phh files (the dataset's data/pluribus)",
    )
    args = parser.parse_args()

    relative = sorted(
        f"{CORPUS_PREFIX}/{path.relative_to(args.corpus).as_posix()}"
        for path in args.corpus.rglob("*.phh")
    )
    selected = select_source_paths(relative)
    print(f"corpus holds {len(relative)} hands; the rule selects {len(selected)}")

    kept: list[dict] = []
    sidecar: dict[str, dict] = {}
    exclusions: list[dict] = []

    for source_path in selected:
        on_disk = args.corpus / source_path[len(CORPUS_PREFIX) + 1 :]
        text = on_disk.read_text(encoding="utf-8")
        try:
            hand = parse_corpus_hand(text, source_path=source_path)
            convert_hand(hand)
        except (CorpusParseError, ConversionError) as error:
            exclusions.append(
                {
                    "hand_id": source_path.removesuffix(".phh"),
                    "reason": str(error),
                }
            )
            continue
        kept.append({"source_path": source_path, "source_text": text})
        sidecar[hand.hand_id] = {
            "source_path": source_path,
            "source_checksum": checksum_for(text),
            "players": list(hand.players),
            "hole_cards": ["".join(pair) for pair in hand.hole_cards],
            "starting_stacks": list(hand.starting_stacks),
            "finishing_stacks": list(hand.finishing_stacks),
        }

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_TEXT_PATH.write_text(
        "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in kept), encoding="utf-8"
    )
    SIDECAR_PATH.write_text(json.dumps(sidecar, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    EXCLUSIONS_PATH.write_text(json.dumps(exclusions, indent=1) + "\n", encoding="utf-8")

    print(f"committed {len(kept)} hands, excluded {len(exclusions)}")
    for entry in exclusions:
        print(f"  excluded {entry['hand_id']}: {entry['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
