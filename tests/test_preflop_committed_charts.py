"""The committed chart itself, not synthetic fixtures.

These tests are what stop `data/artifacts/preflop/` from drifting away from the
export that produced it, and what prove the real file goes through the real importer
and the real lookup.

The hand-authored reference chart these tests originally described is gone. It
covered three spots, it overlapped the solver export on all three, and its big-blind
defence had been widened during Phase 04 on a rake-free heuristic that the raked
solution contradicts. Two artifacts claiming one spot is a library error, so keeping
both was never an option and keeping the invented one was the wrong choice.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import (
    ChartHit,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction, weights_checksum
from scripts.repo_paths import REPO_ROOT

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
ARTIFACT = ARTIFACT_DIR / "six_max_nl25_100bb.json"

LJ_OPEN = "t6/d100/LJ/rfi"
BTN_OPEN = "t6/d100/BTN/rfi"
BB_VS_CO = "t6/d100/BB/CO:raise"
LJ_VS_CO_3BET = "t6/d100/LJ/LJ:raise,CO:raise"


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR))


def test_committed_artifact_imports() -> None:
    artifacts = import_preflop_artifacts(ARTIFACT_DIR)

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.table_size == 6
    assert artifact.stack_depth_bb == 100
    assert artifact.source.kind == "solver-export"
    assert len(artifact.spots) == 36


def test_committed_artifact_checksum_covers_its_weights() -> None:
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert weights_checksum(artifact.action_weights) == artifact.audit_fields.weights_sha256


def test_committed_file_reproduces_from_its_source_export() -> None:
    """The export is the source of truth; the artifact is its output."""
    result = subprocess.run(
        ["python", str(REPO_ROOT / "scripts" / "convert_preflop_export.py"), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_provenance_names_the_export_it_came_from() -> None:
    source = json.loads(ARTIFACT.read_text(encoding="utf-8"))["source"]

    assert (REPO_ROOT / source["reference"]).exists()


@pytest.mark.parametrize(
    ("spot_key_text", "hand_class", "expected"),
    [
        (LJ_OPEN, "AA", "raise"),
        (LJ_OPEN, "72o", "fold"),
        (LJ_OPEN, "K4s", "fold"),
        (BTN_OPEN, "A5o", "raise"),
        (BTN_OPEN, "ATo", "raise"),
        (BTN_OPEN, "32o", "fold"),
        (BB_VS_CO, "AA", "raise"),
        (BB_VS_CO, "72o", "fold"),
    ],
)
def test_known_chart_entries(
    library: PreflopChartLibrary, spot_key_text: str, hand_class: str, expected: str
) -> None:
    """Hands whose correct action is not a judgement call.

    The retired hand-authored chart had the button opening A2o purely. The raked
    solution folds it 91% of the time, so that expectation was carried over from an
    invented range rather than from a solve, and it is gone. A5o and ATo are pure
    opens in both.
    """
    artifact = library.artifacts[0]

    weights = artifact.weights_for(spot_key_text, hand_class)

    assert weights is not None
    assert max(weights, key=lambda entry: entry[1])[0] == expected


def test_first_orbit_spots_cover_all_169_classes(library: PreflopChartLibrary) -> None:
    """Hero has not acted, so every hand is possible and must be answered."""
    for spot_id in (LJ_OPEN, BTN_OPEN, BB_VS_CO):
        assert len(library.hand_classes_for(spot_id)) == 169, spot_id


def test_a_spot_where_hero_already_acted_covers_only_heros_range(
    library: PreflopChartLibrary,
) -> None:
    """A hand the lojack would never open is not a lookup it can make.

    Committing a strategy for a holding hero cannot have would be fabricated
    coverage; an explicit miss is the honest answer.
    """
    covered = library.hand_classes_for(LJ_VS_CO_3BET)

    assert 0 < len(covered) < 169
    assert "AA" in covered
    assert "72o" not in covered


def test_lookup_hits_the_committed_chart_from_hole_cards(library: PreflopChartLibrary) -> None:
    result = library.lookup_hole_cards(6, 100, "LJ", (), ("Ah", "As"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == LJ_OPEN
    assert result.hand_class == "AA"
    assert result.best_action == "raise"


def test_lookup_hits_the_defense_spot(library: PreflopChartLibrary) -> None:
    result = library.lookup(ChartQuery(6, 100, "BB", (PreflopAction("CO", "raise"),), "AA"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == BB_VS_CO


def test_the_cutoff_facing_a_lojack_open_is_now_covered(library: PreflopChartLibrary) -> None:
    """Phase 04's chart missed this spot; the full-table export holds it."""
    result = library.lookup(ChartQuery(6, 100, "CO", (PreflopAction("LJ", "raise"),), "AA"))

    assert isinstance(result, ChartHit)


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
            "squeeze after an open and a cold call",
            ChartQuery(
                6,
                100,
                "BTN",
                (PreflopAction("LJ", "raise"), PreflopAction("CO", "call")),
                "AA",
            ),
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
        (
            "a hand the lojack cannot hold facing a three-bet",
            ChartQuery(
                6,
                100,
                "LJ",
                (PreflopAction("LJ", "raise"), PreflopAction("CO", "raise")),
                "72o",
            ),
            "lookup:hand-class-not-covered",
        ),
    ],
)
def test_uncovered_queries_fail_closed_against_the_committed_chart(
    library: PreflopChartLibrary, label: str, query: ChartQuery, code: str
) -> None:
    result = library.lookup(query)

    assert isinstance(result, ChartMiss), label
    assert result.code == code, label
