"""The committed slice of the public corpus, and the rule that chose it.

Nothing here reaches the network. The corpus text for exactly the selected hands is
committed, so the conversion this phase rests on is checkable offline by a reader who
does not trust it - which is the only form of trust worth having in a repo whose whole
argument is that its numbers came from outside itself.

The selection rule lives here rather than in the builder script so the test that pins
it and the builder that applies it cannot drift apart.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from poker_training_bot.data_pipeline.convert import convert_hand
from poker_training_bot.data_pipeline.corpus import CorpusHand, parse_corpus_hand
from poker_training_bot.hand_history.schema import NormalizedHandHistory

SAMPLE_DIR = Path(__file__).resolve().parents[3] / "data" / "samples" / "public_corpus"
SOURCE_TEXT_PATH = SAMPLE_DIR / "corpus_hands.jsonl"
SIDECAR_PATH = SAMPLE_DIR / "corpus_sidecar.json"
EXCLUSIONS_PATH = SAMPLE_DIR / "corpus_exclusions.json"

# Ruled at the stage 3 human gate: a stride across the whole sorted corpus rather
# than a prefix, because a prefix draws from a handful of consecutive sessions and
# the same few players hold the button in all of them.
SELECTION_STRIDE = 20
SAMPLE_HAND_COUNT = 500

MACHINE_PLAYER = "Pluribus"


@dataclass(frozen=True)
class SampleRecord:
    corpus: CorpusHand
    normalized: NormalizedHandHistory
    source_text: str
    source_checksum: str


@dataclass(frozen=True)
class SampleExclusion:
    hand_id: str
    reason: str


@dataclass(frozen=True)
class CommittedSample:
    records: tuple[SampleRecord, ...]
    exclusions: tuple[SampleExclusion, ...]
    sidecar: dict[str, dict]

    @property
    def committed_paths(self) -> tuple[Path, ...]:
        return (SOURCE_TEXT_PATH, SIDECAR_PATH, EXCLUSIONS_PATH)


def select_source_paths(paths: Sequence[str]) -> tuple[str, ...]:
    """The committed selection rule: a stride over a stable lexicographic sort.

    Sorting first is what makes the rule independent of the order the filesystem
    hands paths back, so the same corpus yields the same sample on any machine.
    """
    return tuple(sorted(paths)[::SELECTION_STRIDE])


def checksum_for(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_committed_sample() -> CommittedSample:
    records: list[SampleRecord] = []
    for line in SOURCE_TEXT_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        text = entry["source_text"]
        corpus = parse_corpus_hand(text, source_path=entry["source_path"])
        records.append(
            SampleRecord(
                corpus=corpus,
                normalized=convert_hand(corpus),
                source_text=text,
                source_checksum=checksum_for(text),
            )
        )
    exclusions = tuple(
        SampleExclusion(entry["hand_id"], entry["reason"])
        for entry in json.loads(EXCLUSIONS_PATH.read_text(encoding="utf-8"))
    )
    sidecar = json.loads(SIDECAR_PATH.read_text(encoding="utf-8"))
    return CommittedSample(tuple(records), exclusions, sidecar)
