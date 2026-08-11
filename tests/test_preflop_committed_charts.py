"""The committed charts themselves, not synthetic fixtures.

These tests are what stop `data/artifacts/preflop/` from drifting away from the
range spec that claims to have produced it, and what prove the real file goes
through the real importer and the real lookup.
"""

from __future__ import annotations

import json

import pytest

from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import (
    ChartHit,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction, weights_checksum
from scripts.build_preflop_chart_artifact import OUTPUT, build_payload
from scripts.repo_paths import REPO_ROOT

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"

CO_OPEN = "t6/d100/CO/rfi"
BTN_OPEN = "t6/d100/BTN/rfi"
BB_VS_CO = "t6/d100/BB/CO:raise"


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR))


def test_committed_artifact_imports() -> None:
    artifacts = import_preflop_artifacts(ARTIFACT_DIR)

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.table_size == 6
    assert artifact.stack_depth_bb == 100
    assert artifact.source.kind == "hand-authored"
    assert [spot.spot_id for spot in artifact.spots] == [CO_OPEN, BTN_OPEN, BB_VS_CO]


def test_committed_artifact_checksum_covers_its_weights() -> None:
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert weights_checksum(artifact.action_weights) == artifact.audit_fields.weights_sha256


def test_committed_file_matches_its_builder() -> None:
    """The range spec is the source of truth; the JSON is its output."""
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))

    assert on_disk == build_payload()


@pytest.mark.parametrize(
    ("spot_key_text", "hand_class", "expected"),
    [
        (CO_OPEN, "AA", "raise"),
        (CO_OPEN, "A2s", "raise"),
        (CO_OPEN, "54s", "raise"),
        (CO_OPEN, "72o", "fold"),
        (CO_OPEN, "K4s", "fold"),
        (BTN_OPEN, "43s", "raise"),
        (BTN_OPEN, "A2o", "raise"),
        (BTN_OPEN, "32o", "fold"),
        (BB_VS_CO, "AKs", "raise"),
        (BB_VS_CO, "AQo", "raise"),
        (BB_VS_CO, "32s", "call"),
        (BB_VS_CO, "98o", "call"),
        (BB_VS_CO, "72o", "fold"),
    ],
)
def test_known_chart_entries(
    library: PreflopChartLibrary, spot_key_text: str, hand_class: str, expected: str
) -> None:
    artifact = library.artifacts[0]

    weights = artifact.weights_for(spot_key_text, hand_class)

    assert weights == ((expected, 1.0),)


def test_every_committed_spot_covers_all_169_classes(library: PreflopChartLibrary) -> None:
    artifact = library.artifacts[0]

    for spot_id, hand_classes in artifact.action_weights:
        assert len(hand_classes) == 169, spot_id


def test_lookup_hits_the_committed_chart_from_hole_cards(library: PreflopChartLibrary) -> None:
    result = library.lookup_hole_cards(6, 100, "CO", (), ("Ah", "Ks"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == CO_OPEN
    assert result.hand_class == "AKo"
    assert result.best_action == "raise"


def test_lookup_hits_the_defense_spot(library: PreflopChartLibrary) -> None:
    result = library.lookup(
        ChartQuery(6, 100, "BB", (PreflopAction("CO", "raise"),), "76s")
    )

    assert isinstance(result, ChartHit)
    assert result.spot_key == BB_VS_CO
    assert result.best_action == "call"


@pytest.mark.parametrize(
    ("label", "query", "code"),
    [
        (
            "nine-handed table",
            ChartQuery(9, 100, "CO", (), "AA"),
            "lookup:no-artifact-for-table-size",
        ),
        (
            "forty big blinds",
            ChartQuery(6, 40, "CO", (), "AA"),
            "lookup:no-artifact-for-stack-depth",
        ),
        (
            "position off the table",
            ChartQuery(6, 100, "UTG", (), "AA"),
            "lookup:position-not-at-table",
        ),
        (
            "cutoff facing a lojack open",
            ChartQuery(6, 100, "CO", (PreflopAction("LJ", "raise"),), "AA"),
            "lookup:spot-not-covered",
        ),
        (
            "big blind facing a four-bet",
            ChartQuery(
                6,
                100,
                "BB",
                (
                    PreflopAction("CO", "raise"),
                    PreflopAction("BB", "raise"),
                    PreflopAction("CO", "raise"),
                ),
                "AA",
            ),
            "lookup:unrepresentable-spot",
        ),
    ],
)
def test_uncovered_queries_fail_closed_against_the_committed_chart(
    library: PreflopChartLibrary, label: str, query: ChartQuery, code: str
) -> None:
    result = library.lookup(query)

    assert isinstance(result, ChartMiss), label
    assert result.code == code, label


def test_the_report_probes_are_the_committed_behavior(library: PreflopChartLibrary) -> None:
    """The chart report is human evidence, so its probes must stay truthful."""
    from scripts.generate_preflop_chart_report import PROBES

    verdicts = [library.lookup(query) for _, query in PROBES]

    assert sum(isinstance(result, ChartHit) for result in verdicts) == 3
    assert sum(isinstance(result, ChartMiss) for result in verdicts) == 5
