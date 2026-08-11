from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts.hand_classes import hand_class_grid_index
from poker_training_bot.solver_artifacts.lookup import (
    LIBRARY_DUPLICATE_SPOT,
    LIBRARY_ERROR_CODES,
    LIBRARY_NO_ARTIFACTS,
    MISS_CODES,
    MISS_HAND_CLASS_NOT_COVERED,
    MISS_NO_ARTIFACT_FOR_DEPTH,
    MISS_NO_ARTIFACT_FOR_TABLE,
    MISS_POSITION_NOT_AT_TABLE,
    MISS_SPOT_NOT_COVERED,
    MISS_UNREPRESENTABLE_SPOT,
    ChartHit,
    ChartLibraryError,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import (
    ARTIFACT_SCHEMA_VERSION,
    ActionWeights,
    ArtifactAuditFields,
    ArtifactSource,
    PreflopAction,
    PreflopArtifact,
    SpotDefinition,
    spot_key,
    weights_checksum,
)

RFI_SPOT = "t6/d100/CO/rfi"
VS_OPEN_SPOT = "t6/d100/BB/CO:raise"

CO_OPEN: tuple[PreflopAction, ...] = (PreflopAction("CO", "raise"),)
FOLDED_TO_HERO: tuple[PreflopAction, ...] = ()
SECOND_ORBIT: tuple[PreflopAction, ...] = (
    PreflopAction("CO", "raise"),
    PreflopAction("BB", "raise"),
    PreflopAction("CO", "raise"),
)

PURE_RAISE: ActionWeights = (("raise", 1.0),)
PURE_FOLD: ActionWeights = (("fold", 1.0),)
MIXED: ActionWeights = (("call", 0.5), ("raise", 0.5))

SpotSpec = tuple[str, tuple[PreflopAction, ...], Mapping[str, ActionWeights]]

CORE_SPOTS: tuple[SpotSpec, ...] = (
    ("CO", FOLDED_TO_HERO, {"AA": PURE_RAISE, "AKs": PURE_RAISE, "72o": PURE_FOLD}),
    ("BB", CO_OPEN, {"AA": PURE_RAISE, "AKs": MIXED, "72o": PURE_FOLD}),
)


def make_artifact(
    spots: Sequence[SpotSpec] = CORE_SPOTS,
    name: str = "Chart A",
    table_size: int = 6,
    stack_depth_bb: int = 100,
) -> PreflopArtifact:
    """Build a fully validated artifact in memory.

    Spot ids are derived with `schema.spot_key` and the audit fields are
    recomputed, so the fixture passes the same validation a committed file does.
    """
    definitions: list[SpotDefinition] = []
    action_weights: list[tuple[str, tuple[tuple[str, ActionWeights], ...]]] = []
    for hero_position, sequence, classes in spots:
        spot_id = spot_key(table_size, stack_depth_bb, hero_position, sequence)
        definitions.append(
            SpotDefinition(
                spot_id=spot_id, hero_position=hero_position, action_sequence=sequence
            )
        )
        action_weights.append(
            (
                spot_id,
                tuple(
                    (hand_class_text, classes[hand_class_text])
                    for hand_class_text in sorted(classes, key=hand_class_grid_index)
                ),
            )
        )
    structure = tuple(action_weights)
    distinct = {name_ for _, classes in structure for name_, _ in classes}
    return PreflopArtifact(
        artifact_schema_version=ARTIFACT_SCHEMA_VERSION,
        source=ArtifactSource(
            name=name, kind="hand-authored", reference="tests/test_preflop_lookup.py"
        ),
        generated_at="2026-08-11T00:00:00Z",
        table_size=table_size,
        stack_depth_bb=stack_depth_bb,
        positions=table_positions(table_size),
        spots=tuple(definitions),
        action_weights=structure,
        audit_fields=ArtifactAuditFields(
            weights_sha256=weights_checksum(structure),
            spot_count=len(definitions),
            hand_class_count=len(distinct),
            notes="hand-authored fixture for chart lookup tests",
        ),
    )


def core_library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts((make_artifact(),))


def query(
    hand_class: str = "AA",
    table_size: int = 6,
    stack_depth_bb: int = 100,
    hero_position: str = "CO",
    action_sequence: tuple[PreflopAction, ...] = FOLDED_TO_HERO,
) -> ChartQuery:
    return ChartQuery(
        table_size=table_size,
        stack_depth_bb=stack_depth_bb,
        hero_position=hero_position,
        action_sequence=action_sequence,
        hand_class=hand_class,
    )


def vs_open(hand_class: str = "AA") -> ChartQuery:
    """The big blind facing a cutoff open, the covered vs-open spot."""
    return query(hand_class=hand_class, hero_position="BB", action_sequence=CO_OPEN)


def hit(outcome: ChartHit | ChartMiss) -> ChartHit:
    assert isinstance(outcome, ChartHit), outcome
    return outcome


def miss(outcome: ChartHit | ChartMiss) -> ChartMiss:
    assert isinstance(outcome, ChartMiss), outcome
    return outcome


def test_spot_key_constants_match_the_derived_keys() -> None:
    assert spot_key(6, 100, "CO", FOLDED_TO_HERO) == RFI_SPOT
    assert spot_key(6, 100, "BB", CO_OPEN) == VS_OPEN_SPOT


def test_rfi_hit_returns_the_artifact_weights_unchanged() -> None:
    library = core_library()
    found = hit(library.lookup(query(hand_class="AKs")))
    assert found.artifact_id == "t6/d100/chart-a"
    assert found.spot_key == RFI_SPOT
    assert found.hand_class == "AKs"
    assert found.action_weights == PURE_RAISE
    assert found.best_action == "raise"


def test_vs_open_hit_returns_the_artifact_weights_in_order() -> None:
    library = core_library()
    found = hit(library.lookup(vs_open("AKs")))
    assert found.spot_key == VS_OPEN_SPOT
    assert found.action_weights == (("call", 0.5), ("raise", 0.5))
    assert [action for action, _ in found.action_weights] == ["call", "raise"]


def test_hit_weights_are_the_artifact_tuple_and_nothing_is_mutated() -> None:
    artifact = make_artifact()
    before = artifact.action_weights
    library = PreflopChartLibrary.from_artifacts((artifact,))
    found = hit(library.lookup(query(hand_class="72o")))
    assert found.action_weights is artifact.weights_for(RFI_SPOT, "72o")
    assert artifact.action_weights == before
    assert library.artifacts == (artifact,)


def test_pure_and_mixed_best_action() -> None:
    library = core_library()
    mixed = hit(library.lookup(vs_open("AKs")))
    assert mixed.action_weights == MIXED
    assert mixed.best_action is None
    pure = hit(library.lookup(vs_open("AA")))
    assert pure.best_action == "raise"
    folded = hit(library.lookup(query(hand_class="72o")))
    assert folded.best_action == "fold"


def test_best_action_ignores_zero_weights() -> None:
    found = ChartHit(
        artifact_id="t6/d100/chart-a",
        spot_key=RFI_SPOT,
        hand_class="AA",
        action_weights=(("fold", 0.0), ("raise", 1.0)),
    )
    assert found.best_action == "raise"


MISSES: tuple[tuple[str, str, dict[str, object]], ...] = (
    ("unknown table size", MISS_NO_ARTIFACT_FOR_TABLE, {"table_size": 9}),
    ("unknown stack depth", MISS_NO_ARTIFACT_FOR_DEPTH, {"stack_depth_bb": 40}),
    ("position not at table", MISS_POSITION_NOT_AT_TABLE, {"hero_position": "UTG"}),
    ("second orbit sequence", MISS_UNREPRESENTABLE_SPOT, {"action_sequence": SECOND_ORBIT}),
    ("uncovered spot", MISS_SPOT_NOT_COVERED, {"hero_position": "SB"}),
    ("uncovered hand class", MISS_HAND_CLASS_NOT_COVERED, {"hand_class": "T9s"}),
)


@pytest.mark.parametrize(
    ("code", "overrides"),
    [(code, overrides) for _, code, overrides in MISSES],
    ids=[name for name, _, _ in MISSES],
)
def test_every_miss_code(code: str, overrides: dict[str, object]) -> None:
    library = core_library()
    assert hit(library.lookup(query()))
    refused = miss(library.lookup(query(**overrides)))  # type: ignore[arg-type]
    assert refused.code == code
    assert refused.detail


def test_miss_codes_are_unique_and_namespaced() -> None:
    assert len(set(MISS_CODES)) == len(MISS_CODES)
    assert all(code.startswith("lookup:") for code in MISS_CODES)
    assert {code for _, code, _ in MISSES} == set(MISS_CODES)
    assert all(code.startswith("library:") for code in LIBRARY_ERROR_CODES)


def test_uncovered_stack_depth_never_borrows_the_nearest_depth() -> None:
    library = core_library()
    covered = hit(library.lookup(query(stack_depth_bb=100)))
    assert covered.action_weights == PURE_RAISE
    for depth in (20, 40, 99, 101, 200):
        refused = miss(library.lookup(query(stack_depth_bb=depth)))
        assert refused.code == MISS_NO_ARTIFACT_FOR_DEPTH
        assert "100" in refused.detail


def test_uncovered_table_size_never_borrows_another_table() -> None:
    library = core_library()
    for table_size in (2, 5, 7, 9):
        refused = miss(library.lookup(query(table_size=table_size)))
        assert refused.code == MISS_NO_ARTIFACT_FOR_TABLE


def test_second_orbit_spot_has_no_key() -> None:
    assert query().spot_key == RFI_SPOT
    assert vs_open().spot_key == VS_OPEN_SPOT
    assert query(action_sequence=SECOND_ORBIT).spot_key is None
    assert query(table_size=99).spot_key is None
    assert query(hero_position="UTG").spot_key is None


@pytest.mark.parametrize("hole_cards", [("As", "Ks"), ("Ks", "As"), ("as", "ks")])
def test_hole_card_entry_points_agree(hole_cards: tuple[str, str]) -> None:
    library = core_library()
    expected = hit(library.lookup(vs_open("AKs")))
    from_query = hit(
        library.lookup(
            ChartQuery.from_hole_cards(
                table_size=6,
                stack_depth_bb=100,
                hero_position="BB",
                action_sequence=CO_OPEN,
                hole_cards=hole_cards,
            )
        )
    )
    direct = hit(
        library.lookup_hole_cards(
            table_size=6,
            stack_depth_bb=100,
            hero_position="BB",
            action_sequence=CO_OPEN,
            hole_cards=hole_cards,
        )
    )
    assert from_query == expected
    assert direct == expected
    assert direct.hand_class == "AKs"


def test_offsuit_hole_cards_are_a_different_class() -> None:
    library = core_library()
    suited = hit(
        library.lookup_hole_cards(6, 100, "BB", CO_OPEN, ("Ah", "Kh")),
    )
    assert suited.hand_class == "AKs"
    refused = miss(library.lookup_hole_cards(6, 100, "BB", CO_OPEN, ("Ah", "Kd")))
    assert refused.code == MISS_HAND_CLASS_NOT_COVERED
    assert "AKo" in refused.detail


def test_identical_queries_return_identical_results() -> None:
    library = core_library()
    for overrides in [{}] + [dict(over) for _, _, over in MISSES]:
        first = library.lookup(query(**overrides))  # type: ignore[arg-type]
        second = library.lookup(query(**overrides))  # type: ignore[arg-type]
        assert first == second
        assert repr(first) == repr(second)


def test_library_ordering_is_stable_regardless_of_input_order() -> None:
    deep = make_artifact(name="Chart A", stack_depth_bb=100)
    shallow = make_artifact(name="Chart B", stack_depth_bb=50)
    forward = PreflopChartLibrary.from_artifacts((deep, shallow))
    backward = PreflopChartLibrary.from_artifacts((shallow, deep))
    assert forward.artifacts == backward.artifacts
    assert [artifact.artifact_id for artifact in forward.artifacts] == [
        "t6/d100/chart-a",
        "t6/d50/chart-b",
    ]
    assert forward.spot_keys() == backward.spot_keys()
    assert forward.spot_keys() == tuple(
        sorted([RFI_SPOT, VS_OPEN_SPOT, "t6/d50/CO/rfi", "t6/d50/BB/CO:raise"])
    )
    assert forward.spot_keys() == forward.spot_keys()


def test_ordering_is_stable_even_for_artifacts_sharing_an_id() -> None:
    """Same source name, table, and depth, disjoint spots: order comes from content."""
    left = make_artifact(spots=(CORE_SPOTS[0],))
    right = make_artifact(spots=(("BTN", FOLDED_TO_HERO, {"AA": PURE_RAISE}),))
    assert left.artifact_id == right.artifact_id
    forward = PreflopChartLibrary.from_artifacts((left, right))
    backward = PreflopChartLibrary.from_artifacts((right, left))
    assert forward.artifacts == backward.artifacts
    assert forward.spot_keys() == tuple(sorted(["t6/d100/BTN/rfi", RFI_SPOT]))
    assert hit(forward.lookup(query(hero_position="BTN"))).spot_key == "t6/d100/BTN/rfi"


def test_both_depths_answer_only_their_own_queries() -> None:
    library = PreflopChartLibrary.from_artifacts(
        (make_artifact(name="Chart A"), make_artifact(name="Chart B", stack_depth_bb=50))
    )
    assert hit(library.lookup(query(stack_depth_bb=100))).artifact_id == "t6/d100/chart-a"
    assert hit(library.lookup(query(stack_depth_bb=50))).artifact_id == "t6/d50/chart-b"
    assert miss(library.lookup(query(stack_depth_bb=75))).code == MISS_NO_ARTIFACT_FOR_DEPTH


def test_duplicate_spot_across_artifacts_fails_closed() -> None:
    with pytest.raises(ChartLibraryError) as error:
        PreflopChartLibrary.from_artifacts(
            (make_artifact(name="Chart A"), make_artifact(name="Chart B"))
        )
    assert error.value.code == LIBRARY_DUPLICATE_SPOT
    assert RFI_SPOT in error.value.message
    assert LIBRARY_DUPLICATE_SPOT in str(error.value)


def test_empty_library_fails_closed() -> None:
    with pytest.raises(ChartLibraryError) as error:
        PreflopChartLibrary.from_artifacts(())
    assert error.value.code == LIBRARY_NO_ARTIFACTS
    assert error.value.message
    assert LIBRARY_NO_ARTIFACTS in str(error.value)


def test_from_directory_imports_and_answers(tmp_path: Path) -> None:
    payload = make_artifact().to_payload()
    (tmp_path / "chart.json").write_text(json.dumps(payload), encoding="utf-8")
    library = PreflopChartLibrary.from_directory(tmp_path)
    assert [artifact.artifact_id for artifact in library.artifacts] == ["t6/d100/chart-a"]
    assert library.spot_keys() == tuple(sorted([RFI_SPOT, VS_OPEN_SPOT]))
    found = hit(library.lookup(vs_open("AKs")))
    assert found.action_weights == MIXED
    assert miss(library.lookup(query(hand_class="T9s"))).code == MISS_HAND_CLASS_NOT_COVERED
    assert PreflopChartLibrary.from_directory(str(tmp_path)).spot_keys() == library.spot_keys()


def test_query_rejects_programming_errors() -> None:
    with pytest.raises(ValueError):
        query(hand_class="A2x")
    with pytest.raises(ValueError):
        query(hand_class="")
    with pytest.raises(ValueError):
        ChartQuery(6, 100, "CO", ("CO:raise",), "AA")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ChartQuery(6, 100, "CO", [PreflopAction("CO", "raise")], "AA")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        query(hero_position="")
    with pytest.raises(ValueError):
        query(table_size="6")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        query(stack_depth_bb=True)  # type: ignore[arg-type]


def test_query_accepts_unknown_tables_and_positions() -> None:
    assert query(table_size=99).table_size == 99
    assert query(table_size=-1).table_size == -1
    assert query(hero_position="ZZ").hero_position == "ZZ"
    assert query(stack_depth_bb=0).stack_depth_bb == 0
    library = core_library()
    assert miss(library.lookup(query(table_size=-1))).code == MISS_NO_ARTIFACT_FOR_TABLE
    assert miss(library.lookup(query(hero_position="ZZ"))).code == MISS_POSITION_NOT_AT_TABLE
    assert miss(library.lookup(query(stack_depth_bb=0))).code == MISS_NO_ARTIFACT_FOR_DEPTH


def test_hit_and_miss_require_content() -> None:
    with pytest.raises(ValueError):
        ChartHit(artifact_id="", spot_key=RFI_SPOT, hand_class="AA", action_weights=PURE_RAISE)
    with pytest.raises(ValueError):
        ChartHit(artifact_id="a", spot_key="", hand_class="AA", action_weights=PURE_RAISE)
    with pytest.raises(ValueError):
        ChartHit(artifact_id="a", spot_key=RFI_SPOT, hand_class="", action_weights=PURE_RAISE)
    with pytest.raises(ValueError):
        ChartHit(artifact_id="a", spot_key=RFI_SPOT, hand_class="AA", action_weights=())
    with pytest.raises(ValueError):
        ChartMiss(code="", detail="detail")
    with pytest.raises(ValueError):
        ChartMiss(code=MISS_SPOT_NOT_COVERED, detail="")
